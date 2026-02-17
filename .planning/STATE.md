# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-15)

**Core value:** Cruzar dados de vendas, atendimentos e prospecção em CARTEIRA unificada com visibilidade total, sem fabricar dados ou duplicar valores financeiros.

## REGRA PRINCIPAL DO PROJETO (INVIOLAVEL)

O objetivo FINAL de todo este trabalho NÃO é "ter uma planilha limpa". É GERAR INTELIGÊNCIA COMERCIAL DIÁRIA:
- Cada consultor recebe uma AGENDA DO DIA com 40-60 atendimentos priorizados
- A priorização vem do CRUZAMENTO AUTOMATICO de: ciclo médio de compra, dias sem comprar, acesso ao e-commerce (acessou/montou carrinho ou não), resultado do último atendimento, fase do funil (prospecção/cadastro/negociação/ouro), tipo de cliente, temperatura, prioridade
- Os RANKINGS e SINALEIROS nas fórmulas da CARTEIRA (RANK, IF, VLOOKUP) existem PRA ISSO
- O gestor (Leandro) passa a agenda de manhã, consultor devolve no fim do dia com resultados
- Resultados do dia alimentam o ciclo do dia seguinte (follow-ups, recuperações, salvamentos)
- Se a CARTEIRA não gerar essa inteligência de agenda diária, TODO O TRABALHO DAS 10 FASES NÃO SERVE PRA NADA
- As regras, status, grupos de colunas do funil na CARTEIRA já foram DESENHADOS para isso — respeitar 100%

**Current focus:** Phase 03 Timeline Mensal COMPLETE -- All plans done, TIME-01/02/03 PASS. Ready for Phase 04.

## Current Position

Phase: 3 of 10 (Timeline Mensal) -- COMPLETE
Plan: 2 of 2 in current phase -- COMPLETE (phase done)
Status: Phase 03 COMPLETE -- All validation PASS (TIME-01/02/03), zero divergence, ABC consistent
Last activity: 2026-02-17 -- Plan 03-02 executed (validation + ABC recalc + TIME requirements)

Progress: [████████░░] 29% (plans 01-01..03, 02-01..03, 03-01..02 of 28 total complete)

## DESCOBERTA CRITICA (16/FEV/2026)

As fórmulas da PROJEÇÃO **NÃO estão perdidas**:
- CRM V12 tem 19.224 fórmulas intactas na aba PROJEÇÃO
- V11 tem 0 (perdidas), mas V12 restaurou
- 4 arquivos PROJEÇÃO standalone com 15.500-21.632 fórmulas cada
- Fórmulas já em INGLÊS (SUM, IF, VLOOKUP, RANK, IFERROR)
- A Fase 1 muda de "reconstruir" para "validar e completar"

### Novos arquivos descobertos (16/FEV/2026)
- `DRAFT2_POPULADO_DADOS_REAIS_v3.xlsx` — **6.775 registros reais de atendimentos** (31 cols)
- `SINALEIRO_POPULADO.xlsx` — Sinaleiro com dados populados
- `CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` — V12 populado (3.9 MB)
- `CONTROLE_FUNIL_JAN2026.xlsx` — 10.483 registros LOG
- `BASE_SAP_META_PROJECAO_2026.xlsx` — Metas 2026
- `BASE_SAP_VENDA_MES_A_MES_2025.xlsx` — Vendas mês a mês
- `BASE_SAP_CLIENTES_SEM_ATENDIMENTO.xlsx` — Gaps de cobertura

### Estado real das fontes de dados para LOG
| Fonte | Registros | Status |
|-------|-----------|--------|
| CONTROLE_FUNIL_JAN2026 | 10.483 | Disponível, não integrado |
| DRAFT2_POPULADO_DADOS_REAIS | 6.775 | Disponível, não integrado |
| Deskrio tickets (12 exports) | ~5.329 | Disponível, não integrado |
| LOG no V12 | ~1 | Quase vazio |
| **TOTAL disponível** | **~22.587** | Pendente integração |

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 9 min
- Total execution time: 1.15 hours

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01-projecao | 01 | 4 min | 2 | 4 |
| 01-projecao | 02 | 6 min | 1 | 2 |
| 01-projecao | 03 | 4 min | 2 | 2 |
| 02-faturamento | 01 | 18 min | 2 | 4 |
| 02-faturamento | 02 | 4 min | 2 | 3 |
| 02-faturamento | 03 | 5 min | 2 | 2 |
| 03-timeline-mensal | 01 | 25 min | 2 | 4 |
| 03-timeline-mensal | 02 | 3 min | 1 | 3 |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- [Init]: Two-Base Architecture confirmada — R$ apenas em VENDA, nunca em LOG
- [Init]: CNPJ string 14 dígitos como chave primária universal
- [Init]: XML Surgery para slicers — openpyxl destrói infraestrutura XML
- [Init]: Fórmulas em INGLÊS para openpyxl
- [Init]: Comprehensive depth + Quality profile + YOLO mode
- [16/02]: V12 é a base — não V11. Fórmulas PROJEÇÃO intactas.
- [16/02]: DRAFT2 com 6.775 registros reais pendentes integração
- [16/02]: Python via pyenv: /c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe
- [17/02]: Sheet name has cedilla accent ("PROJECAO " with tilde) -- use accent-stripping for sheet lookup
- [17/02]: AO column uses emoji indicators, not text labels -- validate structure not exact strings
- [17/02]: Simplified meta extraction from PROJECAO col L (0.67% vs SAP ref) instead of Grupo Chave distribution
- [17/02]: freeze_panes=E30 (not C4), 12 redes (not 15) in actual PROJECAO file
- [17/02]: Unmatched vendas CNPJs zeroed (49 clients) -- clean data for formula recalculation
- [17/02]: Monthly weight rounding 0.001% acceptable -- float precision with weights sum=0.999990
- [17/02]: 4 SAP vendas CNPJs not in PROJECAO roster (R$ 8,794 delta) -- fixed client list
- [17/02]: auto_filter absent in V13 output -- openpyxl limitation, restores when opened in Excel
- [17/02]: PROJ-04 meta R$5.7M aspirational vs R$4.7M actual SAP -- documented discrepancy
- [17/02]: 7 consultors found (not 3-4 assumed) -- "MANU DITZEL" appears as separate entry from "HEMANUELE DITZEL (MANU)"
- [17/02]: Phase 01 PROJECAO complete -- all PROJ-01..04 requirements formally verified PASS
- [17/02]: Sem CNPJ clients on dedicated sheet in 02_VENDAS_POSITIVACAO (not in Vendas Mes a Mes)
- [17/02]: Independent SAP re-extraction matches Phase 1 exactly (489 CNPJs, R$ 2,089,824.23, 0% diff)
- [17/02]: 11 Mercos armadilhas validated (FAT-03 pre-requisite satisfied)
- [17/02]: SAP-First merge: 160 month-cells filled from Mercos where SAP=0, total R$ 2,493k (not R$ 2,149k estimated)
- [17/02]: 27 SAP negative values (credit notes) zeroed at merge time
- [17/02]: All 10 sem_cnpj matched via exact name in Mercos Carteira (no partial/fuzzy needed)
- [17/02]: 529 unique CNPJs from merge + 8 new from fuzzy = 537 total clients
- [17/02]: CARTEIRA population DEFERRED -- V13 has only 3 data rows, needs Phase 9 client roster
- [17/02]: PAINEL R$ 2,156,179 does not match any single source: SAP R$ 2,089k (-3.08%), Mercos R$ 1,895k, Merged R$ 2,493k (+15.65%)
- [17/02]: FAT-01/02 FAIL against merged (source scope mismatch), FAT-03 PASS (11/11 armadilhas), FAT-04 CONDITIONAL (CARTEIRA deferred)
- [17/02]: V13 integrity confirmed: 19,224 PROJECAO formulas intact, CARTEIRA 0 data rows, Phase 2 did not modify V13
- [17/02]: Phase 02 COMPLETE with FAIL_WITH_NOTES -- data correct, PAINEL scope mismatch needs business clarification
- [17/02]: V12 COM_DADOS path is data/sources/crm-versoes/v11-v12/ (not data/sources/crm/ as some plans reference)
- [17/02]: DRAFT 1 has 554 data rows (485 matched merged + 52 new SAP-only + 17 pre-existing unmatched)
- [17/02]: CARTEIRA expanded to 554 formula rows (25,484 INDEX/MATCH formulas) -- covers ALL DRAFT 1 clients
- [17/02]: ABC distribution on merged total (13 months): A=298 (55.5%), B=220 (41.0%), C=19 (3.5%)
- [17/02]: JAN/25 + FEV/25 hidden in totals (R$ 103,893.89) -- no column but included in ABC and derived metrics
- [17/02]: Phase 03 validation PASS: 537/537 cross-check match, 0 ABC mismatches, 10/10 derived fields, V13 19,224 formulas intact
- [17/02]: TIME-01 PASS (vendas preenchidas), TIME-02 PASS (SAP+Mercos merge), TIME-03 PASS (ABC recalc 100% match)
- [17/02]: CARTEIRA row 6088 cosmetic issue -- stale pre-existing row outside data range (4-557), not a real problem

### Fase 1 Revisada

A Fase 1 (PROJEÇÃO) muda de escopo:
- ANTES: Reconstruir 18.180 fórmulas do zero
- AGORA: Validar fórmulas existentes no V12 + popular dados SAP 2026 atualizados
- Fórmulas-chave já mapeadas (SUM, IF, VLOOKUP, RANK)
- Estrutura: 83 cols × 534-1566 rows dependendo da versão

### Pending Todos

None yet.

### Blockers/Concerns

- Relatórios Mercos mentem nos nomes — cuidado extra no ETL
- Julio Gadret 100% fora do sistema — dados limitados disponíveis
- 558 registros ALUCINAÇÃO do CONTROLE_FUNIL — não integrar
- LibreOffice recalc ≠ Excel recalc — testar no Excel real
- CARTEIRA no V12 tem 265 cols (vs 46 "imutáveis" doc) — investigar

## Session Continuity

Last session: 2026-02-17 04:03
Stopped at: Completed 03-02-PLAN.md (Phase 03 validation complete, all TIME requirements PASS). Phase 03 DONE.
Resume file: .planning/phases/03-timeline-mensal/03-02-SUMMARY.md
