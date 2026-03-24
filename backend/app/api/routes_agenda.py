"""
CRM VITAO360 — Rotas /api/agenda

Endpoints:
  GET /api/agenda               — todos os itens de hoje
  GET /api/agenda/{consultor}   — agenda de um consultor específico

A data padrão é hoje (server date).  Para outra data, passar ?data=YYYY-MM-DD.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.agenda import AgendaItem

router = APIRouter(prefix="/api/agenda", tags=["Agenda"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class AgendaItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: Optional[str]
    consultor: str
    data_agenda: date
    posicao: int
    nome_fantasia: Optional[str]
    situacao: Optional[str]
    temperatura: Optional[str]
    score: Optional[float]
    prioridade: Optional[str]
    sinaleiro: Optional[str]
    acao: Optional[str]
    followup_dias: Optional[int]


class AgendaConsultorResponse(BaseModel):
    consultor: str
    data_agenda: date
    total: int
    itens: list[AgendaItemSchema]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_data(data_str: Optional[str]) -> date:
    """Parseia YYYY-MM-DD ou retorna hoje."""
    if data_str:
        try:
            return datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Parâmetro 'data' deve estar no formato YYYY-MM-DD.",
            )
    return date.today()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[AgendaConsultorResponse],
    summary="Agenda do dia — todos os consultores",
)
def agenda_hoje(
    data: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD (padrão: hoje)"),
    db: Session = Depends(get_db),
) -> list[AgendaConsultorResponse]:
    """
    Retorna a agenda agrupada por consultor para a data informada.
    Consultores com agenda vazia não aparecem na resposta.
    """
    data_ref = _parse_data(data)

    stmt = (
        select(AgendaItem)
        .where(AgendaItem.data_agenda == data_ref)
        .order_by(AgendaItem.consultor, AgendaItem.posicao)
    )
    itens = db.scalars(stmt).all()

    # Agrupar por consultor
    por_consultor: dict[str, list[AgendaItem]] = {}
    for item in itens:
        por_consultor.setdefault(item.consultor, []).append(item)

    return [
        AgendaConsultorResponse(
            consultor=consultor,
            data_agenda=data_ref,
            total=len(lista),
            itens=[AgendaItemSchema.model_validate(i) for i in lista],
        )
        for consultor, lista in por_consultor.items()
    ]


@router.get(
    "/{consultor}",
    response_model=AgendaConsultorResponse,
    summary="Agenda de um consultor específico",
)
def agenda_consultor(
    consultor: str,
    data: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD (padrão: hoje)"),
    db: Session = Depends(get_db),
) -> AgendaConsultorResponse:
    """
    Retorna a agenda de um consultor para a data informada.
    Retorna 404 se o consultor não existir ou não tiver agenda na data.

    Consultores válidos: MANU, LARISSA, DAIANE, JULIO.
    """
    consultor_upper = consultor.upper()
    data_ref = _parse_data(data)

    stmt = (
        select(AgendaItem)
        .where(
            AgendaItem.consultor == consultor_upper,
            AgendaItem.data_agenda == data_ref,
        )
        .order_by(AgendaItem.posicao)
    )
    itens = db.scalars(stmt).all()

    if not itens:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nenhum item de agenda para o consultor '{consultor_upper}' "
                f"na data {data_ref.isoformat()}."
            ),
        )

    return AgendaConsultorResponse(
        consultor=consultor_upper,
        data_agenda=data_ref,
        total=len(itens),
        itens=[AgendaItemSchema.model_validate(i) for i in itens],
    )
