#!/usr/bin/env python3
"""
CRM VITAO360 v2.0 -- Import Pipeline
Executa: importar -> classificar -> filtrar -> unificar -> validar -> exportar

Uso:
    python -m scripts.motor.run_import
    python -m scripts.motor.run_import --verbose
    python -m scripts.motor.run_import --dry-run
    python -m scripts.motor.run_import --caminho "path/to/planilha.xlsx"
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# ANSI color codes (para terminal)
# ---------------------------------------------------------------------------
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# Desabilitar cores se nao for terminal
if not sys.stdout.isatty():
    _GREEN = _RED = _YELLOW = _CYAN = _BOLD = _RESET = ""


def _json_serializer(obj: Any) -> Any:
    """Serializa tipos nao-nativos do JSON.

    Trata: datetime, date, NaN, NaT, numpy types, Timestamp.
    """
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, pd.Timestamp):
        if pd.isna(obj):
            return None
        return obj.isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        if np.isnan(obj):
            return None
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, pd.NaT.__class__):
        return None
    if obj is pd.NaT:
        return None
    raise TypeError(f"Tipo nao serializavel: {type(obj).__name__} = {obj!r}")


def run_pipeline(
    caminho: Path | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Executa o pipeline completo de importacao.

    Args:
        caminho: Path da planilha (default: CAMINHO_PLANILHA do config)
        dry_run: Se True, nao exporta JSON
        verbose: Se True, logging detalhado

    Returns:
        Dict com resultado completo: metadata, base, validacao
    """
    # Configurar logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(name)s - %(levelname)s - %(message)s",
        force=True,
    )
    logger = logging.getLogger("motor.run_import")

    t_total = time.time()

    print(f"\n{_BOLD}{'=' * 52}{_RESET}")
    print(f"{_BOLD} CRM VITAO360 v2.0 -- IMPORT PIPELINE{_RESET}")
    print(f"{_BOLD}{'=' * 52}{_RESET}\n")

    # ------------------------------------------------------------------
    # 1. Importar planilha
    # ------------------------------------------------------------------
    print(f"{_CYAN}[1/6] Importando planilha...{_RESET}")
    t0 = time.time()

    from scripts.motor.import_pipeline import importar_planilha

    dfs = importar_planilha(caminho)
    elapsed_import = time.time() - t0

    abas_lidas = len(dfs)
    total_abas = 18  # 14 relevantes + 4 consultor
    print(f"      {_GREEN}OK{_RESET} — {abas_lidas}/{total_abas} abas em {elapsed_import:.1f}s\n")

    # ------------------------------------------------------------------
    # 2. Classificar registros
    # ------------------------------------------------------------------
    print(f"{_CYAN}[2/6] Classificando registros (3-tier)...{_RESET}")
    t0 = time.time()

    from scripts.motor.classify import classificar_registros

    dfs_class = classificar_registros(dfs)
    elapsed_classify = time.time() - t0

    # Distribuicao geral
    dist_geral: dict[str, int] = {}
    for df in dfs_class.values():
        if "classificacao_3tier" in df.columns and len(df) > 0:
            for val, count in df["classificacao_3tier"].value_counts().items():
                dist_geral[val] = dist_geral.get(val, 0) + int(count)

    print(f"      {_GREEN}OK{_RESET} — Distribuicao: {dist_geral} ({elapsed_classify:.1f}s)\n")

    # ------------------------------------------------------------------
    # 3. Filtrar ALUCINACAO
    # ------------------------------------------------------------------
    print(f"{_CYAN}[3/6] Filtrando ALUCINACAO...{_RESET}")
    t0 = time.time()

    from scripts.motor.classify import filtrar_alucinacao

    dfs_filtrado = filtrar_alucinacao(dfs_class)
    elapsed_filter = time.time() - t0

    # Contar removidos
    total_antes = sum(len(df) for df in dfs_class.values())
    total_depois = sum(len(df) for df in dfs_filtrado.values())
    removidos = total_antes - total_depois

    if removidos > 0:
        print(f"      {_YELLOW}REMOVIDOS{_RESET}: {removidos} registros ALUCINACAO ({elapsed_filter:.1f}s)\n")
    else:
        print(f"      {_GREEN}OK{_RESET} — 0 registros ALUCINACAO encontrados ({elapsed_filter:.1f}s)\n")

    # ------------------------------------------------------------------
    # 4. Unificar base
    # ------------------------------------------------------------------
    print(f"{_CYAN}[4/6] Unificando base de clientes...{_RESET}")
    t0 = time.time()

    from scripts.motor.classify import unificar_base

    base = unificar_base(dfs_filtrado)
    elapsed_unify = time.time() - t0

    print(f"      {_GREEN}OK{_RESET} — {len(base)} registros, {len(base.columns)} colunas ({elapsed_unify:.1f}s)\n")

    # ------------------------------------------------------------------
    # 5. Validar
    # ------------------------------------------------------------------
    print(f"{_CYAN}[5/6] Validando base...{_RESET}")
    t0 = time.time()

    from scripts.motor.classify import validar_base

    resultado_validacao = validar_base(base)
    elapsed_validate = time.time() - t0

    # Checar criticos
    criticos_ok = True
    criticos_msgs: list[str] = []

    if resultado_validacao["cnpj_como_float"] > 0:
        criticos_ok = False
        criticos_msgs.append(f"CNPJ como float: {resultado_validacao['cnpj_como_float']}")

    if resultado_validacao["cnpj_duplicados"] > 0:
        criticos_ok = False
        criticos_msgs.append(f"CNPJ duplicados: {resultado_validacao['cnpj_duplicados']}")

    if resultado_validacao["alucinacao_presente"] > 0:
        criticos_ok = False
        criticos_msgs.append(f"ALUCINACAO presente: {resultado_validacao['alucinacao_presente']}")

    validacao_status = "PASSED" if criticos_ok else "FAILED"

    if criticos_ok:
        print(f"      {_GREEN}VALIDACAO PASSED{_RESET} ({elapsed_validate:.1f}s)\n")
    else:
        print(f"      {_RED}VALIDACAO FAILED{_RESET} ({elapsed_validate:.1f}s)")
        for msg in criticos_msgs:
            print(f"        {_RED}ALERTA: {msg}{_RESET}")
        print()

    # ------------------------------------------------------------------
    # 6. Exportar JSON
    # ------------------------------------------------------------------
    output_path = Path("data/output/motor/base_unificada.json")
    file_size_mb = 0.0

    if dry_run:
        print(f"{_CYAN}[6/6] Exportando JSON...{_RESET}")
        print(f"      {_YELLOW}DRY RUN{_RESET} — JSON nao exportado\n")
    else:
        print(f"{_CYAN}[6/6] Exportando JSON...{_RESET}")
        t0 = time.time()

        # Criar diretorio
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Preparar registros (converter DataFrame para lista de dicts)
        registros = []
        for _, row in base.iterrows():
            registro: dict[str, Any] = {}
            for col in base.columns:
                val = row[col]
                # Tratar NaN/NaT/None
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    registro[col] = None
                elif isinstance(val, pd.Timestamp):
                    registro[col] = val.isoformat() if not pd.isna(val) else None
                elif isinstance(val, (np.integer,)):
                    registro[col] = int(val)
                elif isinstance(val, (np.floating,)):
                    registro[col] = float(val) if not np.isnan(val) else None
                elif isinstance(val, (np.bool_,)):
                    registro[col] = bool(val)
                else:
                    registro[col] = val
            registros.append(registro)

        # Construir payload JSON
        payload = {
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "versao": "2.0.0",
                "total_registros": len(base),
                "fonte": "CRM_VITAO360 INTELIGENTE FINAL OK.xlsx",
                "pipeline_versao": "11-02",
                "validacao_status": validacao_status,
                "tempo_execucao_s": round(time.time() - t_total, 1),
            },
            "registros": registros,
            "resumo": {
                "distribuicao_vendedores": resultado_validacao.get("distribuicao_vendedores", {}),
                "distribuicao_situacao": resultado_validacao.get("distribuicao_situacao", {}),
                "distribuicao_classificacao": resultado_validacao.get("distribuicao_classificacao", {}),
                "cnpjs_nulos": resultado_validacao.get("cnpj_nulos", 0),
                "vendedor_desconhecido": resultado_validacao.get("vendedor_desconhecido", {}),
                "classificacao_geral": dist_geral,
                "alucinacao_removidos": removidos,
            },
        }

        # Salvar
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=_json_serializer)

        elapsed_export = time.time() - t0
        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        print(f"      {_GREEN}OK{_RESET} — {output_path} ({file_size_mb:.1f} MB, {elapsed_export:.1f}s)\n")

    # ------------------------------------------------------------------
    # Resumo final
    # ------------------------------------------------------------------
    elapsed_total = time.time() - t_total

    # Distribuicao vendedores formatada
    dist_vendedores = resultado_validacao.get("distribuicao_vendedores", {})
    total_vendedores = sum(dist_vendedores.values()) if dist_vendedores else 0

    print(f"{_BOLD}{'=' * 52}{_RESET}")
    print(f"{_BOLD} CRM VITAO360 v2.0 -- IMPORT PIPELINE COMPLETO{_RESET}")
    print(f"{_BOLD}{'=' * 52}{_RESET}")
    print(f"  Planilha: CRM_VITAO360 INTELIGENTE FINAL OK.xlsx")
    print(f"  Abas lidas: {abas_lidas}/{total_abas}")
    print(f"  Tempo total: {elapsed_total:.1f}s")
    print()
    print(f"  {_BOLD}BASE UNIFICADA:{_RESET}")
    print(f"    Total registros: {len(base)}")
    cnpjs_unicos = base["cnpj_normalizado"].dropna().nunique() if "cnpj_normalizado" in base.columns else 0
    cnpjs_nulos = resultado_validacao.get("cnpj_nulos", 0)
    print(f"    CNPJs unicos: {cnpjs_unicos}")
    print(f"    CNPJs nulos: {cnpjs_nulos}")
    print()
    print(f"  {_BOLD}VENDEDORES:{_RESET}")
    for vendedor in ["DAIANE", "LARISSA", "MANU", "JULIO", "LEGADO", "DESCONHECIDO"]:
        count = dist_vendedores.get(vendedor, 0)
        pct = (count / total_vendedores * 100) if total_vendedores > 0 else 0
        print(f"    {vendedor}: {count} ({pct:.1f}%)")
    print()
    print(f"  {_BOLD}CLASSIFICACAO:{_RESET}")
    dist_class = resultado_validacao.get("distribuicao_classificacao", {})
    for tier in ["REAL", "SINTETICO", "ALUCINACAO"]:
        count = dist_class.get(tier, 0)
        print(f"    {tier}: {count}")
    print(f"    ALUCINACAO excluidos: {removidos}")
    print()
    if criticos_ok:
        print(f"  {_GREEN}{_BOLD}VALIDACAO: PASSED{_RESET}")
    else:
        print(f"  {_RED}{_BOLD}VALIDACAO: FAILED{_RESET}")
        for msg in criticos_msgs:
            print(f"    {_RED}{msg}{_RESET}")

    if not dry_run:
        print(f"  Output: {output_path} ({file_size_mb:.1f} MB)")

    print(f"{_BOLD}{'=' * 52}{_RESET}\n")

    return {
        "base": base,
        "validacao": resultado_validacao,
        "validacao_status": validacao_status,
        "output_path": str(output_path),
        "elapsed": elapsed_total,
        "dist_geral": dist_geral,
        "removidos": removidos,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CRM VITAO360 v2.0 — Import Pipeline Completo",
    )
    parser.add_argument(
        "--caminho",
        type=str,
        default=None,
        help="Path da planilha FINAL (default: config.CAMINHO_PLANILHA)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Roda pipeline sem exportar JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Logging detalhado (DEBUG)",
    )

    args = parser.parse_args()

    caminho = Path(args.caminho) if args.caminho else None

    result = run_pipeline(
        caminho=caminho,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Exit code baseado na validacao
    if result["validacao_status"] != "PASSED":
        sys.exit(1)
