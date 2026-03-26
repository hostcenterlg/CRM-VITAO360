"""
CRM VITAO360 — Rotas /api/sinaleiro

Endpoints:
  GET  /api/sinaleiro/clientes       — distribuicao de sinaleiro dos clientes
  GET  /api/sinaleiro/redes          — penetracao por rede com sinaleiro
  POST /api/sinaleiro/recalcular     — recalcula sinaleiro + score em batch (admin only)

Todos os endpoints requerem autenticacao JWT (Bearer token).
O endpoint /recalcular exige role 'admin'.

R4 — Two-Base Architecture: nenhum valor monetario e calculado aqui;
     calcular_penetracao_rede retorna potencial e pct mas nao cria logs.
R8 — Registros classificados como ALUCINACAO sao excluidos do recalculo batch.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
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
