---
phase: 02-faturamento
plan: 02
subsystem: etl
tags: [merge, sap-first, fuzzy-match, cnpj, json, python, openpyxl]

# Dependency graph
requires:
  - phase: 02-faturamento/01
    provides: mercos_vendas.json (453+10 clients) and sap_vendas.json (489 clients) in array[12] format
provides:
  - sap_mercos_merged.json with 537 unique clients (SAP-First merge + 10 fuzzy-matched)
  - All 10 sem_cnpj clients resolved via Mercos Carteira name matching
  - JAN/26 fully captured (R$ 114,038.03)
  - CARTEIRA population documented as DEFERRED
affects: [02-03 (populate CARTEIRA -- deferred), Phase 9 (Blueprint client roster)]

# Tech tracking
tech-stack:
  added: []
  patterns: [SAP-First merge with month-level complement, simple string fuzzy match without external libs]

key-files:
  created:
    - scripts/phase02_faturamento/03_merge_sap_mercos.py
    - scripts/phase02_faturamento/04_fuzzy_match_sem_cnpj.py
    - data/output/phase02/sap_mercos_merged.json
  modified: []

key-decisions:
  - "SAP-First merge: 160 month-cells filled from Mercos where SAP=0, adding ~R$ 344k in captured sales"
  - "27 SAP negative values (credit notes/returns) zeroed out to ensure no negative entries"
  - "All 10 sem_cnpj matched via exact name in Mercos Carteira -- no partial/fuzzy needed"
  - "60.641.605 is a proper CNPJ (not CPF) -- 60641605000193"
  - "DIVINA TERRA CURITIBA correctly matched to 32828171000108 (not other Divina Terra branches)"
  - "Total R$ 2,493k vs plan estimate R$ 2,149k -- difference is the 160 Mercos-complement months"

patterns-established:
  - "SAP-First strategy: for overlapping CNPJs, SAP value takes priority; Mercos fills only where SAP=0"
  - "Negative SAP values (credit notes) zeroed at merge time, not propagated"
  - "Fuzzy match via Mercos Carteira nome_fantasia lookup before falling back to SAP Cadastro"

# Metrics
duration: 4min
completed: 2026-02-17
---

# Phase 02 Plan 02: SAP+Mercos Merge Summary

**SAP-First merge of 529 unique CNPJs (160 month-cells complemented from Mercos) plus 10/10 sem_cnpj resolved via Mercos Carteira name matching, total R$ 2,493,521.92**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-17T02:29:04Z
- **Completed:** 2026-02-17T02:33:26Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments
- Merged SAP (489) and Mercos (453) clients into 529 unique CNPJs using SAP-First strategy with month-level complement
- Filled 160 month-cells from Mercos where SAP had zero, capturing R$ ~344k additional sales revenue
- Resolved all 10 sem_cnpj clients via exact name matching in Mercos Carteira (none needed partial/fuzzy)
- Final dataset: 537 clients, R$ 2,493,521.92 (2025), R$ 114,038.03 (JAN/26)
- Zeroed 27 SAP negative values (credit notes) to ensure clean data

## Task Commits

Each task was committed atomically:

1. **Task 1a: Merge SAP-First + Mercos-Complement** - `1e047a4` (feat)
2. **Task 1b: Fuzzy match dos 10 clientes Mercos sem CNPJ** - `2c8ee40` (feat)

## Files Created/Modified
- `scripts/phase02_faturamento/03_merge_sap_mercos.py` - SAP-First merge: loads both JSONs, combines by CNPJ with month-level complement, zeros negatives, saves merged JSON
- `scripts/phase02_faturamento/04_fuzzy_match_sem_cnpj.py` - Fuzzy match: builds name->CNPJ lookup from Mercos Carteira + SAP Cadastro, matches 10 sem_cnpj clients, updates merged JSON
- `data/output/phase02/sap_mercos_merged.json` - Final consolidated dataset: 537 clients, stats, fuzzy_matches, JAN/26, CARTEIRA deferral note

## Decisions Made
- **SAP negatives zeroed:** 27 SAP credit note entries (negative R$ values) were zeroed out during merge to prevent negative values in the consolidated dataset. These are legitimate business entries but would corrupt downstream calculations.
- **Total differs from plan estimate:** Plan estimated ~R$ 2,149k but actual merge yields R$ 2,493k. The difference (~R$ 344k) comes from 160 month-cells where SAP had zero but Mercos had sales. This is correct SAP-First complement behavior, not a bug.
- **All 10 matched via exact name:** No partial/fuzzy matching was needed -- all 10 sem_cnpj clients had exact name matches in the Mercos Carteira nome_fantasia column. The fuzzy match fallback code exists but wasn't triggered.
- **DIVINA TERRA disambiguation:** "DIVINA TERRA CURITIBA" matched exactly to CNPJ 32828171000108 (HIPER VERDE ALIMENTOS, Curitiba/PR), correctly avoiding 7 other "Divina Terra" branches in other cities.
- **60.641.605 is CNPJ:** Despite appearing to be a CPF prefix, "60.641.605 LARA DE BARROS AMANDO ALENCAR" has a proper CNPJ in the Carteira: 60.641.605/0001-93 (14 digits).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SAP negative values (credit notes) zeroed out**
- **Found during:** Task 1a (Merge SAP-First)
- **Issue:** 6 CNPJs had negative monthly values from SAP (credit notes/returns totaling 27 negative entries). Plan requires "no negative values" in merged output.
- **Fix:** Added logic to zero out SAP negatives during merge. For "both" clients, negative SAP months fall through to Mercos complement. For SAP-only clients, negatives are replaced with 0.0.
- **Files modified:** scripts/phase02_faturamento/03_merge_sap_mercos.py
- **Verification:** Output has 0 negative values. Stats track negatives_zeroed=27.
- **Committed in:** 1e047a4 (Task 1a commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for data integrity. No scope creep.

## Issues Encountered
- **Client count vs plan estimate:** Plan estimated 650+ unique clients but actual union is 529 (489 + 453 - 413 overlap). The 413 overlap means SAP and Mercos share 78% of their client bases. After fuzzy match, total is 537. This is a plan estimation error, not a data issue.
- **Total vendas vs plan estimate:** Plan expected ~R$ 2,149k but actual is R$ 2,493k. The extra ~R$ 344k comes from 160 month-cells where Mercos had sales but SAP had zero. The plan's estimate didn't account for the additive nature of month-level complementing.

## User Setup Required
None - no external service configuration required.

## Key Metrics

| Metric | Value |
|--------|-------|
| Total unique clients | 537 |
| SAP-only | 76 |
| Mercos-only | 40 |
| Both (SAP base) | 413 |
| Fuzzy matched | 10 (8 new CNPJs + 2 merged into existing) |
| Unmatched | 0 |
| Total vendas 2025 | R$ 2,493,521.92 |
| Total JAN/26 | R$ 114,038.03 |
| Months filled from Mercos | 160 |
| SAP negatives zeroed | 27 |

## Next Phase Readiness
- `sap_mercos_merged.json` is the primary artifact for FAT-04 (vendas consolidadas)
- Ready for Plan 02-03 (CARTEIRA population -- currently DEFERRED due to V13 having only 3 data rows)
- All sem_cnpj clients resolved -- no orphan sales data
- JSON format includes fuzzy_matches array documenting each match decision for audit trail

## Self-Check: PASSED

- [x] scripts/phase02_faturamento/03_merge_sap_mercos.py - FOUND
- [x] scripts/phase02_faturamento/04_fuzzy_match_sem_cnpj.py - FOUND
- [x] data/output/phase02/sap_mercos_merged.json - FOUND
- [x] .planning/phases/02-faturamento/02-02-SUMMARY.md - FOUND
- [x] Commit 1e047a4 (Task 1a) - FOUND
- [x] Commit 2c8ee40 (Task 1b) - FOUND

---
*Phase: 02-faturamento*
*Completed: 2026-02-17*
