# BRIEFING: Rebuild DDE + Análise Crítica — PÁGINAS ERRADAS

> **Data:** 29/Abr/2026
> **De:** Cowork (professor/revisor)
> **Para:** VSCode executor
> **Prioridade:** ALTA — Leandro disse "não representam o que realmente são, está péssimo"
> **Natureza:** DELETE + REBUILD — não é fix, é reescrita total

---

## O PROBLEMA

As duas páginas estão **conceitualmente erradas**. Não é ajuste CSS — é conteúdo falso no lugar errado.

### DDE (`/gestao/dde/page.tsx` — 328 linhas, TRUNCADO)

**O que mostra hoje:**
- Página de "status de projeto" com checklist de 6 tasks (3 done, 3 pending)
- Barra de progresso 50%
- Card de "Previsão de Entrega" (Sprint, Estimativa, etc.)
- Tabela P&L com **R$ 1.250.000 de um cliente FICTÍCIO** — 23 linhas hardcoded
- Tudo com badge "EM CONSTRUÇÃO" piscando
- **ARQUIVO TRUNCADO** — cortado na linha 328 no meio da palavra "ilust..."
- Nem compila.

**O que DEVERIA ser (per SPEC_DDE_CASCATA_REAL.md):**
- Cascata P&L real por cliente
- 25 linhas, 7 blocos, dados do BANCO
- Não é uma página autônoma em `/gestao/dde` — é uma **aba "ANÁLISE" dentro do detalhe do cliente** (`/clientes/[cnpj]`)
- Linhas sem dados = `░░░ Aguardando [fonte]` marcadas como PENDENTE
- Score + Veredito automático (SAUDÁVEL / REVISAR / RENEGOCIAR / SUBSTITUIR)
- Endpoint: `GET /api/dde/cliente/{cnpj}?ano=2025`

### Análise Crítica (`/gestao/analise-critica/page.tsx` — 338 linhas, TRUNCADO)

**O que mostra hoje:**
- Banner "BLOQUEADO — aguarda DDE"
- Score fictício 78/100 com gauge SVG
- Veredito "SAUDÁVEL" hardcoded
- 2 anomalias inventadas
- 5 ações priorizadas com impactos R$ fabricados
- 9 KPIs hardcoded (margem 29.4%, comissão 2.5%, etc.)
- **ARQUIVO TRUNCADO** na linha 338
- Nem compila.

**O que DEVERIA ser (per SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md):**
- DDE + diagnóstico + sinaleiro + recomendação acionável + impacto R$
- Cada cliente: 1 página com DECISÃO, não dashboard
- Score, veredito, 3 anomalias, 5 ações priorizadas
- Botão "Gerar Resumo CEO" (PDF 1 página)
- Depende da engine DDE estar conectada

---

## AÇÃO: REBUILD EM 3 FASES

### FASE 1: LIMPAR (30 min)

1. **Deletar** `frontend/src/app/gestao/dde/page.tsx` e `layout.tsx`
2. **Deletar** `frontend/src/app/gestao/analise-critica/page.tsx` e `layout.tsx`
3. **Atualizar Sidebar.tsx:** manter os links mas mudar:
   - DDE → link para `/gestao/dde` COM badge "EM CONSTRUÇÃO" (mantém visibilidade pra diretoria)
   - Análise Crítica → link para `/gestao/analise-critica` COM badge "BLOQUEADO"
4. Commit: `fix: remove truncated DDE + Analise Critica placeholder pages`

### FASE 2: DDE — PÁGINA HONESTA (2-3h)

Criar `/gestao/dde/page.tsx` com conteúdo **honesto** — mostra o que o DDE É, não fake data.

**Estrutura da nova página:**

```
┌─────────────────────────────────────────────────────────────┐
│  DDE — Demonstração de Desempenho Econômico                  │
│  [EM CONSTRUÇÃO]                                             │
│                                                              │
│  ┌─ O QUE É ──────────────────────────────────────────────┐  │
│  │ DDE é a cascata P&L por cliente. Responde:              │  │
│  │ "Esse cliente dá lucro ou prejuízo pra Vitao?"          │  │
│  │                                                          │  │
│  │ Receita Bruta → Deduções → CMV → Despesas Variáveis     │  │
│  │ → Rateio → Resultado = Margem de Contribuição            │  │
│  │                                                          │  │
│  │ Cada linha tem dado REAL rastreável a fonte (SAP,        │  │
│  │ Sales Hunter, LOG upload). Nada inventado.               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ ESTRUTURA DA CASCATA ─────────────────────────────────┐  │
│  │                                                          │  │
│  │  BLOCO 1: Receita Bruta                                  │  │
│  │    L1  Faturamento bruto a tabela        ✅ DB           │  │
│  │    L2  IPI sobre vendas                  ⚠️ PENDENTE     │  │
│  │    L3  = Receita Bruta com IPI           ⚠️ CALC         │  │
│  │                                                          │  │
│  │  BLOCO 2: Deduções da Receita                            │  │
│  │    L4  (-) Devoluções                    ✅ DB           │  │
│  │    L5  (-) Desconto comercial            ⚠️ PENDENTE     │  │
│  │    L6  (-) Desconto financeiro           ⚠️ PENDENTE     │  │
│  │    L7  (-) Bonificações                  ⚠️ PENDENTE     │  │
│  │    L8  (-) IPI faturado                  ⚠️ PENDENTE     │  │
│  │    L9  (-) ICMS                          🔜 SAP          │  │
│  │    L10 (-) PIS/COFINS/ICMS-ST            🔜 SAP          │  │
│  │    L11 = Receita Líquida                 ⚠️ PARCIAL      │  │
│  │                                                          │  │
│  │  BLOCO 3: CMV                                            │  │
│  │    L12 (-) CMV                           🔜 SAP/SH       │  │
│  │    L13 = Margem Bruta                    ❌ BLOQUEADO    │  │
│  │                                                          │  │
│  │  BLOCO 4: Despesas Variáveis                             │  │
│  │    L14 (-) Frete CT-e                    ⚠️ SCHEMA OK    │  │
│  │    L15 (-) Comissão                      ⚠️ CALC         │  │
│  │    L16 (-) Verbas                        ⚠️ SCHEMA OK    │  │
│  │    L17 (-) Promotor PDV                  ⚠️ SCHEMA OK    │  │
│  │    L18 (-) Rebate                        ❓ ABERTO       │  │
│  │    L19 (-) Inadimplência                 ✅ DB           │  │
│  │    L20 (-) Custo financeiro              ⚠️ CALC         │  │
│  │    L21 = Margem Contribuição             ⚠️ PARCIAL      │  │
│  │                                                          │  │
│  │  BLOCO 5-6: Rateio + Encargos            🔜 FASE B      │  │
│  │  BLOCO 7: Indicadores + Score            ⚠️ PARCIAL      │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ ROADMAP DE DADOS ────────────────────────────────────┐   │
│  │                                                          │  │
│  │  Fase A (agora): Cascata comercial — dados Sales Hunter  │  │
│  │    ✅ Faturamento, Devoluções, Inadimplência             │  │
│  │    ⚠️ Descontos, Bonificações, IPI (campo existe, falta  │  │
│  │       persistir no ingest)                               │  │
│  │    ⚠️ Frete, Verbas, Promotor (schema pronto, falta      │  │
│  │       parser de upload)                                  │  │
│  │                                                          │  │
│  │  Fase B (SAP): Impostos reais + CMV + Margem Bruta       │  │
│  │    🔜 Depende de acesso ao módulo fiscal SAP              │  │
│  │                                                          │  │
│  │  Fase C (BI): Sell-out, ruptura, giro de estoque          │  │
│  │    🔜 Depende de integração POS futura                    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ QUANDO FICA PRONTO ──────────────────────────────────┐   │
│  │  Fase A: ~5 dias dev após aprovação D1-D6               │  │
│  │  Aparece como aba "ANÁLISE" dentro de cada cliente       │  │
│  │  Score + Veredito automático por CNPJ                    │  │
│  │  Comparativo cross-cliente em 1 clique                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Regras visuais:**
- ✅ = verde (#00B050) — dado disponível no banco
- ⚠️ = amarelo (#FFC000) — dado existe na fonte mas falta integrar
- 🔜 = cinza — depende de fonte externa (SAP, BI)
- ❌ = vermelho — bloqueado por dependência
- ❓ = azul — decisão pendente (D1-D6)
- **ZERO valores R$** — nenhum número financeiro na página
- **ZERO dados de cliente** — nenhum CNPJ, nenhum nome
- Texto explicativo sobre O QUE É o DDE, não dados mockados
- Tema LIGHT, fonte Inter, cores R9

### FASE 3: ANÁLISE CRÍTICA — PÁGINA HONESTA (1-2h)

Criar `/gestao/analise-critica/page.tsx` — explica o que é, sem fabricar dados.

**Estrutura da nova página:**

```
┌─────────────────────────────────────────────────────────────┐
│  Análise Crítica do Cliente                                  │
│  [BLOQUEADO — aguarda DDE]                                   │
│                                                              │
│  ┌─ O QUE É ──────────────────────────────────────────────┐  │
│  │ A Análise Crítica transforma o que hoje leva             │  │
│  │ 30-45 minutos de trabalho manual em 2 segundos.          │  │
│  │                                                          │  │
│  │ Para cada cliente, combina:                               │  │
│  │ • DDE (cascata P&L) = os números                         │  │
│  │ • Diagnóstico automático = as anomalias                  │  │
│  │ • Veredito = a decisão (SAUDÁVEL/RENEGOCIAR/SUBSTITUIR)  │  │
│  │ • Ações priorizadas = o que fazer, com impacto R$        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ ARQUITETURA EM 6 CAMADAS ────────────────────────────┐   │
│  │                                                          │  │
│  │  6. INTERFACE ← esta aba                                 │  │
│  │  5. LLM (Resumo CEO) — pós-cálculo, nunca substitui     │  │
│  │  4. ENGINE DE REGRAS (DDE) ← motor Python determinístico │  │
│  │  3. POSTGRESQL (9 tabelas) ← modelo da verdade           │  │
│  │  2. PIPELINE DE INGESTÃO ← ETL mensal + diário           │  │
│  │  1. FONTES DE DADOS (8 fontes) ← SAP, SH, Mercos, LOG   │  │
│  │                                                          │  │
│  │  Status: Camadas 1-3 parcialmente prontas.                │  │
│  │  Camada 4 (DDE engine) é o próximo passo.                 │  │
│  │  Camadas 5-6 dependem de 4.                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ O QUE VAI APARECER ──────────────────────────────────┐   │
│  │                                                          │  │
│  │  Ao abrir um cliente:                                     │  │
│  │                                                          │  │
│  │  1. SCORE (0-100) com gauge visual                        │  │
│  │     Composto de 8 indicadores: margem, devolução,         │  │
│  │     inadimplência, comissão, frete, verba, aging, ciclo   │  │
│  │                                                          │  │
│  │  2. VEREDITO automático baseado em regras Python           │  │
│  │     • SAUDÁVEL — margem >15%, crédito OK                  │  │
│  │     • REVISAR — margem 5-15%                              │  │
│  │     • RENEGOCIAR — margem <5%                             │  │
│  │     • SUBSTITUIR — margem negativa                        │  │
│  │     • ALERTA_CRÉDITO — margem OK mas aging >90d           │  │
│  │                                                          │  │
│  │  3. ANOMALIAS DETECTADAS (top 3)                          │  │
│  │     Regras determinísticas: verba caiu, frete sem CT-e,   │  │
│  │     margem negativa, devolução alta, etc.                  │  │
│  │                                                          │  │
│  │  4. AÇÕES PRIORIZADAS (top 5)                             │  │
│  │     Cada ação com impacto R$ estimado                     │  │
│  │     Ex: "Renegociar contrato" → +R$ X.XXX/mês            │  │
│  │                                                          │  │
│  │  5. RESUMO CEO (1 página PDF)                             │  │
│  │     Gerado por LLM a partir dos dados calculados          │  │
│  │     (não inventa — explica o que a engine calculou)        │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ DEPENDÊNCIAS ────────────────────────────────────────┐   │
│  │  ❌ DDE Engine (Fase A) — pré-requisito                  │  │
│  │  ❌ 5 endpoints API — routes_dde.py                      │  │
│  │  ❌ Parser uploads CFO (frete, verba, contrato, promotor)│  │
│  │  ✅ Schema PostgreSQL — definido nas specs               │  │
│  │  ✅ Motor de regras base — 92 regras existentes           │  │
│  │  ✅ Sinaleiro service — já existe                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Regras:**
- **ZERO dados financeiros** — nenhum R$ na página
- **ZERO nomes de clientes** — nenhum CNPJ, nenhum nome
- Texto explicativo sobre O QUE a feature faz
- Lista de dependências com status real (✅/❌)
- Nenhum mockup, nenhum gauge, nenhum KPI card com valor
- Pra diretoria entender o que está sendo construído SEM ver dados falsos

---

## REGRA DE NEGÓCIO: SCOPING POR CANAL (APROVADA 29/Abr — Leandro)

DDE e Análise Crítica **NÃO atendem todos os canais**. Só fazem sentido para clientes com massa de dados suficiente (contrato, verba, frete CT-e, promotor, volume).

| Canal | Elegível? | Motivo |
|-------|-----------|--------|
| **DIRETO** | ✅ SIM — prioridade | Manu, Larissa, Daiane, Julio — dados completos |
| **INDIRETO** | ✅ SIM — prioridade | Distribuidores com contrato e verba |
| **FOOD_SERVICE** | ⚠️ MÁXIMO | Somente se tiver dados estruturados |
| INTERNO | ❌ NÃO | Funcional VITAO, não é cliente externo |
| FARMA | ❌ NÃO | Sem massa de dados pra cascata |
| BODY | ❌ NÃO | Sem massa de dados |
| DIGITAL | ❌ NÃO | E-commerce/B2C, modelo diferente |

**Implementação:**
- Endpoints `/api/dde/*` DEVEM filtrar por `canal.nome IN ('DIRETO', 'INDIRETO', 'FOOD_SERVICE')`
- Frontend: se cliente pertence a canal inelegível → mostrar card: "Análise DDE indisponível para este canal. Disponível para clientes Direto e Indireto."
- NÃO gerar cascata vazia — melhor não mostrar do que mostrar com tudo NULL
- Nas páginas `/gestao/dde` e `/gestao/analise-critica`, mencionar que a feature atende canais Direto e Indireto

---

## DECISÕES L3 (LEANDRO PRECISA APROVAR)

| # | Decisão | Impacto |
|---|---------|---------|
| D1 | Persistir 4 campos do Sales Hunter no Cliente (desc_comercial_pct, desc_financeiro_pct, total_bonificacao, ipi_total) | Desbloqueia L5-L8 da cascata |
| D2 | Criar `routes_dde.py` com 5 endpoints | Desbloqueia conexão frontend-backend |
| D3 | Linhas de imposto sem dado real: NULL honesto ou alíquota sintética? | Recomendação: NULL |
| D4 | Implementar Fase A agora sem esperar SAP? | Recomendação: GO |
| D5 | `produtos.comissao_pct` é comissão vendedor ou rebate cliente? | Afeta L18 vs L7 |
| D6 | Baixar `RelatorioDeMargemPorProduto` (P2) do Sales Hunter — tem custo unitário? | Se sim, desbloqueia CMV (L12) |

---

## CHECKLIST ANTI-R8 (DETECTOR DE MENTIRA)

Antes de commitar qualquer rebuild:

- [ ] ZERO valores R$ hardcoded nas páginas
- [ ] ZERO CNPJs ou nomes de clientes
- [ ] ZERO arrays de dados mockados (CASCATA, KPIS, ACOES, etc.)
- [ ] Nenhuma tabela com números financeiros
- [ ] Nenhum gauge/score com valor fixo
- [ ] Nenhum percentual de margem, comissão, frete, etc.
- [ ] Texto é EXPLICATIVO sobre a feature, não DEMONSTRATIVO com dados falsos
- [ ] Arquivo .tsx completo (não truncado) — exporta componente corretamente
- [ ] RequireRole mantido (mínimo GERENTE)
- [ ] Fontes mínimo text-xs (12px), sem text-[10px] ou text-[11px]
- [ ] Contraste WCAG AA (text-gray-500 mínimo sobre fundo branco)
- [ ] Tema LIGHT exclusivamente

---

## REFERÊNCIAS

| Doc | Path | O que contém |
|-----|------|-------------|
| SPEC DDE Cascata Real | `docs/specs/cowork/SPEC_DDE_CASCATA_REAL.md` | Spec definitiva: 25 linhas, 7 blocos, fontes, schema, endpoints, fases |
| SPEC Análise Crítica | `docs/specs/cowork/SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md` | Spec completa: 6 camadas, 8 fontes, 9 tabelas, engine, pipeline |
| Briefing UI Aba Análise | `docs/specs/cowork/BRIEFING_UI_ABA_ANALISE_CRITICA.md` | Wireframe ASCII da aba que vai dentro de `/clientes/[cnpj]` |
| SPEC DDE v0 (substituída) | `docs/specs/SPEC_DDE_CLIENTE.md` | Versão anterior — dashboard de métricas (SUPERSEDED pela cascata) |

---

*Briefing gerado por Cowork · 29/Abr/2026 · Revisão professor/revisor*
