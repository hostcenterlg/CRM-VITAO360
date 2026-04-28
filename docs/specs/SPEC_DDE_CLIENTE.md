# SPEC — DDE (Demonstração de Resultado) por Cliente

> **Status:** DRAFT v2 — Substitui SPEC_ANALISE_CRITICA_VIVA.md
> **Autor:** Cowork (professor/revisor)
> **Data:** 2026-04-28
> **Executor:** VSCode Claude Code
> **Natureza:** P&L real por cliente — não dashboard de métricas

---

## 1. O QUE É UMA DDE

DDE = Demonstração de Desempenho Econômico por cliente. É a resposta à pergunta:
**"Esse cliente dá lucro ou dá prejuízo pra Vitao?"**

Não é painel de indicadores. É cascata financeira — cada linha subtrai da anterior até chegar no resultado líquido. Sem cascata completa, não é DDE.

---

## 2. ESTRUTURA DA DDE — CASCATA COMPLETA

```
 RECEITA BRUTA
 (-) Devoluções
 (-) Descontos Comerciais
 (-) Descontos Financeiros
 (-) Bonificações
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 = RECEITA LÍQUIDA COMERCIAL

 (-) IPI
 (-) ICMS
 (-) PIS
 (-) COFINS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 = RECEITA LÍQUIDA FISCAL

 (-) CMV (Custo da Mercadoria Vendida)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 = MARGEM BRUTA

 (-) Frete (custo logístico)
 (-) Comissão do vendedor
 (-) Verbas (conquista + rebate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 = MARGEM DE CONTRIBUIÇÃO

 CONTA CORRENTE (recebíveis)
   Títulos a vencer
   Títulos vencidos
   Pagamentos recebidos
   Dias médio atraso
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 = RESULTADO DO CLIENTE
   (Margem de Contribuição - Inadimplência ajustada)
```

---

## 3. MAPEAMENTO LINHA A LINHA — FONTES REAIS

### Legenda:
- ✅ **DB** — Dado existe no banco PostgreSQL, pronto pra usar
- ✅ **XLSX** — Existe no XLSX do Sales Hunter, precisa integrar ao DB
- ⚠️ **CALC** — Calculável a partir de dados existentes (SINTÉTICO)
- 🔜 **SAP** — Existe no SAP mas Sales Hunter não expõe
- 🔜 **BI** — Virá de integração futura
- ❌ **GAP** — Não existe em nenhuma fonte conhecida

---

### BLOCO 1: RECEITA BRUTA → RECEITA LÍQUIDA COMERCIAL

| # | Linha | Valor exemplo | Fonte | Report SAP | Coluna | Status |
|---|-------|---------------|-------|------------|--------|--------|
| 1 | **RECEITA BRUTA** | R$ 48.200 | fat_cliente | col 23 | `total_faturado` | ✅ DB |
| 2 | (-) Devoluções | -R$ 2.410 | devolucao_cliente | col 18 | `total_devol_total` | ✅ DB |
| 3 | (-) Desc. Comercial | -R$ 2.566 | fat_cliente | col 7 | `desc_comercial` (%) | ⚠️ CALC |
| 4 | (-) Desc. Financeiro | -R$ 964 | fat_cliente | col 8 | `desc_financeiro` (%) | ⚠️ CALC |
| 5 | (-) Bonificações | -R$ 1.928 | fat_cliente | col 16/22 | `bonificacao_mes` / `total_bonificacao` | ✅ XLSX |
| | **= RECEITA LÍQ. COMERCIAL** | **R$ 40.332** | | | | |

**Detalhes técnicos:**

**Linha 1 — Receita Bruta:**
- DB: `clientes.faturamento_total` (agregado) + `vendas.valor_pedido` (por pedido) + `venda_itens.valor_total` (por item)
- Validação: SUM deve bater com fat_empresa ±0.5% (R7)
- Granularidade: por mês (`vendas.mes_referencia`), por pedido, por item de produto
- Code ref: `ingest_sales_hunter.py` line 676: `total_faturado = to_float(row[22])`

**Linha 2 — Devoluções:**
- DB: `clientes.total_devolucao` (valor R$) + `clientes.pct_devolucao` (%) + `clientes.risco_devolucao` (tier)
- Detalhamento: Phase 7 do ingest lê `devolucao_cliente` XLSX
- Risco: BAIXO (<5%) / MEDIO (5-15%) / ALTO (>15%)
- Code ref: `ingest_sales_hunter.py` lines 1397-1406

**Linhas 3-4 — Descontos:**
- XLSX: fat_cliente col 7 (`desc_comercial`) e col 8 (`desc_financeiro`) — formato "5,32%"
- **PROBLEMA:** Armazenado como percentual string, NÃO como valor R$
- **CÁLCULO:** `desconto_r$ = receita_bruta × parse_pct(desc_comercial) / 100`
- **AÇÃO NECESSÁRIA:** Alterar `ingest_sales_hunter.py` Phase 3 para:
  1. Parsear % com `parse_pct()` (já existe no script)
  2. Salvar como float no cliente: `desc_comercial_pct` + `desc_financeiro_pct`
  3. Calcular R$ no endpoint: `receita × pct / 100`
- Code ref: `ingest_sales_hunter.py` lines 671-672 (lidos mas não persistidos)

**Linha 5 — Bonificações:**
- XLSX: fat_cliente col 16 (`bonificacao_mes`) e col 22 (`total_bonificacao`)
- **IMPORTANTE:** Pode ser NEGATIVO (contra-bonificação). Exemplo real: -R$ 35.662,33
- **FÓRMULA SAP:** `faturado_mes = venda_mes - devolucao_mes + bonificacao_mes`
- **PROBLEMA:** Hoje está embutido no `faturado_mes`, não separado
- **AÇÃO NECESSÁRIA:** Extrair separadamente no ingest, salvar em campo próprio
- Code ref: `ingest_sales_hunter.py` line 220: `16: 'bonificacao_mes'`

---

### BLOCO 2: RECEITA LÍQ. COMERCIAL → RECEITA LÍQ. FISCAL

| # | Linha | Valor exemplo | Fonte | Report SAP | Coluna | Status |
|---|-------|---------------|-------|------------|--------|--------|
| 6 | (-) IPI | -R$ 1.209 | pedidos_produto | col 19 | `ipi` (R$) | ✅ XLSX |
| 7 | (-) ICMS | -R$ 5.244 | — | — | — | 🔜 SAP |
| 8 | (-) PIS | -R$ 665 | — | — | — | 🔜 SAP |
| 9 | (-) COFINS | -R$ 3.063 | — | — | — | 🔜 SAP |
| | **= RECEITA LÍQ. FISCAL** | **R$ 30.151** | | | | |

**Detalhes técnicos:**

**Linha 6 — IPI:**
- XLSX: pedidos_produto col 19 — valor em R$ por linha de pedido
- **PROBLEMA:** O ingest Phase 5 (enriquecimento de consultor) **lê col 9 (vendedor) mas IGNORA col 19 (IPI)**
- **AÇÃO NECESSÁRIA:** Expandir Phase 5 para extrair IPI e somar por CNPJ
- **SCHEMA:** Adicionar `ipi_total` ao modelo `Cliente` ou criar tabela de impostos
- Rows: ~23.782 linhas em pedidos_produto (CWB). VV falha (HTTP 302).
- Code ref: `ingest_sales_hunter.py` line 570: `19: 'ipi'` (spec existe, extração não)

**Linhas 7-9 — ICMS, PIS, COFINS:**
- **NÃO EXISTEM no Sales Hunter.** Esses impostos estão no módulo fiscal do SAP (FI/MM), que não é exposto via interface web do Sales Hunter.
- **ALTERNATIVAS:**
  a) Solicitar ao SAP Vitao um relatório fiscal por NF → adicionar ao pipeline
  b) Usar alíquota padrão por UF/regime tributário → SINTÉTICO (flag obrigatório)
  c) Extrair do XML da NF-e se disponível
- **RECOMENDAÇÃO:** Opção (b) como solução intermediária. Alíquotas padrão do Simples/Lucro Presumido são públicas. Marcar como SINTÉTICO na classificação 3-tier.

**Tabela de alíquotas estimadas (se opção B):**

| Imposto | Alíquota média (Lucro Real) | Fonte |
|---------|----------------------------|-------|
| ICMS | 12-18% (varia por UF) | Tabela CONFAZ |
| PIS | 1.65% | Lei 10.637/2002 |
| COFINS | 7.6% | Lei 10.833/2003 |

**⚠️ CLASSIFICAÇÃO:** Se usar alíquotas estimadas = SINTÉTICO. Nunca REAL sem dado fiscal rastreável.

---

### BLOCO 3: RECEITA LÍQ. FISCAL → MARGEM BRUTA

| # | Linha | Valor exemplo | Fonte | Report SAP | Coluna | Status |
|---|-------|---------------|-------|------------|--------|--------|
| 10 | (-) CMV | -R$ 18.091 | — | — | — | 🔜 SAP |
| | **= MARGEM BRUTA** | **R$ 12.060** | | | | |

**Detalhes técnicos:**

**Linha 10 — CMV (Custo da Mercadoria Vendida):**
- **NÃO EXISTE no Sales Hunter.** Custo de produto está no módulo MM (Materials Management) do SAP.
- **SEM CUSTO = SEM MARGEM BRUTA.** Esta é a linha mais crítica da DDE. Sem ela, a DDE para aqui.
- **ALTERNATIVAS:**
  a) Solicitar ao SAP um relatório de custo por produto (custo médio ponderado)
  b) Usar markup reverso se souber a margem média da empresa (ex: ~60% = CMV é 40% da receita)
  c) Relatórios 9-16 do Sales Hunter incluem "Margem" — verificar se contêm custo unitário
- **AÇÃO IMEDIATA:** Verificar se `RelatorioDeMargem` (relatório #9 do Sales Hunter, não integrado) contém custo unitário por produto. Se sim, priorizar integração.
- **RECOMENDAÇÃO:** Dados de custo são L3 (estrutura nova no banco). Precisa campo `custo_unitario` no modelo `Produto` + campo `cmv` calculado no modelo `VendaItem`.

**Schema proposto:**
```python
# Em produto.py:
custo_unitario = Column(Float, nullable=True)  # Custo médio ponderado SAP
margem_bruta_pct = Column(Float, nullable=True)  # Calculado: (preco - custo) / preco

# Em venda_item.py:
cmv_unitario = Column(Float, nullable=True)  # Custo no momento da venda
cmv_total = Column(Float, nullable=True)  # cmv_unitario × quantidade
```

---

### BLOCO 4: MARGEM BRUTA → MARGEM DE CONTRIBUIÇÃO

| # | Linha | Valor exemplo | Fonte | Report SAP | Coluna | Status |
|---|-------|---------------|-------|------------|--------|--------|
| 11 | (-) Frete | -R$ 1.928 | pedidos_produto | col 11 | `tipo_frete` (CIF/FOB) | ❌ GAP |
| 12 | (-) Comissão vendedor | -R$ 1.446 | produto + venda | — | `comissao_pct` | ⚠️ CALC |
| 13 | (-) Verbas (conquista) | -R$ 800 | — | — | — | 🔜 SAP |
| 14 | (-) Verbas (rebate) | -R$ 1.600 | — | — | — | 🔜 SAP |
| | **= MARGEM DE CONTRIBUIÇÃO** | **R$ 6.286** | | | | |

**Detalhes técnicos:**

**Linha 11 — Frete:**
- XLSX: pedidos_produto col 11 = `tipo_frete` (string: "CIF", "FOB", "GRATIS")
- **PROBLEMA:** É o TIPO de frete, não o CUSTO em R$. CIF = Vitao paga, FOB = cliente paga.
- **O VALOR do frete em R$ NÃO está no Sales Hunter.** Está no TMS (Transportation Management System) ou no módulo SD/LOG do SAP.
- **ALTERNATIVA:** Usar custo médio de frete por UF/região como proxy SINTÉTICO
- **O que PODEMOS fazer HOJE:** Classificar clientes como CIF vs FOB (impacta quem paga). Se CIF, Vitao absorve → deduz da margem. Se FOB, cliente paga → não deduz.

**Linha 12 — Comissão:**
- DB: `produtos.comissao_pct` existe (% por produto na tabela)
- **CÁLCULO:** `comissao_r$ = SUM(venda_itens.valor_total × produto.comissao_pct / 100)`
- **INCERTEZA:** `comissao_pct` pode ser comissão do representante, não exatamente o custo da Vitao. Precisa confirmar.
- **O que PODEMOS fazer HOJE:** Calcular o total de comissão estimada por cliente com base no mix de produtos que compra.

**Linhas 13-14 — Verbas:**
- **NÃO EXISTEM no Sales Hunter.** Verbas de conquista (bonificação de entrada) e rebate (% sobre compras acumuladas) estão no módulo CO (Controlling) do SAP.
- **DIFERENÇA DE BONIFICAÇÃO (linha 5):** Bonificação do fat_cliente é mercadoria dada grátis (produto bonificado). Verba de conquista é dinheiro/crédito dado pro cliente começar a comprar. Verba de rebate é devolução financeira sobre volume.
- **AÇÃO:** Quando SAP/BI expuser esses dados, criar tabela `verbas_clientes` (schema na spec anterior).

---

### BLOCO 5: CONTA CORRENTE (RECEBÍVEIS)

| # | Linha | Valor exemplo | Fonte | Tabela DB | Campo | Status |
|---|-------|---------------|-------|-----------|-------|--------|
| 15 | Total títulos emitidos | R$ 12.800 | SAP debitos | `debitos_clientes` | `SUM(valor)` | ✅ DB |
| 16 | Títulos a vencer | R$ 8.200 | SAP debitos | `debitos_clientes` | `WHERE status='A_VENCER'` | ✅ DB |
| 17 | Títulos vencidos | R$ 4.600 | SAP debitos | `debitos_clientes` | `WHERE status='VENCIDO'` | ✅ DB |
| 18 | Pagamentos recebidos | R$ 14.200 | SAP debitos | `debitos_clientes` | `WHERE status='PAGO'` | ✅ DB |
| 19 | Dias médio atraso | 18d | Calculado | `debitos_clientes` | `AVG(dias_atraso)` | ✅ DB |
| 20 | Taxa adimplência | 78% | Calculado | `debitos_clientes` | `COUNT(PAGO)/COUNT(*)` | ⚠️ CALC |
| 21 | Último pagamento | 15/04/26 | SAP debitos | `debitos_clientes` | `MAX(data_pagamento)` | ✅ DB |
| 22 | Saldo verbas devidas | R$ 480 | — | — | — | 🔜 SAP |

**Detalhes técnicos:**

Bloco 5 está **100% disponível** (exceto verbas devidas). O modelo `DebitoCliente` tem todos os campos necessários: `cnpj`, `valor`, `data_vencimento`, `data_pagamento`, `dias_atraso`, `status` (PAGO/VENCIDO/A_VENCER), `nro_nfe`, `parcela`.

**Endpoint proposto:** `GET /api/clientes/{cnpj}/dde/conta-corrente`

```json
{
  "total_titulos": 12800.00,
  "a_vencer": 8200.00,
  "vencido": 4600.00,
  "pago_total": 14200.00,
  "dias_medio_atraso": 18,
  "taxa_adimplencia": 0.78,
  "ultimo_pagamento": "2026-04-15",
  "score_pagamento": "MEDIO",
  "aging": {
    "0_30d": 3200.00,
    "31_60d": 1400.00,
    "61_90d": 0.00,
    "acima_90d": 0.00
  },
  "titulos_abertos": [
    {"nro_nfe": "123456", "parcela": "1/3", "valor": 2800.00, "vencimento": "2026-04-10", "dias_atraso": 18, "status": "VENCIDO"}
  ]
}
```

---

### BLOCO 6: MIX DE PRODUTOS (complemento da DDE)

| # | Linha | Fonte | Status |
|---|-------|-------|--------|
| 23 | SKUs ativos (de 242) | venda_itens + produtos | ✅ DB |
| 24 | Curva ABC do cliente | venda_itens agrupado | ✅ DB |
| 25 | Desconto médio praticado | venda_itens.desconto_pct | ✅ DB |
| 26 | Preço tabela vs praticado | produtos.preco_tabela vs venda_itens.preco_unitario | ✅ DB |
| 27 | SKUs dormentes (comprava, parou) | venda_itens temporal | ⚠️ CALC |
| 28 | Cross-sell (clientes similares compram) | análise de cesta | ⚠️ CALC |
| 29 | Margem por produto | produtos.custo_unitario vs preco | 🔜 SAP |

---

## 4. RESULTADO FINAL DA DDE

```
 MARGEM DE CONTRIBUIÇÃO
 (-) Provisão de inadimplência (títulos vencidos × % de risco)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 = RESULTADO DO CLIENTE

 Classificação:
   LUCRATIVO    (resultado > 5% da receita)
   EQUILIBRADO  (resultado 0-5%)
   DEFICITÁRIO  (resultado < 0%)
   INDEFINIDO   (dados insuficientes para calcular)
```

---

## 5. O QUE TEMOS vs O QUE FALTA — MAPA DA VERDADE

### DISPONÍVEL HOJE (implementar agora):

```
RECEITA BRUTA ────────────────── ✅ fat_cliente.total_faturado
(-) Devoluções ───────────────── ✅ devolucao_cliente + clientes.total_devolucao
(-) Desc. Comercial (% → R$) ── ⚠️ fat_cliente col 7 (% existe, calcular R$)
(-) Desc. Financeiro (% → R$) ─ ⚠️ fat_cliente col 8 (% existe, calcular R$)
(-) Bonificações ─────────────── ✅ fat_cliente col 16/22 (extrair do ingest)
                                ━━━━━━━━━━━━━━━━━━━━━━━━━━
                                = RECEITA LÍQ. COMERCIAL ← ATÉ AQUI PODEMOS IR

(-) IPI ──────────────────────── ✅ pedidos_produto col 19 (existe, não integrado)
                                ━━━━━━━━━━━━━━━━━━━━━━━━━━
                                = RECEITA LÍQ. COMERCIAL - IPI

CONTA CORRENTE ───────────────── ✅ debitos_clientes (100% disponível)
MIX DE PRODUTOS ──────────────── ✅ venda_itens + produtos (100% disponível)
COMISSÃO ESTIMADA ────────────── ⚠️ produto.comissao_pct × venda (calculável)
```

### PRECISA DO SAP (módulos internos):

```
(-) ICMS ─────────── 🔜 Módulo FI/fiscal ou XML NF-e
(-) PIS ──────────── 🔜 Módulo FI/fiscal
(-) COFINS ───────── 🔜 Módulo FI/fiscal
(-) CMV ──────────── 🔜 Módulo MM/custos (MAIS CRÍTICO DE TODOS)
(-) Frete R$ ─────── 🔜 TMS ou SD/logística
(-) Verbas ───────── 🔜 Módulo CO/controlling
```

### RESULTADO:

| Com dados de HOJE | Com SAP módulos internos | Com SAP + BI |
|-------------------|-------------------------|-------------|
| Receita Líquida Comercial - IPI | Margem Bruta + Margem de Contribuição | DDE completa + Sell-out |
| + Conta Corrente completa | + Impostos reais | + Giro de estoque |
| + Mix de Produtos | + Custo real | + Ruptura |
| + Comissão estimada | + Frete real | + Sell-through |
| **~45% da DDE** | **~90% da DDE** | **100% da DDE** |

---

## 6. FASES DE IMPLEMENTAÇÃO

### FASE A — DDE PARCIAL (com dados de hoje) — ~4h implementação

**O que entrega:** Cascata até Receita Líquida Comercial + Conta Corrente + Mix + Score

**Alterações no ingest (`ingest_sales_hunter.py`):**
1. Phase 3: Extrair `desc_comercial_pct`, `desc_financeiro_pct` do fat_cliente (cols 7-8)
2. Phase 3: Extrair `bonificacao_mes`, `total_bonificacao` separadamente (cols 16, 22)
3. Phase 5: Extrair `ipi` do pedidos_produto (col 19), somar por CNPJ

**Alterações no schema (migrations):**
```python
# clientes:
desc_comercial_pct = Column(Float, nullable=True)    # % desconto comercial
desc_financeiro_pct = Column(Float, nullable=True)   # % desconto financeiro
total_bonificacao = Column(Float, nullable=True)      # R$ bonificação acumulada
ipi_total = Column(Float, nullable=True)              # R$ IPI acumulado
```

**Novo router:** `backend/app/routes/routes_dde.py`

**Endpoints:**
| Método | Rota | Retorna |
|--------|------|---------|
| GET | `/api/clientes/{cnpj}/dde` | DDE completa (todas linhas, null onde falta) |
| GET | `/api/clientes/{cnpj}/dde/receita` | Bloco 1: Receita Bruta → Líquida Comercial |
| GET | `/api/clientes/{cnpj}/dde/conta-corrente` | Bloco 5: Títulos, pagamentos, aging |
| GET | `/api/clientes/{cnpj}/dde/mix` | Bloco 6: Produtos, cross-sell, desconto |
| GET | `/api/clientes/{cnpj}/dde/score` | Score composto (0-10) |

**Frontend:** `frontend/src/pages/ClienteDetalhe/DDE.tsx`
- Componente em formato de cascata financeira (não cards soltos)
- Linhas disponíveis em preto, linhas sem dados em cinza itálico com "(aguardando SAP)"
- Barra de progresso: "DDE 45% completa — faltam: CMV, impostos, frete, verbas"

**Two-Base:** VENDA-side only. Todos valores monetários da DDE vêm de registros tipo VENDA. ✅

**Canal scoping:** Vendedor só vê DDE de clientes do seu canal. ✅

### FASE B — DDE COM IMPOSTOS E CUSTO (com SAP módulos internos) — ~3h

**Pré-requisito:** SAP Vitao expor relatório de custo por produto + relatório fiscal por NF

**Alterações:**
1. Novo report no pipeline: `RelatorioDeMargem` (relatório #9 do Sales Hunter — verificar conteúdo)
2. Adicionar `custo_unitario` ao modelo `Produto`
3. Adicionar `cmv_unitario`, `cmv_total` ao modelo `VendaItem`
4. Criar `ingest_impostos.py` para NF-e ou relatório fiscal SAP
5. Tabela `impostos_nf` com: cnpj, nro_nfe, icms, pis, cofins, ipi (por NF)

**Resultado:** Cascata completa até Margem Bruta. Com frete e verbas, até Margem de Contribuição.

### FASE C — DDE COMPLETA (com SAP + BI) — ~2h

**Pré-requisito:** TMS expor custo frete + SAP CO expor verbas + BI expor sell-out

**Alterações:**
1. Tabela `verbas_clientes` (schema da spec anterior)
2. Campo `frete_total` no cliente (ou tabela de frete por NF)
3. Integração BI para sell-out (giro, ruptura, sell-through)
4. Score final com TODAS as dimensões

---

## 7. SCORE DO CLIENTE (calculável hoje)

**Componentes disponíveis (6 de 8):**

| Componente | Peso | Fórmula | Status |
|------------|------|---------|--------|
| Faturamento vs Meta | 20% | `min(realizado/meta, 1.0) × 10` | ✅ DB |
| Tendência YoY | 10% | `clamp((variacao+10)/20, 0, 1) × 10` | ✅ CALC |
| Adimplência | 25% | `taxa_adimplencia × 10` | ✅ DB |
| Penetração SKUs | 10% | `min(skus_cliente/20, 1.0) × 10` | ✅ CALC |
| Frequência compras | 10% | `min(compras_12m/12, 1.0) × 10` | ✅ DB |
| Risco devolução | 10% | `BAIXO=10, MEDIO=5, ALTO=0` | ✅ DB |
| Margem bruta | 10% | `margem_pct × 10 / 30` (0-30% → 0-10) | 🔜 SAP |
| Inadimplência líquida | 5% | `10 - (vencido/total_titulos × 10)` | ✅ DB |

**Score hoje (sem margem bruta):** Recalcula peso de 90% para 100%. 7 componentes. Marcar como "Score parcial (sem margem)".

**Classificação:**

| Score | Label | Cor (R9 LIGHT) | Ação sugerida |
|-------|-------|----------------|---------------|
| 8.0-10.0 | EXCELENTE | #00B050 | Manter, expandir mix |
| 6.0-7.9 | SAUDÁVEL | #FFC000 | Oportunidade de crescimento |
| 4.0-5.9 | ATENÇÃO | #FF8C00 | Cobrar inadimplência, revisar mix |
| 0.0-3.9 | CRÍTICO | #FF0000 | Reunião urgente, plano de recuperação |

---

## 8. PLANO DE AÇÃO AUTOMÁTICO (regras IF/THEN)

```python
acoes = []

# Inadimplência
if titulos_vencidos > 0:
    acoes.append(f"Cobrar {n_vencidos} título(s) vencido(s) — R$ {total_vencido:,.2f}")

# Mix pobre
if penetracao_skus < 5:
    acoes.append(f"Ampliar mix: apenas {skus_ativos} de 242 SKUs. Sugerir: {cross_sell[:3]}")

# Queda de vendas
if tendencia_yoy < -10:
    acoes.append(f"Queda de {abs(tendencia_yoy):.0f}% vs ano anterior. Agendar visita.")

# Devolução alta
if risco_devolucao == "ALTO":
    acoes.append(f"Devolução {pct_devolucao:.1f}% — investigar causa. Qualidade? Prazo?")

# Bonificação negativa
if total_bonificacao < 0:
    acoes.append(f"Contra-bonificação de R$ {abs(total_bonificacao):,.2f} — verificar.")

# Desconto excessivo
if desc_comercial_pct > 15:
    acoes.append(f"Desconto comercial de {desc_comercial_pct:.1f}% — acima do padrão.")

# Meta distante
if pct_alcancado < 25 and mes_atual > 3:
    acoes.append(f"Apenas {pct_alcancado:.0f}% da meta no mês {mes_atual}. Risco de não atingir.")
```

---

## 9. DECISÕES L3 NECESSÁRIAS

| # | Decisão | Impacto |
|---|---------|---------|
| 1 | Adicionar 4 campos ao modelo `Cliente` (desc_comercial_pct, desc_financeiro_pct, total_bonificacao, ipi_total) | Schema change + migration |
| 2 | Criar router `routes_dde.py` (novo arquivo) | Estrutura backend |
| 3 | Usar alíquotas SINTÉTICAS para ICMS/PIS/COFINS enquanto SAP fiscal não chega? | Dados sintéticos na DDE |
| 4 | Prioridade: implementar Fase A agora ou esperar CMV do SAP? | Timing |
| 5 | `produtos.comissao_pct` é comissão do vendedor ou rebate do cliente? | Afeta cálculo da linha 12 |
| 6 | Verificar se `RelatorioDeMargem` (report #9 do Sales Hunter) contém custo unitário | Pode desbloquear CMV |

---

## 10. VALIDAÇÃO (DETECTOR DE MENTIRA aplicável)

**Nível 1 — Existência:**
- [ ] Router routes_dde.py existe e responde
- [ ] Componente DDE.tsx renderiza
- [ ] Endpoint /dde retorna JSON com todas linhas

**Nível 2 — Substância:**
- [ ] Receita Bruta bate com `clientes.faturamento_total`
- [ ] Devoluções batem com `clientes.total_devolucao`
- [ ] Descontos calculados a partir de % real (não hardcoded)
- [ ] Linhas sem dados = `null` (NUNCA valor inventado)
- [ ] Classificação 3-tier: REAL para dados DB, SINTÉTICO para cálculos, null para gaps

**Nível 3 — Conexão:**
- [ ] Canal scoping aplicado em todos endpoints DDE
- [ ] DDE acessível pela ficha do cliente
- [ ] Score recalculado automaticamente com dados novos
- [ ] Plano de ação gerado dinamicamente

---

*Spec baseada em auditoria real do pipeline `ingest_sales_hunter.py` e dos 13 relatórios SAP. Nenhuma fonte inventada. Gaps declarados explicitamente.*
