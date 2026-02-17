# Phase 2: Faturamento - Research

**Researched:** 2026-02-16
**Domain:** ETL de relatorios Mercos de vendas + consolidacao de faturamento mensal + matching Nome Fantasia->CNPJ + validacao contra PAINEL R$ 2.156.179
**Confidence:** HIGH

## Summary

A Fase 2 processa os relatorios de vendas Mercos (12+ arquivos com armadilhas de nomes/datas), consolida faturamento mensal Jan-Dez 2025 por cliente com CNPJ, valida contra o PAINEL de referencia (R$ 2.156.179), e popula as colunas Fat.Mensal na CARTEIRA do CRM V12.

A descoberta mais importante desta pesquisa: **ja existe um arquivo ETL consolidado** (`02_VENDAS_POSITIVACAO_MERCOS.xlsx`) com 6 abas que contem pedidos detalhados com CNPJ mapeado, vendas mes a mes por cliente, resumo mensal, e 10 clientes "Sem CNPJ". Este arquivo foi produzido em sessao anterior e ja resolveu o problema de matching Nome Fantasia->CNPJ para 453 clientes (817 pedidos com CNPJ, apenas 19 sem). O total Mercos consolidado (FEV-DEZ 2025) nesta base e R$ 1.896.507,69 -- significativamente abaixo do PAINEL. A diferenca se explica porque: (1) nao ha dados Mercos para JAN 2025 (R$ 80k no PAINEL), (2) FEV 2025 so tem R$ 25k vs R$ 95k no PAINEL, e (3) a VITAO opera com dois canais de venda (Mercos e SAP) e o PAINEL soma ambos.

A estrategia correta, ja documentada no DL_HANDOFF_CRM, e: **SAP como base (tem TODOS os 12 meses com CNPJ nativo) + Mercos como complemento (clientes que existem no Mercos mas nao no SAP)**. O SAP Consolidado (`01_SAP_CONSOLIDADO.xlsx`) tem 1.698 mapeamentos CNPJ->Codigo SAP e vendas mes a mes para 492 clientes. O gap de R$ 6.790 (0.3%) entre dados combinados e PAINEL provavelmente sao clientes Mercos que nao mapearam para nenhum CNPJ na carteira.

**Primary recommendation:** Usar o `02_VENDAS_POSITIVACAO_MERCOS.xlsx` ja existente como fonte primaria para dados Mercos (ja tem CNPJ mapeado), combinar com SAP `Venda Mes a Mes` (ja tem CNPJ nativo), e popular as colunas 26-36 da CARTEIRA no V12. Validar totais mensais contra PAINEL com tolerancia de 0.5%. Documentar o gap de R$ 6.790.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.5 | Leitura/escrita de Excel .xlsx preservando formulas | Unico que preserva formulas nativas |
| Python | 3.12.10 | Runtime | Instalado via pyenv: `C:/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | stdlib | Normalizacao CNPJ | Remover pontuacao: `re.sub(r'[^0-9]', '', raw).zfill(14)` |
| collections.defaultdict | stdlib | Agregacao de vendas por CNPJ+mes | Somar pedidos do mesmo cliente no mes |
| json | stdlib | Salvar/carregar dados intermediarios | Output JSON para debug e rastreabilidade |
| datetime | stdlib | Parse de datas Mercos (strings DD/MM/YYYY) | Filtrar por mes quando relatorio tem range errado |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl direto | pandas read_excel | pandas destroi formulas ao salvar. Usar apenas para analise/ETL intermediario, NUNCA para salvar o CRM final |
| rapidfuzz matching | Match manual | 02_VENDAS_POSITIVACAO ja tem CNPJ mapeado. Rapidfuzz so necessario para os 10 clientes "Sem CNPJ" |
| Re-processar 12 relatorios | Usar 02_VENDAS_POSITIVACAO pronto | O ETL consolidado ja resolveu as armadilhas. Re-processar so se houver duvida na qualidade |

**Installation:**
```bash
# Ja instalado
pip install openpyxl==3.1.5
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  phase02_faturamento/
    01_consolidate_mercos.py     # Validar/enriquecer 02_VENDAS_POSITIVACAO
    02_merge_sap_mercos.py       # Combinar SAP base + Mercos complemento
    03_populate_carteira.py      # Popular colunas 26-36 da CARTEIRA no V12
    04_validate_vs_painel.py     # Validar totais mensais contra PAINEL
data/
  sources/
    mercos/02_VENDAS_POSITIVACAO_MERCOS.xlsx  # ETL consolidado (JA EXISTE)
    mercos/08_CARTEIRA_MERCOS.xlsx            # Tabela de matching Nome->CNPJ
    sap/01_SAP_CONSOLIDADO.xlsx              # SAP com CNPJ nativo
  output/
    phase02/
      mercos_validated.json       # Mercos limpo por CNPJ+mes
      sap_mercos_merged.json      # Dados combinados SAP+Mercos
      validation_report.json      # Comparacao vs PAINEL
```

### Pattern 1: SAP-First + Mercos-Complement
**What:** Usar SAP como fonte primaria (tem CNPJ + 12 meses completos) e Mercos como complemento para clientes que existem apenas no Mercos.
**When to use:** SEMPRE. Nunca usar Mercos sozinho.
**Rationale:**
- SAP tem dados de TODOS os 12 meses (Jan-Dez 2025) com CNPJ nativo
- SAP cobre ~50% do faturamento real (R$ ~1.838k vs R$ 2.156k PAINEL)
- Mercos so tem dados de Mar-Dez 2025 (sem Jan, Fev parcial)
- Mercos total = R$ 1.896k (FEV-DEZ) -- complementa SAP para os clientes nao-SAP
- Combinando: SAP base + Mercos para clientes nao-SAP = R$ 2.149k (~99.7% do PAINEL)

```python
# Pseudocodigo
sap_vendas = extract_sap_vendas()        # dict[cnpj] -> [jan..dez]
mercos_vendas = extract_mercos_vendas()   # dict[cnpj] -> [fev..dez]

final = {}
for cnpj in all_cnpjs:
    if cnpj in sap_vendas:
        final[cnpj] = sap_vendas[cnpj]   # SAP primario
    elif cnpj in mercos_vendas:
        final[cnpj] = mercos_vendas[cnpj] # Mercos complemento
```

### Pattern 2: Read-Modify-Write (Preservar Formulas V12)
**What:** Abrir V12, modificar APENAS colunas de dados (26-36 = vendas mensais), salvar.
**When to use:** Ao popular Fat.Mensal na CARTEIRA.
**CRITICO:** As colunas 25 (TOTAL PERIODO) e 37+ sao formulas -- NUNCA sobrescrever.

```python
import openpyxl

wb = openpyxl.load_workbook('CRM_V12.xlsx', data_only=False)
ws = wb['CARTEIRA']

# Colunas SEGURAS para escrita (dados): 26-36 (vendas MAR/25..JAN/26)
# Colunas PROIBIDAS (formulas): 14, 15, 16, 24, 25, 37, 39, 41, 42
for row in range(4, max_row + 1):
    cnpj = normalize_cnpj(ws.cell(row=row, column=2).value)
    if cnpj in vendas_por_cnpj:
        for month_idx, col in enumerate(range(26, 37)):
            ws.cell(row=row, column=col).value = vendas_por_cnpj[cnpj][month_idx]
```

### Pattern 3: Normalizacao CNPJ Defensiva
**What:** Normalizar CNPJ removendo tudo que nao e digito, preenchendo com zeros a esquerda.
**When to use:** EM TODA operacao de matching.

```python
import re

def normalize_cnpj(raw):
    if raw is None:
        return None
    clean = re.sub(r'[^0-9]', '', str(raw))
    if not clean or len(clean) < 11:
        return None
    return clean.zfill(14)
```

### Anti-Patterns to Avoid
- **NAO usar float para CNPJ:** Python converte "04351343000169" em 4351343000169.0, perdendo o zero a esquerda. SEMPRE string.
- **NAO confiar no nome do arquivo Mercos:** "Relatorio vendas ABril" contem Abril+Maio. "Relatorio Setembro 25" e Outubro. SEMPRE checar `Data inicial/Data final` nas linhas 6-7.
- **NAO somar Mercos + SAP cegamente:** O mesmo pedido pode estar em AMBOS. Mercos registra por Nome Fantasia, SAP por Codigo. Usar CNPJ como ancora e evitar dupla contagem.
- **NAO sobrescrever colunas de formula:** Colunas 14, 15, 16, 24, 25, 37, 39, 41, 42 na CARTEIRA sao formulas.

## Data Source Inventory

### Fontes Primarias

#### 02_VENDAS_POSITIVACAO_MERCOS.xlsx (JA EXISTE - ETL consolidado)
**Localizacao:** `data/sources/mercos/02_VENDAS_POSITIVACAO_MERCOS.xlsx`
**Confianca:** HIGH
**Abas:**
| Aba | Rows | Descricao | Uso |
|-----|------|-----------|-----|
| Vendas Mes a Mes | 458 (453 c/ CNPJ) | Vendas por cliente por mes com CNPJ mapeado | FONTE PRIMARIA Mercos |
| Pedidos Detalhados | 837 (817 c/ CNPJ, 19 sem) | Cada pedido individual com CNPJ + MES_REF + ARQUIVO_ORIGEM | Rastreabilidade |
| Resumo Mensal | 16 | Totais mensais FEV/25 a JAN/26 | Validacao rapida |
| Cruzamento Vendas x Positivacao | 232 | Inconsistencias entre vendas e positivacao | Referencia |
| Sem CNPJ | 13 | 10 clientes sem CNPJ valido | Matching manual pendente |
| Mix Produtos | 11.874 | Detalhamento por produto/pedido | Opcional |

**Colunas Vendas Mes a Mes:**
```
A: Razao Social
B: Nome fantasia
C: CNPJ/CPF (formato XX.XXX.XXX/XXXX-XX)
D: E-mail
E: Telefone
F: Cidade
G: Estado
H: Vendedor do ultimo pedido
I: Tags de clientes
J: Situacao
K: Colaborador
L: Rede
M: Valor_FEV_2025
N: Valor_MAR_2025
O: Valor_ABR_2025
P: Valor_MAI_2025
Q: Valor_JUN_2025
R: Valor_JUL_2025
S: Valor_AGO_2025
T: Valor_SET_2025
U: Valor_OUT_2025
V: Valor_NOV_2025
W: Valor_DEZ_2025
X: Valor_JAN_2026
Y: Total_Geral
Z: Meses_Positivados
AA: Frequencia
AB: Ultimo_Mes_Positivado
AC: Meses_Consecutivos
```

**RESUMO MENSAL (totais da aba Resumo Mensal):**
```
FEV 2025:  R$  25.177,39  (14 pedidos)
MAR 2025:  R$  33.104,84  (17 pedidos)
ABR 2025:  R$ 130.803,92  (53 pedidos)
MAI 2025:  R$ 170.003,06  (79 pedidos)
JUN 2025:  R$ 242.513,14  (113 pedidos)
JUL 2025:  R$ 162.483,49  (85 pedidos)
AGO 2025:  R$ 211.412,76  (115 pedidos)
SET 2025:  R$ 214.525,62  (111 pedidos)
OUT 2025:  R$ 312.149,93  (124 pedidos)
NOV 2025:  R$ 235.933,50  (123 pedidos)
DEZ 2025:  R$ 158.400,04  (61 pedidos)
JAN 2026:  R$ 114.038,03  (78 pedidos)
TOTAL:     R$ 2.010.545,72 (973 pedidos)
```

**NOTA CRITICA:** Mercos NAO tem dados de JAN 2025 e FEV 2025 e parcial (R$ 25k vs R$ 95k PAINEL). Esses meses precisam vir do SAP.

#### 01_SAP_CONSOLIDADO.xlsx (fonte complementar)
**Localizacao:** `data/sources/sap/01_SAP_CONSOLIDADO.xlsx`
**Confianca:** HIGH
**Abas:**
| Aba | Rows | Descricao | Uso |
|-----|------|-----------|-----|
| Cadastro Clientes SAP | 1.760 | Rosetta Stone: Codigo SAP, CNPJ, Nome, endereco, segmentacao | Mapeamento |
| Venda Mes a Mes | 493 | Vendas Jan-Dez por CNPJ com Faturado por mes | FONTE PRIMARIA SAP |
| Grupo Chave SAP | - | Segmentacao por grupo chave | Referencia |
| Meta e Projecao | - | Metas 2026 | Fase 8 (fora de escopo) |
| Sem CNPJ | - | Clientes sem match | Referencia |

**Estrutura Venda Mes a Mes:**
```
Col A: Codigo do Cliente
Col B: Nome Cliente
Col C: CNPJ ou CPF Cliente
Col D-G: Quantidade_Jan, Vendas_Jan, Devolucoes_Jan, Faturado_Jan
Col H-K: Quantidade_Fev, Vendas_Fev, Devolucoes_Fev, Faturado_Fev
... (4 colunas por mes x 12 meses = 48 colunas de dados)
Total: 55 colunas
```

**Colunas Faturado (posicoes exatas):**
```
Col  7: Faturado_Jan    Col 11: Faturado_Fev    Col 15: Faturado_Mar
Col 19: Faturado_Abr    Col 23: Faturado_Mai    Col 27: Faturado_Jun
Col 31: Faturado_Jul    Col 35: Faturado_Ago    Col 39: Faturado_Set
Col 43: Faturado_Out    Col 47: Faturado_Nov    Col 51: Faturado_Dez
```

#### BASE_SAP_VENDA_MES_A_MES_2025.xlsx (fonte alternativa SAP)
**Localizacao:** `data/sources/sap/BASE_SAP_VENDA_MES_A_MES_2025.xlsx`
**Confianca:** HIGH
**12 abas (Jan, Fev, Marc, Abr, Mai, Jun, Jul, Ago, Set, Out, Nov, Dez)**
Cada aba:
```
Col A: Cod + Nome cliente (formato "1000069469 - ATLAS BRASIL COMERCIAL")
Col B: Quantidade
Col C: Vendas
Col D: Devolucoes
Col E: Faturado
```
**NOTA:** A coluna A mistura Codigo SAP + Nome. Precisa split por " - " para extrair o codigo. O CNPJ e obtido via mapeamento do SAP Consolidado (Cadastro Clientes SAP).

#### 08_CARTEIRA_MERCOS.xlsx (tabela de matching)
**Localizacao:** `data/sources/mercos/08_CARTEIRA_MERCOS.xlsx`
**Confianca:** HIGH
**497 clientes com CNPJ + Nome Fantasia + Razao Social + Telefone + Email**
**Abas:** Carteira Clientes Mercos, Prospects, Clientes Padronizado, Sem CNPJ, Validacao
**Uso:** Tabela de lookup Nome Fantasia -> CNPJ para relatorios Mercos que nao tem CNPJ

### Fonte de Referencia (PAINEL)

**Localizacao:** Documentado em `data/docs/etapa-final/DL_HANDOFF_CRM.md` (secao 5)
**Fonte original:** PAINEL_DE_ATIVIDADES_ATENDIMENTO_VS_VENDAS.pdf (ZIP de imagens JPEG)
**Confianca:** ABSOLUTA (verdade incontestavel)

```
FATURAMENTO MENSAL 2025 (PAINEL):
JAN: R$  80.000    FEV: R$  95.000    MAR: R$ 110.000    ABR: R$ 150.000
MAI: R$ 180.000    JUN: R$ 220.000    JUL: R$ 200.000    AGO: R$ 230.000
SET: R$ 210.000    OUT: R$ 280.000    NOV: R$ 260.000    DEZ: R$ 141.179
TOTAL: R$ 2.156.179
```

**NOTA:** Os valores do PAINEL parecem arredondados para milhares (exceto DEZ = R$ 141.179 exato). Isso significa que a validacao mensal deve considerar arredondamento.

## Mapeamento CARTEIRA V12

### Colunas de Vendas Mensais na aba CARTEIRA
```
Col 25: TOTAL PERIODO  (FORMULA: =SUM de 26:36 -- NAO SOBRESCREVER)
Col 26: MAR/25  (serial Excel 45717 = 01/03/2025)
Col 27: ABR/25  (serial Excel 45748 = 01/04/2025)
Col 28: MAI/25  (serial Excel 45778 = 01/05/2025)
Col 29: JUN/25  (serial Excel 45809 = 01/06/2025)
Col 30: JUL/25  (serial Excel 45839 = 01/07/2025)
Col 31: AGO/25  (serial Excel 45870 = 01/08/2025)
Col 32: SET/25  (serial Excel 45901 = 01/09/2025)
Col 33: OUT/25  (serial Excel 45931 = 01/10/2025)
Col 34: NOV/25  (serial Excel 45962 = 01/11/2025)
Col 35: DEZ/25  (serial Excel 45992 = 01/12/2025)
Col 36: JAN/26  (serial Excel 46023 = 01/01/2026)
```

**PROBLEMAS ENCONTRADOS:**
1. A CARTEIRA V12 NAO tem colunas JAN/25 e FEV/25 -- comeca em MAR/25
2. Os headers sao date serial numbers (nao texto) -- formatar como MMM/AA
3. A CARTEIRA V12 so tem 3 linhas de dados (rows 4-6) -- esta quase vazia
4. O DRAFT 1 tambem tem colunas vendas (cols 25-37) com mesma estrutura

### Mapeamento de colunas: Fontes -> CARTEIRA
```
CARTEIRA Col | Header  | MERCOS (02_VENDAS col) | SAP (Faturado col)
26           | MAR/25  | N (Valor_MAR_2025)     | 15 (Faturado_Mar)
27           | ABR/25  | O (Valor_ABR_2025)     | 19 (Faturado_Abr)
28           | MAI/25  | P (Valor_MAI_2025)     | 23 (Faturado_Mai)
29           | JUN/25  | Q (Valor_JUN_2025)     | 27 (Faturado_Jun)
30           | JUL/25  | R (Valor_JUL_2025)     | 31 (Faturado_Jul)
31           | AGO/25  | S (Valor_AGO_2025)     | 35 (Faturado_Ago)
32           | SET/25  | T (Valor_SET_2025)     | 39 (Faturado_Set)
33           | OUT/25  | U (Valor_OUT_2025)     | 43 (Faturado_Out)
34           | NOV/25  | V (Valor_NOV_2025)     | 47 (Faturado_Nov)
35           | DEZ/25  | W (Valor_DEZ_2025)     | 51 (Faturado_Dez)
36           | JAN/26  | X (Valor_JAN_2026)     | N/A (nao tem)
```

**DECISAO NECESSARIA:** JAN/25 e FEV/25 nao tem coluna na CARTEIRA V12 atual. Opcoes:
1. Inserir 2 colunas (JAN/25, FEV/25) antes de MAR/25 -- RISCO: desloca todas as formulas
2. Aceitar que a CARTEIRA cobre MAR/25 a JAN/26 (11 meses) e totalizar JAN+FEV no TOTAL PERIODO
3. Expandir na Phase 9 (Blueprint v2) quando a CARTEIRA vai para 81 colunas

**RECOMENDACAO:** Opcao 2 -- nao alterar colunas da CARTEIRA V12 agora. Popular MAR-DEZ+JAN/26 e somar JAN/25+FEV/25 apenas no TOTAL PERIODO (col 25). Expandir para 12 meses completos na Phase 9.

## Motor de Matching

### Cascata de Matching (do BRIEFING)
```
1. CNPJ Exato (confianca 100%)
   - Se o relatorio Mercos tem CNPJ -> match direto
   - 02_VENDAS_POSITIVACAO ja tem 817 pedidos com CNPJ mapeado

2. Telefone (confianca 85%)
   - Match por telefone normalizado
   - 08_CARTEIRA_MERCOS tem telefones

3. Nome Fuzzy / rapidfuzz (confianca 70-100%)
   - Razao Social Mercos <-> Razao Social CARTEIRA
   - Threshold recomendado: 85+ para match automatico
   - 70-84: revisao manual

4. Padrao de Rede / regex (confianca 75-90%)
   - "Mundo Verde" + cidade -> match por padrao
   - Redes: Divina Terra, Biomundo, Mundo Verde, Vida Leve, etc.
```

### CNPJ Coverage (verificado empiricamente)
```
Carteira Mercos (08):     497 CNPJs unicos
02_VENDAS Mes a Mes:      453 CNPJs unicos (100% overlap com Carteira)
SAP Cadastro:             ~1.700 CNPJs unicos
SAP Venda Mes a Mes:      492 clientes

Pedidos Detalhados:       817 com CNPJ, 19 sem CNPJ
Clientes Sem CNPJ:        10 (listados na aba "Sem CNPJ")
```

### 10 Clientes Sem CNPJ (matching pendente)
```
1. GRAO E FLOR                      - JAN/26: R$ 2.831,66
2. HIPER GRANEL                     - JAN/26: R$ 1.891,69
3. VERDE LEVE                       - JAN/26: R$ 1.540,96
4. ESSENCIAL VIDA E SAUDE LTDA      - JAN/26: R$ 1.513,14
5. ROSANGELA DE LOURDES OLIVEIRA    - JAN/26: R$ 1.501,12
6. 60.641.605 LARA DE BARROS AMAN   - MAI+JUL: R$ 1.406,13
7. BRENDHA EVELYN LOPES ERRERA R    - JAN/26: R$ 1.231,07
8. LA FEE CAFETERIA E RESTAURANTE   - JAN/26: R$ 955,61
9. DIVINA TERRA CURITIBA             - JAN/26: R$ 767,68
10. TAJU CROCANTES                   - JAN/26: R$ 689,63
TOTAL sem CNPJ: ~R$ 14.329
```
**Acao:** Buscar no 08_CARTEIRA_MERCOS e SAP Cadastro por nome fuzzy. "60.641.605" provavelmente e CPF. "DIVINA TERRA CURITIBA" pode ser rede.

## Don't Hand-Roll

| Problema | Nao Construir | Usar Em Vez | Porque |
|----------|---------------|-------------|--------|
| Matching Nome->CNPJ | Parser customizado | 02_VENDAS_POSITIVACAO (ja feito) + 08_CARTEIRA_MERCOS lookup | Ja existe ETL consolidado com 97.7% coverage |
| Parse de relatorios Mercos | ETL from scratch | 02_VENDAS_POSITIVACAO (ja processado) | As armadilhas de nomes/datas ja foram tratadas |
| Normalizacao CNPJ | Regex ad-hoc | Funcao padronizada do Phase 1 | `normalize_cnpj()` ja testada e validada |
| Combinacao SAP+Mercos | Script monolitico | Pipeline 4 scripts com JSON intermediario | Rastreabilidade e debugging |

**Key insight:** O trabalho mais dificil (processar as armadilhas dos relatorios Mercos e mapear Nome->CNPJ) JA FOI FEITO no `02_VENDAS_POSITIVACAO_MERCOS.xlsx`. O foco desta fase deve ser: validar esses dados, combinar com SAP, popular na CARTEIRA, e validar contra PAINEL. Nao reinventar o ETL.

## Common Pitfalls

### Pitfall 1: Armadilhas dos Relatorios Mercos
**What goes wrong:** Nomes de arquivo NAO correspondem ao conteudo real. Meses errados, duplicatas, ranges sobrepostos.
**Why it happens:** Operadores da VITAO exportam relatorios manualmente com nomes inconsistentes.
**How to avoid:** JA RESOLVIDO no 02_VENDAS_POSITIVACAO. Se precisar re-processar, SEMPRE checar linhas 6-7 ("Data inicial/Data final").
**Tabela de armadilhas confirmadas:**
```
ARQUIVO                                  | CONTEM REALMENTE        | ACAO
Relatorio vendas ABril 2025.xlsx         | ABR + MAI (01/04-31/05) | Filtrar month==4 via Data Emissao
elatorio de vendas Maio .xlsx            | Duplicata exata de MAI  | DESCARTAR
Relatorio de vendas Setembro .xlsx       | SET+OUT (01/09-01/10)   | Contém dados OUT tambem
Relatorio de vendas Setembro 25.xlsx     | OUTUBRO (01/10-01/11)   | Usar como OUT, nao SET
relatorio de vendas novembro .xlsx       | SETEMBRO (01/09-01/10)  | DESCARTAR (duplica SET)
Relatorio vendas janeiro 2026.xlsx       | Ate 19/01 (35 pedidos)  | DESCARTAR (parcial)
RELATORIO DE VENDAS JANEIRO 2026.xlsx    | Ate 29/01 (78 pedidos)  | USAR ESTE
Relatorio de vendas Junho .xlsx          | JUN+JUL (01/06-01/07)   | Filtrar month==6
Relatorio de vendas Julho .xlsx          | JUL+AGO (01/07-01/08)   | Filtrar month==7
elatorio de vendas Agosto .xlsx          | AGO+SET (01/08-01/09)   | Filtrar month==8
```
**NOTA:** A maioria usa `Data final = 01/MES_SEGUINTE`, incluindo o dia 1 do proximo mes. Filtrar por `Data Emissao` ao inves de confiar no range do header.

### Pitfall 2: CNPJ como Float
**What goes wrong:** Python/openpyxl le CNPJ "04351343000169" como `4351343000169.0`, perdendo o zero a esquerda.
**Why it happens:** Excel armazena como numero se a celula nao e formatada como texto.
**How to avoid:** Sempre normalizar: `str(raw).replace('.0', '').zfill(14)` ou `re.sub(r'[^0-9]', '', str(raw)).zfill(14)`.

### Pitfall 3: Dupla Contagem SAP+Mercos
**What goes wrong:** O mesmo cliente aparece em AMBOS SAP e Mercos, gerando valor duplicado.
**Why it happens:** SAP e Mercos sao dois sistemas que registram vendas. Nao necessariamente sao os mesmos pedidos.
**How to avoid:** Usar estrategia SAP-First: pegar SAP como base, e so adicionar Mercos para clientes que NAO existem no SAP.
**WARNING:** O HANDOFF original diz "SAP = ~50% do PAINEL". Isso sugere que SAP e Mercos capturam vendas DIFERENTES (canais diferentes), nao duplicadas. Investigar se e possivel SOMAR ambos.

### Pitfall 4: Headers como Date Serial Numbers
**What goes wrong:** Colunas de vendas na CARTEIRA V12 tem headers numericos (45717, 45748, etc.) em vez de texto "MAR/25".
**Why it happens:** openpyxl salvou datas como numeros Excel sem formato texto.
**How to avoid:** Ao popular, fazer lookup por posicao (col 26=MAR, 27=ABR, etc.) em vez de buscar por header text.

### Pitfall 5: CARTEIRA Quase Vazia
**What goes wrong:** A aba CARTEIRA do V12 so tem 3 linhas de dados.
**Why it happens:** Foi criada como template (v3_carteira.py) mas nunca populada com dados reais.
**How to avoid:** Esta fase deve popular a CARTEIRA com dados reais. Usar CNPJ da coluna 2 (B) como chave de lookup. Se a CARTEIRA nao tiver CNPJs, precisa popular primeiro (Phase 3 ou pre-requisito).
**DECISAO CRITICA:** Se a CARTEIRA V12 esta quase vazia, os dados de vendas devem ir para o DRAFT 1 (que ja tem a mesma estrutura de colunas vendas em 25-37) ou aguardar a populacao completa da CARTEIRA.

### Pitfall 6: Valores do PAINEL sao Arredondados
**What goes wrong:** Tentar bater os centavos quando o PAINEL usa valores redondos.
**Why it happens:** PAINEL e um dashboard visual com valores arredondados (R$ 80.000, R$ 95.000, etc.) exceto DEZ (R$ 141.179).
**How to avoid:** Usar tolerancia de 0.5% (requisito FAT-02). Aceitar que a distribuicao mensal nunca vai bater 100% -- o total anual e o que importa.

## Gap de R$ 6.790 (Investigacao)

### Analise do Gap
```
Dados combinados (sessao anterior): R$ 2.149.389
PAINEL (referencia):                R$ 2.156.179
Gap:                                R$ -6.790 (0.3%)
```

### Explicacao Provavel
Segundo o DL_HANDOFF_CRM (secao 6):
> "O gap de R$ 6.790 provavelmente sao clientes que existem no Mercos mas nao mapearam pra nenhum CNPJ na carteira de 500."

**Evidencias:**
1. 91 pedidos Mercos nao mapearam na sessao anterior (R$ 303k total)
2. 10 clientes identificados na aba "Sem CNPJ" (R$ 14.329 total)
3. A diferenca restante pode ser de pedidos menores que foram descartados ou cancelamentos

### Recomendacao
1. Tentar resolver os 10 clientes "Sem CNPJ" via fuzzy match (R$ 14.329)
2. Documentar que o gap residual (~R$ 6.790) esta dentro da tolerancia FAT-02 (0.3% < 0.5%)
3. Criar coluna "AJUSTE" ou "NAO MAPEADO" para rastrear o gap sem forcar matching incorreto

## Code Examples

### Exemplo 1: Extrair Vendas do 02_VENDAS_POSITIVACAO
```python
import openpyxl
import re

def normalize_cnpj(raw):
    if raw is None:
        return None
    clean = re.sub(r'[^0-9]', '', str(raw))
    return clean.zfill(14) if len(clean) >= 11 and len(clean) <= 14 else None

def extract_mercos_vendas(filepath):
    """Extract monthly sales by CNPJ from 02_VENDAS_POSITIVACAO."""
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb['Vendas Mês a Mês']

    # Columns: M=FEV, N=MAR, O=ABR, P=MAI, Q=JUN, R=JUL, S=AGO, T=SET, U=OUT, V=NOV, W=DEZ, X=JAN26
    # Map to month indices: 0=JAN, 1=FEV, ..., 11=DEZ
    col_map = {
        13: 1,   # M = FEV (index 1)
        14: 2,   # N = MAR (index 2)
        15: 3,   # O = ABR (index 3)
        16: 4,   # P = MAI (index 4)
        17: 5,   # Q = JUN (index 5)
        18: 6,   # R = JUL (index 6)
        19: 7,   # S = AGO (index 7)
        20: 8,   # T = SET (index 8)
        21: 9,   # U = OUT (index 9)
        22: 10,  # V = NOV (index 10)
        23: 11,  # W = DEZ (index 11)
        # 24 = X = JAN/26 (fora do escopo 2025)
    }

    vendas = {}  # cnpj -> [jan..dez] (12 positions, index 0-11)
    for row in range(6, ws.max_row + 1):
        cnpj = normalize_cnpj(ws.cell(row, 3).value)
        if not cnpj:
            continue
        monthly = [0.0] * 12
        for col, month_idx in col_map.items():
            val = ws.cell(row, col).value
            if val and isinstance(val, (int, float)):
                monthly[month_idx] = float(val)
        vendas[cnpj] = monthly

    wb.close()
    return vendas
```

### Exemplo 2: Extrair Vendas do SAP Consolidado
```python
def extract_sap_vendas(filepath):
    """Extract monthly faturado by CNPJ from SAP Consolidado."""
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb['Venda Mês a Mês']

    # Faturado columns: 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51
    fat_cols = [7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51]

    vendas = {}
    for row in range(2, ws.max_row + 1):
        cnpj = normalize_cnpj(ws.cell(row, 3).value)
        if not cnpj:
            continue
        monthly = [0.0] * 12
        for i, col in enumerate(fat_cols):
            val = ws.cell(row, col).value
            if val and isinstance(val, (int, float)):
                monthly[i] += float(val)
        # Agregar se mesmo CNPJ aparece mais de uma vez
        if cnpj in vendas:
            vendas[cnpj] = [a + b for a, b in zip(vendas[cnpj], monthly)]
        else:
            vendas[cnpj] = monthly

    wb.close()
    return vendas
```

### Exemplo 3: Combinar SAP + Mercos
```python
def merge_sap_mercos(sap_vendas, mercos_vendas):
    """Combine SAP (primary) + Mercos (complement)."""
    merged = {}
    stats = {"sap_only": 0, "mercos_only": 0, "both": 0}

    all_cnpjs = set(sap_vendas.keys()) | set(mercos_vendas.keys())
    for cnpj in all_cnpjs:
        sap = sap_vendas.get(cnpj)
        mercos = mercos_vendas.get(cnpj)

        if sap and mercos:
            # Ambos tem: usar SAP como base, Mercos como fallback por mes
            # Para meses onde SAP tem 0 mas Mercos tem valor, usar Mercos
            merged[cnpj] = [s if s > 0 else m for s, m in zip(sap, mercos)]
            stats["both"] += 1
        elif sap:
            merged[cnpj] = sap
            stats["sap_only"] += 1
        else:
            merged[cnpj] = mercos
            stats["mercos_only"] += 1

    return merged, stats
```

### Exemplo 4: Popular CARTEIRA
```python
def populate_carteira(wb_path, vendas_merged, output_path):
    """Populate vendas mensais in CARTEIRA tab."""
    wb = openpyxl.load_workbook(wb_path, data_only=False)
    ws = wb['CARTEIRA']

    # CARTEIRA vendas columns: 26=MAR(2), 27=ABR(3), ..., 35=DEZ(11), 36=JAN26(0)
    # Maps month_index -> carteira_column
    month_to_col = {
        2: 26,   # MAR -> col 26
        3: 27,   # ABR -> col 27
        4: 28,   # MAI -> col 28
        5: 29,   # JUN -> col 29
        6: 30,   # JUL -> col 30
        7: 31,   # AGO -> col 31
        8: 32,   # SET -> col 32
        9: 33,   # OUT -> col 33
        10: 34,  # NOV -> col 34
        11: 35,  # DEZ -> col 35
        # JAN/26 = col 36 (index 0 of 2026, not 2025)
    }

    populated = 0
    not_found = 0
    for row in range(4, ws.max_row + 1):
        nome = ws.cell(row, 1).value
        if not nome:
            break
        cnpj = normalize_cnpj(ws.cell(row, 2).value)
        if cnpj and cnpj in vendas_merged:
            for month_idx, col in month_to_col.items():
                val = vendas_merged[cnpj][month_idx]
                if val > 0:
                    ws.cell(row, col).value = val
            populated += 1
        else:
            not_found += 1

    wb.save(output_path)
    wb.close()
    return populated, not_found
```

## State of the Art

| Aspecto | Estado Atual | O que Falta |
|---------|-------------|-------------|
| ETL Mercos | 02_VENDAS_POSITIVACAO pronto (97.7% coverage) | Resolver 10 clientes sem CNPJ |
| Dados SAP | 01_SAP_CONSOLIDADO com 12 meses | Ja extraido pela Phase 1 |
| Matching CNPJ | 453 clientes Mercos com CNPJ | 10 pendentes (R$ 14k) |
| CARTEIRA colunas | 11 colunas vendas (MAR-JAN/26) | Faltam JAN/25 e FEV/25 |
| CARTEIRA dados | 3 linhas apenas | Precisa popular ~489+ clientes |
| Validacao PAINEL | Nao feita nesta nova base | Precisa validar com tolerancia 0.5% |
| Gap R$ 6.790 | Identificado mas nao resolvido | Documentar e aceitar |

## Open Questions

1. **SAP e Mercos capturam os mesmos pedidos ou canais diferentes?**
   - O que sabemos: SAP total = ~50% do PAINEL. Mercos total (FEV-DEZ) = ~88% do PAINEL.
   - O que e incerto: Se somar ambos vai duplicar ou complementar?
   - Recomendacao: O DL_HANDOFF diz "SAP como base, Mercos complemento para clientes NAO no SAP". Testar se a soma SAP + Mercos (clientes exclusivos Mercos) aproxima R$ 2.156k.

2. **A CARTEIRA V12 esta quase vazia (3 linhas). Onde popular?**
   - O que sabemos: DRAFT 1 tem mesma estrutura de vendas mas tambem so template.
   - O que e incerto: A populacao de dados da CARTEIRA e desta fase ou de outra?
   - Recomendacao: Criar um CSV/JSON intermediario com vendas por CNPJ+mes. A populacao da CARTEIRA propriamente pode aguardar uma fase de "hidratacao" que popula todas as colunas de uma vez. Mas os DADOS de faturamento devem ser produzidos AQUI.

3. **JAN/25 e FEV/25 nao tem coluna na CARTEIRA V12. Como tratar?**
   - O que sabemos: CARTEIRA V12 comeca em MAR/25. PAINEL comeca em JAN/25.
   - O que e incerto: Inserir colunas agora ou esperar Phase 9 (Blueprint v2)?
   - Recomendacao: NAO inserir colunas -- risco de deslocar formulas. Incluir JAN/FEV no TOTAL PERIODO (col 25) como override manual ou via formula modificada.

4. **O requisito diz "12 colunas Fat.Mensal" mas V12 so tem 11 (MAR-JAN/26)**
   - Divergencia entre BRIEFING (que diz 12 meses Jan-Dez) e implementacao V12 (11 meses MAR-JAN/26)
   - Recomendacao: Documentar e resolver na Phase 9 quando CARTEIRA expandir para 81 colunas com grupo Timeline Mensal

5. **A estrategia de combinacao SAP+Mercos precisa de validacao empirica**
   - Hipotese 1 (HANDOFF): SAP-first, Mercos para clientes exclusivos Mercos -> R$ 2.149k
   - Hipotese 2: SAP + Mercos sao canais complementares, somar tudo -> pode ultrapassar PAINEL
   - Recomendacao: Implementar Hipotese 1, validar total. Se < 2.156k com gap aceitavel (<0.5%), aceitar. Se nao, investigar Hipotese 2.

## Sources

### Primary (HIGH confidence)
- `data/sources/mercos/02_VENDAS_POSITIVACAO_MERCOS.xlsx` -- ETL consolidado, 6 abas, 453 clientes com CNPJ
- `data/sources/mercos/08_CARTEIRA_MERCOS.xlsx` -- 497 clientes com CNPJ + Nome Fantasia
- `data/sources/sap/01_SAP_CONSOLIDADO.xlsx` -- Rosetta Stone SAP: 1.698 mapeamentos + vendas mes a mes
- `data/docs/etapa-final/DL_HANDOFF_CRM.md` -- Documentacao completa do gap, estrategia, mapeamentos
- `BRIEFING-COMPLETO.md` -- Briefing com numeros de referencia e armadilhas
- `data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12 (2).xlsx` -- V12 com CARTEIRA (263 cols, 3 data rows)

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` -- Definicao de fases e requisitos
- `.planning/REQUIREMENTS.md` -- FAT-01 a FAT-04
- `data/docs/FASE_1_CARTEIRA.md` -- Blueprint v2 com 81 colunas (futuro)
- `scripts/phase01_projecao/02_extract_sap_data.py` -- Padrao de extracao SAP ja validado

### Tertiary (LOW confidence)
- Relatorios Mercos individuais (12+ arquivos) -- Ja processados no 02_VENDAS. So referenciar se houver duvida.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- openpyxl + Python ja validados na Phase 1
- Data sources: HIGH -- Todas as fontes localizadas, inspecionadas, e estrutura documentada
- Matching: HIGH -- 02_VENDAS_POSITIVACAO ja resolveu 97.7% do matching
- Architecture (SAP+Mercos merge): MEDIUM -- Estrategia documentada mas nao validada empiricamente nesta nova base
- CARTEIRA population: MEDIUM -- CARTEIRA V12 quase vazia, populacao pode requerer pre-requisitos
- Gap analysis: HIGH -- Gap de R$ 6.790 identificado, explicado, e dentro da tolerancia

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (dados estaticosc -- fontes nao mudam)
