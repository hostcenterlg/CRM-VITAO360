"""
CRM VITAO360 — Rotas /api/agenda

Endpoints:
  GET  /api/agenda               — todos os itens de hoje (autenticado)
  GET  /api/agenda/historico     — agenda de data anterior (autenticado)
  GET  /api/agenda/{consultor}   — agenda de um consultor específico (autenticado)
  POST /api/agenda/gerar         — gera/regenera agenda do dia (admin only)

A data padrão é hoje (server date).  Para outra data, passar ?data=YYYY-MM-DD.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import get_db
from backend.app.models.agenda import AgendaItem
from backend.app.models.usuario import Usuario

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

def _parse_data(data_str: Optional[str]) -> date | None:
    """Parseia YYYY-MM-DD ou retorna None (usar data mais recente)."""
    if data_str:
        try:
            return datetime.strptime(data_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Parâmetro 'data' deve estar no formato YYYY-MM-DD.",
            )
    return None


def _data_mais_recente(db: Session, consultor: Optional[str] = None) -> date | None:
    """Retorna a data mais recente com itens de agenda (opcionalmente para um consultor)."""
    stmt = select(func.max(AgendaItem.data_agenda))
    if consultor:
        stmt = stmt.where(AgendaItem.consultor == consultor)
    return db.scalar(stmt)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[AgendaConsultorResponse],
    summary="Agenda do dia — todos os consultores",
)
def agenda_hoje(
    data: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD (padrão: mais recente)"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AgendaConsultorResponse]:
    """
    Retorna a agenda agrupada por consultor para a data informada.
    Se nenhuma data for fornecida, retorna a agenda mais recente disponível.
    Consultores com agenda vazia não aparecem na resposta.
    """
    data_ref = _parse_data(data) or _data_mais_recente(db) or date.today()

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


@router.post(
    "/gerar",
    summary="Gera/regenera agenda do dia — somente admin",
    status_code=200,
)
def gerar_agenda(
    data: Optional[str] = Query(None, description="Data alvo no formato YYYY-MM-DD (padrão: hoje)"),
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """
    Gera (ou regenera) a agenda priorizada para todos os consultores na data informada.

    Regras aplicadas:
      - P0 pula fila e não conta no limite de atendimentos
      - P7 nunca entra na agenda regular
      - Limite: 40 por consultor (Daiane: 20)
      - Ordenação: P0 -> P1 -> P2-P6 por score desc
      - Dados ALUCINAÇÃO são excluídos (R8)

    A operação é idempotente: chamar duas vezes na mesma data substitui a
    agenda anterior sem duplicatas.

    Acesso restrito a administradores.
    """
    from backend.app.services.agenda_service import agenda_service

    data_ref = _parse_data(data) or date.today()
    resultado = agenda_service.gerar_todas(db, data_ref)
    db.commit()

    return {
        "data": data_ref.isoformat(),
        "por_consultor": resultado,
        "total": sum(resultado.values()),
    }


@router.get(
    "/historico",
    response_model=list[AgendaItemSchema],
    summary="Agenda de uma data anterior",
)
def agenda_historico(
    data: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD (padrão: hoje)"),
    consultor: Optional[str] = Query(None, description="Filtrar por consultor (MANU, LARISSA, DAIANE, JULIO)"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AgendaItemSchema]:
    """
    Retorna os itens de agenda de uma data específica.

    Útil para consultar histórico de agendas passadas.
    Pode ser filtrado por consultor via query param.

    Formato da data: YYYY-MM-DD.
    Se omitida, retorna a agenda de hoje.
    """
    target = _parse_data(data) or date.today()

    stmt = (
        select(AgendaItem)
        .where(AgendaItem.data_agenda == target)
        .order_by(AgendaItem.consultor, AgendaItem.posicao)
    )
    if consultor:
        stmt = stmt.where(AgendaItem.consultor == consultor.upper())

    itens = db.scalars(stmt).all()
    return [AgendaItemSchema.model_validate(i) for i in itens]


@router.get(
    "/{consultor}",
    response_model=AgendaConsultorResponse,
    summary="Agenda de um consultor específico",
)
def agenda_consultor(
    consultor: str,
    data: Optional[str] = Query(None, description="Data no formato YYYY-MM-DD (padrão: mais recente)"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AgendaConsultorResponse:
    """
    Retorna a agenda de um consultor para a data informada.
    Se nenhuma data for fornecida, retorna a agenda mais recente.
    Retorna lista vazia se não houver itens.

    Consultores válidos: MANU, LARISSA, DAIANE, JULIO.
    """
    consultor_upper = consultor.upper()
    data_ref = _parse_data(data) or _data_mais_recente(db, consultor_upper) or date.today()

    stmt = (
        select(AgendaItem)
        .where(
            AgendaItem.consultor == consultor_upper,
            AgendaItem.data_agenda == data_ref,
        )
        .order_by(AgendaItem.posicao)
    )
    itens = db.scalars(stmt).all()

    return AgendaConsultorResponse(
        consultor=consultor_upper,
        data_agenda=data_ref,
        total=len(itens),
        itens=[AgendaItemSchema.model_validate(i) for i in itens],
    )
