# Roadmap: CRM VITAO360

## Milestones

- v1.0 Excel Rebuild - Fases 1-10 (entregue 2026-02-17)
- v2.0 Motor Operacional SaaS - Fases 11-15 (em andamento)

## Overview

Rebuild definitivo do CRM VITAO360 em fases incrementais. O milestone v1.0 (fases 1-10) entregou a planilha FINAL com 40 abas, 210K+ formulas e 154.302 formulas validadas. O milestone v2.0 (fases 11-15) extrai toda a inteligencia do Excel para Python funcional: import de dados, motor de regras (92 combinacoes), score ranking, sinaleiro, agenda inteligente diaria e projecao vs meta -- tudo rodando local com dados reais.

## Phases

<details>
<summary>v1.0 Excel Rebuild (Fases 1-10) - ENTREGUE 2026-02-17</summary>

- [x] **Phase 1: Projecao** - Reconstruir 18.180 formulas dinamicas da aba PROJECAO (CRITICO) - 2026-02-17
- [x] **Phase 2: Faturamento** - Validar e consolidar dados de faturamento contra R$ 2.156.179 - 2026-02-17
- [x] **Phase 3: Timeline Mensal** - Popular vendas mes a mes por cliente na CARTEIRA - 2026-02-17
- [x] **Phase 4: LOG Completo** - Integrar ~11.758 registros de CONTROLE_FUNIL + Deskrio + historicos - 2026-02-17
- [x] **Phase 5: Dashboard** - Redesenhar DASH com 3 blocos compactos (~45 rows) - 2026-02-17
- [x] **Phase 6: E-commerce** - Cruzar dados de e-commerce Mercos na CARTEIRA - 2026-02-17
- [x] **Phase 7: Redes e Franquias** - Preencher REDE/REGIONAL e corrigir #REF! - 2026-02-17
- [x] **Phase 8: Comite e Metas** - Integrar metas 2026 SAP e visao consolidada - 2026-02-17
- [x] **Phase 9: Blueprint v2** - Expandir CARTEIRA para 263 colunas com 6 super-grupos + motor inteligencia + 4 AGENDA - 2026-02-17
- [x] **Phase 10: Validacao Final** - Audit CLEAN, V14 FINAL com layout corrigido (V31 learnings), confronto dados completo - 2026-02-17

</details>

### v2.0 Motor Operacional SaaS (Fases 11-15)

- [ ] **Phase 11: Import Pipeline** - Importar xlsx FINAL, normalizar CNPJ, classificar dados, aplicar DE-PARA vendedores
- [ ] **Phase 12: Motor de Regras** - 92 combinacoes SITUACAO x RESULTADO em Python, regras configuraveis, calculo automatico
- [ ] **Phase 13: Score + Sinaleiro** - Score 6 fatores ponderados (0-100), Piramide P1-P7, sinaleiro de saude por cliente
- [ ] **Phase 14: Agenda Inteligente** - Lista diaria 40-60 atendimentos por consultor, priorizada por Score, export xlsx
- [ ] **Phase 15: Projecao + Export** - Realizado vs meta SAP, % alcancado, export xlsx processado, dashboard terminal

## Phase Details

<details>
<summary>v1.0 Excel Rebuild (Fases 1-10) - ENTREGUE 2026-02-17</summary>

### Phase 1: Projecao
**Goal**: Validar as 19.224 formulas existentes na PROJECAO (V12) e popular com dados SAP 2026 atualizados (metas + vendas realizadas), gerando o arquivo V13 com formulas 100% dinamicas e recalculaveis.
**Depends on**: Nothing (first phase)
**Requirements**: PROJ-01, PROJ-02, PROJ-03, PROJ-04
**Success Criteria** (what must be TRUE):
  1. Aba PROJECAO contem 19.224 formulas dinamicas validadas (nao dados estaticos)
  2. Projecao recalcula automaticamente quando dados de REALIZADO mudam (Z=SUM(AA:AL))
  3. Consolidacao por consultor e rede funciona (4 consultores, 15 redes)
  4. Meta 2026 R$ 4.747.200 populada (nota: requisito original R$5.7M revisado com dados SAP reais)
**Plans**: 3/3 COMPLETE

Plans:
- [x] 01-01-PLAN.md — Validar 19.224 formulas intactas + extrair dados SAP
- [x] 01-02-PLAN.md — Popular PROJECAO com dados SAP 2026 via Read-Modify-Write
- [x] 01-03-PLAN.md — Verificacao completa de integridade (10 checks)

### Phase 2: Faturamento
**Goal**: Extrair vendas mensais de SAP (base primaria) e Mercos (complemento), combinar com estrategia SAP-First, popular vendas na CARTEIRA V13, e validar contra PAINEL R$ 2.156.179 (+/-0.5%).
**Depends on**: Phase 1 (usa V13 gerado)
**Requirements**: FAT-01, FAT-02, FAT-03, FAT-04
**Success Criteria** (what must be TRUE):
  1. Todos os 12 relatorios de vendas Mercos processados com armadilhas tratadas
  2. Faturamento mensal Jan-Dez 2025 bate com PAINEL (+/-0.5%)
  3. Fat.Mensal por cliente preenchido nas colunas 26-36 da CARTEIRA
  4. Gap de R$ 6.790 investigado e documentado
**Plans**: 3/3 COMPLETE (FAIL_WITH_NOTES)

Plans:
- [x] 02-01-PLAN.md — Extrair e validar vendas mensais Mercos e SAP em JSONs intermediarios
- [x] 02-02-PLAN.md — Merge SAP-First + Mercos-Complement, fuzzy match, popular CARTEIRA V13
- [x] 02-03-PLAN.md — Validar totais contra PAINEL, documentar gap

### Phase 3: Timeline Mensal
**Goal**: Popular o DRAFT 1 do V12 COM_DADOS com vendas mensais dos 537 clientes, calcular campos derivados e expandir formulas INDEX/MATCH da CARTEIRA.
**Depends on**: Phase 2
**Requirements**: TIME-01, TIME-02, TIME-03
**Success Criteria** (what must be TRUE):
  1. DRAFT 1 com 537 rows de vendas mensais MAR/25-JAN/26 + campos derivados
  2. CARTEIRA com 537 rows de formulas INDEX/MATCH puxando do DRAFT 1
  3. Classificacao ABC recalculada para todos os 537 clientes
  4. Zero divergencia entre DRAFT 1 e sap_mercos_merged.json
**Plans**: 2/2 COMPLETE

Plans:
- [x] 03-01-PLAN.md — Popular DRAFT 1 com vendas + derivados e expandir CARTEIRA formulas
- [x] 03-02-PLAN.md — Validar cruzamento DRAFT 1 vs merged JSON, ABC recalculo

### Phase 4: LOG Completo
**Goal**: Integrar todas as fontes de dados de interacoes no LOG, atingindo ~11.758 registros com Two-Base Architecture respeitada.
**Depends on**: Phase 2
**Requirements**: LOG-01, LOG-02, LOG-03, LOG-04, LOG-05, LOG-06, LOG-07
**Success Criteria** (what must be TRUE):
  1. LOG contem >= 11.758 registros (vs 1.581 atual)
  2. Two-Base Architecture: 100% dos registros de LOG com R$ 0.00
  3. Classificacao 3-tier aplicada: REAL / SINTETICO / ALUCINACAO segregados
  4. Dedup por chave composta DATA + CNPJ + RESULTADO funciona
  5. Julio Gadret presente com dados disponiveis
**Plans**: 4/4 COMPLETE

Plans:
- [x] 04-01-PLAN.md — Criar _helpers.py + ETL CONTROLE_FUNIL
- [x] 04-02-PLAN.md — ETL Deskrio
- [x] 04-03-PLAN.md — Gerador sintetico SAP-anchored
- [x] 04-04-PLAN.md — Merge cross-source, dedup, popular aba LOG no V13

### Phase 5: Dashboard
**Goal**: Redesenhar a DASH de 8 blocos "Frankenstein" para 3 blocos compactos (~45 rows) com formulas validas.
**Depends on**: Phase 3, Phase 4
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. DASH tem 3 blocos: Executivo, Performance Consultor, Pipeline/Funil
  2. Layout <= 45 rows (vs 164 atual)
  3. Todas as formulas referenciam CARTEIRA e LOG corretamente
  4. Numeros da DASH batem com PAINEL de referencia
**Plans**: 3/3 COMPLETE

Plans:
- [x] 05-01-PLAN.md — Normalizar 12 TIPO DO CONTATO para 7 valores canonicos
- [x] 05-02-PLAN.md — Construir aba DASH com 3 blocos + KPI cards + filtros
- [x] 05-03-PLAN.md — Validar DASH estrutura + cross-check LOG

### Phase 6: E-commerce
**Goal**: Processar ~17 relatorios de e-commerce Mercos, cruzar com CNPJ via matching por nome, popular 6 colunas no DRAFT 1.
**Depends on**: Phase 2
**Requirements**: ECOM-01, ECOM-02, ECOM-03
**Success Criteria** (what must be TRUE):
  1. 17 arquivos processados com dedup (10-12 meses unicos)
  2. 6 colunas de e-commerce no DRAFT 1 populadas
  3. Dados cruzados por nome->CNPJ com taxa >= 80%
  4. JSON intermediario pronto para Phase 9
**Plans**: 2/2 COMPLETE

Plans:
- [x] 06-01-PLAN.md — ETL dos 17 relatorios e-commerce
- [x] 06-02-PLAN.md — Matching nome->CNPJ, popular DRAFT 1

### Phase 7: Redes e Franquias
**Goal**: Remapear clientes SEM GRUPO via SAP, expandir tabela de referencia de 12 para 19 redes, criar aba REDES_FRANQUIAS_v2 com sinaleiro de penetracao.
**Depends on**: Phase 2
**Requirements**: REDE-01, REDE-02, REDE-03, REDE-04
**Success Criteria** (what must be TRUE):
  1. REDE/REGIONAL preenchido para 100% dos 534 clientes
  2. Zero #REF! na aba REDES_FRANQUIAS_v2
  3. Sinaleiro de penetracao atualizado com dados 2025 completos
  4. Metas 6M por rede calculadas e operacionais
**Plans**: 3/3 COMPLETE

Plans:
- [x] 07-01-PLAN.md — Remapear 11 clientes SEM GRUPO via SAP + expandir tabela referencia
- [x] 07-02-PLAN.md — Criar aba REDES_FRANQUIAS_v2 com formulas SUMIFS/COUNTIFS
- [x] 07-03-PLAN.md — Validar REDE-01..04 + integridade V13

### Phase 8: Comite e Metas
**Goal**: Validar infraestrutura de metas existente na PROJECAO, construir aba COMITE com 5 blocos gerenciais.
**Depends on**: Phase 3, Phase 7
**Requirements**: META-01, META-02, META-03
**Success Criteria** (what must be TRUE):
  1. Metas 2026 do SAP integradas na CARTEIRA
  2. COMITE com visao consolidada: consultor vs meta vs realizado
  3. Capacidade de atendimento validada (max 40-50/dia/consultor)
**Plans**: 2/2 COMPLETE

Plans:
- [x] 08-01-PLAN.md — Validar/auditar metas existentes na PROJECAO
- [x] 08-02-PLAN.md — Construir aba COMITE com 5 blocos + filtros

### Phase 9: Blueprint v2
**Goal**: Recriar CARTEIRA completa do V12 (263 colunas, 6 super-grupos, 3 niveis agrupamento) no V13, com motor de inteligencia de 3 camadas e 4 abas AGENDA.
**Depends on**: Todas as fases anteriores
**Requirements**: BLUE-01, BLUE-02, BLUE-03, BLUE-04
**Success Criteria** (what must be TRUE):
  1. CARTEIRA tem 263 colunas organizadas em 6 super-grupos
  2. 3 niveis de agrupamento [+] com ancoras por super-grupo e sub-grupo
  3. Motor de inteligencia: Score ranking, Pipeline vs Meta, Alerta de urgencia
  4. 4 abas AGENDA (LARISSA, DAIANE, MANU, JULIO) com tarefas priorizadas por SCORE
**Plans**: 6/6 COMPLETE

Plans:
- [x] 09-01-PLAN.md — Auditoria profunda V12 CARTEIRA
- [x] 09-02-PLAN.md — Criar abas de suporte: REGRAS, DRAFT 1, DRAFT 2
- [x] 09-03-PLAN.md — Esqueleto CARTEIRA + formulas MERCOS e FUNIL
- [x] 09-04-PLAN.md — Blocos SAP + FATURAMENTO mega-bloco
- [x] 09-05-PLAN.md — Motor de inteligencia 3 camadas
- [x] 09-06-PLAN.md — 4 abas AGENDA com dropdowns REGRAS

### Phase 10: Validacao Final
**Goal**: Auditoria completa do CRM: 0 erros de formula, faturamento correto, Two-Base respeitada, teste no Excel real.
**Depends on**: Todas as fases anteriores
**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, VAL-05, VAL-06
**Success Criteria** (what must be TRUE):
  1. 0 erros de formula em TODAS as abas
  2. Faturamento total = R$ 2.156.179 (+/-0.5%)
  3. 100% dos registros LOG tem R$ 0.00 (Two-Base)
  4. 0 CNPJs duplicados, todos com 14 digitos
  5. 13 abas presentes e funcionais
  6. Arquivo abre e recalcula corretamente no Excel real
**Plans**: 3/3 COMPLETE (V14 FINAL)

Plans:
- [x] 10-01-PLAN.md — Comprehensive audit script: VAL-01 through VAL-05
- [x] 10-02-PLAN.md — Fix audit issues + generate delivery report
- [x] 10-03-PLAN.md — Excel real test checkpoint (VAL-06) + V14 com V31 fixes

</details>

### v2.0 Motor Operacional SaaS (Fases 11-15)

**Milestone Goal:** Extrair toda inteligencia do Excel (92 regras, Score, Sinaleiro, Agenda) para Python funcional que roda local com dados reais, gerando agenda inteligente diaria para cada consultor.

### Phase 11: Import Pipeline
**Goal**: Operador importa a planilha FINAL (40 abas) e obtem base de clientes unificada em Python com CNPJ normalizado, dados classificados e vendedores mapeados.
**Depends on**: Phase 10 (planilha FINAL validada como fonte de dados)
**Requirements**: IMPORT-01, IMPORT-02, IMPORT-03, IMPORT-04
**Success Criteria** (what must be TRUE):
  1. Operador executa um comando e a planilha FINAL (40 abas) eh lida em DataFrames Python com todas as abas relevantes extraidas
  2. Todo CNPJ na base esta normalizado como string de 14 digitos zero-padded (nenhum float, nenhum int, nenhum com pontuacao)
  3. Cada registro tem classificacao 3-tier (REAL/SINTETICO/ALUCINACAO) e os 558 registros ALUCINACAO sao excluidos automaticamente
  4. Nomes de vendedores estao canonicalizados pelo DE-PARA (Manu Vitao -> MANU, Larissa Vitao -> LARISSA, etc.) sem nenhum alias solto
  5. Base unificada eh salva em formato intermediario (JSON/Parquet) para consumo pelas fases seguintes
**Plans**: 2 plans

**Plans**: 2/2 COMPLETE

Plans:
- [x] 11-01-PLAN.md — Config + helpers + import pipeline (ler xlsx FINAL, normalizar CNPJs, DE-PARA vendedores)
- [x] 11-02-PLAN.md — Classificacao 3-tier, unificacao de base, export JSON, validacao humana

### Phase 12: Motor de Regras
**Goal**: As 92 combinacoes de SITUACAO x RESULTADO do CRM produzem automaticamente as 9 dimensoes de saida (Estagio Funil, Fase, Tipo Contato, Acao Futura, Temperatura, etc.) via motor Python configuravel.
**Depends on**: Phase 11 (base de clientes importada)
**Requirements**: MOTOR-01, MOTOR-02, MOTOR-03
**Success Criteria** (what must be TRUE):
  1. Dado qualquer par (SITUACAO, RESULTADO) valido, o motor retorna as 9 dimensoes corretas em menos de 1 segundo
  2. As 92 combinacoes (7 SITUACAO x 14 RESULTADO) estao 100% cobertas e batem com a aba REGRAS da planilha FINAL
  3. A tabela de regras vive em arquivo configuravel (JSON ou YAML), nao hardcoded no codigo Python
  4. Dado um atendimento (CNPJ + RESULTADO), o motor calcula e atribui: Estagio Funil, Fase, Tipo Contato, Acao Futura, Temperatura
**Plans**: 1/1 COMPLETE (built in session 23/Mar, committed 24/Mar)

Plans:
- [x] motor_regras.py — 92 combinacoes carregadas de JSON, 9 dimensoes, 99.2% match

### Phase 13: Score + Sinaleiro
**Goal**: Cada cliente recebe um score numerico (0-100) baseado em 6 fatores ponderados que gera Piramide P1-P7, e um sinaleiro de saude (cor) baseado em dias sem compra vs ciclo medio, com cadencia de contato derivada.
**Depends on**: Phase 12 (motor de regras para Temperatura e Estagio)
**Requirements**: SCORE-01, SCORE-02, SCORE-03, SINAL-01, SINAL-02
**Success Criteria** (what must be TRUE):
  1. Cada cliente ativo tem score 0-100 calculado com 6 fatores ponderados (URG 30%, VAL 25%, FU 20%, SIN 15%, TENT 5%, SIT 5%) e o resultado bate com a formula da CARTEIRA Excel
  2. Score gera classificacao Piramide automaticamente: P1 (score >= 85) ate P7 (score < 15), com distribuicao que reflete a base real
  3. Pesos dos 6 fatores sao configuraveis (arquivo externo), nao hardcoded
  4. Cada cliente recebe cor sinaleiro (ROXO/VERDE/AMARELO/LARANJA/VERMELHO) derivada de dias sem compra vs ciclo medio de compra
  5. Cada cor gera cadencia de contato recomendada (ex: ROXO = nunca comprou -> contato diario, VERMELHO = muito atrasado -> contato urgente)
**Plans**: 1/1 COMPLETE (built in session 23/Mar, committed 24/Mar)

Plans:
- [x] score_engine.py + sinaleiro_engine.py — Score 6 dim + P0-P7 + ABC + tipo_cliente + sinaleiro cores

### Phase 14: Agenda Inteligente
**Goal**: Cada consultor recebe uma lista diaria de 40-60 atendimentos priorizados por Score descending, filtravel por consultor, com export xlsx pronto para operar.
**Depends on**: Phase 13 (score e sinaleiro calculados para cada cliente)
**Requirements**: AGENDA-01, AGENDA-02, AGENDA-03, AGENDA-04
**Success Criteria** (what must be TRUE):
  1. O sistema gera lista de 40-60 atendimentos por consultor por dia, ordenada por Score descending
  2. Clientes P1 (URGENTE) aparecem sempre no topo, depois P2, P3, depois por Score dentro de cada faixa
  3. Operador filtra a agenda por consultor (LARISSA, MANU, JULIO, DAIANE) e ve apenas os clientes daquele territorio
  4. Export gera um arquivo xlsx por consultor com a agenda do dia, pronto para enviar via WhatsApp/email
**Plans**: 1/1 COMPLETE (built in session 23/Mar, committed 24/Mar)

Plans:
- [x] agenda_engine.py + excel_builder.py + run_pipeline.py + test_pipeline.py — Agenda 40-60/dia + xlsx 8 abas + 69 testes

### Phase 15: Projecao + Export
**Goal**: O sistema calcula realizado vs meta SAP por cliente e por mes, gera % alcancado trimestral e anual, exporta base processada para xlsx, e mostra resumo executivo no terminal.
**Depends on**: Phase 11 (dados importados com metas SAP)
**Requirements**: PROJ-01, PROJ-02, EXPORT-01, EXPORT-02
**Success Criteria** (what must be TRUE):
  1. Para cada cliente, o sistema mostra realizado vs meta SAP do mes atual e acumulado, com divergencia calculada
  2. % alcancado esta disponivel por trimestre (Q1-Q4) e anual, consolidado por consultor e por rede
  3. Base processada completa (com score, sinaleiro, motor, projecao) eh exportada para xlsx formatado com cores e filtros
  4. Resumo executivo eh impresso no terminal: KPIs principais (fat. total, % meta, top 10 clientes, alertas de churn)
**Plans**: 1/1 COMPLETE (2026-03-24)

Plans:
- [x] projecao_engine.py + pipeline integration — realizado vs meta SAP, dashboard terminal, 8 stages

## Progress

**Execution Order:**
Fases 11-15 executam sequencialmente: 11 -> 12 -> 13 -> 14 -> 15
(Fase 15 depende apenas de 11 para dados, pode rodar em paralelo com 13-14 se necessario.)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Projecao | v1.0 | 3/3 | Complete | 2026-02-17 |
| 2. Faturamento | v1.0 | 3/3 | Complete (FAIL_WITH_NOTES) | 2026-02-17 |
| 3. Timeline Mensal | v1.0 | 2/2 | Complete | 2026-02-17 |
| 4. LOG Completo | v1.0 | 4/4 | Complete | 2026-02-17 |
| 5. Dashboard | v1.0 | 3/3 | Complete | 2026-02-17 |
| 6. E-commerce | v1.0 | 2/2 | Complete | 2026-02-17 |
| 7. Redes e Franquias | v1.0 | 3/3 | Complete | 2026-02-17 |
| 8. Comite e Metas | v1.0 | 2/2 | Complete | 2026-02-17 |
| 9. Blueprint v2 | v1.0 | 6/6 | Complete | 2026-02-17 |
| 10. Validacao Final | v1.0 | 3/3 | Complete (V14 FINAL) | 2026-02-17 |
| 11. Import Pipeline | v2.0 | 2/2 | Complete | 2026-03-23 |
| 12. Motor de Regras | v2.0 | 1/1 | Complete | 2026-03-23 |
| 13. Score + Sinaleiro | v2.0 | 1/1 | Complete | 2026-03-23 |
| 14. Agenda Inteligente | v2.0 | 1/1 | Complete | 2026-03-23 |
| 15. Projecao + Export | v2.0 | 1/1 | Complete | 2026-03-24 |

---
*Roadmap created: 2026-02-15 via DEUS-AIOS*
*v1.0 complete: 10 phases, 31 plans, 43 requirements (2026-02-17)*
*v2.0 added: 2026-03-23 — 5 phases, 20 requirements*
*v2.0 phases 11-14 complete: 2026-03-23 (built) + 2026-03-24 (audited, committed)*
