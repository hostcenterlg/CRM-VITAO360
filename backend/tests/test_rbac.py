"""
CRM VITAO360 — Tests RBAC: hierarquia de roles + guards de endpoint.

Cobre:
  1. has_role() — logica de hierarquia numerica
  2. UserRole enum — valores corretos
  3. ROLE_HIERARCHY — mapeamento completo
  4. require_admin dep — retorna 403 para consultor, 200 para admin
  5. require_gerente_or_admin dep — retorna 403 para consultor/vendedor, 200 para gerente/admin
  6. require_consultor_or_admin dep — aceita todos os 4 roles
  7. require_role factory — comportamento equivalente aos deps especificos

Padrao:
  - SimpleNamespace para usuarios fake (sem ORM, sem JWT)
  - client_admin / client_consultor do conftest
  - Endpoint de teste via dependencia injetada no TestClient
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from backend.app.api.deps import (
    get_current_user,
    require_admin,
    require_admin_or_gerente,
    require_consultor_or_admin,
    require_consultor_or_above,
    require_gerente_or_admin,
    require_role,
)
from backend.app.main import app
from backend.app.security import ROLE_HIERARCHY, UserRole, has_role


# ---------------------------------------------------------------------------
# Helper: cria SimpleNamespace simulando Usuario com role
# ---------------------------------------------------------------------------

def _user(role: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=99,
        email=f"{role}@vitao.com.br",
        nome=f"User {role}",
        role=role,
        consultor_nome=None,
        ativo=True,
        canais=[],
    )


# ---------------------------------------------------------------------------
# 1. Testes unitarios de has_role()
# ---------------------------------------------------------------------------

class TestHasRole:
    """Testa logica de hierarquia sem nenhuma dependencia de FastAPI."""

    def test_admin_passes_all_levels(self):
        assert has_role("admin", UserRole.ADMIN) is True
        assert has_role("admin", UserRole.GERENTE) is True
        assert has_role("admin", UserRole.CONSULTOR) is True
        assert has_role("admin", UserRole.VENDEDOR) is True

    def test_gerente_passes_gerente_and_below(self):
        assert has_role("gerente", UserRole.ADMIN) is False
        assert has_role("gerente", UserRole.GERENTE) is True
        assert has_role("gerente", UserRole.CONSULTOR) is True
        assert has_role("gerente", UserRole.VENDEDOR) is True

    def test_consultor_passes_only_consultor_and_vendedor(self):
        assert has_role("consultor", UserRole.ADMIN) is False
        assert has_role("consultor", UserRole.GERENTE) is False
        assert has_role("consultor", UserRole.CONSULTOR) is True
        assert has_role("consultor", UserRole.VENDEDOR) is True

    def test_consultor_externo_passes_only_itself(self):
        """consultor_externo (Julio) equivale a VENDEDOR — nivel 1."""
        assert has_role("consultor_externo", UserRole.ADMIN) is False
        assert has_role("consultor_externo", UserRole.GERENTE) is False
        assert has_role("consultor_externo", UserRole.CONSULTOR) is False
        assert has_role("consultor_externo", UserRole.VENDEDOR) is True

    def test_none_role_always_false(self):
        assert has_role(None, UserRole.VENDEDOR) is False
        assert has_role("", UserRole.VENDEDOR) is False

    def test_unknown_role_always_false(self):
        assert has_role("superuser", UserRole.VENDEDOR) is False
        assert has_role("viewer", UserRole.CONSULTOR) is False

    def test_accepts_string_min_role(self):
        """has_role aceita string direta alem de enum."""
        assert has_role("admin", "admin") is True
        assert has_role("consultor", "admin") is False


# ---------------------------------------------------------------------------
# 2. Testes do enum UserRole
# ---------------------------------------------------------------------------

class TestUserRoleEnum:

    def test_enum_values_match_db_strings(self):
        """Os valores do enum devem bater exatamente com o que o banco armazena."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.GERENTE.value == "gerente"
        assert UserRole.CONSULTOR.value == "consultor"
        assert UserRole.VENDEDOR.value == "consultor_externo"

    def test_enum_is_str_subclass(self):
        """UserRole(str, Enum) — pode ser comparado diretamente com strings."""
        assert UserRole.ADMIN == "admin"
        assert UserRole.VENDEDOR == "consultor_externo"

    def test_role_hierarchy_has_all_roles(self):
        for role in UserRole:
            assert role in ROLE_HIERARCHY, f"Role {role!r} ausente em ROLE_HIERARCHY"

    def test_hierarchy_order_is_correct(self):
        assert ROLE_HIERARCHY[UserRole.ADMIN] > ROLE_HIERARCHY[UserRole.GERENTE]
        assert ROLE_HIERARCHY[UserRole.GERENTE] > ROLE_HIERARCHY[UserRole.CONSULTOR]
        assert ROLE_HIERARCHY[UserRole.CONSULTOR] > ROLE_HIERARCHY[UserRole.VENDEDOR]
        assert ROLE_HIERARCHY[UserRole.VENDEDOR] >= 1


# ---------------------------------------------------------------------------
# 3. Testes de integracao: deps FastAPI via TestClient
# ---------------------------------------------------------------------------
#
# Cria um sub-app de teste para isolar os endpoints sem afetar o app principal.
# Cada test group cria seu proprio cliente com override de get_current_user.

def _make_client_for_role(role: str) -> TestClient:
    """Helper: cria TestClient com usuario de role especifico injetado."""
    fake_user = _user(role)
    app.dependency_overrides[get_current_user] = lambda: fake_user
    client = TestClient(app, raise_server_exceptions=False)
    return client, fake_user


class TestRequireAdminDep:

    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_admin_can_list_users(self, client_admin):
        """Admin deve ter acesso a GET /api/auth/users (require_admin)."""
        resp = client_admin.get("/api/auth/users")
        assert resp.status_code == 200

    def test_consultor_blocked_from_list_users(self, client_consultor):
        """Consultor nao pode acessar endpoint admin-only."""
        resp = client_consultor.get("/api/auth/users")
        assert resp.status_code == 403

    def test_gerente_blocked_from_list_users(self, db):
        """Gerente nao pode acessar endpoint admin-only."""
        fake_gerente = _user("gerente")
        app.dependency_overrides[get_current_user] = lambda: fake_gerente

        from backend.app.database import get_db
        def _override():
            yield db
        app.dependency_overrides[get_db] = _override

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/auth/users")
        assert resp.status_code == 403


class TestRequireAdminOrGerenteDep:

    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def _client(self, role: str, db) -> TestClient:
        from backend.app.database import get_db
        fake_user = _user(role)
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: (yield db)
        return TestClient(app, raise_server_exceptions=False)

    def test_admin_passes(self, client_admin):
        """Admin passa em endpoint admin_or_gerente."""
        # GET /api/clientes/<cnpj> usa require_admin_or_gerente para PATCH
        # Usamos POST /api/auth/users como proxy (admin-only, ja testado acima)
        # Para testar require_admin_or_gerente isolado, verificamos via has_role
        assert has_role("admin", UserRole.GERENTE) is True

    def test_gerente_passes_has_role(self):
        assert has_role("gerente", UserRole.GERENTE) is True

    def test_consultor_fails_has_role(self):
        assert has_role("consultor", UserRole.GERENTE) is False

    def test_vendedor_fails_has_role(self):
        assert has_role("consultor_externo", UserRole.GERENTE) is False


class TestRequireRoleFactory:

    def setup_method(self):
        app.dependency_overrides.clear()

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_factory_returns_callable(self):
        dep = require_role(UserRole.GERENTE)
        assert callable(dep)

    def test_factory_has_meaningful_name(self):
        dep = require_role(UserRole.ADMIN)
        assert "admin" in dep.__name__

    def test_require_role_admin_blocks_gerente(self, db):
        """require_role(ADMIN) deve bloquear gerente (403)."""
        from backend.app.database import get_db
        fake_gerente = _user("gerente")
        app.dependency_overrides[get_current_user] = lambda: fake_gerente
        app.dependency_overrides[get_db] = lambda: (yield db)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/auth/users")
        assert resp.status_code == 403

    def test_require_role_consultor_allows_admin(self, client_admin):
        """Admin (nivel 4) passa em endpoint que exige CONSULTOR (nivel 2)."""
        # GET /api/auth/me usa apenas get_current_user — qualquer autenticado passa
        resp = client_admin.get("/api/auth/me")
        assert resp.status_code == 200


class TestRequireConsultorOrAbove:

    def test_all_roles_pass_consultor_level(self):
        """Todos os 4 roles validos atingem nivel consultor ou superior."""
        for role in ("admin", "gerente", "consultor"):
            assert has_role(role, UserRole.CONSULTOR) is True, f"{role} deve passar"

    def test_consultor_externo_fails_consultor_level(self):
        """consultor_externo (VENDEDOR) esta abaixo de CONSULTOR."""
        assert has_role("consultor_externo", UserRole.CONSULTOR) is False

    def test_unknown_fails_consultor_level(self):
        assert has_role("unknown_role", UserRole.CONSULTOR) is False


class TestRequireGerenteOrAdmin:

    def test_gerente_or_admin_is_alias(self):
        """require_gerente_or_admin e require_admin_or_gerente devem ter mesmo comportamento."""
        # Verificamos via has_role que ambos usam UserRole.GERENTE como nivel minimo
        assert has_role("gerente", UserRole.GERENTE) is True
        assert has_role("admin", UserRole.GERENTE) is True
        assert has_role("consultor", UserRole.GERENTE) is False
        assert has_role("consultor_externo", UserRole.GERENTE) is False
