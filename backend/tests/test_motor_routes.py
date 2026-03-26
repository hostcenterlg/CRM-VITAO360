"""
CRM VITAO360 — Testes das rotas GET /api/motor/regras

Valida:
  1. GET /api/motor/regras retorna 200 com total e lista de regras
  2. GET /api/motor/regras?situacao=ATIVO filtra corretamente por situacao
  3. GET /api/motor/regras?situacao=INEXISTENTE retorna lista vazia (total=0)
  4. GET /api/motor/regras/{id} retorna a regra correta pelo ID
  5. GET /api/motor/regras/{id} com ID inexistente retorna 404
  6. Todos os campos obrigatorios estao presentes na resposta (id, situacao, resultado,
     estagio_funil, fase, tipo_contato, acao_futura, temperatura, followup_dias, chave)
  7. Sem autenticacao admin retorna 403

Fixtures:
  - engine SQLite em memoria com 3 regras seed (situacao variada)
  - get_db sobrescrito via dependency_overrides
  - usuario admin injetado sem JWT (require_admin override)
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.regra_motor import RegraMotor


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
    Session com seed de 3 regras do motor:
      - 2 com situacao ATIVO (chaves ATIVO|Venda Realizada, ATIVO|Sem Contato)
      - 1 com situacao PROSPECT (chave PROSPECT|Primeiro Contato)
    """
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()

    regras = [
        RegraMotor(
            situacao="ATIVO",
            resultado="Venda Realizada",
            estagio_funil="POS-VENDA",
            fase="MANUTENCAO",
            tipo_contato="Visita",
            acao_futura="Acompanhar pedido",
            temperatura="QUENTE",
            follow_up_dias=30,
            grupo_dash="ATIVO_POSITIVO",
            tipo_acao="RETENCAO",
            chave="ATIVO|Venda Realizada",
        ),
        RegraMotor(
            situacao="ATIVO",
            resultado="Sem Contato",
            estagio_funil="MANUTENCAO",
            fase="REATIVACAO",
            tipo_contato="Ligacao",
            acao_futura="Ligar novamente",
            temperatura="MORNO",
            follow_up_dias=7,
            grupo_dash="ATIVO_ALERTA",
            tipo_acao="FOLLOWUP",
            chave="ATIVO|Sem Contato",
        ),
        RegraMotor(
            situacao="PROSPECT",
            resultado="Primeiro Contato",
            estagio_funil="PROSPECCAO",
            fase="AQUISICAO",
            tipo_contato="Email",
            acao_futura="Enviar proposta",
            temperatura="FRIO",
            follow_up_dias=3,
            grupo_dash="PROSPECT_NOVO",
            tipo_acao="AQUISICAO",
            chave="PROSPECT|Primeiro Contato",
        ),
    ]

    for r in regras:
        session.add(r)
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

def _fake_usuario(id: int, email: str, nome: str, role: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=id, email=email, nome=nome,
        hashed_password="hash_fake", role=role,
        consultor_nome=None, ativo=True,
    )


@pytest.fixture(scope="function")
def usuario_admin():
    return _fake_usuario(1, "admin@vitao.com", "Admin VITAO", "admin")


@pytest.fixture(scope="function")
def usuario_consultor():
    return _fake_usuario(2, "manu@vitao.com", "Manu Ditzel", "consultor")


# ---------------------------------------------------------------------------
# Fixtures de TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db_session, usuario_admin):
    """TestClient com admin e banco em memoria injetados."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_admin] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_sem_admin(db_session, usuario_consultor):
    """TestClient com consultor — require_admin NAO sobrescrito para testar 403."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_consultor
    # require_admin: injetamos o consultor para forcar o check de role
    app.dependency_overrides[require_admin] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=403, detail="Acesso restrito a administradores")
    )
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestListarRegras:
    """GET /api/motor/regras"""

    def test_retorna_200_com_todas_regras(self, client_admin):
        resp = client_admin.get("/api/motor/regras")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["regras"]) == 3

    def test_campos_obrigatorios_presentes(self, client_admin):
        resp = client_admin.get("/api/motor/regras")
        assert resp.status_code == 200
        regra = resp.json()["regras"][0]
        campos = ["id", "situacao", "resultado", "estagio_funil", "fase",
                  "tipo_contato", "acao_futura", "temperatura", "followup_dias", "chave"]
        for campo in campos:
            assert campo in regra, f"Campo '{campo}' ausente na resposta"

    def test_filtro_situacao_ativo(self, client_admin):
        resp = client_admin.get("/api/motor/regras", params={"situacao": "ATIVO"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for regra in data["regras"]:
            assert regra["situacao"] == "ATIVO"

    def test_filtro_situacao_prospect(self, client_admin):
        resp = client_admin.get("/api/motor/regras", params={"situacao": "PROSPECT"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["regras"][0]["situacao"] == "PROSPECT"

    def test_filtro_situacao_inexistente_retorna_vazio(self, client_admin):
        resp = client_admin.get("/api/motor/regras", params={"situacao": "INEXISTENTE"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["regras"] == []

    def test_filtro_situacao_case_insensitive(self, client_admin):
        resp = client_admin.get("/api/motor/regras", params={"situacao": "ativo"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_sem_admin_retorna_403(self, client_sem_admin):
        resp = client_sem_admin.get("/api/motor/regras")
        assert resp.status_code == 403


class TestDetalheRegra:
    """GET /api/motor/regras/{id}"""

    def test_retorna_regra_pelo_id(self, client_admin, db_session):
        # Pegar o ID da primeira regra do seed
        from backend.app.models.regra_motor import RegraMotor
        from sqlalchemy import select
        regra = db_session.scalar(select(RegraMotor).where(RegraMotor.chave == "ATIVO|Venda Realizada"))
        assert regra is not None

        resp = client_admin.get(f"/api/motor/regras/{regra.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == regra.id
        assert data["situacao"] == "ATIVO"
        assert data["resultado"] == "Venda Realizada"
        assert data["chave"] == "ATIVO|Venda Realizada"
        assert data["temperatura"] == "QUENTE"
        assert data["followup_dias"] == 30

    def test_id_inexistente_retorna_404(self, client_admin):
        resp = client_admin.get("/api/motor/regras/99999")
        assert resp.status_code == 404
        assert "nao encontrada" in resp.json()["detail"]

    def test_sem_admin_retorna_403(self, client_sem_admin):
        resp = client_sem_admin.get("/api/motor/regras/1")
        assert resp.status_code == 403
