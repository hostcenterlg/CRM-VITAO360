# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Motor Python funcional que roda localmente com dados reais, gerando agenda inteligente diaria para cada consultor a partir das 92 regras, Score, Sinaleiro e Projecao extraidos do Excel.

**Current focus:** ALL PHASES COMPLETE (11-15). Motor v2.0 com 8 stages operacional.

## Current Position

Phase: 15 of 15 — ALL COMPLETE
Plan: Done
Status: v2.0 Motor Operacional SaaS COMPLETE
Last activity: 2026-03-24 — Phase 15 projecao_engine + pipeline 8 stages

Progress: [##############################] 100% (v2.0) | 100% (v1.0)

## Previous Milestone (v1.0 — Excel Rebuild)
- 10 fases completas, 31 planos, 43 requisitos, 154.302 formulas
- V13->V43 iteracoes, planilha FINAL com 40 abas e 210K+ formulas
- Velocidade media: 12 min/plano, 6.3h total
- Entregue: 2026-02-17

## Current Milestone (v2.0 — Motor Operacional SaaS)

### Phase 11: Import Pipeline — COMPLETE
- 11-01: config + helpers + import_pipeline (committed 864e28f, 55f43c3)
- 11-02: classify + run_import + base_unificada.json (committed 539f3cf, 7b37658)
- QA fixes: config import-time crash, CNPJ agenda, path fix, try/finally (committed 2219c8c)

### Phase 12: Motor de Regras — COMPLETE (code built)
- motor_regras.py: 92 combinacoes, 9 dimensoes, 99.2% match
- Committed: 2219c8c

### Phase 13: Score + Sinaleiro — COMPLETE (code built)
- score_engine.py: 6 fatores ponderados, P0-P7, meta_balance
- sinaleiro_engine.py: VERDE/AMARELO/VERMELHO/ROXO + ABC + tipo_cliente
- Committed: 2219c8c

### Phase 14: Agenda Inteligente — COMPLETE (code built)
- agenda_engine.py: 40-60 atendimentos/dia, priorizados por Score
- excel_builder.py: xlsx final 8 abas, formatacao condicional
- run_pipeline.py: orquestrador 7 stages
- test_pipeline.py: 69 testes (0 FAIL)
- Committed: 2219c8c

### Phase 15: Projecao + Export — COMPLETE
- projecao_engine.py: carregar_metas_sap, calcular_projecao, consolidar_projecao, gerar_dashboard_terminal
- Pipeline upgraded: 7 → 8 stages (projecao entre score e agenda)
- Dashboard terminal ASCII com KPIs, top 10, churn alerts
- Committed: 4f2bae1

## Performance Metrics

**Velocity (v1.0 historico):**
- Total plans completed: 31
- Average duration: 12 min
- Total execution time: 6.30 hours

**Velocity (v2.0):**
- Plans completed: 2 (11-01, 11-02)
- Code built: phases 11-14 complete in single session (23/Mar)
- QA audit + 12 atomic commits: 24/Mar session

## Accumulated Context

### Decisions

- [v1.0]: Two-Base Architecture confirmada — R$ apenas em VENDA, nunca em LOG
- [v1.0]: CNPJ string 14 digitos como chave primaria universal
- [v1.0]: Planilha FINAL tem 40 abas, 210K+ formulas, 263 colunas na CARTEIRA
- [v2.0]: Motor Python extrai inteligencia do Excel — nao substitui a planilha
- [v2.0]: Regras configuraveis (JSON/YAML), nao hardcoded
- [v2.0]: Pesos do Score configuraveis externamente
- [v2.0]: Projecao 2026 = R$ 3.377.120 (PAINEL CEO — fonte auditada)
- [v2.0]: Score pesos = 9 DIM (FASE 25%, SINALEIRO 20%, ABC 20%, TEMP 15%, TIPO 10%, TENT 10%) — configuraveis
- [11-01]: Tab names usam nomes exatos da radiografia com acentos e espacos trailing
- [11-01]: Header rows variam por aba (CARTEIRA=3, OPERACIONAL=2, SINALEIRO=4)
- [11-01]: CNPJ normalizado com NaN->None explicito para prevenir float leakage
- [11-01]: HELDER BRUNKOW (41 clientes) -> DESCONHECIDO (nao esta no DE-PARA)
- [24/Mar]: config.py FileNotFoundError movido de import-time para runtime (validar_caminho_planilha)
- [24/Mar]: agenda_engine CNPJ corrigido para usar normalizar_cnpj do helpers
- [24/Mar]: .gitignore atualizado: .cache/, phase10 xlsx, backups excluidos

### Pending Todos

- Phase 15: Projecao + Export (unica fase restante)
- Testar CRM_VITAO360_MOTOR_v1.xlsx no Excel real (LibreOffice nao recalcula XLOOKUP)
- DRAFT 2 populado (6.772 registros) nao integrado na base ainda
- Motor coverage: 238/1581 clientes com resultado preenchido (maioria PROSPECT/INAT)

### Blockers/Concerns

- Planilha FINAL (40 abas) eh a fonte de dados — VALIDADA, acessivel
- openpyxl data_only=True: DRAFT 2 e RNC retornam 0 rows (formulas nao cached)
- DE-PARA vendedores: RESOLVIDO. HELDER BRUNKOW (41) = DESCONHECIDO.

## Session Continuity

Last session: 2026-03-24
Stopped at: 12 commits atomicos completos, QA audit PASS, STATE atualizado
Resume file: SESSAO_RETOMAR.md
