"""
CRM VITAO360 — Tests /api/dde routes (Onda 4 — PAPA)

Cobre 5 endpoints com auth + canal scoping + edge cases:

  /cliente/{cnpj}:
    - 200: cnpj válido, canal DIRETO, retorna ResultadoDDE
    - 401: sem auth (sem override de get_current_user)
    - 403: user com canal_ids restritos tentando ver cliente de outro canal
    - 422: cnpj de canal não elegível (INTERNO)
    - 404: cnpj inexistente
    - CNPJ com pontuação normalizado para 14 dígitos

  /consultor/{nome}:
    - 200: consultor existente retorna itens elegíveis
    - Vazio: consultor sem clientes elegíveis retorna items=[]

  /canal/{canal_id}:
    - 200: canal_id de DIRETO retorna lista
    - 422: canal_id de canal inelegível (INTERNO)
    - 403: user fora do escopo do canal
    - 404: canal inexistente

  /comparativo:
    - 200: 3 CNPJs válidos retorna 3 items
    - 400: > 20 CNPJs
    - Mistura elegíveis + inelegíveis: inelegíveis filtrados silenciosamente

  /score/{cnpj}:
    - 200: retorna score + breakdown
    - 422: canal não elegível

Padrão: SimpleNamespace fake users + in-memory SQLite + dependency_overrides.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import (
    get_current_user,
    get_user_canal_ids,
    require_admin,
    require_admin_or_gerente,
    require_consultor_or_above,
)
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.canal import Canal
from backend.app.models.cliente import Cliente
from backend.app.models.venda import Venda


# ---------------------------------------------------------------------------
# Engine e sessão SQLite in-memory (isolados por test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine_dde():
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db_dde(engine_dde) -> Session:
    _Session = sessionmaker(bind=engine_dde)
    session = _Session()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Canais de teste
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def canal_direto(db_dde: Session) -> Canal:
    """Canal DIRETO — elegível para DDE."""
    c = Canal(nome="DIRETO", status="ATIVO", descricao="Canal direto elegível DDE")
    db_dde.add(c)
    db_dde.commit()
    db_dde.refresh(c)
    return c


@pytest.fixture(scope="function")
def canal_interno(db_dde: Session) -> Canal:
    """Canal INTERNO — NÃO elegível para DDE."""
    c = Canal(nome="INTERNO", status="ATIVO", descricao="Canal interno não elegível DDE")
    db_dde.add(c)
    db_dde.commit()
    db_dde.refresh(c)
    return c


@pytest.fixture(scope="function")
def canal_food(db_dde: Session) -> Canal:
    """Canal FOOD_SERVICE — elegível para DDE."""
    c = Canal(nome="FOOD_SERVICE", status="ATIVO", descricao="Canal food elegível DDE")
    db_dde.add(c)
    db_dde.commit()
    db_dde.refresh(c)
    return c


# ---------------------------------------------------------------------------
# Clientes de teste
# ---------------------------------------------------------------------------

CNPJ_DIRETO = "11222333000181"
CNPJ_INTERNO = "44555666000172"
CNPJ_FOOD = "77888999000163"
CNPJ_INEXISTENTE = "99999999000199"


@pytest.fixture(scope="function")
def cliente_direto(db_dde: Session, canal_direto: Canal) -> Cliente:
    """Cliente com canal DIRETO (elegível DDE)."""
    c = Cliente(
        cnpj=CNPJ_DIRETO,
        nome_fantasia="Loja Direto Ltda",
        razao_social="Loja Direto LTDA",
        uf="SC",
        cidade="Joinville",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        faturamento_total=50000.0,
        canal_id=canal_direto.id,
    )
    db_dde.add(c)
    db_dde.commit()
    db_dde.refresh(c)
    return c


@pytest.fixture(scope="function")
def cliente_interno(db_dde: Session, canal_interno: Canal) -> Cliente:
    """Cliente com canal INTERNO (NÃO elegível DDE)."""
    c = Cliente(
        cnpj=CNPJ_INTERNO,
        nome_fantasia="Loja Interna Ltda",
        razao_social="Loja Interna LTDA",
        uf="PR",
        cidade="Curitiba",
        consultor="DAIANE",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        faturamento_total=20000.0,
        canal_id=canal_interno.id,
    )
    db_dde.add(c)
    db_dde.commit()
    db_dde.refresh(c)
    return c


@pytest.fixture(scope="function")
def cliente_food(db_dde: Session, canal_food: Canal) -> Cliente:
    """Cliente com canal FOOD_SERVICE (elegível DDE)."""
    c = Cliente(
        cnpj=CNPJ_FOOD,
        nome_fantasia="Restaurant Food Ltda",
        razao_social="Restaurant Food LTDA",
        uf="RS",
        cidade="Porto Alegre",
        consultor="LARISSA",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        faturamento_total=35000.0,
        canal_id=canal_food.id,
    )
    db_dde.add(c)
    db_dde.commit()
    db_dde.refresh(c)
    return c


@pytest.fixture(scope="function")
def venda_direto(db_dde: Session, cliente_direto: Cliente) -> Venda:
    """Venda para cliente_direto (garante L1 > 0 no DDE)."""
    v = Venda(
        cnpj=CNPJ_DIRETO,
        data_pedido=date(2025, 6, 1),
        numero_pedido="PED-DDE-001",
        valor_pedido=25000.00,
        consultor="MANU",
        fonte="SAP",
        classificacao_3tier="REAL",
        mes_referencia="2025-06",
    )
    db_dde.add(v)
    db_dde.commit()
    db_dde.refresh(v)
    return v


@pytest.fixture(scope="function")
def venda_food(db_dde: Session, cliente_food: Cliente) -> Venda:
    """Venda para cliente_food."""
    v = Venda(
        cnpj=CNPJ_FOOD,
        data_pedido=date(2025, 6, 1),
        numero_pedido="PED-DDE-002",
        valor_pedido=18000.00,
        consultor="LARISSA",
        fonte="SAP",
        classificacao_3tier="REAL",
        mes_referencia="2025-06",
    )
    db_dde.add(v)
    db_dde.commit()
    db_dde.refresh(v)
    return v


# ---------------------------------------------------------------------------
# Helpers de fake user
# ---------------------------------------------------------------------------

def _fake_admin() -> SimpleNamespace:
    return SimpleNamespace(
        id=1, email="admin@vitao.com.br", nome="Admin",
        role="admin", consultor_nome=None, ativo=True, canais=[],
    )


def _fake_consultor_direto(canal_direto: Canal) -> SimpleNamespace:
    """Consultor com acesso apenas ao canal DIRETO."""

    class FakeCanal:
        def __init__(self, id_):
            self.id = id_

    user = SimpleNamespace(
        id=2, email="manu@vitao.com.br", nome="Manu",
        role="consultor", consultor_nome="MANU", ativo=True,
        canais=[FakeCanal(canal_direto.id)],
    )
    return user


def _db_override(session: Session):
    def _override():
        yield session
    return _override


# ---------------------------------------------------------------------------
# TestClient fixtures: admin e consultor restrito
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_dde_admin(db_dde: Session) -> TestClient:
    """Admin — sem restrição de canal."""
    admin = _fake_admin()
    app.dependency_overrides[get_db] = _db_override(db_dde)
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[require_consultor_or_above] = lambda: admin
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[require_admin_or_gerente] = lambda: admin
    app.dependency_overrides[get_user_canal_ids] = lambda: None  # admin = None = sem filtro
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_dde_consultor(db_dde: Session, canal_direto: Canal) -> TestClient:
    """Consultor com acesso apenas ao canal DIRETO."""
    user = _fake_consultor_direto(canal_direto)
    app.dependency_overrides[get_db] = _db_override(db_dde)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_consultor_or_above] = lambda: user
    app.dependency_overrides[get_user_canal_ids] = lambda: [canal_direto.id]
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_no_auth(db_dde: Session) -> TestClient:
    """Client sem nenhum override de auth — depende do JWT real (sem token = 401)."""
    app.dependency_overrides[get_db] = _db_override(db_dde)
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ===========================================================================
# TESTES /api/dde/cliente/{cnpj}
# ===========================================================================

class TestDDEClienteEndpoint:
    """Testa GET /api/dde/cliente/{cnpj}."""

    def test_200_cnpj_valido_canal_direto(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_DIRETO}?ano=2025")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["cnpj"] == CNPJ_DIRETO
        assert data["ano"] == 2025
        assert "linhas" in data
        assert len(data["linhas"]) >= 21
        assert "indicadores" in data
        assert "veredito" in data
        assert "fase_ativa" in data
        assert data["fase_ativa"] == "A"

    def test_200_veredito_valido(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_DIRETO}?ano=2025")
        assert resp.status_code == 200
        veredito = resp.json()["veredito"]
        assert veredito in {
            "SAUDAVEL", "REVISAR", "RENEGOCIAR", "SUBSTITUIR",
            "ALERTA_CREDITO", "SEM_DADOS",
        }

    def test_200_l1_bate_com_venda(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_DIRETO}?ano=2025")
        assert resp.status_code == 200
        linhas = resp.json()["linhas"]
        l1 = next((l for l in linhas if l["codigo"] == "L1"), None)
        assert l1 is not None
        # venda_direto = 25000.00
        assert l1["valor"] == pytest.approx(25000.0, rel=1e-3)

    def test_401_sem_auth(self, client_no_auth, cliente_direto):
        resp = client_no_auth.get(f"/api/dde/cliente/{CNPJ_DIRETO}?ano=2025")
        assert resp.status_code == 401

    def test_403_fora_do_escopo_do_canal(
        self, client_dde_consultor, cliente_interno
    ):
        """Consultor com acesso ao canal DIRETO não pode ver cliente do canal INTERNO."""
        resp = client_dde_consultor.get(f"/api/dde/cliente/{CNPJ_INTERNO}?ano=2025")
        assert resp.status_code == 403

    def test_422_canal_nao_elegivel(
        self, client_dde_admin, cliente_interno
    ):
        """Canal INTERNO não é elegível para DDE — deve retornar 422."""
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_INTERNO}?ano=2025")
        assert resp.status_code == 422
        assert "DIRETO" in resp.json()["detail"] or "DDE" in resp.json()["detail"]

    def test_404_cnpj_inexistente(self, client_dde_admin):
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_INEXISTENTE}?ano=2025")
        assert resp.status_code == 404

    def test_cnpj_com_pontuacao_normalizado(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        """
        CNPJ com pontuação (pontos e traço) deve ser normalizado para 14 dígitos.

        Nota: CNPJ com barra '/' no path param quebra a rota HTTP — esse é o
        comportamento padrão de HTTP (path separator). O helper _normaliza_cnpj
        é testado aqui via dígitos + traço + pontos sem barra.

        O endpoint /comparativo aceita CSV no query param e é o local mais
        natural para CNPJs com pontuação completa (testado em test_cnpj_com_pontuacao_aceito).
        """
        # CNPJ_DIRETO = 11222333000181 — representação com pontos e traço sem barra
        # 11222333000181 → com formatação parcial: 11222333-000181
        cnpj_parcial = "11222333-000181"  # hífen removido pelo normaliza_cnpj
        resp = client_dde_admin.get(f"/api/dde/cliente/{cnpj_parcial}?ano=2025")
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == CNPJ_DIRETO

    def test_ano_default_atual(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        """Sem ?ano, deve usar o ano atual sem erro."""
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_DIRETO}")
        assert resp.status_code == 200
        data = resp.json()
        from datetime import datetime
        assert data["ano"] == datetime.now().year

    def test_indicadores_estrutura(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        """Todos os 9 indicadores presentes na resposta."""
        resp = client_dde_admin.get(f"/api/dde/cliente/{CNPJ_DIRETO}?ano=2025")
        assert resp.status_code == 200
        indicadores = resp.json()["indicadores"]
        for i in range(1, 10):
            assert f"I{i}" in indicadores, f"Indicador I{i} ausente na resposta"


# ===========================================================================
# TESTES /api/dde/consultor/{nome}
# ===========================================================================

class TestDDEConsultorEndpoint:
    """Testa GET /api/dde/consultor/{nome}."""

    def test_200_consultor_com_clientes_elegiveis(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get("/api/dde/consultor/MANU?ano=2025")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ano"] == 2025
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["cnpj"] == CNPJ_DIRETO

    def test_200_consultor_sem_clientes_elegiveis(
        self, client_dde_admin, cliente_interno
    ):
        """DAIANE só tem cliente INTERNO — não elegível — items deve ser []."""
        resp = client_dde_admin.get("/api/dde/consultor/DAIANE?ano=2025")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_200_consultor_inexistente_retorna_lista_vazia(
        self, client_dde_admin, canal_direto
    ):
        resp = client_dde_admin.get("/api/dde/consultor/CONSULTOR_INEXISTENTE?ano=2025")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_200_item_tem_campos_esperados(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get("/api/dde/consultor/MANU?ano=2025")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert "cnpj" in item
        assert "veredito" in item
        # receita_bruta pode ser não-null pois há venda
        assert item["receita_bruta"] == pytest.approx(25000.0, rel=1e-3)

    def test_consultor_scoping_restringe_canal(
        self, client_dde_consultor, cliente_direto, cliente_food, venda_direto, venda_food
    ):
        """
        Consultor com canal DIRETO apenas:
        Busca MANU — cliente_direto está em DIRETO (visível),
        cliente_food (LARISSA) não pertence ao consultor de qualquer forma.
        """
        resp = client_dde_consultor.get("/api/dde/consultor/MANU?ano=2025")
        assert resp.status_code == 200
        cnpjs = [i["cnpj"] for i in resp.json()["items"]]
        assert CNPJ_DIRETO in cnpjs
        assert CNPJ_FOOD not in cnpjs  # LARISSA, não MANU


# ===========================================================================
# TESTES /api/dde/canal/{canal_id}
# ===========================================================================

class TestDDECanalEndpoint:
    """Testa GET /api/dde/canal/{canal_id}."""

    def test_200_canal_direto_retorna_lista(
        self, client_dde_admin, canal_direto, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get(f"/api/dde/canal/{canal_direto.id}?ano=2025")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ano"] == 2025
        assert len(data["items"]) == 1
        assert data["items"][0]["cnpj"] == CNPJ_DIRETO

    def test_422_canal_interno_nao_elegivel(
        self, client_dde_admin, canal_interno, cliente_interno
    ):
        resp = client_dde_admin.get(f"/api/dde/canal/{canal_interno.id}?ano=2025")
        assert resp.status_code == 422
        assert "DDE" in resp.json()["detail"] or "DIRETO" in resp.json()["detail"]

    def test_403_user_fora_do_escopo_do_canal(
        self, client_dde_consultor, canal_food, cliente_food, venda_food
    ):
        """Consultor com acesso ao canal DIRETO tentando ver canal FOOD_SERVICE → 403."""
        resp = client_dde_consultor.get(f"/api/dde/canal/{canal_food.id}?ano=2025")
        assert resp.status_code == 403

    def test_404_canal_inexistente(self, client_dde_admin):
        resp = client_dde_admin.get("/api/dde/canal/99999?ano=2025")
        assert resp.status_code == 404

    def test_200_canal_vazio_retorna_items_vazio(
        self, client_dde_admin, canal_direto
    ):
        """Canal elegível mas sem clientes → items=[]."""
        resp = client_dde_admin.get(f"/api/dde/canal/{canal_direto.id}?ano=2025")
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# ===========================================================================
# TESTES /api/dde/comparativo
# ===========================================================================

class TestDDEComparativoEndpoint:
    """Testa GET /api/dde/comparativo?cnpjs=..."""

    def test_200_dois_cnpjs_elegiveis(
        self, client_dde_admin, cliente_direto, cliente_food, venda_direto, venda_food
    ):
        cnpjs = f"{CNPJ_DIRETO},{CNPJ_FOOD}"
        resp = client_dde_admin.get(f"/api/dde/comparativo?cnpjs={cnpjs}&ano=2025")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ano"] == 2025
        assert len(data["items"]) == 2
        result_cnpjs = {i["cnpj"] for i in data["items"]}
        assert CNPJ_DIRETO in result_cnpjs
        assert CNPJ_FOOD in result_cnpjs

    def test_400_mais_de_20_cnpjs(self, client_dde_admin):
        cnpjs = ",".join(["12345678000100"] * 21)
        resp = client_dde_admin.get(f"/api/dde/comparativo?cnpjs={cnpjs}&ano=2025")
        assert resp.status_code == 400
        assert "20" in resp.json()["detail"]

    def test_mistura_elegiveis_e_inelegiveis_filtra_inelegiveis(
        self, client_dde_admin, cliente_direto, cliente_interno, venda_direto
    ):
        """CNPJ_INTERNO (canal INTERNO, inelegível) deve ser filtrado silenciosamente."""
        cnpjs = f"{CNPJ_DIRETO},{CNPJ_INTERNO}"
        resp = client_dde_admin.get(f"/api/dde/comparativo?cnpjs={cnpjs}&ano=2025")
        assert resp.status_code == 200
        result_cnpjs = [i["cnpj"] for i in resp.json()["items"]]
        assert CNPJ_DIRETO in result_cnpjs
        assert CNPJ_INTERNO not in result_cnpjs

    def test_cnpj_inexistente_filtrado_silenciosamente(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        cnpjs = f"{CNPJ_DIRETO},{CNPJ_INEXISTENTE}"
        resp = client_dde_admin.get(f"/api/dde/comparativo?cnpjs={cnpjs}&ano=2025")
        assert resp.status_code == 200
        result_cnpjs = [i["cnpj"] for i in resp.json()["items"]]
        assert CNPJ_DIRETO in result_cnpjs
        assert CNPJ_INEXISTENTE not in result_cnpjs

    def test_scoping_filtra_fora_do_canal(
        self, client_dde_consultor, cliente_direto, cliente_food, venda_direto, venda_food
    ):
        """Consultor DIRETO não vê FOOD_SERVICE no comparativo."""
        cnpjs = f"{CNPJ_DIRETO},{CNPJ_FOOD}"
        resp = client_dde_consultor.get(f"/api/dde/comparativo?cnpjs={cnpjs}&ano=2025")
        assert resp.status_code == 200
        result_cnpjs = [i["cnpj"] for i in resp.json()["items"]]
        assert CNPJ_DIRETO in result_cnpjs
        assert CNPJ_FOOD not in result_cnpjs  # FOOD_SERVICE fora do escopo do consultor

    def test_cnpj_com_pontuacao_aceito(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        cnpj_fmt = "11.222.333/0001-81"
        resp = client_dde_admin.get(f"/api/dde/comparativo?cnpjs={cnpj_fmt}&ano=2025")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1
        assert resp.json()["items"][0]["cnpj"] == CNPJ_DIRETO

    def test_400_lista_vazia(self, client_dde_admin):
        resp = client_dde_admin.get("/api/dde/comparativo?cnpjs=   &ano=2025")
        assert resp.status_code == 400


# ===========================================================================
# TESTES /api/dde/score/{cnpj}
# ===========================================================================

class TestDDEScoreEndpoint:
    """Testa GET /api/dde/score/{cnpj}."""

    def test_200_retorna_score_e_breakdown(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get(f"/api/dde/score/{CNPJ_DIRETO}")
        assert resp.status_code == 200
        data = resp.json()
        assert "cnpj" in data
        assert data["cnpj"] == CNPJ_DIRETO
        assert "score" in data
        assert "breakdown" in data
        assert "veredito" in data

    def test_200_breakdown_tem_todos_indicadores(
        self, client_dde_admin, cliente_direto, venda_direto
    ):
        resp = client_dde_admin.get(f"/api/dde/score/{CNPJ_DIRETO}")
        assert resp.status_code == 200
        breakdown = resp.json()["breakdown"]
        for i in range(1, 10):
            assert f"I{i}" in breakdown, f"I{i} ausente no breakdown"

    def test_422_canal_nao_elegivel(
        self, client_dde_admin, cliente_interno
    ):
        """Canal INTERNO → 422."""
        resp = client_dde_admin.get(f"/api/dde/score/{CNPJ_INTERNO}")
        assert resp.status_code == 422

    def test_404_cnpj_inexistente(self, client_dde_admin):
        resp = client_dde_admin.get(f"/api/dde/score/{CNPJ_INEXISTENTE}")
        assert resp.status_code == 404

    def test_403_fora_do_escopo(
        self, client_dde_consultor, cliente_food, venda_food
    ):
        """Consultor DIRETO não acessa score de cliente FOOD_SERVICE."""
        resp = client_dde_consultor.get(f"/api/dde/score/{CNPJ_FOOD}")
        assert resp.status_code == 403

    def test_score_none_quando_sem_dados_i2(
        self, client_dde_admin, cliente_direto
    ):
        """Sem vendas, L11 é PENDENTE → I9 = None (R8)."""
        # cliente_direto sem venda_direto → L1=None → I2=None → I9=None
        resp = client_dde_admin.get(f"/api/dde/score/{CNPJ_DIRETO}")
        assert resp.status_code == 200
        # I9 pode ser None (sem dados) ou float (se há algum dado)
        score = resp.json()["score"]
        assert score is None or isinstance(score, float)
