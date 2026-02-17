# Phase 9: Blueprint v2 - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Auditar, mapear e recriar do zero a aba CARTEIRA completa no V13, replicando a estrutura de 263 colunas do V12 COM_DADOS com 6 secoes, 3 niveis de agrupamento [+], e motor de inteligencia para gerar AGENDA DIARIA INTELIGENTE por consultor. Inclui criacao de 4 abas AGENDA individuais e todo o fluxo operacional diario.

**MUDANCA DE ESCOPO:** O roadmap original dizia "expandir de 46 para 81 colunas". Na discussao, ficou claro que o escopo real e RECRIAR a CARTEIRA completa do V12 (263 colunas) no V13, com auditoria profunda + motor de inteligencia novo.

</domain>

<decisions>
## Implementation Decisions

### Estrutura da CARTEIRA (Escopo Real)

- V12 COM_DADOS (263 colunas, 8.302 linhas) e a referencia completa a ser replicada
- Recriar do ZERO apos auditoria profunda do V12 -- nao copiar, ENTENDER e reconstruir
- Primeiro auditar racional, formulas e logica, depois decidir quais abas de suporte recriar (DRAFTs, AGENDA, REGRAS)
- CARTEIRA = visao 360 do cliente na MESMA LINHA, trackeado por CNPJ
- 4 visoes analiticas por cliente: MERCOS (comportamental), FUNIL (atendimento), SAP (cadastral), FATURAMENTO (acompanhamento)
- Base de dados: SAP completo (ativos com/sem atendimento + inativos + bloqueados) + Mercos (ativos + inativos recente/antigo + prospects)
- Regra de ouro: Se tem pedido no Mercos -> OBRIGATORIAMENTE tem cadastro no SAP. Prospects Mercos podem nao estar no SAP.

### Fluxo de Dados entre Abas

- META por cliente vem da aba PROJECAO (rateio proporcional ja calculado na Fase 1)
- REALIZADO mensal puxa do DRAFT 1 (vendas Mercos -- fonte primaria de vendas)
- JUSTIFICATIVA semanal (S1-S4) = formula automatica que puxa resultado do atendimento + consultor pode sobrescrever manualmente
- Se tem VENDA -> justificativa = "VENDA/PEDIDO"
- Se nao tem VENDA -> puxa status real: ORCAMENTO, PROSPECCAO, EM ATENDIMENTO, NEGOCIACAO, CADASTRO, RECOMPRA, CS, POS-VENDA, RELACIONAMENTO, NUTRICAO, PERDA
- Fontes de formulas: auditar V12 para definir melhor mapeamento no V13

### Ancoras

- Cada super grupo tem uma ancora principal (coluna que fica visivel quando grupo colapsado)
- Cada sub-grupo dentro do super grupo tambem tem ancora propria
- Ancoras ja foram pensadas e projetadas no V12 -- respeitar 100% como estao
- Servem para: facilitacao de visualizacao e analise de inteligencia para conferir agenda dos consultores
- Modos de uso: grupo todo oculto com so ancora principal OU cada sub-grupo com suas ancoras visiveis

### Organizacao em Grupos

- Seguir 6 secoes do V12 (NAO 8 do roadmap): MERCOS, FUNIL, SAP, STATUS SAP, DADOS CADASTRAIS SAP, FATURAMENTO
- Manter 3 niveis de agrupamento [+]: Nivel 1 (super grupo) -> Nivel 2 (sub-grupo) -> Nivel 3 (detalhe)
- Header 3 linhas: L1=super grupo, L2=sub-grupo, L3=nome da coluna
- Visual: Mix do V12 (estrutura de cores e emojis) + padrao PROJECT.md (tema LIGHT, Arial 9pt dados, 10pt headers)
- Bloco FATURAMENTO: 186 colunas (12 meses x 15 sub-colunas: %YTD, META, REALIZADO, %TRI, META, REALIZADO, %MES, META, REALIZADO, DATA PEDIDO, JUSTIFICATIVA S1-S4, JUSTIFICATIVA MENSAL)

### Motor de Inteligencia (3 Camadas)

**Camada 1 -- Ranking de Prioridade (quem atender primeiro):**
- Criterios: Score/Temperatura/Prioridade, Estagio funil, Ciclo medio de compra, Dias sem comprar, Curva ABC, Acesso e-commerce B2B, Momento ouro de recompra
- Status do cliente: Novo, Recorrente, Em Desenvolvimento, Fidelizado, Maduro
- Quantas vezes ja comprou na vida
- Follow-ups pendentes (orcamentos passados, cadastros D+7/D+15/D+30, 1a/2a/3a tentativa WhatsApp/ligacao)

**Camada 2 -- Pipeline vs Meta (vai bater a meta?):**
- Meta mensal / dias restantes = meta diaria do consultor
- Quantos clientes em "momento ouro" (negociacao/orcamento/cadastro/pedido)?
- Ticket medio do consultor e dos clientes
- Conta fecha ou nao?

**Camada 3 -- Alerta de Urgencia (plano B):**
- Se pipeline atual NAO cobre a meta -> ALERTA: "Precisa buscar prospeccao EXTERNA urgente"
- Janela de 7 dias para prospeccao virar pedido
- Calculo: clientes em pipe * ticket medio vs gap de meta restante

**DECISAO CRITICA:** Criar TODAS as 3 camadas na Fase 9, mesmo que o V12 so tenha a Camada 1. A auditoria determinara o que ja existe e o que precisa ser criado do zero.

### Ciclo Automatico de Retroalimentacao

- Consultor preenche resultado (VENDA, ORCAMENTO, etc.) -> CRM gera automaticamente ACAO FUTURA + DATA + O QUE FAZER
- Follow-ups retroalimentam a agenda: resultado de hoje -> follow-up -> vira tarefa do dia X -> consultor executa -> novo resultado
- 50-60 tarefas/dia/consultor FIXO: se pipeline insuficiente, completar com prospeccoes
- Filtro DATA + CONSULTOR na CARTEIRA = AGENDA DO DIA com tarefas priorizadas + ancoras

### Motor de Regras

- Resultados possiveis: VENDA/PEDIDO, ORCAMENTO, CADASTRO, PROSPECCAO, EM ATENDIMENTO, NEGOCIACAO, RECOMPRA, CS, POS-VENDA, RELACIONAMENTO, NUTRICAO, PERDA, NAO ATENDE/NAO RESPONDE
- Cada resultado gera: estagio funil, temperatura, fase, acao futura, data proxima acao
- Auditar V12 aba REGRAS + pasta auditoria + toda documentacao disponivel para mapear regras completas
- Conversa com usuario ja tem inteligencia suficiente para criar regras faltantes

### Visao Diaria e Operacao

**Acesso:**
- CRM completo: SOMENTE Leandro (gestor) tem acesso
- Consultores: recebem apenas aba AGENDA filtrada

**Abas AGENDA (4 individuais):**
- AGENDA LARISSA, AGENDA DAIANE, AGENDA MANU, AGENDA JULIO
- Puxam da CARTEIRA via formula (filtro: nome consultor + data followup)
- Consultor ve: DATA + NOME + CNPJ fixos + ancoras minimizaveis + colunas verdes (resultado selecionavel via dropdown)
- Dropdowns com opcoes pre-definidas das REGRAS

**Ciclo operacional diario:**
1. Manha: Leandro extrai dados Mercos -> cola no DRAFT 1
2. CRM recalcula automaticamente (CARTEIRA + AGENDAs)
3. Leandro copia AGENDA de cada consultor -> planilha separada no Drive (layout fixo)
4. Envia pro consultor via call matinal
5. Dia: consultor preenche resultados
6. Noite: consultor devolve agenda preenchida via call de acompanhamento
7. Leandro cola resultados no DRAFT 2
8. CRM recalcula -> gera agenda do dia seguinte
9. Repete

**Estrategia de seguranca:** Manual primeiro (Leandro controla copy/paste). Automatizar quando consultores estiverem maduros.

### Claude's Discretion

- Definir melhor formato de freeze panes apos auditar V12
- Definir quais abas de suporte (DRAFTs, REGRAS) precisam ser recriadas vs adaptadas
- Definir exatamente quais formulas apontam para onde (DRAFT 1, PROJECAO, LOG, etc.)
- Escolher melhor abordagem para auto_filter vs slicer
- Definir formato visual exato das colunas verdes (preenchimento consultor)
- Definir se Camadas 2 e 3 do motor sao formulas ou calculo auxiliar
- Propor melhor estrutura para alertas de urgencia (conditional formatting, coluna extra, etc.)

</decisions>

<specifics>
## Specific Ideas

- "Cada super grupo tem uma ancora, e cada sub-grupo dentro do grande grupo tambem tem uma ancora, porque as ancoras sao as informacoes importantes para facilitar nossa visualizacao e analise de inteligencia para conferir a agenda dos consultores dos proximos dias"
- "Se ele nao tiver a venda, precisa ter a justificativa que puxa do resultado do atendimento nessa semana -- ou vem uma justificativa, ou um motivo, ou uma venda, um orcamento, um pedido, ou ele esta prospectando ainda, ou em atendimento, ou negociando, ou em cadastro, ou tem pedido, ou esta em recompra CS, ou pos-venda, ou relacionamento, ou nutricao, ou perda"
- "A carteira vai gerar todos esses dados que sao exatas analytics das regras -- se acontecer isso gera isso, se isso gera aquilo, que ranqueia ele. Dai eu pego e filtro so dia 18, vai ter tudo que o CRM inteligencia ranqueou como mais importantes"
- "Se ele so tem 10 clientes no momento ouro e o ticket medio e so de mil reais, com essa carteira saberemos que ele nao vai bater a meta -- nesse momento temos que ter um alerta de urgencia que ele precisa buscar prospeccoes fora urgente"
- "Na deles (consultores), eles vao ter um layout fixo em uma pasta no Drive, aonde eu so colo la a agenda que a carteira gerou"
- Referencia visual: V12 COM_DADOS e o padrao a seguir para estrutura/ancoras/agrupamentos

</specifics>

<deferred>
## Deferred Ideas

- Automatizacao do retorno de dados (consultor preenche -> dados voltam automaticamente ao CRM) -- futuro, quando consultores estiverem maduros
- Automacao de extracao Mercos (hoje manual: Leandro extrai e cola no DRAFT 1) -- possivel automacao futura
- Mais de 60 tarefas/dia por consultor (sistema adaptativo baseado em performance)

</deferred>

---

## Fontes de Dados para Auditoria

| Fonte | Caminho | Conteudo |
|-------|---------|----------|
| V12 COM_DADOS | data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx | Referencia completa: CARTEIRA 263 cols, DRAFTs, AGENDA, REGRAS |
| Pasta auditoria | Desktop/auditoria conversas sobre agenda atendimento draft 2/ | 9 docs forenses (anatomia, blueprint, regras, playbook, logs) |
| PASTA DE APOIO | Desktop/PASTA DE APOIO PROJETO/AUDITORIA/ | Documentacao adicional |
| Downloads | C:/Users/User/Downloads/ | Arquivos recentes relevantes |
| CLAUDE CODE | Desktop/CLAUDE CODE/ | Arquivos principais do projeto |
| Fontes processadas | data/sources/ | SAP, Mercos, Deskrio, Controle Funil ja processados |

### Arquivos de Auditoria (pasta Desktop)

1. ANATOMIA_ATENDIMENTO_VITAO360.docx -- Anatomia do fluxo de atendimento
2. BLUEPRINT_FORENSE_REGRAS_VITAO360.docx -- Blueprint forense das REGRAS
3. EXTRACAO_FORENSE_CRM_VITAO360_17FEV2026.docx -- Extracao forense do CRM
4. INVENTARIO_FORENSE_DRAFT2_VITAO360.html -- Inventario forense do DRAFT 2
5. LOG_AUDITORIA_V12_REBUILD_DEMANDAS.docx -- Log de auditoria rebuild V12
6. LOG_CONVERSA_DASHBOARD_PRODUTIVIDADE.docx -- Conversa sobre dashboard
7. LOG_CONVERSA_EXTRACAO_CONTROLE_FUNIL_JAN2026.md -- Extracao controle funil
8. PLAYBOOK_EXCELENCIA_100_DRAFT_AGENDA_RETROATIVO.docx -- Playbook de excelencia
9. PROMPT_EXTRACAO_DADOS_CRM_VITAO360.md -- Prompt de extracao de dados

---

*Phase: 09-blueprint-v2*
*Context gathered: 2026-02-17*
