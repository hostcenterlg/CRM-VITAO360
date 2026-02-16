# ══════════════════════════════════════════════════════════════════════════════
# SPEC COMPLETA — CRM VITAO360 V3 — CLAUDE CODE
# Documento unico de referencia para construcao do sistema
# Versao: 3.0 FINAL | Data: 09/02/2026
# ══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 1: DIAGNOSTICO V2 — POR QUE RECONSTRUIR
# ═══════════════════════════════════════════════════════════════════════════

## 1.1 ERROS CRITICOS ENCONTRADOS (440 registros auditados)

```
ERRO 1: ESTAGIO FUNIL 100% ERRADO
  V2 usava grupos dashboard (FUNIL/RELAC./NAO VENDA) como estagio
  Correto: PROSPECCAO, EM ATENDIMENTO, NEGOCIACAO, ORCAMENTO,
           POS-VENDA, CS/RECOMPRA, RELACIONAMENTO, PERDA/NUTRICAO

ERRO 2: 97 CONTRADICOES IMPOSSÍVEIS (22%)
  PROSPECT + RECOMPRA, ATIVO + SALVAMENTO, INAT.ANT + CS, etc.

ERRO 3: TERRITORIO 74% ERRADO (329/440)

ERRO 4: CAMPOS DE INTELIGENCIA 100% VAZIOS
  DIAS SEM COMPRA, CICLO MEDIO, CURVA ABC, SINALEIRO, TEMPERATURA = vazio

ERRO 5: SEM CAUSA-EFEITO
  Campos populados aleatoriamente, sem logica de RESULTADO → calculo
```

## 1.2 PRINCIPIO FUNDAMENTAL V3

> "PARA CADA ACAO, UMA REACAO"
> O RESULTADO do atendimento do consultor DETERMINA automaticamente:
> Estagio, Fase, Tipo Contato, Follow-up, Acao Futura, Temperatura


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 2: ARQUITETURA — FLUXO DE DADOS
# ═══════════════════════════════════════════════════════════════════════════

## 2.1 MAPA COMPLETO

```
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ MERCOS           │  │ RELATORIOS VENDAS│  │ ACESSO ECOMMERCE │  │ POSITIVACAO      │
│ Carteira Clientes│  │ (12 meses)       │  │ (12 meses)       │  │ (12 meses)       │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         └──────────────────────┼───────────────────────┼──────────────────────┘
                                ▼
                  ┌──────────────────────────┐
                  │  📦 DRAFT 1              │
                  │  BASE MESTRE DO CLIENTE   │
                  │  (48 colunas - 7 blocos)  │
                  └─────────────┬────────────┘
                                │
              ╔═════════════════╧═══════════════════════════════════════════╗
              ▼                 ▼                    ▼              ▼       ▼
    ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────┐  ┌──────┐
    │  CARTEIRA     │  │  DRAFT 2 (LOG)│  │  PROJECAO    │  │AGENDA│  │ DASH │
    │  Visao 360    │← │  Atendimentos │  │  Meta SAP    │  │Diaria│  │ KPIs │
    │  (~257 cols)  │  │  (24 cols)    │  │  Sinaleiro   │  │      │  │      │
    └───────────────┘  └───────────────┘  └──────────────┘  └──────┘  └──────┘
```

## 2.2 CICLO OPERACIONAL DIARIO

```
MANHA:    Gestor gera AGENDA do dia (CARTEIRA → ranking por SCORE)
DIA TODO: 4 consultores executam, selecionam RESULTADO nos dropdowns
FIM DIA:  Gestor cola resultados no DRAFT 2
          Motor de regras calcula campos automaticos
          CARTEIRA atualiza via XLOOKUPs
PROXIMO DIA: CARTEIRA atualizada → nova AGENDA com prioridades frescas
```

## 2.3 ABAS DO ARQUIVO

```
┌──────────────┬──────────┬──────────────────────────────────────────────────────────┐
│ ABA          │ COLUNAS  │ FUNCAO                                                   │
├──────────────┼──────────┼──────────────────────────────────────────────────────────┤
│ REGRAS       │ 5        │ Tabelas de referencia (dropdowns, validacoes)            │
│ DRAFT 1      │ 48       │ BASE MESTRE: Mercos tratado → alimenta TUDO             │
│ PROJECAO     │ ~30      │ META SAP anual + Sinaleiro de atingimento               │
│ CARTEIRA     │ ~257     │ VISAO 360: Mercos + Funil + SAP + Acompanhamento        │
│ DRAFT 2      │ 24       │ LOG de atendimentos (motor de regras)                   │
│ AGENDA       │ ~20      │ Agenda diaria do consultor (visao operacional)           │
│ DASH         │ variavel │ KPIs e indicadores                                      │
│ LOG          │ 24       │ Historico completo (DRAFT 2 arquivado)                  │
│ Claude Log   │ variavel │ Registro de acoes do sistema                            │
└──────────────┴──────────┴──────────────────────────────────────────────────────────┘
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 3: ABA REGRAS — TABELAS DE REFERENCIA
# ═══════════════════════════════════════════════════════════════════════════

## 3.1 RESULTADOS (12 opcoes — dropdown do consultor)

```
┌────┬──────────────────────┬──────────────┬──────────────┬─────────────────────────┐
│ #  │ RESULTADO             │ FOLLOW-UP    │ GRUPO DASH   │ QUANDO USAR             │
├────┼──────────────────────┼──────────────┼──────────────┼─────────────────────────┤
│  1 │ EM ATENDIMENTO        │ +2 dias uteis│ FUNIL        │ Negociacao ativa        │
│  2 │ ORCAMENTO             │ +1 dia util  │ FUNIL        │ Proposta enviada        │
│  3 │ CADASTRO              │ +2 dias uteis│ FUNIL        │ Cliente novo em cadastro│
│  4 │ VENDA / PEDIDO        │ +45 dias uteis│ FUNIL       │ Pedido fechado          │
│  5 │ RELACIONAMENTO        │ +7 dias uteis│ RELAC.       │ Contato pos-venda/CS    │
│  6 │ FOLLOW UP 7           │ +7 dias uteis│ RELAC.       │ Retomar em 1 semana     │
│  7 │ FOLLOW UP 15          │ +15 dias uteis│ RELAC.      │ Retomar em 2 semanas    │
│  8 │ SUPORTE               │ 0            │ RELAC.       │ Problema resolvido      │
│  9 │ NAO ATENDE            │ +1 dia util  │ NAO VENDA    │ Ligou sem resposta      │
│ 10 │ NAO RESPONDE          │ +1 dia util  │ NAO VENDA    │ WhatsApp sem resposta   │
│ 11 │ RECUSOU LIGACAO       │ +2 dias uteis│ NAO VENDA    │ Rejeitou chamada        │
│ 12 │ PERDA / FECHOU LOJA   │ 0            │ NAO VENDA    │ Cliente perdido         │
└────┴──────────────────────┴──────────────┴──────────────┴─────────────────────────┘
```

## 3.2 MOTIVOS (10 opcoes)

```
 1. AINDA TEM ESTOQUE
 2. PRODUTO NAO VENDEU / SEM GIRO
 3. LOJA ANEXO/SM
 4. SO QUER GRANEL
 5. PROBLEMA LOGISTICO
 6. PROBLEMA FINANCEIRO
 7. PROPRIETARIO INDISPONIVEL
 8. FECHANDO/FECHOU LOJA
 9. SEM INTERESSE
10. PRIMEIRO CONTATO/SEM RESPOSTA
```

## 3.3 SITUACAO DO CLIENTE (por dias sem compra)

```
┌────────────────┬────────────────┬───────────┬──────────────────────────┐
│ SITUACAO       │ DIAS S/COMPRA  │ COR       │ SIGNIFICADO              │
├────────────────┼────────────────┼───────────┼──────────────────────────┤
│ ATIVO          │ 0 - 50         │ #00B050   │ Comprando normalmente    │
│ EM RISCO       │ 51 - 60        │ #FFC000   │ Ciclo vencendo           │
│ INAT.REC       │ 61 - 90        │ #FFC000   │ Parou de comprar recente │
│ INAT.ANT       │ > 90           │ #FF0000   │ Sumiu ha muito tempo     │
│ NOVO           │ 1a compra      │ #0070C0   │ Primeira compra feita    │
│ PROSPECT       │ nunca comprou  │ #7B2FF2   │ Ainda nao e cliente      │
└────────────────┴────────────────┴───────────┴──────────────────────────┘
COR: Aplicar APENAS na celula SITUACAO, NUNCA na linha inteira
```

## 3.4 ESTAGIOS DO FUNIL (posicao real na jornada)

```
1. PROSPECCAO        → Primeiro contato, ainda nao e cliente
2. EM ATENDIMENTO    → Respondeu, negociacao ativa
3. NEGOCIACAO        → Interesse confirmado, discutindo termos
4. ORCAMENTO         → Proposta enviada, aguardando resposta
5. POS-VENDA         → Comprou, acompanhamento pos-compra
6. CS / RECOMPRA     → Sucesso do cliente, tentativa de recompra
7. RELACIONAMENTO    → Manutencao do vinculo
8. PERDA / NUTRICAO  → Perdido ou em nutrição de longo prazo
```

## 3.5 TENTATIVAS DE CONTATO (cadencia)

```
T1: WhatsApp  → +1 dia util  (se NAO RESPONDE)
T2: Ligacao   → +1 dia util  (se NAO ATENDE)
T3: WhatsApp  → +2 dias uteis (se NAO RESPONDE)
T4: Ligacao   → +2 dias uteis (se NAO ATENDE)
Apos T4 sem resposta → PERDA / NUTRICAO

SE RESPONDE EM QUALQUER T → RESET (volta a T0)
O ESTAGIO NAO MUDA durante tentativas — so a TENTATIVA avanca
```

## 3.6 TIPO CLIENTE (maturidade por meses positivado)

```
PROSPECT:          0 meses (nunca comprou)
NOVO:              1 mes
EM DESENVOLVIMENTO: 2-3 meses
RECORRENTE:        4-6 meses
FIDELIZADO:        7+ meses
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 4: DRAFT 1 — BASE MESTRE DO CLIENTE (48 COLUNAS)
# ═══════════════════════════════════════════════════════════════════════════

## BLOCO 1: IDENTIDADE (11 colunas) — Fonte: Carteira Mercos

```
Col  1: NOME FANTASIA           Texto   Identificacao visual (ancora)
Col  2: CNPJ                    Texto   Chave primaria (14 digitos)
Col  3: RAZAO SOCIAL            Texto   Nome oficial
Col  4: UF                      Texto   Estado (2 letras) → territorio
Col  5: CIDADE                  Texto   Cidade
Col  6: EMAIL                   Texto   Email
Col  7: TELEFONE                Texto   55+DDD+NUM
Col  8: DATA CADASTRO           Data    Data cadastro Mercos
Col  9: REDE / REGIONAL         Texto   Rede franquia
Col 10: CONSULTOR               Texto   Regra territorio (calculado)
Col 11: VENDEDOR ULTIMO PEDIDO  Texto   Referencia historica
```

## BLOCO 2: STATUS (4 colunas) — Fonte: Mercos + Calculado

```
Col 12: SITUACAO                Texto   ATIVO/EM RISCO/INAT.REC/INAT.ANT/NOVO/PROSPECT
Col 13: PRIORIDADE              Numero  1=ATIVO, 2=EM RISCO, 3=INAT.REC, 4=INAT.ANT, 5=PROSPECT
Col 14: DIAS SEM COMPRA         Numero  Quantos dias desde ultimo pedido
Col 15: CICLO MEDIO             Numero  Media dias entre compras (relogio biologico)
```

## BLOCO 3: COMPRAS (3 colunas) — Fonte: Carteira Mercos + Calculado

```
Col 16: DATA ULTIMO PEDIDO      Data    Quando comprou pela ultima vez
Col 17: VALOR ULTIMO PEDIDO     Numero  R$ do ultimo pedido
Col 18: TOTAL PERIODO           Numero  Soma vendas 12 meses (calculado)
```

## BLOCO 4: ECOMMERCE (6 colunas) — Fonte: Relatorios Ecommerce

```
Col 19: ACESSOS SEMANA          Numero  Acessos recentes
Col 20: ACESSO B2B              Numero  Vezes que entrou no portal
Col 21: ACESSOS PORTAL          Numero  Total acessos
Col 22: ITENS CARRINHO          Numero  Itens adicionados ao carrinho
Col 23: VALOR B2B               Numero  Valor potencial no carrinho
Col 24: OPORTUNIDADE            Texto   🔥QUENTE/🟡MORNO/❄️FRIO (calculado)
```

OPORTUNIDADE:
```
🔥 QUENTE: Itens no carrinho + NAO comprou → PRIORIDADE MAXIMA
🟡 MORNO:  Acessou portal + NAO adicionou itens
❄️ FRIO:   Nao acessou nada
```

## BLOCO 5: VENDAS MES A MES (13 colunas) — Fonte: Relatorios Vendas

```
Col 25-36: [MES-11] ate [MES ATUAL]  Numero  Valor vendido em cada mes
Col 37:    TOTAL VENDAS PERIODO       Numero  SOMA(cols 25:36)
```
Colunas rolantes — nomes mudam a cada mes.

## BLOCO 6: RECORRENCIA (7 colunas) — Fonte: Positivacao + Calculado

```
Col 38: Nº COMPRAS              Numero  Total pedidos no periodo
Col 39: CURVA ABC               Texto   A(>=2k) B(>=500) C(<500)
Col 40: MESES POSITIVADO        Numero  Quantos meses comprou (0-12)
Col 41: MEDIA MENSAL            Numero  TOTAL / MESES POSITIVADO
Col 42: TICKET MEDIO            Numero  TOTAL / Nº COMPRAS
Col 43: MESES LISTA             Numero  Tempo na base
Col 44: TIPO CLIENTE            Texto   PROSPECT/NOVO/EM DESENV/RECORRENTE/FIDELIZADO
```

## BLOCO 7: ATENDIMENTO MERCOS (4 colunas) — Fonte: Rel. Atendimentos

```
Col 45: ULT. REGISTRO MERCOS       Data   Ultimo registro CRM Mercos
Col 46: DATA ULT. ATEND. MERCOS    Data   Data ultimo atendimento
Col 47: TIPO ATENDIMENTO MERCOS    Texto  Tipo registrado
Col 48: OBS ATENDIMENTO MERCOS     Texto  Observacao do consultor
```

## 4.1 ETL — COMO POPULAR O DRAFT 1

```
┌────────────────────────────┬───────────────────────────────┬──────────────────────────┐
│ BLOCO                      │ ARQUIVO FONTE                 │ COMO PROCESSAR           │
├────────────────────────────┼───────────────────────────────┼──────────────────────────┤
│ IDENTIDADE (1-11)          │ Carteira_detalhada_*.xlsx     │ Direto (normalizar)      │
│ STATUS (12-15)             │ Carteira_detalhada_*.xlsx     │ SITUACAO direto, resto   │
│                            │                               │ calculado                │
│ COMPRAS (16-18)            │ Carteira_detalhada_*.xlsx     │ Direto + soma vendas     │
│ ECOMMERCE (19-24)          │ Acesso_ao_Ecomerce_*.xlsx     │ header=5, match Razao    │
│ VENDAS MES A MES (25-37)   │ Relatorio_vendas_*.xlsx       │ header=9, match Razao    │
│ RECORRENCIA (38-44)        │ Positivacao_*.xlsx + calculado│ header=9, contar meses   │
│ ATENDIMENTO (45-48)        │ Relatorio_Atendimentos_Mercos │ Ultimo registro por CNPJ │
└────────────────────────────┴───────────────────────────────┴──────────────────────────┘

CHAVE: CNPJ (14 digitos sem pontuacao)
MATCH SECUNDARIO: RAZAO SOCIAL (MAIUSCULO, sem acentos, trim)
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 5: ABA PROJECAO — META SAP + SINALEIRO DE ATINGIMENTO
# ═══════════════════════════════════════════════════════════════════════════

## 5.1 FONTE DOS DADOS

Arquivo: BASE_SAP__META_E_PROJEÇÃO_2026___02__INTERNO__2026.xlsx

```
ABA "Faturamento": Meta mensal por GRUPO CHAVE × PRODUTO
  Filtro: coluna "Grupo Produto" = "01. TOTAL" para meta total do grupo
  Chave: COD GRUPO CHAVE (col 10)
  Meses: JAN(C14) a DEZ(C25), TOTAL(C26)

ABA "Leads": Leads projetados por grupo/mes
ABA "Positivacao": Clientes positivados esperados por grupo/mes
ABA "Balizador": Distribuicao % por categoria de produto
ABA "Resumo": Meta anual consolidada = R$ 4.747.200
```

## 5.2 METAS POR GRUPO (dados reais)

```
┌──────────────────────────────────────┬──────────┬──────────┬──────────────┐
│ GRUPO CHAVE                          │ META JAN │ META FEV │ POSIT. JAN   │
├──────────────────────────────────────┼──────────┼──────────┼──────────────┤
│ CIA DA SAUDE                         │ R$52.500 │ R$55.500 │ 35 clientes  │
│ FITLAND                              │ R$43.500 │ R$45.000 │ 29 clientes  │
│ DIVINA TERRA                         │ R$24.000 │ R$25.500 │ 16 clientes  │
│ VIDA LEVE                            │ R$24.000 │ R$24.000 │ 16 clientes  │
│ BIO MUNDO                            │ R$ 6.000 │ R$ 6.000 │  4 clientes  │
│ TUDO EM GRAOS / VGA                  │ R$ 4.500 │ R$ 4.500 │  3 clientes  │
│ ARMAZEM FIT STORE                    │ R$ 3.000 │ R$ 3.000 │  2 clientes  │
│ MUNDO VERDE                          │ R$ 3.000 │ R$ 3.000 │  2 clientes  │
│ NATURVIDA                            │ R$ 3.000 │ R$ 3.000 │  2 clientes  │
│ ESMERALDA                            │ R$ 3.000 │ R$ 3.000 │  2 clientes  │
│ TRIP                                 │ R$ 1.500 │ R$ 1.500 │  1 cliente   │
│ LIGEIRINHO                           │ R$ 1.500 │ R$ 1.500 │  1 cliente   │
│ MERCOCENTRO                          │ R$ 1.500 │ R$ 1.500 │              │
│                                      │          │          │              │
│ TOTAL MENSAL                         │ R$333.600│ R$348.600│ 385 clientes │
│ TOTAL ANUAL                          │          │          │ R$ 4.747.200 │
└──────────────────────────────────────┴──────────┴──────────┴──────────────┘
```

## 5.3 DISTRIBUICAO DA META POR CLIENTE

A meta do SAP e por GRUPO, nao por cliente individual.
Distribuir proporcionalmente:

```
META_CLIENTE_MES = META_GRUPO_MES × (VENDA_HIST_CLIENTE ÷ VENDA_HIST_GRUPO)

Exemplo:
  CIA DA SAUDE meta JAN = R$ 52.500
  Cliente X faturou 10% do historico total da CIA
  META_CLIENTE_X_JAN = R$ 5.250

  Se cliente NOVO sem historico:
  META_CLIENTE = META_GRUPO ÷ TOTAL_LEADS_GRUPO (distribuicao igual)
```

## 5.4 SINALEIRO DE ATINGIMENTO (🚦 META)

```
🟢 VERDE:  REALIZADO ≥ 100% da META    → Batendo meta
🟡 AMARELO: REALIZADO 50-99% da META   → Precisa acelerar
🔴 VERMELHO: REALIZADO < 50% da META   → Alerta critico
⚫ PRETO:  REALIZADO = 0               → Nenhuma venda
```

## 5.5 DOIS SINALEIROS (NAO CONFUNDIR)

```
🚦 SINALEIRO 1: CICLO DE COMPRA (col 61 da CARTEIRA)
   Pergunta: "O cliente esta no ritmo normal?"
   Compara: DIAS SEM COMPRA vs CICLO MEDIO
   🟢 ≤ Ciclo | 🟡 Ciclo+1 a Ciclo+30 | 🔴 > Ciclo+30 | 🟣 Nunca comprou

🚦 SINALEIRO 2: ATINGIMENTO DE META (aba PROJECAO)
   Pergunta: "O cliente esta batendo a meta projetada?"
   Compara: REALIZADO ACUMULADO vs META ACUMULADA
   🟢 ≥100% | 🟡 50-99% | 🔴 <50% | ⚫ 0%

COMBINACOES ESTRATEGICAS:
  Ciclo 🟢 + Meta 🟢 = PERFEITO → manter rotina
  Ciclo 🟢 + Meta 🔴 = Compra mas POUCO → acao de upsell/mix
  Ciclo 🔴 + Meta 🟢 = Ja bateu meta mas SUMIU → risco de perda
  Ciclo 🔴 + Meta 🔴 = ALERTA MAXIMO → intervencao urgente
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 6: DRAFT 2 — LOG DE ATENDIMENTOS (24 COLUNAS)
# ═══════════════════════════════════════════════════════════════════════════

## 6.1 LAYOUT

```
COLUNAS MANUAIS (consultor preenche):
Col  1: DATA                    Data       Data do contato
Col  2: CNPJ                    Texto      Chave do cliente
Col  3: NOME FANTASIA           Texto      Puxa do DRAFT 1
Col  4: UF                      Texto      Puxa do DRAFT 1
Col  5: CONSULTOR               Texto      Quem atendeu
Col  6: RESULTADO ***            Dropdown   1 dos 12 resultados
Col  7: MOTIVO ***               Dropdown   1 dos 10 motivos
Col  8: WHATSAPP                 SIM/NAO
Col  9: LIGACAO                  SIM/NAO
Col 10: LIG. ATENDIDA            SIM/NAO
Col 11: NOTA DO DIA              Texto      Observacao livre
Col 12: MERCOS ATUALIZADO        SIM/NAO

COLUNAS AUTO-CALCULADAS (motor de regras):
Col 13: SITUACAO                 Texto      Puxa do DRAFT 1
Col 14: ESTAGIO FUNIL ***        Texto      Motor: SITUACAO + RESULTADO
Col 15: FASE ***                 Texto      Motor: jornada do cliente
Col 16: TIPO DO CONTATO ***      Texto      Motor: tipo atendimento
Col 17: TEMPERATURA ***          Texto      Motor: chance de compra
Col 18: TENTATIVA ***            Texto      Motor: T1/T2/T3/T4
Col 19: GRUPO DASH ***           Texto      Motor: FUNIL/RELAC./NAO VENDA
Col 20: FOLLOW-UP ***            Data       Motor: data proximo contato
Col 21: ACAO FUTURA ***          Texto      Motor: proxima acao
Col 22: ACAO DETALHADA ***       Texto      Motor: descricao
Col 23: SINALEIRO CICLO          Emoji      DIAS vs CICLO do DRAFT 1
Col 24: SINALEIRO META           Emoji      REALIZADO vs META da PROJECAO
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 7: MOTOR DE REGRAS — LOGICA CENTRAL
# ═══════════════════════════════════════════════════════════════════════════

## 7.1 ESTAGIO DO FUNIL (posicao real na jornada)

```
REGRA: SITUACAO + RESULTADO → ESTAGIO

PROSPECT + qualquer 1o contato         → PROSPECCAO
QUALQUER + EM ATENDIMENTO              → EM ATENDIMENTO
QUALQUER + ORCAMENTO                   → ORCAMENTO
QUALQUER + CADASTRO                    → EM ATENDIMENTO
QUALQUER + VENDA                       → POS-VENDA
ATIVO + RELACIONAMENTO                 → CS / RECOMPRA
ATIVO + FOLLOW UP 7/15                 → CS / RECOMPRA
ATIVO + SUPORTE                        → RELACIONAMENTO
INAT.REC + RELACIONAMENTO              → CS / RECOMPRA (salvando)
INAT.ANT + RELACIONAMENTO              → RELACIONAMENTO (recuperando)
QUALQUER + PERDA/FECHOU                → PERDA / NUTRICAO

NAO ATENDE / NAO RESPONDE / RECUSOU    → MANTEM estagio anterior!
                                         So avanca TENTATIVA
```

REGRA CRITICA: Quando nao atende, o ESTAGIO nao muda. O cara continua
onde estava. So a tentativa avanca (T1→T2→T3→T4→NUTRICAO).

## 7.2 FASE (momento na jornada especifica da situacao)

```
ATIVO + EM ATENDIMENTO     → EM ATENDIMENTO
ATIVO + ORCAMENTO          → ORCAMENTO
ATIVO + VENDA              → POS-VENDA
ATIVO + NAO ATENDE         → RECOMPRA (continua tentando)
ATIVO + RELACIONAMENTO     → CS
ATIVO + FOLLOW UP          → CS / RECOMPRA
ATIVO + SUPORTE            → RELACIONAMENTO
ATIVO + PERDA              → NUTRICAO

INAT.REC + EM ATENDIMENTO  → SALVAMENTO
INAT.REC + ORCAMENTO       → ORCAMENTO
INAT.REC + VENDA           → POS-VENDA (salvou!)
INAT.REC + NAO ATENDE      → SALVAMENTO
INAT.REC + PERDA           → NUTRICAO

INAT.ANT + EM ATENDIMENTO  → RECUPERACAO
INAT.ANT + ORCAMENTO       → ORCAMENTO
INAT.ANT + VENDA           → POS-VENDA (recuperou!)
INAT.ANT + NAO ATENDE      → RECUPERACAO
INAT.ANT + PERDA           → NUTRICAO

PROSPECT + EM ATENDIMENTO  → PROSPECCAO
PROSPECT + ORCAMENTO       → ORCAMENTO
PROSPECT + CADASTRO        → PROSPECCAO
PROSPECT + VENDA           → POS-VENDA (converteu!)
PROSPECT + NAO ATENDE      → PROSPECCAO
PROSPECT + PERDA           → NUTRICAO
```

## 7.3 TEMPERATURA (chance de comprar AGORA)

```
🔥 QUENTE:
  RESULTADO = ORCAMENTO ou VENDA (ultimos 7 dias)
  OU: Ecommerce com itens no carrinho + nao comprou
  OU: RESULTADO = EM ATENDIMENTO + respondeu rapido

🟡 MORNO:
  RESULTADO = FOLLOW UP 7 ou 15
  OU: RESULTADO = RELACIONAMENTO
  OU: Acessou ecommerce mas nao adicionou itens

❄️ FRIO:
  RESULTADO = NAO ATENDE / NAO RESPONDE (2+ tentativas)
  OU: RESULTADO = RECUSOU LIGACAO
  OU: Sem contato ha mais de 15 dias

💀 PERDIDO:
  RESULTADO = PERDA / FECHOU LOJA
  OU: T4 sem resposta → NUTRICAO
```

## 7.4 TENTATIVAS (estado paralelo ao estagio)

```
Quando RESULTADO = NAO ATENDE / NAO RESPONDE / RECUSOU:

  Se TENTATIVA anterior = vazio → T1
  Se TENTATIVA anterior = T1    → T2
  Se TENTATIVA anterior = T2    → T3
  Se TENTATIVA anterior = T3    → T4
  Se TENTATIVA anterior = T4    → ESTAGIO muda para PERDA/NUTRICAO

Quando RESULTADO = qualquer outro (respondeu):
  TENTATIVA → RESET (volta a vazio)
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 8: CARTEIRA — VISAO 360 (4 MEGA-BLOCOS)
# ═══════════════════════════════════════════════════════════════════════════

## MEGA-BLOCO 1: 🟣 MERCOS (cols 1-43)
Fonte: DRAFT 1 via XLOOKUP por CNPJ
Puxa TODA a vida do cliente no Mercos.

## MEGA-BLOCO 2: 🔵 FUNIL (cols 44-61)
Fonte: DRAFT 2 (ultimo atendimento registrado) via XLOOKUP

```
Col 44: ESTAGIO FUNIL        ← ANCORA 2 (posicao na jornada)
Col 45: PROX. FOLLOW-UP      ← Data proximo contato
Col 46: DATA ULT. ATENDIMENTO ← Quando foi ultimo contato
Col 47: ULTIMO RESULTADO      ← O que aconteceu
Col 48: MOTIVO                ← Por que nao comprou
Col 49: TIPO CLIENTE          ← Maturidade
Col 50: TENTATIVA             ← T1/T2/T3/T4
Col 51: FASE                  ← Momento na jornada
Col 52: ULTIMA RECOMPRA       ← Data ultima recompra
Col 53: 🔥 TEMPERATURA        ← Chance de compra
Col 54: DIAS ATE CONVERSAO    ← Historico de velocidade
Col 55: DATA 1o CONTATO       ← Inicio do relacionamento
Col 56: DATA 1o ORCAMENTO     ← Quando engajou
Col 57: DATA 1a VENDA         ← Quando converteu
Col 58: TOTAL TENTATIVAS      ← Esforco investido
Col 59: PROX. ACAO            ← Acao automatica
Col 60: ACAO DETALHADA        ← Texto descritivo
Col 61: 🚦 SINALEIRO CICLO    ← Urgencia vs ciclo medio
```

## MEGA-BLOCO 3: ⚫ SAP (cols 62-72)
Fonte: BASE SAP via XLOOKUP

```
Col 62: CODIGO CLIENTE SAP    Col 67: NOME DO CANAL
Col 63: DESCRICAO GRUPO       Col 68: TIPO CLIENTE SAP
Col 64: GERENTE NACIONAL      Col 69: MACROREGIAO
Col 65: REPRESENTANTE         Col 70: MICROREGIAO
Col 66: VENDEDOR INTERNO      Col 71: GRUPO CHAVE
                               Col 72: VENDA SAP
```

## MEGA-BLOCO 4: 🟢 ACOMPANHAMENTO (cols 73-257)
15 colunas × 12 meses = 180 + headers

### ESTRUTURA POR MES (15 colunas repetidas):

```
┌─────┬──────────────────────────┬───────────────────────────────────────────────┐
│ SUB │ CAMPO                    │ FONTE V3 (AUTOMATICO)                         │
├─────┼──────────────────────────┼───────────────────────────────────────────────┤
│  1  │ % YTD                    │ =REALIZADO_ACUM ÷ META_ACUM                  │
│  2  │ META YTD                 │ =SOMA(metas ate mes atual) ← ABA PROJECAO    │
│  3  │ REALIZADO YTD            │ =SOMA(realizados ate mes atual)              │
│  4  │ % TRI                    │ =REALIZADO_TRI ÷ META_TRI                   │
│  5  │ META TRI                 │ =SOMA(metas do trimestre) ← ABA PROJECAO    │
│  6  │ REALIZADO TRI            │ =SOMA(realizados do trimestre)              │
│  7  │ % MES                    │ =REALIZADO ÷ META                           │
│  8  │ META MES                 │ ← PUXA da ABA PROJECAO (distribuicao SAP)   │
│  9  │ REALIZADO MES            │ ← PUXA do Rel. Vendas OU DRAFT 2 (=VENDA)  │
│ 10  │ DATA PEDIDO              │ ← PUXA do DRAFT 2 (quando RESULTADO=VENDA)  │
│ 11  │ JUSTIFICATIVA SEMANA 1   │ ← AUTO do DRAFT 2 (resultado da semana 1)   │
│ 12  │ JUSTIFICATIVA SEMANA 2   │ ← AUTO do DRAFT 2 (resultado da semana 2)   │
│ 13  │ JUSTIFICATIVA SEMANA 3   │ ← AUTO do DRAFT 2 (resultado da semana 3)   │
│ 14  │ JUSTIFICATIVA SEMANA 4   │ ← AUTO do DRAFT 2 (resultado da semana 4)   │
│ 15  │ JUSTIFICATIVA MENSAL     │ ← AUTO: resumo consolidado dos resultados   │
└─────┴──────────────────────────┴───────────────────────────────────────────────┘

NADA e preenchido manualmente no ACOMPANHAMENTO.
TUDO puxa automaticamente de alguma fonte.
O consultor so preenche RESULTADO na AGENDA.
```

### LOGICA DAS JUSTIFICATIVAS AUTOMATICAS:

```
JUSTIFICATIVA SEMANA N =
  Buscar no DRAFT 2:
    WHERE CNPJ = este cliente
    AND DATA entre [inicio_semana_N] e [fim_semana_N]
  
  SE encontrou registro:
    RETURN RESULTADO + " - " + MOTIVO (se houver)
    Ex: "ORCAMENTO" ou "NAO ATENDE - PROPRIETARIO INDISPONIVEL"
  
  SE RESULTADO foi VENDA:
    RETURN "VENDA R$ " + VALOR + " - " + DATA
    Ex: "VENDA R$ 2.350 - 12/02/2026 ✅"
  
  SE nao encontrou registro:
    RETURN "-" (sem contato na semana)

JUSTIFICATIVA MENSAL =
  SE teve VENDA no mes:
    "CONVERTEU SEM [N] - TICKET R$ [VALOR]"
  SE teve ORCAMENTO mas nao VENDA:
    "ORCAMENTO PENDENTE - FOLLOW UP"
  SE so teve NAO ATENDE:
    "SEM CONTATO EFETIVO - [N] TENTATIVAS"
  SE nenhum contato:
    "SEM ATENDIMENTO NO MES"
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 9: ALGORITMO DE SCORE — RANKING PARA AGENDA
# ═══════════════════════════════════════════════════════════════════════════

## 9.1 FORMULA COMPOSTA (6 fatores)

```
SCORE = (URGENCIA × 0.30)
      + (VALOR × 0.25)
      + (FOLLOW_UP × 0.20)
      + (SINAL_COMPRA × 0.15)
      + (TENTATIVA × 0.05)
      + (SITUACAO × 0.05)
```

## 9.2 DETALHAMENTO DOS FATORES

### FATOR 1: URGENCIA TEMPORAL (peso 30%)
Fonte: DIAS SEM COMPRA ÷ CICLO MEDIO

```
Ratio < 0.7    →   0 pts  (tranquilo)
Ratio 0.7-1.0  →  30 pts  (atencao, ciclo vencendo)
Ratio 1.0-1.5  →  60 pts  (atrasado!)
Ratio > 1.5    →  90 pts  (emergencia!)
Sem ciclo       →  50 pts  (prospect/novo)
```

### FATOR 2: VALOR DO CLIENTE (peso 25%)
Fonte: CURVA ABC + TIPO CLIENTE

```
Curva A + FIDELIZADO   → 100 pts
Curva A + RECORRENTE   →  80 pts
Curva B + FIDELIZADO   →  70 pts
Curva B + RECORRENTE   →  50 pts
Curva C                →  20 pts
PROSPECT               →  30 pts (potencial desconhecido)
```

### FATOR 3: FOLLOW-UP VENCIDO (peso 20%)
Fonte: PROX. FOLLOW-UP vs HOJE

```
Follow-up e HOJE        → 100 pts
Vencido 1-3 dias        →  80 pts
Vencido 4-7 dias        →  60 pts
Vencido 7+ dias         →  40 pts
Sem follow-up agendado  →   0 pts
```

### FATOR 4: SINAL DE COMPRA (peso 15%)
Fonte: OPORTUNIDADE ECOMMERCE + TEMPERATURA

```
🔥 QUENTE + carrinho     → 100 pts
🔥 QUENTE (orcamento)    →  80 pts
🟡 MORNO (acessou)       →  40 pts
❄️ FRIO                  →   0 pts
```

### FATOR 5: TENTATIVA (peso 5%)
Fonte: TENTATIVA

```
T4 (ultima chance)       → 100 pts
T3 (penultima)           →  50 pts
T1/T2                    →  10 pts
Sem tentativa pendente   →   0 pts
```

### FATOR 6: SITUACAO (peso 5%)
Fonte: SITUACAO MERCOS

```
EM RISCO    →  80 pts
INAT.REC    →  60 pts
ATIVO       →  40 pts
INAT.ANT    →  20 pts
PROSPECT    →  10 pts
```

## 9.3 GERACAO DA AGENDA

```
PASSO 1: FILTRAR quem precisa ser atendido
  ✅ Follow-up vence HOJE ou esta vencido
  ✅ Sinaleiro ciclo 🟡 ou 🔴
  ✅ Oportunidade 🔥 QUENTE (carrinho abandonado)
  ✅ T3/T4 pendente (ultima chance)
  ✅ Sinaleiro meta 🔴 (nao esta batendo meta)

PASSO 2: CALCULAR SCORE de cada um

PASSO 3: ORDENAR por SCORE decrescente

PASSO 4: LIMITAR 40 por consultor/dia

PASSO 5: SEPARAR por BLOCO
  MANHA: ATIVOS + EM RISCO + INAT.REC (quem tem chance)
  TARDE: INAT.ANT + PROSPECTS (mais dificil)

PASSO 6: DISTRIBUIR por TERRITORIO
  1o CIA DA SAUDE/FITLAND → JULIO
  2o Outras redes → DAIANE
  3o SC/PR/RS → MANU
  4o Resto Brasil → LARISSA
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 10: INTEGRACAO SINALEIRO → PROJECAO → CARTEIRA
# ═══════════════════════════════════════════════════════════════════════════

## 10.1 SINALEIRO EXISTENTE (JA CONSTRUIDO)

Dois arquivos Excel ja prontos com metodologia proprietaria VITAO:

```
SINALEIRO_REDES_VITAO.xlsx (5 abas, 220 formulas)
  PARAMETROS: Benchmark R$525/mes/loja, faixas cor, meses periodo
  SINALEIRO:  20 colunas × 8 redes (calculos dinamicos)
  PAINEL:     7 KPIs + ranking por GAP
  PLANO_ACAO: Priorizacao automatica
  CADENCIA:   Frequencia contato por estagio maturidade

REDES_FRANQUIAS_SINALEIRO_v2.xlsx (11 abas, 12.996 formulas)
  RESUMO:          Visao consolidada 8 redes (923 lojas)
  TODAS AS REDES:  Base 923 registros (46 colunas padrao CARTEIRA)
  8 abas por rede: Acompanhamento 143 colunas (45 base + 98 tracking)
```

## 10.2 FORMULA CENTRAL DO SINALEIRO

```
Sinaleiro % = Faturamento Real ÷ Faturamento Potencial × 100
Fat. Potencial = Total Lojas × Benchmark Mensal × Meses Periodo

Benchmark: R$ 525/mes/loja (parametro editavel)
Meses periodo: 11 (Mar/25 a Jan/26)
```

## 10.3 FAIXAS DE COR DO SINALEIRO (maturidade da rede)

```
┌──────────────┬────────┬────────┬───────────────────────────────────────┐
│ COR          │ DE     │ ATE    │ ACAO RECOMENDADA                      │
├──────────────┼────────┼────────┼───────────────────────────────────────┤
│ 🟣 ROXO      │ 0%     │ 1%     │ Prospeccao (rede inexplorada)         │
│ 🔴 VERMELHO  │ 1%     │ 40%    │ Ativacao / Positivacao                │
│ 🟡 AMARELO   │ 40%    │ 60%    │ Sell Out (expandir mix)               │
│ 🟢 VERDE     │ 60%    │ 100%   │ JBP - Joint Business Plan            │
└──────────────┴────────┴────────┴───────────────────────────────────────┘
```

## 10.4 DADOS REAIS ATUAIS DO SINALEIRO

```
┌──────────────────┬──────┬───────┬─────────┬──────────┬────────────┬───────┬──────────┐
│ REDE             │ LOJAS│ CART. │ PROSP.  │ C/VENDA  │ FAT.POT    │ SINAL │ COR      │
├──────────────────┼──────┼───────┼─────────┼──────────┼────────────┼───────┼──────────┤
│ MUNDO VERDE      │ 199  │ 4     │ 195     │ 1        │ R$1.253.700│ 1,4%  │ VERMELHO │
│ BIOMUNDO         │ 167  │ 5     │ 162     │ 1        │ R$1.052.100│ 1,4%  │ VERMELHO │
│ CIA DA SAUDE     │ 163  │ 19    │ 144     │ 12       │ R$1.026.900│ 2,6%  │ VERMELHO │
│ ARMAZEM FITSTORE │ 114  │ 0     │ 114     │ 0        │ R$ 718.200 │ 0%    │ ROXO     │
│ FITLAND          │ 89   │ 46    │ 43      │ 9        │ R$ 560.700 │ 29,8% │ VERMELHO │
│ DIVINA TERRA     │ 85   │ 14    │ 71      │ 5        │ R$ 535.500 │ 10,0% │ VERMELHO │
│ VIDA LEVE        │ 81   │ 18    │ 63      │ 8        │ R$ 510.300 │ 8,0%  │ VERMELHO │
│ TUDO EM GRAOS    │ 25   │ 1     │ 24      │ 1        │ R$ 157.500 │ 6,2%  │ VERMELHO │
├──────────────────┼──────┼───────┼─────────┼──────────┼────────────┼───────┼──────────┤
│ TOTAL            │ 923  │ 107   │ 816     │ 102      │ R$5.330.325│ 6,2%  │ VERMELHO │
└──────────────────┴──────┴───────┴─────────┴──────────┴────────────┴───────┴──────────┘
GAP total: R$ 4.999.526
```

## 10.5 ESTRUTURA DO SINALEIRO POR REDE (8 cols/mes, 143 total)

Cada aba de rede ja tem este layout operacional:

```
Area 1 (cols A-AT, 45 colunas): Base CARTEIRA padrao
Area 2 (cols AV-EM, 98 colunas): Acompanhamento 12 meses × 8 cols

Bloco mensal (8 colunas por mes):
  1. META R$     ← Input (azul)
  2. REAL R$     ← Input (azul)
  3. % MES       ← =IF(AND(META="",REAL=""),"",IFERROR(REAL/META,0))
  4. SEM 1       ← Input (acompanhamento semanal)
  5. SEM 2       ← Input
  6. SEM 3       ← Input
  7. SEM 4       ← Input
  8. RESUMO MES  ← Input/Formula

Mapeamento por mes:
  JAN/26: AV-BC | FEV/26: BD-BK | MAR/26: BL-BS | ABR/26: BT-CA
  MAI/26: CB-CI | JUN/26: CJ-CQ | JUL/26: CR-CY | AGO/26: CZ-DG
  SET/26: DH-DO | OUT/26: DP-DW | NOV/26: DX-EE | DEZ/26: EF-EM
```

## 10.6 COMO CONECTAR: SINALEIRO → PROJECAO → CARTEIRA

```
FLUXO DE DADOS:
═══════════════════════════════════════════════════════════════════════

1. SINALEIRO (macro: REDE → penetracao)
   Responde: "Quanto do potencial desta rede estamos capturando?"
   Nivel: REDE (8 redes × 923 lojas)
   Dados: Total lojas, ativos, prospects, fat potencial, sinaleiro %

2. BASE SAP PROJECAO (macro: GRUPO → meta financeira)
   Responde: "Quanto cada grupo precisa faturar por mes?"
   Nivel: GRUPO CHAVE (20 grupos)
   Dados: Meta mensal JAN-DEZ por grupo, positivacao, leads

3. ABA PROJECAO no CRM (micro: CLIENTE → meta individual)
   Responde: "Quanto ESTE CLIENTE precisa comprar este mes?"
   Nivel: CNPJ individual
   Dados: Meta distribuida + sinaleiro de atingimento

CONEXAO:
  SINALEIRO (rede)  → define MATURIDADE e ACAO RECOMENDADA
  SAP PROJECAO (grupo) → define META FINANCEIRA mensal
  PROJECAO CRM (cliente) → distribui meta + calcula % atingimento
  CARTEIRA ACOMP. → tracking semanal com justificativas do DRAFT 2
```

## 10.7 ABA PROJECAO NO CRM — LAYOUT (~30 COLUNAS)

```
BLOCO IDENTIDADE (4 cols):
  Col A: CNPJ
  Col B: NOME FANTASIA
  Col C: REDE / GRUPO CHAVE
  Col D: CONSULTOR

BLOCO SINALEIRO REDE (5 cols - puxa da planilha Sinaleiro):
  Col E: TOTAL LOJAS REDE
  Col F: SINALEIRO % REDE
  Col G: COR SINALEIRO (ROXO/VERMELHO/AMARELO/VERDE)
  Col H: MATURIDADE REDE
  Col I: ACAO RECOMENDADA REDE

BLOCO META SAP (14 cols - puxa do SAP Projecao):
  Col J: META ANUAL GRUPO
  Col K-V: META JAN a META DEZ (mensal, distribuida ao cliente)
  
  Distribuicao:
    META_CLIENTE = META_GRUPO × (FAT_HIST_CLIENTE ÷ FAT_HIST_GRUPO)
    Se NOVO/PROSPECT: META_GRUPO ÷ LEADS_PROJETADOS

BLOCO REALIZACAO (14 cols - puxa dos Relatorios Vendas):
  Col W: REALIZADO ANUAL ACUM
  Col X-AI: REALIZADO JAN a REALIZADO DEZ

BLOCO INDICADORES (4 cols - calculado):
  Col AJ: % YTD (realizado acum ÷ meta acum)
  Col AK: 🚦 SINALEIRO META (🟢≥100% | 🟡50-99% | 🔴<50% | ⚫0%)
  Col AL: GAP (meta - realizado)
  Col AM: RANKING (=RANK por GAP decrescente)
```

## 10.8 TRES SINALEIROS NO SISTEMA (RESUMO FINAL)

```
┌──────────────────┬──────────────────────┬─────────────────────────────┬──────────────┐
│ SINALEIRO        │ ONDE FICA            │ O QUE MEDE                  │ FAIXAS       │
├──────────────────┼──────────────────────┼─────────────────────────────┼──────────────┤
│ 🚦 CICLO         │ CARTEIRA col 61      │ Dias sem compra vs ciclo    │ 🟢🟡🔴🟣     │
│                  │                      │ medio do cliente            │              │
│ 🚦 META          │ PROJECAO col AK      │ Realizado vs meta SAP do    │ 🟢🟡🔴⚫     │
│                  │ → replica CARTEIRA   │ cliente                     │              │
│ 🚦 PENETRACAO    │ ABA SINALEIRO        │ Fat real vs fat potencial   │ 🟣🔴🟡🟢     │
│                  │ (planilha separada)  │ da REDE inteira             │ (maturidade) │
└──────────────────┴──────────────────────┴─────────────────────────────┴──────────────┘

HIERARQUIA:
  PENETRACAO (rede) → "A rede esta sendo explorada?"     → Estrategico
  META (cliente)    → "O cliente esta batendo meta?"      → Tatico
  CICLO (compra)    → "O cliente esta no ritmo de compra?"→ Operacional

COMBINACOES CRITICAS PARA AGENDA:
  Ciclo 🔴 + Meta 🔴 + Penetracao 🔴 = PRIORIDADE ABSOLUTA
  Ciclo 🟢 + Meta 🔴 + Penetracao 🔴 = Compra mas pouco (upsell)
  Ciclo 🔴 + Meta 🟢 + Penetracao 🟡 = Bateu meta mas sumiu (risco)
  Ciclo 🟢 + Meta 🟢 + Penetracao 🟢 = Perfeito (manter rotina)
```

## 10.9 COMO A META CHEGA NA JUSTIFICATIVA SEMANAL

```
1. SAP define meta anual por GRUPO CHAVE
   Ex: CIA DA SAUDE → R$ 52.500/mes (JAN)

2. PROJECAO distribui ao CLIENTE
   Ex: Loja X (CIA) → R$ 5.250/mes (10% do historico do grupo)

3. CARTEIRA ACOMPANHAMENTO puxa via XLOOKUP
   META MES = PROJECAO!META_JAN (para coluna do mes)

4. REALIZADO puxa do Relatorio Vendas OU do DRAFT 2 (quando VENDA)

5. JUSTIFICATIVAS puxam do DRAFT 2 (ultimo resultado da semana)

RESULTADO FINAL NA CARTEIRA:
  % MES:  = REALIZADO ÷ META = 45% (🟡)
  META:   R$ 5.250 (veio da PROJECAO)
  REAL:   R$ 2.350 (veio do DRAFT 2 = VENDA)
  DATA:   12/02/2026 (data da venda no DRAFT 2)
  SEM 1:  "NAO ATENDE - T1"
  SEM 2:  "VENDA R$ 2.350 ✅"
  SEM 3:  "-"
  SEM 4:  "-"
  RESUMO: "CONVERTEU SEM 2 - TICKET R$2.350 - META 45%"
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 11: CICLO D+45 — SENSOR DE ADERENCIA
# ═══════════════════════════════════════════════════════════════════════════

## 10.1 MECANICA

```
VENDA (D+0) → POS-VENDA → Follow-up +45 dias uteis
  │
  ▼ (45 dias depois)
CS D+45: Consultor liga → "Quer comprar de novo?"
  │
  ├── SIM → ORCAMENTO → fluxo normal de venda
  │
  ├── NAO (ainda tem estoque) → FOLLOW UP 7
  │   → D+52: Liga de novo → "E agora?"
  │   ├── SIM → ORCAMENTO
  │   └── NAO → FOLLOW UP 15
  │       → D+67: Liga de novo
  │
  └── NAO (sem interesse) → FOLLOW UP 15
      → Continua ate T4 ou ate comprar
```

## 10.2 CASAMENTO COM CICLO MEDIO

```
O D+45 e o GATILHO PADRAO.
O SINALEIRO CICLO antecipa quando ciclo < 45 dias.
O SCORE combina ambos para priorizar a agenda.

GESTOR avalia: % clientes dentro do ciclo por consultor
  🟢 80%+ dentro → Rotina casando com ciclo → BOM
  🔴 60%+ atrasados → Rotina nao casando → AJUSTAR
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 12: VALIDACOES — COMBINACOES PROIBIDAS
# ═══════════════════════════════════════════════════════════════════════════

## 11.1 HARD RULES (NUNCA pode acontecer)

```
❌ PROSPECT + FASE=RECOMPRA/CS/POS-VENDA/SALVAMENTO
❌ PROSPECT + TIPO=ATEND.ATIVOS/INATIVOS
❌ ATIVO + FASE=SALVAMENTO/RECUPERACAO
❌ ATIVO + ACAO=REATIVACAO/SALVAMENTO
❌ INAT.ANT + FASE=CS/RECOMPRA
❌ NOVO + FASE=SALVAMENTO/RECUPERACAO
```

## 11.2 REGRAS DE CONSISTENCIA

```
✅ RESULTADO=VENDA → FASE=POS-VENDA (sempre)
✅ RESULTADO=ORCAMENTO → ESTAGIO=ORCAMENTO (sempre)
✅ RESULTADO=PERDA → FASE=NUTRICAO (sempre)
✅ RESULTADO=CADASTRO → so para PROSPECT/NOVO
✅ VENDA → follow-up=+45d (sempre)
✅ Nao atende → ESTAGIO mantem anterior
```

## 11.3 TERRITORIO (100% correto)

```
PRIORIDADE:
  1o CIA DA SAUDE ou FITLAND → JULIO GADRET (qualquer estado)
  2o Outras redes → DAIANE STAVICKI
  3o SC/PR/RS sem rede → MANU DITZEL
  4o Resto Brasil → LARISSA PADILHA
  Max 40 atendimentos/dia/consultor
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 13: FORMATACAO E CORES
# ═══════════════════════════════════════════════════════════════════════════

```
SITUACAO (aplicar APENAS na celula SITUACAO):
  ATIVO:     #00B050 (verde)
  EM RISCO:  #FFC000 (amarelo)
  INAT.REC:  #FFC000 (amarelo)
  INAT.ANT:  #FF0000 (vermelho)
  NOVO:      #0070C0 (azul)
  PROSPECT:  #7B2FF2 (roxo)

CABECALHO: #2F5496 (azul escuro), fonte branca bold
TEMA: SEMPRE light mode, NUNCA dark mode
TEXTO: MAIUSCULO sem acentos
CNPJ: 14 digitos com zeros a esquerda
TELEFONE: 55+DDD+NUM (13 digitos)
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 14: DADOS REAIS IMUTAVEIS
# ═══════════════════════════════════════════════════════════════════════════

```
REGRA SAGRADA: NUNCA INVENTAR DADOS

Vendas 2025: 957 total
  MAR:17 ABR:53 MAI:78 JUN:111 JUL:84 AGO:113 SET:104 OUT:123 NOV:133 DEZ:45

Carteira JAN/2026: 489 clientes
  105 ativos (21.5%) | 80 inat.rec (16.4%) | 304 inat.ant (62.1%)

Franquias: 923 lojas em 8 redes
Meta anual 2026: R$ 4.747.200
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 15: CODIGO PYTHON — MOTOR DE REGRAS
# ═══════════════════════════════════════════════════════════════════════════

```python
from datetime import date, timedelta

# === FUNCOES AUXILIARES ===

def dia_util(data_base, dias):
    """Calcula data futura em dias uteis (seg-sex)"""
    atual = data_base
    contados = 0
    while contados < dias:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            contados += 1
    return atual

def calcular_situacao(dias_sem_compra, tem_compra, nunca_comprou):
    if nunca_comprou: return "PROSPECT"
    if not tem_compra: return "PROSPECT"
    if dias_sem_compra <= 50: return "ATIVO"
    if dias_sem_compra <= 60: return "EM RISCO"
    if dias_sem_compra <= 90: return "INAT.REC"
    return "INAT.ANT"

def calcular_sinaleiro_ciclo(dias_sem_compra, ciclo_medio):
    if ciclo_medio is None or ciclo_medio == 0: return "🟣"
    if dias_sem_compra <= ciclo_medio: return "🟢"
    if dias_sem_compra <= ciclo_medio + 30: return "🟡"
    return "🔴"

def calcular_sinaleiro_meta(realizado, meta):
    if meta is None or meta == 0: return "⚫"
    pct = realizado / meta
    if pct >= 1.0: return "🟢"
    if pct >= 0.5: return "🟡"
    if realizado == 0: return "⚫"
    return "🔴"

def calcular_tipo_cliente(meses_positivado):
    if meses_positivado == 0: return "PROSPECT"
    if meses_positivado == 1: return "NOVO"
    if meses_positivado <= 3: return "EM DESENVOLVIMENTO"
    if meses_positivado <= 6: return "RECORRENTE"
    return "FIDELIZADO"

def calcular_curva(valor_ult):
    if valor_ult is None: return "C"
    if valor_ult >= 2000: return "A"
    if valor_ult >= 500: return "B"
    return "C"

def definir_consultor(uf, rede, vendedor_ultimo=""):
    rede_upper = (rede or "").upper()
    if "CIA DA SAUDE" in rede_upper or "FITLAND" in rede_upper:
        return "JULIO GADRET"
    redes_daiane = ["DIVINA TERRA","BIOMUNDO","MUNDO VERDE","TUDO EM GRAOS","VIDA LEVE",
                    "BIO MUNDO","ARMAZEM","NATURVIDA","LIGEIRINHO","TRIP","ESMERALDA"]
    if any(r in rede_upper for r in redes_daiane):
        return "CENTRAL - DAIANE"
    if uf in ["SC","PR","RS"]:
        return "MANU DITZEL"
    return "LARISSA PADILHA"

def calcular_oportunidade(itens_carrinho, acesso_b2b, comprou_mes):
    if itens_carrinho and itens_carrinho > 0 and not comprou_mes:
        return "🔥 QUENTE"
    if acesso_b2b and acesso_b2b > 0:
        return "🟡 MORNO"
    return "❄️ FRIO"


# === MOTOR DE REGRAS PRINCIPAL ===

FOLLOW_UP_DIAS = {
    "EM ATENDIMENTO": 2, "ORCAMENTO": 1, "CADASTRO": 2,
    "VENDA / PEDIDO": 45, "RELACIONAMENTO": 7, "FOLLOW UP 7": 7,
    "FOLLOW UP 15": 15, "SUPORTE": 0, "NAO ATENDE": 1,
    "NAO RESPONDE": 1, "RECUSOU LIGACAO": 2, "PERDA / FECHOU LOJA": 0,
}

GRUPO_DASH = {
    "EM ATENDIMENTO": "FUNIL", "ORCAMENTO": "FUNIL",
    "CADASTRO": "FUNIL", "VENDA / PEDIDO": "FUNIL",
    "RELACIONAMENTO": "RELAC.", "FOLLOW UP 7": "RELAC.",
    "FOLLOW UP 15": "RELAC.", "SUPORTE": "RELAC.",
    "NAO ATENDE": "NAO VENDA", "NAO RESPONDE": "NAO VENDA",
    "RECUSOU LIGACAO": "NAO VENDA", "PERDA / FECHOU LOJA": "NAO VENDA",
}

def motor_de_regras(situacao, resultado, estagio_anterior=None, tentativa_anterior=None):
    """
    Recebe SITUACAO + RESULTADO, retorna TODOS os campos calculados.
    """
    r = {}
    
    # FOLLOW-UP
    r['follow_up_dias'] = FOLLOW_UP_DIAS.get(resultado, 0)
    r['grupo_dash'] = GRUPO_DASH.get(resultado, "")
    
    # REGRAS UNIVERSAIS (independe de situacao)
    if resultado == "VENDA / PEDIDO":
        r['estagio_funil'] = "POS-VENDA"
        r['fase'] = "POS-VENDA"
        r['tipo_contato'] = "POS-VENDA / RELACIONAMENTO"
        r['acao_futura'] = "POS-VENDA"
        r['temperatura'] = "🔥 QUENTE"
        r['tentativa'] = None  # reset
        return r
    
    if resultado == "ORCAMENTO":
        r['estagio_funil'] = "ORCAMENTO"
        r['fase'] = "ORCAMENTO"
        r['tipo_contato'] = "NEGOCIACAO"
        r['temperatura'] = "🔥 QUENTE"
        r['tentativa'] = None  # reset
        r['acao_futura'] = _acao_futura_por_situacao(situacao)
        return r
    
    if resultado == "PERDA / FECHOU LOJA":
        r['estagio_funil'] = "PERDA / NUTRICAO"
        r['fase'] = "NUTRICAO"
        r['tipo_contato'] = "PERDA / NUTRICAO"
        r['acao_futura'] = "NUTRICAO"
        r['temperatura'] = "💀 PERDIDO"
        r['tentativa'] = None
        return r
    
    # NAO ATENDE / NAO RESPONDE / RECUSOU → manter estagio, avancar tentativa
    if resultado in ["NAO ATENDE", "NAO RESPONDE", "RECUSOU LIGACAO"]:
        r['estagio_funil'] = estagio_anterior or _estagio_padrao(situacao)
        r['fase'] = _fase_padrao(situacao)
        r['tipo_contato'] = _tipo_contato_por_situacao(situacao)
        r['acao_futura'] = _acao_futura_por_situacao(situacao)
        r['temperatura'] = "❄️ FRIO"
        
        # Avancar tentativa
        seq = {"T1": "T2", "T2": "T3", "T3": "T4"}
        if tentativa_anterior is None:
            r['tentativa'] = "T1"
        elif tentativa_anterior == "T4":
            r['estagio_funil'] = "PERDA / NUTRICAO"
            r['fase'] = "NUTRICAO"
            r['acao_futura'] = "NUTRICAO"
            r['temperatura'] = "💀 PERDIDO"
            r['tentativa'] = "NUTRICAO"
        else:
            r['tentativa'] = seq.get(tentativa_anterior, "T1")
        return r
    
    # DEMAIS RESULTADOS por situacao
    r['tentativa'] = None  # reset quando responde
    r['temperatura'] = "🟡 MORNO"
    
    if resultado == "EM ATENDIMENTO":
        r['estagio_funil'] = "EM ATENDIMENTO"
        if situacao == "PROSPECT":
            r['fase'] = "PROSPECCAO"
            r['tipo_contato'] = "PROSPECCAO"
        elif situacao in ["INAT.REC", "EM RISCO"]:
            r['fase'] = "SALVAMENTO"
            r['tipo_contato'] = "ATEND. CLIENTES INATIVOS"
        elif situacao == "INAT.ANT":
            r['fase'] = "RECUPERACAO"
            r['tipo_contato'] = "ATEND. CLIENTES INATIVOS"
        else:
            r['fase'] = "EM ATENDIMENTO"
            r['tipo_contato'] = "ATEND. CLIENTES ATIVOS"
    
    elif resultado == "CADASTRO":
        r['estagio_funil'] = "EM ATENDIMENTO"
        r['fase'] = "PROSPECCAO"
        r['tipo_contato'] = "PROSPECCAO"
    
    elif resultado == "RELACIONAMENTO":
        if situacao in ["ATIVO", "EM RISCO"]:
            r['estagio_funil'] = "CS / RECOMPRA"
            r['fase'] = "CS"
        elif situacao == "INAT.REC":
            r['estagio_funil'] = "CS / RECOMPRA"
            r['fase'] = "SALVAMENTO"
        else:
            r['estagio_funil'] = "RELACIONAMENTO"
            r['fase'] = "RECUPERACAO"
        r['tipo_contato'] = "POS-VENDA / RELACIONAMENTO"
    
    elif resultado in ["FOLLOW UP 7", "FOLLOW UP 15"]:
        if situacao in ["ATIVO", "EM RISCO"]:
            r['estagio_funil'] = "CS / RECOMPRA"
            r['fase'] = "CS / RECOMPRA"
        else:
            r['estagio_funil'] = estagio_anterior or _estagio_padrao(situacao)
            r['fase'] = _fase_padrao(situacao)
        r['tipo_contato'] = "FOLLOW UP"
    
    elif resultado == "SUPORTE":
        r['estagio_funil'] = "RELACIONAMENTO"
        r['fase'] = "RELACIONAMENTO"
        r['tipo_contato'] = "POS-VENDA / RELACIONAMENTO"
    
    r['acao_futura'] = _acao_futura_por_situacao(situacao)
    return r


def _estagio_padrao(situacao):
    return {
        "ATIVO": "CS / RECOMPRA", "EM RISCO": "CS / RECOMPRA",
        "INAT.REC": "EM ATENDIMENTO", "INAT.ANT": "EM ATENDIMENTO",
        "NOVO": "POS-VENDA", "PROSPECT": "PROSPECCAO",
    }.get(situacao, "EM ATENDIMENTO")

def _fase_padrao(situacao):
    return {
        "ATIVO": "RECOMPRA", "EM RISCO": "SALVAMENTO",
        "INAT.REC": "SALVAMENTO", "INAT.ANT": "RECUPERACAO",
        "NOVO": "POS-VENDA", "PROSPECT": "PROSPECCAO",
    }.get(situacao, "EM ATENDIMENTO")

def _acao_futura_por_situacao(situacao):
    return {
        "ATIVO": "RECOMPRA", "EM RISCO": "SALVAMENTO",
        "INAT.REC": "SALVAMENTO", "INAT.ANT": "REATIVACAO",
        "NOVO": "POS-VENDA", "PROSPECT": "PROSPECCAO",
    }.get(situacao, "ATENDIMENTO")

def _tipo_contato_por_situacao(situacao):
    return {
        "ATIVO": "ATEND. CLIENTES ATIVOS", "EM RISCO": "ATEND. CLIENTES ATIVOS",
        "INAT.REC": "ATEND. CLIENTES INATIVOS", "INAT.ANT": "ATEND. CLIENTES INATIVOS",
        "NOVO": "ATEND. CLIENTES ATIVOS", "PROSPECT": "PROSPECCAO",
    }.get(situacao, "ATEND. CLIENTES ATIVOS")


# === SCORE PARA RANKING DA AGENDA ===

def calcular_score(dias_sem_compra, ciclo_medio, curva, tipo_cliente,
                   follow_up_date, hoje, oportunidade, temperatura,
                   tentativa, situacao):
    
    # Fator 1: Urgencia temporal (30%)
    if ciclo_medio and ciclo_medio > 0:
        ratio = dias_sem_compra / ciclo_medio
        if ratio < 0.7: f1 = 0
        elif ratio <= 1.0: f1 = 30
        elif ratio <= 1.5: f1 = 60
        else: f1 = 90
    else:
        f1 = 50
    
    # Fator 2: Valor do cliente (25%)
    valor_map = {
        ("A","FIDELIZADO"):100, ("A","RECORRENTE"):80,
        ("B","FIDELIZADO"):70, ("B","RECORRENTE"):50,
        ("C",None):20, ("A",None):60, ("B",None):40,
    }
    f2 = valor_map.get((curva, tipo_cliente), valor_map.get((curva, None), 20))
    if situacao == "PROSPECT": f2 = 30
    
    # Fator 3: Follow-up vencido (20%)
    if follow_up_date:
        delta = (hoje - follow_up_date).days
        if delta == 0: f3 = 100
        elif delta <= 3: f3 = 80
        elif delta <= 7: f3 = 60
        elif delta > 7: f3 = 40
        else: f3 = 0
    else:
        f3 = 0
    
    # Fator 4: Sinal de compra (15%)
    if oportunidade == "🔥 QUENTE": f4 = 100
    elif temperatura == "🔥 QUENTE": f4 = 80
    elif oportunidade == "🟡 MORNO": f4 = 40
    else: f4 = 0
    
    # Fator 5: Tentativa (5%)
    tent_map = {"T4": 100, "T3": 50, "T2": 10, "T1": 10}
    f5 = tent_map.get(tentativa, 0)
    
    # Fator 6: Situacao (5%)
    sit_map = {"EM RISCO": 80, "INAT.REC": 60, "ATIVO": 40, "INAT.ANT": 20, "PROSPECT": 10}
    f6 = sit_map.get(situacao, 20)
    
    score = (f1 * 0.30) + (f2 * 0.25) + (f3 * 0.20) + (f4 * 0.15) + (f5 * 0.05) + (f6 * 0.05)
    return round(score, 1)


# === VALIDACAO ===

def validar_registro(situacao, estagio, fase, tipo_contato, acao, resultado):
    erros = []
    
    if situacao == "PROSPECT":
        if fase in ["RECOMPRA","CS","POS-VENDA","SALVAMENTO"]:
            erros.append(f"PROSPECT nao pode ter FASE={fase}")
        if tipo_contato in ["ATEND. CLIENTES ATIVOS","ATEND. CLIENTES INATIVOS"]:
            erros.append(f"PROSPECT nao pode ter TIPO={tipo_contato}")
    
    if situacao == "ATIVO":
        if fase in ["SALVAMENTO","RECUPERACAO"]:
            erros.append(f"ATIVO nao pode ter FASE={fase}")
        if acao in ["REATIVACAO","SALVAMENTO"]:
            erros.append(f"ATIVO nao pode ter ACAO={acao}")
    
    if situacao == "INAT.ANT":
        if fase in ["CS","RECOMPRA"]:
            erros.append(f"INAT.ANT nao pode ter FASE={fase}")
    
    if resultado == "VENDA / PEDIDO" and fase != "POS-VENDA":
        erros.append(f"VENDA deve ter FASE=POS-VENDA, nao {fase}")
    
    if resultado == "ORCAMENTO" and estagio != "ORCAMENTO":
        erros.append(f"ORCAMENTO deve ter ESTAGIO=ORCAMENTO, nao {estagio}")
    
    if resultado == "CADASTRO" and situacao not in ["PROSPECT","NOVO"]:
        erros.append(f"CADASTRO so para PROSPECT/NOVO, nao {situacao}")
    
    return erros
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 16: CHECKLIST DE VALIDACAO (ANTES DE ENTREGAR)
# ═══════════════════════════════════════════════════════════════════════════

```
[ ] 1.  Nenhuma combinacao proibida (Parte 11)
[ ] 2.  Todas colunas calculadas seguem motor de regras (Parte 7)
[ ] 3.  Territorio 100% correto (Parte 11.3)
[ ] 4.  Cores APENAS na celula SITUACAO (Parte 12)
[ ] 5.  Follow-up em dias uteis (seg-sex)
[ ] 6.  CNPJ 14 digitos, textos MAIUSCULO sem acentos
[ ] 7.  Max 40 atendimentos/dia/consultor
[ ] 8.  SCORE calculado e agenda ordenada
[ ] 9.  Nenhum dado fabricado
[ ] 10. PROSPECT nunca tem RECOMPRA/CS/POS-VENDA/SALVAMENTO
[ ] 11. ATIVO nunca tem SALVAMENTO/RECUPERACAO/REATIVACAO
[ ] 12. RESULTADO determina ESTAGIO/FASE/ACAO (nao aleatorio)
[ ] 13. CADASTRO so para PROSPECT/NOVO
[ ] 14. VENDA sempre gera FASE=POS-VENDA e follow-up +45d
[ ] 15. NAO ATENDE mantem estagio anterior, so avanca tentativa
[ ] 16. ACOMPANHAMENTO puxa automatico (justificativas do DRAFT 2)
[ ] 17. META puxa da aba PROJECAO (distribuicao SAP)
[ ] 18. Dois sinaleiros distintos (ciclo + meta)
```


# ═══════════════════════════════════════════════════════════════════════════
# PARTE 17: ERROS HISTORICOS — NUNCA REPETIR
# ═══════════════════════════════════════════════════════════════════════════

```
 1. 742% duplicacao (resolvido com Two-Base Architecture)
 2. Dados aleatorios sem causa-efeito
 3. 74% territorio errado
 4. Grupo Dashboard confundido com Estagio Funil
 5. PROSPECT com CS (combinacao impossivel)
 6. ATIVO com SALVAMENTO
 7. Acao futura desconectada do resultado
 8. Fase sem logica de jornada
 9. Cores na linha inteira em vez da celula
10. Dark mode
11. Campos de inteligencia 100% vazios (DIAS, CICLO, CURVA, SINALEIRO)
12. ACOMPANHAMENTO todo manual (deve ser automatico)
13. META sem fonte (deve vir da PROJECAO SAP)
```
