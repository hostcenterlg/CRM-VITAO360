---
phase: 07-redes-franquias
plan: 02
subsystem: data-enrichment
tags: [openpyxl, sumifs, countifs, sinaleiro, rede-franquia, sap, dynamic-formulas]

# Dependency graph
requires:
  - phase: 01-projecao
    provides: "V13 PROJECAO with 19,224 formulas, 537 clients, col C=rede, col Z=REALIZADO"
  - phase: 07-redes-franquias
    plan: 01
    provides: "20 redes + SEM GRUPO in AS:AZ, 11 clients remapped, VLOOKUPs updated"
provides:
  - "REDES_FRANQUIAS_v2 tab with 280 dynamic formulas (SUMIFS, COUNTIFS, IFERROR, IF, RANK)"
  - "META 6M from SAP Faturamento for all 20 redes (CIA DA SAUDE R$351k, FITLAND R$283.5k, etc.)"
  - "TOTAL LOJAS from SAP Leads for 19 redes (MINHA QUITANDINHA has 0)"
  - "Sinaleiro de penetracao: FAT.REAL/FAT.POTENCIAL with COR/MATURIDADE/ACAO derivations"
  - "PARAMETROS editable area (benchmark R$525, meses 11, color thresholds)"
  - "GAP = META_6M - FAT.REAL with RANK-based priority per rede"
affects: [07-03, 09-carteira]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dynamic SUMIFS/COUNTIFS formulas referencing PROJECAO with quoted sheet name ('PROJECAO '!)"
    - "PARAMETROS area for user-editable constants ($W$4, $W$5) referenced by formulas"
    - "Nested IF for categorical derivation: COR->MATURIDADE->ACAO RECOMENDADA"
    - "META 6M extraction: filter Faturamento '01. TOTAL' rows, sum cols JAN-JUN per rede"

key-files:
  created:
    - "scripts/phase07_redes_franquias/02_create_redes_tab.py"
  modified:
    - "data/output/CRM_VITAO360_V13_PROJECAO.xlsx"

key-decisions:
  - "21 data rows (20 redes + SEM GRUPO) instead of plan's 20 (19 + SEM GRUPO) -- MINHA QUITANDINHA is 20th rede from 07-01"
  - "TOTAL row at row 25 (not 24) due to 21 data rows"
  - "RANK formula uses $Q$4:$Q$24 covering all 21 data rows"
  - "SEM GRUPO META 6M included (R$1,029,000 aggregated from SAP) but TOTAL LOJAS=0 (no SAP Leads entry)"
  - "Redes sorted by META 6M descending (not FAT.REAL) for business priority visibility"
  - "MINHA QUITANDINHA: 0 lojas, 0 meta, but retained for completeness (1 active client from 07-01 remap)"

patterns-established:
  - "REDES_FRANQUIAS_v2 formula pattern: =SUMIFS('PROJECAO '!Z$4:Z$537,'PROJECAO '!C$4:C$537,A{row})"
  - "Sinaleiro calculation chain: FAT.REAL/FAT.POTENCIAL -> COR -> MATURIDADE -> ACAO RECOMENDADA"
  - "PARAMETROS reference: FAT.POTENCIAL = C{row}*$W$4*$W$5 (lojas*benchmark*meses)"

# Metrics
duration: 5min
completed: 2026-02-17
---

# Phase 07 Plan 02: Create REDES_FRANQUIAS_v2 Tab Summary

**REDES_FRANQUIAS_v2 tab created with 280 dynamic SUMIFS/COUNTIFS formulas, 21 redes with SAP META 6M (R$1.14M total for named redes), sinaleiro de penetracao chain, and PARAMETROS-driven FAT.POTENCIAL calculation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-17T15:16:55Z
- **Completed:** 2026-02-17T15:22:28Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- REDES_FRANQUIAS_v2 tab created in V13 with 20 columns (A:T) and 21 data rows (20 redes + SEM GRUPO)
- 280 dynamic formulas: 13 per rede (SUMIFS, COUNTIFS, IFERROR, IF, MAX, RANK) + 7 TOTAL row formulas
- META 6M populated from SAP Faturamento: CIA DA SAUDE R$351,000, FITLAND R$283,500, DIVINA TERRA R$157,500, VIDA LEVE R$154,500, and 16 more redes
- TOTAL LOJAS from SAP Leads for 19 redes (MINHA QUITANDINHA has 0, SEM GRUPO has 0)
- Sinaleiro de penetracao chain: FAT.REAL/FAT.POTENCIAL -> COR (ROXO/VERMELHO/AMARELO/VERDE) -> MATURIDADE -> ACAO RECOMENDADA
- PARAMETROS area (V3:X10) with editable benchmark R$525/mes/loja and 11 meses
- GAP = META_6M - FAT.REAL with RANK-based priority (bigger gap = higher priority)
- Zero #REF! errors confirmed (in-memory + independent reload validation)
- 19,224 PROJECAO formulas preserved intact

## Task Commits

Each task was committed atomically:

1. **Task 1: Create REDES_FRANQUIAS_v2 tab with dynamic formulas and META 6M** - `79ea382` (feat)

## Files Created/Modified

- `scripts/phase07_redes_franquias/02_create_redes_tab.py` - Script to create REDES_FRANQUIAS_v2 tab (345 lines), extracts SAP data, builds formulas, validates results
- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - V13 with new REDES_FRANQUIAS_v2 tab (4 tabs total: PROJECAO, LOG, DASH, REDES_FRANQUIAS_v2)

## Decisions Made

1. **21 data rows instead of 20:** Plan specified 19 redes + SEM GRUPO = 20 rows (4-23), but 07-01 already established 20 redes (including MINHA QUITANDINHA). Result: 20 redes + SEM GRUPO = 21 data rows (4-24), TOTAL at row 25.

2. **Redes sorted by META 6M descending:** Plan said "sorted by meta 6M descendente" which surfaces business priority better than FAT.REAL sorting (which was used in 07-01 AS:AZ).

3. **SEM GRUPO META 6M = R$1,029,000:** SAP Faturamento has many "06 - SEM GRUPO" entries with individual metas. Aggregated total is R$1,029,000 but TOTAL LOJAS is 0 (no Leads data for SEM GRUPO).

4. **SAP Faturamento extraction:** Filtered "01. TOTAL" in Grupo Produto (col 12), aggregated JAN-JUN (cols 14-19) per grupo chave. 80 total rows, 20 unique grupos after normalization.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed RANK formula range to cover all 21 data rows**
- **Found during:** Task 1 (after initial script run)
- **Issue:** RANK formula initially used hardcoded $Q$4:$Q$23 (plan assumed 20 rows), but actual data has 21 rows (4-24)
- **Fix:** Changed to dynamic calculation: `last_data_row = 3 + len(rede_list)` resulting in $Q$4:$Q$24
- **Files modified:** scripts/phase07_redes_franquias/02_create_redes_tab.py
- **Verification:** Re-ran script, validated RANK formula covers all data rows
- **Committed in:** 79ea382

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix -- without it, SEM GRUPO (row 24) would be excluded from RANK calculation.

## Issues Encountered

- **MINHA QUITANDINHA absent from SAP Leads:** Has 0 TOTAL LOJAS in Leads tab, meaning FAT.POTENCIAL = 0 and SINALEIRO% = IFERROR(x/0,0) = 0. This is correct behavior -- the rede exists only because of 1 remapped client.
- **SAP Faturamento has 80 "01. TOTAL" rows:** 19 redes (1 each) + 61 SEM GRUPO entries (one per microregion). Correctly aggregated by normalize_rede_name.

## User Setup Required

None - no external service configuration required.

## Rede META 6M Summary

| Rede | META 6M (R$) | TOTAL LOJAS |
|------|-------------|-------------|
| CIA DA SAUDE | 351,000 | 150 |
| FITLAND | 283,500 | 80 |
| DIVINA TERRA | 157,500 | 76 |
| VIDA LEVE | 154,500 | 77 |
| BIO MUNDO | 42,000 | 136 |
| TUDO EM GRAOS | 31,500 | 27 |
| MUNDO VERDE | 21,000 | 171 |
| NATURVIDA | 18,000 | 3 |
| ESMERALDA | 18,000 | 7 |
| ARMAZEM FIT STORE | 18,000 | 5 |
| MAIS NATURAL | 10,500 | 5 |
| JARDIM DAS ERVAS | 10,500 | 22 |
| LIGEIRINHO | 9,000 | 4 |
| TRIP | 9,000 | 2 |
| MERCOCENTRO | 9,000 | 4 |
| NOVA GERACAO | 0 | 13 |
| MIX VALI | 0 | 12 |
| PROSAUDE | 0 | 1 |
| FEDERZONI | 0 | 4 |
| MINHA QUITANDINHA | 0 | 0 |
| **SEM GRUPO** | **1,029,000** | **0** |

## Next Phase Readiness

- REDES_FRANQUIAS_v2 tab ready for 07-03 (formatting, conditional formatting manual, final validation)
- All formulas are dynamic -- opening in Excel will auto-calculate FAT.REAL, ATIVOS, SINALEIRO%, COR, etc.
- Columns E (INAT.REC), F (INAT.ANT), I (N.PEDIDOS) are placeholder zeros -- Phase 9 will populate
- SEM GRUPO has META 6M but no TOTAL LOJAS, so FAT.POTENCIAL will be 0

## Self-Check: PASSED

- FOUND: scripts/phase07_redes_franquias/02_create_redes_tab.py
- FOUND: data/output/CRM_VITAO360_V13_PROJECAO.xlsx
- FOUND: .planning/phases/07-redes-franquias/07-02-SUMMARY.md
- FOUND: commit 79ea382

---
*Phase: 07-redes-franquias*
*Completed: 2026-02-17*
