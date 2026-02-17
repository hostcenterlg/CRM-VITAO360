# Roadmap: CRM VITAO360

## Overview

Rebuild definitivo do CRM VITAO360 em 10 fases, da reconstrução crítica da PROJEÇÃO até a validação final com 0 erros. Cada fase entrega um componente funcional e validado do CRM, seguindo a priorização do Leandro (criador). O projeto processa 873 arquivos-fonte de 3 sistemas (Mercos, SAP, Deskrio) usando Python (openpyxl, pandas, rapidfuzz) para gerar um CRM Excel completo com 14 abas e 81 colunas.

## Phases

- [x] **Phase 1: Projeção** - Reconstruir 18.180 fórmulas dinâmicas da aba PROJEÇÃO (CRÍTICO) ✓ 2026-02-17
- [x] **Phase 2: Faturamento** - Validar e consolidar dados de faturamento contra R$ 2.156.179 ✓ 2026-02-17
- [x] **Phase 3: Timeline Mensal** - Popular vendas mês a mês por cliente na CARTEIRA ✓ 2026-02-17
- [x] **Phase 4: LOG Completo** - Integrar ~11.758 registros de CONTROLE_FUNIL + Deskrio + históricos ✓ 2026-02-17
- [x] **Phase 5: Dashboard** - Redesenhar DASH com 3 blocos compactos (~45 rows) ✓ 2026-02-17
- [x] **Phase 6: E-commerce** - Cruzar dados de e-commerce Mercos na CARTEIRA ✓ 2026-02-17
- [x] **Phase 7: Redes e Franquias** - Preencher REDE/REGIONAL e corrigir #REF! ✓ 2026-02-17
- [ ] **Phase 8: Comitê e Metas** - Integrar metas 2026 SAP e visão consolidada
- [ ] **Phase 9: Blueprint v2** - Expandir CARTEIRA para 81 colunas com 8 grupos [+]
- [ ] **Phase 10: Validação Final** - 0 erros, teste Excel real, entrega completa

## Phase Details

### Phase 1: Projeção
**Goal**: Validar as 19.224 formulas existentes na PROJECAO (V12) e popular com dados SAP 2026 atualizados (metas + vendas realizadas), gerando o arquivo V13 com formulas 100% dinamicas e recalculaveis.
**Depends on**: Nothing (first phase)
**Requirements**: PROJ-01, PROJ-02, PROJ-03, PROJ-04
**Success Criteria** (what must be TRUE):
  1. Aba PROJECAO contem 19.224 formulas dinamicas validadas (nao dados estaticos)
  2. Projecao recalcula automaticamente quando dados de REALIZADO mudam (Z=SUM(AA:AL))
  3. Consolidacao por consultor e rede funciona (4 consultores, 15 redes)
  4. Meta 2026 R$ 4.747.200 populada (nota: requisito original R$5.7M revisado com dados SAP reais)
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Validar 19.224 formulas intactas + extrair dados SAP (mapeamento CNPJ, vendas 2025, metas 2026)
- [ ] 01-02-PLAN.md — Popular PROJECAO com dados SAP 2026 via Read-Modify-Write preservando formulas
- [ ] 01-03-PLAN.md — Verificacao completa de integridade (10 checks) + validacao requisitos PROJ-01..04

### Phase 2: Faturamento
**Goal**: Extrair vendas mensais de SAP (base primaria) e Mercos (complemento), combinar com estrategia SAP-First, popular vendas na CARTEIRA V13, e validar contra PAINEL R$ 2.156.179 (±0.5%).
**Depends on**: Phase 1 (usa V13 gerado)
**Requirements**: FAT-01, FAT-02, FAT-03, FAT-04
**Success Criteria** (what must be TRUE):
  1. Todos os 12 relatórios de vendas Mercos processados com armadilhas tratadas (via ETL pre-existente 02_VENDAS_POSITIVACAO)
  2. Faturamento mensal Jan-Dez 2025 bate com PAINEL (±0.5%)
  3. Fat.Mensal por cliente preenchido nas colunas 26-36 da CARTEIRA (MAR/25-JAN/26)
  4. Gap de R$ 6.790 investigado e documentado
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Extrair e validar vendas mensais Mercos (02_VENDAS_POSITIVACAO) e SAP (01_SAP_CONSOLIDADO) em JSONs intermediarios
- [ ] 02-02-PLAN.md — Merge SAP-First + Mercos-Complement, fuzzy match 10 sem CNPJ, popular CARTEIRA V13 (cols 26-36)
- [ ] 02-03-PLAN.md — Validar totais contra PAINEL R$ 2.156.179, documentar gap R$ 6.790, avaliar FAT-01..04

### Phase 3: Timeline Mensal
**Goal**: Popular o DRAFT 1 do V12 COM_DADOS com vendas mensais dos 537 clientes (sap_mercos_merged.json), calcular campos derivados (ABC, COMPRAS, POSITIVADO, TICKET, MEDIA), expandir formulas INDEX/MATCH da CARTEIRA para 537 rows, e validar cruzamento completo com avaliacao TIME-01..03.
**Depends on**: Phase 2 (precisa do sap_mercos_merged.json com 537 clientes)
**Requirements**: TIME-01, TIME-02, TIME-03
**Success Criteria** (what must be TRUE):
  1. DRAFT 1 com 537 rows de vendas mensais MAR/25-JAN/26 + campos derivados
  2. CARTEIRA com 537 rows de formulas INDEX/MATCH puxando do DRAFT 1
  3. Classificacao ABC recalculada (A>=2000, B>=500, C<500) para todos os 537 clientes
  4. Zero divergencia entre DRAFT 1 e sap_mercos_merged.json
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md — Popular DRAFT 1 com vendas + derivados e expandir CARTEIRA formulas (537 rows)
- [ ] 03-02-PLAN.md — Validar cruzamento DRAFT 1 vs merged JSON, ABC recalculo, avaliar TIME-01..03

### Phase 4: LOG Completo
**Goal**: Integrar todas as fontes de dados de interações no LOG, atingindo ~11.758 registros com Two-Base Architecture respeitada.
**Depends on**: Phase 2 (precisa do Motor de Matching validado)
**Requirements**: LOG-01, LOG-02, LOG-03, LOG-04, LOG-05, LOG-06, LOG-07
**Success Criteria** (what must be TRUE):
  1. LOG contém ≥ 11.758 registros (vs 1.581 atual)
  2. Two-Base Architecture: 100% dos registros de LOG com R$ 0.00
  3. Classificação 3-tier aplicada: REAL / SINTÉTICO / ALUCINAÇÃO segregados
  4. Dedup por chave composta DATA + CNPJ + RESULTADO funciona
  5. Julio Gadret presente com dados disponíveis
**Plans**: 4 plans

Plans:
- [ ] 04-01-PLAN.md — Criar _helpers.py compartilhado + ETL CONTROLE_FUNIL (10,544 registros, 4 abas, classificacao 3-tier) [Wave 1]
- [ ] 04-02-PLAN.md — ETL Deskrio (5,329 tickets ao nivel conversa, matching CNPJ, mapeamento LOG 20-col) [Wave 1]
- [ ] 04-03-PLAN.md — Gerador sintetico SAP-anchored (866 vendas, 6 jornadas GENOMA, 200+ templates, ~3,540 registros) [Wave 2]
- [ ] 04-04-PLAN.md — Merge cross-source, dedup, validacao 15 regras, popular aba LOG no V13, avaliar LOG-01..07 [Wave 3]

### Phase 5: Dashboard
**Goal**: Redesenhar a DASH de 8 blocos "Frankenstein" (164 rows × 19 cols) para 3 blocos compactos (~45 rows) com fórmulas válidas.
**Depends on**: Phase 3, Phase 4 (precisa de CARTEIRA e LOG populados)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. DASH tem 3 blocos: Executivo, Performance Consultor, Pipeline/Funil
  2. Layout ≤ 45 rows (vs 164 atual)
  3. Todas as fórmulas referenciam CARTEIRA e LOG corretamente
  4. Números da DASH batem com PAINEL de referência
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md — Normalizar 12 TIPO DO CONTATO do LOG para 7 valores canonicos (prerequisito para COUNTIFS)
- [ ] 05-02-PLAN.md — Construir aba DASH com 3 blocos + KPI cards + filtros VENDEDOR/PERIODO (formulas LOG)
- [ ] 05-03-PLAN.md — Validar DASH estrutura + cross-check LOG + avaliar DASH-01..05 + PROJECAO preservacao

### Phase 6: E-commerce
**Goal**: Processar ~17 relatorios de e-commerce Mercos (10-12 meses unicos apos dedup), cruzar com CNPJ via matching por nome, e popular 6 colunas de e-commerce no DRAFT 1 + JSON intermediario para Phase 9.
**Depends on**: Phase 2 (Motor de Matching + sap_mercos_merged.json)
**Requirements**: ECOM-01, ECOM-02, ECOM-03
**Success Criteria** (what must be TRUE):
  1. 17 arquivos de e-commerce processados com dedup (10-12 meses unicos, Outubro ausente documentado)
  2. 6 colunas de e-commerce no DRAFT 1 (cols 15-20) populadas para clientes com match
  3. Dados cruzados por nome->CNPJ com taxa >= 80% (lookup Mercos Carteira + SAP)
  4. JSON intermediario (ecommerce_matched.json) pronto para Phase 9 CARTEIRA expandida
**Plans**: 2 plans

Plans:
- [ ] 06-01-PLAN.md -- ETL dos 17 relatorios e-commerce: header detection (9/11 cols), dedup de duplicatas, month assignment, output ecommerce_raw.json
- [ ] 06-02-PLAN.md -- Matching nome->CNPJ (4 niveis), agregacao por CNPJ, popular DRAFT 1 cols 15-20, output ecommerce_matched.json

### Phase 7: Redes e Franquias
**Goal**: Remapear clientes SEM GRUPO via SAP, expandir tabela de referencia de 12 para 19 redes, criar aba REDES_FRANQUIAS_v2 com sinaleiro de penetracao dinamico e metas 6M, e validar os 4 requisitos REDE-01..04.
**Depends on**: Phase 2 (precisa da CARTEIRA com faturamento)
**Requirements**: REDE-01, REDE-02, REDE-03, REDE-04
**Success Criteria** (what must be TRUE):
  1. REDE/REGIONAL preenchido para 100% dos 534 clientes (534 no V13, nao 489)
  2. Zero #REF! na aba REDES_FRANQUIAS_v2
  3. Sinaleiro de penetração atualizado com dados 2025 completos
  4. Metas 6M por rede calculadas e operacionais
**Plans**: 3 plans

Plans:
- [ ] 07-01-PLAN.md -- Remapear 11 clientes SEM GRUPO via SAP CNPJ match + expandir tabela referencia AS:AZ de 12 para 19 redes + atualizar VLOOKUPs
- [ ] 07-02-PLAN.md -- Criar aba REDES_FRANQUIAS_v2 com 20 colunas, formulas SUMIFS/COUNTIFS dinamicas, metas 6M SAP, sinaleiro de penetracao
- [ ] 07-03-PLAN.md -- Validar REDE-01..04 + integridade V13 (19.224 formulas) + gerar validation_report.json

### Phase 8: Comitê e Metas
**Goal**: Validar infraestrutura de metas existente na PROJECAO (3 variantes de rateio), construir aba COMITE com 5 blocos gerenciais (Meta vs Realizado, Capacidade, Alertas, Funil, Motivos), filtros interativos (VENDEDOR, PERIODO, RATEIO toggle), e validar META-01..03.
**Depends on**: Phase 3 (precisa da timeline mensal), Phase 7 (precisa das redes)
**Requirements**: META-01, META-02, META-03
**Success Criteria** (what must be TRUE):
  1. Metas 2026 do SAP integradas na CARTEIRA
  2. COMITÊ com visão consolidada: consultor vs meta vs realizado
  3. Capacidade de atendimento validada (máx 40-50/dia/consultor)
**Plans**: 2 plans

Plans:
- [ ] 08-01-PLAN.md — Validar/auditar metas existentes na PROJECAO (3 variantes), reconciliar SAP delta R$31.803, mapear consultores + REALIZADO, gerar meta_validation_report.json
- [ ] 08-02-PLAN.md — Construir aba COMITE com 5 blocos + filtros VENDEDOR/PERIODO/RATEIO + conditional formatting + validar META-01..03

### Phase 9: Blueprint v2
**Goal**: Expandir CARTEIRA de 46 para 81 colunas com 8 grupos expansíveis [+], sem alterar as 46 originais.
**Depends on**: Todas as fases anteriores (precisa de todos os dados populados)
**Requirements**: BLUE-01, BLUE-02, BLUE-03, BLUE-04
**Success Criteria** (what must be TRUE):
  1. CARTEIRA tem 81 colunas organizadas em 8 grupos
  2. 10 colunas fixas (A-J) mantidas na posição original
  3. 46 colunas originais 100% preservadas e funcionais
  4. Grupos: Identificação, Vida Comercial, Timeline, Jornada, Ecommerce, SAP, Operacional, Comitê
**Plans**: 3 plans

Plans:
- [ ] 09-01: Mapear posição das 35 novas colunas nos 8 grupos
- [ ] 09-02: Inserir colunas via openpyxl preservando fórmulas existentes
- [ ] 09-03: Configurar agrupamento [+] e validar integridade

### Phase 10: Validação Final
**Goal**: Auditoria completa do CRM: 0 erros de fórmula, faturamento correto, Two-Base respeitada, teste no Excel real.
**Depends on**: Todas as fases anteriores
**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, VAL-05, VAL-06
**Success Criteria** (what must be TRUE):
  1. 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?) em TODAS as 14 abas
  2. Faturamento total = R$ 2.156.179 (±0.5%)
  3. 100% dos registros LOG têm R$ 0.00 (Two-Base)
  4. 0 CNPJs duplicados, todos com 14 dígitos
  5. 14 abas presentes e funcionais
  6. Arquivo abre e recalcula corretamente no Excel real
**Plans**: 3 plans

Plans:
- [ ] 10-01: Script de auditoria automática (fórmulas, CNPJ, Two-Base, totais)
- [ ] 10-02: Corrigir todos os erros encontrados pela auditoria
- [ ] 10-03: Teste final no Excel real e relatório de entrega

## Progress

**Execution Order:**
Phases execute em ordem: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
(Fases 1 e 2 podem rodar em paralelo. Fase 6 pode rodar em paralelo com 4-5.)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Projeção | 3/3 | COMPLETE | 2026-02-17 |
| 2. Faturamento | 3/3 | COMPLETE (FAIL_WITH_NOTES) | 2026-02-17 |
| 3. Timeline Mensal | 2/2 | COMPLETE | 2026-02-17 |
| 4. LOG Completo | 4/4 | COMPLETE | 2026-02-17 |
| 5. Dashboard | 3/3 | COMPLETE | 2026-02-17 |
| 6. E-commerce | 2/2 | COMPLETE | 2026-02-17 |
| 7. Redes e Franquias | 3/3 | COMPLETE | 2026-02-17 |
| 8. Comitê e Metas | 0/2 | Not started | - |
| 9. Blueprint v2 | 0/3 | Not started | - |
| 10. Validação Final | 0/3 | Not started | - |

---
*Roadmap created: 2026-02-15 via DEUS-AIOS*
*Total: 10 phases, 28 plans, 43 requirements*
