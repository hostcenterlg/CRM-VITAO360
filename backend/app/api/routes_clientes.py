"""
CRM VITAO360 — Rotas /api/clientes

Endpoints:
  GET /api/clientes         — lista com filtros + paginação
  GET /api/clientes/stats   — agregados (count por situação, consultor, sinaleiro)
  GET /api/clientes/{cnpj}  — detalhe de um cliente

Todos os filtros são opcionais e cumulativos.
Paginação padrão: limit=50, offset=0.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.cliente import Cliente

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])


# ---------------------------------------------------------------------------
# Schemas Pydantic (resposta)
# ---------------------------------------------------------------------------

class ClienteResumo(BaseModel):
    """Campos retornados na listagem — subconjunto leve."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    nome_fantasia: Optional[str]
    uf: Optional[str]
    cidade: Optional[str]
    consultor: Optional[str]
    situacao: Optional[str]
    temperatura: Optional[str]
    score: Optional[float]
    prioridade: Optional[str]
    sinaleiro: Optional[str]
    curva_abc: Optional[str]
    faturamento_total: Optional[float]
    tipo_cliente: Optional[str]
    fase: Optional[str]


class ClienteDetalhe(ClienteResumo):
    """Todos os campos — retornado no endpoint /{cnpj}."""

    razao_social: Optional[str]
    codigo_cliente: Optional[str]
    tipo_cliente_sap: Optional[str]
    macroregiao: Optional[str]
    dias_sem_compra: Optional[int]
    valor_ultimo_pedido: Optional[float]
    ciclo_medio: Optional[float]
    n_compras: Optional[int]
    tipo_contato: Optional[str]
    resultado: Optional[str]
    estagio_funil: Optional[str]
    acao_futura: Optional[str]
    followup_dias: Optional[int]
    grupo_dash: Optional[str]
    tipo_acao: Optional[str]
    tentativas: Optional[str]
    problema_aberto: Optional[bool]
    followup_vencido: Optional[bool]
    cs_no_prazo: Optional[bool]
    classificacao_3tier: Optional[str]
    # Projeção
    meta_anual: Optional[float]
    realizado_acumulado: Optional[float]
    pct_alcancado: Optional[float]
    gap_valor: Optional[float]
    status_meta: Optional[str]


class ListagemResponse(BaseModel):
    total: int
    limit: int
    offset: int
    registros: list[ClienteResumo]


class StatsDistribuicao(BaseModel):
    label: str
    quantidade: int


class StatsResponse(BaseModel):
    total_clientes: int
    por_situacao: list[StatsDistribuicao]
    por_consultor: list[StatsDistribuicao]
    por_sinaleiro: list[StatsDistribuicao]
    por_curva_abc: list[StatsDistribuicao]
    por_prioridade: list[StatsDistribuicao]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=ListagemResponse, summary="Listar clientes")
def listar_clientes(
    consultor: Optional[str] = Query(None, description="Filtrar por consultor (MANU/LARISSA/DAIANE/JULIO)"),
    situacao: Optional[str] = Query(None, description="Filtrar por situação (ATIVO/PROSPECT/INAT.REC/INAT.ANT)"),
    sinaleiro: Optional[str] = Query(None, description="Filtrar por sinaleiro (VERDE/AMARELO/VERMELHO/ROXO)"),
    curva_abc: Optional[str] = Query(None, description="Filtrar por curva ABC (A/B/C)"),
    temperatura: Optional[str] = Query(None, description="Filtrar por temperatura (QUENTE/MORNO/FRIO/CRITICO)"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade (P0–P7)"),
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex.: SP, RS, RJ)"),
    busca: Optional[str] = Query(None, description="Busca por nome fantasia ou razão social (contém)"),
    limit: int = Query(50, ge=1, le=500, description="Registros por página"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: Session = Depends(get_db),
) -> ListagemResponse:
    """
    Retorna lista paginada de clientes com filtros opcionais cumulativos.

    Todos os filtros são case-insensitive para strings de controle
    (consultor, situacao, sinaleiro, curva_abc, temperatura, prioridade).
    """
    stmt = select(Cliente)

    if consultor:
        stmt = stmt.where(Cliente.consultor == consultor.upper())
    if situacao:
        stmt = stmt.where(Cliente.situacao == situacao.upper())
    if sinaleiro:
        stmt = stmt.where(Cliente.sinaleiro == sinaleiro.upper())
    if curva_abc:
        stmt = stmt.where(Cliente.curva_abc == curva_abc.upper())
    if temperatura:
        stmt = stmt.where(Cliente.temperatura == temperatura.upper())
    if prioridade:
        stmt = stmt.where(Cliente.prioridade == prioridade.upper())
    if uf:
        stmt = stmt.where(Cliente.uf == uf.upper())
    if busca:
        termo = f"%{busca}%"
        stmt = stmt.where(
            Cliente.nome_fantasia.ilike(termo) | Cliente.razao_social.ilike(termo)
        )

    # Total antes da paginação
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    # Ordenação padrão: score desc para surfar os mais prioritários primeiro
    stmt = stmt.order_by(Cliente.score.desc().nulls_last(), Cliente.nome_fantasia)
    stmt = stmt.limit(limit).offset(offset)

    clientes = db.scalars(stmt).all()

    return ListagemResponse(
        total=total or 0,
        limit=limit,
        offset=offset,
        registros=[ClienteResumo.model_validate(c) for c in clientes],
    )


@router.get("/stats", response_model=StatsResponse, summary="Agregados por dimensão")
def stats_clientes(db: Session = Depends(get_db)) -> StatsResponse:
    """
    Retorna contagens agrupadas por situação, consultor, sinaleiro,
    curva ABC e prioridade.  Usado pelo dashboard de distribuição.
    """

    def _contar(coluna):
        rows = db.execute(
            select(coluna, func.count().label("qt"))
            .group_by(coluna)
            .order_by(func.count().desc())
        ).all()
        return [StatsDistribuicao(label=r[0] or "—", quantidade=r[1]) for r in rows]

    total = db.scalar(select(func.count()).select_from(Cliente))

    return StatsResponse(
        total_clientes=total or 0,
        por_situacao=_contar(Cliente.situacao),
        por_consultor=_contar(Cliente.consultor),
        por_sinaleiro=_contar(Cliente.sinaleiro),
        por_curva_abc=_contar(Cliente.curva_abc),
        por_prioridade=_contar(Cliente.prioridade),
    )


@router.get("/{cnpj}", response_model=ClienteDetalhe, summary="Detalhe de um cliente")
def detalhe_cliente(cnpj: str, db: Session = Depends(get_db)) -> ClienteDetalhe:
    """
    Retorna todos os campos de um cliente pelo seu CNPJ (14 dígitos, sem pontuação).
    Retorna 404 se o CNPJ não existir na base.
    """
    # Normalizar entrada: remover pontuação e zero-pad
    import re
    cnpj_normalizado = re.sub(r"\D", "", cnpj).zfill(14)

    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_normalizado))
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_normalizado} não encontrado.")

    return ClienteDetalhe.model_validate(cliente)
