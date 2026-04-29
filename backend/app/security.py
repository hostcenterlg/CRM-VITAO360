"""
CRM VITAO360 — Autenticacao JWT e hashing de senhas.

Responsabilidades:
  - Hash/verificacao de senhas com bcrypt direto
  - Geracao e decodificacao de tokens JWT (access + refresh)
  - OAuth2PasswordBearer para extracao do token do header Authorization
  - UserRole enum com hierarquia numerica para RBAC
  - has_role() helper para verificacao de permissao

Algoritmo: HS256 (HMAC-SHA256) — suficiente para uso interno.
Chave secreta: configurada via JWT_SECRET_KEY no .env.

Roles validos (lowercase — valor armazenado no banco):
  admin             — superusuario, acesso total (Leandro)
  gerente           — ve todos, dashboard, redistribuir (Daiane)
  consultor         — propria carteira, sem gestao (Manu, Larissa)
  consultor_externo — propria carteira, sem financeiro (Julio — RCA externo)

Hierarquia numerica:
  admin=4 > gerente=3 > consultor=2 > consultor_externo=1
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import bcrypt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.app.config import settings

# ------------------------------------------------------------------
# RBAC — Enum de roles e hierarquia numerica
# ------------------------------------------------------------------


class UserRole(str, Enum):
    """
    Roles validos do sistema CRM VITAO360.

    Os valores sao strings lowercase — exatamente como sao armazenados
    no banco de dados (coluna usuarios.role).

    Nunca alterar os valores sem migration de dados correspondente.
    """

    ADMIN = "admin"
    GERENTE = "gerente"
    CONSULTOR = "consultor"
    VENDEDOR = "consultor_externo"  # Julio Gadret — RCA externo


# Hierarquia numerica: quanto maior, mais permissoes.
# Usado por has_role() para comparacao de nivel minimo.
ROLE_HIERARCHY: dict[str, int] = {
    UserRole.ADMIN: 4,
    UserRole.GERENTE: 3,
    UserRole.CONSULTOR: 2,
    UserRole.VENDEDOR: 1,
}


def has_role(user_role: str | None, min_role: UserRole | str) -> bool:
    """
    Verifica se um usuario tem nivel de role >= min_role.

    Uso em logica de negocio (fora de FastAPI Depends):
        if has_role(user.role, UserRole.GERENTE):
            # pode ver dashboard agregado

    Retorna False se user_role for None, vazio ou valor desconhecido.

    Args:
        user_role: valor do campo usuarios.role (ex.: "admin", "consultor")
        min_role:  nivel minimo exigido (UserRole enum ou string equivalente)

    Returns:
        True se o nivel do usuario >= nivel minimo exigido.
    """
    if not user_role:
        return False
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    # Normaliza min_role: aceita UserRole enum ou string direta
    min_str = min_role.value if isinstance(min_role, UserRole) else str(min_role)
    min_level = ROLE_HIERARCHY.get(min_str, 0)
    return user_level >= min_level


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
      role — role do usuario (admin | gerente | consultor | consultor_externo)
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
