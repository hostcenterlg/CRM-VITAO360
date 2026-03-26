"""
CRM VITAO360 — Testes das rotas /api/rnc

Valida:
  1. POST /api/rnc cria RNC com status ABERTO e responsavel derivado do tipo_problema
  2. POST /api/rnc seta cliente.problema_aberto = True (P0)
  3. POST /api/rnc com CNPJ inexistente retorna 404
  4. POST /api/rnc com tipo_problema invalido retorna 422
  5. POST /api/rnc com CNPJ nao-numerico retorna 422
  6. GET /api/rnc retorna lista com total e resumo percentual
  7. GET /api/rnc?status=ABERTO filtra por status
  8. GET /api/rnc?consultor=MANU filtra por consultor
  9. GET /api/rnc — consultor ve apenas suas RNCs (isolamento por role)
  10. GET /api/rnc/{id} retorna detalhe correto
  11. GET /api/rnc/{id} inexistente retorna 404
  12. GET /api/rnc/{id} — consultor nao pode ver RNC de outro consultor (403)
  13. PATCH /api/rnc/{id} atualiza status para EM_ANDAMENTO
  14. PATCH /api/rnc/{id} com status RESOLVIDO seta data_resolucao = hoje
  15. PATCH /api/rnc/{id} com status RESOLVIDO seta cliente.problema_aberto = False
       (quando nao ha outras RNCs abertas)
  16. PATCH /api/rnc/{id} com status RESOLVIDO NAO seta problema_aberto = False
       quando ha outras RNCs abertas para o mesmo CNPJ
  17. R4 — Two-Base: RNCResponse nao tem campo valor_pedido
  18. R5 — CNPJ normalizado para 14 digitos na criacao

Padrao de autenticacao:
  dependency_overrides para get_current_user, require_consultor_or_admin.
  Banco SQLite em memoria (isolamento por funcao).
"""

from __future__ import annotations

import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import get_current_user, require_consultor_or_admin
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.rnc import RNC


# ---------------------------------------------------------------------------
# Fixtures de banco
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine_mem():
    """Engine SQLite em memoria — isolamento completo entre testes."""
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
      - 1 cliente ATIVO (CNPJ 98765432000100, consultor LARISSA)
    """
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    clientes = [
        Cliente(
            cnpj="12345678000100",
            nome_fantasia="Distribuidora Teste Ltda",
            situacao="ATIVO",
            consultor="MANU",
            classificacao_3tier="REAL",
            problema_aberto=False,
        ),
        Cliente(
            cnpj="98765432000100",
            nome_fantasia="Mercado Larissa Ltda",
            situacao="ATIVO",
            consultor="LARISSA",
            classificacao_3tier="REAL",
            problema_aberto=False,
        ),
    ]
    for c in clientes:
        session.add(c)
    session.commit()

    yield session
    session.close()


def _make_get_db_override(session: Session):
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
    return SimpleNamespace(
        id=id, email=email, nome=nome,
        hashed_password="hash_fake", role=role,
        consultor_nome=consultor_nome, ativo=True,
    )


@pytest.fixture(scope="function")
def usuario_admin():
    return _fake_usuario(1, "admin@vitao.com", "Admin VITAO", "admin")


@pytest.fixture(scope="function")
def usuario_manu():
    return _fake_usuario(2, "manu@vitao.com", "Manu Ditzel", "consultor", "MANU")


@pytest.fixture(scope="function")
def usuario_larissa():
    return _fake_usuario(3, "larissa@vitao.com", "Larissa Padilha", "consultor", "LARISSA")


# ---------------------------------------------------------------------------
# Fixtures de TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db_session, usuario_admin):
    """TestClient com usuario admin."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_consultor_or_admin] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_manu(db_session, usuario_manu):
    """TestClient com consultor MANU."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_manu
    app.dependency_overrides[require_consultor_or_admin] = lambda: usuario_manu
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_larissa(db_session, usuario_larissa):
    """TestClient com consultor LARISSA."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_larissa
    app.dependency_overrides[require_consultor_or_admin] = lambda: usuario_larissa
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers de payload
# ---------------------------------------------------------------------------

PAYLOAD_VALIDO = {
    "cnpj": "12345678000100",
    "tipo_problema": "ATRASO ENTREGA (TRANSPORTADORA)",
    "descricao": "Pedido 999 nao chegou no prazo de 5 dias uteis.",
    "consultor": "MANU",
}


# ---------------------------------------------------------------------------
# Testes POST /api/rnc
# ---------------------------------------------------------------------------

class TestCriarRNC:
    """POST /api/rnc"""

    def test_cria_rnc_com_status_aberto(self, client_admin):
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ABERTO"
        assert data["cnpj"] == "12345678000100"
        assert data["tipo_problema"] == "ATRASO ENTREGA (TRANSPORTADORA)"
        assert data["consultor"] == "MANU"

    def test_responsavel_derivado_do_tipo_problema(self, client_admin):
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201
        assert resp.json()["responsavel"] == "TRANSPORTADORA"

    def test_responsavel_faturamento_para_erro_nf(self, client_admin):
        payload = {**PAYLOAD_VALIDO, "tipo_problema": "ERRO NOTA FISCAL (FATURAMENTO)"}
        resp = client_admin.post("/api/rnc", json=payload)
        assert resp.status_code == 201
        assert resp.json()["responsavel"] == "FATURAMENTO"

    def test_responsavel_ti_para_problema_sistema(self, client_admin):
        payload = {**PAYLOAD_VALIDO, "tipo_problema": "PROBLEMA SISTEMA (TI)"}
        resp = client_admin.post("/api/rnc", json=payload)
        assert resp.status_code == 201
        assert resp.json()["responsavel"] == "TI"

    def test_p0_seta_problema_aberto_true(self, client_admin, db_session):
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201

        # Verificar que cliente.problema_aberto foi setado para True
        cliente = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "12345678000100")
        )
        assert cliente is not None
        assert cliente.problema_aberto is True

    def test_data_abertura_e_hoje(self, client_admin):
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201
        hoje = datetime.date.today().isoformat()
        assert resp.json()["data_abertura"] == hoje

    def test_cnpj_inexistente_retorna_404(self, client_admin):
        payload = {**PAYLOAD_VALIDO, "cnpj": "00000000000000"}
        resp = client_admin.post("/api/rnc", json=payload)
        assert resp.status_code == 404
        assert "nao encontrado" in resp.json()["detail"]

    def test_tipo_problema_invalido_retorna_422(self, client_admin):
        payload = {**PAYLOAD_VALIDO, "tipo_problema": "CATEGORIA INEXISTENTE"}
        resp = client_admin.post("/api/rnc", json=payload)
        assert resp.status_code == 422

    def test_cnpj_nao_numerico_retorna_422(self, client_admin):
        payload = {**PAYLOAD_VALIDO, "cnpj": "CNPJ_INVALIDO"}
        resp = client_admin.post("/api/rnc", json=payload)
        assert resp.status_code == 422

    def test_r4_two_base_sem_campo_valor(self, client_admin):
        """R4: RNCResponse nao deve ter campo valor_pedido."""
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201
        data = resp.json()
        assert "valor_pedido" not in data
        assert "valor" not in data

    def test_r5_cnpj_normalizado_na_resposta(self, client_admin):
        """R5: CNPJ retornado deve ter 14 digitos numericos."""
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201
        cnpj = resp.json()["cnpj"]
        assert len(cnpj) == 14
        assert cnpj.isdigit()

    def test_nome_fantasia_presente_na_resposta(self, client_admin):
        resp = client_admin.post("/api/rnc", json=PAYLOAD_VALIDO)
        assert resp.status_code == 201
        assert resp.json()["nome_fantasia"] == "Distribuidora Teste Ltda"


# ---------------------------------------------------------------------------
# Testes GET /api/rnc
# ---------------------------------------------------------------------------

class TestListarRNCs:
    """GET /api/rnc"""

    def _criar_rnc(self, client, cnpj="12345678000100", consultor="MANU",
                   tipo="ATRASO ENTREGA (TRANSPORTADORA)"):
        payload = {
            "cnpj": cnpj,
            "tipo_problema": tipo,
            "descricao": "Descricao do problema de teste.",
            "consultor": consultor,
        }
        return client.post("/api/rnc", json=payload)

    def test_lista_vazia_retorna_200(self, client_admin):
        resp = client_admin.get("/api/rnc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert "resumo" in data

    def test_resumo_com_lista_vazia(self, client_admin):
        resp = client_admin.get("/api/rnc")
        resumo = resp.json()["resumo"]
        assert resumo["resolvido_pct"] == 0.0
        assert resumo["em_andamento_pct"] == 0.0
        assert resumo["pendente_pct"] == 0.0

    def test_lista_com_rncs_criadas(self, client_admin):
        self._criar_rnc(client_admin)
        self._criar_rnc(client_admin)
        resp = client_admin.get("/api/rnc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_filtro_por_status(self, client_admin):
        self._criar_rnc(client_admin)
        resp = client_admin.get("/api/rnc", params={"status": "ABERTO"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "ABERTO"

    def test_filtro_por_consultor(self, client_admin):
        self._criar_rnc(client_admin, cnpj="12345678000100", consultor="MANU")
        self._criar_rnc(client_admin, cnpj="98765432000100", consultor="LARISSA")

        resp = client_admin.get("/api/rnc", params={"consultor": "MANU"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["consultor"] == "MANU"

    def test_consultor_ve_apenas_suas_rncs(self, client_admin, client_manu, db_session):
        """Consultor com role='consultor' ve apenas as proprias RNCs."""
        # Admin cria uma RNC de MANU e uma de LARISSA
        self._criar_rnc(client_admin, cnpj="12345678000100", consultor="MANU")
        self._criar_rnc(client_admin, cnpj="98765432000100", consultor="LARISSA")

        # MANU ve apenas suas RNCs
        resp = client_manu.get("/api/rnc")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["consultor"] == "MANU"

    def test_resumo_percentual_correto(self, client_admin, db_session):
        """Resumo deve calcular percentuais baseado no subconjunto filtrado."""
        self._criar_rnc(client_admin)  # 1 ABERTO

        # Setar uma RNC manualmente como RESOLVIDO no banco
        rnc = db_session.scalar(select(RNC))
        # Criar uma segunda RNC manualmente e setar como RESOLVIDO
        from backend.app.models.rnc import RNC as RNCModel
        rnc2 = RNCModel(
            cnpj="12345678000100",
            tipo_problema="PROBLEMA SISTEMA (TI)",
            descricao="Problema resolvido.",
            consultor="MANU",
            status="RESOLVIDO",
            data_abertura=datetime.date.today(),
            responsavel="TI",
        )
        db_session.add(rnc2)
        db_session.commit()

        resp = client_admin.get("/api/rnc")
        assert resp.status_code == 200
        resumo = resp.json()["resumo"]
        # 1 ABERTO (50%), 1 RESOLVIDO (50%)
        assert resumo["pendente_pct"] == 50.0
        assert resumo["resolvido_pct"] == 50.0
        assert resumo["em_andamento_pct"] == 0.0


# ---------------------------------------------------------------------------
# Testes GET /api/rnc/{id}
# ---------------------------------------------------------------------------

class TestDetalheRNC:
    """GET /api/rnc/{id}"""

    def _criar_rnc(self, client, cnpj="12345678000100", consultor="MANU"):
        payload = {
            "cnpj": cnpj,
            "tipo_problema": "ATRASO ENTREGA (TRANSPORTADORA)",
            "descricao": "Descricao do problema.",
            "consultor": consultor,
        }
        resp = client.post("/api/rnc", json=payload)
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_retorna_detalhe_correto(self, client_admin):
        rnc_id = self._criar_rnc(client_admin)
        resp = client_admin.get(f"/api/rnc/{rnc_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == rnc_id
        assert data["tipo_problema"] == "ATRASO ENTREGA (TRANSPORTADORA)"
        assert data["consultor"] == "MANU"
        assert data["status"] == "ABERTO"

    def test_id_inexistente_retorna_404(self, client_admin):
        resp = client_admin.get("/api/rnc/99999")
        assert resp.status_code == 404

    def test_consultor_nao_ve_rnc_de_outro(self, client_admin, client_manu):
        """Consultor MANU nao pode ver RNC de LARISSA (403)."""
        rnc_id = self._criar_rnc(client_admin, cnpj="98765432000100", consultor="LARISSA")

        resp = client_manu.get(f"/api/rnc/{rnc_id}")
        assert resp.status_code == 403

    def test_consultor_ve_propria_rnc(self, client_admin, client_manu):
        """Consultor MANU pode ver suas proprias RNCs."""
        rnc_id = self._criar_rnc(client_admin, cnpj="12345678000100", consultor="MANU")

        resp = client_manu.get(f"/api/rnc/{rnc_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == rnc_id


# ---------------------------------------------------------------------------
# Testes PATCH /api/rnc/{id}
# ---------------------------------------------------------------------------

class TestAtualizarRNC:
    """PATCH /api/rnc/{id}"""

    def _criar_rnc(self, client, cnpj="12345678000100", consultor="MANU"):
        payload = {
            "cnpj": cnpj,
            "tipo_problema": "ATRASO ENTREGA (TRANSPORTADORA)",
            "descricao": "Descricao do problema.",
            "consultor": consultor,
        }
        resp = client.post("/api/rnc", json=payload)
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_atualiza_status_para_em_andamento(self, client_admin):
        rnc_id = self._criar_rnc(client_admin)
        resp = client_admin.patch(f"/api/rnc/{rnc_id}", json={"status": "EM_ANDAMENTO"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "EM_ANDAMENTO"

    def test_atualiza_resolucao(self, client_admin):
        rnc_id = self._criar_rnc(client_admin)
        resp = client_admin.patch(
            f"/api/rnc/{rnc_id}",
            json={"status": "RESOLVIDO", "resolucao": "Transportadora confirmou extravio."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "RESOLVIDO"
        assert data["resolucao"] == "Transportadora confirmou extravio."

    def test_resolvido_seta_data_resolucao(self, client_admin):
        rnc_id = self._criar_rnc(client_admin)
        resp = client_admin.patch(f"/api/rnc/{rnc_id}", json={"status": "RESOLVIDO"})
        assert resp.status_code == 200
        hoje = datetime.date.today().isoformat()
        assert resp.json()["data_resolucao"] == hoje

    def test_p0_resolvido_seta_problema_aberto_false(self, client_admin, db_session):
        """P0: ao resolver unica RNC de um cliente, problema_aberto deve ser False."""
        rnc_id = self._criar_rnc(client_admin)

        # Verificar que problema_aberto e True apos criacao
        cliente = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "12345678000100")
        )
        db_session.refresh(cliente)
        assert cliente.problema_aberto is True

        # Resolver a RNC
        resp = client_admin.patch(f"/api/rnc/{rnc_id}", json={"status": "RESOLVIDO"})
        assert resp.status_code == 200

        # Verificar que problema_aberto voltou para False
        db_session.refresh(cliente)
        assert cliente.problema_aberto is False

    def test_p0_resolvido_com_outra_aberta_mantem_problema_aberto_true(
        self, client_admin, db_session
    ):
        """Se ha outra RNC aberta, problema_aberto permanece True ao resolver uma."""
        rnc_id_1 = self._criar_rnc(client_admin)

        # Criar segunda RNC para o mesmo cliente (direto no banco para evitar interferencia)
        rnc2 = RNC(
            cnpj="12345678000100",
            tipo_problema="PROBLEMA SISTEMA (TI)",
            descricao="Segundo problema aberto.",
            consultor="MANU",
            status="ABERTO",
            data_abertura=datetime.date.today(),
            responsavel="TI",
        )
        db_session.add(rnc2)
        db_session.commit()

        # Resolver apenas a primeira RNC
        resp = client_admin.patch(f"/api/rnc/{rnc_id_1}", json={"status": "RESOLVIDO"})
        assert resp.status_code == 200

        # problema_aberto deve permanecer True (segunda RNC ainda aberta)
        cliente = db_session.scalar(
            select(Cliente).where(Cliente.cnpj == "12345678000100")
        )
        db_session.refresh(cliente)
        assert cliente.problema_aberto is True

    def test_encerrado_seta_data_resolucao(self, client_admin):
        rnc_id = self._criar_rnc(client_admin)
        resp = client_admin.patch(f"/api/rnc/{rnc_id}", json={"status": "ENCERRADO"})
        assert resp.status_code == 200
        hoje = datetime.date.today().isoformat()
        assert resp.json()["data_resolucao"] == hoje

    def test_status_invalido_retorna_422(self, client_admin):
        rnc_id = self._criar_rnc(client_admin)
        resp = client_admin.patch(f"/api/rnc/{rnc_id}", json={"status": "STATUS_INVALIDO"})
        assert resp.status_code == 422

    def test_id_inexistente_retorna_404(self, client_admin):
        resp = client_admin.patch("/api/rnc/99999", json={"status": "EM_ANDAMENTO"})
        assert resp.status_code == 404

    def test_consultor_nao_edita_rnc_de_outro(self, client_admin, client_manu):
        """MANU nao pode editar RNC criada por LARISSA."""
        rnc_id = self._criar_rnc(client_admin, cnpj="98765432000100", consultor="LARISSA")

        resp = client_manu.patch(f"/api/rnc/{rnc_id}", json={"status": "EM_ANDAMENTO"})
        assert resp.status_code == 403
