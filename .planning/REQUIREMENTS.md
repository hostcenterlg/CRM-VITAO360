# Requirements: CRM VITAO360 — Motor Operacional SaaS

**Defined:** 2026-03-23
**Core Value:** Motor Python funcional que roda localmente com dados reais, gerando agenda inteligente diaria para cada consultor

## v2.0 Requirements

### Import de Dados
- [ ] **IMPORT-01**: Importar planilha FINAL (40 abas) e extrair base de clientes
- [ ] **IMPORT-02**: Normalizar CNPJ (14 digitos, string, zero-padded)
- [ ] **IMPORT-03**: Classificar dados como REAL/SINTETICO/ALUCINACAO
- [ ] **IMPORT-04**: Aplicar DE-PARA vendedores

### Motor de Regras
- [ ] **MOTOR-01**: Sistema aplica 92 combinacoes SITUACAO x RESULTADO e retorna 9 dimensoes
- [ ] **MOTOR-02**: Tabela de regras eh configuravel (JSON/YAML, nao hardcoded)
- [ ] **MOTOR-03**: Dado um atendimento (CNPJ + RESULTADO), motor calcula Estagio Funil, Fase, Tipo Contato, Acao Futura, Temperatura

### Score Ranking
- [ ] **SCORE-01**: Cada cliente recebe score 0-100 com 6 fatores ponderados (URG 30%, VAL 25%, FU 20%, SIN 15%, TENT 5%, SIT 5%)
- [ ] **SCORE-02**: Score gera Piramide P1-P7 automaticamente
- [ ] **SCORE-03**: Pesos configuraveis (nao hardcoded)

### Sinaleiro
- [ ] **SINAL-01**: Cada cliente recebe cor sinaleiro (ROXO/VERDE/AMARELO/LARANJA/VERMELHO) baseado em dias vs ciclo
- [ ] **SINAL-02**: Cadencia de contato derivada do sinaleiro

### Agenda Inteligente
- [ ] **AGENDA-01**: Gerar lista 40-60 atendimentos por consultor por dia, ordenada por Score desc
- [ ] **AGENDA-02**: Prioridade P1 sempre no topo, depois P2, P3, depois Score
- [ ] **AGENDA-03**: Filtro por consultor (LARISSA, MANU, JULIO, DAIANE)
- [ ] **AGENDA-04**: Export da agenda para xlsx por consultor

### Projecao e Export
- [ ] **PROJ-01**: Calcular realizado vs meta SAP por cliente por mes
- [ ] **PROJ-02**: Calcular % alcancado (trimestral e anual)
- [ ] **EXPORT-01**: Exportar base processada para xlsx
- [ ] **EXPORT-02**: Gerar relatorio resumo em terminal

## v3.0 Requirements (Futuro)

### Integracoes
- **INTEG-01**: Scripts "Siga-me" para SAP
- **INTEG-02**: Scripts "Siga-me" para Mercos
- **INTEG-03**: API Deskrio (WhatsApp bidirecional)
- **INTEG-04**: API Asana (leads do site)

### IA
- **IA-01**: Agente Priorizador
- **IA-02**: Agente Preditor (churn)
- **IA-03**: Agente CS automatico
- **IA-04**: Agente WhatsApp contextual

## Out of Scope

| Feature | Reason |
|---------|--------|
| Frontend web | Motor Python primeiro |
| API REST | Rodar local primeiro |
| WhatsApp bot | Fase 3 — depende Deskrio API |
| Dashboard web | Terminal primeiro |
| Multi-tenant | Solo operator |
| Dark mode | NUNCA — regra LIGHT |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| IMPORT-01 | Phase 11 | Pending |
| IMPORT-02 | Phase 11 | Pending |
| IMPORT-03 | Phase 11 | Pending |
| IMPORT-04 | Phase 11 | Pending |
| MOTOR-01 | Phase 12 | Pending |
| MOTOR-02 | Phase 12 | Pending |
| MOTOR-03 | Phase 12 | Pending |
| SCORE-01 | Phase 13 | Pending |
| SCORE-02 | Phase 13 | Pending |
| SCORE-03 | Phase 13 | Pending |
| SINAL-01 | Phase 13 | Pending |
| SINAL-02 | Phase 13 | Pending |
| AGENDA-01 | Phase 14 | Pending |
| AGENDA-02 | Phase 14 | Pending |
| AGENDA-03 | Phase 14 | Pending |
| AGENDA-04 | Phase 14 | Pending |
| PROJ-01 | Phase 15 | Pending |
| PROJ-02 | Phase 15 | Pending |
| EXPORT-01 | Phase 15 | Pending |
| EXPORT-02 | Phase 15 | Pending |

**Coverage:** 20/20 requirements mapped, 0 unmapped

---
*Requirements defined: 2026-03-23*
*Traceability updated: 2026-03-23 (roadmap v2.0 created)*
