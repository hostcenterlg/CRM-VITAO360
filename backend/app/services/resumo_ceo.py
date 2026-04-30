"""
CRM VITAO360 — Resumo CEO (Onda 6 — ROMEO)

Gera Resumo CEO (1 página) a partir de ResultadoDDE.

Estratégia:
  - Se LLMClient tem provider disponível: usa LLM com prompt estruturado
  - Senão: template determinístico baseado nos dados do ResultadoDDE
  - Em AMBOS os casos: valida regex R$ contra ResultadoDDE — se divergir > 1%, marca SUSPEITO

REGRAS:
  R8 — Zero alucinação: NÃO inventa dados. Usa APENAS valores de ResultadoDDE.
  R5 — CNPJ: 14 dígitos, string.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, TYPE_CHECKING

from backend.app.services.llm_client import LLMClient

if TYPE_CHECKING:
    from backend.app.services.dde_engine import ResultadoDDE

# ---------------------------------------------------------------------------
# Prompt estruturado para LLM
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """Você é analista financeiro do CRM VITAO360.
Gere RESUMO CEO de 1 página sobre o cliente abaixo (ano {ano}).

Dados reais — NÃO INVENTE, use SÓ estes valores:
- Razão Social: {razao_social}
- CNPJ: {cnpj}
- Receita Bruta (L1): {l1}
- Receita Líquida (L11): {l11}
- Margem de Contribuição (L21): {l21}
- MC%: {mc_pct}
- Score Saúde (I9): {score}/100
- Veredito: {veredito}
- Descrição Veredito: {veredito_descricao}

REGRAS DE ESCRITA:
1. Português Brasileiro, tom executivo conciso
2. NUNCA invente número — use apenas os dados acima
3. Sem ressalvas vagas ("talvez", "pode ser") — declarativo
4. Estrutura obrigatória:
   DIAGNÓSTICO: 2-3 frases sobre situação atual
   ANOMALIAS: top 3 pontos de atenção identificados nos dados
   AÇÕES PRIORITÁRIAS: top 5 ações numeradas, priorizadas por impacto
   RECOMENDAÇÃO FINAL: 1 frase de encaminhamento executivo
5. Máximo 400 palavras

Inicie com: "RESUMO CEO — {razao_social}"
"""


def _formata_brl(valor: Optional[Decimal]) -> str:
    """Formata Decimal como R$ BRL ou '—' se None."""
    if valor is None:
        return "—"
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _formata_pct(valor: Optional[float]) -> str:
    """Formata float como percentual com 1 casa decimal ou '—' se None."""
    if valor is None:
        return "—"
    return f"{valor * 100:.1f}%"


def _get_linha_valor(dre: "ResultadoDDE", codigo: str) -> Optional[Decimal]:
    """Busca valor de uma linha da cascata pelo código (ex: 'L1', 'L11')."""
    for linha in dre.linhas:
        if linha.codigo == codigo:
            return linha.valor
    return None


def _build_prompt(dre: "ResultadoDDE", razao_social: str) -> str:
    """Monta prompt preenchido com dados reais do ResultadoDDE."""
    l1 = _get_linha_valor(dre, "L1")
    l11 = _get_linha_valor(dre, "L11")
    l21 = _get_linha_valor(dre, "L21")
    mc_pct = dre.indicadores.get("I2")
    score = dre.indicadores.get("I9")

    return _PROMPT_TEMPLATE.format(
        ano=dre.ano,
        razao_social=razao_social or "N/A",
        cnpj=dre.cnpj,
        l1=_formata_brl(l1),
        l11=_formata_brl(l11),
        l21=_formata_brl(l21),
        mc_pct=_formata_pct(mc_pct),
        score=f"{score:.1f}" if score is not None else "N/D",
        veredito=dre.veredito,
        veredito_descricao=dre.veredito_descricao,
    )


def _template_fallback(dre: "ResultadoDDE", razao_social: str) -> str:
    """
    Template determinístico — mesmo formato do LLM, sem inferência.
    Usado quando nenhum provider LLM estiver disponível.
    R8: NUNCA inventa dados.
    """
    l1 = _get_linha_valor(dre, "L1")
    l11 = _get_linha_valor(dre, "L11")
    l21 = _get_linha_valor(dre, "L21")
    mc_pct = dre.indicadores.get("I2")
    score = dre.indicadores.get("I9")
    inadimp_pct = dre.indicadores.get("I6")
    frete_pct = dre.indicadores.get("I4")
    devol_pct = dre.indicadores.get("I7")

    nome = razao_social or "N/A"
    score_str = f"{score:.1f}/100" if score is not None else "N/D"
    mc_str = _formata_pct(mc_pct)

    # Diagnóstico
    diagnostico_linhas = [
        f"Receita Bruta de {_formata_brl(l1)} com Receita Líquida de {_formata_brl(l11)} no período.",
        f"Margem de Contribuição de {_formata_brl(l21)} ({mc_str}) — veredito: {dre.veredito}.",
        f"Score de Saúde Financeira: {score_str}.",
    ]

    # Anomalias top 3
    anomalias = []
    if mc_pct is not None and mc_pct < 0:
        anomalias.append(f"Margem de Contribuição negativa ({mc_str}) — cliente destrói valor.")
    elif mc_pct is not None and mc_pct < 0.05:
        anomalias.append(f"Margem de Contribuição crítica ({mc_str}) — abaixo de 5%.")
    if inadimp_pct is not None and inadimp_pct > 0.05:
        anomalias.append(f"Inadimplência elevada ({_formata_pct(inadimp_pct)}) — risco de crédito.")
    if frete_pct is not None and frete_pct > 0.07:
        anomalias.append(f"Frete desproporcional ({_formata_pct(frete_pct)}) — comprime margem.")
    if devol_pct is not None and devol_pct > 0.05:
        anomalias.append(f"Taxa de devolução crítica ({_formata_pct(devol_pct)}).")
    if not anomalias:
        anomalias.append("Indicadores dentro dos parâmetros aceitáveis.")
    anomalias = anomalias[:3]

    # Ações priorizadas
    acoes = []
    if dre.veredito == "SUBSTITUIR":
        acoes.append("1. Iniciar processo de substituição ou inativação do cliente.")
    if dde_veredito_precisa_renegociar(dre):
        acoes.append(
            f"{'2' if acoes else '1'}. Renegociar contrato — margem atual ({mc_str}) abaixo do mínimo."
        )
    if frete_pct is not None and frete_pct > 0.05:
        acoes.append(f"{len(acoes)+1}. Otimizar frete CT-e — custo atual ({_formata_pct(frete_pct)}).")
    if inadimp_pct is not None and inadimp_pct > 0.03:
        acoes.append(f"{len(acoes)+1}. Bloquear crédito e acionar cobrança de débitos em aberto.")
    if dre.veredito == "REVISAR" and len(acoes) < 3:
        acoes.append(f"{len(acoes)+1}. Revisar mix de produtos — focar em SKUs de maior margem.")
    if len(acoes) < 3:
        acoes.append(f"{len(acoes)+1}. Monitorar evolução trimestral dos indicadores.")
    if not acoes:
        acoes.append("1. Manter condições atuais e monitorar evolução trimestral.")
    acoes = acoes[:5]

    # Recomendação final
    recomendacao_map = {
        "SUBSTITUIR": "Encaminhar para deliberação comercial imediata sobre continuidade do relacionamento.",
        "RENEGOCIAR": "Agendar reunião de renegociação contratual com urgência.",
        "REVISAR": "Incluir cliente na agenda de revisão do próximo ciclo trimestral.",
        "ALERTA_CREDITO": "Suspender crédito e acionar jurídico/financeiro para regularização.",
        "SAUDAVEL": "Manter condições e avaliar expansão de mix ou aumento de frequência.",
        "SEM_DADOS": "Completar coleta de dados para viabilizar análise conclusiva.",
    }
    recomendacao = recomendacao_map.get(dre.veredito, "Consultar gestão para definição de estratégia.")

    linhas = [
        f"RESUMO CEO — {nome}",
        "",
        "DIAGNÓSTICO:",
        *diagnostico_linhas,
        "",
        "ANOMALIAS:",
        *[f"- {a}" for a in anomalias],
        "",
        "AÇÕES PRIORITÁRIAS:",
        *acoes,
        "",
        "RECOMENDAÇÃO FINAL:",
        recomendacao,
    ]
    return "\n".join(linhas)


def dde_veredito_precisa_renegociar(dre: "ResultadoDDE") -> bool:
    """Retorna True se veredito indica necessidade de renegociação."""
    return dre.veredito in ("RENEGOCIAR", "REVISAR", "SUBSTITUIR")


# ---------------------------------------------------------------------------
# Validação regex R$
# ---------------------------------------------------------------------------

def _parse_brl_str(s: str) -> Optional[Decimal]:
    """
    Converte string BRL 'X.XXX,XX' para Decimal.
    Retorna None se inválido.
    """
    try:
        # Remove pontos de milhar, troca vírgula por ponto
        normalizado = s.replace(".", "").replace(",", ".")
        return Decimal(normalizado)
    except (InvalidOperation, ValueError):
        return None


def _validar_regex_rs(texto: str, dre: "ResultadoDDE") -> tuple[str, list[str]]:
    """
    Extrai todos os valores R$ X.XXX,XX do texto e verifica contra valores
    reais do ResultadoDDE.

    Se algum valor no texto divergir > 1% de TODOS os valores reais do DRE,
    é marcado como divergência (possível alucinação).

    Retorna: ('OK' | 'SUSPEITO', [lista de divergências descritivas])
    """
    # Coleta valores reais do DRE (em float, sem None)
    valores_reais: list[float] = []
    for linha in dre.linhas:
        if linha.valor is not None:
            try:
                valores_reais.append(float(linha.valor))
            except (TypeError, ValueError):
                pass

    if not valores_reais:
        # Sem dados reais para comparar — não pode validar
        return ("OK", [])

    # Extrai valores do texto: R$ 1.234,56 ou R$1234,56 etc.
    pattern = r"R\$\s*([\d.]+,\d{2})"
    matches = re.findall(pattern, texto)

    divergencias: list[str] = []
    for match in matches:
        valor_texto = _parse_brl_str(match)
        if valor_texto is None:
            continue
        v_float = float(valor_texto)
        if v_float == 0.0:
            continue  # zeros não validamos

        # Verifica se esse valor está próximo de algum valor real do DRE (tolerância 1%)
        encontrou_match = False
        for vr in valores_reais:
            if vr == 0.0:
                continue
            diff_pct = abs(v_float - vr) / abs(vr)
            if diff_pct <= 0.01:  # 1% tolerância
                encontrou_match = True
                break

        if not encontrou_match:
            divergencias.append(
                f"R$ {match} no texto não encontrado nos dados do DRE (divergência > 1%)"
            )

    return ("SUSPEITO" if divergencias else "OK", divergencias)


# ---------------------------------------------------------------------------
# Função principal pública
# ---------------------------------------------------------------------------

def gerar_resumo_ceo(dre: "ResultadoDDE", razao_social: str = "") -> dict:
    """
    Gera Resumo CEO a partir de ResultadoDDE.

    Estratégia:
      1. Tenta LLMClient com qualquer provider disponível (graceful degradation)
      2. Se LLM indisponível (sem keys): usa template determinístico
      3. Valida R$ no texto gerado contra valores reais do DRE

    Retorna dict com:
      texto: str — texto do resumo (multi-linha)
      fonte: 'LLM' | 'TEMPLATE'
      validacao: 'OK' | 'SUSPEITO'
      divergencias: list[str] — valores R$ suspeitos detectados
    """
    llm = LLMClient()
    texto: Optional[str] = None
    fonte: str = "TEMPLATE"

    # Tenta LLM se houver provider disponível
    if llm.available_providers():
        try:
            prompt = _build_prompt(dre, razao_social)
            resp = llm.generate(
                prompt,
                model_tier="cheap",
                max_tokens=1500,
                temperature=0.1,
                use_case="resumo_ceo",
                entity_id=dre.cnpj,
            )
            if resp and resp.text:
                texto = resp.text
                fonte = "LLM"
        except Exception:
            # Falha silenciosa — cai para template
            texto = None
            fonte = "TEMPLATE"

    # Fallback determinístico
    if not texto:
        texto = _template_fallback(dre, razao_social)
        fonte = "TEMPLATE"

    # Validação regex R$
    validacao, divergencias = _validar_regex_rs(texto, dre)

    return {
        "texto": texto,
        "fonte": fonte,
        "validacao": validacao,
        "divergencias": divergencias,
    }
