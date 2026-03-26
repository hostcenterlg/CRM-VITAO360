"""
CRM VITAO360 — Rotas /api/redes

Endpoints:
  GET  /api/redes   — Lista todas as redes com indicadores de penetracao,
                      distribuicao de sinaleiro e lojas (clientes) associados.

Logica de montagem:
  - Fonte primaria: tabela `redes` (nome, total_lojas, lojas_ativas,
    faturamento_real, potencial_maximo, pct_penetracao, sinaleiro, cadencia).
  - Lojas individuais: clientes com tipo_cliente_sap LIKE '%REDES%' ou
    '%FRANQUIAS%' cujo rede_regional bate com o nome da rede.
  - Meta da rede: potencial_maximo (ja calculado no pipeline).
  - Gap: potencial_maximo - faturamento_real.
  - pct_ating: faturamento_real / potencial_maximo * 100 (0.0 se potencial=0).
  - Distribuicao sinaleiro: contagem de lojas (clientes) por cor.

R4 — Two-Base: nenhum log de interacao e mesclado aos valores financeiros.
R5 — CNPJ: String(14).
R8 — Exclui clientes classificados como ALUCINACAO.

Requer autenticacao JWT.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.rede import Rede
from backend.app.models.usuario import Usuario

router = APIRouter(prefix="/api/redes", tags=["Redes"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(numerador: float, denominador: float) -> float:
    """Percentual seguro: retorna 0.0 se denominador for zero."""
    if not denominador:
        return 0.0
    return round(numerador / denominador * 100, 1)


def _lojas_da_rede(db: Session, nome_rede: str) -> list[Cliente]:
    """
    Retorna clientes vinculados a uma rede pelo campo rede_regional.
    Exclui ALUCINACAO (R8).
    """
    return (
        db.query(Cliente)
        .filter(
            Cliente.rede_regional == nome_rede,
            Cliente.classificacao_3tier != "ALUCINACAO",
        )
        .order_by(Cliente.nome_fantasia)
        .all()
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "",
    summary="Listagem de redes com indicadores de penetracao e lojas",
)
def listar_redes(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Retorna todas as redes cadastradas com:
      - Indicadores financeiros (fat_real, potencial_maximo, pct, gap).
      - Distribuicao de sinaleiro das lojas ativas.
      - Lista de lojas (clientes) vinculadas.

    Ordenacao: maior faturamento_real primeiro.

    Requer autenticacao JWT.
    """
    redes: list[Rede] = (
        db.query(Rede).order_by(Rede.faturamento_real.desc()).all()
    )

    resultado: list[dict] = []

    for r in redes:
        lojas_clientes = _lojas_da_rede(db, r.nome)

        # Distribuicao de sinaleiro entre as lojas encontradas
        dist: dict[str, int] = {"VERDE": 0, "AMARELO": 0, "VERMELHO": 0, "ROXO": 0}
        for c in lojas_clientes:
            cor = (c.sinaleiro or "").upper()
            if cor in dist:
                dist[cor] += 1

        # Lojas individuais
        lojas = [
            {
                "cnpj": c.cnpj,
                "nome": c.nome_fantasia or c.razao_social or c.cnpj,
                "cidade": c.cidade or "",
                "uf": c.uf or "",
                "fat_real": round(c.faturamento_total or 0.0, 2),
                "meta": round(c.meta_anual or 0.0, 2),
                "pct_ating": _pct(
                    c.realizado_acumulado or c.faturamento_total or 0.0,
                    c.meta_anual or 0.0,
                ),
                "cor": c.sinaleiro or "SEM DADOS",
            }
            for c in lojas_clientes
        ]

        fat_real = round(r.faturamento_real or 0.0, 2)
        meta = round(r.potencial_maximo or 0.0, 2)
        pct_ating = _pct(fat_real, meta)
        gap = round(meta - fat_real, 2)

        resultado.append(
            {
                "nome": r.nome,
                "consultor": r.consultor_responsavel or "—",
                "total_lojas": r.total_lojas,
                "fat_real": fat_real,
                "meta": meta,
                "pct_ating": pct_ating,
                "gap": gap,
                "cor": r.sinaleiro or "SEM DADOS",
                "distribuicao": dist,
                "lojas": lojas,
            }
        )

    return {
        "total_redes": len(resultado),
        "total_lojas": sum(r["total_lojas"] for r in resultado),
        "redes": resultado,
    }
