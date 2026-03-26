"""
CRM VITAO360 — Rotas /api/motor

Expoe as 92 regras do Motor de Regras (read-only).

As regras sao o nucleo de inteligencia comercial do CRM: cada combinacao
(situacao, resultado) define comportamento de follow-up, temperatura e
estagio do funil para o cliente.

Endpoints:
  GET /api/motor/regras          — lista todas as regras (filtravel por situacao)
  GET /api/motor/regras/{id}     — detalhe de uma regra pelo ID

Autorizacao:
  Ambos os endpoints exigem role=admin (regras sao configuracao interna do motor).

Restricoes:
  - Leitura apenas (nenhum POST/PATCH nesta versao — regras sao mantidas via seed)
  - Nenhum valor monetario (Two-Base Architecture respeitada — R4)
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import require_admin
from backend.app.database import get_db
from backend.app.models.regra_motor import RegraMotor
from backend.app.models.usuario import Usuario

router = APIRouter(prefix="/api/motor", tags=["Motor de Regras"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class RegraMotorResponse(BaseModel):
    """
    Representacao de uma regra do Motor de Regras.

    Campos de entrada (inputs da regra):
      situacao  — estado do cliente no CRM (ATIVO, PROSPECT, INAT.REC, INAT.ANT, ...)
      resultado — resultado da ultima interacao (Venda Realizada, Sem Contato, ...)

    Campos de saida (outputs aplicados ao LogInteracao):
      estagio_funil, fase, tipo_contato, acao_futura, temperatura,
      followup_dias, grupo_dash, tipo_acao, chave

    Nota: o modelo ORM usa follow_up_dias (com underscores).
    A resposta expoe followup_dias (sem underscores) para compatibilidade com o frontend.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    situacao: str
    resultado: str
    estagio_funil: str
    fase: str
    tipo_contato: str
    acao_futura: str
    temperatura: str
    # ORM column: follow_up_dias — exposto como followup_dias para o frontend
    followup_dias: int = Field(alias="follow_up_dias", serialization_alias="followup_dias")
    grupo_dash: Optional[str] = None
    tipo_acao: Optional[str] = None
    chave: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ListaRegrasResponse(BaseModel):
    """Wrapper com total e lista de regras — facilita paginacao futura."""

    total: int
    regras: list[RegraMotorResponse]


# ---------------------------------------------------------------------------
# GET /api/motor/regras — lista todas as regras (filtravel por situacao)
# ---------------------------------------------------------------------------

@router.get(
    "/regras",
    response_model=ListaRegrasResponse,
    summary="Listar regras do motor",
    description=(
        "Retorna todas as 92 regras do Motor de Regras. "
        "Filtragem opcional por situacao (ATIVO, PROSPECT, INAT.REC, INAT.ANT). "
        "Ordenado por situacao e chave. "
        "Restrito a administradores."
    ),
)
def listar_regras(
    situacao: Optional[str] = Query(
        None,
        description="Filtrar por situacao do cliente (ATIVO / PROSPECT / INAT.REC / INAT.ANT)",
    ),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ListaRegrasResponse:
    """
    Lista todas as regras do motor de inteligencia comercial.

    Filtro situacao e case-insensitive e uppercased antes da comparacao.
    Sem filtro retorna as 92 regras completas ordenadas por (situacao, chave).

    Permissao: somente admin.
    """
    stmt = select(RegraMotor).order_by(RegraMotor.situacao, RegraMotor.chave)

    if situacao:
        stmt = stmt.where(RegraMotor.situacao == situacao.upper())

    regras = db.scalars(stmt).all()

    return ListaRegrasResponse(
        total=len(regras),
        regras=[RegraMotorResponse.model_validate(r) for r in regras],
    )


# ---------------------------------------------------------------------------
# GET /api/motor/regras/{regra_id} — detalhe de uma regra
# ---------------------------------------------------------------------------

@router.get(
    "/regras/{regra_id}",
    response_model=RegraMotorResponse,
    summary="Detalhe de uma regra do motor",
    description=(
        "Retorna os dados completos de uma regra do motor pelo ID interno. "
        "Restrito a administradores."
    ),
)
def detalhe_regra(
    regra_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> RegraMotorResponse:
    """
    Retorna uma regra do motor pelo ID.

    Raises:
      HTTPException 404 — regra nao encontrada
    """
    regra = db.scalar(select(RegraMotor).where(RegraMotor.id == regra_id))
    if regra is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Regra do motor com id={regra_id} nao encontrada.",
        )

    return RegraMotorResponse.model_validate(regra)
