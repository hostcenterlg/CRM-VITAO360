#!/usr/bin/env python3
"""
CRM VITAO360 — daily_pipeline.py
==================================
Pipeline diario: snapshot Deskrio -> ingest -> recalc score.

Etapas (na ordem, parando ao primeiro fatal):
  1. snapshot — extrai dados Deskrio para data/deskrio/{HOJE}/
  2. ingest   — sincroniza JSONs do snapshot com banco (Postgres/SQLite)
  3. recalc   — recalcula Score v2 + estagio_funil em todos os clientes

Pensado para ser chamado por scheduler externo (cron, Render Cron Job, GitHub
Actions, Vercel Cron). Nao tem self-scheduling — apenas orquestra.

Exit codes:
  0 = todas as etapas OK
  1 = falha fatal em alguma etapa (parcial 2 do snapshot/ingest tolerado)

Uso:
  python scripts/daily_pipeline.py
  python scripts/daily_pipeline.py --skip-snapshot   # se snapshot ja foi feito
  python scripts/daily_pipeline.py --skip-recalc     # apenas captura+ingest
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Etapas: (nome, comando, codes_aceitos)
# code 2 = sucesso parcial (alguma fase nao critica falhou) — toleramos.
ETAPAS: list[tuple[str, list[str], set[int]]] = [
    ("snapshot", [sys.executable, "scripts/deskrio_daily_snapshot.py"], {0, 2}),
    ("ingest",   [sys.executable, "scripts/sync_deskrio_to_db.py"],     {0, 2}),
    ("recalc",   [sys.executable, "scripts/recalc_score_batch.py"],     {0, 2}),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline diario CRM VITAO360")
    parser.add_argument("--skip-snapshot", action="store_true", help="Pula a etapa de snapshot")
    parser.add_argument("--skip-ingest", action="store_true", help="Pula a etapa de ingestao")
    parser.add_argument("--skip-recalc", action="store_true", help="Pula a etapa de recalc")
    args = parser.parse_args()

    pular = set()
    if args.skip_snapshot:
        pular.add("snapshot")
    if args.skip_ingest:
        pular.add("ingest")
    if args.skip_recalc:
        pular.add("recalc")

    inicio = datetime.now()
    print("=" * 60)
    print(f"CRM VITAO360 — daily_pipeline | inicio={inicio.isoformat()}")
    if pular:
        print(f"  Pulando: {', '.join(sorted(pular))}")
    print("=" * 60)

    falhas: list[tuple[str, int]] = []
    for nome, cmd, codes_ok in ETAPAS:
        if nome in pular:
            print(f"\n--- [{nome}] PULADO ---")
            continue
        print(f"\n--- [{nome}] {' '.join(cmd)} ---")
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode in codes_ok:
            status = "OK" if result.returncode == 0 else "PARCIAL"
            print(f"--- [{nome}] {status} (exit={result.returncode}) ---")
        else:
            falhas.append((nome, result.returncode))
            print(f"--- [{nome}] FALHA (exit={result.returncode}) — abortando pipeline ---")
            break

    fim = datetime.now()
    duracao = (fim - inicio).total_seconds()
    print("\n" + "=" * 60)
    if falhas:
        print(f"PIPELINE FALHOU em {duracao:.0f}s")
        for nome, rc in falhas:
            print(f"  {nome}: exit={rc}")
        print("=" * 60)
        return 1

    print(f"PIPELINE CONCLUIDO em {duracao:.0f}s")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
