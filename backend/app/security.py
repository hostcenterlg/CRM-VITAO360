"""
CRM VITAO360 — Autenticacao JWT e hashing de senhas.

Responsabilidades:
  - Hash/verificacao de senhas com bcrypt direto
  - Geracao e decodificacao de tokens JWT (access + refresh)
  - OAuth2PasswordBearer para extracao do token do header Authorization

Algoritmo: HS256 (HMAC-SHA256) — suficiente para uso interno.
Chave secreta: configurada via JWT_SECRET_KEY no .env.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.app.config import settings

# ------------------------------------------------------------------
# Esquema OAuth2 — extrai token do header "Authorization: Bearer <token>"
# tokenUrl aponta para o endpoint de login
# ------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """Gera hash bcrypt da senha em texto plano."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica senha em texto plano contra hash bcrypt armazenado."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Cria JWT de acesso (curta duracao).

    Payload inclui:
      sub  — ID do usuario (string)
      role — role do usuario (admin | consultor | viewer)
      exp  — timestamp de expiracao (UTC)
      type — "access" (diferencia de refresh)
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Cria JWT de refresh (longa duracao).

    Payload inclui:
      sub  — ID do usuario (string)
      exp  — timestamp de expiracao (UTC)
      type — "refresh" (diferencia de access)
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica e valida um JWT.

    Raises:
      HTTPException 401 — se o token for invalido, expirado ou mal-formado.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
