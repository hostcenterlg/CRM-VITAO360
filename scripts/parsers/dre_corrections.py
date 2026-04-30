"""
CRM VITAO360 — dre_corrections.py
====================================
22 padroes regex para normalizacao de contas DRE extraidas do ZSDFAT SAP.

Funcao publica:
  normaliza_conta_dre(texto: str) -> tuple[str, str]
    Retorna (code, conta_canonica) ou ('RAW', texto_original) se nao reconhecido.

ORDEM IMPORTA:
  C08 (ICMS proprio) DEVE vir antes de C11 (ICMS-ST).
  C08 usa negative lookahead (?!\\s*-?\\s*st) para nao capturar ICMS-ST.

Referencia: docs/specs/cowork/README_TIME_TECNICO_DDE_AC.md secao 4.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# 22 padroes (code, regex, conta_canonica)
# ARMADILHA: C08 ANTES de C11. Negative lookahead em C08 ja protege.
# CMV/CPV/Custo Produtos sao sinonimos — todos capturados em C13.
# ---------------------------------------------------------------------------

DRE_CORRECOES: list[tuple[str, str, str]] = [
    # L1 — Receita topo
    ("C01", r"(?i)faturamento\s*bruto|fat\.?\s*bruto|receita\s*bruta\s*tab", "FATURAMENTO BRUTO A TABELA"),
    # L2 — IPI sobre vendas
    ("C02", r"(?i)ipi\s*(sobre|s/)?\s*venda|ipi\s*faturad", "IPI SOBRE VENDAS"),
    # L3 — Devoluções
    ("C03", r"(?i)devolu[cç][ãa]o|devolu[çc]oes|devolu\w*", "(-) DEVOLUÇÕES"),
    # L4 — Desconto comercial
    ("C04", r"(?i)desc\.?\s*comercial|desconto\s*comerc|desc\.\s*com\.?", "(-) DESCONTO COMERCIAL"),
    # L5 — Desconto financeiro
    ("C05", r"(?i)desc\.?\s*financ|desconto\s*financ|desc\.\s*fin\.?", "(-) DESCONTO FINANCEIRO"),
    # L6 — Bonificações
    ("C06", r"(?i)bonifica[cç][ãa]o|bonif\.?|bonifica[çc]oes|bonifica\w*", "(-) BONIFICAÇÕES"),
    # L7 — IPI recolhido/repassado
    ("C07", r"(?i)ipi\s*re(colhido|passado)|ipi\s*deduz", "(-) IPI FATURADO"),
    # L8 — ICMS proprio (CUIDADO: negative lookahead evita capturar ICMS-ST)
    ("C08", r"(?i)icms(?!\s*-?\s*st)|icms\s*pr[oó]prio", "(-) ICMS"),
    # L9 — PIS
    ("C09", r"(?i)pis\b", "(-) PIS"),
    # L10 — COFINS
    ("C10", r"(?i)cofins\b", "(-) COFINS"),
    # L11 — ICMS-ST (DEVE vir APOS C08 — mais especifico)
    ("C11", r"(?i)icms\s*-?\s*st|substitui[cç][ãa]o\s*tribut", "(-) ICMS-ST"),
    # L12 — Receita Liquida (linha totalizadora)
    ("C12", r"(?i)receita\s*l[ií]quida|rec\.?\s*l[ií]q", "= RECEITA LÍQUIDA"),
    # L13 — CMV / CPV / Custo Produtos (sinonimos — todos mapeados aqui)
    ("C13", r"(?i)cmv|custo\s*(d[oe]s?\s*)?prod|custo\s*mercad|cpv", "(-) CMV"),
    # L14 — Margem Bruta (linha totalizadora)
    ("C14", r"(?i)margem\s*bruta|mg\.?\s*bruta", "= MARGEM BRUTA"),
    # L15 — Frete CT-e
    ("C15", r"(?i)frete|transporte|ct-?e", "(-) FRETE CT-e"),
    # L16 — Comissao sobre venda
    ("C16", r"(?i)comiss[ãa]o|representante|rep\.?\s*comerc", "(-) COMISSÃO SOBRE VENDA"),
    # L17 — Verbas / contratos
    ("C17", r"(?i)verba|contrato\s*desc|zdf2|zpmh", "(-) VERBAS (CONTRATOS)"),
    # L18 — Promotor PDV
    ("C18", r"(?i)promotor|merchandis|pdv\s*agenc", "(-) PROMOTOR PDV"),
    # L19 — Custo de inadimplência
    ("C19", r"(?i)inadimpl[eê]ncia|provis[ãa]o\s*(de\s*)?d[ée]bito|pdd", "(-) CUSTO DE INADIMPLÊNCIA"),
    # L20 — Custo financeiro (capital de giro)
    ("C20", r"(?i)custo\s*financ|capital\s*giro|cdi\b", "(-) CUSTO FINANCEIRO (CAPITAL GIRO)"),
    # L21 — Margem de Contribuicao (linha totalizadora)
    ("C21", r"(?i)margem\s*(de\s*)?contribui[cç][ãa]o|mc\b|mg\.?\s*contrib", "= MARGEM DE CONTRIBUIÇÃO"),
    # L22 — Estrutura comercial alocada
    ("C22", r"(?i)estrutura\s*comerc|folha\s*comerc|desp\.?\s*comerc\s*fix", "(-) ESTRUTURA COMERCIAL ALOCADA"),
]

# Pre-compilar para performance (chamado linha a linha em arquivos grandes)
_COMPILED: list[tuple[str, re.Pattern[str], str]] = [
    (code, re.compile(pattern), canonical)
    for code, pattern, canonical in DRE_CORRECOES
]


def normaliza_conta_dre(texto: str) -> tuple[str, str]:
    """
    Normaliza um texto de conta DRE usando os 22 padroes definidos.

    Args:
        texto: texto bruto da conta (ex.: "Fat. Bruto", "ICMS-ST Retido", "CMV")

    Returns:
        (code, conta_canonica) — ex.: ('C01', 'FATURAMENTO BRUTO A TABELA')
        ('RAW', texto_original) — se nenhum padrao reconheceu o texto

    ORDEM: os padroes sao testados na ordem da lista DRE_CORRECOES.
    C08 (ICMS) vem antes de C11 (ICMS-ST); o negative lookahead em C08
    garante que "ICMS-ST" nao seja capturado por C08.
    """
    texto_limpo = texto.strip() if texto else ""
    if not texto_limpo:
        return ("RAW", texto_limpo)

    for code, compiled, canonical in _COMPILED:
        if compiled.search(texto_limpo):
            return (code, canonical)

    return ("RAW", texto_limpo)
