# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-23)

**Core value:** Motor Python funcional que roda localmente com dados reais, gerando agenda inteligente diaria para cada consultor a partir das 92 regras, Score, Sinaleiro e Projecao extraidos do Excel.

**Current focus:** Phase 11 Import Pipeline — primeira fase do milestone v2.0 Motor Operacional SaaS

## Current Position

Phase: 11 of 15 (Import Pipeline)
Plan: 1 of 2 in current phase
Status: Executing
Last activity: 2026-03-23 — 11-01-PLAN.md completo (config + helpers + import pipeline)

Progress: [#####░░░░░░░░░░░░░░░░░░░░░░░░░] 10% (v2.0) | 100% (v1.0)

## Previous Milestone (v1.0 — Excel Rebuild)
- 10 fases completas, 31 planos, 43 requisitos, 154.302 formulas
- V13->V43 iteracoes, planilha FINAL com 40 abas e 210K+ formulas
- Velocidade media: 12 min/plano, 6.3h total
- Entregue: 2026-02-17

## Performance Metrics

**Velocity (v1.0 historico):**
- Total plans completed: 31
- Average duration: 12 min
- Total execution time: 6.30 hours

**Velocity (v2.0):**
- Plans completed: 1
- 11-01: 8 min (2 tasks, 4 files)

*Metricas v2.0 atualizadas conforme planos sao completados*

## Accumulated Context

### Decisions

- [v1.0]: Two-Base Architecture confirmada — R$ apenas em VENDA, nunca em LOG
- [v1.0]: CNPJ string 14 digitos como chave primaria universal
- [v1.0]: Planilha FINAL tem 40 abas, 210K+ formulas, 263 colunas na CARTEIRA
- [v2.0]: Motor Python extrai inteligencia do Excel — nao substitui a planilha
- [v2.0]: Regras configuraveis (JSON/YAML), nao hardcoded
- [v2.0]: Pesos do Score configuraveis externamente
- [11-01]: Tab names usam nomes exatos da radiografia com acentos e espacos trailing
- [11-01]: Header rows variam por aba (CARTEIRA=3, OPERACIONAL=2, SINALEIRO=4)
- [11-01]: CNPJ normalizado com NaN->None explicito para prevenir float leakage
- [11-01]: HELDER BRUNKOW (41 clientes) -> DESCONHECIDO (nao esta no DE-PARA)

### Pending Todos

None yet.

### Blockers/Concerns

- Planilha FINAL (40 abas) eh a fonte de dados — VALIDADA, acessivel, lida em ~7s
- 558 registros ALUCINACAO devem ser excluidos no import (R8 do projeto) — PENDENTE para 11-02
- openpyxl data_only=True: DRAFT 2 e RNC retornam 0 rows (formulas nao cached). Se necessario, re-salvar no Excel primeiro.
- DE-PARA vendedores: RESOLVIDO, todos alias mapeados. HELDER BRUNKOW (41) = DESCONHECIDO.

## Session Continuity

Last session: 2026-03-23
Stopped at: Completed 11-01-PLAN.md (config + helpers + import pipeline). Proximo: 11-02-PLAN.md
Resume file: .planning/phases/11-import-pipeline/11-01-SUMMARY.md
