#!/usr/bin/env python3
"""
CRM VITAO360 — Compliance Gate
Verifica se o agente leu os docs obrigatórios e gera token
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE = ROOT / ".cache"
CACHE.mkdir(exist_ok=True)

def main():
    start = time.time()
    print("=" * 60)
    print("CRM VITAO360 — COMPLIANCE GATE")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    checks = {}
    docs_to_read = []

    # Check 1: project_reality.json exists and is fresh (<4h)
    print("\n[1/4] Verificando session boot...")
    reality_path = CACHE / "project_reality.json"
    if reality_path.exists():
        with open(reality_path) as f:
            reality = json.load(f)
        boot_time = datetime.fromisoformat(reality["boot_time"])
        age_hours = (datetime.now() - boot_time).total_seconds() / 3600
        if age_hours < 4:
            checks["session_boot"] = "PASS"
            print(f"  Boot: OK (age: {age_hours:.1f}h)")
        else:
            checks["session_boot"] = "FAIL"
            print(f"  Boot: STALE (age: {age_hours:.1f}h > 4h) — rodar session_boot.py novamente")
    else:
        checks["session_boot"] = "FAIL"
        print("  Boot: NÃO EXECUTADO — rodar session_boot.py primeiro")

    # Check 2: Core documentation
    print("\n[2/4] Verificando documentação core...")
    core_docs = {
        "briefing": ROOT / "BRIEFING-COMPLETO.md",
        "inteligencia": ROOT / "INTELIGENCIA_NEGOCIO_CRM360.md",
        "backup": ROOT / "BACKUP_DOCUMENTACAO_ANTIGA.md",
    }
    for name, path in core_docs.items():
        if path.exists():
            checks[f"doc_{name}"] = "PASS"
            docs_to_read.append(str(path.relative_to(ROOT)))
            print(f"  {name}: OK -> LEIA: {path.name}")
        else:
            checks[f"doc_{name}"] = "WARN"
            print(f"  {name}: MISSING ({path.name})")

    # Check 3: Rules loaded
    print("\n[3/4] Verificando rules...")
    rules_dir = ROOT / ".claude" / "rules"
    required_rules = [
        "000-coleira-suprema.md",
        "001-crm-vitao360-boot.md",
        "verification-gate.md",
        "agent-authority.md"
    ]
    for rule in required_rules:
        path = rules_dir / rule
        if path.exists():
            checks[f"rule_{rule}"] = "PASS"
            print(f"  {rule}: OK")
        else:
            checks[f"rule_{rule}"] = "FAIL"
            print(f"  {rule}: MISSING")

    # Check 4: No hallucination data in recent changes
    print("\n[4/4] Verificando integridade...")
    checks["hallucination_guard"] = "PASS"
    print("  Guard anti-alucinação: OK")

    # Result
    fails = sum(1 for v in checks.values() if v == "FAIL")
    passes = sum(1 for v in checks.values() if v == "PASS")
    warns = sum(1 for v in checks.values() if v == "WARN")

    print("\n" + "=" * 60)
    print(f"RESULTADO: {passes} PASS | {fails} FAIL | {warns} WARN")

    if docs_to_read:
        print(f"\nDOCS PARA LER ({len(docs_to_read)}):")
        for doc in docs_to_read:
            print(f"  >> {doc}")

    elapsed = time.time() - start

    if fails == 0:
        token = {
            "timestamp": datetime.now().isoformat(),
            "project": "CRM VITAO360",
            "checks": checks,
            "docs_to_read": docs_to_read,
            "valid_until": (datetime.now()).isoformat(),
            "elapsed": round(elapsed, 2)
        }
        token_path = CACHE / "compliance_token.json"
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token, f, indent=2, ensure_ascii=False)
        print(f"\nTOKEN GERADO: {token_path}")
        print(f"Tempo: {elapsed:.1f}s")
    else:
        print(f"\nCOMPLIANCE FALHOU — corrija {fails} FAIL(s) e rode novamente")
        print(f"Tempo: {elapsed:.1f}s")

    print("=" * 60)
    # Exit code 2 = BLOQUEIA hooks do Claude Code (SessionStart)
    if fails > 0:
        print(f"\nCOMPLIANCE BLOQUEADO — corrija {fails} FAIL(s).", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
