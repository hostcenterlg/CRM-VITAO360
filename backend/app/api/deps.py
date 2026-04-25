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


# ---------------------------------------------------------------------------
# Multi-canal (DECISAO L3 Leandro 25/Apr/2026)
# ---------------------------------------------------------------------------

def get_user_canal_ids(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[int] | None:
    """
    Resolve a lista de canal_ids que o usuario autenticado tem permissao.

    Convencoes:
      - admin: retorna None (sentinela para "todos os canais", inclusive
               clientes legados com canal_id=NULL).
      - gerente / consultor / consultor_externo: retorna list[int] com os
        ids dos canais associados via tabela usuario_canal.
      - usuario sem canal associado: retorna [] (lista vazia — bloqueia
        listagens de clientes filtradas).

    Uso em rotas de listagem:
        canal_ids = Depends(get_user_canal_ids)
        if canal_ids is None:
            ...  # admin — sem filtro
        elif not canal_ids:
            return []  # sem permissao
        else:
            query = query.filter(Cliente.canal_id.in_(canal_ids))
    """
    if user.role == "admin":
        return None  # admin ve tudo

    # Carrega via association table (lazy on user.canais)
    canais = list(user.canais or [])
    return [c.id for c in canais]


def get_user_canal_ids_strict(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[int]:
    """
    Variante de get_user_canal_ids que NUNCA retorna None.

    Para admin retorna a lista completa de canal_ids existentes em canais.
    Util para endpoints que precisam de lista concreta (ex.: filtrar por
    canal especifico via query param).
    """
    from backend.app.models.canal import Canal

    if user.role == "admin":
        return [c[0] for c in db.query(Canal.id).all()]

    return [c.id for c in (user.canais or [])]


# ---------------------------------------------------------------------------
# Helpers reutilizaveis para multi-canal scoping em queries
# ---------------------------------------------------------------------------

def cnpjs_permitidos_subquery(user_canal_ids: list[int] | None):
    """
    Retorna uma subquery SQL que enumera CNPJs cujo cliente pertence aos
    canais permitidos do usuario.

    Uso em endpoints que agregam Vendas/LogInteracoes/etc. e precisam
    restringir por canal:

        sub = cnpjs_permitidos_subquery(user_canal_ids)
        if sub is not None:
            stmt = stmt.where(Venda.cnpj.in_(sub))

    Retorna None se user_canal_ids is None (admin — sem filtro).
    Retorna subquery vazia (NOT IN) se user_canal_ids estiver vazio.
    """
    from sqlalchemy import select
    from backend.app.models.cliente import Cliente

    if user_canal_ids is None:
        return None
    if not user_canal_ids:
        # Subquery que nunca retorna nada — forca lista vazia
        return select(Cliente.cnpj).where(Cliente.id == -1)
    return select(Cliente.cnpj).where(Cliente.canal_id.in_(user_canal_ids))


def cliente_canal_filter(user_canal_ids: list[int] | None):
    """
    Retorna a clausula WHERE para filtrar Cliente por canal_id permitido.

    Uso:
        from backend.app.models.cliente import Cliente
        clause = cliente_canal_filter(user_canal_ids)
        if clause is not None:
            stmt = stmt.where(clause)

    Retorna None se admin (sem filtro). Retorna False-equivalent se sem
    permissao (lista vazia).
    """
    from sqlalchemy import false
    from backend.app.models.cliente import Cliente

    if user_canal_ids is None:
        return None
    if not user_canal_ids:
        return false()
    return Cliente.canal_id.in_(user_canal_ids)
