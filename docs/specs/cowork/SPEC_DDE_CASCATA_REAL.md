# SPEC DDE — Cascata P&L Real por Cliente

**Versão:** 1.0 · **Data:** 28/04/2026 · **Owner:** Leandro · **Status:** spec definitiva

> Esta spec **substitui** SPEC_DDE_CLIENTE.md (v0, dashboard de métricas) e é o **núcleo determinístico** da SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md (camada 4 — Engine de Regras). Não é UI, não é LLM. É a cascata de cálculo P&L que alimenta tudo que vem depois.

---

## 1. TESE

DDE real é P&L cascata por cliente. Começa em Receita Bruta, desce até EBITDA Cliente, atravessa 7 blocos. Cada linha tem fonte, fórmula, sinal e classificação 3-tier (REAL / SINTÉTICO / PENDENTE). Sem CMV não há Margem Bruta. Sem Margem Bruta não há decisão. Estrutura faseada permite entregar parcial honesto enquanto SAP/BI completam o quadro.

**Diferença vs spec antiga:** spec antiga era 7 dimensões justapostas (sell-in, sell-out, conta corrente, mix, etc.). Esta é uma cascata única com sinal e dependência. Dimensões viram desdobramentos da cascata, não substituem.

---

## 2. DECISÕES L3 INCORPORADAS (para confirmação Leandro)

| ID | Decisão | Status | Recomendação |
|---|---|---|---|
| **D1** | Persistir 4 campos do Sales Hunter no Cliente: `desc_comercial_pct`, `desc_financeiro_pct`, `total_bonificacao`, `ipi_total` | PENDENTE | GO — sem isso L7-L9 da cascata vazias |
| **D2** | Criar `routes_dde.py` com 5 endpoints (cliente, vendedor agg, canal agg, comparativo, score) | PENDENTE | GO |
| **D3** | Linhas de imposto sem dado real: `null` ou alíquota sintética setor? | PENDENTE | **NULL** — DDE parcial honesta > inventada |
| **D4** | Implementar Fase A agora ou esperar SAP completo? | PENDENTE | **GO Fase A** — entrega parcial vale, marca PENDENTE no que falta |
| **D5** | `produtos.comissao_pct` é comissão vendedor ou rebate cliente? | ABERTO | Confirmar com SAP — afeta L18 vs L7 |
| **D6** | Baixar `RelatorioDeMargemPorProduto` (P2) — tem custo unitário? | URGENTE | Se sim, desbloqueia CMV (L11) — fim do gap mais crítico |

---

## 3. A CASCATA P&L COMPLETA

### Convenções

- **Sinal:** `+` entra na cascata, `−` deduz da linha anterior, `=` linha calculada
- **Status:** `REAL` (dado existe e é confiável) · `SINTÉTICO` (média/proxy marcado) · `PENDENTE` (fonte definida mas não integrada) · `NULL` (não temos hoje, não inventamos)
- **Fonte:** `SH` Sales Hunter · `SAP` SAP módulos não-Sales-Hunter · `MERCOS` · `BI` BI futuro com POS · `LOG` Logística (CFO upload) · `MANUAL` upload CFO mensal · `CALC` calculado via cascata
- **Fase:** `A` implementável hoje · `B` espera SAP · `C` espera BI

### BLOCO 1 — RECEITA BRUTA

| L | Conta | Sinal | Fórmula | Fonte | Status hoje | Fase |
|---|---|---|---|---|---|---|
| L1 | Faturamento bruto a tabela | + | Σ(qtd × preco_tabela) por NF do cliente | SH `fat_cliente` col 22 | REAL | A |
| L2 | IPI sobre vendas | + | Σ ipi_total por NF | SH `pedidos_produto` col 19 | PENDENTE (ingest não persiste) | A |
| **L3** | **= Receita Bruta com IPI** | = | L1 + L2 | CALC | depende de D1 | A |

### BLOCO 2 — DEDUÇÕES DA RECEITA

| L | Conta | Sinal | Fórmula | Fonte | Status hoje | Fase |
|---|---|---|---|---|---|---|
| L4 | (−) Devoluções | − | Σ valor_nfe de devolucao_cliente | SH `devolucao_cliente` | REAL | A |
| L5 | (−) Desconto comercial | − | Σ (preco_tabela − preco_pratico) × qtd | SH `fat_cliente` col 7 | PENDENTE (ingest não persiste) | A |
| L6 | (−) Desconto financeiro | − | Σ desc_financeiro por NF | SH `fat_cliente` col 8 | PENDENTE | A |
| L7 | (−) Bonificações | − | Σ bonificacao | SH `fat_cliente` col 16 | PENDENTE | A |
| L8 | (−) IPI faturado | − | Σ ipi recolhido | SH `pedidos_produto` col 19 | PENDENTE | A |
| L9 | (−) ICMS | − | base × alíquota_uf | SAP fiscal | NULL hoje (D3) | B |
| L10a | (−) PIS | − | base × 1,65% | SAP fiscal | NULL hoje (D3) | B |
| L10b | (−) COFINS | − | base × 7,6% | SAP fiscal | NULL hoje (D3) | B |
| L10c | (−) ICMS-ST | − | base × ST_uf | SAP fiscal | NULL hoje (D3) | B |
| **L11** | **= Receita Líquida** | = | L3 − L4 − L5 − L6 − L7 − L8 − L9 − L10a − L10b − L10c | CALC | parcial (Fase A entrega L11_comercial = L3 − L4..L8) | A/B |

> **Observação:** Fase A entrega "Receita Líquida Comercial" (sem impostos). Fase B agrega impostos para "Receita Líquida Fiscal".

### BLOCO 3 — CMV (Custo dos Produtos Vendidos)

| L | Conta | Sinal | Fórmula | Fonte | Status hoje | Fase |
|---|---|---|---|---|---|---|
| L12 | (−) CMV | − | Σ (qtd_vendida × custo_unitario_sku) por venda | `RelatorioDeMargemPorProduto` (Sales Hunter P2) **OU** SAP custo médio | PENDENTE — D6 desbloqueia | B |
| **L13** | **= Margem Bruta** | = | L11 − L12 | CALC | aguarda L12 | B |

> **Observação:** Sem L12 não há L13. Sem L13 toda cascata abaixo perde sentido econômico — vira rateio. Por isso D6 é urgente.

### BLOCO 4 — DESPESAS VARIÁVEIS DO CLIENTE (Custo de Servir)

| L | Conta | Sinal | Fórmula | Fonte | Status hoje | Fase |
|---|---|---|---|---|---|---|
| L14 | (−) Frete (CT-e por cliente) | − | Σ valor_cte mensal | LOG upload `Frete por Cliente.xlsx` | PENDENTE — schema definido (cliente_frete_mensal) | A |
| L15 | (−) Comissão sobre venda | − | L11 × comissao_vendedor_pct (ou Σ produto.comissao × qtd) | SH `pedidos_produto` col 9 (vendedor) + tabela comissão | SINTÉTICO se usar % padrão; REAL se cruzar SAP CL1 | A |
| L16 | (−) Verbas (contratos) | − | Σ verba_contrato_anual ÷ 12 (ou efetivada mensal) | LOG upload `Controle de Contratos.xlsx` + `Verbas.xlsx` | PENDENTE — schema definido | A |
| L17 | (−) Promotor PDV | − | Σ valor_agencia mensal | LOG upload `Despesas Clientes.xlsx` | PENDENTE — schema definido | A |
| L18 | (−) Bonificação financeira (rebate) | − | depende de D5 | SH `produtos.comissao_pct` ou separado | ABERTO | A |
| L19 | (−) Custo de inadimplência (provisão) | − | Σ titulos_vencidos × prob_perda | banco `debitos_clientes` | REAL parcial — calculável a partir de aging | A |
| L20 | (−) Custo financeiro (capital de giro) | − | aging médio × CDI × valor_em_aberto | `debitos_clientes` + `vendas` + CDI exógeno | SINTÉTICO (CDI fixo) — REAL se houver fonte | A |
| **L21** | **= Margem de Contribuição** | = | L13 − L14 − L15 − L16 − L17 − L18 − L19 − L20 | CALC | parcial (sem L13 vira "MC sobre Receita Líquida Comercial") | A/B |

### BLOCO 5 — DESPESAS FIXAS ALOCADAS

> **Nota:** rateio de despesa fixa por cliente é polêmico. Pode ser feito por % faturamento, por nº pedidos, por hora-vendedor. Sugestão: marcar como SINTÉTICO sempre, expor metodologia no UI, deixar gerente reclassificar.

| L | Conta | Sinal | Fórmula | Fonte | Status hoje | Fase |
|---|---|---|---|---|---|---|
| L22 | (−) Estrutura comercial alocada | − | (folha_comercial_total ÷ Σ_clientes_ativos) ou rateio por hora-vendedor | SAP folha + base CRM | SINTÉTICO sempre | B |
| L23 | (−) Estrutura administrativa alocada | − | folha_adm × % faturamento_cliente / faturamento_total | SAP folha | SINTÉTICO | B |
| L24 | (−) Marketing alocado | − | gasto_marketing × % faturamento_cliente | SAP/contábil | SINTÉTICO | B |
| **L25** | **= Resultado Operacional Cliente** | = | L21 − L22 − L23 − L24 | CALC | só Fase B | B |

### BLOCO 6 — INDICADORES DERIVADOS (calculados, não somados)

| L | Indicador | Fórmula | Status |
|---|---|---|---|
| I1 | Margem Bruta % | L13 ÷ L11 | depende L13 |
| I2 | Margem Contribuição % | L21 ÷ L11 | parcial Fase A |
| I3 | EBITDA Cliente % | L25 ÷ L11 | só Fase B |
| I4 | Custo de Servir | (L14+L15+L17+L18) ÷ L11 | Fase A |
| I5 | Verba % Receita | L16 ÷ L11 | Fase A |
| I6 | Inadimplência % | L19 ÷ L11 | Fase A |
| I7 | Devolução % | L4 ÷ L1 | Fase A |
| I8 | Aging Médio (DSO) | Σ(dias_atraso × valor) ÷ Σ valor | Fase A — `debitos_clientes` |
| I9 | Score Saúde Financeira | composto I1..I8 (regra) | Fase A parcial / B completa |

### BLOCO 7 — VEREDITOS DETERMINÍSTICOS

```python
def veredito_cliente(dre):
    if dre.margem_contribuicao_pct < 0:
        return ('SUBSTITUIR', 'Margem negativa — cliente destrói valor')
    if dre.margem_contribuicao_pct < 0.05:
        return ('RENEGOCIAR', 'Margem < 5% — abaixo do custo de capital')
    if dre.margem_contribuicao_pct < 0.15:
        return ('REVISAR', 'Margem 5-15% — atenção em verba/devolução')
    if dre.aging_medio > 90 and dre.inadimplencia_pct > 0.10:
        return ('ALERTA_CREDITO', 'Margem OK mas crédito comprometido')
    return ('SAUDAVEL', 'Manter — cliente rentável e em dia')
```

---

## 4. TABELA DE FONTES — RESUMO EXECUTIVO

| Fonte | O que entrega | Linhas DDE | Status integração | Bloqueio |
|---|---|---|---|---|
| **Sales Hunter `fat_cliente`** | Fat. bruto, descontos, bonificações | L1, L5, L6, L7 | INGERIDO mas só L1 persistido | D1 — adicionar 4 campos |
| **Sales Hunter `pedidos_produto`** | IPI, vendedor, qtd | L2, L8, L15 | PARCIAL | persistir IPI |
| **Sales Hunter `devolucao_cliente`** | Devoluções | L4 | INGERIDO | OK |
| **Sales Hunter `RelatorioDeMargemPorProduto`** | Custo unitário SKU? | L12 (CMV) | NÃO INTEGRADO | D6 — baixar e validar |
| **SAP módulo fiscal** | ICMS, PIS, COFINS, ICMS-ST por NF | L9, L10a, L10b, L10c | NÃO TEMOS ACESSO | aguarda Leandro |
| **SAP módulo de custos** | CMV por SKU (alternativa a SH) | L12 | NÃO TEMOS ACESSO | aguarda Leandro |
| **SAP módulo financeiro/folha** | Despesas fixas para rateio | L22-L24 | NÃO TEMOS ACESSO | aguarda Leandro |
| **LOG upload mensal `Frete por Cliente`** | Frete CT-e | L14 | SCHEMA DEFINIDO, parser a fazer | parser |
| **LOG upload mensal `Controle Contratos`** | Verba contrato | L16 | SCHEMA DEFINIDO | parser |
| **LOG upload mensal `Despesas Clientes`** | Promotor PDV | L17 | SCHEMA DEFINIDO | parser |
| **LOG upload mensal `Verbas`** | Verba efetivada | L16 | SCHEMA DEFINIDO | parser |
| **Banco `debitos_clientes`** | Aging, inadimplência | L19, I8 | INGERIDO | OK |
| **Banco `vendas` + CDI** | Custo capital giro | L20 | REAL parcial (CDI fixo) | OK |
| **BI futuro POS** | Sell-out real, ruptura, giro | indicadores complementares (não cascata) | NÃO EXISTE | aguarda BI |

---

## 5. SCHEMA POSTGRESQL (consolidação)

> Aproveita o que já existe (cliente, vendas, debitos_clientes) e adiciona o mínimo necessário. **Não criar 9 tabelas se 6 resolvem.**

### Tabelas novas (4)

```sql
-- L14 — Frete CT-e mensal por cliente
CREATE TABLE cliente_frete_mensal (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  ano INT NOT NULL,
  mes INT NOT NULL,
  qtd_ctes INT,
  valor_brl NUMERIC(14,2) NOT NULL,
  fonte VARCHAR(20) NOT NULL DEFAULT 'LOG_UPLOAD',
  classificacao_3tier VARCHAR(10) NOT NULL DEFAULT 'REAL',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, ano, mes, fonte)
);
CREATE INDEX idx_frete_cnpj ON cliente_frete_mensal(cnpj, ano);

-- L16 — Verba (contrato + efetivada)
CREATE TABLE cliente_verba_anual (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  ano INT NOT NULL,
  tipo VARCHAR(20) NOT NULL,  -- 'CONTRATO' | 'EFETIVADA'
  valor_brl NUMERIC(14,2) NOT NULL,
  desc_total_pct NUMERIC(5,2),  -- só CONTRATO
  inicio_vigencia DATE,
  fim_vigencia DATE,
  fonte VARCHAR(20) NOT NULL,
  classificacao_3tier VARCHAR(10) NOT NULL DEFAULT 'REAL',
  observacao TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, ano, tipo, fonte)
);

-- L17 — Promotor PDV mensal
CREATE TABLE cliente_promotor_mensal (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  agencia VARCHAR(80),
  ano INT NOT NULL,
  mes INT NOT NULL,
  valor_brl NUMERIC(14,2) NOT NULL,
  fonte VARCHAR(20) NOT NULL DEFAULT 'LOG_UPLOAD',
  classificacao_3tier VARCHAR(10) NOT NULL DEFAULT 'REAL',
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, agencia, ano, mes)
);

-- DDE consolidado (cache da cascata, recalculado por trigger)
CREATE TABLE cliente_dre_periodo (
  id SERIAL PRIMARY KEY,
  cnpj VARCHAR(14) NOT NULL,
  ano INT NOT NULL,
  mes INT,  -- NULL = anual
  linha VARCHAR(10) NOT NULL,  -- 'L1', 'L11', 'L21', 'I2'...
  conta VARCHAR(80) NOT NULL,
  valor_brl NUMERIC(14,2),  -- nullable porque pode ser PENDENTE
  pct_sobre_receita NUMERIC(6,3),
  fonte VARCHAR(20),
  classificacao_3tier VARCHAR(10),  -- REAL | SINTETICO | PENDENTE | NULL
  fase VARCHAR(2),  -- 'A' | 'B' | 'C'
  observacao TEXT,
  calculado_em TIMESTAMP DEFAULT NOW(),
  UNIQUE(cnpj, ano, mes, linha)
);
CREATE INDEX idx_dre_cnpj_ano ON cliente_dre_periodo(cnpj, ano);
```

### ALTER em `clientes` (D1)

```sql
ALTER TABLE clientes
  ADD COLUMN desc_comercial_pct NUMERIC(5,2),
  ADD COLUMN desc_financeiro_pct NUMERIC(5,2),
  ADD COLUMN total_bonificacao NUMERIC(14,2),
  ADD COLUMN ipi_total NUMERIC(14,2);
```

### ALTER em `vendas` (granularidade do mensal)

```sql
ALTER TABLE vendas
  ADD COLUMN ipi_total NUMERIC(12,2),
  ADD COLUMN desconto_comercial NUMERIC(12,2),
  ADD COLUMN desconto_financeiro NUMERIC(12,2),
  ADD COLUMN bonificacao NUMERIC(12,2);
```

### Anomalias (reaproveitar pattern do motor de regras existente — não criar tabela nova)

A spec antiga propunha `cliente_anomalia` separada. **Recomendação:** reusar `score_historico` + adicionar coluna `anomalias_jsonb` ou criar view materializada. Decisão depende de como o motor existente está estruturado.

---

## 6. ENDPOINTS API (`backend/app/api/routes_dde.py`)

```python
GET /api/dde/cliente/{cnpj}?ano=2025
  → { dre: [...], indicadores: {...}, veredito: '...', faseatura: 'A' }

GET /api/dde/consultor/{nome}?ano=2025
  → consolidado por consultor — soma dos clientes

GET /api/dde/canal/{canal_id}?ano=2025
  → consolidado por canal

GET /api/dde/comparativo?cnpjs=14d,14d,14d&ano=2025
  → tabela lado a lado para cross-cliente

GET /api/dde/score/{cnpj}
  → só o score I9 + breakdown
```

**Scoping multi-canal:** todos os endpoints aplicam `cliente_canal_filter` (já existe em `deps.py` da Onda 1). Consultor não vê DDE de cliente fora do canal dele. Carteira: consultor vê só os clientes dele (mesma regra de `routes_clientes.py`).

---

## 7. ROADMAP FASEADO (espelha decisão D4)

### Fase A — DDE Comercial (entregável agora, ~5 dias dev)

**Entrega:** L1, L2, L3, L4, L5, L6, L7, L8, L11_comercial, L14, L15, L16, L17, L18, L19, L20, L21_comercial, indicadores I2_parcial, I4, I5, I6, I7, I8.

**Pré-requisitos:**
- D1 GO (4 campos no Cliente + 4 em vendas) → 1 migration
- Persistir descontos/bonificações/IPI no `ingest_sales_hunter.py` → 1h código
- Parser de upload manual: 4 parsers (frete, verba, contrato, promotor) → 1-2 dias
- Engine `calcula_dre_comercial(cnpj, ano)` → 1 dia
- Endpoint `/api/dde/cliente/{cnpj}` → meio dia
- UI minimal no Cliente: aba "Análise" com cascata visível → 1 dia

**Limitação:** sem CMV, sem impostos reais. Marcação clara em todas as linhas afetadas: `status='PENDENTE'`, `fase='B'`. UI exibe linhas em cinza com tooltip "Aguardando integração SAP fiscal".

### Fase B — DDE Fiscal + CMV (espera 2 fontes)

**Trigger:** D6 confirma RelatorioDeMargemPorProduto OU SAP libera módulo de custos OU SAP libera módulo fiscal.

**Adiciona:** L9, L10a-c, L11_fiscal, L12, L13, I1, L22-L25, I3.

**Estimativa:** 3-5 dias dev após fonte estar disponível.

### Fase C — Indicadores BI (espera POS cliente)

**Adiciona:** sell-out real, ruptura, giro, sell-through. **Não entram na cascata** — viram tab "Sell-Out" lado a lado com a DDE.

---

## 8. VALIDAÇÃO — GOLDEN MASTER

**Critério único de aceite:** rodar `calcula_dre_comercial('CNPJ_COELHO_DINIZ', 2025)` e cada linha bater **exatamente** com a coluna correspondente do `Análise Crítica - Coelho Diniz - Forense.xlsx` que vocês geram manualmente hoje.

Tolerância: 0,5% (R7) por linha. Acima disso, parar e investigar.

**Antes de iniciar Fase A**, tem que existir na pasta do repo:
- `examples/coelho_diniz/Análise Crítica - Coelho Diniz - Forense.xlsx`
- `examples/coelho_diniz/Verbas 2025.xlsx`
- `examples/coelho_diniz/Frete 2025.xlsx`
- `examples/coelho_diniz/Despesas 2025.xlsx`
- `examples/coelho_diniz/Contrato vigente.xlsx`

Sem golden master, executor inventa estrutura. Bloqueante.

---

## 9. ANTI-PATTERNS — O QUE NÃO FAZER

1. **Não rotear DDE pra LLM.** LLM explica DDE depois (camada 5). Cálculo é determinístico, Python puro, testável. Spec antiga já cometeu esse erro implicitamente — esta corrige.

2. **Não usar alíquota sintética sem marcar.** Se um dia quiser ICMS 12% genérico, OK — mas `classificacao_3tier='SINTETICO'` e UI exibe com `*` e disclaimer. Nunca passar SINTÉTICO como REAL.

3. **Não calcular Margem Bruta sem CMV.** Se L12 = NULL, L13 fica NULL, ponto. Não substituir por "Receita Líquida × % padrão setor" — isso é alucinação financeira.

4. **Não ratear despesa fixa antes de provar valor.** L22-L24 são polêmicos. Sprint inicial pode pular Bloco 5 inteiro. Margem Contribuição (L21) já dá pra decidir saúde do cliente. EBITDA Cliente é refinamento.

5. **Não duplicar engine.** O motor de regras (`motor_regras.py`) que já existe no CRM tem 92 regras. A engine de DDE é um módulo novo (`dde_engine.py`), separado, mas usa as mesmas convenções (R1 Two-Base, R5 CNPJ 14d, R8 zero alucinação). Não tem que reescrever — tem que conviver.

6. **Não esquecer scoping multi-canal.** Onda 1 já implementou. Endpoints de DDE precisam herdar `get_user_canal_ids` desde o dia 1, senão consultor vê DDE de canal alheio.

---

## 10. INTEGRAÇÃO COM SPEC_FEATURE_ANALISE_CRITICA

Esta spec é a camada 4 (Engine de Regras) da SPEC_FEATURE_ANALISE_CRITICA. Mapeamento:

| SPEC_FEATURE_ANALISE_CRITICA | Esta spec |
|---|---|
| Camada 1 — Fontes (8) | Seção 4 — Tabela de Fontes |
| Camada 2 — Pipeline ingestão | Pré-req Fase A (parsers) |
| Camada 3 — Modelo PostgreSQL | Seção 5 — Schema |
| **Camada 4 — Engine** | **Esta spec inteira** |
| Camada 5 — LLM | Não toca aqui — recebe output desta cascata |
| Camada 6 — Interface | Endpoints seção 6 alimentam UI |

**Sequência de implementação combinada:**

1. Inbox SSR + ingest Deskrio (Bloco 3 do PLANO_12H) — **bloqueante de tudo**
2. Onda Schema DDE (esta spec, seção 5) — pode rodar paralelo
3. Parser ZSDFAT (SPEC_FEATURE_ANALISE_CRITICA) — **só com golden master Coelho Diniz na pasta**
4. Engine DDE Fase A (esta spec, seção 7) — depende de 2
5. UI cascata no cliente — depende de 4
6. LLM Resumo CEO — depende de 5

---

## 11. PERGUNTAS ABERTAS

1. **D5 — `produtos.comissao_pct`:** comissão vendedor (vai em L15) ou rebate cliente (vai em L18)? **Leandro confirma com SAP.**
2. **D6 — `RelatorioDeMargemPorProduto`:** baixar 1 sample, abrir XLSX, listar colunas. Se tiver `custo_unitario` ou `custo_caixa`, **L12 desbloqueada**. Cowork vai baixar na próxima sessão.
3. **Acesso SAP fiscal:** sem isso, B2 (impostos) fica indefinidamente em PENDENTE. Vale Leandro provocar TI/contador interno.
4. **CDI exógeno para L20:** consumir API BCB (PTAX) ou hardcode atualizar trimestral? Decisão menor, mas precisa.
5. **Anomalias — tabela nova ou view sobre `score_historico`?** Cowork vai inspecionar `motor_regras.py` antes de decidir. Spec antiga propunha tabela nova; pode ser desnecessário.

---

## 12. RESUMO 3 LINHAS

DDE real = cascata P&L de 7 blocos, 25 linhas, cada uma com fonte, status 3-tier e fase. Fase A entrega 70% da cascata hoje com Sales Hunter + uploads CFO; Fase B completa quando SAP libera fiscal/custos; Fase C agrega BI sell-out. Golden master = bater o Sidecar Coelho Diniz exatamente. Implementar antes de UI ou LLM — engine determinística primeiro.

---

**Versão:** 1.0 — 28/04/2026
**Substitui:** SPEC_DDE_CLIENTE.md (v0)
**Próxima revisão:** após Sprint 1 com Coelho Diniz validado
**Autor:** Cowork (revisor) + briefing Leandro
