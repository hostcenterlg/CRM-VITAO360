# Phase 9: Blueprint v2 - Research

**Researched:** 2026-02-17
**Domain:** Excel CRM Architecture (openpyxl + formula engineering + column grouping)
**Confidence:** HIGH

## Summary

Phase 9 is the largest and most complex phase of the entire CRM project. The scope -- confirmed during discuss-phase -- goes far beyond the original roadmap description of "expand from 46 to 81 columns." The REAL scope is to **recreate the complete CARTEIRA tab from V12 COM_DADOS** (263 columns, 8,302 rows, 6 super-groups with 3-level grouping, anchors, and a full intelligence engine) in the V13 file, PLUS build 4 individual AGENDA tabs and a retrofeeding rules engine.

Critical finding: **V13 currently has NO CARTEIRA tab at all.** The V13 file (CRM_VITAO360_V13_PROJECAO.xlsx) contains only 5 tabs: PROJECAO (537 rows, 80 cols), LOG (20,830 rows, 21 cols), DASH (41 rows), REDES_FRANQUIAS_v2, and COMITE. The CARTEIRA must be created from scratch, pulling formulas from DRAFT 1, DRAFT 2, PROJECAO, LOG, and REGRAS.

The V12 CARTEIRA has been fully audited: 263 columns, freeze panes at AR6, auto_filter A3:JE1863, 210 grouped columns across 3 outline levels, ~956K formulas estimated across 8,302 rows. The 6 super-groups are: MERCOS (A-AQ), FUNIL (AR-BJ), SAP/STATUS SAP/DADOS CADASTRAIS SAP (BK-BY), and FATURAMENTO (BZ-JC with 186 columns for 12 months x 15 sub-columns each).

**Primary recommendation:** Build the CARTEIRA in phases: (1) Audit and map all V12 formulas and column dependencies, (2) Create DRAFT 1 and DRAFT 2 supporting tabs in V13, (3) Build CARTEIRA skeleton with 263 columns + 3-level grouping, (4) Inject formulas referencing V13 tab names, (5) Build REGRAS motor with 63 combinations, (6) Create 4 AGENDA tabs, (7) Validate the complete intelligence pipeline.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Estrutura da CARTEIRA (Escopo Real):**
- V12 COM_DADOS (263 colunas, 8.302 linhas) e a referencia completa a ser replicada
- Recriar do ZERO apos auditoria profunda do V12 -- nao copiar, ENTENDER e reconstruir
- Primeiro auditar racional, formulas e logica, depois decidir quais abas de suporte recriar (DRAFTs, AGENDA, REGRAS)
- CARTEIRA = visao 360 do cliente na MESMA LINHA, trackeado por CNPJ
- 4 visoes analiticas por cliente: MERCOS (comportamental), FUNIL (atendimento), SAP (cadastral), FATURAMENTO (acompanhamento)
- Base de dados: SAP completo (ativos com/sem atendimento + inativos + bloqueados) + Mercos (ativos + inativos recente/antigo + prospects)
- Regra de ouro: Se tem pedido no Mercos -> OBRIGATORIAMENTE tem cadastro no SAP. Prospects Mercos podem nao estar no SAP.

**Fluxo de Dados entre Abas:**
- META por cliente vem da aba PROJECAO (rateio proporcional ja calculado na Fase 1)
- REALIZADO mensal puxa do DRAFT 1 (vendas Mercos -- fonte primaria de vendas)
- JUSTIFICATIVA semanal (S1-S4) = formula automatica que puxa resultado do atendimento + consultor pode sobrescrever manualmente
- Se tem VENDA -> justificativa = "VENDA/PEDIDO"
- Se nao tem VENDA -> puxa status real: ORCAMENTO, PROSPECCAO, EM ATENDIMENTO, NEGOCIACAO, CADASTRO, RECOMPRA, CS, POS-VENDA, RELACIONAMENTO, NUTRICAO, PERDA
- Fontes de formulas: auditar V12 para definir melhor mapeamento no V13

**Ancoras:**
- Cada super grupo tem uma ancora principal (coluna que fica visivel quando grupo colapsado)
- Cada sub-grupo dentro do super grupo tambem tem ancora propria
- Ancoras ja foram pensadas e projetadas no V12 -- respeitar 100% como estao
- Servem para: facilitacao de visualizacao e analise de inteligencia para conferir agenda dos consultores
- Modos de uso: grupo todo oculto com so ancora principal OU cada sub-grupo com suas ancoras visiveis

**Organizacao em Grupos:**
- Seguir 6 secoes do V12 (NAO 8 do roadmap): MERCOS, FUNIL, SAP, STATUS SAP, DADOS CADASTRAIS SAP, FATURAMENTO
- Manter 3 niveis de agrupamento [+]: Nivel 1 (super grupo) -> Nivel 2 (sub-grupo) -> Nivel 3 (detalhe)
- Header 3 linhas: L1=super grupo, L2=sub-grupo, L3=nome da coluna
- Visual: Mix do V12 (estrutura de cores e emojis) + padrao PROJECT.md (tema LIGHT, Arial 9pt dados, 10pt headers)
- Bloco FATURAMENTO: 186 colunas (12 meses x 15 sub-colunas: %YTD, META, REALIZADO, %TRI, META, REALIZADO, %MES, META, REALIZADO, DATA PEDIDO, JUSTIFICATIVA S1-S4, JUSTIFICATIVA MENSAL)

**Motor de Inteligencia (3 Camadas):**

Camada 1 -- Ranking de Prioridade (quem atender primeiro):
- Criterios: Score/Temperatura/Prioridade, Estagio funil, Ciclo medio de compra, Dias sem comprar, Curva ABC, Acesso e-commerce B2B, Momento ouro de recompra
- Status do cliente: Novo, Recorrente, Em Desenvolvimento, Fidelizado, Maduro
- Quantas vezes ja comprou na vida
- Follow-ups pendentes (orcamentos passados, cadastros D+7/D+15/D+30, 1a/2a/3a tentativa WhatsApp/ligacao)

Camada 2 -- Pipeline vs Meta (vai bater a meta?):
- Meta mensal / dias restantes = meta diaria do consultor
- Quantos clientes em "momento ouro" (negociacao/orcamento/cadastro/pedido)?
- Ticket medio do consultor e dos clientes
- Conta fecha ou nao?

Camada 3 -- Alerta de Urgencia (plano B):
- Se pipeline atual NAO cobre a meta -> ALERTA: "Precisa buscar prospeccao EXTERNA urgente"
- Janela de 7 dias para prospeccao virar pedido
- Calculo: clientes em pipe * ticket medio vs gap de meta restante

DECISAO CRITICA: Criar TODAS as 3 camadas na Fase 9, mesmo que o V12 so tenha a Camada 1.

**Ciclo Automatico de Retroalimentacao:**
- Consultor preenche resultado (VENDA, ORCAMENTO, etc.) -> CRM gera automaticamente ACAO FUTURA + DATA + O QUE FAZER
- Follow-ups retroalimentam a agenda: resultado de hoje -> follow-up -> vira tarefa do dia X -> consultor executa -> novo resultado
- 50-60 tarefas/dia/consultor FIXO: se pipeline insuficiente, completar com prospeccoes
- Filtro DATA + CONSULTOR na CARTEIRA = AGENDA DO DIA com tarefas priorizadas + ancoras

**Motor de Regras:**
- Resultados possiveis: VENDA/PEDIDO, ORCAMENTO, CADASTRO, PROSPECCAO, EM ATENDIMENTO, NEGOCIACAO, RECOMPRA, CS, POS-VENDA, RELACIONAMENTO, NUTRICAO, PERDA, NAO ATENDE/NAO RESPONDE
- Cada resultado gera: estagio funil, temperatura, fase, acao futura, data proxima acao
- Auditar V12 aba REGRAS + pasta auditoria + toda documentacao disponivel para mapear regras completas

**Visao Diaria e Operacao:**
- CRM completo: SOMENTE Leandro (gestor) tem acesso
- Consultores: recebem apenas aba AGENDA filtrada
- 4 abas AGENDA individuais: AGENDA LARISSA, AGENDA DAIANE, AGENDA MANU, AGENDA JULIO
- Puxam da CARTEIRA via formula (filtro: nome consultor + data followup)
- Consultor ve: DATA + NOME + CNPJ fixos + ancoras minimizaveis + colunas verdes (resultado selecionavel via dropdown)
- Dropdowns com opcoes pre-definidas das REGRAS

**Ciclo operacional diario:**
1. Manha: Leandro extrai dados Mercos -> cola no DRAFT 1
2. CRM recalcula automaticamente (CARTEIRA + AGENDAs)
3. Leandro copia AGENDA de cada consultor -> planilha separada no Drive
4. Envia pro consultor via call matinal
5. Dia: consultor preenche resultados
6. Noite: consultor devolve agenda preenchida via call de acompanhamento
7. Leandro cola resultados no DRAFT 2
8. CRM recalcula -> gera agenda do dia seguinte
9. Repete

### Claude's Discretion

- Definir melhor formato de freeze panes apos auditar V12
- Definir quais abas de suporte (DRAFTs, REGRAS) precisam ser recriadas vs adaptadas
- Definir exatamente quais formulas apontam para onde (DRAFT 1, PROJECAO, LOG, etc.)
- Escolher melhor abordagem para auto_filter vs slicer
- Definir formato visual exato das colunas verdes (preenchimento consultor)
- Definir se Camadas 2 e 3 do motor sao formulas ou calculo auxiliar
- Propor melhor estrutura para alertas de urgencia (conditional formatting, coluna extra, etc.)

### Deferred Ideas (OUT OF SCOPE)

- Automatizacao do retorno de dados (consultor preenche -> dados voltam automaticamente ao CRM) -- futuro
- Automacao de extracao Mercos (hoje manual) -- possivel automacao futura
- Mais de 60 tarefas/dia por consultor (sistema adaptativo baseado em performance)
</user_constraints>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.5 | Excel .xlsx creation, formulas, grouping, styles | Already in use, proven in Phases 1-8 |
| pandas | (installed) | Data manipulation for client roster building | ETL of source data |
| json | stdlib | Intermediate data exchange between scripts | Consistent with prior phases |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unicodedata | stdlib | Accent stripping for sheet name lookup | PROJECAO sheet has cedilla accent |
| datetime | stdlib | Date calculations for follow-up rules | JUSTIFICATIVA date ranges |
| pathlib | stdlib | Cross-platform path handling | All file references |
| shutil | stdlib | Backup creation before modifications | V13 safety copies |

### Not Needed

| Library | Reason Not Needed |
|---------|-------------------|
| lxml/zipfile | No slicer manipulation in CARTEIRA (XML Surgery not needed) |
| rapidfuzz | No fuzzy matching (all CNPJs already resolved in Phases 2-6) |
| xlrd | No .xls files involved |

**Python path:** `/c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe`

## Architecture Patterns

### V12 CARTEIRA Structure (263 columns, audited)

```
SUPER-GROUP 1: MERCOS (cols A-AQ, 43 cols)
  L0 anchor: A = NOME FANTASIA (R1: "MERCOS")
  L1 sub-groups:
    IDENTIDADE: B-H (CNPJ, RAZAO SOCIAL, UF, CIDADE, EMAIL, TELEFONE, DATA CADASTRO)
    REDE: I-K (REDE REGIONAL, TIPO CLIENTE, ULT REGISTRO MERCOS)
    EQUIPE: L-M (CONSULTOR, VENDEDOR ULTIMO PEDIDO)
    STATUS: N-O (SITUACAO, PRIORIDADE)
    COMPRA: P-R, S (DIAS SEM COMPRA, DATA ULT PEDIDO, VALOR ULT PEDIDO, CICLO MEDIO)
  L3 sub-sub-group:
    ECOMMERCE: T-X (ACESSO B2B, ACESSOS PORTAL, ITENS CARRINHO, VALOR B2B, OPORTUNIDADE)
  L0 VENDAS block: Y-AJ (TOTAL PERIODO + 11 monthly sales -- note: dates as serial numbers in R3)
  L1 anchor: AK = TIPO CLIENTE (anchor for recurrence sub-group)
  L2 sub-group:
    RECORRENCIA: AL-AQ (N COMPRAS, CURVA ABC, MESES POSITIVADO, MEDIA MENSAL, TICKET MEDIO, MESES LISTA)

SUPER-GROUP 2: FUNIL (cols AR-BJ, 19 cols)
  L0 anchor: AR = ESTAGIO FUNIL (R1: "FUNIL")
  L1 sub-groups:
    PIPELINE: AS-AW (PROX FOLLOWUP, DATA ULT ATENDIMENTO, ACAO FUTURA, ULTIMO RESULTADO, MOTIVO)
    PERFIL: AX-AY (TIPO CLIENTE, TENTATIVA)
  L1 anchors:
    MATURIDADE: AZ = FASE, BA = ULTIMA RECOMPRA
    CONVERSAO: BB = TEMPERATURA, BC-BG (DIAS ATE CONVERSAO, DATA 1o CONTATO, DATA 1o ORCAMENTO, DATA 1a VENDA, TOTAL TENTATIVAS)
    ACAO: BH = PROX ACAO, BI = ACAO DETALHADA
    SINAL: BJ = SINALEIRO

SUPER-GROUP 3: SAP (cols BK-BP, 6 cols)
  L0: BK = CODIGO DO CLIENTE (R1: "SAP ")
  L1: BL = CNPJ, BM = RAZAO SOCIAL
  BN = CADASTRO (R1: "STATUS SAP"), BO = ATENDIMENTO
  L0: BP = BLOQUEIO

SUPER-GROUP 4: DADOS CADASTRAIS SAP (cols BQ-BY, 9 cols)
  L1: BQ-BY (DESC GRUPO CLIENTE, ZP GERENTE, ZR REPRESENTANTE, ZV VEND INTERNO, CANAL, TIPO CLIENTE, MACROREGIAO, MICROREGIAO, GRUPO CHAVE)

SUPER-GROUP 5: FATURAMENTO (cols BZ-JC, 186 cols = anchor + 4 quarters x sub-cols)
  L0: BZ = VENDA (standalone, no group)
  L0: CA = % ALCANCADO (R1: "FATURAMENTO", R2: "ACOMPANHAMENTO")
  Per Quarter (Q1=CB, Q2=DV, Q3=FP, Q4=HJ):
    L1 anchor: %Qn (e.g., CB = % Q1)
    Per Month (3 per quarter):
      L2 header: Month name (e.g., CC=JAN R1)
        L2: %YTD, L3: META, L3: REALIZADO
        L2: %TRI, L3: META, L3: REALIZADO
        L2: %MES, L3: META MES, L3: REALIZADO MES
        L3: DATA PEDIDO
        L3: JUSTIFICATIVA S1, S2 (L0), S3 (L0), S4 (L0)
        L3: JUSTIFICATIVA MENSAL
      = 15 sub-columns per month x 12 months = 180 + Q anchors + CA + BZ = 186 total
```

### V12 Formula Dependencies Map

```
CARTEIRA formulas reference these tabs:
  DRAFT 1 (Mercos data):
    - Simple INDEX/MATCH: =IFERROR(INDEX('DRAFT 1'!$col:$col,MATCH($B{row},'DRAFT 1'!$B:$B,0)),"")
    - Used for: DIAS SEM COMPRA (P), CICLO MEDIO (S), N COMPRAS (AL), CURVA ABC (AM),
      MESES POSITIVADO (AN), MEDIA MENSAL (AO), TICKET MEDIO (AP), TIPO CLIENTE (AX)
    - Key: match on $B (CNPJ) in both tabs

  DRAFT 2 (Agenda/Atendimento data):
    - Complex CSE (array formula): =IFERROR(INDEX('DRAFT 2'!$col:$col,MATCH(1,INDEX(('DRAFT 2'!$D:$D=$B{row})*('DRAFT 2'!$A:$A=MAX(IF('DRAFT 2'!$D:$D=$B{row},'DRAFT 2'!$A:$A))),0,1),0)),"")
    - This finds the MOST RECENT record for a CNPJ by: matching CNPJ in D, finding MAX date in A, then extracting value
    - Used for: ESTAGIO FUNIL (AR), PROX FOLLOWUP (AS), ACAO FUTURA (AU), ULTIMO RESULTADO (AV),
      MOTIVO (AW), TENTATIVA (AY), FASE (AZ), PROX ACAO (BH), ACAO DETALHADA (BI)
    - JUSTIFICATIVA S1-S4: =COUNTIFS('DRAFT 2'!$D:$D,$B{row},'DRAFT 2'!$A:$A,">="&DATE(year,month,start),'DRAFT 2'!$A:$A,"<="&DATE(year,month,end))

  REGRAS (Motor de Regras lookup table):
    - TEMPERATURA: =IFERROR(INDEX(REGRAS!$G$220:$G$282,MATCH(N{row}&AQ{row},REGRAS!$A$220:$A$282&REGRAS!$B$220:$B$282,0)),"")
    - This is a 2-column concatenated MATCH: SITUACAO & RESULTADO -> TEMPERATURA
    - Motor rows 220-282 = 63 combinations (SITUACAO x RESULTADO -> outputs)

  PROJECAO:
    - META per client: referenced from PROJECAO col L (proportional annual meta)

  Calculated internally:
    - TOTAL PERIODO (Y): =SUM(Z{row}:AJ{row})
    - SINALEIRO (BJ): Complex IF/LET using CICLO MEDIO, DIAS SEM COMPRA, SITUACAO
    - % ALCANCADO (CA): =CX{row} (current month % MES)
    - JUSTIFICATIVA MENSAL: =SUM(CM:CP) (sum of 4 weekly justificativas)
```

### V13 Current Tab Structure

```
V13 file: CRM_VITAO360_V13_PROJECAO.xlsx
  1. PROJECAO (537 rows, 80 cols) -- Phase 1 complete, 19,224 formulas
  2. LOG (20,830 rows, 21 cols) -- Phase 4 complete
  3. DASH (41 rows) -- Phase 5 complete
  4. REDES_FRANQUIAS_v2 -- Phase 7 complete
  5. COMITE -- Phase 8 complete

MISSING (must create in Phase 9):
  - CARTEIRA (263 cols, ~534+ rows)
  - DRAFT 1 (Mercos staging, ~45 cols, ~554 rows)
  - DRAFT 2 (Atendimento staging, ~31 cols, grows infinitely)
  - REGRAS (reference tables, ~283 rows, ~13 cols)
  - AGENDA LARISSA
  - AGENDA DAIANE
  - AGENDA MANU
  - AGENDA JULIO
```

### Recommended Build Sequence

```
Phase 9 execution order:

  PLAN 1: AUDIT + PREPARATION
    - Deep audit of V12 all formula patterns (classify every column)
    - Map every formula reference to its V13 equivalent tab/column
    - Build complete column specification JSON (263 entries)
    - Decide DRAFT 1/DRAFT 2/REGRAS structure for V13

  PLAN 2: SUPPORTING TABS
    - Create REGRAS tab (reference tables + motor 63 combinations)
    - Create DRAFT 1 tab (Mercos staging with headers + data from existing sources)
    - Create DRAFT 2 tab (Atendimento staging with headers, initially empty)
    - Populate DRAFT 1 with client data from sap_mercos_merged.json + ecommerce_matched.json

  PLAN 3: CARTEIRA SKELETON + MERCOS/FUNIL BLOCKS
    - Create CARTEIRA tab with 263 columns
    - Set 3 header rows (L1 super-group, L2 sub-group, L3 column name)
    - Apply 3-level column grouping (outline_level 1/2/3)
    - Inject MERCOS block formulas (INDEX/MATCH from DRAFT 1)
    - Inject FUNIL block formulas (array formulas from DRAFT 2)
    - Set freeze_panes, auto_filter, column widths

  PLAN 4: SAP + FATURAMENTO BLOCKS
    - Inject SAP/STATUS SAP/DADOS CADASTRAIS SAP (static data or VLOOKUP)
    - Build FATURAMENTO mega-block (186 columns, 12 months x 15 sub-columns)
    - Generate monthly META/REALIZADO formulas referencing PROJECAO
    - Generate JUSTIFICATIVA S1-S4 COUNTIFS formulas referencing DRAFT 2
    - Apply conditional formatting

  PLAN 5: INTELLIGENCE ENGINE (3 Layers)
    - Layer 1: Ranking/Score formulas (weighted score from 6 factors)
    - Layer 2: Pipeline vs Meta calculations (daily meta, coverage ratio)
    - Layer 3: Urgency alerts (conditional formatting, gap analysis)
    - Retrofeeding cycle: RESULTADO -> ACAO FUTURA + DATE + TASK

  PLAN 6: 4 AGENDA TABS + VALIDATION
    - Create AGENDA LARISSA/DAIANE/MANU/JULIO
    - Each pulls from CARTEIRA via filter (consultor name + followup date)
    - Fixed columns + anchor columns + green result columns with dropdowns
    - Comprehensive validation (formula count, cross-reference check, grouping)
```

### Pattern: openpyxl Column Grouping (3 levels)

```python
from openpyxl.worksheet.properties import Outline

# Set outline properties: buttons on LEFT side of group (for anchors)
ws.sheet_properties.outlinePr = Outline(summaryBelow=False, summaryRight=False)

# Level 0: Anchor column (always visible, no outline)
# No outline_level set -- stays at default 0

# Level 1: Super-group columns
ws.column_dimensions['B'].outline_level = 1
ws.column_dimensions['B'].hidden = True  # collapsed by default

# Level 2: Sub-group columns
ws.column_dimensions['C'].outline_level = 2
ws.column_dimensions['C'].hidden = True

# Level 3: Detail columns (FATURAMENTO sub-sub-columns)
ws.column_dimensions['D'].outline_level = 3
ws.column_dimensions['D'].hidden = False  # or True based on V12
```

**Verified:** openpyxl 3.1.5 fully supports outline_level 1-7 on column_dimensions. Tested with save/reload -- levels persist correctly.

### Pattern: V12 Array Formula for "Most Recent Record"

```python
# This pattern finds the most recent DRAFT 2 record for a client by CNPJ
# It's a CSE (Ctrl+Shift+Enter) array formula in V12

# ESTAGIO FUNIL (col AR):
formula = (
    '=IFERROR(INDEX(\'DRAFT 2\'!$I:$I,'
    'MATCH(1,INDEX((\'DRAFT 2\'!$D:$D=$B{row})*'
    '(\'DRAFT 2\'!$A:$A=MAX(IF(\'DRAFT 2\'!$D:$D=$B{row},\'DRAFT 2\'!$A:$A))),0,1),0)),"")'
)

# In openpyxl, array formulas use ArrayFormula:
from openpyxl.worksheet.formula import ArrayFormula
# cell.value = ArrayFormula(ref="AR4", text=formula)
# OR simply write the formula as text -- Excel will interpret it
# (openpyxl does NOT need explicit CSE marking for modern Excel's IMPLICIT arrays)
```

**CRITICAL NOTE:** The V12 formulas use `_xlfn.LET` and `_xlpm.` prefixes (e.g., in SINALEIRO formula). These are Excel 365 LAMBDA/LET features. openpyxl can write them as text but they require Excel 365 or later to evaluate. LibreOffice may NOT support `_xlfn.LET`.

### Pattern: FATURAMENTO Monthly Block (15 sub-columns)

```
For each month (JAN through DEZ):
  Col 1: %YTD   (L2 outline)  -- cumulative YTD percentage
  Col 2: META   (L3 outline)  -- cumulative YTD meta
  Col 3: REALIZADO (L3)       -- cumulative YTD realizado
  Col 4: %TRI   (L2)          -- quarter percentage
  Col 5: META   (L3)          -- quarter meta
  Col 6: REALIZADO (L3)       -- quarter realizado
  Col 7: %MES   (L2)          -- month percentage (shown in R1 as "100%")
  Col 8: META   (L3)          -- month meta (SUBTOTAL in R1)
  Col 9: REALIZADO (L3)       -- month realizado (SUBTOTAL in R1)
  Col 10: DATA PEDIDO (L3)    -- ArrayFormula
  Col 11: JUSTIFICATIVA S1 (L3) -- COUNTIFS weekly
  Col 12: JUSTIFICATIVA S2 (L0) -- COUNTIFS weekly
  Col 13: JUSTIFICATIVA S3 (L0) -- COUNTIFS weekly
  Col 14: JUSTIFICATIVA S4 (L0) -- COUNTIFS weekly
  Col 15: JUSTIFICATIVA MENSAL (L3 or L0) -- =SUM(S1:S4)
```

Quarter anchor columns (CB, DV, FP, HJ) at L1 wrap 3 months each.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Column letter calculation | Manual "A","B"..."AA","AB" | openpyxl.utils.get_column_letter() | Handles multi-letter cols (JC=263) |
| CNPJ matching | Custom string matching | Existing sap_mercos_merged.json | Already resolved in Phase 2-3 |
| Array formula injection | Manual CSE marking | openpyxl implicit array support | Modern Excel handles implicit arrays |
| Motor de Regras logic | Python if/else chains | REGRAS tab + INDEX/MATCH lookup | V12 pattern proven, Excel-native recalculation |
| Column grouping | XML manipulation | openpyxl column_dimensions.outline_level | Tested, works with 3 levels |
| Date serial numbers | Manual epoch math | openpyxl date handling | Avoids off-by-one errors |

**Key insight:** The CARTEIRA is fundamentally a FORMULA sheet, not a data sheet. Almost every cell in data rows contains a formula that pulls from DRAFT 1, DRAFT 2, PROJECAO, or REGRAS. The challenge is formula generation (263 columns x N rows), not data processing.

## Common Pitfalls

### Pitfall 1: Formula References to Wrong Tab Names
**What goes wrong:** V12 references `'DRAFT 2'!$D:$D` but V13 may use different tab name, causing #REF!
**Why it happens:** Tab names change between versions. V13 LOG tab was renamed from V12 DRAFT 2 structure.
**How to avoid:** Create a TAB_NAME_MAP constant at the top of every script. Before writing any formula, substitute V12 tab names with V13 equivalents.
**Warning signs:** #REF! errors when opening in Excel, formulas showing "0" or empty when data exists.

### Pitfall 2: V12 Row Count Mismatch
**What goes wrong:** V12 has 8,302 rows but V13 PROJECAO has only 534 clients. Writing 8,302 rows of formulas wastes space and causes performance issues.
**Why it happens:** V12 was pre-allocated for growth. V13 should match actual client count.
**How to avoid:** Use the PROJECAO client roster (534 CNPJs) as the definitive row count. Add buffer rows (~500) for growth. Total: ~1,034 formula rows.
**Warning signs:** Excel sluggishness, file size >10MB, recalculation taking >30 seconds.

### Pitfall 3: _xlfn.LET / _xlpm. Prefix Functions
**What goes wrong:** SINALEIRO formula uses `_xlfn.LET(_xlpm.ciclo,...)` which is Excel 365-only syntax. LibreOffice and older Excel versions show #NAME? error.
**Why it happens:** V12 was created in Excel 365. These are modern dynamic array functions.
**How to avoid:** Rewrite LET formulas as nested IFs for compatibility. The SINALEIRO formula can be expressed without LET: `=IF(P{r}="","",IF(OR(N{r}="PROSPECT",N{r}="LEAD"),"...",IF(N{r}="NOVO","...",IF(AK{r}=0,IF(P{r}<=50,"...",IF(P{r}<=90,"...","...")),IF(P{r}<=AK{r},"...",IF(P{r}<=AK{r}+30,"...","..."))))))`
**Warning signs:** #NAME? errors in any cell, formulas showing `_xlfn.` prefix.

### Pitfall 4: Array Formula Performance with Full-Column References
**What goes wrong:** Formulas like `INDEX('DRAFT 2'!$A:$A,MATCH(...))` search entire columns (1M rows) causing extreme slowness.
**Why it happens:** V12 uses full-column references ($A:$A) for flexibility but this is a known Excel performance killer with array formulas.
**How to avoid:** Use bounded ranges: `$A$3:$A$25000` instead of `$A:$A`. This still allows ample growth while limiting search scope.
**Warning signs:** Excel "Calculating..." status bar, file takes >5 minutes to open.

### Pitfall 5: Conditional Formatting Accumulation
**What goes wrong:** Each save/load cycle with openpyxl can duplicate conditional formatting rules, eventually corrupting the file.
**Why it happens:** openpyxl doesn't always clean up existing rules before adding new ones.
**How to avoid:** When building CARTEIRA from scratch (not modifying existing), this is less risky. Still, apply CF rules ONCE and verify count matches expectation.
**Warning signs:** File size growing with each save, Excel reporting "too many conditional formats."

### Pitfall 6: DRAFT 2 Does Not Exist Yet in V13
**What goes wrong:** CARTEIRA formulas reference DRAFT 2 but V13 has no DRAFT 2 tab -- all formulas return #REF!
**Why it happens:** V13 was built incrementally (phases 1-8) and DRAFT 2 was deferred.
**How to avoid:** DRAFT 2 MUST be created before or simultaneously with CARTEIRA. Even an empty DRAFT 2 with correct headers prevents #REF!.
**Warning signs:** Every FUNIL-block formula showing #REF! on first open.

### Pitfall 7: DRAFT 1 Column Index Mismatch
**What goes wrong:** V12 CARTEIRA formulas reference DRAFT 1 columns by letter (e.g., `$L:$L` = DIAS SEM COMPRA, `$O:$O` = CICLO MEDIO). V13 DRAFT 1 may have different column positions.
**Why it happens:** Phase 3 already populated DRAFT 1 in V13 with a specific column layout that may differ from V12.
**How to avoid:** Audit V13 DRAFT 1 column positions BEFORE writing CARTEIRA formulas. Create a column map: V12_DRAFT1_col -> V13_DRAFT1_col.
**Warning signs:** Formulas pulling wrong data (e.g., CURVA ABC showing a date value).

## Code Examples

### Example 1: Creating CARTEIRA Tab with 3-Level Grouping

```python
from openpyxl.worksheet.properties import Outline
from openpyxl.utils import get_column_letter

def build_carteira_skeleton(wb):
    ws = wb.create_sheet("CARTEIRA")

    # Outline: buttons on LEFT (summaryRight=False)
    ws.sheet_properties.outlinePr = Outline(
        summaryBelow=False, summaryRight=False
    )

    # Define column structure: (col_num, name, super_group, sub_group, outline_level, width, hidden)
    # Level 0 = anchor (always visible)
    # Level 1 = super-group member
    # Level 2 = sub-group member
    # Level 3 = detail (FATURAMENTO sub-sub-cols)

    columns = [
        (1, "NOME FANTASIA", "MERCOS", "ANCORA", 0, 25, False),
        (2, "CNPJ", "MERCOS", "IDENTIDADE", 1, 18, True),
        (3, "RAZAO SOCIAL", "MERCOS", "IDENTIDADE", 2, 30, True),
        # ... etc for all 263 columns
    ]

    for col_num, name, sg, sub, level, width, hidden in columns:
        letter = get_column_letter(col_num)
        ws.column_dimensions[letter].width = width
        if level > 0:
            ws.column_dimensions[letter].outline_level = level
            ws.column_dimensions[letter].hidden = hidden

        # Write headers
        ws.cell(row=1, column=col_num, value=sg if col_num == 1 else None)  # R1: super-group
        ws.cell(row=2, column=col_num, value=sub)  # R2: sub-group
        ws.cell(row=3, column=col_num, value=name)  # R3: column name

    # Freeze panes at AR6 (matching V12)
    ws.freeze_panes = "AR6"

    # Auto filter on row 3
    ws.auto_filter.ref = f"A3:JC{max_row}"

    return ws
```

### Example 2: Generating FATURAMENTO Monthly Block

```python
def write_faturamento_month(ws, start_col, month_num, year, data_start_row, data_end_row):
    """Write 15 sub-columns for one month of FATURAMENTO."""
    month_names = ["JAN","FEV","MAR","ABR","MAI","JUN","JUL","AGO","SET","OUT","NOV","DEZ"]
    month_name = month_names[month_num - 1]

    # Sub-column offsets (0-14)
    # 0=%YTD, 1=META_YTD, 2=REAL_YTD, 3=%TRI, 4=META_TRI, 5=REAL_TRI,
    # 6=%MES, 7=META_MES, 8=REAL_MES, 9=DATA_PEDIDO,
    # 10=JUST_S1, 11=JUST_S2, 12=JUST_S3, 13=JUST_S4, 14=JUST_MENSAL

    outline_levels = [2, 3, 3, 2, 3, 3, 2, 3, 3, 3, 3, 0, 0, 0, 3]
    headers_r3 = [
        "% YTD", "META", "REALIZADO", "% TRI", "META", "REALIZADO",
        "% MES", "META", "REALIZADO", "DATA PEDIDO",
        "JUSTIFICATIVA SEMANA 1", "JUSTIFICATIVA SEMANA 2",
        "JUSTIFICATIVA SEMANA 3", "JUSTIFICATIVA SEMANA 4",
        "JUSTIFICATIVA MENSAL"
    ]

    col = start_col
    for offset, (level, header) in enumerate(zip(outline_levels, headers_r3)):
        letter = get_column_letter(col)
        if level > 0:
            ws.column_dimensions[letter].outline_level = level

        # R1: month name (only on first sub-col)
        if offset == 0:
            ws.cell(row=1, column=col, value=month_name)

        # R3: column header
        ws.cell(row=3, column=col, value=header)

        # Formulas for data rows
        for row in range(data_start_row, data_end_row + 1):
            if offset == 10:  # JUSTIFICATIVA S1
                # Week 1: day 1-7 of the month
                ws.cell(row=row, column=col).value = (
                    f'=COUNTIFS(\'DRAFT 2\'!$D:$D,$B{row},'
                    f'\'DRAFT 2\'!$A:$A,">="&DATE({year},{month_num},1),'
                    f'\'DRAFT 2\'!$A:$A,"<="&DATE({year},{month_num},7))'
                )
            elif offset == 14:  # JUSTIFICATIVA MENSAL
                s1_letter = get_column_letter(col - 4)
                s4_letter = get_column_letter(col - 1)
                ws.cell(row=row, column=col).value = f'=SUM({s1_letter}{row}:{s4_letter}{row})'

        col += 1
```

### Example 3: Building REGRAS Motor (63 Combinations)

```python
def build_regras_motor(ws, start_row=220):
    """Build the SITUACAO x RESULTADO -> outputs lookup table."""
    # Header
    headers = ["SITUACAO", "RESULTADO", "ESTAGIO FUNIL", "FASE",
               "TIPO CONTATO", "ACAO FUTURA", "TEMPERATURA"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=start_row-1, column=c, value=h)

    # 63 combinations from V12 REGRAS rows 220-282
    motor = [
        ("ATIVO", "EM ATENDIMENTO", "EM ATENDIMENTO", "EM ATENDIMENTO",
         "ATEND. CLIENTES ATIVOS", "FECHAR NEGOCIACAO EM ANDAMENTO", "MORNO"),
        ("ATIVO", "ORCAMENTO", "ORCAMENTO", "ORCAMENTO",
         "NEGOCIACAO", "CONFIRMAR ORCAMENTO ENVIADO", "QUENTE"),
        # ... all 63 combinations
    ]

    for i, row_data in enumerate(motor):
        r = start_row + i
        for c, val in enumerate(row_data, 1):
            ws.cell(row=r, column=c, value=val)

    # TEMPERATURA lookup formula in CARTEIRA:
    # =IFERROR(INDEX(REGRAS!$G${start}:$G${end},
    #   MATCH(N{row}&AQ{row},REGRAS!$A${start}:$A${end}&REGRAS!$B${start}:$B${end},0)),"")
```

## State of the Art

| Old Approach (V12) | Current Approach (V13) | Impact |
|---|---|---|
| 8,302 pre-allocated rows | ~534 client rows + ~500 buffer | Performance: ~6x fewer formula evaluations |
| Full-column references ($A:$A) | Bounded ranges ($A$3:$A$25000) | Prevents 1M-row array scans |
| `_xlfn.LET` functions | Nested IF equivalents | LibreOffice/older Excel compatibility |
| DRAFT 2 mixed with LOG | LOG separate (20,830 rows), DRAFT 2 for operational cycle | Two-Base Architecture respected |
| Manual AGENDA single tab | 4 individual AGENDA tabs per consultant | Operational efficiency for daily workflow |
| Only Layer 1 intelligence (ranking) | 3-layer intelligence engine | Pipeline coverage, urgency alerts added |

## Open Questions

1. **DRAFT 1 in V13: Create new or use existing?**
   - What we know: Phase 3 populated a DRAFT 1 in V12 COM_DADOS (not V13). V13 has no DRAFT 1 tab.
   - What's unclear: Whether to copy DRAFT 1 from V12 or create fresh from sap_mercos_merged.json
   - Recommendation: Create fresh DRAFT 1 from sap_mercos_merged.json (Phase 2 output) + ecommerce_matched.json (Phase 6 output). This ensures clean column positions and avoids V12 legacy issues.

2. **Client roster: 534 or 554?**
   - What we know: PROJECAO has 534 rows (from Phase 1). Phase 3 expanded CARTEIRA to 554 rows (including fuzzy-matched and SAP-only clients).
   - What's unclear: Which is the definitive client count for CARTEIRA.
   - Recommendation: Use 554 (the expanded set from Phase 3) as the CARTEIRA roster. Any client in DRAFT 1 or PROJECAO should appear.

3. **FATURAMENTO META source: PROJECAO col L or calculated?**
   - What we know: V12 META columns in FATURAMENTO show None/static values. PROJECAO col L has proportional annual meta.
   - What's unclear: How monthly META is derived (annual/12? seasonal weighting?)
   - Recommendation: META MES = PROJECAO col L / 12 (simple annual/12, consistent with Phase 8 COMITE approach).

4. **Layers 2 and 3: Formula-based or auxiliary tab?**
   - What we know: Layer 1 (ranking/score) exists in V12 as REGRAS section 16. Layers 2-3 are new.
   - What's unclear: Whether pipeline vs meta calculations should be inline formulas or a helper tab.
   - Recommendation: Layer 2 as inline formulas in CARTEIRA (simple arithmetic). Layer 3 as conditional formatting rules (color alerts) + 1-2 summary columns. Avoid auxiliary tabs to keep the architecture simple.

5. **DATA PEDIDO ArrayFormula handling**
   - What we know: V12 uses `<openpyxl.worksheet.formula.ArrayFormula>` for DATA PEDIDO columns. openpyxl can read but may have issues writing ArrayFormula objects.
   - What's unclear: Whether openpyxl 3.1.5 can write CSE-style formulas that Excel interprets correctly.
   - Recommendation: Write DATA PEDIDO as a regular formula (not array). Modern Excel 365 with dynamic arrays can handle INDEX/MATCH without CSE. If issues arise, use a simpler MAXIFS approach: `=IFERROR(MAXIFS('DRAFT 2'!$A:$A,'DRAFT 2'!$D:$D,$B{row}),"")`.

6. **AGENDA formula pattern: INDEX/MATCH filter or FILTER function?**
   - What we know: V12 AGENDA tab is mostly empty (headers only). The user wants formula-driven agenda.
   - What's unclear: Excel 365 has FILTER() and SORT() dynamic array functions which would be ideal. But LibreOffice doesn't support them.
   - Recommendation: Use FILTER() + SORT() for Excel 365 target (Leandro uses Excel). Document that LibreOffice won't support AGENDA tabs. Alternative: Use INDEX/MATCH with helper columns.

## V12 REGRAS Complete Audit (Motor de Regras)

The REGRAS tab in V12 has 283 rows, 13 columns, organized in 17 sections:

| Section | Rows | Content | Count |
|---------|------|---------|-------|
| 1. RESULTADO | 5-20 | 14-16 result types with follow-up days | 14 |
| 2. TIPO DO CONTATO | 23-30 | 7-8 contact types | 7 |
| 3. MOTIVO | 33-55 | 22 motivos with owner | 22 |
| 4. SITUACAO | 58-65 | 7 status values with colors | 7 |
| 5. FASE | 68-77 | 9 lifecycle phases | 9 |
| 6. TIPO CLIENTE | 80-86 | 6 maturity types | 6 |
| 7. CONSULTOR | 89-94 | 5 team members | 5 |
| 8. TENTATIVA | 97-103 | 6 contact protocol steps | 6 |
| 9. SINALEIRO | 106-110 | 4 health indicator colors | 4 |
| 10. LISTAS SIMPLES | 113-130 | 5 dropdown lists | ~18 |
| 11. TIPO ACAO | 133-139 | 6 action types | 6 |
| 12. TIPO PROBLEMA | 142-150 | 8 RNC categories | 8 |
| 13. ACAO FUTURA | 153-200 | 22+26 future actions | 48 |
| 14. TAREFA/DEMANDA | (section 14) | 25 internal tasks | 25 |
| 15. SINALEIRO META | 202-207 | 4 achievement bands | 4 |
| 16. SCORE RANKING | 209-216 | 6 weighted factors | 6 |
| 17. MOTOR DE REGRAS | 219-283 | SITUACAO x RESULTADO matrix | 63 |

**Section 16 (SCORE RANKING)** is the foundation of Layer 1 intelligence:
- URGENCIA TEMPORAL: 30% weight (DIAS SEM COMPRA / CICLO MEDIO)
- VALOR DO CLIENTE: 25% weight (CURVA ABC + TIPO CLIENTE)
- FOLLOW-UP VENCIDO: 20% weight (PROX FOLLOWUP vs TODAY)
- SINAL DE COMPRA: 15% weight (ECOMMERCE + TEMPERATURA)
- TENTATIVA: 5% weight (T1/T2/T3/T4 protocol step)
- SITUACAO: 5% weight (status urgency)

**Section 17 (MOTOR DE REGRAS)** has 63 combinations across 7 SITUACAO values:
- ATIVO: 12 combinations (rows 221-232)
- EM RISCO: 10 combinations (rows 233-242)
- INAT.REC: 9 combinations (rows 243-251)
- INAT.ANT: 9 combinations (rows 252-260)
- PROSPECT: 9 combinations (rows 261-269)
- NOVO: 7 combinations (rows 270-276)
- LEAD: 7 combinations (rows 277-283)

## Sources

### Primary (HIGH confidence)
- V12 COM_DADOS file: `data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` -- full structure audit
- V13 current file: `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` -- verified 5 tabs, no CARTEIRA
- openpyxl 3.1.5 grouping: verified via live test with save/reload
- Phase 8 script patterns: `scripts/phase08_comite_metas/02_build_comite_tab.py`
- REGRAS tab: complete extraction of 283 rows, 17 sections
- CONTEXT.md: 24 decisions from discuss-phase

### Secondary (MEDIUM confidence)
- Audit documents: `Desktop/auditoria conversas sobre agenda atendimento draft 2/` -- 12 files reviewed
- Blueprint v2 log: `Desktop/PASTA DE APOIO PROJETO/AUDITORIA/LOG_CONVERSA_JARVIS_FASE1_BLUEPRINT_V2.md` -- 81-column spec (now superseded by 263-column V12 spec)
- Existing scripts: `v3_carteira.py`, `v3_regras.py`, `motor_regras.py` -- reference implementations

### Tertiary (LOW confidence)
- Formula estimate (~956K formulas in V12 CARTEIRA) -- based on 97-row sample extrapolation. Actual formula patterns in later rows may differ from rows 4-100.
- AGENDA FILTER() recommendation -- not verified if Leandro's Excel version supports dynamic arrays.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- openpyxl 3.1.5 proven in 8 prior phases, grouping verified via test
- Architecture: HIGH -- V12 fully audited (263 cols, all headers, all grouping levels, sample formulas for every section)
- Pitfalls: HIGH -- based on direct experience from Phases 1-8 + documented bugs in audit logs
- Intelligence engine: MEDIUM -- Layers 2-3 are NEW (no V12 precedent), design is from user discussion only
- AGENDA tabs: MEDIUM -- V12 AGENDA tab is mostly empty, formula pattern needs design from scratch

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable domain, no external library changes expected)
