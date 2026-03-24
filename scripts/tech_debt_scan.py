#!/usr/bin/env python3
"""
TECH DEBT SCANNER — CRM VITAO360 SaaS
Scanneia código por dívida técnica: TODO/FIXME, stubs, hardcoded paths,
dead imports, 'as any', patterns de Excel onde deveria ser Supabase.
Salva .cache/tech_debt_report.json. Informacional (não bloqueia).
"""
import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / ".cache"
CACHE.mkdir(exist_ok=True)

# Scripts de enforcement (excluir da varredura)
EXCLUDE_FILES = {
    "tech_debt_scan.py", "verify.py", "session_boot.py",
    "compliance_gate.py", "preflight_check.py", "postflight_check.py",
}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".cache", "venv", ".venv"}

PATTERNS = {
    "TODO/FIXME": re.compile(r'\b(TODO|FIXME|XXX|HACK|PLACEHOLDER)\b', re.IGNORECASE),
    "Stub/Placeholder": re.compile(r'(return None|return \{\}|return \[\]|raise NotImplementedError|pass\s*$|coming soon|lorem ipsum)', re.IGNORECASE),
    "Hardcoded path": re.compile(r'[A-Z]:\\\\|C:/Users|/home/|/tmp/(?!\.)', re.IGNORECASE),
    "Hardcoded secret": re.compile(r'(password\s*=\s*["\']|api_key\s*=\s*["\']|token\s*=\s*["\']eyJ)', re.IGNORECASE),
    "Dead import": re.compile(r'^import\s+\w+\s*$|^from\s+\w+\s+import\s+\*', re.MULTILINE),
    "Excel dependency (should be Supabase)": re.compile(r'openpyxl\.(load_workbook|Workbook)|\.xlsx|data_only=True', re.IGNORECASE),
    "CNPJ as float": re.compile(r'(int\(cnpj|float\(cnpj|cnpj.*int\(|cnpj.*float\()', re.IGNORECASE),
    "Two-Base violation hint": re.compile(r'(LOG|log_atendimento).*valor.*[1-9]', re.IGNORECASE),
    "ALUCINAÇÃO integration": re.compile(r'(insert|append|merge).*alucinac', re.IGNORECASE),
    "Print debug": re.compile(r'print\s*\(\s*["\']debug|print\s*\(\s*["\']test', re.IGNORECASE),
}

print("=" * 60)
print("CRM VITAO360 — TECH DEBT SCAN")
print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

findings = defaultdict(list)
file_count = 0
total_debt = 0

SCAN_DIRS = [
    BASE / "scripts",
    BASE / "src",
    BASE / "app",
    BASE / "lib",
    BASE / "api",
    BASE / "components",
    BASE / "pages",
    BASE / "supabase",
]

for scan_dir in SCAN_DIRS:
    if not scan_dir.exists():
        continue
    for root, dirs, files in os.walk(scan_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            if fname in EXCLUDE_FILES:
                continue
            if not fname.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".sql")):
                continue

            fpath = Path(root) / fname
            file_count += 1

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    for pattern_name, pattern in PATTERNS.items():
                        if pattern.search(line):
                            findings[pattern_name].append({
                                "file": str(fpath.relative_to(BASE)),
                                "line": i,
                                "text": line.strip()[:120],
                            })
                            total_debt += 1
            except Exception:
                pass

# Report
print(f"\nArquivos escaneados: {file_count}")
print(f"Dívida técnica encontrada: {total_debt} items\n")

for category, items in sorted(findings.items(), key=lambda x: -len(x[1])):
    print(f"  [{len(items)}] {category}")
    for item in items[:5]:
        print(f"      {item['file']}:{item['line']} — {item['text'][:80]}")
    if len(items) > 5:
        print(f"      ... e mais {len(items) - 5}")

# Severity
severity = "LOW"
if total_debt > 20:
    severity = "MEDIUM"
if total_debt > 50:
    severity = "HIGH"
if any(k in findings for k in ["Hardcoded secret", "ALUCINAÇÃO integration", "Two-Base violation hint"]):
    severity = "HIGH"

# Save report
report = {
    "timestamp": datetime.now().isoformat(),
    "files_scanned": file_count,
    "total_findings": total_debt,
    "severity": severity,
    "categories": {k: len(v) for k, v in findings.items()},
    "findings": dict(findings),
}

report_path = CACHE / "tech_debt_report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(f"\n{'=' * 60}")
print(f"SEVERIDADE: {severity}")
print(f"Relatório: {report_path}")
print(f"{'=' * 60}")
