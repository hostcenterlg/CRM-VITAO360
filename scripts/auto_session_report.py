#!/usr/bin/env python3
"""
AUTO SESSION REPORT — CRM VITAO360 SaaS
Gera SESSAO_RETOMAR.md automaticamente com:
- Git state, verify results, pendências, próximos passos
- Salva na raiz do projeto para contexto de retomada

Uso: python scripts/auto_session_report.py
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / ".cache"

def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(BASE), timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""

print("=" * 60)
print("CRM VITAO360 — AUTO SESSION REPORT")
print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Git state
branch = run(["git", "branch", "--show-current"])
last_commits = run(["git", "log", "--oneline", "-10"])
uncommitted = run(["git", "status", "--short"])
stash_count = run(["git", "stash", "list"])

# Planning state
state_path = BASE / ".planning" / "STATE.md"
state_content = ""
if state_path.exists():
    state_content = state_path.read_text(encoding="utf-8")
    # Extract current position
    for line in state_content.split("\n"):
        if line.startswith("Phase:") or line.startswith("Status:") or line.startswith("Last activity:"):
            print(f"  {line.strip()}")

# Verify results
verify_summary = ""
compliance_path = CACHE / "compliance_token.json"
if compliance_path.exists():
    token = json.loads(compliance_path.read_text(encoding="utf-8"))
    ts = datetime.fromisoformat(token.get("timestamp", "2000-01-01"))
    age = (datetime.now() - ts).total_seconds() / 3600
    verify_summary += f"Compliance token: {'OK' if age < 4 else 'EXPIRADO'} ({age:.1f}h)\n"

# Tech debt
debt_path = CACHE / "tech_debt_report.json"
debt_summary = ""
if debt_path.exists():
    debt = json.loads(debt_path.read_text(encoding="utf-8"))
    debt_summary = f"Tech debt: {debt.get('total_findings', '?')} items ({debt.get('severity', '?')})"

# Generate report
report = f"""# SESSÃO PARA RETOMAR — CRM VITAO360 SaaS

**Gerado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Branch:** {branch}

## Estado do Projeto

```
{state_content[:500] if state_content else 'STATE.md não encontrado'}
```

## Git

### Últimos Commits
```
{last_commits}
```

### Arquivos Não Commitados
```
{uncommitted if uncommitted else '(nada)'}
```

### Stash
```
{stash_count if stash_count else '(vazio)'}
```

## Verificações

{verify_summary}
{debt_summary}

## Próximos Passos

1. Rodar boot: `python scripts/session_boot.py`
2. Rodar compliance: `python scripts/compliance_gate.py`
3. Verificar estado: `/gsd:progress`
4. Continuar de onde parou (ver STATE.md acima)

## Contexto Importante

- **Projeto**: CRM VITAO360 → SaaS com Supabase
- **Motor**: 92 combinações (SITUAÇÃO × RESULTADO) → 9 dimensões
- **Score**: 6 fatores ponderados (0-100) → Pirâmide P1-P7
- **Faturamento baseline**: R$ 2.091.000 (2025)
- **Churn**: 80% — maior risco estrutural
- **Deskrio API**: Conectada (15.468 contatos)
- **Skills**: 7 (crm-vitao360, dev-motor, data-pipeline, qa-validacao, ux-visual, projecao-metas, aios-god-mode)
- **Detector de Mentira**: 3 níveis ativos + 8 checks verify.py
- **Pre-commit hook**: 5 checks instalado

---
*Auto-gerado por scripts/auto_session_report.py*
"""

report_path = BASE / "SESSAO_RETOMAR.md"
report_path.write_text(report, encoding="utf-8")
print(f"\nRelatório salvo em: {report_path}")
print("Pronto para retomada de sessão.")
