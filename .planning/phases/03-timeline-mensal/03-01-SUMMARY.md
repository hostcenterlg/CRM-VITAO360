---
phase: 03-timeline-mensal
plan: 01
subsystem: etl
tags: [openpyxl, draft1, carteira, index-match, vendas, abc, cnpj, python]

# Dependency graph
requires:
  - phase: 02-faturamento/02
    provides: sap_mercos_merged.json with 537 clients, 12-month vendas arrays, jan26_vendas
provides:
  - DRAFT 1 populated with 537 merged clients vendas mensais MAR/25-JAN/26 + derived fields
  - CARTEIRA expanded to 554 rows with full INDEX/MATCH formulas referencing DRAFT 1
  - Population report JSON with ABC distribution, total vendas, audit trail
affects: [03-02 (ABC validation + recalc), Phase 9 (Blueprint CARTEIRA), Phase 10 (final consolidation)]

# Tech tracking
tech-stack:
  added: []
  patterns: [DRAFT 1 as data layer + CARTEIRA as formula layer (INDEX/MATCH cascade), value-write in DRAFT 1 + formula-write in CARTEIRA]

key-files:
  created:
    - scripts/phase03_timeline/01_populate_draft1_vendas.py
    - scripts/phase03_timeline/02_expand_carteira_formulas.py
    - data/output/phase03/draft1_population_report.json
  modified:
    - data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx

key-decisions:
  - "554 total DRAFT 1 rows (485 updated + 52 new + 17 pre-existing unmatched) vs plan's 537 estimate"
  - "CARTEIRA expanded for all 554 DRAFT 1 clients, not just 537 merged, to ensure full coverage"
  - "V12 COM_DADOS actual path: data/sources/crm-versoes/v11-v12/ (not data/sources/crm/ as plan stated)"
  - "Col 43 MEDIA MENSAL written as value, overwriting existing formula -- more reliable for 537+ rows"
  - "ABC distribution: A=298 (55%), B=220 (41%), C=19 (4%) -- heavily weighted toward high-value clients"

patterns-established:
  - "DRAFT 1 row 4 to max_row is the data range; CARTEIRA mirrors with formulas starting at row 4"
  - "CNPJ stored as 14-digit string (zfill) in both DRAFT 1 and CARTEIRA for INDEX/MATCH compatibility"
  - "46 formula columns per CARTEIRA row: identity (3-8), rede/equipe (9,11-13), compra (16-19), ecommerce (20-24), total (25), vendas (26-36), recorrencia (38-42), funil (44-52), regras (54)"

# Metrics
duration: 25min
completed: 2026-02-17
---

# Phase 03 Plan 01: DRAFT 1 + CARTEIRA Population Summary

**Populated DRAFT 1 with 537 clients vendas mensais (R$ 2,607k total, ABC: A=298/B=220/C=19) and expanded CARTEIRA to 554 rows with 25,484 INDEX/MATCH formulas**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-17T03:31:11Z
- **Completed:** 2026-02-17T03:55:45Z
- **Tasks:** 2
- **Files created/modified:** 4

## Accomplishments
- Populated DRAFT 1 with vendas mensais MAR/25-JAN/26 for 537 merged clients (485 updated, 52 new SAP-only/fuzzy)
- Calculated derived fields for all clients: Nro COMPRAS, CURVA ABC, MESES POSITIVADO, TICKET MEDIO, MEDIA MENSAL
- Expanded CARTEIRA from ~16 partial rows to 554 fully-formulated rows with INDEX/MATCH from DRAFT 1
- Total vendas: R$ 2,607,559.95 (all 13 months including JAN/FEV 2025 hidden in totals)
- ABC classification: A=298 (55.5%), B=220 (41.0%), C=19 (3.5%) -- 537 merged clients classified
- Generated population report with full audit trail and validation checks

## Task Commits

Each task was committed atomically:

1. **Task 1: Popular DRAFT 1 com vendas mensais + campos derivados** - `d0906a3` (feat)
2. **Task 2: Expandir formulas INDEX/MATCH da CARTEIRA** - `c065bca` (feat)

## Files Created/Modified
- `scripts/phase03_timeline/01_populate_draft1_vendas.py` - Populates DRAFT 1 with vendas from sap_mercos_merged.json + calculates derived fields
- `scripts/phase03_timeline/02_expand_carteira_formulas.py` - Expands CARTEIRA INDEX/MATCH formulas for all DRAFT 1 clients (46 formula columns x 554 rows)
- `data/output/phase03/draft1_population_report.json` - Population statistics: 537 clients, ABC distribution, total vendas, sample clients
- `data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` - V12 COM_DADOS with DRAFT 1 (554 data rows) and CARTEIRA (554 formula rows)

## Decisions Made
- **554 vs 537 rows:** DRAFT 1 had 502 existing rows but only 485 matched merged JSON CNPJs. 17 pre-existing clients were NOT in the merged data and were left untouched. 52 new SAP-only/fuzzy clients were added. Total: 485 + 17 + 52 = 554 rows.
- **CARTEIRA coverage for all 554:** Even though merged JSON has 537 clients, CARTEIRA formulas were expanded for all 554 DRAFT 1 rows. The 17 unmatched still have their original data and benefit from formula coverage.
- **File path correction:** Plan referenced `data/sources/crm/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` but actual file is at `data/sources/crm-versoes/v11-v12/`. Scripts use correct actual path.
- **MEDIA MENSAL as value:** Existing DRAFT 1 had `=IF(AJ{r}=0,0,IFERROR(SUM(U{r}:AF{r})/AJ{r},0))` formula in col 43. We overwrote with calculated value for the 537 merged clients. Formula is preserved for the 17 unmatched rows.
- **ABC based on total 13 months:** Includes JAN/25 + FEV/25 (R$ 103,893.89 hidden, no column) in the total used for ABC classification. This matches the documented threshold: A >= R$ 2000, B >= R$ 500, C < R$ 500.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] V12 COM_DADOS file path different from plan**
- **Found during:** Task 1 (script setup)
- **Issue:** Plan specified `data/sources/crm/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` but file is at `data/sources/crm-versoes/v11-v12/`
- **Fix:** Used correct actual path in both scripts
- **Files modified:** scripts/phase03_timeline/01_populate_draft1_vendas.py, scripts/phase03_timeline/02_expand_carteira_formulas.py
- **Verification:** File loads correctly, save succeeds
- **Committed in:** d0906a3, c065bca

**2. [Rule 2 - Missing Critical] CARTEIRA expanded for all 554 clients, not just 537**
- **Found during:** Task 2 (CARTEIRA expansion)
- **Issue:** Plan specified 537 rows but DRAFT 1 has 554 unique CNPJs (17 pre-existing not in merged JSON). Leaving those 17 without CARTEIRA formulas would create gaps.
- **Fix:** Read all 554 unique CNPJs from DRAFT 1 and expanded CARTEIRA to cover all of them
- **Files modified:** scripts/phase03_timeline/02_expand_carteira_formulas.py
- **Verification:** 554 rows with formulas confirmed, 0 gaps
- **Committed in:** c065bca

---

**Total deviations:** 2 auto-fixed (1 blocking path issue, 1 missing critical coverage)
**Impact on plan:** Both fixes essential for correctness. No scope creep -- same operations, just on slightly different inputs.

## Issues Encountered
- **17 unmatched DRAFT 1 rows:** 502 existing DRAFT 1 CNPJs minus 485 matched = 17 clients in DRAFT 1 but not in the merged JSON. These are likely Mercos-only clients with no vendas data in the SAP/Mercos merge period. Their existing data was preserved; their vendas columns were overwritten with 0s only if they matched (they didn't). No data loss.
- **CARTEIRA max_row 8305:** The CARTEIRA sheet reports max_row=8305 even though data only goes to row 557. This is because the original template had formulas and formatting extending far down. Our script only touched rows 4-557 and cleared 19 leftover rows in 558-576. The high max_row is cosmetic.

## User Setup Required
None - no external service configuration required.

## Key Metrics

| Metric | Value |
|--------|-------|
| Total DRAFT 1 data rows | 554 (485 updated + 52 new + 17 untouched) |
| Total merged clients processed | 537 |
| CARTEIRA formula rows | 554 |
| Total formulas written | 25,484 (46 cols x 554 rows) |
| ABC: A clients | 298 (55.5%) |
| ABC: B clients | 220 (41.0%) |
| ABC: C clients | 19 (3.5%) |
| Total vendas (13 months) | R$ 2,607,559.95 |
| Total vendas visible (MAR-JAN/26) | R$ 2,503,666.06 |
| JAN/FEV 2025 hidden in totals | R$ 103,893.89 |

## Next Phase Readiness
- DRAFT 1 fully populated -- ready for ABC validation and recalculation (Plan 03-02)
- CARTEIRA formulas will auto-populate when Excel recalculates -- vendas, ABC, TOTAL all pull from DRAFT 1
- V12 COM_DADOS is the working file for all remaining phases (CARTEIRA, LOG, DRAFT 2)
- 17 unmatched rows may need investigation in Plan 03-02 or Phase 9

## Self-Check: PASSED

- [x] scripts/phase03_timeline/01_populate_draft1_vendas.py - FOUND
- [x] scripts/phase03_timeline/02_expand_carteira_formulas.py - FOUND
- [x] data/output/phase03/draft1_population_report.json - FOUND
- [x] data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx - FOUND
- [x] .planning/phases/03-timeline-mensal/03-01-SUMMARY.md - FOUND
- [x] Commit d0906a3 (Task 1) - FOUND
- [x] Commit c065bca (Task 2) - FOUND

---
*Phase: 03-timeline-mensal*
*Completed: 2026-02-17*
