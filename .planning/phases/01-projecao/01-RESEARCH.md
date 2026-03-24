# Phase 1: Projecao - Research

**Researched:** 2026-02-16
**Domain:** Validacao de planilha Excel PROJECAO com formulas dinamicas + populacao de dados SAP 2026
**Confidence:** HIGH

## Summary

A Fase 1 mudou radicalmente de escopo apos a descoberta de 16/FEV/2026: as 19.224 formulas da aba PROJECAO **NAO estao perdidas**. Elas existem intactas no CRM V12 e em 4 arquivos standalone. A tarefa agora e **validar as formulas existentes e popular com dados SAP 2026 atualizados**, nao reconstruir do zero.

A investigacao profunda revelou que: (1) PROJECAO_534_INTEGRADA e a aba PROJECAO do V12 sao **identicas** -- mesmos 534 CNPJs, mesmas 19.224 formulas, mesmos valores META; (2) SAP Consolidado (01_SAP_CONSOLIDADO.xlsx) contem a tabela "Rosetta Stone" com mapeamento CNPJ <-> Codigo SAP para 1.698 clientes; (3) Os dados de VENDA MES A MES 2025 estao disponiveis por cliente com CNPJ; (4) As formulas usam exclusivamente funcoes em INGLES (SUM, IF, VLOOKUP, RANK, IFERROR, SUMPRODUCT, COUNTIF, COUNTA, MAX) que openpyxl 3.1.5 suporta nativamente; (5) O V12 nao tem tabelas, graficos, imagens, pivots ou slicers na aba PROJECAO -- openpyxl pode manipula-la com seguranca.

Existem 4 variantes de PROJECAO com diferencas importantes nas formulas (thresholds de sinaleiro, calculo de META por cliente, formula de META compensada). A variante PROJECAO_534_INTEGRADA/V12 usa um modelo de distribuicao baseado em media (SUM/COUNTA), enquanto a PROJECAO_CORRIGIDA usa pesos percentuais fixos derivados do SAP (que somam exatamente 100%). A decisao de qual modelo adotar e critica.

**Primary recommendation:** Usar a PROJECAO_534_INTEGRADA (=V12) como base de formulas, mas atualizar os dados de valor (metas SAP 2026, vendas realizadas 2025) com dados frescos do SAP Consolidado. Adotar os pesos percentuais da CORRIGIDA para distribuicao de meta mensal, pois sao derivados diretamente do SAP e somam exatamente 100%.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.5 | Leitura/escrita de Excel .xlsx com formulas | Unico que preserva formulas nativas do Excel |
| Python | 3.12.10 | Runtime | Instalado via pyenv no sistema |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| collections.defaultdict | stdlib | Agregacao de dados SAP | Quando processar meta por grupo chave |
| re (regex) | stdlib | Limpeza de CNPJ | Remover pontuacao de CNPJ formatado |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl | xlsxwriter | xlsxwriter nao le arquivos existentes -- apenas escreve. Descartado |
| openpyxl | pandas + openpyxl | pandas destroi formulas ao salvar. So usar para analise, nunca para salvar |
| Manipulacao direta | XML Surgery (zipfile) | Necessario APENAS se houver slicers/pivots para preservar. V12 PROJECAO nao tem -- openpyxl seguro |

**Installation:**
```bash
# Ja instalado
pip install openpyxl==3.1.5
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  phase01_projecao/
    01_validate_formulas.py    # Validar que formulas existentes estao intactas
    02_extract_sap_data.py     # Extrair metas 2026 e vendas 2025 do SAP
    03_populate_projecao.py    # Popular valores nas colunas de dados
    04_verify_projecao.py      # Verificar totais, formulas, integridade
data/
  sources/
    sap/01_SAP_CONSOLIDADO.xlsx           # Rosetta Stone: CNPJ <-> SAP Code
    sap/BASE_SAP_META_PROJECAO_2026.xlsx  # Metas 2026 por grupo chave
    sap/BASE_SAP_VENDA_MES_A_MES_2025.xlsx # Vendas realizadas 2025
    projecao/PROJECAO_534_INTEGRADA.xlsx  # Base de formulas (=V12)
  output/
    CRM_VITAO360_V13.xlsx                 # Output final
```

### Pattern 1: Read-Modify-Write (Preservar Formulas)
**What:** Abrir o workbook existente com formulas, modificar APENAS as celulas de dados (valores), salvar.
**When to use:** Sempre que precisar popular dados sem destruir formulas existentes.
**Example:**
```python
import openpyxl

# SEMPRE usar data_only=False para preservar formulas
wb = openpyxl.load_workbook('PROJECAO_534_INTEGRADA.xlsx', data_only=False)
ws = wb['PROJECAO ']  # NOTA: tem espaco no final do nome!

# Popular APENAS colunas de dados (NUNCA sobrescrever colunas de formula)
# Colunas seguras para escrita: A-E, K, L-X, AA-AL, AS-AZ
# Colunas PROIBIDAS (formulas): F-J, Z, AN-AQ, BB-CB
for row in range(4, 538):
    ws.cell(row=row, column=27).value = valor_jan  # AA = REAL JAN

wb.save('output.xlsx')
```

### Pattern 2: CNPJ como Chave Universal
**What:** Usar CNPJ normalizado (14 digitos, sem pontuacao, string) como chave de cruzamento entre todos os arquivos.
**When to use:** Sempre que cruzar dados entre fontes diferentes.
**Example:**
```python
import re

def normalize_cnpj(raw):
    """Normaliza CNPJ para string de 14 digitos."""
    if raw is None:
        return None
    clean = re.sub(r'[^0-9]', '', str(raw))
    return clean.zfill(14) if len(clean) <= 14 else clean

# SAP Consolidado tem CNPJ formatado: "32.387.943/0001-05"
# PROJECAO tem CNPJ numerico: 32387943000105
# Ambos normalizam para: "32387943000105"
```

### Pattern 3: Mapeamento SAP Code <-> CNPJ via Rosetta Stone
**What:** O SAP usa "Codigo do Cliente" (10 digitos) internamente, nao CNPJ. O cruzamento requer a tabela de mapeamento do SAP Consolidado.
**When to use:** Sempre que dados SAP (META, Faturamento, Grupo Chave) precisam ser vinculados a clientes por CNPJ.
**Example:**
```python
# Construir mapa CNPJ -> SAP data a partir de 01_SAP_CONSOLIDADO.xlsx
wb_sap = openpyxl.load_workbook('01_SAP_CONSOLIDADO.xlsx', data_only=True)
ws_cadastro = wb_sap['Cadastro Clientes SAP']

cnpj_to_sap = {}
for row in range(2, ws_cadastro.max_row + 1):
    cod_cliente = ws_cadastro.cell(row=row, column=3).value   # C = Codigo do Cliente
    cnpj_raw = ws_cadastro.cell(row=row, column=5).value      # E = CNPJ Cliente
    cnpj = normalize_cnpj(cnpj_raw)
    if cnpj and cod_cliente:
        cnpj_to_sap[cnpj] = str(cod_cliente)
# 1.698 mapeamentos disponiveis
```

### Anti-Patterns to Avoid
- **Abrir com data_only=True para salvar:** Destroi TODAS as formulas, substituindo por valores cached. NUNCA usar data_only=True se for salvar o arquivo.
- **Sobrescrever celulas de formula:** As colunas F-J, Z, AN-AQ, BB-CB contem formulas. Escrever valores nelas destroi a logica dinamica.
- **Ignorar o espaco no nome da aba:** A aba se chama "PROJECAO " (com espaco no final). `wb['PROJECAO']` sem espaco dara KeyError.
- **Tratar CNPJ como numero:** CNPJs com zero a esquerda perdem o zero. SEMPRE tratar como string de 14 digitos.
- **Usar pandas.to_excel():** Destroi toda a formatacao, formulas, freeze panes, auto-filter. Nunca usar para salvar o CRM.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Distribuicao de meta mensal | Calcular % manualmente | Usar pesos SAP (Row 8 do Meta e Projecao) | Pesos do SAP somam exatamente 100% e batem com metas mensais oficiais |
| Calculo de % atingimento | Python calc | Formula Excel `=IF(L4=0,0,Z4/L4)` | Ja existe na planilha, recalcula automaticamente |
| Sinaleiro visual | Logica Python | Formula Excel `=IF(AN4>=0.9,...)` | Ja existe, atualiza automaticamente quando dados mudam |
| Ranking | Python sort | Formula Excel `=RANK(Z4,Z$4:Z$537,0)` | Dinamico, recalcula com novos dados |
| Lookup de rede | Python dict lookup | Formula Excel `=IFERROR(VLOOKUP(C4,...),"")`  | Ja existe, referencia tabela auxiliar AS:AX |
| Limpeza de CNPJ | Regex complexo | `re.sub(r'[^0-9]', '', str(raw)).zfill(14)` | Simples e robusto |

**Key insight:** As 19.224 formulas JA existem e funcionam. O trabalho e popular os DADOS (valores), nao as formulas. Tentar reescrever formulas quando elas ja existem e um risco desnecessario de introduzir bugs.

## Common Pitfalls

### Pitfall 1: Nome da Aba com Espaco Final
**What goes wrong:** `wb['PROJECAO']` causa KeyError.
**Why it happens:** A aba se chama `"PROJECAO "` (com espaco no final) em todos os arquivos.
**How to avoid:** Sempre usar `wb['PROJECAO ']` com espaco, ou iterar sobre `wb.sheetnames` para encontrar.
**Warning signs:** KeyError ao acessar a aba.

### Pitfall 2: Row Ranges Hardcoded nas Formulas
**What goes wrong:** Se mudar o numero de clientes (ex: de 534 para 600), formulas como `RANK(Z4,Z$4:Z$537,0)` nao cobrem as novas linhas.
**Why it happens:** As formulas referenciam ranges fixos ($Z$4:$Z$537 para 534 clientes).
**How to avoid:** Se adicionar clientes, TODAS as formulas com ranges fixos precisam ser atualizadas. Documentar o range correto para cada variante.
**Warning signs:** Novos clientes com RANKING vazio ou % YTD incorreto.

### Pitfall 3: Discrepancia de Meta Total (0.7%)
**What goes wrong:** Soma das metas individuais dos 534 clientes = R$ 4.779.003, mas SAP total = R$ 4.747.200 (diferenca de R$ 31.803 / 0.67%).
**Why it happens:** A distribuicao de meta para clientes individuais usa um modelo que nao soma exatamente ao total SAP. Pode ser arredondamento ou clientes extras.
**How to avoid:** Aceitar a discrepancia como conhecida e documentada, OU redistribuir proporcionalmente para que a soma bata.
**Warning signs:** Totais nao batem quando comparados com dashboard SAP.

### Pitfall 4: Variantes de Formula com Thresholds Diferentes
**What goes wrong:** Sinaleiro mostra cores incorretas para o modelo de negocio.
**Why it happens:** Existem 2 modelos de sinaleiro:
  - **534/V12:** `>=0.9` verde, `>=0.7` amarelo, `>=0.5` laranja, resto vermelho
  - **CORRIGIDA:** `>=1.0` verde, `>=0.7` amarelo, `>=0.4` laranja, resto vermelho
**How to avoid:** Decidir qual modelo de thresholds usar e aplicar consistentemente.
**Warning signs:** Comparar visualmente os sinaleiros com o criterio esperado pela equipe.

### Pitfall 5: SAP Usa Codigo Interno, Nao CNPJ
**What goes wrong:** Nao consegue cruzar dados de META/Faturamento do SAP com a PROJECAO.
**Why it happens:** SAP identifica clientes por "Codigo do Cliente" (10 digitos, ex: 1000202181), enquanto a PROJECAO usa CNPJ (14 digitos, ex: 32387943000105). Sao chaves diferentes.
**How to avoid:** Usar a tabela de mapeamento em `01_SAP_CONSOLIDADO.xlsx > Cadastro Clientes SAP` que tem ambas as chaves (col C = Codigo, col E = CNPJ). 1.698 mapeamentos disponiveis.
**Warning signs:** Muitos clientes sem match, dados de meta vazios.

### Pitfall 6: Vendas MES A MES com Formato Misto
**What goes wrong:** Nao parseia corretamente os codigos de cliente no arquivo de vendas mensais.
**Why it happens:** `BASE_SAP_VENDA_MES_A_MES_2025.xlsx` tem 12 abas (Jan-Dez), cada uma com formato "1000069469 - ATLAS BRASIL..." na coluna A. O codigo SAP esta antes do " - ".
**How to avoid:** Parsear com split e strip, e depois usar o mapeamento CNPJ.
**Warning signs:** Clientes nao encontrados, vendas perdidas.

### Pitfall 7: META por Grupo Chave vs META por Cliente
**What goes wrong:** Confundir os niveis de agregacao.
**Why it happens:** O SAP (BASE_SAP_META_PROJECAO_2026.xlsx) organiza metas por "GRUPO CHAVE" (ex: "06 - INTERNA - BIO MUNDO"), que pode conter multiplos CNPJs. A PROJECAO distribui meta a nivel de CNPJ individual.
**How to avoid:** Usar `01_SAP_CONSOLIDADO > Grupo Chave SAP` para mapear Grupo Chave -> CNPJs individuais, depois distribuir a meta do grupo proporcionalmente.
**Warning signs:** Meta de um grupo inteiro atribuida a um unico cliente.

## Code Examples

### Exemplo 1: Carregar PROJECAO preservando formulas
```python
import openpyxl

wb = openpyxl.load_workbook(
    'data/sources/projecao/PROJECAO_534_INTEGRADA.xlsx',
    data_only=False  # CRITICO: preservar formulas
)
ws = wb['PROJECAO ']  # NOTA: espaco no final

# Verificar estrutura
assert ws.max_row == 537  # 3 header rows + 534 data rows
assert ws.max_column == 80  # 80 colunas (A ate CB)
assert ws.freeze_panes == 'C4'  # Freeze em C4
```

### Exemplo 2: Construir mapa CNPJ -> Vendas Mensais 2025
```python
import openpyxl
import re

def normalize_cnpj(raw):
    if raw is None: return None
    clean = re.sub(r'[^0-9]', '', str(raw))
    return clean.zfill(14) if len(clean) <= 14 else clean

# Carregar SAP Consolidado
wb_sap = openpyxl.load_workbook('data/sources/sap/01_SAP_CONSOLIDADO.xlsx', data_only=True)
ws_vendas = wb_sap['Venda Mes a Mes']

vendas_por_cnpj = {}
for row in range(2, ws_vendas.max_row + 1):
    cnpj_raw = ws_vendas.cell(row=row, column=3).value  # C = CNPJ ou CPF Cliente
    cnpj = normalize_cnpj(cnpj_raw)
    if not cnpj: continue

    # Faturado por mes: cols G(Jan), K(Fev), O(Mar), S(Abr), W(Mai),
    # AA(Jun), AE(Jul), AI(Ago), AM(Set), AQ(Out), AU(Nov), AY(Dez)
    fat_cols = [7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51]
    monthly = []
    for col in fat_cols:
        v = ws_vendas.cell(row=row, column=col).value
        monthly.append(float(v) if v else 0.0)
    vendas_por_cnpj[cnpj] = monthly
```

### Exemplo 3: Popular colunas REALIZADO na PROJECAO
```python
# Colunas REALIZADO: AA(27)=Jan, AB(28)=Fev, ... AL(38)=Dez
# Z(26) = SUM(AA:AL) -- formula existente, NAO sobrescrever

for row in range(4, ws.max_row + 1):
    cnpj = normalize_cnpj(ws.cell(row=row, column=1).value)  # A = CNPJ
    vendas = vendas_por_cnpj.get(cnpj, [0]*12)

    for i, col in enumerate(range(27, 39)):  # AA=27 ate AL=38
        ws.cell(row=row, column=col).value = vendas[i]
        ws.cell(row=row, column=col).number_format = (
            '_-"R$"\\ * #,##0.00_-;\\-"R$"\\ * #,##0.00_-;'
            '_-"R$"\\ * "-"??_-;_-@_-'
        )
    # Z26 (REAL ANUAL) = formula =SUM(AA:AL) -- nao tocar!
```

### Exemplo 4: Validar integridade das formulas
```python
# Verificar que TODAS as 36 colunas de formula estao intactas
FORMULA_COLS = {
    6: '=IFERROR(VLOOKUP(C{r},$AS$4:$AT$18,2,FALSE),"")',   # F
    7: '=IFERROR(VLOOKUP(C{r},$AS$4:$AU$18,3,FALSE),"")',   # G
    8: '=IFERROR(VLOOKUP(C{r},$AS$4:$AV$18,4,FALSE),"")',   # H
    9: '=IFERROR(VLOOKUP(C{r},$AS$4:$AW$18,5,FALSE),"")',   # I
    10: '=IFERROR(VLOOKUP(C{r},$AS$4:$AX$18,6,FALSE),"")',  # J
    26: '=SUM(AA{r}:AL{r})',                                  # Z
    40: '=IF(L{r}=0,0,Z{r}/L{r})',                           # AN
    42: '=IF(L{r}=0,0,L{r}-Z{r})',                           # AP
}

errors = 0
for row in range(4, ws.max_row + 1):
    for col, pattern in FORMULA_COLS.items():
        expected = pattern.format(r=row)
        actual = ws.cell(row=row, column=col).value
        if actual != expected:
            errors += 1
            print(f'  MISMATCH {openpyxl.utils.get_column_letter(col)}{row}: '
                  f'expected={expected}, actual={actual}')

print(f'Formula validation: {errors} errors found')
```

## Detailed Analysis of Source Files

### Inventario Completo de Fontes

| Arquivo | Local | Sheets | Rows | Formulas | Uso |
|---------|-------|--------|------|----------|-----|
| PROJECAO_534_INTEGRADA.xlsx | data/sources/projecao/ | 1 (PROJECAO) | 537 x 80 | 19.224 | **BASE PRINCIPAL** - Identica ao V12 |
| PROJECAO_CORRIGIDA (2).xlsx | data/sources/projecao/ | 7 | 504 x 80 | 15.500 | Formula alternativa com pesos % + sheets extras |
| PROJECAO_INTERNO_1566.xlsx | data/sources/projecao/ | 3 | 1570 x 83 | 56.544 | Versao expandida com 1566 clientes |
| PROJECAO_POPULADA_1566.xlsx | data/sources/projecao/ | 1 | 1569 x 80 | 56.376 | 1566 clientes populada |
| CRM V12 (2) PROJECAO tab | data/sources/crm-versoes/v11-v12/ | 15 tabs no CRM | 537 x 80 | 19.224 | Identica a 534_INTEGRADA |
| 01_SAP_CONSOLIDADO.xlsx | data/sources/sap/ | 5 | Variavel | 0 | Rosetta Stone: CNPJ<->SAP + Vendas Mes a Mes |
| BASE_SAP_META_PROJECAO_2026.xlsx | data/sources/sap/ | 7 | Variavel | 0 | Metas 2026 por Grupo Chave |
| BASE_SAP_VENDA_MES_A_MES_2025.xlsx | data/sources/sap/ | 12 | 35-121/mes | 0 | Vendas realizadas 2025 |

### Mapeamento Completo de Colunas PROJECAO (80 colunas)

#### Bloco 1: Identificacao (A-E) -- DADOS
| Col | Header | Tipo | Exemplo | Fonte |
|-----|--------|------|---------|-------|
| A | CNPJ | Valor (14 digits string) | 32387943000105 | CARTEIRA/SAP |
| B | NOME FANTASIA | Valor | FACILITIES EDUCACIONAIS LTDA | CARTEIRA/SAP |
| C | REDE / GRUPO CHAVE | Valor | SEM GRUPO | SAP Grupo Chave |
| D | CONSULTOR | Valor | DAIANE STAVICKI | SAP/CRM |
| E | (separador) | "." | . | Fixo |

#### Bloco 2: Sinaleiro Rede (F-J) -- FORMULAS (VLOOKUP para AS:AX)
| Col | Header | Formula | Referencia |
|-----|--------|---------|------------|
| F | TOTAL LOJAS | `=IFERROR(VLOOKUP(C{r},$AS$4:$AT$18,2,FALSE),"")` | Lookup por Rede |
| G | SINALEIRO % | `=IFERROR(VLOOKUP(C{r},$AS$4:$AU$18,3,FALSE),"")` | Lookup por Rede |
| H | COR SINALEIRO | `=IFERROR(VLOOKUP(C{r},$AS$4:$AV$18,4,FALSE),"")` | Lookup por Rede |
| I | MATURIDADE | `=IFERROR(VLOOKUP(C{r},$AS$4:$AW$18,5,FALSE),"")` | Lookup por Rede |
| J | ACAO REDE | `=IFERROR(VLOOKUP(C{r},$AS$4:$AX$18,6,FALSE),"")` | Lookup por Rede |
| K | (separador) | "." | Fixo |

#### Bloco 3: Meta SAP Mensal (L-X) -- DADOS
| Col | Header | Tipo | Fonte |
|-----|--------|------|-------|
| L | META ANUAL | Valor R$ | SAP Meta 2026 |
| M-X | META JAN-DEZ | Valor R$ | L * peso mensal |
| Y | (separador) | "." | Fixo |

#### Bloco 4: Realizado Mensal (Z-AL) -- Z=FORMULA, AA-AL=DADOS
| Col | Header | Tipo | Fonte |
|-----|--------|------|-------|
| Z | REAL ANUAL | **FORMULA** `=SUM(AA{r}:AL{r})` | Calculado |
| AA-AL | REAL JAN-DEZ | Valor R$ | SAP Vendas 2025 / Mercos |
| AM | (separador) | "." | Fixo |

#### Bloco 5: Indicadores (AN-AQ) -- FORMULAS
| Col | Header | Formula |
|-----|--------|---------|
| AN | % YTD | `=IF(L{r}=0,0,Z{r}/L{r})` |
| AO | SINAL META | `=IF(AN{r}="","",IF(AN{r}>=0.9,"verde",IF(AN{r}>=0.7,"amarelo",IF(AN{r}>=0.5,"laranja","vermelho"))))` |
| AP | GAP | `=IF(L{r}=0,0,L{r}-Z{r})` |
| AQ | RANKING | `=IF(Z{r}=0,"",RANK(Z{r},Z$4:Z$537,0))` |
| AR | (separador) | "." | Fixo |

#### Bloco 6: Tabela Auxiliar Sinaleiro Redes (AS-AZ) -- DADOS
| Col | Header | Conteudo |
|-----|--------|----------|
| AS | REDE | Nome da rede (FITLAND, VIDA LEVE, etc.) |
| AT | TOTAL LOJAS | Numero de lojas |
| AU | SINALEIRO % | Percentual de penetracao |
| AV | COR | Emoji + cor (ex: "amarelo AMARELO") |
| AW | MATURIDADE | SELL OUT / POSITIVACAO / JBP |
| AX | ACAO RECOMENDADA | Texto de acao |
| AY | FAT. REAL | Faturamento real da rede |
| AZ | GAP | Gap de meta da rede |
| BA | (separador) | "." |

Linhas: 15 redes (rows 4-18), referenciadas pelos VLOOKUPs de F-J.

#### Bloco 7: Meta Cliente Igualitaria (BB-BN) -- FORMULAS
| Col | Header | Formula |
|-----|--------|---------|
| BB | DIST ANUAL | `=SUM(L$4:L$537)/COUNTA(A$4:A$537)` -- meta media |
| BC-BN | DIST JAN-DEZ | `=SUM(M$4:M$537)/COUNTA(A$4:A$537)` -- media mensal |
| BO | (separador) | "." |

**Nota:** Na variante CORRIGIDA, estas sao `=L{r}*0.0702730030` (peso fixo), nao media.

#### Bloco 8: Meta Compensada Dinamica (BP-CB) -- FORMULAS
| Col | Header | Formula (534/V12) |
|-----|--------|---------|
| BP | COMP ANUAL | `=IF(Z{r}>=BB{r},0,IFERROR(BB{r}+(SUMPRODUCT(...)...)` |
| BQ-CB | COMP JAN-DEZ | Similar com colunas mensais |

**Nota:** Na variante CORRIGIDA, estas sao simplesmente `=SUM(BQ{r}:CB{r})`.

### Formula Count Breakdown
- 36 colunas com formulas * 534 rows = **19.224 formulas** (confirmado)
  - Bloco Sinaleiro (F-J): 5 cols * 534 = 2.670
  - Realizado Total (Z): 1 col * 534 = 534
  - Indicadores (AN-AQ): 4 cols * 534 = 2.136
  - Meta Igualitaria (BB-BN): 13 cols * 534 = 6.942
  - Meta Compensada (BP-CB): 13 cols * 534 = 6.942
  - **Total: 19.224**

### Diferencas entre Variantes

| Aspecto | 534/V12 | CORRIGIDA | INTERNO_1566 |
|---------|---------|-----------|--------------|
| Clientes | 534 | 504 | 1.566 |
| Formulas | 19.224 | 15.500 | 56.544 |
| Sinaleiro thresholds | 90/70/50% | 100/70/40% | 90/70/50% |
| Meta distribuicao | Media (SUM/COUNTA) | Peso fixo (L*%) | Media (SUM/COUNTA) |
| Meta compensada | SUMPRODUCT complexo | SUM simples | SUMPRODUCT complexo |
| GAP formula | IF(L=0,0,L-Z) | L-Z (sem guard) | IF(L=0,0,L-Z) |
| RANK range | Z$4:Z$537 | $Z$4:$Z$503 | Z$4:Z$1569 |
| Sheets extras | 0 | 6 (Resumo, Historico, Interno, Status, Ciclo, Update_Log) | 2 (Update_Log, Interno) |
| META ANUAL client 1 | R$ 10.601 | R$ 249.796 | R$ 1.614 |

### Pesos de Distribuicao Mensal SAP
```
JAN: 7.027%  |  FEV: 7.343%  |  MAR: 7.520%  |  ABR: 7.716%
MAI: 7.969%  |  JUN: 8.177%  |  JUL: 8.493%  |  AGO: 8.702%
SET: 8.898%  |  OUT: 9.119%  |  NOV: 9.359%  |  DEZ: 9.676%
TOTAL: 100.000% (exato)
```
Estes pesos foram confirmados contra as metas mensais oficiais do SAP (R$ 4.747.200 total). Cada peso * total = meta mensal exata.

### Formatos de Numero Importantes
| Coluna | Formato Excel |
|--------|---------------|
| A (CNPJ) | `"0"` (numero com zeros a esquerda) |
| L-X, Z, AA-AL, AP, BB-CB (R$) | `_-"R$"\ * #,##0.00_-;\-"R$"\ * #,##0.00_-;_-"R$"\ * "-"??_-;_-@_-` |
| AN (%) | `"0%"` |

### Propriedades da Aba PROJECAO
- Freeze panes: C4
- Auto-filter: A3:CB537
- Column widths: A=16, B=30, C=20, D=20, E=2, F=12, L=12, Z=12, AN=10
- Row 3 height: 28

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reconstruir 18.180 formulas | Validar existentes + popular dados | 16/FEV/2026 | Reducao massiva de risco e esforco |
| v3_projecao.py (hardcoded per-rede) | Read-modify-write per-CNPJ | Agora | De 13 redes fixas para 534+ clientes dinamicos |
| Distribuicao de meta por media | Pesos % fixos do SAP | Agora | Precisao 100% vs divergencia de 0.7% |

**Deprecated/outdated:**
- `scripts/v3_projecao.py`: Script antigo que criava PROJECAO do zero com apenas 13 redes (nao clientes individuais). Completamente inadequado para a estrutura real de 534 clientes com 80 colunas.
- `scripts/extract_meta_sap.py`: Referencia um caminho de arquivo que nao existe mais (Desktop). Util como referencia de logica mas precisa ser atualizado.

## Open Questions

1. **Qual variante de thresholds de sinaleiro usar?**
   - 534/V12: 90/70/50% (mais leniente para verde)
   - CORRIGIDA: 100/70/40% (mais rigoroso: so verde se >=100%)
   - Recommendation: Perguntar ao Leandro qual modelo ele prefere. Se nao disponivel, usar CORRIGIDA (100/70/40%) pois e mais recente e mais alinhada com metas reais.

2. **534 clientes vs 1.566 clientes: qual base usar?**
   - 534: Clientes ativos com meta SAP
   - 1.566: Inclui inativos/prospects/sem venda
   - Recommendation: Comecar com 534 (ativos com meta), pois e a base do V12. Fase 9 (Blueprint v2) pode expandir.

3. **Discrepancia de R$ 31.803 (0.67%) na soma de metas: corrigir?**
   - Soma das metas individuais: R$ 4.779.003
   - Total SAP oficial: R$ 4.747.200
   - Recommendation: Investigar se ha clientes duplicados ou distribuicao incorreta. Se nao resolver, documentar como "arredondamento de distribuicao".

4. **Meta por Grupo Chave vs Meta por Cliente: como distribuir?**
   - SAP organiza meta por GRUPO CHAVE (80 grupos), nao por CNPJ individual
   - PROJECAO tem meta a nivel de CNPJ individual
   - What we know: A distribuicao atual no 534 ja resolveu isso (cada CNPJ tem uma meta)
   - Recommendation: Manter a distribuicao existente. So recalcular se for necessario atualizar com novos dados SAP 2026.

5. **Dados de vendas 2025: usar SAP Consolidado (493 clientes) ou BASE_SAP_VENDA_MES_A_MES (12 abas)?**
   - SAP Consolidado > Venda Mes a Mes: 493 clientes com CNPJ, mensal com Quantidade/Vendas/Devolucoes/Faturado
   - BASE_SAP_VENDA_MES_A_MES: 12 abas separadas, codigo SAP + nome (sem CNPJ direto)
   - Recommendation: Usar SAP Consolidado (Venda Mes a Mes) pois ja tem CNPJ direto. O outro requer parsing de strings.

## Validation Strategy

### Checklist de Validacao da Fase 1
1. **Formula integrity:** 19.224 formulas intactas (36 colunas * 534 rows)
2. **Data population:** Colunas AA-AL (REALIZADO) populadas com vendas 2025
3. **Meta values:** Coluna L (META ANUAL) com valores SAP 2026
4. **CNPJ integrity:** 534 CNPJs unicos, 14 digitos, string, sem duplicatas
5. **Totals check:** Z (REAL ANUAL) = SUM(AA:AL) recalcula corretamente
6. **Indicadores:** AN (% YTD), AO (sinaleiro), AP (GAP), AQ (RANKING) funcionam
7. **Lookup table:** AS:AX com 15 redes intactas
8. **Number formats:** R$ para valores monetarios, % para percentuais
9. **Freeze panes:** C4 mantido
10. **Auto-filter:** A3:CB537 mantido

### Numeros de Referencia
- Total META SAP 2026: R$ 4.747.200
- Meta mensal minima (JAN): R$ 333.600
- Meta mensal maxima (DEZ): R$ 459.300
- Clientes com meta: 534
- Redes na tabela auxiliar: 15
- Formulas totais: 19.224

## Sources

### Primary (HIGH confidence)
- Analise direta dos arquivos Excel com openpyxl 3.1.5 (16/FEV/2026)
- PROJECAO_534_INTEGRADA.xlsx: 19.224 formulas verificadas celula por celula
- CRM V12 (2): Confirmado identico ao 534_INTEGRADA (CNPJs, formulas, valores)
- 01_SAP_CONSOLIDADO.xlsx: 1.698 mapeamentos CNPJ<->SAP verificados
- BASE_SAP_META_PROJECAO_2026.xlsx: R$ 4.747.200 total confirmado

### Secondary (MEDIUM confidence)
- Pesos de distribuicao mensal extraidos de PROJECAO_CORRIGIDA (2).xlsx -- confirmados contra metas SAP (100% match)
- Scripts existentes em scripts/ como referencia de logica previa

### Tertiary (LOW confidence)
- Relacao entre meta individual e meta total SAP (discrepancia de 0.67% nao investigada a fundo)
- Escolha de thresholds de sinaleiro (depende de decisao do usuario)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - openpyxl 3.1.5 testado e confirmado para todos os tipos de formula necessarios
- Architecture: HIGH - Analise direta de todos os arquivos fontes com verificacao cruzada
- Pitfalls: HIGH - Cada pitfall identificado por evidencia direta na analise dos dados
- Data mapping: MEDIUM - Mapeamento CNPJ<->SAP verificado mas discrepancia de 0.67% pendente investigacao

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (estavel -- arquivos de origem sao estaticos)
