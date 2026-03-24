#!/usr/bin/env python3
"""
CRM VITAO360 — Session Boot Script
Verifica estado do projeto e gera .cache/project_reality.json
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
    print("CRM VITAO360 — SESSION BOOT")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    reality = {
        "boot_time": datetime.now().isoformat(),
        "project": "CRM VITAO360",
        "checks": {},
        "warnings": [],
        "errors": [],
        "sources": {},
        "scripts": [],
        "abas_esperadas": [
            "CARTEIRA", "CRM TRATADO", "PROJEÇÃO", "LOG", "AGENDA",
            "COMITÊ", "DASH", "E-COMMERCE", "REDES", "SINALEIRO",
            "BLUEPRINT", "REGRAS", "FUNIL", "TIMELINE"
        ]
    }

    # Check 1: Required files
    print("\n[1/5] Verificando arquivos obrigatórios...")
    required_files = {
        "briefing": ROOT / "BRIEFING-COMPLETO.md",
        "inteligencia": ROOT / "INTELIGENCIA_NEGOCIO_CRM360.md",
        "backup": ROOT / "BACKUP_DOCUMENTACAO_ANTIGA.md",
    }
    for name, path in required_files.items():
        exists = path.exists()
        reality["checks"][f"file_{name}"] = "PASS" if exists else "FAIL"
        status = "OK" if exists else "MISSING"
        print(f"  {name}: {status} ({path.name})")
        if not exists:
            reality["errors"].append(f"Arquivo obrigatório missing: {path.name}")

    # Check 2: Python dependencies
    print("\n[2/5] Verificando dependências Python...")
    deps = ["openpyxl", "pandas", "rapidfuzz"]
    for dep in deps:
        try:
            __import__(dep)
            reality["checks"][f"dep_{dep}"] = "PASS"
            print(f"  {dep}: OK")
        except ImportError:
            reality["checks"][f"dep_{dep}"] = "FAIL"
            reality["errors"].append(f"Dependência missing: {dep}")
            print(f"  {dep}: MISSING (pip install {dep})")

    # Check 3: Data sources
    print("\n[3/5] Verificando fontes de dados...")
    data_dir = ROOT / "data"
    sources_dir = ROOT / "data" / "sources" if (ROOT / "data" / "sources").exists() else ROOT / "sources"
    output_dir = ROOT / "data" / "output" if (ROOT / "data" / "output").exists() else ROOT / "output"

    for d_name, d_path in [("data", data_dir), ("sources", sources_dir), ("output", output_dir)]:
        if d_path.exists():
            files = list(d_path.glob("*"))
            xlsx_files = [f for f in files if f.suffix.lower() in ['.xlsx', '.xls']]
            reality["sources"][d_name] = {
                "path": str(d_path),
                "total_files": len(files),
                "xlsx_files": len(xlsx_files)
            }
            print(f"  {d_name}/: {len(files)} files ({len(xlsx_files)} xlsx)")
        else:
            reality["sources"][d_name] = {"path": str(d_path), "exists": False}
            print(f"  {d_name}/: NÃO EXISTE")

    # Check 4: Scripts inventory
    print("\n[4/5] Inventariando scripts...")
    scripts_dir = ROOT / "scripts"
    if scripts_dir.exists():
        py_files = list(scripts_dir.glob("*.py"))
        phase_dirs = list(scripts_dir.glob("phase*"))
        reality["scripts"] = [f.name for f in py_files]
        print(f"  Scripts raiz: {len(py_files)}")
        print(f"  Diretórios de fase: {len(phase_dirs)}")
    else:
        print("  scripts/: NÃO EXISTE")
        reality["warnings"].append("Diretório scripts/ não encontrado")

    # Check 5: Git status
    print("\n[5/5] Verificando git...")
    if (ROOT / ".git").exists():
        reality["checks"]["git"] = "PASS"
        print("  Git: OK (repositório inicializado)")
    else:
        reality["checks"]["git"] = "FAIL"
        reality["warnings"].append("Git não inicializado")
        print("  Git: NÃO INICIALIZADO")

    # Summary
    errors = len(reality["errors"])
    warnings = len(reality["warnings"])
    passes = sum(1 for v in reality["checks"].values() if v == "PASS")
    fails = sum(1 for v in reality["checks"].values() if v == "FAIL")

    print("\n" + "=" * 60)
    print(f"RESULTADO: {passes} PASS | {fails} FAIL | {warnings} WARNINGS")
    if errors > 0:
        print(f"\nERROS ({errors}):")
        for e in reality["errors"]:
            print(f"  X {e}")
    if warnings > 0:
        print(f"\nWARNINGS ({warnings}):")
        for w in reality["warnings"]:
            print(f"  ! {w}")

    elapsed = time.time() - start
    reality["elapsed_seconds"] = round(elapsed, 2)
    print(f"\nTempo: {elapsed:.1f}s")
    print("=" * 60)

    # Save reality
    output_path = CACHE / "project_reality.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reality, f, indent=2, ensure_ascii=False)
    print(f"\nSalvo em: {output_path}")

    # Exit code 2 = BLOQUEIA hooks do Claude Code (SessionStart)
    # Exit code 0 = permite prosseguir
    if fails > 0:
        print("\nBOOT FALHOU — sessão BLOQUEADA até corrigir.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
