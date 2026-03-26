"""
CRM VITAO360 — Testes do modulo de Vendas (Two-Base: metade VENDA).

Valida:
  1. Registrar venda com valor > 0 retorna 201 com dados corretos
  2. Venda com valor <= 0 e rejeitada pelo schema Pydantic (422)
  3. Venda com CNPJ inexistente retorna 404
  4. GET /totais calcula corretamente para N vendas (soma, ticket medio, por_consultor, por_mes)
  5. Two-Base: model Venda NAO possui campos de interacao (log, resultado, fase, estagio_funil)
  6. Filtro por consultor: consultor ve apenas seus registros, admin ve todos
  7. R8: ALUCINACAO e excluida do calculo de faturamento

Fixtures:
  - engine SQLite em memoria (isolamento total entre testes)
  - 1 cliente seed (CNPJ 12345678000100, consultor MANU)
  - get_db sobrescrito via dependency_overrides (pattern correto para TestClient)
  - usuarios admin/consultor injetados sem JWT

Padrao de autenticacao:
  As rotas usam Depends(get_current_user) e Depends(require_admin).
  Nos testes, sobrescrevemos essas dependencias via app.dependency_overrides
  para injetar usuarios diretos sem JWT, mantendo a logica de autorizacao intacta.

  IMPORTANTE: get_db precisa ser sobrescrito como generator (yield session)
  para que o TestClient use a mesma session que os seeds.
"""

from __future__ import annotations

import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.api.deps import get_current_user, require_admin, require_consultor_or_admin
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.venda import Venda
from backend.app.schemas.venda import VendaCreate


# ---------------------------------------------------------------------------
# Fixtures de banco
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine_mem():
    """
    Engine SQLite em memoria — isolamento completo entre funcoes de teste.

    StaticPool garante que todas as threads do TestClient compartilhem a mesma
    conexao em memoria. Sem StaticPool, threads diferentes veem bancos diferentes
    e a session injetada via get_db nao enxerga os dados do seed.
    """
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine_mem) -> Session:
    """
    Session com seed basico:
      - 1 cliente ATIVO (CNPJ 12345678000100, consultor MANU)

    Retorna a session ativa para que os testes possam adicionar dados adicionais.
    """
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    cliente = Cliente(
        cnpj="12345678000100",
        nome_fantasia="Distribuidora Teste Ltda",
        situacao="ATIVO",
        consultor="MANU",
        classificacao_3tier="REAL",
    )
    session.add(cliente)
    session.commit()

    yield session
    session.close()


def _make_get_db_override(session: Session):
    """
    Fabrica um override generator para get_db que reutiliza a session do teste.
    O generator padrao do FastAPI faz yield e depois fecha — aqui nao fechamos
    porque a session pertence ao ciclo de vida do teste.
    """
    def _override():
        yield session
    return _override


# ---------------------------------------------------------------------------
# Fixtures de usuarios
# ---------------------------------------------------------------------------

def _fake_usuario(
    id: int,
    email: str,
    nome: str,
    role: str,
    consultor_nome: str | None = None,
) -> SimpleNamespace:
    """
    Cria um objeto simples que imita um Usuario ORM para injecao via dependency_overrides.
    Usa SimpleNamespace em vez de Usuario() para evitar o overhead do SQLAlchemy mapper
    e o erro '_sa_instance_state' ao criar objetos fora de uma session.
    Os campos acessados nas rotas sao: role, nome, consultor_nome, id, ativo.
    """
    return SimpleNamespace(
        id=id,
        email=email,
        nome=nome,
        hashed_password="hash_fake",
        role=role,
        consultor_nome=consultor_nome,
        ativo=True,
    )


@pytest.fixture(scope="function")
def usuario_admin():
    """Usuario com role admin — acesso irrestrito."""
    return _fake_usuario(1, "admin@vitao.com", "Admin VITAO", "admin")


@pytest.fixture(scope="function")
def usuario_consultor_manu():
    """Usuario com role consultor vinculado a MANU."""
    return _fake_usuario(2, "manu@vitao.com", "Manu Ditzel", "consultor", "MANU")


@pytest.fixture(scope="function")
def usuario_consultor_larissa():
    """Usuario com role consultor vinculado a LARISSA."""
    return _fake_usuario(3, "larissa@vitao.com", "Larissa Padilha", "consultor", "LARISSA")


# ---------------------------------------------------------------------------
# Fixtures de TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db_session, usuario_admin):
    """TestClient com usuario admin e banco em memoria injetados."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_admin] = lambda: usuario_admin
    app.dependency_overrides[require_consultor_or_admin] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_manu(db_session, usuario_consultor_manu):
    """TestClient com usuario consultor MANU e banco em memoria injetados."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_consultor_manu
    app.dependency_overrides[require_admin] = lambda: usuario_consultor_manu
    app.dependency_overrides[require_consultor_or_admin] = lambda: usuario_consultor_manu
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_larissa(db_session, usuario_consultor_larissa):
    """TestClient com usuario consultor LARISSA e banco em memoria injetados."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_consultor_larissa
    app.dependency_overrides[require_admin] = lambda: usuario_consultor_larissa
    app.dependency_overrides[require_consultor_or_admin] = lambda: usuario_consultor_larissa
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Testes: POST /api/vendas — registro de venda
# ---------------------------------------------------------------------------

class TestCriarVenda:
    """Testa o endpoint POST /api/vendas."""

    def test_criar_venda_sucesso(self, client_admin):
        """
        Cenario feliz: venda valida (valor > 0, CNPJ existente) retorna 201
        com todos os campos esperados, incluindo mes_referencia derivado da data_pedido.
        """
        payload = {
            "cnpj": "12345678000100",
            "data_pedido": "2026-03-15",
            "numero_pedido": "MRC-00001",
            "valor_pedido": 1500.00,
            "fonte": "MERCOS",
        }
        resp = client_admin.post("/api/vendas", json=payload)

        assert resp.status_code == 201, resp.text
        data = resp.json()

        assert data["cnpj"] == "12345678000100"
        assert data["valor_pedido"] == 1500.00
        assert data["numero_pedido"] == "MRC-00001"
        assert data["fonte"] == "MERCOS"
        assert data["mes_referencia"] == "2026-03"
        assert data["classificacao_3tier"] == "REAL"
        assert data["nome_fantasia"] == "Distribuidora Teste Ltda"
        assert "id" in data
        assert "created_at" in data

    def test_criar_venda_valor_zero_rejeitado(self, client_admin):
        """
        R4: valor_pedido = 0 deve ser rejeitado pelo schema Pydantic (HTTP 422).
        Valor zero na tabela vendas viola a Two-Base Architecture.
        """
        payload = {
            "cnpj": "12345678000100",
            "data_pedido": "2026-03-15",
            "valor_pedido": 0.0,
            "fonte": "MANUAL",
        }
        resp = client_admin.post("/api/vendas", json=payload)

        assert resp.status_code == 422, (
            f"Esperado 422 (Pydantic rejeita valor <= 0), recebido {resp.status_code}: {resp.text}"
        )

    def test_criar_venda_valor_negativo_rejeitado(self, client_admin):
        """
        R4: valor_pedido negativo tambem deve ser rejeitado (HTTP 422).
        """
        payload = {
            "cnpj": "12345678000100",
            "data_pedido": "2026-03-15",
            "valor_pedido": -100.0,
            "fonte": "MANUAL",
        }
        resp = client_admin.post("/api/vendas", json=payload)

        assert resp.status_code == 422, (
            f"Esperado 422, recebido {resp.status_code}: {resp.text}"
        )

    def test_criar_venda_cnpj_inexistente_retorna_404(self, client_admin):
        """
        CNPJ que nao existe na tabela clientes deve retornar 404.
        """
        payload = {
            "cnpj": "99999999999999",
            "data_pedido": "2026-03-15",
            "valor_pedido": 500.00,
            "fonte": "MANUAL",
        }
        resp = client_admin.post("/api/vendas", json=payload)

        assert resp.status_code == 404, resp.text
        assert "nao encontrado" in resp.json()["detail"].lower()

    def test_criar_venda_consultor_herdado_do_usuario(self, client_manu):
        """
        Se payload nao informa consultor, deve usar consultor_nome do usuario logado (MANU).
        """
        payload = {
            "cnpj": "12345678000100",
            "data_pedido": "2026-03-10",
            "valor_pedido": 800.00,
            "fonte": "MANUAL",
        }
        resp = client_manu.post("/api/vendas", json=payload)

        assert resp.status_code == 201, resp.text
        assert resp.json()["consultor"] == "MANU"

    def test_criar_venda_fonte_invalida_rejeitada(self, client_admin):
        """
        Fonte nao mapeada deve ser rejeitada com 422.
        """
        payload = {
            "cnpj": "12345678000100",
            "data_pedido": "2026-03-15",
            "valor_pedido": 300.00,
            "fonte": "DESKRIO",
        }
        resp = client_admin.post("/api/vendas", json=payload)

        assert resp.status_code == 422, resp.text

    def test_mes_referencia_derivado_corretamente(self, client_admin):
        """
        mes_referencia deve ser 'AAAA-MM' derivado automaticamente de data_pedido.
        """
        payload = {
            "cnpj": "12345678000100",
            "data_pedido": "2026-01-28",
            "valor_pedido": 200.00,
            "fonte": "SAP",
        }
        resp = client_admin.post("/api/vendas", json=payload)

        assert resp.status_code == 201, resp.text
        assert resp.json()["mes_referencia"] == "2026-01"


# ---------------------------------------------------------------------------
# Testes: GET /api/vendas/totais — faturamento agregado
# ---------------------------------------------------------------------------

class TestTotaisFaturamento:
    """Testa o endpoint GET /api/vendas/totais."""

    def _criar_venda_db(
        self,
        session: Session,
        valor: float,
        consultor: str,
        mes: str,
        tier: str = "REAL",
    ) -> Venda:
        """Helper para criar venda diretamente no banco (bypassa HTTP)."""
        ano, m = mes.split("-")
        venda = Venda(
            cnpj="12345678000100",
            data_pedido=datetime.date(int(ano), int(m), 15),
            valor_pedido=valor,
            consultor=consultor,
            fonte="MANUAL",
            classificacao_3tier=tier,
            mes_referencia=mes,
        )
        session.add(venda)
        session.commit()
        return venda

    def test_totais_calcula_corretamente(self, db_session, client_admin):
        """
        Cria 3 vendas e verifica que totais retornam soma, contagem e ticket medio corretos.
        """
        self._criar_venda_db(db_session, 1000.00, "MANU", "2026-03")
        self._criar_venda_db(db_session, 2000.00, "LARISSA", "2026-03")
        self._criar_venda_db(db_session, 500.00, "MANU", "2026-02")

        resp = client_admin.get("/api/vendas/totais")

        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["faturamento_total"] == 3500.00
        assert data["total_vendas"] == 3
        assert data["ticket_medio"] == round(3500.00 / 3, 2)

    def test_totais_por_consultor(self, db_session, client_admin):
        """Breakdown por consultor deve somar corretamente."""
        self._criar_venda_db(db_session, 1000.00, "MANU", "2026-03")
        self._criar_venda_db(db_session, 2000.00, "MANU", "2026-03")
        self._criar_venda_db(db_session, 500.00, "LARISSA", "2026-03")

        resp = client_admin.get("/api/vendas/totais")
        data = resp.json()

        por_consultor = {item["consultor"]: item for item in data["por_consultor"]}
        assert por_consultor["MANU"]["faturamento"] == 3000.00
        assert por_consultor["MANU"]["qtd"] == 2
        assert por_consultor["LARISSA"]["faturamento"] == 500.00
        assert por_consultor["LARISSA"]["qtd"] == 1

    def test_totais_por_mes(self, db_session, client_admin):
        """Breakdown por mes deve agrupar por mes_referencia."""
        self._criar_venda_db(db_session, 1000.00, "MANU", "2026-03")
        self._criar_venda_db(db_session, 500.00, "MANU", "2026-02")

        resp = client_admin.get("/api/vendas/totais")
        data = resp.json()

        por_mes = {item["mes"]: item for item in data["por_mes"]}
        assert por_mes["2026-03"]["faturamento"] == 1000.00
        assert por_mes["2026-02"]["faturamento"] == 500.00

    def test_totais_sem_vendas_retorna_zeros(self, client_admin):
        """Com banco sem vendas, todos os totais devem ser zero."""
        resp = client_admin.get("/api/vendas/totais")

        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["faturamento_total"] == 0.0
        assert data["total_vendas"] == 0
        assert data["ticket_medio"] == 0.0
        assert data["por_consultor"] == []
        assert data["por_mes"] == []

    def test_totais_exclui_alucinacao(self, db_session, client_admin):
        """
        R8: registros com classificacao_3tier = ALUCINACAO nao devem entrar no calculo.
        Apenas REAL e SINTETICO sao somados.
        """
        # Venda legitima
        self._criar_venda_db(db_session, 1000.00, "MANU", "2026-03", tier="REAL")
        # Venda fabricada — NUNCA deve entrar no faturamento (R8)
        self._criar_venda_db(db_session, 99999.00, "MANU", "2026-03", tier="ALUCINACAO")

        resp = client_admin.get("/api/vendas/totais")
        data = resp.json()

        # Apenas a venda REAL deve entrar
        assert data["faturamento_total"] == 1000.00
        assert data["total_vendas"] == 1


# ---------------------------------------------------------------------------
# Testes: Two-Base Architecture — verificacao estrutural
# ---------------------------------------------------------------------------

class TestTwoBaseVenda:
    """
    R4 — Two-Base Architecture.

    Verifica que o model Venda nao possui campos de interacao (log).
    Venda e apenas financeiro; log e apenas operacional.
    Mistura causa inflacao de 742% (ja aconteceu).
    """

    def test_venda_nao_tem_campos_de_interacao(self):
        """
        Model Venda nao pode ter campos de log/interacao como resultado,
        estagio_funil, fase, tipo_contato, acao_futura, temperatura.
        """
        colunas = {c.name for c in Venda.__table__.columns}
        campos_proibidos = [
            "resultado",
            "estagio_funil",
            "fase",
            "tipo_contato",
            "acao_futura",
            "temperatura",
            "follow_up_dias",
            "grupo_dash",
            "tentativa",
            "descricao",
        ]
        violacoes = [campo for campo in campos_proibidos if campo in colunas]
        assert not violacoes, (
            f"Two-Base VIOLADA: Venda tem campo(s) de interacao/log: {violacoes}. "
            "Tabela vendas deve conter APENAS dados financeiros."
        )

    def test_venda_tem_campos_financeiros_esperados(self):
        """Model Venda deve ter os campos financeiros canonicos."""
        colunas = {c.name for c in Venda.__table__.columns}
        campos_esperados = [
            "id",
            "cnpj",
            "data_pedido",
            "numero_pedido",
            "valor_pedido",
            "consultor",
            "fonte",
            "classificacao_3tier",
            "mes_referencia",
            "created_at",
        ]
        ausentes = [campo for campo in campos_esperados if campo not in colunas]
        assert not ausentes, (
            f"Model Venda esta faltando campos esperados: {ausentes}"
        )

    def test_check_constraint_valor_positivo_existe(self):
        """
        CheckConstraint 'ck_venda_valor_positivo' deve estar presente na tabela.
        Esta constraint e a ultima linha de defesa do Two-Base no banco.
        """
        constraints = {c.name for c in Venda.__table__.constraints}
        assert "ck_venda_valor_positivo" in constraints, (
            "CheckConstraint 'ck_venda_valor_positivo' nao encontrada no model Venda. "
            "Sem esta constraint, o banco nao enforça Two-Base."
        )


# ---------------------------------------------------------------------------
# Testes: isolamento por consultor (GET /api/vendas)
# ---------------------------------------------------------------------------

class TestIsolamentoPorConsultor:
    """Testa que consultores veem apenas seus proprios registros."""

    def _criar_venda_db(
        self,
        session: Session,
        consultor: str,
        valor: float,
    ) -> Venda:
        venda = Venda(
            cnpj="12345678000100",
            data_pedido=datetime.date(2026, 3, 1),
            valor_pedido=valor,
            consultor=consultor,
            fonte="MANUAL",
            classificacao_3tier="REAL",
            mes_referencia="2026-03",
        )
        session.add(venda)
        session.commit()
        return venda

    def test_consultor_ve_apenas_proprios_registros(self, db_session, client_manu):
        """
        Consultor MANU so deve ver suas vendas.
        Vendas de LARISSA nao devem aparecer.
        """
        self._criar_venda_db(db_session, "MANU", 1000.00)
        self._criar_venda_db(db_session, "LARISSA", 2000.00)

        resp = client_manu.get("/api/vendas")

        assert resp.status_code == 200, resp.text
        vendas = resp.json()

        assert len(vendas) == 1
        assert all(v["consultor"] == "MANU" for v in vendas)

    def test_admin_ve_todos_os_registros(self, db_session, client_admin):
        """Admin deve ver vendas de todos os consultores sem restricao."""
        self._criar_venda_db(db_session, "MANU", 1000.00)
        self._criar_venda_db(db_session, "LARISSA", 2000.00)
        self._criar_venda_db(db_session, "DAIANE", 500.00)

        resp = client_admin.get("/api/vendas")

        assert resp.status_code == 200, resp.text
        vendas = resp.json()

        assert len(vendas) == 3

    def test_consultor_nao_acessa_venda_de_outro(self, db_session, client_larissa):
        """
        Consultor LARISSA tentando acessar venda de MANU deve receber 403.
        """
        venda_manu = self._criar_venda_db(db_session, "MANU", 1000.00)

        resp = client_larissa.get(f"/api/vendas/{venda_manu.id}")

        assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Testes: schema Pydantic VendaCreate — validacoes isoladas
# ---------------------------------------------------------------------------

class TestVendaCreateSchema:
    """Testa validacoes do schema VendaCreate sem dependencia de HTTP."""

    def test_cnpj_com_pontuacao_rejeitado(self):
        """
        CNPJ com pontuacao deve ser rejeitado pelo schema.

        CNPJ '12.345.678/0001-00' tem 18 chars → rejeitado por max_length=14.
        CNPJ '12345678/00010' tem 14 chars mas contem '/' → rejeitado pelo validator numerico.
        Testamos o segundo caso para cobrir o validator de forma explicita.
        """
        from pydantic import ValidationError
        # Este CNPJ tem exatamente 14 caracteres mas contem barra — chega ao validator
        with pytest.raises(ValidationError, match="numericos"):
            VendaCreate(
                cnpj="12345678/00010",
                data_pedido=datetime.date(2026, 3, 1),
                valor_pedido=100.0,
            )

    def test_valor_pedido_zero_rejeitado(self):
        """valor_pedido = 0 deve levantar ValidationError (R4)."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            VendaCreate(
                cnpj="12345678000100",
                data_pedido=datetime.date(2026, 3, 1),
                valor_pedido=0.0,
            )

    def test_fonte_normalizada_para_uppercase(self):
        """Fonte 'mercos' deve ser normalizada para 'MERCOS'."""
        venda = VendaCreate(
            cnpj="12345678000100",
            data_pedido=datetime.date(2026, 3, 1),
            valor_pedido=100.0,
            fonte="mercos",
        )
        assert venda.fonte == "MERCOS"

    def test_venda_minima_valida(self):
        """Campos obrigatorios minimos (cnpj, data_pedido, valor_pedido) devem ser aceitos."""
        venda = VendaCreate(
            cnpj="12345678000100",
            data_pedido=datetime.date(2026, 3, 1),
            valor_pedido=1.0,
        )
        assert venda.cnpj == "12345678000100"
        assert venda.valor_pedido == 1.0
        assert venda.fonte == "MANUAL"     # default
        assert venda.consultor is None     # opcional
        assert venda.numero_pedido is None  # opcional
