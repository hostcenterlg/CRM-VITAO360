---
phase: 09-blueprint-v2
plan: 01
subsystem: excel-audit
tags: [openpyxl, json, formula-audit, column-spec, v12-carteira]

# Dependency graph
requires:
  - phase: 01-projecao
    provides: "V13 PROJECAO tab with 534 clients, 19,224 formulas"
  - phase: 02-faturamento
    provides: "SAP+Mercos merged data, sap_mercos_merged.json"
  - phase: 06-e-commerce
    provides: "E-commerce matched data, ecommerce_matched.json"
provides:
  - "carteira_column_spec.json: 263-column specification with grouping, formula patterns, header text"
  - "v12_formula_audit.json: 7 formula pattern types classified with templates"
  - "tab_name_map.json: V12->V13 tab name mapping (DRAFT 1, DRAFT 2, REGRAS all need creation)"
  - "draft1_column_map.json: V12->V13 DRAFT 1 column position map (0 mismatches)"
affects: [09-02, 09-03, 09-04, 09-05, 09-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Super-group detection via emoji-prefixed R1 headers in V12"
    - "Formula classification: 7 pattern types (static_data, index_match_draft1, index_match_draft2_cse, countifs_draft2, index_match_regras, internal_calc, let_function)"
    - "Known column ranges for super-group assignment (not R1 propagation)"

key-files:
  created:
    - "scripts/phase09_blueprint_v2/01_audit_v12_carteira.py"
    - "scripts/phase09_blueprint_v2/02_validate_draft1_map.py"
    - "data/output/phase09/carteira_column_spec.json"
    - "data/output/phase09/v12_formula_audit.json"
    - "data/output/phase09/tab_name_map.json"
    - "data/output/phase09/draft1_column_map.json"
  modified: []

key-decisions:
  - "V12 R1 headers use emoji prefixes -- super-groups detected by known column ranges, not R1 text matching"
  - "DRAFT 1 columns at identical positions in V12 and V13 -- no remapping needed for formula injection"
  - "META columns are static in V12 (not formulas referencing PROJECAO) -- V13 needs META MES = PROJECAO col L / 12"
  - "1 _xlfn.LET formula (SINALEIRO at col BJ) must be rewritten as nested IF for compatibility"
  - "All 3 tabs referenced by CARTEIRA formulas (DRAFT 1, DRAFT 2, REGRAS) must be created in V13"
  - "FATURAMENTO has 186 columns (12 months x 15 sub-cols + 2 anchors BZ/CA)"
  - "149 of 263 columns are static data (no formula), 114 have formulas"

patterns-established:
  - "Formula template with {row} placeholder for row-parameterized generation"
  - "JSON-driven CARTEIRA construction: column_spec drives Plans 03-06"

# Metrics
duration: 16min
completed: 2026-02-17
---

# Phase 9 Plan 01: V12 CARTEIRA Audit Summary

**Deep audit of V12 CARTEIRA: 263 columns cataloged across 6 super-groups with 7 formula pattern types, 3-level grouping, and complete DRAFT 1 column position map confirming zero mismatches between V12 and V13**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-17T20:15:22Z
- **Completed:** 2026-02-17T20:32:02Z
- **Tasks:** 2
- **Files created:** 6

## Accomplishments

- Complete 263-column specification with super-group, sub-group, outline level, width, hidden state, formula pattern, and template for every column
- 7 distinct formula pattern types classified: static_data (149), index_match_draft1 (35), countifs_draft2 (48), index_match_draft2_cse (10), internal_calc (19), index_match_regras (1), let_function (1)
- V12-to-V13 DRAFT 1 column map with 36 referenced columns all at identical positions (zero remapping needed)
- Tab name map identifying DRAFT 1, DRAFT 2, and REGRAS as tabs that must be created in V13
- FATURAMENTO 186-column structure validated (12 months x 15 sub-columns)
- _xlfn.LET formula (SINALEIRO) flagged for rewrite in Plans 03-05

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract complete V12 CARTEIRA column specification and formula patterns** - `3529ac2` (feat)
2. **Task 2: Validate audit completeness and generate V12-to-V13 column position map** - `471e2e9` (feat)

## Files Created

- `scripts/phase09_blueprint_v2/01_audit_v12_carteira.py` - Main audit script: reads V12 CARTEIRA, extracts 263 column specs, classifies formulas, builds tab name map
- `scripts/phase09_blueprint_v2/02_validate_draft1_map.py` - Validation script: DRAFT 1 column position map, FATURAMENTO count, anchor verification
- `data/output/phase09/carteira_column_spec.json` - 263-column specification (201 KB) with all headers, grouping, formulas
- `data/output/phase09/v12_formula_audit.json` - Formula audit (38 KB) with 7 pattern types and examples
- `data/output/phase09/tab_name_map.json` - V12->V13 tab name mapping for formula rewriting
- `data/output/phase09/draft1_column_map.json` - DRAFT 1 column position map (14 KB) with 36 referenced columns

## Decisions Made

1. **Super-group detection via known column ranges:** V12 R1 headers use emoji prefixes ("🟣 MERCOS", "🔵 FUNIL", etc.) and also contain month names, Q1-Q4, "100%", and SUBTOTAL formulas in the FATURAMENTO section. Instead of trying to parse these, super-groups are assigned by known column ranges confirmed during audit.

2. **DRAFT 1 columns need no remapping:** All 36 DRAFT 1 columns referenced by CARTEIRA formulas are at the same position in both V12 and V13 standalone DRAFT 1 file. Formula injection in Plans 03-05 can use V12 column letters directly.

3. **META columns are static in V12:** The PROJECAO tab is NOT referenced by any CARTEIRA formula in sample rows. V12 appears to have static META values. For V13, formulas should reference PROJECAO col L / 12 for monthly META.

4. **Single _xlfn.LET formula:** Only the SINALEIRO column (BJ) uses `_xlfn.LET`. This must be rewritten as nested IF for Excel compatibility.

5. **3 tabs must be created in V13:** DRAFT 1, DRAFT 2, and REGRAS are all absent from V13 and must be created in Plan 02 before CARTEIRA formulas can reference them.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Super-group detection failed with emoji-prefixed R1 headers**
- **Found during:** Task 1 (column specification extraction)
- **Issue:** Initial super-group detection logic matched R1 values against known names like "SAP", but actual values are "🟣 MERCOS", "🔵 FUNIL", "🚦 STATUS SAP", etc. Only "SAP " matched (1 of 6).
- **Fix:** Replaced text-matching approach with known column range definitions confirmed by examining all non-None R1 values in the V12 CARTEIRA.
- **Files modified:** scripts/phase09_blueprint_v2/01_audit_v12_carteira.py
- **Verification:** Re-run produced 6 super-groups: MERCOS(43), FUNIL(19), SAP(3), STATUS SAP(3), DADOS CADASTRAIS SAP(9), FATURAMENTO(186)
- **Committed in:** 3529ac2 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for correct super-group identification. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviation above.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 09-02 (Supporting Tabs):** Ready to create REGRAS, DRAFT 1, and DRAFT 2 tabs in V13. All required data is in the audit artifacts.
- **Plans 09-03 through 09-05 (CARTEIRA Construction):** Column spec JSON drives skeleton builder and formula injection. Formula templates with {row} placeholders are ready for parameterized generation.
- **Key data for Plan 02:** tab_name_map.json confirms all 3 tabs need creation. draft1_column_map.json confirms V12 column positions can be reused directly.

### V12 CARTEIRA Structure Summary (for downstream plans)

| Super-Group | Cols | Formula Cols | Static Cols | Key Pattern |
|---|---|---|---|---|
| MERCOS (A-AQ) | 43 | 35 | 8 | index_match_draft1 |
| FUNIL (AR-BJ) | 19 | 11 | 8 | index_match_draft2_cse |
| SAP (BK-BM) | 3 | 0 | 3 | static_data |
| STATUS SAP (BN-BP) | 3 | 0 | 3 | static_data |
| DADOS CAD. SAP (BQ-BY) | 9 | 0 | 9 | static_data |
| FATURAMENTO (BZ-JC) | 186 | 68 | 118 | countifs_draft2, internal_calc |

---
*Phase: 09-blueprint-v2*
*Completed: 2026-02-17*
