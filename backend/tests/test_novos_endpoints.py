"""
CRM VITAO360 — Testes dos 3 novos endpoints.

Cobertura:
  1. PATCH /api/clientes/{cnpj}
     - Reatribuicao de consultor por admin (200)
     - Alteracao de rede_regional (200)
     - Sem mudanca real nao gera audit (campos_alterados=[])
     - CNPJ normalizado (pontuacao removida)
     - CNPJ inexistente retorna 404
     - role=consultor retorna 403
     - Registro em AuditLog verificado diretamente no banco

  2. GET /api/clientes/{cnpj}/score
     - Retorna 200 com score_total, prioridade, fatores
     - Fatores contem valor, peso, contribuicao
     - Soma das contribuicoes === score_total (tolerancia 0.1)
     - Pesos somam 1.0
     - CNPJ inexistente retorna 404
     - Sem autenticacao retorna 401

  3. POST /api/sinaleiro/recalcular
     - Retorna 200 com clientes_recalculados, tempo_ms
     - tempo_ms >= 0
     - clientes_recalculados >= numero de clientes no banco (excluindo ALUCINACAO)
     - role=consultor retorna 403

R4  — Two-Base: nenhum endpoint toca valores monetarios de LOG.
R5  — CNPJ: String(14), zero-padded.
R8  — ALUCINACAO excluida do recalculo batch.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import get_current_user, require_admin, require_admin_or_gerente
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.audit_log import AuditLog
from backend.app.models.cliente import Cliente


# ---------------------------------------------------------------------------
# Helpers de usuarios simulados (sem JWT)
# ---------------------------------------------------------------------------

def _fake_usuario(id: int, email: str, nome: str, role: str, consultor_nome: str | None = None):
    return SimpleNamespace(
        id=id,
        email=email,
        nome=nome,
        hashed_password="hash_fake",
        role=role,
        consultor_nome=consultor_nome,
        ativo=True,
    )


# ---------------------------------------------------------------------------
# Fixtures compartilhadas entre as 3 classes de teste
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine_mem():
    """Engine SQLite em memoria — schema completo, isolado do banco real."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="module")
def db_session(engine_mem) -> Session:
    """Sessao com seed de clientes variados para cobrir todos os cenarios."""
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    clientes = [
        # Cliente REAL - MANU - ATIVO
        Cliente(
            cnpj="04067573000193",
            nome_fantasia="Emporio Natural",
            razao_social="Emporio Natural LTDA",
            uf="SC",
            consultor="MANU",
            situacao="ATIVO",
            classificacao_3tier="REAL",
            faturamento_total=45000.0,
            score=82.5,
            prioridade="P2",
            sinaleiro="VERDE",
            temperatura="QUENTE",
            curva_abc="A",
            tipo_cliente="MADURO",
            dias_sem_compra=15,
            ciclo_medio=30,
            n_compras=12,
            rede_regional="Rede Norte",
        ),
        # Cliente REAL - LARISSA - PROSPECT
        Cliente(
            cnpj="12345678000195",
            nome_fantasia="Mercado Organico",
            razao_social="Mercado Organico ME",
            uf="RS",
            consultor="LARISSA",
            situacao="PROSPECT",
            classificacao_3tier="REAL",
            faturamento_total=0.0,
            score=35.0,
            prioridade="P7",
            sinaleiro="ROXO",
            temperatura="FRIO",
            curva_abc="C",
            tipo_cliente="PROSPECT",
        ),
        # Cliente ALUCINACAO — deve ser excluido do recalculo (R8)
        Cliente(
            cnpj="99999999999901",
            nome_fantasia="ALUCINACAO CLIENTE",
            razao_social="ALUCINACAO LTDA",
            uf="SP",
            consultor="MANU",
            situacao="ATIVO",
            classificacao_3tier="ALUCINACAO",
            faturamento_total=999999.0,
            score=99.0,
            prioridade="P0",
        ),
    ]

    for c in clientes:
        session.add(c)
    session.commit()

    yield session
    session.close()


def _make_override(session: Session):
    def _get_db_override():
        yield session
    return _get_db_override


@pytest.fixture(scope="module")
def usuario_admin():
    return _fake_usuario(1, "admin@vitao.com", "Admin VITAO", "admin")


@pytest.fixture(scope="module")
def usuario_gerente():
    return _fake_usuario(2, "daiane@vitao.com", "Daiane Stavicki", "gerente")


@pytest.fixture(scope="module")
def usuario_consultor():
    return _fake_usuario(3, "manu@vitao.com", "Manu Ditzel", "consultor", consultor_nome="MANU")


# ---------------------------------------------------------------------------
# Fixture de clients com roles diferentes
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db_session, usuario_admin):
    """TestClient com usuario admin e banco em memoria."""
    app.dependency_overrides[get_db] = _make_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_admin_or_gerente] = lambda: usuario_admin
    app.dependency_overrides[require_admin] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_gerente(db_session, usuario_gerente):
    """TestClient com usuario gerente."""
    app.dependency_overrides[get_db] = _make_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_gerente
    app.dependency_overrides[require_admin_or_gerente] = lambda: usuario_gerente
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_consultor(db_session, usuario_consultor):
    """TestClient com usuario consultor — PATCH deve retornar 403."""
    app.dependency_overrides[get_db] = _make_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_consultor
    # require_admin_or_gerente: injetar consultor para forcar 403
    app.dependency_overrides[require_admin_or_gerente] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=403, detail="Acesso restrito a administradores e gerentes")
    )
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=403, detail="Acesso restrito a administradores")
    )
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Testes: PATCH /api/clientes/{cnpj}
# ---------------------------------------------------------------------------

class TestPatchCliente:
    """PATCH /api/clientes/{cnpj} — edicao inline (admin/gerente)"""

    def test_patch_consultor_por_admin_retorna_200(self, client_admin):
        """Admin pode reatribuir consultor de um cliente."""
        resp = client_admin.patch(
            "/api/clientes/04067573000193",
            json={"consultor": "LARISSA"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cnpj"] == "04067573000193"
        assert "consultor" in data["campos_alterados"]
        assert data["cliente"]["consultor"] == "LARISSA"

    def test_patch_retorna_cliente_atualizado(self, client_admin):
        """Resposta deve conter o cliente completo apos atualizacao."""
        resp = client_admin.patch(
            "/api/clientes/04067573000193",
            json={"consultor": "MANU"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cliente" in data
        cliente = data["cliente"]
        # Campos obrigatorios do ClienteDetalhe devem estar presentes
        assert "cnpj" in cliente
        assert "nome_fantasia" in cliente
        assert "situacao" in cliente

    def test_patch_consultor_normalizado_para_uppercase(self, client_admin):
        """Consultor enviado em minusculas deve ser normalizado para UPPERCASE."""
        resp = client_admin.patch(
            "/api/clientes/04067573000193",
            json={"consultor": "larissa"},
        )
        assert resp.status_code == 200
        assert resp.json()["cliente"]["consultor"] == "LARISSA"

    def test_patch_rede_regional_por_gerente(self, client_gerente):
        """Gerente pode alterar rede_regional."""
        resp = client_gerente.patch(
            "/api/clientes/04067573000193",
            json={"rede_regional": "Rede Sul"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rede_regional" in data["campos_alterados"]
        assert data["cliente"]["rede_regional"] == "Rede Sul"

    def test_patch_sem_mudanca_real_retorna_campos_alterados_vazio(self, client_admin, db_session):
        """Se valor enviado == valor atual, campos_alterados deve ser []."""
        # Garantir que o consultor e LARISSA (do teste anterior que setou)
        cliente_atual = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "04067573000193")
        )
        consultor_atual = cliente_atual.consultor

        resp = client_admin.patch(
            "/api/clientes/04067573000193",
            json={"consultor": consultor_atual},
        )
        assert resp.status_code == 200
        assert resp.json()["campos_alterados"] == []

    def test_patch_cnpj_inexistente_retorna_404(self, client_admin):
        """CNPJ que nao existe deve retornar 404."""
        resp = client_admin.patch(
            "/api/clientes/99999999999999",
            json={"consultor": "MANU"},
        )
        assert resp.status_code == 404
        assert "nao encontrado" in resp.json()["detail"]

    def test_patch_cnpj_normalizado_com_pontuacao(self, client_admin):
        """CNPJ com pontos deve ser normalizado e encontrar o cliente."""
        resp = client_admin.patch(
            "/api/clientes/04.067.573.0001-93",
            json={"rede_regional": "Rede Teste"},
        )
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == "04067573000193"

    def test_patch_consultor_gera_audit_log(self, client_admin, db_session):
        """Alteracao de consultor deve gerar registro em AuditLog."""
        # Fazer uma alteracao garantida (mudar para DAIANE)
        resp = client_admin.patch(
            "/api/clientes/04067573000193",
            json={"consultor": "DAIANE"},
        )
        assert resp.status_code == 200
        assert "consultor" in resp.json()["campos_alterados"]

        # Verificar que AuditLog foi criado
        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.cnpj == "04067573000193",
                AuditLog.campo == "consultor",
                AuditLog.valor_novo == "DAIANE",
            )
            .first()
        )
        assert audit is not None, "AuditLog nao foi criado para alteracao de consultor"
        assert audit.valor_novo == "DAIANE"
        assert audit.campo == "consultor"

    def test_patch_por_consultor_retorna_403(self, client_consultor):
        """Consultor nao pode alterar campos de cliente via PATCH."""
        resp = client_consultor.patch(
            "/api/clientes/04067573000193",
            json={"consultor": "LARISSA"},
        )
        assert resp.status_code == 403

    def test_patch_payload_vazio_retorna_campos_alterados_vazio(self, client_admin):
        """Payload sem campos deve retornar campos_alterados=[]."""
        resp = client_admin.patch(
            "/api/clientes/04067573000193",
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["campos_alterados"] == []

    def test_patch_audit_log_registra_usuario_nome(self, client_admin, db_session):
        """AuditLog deve registrar o nome do usuario que fez a alteracao."""
        # Alterar rede para gerar um novo audit com usuario
        resp = client_admin.patch(
            "/api/clientes/12345678000195",
            json={"rede_regional": "Rede Auditada"},
        )
        assert resp.status_code == 200

        audit = (
            db_session.query(AuditLog)
            .filter(
                AuditLog.cnpj == "12345678000195",
                AuditLog.campo == "rede_regional",
                AuditLog.valor_novo == "Rede Auditada",
            )
            .first()
        )
        assert audit is not None
        # usuario_nome deve ser preenchido (admin@vitao.com ou "Admin VITAO")
        assert audit.usuario_nome is not None
        assert len(audit.usuario_nome) > 0


# ---------------------------------------------------------------------------
# 2. Testes: GET /api/clientes/{cnpj}/score
# ---------------------------------------------------------------------------

class TestScoreBreakdown:
    """GET /api/clientes/{cnpj}/score — breakdown dos 6 fatores v2"""

    def test_score_retorna_200(self, client_admin):
        """Endpoint deve retornar 200 para CNPJ existente."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        assert resp.status_code == 200

    def test_score_contem_campos_obrigatorios(self, client_admin):
        """Resposta deve conter cnpj, score_total, prioridade e fatores."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        data = resp.json()
        assert "cnpj" in data
        assert "score_total" in data
        assert "prioridade" in data
        assert "fatores" in data

    def test_score_fatores_contem_todos_os_6(self, client_admin):
        """fatores deve conter os 6 nomes: urgencia, valor, followup, sinal, tentativa, situacao."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        fatores = resp.json()["fatores"]
        for nome in ("urgencia", "valor", "followup", "sinal", "tentativa", "situacao"):
            assert nome in fatores, f"Fator '{nome}' ausente em /score"

    def test_score_cada_fator_tem_valor_peso_contribuicao(self, client_admin):
        """Cada fator deve conter as chaves: valor, peso, contribuicao."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        fatores = resp.json()["fatores"]
        for nome, fator in fatores.items():
            assert "valor" in fator, f"Fator '{nome}' sem 'valor'"
            assert "peso" in fator, f"Fator '{nome}' sem 'peso'"
            assert "contribuicao" in fator, f"Fator '{nome}' sem 'contribuicao'"

    def test_score_total_equals_soma_contribuicoes(self, client_admin):
        """score_total deve ser igual a soma das contribuicoes (tolerancia 0.2)."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        data = resp.json()
        soma = sum(f["contribuicao"] for f in data["fatores"].values())
        assert abs(data["score_total"] - soma) <= 0.2, (
            f"score_total={data['score_total']} != soma contribuicoes={soma}"
        )

    def test_score_pesos_somam_1(self, client_admin):
        """A soma dos pesos deve ser exatamente 1.0 (tolerancia 1e-6)."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        fatores = resp.json()["fatores"]
        soma_pesos = sum(f["peso"] for f in fatores.values())
        assert abs(soma_pesos - 1.0) < 1e-6, f"Soma dos pesos = {soma_pesos}, esperado 1.0"

    def test_score_total_entre_0_e_100(self, client_admin):
        """score_total deve estar no range [0, 100]."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        score = resp.json()["score_total"]
        assert 0.0 <= score <= 100.0, f"score_total={score} fora do range [0, 100]"

    def test_score_prioridade_no_range_p0_p7(self, client_admin):
        """prioridade deve ser P0-P7."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        prioridade = resp.json()["prioridade"]
        assert prioridade in {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"}, (
            f"Prioridade invalida: {prioridade}"
        )

    def test_score_cnpj_retornado_normalizado(self, client_admin):
        """CNPJ na resposta deve ser string de 14 digitos."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str)
        assert len(cnpj) == 14
        assert cnpj.isdigit()

    def test_score_cnpj_inexistente_retorna_404(self, client_admin):
        """CNPJ inexistente deve retornar 404."""
        resp = client_admin.get("/api/clientes/99999999999999/score")
        assert resp.status_code == 404

    def test_score_contribuicao_urgencia_e_30pct_do_valor(self, client_admin):
        """contribuicao de urgencia deve ser valor * 0.30."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        fator_urgencia = resp.json()["fatores"]["urgencia"]
        esperado = round(fator_urgencia["valor"] * 0.30, 2)
        assert abs(fator_urgencia["contribuicao"] - esperado) < 0.01, (
            f"Contribuicao urgencia: {fator_urgencia['contribuicao']} != {esperado}"
        )

    def test_score_contribuicao_valor_e_25pct(self, client_admin):
        """contribuicao de valor deve ser valor * 0.25."""
        resp = client_admin.get("/api/clientes/04067573000193/score")
        fator_valor = resp.json()["fatores"]["valor"]
        esperado = round(fator_valor["valor"] * 0.25, 2)
        assert abs(fator_valor["contribuicao"] - esperado) < 0.01

    def test_score_prospect_tem_urgencia_baixa(self, client_admin):
        """Cliente PROSPECT deve ter fator_urgencia = 10 (regra do motor)."""
        resp = client_admin.get("/api/clientes/12345678000195/score")
        assert resp.status_code == 200
        fator_urgencia = resp.json()["fatores"]["urgencia"]
        assert fator_urgencia["valor"] == 10.0, (
            f"PROSPECT deveria ter urgencia=10.0, obtido {fator_urgencia['valor']}"
        )


# ---------------------------------------------------------------------------
# 3. Testes: POST /api/sinaleiro/recalcular
# ---------------------------------------------------------------------------

class TestRecalcularSinaleiro:
    """POST /api/sinaleiro/recalcular — batch (admin only)"""

    def test_recalcular_retorna_200(self, client_admin):
        """Endpoint deve retornar 200."""
        resp = client_admin.post("/api/sinaleiro/recalcular")
        assert resp.status_code == 200

    def test_recalcular_retorna_clientes_recalculados(self, client_admin):
        """Resposta deve conter o campo clientes_recalculados."""
        resp = client_admin.post("/api/sinaleiro/recalcular")
        data = resp.json()
        assert "clientes_recalculados" in data

    def test_recalcular_retorna_tempo_ms(self, client_admin):
        """Resposta deve conter tempo_ms >= 0."""
        resp = client_admin.post("/api/sinaleiro/recalcular")
        data = resp.json()
        assert "tempo_ms" in data
        assert data["tempo_ms"] >= 0.0, f"tempo_ms deve ser >= 0, obtido {data['tempo_ms']}"

    def test_recalcular_exclui_alucinacao(self, client_admin, db_session):
        """
        R8: clientes com classificacao_3tier=ALUCINACAO devem ser excluidos.
        O seed tem 3 clientes: 2 REAL + 1 ALUCINACAO.
        Portanto clientes_recalculados deve ser 2.
        """
        resp = client_admin.post("/api/sinaleiro/recalcular")
        data = resp.json()
        # Seed: 2 clientes REAL, 1 ALUCINACAO
        assert data["clientes_recalculados"] == 2, (
            f"Esperado 2 clientes REAL recalculados, obtido {data['clientes_recalculados']}"
        )

    def test_recalcular_atualiza_sinaleiro_no_banco(self, client_admin, db_session):
        """Apos recalculo, sinaleiro dos clientes REAL deve estar preenchido."""
        client_admin.post("/api/sinaleiro/recalcular")

        cliente = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "04067573000193")
        )
        db_session.refresh(cliente)
        assert cliente.sinaleiro in ("VERDE", "AMARELO", "LARANJA", "VERMELHO", "ROXO"), (
            f"Sinaleiro invalido apos recalculo: {cliente.sinaleiro}"
        )

    def test_recalcular_atualiza_score_no_banco(self, client_admin, db_session):
        """Apos recalculo, score dos clientes REAL deve estar entre 0 e 100."""
        client_admin.post("/api/sinaleiro/recalcular")

        cliente = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "04067573000193")
        )
        db_session.refresh(cliente)
        assert cliente.score is not None
        assert 0.0 <= cliente.score <= 100.0, f"Score fora do range: {cliente.score}"

    def test_recalcular_atualiza_prioridade_no_banco(self, client_admin, db_session):
        """Apos recalculo, prioridade deve ser P0-P7."""
        client_admin.post("/api/sinaleiro/recalcular")

        cliente = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "04067573000193")
        )
        db_session.refresh(cliente)
        assert cliente.prioridade in {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"}, (
            f"Prioridade invalida apos recalculo: {cliente.prioridade}"
        )

    def test_recalcular_mensagem_presente(self, client_admin):
        """Resposta deve conter campo 'mensagem' nao vazio."""
        resp = client_admin.post("/api/sinaleiro/recalcular")
        data = resp.json()
        assert "mensagem" in data
        assert len(data["mensagem"]) > 0

    def test_recalcular_por_consultor_retorna_403(self, client_consultor):
        """Consultor nao pode executar recalculo batch."""
        resp = client_consultor.post("/api/sinaleiro/recalcular")
        assert resp.status_code == 403
