# INTELIGENCIA DO NEGOCIO — CRM VITAO360
**Atualizado: 25/03/2026 | Fonte de verdade: INTELIGENTE FINAL OK.xlsx (40 abas, 5.8MB)**
**Baseline corrigido: R$ 2.091.000 (auditoria forense 68 arquivos, 23/03/2026)**

---

## FILOSOFIA CORE

> O CRM VITAO360 e um sistema AUTONOMO PREDITIVO.
> O Motor decide. O Score prioriza. A Agenda manda. O consultor EXECUTA.
> O humano nao pensa o que fazer — o CRM diz QUEM ligar, POR QUE, O QUE FAZER, e QUANDO voltar.

---

## ARQUITETURA: 9 DIMENSOES + SCORE + PRIORIDADE

Cada cliente tem 9 dimensoes calculadas automaticamente:

| # | Dimensao | Quem Preenche | Valores | Regra |
|---|----------|---------------|---------|-------|
| 1 | **SITUACAO** | Mercos (auto) | ATIVO (<=50d), EM RISCO (51-60d), INAT.REC (61-90d), INAT.ANT (>90d), PROSPECT (sem compra), LEAD (manual Daiane), NOVO (1a compra) | CRM le do Mercos, nao altera |
| 2 | **ESTAGIO FUNIL** | Motor sugere | 14 estagios (ver secao FUNIL) | Motor gera via XLOOKUP(SITUACAO\|RESULTADO) |
| 3 | **RESULTADO** | Consultor (dropdown) | 14 opcoes: VENDA/PEDIDO, ORCAMENTO, POS-VENDA, CS, RELACIONAMENTO, EM ATENDIMENTO, FU7, FU15, SUPORTE, NAO ATENDE, NAO RESPONDE, RECUSOU, CADASTRO, PERDA/FECHOU LOJA | Um so por atendimento |
| 4 | **TIPO CLIENTE** | Motor calcula | PROSPECT, LEAD, NOVO (1a compra), EM DESENVOLVIMENTO (2-3), RECORRENTE (4+ e 3+ meses), FIDELIZADO (6+ e 6+ meses), MADURO | Baseado em qtd pedidos + tempo |
| 5 | **FASE** | Motor gera | PROSPECCAO, NEGOCIACAO, RECOMPRA, SALVAMENTO, RECUPERACAO, NUTRICAO, POS-VENDA, CS, EM ATENDIMENTO, ORCAMENTO | SITUACAO x RESULTADO via Motor |
| 6 | **CURVA ABC** | Motor calcula | A (top 20%), B (prox 30%), C (restante 50%) | Faturamento acumulado |
| 7 | **TEMPERATURA** | Motor gera | QUENTE, MORNO, FRIO, CRITICO, PERDIDO | Motor prevalece, sem dropdown |
| 8 | **SINALEIRO** | Motor calcula | VERDE (dias<=ciclo), AMARELO (dias<=ciclo+30), VERMELHO (dias>ciclo+30), ROXO (sem historico) | LET(ciclo, dias, IF...) |
| 9 | **TENTATIVAS** | Motor incrementa | T1 (WPP dia 0), T2 (Ligacao +1d), T3 (WPP+Lig +1d), T4 (Lig final +2d), NUTRICAO (Email+WPP ciclo 15d), RESET (quando responde) | T1->T2->T3->T4->NUTRICAO. Reset apos VENDA |

---

## SCORE v2 — PESOS OFICIAIS (CARTEIRA cols 137-144)

**Formula:** `SCORE = (URGENCIA x 0.30) + (VALOR x 0.25) + (FOLLOW-UP x 0.20) + (SINAL x 0.15) + (TENTATIVA x 0.05) + (SITUACAO x 0.05)`

| # | Fator | Peso | Fonte | Pontuacao |
|---|-------|------|-------|-----------|
| 1 | **URGENCIA TEMPORAL** | 30% | DIAS SEM COMPRA / CICLO MEDIO | INAT.ANT=100, INAT.REC=90, EM RISCO=70, ratio>=1.5=100, >=1.0=60, >=0.7=40, <0.7=20, PROSPECT/LEAD=10 |
| 2 | **VALOR DO CLIENTE** | 25% | CURVA ABC + TIPO CLIENTE | A+FID/MAD=100, A=80, B+REC/FID=60, B=50, C=20, FID/MAD sem ABC=60, REC=40, EM_DESENV=20, default=10 |
| 3 | **FOLLOW-UP VENCIDO** | 20% | PROX FOLLOW-UP vs HOJE | >=7d atraso=100, >=3d=80, >=1d=70, hoje=60, ate -3d=40, default=20, sem FU=50 |
| 4 | **SINAL DE COMPRA** | 15% | TEMPERATURA + E-COMMERCE | CRITICO=90, QUENTE+carrinho=100, QUENTE=80, MORNO+B2B+carrinho=70, MORNO+B2B=60, MORNO=40, FRIO=10, PERDIDO=0 |
| 5 | **TENTATIVA** | 5% | T1/T2/T3/T4 | T4+=100, T3=50, T1/T2=10 |
| 6 | **SITUACAO** | 5% | SITUACAO Mercos | EM RISCO=80, ATIVO=40, INAT.REC/ANT=20, PROSPECT=10 |

---

## PRIORIDADE v2 — 7 NIVEIS (CARTEIRA col 144)

| Prioridade | Label | Regra | Distribuicao/dia |
|-----------|-------|-------|-----------------|
| **P1** | NAMORO NOVO | POS-VENDA/CS + NOVO/ATIVO + Score>=70 | Pula fila (inviolavel) |
| **P2** | NEGOCIACAO ATIVA | ORCAMENTO/EM ATENDIMENTO/CADASTRO | 15-20/dia |
| **P3** | PROBLEMA | SUPORTE aberto | Pula fila |
| **P4** | MOMENTO OURO | INAT.REC Score>=75 OU NOVO OU Score>=50 | 10-15/dia |
| **P5** | INAT. RECENTE | INAT.REC default OU INAT.ANT Score>=80 | 5-10/dia |
| **P6** | INAT. ANTIGO | INAT.ANT default | 0-5/dia |
| **P7** | PROSPECCAO | PROSPECT/LEAD | 0 (campanha mensal) |

### Desempate (quando score empata)
1. CURVA ABC (A primeiro)
2. TICKET MEDIO (maior primeiro)
3. TIPO CLIENTE (mais maduro primeiro)
4. FOLLOW-UP mais vencido primeiro

### Meta Balance
Se P2-P5 nao cobrem 80% da meta mensal, clientes PROSPECCAO recebem +20 pontos bonus no Score.

---

## MOTOR DE REGRAS v4 — 92 COMBINACOES

**CHAVE = SITUACAO|RESULTADO** → gera 9 outputs automaticamente

### 7 SITUACOES x ~14 RESULTADOS = 92 regras

| SITUACAO | Qtd Regras | Threshold (dias sem compra) | Estagios gerados |
|----------|-----------|---------------------------|-----------------|
| ATIVO | 14 | <= 50 dias | POS-VENDA, ORCAMENTO, EM ATENDIMENTO, CS/RECOMPRA, NAO ATENDE/RESPONDE, PERDA |
| EM RISCO | 13 | 51-60 dias | Mesmos + urgencia de salvamento |
| INAT.REC | 14 | 61-90 dias | REATIVACAO + salvamento |
| INAT.ANT | 14 | > 90 dias | RESGATE + recuperacao |
| PROSPECT | 12 | Nunca comprou | PROSPECCAO, ORCAMENTO, POS-VENDA |
| LEAD | 12 | Lead qualificado | Mesmos que PROSPECT |
| NOVO | 13 | Primeiro pedido recente | POS-VENDA, EM ATENDIMENTO, CS/RECOMPRA |

### 9 Outputs por combinacao
1. ESTAGIO FUNIL (posicao no Kanban)
2. FASE (estrategia comercial)
3. TIPO CONTATO (classificacao do contato)
4. ACAO FUTURA (texto prescritivo — o que fazer)
5. TEMPERATURA (engajamento)
6. FOLLOW-UP DIAS (quando voltar)
7. GRUPO DASH (agrupamento dashboard)
8. TIPO ACAO (classificacao da acao)
9. CHAVE (concatenacao para lookup)

### Como funciona no Excel
```
LOG (LARISSA/MANU/JULIO/DAIANE):
  TIPO CONTATO = XLOOKUP(SITUACAO|RESULTADO, MOTOR!CHAVE, MOTOR!TIPO_CONTATO)
  FOLLOW-UP    = TODAY() + XLOOKUP(SITUACAO|RESULTADO, MOTOR!CHAVE, MOTOR!FOLLOWUP_DIAS)
  ACAO SUGERIDA = XLOOKUP(SITUACAO|RESULTADO, MOTOR!CHAVE, MOTOR!ACAO_FUTURA)
  TIPO ACAO    = XLOOKUP(SITUACAO|RESULTADO, MOTOR!CHAVE, MOTOR!TIPO_ACAO)
```

---

## 14 ESTAGIOS DO FUNIL — Kanban

### Jornada Pre-Venda
1. INICIO CONTATO → Primeiro contato
2. TENTATIVA → T1-T4 em andamento
3. PROSPECCAO → Nao respondeu, continuamos

### Jornada Venda
4. EM ATENDIMENTO → Respondeu, conversa ativa (2 pontas falando)
5. CADASTRO → Fazendo cadastro
6. ORCAMENTO → Proposta enviada
7. PEDIDO → Venda fechada (MARCO)

### Jornada Pos-Venda (ciclo automatico D+4→D+15→D+30)
8. ACOMP POS-VENDA → D+4: faturou? saiu da expedicao?
9. POS-VENDA → D+15: recebeu? chegou bem?
10. CS → D+30: tentativa de recompra (sell out + criacao de intencao)

### Loop Follow-Up
11. FOLLOW-UP → D+15 ou D+30 apos CS nao converter

### Auxiliares
12. SUPORTE → Problema a resolver (pula fila P0)
13. RELACIONAMENTO → Manutencao de ativo estavel
14. NUTRICAO → T4+ sem resposta, campanha mensal

### Fluxo
```
PRE-VENDA:  INICIO → TENTATIVA → PROSPECCAO → EM ATENDIMENTO
VENDA:      EM ATENDIMENTO → CADASTRO → ORCAMENTO → PEDIDO
POS-VENDA:  PEDIDO → ACOMP D+4 → POS-VENDA D+15 → CS D+30
LOOP:       CS nao vendeu → FOLLOW-UP D+15/D+30 → repete
RESET:      Qualquer estagio + VENDA → volta para POS-VENDA
```

---

## 6 FASES ESTRATEGICAS

| # | Fase | Descricao | Score Base |
|---|------|-----------|-----------|
| 1 | PROSPECCAO | Nunca comprou, tentando conquistar | 30 |
| 2 | NEGOCIACAO | Ativo, em conversa, namoro novo | 80 |
| 3 | RECOMPRA | Ativo, no ciclo. CULTIVAR e prioridade #1 | 100 |
| 4 | SALVAMENTO | Inativo recente (61-90d). Salvar antes que piore | 60 |
| 5 | RECUPERACAO | Inativo antigo (>90d). Trazer de volta | 40 |
| 6 | NUTRICAO | Esgotou tentativas T1-T4. Campanha 1x/mes | 10 |

**Filosofia: CULTIVAR (recompra) > SALVAR (inativos recentes) > CONQUISTAR (prospects)**

---

## 18 TABELAS DE REGRAS (aba REGRAS, 496 rows)

| # | Tabela | Qtd Valores | Funcao |
|---|--------|-------------|--------|
| 1 | RESULTADO | 14 valores | Dropdown do consultor: o que aconteceu |
| 2 | TIPO DO CONTATO | 7 valores | Classificacao do contato |
| 3 | MOTIVO | 22 valores | Por que o cliente nao comprou + area responsavel |
| 4 | SITUACAO | 7 valores + cores | Status automatico por dias sem compra |
| 5 | FASE | 9 valores | Ciclo comercial do cliente |
| 6 | TIPO CLIENTE | 6 valores + criterios | Maturidade na carteira |
| 7 | CONSULTOR | 5 nomes + territorios | Equipe comercial |
| 8 | TENTATIVA | 6 fases + canais + intervalos | Protocolo T1-T4 + NUTRICAO + RESET |
| 9 | SINALEIRO | 4 cores + regras | Saude do cliente (dias vs ciclo) |
| 10 | LISTAS SIMPLES | 5 listas | SIM/NAO, TIPO_ATEND, CURVA_ABC, GRUPO_DASH, TEMPERATURA |
| 11 | TIPO ACAO | 6 valores | VENDA, PRE-VENDA, POS-VENDA, RESOLUCAO, PROSPECCAO, ADMIN |
| 12 | TIPO PROBLEMA | 8 categorias + area | RNC: atraso, avariado, erro NF, cobranca, etc |
| 13 | ACAO FUTURA | 22 acoes prescritas | O que o Motor manda fazer |
| 14 | TAREFA/DEMANDA | 25 tarefas operacionais | Tarefas do dia-a-dia |
| 15 | SINALEIRO META | 4 faixas | VERDE >=100%, AMARELO 50-99%, VERMELHO 1-49%, PRETO 0% |
| 16 | SCORE RANKING | 6 fatores + pesos | Score v2 oficial |
| 17 | MOTOR DE REGRAS | 92 combinacoes | SITUACAO x RESULTADO → 9 outputs |
| 18 | METODOLOGIA PRIORIZACAO | 7 niveis + 6 regras | P1-P7 + desempate + meta balance |

---

## PROTOCOLO DE TENTATIVAS T1-T4

| # | Tentativa | Canal | Intervalo | Acao |
|---|-----------|-------|-----------|------|
| T1 | Primeira | WhatsApp | Dia 0 | Mensagem inicial |
| T2 | Segunda | Ligacao | +1 dia | Mudar horario |
| T3 | Terceira | WhatsApp + Ligacao | +1 dia | Mensagem diferente + tentar ligar |
| T4 | Quarta (final) | Ligacao final | +2 dias | Ultima tentativa |
| NUTRICAO | Campanha | Email + WhatsApp | Ciclo 15 dias | So campanha, nao entra na agenda |
| RESET | Respondeu | Qualquer | Imediato | Volta para T1 |

---

## FLUXO DE DADOS ENTRE ABAS

```
FONTES (input)
  DRAFT 1 (566 x 60) ← Mercos brutos (identidade, compras, e-commerce, vendas mes a mes)
  DRAFT 2 (1001 x 40) ← LOG atendimentos com Motor
  DRAFT 3 (1542 x 18) ← SAP cadastro
  PROJECAO (662 x 80) ← Metas SAP vs Realizado

MOTOR (abas ocultas — processamento)
  MOTOR DE REGRAS (92 combos) ← XLOOKUP por CHAVE = SITUACAO|RESULTADO
  REGRAS (496 rows, 18 tabelas) ← alimenta dropdowns + validacoes
  ARQUITETURA 9 DIMENSOES ← pesos Score + prioridades

SAIDA (o que o consultor ve)
  CARTEIRA (1593 x 144) ← INDEX-MATCH de DRAFT 1 + XLOOKUP de DRAFT 2 + PROJECAO
  AGENDA (670 x 18) ← priorizados por Score, 40-60/dia
  LARISSA/MANU/JULIO/DAIANE (40 cols) ← LOG append-only com Motor
  SINALEIRO (665 x 26) ← meta vs real por cliente
  DASHBOARD (54 x 14) ← KPIs CEO, sinaleiro por cor, performance
  RNC (1503 x 15) ← problemas com SLA
```

---

## NUMEROS-CHAVE ATUALIZADOS

| Metrica | Valor (atualizado 25/03/2026) |
|---------|-------------------------------|
| Abas totais | 40 (16 visiveis + 24 ocultas) |
| Clientes CARTEIRA | 1.581 (+ 9 CNPJs vazios + 1 em branco) |
| Clientes SINALEIRO | 661 |
| Combinacoes Motor | 92 (7 SITUACOES x ~14 RESULTADOS) |
| Tabelas REGRAS | 18 |
| Estagios Funil | 14 |
| Fases Estrategicas | 6 (+ 3 operacionais: POS-VENDA, CS, EM ATENDIMENTO) |
| Motivos nao-compra | 22 |
| Tipos problema RNC | 8 |
| Acoes futuras | 22 |
| Tarefas operacionais | 25 |
| Faturamento baseline | R$ 2.091.000 (CORRIGIDO 23/03/2026) |
| Meta anual 2026 | R$ 4.747.200 (SAP) |
| Projecao 2026 | R$ 3.377.120 (+69% vs 2025) |
| Q1 2026 real | R$ 415.904 (35.6% atingimento trimestre) |
| Consultores ativos | 4 (Manu, Larissa, Julio, Daiane) + Helder (supervisao) |

---

## CONSULTORES — DE-PARA + PERFORMANCE

| Consultor | Territorio | Clientes | Fat Real 2025 | Meta 2026 | % Ating | Status |
|-----------|-----------|----------|---------------|-----------|---------|--------|
| MANU DITZEL | SC/PR/RS | 165 | R$ 777.656 | R$ 926.557 | 83.9% | BOM |
| LARISSA PADILHA | Brasil sem rede | 222 | R$ 964.073 | R$ 1.246.641 | 77.3% | BOM |
| DAIANE STAVICKI | Redes/Franquias | 164 | R$ 210.316 | R$ 1.400.219 | 15.0% | CRITICO |
| JULIO GADRET | Cia Saude + Fitland | 110 | R$ 149.695 | R$ 1.188.181 | 12.6% | CRITICO |
| **TOTAL** | — | **661** | **R$ 2.101.741** | **R$ 4.761.598** | **44.1%** | — |

### Aliases (DE-PARA)
- MANU: Manu, Manu Vitao, Manu Ditzel, Hemanuele Ditzel, HEMANUELE ROSA DITZEL
- LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo
- DAIANE: Daiane, Central Daiane, Daiane Vitao, Central-Daiane
- JULIO: Julio, Julio Gadret
- LEGADO: Bruno Gretter, Jeferson Vitao, Patric, Gabriel, Sergio, Ive, Ana

---

## TWO-BASE ARCHITECTURE (INVIOLAVEL)

| Tipo | Valor R$ | Onde vive | Regra |
|------|----------|-----------|-------|
| **VENDA** | SIM (faturamento, ticket, comissao) | CARTEIRA blocos VENDAS, DRAFT 1 | Unico lugar com R$ real |
| **LOG** | SEMPRE R$ 0.00 | LARISSA/MANU/JULIO/DAIANE, DRAFT 2 | Nenhum campo monetario |

**Violacao = inflacao de 742%.** Ja aconteceu com ChatGPT (558 registros ALUCINACAO).

---

## LIMITACOES CONHECIDAS

1. **Score v2 (CARTEIRA) vs Score Engine (Python)**: Pesos diferentes. v2 da planilha e o OFICIAL.
2. **CNPJ formato inconsistente**: CARTEIRA=numerico 14d, OPERACIONAL=com pontos, PROJECAO=sem zeros esquerda
3. **2 erros formula**: REGRAS VISUAL!F284 (#VALUE!) — impacto BAIXO
4. **Julio Gadret**: 100% fora do sistema. Dados limitados.
5. **558 registros ALUCINACAO**: ChatGPT. Catalogados. NUNCA integrar.
6. **Manu licenca maternidade Q2 2026**: Carteira sera redistribuida.
7. **E-commerce**: Outubro e Maio 2025 ausentes (sem arquivo).
8. **openpyxl nao recalcula**: Formulas precisam ser recalculadas no Excel real.

---

## DOCUMENTOS DE REFERENCIA

| Documento | Conteudo |
|-----------|----------|
| `data/docs/PRD_SAAS.md` | PRD completo (14 epicos, 60+ features) |
| `data/docs/RAIO_X_PLANILHA_INTELIGENTE_FINAL.md` | Raio-X 40 abas, formulas, fluxos |
| `data/docs/INVENTARIO_FONTES_DESKTOP.md` | 4 arquivos finais + CENTRAL CRM 360 (1.151 arquivos) |
| `BRIEFING-COMPLETO.md` | Contexto do negocio |
| `BACKUP_DOCUMENTACAO_ANTIGA.md` | Historico completo (10 fases, 154K formulas) |
| `data/intelligence/*.json` | 13 JSONs de inteligencia extraida |

---

*Documento atualizado pelo @aios-master em 25/03/2026.*
*Fonte de verdade: CRM_VITAO360 INTELIGENTE FINAL OK.xlsx (40 abas, 5.8MB)*
