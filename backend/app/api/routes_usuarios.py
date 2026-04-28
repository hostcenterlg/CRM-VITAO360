"""
CRM VITAO360 — Rotas /api/usuarios

Endpoints administrativos focados na ACL de canais por usuario.
Complementa /api/auth/users (CRUD basico) e /api/canais (listagem + grant/revoke
por (canal, usuario) individualmente).

Endpoints:
  GET  /api/usuarios/{usuario_id}/canais   — admin: lista canais do usuario
  PUT  /api/usuarios/{usuario_id}/canais   — admin: substitui ACL completa do usuario

DECISAO L3 (Leandro 25/Apr/2026): canal_ids passado em PUT substitui a ACL
inteira do usuario em uma transacao unica (delete + insert), para evitar
estados intermediarios visiveis a outros admins simultaneos.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import require_admin
from backend.app.database import get_db
from backend.app.models.canal import Canal
from backend.app.models.usuario import Usuario
from backend.app.models.usuario_canal import UsuarioCanal

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class CanalACLItem(BaseModel):
    """Canal exposto na ACL de um usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    status: str
    descricao: Optional[str] = None


class UsuarioCanaisUpdate(BaseModel):
    """Body do PUT /api/usuarios/{id}/canais — lista canonica de canais permitidos."""

    canal_ids: list[int] = Field(
        ...,
        description="IDs dos canais que o usuario tera acesso. Substitui a ACL inteira.",
    )


class UsuarioCanaisResponse(BaseModel):
    """Resposta consistente para GET e PUT da ACL de canais do usuario."""

    usuario_id: int
    canais: list[CanalACLItem]


# ---------------------------------------------------------------------------
# GET /api/usuarios/{usuario_id}/canais
# ---------------------------------------------------------------------------

@router.get(
    "/{usuario_id}/canais",
    response_model=UsuarioCanaisResponse,
    summary="Lista canais permitidos de um usuario (admin)",
)
def listar_canais_do_usuario(
    usuario_id: int,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioCanaisResponse:
    """Retorna a ACL atual de canais para o usuario informado."""
    user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario nao encontrado")

    canais = (
        db.query(Canal)
        .join(UsuarioCanal, Canal.id == UsuarioCanal.canal_id)
        .filter(UsuarioCanal.usuario_id == usuario_id)
        .order_by(Canal.id)
        .all()
    )
    return UsuarioCanaisResponse(usuario_id=usuario_id, canais=canais)


# ---------------------------------------------------------------------------
# PUT /api/usuarios/{usuario_id}/canais — bulk replace ACL
# ---------------------------------------------------------------------------

@router.put(
    "/{usuario_id}/canais",
    response_model=UsuarioCanaisResponse,
    summary="Substitui ACL de canais do usuario (admin)",
)
def atualizar_canais_do_usuario(
    usuario_id: int,
    body: UsuarioCanaisUpdate,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioCanaisResponse:
    """
    Substitui completamente a ACL de canais do usuario.

    Fluxo (em uma unica transacao):
      1. Verifica se o usuario existe (404 se nao)
      2. Verifica se TODOS os canal_ids existem em `canais` (400 se nao)
      3. DELETE FROM usuario_canal WHERE usuario_id = :id
      4. INSERT INTO usuario_canal (usuario_id, canal_id) para cada canal_id
      5. Retorna a ACL final como lista de canais ordenada por id

    Note: canal_ids vazia eh permitido (revoga todos os canais do usuario).
    """
    user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario nao encontrado")

    canal_ids_unicos = list(dict.fromkeys(body.canal_ids))  # mantem ordem, remove dup

    if canal_ids_unicos:
        canais_existentes = (
            db.query(Canal).filter(Canal.id.in_(canal_ids_unicos)).all()
        )
        ids_existentes = {c.id for c in canais_existentes}
        ids_invalidos = [cid for cid in canal_ids_unicos if cid not in ids_existentes]
        if ids_invalidos:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"canal_ids invalidos: {ids_invalidos}",
            )

    try:
        # DELETE existente
        db.query(UsuarioCanal).filter(
            UsuarioCanal.usuario_id == usuario_id
        ).delete(synchronize_session=False)

        # INSERT novo conjunto
        for cid in canal_ids_unicos:
            db.add(UsuarioCanal(usuario_id=usuario_id, canal_id=cid))

        db.commit()
    except Exception:
        db.rollback()
        raise

    canais = (
        db.query(Canal)
        .join(UsuarioCanal, Canal.id == UsuarioCanal.canal_id)
        .filter(UsuarioCanal.usuario_id == usuario_id)
        .order_by(Canal.id)
        .all()
    )
    return UsuarioCanaisResponse(usuario_id=usuario_id, canais=canais)
