"""
CRM VITAO360 — Rotas /api/sinaleiro

Endpoints:
  GET  /api/sinaleiro                — lista clientes com sinaleiro (filtros opcionais)
  GET  /api/sinaleiro/clientes       — distribuicao agrupada de sinaleiro dos clientes
  GET  /api/sinaleiro/redes          — penetracao por rede com sinaleiro
  POST /api/sinaleiro/recalcular     — recalcula sinaleiro + score em batch (admin only)

Todos os endpoints requerem autenticacao JWT (Bearer token).
O endpoint /recalcular exige role 'admin'.

R4 — Two-Base Architecture: nenhum valor monetario e calculado aqui;
     calcular_penetracao_rede retorna potencial e pct mas nao cria logs.
R8 — Registros classificados como ALUCINACAO sao excluidos do recalculo batch.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.rede import Rede
from backend.app.models.usuario import Usuario
from backend.app.services.score_service import score_service
from backend.app.services.sinaleiro_service import sinaleiro_service

router = APIRouter(prefix="/api/sinaleiro", tags=["Sinaleiro"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_safe(num: float, den: float) -> float:
    return round(num / den * 100, 1) if den else 0.0


# ---------------------------------------------------------------------------
# GET / — lista de clientes com sinaleiro (endpoint principal da pagina Sinaleiro)
# ---------------------------------------------------------------------------

@router.get(
    "",
    summary="Lista clientes com sinaleiro, maturidade e acao recomendada",
)
def sinaleiro_lista(
    cor: Optional[str] = Query(None, description="Filtrar por cor: VERDE/AMARELO/LARANJA/VERMELHO/ROXO"),
    consultor: Optional[str] = Query(None, description="Filtrar por consultor (MANU/LARISSA/DAIANE/JULIO)"),
    rede: Optional[str] = Query(None, description="Filtrar por rede_regional"),
    limit: int = Query(100, ge=1, le=1000, description="Maximo de registros"),
    offset: int = Query(0, ge=0, description="Offset para paginacao"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Retorna lista de clientes enriquecida com dados de sinaleiro, maturidade
    e acao recomendada para a pagina de Sinaleiro de Carteira.

    Estrutura de resposta:
      - total: total de registros (sem paginacao)
      - resumo: distribuicao por cor [{cor, count, pct, faturamento}]
      - itens: lista de clientes [{cnpj, nome_fantasia, uf, consultor, rede,
                meta_anual, realizado, pct_atingimento, gap, cor, maturidade,
                acao_recomendada}]

    R8: exclui clientes classificados como ALUCINACAO.
    Requer autenticacao JWT.
    """
    # Base query — excluir ALUCINACAO (R8)
    base_q = db.query(Cliente).filter(
        Cliente.classificacao_3tier != "ALUCINACAO",
        Cliente.classificacao_3tier.isnot(None),
    )

    if cor:
        base_q = base_q.filter(Cliente.sinaleiro == cor.upper())
    if consultor:
        base_q = base_q.filter(Cliente.consultor == consultor.upper())
    if rede:
        base_q = base_q.filter(Cliente.rede_regional == rede)

    total = base_q.count()

    clientes = (
        base_q
        .order_by(Cliente.sinaleiro, Cliente.score.desc().nulls_last())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Resumo por cor (sobre o conjunto filtrado)
    resumo_rows = (
        db.query(
            Cliente.sinaleiro,
            func.count().label("qt"),
            func.coalesce(func.sum(Cliente.faturamento_total), 0.0).label("fat"),
        )
        .filter(
            Cliente.classificacao_3tier != "ALUCINACAO",
            Cliente.classificacao_3tier.isnot(None),
            *(
                [Cliente.consultor == consultor.upper()] if consultor else []
            ),
        )
        .group_by(Cliente.sinaleiro)
        .all()
    )

    total_geral = sum(r.qt for r in resumo_rows) or 1
    resumo = [
        {
            "cor": r.sinaleiro or "SEM DADOS",
            "count": r.qt,
            "pct": _pct_safe(r.qt, total_geral),
            "faturamento": round(float(r.fat), 2),
        }
        for r in resumo_rows
        if r.sinaleiro
    ]

    def _maturidade(c: Cliente) -> str:
        """Classifica maturidade do cliente baseado no ciclo de compras."""
        dias = c.dias_sem_compra or 0
        ciclo = c.ciclo_medio or 45
        if dias == 0:
            return "SEM HISTORICO"
        ratio = dias / ciclo if ciclo > 0 else 99
        if ratio <= 0.8:
            return "DENTRO DO CICLO"
        if ratio <= 1.2:
            return "NO LIMITE"
        if ratio <= 2.0:
            return "ATRASADO"
        return "MUITO ATRASADO"

    def _acao_recomendada(c: Cliente) -> str:
        """Acao prescrita baseada no sinaleiro e temperatura."""
        sinal = (c.sinaleiro or "").upper()
        temp = (c.temperatura or "").upper()
        if sinal == "VERMELHO":
            return "CONTATO URGENTE — risco de perda"
        if sinal == "ROXO":
            return "PROSPECTAR — sem historico de compra"
        if temp == "CRITICO":
            return "ESCALADA GERENCIAL — churn critico"
        if sinal == "AMARELO":
            return "FOLLOW UP — em alerta de ciclo"
        if sinal == "LARANJA":
            return "REATIVACAO — ciclo ultrapassado"
        return c.acao_futura or "MANUTENCAO — dentro do ciclo"

    itens = [
        {
            "cnpj": c.cnpj,
            "nome_fantasia": c.nome_fantasia or c.razao_social or c.cnpj,
            "uf": c.uf or "",
            "consultor": c.consultor or "—",
            "rede": c.rede_regional or "",
            "meta_anual": round(c.meta_anual or 0.0, 2),
            "realizado": round(c.realizado_acumulado or c.faturamento_total or 0.0, 2),
            "pct_atingimento": _pct_safe(
                c.realizado_acumulado or c.faturamento_total or 0.0,
                c.meta_anual or 0.0,
            ),
            "gap": round(
                (c.meta_anual or 0.0) - (c.realizado_acumulado or c.faturamento_total or 0.0),
                2,
            ),
            "cor": c.sinaleiro or "SEM DADOS",
            "maturidade": _maturidade(c),
            "acao_recomendada": _acao_recomendada(c),
        }
        for c in clientes
    ]

    return {"total": total, "resumo": resumo, "itens": itens}


@router.get(
    "/clientes",
    summary="Distribuicao de sinaleiro dos clientes",
)
def sinaleiro_clientes(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna a contagem de clientes agrupados por sinaleiro.

    Util para o painel de saude da carteira (VERDE/AMARELO/VERMELHO/ROXO).

    Requer autenticacao JWT.
    """
    rows = (
        db.query(Cliente.sinaleiro, func.count().label("total"))
        .group_by(Cliente.sinaleiro)
        .order_by(func.count().desc())
        .all()
    )
    return [
        {"sinaleiro": r.sinaleiro or "SEM DADOS", "total": r.total}
        for r in rows
    ]


@router.get(
    "/redes",
    summary="Penetracao por rede com sinaleiro e cadencia",
)
def sinaleiro_redes(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna todas as redes cadastradas com seus indicadores de penetracao,
    sinaleiro e cadencia recomendada de contato.

    Ordenado por pct_penetracao decrescente (redes mais penetradas primeiro).

    Requer autenticacao JWT.
    """
    redes = db.query(Rede).order_by(Rede.pct_penetracao.desc()).all()

    return [
        {
            "nome": r.nome,
            "total_lojas": r.total_lojas,
            "lojas_ativas": r.lojas_ativas,
            "faturamento_real": r.faturamento_real,
            "potencial_maximo": r.potencial_maximo,
            "pct_penetracao": r.pct_penetracao,
            "sinaleiro": r.sinaleiro,
            "cadencia": r.cadencia,
        }
        for r in redes
    ]


@router.post(
    "/recalcular",
    summary="Recalcula sinaleiro + score para todos os clientes (admin only)",
)
def recalcular_sinaleiro(
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """
    Recalcula sinaleiro e score para todos os clientes nao classificados
    como ALUCINACAO (R8 — nunca processar dados fabricados).

    Operacao em batch: flush e commit unico ao final para performance.
    Deve ser executado apos importacao de novos dados ou alteracao de
    parametros do motor.

    Requer autenticacao JWT com role 'admin'.

    Returns:
        Dict com: recalculados (int), mensagem (str).
    """
    # R8: excluir registros classificados como ALUCINACAO
    clientes = (
        db.query(Cliente)
        .filter(Cliente.classificacao_3tier != "ALUCINACAO")
        .all()
    )

    total = 0
    for c in clientes:
        sinaleiro_service.aplicar(db, c)
        score_service.aplicar_e_salvar(db, c)
        total += 1

    db.commit()

    return {
        "recalculados": total,
        "mensagem": f"Sinaleiro + Score recalculados para {total} clientes",
    }
