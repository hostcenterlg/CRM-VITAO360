---
phase: 09-blueprint-v2
plan: 03
subsystem: excel-carteira
tags: [openpyxl, carteira, index-match, cse-array, column-grouping, formula-injection, bounded-ranges]

# Dependency graph
requires:
  - phase: 09-blueprint-v2
    plan: 01
    provides: "carteira_column_spec.json (263 columns), v12_formula_audit.json, draft1_column_map.json"
  - phase: 09-blueprint-v2
    plan: 02
    provides: "V13 with REGRAS, DRAFT 1 (554 clients), DRAFT 2 (6,772 records) tabs"
provides:
  - "V13 CARTEIRA tab: 263 columns, 3-level grouping, 6 super-groups, 554 client rows"
  - "MERCOS block (43 cols): 35 INDEX/MATCH from DRAFT 1 + 1 SUM + 1 IFERROR division"
  - "FUNIL block (19 cols): 10 CSE array from DRAFT 2 + 1 REGRAS motor + 1 nested IF SINALEIRO"
  - "27,146 formulas in MERCOS+FUNIL blocks across 554 rows"
  - "carteira_mercos_funil_validation.json: all 11 checks PASS"
affects: [09-04, 09-05, 09-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bounded range formula injection: $X$3:$X$25000 replaces $X:$X via regex substitution"
    - "JSON-driven CARTEIRA skeleton: column_spec.json drives all 263 column properties"
    - "SINALEIRO nested IF rewrite pattern: _xlfn.LET -> IF(S=0,IF(P<=50,...),IF(P<=S,...))"
    - "TEMPERATURA uses N&AV (SITUACAO & ULTIMO RESULTADO) for REGRAS motor MATCH"

key-files:
  created:
    - "scripts/phase09_blueprint_v2/03_build_carteira_mercos_funil.py"
    - "scripts/phase09_blueprint_v2/04_verify_carteira_mercos_funil.py"
    - "data/output/phase09/carteira_mercos_funil_validation.json"
  modified:
    - "data/output/CRM_VITAO360_V13_PROJECAO.xlsx"

key-decisions:
  - "TEMPERATURA formula uses N&AV (SITUACAO & ULTIMO RESULTADO) instead of V12's N&AQ (SITUACAO & MESES LISTA) for semantic correctness with REGRAS motor"
  - "SINALEIRO uses S (CICLO MEDIO) not AK (TIPO CLIENTE text) as ciclo variable, matching plan's nested IF rewrite"
  - "All V12 formula templates converted to bounded ranges via regex: $COL:$COL -> $COL$3:$COL$25000"
  - "CNPJ and NOME FANTASIA read directly from DRAFT 1 tab in V13 (same row mapping)"

patterns-established:
  - "bounded_ref() utility: regex replacement of full-column refs to bounded ranges"
  - "make_bounded_formula(): template + row number + bounded range conversion pipeline"
  - "CARTEIRA data rows 4-557 aligned with DRAFT 1 rows 4-557 (same client ordering)"

# Metrics
duration: 5min
completed: 2026-02-17
---

# Phase 9 Plan 03: CARTEIRA Skeleton + MERCOS/FUNIL Blocks Summary

**263-column CARTEIRA tab with 3-level grouping, 6 super-groups, and 27,146 INDEX/MATCH + CSE array formulas across MERCOS (43 cols) and FUNIL (19 cols) blocks for 554 clients -- all using bounded ranges, SINALEIRO rewritten without _xlfn.LET**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-17T20:53:05Z
- **Completed:** 2026-02-17T20:58:11Z
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 1

## Accomplishments

- Complete 263-column CARTEIRA tab skeleton with 3 header rows (R1=super-group, R2=sub-group, R3=column name), 210 grouped columns across 3 outline levels, freeze panes at AR6, and auto filter A3:JC557
- MERCOS block (43 columns, A-AQ): 35 INDEX/MATCH formulas from DRAFT 1, 1 SUM (TOTAL PERIODO), 1 IFERROR division (MEDIA MENSAL), 8 static data columns -- all with bounded ranges
- FUNIL block (19 columns, AR-BJ): 10 CSE array formulas from DRAFT 2 (most-recent-record lookup), 1 REGRAS motor lookup (TEMPERATURA), 1 nested IF (SINALEIRO), 1 INDEX/MATCH from DRAFT 1 (TIPO CLIENTE), 6 static data columns
- 27,146 total formulas injected across 554 client rows (rows 4-557)
- SINALEIRO rewritten from `_xlfn.LET(_xlpm.ciclo,AK{r}...)` to nested IF using S (CICLO MEDIO) and P (DIAS SEM COMPRA) -- fully compatible without Excel 365 LET
- All 19,224 PROJECAO formulas verified intact after modification

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CARTEIRA tab skeleton with 263 columns and 3-level grouping + inject formulas** - `05cae6d` (feat)
2. **Task 2: Validate MERCOS + FUNIL block formulas for 554 client rows** - `ad45778` (feat)

## Files Created

- `scripts/phase09_blueprint_v2/03_build_carteira_mercos_funil.py` - Main builder: creates CARTEIRA tab, writes headers/grouping/properties from column_spec.json, injects MERCOS+FUNIL formulas with bounded ranges
- `scripts/phase09_blueprint_v2/04_verify_carteira_mercos_funil.py` - Validation: 11 checks covering formula patterns, bounded ranges, SINALEIRO/TEMPERATURA, PROJECAO integrity
- `data/output/phase09/carteira_mercos_funil_validation.json` - All 11 validation checks PASS

## Files Modified

- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - Now has 9 tabs (was 8, added CARTEIRA)

## Decisions Made

1. **TEMPERATURA uses N&AV instead of V12's N&AQ:** The V12 formula at col BB uses `MATCH(N{r}&AQ{r},...)` where AQ=MESES LISTA (a number). The REGRAS motor matches SITUACAO (text) x RESULTADO (text). Column AV=ULTIMO RESULTADO is the correct semantic match for the motor's column B (RESULTADO). Using AQ would never find a match since numbers don't match result text strings.

2. **SINALEIRO uses S (CICLO MEDIO) not AK (TIPO CLIENTE):** The V12 formula uses `_xlfn.LET(_xlpm.ciclo,AK{r},...)` where AK=TIPO CLIENTE (text like "EM DESENVOLVIMENTO"). The LET variable `ciclo` is used in numeric comparisons (`ciclo=0`, `dias<=ciclo`). Column S=CICLO MEDIO (numeric) is the correct variable for the nested IF rewrite. The plan's nested IF pattern was followed.

3. **Bounded range conversion via regex:** All V12 formula templates use full-column references ($X:$X). A regex-based `bounded_ref()` function converts these to `$X$3:$X$25000` at injection time, preventing 1M-row array scans per Pitfall #4.

4. **CNPJ and NOME FANTASIA from V13 DRAFT 1:** Rather than reading from an external source, client data was read directly from the DRAFT 1 tab already in V13 (created in Plan 02). Same row mapping (rows 4-557) ensures consistency.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - script executed cleanly on first run with all verification checks passing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 09-04 (SAP + FATURAMENTO Blocks):** CARTEIRA skeleton complete with 263 columns ready for SAP static data injection (cols BK-BY, 15 cols) and FATURAMENTO mega-block (cols BZ-JC, 186 cols) formula generation.
- **Formula pipeline validated:** The bounded_ref() + make_bounded_formula() pattern is proven and can be reused for FATURAMENTO's COUNTIFS and internal_calc formulas.
- **Key data for Plan 04:** FATURAMENTO needs META MES = PROJECAO col L / 12, REALIZADO from DRAFT 1 monthly columns, JUSTIFICATIVA S1-S4 COUNTIFS from DRAFT 2.

### Validation Results Summary

| Check | Result | Details |
|-------|--------|---------|
| mercos_spot_check | PASS | 5 rows with INDEX/MATCH to DRAFT 1 |
| funil_spot_check | PASS | 3 rows with CSE array to DRAFT 2 |
| temperatura_regras | PASS | REGRAS!$G$220:$G$282 motor lookup |
| sinaleiro_no_let | PASS | Nested IF, no _xlfn.LET |
| no_full_column_refs | PASS | 0 full-column refs found |
| formula_count_mercos_funil | PASS | 27,146 formulas (>= 25,000) |
| projecao_intact | PASS | 19,224 formulas unchanged |
| column_count_263 | PASS | JC3 has value, JD3 empty |
| cnpj_count | PASS | 554 CNPJs in col B |
| freeze_panes | PASS | AR6 |
| grouped_columns | PASS | 210 columns grouped |

## Self-Check: PASSED

All files verified:
- FOUND: scripts/phase09_blueprint_v2/03_build_carteira_mercos_funil.py
- FOUND: scripts/phase09_blueprint_v2/04_verify_carteira_mercos_funil.py
- FOUND: data/output/phase09/carteira_mercos_funil_validation.json
- FOUND: data/output/CRM_VITAO360_V13_PROJECAO.xlsx
- FOUND: .planning/phases/09-blueprint-v2/09-03-SUMMARY.md

All commits verified:
- FOUND: 05cae6d (Task 1)
- FOUND: ad45778 (Task 2)

---
*Phase: 09-blueprint-v2*
*Completed: 2026-02-17*
