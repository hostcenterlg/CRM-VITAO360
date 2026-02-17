---
phase: 01-projecao
plan: 02
subsystem: data-population
tags: [openpyxl, excel, sap, cnpj, etl, read-modify-write, formulas]

# Dependency graph
requires:
  - phase: 01-projecao-01
    provides: "SAP data extracted as JSON (metas, vendas, weights)"
provides:
  - "CRM_VITAO360_V13_PROJECAO.xlsx with SAP 2026 data populated"
  - "534 client metas updated (R$ 4,779,003.04 total)"
  - "485 client vendas 2025 populated (R$ 2,081,030.28 total)"
  - "19,224 formulas preserved intact"
  - "Reproducible idempotent population script"
affects: [01-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [read-modify-write, safe_float, formula-column-blacklist]

key-files:
  created:
    - scripts/phase01_projecao/03_populate_projecao.py
    - data/output/CRM_VITAO360_V13_PROJECAO.xlsx
  modified: []

key-decisions:
  - "Vendas for unmatched CNPJs set to 0 (49 clients) rather than preserving old values"
  - "Monthly weights produce 0.001% rounding vs annual due to float precision -- acceptable"
  - "41 clients with zero annual meta get zero monthly values (no division needed)"

patterns-established:
  - "Read-Modify-Write: load with data_only=False, write only data columns, save preserves formulas"
  - "Formula column blacklist: F-J, Z, AN-AQ, BB-CB are never touched by write operations"
  - "safe_float: defensive numeric conversion for all monetary values from JSON"

# Metrics
duration: 6min
completed: 2026-02-17
---

# Phase 01 Plan 02: Populate PROJECAO with SAP 2026 Data Summary

**534 clients updated with SAP 2026 metas (R$ 4.78M) and 2025 vendas (R$ 2.08M) via Read-Modify-Write preserving all 19,224 formulas in V13 output**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-17T00:58:19Z
- **Completed:** 2026-02-17T01:04:28Z
- **Tasks:** 1
- **Files created:** 2

## Accomplishments
- All 534 clients processed: META ANUAL (col L), META MENSAL JAN-DEZ (cols M-X), and REALIZADO JAN-DEZ (cols AA-AL) populated from SAP JSON
- Total META populated: R$ 4,779,003.04 across 534 clients (41 with zero meta)
- Total VENDAS populated: R$ 2,081,030.28 across 485 clients with sales data (49 zeroed)
- Monthly metas distributed using SAP weights (12 months, sum=0.999990) with 0.001% rounding tolerance
- All 19,224 formulas verified intact after population (formula count exact match)
- R$ number format preserved on all monetary cells
- freeze_panes (E30) and all workbook properties preserved
- Output file: 380KB (data/output/CRM_VITAO360_V13_PROJECAO.xlsx)

## Task Commits

Each task was committed atomically:

1. **Task 1: Populate PROJECAO with SAP 2026 data** - `5bc77cf` (feat)

## Files Created/Modified
- `scripts/phase01_projecao/03_populate_projecao.py` - Read-Modify-Write script: loads SAP JSON, opens PROJECAO with formulas preserved, populates data columns, verifies formulas, saves V13 output
- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - V13 PROJECAO with SAP 2026 data populated (380KB, 537 rows x 80 cols)

## Decisions Made

1. **Unmatched vendas clients zeroed:** 49 clients without SAP vendas data get 0 in all REALIZADO columns (AA-AL) rather than preserving whatever old values existed. This ensures clean data -- the formulas (Z=SUM, %YTD, GAP) will correctly show zero realization.

2. **Monthly weight rounding accepted:** Multiplying meta_anual by each monthly weight produces a sum that's ~0.001% less than the annual total (e.g., R$ 10,600.92 vs R$ 10,601.03 for row 4). This is due to float precision with weights summing to 0.999990 instead of 1.0. The difference is negligible (< R$ 0.50 per client).

3. **Zero-meta clients handled:** 41 clients have zero annual meta from SAP. Their monthly columns are set to 0 (not skipped), ensuring the formula infrastructure works correctly (no division-by-zero issues in %YTD calculations, which already have IF(L=0,0,...) guards).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Vendas total discrepancy:** Script populated R$ 2,081,030.28 vs SAP extraction total of R$ 2,089,824.23. The R$ 8,793.95 difference comes from 4 CNPJs present in SAP vendas data but not in the PROJECAO file's 534 client list. These 4 clients have sales but no row in PROJECAO, so their data cannot be populated. This is expected -- the PROJECAO file has a fixed client roster.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- V13 PROJECAO ready with fresh SAP 2026 data for Plan 03 (final validation + integrity checks)
- All formula recalculations will activate when opened in Excel (SUM, %YTD, sinaleiro, GAP, ranking)
- Note: LibreOffice Calc may calculate differently from Excel -- final validation should ideally be in Excel
- The 49 clients with zeroed vendas may show as "zero realization" in sinaleiro -- this is correct behavior

## Self-Check: PASSED

- [x] scripts/phase01_projecao/03_populate_projecao.py exists
- [x] data/output/CRM_VITAO360_V13_PROJECAO.xlsx exists
- [x] Commit 5bc77cf exists (Task 1)

---
*Phase: 01-projecao*
*Completed: 2026-02-17*
