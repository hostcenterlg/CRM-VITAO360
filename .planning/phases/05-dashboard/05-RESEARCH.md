# Phase 5: Dashboard - Research

**Researched:** 2026-02-17
**Domain:** Excel dashboard formulas via openpyxl (COUNTIFS/SUM referencing LOG tab)
**Confidence:** HIGH

## Summary

Phase 5 builds the DASH tab in V13 (CRM_VITAO360_V13_PROJECAO.xlsx). The current V13 has only 2 tabs: PROJECAO (537 rows, 19,224 formulas) and LOG (20,830 records, 20 cols + 1 hidden). The DASH must be created from scratch referencing LOG data via COUNTIFS formulas. There is NO CARTEIRA tab in V13 (only 3 data rows per STATE.md -- expansion deferred to Phase 9), so all DASH CLIENTES blocks that reference CARTEIRA must be deferred.

The existing v3_dash.py (762 lines) provides a complete working implementation but references DRAFT 2 columns (different column mapping). The V12 COM_DADOS has an old DASH (74 rows, 18 cols) also referencing DRAFT 2. Both must be translated to reference the V13 LOG column structure. The approved design (DASH_FINAL_APROVADO.html) shows 3 blocks, while detailed specs (FASE_4_DASH.md) describe 7 blocks with formulas in Portuguese. Since openpyxl requires ENGLISH formulas, all CONT.SES become COUNTIFS, SE becomes IF, SOMA becomes SUM.

**CRITICAL DISCOVERY: LOG data has INCONSISTENT TIPO DO CONTATO values.** The LOG contains 12 different TIPO values including duplicates with different naming (e.g., "ATEND. CLIENTES ATIVOS" vs "ATENDIMENTO CLIENTES ATIVOS", "POS-VENDA / RELACIONAMENTO" vs "POS VENDA / RELACIONAMENTO"). COUNTIFS exact-match formulas will NOT aggregate these correctly. This must be addressed either by normalizing LOG data first or by using additive COUNTIFS in formulas.

**Primary recommendation:** Build DASH with 3 approved blocks from DASH_FINAL_APROVADO.html (matching the 45-row requirement), reference V13 LOG columns, use ENGLISH formulas, and handle TIPO DO CONTATO inconsistency via additive COUNTIFS or LOG data normalization as a prerequisite step.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.x | Read/write Excel OOXML | Already used in all prior phases |
| Python | 3.12.10 | Script runtime | pyenv-managed, consistent across project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| v3_styles.py | local | Shared formatting constants | FILL_DARK, FONT_HEADER, THIN_BORDER, style_cell(), write_header() |
| openpyxl.chart | built-in | BarChart for RESULTADO distribution | Bloco 1 bar chart (optional) |
| openpyxl.worksheet.datavalidation | built-in | Dropdown for VENDEDOR filter | Filter row at top of DASH |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Individual COUNTIFS per TIPO variation | Normalize LOG data first | Normalization is cleaner but modifies LOG; additive formulas are safe but verbose |
| Bar chart via openpyxl | No chart (numbers only) | CEO prefers numbers; chart is nice-to-have, not required |

**Installation:**
```bash
# No new packages needed -- openpyxl already installed
/c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe -c "import openpyxl; print(openpyxl.__version__)"
```

## Architecture Patterns

### V13 Current State (INPUT)
```
CRM_VITAO360_V13_PROJECAO.xlsx
  |-- PROJECAO (537 rows, 80 cols, 19,224 formulas) -- DO NOT TOUCH
  |-- LOG (20,832 rows incl header+title, 21 cols)   -- READ ONLY from DASH
  |-- [DASH] (to be created)                          -- NEW in Phase 5
```

### V13 LOG Column Map (CRITICAL for all formulas)
```
Col  Letter  Header              DASH Usage
1    A       DATA                Date filter: ">="&date_start, "<="&date_end
2    B       CONSULTOR           Consultant filter
3    C       NOME FANTASIA       Not used in DASH
4    D       CNPJ                Not used in DASH
5    E       UF                  Not used in DASH
6    F       REDE/REGIONAL       Not used in core DASH (future REDES dash)
7    G       SITUACAO            Not used in core DASH (CARTEIRA not ready)
8    H       WHATSAPP            Bloco 2: CONTATOS channel counting
9    I       LIGACAO             Bloco 2: CONTATOS channel counting
10   J       LIGACAO ATENDIDA    Bloco 2: CONTATOS channel counting
11   K       TIPO ACAO           Not used in core DASH
12   L       TIPO DO CONTATO     Bloco 1 & 2: Row grouping (7 types)
13   M       RESULTADO           Bloco 1: Column grouping (11 result types)
14   N       MOTIVO              Bloco 3: Motivos counting
15   O       FOLLOW-UP           Not used in DASH
16   P       ACAO                Not used in core DASH
17   Q       MERCOS ATUALIZADO   Bloco 3: % MERCOS per consultant
18   R       FASE                Not used in core DASH
19   S       TENTATIVA           Not used in core DASH
20   T       NOTA DO DIA         Not used in DASH
21   U       ORIGEM_DADO         Hidden metadata, not used
```

### DRAFT 2 -> LOG Column Translation (v3_dash.py reference)
```
v3_dash.py (DRAFT 2)    V13 LOG          Change
$A (DATA)                $A (DATA)        SAME
$B (CNPJ)               $D (CNPJ)        NOT USED in DASH
$E (CONSULTOR)           $B (CONSULTOR)   E -> B
$F (RESULTADO)           $M (RESULTADO)   F -> M
$G (MOTIVO)              $N (MOTIVO)      G -> N
$H (WHATSAPP)            $H (WHATSAPP)    SAME
$I (LIGACAO)             $I (LIGACAO)     SAME
$J (LIG.ATENDIDA)        $J (LIG.ATEND)   SAME
$L (MERCOS)              $Q (MERCOS)      L -> Q
$P (TIPO DO CONTATO)     $L (TIPO CONTATO) P -> L
$S (GRUPO DASH)          N/A              REMOVED (not in V13 LOG)
$W (SINALEIRO CICLO)     N/A              REMOVED (CARTEIRA field)
```

### LOG Data Range
```
Row 1: Title (merged A1:U1)
Row 2: Headers
Row 3: First data row
Row 20832: Last data row (~20,830 records)

FORMULA RANGE: LOG!$A$3:$A$20832 (or LOG!$A:$A for full column)
```

### Recommended DASH Layout (3 Blocks, ~45 rows)

Based on DASH_FINAL_APROVADO.html (Leandro-approved), adapted to V13:

```
DASH Tab Layout:
Row 1:   Title "DASHBOARD JARVIS CRM -- VITAO ALIMENTOS" (merged)
Row 2:   Filters: VENDEDOR dropdown (B2) | PERIODO: date_start (E2) date_end (F2)
Row 3:   (spacer)
Row 4:   KPI Cards (6 merged cells: CONTATOS, VENDAS, ORCAMENTOS, NAO ATENDE, %CONV, MERCOS)
Row 5:   KPI Values
Row 6:   (spacer)
Row 7:   Bloco 1 Title "TIPO DO CONTATO x RESULTADO DO CONTATO"
Row 8:   Headers (13 cols: TIPO | TOTAL | ORCAM | CADAST | RELAC | EM ATEND | SUPORTE | VENDA | N ATENDE | RECUSOU | N RESP | PERDA | FOLLOW UP)
Row 9-15: 7 TIPO DO CONTATO rows
Row 16:  TOTAL row
Row 17:  (spacer)
Row 18:  Bloco 2 Title "CONTATOS REALIZADOS + FUNIL DE VENDA"
Row 19:  Group headers (CANAIS | FUNIL | RELAC | NAO VENDA)
Row 20:  Sub-headers
Row 21-27: 7 TIPO rows with channels + funil breakdown
Row 28:  TOTAL row
Row 29:  (spacer)
Row 30:  Bloco 3 Title "MOTIVOS + PRODUTIVIDADE"
Row 31:  Side-by-side: MOTIVOS (left A-G) | PRODUTIVIDADE (right I-Q)
Row 32:  Motivos headers | Produtividade headers
Row 33-42: 10 motivos | 4 consultors + total
Row 43:  TOTAL motivos
Row 44:  (spacer)
Row 45:  End

TOTAL: ~45 rows (meets requirement)
```

### Formula Pattern: cf() helper rewrite for V13 LOG

The v3_dash.py `cf()` function must be rewritten:

```python
# OLD (DRAFT 2):
def cf(extra_criteria="", use_todos=True):
    date_filter = "'DRAFT 2'!$A$3:$A$5000,\">=\"&$E$2,'DRAFT 2'!$A$3:$A$5000,\"<=\"&$F$2"
    cons_filter = ",'DRAFT 2'!$E$3:$E$5000,$C$2"
    ...

# NEW (V13 LOG):
def cf(extra_criteria="", use_todos=True):
    date_filter = "LOG!$A$3:$A$21000,\">=\"&$E$2,LOG!$A$3:$A$21000,\"<=\"&$F$2"
    cons_filter = ",LOG!$B$3:$B$21000,$C$2"
    if use_todos:
        base_all = f"COUNTIFS({date_filter}{extra_criteria})"
        base_cons = f"COUNTIFS({date_filter}{cons_filter}{extra_criteria})"
        return f'IF(OR($C$2="",$C$2="TODOS"),{base_all},{base_cons})'
    ...
```

**Key changes:**
- `'DRAFT 2'` -> `LOG` (no quotes needed, no spaces in tab name)
- Consultor column: `$E` -> `$B`
- Resultado column: `$F` -> `$M`
- Tipo Do Contato column: `$P` -> `$L`
- Motivo column: `$G` -> `$N`
- WhatsApp column: `$H` -> `$H` (same)
- Ligacao column: `$I` -> `$I` (same)
- Lig.Atendida column: `$J` -> `$J` (same)
- Mercos column: `$L` -> `$Q`
- Data range: `$3:$5000` -> `$3:$21000` (LOG has 20,830 rows)
- Filter cells: `$C$2` vendedor, `$E$2` date start, `$F$2` date end

### Anti-Patterns to Avoid
- **Using LOG!$A:$A (full column references):** With 20,830+ rows, full-column COUNTIFS are SLOW in Excel. Use bounded ranges like `LOG!$A$3:$A$21000`.
- **Accented characters in TIPO labels:** LOG data uses NO ACCENTS ("PROSPECCAO" not "PROSPECAO"), "NAO ATENDE" not "NAO ATENDE"). Formulas must match EXACTLY what's in the LOG.
- **Referencing CARTEIRA:** V13 has no CARTEIRA tab. Any CARTEIRA formulas will produce #REF! errors. DEFER all CARTEIRA blocks.
- **Portuguese function names:** openpyxl writes raw XML. Must use ENGLISH: COUNTIFS, IF, SUM, IFERROR, OR, COUNTA.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cell styling | Custom font/fill per cell | v3_styles.py (FILL_DARK, FONT_HEADER, etc.) | Consistent with all other tabs |
| COUNTIFS with filter | Inline repeated logic | cf() helper function (rewritten for LOG) | DRY, reduces formula errors |
| Data validation | Manual cell ranges | openpyxl DataValidation class | Dropdown lists for VENDEDOR |
| Formula string escaping | Manual quote escaping | f-strings with proper delimiter handling | openpyxl handles escaping |

**Key insight:** The v3_dash.py is 90% reusable. The structural logic (block layout, section titles, total rows, formatting) is correct. Only the column references and tab name need changing.

## Common Pitfalls

### Pitfall 1: TIPO DO CONTATO Inconsistency (CRITICAL)
**What goes wrong:** LOG has 12 different TIPO values instead of the expected 7. Duplicates exist:
- "ATEND. CLIENTES ATIVOS" (3,516) vs "ATENDIMENTO CLIENTES ATIVOS" (1,780) = same concept, 2 spellings
- "POS-VENDA / RELACIONAMENTO" (5,847) vs "POS VENDA / RELACIONAMENTO" (565) = different hyphenation
- "PROSPECCAO NOVOS CLIENTES" (3,932) vs "PROSPECCAO" (30) = abbreviated vs full
- Extra types not in spec: "CONTATOS PASSIVO / SUPORTE" (2,258), "ENVIO DE MATERIAL - MKT" (672)
**Why it happens:** LOG was populated from multiple sources (CONTROLE_FUNIL, Deskrio, Synthetic) with different naming conventions. Phase 4 normalization was incomplete for TIPO DO CONTATO.
**How to avoid:** Two options:
  1. **OPTION A (Recommended):** Normalize LOG TIPO DO CONTATO in a pre-processing step before building DASH. Map all 12 values to the canonical 7.
  2. **OPTION B:** Use additive COUNTIFS in formulas (e.g., count both "ATEND. CLIENTES ATIVOS" AND "ATENDIMENTO CLIENTES ATIVOS"). This makes formulas extremely long and fragile.
**Warning signs:** DASH totals don't match simple COUNTA of LOG rows.

### Pitfall 2: MOTIVO Column Is Mostly Empty
**What goes wrong:** 20,698 out of 20,830 LOG records have empty MOTIVO (99.4%). Only 132 records have MOTIVO values, and they use different names than the spec:
- "PRODUTO NAO VENDEU / SEM GIRO" (40), "PROBLEMA LOGISTICO / ENTREGA" (37)
- Missing from LOG: most of the 10 canonical motivos
**Why it happens:** Historical data sources didn't consistently capture MOTIVO. Only recent CONTROLE_FUNIL records have motivos.
**How to avoid:** Build the MOTIVOS block but expect most cells to show 0. This is correct behavior -- the block will become useful as new LOG entries (with proper motivos) are added.
**Warning signs:** MOTIVOS total is ~132 vs CONTATOS total of ~20,830. This is expected, not an error.

### Pitfall 3: RESULTADO Values Don't Include RECUSOU LIGACAO
**What goes wrong:** The approved DASH_FINAL_APROVADO shows "RECUSOU" as a column, but V13 LOG contains ZERO records with "RECUSOU LIGACAO" as RESULTADO. Only "NAO ATENDE" (214) and "NAO RESPONDE" (259) exist.
**Why it happens:** RECUSOU LIGACAO was specified but data sources didn't produce any records with that exact value.
**How to avoid:** Include the RECUSOU column in DASH formulas (future data may have it), but expect 0 values. Do NOT remove the column from the design.

### Pitfall 4: Sheet Name with Accent in PROJECAO
**What goes wrong:** The PROJECAO sheet name is "PROJECAO " (with cedilla accent and trailing space). If DASH formulas reference it, they must use the EXACT sheet name.
**Why it happens:** Original file had accent in name.
**How to avoid:** DASH formulas reference LOG (no accent, no space), so this is not an issue for Phase 5. But be aware when loading/saving the workbook -- do NOT modify PROJECAO tab.

### Pitfall 5: Formula Length Limits in Excel
**What goes wrong:** IF(OR(...),COUNTIFS(...),COUNTIFS(...)) with multiple criteria can exceed 8,192 character cell formula limit.
**Why it happens:** Complex consultant filter + date filter + TIPO + RESULTADO = 6+ criteria pairs.
**How to avoid:** Keep formulas under ~500 chars each. The cf() pattern with 4-6 criteria pairs is well within limits.

### Pitfall 6: Date Format in Filter Cells
**What goes wrong:** COUNTIFS date comparison requires actual date values, not text strings.
**Why it happens:** If filter cells (E2, F2) contain text "01/02/2026" instead of datetime, ">=" comparison fails silently (returns 0).
**How to avoid:** Write datetime objects to filter cells via openpyxl, NOT strings. Apply FMT_DATE number format for display.

### Pitfall 7: Preserving PROJECAO Formulas
**What goes wrong:** Saving V13 after adding DASH tab destroys some PROJECAO formulas.
**Why it happens:** openpyxl can normalize formulas or break complex references when loading/saving.
**How to avoid:** Load with data_only=False, add DASH tab, save, then verify PROJECAO formula count >= 19,200.

### Pitfall 8: Consultant List Mismatch
**What goes wrong:** DASH shows only 4 consultants but LOG has 8 (including RODRIGO, HELDER BRUNKOW, LORRANY, LEANDRO GARCIA).
**Why it happens:** The 4 canonical consultants (MANU, LARISSA, JULIO, DAIANE) are the active team. Others are historical.
**How to avoid:** Filter dropdown includes only the 4 + "TODOS". When TODOS is selected, ALL consultants are counted (including historical). Individual consultant rows in Bloco 3 show only the 4 canonical ones. Total row should use SUM of the COUNTIFS, not sum of the 4 rows, to catch all consultants.

## Code Examples

### Pattern 1: cf() helper for V13 LOG (rewritten from v3_dash.py)

```python
# Source: v3_dash.py, adapted for V13 LOG column mapping
def cf(extra_criteria="", use_todos=True):
    """Build COUNTIFS formula string referencing V13 LOG tab.

    V13 LOG columns used:
      A = DATA (date filter)
      B = CONSULTOR (consultant filter)
      L = TIPO DO CONTATO
      M = RESULTADO
      N = MOTIVO
      H = WHATSAPP
      I = LIGACAO
      J = LIGACAO ATENDIDA
      Q = MERCOS ATUALIZADO

    DASH filter cells:
      C2 = VENDEDOR (dropdown: TODOS or name)
      E2 = PERIODO DE (date start)
      F2 = PERIODO ATE (date end)
    """
    date_filter = 'LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2'
    cons_filter = ',LOG!$B$3:$B$21000,$C$2'
    if use_todos:
        base_all = f"COUNTIFS({date_filter}{extra_criteria})"
        base_cons = f"COUNTIFS({date_filter}{cons_filter}{extra_criteria})"
        return f'IF(OR($C$2="",$C$2="TODOS"),{base_all},{base_cons})'
    else:
        return f"COUNTIFS({date_filter}{extra_criteria})"
```

### Pattern 2: TIPO x RESULTADO cross-tab formula

```python
# Source: Adapted from v3_dash.py Bloco 1
# For cell at intersection of TIPO row and RESULTADO column:
tipo_ref = f',LOG!$L$3:$L$21000,A{row}'  # TIPO from col A label
res_ref = f',LOG!$M$3:$M$21000,"{resultado}"'  # RESULTADO literal
formula = f'={cf(tipo_ref + res_ref)}'
# Produces: =IF(OR($C$2="",$C$2="TODOS"),COUNTIFS(LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2,LOG!$L$3:$L$21000,A9,LOG!$M$3:$M$21000,"ORCAMENTO"),COUNTIFS(LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2,LOG!$B$3:$B$21000,$C$2,LOG!$L$3:$L$21000,A9,LOG!$M$3:$M$21000,"ORCAMENTO"))
```

### Pattern 3: % CONVERSAO formula (excluding NAO ATENDE/NAO RESPONDE)

```python
# Source: FASE_4_DASH.md, adapted for V13 LOG
# % Conversao = VENDAS / (CONTATOS - NAO_ATENDE - NAO_RESPONDE)
# For consultant row:
na_count = f'COUNTIFS(LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2,LOG!$B$3:$B$21000,I{row},LOG!$M$3:$M$21000,"NAO ATENDE")'
nr_count = f'COUNTIFS(LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2,LOG!$B$3:$B$21000,I{row},LOG!$M$3:$M$21000,"NAO RESPONDE")'
formula = f'=IFERROR(K{row}/(J{row}-{na_count}-{nr_count}),0)'
```

### Pattern 4: DataValidation dropdown for VENDEDOR

```python
# Source: v3_dash.py row 101-105
from openpyxl.worksheet.datavalidation import DataValidation
dv_cons = DataValidation(
    type="list",
    formula1='"TODOS,MANU DITZEL,LARISSA PADILHA,JULIO GADRET,DAIANE STAVICKI"',
    allow_blank=True
)
ws.add_data_validation(dv_cons)
dv_cons.add("C2")
ws.cell(row=2, column=3, value="TODOS")
```

### Pattern 5: Date filter cells with proper datetime

```python
# Source: v3_dash.py row 108-113
import datetime
ws.cell(row=2, column=5, value=datetime.date(2026, 2, 1))
ws.cell(row=2, column=5).number_format = 'DD/MM/YYYY'
ws.cell(row=2, column=6, value=datetime.date(2026, 2, 28))
ws.cell(row=2, column=6).number_format = 'DD/MM/YYYY'
```

### Pattern 6: Workbook load/save preserving PROJECAO

```python
# Source: 05_populate_v13_log.py pattern
import openpyxl
wb = openpyxl.load_workbook(str(V13_PATH), data_only=False)
# NEVER use read_only=True when writing
# ALWAYS check formula count after save
ws_dash = wb.create_sheet("DASH")
# ... build DASH ...
wb.save(str(V13_PATH))

# Verify
wb2 = openpyxl.load_workbook(str(V13_PATH), data_only=False)
proj_ws = wb2['PROJECAO ']  # Note: accent + trailing space
formula_count = sum(1 for row in proj_ws.iter_rows()
                    for cell in row if cell.value and str(cell.value).startswith('='))
assert formula_count >= 19200, f"Formula loss! {formula_count}"
```

## Critical Data Findings

### TIPO DO CONTATO Normalization Map

The LOG has these TIPO values that must be mapped to the 7 canonical types:

| LOG Value | Count | Canonical TIPO | Action |
|-----------|-------|----------------|--------|
| POS-VENDA / RELACIONAMENTO | 5,847 | POS-VENDA / RELACIONAMENTO | Primary |
| POS VENDA / RELACIONAMENTO | 565 | POS-VENDA / RELACIONAMENTO | Merge (missing hyphen) |
| PROSPECCAO NOVOS CLIENTES | 3,932 | PROSPECCAO | Primary (rename) |
| PROSPECCAO | 30 | PROSPECCAO | Merge |
| ATEND. CLIENTES ATIVOS | 3,516 | ATEND. CLIENTES ATIVOS | Primary |
| ATENDIMENTO CLIENTES ATIVOS | 1,780 | ATEND. CLIENTES ATIVOS | Merge (abbreviated) |
| ATENDIMENTO CLIENTES INATIVOS | 1,227 | ATEND. CLIENTES INATIVOS | Primary |
| NEGOCIACAO | 944 | NEGOCIACAO | Keep |
| CONTATOS PASSIVO / SUPORTE | 2,258 | FOLLOW UP (*) | Map to closest |
| ENVIO DE MATERIAL - MKT | 672 | PROSPECCAO (*) | Map to closest |
| PERDA / NUTRICAO | 55 | PERDA / NUTRICAO | Keep |
| FOLLOW UP | 4 | FOLLOW UP | Keep |

(*) These 2 types (2,930 records) have no direct mapping. Options:
1. Map to closest canonical type
2. Create an "OUTROS" catch-all
3. Normalize before building DASH (recommended)

**Recommendation:** Normalize LOG data as a prerequisite task in Phase 5. Update the TIPO DO CONTATO values in the LOG tab directly using openpyxl. This ensures COUNTIFS formulas work correctly with exact string matching.

### RESULTADO Values (Clean)

| LOG Value | Count | Spec Match |
|-----------|-------|------------|
| EM ATENDIMENTO | 7,321 | YES |
| SUPORTE | 6,824 | YES |
| VENDA / PEDIDO | 2,311 | YES |
| ORCAMENTO | 2,256 | YES |
| RELACIONAMENTO | 822 | YES |
| CADASTRO | 568 | YES |
| NAO RESPONDE | 259 | YES |
| NAO ATENDE | 214 | YES |
| PERDA / FECHOU LOJA | 119 | YES |
| FOLLOW UP 7 | 112 | YES |
| FOLLOW UP 15 | 24 | YES |
| RECUSOU LIGACAO | 0 | In spec, 0 records |

RESULTADO values are CLEAN. All 11 values match spec exactly. No normalization needed.

### Consultores (8 in LOG, 4 canonical)

| Consultor | Records | Team Status |
|-----------|---------|-------------|
| LARISSA PADILHA | 8,517 | Active team |
| MANU DITZEL | 7,532 | Active team |
| JULIO GADRET | 1,813 | Active team |
| DAIANE STAVICKI | 1,575 | Active team |
| RODRIGO | 802 | Historical (Deskrio) |
| HELDER BRUNKOW | 532 | Historical |
| LORRANY | 52 | Historical |
| LEANDRO GARCIA | 7 | Historical |

DASH dropdown: 4 canonical + "TODOS". When TODOS selected, all 8 counted.

## State of the Art

| Old Approach (V12 DASH) | New Approach (V13 DASH) | Impact |
|--------------------------|-------------------------|--------|
| References DRAFT 2 | References LOG | Column mapping changes |
| 74 rows, 18 cols, 8+ blocks | ~45 rows, ~16 cols, 3 blocks | Cleaner, per requirements |
| Portuguese formula names in comments | English formulas in openpyxl | Required for openpyxl |
| No date/consultant filter | IF(OR()) filter pattern | Interactive filtering |
| No TIPO DO CONTATO normalization | Must normalize first | Critical prerequisite |

**Deprecated/outdated:**
- v3_dash.py: Working code but wrong column references (DRAFT 2 not LOG). Use as structural template only.
- V12 DASH: Too complex (8 blocks, RNC, temperatura, demandas). Simplified to 3 blocks per approved design.

## Scope Decision: CARTEIRA-dependent Blocks

### What's DEFERRED (no CARTEIRA in V13):
1. **DASH CLIENTES** (FASE_5_DASH_CLIENTES.md) -- All 4 blocks reference CARTEIRA columns (SITUACAO, SINALEIRO, FASE, TICKET MEDIO, POSITIVACAO). Deferred to Phase 9+.
2. **Bloco 4 from v3_dash.py** (Situacao CRM + Fases) -- References CARTEIRA!$N and CARTEIRA!$I. Deferred.
3. **Bloco 5 from v3_dash.py** (Situacao por Rede) -- References CARTEIRA!$I and CARTEIRA!$N. Deferred.
4. **Bloco 6 from v3_dash.py** (Saude Carteira x Acoes) -- References DRAFT 2!$W (SINALEIRO) and DRAFT 2!$U (ACAO). Deferred.

### What's IN SCOPE (LOG-only):
1. **Bloco 1:** TIPO DO CONTATO x RESULTADO (matrix) -- LOG cols L, M
2. **Bloco 2:** CONTATOS + FUNIL (channels + results by tipo) -- LOG cols H, I, J, L, M
3. **Bloco 3:** MOTIVOS (left) + PRODUTIVIDADE (right) -- LOG cols N (motivo), B (consultor)
4. **KPI Cards:** Summary numbers from LOG
5. **Filters:** VENDEDOR dropdown + PERIODO dates

## Open Questions

1. **TIPO DO CONTATO normalization approach**
   - What we know: 12 values exist, 7 canonical expected, normalization needed
   - What's unclear: Should we modify LOG data in V13 (destructive) or handle in formulas (verbose)?
   - Recommendation: Normalize LOG data. It was already written by Python; fixing it in Python is safe and clean. Create a backup first.

2. **"CONTATOS PASSIVO / SUPORTE" and "ENVIO DE MATERIAL - MKT" mapping**
   - What we know: 2,930 records with types not in the canonical 7
   - What's unclear: Which canonical type to map them to. "CONTATOS PASSIVO / SUPORTE" could be POS-VENDA or FOLLOW UP. "ENVIO DE MATERIAL - MKT" could be PROSPECCAO.
   - Recommendation: Ask Leandro OR map them to closest match and note in documentation.

3. **Bar chart inclusion**
   - What we know: DASH_FINAL_APROVADO shows horizontal bars for RESULTADO distribution
   - What's unclear: Whether openpyxl BarChart renders well enough for CEO review
   - Recommendation: Include as optional. The numbers table is the primary view; chart is enhancement.

4. **PAINEL validation target**
   - What we know: Success criteria says "Numeros da DASH batem com PAINEL de referencia"
   - What's unclear: What is the PAINEL? Phase 2 showed no single source matches R$ 2,156,179. DASH counts LOG interactions (not financials), so "bater com PAINEL" may mean contact counts, not R$.
   - Recommendation: Validate that DASH TOTAL CONTATOS = COUNTA(LOG data rows within date range). This is the verifiable check.

## Sources

### Primary (HIGH confidence)
- V13 Excel file direct analysis (openpyxl read, all tabs/columns/values) -- LIVE DATA
- v3_dash.py (762 lines, complete working DASH builder) -- LOCAL CODE
- v3_styles.py (shared formatting) -- LOCAL CODE
- 05_populate_v13_log.py (LOG writer, confirms column mapping) -- LOCAL CODE
- V12 COM_DADOS DASH tab (74 rows, existing formula patterns) -- LOCAL DATA

### Secondary (MEDIUM confidence)
- DASH_FINAL_APROVADO.html (Leandro-approved 3-block design) -- LOCAL SPEC
- FASE_4_DASH.md (detailed 7-block formula spec, Portuguese) -- LOCAL SPEC
- FASE_5_DASH_CLIENTES.md (4-block CARTEIRA-dependent spec) -- LOCAL SPEC (deferred)
- BLUEPRINT_v3_LOG_AGENDA_DASH.html (full architecture spec) -- LOCAL SPEC

### Tertiary (LOW confidence)
- ROADMAP.md plan descriptions for Phase 5 (3 plans listed, may need revision)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- openpyxl confirmed, v3_styles.py available, patterns from prior phases
- Architecture: HIGH -- V13 structure verified, LOG column mapping confirmed via code
- Formula patterns: HIGH -- cf() helper tested in v3_dash.py, column translation verified
- TIPO normalization: HIGH -- Values enumerated from actual LOG data scan
- Pitfalls: HIGH -- All discovered from actual data analysis, not speculation

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable -- V13 structure won't change until Phase 9)

## Summary of Prerequisites for Phase 5

1. **TIPO DO CONTATO normalization** -- Must be done BEFORE building DASH formulas
2. **V13 backup** -- Before any modification (pattern from prior phases)
3. **19,224 PROJECAO formula preservation** -- Verify after every save
4. **No CARTEIRA blocks** -- Only LOG-referenced blocks in scope

## Recommended Plan Structure

- **Plan 05-01:** Normalize LOG TIPO DO CONTATO + define DASH layout (prerequisite)
- **Plan 05-02:** Build DASH tab with 3 blocks + KPIs + filters (main work)
- **Plan 05-03:** Validate DASH numbers + formatting + PROJECAO preservation
