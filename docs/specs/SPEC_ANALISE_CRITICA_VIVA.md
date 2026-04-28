# SPEC — Análise Crítica Viva do Cliente

> **Status:** DRAFT — Aguardando aprovação L3 (nova feature)
> **Autor:** Cowork (professor/revisor)
> **Data:** 2026-04-28
> **Executor:** VSCode Claude Code
> **Prioridade:** Onda 2-3 (após deploy PROD e pipeline automático)

---

## 1. VISÃO GERAL

Ao abrir a ficha de um cliente no CRM, mostrar uma **análise financeira completa e viva** — atualizada automaticamente pelo pipeline. Não é relatório estático: é um P&L por cliente que respira junto com SAP, Sales Hunter e BI.

### O que o vendedor vê ao abrir um cliente:

```
┌─────────────────────────────────────────────────────┐
│  ANÁLISE CRÍTICA — CNPJ 12.345.678/0001-90          │
│  Razão Social: SUPERMERCADO EXEMPLO LTDA            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  SELL-IN (Faturamento Vitao → Cliente)              │
│  ├── 2025: R$ 48.200   │  2026 YTD: R$ 15.600      │
│  ├── Ticket médio: R$ 4.820  │  Compras: 10x/ano   │
│  └── Tendência: ▲ +12% vs ano anterior              │
│                                                     │
│  SELL-OUT (Cliente → Consumidor Final)    [BI]      │
│  ├── Giro médio: 45 dias                            │
│  ├── Ruptura: 3 SKUs sem reposição há 60d           │
│  └── Penetração: 18/42 SKUs ativos                  │
│                                                     │
│  VERBAS                                   [SAP]     │
│  ├── Conquista: R$ 2.400 (bonificação entrada)      │
│  ├── Gerada: R$ 1.920 (4% s/ faturamento)           │
│  ├── Devida: R$ 480 (saldo a pagar)                 │
│  └── Saldo líquido: R$ 1.440                        │
│                                                     │
│  CONTA CORRENTE                           [SAP/SH]  │
│  ├── Total títulos: R$ 12.800                       │
│  ├── A vencer: R$ 8.200  │  Vencido: R$ 4.600      │
│  ├── Dias médio atraso: 18d                         │
│  └── Score de pagamento: ⚠️ MÉDIO                   │
│                                                     │
│  PAGAMENTOS RECEBIDOS                     [SAP/SH]  │
│  ├── Últimos 90d: R$ 14.200 recebidos               │
│  ├── Taxa de adimplência: 78%                       │
│  └── Último pagamento: 2026-04-15                   │
│                                                     │
│  MIX DE PRODUTOS                          [DB]      │
│  ├── 18 SKUs ativos (de 242 possíveis)              │
│  ├── Curva A: 4 produtos (62% do faturamento)       │
│  ├── Margem média: --% [aguardando custo SAP]       │
│  └── Cross-sell: 6 SKUs recomendados                │
│                                                     │
│  SCORE GERAL: 7.2/10 — SAUDÁVEL                    │
│  Plano de ação: Incluir granola linha premium,      │
│  regularizar 2 títulos vencidos, propor mix castanha│
└─────────────────────────────────────────────────────┘
```

---

## 2. AS 7 DIMENSÕES — Mapeamento de Fontes

### Legenda de disponibilidade:
- ✅ **EXISTE** — Dado já está no banco, só precisa de endpoint/cálculo
- 🔜 **SAP** — Virá do SAP (próximas extrações Sales Hunter)
- 🔜 **BI** — Virá do BI (integração futura)
- ❌ **NÃO EXISTE** — Precisa de fonte nova ou cálculo derivado

---

### DIMENSÃO 1: SELL-IN (Faturamento Vitao → Cliente)

**Status: ✅ EXISTE COMPLETO**

| Dado | Tabela | Campo | Status |
|------|--------|-------|--------|
| Faturamento total | `clientes` | `faturamento_total` | ✅ |
| Faturamento por período | `vendas` | `SUM(valor_pedido) GROUP BY mes_referencia` | ✅ |
| Qtd compras | `clientes` | `n_compras` | ✅ |
| Ticket médio | `clientes` | `valor_ultimo_pedido` / calculado | ✅ |
| Ciclo médio (dias entre compras) | `clientes` | `ciclo_medio` | ✅ |
| Última compra | `clientes` | `data_ultima_compra` | ✅ |
| Tendência YoY | `vendas` | Calculado: SUM 2026 vs SUM 2025 | ✅ cálculo |
| Meta vs realizado | `metas` | `meta_sap`, `realizado` | ✅ |
| Consultor responsável | `clientes` | `consultor` | ✅ |
| Condição pagamento | `vendas` | `condicao_pagamento` | ✅ |

**Endpoint necessário:** `GET /api/clientes/{cnpj}/analise-critica/sell-in`
```json
{
  "faturamento_2025": 48200.00,
  "faturamento_2026_ytd": 15600.00,
  "variacao_yoy_pct": 12.4,
  "n_compras_2025": 10,
  "n_compras_2026_ytd": 4,
  "ticket_medio": 4820.00,
  "ciclo_medio_dias": 36,
  "ultima_compra": "2026-03-18",
  "meta_anual": 60000.00,
  "realizado_acumulado": 15600.00,
  "pct_alcancado": 26.0,
  "mensal": [
    {"mes": "2026-01", "valor": 4800.00},
    {"mes": "2026-02", "valor": 5200.00},
    {"mes": "2026-03", "valor": 5600.00}
  ]
}
```

**Two-Base:** VENDA-side only. Todos os valores vêm de `vendas.valor_pedido`. ✅

---

### DIMENSÃO 2: SELL-OUT (Cliente → Consumidor Final)

**Status: 🔜 BI FUTURO — NÃO existe hoje**

| Dado | Fonte futura | Status |
|------|-------------|--------|
| Giro de estoque (dias) | BI — dados POS do cliente | 🔜 BI |
| Ruptura de SKUs | BI — out-of-stock tracking | 🔜 BI |
| Penetração de SKUs | Calculável: VendaItem vs Produto catálogo | ✅ parcial |
| Sell-through rate | BI — sell-in vs sell-out ratio | 🔜 BI |

**O que PODEMOS fazer HOJE (sem BI):**
- **Penetração de SKUs:** Contar quantos produtos distintos o cliente comprou vs total do catálogo → já temos `venda_itens` + `produtos`
- **Frequência por SKU:** Quais produtos compra sempre vs esporádicos → `venda_itens` agrupado
- **SKUs dormentes:** Produtos que comprava e parou → gap analysis temporal

**Endpoint (versão parcial):** `GET /api/clientes/{cnpj}/analise-critica/sell-out`
```json
{
  "fonte": "PARCIAL — sem dados POS/BI",
  "skus_ativos": 18,
  "skus_catalogo": 242,
  "penetracao_pct": 7.4,
  "skus_dormentes": [
    {"produto": "Granola Tradicional 800g", "ultima_compra": "2025-09-15", "dias_sem_compra": 225}
  ],
  "skus_frequentes": [
    {"produto": "Mix Castanhas 200g", "compras_12m": 8, "valor_12m": 3200.00}
  ]
}
```

**Nota:** Sell-out REAL (quanto o cliente vendeu pro consumidor) só virá quando tiver integração BI com POS. Até lá, usamos proxy de penetração e frequência.

---

### DIMENSÃO 3: VERBA CONQUISTA (Bonificação de Entrada)

**Status: 🔜 SAP — Campo existe no SAP, precisa extrair**

| Dado | Fonte | Status |
|------|-------|--------|
| Verba conquista por cliente | SAP — campo bonificação/verba | 🔜 SAP |
| Histórico de verbas | SAP — relatórios de bonificação | 🔜 SAP |

**O que sabemos:**
- SAP tem campos de bonificação por pedido/cliente
- Sales Hunter PODE ter relatório de verbas (verificar lista de 14 relatórios)
- Não existe tabela/modelo no banco hoje para verbas

**Ação necessária:**
1. Verificar se Sales Hunter tem relatório de verbas/bonificação
2. Se sim: adicionar ao `download_sales_hunter.py` e criar `ingest_verbas.py`
3. Se não: extrair diretamente do SAP BI

**Modelo proposto (QUANDO tiver dados):**
```python
class VerbaCliente(Base):
    __tablename__ = "verbas_clientes"
    id = Column(Integer, primary_key=True)
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"))
    tipo = Column(String(20))  # CONQUISTA, GERADA, PAGA
    valor = Column(Float)
    data_referencia = Column(Date)
    pedido_origem = Column(String(50), nullable=True)
    fonte = Column(String(20), default="SAP")
    classificacao_3tier = Column(String(15), default="REAL")
```

**⚠️ DECISÃO L3:** Criar tabela `verbas_clientes` — estrutura nova no banco.

---

### DIMENSÃO 4: VERBA GERADA (Comissão/Rebate sobre Faturamento)

**Status: ✅ PARCIAL — calculável a partir de dados existentes**

| Dado | Fonte | Status |
|------|-------|--------|
| Comissão % por produto | `produtos.comissao_pct` | ✅ existe |
| Valor comissão por venda | Calculado: `venda_itens.valor_total × produto.comissao_pct` | ✅ cálculo |
| Total verba gerada por cliente | Agregação do cálculo acima | ✅ cálculo |

**O que PODEMOS fazer HOJE:**
```sql
SELECT 
    v.cnpj,
    SUM(vi.valor_total * p.comissao_pct / 100) as verba_gerada_total
FROM vendas v
JOIN venda_itens vi ON vi.venda_id = v.id
JOIN produtos p ON p.id = vi.produto_id
WHERE v.cnpj = :cnpj
GROUP BY v.cnpj
```

**Ressalva:** `comissao_pct` no produto pode ser a comissão do vendedor, não o rebate do cliente. Precisamos confirmar com Leandro se é o campo correto ou se verba gerada vem de outra lógica SAP.

**⚠️ PERGUNTA para Leandro:** `produtos.comissao_pct` é comissão do vendedor ou rebate/verba do cliente? Se for do vendedor, verba gerada precisa de campo SAP separado.

---

### DIMENSÃO 5: VERBA DEVIDA (Saldo de Verba a Pagar)

**Status: 🔜 SAP — Depende de Dimensão 3 + 4**

| Dado | Cálculo | Status |
|------|---------|--------|
| Verba devida | Verba gerada - Verba paga | 🔜 depende SAP |

**Lógica:**
```
verba_devida = verba_conquista + verba_gerada - verba_paga
```

- `verba_conquista` → 🔜 SAP (Dimensão 3)
- `verba_gerada` → ✅ parcial (Dimensão 4, se comissao_pct correto)
- `verba_paga` → 🔜 SAP (precisa de campo/relatório de pagamento de verbas)

**Ação:** Só implementável APÓS ter dados de verba do SAP. Endpoint retorna null até lá.

---

### DIMENSÃO 6: CONTA CORRENTE (Títulos e Recebíveis)

**Status: ✅ EXISTE COMPLETO**

| Dado | Tabela | Campo | Status |
|------|--------|-------|--------|
| Total títulos | `debitos_clientes` | `SUM(valor)` | ✅ |
| A vencer | `debitos_clientes` | `SUM(valor) WHERE status='A_VENCER'` | ✅ |
| Vencidos | `debitos_clientes` | `SUM(valor) WHERE status='VENCIDO'` | ✅ |
| Dias médio atraso | `debitos_clientes` | `AVG(dias_atraso) WHERE status='VENCIDO'` | ✅ |
| Total débitos acumulado | `clientes` | `total_debitos` | ✅ |
| Risco devolução | `clientes` | `risco_devolucao` (BAIXO/MEDIO/ALTO) | ✅ |
| Detalhe por NF | `debitos_clientes` | `nro_nfe, parcela, valor, data_vencimento` | ✅ |

**Endpoint:** `GET /api/clientes/{cnpj}/analise-critica/conta-corrente`
```json
{
  "total_titulos": 12800.00,
  "a_vencer": 8200.00,
  "vencido": 4600.00,
  "pago_total": 14200.00,
  "dias_medio_atraso": 18,
  "risco": "MEDIO",
  "score_pagamento": 6.5,
  "titulos": [
    {
      "nro_nfe": "123456",
      "parcela": "1/3",
      "valor": 2800.00,
      "data_vencimento": "2026-04-10",
      "data_pagamento": null,
      "status": "VENCIDO",
      "dias_atraso": 18
    }
  ]
}
```

**Two-Base:** VENDA-side (débitos são financeiros). ✅

---

### DIMENSÃO 7: PAGAMENTOS RECEBIDOS

**Status: ✅ EXISTE COMPLETO**

| Dado | Tabela | Campo | Status |
|------|--------|-------|--------|
| Pagamentos no período | `debitos_clientes` | `SUM(valor) WHERE status='PAGO' AND data_pagamento >= :inicio` | ✅ |
| Último pagamento | `debitos_clientes` | `MAX(data_pagamento)` | ✅ |
| Taxa adimplência | Calculado | `COUNT(PAGO) / COUNT(*)` | ✅ cálculo |
| Histórico mensal | `debitos_clientes` | Agrupado por mês de pagamento | ✅ |

**Incluso no endpoint de conta-corrente acima.**

---

## 3. MIX DE PRODUTOS (Dimensão Bônus — já existe)

**Status: ✅ EXISTE COMPLETO**

| Dado | Tabela | Campo | Status |
|------|--------|-------|--------|
| Produtos que compra | `venda_itens` + `produtos` | JOIN por produto_id | ✅ |
| Curva ABC por produto | `produtos` | `curva_abc_produto` | ✅ |
| Desconto médio | `venda_itens` | `AVG(desconto_pct)` | ✅ |
| Preço tabela vs praticado | `produtos.preco_tabela` vs `venda_itens.preco_unitario` | ✅ |
| Cross-sell sugerido | Calculado | Clientes similares compram X | ✅ cálculo |
| Margem por produto | `produtos` | **❌ NÃO TEM custo** | 🔜 SAP |

**Endpoint:** `GET /api/clientes/{cnpj}/analise-critica/mix-produtos`
```json
{
  "skus_ativos": 18,
  "skus_catalogo": 242,
  "penetracao_pct": 7.4,
  "curva_a_qtd": 4,
  "curva_a_pct_faturamento": 62.0,
  "desconto_medio_pct": 8.5,
  "produtos": [
    {
      "nome": "Mix Castanhas 200g",
      "categoria": "Castanhas",
      "curva": "A",
      "qtd_comprada_12m": 480,
      "valor_12m": 3200.00,
      "preco_tabela": 8.90,
      "preco_praticado_medio": 6.67,
      "desconto_medio_pct": 25.0
    }
  ],
  "cross_sell": [
    {
      "produto": "Granola Premium 800g",
      "motivo": "82% dos clientes do mesmo porte compram",
      "margem_estimada": null
    }
  ]
}
```

---

## 4. SCORE GERAL DO CLIENTE

**Cálculo composto (0-10):**

| Componente | Peso | Fonte | Disponível |
|------------|------|-------|------------|
| Faturamento vs Meta | 25% | Sell-in | ✅ |
| Tendência YoY | 15% | Sell-in | ✅ |
| Adimplência (pagamentos) | 25% | Conta corrente | ✅ |
| Penetração de SKUs | 15% | Mix produtos | ✅ |
| Frequência de compra | 10% | Sell-in | ✅ |
| Risco devolução | 10% | Cliente | ✅ |

**Fórmula:**
```python
score = (
    (pct_meta_alcancada / 100 * 10) * 0.25 +       # 0-10 proporcional à meta
    (min(variacao_yoy + 10, 20) / 20 * 10) * 0.15 + # -10% a +10% → 0 a 10
    (taxa_adimplencia * 10) * 0.25 +                 # 0% a 100% → 0 a 10
    (penetracao_skus / 20 * 10) * 0.15 +             # 0% a 20% → 0 a 10
    (min(n_compras_12m, 12) / 12 * 10) * 0.10 +     # 0 a 12 compras → 0 a 10
    (10 - risco_devolucao_score) * 0.10              # BAIXO=10, MEDIO=5, ALTO=0
)
```

**Classificação:**
| Score | Label | Cor |
|-------|-------|-----|
| 8-10 | EXCELENTE | #00B050 (verde) |
| 6-7.9 | SAUDÁVEL | #FFC000 (amarelo) |
| 4-5.9 | ATENÇÃO | #FF8C00 (laranja) |
| 0-3.9 | CRÍTICO | #FF0000 (vermelho) |

---

## 5. PLANO DE AÇÃO SUGERIDO (IA)

Baseado nas 7 dimensões, gerar automaticamente:

```
SE score < 4 → "Cliente em risco. Priorizar regularização de [N] títulos vencidos."
SE penetracao < 5% → "Oportunidade de mix: sugerir [produtos cross-sell]"
SE tendencia < -10% → "Queda de [X]%. Agendar visita de reativação."
SE dias_atraso > 30 → "Inadimplência: [N] títulos com [X] dias de atraso médio."
SE verba_devida > 0 → "Verba pendente de R$ [X]. Negociar compensação."
```

Versão 1: regras IF/THEN (implementável hoje).
Versão 2: LLM gera texto natural a partir das métricas (Onda IA).

---

## 6. ARQUITETURA TÉCNICA

### Backend — Novo router

**Arquivo:** `backend/app/routes/routes_analise_critica.py`

| Endpoint | Método | Descrição | Fonte |
|----------|--------|-----------|-------|
| `/api/clientes/{cnpj}/analise-critica` | GET | Resumo completo (todas dimensões) | Agregação |
| `/api/clientes/{cnpj}/analise-critica/sell-in` | GET | Sell-in detalhado | vendas, metas |
| `/api/clientes/{cnpj}/analise-critica/sell-out` | GET | Sell-out (parcial) | venda_itens, produtos |
| `/api/clientes/{cnpj}/analise-critica/verbas` | GET | Verbas (quando disponível) | verbas_clientes (🔜) |
| `/api/clientes/{cnpj}/analise-critica/conta-corrente` | GET | Títulos e recebíveis | debitos_clientes |
| `/api/clientes/{cnpj}/analise-critica/mix-produtos` | GET | Mix e cross-sell | venda_itens, produtos |
| `/api/clientes/{cnpj}/analise-critica/score` | GET | Score composto | Cálculo agregado |

**Canal scoping:** Todos endpoints passam por `cliente_canal_filter` — vendedor só vê clientes do seu canal.

### Frontend — Nova aba/seção na ficha do cliente

**Arquivo:** `frontend/src/pages/ClienteDetalhe/AnaliseCritica.tsx`

- Componente React com 7 cards (1 por dimensão)
- Gráfico de tendência (sell-in mensal, recharts)
- Tabela de títulos (conta corrente)
- Lista de cross-sell recomendados
- Score visual (gauge/medidor)
- Cards de verba mostram "Aguardando dados SAP" quando null

### Migração

**Quando tiver dados de verba:**
```sql
CREATE TABLE verbas_clientes (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) REFERENCES clientes(cnpj),
    tipo VARCHAR(20) NOT NULL,  -- CONQUISTA, GERADA, PAGA
    valor FLOAT NOT NULL,
    data_referencia DATE NOT NULL,
    pedido_origem VARCHAR(50),
    fonte VARCHAR(20) DEFAULT 'SAP',
    classificacao_3tier VARCHAR(15) DEFAULT 'REAL',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_tipo CHECK (tipo IN ('CONQUISTA', 'GERADA', 'PAGA'))
);
```

---

## 7. FASES DE IMPLEMENTAÇÃO

### Fase A — AGORA (com dados existentes)
- [x] Sell-in completo (vendas, metas, tendência)
- [x] Conta corrente completa (debitos_clientes)
- [x] Pagamentos recebidos (debitos WHERE PAGO)
- [x] Mix de produtos (venda_itens + produtos)
- [x] Sell-out parcial (penetração, SKUs dormentes)
- [x] Score geral (6 componentes disponíveis)
- [x] Plano de ação v1 (regras IF/THEN)

**Esforço estimado:** 2-3 horas de implementação (1 router + 1 componente React)

### Fase B — COM SAP/SALES HUNTER (próximas extrações)
- [ ] Verba conquista (bonificação)
- [ ] Verba gerada (se diferente de comissão)
- [ ] Verba devida (saldo)
- [ ] Custo do produto (margem real)
- [ ] Custo de frete por cliente

**Dependência:** Confirmar quais relatórios SAP/Sales Hunter contêm dados de verba

### Fase C — COM BI (integração futura)
- [ ] Sell-out real (dados POS do cliente)
- [ ] Giro de estoque
- [ ] Ruptura de SKUs
- [ ] Sell-through rate
- [ ] Plano de ação v2 (LLM)

---

## 8. RESUMO DE DISPONIBILIDADE

| Dimensão | Hoje | SAP/SH | BI | Fase |
|----------|------|--------|-----|------|
| **1. Sell-in** | ✅ 100% | — | — | A |
| **2. Sell-out** | ⚠️ 30% (proxy) | — | 🔜 100% | A+C |
| **3. Verba conquista** | ❌ 0% | 🔜 100% | — | B |
| **4. Verba gerada** | ⚠️ 50% (comissão?) | 🔜 100% | — | A+B |
| **5. Verba devida** | ❌ 0% | 🔜 100% | — | B |
| **6. Conta corrente** | ✅ 100% | — | — | A |
| **7. Pagamentos** | ✅ 100% | — | — | A |
| **Mix produtos** | ✅ 95% (sem custo) | 🔜 custo | — | A+B |
| **Score geral** | ✅ 85% | 🔜 100% | — | A |

**Conclusão:** 5 de 7 dimensões implementáveis HOJE. As 2 restantes (verbas) dependem de SAP. Sell-out real depende de BI.

---

## 9. REGRAS INVIOLÁVEIS APLICÁVEIS

- **R4 Two-Base:** Todos valores monetários são VENDA-side. Score e penetração são SINTÉTICOS (derivados).
- **R5 CNPJ:** Todos endpoints usam CNPJ normalizado (14 dígitos, string).
- **R8 Zero fabricação:** Dimensões sem dados retornam `null`, NUNCA valores inventados.
- **R9 Visual LIGHT:** Cards em fundo branco, cores de status conforme padrão (verde/amarelo/vermelho).
- **Canal scoping:** Vendedor só vê análise de clientes do seu canal.

---

## 10. DECISÕES L3 NECESSÁRIAS

| # | Decisão | Opções |
|---|---------|--------|
| 1 | Criar tabela `verbas_clientes` | A) Criar agora (schema pronto, dados depois) B) Esperar ter dados SAP |
| 2 | `produtos.comissao_pct` é comissão vendedor ou rebate cliente? | Confirmar com Leandro |
| 3 | Implementar Fase A agora ou esperar SAP completo? | A) Agora (5/7 dimensões) B) Esperar tudo |

---

*Spec baseada em dados REAIS do banco. Nenhum valor inventado. Fontes mapeadas: DB existente, SAP futuro, BI futuro.*
