# Phase 4: LOG Completo - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrar todas as fontes de dados de interacoes (CONTROLE_FUNIL, Deskrio, historicos) no LOG do CRM + criar dados sinteticos ultra-realistas para completar o historico de 2025 e inicio de 2026. O LOG e o repositorio historico bruto. DRAFT 2 + AGENDA sao as abas ativas (um recebe atendimentos do dia e alimenta CARTEIRA, outro vai pro consultor). Tudo ja mapeado na documentacao do CRM V12/V13.

**Meta:** Fechar 2025 com 10.000+ atendimentos (igual PAINEL) + Jan-Fev 2026.
**Two-Base Architecture:** 100% dos registros do LOG com R$ 0.00 (valores financeiros so na VENDA).

</domain>

<decisions>
## Implementation Decisions

### Classificacao 3-tier
- **REAL:** Registro com resultado documentado (fonte confiavel + data + CNPJ + resultado do contato)
- **SINTETICO:** Dado importado/estimado — criado por scripts para preencher gaps, seguindo padrao ouro de atendimento
- **ALUCINACAO:** 558 registros ja identificados — Claude decide melhor abordagem (fora do LOG ou marcados)
- Visibilidade da classificacao no CRM: Claude decide (coluna visivel filtravel vs metadata interna)

### Estrutura do LOG e DRAFT 2
- **LOG = historico bruto** (todos os dados passados)
- **DRAFT 2 = aba ativa** que recebe atendimentos do dia e alimenta CARTEIRA
- **AGENDA = agenda diaria** que vai pro consultor
- Manter estrutura de colunas do V12 para o LOG
- Criar colunas auxiliares para campos extras que nao cabem na estrutura V12 (CONTROLE_FUNIL tem 31 cols)
- DRAFT 2 existente (6.775 registros) precisa ser REVALIDADO antes de usar como base
- Resultados de atendimento ja mapeados no CRM V12/V13 (README + regras) — cada resultado gera acao futura automatica
- Estrutura de colunas da CARTEIRA (azuis=agenda, verdes=consultor preenche, brancas=automaticas) ja mapeia tracking, ranking, temperatura, funil

### Volume e Dados Sinteticos
- **Periodo:** Jan/2025 a Fev/2026 (14 meses completos)
- **Logica de volume:** ~900 vendas/2025 x 6-8 contatos por venda = ~5.400-7.200 atendimentos de venda + ligacoes pre/pos venda + suporte + prospeccao para completar 10.284+
- **Script automatico:** Gerar todos sinteticos de uma vez seguindo regras do CRM (sem aprovacao de amostra)
- **Ultra-realista:** Respeitar calendario real (feriados, ferias, ausencias, capacidade reduzida de cada consultor)
- **PADRAO HUMANO OBRIGATORIO:** Variacao realista — alguns clientes 3 contatos, outros 14, outros 1. Nem todos atendem, varios ignoram, varios recusam. Falhas humanas. NADA de padrao robotico serial
- **Ancora da venda:** Data da venda e imutavel. Pre-venda 7-10 dias antes. Pos-venda: D+3/4 conferencia, D+15 pos-venda, D+30 CS
- **Contatos passivos:** 1-2 por venda (cliente liga pedindo rastreio, reclamando, pedindo NFe/boleto/MKT)
- **Etapas do funil:** Prospeccao -> 1o contato -> 2o contato -> Ligacao -> Orcamento -> Cadastro -> Pedido -> Pos-venda D+15 -> CS D+30 -> Relacionamento
- **Tarefas por atendimento:** ASNA, link pagamento, rastreio, MKT, segunda via boleto/NFe, CRM, follow-up
- **Clientes que pararam de comprar:** Minimo 3 ciclos de tentativa antes de perda com motivo documentado

### Equipe 2025 (para sinteticos realistas)
- **Jan-Set/2025:** 3 consultores (Larissa, Manu, Daiane)
- **Set-Out/2025:** Julio entra — passa a 4 consultores
- **Manu:** Gravida (6o mes). Ate 3o mes: 3 faltas/semana. Depois acalmou
- **Dezembro/2025:** So ate dia 19
- **Janeiro/2026:** Manu+Larissa comecaram dia 05, Daiane+Julio dia 12/01
- **Capacidade:** ~40 atendimentos/dia por consultor

### Tratamento de Conflitos
- Quando CONTROLE_FUNIL e Deskrio tem mesmo cliente/data: **dado de melhor qualidade prevalece**
- Se ambos ruins: Claude reescreve com qualidade preenchendo todos campos da agenda
- Multiplos contatos no mesmo dia para o mesmo cliente: **ambos ficam** (registros separados — chave inclui tipo/horario)
- CONTROLE_FUNIL: 10.484 registros, todos de 2025
- Deskrio: 5.329 tickets de atendimento (conversas extraidas para cruzar dados/padroes — tickets nunca fechados corretamente pelos consultores)
- Mercos atendimentos: Falhos — consultores registravam quando queriam
- **558 alucinacoes: Descartar totalmente e recriar dados com qualidade 100/100**

### Julio Gadret
- Entrou Set-Out/2025 — exclusivo de SC (Santa Catarina)
- Prioridade: redes CIA da Saude e Fitland
- Antes dele, Daiane cobria essas redes
- Opera via WhatsApp pessoal — zero registro em sistemas
- **Criar historico sintetico completo desde Set/25:** prospeccao, contatos, funil completo
- Dados de vendas reais do Julio existem no SAP/Mercos — usar como ancora

### Claude's Discretion
- Tratamento dos 558 alucinados (fora do LOG ou marcados com flag)
- Visibilidade da classificacao 3-tier (coluna filtravel ou metadata)
- Granularidade Deskrio (1 registro por conversa vs por mensagem)
- Nivel de detalhe das colunas auxiliares
- Algoritmo de variacao humana para sinteticos

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

</deferred>

---

*Phase: 04-log-completo*
*Context gathered: 2026-02-17*
