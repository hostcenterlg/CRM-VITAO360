"""
CRM VITAO360 — Rotas /api/dashboard

Endpoints KPI para o painel gerencial:

  GET /api/dashboard/kpis          — indicadores principais
  GET /api/dashboard/distribuicao  — distribuições (sinaleiro, situação, prioridade, consultor)
  GET /api/dashboard/top10         — top 10 clientes por faturamento
  GET /api/dashboard/projecao      — projeção: realizado vs meta por consultor

Faturamento baseline: R$ 2.091.000 (CORRIGIDO 2026-03-23, R7).
Todos os valores monetários são Float; o frontend formata como R$.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.cliente import Cliente

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Baseline auditado (R7) — referência para % de meta quando meta_anual não está preenchida
FATURAMENTO_BASELINE = 2_091_000.0


# ---------------------------------------------------------------------------
# Schemas de resposta
# ---------------------------------------------------------------------------

class KPIsResponse(BaseModel):
    total_clientes: int
    total_ativos: int
    total_prospects: int
    total_inativos: int         # soma INAT.REC + INAT.ANT
    faturamento_total: float    # soma de faturamento_total dos registros REAL
    media_score: float
    clientes_alerta: int        # sinaleiro VERMELHO ou AMARELO
    clientes_criticos: int      # temperatura CRITICO
    followups_vencidos: int


class DistribuicaoItem(BaseModel):
    label: str
    quantidade: int
    percentual: float


class DistribuicaoResponse(BaseModel):
    por_sinaleiro: list[DistribuicaoItem]
    por_situacao: list[DistribuicaoItem]
    por_prioridade: list[DistribuicaoItem]
    por_consultor: list[DistribuicaoItem]
    por_curva_abc: list[DistribuicaoItem]
    por_temperatura: list[DistribuicaoItem]


class Top10Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cnpj: str
    nome_fantasia: Optional[str]
    consultor: Optional[str]
    faturamento_total: Optional[float]
    curva_abc: Optional[str]
    sinaleiro: Optional[str]
    situacao: Optional[str]


class ProjecaoConsultor(BaseModel):
    consultor: str
    total_clientes: int
    faturamento_realizado: float
    meta_anual_total: float
    pct_alcancado_medio: float   # média ponderada de pct_alcancado
    clientes_acima_meta: int
    clientes_alerta: int
    clientes_criticos: int


class ProjecaoResponse(BaseModel):
    faturamento_total_real: float
    faturamento_baseline: float
    pct_baseline: float           # faturamento_total_real / baseline
    por_consultor: list[ProjecaoConsultor]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _distribuicao(db: Session, coluna, total: int) -> list[DistribuicaoItem]:
    rows = db.execute(
        select(coluna, func.count().label("qt"))
        .group_by(coluna)
        .order_by(func.count().desc())
    ).all()
    return [
        DistribuicaoItem(
            label=r[0] or "—",
            quantidade=r[1],
            percentual=round(r[1] / total * 100, 1) if total else 0.0,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/kpis", response_model=KPIsResponse, summary="KPIs principais")
def kpis(db: Session = Depends(get_db)) -> KPIsResponse:
    """
    Indicadores-chave do painel gerencial.

    - faturamento_total: soma dos registros com classificacao_3tier IN (REAL, SINTETICO).
      Registros ALUCINACAO são excluídos (R8).
    - clientes_alerta: sinaleiro VERMELHO ou AMARELO.
    - followups_vencidos: followup_vencido = True.
    """
    total = db.scalar(select(func.count()).select_from(Cliente)) or 0

    total_ativos = db.scalar(
        select(func.count()).select_from(Cliente).where(Cliente.situacao == "ATIVO")
    ) or 0

    total_prospects = db.scalar(
        select(func.count()).select_from(Cliente).where(Cliente.situacao == "PROSPECT")
    ) or 0

    total_inativos = db.scalar(
        select(func.count())
        .select_from(Cliente)
        .where(Cliente.situacao.in_(["INAT.REC", "INAT.ANT"]))
    ) or 0

    # R8: excluir ALUCINACAO do faturamento
    fat_total = db.scalar(
        select(func.coalesce(func.sum(Cliente.faturamento_total), 0.0))
        .where(Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]))
    ) or 0.0

    media_score = db.scalar(
        select(func.avg(Cliente.score))
    ) or 0.0

    clientes_alerta = db.scalar(
        select(func.count())
        .select_from(Cliente)
        .where(Cliente.sinaleiro.in_(["VERMELHO", "AMARELO"]))
    ) or 0

    clientes_criticos = db.scalar(
        select(func.count())
        .select_from(Cliente)
        .where(Cliente.temperatura == "CRITICO")
    ) or 0

    followups_vencidos = db.scalar(
        select(func.count())
        .select_from(Cliente)
        .where(Cliente.followup_vencido == True)  # noqa: E712
    ) or 0

    return KPIsResponse(
        total_clientes=total,
        total_ativos=total_ativos,
        total_prospects=total_prospects,
        total_inativos=total_inativos,
        faturamento_total=round(fat_total, 2),
        media_score=round(float(media_score), 1),
        clientes_alerta=clientes_alerta,
        clientes_criticos=clientes_criticos,
        followups_vencidos=followups_vencidos,
    )


@router.get("/distribuicao", response_model=DistribuicaoResponse, summary="Distribuições")
def distribuicao(db: Session = Depends(get_db)) -> DistribuicaoResponse:
    """
    Distribuições percentuais por sinaleiro, situação, prioridade,
    consultor, curva ABC e temperatura.
    """
    total = db.scalar(select(func.count()).select_from(Cliente)) or 1  # evitar /0

    return DistribuicaoResponse(
        por_sinaleiro=_distribuicao(db, Cliente.sinaleiro, total),
        por_situacao=_distribuicao(db, Cliente.situacao, total),
        por_prioridade=_distribuicao(db, Cliente.prioridade, total),
        por_consultor=_distribuicao(db, Cliente.consultor, total),
        por_curva_abc=_distribuicao(db, Cliente.curva_abc, total),
        por_temperatura=_distribuicao(db, Cliente.temperatura, total),
    )


@router.get("/top10", response_model=list[Top10Item], summary="Top 10 clientes por faturamento")
def top10(db: Session = Depends(get_db)) -> list[Top10Item]:
    """
    Os 10 clientes com maior faturamento_total.
    Apenas registros REAL ou SINTETICO (R8).
    """
    stmt = (
        select(Cliente)
        .where(
            Cliente.faturamento_total.isnot(None),
            Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]),
        )
        .order_by(Cliente.faturamento_total.desc())
        .limit(10)
    )
    clientes = db.scalars(stmt).all()
    return [Top10Item.model_validate(c) for c in clientes]


@router.get("/projecao", response_model=ProjecaoResponse, summary="Projeção vs meta por consultor")
def projecao(db: Session = Depends(get_db)) -> ProjecaoResponse:
    """
    Consolidado de projeção anual:
      - faturamento_total_real: soma do realizado por todos os consultores
      - pct_baseline: quanto representa do baseline R$ 2.091.000
      - por_consultor: detalhamento por consultor com status_meta
    """
    consultores_alvo = ["MANU", "LARISSA", "DAIANE", "JULIO"]

    fat_total = db.scalar(
        select(func.coalesce(func.sum(Cliente.faturamento_total), 0.0))
        .where(Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]))
    ) or 0.0

    por_consultor: list[ProjecaoConsultor] = []

    for consultor in consultores_alvo:
        total_c = db.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(Cliente.consultor == consultor)
        ) or 0

        fat_c = db.scalar(
            select(func.coalesce(func.sum(Cliente.faturamento_total), 0.0))
            .where(
                Cliente.consultor == consultor,
                Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            )
        ) or 0.0

        meta_c = db.scalar(
            select(func.coalesce(func.sum(Cliente.meta_anual), 0.0))
            .where(Cliente.consultor == consultor)
        ) or 0.0

        pct_medio = db.scalar(
            select(func.avg(Cliente.pct_alcancado))
            .where(
                Cliente.consultor == consultor,
                Cliente.pct_alcancado.isnot(None),
            )
        ) or 0.0

        acima = db.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(
                Cliente.consultor == consultor,
                Cliente.status_meta == "ACIMA",
            )
        ) or 0

        alerta = db.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(
                Cliente.consultor == consultor,
                Cliente.status_meta == "ALERTA",
            )
        ) or 0

        critico = db.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(
                Cliente.consultor == consultor,
                Cliente.status_meta == "CRITICO",
            )
        ) or 0

        por_consultor.append(
            ProjecaoConsultor(
                consultor=consultor,
                total_clientes=total_c,
                faturamento_realizado=round(fat_c, 2),
                meta_anual_total=round(meta_c, 2),
                pct_alcancado_medio=round(float(pct_medio) * 100, 1),
                clientes_acima_meta=acima,
                clientes_alerta=alerta,
                clientes_criticos=critico,
            )
        )

    return ProjecaoResponse(
        faturamento_total_real=round(fat_total, 2),
        faturamento_baseline=FATURAMENTO_BASELINE,
        pct_baseline=round(fat_total / FATURAMENTO_BASELINE * 100, 1),
        por_consultor=por_consultor,
    )
