"""
CRM VITAO360 — Dependencies FastAPI para injecao em rotas.

Centraliza a logica de autenticacao e autorizacao reutilizavel.
Cada dependency pode ser usada como parametro em qualquer rota via Depends().

Hierarquia de roles:
  admin             — acesso total
  gerente           — ve todos os consultores, sem configuracao (Daiane)
  consultor         — acesso a propria carteira
  consultor_externo — carteira propria, sem dados financeiros (Julio)
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.usuario import Usuario
from backend.app.security import decode_token, oauth2_scheme


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Extrai e valida o usuario autenticado a partir do JWT.

    Fluxo:
      1. Decodifica o token (JWTError levanta 401 internamente)
      2. Extrai o campo 'sub' (ID do usuario)
      3. Busca o usuario no banco
      4. Verifica se esta ativo

    Raises:
      HTTPException 401 — token invalido, sub ausente ou usuario nao encontrado
    """
    payload = decode_token(token)

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificacao de usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado ou inativo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Exige que o usuario autenticado tenha role 'admin'.

    Raises:
      HTTPException 403 — se role != 'admin'
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return user


def require_consultor_or_admin(
    user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Exige que o usuario autenticado tenha role com permissao de escrita.

    Roles permitidos: admin, gerente, consultor, consultor_externo.
    Usada em rotas de escrita (POST, PUT, DELETE) de atendimentos e carteira.

    Raises:
      HTTPException 403 — se role nao tiver permissao de escrita
    """
    if user.role not in ("admin", "gerente", "consultor", "consultor_externo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a consultores e administradores",
        )
    return user


def require_admin_or_gerente(user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Exige que o usuario autenticado tenha role 'admin' ou 'gerente'.

    Usada em rotas de edicao inline de carteira (PATCH /api/clientes/{cnpj}):
      - admin: acesso total, pode reatribuir qualquer cliente
      - gerente: pode reatribuir clientes da carteira (Daiane)

    Raises:
      HTTPException 403 — se role nao for admin nem gerente
    """
    if user.role not in ("admin", "gerente"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores e gerentes",
        )
    return user
