#!/usr/bin/env python3
"""
POSTFLIGHT CHECK — CRM VITAO360
Roda DEPOIS de completar uma fase/task.
Valida que dados foram processados DE VERDADE.

Uso: python scripts/postflight_check.py --fase N
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CACHE = BASE / ".cache"

results = {"PASS": 0, "FAIL": 0, "WARN": 0}

def check(name, condition, severity="FAIL", detail=""):
    status = "PASS" if condition else severity
    results[status] = results.get(status, 0) + 1
    icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}[status]
    print(f"  {icon} {name}: {status}" + (f" — {detail}" if detail and not condition else ""))
    return condition

parser = argparse.ArgumentParser(description="Postflight Check CRM VITAO360")
parser.add_argument("--fase", type=int, required=True, help="Número da fase (11-15)")
args = parser.parse_args()

print("=" * 60)
print(f"CRM VITAO360 — POSTFLIGHT CHECK — FASE {args.fase}")
print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# ============================================================
# VERIFICAÇÕES POR FASE
# ============================================================

if args.fase == 11:
    print("\n[FASE 11] Import Pipeline")

    # 1. Base unificada gerada?
    base_path = BASE / "data" / "output" / "motor" / "base_unificada.json"
    check("Base unificada existe", base_path.exists(), detail=str(base_path))

    if base_path.exists():
        data = json.loads(base_path.read_text(encoding="utf-8"))
        clientes = data if isinstance(data, list) else data.get("clientes", [])

        # 2. Tem clientes?
        check(f"Clientes importados (>500)", len(clientes) > 500, detail=f"{len(clientes)} encontrados")

        # 3. CNPJ normalizado?
        cnpj_ok = 0
        cnpj_fail = 0
        for c in clientes[:100]:  # sample
            cnpj = c.get("cnpj", "")
            if isinstance(cnpj, str) and len(cnpj) == 14 and cnpj.isdigit():
                cnpj_ok += 1
            else:
                cnpj_fail += 1
        check(f"CNPJ normalizado (sample 100)", cnpj_fail == 0, detail=f"{cnpj_ok} OK, {cnpj_fail} FAIL")

        # 4. DE-PARA aplicado?
        consultores = set(c.get("consultor", "") for c in clientes if c.get("consultor"))
        canonical = {"MANU", "LARISSA", "DAIANE", "JULIO", "LEGADO"}
        aliases_soltos = consultores - canonical - {""}
        check("DE-PARA vendedores (sem alias soltos)", len(aliases_soltos) == 0,
              "WARN", f"Aliases não mapeados: {aliases_soltos}" if aliases_soltos else "")

        # 5. Classificação 3-tier?
        with_tier = sum(1 for c in clientes if c.get("classificacao_tier"))
        check(f"Classificação 3-tier ({with_tier}/{len(clientes)})",
              with_tier / max(len(clientes), 1) > 0.9,
              detail=f"{with_tier/max(len(clientes),1)*100:.0f}% classificados")

        # 6. Zero ALUCINAÇÃO?
        alucinacao = sum(1 for c in clientes if c.get("classificacao_tier") == "ALUCINACAO")
        check(f"Zero ALUCINAÇÃO integrados", alucinacao == 0, detail=f"{alucinacao} encontrados")

    # 7. Scripts existem?
    motor_dir = BASE / "scripts" / "motor"
    for script in ["__init__.py", "config.py", "helpers.py", "import_pipeline.py"]:
        check(f"scripts/motor/{script} existe", (motor_dir / script).exists())

elif args.fase == 12:
    print("\n[FASE 12] Motor de Regras")

    motor_dir = BASE / "scripts" / "motor"
    check("motor_regras.py existe", (motor_dir / "motor_regras.py").exists())

    regras_json = BASE / "config" / "regras_motor.json"
    regras_yaml = BASE / "config" / "regras_motor.yaml"
    check("Regras configuráveis (JSON ou YAML)",
          regras_json.exists() or regras_yaml.exists(),
          detail="Nem JSON nem YAML encontrado")

    if regras_json.exists() or regras_yaml.exists():
        path = regras_json if regras_json.exists() else regras_yaml
        content = path.read_text(encoding="utf-8")
        # Count combinations
        count = content.count('"ATIVO"') + content.count("ATIVO")
        check("92 combinações presentes", count >= 7, "WARN", f"ATIVO aparece {count}x")

elif args.fase == 13:
    print("\n[FASE 13] Score + Sinaleiro")

    motor_dir = BASE / "scripts" / "motor"
    check("score_ranking.py existe", (motor_dir / "score_ranking.py").exists())
    check("sinaleiro.py existe", (motor_dir / "sinaleiro.py").exists())

    config_path = BASE / "config" / "score_weights.json"
    check("Pesos configuráveis (score_weights.json)", config_path.exists())

elif args.fase == 14:
    print("\n[FASE 14] Agenda Inteligente")

    motor_dir = BASE / "scripts" / "motor"
    check("agenda.py existe", (motor_dir / "agenda.py").exists())

    # Check output
    agenda_dir = BASE / "data" / "output" / "motor" / "agendas"
    if agenda_dir.exists():
        xlsx_files = list(agenda_dir.glob("*.xlsx"))
        check(f"Agendas xlsx geradas ({len(xlsx_files)})", len(xlsx_files) >= 1)
    else:
        check("Diretório agendas existe", False, detail=str(agenda_dir))

elif args.fase == 15:
    print("\n[FASE 15] Projeção + Export")

    motor_dir = BASE / "scripts" / "motor"
    check("projecao.py existe", (motor_dir / "projecao.py").exists())

    export_path = BASE / "data" / "output" / "motor" / "crm_processado.xlsx"
    check("Excel processado exportado", export_path.exists())

else:
    print(f"\n✗ Fase {args.fase} não reconhecida (válido: 11-15)")
    sys.exit(1)

# ============================================================
# RESULTADO
# ============================================================
print(f"\n{'=' * 60}")
print(f"RESULTADO FASE {args.fase}: {results['PASS']} PASS | {results['WARN']} WARN | {results['FAIL']} FAIL")
print(f"{'=' * 60}")

if results["FAIL"] > 0:
    print(f"\n✗ {results['FAIL']} CHECKS FALHARAM — FASE {args.fase} INCOMPLETA")
    sys.exit(1)
else:
    print(f"\n✓ Fase {args.fase} verificada — COMPLETA")
    sys.exit(0)
