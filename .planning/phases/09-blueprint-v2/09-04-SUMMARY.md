---
phase: 09-blueprint-v2
plan: 04
subsystem: excel-carteira
tags: [openpyxl, sap-cadastro, faturamento, countifs, index-match, bounded-ranges, meta-realizado]

# Dependency graph
requires:
  - phase: 09-blueprint-v2
    plan: 01
    provides: "carteira_column_spec.json (263 columns), v12_formula_audit.json with formula patterns"
  - phase: 09-blueprint-v2
    plan: 02
    provides: "V13 with REGRAS, DRAFT 1 (554 clients), DRAFT 2 (6,772 records) tabs"
  - phase: 09-blueprint-v2
    plan: 03
    provides: "V13 CARTEIRA tab with 263-column skeleton, MERCOS+FUNIL 27,146 formulas"
  - phase: 01-projecao
    provides: "V13 PROJECAO with 19,224 formulas, col L = META ANUAL per client"
provides:
  - "V13 CARTEIRA with all 263 columns populated: SAP static data + FATURAMENTO formulas"
  - "SAP block (BK-BP): 518 clients with CODIGO, CNPJ, RAZAO SOCIAL, CADASTRO, ATENDIMENTO, BLOQUEIO"
  - "DADOS CADASTRAIS SAP (BQ-BY): 518 clients with 9 master data fields from SAP Cadastro"
  - "FATURAMENTO mega-block (BZ-JC): 186 columns, 12 months x 15 sub-columns, 554 rows"
  - "130,214 CARTEIRA formulas total, 150,364 V13 total across all tabs"
  - "sap_faturamento_validation.json: all critical checks PASS"
affects: [09-05, 09-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SAP Cadastro static injection by CNPJ match (clean_cnpj strips dots/dashes/slashes)"
    - "FATURAMENTO month-parametric function: write_faturamento_month(ws, month_num, year)"
    - "YTD/TRI cumulative sums via SUM of prior months META MES and REALIZADO MES columns"
    - "JUSTIFICATIVA S4 uses DATE(year,month+1,1) for end-of-month boundary (works for Dec)"
    - "MAXIFS for DATA PEDIDO instead of CSE array (per Research Open Question #5)"

key-files:
  created:
    - "scripts/phase09_blueprint_v2/04_build_carteira_sap_faturamento.py"
    - "scripts/phase09_blueprint_v2/05_verify_sap_faturamento.py"
    - "data/output/phase09/sap_faturamento_validation.json"
  modified:
    - "data/output/CRM_VITAO360_V13_PROJECAO.xlsx"

key-decisions:
  - "SAP blocks use static values (not formulas) since SAP data is relatively static and no dedicated SAP lookup tab in V13"
  - "FATURAMENTO year = 2026 (confirmed by V12 COUNTIFS DATE patterns)"
  - "META MES = PROJECAO col L / 12 (proportional annual meta, per Phase 8 decision)"
  - "REALIZADO MES maps to DRAFT 1 monthly cols: JAN=AE, FEB=AF, MAR=U through DEZ=AD"
  - "% ALCANCADO (CA) references FEB (current month) %MES column"
  - "Quarter anchors use AVERAGE of 3 monthly %MES columns"
  - "11 empty columns (J, N, O, AK, AQ, BA, BC-BG) are user-editable MERCOS/FUNIL static fields -- expected, not Plan 04 scope"

patterns-established:
  - "Month-parametric FATURAMENTO builder: single function handles all 15 sub-columns per month"
  - "YTD = cumulative SUM of all months from JAN to current, TRI = cumulative for quarter months only"
  - "JUSTIFICATIVA weekly date ranges: S1(1-7), S2(8-14), S3(15-21), S4(22-end)"

# Metrics
duration: 7min
completed: 2026-02-17
---

# Phase 9 Plan 04: SAP + FATURAMENTO Blocks Summary

**518 SAP clients populated with static cadastral data + 103,068 FATURAMENTO formulas across 186 columns (12 months x 15 sub-cols) with META/REALIZADO/JUSTIFICATIVA chain referencing PROJECAO, DRAFT 1, and DRAFT 2 -- all bounded ranges, 130,214 total CARTEIRA formulas**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-17T21:04:50Z
- **Completed:** 2026-02-17T21:11:21Z
- **Tasks:** 2
- **Files created:** 3
- **Files modified:** 1

## Accomplishments

- SAP block (BK-BP, 6 columns) populated for 518/554 rows with CODIGO, CNPJ, RAZAO SOCIAL, CADASTRO status, ATENDIMENTO status, and BLOQUEIO from SAP Cadastro source (1,698 unique clients matched by CNPJ)
- DADOS CADASTRAIS SAP (BQ-BY, 9 columns) populated for 518 rows with DESC GRUPO CLIENTE, ZP GERENTE, ZR REPRESENTANTE, ZV VEND INTERNO, CANAL, TIPO CLIENTE, MACROREGIAO, MICROREGIAO, GRUPO CHAVE
- FATURAMENTO mega-block (BZ-JC, 186 columns): 12 months with 15 sub-columns each, all 554 client rows populated with formulas for META MES (PROJECAO col L / 12), REALIZADO MES (DRAFT 1 monthly sales), %MES/%TRI/%YTD percentages, DATA PEDIDO (MAXIFS from DRAFT 2), JUSTIFICATIVA S1-S4 (COUNTIFS weekly ranges from DRAFT 2), and JUSTIFICATIVA MENSAL (SUM S1:S4)
- 130,214 total CARTEIRA formulas (27,146 MERCOS+FUNIL from Plan 03 + 103,068 FATURAMENTO)
- 150,364 total V13 formulas across all 9 tabs (PROJECAO 19,224 intact)
- File size 5.0 MB (well under 25 MB limit)
- Zero full-column references -- all COUNTIFS and INDEX/MATCH use bounded ranges ($X$3:$X$25000)
- 5/5 SAP spot-checks match source data exactly

## Task Commits

Each task was committed atomically:

1. **Task 1: Inject SAP and DADOS CADASTRAIS SAP block + build FATURAMENTO mega-block script** - `d81e0d1` (feat)
2. **Task 2: V13 CARTEIRA complete with all 263 columns + verification** - `24edfc5` (feat)

## Files Created

- `scripts/phase09_blueprint_v2/04_build_carteira_sap_faturamento.py` - Main builder: loads SAP Cadastro, injects static values for 15 SAP columns, generates FATURAMENTO formulas for 186 columns x 554 rows
- `scripts/phase09_blueprint_v2/05_verify_sap_faturamento.py` - Validation: 17 checks covering SAP population, spot-checks, FATURAMENTO structure, formula patterns, bounded ranges, integrity
- `data/output/phase09/sap_faturamento_validation.json` - Full validation results (all critical checks PASS)

## Files Modified

- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - CARTEIRA tab now has all 263 columns populated (SAP static data + FATURAMENTO formulas added to existing MERCOS/FUNIL)

## Decisions Made

1. **SAP blocks use static values:** The plan gave Claude discretion to choose the simplest approach. Since SAP data is relatively static (doesn't change daily) and there's no dedicated SAP lookup tab in V13, static values from SAP Cadastro were injected directly. This avoids unnecessary INDEX/MATCH overhead for data that only changes when SAP master data is updated.

2. **FATURAMENTO year = 2026:** Confirmed by examining V12 COUNTIFS formula templates which use DATE(2026,...) patterns. All 12 months use year 2026.

3. **REALIZADO MES monthly column mapping:** DRAFT 1 has 12 monthly columns from MAR/25 (col U) to FEB/26 (col AF). FATURAMENTO months map as: JAN->AE (JAN/26), FEB->AF (FEB/26), MAR->U (MAR/25), ..., DEZ->AD (DEZ/25). This aligns with the actual Mercos sales data period.

4. **% ALCANCADO = FEB %MES:** Per V12 template `=CX{row}` which points to FEB's %MES column. FEB 2026 is the current operational month.

5. **Quarter anchors use AVERAGE:** Per V12 template `=AVERAGE(CI{row},CX{row},DM{row})` for Q1. Each quarter anchor shows the average %MES of its 3 constituent months.

6. **11 empty columns are expected:** Columns J, N, O, AK, AQ, BA, BC-BG are static user-editable fields from MERCOS/FUNIL blocks (Plan 03 scope). They were also static_data in V12 with no formula template -- they require manual data entry by Leandro.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both tasks executed cleanly on first run with all validation checks passing.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 09-05 (AGENDA tabs):** CARTEIRA now complete with all 263 columns. 4 individual consultant AGENDA tabs can be built using CARTEIRA formulas filtered by consultant name (col L) and date.
- **Plan 09-06 (Final Validation):** All data layers complete. Ready for end-to-end validation of the complete V13 intelligence pipeline.
- **Key formula chain verified:** PROJECAO col L -> META MES (FATURAMENTO) -> %MES -> %TRI -> %YTD -> % ALCANCADO. DRAFT 1 monthly sales -> REALIZADO MES. DRAFT 2 atendimentos -> JUSTIFICATIVA S1-S4.

### Validation Results Summary

| Check | Result | Details |
|-------|--------|---------|
| sap_block_populated | PASS | 518/554 rows with SAP CODIGO |
| dados_cadastrais_populated | PASS | 518/554 rows with DESC GRUPO CLIENTE |
| sap_spot_check | PASS | 5/5 CNPJs match SAP source |
| no_ref_errors_sap | PASS | 0 #REF! errors |
| faturamento_span | PASS | BZ3=VENDA, JC3=JUSTIFICATIVA MENSAL |
| month_15_subcols | PASS | All 12 months have 15 sub-columns |
| jan_meta_projecao | PASS | References PROJECAO col L / 12 |
| jan_real_draft1 | PASS | References DRAFT 1 col AE |
| jan_just_s1 | PASS | COUNTIFS with DATE(2026,1,1) to DATE(2026,1,7) |
| dez_month12 | PASS | Uses DATE(2026,12,...) dates |
| quarter_anchors | PASS | All 4 (%Q1-%Q4) have AVERAGE formulas |
| pct_alcancado | PASS | References FEB %MES |
| carteira_formula_count | PASS | 130,214 formulas (>= 100,000) |
| projecao_intact | PASS | 19,224 formulas unchanged |
| file_size | PASS | 5.0 MB (< 25 MB) |
| bounded_ranges | PASS | 0 full-column references |
| all_263_populated | NOTE | 11 empty cols are MERCOS/FUNIL user-editable (expected) |

## Self-Check: PASSED

All files verified:
- FOUND: scripts/phase09_blueprint_v2/04_build_carteira_sap_faturamento.py
- FOUND: scripts/phase09_blueprint_v2/05_verify_sap_faturamento.py
- FOUND: data/output/phase09/sap_faturamento_validation.json
- FOUND: data/output/CRM_VITAO360_V13_PROJECAO.xlsx
- FOUND: .planning/phases/09-blueprint-v2/09-04-SUMMARY.md

All commits verified:
- FOUND: d81e0d1 (Task 1)
- FOUND: 24edfc5 (Task 2)

---
*Phase: 09-blueprint-v2*
*Completed: 2026-02-17*
