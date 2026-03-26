#!/usr/bin/env python3
"""
CRM VITAO360 v2.0 -- Pipeline Completo (Orquestrador)

Encadeia todos os modulos do Motor Operacional em sequencia:
  Stage 1: IMPORT    -- le xlsx FINAL, normaliza CNPJs/vendedores
  Stage 2: CLASSIFY  -- 3-tier (REAL/SINTETICO/ALUCINACAO), unifica base
  Stage 3: MOTOR     -- aplica 92 regras (7 SITUACAO x 14 RESULTADO)
  Stage 4: SINALEIRO -- calcula sinaleiro, tipo_cliente, curva_abc, tentativas
  Stage 5: SCORE     -- score ponderado (0-100) + prioridade P0-P7
  Stage 6: PROJECAO  -- realizado vs meta SAP, % alcancado, dashboard
  Stage 7: AGENDA    -- gera agendas diarias por consultor
  Stage 8: EXPORT    -- salva JSONs de saida e stats

Uso:
    python -m scripts.motor.run_pipeline
    python -m scripts.motor.run_pipeline --skip-import
    python -m scripts.motor.run_pipeline --stage motor
    python -m scripts.motor.run_pipeline --dry-run
    python -m scripts.motor.run_pipeline --verbose

Regras aplicadas (ver CLAUDE.md):
    R4  -- Two-Base: VENDA=R$, LOG=R$0.00
    R5  -- CNPJ sempre string 14 digitos
    R7  -- Faturamento baseline R$ 2.091.000
    R8  -- NUNCA fabricar dados
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths do projeto (raiz = CRM-VITAO360/)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]
_OUTPUT_DIR = _ROOT / "data" / "output" / "motor"
_BASE_UNIFICADA_JSON = _OUTPUT_DIR / "base_unificada.json"

# ---------------------------------------------------------------------------
# ANSI color codes (desabilitados se nao for terminal)
# ---------------------------------------------------------------------------
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"

if not sys.stdout.isatty():
    _GREEN = _RED = _YELLOW = _CYAN = _BOLD = _DIM = _RESET = ""

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("motor.pipeline")

# Mapeamento de stages a partir de --stage
_STAGE_ORDER = ["import", "classify", "motor", "sinaleiro", "score", "projecao", "agenda", "export"]

# DataFrames brutos do import (preservados para stages que precisam de dados nao-unificados)
_cached_dfs: dict[str, "pd.DataFrame"] = {}


# ---------------------------------------------------------------------------
# Serializador JSON (compativel com numpy / pandas types)
# ---------------------------------------------------------------------------

def _json_serial(obj: Any) -> Any:
    """Serializa tipos nao-nativos do JSON (numpy, pandas, datetime).

    Args:
        obj: Objeto a serializar.

    Returns:
        Tipo serializavel ou TypeError.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat() if not pd.isna(obj) else None
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj) if not np.isnan(obj) else None
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if obj is pd.NaT:
        return None
    raise TypeError(f"Tipo nao serializavel: {type(obj).__name__} = {obj!r}")


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Converte DataFrame para lista de dicts serializavel em JSON.

    Trata NaN/NaT/None, Timestamp e numpy types. CNPJ permanece
    como string (R5 — nunca float).

    Args:
        df: DataFrame com quaisquer tipos de colunas.

    Returns:
        Lista de dicts com valores serializaveis.
    """
    registros: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        rec: dict[str, Any] = {}
        for col, val in row.items():
            if val is None or (isinstance(val, float) and np.isnan(val)):
                rec[col] = None
            elif isinstance(val, pd.Timestamp):
                rec[col] = val.isoformat() if not pd.isna(val) else None
            elif isinstance(val, np.integer):
                rec[col] = int(val)
            elif isinstance(val, np.floating):
                rec[col] = float(val) if not np.isnan(val) else None
            elif isinstance(val, np.bool_):
                rec[col] = bool(val)
            else:
                rec[col] = val
        registros.append(rec)
    return registros


# ---------------------------------------------------------------------------
# Contexto de execucao de cada stage
# ---------------------------------------------------------------------------

class StageResult:
    """Resultado de execucao de um stage do pipeline.

    Attributes:
        nome: Identificador do stage (ex: "IMPORT").
        status: "PASS", "FAIL" ou "SKIP".
        registros: Numero de registros processados.
        elapsed: Tempo decorrido em segundos.
        erro: Mensagem de erro (se status == "FAIL").
    """

    def __init__(self, nome: str) -> None:
        self.nome = nome
        self.status = "PASS"
        self.registros = 0
        self.elapsed = 0.0
        self.erro: str | None = None

    def fail(self, msg: str) -> None:
        """Marca stage como FAIL com mensagem de erro."""
        self.status = "FAIL"
        self.erro = msg

    def skip(self) -> None:
        """Marca stage como SKIP (nao executado por --stage)."""
        self.status = "SKIP"


# ---------------------------------------------------------------------------
# Helpers de log por stage
# ---------------------------------------------------------------------------

def _banner(texto: str) -> None:
    """Imprime banner de secao."""
    print(f"\n{_BOLD}{'=' * 56}{_RESET}")
    print(f"{_BOLD} {texto}{_RESET}")
    print(f"{_BOLD}{'=' * 56}{_RESET}")


def _log_stage_start(numero: int, total: int, nome: str) -> float:
    """Imprime inicio de stage e retorna timestamp.

    Args:
        numero: Numero do stage (1-based).
        total: Total de stages.
        nome: Nome do stage.

    Returns:
        Timestamp de inicio (time.time()).
    """
    print(f"\n{_CYAN}[{numero}/{total}] {nome}...{_RESET}")
    return time.time()


def _log_stage_ok(t0: float, msg: str) -> float:
    """Imprime resultado OK com tempo decorrido e retorna elapsed.

    Args:
        t0: Timestamp de inicio.
        msg: Mensagem de resultado.

    Returns:
        Tempo decorrido em segundos.
    """
    elapsed = time.time() - t0
    print(f"      {_GREEN}OK{_RESET} -- {msg} ({elapsed:.1f}s)")
    return elapsed


def _log_stage_fail(t0: float, msg: str) -> float:
    """Imprime resultado FAIL com tempo decorrido e retorna elapsed.

    Args:
        t0: Timestamp de inicio.
        msg: Mensagem de erro.

    Returns:
        Tempo decorrido em segundos.
    """
    elapsed = time.time() - t0
    print(f"      {_RED}FAIL{_RESET} -- {msg} ({elapsed:.1f}s)")
    return elapsed


def _log_stage_skip(nome: str) -> None:
    """Imprime que stage foi ignorado."""
    print(f"      {_DIM}SKIP{_RESET} -- {nome} (antes do stage inicial)")


# ---------------------------------------------------------------------------
# Funcao de carregamento da base_unificada.json (para --skip-import)
# ---------------------------------------------------------------------------

def _carregar_base_json(caminho: Path) -> pd.DataFrame:
    """Carrega base_unificada.json e retorna como DataFrame.

    Garante que cnpj_normalizado permanece string (R5).

    Args:
        caminho: Path do arquivo JSON.

    Returns:
        DataFrame com registros da base unificada.

    Raises:
        FileNotFoundError: Se arquivo nao existir.
        ValueError: Se formato for inesperado.
    """
    if not caminho.exists():
        raise FileNotFoundError(
            f"base_unificada.json nao encontrado em: {caminho}\n"
            "Execute sem --skip-import para gerar o arquivo."
        )

    with caminho.open(encoding="utf-8") as fh:
        dados = json.load(fh)

    if "registros" not in dados:
        raise ValueError(
            f"Formato inesperado em {caminho}: chave 'registros' ausente. "
            f"Chaves encontradas: {list(dados.keys())}"
        )

    df = pd.DataFrame(dados["registros"])

    # Garantir CNPJ como string 14 digitos (R5 — nunca float)
    if "cnpj_normalizado" in df.columns:
        df["cnpj_normalizado"] = df["cnpj_normalizado"].apply(
            lambda v: str(v) if v is not None and str(v) not in ("None", "nan", "") else None
        )

    return df


# ---------------------------------------------------------------------------
# Stage 1: IMPORT
# ---------------------------------------------------------------------------

def stage_import(verbose: bool = False) -> tuple[pd.DataFrame, StageResult]:
    """Stage 1: importa xlsx FINAL, classifica e unifica base.

    Executa o pipeline completo de run_import.py em memoria e retorna
    o DataFrame da base unificada.

    Args:
        verbose: Se True, ativa logging DEBUG.

    Returns:
        Tupla (base_df, StageResult).
    """
    resultado = StageResult("IMPORT")
    t0 = _log_stage_start(1, 8, "IMPORT -- Lendo planilha FINAL")

    try:
        from scripts.motor.import_pipeline import importar_planilha
        from scripts.motor.classify import (
            classificar_registros,
            filtrar_alucinacao,
            unificar_base,
        )

        # 1a. Importar xlsx
        dfs = importar_planilha()
        logger.info("Importacao: %d abas lidas", len(dfs))

        # 1b. Preservar DataFrames brutos para stages posteriores (projecao)
        _cached_dfs.clear()
        _cached_dfs.update(dfs)

        # 1c. Classificar 3-tier
        dfs_class = classificar_registros(dfs)

        # 1d. Filtrar ALUCINACAO
        dfs_filtrado = filtrar_alucinacao(dfs_class)

        # 1e. Unificar base (CARTEIRA como fonte primaria)
        base = unificar_base(dfs_filtrado)

        resultado.registros = len(base)
        resultado.elapsed = _log_stage_ok(
            t0,
            f"{len(base)} registros, {len(base.columns)} colunas",
        )
        return base, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage IMPORT falhou")
        return pd.DataFrame(), resultado


# ---------------------------------------------------------------------------
# Stage 2: CLASSIFY (re-valida base carregada de JSON)
# ---------------------------------------------------------------------------

def stage_classify(base: pd.DataFrame) -> tuple[pd.DataFrame, StageResult]:
    """Stage 2: valida e enriquece classificacao 3-tier na base.

    Quando a base vem de --skip-import (JSON ja processado), este stage
    re-valida a classificacao e garante conformidade com R8.

    Args:
        base: DataFrame da base unificada (do stage IMPORT ou do JSON).

    Returns:
        Tupla (base_enriquecida, StageResult).
    """
    resultado = StageResult("CLASSIFY")
    t0 = _log_stage_start(2, 8, "CLASSIFY -- Validando classificacao 3-tier")

    try:
        from scripts.motor.classify import validar_base

        # Garantir coluna classificacao_3tier
        if "classificacao_3tier" not in base.columns:
            base = base.copy()
            base["classificacao_3tier"] = "REAL"
            logger.info("Coluna classificacao_3tier adicionada como REAL (base do JSON)")

        # Rodar validacao
        validacao = validar_base(base)

        # Checar violacoes criticas (R5, R8)
        alertas: list[str] = []
        if validacao.get("cnpj_como_float", 0) > 0:
            alertas.append(f"CNPJ como float: {validacao['cnpj_como_float']} (R5 VIOLADO)")
        if validacao.get("cnpj_duplicados", 0) > 0:
            alertas.append(f"CNPJ duplicados: {validacao['cnpj_duplicados']}")
        if validacao.get("alucinacao_presente", 0) > 0:
            alertas.append(f"ALUCINACAO presente: {validacao['alucinacao_presente']} (R8 VIOLADO)")

        for alerta in alertas:
            print(f"      {_YELLOW}ALERTA{_RESET}: {alerta}")

        msg = (
            f"{validacao['total_registros']} registros | "
            f"REAL={validacao.get('distribuicao_classificacao', {}).get('REAL', 0)} | "
            f"SINTETICO={validacao.get('distribuicao_classificacao', {}).get('SINTETICO', 0)} | "
            f"ALUCINACAO removidos: {validacao.get('alucinacao_presente', 0)}"
        )

        resultado.registros = len(base)
        resultado.elapsed = _log_stage_ok(t0, msg)
        return base, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage CLASSIFY falhou")
        return base, resultado


# ---------------------------------------------------------------------------
# Stage 3: MOTOR DE REGRAS
# ---------------------------------------------------------------------------

def stage_motor(base: pd.DataFrame) -> tuple[pd.DataFrame, StageResult]:
    """Stage 3: aplica 92 regras (SITUACAO x RESULTADO) em lote.

    Adiciona 8 colunas: estagio_funil, fase, tipo_contato, acao_futura,
    temperatura, followup_dias, grupo_dash, tipo_acao.

    Mapeia colunas da base para os nomes esperados pelo motor_regras
    antes de chamar aplicar_regras_batch().

    Args:
        base: DataFrame com colunas 'situacao' e 'resultado'.

    Returns:
        Tupla (base_enriquecida, StageResult).
    """
    resultado = StageResult("MOTOR")
    t0 = _log_stage_start(3, 8, "MOTOR DE REGRAS -- Aplicando 92 regras")

    try:
        from scripts.motor.motor_regras import aplicar_regras_batch, CAMPOS_OUTPUT

        # Verificar colunas de input
        col_sit = "situacao"
        col_res = "resultado"

        # A base pode ter "situacao" diretamente (do JSON ou da CARTEIRA)
        # ou precisar de mapeamento
        col_sit_real = col_sit if col_sit in base.columns else None
        col_res_real = col_res if col_res in base.columns else None

        # Busca case-insensitive como fallback
        if col_sit_real is None:
            for col in base.columns:
                if "situa" in col.lower():
                    col_sit_real = col
                    break
        if col_res_real is None:
            for col in base.columns:
                if "result" in col.lower() or "resultado" in col.lower():
                    col_res_real = col
                    break

        if col_sit_real is None:
            # Sem coluna de situacao: adicionar coluna vazia e continuar
            logger.warning("Coluna 'situacao' nao encontrada. Motor aplicara fallback None.")
            base = base.copy()
            base["situacao"] = ""
            col_sit_real = "situacao"

        if col_res_real is None:
            logger.warning("Coluna 'resultado' nao encontrada. Motor aplicara fallback None.")
            base = base.copy()
            base["resultado"] = ""
            col_res_real = "resultado"

        # Renomear para nomes canonicos se necessario
        rename_map: dict[str, str] = {}
        if col_sit_real != "situacao":
            rename_map[col_sit_real] = "situacao"
        if col_res_real != "resultado":
            rename_map[col_res_real] = "resultado"

        df_work = base.rename(columns=rename_map) if rename_map else base.copy()

        # Aplicar motor em lote
        df_enriquecido = aplicar_regras_batch(
            df_work,
            col_situacao="situacao",
            col_resultado="resultado",
        )

        # Contar cobertura (quantas linhas tem regra aplicada)
        cobertura = sum(
            1 for val in df_enriquecido["estagio_funil"]
            if val is not None and str(val).strip().upper() not in ("NONE", "NAN", "")
        )

        msg = (
            f"{len(df_enriquecido)} registros | "
            f"cobertura: {cobertura}/{len(df_enriquecido)} | "
            f"8 campos adicionados"
        )

        resultado.registros = len(df_enriquecido)
        resultado.elapsed = _log_stage_ok(t0, msg)
        return df_enriquecido, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage MOTOR falhou")
        return base, resultado


# ---------------------------------------------------------------------------
# Stage 4: SINALEIRO
# ---------------------------------------------------------------------------

def stage_sinaleiro(base: pd.DataFrame) -> tuple[pd.DataFrame, StageResult]:
    """Stage 4: calcula sinaleiro, tipo_cliente, curva_abc e tentativas.

    Usa calcular_sinaleiro_batch() para o sinaleiro principal.
    tipo_cliente e curva_abc: usa valores existentes na base se presentes
    (ja calculados pelo Excel), ou calcula via sinaleiro_engine se ausentes.

    Args:
        base: DataFrame com colunas dias_sem_compra, ciclo_medio, situacao.

    Returns:
        Tupla (base_com_sinaleiro, StageResult).
    """
    resultado = StageResult("SINALEIRO")
    t0 = _log_stage_start(4, 8, "SINALEIRO -- Calculando saude dos clientes")

    try:
        from scripts.motor.sinaleiro_engine import (
            calcular_sinaleiro_batch,
            calcular_tipo_cliente_batch,
            calcular_curva_abc_batch,
            calcular_tentativas_batch,
        )

        df = base.copy()

        # Verificar se sinaleiro ja existe (vem da CARTEIRA)
        sinaleiro_existente = (
            "sinaleiro" in df.columns
            and df["sinaleiro"].notna().sum() > 0
        )

        if sinaleiro_existente:
            # Usar sinaleiro existente; recalcular apenas se vazio
            n_vazios = (df["sinaleiro"].isna() | (df["sinaleiro"] == "")).sum()
            if n_vazios > 0:
                logger.info(
                    "Sinaleiro: %d/%d registros sem valor -- recalculando vazios",
                    n_vazios, len(df),
                )
                # Calcular para todos e usar calcuado apenas onde vazio
                df_calc = calcular_sinaleiro_batch(
                    df,
                    col_dias="dias_sem_compra",
                    col_ciclo="ciclo_medio",
                    col_situacao="situacao",
                )
                mask_vazio = df["sinaleiro"].isna() | (df["sinaleiro"] == "")
                df.loc[mask_vazio, "sinaleiro"] = df_calc.loc[mask_vazio, "sinaleiro"]
            logger.info("Sinaleiro: reaproveitando %d valores existentes", len(df))
        else:
            # Calcular do zero
            df = calcular_sinaleiro_batch(
                df,
                col_dias="dias_sem_compra",
                col_ciclo="ciclo_medio",
                col_situacao="situacao",
            )

        # tipo_cliente: usar existente ou calcular
        if "tipo_cliente" not in df.columns or df["tipo_cliente"].isna().all():
            try:
                df = calcular_tipo_cliente_batch(df)
                logger.info("tipo_cliente calculado via sinaleiro_engine")
            except (AttributeError, TypeError) as exc:
                logger.warning("calcular_tipo_cliente_batch nao disponivel: %s", exc)
                df["tipo_cliente"] = df.get("tipo_cliente", pd.Series(["PROSPECT"] * len(df), index=df.index))

        # curva_abc: usar existente ou calcular
        if "curva_abc" not in df.columns or df["curva_abc"].isna().all():
            try:
                df = calcular_curva_abc_batch(df)
                logger.info("curva_abc calculado via sinaleiro_engine")
            except (AttributeError, TypeError) as exc:
                logger.warning("calcular_curva_abc_batch nao disponivel: %s", exc)
                df["curva_abc"] = df.get("curva_abc", pd.Series(["C"] * len(df), index=df.index))

        # tentativas: usar existente ou calcular
        if "tentativas" not in df.columns or df["tentativas"].isna().all():
            try:
                df = calcular_tentativas_batch(df)
                logger.info("tentativas calculado via sinaleiro_engine")
            except (AttributeError, TypeError) as exc:
                logger.warning("calcular_tentativas_batch nao disponivel: %s", exc)
                df["tentativas"] = df.get("tentativas", pd.Series(["T1"] * len(df), index=df.index))

        # Distribuicao do sinaleiro para o log
        dist_sin = df["sinaleiro"].value_counts().to_dict()
        msg = (
            f"{len(df)} registros | sinaleiro: {dist_sin}"
        )

        resultado.registros = len(df)
        resultado.elapsed = _log_stage_ok(t0, msg)
        return df, resultado

    except ImportError as exc:
        # calcular_tipo_cliente_batch / calcular_curva_abc_batch podem nao existir
        # ainda -- degradar graciosamente usando valores existentes na base
        logger.warning("Algumas funcoes do sinaleiro_engine nao encontradas: %s", exc)
        try:
            from scripts.motor.sinaleiro_engine import calcular_sinaleiro_batch
            df = base.copy()
            df = calcular_sinaleiro_batch(df)

            # Garantir colunas necessarias para stages seguintes
            if "tipo_cliente" not in df.columns:
                df["tipo_cliente"] = "PROSPECT"
            if "curva_abc" not in df.columns:
                df["curva_abc"] = "C"
            if "tentativas" not in df.columns:
                df["tentativas"] = "T1"

            dist_sin = df["sinaleiro"].value_counts().to_dict()
            resultado.registros = len(df)
            resultado.elapsed = _log_stage_ok(t0, f"{len(df)} registros (parcial) | {dist_sin}")
            return df, resultado
        except Exception as exc2:
            resultado.elapsed = _log_stage_fail(t0, str(exc2))
            resultado.fail(str(exc2))
            logger.exception("Stage SINALEIRO falhou")
            return base, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage SINALEIRO falhou")
        return base, resultado


# ---------------------------------------------------------------------------
# Stage 5: SCORE + PRIORIDADE
# ---------------------------------------------------------------------------

def stage_score(base: pd.DataFrame) -> tuple[pd.DataFrame, StageResult]:
    """Stage 5: calcula score ponderado (0-100) e prioridade P0-P7.

    Requer as 6 dimensoes: fase, sinaleiro, curva_abc, temperatura,
    tipo_cliente, tentativas. Colunas ausentes recebem valor padrao seguro.

    Args:
        base: DataFrame com dimensoes de score.

    Returns:
        Tupla (base_com_score, StageResult).
    """
    resultado = StageResult("SCORE")
    t0 = _log_stage_start(5, 8, "SCORE + PRIORIDADE -- Calculando P0-P7")

    try:
        from scripts.motor.score_engine import calcular_score_batch

        df = base.copy()

        # Garantir colunas obrigatorias v2 com defaults seguros
        # score_engine v2: situacao, curva_abc, tipo_cliente, temperatura, tentativas
        _defaults_str: dict[str, str] = {
            "situacao": "PROSPECT",
            "curva_abc": "C",
            "temperatura": "FRIO",
            "tipo_cliente": "PROSPECT",
            "tentativas": "T1",
        }
        for col, default in _defaults_str.items():
            if col not in df.columns:
                logger.warning("Coluna '%s' ausente -- usando default '%s'", col, default)
                df[col] = default
            else:
                # Preencher vazios com default
                mask_vazio = df[col].isna() | (df[col].astype(str).str.strip().isin(["", "None", "nan"]))
                if mask_vazio.sum() > 0:
                    logger.info(
                        "Coluna '%s': %d valores vazios preenchidos com '%s'",
                        col, mask_vazio.sum(), default,
                    )
                    df.loc[mask_vazio, col] = default

        # Colunas opcionais numericas v2
        for col_num in ("dias_sem_compra", "ciclo_medio", "dias_atraso_followup"):
            if col_num not in df.columns:
                df[col_num] = None
        if "ecommerce_carrinho" not in df.columns:
            df["ecommerce_carrinho"] = 0.0

        # Calcular score e prioridade
        df = calcular_score_batch(df)

        # Distribuicao de prioridades
        dist_prio = df["prioridade"].value_counts().to_dict()
        score_medio = df["score"].mean() if "score" in df.columns else 0.0

        msg = (
            f"{len(df)} registros | "
            f"score medio: {score_medio:.1f} | "
            f"prioridades: {dist_prio}"
        )

        resultado.registros = len(df)
        resultado.elapsed = _log_stage_ok(t0, msg)
        return df, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage SCORE falhou")
        return base, resultado


# ---------------------------------------------------------------------------
# Stage 6: PROJECAO
# ---------------------------------------------------------------------------

def stage_projecao(base: pd.DataFrame) -> tuple[pd.DataFrame, StageResult]:
    """Stage 6: calcula realizado vs meta SAP e enriquece base.

    Usa DataFrames brutos do import (_cached_dfs) para extrair metas
    e vendas mensais. Adiciona colunas de projecao ao base.

    Args:
        base: DataFrame com clientes enriquecidos (pos-score).

    Returns:
        Tupla (base_enriquecida, StageResult).
    """
    resultado = StageResult("PROJECAO")
    t0 = _log_stage_start(6, 8, "PROJECAO -- Realizado vs Meta SAP")

    try:
        from scripts.motor.projecao_engine import (
            carregar_metas_sap,
            calcular_projecao,
            consolidar_projecao,
            gerar_dashboard_terminal,
        )

        # 6a. Carregar metas (usa dfs brutos do import)
        if _cached_dfs:
            metas = carregar_metas_sap(_cached_dfs)
        else:
            # Fallback: se pipeline rodou com --skip-import, sem dfs
            logger.warning("Sem DataFrames brutos -- projecao com dados limitados")
            metas = pd.DataFrame()

        if metas.empty:
            resultado.elapsed = _log_stage_ok(
                t0, "Sem metas SAP disponíveis — projeção parcial"
            )
            resultado.registros = len(base)
            return base, resultado

        # 6b. Calcular projecao
        base = calcular_projecao(base, metas)

        # 6c. Consolidar e gerar dashboard
        consolidado = consolidar_projecao(base)
        dashboard = gerar_dashboard_terminal(base, consolidado)

        # Imprimir dashboard
        print(dashboard)

        n_com_meta = base["meta_anual"].notna().sum() if "meta_anual" in base.columns else 0
        resultado.registros = len(base)
        resultado.elapsed = _log_stage_ok(
            t0,
            f"{len(base)} registros, {n_com_meta} com meta SAP",
        )
        return base, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage PROJECAO falhou")
        return base, resultado


# ---------------------------------------------------------------------------
# Stage 7: AGENDA
# ---------------------------------------------------------------------------

def stage_agenda(base: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], StageResult]:
    """Stage 7: gera agendas diarias por consultor.

    Utiliza agenda_engine.gerar_agenda() que internamente:
      - filtra por consultor (DE-PARA aplicado)
      - aplica meta_balance se necessario
      - ordena por prioridade
      - seleciona ate 40 atendimentos (P0 ilimitado, P7 excluido)

    Requer coluna 'consultor_normalizado' ou 'consultor' no DataFrame.

    Args:
        base: DataFrame com colunas score, prioridade e consultor.

    Returns:
        Tupla (dict{consultor: DataFrame_agenda}, StageResult).
    """
    resultado = StageResult("AGENDA")
    t0 = _log_stage_start(7, 8, "AGENDA -- Gerando agendas por consultor")

    try:
        from scripts.motor.agenda_engine import gerar_agenda

        df = base.copy()

        # agenda_engine espera coluna 'consultor' (nao 'consultor_normalizado')
        if "consultor_normalizado" in df.columns and "consultor" not in df.columns:
            df["consultor"] = df["consultor_normalizado"]
        elif "consultor" not in df.columns:
            # Busca fallback
            for col in df.columns:
                if "consult" in col.lower():
                    df["consultor"] = df[col]
                    break
            else:
                logger.warning("Coluna de consultor nao encontrada -- agendas ficarao vazias")
                df["consultor"] = "DESCONHECIDO"

        agendas = gerar_agenda(df)

        total_atend = sum(len(ag) for ag in agendas.values())
        resumo_por_consultor = {
            c: len(ag) for c, ag in agendas.items()
        }

        msg = (
            f"{total_atend} atendimentos totais | "
            f"por consultor: {resumo_por_consultor}"
        )

        resultado.registros = total_atend
        resultado.elapsed = _log_stage_ok(t0, msg)
        return agendas, resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage AGENDA falhou")
        return {}, resultado


# ---------------------------------------------------------------------------
# Stage 7: EXPORT
# ---------------------------------------------------------------------------

def stage_export(
    base: pd.DataFrame,
    agendas: dict[str, pd.DataFrame],
    resultados_stages: list[StageResult],
    t_inicio: float,
    dry_run: bool = False,
) -> StageResult:
    """Stage 7: exporta base enriquecida, agendas e stats para JSON.

    Arquivos gerados em data/output/motor/:
        pipeline_output.json    -- base completa enriquecida
        agenda_CONSULTOR.json   -- agenda diaria por consultor
        pipeline_stats.json     -- metricas e timing de todos os stages

    Args:
        base: DataFrame final com todos os enrichments.
        agendas: Dict {consultor: DataFrame_agenda}.
        resultados_stages: Lista de StageResult para compor stats.
        t_inicio: Timestamp de inicio do pipeline completo.
        dry_run: Se True, nao salva arquivos.

    Returns:
        StageResult do stage EXPORT.
    """
    resultado = StageResult("EXPORT")
    t0 = _log_stage_start(8, 8, "EXPORT -- Salvando outputs")

    if dry_run:
        print(f"      {_YELLOW}DRY RUN{_RESET} -- nenhum arquivo salvo")
        resultado.elapsed = time.time() - t0
        return resultado

    try:
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------------
        # 7a. pipeline_output.json (base completa)
        # ---------------------------------------------------------------
        output_base = _OUTPUT_DIR / "pipeline_output.json"
        registros = _df_to_records(base)

        payload_base: dict[str, Any] = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "versao": "2.0.0",
                "pipeline": "run_pipeline.py",
                "total_registros": len(base),
                "colunas": list(base.columns),
            },
            "registros": registros,
        }

        with output_base.open("w", encoding="utf-8") as fh:
            json.dump(payload_base, fh, ensure_ascii=False, indent=2, default=_json_serial)

        size_base = output_base.stat().st_size / (1024 * 1024)
        print(
            f"      {_GREEN}OK{_RESET} -- pipeline_output.json "
            f"({len(base)} registros, {size_base:.1f} MB)"
        )

        # ---------------------------------------------------------------
        # 7b. agenda_CONSULTOR.json por consultor
        # ---------------------------------------------------------------
        for consultor, df_agenda in agendas.items():
            if df_agenda is None or df_agenda.empty:
                logger.info("Agenda %s vazia -- arquivo JSON gerado com 0 registros", consultor)

            agenda_records = _df_to_records(df_agenda) if not df_agenda.empty else []
            payload_agenda: dict[str, Any] = {
                "metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "consultor": consultor,
                    "data_agenda": datetime.now().strftime("%d/%m/%Y"),
                    "total_atendimentos": len(df_agenda),
                },
                "agenda": agenda_records,
            }

            saida = _OUTPUT_DIR / f"agenda_{consultor}.json"
            with saida.open("w", encoding="utf-8") as fh:
                json.dump(payload_agenda, fh, ensure_ascii=False, indent=2, default=_json_serial)

            print(
                f"      {_GREEN}OK{_RESET} -- agenda_{consultor}.json "
                f"({len(df_agenda)} atendimentos)"
            )

        # ---------------------------------------------------------------
        # 7c. pipeline_stats.json
        # ---------------------------------------------------------------
        elapsed_total = time.time() - t_inicio

        stats_stages: list[dict[str, Any]] = []
        for sr in resultados_stages:
            stats_stages.append({
                "stage": sr.nome,
                "status": sr.status,
                "registros": sr.registros,
                "elapsed_s": round(sr.elapsed, 2),
                "erro": sr.erro,
            })

        dist_prio = (
            base["prioridade"].value_counts().to_dict()
            if "prioridade" in base.columns
            else {}
        )
        dist_consultor = (
            base["consultor_normalizado"].value_counts().to_dict()
            if "consultor_normalizado" in base.columns
            else {}
        )
        dist_sinaleiro = (
            base["sinaleiro"].value_counts().to_dict()
            if "sinaleiro" in base.columns
            else {}
        )

        payload_stats: dict[str, Any] = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "elapsed_total_s": round(elapsed_total, 2),
                "pipeline_versao": "2.0.0",
            },
            "stages": stats_stages,
            "resumo": {
                "total_registros": len(base),
                "distribuicao_prioridade": {
                    str(k): int(v) for k, v in dist_prio.items()
                },
                "distribuicao_consultor": {
                    str(k): int(v) for k, v in dist_consultor.items()
                },
                "distribuicao_sinaleiro": {
                    str(k): int(v) for k, v in dist_sinaleiro.items()
                },
                "total_atendimentos_agenda": sum(
                    len(ag) for ag in agendas.values()
                ),
                "agendas": {
                    c: {"atendimentos": len(ag)} for c, ag in agendas.items()
                },
            },
        }

        stats_path = _OUTPUT_DIR / "pipeline_stats.json"
        with stats_path.open("w", encoding="utf-8") as fh:
            json.dump(payload_stats, fh, ensure_ascii=False, indent=2, default=_json_serial)

        print(f"      {_GREEN}OK{_RESET} -- pipeline_stats.json")

        resultado.registros = len(base) + sum(len(ag) for ag in agendas.values())
        resultado.elapsed = _log_stage_ok(
            t0,
            f"3 arquivos base + {len(agendas)} agendas + stats",
        )
        return resultado

    except Exception as exc:
        resultado.elapsed = _log_stage_fail(t0, str(exc))
        resultado.fail(str(exc))
        logger.exception("Stage EXPORT falhou")
        return resultado


# ---------------------------------------------------------------------------
# Tabela de resumo final
# ---------------------------------------------------------------------------

def _imprimir_tabela_final(
    resultados: list[StageResult],
    elapsed_total: float,
) -> None:
    """Imprime tabela de resumo com status, registros e tempo por stage.

    Args:
        resultados: Lista de StageResult na ordem de execucao.
        elapsed_total: Tempo total do pipeline em segundos.
    """
    _banner("RESUMO DO PIPELINE")
    print()

    col_widths = (12, 6, 12, 10, 40)
    header = (
        f"  {'STAGE':<{col_widths[0]}} "
        f"{'STATUS':<{col_widths[1]}} "
        f"{'REGISTROS':>{col_widths[2]}} "
        f"{'TEMPO':>{col_widths[3]}} "
        f"{'DETALHE':<{col_widths[4]}}"
    )
    print(f"{_BOLD}{header}{_RESET}")
    print("  " + "-" * (sum(col_widths) + 4))

    n_pass = n_fail = n_skip = 0
    for sr in resultados:
        if sr.status == "PASS":
            cor = _GREEN
            n_pass += 1
        elif sr.status == "FAIL":
            cor = _RED
            n_fail += 1
        else:
            cor = _DIM
            n_skip += 1

        detalhe = sr.erro or ""
        if len(detalhe) > col_widths[4] - 3:
            detalhe = detalhe[:col_widths[4] - 6] + "..."

        linha = (
            f"  {sr.nome:<{col_widths[0]}} "
            f"{cor}{sr.status:<{col_widths[1]}}{_RESET} "
            f"{sr.registros:>{col_widths[2]},} "
            f"{sr.elapsed:>{col_widths[3] - 1}.1f}s "
            f"{detalhe:<{col_widths[4]}}"
        )
        print(linha)

    print("  " + "-" * (sum(col_widths) + 4))
    print(f"\n  Stages: {_GREEN}{n_pass} PASS{_RESET}", end="")
    if n_fail:
        print(f"  {_RED}{n_fail} FAIL{_RESET}", end="")
    if n_skip:
        print(f"  {_DIM}{n_skip} SKIP{_RESET}", end="")
    print(f"\n  Tempo total: {elapsed_total:.1f}s")
    print()


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def run_pipeline(
    skip_import: bool = False,
    stage_inicial: str = "import",
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Executa o pipeline completo CRM VITAO360.

    Encadeia todos os 8 stages em ordem, com degradacao gracista:
    se um stage falhar, o pipeline tenta continuar com o proximo
    usando o DataFrame disponivel.

    Args:
        skip_import: Se True, carrega base_unificada.json e pula stage 1.
        stage_inicial: Stage a partir do qual executar
            (import/classify/motor/sinaleiro/score/agenda/export).
        dry_run: Se True, nao salva arquivos no stage 7.
        verbose: Se True, ativa logging DEBUG.

    Returns:
        Dict com: base (DataFrame), agendas (dict), resultados (list[StageResult]),
        elapsed (float), status_geral ("PASS"/"FAIL").
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s -- %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    t_inicio = time.time()
    _banner("CRM VITAO360 v2.0 -- PIPELINE COMPLETO")

    # Determinar a partir de qual stage executar
    try:
        idx_inicial = _STAGE_ORDER.index(stage_inicial.lower())
    except ValueError:
        print(
            f"{_RED}Stage invalido: '{stage_inicial}'. "
            f"Validos: {', '.join(_STAGE_ORDER)}{_RESET}"
        )
        sys.exit(1)

    resultados: list[StageResult] = []

    # DataFrame de trabalho (vai sendo passado e enriquecido entre stages)
    base: pd.DataFrame = pd.DataFrame()
    agendas: dict[str, pd.DataFrame] = {}

    def _deve_executar(nome_stage: str) -> bool:
        """Retorna True se o stage deve ser executado."""
        try:
            return _STAGE_ORDER.index(nome_stage) >= idx_inicial
        except ValueError:
            return True

    # -----------------------------------------------------------------------
    # Stage 1: IMPORT (ou carregamento do JSON)
    # -----------------------------------------------------------------------
    sr_import = StageResult("IMPORT")
    if not _deve_executar("import") or skip_import:
        sr_import.skip()
        if skip_import:
            # Carregar do JSON
            t0_json = time.time()
            print(f"\n{_CYAN}[1/8] IMPORT (skip) -- Carregando base_unificada.json...{_RESET}")
            try:
                base = _carregar_base_json(_BASE_UNIFICADA_JSON)
                elapsed_json = time.time() - t0_json
                print(
                    f"      {_GREEN}OK{_RESET} -- {len(base)} registros de "
                    f"{_BASE_UNIFICADA_JSON.name} ({elapsed_json:.1f}s)"
                )
                sr_import.status = "PASS"
                sr_import.registros = len(base)
                sr_import.elapsed = elapsed_json
            except Exception as exc:
                elapsed_json = time.time() - t0_json
                print(f"      {_RED}FAIL{_RESET} -- {exc} ({elapsed_json:.1f}s)")
                sr_import.fail(str(exc))
                sr_import.elapsed = elapsed_json
    else:
        base, sr_import = stage_import(verbose=verbose)

    resultados.append(sr_import)

    # Se import falhou e base esta vazia: nao ha como continuar
    if sr_import.status == "FAIL" and base.empty:
        print(f"\n{_RED}Pipeline interrompido: base vazia apos stage IMPORT.{_RESET}")
        _imprimir_tabela_final(resultados, time.time() - t_inicio)
        return {
            "base": base,
            "agendas": agendas,
            "resultados": resultados,
            "elapsed": time.time() - t_inicio,
            "status_geral": "FAIL",
        }

    # -----------------------------------------------------------------------
    # Stage 2: CLASSIFY
    # -----------------------------------------------------------------------
    sr_classify = StageResult("CLASSIFY")
    if not _deve_executar("classify"):
        _log_stage_skip("CLASSIFY")
        sr_classify.skip()
    else:
        base, sr_classify = stage_classify(base)
    resultados.append(sr_classify)

    # -----------------------------------------------------------------------
    # Stage 3: MOTOR DE REGRAS
    # -----------------------------------------------------------------------
    sr_motor = StageResult("MOTOR")
    if not _deve_executar("motor"):
        _log_stage_skip("MOTOR")
        sr_motor.skip()
    else:
        base, sr_motor = stage_motor(base)
    resultados.append(sr_motor)

    # -----------------------------------------------------------------------
    # Stage 4: SINALEIRO
    # -----------------------------------------------------------------------
    sr_sinaleiro = StageResult("SINALEIRO")
    if not _deve_executar("sinaleiro"):
        _log_stage_skip("SINALEIRO")
        sr_sinaleiro.skip()
    else:
        base, sr_sinaleiro = stage_sinaleiro(base)
    resultados.append(sr_sinaleiro)

    # -----------------------------------------------------------------------
    # Stage 5: SCORE + PRIORIDADE
    # -----------------------------------------------------------------------
    sr_score = StageResult("SCORE")
    if not _deve_executar("score"):
        _log_stage_skip("SCORE")
        sr_score.skip()
    else:
        base, sr_score = stage_score(base)
    resultados.append(sr_score)

    # -----------------------------------------------------------------------
    # Stage 6: PROJECAO
    # -----------------------------------------------------------------------
    sr_projecao = StageResult("PROJECAO")
    if not _deve_executar("projecao"):
        _log_stage_skip("PROJECAO")
        sr_projecao.skip()
    else:
        base, sr_projecao = stage_projecao(base)
    resultados.append(sr_projecao)

    # -----------------------------------------------------------------------
    # Stage 7: AGENDA
    # -----------------------------------------------------------------------
    sr_agenda = StageResult("AGENDA")
    if not _deve_executar("agenda"):
        _log_stage_skip("AGENDA")
        sr_agenda.skip()
    else:
        agendas, sr_agenda = stage_agenda(base)
    resultados.append(sr_agenda)

    # -----------------------------------------------------------------------
    # Stage 8: EXPORT
    # -----------------------------------------------------------------------
    sr_export = StageResult("EXPORT")
    if not _deve_executar("export"):
        _log_stage_skip("EXPORT")
        sr_export.skip()
    else:
        sr_export = stage_export(
            base=base,
            agendas=agendas,
            resultados_stages=resultados,
            t_inicio=t_inicio,
            dry_run=dry_run,
        )
    resultados.append(sr_export)

    # -----------------------------------------------------------------------
    # Tabela de resumo
    # -----------------------------------------------------------------------
    elapsed_total = time.time() - t_inicio
    _imprimir_tabela_final(resultados, elapsed_total)

    # Status geral: PASS se todos PASS ou SKIP; FAIL se qualquer FAIL
    status_geral = "FAIL" if any(sr.status == "FAIL" for sr in resultados) else "PASS"

    if status_geral == "PASS":
        print(f"  {_GREEN}{_BOLD}STATUS GERAL: PASS{_RESET}\n")
    else:
        n_fail = sum(1 for sr in resultados if sr.status == "FAIL")
        print(f"  {_RED}{_BOLD}STATUS GERAL: FAIL ({n_fail} stage(s) com erro){_RESET}\n")

    return {
        "base": base,
        "agendas": agendas,
        "resultados": resultados,
        "elapsed": elapsed_total,
        "status_geral": status_geral,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CRM VITAO360 v2.0 -- Pipeline Completo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m scripts.motor.run_pipeline
  python -m scripts.motor.run_pipeline --skip-import
  python -m scripts.motor.run_pipeline --stage motor
  python -m scripts.motor.run_pipeline --dry-run
  python -m scripts.motor.run_pipeline --verbose
        """,
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help=(
            "Pular Stage 1 e usar base_unificada.json ja existente "
            f"(path: {_BASE_UNIFICADA_JSON})"
        ),
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="import",
        metavar="STAGE",
        choices=_STAGE_ORDER,
        help=(
            "Executar a partir deste stage (stages anteriores sao SKIP). "
            f"Opcoes: {', '.join(_STAGE_ORDER)}"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Roda pipeline completo sem salvar arquivos no Stage 7.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Logging detalhado (DEBUG level).",
    )

    args = parser.parse_args()

    # --skip-import implica --stage classify (pula apenas o import do xlsx)
    stage_arg = args.stage
    if args.skip_import and stage_arg == "import":
        # --skip-import com --stage import ainda executa a partir de classify
        # (import eh tratado especialmente: carrega JSON em vez de xlsx)
        stage_arg = "import"  # mantido, tratado em run_pipeline()

    resultado = run_pipeline(
        skip_import=args.skip_import,
        stage_inicial=stage_arg,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    sys.exit(0 if resultado["status_geral"] == "PASS" else 1)
