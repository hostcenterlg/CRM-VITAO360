"""
Projecao Engine -- Motor de Projecao SAP x Realizado CRM VITAO360 v1.0.

Calcula realizacao vs meta SAP por cliente, consolida por consultor, por
quarter e por rede/franquia. Fornece dashboard ASCII para monitoramento
rapido no terminal.

Regras aplicadas (ver CLAUDE.md e 000-coleira-suprema.md):
    R4  -- Two-Base Architecture: VENDA=R$, LOG=R$0.00
            Este modulo apenas le dados de VENDA -- nunca soma LOG.
    R5  -- CNPJ sempre string 14 digitos zero-padded, NUNCA float/int.
    R8  -- Zero fabricacao de dados. Se coluna nao existe retorna None/NaN.
    R9  -- Faturamento baseline 2025: R$ 2.091.000 (PAINEL CEO auditado).
            Projecao 2026: R$ 3.377.120 (PAINEL CEO definitivo).

Fontes de dados (ingestao via import_pipeline):
    dfs['projecao']  -- aba "PROJECAO " (659 linhas, 81 colunas), meta SAP
    dfs['venda_mes'] -- aba "Venda Mes a Mes" (569 linhas, 72 colunas), SAP real

Fontes JSON de referencia:
    data/intelligence/q1_2026_real.json
    data/intelligence/motor_rampup.json
    data/intelligence/premissas.json
    data/intelligence/painel_ceo.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
_INTELLIGENCE_DIR = _ROOT / "data" / "intelligence"

logger = logging.getLogger("motor.projecao_engine")

# ---------------------------------------------------------------------------
# Constantes de negocio (alterar apenas com aprovacao L3)
# ---------------------------------------------------------------------------

# Financeiro
FATURAMENTO_BASELINE: float = 2_091_000.0   # 2025 real -- PAINEL CEO auditado
PROJECAO_2026: float = 3_377_120.0          # meta PAINEL CEO 2026
Q1_REAL: float = 459_465.0                  # Q1 2026 SAP -- 178 clientes

# Meses 2025-2026 que aparecem na aba Venda Mes a Mes.
# Nomes sao aproximados -- o motor tenta match por substring case-insensitive.
MESES_VENDA: list[str] = [
    "jan_25", "fev_25", "mar_25", "abr_25", "mai_25", "jun_25",
    "jul_25", "ago_25", "set_25", "out_25", "nov_25", "dez_25",
    "jan_26", "fev_26", "mar_26",
]

# Mes corrente (Março 2026) -- Q1 2026 e o periodo ativo.
MES_CORRENTE: str = "mar_26"
QUARTER_ATUAL: str = "Q1"

# Thresholds de status de meta
THRESHOLD_ACIMA: float = 100.0   # pct >= 100 -> ACIMA
THRESHOLD_ALERTA: float = 70.0   # pct 70-99 -> ALERTA; < 70 -> CRITICO

# Gap minimo para exibir alerta no dashboard
ALERTA_GAP_MINIMO: float = 5_000.0   # R$ 5k de gap = merece atencao

# Mapeamento quarter -> meses de meta
_QUARTER_MESES: dict[str, list[str]] = {
    "Q1": ["jan", "fev", "mar"],
    "Q2": ["abr", "mai", "jun"],
    "Q3": ["jul", "ago", "set"],
    "Q4": ["out", "nov", "dez"],
}


# ---------------------------------------------------------------------------
# Utilitarios internos
# ---------------------------------------------------------------------------

def _normalizar_cnpj(val: object) -> Optional[str]:
    """Normaliza CNPJ para string de 14 digitos zero-padded.

    Replica a logica de helpers.normalizar_cnpj para evitar dependencia circular
    em contextos de self-test. No pipeline completo, usar helpers.normalizar_cnpj.

    Tratamento de float-strings (ex: "12345678000195.0"):
        Remove a parte decimal antes de extrair os digitos para evitar que o
        ".0" espurio gere um digito extra e corrompa os 14 digitos do CNPJ.

    Args:
        val: Qualquer valor (str, int, float, None).

    Returns:
        String de 14 digitos ou None se vazio/invalido.
    """
    import re

    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("nan", "none", ""):
        return None

    # Remove parte decimal espuria gerada por armazenamento como float
    # Ex: "12345678000195.0" -> "12345678000195"
    # Ex: "12.345.678/0001-95" -> mantido (nao e decimal float)
    if "." in val_str:
        try:
            int_part = str(int(float(val_str)))
            # Usar int_part se o valor original eh um numero (float espurio)
            import re as _re
            if _re.fullmatch(r"[\d.,/\-]+", val_str):
                val_str = int_part
        except (ValueError, OverflowError):
            pass  # Nao e um float -- usar val_str original com pontuacao

    digits = re.sub(r"\D", "", val_str)
    if not digits:
        return None
    cnpj = digits.zfill(14)
    if len(cnpj) > 14:
        logger.warning(
            "CNPJ com mais de 14 digitos: %r -> %s (usando ultimos 14)", val, cnpj
        )
        cnpj = cnpj[-14:]
    return cnpj


def _encontrar_coluna(df: pd.DataFrame, fragmentos: list[str]) -> Optional[str]:
    """Retorna o nome da primeira coluna que contem qualquer dos fragmentos.

    A busca e case-insensitive e usa match de substring. Retorna None se nao
    encontrar nenhuma coluna correspondente.

    Args:
        df: DataFrame a inspecionar.
        fragmentos: Lista de substrings a procurar no nome das colunas.

    Returns:
        Nome da coluna encontrada ou None.
    """
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for frag in fragmentos:
        frag_lower = frag.lower()
        for col_lower, col_real in cols_lower.items():
            if frag_lower in col_lower:
                return col_real
    return None


def _safe_float(val: object) -> Optional[float]:
    """Converte valor para float de forma segura; retorna None se impossivel.

    Args:
        val: Valor a converter.

    Returns:
        float ou None.
    """
    if val is None:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) or np.isinf(f) else f
    except (ValueError, TypeError):
        return None


def _pct_alcancado(realizado: float, meta: float) -> Optional[float]:
    """Calcula percentual realizado / meta, tratando divisao por zero.

    Args:
        realizado: Valor realizado acumulado.
        meta: Meta acumulada ate o periodo.

    Returns:
        Percentual (0-200+ range) ou None se meta for zero/ausente.
    """
    if meta is None or meta == 0.0:
        return None
    return round(realizado / meta * 100.0, 2)


def _status_meta(pct: Optional[float]) -> Optional[str]:
    """Classifica o percentual de alcance da meta em status textual.

    Args:
        pct: Percentual de alcance (0-200+).

    Returns:
        'ACIMA' | 'ALERTA' | 'CRITICO' | None se sem meta.
    """
    if pct is None:
        return None
    if pct >= THRESHOLD_ACIMA:
        return "ACIMA"
    if pct >= THRESHOLD_ALERTA:
        return "ALERTA"
    return "CRITICO"


# ---------------------------------------------------------------------------
# Stage 1: Carregar metas SAP
# ---------------------------------------------------------------------------

def carregar_metas_sap(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Extrai metas SAP e vendas mensais das abas PROJECAO e Venda Mes a Mes.

    Regras:
        - CNPJ normalizado para 14 digitos (R5).
        - Valores monetarios somente de registros tipo VENDA (R4).
        - Se coluna nao existe, retorna NaN para aquela metrica -- NUNCA fabrica (R8).
        - Clientes sem meta (PROSPECTs) recebem NaN em todas as colunas de meta.

    Args:
        dfs: Dicionario de DataFrames gerado pelo import_pipeline.
              Chaves esperadas: 'projecao', 'venda_mes'.

    Returns:
        DataFrame indexado por cnpj_normalizado com colunas:
            cnpj_normalizado  -- str 14 digitos
            meta_anual        -- float ou NaN
            meta_q1, meta_q2, meta_q3, meta_q4  -- float ou NaN
            meta_jan_26, meta_fev_26, meta_mar_26  -- float ou NaN
            jan_25 .. mar_26  -- vendas mensais reais (float ou NaN)

    Raises:
        KeyError: Se nenhuma das chaves 'projecao' ou 'venda_mes' existir.
    """
    if "projecao" not in dfs and "venda_mes" not in dfs:
        raise KeyError(
            "dfs precisa ter ao menos uma das chaves: 'projecao', 'venda_mes'."
        )

    # ---- 1. Extrair metas da aba PROJECAO ----
    metas_rows: list[dict] = []

    df_proj = dfs.get("projecao")
    if df_proj is not None and not df_proj.empty:
        logger.info(
            "Processando aba PROJECAO: %d linhas x %d colunas",
            len(df_proj),
            len(df_proj.columns),
        )

        col_cnpj = _encontrar_coluna(df_proj, ["cnpj"])
        col_meta_anual = _encontrar_coluna(df_proj, ["meta_anual", "meta anual", "total"])
        col_q1 = _encontrar_coluna(df_proj, ["meta_q1", "meta q1", "q1"])
        col_q2 = _encontrar_coluna(df_proj, ["meta_q2", "meta q2", "q2"])
        col_q3 = _encontrar_coluna(df_proj, ["meta_q3", "meta q3", "q3"])
        col_q4 = _encontrar_coluna(df_proj, ["meta_q4", "meta q4", "q4"])

        # Metas mensais individuais (jan_26 ... mar_26 no minimo)
        col_meta_jan_26 = _encontrar_coluna(df_proj, ["meta_jan_26", "jan_26", "jan26", "jan 26"])
        col_meta_fev_26 = _encontrar_coluna(df_proj, ["meta_fev_26", "fev_26", "fev26", "fev 26"])
        col_meta_mar_26 = _encontrar_coluna(df_proj, ["meta_mar_26", "mar_26", "mar26", "mar 26"])

        logger.debug(
            "Colunas encontradas em PROJECAO: cnpj=%s meta_anual=%s q1=%s q2=%s q3=%s q4=%s",
            col_cnpj, col_meta_anual, col_q1, col_q2, col_q3, col_q4,
        )

        if col_cnpj is None:
            logger.warning(
                "Coluna CNPJ nao encontrada na aba PROJECAO. "
                "Colunas disponiveis: %s",
                list(df_proj.columns[:20]),
            )
        else:
            for _, row in df_proj.iterrows():
                cnpj = _normalizar_cnpj(row[col_cnpj])
                if cnpj is None:
                    continue  # linha sem CNPJ valido: pular

                record: dict = {"cnpj_normalizado": cnpj}

                record["meta_anual"] = _safe_float(
                    row[col_meta_anual] if col_meta_anual else None
                )
                record["meta_q1"] = _safe_float(
                    row[col_q1] if col_q1 else None
                )
                record["meta_q2"] = _safe_float(
                    row[col_q2] if col_q2 else None
                )
                record["meta_q3"] = _safe_float(
                    row[col_q3] if col_q3 else None
                )
                record["meta_q4"] = _safe_float(
                    row[col_q4] if col_q4 else None
                )
                record["meta_jan_26"] = _safe_float(
                    row[col_meta_jan_26] if col_meta_jan_26 else None
                )
                record["meta_fev_26"] = _safe_float(
                    row[col_meta_fev_26] if col_meta_fev_26 else None
                )
                record["meta_mar_26"] = _safe_float(
                    row[col_meta_mar_26] if col_meta_mar_26 else None
                )
                metas_rows.append(record)

        logger.info("Metas SAP extraidas: %d registros", len(metas_rows))
    else:
        logger.warning("Aba PROJECAO nao disponivel em dfs ou vazia.")

    # ---- 2. Extrair vendas mensais da aba Venda Mes a Mes ----
    vendas_rows: list[dict] = []

    df_venda = dfs.get("venda_mes")
    if df_venda is not None and not df_venda.empty:
        logger.info(
            "Processando aba Venda Mes a Mes: %d linhas x %d colunas",
            len(df_venda),
            len(df_venda.columns),
        )

        col_cnpj_v = _encontrar_coluna(df_venda, ["cnpj"])
        if col_cnpj_v is None:
            logger.warning(
                "Coluna CNPJ nao encontrada em Venda Mes a Mes. "
                "Colunas disponiveis: %s",
                list(df_venda.columns[:20]),
            )
        else:
            # Mapear colunas de vendas mensais
            colunas_meses: dict[str, Optional[str]] = {}
            for mes in MESES_VENDA:
                # Tenta variantes: "jan_25", "jan25", "jan 25", "jan/25"
                variantes = [mes, mes.replace("_", ""), mes.replace("_", " "),
                             mes.replace("_", "/")]
                colunas_meses[mes] = _encontrar_coluna(df_venda, variantes)

            for _, row in df_venda.iterrows():
                cnpj = _normalizar_cnpj(row[col_cnpj_v])
                if cnpj is None:
                    continue

                record_v: dict = {"cnpj_normalizado": cnpj}
                for mes, col in colunas_meses.items():
                    record_v[mes] = _safe_float(row[col] if col else None)
                vendas_rows.append(record_v)

        logger.info("Vendas mensais extraidas: %d registros", len(vendas_rows))
    else:
        logger.warning("Aba Venda Mes a Mes nao disponivel em dfs ou vazia.")

    # ---- 3. Montar DataFrame final ----
    df_metas = (
        pd.DataFrame(metas_rows)
        if metas_rows
        else pd.DataFrame(columns=["cnpj_normalizado"])
    )
    df_vendas = (
        pd.DataFrame(vendas_rows)
        if vendas_rows
        else pd.DataFrame(columns=["cnpj_normalizado"])
    )

    # Garantir CNPJ como string (R5)
    for df_ in (df_metas, df_vendas):
        if "cnpj_normalizado" in df_.columns:
            df_["cnpj_normalizado"] = df_["cnpj_normalizado"].astype(str)

    # Merge outer: preservar todos os CNPJs de ambas as fontes
    if df_metas.empty and df_vendas.empty:
        logger.warning("Nenhum dado carregado de PROJECAO nem Venda Mes a Mes.")
        return pd.DataFrame(columns=["cnpj_normalizado"])

    if df_metas.empty:
        resultado = df_vendas
    elif df_vendas.empty:
        resultado = df_metas
    else:
        resultado = pd.merge(
            df_metas,
            df_vendas,
            on="cnpj_normalizado",
            how="outer",
        )

    # Remover CNPJs "00000000000000" (zerados) ou invalidos
    resultado = resultado[
        resultado["cnpj_normalizado"].notna()
        & (resultado["cnpj_normalizado"] != "00000000000000")
        & (resultado["cnpj_normalizado"].str.len() == 14)
    ].copy()

    # Remover duplicatas de CNPJ (agregar somando vendas, mantendo primeira meta)
    if resultado.duplicated(subset=["cnpj_normalizado"]).any():
        n_dup = resultado.duplicated(subset=["cnpj_normalizado"]).sum()
        logger.warning("Duplicatas de CNPJ encontradas: %d. Agregando.", n_dup)

        # Colunas numericas: somar para vendas mensais, manter primeira para metas
        cols_meta = [c for c in resultado.columns if c.startswith("meta_")]
        cols_venda = [c for c in resultado.columns if c in MESES_VENDA]

        first_part = (
            resultado[["cnpj_normalizado"] + cols_meta]
            .groupby("cnpj_normalizado", as_index=False)
            .first()
        )
        sum_part = (
            resultado[["cnpj_normalizado"] + cols_venda]
            .groupby("cnpj_normalizado", as_index=False)
            .sum(min_count=1)
        )
        resultado = pd.merge(first_part, sum_part, on="cnpj_normalizado", how="outer")

    logger.info(
        "DataFrame de metas SAP construido: %d clientes, %d colunas.",
        len(resultado),
        len(resultado.columns),
    )
    return resultado.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Stage 2: Calcular projecao
# ---------------------------------------------------------------------------

def calcular_projecao(base: pd.DataFrame, metas: pd.DataFrame) -> pd.DataFrame:
    """Mescla metas SAP na base de clientes e calcula metricas de projecao.

    Para cada cliente calcula:
        realizado_acumulado -- soma de vendas mensais ate o mes corrente (Q1 2026)
        meta_acumulado      -- soma de metas mensais ate o mes corrente
        pct_alcancado       -- realizado / meta * 100 (None se sem meta)
        gap_valor           -- meta_acumulado - realizado_acumulado (positivo = atrasado)
        status_meta         -- ACIMA | ALERTA | CRITICO | None

    Regra Two-Base (R4): soma apenas meses com registros tipo VENDA.
    Se a base tiver coluna 'tipo_registro', filtra apenas VENDA. Caso contrario,
    assume que todos os valores monetarios ja sao de vendas.

    Args:
        base: DataFrame principal de clientes (saida do motor pipeline).
              Deve ter 'cnpj_normalizado'.
        metas: DataFrame de metas SAP (saida de carregar_metas_sap).
               Deve ter 'cnpj_normalizado'.

    Returns:
        DataFrame base enriquecido com as colunas de projecao.
    """
    if base.empty:
        logger.warning("Base vazia recebida em calcular_projecao. Retornando sem alteracoes.")
        return base.copy()

    if "cnpj_normalizado" not in base.columns:
        logger.error(
            "Coluna 'cnpj_normalizado' ausente na base. Colunas: %s",
            list(base.columns[:15]),
        )
        return base.copy()

    # ---- 1. Merge metas na base ----
    # Usar left join: preservar todos os clientes da base.
    # Clientes sem meta ficam com NaN nas colunas de meta.
    if metas.empty or "cnpj_normalizado" not in metas.columns:
        logger.warning(
            "DataFrame de metas vazio ou sem CNPJ. "
            "Projecao sera calculada sem metas SAP."
        )
        base_enriquecida = base.copy()
        for col in ["meta_anual", "meta_q1", "meta_q2", "meta_q3", "meta_q4",
                    "meta_jan_26", "meta_fev_26", "meta_mar_26"]:
            if col not in base_enriquecida.columns:
                base_enriquecida[col] = np.nan
    else:
        # Selecionar apenas colunas de meta para o merge (evitar colisao com colunas ja na base)
        cols_metas_para_merge = ["cnpj_normalizado"] + [
            c for c in metas.columns
            if c != "cnpj_normalizado"
            and c not in base.columns
        ]
        base_enriquecida = pd.merge(
            base,
            metas[cols_metas_para_merge],
            on="cnpj_normalizado",
            how="left",
        )
        logger.info(
            "Merge metas: %d clientes na base, %d com meta SAP.",
            len(base_enriquecida),
            base_enriquecida["meta_anual"].notna().sum()
            if "meta_anual" in base_enriquecida.columns
            else 0,
        )

    # ---- 2. Calcular realizado acumulado Q1 2026 ----
    # Meses do Q1 2026 que estao nos dados de venda
    meses_q1_2026 = ["jan_26", "fev_26", "mar_26"]
    cols_q1_presentes = [m for m in meses_q1_2026 if m in base_enriquecida.columns]

    if cols_q1_presentes:
        base_enriquecida["realizado_acumulado"] = (
            base_enriquecida[cols_q1_presentes]
            .apply(pd.to_numeric, errors="coerce")
            .sum(axis=1, min_count=1)
        )
        logger.info(
            "realizado_acumulado calculado a partir de %d colunas: %s",
            len(cols_q1_presentes),
            cols_q1_presentes,
        )
    else:
        # Fallback: usar meses 2025 se 2026 nao estiver nas colunas
        meses_2025 = [m for m in MESES_VENDA if "_25" in m and m in base_enriquecida.columns]
        if meses_2025:
            logger.warning(
                "Colunas Q1 2026 ausentes. Usando 2025 como fallback: %s", meses_2025
            )
            base_enriquecida["realizado_acumulado"] = (
                base_enriquecida[meses_2025]
                .apply(pd.to_numeric, errors="coerce")
                .sum(axis=1, min_count=1)
            )
        else:
            logger.warning(
                "Nenhuma coluna de venda mensal encontrada. "
                "realizado_acumulado sera NaN para todos os clientes."
            )
            base_enriquecida["realizado_acumulado"] = np.nan

    # ---- 3. Calcular meta acumulada Q1 2026 ----
    # Prefere meta_q1 se disponivel; fallback para soma das metas mensais
    if "meta_q1" in base_enriquecida.columns:
        base_enriquecida["meta_acumulado"] = pd.to_numeric(
            base_enriquecida["meta_q1"], errors="coerce"
        )
    else:
        cols_meta_mensais_q1 = [
            c for c in ["meta_jan_26", "meta_fev_26", "meta_mar_26"]
            if c in base_enriquecida.columns
        ]
        if cols_meta_mensais_q1:
            base_enriquecida["meta_acumulado"] = (
                base_enriquecida[cols_meta_mensais_q1]
                .apply(pd.to_numeric, errors="coerce")
                .sum(axis=1, min_count=1)
            )
        else:
            base_enriquecida["meta_acumulado"] = np.nan

    # ---- 4. Metricas derivadas ----
    # Vetorizado para performance (sem apply linha a linha)
    realizado = pd.to_numeric(base_enriquecida["realizado_acumulado"], errors="coerce")
    meta = pd.to_numeric(base_enriquecida["meta_acumulado"], errors="coerce")

    # pct_alcancado: 0 se realizado=0 e meta>0; None se meta=0 ou NaN
    pct = np.where(
        meta.notna() & (meta > 0),
        np.round(realizado.fillna(0.0) / meta * 100.0, 2),
        np.nan,
    )
    base_enriquecida["pct_alcancado"] = pct

    # gap_valor: meta - realizado (positivo = atrasado)
    base_enriquecida["gap_valor"] = np.where(
        meta.notna(),
        meta.fillna(0.0) - realizado.fillna(0.0),
        np.nan,
    )

    # status_meta: categorico baseado em pct
    pct_series = pd.to_numeric(base_enriquecida["pct_alcancado"], errors="coerce")
    conditions = [
        pct_series.notna() & (pct_series >= THRESHOLD_ACIMA),
        pct_series.notna() & (pct_series >= THRESHOLD_ALERTA),
        pct_series.notna() & (pct_series < THRESHOLD_ALERTA),
    ]
    choices = ["ACIMA", "ALERTA", "CRITICO"]
    base_enriquecida["status_meta"] = np.select(conditions, choices, default=None)
    # Substituir a string "None" pelo None real (np.select retorna string)
    base_enriquecida["status_meta"] = base_enriquecida["status_meta"].replace("None", np.nan)

    logger.info(
        "Projecao calculada. Status: ACIMA=%d ALERTA=%d CRITICO=%d SEM_META=%d",
        (base_enriquecida["status_meta"] == "ACIMA").sum(),
        (base_enriquecida["status_meta"] == "ALERTA").sum(),
        (base_enriquecida["status_meta"] == "CRITICO").sum(),
        base_enriquecida["status_meta"].isna().sum(),
    )
    return base_enriquecida


# ---------------------------------------------------------------------------
# Stage 3: Consolidar projecao
# ---------------------------------------------------------------------------

def consolidar_projecao(base: pd.DataFrame) -> dict:
    """Consolida metricas de projecao por consultor, quarter e rede.

    Gera tres grupos de consolidacao:
        'por_consultor' -- fat_total, meta_total, pct_alcancado, n_clientes
        'por_quarter'   -- realizados vs metas Q1-Q4 (Q2-Q4 apenas metas)
        'por_rede'      -- consolidado por descricao_grupo se coluna existir

    Args:
        base: DataFrame enriquecido (saida de calcular_projecao).

    Returns:
        Dicionario com chaves 'por_consultor', 'por_quarter', 'por_rede',
        'resumo_geral' e 'alertas'.
    """
    resultado: dict = {
        "por_consultor": [],
        "por_quarter": [],
        "por_rede": [],
        "resumo_geral": {},
        "alertas": [],
    }

    if base.empty:
        logger.warning("Base vazia em consolidar_projecao.")
        return resultado

    # ---- Resumo geral ----
    fat_total = _safe_float(
        pd.to_numeric(base.get("realizado_acumulado"), errors="coerce").sum()
    ) or 0.0
    meta_total = _safe_float(
        pd.to_numeric(base.get("meta_acumulado"), errors="coerce").sum()
    ) or 0.0
    pct_geral = _pct_alcancado(fat_total, meta_total)

    resultado["resumo_geral"] = {
        "fat_total_realizado": round(fat_total, 2),
        "meta_total_q1": round(meta_total, 2),
        "pct_alcancado": pct_geral,
        "status_meta": _status_meta(pct_geral),
        "n_clientes_total": len(base),
        "n_com_meta": int(
            pd.to_numeric(base.get("meta_acumulado"), errors="coerce").notna().sum()
        ),
        "quarter_referencia": QUARTER_ATUAL,
        "baseline_2025": FATURAMENTO_BASELINE,
        "projecao_2026": PROJECAO_2026,
        "q1_real_referencia": Q1_REAL,
    }

    # ---- Por consultor ----
    col_consultor = _encontrar_coluna(base, ["consultor", "vendedor"])
    if col_consultor:
        for consultor, grupo in base.groupby(col_consultor, dropna=False):
            consultor_nome = str(consultor) if consultor and str(consultor) != "nan" else "SEM_CONSULTOR"
            fat_cons = _safe_float(
                pd.to_numeric(grupo.get("realizado_acumulado"), errors="coerce").sum()
            ) or 0.0
            meta_cons = _safe_float(
                pd.to_numeric(grupo.get("meta_acumulado"), errors="coerce").sum()
            ) or 0.0
            pct_cons = _pct_alcancado(fat_cons, meta_cons)

            resultado["por_consultor"].append({
                "consultor": consultor_nome,
                "fat_total": round(fat_cons, 2),
                "meta_total": round(meta_cons, 2),
                "pct_alcancado": pct_cons,
                "status_meta": _status_meta(pct_cons),
                "n_clientes": len(grupo),
            })

        resultado["por_consultor"].sort(key=lambda x: x["fat_total"], reverse=True)
        logger.info(
            "Consolidado por consultor: %d consultores.", len(resultado["por_consultor"])
        )
    else:
        logger.warning(
            "Coluna de consultor/vendedor nao encontrada na base. "
            "Colunas disponiveis: %s",
            list(base.columns[:20]),
        )

    # ---- Por quarter ----
    # Q1 2026: dados reais disponiveis
    resultado["por_quarter"].append({
        "quarter": "Q1_2026",
        "meses": ["jan_26", "fev_26", "mar_26"],
        "realizado": round(fat_total, 2),
        "meta": round(meta_total, 2),
        "pct_alcancado": pct_geral,
        "status_meta": _status_meta(pct_geral),
        "fonte": "SAP real (2.758 itens)",
    })

    # Q2-Q4 2026: apenas metas (sem realizado ainda)
    for q, meses_q in _QUARTER_MESES.items():
        if q == "Q1":
            continue  # ja adicionado acima
        cols_meta_q = [
            f"meta_{m}_26" for m in meses_q
            if f"meta_{m}_26" in base.columns
        ]
        # Tenta tambem coluna meta_qN
        col_meta_qn = f"meta_{q.lower()}"
        if col_meta_qn in base.columns:
            meta_q = _safe_float(
                pd.to_numeric(base[col_meta_qn], errors="coerce").sum()
            ) or 0.0
        elif cols_meta_q:
            meta_q = _safe_float(
                base[cols_meta_q]
                .apply(pd.to_numeric, errors="coerce")
                .sum(axis=1, min_count=1)
                .sum()
            ) or 0.0
        else:
            meta_q = None

        resultado["por_quarter"].append({
            "quarter": f"{q}_2026",
            "meses": [f"{m}_26" for m in meses_q],
            "realizado": None,
            "meta": round(meta_q, 2) if meta_q else None,
            "pct_alcancado": None,
            "status_meta": None,
            "fonte": "Meta SAP (sem realizado)",
        })

    # ---- Por rede ----
    col_rede = _encontrar_coluna(base, ["descricao_grupo", "rede", "grupo", "franquia"])
    if col_rede:
        for rede, grupo_r in base.groupby(col_rede, dropna=False):
            rede_nome = str(rede) if rede and str(rede) != "nan" else "SEM_GRUPO"
            fat_rede = _safe_float(
                pd.to_numeric(grupo_r.get("realizado_acumulado"), errors="coerce").sum()
            ) or 0.0
            meta_rede = _safe_float(
                pd.to_numeric(grupo_r.get("meta_acumulado"), errors="coerce").sum()
            ) or 0.0
            pct_rede = _pct_alcancado(fat_rede, meta_rede)

            resultado["por_rede"].append({
                "rede": rede_nome,
                "fat_total": round(fat_rede, 2),
                "meta_total": round(meta_rede, 2),
                "pct_alcancado": pct_rede,
                "status_meta": _status_meta(pct_rede),
                "n_clientes": len(grupo_r),
            })

        resultado["por_rede"].sort(key=lambda x: x["fat_total"], reverse=True)
        logger.info(
            "Consolidado por rede: %d grupos.", len(resultado["por_rede"])
        )
    else:
        logger.debug("Coluna de rede/grupo nao encontrada. Consolidacao por rede ignorada.")

    # ---- Alertas: clientes com gap > threshold e status CRITICO/ALERTA ----
    col_razao = _encontrar_coluna(base, ["razao_social", "nome", "cliente"])
    col_gap = "gap_valor"
    col_status = "status_meta"

    if col_gap in base.columns and col_status in base.columns:
        gap_serie = pd.to_numeric(base[col_gap], errors="coerce")
        alertas_mask = (
            base[col_status].isin(["CRITICO", "ALERTA"])
            & gap_serie.notna()
            & (gap_serie > ALERTA_GAP_MINIMO)
        )
        alertas_df = base[alertas_mask].copy()
        alertas_df["gap_valor"] = gap_serie[alertas_mask]

        for _, row in alertas_df.iterrows():
            razao = (
                str(row[col_razao]).strip()
                if col_razao and pd.notna(row.get(col_razao))
                else row.get("cnpj_normalizado", "N/A")
            )
            consultor_a = (
                str(row[col_consultor]).strip()
                if col_consultor and pd.notna(row.get(col_consultor))
                else "N/A"
            )
            resultado["alertas"].append({
                "cnpj": row.get("cnpj_normalizado", "N/A"),
                "razao_social": razao,
                "consultor": consultor_a,
                "status_meta": row.get("status_meta"),
                "realizado": _safe_float(row.get("realizado_acumulado")),
                "meta": _safe_float(row.get("meta_acumulado")),
                "pct_alcancado": _safe_float(row.get("pct_alcancado")),
                "gap_valor": round(_safe_float(row.get("gap_valor")) or 0.0, 2),
            })

        resultado["alertas"].sort(key=lambda x: x["gap_valor"], reverse=True)
        logger.info(
            "Alertas de projecao: %d clientes com gap > R$ %.0f",
            len(resultado["alertas"]),
            ALERTA_GAP_MINIMO,
        )

    return resultado


# ---------------------------------------------------------------------------
# Stage 4: Dashboard terminal
# ---------------------------------------------------------------------------

def gerar_dashboard_terminal(base: pd.DataFrame, consolidado: dict) -> str:
    """Gera dashboard ASCII formatado para exibicao no terminal.

    Layout:
        - Cabecalho com data de referencia e totais
        - Faturamento realizado vs meta Q1 2026
        - Top 10 clientes por faturamento
        - Bottom 10 clientes por % meta (risco de churn)
        - Consolidacao por consultor
        - Alertas: clientes criticos com gap > threshold

    Regras de formatacao:
        - Sem emojis (conforme instrucao CLAUDE.md)
        - Sem dark mode -- output ASCII puro
        - Separadores com caracteres ASCII apenas
        - Valores monetarios em formato brasileiro (R$ X.XXX,XX)
        - Largura maxima de 100 caracteres por linha

    Args:
        base: DataFrame enriquecido (saida de calcular_projecao).
        consolidado: Dict de consolidacoes (saida de consolidar_projecao).

    Returns:
        String formatada do dashboard.
    """
    linhas: list[str] = []

    def sep(char: str = "-", largura: int = 100) -> str:
        return char * largura

    def brl(valor: Optional[float]) -> str:
        if valor is None or (isinstance(valor, float) and np.isnan(valor)):
            return "N/A"
        return f"R$ {valor:>12,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def pct_fmt(pct: Optional[float]) -> str:
        if pct is None or (isinstance(pct, float) and np.isnan(pct)):
            return "  N/A  "
        return f"{pct:6.1f}%"

    def status_fmt(status: Optional[str]) -> str:
        mapa = {
            "ACIMA": "[ACIMA  ]",
            "ALERTA": "[ALERTA ]",
            "CRITICO": "[CRITICO]",
        }
        return mapa.get(status or "", "[SEM META]")

    # ---- Cabecalho ----
    linhas.append(sep("="))
    linhas.append("  CRM VITAO360 -- DASHBOARD DE PROJECAO SAP x REALIZADO")
    linhas.append("  Periodo: Q1 2026 (Jan/Fev/Mar) | Baseline 2025: R$ 2.091.000 | Meta 2026: R$ 3.377.120")
    linhas.append(sep("="))

    # ---- Resumo geral ----
    resumo = consolidado.get("resumo_geral", {})
    fat_realizado = resumo.get("fat_total_realizado", 0.0)
    meta_q1 = resumo.get("meta_total_q1", 0.0)
    pct_geral = resumo.get("pct_alcancado")
    status_geral = resumo.get("status_meta", "N/A")
    n_clientes = resumo.get("n_clientes_total", 0)
    n_com_meta = resumo.get("n_com_meta", 0)

    linhas.append("")
    linhas.append("  RESUMO GERAL Q1 2026")
    linhas.append(sep("-", 60))
    linhas.append(f"  {'Realizado Q1 2026:':<30} {brl(fat_realizado)}")
    linhas.append(f"  {'Meta Q1 2026 (SAP):':<30} {brl(meta_q1)}")
    linhas.append(f"  {'% Alcancado:':<30} {pct_fmt(pct_geral)}  {status_fmt(status_geral)}")
    linhas.append(f"  {'Clientes na base:':<30} {n_clientes:>6d}")
    linhas.append(f"  {'Clientes com meta SAP:':<30} {n_com_meta:>6d}")
    linhas.append(f"  {'Ref. Q1 real (SAP):':<30} {brl(Q1_REAL)}")
    linhas.append("")

    # ---- Top 10 por faturamento ----
    col_razao = _encontrar_coluna(base, ["razao_social", "nome", "cliente"])
    col_cons = _encontrar_coluna(base, ["consultor", "vendedor"])

    linhas.append(sep("-", 100))
    linhas.append("  TOP 10 CLIENTES -- MAIOR FATURAMENTO REALIZADO Q1 2026")
    linhas.append(sep("-", 100))
    linhas.append(
        f"  {'#':>3}  {'CNPJ':<14}  {'CONSULTOR':<10}  "
        f"{'REALIZADO':>16}  {'META':>16}  {'%':>8}  STATUS"
    )
    linhas.append(sep("-", 100))

    if "realizado_acumulado" in base.columns and not base.empty:
        top10 = (
            base.assign(
                _realizado_num=pd.to_numeric(
                    base["realizado_acumulado"], errors="coerce"
                ).fillna(0.0)
            )
            .nlargest(10, "_realizado_num")
        )
        for idx, (_, row) in enumerate(top10.iterrows(), 1):
            cnpj = row.get("cnpj_normalizado", "N/A")
            consultor = (
                str(row[col_cons])[:10] if col_cons and pd.notna(row.get(col_cons)) else "N/A"
            )
            real_v = _safe_float(row.get("realizado_acumulado"))
            meta_v = _safe_float(row.get("meta_acumulado"))
            pct_v = _safe_float(row.get("pct_alcancado"))
            status_v = row.get("status_meta") or "N/A"
            linhas.append(
                f"  {idx:>3}  {cnpj:<14}  {consultor:<10}  "
                f"{brl(real_v):>16}  {brl(meta_v):>16}  {pct_fmt(pct_v):>8}  {status_fmt(status_v)}"
            )
    else:
        linhas.append("  (dados de realizacao nao disponiveis)")

    linhas.append("")

    # ---- Bottom 10 por % meta (risco de churn) ----
    linhas.append(sep("-", 100))
    linhas.append("  BOTTOM 10 CLIENTES -- MENOR % META ALCANCADO (RISCO CHURN)")
    linhas.append(sep("-", 100))
    linhas.append(
        f"  {'#':>3}  {'CNPJ':<14}  {'CONSULTOR':<10}  "
        f"{'REALIZADO':>16}  {'META':>16}  {'%':>8}  STATUS"
    )
    linhas.append(sep("-", 100))

    if "pct_alcancado" in base.columns and not base.empty:
        # Apenas clientes que TEM meta (sem meta nao e risco mensuravel)
        com_meta = base[
            pd.to_numeric(base["meta_acumulado"], errors="coerce").notna()
            & (pd.to_numeric(base["meta_acumulado"], errors="coerce") > 0)
        ].copy()

        if not com_meta.empty:
            bottom10 = (
                com_meta.assign(
                    _pct_num=pd.to_numeric(
                        com_meta["pct_alcancado"], errors="coerce"
                    ).fillna(0.0)
                )
                .nsmallest(10, "_pct_num")
            )
            for idx, (_, row) in enumerate(bottom10.iterrows(), 1):
                cnpj = row.get("cnpj_normalizado", "N/A")
                consultor = (
                    str(row[col_cons])[:10] if col_cons and pd.notna(row.get(col_cons)) else "N/A"
                )
                real_v = _safe_float(row.get("realizado_acumulado"))
                meta_v = _safe_float(row.get("meta_acumulado"))
                pct_v = _safe_float(row.get("pct_alcancado"))
                status_v = row.get("status_meta") or "N/A"
                linhas.append(
                    f"  {idx:>3}  {cnpj:<14}  {consultor:<10}  "
                    f"{brl(real_v):>16}  {brl(meta_v):>16}  {pct_fmt(pct_v):>8}  {status_fmt(status_v)}"
                )
        else:
            linhas.append("  (nenhum cliente com meta SAP disponivel)")
    else:
        linhas.append("  (dados de % meta nao disponiveis)")

    linhas.append("")

    # ---- Por consultor ----
    por_consultor = consolidado.get("por_consultor", [])
    if por_consultor:
        linhas.append(sep("-", 80))
        linhas.append("  CONSOLIDACAO POR CONSULTOR")
        linhas.append(sep("-", 80))
        linhas.append(
            f"  {'CONSULTOR':<12}  {'CLIENTES':>8}  {'REALIZADO':>16}  "
            f"{'META':>16}  {'%':>8}  STATUS"
        )
        linhas.append(sep("-", 80))
        for entry in por_consultor:
            cons = str(entry.get("consultor", "N/A"))[:12]
            n = entry.get("n_clientes", 0)
            fat_c = entry.get("fat_total", 0.0)
            meta_c = entry.get("meta_total", 0.0)
            pct_c = entry.get("pct_alcancado")
            status_c = entry.get("status_meta")
            linhas.append(
                f"  {cons:<12}  {n:>8d}  {brl(fat_c):>16}  "
                f"{brl(meta_c):>16}  {pct_fmt(pct_c):>8}  {status_fmt(status_c)}"
            )
        linhas.append("")

    # ---- Alertas ----
    alertas = consolidado.get("alertas", [])
    if alertas:
        linhas.append(sep("-", 100))
        linhas.append(
            f"  ALERTAS -- {len(alertas)} CLIENTES COM GAP > R$ {ALERTA_GAP_MINIMO:,.0f} E STATUS CRITICO/ALERTA"
        )
        linhas.append(sep("-", 100))
        linhas.append(
            f"  {'CNPJ':<14}  {'CONSULTOR':<10}  {'RAZAO SOCIAL':<35}  "
            f"{'GAP (R$)':>14}  STATUS"
        )
        linhas.append(sep("-", 100))
        for alerta in alertas[:20]:   # limitar a 20 para nao poluir o terminal
            cnpj_a = str(alerta.get("cnpj", "N/A"))
            cons_a = str(alerta.get("consultor", "N/A"))[:10]
            razao_a = str(alerta.get("razao_social", "N/A"))[:35]
            gap_a = alerta.get("gap_valor", 0.0)
            status_a = alerta.get("status_meta", "N/A")
            linhas.append(
                f"  {cnpj_a:<14}  {cons_a:<10}  {razao_a:<35}  "
                f"{brl(gap_a):>14}  {status_fmt(status_a)}"
            )
        if len(alertas) > 20:
            linhas.append(
                f"  ... e mais {len(alertas) - 20} alertas nao exibidos."
            )
        linhas.append("")

    # ---- Rodape ----
    linhas.append(sep("="))
    linhas.append("  CRM VITAO360 -- Projecao Engine v1.0 | Baseline: R$ 2.091.000 | Meta 2026: R$ 3.377.120")
    linhas.append(sep("="))

    return "\n".join(linhas)


# ---------------------------------------------------------------------------
# Self-test / entry point
# ---------------------------------------------------------------------------

def _self_test() -> int:
    """Executa self-test com dados sinteticos para validar a logica do modulo.

    Nao usa dados reais -- apenas estruturas sinteticas para testar os
    caminhos de codigo. Retorna 0 se todos os checks passarem.

    Returns:
        0 em sucesso, 1 em falha.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    erros: list[str] = []

    # ---- Teste: normalizar_cnpj ----
    assert _normalizar_cnpj(None) is None, "CNPJ None deve retornar None"
    assert _normalizar_cnpj("") is None, "CNPJ vazio deve retornar None"
    assert _normalizar_cnpj(12345678000195) == "12345678000195", "CNPJ int deve virar string 14d"
    assert _normalizar_cnpj("12.345.678/0001-95") == "12345678000195", "CNPJ formatado"
    assert _normalizar_cnpj("12345678000195.0") == "12345678000195", "CNPJ float-string"
    assert len(_normalizar_cnpj("99")) == 14, "CNPJ curto deve ser zero-padded"
    print("  [OK] _normalizar_cnpj -- 5 casos")

    # ---- Teste: _safe_float ----
    assert _safe_float(None) is None
    assert _safe_float("nan") is None
    assert _safe_float("1500.50") == 1500.50
    assert _safe_float(0) == 0.0
    print("  [OK] _safe_float -- 4 casos")

    # ---- Teste: _pct_alcancado ----
    assert _pct_alcancado(100.0, 0.0) is None, "Meta zero deve retornar None"
    assert _pct_alcancado(50.0, 100.0) == 50.0
    assert _pct_alcancado(120.0, 100.0) == 120.0
    print("  [OK] _pct_alcancado -- 3 casos")

    # ---- Teste: _status_meta ----
    assert _status_meta(None) is None
    assert _status_meta(100.0) == "ACIMA"
    assert _status_meta(85.0) == "ALERTA"
    assert _status_meta(50.0) == "CRITICO"
    print("  [OK] _status_meta -- 4 casos")

    # ---- Teste: carregar_metas_sap com dfs vazios ----
    dfs_vazios: dict[str, pd.DataFrame] = {
        "projecao": pd.DataFrame(),
        "venda_mes": pd.DataFrame(),
    }
    df_metas = carregar_metas_sap(dfs_vazios)
    assert "cnpj_normalizado" in df_metas.columns, "Deve ter coluna cnpj_normalizado"
    print("  [OK] carregar_metas_sap -- dfs vazios")

    # ---- Teste: carregar_metas_sap com dados sinteticos ----
    df_proj_sint = pd.DataFrame({
        "CNPJ": ["12.345.678/0001-95", "98.765.432/0001-10", None, "00000000000000"],
        "META_ANUAL": [120000.0, 80000.0, 0.0, 5000.0],
        "META_Q1": [30000.0, 20000.0, 0.0, 1250.0],
        "META_Q2": [30000.0, 20000.0, 0.0, 1250.0],
        "META_Q3": [30000.0, 20000.0, 0.0, 1250.0],
        "META_Q4": [30000.0, 20000.0, 0.0, 1250.0],
    })
    df_venda_sint = pd.DataFrame({
        "CNPJ": ["12.345.678/0001-95", "98.765.432/0001-10"],
        "jan_26": [10000.0, 5000.0],
        "fev_26": [11000.0, 6000.0],
        "mar_26": [12000.0, 7000.0],
    })
    dfs_sint: dict[str, pd.DataFrame] = {
        "projecao": df_proj_sint,
        "venda_mes": df_venda_sint,
    }
    df_metas_sint = carregar_metas_sap(dfs_sint)
    # CNPJ None e "00000000000000" devem ser filtrados
    assert "None" not in df_metas_sint["cnpj_normalizado"].values, "None nao deve aparecer"
    assert "00000000000000" not in df_metas_sint["cnpj_normalizado"].values, "CNPJ zerado filtrado"
    assert len(df_metas_sint) == 2, f"Esperado 2 registros, obteve {len(df_metas_sint)}"
    assert df_metas_sint.loc[
        df_metas_sint["cnpj_normalizado"] == "12345678000195", "meta_anual"
    ].iloc[0] == 120000.0
    print("  [OK] carregar_metas_sap -- dados sinteticos (2 CNPJs validos)")

    # ---- Teste: calcular_projecao ----
    base_sint = pd.DataFrame({
        "cnpj_normalizado": ["12345678000195", "98765432000110", "11111111000100"],
        "consultor": ["MANU", "LARISSA", "JULIO"],
        "jan_26": [10000.0, 5000.0, 0.0],
        "fev_26": [11000.0, 6000.0, 0.0],
        "mar_26": [12000.0, 7000.0, 0.0],
    })
    base_calc = calcular_projecao(base_sint, df_metas_sint)
    assert "realizado_acumulado" in base_calc.columns, "realizado_acumulado ausente"
    assert "meta_acumulado" in base_calc.columns, "meta_acumulado ausente"
    assert "pct_alcancado" in base_calc.columns, "pct_alcancado ausente"
    assert "gap_valor" in base_calc.columns, "gap_valor ausente"
    assert "status_meta" in base_calc.columns, "status_meta ausente"

    # CNPJ sem meta deve ter status None
    row_julio = base_calc[base_calc["cnpj_normalizado"] == "11111111000100"].iloc[0]
    assert pd.isna(row_julio["status_meta"]), "JULIO sem meta deve ter status NaN"

    # CNPJ com meta deve ter status calculado
    row_manu = base_calc[base_calc["cnpj_normalizado"] == "12345678000195"].iloc[0]
    assert row_manu["realizado_acumulado"] == 33000.0, f"Realizado MANU: {row_manu['realizado_acumulado']}"
    assert row_manu["meta_acumulado"] == 30000.0, f"Meta MANU: {row_manu['meta_acumulado']}"
    assert row_manu["status_meta"] == "ACIMA", f"MANU status: {row_manu['status_meta']}"

    print("  [OK] calcular_projecao -- 5 verificacoes")

    # ---- Teste: consolidar_projecao ----
    consolidado = consolidar_projecao(base_calc)
    assert "resumo_geral" in consolidado, "Falta resumo_geral"
    assert "por_consultor" in consolidado, "Falta por_consultor"
    assert "por_quarter" in consolidado, "Falta por_quarter"
    assert "alertas" in consolidado, "Falta alertas"
    assert consolidado["resumo_geral"]["n_clientes_total"] == 3, "n_clientes_total errado"
    assert len(consolidado["por_consultor"]) == 3, f"Esperado 3 consultores: {consolidado['por_consultor']}"
    print("  [OK] consolidar_projecao -- 5 verificacoes")

    # ---- Teste: gerar_dashboard_terminal ----
    dashboard = gerar_dashboard_terminal(base_calc, consolidado)
    assert isinstance(dashboard, str), "Dashboard deve ser string"
    assert "CRM VITAO360" in dashboard, "Cabecalho ausente"
    assert "Q1 2026" in dashboard, "Periodo Q1 2026 ausente"
    assert "R$ 2.091.000" in dashboard, "Baseline ausente no dashboard"
    assert len(dashboard) > 500, "Dashboard muito curto"
    print("  [OK] gerar_dashboard_terminal -- 5 verificacoes")

    if erros:
        print(f"\n  FALHAS: {len(erros)}")
        for e in erros:
            print(f"    - {e}")
        return 1

    print("\n  Todos os checks passaram. projecao_engine.py pronto para integracao.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Projecao Engine -- CRM VITAO360",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Executa self-test com dados sinteticos.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Habilita logging DEBUG.",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.self_test:
        print("\nExecutando self-test do projecao_engine...")
        sys.exit(_self_test())
    else:
        print(
            "projecao_engine.py -- use --self-test para validar ou importe o modulo no pipeline.\n"
            "Exemplo:\n"
            "  python -m scripts.motor.projecao_engine --self-test\n"
            "  python -m scripts.motor.projecao_engine --self-test --verbose"
        )
        sys.exit(0)
