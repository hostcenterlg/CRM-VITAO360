# FASE 4 — ABA DASH ATENDIMENTOS (7 Blocos Verticais)
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

A **aba DASH** é o painel de controle gerencial. Empilha 7 blocos verticais (~60 linhas) que o CEO pode rolar de cima pra baixo. Todas as fórmulas são COUNTIFS/SOMASES referenciando a aba LOG.

**CEO é autista, altamente inteligente, prefere formatos resumidos. Vertical scroll only — sem scroll horizontal.**

**Pré-requisitos:** Abas REGRAS, CARTEIRA e LOG existem.

**Ferramenta:** openpyxl
**Arquivo:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
**Aba:** `DASH` (inserir após DRAFT 2)
**Font:** Arial 10 | Tema: Light
**Largura máxima:** ~16 colunas (A-P)

---

## BLOCO 1 — FILTROS (linhas 1-3)

| CÉL | CONTEÚDO | TIPO |
|-----|----------|------|
| A1 | 📊 DASHBOARD ATENDIMENTOS | Merge A1:P1, font 14 bold |
| A2 | VENDEDOR: | Label |
| B2 | (dropdown) | Data Validation → TAB_CONSULTOR + "TODOS" |
| D2 | PERÍODO DE: | Label |
| E2 | (data início) | Data, default = 1º dia mês atual |
| G2 | ATÉ: | Label |
| H2 | (data fim) | Data, default = HOJE() |
| A3 | (vazio — separador) | — |

**Named Cells:**
- `FILTRO_VENDEDOR` = DASH!$B$2
- `FILTRO_DATA_INI` = DASH!$E$2
- `FILTRO_DATA_FIM` = DASH!$H$2

**Helper para fórmulas (usar em todas COUNTIFS):**
- Se FILTRO_VENDEDOR = "TODOS", não filtrar por consultor
- Padrão COUNTIFS: `=CONT.SES(LOG!$B:$B, SE(FILTRO_VENDEDOR="TODOS","*",FILTRO_VENDEDOR), LOG!$A:$A, ">="&FILTRO_DATA_INI, LOG!$A:$A, "<="&FILTRO_DATA_FIM, ...)`

**NOTA:** CONT.SES não suporta wildcard condicional inline. Solução:
```excel
=SE(FILTRO_VENDEDOR="TODOS",
  CONT.SES(LOG!$A:$A,">="&FILTRO_DATA_INI, LOG!$A:$A,"<="&FILTRO_DATA_FIM, LOG!$M:$M,"VENDA/PEDIDO"),
  CONT.SES(LOG!$B:$B,FILTRO_VENDEDOR, LOG!$A:$A,">="&FILTRO_DATA_INI, LOG!$A:$A,"<="&FILTRO_DATA_FIM, LOG!$M:$M,"VENDA/PEDIDO"))
```

---

## BLOCO 2 — KPIs RESUMO (linhas 4-8, 6 cards em merge cells)

Layout: 6 KPIs em cells mescladas 2×2 cada

| KPI | POSIÇÃO | FÓRMULA | COR FUNDO |
|-----|---------|---------|-----------|
| CONTATOS | A4:B5 | Total linhas no LOG (período+vendedor) | `#D1FAE5` verde claro |
| VENDAS | C4:D5 | COUNTIFS RESULTADO="VENDA/PEDIDO" | `#DBEAFE` azul claro |
| ORÇAMENTOS | E4:F5 | COUNTIFS RESULTADO="ORÇAMENTO" | `#FEF3C7` amarelo claro |
| NÃO ATENDE | G4:H5 | COUNTIFS RESULTADO="NÃO ATENDE" | `#FEE2E2` vermelho claro |
| % CONVERSÃO | I4:J5 | =VENDAS/(CONTATOS-NÃO ATENDE-NÃO RESPONDE)×100 | `#EDE9FE` roxo claro |
| MERCOS OK | K4:L5 | =COUNTIFS(MERCOS="SIM")/CONTATOS×100 | `#CCFBF1` teal claro |

Cada KPI:
- Linha superior: Label (font 9, bold)
- Linha inferior: Valor (font 20, bold)

---

## BLOCO 3 — DASH CONTATOS & FUNIL (linhas 10-21, matriz 8×16)

**Título:** Merge A9:P9 → "CONTATOS & FUNIL POR TIPO" | fill `#1F4E79`, font branca

### Layout da matriz:

| | A: TIPO | B: TOTAL | C: WA | D: LIG | E: ATEND | F: Ñ ATEND | | G: EM AT. | H: ORÇ | I: CAD | J: VENDA | | K: FU7 | L: FU15 | M: SUP | | N: Ñ RESP | O: REC.LIG | P: PERDA |
|---|---------|---------|-------|--------|----------|------------|---|---------|--------|--------|----------|---|--------|---------|--------|---|---------|-----------|---------|

**Linhas (10-20):**

| LINHA | A: TIPO DO CONTATO |
|-------|-------------------|
| 10 | (HEADER) |
| 11 | PROSPECÇÃO |
| 12 | NEGOCIAÇÃO |
| 13 | FOLLOW UP |
| 14 | ATEND. CLIENTES ATIVOS |
| 15 | ATEND. CLIENTES INATIVOS |
| 16 | PÓS-VENDA/RELACIONAMENTO |
| 17 | MOTIVO/PAROU DE COMPRAR |
| 18 | (vazio) |
| 19 | **TOTAL** |
| 20 | (vazio separador) |

**Fórmula padrão célula (ex: B11 = Total Prospecção):**
```excel
=SE($B$2="TODOS",
  CONT.SES(LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$L:$L,$A11),
  CONT.SES(LOG!$B:$B,$B$2, LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$L:$L,$A11))
```

**Fórmula cruzamento (ex: G11 = Prospecção com resultado EM ATENDIMENTO):**
```excel
=SE($B$2="TODOS",
  CONT.SES(LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$L:$L,$A11, LOG!$M:$M,G$10),
  CONT.SES(LOG!$B:$B,$B$2, LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$L:$L,$A11, LOG!$M:$M,G$10))
```

**Linha TOTAL:** =SOMA(coluna) para cada coluna.

**Sub-headers (linha 10):** Agrupar visualmente:
- B: TOTAL (fill cinza)
- C-F: 📱📞 CONTATOS (fill `#DBEAFE`)
- G-J: 🔄 FUNIL (fill `#D1FAE5`)
- K-M: 🤝 RELACIONAMENTO (fill `#FEF3C7`)
- N-P: ❌ NÃO VENDA (fill `#FEE2E2`)

---

## BLOCO 4 — DASH TIPO × RESULTADO (linhas 22-33, matriz 8×13)

**Título:** Merge A21:P21 → "TIPO DO CONTATO × RESULTADO COMPLETO" | fill `#1F4E79`

Mesma estrutura do Bloco 3 mas com TODOS os 12 RESULTADOS como colunas:

| | A: TIPO | B: TOTAL | C: EM AT. | D: ORÇ | E: CAD | F: VENDA | G: RELAC | H: FU7 | I: FU15 | J: SUP | K: Ñ AT | L: Ñ RESP | M: REC.LIG | N: PERDA |
|---|---------|---------|---------|--------|--------|----------|---------|--------|---------|--------|---------|----------|-----------|---------|

Linhas: mesmos 7 tipos + TOTAL
Fórmulas: idênticas ao Bloco 3 (CONT.SES cruzado)

---

## BLOCO 5 — DASH MOTIVOS (linhas 35-48)

**Título:** Merge A34:P34 → "POR QUE NÃO COMPRAM — INTELIGÊNCIA DIRETORIA" | fill `#C00000` (vermelho escuro), font branca

| | A: MOTIVO | B: TOTAL | C: % DO TOTAL | D: PROSPECÇÃO | E: ATIVOS | F: INATIVOS | G: PÓS-VENDA |
|---|----------|---------|-------------|-------------|---------|-----------|------------|

**Linhas (36-46):**
10 motivos + linha TOTAL

**Fórmula B36 (Total por motivo):**
```excel
=SE($B$2="TODOS",
  CONT.SES(LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$N:$N,$A36),
  CONT.SES(LOG!$B:$B,$B$2, LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$N:$N,$A36))
```

**Fórmula C36 (% do total):**
```excel
=SE(B$46>0,B36/B$46,0)
```
Formato: 0.0%

**⚠ ALERTA AUTOMÁTICO:**
Na célula A48, fórmula:
```excel
=SE(C36>=0.35,"⚠ ALERTA: 'PRODUTO NÃO VENDEU' ≥35% — REPORTAR COMITÊ QUARTA","")
```
Font: 12, bold, vermelho. Merge A48:P48.

---

## BLOCO 6 — DASH FORMA DO CONTATO (linhas 50-55)

**Título:** Merge A49:P49 → "FORMA DO CONTATO" | fill `#1F4E79`

| | A: FORMA | B: TOTAL | C: % |
|---|---------|---------|------|
| 50 | (header) | | |
| 51 | 📱 WHATSAPP (apenas) | COUNTIFS WA=SIM, LIG=NÃO | % |
| 52 | 📞 LIGAÇÃO (apenas) | COUNTIFS WA=NÃO, LIG=SIM | % |
| 53 | 📱📞 WHATSAPP + LIGAÇÃO | COUNTIFS WA=SIM, LIG=SIM | % |
| 54 | **TOTAL** | SOMA | 100% |

---

## BLOCO 7 — DASH PRODUTIVIDADE (linhas 57-63)

**Título:** Merge A56:P56 → "PRODUTIVIDADE POR CONSULTOR" | fill `#1F4E79`

| | A: CONSULTOR | B: CONTATOS | C: VENDAS | D: ORÇ. | E: CADASTROS | F: % CONVERSÃO | G: NÃO ATENDE | H: PERDA | I: MERCOS OK |
|---|------------|-----------|---------|--------|------------|-------------|-------------|--------|-----------|

**Linhas:**
| LINHA | A |
|-------|---|
| 58 | MANU DITZEL |
| 59 | LARISSA PADILHA |
| 60 | JULIO GADRET |
| 61 | DAIANE STAVICKI (CENTRAL) |
| 62 | **TOTAL TIME** |

**Fórmula B58 (Contatos Manu):**
```excel
=CONT.SES(LOG!$B:$B,"MANU DITZEL", LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2)
```

**% CONVERSÃO (F):**
```excel
=SE((B58-G58-CONT.SES(LOG!$B:$B,$A58, LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$M:$M,"NÃO RESPONDE"))>0,
  C58/(B58-G58-CONT.SES(LOG!$B:$B,$A58, LOG!$A:$A,">="&$E$2, LOG!$A:$A,"<="&$H$2, LOG!$M:$M,"NÃO RESPONDE")),0)
```
Formato: 0.0%

**Formatação condicional % CONVERSÃO:**
- ≥20% → fill `#C6EFCE` (bom)
- 10-19% → fill `#FEF3C7` (médio)
- <10% → fill `#FFC7CE` (baixo)

---

## FORMATAÇÃO GERAL

### Títulos de bloco:
- Font: Arial 12, bold, branca
- Fill: `#1F4E79` (azul escuro)
- Merge across width
- Altura: 25

### Headers de tabela:
- Font: Arial 9, bold
- Fill conforme sub-grupo (cores especificadas acima)
- Border: thin all
- Alignment: center

### Dados:
- Font: Arial 10
- Border: thin all
- Números: center
- Linhas TOTAL: bold, fill `#D9E2F3` (azul pálido)

### Larguras:
- Col A (labels): 35
- Demais: 12-15

---

## INSTRUÇÕES PARA O CLAUDE

1. Abrir workbook existente
2. Criar aba "DASH" após DRAFT 2
3. Implementar sequencialmente: FILTROS → KPIs → Bloco 3-7
4. Todas fórmulas = CONT.SES referenciando LOG
5. Respeitar condição FILTRO_VENDEDOR = "TODOS" (sem filtro consultor)
6. Merge cells para títulos e KPIs
7. Formatação condicional onde especificado
8. ALERTA automático motivos (>=35%)
9. Named Cells para filtros (FILTRO_VENDEDOR, FILTRO_DATA_INI, FILTRO_DATA_FIM)
10. Rodar `python scripts/recalc.py` — aceitar que fórmulas mostram 0 (LOG vazio é normal)

**CRÍTICO:**
- Fórmulas em PORTUGUÊS (CONT.SES, SE, SOMA, HOJE)
- Layout VERTICAL — 7 blocos empilhados, ~60 linhas
- Sem scroll horizontal (máx 16 colunas)
- CEO vê de cima pra baixo
- Referências ao LOG: coluna A=DATA, B=CONSULTOR, H=WHATSAPP, I=LIGAÇÃO, L=TIPO CONTATO, M=RESULTADO, N=MOTIVO, Q=MERCOS

---

## VALIDAÇÃO (checklist)

- [ ] 7 blocos na ordem correta (vertical)
- [ ] Filtros funcionam (vendedor + período)
- [ ] KPIs calculam corretamente
- [ ] Matrizes TIPO×RESULTADO com CONT.SES
- [ ] ALERTA motivos ≥35%
- [ ] Produtividade por consultor
- [ ] % CONVERSÃO com fórmula correta (excluindo NÃO ATENDE/RESPONDE)
- [ ] Formatação condicional em % CONVERSÃO
- [ ] Merge cells nos títulos e KPIs
- [ ] Máximo 16 colunas (sem scroll horizontal)
- [ ] Zero erros (recalc.py)
