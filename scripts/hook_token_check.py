#!/usr/bin/env python3
"""
HOOK: Token Check — roda antes de Bash/Edit/Write.
Se compliance_token.json não existe ou expirou → EXIT 2 (BLOQUEIA).
Leve: <100ms de execução.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOKEN = ROOT / ".cache" / "compliance_token.json"

# Se token não existe → BLOQUEAR
if not TOKEN.exists():
    print("BLOQUEADO: compliance_token.json não existe.", file=sys.stderr)
    print("Rode: python scripts/session_boot.py && python scripts/compliance_gate.py", file=sys.stderr)
    sys.exit(2)

# Se token expirou (>4h) → BLOQUEAR
try:
    data = json.loads(TOKEN.read_text(encoding="utf-8"))
    ts = datetime.fromisoformat(data["timestamp"])
    age_hours = (datetime.now() - ts).total_seconds() / 3600
    if age_hours > 4:
        print(f"BLOQUEADO: token expirado ({age_hours:.1f}h > 4h máximo).", file=sys.stderr)
        print("Rode: python scripts/session_boot.py && python scripts/compliance_gate.py", file=sys.stderr)
        sys.exit(2)
except Exception as e:
    print(f"BLOQUEADO: token corrompido ({e}).", file=sys.stderr)
    sys.exit(2)

# Token válido → PERMITIR
sys.exit(0)
