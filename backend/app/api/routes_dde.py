"""
CRM VITAO360 — Rotas /api/dde (Onda 4 — PAPA)

Endpoints:
  GET /api/dde/cliente/{cnpj}          — DDE cascata completa de um cliente
  GET /api/dde/consultor/{nome}        — Consolidado DDE por consultor (clientes elegíveis)
  GET /api/dde/canal/{canal_id}        — Consolidado DDE por canal (DIRETO/INDIRETO/FOOD_SERVICE)
  GET /api/dde/comparativo?cnpjs=...   — Comparativo lado a lado de N CNPJs (máx. 20)
  GET /api/dde/score/{cnpj}            — Score I9 + breakdown dos 9 indicadores

Canal scoping:
  - Canal inelegível → 422 com mensagem amigável
  - Cliente fora do escopo do user → 403
  - Canais elegíveis: DIRETO | INDIRETO | FOOD_SERVICE

Multi-canal RBAC:
  - get_user_canal_ids: None = admin (vê tudo); list[int] = restrito ao escopo
  - 403 se cliente.canal_id not in user_canal_ids (não-admin)

R5 — CNPJ: helper _normaliza_cnpj aplicado em todo input externo.
R8 — Zero alucinação: API retorna null para linhas PENDENTE/NULL.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_db,
    get_user_canal_ids,
    require_consultor_or_above,
)
from backend.app.models.canal import Canal
from backend.app.models.cliente import Cliente
from backend.app.schemas.dde import (
    DDEComparativoItem,
    DDEComparativoResponse,
    DDEScoreResponse,
    IndicadoresDDE,
    LinhaDREResponse,
    ResultadoDDEResponse,
)
from backend.app.services.dde_engine import (
    ResultadoDDE,
    calcula_dre_comercial,
    cliente_elegivel_dde,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dde", tags=["DDE"])

# Canais elegíveis para DDE (consistente com CANAIS_DDE em dde_engine.py)
_CANAIS_DDE = frozenset({"DIRETO", "INDIRETO", "FOOD_SERVICE"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normaliza_cnpj(val: str) -> str:
    """R5: 14 dígitos, string, zero-padded. Aceita formato com pontuação."""
    return re.sub(r"\D", "", str(val)).zfill(14)[:14]


def _ano_default(ano: Optional[int]) -> int:
    return ano if ano is not None else datetime.now().year


def _check_canal_e_scoping(
    cnpj: str,
    db: Session,
    user_canal_ids: list[int] | None,
) -> Cliente:
    """
    Valida cliente, multi-canal RBAC e elegibilidade DDE.

    1. Busca cliente pelo CNPJ normalizado → 404 se não encontrado
    2. Verifica multi-canal RBAC → 403 se fora do escopo
    3. Verifica elegibilidade DDE (canal in _CANAIS_DDE) → 422 se inelegível

    Returns: Cliente ORM object
    """
    cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj).first()
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente {cnpj} não encontrado")

    # Multi-canal RBAC: admin (None) vê tudo; demais checam lista de canal_ids
    if user_canal_ids is not None and cliente.canal_id not in user_canal_ids:
        raise HTTPException(
            status_code=403,
            detail="Cliente fora do escopo do seu canal",
        )

    # DDE elegibilidade por canal
    if not cliente_elegivel_dde(cliente):
        canal_nome = cliente.canal.nome if cliente.canal else "sem canal"
        raise HTTPException(
            status_code=422,
            detail=(
                f"DDE indisponível para canal '{canal_nome}'. "
                f"Disponível apenas para: {', '.join(sorted(_CANAIS_DDE))}"
            ),
        )

    return cliente


def _resultado_to_response(resultado: ResultadoDDE) -> ResultadoDDEResponse:
    """Converte ResultadoDDE (dataclass OSCAR) para Pydantic response."""
    linhas = [
        LinhaDREResponse(
            codigo=l.codigo,
            conta=l.conta,
            sinal=l.sinal,
            valor=float(l.valor) if l.valor is not None else None,
            pct_receita=l.pct_receita,
            fonte=l.fonte,
            classificacao=l.classificacao,
            fase=l.fase,
            observacao=l.observacao,
        )
        for l in resultado.linhas
    ]

    indicadores = IndicadoresDDE(
        I1=resultado.indicadores.get("I1"),
        I2=resultado.indicadores.get("I2"),
        I3=resultado.indicadores.get("I3"),
        I4=resultado.indicadores.get("I4"),
        I5=resultado.indicadores.get("I5"),
        I6=resultado.indicadores.get("I6"),
        I7=resultado.indicadores.get("I7"),
        I8=resultado.indicadores.get("I8"),
        I9=resultado.indicadores.get("I9"),
    )

    return ResultadoDDEResponse(
        cnpj=resultado.cnpj,
        ano=resultado.ano,
        linhas=linhas,
        indicadores=indicadores,
        veredito=resultado.veredito,
        veredito_descricao=resultado.veredito_descricao,
        fase_ativa=resultado.fase_ativa,
    )


def _resultado_to_comparativo_item(
    resultado: ResultadoDDE,
    razao_social: Optional[str] = None,
) -> DDEComparativoItem:
    """Extrai campos-chave de ResultadoDDE para DDEComparativoItem."""
    # L1 (Faturamento Bruto) — primeiro item da cascata
    l1_linha = next((l for l in resultado.linhas if l.codigo == "L1"), None)
    l21_linha = next((l for l in resultado.linhas if l.codigo == "L21"), None)

    receita_bruta = float(l1_linha.valor) if l1_linha and l1_linha.valor is not None else None
    margem_contrib = float(l21_linha.valor) if l21_linha and l21_linha.valor is not None else None

    return DDEComparativoItem(
        cnpj=resultado.cnpj,
        razao_social=razao_social,
        receita_bruta=receita_bruta,
        margem_contribuicao=margem_contrib,
        mc_pct=resultado.indicadores.get("I2"),
        score=resultado.indicadores.get("I9"),
        veredito=resultado.veredito,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/cliente/{cnpj}",
    response_model=ResultadoDDEResponse,
    summary="DDE cascata completa de um cliente",
    description=(
        "Calcula a cascata P&L L1..L21 + indicadores I1..I9 + veredito determinístico "
        "para o CNPJ informado. Requer canal elegível (DIRETO/INDIRETO/FOOD_SERVICE). "
        "Aceita CNPJ com ou sem pontuação."
    ),
)
def get_dde_cliente(
    cnpj: str,
    ano: Optional[int] = Query(default=None, description="Ano de referência (padrão: ano atual)"),
    user=Depends(require_consultor_or_above),
    user_canal_ids=Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> ResultadoDDEResponse:
    """DDE cascata completa de um cliente."""
    cnpj = _normaliza_cnpj(cnpj)
    ano = _ano_default(ano)

    _check_canal_e_scoping(cnpj, db, user_canal_ids)

    resultado = calcula_dre_comercial(cnpj, ano, db)
    return _resultado_to_response(resultado)


@router.get(
    "/consultor/{nome}",
    response_model=DDEComparativoResponse,
    summary="Consolidado DDE por consultor",
    description=(
        "Agrega DDE de todos os clientes elegíveis do consultor informado. "
        "Retorna lista DDEComparativoItem (1 por cliente). "
        "Consultor sem clientes elegíveis retorna items vazio."
    ),
)
def get_dde_consultor(
    nome: str,
    ano: Optional[int] = Query(default=None, description="Ano de referência (padrão: ano atual)"),
    user=Depends(require_consultor_or_above),
    user_canal_ids=Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> DDEComparativoResponse:
    """Consolidado DDE por consultor — agrega clientes elegíveis."""
    ano = _ano_default(ano)

    # Busca clientes do consultor com canal elegível
    query = (
        db.query(Cliente)
        .join(Canal, Cliente.canal_id == Canal.id)
        .filter(
            Cliente.consultor == nome.upper(),
            Canal.nome.in_(_CANAIS_DDE),
        )
    )

    # Multi-canal RBAC: admin vê tudo, demais filtram por canal_ids
    if user_canal_ids is not None:
        if not user_canal_ids:
            return DDEComparativoResponse(ano=ano, items=[])
        query = query.filter(Cliente.canal_id.in_(user_canal_ids))

    clientes = query.all()
    items: list[DDEComparativoItem] = []

    for cliente in clientes:
        try:
            resultado = calcula_dre_comercial(cliente.cnpj, ano, db)
            items.append(
                _resultado_to_comparativo_item(resultado, razao_social=cliente.razao_social)
            )
        except Exception:
            logger.exception(
                "DDE falhou para cnpj=%s no consolidado consultor=%s", cliente.cnpj, nome
            )
            # Inclui item com veredito SEM_DADOS em vez de quebrar toda a listagem
            items.append(
                DDEComparativoItem(
                    cnpj=cliente.cnpj,
                    razao_social=cliente.razao_social,
                    veredito="SEM_DADOS",
                )
            )

    return DDEComparativoResponse(ano=ano, items=items)


@router.get(
    "/canal/{canal_id}",
    response_model=DDEComparativoResponse,
    summary="Consolidado DDE por canal",
    description=(
        "Agrega DDE de todos os clientes do canal informado. "
        "Requer canal elegível (DIRETO/INDIRETO/FOOD_SERVICE) — 422 para canais não elegíveis. "
        "Usuário sem permissão para o canal → 403."
    ),
)
def get_dde_canal(
    canal_id: int,
    ano: Optional[int] = Query(default=None, description="Ano de referência (padrão: ano atual)"),
    user=Depends(require_consultor_or_above),
    user_canal_ids=Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> DDEComparativoResponse:
    """Consolidado DDE por canal (apenas DIRETO/INDIRETO/FOOD_SERVICE)."""
    ano = _ano_default(ano)

    # Verifica existência do canal
    canal = db.query(Canal).filter(Canal.id == canal_id).first()
    if not canal:
        raise HTTPException(status_code=404, detail=f"Canal {canal_id} não encontrado")

    # Verifica elegibilidade DDE do canal
    if canal.nome not in _CANAIS_DDE:
        raise HTTPException(
            status_code=422,
            detail=(
                f"DDE indisponível para canal '{canal.nome}'. "
                f"Disponível apenas para: {', '.join(sorted(_CANAIS_DDE))}"
            ),
        )

    # Multi-canal RBAC: verifica se user tem permissão para este canal
    if user_canal_ids is not None and canal_id not in user_canal_ids:
        raise HTTPException(
            status_code=403,
            detail="Canal fora do escopo do seu perfil",
        )

    clientes = db.query(Cliente).filter(Cliente.canal_id == canal_id).all()
    items: list[DDEComparativoItem] = []

    for cliente in clientes:
        try:
            resultado = calcula_dre_comercial(cliente.cnpj, ano, db)
            items.append(
                _resultado_to_comparativo_item(resultado, razao_social=cliente.razao_social)
            )
        except Exception:
            logger.exception(
                "DDE falhou para cnpj=%s no consolidado canal_id=%d", cliente.cnpj, canal_id
            )
            items.append(
                DDEComparativoItem(
                    cnpj=cliente.cnpj,
                    razao_social=cliente.razao_social,
                    veredito="SEM_DADOS",
                )
            )

    return DDEComparativoResponse(ano=ano, items=items)


@router.get(
    "/comparativo",
    response_model=DDEComparativoResponse,
    summary="Comparativo lado a lado de N CNPJs",
    description=(
        "Calcula DDE para uma lista CSV de CNPJs (máximo 20). "
        "CNPJs inelegíveis ou fora do escopo do user são silenciosamente ignorados. "
        "Aceita CNPJs com ou sem pontuação."
    ),
)
def get_dde_comparativo(
    cnpjs: str = Query(..., description="Lista CSV de CNPJs (máx. 20)"),
    ano: Optional[int] = Query(default=None, description="Ano de referência (padrão: ano atual)"),
    user=Depends(require_consultor_or_above),
    user_canal_ids=Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> DDEComparativoResponse:
    """Comparativo DDE de múltiplos CNPJs."""
    ano = _ano_default(ano)

    cnpj_list = [_normaliza_cnpj(c) for c in cnpjs.split(",") if c.strip()]
    if len(cnpj_list) > 20:
        raise HTTPException(status_code=400, detail="Máximo 20 CNPJs por comparativo")
    if not cnpj_list:
        raise HTTPException(status_code=400, detail="Informe ao menos 1 CNPJ")

    items: list[DDEComparativoItem] = []

    for cnpj in cnpj_list:
        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj).first()
        if not cliente:
            continue  # CNPJ inexistente — pular silenciosamente

        # Multi-canal RBAC — pular silenciosamente se fora do escopo
        if user_canal_ids is not None and cliente.canal_id not in user_canal_ids:
            continue

        # Canal não elegível — pular silenciosamente
        if not cliente_elegivel_dde(cliente):
            continue

        try:
            resultado = calcula_dre_comercial(cnpj, ano, db)
            items.append(
                _resultado_to_comparativo_item(resultado, razao_social=cliente.razao_social)
            )
        except Exception:
            logger.exception("DDE falhou para cnpj=%s no comparativo", cnpj)
            items.append(
                DDEComparativoItem(
                    cnpj=cnpj,
                    razao_social=cliente.razao_social,
                    veredito="SEM_DADOS",
                )
            )

    return DDEComparativoResponse(ano=ano, items=items)


@router.get(
    "/score/{cnpj}",
    response_model=DDEScoreResponse,
    summary="Score I9 + breakdown dos 9 indicadores",
    description=(
        "Retorna apenas o score I9 (0-100) e o breakdown completo I1..I9. "
        "Mais leve que o endpoint /cliente/{cnpj} para uso em listagens. "
        "Requer canal elegível."
    ),
)
def get_dde_score(
    cnpj: str,
    user=Depends(require_consultor_or_above),
    user_canal_ids=Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> DDEScoreResponse:
    """Score I9 + breakdown indicadores I1..I9."""
    cnpj = _normaliza_cnpj(cnpj)
    _check_canal_e_scoping(cnpj, db, user_canal_ids)

    ano = datetime.now().year
    resultado = calcula_dre_comercial(cnpj, ano, db)

    return DDEScoreResponse(
        cnpj=cnpj,
        score=resultado.indicadores.get("I9"),
        breakdown=resultado.indicadores,
        veredito=resultado.veredito,
    )


@router.post(
    "/cliente/{cnpj}/resumo-ceo",
    summary="Gera PDF 1 página do Resumo CEO",
    description=(
        "Gera PDF A4 1 página com análise executiva do cliente. "
        "Se ANTHROPIC_API_KEY ou outro provider LLM estiver configurado, "
        "usa LLM para gerar o texto; caso contrário, usa template determinístico. "
        "Valida valores R$ gerados contra dados reais do ResultadoDDE. "
        "Returns: application/pdf"
    ),
    response_class=None,
)
def gerar_resumo_ceo_endpoint(
    cnpj: str,
    ano: Optional[int] = Query(default=None, description="Ano de referência (padrão: ano atual)"),
    user=Depends(require_consultor_or_above),
    user_canal_ids=Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
):
    """Gera PDF 1 página do Resumo CEO. Returns: application/pdf."""
    from fastapi.responses import Response as FastAPIResponse
    from backend.app.services.resumo_ceo import gerar_resumo_ceo
    from backend.app.services.pdf_generator import gerar_pdf_resumo_ceo

    cnpj = _normaliza_cnpj(cnpj)
    ano = _ano_default(ano)

    cliente = _check_canal_e_scoping(cnpj, db, user_canal_ids)

    resultado = calcula_dre_comercial(cnpj, ano, db)
    resumo = gerar_resumo_ceo(resultado, cliente.razao_social or "")
    pdf_bytes = gerar_pdf_resumo_ceo(resumo["texto"], {
        "cnpj": cnpj,
        "ano": ano,
        "razao_social": cliente.razao_social or "",
        "veredito": resultado.veredito,
        "fonte": resumo["fonte"],
        "validacao": resumo["validacao"],
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="resumo_ceo_{cnpj}_{ano}.pdf"'
        },
    )
