# Phase 4: LOG Completo - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrar todas as fontes de dados de interacoes no LOG do CRM + criar dados sinteticos ultra-realistas para completar o historico Jan/2025 a Fev/2026. O LOG e o repositorio historico bruto. DRAFT 2 + AGENDA sao as abas ativas (um recebe atendimentos do dia e alimenta CARTEIRA, outro vai pro consultor). Tudo ja mapeado na documentacao do CRM V12/V13 e no GENOMA COMERCIAL.

**Meta:** Fechar 2025 com 10.634 atendimentos qualificados (conforme PAINEL real) + Jan-Fev 2026.
**Two-Base Architecture:** 100% dos registros do LOG com R$ 0.00 (valores financeiros so em BASE_VENDAS).

</domain>

<decisions>
## Implementation Decisions

### Classificacao 3-tier (criterios JA documentados na auditoria)
- **REAL:** Notas contextuais >15 chars com detalhes especificos. Referencias a valores R$, "FECHADO", boleto, rastreamento, XML, negociacao, reuniao. Nao se enquadra em padrao sintetico.
- **SINTETICO:** 12 padroes de notas genericas ("primeiro contato com prospect", "follow-up apos primeiro contato", "material de marketing enviado", etc.). Sequencias regulares de 8-10 contatos com offsets padronizados. Notas curtas sem contexto especifico.
- **ALUCINACAO:** CNPJ invalido (<14 digitos), nome padrao "CLIENTE + numero", vendedores ficticios (JOAO SILVA, PEDRO OLIVEIRA, etc.). 558 registros JA identificados e separados.
- **558 alucinacoes: Descartar totalmente e recriar dados com qualidade 100/100**
- Visibilidade da classificacao no CRM: Claude decide (coluna visivel filtravel vs metadata interna)

### Estrutura do LOG e DRAFT 2
- **LOG = historico bruto** (todos os dados passados) — repositorio de todos os 14 meses
- **DRAFT 2 = aba ativa** que recebe atendimentos do dia e alimenta CARTEIRA
- **AGENDA = agenda diaria** que vai pro consultor
- Manter estrutura de colunas do V12 para o LOG (42 colunas originais no CONTROLE_FUNIL)
- LOG no Blueprint v2: 26 colunas em 6 grupos (IDENTIFICACAO, CONTEXTO COMERCIAL, CANAL, CLASSIFICACAO, DETALHAMENTO, CONTROLE OPERACIONAL)
- Criar colunas auxiliares para campos extras + metadados de rastreabilidade (ABA_ORIGEM, ROW_ORIGINAL, ORIGEM_DADO, CRITERIO_CLASSIFICACAO, FLAG_ALUCINACAO)
- DRAFT 2 existente (6.775 registros) precisa ser REVALIDADO antes de usar como base
- Resultados de atendimento ja mapeados no CRM V12/V13 (README + regras + GENOMA COMERCIAL)
- Cada resultado gera ACAO FUTURA automatica (tabela de follow-up completa)

### Fontes de Dados Existentes (JA extraidas)
- **CONTROLE_FUNIL (06_LOG_FUNIL.xlsx):** 10.544 registros limpos (apos dedup e remoao de 558 alucinacoes + 589 duplicatas). Zero data loss confirmado (11.691 brutos = 10.544 + 558 + 589)
- **Deskrio:** 5.329 tickets / 77.805 mensagens / 5.425 conversas (tickets nunca fechados corretamente)
- **Mercos atendimentos:** 1.581 registros (consultores registravam quando queriam — dados falhos)
- **DRAFT 2 V12:** 6.775 registros reais (precisa revalidacao)
- **Painel de Atividades REAL 2025:** 77.805 msgs → 5.425 conversas → 10.634 atendimentos → 1.419 orcamentos → 957 vendas

### Volume e Dados Sinteticos
- **Periodo:** Jan/2025 a Fev/2026 (14 meses completos)
- **Meta de volume:** 10.634 atendimentos qualificados em 2025 (conforme PAINEL real) + Jan-Fev 2026
- **Logica de volume do PAINEL REAL:**
  - 957 vendas × 11,1 atendimentos/venda = 10.634 atendimentos
  - Taxa conversao geral: 9,0%
  - 78 msgs por venda, 17 dias de jornada completa
- **Distribuicao mensal REAL do PAINEL (atendimentos qualificados):**
  - JAN:156 FEV:269 MAR:442 ABR:596 MAI:862 JUN:1203 JUL:958 AGO:1244 SET:1185 OUT:1395 NOV:1528 DEZ:796
- **Script automatico:** Gerar todos sinteticos seguindo regras do GENOMA COMERCIAL (sem aprovacao de amostra)
- **Ultra-realista:** Respeitar calendario real (feriados, ferias, ausencias, capacidade reduzida)
- **PADRAO HUMANO OBRIGATORIO:** Variacao realista — alguns clientes 3 contatos, outros 14, outros 1. Nem todos atendem, varios ignoram, varios recusam. Falhas humanas. NADA de padrao robotico serial

### Jornadas Completas (GENOMA COMERCIAL — 6 cenarios)
- **Jornada A — PROSPECT → 1a COMPRA:** 8-10 contatos, 17 dias, 78 msgs. Variacoes: A1 rapido (6 contatos, 10 dias), A2 lento (12-15 contatos, 25-30 dias), A3 com problema (+2-3 suportes)
- **Jornada B — ATIVO → RECOMPRA:** 3-5 contatos, 5-7 dias, 25 msgs. Variacoes: B1 ultra-rapido (3), B2 com objecao (5-6)
- **Jornada C — INATIVO RECENTE → RESGATE:** 5-8 contatos, 12-15 dias, 45 msgs
- **Jornada D — INATIVO ANTIGO → REATIVACAO:** 5-8 contatos, 15-20 dias, 40 msgs
- **Jornada E — NAO VENDA / PERDA:** 4-5 contatos, 10-15 dias. Variacoes: E1 sumiu, E2 recusou, E3 preco, E4 problema, E5 fechou loja
- **Jornada F — NUTRICAO / LONGO PRAZO:** 2-3 contatos por ciclo trimestral
- **Ancora da venda:** Data da venda e imutavel. Reconstruir de tras pra frente com offsets D-7 a D+10

### Motor de Regras (GENOMA COMERCIAL — tabelas completas)
- **13 resultados possiveis:** EM ATENDIMENTO, ORCAMENTO, CADASTRO, VENDA/PEDIDO, FOLLOW UP 7, FOLLOW UP 15, RELACIONAMENTO, CS, SUPORTE, NAO ATENDE, NAO RESPONDE, RECUSOU LIGACAO, PERDA/FECHOU LOJA, NUTRICAO
- **Cada resultado gera:** follow-up (dias), estagio funil, temperatura, fase, acao futura
- **6 tipos de contato validos:** PROSPECCAO NOVOS CLIENTES, ATENDIMENTO CLIENTES ATIVOS, ATENDIMENTO CLIENTES INATIVOS, ENVIO DE MATERIAL MKT, CONTATOS PASSIVO/SUPORTE, POS VENDA/RELACIONAMENTO
- **Canais:** WhatsApp 98.3%, Ligacao 49.7%, Ligacao Atendida 20% das ligacoes (80% nao atendidas)
- **Tipo Acao:** ATIVO (consultor iniciou) vs RECEPTIVO (cliente iniciou)

### Distribuicoes Estatisticas REAIS (para sinteticos realistas)
- **Por dia da semana:** Seg 22%, Ter 21%, Qua 20%, Qui 20%, Sex 17%, Sab/Dom 0% (PROIBIDO)
- **Por horario:** 09-12h = 55% do volume, 12-13:30 = 10%, 13:30-16h = 30%, 16-17h = 5%
- **Capacidade diaria:** 40 atendimentos/consultor (MANHA 22 + TARDE 18)
- **Distribuicao resultados:** EM ATENDIMENTO 40-50%, VENDA 8-12%, ORCAMENTO 10-15%, SUPORTE 10-15%, RELAC/CS 5-8%, CADASTRO 3-5%, FOLLOW UP 3-5%, NAO RESP 5-8%, NAO ATENDE 3-5%, PERDA 1-2%

### 200+ Templates de Notas (GENOMA COMERCIAL)
- Organizados por categoria: pre-venda/prospeccao, follow-up, orcamento/cadastro, venda/fechamento, pos-venda/suporte, CS, problemas reais, inatividade/perda
- GENOMA COMERCIAL tem catalogo completo em secoes 7.1 a 7.6
- Notas devem variar — nao repetir mesma nota mais de 3x

### Regras de Validacao (sequencias obrigatorias e proibidas)
- **OBRIGATORIO:** Toda venda tem ORCAMENTO antes (D-1 a D-3). Novos tem CADASTRO antes. Toda venda gera MATERIAL MKT depois (D+2/3). Nenhum atendimento sabado/domingo. R$ 0,00 sempre. CNPJ 14 digitos. Max 40/dia/consultor.
- **PROIBIDO:** VENDA sem ORCAMENTO antes. CADASTRO pra cliente existente. SUPORTE antes da VENDA (exceto passivo). CS antes da VENDA. MKT sem VENDA. >1 VENDA/dia mesmo CNPJ. FOLLOW UP 7 seguido de FOLLOW UP 7.
- **SEQUENCIAS:** PROSPECT: EM ATEND → [FOLLOW UP] → ORCAMENTO → CADASTRO → VENDA. ATIVO: [EM ATEND] → ORCAMENTO → VENDA → MKT. INATIVO: EM ATEND → [NAO RESP] → [FOLLOW UP] → ORCAMENTO → VENDA.

### Contatos passivos e suporte
- 1-2 por venda (cliente liga pedindo rastreio, reclamando, pedindo NFe/boleto/MKT)
- Novos geram suporte passivo 30% das vezes, Ativos 20%, Inativos 15%
- 25 demandas operacionais documentadas no GENOMA (D01-D25)
- 8 objecoes principais com taxa de conversao documentada

### Equipe 2025 (para sinteticos realistas)
- **Jan-Set/2025:** 3 consultores (Larissa, Manu, Daiane). Helder Brunkow backup/historico (~50/mes)
- **Set-Out/2025:** Julio entra — passa a 4 consultores
- **Manu Ditzel:** SC/PR/RS, 152 clientes, 32.5% receita, ~500 atend/mes, ~30 vendas/mes. Gravida (6o mes), ate 3o mes: 3 faltas/semana
- **Larissa Padilha:** Resto do Brasil, 178 clientes, 28% receita, ~400 atend/mes, ~25 vendas/mes
- **Julio Gadret:** CIA da Saude + Fitland, 86 clientes, 22% receita, ~200 atend/mes*, ~18 vendas/mes (*sub-registrado)
- **Daiane Stavicki:** Redes/Franquias, 73 + 628 prospects, 15% receita, ~300 atend/mes, ~10 vendas/mes
- **Dezembro/2025:** So ate dia 19
- **Janeiro/2026:** Manu+Larissa comecaram dia 05, Daiane+Julio dia 12/01
- **Bug:** Julio Gadret aparece com 2 grafias ("Julio  Gadret" vs "Julio Gadret") — normalizar

### Tratamento de Conflitos
- Quando CONTROLE_FUNIL e Deskrio tem mesmo cliente/data: **dado de melhor qualidade prevalece**
- Se ambos ruins: Claude reescreve com qualidade preenchendo todos campos da agenda
- Multiplos contatos no mesmo dia para o mesmo cliente: **ambos ficam** (registros separados)
- Chave de deduplicacao: DATA (YYYY-MM-DD) + CNPJ (14 digitos, zero-padded) + RESULTADO (uppercase, trimmed)
- Prioridade de abas: LOG > Manu log > Planilha5 > Planilha4
- CONTROLE_FUNIL: 10.544 limpos (10.484 brutos - 558 aluc - 589 dedup), todos de 2025
- Deskrio: 5.329 tickets (extraidos para cruzar dados — nunca fechados corretamente)
- Mercos atendimentos: 1.581 (falhos — consultores registravam quando queriam)

### Julio Gadret
- Entrou Set-Out/2025 — exclusivo de SC (Santa Catarina)
- Prioridade: redes CIA da Saude e Fitland
- Antes dele, Daiane cobria essas redes
- Opera via WhatsApp pessoal — zero registro em sistemas (90% WhatsApp pessoal)
- **Criar historico sintetico completo desde Set/25:** prospeccao, contatos, funil completo
- Dados de vendas reais do Julio existem no SAP/Mercos — usar como ancora
- 1.814 interacoes no CONTROLE_FUNIL (963 + 851 com 2 grafias diferentes)

### Clientes que pararam de comprar
- Minimo 3 ciclos de tentativa antes de perda com motivo documentado
- Motivos de perda: PRECO / PRODUTO NAO GIRA / CONCORRENCIA / FECHANDO LOJA / MUDOU SEGMENTO / PROBLEMA LOGISTICA / PROBLEMA QUALIDADE / OUTRO
- Contadores de falha: >=4 tentativas sem resposta → auto-NUTRICAO, follow-up 90 dias

### Claude's Discretion
- Tratamento dos 558 alucinados (fora do LOG ou marcados com flag)
- Visibilidade da classificacao 3-tier (coluna filtravel ou metadata)
- Granularidade Deskrio (1 registro por conversa vs por mensagem)
- Nivel de detalhe das colunas auxiliares
- Algoritmo de variacao humana para sinteticos (baseado no pseudo-codigo do GENOMA secao 11)

</decisions>

<specifics>
## Specific Ideas

- "Temos que criar um padrao de atendimento ultra realista mesmo com dados sinteticos, a ideia aqui e mostrar nossa excelencia do passado, e criar um padrao ouro pro futuro"
- "Precisamos mostrar um historico de excelencia, para criar um padrao ouro pra seguir de agora em diante"
- "Imitar padroes humanos — vc precisa ser um humano agora, tanto cliente quanto consultor pra imitar os comportamentos"
- "Nada seguindo um padrao de numeros series rotinas tentativas — nao somos robos"
- "Todo cliente que deixou de comprar foi atendido pelo menos 3 vezes seguidas rodando o ciclo"
- "Mesmo sem venda, mostrar que o time esta operando no maximo — sao inumeras tarefas"
- "Todo atendimento obrigatoriamente gera uma tarefa/demanda"
- Contexto de urgencia: Dashboard precisa estar pronto amanha 8h para apresentacao aos CEOs
- Fonte de verdade: toda logica, regras, status, resultados ja mapeados no CRM V12/V13 e documentacao

## Documentos de Referencia Criticos

| Documento | Local | Conteudo |
|-----------|-------|----------|
| GENOMA_COMERCIAL_VITAO360.md | Downloads/ | DNA da operacao: 6 jornadas, motor de regras, 200+ templates de notas, distribuicoes estatisticas, algoritmo de geracao, regras de validacao |
| AUDITORIA_COMPLETA_32_SESSOES.md | PASTA DE APOIO PROJETO/AUDITORIA/ | 82 decisoes (DEC-001 a DEC-082), 13 bugs, 18 pendencias, arquitetura completa |
| LOG_CONVERSA_EXTRACAO_CONTROLE_FUNIL.md | PASTA DE APOIO PROJETO/AUDITORIA/ | Detalhes da extracao dos 10.544 registros, criterios de classificacao, estatisticas completas |
| 06_LOG_FUNIL.xlsx | Output do pipeline ETL | 10.544 registros limpos + 558 alucinacoes + 589 duplicatas (16 abas) |
| Blueprint v2 (HTML) | Pasta de apoio | Especificacao definitiva: 81 colunas, 8 grupos, 10 fixas. VERSAO AUTORITATIVA (DEC-080) |
| Blueprint v3 LOG/AGENDA/DASH (HTML) | Pasta de apoio | Especificacao completa de LOG, AGENDA e DASHBOARDS |

</specifics>

<deferred>
## Deferred Ideas

- **Aba SINALEIRO/SEMAFORO** com filtros por estado, regiao, consultor, cor do semaforo — Phase 5/9
- **Aba PROJECAO/META por cliente** (refinar a ja feita na Phase 1) — Phase 8
- **Agendas individuais** por consultor (agenda_julio, agenda_daiane, etc.) — Phase 9/10
- **Unificacao AGENDA + DRAFT 2** como "santo graal" — Phase 9
- **Logica de retroalimentacao CARTEIRA <-> DRAFT 2** — Phase 9
- **Inteligencia de capacidade de atendimento** (quantos clientes ouro, quantas reativacoes, quantas prospeccoes para bater meta) — Phase 8/9
- **Dashboard com ligacoes, atendimentos, tarefas, motivos de Jan/Fev** — Phase 5
- **Redistribuicao da Manu** (maternidade, 32.5% da receita) — Phase 8/9
- **VBA/Macro PROCESSAR** (DRAFT → LOG automatico) — Phase 10

</deferred>

---

*Phase: 04-log-completo*
*Context gathered: 2026-02-17*
*Enriched with: AUDITORIA_COMPLETA_32_SESSOES + GENOMA_COMERCIAL + LOG_CONVERSA_CONTROLE_FUNIL*
