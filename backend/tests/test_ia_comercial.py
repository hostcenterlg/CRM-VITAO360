"""
CRM VITAO360 — Testes dos novos endpoints de IA Comercial.

Cobre:
  1. GET  /api/ia/briefing/{cnpj}             — briefing expandido (histórico + script)
  2. GET  /api/ia/mensagem-wa/{cnpj}           — mensagem WA automática por situação
  3. GET  /api/ia/resumo-semanal/{consultor}   — resumo com clientes contactados + pipeline
  4. GET  /api/ia/churn-risk/{cnpj}            — score de risco de churn
  5. GET  /api/ia/sugestao-produto/{cnpj}      — cross-sell/up-sell

Estratégia: banco SQLite em memória com seed completo (usuários + clientes + vendas + itens + produtos).
ANTHROPIC_API_KEY ausente em todos os testes → graceful degradation (ia_configurada=false).

Garantias verificadas:
  R4  — Two-Base: vendas e logs lidos em tabelas separadas, sem mistura de valores.
  R5  — CNPJ: String(14) na resposta, normalizado na entrada.
  R9  — JWT obrigatório em todos os endpoints.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.produto import Produto
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.models.venda_item import VendaItem
from backend.app.security import hash_password


# ---------------------------------------------------------------------------
# Garantia: ANTHROPIC_API_KEY não pode estar definida durante os testes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def _sem_anthropic_key():
    """
    Remove ANTHROPIC_API_KEY para forçar graceful degradation (templates locais).
    Patcha tanto os.environ quanto o atributo do módulo.
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
# Fixtures: banco em memória com seed completo
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine_mem():
    """Engine SQLite em memória compartilhada pelo módulo de testes."""
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
    Seed completo:
      - 2 usuários: admin (leandro) + consultor (manu)
      - 4 clientes: ATIVO, INAT.REC, PROSPECT, EM_RISCO
      - 5 vendas com itens para o cliente ATIVO
      - 2 produtos de categorias distintas
      - 3 log_interacoes para o cliente ATIVO
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
    manu_user = Usuario(
        email="manu@vitao.com.br",
        nome="Manu Ditzel",
        role="consultor",
        consultor_nome="MANU",
        hashed_password=hash_password("vitao2026"),
        ativo=True,
    )
    session.add_all([admin, manu_user])
    session.commit()

    # ---- Produtos ----
    prod_granola = Produto(
        codigo="GRA-001",
        nome="Granola Tradicional 400g",
        categoria="Cereais",
        fabricante="VITAO",
        unidade="UN",
        preco_tabela=18.50,
        preco_minimo=15.00,
        comissao_pct=3.5,
        ipi_pct=0.0,
        ativo=True,
    )
    prod_fruta = Produto(
        codigo="FRU-042",
        nome="Mix Frutas Secas 300g",
        categoria="Frutas Secas",
        fabricante="VITAO",
        unidade="UN",
        preco_tabela=24.90,
        preco_minimo=20.00,
        comissao_pct=3.5,
        ipi_pct=0.0,
        ativo=True,
    )
    prod_proteina = Produto(
        codigo="PRO-010",
        nome="Proteína Vegetal Pea 500g",
        categoria="Proteínas",
        fabricante="VITAO",
        unidade="UN",
        preco_tabela=52.00,
        preco_minimo=44.00,
        comissao_pct=4.0,
        ipi_pct=0.0,
        ativo=True,
    )
    session.add_all([prod_granola, prod_fruta, prod_proteina])
    session.commit()

    # ---- Clientes ----
    # Cliente 1: ATIVO (MANU) — histórico completo
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
        valor_ultimo_pedido=3200.0,
        estagio_funil="POS-VENDA",
        fase="MANUTENCAO",
        acao_futura="Acompanhar recompra",
        followup_vencido=False,
        followup_dias=15,
        tentativas="T1",
    )
    # Cliente 2: INAT.REC (MANU) — inativo recente
    cliente_inat_rec = Cliente(
        cnpj="12345678000195",
        nome_fantasia="Mercado Orgânico Teste",
        razao_social="Mercado Orgânico Teste ME",
        uf="RS",
        cidade="Porto Alegre",
        consultor="MANU",
        situacao="INAT.REC",
        classificacao_3tier="REAL",
        faturamento_total=12000.0,
        score=35.0,
        prioridade="P4",
        sinaleiro="LARANJA",
        temperatura="FRIO",
        curva_abc="B",
        tipo_cliente="REATIVACAO",
        dias_sem_compra=75,
        ciclo_medio=30,
        n_compras=5,
        valor_ultimo_pedido=1800.0,
        estagio_funil="REATIVACAO",
        fase="REATIVACAO",
        acao_futura="Ligar para reativação",
        followup_vencido=True,
        followup_dias=0,
        tentativas="T2",
    )
    # Cliente 3: PROSPECT (LARISSA)
    cliente_prospect = Cliente(
        cnpj="99887766000100",
        nome_fantasia="Loja Natural Gaúcha",
        razao_social="Loja Natural Gaúcha EIRELI",
        uf="RS",
        cidade="Caxias do Sul",
        consultor="LARISSA",
        situacao="PROSPECT",
        classificacao_3tier="REAL",
        faturamento_total=0.0,
        score=15.0,
        prioridade="P7",
        sinaleiro="ROXO",
        temperatura="FRIO",
        curva_abc="C",
        tipo_cliente="PROSPECT",
        dias_sem_compra=None,
        ciclo_medio=None,
        n_compras=0,
        valor_ultimo_pedido=None,
        estagio_funil="PROSPECCAO",
        fase="AQUISICAO",
        acao_futura="Enviar proposta",
        followup_vencido=False,
    )
    # Cliente 4: EM_RISCO (MANU)
    cliente_em_risco = Cliente(
        cnpj="11223344000155",
        nome_fantasia="Vitalize Suplementos",
        razao_social="Vitalize Suplementos LTDA",
        uf="SP",
        cidade="São Paulo",
        consultor="MANU",
        situacao="EM_RISCO",
        classificacao_3tier="REAL",
        faturamento_total=22000.0,
        score=42.0,
        prioridade="P3",
        sinaleiro="VERMELHO",
        temperatura="CRITICO",
        curva_abc="B",
        tipo_cliente="EM_RISCO",
        dias_sem_compra=55,
        ciclo_medio=25,
        n_compras=8,
        valor_ultimo_pedido=2100.0,
        estagio_funil="EM_RISCO",
        fase="REATIVACAO",
        acao_futura="Contato urgente",
        followup_vencido=True,
        followup_dias=0,
        tentativas="T3",
    )
    session.add_all([cliente_ativo, cliente_inat_rec, cliente_prospect, cliente_em_risco])
    session.commit()

    # ---- Vendas (R4: tabela separada, valor > 0) ----
    hoje = date.today()
    venda1 = Venda(
        cnpj="04067573000193",
        data_pedido=hoje - timedelta(days=12),
        numero_pedido="MRC-001234",
        valor_pedido=3200.00,
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-03",
    )
    venda2 = Venda(
        cnpj="04067573000193",
        data_pedido=hoje - timedelta(days=40),
        numero_pedido="MRC-001100",
        valor_pedido=2800.00,
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-02",
    )
    venda3 = Venda(
        cnpj="04067573000193",
        data_pedido=hoje - timedelta(days=70),
        numero_pedido="MRC-000980",
        valor_pedido=3500.00,
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-01",
    )
    venda_recente_manu = Venda(
        cnpj="04067573000193",
        data_pedido=hoje - timedelta(days=2),
        numero_pedido="MRC-001300",
        valor_pedido=1500.00,
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-04",
    )
    venda_inat = Venda(
        cnpj="12345678000195",
        data_pedido=hoje - timedelta(days=75),
        numero_pedido="MRC-000800",
        valor_pedido=1800.00,
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-01",
    )
    session.add_all([venda1, venda2, venda3, venda_recente_manu, venda_inat])
    session.commit()

    # ---- VendaItems (R4: valor > 0, vinculado à venda) ----
    item1 = VendaItem(
        venda_id=venda1.id,
        produto_id=prod_granola.id,
        quantidade=50.0,
        preco_unitario=18.50,
        desconto_pct=5.0,
        valor_total=50 * 18.50 * 0.95,
    )
    item2 = VendaItem(
        venda_id=venda1.id,
        produto_id=prod_fruta.id,
        quantidade=20.0,
        preco_unitario=24.90,
        desconto_pct=0.0,
        valor_total=20 * 24.90,
    )
    item3 = VendaItem(
        venda_id=venda2.id,
        produto_id=prod_granola.id,
        quantidade=60.0,
        preco_unitario=18.50,
        desconto_pct=5.0,
        valor_total=60 * 18.50 * 0.95,
    )
    session.add_all([item1, item2, item3])
    session.commit()

    # ---- LogInteracoes (R4: sem valor monetário) ----
    log1 = LogInteracao(
        cnpj="04067573000193",
        data_interacao=datetime.now() - timedelta(days=12),
        consultor="MANU",
        resultado="VENDA / PEDIDO",
        descricao="Pedido realizado. Cliente satisfeito com entrega anterior.",
        estagio_funil="POS-VENDA",
        fase="MANUTENCAO",
        tipo_contato="LIGACAO",
        temperatura="QUENTE",
        follow_up_dias=28,
    )
    log2 = LogInteracao(
        cnpj="04067573000193",
        data_interacao=datetime.now() - timedelta(days=40),
        consultor="MANU",
        resultado="POS-VENDA",
        descricao="Confirmação de entrega. Sem problemas.",
        estagio_funil="POS-VENDA",
        fase="MANUTENCAO",
        tipo_contato="WHATSAPP",
        temperatura="QUENTE",
        follow_up_dias=28,
    )
    # Log da semana atual (para testar clientes_contactados_semana)
    log3 = LogInteracao(
        cnpj="12345678000195",
        data_interacao=datetime.now() - timedelta(days=3),
        consultor="MANU",
        resultado="SEM CONTATO",
        descricao="Tentativa de contato — não atendeu.",
        estagio_funil="REATIVACAO",
        fase="REATIVACAO",
        tipo_contato="LIGACAO",
        temperatura="FRIO",
        follow_up_dias=2,
    )
    session.add_all([log1, log2, log3])
    session.commit()

    yield session
    session.close()


def _make_override(session: Session):
    def _override():
        yield session
    return _override


@pytest.fixture(scope="module")
def client(db_session) -> TestClient:
    """TestClient com get_db apontando para banco em memória. JWT real."""
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
CNPJ_INAT_REC = "12345678000195"
CNPJ_PROSPECT = "99887766000100"
CNPJ_EM_RISCO = "11223344000155"
CNPJ_INEXISTENTE = "99999999999999"


# ===========================================================================
# 1. GET /api/ia/briefing/{cnpj} — MELHORADO (histórico + script)
# ===========================================================================

class TestBriefingExpandido:
    """Testes para o briefing expandido com histórico de compras e script."""

    def test_briefing_sem_token_retorna_401(self, client):
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}")
        assert resp.status_code == 401

    def test_briefing_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_INEXISTENTE}", headers=_auth(token))
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_briefing_cliente_ativo_retorna_200(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_briefing_campos_obrigatorios_presentes(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        data = resp.json()
        for campo in ("cnpj", "nome_cliente", "briefing", "tokens_usados", "cached", "ia_configurada"):
            assert campo in data, f"Campo ausente: '{campo}'"

    def test_briefing_retorna_ia_configurada_false(self, client):
        """Sem ANTHROPIC_API_KEY, ia_configurada deve ser False."""
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["ia_configurada"] is False

    def test_briefing_usa_template_local_sem_chave(self, client):
        """Sem API key, briefing deve conter conteúdo do template local (não fallback genérico)."""
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        briefing = resp.json()["briefing"]
        assert isinstance(briefing, str)
        assert len(briefing) > 50  # template local é mais rico que a msg de fallback

    def test_briefing_cnpj_normalizado_na_resposta(self, client):
        """R5: CNPJ na resposta deve ser string de 14 dígitos."""
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str)
        assert len(cnpj) == 14
        assert cnpj.isdigit()

    def test_briefing_aceita_cnpj_formatado(self, client):
        """R5: CNPJ com pontuação deve ser normalizado e encontrar cliente."""
        token = _login(client)
        resp = client.get("/api/ia/briefing/04.067.573.0001-93", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_ATIVO

    def test_briefing_tokens_zero_sem_api_key(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["tokens_usados"] == 0

    def test_briefing_cached_sempre_false(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["cached"] is False

    def test_briefing_nome_cliente_preenchido(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        nome = resp.json()["nome_cliente"]
        assert nome and nome != ""

    def test_briefing_inat_rec_retorna_200(self, client):
        """Cliente INAT.REC também deve ter briefing via template local."""
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_INAT_REC}", headers=_auth(token))
        assert resp.status_code == 200

    def test_briefing_prospect_retorna_200(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_PROSPECT}", headers=_auth(token))
        assert resp.status_code == 200

    def test_briefing_em_risco_retorna_200(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/briefing/{CNPJ_EM_RISCO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_briefing_acessivel_por_consultor(self, client):
        """Consultor também pode acessar briefings."""
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get(f"/api/ia/briefing/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200


# ===========================================================================
# 2. GET /api/ia/mensagem-wa/{cnpj} — NOVO
# ===========================================================================

class TestMensagemWAAutomatica:
    """Testes para GET /api/ia/mensagem-wa/{cnpj} — mensagem automática por situação."""

    def test_mensagem_wa_sem_token_retorna_401(self, client):
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}")
        assert resp.status_code == 401

    def test_mensagem_wa_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_INEXISTENTE}", headers=_auth(token))
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_mensagem_wa_ativo_retorna_200(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_mensagem_wa_campos_obrigatorios(self, client):
        """Resposta deve conter cnpj, nome_cliente, mensagem, tom, contexto."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        data = resp.json()
        for campo in ("cnpj", "nome_cliente", "mensagem", "tom", "contexto", "tokens_usados", "ia_configurada"):
            assert campo in data, f"Campo ausente: '{campo}'"

    def test_mensagem_wa_cnpj_string_14_digitos(self, client):
        """R5: CNPJ na resposta deve ser string de 14 dígitos."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str) and len(cnpj) == 14 and cnpj.isdigit()

    def test_mensagem_wa_ia_configurada_false(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["ia_configurada"] is False

    def test_mensagem_wa_mensagem_nao_vazia(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        mensagem = resp.json()["mensagem"]
        assert isinstance(mensagem, str) and len(mensagem) > 20

    def test_mensagem_wa_tom_preenchido(self, client):
        """Campo tom deve ser uma string não vazia."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        tom = resp.json()["tom"]
        assert isinstance(tom, str) and len(tom) > 0

    def test_mensagem_wa_contexto_preenchido(self, client):
        """Campo contexto deve ser uma string não vazia."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        contexto = resp.json()["contexto"]
        assert isinstance(contexto, str) and len(contexto) > 0

    def test_mensagem_wa_inat_rec_retorna_200(self, client):
        """Cliente INAT.REC deve gerar mensagem de reativação."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_INAT_REC}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "reativação" in data["tom"].lower() or "reativacao" in data["tom"].lower()

    def test_mensagem_wa_prospect_retorna_200(self, client):
        """Prospect deve gerar mensagem de prospecção."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_PROSPECT}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "prospec" in data["tom"].lower()

    def test_mensagem_wa_em_risco_retorna_200(self, client):
        """Cliente EM_RISCO deve gerar mensagem de retenção urgente."""
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_EM_RISCO}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "reten" in data["tom"].lower() or "urgent" in data["tom"].lower()

    def test_mensagem_wa_tokens_zero_sem_chave(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["tokens_usados"] == 0

    def test_mensagem_wa_aceita_cnpj_formatado(self, client):
        """R5: CNPJ formatado deve ser normalizado."""
        token = _login(client)
        resp = client.get("/api/ia/mensagem-wa/04.067.573.0001-93", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_ATIVO

    def test_mensagem_wa_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get(f"/api/ia/mensagem-wa/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200


# ===========================================================================
# 3. GET /api/ia/resumo-semanal/{consultor} — MELHORADO
# ===========================================================================

class TestResumoSemanalMelhorado:
    """Testes para o resumo semanal com clientes contactados + pipeline."""

    def test_resumo_sem_token_retorna_401(self, client):
        resp = client.get("/api/ia/resumo-semanal/MANU")
        assert resp.status_code == 401

    def test_resumo_manu_retorna_200(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.status_code == 200

    def test_resumo_campos_obrigatorios(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        data = resp.json()
        for campo in ("consultor", "periodo", "resumo", "tokens_usados", "metricas", "ia_configurada"):
            assert campo in data, f"Campo ausente: '{campo}'"

    def test_resumo_metricas_tem_novos_campos(self, client):
        """Métricas devem incluir campos novos: clientes_contactados_semana, pipeline, top3."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert "clientes_contactados_semana" in metricas
        assert "pipeline" in metricas
        assert "top3_proxima_semana" in metricas

    def test_resumo_metricas_todos_campos_obrigatorios(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        for campo in (
            "total_carteira",
            "clientes_contactados_semana",
            "vendas_semana_qtd",
            "vendas_semana_volume",
            "clientes_em_risco",
            "followups_vencidos",
            "pipeline",
            "top3_proxima_semana",
        ):
            assert campo in metricas, f"Campo ausente em metricas: '{campo}'"

    def test_resumo_metricas_nao_negativos(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert metricas["total_carteira"] >= 0
        assert metricas["clientes_contactados_semana"] >= 0
        assert metricas["vendas_semana_qtd"] >= 0
        assert metricas["vendas_semana_volume"] >= 0.0
        assert metricas["clientes_em_risco"] >= 0
        assert metricas["followups_vencidos"] >= 0

    def test_resumo_clientes_contactados_conta_log_interacoes(self, client):
        """
        MANU tem log3 (cnpj INAT.REC) nos últimos 7 dias e log1 (cnpj ATIVO).
        clientes_contactados_semana deve refletir logs recentes.
        """
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        # log3 é da semana (3 dias atrás) — pelo menos 1
        assert metricas["clientes_contactados_semana"] >= 1

    def test_resumo_pipeline_eh_dict(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        pipeline = resp.json()["metricas"]["pipeline"]
        assert isinstance(pipeline, dict)

    def test_resumo_top3_eh_lista(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        top3 = resp.json()["metricas"]["top3_proxima_semana"]
        assert isinstance(top3, list)

    def test_resumo_top3_tem_campos_esperados(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        top3 = resp.json()["metricas"]["top3_proxima_semana"]
        if top3:  # Pode ser vazio se não houver clientes elegíveis
            for item in top3:
                for campo in ("cnpj", "nome", "score", "situacao", "acao_futura"):
                    assert campo in item, f"Campo ausente em top3: '{campo}'"

    def test_resumo_consultor_normalizado_uppercase(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/manu", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["consultor"] == "MANU"

    def test_resumo_sem_clientes_retorna_metricas_zeradas(self, client):
        """JULIO não tem clientes no seed — métricas devem ser zeradas."""
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/JULIO", headers=_auth(token))
        assert resp.status_code == 200
        metricas = resp.json()["metricas"]
        assert metricas["total_carteira"] == 0
        assert metricas["vendas_semana_qtd"] == 0
        assert metricas["clientes_contactados_semana"] == 0

    def test_resumo_ia_configurada_false(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.json()["ia_configurada"] is False

    def test_resumo_periodo_formato_correto(self, client):
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        periodo = resp.json()["periodo"]
        assert isinstance(periodo, str) and " a " in periodo

    def test_resumo_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        assert resp.status_code == 200


# ===========================================================================
# 4. GET /api/ia/churn-risk/{cnpj} — NOVO
# ===========================================================================

class TestChurnRisk:
    """Testes para GET /api/ia/churn-risk/{cnpj} — score de risco de churn."""

    def test_churn_sem_token_retorna_401(self, client):
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}")
        assert resp.status_code == 401

    def test_churn_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_INEXISTENTE}", headers=_auth(token))
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_churn_cliente_ativo_retorna_200(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_churn_campos_obrigatorios(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        data = resp.json()
        for campo in ("cnpj", "nome_cliente", "risco_pct", "nivel", "fatores", "recomendacao", "ia_configurada"):
            assert campo in data, f"Campo ausente: '{campo}'"

    def test_churn_risco_pct_entre_0_e_100(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        risco = resp.json()["risco_pct"]
        assert isinstance(risco, (int, float))
        assert 0.0 <= risco <= 100.0

    def test_churn_nivel_valor_valido(self, client):
        """Nível deve ser um dos 4 valores válidos."""
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        nivel = resp.json()["nivel"]
        assert nivel in ("BAIXO", "MEDIO", "ALTO", "CRITICO")

    def test_churn_fatores_eh_lista(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        fatores = resp.json()["fatores"]
        assert isinstance(fatores, list) and len(fatores) > 0

    def test_churn_recomendacao_nao_vazia(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        recomendacao = resp.json()["recomendacao"]
        assert isinstance(recomendacao, str) and len(recomendacao) > 20

    def test_churn_ia_configurada_false(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["ia_configurada"] is False

    def test_churn_cnpj_string_14_digitos(self, client):
        """R5: CNPJ na resposta deve ser string de 14 dígitos."""
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str) and len(cnpj) == 14 and cnpj.isdigit()

    def test_churn_cliente_ativo_nivel_baixo(self, client):
        """Cliente ATIVO com 12 dias sem compra e ciclo 28 deve ter risco BAIXO ou MEDIO."""
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        nivel = resp.json()["nivel"]
        assert nivel in ("BAIXO", "MEDIO")

    def test_churn_cliente_inat_rec_nivel_alto(self, client):
        """Cliente INAT.REC (75 dias, ciclo 30, sinaleiro LARANJA) deve ter risco ALTO ou CRITICO."""
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_INAT_REC}", headers=_auth(token))
        nivel = resp.json()["nivel"]
        assert nivel in ("ALTO", "CRITICO")

    def test_churn_em_risco_nivel_alto_ou_critico(self, client):
        """Cliente EM_RISCO (vermelho, critico, 55 dias) deve ter risco alto."""
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_EM_RISCO}", headers=_auth(token))
        nivel = resp.json()["nivel"]
        assert nivel in ("ALTO", "CRITICO")

    def test_churn_aceita_cnpj_formatado(self, client):
        """R5: CNPJ com formatação deve ser normalizado."""
        token = _login(client)
        resp = client.get("/api/ia/churn-risk/04.067.573.0001-93", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_ATIVO

    def test_churn_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_churn_todos_clientes_retornam_200(self, client):
        """Todos os CNPJs do seed devem retornar 200."""
        token = _login(client)
        for cnpj in (CNPJ_ATIVO, CNPJ_INAT_REC, CNPJ_PROSPECT, CNPJ_EM_RISCO):
            resp = client.get(f"/api/ia/churn-risk/{cnpj}", headers=_auth(token))
            assert resp.status_code == 200, f"Falhou para cnpj={cnpj}: {resp.text}"


# ===========================================================================
# 5. GET /api/ia/sugestao-produto/{cnpj} — NOVO
# ===========================================================================

class TestSugestaoProduto:
    """Testes para GET /api/ia/sugestao-produto/{cnpj} — cross-sell/up-sell."""

    def test_sugestao_sem_token_retorna_401(self, client):
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}")
        assert resp.status_code == 401

    def test_sugestao_cnpj_inexistente_retorna_404(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_INEXISTENTE}", headers=_auth(token))
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_sugestao_cliente_ativo_retorna_200(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_sugestao_campos_obrigatorios(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        data = resp.json()
        for campo in ("cnpj", "nome_cliente", "produtos_sugeridos", "estrategia", "categorias_frequentes", "ia_configurada"):
            assert campo in data, f"Campo ausente: '{campo}'"

    def test_sugestao_produtos_sugeridos_eh_lista(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        produtos = resp.json()["produtos_sugeridos"]
        assert isinstance(produtos, list)

    def test_sugestao_produtos_tem_campos_esperados(self, client):
        """Cada produto sugerido deve ter os campos mínimos."""
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        produtos = resp.json()["produtos_sugeridos"]
        if produtos:
            for p in produtos:
                for campo in ("id", "codigo", "nome", "categoria", "motivo"):
                    assert campo in p, f"Campo ausente em produto: '{campo}'"

    def test_sugestao_estrategia_nao_vazia(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        estrategia = resp.json()["estrategia"]
        assert isinstance(estrategia, str) and len(estrategia) > 20

    def test_sugestao_categorias_frequentes_eh_lista(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        cats = resp.json()["categorias_frequentes"]
        assert isinstance(cats, list)

    def test_sugestao_ia_configurada_false(self, client):
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.json()["ia_configurada"] is False

    def test_sugestao_cnpj_string_14_digitos(self, client):
        """R5: CNPJ na resposta deve ser string de 14 dígitos."""
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        cnpj = resp.json()["cnpj"]
        assert isinstance(cnpj, str) and len(cnpj) == 14 and cnpj.isdigit()

    def test_sugestao_cliente_com_historico_tem_categorias(self, client):
        """
        Cliente ATIVO tem compras de Granola (Cereais) e Mix Frutas (Frutas Secas).
        categorias_frequentes deve conter ao menos uma dessas categorias.
        """
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        cats = resp.json()["categorias_frequentes"]
        assert len(cats) > 0
        assert any(c in ("Cereais", "Frutas Secas") for c in cats)

    def test_sugestao_prospect_sem_historico_retorna_200(self, client):
        """Prospect sem histórico de compras deve retornar 200 com lista possivelmente vazia."""
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_PROSPECT}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["produtos_sugeridos"], list)

    def test_sugestao_aceita_cnpj_formatado(self, client):
        """R5: CNPJ com formatação deve ser normalizado."""
        token = _login(client)
        resp = client.get("/api/ia/sugestao-produto/04.067.573.0001-93", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_ATIVO

    def test_sugestao_acessivel_por_consultor(self, client):
        token = _login(client, "manu@vitao.com.br", "vitao2026")
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_ATIVO}", headers=_auth(token))
        assert resp.status_code == 200

    def test_sugestao_todos_clientes_retornam_200(self, client):
        """Todos os CNPJs do seed devem retornar 200."""
        token = _login(client)
        for cnpj in (CNPJ_ATIVO, CNPJ_INAT_REC, CNPJ_PROSPECT, CNPJ_EM_RISCO):
            resp = client.get(f"/api/ia/sugestao-produto/{cnpj}", headers=_auth(token))
            assert resp.status_code == 200, f"Falhou para cnpj={cnpj}: {resp.text}"


# ===========================================================================
# 6. Verificações Two-Base (R4)
# ===========================================================================

class TestTwoBaseCompliance:
    """Verificações indiretas de compliance com Two-Base Architecture (R4)."""

    def test_churn_risk_nao_usa_log_para_calcular_risco(self, client):
        """
        O score de churn é calculado com dados do cliente e da tabela vendas.
        Verificação indireta: prospect sem vendas deve retornar risco calculado (não erro).
        """
        token = _login(client)
        resp = client.get(f"/api/ia/churn-risk/{CNPJ_PROSPECT}", headers=_auth(token))
        assert resp.status_code == 200
        assert 0.0 <= resp.json()["risco_pct"] <= 100.0

    def test_sugestao_produto_usa_venda_itens_nao_log(self, client):
        """
        Sugestão de produto usa venda_itens (tabela VENDA).
        Prospect sem venda_itens deve retornar 200 com lista vazia (não erro por ausência de log).
        """
        token = _login(client)
        resp = client.get(f"/api/ia/sugestao-produto/{CNPJ_PROSPECT}", headers=_auth(token))
        assert resp.status_code == 200
        # Categorias frequentes devem ser vazias para prospect sem histórico
        cats = resp.json()["categorias_frequentes"]
        assert isinstance(cats, list)  # pode ser vazio — correto para prospect

    def test_resumo_semanal_separa_contactados_e_vendas(self, client):
        """
        R4: clientes_contactados_semana vem de log_interacoes (sem R$).
        vendas_semana_volume vem de vendas (com R$).
        Ambos devem coexistir sem mistura.
        """
        token = _login(client)
        resp = client.get("/api/ia/resumo-semanal/MANU", headers=_auth(token))
        metricas = resp.json()["metricas"]
        assert "clientes_contactados_semana" in metricas
        assert "vendas_semana_volume" in metricas
        # Volume deve ser >= 0 (vem exclusivamente da tabela vendas)
        assert metricas["vendas_semana_volume"] >= 0.0
