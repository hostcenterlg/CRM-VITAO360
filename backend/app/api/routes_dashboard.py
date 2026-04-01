"""
CRM VITAO360 — Rotas /api/dashboard

Endpoints KPI para o painel gerencial:

  GET /api/dashboard/kpis          — indicadores principais
  GET /api/dashboard/distribuicao  — distribuicoes (sinaleiro, situacao, prioridade, consultor)
  GET /api/dashboard/top10         — top 10 clientes por faturamento
  GET /api/dashboard/projecao      — projecao: realizado vs meta por consultor
  GET /api/dashboard/funil         — pipeline por estagio de funil
  GET /api/dashboard/tendencias    — tendencias mensais dos ultimos 12 meses
  GET /api/dashboard/atividades    — contagens de log_interacoes por tipo, consultor e mes
  GET /api/dashboard/positivacao   — clientes que compraram em determinado mes/ano

Faturamento baseline: R$ 2.091.000 (CORRIGIDO 2026-03-23, R7).
Todos os valores monetarios sao Float; o frontend formata como R$.
Todos os endpoints requerem autenticacao JWT (Bearer token).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
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
    # Activity fields — sourced from log_interacoes (Two-Base: no monetary values)
    total_atividades: int       # COUNT(*) log_interacoes (all time)
    atividades_mes_atual: int   # COUNT(*) log_interacoes WHERE data_interacao in current month
    taxa_positivacao: float     # % clientes positivados no mes atual (vendas table only)


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

    # --- Activity counts (log_interacoes — Two-Base: zero monetary values) ---
    total_atividades = db.scalar(
        select(func.count()).select_from(LogInteracao)
    ) or 0

    hoje = date.today()
    mes_inicio_atual = hoje.replace(day=1)
    # Last day of current month: first day of next month minus 1 day
    if hoje.month == 12:
        mes_fim_atual = hoje.replace(year=hoje.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        mes_fim_atual = hoje.replace(month=hoje.month + 1, day=1) - timedelta(days=1)

    atividades_mes_atual = db.scalar(
        select(func.count())
        .select_from(LogInteracao)
        .where(
            func.date(LogInteracao.data_interacao) >= mes_inicio_atual,
            func.date(LogInteracao.data_interacao) <= mes_fim_atual,
        )
    ) or 0

    # --- Positivacao current month (vendas table only — Two-Base: R1) ---
    # Distinct CNPJs with at least one venda in the current month (non-ALUCINACAO)
    positivados_mes = db.scalar(
        select(func.count(func.distinct(Venda.cnpj)))
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            func.date(Venda.data_pedido) >= mes_inicio_atual,
            func.date(Venda.data_pedido) <= mes_fim_atual,
        )
    ) or 0

    # Total carteira excludes ALUCINACAO clients
    total_carteira = db.scalar(
        select(func.count())
        .select_from(Cliente)
        .where(Cliente.classificacao_3tier != "ALUCINACAO")
    ) or 0

    taxa_positivacao = round(positivados_mes / total_carteira * 100, 1) if total_carteira > 0 else 0.0

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
        total_atividades=total_atividades,
        atividades_mes_atual=atividades_mes_atual,
        taxa_positivacao=taxa_positivacao,
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


# ---------------------------------------------------------------------------
# Atividades — schemas e endpoint
# Two-Base: log_interacoes NEVER has monetary values (R1/R4)
# ---------------------------------------------------------------------------

class AtividadeTipoItem(BaseModel):
    tipo: str
    quantidade: int


class AtividadeConsultorItem(BaseModel):
    consultor: str
    quantidade: int
    tipos: dict[str, int]


class AtividadeMesItem(BaseModel):
    mes: str     # "YYYY-MM"
    quantidade: int


class AtividadeResultadoItem(BaseModel):
    resultado: str
    quantidade: int


class AtividadesResponse(BaseModel):
    total: int
    por_tipo: list[AtividadeTipoItem]
    por_resultado: list[AtividadeResultadoItem]
    por_consultor: list[AtividadeConsultorItem]
    por_mes: list[AtividadeMesItem]
    periodo: dict[str, str]  # {"inicio": "YYYY-MM-DD", "fim": "YYYY-MM-DD"}


@router.get(
    "/atividades",
    response_model=AtividadesResponse,
    summary="Contagens de atividades (log_interacoes) por tipo, consultor e mes",
)
def atividades(
    consultor: Optional[str] = Query(default=None, description="Filtrar por consultor (MANU, LARISSA, DAIANE, JULIO)"),
    data_inicio: Optional[date] = Query(default=None, description="Data inicial (YYYY-MM-DD, inclusive)"),
    data_fim: Optional[date] = Query(default=None, description="Data final (YYYY-MM-DD, inclusive)"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AtividadesResponse:
    """
    Retorna contagens de interacoes do log_interacoes agrupadas por:
      - tipo_contato (LIGACAO, WHATSAPP, VISITA, EMAIL, ...)
      - consultor com breakdown por tipo_contato
      - mes (formato YYYY-MM) para tendencia

    Two-Base: esta tabela nao contem valores R$ — apenas contagens de interacoes.
    Requer autenticacao JWT.
    """

    # Build shared WHERE clauses for optional filters
    def _base_filters():
        filters = []
        if consultor:
            filters.append(LogInteracao.consultor == consultor)
        if data_inicio:
            filters.append(func.date(LogInteracao.data_interacao) >= data_inicio)
        if data_fim:
            filters.append(func.date(LogInteracao.data_interacao) <= data_fim)
        return filters

    base_filters = _base_filters()

    # --- Total atividades ---
    total_atividades = db.scalar(
        select(func.count())
        .select_from(LogInteracao)
        .where(*base_filters)
    ) or 0

    # --- Por tipo_contato ---
    tipo_rows = db.execute(
        select(
            LogInteracao.tipo_contato,
            func.count().label("qt"),
        )
        .where(*base_filters)
        .group_by(LogInteracao.tipo_contato)
        .order_by(func.count().desc())
    ).all()

    por_tipo = [
        AtividadeTipoItem(tipo=r[0] or "NAO_INFORMADO", quantidade=r[1])
        for r in tipo_rows
    ]

    # --- Por resultado (VENDA, ORCAMENTO, etc.) ---
    resultado_rows = db.execute(
        select(
            LogInteracao.resultado,
            func.count().label("qt"),
        )
        .where(*base_filters)
        .group_by(LogInteracao.resultado)
        .order_by(func.count().desc())
    ).all()

    por_resultado = [
        AtividadeResultadoItem(resultado=r[0] or "NAO_INFORMADO", quantidade=r[1])
        for r in resultado_rows
    ]

    # --- Por consultor com breakdown de tipos ---
    # Step 1: all (consultor, tipo_contato, count) combinations
    consultor_tipo_rows = db.execute(
        select(
            LogInteracao.consultor,
            LogInteracao.tipo_contato,
            func.count().label("qt"),
        )
        .where(*base_filters)
        .group_by(LogInteracao.consultor, LogInteracao.tipo_contato)
        .order_by(LogInteracao.consultor, func.count().desc())
    ).all()

    # Step 2: aggregate into consultor buckets
    consultor_map: dict[str, dict] = {}
    for row in consultor_tipo_rows:
        cons = row[0] or "NAO_INFORMADO"
        tipo = row[1] or "NAO_INFORMADO"
        qt = row[2]
        if cons not in consultor_map:
            consultor_map[cons] = {"total": 0, "tipos": {}}
        consultor_map[cons]["total"] += qt
        consultor_map[cons]["tipos"][tipo] = qt

    por_consultor = [
        AtividadeConsultorItem(
            consultor=cons,
            quantidade=data["total"],
            tipos=data["tipos"],
        )
        for cons, data in sorted(
            consultor_map.items(), key=lambda x: x[1]["total"], reverse=True
        )
    ]

    # --- Por mes (YYYY-MM derived from data_interacao) ---
    # SQLite: strftime; PostgreSQL: to_char. Use func.strftime for portability
    # with SQLite dev db; for Postgres in prod the same call works via cast.
    mes_rows = db.execute(
        select(
            func.strftime("%Y-%m", LogInteracao.data_interacao).label("mes"),
            func.count().label("qt"),
        )
        .where(*base_filters)
        .group_by(func.strftime("%Y-%m", LogInteracao.data_interacao))
        .order_by(func.strftime("%Y-%m", LogInteracao.data_interacao).asc())
    ).all()

    por_mes = [
        AtividadeMesItem(mes=r[0] or "DESCONHECIDO", quantidade=r[1])
        for r in mes_rows
    ]

    # Build periodo dict
    periodo_dict = {
        "inicio": str(data_inicio) if data_inicio else "",
        "fim": str(data_fim) if data_fim else "",
    }

    return AtividadesResponse(
        total=total_atividades,
        por_tipo=por_tipo,
        por_resultado=por_resultado,
        por_consultor=por_consultor,
        por_mes=por_mes,
        periodo=periodo_dict,
    )


# ---------------------------------------------------------------------------
# Positivacao — schemas e endpoint
# Two-Base: positivacao usa APENAS a tabela vendas (R1/R4)
# ---------------------------------------------------------------------------

class PositivacaoSituacaoItem(BaseModel):
    situacao: str
    quantidade: int
    pct: float


class PositivacaoConsultorItem(BaseModel):
    consultor: str
    total_carteira: int
    positivados: int
    taxa: float


class PositivacaoResponse(BaseModel):
    periodo: str                              # "YYYY-MM"
    total_carteira: int
    positivados: int
    taxa_positivacao: float
    por_situacao: list[PositivacaoSituacaoItem]
    por_consultor: list[PositivacaoConsultorItem]


@router.get(
    "/positivacao",
    response_model=PositivacaoResponse,
    summary="Clientes positivados (ao menos 1 venda) em determinado mes/ano",
)
def positivacao(
    mes: int = Query(default=None, ge=1, le=12, description="Mes (1-12). Padrao: mes atual."),
    ano: int = Query(default=None, ge=2020, description="Ano (ex.: 2026). Padrao: ano atual."),
    consultor: Optional[str] = Query(default=None, description="Filtrar por consultor"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PositivacaoResponse:
    """
    Retorna positivacao para o periodo indicado.

    Positivacao: cliente com ao menos 1 venda no mes/ano selecionado.
    Two-Base: usa APENAS a tabela vendas (nunca log_interacoes).
    Exclui clientes com classificacao_3tier = 'ALUCINACAO' (R8).

    Requer autenticacao JWT.
    """
    hoje = date.today()
    mes_ref = mes if mes is not None else hoje.month
    ano_ref = ano if ano is not None else hoje.year

    periodo_str = f"{ano_ref:04d}-{mes_ref:02d}"

    # Date range for the requested month
    data_inicio_periodo = date(ano_ref, mes_ref, 1)
    if mes_ref == 12:
        data_fim_periodo = date(ano_ref + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim_periodo = date(ano_ref, mes_ref + 1, 1) - timedelta(days=1)

    # --- Total carteira (non-ALUCINACAO) ---
    carteira_q = (
        select(func.count())
        .select_from(Cliente)
        .where(Cliente.classificacao_3tier != "ALUCINACAO")
    )
    if consultor:
        carteira_q = carteira_q.where(Cliente.consultor == consultor)
    total_carteira = db.scalar(carteira_q) or 0

    # --- CNPJs positivados: distinct CNPJs with >= 1 venda in period ---
    positivados_q = (
        select(func.count(func.distinct(Venda.cnpj)))
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= data_inicio_periodo,
            Venda.data_pedido <= data_fim_periodo,
        )
    )
    if consultor:
        positivados_q = positivados_q.where(Venda.consultor == consultor)
    positivados = db.scalar(positivados_q) or 0

    taxa_positivacao = round(positivados / total_carteira * 100, 1) if total_carteira > 0 else 0.0

    # --- Breakdown por situacao do cliente ---
    # Join vendas <-> clientes to get situacao of positivated clients
    situacao_rows = db.execute(
        select(
            Cliente.situacao,
            func.count(func.distinct(Venda.cnpj)).label("qt"),
        )
        .join(Cliente, Venda.cnpj == Cliente.cnpj)
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= data_inicio_periodo,
            Venda.data_pedido <= data_fim_periodo,
            Cliente.classificacao_3tier != "ALUCINACAO",
        )
        .group_by(Cliente.situacao)
        .order_by(func.count(func.distinct(Venda.cnpj)).desc())
    ).all()

    por_situacao = [
        PositivacaoSituacaoItem(
            situacao=r[0] or "NAO_INFORMADO",
            quantidade=r[1],
            pct=round(r[1] / positivados * 100, 2) if positivados > 0 else 0.0,
        )
        for r in situacao_rows
    ]

    # --- Breakdown por consultor ---
    consultores_alvo = ["MANU", "LARISSA", "DAIANE", "JULIO"]
    # If a specific consultor is requested, restrict to that one
    if consultor:
        consultores_alvo = [consultor]

    por_consultor: list[PositivacaoConsultorItem] = []
    for cons in consultores_alvo:
        carteira_cons = db.scalar(
            select(func.count())
            .select_from(Cliente)
            .where(
                Cliente.consultor == cons,
                Cliente.classificacao_3tier != "ALUCINACAO",
            )
        ) or 0

        positivados_cons = db.scalar(
            select(func.count(func.distinct(Venda.cnpj)))
            .where(
                Venda.consultor == cons,
                Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
                Venda.data_pedido >= data_inicio_periodo,
                Venda.data_pedido <= data_fim_periodo,
            )
        ) or 0

        taxa_cons = round(positivados_cons / carteira_cons * 100, 1) if carteira_cons > 0 else 0.0

        por_consultor.append(
            PositivacaoConsultorItem(
                consultor=cons,
                total_carteira=carteira_cons,
                positivados=positivados_cons,
                taxa=taxa_cons,
            )
        )

    return PositivacaoResponse(
        periodo=periodo_str,
        total_carteira=total_carteira,
        positivados=positivados,
        taxa_positivacao=taxa_positivacao,
        por_situacao=por_situacao,
        por_consultor=por_consultor,
    )


# ---------------------------------------------------------------------------
# Churn — clientes que compraram no período anterior mas NÃO no atual
# Two-Base: APENAS tabela vendas (R1/R4)
# ---------------------------------------------------------------------------

class ChurnClienteItem(BaseModel):
    cnpj: str
    nome: Optional[str]
    ultimo_pedido: Optional[str]   # ISO date string
    faturamento_total: Optional[float]


class ChurnConsultorItem(BaseModel):
    consultor: str
    perdidos: int
    valor: float


class ChurnResponse(BaseModel):
    periodo: str                              # "YYYY-MM" (período atual analisado)
    clientes_perdidos: int
    valor_perdido: float
    por_consultor: list[ChurnConsultorItem]
    top_perdidos: list[ChurnClienteItem]


@router.get(
    "/churn",
    response_model=ChurnResponse,
    summary="Clientes que compraram no período anterior mas não no atual (churn)",
)
def churn(
    mes: Optional[int] = Query(default=None, ge=1, le=12, description="Mês atual (1-12). Padrão: mês atual."),
    ano: Optional[int] = Query(default=None, ge=2020, description="Ano atual (ex.: 2026). Padrão: ano atual."),
    consultor: Optional[str] = Query(default=None, description="Filtrar por consultor"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChurnResponse:
    """
    Identifica clientes que tiveram vendas no período ANTERIOR (mes-1/ano)
    mas NÃO tiveram nenhuma venda no período ATUAL (mes/ano).

    Interpretação: clientes que foram perdidos / deixaram de comprar.

    Two-Base: usa APENAS tabela vendas (R1). Exclui ALUCINACAO (R8).
    Requer autenticação JWT.
    """
    hoje = date.today()
    mes_atual = mes if mes is not None else hoje.month
    ano_atual = ano if ano is not None else hoje.year

    # --- Date ranges ---
    # Current period
    dt_atual_ini = date(ano_atual, mes_atual, 1)
    if mes_atual == 12:
        dt_atual_fim = date(ano_atual + 1, 1, 1) - timedelta(days=1)
    else:
        dt_atual_fim = date(ano_atual, mes_atual + 1, 1) - timedelta(days=1)

    # Previous period (one month back)
    if mes_atual == 1:
        mes_ant, ano_ant = 12, ano_atual - 1
    else:
        mes_ant, ano_ant = mes_atual - 1, ano_atual

    dt_ant_ini = date(ano_ant, mes_ant, 1)
    if mes_ant == 12:
        dt_ant_fim = date(ano_ant + 1, 1, 1) - timedelta(days=1)
    else:
        dt_ant_fim = date(ano_ant, mes_ant + 1, 1) - timedelta(days=1)

    periodo_str = f"{ano_atual:04d}-{mes_atual:02d}"

    # --- CNPJs that bought in the PREVIOUS period ---
    prev_q = (
        select(func.distinct(Venda.cnpj))
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_ant_ini,
            Venda.data_pedido <= dt_ant_fim,
        )
    )
    if consultor:
        prev_q = prev_q.where(Venda.consultor == consultor.upper())

    prev_cnpjs: set[str] = {row[0] for row in db.execute(prev_q).all()}

    # --- CNPJs that bought in the CURRENT period ---
    curr_q = (
        select(func.distinct(Venda.cnpj))
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_atual_ini,
            Venda.data_pedido <= dt_atual_fim,
        )
    )
    if consultor:
        curr_q = curr_q.where(Venda.consultor == consultor.upper())

    curr_cnpjs: set[str] = {row[0] for row in db.execute(curr_q).all()}

    # Churned = bought previously but NOT in current period
    churned_cnpjs: set[str] = prev_cnpjs - curr_cnpjs

    if not churned_cnpjs:
        return ChurnResponse(
            periodo=periodo_str,
            clientes_perdidos=0,
            valor_perdido=0.0,
            por_consultor=[],
            top_perdidos=[],
        )

    # --- Valor perdido: faturamento desses clientes no período anterior ---
    valor_rows = db.execute(
        select(
            Venda.cnpj,
            Venda.consultor,
            func.sum(Venda.valor_pedido).label("total"),
        )
        .where(
            Venda.cnpj.in_(churned_cnpjs),
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_ant_ini,
            Venda.data_pedido <= dt_ant_fim,
        )
        .group_by(Venda.cnpj, Venda.consultor)
        .order_by(func.sum(Venda.valor_pedido).desc())
    ).all()

    valor_total = round(sum(float(r.total or 0) for r in valor_rows), 2)

    # --- Por consultor ---
    consultor_map: dict[str, dict] = {}
    for r in valor_rows:
        cons = r.consultor or "NAO_INFORMADO"
        if cons not in consultor_map:
            consultor_map[cons] = {"perdidos": 0, "valor": 0.0}
        consultor_map[cons]["perdidos"] += 1
        consultor_map[cons]["valor"] += float(r.total or 0)

    por_consultor = [
        ChurnConsultorItem(
            consultor=cons,
            perdidos=data["perdidos"],
            valor=round(data["valor"], 2),
        )
        for cons, data in sorted(
            consultor_map.items(), key=lambda x: x[1]["valor"], reverse=True
        )
    ]

    # --- Top perdidos: join with clientes for name + last order date ---
    # Build a mapping cnpj -> (nome, data_ultimo_pedido, fat_total) from the query
    top_rows = db.execute(
        select(
            Venda.cnpj,
            Cliente.nome_fantasia,
            func.max(Venda.data_pedido).label("ultimo_pedido"),
            func.sum(Venda.valor_pedido).label("fat_total"),
        )
        .join(Cliente, Venda.cnpj == Cliente.cnpj, isouter=True)
        .where(
            Venda.cnpj.in_(churned_cnpjs),
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
        )
        .group_by(Venda.cnpj, Cliente.nome_fantasia)
        .order_by(func.sum(Venda.valor_pedido).desc())
        .limit(20)  # cap top list
    ).all()

    top_perdidos = [
        ChurnClienteItem(
            cnpj=r.cnpj,
            nome=r.nome_fantasia,
            ultimo_pedido=r.ultimo_pedido.isoformat() if r.ultimo_pedido else None,
            faturamento_total=round(float(r.fat_total or 0), 2),
        )
        for r in top_rows
    ]

    return ChurnResponse(
        periodo=periodo_str,
        clientes_perdidos=len(churned_cnpjs),
        valor_perdido=valor_total,
        por_consultor=por_consultor,
        top_perdidos=top_perdidos,
    )


# ---------------------------------------------------------------------------
# Reativação — clientes sem vendas nos 3 meses anteriores que voltaram a comprar
# Two-Base: APENAS tabela vendas (R1/R4)
# ---------------------------------------------------------------------------

class ReativacaoConsultorItem(BaseModel):
    consultor: str
    reativados: int
    valor: float


class ReativacaoResponse(BaseModel):
    periodo: str                              # "YYYY-MM"
    reativados: int
    valor_reativado: float
    por_consultor: list[ReativacaoConsultorItem]


@router.get(
    "/reativacao",
    response_model=ReativacaoResponse,
    summary="Clientes reativados: sem compra nos 3 meses anteriores e com venda no período atual",
)
def reativacao(
    mes: Optional[int] = Query(default=None, ge=1, le=12, description="Mês atual (1-12). Padrão: mês atual."),
    ano: Optional[int] = Query(default=None, ge=2020, description="Ano atual (ex.: 2026). Padrão: ano atual."),
    consultor: Optional[str] = Query(default=None, description="Filtrar por consultor"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReativacaoResponse:
    """
    Identifica clientes que NÃO tiveram vendas nos 3 meses anteriores ao período
    informado, mas SIM tiveram ao menos uma venda no período atual.

    Interpretação: clientes que foram reativados / voltaram a comprar.

    Two-Base: usa APENAS tabela vendas (R1). Exclui ALUCINACAO (R8).
    Requer autenticação JWT.
    """
    hoje = date.today()
    mes_atual = mes if mes is not None else hoje.month
    ano_atual = ano if ano is not None else hoje.year

    # --- Date ranges ---
    # Current period: mes/ano
    dt_atual_ini = date(ano_atual, mes_atual, 1)
    if mes_atual == 12:
        dt_atual_fim = date(ano_atual + 1, 1, 1) - timedelta(days=1)
    else:
        dt_atual_fim = date(ano_atual, mes_atual + 1, 1) - timedelta(days=1)

    # Silence period: 3 months before the current period
    # Calculate first day 3 months back
    cursor = dt_atual_ini
    for _ in range(3):
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    dt_silencio_ini = cursor
    # Last day of silence window = day before current period start
    dt_silencio_fim = dt_atual_ini - timedelta(days=1)

    periodo_str = f"{ano_atual:04d}-{mes_atual:02d}"

    # --- CNPJs that bought in the CURRENT period ---
    curr_q = (
        select(func.distinct(Venda.cnpj))
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_atual_ini,
            Venda.data_pedido <= dt_atual_fim,
        )
    )
    if consultor:
        curr_q = curr_q.where(Venda.consultor == consultor.upper())

    curr_cnpjs: set[str] = {row[0] for row in db.execute(curr_q).all()}

    if not curr_cnpjs:
        return ReativacaoResponse(
            periodo=periodo_str,
            reativados=0,
            valor_reativado=0.0,
            por_consultor=[],
        )

    # --- CNPJs that bought DURING the 3-month silence window ---
    silencio_q = (
        select(func.distinct(Venda.cnpj))
        .where(
            Venda.cnpj.in_(curr_cnpjs),
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_silencio_ini,
            Venda.data_pedido <= dt_silencio_fim,
        )
    )

    silencio_cnpjs: set[str] = {row[0] for row in db.execute(silencio_q).all()}

    # Reativados = bought in current period AND were silent in the previous 3 months
    reativados_cnpjs: set[str] = curr_cnpjs - silencio_cnpjs

    if not reativados_cnpjs:
        return ReativacaoResponse(
            periodo=periodo_str,
            reativados=0,
            valor_reativado=0.0,
            por_consultor=[],
        )

    # --- Valor reativado: faturamento no período atual ---
    valor_rows = db.execute(
        select(
            Venda.consultor,
            func.count(func.distinct(Venda.cnpj)).label("reativados"),
            func.sum(Venda.valor_pedido).label("valor"),
        )
        .where(
            Venda.cnpj.in_(reativados_cnpjs),
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_atual_ini,
            Venda.data_pedido <= dt_atual_fim,
        )
        .group_by(Venda.consultor)
        .order_by(func.sum(Venda.valor_pedido).desc())
    ).all()

    valor_total = round(sum(float(r.valor or 0) for r in valor_rows), 2)

    por_consultor = [
        ReativacaoConsultorItem(
            consultor=r.consultor or "NAO_INFORMADO",
            reativados=int(r.reativados),
            valor=round(float(r.valor or 0), 2),
        )
        for r in valor_rows
    ]

    return ReativacaoResponse(
        periodo=periodo_str,
        reativados=len(reativados_cnpjs),
        valor_reativado=valor_total,
        por_consultor=por_consultor,
    )


# ---------------------------------------------------------------------------
# Positivação por UF — taxa de positivação agrupada por estado
# Two-Base: APENAS tabela vendas para positivação (R1/R4)
# ---------------------------------------------------------------------------

class PositivacaoUFItem(BaseModel):
    uf: str
    total_carteira: int
    positivados: int
    taxa: float


class PositivacaoUFResponse(BaseModel):
    periodo: str                              # "YYYY-MM"
    por_uf: list[PositivacaoUFItem]


@router.get(
    "/positivacao-uf",
    response_model=PositivacaoUFResponse,
    summary="Positivação de clientes agrupada por UF (estado)",
)
def positivacao_uf(
    mes: Optional[int] = Query(default=None, ge=1, le=12, description="Mês (1-12). Padrão: mês atual."),
    ano: Optional[int] = Query(default=None, ge=2020, description="Ano (ex.: 2026). Padrão: ano atual."),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PositivacaoUFResponse:
    """
    Retorna a taxa de positivação de clientes agrupada por UF (estado).

    Para cada UF:
      - total_carteira: clientes não-ALUCINACAO com UF preenchida
      - positivados:    distintos CNPJs com ao menos 1 venda no período
      - taxa:           positivados / total_carteira * 100 (%)

    Two-Base: positivação calculada APENAS via tabela vendas (R1).
    Exclui ALUCINACAO (R8). Ordena por taxa decrescente.
    Requer autenticação JWT.
    """
    hoje = date.today()
    mes_ref = mes if mes is not None else hoje.month
    ano_ref = ano if ano is not None else hoje.year

    # Date range for the requested month
    dt_inicio = date(ano_ref, mes_ref, 1)
    if mes_ref == 12:
        dt_fim = date(ano_ref + 1, 1, 1) - timedelta(days=1)
    else:
        dt_fim = date(ano_ref, mes_ref + 1, 1) - timedelta(days=1)

    periodo_str = f"{ano_ref:04d}-{mes_ref:02d}"

    # --- Total carteira by UF (non-ALUCINACAO, UF not null) ---
    carteira_rows = db.execute(
        select(
            Cliente.uf,
            func.count().label("total"),
        )
        .where(
            Cliente.classificacao_3tier != "ALUCINACAO",
            Cliente.uf.isnot(None),
        )
        .group_by(Cliente.uf)
    ).all()

    # Build a dict uf -> total_carteira
    carteira_by_uf: dict[str, int] = {r.uf: int(r.total) for r in carteira_rows}

    # --- Positivados by UF: join vendas with clientes ---
    positiv_rows = db.execute(
        select(
            Cliente.uf,
            func.count(func.distinct(Venda.cnpj)).label("positivados"),
        )
        .join(Cliente, Venda.cnpj == Cliente.cnpj)
        .where(
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.data_pedido >= dt_inicio,
            Venda.data_pedido <= dt_fim,
            Cliente.classificacao_3tier != "ALUCINACAO",
            Cliente.uf.isnot(None),
        )
        .group_by(Cliente.uf)
    ).all()

    positiv_by_uf: dict[str, int] = {r.uf: int(r.positivados) for r in positiv_rows}

    # --- Build response: only UFs that exist in carteira ---
    resultado: list[PositivacaoUFItem] = []
    for uf_val, total in carteira_by_uf.items():
        posit = positiv_by_uf.get(uf_val, 0)
        taxa = round(posit / total * 100, 1) if total > 0 else 0.0
        resultado.append(
            PositivacaoUFItem(
                uf=uf_val,
                total_carteira=total,
                positivados=posit,
                taxa=taxa,
            )
        )

    # Sort by taxa descending, then uf ascending for tie-breaking
    resultado.sort(key=lambda x: (-x.taxa, x.uf))

    return PositivacaoUFResponse(
        periodo=periodo_str,
        por_uf=resultado,
    )
