---
phase: 05-dashboard
plan: 02
subsystem: dashboard
tags: [openpyxl, excel, dash, countifs, kpi, filters, dropdown, formulas]

# Dependency graph
requires:
  - phase: 05-dashboard-01
    provides: "V13 LOG TIPO DO CONTATO normalized to 7 canonical types for COUNTIFS exact-match"
provides:
  - "V13 DASH tab with 3 compact blocks (41 rows, 304 formulas)"
  - "DASH builder script (scripts/phase05_dashboard/02_build_dash.py)"
  - "cf() helper generating IF/OR/COUNTIFS formulas for VENDEDOR filter + date range"
  - "VENDEDOR dropdown (TODOS + 4 consultants) + PERIODO date filter"
  - "6 KPI cards (TOTAL CONTATOS, WHATSAPP, LIGACOES, LIG.ATENDIDAS, ORCAMENTOS, VENDAS)"
affects: [05-dashboard-03]

# Tech tracking
tech-stack:
  added: []
  patterns: ["cf() formula builder with IF/OR VENDEDOR toggle + date range filtering", "3-block compact DASH layout replacing 7-block 164-row original"]

key-files:
  created:
    - "scripts/phase05_dashboard/02_build_dash.py"
  modified:
    - "data/output/CRM_VITAO360_V13_PROJECAO.xlsx"

key-decisions:
  - "6 KPI cards (not 8 from v3_dash.py) -- removed PROSPECCOES and FOLLOW UPS as separate KPIs"
  - "Bloco 2 FOLLOW UP column includes RELACIONAMENTO in sum (fu7 + fu15 + rel)"
  - "Produtividade uses direct COUNTIFS (no cf() helper) since consultant is explicit in cell reference"
  - "Separator columns (H, L, O) width=2 with FILL_SEP + NO_BORDER for visual grouping"
  - "NO ACCENTS in data values -- LOG stores PROSPECCAO, NEGOCIACAO, NAO ATENDE etc."

patterns-established:
  - "cf() helper: IF(OR($C$2=\"\",$C$2=\"TODOS\"),COUNTIFS(date+extra),COUNTIFS(date+consultor+extra))"
  - "DASH formula pattern: bounded ranges LOG!$X$3:$X$21000 (not full-column references)"
  - "Re-runnable DASH builder: deletes existing DASH tab before rebuilding"

# Metrics
duration: 3min
completed: 2026-02-17
---

# Phase 05 Plan 02: Build DASH Tab Summary

**41-row compact DASH with 304 COUNTIFS formulas across 3 blocks (TIPO x RESULTADO, CONTATOS + FUNIL, MOTIVOS + PRODUTIVIDADE) plus 6 KPI cards and VENDEDOR/PERIODO interactive filters**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-17T10:18:15Z
- **Completed:** 2026-02-17T10:21:38Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Built DASH tab in V13 with 3 compact blocks in 41 rows (vs 164-row original 7-block design)
- 304 COUNTIFS formulas all referencing LOG tab columns (A, B, H, I, J, L, M, N, Q)
- VENDEDOR dropdown filter with DataValidation (TODOS + 4 canonical consultants)
- PERIODO date filter with datetime objects and DD/MM/YYYY format
- 6 KPI summary cards (TOTAL CONTATOS, WHATSAPP, LIGACOES, LIG.ATENDIDAS, ORCAMENTOS, VENDAS)
- All formulas use ENGLISH function names: COUNTIFS, IF, OR, SUM, IFERROR
- PROJECAO 19,224 formulas intact after DASH creation (zero formula loss)
- Script is fully re-runnable (deletes existing DASH before rebuilding)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create DASH builder script with cf() helper and filter row** - `9de5513` (feat)

## Files Created/Modified
- `scripts/phase05_dashboard/02_build_dash.py` - DASH tab builder with cf() helper, 3 blocks, KPIs, filters (569 lines)
- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - V13 with DASH tab added (41 rows, 304 formulas)

## DASH Structure

### Layout (41 rows)
| Rows | Content |
|------|---------|
| 1 | Title: "DASHBOARD JARVIS CRM -- VITAO ALIMENTOS" (red background) |
| 2 | Filters: VENDEDOR dropdown (C2) + PERIODO dates (E2:F2) |
| 3-4 | 6 KPI cards (merged cells, blue background) |
| 5 | Spacer |
| 6-15 | Bloco 1: TIPO DO CONTATO x RESULTADO (7 types x 13 result columns) |
| 16 | Spacer |
| 17-27 | Bloco 2: CONTATOS REALIZADOS + FUNIL DE VENDA (channels, funnel, relationship, non-sale) |
| 28 | Spacer |
| 29-41 | Bloco 3: MOTIVOS DE NAO COMPRA (left, 10 motivos) + PRODUTIVIDADE POR CONSULTOR (right, 4 consultants) |

### Formula Architecture
- **cf() helper:** `IF(OR($C$2="",$C$2="TODOS"),COUNTIFS(date+extra),COUNTIFS(date+consultor+extra))`
- **Date filter:** `LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2`
- **Produtividade:** Direct COUNTIFS with explicit consultant name from cell reference (no cf() needed)
- **All ranges bounded:** $X$3:$X$21000 (never full-column $X:$X)

## Decisions Made
- **6 KPI cards (not 8):** Removed PROSPECCOES and FOLLOW UPS KPIs from v3_dash design; kept the 6 most actionable metrics
- **Bloco 2 FOLLOW UP includes RELACIONAMENTO:** Sum of FOLLOW UP 7 + FOLLOW UP 15 + RELACIONAMENTO for complete relationship tracking
- **Produtividade direct COUNTIFS:** Since consultant name comes from cell I{r}, no need for cf() VENDEDOR toggle
- **NO ACCENTS throughout:** All data values match LOG sem-acento convention (PROSPECCAO, NEGOCIACAO, NAO ATENDE, etc.)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - script ran on first attempt with all 304 formulas and 19,224 PROJECAO formulas preserved.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- V13 DASH tab fully functional with 3 blocks + KPI cards + filters
- Ready for Plan 05-03 (styling, charts, final polish if applicable)
- PROJECAO 19,224 formulas intact, safe for continued modifications
- Script re-runnable for iterative refinement

## Self-Check: PASSED

- FOUND: scripts/phase05_dashboard/02_build_dash.py (569 lines, min_lines: 300 satisfied)
- FOUND: data/output/CRM_VITAO360_V13_PROJECAO.xlsx
- FOUND: .planning/phases/05-dashboard/05-02-SUMMARY.md
- FOUND: commit 9de5513 (feat(05-02): build DASH tab with 3 blocks + KPIs + filters in V13)

---
*Phase: 05-dashboard*
*Completed: 2026-02-17*
