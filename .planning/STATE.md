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

**Current focus:** Phase 07 Redes e Franquias -- Plan 01 COMPLETE, executing Plan 02.

## Current Position

Phase: 7 of 10 (Redes e Franquias)
Plan: 1 of 3 in current phase (07-01 COMPLETE)
Status: Plan 07-01 COMPLETE -- 11 SEM GRUPO remapped, AS:AZ expanded to 20 redes + SEM GRUPO, 2,670 VLOOKUPs updated
Last activity: 2026-02-17 -- Plan 07-01 executed (remap + expand reference table)

Progress: [██████████████████] 65% (plans 01-01..03, 02-01..03, 03-01..02, 04-01..04, 05-01..03, 06-01..02, 07-01 of 31 total complete)

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
| CONTROLE_FUNIL_JAN2026 | 10,434 | **INTEGRADO + DEDUP** |
| Deskrio tickets (07_TICKETS) | 4,240 | **INTEGRADO + DEDUP** |
| Synthetic SAP-anchored | 6,156 | **GERADO + DEDUP** |
| **TOTAL no V13 LOG** | **20,830** | **COMPLETO** |

## Performance Metrics

**Velocity:**
- Total plans completed: 20
- Average duration: 14 min
- Total execution time: 4.75 hours

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
| 04-log-completo | 01 | 6 min | 2 | 4 |
| 04-log-completo | 02 | 10 min | 1 | 2 |
| 04-log-completo | 03 | 25 min | 3 | 2 |
| 04-log-completo | 04 | 45 min | 2 | 5 |
| 05-dashboard | 01 | 2 min | 1 | 2 |
| 05-dashboard | 02 | 3 min | 1 | 2 |
| 05-dashboard | 03 | 2 min | 1 | 1 |
| 06-e-commerce | 01 | 8 min | 1 | 2 |
| 06-e-commerce | 02 | 53 min | 2 | 4 |
| 07-redes-franquias | 01 | 69 min | 1 | 2 |

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
- [17/02]: 06_LOG_FUNIL.xlsx has pre-classified 'Interacoes' sheet (not raw 4-tab structure) -- alucinacoes already separated
- [17/02]: RESULTADO normalization: VENDA->VENDA/PEDIDO, PERDA/NAO VENDA->PERDA/FECHOU LOJA, FOLLOW UP->FOLLOW UP 7
- [17/02]: P8 accent stripping via bidirectional map: LOG stores sem-acento, motor_de_regras uses com-acento
- [17/02]: 10,442 CONTROLE_FUNIL records processed (9,120 REAL + 1,322 SINTETICO), 558 alucinacoes documented
- [17/02]: DAIANE STAVICKI canonical name (not CENTRAL - DAIANE), JULIO GADRET single spelling (1,814 records merged)
- [17/02]: Deskrio already at ticket level (5,329 tickets not 77,805 messages) -- no aggregation needed
- [17/02]: Deskrio CNPJ matching: 3,907 direct + 564 name-based (83.9% rate); 762 pendentes discarded (internal/transport/test)
- [17/02]: Deskrio TIPO ACAO preserves Origem field (60.6% Ativo, 39.4% Receptivo) -- not all RECEPTIVO as initially assumed
- [17/02]: Rodrigo (952 Deskrio tickets) kept as consultant -- Deskrio operator, not in canonical CRM team
- [17/02]: Deskrio WHATSAPP=NAO, LIGACAO=NAO for all (own chat platform, not WhatsApp/phone)
- [17/02]: TIPO DO CONTATO normalized 12->7: CONTATOS PASSIVO/SUPORTE->POS-VENDA, ENVIO MKT->PROSPECCAO, PROSPECCAO NOVOS->PROSPECCAO
- [17/02]: ATENDIMENTO CLIENTES INATIVOS abbreviated to ATEND. CLIENTES INATIVOS (matching ATIVOS pattern)
- [17/02]: After normalization: POS-VENDA 8,670 | ATEND.ATIVOS 5,296 | PROSPECCAO 4,634 | ATEND.INATIVOS 1,227 | NEGOCIACAO 944 | PERDA 55 | FOLLOW UP 4
- [17/02]: DASH tab 41 rows, 304 formulas -- 3 blocks replacing 7-block 164-row original design
- [17/02]: cf() helper: IF(OR VENDEDOR toggle) + COUNTIFS(date_range + extra_criteria) for all DASH formulas
- [17/02]: 6 KPI cards (not 8) -- removed PROSPECCOES and FOLLOW UPS separate KPIs
- [17/02]: Produtividade section uses direct COUNTIFS (no cf()) since consultant explicit in cell reference
- [17/02]: DASH separator columns (H, L, O) width=2 for visual block grouping in Bloco 2
- [17/02]: Phase 05 COMPLETE -- 22/22 checks PASS, 5/5 requirements (DASH-01..05) formally verified
- [17/02]: 230 LOG records in default Feb 2026 date range -- expected TOTAL CONTATOS KPI value in Excel
- [17/02]: Trio Abril/Maio/junho (identical data, 77 rows each) reassigned to April -- data differs from real June file (126 rows)
- [17/02]: Dezembro partial (17 rows) L2-deduped in favor of Dezembro 2025 (101 rows)
- [17/02]: rELATORIO JANEIRO 2026 (127 rows, emitted 30/01) preferred over Acesso janeiro (59 rows, emitted 15/01)
- [17/02]: fev2026/ file (91 rows) preferred over b2b fevereiro (43 rows) for Feb 2026
- [17/02]: October 2025 and May 2025 ABSENT from e-commerce data -- no files found
- [17/02]: .xls files gracefully skipped (pip broken, xlrd unavailable) -- non-blocking
- [17/02]: E-commerce ETL produces 10 months, 1075 records in ecommerce_raw.json
- [17/02]: E-commerce match rate 64.6% (441/683 names) -- 200+ unmatched are B2B portal prospects NOT in any client database
- [17/02]: 5-level matching: cnpj_prefix -> exact -> exact_normalized -> partial -> partial_normalized
- [17/02]: 3 lookup sources: Mercos Carteira (497), DRAFT 1 (502), SAP Cadastro (1698) = 3699 merged entries
- [17/02]: DRAFT 1 actual path: data/sources/drafts/ (not crm-versoes/v11-v12); CNPJ in col 2 (not col 3)
- [17/02]: DRAFT 1 cols 15-20 populated: 294 rows with e-commerce data (ACESSOS, ACESSO B2B, PORTAL, ITENS, VALOR B2B, OPORTUNIDADE)
- [17/02]: Phase 06 E-commerce COMPLETE -- ETL + Match + Populate all done
- [17/02]: 20 redes (not 19): MINHA QUITANDINHA discovered as real SAP rede with 1 client
- [17/02]: VLOOKUP F:J end row $24 (20 redes + SEM GRUPO in AS:AZ rows 4-24)
- [17/02]: SAP has 18 redes with CNPJ assignments; MIX VALI in Leads only (0 clients in Cadastro)
- [17/02]: FAT.REAL via sum AA:AL (col Z formula returns None with data_only=True)
- [17/02]: MINHA QUITANDINHA has 0 lojas in SAP Leads but R$1,928 fat.real from 1 active client
- [17/02]: 11 SEM GRUPO remapped: 7 ESMERALDA, 1 DIVINA TERRA, 1 MERCOCENTRO, 1 MINHA QUITANDINHA, 1 VIDA LEVE

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

Last session: 2026-02-17 15:12
Stopped at: Completed 07-01-PLAN.md (remap 11 SEM GRUPO + expand AS:AZ to 20 redes + SEM GRUPO)
Resume file: .planning/phases/07-redes-franquias/07-01-SUMMARY.md
Next step: Execute 07-02-PLAN.md (create REDES_FRANQUIAS_v2 tab)
