---
phase: 04-log-completo
plan: 01
subsystem: data-etl
tags: [python, openpyxl, etl, classification, cnpj, dedup, json]

# Dependency graph
requires:
  - phase: 03-timeline-mensal
    provides: "V13 with PROJECAO formulas intact and CARTEIRA 554 rows populated"
provides:
  - "_helpers.py: shared module with 8 functions for all Phase 04 plans"
  - "controle_funil_classified.json: 10,442 records (9,120 REAL + 1,322 SINTETICO) in 20-col LOG format"
  - "Consultant normalization pipeline (Julio Gadret, Daiane Stavicki canonical forms)"
  - "RESULTADO normalization map (VENDA->VENDA/PEDIDO, accent stripping for P8)"
affects: [04-02, 04-03, 04-04, 05-dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns: [3-tier-classification, resultado-normalization, p8-accent-stripping, composite-dedup-key]

key-files:
  created:
    - scripts/phase04_log_completo/__init__.py
    - scripts/phase04_log_completo/_helpers.py
    - scripts/phase04_log_completo/01_process_controle_funil.py
    - data/output/phase04/controle_funil_classified.json
  modified: []

key-decisions:
  - "Use 'Interacoes' sheet (pre-classified) instead of raw 4-tab structure; data already extracted and classified"
  - "RESULTADO normalized without accents in LOG (P8 VITAO SEM ACENTO); bidirectional map for motor_de_regras"
  - "10,442 records output (not ~9,986 expected) because alucinacoes were already in separate sheet"
  - "Weekend records (228) kept from source data with warning — not auto-generated, from real CONTROLE_FUNIL"
  - "DAIANE STAVICKI as canonical name (not CENTRAL - DAIANE) matching motor_regras.py"
  - "TIPO DO CONTATO preserved from source when available (real data), motor calculates when missing"

patterns-established:
  - "normalize_resultado(): bidirectional accent mapping for P8 compliance while using accented motor_de_regras"
  - "process_row() pattern: extract -> filter -> normalize -> classify -> make_log_record"
  - "JSON intermediate format with metadata header for pipeline inspection"

# Metrics
duration: 6min
completed: 2026-02-17
---

# Phase 4 Plan 01: CONTROLE_FUNIL ETL Summary

**ETL pipeline processing 10,442 CONTROLE_FUNIL records into 20-col LOG format with 3-tier classification, consultant normalization, and P8 accent stripping**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-17T06:05:29Z
- **Completed:** 2026-02-17T06:11:51Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- _helpers.py shared module with 8 reusable functions for all Phase 04 plans (normalize_cnpj, normalize_consultor, classify_record, make_dedup_key, make_log_record, subtract_business_days, generate_channels, normalize_resultado)
- 10,442 records classified and mapped from 32-col CONTROLE_FUNIL to 20-col LOG format (9,120 REAL + 1,322 SINTETICO)
- Julio Gadret dual spelling (963 + 851 records) merged into single canonical "JULIO GADRET" (1,814 total)
- DAIANE STAVICKI normalized from "CENTRAL - DAIANE" variant (1,319 records)
- Zero financial fields in output (Two-Base Architecture compliance)
- All 10,442 CNPJs validated as 14-digit zero-padded

## Task Commits

Each task was committed atomically:

1. **Task 1: Create _helpers.py shared module** - `1dfd6c2` (feat)
2. **Task 2: ETL CONTROLE_FUNIL to JSON** - `e26f2b1` (feat)

## Files Created/Modified
- `scripts/phase04_log_completo/__init__.py` - Package init for Phase 04 scripts
- `scripts/phase04_log_completo/_helpers.py` - 8 shared functions: normalize_cnpj, normalize_consultor, classify_record, make_dedup_key, make_log_record, subtract_business_days, generate_channels, normalize_resultado
- `scripts/phase04_log_completo/01_process_controle_funil.py` - Full ETL: reads 06_LOG_FUNIL.xlsx, processes Interacoes sheet, maps 32 cols to 20-col LOG, validates, saves JSON
- `data/output/phase04/controle_funil_classified.json` - 10,442 classified records (7.5 MB) ready for merge in Plan 04-04

## Decisions Made
- **Sheet structure deviation:** 06_LOG_FUNIL.xlsx has "Interacoes" (pre-classified clean data) instead of raw "LOG/Manu log/Planilha5/Planilha4" tabs. The extraction was already done in a prior session. Adapted ETL to use pre-classified data.
- **Record count:** 10,442 output (not ~9,986 plan estimate) because 558 alucinacoes were already in separate sheet, not mixed in the 10,544 Interacoes rows. Only 102 discarded (99 null DATA + 3 null RESULTADO).
- **RESULTADO mapping:** Created canonical normalization map — "VENDA" -> "VENDA / PEDIDO", "PERDA / NAO VENDA" -> "PERDA / FECHOU LOJA", "FOLLOW UP" (no number) -> "FOLLOW UP 7", "CLIENTE INATIVO" -> "NAO RESPONDE", "CS" -> "RELACIONAMENTO"
- **P8 accent stripping:** All RESULTADO, FASE, TIPO DO CONTATO, ACAO stored without accents in LOG. Bidirectional map to call motor_de_regras with accented values.
- **Weekend records:** 228 records on weekends kept as-is (source data, not generated). Documented as warning.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted to actual sheet structure**
- **Found during:** Task 2 (ETL development)
- **Issue:** Plan specified 4 tabs (LOG, Manu log, Planilha5, Planilha4) but actual file has "Interacoes" sheet with pre-classified data (ORIGEM_DADO, ABA_ORIGEM, FLAG_ALUCINACAO columns)
- **Fix:** Read "Interacoes" sheet directly, use pre-existing classification, track ABA_ORIGEM for dedup priority
- **Files modified:** scripts/phase04_log_completo/01_process_controle_funil.py
- **Verification:** Output matches expected counts: 10,544 read, 558 alucinacoes in separate sheet, 10,442 in output
- **Committed in:** e26f2b1

**2. [Rule 1 - Bug] Fixed RESULTADO normalization for non-standard values**
- **Found during:** Task 2 (data inspection)
- **Issue:** Source has "VENDA" (not "VENDA / PEDIDO"), "PERDA / NAO VENDA" (not "PERDA / FECHOU LOJA"), "FOLLOW UP" (no number), "CLIENTE INATIVO"
- **Fix:** Created RESULTADO_NORMALIZATION map with all variants mapped to canonical 12 RESULTADO values
- **Files modified:** scripts/phase04_log_completo/01_process_controle_funil.py
- **Verification:** All 10,442 records have valid RESULTADO values matching motor_de_regras expectations
- **Committed in:** e26f2b1

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both deviations were necessary to handle real data structure. No scope creep. Output exceeds plan minimum (10,442 > 9,000).

## Issues Encountered
- 99 rows with null DATA field at end of Interacoes sheet (likely trailing empty rows) — discarded with counter
- 3 rows with null RESULTADO — discarded with counter
- Col 2 header is "_EMPTY_2" (unnamed column in source) — ignored in mapping

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `_helpers.py` ready for import by Plans 04-02 (Deskrio), 04-03 (Synthetic), 04-04 (Dedup/Validate)
- `controle_funil_classified.json` ready for merge in Plan 04-04
- Output JSON includes metadata header with counts for pipeline verification
- Distribution data available for synthetic generation calibration (Plan 04-03):
  - Monthly: Jan 847, Feb 28, Mar 204, ... Oct 2429, Nov 1972, Dec 734
  - Consultors: Manu 3636, Larissa 3086, Julio 1814, Daiane 1319, Helder 528
  - Resultado: EM ATENDIMENTO 4251, SUPORTE 2786, VENDA/PEDIDO 1332, ORCAMENTO 1312

---
*Phase: 04-log-completo*
*Completed: 2026-02-17*
