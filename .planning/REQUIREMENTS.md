# Requirements: CRM VITAO360

**Defined:** 2026-02-15
**Core Value:** Cruzar dados de vendas, atendimentos e prospecção em CARTEIRA unificada com visibilidade total, sem fabricar dados ou duplicar valores financeiros.

## v1 Requirements

Requirements para o rebuild definitivo. Cada um mapeia para fases do roadmap.

### Projeção (CRÍTICO)

- [ ] **PROJ-01**: Aba PROJEÇÃO contém 18.180 fórmulas dinâmicas recalculáveis
- [ ] **PROJ-02**: Projeção mensal por cliente baseada em histórico de vendas real
- [ ] **PROJ-03**: Projeção consolida por consultor, ABC, status e região
- [ ] **PROJ-04**: Projeção 2026: R$ 5.7M projetado, 3.168 vendas, 3/dia/consultor

### Faturamento

- [ ] **FAT-01**: Faturamento mensal Jan-Dez 2025 bate com PAINEL (R$ 2.156.179 total)
- [ ] **FAT-02**: Divergência Mercos vs PAINEL ≤ 0.5% (gap atual: R$ 6.790 / 0.3%)
- [ ] **FAT-03**: Relatórios Mercos processados com armadilhas tratadas (Abril=Abr+Mai, etc.)
- [ ] **FAT-04**: Vendas por cliente mês a mês preenchidas na CARTEIRA (colunas Fat.Mensal)

### Timeline Mensal

- [ ] **TIME-01**: Vendas mês a mês por cliente preenchidas (Jan-Dez 2025)
- [ ] **TIME-02**: Dados cruzados entre Mercos (vendas) e SAP (mês a mês)
- [ ] **TIME-03**: Classificação ABC recalculada com base na timeline completa

### LOG

- [ ] **LOG-01**: LOG contém ≥ 11.758 registros (vs 1.581 atual = 13.4%)
- [ ] **LOG-02**: 10.484 registros do CONTROLE_FUNIL integrados com classificação 3-tier
- [ ] **LOG-03**: 5.329 tickets Deskrio integrados no LOG
- [ ] **LOG-04**: 3.540 contatos históricos retroativos integrados
- [ ] **LOG-05**: Two-Base Architecture respeitada: LOG sempre R$ 0.00
- [ ] **LOG-06**: Chave composta DATA + CNPJ + RESULTADO para dedup
- [ ] **LOG-07**: Julio Gadret presente no LOG (WhatsApp pessoal → dados manuais)

### Dashboard

- [ ] **DASH-01**: DASH redesenhada com 3 blocos compactos (~45 rows vs 164 atual)
- [ ] **DASH-02**: Bloco 1: Visão executiva (faturamento, vendas, atendimentos)
- [ ] **DASH-03**: Bloco 2: Performance por consultor
- [ ] **DASH-04**: Bloco 3: Pipeline e funil
- [ ] **DASH-05**: Fórmulas referenciam CARTEIRA e LOG corretamente

### E-commerce

- [ ] **ECOM-01**: Dados de e-commerce Mercos cruzados na CARTEIRA
- [ ] **ECOM-02**: Colunas de e-commerce (4 colunas) populadas para todos os clientes
- [ ] **ECOM-03**: Acesso ao e-commerce por mês (20 arquivos) processados

### Redes e Franquias

- [ ] **REDE-01**: REDE/REGIONAL preenchido para todos os 489 clientes
- [ ] **REDE-02**: #REF! corrigidos nas REDES_FRANQUIAS_v2
- [ ] **REDE-03**: Sinaleiro de penetração atualizado com dados 2025 completos
- [ ] **REDE-04**: Metas 6M por rede operacionais

### Comitê e Metas

- [ ] **META-01**: Metas 2026 do SAP integradas na CARTEIRA
- [ ] **META-02**: COMITÊ com visão consolidada por consultor vs meta
- [ ] **META-03**: Capacidade de atendimento validada (máx 40-50/dia/consultor)

### Blueprint v2

- [ ] **BLUE-01**: CARTEIRA expandida para 81 colunas com 8 grupos [+]
- [ ] **BLUE-02**: 10 colunas fixas (A-J) mantidas
- [ ] **BLUE-03**: 46 colunas originais IMUTÁVEIS preservadas
- [ ] **BLUE-04**: Grupos: Identificação, Vida Comercial, Timeline, Jornada, Ecommerce, SAP, Operacional, Comitê

### Validação Final

- [ ] **VAL-01**: 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?) em todas as abas
- [ ] **VAL-02**: Faturamento total bate com R$ 2.156.179
- [ ] **VAL-03**: Two-Base Architecture respeitada em 100% dos registros
- [ ] **VAL-04**: CNPJ sem duplicatas (14 dígitos, string, zfill)
- [ ] **VAL-05**: 14 abas presentes e funcionais
- [ ] **VAL-06**: Teste de abertura e recálculo no Excel real (não LibreOffice)

## v2 Requirements

Deferred para futuras versões. Trackeados mas não no roadmap atual.

### Automação

- **AUTO-01**: Script de import automático dos exports Mercos/SAP
- **AUTO-02**: Geração automática de DRAFT 1/2/3 a partir de novos exports
- **AUTO-03**: Atualização batch mensal do CRM via Python

### Relatórios Avançados

- **REL-01**: Relatório de performance temporal (trend analysis)
- **REL-02**: Predição de churn baseada em padrões de inatividade
- **REL-03**: Score de saúde do cliente

### Integração Julio

- **JUL-01**: Processo estruturado para Julio reportar via formulário/WhatsApp
- **JUL-02**: Pipeline separado para RCA externo

## Out of Scope

| Feature | Reason |
|---------|--------|
| Migração para web/SaaS | Sistema permanece Excel — Leandro opera nele diariamente |
| API integrations (Mercos/SAP) | Sem acesso a APIs — dados via export manual |
| Dark mode | Decisão do Leandro: tema LIGHT exclusivamente |
| App mobile | Consultores usam desktop |
| Integração ExactSales | Sistema foi descontinuado Out/2024 |
| Dados fabricados/alucinação | 558 registros já classificados como ALUCINAÇÃO — não integrar |
| IA/ML para predições | Fora do escopo v1 — foco em dados corretos primeiro |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROJ-01 | Phase 1 | Pending |
| PROJ-02 | Phase 1 | Pending |
| PROJ-03 | Phase 1 | Pending |
| PROJ-04 | Phase 1 | Pending |
| FAT-01 | Phase 2 | Pending |
| FAT-02 | Phase 2 | Pending |
| FAT-03 | Phase 2 | Pending |
| FAT-04 | Phase 2 | Pending |
| TIME-01 | Phase 3 | Pending |
| TIME-02 | Phase 3 | Pending |
| TIME-03 | Phase 3 | Pending |
| LOG-01 | Phase 4 | Pending |
| LOG-02 | Phase 4 | Pending |
| LOG-03 | Phase 4 | Pending |
| LOG-04 | Phase 4 | Pending |
| LOG-05 | Phase 4 | Pending |
| LOG-06 | Phase 4 | Pending |
| LOG-07 | Phase 4 | Pending |
| DASH-01 | Phase 5 | Pending |
| DASH-02 | Phase 5 | Pending |
| DASH-03 | Phase 5 | Pending |
| DASH-04 | Phase 5 | Pending |
| DASH-05 | Phase 5 | Pending |
| ECOM-01 | Phase 6 | Pending |
| ECOM-02 | Phase 6 | Pending |
| ECOM-03 | Phase 6 | Pending |
| REDE-01 | Phase 7 | Pending |
| REDE-02 | Phase 7 | Pending |
| REDE-03 | Phase 7 | Pending |
| REDE-04 | Phase 7 | Pending |
| META-01 | Phase 8 | Pending |
| META-02 | Phase 8 | Pending |
| META-03 | Phase 8 | Pending |
| BLUE-01 | Phase 9 | Pending |
| BLUE-02 | Phase 9 | Pending |
| BLUE-03 | Phase 9 | Pending |
| BLUE-04 | Phase 9 | Pending |
| VAL-01 | Phase 10 | Pending |
| VAL-02 | Phase 10 | Pending |
| VAL-03 | Phase 10 | Pending |
| VAL-04 | Phase 10 | Pending |
| VAL-05 | Phase 10 | Pending |
| VAL-06 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-15*
*Last updated: 2026-02-15 after initialization via DEUS-AIOS*
