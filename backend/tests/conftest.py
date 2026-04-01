"""
CRM VITAO360 — Shared pytest fixtures for all backend tests.

Provides:
  - in-memory SQLite engine and session factory
  - FastAPI TestClient with get_db overridden
  - Fake admin and consultor user objects (no JWT needed)
  - Auth headers built via real JWT creation for routes that inspect the token
  - Sample Cliente (CNPJ: 12345678000100, ATIVO, MANU)
  - Sample Venda  (valor_pedido > 0, enforced by DB constraint)
  - Sample RegraMotor entries seeded for motor tests
  - Helper _make_admin_client / _make_consultor_client for one-liner test clients

Pattern matches existing tests:
  - scope=function for full isolation
  - dependency_overrides cleared in teardown
  - SimpleNamespace for fake user objects
  - StaticPool to reuse the same in-memory connection
"""

from __future__ import annotations

import os

# Disable rate limiting middleware during tests (avoids false 429s)
os.environ.setdefault("TESTING", "1")

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.deps import get_current_user, require_admin, require_admin_or_gerente
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.regra_motor import RegraMotor
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.security import create_access_token, hash_password


# ---------------------------------------------------------------------------
# In-memory SQLite engine (StaticPool keeps same connection across threads)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine():
    """Isolated SQLite in-memory engine per test function."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Session:
    """
    SQLAlchemy session connected to the in-memory engine.
    Teardown rolls back uncommitted changes and closes the session.
    """
    _Session = sessionmaker(bind=engine)
    session = _Session()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Fake user objects (no DB lookup, no JWT) — for dependency_overrides
# ---------------------------------------------------------------------------

def _make_fake_user(
    id: int = 1,
    email: str = "admin@vitao.com.br",
    nome: str = "Admin Vitao",
    role: str = "admin",
    consultor_nome: str | None = None,
    ativo: bool = True,
) -> SimpleNamespace:
    """Build a SimpleNamespace that satisfies all attribute accesses in routes/deps."""
    return SimpleNamespace(
        id=id,
        email=email,
        nome=nome,
        role=role,
        consultor_nome=consultor_nome,
        ativo=ativo,
        hashed_password="hashed_fake",
    )


@pytest.fixture(scope="function")
def fake_admin() -> SimpleNamespace:
    """Admin user for dependency injection."""
    return _make_fake_user(id=1, email="admin@vitao.com.br", role="admin")


@pytest.fixture(scope="function")
def fake_consultor() -> SimpleNamespace:
    """Consultor user (MANU) for dependency injection."""
    return _make_fake_user(
        id=2, email="manu@vitao.com.br",
        nome="Manu Ditzel", role="consultor",
        consultor_nome="MANU",
    )


# ---------------------------------------------------------------------------
# DB session dependency override helper
# ---------------------------------------------------------------------------

def _db_override(session: Session):
    """Returns a get_db override that always yields the provided session."""
    def _override():
        yield session
    return _override


# ---------------------------------------------------------------------------
# FastAPI TestClient fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db, fake_admin) -> TestClient:
    """
    TestClient with:
      - get_db        -> in-memory SQLite session
      - get_current_user -> fake_admin (role=admin)
      - require_admin    -> fake_admin (bypass role check)
      - require_admin_or_gerente -> fake_admin
    """
    app.dependency_overrides[get_db] = _db_override(db)
    app.dependency_overrides[get_current_user] = lambda: fake_admin
    app.dependency_overrides[require_admin] = lambda: fake_admin
    app.dependency_overrides[require_admin_or_gerente] = lambda: fake_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_consultor(db, fake_consultor) -> TestClient:
    """
    TestClient with:
      - get_db        -> in-memory SQLite session
      - get_current_user -> fake_consultor (role=consultor, MANU)
      No admin overrides — require_admin will return 403.
    """
    app.dependency_overrides[get_db] = _db_override(db)
    app.dependency_overrides[get_current_user] = lambda: fake_consultor
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Real DB user for login tests (auth routes query the DB)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def real_admin_user(db) -> Usuario:
    """
    Persists a real Usuario row in the in-memory DB so login endpoints work.
    Password: vitao2026
    """
    user = Usuario(
        email="admin@vitao.com.br",
        nome="Admin Vitao",
        role="admin",
        consultor_nome=None,
        hashed_password=hash_password("vitao2026"),
        ativo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def client_with_real_db(db) -> TestClient:
    """
    TestClient with get_db overridden to in-memory DB but no user override.
    Used for login/auth endpoint tests that need a real DB lookup.
    """
    app.dependency_overrides[get_db] = _db_override(db)
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth headers helper (real JWT, no DB)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def admin_headers(fake_admin) -> dict:
    """
    Real JWT access token for fake_admin.
    Useful when routes decode the token directly instead of using Depends.
    """
    token = create_access_token(
        {"sub": str(fake_admin.id), "role": fake_admin.role, "consultor": fake_admin.consultor_nome}
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Domain fixture: sample Cliente
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def sample_cliente(db) -> Cliente:
    """
    ATIVO client with valid 14-digit CNPJ (R5), persisted in test DB.
    faturamento_total comes from Venda records only (R4 — Two-Base).
    """
    c = Cliente(
        cnpj="12345678000100",       # 14 digits, zero-padded (R5)
        nome_fantasia="Natura Store Ltda",
        razao_social="Natura Store LTDA",
        uf="SP",
        cidade="São Paulo",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        curva_abc="A",
        tipo_cliente="MADURO",
        temperatura="QUENTE",
        sinaleiro="VERDE",
        score=78.5,
        prioridade="P4",
        faturamento_total=12000.0,
        dias_sem_compra=20,
        ciclo_medio=30.0,
        n_compras=15,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ---------------------------------------------------------------------------
# Domain fixture: sample Venda (Two-Base — valor > 0)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def sample_venda(db, sample_cliente) -> Venda:
    """
    Venda with valor_pedido > 0 (R4 enforced by DB CheckConstraint).
    Linked to sample_cliente via CNPJ FK.
    """
    v = Venda(
        cnpj=sample_cliente.cnpj,
        data_pedido=date(2026, 3, 1),
        numero_pedido="PED-001",
        valor_pedido=1500.00,         # R4: MUST be > 0
        consultor="MANU",
        fonte="MERCOS",
        classificacao_3tier="REAL",
        mes_referencia="2026-03",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


# ---------------------------------------------------------------------------
# Domain fixture: seeded RegraMotor entries
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def regras_seed(db) -> list[RegraMotor]:
    """
    Minimal set of motor rules covering ATIVO and PROSPECT situations.
    9 output dimensions per rule (estagio_funil, fase, tipo_contato,
    acao_futura, temperatura, follow_up_dias, grupo_dash, tipo_acao, chave).
    """
    regras = [
        RegraMotor(
            situacao="ATIVO",
            resultado="VENDA / PEDIDO",
            estagio_funil="POS-VENDA",
            fase="POS-VENDA",
            tipo_contato="POS-VENDA / RELACIONAMENTO",
            acao_futura="Acompanhar recompra",
            temperatura="QUENTE",
            follow_up_dias=45,
            grupo_dash="FUNIL",
            tipo_acao="VENDA",
            chave="ATIVO|VENDA / PEDIDO",
        ),
        RegraMotor(
            situacao="ATIVO",
            resultado="ORCAMENTO",
            estagio_funil="EM ATENDIMENTO",
            fase="NEGOCIACAO",
            tipo_contato="LIGACAO",
            acao_futura="Fechar orcamento",
            temperatura="MORNO",
            follow_up_dias=2,
            grupo_dash="FUNIL",
            tipo_acao="VENDA",
            chave="ATIVO|ORCAMENTO",
        ),
        RegraMotor(
            situacao="PROSPECT",
            resultado="PRIMEIRO CONTATO",
            estagio_funil="PROSPECCAO",
            fase="AQUISICAO",
            tipo_contato="LIGACAO",
            acao_futura="Enviar proposta",
            temperatura="FRIO",
            follow_up_dias=3,
            grupo_dash="FUNIL",
            tipo_acao="ATENDIMENTO",
            chave="PROSPECT|PRIMEIRO CONTATO",
        ),
    ]
    db.add_all(regras)
    db.commit()
    return regras
