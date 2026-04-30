"""
CRM VITAO360 — Rotas /api/inbox

Endpoints especializados para a pagina Inbox do CRM.
Diferencia-se de /api/whatsapp ao retornar conversas JA ENRIQUECIDAS
com dados Mercos (temperatura, curva_abc, ticket_medio, dias_sem_compra,
sinaleiro) via cruzamento telefone/numero -> tabela clientes.

Endpoints:
  GET  /api/inbox/conversas                  — lista conversas enriquecidas (ultimos N dias)
  GET  /api/inbox/conversas/{ticket_id}/mensagens — mensagens paginadas de um ticket
  POST /api/inbox/conversas/{ticket_id}/enviar    — envia mensagem via Deskrio (por ticket_id)

Diferenca vs /api/whatsapp/inbox:
  - Inclui campos: temperatura, curva_abc, ticket_medio, dias_sem_compra, sinaleiro,
    nome_fantasia, canal_id por conversa (sem segundo fetch no frontend).
  - Usa ticket_id para envio (novo padrao) ao inves de CNPJ (legado).

Multi-canal R12: filtra tickets cujo contato pertence a canal permitido do usuario.
R5 — CNPJ: 14 digitos, string, normalizado antes de qualquer operacao.
R4 — Two-Base: mensagens WA sao LOG (R$ 0.00). NUNCA valor monetario aqui.
R8 — Zero fabricacao: dados que nao existem no banco retornam None/null.
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_user_canal_ids,
    require_consultor_or_above,
)
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.usuario import Usuario
from backend.app.services.deskrio_service import deskrio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inbox", tags=["Inbox"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalizar_cnpj(cnpj: str) -> str:
    """R5: remove pontuacao e zero-pad para 14 digitos."""
    return re.sub(r"\D", "", str(cnpj)).zfill(14)


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class ConversaResponse(BaseModel):
    """
    Conversa Inbox enriquecida com dados Mercos.

    Combina dados do ticket Deskrio com dados da tabela clientes (Postgres)
    para exibir temperatura, curva_abc, ticket_medio, etc. diretamente
    na lista de conversas sem segundo fetch.
    """
    ticket_id: int
    status: str                             # "open", "closed", "pending", "unknown"
    contato_nome: str
    contato_numero: str
    cnpj: str | None = None                 # 14 digitos — R5
    ultima_mensagem: str
    hora: str | None = None                 # lastMessageDate ISO
    nao_lidas: int = 0
    aguardando_resposta: bool = False
    atendente_nome: str | None = None

    # Enriquecimento Mercos — pode ser None se cliente nao cadastrado localmente
    temperatura: str | None = None
    curva_abc: str | None = None
    ticket_medio: float | None = None
    dias_sem_compra: int | None = None
    sinaleiro: str | None = None
    nome_fantasia: str | None = None        # Nome comercial do cliente
    canal_id: int | None = None


class MensagemResponse(BaseModel):
    """Mensagem individual de um ticket Deskrio."""
    id: int | str | None = None
    body: str
    fromMe: bool                            # True = enviada pelo vendedor
    timestamp: str
    mediaType: str | None = None
    mediaUrl: str | None = None
    nomeContato: str | None = None          # Nome de quem enviou (se disponivel)


class EnviarMensagemRequest(BaseModel):
    """Payload para envio de mensagem por ticket_id."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Texto da mensagem a enviar.",
    )


class EnviarMensagemResponse(BaseModel):
    """Resultado do envio de mensagem."""
    enviado: bool
    mensagem_id: str | None = None
    erro: str | None = None


# ---------------------------------------------------------------------------
# Endpoint 1: GET /api/inbox/conversas
# ---------------------------------------------------------------------------

@router.get(
    "/conversas",
    response_model=list[ConversaResponse],
    summary="Lista conversas Deskrio enriquecidas com dados Mercos",
    description=(
        "Retorna os tickets Deskrio dos ultimos N dias (padrao 30, max 30 pela "
        "limitacao de 6 dias por chamada Deskrio — multiplas chamadas paginadas). "
        "Cada conversa ja vem enriquecida com temperatura, curva_abc, ticket_medio, "
        "dias_sem_compra e sinaleiro da tabela clientes (cruzamento por telefone). "
        "Multi-canal R12: filtra pelos canais permitidos do usuario. "
        "R5: CNPJ sempre 14 digitos string. "
        "R4: sem valores monetarios em log de mensagem. "
        "Graceful degradation: se Deskrio nao configurado, retorna lista vazia."
    ),
)
def listar_conversas(
    days: int = Query(7, ge=1, le=30, description="Quantos dias buscar (1-30)"),
    user: Usuario = Depends(require_consultor_or_above),
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> list[ConversaResponse]:
    """
    Lista conversas Deskrio enriquecidas com dados Mercos.

    Fluxo:
      1. Busca tickets Deskrio (respeitando limite de 6 dias por chamada)
      2. Pre-carrega mapa telefone -> (cnpj, canal_id, dados_mercos) do banco
      3. Para cada ticket, cruza numero do contato com o mapa
      4. Filtra multi-canal se user_canal_ids != None
      5. Inclui dados Mercos enriquecidos no response
      6. Ordena: abertos primeiro, depois por hora desc

    Multi-canal: admin (user_canal_ids=None) ve todos.
    Graceful: se Deskrio offline, retorna [].
    """
    logger.info(
        "GET /api/inbox/conversas | days=%d usuario=%s canal_ids=%s",
        days,
        getattr(user, "email", user.id),
        user_canal_ids,
    )

    if not deskrio_service.configurado:
        logger.info("Deskrio nao configurado — retornando lista vazia")
        return []

    # Multi-canal: usuario sem canal nao ve nada
    if user_canal_ids is not None and not user_canal_ids:
        return []

    # --- Buscar tickets Deskrio ---
    # A API Deskrio limita a 6 dias por chamada (ERR_DATE_LIMIT_OFF_1_WEEK).
    # deskrio_service.listar_tickets ja trunca automaticamente para 6 dias.
    hoje = date.today()
    inicio = hoje - timedelta(days=days)

    try:
        tickets_raw = deskrio_service.listar_tickets(
            data_inicio=inicio.isoformat(),
            data_fim=hoje.isoformat(),
        )
    except Exception:
        logger.exception("Erro ao listar tickets Deskrio | days=%d", days)
        return []

    if not tickets_raw:
        logger.info("Deskrio retornou 0 tickets | inicio=%s fim=%s", inicio, hoje)
        return []

    # --- Pre-carrega mapa telefone -> cliente (lookup por sufixo 11 digitos) ---
    rows = db.execute(
        select(
            Cliente.cnpj,
            Cliente.canal_id,
            Cliente.telefone,
            Cliente.temperatura,
            Cliente.curva_abc,
            # ticket_medio nao existe no modelo — usamos valor_ultimo_pedido como proxy.
            # Se n_compras > 0, podemos calcular faturamento_total / n_compras.
            Cliente.faturamento_total,
            Cliente.n_compras,
            Cliente.dias_sem_compra,
            Cliente.sinaleiro,
            Cliente.nome_fantasia,
        ).where(Cliente.telefone.isnot(None))
    ).all()

    # Mapa: sufixo_telefone -> dados do cliente
    _ClienteData = dict  # typing alias local
    tel_para_cliente: dict[str, _ClienteData] = {}

    for row in rows:
        (
            cnpj_c, canal_id_c, tel_c,
            temperatura_c, curva_abc_c, faturamento_c, n_compras_c,
            dias_sem_compra_c, sinaleiro_c, nome_fantasia_c,
        ) = row

        if not tel_c:
            continue
        tel_norm = re.sub(r"\D", "", str(tel_c))
        if not tel_norm:
            continue
        sufixo = tel_norm[-11:] if len(tel_norm) >= 11 else tel_norm

        # Calcular ticket_medio: faturamento_total / n_compras (R4: apenas VENDA)
        ticket_medio_c: float | None = None
        if faturamento_c and n_compras_c and n_compras_c > 0:
            ticket_medio_c = round(faturamento_c / n_compras_c, 2)

        if sufixo not in tel_para_cliente:
            tel_para_cliente[sufixo] = {
                "cnpj": _normalizar_cnpj(cnpj_c) if cnpj_c else None,
                "canal_id": canal_id_c,
                "temperatura": temperatura_c,
                "curva_abc": curva_abc_c,
                "ticket_medio": ticket_medio_c,
                "dias_sem_compra": dias_sem_compra_c,
                "sinaleiro": sinaleiro_c,
                "nome_fantasia": nome_fantasia_c,
            }

    # Multi-canal: telefones permitidos para o usuario (None = admin, sem filtro)
    telefones_permitidos: set[str] | None = None
    if user_canal_ids is not None:
        telefones_permitidos = {
            sufixo for sufixo, dados in tel_para_cliente.items()
            if dados["canal_id"] in user_canal_ids
        }

    # --- Montar response ---
    conversas: list[ConversaResponse] = []

    for t in tickets_raw:
        t_status = (t.get("status") or "").lower()

        contato_raw = t.get("contact") or {}
        contato_nome = (
            contato_raw.get("name") or ""
            if isinstance(contato_raw, dict) else ""
        )
        contato_numero = (
            contato_raw.get("number") or ""
            if isinstance(contato_raw, dict) else ""
        )

        # Sufixo do numero para cruzamento
        num_norm = re.sub(r"\D", "", str(contato_numero or ""))
        sufixo = (
            (num_norm[-11:] if len(num_norm) >= 11 else num_norm)
            if num_norm else ""
        )

        # Multi-canal: filtrar se fora do escopo
        if telefones_permitidos is not None:
            if not sufixo or sufixo not in telefones_permitidos:
                continue

        # Buscar dados do cliente pelo sufixo de telefone
        dados_cliente = tel_para_cliente.get(sufixo) if sufixo else None

        cnpj_ticket: str | None = dados_cliente["cnpj"] if dados_cliente else None

        # Atendente
        user_raw = t.get("user") or {}
        atendente_nome = (
            user_raw.get("name") or None
            if isinstance(user_raw, dict) else None
        )

        # Datas das mensagens
        ultima_msg_data = t.get("lastMessageDate") or None
        ultima_msg_cliente_data = t.get("lastMessageDateNotFromMe") or None

        # Flag aguardando resposta
        aguardando = False
        if ultima_msg_data and ultima_msg_cliente_data:
            aguardando = ultima_msg_cliente_data > ultima_msg_data

        ticket_id_val = t.get("id")
        if not ticket_id_val:
            continue

        conversas.append(
            ConversaResponse(
                ticket_id=int(ticket_id_val),
                status=t_status or "unknown",
                contato_nome=contato_nome,
                contato_numero=contato_numero,
                cnpj=cnpj_ticket,
                ultima_mensagem=t.get("lastMessage") or "",
                hora=ultima_msg_data,
                nao_lidas=int(t.get("unreadMessages") or 0),
                aguardando_resposta=aguardando,
                atendente_nome=atendente_nome,
                # Enriquecimento Mercos — None se cliente nao cadastrado
                temperatura=dados_cliente["temperatura"] if dados_cliente else None,
                curva_abc=dados_cliente["curva_abc"] if dados_cliente else None,
                ticket_medio=dados_cliente["ticket_medio"] if dados_cliente else None,
                dias_sem_compra=dados_cliente["dias_sem_compra"] if dados_cliente else None,
                sinaleiro=dados_cliente["sinaleiro"] if dados_cliente else None,
                nome_fantasia=dados_cliente["nome_fantasia"] if dados_cliente else None,
                canal_id=dados_cliente["canal_id"] if dados_cliente else None,
            )
        )

    # Ordenar: abertos/pending primeiro, depois por hora desc (mesmo padrao do whatsapp/inbox)
    _STATUS_PRIORITY = {"open": 0, "pending": 1}
    conversas.sort(key=lambda c: c.hora or "", reverse=True)
    conversas.sort(key=lambda c: _STATUS_PRIORITY.get(c.status, 2))

    logger.info(
        "GET /api/inbox/conversas OK | total=%d usuario=%s",
        len(conversas),
        getattr(user, "email", user.id),
    )
    return conversas


# ---------------------------------------------------------------------------
# Endpoint 2: GET /api/inbox/conversas/{ticket_id}/mensagens
# ---------------------------------------------------------------------------

@router.get(
    "/conversas/{ticket_id}/mensagens",
    response_model=list[MensagemResponse],
    summary="Mensagens de um ticket (paginadas)",
    description=(
        "Retorna mensagens de um ticket Deskrio especifico, paginadas. "
        "fromMe=True indica mensagem enviada pelo vendedor. "
        "Retorna lista vazia (sem 500) se ticket nao encontrado ou sem mensagens."
    ),
)
def mensagens_conversa(
    ticket_id: int,
    page: int = Query(1, ge=1, le=100, description="Pagina (1-based)"),
    user: Usuario = Depends(require_consultor_or_above),
) -> list[MensagemResponse]:
    """
    Retorna mensagens de um ticket Deskrio especifico.

    Graceful: retorna [] se Deskrio nao configurado ou ticket inexistente.
    """
    logger.info(
        "GET /api/inbox/conversas/%d/mensagens | page=%d usuario=%s",
        ticket_id,
        page,
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return []

    try:
        dados = deskrio_service.listar_mensagens(ticket_id, page=page)
    except Exception:
        logger.exception(
            "Erro ao listar mensagens | ticket_id=%d page=%d", ticket_id, page
        )
        return []

    mensagens_raw = dados.get("messages", []) if isinstance(dados, dict) else []

    result: list[MensagemResponse] = []
    for m in mensagens_raw:
        result.append(
            MensagemResponse(
                id=m.get("id"),
                body=m.get("body") or m.get("message") or "",
                fromMe=bool(m.get("fromMe")),
                timestamp=m.get("createdAt") or m.get("timestamp") or "",
                mediaType=m.get("mediaType"),
                mediaUrl=m.get("mediaUrl"),
                nomeContato=(
                    m.get("contact", {}).get("name")
                    if isinstance(m.get("contact"), dict) else None
                ),
            )
        )

    logger.info(
        "GET /api/inbox/conversas/%d/mensagens OK | count=%d page=%d",
        ticket_id,
        len(result),
        page,
    )
    return result


# ---------------------------------------------------------------------------
# Endpoint 3: POST /api/inbox/conversas/{ticket_id}/enviar
# ---------------------------------------------------------------------------

@router.post(
    "/conversas/{ticket_id}/enviar",
    response_model=EnviarMensagemResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Envia mensagem via Deskrio usando ticket_id",
    description=(
        "Envia mensagem de texto em um ticket Deskrio existente. "
        "Usa ticket_id (nao CNPJ) — diferente do legado /api/whatsapp/enviar. "
        "Retorna enviado=False com campo 'erro' em vez de HTTP 4xx/5xx para "
        "nao bloquear o CRM quando o envio falha. "
        "R4 — Two-Base: envio de WA e operacao de LOG (sem valor monetario)."
    ),
)
def enviar_mensagem(
    ticket_id: int,
    body: EnviarMensagemRequest,
    user: Usuario = Depends(require_consultor_or_above),
    db: Session = Depends(get_db),
) -> EnviarMensagemResponse:
    """
    Envia mensagem em um ticket Deskrio.

    Fluxo:
      1. Valida message (Pydantic min_length=1)
      2. Busca dados do ticket no Deskrio (obter_ticket)
      3. Extrai numero do contato do ticket
      4. Envia via deskrio_service.enviar_mensagem(numero, texto)
      5. Retorna resultado

    R4 — Two-Base: operacao de LOG, sem valor monetario.
    Graceful: retorna enviado=False + erro em vez de 500.
    """
    logger.info(
        "POST /api/inbox/conversas/%d/enviar | msg_len=%d usuario=%s",
        ticket_id,
        len(body.message),
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return EnviarMensagemResponse(
            enviado=False,
            erro="WhatsApp nao configurado — defina DESKRIO_API_TOKEN e DESKRIO_API_URL",
        )

    # Buscar dados do ticket para obter o numero do contato
    try:
        ticket_data = deskrio_service.obter_ticket(ticket_id)
    except Exception:
        logger.exception("Erro ao buscar ticket | ticket_id=%d", ticket_id)
        return EnviarMensagemResponse(
            enviado=False,
            erro=f"Erro ao buscar ticket {ticket_id}",
        )

    if ticket_data is None:
        return EnviarMensagemResponse(
            enviado=False,
            erro=f"Ticket {ticket_id} nao encontrado no Deskrio",
        )

    # Extrair numero do contato do ticket
    contato_raw = ticket_data.get("contact") or {}
    numero: str | None = None

    if isinstance(contato_raw, dict):
        numero = contato_raw.get("number")
    if not numero:
        numero = ticket_data.get("contactNumber") or ticket_data.get("number")

    if not numero:
        logger.warning(
            "Ticket %d sem numero de contato | ticket_keys=%s",
            ticket_id,
            list(ticket_data.keys()),
        )
        return EnviarMensagemResponse(
            enviado=False,
            erro=f"Ticket {ticket_id} nao tem numero de contato associado",
        )

    # Enviar mensagem
    try:
        resultado = deskrio_service.enviar_mensagem(numero, body.message)
    except Exception:
        logger.exception(
            "Erro ao enviar mensagem | ticket_id=%d numero=%s", ticket_id, numero
        )
        return EnviarMensagemResponse(
            enviado=False,
            erro="Falha ao enviar mensagem via Deskrio",
        )

    if resultado is None:
        return EnviarMensagemResponse(
            enviado=False,
            erro="Deskrio retornou resposta vazia ao enviar mensagem",
        )

    # Extrair ID da mensagem (estrutura varia por versao da API)
    mensagem_id: str | None = None
    for chave in ("id", "messageId", "message_id"):
        if isinstance(resultado, dict) and chave in resultado:
            mensagem_id = str(resultado[chave])
            break

    logger.info(
        "Mensagem enviada via inbox | ticket_id=%d numero=%s msg_id=%s usuario=%s",
        ticket_id,
        numero,
        mensagem_id,
        getattr(user, "email", user.id),
    )

    return EnviarMensagemResponse(
        enviado=True,
        mensagem_id=mensagem_id,
    )
