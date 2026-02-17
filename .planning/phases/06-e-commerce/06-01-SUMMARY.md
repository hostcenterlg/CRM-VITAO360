---
phase: 06-e-commerce
plan: 01
subsystem: etl
tags: [openpyxl, mercos, ecommerce, b2b, dedup, header-detection, json]

# Dependency graph
requires:
  - phase: data-sources
    provides: "17 xlsx + 2 xls e-commerce Mercos reports in data/sources/mercos/ecommerce/"
provides:
  - "data/output/phase06/ecommerce_raw.json -- 10 months, 1075 records, normalized by month"
  - "scripts/phase06_ecommerce/01_extract_ecommerce.py -- reusable ETL with header detection"
  - "File inventory with dedup decisions for all 18 source files"
affects: [06-e-commerce, 09-population]

# Tech tracking
tech-stack:
  added: []
  patterns: [dynamic-header-detection, two-level-dedup, trio-conflict-resolution, month-assignment-via-emission-date]

key-files:
  created:
    - scripts/phase06_ecommerce/01_extract_ecommerce.py
    - data/output/phase06/ecommerce_raw.json
  modified: []

key-decisions:
  - "Trio Abril/Maio/junho (identical data) reassigned to April -- data differs from real June file"
  - "Dezembro partial (17 rows) L2-deduped in favor of Dezembro 2025 (101 rows, emitted 15/01/2026)"
  - "Janeiro 2026: rELATORIO (134 rows, emitted 30/01) preferred over Acesso (59 rows, emitted 15/01)"
  - "Fevereiro 2026: fev2026/ file (91 rows, emitted 15/02) preferred over b2b file (43 rows, emitted 06/02)"
  - "October 2025 ABSENT -- no file found in any location"
  - "May 2025 ABSENT -- trio data was only copy, reassigned to April"
  - ".xls files gracefully skipped -- xlrd not available (pip broken), non-blocking per plan"

patterns-established:
  - "Two-level dedup: L1 signature-based (identical files), L2 month-based (same period)"
  - "Trio conflict resolution: when L1 group spans multiple month names and conflicts with real month data"
  - "Header detection: find_header_row + detect_format (9 vs 11 cols) for Mercos reports"

# Metrics
duration: 8min
completed: 2026-02-17
---

# Phase 06 Plan 01: E-commerce ETL Summary

**ETL de 16 .xlsx Mercos e-commerce com header detection dinamica (9/11 colunas), dedup em 2 niveis (5 grupos), e month assignment para 10 meses unicos com 1.075 registros**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-17T12:11:32Z
- **Completed:** 2026-02-17T12:20:09Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Read 16 .xlsx files with dynamic header detection -- both 9-column (OLD) and 11-column (NEW with Email/Telefone) formats handled
- L1 dedup identified 2 groups of identical files: Abril/Maio/junho trio (same data, 77 rows each) and Dezembro pair (same data, 17 rows each)
- L2 dedup resolved 3 same-month conflicts (Dezembro, Janeiro, Fevereiro) always keeping the file with most rows and later emission date
- Trio conflict resolution: reassigned trio data from June to April since real June file exists with different data (126 vs 77 rows)
- 10 unique months extracted (Mar/25 through Feb/26, minus May and October)
- 1,075 total records across 10 months -- within expected 800-1200 range
- Complete file inventory documenting status and dedup decisions for all 18 source files

## Task Commits

Each task was committed atomically:

1. **Task 1: ETL script + JSON output** - `d3d9631` (feat)

## Files Created/Modified
- `scripts/phase06_ecommerce/01_extract_ecommerce.py` - ETL completo: discover, read, dedup L1+L2, month assign, output JSON (380+ lines)
- `data/output/phase06/ecommerce_raw.json` - 440KB JSON with metadata, file_inventory, monthly_data, dedup_report

## Decisions Made

1. **Trio reassignment to April:** The 3 identical files (Abril, Maio, junho with space) contain data that is NOT June data (different from junho.xlsx with 126 rows). Reassigned to April (2025-04) as it is the first available alternate month. This means the trio data could also be May, but April was chosen as the first unclaimed month from the group.

2. **Dezembro partial discarded:** "Acesso ao Ecomerce Dezembro .xlsx" (17 rows) and "Acessos ao Ecomerce Dezembro .xlsx" (17 rows) are identical (L1). Both are L2-deduped in favor of "Acesso ao ecomerce Dezembro 2025.xlsx" (101 rows, emitted 15/01/2026 -- complete month).

3. **January: rELATORIO preferred:** "rELATORIO DE ACESSOS NO ECOMERCE JANEIRO 2026.xlsx" (127 rows, emitted 30/01/2026) preferred over "Acesso ao ecomerce janeiro 2026.xlsx" (59 rows, emitted 15/01/2026). Different data, more complete.

4. **February: fev2026/ preferred:** "acesso ao ecomerce fevereiro 2026.xlsx" (91 rows, emitted 15/02/2026) from fev2026/ preferred over "Acesso ao ecomerce b2b - fevereiro 2026.xlsx" (43 rows, emitted 06/02/2026).

5. **.xls graceful skip:** pip is broken (corrupted distlib module), cannot install xlrd. 2 .xls files skipped without blocking ETL. Plan explicitly allows this.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Trio data lost in dual dedup**
- **Found during:** Task 1 (verification of first run output)
- **Issue:** Trio files (Abril/Maio/junho with space, identical data) were L1-deduped keeping "junho .xlsx", then L2-deduped against "junho.xlsx" (real June data). Result: trio data entirely discarded, losing a unique month of data.
- **Fix:** Added trio conflict resolution: detect when L1 group members claim different months, check if kept file conflicts with another file on same month, and reassign to first available alternate month (April).
- **Files modified:** scripts/phase06_ecommerce/01_extract_ecommerce.py
- **Verification:** Script now produces 10 months with trio data preserved as April
- **Committed in:** d3d9631 (Task 1 commit)

**2. [Rule 1 - Bug] Dezembro L1 group incorrectly caught by trio fix**
- **Found during:** Task 1 (second verification run)
- **Issue:** Initial trio fix applied to ALL L1 groups including the Dezembro pair (same month names). This incorrectly reassigned Dezembro partial to UNKNOWN.
- **Fix:** Added check: only apply trio fix to L1 groups where members claim DIFFERENT months (len(member_months) > 1).
- **Files modified:** scripts/phase06_ecommerce/01_extract_ecommerce.py
- **Verification:** Dezembro pair now correctly handled by L2 dedup only
- **Committed in:** d3d9631 (Task 1 commit)

**3. [Rule 1 - Bug] f-string syntax error with escaped quotes**
- **Found during:** Task 1 (first run attempt)
- **Issue:** f-string containing backslash-escaped quotes in list comprehension caused SyntaxError
- **Fix:** Extracted to helper function `_build_dedup_reason()` to avoid complex f-string escaping
- **Files modified:** scripts/phase06_ecommerce/01_extract_ecommerce.py
- **Committed in:** d3d9631 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (3 Rule 1 bugs)
**Impact on plan:** All auto-fixes necessary for correctness. No scope creep. Key fix was preserving trio data that would otherwise be lost.

## Issues Encountered
- pip is broken (corrupted `pip._vendor.distlib.util` module). Cannot install xlrd. 2 .xls files skipped. This was anticipated in the plan ("NAO falhar se xlrd nao estiver instalado").

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `ecommerce_raw.json` ready for consumption by Plan 06-02 (match + populate)
- 10 months of normalized e-commerce data available for CNPJ matching
- Missing months (May, October) documented -- plan 06-02 should handle gaps gracefully
- File inventory provides full audit trail of dedup decisions
- Note: .xls files may contain additional months (possibly October) -- should attempt xlrd install in future if pip is fixed

## Self-Check: PASSED

- FOUND: scripts/phase06_ecommerce/01_extract_ecommerce.py
- FOUND: data/output/phase06/ecommerce_raw.json
- FOUND: .planning/phases/06-e-commerce/06-01-SUMMARY.md
- FOUND: commit d3d9631

---
*Phase: 06-e-commerce*
*Completed: 2026-02-17*
