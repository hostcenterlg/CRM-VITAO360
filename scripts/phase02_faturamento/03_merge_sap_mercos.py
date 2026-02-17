#!/usr/bin/env python3
"""
Phase 02, Plan 02, Task 1a: Merge SAP-First + Mercos-Complement
================================================================
Combines SAP and Mercos sales data using SAP-First strategy:
- SAP as primary source
- Mercos fills gaps where SAP=0 but Mercos>0
- JAN/26 stored separately (only from Mercos)
- No double-counting

Input:
  data/output/phase02/mercos_vendas.json
  data/output/phase02/sap_vendas.json

Output:
  data/output/phase02/sap_mercos_merged.json
"""

import json
import os
import re
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def normalize_cnpj(raw):
    """Normalize CNPJ to 14-digit string."""
    return re.sub(r'[^0-9]', '', str(raw)).zfill(14)


def load_json(path):
    """Load a JSON file and return the parsed data."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_sap_mercos():
    """Merge SAP and Mercos sales data using SAP-First strategy."""

    # 1. Load input JSONs from Plan 02-01
    mercos_path = PROJECT_ROOT / "data" / "output" / "phase02" / "mercos_vendas.json"
    sap_path = PROJECT_ROOT / "data" / "output" / "phase02" / "sap_vendas.json"

    print("=" * 70)
    print("MERGE SAP-FIRST + MERCOS-COMPLEMENT")
    print("=" * 70)
    print()

    mercos_data = load_json(mercos_path)
    sap_data = load_json(sap_path)

    print(f"Loaded Mercos: {len(mercos_data['cnpj_to_vendas'])} clients with CNPJ")
    print(f"Loaded SAP:    {len(sap_data['cnpj_to_vendas'])} clients")
    print()

    # 2. MERGE SAP-FIRST
    merged = {}
    stats = {
        "sap_only": 0,
        "mercos_only": 0,
        "both_sap_base": 0,
        "months_filled_from_mercos": 0,  # track how many month-cells Mercos filled
    }

    sap_cnpjs = set(sap_data["cnpj_to_vendas"].keys())
    mercos_cnpjs = set(mercos_data["cnpj_to_vendas"].keys())
    all_cnpjs = sap_cnpjs | mercos_cnpjs

    negatives_zeroed = 0  # track SAP credit notes zeroed out

    for cnpj in sorted(all_cnpjs):
        sap = sap_data["cnpj_to_vendas"].get(cnpj)
        mercos = mercos_data["cnpj_to_vendas"].get(cnpj)

        if sap and mercos:
            # Both sources: SAP as base. For months where SAP=0 but Mercos>0, use Mercos
            result = []
            for s, m in zip(sap, mercos):
                if s > 0:
                    result.append(s)
                elif s < 0:
                    # SAP credit note/return -- zero it out, use Mercos if available
                    negatives_zeroed += 1
                    if m > 0:
                        result.append(m)
                        stats["months_filled_from_mercos"] += 1
                    else:
                        result.append(0.0)
                elif m > 0:
                    result.append(m)
                    stats["months_filled_from_mercos"] += 1
                else:
                    result.append(0.0)
            merged[cnpj] = result
            stats["both_sap_base"] += 1
        elif sap:
            # SAP-only: zero out any negative values
            cleaned = []
            for s in sap:
                if s < 0:
                    negatives_zeroed += 1
                    cleaned.append(0.0)
                else:
                    cleaned.append(s)
            merged[cnpj] = cleaned
            stats["sap_only"] += 1
        else:
            merged[cnpj] = mercos
            stats["mercos_only"] += 1

    # 3. Handle JAN/26 (outside the 12-month 2025 array)
    # JAN/26 comes only from Mercos
    jan26_vendas = {}
    if "jan26_vendas" in mercos_data:
        for cnpj, valor in mercos_data["jan26_vendas"].items():
            if valor > 0:
                jan26_vendas[cnpj] = round(valor, 2)

    # 4. Calculate totals (before fuzzy match -- Task 1b will update)
    total_vendas_2025 = 0.0
    for cnpj, vals in merged.items():
        total_vendas_2025 += sum(vals)

    total_jan26 = sum(jan26_vendas.values())

    stats["total_clientes"] = len(merged)
    stats["total_vendas_2025"] = round(total_vendas_2025, 2)
    stats["total_jan26"] = round(total_jan26, 2)
    stats["fuzzy_matched"] = 0
    stats["unmatched"] = 0
    stats["negatives_zeroed"] = negatives_zeroed

    # 5. Validate: no negative values remain after cleanup
    negatives_found = 0
    for cnpj, vals in merged.items():
        for v in vals:
            if v < 0:
                negatives_found += 1
                print(f"  WARNING: Negative value still present for CNPJ {cnpj}: {v}")

    # 6. Build output JSON
    output = {
        "cnpj_to_vendas": merged,
        "jan26_vendas": jan26_vendas,
        "unmatched": [],
        "fuzzy_matches": [],
        "stats": stats,
        "source": "SAP-First + Mercos-Complement",
        "carteira_population": (
            "DEFERRED -- CARTEIRA V13 has only 3 data rows. "
            "Population deferred to Phase 9 when client roster is complete."
        ),
    }

    # 7. Save JSON
    output_path = PROJECT_ROOT / "data" / "output" / "phase02" / "sap_mercos_merged.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 8. Print report
    print("-" * 70)
    print("MERGE RESULTS")
    print("-" * 70)
    print(f"  SAP-only clients:        {stats['sap_only']}")
    print(f"  Mercos-only clients:      {stats['mercos_only']}")
    print(f"  Both (SAP base):          {stats['both_sap_base']}")
    print(f"  Months filled from Mercos: {stats['months_filled_from_mercos']}")
    print(f"  ---")
    print(f"  TOTAL unique clients:     {stats['total_clientes']}")
    print(f"  Total vendas 2025:        R$ {stats['total_vendas_2025']:,.2f}")
    print(f"  Total JAN/26:             R$ {stats['total_jan26']:,.2f}")
    print(f"  SAP negatives zeroed:     {negatives_zeroed}")
    print(f"  Negative values remaining: {negatives_found}")
    print()

    # Consistency check
    expected_total = stats["sap_only"] + stats["mercos_only"] + stats["both_sap_base"]
    assert expected_total == stats["total_clientes"], (
        f"Stats inconsistency: {expected_total} != {stats['total_clientes']}"
    )
    print(f"  Consistency check: sap_only({stats['sap_only']}) + "
          f"mercos_only({stats['mercos_only']}) + "
          f"both({stats['both_sap_base']}) = "
          f"{expected_total} == total({stats['total_clientes']}) PASS")
    print()
    print(f"  NOTE: 10 clients without CNPJ pending fuzzy match (Task 1b)")
    print()
    print(f"  Output: {output_path}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    merge_sap_mercos()
