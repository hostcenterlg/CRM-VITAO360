"""
Configuracao central do Motor Operacional CRM VITAO360 v2.0.

Todas as constantes do projeto: caminho da planilha, DE-PARA vendedores,
lista de abas relevantes, thresholds de validacao.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminho da planilha FINAL
# ---------------------------------------------------------------------------
CAMINHO_PLANILHA = Path(
    r"C:\Users\User\OneDrive\Área de Trabalho"
    r"\CRM_VITAO360  INTELIGENTE   FINAL OK .xlsx"
)

if not CAMINHO_PLANILHA.exists():
    raise FileNotFoundError(
        f"Planilha FINAL nao encontrada em: {CAMINHO_PLANILHA}\n"
        "Verifique se o arquivo esta no Desktop e o OneDrive esta sincronizado."
    )

# ---------------------------------------------------------------------------
# DE-PARA Vendedores (5 grupos canonicos + alias)
# ---------------------------------------------------------------------------
DE_PARA_VENDEDORES: dict[str, list[str]] = {
    "MANU": [
        "Manu",
        "Manu Vitao",
        "Manu Ditzel",
        "HEMANUELE DITZEL (MANU)",
        "HEMANUELE",
    ],
    "LARISSA": [
        "Larissa",
        "Lari",
        "Larissa Vitao",
        "Mais Granel",
        "Rodrigo",
    ],
    "DAIANE": [
        "Daiane",
        "Central Daiane",
        "Daiane Vitao",
        "CENTRAL - DAIANE",
    ],
    "JULIO": [
        "Julio",
        "Julio Gadret",
    ],
    "LEGADO": [
        "Bruno Gretter",
        "Jeferson Vitao",
        "Patric",
        "Gabriel",
        "Sergio",
        "Ive",
        "Ana",
        "Lorrany",
        "Leandro",
    ],
}

# ---------------------------------------------------------------------------
# Abas relevantes: nome_logico -> nome_real_na_planilha
# ATENCAO: algumas abas tem espacos trailing ou acentos!
# Nomes extraidos de .cache/radiografia_completa.json
# ---------------------------------------------------------------------------
ABAS_RELEVANTES: dict[str, str] = {
    "carteira": "CARTEIRA",
    "operacional": "OPERACIONAL",
    "projecao": "PROJE\u00c7\u00c3O ",       # "PROJECAO " com acento + espaco trailing
    "resumo_meta": "RESUMO META",
    "sinaleiro": "SINALEIRO",
    "draft1": "DRAFT 1",
    "draft2": "DRAFT 2",
    "draft3": "DRAFT 3 ",                     # espaco trailing
    "motor_regras": "MOTOR DE REGRAS",
    "regras": "REGRAS",
    "venda_mes": "Venda M\u00eas a M\u00eas", # "Venda Mes a Mes" com acentos
    "agenda": "AGENDA",
    "painel_sinaleiro": "PAINEL SINALEIRO ",   # espaco trailing
    "rnc": "RNC",
}

# ---------------------------------------------------------------------------
# Abas de consultor (LOG por vendedor)
# ---------------------------------------------------------------------------
ABAS_CONSULTOR: dict[str, str] = {
    "LARISSA": "LARISSA",
    "MANU": "MANU",
    "JULIO": "JULIO",
    "DAIANE": "DAIANE",
}

# ---------------------------------------------------------------------------
# Headers especiais por aba (row do header, 1-indexed)
# Abas com super-grupo headers precisam de tratamento especial
# ---------------------------------------------------------------------------
HEADER_ROWS: dict[str, int] = {
    "CARTEIRA": 3,    # rows 1-2 sao super-grupo headers
    "DRAFT 1": 3,     # rows 1-2 sao agrupamento
    # Todas as demais: header na row 1 (padrao)
}

# ---------------------------------------------------------------------------
# Colunas de CNPJ por aba (nome da coluna ou indice 0-based)
# ---------------------------------------------------------------------------
COLUNAS_CNPJ: dict[str, str] = {
    "CARTEIRA": "CNPJ",              # Coluna B
    "OPERACIONAL": "CNPJ",           # Coluna W (formatado)
    "DRAFT 1": "CNPJ",               # Coluna BH
    "DRAFT 3 ": "CNPJ",              # Coluna R
    "RNC": "CNPJ",                   # Se existir
}

# ---------------------------------------------------------------------------
# Thresholds e constantes de validacao
# ---------------------------------------------------------------------------
ALUCINACAO_COUNT: int = 558
FATURAMENTO_BASELINE: float = 2_091_000.0
FATURAMENTO_TOLERANCIA: float = 0.005  # 0.5%
