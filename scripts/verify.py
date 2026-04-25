#!/usr/bin/env python3
"""
CRM VITAO360 — Verification Script
Verifica claims antes de declarar "done"
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
CACHE = ROOT / ".cache"

# Scripts de enforcement que contêm patterns de detecção — excluir da varredura
SELF_EXCLUDE = {
    "verify.py",
    "session_boot.py",
    "compliance_gate.py",
    "preflight_check.py",
    "tech_debt_scan.py",
    "postflight_check.py",
}

# Regex: linha começa (após whitespace) com chamada de logger
_LOGGER_LINE = re.compile(
    r'^\s*(log|logger|logging)\.(info|warning|error|debug|exception|critical)\s*\('
)
# Regex: linha é comentário puro ou docstring marker
_COMMENT_LINE = re.compile(r'^\s*(#|"""|\'\'\'|\*)')
# Regex: guarda ALUCINAÇÃO (compara ou conta)
_ALUC_GUARD = re.compile(
    r"(!=\s*['\"]ALUCINACAO['\"]|==\s*['\"]ALUCINACAO['\"]|count\s*\(.*alucinacao|zero\s+alucin|classifica(cao_)?(_?)3?tier)",
    re.IGNORECASE,
)


def _should_skip(filepath):
    """Retorna True se o arquivo é um script de enforcement (contém patterns de detecção)"""
    return Path(filepath).name in SELF_EXCLUDE

def _docstring_line_ranges(source: str) -> set[int]:
    """Retorna set de numeros de linha (1-indexed) que estao dentro de docstrings."""
    import ast
    lines_in_docstring: set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return lines_in_docstring

    def _walk(node):
        # Module, ClassDef, FunctionDef, AsyncFunctionDef podem ter docstring
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                ds = body[0]
                start = ds.lineno
                end = getattr(ds, "end_lineno", start)
                for ln in range(start, end + 1):
                    lines_in_docstring.add(ln)
        for child in ast.iter_child_nodes(node):
            _walk(child)

    _walk(tree)
    return lines_in_docstring


def check_two_base(files=None):
    """Verifica que Two-Base Architecture está respeitada nos scripts.

    FPs excluídos (refinado 2026-04-24):
      - Linhas dentro de docstrings (AST-parsed)
      - Linhas que começam com logger (log.info, logger.warning, logging.*)
      - Linhas que começam com # ou docstring markers
      - Linhas com `0.0`, `0.00`, `== 0`, `<= 0`, `>= 0`, `zero`
      - Linhas que mencionam "NUNCA", "respeitada", "proibido" (explicam a regra)
      - Scripts de enforcement (ja em SELF_EXCLUDE)
    """
    issues = []
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return "SKIP", ["scripts/ não existe"]

    # Keywords que indicam linha explicativa (FP), não violação
    EXPLAINER_TOKENS = (
        "nunca", "never", "respeitada", "respect", "proibido", "forbidden",
        "violac", "violation", "two-base", "r4 ",
    )

    target_files = files or list(scripts_dir.rglob("*.py"))
    for f in target_files:
        if isinstance(f, str):
            f = Path(f)
        if not f.exists() or _should_skip(f):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            docstring_lines = _docstring_line_ranges(content)
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                upper = line.upper()
                lower = line.lower()
                if "LOG" not in upper:
                    continue
                if "R$" not in line and "valor" not in lower:
                    continue
                # Inside a docstring?
                if i in docstring_lines:
                    continue
                # Already zero?
                if "0.00" in line or "0.0" in line or re.search(r"[<>=!]=\s*0\b", line) or "zero" in lower:
                    continue
                # Logger call?
                if _LOGGER_LINE.match(line):
                    continue
                # Comment / docstring marker?
                if _COMMENT_LINE.match(line):
                    continue
                # Explainer text?
                if any(tok in lower for tok in EXPLAINER_TOKENS):
                    continue
                # Print that confirms the rule?
                if "print(" in line and any(tok in lower for tok in ("respeitada", "nunca", "proibido")):
                    continue
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
                content = f.read_text(encoding="utf-8", errors="ignore")
                low = content.lower()
                if "alucinacao" not in low:
                    continue
                if not any(p in low for p in ("integr", "merge", "insert")):
                    continue
                # Já é um guard (exclui/filtra/skip)?
                if any(p in low for p in ("exclu", "filter", "skip", "!= 'alucinacao'", "== 'alucinacao'")):
                    continue
                # Guard por comparação ou contagem?
                if _ALUC_GUARD.search(content):
                    continue
                # Arquivo de classificação 3-tier: classifica REAL/SINTÉTICO/ALUCINAÇÃO, não integra
                if "classify" in f.name.lower() or "classifica" in f.name.lower():
                    continue
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
        # Exclui worktrees (cópias temporárias de agentes, não são docs do projeto)
        for f in (ROOT / ".claude").rglob("*.md"):
            if "worktrees" in f.parts:
                continue
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

    if args.all or args.claim == "deskrio":
        print("\n[9] Deskrio snapshots integrity...")
        desk_issues = []
        desk_root = ROOT / "data" / "deskrio"
        if not desk_root.exists():
            desk_issues.append("data/deskrio/ não existe")
        else:
            # Verificar últimos 7 dias
            expected = {
                "connections.json": 500,
                "contacts.json": 1_000_000,
                "kanban_boards.json": 500,
                "tickets.json": 100,
            }
            today = date.today()
            days_checked = 0
            for delta in range(7):
                d = today - timedelta(days=delta)
                day_dir = desk_root / d.isoformat()
                if not day_dir.exists():
                    continue
                days_checked += 1
                for fname, min_size in expected.items():
                    fpath = day_dir / fname
                    if not fpath.exists():
                        desk_issues.append(f"{d.isoformat()}/{fname} AUSENTE")
                        continue
                    size = fpath.stat().st_size
                    if size < min_size:
                        desk_issues.append(f"{d.isoformat()}/{fname} muito pequeno ({size} < {min_size})")
                        continue
                    # Detectar corpo de erro 403
                    try:
                        head = fpath.read_text(encoding="utf-8", errors="ignore")[:300]
                        if "Invalid token" in head or '"statusCode":403' in head:
                            desk_issues.append(f"{d.isoformat()}/{fname} contém ERRO 403 persistido")
                    except Exception:
                        pass
            if days_checked == 0:
                desk_issues.append("Nenhum snapshot encontrado nos últimos 7 dias")
        status = "WARN" if desk_issues else "PASS"
        results["deskrio"] = {"status": status, "issues": desk_issues}
        print(f"  {status}: {len(desk_issues)} issues" if desk_issues else f"  {status}")
        for iss in desk_issues[:5]:
            print(f"    -> {iss}")

    if args.all or args.claim == "sales_hunter":
        print("\n[10] Sales Hunter integrity...")
        sh_issues = []
        sh_warns = []
        try:
            import sqlite3
            db_path = ROOT / "data" / "crm_vitao360.db"
            if not db_path.exists():
                sh_issues.append("data/crm_vitao360.db não existe")
            else:
                con = sqlite3.connect(str(db_path))
                # Tabela debitos_clientes existe?
                tbls = {r[0] for r in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()}
                if "debitos_clientes" not in tbls:
                    sh_issues.append("tabela debitos_clientes ausente (migration nao aplicada)")
                else:
                    # CNPJ no formato correto em debitos_clientes
                    bad_cnpj = con.execute(
                        "SELECT COUNT(*) FROM debitos_clientes "
                        "WHERE LENGTH(cnpj) != 14 OR cnpj GLOB '*[^0-9]*'"
                    ).fetchone()[0]
                    if bad_cnpj > 0:
                        sh_issues.append(
                            f"{bad_cnpj} CNPJs invalidos em debitos_clientes (R2)"
                        )
                # ImportJob SALES_HUNTER recente
                jobs = con.execute(
                    "SELECT COUNT(*) FROM import_jobs "
                    "WHERE tipo='SALES_HUNTER' AND status='CONCLUIDO'"
                ).fetchone()[0]
                if jobs == 0:
                    sh_warns.append(
                        "Nenhum ImportJob SALES_HUNTER CONCLUIDO ainda"
                    )
                # Faturamento populado?
                clientes_com_fat = con.execute(
                    "SELECT COUNT(*) FROM clientes "
                    "WHERE faturamento_total IS NOT NULL AND faturamento_total > 0"
                ).fetchone()[0]
                total_clientes = con.execute(
                    "SELECT COUNT(*) FROM clientes"
                ).fetchone()[0]
                if total_clientes > 0:
                    pct = clientes_com_fat / total_clientes * 100
                    if pct < 20:
                        sh_warns.append(
                            f"Apenas {pct:.0f}% dos clientes tem faturamento populado "
                            f"({clientes_com_fat}/{total_clientes})"
                        )
                con.close()
        except Exception as exc:
            sh_warns.append(f"Erro ao inspecionar DB: {exc}")
        status = "FAIL" if sh_issues else ("WARN" if sh_warns else "PASS")
        results["sales_hunter"] = {
            "status": status,
            "issues": sh_issues + sh_warns,
        }
        all_msgs = sh_issues + sh_warns
        print(
            f"  {status}: {len(all_msgs)} issues" if all_msgs else f"  {status}"
        )
        for iss in all_msgs[:5]:
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
