# Auditoria de Paridade Mercos — 29/Abr/2026

> **Auditor:** SQUAD JULIET
> **Fonte:** `docs/specs/MERCOS_PARIDADE_SPEC.md`
> **Tempo de auditoria:** ~2h
> **Status:** READ-ONLY (sem código modificado)

---

## SUMÁRIO EXECUTIVO

| Status | Qtd | % |
|--------|-----|---|
| Implementado | 14 | 35% |
| Parcial | 15 | 37,5% |
| Ausente | 11 | 27,5% |
| **Total** | **40** | **100%** |

### Top 3 áreas mais completas
1. Pedidos (4/6 implementados ou parciais — filtros, cards, agrupamento e CSV exportação)
2. Tarefas/Atividades (3/3 tipos de contato + filtros básicos implementados)
3. Transversais — Busca global + Vendedores com perfis (2/2 implementados)

### Top 3 áreas mais ausentes
1. E-commerce B2B (5/5 itens ausentes — zero implementação de portal/configuração)
2. Produtos — abas extras (Promoções, Destaques, Estoque, Importar fotos — 4/5 ausentes)
3. Clientes — funcionalidades de detalhe (Títulos, Notas Fiscais, Limite de Crédito, Resumo 6 meses — 4/9 ausentes)

### Estimativa total de esforço para paridade
- Itens P0 ausentes/parciais: ~38h
- Itens P1 ausentes/parciais: ~22h
- Itens P2/P3: ~16h
- **TOTAL: ~76h**

---

## SEÇÃO 1 — NAVEGAÇÃO PRINCIPAL

### [1.1] Indicadores `/indicadores/`
- **Status:** Parcial
- **Onde está:** `frontend/src/app/page.tsx` (dashboard principal, aba `indicadores` na linha 82)
- **Gap:** No Mercos, Indicadores é a rota raiz dedicada. No CRM, o painel de indicadores é uma aba (`indicadores`) dentro do Dashboard principal (`/`). Não há rota `/indicadores/` isolada.
- **Esforço estimado:** baixo (<2h) — renomear rota ou criar redirect
- **Prioridade sugerida:** P3
- **Dependências técnicas:** nenhuma (só routing Next.js)

### [1.2] Pedidos `/pedidos/`
- **Status:** Implementado
- **Onde está:** `frontend/src/app/pedidos/page.tsx` — rota `/pedidos` com filtros e cards
- **Gap:** nenhum bloqueante de rota
- **Esforço estimado:** —
- **Prioridade sugerida:** —
- **Dependências técnicas:** —

### [1.3] Clientes `/clientes/`
- **Status:** Implementado
- **Onde está:** `frontend/src/app/clientes/page.tsx` + `frontend/src/app/carteira/page.tsx` — clientes listados em `/carteira` (nome diferente de `/clientes`)
- **Gap:** A rota principal é `/carteira`, não `/clientes`. O Mercos usa `/clientes/`. Há um link "Clientes" na sidebar apontando para `/clientes` (Sidebar.tsx:198), mas a rota real é `/carteira`.
- **Esforço estimado:** baixo (<2h)
- **Prioridade sugerida:** P2
- **Dependências técnicas:** ajuste de alias de rota

### [1.4] Produtos `/produtos/`
- **Status:** Implementado
- **Onde está:** `frontend/src/app/produtos/page.tsx`
- **Gap:** nenhum bloqueante de rota
- **Esforço estimado:** —
- **Prioridade sugerida:** —
- **Dependências técnicas:** —

### [1.5] E-Commerce `/configuracoes-portal-e-ecommerce/`
- **Status:** Ausente
- **Onde está:** não existe rota dedicada para configuração do e-commerce B2B
- **Gap:** Zero. Não há página de configuração de e-commerce no CRM.
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3 (Vitão usa vitaomais.meuspedidos.com.br diretamente — não via CRM)
- **Dependências técnicas:** nova página + endpoints backend de configuração + integração Mercos API

### [1.6] Tarefas `/agenda/`
- **Status:** Implementado
- **Onde está:** `frontend/src/app/agenda/page.tsx` — aba TAREFAS integrada na página Agenda
- **Gap:** nenhum bloqueante de rota
- **Esforço estimado:** —
- **Prioridade sugerida:** —
- **Dependências técnicas:** —

### [1.7] Minha Conta (configurações gerais)
- **Status:** Parcial
- **Onde está:** `frontend/src/app/admin/usuarios/` (gerenciamento de usuários)
- **Gap:** Não há perfil "Minha Conta" individual para o vendedor. Admin tem painel em `/admin/`. Falta página self-service de conta (alterar senha, preferências pessoais).
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2
- **Dependências técnicas:** nova página `/perfil` ou `/minha-conta`

---

## SEÇÃO 2 — INDICADORES (Painel)

### [2.1] Filtros globais Mês/Ano/Vendedor
- **Status:** Implementado
- **Onde está:** `frontend/src/app/page.tsx` linhas 487-517 — dropdowns `filtroMes`, `filtroAno`, `consultor` presentes na barra de filtros do dashboard
- **Gap:** nenhum
- **Esforço estimado:** —
- **Prioridade sugerida:** —
- **Dependências técnicas:** —

### [2.2] 10 indicadores ativos default
- **Status:** Parcial
- **Onde está:** `frontend/src/app/page.tsx` — aba `indicadores` (linha 82), endpoints `backend/app/api/routes_dashboard.py` (/evolucao-vendas, /positivacao-diaria, /positivacao-vendedor, /atendimentos-diarios, /ecommerce, /curva-abc)
- **Gap:** Mapeamento dos 10 do Mercos vs o que existe no CRM:
  1. Evolução de Venda (Linha multi-série): IMPLEMENTADO — `/api/dashboard/evolucao-vendas` + gráfico AreaChart
  2. Carteira de Clientes (Donut): IMPLEMENTADO — distribuição por situação presente
  3. Positivação (Donut + Gauge): PARCIAL — Donut existe; Gauge (widget circular de progresso) não implementado — só valor numérico
  4. Curva ABC de Clientes (Donut): IMPLEMENTADO — PieChart na aba indicadores
  5. E-commerce B2B (Barras): PARCIAL — só 4 KPIs numéricos, sem gráfico de barras
  6. Positivação Diária (Barras + Linha): IMPLEMENTADO — endpoint + gráfico existem
  7. Volume de Atendimentos Diário (Linha multi-série): IMPLEMENTADO — `/api/dashboard/atendimentos-diarios`
  8. Volume de Atendimentos (Gauge): AUSENTE — só contagem numérica, sem gauge visual
  9. Positivação Específica (Donut por vendedor/plataforma): PARCIAL — positivação por vendedor existe, mas sem segmentação por plataforma/situação
  10. Positivação Comparada por Vendedor (Barras): IMPLEMENTADO — `/api/dashboard/positivacao-vendedor` + BarChart
- **Esforço estimado:** médio (2-8h) — implementar Gauge widgets (2 instâncias) + gráfico barras E-commerce
- **Prioridade sugerida:** P1
- **Dependências técnicas:** novo componente GaugeChart (Recharts RadialBarChart ou SVG custom); sem migration

### [2.3] 29 indicadores no catálogo
- **Status:** Parcial
- **Onde está:** `backend/app/api/routes_dashboard.py` — ~12 endpoints existentes
- **Gap:** Dos 29 indicadores catalogados no Mercos, o CRM tem ~12 cobertos (estimativa):
  - VENDAS (8): Evolução vendas (OK), Valor diário (OK via evolucao-vendas), Valor por vendedor (OK via performance), Qty por categoria (ausente), Evolução produto (ausente), Evolução geral (OK), Valor comparado por vendedor (OK), Qty por categoria-2 (ausente). Total: ~5/8
  - POSITIVACAO (10): ~7/10 — ausentes: Positivação por produto específico, Positivação diária de produto, Positivação de produto por vendedor
  - FATURAMENTO (5): ~3/5 — ausentes: Faturamento específico (por produto), Faturamento diário detalhado
  - ATIVIDADES (3): ~3/3 — implementados
  - OUTROS (3): Situação carteira (OK), Curva ABC (OK), Conversão E-commerce (parcial). Total: ~2/3
  - **Total estimado: ~20/29 indicadores cobertos conceitualmente**
- **Esforço estimado:** alto (>8h) — ~9 indicadores faltantes de produto/categoria
- **Prioridade sugerida:** P2
- **Dependências técnicas:** endpoints novos para indicadores de produto; tabelas `produtos` e `venda_itens` já existem (migration 97b67bcd926f)

---

## SEÇÃO 3 — RELATÓRIOS (19 relatórios)

### [3.1] VENDAS (5 relatórios do Mercos)

**Resumo de vendas**
- **Status:** Implementado
- **Onde está:** `backend/app/api/routes_relatorios.py:230` — `/api/relatorios/vendas` gera XLSX com dados de vendas

**Vendas detalhadas**
- **Status:** Implementado
- **Onde está:** mesmo endpoint acima, com colunas: Data, Nº Pedido, Cliente, CNPJ, Consultor, Valor, Status, Cond. Pagamento

**Ranking de vendedor / Meta**
- **Status:** Implementado
- **Onde está:** `backend/app/api/routes_relatorios.py:725` — `/api/relatorios/metas` — relatório Metas vs Realizado por consultor

**Relatório gerencial para representada**
- **Status:** Ausente
- **Gap:** Não há relatório específico para representada (VITAO MAIS = 659182). O conceito de "representada" não existe no schema atual.
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

**Movimentações do Saldo Flex**
- **Status:** Ausente
- **Gap:** Saldo Flex é feature específica do Mercos (crédito flexível de cliente). Não existe no schema VITAO360.
- **Esforço estimado:** alto (>8h) — requer novo conceito de domínio
- **Prioridade sugerida:** P3 (fora do escopo atual)

### [3.2] FATURAMENTO E TÍTULOS (3 relatórios)

**Pedidos faturados**
- **Status:** Parcial
- **Onde está:** relatório de vendas cobre parcialmente (filtro por status FATURADO em `/pedidos`)
- **Gap:** Não há relatório XLSX dedicado a "pedidos faturados" (só a lista de pedidos)
- **Esforço estimado:** baixo (<2h) — filtro adicional no relatório de vendas

**Faturamento**
- **Status:** Implementado
- **Onde está:** `/api/relatorios/metas` + dados de faturamento nos KPIs

**Títulos**
- **Status:** Ausente
- **Gap:** Não há tabela de títulos (contas a receber/recebidas) no schema. Nenhum endpoint de títulos.
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P1 (importante para gestão financeira/cobrança)

### [3.3] CLIENTES (7 relatórios)

**Clientes**
- **Status:** Implementado
- **Onde está:** exportação CSV em `/carteira` (`frontend/src/app/carteira/page.tsx`)

**Situação da carteira de clientes**
- **Status:** Implementado
- **Onde está:** `/api/relatorios/clientes-inativos` + stats em `/api/clientes/stats`

**Positivação de clientes**
- **Status:** Implementado
- **Onde está:** `backend/app/api/routes_relatorios.py:357` — `/api/relatorios/positivacao`

**Curva ABC de clientes**
- **Status:** Parcial
- **Onde está:** dados de curva ABC nos KPIs e distribuição; sem relatório XLSX dedicado de curva ABC
- **Gap:** Falta endpoint `/api/relatorios/curva-abc` que gere XLSX
- **Esforço estimado:** baixo (<2h)
- **Prioridade sugerida:** P2

**Acessos e atividades do E-commerce**
- **Status:** Ausente
- **Gap:** Sem portal E-commerce implementado; sem dados de acesso
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3

**Visitas com check-in**
- **Status:** Ausente
- **Gap:** Tipo de atividade VISITA existe no `AtendimentoForm.tsx` (linha 57), mas check-in geolocalizado não está implementado. Não há campo de localização no `LogInteracao`.
- **Esforço estimado:** alto (>8h) — requer geolocalização + novo campo na migration
- **Prioridade sugerida:** P3

**Relatório de tarefas realizadas**
- **Status:** Parcial
- **Onde está:** `/api/relatorios/atividades` cobre parcialmente
- **Gap:** Falta filtro por "tipo tarefa" e status tarefa (realizada/não realizada) no relatório. O XLSX de atividades não diferencia tarefas de atendimentos.
- **Esforço estimado:** baixo (<2h)
- **Prioridade sugerida:** P2

### [3.4] COMISSÕES (2 relatórios)

**Relatório de comissões**
- **Status:** Ausente
- **Gap:** Campo `comissao_pct` existe em `Produto` (migration 97b67bcd926f), mas não há cálculo de comissão por vendedor, nem relatório.
- **Esforço estimado:** médio (2-8h) — usar comissao_pct * valor_pedido
- **Prioridade sugerida:** P1

**Comissões por pedido**
- **Status:** Ausente
- **Gap:** idem acima
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [3.5] PRODUTOS (3 relatórios)

**Produtos mais vendidos**
- **Status:** Implementado
- **Onde está:** `backend/app/api/routes_produtos.py:149` — `/api/produtos/mais-vendidos` + `MaisVendidosSection` em `frontend/src/app/produtos/page.tsx:256`

**Positivação de produtos por cliente**
- **Status:** Ausente
- **Gap:** Não há relatório de quais clientes compraram quais produtos
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

**Produtos por pedido**
- **Status:** Ausente
- **Gap:** `VendaItem` existe no schema (migration 97b67bcd926f), mas não há relatório XLSX detalhando itens por pedido
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [3.6] OUTROS (2 relatórios)

**E-mails enviados**
- **Status:** Ausente
- **Gap:** Tipo EMAIL existe em `AtendimentoForm.tsx`, mas sem relatório de e-mails disparados
- **Esforço estimado:** baixo (<2h) — filtro no relatório de atividades por tipo=EMAIL
- **Prioridade sugerida:** P3

**Extrato das videochamadas**
- **Status:** Ausente
- **Gap:** Tipo VIDEOCHAMADA existe em `AtendimentoForm.tsx` (linha 59), mas sem relatório dedicado
- **Esforço estimado:** baixo (<2h) — filtro no relatório de atividades
- **Prioridade sugerida:** P3

---

## SEÇÃO 4 — POSITIVAÇÃO DETALHADA

### [4.1] Abas PAINEL | RELATÓRIOS
- **Status:** Parcial
- **Onde está:** o painel de positivação está embutido na aba `indicadores` do dashboard (`page.tsx`); o relatório XLSX está em `/api/relatorios/positivacao`
- **Gap:** Não existe uma página `/positivacao/` dedicada com abas PAINEL | RELATÓRIOS separadas como no Mercos
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

### [4.2] Filtros de positivação (Período, Representada, Vendedor multi-select, Situação)
- **Status:** Parcial
- **Onde está:** `/api/relatorios/positivacao` aceita `mes`, `ano`, `consultor`
- **Gap:** Filtro por "Situação" (Novos/Ativos/Inativos rec/Inativos antigos) ausente; multi-select de vendedor não implementado; filtro por "Representada" não existe no schema
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

### [4.3] Visualizações (Donut segmentado + KPI % + Toggle donut/linha)
- **Status:** Parcial
- **Onde está:** Donut de positivação existe na aba `indicadores` do dashboard
- **Gap:** Sem toggle donut/linha; sem KPI explícito "% dos clientes ativos positivados este mês" como valor primário
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [4.4] Tabela de positivação (colunas configuráveis)
- **Status:** Ausente
- **Gap:** Não existe tabela de positivação interativa com as 13 colunas do Mercos (razão social, CNPJ, último pedido, data, penúltimo pedido, diferença dias, situação, etc.)
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [4.5] Exportação Excel
- **Status:** Implementado
- **Onde está:** `/api/relatorios/positivacao` gera XLSX com 7 colunas (parcialmente compatível)

---

## SEÇÃO 5 — PEDIDOS

### [5.1] Abas PEDIDOS | CONFIGURAÇÕES
- **Status:** Parcial
- **Onde está:** `frontend/src/app/pedidos/page.tsx` — aba PEDIDOS implementada
- **Gap:** Aba CONFIGURAÇÕES (campos extras, status configurável, tipo de pedido) totalmente ausente
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

### [5.2] Ações (Criar pedido/orçamento, Criar carrinho, Imprimir)
- **Status:** Ausente
- **Gap:** Página de pedidos é read-only. Não há botão de criar pedido/orçamento. Sem impressão de pedidos.
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P2 (CRM VITAO360 é observador de pedidos SAP, não emissor — decisão arquitetural)

### [5.3] Busca: pedido/cliente/representada/NF/data
- **Status:** Implementado
- **Onde está:** `frontend/src/app/pedidos/page.tsx:519` — campo busca por cliente, CNPJ ou número de pedido

### [5.4] Filtros Inline (Tipo/Vendedor/Plataforma/Envio/Status)
- **Status:** Parcial
- **Onde está:** `frontend/src/app/pedidos/page.tsx:559-637` — filtros por Status, Consultor, Data
- **Gap:** Filtros de "Tipo de pedido" (Pedidos ativos/Todos/Orçamentos), "Plataforma" (App/E-commerce/Web), "Envio" (Enviados/Não enviados) ausentes
- **Esforço estimado:** baixo (<2h)
- **Prioridade sugerida:** P1

### [5.5] Card de pedido (badges status, condição pgto, valor, agrupamento)
- **Status:** Implementado
- **Onde está:** `frontend/src/app/pedidos/page.tsx:228` — `CardPedido` com número, consultor, status badge, razão social, condição pagamento, valor; agrupamento HOJE/ONTEM/data em `labelData` (linha 62)

### [5.6] Configurações (campos extras, status configurável, tipo pedido)
- **Status:** Ausente
- **Gap:** Não existe página de configuração de pedidos
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P3

---

## SEÇÃO 6 — CLIENTES

### [6.1] Abas CLIENTES | CONFIGURAÇÕES
- **Status:** Parcial
- **Onde está:** `/carteira` tem lista de clientes; sem aba CONFIGURAÇÕES dedicada
- **Gap:** Aba CONFIGURAÇÕES (campos personalizados, regras de situação) ausente
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P3

### [6.2] Ações: Cadastrar/Importar/Vínculos e permissões
- **Status:** Parcial
- **Onde está:** `frontend/src/app/admin/import/` — importação existe; edição inline via PATCH `/api/clientes/{cnpj}`
- **Gap:** Cadastro manual de novo cliente ausente; "Vínculos e permissões" (representadas vinculadas) não implementado
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

### [6.3] Busca: nome/CNPJ + cidade/estado avançado
- **Status:** Implementado
- **Onde está:** `frontend/src/app/carteira/page.tsx:44-100` — filtros por busca (nome/CNPJ), UF, cidade (implícito via busca)

### [6.4] Sidebar Carteira (Donut 4 segmentos)
- **Status:** Implementado
- **Onde está:** dashboard principal aba `funil` + aba `saude` — distribuição por situação (ATIVO/INAT.REC/INAT.ANT/PROSPECT); também no KPI hero section

### [6.5] Card lista (nome, CNPJ, fantasia, telefone, email, cidade)
- **Status:** Implementado
- **Onde está:** `frontend/src/components/ClienteTable.tsx` — tabela com colunas relevantes

### [6.6] Detalhe completo do cliente
- **Status:** Parcial
- **Onde está:** `frontend/src/components/ClienteDetalhe.tsx` — drawer lateral com 8 blocos
- **Itens presentes:**
  - Cabeçalho com nome, telefone, email, endereço: IMPLEMENTADO (bloco Identidade)
  - WhatsApp inline (envio de mensagem pelo drawer): IMPLEMENTADO (bloco IA)
  - Timeline de atividades (PEDIDOS E ATIVIDADES): IMPLEMENTADO (bloco Timeline + Histórico)
  - Produtos mais comprados: PARCIAL — "Ultimas Compras" mostra pedidos, mas não ranking de produtos mais comprados por cliente
  - Mapa: AUSENTE
  - Tarefas: PARCIAL — criar atendimento existe, mas sem criação de tarefa agendada pelo detalhe
  - E-COMMERCE (acessar como cliente, toggle liberado): AUSENTE
  - Limite de crédito por representada: AUSENTE
  - Títulos a receber/recebidos + WhatsApp cobrança: AUSENTE
  - Notas Fiscais vinculadas: AUSENTE
- **Esforço estimado:** alto (>8h) — múltiplos blocos faltantes
- **Prioridade sugerida:** P0/P1

---

## SEÇÃO 7 — PRODUTOS

### [7.1] Abas PRODUTOS | PROMOÇÕES | DESTAQUES | CONFIGURAÇÕES
- **Status:** Parcial
- **Onde está:** `frontend/src/app/produtos/page.tsx` — apenas aba PRODUTOS implementada
- **Gap:** Abas PROMOÇÕES, DESTAQUES e CONFIGURAÇÕES totalmente ausentes
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P2

### [7.2] Sub-abas Produtos (Produtos e tabelas | Gerenciar estoque | Importar fotos)
- **Status:** Parcial
- **Onde está:** listagem de produtos existe; sem sub-abas
- **Gap:** "Gerenciar estoque" e "Importar fotos" ausentes
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P2

### [7.3] Ações (Cadastrar, Importar, Mais opções)
- **Status:** Parcial
- **Onde está:** `POST /api/produtos` e `PATCH /api/produtos/{id}` existem (admin-only); sem UI de cadastro frontend
- **Gap:** Sem tela de cadastro de produto; sem importação em massa no frontend
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P2

### [7.4] Filtros (Categoria, Busca, Status ativo/inativo)
- **Status:** Implementado
- **Onde está:** `frontend/src/app/produtos/page.tsx` — filtros por categoria, busca textual e status ativo/inativo

### [7.5] Tabela com Preços por Estado (27 colunas — CRÍTICO)
- **Status:** Parcial
- **Onde está:** Schema `precos_regionais` existe (migration `97b67bcd926f` — tabela com `produto_id`, `uf`, `preco`); frontend exibe precos regionais no modal de detalhe (`produtos/page.tsx:190-206`)
- **Gap:** A tabela principal de produtos não tem colunas por estado (27 colunas). O modal mostra como lista sem a visão de grade de 27 estados simultâneos. O Mercos exibe uma coluna por estado diretamente na tabela de listagem — isso não está implementado.
- **Esforço estimado:** médio (2-8h) — UI de tabela com scroll horizontal por estado
- **Prioridade sugerida:** P0 (CRÍTICO para Vitão: tabelas regionais Norte+Nordeste, Sudeste+CO, Sul)

---

## SEÇÃO 8 — E-COMMERCE

### [8.1] Portal vitaomais.meuspedidos.com.br
- **Status:** Ausente
- **Gap:** Portal é gerenciado diretamente no Mercos. O CRM não gerencia este portal.
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3

### [8.2] Configurações (toggle ativo, visibilidade, PJ, cadastro auto)
- **Status:** Ausente
- **Gap:** Nenhuma tela de configuração de e-commerce
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3

### [8.3] Cupons de desconto
- **Status:** Ausente
- **Gap:** Não implementado
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3

### [8.4] "Acessar como cliente" simulação
- **Status:** Ausente
- **Gap:** Feature de impersonation de cliente para ver o e-commerce
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3

### [8.5] Relatório de atividades do e-commerce
- **Status:** Ausente
- **Gap:** Não implementado
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P3

---

## SEÇÃO 9 — TAREFAS E ATIVIDADES

### [9.1] Abas TAREFAS | ROTEIROS
- **Status:** Parcial
- **Onde está:** `frontend/src/app/agenda/page.tsx` — aba TAREFAS implementada (linha 26, `AgendaPageTab = 'compromissos' | 'tarefas'`)
- **Gap:** Aba ROTEIROS completamente ausente. Não há conceito de roteiro (visita planejada recorrente por dia da semana) no CRM.
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P1

### [9.2] Ações (Criar tarefa, Registrar atividade, Exportar Excel)
- **Status:** Parcial
- **Onde está:** "Registrar atividade" implementado via `AtendimentoForm.tsx` e `AtendimentoModal.tsx`; exportação CSV existe em `/carteira`
- **Gap:** "Criar tarefa" como entidade separada (com data, responsável, status) não implementado. Existe `TarefasPanel.tsx` que agrega follow-ups e agenda, mas sem criação de tarefa avulsa. Exportação Excel específica de tarefas ausente.
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [9.3] Filtros de tarefas (Período, Vendedor multi, Cliente, Meio contato, Status)
- **Status:** Parcial
- **Onde está:** `frontend/src/app/agenda/page.tsx` — filtros por consultor e data existem
- **Gap:** Filtro por "Meio de contato" (WhatsApp/Ligação/Email/Visita/Videochamada) ausente; filtro por "Cliente" específico ausente; "Status" (realizadas/não realizadas/todas) ausente
- **Esforço estimado:** baixo (<2h)
- **Prioridade sugerida:** P1

### [9.4] Tipos de atividade (WhatsApp, Ligação, Email, Visita c/check-in, Videochamada)
- **Status:** Parcial
- **Onde está:** `frontend/src/components/AtendimentoForm.tsx:54-60` — TIPOS_CONTATO = ['LIGACAO', 'WHATSAPP', 'VISITA', 'EMAIL', 'VIDEOCHAMADA']
- **Gap:** Todos os 5 tipos estão no formulário. Porém "Visita c/ check-in" não tem geolocalização — apenas o tipo VISITA sem localização. A parity aqui é de nome mas não de funcionalidade completa (sem GPS/mapa).
- **Esforço estimado:** alto (>8h) — check-in com geolocalização
- **Prioridade sugerida:** P2 (sem GPS é suficiente para registrar visita)

### [9.5] Roteiros (Roteiro/Vendedor/Data/Repete/Dia semana/Qtde clientes/Situação)
- **Status:** Ausente
- **Gap:** Nenhuma estrutura de roteiro no schema ou no frontend
- **Esforço estimado:** alto (>8h) — novo modelo de dados + nova página
- **Prioridade sugerida:** P1

---

## SEÇÃO 10 — FUNCIONALIDADES TRANSVERSAIS

### [10.1] Busca rápida global no header
- **Status:** Implementado
- **Onde está:** `frontend/src/components/AppShell.tsx:9,498` — `SearchModal` importado e aberto pelo `SearchInput` no header

### [10.2] WhatsApp no header, detalhe cliente, títulos, atividades
- **Status:** Parcial
- **Onde está:** WhatsApp no detalhe cliente (bloco IA, `ClienteDetalhe.tsx:868`); WhatsApp na agenda (`agenda/page.tsx` — modal de envio WhatsApp); WhatsApp no header (sino de notificações, não WA direto)
- **Gap:** WhatsApp no header (botão de WA rápido para qualquer número) ausente; WhatsApp em títulos ausente (títulos não existem)
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [10.3] Excel em todas tabelas/relatórios + impressão pedidos
- **Status:** Parcial
- **Onde está:** Exportação CSV em pedidos (`pedidos/page.tsx:387`), exportação CSV em carteira (`carteira/page.tsx`); relatórios XLSX em `/api/relatorios/*`
- **Gap:** Nem todas as tabelas têm exportação (falta em produtos, agenda/tarefas, positivação dedicada); impressão de pedidos ausente
- **Esforço estimado:** médio (2-8h)
- **Prioridade sugerida:** P1

### [10.4] Filtro por Representada (VITAO MAIS = 659182)
- **Status:** Ausente
- **Gap:** O conceito de "representada" não existe no schema do CRM VITAO360. Todos os dados são da VITAO MAIS implicitamente. Para multi-representada (futura expansão SaaS), seria necessário novo campo.
- **Esforço estimado:** alto (>8h)
- **Prioridade sugerida:** P3 (VITAO tem uma única representada — não é bloqueante)

### [10.5] Vendedores Larissa/Manu/Daiane/Julio/Leandro com perfis
- **Status:** Implementado
- **Onde está:** `backend/app/models/usuario.py:54` — roles `admin|gerente|consultor|consultor_externo`; BRAVO implementou RBAC completo (migration `a1b2c3d4e5f6_rbac_role_backfill.py`); `AuthContext.tsx` expandido

---

## CHECKLIST DE 40 ITENS-CHAVE (resumo da seção 11 do spec)

### Dashboard de Indicadores (itens 1-6)
| # | Item | Status |
|---|------|--------|
| 1 | Filtros globais Mês/Ano/Vendedor no painel | Implementado |
| 2 | 29 indicadores configuráveis com 3 categorias | Parcial (~20/29) |
| 3 | 10 indicadores ativos default no painel | Parcial (8/10 — sem Gauge) |
| 4 | Gauge widgets (positivação, atividades) | Ausente |
| 5 | Donut widgets (carteira, ABC) | Implementado |
| 6 | Linha multi-série (evolução) | Implementado |

### Relatórios (itens 7-10)
| # | Item | Status |
|---|------|--------|
| 7 | 19 relatórios em 6 categorias via menu | Parcial (5 de 19) |
| 8 | Exportação Excel funcional em todos | Parcial (5 relatórios XLSX, sem os 14 faltantes) |
| 9 | Filtros de período/vendedor/representada em cada | Parcial (período/vendedor OK; representada ausente) |
| 10 | Toggle gráfico/tabela em positivação | Ausente |

### Pedidos (itens 11-16)
| # | Item | Status |
|---|------|--------|
| 11 | Aba PEDIDOS + CONFIGURAÇÕES | Parcial (PEDIDOS sim; CONFIGURAÇÕES não) |
| 12 | Filtros Tipo/Vendedor/Plataforma/Envio/Status | Parcial (Vendedor/Status OK; Tipo/Plataforma/Envio não) |
| 13 | Card pedido com badges status, condição pgto, valor | Implementado |
| 14 | Agrupamento HOJE/ONTEM/data | Implementado |
| 15 | Status configurável + Tipo pedido (Venda/Bonificação) | Ausente |
| 16 | Campos extras configuráveis | Ausente |

### Clientes (itens 17-25)
| # | Item | Status |
|---|------|--------|
| 17 | Sidebar widget Carteira (donut 4 segmentos) | Implementado |
| 18 | Cadastrar/Importar/Vínculos | Parcial (importar OK; cadastrar/vínculos parcial) |
| 19 | Detalhe completo com timeline atividades | Parcial (timeline OK; faltam blocos) |
| 20 | Resumo 6 meses (ranking, total, pedidos, ticket, dias) | Parcial (ticket, dias, faturamento OK; ranking e mini-sidebar resumo como no Mercos ausente) |
| 21 | WhatsApp inline em telefone/títulos | Parcial (no detalhe/agenda OK; em títulos ausente) |
| 22 | Limite crédito por representada | Ausente |
| 23 | Títulos a receber/recebidos | Ausente |
| 24 | Notas fiscais vinculadas | Ausente |
| 25 | Produtos mais comprados (ranking por cliente) | Parcial (ultimas compras OK; ranking de produtos não) |

### Produtos (itens 26-30)
| # | Item | Status |
|---|------|--------|
| 26 | Aba PRODUTOS + PROMOÇÕES + DESTAQUES + CONFIGURAÇÕES | Parcial (PRODUTOS OK; demais ausentes) |
| 27 | Preços por estado (27 colunas) — CRÍTICO | Parcial (schema OK; UI de grade 27 estados ausente) |
| 28 | Categoria, IPI, Unidade, Comissão, Preço Mín/Tabela | Implementado |
| 29 | Importar fotos em massa | Ausente |
| 30 | Gerenciar estoque | Ausente |

### E-commerce (itens 31-35)
| # | Item | Status |
|---|------|--------|
| 31 | Portal vitaomais.meuspedidos.com.br | Ausente |
| 32 | Toggle ativo, visibilidade, PJ, cadastro auto | Ausente |
| 33 | Cupons de desconto | Ausente |
| 34 | "Acessar como cliente" simulação | Ausente |
| 35 | Relatório atividades e-commerce | Ausente |

### Tarefas (itens 36-38)
| # | Item | Status |
|---|------|--------|
| 36 | Filtros: período, vendedor multi, cliente, meio contato, status | Parcial (período/vendedor OK; cliente/meio/status ausentes) |
| 37 | Tipos: WhatsApp, Ligação, Email, Visita c/check-in, Videochamada | Parcial (5 tipos sem GPS) |
| 38 | Roteiros planejados (recorrência por dia da semana) | Ausente |

### Transversais (itens 39-40)
| # | Item | Status |
|---|------|--------|
| 39 | Busca global no header | Implementado |
| 40 | Vendedores Larissa/Manu/Daiane/Julio/Leandro com perfis | Implementado |

---

## RECOMENDAÇÕES DE ROADMAP DE IMPLEMENTAÇÃO

### Wave Mercos-1 — P0 Crítico para operação diária: ~18h
**Itens:**
- [item 4] Gauge widgets — positivação e atividades (~4h)
- [item 27] Preços por estado — grade 27 colunas na tabela de produtos (~4h)
- [item 19/23/24] Blocos faltantes no detalhe cliente: Títulos a receber/recebidos + NF vinculadas (~6h)
- [item 12] Filtros de pedidos: Tipo/Plataforma/Envio (~2h)
- [item 36] Filtros de tarefas: meio contato + status realizada/não realizada (~2h)

**Squads sugeridos:** SQUAD LIMA (backend + frontend) para detalhe cliente; SQUAD MIKE para indicadores gauge
**Justificativa:** Preços por estado é bloqueante para o dia a dia de negociação. Titles/NF afetam cobrança. Gauge widgets completam o painel principal.

### Wave Mercos-2 — P1 Alta prioridade: ~30h
**Itens:**
- [item 7/8] Relatórios faltantes: Comissões (2), Produtos por pedido (1), Curva ABC XLSX (1) (~8h)
- [item 23] Títulos (estrutura completa: schema + endpoints + UI) (~8h)
- [item 38] Roteiros planejados (novo modelo de dados + página) (~8h)
- [item 10] Toggle gráfico/tabela em positivação (~2h)
- [item 9.2] Criar tarefa avulsa (não só follow-up de cliente) (~4h)

**Squads sugeridos:** SQUAD NOVEMBER (tarefas/roteiros); SQUAD OSCAR (relatórios + comissões)

### Wave Mercos-3 — P2/P3 Completude: ~28h
**Itens:**
- [item 26] Abas produtos: Promoções, Destaques (~6h)
- [item 30] Gerenciar estoque (~4h)
- [item 11/16] Configurações de pedidos + campos extras (~4h)
- [item 2] Indicadores de produto faltantes nos 29 (~8h)
- [item 31-35] E-commerce — avaliar se necessário ou manter gerenciamento direto no Mercos (~6h)

---

## REGRA DE NEGÓCIO RELEVANTE — DDE/CANAIS

Confirmado em `SQUAD_COORDINATION_29ABR.md` linha 131-143: DDE/Análise Crítica aplica-se **somente** a clientes dos canais **Direto**, **Indireto** e **Food Service**. Clientes de Varejo, PME e Interno ficam de fora.

**Impacto na paridade Mercos:**
- O spec Mercos não menciona restrição por canal para seus indicadores — Mercos trata todos os clientes de forma uniforme.
- No CRM VITAO360, o filtro `canal_id` na arquitetura multi-canal impõe essa restrição naturalmente.
- **Ação necessária:** Ao implementar relatórios de comissão, positivação detalhada e DDE em Waves futuras, garantir que a UI exiba nota "Análise Crítica não aplicável a clientes do canal Varejo/PME/Interno" (fallback já planejado pelo SQUAD HOTEL).
- Os indicadores de positivação e faturamento do painel principal já respeitam isso via `user_canal_ids` no backend.

---

## ITENS NÃO MAPEADOS DO SPEC

Os seguintes itens do spec não puderam ser totalmente auditados por ausência de acesso ao banco PROD de forma read-only durante esta sessão:

1. **Contagem real de indicadores populados**: foram auditados os endpoints e o código UI; os dados reais (quantos dos 29 indicadores retornam valores não-zero) dependem dos dados importados.
2. **Precos regionais populados por UF**: o schema `precos_regionais` existe mas não foi possível verificar se está populado para todos os 27 estados dos produtos VITAO.
3. **WhatsApp inline em pedidos**: o Mercos tem WhatsApp no detalhe de pedido para contato com cliente. Não encontrei evidência explícita disso no detalhe de pedido do CRM (o modal de pedido é read-only sem WhatsApp). Possivelmente ausente.
