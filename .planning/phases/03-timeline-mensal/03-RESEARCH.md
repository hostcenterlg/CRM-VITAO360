# Phase 3: Timeline Mensal - Research

**Researched:** 2026-02-17
**Domain:** Popular vendas mes a mes na CARTEIRA (via DRAFT 1), cruzar SAP+Mercos, recalcular Classificacao ABC
**Confidence:** HIGH

## Summary

A Fase 3 tem como objetivo popular as vendas mensais por cliente na CARTEIRA do CRM. A investigacao revelou uma **arquitetura em cascata** critica que muda completamente a abordagem: a CARTEIRA nao armazena dados diretamente -- ela usa formulas `INDEX/MATCH` que puxam dados do **DRAFT 1**. Portanto, **popular a CARTEIRA = popular o DRAFT 1 com vendas mensais + garantir que CARTEIRA tenha as formulas INDEX/MATCH para todos os clientes**.

**Descobertas criticas:**

1. **V13 NAO tem CARTEIRA** -- o arquivo V13 (CRM_VITAO360_V13_PROJECAO.xlsx) contem apenas a aba PROJECAO. A CARTEIRA, DRAFT 1, DRAFT 2, LOG e todas as outras abas existem apenas no V12 COM_DADOS.

2. **V12 CARTEIRA tem apenas 3 rows de dados** (rows 4-6) com formulas INDEX/MATCH que puxam do DRAFT 1. Porem o **DRAFT 1 ja tem 502 rows de dados** com CNPJs, vendas mensais (MAR-JAN/26), e CURVA ABC. O DRAFT 1 e a **fonte intermediaria de dados** da CARTEIRA.

3. **O sap_mercos_merged.json tem 537 clientes** com arrays de 12 meses (JAN-DEZ 2025). O DRAFT 1 existente tem 502 rows (fonte Mercos). A diferenca sao os clientes SAP-only (76 clientes) + 8 fuzzy-matched -- esses precisam ser adicionados.

4. **A Classificacao ABC ja existe em 3 formas independentes:** (a) Formula no DRAFT 1: `=IF(AK4>=2000,"A",IF(AK4>=500,"B","C"))` onde AK4=TOTAL PERIODO, (b) Arquivo 04_CURVA_ABC_MERCOS.xlsx com 483 clientes e classificacao mensal por mes, (c) Criterio documentado no MANUAL: A>=R$2000, B>=R$500, C<R$500.

**Primary recommendation:** Popular o DRAFT 1 com os dados do sap_mercos_merged.json (537 clientes), recalcular campos derivados (TOTAL PERIODO, Nro COMPRAS, MESES POSITIVADO, CURVA ABC, MEDIA MENSAL, TICKET MEDIO), e expandir as 3 rows de formulas INDEX/MATCH da CARTEIRA para cobrir todos os 537 clientes. A classificacao ABC deve usar os thresholds documentados (A>=2000, B>=500, C<500) sobre o total acumulado do periodo (MAR/25-JAN/26).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.5 | Leitura/escrita de Excel .xlsx preservando formulas | Unico que preserva formulas nativas -- ja validado em Phases 1+2 |
| Python | 3.12.10 | Runtime | Instalado via pyenv: `/c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe` |
| json | stdlib | Carregar sap_mercos_merged.json e demais JSONs | Formato intermediario padrao do projeto |
| re | stdlib | Normalizacao CNPJ | Funcao padronizada `normalize_cnpj()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| collections.Counter | stdlib | Contagem de distribuicao ABC | Para relatorio de validacao |
| datetime | stdlib | Conversao de datas Excel serial | Para headers de colunas que sao date serial numbers |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Popular DRAFT 1 diretamente | Popular CARTEIRA direto | CARTEIRA usa INDEX/MATCH do DRAFT 1. Popular a CARTEIRA direto quebraria a arquitetura de formulas. Sempre popular via DRAFT 1. |
| Recriar V13 com CARTEIRA | Usar V12 COM_DADOS como base | V13 so tem PROJECAO. O V12 COM_DADOS e o arquivo que tem TODAS as abas. Phase 3 deve operar sobre V12 COM_DADOS. |
| ABC formula | ABC data-driven | A formula `=IF(>=2000,"A",...)` e mais fragil (hardcoded). Melhor escrever o valor ABC diretamente no DRAFT 1 e ter a formula como backup na CARTEIRA. |

**Installation:**
```bash
# Ja instalado
pip install openpyxl==3.1.5
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  phase03_timeline/
    01_populate_draft1_vendas.py    # Popular DRAFT 1 com vendas do merged JSON
    02_expand_carteira_formulas.py  # Expandir formulas INDEX/MATCH para 537 rows
    03_recalc_abc_validate.py       # Recalcular ABC, validar totais
data/
  output/
    phase03/
      draft1_population_report.json  # Relatorio de populacao do DRAFT 1
      abc_classification.json        # Classificacao ABC final com distribuicao
      validation_report.json         # Validacao de totais e cruzamento
```

### Pattern 1: DRAFT 1 como Camada de Dados, CARTEIRA como Camada de Formulas
**What:** O CRM V12 usa uma arquitetura em cascata: DRAFT 1 armazena dados brutos (valores), CARTEIRA referencia via INDEX/MATCH. Para popular a CARTEIRA, e preciso popular o DRAFT 1 primeiro.
**When to use:** SEMPRE ao manipular dados de vendas no CRM.
**Evidencia:** Todas as formulas encontradas na CARTEIRA (rows 5-8) seguem o padrao:
```
=IFERROR(INDEX('DRAFT 1'!$U:$U,MATCH($B5,'DRAFT 1'!$B:$B,0)),"")
```
Onde `$B` e a coluna CNPJ em ambas as abas.

**Mapeamento DRAFT 1 -> CARTEIRA (colunas de vendas):**
```
DRAFT 1         CARTEIRA        Conteudo
Col 21 (MAR/25) -> Col 26       via INDEX('DRAFT 1'!$U:$U, MATCH($B, 'DRAFT 1'!$B:$B, 0))
Col 22 (ABR/25) -> Col 27       via INDEX('DRAFT 1'!$V:$V, ...)
Col 23 (MAI/25) -> Col 28       via INDEX('DRAFT 1'!$W:$W, ...)
Col 24 (JUN/25) -> Col 29       via INDEX('DRAFT 1'!$X:$X, ...)
Col 25 (JUL/25) -> Col 30       via INDEX('DRAFT 1'!$Y:$Y, ...)
Col 26 (AGO/25) -> Col 31       via INDEX('DRAFT 1'!$Z:$Z, ...)
Col 27 (SET/25) -> Col 32       via INDEX('DRAFT 1'!$AA:$AA, ...)
Col 28 (OUT/25) -> Col 33       via INDEX('DRAFT 1'!$AB:$AB, ...)
Col 29 (NOV/25) -> Col 34       via INDEX('DRAFT 1'!$AC:$AC, ...)
Col 30 (DEZ/25) -> Col 35       via INDEX('DRAFT 1'!$AD:$AD, ...)
Col 31 (JAN/26) -> Col 36       via INDEX('DRAFT 1'!$AE:$AE, ...)
Col 35 (ABC)    -> Col 39       via INDEX('DRAFT 1'!$AI:$AI, ...)
Col 34 (COMPRAS)-> Col 38       via INDEX('DRAFT 1'!$AH:$AH, ...)
Col 36 (POSIT)  -> Col 40       via INDEX('DRAFT 1'!$AJ:$AJ, ...)
```

### Pattern 2: Merged JSON como Fonte Unica de Verdade
**What:** O sap_mercos_merged.json produzido na Phase 2 contem os dados definitivos: 537 CNPJs com arrays de 12 floats (JAN=idx0 a DEZ=idx11).
**When to use:** Para popular vendas mensais. NAO re-extrair de Mercos/SAP.
**Formato:**
```python
# sap_mercos_merged.json
{
  "cnpj_to_vendas": {
    "00939085000178": [0.0, 0.0, 0.0, 4924.71, 0.0, 5040.0, 0.0, 0.0, 5037.0, 10920.0, 5490.9, 7674.6],
    ...
  },
  "jan26_vendas": { "00939085000178": 15300.0, ... },  // JAN/26 separado
  "stats": {
    "sap_only": 76,
    "mercos_only": 40,
    "both_sap_base": 413,
    "total_clientes": 537,
    "total_vendas_2025": 2493521.92,
    "total_jan26": 114038.03
  }
}
```

**MAPEAMENTO de indices JSON -> colunas DRAFT 1:**
```
JSON idx 0 (JAN/25): NAO TEM COLUNA no DRAFT 1 (DRAFT 1 comeca em MAR/25)
JSON idx 1 (FEV/25): NAO TEM COLUNA no DRAFT 1
JSON idx 2 (MAR/25): DRAFT 1 col 21
JSON idx 3 (ABR/25): DRAFT 1 col 22
JSON idx 4 (MAI/25): DRAFT 1 col 23
JSON idx 5 (JUN/25): DRAFT 1 col 24
JSON idx 6 (JUL/25): DRAFT 1 col 25
JSON idx 7 (AGO/25): DRAFT 1 col 26
JSON idx 8 (SET/25): DRAFT 1 col 27
JSON idx 9 (OUT/25): DRAFT 1 col 28
JSON idx 10(NOV/25): DRAFT 1 col 29
JSON idx 11(DEZ/25): DRAFT 1 col 30
jan26_vendas[cnpj]:  DRAFT 1 col 31
```

### Pattern 3: ABC Classification por Total Acumulado
**What:** Classificar cada cliente como A, B ou C com base no total de vendas acumulado no periodo.
**Thresholds (documentados no MANUAL e na SPEC):**
```
A: Total Periodo >= R$ 2.000
B: Total Periodo >= R$ 500
C: Total Periodo < R$ 500
```
**Formula Excel (DRAFT 1 col 35):** `=IF(AK4>=2000,"A",IF(AK4>=500,"B","C"))`
**Nota:** AK4 no template e col 37 (TOTAL VENDAS PERIODO) que e `=SUM(Y4:AJ4)` -- porem no DRAFT 1 do V12 COM_DADOS, a coluna de vendas comeca em col 21. Conferir mapeamento exato antes de escrever.

### Pattern 4: Campos Derivados a Calcular
**What:** Alem das vendas mensais, o DRAFT 1 tem campos calculados que dependem dos dados de vendas.
**Campos:**
```
TOTAL PERÍODO (col 18 ou similar)  = SUM de todas as vendas mensais
Nº COMPRAS (col 34)                = COUNT de meses com vendas > 0
CURVA ABC (col 35)                 = IF(TOTAL>=2000,"A",IF(TOTAL>=500,"B","C"))
MESES POSITIVADO (col 36)          = COUNT de meses com vendas > 0
TICKET MÉDIO (col 37)              = TOTAL / Nº COMPRAS (se > 0, senao 0)
MÉDIA MENSAL (col 43)              = TOTAL / MESES POSITIVADO (se > 0, senao 0)
CICLO MÉDIO (col 33)               = Calculo baseado em datas de pedidos
OPORTUNIDADE (col 20)              = Based on B2B access
```

### Anti-Patterns to Avoid
- **NAO popular CARTEIRA diretamente com valores:** CARTEIRA usa INDEX/MATCH do DRAFT 1. Se voce escrever valores nas colunas de vendas da CARTEIRA, as formulas serao destruidas.
- **NAO ignorar JAN/25 e FEV/25:** O merged JSON tem indices 0 e 1 (JAN e FEV) mas o DRAFT 1 comeca em MAR/25. Esses 2 meses devem ser incluidos no TOTAL PERIODO mas NAO tem coluna individual no DRAFT 1.
- **NAO tratar ABC como formula no DRAFT 1:** O DRAFT 1 pode ter a formula OU o valor. Para 537 clientes, e mais seguro escrever o valor ABC diretamente (evita dependencia de formula sobre coluna de total que pode estar em posicao diferente).
- **NAO assumir que DRAFT 1 tem 502 CNPJs = 502 CNPJs validos:** Verificar que todos os 502 rows tem CNPJ valido (14 digitos).
- **NAO sobrescrever rows existentes no DRAFT 1 sem verificar:** Merge incremental: atualizar rows existentes (por CNPJ match), adicionar rows novos (SAP-only + fuzzy).

## Data Architecture Discovery

### Estado Atual dos Arquivos

| Arquivo | Aba | Data Rows | Colunas Vendas | ABC | Papel |
|---------|-----|-----------|----------------|-----|-------|
| V13 (PROJECAO) | PROJECAO | 489+ | N/A | N/A | Apenas formulas de projecao |
| V12 COM_DADOS | CARTEIRA | 3 | Cols 26-36 (INDEX/MATCH) | Col 39 (INDEX/MATCH) | Camada de visualizacao/formulas |
| V12 COM_DADOS | DRAFT 1 | 502 | Cols 21-31 (MAR-JAN/26) | Col 35 (valor) | Camada de dados |
| V12 COM_DADOS | DRAFT 2 | ~6.775 | N/A | N/A | LOG de atendimentos |
| sap_mercos_merged.json | - | 537 CNPJs | 12 indices (JAN-DEZ) | N/A | Fonte de verdade Phase 2 |

### Cascata de Dados (Fluxo)
```
sap_mercos_merged.json (537 clientes, 12 meses)
    |
    v
DRAFT 1 (502 -> 537+ rows, dados brutos: vendas + ABC + metricas)
    |
    v (INDEX/MATCH por CNPJ)
CARTEIRA (3 -> 537+ rows, formulas que puxam do DRAFT 1)
    |
    v (formulas referenciam CARTEIRA)
DASH, PROJECAO, AGENDA, etc. (consumidores finais)
```

### CARTEIRA Column Map (V12 COM_DADOS, confirmado por inspecao)
```
Col  1: NOME FANTASIA        (ANCORA)
Col  2: CNPJ                 (IDENTIDADE)
Col  3: RAZAO SOCIAL         (IDENTIDADE)
Col  4: UF                   (IDENTIDADE)
Col  5: CIDADE               (IDENTIDADE)
Col  6: EMAIL                (IDENTIDADE)
Col  7: TELEFONE             (IDENTIDADE)
Col  8: DATA CADASTRO        (IDENTIDADE)
Col  9: REDE REGIONAL        (REDE)
Col 10: TIPO CLIENTE          (REDE)
Col 11: ULT REGISTRO MERCOS  (REDE)
Col 12: CONSULTOR            (EQUIPE)
Col 13: VENDEDOR ULT PEDIDO  (EQUIPE)
Col 14: SITUACAO             (STATUS)
Col 15: PRIORIDADE           (STATUS)
Col 16: DIAS SEM COMPRA      (COMPRA)
Col 17: DATA ULT PEDIDO      (COMPRA)
Col 18: VALOR ULT PEDIDO     (COMPRA)
Col 19: CICLO MEDIO          (COMPRA)
Col 20: ACESSO B2B           (ECOMMERCE)
Col 21: ACESSOS PORTAL       (ECOMMERCE)
Col 22: ITENS CARRINHO       (ECOMMERCE)
Col 23: VALOR B2B            (ECOMMERCE)
Col 24: OPORTUNIDADE         (ECOMMERCE)
Col 25: TOTAL PERIODO        (VENDAS) -- FORMULA: =SUM(Z7:AJ7)
Col 26: MAR/25 (serial 45717)(VENDAS) -- INDEX/MATCH do DRAFT 1
Col 27: ABR/25 (serial 45748)(VENDAS)
Col 28: MAI/25 (serial 45778)(VENDAS)
Col 29: JUN/25 (serial 45809)(VENDAS)
Col 30: JUL/25 (serial 45839)(VENDAS)
Col 31: AGO/25 (serial 45870)(VENDAS)
Col 32: SET/25 (serial 45901)(VENDAS)
Col 33: OUT/25 (serial 45931)(VENDAS)
Col 34: NOV/25 (serial 45962)(VENDAS)
Col 35: DEZ/25 (serial 45992)(VENDAS)
Col 36: JAN/26 (serial 46023)(VENDAS)
Col 37: TIPO CLIENTE          (ANCORA)
Col 38: Nro COMPRAS          (RECORRENCIA)
Col 39: CURVA ABC            (RECORRENCIA)
Col 40: MESES POSITIVADO     (RECORRENCIA)
Col 41: MEDIA MENSAL         (RECORRENCIA)
Col 42: TICKET MEDIO         (RECORRENCIA)
Col 43: MESES LISTA          (RECORRENCIA)
Cols 44-62: FUNIL (ESTAGIO, PIPELINE, PERFIL, MATURIDADE, CONVERSAO, ACAO, SINALEIRO)
Cols 63-78: SAP (CODIGO, CNPJ, RAZAO, CADASTRO, GRUPO CHAVE, etc.)
Cols 79-263: ACOMPANHAMENTO (% ALCANCADO, Q1-Q4, 15 cols/mes x 12 meses)
```

### DRAFT 1 Column Map (V12 COM_DADOS, confirmado por inspecao)
```
Col  1: NOME FANTASIA
Col  2: CNPJ
Col  3: RAZAO SOCIAL
Col  4: UF
Col  5: CIDADE
Col  6: EMAIL
Col  7: TELEFONE
Col  8: DATA CADASTRO
Col  9: REDE / REGIONAL
Col 10: CONSULTOR
Col 11: VENDEDOR ULTIMO PEDIDO
Col 12: DIAS SEM COMPRA
Col 13: DATA ULTIMO PEDIDO
Col 14: VALOR ULTIMO PEDIDO
Col 15: ACESSOS SEMANA
Col 16: ACESSO B2B
Col 17: ACESSOS PORTAL
Col 18: ITENS CARRINHO
Col 19: VALOR B2B
Col 20: OPORTUNIDADE
Col 21: MAR/25               ** VENDAS MENSAIS INICIO **
Col 22: ABR/25
Col 23: MAI/25
Col 24: JUN/25
Col 25: JUL/25
Col 26: AGO/25
Col 27: SET/25
Col 28: OUT/25
Col 29: NOV/25
Col 30: DEZ/25
Col 31: JAN/26
Col 32: FEV/26               ** VENDAS MENSAIS FIM **
Col 33: CICLO MEDIO
Col 34: Nro COMPRAS
Col 35: CURVA ABC
Col 36: MESES POSITIVADO
Col 37: TICKET MEDIO
Col 38: ULT. REGISTRO MERCOS
Col 39: DATA ULT. ATENDIMENTO MERCOS
Col 40: TIPO ATENDIMENTO MERCOS
Col 41: OBS ATENDIMENTO MERCOS
Col 42: TIPO CLIENTE
Col 43: MEDIA MENSAL
Col 44: IDENTIDADE (A-K) -- fonte dos dados
Col 45: Carteira Detalhada de Clientes
```

## Don't Hand-Roll

| Problema | Nao Construir | Usar Em Vez | Porque |
|----------|---------------|-------------|--------|
| Extracao de vendas SAP+Mercos | Re-extrair de fontes brutas | sap_mercos_merged.json (Phase 2 output) | Ja consolidado com 537 clientes, SAP-First strategy, fuzzy matches |
| Matching CNPJ | Novo motor de matching | CNPJ como chave direta (14 digitos) | Phase 2 ja resolveu todos os matchings |
| Normalizacao CNPJ | Regex ad-hoc | `normalize_cnpj()` padrao do projeto | `re.sub(r'[^0-9]', '', str(raw)).zfill(14)` |
| Classificacao ABC | Algoritmo complexo de percentis | Thresholds fixos A>=2000, B>=500, C<500 | Documentado no MANUAL, implementado na formula, confirmado no SPEC |

**Key insight:** O trabalho pesado ja foi feito na Phase 2 (extracao, merge, matching). Phase 3 e fundamentalmente um trabalho de **populacao de planilha** + **calculo de metricas derivadas** + **expansao de formulas**. Nao ha ETL novo a fazer.

## Common Pitfalls

### Pitfall 1: Popular CARTEIRA Direto ao Inves do DRAFT 1
**What goes wrong:** Escrever valores de vendas diretamente nas colunas 26-36 da CARTEIRA sobrescreve as formulas INDEX/MATCH.
**Why it happens:** A CARTEIRA aparenta ser a aba "principal" e tem as colunas de vendas visiveis.
**How to avoid:** SEMPRE popular o DRAFT 1. A CARTEIRA puxa dados do DRAFT 1 via INDEX/MATCH.
**Warning signs:** Se apos popular, a CARTEIRA nao mostra os dados = formulas INDEX/MATCH estao quebradas ou ausentes.

### Pitfall 2: Desalinhamento de Colunas DRAFT 1 vs Merged JSON
**What goes wrong:** Escrever vendas de MAR na coluna de ABR por confusao nos indices.
**Why it happens:** O merged JSON usa indices 0-11 (JAN-DEZ), mas DRAFT 1 comeca em MAR/25 (col 21). O offset e 2 meses.
**How to avoid:** Criar mapeamento explicito:
```python
# JSON index -> DRAFT 1 column
JSON_TO_DRAFT1 = {
    2: 21,   # MAR -> Col 21
    3: 22,   # ABR -> Col 22
    4: 23,   # MAI -> Col 23
    5: 24,   # JUN -> Col 24
    6: 25,   # JUL -> Col 25
    7: 26,   # AGO -> Col 26
    8: 27,   # SET -> Col 27
    9: 28,   # OUT -> Col 28
    10: 29,  # NOV -> Col 29
    11: 30,  # DEZ -> Col 30
}
# JAN/26 from jan26_vendas -> Col 31
# JAN/25 (idx 0) e FEV/25 (idx 1) NAO TEM COLUNA
```

### Pitfall 3: Expansao de CARTEIRA sem Formulas
**What goes wrong:** Adicionar rows na CARTEIRA com valores em vez de formulas INDEX/MATCH. Quando o DRAFT 1 e atualizado, a CARTEIRA nao reflete.
**Why it happens:** E mais facil copiar valores do que construir 30+ formulas por row.
**How to avoid:** Usar template de formulas da row 7 (que tem formulas completas) e replicar para todas as novas rows.
**Template (row 7):**
```python
# Para cada coluna com formula na CARTEIRA:
formulas = {
    16: '=IFERROR(INDEX(\'DRAFT 1\'!$L:$L,MATCH($B{r},\'DRAFT 1\'!$B:$B,0)),"")'),
    # ... (16-24, 26-36, 38-42)
    25: '=SUM(Z{r}:AJ{r})',  # TOTAL PERIODO
    41: '=IFERROR(Y{r}/AN{r},0)',  # MEDIA MENSAL (Y=TOTAL, AN=MESES POSITIVADO)
}
```

### Pitfall 4: CNPJ como Float no DRAFT 1
**What goes wrong:** CNPJs com zero a esquerda perdem o zero: "04351343000169" -> 4351343000169.
**Why it happens:** openpyxl pode interpretar como numero ao ler/escrever.
**How to avoid:** Sempre ler como `str(raw).replace('.0', '')` e escrever como string. Verificar que todos os 537 CNPJs tem 14 caracteres apos normalizacao.

### Pitfall 5: 04_CURVA_ABC_MERCOS vs ABC Recalculado
**What goes wrong:** A classificacao ABC do 04_CURVA_ABC_MERCOS (483 clientes, por mes) nao bate com o ABC recalculado sobre o total acumulado.
**Why it happens:** O 04_CURVA_ABC classifica MES A MES (cada mes independente), enquanto o DRAFT 1 e a CARTEIRA classificam pelo TOTAL ACUMULADO do periodo.
**How to avoid:** Usar os thresholds do MANUAL/SPEC sobre o TOTAL ACUMULADO. O 04_CURVA_ABC e apenas referencia historica, nao fonte para a classificacao final.
**Distribuicao esperada (baseada em 04_CURVA_ABC anual):** A=191, B=162, C=115 (468 clientes Mercos). Com SAP adicionado, a distribuicao deve mudar.

### Pitfall 6: V13 NAO Tem CARTEIRA
**What goes wrong:** Tentar operar sobre V13 para popular a CARTEIRA.
**Why it happens:** O nome "V13" sugere que e a versao mais recente e completa.
**How to avoid:** V13 so tem PROJECAO (19.224 formulas). Usar V12 COM_DADOS para tudo que envolve CARTEIRA, DRAFT 1, DRAFT 2, LOG. A consolidacao final (Phase 10) unificara V13 PROJECAO + V12 demais abas.

### Pitfall 7: JAN/25 e FEV/25 Perdidos
**What goes wrong:** Os meses JAN/25 (idx 0) e FEV/25 (idx 1) do merged JSON nao tem coluna no DRAFT 1 nem na CARTEIRA.
**Why it happens:** O DRAFT 1 comeca em MAR/25. A CARTEIRA espelha o DRAFT 1.
**How to avoid:** Incluir JAN/25 e FEV/25 no calculo do TOTAL PERIODO e em metricas derivadas (Nro COMPRAS, MESES POSITIVADO), mesmo sem coluna individual. Documentar que 2 meses sao "embutidos" no total mas nao tem visibilidade mensal.
**Impacto:** Para 76 clientes SAP-only, JAN/25 pode ter vendas significativas (R$80k total no PAINEL). Esses valores entram no total mas nao sao visiveis individualmente.

## Code Examples

### Exemplo 1: Carregar Merged JSON e Preparar para DRAFT 1
```python
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MERGED_PATH = PROJECT_ROOT / "data" / "output" / "phase02" / "sap_mercos_merged.json"

def normalize_cnpj(raw):
    if raw is None: return None
    clean = re.sub(r'[^0-9]', '', str(raw))
    return clean.zfill(14) if len(clean) >= 11 else None

def load_merged():
    with open(MERGED_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['cnpj_to_vendas'], data.get('jan26_vendas', {}), data['stats']

# JSON idx -> DRAFT 1 column mapping
JSON_IDX_TO_DRAFT1_COL = {
    2: 21,   # MAR -> Col 21
    3: 22,   # ABR
    4: 23,   # MAI
    5: 24,   # JUN
    6: 25,   # JUL
    7: 26,   # AGO
    8: 27,   # SET
    9: 28,   # OUT
    10: 29,  # NOV
    11: 30,  # DEZ
}
JAN26_COL = 31
```

### Exemplo 2: Popular DRAFT 1 com Vendas Mensais
```python
import openpyxl

def populate_draft1(wb_path, cnpj_to_vendas, jan26_vendas, output_path):
    """Populate DRAFT 1 with vendas from merged JSON."""
    wb = openpyxl.load_workbook(wb_path, data_only=False)
    ws = wb['DRAFT 1']

    # 1. Build existing CNPJ -> row map
    existing = {}  # cnpj -> row_number
    for row in range(4, ws.max_row + 1):
        raw = ws.cell(row, 2).value
        cnpj = normalize_cnpj(raw)
        if cnpj:
            existing[cnpj] = row

    updated = 0
    added = 0
    next_row = ws.max_row + 1

    for cnpj, vendas in cnpj_to_vendas.items():
        if cnpj in existing:
            row = existing[cnpj]
        else:
            row = next_row
            ws.cell(row, 2).value = cnpj  # CNPJ col 2
            next_row += 1
            added += 1

        # Write monthly vendas (MAR-DEZ)
        for json_idx, col in JSON_IDX_TO_DRAFT1_COL.items():
            val = vendas[json_idx]
            ws.cell(row, col).value = val if val > 0 else 0

        # JAN/26
        jan26 = jan26_vendas.get(cnpj, 0)
        ws.cell(row, JAN26_COL).value = jan26 if jan26 > 0 else 0

        # Calculate derived fields
        total_all = sum(vendas) + jan26  # Include JAN/25 + FEV/25
        total_visible = sum(vendas[2:]) + jan26  # MAR-DEZ + JAN/26
        meses_pos = sum(1 for v in vendas if v > 0) + (1 if jan26 > 0 else 0)
        n_compras = meses_pos  # Each positive month = 1 purchase

        # TOTAL PERIODO (varies by position)
        # Need to find correct column -- check template

        # CURVA ABC
        abc = 'A' if total_all >= 2000 else ('B' if total_all >= 500 else 'C')
        ws.cell(row, 35).value = abc

        # Nro COMPRAS
        ws.cell(row, 34).value = n_compras

        # MESES POSITIVADO
        ws.cell(row, 36).value = meses_pos

        # TICKET MEDIO
        ws.cell(row, 37).value = round(total_all / n_compras, 2) if n_compras > 0 else 0

        # MEDIA MENSAL
        ws.cell(row, 43).value = round(total_all / meses_pos, 2) if meses_pos > 0 else 0

        if cnpj in existing:
            updated += 1

    wb.save(output_path)
    wb.close()
    return updated, added
```

### Exemplo 3: Expandir Formulas da CARTEIRA
```python
def expand_carteira_formulas(wb_path, total_rows, output_path):
    """Expand CARTEIRA INDEX/MATCH formulas for all data rows."""
    wb = openpyxl.load_workbook(wb_path, data_only=False)
    ws = wb['CARTEIRA']

    # Template: use row 7 formulas (most complete found in inspection)
    # Columns that need INDEX/MATCH formulas from DRAFT 1:
    # 16-24 (COMPRA + ECOMMERCE), 26-36 (VENDAS), 38-42 (RECORRENCIA)
    FORMULA_COLS = {
        16: "=IFERROR(INDEX('DRAFT 1'!$L:$L,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        17: "=IFERROR(INDEX('DRAFT 1'!$M:$M,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        18: "=IFERROR(INDEX('DRAFT 1'!$N:$N,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        19: "=IFERROR(INDEX('DRAFT 1'!$O:$O,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        20: "=IFERROR(INDEX('DRAFT 1'!$P:$P,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        21: "=IFERROR(INDEX('DRAFT 1'!$Q:$Q,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        22: "=IFERROR(INDEX('DRAFT 1'!$R:$R,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        23: "=IFERROR(INDEX('DRAFT 1'!$S:$S,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        24: "=IFERROR(INDEX('DRAFT 1'!$T:$T,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        25: "=SUM(Z{r}:AJ{r})",  # TOTAL PERIODO
        26: "=IFERROR(INDEX('DRAFT 1'!$U:$U,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        27: "=IFERROR(INDEX('DRAFT 1'!$V:$V,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        28: "=IFERROR(INDEX('DRAFT 1'!$W:$W,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        29: "=IFERROR(INDEX('DRAFT 1'!$X:$X,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        30: "=IFERROR(INDEX('DRAFT 1'!$Y:$Y,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        31: "=IFERROR(INDEX('DRAFT 1'!$Z:$Z,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        32: "=IFERROR(INDEX('DRAFT 1'!$AA:$AA,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        33: "=IFERROR(INDEX('DRAFT 1'!$AB:$AB,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        34: "=IFERROR(INDEX('DRAFT 1'!$AC:$AC,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        35: "=IFERROR(INDEX('DRAFT 1'!$AD:$AD,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        36: "=IFERROR(INDEX('DRAFT 1'!$AE:$AE,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        38: "=IFERROR(INDEX('DRAFT 1'!$AH:$AH,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        39: "=IFERROR(INDEX('DRAFT 1'!$AI:$AI,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        40: "=IFERROR(INDEX('DRAFT 1'!$AJ:$AJ,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
        41: "=IFERROR(Y{r}/AN{r},0)",  # MEDIA MENSAL
        42: "=IFERROR(INDEX('DRAFT 1'!$AK:$AK,MATCH($B{r},'DRAFT 1'!$B:$B,0)),\"\")",
    }

    # For each row, write CNPJ in col B and formulas
    for row in range(4, 4 + total_rows):
        for col, template in FORMULA_COLS.items():
            formula = template.format(r=row)
            ws.cell(row, col).value = formula

    wb.save(output_path)
    wb.close()
```

### Exemplo 4: Classificacao ABC e Validacao
```python
def classify_abc(cnpj_to_vendas, jan26_vendas):
    """Classify all clients into A/B/C based on total vendas."""
    classification = {}
    distribution = {'A': 0, 'B': 0, 'C': 0}

    for cnpj, vendas in cnpj_to_vendas.items():
        jan26 = jan26_vendas.get(cnpj, 0)
        total = sum(vendas) + jan26  # All months including JAN/FEV 2025

        if total >= 2000:
            abc = 'A'
        elif total >= 500:
            abc = 'B'
        else:
            abc = 'C'

        classification[cnpj] = {
            'abc': abc,
            'total': total,
            'meses_positivos': sum(1 for v in vendas if v > 0) + (1 if jan26 > 0 else 0)
        }
        distribution[abc] += 1

    return classification, distribution
```

## State of the Art

| Aspecto | Estado Atual | O que Falta para Phase 3 |
|---------|-------------|--------------------------|
| sap_mercos_merged.json | 537 clientes, 12 meses, pronto | Nada -- usar como fonte |
| DRAFT 1 (V12) | 502 rows com dados Mercos | +35 rows SAP-only, atualizar vendas do merged |
| CARTEIRA (V12) | 3 rows com formulas INDEX/MATCH | Expandir para 537+ rows com formulas |
| ABC Classification | Formula no DRAFT 1 template + 04_CURVA_ABC_MERCOS | Recalcular com dados merged (total acumulado) |
| V13 | Apenas PROJECAO (19.224 formulas) | Nao precisa de CARTEIRA ate Phase 9 |
| Campos derivados | Template em DRAFT 1 row 4 | Calcular para todos os 537 clientes |
| PAINEL Validation | Gap documentado (15.65%) | Cruzar totais CARTEIRA vs merged |

## Open Questions

1. **Os 502 rows do DRAFT 1 existente ja tem dados de vendas Mercos-only -- devemos sobrescrever com merged?**
   - O que sabemos: DRAFT 1 tem 502 rows com vendas Mercos. O merged JSON tem 537 clientes com SAP-First + Mercos complement.
   - O que e incerto: Os valores Mercos no DRAFT 1 existente podem ser diferentes dos valores no merged (que ja tem SAP preenchendo gaps).
   - Recomendacao: SOBRESCREVER com os dados do merged JSON. O merged e mais completo e preciso (SAP-First com Mercos complement para 160 month-cells).

2. **A CARTEIRA precisa de CNPJ + NOME FANTASIA nas colunas A e B para as formulas INDEX/MATCH funcionarem. De onde vem esses dados?**
   - O que sabemos: CARTEIRA col 1 = NOME FANTASIA, col 2 = CNPJ. As formulas usam $B (CNPJ) para MATCH.
   - O que e incerto: O DRAFT 1 existente tem nomes e CNPJs. Mas para os 35+ novos clientes (SAP-only), precisamos de nomes.
   - Recomendacao: Buscar nomes no 01_SAP_CONSOLIDADO.xlsx (Cadastro Clientes SAP) ou no merged JSON. Para a CARTEIRA, copiar NOME e CNPJ do DRAFT 1 populado.

3. **O TOTAL PERIODO na CARTEIRA e `=SUM(Z7:AJ7)` -- quais sao as colunas Z a AJ?**
   - O que sabemos: A formula referencia Z a AJ (colunas 26 a 36 no formato A1) que sao exatamente as colunas de vendas mensais MAR-JAN/26. Porem a formula na CARTEIRA usa referencia de coluna por LETRA, nao por numero.
   - O que e incerto: Se a formula referencia correta e Z:AJ ou se deve incluir JAN/25 + FEV/25.
   - Recomendacao: Manter `=SUM(Z{r}:AJ{r})` para as 11 colunas visiveis. Documentar que JAN/25 + FEV/25 nao estao incluidos no TOTAL PERIODO visivel da CARTEIRA. Considerar coluna extra no DRAFT 1 para total "completo" incluindo JAN/FEV.

4. **A formula CARTEIRA col 25 = `=SUM(Z7:AJ7)` mas col Z = col 26 e col AJ = col 36. Isso confirma o mapeamento?**
   - Confirmado: Z = coluna 26 em notacao R1C1. AJ = coluna 36. O SUM cobre exatamente as 11 colunas de vendas mensais (MAR/25 a JAN/26).
   - Nao ha discrepancia.

5. **Devemos manter as formulas do DRAFT 1 ou substituir por valores calculados?**
   - O DRAFT 1 template (v3_draft1.py) usa formulas para ABC, MEDIA MENSAL, TICKET MEDIO. Porem, com 537 rows, e mais robusto escrever valores diretamente (evita erro de formula).
   - Recomendacao: Escrever VALORES no DRAFT 1 (dados), manter FORMULAS na CARTEIRA (camada de visualizacao). Essa e a arquitetura original: DRAFT 1 = dados, CARTEIRA = formulas que puxam dados.

## Sources

### Primary (HIGH confidence)
- `data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` -- Inspecao direta: CARTEIRA (3 rows, 263 cols), DRAFT 1 (502 rows, 45 cols), formulas INDEX/MATCH confirmadas
- `data/output/phase02/sap_mercos_merged.json` -- 537 CNPJs com 12-month arrays, stats, jan26_vendas
- `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` -- Confirmado: apenas 1 aba (PROJECAO), sem CARTEIRA
- `data/sources/mercos/04_CURVA_ABC_MERCOS.xlsx` -- 483 clientes com ABC por mes (MAR/25-FEV/26)
- `.planning/phases/02-faturamento/02-RESEARCH.md` -- Mapeamento completo de colunas, armadilhas, estrategia SAP-First
- `.planning/phases/02-faturamento/02-VERIFICATION.md` -- 537 CNPJs validados, stats consistentes
- `.planning/phases/02-faturamento/02-03-SUMMARY.md` -- CARTEIRA 0 data rows confirmado, DRAFT 1 -> CARTEIRA architecture

### Secondary (MEDIUM confidence)
- `scripts/v3_draft1.py` -- Template de construcao do DRAFT 1: ABC formula `=IF(AK4>=2000,"A",...)`, column map
- `scripts/v3_carteira.py` -- Template de construcao da CARTEIRA: 257 colunas, 4 mega-blocos, column grouping
- `data/docs/SPEC_FINAL_CRM_VITAO360_V3.md` -- ABC thresholds: A>=2k, B>=500, C<500
- `data/docs/MANUAL_AGENDA_COMERCIAL_VITAO_v3_FINAL.md` -- ABC criterios confirmados
- `data/docs/HANDOFF_CRM_V3.md` -- DRAFT 1 via INDEX/MATCH architecture documentada
- `data/docs/FASE_1_CARTEIRA.md` -- Blueprint v2 com 81 colunas e grupos expansiveis

### Tertiary (LOW confidence)
- `.planning/ROADMAP.md` -- Phase 3 description e requirements (pode nao refletir estado real pos-Phase 2)

## Metadata

**Confidence breakdown:**
- Data source (merged JSON): HIGH -- 537 CNPJs validados, stats consistentes, produzido e verificado na Phase 2
- DRAFT 1 -> CARTEIRA architecture: HIGH -- Confirmado por inspecao direta de formulas no V12 COM_DADOS
- ABC classification thresholds: HIGH -- Documentado em MANUAL, SPEC, e formula existente no DRAFT 1
- Column mapping DRAFT 1: HIGH -- Confirmado por inspecao direta (headers row 3)
- Column mapping CARTEIRA: HIGH -- Confirmado por inspecao direta (headers rows 2-3)
- Formula expansion pattern: MEDIUM -- Baseado nas formulas de row 7 (unica row completa). Precisa validar contra row 5 e template original.
- JAN/FEV handling: MEDIUM -- Confirmado que nao tem coluna, mas impacto no total precisa validacao.
- V13 status: HIGH -- Confirmado que V13 so tem PROJECAO, sem CARTEIRA.

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (dados estaticos -- fontes nao mudam)
