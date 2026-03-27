"""
CRM VITAO360 — Serviço de Inteligência Artificial (IA Service)

Gera briefings pré-ligação, rascunhos de mensagens WhatsApp e resumos semanais
utilizando o modelo Claude via API Anthropic.

Comportamento sem chave configurada:
  - Retorna mensagem explicativa em vez de levantar exceção (graceful degradation).
  - O CRM continua funcional — IA é um recurso adicional, não um bloqueador.

R5 — CNPJ: normalizado para String(14) antes de qualquer consulta.
R4 — Two-Base: este serviço lê vendas e logs separadamente — nunca mistura valores.

Dependências:
  - httpx (async HTTP client)
  - ANTHROPIC_API_KEY no ambiente (opcional — degrada graciosamente se ausente)
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy.orm import Session

from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.venda import Venda

# ---------------------------------------------------------------------------
# Configuração de logging estruturado
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
_ANTHROPIC_URL: str = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION: str = "2023-06-01"
_MAX_TOKENS_BRIEFING: int = 1024
_MAX_TOKENS_WHATSAPP: int = 512
_MAX_TOKENS_RESUMO: int = 2048
_TIMEOUT_SEGUNDOS: float = 30.0

# Mensagem exibida quando a chave não está configurada
_MSG_SEM_CHAVE: str = "[IA não configurada — defina ANTHROPIC_API_KEY no .env]"

# ---------------------------------------------------------------------------
# Prompts do sistema
# ---------------------------------------------------------------------------

_SYSTEM_BRIEFING: str = (
    "Você é o assistente de inteligência comercial da VITAO Alimentos, "
    "distribuidora B2B de alimentos naturais.\n"
    "Gere um briefing pré-ligação conciso (máximo 150 palavras) para o consultor comercial.\n"
    "Estrutura obrigatória:\n"
    "  1) Quem é o cliente (1 linha)\n"
    "  2) Situação atual (score, sinaleiro, última compra)\n"
    "  3) O que fazer nesta ligação (ação específica)\n"
    "  4) O que oferecer (cross-sell se aplicável)\n"
    "Tom: direto, prático, orientado a ação. Sem floreios. Sem markdown excessivo."
)

_SYSTEM_WHATSAPP: str = (
    "Você é o assistente de inteligência comercial da VITAO Alimentos, "
    "distribuidora B2B de alimentos naturais.\n"
    "Redija uma mensagem de WhatsApp para o consultor enviar ao cliente.\n"
    "Regras:\n"
    "  - Tom: profissional mas cordial, como uma conversa B2B no Brasil\n"
    "  - Máximo 3 parágrafos curtos\n"
    "  - Incluir saudação pelo nome fantasia do cliente\n"
    "  - Finalizar com CTA claro (ex.: 'Posso te ligar amanhã às 10h?')\n"
    "  - NÃO incluir emojis em excesso — máximo 2\n"
    "  - NÃO inventar produtos ou preços — use apenas o que está no contexto"
)

_SYSTEM_RESUMO_SEMANAL: str = (
    "Você é o assistente de inteligência comercial da VITAO Alimentos, "
    "distribuidora B2B de alimentos naturais.\n"
    "Gere um resumo semanal da performance do consultor comercial.\n"
    "Estrutura:\n"
    "  1) Performance da semana (vendas realizadas, volume R$)\n"
    "  2) Clientes em risco que precisam de atenção (sinaleiro VERMELHO/LARANJA)\n"
    "  3) Top 3 oportunidades para a próxima semana\n"
    "  4) Recomendação de foco para o próximo período\n"
    "Tom: gerencial, analítico, orientado a decisão. Máximo 250 palavras."
)


# ---------------------------------------------------------------------------
# Função interna: chamada à API Anthropic
# ---------------------------------------------------------------------------

async def _call_claude(
    system: str,
    user: str,
    max_tokens: int = _MAX_TOKENS_BRIEFING,
) -> tuple[str, int]:
    """
    Realiza chamada assíncrona à API Anthropic (Claude).

    Retorna tupla (texto_gerado, tokens_usados).
    Em caso de chave ausente ou erro de API, retorna mensagem de fallback
    sem levantar exceção (graceful degradation).

    Args:
        system: Prompt do sistema que define o papel e tom do assistente.
        user:   Mensagem do usuário com os dados do cliente/consultor.
        max_tokens: Limite de tokens na resposta gerada.

    Returns:
        Tupla (texto: str, tokens_usados: int).
    """
    if not ANTHROPIC_API_KEY:
        logger.warning(
            "ANTHROPIC_API_KEY nao configurada — retornando mensagem de fallback"
        )
        return _MSG_SEM_CHAVE, 0

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": _ANTHROPIC_VERSION,
        "content-type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SEGUNDOS) as client:
            resp = await client.post(_ANTHROPIC_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        texto: str = data["content"][0]["text"]
        tokens_usados: int = data.get("usage", {}).get("output_tokens", 0)

        logger.info(
            "Chamada Claude bem-sucedida | modelo=%s tokens_saida=%d",
            CLAUDE_MODEL,
            tokens_usados,
        )
        return texto, tokens_usados

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Erro HTTP na API Anthropic | status=%d corpo=%s",
            exc.response.status_code,
            exc.response.text[:500],
        )
        return (
            f"[Erro na API de IA: HTTP {exc.response.status_code} — tente novamente]",
            0,
        )
    except httpx.TimeoutException:
        logger.error("Timeout na chamada à API Anthropic (%.1fs)", _TIMEOUT_SEGUNDOS)
        return "[Erro na API de IA: timeout — tente novamente]", 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erro inesperado na chamada à API Anthropic: %s", exc)
        return "[Erro interno na IA — contate o administrador]", 0


# ---------------------------------------------------------------------------
# Funções auxiliares de formatação de contexto
# ---------------------------------------------------------------------------

def _normalizar_cnpj(cnpj: str) -> str:
    """R5: remove pontuação e zero-pad para 14 dígitos."""
    return re.sub(r"\D", "", cnpj).zfill(14)


def _formatar_data(valor: date | datetime | None) -> str:
    """Formata data para exibição legível em PT-BR."""
    if valor is None:
        return "não informada"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")
    return valor.strftime("%d/%m/%Y")


def _formatar_moeda(valor: float | None) -> str:
    """Formata valor monetário para PT-BR."""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _construir_contexto_cliente(
    cliente: Cliente,
    ultimas_interacoes: list[LogInteracao],
    ultimas_vendas: list[Venda],
) -> str:
    """
    Monta o bloco de contexto em texto estruturado para o prompt do usuário.

    R4 — Two-Base: vendas e interações são formatadas separadamente.
    """
    linhas: list[str] = [
        "=== DADOS DO CLIENTE ===",
        f"Nome Fantasia: {cliente.nome_fantasia or 'não informado'}",
        f"Razão Social: {cliente.razao_social or 'não informada'}",
        f"CNPJ: {cliente.cnpj}",
        f"Cidade/UF: {cliente.cidade or '—'} / {cliente.uf or '—'}",
        f"Consultor responsável: {cliente.consultor or 'não atribuído'}",
        f"Tipo de cliente SAP: {cliente.tipo_cliente_sap or 'não informado'}",
        f"Rede/Franquia: {cliente.rede_regional or 'independente'}",
        "",
        "=== SITUAÇÃO COMERCIAL ===",
        f"Situação: {cliente.situacao or 'não informada'}",
        f"Sinaleiro: {cliente.sinaleiro or 'não informado'}",
        f"Score: {cliente.score:.1f}/100" if cliente.score is not None else "Score: não calculado",
        f"Prioridade: {cliente.prioridade or 'não definida'}",
        f"Temperatura: {cliente.temperatura or 'não informada'}",
        f"Curva ABC: {cliente.curva_abc or 'não classificado'}",
        f"Fase atual: {cliente.fase or 'não informada'}",
        f"Estágio no funil: {cliente.estagio_funil or 'não informado'}",
        "",
        "=== HISTÓRICO DE COMPRAS ===",
        f"Total de compras: {cliente.n_compras or 0}",
        f"Faturamento acumulado: {_formatar_moeda(cliente.faturamento_total)}",
        f"Dias sem compra: {cliente.dias_sem_compra or 'não informado'}",
        f"Valor do último pedido: {_formatar_moeda(cliente.valor_ultimo_pedido)}",
        f"Ciclo médio entre compras: {cliente.ciclo_medio:.0f} dias" if cliente.ciclo_medio else "Ciclo médio: não calculado",
        "",
        "=== META E PROJEÇÃO ===",
        f"Meta anual: {_formatar_moeda(cliente.meta_anual)}",
        f"Realizado acumulado: {_formatar_moeda(cliente.realizado_acumulado)}",
        f"% da meta atingida: {(cliente.pct_alcancado or 0) * 100:.1f}%",
        f"Status da meta: {cliente.status_meta or 'não definido'}",
        "",
        "=== PRÓXIMA AÇÃO RECOMENDADA ===",
        f"Ação futura: {cliente.acao_futura or 'não definida'}",
        f"Follow-up em: {cliente.followup_dias or 0} dias",
        f"Follow-up vencido: {'SIM' if cliente.followup_vencido else 'NÃO'}",
        f"Tentativas: {cliente.tentativas or 'T1'}",
    ]

    # Últimas 3 vendas (R4: tabela separada, só valores positivos)
    linhas.append("")
    linhas.append("=== ÚLTIMAS VENDAS (até 3) ===")
    if ultimas_vendas:
        for v in ultimas_vendas:
            linhas.append(
                f"  - {_formatar_data(v.data_pedido)} | "
                f"{_formatar_moeda(v.valor_pedido)} | "
                f"Pedido: {v.numero_pedido or 'sem número'} | "
                f"Fonte: {v.fonte}"
            )
    else:
        linhas.append("  (sem vendas registradas)")

    # Últimas 5 interações (R4: tabela separada, sem valor monetário)
    linhas.append("")
    linhas.append("=== ÚLTIMAS INTERAÇÕES (até 5) ===")
    if ultimas_interacoes:
        for i in ultimas_interacoes:
            descricao_trunc = (i.descricao or "")[:200]
            linhas.append(
                f"  - {_formatar_data(i.data_interacao)} | "
                f"Resultado: {i.resultado} | "
                f"Fase: {i.fase or '—'} | "
                f"Temperatura: {i.temperatura or '—'}\n"
                f"    Obs: {descricao_trunc or '(sem observação)'}"
            )
    else:
        linhas.append("  (sem interações registradas)")

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------

class IAService:
    """
    Serviço de Inteligência Artificial do CRM VITAO360.

    Métodos públicos (todos assíncronos):
      - gerar_briefing: briefing pré-ligação para um cliente
      - gerar_mensagem_whatsapp: rascunho de mensagem WA para um objetivo
      - gerar_resumo_semanal: resumo executivo semanal por consultor
    """

    # ------------------------------------------------------------------
    # Método 1: Briefing pré-ligação
    # ------------------------------------------------------------------

    async def gerar_briefing(self, cnpj: str, db: Session) -> dict[str, Any]:
        """
        Gera um briefing pré-ligação completo para o consultor sobre um cliente.

        Busca os dados mais recentes do cliente (situação, score, sinaleiro),
        as últimas 5 interações e as últimas 3 vendas e envia ao Claude para
        gerar um texto conciso e orientado a ação.

        Args:
            cnpj: CNPJ do cliente (14 dígitos, aceita formatado).
            db:   Sessão SQLAlchemy ativa (injetada pelo FastAPI).

        Returns:
            dict com:
              - briefing (str): texto gerado pelo Claude (ou fallback)
              - tokens_usados (int): tokens de saída consumidos
              - cached (bool): sempre False — sem cache implementado ainda
              - cnpj (str): CNPJ normalizado consultado
              - nome_cliente (str): nome fantasia do cliente
              - ia_configurada (bool): se ANTHROPIC_API_KEY está presente

        Raises:
            ValueError: se o CNPJ não for encontrado na base.
        """
        cnpj_n = _normalizar_cnpj(cnpj)

        # Buscar cliente
        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj_n).first()
        if not cliente:
            raise ValueError(f"Cliente CNPJ {cnpj_n} não encontrado")

        # R4: buscar interações (LOG — sem valor monetário)
        ultimas_interacoes = (
            db.query(LogInteracao)
            .filter(LogInteracao.cnpj == cnpj_n)
            .order_by(LogInteracao.data_interacao.desc())
            .limit(5)
            .all()
        )

        # R4: buscar vendas separadamente (VENDA — valor > 0)
        ultimas_vendas = (
            db.query(Venda)
            .filter(Venda.cnpj == cnpj_n)
            .order_by(Venda.data_pedido.desc())
            .limit(3)
            .all()
        )

        contexto = _construir_contexto_cliente(cliente, ultimas_interacoes, ultimas_vendas)

        prompt_usuario = (
            f"Gere o briefing pré-ligação para o cliente abaixo:\n\n{contexto}"
        )

        logger.info(
            "Gerando briefing | cnpj=%s nome=%s score=%.1f",
            cnpj_n,
            cliente.nome_fantasia or "—",
            cliente.score or 0.0,
        )

        texto, tokens = await _call_claude(
            system=_SYSTEM_BRIEFING,
            user=prompt_usuario,
            max_tokens=_MAX_TOKENS_BRIEFING,
        )

        return {
            "cnpj": cnpj_n,
            "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
            "briefing": texto,
            "tokens_usados": tokens,
            "cached": False,
            "ia_configurada": bool(ANTHROPIC_API_KEY),
        }

    # ------------------------------------------------------------------
    # Método 2: Rascunho de mensagem WhatsApp
    # ------------------------------------------------------------------

    async def gerar_mensagem_whatsapp(
        self, cnpj: str, objetivo: str, db: Session
    ) -> dict[str, Any]:
        """
        Gera um rascunho de mensagem WhatsApp para o consultor enviar ao cliente.

        O objetivo orienta o tom e o conteúdo (ex.: 'reativação após 60 dias sem compra',
        'oferta de novo produto linha cereais', 'confirmação de visita').

        Args:
            cnpj:    CNPJ do cliente (aceita formatado).
            objetivo: Texto livre descrevendo o objetivo da mensagem.
            db:      Sessão SQLAlchemy ativa.

        Returns:
            dict com:
              - mensagem (str): rascunho da mensagem WA
              - tokens_usados (int): tokens consumidos
              - cnpj (str): CNPJ normalizado
              - nome_cliente (str): nome fantasia do cliente
              - ia_configurada (bool): se ANTHROPIC_API_KEY está presente

        Raises:
            ValueError: se o CNPJ não for encontrado.
        """
        cnpj_n = _normalizar_cnpj(cnpj)

        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj_n).first()
        if not cliente:
            raise ValueError(f"Cliente CNPJ {cnpj_n} não encontrado")

        # Para WA basta o contexto resumido (sem histórico detalhado)
        ultimas_interacoes = (
            db.query(LogInteracao)
            .filter(LogInteracao.cnpj == cnpj_n)
            .order_by(LogInteracao.data_interacao.desc())
            .limit(3)
            .all()
        )
        ultimas_vendas = (
            db.query(Venda)
            .filter(Venda.cnpj == cnpj_n)
            .order_by(Venda.data_pedido.desc())
            .limit(2)
            .all()
        )

        contexto = _construir_contexto_cliente(cliente, ultimas_interacoes, ultimas_vendas)

        prompt_usuario = (
            f"Objetivo desta mensagem: {objetivo}\n\n"
            f"Dados do cliente:\n{contexto}\n\n"
            "Escreva a mensagem WhatsApp que o consultor deve enviar."
        )

        logger.info(
            "Gerando mensagem WA | cnpj=%s objetivo=%.80s",
            cnpj_n,
            objetivo,
        )

        texto, tokens = await _call_claude(
            system=_SYSTEM_WHATSAPP,
            user=prompt_usuario,
            max_tokens=_MAX_TOKENS_WHATSAPP,
        )

        return {
            "cnpj": cnpj_n,
            "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
            "mensagem": texto,
            "tokens_usados": tokens,
            "ia_configurada": bool(ANTHROPIC_API_KEY),
        }

    # ------------------------------------------------------------------
    # Método 3: Resumo semanal por consultor
    # ------------------------------------------------------------------

    async def gerar_resumo_semanal(
        self, consultor: str, db: Session
    ) -> dict[str, Any]:
        """
        Gera um resumo executivo da semana corrente para um consultor.

        Agrega automaticamente:
          - Vendas dos últimos 7 dias (R4: tabela vendas)
          - Clientes em risco (sinaleiro VERMELHO ou LARANJA)
          - Clientes com follow-up vencido
          - Top 5 clientes por score para priorização

        Args:
            consultor: Nome do consultor (MANU/LARISSA/DAIANE/JULIO).
            db:        Sessão SQLAlchemy ativa.

        Returns:
            dict com:
              - consultor (str): nome normalizado
              - resumo (str): texto gerado pelo Claude
              - tokens_usados (int): tokens consumidos
              - periodo (str): período de referência (DD/MM-DD/MM/AAAA)
              - metricas (dict): dados brutos que alimentaram o prompt
              - ia_configurada (bool): se ANTHROPIC_API_KEY está presente
        """
        consultor_norm = consultor.upper().strip()

        hoje = date.today()
        inicio_semana = hoje - timedelta(days=7)

        # R4: vendas da semana (tabela vendas — valor > 0)
        vendas_semana = (
            db.query(Venda)
            .filter(
                Venda.consultor == consultor_norm,
                Venda.data_pedido >= inicio_semana,
            )
            .order_by(Venda.data_pedido.desc())
            .all()
        )

        total_vendas_semana = sum(v.valor_pedido for v in vendas_semana)
        qtd_vendas_semana = len(vendas_semana)

        # Clientes em risco (sinaleiro VERMELHO ou LARANJA)
        clientes_risco = (
            db.query(Cliente)
            .filter(
                Cliente.consultor == consultor_norm,
                Cliente.sinaleiro.in_(["VERMELHO", "LARANJA"]),
            )
            .order_by(Cliente.score.desc().nulls_last())
            .limit(10)
            .all()
        )

        # Clientes com follow-up vencido
        followup_vencidos = (
            db.query(Cliente)
            .filter(
                Cliente.consultor == consultor_norm,
                Cliente.followup_vencido == True,  # noqa: E712
            )
            .count()
        )

        # Top 5 por score (oportunidades)
        top_score = (
            db.query(Cliente)
            .filter(
                Cliente.consultor == consultor_norm,
                Cliente.situacao.in_(["ATIVO", "EM_RISCO", "INAT.REC"]),
            )
            .order_by(Cliente.score.desc().nulls_last())
            .limit(5)
            .all()
        )

        # Total de clientes na carteira
        total_carteira = (
            db.query(Cliente)
            .filter(Cliente.consultor == consultor_norm)
            .count()
        )

        # Montar contexto para o prompt
        linhas_risco = "\n".join(
            f"  - {c.nome_fantasia or c.cnpj} | Sinaleiro: {c.sinaleiro} | "
            f"Dias sem compra: {c.dias_sem_compra or '?'} | Score: {c.score or 0:.0f}"
            for c in clientes_risco[:5]
        )

        linhas_oportunidades = "\n".join(
            f"  - {c.nome_fantasia or c.cnpj} | Score: {c.score or 0:.0f} | "
            f"Situação: {c.situacao} | Fase: {c.fase or '—'} | "
            f"Ação: {c.acao_futura or 'não definida'}"
            for c in top_score
        )

        contexto_semana = (
            f"=== RESUMO SEMANAL — {consultor_norm} ===\n"
            f"Período: {inicio_semana.strftime('%d/%m')} a {hoje.strftime('%d/%m/%Y')}\n"
            f"Carteira total: {total_carteira} clientes\n"
            f"\n=== VENDAS DA SEMANA ===\n"
            f"Pedidos realizados: {qtd_vendas_semana}\n"
            f"Volume total: {_formatar_moeda(total_vendas_semana)}\n"
            f"\n=== CLIENTES EM RISCO (VERMELHO/LARANJA) ===\n"
            f"Total em risco: {len(clientes_risco)}\n"
            f"{linhas_risco or '  (nenhum cliente em risco)'}\n"
            f"\n=== FOLLOW-UPS VENCIDOS ===\n"
            f"Total: {followup_vencidos}\n"
            f"\n=== TOP 5 OPORTUNIDADES (por score) ===\n"
            f"{linhas_oportunidades or '  (sem oportunidades mapeadas)'}"
        )

        prompt_usuario = (
            f"Gere o resumo semanal de performance para o consultor {consultor_norm}:\n\n"
            f"{contexto_semana}"
        )

        logger.info(
            "Gerando resumo semanal | consultor=%s vendas=%d volume=%s",
            consultor_norm,
            qtd_vendas_semana,
            _formatar_moeda(total_vendas_semana),
        )

        texto, tokens = await _call_claude(
            system=_SYSTEM_RESUMO_SEMANAL,
            user=prompt_usuario,
            max_tokens=_MAX_TOKENS_RESUMO,
        )

        return {
            "consultor": consultor_norm,
            "periodo": f"{inicio_semana.strftime('%d/%m')} a {hoje.strftime('%d/%m/%Y')}",
            "resumo": texto,
            "tokens_usados": tokens,
            "metricas": {
                "total_carteira": total_carteira,
                "vendas_semana_qtd": qtd_vendas_semana,
                "vendas_semana_volume": total_vendas_semana,
                "clientes_em_risco": len(clientes_risco),
                "followups_vencidos": followup_vencidos,
            },
            "ia_configurada": bool(ANTHROPIC_API_KEY),
        }


# ---------------------------------------------------------------------------
# Instância singleton (padrão dos outros services do projeto)
# ---------------------------------------------------------------------------

ia_service = IAService()
