# FASE 0 — ABA REGRAS (Foundation)
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

Você vai construir a **aba REGRAS** de uma planilha CRM Excel (.xlsx) para a VITAO Alimentos, distribuidora B2B de alimentos naturais em Curitiba-PR. Esta aba é a **fundação** — todas as outras abas dependem dela para dropdowns, validações e cálculos automáticos.

**Ferramenta:** openpyxl (Python). Fórmulas Excel reais, NUNCA hardcoded.
**Arquivo:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
**Aba:** `REGRAS` (criar como 1ª aba do workbook)
**Font padrão:** Arial 10
**Tema:** Light (nunca dark mode)

---

## ESTRUTURA DA ABA REGRAS

A aba REGRAS contém **5 tabelas nomeadas** (Named Ranges) que alimentam dropdowns e fórmulas das demais abas.

### TABELA 1: RESULTADO → FOLLOW-UP (colunas A-C)

| LINHA | A: RESULTADO | B: DIAS_FOLLOWUP | C: AÇÃO_PADRÃO |
|-------|-------------|-----------------|----------------|
| 1 | **HEADER** | **HEADER** | **HEADER** |
| 2 | EM ATENDIMENTO | 2 | Retornar contato |
| 3 | ORÇAMENTO | 1 | Cobrar retorno orçamento |
| 4 | CADASTRO | 2 | Acompanhar cadastro |
| 5 | VENDA/PEDIDO | 45 | Pós-venda / CS |
| 6 | RELACIONAMENTO | 7 | Manter contato ativo |
| 7 | FOLLOW UP 7 | 7 | Retornar em 7 dias |
| 8 | FOLLOW UP 15 | 15 | Retornar em 15 dias |
| 9 | SUPORTE | 0 | Sem follow-up automático |
| 10 | NÃO ATENDE | 1 | Tentar novamente (escalona T+1) |
| 11 | NÃO RESPONDE | 1 | Tentar novamente (escalona T+1) |
| 12 | RECUSOU LIGAÇÃO | 2 | Mudar canal (WhatsApp) |
| 13 | PERDA/FECHOU LOJA | 0 | Terminal — sem follow-up |

**Named Range:** `TAB_RESULTADO` → `REGRAS!$A$2:$A$13`
**Named Range:** `TAB_RESULTADO_FOLLOWUP` → `REGRAS!$A$2:$C$13`

**Regras especiais:**
- DIAS_FOLLOWUP = 0 significa SEM follow-up automático
- NÃO ATENDE / NÃO RESPONDE / RECUSOU LIGAÇÃO → escalona contador de TENTATIVA no LOG
- PERDA/FECHOU LOJA → status terminal, remove do fluxo ativo

---

### TABELA 2: TIPO DO CONTATO (colunas E-F)

| LINHA | E: TIPO_CONTATO | F: DESCRIÇÃO |
|-------|----------------|-------------|
| 1 | **HEADER** | **HEADER** |
| 2 | PROSPECÇÃO | 1º contato com prospect/lead que nunca comprou |
| 3 | NEGOCIAÇÃO | Processo ativo (orçamento, amostra, negociação) |
| 4 | FOLLOW UP | Retorno agendado de contato anterior |
| 5 | ATENDIMENTO CLIENTES ATIVOS | Cliente dentro do ciclo de compra |
| 6 | ATENDIMENTO CLIENTES INATIVOS | Cliente ultrapassou ciclo (salvamento/recuperação) |
| 7 | PÓS-VENDA/RELACIONAMENTO | CS, verificar se vendeu no PDV |
| 8 | MOTIVO/PAROU DE COMPRAR | Investigar por quê parou (feedback diretoria/fábrica) |

**Named Range:** `TAB_TIPO_CONTATO` → `REGRAS!$E$2:$E$8`

---

### TABELA 3: MOTIVO (colunas H-I)

| LINHA | H: MOTIVO | I: CATEGORIA |
|-------|----------|-------------|
| 1 | **HEADER** | **HEADER** |
| 2 | PRODUTO NÃO VENDEU/SEM GIRO | PRODUTO |
| 3 | PREÇO ALTO/MARGEM | COMERCIAL |
| 4 | PREFERIU CONCORRENTE | COMERCIAL |
| 5 | PROBLEMA LOGÍSTICO | OPERACIONAL |
| 6 | PROBLEMA FINANCEIRO | FINANCEIRO |
| 7 | AINDA TEM ESTOQUE | CICLO |
| 8 | FECHOU LOJA | TERMINAL |
| 9 | SEM INTERESSE | REJEIÇÃO |
| 10 | VIAJANDO/INDISPONÍVEL | TEMPORÁRIO |
| 11 | 1º CONTATO/SEM MOTIVO | INICIAL |

**Named Range:** `TAB_MOTIVO` → `REGRAS!$H$2:$H$11`

**IMPORTANTE:** "PRODUTO NÃO VENDEU/SEM GIRO" é o dado mais crítico para a fábrica/diretoria. Se ≥35% dos motivos forem este, o DASH gera alerta automático pro comitê de quarta-feira.

---

### TABELA 4: SITUAÇÃO → STATUS (colunas K-N)

| LINHA | K: SITUAÇÃO | L: DIAS_MIN | M: DIAS_MAX | N: COR_HEX |
|-------|-----------|-----------|-----------|-----------|
| 1 | **HEADER** | **HEADER** | **HEADER** | **HEADER** |
| 2 | ATIVO | 0 | 50 | 00B050 |
| 3 | EM RISCO | 51 | 60 | FFC000 |
| 4 | INAT.REC | 61 | 90 | FFC000 |
| 5 | INAT.ANT | 91 | 9999 | FF0000 |
| 6 | PROSPECT | — | — | BDD7EE |
| 7 | LEAD | — | — | BDD7EE |

**Named Range:** `TAB_SITUACAO` → `REGRAS!$K$2:$K$7`
**Named Range:** `TAB_SITUACAO_REGRAS` → `REGRAS!$K$2:$N$7`

**Cores IMUTÁVEIS (não alterar jamais):**
- ATIVO = `#00B050` (verde)
- INAT.REC = `#FFC000` (amarelo)
- INAT.ANT = `#FF0000` (vermelho)
- PROSPECT/LEAD = `#BDD7EE` (azul claro)

---

### TABELA 5: CONSULTORES (colunas P-R)

| LINHA | P: CONSULTOR | Q: TERRITÓRIO | R: REDES |
|-------|-------------|--------------|---------|
| 1 | **HEADER** | **HEADER** | **HEADER** |
| 2 | MANU DITZEL | SC, PR, RS | — |
| 3 | LARISSA PADILHA | Resto do Brasil | — |
| 4 | JULIO GADRET | — | CIA DA SAUDE, FITLAND |
| 5 | DAIANE STAVICKI | — | DIVINA TERRA, BIOMUNDO, MUNDO VERDE, VIDA LEVE, TUDO EM GRAOS |
| 6 | CENTRAL | — | — |

**Named Range:** `TAB_CONSULTOR` → `REGRAS!$P$2:$P$6`

---

### TABELA 6: LISTAS AUXILIARES (colunas T-V)

| T: SIM_NAO | U: TIPO_ACAO | V: FASE |
|-----------|-------------|--------|
| SIM | ATIVO | ABERTURA |
| NÃO | RECEPTIVO | ATIVAÇÃO |
| | | CS/RECOMPRA |
| | | ATENÇÃO |
| | | SALVAR |
| | | PERDA |
| | | NUTRIÇÃO |

**Named Ranges:**
- `TAB_SIM_NAO` → `REGRAS!$T$2:$T$3`
- `TAB_TIPO_ACAO` → `REGRAS!$U$2:$U$3`
- `TAB_FASE` → `REGRAS!$V$2:$V$8`

**Cores das FASES:**
- CS/RECOMPRA = `#C6EFCE` (verde claro)
- ATENÇÃO/SALVAR = `#FFC000` (amarelo)
- PERDA/NUTRIÇÃO = `#FFC7CE` (vermelho claro)
- ABERTURA/ATIVAÇÃO = `#BDD7EE` (azul claro — só prospects)

---

## FORMATAÇÃO VISUAL

### Headers (linha 1 de cada tabela)
- Font: Arial 10, Bold, cor branca
- Fill: `#1F4E79` (azul escuro)
- Alignment: center
- Border: thin all

### Dados (linhas 2+)
- Font: Arial 10, regular, preta
- Fill: branco ou alternado `#F2F2F2` (zebra)
- Border: thin all
- Alignment: left (texto), center (números)

### Larguras de coluna
- Texto longo (RESULTADO, TIPO_CONTATO, MOTIVO, DESCRIÇÃO): 35
- Números (DIAS): 15
- Cores (HEX): 12
- Consultores: 25
- Território: 30

---

## NAMED RANGES CONSOLIDADOS (criar todos)

```
TAB_RESULTADO          = REGRAS!$A$2:$A$13
TAB_RESULTADO_FOLLOWUP = REGRAS!$A$2:$C$13
TAB_TIPO_CONTATO       = REGRAS!$E$2:$E$8
TAB_MOTIVO             = REGRAS!$H$2:$H$11
TAB_SITUACAO           = REGRAS!$K$2:$K$7
TAB_SITUACAO_REGRAS    = REGRAS!$K$2:$N$7
TAB_CONSULTOR          = REGRAS!$P$2:$P$6
TAB_SIM_NAO            = REGRAS!$T$2:$T$3
TAB_TIPO_ACAO          = REGRAS!$U$2:$U$3
TAB_FASE               = REGRAS!$V$2:$V$8
```

---

## INSTRUÇÕES PARA O CLAUDE

1. Criar workbook novo com openpyxl
2. Renomear aba padrão para "REGRAS"
3. Popular todas as 6 tabelas exatamente como especificado
4. Criar TODOS os Named Ranges listados
5. Aplicar formatação (headers azul escuro, zebra dados, borders)
6. Definir larguras de colunas
7. Congelar painel na linha 1
8. Salvar como `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
9. Rodar `python scripts/recalc.py` para validar
10. NÃO criar dados fictícios — apenas as tabelas de referência

**IMPORTANTE:** Esta aba é a FUNDAÇÃO. Todas as outras abas vão referenciar estes Named Ranges para dropdowns (Data Validation) e fórmulas (VLOOKUP/INDEX/MATCH). Se algo estiver errado aqui, TUDO quebra.

---

## VALIDAÇÃO (checklist antes de entregar)

- [ ] 12 resultados na TAB_RESULTADO (nenhum faltando)
- [ ] 7 tipos de contato na TAB_TIPO_CONTATO
- [ ] 10 motivos na TAB_MOTIVO
- [ ] 6 situações na TAB_SITUACAO (com cores corretas)
- [ ] 5 consultores na TAB_CONSULTOR (+ CENTRAL)
- [ ] 7 fases na TAB_FASE
- [ ] TODOS os Named Ranges criados e apontando para ranges corretos
- [ ] Zero erros de fórmula (rodar recalc.py)
- [ ] Headers formatados (azul escuro, bold, branco)
- [ ] Font Arial 10 em toda a aba
