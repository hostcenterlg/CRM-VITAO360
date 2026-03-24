"""
Motor de Sinaleiro — CRM VITAO360 v2.0.

Calcula o sinaleiro de saude do cliente baseado em comportamento de compra:
  VERDE    — dentro do ciclo, cliente saudavel
  AMARELO  — em risco, ciclo ultrapassado mas dentro da margem
  VERMELHO — perigo, muito tempo sem comprar
  ROXO     — prospect/lead (nunca comprou) ou inativo antigo sem ciclo

Tambem calcula:
  - Sinaleiro de redes/franquias (penetracao por potencial)
  - Tipo de cliente (maturidade na carteira)
  - Curva ABC (pareto por faturamento)
  - Tentativas de contato (T1 a NUTRICAO)

Regras extraidas das formulas Excel da CARTEIRA + arquitetura_9_dimensoes.json.
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger("motor.sinaleiro_engine")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Score do sinaleiro para calculo ponderado de prioridade.
# VERMELHO tem score MAXIMO pois requer atencao URGENTE (logica invertida de
# perigo = prioridade, nao de saude).
SCORE_SINALEIRO: dict[str, int] = {
    "VERMELHO": 100,
    "AMARELO": 60,
    "VERDE": 30,
    "ROXO": 0,
}

# Fallback quando ciclo_medio eh 0 ou ausente (clientes sem historico suficiente)
FALLBACK_VERDE_DIAS: int = 50    # <= 50 dias: VERDE
FALLBACK_AMARELO_DIAS: int = 90  # 51-90 dias: AMARELO, > 90: VERMELHO

# Ticket de referencia mensal para calculo de potencial de redes (R$)
TICKET_REF_REDES: float = 525.0

# Meses de referencia para calculo de potencial de redes
MESES_REF_REDES: int = 11

# Situacoes que indicam prospect/lead (nunca compraram)
_SITUACOES_ROXO: frozenset[str] = frozenset({"PROSPECT", "LEAD"})

# Situacoes que indicam cliente novo (sempre VERDE, independente de dias)
_SITUACOES_VERDE_FORCADO: frozenset[str] = frozenset({"NOVO"})

# Situacoes que indicam cliente inativo antigo (influencia no fallback)
_SITUACOES_VERMELHO_FORCADO: frozenset[str] = frozenset({"INAT.ANT"})

# Situacoes que indicam cliente em risco de inativacao recente
_SITUACOES_AMARELO_HINT: frozenset[str] = frozenset({"INAT.REC", "EM RISCO"})

# Valores sentinela de dias/ciclo que indicam dado ausente
_NAN_LIKE: frozenset[str] = frozenset({"nan", "none", "", "-", "n/a", "nd"})


# ---------------------------------------------------------------------------
# Utilitarios internos
# ---------------------------------------------------------------------------

def _to_float_safe(val: Any) -> float | None:
    """Converte valor para float, retorna None se impossivel ou NaN.

    Args:
        val: Qualquer valor (str, int, float, None, NaN).

    Returns:
        Float valido ou None.
    """
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(val, (int, np.integer)):
        return float(val)
    val_str = str(val).strip().lower()
    if val_str in _NAN_LIKE:
        return None
    # Remove separadores de milhar e normaliza decimal
    val_str = val_str.replace(".", "").replace(",", ".")
    try:
        result = float(val_str)
        if math.isnan(result) or math.isinf(result):
            return None
        return result
    except (ValueError, OverflowError):
        return None


def _situacao_upper(situacao: str) -> str:
    """Normaliza string de situacao para UPPER sem espacos extras."""
    return str(situacao).strip().upper() if situacao else ""


# ---------------------------------------------------------------------------
# 1. calcular_sinaleiro — registro unico
# ---------------------------------------------------------------------------

def calcular_sinaleiro(
    dias_sem_compra: float | None,
    ciclo_medio: float | None,
    situacao: str = "",
) -> str:
    """Calcula o sinaleiro de saude de um cliente.

    Logica (em ordem de precedencia):

    1. PROSPECT ou LEAD -> sempre ROXO (nunca compraram)
    2. NOVO -> sempre VERDE (recente, independente de dias)
    3. INAT.ANT -> sempre VERMELHO (inativo antigo)
    4. Sem dias_sem_compra E ciclo_medio: usa situacao como hint
       - INAT.REC / EM RISCO -> AMARELO
       - ATIVO sem dados -> VERDE (beneficio da duvida)
    5. Com ciclo_medio valido (> 0):
       - dias <= ciclo -> VERDE
       - dias <= ciclo + 30 -> AMARELO
       - dias > ciclo + 30 -> VERMELHO
    6. Fallback (ciclo_medio == 0 ou ausente):
       - dias <= 50 -> VERDE
       - dias <= 90 -> AMARELO
       - dias > 90 -> VERMELHO

    Args:
        dias_sem_compra: Dias desde a ultima compra. None/NaN aceito.
        ciclo_medio: Ciclo medio de compras em dias. None/NaN/0 aceito.
        situacao: Status Mercos do cliente (ATIVO, INAT.REC, INAT.ANT,
                  PROSPECT, LEAD, NOVO, EM RISCO...).

    Returns:
        Uma de: "VERDE", "AMARELO", "VERMELHO", "ROXO".
    """
    sit = _situacao_upper(situacao)

    # --- Regra 1: PROSPECT / LEAD -> ROXO ---
    if sit in _SITUACOES_ROXO:
        return "ROXO"

    # --- Regra 2: NOVO -> VERDE (recente, independente de dias) ---
    if sit in _SITUACOES_VERDE_FORCADO:
        return "VERDE"

    # --- Regra 3: INAT.ANT -> VERMELHO (inativo antigo) ---
    if sit in _SITUACOES_VERMELHO_FORCADO:
        return "VERMELHO"

    dias = _to_float_safe(dias_sem_compra)
    ciclo = _to_float_safe(ciclo_medio)

    # Tratar ciclo <= 0 como ausente
    if ciclo is not None and ciclo <= 0.0:
        ciclo = None

    # --- Regra 4: Sem dados de dias ---
    if dias is None:
        if sit in _SITUACOES_AMARELO_HINT:
            return "AMARELO"
        # ATIVO sem dados -> beneficio da duvida = VERDE
        return "VERDE"

    # --- Regra 4b: dias negativo (erro de dado) -> tratar como 0 ---
    if dias < 0:
        logger.warning(
            "dias_sem_compra negativo (%s) — tratado como 0 para calcular sinaleiro",
            dias,
        )
        dias = 0.0

    # --- Regra 5: Ciclo medio valido ---
    if ciclo is not None:
        if dias <= ciclo:
            return "VERDE"
        if dias <= ciclo + 30.0:
            return "AMARELO"
        return "VERMELHO"

    # --- Regra 6: Fallback sem ciclo ---
    # INAT.REC / EM RISCO sem ciclo: usar fallback mais agressivo
    if sit in _SITUACOES_AMARELO_HINT and dias <= FALLBACK_AMARELO_DIAS:
        return "AMARELO"

    if dias <= FALLBACK_VERDE_DIAS:
        return "VERDE"
    if dias <= FALLBACK_AMARELO_DIAS:
        return "AMARELO"
    return "VERMELHO"


# ---------------------------------------------------------------------------
# 2. calcular_sinaleiro_batch — DataFrame
# ---------------------------------------------------------------------------

def calcular_sinaleiro_batch(
    df: pd.DataFrame,
    col_dias: str = "dias_sem_compra",
    col_ciclo: str = "ciclo_medio",
    col_situacao: str = "situacao",
) -> pd.DataFrame:
    """Aplica calcular_sinaleiro a todos os registros de um DataFrame.

    Adiciona (ou substitui) a coluna "sinaleiro" no DataFrame de entrada.
    O DataFrame original nao eh modificado (copia interna).

    Args:
        df: DataFrame com registros de clientes.
        col_dias: Nome da coluna com dias sem compra.
        col_ciclo: Nome da coluna com ciclo medio de compras.
        col_situacao: Nome da coluna com a situacao Mercos.

    Returns:
        DataFrame com coluna "sinaleiro" adicionada.
    """
    df = df.copy()

    # Extrair series, tolerando colunas ausentes
    dias_series: pd.Series = df[col_dias] if col_dias in df.columns else pd.Series(
        [None] * len(df), index=df.index
    )
    ciclo_series: pd.Series = df[col_ciclo] if col_ciclo in df.columns else pd.Series(
        [None] * len(df), index=df.index
    )
    sit_series: pd.Series = df[col_situacao] if col_situacao in df.columns else pd.Series(
        [""] * len(df), index=df.index
    )

    # Tentativa de vetorizacao das regras mais simples usando numpy
    # Depois aplica a funcao escalar apenas para linhas que precisam de logica
    # mais complexa (fallback + situacao). Esta abordagem evita iterrows()
    # para os casos frequentes.

    sit_upper = sit_series.fillna("").astype(str).str.strip().str.upper()

    # Converter dias e ciclo para float (NaN onde invalido)
    dias_num = pd.to_numeric(dias_series, errors="coerce")
    ciclo_num = pd.to_numeric(ciclo_series, errors="coerce")

    # Ciclo <= 0 -> NaN (ausente)
    ciclo_num = ciclo_num.where(ciclo_num > 0, other=np.nan)

    # Inicializar resultado com str vazia
    sinaleiro = pd.Series([""] * len(df), index=df.index, dtype=object)

    # Mascaras de situacoes especiais
    mask_roxo = sit_upper.isin(_SITUACOES_ROXO)
    mask_verde_forcado = sit_upper.isin(_SITUACOES_VERDE_FORCADO)
    mask_vermelho_forcado = sit_upper.isin(_SITUACOES_VERMELHO_FORCADO)
    mask_amarelo_hint = sit_upper.isin(_SITUACOES_AMARELO_HINT)

    # Aplicar regras na ordem de precedencia
    sinaleiro = sinaleiro.where(~mask_roxo, "ROXO")
    sinaleiro = sinaleiro.where(~mask_verde_forcado | (sinaleiro != ""), sinaleiro)
    sinaleiro = sinaleiro.where(~mask_verde_forcado, "VERDE")
    sinaleiro = sinaleiro.where(~mask_vermelho_forcado, "VERMELHO")

    # Linhas sem situacao especial (ainda "")
    mask_sem_resultado = sinaleiro == ""

    # Sem dias -> hint de situacao ou VERDE
    mask_sem_dias = dias_num.isna() & mask_sem_resultado
    sinaleiro = sinaleiro.where(
        ~(mask_sem_dias & mask_amarelo_hint), "AMARELO"
    )
    # Restante sem dias: VERDE
    sinaleiro = sinaleiro.where(~(mask_sem_dias & (sinaleiro == "")), "VERDE")

    # Linhas com dias disponivel (e ainda sem sinaleiro definido)
    mask_sem_resultado = sinaleiro == ""
    mask_tem_dias = dias_num.notna() & mask_sem_resultado

    # Dias negativos -> tratar como 0
    dias_eff = dias_num.clip(lower=0)

    # Com ciclo valido
    mask_tem_ciclo = ciclo_num.notna() & mask_tem_dias
    sinaleiro = sinaleiro.where(
        ~(mask_tem_ciclo & (dias_eff <= ciclo_num)), "VERDE"
    )
    sinaleiro = sinaleiro.where(
        ~(mask_tem_ciclo & (sinaleiro == "") & (dias_eff <= ciclo_num + 30)),
        "AMARELO",
    )
    sinaleiro = sinaleiro.where(
        ~(mask_tem_ciclo & (sinaleiro == "")), "VERMELHO"
    )

    # Sem ciclo: fallback
    mask_sem_ciclo = ciclo_num.isna() & (sinaleiro == "")
    # INAT.REC / EM RISCO sem ciclo
    mask_amarelo_agressivo = mask_sem_ciclo & mask_amarelo_hint & (
        dias_eff <= FALLBACK_AMARELO_DIAS
    )
    sinaleiro = sinaleiro.where(~mask_amarelo_agressivo, "AMARELO")

    # Fallback normal
    mask_fallback = sinaleiro == ""
    sinaleiro = sinaleiro.where(
        ~(mask_fallback & (dias_eff <= FALLBACK_VERDE_DIAS)), "VERDE"
    )
    sinaleiro = sinaleiro.where(
        ~(mask_fallback & (sinaleiro == "") & (dias_eff <= FALLBACK_AMARELO_DIAS)),
        "AMARELO",
    )
    sinaleiro = sinaleiro.where(~(sinaleiro == ""), sinaleiro)
    sinaleiro = sinaleiro.replace("", "VERMELHO")

    df["sinaleiro"] = sinaleiro

    # Log de distribuicao
    dist = df["sinaleiro"].value_counts().to_dict()
    logger.info(
        "sinaleiro_batch: %d registros processados. Distribuicao: %s",
        len(df),
        dist,
    )

    return df


# ---------------------------------------------------------------------------
# 3. calcular_sinaleiro_rede — registro unico
# ---------------------------------------------------------------------------

def calcular_sinaleiro_rede(
    fat_real: float,
    total_lojas: int,
    ticket_ref: float = TICKET_REF_REDES,
    meses: int = MESES_REF_REDES,
) -> tuple[str, float]:
    """Calcula sinaleiro de saude de uma rede/franquia por penetracao.

    Formula de penetracao:
        penetracao = fat_real / (total_lojas * ticket_ref * meses) * 100

    Faixas de classificacao:
        < 1%  -> ROXO      (praticamente sem penetracao)
        1-40% -> VERMELHO  (penetracao baixa, perigo)
        40-60%-> AMARELO   (penetracao media, atencao)
        > 60% -> VERDE     (penetracao boa, saudavel)

    Args:
        fat_real: Faturamento real acumulado da rede (R$).
        total_lojas: Numero total de lojas da rede.
        ticket_ref: Ticket mensal de referencia por loja (padrao R$525).
        meses: Numero de meses de referencia (padrao 11).

    Returns:
        Tupla (sinaleiro: str, penetracao_pct: float).
        penetracao_pct eh 0.0 se potencial == 0.
    """
    fat_real_f = _to_float_safe(fat_real) or 0.0
    total_lojas_i = int(total_lojas) if total_lojas is not None else 0
    ticket_ref_f = _to_float_safe(ticket_ref) or TICKET_REF_REDES
    meses_i = int(meses) if meses else MESES_REF_REDES

    potencial = total_lojas_i * ticket_ref_f * meses_i

    if potencial <= 0.0:
        logger.warning(
            "calcular_sinaleiro_rede: potencial == 0 "
            "(total_lojas=%d, ticket_ref=%.2f, meses=%d) -> ROXO",
            total_lojas_i,
            ticket_ref_f,
            meses_i,
        )
        return ("ROXO", 0.0)

    penetracao = (fat_real_f / potencial) * 100.0

    if penetracao < 1.0:
        return ("ROXO", penetracao)
    if penetracao < 40.0:
        return ("VERMELHO", penetracao)
    if penetracao < 60.0:
        return ("AMARELO", penetracao)
    return ("VERDE", penetracao)


# ---------------------------------------------------------------------------
# 4. calcular_sinaleiro_redes_batch — DataFrame de redes
# ---------------------------------------------------------------------------

def calcular_sinaleiro_redes_batch(
    df: pd.DataFrame,
    col_fat_real: str = "total_2025",
    col_total_lojas: str = "total_lojas",
    ticket_ref: float = TICKET_REF_REDES,
    meses: int = MESES_REF_REDES,
) -> pd.DataFrame:
    """Aplica calcular_sinaleiro_rede a todas as linhas de um DataFrame de redes.

    Adiciona colunas "sinaleiro_rede" e "penetracao_pct" ao DataFrame.

    Args:
        df: DataFrame com registros de redes/franquias.
        col_fat_real: Coluna com faturamento real da rede.
        col_total_lojas: Coluna com total de lojas.
        ticket_ref: Ticket mensal de referencia por loja.
        meses: Numero de meses de referencia.

    Returns:
        DataFrame com colunas "sinaleiro_rede" e "penetracao_pct" adicionadas.
    """
    df = df.copy()

    fat_series = (
        pd.to_numeric(df[col_fat_real], errors="coerce").fillna(0.0)
        if col_fat_real in df.columns
        else pd.Series([0.0] * len(df), index=df.index)
    )
    lojas_series = (
        pd.to_numeric(df[col_total_lojas], errors="coerce").fillna(0).astype(int)
        if col_total_lojas in df.columns
        else pd.Series([0] * len(df), index=df.index)
    )

    resultados = [
        calcular_sinaleiro_rede(fat, lojas, ticket_ref, meses)
        for fat, lojas in zip(fat_series, lojas_series)
    ]

    df["sinaleiro_rede"] = [r[0] for r in resultados]
    df["penetracao_pct"] = [r[1] for r in resultados]

    dist = df["sinaleiro_rede"].value_counts().to_dict()
    logger.info(
        "sinaleiro_redes_batch: %d redes processadas. Distribuicao: %s",
        len(df),
        dist,
    )

    return df


# ---------------------------------------------------------------------------
# 5. calcular_tipo_cliente — registro unico
# ---------------------------------------------------------------------------

def calcular_tipo_cliente(
    num_compras: int,
    meses_ativo: int,
    situacao: str = "",
) -> str:
    """Calcula o tipo de cliente com base em maturidade na carteira.

    Hierarquia de maturidade (da mais imatura para a mais madura):
        PROSPECT     — 0 compras, situacao PROSPECT
        LEAD         — 0 compras, situacao LEAD (interesse mas sem pedido)
        NOVO         — 1 compra
        EM DESENVOLVIMENTO — 2-3 compras
        RECORRENTE   — 4-6 compras E 3+ meses ativo
        FIDELIZADO   — 7-11 compras E 5+ meses ativo
        MADURO       — 12+ compras E 7+ meses ativo

    Para atingir RECORRENTE, FIDELIZADO ou MADURO, o cliente precisa tanto
    do numero de compras quanto do tempo minimo ativo. Se so o numero for
    atingido mas o tempo nao, cai para o tier anterior.

    Args:
        num_compras: Numero total de pedidos/compras do cliente.
        meses_ativo: Quantos meses o cliente esta ativo na carteira.
        situacao: Status Mercos (PROSPECT, LEAD, ATIVO, INAT.REC, etc.).

    Returns:
        Uma de: PROSPECT, LEAD, NOVO, EM DESENVOLVIMENTO, RECORRENTE,
                FIDELIZADO, MADURO.
    """
    sit = _situacao_upper(situacao)
    n = int(num_compras) if num_compras is not None and not (
        isinstance(num_compras, float) and math.isnan(num_compras)
    ) else 0
    m = int(meses_ativo) if meses_ativo is not None and not (
        isinstance(meses_ativo, float) and math.isnan(meses_ativo)
    ) else 0

    # Prospect e Lead: nunca compraram
    if n <= 0:
        if sit == "LEAD":
            return "LEAD"
        return "PROSPECT"

    # A partir de 1 compra
    if n == 1:
        return "NOVO"

    if n <= 3:
        return "EM DESENVOLVIMENTO"

    # Para RECORRENTE em diante, tempo minimo tambem importa
    if n <= 6:
        if m >= 3:
            return "RECORRENTE"
        return "EM DESENVOLVIMENTO"

    if n <= 11:
        if m >= 5:
            return "FIDELIZADO"
        return "RECORRENTE"

    # 12+ compras
    if m >= 7:
        return "MADURO"
    return "FIDELIZADO"


# ---------------------------------------------------------------------------
# 6. calcular_tipo_cliente_batch — DataFrame
# ---------------------------------------------------------------------------

def calcular_tipo_cliente_batch(
    df: pd.DataFrame,
    col_num_compras: str = "n_compras",
    col_meses_ativo: str = "meses_ativo",
    col_situacao: str = "situacao",
) -> pd.DataFrame:
    """Aplica calcular_tipo_cliente a todos os registros de um DataFrame.

    Adiciona (ou substitui) a coluna "tipo_cliente" no DataFrame.

    Args:
        df: DataFrame com registros de clientes.
        col_num_compras: Coluna com numero de compras.
        col_meses_ativo: Coluna com meses ativo na carteira.
        col_situacao: Coluna com situacao Mercos.

    Returns:
        DataFrame com coluna "tipo_cliente" adicionada.
    """
    df = df.copy()

    n_series = (
        pd.to_numeric(df[col_num_compras], errors="coerce").fillna(0).astype(int)
        if col_num_compras in df.columns
        else pd.Series([0] * len(df), index=df.index)
    )
    m_series = (
        pd.to_numeric(df[col_meses_ativo], errors="coerce").fillna(0).astype(int)
        if col_meses_ativo in df.columns
        else pd.Series([0] * len(df), index=df.index)
    )
    sit_series = (
        df[col_situacao].fillna("").astype(str)
        if col_situacao in df.columns
        else pd.Series([""] * len(df), index=df.index)
    )

    df["tipo_cliente"] = [
        calcular_tipo_cliente(n, m, s)
        for n, m, s in zip(n_series, m_series, sit_series)
    ]

    dist = df["tipo_cliente"].value_counts().to_dict()
    logger.info(
        "tipo_cliente_batch: %d registros processados. Distribuicao: %s",
        len(df),
        dist,
    )

    return df


# ---------------------------------------------------------------------------
# 7. calcular_curva_abc — DataFrame
# ---------------------------------------------------------------------------

def calcular_curva_abc(
    df: pd.DataFrame,
    col_faturamento: str = "total_2025",
) -> pd.DataFrame:
    """Classifica clientes em curva ABC por faturamento (Pareto).

    Criterio:
        A — top 20% do faturamento acumulado (os que mais faturam)
        B — proximo 30% do faturamento acumulado
        C — restante 50%

    Apenas clientes com faturamento > 0 entram na classificacao.
    Clientes sem faturamento (0 ou ausente) recebem "C" por padrao.

    Args:
        df: DataFrame com registros de clientes.
        col_faturamento: Coluna com faturamento total para classificacao.

    Returns:
        DataFrame com coluna "curva_abc" adicionada.
    """
    df = df.copy()

    if col_faturamento not in df.columns:
        logger.warning(
            "calcular_curva_abc: coluna '%s' nao encontrada. "
            "Todos recebem 'C'.",
            col_faturamento,
        )
        df["curva_abc"] = "C"
        return df

    fat = pd.to_numeric(df[col_faturamento], errors="coerce").fillna(0.0)

    # Inicializar todos como C
    df["curva_abc"] = "C"

    # Apenas clientes com faturamento > 0
    mask_positivo = fat > 0.0
    total_positivos = mask_positivo.sum()

    if total_positivos == 0:
        logger.warning(
            "calcular_curva_abc: nenhum cliente com faturamento > 0. "
            "Todos recebem 'C'."
        )
        return df

    # Ordenar por faturamento decrescente (apenas positivos)
    fat_positivo = fat[mask_positivo].sort_values(ascending=False)
    fat_total = fat_positivo.sum()

    fat_acumulado = fat_positivo.cumsum()
    fat_acumulado_pct = fat_acumulado / fat_total * 100.0

    # Classificar A (ate 80%), B (ate 50% seguinte = 80% total?).
    # Pareto real: A = top 20% do VOLUME cumulativo, mas em CRM B2B
    # usamos: A = top 80% do faturamento, B = proximo 15%, C = restante 5%?
    # A spec diz: A=top 20%, B=prox 30%, C=50% rest (por numero de clientes).
    # Implementacao por NUMERO de clientes (n_clientes, nao por valor):
    #   - Ordenar por fat desc
    #   - Top 20% dos registros positivos = A
    #   - Proximo 30% = B
    #   - Restante = C
    # Esta e a abordagem usada na arquitetura_9_dimensoes.json.

    n_a = max(1, round(total_positivos * 0.20))
    n_b = max(1, round(total_positivos * 0.30))

    indices_a = fat_positivo.index[:n_a]
    indices_b = fat_positivo.index[n_a: n_a + n_b]

    df.loc[indices_a, "curva_abc"] = "A"
    df.loc[indices_b, "curva_abc"] = "B"
    # C ja esta setado como default para todos

    dist = df["curva_abc"].value_counts().to_dict()
    fat_por_curva = {
        curva: float(fat[df["curva_abc"] == curva].sum())
        for curva in ["A", "B", "C"]
    }
    logger.info(
        "curva_abc: %d registros. Dist: %s. Fat R$: %s",
        len(df),
        dist,
        {k: f"{v:,.2f}" for k, v in fat_por_curva.items()},
    )

    return df


# ---------------------------------------------------------------------------
# 8. calcular_tentativa — registro unico
# ---------------------------------------------------------------------------

def calcular_tentativa(
    historico_contatos: int,
    ultimo_respondeu: bool,
) -> str:
    """Calcula o estagio de tentativa de contato do consultor.

    Regra de RESET: se o cliente respondeu na ultima interacao, volta para
    T1 (recomecar ciclo de contato — o cliente esta engajado).

    Sequencia normal:
        1 contato  -> T1
        2 contatos -> T2
        3 contatos -> T3
        4 contatos -> T4
        5+ contatos -> NUTRICAO (cliente nao engajado, modo passivo)

    Args:
        historico_contatos: Numero de contatos registrados com o cliente.
        ultimo_respondeu: Se True, o cliente respondeu na ultima interacao.

    Returns:
        Uma de: "T1", "T2", "T3", "T4", "NUTRICAO".
    """
    # RESET: respondeu -> T1 (recomecar)
    if ultimo_respondeu:
        return "T1"

    n = int(historico_contatos) if historico_contatos is not None and not (
        isinstance(historico_contatos, float) and math.isnan(historico_contatos)
    ) else 0

    if n <= 0:
        return "T1"
    if n == 1:
        return "T1"
    if n == 2:
        return "T2"
    if n == 3:
        return "T3"
    if n == 4:
        return "T4"
    return "NUTRICAO"


# ---------------------------------------------------------------------------
# 9. stats — sumario estatistico
# ---------------------------------------------------------------------------

def stats(df: pd.DataFrame) -> dict[str, Any]:
    """Gera distribuicao estatistica das dimensoes calculadas.

    Args:
        df: DataFrame com colunas calculadas pelo sinaleiro_engine.

    Returns:
        Dict com distribuicao de cada dimensao presente no DataFrame.
        Chaves: "sinaleiro", "tipo_cliente", "curva_abc", "sinaleiro_rede".
        Cada chave mapeia para um dict {valor: contagem}.
    """
    resultado: dict[str, Any] = {
        "total_registros": len(df),
    }

    dimensoes = ["sinaleiro", "tipo_cliente", "curva_abc", "sinaleiro_rede"]

    for dim in dimensoes:
        if dim in df.columns:
            dist = df[dim].value_counts(dropna=False).to_dict()
            # Converter chaves NaN para string legivel
            dist_clean = {
                (str(k) if not (isinstance(k, float) and math.isnan(k)) else "NULO"): int(v)
                for k, v in dist.items()
            }
            resultado[dim] = dist_clean
        else:
            resultado[dim] = {}

    # Score medio do sinaleiro (para benchmark de saude da carteira)
    if "sinaleiro" in df.columns:
        scores = df["sinaleiro"].map(SCORE_SINALEIRO).dropna()
        resultado["score_sinaleiro_medio"] = round(float(scores.mean()), 1) if len(scores) > 0 else 0.0

    return resultado


# ---------------------------------------------------------------------------
# CLI de teste — executar com: python -m scripts.motor.sinaleiro_engine --test
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    """Roda testes funcionais e de borda para todas as funcoes do modulo."""
    import sys

    erros: list[str] = []

    def check(descricao: str, resultado: Any, esperado: Any) -> None:
        if resultado != esperado:
            msg = f"FALHA: {descricao} -> got={resultado!r}, expected={esperado!r}"
            erros.append(msg)
            print(f"  [FAIL] {msg}")
        else:
            print(f"  [OK]   {descricao}")

    print("\n=== TEST: calcular_sinaleiro ===")
    # Casos normais com ciclo
    check("VERDE: dias=20, ciclo=30", calcular_sinaleiro(20, 30), "VERDE")
    check("VERDE: dias=30, ciclo=30", calcular_sinaleiro(30, 30), "VERDE")
    check("AMARELO: dias=50, ciclo=30", calcular_sinaleiro(50, 30), "AMARELO")
    check("AMARELO: dias=60, ciclo=30", calcular_sinaleiro(60, 30), "AMARELO")
    check("VERMELHO: dias=61, ciclo=30", calcular_sinaleiro(61, 30), "VERMELHO")
    check("VERMELHO: dias=200, ciclo=30", calcular_sinaleiro(200, 30), "VERMELHO")

    # Situacoes forcadas
    check("ROXO: PROSPECT", calcular_sinaleiro(None, None, "PROSPECT"), "ROXO")
    check("ROXO: LEAD", calcular_sinaleiro(200, 30, "LEAD"), "ROXO")
    check("VERDE: NOVO", calcular_sinaleiro(None, None, "NOVO"), "VERDE")
    check("VERMELHO: INAT.ANT", calcular_sinaleiro(None, None, "INAT.ANT"), "VERMELHO")
    check("AMARELO: INAT.REC sem dados", calcular_sinaleiro(None, None, "INAT.REC"), "AMARELO")
    check("AMARELO: EM RISCO sem dados", calcular_sinaleiro(None, None, "EM RISCO"), "AMARELO")

    # Edge cases: None/0/negativo
    check("VERDE: dias=None, ciclo=None, ATIVO", calcular_sinaleiro(None, None, "ATIVO"), "VERDE")
    check("VERDE: dias=0, ciclo=30", calcular_sinaleiro(0, 30), "VERDE")
    check("VERDE: dias negativo", calcular_sinaleiro(-5, 30), "VERDE")
    check("VERDE: ciclo=0 usa fallback, dias=40", calcular_sinaleiro(40, 0), "VERDE")
    check("AMARELO: ciclo=0, dias=70", calcular_sinaleiro(70, 0), "AMARELO")
    check("VERMELHO: ciclo=0, dias=100", calcular_sinaleiro(100, 0), "VERMELHO")
    check("VERDE: ciclo=None, dias=40", calcular_sinaleiro(40, None), "VERDE")
    check("VERDE: ciclo=nan, dias=25", calcular_sinaleiro(25, float("nan")), "VERDE")
    check("VERDE: dias=nan, ciclo=30, ATIVO", calcular_sinaleiro(float("nan"), 30, "ATIVO"), "VERDE")

    print("\n=== TEST: calcular_sinaleiro_batch ===")
    df_test = pd.DataFrame({
        "dias_sem_compra": [20, 50, 100, None, None, None, 40, 70, 100],
        "ciclo_medio":     [30, 30,  30,   30,    0,  None, 0,  0,   0],
        "situacao":        ["ATIVO", "ATIVO", "ATIVO", "INAT.REC", "NOVO", "PROSPECT",
                            "ATIVO", "ATIVO", "ATIVO"],
    })
    esperados = ["VERDE", "AMARELO", "VERMELHO", "AMARELO", "VERDE", "ROXO",
                 "VERDE", "AMARELO", "VERMELHO"]
    df_resultado = calcular_sinaleiro_batch(df_test)
    for i, (got, exp) in enumerate(zip(df_resultado["sinaleiro"], esperados)):
        check(f"batch[{i}] situacao={df_test.at[i,'situacao']}", got, exp)

    print("\n=== TEST: calcular_sinaleiro_rede ===")
    check("ROXO: penetracao < 1%",
          calcular_sinaleiro_rede(100, 20)[0], "ROXO")
    check("VERMELHO: penetracao 1-40%",
          calcular_sinaleiro_rede(500, 5)[0], "VERMELHO")
    check("AMARELO: penetracao 40-60%",
          calcular_sinaleiro_rede(14_000, 5)[0], "AMARELO")
    check("VERDE: penetracao > 60%",
          calcular_sinaleiro_rede(25_000, 5)[0], "VERDE")
    check("ROXO: total_lojas=0",
          calcular_sinaleiro_rede(10_000, 0)[0], "ROXO")
    pct = calcular_sinaleiro_rede(525 * 11 * 10, 10)[1]
    check("penetracao=100% (fat=potencial)", round(pct, 1), 100.0)

    print("\n=== TEST: calcular_tipo_cliente ===")
    check("PROSPECT: 0 compras", calcular_tipo_cliente(0, 0, "PROSPECT"), "PROSPECT")
    check("LEAD: 0 compras, LEAD", calcular_tipo_cliente(0, 0, "LEAD"), "LEAD")
    check("NOVO: 1 compra", calcular_tipo_cliente(1, 1, "ATIVO"), "NOVO")
    check("EM DESENVOLVIMENTO: 2 compras", calcular_tipo_cliente(2, 2, "ATIVO"), "EM DESENVOLVIMENTO")
    check("EM DESENVOLVIMENTO: 3 compras", calcular_tipo_cliente(3, 4, "ATIVO"), "EM DESENVOLVIMENTO")
    check("EM DESENVOLVIMENTO: 5 compras, 2 meses (sem tempo min)",
          calcular_tipo_cliente(5, 2, "ATIVO"), "EM DESENVOLVIMENTO")
    check("RECORRENTE: 4 compras, 3 meses", calcular_tipo_cliente(4, 3, "ATIVO"), "RECORRENTE")
    check("RECORRENTE: 6 compras, 5 meses", calcular_tipo_cliente(6, 5, "ATIVO"), "RECORRENTE")
    check("RECORRENTE: 8 compras, 3 meses (sem tempo min para fidelizado)",
          calcular_tipo_cliente(8, 3, "ATIVO"), "RECORRENTE")
    check("FIDELIZADO: 7 compras, 5 meses", calcular_tipo_cliente(7, 5, "ATIVO"), "FIDELIZADO")
    check("FIDELIZADO: 11 compras, 6 meses", calcular_tipo_cliente(11, 6, "ATIVO"), "FIDELIZADO")
    check("FIDELIZADO: 15 compras, 5 meses (sem tempo min para maduro)",
          calcular_tipo_cliente(15, 5, "ATIVO"), "FIDELIZADO")
    check("MADURO: 12 compras, 7 meses", calcular_tipo_cliente(12, 7, "ATIVO"), "MADURO")
    check("MADURO: 50 compras, 24 meses", calcular_tipo_cliente(50, 24, "ATIVO"), "MADURO")
    # Edge cases
    check("PROSPECT: num_compras=None", calcular_tipo_cliente(None, 5, "ATIVO"), "PROSPECT")
    check("PROSPECT: num_compras=nan", calcular_tipo_cliente(float("nan"), 5, "ATIVO"), "PROSPECT")

    print("\n=== TEST: calcular_curva_abc ===")
    df_abc = pd.DataFrame({
        "total_2025": [1000, 800, 600, 400, 300, 200, 100, 50, 20, 10],
    })
    df_abc_res = calcular_curva_abc(df_abc)
    # 10 registros: A=top 20%=2, B=prox 30%=3, C=resto 5
    check("ABC A: primeiros 2", list(df_abc_res["curva_abc"][:2]), ["A", "A"])
    check("ABC B: proximos 3", list(df_abc_res["curva_abc"][2:5]), ["B", "B", "B"])
    check("ABC C: restante", list(df_abc_res["curva_abc"][5:]), ["C", "C", "C", "C", "C"])

    df_abc_zero = pd.DataFrame({"total_2025": [0, 0, 0]})
    df_abc_zero_res = calcular_curva_abc(df_abc_zero)
    check("ABC todos zero -> C", list(df_abc_zero_res["curva_abc"]), ["C", "C", "C"])

    df_abc_sem_col = pd.DataFrame({"faturamento": [1000]})
    df_abc_sem_col_res = calcular_curva_abc(df_abc_sem_col)
    check("ABC sem coluna -> C", df_abc_sem_col_res["curva_abc"].iloc[0], "C")

    print("\n=== TEST: calcular_tentativa ===")
    check("T1: respondeu=True (RESET)", calcular_tentativa(5, True), "T1")
    check("T1: 0 contatos", calcular_tentativa(0, False), "T1")
    check("T1: 1 contato", calcular_tentativa(1, False), "T1")
    check("T2: 2 contatos", calcular_tentativa(2, False), "T2")
    check("T3: 3 contatos", calcular_tentativa(3, False), "T3")
    check("T4: 4 contatos", calcular_tentativa(4, False), "T4")
    check("NUTRICAO: 5 contatos", calcular_tentativa(5, False), "NUTRICAO")
    check("NUTRICAO: 100 contatos", calcular_tentativa(100, False), "NUTRICAO")
    check("T1: None contatos", calcular_tentativa(None, False), "T1")

    print("\n=== TEST: stats ===")
    df_stats = pd.DataFrame({
        "sinaleiro": ["VERDE", "VERDE", "AMARELO", "VERMELHO", "ROXO"],
        "tipo_cliente": ["MADURO", "FIDELIZADO", "RECORRENTE", "NOVO", "PROSPECT"],
        "curva_abc": ["A", "A", "B", "C", "C"],
    })
    s = stats(df_stats)
    check("stats total_registros", s["total_registros"], 5)
    check("stats sinaleiro VERDE", s["sinaleiro"].get("VERDE", 0), 2)
    check("stats curva_abc A", s["curva_abc"].get("A", 0), 2)
    check("stats score_sinaleiro_medio",
          s["score_sinaleiro_medio"],
          round((30 + 30 + 60 + 100 + 0) / 5, 1))

    print(f"\n{'='*50}")
    if erros:
        print(f"FALHAS: {len(erros)}")
        for e in erros:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"Todos os testes passaram. (0 falhas)")


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    if "--test" in sys.argv:
        _run_tests()
    else:
        print(
            "Sinaleiro Engine — CRM VITAO360 v2.0\n"
            "Uso: python -m scripts.motor.sinaleiro_engine --test\n"
            "     (para rodar suite de testes funcionais)"
        )
