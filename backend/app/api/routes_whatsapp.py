"""
CRM VITAO360 — Rotas /api/whatsapp

Endpoints de integracao com o Deskrio (plataforma WhatsApp Business da VITAO).

Endpoints:
  GET  /api/whatsapp/status           — status das conexoes WA (configurado/conectado)
  GET  /api/whatsapp/contato/{cnpj}   — busca contato Deskrio por CNPJ
  POST /api/whatsapp/enviar           — envia mensagem WA via Deskrio
  GET  /api/whatsapp/tickets          — tickets recentes de um cliente
  GET  /api/whatsapp/conexoes         — lista conexoes WA disponiveis

Comportamento sem configuracao:
  - Se DESKRIO_API_TOKEN / DESKRIO_API_URL ausentes, retorna HTTP 200 com
    campo 'configurado: false' (graceful degradation — nunca bloqueia o CRM).

Autenticacao: todos os endpoints exigem JWT valido (Bearer token).

R5  — CNPJ: normalizado para 14 digitos antes de qualquer busca.
R8  — Nenhum dado fabricado: se contato nao encontrado, retorna encontrado=false.
R10 — Two-Base: envio de mensagem WA e operacao de LOG (sem valor monetario).
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import require_consultor_or_admin
from backend.app.database import get_db
from backend.app.models.usuario import Usuario
from backend.app.services.deskrio_service import deskrio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalizar_cnpj(cnpj: str) -> str:
    """R5: remove pontuacao e zero-pad para 14 digitos."""
    return re.sub(r"\D", "", str(cnpj)).zfill(14)


# ---------------------------------------------------------------------------
# Schemas Pydantic — Requests
# ---------------------------------------------------------------------------

class EnviarWhatsAppInput(BaseModel):
    """Payload para envio de mensagem WhatsApp."""

    cnpj: str = Field(
        ...,
        description="CNPJ do cliente destinatario (qualquer formato).",
        examples=["12345678000100"],
    )
    mensagem: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Texto da mensagem a ser enviada.",
        examples=["Ola! Passando para verificar se posso ajudar com o pedido."],
    )


# ---------------------------------------------------------------------------
# Schemas Pydantic — Responses
# ---------------------------------------------------------------------------

class ConexaoWA(BaseModel):
    """Dados de uma conexao WhatsApp individual."""
    id: int | None = None
    nome: str
    status: str
    status_legivel: str


class WhatsAppStatusResponse(BaseModel):
    """Resposta do endpoint de status das conexoes WA."""
    configurado: bool
    conexoes: list[ConexaoWA]
    alguma_conectada: bool
    total_conexoes: int


class WhatsAppContatoResponse(BaseModel):
    """Resposta do endpoint de busca de contato por CNPJ."""
    encontrado: bool
    numero: str | None = None
    nome: str | None = None
    deskrio_id: int | None = None
    cnpj: str | None = None


class WhatsAppEnviarResponse(BaseModel):
    """Resposta do endpoint de envio de mensagem WA."""
    enviado: bool
    mensagem_id: str | None = None
    numero: str | None = None
    erro: str | None = None


class TicketWA(BaseModel):
    """Dados de um ticket de atendimento Deskrio."""
    id: int | None = None
    status: str | None = None
    criado_em: str | None = None
    atualizado_em: str | None = None
    contact_id: int | None = None


class WhatsAppTicketsResponse(BaseModel):
    """Resposta do endpoint de tickets."""
    cnpj: str | None = None
    numero: str | None = None
    total: int
    tickets: list[TicketWA]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/status",
    response_model=WhatsAppStatusResponse,
    summary="Status das conexoes WhatsApp (Deskrio)",
    description=(
        "Retorna se o Deskrio esta configurado e quais conexoes WA estao ativas. "
        "Se DESKRIO_API_TOKEN nao estiver no .env, retorna configurado=false sem erro."
    ),
)
def get_status(
    user: Usuario = Depends(require_consultor_or_admin),
) -> WhatsAppStatusResponse:
    """
    Retorna o status das conexoes WhatsApp via Deskrio.

    Requer autenticacao JWT.
    """
    logger.info(
        "GET /api/whatsapp/status | usuario=%s role=%s",
        getattr(user, "email", user.id),
        user.role,
    )

    status_data = deskrio_service.status_conexoes()

    return WhatsAppStatusResponse(
        configurado=status_data["configurado"],
        conexoes=[
            ConexaoWA(
                id=c.get("id"),
                nome=c.get("nome", "—"),
                status=c.get("status", "DISCONNECTED"),
                status_legivel=c.get("status_legivel", "desconhecido"),
            )
            for c in status_data.get("conexoes", [])
        ],
        alguma_conectada=status_data["alguma_conectada"],
        total_conexoes=status_data["total_conexoes"],
    )


@router.get(
    "/contato/{cnpj}",
    response_model=WhatsAppContatoResponse,
    summary="Busca contato Deskrio por CNPJ",
    description=(
        "Procura no Deskrio o contato cujo campo extra 'CNPJ' bate com o CNPJ "
        "informado. Retorna encontrado=false (sem erro 404) se nao encontrar, "
        "para que o frontend possa lidar graciosamente."
    ),
)
def get_contato_por_cnpj(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
) -> WhatsAppContatoResponse:
    """
    Busca contato WhatsApp associado ao CNPJ informado.

    O CNPJ pode ser enviado com ou sem formatacao; e normalizado (R5).
    Retorna encontrado=false se Deskrio nao estiver configurado ou contato
    nao existir — nunca levanta 404 para nao bloquear o fluxo do CRM.

    Requer autenticacao JWT.
    """
    cnpj_norm = _normalizar_cnpj(cnpj)

    logger.info(
        "GET /api/whatsapp/contato/%s | usuario=%s",
        cnpj_norm,
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return WhatsAppContatoResponse(
            encontrado=False,
            cnpj=cnpj_norm,
        )

    contato = deskrio_service.buscar_contato_por_cnpj(cnpj_norm)

    if contato is None:
        return WhatsAppContatoResponse(
            encontrado=False,
            cnpj=cnpj_norm,
        )

    return WhatsAppContatoResponse(
        encontrado=True,
        numero=contato.get("number"),
        nome=contato.get("name"),
        deskrio_id=contato.get("id"),
        cnpj=cnpj_norm,
    )


@router.post(
    "/enviar",
    response_model=WhatsAppEnviarResponse,
    status_code=status.HTTP_200_OK,
    summary="Envia mensagem WhatsApp via Deskrio",
    description=(
        "Localiza o numero de telefone do cliente pelo CNPJ no Deskrio e "
        "envia a mensagem via WhatsApp. "
        "Retorna enviado=false com campo 'erro' em vez de HTTP 4xx/5xx para "
        "nao bloquear o CRM quando o envio falha. "
        "R10 — Two-Base: envio de WA e operacao de LOG (sem valor monetario)."
    ),
)
def post_enviar(
    payload: EnviarWhatsAppInput,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> WhatsAppEnviarResponse:
    """
    Envia mensagem WhatsApp para o cliente identificado pelo CNPJ.

    Fluxo:
      1. Normaliza CNPJ (R5)
      2. Busca numero de telefone do contato no Deskrio
      3. Envia mensagem via API Deskrio
      4. Retorna resultado (enviado / erro)

    Requer autenticacao JWT.
    """
    cnpj_norm = _normalizar_cnpj(payload.cnpj)

    logger.info(
        "POST /api/whatsapp/enviar | cnpj=%s usuario=%s texto_len=%d",
        cnpj_norm,
        getattr(user, "email", user.id),
        len(payload.mensagem),
    )

    if not deskrio_service.configurado:
        return WhatsAppEnviarResponse(
            enviado=False,
            erro="WhatsApp nao configurado — defina DESKRIO_API_TOKEN e DESKRIO_API_URL no .env",
        )

    # Buscar numero de telefone do cliente no Deskrio
    contato = deskrio_service.buscar_contato_por_cnpj(cnpj_norm)
    if contato is None:
        return WhatsAppEnviarResponse(
            enviado=False,
            erro=f"Contato nao encontrado no Deskrio para CNPJ {cnpj_norm}",
        )

    numero = contato.get("number", "")
    if not numero:
        return WhatsAppEnviarResponse(
            enviado=False,
            erro=f"Contato Deskrio sem numero de telefone (CNPJ {cnpj_norm})",
        )

    # Enviar mensagem
    resultado = deskrio_service.enviar_mensagem(numero, payload.mensagem)

    if resultado is None:
        return WhatsAppEnviarResponse(
            enviado=False,
            numero=numero,
            erro="Falha ao enviar mensagem via Deskrio — verifique conexao e token",
        )

    # Extrair ID da mensagem da resposta (estrutura varia por versao da API)
    mensagem_id: str | None = None
    for chave in ("id", "messageId", "message_id"):
        if chave in resultado:
            mensagem_id = str(resultado[chave])
            break

    logger.info(
        "Mensagem WA enviada | cnpj=%s numero=%s id=%s",
        cnpj_norm,
        numero,
        mensagem_id,
    )

    return WhatsAppEnviarResponse(
        enviado=True,
        mensagem_id=mensagem_id,
        numero=numero,
    )


@router.get(
    "/tickets",
    response_model=WhatsAppTicketsResponse,
    summary="Tickets de atendimento recentes de um cliente",
    description=(
        "Retorna os tickets de atendimento Deskrio do cliente identificado pelo CNPJ "
        "nos ultimos N dias (padrao 7). Util para ver historico de contatos WA."
    ),
)
def get_tickets(
    cnpj: str = Query(..., description="CNPJ do cliente (qualquer formato)"),
    dias: int = Query(7, ge=1, le=90, description="Numero de dias para buscar (1-90)"),
    user: Usuario = Depends(require_consultor_or_admin),
) -> WhatsAppTicketsResponse:
    """
    Retorna tickets de atendimento Deskrio para um cliente.

    Fluxo:
      1. Busca o numero de telefone via CNPJ no Deskrio
      2. Lista tickets filtrados pelo numero no periodo informado

    Retorna lista vazia (sem erro) se cliente nao tiver contato no Deskrio
    ou se nao houver tickets no periodo.

    Requer autenticacao JWT.
    """
    cnpj_norm = _normalizar_cnpj(cnpj)

    logger.info(
        "GET /api/whatsapp/tickets | cnpj=%s dias=%d usuario=%s",
        cnpj_norm,
        dias,
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return WhatsAppTicketsResponse(
            cnpj=cnpj_norm,
            total=0,
            tickets=[],
        )

    # Calcular periodo
    hoje = date.today()
    inicio = hoje - timedelta(days=dias)

    # Buscar numero do contato
    contato = deskrio_service.buscar_contato_por_cnpj(cnpj_norm)
    numero = contato.get("number") if contato else None

    # Buscar tickets (filtrado por numero se disponivel)
    tickets_raw = deskrio_service.listar_tickets(
        data_inicio=inicio.isoformat(),
        data_fim=hoje.isoformat(),
        numero=numero,
    )

    tickets: list[TicketWA] = []
    for t in tickets_raw:
        tickets.append(
            TicketWA(
                id=t.get("id"),
                status=t.get("status"),
                criado_em=t.get("createdAt"),
                atualizado_em=t.get("updatedAt"),
                contact_id=t.get("contactId"),
            )
        )

    return WhatsAppTicketsResponse(
        cnpj=cnpj_norm,
        numero=numero,
        total=len(tickets),
        tickets=tickets,
    )


@router.get(
    "/conexoes",
    response_model=list[ConexaoWA],
    summary="Lista conexoes WhatsApp disponiveis",
    description=(
        "Retorna todas as conexoes WhatsApp configuradas no Deskrio "
        "com seus respectivos status (CONNECTED / DISCONNECTED)."
    ),
)
def get_conexoes(
    user: Usuario = Depends(require_consultor_or_admin),
) -> list[ConexaoWA]:
    """
    Lista conexoes WhatsApp da conta Deskrio.

    Retorna lista vazia se Deskrio nao estiver configurado.

    Requer autenticacao JWT.
    """
    logger.info(
        "GET /api/whatsapp/conexoes | usuario=%s",
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return []

    conexoes_raw = deskrio_service.listar_conexoes()

    return [
        ConexaoWA(
            id=c.get("id"),
            nome=c.get("name", "—"),
            status=str(c.get("status", "DISCONNECTED")).upper(),
            status_legivel=(
                "conectado" if str(c.get("status", "")).upper() == "CONNECTED"
                else "desconectado"
            ),
        )
        for c in conexoes_raw
    ]
