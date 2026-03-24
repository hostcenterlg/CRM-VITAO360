#!/bin/bash
# PRE-COMMIT HOOK — CRM VITAO360
# 5 checks bloqueiam commit ruim.
# Instalar: cp scripts/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

set -e

PYTHON="/c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe"
BASE="$(git rev-parse --show-toplevel)"

echo "═══════════════════════════════════════════"
echo " CRM VITAO360 — PRE-COMMIT HOOK"
echo "═══════════════════════════════════════════"

FAIL=0

# CHECK 1: Compliance token existe e fresco (<4h)
echo -n "[1/5] Compliance token... "
TOKEN_FILE="$BASE/.cache/compliance_token.json"
if [ -f "$TOKEN_FILE" ]; then
    AGE=$(( ($(date +%s) - $(date -r "$TOKEN_FILE" +%s)) / 3600 ))
    if [ "$AGE" -lt 4 ]; then
        echo "OK (${AGE}h)"
    else
        echo "FAIL — token expirado (${AGE}h). Rodar: python scripts/compliance_gate.py"
        FAIL=$((FAIL + 1))
    fi
else
    echo "FAIL — token não existe. Rodar: python scripts/session_boot.py + compliance_gate.py"
    FAIL=$((FAIL + 1))
fi

# CHECK 2: Secrets não commitados
echo -n "[2/5] Secrets scan... "
STAGED=$(git diff --cached --name-only)
SECRETS_FOUND=0
for f in $STAGED; do
    if echo "$f" | grep -qE '\.env$|\.env\.|credentials|secret|token.*\.json$'; then
        if [ "$f" != ".cache/compliance_token.json" ]; then
            echo ""
            echo "  ✗ SEGREDO DETECTADO: $f"
            SECRETS_FOUND=$((SECRETS_FOUND + 1))
        fi
    fi
done
if [ "$SECRETS_FOUND" -gt 0 ]; then
    echo "FAIL — $SECRETS_FOUND arquivo(s) com possíveis secrets"
    FAIL=$((FAIL + 1))
else
    echo "OK"
fi

# CHECK 3: .env não commitado
echo -n "[3/5] .env protegido... "
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo "FAIL — .env está no staging! Rodar: git reset HEAD .env"
    FAIL=$((FAIL + 1))
else
    echo "OK"
fi

# CHECK 4: ALUCINAÇÃO scan (558 registros proibidos)
echo -n "[4/5] ALUCINAÇÃO scan... "
ALUC_FOUND=0
for f in $STAGED; do
    if echo "$f" | grep -qE '\.(py|json)$'; then
        if [ -f "$f" ]; then
            if grep -qiE 'alucinacao.*integr|integr.*alucinacao' "$f" 2>/dev/null; then
                # Check if it's actually integrating (not just checking/excluding)
                if grep -qiE 'insert.*alucinacao|append.*alucinacao|merge.*alucinacao' "$f" 2>/dev/null; then
                    echo ""
                    echo "  ✗ ALUCINAÇÃO sendo INTEGRADA em: $f"
                    ALUC_FOUND=$((ALUC_FOUND + 1))
                fi
            fi
        fi
    fi
done
if [ "$ALUC_FOUND" -gt 0 ]; then
    echo "FAIL — dados ALUCINAÇÃO sendo integrados!"
    FAIL=$((FAIL + 1))
else
    echo "OK"
fi

# CHECK 5: Two-Base Architecture scan
echo -n "[5/5] Two-Base scan... "
TWOBASE_FAIL=0
# Enforcement scripts are excluded (they CONTAIN detection patterns)
ENFORCE_SKIP="verify.py|tech_debt_scan.py|preflight_check.py|postflight_check.py|session_boot.py|compliance_gate.py|auto_session_report.py"
for f in $STAGED; do
    if echo "$f" | grep -qE '\.py$'; then
        if echo "$f" | grep -qE "$ENFORCE_SKIP"; then
            continue
        fi
        if [ -f "$f" ]; then
            # Detect mixing: LOG/atendimento with monetary values (not R$ 0.00)
            if grep -qE '(LOG|log|atendimento).*valor.*[1-9]' "$f" 2>/dev/null; then
                echo ""
                echo "  ✗ Two-Base violada em: $f (LOG com valor > 0)"
                TWOBASE_FAIL=$((TWOBASE_FAIL + 1))
            fi
        fi
    fi
done
if [ "$TWOBASE_FAIL" -gt 0 ]; then
    echo "FAIL — Two-Base Architecture violada!"
    FAIL=$((FAIL + 1))
else
    echo "OK"
fi

# RESULTADO
echo ""
echo "═══════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
    echo " ✗ $FAIL CHECK(S) FALHARAM — COMMIT BLOQUEADO"
    echo "═══════════════════════════════════════════"
    exit 1
else
    echo " ✓ 5/5 CHECKS PASSARAM — COMMIT PERMITIDO"
    echo "═══════════════════════════════════════════"
    exit 0
fi
