# ESPECIFICAÇÃO COMPLETA — MERCOS → SaaS CRM VITAO360

> **Data:** 2026-04-01
> **Fonte:** Mapeamento direto do app.mercos.com/399424 (conta VITAO MAIS)
> **Objetivo:** Replicar TODOS os filtros, dashboards, indicadores e funcionalidades do Mercos no nosso SaaS
> **Status:** fonte de verdade para auditoria de paridade — usado por SQUAD JULIET (29/Abr/2026)

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

### 2.3 Catálogo Completo (29 indicadores)

#### Categorias de Estratégia:
- **Aquisição** — indicadores de novos clientes
- **Fidelização** — indicadores de retenção
- **Expansão** — indicadores de crescimento de vendas

#### VENDAS (8 indicadores)
1. Quantidade ou valor vendido de um produto ou categoria — Expansão
2. Valor diário em vendas de produtos — Expansão
3. Valor vendido em produtos comparado por vendedor — Expansão
4. Quantidade vendida em produtos comparado por categoria — Expansão
5. Evolução das vendas de um produto ou categoria — Expansão
6. Evolução de vendas — Expansão
7. Valor vendido comparado por vendedor — Expansão
8. Quantidade vendida comparado por categoria — Expansão

#### POSITIVAÇÃO (10 indicadores)
1. Positivação de clientes específica — Aquisição+Fidelização
2. Positivação de clientes diária — Aquisição+Fidelização
3. Positivação de novos clientes comparada por vendedor — Aquisição
4. Positivação de clientes ativos comparada por vendedor — Fidelização
5. Positivação de clientes da categoria ou produto específico — Expansão
6. Positivação de uma categoria ou produto diária — Expansão
7. Positivação de clientes da categoria ou produto por vendedor — Expansão
8. Positivação de clientes por categoria de produto — Expansão
9. Positivação de clientes geral — Aquisição+Fidelização
10. Positivação gauge no painel — Aquisição+Fidelização

#### FATURAMENTO (5 indicadores)
1. Faturamento específico — Expansão
2. Faturamento diário — Expansão
3. Faturamento total — Expansão
4. Faturamento comparado por vendedor — Expansão
5. Evolução do faturamento — Expansão

#### ATIVIDADES (3 indicadores)
1. Volume de atividades — Aquisição+Fidelização+Expansão
2. Volume de atividades por vendedor — idem
3. Volume de atividades diário — idem

#### OUTROS (3 indicadores)
1. Situação de carteira — Aquisição+Fidelização
2. Curva ABC de clientes — Fidelização
3. Conversão do E-commerce — Fidelização+Aquisição

---

## 3. INDICADORES — RELATÓRIOS (19 relatórios)

### 3.1 VENDAS (5)
- Resumo de vendas
- Vendas detalhadas
- Ranking de vendedor / Meta
- Relatório gerencial para representada
- Movimentações do Saldo Flex

### 3.2 FATURAMENTO E TÍTULOS (3)
- Pedidos faturados
- Faturamento
- Títulos

### 3.3 CLIENTES (7)
- Clientes
- Situação da carteira de clientes
- Positivação de clientes
- Curva ABC de clientes
- Acessos e atividades do E-commerce
- Visitas com check-in
- Relatório de tarefas realizadas

### 3.4 COMISSÕES (2)
- Relatório de comissões
- Comissões por pedido

### 3.5 PRODUTOS (3)
- Produtos mais vendidos
- Positivação de produtos por cliente
- Produtos por pedido

### 3.6 OUTROS (2)
- E-mails enviados
- Extrato das videochamadas

---

## 4. POSITIVAÇÃO DE CLIENTES — Relatório Detalhado

### 4.1 Abas: PAINEL | RELATÓRIOS

### 4.2 Filtros
- Período (data inicial / data final)
- Representada
- Vendedor (multi-select)
- Situação (Novos, Ativos, Inativos recentes, Inativos antigos)

### 4.3 Visualizações
- Donut chart segmentado: Novos %, Ativos %, Inativos recentes %, Inativos antigos %
- KPI: "% dos clientes ativos foram positivados neste mês"
- Toggle donut/line chart

### 4.4 Tabela (colunas configuráveis)
- Razão social (default)
- Nome fantasia
- CNPJ/CPF
- Inscrição Estadual
- E-mail / Telefone
- Cidade
- Último pedido (nº) (default)
- Data do último pedido (default)
- Data do penúltimo pedido (default)
- Diferença em dias (default)
- Vendedor do último pedido
- Situação (default)
- Tags de cliente

### 4.5 Exportação Excel

---

## 5. PEDIDOS

### 5.1 Abas: PEDIDOS | CONFIGURAÇÕES
### 5.2 Ações: Criar pedido/orçamento, Criar carrinho, Imprimir pedidos
### 5.3 Busca: pedido/cliente/representada/NF/data
### 5.4 Filtros Inline
- Tipo de pedido (Pedidos ativos/Todos/Orçamentos)
- Vendedor
- Plataforma (App, E-commerce, Web)
- Envio (Sem considerar/Enviados/Não enviados)
- Status (Em orçamento/Concluído/Faturado...)

### 5.5 Card de Pedido
- Número, vendedor, badges status
- Razão social + nome fantasia
- Condição pagamento, valor R$
- Agrupamento HOJE/ONTEM/data

### 5.6 Configurações
- Campos extras
- Status configurável
- Tipo de pedido (Venda, Bonificação, etc.)

---

## 6. CLIENTES

### 6.1 Abas: CLIENTES | CONFIGURAÇÕES
### 6.2 Ações: Cadastrar, Importar, Vínculos e permissões
### 6.3 Busca: nome/CNPJ + cidade/estado avançado
### 6.4 Sidebar Carteira: Donut com Ativos/Inativos rec/Inativos antigos/Prospects
### 6.5 Card lista: Nome/Razão, CNPJ, fantasia, telefone, email, cidade, alterar/excluir
### 6.6 Detalhe completo
- Cabeçalho: nome, alterar, vínculos, mais opções, telefone WhatsApp, email, endereço, CEP, mapa
- Sidebar resumo (6 meses): ranking, total compras, pedidos, ticket médio, dias sem comprar
- TAREFAS: criar tarefa, criar videochamada
- E-COMMERCE: acessar como cliente, toggle liberado, gerenciar acessos, último acesso
- LIMITE DE CRÉDITO: por representada
- TÍTULOS: a receber/recebidos, adicionar, WhatsApp cobrança
- PEDIDOS E ATIVIDADES (timeline): WhatsApp/Ligação/Pedido/Visita c/ check-in
- NOTAS FISCAIS
- PRODUTOS MAIS COMPRADOS (ranking)

---

## 7. PRODUTOS

### 7.1 Abas: PRODUTOS | PROMOÇÕES | DESTAQUES | CONFIGURAÇÕES
### 7.2 Sub-abas Produtos: Produtos e tabelas | Gerenciar estoque | Importar fotos
### 7.3 Ações: Cadastrar, Importar, Mais opções
### 7.4 Filtros: Categoria, Busca, Status (ativos/inativos)
### 7.5 Tabela
- Foto, Código (300000002), Nome, Variações, IPI, Unidade, Comissão %, Preço Mínimo, Preço Tabela
- **Preço por Estado** (1 coluna por estado brasileiro — CRÍTICO para Vitão: tabelas regionais Norte+Nordeste, Sudeste+Centro-Oeste, Sul)

---

## 8. E-COMMERCE B2B

### 8.1 URL: vitaomais.meuspedidos.com.br
### 8.2 Abas: CONFIGURAÇÕES | PERSONALIZAÇÃO
### 8.3 Sub-abas Configurações: E-commerce | Catálogo | Portal do cliente
### 8.4 Configurações principais
- E-commerce ativo (toggle)
- Visibilidade público/privado
- Aceitar apenas PJ
- Obrigar endereço
- Cadastro automático cliente
- Acesso imediato novos clientes
- Usuário responsável (recebe email orçamento)
- Configurações checkout
### 8.5 Features: Cupons, Relatório atividades, Acessar como cliente

---

## 9. TAREFAS E ATIVIDADES

### 9.1 Abas: TAREFAS | ROTEIROS
### 9.2 Ações: Criar tarefa, Registrar atividade, Exportar Excel
### 9.3 Filtros
- Período (data range)
- Vendedor (multi-tags)
- Cliente
- Meio de contato (WhatsApp/Ligação/Email/Visita/Videochamada)
- Status (não realizadas/realizadas/todas)
### 9.4 Tipos atividade: WhatsApp, Ligação, E-mail, Visita c/ check-in, Videochamada
### 9.5 Roteiros: Roteiro/Vendedor/Data/Repete/Dia semana/Qtde clientes/Situação

---

## 10. FUNCIONALIDADES TRANSVERSAIS

- Busca rápida global no header
- WhatsApp em header, detalhe cliente, títulos, atividades
- Excel em todas tabelas/relatórios + impressão pedidos
- Filtro por Representada (VITAO MAIS = 659182), limite crédito por rep, preços por rep
- Vendedores: Larissa, Manu, Daiane, Julio, Leandro (admin)

---

## 11. CHECKLIST DE PARIDADE (40 itens-chave)

### Dashboard de Indicadores
1. Filtros globais Mês/Ano/Vendedor no painel
2. 29 indicadores configuráveis com 3 categorias
3. 10 indicadores ativos default no painel
4. Gauge widgets (positivação, atividades)
5. Donut widgets (carteira, ABC)
6. Linha multi-série (evolução)

### Relatórios
7. 19 relatórios em 6 categorias acessíveis via menu
8. Exportação Excel funcional em todos
9. Filtros de período/vendedor/representada em cada
10. Toggle gráfico/tabela em positivação

### Pedidos
11. Aba PEDIDOS + CONFIGURAÇÕES
12. Filtros Tipo/Vendedor/Plataforma/Envio/Status
13. Card pedido com badges status, condição pgto, valor
14. Agrupamento HOJE/ONTEM/data
15. Status configurável + Tipo pedido (Venda/Bonificação)
16. Campos extras configuráveis

### Clientes
17. Sidebar widget Carteira (donut com 4 segmentos)
18. Cadastrar/Importar/Vínculos
19. Detalhe completo com timeline atividades
20. Resumo 6 meses (ranking, total, pedidos, ticket, dias)
21. WhatsApp inline em telefone/títulos
22. Limite crédito por representada
23. Títulos a receber/recebidos
24. Notas fiscais vinculadas
25. Produtos mais comprados (ranking)

### Produtos
26. Aba PRODUTOS + PROMOÇÕES + DESTAQUES + CONFIGURAÇÕES
27. **Preços por estado** (27 colunas, 1 por estado) — CRÍTICO
28. Categoria, IPI, Unidade, Comissão, Preço Mín/Tabela
29. Importar fotos em massa
30. Gerenciar estoque

### E-commerce
31. Portal vitaomais.meuspedidos.com.br
32. Toggle ativo, visibilidade, PJ, cadastro auto
33. Cupons de desconto
34. "Acessar como cliente" simulação
35. Relatório atividades

### Tarefas
36. Filtros: período, vendedor (multi), cliente, meio contato, status
37. Tipos: WhatsApp, Ligação, Email, Visita c/ check-in, Videochamada
38. Roteiros planejados (recorrência por dia da semana)

### Transversais
39. Busca global no header
40. Vendedores Larissa/Manu/Daiane/Julio/Leandro com perfis

---

*Documento gerado por mapeamento direto do Mercos em 2026-04-01.*
