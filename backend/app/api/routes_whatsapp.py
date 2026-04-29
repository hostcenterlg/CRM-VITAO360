"""
CRM VITAO360 — Rotas /api/whatsapp

Endpoints de integracao com o Deskrio (plataforma WhatsApp Business da VITAO).

Endpoints:
  GET  /api/whatsapp/status           — status das conexoes WA (configurado/conectado)
  GET  /api/whatsapp/contato/{cnpj}   — busca contato Deskrio por CNPJ
  POST /api/whatsapp/enviar           — envia mensagem WA via Deskrio
  GET  /api/whatsapp/tickets          — tickets recentes de um cliente (por CNPJ)
  GET  /api/whatsapp/conexoes         — lista conexoes WA disponiveis
  GET  /api/whatsapp/inbox            — todos os tickets abertos/recentes (Inbox page)

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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_user_canal_ids,
    require_consultor_or_admin,
)
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
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


def _verificar_cnpj_no_escopo(
    db: Session,
    cnpj_norm: str,
    user_canal_ids: list[int] | None,
) -> None:
    """
    Multi-canal: verifica se o CNPJ pertence a um cliente cujo canal_id
    esta entre os canais permitidos do usuario.

    Para admin (user_canal_ids=None): nao bloqueia.
    Para usuario sem canais (lista vazia): 403.
    Para CNPJ inexistente no banco: nao bloqueia (deixa fluxo Deskrio
    decidir — pode haver contato sem cadastro local).
    Para CNPJ existente fora do escopo: 403.

    R5 — Cliente esta cadastrado com CNPJ 14 digitos string.
    """
    if user_canal_ids is None:
        return
    if not user_canal_ids:
        raise HTTPException(
            status_code=403,
            detail="Usuario sem canais autorizados",
        )
    canal_id_cliente = db.scalar(
        select(Cliente.canal_id).where(Cliente.cnpj == cnpj_norm)
    )
    if canal_id_cliente is None:
        # Cliente nao cadastrado: nao bloqueia (Deskrio pode ter contatos
        # sem cadastro local — manter comportamento gracioso atual)
        return
    if canal_id_cliente not in user_canal_ids:
        raise HTTPException(
            status_code=403,
            detail="Cliente fora do seu escopo de canais",
        )


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
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> WhatsAppContatoResponse:
    """
    Busca contato WhatsApp associado ao CNPJ informado.

    O CNPJ pode ser enviado com ou sem formatacao; e normalizado (R5).
    Retorna encontrado=false se Deskrio nao estiver configurado ou contato
    nao existir — nunca levanta 404 para nao bloquear o fluxo do CRM.

    Multi-canal: bloqueia (403) se o CNPJ pertencer a cliente fora do
    escopo de canais permitidos do usuario.

    Requer autenticacao JWT.
    """
    cnpj_norm = _normalizar_cnpj(cnpj)
    _verificar_cnpj_no_escopo(db, cnpj_norm, user_canal_ids)

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
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> WhatsAppEnviarResponse:
    """
    Envia mensagem WhatsApp para o cliente identificado pelo CNPJ.

    Fluxo:
      1. Normaliza CNPJ (R5)
      2. Verifica escopo de canais do usuario (403 se fora)
      3. Busca numero de telefone do contato no Deskrio
      4. Envia mensagem via API Deskrio
      5. Retorna resultado (enviado / erro)

    Multi-canal: 403 se CNPJ fora do escopo de canais permitidos.
    Requer autenticacao JWT.
    """
    cnpj_norm = _normalizar_cnpj(payload.cnpj)
    _verificar_cnpj_no_escopo(db, cnpj_norm, user_canal_ids)

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
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> WhatsAppTicketsResponse:
    """
    Retorna tickets de atendimento Deskrio para um cliente.

    Fluxo:
      1. Busca o numero de telefone via CNPJ no Deskrio
      2. Lista tickets filtrados pelo numero no periodo informado

    Retorna lista vazia (sem erro) se cliente nao tiver contato no Deskrio
    ou se nao houver tickets no periodo.

    Multi-canal: 403 se CNPJ fora do escopo de canais permitidos.
    Requer autenticacao JWT.
    """
    cnpj_norm = _normalizar_cnpj(cnpj)
    _verificar_cnpj_no_escopo(db, cnpj_norm, user_canal_ids)

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


# ---------------------------------------------------------------------------
# Schemas — Conversa real
# ---------------------------------------------------------------------------

class MensagemWA(BaseModel):
    """Uma mensagem individual do WhatsApp (Deskrio)."""
    id: int | str | None = None
    texto: str
    de_cliente: bool
    timestamp: str
    tipo: str = "chat"
    media_url: str | None = None
    nome_contato: str | None = None


class ContatoResumo(BaseModel):
    id: int | None = None
    nome: str | None = None
    numero: str | None = None


class TicketResumo(BaseModel):
    id: int | None = None
    status: str | None = None
    criado_em: str | None = None
    atualizado_em: str | None = None
    ultima_mensagem: str | None = None


class ConversaResponse(BaseModel):
    """Conversa WhatsApp completa de um cliente."""
    configurado: bool
    contato: ContatoResumo | None = None
    ticket: TicketResumo | None = None
    mensagens: list[MensagemWA]
    total: int


class MensagensTicketResponse(BaseModel):
    """Mensagens de um ticket especifico."""
    ticket_id: int
    mensagens: list[MensagemWA]
    total: int
    has_more: bool


# ---------------------------------------------------------------------------
# Endpoints — Conversa real (NOVOS — nao alteram os existentes)
# ---------------------------------------------------------------------------

@router.get(
    "/conversa/{cnpj}",
    response_model=ConversaResponse,
    summary="Conversa WhatsApp completa de um cliente",
    description=(
        "Busca o contato Deskrio pelo CNPJ, encontra o ticket mais recente "
        "(preferindo abertos), e retorna as mensagens reais do WhatsApp. "
        "Este e o endpoint principal para a Inbox mostrar conversas reais."
    ),
)
def get_conversa(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> ConversaResponse:
    """
    Retorna conversa WhatsApp real de um cliente.

    Fluxo: CNPJ -> contato Deskrio -> tickets -> mensagens do ticket.
    Retorna lista vazia (sem erro) se nao encontrar contato ou tickets.

    Multi-canal: 403 se CNPJ fora do escopo de canais permitidos.
    """
    cnpj_norm = _normalizar_cnpj(cnpj)
    _verificar_cnpj_no_escopo(db, cnpj_norm, user_canal_ids)

    logger.info(
        "GET /api/whatsapp/conversa/%s | usuario=%s",
        cnpj_norm,
        getattr(user, "email", user.id),
    )

    dados = deskrio_service.obter_conversa_completa(cnpj_norm)

    return ConversaResponse(
        configurado=dados["configurado"],
        contato=ContatoResumo(**dados["contato"]) if dados["contato"] else None,
        ticket=TicketResumo(**dados["ticket"]) if dados["ticket"] else None,
        mensagens=[MensagemWA(**m) for m in dados["mensagens"]],
        total=dados["total"],
    )


@router.get(
    "/mensagens/{ticket_id}",
    response_model=MensagensTicketResponse,
    summary="Mensagens de um ticket especifico",
    description=(
        "Retorna mensagens paginadas de um ticket Deskrio. "
        "Util para navegar tickets antigos ou carregar mais mensagens."
    ),
)
def get_mensagens_ticket(
    ticket_id: int,
    page: int = Query(1, ge=1, le=100, description="Pagina (1-based)"),
    user: Usuario = Depends(require_consultor_or_admin),
) -> MensagensTicketResponse:
    """
    Retorna mensagens de um ticket Deskrio especifico.
    """
    logger.info(
        "GET /api/whatsapp/mensagens/%d | page=%d usuario=%s",
        ticket_id,
        page,
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return MensagensTicketResponse(
            ticket_id=ticket_id,
            mensagens=[],
            total=0,
            has_more=False,
        )

    dados = deskrio_service.listar_mensagens(ticket_id, page=page)
    mensagens_raw = dados.get("messages", [])

    mensagens = [
        MensagemWA(
            id=m.get("id"),
            texto=m.get("body") or m.get("message") or "",
            de_cliente=not bool(m.get("fromMe")),
            timestamp=m.get("createdAt") or m.get("timestamp") or "",
            tipo=m.get("mediaType") or "chat",
            media_url=m.get("mediaUrl"),
            nome_contato=(
                m.get("contact", {}).get("name")
                if isinstance(m.get("contact"), dict) else None
            ),
        )
        for m in mensagens_raw
    ]

    return MensagensTicketResponse(
        ticket_id=ticket_id,
        mensagens=mensagens,
        total=dados.get("count", len(mensagens)),
        has_more=dados.get("hasMore", False),
    )


# ---------------------------------------------------------------------------
# Schemas — Inbox (todos os tickets)
# ---------------------------------------------------------------------------

class InboxTicketItem(BaseModel):
    """Um ticket da inbox do Deskrio, enriquecido para a pagina Inbox."""

    ticket_id: int
    status: str  # "open", "closed", "pending"
    contato_nome: str
    contato_numero: str
    cnpj: str | None = None                  # CNPJ do cliente (lookup por telefone)
    atendente_nome: str | None = None        # user.name do Deskrio
    ultima_mensagem: str                     # lastMessage (preview)
    ultima_mensagem_data: str | None = None  # lastMessageDate ISO
    ultima_msg_cliente_data: str | None = None  # lastMessageDateNotFromMe ISO
    mensagens_nao_lidas: int                 # unreadMessages
    origem: str | None = None               # "Receptivo", "Ativo", etc.
    aguardando_resposta: bool               # True = cliente enviou por ultimo


class InboxResponse(BaseModel):
    """Resposta do endpoint GET /api/whatsapp/inbox."""

    total: int
    tickets: list[InboxTicketItem]
    configurado: bool  # False se Deskrio nao estiver configurado


# ---------------------------------------------------------------------------
# Endpoint — Inbox
# ---------------------------------------------------------------------------

@router.get(
    "/inbox",
    response_model=InboxResponse,
    summary="Inbox de tickets WhatsApp (todos os atendimentos recentes)",
    description=(
        "Retorna todos os tickets Deskrio dos ultimos N dias (padrao 7), "
        "ordenados por lastMessageDate decrescente — abertos primeiro, depois fechados. "
        "Inclui flag 'aguardando_resposta' para identificar conversas em que o "
        "cliente enviou a ultima mensagem. "
        "Retorna configurado=false (sem erro) se Deskrio nao estiver configurado."
    ),
)
def get_inbox(
    dias: int = Query(7, ge=1, le=30, description="Quantos dias buscar (1-30)"),
    status_filtro: str | None = Query(
        None,
        alias="status",
        description="Filtrar por status: 'open', 'closed', ou omitir para todos",
    ),
    user: Usuario = Depends(require_consultor_or_admin),
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> InboxResponse:
    """
    Retorna inbox de todos os atendimentos WhatsApp recentes.

    Fluxo:
      1. Chama listar_tickets() para os ultimos N dias (sem filtro de numero)
      2. Filtra por status se informado
      3. Multi-canal: filtra tickets cujo numero pertenca a Cliente em
         canal permitido do usuario (admin: sem filtro)
      4. Calcula aguardando_resposta comparando datas das ultimas mensagens
      5. Ordena: abertos primeiro, depois por lastMessageDate desc

    Graceful degradation: se Deskrio nao estiver configurado, retorna lista
    vazia com configurado=false — nunca levanta excecao.

    Requer autenticacao JWT.
    """
    logger.info(
        "GET /api/whatsapp/inbox | dias=%d status=%s usuario=%s",
        dias,
        status_filtro,
        getattr(user, "email", user.id),
    )

    if not deskrio_service.configurado:
        return InboxResponse(total=0, tickets=[], configurado=False)

    # Multi-canal: usuario sem nenhum canal nao ve nenhum ticket
    if user_canal_ids is not None and not user_canal_ids:
        return InboxResponse(total=0, tickets=[], configurado=True)

    hoje = date.today()
    inicio = hoje - timedelta(days=dias)

    try:
        tickets_raw = deskrio_service.listar_tickets(
            data_inicio=inicio.isoformat(),
            data_fim=hoje.isoformat(),
        )
    except Exception:  # noqa: BLE001
        logger.exception("Erro ao listar tickets da inbox | dias=%d", dias)
        return InboxResponse(total=0, tickets=[], configurado=True)

    # Pre-carrega mapa telefone_normalizado (sufixo 11 digitos) -> (cnpj, canal_id)
    # para enriquecer cada ticket com o CNPJ do cliente (necessario para chamar
    # /api/whatsapp/enviar e /api/clientes/{cnpj} a partir do frontend).
    # Para multi-canal: tambem usa esse map para filtrar tickets fora do escopo.
    rows_clientes = db.execute(
        select(Cliente.cnpj, Cliente.canal_id, Cliente.telefone).where(
            Cliente.telefone.isnot(None),
        )
    ).all()
    telefone_para_cliente: dict[str, tuple[str, int | None]] = {}
    for row in rows_clientes:
        cnpj_cliente, canal_id_cliente, tel_cliente = row
        if not tel_cliente:
            continue
        tel_norm = re.sub(r"\D", "", str(tel_cliente))
        if not tel_norm:
            continue
        sufixo_tel = tel_norm[-11:] if len(tel_norm) >= 11 else tel_norm
        # Primeiro match ganha (caso de duplicatas raras de telefone)
        if sufixo_tel not in telefone_para_cliente:
            telefone_para_cliente[sufixo_tel] = (cnpj_cliente, canal_id_cliente)

    # Multi-canal: define quais sufixos de telefone estao no escopo do usuario.
    # Para admin (user_canal_ids=None): nao filtra (telefones_permitidos=None).
    telefones_permitidos: set[str] | None = None
    if user_canal_ids is not None:
        telefones_permitidos = {
            sufixo for sufixo, (_cnpj, canal_id) in telefone_para_cliente.items()
            if canal_id in user_canal_ids
        }

    items: list[InboxTicketItem] = []

    for t in tickets_raw:
        t_status = (t.get("status") or "").lower()

        # Aplicar filtro de status quando informado
        if status_filtro and t_status != status_filtro.lower():
            continue

        # --- Dados do contato ---
        contato_raw = t.get("contact") or {}
        contato_nome = (
            contato_raw.get("name") or ""
            if isinstance(contato_raw, dict) else ""
        )
        contato_numero = (
            contato_raw.get("number") or ""
            if isinstance(contato_raw, dict) else ""
        )

        # --- Lookup CNPJ pelo numero de telefone (sufixo 11 digitos) ---
        num_norm = re.sub(r"\D", "", str(contato_numero or ""))
        sufixo = (
            (num_norm[-11:] if len(num_norm) >= 11 else num_norm)
            if num_norm else ""
        )
        cnpj_ticket: str | None = None
        if sufixo and sufixo in telefone_para_cliente:
            cnpj_ticket = telefone_para_cliente[sufixo][0]

        # Multi-canal: filtrar tickets cujo numero nao bate com clientes
        # em canal permitido (admin: nao filtra).
        if telefones_permitidos is not None:
            if not sufixo or sufixo not in telefones_permitidos:
                continue

        # --- Dados do atendente ---
        user_raw = t.get("user") or {}
        atendente_nome = (
            user_raw.get("name") or None
            if isinstance(user_raw, dict) else None
        )

        # --- Datas das mensagens ---
        ultima_msg_data = t.get("lastMessageDate") or None
        ultima_msg_cliente_data = t.get("lastMessageDateNotFromMe") or None

        # --- Flag: aguardando resposta ---
        # True quando o cliente enviou a ultima mensagem (data do cliente > data geral)
        aguardando = False
        if ultima_msg_data and ultima_msg_cliente_data:
            # Comparacao lexicografica e segura para ISO 8601
            aguardando = ultima_msg_cliente_data > ultima_msg_data

        items.append(
            InboxTicketItem(
                ticket_id=t.get("id", 0),
                status=t_status or "unknown",
                contato_nome=contato_nome,
                contato_numero=contato_numero,
                cnpj=cnpj_ticket,
                atendente_nome=atendente_nome,
                ultima_mensagem=t.get("lastMessage") or "",
                ultima_mensagem_data=ultima_msg_data,
                ultima_msg_cliente_data=ultima_msg_cliente_data,
                mensagens_nao_lidas=int(t.get("unreadMessages") or 0),
                origem=t.get("origin") or None,
                aguardando_resposta=aguardando,
            )
        )

    # Ordenar: abertos/pendentes primeiro, depois por lastMessageDate desc.
    # Dois passes estaveis: primeiro por data desc (chave secundaria), depois
    # por prioridade de status asc (chave primaria). Python sort e estavel, entao
    # a ordem relativa dos itens com mesma prioridade e preservada da passada anterior.
    _STATUS_PRIORITY = {"open": 0, "pending": 1}

    items.sort(key=lambda i: i.ultima_mensagem_data or "", reverse=True)
    items.sort(key=lambda i: _STATUS_PRIORITY.get(i.status, 2))

    return InboxResponse(
        total=len(items),
        tickets=items,
        configurado=True,
    )
