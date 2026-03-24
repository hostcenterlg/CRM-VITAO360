"""
Classificacao 3-tier e unificacao de base — Motor Operacional CRM VITAO360 v2.0.

Aplica classificacao REAL / SINTETICO / ALUCINACAO a todos os registros,
filtra registros ALUCINACAO, unifica base de clientes a partir da CARTEIRA
e valida integridade da base final.

Funcoes exportadas:
    classificar_registros(dfs) -> dict de DataFrames com coluna classificacao_3tier
    filtrar_alucinacao(dfs) -> dict de DataFrames sem registros ALUCINACAO
    unificar_base(dfs) -> DataFrame unificado de clientes
    validar_base(base) -> dict com resultado da validacao
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

from scripts.motor.helpers import normalizar_cnpj, normalizar_vendedor

logger = logging.getLogger("motor.classify")

# ---------------------------------------------------------------------------
# Abas e suas classificacoes padroes
# ---------------------------------------------------------------------------
# Classificacao por aba conforme documentacao do projeto:
#   CARTEIRA: REAL (dados recalculados de fontes primarias SAP/Mercos)
#   OPERACIONAL: REAL (fonte SAP direta)
#   DRAFT 1: REAL (staging Mercos)
#   DRAFT 2: Classificar por origem (CONTROLE_FUNIL -> ALUCINACAO/SUSPEITO)
#   DRAFT 3: REAL (staging SAP)
#   SINALEIRO: SINTETICO (calculado)
#   MOTOR DE REGRAS: REAL (definicao de regras)
#   REGRAS: REAL (definicao de regras)
#   PROJECAO: SINTETICO (calculado)
#   RESUMO META: SINTETICO (consolidado)
#   VENDA MES: REAL (SAP vendas)
#   AGENDA: SINTETICO (gerada)
#   PAINEL SINALEIRO: SINTETICO (consolidado)
#   RNC: REAL (dados SAP)
#   Abas consultor: Classificar por conteudo

_CLASSIFICACAO_PADRAO: dict[str, str] = {
    "carteira": "REAL",
    "operacional": "REAL",
    "draft1": "REAL",
    "draft3": "REAL",
    "motor_regras": "REAL",
    "regras": "REAL",
    "venda_mes": "REAL",
    "rnc": "REAL",
    "sinaleiro": "SINTETICO",
    "projecao": "SINTETICO",
    "resumo_meta": "SINTETICO",
    "agenda": "SINTETICO",
    "painel_sinaleiro": "SINTETICO",
}


def _detect_alucinacao_cnpjs(dfs: dict[str, pd.DataFrame]) -> set[str]:
    """Detecta CNPJs que sao ALUCINACAO.

    Estrategia pragmatica (conforme plano — ALTERNATIVA PRAGMATICA):
    Como DRAFT 2 retorna 0 rows com data_only=True (formulas nao cached),
    nao conseguimos detectar os 558 registros por criterio automatico direto.

    Em vez disso, verificamos todas as fontes primarias (CARTEIRA,
    OPERACIONAL, DRAFT 1, DRAFT 3, Venda Mes a Mes) para construir
    o conjunto de CNPJs CONFIRMADOS como REAL. Qualquer CNPJ que
    apareca em abas consultor mas NAO esteja em fontes primarias
    eh classificado como SUSPEITO.

    Para os 558 registros ALUCINACAO do CONTROLE_FUNIL:
    - DRAFT 2 esta vazio (0 rows) portanto nenhum dado ALUCINACAO
      pode entrar via essa aba
    - Se futuramente DRAFT 2 tiver dados, os registros do CONTROLE_FUNIL
      serao marcados como SUSPEITO automaticamente

    Returns:
        Set de CNPJs identificados como potencialmente ALUCINACAO
    """
    # Construir conjunto de CNPJs confirmados de fontes primarias
    cnpjs_confirmados: set[str] = set()

    fontes_primarias = ["carteira", "operacional", "draft1", "draft3", "venda_mes"]
    for fonte in fontes_primarias:
        df = dfs.get(fonte)
        if df is not None and "cnpj_normalizado" in df.columns:
            cnpjs_validos = df["cnpj_normalizado"].dropna().tolist()
            cnpjs_confirmados.update(cnpjs_validos)

    logger.info(
        "CNPJs confirmados em fontes primarias: %d unicos",
        len(cnpjs_confirmados),
    )

    # CNPJs suspeitos: presentes em consultor mas NAO em fontes primarias
    cnpjs_suspeitos: set[str] = set()
    for nome, df in dfs.items():
        if nome.startswith("consultor_") and "cnpj_normalizado" in df.columns:
            cnpjs_consultor = set(df["cnpj_normalizado"].dropna().tolist())
            nao_confirmados = cnpjs_consultor - cnpjs_confirmados
            if nao_confirmados:
                logger.warning(
                    "Aba %s: %d CNPJs nao confirmados em fontes primarias",
                    nome,
                    len(nao_confirmados),
                )
                cnpjs_suspeitos.update(nao_confirmados)

    logger.info(
        "CNPJs suspeitos (nao confirmados): %d",
        len(cnpjs_suspeitos),
    )

    return cnpjs_suspeitos


def classificar_registros(
    dfs: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Aplica classificacao 3-tier a cada registro de cada DataFrame.

    Regras de classificacao por aba:
    - CARTEIRA: REAL (dados recalculados de fontes primarias SAP/Mercos)
    - OPERACIONAL: REAL (fonte SAP direta)
    - DRAFT 1: REAL (staging Mercos — fonte primaria)
    - DRAFT 2: SUSPEITO se tiver dados (vem de CONTROLE_FUNIL potencialmente)
    - DRAFT 3: REAL (staging SAP — fonte primaria)
    - SINALEIRO: SINTETICO (calculado a partir de dados REAL)
    - MOTOR DE REGRAS: REAL (definicao de regras, nao dado)
    - REGRAS: REAL (definicao de regras)
    - Abas consultor: Classificar por conteudo (CNPJ valido + em fonte primaria = REAL)

    Args:
        dfs: Dict de DataFrames retornado por importar_planilha()

    Returns:
        Dict de DataFrames com coluna 'classificacao_3tier' adicionada
    """
    cnpjs_suspeitos = _detect_alucinacao_cnpjs(dfs)
    result: dict[str, pd.DataFrame] = {}

    for nome, df in dfs.items():
        if len(df) == 0:
            # Abas vazias: manter sem classificacao
            df = df.copy()
            df["classificacao_3tier"] = pd.Series(dtype="object")
            result[nome] = df
            continue

        df = df.copy()

        # Verificar se tem classificacao padrao
        if nome in _CLASSIFICACAO_PADRAO:
            df["classificacao_3tier"] = _CLASSIFICACAO_PADRAO[nome]
            logger.info(
                "Aba '%s': %d registros classificados como %s",
                nome,
                len(df),
                _CLASSIFICACAO_PADRAO[nome],
            )

        elif nome == "draft2":
            # DRAFT 2: todos os registros sao SUSPEITO (CONTROLE_FUNIL)
            # DRAFT 2 retorna 0 rows com data_only=True, mas se tiver dados
            # no futuro, marcar como SUSPEITO para revisao
            if len(df) > 0:
                df["classificacao_3tier"] = "ALUCINACAO"
                logger.warning(
                    "DRAFT 2: %d registros marcados como ALUCINACAO "
                    "(fonte CONTROLE_FUNIL potencialmente contaminada)",
                    len(df),
                )
            else:
                df["classificacao_3tier"] = pd.Series(dtype="object")
                logger.info("DRAFT 2: 0 registros (formula-only, esperado)")

        elif nome.startswith("consultor_"):
            # Abas consultor: classificar por CNPJ
            if "cnpj_normalizado" in df.columns:
                classificacao = []
                for _, row in df.iterrows():
                    cnpj = row.get("cnpj_normalizado")
                    if cnpj is None:
                        classificacao.append("SINTETICO")
                    elif cnpj in cnpjs_suspeitos:
                        classificacao.append("ALUCINACAO")
                    else:
                        classificacao.append("REAL")
                df["classificacao_3tier"] = classificacao
            else:
                # Sem CNPJ, classificar como SINTETICO
                df["classificacao_3tier"] = "SINTETICO"

            dist = df["classificacao_3tier"].value_counts().to_dict()
            logger.info("Aba '%s': classificacao = %s", nome, dist)

        else:
            # Qualquer aba nao mapeada: SINTETICO por padrao
            df["classificacao_3tier"] = "SINTETICO"
            logger.info(
                "Aba '%s': %d registros classificados como SINTETICO (padrao)",
                nome,
                len(df),
            )

        result[nome] = df

    # Resumo geral
    total = sum(len(df) for df in result.values())
    dist_geral: dict[str, int] = {}
    for df in result.values():
        if "classificacao_3tier" in df.columns and len(df) > 0:
            for val, count in df["classificacao_3tier"].value_counts().items():
                dist_geral[val] = dist_geral.get(val, 0) + int(count)

    logger.info(
        "Classificacao geral: %d registros total, distribuicao = %s",
        total,
        dist_geral,
    )

    return result


def filtrar_alucinacao(
    dfs: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Remove registros classificados como ALUCINACAO de todos os DataFrames.

    Args:
        dfs: Dict de DataFrames com coluna 'classificacao_3tier'

    Returns:
        Dict de DataFrames sem registros ALUCINACAO
    """
    result: dict[str, pd.DataFrame] = {}
    total_removidos = 0

    for nome, df in dfs.items():
        if "classificacao_3tier" not in df.columns or len(df) == 0:
            result[nome] = df
            continue

        antes = len(df)
        df_filtrado = df[df["classificacao_3tier"] != "ALUCINACAO"].copy()
        removidos = antes - len(df_filtrado)

        if removidos > 0:
            logger.info(
                "Aba '%s': %d registros ALUCINACAO removidos (%d -> %d)",
                nome,
                removidos,
                antes,
                len(df_filtrado),
            )
            total_removidos += removidos

        result[nome] = df_filtrado

    logger.info("Total registros ALUCINACAO removidos: %d", total_removidos)
    return result


def unificar_base(
    dfs: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Constroi DataFrame unificado de clientes a partir da CARTEIRA.

    A CARTEIRA eh a visao consolidada de todos os clientes, entao eh
    usada como base principal. Dados do OPERACIONAL (SAP) sao usados
    para enriquecimento via cnpj_normalizado.

    Args:
        dfs: Dict de DataFrames (ja filtrados, sem ALUCINACAO)

    Returns:
        DataFrame unificado de clientes com colunas essenciais
    """
    if "carteira" not in dfs:
        raise ValueError("DataFrame 'carteira' nao encontrado nos dfs")

    cart = dfs["carteira"]
    logger.info("Base CARTEIRA: %d registros", len(cart))

    # ---------------------------------------------------------------------------
    # 1. Extrair colunas essenciais da CARTEIRA
    # Mapeamento: nome_logico -> nome_real_na_coluna
    # ---------------------------------------------------------------------------
    colunas_essenciais: dict[str, str] = {
        "cnpj_normalizado": "cnpj_normalizado",
        "nome_fantasia": "NOME FANTASIA",
        "razao_social": "RAZÃO SOCIAL",
        "uf": "UF",
        "cidade": "CIDADE",
        "consultor_normalizado": "consultor_normalizado",
        "situacao": "SITUAÇÃO",
        "dias_sem_compra": "DIAS SEM COMPRA",
        "valor_ultimo_pedido": "VALOR ÚLTIMO PEDIDO",
        "ciclo_medio": "CICLO MÉDIO",
        "tipo_contato": "TIPO CONTATO",
        "resultado": "RESULTADO",
        "estagio_funil": "ESTÁGIO FUNIL",
        "acao_futura": "AÇÃO FUTURA",
        "temperatura": "TEMPERATURA",
        "score": "SCORE",
        "prioridade_v2": "PRIORIDADE v2",
        "sinaleiro": "SINALEIRO",
        "curva_abc": "CURVA ABC",
        "n_compras": "Nº COMPRAS",
        "tipo_cliente": "TIPO CLIENTE",
    }

    # Construir base extraindo colunas que existem
    base_data: dict[str, Any] = {}
    colunas_faltando: list[str] = []

    for nome_logico, nome_real in colunas_essenciais.items():
        if nome_real in cart.columns:
            base_data[nome_logico] = cart[nome_real].values
        else:
            # Busca case-insensitive e parcial
            found = False
            for col in cart.columns:
                if nome_real.lower() in col.lower():
                    base_data[nome_logico] = cart[col].values
                    found = True
                    logger.info(
                        "Coluna '%s' mapeada para '%s' (match parcial)",
                        nome_logico,
                        col,
                    )
                    break
            if not found:
                colunas_faltando.append(nome_logico)
                logger.warning("Coluna essencial NAO encontrada: %s -> '%s'", nome_logico, nome_real)

    if colunas_faltando:
        logger.warning(
            "%d colunas essenciais nao encontradas: %s",
            len(colunas_faltando),
            colunas_faltando,
        )

    # Calcular faturamento_total (soma das colunas mensais de venda)
    # Na CARTEIRA, colunas 27-42 sao os meses de venda (Jan-Dez + extras)
    # Os headers sao valores numericos (totais da row 2 super-header)
    faturamento_cols = []
    for i, col in enumerate(cart.columns):
        # Colunas de venda mensal: indices 27-42 (entre os meses e as colunas finais)
        if 27 <= i <= 42:
            faturamento_cols.append(col)

    if faturamento_cols:
        # Converter para numerico e somar
        fat_df = cart[faturamento_cols].apply(pd.to_numeric, errors="coerce")
        base_data["faturamento_total"] = fat_df.sum(axis=1).values
        logger.info(
            "Faturamento calculado: %d colunas mensais, total geral = R$ %.2f",
            len(faturamento_cols),
            float(np.nansum(base_data["faturamento_total"])),
        )
    else:
        logger.warning("Colunas de faturamento mensal nao encontradas")

    # Classificacao 3-tier: CARTEIRA eh REAL
    base_data["classificacao_3tier"] = "REAL"

    base = pd.DataFrame(base_data)
    logger.info("Base construida: %d registros x %d colunas", len(base), len(base.columns))

    # ---------------------------------------------------------------------------
    # 2. Enriquecer com OPERACIONAL (SAP)
    # ---------------------------------------------------------------------------
    if "operacional" in dfs:
        op = dfs["operacional"]

        # Mapear colunas do OPERACIONAL para nomes logicos
        enriquecimento: dict[str, str] = {
            "codigo_cliente": "Código SAP",
            "canal": "01 NOME DO CANAL" if "01 NOME DO CANAL" in op.columns else None,
            "tipo_cliente_sap": "Tipo Carteira",
            "macroregiao": "Região",
        }

        # Buscar colunas de descricao e grupo
        for col in op.columns:
            col_lower = col.lower()
            if "grupo" in col_lower and "descri" in col_lower:
                enriquecimento["descricao_grupo"] = col
            elif "micro" in col_lower and "regi" in col_lower:
                enriquecimento["microregiao"] = col

        # Construir lookup por CNPJ
        if "cnpj_normalizado" in op.columns:
            op_lookup = op.drop_duplicates(subset="cnpj_normalizado").set_index(
                "cnpj_normalizado"
            )

            for nome_logico, nome_real in enriquecimento.items():
                if nome_real is None:
                    continue
                if nome_real in op_lookup.columns:
                    # Merge via cnpj_normalizado
                    base[nome_logico] = base["cnpj_normalizado"].map(
                        op_lookup[nome_real]
                    )
                    preenchidos = base[nome_logico].notna().sum()
                    logger.info(
                        "Enriquecimento '%s' (OPERACIONAL.%s): %d/%d preenchidos",
                        nome_logico,
                        nome_real,
                        preenchidos,
                        len(base),
                    )
                else:
                    logger.warning(
                        "Coluna OPERACIONAL '%s' nao encontrada para '%s'",
                        nome_real,
                        nome_logico,
                    )

    # ---------------------------------------------------------------------------
    # 3. Garantir integridade CNPJ
    # ---------------------------------------------------------------------------
    # Garantir cnpj_normalizado eh string, None para nulos
    if "cnpj_normalizado" in base.columns:
        base["cnpj_normalizado"] = base["cnpj_normalizado"].apply(
            lambda x: normalizar_cnpj(x) if x is not None and str(x).strip() != "" else None
        )
        # Converter NaN para None
        base["cnpj_normalizado"] = (
            base["cnpj_normalizado"]
            .astype(object)
            .where(base["cnpj_normalizado"].notna(), None)
        )

    # ---------------------------------------------------------------------------
    # 4. Garantir vendedores canonicalizados
    # ---------------------------------------------------------------------------
    _CANONICAL_VENDEDORES = {"MANU", "LARISSA", "DAIANE", "JULIO", "LEGADO", "DESCONHECIDO"}

    if "consultor_normalizado" in base.columns:
        # Re-aplicar normalizacao apenas para valores que NAO sao canonicos
        # Evita bug: normalizar_vendedor("LEGADO") retorna "DESCONHECIDO"
        # porque "LEGADO" eh uma chave, nao um alias
        def _safe_renormalize(x):
            if x is None:
                return None
            if str(x) in _CANONICAL_VENDEDORES:
                return str(x)
            return normalizar_vendedor(x)

        base["consultor_normalizado"] = base["consultor_normalizado"].apply(_safe_renormalize)

    # ---------------------------------------------------------------------------
    # 5. Validacoes finais
    # ---------------------------------------------------------------------------
    # CNPJ duplicados
    cnpj_validos = base["cnpj_normalizado"].dropna()
    duplicados = cnpj_validos[cnpj_validos.duplicated()].tolist()
    if duplicados:
        logger.error(
            "CNPJ duplicados encontrados: %d (%s...)",
            len(duplicados),
            duplicados[:5],
        )

    # CNPJ como float
    cnpj_float = sum(
        1 for v in base["cnpj_normalizado"]
        if v is not None and isinstance(v, float)
    )
    if cnpj_float > 0:
        logger.error("CNPJ como float: %d (VIOLACAO R2!)", cnpj_float)

    # Vendedores nao canonicos
    if "consultor_normalizado" in base.columns:
        vendedores_validos = {"MANU", "LARISSA", "DAIANE", "JULIO", "LEGADO", "DESCONHECIDO", None}
        nao_canonicos = base["consultor_normalizado"].dropna().unique()
        alias_soltos = [v for v in nao_canonicos if v not in vendedores_validos]
        if alias_soltos:
            logger.error("Vendedores NAO canonicalizados: %s", alias_soltos)

    logger.info(
        "Base unificada final: %d registros, %d colunas",
        len(base),
        len(base.columns),
    )

    return base


def validar_base(base: pd.DataFrame) -> dict[str, Any]:
    """Roda checklist de validacao na base unificada.

    Args:
        base: DataFrame retornado por unificar_base()

    Returns:
        Dict com resultado de cada check
    """
    resultado: dict[str, Any] = {}

    # CNPJ como float
    cnpj_float = 0
    if "cnpj_normalizado" in base.columns:
        cnpj_float = sum(
            1 for v in base["cnpj_normalizado"]
            if v is not None and isinstance(v, float)
        )
    resultado["cnpj_como_float"] = cnpj_float

    # CNPJ duplicados
    cnpj_duplicados = 0
    if "cnpj_normalizado" in base.columns:
        valid_docs = base["cnpj_normalizado"].dropna()
        cnpj_duplicados = int(valid_docs.duplicated().sum())
    resultado["cnpj_duplicados"] = cnpj_duplicados

    # CNPJ nulos
    cnpj_nulos = 0
    if "cnpj_normalizado" in base.columns:
        cnpj_nulos = int(base["cnpj_normalizado"].isna().sum())
    resultado["cnpj_nulos"] = cnpj_nulos

    # Vendedor desconhecido
    vendedor_desconhecido: dict[str, Any] = {"count": 0, "lista": []}
    if "consultor_normalizado" in base.columns:
        desc = base[base["consultor_normalizado"] == "DESCONHECIDO"]
        vendedor_desconhecido["count"] = len(desc)
        if len(desc) > 0 and "nome_fantasia" in base.columns:
            vendedor_desconhecido["lista"] = desc["nome_fantasia"].head(10).tolist()
    resultado["vendedor_desconhecido"] = vendedor_desconhecido

    # ALUCINACAO presente
    alucinacao_presente = 0
    if "classificacao_3tier" in base.columns:
        alucinacao_presente = int(
            (base["classificacao_3tier"] == "ALUCINACAO").sum()
        )
    resultado["alucinacao_presente"] = alucinacao_presente

    # Total registros
    resultado["total_registros"] = len(base)

    # Distribuicao vendedores
    if "consultor_normalizado" in base.columns:
        resultado["distribuicao_vendedores"] = (
            base["consultor_normalizado"]
            .value_counts()
            .to_dict()
        )
        # Converter numpy types para python types
        resultado["distribuicao_vendedores"] = {
            str(k): int(v) for k, v in resultado["distribuicao_vendedores"].items()
        }
    else:
        resultado["distribuicao_vendedores"] = {}

    # Distribuicao situacao
    if "situacao" in base.columns:
        resultado["distribuicao_situacao"] = (
            base["situacao"]
            .value_counts()
            .to_dict()
        )
        resultado["distribuicao_situacao"] = {
            str(k): int(v) for k, v in resultado["distribuicao_situacao"].items()
        }
    else:
        resultado["distribuicao_situacao"] = {}

    # Distribuicao classificacao
    if "classificacao_3tier" in base.columns:
        resultado["distribuicao_classificacao"] = (
            base["classificacao_3tier"]
            .value_counts()
            .to_dict()
        )
        resultado["distribuicao_classificacao"] = {
            str(k): int(v) for k, v in resultado["distribuicao_classificacao"].items()
        }
    else:
        resultado["distribuicao_classificacao"] = {}

    return resultado
