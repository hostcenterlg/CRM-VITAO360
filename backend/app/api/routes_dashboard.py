"""
CRM VITAO360 — Rotas /api/dashboard

Endpoints KPI para o painel gerencial:

  GET /api/dashboard/kpis          — indicadores principais
  GET /api/dashboard/distribuicao  — distribuicoes (sinaleiro, situacao, prioridade, consultor)
  GET /api/dashboard/top10         — top 10 clientes por faturamento
  GET /api/dashboard/projecao      — projecao: realizado vs meta por consultor
  GET /api/dashboard/funil         — pipeline por estagio de funil
  GET /api/dashboard/tendencias    — tendencias mensais dos ultimos 12 meses

Faturamento baseline: R$ 2.091.000 (CORRIGIDO 2026-03-23, R7).
Todos os valores monetarios sao Float; o frontend formata como R$.
Todos os endpoints requerem autenticacao JWT (Bearer token).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda

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
    # Fonte de verdade: tabela vendas (Two-Base Architecture — R1/R7)
    fat_total = db.scalar(
        select(func.coalesce(func.sum(Venda.valor_pedido), 0.0))
        .where(Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]))
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

    # Fonte de verdade: tabela vendas (Two-Base Architecture — R1/R7)
    fat_total = db.scalar(
        select(func.coalesce(func.sum(Venda.valor_pedido), 0.0))
        .where(Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]))
    ) or 0.0

    por_consultor: list[ProjecaoConsultor] = []

    for consultor in consultores_alvo:
        fat_c = db.scalar(
            select(func.coalesce(func.sum(Venda.valor_pedido), 0.0))
            .where(
                Venda.consultor == consultor,
                Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
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


# ---------------------------------------------------------------------------
# Territorios por consultor — mapeamento fixo (dominio VITAO360)
# ---------------------------------------------------------------------------

_TERRITORIOS: dict[str, str] = {
    "MANU":    "SC / PR / RS",
    "LARISSA": "Resto do Brasil",
    "DAIANE":  "Key Account / Redes",
    "JULIO":   "Externo (RCA)",
}

# Meta 2026 proporcional ao baseline (distribuicao historica)
_METAS_2026: dict[str, float] = {
    "MANU":    693_000.0,   # ~33% do baseline R$2.091M
    "LARISSA": 940_950.0,   # ~45%
    "DAIANE":  300_000.0,   # ~14%
    "JULIO":   156_150.0,   # ~8%
}


@router.get(
    "/performance",
    summary="Performance por consultor — KPIs de meta e faturamento",
)
def performance(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna performance de cada consultor com:
      - territorio: regiao de atuacao
      - total_clientes: clientes na carteira (nao-ALUCINACAO)
      - faturamento_real: soma de faturamento_total dos clientes REAL/SINTETICO
      - meta_2026: meta anual 2026 (soma de meta_anual ou fallback proporcional)
      - pct_atingimento: faturamento_real / meta_2026 * 100
      - status: BOM (>=70%), ALERTA (40-69%), CRITICO (<40%)

    Ordenacao: maior faturamento_real primeiro.

    Requer autenticacao JWT.
    """
    consultores_alvo = list(_TERRITORIOS.keys())
    resultado: list[dict] = []

    for consultor in consultores_alvo:
        total_clientes = db.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(
                Cliente.consultor == consultor,
                Cliente.classificacao_3tier != "ALUCINACAO",
            )
        ) or 0

        # Fonte de verdade: tabela vendas (Two-Base Architecture — R1/R7)
        fat_real = db.scalar(
            select(func.coalesce(func.sum(Venda.valor_pedido), 0.0))
            .where(
                Venda.consultor == consultor,
                Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            )
        ) or 0.0

        # Meta: soma das metas individuais; fallback ao _METAS_2026
        meta_db = db.scalar(
            select(func.coalesce(func.sum(Cliente.meta_anual), 0.0))
            .where(Cliente.consultor == consultor)
        ) or 0.0

        meta_2026 = round(meta_db if meta_db > 0 else _METAS_2026.get(consultor, 0.0), 2)
        fat_real = round(float(fat_real), 2)
        pct = round(fat_real / meta_2026 * 100, 1) if meta_2026 > 0 else 0.0

        if pct >= 70:
            status = "BOM"
        elif pct >= 40:
            status = "ALERTA"
        else:
            status = "CRITICO"

        resultado.append(
            {
                "consultor": consultor,
                "territorio": _TERRITORIOS[consultor],
                "total_clientes": total_clientes,
                "faturamento_real": fat_real,
                "meta_2026": meta_2026,
                "pct_atingimento": pct,
                "status": status,
            }
        )

    # Ordenar: maior faturamento primeiro
    resultado.sort(key=lambda x: x["faturamento_real"], reverse=True)
    return resultado


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


# ---------------------------------------------------------------------------
# Tendencias Mensais — schemas e endpoint
# ---------------------------------------------------------------------------

class TendenciaMensal(BaseModel):
    """Um ponto de dados mensal para o grafico de tendencias."""
    mes: str              # Formato "YYYY-MM" ex.: "2025-01"
    faturamento: float    # SUM(valor_pedido) das vendas REAL/SINTETICO daquele mes
    vendas_qtd: int       # COUNT(id) das vendas daquele mes
    clientes_ativos: int  # COUNT(DISTINCT cnpj) com vendas naquele mes
    ticket_medio: float   # faturamento / vendas_qtd (0 quando sem vendas)


class TendenciasResponse(BaseModel):
    """Resposta com lista de tendencias mensais ordenadas por mes ASC."""
    meses: list[TendenciaMensal]


@router.get(
    "/tendencias",
    response_model=TendenciasResponse,
    summary="Tendencias mensais dos ultimos 12 meses",
)
def tendencias(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TendenciasResponse:
    """
    Retorna tendencias mensais de faturamento, volume de vendas e clientes
    ativos para os ultimos 12 meses completos.

    Regras (R1/R7/R8):
      - Apenas vendas com classificacao_3tier IN ('REAL', 'SINTETICO').
      - Registros ALUCINACAO sao excluidos.
      - Two-Base: somente tabela vendas (valor_pedido > 0 por constraint).
      - mes_referencia no formato "YYYY-MM" (ex.: "2026-03").

    Ordenacao: ASC por mes_referencia.
    Requer autenticacao JWT.
    """
    # Calcular os ultimos 12 meses a partir do mes atual (hoje)
    hoje = date.today()
    # Primeiro dia do mes atual
    primeiro_dia_mes_atual = hoje.replace(day=1)
    # Primeiro dia do mes 12 meses atras (inclusive)
    # Subtrair 11 meses (mantemos o mes atual + 11 anteriores = 12 total)
    mes_inicio = primeiro_dia_mes_atual
    for _ in range(11):
        mes_inicio = (mes_inicio - timedelta(days=1)).replace(day=1)

    # Gerar lista de strings "YYYY-MM" para os 12 meses
    meses_range: list[str] = []
    cursor = mes_inicio
    while cursor <= primeiro_dia_mes_atual:
        meses_range.append(cursor.strftime("%Y-%m"))
        # Avançar para o proximo mes
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    # Consulta agrupada por mes_referencia
    stmt = (
        select(
            Venda.mes_referencia,
            func.coalesce(func.sum(Venda.valor_pedido), 0.0).label("faturamento"),
            func.count(Venda.id).label("vendas_qtd"),
            func.count(func.distinct(Venda.cnpj)).label("clientes_ativos"),
        )
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.mes_referencia.in_(meses_range),
        )
        .group_by(Venda.mes_referencia)
        .order_by(Venda.mes_referencia.asc())
    )

    rows = db.execute(stmt).all()

    # Indexar resultados por mes para preencher meses sem dados com zeros
    dados_por_mes: dict[str, dict] = {
        r.mes_referencia: {
            "faturamento": float(r.faturamento),
            "vendas_qtd": int(r.vendas_qtd),
            "clientes_ativos": int(r.clientes_ativos),
        }
        for r in rows
    }

    # Montar lista completa com zeros para meses sem vendas
    resultado: list[TendenciaMensal] = []
    for mes in meses_range:
        d = dados_por_mes.get(mes, {"faturamento": 0.0, "vendas_qtd": 0, "clientes_ativos": 0})
        fat = round(d["faturamento"], 2)
        qtd = d["vendas_qtd"]
        ticket = round(fat / qtd, 2) if qtd > 0 else 0.0
        resultado.append(
            TendenciaMensal(
                mes=mes,
                faturamento=fat,
                vendas_qtd=qtd,
                clientes_ativos=d["clientes_ativos"],
                ticket_medio=ticket,
            )
        )

    return TendenciasResponse(meses=resultado)
