"""
CRM VITAO360 — Serviço de Inteligência Artificial (IA Service)

Gera briefings pré-ligação, rascunhos de mensagens WhatsApp, resumos semanais,
scores de churn, sugestões de produto e mensagens WA automáticas por situação,
utilizando o modelo Claude via API Anthropic.

Comportamento sem chave configurada:
  - Retorna mensagem explicativa em vez de levantar exceção (graceful degradation).
  - Fallback local usando templates baseados na situação do cliente.
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
from backend.app.models.produto import Produto
from backend.app.models.venda import Venda
from backend.app.models.venda_item import VendaItem

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
_MAX_TOKENS_BRIEFING: int = 1536
_MAX_TOKENS_WHATSAPP: int = 512
_MAX_TOKENS_RESUMO: int = 2048
_MAX_TOKENS_CHURN: int = 512
_MAX_TOKENS_PRODUTO: int = 768
_TIMEOUT_SEGUNDOS: float = 30.0

# Mensagem exibida quando a chave não está configurada
_MSG_SEM_CHAVE: str = "[IA não configurada — defina ANTHROPIC_API_KEY no .env]"

# ---------------------------------------------------------------------------
# Prompts do sistema
# ---------------------------------------------------------------------------

_SYSTEM_BRIEFING: str = (
    "Você é o assistente de inteligência comercial da VITAO Alimentos, "
    "distribuidora B2B de alimentos naturais.\n"
    "Gere um briefing pré-ligação completo e orientado a ação para o consultor comercial.\n"
    "Estrutura obrigatória:\n"
    "  1) QUEM É O CLIENTE (1 linha: nome, cidade/UF, consultor)\n"
    "  2) SITUAÇÃO ATUAL (score, sinaleiro, prioridade, temperatura, dias sem compra)\n"
    "  3) HISTÓRICO RECENTE (últimas compras: datas, valores, produtos se disponível)\n"
    "  4) ÚLTIMO CONTATO (data, canal, resultado do atendimento)\n"
    "  5) AÇÃO RECOMENDADA (o que fazer nesta ligação — específico, não genérico)\n"
    "  6) SCRIPT SUGERIDO (3-4 linhas que o consultor pode falar)\n"
    "Tom: direto, prático, orientado a resultado. Sem floreios. Sem markdown excessivo."
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
    "  1) Performance da semana (clientes contactados, vendas realizadas, volume R$)\n"
    "  2) Clientes em risco que precisam de atenção (sinaleiro VERMELHO/LARANJA)\n"
    "  3) Top 3 oportunidades para a próxima semana\n"
    "  4) Recomendação de foco para o próximo período\n"
    "Tom: gerencial, analítico, orientado a decisão. Máximo 250 palavras."
)

_SYSTEM_CHURN: str = (
    "Você é o analista de churn da VITAO Alimentos, distribuidora B2B de alimentos naturais.\n"
    "Analise os dados do cliente e gere uma recomendação de retenção objetiva.\n"
    "Regras:\n"
    "  - Máximo 3 frases de recomendação\n"
    "  - Cite especificamente os fatores de risco identificados\n"
    "  - Sugira ação concreta para o consultor realizar hoje\n"
    "  - NÃO repita dados já apresentados — apenas insights e ações"
)

_SYSTEM_PRODUTO: str = (
    "Você é o especialista em cross-sell da VITAO Alimentos, distribuidora B2B de alimentos naturais.\n"
    "Com base no histórico de compras do cliente, sugira estratégia de cross-sell e up-sell.\n"
    "Regras:\n"
    "  - Explique a lógica de cada sugestão em 1 frase\n"
    "  - Foque em produtos complementares às categorias já compradas\n"
    "  - Máximo 2 parágrafos de estratégia\n"
    "  - NÃO inventar produtos — use apenas os que constam no contexto"
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

    # Últimas 5 vendas (R4: tabela separada, só valores positivos)
    linhas.append("")
    linhas.append("=== ÚLTIMAS VENDAS (até 5) ===")
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
# Templates de fallback local (sem ANTHROPIC_API_KEY)
# ---------------------------------------------------------------------------

def _template_briefing_local(cliente: Cliente, ultimas_interacoes: list[LogInteracao], ultimas_vendas: list[Venda]) -> str:
    """
    Gera briefing local quando ANTHROPIC_API_KEY não está configurada.
    Baseado na situação, sinaleiro e histórico do cliente.
    """
    nome = cliente.nome_fantasia or cliente.razao_social or cliente.cnpj
    situacao = cliente.situacao or "desconhecida"
    sinaleiro = cliente.sinaleiro or "—"
    score = f"{cliente.score:.0f}" if cliente.score is not None else "—"
    prioridade = cliente.prioridade or "—"
    temperatura = cliente.temperatura or "—"
    dias_sem_compra = cliente.dias_sem_compra or 0

    # Último contato
    ultimo_contato = "nenhum contato registrado"
    if ultimas_interacoes:
        ult = ultimas_interacoes[0]
        ultimo_contato = (
            f"{_formatar_data(ult.data_interacao)} — {ult.resultado} "
            f"(canal: {ult.tipo_contato or 'não informado'})"
        )

    # Última compra
    ultima_compra = "nenhuma compra registrada"
    if ultimas_vendas:
        v = ultimas_vendas[0]
        ultima_compra = (
            f"{_formatar_data(v.data_pedido)} — {_formatar_moeda(v.valor_pedido)} "
            f"(pedido {v.numero_pedido or 'sem número'})"
        )

    # Sugestão de abordagem por situação
    sugestao_map = {
        "ATIVO": f"Cliente ativo há {dias_sem_compra} dias sem novo pedido. Verificar necessidade de reposição e apresentar novidades.",
        "INAT.REC": f"Cliente inativo recente há {dias_sem_compra} dias. Abordar com oferta de reativação focada nas categorias que mais comprava.",
        "INAT.ANT": f"Cliente inativo antigo há {dias_sem_compra} dias. Contato de retomada — apresentar a VITAO novamente com portfólio atualizado.",
        "PROSPECT": "Prospect em prospecção. Apresentar VITAO Alimentos e portfólio de produtos naturais. Qualificar necessidade e volume.",
        "EM_RISCO": f"Cliente em risco — {dias_sem_compra} dias sem compra. Prioridade alta: contato urgente para entender motivo de distância.",
    }
    sugestao = sugestao_map.get(situacao, f"Verificar situação do cliente ({situacao}) e definir próximo passo.")

    # Script sugerido por situação
    script_map = {
        "ATIVO": (
            f"'Bom dia, falo com {nome}? Sou [seu nome] da VITAO. "
            f"Passando para checar se precisam repor estoque — nosso último pedido foi em {ultima_compra}. "
            "Tenho algumas novidades que podem te interessar. Tem 5 minutos?'"
        ),
        "INAT.REC": (
            f"'Olá {nome}, tudo bem? Sou [seu nome] da VITAO. "
            f"Percebi que faz um tempo que não pedimos juntos — nosso último foi em {ultima_compra}. "
            "Queria entender se surgiu algum problema ou se posso te apresentar nossas novidades. Quando podemos conversar?'"
        ),
        "INAT.ANT": (
            f"'Bom dia, falo com {nome}? Sou [seu nome] da VITAO Alimentos. "
            "Trabalhamos com linha completa de alimentos naturais e estávamos parceiros antes. "
            "Gostaríamos de apresentar nosso portfólio atualizado. Teria interesse em receber nossa tabela?'"
        ),
        "PROSPECT": (
            f"'Olá {nome}, sou [seu nome] da VITAO Alimentos. "
            "Trabalhamos com distribuição B2B de alimentos naturais — granolas, frutas secas, cereais e proteínas. "
            "Vi que vocês trabalham com esse segmento e gostaríamos de apresentar nossa proposta. Tem disponibilidade?'"
        ),
        "EM_RISCO": (
            f"'Olá {nome}, sou [seu nome] da VITAO. "
            "Notei que faz um tempo sem pedidos e quero garantir que tudo está bem. "
            "Houve algum problema com nosso serviço ou produto? Gostaria de entender para poder ajudar.'"
        ),
    }
    script = script_map.get(situacao, f"'Olá {nome}, sou [seu nome] da VITAO. Gostaria de conversar sobre nossa parceria. Quando seria um bom momento?'")

    return (
        f"CLIENTE: {nome} | {cliente.cidade or '—'}/{cliente.uf or '—'} | Consultor: {cliente.consultor or '—'}\n\n"
        f"SITUAÇÃO: {situacao} | Sinaleiro: {sinaleiro} | Score: {score}/100 | Prioridade: {prioridade} | Temperatura: {temperatura}\n"
        f"Dias sem compra: {dias_sem_compra} | Curva ABC: {cliente.curva_abc or '—'} | N° compras: {cliente.n_compras or 0}\n\n"
        f"HISTÓRICO RECENTE:\n"
        f"  Última compra: {ultima_compra}\n"
        f"  Último contato: {ultimo_contato}\n"
        f"  Valor último pedido: {_formatar_moeda(cliente.valor_ultimo_pedido)}\n\n"
        f"AÇÃO RECOMENDADA: {sugestao}\n\n"
        f"SCRIPT SUGERIDO:\n{script}\n\n"
        "[Briefing gerado por template local — configure ANTHROPIC_API_KEY para IA completa]"
    )


def _template_mensagem_wa_local(cliente: Cliente, situacao_norm: str) -> str:
    """
    Gera mensagem WhatsApp por template local baseado na situação do cliente.
    """
    nome = cliente.nome_fantasia or cliente.razao_social or "cliente"
    dias = cliente.dias_sem_compra or 0
    valor_ult = _formatar_moeda(cliente.valor_ultimo_pedido)

    templates = {
        "ATIVO": {
            "mensagem": (
                f"Olá *{nome}*! Tudo bem?\n\n"
                f"Passando para verificar se precisam de reposição no estoque. "
                f"Nosso último pedido foi de {valor_ult} e queremos garantir que não fique sem produto. 😊\n\n"
                "Posso te enviar nossa tabela atualizada ou prefere que eu ligue?"
            ),
            "tom": "relacionamento",
            "contexto": f"Cliente ATIVO há {dias} dias sem novo pedido",
        },
        "INAT.REC": {
            "mensagem": (
                f"Olá *{nome}*, tudo certo?\n\n"
                f"Sentimos sua falta! Faz {dias} dias do nosso último pedido e gostaríamos de retomar a parceria. "
                "Temos novidades no portfólio e condições especiais para clientes como vocês.\n\n"
                "Quando seria um bom momento para conversar? 🌿"
            ),
            "tom": "reativação",
            "contexto": f"Cliente INAT.REC há {dias} dias sem compra",
        },
        "INAT.ANT": {
            "mensagem": (
                f"Olá *{nome}*!\n\n"
                "Sou [seu nome] da VITAO Alimentos. Trabalhamos com distribuição de alimentos naturais — "
                "granolas, frutas secas, cereais e muito mais.\n\n"
                "Gostaríamos de apresentar nosso portfólio atualizado e verificar se faz sentido retomar a parceria. "
                "Teria disponibilidade para uma conversa rápida?"
            ),
            "tom": "retomada",
            "contexto": f"Cliente inativo há {dias} dias — contato de retomada",
        },
        "PROSPECT": {
            "mensagem": (
                f"Olá *{nome}*!\n\n"
                "Sou [seu nome] da VITAO Alimentos, distribuidora B2B de alimentos naturais. "
                "Trabalhamos com granolas, frutas secas, cereais integrais, proteínas e muito mais.\n\n"
                "Gostaria de apresentar nosso portfólio e verificar se podemos ser parceiros. "
                "Posso te enviar nosso catálogo?"
            ),
            "tom": "prospecção",
            "contexto": "Primeiro contato com prospect",
        },
        "EM_RISCO": {
            "mensagem": (
                f"Olá *{nome}*, tudo bem?\n\n"
                "Notei que faz um tempo sem pedidos e quero garantir que está tudo OK com nossa parceria. "
                f"Nosso último pedido foi de {valor_ult}.\n\n"
                "Houve algum problema? Gostaria de conversar para entender como posso ajudar."
            ),
            "tom": "retenção urgente",
            "contexto": f"Cliente EM_RISCO há {dias} dias sem compra",
        },
    }

    template = templates.get(situacao_norm, templates["ATIVO"])
    return template


def _template_churn_local(
    cliente: Cliente,
    risco_pct: float,
    nivel: str,
    fatores: list[str],
) -> str:
    """Gera recomendação de churn por template local."""
    nome = cliente.nome_fantasia or cliente.razao_social or cliente.cnpj
    fatores_str = "; ".join(fatores) if fatores else "dados insuficientes para análise"

    if nivel == "CRITICO":
        return (
            f"Cliente {nome} em risco CRÍTICO ({risco_pct:.0f}%). Fatores: {fatores_str}. "
            "Contato imediato do consultor responsável — ligar hoje, oferecer condição especial de reativação. "
            "Se não houver retorno em 48h, escalar para gerência."
        )
    elif nivel == "ALTO":
        return (
            f"Cliente {nome} com risco ALTO de churn ({risco_pct:.0f}%). Fatores: {fatores_str}. "
            "Agendar ligação nesta semana para verificar situação e oferecer apoio. "
            "Considerar desconto ou prazo especial para reativação."
        )
    elif nivel == "MEDIO":
        return (
            f"Cliente {nome} com risco MÉDIO ({risco_pct:.0f}%). Fatores: {fatores_str}. "
            "Monitorar na próxima semana — enviar mensagem WhatsApp para manter relacionamento. "
            "Verificar se há novidades no portfólio que possam despertar interesse."
        )
    else:
        return (
            f"Cliente {nome} com risco BAIXO ({risco_pct:.0f}%). Fatores: {fatores_str}. "
            "Manter ritmo atual de relacionamento — follow-up no prazo padrão. "
            "Aproveitar próxima interação para apresentar novidades e cross-sell."
        )


# ---------------------------------------------------------------------------
# Serviço principal
# ---------------------------------------------------------------------------

class IAService:
    """
    Serviço de Inteligência Artificial do CRM VITAO360.

    Métodos públicos (todos assíncronos):
      - gerar_briefing: briefing pré-ligação expandido para um cliente
      - gerar_mensagem_whatsapp: rascunho de mensagem WA para um objetivo
      - gerar_mensagem_wa_automatica: mensagem WA automática por situação do cliente
      - gerar_resumo_semanal: resumo executivo semanal por consultor
      - calcular_churn_risk: score de risco de churn para um cliente
      - sugerir_produtos: cross-sell/up-sell baseado em histórico de compras
    """

    # ------------------------------------------------------------------
    # Método 1: Briefing pré-ligação expandido
    # ------------------------------------------------------------------

    async def gerar_briefing(self, cnpj: str, db: Session) -> dict[str, Any]:
        """
        Gera um briefing pré-ligação completo para o consultor sobre um cliente.

        Inclui: histórico de compras (últimas 5), último contato, score/prioridade/temperatura,
        sugestão de abordagem e script de venda sugerido.

        Args:
            cnpj: CNPJ do cliente (14 dígitos, aceita formatado).
            db:   Sessão SQLAlchemy ativa (injetada pelo FastAPI).

        Returns:
            dict com:
              - briefing (str): texto gerado pelo Claude (ou template local)
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
            .limit(5)
            .all()
        )

        logger.info(
            "Gerando briefing | cnpj=%s nome=%s score=%.1f",
            cnpj_n,
            cliente.nome_fantasia or "—",
            cliente.score or 0.0,
        )

        # Sem API key: usar template local rico
        if not ANTHROPIC_API_KEY:
            briefing_texto = _template_briefing_local(cliente, ultimas_interacoes, ultimas_vendas)
            return {
                "cnpj": cnpj_n,
                "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
                "briefing": briefing_texto,
                "tokens_usados": 0,
                "cached": False,
                "ia_configurada": False,
            }

        contexto = _construir_contexto_cliente(cliente, ultimas_interacoes, ultimas_vendas)
        prompt_usuario = (
            f"Gere o briefing pré-ligação para o cliente abaixo:\n\n{contexto}"
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
            "ia_configurada": True,
        }

    # ------------------------------------------------------------------
    # Método 2: Rascunho de mensagem WhatsApp (objetivo livre)
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

        logger.info(
            "Gerando mensagem WA | cnpj=%s objetivo=%.80s",
            cnpj_n,
            objetivo,
        )

        contexto = _construir_contexto_cliente(cliente, ultimas_interacoes, ultimas_vendas)

        prompt_usuario = (
            f"Objetivo desta mensagem: {objetivo}\n\n"
            f"Dados do cliente:\n{contexto}\n\n"
            "Escreva a mensagem WhatsApp que o consultor deve enviar."
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
    # Método 3: Mensagem WhatsApp automática por situação
    # ------------------------------------------------------------------

    async def gerar_mensagem_wa_automatica(
        self, cnpj: str, db: Session
    ) -> dict[str, Any]:
        """
        Gera mensagem WhatsApp contextual automática baseada na situação atual do cliente.

        Diferente de gerar_mensagem_whatsapp (que recebe objetivo livre),
        este método usa a situação/resultado do banco para determinar
        automaticamente o tom e conteúdo da mensagem.

        Situações mapeadas:
          - ATIVO + PÓS-VENDA: mensagem de relacionamento/reposição
          - INAT.REC: mensagem de reativação
          - INAT.ANT: mensagem de retomada
          - PROSPECT: apresentação comercial
          - EM_RISCO: mensagem de retenção urgente

        Returns:
            dict com: mensagem, tom, contexto, cnpj, nome_cliente,
                      ia_configurada, tokens_usados

        Raises:
            ValueError: se o CNPJ não for encontrado.
        """
        cnpj_n = _normalizar_cnpj(cnpj)

        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj_n).first()
        if not cliente:
            raise ValueError(f"Cliente CNPJ {cnpj_n} não encontrado")

        situacao = (cliente.situacao or "ATIVO").upper()

        logger.info(
            "Gerando mensagem WA automática | cnpj=%s situacao=%s",
            cnpj_n,
            situacao,
        )

        # Sem API key: usar template local por situação
        if not ANTHROPIC_API_KEY:
            resultado_template = _template_mensagem_wa_local(cliente, situacao)
            return {
                "cnpj": cnpj_n,
                "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
                "mensagem": resultado_template["mensagem"],
                "tom": resultado_template["tom"],
                "contexto": resultado_template["contexto"],
                "tokens_usados": 0,
                "ia_configurada": False,
            }

        # Com API key: contexto reduzido para WA automático
        ultimas_vendas = (
            db.query(Venda)
            .filter(Venda.cnpj == cnpj_n)
            .order_by(Venda.data_pedido.desc())
            .limit(2)
            .all()
        )
        ultimas_interacoes = (
            db.query(LogInteracao)
            .filter(LogInteracao.cnpj == cnpj_n)
            .order_by(LogInteracao.data_interacao.desc())
            .limit(2)
            .all()
        )

        contexto = _construir_contexto_cliente(cliente, ultimas_interacoes, ultimas_vendas)

        tom_map = {
            "ATIVO": "relacionamento e reposição",
            "INAT.REC": "reativação com oferta especial",
            "INAT.ANT": "retomada de parceria",
            "PROSPECT": "apresentação comercial",
            "EM_RISCO": "retenção urgente",
        }
        tom_desejado = tom_map.get(situacao, "relacionamento comercial")

        prompt_usuario = (
            f"Gere uma mensagem WhatsApp com tom de '{tom_desejado}' para o cliente abaixo.\n"
            f"A mensagem será enviada diretamente pelo consultor — deve ser natural e não parecer automática.\n\n"
            f"Dados do cliente:\n{contexto}\n\n"
            "Após a mensagem, forneça em nova linha:\n"
            "TOM: [tom da mensagem]\n"
            "CONTEXTO: [contexto resumido em 1 linha]"
        )

        texto_completo, tokens = await _call_claude(
            system=_SYSTEM_WHATSAPP,
            user=prompt_usuario,
            max_tokens=_MAX_TOKENS_WHATSAPP,
        )

        # Extrair campos do texto gerado
        mensagem = texto_completo
        tom = tom_desejado
        contexto_resumo = f"Situação: {situacao}, {cliente.dias_sem_compra or 0} dias sem compra"

        if "TOM:" in texto_completo:
            partes = texto_completo.split("TOM:")
            mensagem = partes[0].strip()
            resto = partes[1].strip()
            if "CONTEXTO:" in resto:
                tom_linha, ctx_linha = resto.split("CONTEXTO:", 1)
                tom = tom_linha.strip()
                contexto_resumo = ctx_linha.strip()
            else:
                tom = resto.strip()

        return {
            "cnpj": cnpj_n,
            "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
            "mensagem": mensagem,
            "tom": tom,
            "contexto": contexto_resumo,
            "tokens_usados": tokens,
            "ia_configurada": True,
        }

    # ------------------------------------------------------------------
    # Método 4: Resumo semanal por consultor
    # ------------------------------------------------------------------

    async def gerar_resumo_semanal(
        self, consultor: str, db: Session
    ) -> dict[str, Any]:
        """
        Gera um resumo executivo da semana corrente para um consultor.

        Agrega automaticamente:
          - Clientes contactados (log_interacoes últimos 7 dias)
          - Vendas dos últimos 7 dias (R4: tabela vendas)
          - Pipeline: quantos clientes em cada estágio do funil
          - Top 3 clientes por score para focar na próxima semana
          - Clientes em risco (sinaleiro VERMELHO ou LARANJA)
          - Clientes com follow-up vencido

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

        # R4: clientes contactados na semana (tabela log_interacoes — sem R$)
        clientes_contactados_semana = (
            db.query(LogInteracao.cnpj)
            .filter(
                LogInteracao.consultor == consultor_norm,
                LogInteracao.data_interacao >= datetime.combine(inicio_semana, datetime.min.time()),
            )
            .distinct()
            .count()
        )

        # Pipeline: distribuição por estágio do funil
        from sqlalchemy import func as sqlfunc
        pipeline_dist = (
            db.query(Cliente.estagio_funil, sqlfunc.count(Cliente.id).label("qtd"))
            .filter(Cliente.consultor == consultor_norm)
            .filter(Cliente.estagio_funil.isnot(None))
            .group_by(Cliente.estagio_funil)
            .all()
        )
        pipeline_dict = {row.estagio_funil: row.qtd for row in pipeline_dist}

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

        # Top 3 clientes por score (foco próxima semana)
        top_score = (
            db.query(Cliente)
            .filter(
                Cliente.consultor == consultor_norm,
                Cliente.situacao.in_(["ATIVO", "EM_RISCO", "INAT.REC"]),
            )
            .order_by(Cliente.score.desc().nulls_last())
            .limit(3)
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

        linhas_top3 = "\n".join(
            f"  - {c.nome_fantasia or c.cnpj} | Score: {c.score or 0:.0f} | "
            f"Situação: {c.situacao} | Fase: {c.fase or '—'} | "
            f"Ação: {c.acao_futura or 'não definida'}"
            for c in top_score
        )

        pipeline_resumo = " | ".join(f"{k}: {v}" for k, v in pipeline_dict.items()) if pipeline_dict else "sem dados de funil"

        contexto_semana = (
            f"=== RESUMO SEMANAL — {consultor_norm} ===\n"
            f"Período: {inicio_semana.strftime('%d/%m')} a {hoje.strftime('%d/%m/%Y')}\n"
            f"Carteira total: {total_carteira} clientes\n"
            f"\n=== CONTACTADOS NA SEMANA (LOG) ===\n"
            f"Clientes contactados: {clientes_contactados_semana}\n"
            f"\n=== VENDAS DA SEMANA ===\n"
            f"Pedidos realizados: {qtd_vendas_semana}\n"
            f"Volume total: {_formatar_moeda(total_vendas_semana)}\n"
            f"\n=== PIPELINE (por estágio) ===\n"
            f"{pipeline_resumo}\n"
            f"\n=== CLIENTES EM RISCO (VERMELHO/LARANJA) ===\n"
            f"Total em risco: {len(clientes_risco)}\n"
            f"{linhas_risco or '  (nenhum cliente em risco)'}\n"
            f"\n=== FOLLOW-UPS VENCIDOS ===\n"
            f"Total: {followup_vencidos}\n"
            f"\n=== TOP 3 PARA FOCAR NA PRÓXIMA SEMANA ===\n"
            f"{linhas_top3 or '  (sem oportunidades mapeadas)'}"
        )

        prompt_usuario = (
            f"Gere o resumo semanal de performance para o consultor {consultor_norm}:\n\n"
            f"{contexto_semana}"
        )

        logger.info(
            "Gerando resumo semanal | consultor=%s contactados=%d vendas=%d volume=%s",
            consultor_norm,
            clientes_contactados_semana,
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
                "clientes_contactados_semana": clientes_contactados_semana,
                "vendas_semana_qtd": qtd_vendas_semana,
                "vendas_semana_volume": total_vendas_semana,
                "clientes_em_risco": len(clientes_risco),
                "followups_vencidos": followup_vencidos,
                "pipeline": pipeline_dict,
                "top3_proxima_semana": [
                    {
                        "cnpj": c.cnpj,
                        "nome": c.nome_fantasia or c.razao_social or c.cnpj,
                        "score": c.score or 0.0,
                        "situacao": c.situacao,
                        "acao_futura": c.acao_futura or "não definida",
                    }
                    for c in top_score
                ],
            },
            "ia_configurada": bool(ANTHROPIC_API_KEY),
        }

    # ------------------------------------------------------------------
    # Método 5: Score de risco de churn
    # ------------------------------------------------------------------

    async def calcular_churn_risk(self, cnpj: str, db: Session) -> dict[str, Any]:
        """
        Calcula o score de risco de churn para um cliente específico.

        Fatores considerados:
          - Dias sem compra vs ciclo médio histórico
          - Tendência de ticket (queda no valor dos pedidos)
          - Frequência decrescente de compras
          - Sinaleiro atual (VERMELHO/LARANJA aumenta risco)
          - Temperatura (CRITICO/FRIO aumenta risco)
          - Situação atual (INAT.REC/INAT.ANT = risco máximo)

        Returns:
            dict com:
              - risco_pct (float): percentual de risco 0-100
              - nivel (str): "BAIXO" | "MEDIO" | "ALTO" | "CRITICO"
              - fatores (list[str]): lista de fatores que contribuíram ao risco
              - recomendacao (str): texto com ação recomendada
              - cnpj (str): CNPJ normalizado
              - nome_cliente (str): nome fantasia
              - ia_configurada (bool): se usou API ou template local

        Raises:
            ValueError: se o CNPJ não for encontrado.
        """
        cnpj_n = _normalizar_cnpj(cnpj)

        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj_n).first()
        if not cliente:
            raise ValueError(f"Cliente CNPJ {cnpj_n} não encontrado")

        # R4: últimas vendas para análise de tendência
        ultimas_vendas = (
            db.query(Venda)
            .filter(Venda.cnpj == cnpj_n)
            .order_by(Venda.data_pedido.desc())
            .limit(10)
            .all()
        )

        # ---------- Cálculo do score de churn ----------
        risco_pct: float = 0.0
        fatores: list[str] = []

        # Fator 1: situação atual (peso 40%)
        situacao = (cliente.situacao or "ATIVO").upper()
        situacao_risco = {
            "INAT.ANT": 40.0,
            "INAT.REC": 35.0,
            "EM_RISCO": 30.0,
            "PROSPECT": 20.0,
            "ATIVO": 5.0,
        }
        risco_situacao = situacao_risco.get(situacao, 15.0)
        risco_pct += risco_situacao
        if risco_situacao >= 30:
            fatores.append(f"situação {situacao} (alto risco)")

        # Fator 2: dias sem compra vs ciclo médio (peso 30%)
        dias_sem_compra = cliente.dias_sem_compra or 0
        ciclo_medio = cliente.ciclo_medio or 30.0
        if ciclo_medio > 0 and dias_sem_compra > 0:
            ratio_ciclo = dias_sem_compra / ciclo_medio
            risco_ciclo = min(ratio_ciclo * 15.0, 30.0)
            risco_pct += risco_ciclo
            if ratio_ciclo > 1.5:
                fatores.append(f"{dias_sem_compra} dias sem compra ({ratio_ciclo:.1f}x o ciclo médio de {ciclo_medio:.0f} dias)")
            elif ratio_ciclo > 1.0:
                fatores.append(f"{dias_sem_compra} dias sem compra (acima do ciclo médio)")

        # Fator 3: sinaleiro (peso 15%)
        sinaleiro = (cliente.sinaleiro or "VERDE").upper()
        sinaleiro_risco = {
            "VERMELHO": 15.0,
            "LARANJA": 10.0,
            "AMARELO": 5.0,
            "VERDE": 0.0,
            "ROXO": 5.0,  # ROXO = prospect, risco moderado
        }
        risco_sinaleiro = sinaleiro_risco.get(sinaleiro, 5.0)
        risco_pct += risco_sinaleiro
        if risco_sinaleiro >= 10:
            fatores.append(f"sinaleiro {sinaleiro}")

        # Fator 4: temperatura (peso 10%)
        temperatura = (cliente.temperatura or "MORNO").upper()
        temperatura_risco = {
            "CRITICO": 10.0,
            "FRIO": 7.0,
            "MORNO": 3.0,
            "QUENTE": 0.0,
        }
        risco_temperatura = temperatura_risco.get(temperatura, 3.0)
        risco_pct += risco_temperatura
        if risco_temperatura >= 7:
            fatores.append(f"temperatura {temperatura}")

        # Fator 5: tendência de ticket decrescente (peso 5%)
        if len(ultimas_vendas) >= 3:
            valores = [v.valor_pedido for v in ultimas_vendas[:5]]
            if len(valores) >= 2:
                media_recente = sum(valores[:2]) / 2
                media_antiga = sum(valores[2:]) / max(len(valores[2:]), 1)
                if media_antiga > 0 and media_recente < media_antiga * 0.7:
                    risco_pct += 5.0
                    queda_pct = (1 - media_recente / media_antiga) * 100
                    fatores.append(f"ticket médio caiu {queda_pct:.0f}% nas últimas compras")

        # Normalizar entre 0-100
        risco_pct = min(risco_pct, 100.0)

        # Determinar nível
        if risco_pct >= 70:
            nivel = "CRITICO"
        elif risco_pct >= 50:
            nivel = "ALTO"
        elif risco_pct >= 30:
            nivel = "MEDIO"
        else:
            nivel = "BAIXO"

        if not fatores:
            fatores.append("comportamento de compra dentro do padrão normal")

        logger.info(
            "Churn risk calculado | cnpj=%s risco=%.1f nivel=%s",
            cnpj_n,
            risco_pct,
            nivel,
        )

        # Gerar recomendação via IA ou template local
        if not ANTHROPIC_API_KEY:
            recomendacao = _template_churn_local(cliente, risco_pct, nivel, fatores)
            return {
                "cnpj": cnpj_n,
                "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
                "risco_pct": round(risco_pct, 1),
                "nivel": nivel,
                "fatores": fatores,
                "recomendacao": recomendacao,
                "ia_configurada": False,
            }

        # Com API key: gerar recomendação contextual
        nome = cliente.nome_fantasia or cliente.razao_social or cnpj_n
        contexto_churn = (
            f"Cliente: {nome} | Situação: {situacao} | Sinaleiro: {sinaleiro}\n"
            f"Score geral: {cliente.score or 0:.0f}/100 | Temperatura: {temperatura}\n"
            f"Dias sem compra: {dias_sem_compra} | Ciclo médio: {ciclo_medio:.0f} dias\n"
            f"Score de churn calculado: {risco_pct:.0f}% | Nível: {nivel}\n"
            f"Fatores identificados: {'; '.join(fatores)}\n"
            f"Faturamento total: {_formatar_moeda(cliente.faturamento_total)}\n"
            f"N° compras históricas: {cliente.n_compras or 0}"
        )

        prompt_usuario = (
            f"Analise o risco de churn do cliente abaixo e forneça recomendação de retenção:\n\n"
            f"{contexto_churn}"
        )

        texto, tokens = await _call_claude(
            system=_SYSTEM_CHURN,
            user=prompt_usuario,
            max_tokens=_MAX_TOKENS_CHURN,
        )

        return {
            "cnpj": cnpj_n,
            "nome_cliente": nome,
            "risco_pct": round(risco_pct, 1),
            "nivel": nivel,
            "fatores": fatores,
            "recomendacao": texto,
            "ia_configurada": True,
        }

    # ------------------------------------------------------------------
    # Método 6: Sugestão de produto (cross-sell/up-sell)
    # ------------------------------------------------------------------

    async def sugerir_produtos(self, cnpj: str, db: Session) -> dict[str, Any]:
        """
        Sugere produtos para cross-sell e up-sell com base no histórico de compras.

        Busca os últimos itens de venda do cliente (via venda_itens + produtos),
        identifica as categorias mais compradas e sugere produtos complementares
        ou da mesma categoria que o cliente ainda não comprou.

        Returns:
            dict com:
              - produtos_sugeridos (list): [{id, nome, categoria, motivo}]
              - estrategia (str): texto com a estratégia de abordagem
              - categorias_frequentes (list[str]): categorias mais compradas
              - cnpj (str): CNPJ normalizado
              - nome_cliente (str): nome fantasia
              - ia_configurada (bool): se usou API ou template local

        Raises:
            ValueError: se o CNPJ não for encontrado.
        """
        cnpj_n = _normalizar_cnpj(cnpj)

        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj_n).first()
        if not cliente:
            raise ValueError(f"Cliente CNPJ {cnpj_n} não encontrado")

        # R4: buscar vendas recentes com seus itens
        ultimas_vendas = (
            db.query(Venda)
            .filter(Venda.cnpj == cnpj_n)
            .order_by(Venda.data_pedido.desc())
            .limit(10)
            .all()
        )

        venda_ids = [v.id for v in ultimas_vendas]

        # Buscar itens das últimas vendas com produtos
        itens_comprados: list[VendaItem] = []
        produtos_comprados_ids: set[int] = set()
        categorias_compradas: dict[str, int] = {}

        if venda_ids:
            itens_comprados = (
                db.query(VendaItem)
                .filter(VendaItem.venda_id.in_(venda_ids))
                .all()
            )

            for item in itens_comprados:
                if item.produto_id:
                    produtos_comprados_ids.add(item.produto_id)

        # Carregar produtos dos itens para descobrir categorias
        if produtos_comprados_ids:
            produtos_cliente = (
                db.query(Produto)
                .filter(Produto.id.in_(produtos_comprados_ids))
                .all()
            )
            for p in produtos_cliente:
                if p.categoria:
                    categorias_compradas[p.categoria] = categorias_compradas.get(p.categoria, 0) + 1

        # Categorias mais frequentes (top 3)
        categorias_frequentes = sorted(
            categorias_compradas.keys(),
            key=lambda c: categorias_compradas[c],
            reverse=True,
        )[:3]

        # Buscar produtos das mesmas categorias que o cliente NÃO comprou
        produtos_sugeridos_raw: list[Produto] = []
        if categorias_frequentes:
            produtos_sugeridos_raw = (
                db.query(Produto)
                .filter(
                    Produto.categoria.in_(categorias_frequentes),
                    Produto.ativo == True,  # noqa: E712
                    ~Produto.id.in_(produtos_comprados_ids) if produtos_comprados_ids else True,
                )
                .limit(10)
                .all()
            )

        # Se não tem histórico de categorias, sugerir produtos mais populares ativos
        if not produtos_sugeridos_raw:
            produtos_sugeridos_raw = (
                db.query(Produto)
                .filter(Produto.ativo == True)  # noqa: E712
                .limit(10)
                .all()
            )

        logger.info(
            "Sugestão de produto | cnpj=%s categorias=%s sugestoes=%d",
            cnpj_n,
            categorias_frequentes,
            len(produtos_sugeridos_raw),
        )

        # Montar lista de produtos sugeridos (até 5)
        produtos_sugeridos: list[dict[str, Any]] = []
        for p in produtos_sugeridos_raw[:5]:
            # Determinar motivo da sugestão
            if p.categoria in categorias_frequentes:
                posicao = categorias_frequentes.index(p.categoria) + 1
                motivo = f"mesma categoria ({p.categoria}) — {posicao}ª mais comprada pelo cliente"
            else:
                motivo = f"produto ativo do catálogo — categoria {p.categoria or 'geral'}"

            produtos_sugeridos.append({
                "id": p.id,
                "codigo": p.codigo,
                "nome": p.nome,
                "categoria": p.categoria or "sem categoria",
                "motivo": motivo,
                "preco_tabela": p.preco_tabela,
            })

        # Sem API key: gerar estratégia por template local
        if not ANTHROPIC_API_KEY:
            nome = cliente.nome_fantasia or cliente.razao_social or cnpj_n
            if categorias_frequentes:
                cats_str = ", ".join(categorias_frequentes)
                estrategia = (
                    f"Cliente {nome} tem histórico de compras nas categorias: {cats_str}. "
                    f"Estratégia recomendada: apresentar os {len(produtos_sugeridos)} produtos sugeridos "
                    "na próxima ligação, destacando a complementaridade com o que já compra. "
                    "Oferecer degustação ou amostra grátis para novidades da mesma linha."
                )
            else:
                estrategia = (
                    f"Cliente {nome} sem histórico de categorias definido. "
                    "Apresentar portfólio completo da VITAO e identificar necessidades. "
                    "Foco em granolas e cereais como porta de entrada do catálogo."
                )

            return {
                "cnpj": cnpj_n,
                "nome_cliente": nome,
                "produtos_sugeridos": produtos_sugeridos,
                "estrategia": estrategia,
                "categorias_frequentes": categorias_frequentes,
                "ia_configurada": False,
            }

        # Com API key: gerar estratégia contextual
        produtos_nomes = ", ".join(p["nome"] for p in produtos_sugeridos[:5]) if produtos_sugeridos else "sem sugestões disponíveis"
        historico_cats = ", ".join(f"{c} ({categorias_compradas.get(c, 0)} compras)" for c in categorias_frequentes) if categorias_frequentes else "sem histórico de categorias"

        contexto_produto = (
            f"Cliente: {cliente.nome_fantasia or cliente.razao_social or cnpj_n}\n"
            f"Situação: {cliente.situacao or 'não informada'} | Score: {cliente.score or 0:.0f}/100\n"
            f"Categorias mais compradas: {historico_cats}\n"
            f"Total de compras históricas: {cliente.n_compras or 0}\n"
            f"Produtos sugeridos para cross-sell: {produtos_nomes}\n"
            f"Faturamento acumulado: {_formatar_moeda(cliente.faturamento_total)}"
        )

        prompt_usuario = (
            f"Gere uma estratégia de cross-sell e up-sell para o cliente abaixo:\n\n"
            f"{contexto_produto}\n\n"
            "Explique como o consultor deve abordar esses produtos na próxima ligação."
        )

        texto, tokens = await _call_claude(
            system=_SYSTEM_PRODUTO,
            user=prompt_usuario,
            max_tokens=_MAX_TOKENS_PRODUTO,
        )

        return {
            "cnpj": cnpj_n,
            "nome_cliente": cliente.nome_fantasia or cliente.razao_social or cnpj_n,
            "produtos_sugeridos": produtos_sugeridos,
            "estrategia": texto,
            "categorias_frequentes": categorias_frequentes,
            "ia_configurada": True,
        }


# ---------------------------------------------------------------------------
# Instância singleton (padrão dos outros services do projeto)
# ---------------------------------------------------------------------------

ia_service = IAService()
