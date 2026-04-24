#!/usr/bin/env python3
"""
CRM VITAO360 — deskrio_health_check.py
=======================================
Valida integridade dos snapshots Deskrio em data/deskrio/{YYYY-MM-DD}/.

Checa:
  1. Diretorio existe
  2. Arquivos esperados presentes (connections, contacts, tickets, kanban_boards)
  3. Nenhum arquivo com corpo de erro 403 ("Invalid token")
  4. Tamanhos minimos (contacts >1MB, tickets >1KB, etc.)
  5. Schema basico (JSON valido, tipo esperado)

USO:
  python scripts/deskrio_health_check.py                # hoje
  python scripts/deskrio_health_check.py --date 2026-04-24
  python scripts/deskrio_health_check.py --last-7       # ultimos 7 dias
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESKRIO_ROOT = ROOT / "data" / "deskrio"

# Expected files and minimum byte sizes
EXPECTED_FILES: dict[str, int] = {
    "connections.json": 500,
    "contacts.json": 1_000_000,  # 1MB+ (15k contacts)
    "extrainfo_fields.json": 100,
    "kanban_boards.json": 500,
    "tickets.json": 100,
}

# Optional files (warn only if missing)
OPTIONAL_FILES: dict[str, int] = {
    "kanban_cards_20.json": 500,
    "kanban_cards_100.json": 500,
}


def check_day(day: date) -> tuple[bool, list[str]]:
    issues: list[str] = []
    day_dir = DESKRIO_ROOT / day.isoformat()

    if not day_dir.exists():
        return False, [f"diretorio ausente: {day_dir.name}"]

    # Required files
    for fname, min_size in EXPECTED_FILES.items():
        fpath = day_dir / fname
        if not fpath.exists():
            issues.append(f"MISSING {fname}")
            continue
        size = fpath.stat().st_size
        if size < min_size:
            issues.append(f"TOO_SMALL {fname} ({size} < {min_size})")
            continue
        # Check content: must not be a 403 error payload
        try:
            head = fpath.read_text(encoding="utf-8", errors="ignore")[:500]
            if "Invalid token" in head or '"statusCode":403' in head:
                issues.append(f"ERROR_BODY {fname} (403 persisted as data)")
                continue
            # Parse as JSON
            data = json.loads(head + fpath.read_text(encoding="utf-8")[500:])
            # Basic type sanity
            if fname == "contacts.json" and not isinstance(data, list):
                issues.append(f"SCHEMA {fname} (expected list)")
            elif fname == "tickets.json" and not isinstance(data, list):
                issues.append(f"SCHEMA {fname} (expected list)")
            elif fname == "connections.json":
                # API retorna {"whatsappConnections": [...]} OU list direta
                if not (isinstance(data, dict) and "whatsappConnections" in data) and not isinstance(data, list):
                    issues.append(f"SCHEMA {fname} (expected dict.whatsappConnections or list)")
            elif fname == "kanban_boards.json" and not isinstance(data, dict):
                issues.append(f"SCHEMA {fname} (expected dict)")
        except json.JSONDecodeError as e:
            issues.append(f"INVALID_JSON {fname} ({e})")
        except Exception as e:
            issues.append(f"READ_ERROR {fname} ({e})")

    # Optional files: warn if present but corrupt
    for fname, min_size in OPTIONAL_FILES.items():
        fpath = day_dir / fname
        if fpath.exists():
            size = fpath.stat().st_size
            head = fpath.read_text(encoding="utf-8", errors="ignore")[:500]
            if "Invalid token" in head:
                issues.append(f"ERROR_BODY (optional) {fname} (403 persisted)")
            elif size < min_size:
                issues.append(f"TOO_SMALL (optional) {fname} ({size})")

    return (not issues), issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD", default=None)
    ap.add_argument("--last-7", action="store_true")
    args = ap.parse_args()

    if args.last_7:
        days = [date.today() - timedelta(days=i) for i in range(7)]
    elif args.date:
        try:
            days = [datetime.strptime(args.date, "%Y-%m-%d").date()]
        except ValueError:
            print(f"ERRO: data invalida {args.date}")
            return 1
    else:
        days = [date.today()]

    all_ok = True
    print("=" * 60)
    print(f"Deskrio health check | dias: {len(days)}")
    print("=" * 60)
    for d in days:
        ok, issues = check_day(d)
        status = "PASS" if ok else "FAIL"
        icon = "[OK]  " if ok else "[FAIL]"
        print(f"{icon} {d.isoformat()} — {status}")
        for iss in issues:
            print(f"        -> {iss}")
        if not ok:
            all_ok = False

    print("=" * 60)
    print("TODOS PASSARAM" if all_ok else "HA FALHAS")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
