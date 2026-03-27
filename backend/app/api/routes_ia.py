"""
CRM VITAO360 — Rotas /api/ia

Endpoints de Inteligência Artificial: geração de briefings, mensagens WhatsApp
e resumos semanais usando o modelo Claude (Anthropic).

Endpoints:
  GET  /api/ia/briefing/{cnpj}          — briefing pré-ligação para um cliente
  POST /api/ia/mensagem/{cnpj}          — rascunho de mensagem WhatsApp
  GET  /api/ia/resumo-semanal/{consultor} — resumo executivo semanal do consultor

Comportamento sem ANTHROPIC_API_KEY configurada:
  - Retorna HTTP 200 com campo 'ia_configurada: false' e mensagem explicativa.
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
    """Payload para geração de mensagem WhatsApp."""

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
    """Resposta do endpoint de briefing pré-ligação."""

    cnpj: str
    nome_cliente: str
    briefing: str
    tokens_usados: int
    cached: bool
    ia_configurada: bool


class MensagemWhatsAppResponse(BaseModel):
    """Resposta do endpoint de geração de mensagem WhatsApp."""

    cnpj: str
    nome_cliente: str
    mensagem: str
    tokens_usados: int
    ia_configurada: bool


class MetricasSemanaisResponse(BaseModel):
    """Métricas brutas que alimentaram o resumo semanal."""

    total_carteira: int
    vendas_semana_qtd: int
    vendas_semana_volume: float
    clientes_em_risco: int
    followups_vencidos: int


class ResumoSemanalResponse(BaseModel):
    """Resposta do endpoint de resumo semanal do consultor."""

    consultor: str
    periodo: str
    resumo: str
    tokens_usados: int
    metricas: MetricasSemanaisResponse
    ia_configurada: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/briefing/{cnpj}",
    response_model=BriefingResponse,
    summary="Briefing pré-ligação para um cliente",
    description=(
        "Gera um briefing conciso (máximo 150 palavras) com situação comercial do cliente, "
        "histórico recente e ação recomendada para a ligação. "
        "Se a chave ANTHROPIC_API_KEY não estiver configurada, retorna mensagem explicativa "
        "com HTTP 200 (graceful degradation)."
    ),
)
async def get_briefing(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> BriefingResponse:
    """
    Gera briefing pré-ligação para o cliente identificado pelo CNPJ.

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


@router.post(
    "/mensagem/{cnpj}",
    response_model=MensagemWhatsAppResponse,
    status_code=status.HTTP_200_OK,
    summary="Rascunho de mensagem WhatsApp para um cliente",
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
        "vendas realizadas, clientes em risco (VERMELHO/LARANJA), follow-ups vencidos "
        "e top oportunidades por score. Gera texto executivo via Claude. "
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
