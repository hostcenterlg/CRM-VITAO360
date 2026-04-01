# SPEC: Dashboards e Relatórios Mercos → CRM VITAO360 SaaS

> Mapeamento completo de TUDO que o Mercos oferece em Indicadores + Relatórios.
> Objetivo: replicar no nosso SaaS (Vercel + Supabase) com melhorias de IA.
> Data: 2026-04-01 | Fonte: app.mercos.com/399424/indicadores/
> Atualizado com captura COMPLETA do catálogo de indicadores + painel ativo + relatórios.

---

## 1. FILTROS GLOBAIS (top bar — presente em TODOS os indicadores)

| Filtro | Tipo | Valores |
|--------|------|---------|
| Mês | dropdown | Janeiro a Dezembro |
| Ano | dropdown | 2024, 2025, 2026... |
| Vendedor | dropdown | Todos os vendedores / Larissa Padilha / Manu Ditzel / Central-Daiane / Julio Gadret |

**No SaaS**: Manter os 3 filtros + adicionar: UF, Segmento, Curva ABC, Status do Cliente.

---

## 2. CATÁLOGO COMPLETO DE INDICADORES (27 disponíveis no Mercos)

### Categorias Mercos
- **Aquisição**: foco em conquistar novos clientes
- **Fidelização**: foco em manter clientes ativos comprando
- **Expansão**: foco em aumentar ticket e mix por cliente

### 2.1 VENDAS (7 indicadores)

| # | Indicador | Categorias | Tipo de Gráfico | Descrição |
|---|-----------|-----------|-----------------|-----------|
| 1 | **Evolução de venda** | Expansão | Line chart cumulativo | Vendas acumuladas dia a dia vs objetivo, previsão, mês/ano anterior |
| 2 | Quantidade ou valor vendido de um produto ou categoria | Expansão | Gauge + bar | Performance de vendas por produto/categoria |
| 3 | Valor diário em vendas de produtos | Expansão | Bar chart diário | Valor ou quantidade de categoria/produto por dia |
| 4 | Valor vendido em produtos comparado por vendedor | Expansão | Bar chart comparativo | Compara por vendedor o valor/quantidade vendida no mês |
| 5 | Quantidade vendida em produtos comparado por categoria | Expansão | Bar chart comparativo | Compara por categoria o valor/quantidade vendida no mês |
| 6 | Evolução das vendas de um produto ou categoria | Expansão | Line chart tendência | Vendido de produtos/categorias + previsão, comparando meses/ano anterior |
| 7 | Evolução de vendas (Antigo) | Expansão | Line chart tendência | Quanto já foi vendido + previsão, comparando meses/ano anterior |

### 2.2 POSITIVAÇÃO (9 indicadores)

| # | Indicador | Categorias | Tipo de Gráfico | Descrição |
|---|-----------|-----------|-----------------|-----------|
| 8 | **Positivação de clientes específica** | Aquisição, Fidelização | Gauge (speedometer) | % clientes positivados vs objetivo mensal por vendedor/plataforma/situação |
| 9 | **Positivação de clientes diária** | Aquisição, Fidelização | Bar chart diário | Número de clientes que fizeram pedidos por dia |
| 10 | Positivação de novos clientes comparada por vendedor | Aquisição | Bar chart comparativo | Novos clientes ativos que fizeram pedidos por vendedor |
| 11 | **Positivação de clientes ativos comparada por vendedor** | Fidelização | Bar chart comparativo | Clientes ativos que fizeram pedidos por vendedor |
| 12 | Positivação de clientes da categoria ou produto específico | Expansão | Gauge | Quantidade de clientes positivados em categoria/produto |
| 13 | Positivação de uma categoria ou produto diária | Expansão | Bar chart diário | Quantos clientes compraram categoria/produto por dia |
| 14 | Positivação de clientes da categoria ou produto por vendedor | Expansão | Bar chart comparativo | Clientes positivados que compraram categoria/produto por vendedor |
| 15 | Positivação de clientes por categoria de produto | Expansão | Bar chart comparativo | Número de clientes positivados por categoria de produto |
| 16 | **Positivação de clientes geral** | Aquisição, Fidelização | Donut + legenda | Número de clientes que fizeram pedidos e situação antes da positivação |

### 2.3 FATURAMENTO (5 indicadores)

| # | Indicador | Categorias | Tipo de Gráfico | Descrição |
|---|-----------|-----------|-----------------|-----------|
| 17 | Faturamento específico | Expansão | Gauge | Faturamento da empresa ou tipo de pedido específico |
| 18 | Faturamento diário | Expansão | Bar chart diário | Valor faturado por dia do mês |
| 19 | Faturamento total | Expansão | KPI card + tendência | Faturamento da empresa comparado com o ano anterior |
| 20 | Faturamento comparado por vendedor | Expansão | Bar chart comparativo | Valor faturado por vendedor no mês |
| 21 | Evolução do faturamento | Expansão | Line chart tendência | Quanto já foi faturado + previsão, comparando com meses/ano anterior |

### 2.4 ATIVIDADES (3 indicadores)

| # | Indicador | Categorias | Tipo de Gráfico | Descrição |
|---|-----------|-----------|-----------------|-----------|
| 22 | Volume de atividades | Aquisição, Fidelização, Expansão | Gauge + bar | Atividades realizadas (ligações, visitas, etc.) |
| 23 | Volume de atividades por vendedor | Aquisição, Fidelização, Expansão | Bar chart comparativo | Atividades realizadas por vendedor no mês |
| 24 | Volume de atividades diário | Aquisição, Fidelização, Expansão | Bar chart diário | Volume de atividades por dia do mês |

### 2.5 OUTROS (3 indicadores)

| # | Indicador | Categorias | Tipo de Gráfico | Descrição |
|---|-----------|-----------|-----------------|-----------|
| 25 | **Situação de carteira** | Aquisição, Fidelização | Donut (pizza) | Proporção de clientes ativos, inativos recentes, inativos antigos, prospects |
| 26 | **Curva ABC de clientes** | Fidelização | Donut (pizza) | Concentração de vendas por curvas A, B, C |
| 27 | **Conversão do E-commerce** | Fidelização, Aquisição | Bar chart agrupado | Conversão das visitas recebidas no e-commerce em pedidos |

**Negrito** = atualmente ATIVO no painel da Vitão.

---

## 3. PAINEL ATIVO — Widgets configurados (Março 2026)

O painel da Vitão tem 8 widgets ativos (widgetsIds: 52433, 52435, 56465, 56467, 56468 + sub-widgets):

### 3.1 EVOLUÇÃO DE VENDA
- **Tipo**: Line chart cumulativo (Highcharts)
- **Eixo X**: Dias do mês (1-31) com dia da semana
- **Séries**: Vendas no mês (verde), Objetivo (cinza), Previsão de vendas (pontilhado), Mês passado (cinza claro), Ano passado (cinza claro)
- **KPIs laterais**: Vendido no mês, Hoje, Objetivo do mês, % atingido, Necessário vender por dia útil
- **Link**: Detalhar por vendedor → /indicadores/ranking-de-vendedores/
- **DADOS REAIS Mar/2026**: R$ 171.623,94 | Hoje: R$ 13.147,84 | Meta: R$ 0 (não definida)

### 3.2 CARTEIRA DE CLIENTES
- **Tipo**: Donut chart + legenda com números absolutos
- **Segmentos**: Ativos (verde), Inativos recentes (amarelo), Inativos antigos (vermelho), Prospects (cinza)
- **Link**: Detalhar carteira
- **DADOS REAIS Mar/2026**: 553 clientes = 150 ativos (27,12%) + 49 inativos recentes (8,86%) + 354 inativos antigos (64,01%) | 5.876 prospects

### 3.3 POSITIVAÇÃO GERAL
- **Tipo**: Summary cards com contadores coloridos
- **Métricas**: % positivados, Novos (roxo), Ativos (verde), Inativos recentes (amarelo), Inativos antigos (vermelho)
- **Link**: Detalhar positivação
- **DADOS REAIS Mar/2026**: 15,94% positivados | 37 novos, 22 ativos, 1 inativo recente, 26 inativos antigos

### 3.4 CURVA ABC DE CLIENTES
- **Tipo**: Summary cards com cores por curva
- **Segmentos**: Curva A (verde escuro), Curva B (roxo), Curva C (rosa claro)
- **Link**: Detalhar curva ABC
- **DADOS REAIS Mar/2026**: 210 clientes Curva A + 193 Curva B + 145 Curva C = 548 classificados

### 3.5 CONVERSÃO DO E-COMMERCE
- **Tipo**: Bar chart agrupado por mês
- **Métricas**: Clientes que acessaram, Adicionaram ao carrinho, Finalizaram e-commerce
- **DADOS REAIS Mar/2026**: (gráfico de barras com 3 grupos)

### 3.6 POSITIVAÇÃO DE CLIENTES DIÁRIA
- **Tipo**: Bar chart diário (dia 1-31)
- **Métricas**: Clientes positivados (verde) vs Objetivo do dia (cinza)
- **DADOS REAIS Mar/2026**: ~2-5 clientes positivados por dia

### 3.7 POSITIVAÇÃO DE CLIENTES ESPECÍFICA
- **Tipo**: Gauge (speedometer) com ponteiro
- **Métricas**: Clientes positivados vs objetivo mensal (escala 0 a N)
- **DADOS REAIS Mar/2026**: 86 clientes positivados de 310 = 27,74% do objetivo

### 3.8 POSITIVAÇÃO DE CLIENTES ATIVOS COMPARADA POR VENDEDOR
- **Tipo**: Bar chart comparativo por vendedor
- **Vendedores**: Larissa Padilha, Manu Ditzel, Central - Daiane, Julio Gadret
- **Métricas**: Clientes positivados (verde) vs Objetivo do mês (cinza) por vendedor

---

## 4. ABA RELATÓRIOS — Lista Completa (23 relatórios)

### 4.1 VENDAS (5 relatórios)
| # | Relatório | URL | Descrição |
|---|-----------|-----|-----------|
| 1 | **Resumo de vendas** (NOVO) | /relatorios/comparativo-vendas/ | Visão consolidada de vendas com comparações |
| 2 | **Vendas detalhadas** (NOVO) | /relatorios/vendas/ | Detalhamento pedido a pedido |
| 3 | Ranking de vendedor / Meta | /indicadores/ranking-de-vendedores/ | Performance por vendedor vs meta |
| 4 | Relatório gerencial para representada | /relatorios/representada/ | Visão da representada (indústria) |
| 5 | Movimentações do Saldo Flex | /indicadores/movimentacao-saldo-flex/ | Saldo flex (crédito/débito) |

### 4.2 FATURAMENTO E TÍTULOS (3 relatórios)
| # | Relatório | URL | Descrição |
|---|-----------|-----|-----------|
| 6 | Pedidos faturados | /relatorios/pedidos_faturados/ | Pedidos que já foram faturados (NF emitida) |
| 7 | Faturamento | /relatorios/faturamento/ | Valor faturado por período |
| 8 | Títulos | /indicadores/titulos/ | Títulos a receber (duplicatas) |

### 4.3 CLIENTES (7 relatórios)
| # | Relatório | URL | Descrição |
|---|-----------|-----|-----------|
| 9 | Clientes | /relatorios/clientes/ | Lista completa de clientes com filtros |
| 10 | Situação da carteira de clientes | /indicadores/situacao-de-carteira/ | Ativos, inativos recentes, inativos antigos |
| 11 | Positivação de clientes | /indicadores/positivacao-de-clientes/ | % clientes que compraram no período |
| 12 | Curva ABC de clientes | /indicadores/curva-abc/ | Classificação A/B/C por faturamento |
| 13 | Acessos e atividades do E-commerce | /relatorios/metricas_b2b/ | Métricas do portal B2B |
| 14 | Visitas com check-in | /indicadores/visitas/ | Visitas presenciais registradas com GPS |
| 15 | Relatório de tarefas realizadas | /indicadores/atendimentos/ | Atividades comerciais realizadas |

### 4.4 COMISSÕES (2 relatórios)
| # | Relatório | URL | Descrição |
|---|-----------|-----|-----------|
| 16 | Relatório de comissões | /comissoes/ | Comissões acumuladas por vendedor |
| 17 | Comissões por pedido | /relatorios/comissoes_pedido/ | Comissão detalhada por pedido |

### 4.5 PRODUTOS (4 relatórios)
| # | Relatório | URL | Descrição |
|---|-----------|-----|-----------|
| 18 | Produtos mais vendidos | /indicadores/produtos-mais-vendidos/ | Ranking de produtos por valor/quantidade |
| 19 | Positivação de produtos por cliente | — | Quais clientes compraram quais produtos |
| 20 | Produtos por pedido | — | Mix de produtos por pedido |
| 21 | Estoque | — | Saldo de estoque atual |

### 4.6 OUTROS (2 relatórios)
| # | Relatório | URL | Descrição |
|---|-----------|-----|-----------|
| 22 | E-mails enviados | /relatorios/emails_enviados/ | Histórico de e-mails disparados pelo sistema |
| 23 | Extrato das videochamadas | — | Histórico de videochamadas realizadas |

---

## 5. DADOS REAIS — Março 2026

| Métrica | Valor | Fonte |
|---------|-------|-------|
| Vendido no mês | R$ 171.623,94 | Painel Mercos (31/Mar/2026) |
| Vendido hoje | R$ 13.147,84 | Painel Mercos |
| Carteira total | 553 clientes | Painel Mercos |
| Clientes ativos | 150 (27,12%) | Painel Mercos |
| Inativos recentes | 49 (8,86%) | Painel Mercos |
| Inativos antigos | 354 (64,01%) | Painel Mercos |
| Prospects | 5.876 | Painel Mercos |
| Positivação | 15,94% (86 de 310) | Painel Mercos |
| Curva A | 210 clientes | Painel Mercos |
| Curva B | 193 clientes | Painel Mercos |
| Curva C | 145 clientes | Painel Mercos |
| Clientes extraídos (API) | 6.429 | mercos_clientes_completo.json |
| CNPJs únicos | 6.197 | Análise pós-extração |

### Metadados da Conta Mercos
- **ID Empresa**: 399424
- **Plano**: Ouro (Indústria)
- **Representada ID**: 659182
- **Domínio B2B**: vitaomais.meuspedidos.com.br
- **Usuários**: 5 (Leandro Garcia admin)
- **Widgets IDs ativos**: 52433, 52435, 56465, 56467, 56468

---

## 6. PLANO DE IMPLEMENTAÇÃO NO SAAS (Vercel + Supabase)

### Fase 1 — MVP Dashboard (Prioridade ALTA)
Replicar os 8 widgets ATIVOS do painel:
1. Evolução de Venda (line chart)
2. Carteira de Clientes (donut)
3. Positivação Geral (summary cards)
4. Curva ABC (summary cards)
5. Conversão E-commerce (bar chart)
6. Positivação Diária (bar chart)
7. Positivação Específica (gauge)
8. Positivação por Vendedor (bar chart comparativo)

**Filtros**: Mês, Ano, Vendedor + UF, Segmento (extras da nossa SaaS)
**Lib gráficos**: Recharts (React-native) ou Chart.js
**Dados**: Supabase views/functions alimentadas por mercos_clientes_completo.json + vendas (quando extraídas)

### Fase 2 — Relatórios Tabulares
Replicar os 23 relatórios como tabelas filtráveis:
- Vendas detalhadas (DataGrid com export)
- Ranking vendedor/Meta
- Positivação de clientes
- Curva ABC detalhada
- Produtos mais vendidos
- Comissões

### Fase 3 — Indicadores Avançados + IA
Adicionar os 19 indicadores NÃO ativos do catálogo Mercos:
- Faturamento (5 widgets)
- Atividades (3 widgets)
- Vendas por produto/categoria (5 widgets extras)
- Positivação por produto/categoria (4 widgets extras)
- Conversão E-commerce (já ativo)
- Carteira (já ativo)

**Plus IA exclusivos do nosso SaaS**:
- Previsão de churn (cliente vai parar de comprar)
- Sugestão de mix por cliente (recomendação de produtos)
- Score de temperatura (quente/morno/frio)
- Alerta de oportunidade (cliente comprando menos que potencial)
- Semáforo de saúde comercial (verde/amarelo/vermelho)

### Fase 4 — Licitações + Foodservice
- Tab Licitações: integração PNCP API (spec em ESTRUTURA_LICITACOES_FOODSERVICE.md)
- Tab Foodservice: pipeline PROSPECT → ATIVO (spec em ESTRUTURA_LICITACOES_FOODSERVICE.md)

---

## 7. TABELAS SUPABASE NECESSÁRIAS

```sql
-- Clientes (alimentado por mercos_clientes_completo.json)
CREATE TABLE mercos_clientes (
    id BIGINT PRIMARY KEY,
    razao_social TEXT,
    nome_fantasia TEXT,
    cnpj VARCHAR(18),
    cnpj_normalizado VARCHAR(14) GENERATED ALWAYS AS (
        LPAD(REGEXP_REPLACE(cnpj, '[^0-9]', '', 'g'), 14, '0')
    ) STORED,
    inscricao_estadual TEXT,
    endereco TEXT,
    bairro TEXT,
    cidade TEXT,
    estado VARCHAR(2),
    cep VARCHAR(9),
    segmento_nome TEXT,
    rede_nome TEXT,
    data_cadastro TIMESTAMPTZ,
    origem TEXT,
    bloqueado BOOLEAN DEFAULT FALSE,
    emails TEXT[],
    telefones TEXT[],
    colaboradores TEXT[],
    tags TEXT[],
    -- Campos calculados no SaaS
    curva_abc VARCHAR(1),
    status_carteira VARCHAR(20), -- ATIVO, INATIVO_RECENTE, INATIVO_ANTIGO, PROSPECT
    temperatura VARCHAR(10), -- QUENTE, MORNO, FRIO
    ultimo_pedido DATE,
    faturamento_12m DECIMAL(15,2),
    ticket_medio DECIMAL(15,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendas (será alimentado por extração Mercos vendas detalhadas)
CREATE TABLE mercos_vendas (
    id BIGSERIAL PRIMARY KEY,
    pedido_id BIGINT,
    cliente_id BIGINT REFERENCES mercos_clientes(id),
    cnpj_normalizado VARCHAR(14),
    vendedor TEXT,
    vendedor_normalizado VARCHAR(20), -- MANU, LARISSA, DAIANE, JULIO, LEGADO
    data_pedido DATE,
    data_faturamento DATE,
    valor_pedido DECIMAL(15,2),
    valor_faturado DECIMAL(15,2),
    status_pedido TEXT,
    itens JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indicadores diários (cache para dashboards)
CREATE TABLE indicadores_diarios (
    id BIGSERIAL PRIMARY KEY,
    data DATE NOT NULL,
    vendedor TEXT,
    vendas_valor DECIMAL(15,2) DEFAULT 0,
    vendas_quantidade INTEGER DEFAULT 0,
    clientes_positivados INTEGER DEFAULT 0,
    faturamento DECIMAL(15,2) DEFAULT 0,
    atividades INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(data, vendedor)
);

-- Índices
CREATE INDEX idx_clientes_cnpj ON mercos_clientes(cnpj_normalizado);
CREATE INDEX idx_clientes_estado ON mercos_clientes(estado);
CREATE INDEX idx_clientes_status ON mercos_clientes(status_carteira);
CREATE INDEX idx_vendas_data ON mercos_vendas(data_pedido);
CREATE INDEX idx_vendas_vendedor ON mercos_vendas(vendedor_normalizado);
CREATE INDEX idx_vendas_cliente ON mercos_vendas(cliente_id);
CREATE INDEX idx_indicadores_data ON indicadores_diarios(data);
```

---

## 8. SIDEBAR NAVIGATION (SaaS)

```
INDICADORES
├── Dashboard (= Painel Mercos com 8+ widgets)
├── Vendas
│   ├── Evolução de Venda
│   ├── Vendas Detalhadas
│   ├── Ranking Vendedor/Meta
│   └── Vendas por Produto/Categoria
├── Clientes
│   ├── Carteira (Situação)
│   ├── Positivação
│   ├── Curva ABC
│   └── E-commerce (Conversão)
├── Faturamento
│   ├── Evolução
│   ├── Pedidos Faturados
│   └── Títulos
├── Atividades
│   ├── Volume
│   ├── Por Vendedor
│   └── Diário
├── Comissões
│   ├── Por Vendedor
│   └── Por Pedido
├── Produtos
│   ├── Mais Vendidos
│   ├── Mix por Cliente
│   └── Estoque
├── [NOVO] Licitações
│   ├── Pipeline
│   ├── Radar PNCP
│   └── Histórico
├── [NOVO] Foodservice
│   ├── Pipeline
│   ├── Prospects
│   └── Histórico
└── [NOVO] Inteligência IA
    ├── Previsão de Churn
    ├── Score de Temperatura
    ├── Recomendação de Mix
    └── Alertas
```

---

## 9. PENDÊNCIAS

- [ ] Extrair Mercos VENDAS DETALHADAS (endpoint: /api-online/indicadores/vendas/)
- [ ] Extrair dados de FATURAMENTO do Mercos
- [ ] Importar mercos_clientes_completo.json para Supabase
- [ ] Calcular curva ABC e status carteira no Supabase
- [ ] Criar views SQL para cada widget do dashboard
- [ ] Implementar DE-PARA vendedores no Supabase
- [ ] Aguardar dashboards adicionais do Leandro ("além dos que vou te mandar depois")
- [ ] Integrar SAP (Sales Hunter) para faturamento real
- [ ] PNCP API para Licitações (spec pronta)

---

*Classificação 3-tier: TODOS os dados nesta spec são REAL (fonte: Mercos API direta, captura visual de tela).*
*Nenhum dado fabricado. Zero alucinação.*
