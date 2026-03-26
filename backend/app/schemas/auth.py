"""
CRM VITAO360 — Schemas Pydantic para autenticacao.

Define contratos de entrada e saida dos endpoints de auth:
  - LoginRequest       : corpo do POST /api/auth/login
  - TokenResponse      : resposta com par de tokens JWT
  - RefreshRequest     : corpo do POST /api/auth/refresh
  - UsuarioResponse    : representacao publica de um usuario (sem senha)
  - UsuarioCreate      : corpo do POST /api/auth/users (admin only)
  - ChangePasswordRequest : corpo do PUT /api/auth/password
"""

from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Credenciais para autenticacao."""

    email: str
    senha: str


class TokenResponse(BaseModel):
    """Par de tokens JWT retornado apos login ou refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token de refresh para renovar o access token."""

    refresh_token: str


class UsuarioResponse(BaseModel):
    """
    Representacao publica de um usuario.

    Nunca expoe hashed_password nem dados sensiveis.
    """

    id: int
    email: str
    nome: str
    role: str
    consultor_nome: str | None
    ativo: bool

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    """
    Dados para criacao de novo usuario (admin only).

    role padrao: 'consultor' — exige consultor_nome para vinculo ao DE-PARA
    de vendedores (MANU, LARISSA, DAIANE).
    """

    email: str
    nome: str
    senha: str
    role: str = "consultor"
    consultor_nome: str | None = None


class ChangePasswordRequest(BaseModel):
    """Troca de senha autenticada — exige confirmacao da senha atual."""

    senha_atual: str
    nova_senha: str
