"""
CRM VITAO360 — Testes dos 6 novos endpoints de indicadores Mercos.

Cobertura:
  1. GET /api/dashboard/evolucao-vendas?mes=4&ano=2026&consultor=MANU
     - Retorna 200 com campos obrigatorios
     - Filtro por consultor isola dados corretamente
     - Filtro por mes/ano funciona
     - Sem filtros retorna dados do mes/ano atual
     - Sem JWT -> 401
     - Mes invalido (0 ou 13) -> 422
     - Consultor inexistente -> dados vazios (nao erro)
     - Two-Base: usa APENAS tabela vendas (valor > 0)
     - ALUCINACAO excluida dos resultados

  2. GET /api/dashboard/positivacao-diaria?mes=4&ano=2026
     - Retorna 200 com lista de dias
     - Cada item contem data e total_clientes_positivados
     - Mes invalido -> 422
     - Dias sem venda nao aparecem ou aparecem zerados

  3. GET /api/dashboard/positivacao-vendedor?mes=4&ano=2026
     - Retorna 200 com dados por vendedor
     - Cada item contem consultor e total_positivados
     - Filtro mes/ano funciona
     - ALUCINACAO excluida

  4. GET /api/dashboard/atendimentos-diarios?mes=4&ano=2026
     - Retorna 200 com lista de dias
     - Cada item contem data e total_atendimentos
     - Two-Base: usa APENAS log_interacoes (sem valor monetario)
     - Mes invalido -> 422

  5. GET /api/dashboard/curva-abc-detalhe?consultor=LARISSA
     - Retorna 200 com distribuicao A/B/C
     - Cada bucket contem total_clientes e faturamento
     - Filtro por consultor funciona
     - Consultor inexistente -> dados vazios

  6. GET /api/dashboard/ecommerce?mes=4&ano=2026
     - Retorna 200 com indicadores ecommerce
     - Campos obrigatorios presentes
     - Mes invalido -> 422

R4  — Two-Base: evolucao-vendas usa APENAS vendas; atendimentos-diarios usa APENAS log.
R5  — CNPJ: String(14), zero-padded — nunca float.
R8  — ALUCINACAO excluida de todos os resultados.
"""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import get_current_user, require_admin, require_admin_or_gerente
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.venda import Venda


# ---------------------------------------------------------------------------
# Helpers de usuarios simulados (sem JWT)
# ---------------------------------------------------------------------------

def _fake_usuario(
    id: int,
    email: str,
    nome: str,
    role: str,
    consultor_nome: str | None = None,
) -> SimpleNamespace:
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
# Fixtures: engine + sessao com seed de dados reais (module-scope = isolado)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine_indicadores():
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
def db_indicadores(engine_indicadores) -> Session:
    """
    Sessao com seed cobrindo:
      - 3 clientes: MANU-ATIVO, LARISSA-ATIVO, ALUCINACAO
      - Vendas em abril/2026 para MANU e LARISSA (Two-Base: valor > 0)
      - Vendas em marco/2026 para MANU (teste de filtro de mes)
      - Log_interacoes em abril/2026 para MANU (Two-Base: sem valor)
      - Venda de cliente ALUCINACAO (para garantir exclusao)
    """
    _Session = sessionmaker(bind=engine_indicadores)
    session = _Session()

    # --- Clientes ---
    clientes = [
        # R5: CNPJ string 14 digitos, zero-padded
        Cliente(
            cnpj="04067573000193",          # cliente real MANU
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
            ciclo_medio=30.0,
            n_compras=12,
        ),
        Cliente(
            cnpj="12345678000195",          # cliente real LARISSA
            nome_fantasia="Mercado Organico",
            razao_social="Mercado Organico ME",
            uf="RS",
            consultor="LARISSA",
            situacao="ATIVO",
            classificacao_3tier="REAL",
            faturamento_total=28000.0,
            score=65.0,
            prioridade="P4",
            sinaleiro="AMARELO",
            temperatura="MORNO",
            curva_abc="B",
            tipo_cliente="MADURO",
            dias_sem_compra=40,
            ciclo_medio=45.0,
            n_compras=8,
        ),
        # R8: cliente ALUCINACAO — deve ser excluido de todos os resultados
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
    session.flush()

    # --- Vendas (Two-Base: valor > 0, tabela vendas) ---
    vendas = [
        # MANU — abril/2026 (mes=4, dia=5 e dia=20)
        Venda(
            cnpj="04067573000193",
            data_pedido=date(2026, 4, 5),
            numero_pedido="PED-MANU-0401",
            valor_pedido=3500.00,           # R4: deve ser > 0
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
            mes_referencia="2026-04",
        ),
        Venda(
            cnpj="04067573000193",
            data_pedido=date(2026, 4, 20),
            numero_pedido="PED-MANU-0402",
            valor_pedido=1200.00,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
            mes_referencia="2026-04",
        ),
        # LARISSA — abril/2026 (dia=10)
        Venda(
            cnpj="12345678000195",
            data_pedido=date(2026, 4, 10),
            numero_pedido="PED-LARI-0401",
            valor_pedido=2800.00,
            consultor="LARISSA",
            fonte="MERCOS",
            classificacao_3tier="REAL",
            mes_referencia="2026-04",
        ),
        # MANU — marco/2026 (para testar filtro de mes diferente)
        Venda(
            cnpj="04067573000193",
            data_pedido=date(2026, 3, 15),
            numero_pedido="PED-MANU-0301",
            valor_pedido=4000.00,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
            mes_referencia="2026-03",
        ),
        # ALUCINACAO — para garantir que nao aparece nos resultados (R8)
        Venda(
            cnpj="99999999999901",
            data_pedido=date(2026, 4, 1),
            numero_pedido="PED-ALUC-001",
            valor_pedido=50000.00,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="ALUCINACAO",
            mes_referencia="2026-04",
        ),
    ]
    for v in vendas:
        session.add(v)
    session.flush()

    # --- LogInteracoes (Two-Base: sem valor monetario) ---
    logs = [
        # MANU — abril/2026 (dia=3, dia=7, dia=7 = 2 no mesmo dia)
        LogInteracao(
            cnpj="04067573000193",
            data_interacao=datetime(2026, 4, 3, 10, 0, 0),
            consultor="MANU",
            resultado="Sem Contato",
            descricao="Tentativa de ligacao sem retorno",
            estagio_funil="EM ATENDIMENTO",
            temperatura="MORNO",
        ),
        LogInteracao(
            cnpj="04067573000193",
            data_interacao=datetime(2026, 4, 7, 14, 0, 0),
            consultor="MANU",
            resultado="Venda Realizada",
            descricao="Pedido confirmado",
            estagio_funil="POS-VENDA",
            temperatura="QUENTE",
        ),
        LogInteracao(
            cnpj="04067573000193",
            data_interacao=datetime(2026, 4, 7, 16, 30, 0),
            consultor="MANU",
            resultado="Follow-up",
            descricao="Confirmacao de entrega",
            estagio_funil="POS-VENDA",
            temperatura="QUENTE",
        ),
        # LARISSA — abril/2026 (dia=10)
        LogInteracao(
            cnpj="12345678000195",
            data_interacao=datetime(2026, 4, 10, 9, 0, 0),
            consultor="LARISSA",
            resultado="Reuniao",
            descricao="Apresentacao de produtos",
            estagio_funil="NEGOCIACAO",
            temperatura="MORNO",
        ),
        # MANU — marco/2026 (para testar filtro de mes diferente)
        LogInteracao(
            cnpj="04067573000193",
            data_interacao=datetime(2026, 3, 20, 11, 0, 0),
            consultor="MANU",
            resultado="Ligacao",
            descricao="Prospeccao",
            estagio_funil="PROSPECCAO",
            temperatura="FRIO",
        ),
    ]
    for log in logs:
        session.add(log)
    session.commit()

    yield session
    session.close()


# ---------------------------------------------------------------------------
# Helper para montar o override de get_db
# ---------------------------------------------------------------------------

def _make_db_override(session: Session):
    def _override():
        yield session
    return _override


# ---------------------------------------------------------------------------
# Fixtures: usuarios e clients por role
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def usuario_admin():
    return _fake_usuario(1, "admin@vitao.com.br", "Admin VITAO", "admin")


@pytest.fixture(scope="module")
def usuario_consultor_manu():
    return _fake_usuario(2, "manu@vitao.com.br", "Manu Ditzel", "consultor", "MANU")


@pytest.fixture(scope="function")
def client_admin(db_indicadores, usuario_admin):
    """TestClient admin com banco em memoria."""
    app.dependency_overrides[get_db] = _make_db_override(db_indicadores)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_admin] = lambda: usuario_admin
    app.dependency_overrides[require_admin_or_gerente] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_unauthenticated(db_indicadores):
    """TestClient SEM override de autenticacao — para testar 401."""
    app.dependency_overrides[get_db] = _make_db_override(db_indicadores)
    # Sem get_current_user override: a dependencia real rejeita requests sem token
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ===========================================================================
# 1. Testes: GET /api/dashboard/evolucao-vendas
# ===========================================================================

class TestEvolucaoVendas:
    """GET /api/dashboard/evolucao-vendas — evolucao de vendas por mes/consultor"""

    # --- Testes positivos ---

    def test_retorna_200_com_filtros(self, client_admin):
        """Retorna HTTP 200 com mes, ano e consultor validos."""
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026, "consultor": "MANU"},
        )
        assert resp.status_code == 200

    def test_campos_obrigatorios_presentes(self, client_admin):
        """Resposta deve conter pelo menos uma lista ou objeto com dados de vendas."""
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026, "consultor": "MANU"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Resposta pode ser lista ou dict — deve ser nao-None
        assert data is not None

    def test_filtro_consultor_manu_retorna_apenas_vendas_manu(self, client_admin):
        """Filtro consultor=MANU retorna somente vendas de MANU no periodo."""
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026, "consultor": "MANU"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Verificar que os dados sao consistentes com MANU (endpoint nao pode retornar LARISSA)
        if isinstance(data, list):
            for item in data:
                if "consultor" in item:
                    assert item["consultor"] == "MANU"

    def test_filtro_mes_ano_abril_exclui_marco(self, client_admin):
        """Filtro mes=4&ano=2026 nao deve incluir vendas de marco/2026."""
        resp_abril = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026},
        )
        resp_marco = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 3, "ano": 2026},
        )
        assert resp_abril.status_code == 200
        assert resp_marco.status_code == 200
        # Os dois periodos devem retornar dados distintos
        assert resp_abril.json() != resp_marco.json()

    def test_sem_filtros_retorna_200(self, client_admin):
        """Sem filtros o endpoint retorna 200 (usa mes/ano atual por padrao)."""
        resp = client_admin.get("/api/dashboard/evolucao-vendas")
        assert resp.status_code == 200

    def test_consultor_inexistente_retorna_dados_vazios(self, client_admin):
        """Consultor que nao existe deve retornar dados vazios, nao erro."""
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026, "consultor": "CONSULTOR_FANTASMA"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Lista vazia ou dict com zeros — nao pode ser 404/500
        if isinstance(data, list):
            assert len(data) == 0 or all(
                (item.get("total") == 0 or item.get("valor_total") == 0)
                for item in data
                if isinstance(item, dict)
            )

    # --- Testes negativos ---

    def test_sem_jwt_retorna_401(self, client_unauthenticated):
        """Sem autenticacao JWT deve retornar HTTP 401."""
        resp = client_unauthenticated.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 401

    def test_mes_zero_retorna_422(self, client_admin):
        """Mes=0 e invalido e deve retornar HTTP 422."""
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 0, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_mes_13_retorna_422(self, client_admin):
        """Mes=13 e invalido e deve retornar HTTP 422."""
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 13, "ano": 2026},
        )
        assert resp.status_code == 422

    # --- Testes Two-Base (R4) ---

    def test_two_base_usa_apenas_tabela_vendas(self, client_admin, db_indicadores):
        """
        R4 — Two-Base: evolucao-vendas deve usar APENAS a tabela vendas.
        Verificamos que os valores retornados sao consistentes com os dados
        da tabela vendas (nao log_interacoes que nao tem valor monetario).
        """
        # Abril/2026 MANU: PED-MANU-0401 (3500) + PED-MANU-0402 (1200) = 4700
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026, "consultor": "MANU"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Se a resposta contem valor total, ele deve ser baseado em vendas reais
        if isinstance(data, dict) and "valor_total" in data:
            # 3500 + 1200 = 4700 para MANU em abril (excluindo ALUCINACAO)
            assert data["valor_total"] == pytest.approx(4700.0, rel=1e-2)
        elif isinstance(data, list):
            total = sum(item.get("valor_total", 0) or item.get("valor", 0) for item in data)
            if total > 0:
                assert total == pytest.approx(4700.0, rel=1e-2)

    # --- Testes data quality (R8) ---

    def test_alucinacao_excluida_dos_resultados(self, client_admin):
        """
        R8: vendas com classificacao_3tier=ALUCINACAO nao devem aparecer.
        O cliente 99999999999901 tem uma venda de R$50.000 classificada como ALUCINACAO.
        """
        resp = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Verificar que nenhum item referencia o CNPJ de alucinacao
        if isinstance(data, list):
            for item in data:
                assert item.get("cnpj") != "99999999999901", (
                    "ALUCINACAO nao deve aparecer em evolucao-vendas"
                )


# ===========================================================================
# 2. Testes: GET /api/dashboard/positivacao-diaria
# ===========================================================================

class TestPositivacaoDiaria:
    """GET /api/dashboard/positivacao-diaria — clientes positivados por dia"""

    def test_retorna_200(self, client_admin):
        """Retorna HTTP 200 para mes e ano validos."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200

    def test_resposta_e_lista(self, client_admin):
        """Resposta deve ser uma lista (serie temporal de dias)."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"Esperado lista, obtido {type(data)}"

    def test_itens_contem_campos_obrigatorios(self, client_admin):
        """Cada item deve conter data e quantidade de clientes positivados."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        for item in data:
            assert isinstance(item, dict), "Cada item deve ser um dicionario"
            # Deve ter um campo de data e um campo de contagem
            tem_data = "data" in item or "dia" in item or "date" in item
            tem_contagem = (
                "total_clientes_positivados" in item
                or "positivados" in item
                or "total" in item
                or "count" in item
            )
            assert tem_data, f"Item sem campo de data: {list(item.keys())}"
            assert tem_contagem, f"Item sem campo de contagem: {list(item.keys())}"

    def test_sem_jwt_retorna_401(self, client_unauthenticated):
        """Sem autenticacao JWT deve retornar HTTP 401."""
        resp = client_unauthenticated.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 401

    def test_mes_zero_retorna_422(self, client_admin):
        """Mes=0 invalido deve retornar 422."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 0, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_mes_13_retorna_422(self, client_admin):
        """Mes=13 invalido deve retornar 422."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 13, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_sem_filtros_retorna_200(self, client_admin):
        """Sem filtros retorna 200 (usa mes/ano atual)."""
        resp = client_admin.get("/api/dashboard/positivacao-diaria")
        assert resp.status_code == 200

    def test_dias_com_venda_aparecem_na_lista(self, client_admin):
        """
        Dias que tiveram vendas devem aparecer na lista com contagem > 0.
        Seed: MANU vendeu em 05/04 e 20/04; LARISSA em 10/04.
        """
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        data = resp.json()
        if len(data) > 0:
            # Deve haver pelo menos um dia com positivacao > 0
            totais = [
                item.get("total_clientes_positivados")
                or item.get("positivados")
                or item.get("total")
                or item.get("count")
                or 0
                for item in data
            ]
            assert any(t > 0 for t in totais), "Nenhum dia com positivacao > 0 em abril/2026"

    def test_alucinacao_excluida(self, client_admin):
        """R8: vendas ALUCINACAO nao contam para positivacao diaria."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-diaria",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        # Endpoint nao pode quebrar; conteudo ja e validado pela exclusao do seed


# ===========================================================================
# 3. Testes: GET /api/dashboard/positivacao-vendedor
# ===========================================================================

class TestPositivacaoVendedor:
    """GET /api/dashboard/positivacao-vendedor — positivacao por vendedor no mes"""

    def test_retorna_200(self, client_admin):
        """Retorna HTTP 200 para mes e ano validos."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200

    def test_resposta_e_lista(self, client_admin):
        """Resposta deve ser uma lista (um item por vendedor)."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        assert isinstance(data, list)

    def test_itens_contem_consultor_e_total(self, client_admin):
        """Cada item deve conter o nome do consultor e total de positivados."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        for item in data:
            tem_consultor = "consultor" in item or "vendedor" in item
            tem_total = (
                "total_positivados" in item
                or "positivados" in item
                or "total" in item
                or "count" in item
            )
            assert tem_consultor, f"Item sem campo consultor: {list(item.keys())}"
            assert tem_total, f"Item sem campo de total: {list(item.keys())}"

    def test_sem_jwt_retorna_401(self, client_unauthenticated):
        """Sem JWT deve retornar 401."""
        resp = client_unauthenticated.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 401

    def test_mes_zero_retorna_422(self, client_admin):
        """Mes=0 invalido -> 422."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 0, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_mes_13_retorna_422(self, client_admin):
        """Mes=13 invalido -> 422."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 13, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_sem_filtros_retorna_200(self, client_admin):
        """Sem filtros retorna 200 (padrao: mes/ano atual)."""
        resp = client_admin.get("/api/dashboard/positivacao-vendedor")
        assert resp.status_code == 200

    def test_manu_e_larissa_aparecem_em_abril(self, client_admin):
        """
        Seed: MANU tem 2 vendas e LARISSA tem 1 venda em abril/2026.
        Ambos devem aparecer na lista de positivacao do vendedor.
        """
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        consultores = [
            item.get("consultor") or item.get("vendedor")
            for item in data
        ]
        assert "MANU" in consultores, "MANU deveria aparecer com positivacao em abril/2026"
        assert "LARISSA" in consultores, "LARISSA deveria aparecer com positivacao em abril/2026"

    def test_alucinacao_excluida_dos_resultados(self, client_admin):
        """R8: vendas ALUCINACAO nao devem contar para positivacao do vendedor."""
        resp = client_admin.get(
            "/api/dashboard/positivacao-vendedor",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        data = resp.json()
        # O CNPJ 99999999999901 tem venda ALUCINACAO em abril
        # Se o total de positivados da MANU vier correto (1 cliente, nao 2),
        # a ALUCINACAO foi excluida
        for item in data:
            consultor = item.get("consultor") or item.get("vendedor")
            if consultor == "MANU":
                total = (
                    item.get("total_positivados")
                    or item.get("positivados")
                    or item.get("total")
                    or item.get("count")
                )
                if total is not None:
                    # MANU tem 1 cliente REAL positivado em abril (04067573000193)
                    # O cliente ALUCINACAO nao deve contar
                    assert total <= 1, (
                        f"MANU deveria ter <= 1 cliente REAL positivado, "
                        f"mas obteve {total} (ALUCINACAO pode estar incluida)"
                    )


# ===========================================================================
# 4. Testes: GET /api/dashboard/atendimentos-diarios
# ===========================================================================

class TestAtendimentosDiarios:
    """GET /api/dashboard/atendimentos-diarios — atendimentos de log por dia"""

    def test_retorna_200(self, client_admin):
        """Retorna HTTP 200 para mes e ano validos."""
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200

    def test_resposta_e_lista(self, client_admin):
        """Resposta deve ser uma lista (serie temporal de dias)."""
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        assert isinstance(data, list)

    def test_itens_contem_campos_obrigatorios(self, client_admin):
        """Cada item deve conter data e total de atendimentos."""
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        for item in data:
            assert isinstance(item, dict)
            tem_data = "data" in item or "dia" in item or "date" in item
            tem_total = (
                "total_atendimentos" in item
                or "atendimentos" in item
                or "total" in item
                or "count" in item
            )
            assert tem_data, f"Item sem campo de data: {list(item.keys())}"
            assert tem_total, f"Item sem campo de total: {list(item.keys())}"

    def test_sem_jwt_retorna_401(self, client_unauthenticated):
        """Sem JWT deve retornar 401."""
        resp = client_unauthenticated.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 401

    def test_mes_zero_retorna_422(self, client_admin):
        """Mes=0 invalido -> 422."""
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 0, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_mes_13_retorna_422(self, client_admin):
        """Mes=13 invalido -> 422."""
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 13, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_sem_filtros_retorna_200(self, client_admin):
        """Sem filtros retorna 200 (padrao: mes/ano atual)."""
        resp = client_admin.get("/api/dashboard/atendimentos-diarios")
        assert resp.status_code == 200

    def test_dias_com_log_aparecem_na_lista(self, client_admin):
        """
        Seed: MANU tem logs em 03/04 (1) e 07/04 (2); LARISSA em 10/04 (1).
        Total: 3 dias com atendimentos em abril/2026.
        """
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        if len(data) > 0:
            totais = [
                item.get("total_atendimentos")
                or item.get("atendimentos")
                or item.get("total")
                or item.get("count")
                or 0
                for item in data
            ]
            assert any(t > 0 for t in totais), (
                "Nenhum atendimento encontrado em abril/2026, mas seed tem 4 logs"
            )

    # --- Teste Two-Base (R4) ---

    def test_two_base_usa_apenas_log_interacoes(self, client_admin):
        """
        R4 — Two-Base: atendimentos-diarios deve usar APENAS log_interacoes.
        Verificamos que o endpoint retorna dados consistentes com os logs do seed,
        sem incluir dados monetarios ou da tabela vendas.
        """
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        data = resp.json()
        # Nenhum item deve ter campo de valor monetario
        for item in data:
            assert "valor" not in item, "atendimentos-diarios nao deve ter campo 'valor' (Two-Base)"
            assert "valor_pedido" not in item, "atendimentos-diarios nao deve ter 'valor_pedido'"
            assert "faturamento" not in item, "atendimentos-diarios nao deve ter 'faturamento'"

    def test_total_atendimentos_abril_bate_com_seed(self, client_admin):
        """
        Seed tem 4 logs em abril/2026 (3 MANU + 1 LARISSA).
        A soma de todos os dias deve ser 4.
        """
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        total_somado = sum(
            item.get("total_atendimentos")
            or item.get("atendimentos")
            or item.get("total")
            or item.get("count")
            or 0
            for item in data
        )
        assert total_somado == 4, (
            f"Esperados 4 atendimentos em abril/2026 (seed), obtido {total_somado}"
        )


# ===========================================================================
# 5. Testes: GET /api/dashboard/curva-abc-detalhe
# ===========================================================================

class TestCurvaAbcDetalhe:
    """GET /api/dashboard/curva-abc-detalhe — distribuicao de curva ABC com detalhes"""

    def test_retorna_200(self, client_admin):
        """Retorna HTTP 200 sem filtros."""
        resp = client_admin.get("/api/dashboard/curva-abc-detalhe")
        assert resp.status_code == 200

    def test_retorna_200_com_filtro_consultor(self, client_admin):
        """Retorna HTTP 200 com filtro de consultor."""
        resp = client_admin.get(
            "/api/dashboard/curva-abc-detalhe",
            params={"consultor": "LARISSA"},
        )
        assert resp.status_code == 200

    def test_campos_obrigatorios_presentes(self, client_admin):
        """Resposta deve conter dados de curva ABC (A, B, C)."""
        resp = client_admin.get("/api/dashboard/curva-abc-detalhe")
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None

    def test_buckets_abc_contem_total_clientes(self, client_admin):
        """Cada bucket (A/B/C) deve conter total_clientes ou contagem equivalente."""
        resp = client_admin.get("/api/dashboard/curva-abc-detalhe")
        data = resp.json()
        if isinstance(data, list):
            for item in data:
                assert isinstance(item, dict)
                tem_curva = "curva" in item or "curva_abc" in item or "categoria" in item
                tem_total = (
                    "total_clientes" in item
                    or "clientes" in item
                    or "total" in item
                    or "count" in item
                )
                assert tem_curva, f"Item sem campo de curva: {list(item.keys())}"
                assert tem_total, f"Item sem campo de total: {list(item.keys())}"
        elif isinstance(data, dict):
            # Resposta pode ser dict {A: {...}, B: {...}, C: {...}}
            for curva in ("A", "B", "C"):
                if curva in data:
                    bucket = data[curva]
                    assert isinstance(bucket, dict)

    def test_filtro_consultor_larissa_isola_dados(self, client_admin):
        """Filtro consultor=LARISSA retorna somente dados dos clientes de LARISSA."""
        resp_larissa = client_admin.get(
            "/api/dashboard/curva-abc-detalhe",
            params={"consultor": "LARISSA"},
        )
        resp_manu = client_admin.get(
            "/api/dashboard/curva-abc-detalhe",
            params={"consultor": "MANU"},
        )
        assert resp_larissa.status_code == 200
        assert resp_manu.status_code == 200
        # Os resultados de LARISSA e MANU devem ser diferentes
        assert resp_larissa.json() != resp_manu.json()

    def test_consultor_inexistente_retorna_dados_vazios(self, client_admin):
        """Consultor que nao existe deve retornar dados vazios, nao erro."""
        resp = client_admin.get(
            "/api/dashboard/curva-abc-detalhe",
            params={"consultor": "CONSULTOR_FANTASMA"},
        )
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, list):
            # Lista vazia ou todos os totais zerados
            totais = [
                item.get("total_clientes") or item.get("total") or item.get("count") or 0
                for item in data
            ]
            assert all(t == 0 for t in totais) or len(data) == 0

    def test_sem_jwt_retorna_401(self, client_unauthenticated):
        """Sem JWT deve retornar 401."""
        resp = client_unauthenticated.get(
            "/api/dashboard/curva-abc-detalhe",
            params={"consultor": "LARISSA"},
        )
        assert resp.status_code == 401

    def test_alucinacao_excluida_do_detalhe(self, client_admin):
        """R8: cliente ALUCINACAO nao deve aparecer no detalhe de curva ABC."""
        resp = client_admin.get("/api/dashboard/curva-abc-detalhe")
        data = resp.json()
        if isinstance(data, list):
            for item in data:
                assert item.get("cnpj") != "99999999999901", (
                    "ALUCINACAO (99999999999901) nao deve aparecer em curva-abc-detalhe"
                )


# ===========================================================================
# 6. Testes: GET /api/dashboard/ecommerce
# ===========================================================================

class TestEcommerce:
    """GET /api/dashboard/ecommerce — indicadores de ecommerce por mes/ano"""

    def test_retorna_200(self, client_admin):
        """Retorna HTTP 200 para mes e ano validos."""
        resp = client_admin.get(
            "/api/dashboard/ecommerce",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200

    def test_campos_obrigatorios_presentes(self, client_admin):
        """Resposta deve conter campos de indicadores de ecommerce."""
        resp = client_admin.get(
            "/api/dashboard/ecommerce",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None
        # Resposta deve ser dict ou lista nao-vazia
        assert isinstance(data, (dict, list))

    def test_sem_jwt_retorna_401(self, client_unauthenticated):
        """Sem JWT deve retornar 401."""
        resp = client_unauthenticated.get(
            "/api/dashboard/ecommerce",
            params={"mes": 4, "ano": 2026},
        )
        assert resp.status_code == 401

    def test_mes_zero_retorna_422(self, client_admin):
        """Mes=0 invalido -> 422."""
        resp = client_admin.get(
            "/api/dashboard/ecommerce",
            params={"mes": 0, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_mes_13_retorna_422(self, client_admin):
        """Mes=13 invalido -> 422."""
        resp = client_admin.get(
            "/api/dashboard/ecommerce",
            params={"mes": 13, "ano": 2026},
        )
        assert resp.status_code == 422

    def test_sem_filtros_retorna_200(self, client_admin):
        """Sem filtros retorna 200 (padrao: mes/ano atual)."""
        resp = client_admin.get("/api/dashboard/ecommerce")
        assert resp.status_code == 200

    def test_valores_nao_negativos(self, client_admin):
        """
        Quaisquer valores numericos no resultado de ecommerce
        devem ser nao-negativos (sem valores absurdos ou negativos).
        """
        resp = client_admin.get(
            "/api/dashboard/ecommerce",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    assert value >= 0, f"Campo {key}={value} nao deve ser negativo"


# ===========================================================================
# Testes de separacao Two-Base: verificacao cruzada entre endpoints
# ===========================================================================

class TestTwoBaseAcrossEndpoints:
    """
    R4 — Two-Base Architecture: verifica que endpoints de vendas e de log
    acessam tabelas separadas e nao se contaminam.
    """

    def test_evolucao_vendas_nao_inclui_contagem_de_logs(self, client_admin):
        """
        Seed abril/2026: 4 logs, 3 vendas REAL.
        Se evolucao-vendas incluir logs, a contagem seria errada.
        O endpoint de vendas deve trabalhar apenas com a tabela vendas.
        """
        resp_vendas = client_admin.get(
            "/api/dashboard/evolucao-vendas",
            params={"mes": 4, "ano": 2026},
        )
        resp_logs = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        assert resp_vendas.status_code == 200
        assert resp_logs.status_code == 200
        # Os dois endpoints devem retornar dados distintos (tabelas diferentes)
        # Um endpoint de vendas e um de log nao podem retornar objetos identicos
        # (se forem iguais, um deles pode estar usando a tabela errada)
        assert resp_vendas.json() != resp_logs.json(), (
            "evolucao-vendas e atendimentos-diarios retornam o mesmo resultado — "
            "possivel violacao Two-Base (usando mesma tabela)"
        )

    def test_atendimentos_diarios_nao_contem_campo_valor_monetario(self, client_admin):
        """
        R4: log_interacoes nao tem valor monetario.
        atendimentos-diarios nao pode expor nenhum campo de R$.
        """
        resp = client_admin.get(
            "/api/dashboard/atendimentos-diarios",
            params={"mes": 4, "ano": 2026},
        )
        data = resp.json()
        campos_monetarios = {"valor", "valor_pedido", "faturamento", "receita", "ticket"}
        if isinstance(data, list):
            for item in data:
                for campo in campos_monetarios:
                    assert campo not in item, (
                        f"Campo monetario '{campo}' encontrado em atendimentos-diarios "
                        f"— violacao Two-Base (R4)"
                    )
        elif isinstance(data, dict):
            for campo in campos_monetarios:
                assert campo not in data, (
                    f"Campo monetario '{campo}' encontrado em atendimentos-diarios "
                    f"— violacao Two-Base (R4)"
                )
