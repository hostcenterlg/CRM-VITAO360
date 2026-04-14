"""
CRM VITAO360 — Rotas /api/ia

Endpoints de Inteligência Artificial: briefing expandido, mensagens WhatsApp,
resumo semanal, score de churn e sugestão de produtos cross-sell.

Endpoints:
  GET  /api/ia/briefing/{cnpj}             — briefing pré-ligação expandido
  GET  /api/ia/mensagem-wa/{cnpj}          — mensagem WA automática por situação
  POST /api/ia/mensagem/{cnpj}             — rascunho de mensagem WhatsApp (objetivo livre)
  GET  /api/ia/resumo-semanal/{consultor}  — resumo executivo semanal do consultor
  GET  /api/ia/churn-risk/{cnpj}           — score de risco de churn
  GET  /api/ia/sugestao-produto/{cnpj}     — sugestão de cross-sell/up-sell

Comportamento sem ANTHROPIC_API_KEY configurada:
  - Retorna HTTP 200 com campo 'ia_configurada: false' e conteúdo via template local.
  - O CRM continua funcional — a IA é um recurso adicional, não um bloqueador.

Autenticação: todos os endpoints exigem JWT válido (Bearer token).
Autorização:  qualquer usuário autenticado (consultor, gerente, admin).

R5 — CNPJ: normalizado internamente no serviço.
R4 — Two-Base: o serviço lê vendas e logs em tabelas separadas.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import require_consultor_or_admin
from backend.app.database import get_db
from backend.app.models.usuario import Usuario
from backend.app.services.ia_service import ia_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ia", tags=["Inteligência Artificial"])


# ---------------------------------------------------------------------------
# Schemas Pydantic — Request
# ---------------------------------------------------------------------------

class MensagemWhatsAppInput(BaseModel):
    """Payload para geração de mensagem WhatsApp com objetivo livre."""

    objetivo: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description=(
            "Objetivo da mensagem. Ex.: 'reativar cliente após 60 dias sem compra', "
            "'apresentar nova linha de cereais', 'confirmar visita para amanhã'."
        ),
        examples=["reativar cliente após 60 dias sem compra"],
    )


# ---------------------------------------------------------------------------
# Schemas Pydantic — Response
# ---------------------------------------------------------------------------

class BriefingResponse(BaseModel):
    """Resposta do endpoint de briefing pré-ligação expandido."""

    cnpj: str
    nome_cliente: str
    briefing: str
    tokens_usados: int
    cached: bool
    ia_configurada: bool


class MensagemWhatsAppResponse(BaseModel):
    """Resposta do endpoint de geração de mensagem WhatsApp (objetivo livre)."""

    cnpj: str
    nome_cliente: str
    mensagem: str
    tokens_usados: int
    ia_configurada: bool


class MensagemWAAutomaticaResponse(BaseModel):
    """Resposta do endpoint de mensagem WA automática por situação."""

    cnpj: str
    nome_cliente: str
    mensagem: str
    tom: str
    contexto: str
    tokens_usados: int
    ia_configurada: bool


class MetricasSemanaisResponse(BaseModel):
    """Métricas brutas que alimentaram o resumo semanal."""

    total_carteira: int
    clientes_contactados_semana: int
    vendas_semana_qtd: int
    vendas_semana_volume: float
    clientes_em_risco: int
    followups_vencidos: int
    pipeline: dict
    top3_proxima_semana: list


class ResumoSemanalResponse(BaseModel):
    """Resposta do endpoint de resumo semanal do consultor."""

    consultor: str
    periodo: str
    resumo: str
    tokens_usados: int
    metricas: MetricasSemanaisResponse
    ia_configurada: bool


class ChurnRiskResponse(BaseModel):
    """Resposta do endpoint de score de risco de churn."""

    cnpj: str
    nome_cliente: str
    risco_pct: float
    nivel: str
    fatores: list
    recomendacao: str
    ia_configurada: bool


class ProdutoSugeridoItem(BaseModel):
    """Item individual da lista de produtos sugeridos."""

    id: int
    codigo: str
    nome: str
    categoria: str
    motivo: str
    preco_tabela: float


class SugestaoProdutoResponse(BaseModel):
    """Resposta do endpoint de sugestão de produtos cross-sell/up-sell."""

    cnpj: str
    nome_cliente: str
    produtos_sugeridos: list
    estrategia: str
    categorias_frequentes: list
    ia_configurada: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/briefing/{cnpj}",
    response_model=BriefingResponse,
    summary="Briefing pré-ligação expandido para um cliente",
    description=(
        "Gera um briefing completo com histórico de compras (últimas 5), último contato, "
        "score/prioridade/temperatura, sugestão de abordagem e script de venda sugerido. "
        "Se ANTHROPIC_API_KEY não estiver configurada, retorna briefing via template local "
        "com HTTP 200 (graceful degradation)."
    ),
)
async def get_briefing(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """
    Gera briefing pré-ligação expandido para o cliente identificado pelo CNPJ.

    O CNPJ pode ser enviado com ou sem formatação (pontos, barras, traços);
    é normalizado automaticamente para 14 dígitos.

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de briefing | cnpj=%s usuario=%s role=%s",
        cnpj,
        getattr(user, "email", user.id),
        user.role,
    )

    try:
        resultado: dict[str, Any] = await ia_service.gerar_briefing(cnpj=cnpj, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Erro inesperado ao gerar briefing | cnpj=%s: %s", cnpj, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar briefing — contate o administrador.",
        ) from exc

    return BriefingResponse(**resultado)


@router.get(
    "/mensagem-wa/{cnpj}",
    response_model=MensagemWAAutomaticaResponse,
    summary="Mensagem WhatsApp automática por situação do cliente",
    description=(
        "Gera mensagem WhatsApp personalizada baseada automaticamente na situação atual "
        "do cliente (ATIVO, INAT.REC, INAT.ANT, PROSPECT, EM_RISCO). "
        "Sem necessidade de informar objetivo — o sistema determina o tom adequado. "
        "Se ANTHROPIC_API_KEY não estiver configurada, usa template local por situação."
    ),
)
async def get_mensagem_wa_automatica(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> MensagemWAAutomaticaResponse:
    """
    Gera mensagem WhatsApp automática contextual baseada na situação do cliente.

    O CNPJ pode ser enviado formatado; é normalizado automaticamente.

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de mensagem WA automática | cnpj=%s usuario=%s",
        cnpj,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.gerar_mensagem_wa_automatica(
            cnpj=cnpj, db=db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Erro inesperado ao gerar mensagem WA | cnpj=%s: %s", cnpj, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar mensagem — contate o administrador.",
        ) from exc

    return MensagemWAAutomaticaResponse(**resultado)


@router.post(
    "/mensagem/{cnpj}",
    response_model=MensagemWhatsAppResponse,
    status_code=status.HTTP_200_OK,
    summary="Rascunho de mensagem WhatsApp com objetivo livre",
    description=(
        "Gera um rascunho de mensagem WhatsApp personalizada para o objetivo informado. "
        "O consultor pode editar antes de enviar. "
        "Se a chave ANTHROPIC_API_KEY não estiver configurada, retorna mensagem explicativa."
    ),
)
async def post_mensagem_whatsapp(
    cnpj: str,
    payload: MensagemWhatsAppInput,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> MensagemWhatsAppResponse:
    """
    Gera rascunho de mensagem WhatsApp orientada ao objetivo informado.

    O CNPJ pode ser enviado formatado; é normalizado automaticamente.
    O campo 'objetivo' define o contexto e tom da mensagem (mín. 5 caracteres).

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de mensagem WA | cnpj=%s objetivo=%.60s usuario=%s",
        cnpj,
        payload.objetivo,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.gerar_mensagem_whatsapp(
            cnpj=cnpj, objetivo=payload.objetivo, db=db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Erro inesperado ao gerar mensagem WA | cnpj=%s: %s", cnpj, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar mensagem — contate o administrador.",
        ) from exc

    return MensagemWhatsAppResponse(**resultado)


@router.get(
    "/resumo-semanal/{consultor}",
    response_model=ResumoSemanalResponse,
    summary="Resumo executivo semanal de um consultor",
    description=(
        "Agrega dados da semana corrente (últimos 7 dias) para o consultor informado: "
        "clientes contactados (log_interacoes), vendas realizadas, pipeline por estágio, "
        "top 3 clientes para focar, clientes em risco (VERMELHO/LARANJA) e follow-ups vencidos. "
        "Consultores válidos: MANU, LARISSA, DAIANE, JULIO."
    ),
)
async def get_resumo_semanal(
    consultor: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> ResumoSemanalResponse:
    """
    Gera resumo semanal de performance para o consultor informado.

    O nome do consultor é normalizado para UPPERCASE.
    Consultores reconhecidos pelo DE-PARA: MANU, LARISSA, DAIANE, JULIO.

    Se o consultor não tiver dados na base, retorna resumo com métricas zeradas.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de resumo semanal | consultor=%s usuario=%s role=%s",
        consultor,
        getattr(user, "email", user.id),
        user.role,
    )

    try:
        resultado: dict[str, Any] = await ia_service.gerar_resumo_semanal(
            consultor=consultor, db=db
        )
    except Exception as exc:
        logger.exception(
            "Erro inesperado ao gerar resumo semanal | consultor=%s: %s",
            consultor,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar resumo — contate o administrador.",
        ) from exc

    return ResumoSemanalResponse(
        consultor=resultado["consultor"],
        periodo=resultado["periodo"],
        resumo=resultado["resumo"],
        tokens_usados=resultado["tokens_usados"],
        metricas=MetricasSemanaisResponse(**resultado["metricas"]),
        ia_configurada=resultado["ia_configurada"],
    )


@router.get(
    "/churn-risk/{cnpj}",
    response_model=ChurnRiskResponse,
    summary="Score de risco de churn para um cliente",
    description=(
        "Calcula o percentual de risco de churn baseado em: dias sem compra vs ciclo médio, "
        "sinaleiro atual, temperatura, situação comercial e tendência de ticket. "
        "Retorna nível BAIXO/MEDIO/ALTO/CRITICO e lista de fatores de risco identificados. "
        "Se ANTHROPIC_API_KEY não estiver configurada, gera recomendação via template local."
    ),
)
async def get_churn_risk(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> ChurnRiskResponse:
    """
    Calcula o score de risco de churn para o cliente identificado pelo CNPJ.

    O CNPJ pode ser enviado formatado; é normalizado automaticamente.

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de churn risk | cnpj=%s usuario=%s",
        cnpj,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.calcular_churn_risk(
            cnpj=cnpj, db=db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Erro inesperado ao calcular churn risk | cnpj=%s: %s", cnpj, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao calcular risco de churn — contate o administrador.",
        ) from exc

    return ChurnRiskResponse(**resultado)


@router.get(
    "/sugestao-produto/{cnpj}",
    response_model=SugestaoProdutoResponse,
    summary="Sugestão de produtos cross-sell/up-sell para um cliente",
    description=(
        "Analisa o histórico de compras do cliente (venda_itens + produtos), "
        "identifica as categorias mais frequentes e sugere produtos complementares "
        "que o cliente ainda não comprou. "
        "Se ANTHROPIC_API_KEY não estiver configurada, gera estratégia via template local."
    ),
)
async def get_sugestao_produto(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> SugestaoProdutoResponse:
    """
    Gera sugestão de produtos para cross-sell/up-sell baseado no histórico de compras.

    O CNPJ pode ser enviado formatado; é normalizado automaticamente.

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de sugestão de produto | cnpj=%s usuario=%s",
        cnpj,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.sugerir_produtos(
            cnpj=cnpj, db=db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Erro inesperado ao gerar sugestão de produto | cnpj=%s: %s", cnpj, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar sugestão — contate o administrador.",
        ) from exc

    return SugestaoProdutoResponse(**resultado)
