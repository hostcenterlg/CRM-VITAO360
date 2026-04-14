"""
CRM VITAO360 — Rotas /api/pipeline e /api/notificacoes e /api/webhook/deskrio

Endpoints:
  POST /api/pipeline/run       — dispara pipeline completo (admin only)
  GET  /api/pipeline/status    — ultimo run, duracao, resultado
  GET  /api/pipeline/logs      — ultimos 20 runs de execucao
  GET  /api/notificacoes       — alertas dinamicos do estado do banco
  POST /api/webhook/deskrio    — recebe eventos Deskrio (publico, sem JWT)

Regras:
  R4 — Two-Base Architecture: webhook cria LOGs com valor R$ 0.00 SEMPRE.
  R5 — CNPJ normalizado para 14 digitos em todos os fluxos.
  R8 — NUNCA fabricar dados. Webhook so cria log se CNPJ existe no banco.
  R11 — Logs estruturados com contexto (cnpj, evento, duracao).

Autorizacao:
  POST /api/pipeline/run  — require_admin
  GET  /api/pipeline/*    — require_admin
  GET  /api/notificacoes  — get_current_user (qualquer usuario autenticado)
  POST /api/webhook/deskrio — publico (Deskrio nao envia token)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import get_db
from backend.app.services.pipeline_service import pipeline_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Pipeline e Notificacoes"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalizar_cnpj(valor: Any) -> str:
    """R5: string 14 digitos, zero-padded."""
    return re.sub(r"\D", "", str(valor)).zfill(14)


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class StepResultResponse(BaseModel):
    nome: str
    sucesso: bool
    registros_processados: int
    mensagem: str
    erro: str


class PipelineRunResponse(BaseModel):
    inicio: str
    fim: str | None
    duracao_segundos: float | None
    sucesso: bool
    total_clientes_atualizados: int
    mensagem: str
    steps: list[StepResultResponse]


class PipelineStatusResponse(BaseModel):
    ultimo_run: PipelineRunResponse | None
    proximo_agendado: str | None
    em_execucao: bool


class AlertaResponse(BaseModel):
    tipo: str = Field(..., description="CHURN | SINALEIRO_VERMELHO | FOLLOWUP_VENCIDO | META_RISCO")
    prioridade: str = Field(..., description="ALTA | MEDIA | BAIXA")
    cnpj: str = Field(..., description="CNPJ 14 digitos (R5)")
    nome: str
    mensagem: str
    acao: str


class NotificacoesResponse(BaseModel):
    total: int
    alertas: list[AlertaResponse]


class WebhookDeskrioPayload(BaseModel):
    """
    Payload de evento Deskrio.

    Campos esperados:
      event: tipo de evento ("message.received", "ticket.created", etc.)
      data:  objeto com dados do evento (numero, contactId, body, etc.)
    """
    event: str
    data: dict[str, Any] = Field(default_factory=dict)


class WebhookDeskrioResponse(BaseModel):
    recebido: bool
    mensagem: str
    log_id: int | None = None


# ---------------------------------------------------------------------------
# Pipeline endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/api/pipeline/run",
    response_model=PipelineRunResponse,
    summary="Disparar pipeline completo",
    description=(
        "Executa o pipeline completo: sync_deskrio → sync_mercos → recalculate. "
        "Restrito a administradores. Retorna resultado detalhado por step."
    ),
)
def run_pipeline(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """
    Dispara o pipeline de sincronizacao e recalculo.

    Idempotente: se ja houver um run ativo, retorna 409 Conflict.
    """
    status_atual = pipeline_service.get_status()
    if status_atual.em_execucao:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pipeline ja em execucao. Aguarde o termino antes de disparar novamente.",
        )

    logger.info("Pipeline: run manual disparado por admin")
    result = pipeline_service.run_full_pipeline(db)

    return PipelineRunResponse(
        inicio=result.inicio.isoformat(),
        fim=result.fim.isoformat() if result.fim else None,
        duracao_segundos=result.duracao_segundos,
        sucesso=result.sucesso,
        total_clientes_atualizados=result.total_clientes_atualizados,
        mensagem=result.mensagem,
        steps=[
            StepResultResponse(
                nome=s.nome,
                sucesso=s.sucesso,
                registros_processados=s.registros_processados,
                mensagem=s.mensagem,
                erro=s.erro,
            )
            for s in result.steps
        ],
    )


@router.get(
    "/api/pipeline/status",
    response_model=PipelineStatusResponse,
    summary="Status do pipeline",
    description="Retorna o ultimo run executado, duracao, resultado e flag em_execucao.",
)
def get_pipeline_status(_admin=Depends(require_admin)):
    """Status do pipeline: ultimo run e se esta em execucao."""
    status_obj = pipeline_service.get_status()

    ultimo = None
    if status_obj.ultimo_run:
        r = status_obj.ultimo_run
        ultimo = PipelineRunResponse(
            inicio=r.inicio.isoformat(),
            fim=r.fim.isoformat() if r.fim else None,
            duracao_segundos=r.duracao_segundos,
            sucesso=r.sucesso,
            total_clientes_atualizados=r.total_clientes_atualizados,
            mensagem=r.mensagem,
            steps=[
                StepResultResponse(
                    nome=s.nome,
                    sucesso=s.sucesso,
                    registros_processados=s.registros_processados,
                    mensagem=s.mensagem,
                    erro=s.erro,
                )
                for s in r.steps
            ],
        )

    return PipelineStatusResponse(
        ultimo_run=ultimo,
        proximo_agendado=status_obj.proximo_agendado,
        em_execucao=status_obj.em_execucao,
    )


@router.get(
    "/api/pipeline/logs",
    summary="Logs de execucao do pipeline",
    description="Retorna os ultimos 20 runs do pipeline, mais recente primeiro.",
)
def get_pipeline_logs(_admin=Depends(require_admin)):
    """Historico dos ultimos 20 runs do pipeline."""
    return {"logs": pipeline_service.get_logs()}


# ---------------------------------------------------------------------------
# Notificacoes
# ---------------------------------------------------------------------------

@router.get(
    "/api/notificacoes",
    response_model=NotificacoesResponse,
    summary="Alertas e notificacoes do CRM",
    description=(
        "Gera alertas dinamicos baseados no estado atual do banco: "
        "CHURN, SINALEIRO_VERMELHO, FOLLOWUP_VENCIDO, META_RISCO. "
        "Disponivel para qualquer usuario autenticado."
    ),
)
def get_notificacoes(
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """
    Retorna lista de alertas priorizados.

    Categorias:
      CHURN              — temperatura='CRITICO'
      SINALEIRO_VERMELHO — sinaleiro='VERMELHO' + sem contato >= 7 dias
      FOLLOWUP_VENCIDO   — followup_vencido=True
      META_RISCO         — pct_alcancado < 50% da meta anual

    Ordenado: ALTA antes de MEDIA.
    """
    alertas = pipeline_service.get_notifications(db)

    return NotificacoesResponse(
        total=len(alertas),
        alertas=[
            AlertaResponse(
                tipo=a["tipo"],
                prioridade=a["prioridade"],
                cnpj=a["cnpj"],
                nome=a["nome"],
                mensagem=a["mensagem"],
                acao=a["acao"],
            )
            for a in alertas
        ],
    )


# ---------------------------------------------------------------------------
# Webhook Deskrio
# ---------------------------------------------------------------------------

@router.post(
    "/api/webhook/deskrio",
    response_model=WebhookDeskrioResponse,
    status_code=200,
    summary="Webhook Deskrio — eventos de mensagem",
    description=(
        "Recebe eventos do Deskrio. Endpoint publico (sem JWT). "
        "Evento 'message.received' cria LogInteracao automaticamente. "
        "R4: log sempre com valor R$ 0.00. "
        "R5: CNPJ normalizado. "
        "R8: log so criado se cliente existe no banco."
    ),
)
def webhook_deskrio(
    payload: WebhookDeskrioPayload,
    db: Session = Depends(get_db),
):
    """
    Processa webhook do Deskrio.

    Fluxo para event='message.received':
      1. Extrai numero de telefone do payload.data
      2. Busca cliente por numero de telefone (campo Cliente.telefone)
      3. Resolve CNPJ — R8: se nao encontrar, descarta silenciosamente
      4. Insere LogInteracao com R$ 0.00 (R4 — Two-Base)
      5. Retorna 200 imediatamente (webhook deve responder rapido)

    Eventos desconhecidos: retorna 200 com mensagem informativa (nao bloquear Deskrio).
    """
    evento = (payload.event or "").strip().lower()
    data = payload.data or {}

    logger.info("Webhook Deskrio: evento=%s", evento)

    if evento != "message.received":
        logger.debug("Webhook Deskrio: evento '%s' ignorado", evento)
        return WebhookDeskrioResponse(
            recebido=True,
            mensagem=f"Evento '{payload.event}' recebido mas nao processado (apenas message.received e tratado).",
        )

    # -- Extrair numero de telefone
    numero_raw: str = ""
    # Varios campos possiveis dependendo da versao do Deskrio
    for campo in ("number", "from", "contact_number", "phone"):
        valor = data.get(campo) or ""
        if valor:
            numero_raw = str(valor).strip()
            break

    # Tentar via sub-objeto contact
    if not numero_raw:
        contato_obj = data.get("contact") or {}
        if isinstance(contato_obj, dict):
            numero_raw = str(contato_obj.get("number") or "").strip()

    if not numero_raw:
        logger.warning("Webhook Deskrio: message.received sem numero de telefone | data_keys=%s", list(data.keys()))
        return WebhookDeskrioResponse(
            recebido=True,
            mensagem="Evento recebido mas sem numero de telefone identificavel.",
        )

    # Normalizar numero (apenas digitos)
    numero_norm = re.sub(r"\D", "", numero_raw)

    # -- Buscar cliente por telefone
    from backend.app.models.cliente import Cliente
    from backend.app.models.log_interacao import LogInteracao

    cliente = (
        db.query(Cliente)
        .filter(Cliente.telefone == numero_norm)
        .first()
    )

    # Fallback: buscar sem DDI (ultimos 11 digitos)
    if not cliente and len(numero_norm) > 11:
        sufixo = numero_norm[-11:]
        cliente = (
            db.query(Cliente)
            .filter(Cliente.telefone.like(f"%{sufixo}"))
            .first()
        )

    if not cliente:
        logger.debug(
            "Webhook Deskrio: cliente nao encontrado para numero=%s — log nao criado",
            numero_norm,
        )
        return WebhookDeskrioResponse(
            recebido=True,
            mensagem=f"Cliente nao encontrado para numero {numero_norm}. Log nao criado.",
        )

    # -- Montar descricao do log
    body_msg = str(data.get("body") or data.get("message") or "").strip()[:500]
    if not body_msg:
        body_msg = "Mensagem WhatsApp recebida via Deskrio."

    contato_nome = ""
    contato_obj = data.get("contact") or {}
    if isinstance(contato_obj, dict):
        contato_nome = str(contato_obj.get("name") or "").strip()

    descricao = f"[WEBHOOK DESKRIO] {contato_nome}: {body_msg}" if contato_nome else f"[WEBHOOK DESKRIO] {body_msg}"

    # -- Criar LogInteracao
    # R4 — Two-Base: sem valor monetario aqui
    # R5 — CNPJ ja e string 14 digitos (vem do modelo Cliente)
    try:
        log = LogInteracao(
            cnpj=cliente.cnpj,
            data_interacao=datetime.now(timezone.utc),
            consultor=cliente.consultor or "LEGADO",
            resultado="MENSAGEM RECEBIDA",
            descricao=descricao,
            tipo_contato="WHATSAPP",
            # Campos calculados pelo motor ficam vazios (serao preenchidos no recalculo)
            estagio_funil=None,
            fase=None,
            acao_futura=None,
            temperatura=None,
            follow_up_dias=None,
            grupo_dash=None,
            tentativa=None,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        logger.info(
            "Webhook Deskrio: log criado | log_id=%d cnpj=%s numero=%s",
            log.id,
            cliente.cnpj,
            numero_norm,
        )

        return WebhookDeskrioResponse(
            recebido=True,
            mensagem=f"Mensagem registrada para cliente {cliente.nome_fantasia or cliente.cnpj}.",
            log_id=log.id,
        )

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Webhook Deskrio: erro ao criar log | cnpj=%s erro=%s",
            cliente.cnpj,
            exc,
        )
        # Retornar 200 mesmo em erro para nao bloquear o Deskrio
        return WebhookDeskrioResponse(
            recebido=True,
            mensagem="Evento recebido. Erro interno ao persistir log (nao afeta o Deskrio).",
        )
