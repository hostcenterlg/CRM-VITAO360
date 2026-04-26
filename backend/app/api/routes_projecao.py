"""
CRM VITAO360 — Rotas /api/projecao

Endpoints de projecao anual com meta vs realizado:

  GET /api/projecao              — resumo + detalhamento por consultor
  GET /api/projecao/{consultor}  — evolucao mensal de um consultor especifico

Fonte preferencial: tabela vendas (dados reais Mercos/SAP).
Fallback: campo faturamento_total da tabela clientes (quando vendas vazia).

R4 — Two-Base Architecture:
  Somente registros tipo VENDA entram no calculo de faturamento.
  Registros LOG (log_interacoes) NUNCA sao somados aqui.

R7 — Faturamento baseline: R$ 2.091.000 (CORRIGIDO 2026-03-23).
R8 — Registros classificacao_3tier = ALUCINACAO sao excluidos do calculo.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.meta import Meta
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda

router = APIRouter(prefix="/api/projecao", tags=["Projecao"])

# Constantes de negocio (R7)
FATURAMENTO_BASELINE = 2_091_000.0
PROJECAO_2026 = 3_377_120.0
Q1_REAL = 459_465.0

# Consultores ativos (DE-PARA padrao do dominio)
CONSULTORES_ALVO = ["MANU", "LARISSA", "DAIANE", "JULIO"]


# ---------------------------------------------------------------------------
# Schemas de resposta
# ---------------------------------------------------------------------------

class ProjecaoResumo(BaseModel):
    """Resumo anual de faturamento vs metas."""

    faturamento_realizado: float
    baseline_2025: float
    projecao_2026: float
    meta_2026: float             # soma das metas SAP de todos os clientes
    q1_2026_real: float
    pct_projecao: float          # % do realizado sobre a projecao 2026
    fonte_dados: str             # "vendas" ou "clientes_fallback"


class ProjecaoConsultor(BaseModel):
    """Faturamento vs meta por consultor."""

    consultor: str
    faturamento: float
    meta: float
    pct_alcancado: float
    total_vendas: int            # numero de pedidos/registros


class ProjecaoResponse(BaseModel):
    resumo: ProjecaoResumo
    por_consultor: list[ProjecaoConsultor]


class MensalItem(BaseModel):
    """Realizado e meta em um mes especifico."""

    mes_referencia: str          # formato "AAAA-MM"
    faturamento: float
    meta: float
    total_vendas: int


class ProjecaoConsultorDetalhe(BaseModel):
    """Evolucao mensal de um consultor com meta vs realizado."""

    consultor: str
    faturamento_total: float
    meta_total: float
    pct_alcancado: float
    mensal: list[MensalItem]


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _faturamento_de_vendas(db: Session) -> tuple[float, bool]:
    """
    Soma o faturamento da tabela vendas (REAL ou SINTETICO, nunca ALUCINACAO).

    Retorna (total, usou_vendas):
      - usou_vendas=True  → tabela vendas tinha registros, valor confivel
      - usou_vendas=False → tabela vendas vazia, necessario usar fallback
    """
    # R8: excluir ALUCINACAO
    total = db.scalar(
        select(func.coalesce(func.sum(Venda.valor_pedido), 0.0))
        .where(Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]))
    ) or 0.0

    usou_vendas = total > 0.0
    return float(total), usou_vendas


def _faturamento_fallback_clientes(db: Session) -> float:
    """
    Fallback: soma faturamento_total da tabela clientes quando vendas esta vazia.
    R8: exclui ALUCINACAO.
    """
    total = db.scalar(
        select(func.coalesce(func.sum(Cliente.faturamento_total), 0.0))
        .where(Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]))
    ) or 0.0
    return float(total)


def _faturamento_consultor_vendas(db: Session, consultor: str) -> tuple[float, int]:
    """
    Retorna (faturamento_total, total_pedidos) de um consultor via tabela vendas.
    R8: exclui ALUCINACAO.
    """
    resultado = db.execute(
        select(
            func.coalesce(func.sum(Venda.valor_pedido), 0.0).label("total"),
            func.count(Venda.id).label("qtd"),
        )
        .where(
            Venda.consultor == consultor,
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
        )
    ).first()

    total = float(resultado.total) if resultado else 0.0
    qtd = int(resultado.qtd) if resultado else 0
    return total, qtd


def _faturamento_consultor_fallback(db: Session, consultor: str) -> float:
    """
    Fallback: faturamento do consultor via clientes.faturamento_total.
    R8: exclui ALUCINACAO.
    """
    total = db.scalar(
        select(func.coalesce(func.sum(Cliente.faturamento_total), 0.0))
        .where(
            Cliente.consultor == consultor,
            Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]),
        )
    ) or 0.0
    return float(total)


def _meta_total_sap(db: Session) -> float:
    """
    Soma a meta_sap de todos os clientes na tabela metas (todos os periodos/consultores).

    Retorna PROJECAO_2026 como fallback se nenhuma meta estiver cadastrada,
    garantindo que o campo meta_2026 nunca seja zero.

    R8: nao filtra por classificacao_3tier pois Meta nao possui esse campo.
    """
    total = db.scalar(
        select(func.coalesce(func.sum(Meta.meta_sap), 0.0))
    ) or 0.0
    result = float(total)
    return result if result > 0.0 else PROJECAO_2026


def _meta_consultor(db: Session, consultor: str) -> float:
    """
    Soma a meta_sap de todos os periodos do consultor na tabela metas.
    Se nao houver registros, aplica fallback proporcional ao baseline.
    """
    total_meta = db.scalar(
        select(func.coalesce(func.sum(Meta.meta_sap), 0.0))
        .join(Cliente, Meta.cnpj == Cliente.cnpj)
        .where(Cliente.consultor == consultor)
    ) or 0.0

    if float(total_meta) == 0.0:
        # Fallback proporcional: distribui baseline igualmente entre os 4 consultores
        return FATURAMENTO_BASELINE / len(CONSULTORES_ALVO)

    return float(total_meta)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ProjecaoResponse,
    summary="Resumo de projecao anual + detalhamento por consultor",
)
def projecao_resumo(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjecaoResponse:
    """
    Consolida faturamento realizado vs projecao anual e meta por consultor.

    Fonte de dados:
      1. Tabela vendas (preferencial) — R8: exclui ALUCINACAO
      2. Fallback para clientes.faturamento_total se vendas estiver vazia

    Meta por consultor:
      1. Tabela metas (soma meta_sap por consultor via join com clientes)
      2. Fallback proporcional ao baseline R$ 2.091.000 se meta nao cadastrada

    Requer autenticacao JWT.
    """
    fat_total, usou_vendas = _faturamento_de_vendas(db)
    fonte_dados = "vendas"

    if not usou_vendas:
        fat_total = _faturamento_fallback_clientes(db)
        fonte_dados = "clientes_fallback"

    pct_projecao = round(fat_total / PROJECAO_2026 * 100, 1) if PROJECAO_2026 > 0 else 0.0

    # meta_2026: soma real das metas SAP cadastradas (fallback para PROJECAO_2026)
    meta_2026 = _meta_total_sap(db)

    por_consultor: list[ProjecaoConsultor] = []

    for consultor in CONSULTORES_ALVO:
        if usou_vendas:
            fat_c, total_vendas = _faturamento_consultor_vendas(db, consultor)
        else:
            fat_c = _faturamento_consultor_fallback(db, consultor)
            total_vendas = 0

        meta_c = _meta_consultor(db, consultor)
        pct = round(fat_c / meta_c * 100, 1) if meta_c > 0 else 0.0

        por_consultor.append(
            ProjecaoConsultor(
                consultor=consultor,
                faturamento=round(fat_c, 2),
                meta=round(meta_c, 2),
                pct_alcancado=pct,
                total_vendas=total_vendas,
            )
        )

    return ProjecaoResponse(
        resumo=ProjecaoResumo(
            faturamento_realizado=round(fat_total, 2),
            baseline_2025=FATURAMENTO_BASELINE,
            projecao_2026=PROJECAO_2026,
            meta_2026=round(meta_2026, 2),
            q1_2026_real=Q1_REAL,
            pct_projecao=pct_projecao,
            fonte_dados=fonte_dados,
        ),
        por_consultor=por_consultor,
    )


@router.get(
    "/{consultor}",
    response_model=ProjecaoConsultorDetalhe,
    summary="Evolucao mensal de um consultor (meta vs realizado)",
)
def projecao_consultor(
    consultor: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjecaoConsultorDetalhe:
    """
    Retorna a evolucao mensal de faturamento e meta de um consultor.

    Agrupamento por mes_referencia (formato "AAAA-MM").
    Meta mensal: soma de meta_sap dos clientes do consultor no periodo.
    Realizado: soma de valor_pedido da tabela vendas (R8: exclui ALUCINACAO).

    Multi-canal: consultor/consultor_externo so podem ver projecao propria
    (403 caso contrario). Admin/gerente veem qualquer.

    Consultores validos: MANU, LARISSA, DAIANE, JULIO.

    Requer autenticacao JWT.
    """
    consultor_upper = consultor.upper()

    # Carteira enforcement: consultor/_externo so ve a propria
    if user.role in ("consultor", "consultor_externo") and user.consultor_nome:
        if consultor_upper != user.consultor_nome.upper():
            raise HTTPException(
                status_code=403,
                detail="Acesso restrito a projecao propria",
            )

    if consultor_upper not in CONSULTORES_ALVO:
        raise HTTPException(
            status_code=404,
            detail=f"Consultor '{consultor_upper}' nao encontrado. Validos: {CONSULTORES_ALVO}",
        )

    # Faturamento mensal agrupado por mes_referencia
    rows_realizado = db.execute(
        select(
            Venda.mes_referencia,
            func.sum(Venda.valor_pedido).label("total"),
            func.count(Venda.id).label("qtd"),
        )
        .where(
            Venda.consultor == consultor_upper,
            Venda.classificacao_3tier.in_(["REAL", "SINTETICO"]),
            Venda.mes_referencia.isnot(None),
        )
        .group_by(Venda.mes_referencia)
        .order_by(Venda.mes_referencia)
    ).all()

    # Meta mensal — join metas com clientes para filtrar por consultor.
    # Fetch raw ano+mes integers and build "AAAA-MM" in Python to avoid
    # SQLite-specific func.printf that breaks on PostgreSQL.
    rows_meta = db.execute(
        select(
            Meta.ano,
            Meta.mes,
            func.sum(Meta.meta_sap).label("meta"),
        )
        .join(Cliente, Meta.cnpj == Cliente.cnpj)
        .where(Cliente.consultor == consultor_upper)
        .group_by(Meta.ano, Meta.mes)
        .order_by(Meta.ano, Meta.mes)
    ).all()

    # Montar dicionario de meta por mes para cruzamento (zero-pad in Python)
    meta_por_mes: dict[str, float] = {
        f"{r.ano}-{r.mes:02d}": float(r.meta) for r in rows_meta
    }

    mensal: list[MensalItem] = []
    for row in rows_realizado:
        mes_ref = row.mes_referencia or "DESCONHECIDO"
        meta_mes = meta_por_mes.get(mes_ref, 0.0)
        mensal.append(
            MensalItem(
                mes_referencia=mes_ref,
                faturamento=round(float(row.total), 2),
                meta=round(meta_mes, 2),
                total_vendas=int(row.qtd),
            )
        )

    fat_total = sum(m.faturamento for m in mensal)
    meta_total = _meta_consultor(db, consultor_upper)
    pct = round(fat_total / meta_total * 100, 1) if meta_total > 0 else 0.0

    return ProjecaoConsultorDetalhe(
        consultor=consultor_upper,
        faturamento_total=round(fat_total, 2),
        meta_total=round(meta_total, 2),
        pct_alcancado=pct,
        mensal=mensal,
    )
