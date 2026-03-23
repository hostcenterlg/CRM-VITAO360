#!/usr/bin/env python3
"""
CRM VITAO360 — Verification Script
Verifica claims antes de declarar "done"
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE = ROOT / ".cache"

# Scripts de enforcement que contêm patterns de detecção — excluir da varredura
SELF_EXCLUDE = {
    "verify.py",
    "session_boot.py",
    "compliance_gate.py",
}

def _should_skip(filepath):
    """Retorna True se o arquivo é um script de enforcement (contém patterns de detecção)"""
    return Path(filepath).name in SELF_EXCLUDE

def check_two_base(files=None):
    """Verifica que Two-Base Architecture está respeitada nos scripts"""
    issues = []
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return "SKIP", ["scripts/ não existe"]

    target_files = files or list(scripts_dir.rglob("*.py"))
    for f in target_files:
        if isinstance(f, str):
            f = Path(f)
        if not f.exists() or _should_skip(f):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            # Check for common Two-Base violations
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Flag if mixing LOG and monetary values without separation
                if "LOG" in line.upper() and ("R$" in line or "valor" in line.lower()):
                    if "0.00" not in line and "zero" not in line.lower():
                        issues.append(f"{f.name}:{i} — possível mistura LOG + valor monetário")
        except Exception:
            pass

    if issues:
        return "WARN", issues
    return "PASS", []

def check_cnpj_handling(files=None):
    """Verifica que CNPJ é tratado como string"""
    issues = []
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return "SKIP", ["scripts/ não existe"]

    target_files = files or list(scripts_dir.rglob("*.py"))
    for f in target_files:
        if isinstance(f, str):
            f = Path(f)
        if not f.exists() or _should_skip(f):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                low = line.lower()
                if "cnpj" in low:
                    if "int(cnpj" in low or "float(cnpj" in low:
                        issues.append(f"{f.name}:{i} — CNPJ convertido para int/float (PROIBIDO)")
        except Exception:
            pass

    if issues:
        return "FAIL", issues
    return "PASS", []

def check_formula_language(files=None):
    """Verifica que fórmulas openpyxl estão em inglês"""
    issues = []
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return "SKIP", ["scripts/ não existe"]

    target_files = files or list(scripts_dir.rglob("*.py"))
    pt_formulas = ["=SE(", "=PROCV(", "=SOMASE(", "=CONT.SE(", "=MÉDIA(", "=SOMA("]

    for f in target_files:
        if isinstance(f, str):
            f = Path(f)
        if not f.exists() or _should_skip(f):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                for formula in pt_formulas:
                    if formula in line.upper():
                        issues.append(f"{f.name}:{i} — fórmula em português: {formula}")
        except Exception:
            pass

    if issues:
        return "FAIL", issues
    return "PASS", []

def check_compliance_token():
    """Verifica token de compliance válido"""
    token_path = CACHE / "compliance_token.json"
    if not token_path.exists():
        return "FAIL", ["Token não existe — rodar compliance_gate.py"]

    with open(token_path) as f:
        token = json.load(f)

    ts = datetime.fromisoformat(token["timestamp"])
    age = (datetime.now() - ts).total_seconds() / 3600
    if age > 4:
        return "FAIL", [f"Token expirado (age: {age:.1f}h > 4h)"]

    return "PASS", []

def main():
    parser = argparse.ArgumentParser(description="CRM VITAO360 — Verification")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--claim", type=str, help="Verify specific claim")
    args = parser.parse_args()

    start = time.time()
    print("=" * 60)
    print("CRM VITAO360 — VERIFY")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    if args.all or args.claim == "compliance":
        print("\n[1] Compliance token...")
        status, issues = check_compliance_token()
        results["compliance_token"] = {"status": status, "issues": issues}
        print(f"  {status}: {issues[0] if issues else 'OK'}")

    if args.all or args.claim == "two_base":
        print("\n[2] Two-Base Architecture...")
        status, issues = check_two_base()
        results["two_base"] = {"status": status, "issues": issues}
        print(f"  {status}: {len(issues)} issues" if issues else f"  {status}")
        for iss in issues[:5]:
            print(f"    -> {iss}")

    if args.all or args.claim == "cnpj":
        print("\n[3] CNPJ handling...")
        status, issues = check_cnpj_handling()
        results["cnpj"] = {"status": status, "issues": issues}
        print(f"  {status}: {len(issues)} issues" if issues else f"  {status}")
        for iss in issues[:5]:
            print(f"    -> {iss}")

    if args.all or args.claim == "formulas":
        print("\n[4] Formula language...")
        status, issues = check_formula_language()
        results["formulas"] = {"status": status, "issues": issues}
        print(f"  {status}: {len(issues)} issues" if issues else f"  {status}")
        for iss in issues[:5]:
            print(f"    -> {iss}")

    if args.all or args.claim == "alucinacao":
        print("\n[5] ALUCINAÇÃO guard...")
        aluc_issues = []
        scripts_dir = ROOT / "scripts"
        for f in scripts_dir.rglob("*.py"):
            if _should_skip(f):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore").lower()
                if "alucinacao" in content and ("integr" in content or "merge" in content or "insert" in content):
                    if "exclu" not in content and "filter" not in content and "skip" not in content:
                        aluc_issues.append(f"{f.name} — possível integração de dados ALUCINAÇÃO")
            except Exception:
                pass
        status = "WARN" if aluc_issues else "PASS"
        results["alucinacao"] = {"status": status, "issues": aluc_issues}
        print(f"  {status}: {len(aluc_issues)} issues" if aluc_issues else f"  {status}")
        for iss in aluc_issues[:3]:
            print(f"    -> {iss}")

    if args.all or args.claim == "faturamento":
        print("\n[6] Faturamento baseline...")
        fat_issues = []
        # Verificar se R$ 2.091.000 é usado (não o antigo R$ 2.156.179)
        for f in (ROOT / ".claude").rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "2.156.179" in content and "SUPERSEDED" not in content and "ANTERIOR" not in content and "CORRIGIDO" not in content:
                    fat_issues.append(f"{f.name} — ainda usa baseline ANTIGO R$ 2.156.179")
            except Exception:
                pass
        status = "FAIL" if fat_issues else "PASS"
        results["faturamento"] = {"status": status, "issues": fat_issues}
        print(f"  {status}: {len(fat_issues)} issues" if fat_issues else f"  {status}")
        for iss in fat_issues[:3]:
            print(f"    -> {iss}")

    if args.all or args.claim == "skills":
        print("\n[7] Skills completas...")
        skills_dir = ROOT / ".claude" / "skills"
        required = ["crm-vitao360", "dev-motor", "data-pipeline", "qa-validacao", "ux-visual", "projecao-metas"]
        skill_issues = []
        for s in required:
            if not (skills_dir / s / "SKILL.md").exists():
                skill_issues.append(f"Skill {s} NÃO EXISTE")
            elif os.path.getsize(skills_dir / s / "SKILL.md") < 500:
                skill_issues.append(f"Skill {s} muito pequena ({os.path.getsize(skills_dir / s / 'SKILL.md')} bytes)")
        status = "FAIL" if skill_issues else "PASS"
        results["skills"] = {"status": status, "issues": skill_issues}
        print(f"  {status}: {len(skill_issues)} issues" if skill_issues else f"  {status}")
        for iss in skill_issues[:5]:
            print(f"    -> {iss}")

    if args.all or args.claim == "motor":
        print("\n[8] Motor coverage...")
        motor_issues = []
        motor_dir = ROOT / "scripts" / "motor"
        if motor_dir.exists():
            # Check if motor_regras exists and has 92 combinations
            mr = motor_dir / "motor_regras.py"
            if mr.exists():
                content = mr.read_text(encoding="utf-8", errors="ignore")
                situacoes = ["ATIVO", "EM RISCO", "INAT.REC", "INAT.ANT", "PROSPECT", "LEAD", "NOVO"]
                for s in situacoes:
                    if s not in content:
                        motor_issues.append(f"SITUAÇÃO '{s}' não encontrada em motor_regras.py")
            else:
                motor_issues.append("motor_regras.py não existe (Phase 12 pendente)")
        else:
            motor_issues.append("scripts/motor/ não existe (Phase 11 pendente)")
        status = "WARN" if motor_issues else "PASS"
        results["motor"] = {"status": status, "issues": motor_issues}
        print(f"  {status}: {len(motor_issues)} issues" if motor_issues else f"  {status}")
        for iss in motor_issues[:3]:
            print(f"    -> {iss}")

    # Summary
    fails = sum(1 for r in results.values() if r["status"] == "FAIL")
    passes = sum(1 for r in results.values() if r["status"] == "PASS")
    warns = sum(1 for r in results.values() if r["status"] == "WARN")
    skips = sum(1 for r in results.values() if r["status"] == "SKIP")

    elapsed = time.time() - start

    print("\n" + "=" * 60)
    print(f"RESULTADO: {passes} PASS | {fails} FAIL | {warns} WARN | {skips} SKIP")
    print(f"Tempo: {elapsed:.1f}s")
    print("=" * 60)

    if fails > 0:
        print("\nVERIFICAÇÃO FALHOU — NÃO é 'done'")
    else:
        print("\nTODAS verificações passaram")

    return 1 if fails > 0 else 0

if __name__ == "__main__":
    sys.exit(main())
