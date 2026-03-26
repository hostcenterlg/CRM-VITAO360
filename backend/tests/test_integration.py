"""
CRM VITAO360 — Testes de integração dos endpoints críticos.

Estratégia: banco SQLite em memória com seed completo (usuários + regras do
motor + clientes de teste). Nenhum override de dependency — os endpoints
passam pelo fluxo real de JWT, get_db, e motor_service.

Cobertura:
  1. Fluxo de Login completo (POST /api/auth/login, GET /api/auth/me)
  2. Fluxo de Atendimento — núcleo operacional (POST /api/atendimentos)
     - Inclui verificação Two-Base: LogInteracao não tem campo de valor R$
  3. Dashboard — KPIs, distribuição, top10, performance
  4. Agenda — listagem por consultor, geração (admin)
  5. Motor — listagem de regras, filtro por situação
  6. CNPJ normalização — busca com e sem pontuação
  7. Score v2 — range 0-100, prioridade P0-P7

R4  — Two-Base: LogInteracao criada por atendimento NUNCA tem valor monetário.
R5  — CNPJ: String(14), zero-padded.
R9  — Autenticação JWT validada em todos os testes que exigem token.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.agenda import AgendaItem
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.regra_motor import RegraMotor
from backend.app.models.usuario import Usuario
from backend.app.security import hash_password


# ---------------------------------------------------------------------------
# Fixtures: banco em memória + seed completo
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine_mem():
    """Engine SQLite em memória compartilhada por todos os testes do módulo."""
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
    """
    Sessão com seed completo:
      - 2 usuários: admin (leandro) + consultor (manu)
      - 2 clientes VITAO360 com campos de inteligência preenchidos
      - 3 regras do motor (ATIVO|VENDA / PEDIDO, ATIVO|NÃO ATENDE, PROSPECT|CADASTRO)
      - 1 item de agenda para MANU
    """
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    # ---- Usuários ----
    admin = Usuario(
        email="leandro@vitao.com.br",
        nome="Leandro",
        role="admin",
        consultor_nome=None,
        hashed_password=hash_password("vitao2026"),
        ativo=True,
    )
    manu = Usuario(
        email="manu@vitao.com.br",
        nome="Manu Ditzel",
        role="consultor",
        consultor_nome="MANU",
        hashed_password=hash_password("vitao2026"),
        ativo=True,
    )
    session.add_all([admin, manu])
    session.commit()

    # ---- Clientes ----
    cliente_a = Cliente(
        cnpj="04067573000193",
        nome_fantasia="Empório Natural A",
        razao_social="Empório Natural A LTDA",
        uf="SC",
        cidade="Florianópolis",
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
    )
    cliente_b = Cliente(
        cnpj="12345678000195",
        nome_fantasia="Mercado Orgânico B",
        razao_social="Mercado Orgânico B ME",
        uf="RS",
        cidade="Porto Alegre",
        consultor="MANU",
        situacao="PROSPECT",
        classificacao_3tier="REAL",
        faturamento_total=0.0,
        score=35.0,
        prioridade="P7",
        sinaleiro="ROXO",
        temperatura="FRIO",
        curva_abc="C",
        tipo_cliente="PROSPECT",
        dias_sem_compra=None,
        ciclo_medio=None,
        n_compras=0,
    )
    session.add_all([cliente_a, cliente_b])
    session.commit()

    # ---- Regras do Motor ----
    regras = [
        RegraMotor(
            situacao="ATIVO",
            resultado="VENDA / PEDIDO",
            estagio_funil="POS-VENDA",
            fase="MANUTENCAO",
            tipo_contato="Visita",
            acao_futura="Acompanhar pedido",
            temperatura="QUENTE",
            follow_up_dias=45,
            grupo_dash="FUNIL",
            tipo_acao="VENDA",
            chave="ATIVO|VENDA / PEDIDO",
        ),
        RegraMotor(
            situacao="ATIVO",
            resultado="NÃO ATENDE",
            estagio_funil="MANUTENCAO",
            fase="REATIVACAO",
            tipo_contato="Ligacao",
            acao_futura="Tentar novamente",
            temperatura="FRIO",
            follow_up_dias=1,
            grupo_dash="NÃO VENDA",
            tipo_acao="NAO_VENDA",
            chave="ATIVO|NÃO ATENDE",
        ),
        RegraMotor(
            situacao="PROSPECT",
            resultado="CADASTRO",
            estagio_funil="PROSPECCAO",
            fase="AQUISICAO",
            tipo_contato="Email",
            acao_futura="Enviar proposta",
            temperatura="MORNO",
            follow_up_dias=2,
            grupo_dash="FUNIL",
            tipo_acao="AQUISICAO",
            chave="PROSPECT|CADASTRO",
        ),
    ]
    session.add_all(regras)
    session.commit()

    # ---- Agenda ----
    from datetime import date
    agenda_item = AgendaItem(
        cnpj="04067573000193",
        consultor="MANU",
        data_agenda=date(2026, 3, 25),
        posicao=1,
        nome_fantasia="Empório Natural A",
        situacao="ATIVO",
        temperatura="QUENTE",
        score=82.5,
        prioridade="P2",
        sinaleiro="VERDE",
        acao="Ligar para fechamento",
        followup_dias=45,
    )
    session.add(agenda_item)
    session.commit()

    yield session
    session.close()


def _make_override(session: Session):
    def _override():
        yield session
    return _override


@pytest.fixture(scope="module")
def client(db_session) -> TestClient:
    """
    TestClient com get_db apontando para o banco em memória.
    Autenticação JWT permanece real — sem override de get_current_user.
    """
    app.dependency_overrides[get_db] = _make_override(db_session)
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str = "leandro@vitao.com.br", senha: str = "vitao2026") -> str:
    """Faz login e retorna o access_token."""
    resp = client.post("/api/auth/login", json={"email": email, "senha": senha})
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Fluxo de Login
# ---------------------------------------------------------------------------

class TestLoginFluxo:
    """POST /api/auth/login e GET /api/auth/me"""

    def test_login_credenciais_corretas_retorna_200_e_token(self, client):
        resp = client.post("/api/auth/login", json={"email": "leandro@vitao.com.br", "senha": "vitao2026"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_senha_errada_retorna_401(self, client):
        resp = client.post("/api/auth/login", json={"email": "leandro@vitao.com.br", "senha": "senhaerrada"})
        assert resp.status_code == 401

    def test_login_email_inexistente_retorna_401(self, client):
        resp = client.post("/api/auth/login", json={"email": "naoexiste@vitao.com.br", "senha": "vitao2026"})
        assert resp.status_code == 401

    def test_me_com_token_valido_retorna_200_e_dados_usuario(self, client):
        token = _login(client)
        resp = client.get("/api/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "leandro@vitao.com.br"
        assert data["nome"] == "Leandro"
        assert data["role"] == "admin"

    def test_me_sem_token_retorna_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_token_invalido_retorna_401(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer tokeninvalido123"})
        assert resp.status_code == 401

    def test_login_consultor_retorna_token_com_dados_corretos(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get("/api/auth/me", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["consultor_nome"] == "MANU"
        assert data["role"] == "consultor"


# ---------------------------------------------------------------------------
# 2. Fluxo de Atendimento — núcleo operacional
# ---------------------------------------------------------------------------

class TestAtendimentoFluxo:
    """POST /api/atendimentos — fluxo crítico com Motor de Regras"""

    def test_registrar_atendimento_valido_retorna_201(self, client):
        token = _login(client)
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "04067573000193",
                "resultado": "VENDA / PEDIDO",
                "descricao": "Pedido fechado via WhatsApp",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201

    def test_motor_processa_e_retorna_estagio_funil(self, client):
        token = _login(client)
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "04067573000193",
                "resultado": "VENDA / PEDIDO",
                "descricao": "Teste motor",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "motor" in data
        motor = data["motor"]
        assert "estagio_funil" in motor
        assert "temperatura" in motor
        assert "fase" in motor
        assert "follow_up_dias" in motor

    def test_two_base_log_nao_tem_campo_valor_monetario(self, client, db_session):
        """
        R4 — Two-Base Architecture: LogInteracao NUNCA deve ter campo de valor R$.
        Verifica diretamente no model que os campos monetários não existem.
        """
        log = db_session.query(LogInteracao).first()
        assert log is not None, "Esperado ao menos um log após registrar atendimentos"
        # O model LogInteracao não deve ter nenhum atributo monetário
        atributos_monetarios = ["valor", "valor_pedido", "faturamento", "receita", "preco"]
        for attr in atributos_monetarios:
            assert not hasattr(log, attr), (
                f"Two-Base violada: LogInteracao tem atributo monetário '{attr}'"
            )

    def test_atendimento_sem_resultado_retorna_422(self, client):
        token = _login(client)
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "04067573000193",
                "descricao": "Faltou resultado",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_atendimento_resultado_invalido_retorna_400(self, client):
        token = _login(client)
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "04067573000193",
                "resultado": "RESULTADO_INEXISTENTE",
                "descricao": "Teste resultado inválido",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_atendimento_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "99999999999999",
                "resultado": "VENDA / PEDIDO",
                "descricao": "CNPJ que não existe",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_atendimento_sem_autenticacao_retorna_401(self, client):
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "04067573000193",
                "resultado": "VENDA / PEDIDO",
                "descricao": "Sem token",
            },
        )
        assert resp.status_code == 401

    def test_motor_temperatura_presente_no_resultado(self, client):
        token = _login(client)
        resp = client.post(
            "/api/atendimentos",
            json={
                "cnpj": "04067573000193",
                "resultado": "NÃO ATENDE",
                "descricao": "Não atendeu",
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        motor = resp.json()["motor"]
        assert motor["temperatura"] in ("QUENTE", "MORNO", "FRIO", "CRITICO")


# ---------------------------------------------------------------------------
# 3. Dashboard — KPIs, distribuição, top10, performance
# ---------------------------------------------------------------------------

class TestDashboard:
    """GET /api/dashboard/kpis, /distribuicao, /top10, /performance"""

    def test_kpis_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/kpis", headers=_auth(token))
        assert resp.status_code == 200

    def test_kpis_total_clientes_maior_que_zero(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/kpis", headers=_auth(token))
        data = resp.json()
        assert data["total_clientes"] > 0

    def test_kpis_campos_obrigatorios_presentes(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/kpis", headers=_auth(token))
        data = resp.json()
        campos = [
            "total_clientes", "total_ativos", "total_prospects",
            "total_inativos", "faturamento_total", "media_score",
            "clientes_alerta", "clientes_criticos", "followups_vencidos",
        ]
        for campo in campos:
            assert campo in data, f"Campo '{campo}' ausente em /kpis"

    def test_kpis_sem_token_retorna_401(self, client):
        resp = client.get("/api/dashboard/kpis")
        assert resp.status_code == 401

    def test_distribuicao_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/distribuicao", headers=_auth(token))
        assert resp.status_code == 200

    def test_distribuicao_por_sinaleiro_retorna_lista(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/distribuicao", headers=_auth(token))
        data = resp.json()
        assert "por_sinaleiro" in data
        assert isinstance(data["por_sinaleiro"], list)
        assert len(data["por_sinaleiro"]) >= 1

    def test_distribuicao_itens_tem_label_count_pct(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/distribuicao", headers=_auth(token))
        data = resp.json()
        for item in data["por_sinaleiro"]:
            assert "label" in item
            assert "count" in item
            assert "pct" in item

    def test_top10_retorna_lista(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/top10", headers=_auth(token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_top10_maximo_10_itens(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/top10", headers=_auth(token))
        assert len(resp.json()) <= 10

    def test_performance_retorna_4_consultores(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/performance", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        consultores = [item["consultor"] for item in data]
        assert set(consultores) == {"MANU", "LARISSA", "DAIANE", "JULIO"}

    def test_performance_campos_obrigatorios_presentes(self, client):
        token = _login(client)
        resp = client.get("/api/dashboard/performance", headers=_auth(token))
        for item in resp.json():
            assert "consultor" in item
            assert "territorio" in item
            assert "faturamento_real" in item
            assert "meta_2026" in item
            assert "pct_atingimento" in item
            assert "status" in item


# ---------------------------------------------------------------------------
# 4. Agenda — listagem por consultor e geração
# ---------------------------------------------------------------------------

class TestAgenda:
    """GET /api/agenda/{consultor} e POST /api/agenda/gerar"""

    def test_agenda_consultor_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/agenda/MANU", headers=_auth(token))
        assert resp.status_code == 200

    def test_agenda_consultor_retorna_campos_score_e_prioridade(self, client):
        token = _login(client)
        resp = client.get("/api/agenda/MANU", headers=_auth(token))
        data = resp.json()
        assert "consultor" in data
        assert "total" in data
        assert "itens" in data
        # Com o seed, MANU tem 1 item de agenda
        if data["total"] > 0:
            item = data["itens"][0]
            assert "score" in item
            assert "prioridade" in item

    def test_agenda_consultor_uppercase_insensitive(self, client):
        """Consultor em minúsculas deve ser normalizado para maiúsculas."""
        token = _login(client)
        resp = client.get("/api/agenda/manu", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["consultor"] == "MANU"

    def test_agenda_sem_token_retorna_401(self, client):
        resp = client.get("/api/agenda/MANU")
        assert resp.status_code == 401

    def test_gerar_agenda_admin_retorna_200(self, client):
        token = _login(client)
        resp = client.post(
            "/api/agenda/gerar",
            params={"data": "2026-03-25"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "por_consultor" in data
        assert "total" in data

    def test_gerar_agenda_consultor_sem_permissao_retorna_403(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.post(
            "/api/agenda/gerar",
            params={"data": "2026-03-25"},
            headers=_auth(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 5. Motor de Regras
# ---------------------------------------------------------------------------

class TestMotor:
    """GET /api/motor/regras — admin only"""

    def test_regras_retorna_200_e_total(self, client):
        token = _login(client)
        resp = client.get("/api/motor/regras", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert data["total"] >= 3  # seed tem 3 regras

    def test_regras_filtro_situacao_ativo(self, client):
        token = _login(client)
        resp = client.get("/api/motor/regras", params={"situacao": "ATIVO"}, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        for regra in data["regras"]:
            assert regra["situacao"] == "ATIVO"

    def test_regras_filtro_situacao_retorna_apenas_correspondentes(self, client):
        token = _login(client)
        resp = client.get("/api/motor/regras", params={"situacao": "PROSPECT"}, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for regra in data["regras"]:
            assert regra["situacao"] == "PROSPECT"

    def test_regras_filtro_situacao_inexistente_retorna_vazio(self, client):
        token = _login(client)
        resp = client.get("/api/motor/regras", params={"situacao": "SITUACAO_FANTASMA"}, headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_regras_consultor_sem_permissao_retorna_403(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get("/api/motor/regras", headers=_auth(token))
        assert resp.status_code == 403

    def test_regras_campos_obrigatorios_presentes(self, client):
        token = _login(client)
        resp = client.get("/api/motor/regras", headers=_auth(token))
        regra = resp.json()["regras"][0]
        campos = [
            "id", "situacao", "resultado", "estagio_funil", "fase",
            "tipo_contato", "acao_futura", "temperatura", "followup_dias", "chave",
        ]
        for campo in campos:
            assert campo in regra, f"Campo '{campo}' ausente em regras do motor"


# ---------------------------------------------------------------------------
# 6. CNPJ — normalização automática (R5)
# ---------------------------------------------------------------------------

class TestCnpjNormalizacao:
    """GET /api/clientes/{cnpj} — normalização de pontuação (R5)"""

    def test_busca_cnpj_sem_pontuacao_encontra_cliente(self, client):
        token = _login(client)
        resp = client.get("/api/clientes/04067573000193", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == "04067573000193"

    def test_busca_cnpj_com_pontos_e_hifen_normaliza_e_encontra(self, client):
        """
        R5: CNPJ '04.067.573.0001-93' (pontos e hífen, sem barra) deve ser
        normalizado para '04067573000193' via re.sub(r'\\D', '', cnpj).zfill(14).

        Nota: barra '/' no path param é limitação de roteamento HTTP (splits URL).
        Este teste cobre a normalização de pontuação real que chega nas requisições
        de frontends que formatam o CNPJ com pontos e hífen.
        """
        token = _login(client)
        # CNPJ com pontos e hífen mas sem barra — forma comum enviada pelo frontend
        resp = client.get("/api/clientes/04.067.573.0001-93", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == "04067573000193"

    def test_busca_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.get("/api/clientes/99999999999999", headers=_auth(token))
        assert resp.status_code == 404

    def test_cnpj_no_retorno_sempre_string_14_digitos(self, client):
        """R5: CNPJ na resposta deve ser string de exatamente 14 caracteres numéricos."""
        token = _login(client)
        resp = client.get("/api/clientes/04067573000193", headers=_auth(token))
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str), "CNPJ deve ser string, nunca float"
        assert len(cnpj) == 14, f"CNPJ deve ter 14 dígitos, tem {len(cnpj)}"
        assert cnpj.isdigit(), "CNPJ deve conter apenas dígitos"


# ---------------------------------------------------------------------------
# 7. Score v2 — validação de range e prioridade
# ---------------------------------------------------------------------------

class TestScoreV2:
    """GET /api/clientes/{cnpj} — score entre 0-100, prioridade P0-P7"""

    def test_score_esta_entre_0_e_100(self, client):
        token = _login(client)
        resp = client.get("/api/clientes/04067573000193", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        if data["score"] is not None:
            assert 0.0 <= data["score"] <= 100.0, (
                f"Score fora do range 0-100: {data['score']}"
            )

    def test_prioridade_esta_no_range_p0_p7(self, client):
        token = _login(client)
        resp = client.get("/api/clientes/04067573000193", headers=_auth(token))
        data = resp.json()
        if data["prioridade"] is not None:
            prioridades_validas = {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"}
            assert data["prioridade"] in prioridades_validas, (
                f"Prioridade inválida: {data['prioridade']}"
            )

    def test_listagem_clientes_retorna_score_e_prioridade(self, client):
        token = _login(client)
        resp = client.get("/api/clientes", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        for cliente in data["registros"]:
            if cliente["score"] is not None:
                assert 0.0 <= cliente["score"] <= 100.0

    def test_score_prospect_menor_que_score_ativo(self, client):
        """
        Regra de negócio: clientes ATIVO com histórico devem ter score
        maior que PROSPECT sem compras.
        """
        token = _login(client)
        resp_a = client.get("/api/clientes/04067573000193", headers=_auth(token))
        resp_b = client.get("/api/clientes/12345678000195", headers=_auth(token))
        score_ativo = resp_a.json().get("score") or 0.0
        score_prospect = resp_b.json().get("score") or 0.0
        assert score_ativo >= score_prospect, (
            f"Esperado score ATIVO ({score_ativo}) >= PROSPECT ({score_prospect})"
        )
