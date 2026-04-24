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
        logger.exception("Erro ao gerar briefing | cnpj=%s: %s — retornando fallback", cnpj, exc)
        return BriefingResponse(
            cnpj=cnpj,
            nome_cliente="—",
            briefing="[Briefing temporariamente indisponível — tente novamente em instantes]",
            tokens_usados=0,
            cached=False,
            ia_configurada=False,
        )

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
            "Erro ao gerar mensagem WA | cnpj=%s: %s — retornando fallback", cnpj, exc
        )
        return MensagemWAAutomaticaResponse(
            cnpj=cnpj,
            nome_cliente="—",
            mensagem="[Geração de mensagem temporariamente indisponível]",
            tom="NEUTRO",
            contexto="INDISPONIVEL",
            tokens_usados=0,
            ia_configurada=False,
        )

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
            "Erro ao gerar mensagem WA | cnpj=%s: %s — retornando fallback", cnpj, exc
        )
        return MensagemWhatsAppResponse(
            cnpj=cnpj,
            nome_cliente="—",
            mensagem="[Geração de mensagem temporariamente indisponível]",
            tokens_usados=0,
            ia_configurada=False,
        )

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
        # Graceful degradation — responde 200 com payload zerado em vez de 500.
        # Frontend lida com ia_configurada=False mostrando mensagem neutra.
        logger.exception(
            "Erro ao gerar resumo semanal | consultor=%s: %s — retornando fallback",
            consultor,
            exc,
        )
        return ResumoSemanalResponse(
            consultor=consultor.upper(),
            periodo="",
            resumo="[Resumo indisponível — serviço degradado]",
            tokens_usados=0,
            metricas=MetricasSemanaisResponse(
                total_carteira=0,
                clientes_contactados_semana=0,
                vendas_semana_qtd=0,
                vendas_semana_volume=0.0,
                clientes_em_risco=0,
                followups_vencidos=0,
                pipeline={},
                top3_proxima_semana=[],
            ),
            ia_configurada=False,
        )

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
        # Graceful degradation — 200 com risco BAIXO + sem fatores em vez de 500.
        logger.exception(
            "Erro ao calcular churn risk | cnpj=%s: %s — retornando fallback",
            cnpj, exc,
        )
        return ChurnRiskResponse(
            cnpj=cnpj,
            nome_cliente="—",
            risco_pct=0.0,
            nivel="INDISPONIVEL",
            fatores=[],
            recomendacao="Serviço de risco temporariamente indisponível.",
            ia_configurada=False,
        )

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
            "Erro ao gerar sugestão de produto | cnpj=%s: %s — retornando fallback", cnpj, exc
        )
        return SugestaoProdutoResponse(
            cnpj=cnpj,
            nome_cliente="—",
            produtos_sugeridos=[],
            estrategia="Serviço de sugestão temporariamente indisponível.",
            categorias_frequentes=[],
            ia_configurada=False,
        )

    return SugestaoProdutoResponse(**resultado)


# ---------------------------------------------------------------------------
# Schemas Pydantic — Response (módulo IA avançada)
# ---------------------------------------------------------------------------

class HistoricoSentimentoItem(BaseModel):
    """Item individual do histórico de sentimento."""

    data: str
    resultado: str
    sentimento: str


class SentimentoResponse(BaseModel):
    """Resposta do endpoint de análise de sentimento WhatsApp."""

    cnpj: str
    sentimento: str          # POSITIVO | NEUTRO | NEGATIVO | URGENTE
    score: float             # 0-100
    historico: list[HistoricoSentimentoItem]
    tendencia: str           # MELHORANDO | ESTAVEL | PIORANDO
    recomendacao: str


class FatorFechamentoItem(BaseModel):
    """Fator individual que compõe a previsão de fechamento."""

    nome: str
    peso: int
    contribuicao: float


class PrevisaoFechamentoResponse(BaseModel):
    """Resposta do endpoint de previsão de fechamento de venda."""

    cnpj: str
    probabilidade_pct: float
    nivel: str               # ALTA | MEDIA | BAIXA
    fatores: list[FatorFechamentoItem]
    tempo_estimado_dias: int
    recomendacao: str


class MetricasCoachResponse(BaseModel):
    """Métricas numéricas do coach de vendas."""

    conversao_pct: float
    ticket_medio: float
    atendimentos_dia: float
    positivacao_pct: float


class RecomendacaoCoachItem(BaseModel):
    """Recomendação individual do coach de vendas."""

    prioridade: str
    acao: str
    impacto_estimado: str


class CoachVendasResponse(BaseModel):
    """Resposta do endpoint de coach de vendas."""

    consultor: str
    periodo: str
    metricas: MetricasCoachResponse
    pontos_fortes: list[str]
    pontos_fracos: list[str]
    recomendacoes: list[RecomendacaoCoachItem]
    meta_sugerida: str


class OportunidadeItem(BaseModel):
    """Oportunidade de venda detectada automaticamente."""

    cnpj: str
    nome: str
    tipo: str                # REATIVACAO | UPSELL | PROSPECT_QUENTE | CROSS_SELL_REDE
    prioridade: str          # ALTA | MEDIA
    valor_potencial: float
    motivo: str
    acao_sugerida: str


class AlertaOportunidadeResponse(BaseModel):
    """Resposta do endpoint de alertas de oportunidade."""

    total: int
    oportunidades: list[OportunidadeItem]


class ConsultorDestaqueItem(BaseModel):
    """Consultor em destaque no dashboard IA."""

    nome: str
    motivo: str


class DashboardIAResponse(BaseModel):
    """Resposta do endpoint de dashboard de KPIs de IA."""

    briefings_disponiveis: int
    alertas_ativos: int
    oportunidades: int
    clientes_em_risco: int
    consultor_destaque: ConsultorDestaqueItem
    insight_do_dia: str


# ---------------------------------------------------------------------------
# Endpoints — IA Avançada
# ---------------------------------------------------------------------------

@router.get(
    "/sentimento/{cnpj}",
    response_model=SentimentoResponse,
    summary="Análise de sentimento das últimas interações WhatsApp do cliente",
    description=(
        "Analisa os últimos 20 registros de interação WhatsApp do cliente. "
        "Classifica o sentimento dominante em POSITIVO, NEUTRO, NEGATIVO ou URGENTE "
        "com base nos resultados dos atendimentos. "
        "Calcula score (0-100), tendência (MELHORANDO/ESTAVEL/PIORANDO) e recomendação de ação. "
        "R4: busca apenas log_interacoes — sem valores monetários."
    ),
)
async def get_sentimento(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> SentimentoResponse:
    """
    Retorna análise de sentimento baseada no histórico de interações do cliente.

    O CNPJ pode ser enviado formatado; é normalizado automaticamente.

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de sentimento | cnpj=%s usuario=%s",
        cnpj,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.analisar_sentimento(cnpj=cnpj, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(
            "Erro ao analisar sentimento | cnpj=%s: %s — retornando fallback",
            cnpj, exc,
        )
        return SentimentoResponse(
            cnpj=cnpj,
            sentimento="NEUTRO",
            score=0.0,
            historico=[],
            tendencia="ESTAVEL",
            recomendacao="Análise temporariamente indisponível.",
        )

    return SentimentoResponse(
        cnpj=resultado["cnpj"],
        sentimento=resultado["sentimento"],
        score=resultado["score"],
        historico=[HistoricoSentimentoItem(**h) for h in resultado["historico"]],
        tendencia=resultado["tendencia"],
        recomendacao=resultado["recomendacao"],
    )


@router.get(
    "/previsao-fechamento/{cnpj}",
    response_model=PrevisaoFechamentoResponse,
    summary="Probabilidade de fechar venda com o cliente",
    description=(
        "Calcula probabilidade de fechamento de venda considerando 4 fatores ponderados: "
        "estágio no funil (40%), tempo no estágio/dias sem compra (20%), "
        "taxa de conversão histórica do consultor (20%) e perfil de ticket (20%). "
        "Retorna nível ALTA/MEDIA/BAIXA, fatores detalhados e tempo estimado. "
        "R4: vendas e logs consultados em queries separadas."
    ),
)
async def get_previsao_fechamento(
    cnpj: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> PrevisaoFechamentoResponse:
    """
    Retorna probabilidade de fechamento de venda para o cliente.

    O CNPJ pode ser enviado formatado; é normalizado automaticamente.

    Retorna 404 se o CNPJ não existir na base de clientes.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de previsão de fechamento | cnpj=%s usuario=%s",
        cnpj,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.prever_fechamento(cnpj=cnpj, db=db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Erro ao prever fechamento | cnpj=%s: %s — retornando fallback", cnpj, exc)
        return PrevisaoFechamentoResponse(
            cnpj=cnpj,
            probabilidade_pct=0.0,
            nivel="BAIXA",
            fatores=[],
            tempo_estimado_dias=0,
            recomendacao="Previsão temporariamente indisponível.",
        )

    return PrevisaoFechamentoResponse(
        cnpj=resultado["cnpj"],
        probabilidade_pct=resultado["probabilidade_pct"],
        nivel=resultado["nivel"],
        fatores=[FatorFechamentoItem(**f) for f in resultado["fatores"]],
        tempo_estimado_dias=resultado["tempo_estimado_dias"],
        recomendacao=resultado["recomendacao"],
    )


@router.get(
    "/coach/{consultor}",
    response_model=CoachVendasResponse,
    summary="Coach de vendas — análise de performance e recomendações de foco",
    description=(
        "Analisa a performance do consultor nos últimos 30 dias: "
        "taxa de conversão, ticket médio, volume de atendimentos e positivação de carteira. "
        "Compara com benchmarks internos da VITAO e identifica pontos fortes e fracos. "
        "Retorna recomendações priorizadas (ALTA/MEDIA/BAIXA) e meta sugerida. "
        "Consultores válidos: MANU, LARISSA, DAIANE, JULIO."
    ),
)
async def get_coach_vendas(
    consultor: str,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> CoachVendasResponse:
    """
    Retorna análise de performance e recomendações de coaching para o consultor.

    O nome do consultor é normalizado para UPPERCASE.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de coach de vendas | consultor=%s usuario=%s",
        consultor,
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.coach_vendas(consultor=consultor, db=db)
    except Exception as exc:
        logger.exception("Erro ao gerar coach | consultor=%s: %s — retornando fallback", consultor, exc)
        return CoachVendasResponse(
            consultor=consultor.upper(),
            periodo="",
            metricas=MetricasCoachResponse(
                conversao_pct=0.0,
                ticket_medio=0.0,
                atendimentos_dia=0.0,
                positivacao_pct=0.0,
            ),
            pontos_fortes=[],
            pontos_fracos=[],
            recomendacoes=[],
            meta_sugerida="Serviço de coaching temporariamente indisponível.",
        )

    return CoachVendasResponse(
        consultor=resultado["consultor"],
        periodo=resultado["periodo"],
        metricas=MetricasCoachResponse(**resultado["metricas"]),
        pontos_fortes=resultado["pontos_fortes"],
        pontos_fracos=resultado["pontos_fracos"],
        recomendacoes=[RecomendacaoCoachItem(**r) for r in resultado["recomendacoes"]],
        meta_sugerida=resultado["meta_sugerida"],
    )


@router.get(
    "/alerta-oportunidade",
    response_model=AlertaOportunidadeResponse,
    summary="Top 10 oportunidades de venda detectadas automaticamente",
    description=(
        "Detecta automaticamente as melhores oportunidades na carteira completa. "
        "Padrões: REATIVACAO (recorrente parou de comprar), UPSELL (ticket em alta), "
        "PROSPECT_QUENTE (prospect com contato recente), CROSS_SELL_REDE (mesma rede de cliente ativo). "
        "Retorna top 10 ordenadas por prioridade e score interno. "
        "R4: vendas e clientes consultados em queries separadas."
    ),
)
async def get_alerta_oportunidade(
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> AlertaOportunidadeResponse:
    """
    Retorna as top 10 oportunidades de venda detectadas automaticamente.

    Não requer parâmetros de rota — analisa a carteira completa.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de alertas de oportunidade | usuario=%s",
        getattr(user, "email", user.id),
    )

    try:
        resultado: dict[str, Any] = await ia_service.detectar_oportunidades(db=db)
    except Exception as exc:
        logger.exception("Erro ao detectar oportunidades: %s — retornando fallback", exc)
        return AlertaOportunidadeResponse(total=0, oportunidades=[])

    return AlertaOportunidadeResponse(
        total=resultado["total"],
        oportunidades=[OportunidadeItem(**op) for op in resultado["oportunidades"]],
    )


@router.get(
    "/dashboard",
    response_model=DashboardIAResponse,
    summary="Dashboard de KPIs do módulo de Inteligência Artificial",
    description=(
        "Agrega métricas-chave do módulo de IA: briefings disponíveis, alertas ativos no sinaleiro, "
        "oportunidades detectadas, clientes em risco e consultor em destaque. "
        "Inclui insight do dia gerado por template local. "
        "Ideal para o painel executivo. Requer autenticação JWT."
    ),
)
async def get_dashboard_ia(
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> DashboardIAResponse:
    """
    Retorna KPIs agregados do módulo de IA para o painel executivo.

    Requer autenticação JWT.
    """
    logger.info(
        "Requisição de dashboard IA | usuario=%s role=%s",
        getattr(user, "email", user.id),
        user.role,
    )

    try:
        resultado: dict[str, Any] = await ia_service.dashboard_ia(db=db)
    except Exception as exc:
        logger.exception("Erro ao gerar dashboard IA: %s — retornando fallback", exc)
        return DashboardIAResponse(
            briefings_disponiveis=0,
            alertas_ativos=0,
            oportunidades=0,
            clientes_em_risco=0,
            consultor_destaque=ConsultorDestaqueItem(nome="—", motivo="Indisponível"),
            insight_do_dia="Dashboard IA temporariamente indisponível.",
        )

    return DashboardIAResponse(
        briefings_disponiveis=resultado["briefings_disponiveis"],
        alertas_ativos=resultado["alertas_ativos"],
        oportunidades=resultado["oportunidades"],
        clientes_em_risco=resultado["clientes_em_risco"],
        consultor_destaque=ConsultorDestaqueItem(**resultado["consultor_destaque"]),
        insight_do_dia=resultado["insight_do_dia"],
    )
