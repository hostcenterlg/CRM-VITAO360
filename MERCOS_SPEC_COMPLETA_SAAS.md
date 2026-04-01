# ESPECIFICAÇÃO COMPLETA — MERCOS → SaaS CRM VITAO360

> **Data:** 2026-04-01
> **Fonte:** Mapeamento direto do app.mercos.com/399424 (conta VITAO MAIS)
> **Objetivo:** Replicar TODOS os filtros, dashboards, indicadores e funcionalidades do Mercos no nosso SaaS

---

## 1. NAVEGAÇÃO PRINCIPAL (Sidebar)

| # | Seção | URL Pattern |
|---|-------|-------------|
| 1 | INDICADORES | `/indicadores/` |
| 2 | PEDIDOS | `/pedidos/` |
| 3 | CLIENTES | `/clientes/` |
| 4 | PRODUTOS | `/produtos/` |
| 5 | E-COMMERCE | `/configuracoes-portal-e-ecommerce/` |
| 6 | TAREFAS | `/agenda/` |
| 7 | MINHA CONTA | (configurações gerais) |

---

## 2. INDICADORES — PAINEL

### 2.1 Filtros Globais do Painel

| Filtro | Tipo | Valores |
|--------|------|---------|
| Mês | Dropdown | Janeiro...Dezembro |
| Ano | Dropdown | 2024, 2025, 2026... |
| Vendedor | Dropdown | "Todos os vendedores", Larissa Padilha, Manu Ditzel, Central - Daiane, Julio Gadret |

### 2.2 Indicadores Ativos no Painel (já configurados)

| # | Indicador | Tipo Gráfico | Período | Métricas |
|---|-----------|-------------|---------|----------|
| 1 | Evolução de Venda | Linha (multi-série) | Mês selecionado | Vendas do mês, previsão, mês passado, ano passado |
| 2 | Carteira de Clientes | Donut | Mês selecionado | Ativos, Inativos recentes, Inativos antigos, Prospects |
| 3 | Positivação | Donut + Gauge | Mês selecionado | Clientes positivados vs objetivo mensal |
| 4 | Curva ABC de Clientes | Donut | Últimos 12 meses | Curva A, B, C (qtd clientes) |
| 5 | E-commerce B2B | Barras | Mês selecionado | (conversão/atividades) |
| 6 | Positivação de Clientes Diária | Barras + Linha | Mês selecionado | Positivados por dia vs objetivo diário |
| 7 | Volume de Atendimentos Diário | Linha (multi-série) | Mês selecionado | Atividades realizadas, objetivo do dia, previsão do dia, mês passado, ano passado |
| 8 | Volume de Atendimentos | Gauge | Mês selecionado | Total atividades vs objetivo mensal + esperados até hoje |
| 9 | Positivação de Clientes Específica | Donut | Mês selecionado | Por vendedor/plataforma/situação |
| 10 | Positivação de Clientes Ativos Comparada por Vendedor | Barras | Mês selecionado | Barras por vendedor: positivados vs objetivo |

### 2.3 TODOS os Indicadores Disponíveis (Catálogo Completo)

#### Categorias de Estratégia:
- **Aquisição** — indicadores de novos clientes
- **Fidelização** — indicadores de retenção
- **Expansão** — indicadores de crescimento de vendas

#### VENDAS (8 indicadores)

| # | Nome | Categorias | Tipo Gráfico | Descrição |
|---|------|-----------|-------------|-----------|
| 1 | Quantidade ou valor vendido de um produto ou categoria | Expansão | Gauge + barras | Performance de vendas por produto/categoria |
| 2 | Valor diário em vendas de produtos | Expansão | Barras diárias | Valor ou quantidade de produto/categoria por dia |
| 3 | Valor vendido em produtos comparado por vendedor | Expansão | Barras agrupadas | Comparação vendedores por valor de produto |
| 4 | Quantidade vendida em produtos comparado por categoria | Expansão | Barras agrupadas | Comparação categorias por quantidade |
| 5 | Evolução das vendas de um produto ou categoria | Expansão | Linha (multi-série) | Vendido + previsão vs meses anteriores |
| 6 | Evolução de vendas | Expansão | Linha (multi-série) | Vendido + previsão vs ano e meses anteriores |
| 7 | (Valor vendido comparado por vendedor — variante) | Expansão | Barras | Compare por vendedor o valor vendido no mês |
| 8 | (Quantidade vendida comparado por categoria — variante) | Expansão | Barras | Compare por categoria o valor/quantidade vendida |

#### POSITIVAÇÃO (10 indicadores)

| # | Nome | Categorias | Tipo Gráfico | Descrição |
|---|------|-----------|-------------|-----------|
| 1 | Positivação de clientes específica | Aquisição + Fidelização | Gauge + donut | Clientes que fizeram pedidos por vendedor/plataforma/situação |
| 2 | Positivação de clientes diária | Aquisição + Fidelização | Barras diárias | Nº clientes que fizeram pedidos cada dia |
| 3 | Positivação de novos clientes comparada por vendedor | Aquisição | Barras agrupadas | Novos clientes ativos por vendedor |
| 4 | Positivação de clientes ativos comparada por vendedor | Fidelização | Barras agrupadas | Clientes ativos que compraram por vendedor |
| 5 | Positivação de clientes da categoria ou produto específico | Expansão | Gauge + donut | Qtd clientes positivados em categoria/produto |
| 6 | Positivação de uma categoria ou produto diária | Expansão | Barras diárias | Clientes que compraram categoria/produto por dia |
| 7 | Positivação de clientes da categoria ou produto por vendedor | Expansão | Barras agrupadas | Positivados em categoria/produto por vendedor |
| 8 | Positivação de clientes por categoria de produto | Expansão | Barras agrupadas | Nº clientes positivados por categoria |
| 9 | Positivação de clientes geral | Aquisição + Fidelização | Donut | Visão geral: novos, ativos, inativos recentes/antigos |
| 10 | (Positivação gauge no painel) | Aquisição + Fidelização | Gauge | Clientes positivados vs objetivo mensal |

#### FATURAMENTO (5 indicadores)

| # | Nome | Categorias | Tipo Gráfico | Descrição |
|---|------|-----------|-------------|-----------|
| 1 | Faturamento específico | Expansão | Gauge + donut | Faturamento da empresa ou tipo de pedido |
| 2 | Faturamento diário | Expansão | Barras diárias | Valor faturado em cada dia do mês |
| 3 | Faturamento total | Expansão | KPI card | Faturamento comparado com ano anterior |
| 4 | Faturamento comparado por vendedor | Expansão | Barras agrupadas | Valor faturado por vendedor |
| 5 | Evolução do faturamento | Expansão | Linha (multi-série) | Faturado + previsão vs ano e meses anteriores |

#### ATIVIDADES (3 indicadores)

| # | Nome | Categorias | Tipo Gráfico | Descrição |
|---|------|-----------|-------------|-----------|
| 1 | Volume de atividades | Aquisição + Fidelização + Expansão | Gauge | Atividades realizadas vs objetivo |
| 2 | Volume de atividades por vendedor | Aquisição + Fidelização + Expansão | Barras agrupadas | Atividades realizadas por vendedor |
| 3 | Volume de atividades diário | Aquisição + Fidelização + Expansão | Barras diárias | Volume de atividades em cada dia do mês |

#### OUTROS (3 indicadores)

| # | Nome | Categorias | Tipo Gráfico | Descrição |
|---|------|-----------|-------------|-----------|
| 1 | Situação de carteira | Aquisição + Fidelização | Donut | Proporção ativos, inativos recentes, inativos antigos, prospects |
| 2 | Curva ABC de clientes | Fidelização | Donut | Concentração das vendas por curvas A, B, C |
| 3 | Conversão do E-commerce | Fidelização + Aquisição | Barras agrupadas | Conversão de visitas em pedidos no e-commerce |

**TOTAL: 29 indicadores disponíveis**

---

## 3. INDICADORES — RELATÓRIOS

### 3.1 Relatórios de VENDAS

| # | Relatório | Tag |
|---|-----------|-----|
| 1 | Resumo de vendas | NOVO |
| 2 | Vendas detalhadas | NOVO |
| 3 | Ranking de vendedor / Meta | — |
| 4 | Relatório gerencial para representada | — |
| 5 | Movimentações do Saldo Flex | — |

### 3.2 Relatórios de FATURAMENTO E TÍTULOS

| # | Relatório |
|---|-----------|
| 1 | Pedidos faturados |
| 2 | Faturamento |
| 3 | Títulos |

### 3.3 Relatórios de CLIENTES

| # | Relatório |
|---|-----------|
| 1 | Clientes |
| 2 | Situação da carteira de clientes |
| 3 | Positivação de clientes |
| 4 | Curva ABC de clientes |
| 5 | Acessos e atividades do E-commerce |
| 6 | Visitas com check-in |
| 7 | Relatório de tarefas realizadas |

### 3.4 Relatórios de COMISSÕES

| # | Relatório |
|---|-----------|
| 1 | Relatório de comissões |
| 2 | Comissões por pedido |

### 3.5 Relatórios de PRODUTOS

| # | Relatório |
|---|-----------|
| 1 | Produtos mais vendidos |
| 2 | Positivação de produtos por cliente |
| 3 | Produtos por pedido |

### 3.6 Relatórios OUTROS

| # | Relatório |
|---|-----------|
| 1 | E-mails enviados |
| 2 | Extrato das videochamadas |

**TOTAL: 19 relatórios disponíveis**

---

## 4. POSITIVAÇÃO DE CLIENTES (Relatório Detalhado)

### 4.1 Abas
- **PAINEL** — gráficos visuais
- **RELATÓRIOS** — dados tabulares

### 4.2 Filtros do Relatório

| Filtro | Tipo |
|--------|------|
| Período (data inicial / data final) | Date range |
| Representada | Dropdown |
| Vendedor | Multi-select |
| Situação (Novos, Ativos, Inativos recentes, Inativos antigos) | Checkboxes |

### 4.3 Configurações
- "Configurar período de inatividade" — define quando cliente vira inativo
- Toggle donut chart / line chart

### 4.4 Visualizações
- **Donut chart:** 86 Clientes positivados (exemplo Mar/2026), segmentado por: Novos (43.02%), Ativos (25.58%), Inativos recentes (1.16%), Inativos antigos (30.23%)
- **KPI:** "15.94% dos clientes ativos foram positivados neste mês"
- **Legenda:** 37 novos, 22 ativos, 1 inativos recentes, 26 inativos antigos

### 4.5 Tabela de Clientes

Colunas disponíveis (todas configuráveis):

| Coluna | Padrão? |
|--------|---------|
| Razão social | ✅ |
| Nome fantasia | ☐ |
| CNPJ/CPF | ☐ |
| Inscrição Estadual | ☐ |
| E-mail | ☐ |
| Telefone | ☐ |
| Cidade | ☐ |
| Último pedido (nº) | ✅ |
| Data do último pedido | ✅ |
| Data do penúltimo pedido | ✅ |
| Diferença (em dias) | ✅ |
| Vendedor do último pedido | ☐ |
| Situação | ✅ |
| Tags de cliente | ☐ |

### 4.6 Exportação
- Botão **Excel** para exportar tabela

---

## 5. PEDIDOS

### 5.1 Abas
- **PEDIDOS** — lista de pedidos
- **CONFIGURAÇÕES** — configurações do módulo

### 5.2 Ações
- **+ Criar pedido / orçamento**
- **Criar carrinho**
- **Imprimir pedidos**

### 5.3 Busca
- "Pedido, cliente ou representada"
- "Pesquise por nota fiscal, data de emissão, etc."

### 5.4 Filtros Inline

| Filtro | Tipo | Opções |
|--------|------|--------|
| Tipo de pedido | Dropdown | Pedidos ativos, Todos, Orçamentos... |
| Vendedor | Dropdown | Todos os vendedores, [lista vendedores] |
| Plataforma | Dropdown | Todas as plataformas, App, E-commerce, Web |
| Envio | Dropdown | Sem considerar o envio, Enviados, Não enviados |
| Status | Dropdown | Qualquer status, Em orçamento, Concluído, Faturado... |

### 5.5 Card de Pedido (dados exibidos)
- Número do pedido (#2195)
- Vendedor que emitiu
- Status badges: "Em orçamento", "e-commerce concluído", "Concluído"
- Razão social do cliente
- Nome fantasia
- Condição de pagamento (ex: "Boleto: Norte + Nordeste 35/42/49")
- Valor em R$
- Agrupamento temporal: HOJE / ONTEM / data

### 5.6 Configurações de Pedidos

| Sub-aba | Descrição |
|---------|-----------|
| Campos extras | Campos customizáveis adicionais no pedido |
| Status de pedido | Fluxo de status configurável |
| Tipo de pedido | Tipos configuráveis (Venda, Bonificação, etc.) |
| Geral | Configurações gerais do módulo |

---

## 6. CLIENTES

### 6.1 Abas
- **CLIENTES** — lista de clientes
- **CONFIGURAÇÕES** — configurações do módulo

### 6.2 Ações
- **+ Cadastrar cliente**
- **Importar** (importação em massa)
- **Vínculos e permissões**

### 6.3 Busca e Filtros

| Filtro | Tipo |
|--------|------|
| "Pesquise por nome ou CNPJ" | Text search |
| "Pesquise por cidade, estado, etc." | Text search avançado |
| Exibir | Dropdown: "clientes não bloqueados", "todos", "bloqueados" |

### 6.4 Sidebar — Carteira de Clientes (Widget)
- Donut chart com total de clientes (553)
- Segmentos: Ativos (150), Inativos recentes (49), Inativos antigos (354), Prospects (5876)
- Link "Detalhar carteira"

### 6.5 Card de Cliente (lista)
- Nome / Razão social
- CNPJ
- Nome fantasia
- Telefone
- E-mail
- Cidade
- Botões: Alterar / Excluir

### 6.6 Detalhe do Cliente (página completa)

#### Cabeçalho
- Nome completo
- Botões: Alterar, Vínculos e Permissões, Mais opções
- Telefone (com botão WhatsApp)
- E-mail (clicável)
- Endereço completo + CEP + Cidade/Estado + "Visualizar mapa"
- "Ver cadastro completo" (expande campos extras)

#### Sidebar — RESUMO (Últimos 6 meses)

| Métrica | Exemplo |
|---------|---------|
| Ranking "Cliente que mais compra" | 184º |
| Total em compras | R$ 1.231,07 |
| Pedidos realizados | 1 |
| Ticket médio | R$ 1.231,07 |
| Dias sem comprar | 65 |

#### TAREFAS (no detalhe do cliente)
- Criar tarefa
- Criar videochamada

#### E-COMMERCE (no detalhe do cliente)
- "Acessar como cliente" (simular visão)
- Toggle "E-commerce liberado"
- Gerenciar acessos
- Último acesso (data/hora)

#### LIMITE DE CRÉDITO
- Por representada (VITAO MAIS)
- Limite disponível / Limite total

#### TÍTULOS
- Abas: "A receber" | "Recebidos"
- + Adicionar título
- WhatsApp (para cobranças)

#### PEDIDOS E ATIVIDADES (Timeline)
- Ações: Criar pedido, Registrar atividade
- Timeline unificada com tipos:
  - **WhatsApp** — data/hora, responsável, descrição
  - **Ligação** — data/hora, responsável, descrição
  - **Pedido** — nº, data, vendedor, condição pgto, valor, status
  - **Visita** — data/hora, responsável, descrição + check-in

#### NOTAS FISCAIS
- Lista de notas fiscais vinculadas ao cliente

#### PRODUTOS MAIS COMPRADOS
- Ranking 1, 2, 3, 4... com nome do produto e código

---

## 7. PRODUTOS

### 7.1 Abas
- **PRODUTOS** — catálogo
- **PROMOÇÕES** — regras de promoção
- **DESTAQUES** — produtos em destaque
- **CONFIGURAÇÕES** — configurações do módulo

### 7.2 Sub-abas (Produtos)
- **Produtos e tabelas** — lista principal
- **Gerenciar estoque** — controle de estoque
- **Importar fotos** — upload em massa

### 7.3 Ações
- **+ Cadastrar produto**
- **Importar produtos** (importação em massa)
- **Mais opções** (dropdown)

### 7.4 Filtros

| Filtro | Tipo |
|--------|------|
| Categoria | Dropdown: "Todas as categorias" |
| Busca | "Pesquise por código ou nome" |
| Status | "Exibir produtos ativos ▼" |

### 7.5 Tabela de Produtos

Colunas:

| Coluna | Descrição |
|--------|-----------|
| Fotos | Thumbnail do produto |
| Código | Código SAP/interno (ex: 300000002) |
| Nome | Nome completo do produto |
| Variações | Variações do produto (se houver) |
| IPI | Imposto sobre Produtos Industrializados |
| Unidade | UN, CX, KG, etc. |
| Comissão | % comissão do vendedor |
| Preço Mínimo | Preço mínimo permitido |
| Preço de Tabela | Preço padrão |
| Preço por Estado | UMA COLUNA POR ESTADO (Acre, Alagoas, Amapá, Amazonas, Bahia, Brasília, Ceará, Espírito Santo, Goiás, Maranhão, Mato Grosso, ...) |

### 7.6 Nota sobre Preços Regionais
O Mercos permite definir preços diferentes por estado brasileiro. Isso é CRÍTICO para a Vitão que opera com tabelas regionais diferentes (Norte+Nordeste, Sudeste+Centro-Oeste, Sul).

---

## 8. E-COMMERCE B2B

### 8.1 URL
- `vitaomais.meuspedidos.com.br`

### 8.2 Abas
- **CONFIGURAÇÕES** — regras do e-commerce
- **PERSONALIZAÇÃO** — visual/branding

### 8.3 Sub-abas (Configurações)
- **E-commerce** — configurações gerais
- **Catálogo** — configurações do catálogo
- **Portal do cliente** — área logada do cliente

### 8.4 Configurações do E-commerce

#### ACESSO E VISIBILIDADE
| Config | Tipo | Opções |
|--------|------|--------|
| E-commerce ativo | Toggle | On/Off |
| Visibilidade | Radio | Público (aberto) / Privado (login obrigatório) |
| Aceitar apenas PJ | Checkbox | ✅ |
| Obrigar preenchimento endereço | Checkbox | ✅ |
| Cadastro automático como cliente | Checkbox | ☐ |
| Acesso imediato novos clientes | Checkbox | ☐ |

#### USUÁRIO RESPONSÁVEL
- Dropdown de vendedores (recebe email a cada orçamento do e-commerce)
- Atual: Central - Daiane

#### FINALIZAÇÃO DO PEDIDO - CHECKOUT
- Configurações de checkout

### 8.5 Features
- **Cupons de desconto** (novidade)
- **Relatório de atividades** (acessos, conversões)
- **"Acessar como cliente"** — simular visão do e-commerce como cliente específico

---

## 9. TAREFAS E ATIVIDADES

### 9.1 Abas
- **TAREFAS** — agenda de tarefas e atividades
- **ROTEIROS** — roteiros planejados de visitas

### 9.2 Ações
- **Criar tarefa**
- **Registrar atividade**
- **Exportar Excel**

### 9.3 Filtros de Tarefas

| Filtro | Tipo | Opções |
|--------|------|--------|
| Período | Date range | Data inicial — Data final + "Outro período" |
| Vendedor | Multi-select com tags | Leandro Garcia, Larissa Padilha, Manu Ditzel, etc. |
| Cliente | Dropdown | "Todos os clientes" ou busca |
| Meio de contato | Dropdown | "Todos os meios de contato" (WhatsApp, Ligação, E-mail, Visita...) |
| Status | Dropdown | "Não realizadas", "Realizadas", "Todas" |

### 9.4 Tipos de Atividade (meios de contato)
- WhatsApp
- Ligação
- E-mail
- Visita (com check-in/geolocalização)
- Videochamada

### 9.5 ROTEIROS PLANEJADOS

Tabela com colunas:

| Coluna | Descrição |
|--------|-----------|
| Roteiro | Nome do roteiro |
| Vendedor | Quem executa |
| Data | Data planejada |
| Repete | Recorrência |
| Dia da semana | Dia fixo |
| Qtde. de clientes | Número de clientes no roteiro |
| Situação | Status do roteiro |

---

## 10. FUNCIONALIDADES TRANSVERSAIS

### 10.1 Busca Rápida Global
- Campo "Busca rápida" no header
- Pesquisa em pedidos, clientes, produtos

### 10.2 WhatsApp Integration
- Botão WhatsApp no header do painel
- Botão WhatsApp no detalhe do cliente (telefone)
- Botão WhatsApp nos títulos (cobranças)
- Registro de atividade tipo WhatsApp

### 10.3 Exportações
- Excel em praticamente todas as tabelas/relatórios
- Impressão de pedidos

### 10.4 Configurações por Representada
- Filtro por representada (VITAO MAIS = ID 659182)
- Limite de crédito por representada
- Preços por representada

### 10.5 Vendedores (Equipe Comercial)
- Larissa Padilha
- Manu Ditzel
- Central - Daiane
- Julio Gadret
- Leandro Garcia (admin)

---

## 11. RESUMO PARA IMPLEMENTAÇÃO NO SAAS

### O que o SaaS DEVE ter (Paridade Mercos):

1. **Dashboard de Indicadores** — 29 indicadores configuráveis com 3 categorias (Aquisição/Fidelização/Expansão)
2. **19 Relatórios** em 6 categorias (Vendas, Faturamento, Clientes, Comissões, Produtos, Outros)
3. **Gestão de Pedidos** — CRUD completo com fluxo de status, campos extras, filtros avançados
4. **Gestão de Clientes** — Cadastro completo com timeline de atividades, resumo financeiro, positivação
5. **Catálogo de Produtos** — Com preços regionais por estado, promoções, destaques
6. **E-commerce B2B** — Portal do cliente com acesso configurável
7. **Tarefas e Atividades** — Agenda com filtros, tipos de contato, roteiros planejados
8. **Positivação** — Motor de cálculo: Novos, Ativos, Inativos recentes, Inativos antigos
9. **Curva ABC** — Classificação automática A/B/C por faturamento
10. **Integração WhatsApp** — Em todas as telas relevantes

### O que o SaaS DEVE ter A MAIS (valor agregado):

> (Aguardando lista adicional do Leandro)

---

*Documento gerado por mapeamento direto do Mercos em 2026-04-01. Leandro vai complementar com features adicionais.*
