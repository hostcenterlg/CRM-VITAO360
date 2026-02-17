# Phase 8: Comitê e Metas - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrar metas 2026 do SAP na CARTEIRA (coluna META por cliente) e criar aba COMITÊ no V13 com visão consolidada gerencial: consultor vs meta vs realizado, capacidade de atendimento, e blocos operacionais adaptados dos modelos de referência HTML. A aba COMITÊ deve ser uma visão única e densa que o gestor (Leandro) abre na reunião de equipe.

Dependências: Phase 3 (timeline mensal) + Phase 7 (redes). Ambas COMPLETAS.

</domain>

<decisions>
## Implementation Decisions

### Metas SAP na CARTEIRA (META-01)
- SAP já fornece meta por consultor (não precisa estimar)
- Coluna META ANUAL + coluna META MÊS na CARTEIRA por cliente
- Rateio da meta do consultor para clientes: **proporcional ao histórico de vendas 2025**
- Duas versões selecionáveis: proporcional ao histórico E distribuição igual — gestor escolhe qual visão usar
- Na CARTEIRA: meta puxa da PROJEÇÃO e do SINALEIRO, realizado puxa das vendas realizadas
- **Rateio dinâmico mês a mês:** se venda realizada < projetada → gap redistribui proporcionalmente para os demais clientes do mês seguinte. Se venda > projetada → reduz meta dos outros
- Fonte: BASE_SAP_META_PROJECAO_2026.xlsx (já em data/sources/sap/)
- Valores de referência: Meta total R$ 4.747.200 (SAP real, não R$ 5.7M aspiracional)

### Layout da aba COMITÊ (META-02)
- **1 aba** com blocos separados por linhas em branco (não múltiplas abas)
- **Tabela completa direto** — sem KPI cards (estilo FORMATO_APROVADO, Excel-like)
- Modelo completo (tudo): Meta, Realizado, %, GAP R$, Semáforo, Contatos/dia, Vendas/dia, Conversão, Capacidade %, Clientes ativos, Suporte, Follow-ups, Prospecções, Risco, Agenda oc./livre
- Adaptar ao máximo as 8 visões do modelo HTML V12_COMPLETO em blocos dentro da aba COMITÊ
- Blocos esperados (adaptados ao que os dados do V13 suportam):
  1. **Meta vs Realizado por consultor** — tabela principal
  2. **Capacidade/Produtividade** — carga/dia, vendas/dia, conversão, suporte
  3. **Alertas visuais** — riscos (ex: licença MANU), sobrecarga, gaps
  4. **Funil consolidado** — tipo de contato × resultado (estilo FORMATO_APROVADO)
  5. **Motivos de não compra** — top motivos com % e dono da ação

### Validação de Capacidade (META-03)
- Limite padrão: **50 atendimentos/dia** por consultor (pode chegar a 60 — muitos são rápidos)
- 22 dias úteis fixo por mês (sem cálculo de feriados)
- **Semáforo + barra de progresso** para cada consultor:
  - Verde: < 35/dia
  - Amarelo: 35-50/dia
  - Vermelho: > 50/dia
- Se consultor com agenda lotada: o CRM não redistribui automaticamente — mas os dados alimentam o motor de ranking da agenda diária (Fase 9)

### Sinaleiros e Formatação
- Semáforo + percentual colorido na mesma linha para GAP (meta - realizado)
  - Verde: atingiu/superou (>= 100%)
  - Amarelo: 70-99% da meta
  - Vermelho: < 70% da meta
- Barras horizontais para comparar volume por consultor (estilo dos modelos HTML)
- Header com filtro VENDEDOR + PERÍODO (estilo FORMATO_APROVADO)

### Claude's Discretion
- Quantos blocos exatos cabem na aba sem ficar poluída
- Quais visões dos 8 tabs do HTML são viáveis com fórmulas Excel (vs precisando de macro/VBA)
- Ordem dos blocos na aba COMITÊ
- Largura das colunas e formatação condicional específica
- Como implementar as "duas versões selecionáveis" de rateio (pode ser toggle via célula filtro ou seções paralelas)

</decisions>

<specifics>
## Specific Ideas

### Referências visuais (4 modelos HTML em Downloads/)
1. **DASH_FORMATO_APROVADO_DADOS_REAIS.html** — Layout mais próximo do Excel: Calibri 11px, bordas, header escuro, tabela TIPO×RESULTADO matrix, funil com colunas agrupadas (Contatos | Funil de Venda | Relacionamento | Não Venda), motivos de não compra + indicadores por consultor. **ESTE É O FORMATO APROVADO para uso em Excel.**
2. **DASH_ULTRA_REALISTA_VITAO360.html** — Dashboard analítico completo: cadência obrigatória T1→T2→T3→Orçamento→Venda→D+4→D+15→D+30→MKT, produtividade por consultor consolidada, evolução mensal, motivos com "dono da ação", receptivo por tipo de demanda.
3. **DASH_VITAO360_ANALYTICS.html** — KPIs 6-col, evolução 4 meses em cards, consolidado mensal por consultor, cadência de atendimento T1-T4+FUP, motivos evolução mensal com dono.
4. **DASHBOARD_VITAO360_V12_COMPLETO.html** — 8 tabs (Resumo/Operacional/Funil/Performance/Tendências/Sinaleiro/Eficiência/Produtividade), estilo web premium (Plus Jakarta Sans, cards com shadow, barras coloridas, insights em caixas verdes, alertas em caixas vermelhas).

### Visão geral do CRM
- O usuário quer TODAS as 8 visões do V12_COMPLETO reproduzidas NO CRM Excel (não só na aba COMITÊ)
- A aba DASH (Fase 5) já cobre parte: KPIs executivos + Performance + Pipeline
- A aba REDES_FRANQUIAS_v2 (Fase 7) já cobre: Sinaleiro de penetração
- A aba COMITÊ (Fase 8) deve cobrir: Meta vs Realizado + Produtividade + Alertas
- Visões restantes (Tendências detalhadas, Eficiência CAC/ROI, Cadência T1-T4) → deferred

### Motor de Ranking / Agenda Diária Inteligente (contexto crítico)
O objetivo FINAL do CRM é gerar agenda diária por consultor (40-60 atendimentos priorizados). O ranking deve considerar (em ordem de prioridade):
1. Orçamentos em andamento (alta urgência)
2. Cadastros novos (janela de oportunidade)
3. Clientes super quentes / alta probabilidade de fechamento
4. Melhor momento de compra (ciclo médio de compra atingido)
5. Cliente solicitou atendimento (inbound/receptivo)
6. Acessou e-commerce + carrinho aberto ou montou orçamento
7. Clientes no ciclo de reativação/resgate/salvamento
8. Follow-ups pendentes
9. Prospecções novas (SEMPRE rodando em paralelo)
10. Se meta pessoal em risco → aumentar prospecção no início do mês
11. Agenda cheia com alta probabilidade → postergar menor prioridade pro dia seguinte

**NOTA:** Este motor de ranking é o core value do CRM e alimenta a Fase 9 (Blueprint v2). A Fase 8 prepara os dados de META necessários para este ranking funcionar.

</specifics>

<deferred>
## Deferred Ideas

### Para Fase 9 (Blueprint v2) — PRIORITÁRIO
- Motor de ranking completo da agenda diária inteligente (10+ regras de priorização)
- Implementação da agenda com 50-60 atendimentos/dia priorizados automaticamente
- CARTEIRA expandida para 81 colunas incluindo todos os inputs do ranking

### Para fases futuras / backlog
- **Tendências mensais** — visão mês a mês com análise de sazonalidade (tab Tendências do V12_COMPLETO)
- **Eficiência comercial** — CAC, ROI, Win Rate, Contatos por Venda (tab Eficiência do V12_COMPLETO)
- **Cadência de atendimento** — protocolo T1→T2→T3→T4→D+4→D+15→D+30→MKT como visão separada (ULTRA_REALISTA)
- **Receptivo por tipo de demanda** — Status Pedido, 2ª Via NFe, Atraso Entrega, etc. (ULTRA_REALISTA)
- **Motivos de não compra evolução mensal** — com "dono da ação" por área (ANALYTICS)
- **Reprodução completa das 8 tabs** do V12_COMPLETO como abas ou blocos no Excel (beyond Phase 8)

</deferred>

---

*Phase: 08-comite-metas*
*Context gathered: 2026-02-17*
