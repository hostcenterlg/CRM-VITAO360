---
phase: 11-import-pipeline
plan: 01
subsystem: data-pipeline
tags: [openpyxl, pandas, cnpj, depara, import, excel, dataframe]

# Dependency graph
requires:
  - phase: 10-validacao-final
    provides: Planilha FINAL validada (40 abas, 210K+ formulas, 6.2 MB)
provides:
  - Modulo scripts/motor/ com config, helpers e import pipeline
  - normalizar_cnpj() — string 14 digitos zero-padded
  - normalizar_vendedor() — DE-PARA 5 grupos canonicos
  - importar_planilha() — le xlsx FINAL e retorna 18 DataFrames nomeados
affects: [12-motor-regras, 13-score-sinaleiro, 14-agenda-inteligente, 15-projecao-export]

# Tech tracking
tech-stack:
  added: [openpyxl (data_only+read_only), pandas DataFrames]
  patterns: [lazy module imports via __getattr__, tab-specific header detection, NaN-to-None CNPJ safety]

key-files:
  created:
    - scripts/motor/__init__.py
    - scripts/motor/config.py
    - scripts/motor/helpers.py
    - scripts/motor/import_pipeline.py
  modified: []

key-decisions:
  - "Tab names use exact radiografia values including accents (PROJECAO) and trailing spaces (DRAFT 3 )"
  - "Header rows vary per tab: CARTEIRA row 3, OPERACIONAL row 2, SINALEIRO row 4, MOTOR row 4"
  - "CNPJ normalization converts NaN back to None explicitly to prevent float leakage in pandas"
  - "DESCONHECIDO is the fallback for unmapped vendors (HELDER BRUNKOW=41); LEGADO is for known departed staff"
  - "DRAFT 2 and RNC return 0 data rows with data_only=True (formulas not cached) — expected behavior"

patterns-established:
  - "Tab header config dict: _HEADER_CONFIG maps sheet name to (header_row, data_start_row)"
  - "CNPJ normalization: re.sub(r'\\D', '', str(val)).zfill(14) -> always string 14 digits"
  - "Lazy imports via __getattr__ in __init__.py for forward-compatible module structure"

requirements-completed: [IMPORT-01, IMPORT-02]

# Metrics
duration: 8min
completed: 2026-03-23
---

# Phase 11 Plan 01: Config + Helpers + Import Pipeline Summary

**Modulo scripts/motor/ com importacao openpyxl data_only da planilha FINAL (40 abas) retornando 18 DataFrames com 1581 clientes CARTEIRA, CNPJs 14-digit string e vendedores DE-PARA canonicalizados em ~7s**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-23T23:29:57Z
- **Completed:** 2026-03-23T23:38:23Z
- **Tasks:** 2
- **Files created:** 4

## Accomplishments

- Modulo scripts/motor/ completo com 4 arquivos: __init__.py, config.py, helpers.py, import_pipeline.py
- Pipeline le planilha FINAL (6.2 MB, 40 abas) em ~7 segundos, retornando 18 DataFrames nomeados
- Todos os 1581 CNPJs da CARTEIRA normalizados como string 14 digitos (0 floats, 0 duplicatas)
- 4 consultores ativos identificados via DE-PARA: DAIANE=1116, LARISSA=157, MANU=151, JULIO=91
- 92 combinacoes do MOTOR DE REGRAS importadas corretamente

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar scripts/motor/ com config.py e helpers.py** - `864e28f` (feat)
2. **Task 2: Criar import_pipeline.py que le xlsx FINAL e retorna DataFrames** - `55f43c3` (feat)

## Files Created/Modified

- `scripts/motor/__init__.py` - Pacote motor v2.0 com lazy imports e exports publicos
- `scripts/motor/config.py` - Constantes: CAMINHO_PLANILHA, DE_PARA_VENDEDORES (5 grupos), ABAS_RELEVANTES (14 tabs), ABAS_CONSULTOR (4), thresholds
- `scripts/motor/helpers.py` - normalizar_cnpj (14-digit string), normalizar_vendedor (DE-PARA), safe_read_sheet
- `scripts/motor/import_pipeline.py` - importar_planilha() com tab-specific header detection, CNPJ normalization, vendedor canonicalization

## DataFrames Retornados (18/18)

| DataFrame | Rows | Cols | CNPJ? | Notas |
|-----------|------|------|-------|-------|
| carteira | 1581 | 146 | Sim + consultor_normalizado | Header row 3 |
| operacional | 661 | 24 | Sim (2 nulos "SEM CNPJ") | Header row 2 |
| projecao | 659 | 81 | Sim | Header row 3 |
| resumo_meta | 10 | 17 | Nao | Header row 2 |
| sinaleiro | 661 | 27 | Sim (2 nulos) | Header row 4 |
| draft1 | 563 | 61 | Sim | Header row 3 |
| draft2 | 0 | 41 | - | Dados = formulas nao cached |
| draft3 | 1540 | 19 | Sim (1 nulo) | Header row 2 |
| motor_regras | 92 | 12 | Nao | 92 combinacoes SITUACAO x RESULTADO |
| regras | 465 | 13 | Nao | Dropdowns e tabelas de referencia |
| venda_mes | 569 | 72 | Sim (55 nulos) | Venda mes a mes SAP |
| agenda | 493 | 18 | Nao | Agenda marco 2026 |
| painel_sinaleiro | 48 | 14 | Nao | Painel comercial |
| rnc | 0 | 16 | - | Dados = formulas nao cached |
| consultor_larissa | 157 | 41 | Sim | LOG atendimentos |
| consultor_manu | 151 | 41 | Sim | LOG atendimentos |
| consultor_julio | 91 | 41 | Sim | LOG atendimentos |
| consultor_daiane | 76 | 41 | Sim | LOG atendimentos |

## Decisions Made

1. **Tab names exatos da radiografia** — Usamos os nomes EXATOS incluindo acentos (PROJECAO com cedilha e til) e espacos trailing (DRAFT 3 , PAINEL SINALEIRO ) para evitar KeyError
2. **Header rows variam por aba** — Criamos _HEADER_CONFIG dict que mapeia cada aba para (header_row, data_start_row), detectado via inspecao manual dos dados reais
3. **NaN -> None explicito** — Pandas converte None para NaN (float) em colunas object; adicionamos conversao explicita `.where().` + None para garantir que cnpj_normalizado NUNCA tem float
4. **HELDER BRUNKOW -> DESCONHECIDO** — 41 clientes tem vendedor "HELDER BRUNKOW" nao mapeado no DE-PARA; classificado como DESCONHECIDO (nao LEGADO, que eh para vendedores CONHECIDOS que sairam)
5. **DRAFT 2 e RNC vazios** — Ambas retornam 0 rows porque os dados sao formula-driven e data_only=True mostra valores cached (que nao existem). Esperado e documentado.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed float NaN in cnpj_normalizado column**
- **Found during:** Task 2 (import_pipeline.py verification)
- **Issue:** normalizar_cnpj retorna None para valores como "SEM CNPJ", mas pandas converte None -> NaN (float), fazendo 2 CNPJs no OPERACIONAL passarem como isinstance(float)
- **Fix:** Adicionado `.astype(object)` + `.where(notna(), None)` apos apply para garantir que None permanece None
- **Files modified:** scripts/motor/import_pipeline.py
- **Verification:** Re-run verificou 0 floats em todas as 18 abas
- **Committed in:** 55f43c3 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Fix essencial para garantir R2 (CNPJ NUNCA float). Sem scope creep.

## Issues Encountered

- OPERACIONAL header na row 2 (row 1 vazia) — detectado via inspecao e configurado em _HEADER_CONFIG
- SINALEIRO header na row 4 (rows 1-3 sao titulo/resumo/grupo) — idem
- MOTOR DE REGRAS header na row 4 — idem
- Nenhum destes causou falha; foram resolvidos durante implementacao

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Pronto para 11-02-PLAN.md**: Classificacao 3-tier, unificacao de base, export JSON
- **Pronto para fase 12**: Motor de Regras tem 92 rows importadas, prontas para processamento Python
- **Nota**: DRAFT 2 e RNC retornam 0 rows com data_only=True. Se dados forem necessarios, considerar leitura sem data_only (formula text) ou re-salvar no Excel antes de importar.

## Self-Check: PASSED

All 4 created files verified on disk. Both commits (864e28f, 55f43c3) found in git log. SUMMARY.md created at expected path.

---
*Phase: 11-import-pipeline*
*Completed: 2026-03-23*
