# Phase 4: LOG Completo - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning
**Enriched:** ~95 documentos de 47+ pastas na Area de Trabalho + Downloads + AUDITORIA

<domain>
## Phase Boundary

Integrar todas as fontes de dados de interacoes no LOG do CRM + criar dados sinteticos ultra-realistas para completar o historico Jan/2025 a Fev/2026. O LOG e o repositorio historico bruto. DRAFT 2 + AGENDA sao as abas ativas (um recebe atendimentos do dia e alimenta CARTEIRA, outro vai pro consultor). Tudo ja mapeado na documentacao do CRM V12/V13 e no GENOMA COMERCIAL.

**Meta:** Fechar 2025 com 10.634 atendimentos qualificados (conforme PAINEL real) + Jan-Fev 2026.
**Two-Base Architecture:** 100% dos registros do LOG com R$ 0.00 (valores financeiros so em BASE_VENDAS).

</domain>

<decisions>
## Implementation Decisions

---

### 10 PRINCIPIOS INVIOLAVEIS (REGRAS_INTELIGENCIA_CRM_VITAO_v2)

- **P1** ZERO DADOS FABRICADOS — toda info de fonte real. IA nunca inventa dados. Campo sem dado = vazio.
- **P2** TWO-BASE ARCHITECTURE — valores financeiros NUNCA no LOG. Separacao absoluta BASE_VENDAS vs LOG. CNPJ como chave.
- **P3** CARTEIRA IMUTAVEL — layout base (46 cols MERCOS) nao pode ser alterado. Extensoes APOS as 46.
- **P4** LOG APPEND-ONLY — so recebe novas linhas. Nunca editar, nunca deletar.
- **P5** CONSULTOR NUNCA TOCA O LOG — preenche AGENDA → devolve → Leandro cola no DRAFT 2 → validacao → LOG.
- **P6** CNPJ COMO CHAVE PRIMARIA — 14 digitos sem pontuacao (ex: 32387943000105). Match secundario: RAZAO SOCIAL.
- **P7** PARA CADA ACAO UMA REACAO — RESULTADO determina automaticamente: Estagio, Fase, Tipo Contato, Follow-up, Acao Futura, Temperatura, Tentativa.
- **P8** VITAO SEMPRE SEM ACENTO — em todo documento, planilha, HTML, codigo.
- **P9** LIGHT THEME + HTML RESPONSIVO — nunca dark mode.
- **P10** 100% RASTREABILIDADE — cada dado tem rastreabilidade para fonte original.

---

### Classificacao 3-tier (criterios JA documentados na auditoria)

- **REAL:** Notas contextuais >15 chars com detalhes especificos. Referencias a valores R$, "FECHADO", boleto, rastreamento, XML, negociacao, reuniao. Nao se enquadra em padrao sintetico.
- **SINTETICO:** 12 padroes de notas genericas ("primeiro contato com prospect", "follow-up apos primeiro contato", "material de marketing enviado", etc.). Sequencias regulares de 8-10 contatos com offsets padronizados. Notas curtas sem contexto especifico.
- **ALUCINACAO:** CNPJ invalido (<14 digitos), nome padrao "CLIENTE + numero", vendedores ficticios (JOAO SILVA, PEDRO OLIVEIRA, etc.). 558 registros JA identificados e separados.
- **558 alucinacoes: Descartar totalmente e recriar dados com qualidade 100/100**
- Visibilidade da classificacao no CRM: Claude decide (coluna visivel filtravel vs metadata interna)

---

### Pipeline Completo: AGENDA → DRAFT 2 → LOG (SKILL_LOG_DRAFT_PIPELINE)

```
CARTEIRA (cerebro, ~257 cols) → gera → AGENDA (arquivo .xlsx separado por consultor)
                                           ↓
                              Consultor PREENCHE resultado (10 colunas editaveis)
                                           ↓
                              Resultado vai para → DRAFT 2 (quarentena, 24-27 cols)
                                                      ↓
                              Validacao automatica (VALIDO="OK" + MIGRADO=vazio)
                                                      ↓
                              Linhas aprovadas → LOG (oficial, append-only, 20 cols)
                                                      ↓
                              LOG retroalimenta → CARTEIRA (funil + inteligencia)
                                                      ↓
                              SCORE recalcula → nova AGENDA com prioridades frescas
```

**Ciclo Diario:**
- MANHA (Leandro): Extrai Mercos → atualiza DRAFT 1 → formulas atualizam CARTEIRA → SCORE calcula ranking → filtra por consultor → gera AGENDA (max 40/consultor) → envia WhatsApp
- DIA (Consultores): Recebe .xlsx → trabalha clientes → preenche dropdowns → devolve planilha
- FIM DIA (Leandro): Cola no DRAFT 2 → validacao automatica → motor de regras calcula → linhas OK entram no LOG → marca MIGRADO="SIM"
- PROXIMO DIA: CARTEIRA atualizada → novo SCORE → nova AGENDA

---

### Estrutura EXATA das Abas (MULTIPLAS FONTES — resolucao de conflitos)

**NOTA CRITICA:** Existem MULTIPLAS versoes da spec com numeros diferentes de colunas:
- DOC_DEFINITIVA_AGENDA_DRAFT2.md: DRAFT 2 = 24 cols, AGENDA = 24 cols
- PROMPT_POPULAR_DRAFT2_ATENDIMENTOS.md: DRAFT 2 = 31 cols (22 dados + 9 formula)
- SKILL_LOG_DRAFT_PIPELINE.md: LOG = 20 cols, DRAFT 2 = 27 cols (3 zonas)
- REGRAS_INTELIGENCIA_CRM_VITAO_v2.md: DRAFT 2 = 24 cols

**Resolucao:** A versao MAIS RECENTE e autoritativa e a DOC_DEFINITIVA (11/02/2026) para o fluxo operacional. A versao 31 cols (V11 LIMPO) inclui colunas extras de tracking/formula. Usar DOC_DEFINITIVA como base, estender conforme necessario.

#### DRAFT 2 — 24 Colunas Operacionais (DOC_DEFINITIVA)

```
Col  1: DATA                Data        Data do atendimento
Col  2: CONSULTOR           Dropdown    4 consultores
Col  3: NOME FANTASIA       Texto       Nome do cliente
Col  4: CNPJ                Texto       Chave primaria (14 digitos)
Col  5: UF                  Texto       Estado (2 letras)
Col  6: REDE / REGIONAL     Texto       Rede ou "DEMAIS CLIENTES"
Col  7: SITUACAO            Dropdown    ATIVO/EM RISCO/INAT.REC/INAT.ANT/NOVO/PROSPECT
Col  8: DIAS SEM COMPRA     Numero      Calculado
Col  9: ESTAGIO FUNIL       Texto       FUNIL / NAO VENDA / RELAC.
Col 10: TIPO CLIENTE        Texto       Maturidade
Col 11: FASE                Texto       8 valores do motor
Col 12: SINALEIRO           Emoji       🟢 / 🟡 / 🔴
Col 13: TENTATIVA           Texto       T1/T2/T3/T4
Col 14: WHATSAPP            Dropdown    SIM/NAO
Col 15: LIGACAO             Dropdown    SIM/NAO
Col 16: LIGACAO ATENDIDA    Dropdown    SIM/NAO/N/A
Col 17: TIPO DO CONTATO     Dropdown    7 opcoes
Col 18: RESULTADO           Dropdown    12 opcoes
Col 19: MOTIVO              Dropdown    10 opcoes
Col 20: FOLLOW-UP           Data/Texto  Proxximo contato ou "SEM"
Col 21: ACAO FUTURA         Texto       Classificacao estrategica
Col 22: ACAO DETALHADA      Texto       Descricao livre
Col 23: MERCOS ATUALIZADO   Dropdown    SIM/NAO
Col 24: NOTA DO DIA         Texto       Observacao livre
```

#### AGENDA — 24 Colunas (arquivo .xlsx separado)

```
Cols 1-13:  CONTEXTO (automatico, read-only — vem da CARTEIRA via XLOOKUP)
            NOME FANTASIA, CNPJ, UF, REDE/REGIONAL, SITUACAO, DIAS SEM COMPRA,
            ESTAGIO FUNIL, TIPO CLIENTE, FASE, TEMPERATURA, SINALEIRO, PROX.ACAO, TENTATIVA
Cols 14-24: RESULTADO (consultor PREENCHE nos dropdowns)
            WHATSAPP, LIGACAO, LIGACAO ATENDIDA, TIPO DO CONTATO, RESULTADO,
            MOTIVO, FOLLOW-UP, ACAO FUTURA, ACAO DETALHADA, MERCOS ATUALIZADO, NOTA DO DIA
```

**DIFERENCA CRITICA ACAO FUTURA:**
- AGENDA usa acoes OPERACIONAIS: LIGAR, WHATSAPP, ENVIAR ORCAMENTO, ENVIAR CATALOGO, REAGENDAR, VISITAR, AGUARDAR RETORNO, NENHUMA
- DRAFT 2 usa classificacoes ESTRATEGICAS: CS, NUTRICAO, PROSPECCAO, POS-VENDA, REATIVACAO, RECOMPRA, SALVAMENTO

#### LOG — 20 Colunas (SKILL_LOG_DRAFT_PIPELINE)

```
BLOCO 1 IDENTIFICACAO (A-G): DATA, CONSULTOR, NOME FANTASIA(formula), CNPJ, UF(formula), REDE(formula), SITUACAO(formula)
BLOCO 2 CONTATO (H-K): WHATSAPP, LIGACAO, LIGACAO ATENDIDA, TIPO ACAO
BLOCO 3 CLASSIFICACAO (L-N): TIPO DO CONTATO, RESULTADO, MOTIVO
BLOCO 4 ACAO FUTURA (O-P): FOLLOW-UP(formula), ACAO(formula)
BLOCO 5 CONTROLE (Q-T): MERCOS ATUALIZADO, FASE(formula), TENTATIVA(formula), NOTA DO DIA
```

---

### Mapeamento AGENDA → DRAFT 2 (DOC_DEFINITIVA secao 8)

- AGENDA cols 1-13 → DRAFT 2 cols 3-13 (contexto do cliente)
- AGENDA cols 14-24 → DRAFT 2 cols 14-24 (resultado do consultor)
- DRAFT 2 adiciona: Col 1 (DATA) e Col 2 (CONSULTOR) — nao existem na AGENDA
- AGENDA tem TEMPERATURA e PROX.ACAO que NAO vao pro DRAFT 2

---

### Motor de Regras — RESULTADO → Follow-up + Grupo (DOC_DEFINITIVA secao 3)

```
RESULTADO              FOLLOW-UP        GRUPO
EM ATENDIMENTO         +2 dias uteis    FUNIL
ORCAMENTO              +1 dia util      FUNIL
CADASTRO               +2 dias uteis    FUNIL
VENDA / PEDIDO         +45 dias         FUNIL
RELACIONAMENTO         +7 dias uteis    RELAC.
FOLLOW UP 7            +7 dias uteis    RELAC.
FOLLOW UP 15           +15 dias         RELAC.
SUPORTE                0 (sem)          RELAC.
NAO ATENDE             +1 dia util      NAO VENDA
NAO RESPONDE           +1 dia util      NAO VENDA
RECUSOU LIGACAO        +2 dias uteis    NAO VENDA
PERDA / FECHOU LOJA    0 (sem)          NAO VENDA
```

### TIPO DO CONTATO — Logica de derivacao (DOC_DEFINITIVA secao 4)

```
RESULTADO = VENDA/PEDIDO, SUPORTE, RELACIONAMENTO → POS-VENDA/RELACIONAMENTO
RESULTADO = FOLLOW UP 7, FOLLOW UP 15             → FOLLOW UP
RESULTADO = ORCAMENTO, EM ATENDIMENTO             → NEGOCIACAO
RESULTADO = CADASTRO                               → PROSPECCAO
RESULTADO = PERDA/FECHOU LOJA                      → PERDA/NUTRICAO
RESULTADO = NAO ATENDE/NAO RESPONDE/RECUSOU LIG   → Depende SITUACAO:
   ATIVO/EM RISCO    → ATEND. CLIENTES ATIVOS
   INAT.REC/INAT.ANT → ATEND. CLIENTES INATIVOS
   PROSPECT          → PROSPECCAO
```

**ATENCAO:** Na pratica, consultor tem LIBERDADE para escolher TIPO DO CONTATO. Tabela e orientacao, nao regra rigida.

### MOTIVO — 10 opcoes (quando NAO houve venda)

```
1. AINDA TEM ESTOQUE
2. PRODUTO NAO VENDEU / SEM GIRO    ← se 35%+ → alerta diretoria
3. LOJA ANEXO/PROXIMO - SM
4. SO QUER COMPRAR GRANEL
5. PROBLEMA LOGISTICO / ENTREGA
6. PROBLEMA FINANCEIRO / CREDITO
7. PROPRIETARIO / INDISPONIVEL
8. FECHANDO / FECHOU LOJA
9. SEM INTERESSE NO MOMENTO
10. PRIMEIRO CONTATO / SEM RESPOSTA
```

---

### DADOS REAIS DE VENDAS 2025 (CORRECAO_ALUCINACOES — dados verificados)

**Faturamento Total 2025:** R$ 1.801.623,07 (866 vendas, ticket medio R$ 2.080,40)

**Por Vendedor:**

| Vendedor | Faturamento | Vendas | Ticket Medio | % Total |
|----------|-------------|--------|-------------|---------|
| MANU DITZEL | R$ 585.936 | 290 | R$ 2.020 | 32.5% |
| LARISSA PADILHA | R$ 425.824 | 234 | R$ 1.819 | 23.6% |
| HELDER BRUNKOW | R$ 350.007 | 140 | R$ 2.500 | 19.4% |
| CENTRAL - DAIANE | R$ 247.188 | 87 | R$ 2.841 | 13.7% |
| JULIO GADRET | R$ 183.248 | 105 | R$ 1.745 | 10.2% |
| LORRANY | R$ 6.374 | 8 | R$ 796 | 0.4% |
| LEANDRO GARCIA | R$ 1.650 | 1 | — | 0.1% |

**Vendas Mes a Mes 2025:**

| Mes | Faturamento | Vendas | Ticket | Obs |
|-----|-------------|--------|--------|-----|
| Fev | R$ 2.907 | 1 | R$ 2.907 | Inicio operacao |
| Mar | R$ 33.104 | 17 | R$ 1.947 | Ramp-up |
| Abr | R$ 130.803 | 53 | R$ 2.468 | Aceleracao |
| Mai | R$ 170.003 | 78 | R$ 2.179 | Crescimento |
| Jun | R$ 240.507 | 111 | R$ 2.166 | Pico vendas |
| Jul | R$ 162.483 | 84 | R$ 1.934 | Queda |
| Ago | R$ 210.554 | 113 | R$ 1.863 | Recuperacao |
| Set | R$ 208.774 | 104 | R$ 2.007 | Estavel |
| Out | R$ 312.149 | 123 | R$ 2.537 | PICO FATURAMENTO |
| Nov | R$ 254.853 | 133 | R$ 1.916 | Pico quantidade (BF) |
| Dez | R$ 75.481 | 49 | R$ 1.540 | So ate 15/12 |

**Por Rede:** 81% DEMAIS CLIENTES, Fit Land 8.6%, Vida Leve 2.4%, Cia Saude 2.0%, Bio Mundo 1.8%

**Base de Clientes:** 477 total (128 ATIVO 26.8%, 78 INAT.REC 16.3%, 271 INAT.ANT 56.8%)

**Atendimentos Mercos:** 3.987 registros (16/Jan - 15/Dez). Media 12/dia. 4.6 atend/venda.

---

### Fontes de Dados Existentes (JA extraidas)

- **CONTROLE_FUNIL (06_LOG_FUNIL.xlsx):** 10.544 registros limpos (apos dedup e remocao de 558 alucinacoes + 589 duplicatas). Zero data loss. Todos de 2025.
- **Deskrio:** 5.329 tickets / 77.805 mensagens / 5.425 conversas (tickets nunca fechados)
- **Mercos atendimentos:** 3.987 registros (consultores registravam quando queriam — dados falhos)
- **DRAFT 2 V12:** 6.775 registros reais (precisa revalidacao). 440 do Feb/2026 ja populados.
- **DRAFT 2 V11 LIMPO:** Removidos 441 registros sinteticos.
- **Painel de Atividades REAL 2025:** 77.805 msgs → 5.425 conversas → 10.634 atendimentos → 1.419 orcamentos → 957 vendas
- **SAP Vendas:** 866 vendas confirmadas (Fev-Dez/2025), R$ 1.801.623
- **E-commerce B2B:** 762 registros, 481 clientes unicos, 2.769 acessos

---

### Volume e Dados Sinteticos

- **Periodo:** Jan/2025 a Fev/2026 (14 meses completos)
- **Meta de volume:** 10.634 atendimentos qualificados em 2025 (conforme PAINEL real) + Jan-Fev 2026
- **Logica de volume:**
  - 957 vendas × 11,1 atendimentos/venda = 10.634 atendimentos
  - Taxa conversao geral: 9,0%
  - 78 msgs por venda, 17 dias de jornada completa
- **Distribuicao mensal REAL (atendimentos qualificados):**
  - JAN:156 FEV:269 MAR:442 ABR:596 MAI:862 JUN:1203 JUL:958 AGO:1244 SET:1185 OUT:1395 NOV:1528 DEZ:796
- **ANCORA:** Usar vendas SAP REAIS (866 vendas com datas e valores) como ancora. Reconstruir funil de tras pra frente (D-7 a D+10 da venda).
- **Script automatico:** Gerar todos sinteticos seguindo regras do GENOMA COMERCIAL
- **Ultra-realista:** Respeitar calendario real (feriados, ferias, ausencias, capacidade reduzida)
- **PADRAO HUMANO OBRIGATORIO:** Variacao realista — alguns clientes 3 contatos, outros 14, outros 1. NADA de padrao robotico serial.

---

### Jornadas Completas (GENOMA COMERCIAL — 6 cenarios)

- **Jornada A — PROSPECT → 1a COMPRA:** 8-10 contatos, 17 dias, 78 msgs. Variacoes: A1 rapido (6 contatos, 10 dias), A2 lento (12-15 contatos, 25-30 dias), A3 com problema (+2-3 suportes)
- **Jornada B — ATIVO → RECOMPRA:** 3-5 contatos, 5-7 dias, 25 msgs. Variacoes: B1 ultra-rapido (3), B2 com objecao (5-6)
- **Jornada C — INATIVO RECENTE → RESGATE:** 5-8 contatos, 12-15 dias, 45 msgs
- **Jornada D — INATIVO ANTIGO → REATIVACAO:** 5-8 contatos, 15-20 dias, 40 msgs
- **Jornada E — NAO VENDA / PERDA:** 4-5 contatos, 10-15 dias. Variacoes: E1 sumiu, E2 recusou, E3 preco, E4 problema, E5 fechou loja
- **Jornada F — NUTRICAO / LONGO PRAZO:** 2-3 contatos por ciclo trimestral

---

### Motor de Regras Completo (GENOMA COMERCIAL)

- **13 resultados possiveis:** EM ATENDIMENTO, ORCAMENTO, CADASTRO, VENDA/PEDIDO, FOLLOW UP 7, FOLLOW UP 15, RELACIONAMENTO, CS, SUPORTE, NAO ATENDE, NAO RESPONDE, RECUSOU LIGACAO, PERDA/FECHOU LOJA, NUTRICAO
- **Cada resultado gera automaticamente:** follow-up (dias), estagio funil, temperatura, fase, acao futura
- **6 tipos de contato validos:** PROSPECCAO NOVOS CLIENTES, ATENDIMENTO CLIENTES ATIVOS, ATENDIMENTO CLIENTES INATIVOS, ENVIO DE MATERIAL MKT, CONTATOS PASSIVO/SUPORTE, POS VENDA/RELACIONAMENTO
- **Canais:** WhatsApp 98.3%, Ligacao 49.7%, Ligacao Atendida 20% das ligacoes (80% nao atendidas)
- **Tipo Acao:** ATIVO (consultor iniciou) vs RECEPTIVO (cliente iniciou)

---

### Distribuicoes Estatisticas REAIS (para sinteticos realistas)

- **Por dia da semana:** Seg 22%, Ter 21%, Qua 20%, Qui 20%, Sex 17%, Sab/Dom 0% (PROIBIDO)
- **Por horario:** 09-12h = 55% do volume, 12-13:30 = 10%, 13:30-16h = 30%, 16-17h = 5%
- **Capacidade diaria:** 40 atendimentos/consultor (MANHA 22 + TARDE 18)
- **Distribuicao resultados:** EM ATENDIMENTO 40-50%, VENDA 8-12%, ORCAMENTO 10-15%, SUPORTE 10-15%, RELAC/CS 5-8%, CADASTRO 3-5%, FOLLOW UP 3-5%, NAO RESP 5-8%, NAO ATENDE 3-5%, PERDA 1-2%

---

### 200+ Templates de Notas (GENOMA COMERCIAL)

- Organizados por categoria: pre-venda/prospeccao, follow-up, orcamento/cadastro, venda/fechamento, pos-venda/suporte, CS, problemas reais, inatividade/perda
- GENOMA COMERCIAL tem catalogo completo em secoes 7.1 a 7.6
- Notas devem variar — nao repetir mesma nota mais de 3x

---

### Regras de Validacao (sequencias obrigatorias e proibidas)

- **OBRIGATORIO:** Toda venda tem ORCAMENTO antes (D-1 a D-3). Novos tem CADASTRO antes. Toda venda gera MATERIAL MKT depois (D+2/3). Nenhum atendimento sabado/domingo. R$ 0,00 sempre. CNPJ 14 digitos. Max 40/dia/consultor.
- **PROIBIDO:** VENDA sem ORCAMENTO antes. CADASTRO pra cliente existente. SUPORTE antes da VENDA (exceto passivo). CS antes da VENDA. MKT sem VENDA. >1 VENDA/dia mesmo CNPJ. FOLLOW UP 7 seguido de FOLLOW UP 7.
- **SEQUENCIAS:** PROSPECT: EM ATEND → [FOLLOW UP] → ORCAMENTO → CADASTRO → VENDA. ATIVO: [EM ATEND] → ORCAMENTO → VENDA → MKT. INATIVO: EM ATEND → [NAO RESP] → [FOLLOW UP] → ORCAMENTO → VENDA.

---

### Contatos passivos e suporte

- 1-2 por venda (cliente liga pedindo rastreio, reclamando, pedindo NFe/boleto/MKT)
- Novos geram suporte passivo 30% das vezes, Ativos 20%, Inativos 15%
- 25 demandas operacionais documentadas no GENOMA (D01-D25)
- 8 objecoes principais com taxa de conversao documentada

---

### Equipe 2025 — Dados REAIS verificados (CORRECAO_ALUCINACOES + REGRAS_INTELIGENCIA)

**Consultores e Territorios:**
```
MANU DITZEL      | SC, PR, RS      | Interna | Clientes SEM rede em SC/PR/RS
LARISSA PADILHA  | Resto do Brasil | Interna | Clientes SEM rede fora SC/PR/RS
JULIO GADRET     | Brasil todo     | RCA Ext | EXCLUSIVO: Cia Saude + Fitland
CENTRAL - DAIANE | Brasil todo     | Key Acc | TODAS redes EXCETO Cia Saude/Fitland
```

**Regra de Atribuicao (PRIORIDADE):**
```
1o: CNPJ pertence a CIA SAUDE ou FITLAND?    → JULIO GADRET
2o: CNPJ pertence a outra REDE identificada? → CENTRAL - DAIANE
3o: CNPJ esta em SC/PR/RS sem rede?          → MANU DITZEL
4o: Todos os demais                           → LARISSA PADILHA
```

**Redes Daiane:** DIVINA TERRA, BIOMUNDO, MUNDO VERDE, TUDO EM GRAOS, VIDA LEVE, BIO MUNDO, ARMAZEM, NATURVIDA, LIGEIRINHO, TRIP, ESMERALDA

**Timeline:**
- Jan-Ago/2025: 3 consultoras (Manu, Larissa, Daiane) + Helder Brunkow (backup)
- Ago/2025: Helder SAI — 140 vendas ate la, ticket alto R$ 2.500
- Set-Out/2025: Julio entra — passa a 4 consultores
- Dez/2025: So ate dia 19
- Jan/2026: Manu+Larissa comecaram dia 05, Daiane+Julio dia 12/01
- Manu Ditzel: gravida (6o mes), ate 3o mes: 3 faltas/semana

**Performance REAL por vendedor (SAP 2025):**
- Manu: 290 vendas (33.5%), R$ 585k, ~500 atend/mes
- Larissa: 234 vendas (27%), R$ 425k, ~400 atend/mes
- Julio: 105 vendas (12.1%), R$ 183k, ~200 atend/mes (sub-registrado, 90% WhatsApp pessoal)
- Daiane: 87 vendas (10%), R$ 247k, ~300 atend/mes (menor volume, maior ticket R$ 2.841)
- Lorrany: 8 vendas (marginal)

**Bug:** Julio Gadret aparece com 2 grafias ("Julio  Gadret" vs "Julio Gadret") — normalizar

---

### Tratamento de Conflitos

- Quando CONTROLE_FUNIL e Deskrio tem mesmo cliente/data: **dado de melhor qualidade prevalece**
- Se ambos ruins: Claude reescreve com qualidade preenchendo todos campos
- Multiplos contatos no mesmo dia para o mesmo cliente: **ambos ficam** (registros separados)
- Chave de deduplicacao: DATA (YYYY-MM-DD) + CNPJ (14 digitos, zero-padded) + RESULTADO (uppercase, trimmed)
- Prioridade de abas: LOG > Manu log > Planilha5 > Planilha4
- CONTROLE_FUNIL: 10.544 limpos, todos de 2025
- Deskrio: 5.329 tickets (extraidos para cruzar — nunca fechados)
- Mercos atendimentos: 3.987 (falhos — consultores registravam quando queriam)

---

### Julio Gadret — Detalhes Completos

- Entrou Set-Out/2025 — exclusivo de SC (Santa Catarina)
- Prioridade: redes CIA da Saude e Fitland
- Antes dele, Daiane cobria essas redes
- Opera via WhatsApp pessoal — zero registro em sistemas (90% WhatsApp pessoal)
- 105 vendas confirmadas no SAP (R$ 183.248, ticket medio R$ 1.745)
- 1.814 interacoes no CONTROLE_FUNIL (963 + 851 com 2 grafias diferentes)
- **Criar historico sintetico completo desde Set/25:** prospeccao, contatos, funil

---

### Logica de Selecao de Clientes para AGENDA (SKILL_AGENDA_GENERATOR)

**Prioridade 1:** Follow-ups do dia (obrigatorios) — CARTEIRA onde PROX.FOLLOW-UP <= HOJE()
**Prioridade 2:** Clientes em risco sem follow-up — SITUACAO in {EM RISCO, INAT.REC} e sem agenda
**Prioridade 3:** Prospects agendados
**Completar:** Se < 40, adicionar clientes ATIVOS sem contato recente
**Blocos:** MANHA (9-12h) = carteira ativa + inativos, TARDE (13-17h) = prospeccao

---

### Clientes que pararam de comprar

- Minimo 3 ciclos de tentativa antes de perda com motivo documentado
- Motivos: PRECO / PRODUTO NAO GIRA / CONCORRENCIA / FECHANDO LOJA / MUDOU SEGMENTO / PROBLEMA LOGISTICA / PROBLEMA QUALIDADE / OUTRO
- Contadores de falha: >=4 tentativas sem resposta → auto-NUTRICAO, follow-up 90 dias

---

### DRAFT 2 — Dados REAIS Preenchidos Fev/2026 (440 registros)

**Distribuicao real para calibrar sinteticos:**
- CONSULTOR: Manu 30.2%, Larissa 25.0%, Daiane 25.2%, Julio 19.5%
- REDE: DEMAIS CLIENTES 35.2%, MUNDO VERDE 14.1%, CIA DA SAUDE 9.5%, DIVINA TERRA 9.5%, VIDA LEVE 9.1%, FIT LAND 8.0%, BIOMUNDO 7.7%, TUDO EM GRAOS 6.8%
- SITUACAO: ATIVO 34.3%, INAT.ANT 18.6%, EM RISCO 15.0%, NOVO 12.5%, INAT.REC 11.8%, PROSPECT 7.7%
- ESTAGIO FUNIL: RELAC. 38.2%, FUNIL 37.5%, NAO VENDA 24.3%
- FASE: RECUPERACAO 21.1%, PROSPECCAO 16.1%, SALVAMENTO 15.7%, CS 13.2%, RECOMPRA 10.7%, EM ATENDIMENTO 10.7%, POS-VENDA 9.3%, NUTRICAO 3.2%
- SINALEIRO: 🟢 43.0%, 🟡 33.6%, 🔴 23.4%

---

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
- Contexto de urgencia: Dashboard precisa estar pronto para apresentacao aos CEOs

## Documentos de Referencia Criticos

| Documento | Local | Conteudo |
|-----------|-------|----------|
| GENOMA_COMERCIAL_VITAO360.md | Downloads/ | DNA da operacao: 6 jornadas, motor de regras, 200+ templates de notas, distribuicoes estatisticas, algoritmo de geracao, regras de validacao |
| AUDITORIA_COMPLETA_32_SESSOES.md | PASTA DE APOIO PROJETO/AUDITORIA/ | 82 decisoes (DEC-001 a DEC-082), 13 bugs, 18 pendencias, arquitetura completa |
| LOG_CONVERSA_EXTRACAO_CONTROLE_FUNIL.md | PASTA DE APOIO PROJETO/AUDITORIA/ | Detalhes da extracao dos 10.544 registros, criterios de classificacao |
| DOC_DEFINITIVA_AGENDA_DRAFT2.md | PASTA DE APOIO PROJETO/ | Fluxo AGENDA→DRAFT 2, 24 colunas EXATAS, mapeamento completo, dados reais Feb/2026 |
| REGRAS_INTELIGENCIA_CRM_VITAO_v2.md | PASTA DE APOIO PROJETO/ | DOCUMENTO MESTRE DEFINITIVO: 33 secoes, 10 principios, DRAFT 1 (48 cols), CARTEIRA (~257 cols), motor completo, Python code |
| CORRECAO_ALUCINACOES_DADOS_REAIS.md | PASTA G/ANALISES/ | Dados REAIS verificados: 866 vendas, R$ 1.8M, performance por vendedor/mes/rede |
| PROMPT_POPULAR_DRAFT2_ATENDIMENTOS.md | Downloads/ | Layout expandido 31 cols, 9 formulas automaticas, regras de processamento |
| SKILL_LOG_DRAFT_PIPELINE.md | CONSTURÇÃO DRAFT/ | Spec tecnica: LOG 20 cols, DRAFT 2 27 cols, formulas, formatacao, migration |
| SKILL_AGENDA_GENERATOR.md | CONSTURÇÃO DRAFT/ | Spec tecnica: AGENDA arquivo separado, 24 cols, logica selecao clientes, Python code |
| SKILL_REGRAS_FOUNDATION.md | CONSTURÇÃO DRAFT/ | Aba REGRAS: dropdowns, tabelas referencia, named ranges |
| INJECAO_CONTEXTO_DRAFT2_AGENDA_FINAL.md | Downloads/ | 31 colunas DRAFT 2, 30 colunas AGENDA, REGRAS 283 rows, 63 combinacoes, SCORE ranking |
| Blueprint v2 (HTML) | Pasta de apoio | Spec definitiva: 81 colunas, 8 grupos (DEC-080) |
| Blueprint v3 LOG/AGENDA/DASH (HTML) | Pasta de apoio | Spec de LOG, AGENDA e DASHBOARDS |

## Pastas Varridas na Area de Trabalho (47+)

ABA CRM TRATADO, ABA PROJECAO, AGENDA, AGENDA (ANDAMENTO), BLUEPRINTS, CAMPANHAS E ACOES, CARTEIRA REGIONAL, CLAUDE CODE, CLAUDE IA, CONSTURÇÃO DRAFT, CONSULTOR (Daiane/Manu/Larissa/Julio), CONTROLE FUNIL LOG, CRM 360 V12, CRM AINTELLIGENC360, DADOS CADASTRAIS VITAO, DAMARES CARTEIRAS METAS, DASH, DIRETORIO CENTRAL INTERNO, DRAFT1, DRAFT2, DRAFT3, GERENCIAL, GERENTE, MATERIAIS, MODELO DE PROCESSOS, NOVO FORMATO DE CONTROLE DIARIO, PASTA DE APOIO PROJETO (+AUDITORIA), PASTA ETAPA FINAL, PASTA G (CENTRAL INTERNO) (+ANALISES, +DOC LOG CRM, +EXTRACAO DE DADOS, +CARTEIRA SAP, +CARTEIRA REDES), PLANILHA CRM INTELIGENTE, PRECOS E TABELAS, PRODUTOS SAP, PUSH 2026, REDES E FRANQUIAS, SINALEIRO REDES, TRADE, VIDEOS REUNIOES CRM

</specifics>

<deferred>
## Deferred Ideas

- **Aba SINALEIRO/SEMAFORO** com filtros por estado, regiao, consultor, cor do semaforo — Phase 5/9
- **Aba PROJECAO/META por cliente** (refinar a ja feita na Phase 1) — Phase 8
- **Agendas individuais** por consultor (agenda_julio, agenda_daiane, etc.) — Phase 9/10
- **Unificacao AGENDA + DRAFT 2** como "santo graal" — Phase 9
- **Logica de retroalimentacao CARTEIRA <-> DRAFT 2** — Phase 9
- **Inteligencia de capacidade de atendimento** — Phase 8/9
- **Dashboard com ligacoes, atendimentos, tarefas, motivos de Jan/Fev** — Phase 5
- **Redistribuicao da Manu** (maternidade, 32.5% da receita) — Phase 8/9
- **VBA/Macro PROCESSAR** (DRAFT → LOG automatico) — Phase 10

</deferred>

---

*Phase: 04-log-completo*
*Context gathered: 2026-02-17*
*Enriched: AUDITORIA(20 docs) + GENOMA_COMERCIAL + INJECAO_CONTEXTO + DOC_DEFINITIVA + REGRAS_INTELIGENCIA_v2 + CORRECAO_ALUCINACOES + SKILLS(3) + FASES_JARVIS(7) + Downloads(15) + PASTA_G_ANALISES(13) + DOC_LOG_CRM(17)*
