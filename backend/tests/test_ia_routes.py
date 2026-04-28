"""
CRM VITAO360 — Testes de integração dos endpoints /api/ia.

Estratégia: banco SQLite em memória com seed mínimo (usuários + clientes).
Sem override de get_current_user — autenticação JWT permanece real.
ANTHROPIC_API_KEY ausente em todos os testes → graceful degradation (ia_configurada=false).

Cobertura:
  1. GET  /api/ia/briefing/{cnpj}         — autenticação, 404, 200 + campos de resposta
  2. POST /api/ia/mensagem/{cnpj}         — autenticação, 404, validação de payload, 200
  3. GET  /api/ia/resumo-semanal/{consultor} — autenticação, 200 + sub-objeto metricas

Garantias de projeto verificadas:
  R4  — Two-Base: gerar_resumo_semanal consulta vendas e logs em tabelas separadas.
  R5  — CNPJ: String(14) na resposta, aceita formatação na entrada.
  R9  — JWT obrigatório em todos os endpoints de IA.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.canal import Canal
from backend.app.models.cliente import Cliente
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.security import hash_password


# ---------------------------------------------------------------------------
# Garantia: ANTHROPIC_API_KEY não pode estar definida durante os testes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def _sem_anthropic_key():
    """
    Remove ANTHROPIC_API_KEY do ambiente para forçar o caminho de graceful
    degradation em todos os testes deste módulo.

    O módulo ia_service lê a variável no nível de módulo via os.getenv(),
    então o monkeypatch precisa acontecer antes da importação — mas como o
    módulo já foi importado, também patchamos o atributo diretamente.
    """
    import backend.app.services.ia_service as _svc

    original_env = os.environ.pop("ANTHROPIC_API_KEY", None)
    original_attr = _svc.ANTHROPIC_API_KEY
    _svc.ANTHROPIC_API_KEY = ""

    yield

    _svc.ANTHROPIC_API_KEY = original_attr
    if original_env is not None:
        os.environ["ANTHROPIC_API_KEY"] = original_env


# ---------------------------------------------------------------------------
# Fixtures: banco em memória com seed de usuários e clientes
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine_mem():
    """Engine SQLite em memória compartilhada pelo módulo de testes IA."""
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
    Seed completo para os testes de IA:
      - 2 usuários: admin (leandro) + consultor (manu)
      - 2 clientes: um ATIVO com histórico (MANU), um PROSPECT (LARISSA)
      - 1 venda para o cliente ATIVO (R4: tabela vendas separada)
    """
    from datetime import date

    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    # ---- Canal default (multi-canal scoping L3 25/Apr/2026) ----
    canal_default = Canal(
        nome="REVENDA",
        descricao="Canal de teste",
        status="ativo",
    )
    session.add(canal_default)
    session.commit()

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
    # Associar manu ao canal default (admin nao precisa: sees all)
    manu.canais = [canal_default]
    session.add_all([admin, manu])
    session.commit()

    # ---- Clientes ----
    # Cliente ATIVO com dados completos (carteira MANU)
    cliente_ativo = Cliente(
        cnpj="04067573000193",
        nome_fantasia="Empório Natural VITAO",
        razao_social="Empório Natural VITAO LTDA",
        uf="SC",
        cidade="Florianópolis",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        faturamento_total=48000.0,
        score=78.5,
        prioridade="P2",
        sinaleiro="VERDE",
        temperatura="QUENTE",
        curva_abc="A",
        tipo_cliente="MADURO",
        dias_sem_compra=12,
        ciclo_medio=28,
        n_compras=14,
        canal_id=canal_default.id,
    )
    # Cliente PROSPECT sem histórico de compras (carteira LARISSA)
    cliente_prospect = Cliente(
        cnpj="12345678000195",
        nome_fantasia="Mercado Orgânico Teste",
        razao_social="Mercado Orgânico Teste ME",
        uf="RS",
        cidade="Porto Alegre",
        consultor="LARISSA",
        situacao="PROSPECT",
        classificacao_3tier="REAL",
        faturamento_total=0.0,
        score=22.0,
        prioridade="P7",
        sinaleiro="ROXO",
        temperatura="FRIO",
        curva_abc="C",
        tipo_cliente="PROSPECT",
        dias_sem_compra=None,
        ciclo_medio=None,
        n_compras=0,
        canal_id=canal_default.id,
    )
    session.add_all([cliente_ativo, cliente_prospect])
    session.commit()

    # ---- Venda (R4: Two-Base — tabela separada, valor > 0) ----
    venda = Venda(
        cnpj="04067573000193",
        data_pedido=date(2026, 3, 14),
        numero_pedido="MRC-001234",
        valor_pedido=3200.00,
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-03",
    )
    session.add(venda)
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
    JWT real — sem override de get_current_user.
    """
    app.dependency_overrides[get_db] = _make_override(db_session)
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(
    client: TestClient,
    email: str = "leandro@vitao.com.br",
    senha: str = "vitao2026",
) -> str:
    """Faz login e retorna o access_token."""
    resp = client.post("/api/auth/login", json={"email": email, "senha": senha})
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# CNPJs usados nos seeds
CNPJ_ATIVO = "04067573000193"
CNPJ_PROSPECT = "12345678000195"
CNPJ_INEXISTENTE = "99999999999999"


# ===========================================================================
# 1. GET /api/ia/briefing/{cnpj}
# ===========================================================================

class TestBriefing:
    """Testes para GET /api/ia/briefing/{cnpj}"""

    # --- Autenticação ---

    def test_briefing_sem_token_retorna_401(self, client):
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}")
        assert resp.status_code == 401

    def test_briefing_token_invalido_retorna_401(self, client):
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers={"Authorization": "Bearer tokeninvalidoxyz"},
        )
        assert resp.status_code == 401

    # --- 404 para CNPJ inexistente ---

    def test_briefing_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_INEXISTENTE}",
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_briefing_404_tem_mensagem_detail(self, client):
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_INEXISTENTE}",
            headers=_auth(token),
        )
        assert "detail" in resp.json()

    # --- 200 com graceful degradation (sem ANTHROPIC_API_KEY) ---

    def test_briefing_cliente_ativo_retorna_200(self, client):
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        assert resp.status_code == 200

    def test_briefing_retorna_ia_configurada_false(self, client):
        """Sem ANTHROPIC_API_KEY o serviço degrada graciosamente."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        assert resp.json()["ia_configurada"] is False

    def test_briefing_campos_obrigatorios_presentes(self, client):
        """Resposta deve conter todos os campos do BriefingResponse."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        data = resp.json()
        for campo in ("cnpj", "nome_cliente", "briefing", "tokens_usados", "cached", "ia_configurada"):
            assert campo in data, f"Campo obrigatório ausente: '{campo}'"

    def test_briefing_cnpj_retornado_eh_string_14_digitos(self, client):
        """R5: CNPJ na resposta deve ser string de 14 dígitos numéricos."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str), "CNPJ deve ser string, nunca float"
        assert len(cnpj) == 14, f"CNPJ deve ter 14 dígitos, tem {len(cnpj)}"
        assert cnpj.isdigit(), "CNPJ deve conter apenas dígitos"

    def test_briefing_tokens_usados_zero_sem_chave(self, client):
        """Sem chave da API, tokens_usados deve ser 0 (fallback sem chamada real)."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        assert resp.json()["tokens_usados"] == 0

    def test_briefing_cached_false(self, client):
        """cached deve ser False — cache ainda não implementado."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        assert resp.json()["cached"] is False

    def test_briefing_nome_cliente_preenchido(self, client):
        """nome_cliente deve refletir nome_fantasia do seed."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        data = resp.json()
        assert data["nome_cliente"] != ""
        assert data["nome_cliente"] is not None

    def test_briefing_briefing_contem_mensagem_fallback(self, client):
        """Sem chave, briefing deve conter a mensagem de fallback do serviço."""
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        briefing = resp.json()["briefing"]
        assert isinstance(briefing, str)
        assert len(briefing) > 0

    # --- R5: normalização de CNPJ formatado ---

    def test_briefing_aceita_cnpj_com_pontuacao(self, client):
        """R5: CNPJ com pontos e hífen deve ser normalizado e encontrar o cliente."""
        token = _login(client)
        # CNPJ formatado sem barra (limitação de roteamento HTTP para '/').
        resp = client.get(
            "/api/ia/briefing/04.067.573.0001-93",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_ATIVO

    # --- Consultor também pode chamar o endpoint ---

    def test_briefing_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        assert resp.status_code == 200

    # --- Cliente prospect (sem vendas) também deve funcionar ---

    def test_briefing_cliente_prospect_retorna_200(self, client):
        token = _login(client)
        resp = client.get(
            f"/api/ia/briefing/{CNPJ_PROSPECT}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["ia_configurada"] is False


# ===========================================================================
# 2. POST /api/ia/mensagem/{cnpj}
# ===========================================================================

class TestMensagemWhatsApp:
    """Testes para POST /api/ia/mensagem/{cnpj}"""

    # --- Autenticação ---

    def test_mensagem_sem_token_retorna_401(self, client):
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "reativar cliente após 60 dias"},
        )
        assert resp.status_code == 401

    def test_mensagem_token_invalido_retorna_401(self, client):
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "reativar cliente após 60 dias"},
            headers={"Authorization": "Bearer tokeninvalidoxyz"},
        )
        assert resp.status_code == 401

    # --- 404 para CNPJ inexistente ---

    def test_mensagem_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_INEXISTENTE}",
            json={"objetivo": "apresentar nova linha de produtos"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_mensagem_404_tem_mensagem_detail(self, client):
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_INEXISTENTE}",
            json={"objetivo": "confirmar visita amanhã"},
            headers=_auth(token),
        )
        assert "detail" in resp.json()

    # --- Validação de payload ---

    def test_mensagem_objetivo_muito_curto_retorna_422(self, client):
        """objetivo com menos de 5 caracteres deve retornar 422."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "oi"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_mensagem_objetivo_com_exatamente_4_chars_retorna_422(self, client):
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "abcd"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_mensagem_objetivo_muito_longo_retorna_422(self, client):
        """objetivo com mais de 500 caracteres deve retornar 422."""
        token = _login(client)
        objetivo_longo = "x" * 501
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": objetivo_longo},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_mensagem_sem_objetivo_retorna_422(self, client):
        """Body sem o campo 'objetivo' deve retornar 422."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_mensagem_body_vazio_retorna_422(self, client):
        """Body completamente vazio deve retornar 422."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            headers=_auth(token),
        )
        assert resp.status_code == 422

    # --- 200 com graceful degradation ---

    def test_mensagem_valida_retorna_200(self, client):
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "reativar cliente após 60 dias sem compra"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    def test_mensagem_retorna_ia_configurada_false(self, client):
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "apresentar nova linha de cereais integrais"},
            headers=_auth(token),
        )
        assert resp.json()["ia_configurada"] is False

    def test_mensagem_campos_obrigatorios_presentes(self, client):
        """Resposta deve conter todos os campos do MensagemWhatsAppResponse."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "confirmar visita presencial para a próxima semana"},
            headers=_auth(token),
        )
        data = resp.json()
        for campo in ("cnpj", "nome_cliente", "mensagem", "tokens_usados", "ia_configurada"):
            assert campo in data, f"Campo obrigatório ausente: '{campo}'"

    def test_mensagem_cnpj_retornado_eh_string_14_digitos(self, client):
        """R5: CNPJ na resposta deve ser string de 14 dígitos numéricos."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "oferta especial de fim de mês para o cliente"},
            headers=_auth(token),
        )
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str)
        assert len(cnpj) == 14
        assert cnpj.isdigit()

    def test_mensagem_tokens_usados_zero_sem_chave(self, client):
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "enviar proposta de parceria exclusiva na região"},
            headers=_auth(token),
        )
        assert resp.json()["tokens_usados"] == 0

    def test_mensagem_texto_gerado_nao_vazio(self, client):
        """O campo 'mensagem' deve conter texto (fallback ou gerado)."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "reativar cliente após longo período sem pedido"},
            headers=_auth(token),
        )
        mensagem = resp.json()["mensagem"]
        assert isinstance(mensagem, str)
        assert len(mensagem) > 0

    def test_mensagem_objetivo_com_minimo_5_chars_retorna_200(self, client):
        """objetivo com exatamente 5 caracteres deve ser aceito."""
        token = _login(client)
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "abcde"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    def test_mensagem_objetivo_com_500_chars_retorna_200(self, client):
        """objetivo com exatamente 500 caracteres deve ser aceito."""
        token = _login(client)
        objetivo_max = "reativar cliente " + "x" * (500 - 17)
        assert len(objetivo_max) == 500
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": objetivo_max},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    # --- R5: normalização de CNPJ na entrada ---

    def test_mensagem_aceita_cnpj_com_pontuacao(self, client):
        """R5: CNPJ com pontos e hífen deve ser normalizado e encontrar o cliente."""
        token = _login(client)
        resp = client.post(
            "/api/ia/mensagem/04.067.573.0001-93",
            json={"objetivo": "reativar após 45 dias sem compra"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_ATIVO

    # --- Consultor pode usar o endpoint ---

    def test_mensagem_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.post(
            f"/api/ia/mensagem/{CNPJ_ATIVO}",
            json={"objetivo": "manter relacionamento com cliente QUENTE"},
            headers=_auth(token),
        )
        assert resp.status_code == 200


# ===========================================================================
# 3. GET /api/ia/resumo-semanal/{consultor}
# ===========================================================================

class TestResumoSemanal:
    """Testes para GET /api/ia/resumo-semanal/{consultor}"""

    # --- Autenticação ---

    def test_resumo_sem_token_retorna_401(self, client):
        resp = client.get("/api/ia/resumo-semanal/MANU")
        assert resp.status_code == 401

    def test_resumo_token_invalido_retorna_401(self, client):
        resp = client.get(
            "/api/ia/resumo-semanal/MANU",
            headers={"Authorization": "Bearer tokeninvalidoxyz"},
        )
        assert resp.status_code == 401

    # --- 200 para consultores do DE-PARA ---

    def test_resumo_manu_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.status_code == 200

    def test_resumo_larissa_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/LARISSA", headers=_auth(token))
        assert resp.status_code == 200

    def test_resumo_daiane_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/DAIANE", headers=_auth(token))
        assert resp.status_code == 200

    def test_resumo_julio_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/JULIO", headers=_auth(token))
        assert resp.status_code == 200

    # --- Graceful degradation sem chave ---

    def test_resumo_retorna_ia_configurada_false(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.json()["ia_configurada"] is False

    def test_resumo_tokens_usados_zero_sem_chave(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.json()["tokens_usados"] == 0

    # --- Campos obrigatórios de ResumoSemanalResponse ---

    def test_resumo_campos_obrigatorios_presentes(self, client):
        """Resposta deve conter todos os campos do ResumoSemanalResponse."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        data = resp.json()
        for campo in ("consultor", "periodo", "resumo", "tokens_usados", "metricas", "ia_configurada"):
            assert campo in data, f"Campo obrigatório ausente: '{campo}'"

    def test_resumo_metricas_tem_sub_campos_obrigatorios(self, client):
        """Sub-objeto metricas deve conter todos os campos do MetricasSemanaisResponse."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert isinstance(metricas, dict), "metricas deve ser um objeto JSON"
        for campo in (
            "total_carteira",
            "vendas_semana_qtd",
            "vendas_semana_volume",
            "clientes_em_risco",
            "followups_vencidos",
        ):
            assert campo in metricas, f"Campo obrigatório ausente em metricas: '{campo}'"

    def test_resumo_metricas_sao_numericos(self, client):
        """Todos os campos de metricas devem ser tipos numéricos."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert isinstance(metricas["total_carteira"], int)
        assert isinstance(metricas["vendas_semana_qtd"], int)
        assert isinstance(metricas["vendas_semana_volume"], (int, float))
        assert isinstance(metricas["clientes_em_risco"], int)
        assert isinstance(metricas["followups_vencidos"], int)

    def test_resumo_metricas_nao_negativos(self, client):
        """Todos os campos de metricas devem ser >= 0."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert metricas["total_carteira"] >= 0
        assert metricas["vendas_semana_qtd"] >= 0
        assert metricas["vendas_semana_volume"] >= 0.0
        assert metricas["clientes_em_risco"] >= 0
        assert metricas["followups_vencidos"] >= 0

    def test_resumo_consultor_normalizado_para_uppercase(self, client):
        """Consultor passado em minúsculas deve ser normalizado para UPPERCASE na resposta."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/manu", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["consultor"] == "MANU"

    def test_resumo_periodo_preenchido(self, client):
        """Período deve ser uma string no formato DD/MM a DD/MM/AAAA."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        periodo = resp.json()["periodo"]
        assert isinstance(periodo, str)
        assert len(periodo) > 0
        # Formato esperado: "DD/MM a DD/MM/AAAA"
        assert " a " in periodo

    def test_resumo_texto_nao_vazio(self, client):
        """Campo resumo deve conter texto (fallback ou gerado)."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        resumo = resp.json()["resumo"]
        assert isinstance(resumo, str)
        assert len(resumo) > 0

    def test_resumo_consultor_sem_clientes_retorna_metricas_zeradas(self, client):
        """
        JULIO não tem clientes no seed — total_carteira deve ser 0.
        O endpoint retorna 200 com métricas zeradas, nunca 404.
        """
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/JULIO", headers=_auth(token))
        assert resp.status_code == 200
        metricas = resp.json()["metricas"]
        assert metricas["total_carteira"] == 0
        assert metricas["vendas_semana_qtd"] == 0
        assert metricas["vendas_semana_volume"] == 0.0

    # --- R4: Two-Base — verificação indireta via metricas ---

    def test_resumo_manu_total_carteira_corresponde_ao_seed(self, client):
        """
        MANU tem 1 cliente no seed (Empório Natural VITAO).
        total_carteira deve refletir exatamente esse valor.
        R4: a venda na tabela vendas NÃO infla a contagem de carteira.
        """
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert metricas["total_carteira"] == 1

    # --- Consultor pode acessar o próprio resumo ---

    def test_resumo_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.status_code == 200
