"""
CRM VITAO360 — Rotas de autenticacao.

Endpoints:
  POST   /api/auth/login        — Login com email + senha, retorna par JWT
  POST   /api/auth/refresh      — Renova access token a partir do refresh token
  GET    /api/auth/me           — Dados do usuario autenticado
  PUT    /api/auth/password     — Troca de senha (requer senha atual)
  POST   /api/auth/users        — Cria novo usuario (admin only)
  GET    /api/auth/users        — Lista todos os usuarios (admin only)

Seguranca:
  - Senhas armazenadas como hash bcrypt
  - Tokens JWT com expiracao (access: 8h, refresh: 30d)
  - Refresh token valida tipo "refresh" para evitar uso cruzado
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import get_db
from backend.app.models.usuario import Usuario
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UsuarioCreate,
    UsuarioResponse,
)
from backend.app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Autenticacao"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login com email e senha",
)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica o usuario e retorna par de tokens JWT.

    - Verifica email e senha via bcrypt
    - Atualiza campo last_login
    - Retorna access token (8h) e refresh token (30d)

    Raises:
      401 — email ou senha incorretos
      403 — usuario desativado
    """
    user = db.query(Usuario).filter(Usuario.email == body.email).first()

    # Verificacao em dois passos para evitar timing attack (nao revelar qual falhou)
    if not user or not verify_password(body.senha, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desativado — contate o administrador",
        )

    # Registra ultimo acesso
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "consultor": user.consultor_nome,
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token",
)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """
    Emite novo par de tokens a partir de um refresh token valido.

    Valida que o token e do tipo 'refresh' antes de processar.

    Raises:
      400 — token nao e do tipo refresh
      401 — usuario invalido ou inativo
    """
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token nao e do tipo refresh",
        )

    user_id: str | None = payload.get("sub")
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()

    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario invalido ou inativo",
        )

    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "consultor": user.consultor_nome,
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Dados do usuario autenticado",
)
def me(user: Usuario = Depends(get_current_user)):
    """
    Retorna os dados publicos do usuario autenticado.

    Utiliza a dependency get_current_user para validar o Bearer token.
    """
    return user


@router.put(
    "/password",
    summary="Trocar senha",
)
def change_password(
    body: ChangePasswordRequest,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permite que o usuario troque sua propria senha.

    Exige confirmacao da senha atual para prevenir alteracao indevida
    em sessoes roubadas.

    Raises:
      400 — senha atual incorreta
    """
    if not verify_password(body.senha_atual, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )

    user.hashed_password = hash_password(body.nova_senha)
    db.commit()

    return {"mensagem": "Senha alterada com sucesso"}


@router.post(
    "/users",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuario (admin)",
)
def create_user(
    body: UsuarioCreate,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Cria novo usuario no sistema. Acesso restrito a administradores.

    Para role 'consultor', o campo consultor_nome deve corresponder ao
    DE-PARA de vendedores: MANU, LARISSA, DAIANE.

    Raises:
      409 — email ja cadastrado
    """
    if db.query(Usuario).filter(Usuario.email == body.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ja cadastrado",
        )

    user = Usuario(
        email=body.email,
        nome=body.nome,
        hashed_password=hash_password(body.senha),
        role=body.role,
        consultor_nome=body.consultor_nome,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get(
    "/users",
    response_model=list[UsuarioResponse],
    summary="Listar usuarios (admin)",
)
def list_users(
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Lista todos os usuarios do sistema ordenados por nome.

    Acesso restrito a administradores.
    """
    return db.query(Usuario).order_by(Usuario.nome).all()
