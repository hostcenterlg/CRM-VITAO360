#!/usr/bin/env python3
"""
CRM VITAO360 — backfill_deskrio.py
====================================
Backfill: roda sync_deskrio_to_db.py para todos os snapshots em
data/deskrio/YYYY-MM-DD/ (idempotente — registros ja existentes sao puldados).

Uso:
  python scripts/backfill_deskrio.py                    # todos os dias
  python scripts/backfill_deskrio.py --since 2026-04-15 # apenas a partir desta data
  python scripts/backfill_deskrio.py --skip-contatos    # pula sync de contatos (mais rapido)

Saida:
  Sumario por dia + total geral.
  Exit code 0 = todos OK; 1 = alguma falha; 2 = sucesso parcial.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESKRIO_ROOT = ROOT / "data" / "deskrio"
SYNC_SCRIPT = ROOT / "scripts" / "sync_deskrio_to_db.py"


def listar_dias(since: date | None = None) -> list[Path]:
    """Lista pastas YYYY-MM-DD em data/deskrio/, ordenadas asc.

    Filtra por data >= since se fornecida.
    """
    if not DESKRIO_ROOT.exists():
        return []
    candidates = []
    for p in DESKRIO_ROOT.iterdir():
        if not p.is_dir():
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", p.name):
            continue
        if since is not None:
            try:
                day = datetime.strptime(p.name, "%Y-%m-%d").date()
                if day < since:
                    continue
            except ValueError:
                continue
        candidates.append(p)
    return sorted(candidates, key=lambda p: p.name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill Deskrio snapshots -> banco (idempotente)"
    )
    parser.add_argument(
        "--since",
        help="Apenas dias >= esta data (YYYY-MM-DD). Default: todos.",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Repassa --dry-run para sync_deskrio_to_db.py.",
    )
    parser.add_argument(
        "--skip-contatos",
        action="store_true",
        help="Repassa --skip-contatos para sync_deskrio_to_db.py (pula SyncContatos ~12min/dia).",
    )
    args = parser.parse_args()

    since: date | None = None
    if args.since:
        try:
            since = datetime.strptime(args.since, "%Y-%m-%d").date()
        except ValueError:
            print(f"ERRO: --since invalido: {args.since}", file=sys.stderr)
            return 1

    dias = listar_dias(since)
    if not dias:
        print(f"Nenhum dia encontrado em {DESKRIO_ROOT}" + (f" desde {since}" if since else ""))
        return 0

    print("=" * 60)
    print(f"BACKFILL DESKRIO — {len(dias)} dias")
    print(f"  Range: {dias[0].name} -> {dias[-1].name}")
    if args.dry_run:
        print("  Modo: DRY-RUN (nao grava no banco)")
    print("=" * 60)

    sucessos = 0
    parciais = 0
    falhas: list[tuple[str, int]] = []

    for idx, day_dir in enumerate(dias, 1):
        print(f"\n[{idx}/{len(dias)}] {day_dir.name}")
        cmd = [
            sys.executable,
            str(SYNC_SCRIPT),
            "--data-dir",
            str(day_dir.relative_to(ROOT)),
        ]
        if args.dry_run:
            cmd.append("--dry-run")
        if args.skip_contatos:
            cmd.append("--skip-contatos")

        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode == 0:
            sucessos += 1
        elif result.returncode == 2:
            parciais += 1
        else:
            falhas.append((day_dir.name, result.returncode))

    print("\n" + "=" * 60)
    print("BACKFILL CONCLUIDO")
    print(f"  Sucessos completos : {sucessos}/{len(dias)}")
    print(f"  Sucessos parciais  : {parciais}/{len(dias)}")
    print(f"  Falhas             : {len(falhas)}/{len(dias)}")
    if falhas:
        print("  Detalhe das falhas:")
        for name, rc in falhas:
            print(f"    - {name}: exit={rc}")
    print("=" * 60)

    if falhas:
        return 1
    if parciais:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
