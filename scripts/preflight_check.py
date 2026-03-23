#!/usr/bin/env python3
"""
PREFLIGHT CHECK — CRM VITAO360
Roda ANTES de mexer no motor/dados/pipeline.
Se CRITICAL = NÃO PROSSEGUIR.

Baseado no preflight_check.py do us-county-radar.
7 seções de verificação.
"""
import os
import sys
import json
import importlib
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / ".cache"

results = {"PASS": 0, "WARN": 0, "CRITICAL": 0}

def check(section, name, condition, severity="PASS", detail=""):
    status = "PASS" if condition else severity
    results[status] = results.get(status, 0) + 1
    icon = {"PASS": "✓", "WARN": "⚠", "CRITICAL": "✗"}[status]
    print(f"  {icon} {name}: {status}" + (f" — {detail}" if detail and not condition else ""))
    return condition

print("=" * 60)
print("CRM VITAO360 — PREFLIGHT CHECK")
print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# ============================================================
# SEÇÃO 1: AMBIENTE
# ============================================================
print("\n[1/7] Ambiente...")

check("env", "Python 3.12+",
      sys.version_info >= (3, 12),
      "CRITICAL", f"Python {sys.version_info.major}.{sys.version_info.minor}")

for mod in ["openpyxl", "pandas", "rapidfuzz"]:
    try:
        importlib.import_module(mod)
        check("env", f"Módulo {mod}", True)
    except ImportError:
        check("env", f"Módulo {mod}", False, "CRITICAL", "pip install necessário")

check("env", ".env existe",
      (BASE / ".env").exists(),
      "WARN", "Token Deskrio não configurado")

# ============================================================
# SEÇÃO 2: COMPLIANCE TOKEN
# ============================================================
print("\n[2/7] Compliance Token...")

token_path = CACHE / "compliance_token.json"
if token_path.exists():
    token = json.loads(token_path.read_text(encoding="utf-8"))
    ts = datetime.fromisoformat(token.get("timestamp", "2000-01-01"))
    age_hours = (datetime.now() - ts).total_seconds() / 3600
    check("token", "Token existe", True)
    check("token", "Token fresco (<4h)",
          age_hours < 4,
          "CRITICAL", f"Idade: {age_hours:.1f}h — rodar compliance_gate.py")
else:
    check("token", "Token existe", False, "CRITICAL", "Rodar: python scripts/compliance_gate.py")

# ============================================================
# SEÇÃO 3: PROJETO REALITY
# ============================================================
print("\n[3/7] Project Reality...")

reality_path = CACHE / "project_reality.json"
if reality_path.exists():
    reality = json.loads(reality_path.read_text(encoding="utf-8"))
    check("reality", "project_reality.json existe", True)
    errors = reality.get("errors", [])
    check("reality", "0 erros no boot",
          len(errors) == 0,
          "CRITICAL", f"{len(errors)} erros: {errors}")
else:
    check("reality", "project_reality.json existe", False, "CRITICAL", "Rodar: python scripts/session_boot.py")

# ============================================================
# SEÇÃO 4: FONTES DE DADOS
# ============================================================
print("\n[4/7] Fontes de Dados...")

PLANILHA_FINAL = r"C:\Users\User\OneDrive\Área de Trabalho\CRM_VITAO360  INTELIGENTE   FINAL OK .xlsx"
check("dados", "Planilha FINAL acessível",
      os.path.exists(PLANILHA_FINAL),
      "CRITICAL", f"Não encontrada: {PLANILHA_FINAL}")

if os.path.exists(PLANILHA_FINAL):
    size_mb = os.path.getsize(PLANILHA_FINAL) / 1024 / 1024
    check("dados", f"Planilha FINAL > 1MB ({size_mb:.1f}MB)",
          size_mb > 1,
          "WARN", "Arquivo muito pequeno — pode estar corrompido")

# Radiografias
for rj in ["radiografia_completa.json", "radiografia_carteira.json"]:
    rpath = CACHE / rj
    if rpath.exists():
        check("dados", f"{rj} existe ({os.path.getsize(rpath)} bytes)",
              os.path.getsize(rpath) > 100, "WARN", "Arquivo vazio")
    else:
        check("dados", f"{rj} existe", False, "WARN", "Rodar radiografia novamente")

# ============================================================
# SEÇÃO 5: REGRAS E SKILLS
# ============================================================
print("\n[5/7] Regras e Skills...")

rules_dir = BASE / ".claude" / "rules"
required_rules = [
    "000-coleira-suprema.md",
    "detector-de-mentira.md",
    "verification-gate.md",
    "agent-authority.md",
]
for rule in required_rules:
    check("rules", f"Regra {rule}",
          (rules_dir / rule).exists(),
          "CRITICAL", "Regra obrigatória ausente")

skills_dir = BASE / ".claude" / "skills"
required_skills = ["crm-vitao360", "dev-motor", "data-pipeline", "qa-validacao"]
for skill in required_skills:
    check("skills", f"Skill {skill}",
          (skills_dir / skill / "SKILL.md").exists(),
          "WARN", "Skill de agente ausente")

# ============================================================
# SEÇÃO 6: PLANNING
# ============================================================
print("\n[6/7] Planning...")

planning = BASE / ".planning"
for pfile in ["PROJECT.md", "ROADMAP.md", "REQUIREMENTS.md", "STATE.md", "DECISIONS.md"]:
    check("planning", f"{pfile} existe",
          (planning / pfile).exists(),
          "WARN", "Artefato de planejamento ausente")

# ============================================================
# SEÇÃO 7: TWO-BASE E CNPJ SCAN
# ============================================================
print("\n[7/7] Two-Base & CNPJ Quick Scan...")

# Scan scripts/motor/ for Two-Base violations
motor_dir = BASE / "scripts" / "motor"
if motor_dir.exists():
    violations = 0
    for pyfile in motor_dir.glob("**/*.py"):
        content = pyfile.read_text(encoding="utf-8", errors="ignore")
        # Check for mixing valor and LOG
        if "LOG" in content and ("valor" in content.lower() or "r$" in content.lower()):
            if "R$ 0" not in content and "0.00" not in content and "Two-Base" not in content:
                violations += 1
                print(f"    ⚠ {pyfile.name}: possível mistura LOG + valor")
    check("twobase", "Scan Two-Base em scripts/motor/",
          violations == 0,
          "WARN", f"{violations} possíveis violações")
else:
    check("twobase", "scripts/motor/ existe", False, "WARN", "Diretório ainda não criado (Phase 11)")

# ============================================================
# RESULTADO
# ============================================================
print(f"\n{'=' * 60}")
print(f"RESULTADO: {results['PASS']} PASS | {results['WARN']} WARN | {results['CRITICAL']} CRITICAL")
print(f"{'=' * 60}")

if results["CRITICAL"] > 0:
    print(f"\n✗ {results['CRITICAL']} CHECKS CRÍTICOS FALHARAM — NÃO PROSSEGUIR")
    sys.exit(1)
elif results["WARN"] > 0:
    print(f"\n⚠ {results['WARN']} avisos — prosseguir com cautela")
    sys.exit(0)
else:
    print(f"\n✓ Tudo OK — pode prosseguir")
    sys.exit(0)
