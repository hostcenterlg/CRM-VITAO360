# ROADMAP COWORK — Consolidação 3 specs (28/abr/2026)

> **Autor:** Claude (analista) · **Data consolidação:** 28/abr/2026
> **Specs originais:** `SPEC_ANALISE_CRITICA_VIVA.md`, `SPEC_DDE_CLIENTE.md`, `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md`
> **Origem:** Cowork (consultor externo)
> **Status:** Roadmap acionável — aguardando decisões L3 do Leandro
> **Escopo:** Apenas síntese e ordenação. Nada implementado.

---

## 0. RELAÇÃO ENTRE OS 3 SPECS (declarada pelo próprio autor)

O spec `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md` (o mais novo, 28/abr 17:38) declara explicitamente na seção 15:

> "**SPEC_DDE_CLIENTE.md** → SUPERSEDED por esta spec."
> "**SPEC_ANALISE_CRITICA_VIVA.md** → SUPERSEDED. Era um dashboard de métricas, não uma análise real."

Isto é, o terceiro arquivo (`SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md`) **substitui formalmente** os outros dois. Os dois primeiros são iterações anteriores do mesmo conceito (DRE/análise de cliente), evoluindo:

1. **`SPEC_ANALISE_CRITICA_VIVA.md` (v1, 11:49):** dashboard de métricas com 7 dimensões, score composto, plano de ação por regras IF/THEN. Foco: **dashboard**.
2. **`SPEC_DDE_CLIENTE.md` (v2, 13:22):** evoluiu para cascata P&L real (Receita → Margem → Resultado). Foco: **DDE financeira**.
3. **`SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md` (v3, 17:38):** consolida tudo + acrescenta param SAP vs efetivado, sinaleiro SKU, anomalias, comparativo cross-cliente, RH (Resumo CEO). Foco: **decisão acionável**.

**Implicação prática:** o trabalho real é o spec v3. Os v1 e v2 servem de referência para fórmulas e endpoints já mapeados (especialmente os que já têm dado em DB). Não duplicam trabalho — somam contexto.

---

## 1. TABELA EXECUTIVA

| Spec | Objetivo (1 linha) | Esforço total | Risco | Pré-requisito | Status implementação |
|------|---------------------|---------------|-------|----------------|----------------------|
| **v1 — Análise Crítica Viva** | Dashboard 7 dimensões + score por cliente | M (~6-8h) | BAIXO | Dados DB atuais | SUPERSEDED — usar como referência |
| **v2 — DDE Cliente** | Cascata P&L (Receita → Margem → Resultado) parcial com dados de hoje | M (~4h Fase A) + L (Fases B-C) | MÉDIO | Phase 3+5 ingest_sales_hunter | SUPERSEDED — usar como referência |
| **v3 — Análise Crítica (FEATURE)** | DRE param SAP vs efetivado + sinaleiro SKU + anomalias + Resumo CEO | XL (~5 sprints, ~10 semanas) | ALTO | 6 novas tabelas + parsers Excel + LLM ativo (Sprint 4+) | SPEC ATIVA — implementar este |

**Esforço consolidado v3 (referência do próprio spec):**

| Sprint | Conteúdo | Estimativa autor | Reavaliação | Risco |
|--------|----------|------------------|-------------|-------|
| Sprint 1 — MVP | 6 tabelas + parsers + engine DRE + UI 1 página | "2 semanas" | **L (12-30h)** real | MÉDIO |
| Sprint 2 — Mercado | mercado_sku_preco + crawler + veredito + LLM Resumo CEO | "2 semanas" | **L** | MÉDIO-ALTO (crawler externo, LLM) |
| Sprint 3 — Cross-cliente | Comparativo + anomalia inteligente LLM + histórico | "2 semanas" | **M** | MÉDIO |
| Sprint 4 — Automação | ETL cron + notificações + workflow anomalia | "2 semanas" | **M** | BAIXO-MÉDIO |
| Sprint 5 — Acabamento | Chat com aba (RAG) + PDF Resumo CEO + snapshot mensal | "indef." | **L** | ALTO (RAG + LLM intenso) |

---

## 2. SUMÁRIO DETALHADO POR SPEC

### 2.1 SPEC_ANALISE_CRITICA_VIVA.md (v1, 19.6 KB)

**Objetivo:** Mostrar análise financeira por cliente em 7 dimensões (Sell-in, Sell-out, Verba conquista, Verba gerada, Verba devida, Conta corrente, Pagamentos) + Mix produtos + Score 0-10 + plano de ação IF/THEN.

**Escopo backend:**
- Novo router: `backend/app/routes/routes_analise_critica.py`
- 7 endpoints: `/api/clientes/{cnpj}/analise-critica` + 6 sub-rotas (sell-in, sell-out, verbas, conta-corrente, mix-produtos, score)
- **NOVO modelo:** `VerbaCliente` (tabela `verbas_clientes`) — proposto mas dependente de SAP
- Sem migrations agressivas: 5/7 dimensões usam tabelas atuais (`clientes`, `vendas`, `venda_itens`, `produtos`, `debitos_clientes`)
- Cálculos derivados em SQL agregadores (SUM, AVG, GROUP BY)

**Escopo frontend:**
- `frontend/src/pages/ClienteDetalhe/AnaliseCritica.tsx`
- 7 cards (1 por dimensão) + gráfico tendência (recharts) + tabela títulos + cross-sell + score gauge
- Cards de verba mostram "Aguardando dados SAP" quando `null`

**Dependências:**
- Phase A (5/7 dimensões): nenhuma — implementável **HOJE**
- Phase B (verbas): depende SAP + Sales Hunter relatório de bonificação
- Phase C (sell-out real): depende BI futuro

**Esforço:** Autor estima "2-3 horas" para Phase A. Reavaliação realista: **M (4-8h)** considerando testes + frontend + canal scoping.

**Decisões L3:**
1. Criar `verbas_clientes` agora (schema sem dados) ou esperar SAP? — Resposta padrão CRM: esperar (R8 — não fabricar).
2. `produtos.comissao_pct` é comissão vendedor ou rebate cliente?
3. Implementar Phase A agora ou esperar SAP completo?

**Risco:** BAIXO. 5/7 dimensões já têm dados confiáveis. Two-Base respeitada (todos valores são VENDA-side).

**LLM:** spec menciona "Versão 2: LLM gera texto natural a partir das métricas (Onda IA)". **Sprint 4+ — depende de ativação LLMClient (Tipo A). NÃO implementar agora.**

---

### 2.2 SPEC_DDE_CLIENTE.md (v2, 23 KB)

**Objetivo:** Cascata P&L completa por cliente: Receita Bruta → Receita Líq. Comercial → Receita Líq. Fiscal → Margem Bruta → Margem de Contribuição → Resultado. **Substitui o dashboard v1 por uma DDE financeira real.**

**Escopo backend:**
- Novo router: `backend/app/routes/routes_dde.py`
- 5 endpoints: `/dde`, `/dde/receita`, `/dde/conta-corrente`, `/dde/mix`, `/dde/score`
- **MIGRATION OBRIGATÓRIA Fase A** — 4 colunas no modelo `Cliente`:
  - `desc_comercial_pct` (Float)
  - `desc_financeiro_pct` (Float)
  - `total_bonificacao` (Float)
  - `ipi_total` (Float)
- **Alteração no `ingest_sales_hunter.py`:**
  - Phase 3: extrair cols 7, 8, 16, 22 do fat_cliente (descontos % e bonificação separada)
  - Phase 5: extrair col 19 (IPI) do pedidos_produto, somar por CNPJ
- **Migrations futuras (Fases B/C):**
  - Adicionar `custo_unitario` em `produtos`
  - Adicionar `cmv_unitario`, `cmv_total` em `venda_itens`
  - Criar `impostos_nf` (cnpj, nro_nfe, icms, pis, cofins, ipi)
  - Criar `verbas_clientes` (mesmo schema do v1)

**Escopo frontend:**
- `frontend/src/pages/ClienteDetalhe/DDE.tsx`
- Layout em **cascata financeira** (não cards soltos): cada linha subtrai a anterior
- Linhas sem dados em cinza itálico ("aguardando SAP")
- Barra de progresso "DDE 45% completa — faltam: CMV, impostos, frete, verbas"

**Dependências:**
- Fase A (Receita Líq. Comercial + IPI + Conta Corrente + Mix): mexe no `ingest_sales_hunter.py` — **risco de regressão na ingestão**
- Fase B (Margem Bruta + Margem de Contribuição): depende SAP MM (custo) + SAP FI (impostos) + relatório fiscal NF-e
- Fase C (DDE completa): depende TMS (frete R$) + SAP CO (verbas) + BI (sell-out)

**Esforço:** Autor estima "~4h Fase A". Reavaliação realista considerando alteração do ingest + 4 colunas + 5 endpoints + frontend cascata: **L (12-20h)** mínimo.

**Decisões L3:**
1. Adicionar 4 campos ao `Cliente` (migration L3-3-aceita).
2. Criar router `routes_dde.py`.
3. **Usar alíquotas SINTÉTICAS para ICMS/PIS/COFINS?** — VIOLA R8 se não for explicitamente flagado SINTÉTICO.
4. Implementar Fase A agora ou esperar CMV?
5. `produtos.comissao_pct` (mesma pergunta do v1).
6. Verificar se `RelatorioDeMargem` (Sales Hunter #9, não integrado) tem custo unitário.

**Risco:** MÉDIO. Alteração do `ingest_sales_hunter.py` pode quebrar pipeline atual. Migration adiciona 4 colunas não-críticas mas requer Alembic + reload Vercel.

**LLM:** este spec **não menciona LLM**. É puramente determinístico (regras IF/THEN para plano de ação no v1, ainda Python puro).

---

### 2.3 SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md (v3, 25.6 KB) — **ATIVA**

**Objetivo:** Substituir o trabalho manual atual (Excel ZSDFAT + LOG | EFETIVADO + Pricing + 30-45 min/cliente de analista) por **1 página no CRM** com:
- Margem global + veredito (SAUDÁVEL / RENEGOCIAR / SUBSTITUIR)
- 3 anomalias críticas detectadas automaticamente
- 5 ações priorizadas com impacto R$
- Botão "Gerar Resumo CEO" (PDF 1 página via LLM)
- Comparativo cross-cliente

**Escopo backend:**

**6 novas tabelas (L3 — schema change crítico):**
1. `cliente_contrato` — contratos de desconto (BP, vigência, % ZDF2/ZPMH)
2. `cliente_verbas_anual` — verbas por ano (cliente, ano, valor, fonte)
3. `cliente_frete_mensal` — frete CT-e mensal (qtd_ctes, valor)
4. `cliente_promotor_mensal` — custo promotor por agência
5. `cliente_sku_praticado` — preço/custo praticado por SKU/mês
6. `cliente_dre_periodo` — DRE consolidado (linha, conta, valor_param_sap, valor_efetivado, fonte_efetivado)
7. `mercado_sku_preco` — pricing concorrência (Sprint 2)
8. `mercado_categoria_veredito` — veredito por categoria (Sprint 2)
9. `cliente_anomalia` — cache de anomalias detectadas (CRITICO/ATENCAO/REVISAR)

**6 parsers (todos novos, base class `BaseParser`):**
- `parser_zsdfat.py` — parser do Excel SAP (13 abas, 24 checks de validação)
- `parser_verbas.py`
- `parser_frete.py`
- `parser_contratos.py`
- `parser_promotores.py`
- `parser_ult_praticado.py`

**Engine de regras (Python puro, determinístico):**
- `calcula_dre_efetivado(cliente_id, ano)` — cruza param SAP vs LOG
- `sinaleiro_sku()` — 6 estados (OK / REVISAR / AJUSTAR / SUBSTITUIR / DEVOLUCAO_NAO_CAPTURADA / SEM_DADOS)
- `detecta_anomalias()` — 8 regras IF/THEN
- `veredito_sku_vs_mercado()` — 4 estados (BARATO_DEMAIS / COMPETITIVO / PREMIUM / CARO_DEMAIS)

**Pipeline de ingestão:**
- Upload manual Excel via interface (CFO sobe 6 arquivos/mês)
- 5 jobs cron: `etl_zsdfat_monthly`, `etl_log_efetivado`, `etl_pricing_mercado`, `engine_recalc_dre`, `engine_anomalia_alert`
- Crawler externo de pricing (49 SKUs × 23 canais)

**API REST (mínimo):**
- `GET /clientes/:id/analise-critica` — payload com DRE 4 anos + anomalias + ações
- `GET /clientes/comparativo?ids=...` — cross-cliente

**Escopo frontend:**
- Aba "Análise Crítica" no CRM (mesma stack atual: Next.js 14 + TS + Tailwind)
- Layout 1 página com: header (margem + veredito) + KPI strip 5 cards + tabs [DRE / Mix / Anomalias / Recomendações] + botões [Gerar Resumo CEO PDF / Exportar Excel]
- Tela comparativo cross-cliente (Sprint 3)
- Charts: Recharts (combo bar+line, pie sinaleiro)
- Tabela virtualizada para SKUs >100

**Dependências:**

| # | Dependência | Bloqueia | Status |
|---|--------------|----------|--------|
| D1 | 6 arquivos Excel reais do CFO (golden master Coelho Diniz Forense) | Sprint 1 | **Aguarda Leandro** |
| D2 | Schema PostgreSQL aprovado (9 tabelas L3) | Sprint 1 | **Aguarda L3** |
| D3 | Parser ZSDFAT estável (24 checks playbook v3.0) | Sprint 1 | Não iniciado |
| D4 | LLMClient ativo (`backend/app/services/llm_client.py`) | **Sprint 2+** | **DORMENTE — Tipo A** |
| D5 | Crawler de pricing (Claude in Chrome ou Playwright headless) | Sprint 2 | Não iniciado |
| D6 | Decisão de hosting do ETL cron (Render/Vercel/AWS) | Sprint 4 | Aguarda Leandro |

**Esforço (reavaliação realista):**
- Sprint 1: **L (20-30h)** — 6 tabelas + 6 parsers + engine DRE + UI = sprint sólido
- Sprint 2: **XL (30h+)** — crawler externo é trabalho desconhecido + LLM + UI nova
- Sprint 3: **L (12-20h)** — comparativo cross-cliente + LLM
- Sprint 4: **M (8-12h)** — ETL cron + notificações
- Sprint 5: **XL (30h+)** — Chat RAG + PDF + snapshot

**Total: ~100-150h reais (12-19 semanas com 1 dev solo).**

**Decisões L3:**
1. **L3 — Aprovar 9 novas tabelas** (impacto crítico no schema atual).
2. **L3 — Aprovar interface de upload manual** (CFO sobe arquivos vs. extração automática).
3. **L3 — Estratégia LLM:** Sprint 2+ depende LLMClient. Aprovar ativação ou postergar Sprints 2-3-5?
4. **L3 — Crawler de mercado:** Claude in Chrome vs. Playwright headless?
5. **L3 — Hosting ETL cron:** Render/Vercel/AWS?
6. **L3 — Feature flag por cliente:** `ANALISE_CRITICA_HABILITADA` (rollout gradual)?
7. **L3 — Golden master Coelho Diniz:** ter Excel forense disponível como referência de aceite.
8. **L3 — Versionamento snapshot mensal:** salvar cada análise como histórico (Sprint 5)?

**Risco:** **ALTO**. Por que:
- 9 novas tabelas afetam estrutura atual (potencial conflito com `vendas`, `venda_itens`, `clientes`).
- 6 parsers de Excel = ponto de falha frequente (24 checks só pro ZSDFAT).
- Crawler externo é dependência fora do controle (WAF, rate limit).
- LLM em produção precisa: validação pós-geração, rate limiting, custo, fallback.
- Espelha processo manual do CFO — qualquer erro causa perda de confiança e volta para Excel.

**LLM (Sprint 2+):**
> **MARCADO EXPLICITAMENTE: depende de ativação LLMClient (Tipo A).**
>
> **NÃO implementar Sprint 2-3-5 até decisão L3 sobre LLM.**
>
> Funções LLM previstas:
> - Resumo CEO (Sonnet 4.5) — Sprint 2
> - Justificar anomalia (Haiku 4.5) — Sprint 3
> - Sugerir ação (Sonnet 4.5) — Sprint 3
> - Cross-cliente comparativo (Sonnet 4.5) — Sprint 3
> - Chat com a aba (Sonnet 4.5 + RAG) — Sprint 5

---

## 3. ORDEM RECOMENDADA DE IMPLEMENTAÇÃO

### Critério de ordenação:
1. **Ganho imediato** — entregar valor com dados de hoje
2. **Risco crescente** — começar pelos blocos sem dependência externa
3. **Two-Base sagrada** — operações monetárias só em VENDA-side
4. **R8 zero fabricação** — gaps explícitos como `null`, nunca alíquotas inventadas sem flag SINTÉTICO

### Fase 0 — DECISÕES L3 (ANTES DE QUALQUER CÓDIGO)

**Bloqueador:** Leandro precisa responder as decisões L3 listadas na seção 4 antes de começar.

**Particularmente:**
- D1 (golden master Coelho Diniz Forense): ter acesso ao Excel de referência.
- D2 (9 tabelas v3): aprovação explícita.
- D3 (estratégia LLM): decidir se ativa LLMClient ou posterga.

**Saída esperada:** doc `docs/specs/DECISOES_L3_COWORK_APROVADAS.md` assinado pelo Leandro.

---

### Fase 1 — Vitórias rápidas com dados existentes (REUSO de v1+v2 dentro de v3)

**Justificativa:** As 5 dimensões "100% disponíveis" do v1 (Sell-in, Conta Corrente, Pagamentos, Mix produtos, Score parcial) **já podem virar UI** sem novas tabelas. Isso entrega valor imediato e valida o desenho de UI antes do Sprint 1 do v3.

**Ações:**
1. Implementar Phase A do v1: router `routes_analise_critica.py` (read-only, agregações SQL).
2. UI react simples (5 cards) na ficha do cliente.
3. Score 6 componentes (sem margem bruta — flag "score parcial").

**Esforço:** **M (6-10h)** — read-only, baixo risco, boa proxy do que vem depois.

**Risco:** BAIXO. Nada de migration. Nada de ingest. Read-only.

**Saída:** UI funcional para validar com Leandro o design antes de investir Sprint 1 v3 inteiro.

---

### Fase 2 — Migration leve do v2 (apenas Phase A)

**Justificativa:** O v2 propõe 4 colunas no `Cliente` e alterações no `ingest_sales_hunter.py` que **dão a base para Receita Líquida Comercial**. Sem isso, a DDE para na Receita Bruta. Esses 4 campos também alimentam o Sprint 1 do v3 (linhas 5, 7, 8, 16, 22 do DRE).

**Ações:**
1. Migration Alembic: 4 colunas em `clientes` (`desc_comercial_pct`, `desc_financeiro_pct`, `total_bonificacao`, `ipi_total`).
2. Patch no `ingest_sales_hunter.py`:
   - Phase 3: extrair cols 7, 8, 16, 22.
   - Phase 5: extrair col 19 (IPI), somar por CNPJ.
3. Reingestão de dados existentes (rerun do pipeline).
4. Endpoint `/dde/receita` (cascata até Receita Líq. Comercial).
5. UI cascata simples (1 bloco da DDE).

**Esforço:** **L (12-18h)** — alteração de pipeline existente é mais delicada que código novo.

**Risco:** MÉDIO. Toca `ingest_sales_hunter.py` em produção. Necessita testes E2E de regressão.

**Saída:** DDE 45% completa (até Receita Líq. Comercial + Conta Corrente + Mix + IPI).

---

### Fase 3 — Sprint 1 v3 (FEATURE Análise Crítica MVP)

**Justificativa:** Agora sim, com Fase 1+2 entregues, o Sprint 1 do v3 fica viável. Precisa do golden master Coelho Diniz para aceite.

**Ações (do próprio spec v3):**
1. 6 tabelas PostgreSQL + migrations (cliente_contrato, cliente_verbas_anual, cliente_frete_mensal, cliente_promotor_mensal, cliente_sku_praticado, cliente_dre_periodo).
2. Parser ZSDFAT + 4 parsers LOG | EFETIVADO.
3. Engine DRE: cálculo L30-L35 efetivado.
4. UI: 1 página com DRE 4 anos + KPI strip + lista anomalias (regras hardcoded).
5. Botão "Exportar Excel" (replica formato Sidecar v2 atual).

**Critério de aceite:** Coelho Diniz aberto no CRM bate 100% com Excel manual (Análise Crítica — Coelho Diniz — Forense.xlsx).

**Esforço:** **L-XL (20-30h).**

**Risco:** ALTO. Parser ZSDFAT é ponto crítico (13 abas, 24 checks). Sem golden master, não dá para validar.

---

### Fase 4 — Cross-cliente sem LLM (Sprint 3 v3 parcial)

**Justificativa:** Comparativo cross-cliente é tabela + filtro — implementável sem LLM. Adia "anomalia inteligente" para depois.

**Ações:**
1. Endpoint `GET /clientes/comparativo?ids=...`
2. UI tabela comparativa (8 clientes lado a lado).
3. Histórico evolução (3 anos) com Recharts.

**Esforço:** **M (6-10h).**

**Risco:** BAIXO.

---

### Fase 5 — ETL automático (Sprint 4 v3)

**Justificativa:** Antes de ativar LLM (Sprint 2+5), automatizar o ETL para garantir dados sempre frescos.

**Ações:**
1. Cron jobs (Render/Vercel/AWS — depende decisão L3).
2. Notificação de anomalias (email/Slack).
3. Workflow ABERTA / RESOLVIDA / IGNORADA com auditoria.

**Esforço:** **M (8-12h).**

**Risco:** MÉDIO (depende infra cron).

---

### Fase 6 — Mercado + LLM (Sprint 2 v3) — **DEPENDE LLMClient ATIVO**

**Justificativa:** Sprint 2 do spec v3 trouxe junto pricing mercado + LLM Resumo CEO. Posterga até **decisão L3 sobre LLMClient**.

**Ações:**
1. Crawler de pricing (Claude in Chrome ou Playwright).
2. Tabelas `mercado_sku_preco` + `mercado_categoria_veredito`.
3. Engine veredito SKU vs mercado.
4. **LLM Resumo CEO** (Sonnet 4.5) — primeiro uso de LLM.
5. Validação pós-geração (regex de R$ deve bater com dados injetados).

**Esforço:** **XL (30h+).**

**Risco:** ALTO. Crawler bloqueado por WAF. LLM custo/alucinação.

---

### Fase 7 — LLM intenso (Sprint 5 v3) — **DEPENDE LLMClient ATIVO**

**Ações:**
1. Chat com a aba (Sonnet 4.5 + RAG).
2. PDF Resumo CEO.
3. Snapshot mensal de cada análise.

**Esforço:** **XL (30h+).**

**Risco:** ALTO.

---

## 4. DECISÕES L3 CONSOLIDADAS (AGRUPADAS POR TEMA)

### Tema A — Schema do banco (impactam estrutura)

| # | Decisão | Origem | Impacto |
|---|---------|--------|---------|
| L3-A1 | **Adicionar 4 colunas ao `Cliente`:** `desc_comercial_pct`, `desc_financeiro_pct`, `total_bonificacao`, `ipi_total` | v2, v3 | Migration leve |
| L3-A2 | **Criar tabela `verbas_clientes`** agora (sem dados) ou esperar SAP? | v1, v2 | Schema novo opcional |
| L3-A3 | **Criar 6 tabelas v3:** `cliente_contrato`, `cliente_verbas_anual`, `cliente_frete_mensal`, `cliente_promotor_mensal`, `cliente_sku_praticado`, `cliente_dre_periodo` | v3 | **Schema crítico** |
| L3-A4 | **Criar 2 tabelas mercado** (`mercado_sku_preco`, `mercado_categoria_veredito`) | v3 Sprint 2 | Schema novo |
| L3-A5 | **Criar tabela `cliente_anomalia`** (cache de regras detectadas) | v3 | Schema novo |
| L3-A6 | **Adicionar `custo_unitario` em `produtos`** + `cmv_unitario`, `cmv_total` em `venda_itens` | v2 Fase B | Migration média |
| L3-A7 | **Criar tabela `impostos_nf`** (cnpj, nro_nfe, icms, pis, cofins, ipi) | v2 Fase B | Schema novo |

### Tema B — Pipeline e ingestão

| # | Decisão | Origem | Impacto |
|---|---------|--------|---------|
| L3-B1 | **Alterar `ingest_sales_hunter.py`** Phase 3+5 para extrair descontos %, bonificação separada, IPI | v2, v3 | Risco regressão |
| L3-B2 | **Criar interface de upload manual de Excel** (CFO sobe 6 arquivos/mês) | v3 | Backend + UI nova |
| L3-B3 | **Hosting do ETL cron:** Render / Vercel cron / AWS / outro? | v3 Sprint 4 | Infra |
| L3-B4 | **Crawler de pricing:** Claude in Chrome (assistido) ou Playwright headless? | v3 Sprint 2 | Stack tooling |
| L3-B5 | **Verificar `RelatorioDeMargem` (Sales Hunter #9, não integrado)** — contém custo unitário? Se sim, prioriza CMV. | v2 | Pode desbloquear margem |

### Tema C — LLM (Tipo A — DORMENTE)

| # | Decisão | Origem | Impacto |
|---|---------|--------|---------|
| L3-C1 | **Ativar LLMClient agora ou postergar?** | v3 Sprints 2/3/5 | **Bloqueia Sprint 2+5** |
| L3-C2 | **Modelo:** Sonnet 4.5 (Resumo CEO, ações, comparativos) + Haiku 4.5 (anomalias) | v3 | Custo |
| L3-C3 | **Validação pós-geração LLM** (regex R$ vs dados injetados) — implementar como gate | v3 anti-alucinação | Qualidade |
| L3-C4 | **RAG no Chat com a aba** (Sprint 5) — fonte de embeddings (cliente atual + histórico) | v3 Sprint 5 | Stack vector DB |

### Tema D — Regras de negócio

| # | Decisão | Origem | Impacto |
|---|---------|--------|---------|
| L3-D1 | **`produtos.comissao_pct` é comissão vendedor ou rebate cliente?** Afeta cálculos de Margem de Contribuição. | v1, v2 | Impacta DDE |
| L3-D2 | **Usar alíquotas SINTÉTICAS para ICMS/PIS/COFINS** enquanto SAP fiscal não chega? | v2 Fase B | **Viola R8 se sem flag** |
| L3-D3 | **Implementar Phase A v1/v2 já** ou esperar tudo do SAP completo? | v1, v2 | Timing |
| L3-D4 | **Frete:** TIPO (CIF/FOB) hoje vs. VALOR R$ futuro — usar proxy SINTÉTICO ou só CIF/FOB classifier? | v2 Fase B | Precisão |
| L3-D5 | **Versionamento snapshot mensal** das análises críticas (cada cliente, cada mês) | v3 Sprint 5 | Storage + retenção |

### Tema E — Produto e UX

| # | Decisão | Origem | Impacto |
|---|---------|--------|---------|
| L3-E1 | **Feature flag `ANALISE_CRITICA_HABILITADA` por cliente** — rollout gradual? | v3 | Risco controlado |
| L3-E2 | **Golden master Coelho Diniz Forense:** acessar Excel de referência para aceite Sprint 1. | v3 | Bloqueia aceite |
| L3-E3 | **Aba "Análise Crítica" na ficha cliente** ou em rota separada `/analise-critica/{cnpj}`? | v3 | UX e navegação |
| L3-E4 | **Comparativo cross-cliente:** quantos clientes lado a lado? (8? variável?) | v3 Sprint 3 | UI |
| L3-E5 | **PDF Resumo CEO** — usar wkhtmltopdf, reportlab, browser-side, ou serviço externo? | v3 Sprint 5 | Stack |

### Tema F — Decisões críticas (precedência)

**Top 5 decisões bloqueadoras (a responder antes de qualquer código):**

1. **L3-A3** — Aprovar as 6+2+1 = 9 novas tabelas do v3? (sim/não/parcial)
2. **L3-C1** — Ativar LLMClient agora ou postergar? (afeta 3 sprints inteiros)
3. **L3-E2** — Acesso ao Excel Coelho Diniz Forense? (sem ele, Sprint 1 não tem aceite)
4. **L3-D2** — Alíquotas SINTÉTICAS aceitas (com flag SINTÉTICO) ou só dados REAL? (afeta R8)
5. **L3-D3** — Implementar Fase A v1/v2 antes do v3 (vitória rápida) ou ir direto v3 Sprint 1?

---

## 5. CAMINHOS CRÍTICOS — paralelização

### 5.1 Trabalho que pode rodar em paralelo

**Workstream 1: Backend (Phase A v1)**
- Endpoints de leitura para 5 dimensões já disponíveis em DB.
- Não toca em ingest, não toca em schema.
- **Paralelo com:** Workstream 2 (frontend skeleton).

**Workstream 2: Frontend (UI skeleton)**
- Layout de aba "Análise Crítica" sem dados (placeholders).
- Card structures, tabs, design system.
- **Paralelo com:** Workstream 1 (mocks aguardam endpoint real).

**Workstream 3: Migration v2 (4 colunas + ingest patch)**
- Migration Alembic + alteração `ingest_sales_hunter.py`.
- **Não paralelo com:** Workstreams 1/2 (afeta dados).

### 5.2 Sequenciamento crítico (NÃO PARALELIZAR)

- **Sprint 1 v3** depende de **golden master Coelho Diniz** (L3-E2) — sem ele, sem aceite.
- **Sprint 2 v3 (LLM)** depende de **L3-C1 (ativar LLMClient)** — bloqueio absoluto.
- **Parser ZSDFAT** depende de **schema PostgreSQL aprovado** (L3-A3).
- **Crawler de mercado** depende de **decisão Claude-in-Chrome vs. Playwright** (L3-B4).

### 5.3 Estimativa otimizada com paralelização

Se 2 devs (ou Claude+Codex em paralelo):
- Fase 1 (v1 Phase A) + Fase 2 (v2 migration): **paralelizáveis** parcialmente — ganho de ~30%.
- Sprint 1 v3 backend (parsers + engine) + frontend (UI): **paralelizáveis** — ganho de ~40%.
- Total: de ~150h para ~90-100h reais.

Solo dev (Leandro + Claude apenas): manter sequencial. Total: ~150h.

---

## 6. CONFLITOS E AMBIGUIDADES DETECTADAS ENTRE OS SPECS

### Conflito 1: Score composto

- **v1** define peso de 6 componentes (Faturamento, Tendência, Adimplência, Penetração, Frequência, Risco) com pesos 25/15/25/15/10/10.
- **v2** define peso de 8 componentes (adiciona Margem Bruta + Inadimplência líquida) com pesos 20/10/25/10/10/10/10/5.
- **v3** não define score composto explícito — usa veredito qualitativo (SAUDÁVEL / RENEGOCIAR / SUBSTITUIR).

**Resolução proposta:** v3 é a fonte de verdade. Score numérico do v1/v2 é informação complementar (KPI strip), mas o **veredito do v3** é o output principal.

### Conflito 2: Formato de UI

- **v1** propõe 7 cards (1 por dimensão) — dashboard.
- **v2** propõe layout em **cascata financeira** — DDE.
- **v3** propõe **header + KPI strip + tabs** (DRE / Mix / Anomalias / Recomendações) — decisão.

**Resolução:** v3 é a fonte. v2 cascata pode ser uma TAB dentro do v3 (tab "DRE detalhada"). v1 cards podem ser KPI strip simplificado.

### Conflito 3: Endpoint naming

- **v1:** `/api/clientes/{cnpj}/analise-critica/...`
- **v2:** `/api/clientes/{cnpj}/dde/...`
- **v3:** `/clientes/:id/analise-critica` (sem `/api/` explícito, usa id em vez de cnpj)

**Resolução:** padronizar em `/api/clientes/{cnpj}/analise-critica` (CNPJ é chave primária — R5 — e `/api/` é convenção do FastAPI atual). Ignorar `id` numérico do v3.

### Conflito 4: Comissão vs. Rebate

- v1 e v2 perguntam a mesma coisa: `produtos.comissao_pct` é vendedor ou cliente?
- v3 trata como linha "Comissão vendedor" no DRE (L34_efetivado = SAP Fat.CL1).

**Resolução:** decisão L3-D1 deve esclarecer. v3 sugere que comissão de vendedor vem do SAP Fat.CL1, NÃO do `produtos.comissao_pct`. **Recomendação:** investigar Fat.CL1 antes de assumir que `produtos.comissao_pct` resolve isso.

### Ambiguidade 1: "Plano de ação"

- v1 propõe **regras IF/THEN** (Python puro).
- v3 propõe **LLM gera 5 ações com impacto R$** (Sonnet 4.5).

**Resolução proposta:** começar com IF/THEN (v1) na Fase 1. Trocar por LLM no Sprint 2 do v3 quando LLMClient estiver ativo.

### Ambiguidade 2: Sell-out

- v1 propõe sell-out **parcial** (penetração de SKUs) hoje, full **com BI futuro**.
- v3 não menciona sell-out diretamente — foca em DRE.

**Resolução:** sell-out parcial é "bonus" — implementar como parte do bloco MIX no v3 (Tab "Mix SKUs"), não como bloco separado.

---

## 7. RESUMO EXECUTIVO

### O que entregar (ordem)

1. **Fase 0 — DECISÕES L3** (Leandro responde top 5 perguntas) — ANTES DE QUALQUER CÓDIGO
2. **Fase 1 — UI Phase A v1** (5 dimensões já em DB, read-only) — vitória rápida
3. **Fase 2 — Migration v2** (4 colunas + ingest patch) — fundação Receita Líquida
4. **Fase 3 — Sprint 1 v3 MVP** (6 tabelas + parsers + DRE + UI) — feature principal
5. **Fase 4 — Cross-cliente sem LLM** (comparativo)
6. **Fase 5 — ETL cron** (automação)
7. **Fase 6 — LLM (Sprint 2 v3)** — **DEPENDE L3-C1 (ativar LLMClient)**
8. **Fase 7 — LLM intenso (Sprint 5 v3)** — **DEPENDE L3-C1**

### Esforço total realista

- **Solo dev (Claude + Leandro):** ~150-200h reais (~6 meses solo, ~10 meses calendário com pausas)
- **Com paralelização (2 fontes IA):** ~90-120h reais (~4 meses)

### Risco geral

- **Fases 1-2:** BAIXO-MÉDIO
- **Fase 3 (Sprint 1 v3):** ALTO sem golden master, MÉDIO com ele
- **Fases 4-5:** MÉDIO
- **Fases 6-7 (LLM):** ALTO — alucinação, custo, latência

### Top 3 bloqueadores imediatos

1. **L3-A3** (aprovar 9 novas tabelas)
2. **L3-E2** (acesso ao Excel Coelho Diniz Forense)
3. **L3-C1** (ativar LLMClient — afeta 3 sprints)

---

## 8. APÊNDICE — Mapeamento entre specs (referência cruzada)

### Conceitos compartilhados

| Conceito | v1 | v2 | v3 |
|----------|-----|-----|-----|
| Sell-in (faturamento Vitao→Cliente) | Dim 1 (✅ 100%) | Bloco 1 (✅ Receita Bruta) | DRE Linha 18 |
| Sell-out (Cliente→Consumidor) | Dim 2 (🔜 BI) | Bloco 6 (⚠️ proxy) | Tab Mix SKUs |
| Verba conquista | Dim 3 (🔜 SAP) | Linha 13 (🔜 SAP) | DRE L31 efetivado |
| Verba gerada (rebate) | Dim 4 (⚠️ comissão?) | Linha 14 (🔜 SAP) | DRE L31 efetivado |
| Conta corrente | Dim 6 (✅ 100%) | Bloco 5 (✅ 100%) | Tab Anomalias (linhas vencidas) |
| Pagamentos recebidos | Dim 7 (✅ 100%) | Bloco 5 (✅ 100%) | (incluso conta corrente) |
| Mix produtos | Bonus (✅ 95%) | Bloco 6 (✅ 95%) | Tab Mix SKUs |
| Score | Sec 4 (6 comp.) | Sec 7 (8 comp.) | Veredito qualitativo |
| Plano de ação | Sec 5 (IF/THEN) | Sec 8 (IF/THEN) | LLM Resumo CEO |

### Endpoints propostos (consolidados)

```
GET /api/clientes/{cnpj}/analise-critica           # v3 root (DRE + KPI + tabs)
GET /api/clientes/{cnpj}/analise-critica/dre       # cascata DDE (v2)
GET /api/clientes/{cnpj}/analise-critica/mix       # SKUs + cross-sell (v1+v2)
GET /api/clientes/{cnpj}/analise-critica/anomalias # detector de regras (v3)
GET /api/clientes/{cnpj}/analise-critica/acoes     # IF/THEN ou LLM (v1→v3)
GET /api/clientes/comparativo?cnpjs=...            # cross-cliente (v3)
POST /api/llm/resumo-ceo                           # LLM Sonnet 4.5 (v3 Sprint 2)
POST /api/admin/upload-excel                       # interface manual CFO (v3)
```

---

## 9. NOTAS FINAIS

- **LLMClient está dormente propositalmente.** Não tocar `backend/app/services/llm_client.py` nem `frontend/src/lib/llm_provider.ts` até L3-C1 aprovar.
- **R8 zero fabricação** é o filtro mais forte deste roadmap. Qualquer alíquota SINTÉTICA precisa flag explícito.
- **R4 Two-Base** sempre respeitada: todos valores monetários são VENDA-side.
- **R5 CNPJ** sempre normalizado (string, 14 dígitos) em endpoints.
- **R7 Faturamento baseline R$ 2.091.000** — qualquer total que divirja >0.5% é alerta.
- **Specs originais permanecem untracked** na raiz do projeto até decisão sobre arquivamento (briefing futuro do passo 0 VSCode).

---

*Roadmap consolidado em 2026-04-28. Aguardando decisões L3 do Leandro antes de iniciar implementação.*
