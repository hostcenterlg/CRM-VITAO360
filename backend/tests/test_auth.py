"""
CRM VITAO360 — Tests for /api/auth endpoints.

Covers:
  - Login success returns access + refresh tokens
  - Login with wrong password returns 401
  - Login with nonexistent user returns 401
  - Protected endpoint without token returns 401
  - Protected endpoint with valid token returns 200
  - Refresh token issues new access + refresh pair
  - Admin can create new users (POST /api/auth/users -> 201)
  - Consultor cannot create users (403)
  - Create user with duplicate email returns 409

Pattern:
  - Login tests use real Usuario in DB (client_with_real_db + real_admin_user)
  - Route protection tests use TestClient without auth override
  - User creation tests use client_admin (admin override injected)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.models.usuario import Usuario
from backend.app.security import create_access_token, create_refresh_token, hash_password


# ---------------------------------------------------------------------------
# Login tests (real DB, no dependency override on auth)
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_success_returns_token_pair(self, client_with_real_db, real_admin_user):
        """Correct credentials return access_token and refresh_token."""
        resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "admin@vitao.com.br", "senha": "vitao2026"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_login_wrong_password_returns_401(self, client_with_real_db, real_admin_user):
        """Wrong password must return 401 — does not reveal which field failed."""
        resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "admin@vitao.com.br", "senha": "senha_errada"},
        )
        assert resp.status_code == 401
        assert "Email ou senha incorretos" in resp.json()["detail"]

    def test_login_nonexistent_user_returns_401(self, client_with_real_db):
        """Email not in DB returns 401 (no timing leak distinguishing cases)."""
        resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "fantasma@vitao.com.br", "senha": "qualquer"},
        )
        assert resp.status_code == 401

    def test_login_inactive_user_returns_403(self, client_with_real_db, db):
        """Inactive user (ativo=False) must be rejected with 403."""
        user = Usuario(
            email="inativo@vitao.com.br",
            nome="Inativo",
            role="consultor",
            hashed_password=hash_password("vitao2026"),
            ativo=False,
        )
        db.add(user)
        db.commit()

        resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "inativo@vitao.com.br", "senha": "vitao2026"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Protected endpoint access tests
# ---------------------------------------------------------------------------

class TestProtectedEndpoints:

    def test_get_me_without_token_returns_401(self, client_with_real_db):
        """GET /api/auth/me without Authorization header returns 401."""
        resp = client_with_real_db.get("/api/auth/me")
        assert resp.status_code == 401

    def test_get_me_with_valid_token_returns_user_data(self, client_with_real_db, real_admin_user):
        """GET /api/auth/me with valid JWT returns user fields."""
        # First login to get a real token
        login_resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "admin@vitao.com.br", "senha": "vitao2026"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        me_resp = client_with_real_db.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me = me_resp.json()
        assert me["email"] == "admin@vitao.com.br"
        assert me["role"] == "admin"
        assert "hashed_password" not in me

    def test_get_me_with_invalid_token_returns_401(self, client_with_real_db):
        """Malformed JWT returns 401."""
        resp = client_with_real_db.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token.invalido.aqui"},
        )
        assert resp.status_code == 401

    def test_clientes_endpoint_without_token_returns_401(self, client_with_real_db):
        """GET /api/clientes without token returns 401 (any protected endpoint)."""
        resp = client_with_real_db.get("/api/clientes")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Refresh token tests
# ---------------------------------------------------------------------------

class TestRefreshToken:

    def test_refresh_returns_new_token_pair(self, client_with_real_db, real_admin_user):
        """Valid refresh token produces a new access_token + refresh_token."""
        login_resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "admin@vitao.com.br", "senha": "vitao2026"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client_with_real_db.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_returns_400(self, client_with_real_db, real_admin_user):
        """Using an access token in the refresh endpoint must fail (type mismatch)."""
        login_resp = client_with_real_db.post(
            "/api/auth/login",
            json={"email": "admin@vitao.com.br", "senha": "vitao2026"},
        )
        # Use access_token (type=access) where refresh is expected
        access_token = login_resp.json()["access_token"]

        resp = client_with_real_db.post(
            "/api/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 400

    def test_refresh_with_invalid_token_returns_401(self, client_with_real_db):
        """Completely bogus refresh token returns 401."""
        resp = client_with_real_db.post(
            "/api/auth/refresh",
            json={"refresh_token": "nao.e.um.jwt"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------

class TestCreateUser:

    def test_admin_can_create_user(self, client_admin):
        """POST /api/auth/users by admin returns 201 with user data."""
        resp = client_admin.post(
            "/api/auth/users",
            json={
                "email": "novo@vitao.com.br",
                "nome": "Novo Consultor",
                "senha": "senha123",
                "role": "consultor",
                "consultor_nome": "LARISSA",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "novo@vitao.com.br"
        assert data["role"] == "consultor"
        assert "hashed_password" not in data

    def test_admin_create_user_duplicate_email_returns_409(self, client_admin, db):
        """Creating a user with an existing email returns 409 Conflict."""
        # Insert user directly in the test DB
        existing = Usuario(
            email="duplicado@vitao.com.br",
            nome="Duplicado",
            role="consultor",
            hashed_password=hash_password("abc"),
            ativo=True,
        )
        db.add(existing)
        db.commit()

        resp = client_admin.post(
            "/api/auth/users",
            json={
                "email": "duplicado@vitao.com.br",
                "nome": "Outro",
                "senha": "abc",
                "role": "consultor",
            },
        )
        assert resp.status_code == 409

    def test_consultor_cannot_create_user_returns_403(self, client_consultor):
        """Consultor role must be denied user creation (403)."""
        resp = client_consultor.post(
            "/api/auth/users",
            json={
                "email": "tentativa@vitao.com.br",
                "nome": "Tentativa",
                "senha": "abc",
                "role": "consultor",
            },
        )
        assert resp.status_code == 403
