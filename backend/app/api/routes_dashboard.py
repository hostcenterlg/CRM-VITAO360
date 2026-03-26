"""
CRM VITAO360 — Rotas /api/dashboard

Endpoints KPI para o painel gerencial:

  GET /api/dashboard/kpis          — indicadores principais
  GET /api/dashboard/distribuicao  — distribuicoes (sinaleiro, situacao, prioridade, consultor)
  GET /api/dashboard/top10         — top 10 clientes por faturamento
  GET /api/dashboard/projecao      — projecao: realizado vs meta por consultor
  GET /api/dashboard/funil         — pipeline por estagio de funil

Faturamento baseline: R$ 2.091.000 (CORRIGIDO 2026-03-23, R7).
Todos os valores monetarios sao Float; o frontend formata como R$.
Todos os endpoints requerem autenticacao JWT (Bearer token).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.usuario import Usuario

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
    count: int
    pct: float


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
    score: Optional[float]
    prioridade: Optional[str]
    curva_abc: Optional[str]
    sinaleiro: Optional[str]
    situacao: Optional[str]


class ProjecaoResumo(BaseModel):
    faturamento_realizado: float
    meta_q1: float
    pct_alcancado: float
    baseline_2025: float
    projecao_2026: float


class ProjecaoConsultor(BaseModel):
    consultor: str
    faturamento: float
    meta: float
    pct_alcancado: float


class ProjecaoResponse(BaseModel):
    resumo: ProjecaoResumo
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
            count=r[1],
            pct=round(r[1] / total * 100, 1) if total else 0.0,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/kpis", response_model=KPIsResponse, summary="KPIs principais")
def kpis(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KPIsResponse:
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


@router.get("/distribuicao", response_model=DistribuicaoResponse, summary="Distribuicoes")
def distribuicao(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DistribuicaoResponse:
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
def top10(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Top10Item]:
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


@router.get("/projecao", response_model=ProjecaoResponse, summary="Projecao vs meta por consultor")
def projecao(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjecaoResponse:
    """
    Consolidado de projeção anual:
      - resumo: faturamento realizado, meta Q1, % alcançado, baseline e projeção
      - por_consultor: faturamento vs meta por consultor
    """
    PROJECAO_2026 = 3_377_120.0
    META_Q1 = PROJECAO_2026 / 4  # meta trimestral proporcional

    consultores_alvo = ["MANU", "LARISSA", "DAIANE", "JULIO"]

    fat_total = db.scalar(
        select(func.coalesce(func.sum(Cliente.faturamento_total), 0.0))
        .where(Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]))
    ) or 0.0

    por_consultor: list[ProjecaoConsultor] = []

    for consultor in consultores_alvo:
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

        # Se meta_anual não estiver preenchida, distribui proporcional ao baseline
        if meta_c == 0:
            meta_c = FATURAMENTO_BASELINE / len(consultores_alvo)

        pct = round(fat_c / meta_c * 100, 1) if meta_c > 0 else 0.0

        por_consultor.append(
            ProjecaoConsultor(
                consultor=consultor,
                faturamento=round(fat_c, 2),
                meta=round(meta_c, 2),
                pct_alcancado=pct,
            )
        )

    pct_q1 = round(fat_total / META_Q1 * 100, 1) if META_Q1 > 0 else 0.0

    return ProjecaoResponse(
        resumo=ProjecaoResumo(
            faturamento_realizado=round(fat_total, 2),
            meta_q1=round(META_Q1, 2),
            pct_alcancado=pct_q1,
            baseline_2025=FATURAMENTO_BASELINE,
            projecao_2026=PROJECAO_2026,
        ),
        por_consultor=por_consultor,
    )


@router.get(
    "/funil",
    summary="Pipeline de clientes por estagio de funil",
)
def funil(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna a distribuicao de clientes por estagio_funil.

    Clientes sem estagio_funil preenchido sao omitidos.
    Ordenacao: maior volume primeiro.

    Requer autenticacao JWT.
    """
    rows = db.execute(
        select(Cliente.estagio_funil, func.count().label("qt"))
        .where(Cliente.estagio_funil.isnot(None))
        .group_by(Cliente.estagio_funil)
        .order_by(func.count().desc())
    ).all()

    return [{"estagio": r[0], "total": r[1]} for r in rows]
