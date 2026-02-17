---
phase: 02-faturamento
plan: 01
subsystem: etl
tags: [openpyxl, mercos, sap, cnpj, vendas, json, python]

# Dependency graph
requires:
  - phase: 01-projecao
    provides: sap_data_extracted.json with 489 CNPJs and R$ 2,089,824.23 for cross-check
provides:
  - mercos_vendas.json with 453+10 clients monthly sales by CNPJ (FEV-DEZ 2025 + JAN26)
  - sap_vendas.json with 489 clients monthly faturado by CNPJ (JAN-DEZ 2025)
  - 11 Mercos armadilhas validated (FAT-03 pre-requisite)
  - Standardized array[12] format for both sources ready for merge
affects: [02-02 (merge SAP+Mercos), 02-03 (populate CARTEIRA)]

# Tech tracking
tech-stack:
  added: []
  patterns: [extract_sem_cnpj from dedicated sheet, cross-check vs prior phase output]

key-files:
  created:
    - scripts/phase02_faturamento/01_extract_mercos_vendas.py
    - scripts/phase02_faturamento/02_extract_sap_vendas.py
    - data/output/phase02/mercos_vendas.json
    - data/output/phase02/sap_vendas.json
  modified: []

key-decisions:
  - "Sem CNPJ clients are on dedicated sheet, not in Vendas Mes a Mes -- extract separately"
  - "Independent SAP re-extraction for cross-validation (not reusing Phase 1 JSON)"
  - "Resumo Mensal includes sem_cnpj totals -- total geral matches R$ 2,010,545.72 exactly"

patterns-established:
  - "Phase 02 JSON format: cnpj_to_vendas dict with array[12] [JAN..DEZ] per CNPJ"
  - "Sem CNPJ clients stored as list with nome + monthly breakdown + total"
  - "Cross-check pattern: compare new extraction vs prior phase output for data integrity"

# Metrics
duration: 18min
completed: 2026-02-17
---

# Phase 02 Plan 01: Data Extraction Summary

**ETL de vendas Mercos (453+10 clientes) e SAP faturado (489 clientes) em JSON padronizado com validacao de 11 armadilhas e cross-check contra Phase 1**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-17T02:06:52Z
- **Completed:** 2026-02-17T02:25:51Z
- **Tasks:** 2
- **Files created:** 4

## Accomplishments
- Extracted Mercos monthly sales: 453 clients with CNPJ + 10 without CNPJ, total R$ 2,010,545.72 (exact match with reference)
- Extracted SAP monthly faturado: 489 clients, total R$ 2,089,824.23 (exact match with Phase 1 -- 0.0000% diff)
- Validated all 11 known Mercos armadilhas: 11/11 VALIDADO, 0 ALERTA (FAT-03 pre-requisite satisfied)
- Both sources use identical format: dict[cnpj] -> array[12] [JAN=0..DEZ=11] ready for merge in Plan 02-02

## Task Commits

Each task was committed atomically:

1. **Task 1: Extrair vendas mensais Mercos do 02_VENDAS_POSITIVACAO** - `2b89555` (feat)
2. **Task 2: Extrair faturado mensal SAP do 01_SAP_CONSOLIDADO** - `13c4f63` (feat)

## Files Created/Modified
- `scripts/phase02_faturamento/01_extract_mercos_vendas.py` - ETL Mercos: reads 02_VENDAS_POSITIVACAO_MERCOS.xlsx, extracts vendas by CNPJ, validates armadilhas
- `scripts/phase02_faturamento/02_extract_sap_vendas.py` - ETL SAP: reads 01_SAP_CONSOLIDADO.xlsx, extracts faturado by CNPJ, cross-checks vs Phase 1
- `data/output/phase02/mercos_vendas.json` - 453 CNPJs + 10 sem_cnpj + resumo_mensal + armadilhas_validation
- `data/output/phase02/sap_vendas.json` - 489 CNPJs + stats + cross_check result

## Decisions Made
- **Sem CNPJ on dedicated sheet:** The "Vendas Mes a Mes" sheet contains only clients WITH CNPJ (453 rows). The 10 clients without CNPJ are on a separate "Sem CNPJ" sheet with different column structure (A=Nome, B-L=FEV-DEZ, M=JAN26, N=Total). Script extracts both sheets.
- **Independent re-extraction for SAP:** Instead of reusing Phase 1 JSON, the script re-reads the Excel for independent validation. Cross-check confirms 489/489 CNPJs match exactly with R$ 0.00 diff.
- **Resumo Mensal includes sem_cnpj:** The R$ 2,010,545.72 reference total includes both CNPJ clients (R$ 1,895,101.56 FEV-DEZ) and sem_cnpj clients (R$ 1,406.13 FEV-DEZ). With JAN26 (R$ 114,038.03), total matches reference exactly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Sem CNPJ clients not extracted from Vendas Mes a Mes sheet**
- **Found during:** Task 1 (Mercos extraction)
- **Issue:** Initial implementation only read "Vendas Mes a Mes" sheet which has 453 clients all WITH CNPJ. The 10 sem_cnpj clients are on a dedicated "Sem CNPJ" sheet with different column layout.
- **Fix:** Added `extract_sem_cnpj()` function to read the dedicated sheet (rows 4-13, col A=nome, B-L=monthly, M=JAN26, N=total). Integrated into main() and stats calculation.
- **Files modified:** scripts/phase02_faturamento/01_extract_mercos_vendas.py
- **Verification:** Total geral went from R$ 1,996,217.03 (0.71% off) to R$ 2,010,545.72 (0.0000% -- exact match)
- **Committed in:** 2b89555 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix -- without it, 10 clients (R$ 14,328.69) would be missing from the extraction. No scope creep.

## Issues Encountered
None -- both scripts ran on first attempt after the sem_cnpj fix.

## Key Metrics

| Metric | Mercos | SAP |
|--------|--------|-----|
| Clients | 453 + 10 sem CNPJ | 489 |
| Total | R$ 2,010,545.72 | R$ 2,089,824.23 |
| Months | FEV-DEZ (JAN=0) + JAN26 | JAN-DEZ (all 12) |
| vs Reference | 0.0000% diff | 0.0000% diff |
| Format | array[12] + jan26 separate | array[12] |
| Armadilhas | 11/11 VALIDADO | N/A |

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both JSON intermediaries ready for merge in Plan 02-02 (SAP-First + Mercos complement)
- Standardized format ensures direct array comparison and aggregation
- 10 sem_cnpj clients documented for potential fuzzy matching in Plan 02-02
- Armadilhas validation satisfies FAT-03 pre-requisite

## Self-Check: PASSED

- [x] scripts/phase02_faturamento/01_extract_mercos_vendas.py - FOUND
- [x] scripts/phase02_faturamento/02_extract_sap_vendas.py - FOUND
- [x] data/output/phase02/mercos_vendas.json - FOUND
- [x] data/output/phase02/sap_vendas.json - FOUND
- [x] .planning/phases/02-faturamento/02-01-SUMMARY.md - FOUND
- [x] Commit 2b89555 (Task 1) - FOUND
- [x] Commit 13c4f63 (Task 2) - FOUND

---
*Phase: 02-faturamento*
*Completed: 2026-02-17*
