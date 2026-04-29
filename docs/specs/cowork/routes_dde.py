"""
Routes DDE — Cascata P&L por Cliente
CRM VITAO360 · FastAPI

5 endpoints conforme SPEC_DDE_CASCATA_REAL.md seção 6.
Scoping multi-canal: herda get_user_canal_ids da Onda 1.

Copiar para: backend/app/api/routes_dde.py
Registrar em: backend/app/api/__init__.py → router.include_router(dde_router, prefix="/api/dde")
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, get_user_canal_ids  # Onda 1

# Engine imports
from app.services.dde_engine import (
    calcula_dre_efetivado,
    sinaleiro_sku,
    detecta_anomalias,
    persiste_dre,
)

dde_router = APIRouter(tags=["DDE - Análise P&L"])


# ============================================================
# HELPERS
# ============================================================

async def _valida_acesso_cnpj(db: AsyncSession, cnpj: str, canal_ids: list[int]) -> bool:
    """Verifica se o CNPJ pertence a um dos canais do usuário."""
    if not canal_ids:
        return True  # admin sem restrição
    sql = text("""
        SELECT 1 FROM clientes
        WHERE cnpj = :cnpj AND canal_id = ANY(:canais)
        LIMIT 1
    """)
    row = (await db.execute(sql, {"cnpj": cnpj, "canais": canal_ids})).first()
    return row is not None


async def _get_cnpjs_consultor(db: AsyncSession, nome: str, canal_ids: list[int]) -> list[str]:
    """Retorna CNPJs do consultor, filtrados por canal."""
    filtro_canal = "AND canal_id = ANY(:canais)" if canal_ids else ""
    sql = text(f"""
        SELECT DISTINCT cnpj FROM clientes
        WHERE consultor = :nome {filtro_canal}
    """)
    params: dict = {"nome": nome}
    if canal_ids:
        params["canais"] = canal_ids
    rows = (await db.execute(sql, params)).all()
    return [r[0] for r in rows]


async def _get_cnpjs_canal(db: AsyncSession, canal_id: int) -> list[str]:
    """Retorna CNPJs de um canal."""
    sql = text("SELECT DISTINCT cnpj FROM clientes WHERE canal_id = :canal_id")
    rows = (await db.execute(sql, {"canal_id": canal_id})).all()
    return [r[0] for r in rows]


# ============================================================
# ENDPOINT 1: DDE por Cliente
# GET /api/dde/cliente/{cnpj}?ano=2025&mes=3
# ============================================================

@dde_router.get("/cliente/{cnpj}")
async def get_dde_cliente(
    cnpj: str,
    ano: int = Query(default=2025, ge=2020, le=2030),
    mes: Optional[int] = Query(default=None, ge=1, le=12),
    persist: bool = Query(default=False, description="Salvar resultado no cache"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    canal_ids: list[int] = Depends(get_user_canal_ids),
):
    """
    Cascata P&L completa para um cliente.
    Retorna: dre (25 linhas), indicadores (I1-I9), veredito, fase_atual.
    """
    cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "").zfill(14)

    if not await _valida_acesso_cnpj(db, cnpj, canal_ids):
        raise HTTPException(403, "Sem acesso a este cliente no seu canal")

    resultado = await calcula_dre_efetivado(db, cnpj, ano, mes)

    if persist:
        await persiste_dre(db, resultado)

    return resultado.to_dict()


# ============================================================
# ENDPOINT 2: DDE Consolidado por Consultor
# GET /api/dde/consultor/{nome}?ano=2025
# ============================================================

@dde_router.get("/consultor/{nome}")
async def get_dde_consultor(
    nome: str,
    ano: int = Query(default=2025, ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    canal_ids: list[int] = Depends(get_user_canal_ids),
):
    """
    Consolidado DDE do consultor: soma das cascatas de todos os clientes dele.
    Inclui lista de clientes com veredito individual.
    """
    cnpjs = await _get_cnpjs_consultor(db, nome, canal_ids)
    if not cnpjs:
        raise HTTPException(404, f"Consultor '{nome}' não encontrado ou sem clientes no seu canal")

    clientes_dre = []
    totais = {}

    for cnpj in cnpjs:
        dre = await calcula_dre_efetivado(db, cnpj, ano)
        resumo = {
            "cnpj": cnpj,
            "veredito": dre.veredito[0] if dre.veredito else None,
        }
        for l in dre.linhas:
            resumo[l.linha] = float(l.valor_brl) if l.valor_brl is not None else None
            if l.valor_brl is not None:
                totais[l.linha] = totais.get(l.linha, 0) + float(l.valor_brl)
        clientes_dre.append(resumo)

    return {
        "consultor": nome,
        "ano": ano,
        "qtd_clientes": len(cnpjs),
        "totais": totais,
        "clientes": clientes_dre,
    }


# ============================================================
# ENDPOINT 3: DDE Consolidado por Canal
# GET /api/dde/canal/{canal_id}?ano=2025
# ============================================================

@dde_router.get("/canal/{canal_id}")
async def get_dde_canal(
    canal_id: int,
    ano: int = Query(default=2025, ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    canal_ids: list[int] = Depends(get_user_canal_ids),
):
    """Consolidado DDE por canal de venda."""
    if canal_ids and canal_id not in canal_ids:
        raise HTTPException(403, "Sem acesso a este canal")

    cnpjs = await _get_cnpjs_canal(db, canal_id)
    if not cnpjs:
        raise HTTPException(404, f"Canal {canal_id} sem clientes")

    totais = {}
    vereditos = {"SAUDAVEL": 0, "REVISAR": 0, "RENEGOCIAR": 0, "SUBSTITUIR": 0, "ALERTA_CREDITO": 0, "SEM_DADOS": 0}

    for cnpj in cnpjs:
        dre = await calcula_dre_efetivado(db, cnpj, ano)
        if dre.veredito:
            vereditos[dre.veredito[0]] = vereditos.get(dre.veredito[0], 0) + 1
        for l in dre.linhas:
            if l.valor_brl is not None:
                totais[l.linha] = totais.get(l.linha, 0) + float(l.valor_brl)

    return {
        "canal_id": canal_id,
        "ano": ano,
        "qtd_clientes": len(cnpjs),
        "totais": totais,
        "vereditos": vereditos,
    }


# ============================================================
# ENDPOINT 4: Comparativo cross-cliente
# GET /api/dde/comparativo?cnpjs=11111111000100,22222222000200&ano=2025
# ============================================================

@dde_router.get("/comparativo")
async def get_dde_comparativo(
    cnpjs: str = Query(..., description="CNPJs separados por vírgula (máx 10)"),
    ano: int = Query(default=2025, ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    canal_ids: list[int] = Depends(get_user_canal_ids),
):
    """
    Tabela lado a lado para comparação entre clientes.
    Máximo 10 CNPJs por request.
    """
    lista_cnpjs = [c.strip().replace(".", "").replace("/", "").replace("-", "").zfill(14)
                   for c in cnpjs.split(",")]

    if len(lista_cnpjs) > 10:
        raise HTTPException(400, "Máximo 10 CNPJs por comparativo")

    comparativo = []
    for cnpj in lista_cnpjs:
        if not await _valida_acesso_cnpj(db, cnpj, canal_ids):
            continue
        dre = await calcula_dre_efetivado(db, cnpj, ano)
        comparativo.append(dre.to_dict())

    return {
        "ano": ano,
        "clientes": comparativo,
    }


# ============================================================
# ENDPOINT 5: Score Saúde Financeira
# GET /api/dde/score/{cnpj}
# ============================================================

@dde_router.get("/score/{cnpj}")
async def get_dde_score(
    cnpj: str,
    ano: int = Query(default=2025, ge=2020, le=2030),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    canal_ids: list[int] = Depends(get_user_canal_ids),
):
    """
    Score I9 + breakdown de anomalias.
    Retorna: score, veredito, anomalias[], sinaleiro_sku[].
    """
    cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "").zfill(14)

    if not await _valida_acesso_cnpj(db, cnpj, canal_ids):
        raise HTTPException(403, "Sem acesso a este cliente no seu canal")

    dre = await calcula_dre_efetivado(db, cnpj, ano)
    anomalias = await detecta_anomalias(db, cnpj, ano)

    # Score simples: 100 - penalidades por anomalia
    score = 100
    for a in anomalias:
        if a["severidade"] == "CRITICA":
            score -= 30
        elif a["severidade"] == "ALTA":
            score -= 15
        elif a["severidade"] == "MEDIA":
            score -= 8
    score = max(0, score)

    # Sinaleiro SKU (pode ser lento — só retorna se existir mercado_sku_preco)
    try:
        skus = await sinaleiro_sku(db, cnpj, ano)
    except Exception:
        skus = []  # Tabela mercado_sku_preco pode não existir ainda

    return {
        "cnpj": cnpj,
        "ano": ano,
        "score_saude": score,
        "classificacao": _classifica_score(score),
        "veredito": {"status": dre.veredito[0], "motivo": dre.veredito[1]} if dre.veredito else None,
        "anomalias": anomalias,
        "sinaleiro_sku": skus[:20],  # Top 20 SKUs por volume
        "indicadores": dre.indicadores,
    }


def _classifica_score(score: int) -> str:
    if score >= 80:
        return "SAUDAVEL"
    if score >= 60:
        return "ATENCAO"
    if score >= 40:
        return "CRITICO"
    return "EMERGENCIAL"
