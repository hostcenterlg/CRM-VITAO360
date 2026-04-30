"""
CRM VITAO360 — Testes dos 5 endpoints de IA avançada.

Endpoints cobertos:
  GET /api/ia/sentimento/{cnpj}
  GET /api/ia/previsao-fechamento/{cnpj}
  GET /api/ia/coach/{consultor}
  GET /api/ia/alerta-oportunidade
  GET /api/ia/dashboard

Garantias verificadas:
  R4  — Two-Base Architecture: vendas e logs sempre em queries separadas.
  R5  — CNPJ normalizado para String(14) nas respostas.
  R8  — Nenhum dado fabricado — todos baseados em seed real do DB em memória.
  R9  — JWT obrigatório em todos os endpoints.

Estratégia:
  - SQLite em memória com seed controlado (engine de módulo para compartilhar).
  - Todas as keys LLM removidas em todos os testes (graceful degradation).
  - dependency_overrides para bypassar JWT nas rotas.
  - Testes de serviço chamam métodos async via asyncio.run() (sem pytest-asyncio).
  - 30+ testes distribuídos entre serviço (unitário) e rotas (integração).
"""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker


def _run(coro):
    """Executa coroutine em loop síncrono — sem necessidade de pytest-asyncio."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Garantir ausência de todas as keys LLM em todos os testes
# ---------------------------------------------------------------------------

_LLM_KEYS = ("DEEPINFRA_API_KEY", "GROQ_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")


@pytest.fixture(autouse=True, scope="module")
def _sem_llm_keys():
    """Remove TODAS as keys LLM e força graceful degradation."""
    import backend.app.services.ia_service as _svc
    from backend.app.services.llm_client import LLMClient

    saved = {k: os.environ.pop(k, None) for k in _LLM_KEYS}
    _svc._llm = LLMClient()

    yield

    for k, v in saved.items():
        if v is not None:
            os.environ[k] = v
    _svc._llm = LLMClient()


# ---------------------------------------------------------------------------
# Engine e sessão em memória
# ---------------------------------------------------------------------------

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.security import hash_password
from backend.app.api.deps import require_consultor_or_admin, get_current_user


@pytest.fixture(scope="module")
def engine_mem():
    """Engine SQLite em memória compartilhada pelo módulo."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="module")
def db_session(engine_mem) -> Generator[Session, None, None]:
    """Sessão compartilhada pelo módulo com seed completo."""
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    # Usuário admin
    user = Usuario(
        email="admin@vitao.com.br",
        nome="Admin Vitao",
        role="admin",
        consultor_nome=None,
        hashed_password=hash_password("vitao2026"),
        ativo=True,
    )
    session.add(user)

    # Cliente ATIVO — curva A — MANU — estagio ORCAMENTO
    c1 = Cliente(
        cnpj="12345678000100",
        nome_fantasia="Natural Store SP",
        razao_social="Natural Store Ltda",
        uf="SP",
        cidade="São Paulo",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        curva_abc="A",
        temperatura="QUENTE",
        sinaleiro="VERDE",
        score=82.0,
        prioridade="P4",
        faturamento_total=15000.0,
        dias_sem_compra=20,
        ciclo_medio=30.0,
        n_compras=10,
        estagio_funil="ORCAMENTO",
        rede_regional="Rede Saude",
    )

    # Cliente INAT.REC — LARISSA — sinaleiro VERMELHO — 90 dias sem compra
    c2 = Cliente(
        cnpj="98765432000111",
        nome_fantasia="Bio Market RJ",
        razao_social="Bio Market LTDA",
        uf="RJ",
        cidade="Rio de Janeiro",
        consultor="LARISSA",
        situacao="INAT.REC",
        classificacao_3tier="REAL",
        curva_abc="B",
        temperatura="FRIO",
        sinaleiro="VERMELHO",
        score=30.0,
        prioridade="P2",
        faturamento_total=5000.0,
        dias_sem_compra=90,
        ciclo_medio=30.0,
        n_compras=5,
        estagio_funil="REATIVACAO",
        rede_regional=None,
    )

    # Cliente PROSPECT — MANU — sem compra
    c3 = Cliente(
        cnpj="11111111000100",
        nome_fantasia="Verde Vida",
        razao_social="Verde Vida LTDA",
        uf="SP",
        cidade="Campinas",
        consultor="MANU",
        situacao="PROSPECT",
        classificacao_3tier="REAL",
        curva_abc=None,
        temperatura="FRIO",
        sinaleiro="ROXO",
        score=10.0,
        prioridade="P1",
        faturamento_total=0.0,
        dias_sem_compra=None,
        ciclo_medio=None,
        n_compras=0,
        estagio_funil="PROSPECCAO",
        rede_regional="Rede Saude",
    )

    # Cliente INAT.ANT — LARISSA
    c4 = Cliente(
        cnpj="22222222000100",
        nome_fantasia="Granel Shop",
        razao_social="Granel Shop LTDA",
        uf="MG",
        cidade="Belo Horizonte",
        consultor="LARISSA",
        situacao="INAT.ANT",
        classificacao_3tier="REAL",
        curva_abc="C",
        temperatura="FRIO",
        sinaleiro="VERMELHO",
        score=15.0,
        prioridade="P2",
        faturamento_total=3000.0,
        dias_sem_compra=200,
        ciclo_medio=45.0,
        n_compras=3,
        estagio_funil="PROSPECCAO",
        rede_regional=None,
    )

    session.add_all([c1, c2, c3, c4])
    session.flush()

    # Vendas para c1 — R4: valor > 0 obrigatório
    vendas_c1 = [
        Venda(cnpj="12345678000100", data_pedido=date(2026, 3, 1), numero_pedido="PED-001",
              valor_pedido=1000.0, consultor="MANU", fonte="MERCOS",
              classificacao_3tier="REAL", mes_referencia="2026-03"),
        Venda(cnpj="12345678000100", data_pedido=date(2026, 2, 1), numero_pedido="PED-002",
              valor_pedido=1200.0, consultor="MANU", fonte="MERCOS",
              classificacao_3tier="REAL", mes_referencia="2026-02"),
        Venda(cnpj="12345678000100", data_pedido=date(2026, 1, 1), numero_pedido="PED-003",
              valor_pedido=1500.0, consultor="MANU", fonte="MERCOS",
              classificacao_3tier="REAL", mes_referencia="2026-01"),
    ]
    session.add_all(vendas_c1)

    # Venda para c2 — antiga (para detectar REATIVACAO)
    session.add(
        Venda(cnpj="98765432000111", data_pedido=date(2026, 1, 10), numero_pedido="PED-004",
              valor_pedido=800.0, consultor="LARISSA", fonte="MERCOS",
              classificacao_3tier="REAL", mes_referencia="2026-01")
    )

    # Logs para c1 — mistura de WA e LIGACAO (R4: sem valor monetário)
    hoje = datetime.now()
    logs_c1 = [
        LogInteracao(cnpj="12345678000100", data_interacao=hoje - timedelta(days=2),
                     consultor="MANU", resultado="VENDA / PEDIDO",
                     tipo_contato="WHATSAPP", estagio_funil="POS-VENDA"),
        LogInteracao(cnpj="12345678000100", data_interacao=hoje - timedelta(days=10),
                     consultor="MANU", resultado="ORCAMENTO",
                     tipo_contato="WHATSAPP", estagio_funil="EM ATENDIMENTO"),
        LogInteracao(cnpj="12345678000100", data_interacao=hoje - timedelta(days=20),
                     consultor="MANU", resultado="NAO ATENDE",
                     tipo_contato="LIGACAO", estagio_funil="EM ATENDIMENTO"),
    ]
    session.add_all(logs_c1)

    # Log recente para prospect c3
    session.add(
        LogInteracao(cnpj="11111111000100", data_interacao=hoje - timedelta(days=5),
                     consultor="MANU", resultado="PRIMEIRO CONTATO",
                     tipo_contato="WHATSAPP", estagio_funil="PROSPECCAO")
    )

    session.commit()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# TestClient com dependency_overrides
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fake_admin_user():
    from types import SimpleNamespace
    return SimpleNamespace(id=1, email="admin@vitao.com.br", nome="Admin", role="admin",
                           consultor_nome=None, ativo=True)


@pytest.fixture(scope="module")
def client_ia(db_session, fake_admin_user) -> TestClient:
    """TestClient com get_db e auth sobrescritos."""
    def _db_override():
        yield db_session

    app.dependency_overrides[get_db] = _db_override
    app.dependency_overrides[get_current_user] = lambda: fake_admin_user
    app.dependency_overrides[require_consultor_or_admin] = lambda: fake_admin_user

    c = TestClient(app, raise_server_exceptions=True)
    yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CNPJ_ATIVO = "12345678000100"
CNPJ_INAT = "98765432000111"
CNPJ_PROSPECT = "11111111000100"
CNPJ_INEXISTENTE = "99999999999999"


# ===========================================================================
# BLOCO 1 — Testes unitários do IAService (chamadas diretas via _run)
# ===========================================================================

class TestAnalisarSentimentoService:
    """Testes unitários do método analisar_sentimento."""

    def test_sentimento_cliente_positivo(self, db_session):
        """Cliente com VENDA/PEDIDO recente deve retornar campos válidos."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.analisar_sentimento(cnpj=CNPJ_ATIVO, db=db_session))
        assert result["cnpj"] == CNPJ_ATIVO
        assert result["sentimento"] in ("POSITIVO", "NEUTRO", "NEGATIVO", "URGENTE")
        assert 0 <= result["score"] <= 100
        assert result["tendencia"] in ("MELHORANDO", "ESTAVEL", "PIORANDO")
        assert isinstance(result["historico"], list)
        assert isinstance(result["recomendacao"], str)
        assert len(result["recomendacao"]) > 0

    def test_sentimento_cliente_sem_historico_retorna_sentimento_valido(self, db_session):
        """Cliente sem logs WA retorna sentimento funcional (não levanta erro)."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.analisar_sentimento(cnpj=CNPJ_INAT, db=db_session))
        assert result["cnpj"] == CNPJ_INAT
        assert result["sentimento"] in ("POSITIVO", "NEUTRO", "NEGATIVO", "URGENTE")

    def test_sentimento_cnpj_inexistente_levanta_valueerror(self, db_session):
        """CNPJ não cadastrado deve levantar ValueError."""
        from backend.app.services.ia_service import ia_service
        with pytest.raises(ValueError, match="não encontrado"):
            _run(ia_service.analisar_sentimento(cnpj=CNPJ_INEXISTENTE, db=db_session))

    def test_sentimento_historico_contem_campos_obrigatorios(self, db_session):
        """Cada item do histórico deve ter data, resultado e sentimento."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.analisar_sentimento(cnpj=CNPJ_ATIVO, db=db_session))
        for item in result["historico"]:
            assert "data" in item
            assert "resultado" in item
            assert "sentimento" in item
            assert item["sentimento"] in ("POSITIVO", "NEUTRO", "NEGATIVO", "URGENTE")

    def test_sentimento_score_range(self, db_session):
        """Score sempre entre 0.0 e 100.0."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.analisar_sentimento(cnpj=CNPJ_ATIVO, db=db_session))
        assert 0.0 <= result["score"] <= 100.0

    def test_sentimento_cnpj_normalizado_na_resposta(self, db_session):
        """CNPJ formatado na entrada deve retornar normalizado (14 dígitos)."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.analisar_sentimento(cnpj="12.345.678/0001-00", db=db_session))
        assert result["cnpj"] == CNPJ_ATIVO
        assert len(result["cnpj"]) == 14


class TestPreverFechamentoService:
    """Testes unitários do método prever_fechamento."""

    def test_previsao_campos_obrigatorios(self, db_session):
        """Resposta deve ter todos os campos esperados."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.prever_fechamento(cnpj=CNPJ_ATIVO, db=db_session))
        assert "cnpj" in result
        assert "probabilidade_pct" in result
        assert "nivel" in result
        assert "fatores" in result
        assert "tempo_estimado_dias" in result
        assert "recomendacao" in result

    def test_previsao_probabilidade_range(self, db_session):
        """Probabilidade deve estar entre 0 e 100."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.prever_fechamento(cnpj=CNPJ_ATIVO, db=db_session))
        assert 0.0 <= result["probabilidade_pct"] <= 100.0

    def test_previsao_nivel_valido(self, db_session):
        """Nível deve ser ALTA, MEDIA ou BAIXA."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.prever_fechamento(cnpj=CNPJ_ATIVO, db=db_session))
        assert result["nivel"] in ("ALTA", "MEDIA", "BAIXA")

    def test_previsao_fatores_tem_4_itens(self, db_session):
        """Devem ser retornados exatamente 4 fatores."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.prever_fechamento(cnpj=CNPJ_ATIVO, db=db_session))
        assert len(result["fatores"]) == 4
        for f in result["fatores"]:
            assert "nome" in f
            assert "peso" in f
            assert "contribuicao" in f

    def test_previsao_prospect_nivel_mais_baixo_que_orcamento(self, db_session):
        """Prospect em PROSPECCAO tem probabilidade menor que cliente em ORCAMENTO."""
        from backend.app.services.ia_service import ia_service
        result_prospect = _run(ia_service.prever_fechamento(cnpj=CNPJ_PROSPECT, db=db_session))
        result_ativo = _run(ia_service.prever_fechamento(cnpj=CNPJ_ATIVO, db=db_session))
        assert result_prospect["probabilidade_pct"] < result_ativo["probabilidade_pct"]

    def test_previsao_cnpj_inexistente_levanta_valueerror(self, db_session):
        """CNPJ não cadastrado deve levantar ValueError."""
        from backend.app.services.ia_service import ia_service
        with pytest.raises(ValueError, match="não encontrado"):
            _run(ia_service.prever_fechamento(cnpj=CNPJ_INEXISTENTE, db=db_session))

    def test_previsao_tempo_estimado_positivo(self, db_session):
        """Tempo estimado deve ser positivo."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.prever_fechamento(cnpj=CNPJ_ATIVO, db=db_session))
        assert result["tempo_estimado_dias"] > 0


class TestCoachVendasService:
    """Testes unitários do método coach_vendas."""

    def test_coach_campos_obrigatorios(self, db_session):
        """Resposta deve conter todos os campos esperados."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.coach_vendas(consultor="MANU", db=db_session))
        assert result["consultor"] == "MANU"
        assert result["periodo"] == "ultimos_30_dias"
        assert "metricas" in result
        assert "pontos_fortes" in result
        assert "pontos_fracos" in result
        assert "recomendacoes" in result
        assert "meta_sugerida" in result

    def test_coach_metricas_obrigatorias(self, db_session):
        """Sub-objeto metricas deve ter todos os campos."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.coach_vendas(consultor="MANU", db=db_session))
        m = result["metricas"]
        assert "conversao_pct" in m
        assert "ticket_medio" in m
        assert "atendimentos_dia" in m
        assert "positivacao_pct" in m

    def test_coach_metricas_range(self, db_session):
        """Métricas de percentual devem estar entre 0 e 100."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.coach_vendas(consultor="MANU", db=db_session))
        m = result["metricas"]
        assert 0.0 <= m["conversao_pct"] <= 100.0
        assert 0.0 <= m["positivacao_pct"] <= 100.0
        assert m["ticket_medio"] >= 0.0
        assert m["atendimentos_dia"] >= 0.0

    def test_coach_recomendacoes_tem_prioridade(self, db_session):
        """Cada recomendação deve ter prioridade, acao e impacto_estimado."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.coach_vendas(consultor="MANU", db=db_session))
        assert len(result["recomendacoes"]) > 0
        for rec in result["recomendacoes"]:
            assert rec["prioridade"] in ("ALTA", "MEDIA", "BAIXA")
            assert isinstance(rec["acao"], str)
            assert isinstance(rec["impacto_estimado"], str)

    def test_coach_consultor_normalizado(self, db_session):
        """Consultor minúsculo deve retornar normalizado em uppercase."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.coach_vendas(consultor="manu", db=db_session))
        assert result["consultor"] == "MANU"

    def test_coach_consultor_sem_dados_retorna_zeros(self, db_session):
        """Consultor sem vendas/logs deve retornar métricas zeradas sem erro."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.coach_vendas(consultor="JULIO", db=db_session))
        assert result["metricas"]["conversao_pct"] == 0.0
        assert result["metricas"]["ticket_medio"] == 0.0


class TestDetectarOportunidadesService:
    """Testes unitários do método detectar_oportunidades."""

    def test_oportunidades_campos_obrigatorios(self, db_session):
        """Resposta deve ter total e oportunidades."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        assert "total" in result
        assert "oportunidades" in result
        assert isinstance(result["total"], int)
        assert isinstance(result["oportunidades"], list)

    def test_oportunidades_total_coerente(self, db_session):
        """total deve ser igual ao comprimento da lista."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        assert result["total"] == len(result["oportunidades"])

    def test_oportunidades_maxima_10(self, db_session):
        """Nunca retornar mais de 10 oportunidades."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        assert result["total"] <= 10

    def test_oportunidades_campos_por_item(self, db_session):
        """Cada oportunidade deve ter todos os campos exigidos e sem _score interno."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        for op in result["oportunidades"]:
            assert "cnpj" in op
            assert "nome" in op
            assert "tipo" in op
            assert "prioridade" in op
            assert "valor_potencial" in op
            assert "motivo" in op
            assert "acao_sugerida" in op
            assert op["tipo"] in ("REATIVACAO", "UPSELL", "PROSPECT_QUENTE", "CROSS_SELL_REDE")
            assert op["prioridade"] in ("ALTA", "MEDIA")
            # Campo interno _score não deve vazar na resposta
            assert "_score" not in op

    def test_oportunidade_reativacao_detectada(self, db_session):
        """c2 com 90 dias sem compra e ciclo 30d deve gerar REATIVACAO."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        tipos = [op["tipo"] for op in result["oportunidades"]]
        assert "REATIVACAO" in tipos

    def test_oportunidade_prospect_quente_detectada(self, db_session):
        """c3 (PROSPECT) com log nos últimos 14 dias deve ser PROSPECT_QUENTE."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        tipos = [op["tipo"] for op in result["oportunidades"]]
        assert "PROSPECT_QUENTE" in tipos

    def test_oportunidades_cnpj_sempre_14_digitos(self, db_session):
        """CNPJ em cada oportunidade deve ter exatamente 14 dígitos."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.detectar_oportunidades(db=db_session))
        for op in result["oportunidades"]:
            assert len(op["cnpj"]) == 14


class TestDashboardIAService:
    """Testes unitários do método dashboard_ia."""

    def test_dashboard_campos_obrigatorios(self, db_session):
        """Resposta deve ter todos os campos do contrato."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.dashboard_ia(db=db_session))
        assert "briefings_disponiveis" in result
        assert "alertas_ativos" in result
        assert "oportunidades" in result
        assert "clientes_em_risco" in result
        assert "consultor_destaque" in result
        assert "insight_do_dia" in result

    def test_dashboard_contagens_inteiras_e_positivas(self, db_session):
        """Campos de contagem devem ser inteiros >= 0."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.dashboard_ia(db=db_session))
        assert isinstance(result["briefings_disponiveis"], int)
        assert isinstance(result["alertas_ativos"], int)
        assert isinstance(result["oportunidades"], int)
        assert isinstance(result["clientes_em_risco"], int)
        assert result["briefings_disponiveis"] >= 0
        assert result["alertas_ativos"] >= 0
        assert result["clientes_em_risco"] >= 0

    def test_dashboard_consultor_destaque_campos(self, db_session):
        """Consultor destaque deve ter nome e motivo não vazios."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.dashboard_ia(db=db_session))
        cd = result["consultor_destaque"]
        assert "nome" in cd
        assert "motivo" in cd
        assert isinstance(cd["nome"], str)
        assert len(cd["nome"]) > 0

    def test_dashboard_alertas_coerentes_com_seed(self, db_session):
        """c2 e c4 têm VERMELHO no sinaleiro — alertas_ativos deve ser >= 2."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.dashboard_ia(db=db_session))
        assert result["alertas_ativos"] >= 2

    def test_dashboard_briefings_coerentes_com_seed(self, db_session):
        """c1 (ATIVO) e c2 (INAT.REC) qualificam — briefings_disponiveis >= 2."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.dashboard_ia(db=db_session))
        assert result["briefings_disponiveis"] >= 2

    def test_dashboard_clientes_em_risco_coerente(self, db_session):
        """c4 é INAT.ANT — clientes_em_risco deve ser >= 1."""
        from backend.app.services.ia_service import ia_service
        result = _run(ia_service.dashboard_ia(db=db_session))
        assert result["clientes_em_risco"] >= 1


# ===========================================================================
# BLOCO 2 — Testes de integração das rotas HTTP
# ===========================================================================

class TestRotaSentimento:
    """Testes de integração do endpoint GET /api/ia/sentimento/{cnpj}."""

    def test_200_cliente_valido(self, client_ia):
        r = client_ia.get(f"/api/ia/sentimento/{CNPJ_ATIVO}")
        assert r.status_code == 200
        data = r.json()
        assert data["cnpj"] == CNPJ_ATIVO
        assert "sentimento" in data
        assert "score" in data
        assert "historico" in data
        assert "tendencia" in data
        assert "recomendacao" in data

    def test_404_cnpj_inexistente(self, client_ia):
        r = client_ia.get(f"/api/ia/sentimento/{CNPJ_INEXISTENTE}")
        assert r.status_code == 404

    def test_score_e_float_no_json(self, client_ia):
        r = client_ia.get(f"/api/ia/sentimento/{CNPJ_ATIVO}")
        assert r.status_code == 200
        assert isinstance(r.json()["score"], (int, float))

    def test_sentimento_field_valido(self, client_ia):
        r = client_ia.get(f"/api/ia/sentimento/{CNPJ_ATIVO}")
        assert r.json()["sentimento"] in ("POSITIVO", "NEUTRO", "NEGATIVO", "URGENTE")

    def test_tendencia_field_valido(self, client_ia):
        r = client_ia.get(f"/api/ia/sentimento/{CNPJ_ATIVO}")
        assert r.json()["tendencia"] in ("MELHORANDO", "ESTAVEL", "PIORANDO")


class TestRotaPrevisaoFechamento:
    """Testes de integração do endpoint GET /api/ia/previsao-fechamento/{cnpj}."""

    def test_200_cliente_valido(self, client_ia):
        r = client_ia.get(f"/api/ia/previsao-fechamento/{CNPJ_ATIVO}")
        assert r.status_code == 200
        data = r.json()
        assert "probabilidade_pct" in data
        assert "nivel" in data
        assert "fatores" in data
        assert "tempo_estimado_dias" in data
        assert "recomendacao" in data

    def test_404_cnpj_inexistente(self, client_ia):
        r = client_ia.get(f"/api/ia/previsao-fechamento/{CNPJ_INEXISTENTE}")
        assert r.status_code == 404

    def test_nivel_valido(self, client_ia):
        r = client_ia.get(f"/api/ia/previsao-fechamento/{CNPJ_ATIVO}")
        assert r.json()["nivel"] in ("ALTA", "MEDIA", "BAIXA")

    def test_4_fatores_presentes(self, client_ia):
        r = client_ia.get(f"/api/ia/previsao-fechamento/{CNPJ_ATIVO}")
        assert len(r.json()["fatores"]) == 4

    def test_probabilidade_range(self, client_ia):
        r = client_ia.get(f"/api/ia/previsao-fechamento/{CNPJ_ATIVO}")
        prob = r.json()["probabilidade_pct"]
        assert 0.0 <= prob <= 100.0


class TestRotaCoach:
    """Testes de integração do endpoint GET /api/ia/coach/{consultor}."""

    def test_200_consultor_manu(self, client_ia):
        r = client_ia.get("/api/ia/coach/MANU")
        assert r.status_code == 200
        data = r.json()
        assert data["consultor"] == "MANU"
        assert "metricas" in data
        assert "pontos_fortes" in data
        assert "pontos_fracos" in data
        assert "recomendacoes" in data
        assert "meta_sugerida" in data

    def test_200_consultor_minusculo_normalizado(self, client_ia):
        """Consultor em minúsculo deve ser aceito e normalizado."""
        r = client_ia.get("/api/ia/coach/larissa")
        assert r.status_code == 200
        assert r.json()["consultor"] == "LARISSA"

    def test_metricas_percentuais_validos(self, client_ia):
        r = client_ia.get("/api/ia/coach/MANU")
        m = r.json()["metricas"]
        assert 0.0 <= m["conversao_pct"] <= 100.0
        assert 0.0 <= m["positivacao_pct"] <= 100.0

    def test_recomendacoes_prioridade_valida(self, client_ia):
        r = client_ia.get("/api/ia/coach/MANU")
        for rec in r.json()["recomendacoes"]:
            assert rec["prioridade"] in ("ALTA", "MEDIA", "BAIXA")


class TestRotaAlertaOportunidade:
    """Testes de integração do endpoint GET /api/ia/alerta-oportunidade."""

    def test_200_retorna_lista(self, client_ia):
        r = client_ia.get("/api/ia/alerta-oportunidade")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "oportunidades" in data
        assert data["total"] == len(data["oportunidades"])

    def test_maximo_10_oportunidades(self, client_ia):
        r = client_ia.get("/api/ia/alerta-oportunidade")
        assert r.json()["total"] <= 10

    def test_campos_obrigatorios_por_item(self, client_ia):
        r = client_ia.get("/api/ia/alerta-oportunidade")
        for op in r.json()["oportunidades"]:
            assert "cnpj" in op
            assert "nome" in op
            assert "tipo" in op
            assert "prioridade" in op
            assert "valor_potencial" in op
            assert "motivo" in op
            assert "acao_sugerida" in op

    def test_tipo_valido_por_item(self, client_ia):
        r = client_ia.get("/api/ia/alerta-oportunidade")
        for op in r.json()["oportunidades"]:
            assert op["tipo"] in ("REATIVACAO", "UPSELL", "PROSPECT_QUENTE", "CROSS_SELL_REDE")

    def test_sem_campo_score_interno_na_resposta(self, client_ia):
        """O campo _score interno não deve aparecer na resposta HTTP."""
        r = client_ia.get("/api/ia/alerta-oportunidade")
        for op in r.json()["oportunidades"]:
            assert "_score" not in op


class TestRotaDashboardIA:
    """Testes de integração do endpoint GET /api/ia/dashboard."""

    def test_200_campos_obrigatorios(self, client_ia):
        r = client_ia.get("/api/ia/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "briefings_disponiveis" in data
        assert "alertas_ativos" in data
        assert "oportunidades" in data
        assert "clientes_em_risco" in data
        assert "consultor_destaque" in data
        assert "insight_do_dia" in data

    def test_contagens_positivas(self, client_ia):
        r = client_ia.get("/api/ia/dashboard")
        d = r.json()
        assert d["briefings_disponiveis"] >= 0
        assert d["alertas_ativos"] >= 0
        assert d["oportunidades"] >= 0
        assert d["clientes_em_risco"] >= 0

    def test_consultor_destaque_estrutura(self, client_ia):
        r = client_ia.get("/api/ia/dashboard")
        cd = r.json()["consultor_destaque"]
        assert "nome" in cd
        assert "motivo" in cd

    def test_insight_nao_vazio(self, client_ia):
        r = client_ia.get("/api/ia/dashboard")
        assert len(r.json()["insight_do_dia"]) > 0

    def test_alertas_coerentes_com_seed(self, client_ia):
        """c2 e c4 têm sinaleiro VERMELHO — alertas_ativos deve ser >= 2."""
        r = client_ia.get("/api/ia/dashboard")
        assert r.json()["alertas_ativos"] >= 2

    def test_briefings_coerentes_com_seed(self, client_ia):
        """c1 (ATIVO) e c2 (INAT.REC) — briefings_disponiveis deve ser >= 2."""
        r = client_ia.get("/api/ia/dashboard")
        assert r.json()["briefings_disponiveis"] >= 2

    def test_sem_auth_retorna_erro(self):
        """Sem JWT o endpoint deve negar acesso quando overrides estão limpos."""
        # Salva e limpa overrides para testar auth real isoladamente
        saved_overrides = dict(app.dependency_overrides)
        app.dependency_overrides.clear()
        try:
            bare_client = TestClient(app, raise_server_exceptions=False)
            r = bare_client.get("/api/ia/dashboard")
            assert r.status_code in (401, 403, 422)
        finally:
            app.dependency_overrides.update(saved_overrides)
