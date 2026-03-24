#!/usr/bin/env python3
"""
HOOK: Verify on Stop — roda quando Claude tenta parar de responder.
Se verify.py falha → EXIT 2 (BLOQUEIA o "done").
Claude é FORÇADO a continuar trabalhando.

IMPORTANTE: Só bloqueia se houve modificação de arquivos na sessão.
Se foi só conversa/leitura, permite parar normalmente.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE = ROOT / ".cache"
TOKEN = CACHE / "compliance_token.json"

# Se não tem token, não há sessão ativa → permitir parar
if not TOKEN.exists():
    sys.exit(0)

# Verificar se houve mudanças (git diff)
try:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=5
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=5
    )
    changes = (result.stdout.strip() + "\n" + staged.stdout.strip()).strip()

    # Se não houve mudanças → permitir parar (foi só conversa)
    if not changes:
        sys.exit(0)
except Exception:
    # Se git falhar, permitir parar
    sys.exit(0)

# Houve mudanças → rodar verify.py
try:
    verify = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify.py"), "--all"],
        capture_output=True, text=True, cwd=str(ROOT), timeout=30
    )

    if verify.returncode != 0:
        print("BLOQUEADO: verify.py FALHOU — você NÃO pode dizer 'done'.", file=sys.stderr)
        print("", file=sys.stderr)
        # Mostrar output do verify para o Claude saber o que corrigir
        if verify.stdout:
            for line in verify.stdout.split("\n"):
                if "FAIL" in line or "WARN" in line or "RESULTADO" in line:
                    print(f"  {line.strip()}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Corrija os problemas acima e tente novamente.", file=sys.stderr)
        sys.exit(2)

except subprocess.TimeoutExpired:
    print("AVISO: verify.py timeout (>30s) — permitindo parar.", file=sys.stderr)
    sys.exit(0)
except Exception as e:
    print(f"AVISO: erro ao rodar verify.py ({e}) — permitindo parar.", file=sys.stderr)
    sys.exit(0)

# Verify passou → PERMITIR parar
sys.exit(0)
