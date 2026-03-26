"""
CRM VITAO360 — Rotas /api/clientes

Endpoints:
  GET /api/clientes               — lista com filtros + paginacao
  GET /api/clientes/stats         — agregados (count por situacao, consultor, sinaleiro)
  GET /api/clientes/{cnpj}        — detalhe de um cliente
  GET /api/clientes/{cnpj}/timeline — historico unificado (vendas + interacoes)

Todos os filtros sao opcionais e cumulativos.
Paginacao padrao: limit=50, offset=0.

Consultores com role='consultor' tem a carteira filtrada automaticamente
pelo proprio nome (consultor_nome do JWT). Admins veem todos.

Todos os endpoints requerem autenticacao JWT (Bearer token).
"""

from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda

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
    situacao: Optional[str] = Query(None, description="Filtrar por situacao (ATIVO/PROSPECT/INAT.REC/INAT.ANT)"),
    sinaleiro: Optional[str] = Query(None, description="Filtrar por sinaleiro (VERDE/AMARELO/VERMELHO/ROXO)"),
    curva_abc: Optional[str] = Query(None, description="Filtrar por curva ABC (A/B/C)"),
    temperatura: Optional[str] = Query(None, description="Filtrar por temperatura (QUENTE/MORNO/FRIO/CRITICO)"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade (P0-P7)"),
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex.: SP, RS, RJ)"),
    busca: Optional[str] = Query(None, description="Busca por nome fantasia ou razao social (contem)"),
    limit: int = Query(50, ge=1, le=500, description="Registros por pagina"),
    offset: int = Query(0, ge=0, description="Offset para paginacao"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListagemResponse:
    """
    Retorna lista paginada de clientes com filtros opcionais cumulativos.

    Todos os filtros sao case-insensitive para strings de controle
    (consultor, situacao, sinaleiro, curva_abc, temperatura, prioridade).

    Consultores com role='consultor' tem a carteira filtrada automaticamente
    pelo proprio consultor_nome; nao podem ver carteira alheia.
    Admins e viewers veem todos (sujeito ao filtro manual de consultor).

    Requer autenticacao JWT.
    """
    stmt = select(Cliente)

    # Filtro automatico por carteira para role=consultor
    if user.role == "consultor" and user.consultor_nome:
        stmt = stmt.where(Cliente.consultor == user.consultor_nome.upper())
    elif consultor:
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


@router.get("/stats", response_model=StatsResponse, summary="Agregados por dimensao")
def stats_clientes(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatsResponse:
    """
    Retorna contagens agrupadas por situacao, consultor, sinaleiro,
    curva ABC e prioridade. Usado pelo dashboard de distribuicao.

    Requer autenticacao JWT.
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
def detalhe_cliente(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClienteDetalhe:
    """
    Retorna todos os campos de um cliente pelo seu CNPJ (14 digitos, sem pontuacao).
    Retorna 404 se o CNPJ nao existir na base.

    Requer autenticacao JWT.
    """
    # R5: normalizar CNPJ — remover pontuacao e zero-pad para 14 digitos
    cnpj_normalizado = re.sub(r"\D", "", cnpj).zfill(14)

    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_normalizado))
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_normalizado} nao encontrado.")

    return ClienteDetalhe.model_validate(cliente)


@router.get(
    "/{cnpj}/score-history",
    summary="Evolucao do score ao longo do tempo",
)
def score_history(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna o historico de score de um cliente ordenado por data decrescente.

    Exibe os ultimos 30 calculos com score, prioridade, sinaleiro e todos os
    fatores de composicao para rastreabilidade e analise de tendencia.

    R5: CNPJ normalizado para 14 digitos antes da consulta.

    Requer autenticacao JWT.
    """
    from backend.app.models.score_historico import ScoreHistorico  # noqa: PLC0415

    cnpj_n = re.sub(r"\D", "", cnpj).zfill(14)

    historico = (
        db.query(ScoreHistorico)
        .filter(ScoreHistorico.cnpj == cnpj_n)
        .order_by(ScoreHistorico.data_calculo.desc())
        .limit(30)
        .all()
    )

    return [
        {
            "data": h.data_calculo.isoformat(),
            "score": h.score,
            "prioridade": h.prioridade,
            "sinaleiro": h.sinaleiro,
            "fator_fase": h.fator_fase,
            "fator_sinaleiro": h.fator_sinaleiro,
            "fator_curva": h.fator_curva,
            "fator_temperatura": h.fator_temperatura,
            "fator_tipo_cliente": h.fator_tipo_cliente,
            "fator_tentativas": h.fator_tentativas,
        }
        for h in historico
    ]


@router.get(
    "/{cnpj}/timeline",
    summary="Timeline unificada: vendas + interacoes de um cliente",
)
def timeline_cliente(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna a timeline unificada de um cliente ordenada por data decrescente.

    Combina dois tipos de evento:
      - VENDA: registros da tabela vendas (valor_pedido, data_pedido)
      - INTERACAO: registros de log_interacoes (resultado, descricao, temperatura)

    R4 — Two-Base Architecture: vendas e interacoes ficam em tabelas separadas.
    Esta rota apenas EXIBE os dois tipos juntos; nao mistura valores monetarios.
    R5: CNPJ normalizado para 14 digitos antes da consulta.

    Requer autenticacao JWT.
    """
    # R5: normalizar CNPJ
    cnpj_n = re.sub(r"\D", "", cnpj).zfill(14)

    # Verificar existencia do cliente (retorna 404 limpo)
    existe = db.scalar(select(func.count()).select_from(Cliente).where(Cliente.cnpj == cnpj_n))
    if not existe:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_n} nao encontrado.")

    vendas = db.query(Venda).filter(Venda.cnpj == cnpj_n).all()
    logs = db.query(LogInteracao).filter(LogInteracao.cnpj == cnpj_n).all()

    timeline: list[dict] = []

    for v in vendas:
        timeline.append({
            "tipo": "VENDA",
            "data": v.data_pedido.isoformat() if v.data_pedido else None,
            "valor": v.valor_pedido,
            "consultor": v.consultor,
            "descricao": f"Pedido {v.numero_pedido or ''} - R$ {v.valor_pedido:,.2f}".strip(),
            "fonte": v.fonte,
            "classificacao": v.classificacao_3tier,
        })

    for l in logs:
        timeline.append({
            "tipo": "INTERACAO",
            "data": l.data_interacao.isoformat() if l.data_interacao else None,
            "resultado": l.resultado,
            "consultor": l.consultor,
            "descricao": l.descricao or l.resultado,
            "fase": l.fase,
            "temperatura": l.temperatura,
            "estagio_funil": l.estagio_funil,
        })

    # Ordenar por data decrescente; eventos sem data ficam no fim
    timeline.sort(key=lambda x: x.get("data") or "", reverse=True)

    return timeline
