"""
CRM VITAO360 — Rotas /api/canais

Implementa a camada de API da arquitetura multi-canal (DECISAO L3 do
Leandro, 25/Apr/2026). Cada usuario ve apenas os canais autorizados via
tabela usuario_canal.

Endpoints:
  GET    /api/canais                              — lista canais visiveis ao user
  GET    /api/canais/me                           — canais permitidos do user atual
  GET    /api/canais/all                          — admin only, lista TODOS canais
  POST   /api/canais/{canal_id}/usuarios/{uid}    — admin: concede acesso
  DELETE /api/canais/{canal_id}/usuarios/{uid}    — admin: revoga acesso

Sem POST/PATCH/DELETE em /api/canais (criacao de canal eh via Alembic seed
para garantir consistencia operacional — DECISAO L3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_user,
    get_user_canal_ids,
    require_admin,
)
from backend.app.database import get_db
from backend.app.models.canal import Canal
from backend.app.models.usuario import Usuario
from backend.app.models.usuario_canal import UsuarioCanal

router = APIRouter(prefix="/api/canais", tags=["Canais"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class CanalResponse(BaseModel):
    """Canal de vendas SAP (workspace dimension)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    status: str
    descricao: Optional[str] = None
    created_at: Optional[datetime] = None


class UsuarioCanalResponse(BaseModel):
    """Associacao usuario-canal (dado de auditoria)."""

    model_config = ConfigDict(from_attributes=True)

    usuario_id: int
    canal_id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# GET /api/canais — canais visiveis ao usuario logado
# ---------------------------------------------------------------------------

@router.get("", response_model=list[CanalResponse], summary="Lista canais visiveis")
def listar_canais(
    user: Usuario = Depends(get_current_user),
    canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> list[Canal]:
    """
    Retorna canais que o usuario autenticado pode acessar.

    - admin: todos os canais (canal_ids=None na dependency)
    - demais: somente canais associados via usuario_canal

    Resposta vazia indica usuario sem canal — front deve mostrar empty state
    pedindo ao admin para conceder acesso.
    """
    query = db.query(Canal)
    if canal_ids is not None:
        if not canal_ids:
            return []
        query = query.filter(Canal.id.in_(canal_ids))
    return query.order_by(Canal.status.desc(), Canal.nome).all()


@router.get("/me", response_model=list[CanalResponse], summary="Canais do usuario atual")
def meus_canais(
    user: Usuario = Depends(get_current_user),
    canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> list[Canal]:
    """
    Atalho semantico para o seletor de canal no header/sidebar do front.
    Equivalente a GET /api/canais mas explicitamente "perspectiva do user".
    """
    return listar_canais(user=user, canal_ids=canal_ids, db=db)


@router.get(
    "/meus",
    response_model=list[CanalResponse],
    summary="Canais visiveis ao usuario atual (alias pt-BR)",
)
def listar_meus_canais(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Canal]:
    """
    Endpoint dedicado para o componente <CanalSelector/> do front.

    Difere de /me porque a ordenacao eh por `id` (nao por status), o que
    estabiliza o dropdown e mantem as cores dos badges previsiveis.

    - admin (role='admin'): retorna TODOS os canais (`SELECT * FROM canais ORDER BY id`).
    - demais roles: retorna apenas canais associados via tabela `usuario_canal`
      (`SELECT canais.* FROM canais JOIN usuario_canal ON canais.id = usuario_canal.canal_id
      WHERE usuario_canal.usuario_id = :user_id ORDER BY canais.id`).

    Resposta vazia indica usuario sem canal — front deve mostrar empty state
    pedindo ao admin para conceder acesso.
    """
    if user.role == "admin":
        return db.query(Canal).order_by(Canal.id).all()

    return (
        db.query(Canal)
        .join(UsuarioCanal, Canal.id == UsuarioCanal.canal_id)
        .filter(UsuarioCanal.usuario_id == user.id)
        .order_by(Canal.id)
        .all()
    )


@router.get(
    "/all",
    response_model=list[CanalResponse],
    summary="Lista TODOS canais (admin)",
)
def listar_todos_canais(
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Canal]:
    """Lista completa de canais (independente de usuario_canal). Admin only."""
    return db.query(Canal).order_by(Canal.status.desc(), Canal.nome).all()


# ---------------------------------------------------------------------------
# Permissions admin (concede / revoga acesso)
# ---------------------------------------------------------------------------

@router.post(
    "/{canal_id}/usuarios/{usuario_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=UsuarioCanalResponse,
    summary="Concede acesso de canal a usuario (admin)",
)
def conceder_acesso(
    canal_id: int,
    usuario_id: int,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioCanal:
    """Admin concede a um usuario o acesso a um canal especifico."""
    canal = db.query(Canal).filter(Canal.id == canal_id).first()
    if canal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canal nao encontrado")
    user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario nao encontrado")

    existente = (
        db.query(UsuarioCanal)
        .filter(
            UsuarioCanal.canal_id == canal_id,
            UsuarioCanal.usuario_id == usuario_id,
        )
        .first()
    )
    if existente:
        return existente  # idempotente

    assoc = UsuarioCanal(canal_id=canal_id, usuario_id=usuario_id)
    db.add(assoc)
    db.commit()
    db.refresh(assoc)
    return assoc


@router.delete(
    "/{canal_id}/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoga acesso de canal a usuario (admin)",
)
def revogar_acesso(
    canal_id: int,
    usuario_id: int,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Admin revoga o acesso de um usuario a um canal."""
    n = (
        db.query(UsuarioCanal)
        .filter(
            UsuarioCanal.canal_id == canal_id,
            UsuarioCanal.usuario_id == usuario_id,
        )
        .delete()
    )
    db.commit()
    if n == 0:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Associacao nao encontrada"
        )
