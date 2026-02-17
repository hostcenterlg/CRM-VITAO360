---
phase: 07-redes-franquias
plan: 01
subsystem: data-enrichment
tags: [openpyxl, vlookup, sinaleiro, rede-franquia, cnpj-matching, sap]

# Dependency graph
requires:
  - phase: 01-projecao
    provides: "V13 PROJECAO with 19,224 formulas, 534 clients, 12 redes in AS:AZ"
  - phase: 02-faturamento
    provides: "Monthly vendas data in cols AA:AL for FAT.REAL calculation"
provides:
  - "11 SEM GRUPO clients remapped to correct rede via SAP CNPJ match"
  - "AS:AZ reference table expanded from 12 to 20 redes + SEM GRUPO (21 rows)"
  - "VLOOKUPs in F:J updated to reference expanded range ($24)"
  - "Real 2025 sinaleiro data per rede (TOTAL LOJAS, FAT.REAL, SINALEIRO%, COR, MATURIDADE, ACAO, GAP)"
affects: [07-02, 07-03, 09-carteira]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sum AA:AL fallback when col Z formula returns None with data_only=True"
    - "REDE_NORMALIZE map for SAP grupo chave -> V13 rede name normalization"
    - "COR/MATURIDADE/ACAO lookup from sinaleiro percentage thresholds"

key-files:
  created:
    - "scripts/phase07_redes_franquias/01_remap_expand_reftable.py"
  modified:
    - "data/output/CRM_VITAO360_V13_PROJECAO.xlsx"

key-decisions:
  - "20 redes instead of 19: MINHA QUITANDINHA discovered as real rede via SAP CNPJ match (1 client remapped)"
  - "VLOOKUPs reference row $24 (20 redes + SEM GRUPO) instead of planned $22 (19 redes)"
  - "All redes included regardless of FAT.REAL=0 (JARDIM DAS ERVAS, ARMAZEM FIT STORE, etc.)"
  - "SAP Leads TOTAL LOJAS used directly per rede (not aggregated by microregion)"
  - "MINHA QUITANDINHA has 0 TOTAL LOJAS in SAP Leads but 1 client with R$1,928 fat real"

patterns-established:
  - "REDE_NORMALIZE: canonical map from SAP '06 - INTERNA - X' to short rede name"
  - "Sinaleiro thresholds: ROXO 0-1%, VERMELHO 1-40%, AMARELO 40-60%, VERDE 60-100%+"
  - "FAT.POTENCIAL = TOTAL_LOJAS * R$525 * 11 meses"

# Metrics
duration: 69min
completed: 2026-02-17
---

# Phase 07 Plan 01: Remap + Expand Reference Table Summary

**11 SEM GRUPO clients remapped via SAP CNPJ match (7 ESMERALDA, 1 DIVINA TERRA, 1 MERCOCENTRO, 1 MINHA QUITANDINHA, 1 VIDA LEVE) and AS:AZ reference table expanded from 12 to 20 redes + SEM GRUPO with real 2025 sinaleiro data**

## Performance

- **Duration:** 69 min (includes 2x V13 load/save ~5 min each, validation reload)
- **Started:** 2026-02-17T14:02:45Z
- **Completed:** 2026-02-17T15:11:45Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments

- 11 clients remapped from SEM GRUPO to correct rede: 7 ESMERALDA, 1 DIVINA TERRA, 1 MERCOCENTRO, 1 MINHA QUITANDINHA, 1 VIDA LEVE (SEM GRUPO reduced from 405 to 394)
- AS:AZ reference table expanded from 12 to 20 redes + SEM GRUPO (21 data rows), sorted by FAT.REAL descending, with TOTAL LOJAS, SINALEIRO%, COR, MATURIDADE, ACAO, GAP
- 2,670 VLOOKUP formulas in cols F:J updated from `$AS$4:$A?$18` to `$AS$4:$A?$24`
- 19,224 PROJECAO formulas preserved intact
- freeze_panes E30 preserved

## Task Commits

Each task was committed atomically:

1. **Task 1: Remap 11 SEM GRUPO clients + expand AS:AZ reference table** - `e2bcf62` (feat)

## Files Created/Modified

- `scripts/phase07_redes_franquias/01_remap_expand_reftable.py` - Script to remap clients and expand reference table (253 lines)
- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - V13 with corrected col C, expanded AS:AZ, updated VLOOKUPs

## Decisions Made

1. **20 redes instead of 19:** MINHA QUITANDINHA was discovered as a real SAP rede with 1 client remapped to it. Plan listed 19 redes (12 existing + 7 new) but MINHA QUITANDINHA was not in either list. Included all 20 to avoid data loss.

2. **VLOOKUP end row $24 instead of $22:** With 20 redes (rows 4-23) + SEM GRUPO (row 24), the VLOOKUP range ends at row 24. Plan specified row 22 based on 19 redes assumption.

3. **SAP has 18 redes with CNPJ assignments (not 19):** The 19th rede (MIX VALI) exists in SAP Leads but has 0 clients with CNPJ in Cadastro. Still included in reference table from Leads data.

4. **Sum AA:AL for FAT.REAL:** Col Z has `=SUM(AA:AL)` formula, and `data_only=True` returns None (file not opened in Excel). Used direct sum of cols AA:AL (27:38) which have numeric values.

5. **COR with emoji prefix:** Maintained existing pattern of emoji+text for COR column (e.g., "VERMELHO") to match V13 original formatting.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added MINHA QUITANDINHA as 20th rede**
- **Found during:** Task 1 (rede data assembly)
- **Issue:** MINHA QUITANDINHA not in plan's 19-rede list but exists as SAP grupo chave with 1 remapped client
- **Fix:** Expanded KNOWN_REDES to 20, included all redes in reference table, adjusted VLOOKUP end row to $24
- **Files modified:** scripts/phase07_redes_franquias/01_remap_expand_reftable.py, data/output/CRM_VITAO360_V13_PROJECAO.xlsx
- **Verification:** All 20 redes + SEM GRUPO present in AS:AZ, VLOOKUPs reference $24
- **Committed in:** e2bcf62

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for data completeness -- excluding a real rede with an active client would cause VLOOKUP mismatches.

## Issues Encountered

- **Python output buffering:** Initial runs appeared to hang because Python's stdout was buffered. Fixed by using `-u` flag for unbuffered output.
- **openpyxl slow load:** V13 load with `data_only=False` takes ~5 minutes for the 3MB file with 19,224 formulas. Expected behavior.
- **Script idempotency:** Second run correctly remapped 0 clients (already remapped) and still passed all validations.

## User Setup Required

None - no external service configuration required.

## Rede Data Summary

| Rede | Lojas | Fat.Real | Sinaleiro% | COR | Maturidade |
|------|-------|----------|------------|-----|------------|
| FITLAND | 80 | R$ 129,989 | 28.14% | VERMELHO | ATIVACAO/POSITIVACAO |
| VIDA LEVE | 77 | R$ 42,967 | 9.66% | VERMELHO | ATIVACAO/POSITIVACAO |
| CIA DA SAUDE | 150 | R$ 36,384 | 4.20% | VERMELHO | ATIVACAO/POSITIVACAO |
| NATURVIDA | 3 | R$ 26,966 | 155.65% | VERDE | JBP |
| ESMERALDA | 7 | R$ 24,431 | 60.44% | VERDE | JBP |
| DIVINA TERRA | 76 | R$ 24,273 | 5.53% | VERMELHO | ATIVACAO/POSITIVACAO |
| MUNDO VERDE | 171 | R$ 15,019 | 1.52% | VERMELHO | ATIVACAO/POSITIVACAO |
| TRIP | 2 | R$ 13,524 | 117.09% | VERDE | JBP |
| MERCOCENTRO | 4 | R$ 11,928 | 51.64% | AMARELO | SELL OUT |
| BIO MUNDO | 136 | R$ 10,381 | 1.32% | VERMELHO | ATIVACAO/POSITIVACAO |
| TUDO EM GRAOS | 27 | R$ 8,315 | 5.33% | VERMELHO | ATIVACAO/POSITIVACAO |
| MAIS NATURAL | 5 | R$ 7,533 | 26.09% | VERMELHO | ATIVACAO/POSITIVACAO |
| LIGEIRINHO | 4 | R$ 6,201 | 26.85% | VERMELHO | ATIVACAO/POSITIVACAO |
| MINHA QUITANDINHA | 0 | R$ 1,928 | 0.00% | ROXO | PROSPECCAO |
| PROSAUDE | 1 | R$ 953 | 16.52% | VERMELHO | ATIVACAO/POSITIVACAO |
| NOVA GERACAO | 13 | R$ 0 | 0.00% | ROXO | PROSPECCAO |
| MIX VALI | 12 | R$ 0 | 0.00% | ROXO | PROSPECCAO |
| FEDERZONI | 4 | R$ 0 | 0.00% | ROXO | PROSPECCAO |
| JARDIM DAS ERVAS | 22 | R$ 0 | 0.00% | ROXO | PROSPECCAO |
| ARMAZEM FIT STORE | 5 | R$ 0 | 0.00% | ROXO | PROSPECCAO |
| **SEM GRUPO** | **394** | **R$ 1,720,231** | - | ROXO | PROSPECCAO |

## Next Phase Readiness

- AS:AZ reference table with 20 redes + SEM GRUPO ready for Plan 07-02 (REDES_FRANQUIAS_v2 aba creation)
- Client col C corrected for 11 clients, enabling accurate rede aggregation
- Sinaleiro data (COR, MATURIDADE, ACAO) ready for rede dashboard

## Self-Check: PASSED

- FOUND: scripts/phase07_redes_franquias/01_remap_expand_reftable.py
- FOUND: data/output/CRM_VITAO360_V13_PROJECAO.xlsx
- FOUND: .planning/phases/07-redes-franquias/07-01-SUMMARY.md
- FOUND: commit e2bcf62

---
*Phase: 07-redes-franquias*
*Completed: 2026-02-17*
