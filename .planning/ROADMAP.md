# Roadmap: CRM VITAO360

## Overview

Rebuild definitivo do CRM VITAO360 em 10 fases, da reconstrução crítica da PROJEÇÃO até a validação final com 0 erros. Cada fase entrega um componente funcional e validado do CRM, seguindo a priorização do Leandro (criador). O projeto processa 873 arquivos-fonte de 3 sistemas (Mercos, SAP, Deskrio) usando Python (openpyxl, pandas, rapidfuzz) para gerar um CRM Excel completo com 14 abas e 81 colunas.

## Phases

- [ ] **Phase 1: Projeção** - Reconstruir 18.180 fórmulas dinâmicas da aba PROJEÇÃO (CRÍTICO)
- [ ] **Phase 2: Faturamento** - Validar e consolidar dados de faturamento contra R$ 2.156.179
- [ ] **Phase 3: Timeline Mensal** - Popular vendas mês a mês por cliente na CARTEIRA
- [ ] **Phase 4: LOG Completo** - Integrar ~11.758 registros de CONTROLE_FUNIL + Deskrio + históricos
- [ ] **Phase 5: Dashboard** - Redesenhar DASH com 3 blocos compactos (~45 rows)
- [ ] **Phase 6: E-commerce** - Cruzar dados de e-commerce Mercos na CARTEIRA
- [ ] **Phase 7: Redes e Franquias** - Preencher REDE/REGIONAL e corrigir #REF!
- [ ] **Phase 8: Comitê e Metas** - Integrar metas 2026 SAP e visão consolidada
- [ ] **Phase 9: Blueprint v2** - Expandir CARTEIRA para 81 colunas com 8 grupos [+]
- [ ] **Phase 10: Validação Final** - 0 erros, teste Excel real, entrega completa

## Phase Details

### Phase 1: Projeção
**Goal**: Reconstruir as 18.180 fórmulas perdidas da aba PROJEÇÃO, tornando-a 100% dinâmica e recalculável. Esta é a entrega mais crítica do projeto.
**Depends on**: Nothing (first phase)
**Requirements**: PROJ-01, PROJ-02, PROJ-03, PROJ-04
**Success Criteria** (what must be TRUE):
  1. Aba PROJEÇÃO contém 18.180 fórmulas dinâmicas (não dados estáticos)
  2. Projeção recalcula automaticamente quando dados da CARTEIRA mudam
  3. Consolidação por consultor, ABC, status e região funciona
  4. Projeção 2026 mostra R$ 5.7M / 3.168 vendas / 3 por dia por consultor
**Plans**: 3 plans

Plans:
- [ ] 01-01: Analisar estrutura da PROJEÇÃO existente e mapear fórmulas necessárias
- [ ] 01-02: Gerar fórmulas dinâmicas em Python (openpyxl) respeitando INGLÊS
- [ ] 01-03: Validar PROJEÇÃO contra dados do PAINEL e números de referência

### Phase 2: Faturamento
**Goal**: Processar os 12+ relatórios de vendas Mercos (com armadilhas de nomes) e consolidar faturamento mensal validado contra R$ 2.156.179 do PAINEL.
**Depends on**: Nothing (pode rodar em paralelo com Phase 1)
**Requirements**: FAT-01, FAT-02, FAT-03, FAT-04
**Success Criteria** (what must be TRUE):
  1. Todos os 12 relatórios de vendas Mercos processados com armadilhas tratadas
  2. Faturamento mensal Jan-Dez 2025 bate com PAINEL (±0.5%)
  3. Fat.Mensal por cliente preenchido nas 12 colunas da CARTEIRA
  4. Gap de R$ 6.790 investigado e documentado
**Plans**: 3 plans

Plans:
- [ ] 02-01: ETL dos relatórios Mercos com tratamento de armadilhas (header linha 10, nomes incorretos)
- [ ] 02-02: Cruzamento Mercos × CARTEIRA via Motor de Matching (Nome Fantasia, sem CNPJ)
- [ ] 02-03: Validação de faturamento contra PAINEL e investigação do gap de R$ 6.790

### Phase 3: Timeline Mensal
**Goal**: Popular as vendas mês a mês por cliente na CARTEIRA, cruzando Mercos e SAP.
**Depends on**: Phase 2 (precisa dos dados de faturamento processados)
**Requirements**: TIME-01, TIME-02, TIME-03
**Success Criteria** (what must be TRUE):
  1. Colunas de vendas mensais (Jan-Dez 2025) preenchidas para cada cliente
  2. Dados cruzados entre Mercos (vendas) e SAP (mês a mês) sem divergência
  3. Classificação ABC recalculada com base na timeline completa
**Plans**: 2 plans

Plans:
- [ ] 03-01: Cruzar vendas mensais Mercos + SAP por CNPJ e popular na CARTEIRA
- [ ] 03-02: Recalcular classificação ABC e validar totais mensais

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
- [ ] 04-01: Processar 10.484 registros do CONTROLE_FUNIL com classificação 3-tier
- [ ] 04-02: Processar 5.329 tickets Deskrio (77.805 mensagens, 5.425 conversas)
- [ ] 04-03: Integrar 3.540 contatos históricos retroativos + dados Julio
- [ ] 04-04: Dedup, validação Two-Base e contagem final

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
- [ ] 05-01: Definir layout dos 3 blocos e especificar fórmulas necessárias
- [ ] 05-02: Construir aba DASH com fórmulas em INGLÊS (openpyxl)
- [ ] 05-03: Validar números da DASH contra PAINEL e formatar visualmente

### Phase 6: E-commerce
**Goal**: Cruzar os 20 relatórios de e-commerce Mercos com a CARTEIRA e popular as 4 colunas de e-commerce.
**Depends on**: Phase 2 (precisa do Motor de Matching)
**Requirements**: ECOM-01, ECOM-02, ECOM-03
**Success Criteria** (what must be TRUE):
  1. 20 relatórios de acesso ao e-commerce processados
  2. 4 colunas de e-commerce na CARTEIRA populadas para todos os clientes
  3. Dados cruzados por CNPJ/Nome Fantasia corretamente
**Plans**: 2 plans

Plans:
- [ ] 06-01: ETL dos 20 relatórios de e-commerce (Acesso Ecomerce/*.xlsx)
- [ ] 06-02: Cruzar com CARTEIRA e popular 4 colunas de e-commerce

### Phase 7: Redes e Franquias
**Goal**: Preencher REDE/REGIONAL para todos os clientes e corrigir os erros #REF! na aba REDES_FRANQUIAS_v2.
**Depends on**: Phase 2 (precisa da CARTEIRA com faturamento)
**Requirements**: REDE-01, REDE-02, REDE-03, REDE-04
**Success Criteria** (what must be TRUE):
  1. REDE/REGIONAL preenchido para 100% dos 489 clientes
  2. Zero #REF! na aba REDES_FRANQUIAS_v2
  3. Sinaleiro de penetração atualizado com dados 2025 completos
  4. Metas 6M por rede calculadas e operacionais
**Plans**: 3 plans

Plans:
- [ ] 07-01: Mapear clientes → redes/regionais usando Motor de Matching + regex
- [ ] 07-02: Corrigir #REF! na REDES_FRANQUIAS_v2
- [ ] 07-03: Atualizar sinaleiro de penetração e metas 6M

### Phase 8: Comitê e Metas
**Goal**: Integrar metas 2026 do SAP e criar visão consolidada do COMITÊ.
**Depends on**: Phase 3 (precisa da timeline mensal), Phase 7 (precisa das redes)
**Requirements**: META-01, META-02, META-03
**Success Criteria** (what must be TRUE):
  1. Metas 2026 do SAP integradas na CARTEIRA
  2. COMITÊ com visão consolidada: consultor vs meta vs realizado
  3. Capacidade de atendimento validada (máx 40-50/dia/consultor)
**Plans**: 2 plans

Plans:
- [ ] 08-01: Importar metas 2026 do SAP e cruzar com CARTEIRA
- [ ] 08-02: Construir aba COMITÊ com visão consolidada

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
| 1. Projeção | 0/3 | Not started | - |
| 2. Faturamento | 0/3 | Not started | - |
| 3. Timeline Mensal | 0/2 | Not started | - |
| 4. LOG Completo | 0/4 | Not started | - |
| 5. Dashboard | 0/3 | Not started | - |
| 6. E-commerce | 0/2 | Not started | - |
| 7. Redes e Franquias | 0/3 | Not started | - |
| 8. Comitê e Metas | 0/2 | Not started | - |
| 9. Blueprint v2 | 0/3 | Not started | - |
| 10. Validação Final | 0/3 | Not started | - |

---
*Roadmap created: 2026-02-15 via DEUS-AIOS*
*Total: 10 phases, 28 plans, 43 requirements*
