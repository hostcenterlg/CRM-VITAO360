"""
CRM VITAO360 — Testes FR-022: Redistribuicao de Carteira.

Cobertura:
  1. GET /api/clientes/por-consultor
     - Retorna lista com consultor, total, faturamento
     - Faturamento e float (R4 — Two-Base: apenas registros VENDA)
     - Requer autenticacao (401 sem token)

  2. PATCH /api/clientes/redistribuir
     - Redistribuicao valida por admin (200)
     - Retorna total_processados, total_atualizados, erros
     - Consultor destino invalido retorna 422
     - CNPJ nao encontrado vai para lista de erros (nao aborta lote)
     - CNPJ ja com consultor destino e contado sem gerar audit duplicado
     - role=consultor retorna 403 (require_admin)
     - CNPJ normalizado: pontuacao removida, zero-padded (R5)
     - Alteracao gera registro em AuditLog (R12)
     - Payload vazio (cnpjs=[]) processa 0 e retorna sem erro

R4  — Two-Base: faturamento_total vem apenas de registros VENDA.
R5  — CNPJ: String(14), zero-padded, sem pontuacao.
R8  — Dados ALUCINACAO nao devem ser redistribuidos (clientes ficam disponiveis;
       a validacao de alucinacao e responsabilidade do operador).
R12 — Audit log registrado para cada alteracao real de consultor.
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
# Fixtures de banco e sessao
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
    """Sessao com seed de clientes para cobrir todos os cenarios FR-022."""
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    clientes = [
        # MANU — SC — ATIVO — faturamento alto
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
            curva_abc="A",
        ),
        # MANU — PR — ATIVO
        Cliente(
            cnpj="11222333000181",
            nome_fantasia="Natural Market PR",
            razao_social="Natural Market PR LTDA",
            uf="PR",
            consultor="MANU",
            situacao="ATIVO",
            classificacao_3tier="REAL",
            faturamento_total=18000.0,
            score=60.0,
            prioridade="P4",
            sinaleiro="AMARELO",
            curva_abc="B",
        ),
        # LARISSA — SP — PROSPECT
        Cliente(
            cnpj="22333444000155",
            nome_fantasia="Bio Saudavel SP",
            razao_social="Bio Saudavel ME",
            uf="SP",
            consultor="LARISSA",
            situacao="PROSPECT",
            classificacao_3tier="REAL",
            faturamento_total=0.0,
            score=35.0,
            prioridade="P7",
            sinaleiro="ROXO",
            curva_abc="C",
        ),
        # DAIANE — SP — ATIVO
        Cliente(
            cnpj="33444555000122",
            nome_fantasia="Rede Organica SP",
            razao_social="Rede Organica LTDA",
            uf="SP",
            consultor="DAIANE",
            situacao="ATIVO",
            classificacao_3tier="REAL",
            faturamento_total=120000.0,
            score=95.0,
            prioridade="P0",
            sinaleiro="VERDE",
            curva_abc="A",
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
    return _fake_usuario(10, "admin@vitao.com", "Admin VITAO", "admin")


@pytest.fixture(scope="module")
def usuario_consultor():
    return _fake_usuario(30, "manu@vitao.com", "Manu Ditzel", "consultor", consultor_nome="MANU")


# ---------------------------------------------------------------------------
# Fixtures de TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db_session, usuario_admin):
    app.dependency_overrides[get_db] = _make_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_admin] = lambda: usuario_admin
    app.dependency_overrides[require_admin_or_gerente] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_consultor(db_session, usuario_consultor):
    app.dependency_overrides[get_db] = _make_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_consultor
    # NAO sobrescreve require_admin — deve retornar 403
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Testes: GET /api/clientes/por-consultor
# ---------------------------------------------------------------------------

class TestPorConsultor:
    def test_retorna_lista_com_consultores(self, client_admin):
        """Deve retornar lista com pelo menos MANU, LARISSA e DAIANE."""
        res = client_admin.get("/api/clientes/por-consultor")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        consultores = [r["consultor"] for r in data]
        assert "MANU" in consultores
        assert "LARISSA" in consultores
        assert "DAIANE" in consultores

    def test_campos_obrigatorios(self, client_admin):
        """Cada item deve ter consultor, total e faturamento."""
        res = client_admin.get("/api/clientes/por-consultor")
        assert res.status_code == 200
        for item in res.json():
            assert "consultor" in item
            assert "total" in item
            assert "faturamento" in item
            assert isinstance(item["total"], int)
            assert isinstance(item["faturamento"], float)

    def test_faturamento_nao_negativo(self, client_admin):
        """Faturamento deve ser >= 0 para todos os consultores (R4 — Two-Base)."""
        res = client_admin.get("/api/clientes/por-consultor")
        assert res.status_code == 200
        for item in res.json():
            assert item["faturamento"] >= 0.0

    def test_total_correto_para_manu(self, client_admin):
        """MANU deve ter 2 clientes no seed."""
        res = client_admin.get("/api/clientes/por-consultor")
        assert res.status_code == 200
        manu = next((r for r in res.json() if r["consultor"] == "MANU"), None)
        assert manu is not None
        assert manu["total"] == 2
        # Faturamento MANU: 45000 + 18000 = 63000
        assert abs(manu["faturamento"] - 63000.0) < 1.0

    def test_sem_autenticacao_retorna_401(self, db_session):
        """Sem override de auth — deve retornar 401."""
        # Limpa overrides para simular request sem token
        app.dependency_overrides.clear()
        app.dependency_overrides[get_db] = _make_override(db_session)
        client_sem_auth = TestClient(app, raise_server_exceptions=False)
        res = client_sem_auth.get("/api/clientes/por-consultor")
        assert res.status_code == 401
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Testes: PATCH /api/clientes/redistribuir
# ---------------------------------------------------------------------------

class TestRedistribuirCarteira:
    def test_redistribuicao_valida(self, client_admin, db_session):
        """Admin redistribui cliente de MANU para LARISSA — 200 com totais corretos."""
        cnpj_alvo = "04067573000193"

        # Garantir que o cliente esta com MANU antes do teste
        cliente = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_alvo))
        if cliente and cliente.consultor != "MANU":
            cliente.consultor = "MANU"
            db_session.commit()

        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [cnpj_alvo], "novo_consultor": "LARISSA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_processados"] == 1
        assert data["total_atualizados"] == 1
        assert data["erros"] == []

        # Verificar banco atualizado
        db_session.expire_all()
        cliente_atualizado = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_alvo))
        assert cliente_atualizado is not None
        assert cliente_atualizado.consultor == "LARISSA"

        # Restaurar para outros testes
        cliente_atualizado.consultor = "MANU"
        db_session.commit()

    def test_audit_log_gerado(self, client_admin, db_session):
        """Cada alteracao de consultor deve gerar um registro em AuditLog."""
        cnpj_alvo = "11222333000181"

        # Garantir estado inicial
        cliente = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_alvo))
        if cliente and cliente.consultor != "MANU":
            cliente.consultor = "MANU"
            db_session.commit()

        # Contar audits antes
        audits_antes = db_session.query(AuditLog).filter(
            AuditLog.cnpj == cnpj_alvo, AuditLog.campo == "consultor"
        ).count()

        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [cnpj_alvo], "novo_consultor": "DAIANE"},
        )
        assert res.status_code == 200

        db_session.expire_all()
        # Deve ter exatamente +1 audit
        audits_depois = db_session.query(AuditLog).filter(
            AuditLog.cnpj == cnpj_alvo, AuditLog.campo == "consultor"
        ).count()
        assert audits_depois == audits_antes + 1

        # Verificar conteudo do ultimo audit
        ultimo_audit = (
            db_session.query(AuditLog)
            .filter(AuditLog.cnpj == cnpj_alvo, AuditLog.campo == "consultor")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert ultimo_audit is not None
        assert ultimo_audit.valor_anterior == "MANU"
        assert ultimo_audit.valor_novo == "DAIANE"

        # Restaurar
        cliente_atual = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_alvo))
        if cliente_atual:
            cliente_atual.consultor = "MANU"
            db_session.commit()

    def test_cnpj_nao_encontrado_vai_para_erros(self, client_admin):
        """CNPJ inexistente deve aparecer em erros sem abortar o lote."""
        cnpj_invalido = "00000000000000"
        cnpj_valido = "04067573000193"

        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [cnpj_valido, cnpj_invalido], "novo_consultor": "LARISSA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_processados"] == 2
        # cnpj_invalido vai para erros
        assert len(data["erros"]) == 1
        assert cnpj_invalido in data["erros"][0]

    def test_consultor_invalido_retorna_422(self, client_admin):
        """Consultor destino nao pertencente ao DE-PARA deve retornar 422."""
        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": ["04067573000193"], "novo_consultor": "RODRIGO"},
        )
        assert res.status_code == 422
        assert "invalido" in res.json()["detail"].lower()

    def test_role_consultor_retorna_403(self, client_consultor):
        """Consultor nao pode redistribuir carteira — require_admin."""
        res = client_consultor.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": ["04067573000193"], "novo_consultor": "LARISSA"},
        )
        assert res.status_code == 403

    def test_cnpj_com_pontuacao_normalizado(self, client_admin, db_session):
        """CNPJ com pontuacao deve ser normalizado para 14 digitos (R5)."""
        # CNPJ formatado: 04.067.573/0001-93
        cnpj_formatado = "04.067.573/0001-93"
        cnpj_normalizado = "04067573000193"

        # Garantir estado inicial
        cliente = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_normalizado))
        if cliente and cliente.consultor != "MANU":
            cliente.consultor = "MANU"
            db_session.commit()

        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [cnpj_formatado], "novo_consultor": "JULIO"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_processados"] == 1
        assert data["total_atualizados"] == 1
        assert data["erros"] == []

        # Restaurar
        db_session.expire_all()
        cliente_atual = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_normalizado))
        if cliente_atual:
            cliente_atual.consultor = "MANU"
            db_session.commit()

    def test_cnpj_ja_com_destino_nao_duplica_audit(self, client_admin, db_session):
        """Quando consultor ja e o destino, deve ser contado como atualizado sem novo audit."""
        cnpj_alvo = "33444555000122"  # DAIANE

        audits_antes = db_session.query(AuditLog).filter(
            AuditLog.cnpj == cnpj_alvo, AuditLog.campo == "consultor"
        ).count()

        # Redistribuir para DAIANE (ja e DAIANE)
        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [cnpj_alvo], "novo_consultor": "DAIANE"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_processados"] == 1
        assert data["total_atualizados"] == 1  # Contado mas sem mudanca real
        assert data["erros"] == []

        db_session.expire_all()
        # Sem novo audit pois o valor ja era DAIANE
        audits_depois = db_session.query(AuditLog).filter(
            AuditLog.cnpj == cnpj_alvo, AuditLog.campo == "consultor"
        ).count()
        assert audits_depois == audits_antes

    def test_payload_vazio_retorna_zeros(self, client_admin):
        """Lista vazia de CNPJs deve retornar totais zerados sem erro."""
        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [], "novo_consultor": "LARISSA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_processados"] == 0
        assert data["total_atualizados"] == 0
        assert data["erros"] == []

    def test_lote_multiplos_cnpjs(self, client_admin, db_session):
        """Redistribuicao em lote: varios CNPJs de uma vez."""
        cnpjs = ["04067573000193", "11222333000181"]

        # Garantir estado MANU
        for cnpj in cnpjs:
            c = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj))
            if c and c.consultor != "MANU":
                c.consultor = "MANU"
        db_session.commit()

        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": cnpjs, "novo_consultor": "LARISSA"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_processados"] == 2
        assert data["total_atualizados"] == 2
        assert data["erros"] == []

        # Verificar banco
        db_session.expire_all()
        for cnpj in cnpjs:
            c = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj))
            assert c is not None
            assert c.consultor == "LARISSA"

        # Restaurar
        for cnpj in cnpjs:
            c = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj))
            if c:
                c.consultor = "MANU"
        db_session.commit()

    def test_novo_consultor_case_insensitive(self, client_admin, db_session):
        """Consultor em lowercase deve ser normalizado para uppercase."""
        cnpj_alvo = "04067573000193"

        # Garantir MANU
        cliente = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_alvo))
        if cliente and cliente.consultor != "MANU":
            cliente.consultor = "MANU"
            db_session.commit()

        res = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [cnpj_alvo], "novo_consultor": "larissa"},
        )
        assert res.status_code == 200

        db_session.expire_all()
        cliente_atual = db_session.scalar(select(Cliente).where(Cliente.cnpj == cnpj_alvo))
        assert cliente_atual is not None
        assert cliente_atual.consultor == "LARISSA"

        # Restaurar
        cliente_atual.consultor = "MANU"
        db_session.commit()
