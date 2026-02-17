# Phase 8: Comite e Metas - Research

**Researched:** 2026-02-17
**Domain:** CRM spreadsheet -- meta integration per client/consultor + COMITE gerencial tab com visao consolidada
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Metas SAP na CARTEIRA (META-01)
- SAP ja fornece meta por consultor (nao precisa estimar)
- Coluna META ANUAL + coluna META MES na CARTEIRA por cliente
- Rateio da meta do consultor para clientes: **proporcional ao historico de vendas 2025**
- Duas versoes selecionaveis: proporcional ao historico E distribuicao igual -- gestor escolhe qual visao usar
- Na CARTEIRA: meta puxa da PROJECAO e do SINALEIRO, realizado puxa das vendas realizadas
- **Rateio dinamico mes a mes:** se venda realizada < projetada -> gap redistribui proporcionalmente para os demais clientes do mes seguinte. Se venda > projetada -> reduz meta dos outros
- Fonte: BASE_SAP_META_PROJECAO_2026.xlsx (ja em data/sources/sap/)
- Valores de referencia: Meta total R$ 4.747.200 (SAP real, nao R$ 5.7M aspiracional)

#### Layout da aba COMITE (META-02)
- **1 aba** com blocos separados por linhas em branco (nao multiplas abas)
- **Tabela completa direto** -- sem KPI cards (estilo FORMATO_APROVADO, Excel-like)
- Modelo completo (tudo): Meta, Realizado, %, GAP R$, Semaforo, Contatos/dia, Vendas/dia, Conversao, Capacidade %, Clientes ativos, Suporte, Follow-ups, Prospeccoes, Risco, Agenda oc./livre
- Adaptar ao maximo as 8 visoes do modelo HTML V12_COMPLETO em blocos dentro da aba COMITE
- Blocos esperados (adaptados ao que os dados do V13 suportam):
  1. **Meta vs Realizado por consultor** -- tabela principal
  2. **Capacidade/Produtividade** -- carga/dia, vendas/dia, conversao, suporte
  3. **Alertas visuais** -- riscos (ex: licenca MANU), sobrecarga, gaps
  4. **Funil consolidado** -- tipo de contato x resultado (estilo FORMATO_APROVADO)
  5. **Motivos de nao compra** -- top motivos com % e dono da acao

#### Validacao de Capacidade (META-03)
- Limite padrao: **50 atendimentos/dia** por consultor (pode chegar a 60 -- muitos sao rapidos)
- 22 dias uteis fixo por mes (sem calculo de feriados)
- **Semaforo + barra de progresso** para cada consultor:
  - Verde: < 35/dia
  - Amarelo: 35-50/dia
  - Vermelho: > 50/dia
- Se consultor com agenda lotada: o CRM nao redistribui automaticamente -- mas os dados alimentam o motor de ranking da agenda diaria (Fase 9)

#### Sinaleiros e Formatacao
- Semaforo + percentual colorido na mesma linha para GAP (meta - realizado)
  - Verde: atingiu/superou (>= 100%)
  - Amarelo: 70-99% da meta
  - Vermelho: < 70% da meta
- Barras horizontais para comparar volume por consultor (estilo dos modelos HTML)
- Header com filtro VENDEDOR + PERIODO (estilo FORMATO_APROVADO)

### Claude's Discretion
- Quantos blocos exatos cabem na aba sem ficar poluida
- Quais visoes dos 8 tabs do HTML sao viaveis com formulas Excel (vs precisando de macro/VBA)
- Ordem dos blocos na aba COMITE
- Largura das colunas e formatacao condicional especifica
- Como implementar as "duas versoes selecionaveis" de rateio (pode ser toggle via celula filtro ou secoes paralelas)

### Deferred Ideas (OUT OF SCOPE)
- Motor de ranking completo da agenda diaria inteligente (10+ regras de priorizacao) -> Fase 9
- Implementacao da agenda com 50-60 atendimentos/dia priorizados automaticamente -> Fase 9
- CARTEIRA expandida para 81 colunas incluindo todos os inputs do ranking -> Fase 9
- Tendencias mensais, Eficiencia comercial (CAC/ROI), Cadencia T1-T4 -> backlog
- Receptivo por tipo de demanda, Motivos evolucao mensal com dono -> backlog

</user_constraints>

## Summary

A pesquisa revelou uma descoberta critica: **a aba PROJECAO do V13 JA CONTEM toda a infraestrutura de metas por cliente**. Colunas L:X (META ANUAL + META JAN-DEZ), Z:AL (REALIZADO ANUAL + REAL JAN-DEZ), AN:AQ (indicadores: % YTD, SINAL META, GAP, RANKING), BB:BN (META IGUALITARIA distribuicao igual), e BP:CB (META COMPENSADA DINAMICA com formulas SUMPRODUCT que redistribuem gaps). Total: 534 clientes, R$ 4.779.003 distribuidos (vs R$ 4.747.200 SAP -- 0.67% de diferenca por arredondamento do rateio proporcional).

Portanto, o **Plan 08-01** (importar metas) NEM PRECISA criar colunas novas na PROJECAO -- as metas ja estao la desde Phase 1. O trabalho real e: (a) verificar/corrigir a diferenca de R$ 31.803, (b) garantir que os dados REALIZADO (colunas AA-AL) estao populados para os meses recentes (atualmente so OUT/NOV/DEZ 2025 tem dados), e (c) criar a aba COMITE nova.

A aba COMITE sera construida com ~5 blocos de formulas SUMIFS/COUNTIFS referenciando PROJECAO e LOG, usando o padrao ja estabelecido nas abas DASH e REDES_FRANQUIAS_v2. Layout sera estilo FORMATO_APROVADO: Calibri 11px, header escuro (#404040), bordas finas, tabelas densas separadas por spacers.

**Recomendacao principal:** Dividir em 2 plans: Plan 08-01 = validar/ajustar metas existentes na PROJECAO + popular REALIZADO faltante; Plan 08-02 = construir aba COMITE completa com 5 blocos + formatacao condicional.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.5 | Leitura/escrita XLSX com formulas | Ja usado em todas as 7 fases anteriores |
| Python | 3.12.10 | Runtime via pyenv | Padrao do projeto |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openpyxl.formatting.rule | 3.1.5 | Conditional formatting (DataBarRule, CellIsRule, FormulaRule, IconSetRule) | Semaforos, barras, cores |
| openpyxl.worksheet.datavalidation | 3.1.5 | Dropdown para filtro VENDEDOR/PERIODO | Header da aba COMITE |
| collections (stdlib) | - | defaultdict/Counter para agregacoes | Contagem por consultor |
| v3_styles.py | local | Constantes de estilo compartilhadas (fonts, fills, borders, helpers) | Manter consistencia visual |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl formulas | VBA macros | Formulas sao suficientes para tudo planejado; VBA complica distribuicao |
| DataBarRule nativo | Colunas com barra manual via texto | DataBarRule e nativo do Excel e funciona via openpyxl |
| IconSetRule | Emoji semaforo em formula | Emoji ja usado na PROJECAO (col AO), mas IconSetRule e mais profissional |

**Installation:**
```bash
# Nenhuma instalacao necessaria -- tudo ja esta no ambiente
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  phase08_comite_metas/
    01_validate_adjust_metas.py     # Validar metas existentes, corrigir rateio, popular REALIZADO
    02_build_comite_tab.py          # Construir aba COMITE com 5 blocos
    03_validate_phase08.py          # Validacao final cruzada
```

### Pattern 1: Formula-Based Cross-Sheet References (Estabelecido)
**What:** Todas as metricas na aba COMITE serao formulas dinamicas referenciando PROJECAO e LOG
**When to use:** Sempre que o dado existe em outra aba
**Example:**
```python
# Padrao estabelecido em Phase 5 (DASH) e Phase 7 (REDES)
prj_ref = "'PROJECAO '!"  # Note: trailing space no nome da aba

# SUMIFS para agregar por consultor
f_meta = f'=SUMIFS({prj_ref}L$4:L$537,{prj_ref}D$4:D$537,"CONSULTOR_NAME")'
f_real = f'=SUMIFS({prj_ref}Z$4:Z$537,{prj_ref}D$4:D$537,"CONSULTOR_NAME")'
f_gap  = f'=SUMIFS({prj_ref}AP$4:AP$537,{prj_ref}D$4:D$537,"CONSULTOR_NAME")'

# COUNTIFS para contagem de contatos (referencia LOG)
date_filter = 'LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2'
f_contatos = f'=COUNTIFS({date_filter},LOG!$B$3:$B$21000,"CONSULTOR_NAME")'
```

### Pattern 2: Block-Based Tab Layout (Estabelecido na DASH)
**What:** Blocos separados por linhas em branco (spacers), cada bloco com titulo estilizado + headers + dados + total
**When to use:** Para a aba COMITE (e DASH)
**Example:**
```python
# Padrao de Phase 5 (DASH): section_title() + headers + data + total_row()
def section_title(ws, row, label, end_col=17):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=end_col)
    cell = ws.cell(row=row, column=1, value=f"  {label}")
    style_cell(cell, font=FONT_TITLE, fill=FILL_GRAY_D9, align=ALIGN_LEFT)

# Spacer entre blocos: 3 linhas em branco
SPACER_ROWS = 3
```

### Pattern 3: Filter Header (Estabelecido na DASH)
**What:** Row 2 com VENDEDOR dropdown + PERIODO date range que controlam todas as formulas
**When to use:** Topo da aba COMITE
**Example:**
```python
# DASH row 2: C2=VENDEDOR, E2=date_start, F2=date_end
# Formulas usam IF(OR($C$2="",$C$2="TODOS"), formula_all, formula_filtered)
# DataValidation dropdown para VENDEDOR
dv = DataValidation(type="list", formula1='"TODOS,MANU DITZEL,LARISSA PADILHA,JULIO GADRET,DAIANE STAVICKI"')
ws.add_data_validation(dv)
dv.add(ws['C2'])
```

### Pattern 4: Conditional Formatting for Semaforos and Bars
**What:** openpyxl suporta DataBarRule, CellIsRule, FormulaRule, IconSetRule nativamente
**When to use:** Semaforos de meta, barras de volume, cores de alerta
**Example:**
```python
from openpyxl.formatting.rule import DataBarRule, CellIsRule, FormulaRule

# Barra horizontal para volume
bar_rule = DataBarRule(start_type='min', end_type='max', color='638EC6', showValue=True)
ws.conditional_formatting.add('D5:D11', bar_rule)

# Semaforo de meta via FormulaRule (3 regras empilhadas)
red_fill = PatternFill(bgColor='FFCCCC')
yellow_fill = PatternFill(bgColor='FFFFCC')
green_fill = PatternFill(bgColor='CCFFCC')

# Verde: >= 100% (regra 1, prioridade mais alta)
ws.conditional_formatting.add('F5:F11',
    FormulaRule(formula=['F5>=1'], fill=green_fill))
# Amarelo: 70-99%
ws.conditional_formatting.add('F5:F11',
    FormulaRule(formula=['AND(F5>=0.7,F5<1)'], fill=yellow_fill))
# Vermelho: < 70%
ws.conditional_formatting.add('F5:F11',
    FormulaRule(formula=['F5<0.7'], fill=red_fill))
```

### Anti-Patterns to Avoid
- **NAO usar pandas para ler V13:** pandas nao preserva formulas; openpyxl com data_only=False e obrigatorio
- **NAO criar nova aba "CARTEIRA":** A PROJECAO JA E a carteira com metas. Nao duplicar dados.
- **NAO hardcodar nomes de consultor em formulas:** Usar celula de referencia ou lista para flexibilidade
- **NAO ignorar a variacao de R$ 31.803:** Investigar e corrigir (provavelmente arredondamento do rateio)
- **NAO reprocessar o V13 inteiro:** Apenas adicionar a aba COMITE; preservar as 19.224+ formulas existentes
- **NAO misturar formulas em INGLES e PORTUGUES:** openpyxl grava em INGLES (SUMIFS, COUNTIFS, IF) -- Excel traduz

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Semaforo visual | Formula IF com emoji | openpyxl FormulaRule/CellIsRule conditional formatting | Emoji funciona mas IconSet/fills sao mais profissionais |
| Barras horizontais | Coluna de texto com pipe chars | DataBarRule nativo do openpyxl | Renderiza como barra real no Excel |
| Dropdown de filtro | Validacao manual | DataValidation (ja usado na DASH) | Padrao estabelecido |
| Cross-sheet sum | Python calcula e grava valor | Formula SUMIFS/COUNTIFS | Dados atualizam dinamicamente |
| Estilo visual | CSS/HTML inline | v3_styles.py constantes compartilhadas | Consistencia entre abas |

**Key insight:** Toda a infraestrutura de metas ja existe na PROJECAO. O trabalho da Phase 8 e AGREGAR esses dados por consultor na aba COMITE, nao recalcular.

## Common Pitfalls

### Pitfall 1: Destruir formulas da PROJECAO ao salvar
**What goes wrong:** openpyxl pode perder formulas se carregar com data_only=True ou se XML complexo for corrompido
**Why it happens:** V13 tem 19.224+ formulas incluindo SUMPRODUCT complexos e merged cells
**How to avoid:** Sempre usar data_only=False; validar contagem de formulas antes e depois do save; manter BACKUP
**Warning signs:** Contagem de formulas < 19.224 apos reload

### Pitfall 2: Nome da aba PROJECAO com acento e espaco
**What goes wrong:** O nome real da aba e 'PROJECAO ' (com cedilha e espaco trailing)
**Why it happens:** Nome original preservado desde V11
**How to avoid:** Usar find_projecao_sheet() helper (ja existe em phase07); em formulas usar f"'PROJECAO '!" com aspas
**Warning signs:** #REF! errors nas formulas cross-sheet

### Pitfall 3: Consultores com nomes inconsistentes
**What goes wrong:** Dados mostram "HEMANUELE DITZEL (MANU)" vs "MANU DITZEL" (10 clientes com nome antigo)
**Why it happens:** Mudanca de nomenclatura entre fases
**How to avoid:** Normalizar para lista canonica: ["HEMANUELE DITZEL (MANU)", "LARISSA PADILHA", "JULIO GADRET", "DAIANE STAVICKI"]; incluir "MANU DITZEL" como alias nas formulas
**Warning signs:** Soma dos consultores < total geral (clientes orfaos)

### Pitfall 4: Colunas REALIZADO quase vazias
**What goes wrong:** As colunas AA-AL (REAL JAN-DEZ) so tem dados para OUT/NOV/DEZ 2025 -- o restante esta zerado
**Why it happens:** Phase 2 (faturamento) so integrou dados que existiam na epoca
**How to avoid:** Para a COMITE, agregar o que existe; documentar que REAL JAN/FEV/MAR 2026 sao zero ate dados serem alimentados; usar a coluna Z (REAL ANUAL = soma dos meses) que reflete o total disponivel
**Warning signs:** % atingimento absurdamente baixo porque realizado so tem 3 meses de dados vs 12 meses de meta

### Pitfall 5: Toggle de versao de rateio complexo em formulas Excel
**What goes wrong:** O usuario quer 2 versoes selecionaveis (proporcional vs igual) mas formulas IF aninhadas ficam enormes
**Why it happens:** Cada celula precisaria de IF(toggle_cell="PROPORCIONAL", formula_prop, formula_igual)
**How to avoid:** As 2 versoes JA EXISTEM em colunas separadas: colunas L:X = proporcional, colunas BB:BN = igualitaria, colunas BP:CB = compensada dinamica. Na COMITE, referenciar a versao adequada via celula de controle ou mostrar ambas
**Warning signs:** Formulas > 255 chars (limite Excel)

### Pitfall 6: DataBar/IconSet pode nao ser preservado apos reopen via openpyxl
**What goes wrong:** openpyxl grava conditional formatting corretamente, mas ao reabrir e salvar novamente pode perder regras
**Why it happens:** Bug conhecido do openpyxl com conditional formatting complexo em reopens
**How to avoid:** Aplicar conditional formatting DEPOIS de gravar todos os dados; nao reprocessar a aba COMITE apos criacao; usar XML surgery se necessario (padrao Phase 5)
**Warning signs:** Formatacao visual some apos reopem no Python (mas funciona no Excel)

## Code Examples

### Aggregar META por consultor (formula para COMITE)
```python
# Referenciando PROJECAO sheet (nome com acento + trailing space)
prj_ref = "'PROJECAO '!"  # Use the actual sheet reference
consultor_cell = f'A{row}'  # Cell containing consultant name

# META ANUAL por consultor
f_meta_anual = f'=SUMIFS({prj_ref}L$4:L$537,{prj_ref}D$4:D$537,{consultor_cell})'

# REALIZADO ANUAL por consultor
f_real_anual = f'=SUMIFS({prj_ref}Z$4:Z$537,{prj_ref}D$4:D$537,{consultor_cell})'

# % ATINGIMENTO
f_pct = f'=IFERROR(C{row}/B{row},0)'  # real / meta

# GAP R$
f_gap = f'=B{row}-C{row}'  # meta - real

# META por mes (exemplo JAN, col M na PROJECAO)
f_meta_jan = f'=SUMIFS({prj_ref}M$4:M$537,{prj_ref}D$4:D$537,{consultor_cell})'
```

### Contagem de contatos por consultor (formula para COMITE)
```python
# Referenciando LOG sheet
# LOG columns: A=DATA, B=CONSULTOR, L=TIPO, M=RESULTADO
date_filter = 'LOG!$A$3:$A$21000,">="&$E$2,LOG!$A$3:$A$21000,"<="&$F$2'
cons_filter = f',LOG!$B$3:$B$21000,A{row}'

# Total contatos
f_total = f'=COUNTIFS({date_filter}{cons_filter})'

# Vendas
f_vendas = f'=COUNTIFS({date_filter}{cons_filter},LOG!$M$3:$M$21000,"VENDA")'

# Orcamentos
f_orcam = f'=COUNTIFS({date_filter}{cons_filter},LOG!$M$3:$M$21000,"ORCAMENTO")'

# Contatos/dia (22 dias uteis)
f_contatos_dia = f'=IFERROR(TOTAL_CELL/22,0)'
```

### Capacidade de atendimento com semaforo
```python
# Contatos/dia calculado
f_carga_dia = f'=IFERROR(B{row}/22,0)'  # total contatos / 22 dias uteis

# Semaforo de capacidade (formula texto)
f_semaforo_cap = f'=IF(G{row}<35,"VERDE",IF(G{row}<=50,"AMARELO","VERMELHO"))'

# Conditional formatting (via Python, nao formula)
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill

green = PatternFill(bgColor='C6EFCE')
yellow = PatternFill(bgColor='FFEB9C')
red = PatternFill(bgColor='FFC7CE')

# Aplicar na range de carga/dia
ws.conditional_formatting.add(f'G5:G11',
    FormulaRule(formula=[f'G5<35'], fill=green))
ws.conditional_formatting.add(f'G5:G11',
    FormulaRule(formula=[f'AND(G5>=35,G5<=50)'], fill=yellow))
ws.conditional_formatting.add(f'G5:G11',
    FormulaRule(formula=[f'G5>50'], fill=red))
```

### Bloco COMITE com estilo FORMATO_APROVADO
```python
from v3_styles import *

# Titulo do bloco (estilo DASH existente)
def build_block_header(ws, row, title, cols=17):
    section_title(ws, row, title, end_col=cols)

# Header de coluna (fundo escuro, texto branco, Calibri 10 bold)
def build_col_headers(ws, row, headers):
    for i, h in enumerate(headers, 1):
        write_header(ws, row, i, h, fill=FILL_DARK, font=FONT_HEADER)

# Linha de dados
def build_data_row(ws, row, col_values):
    for col, val in col_values.items():
        write_data(ws, row, col, val)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Meta so por rede (V11-V12) | Meta por CLIENTE individual (V13/Phase 1) | Phase 1 | 534 metas individuais vs 20 por rede |
| Dashboard KPI cards | Tabela densa estilo FORMATO_APROVADO | Phase 5 | Layout aprovado pelo usuario |
| Dados estaticos | Formulas dinamicas cross-sheet | Phase 5/7 | Atualiza automaticamente |
| Semaforo via emoji | Conditional formatting nativo | Phase 8 (novo) | Mais profissional |

**Informacao critica ja existente no V13:**

| Dado | Localizacao V13 | Status |
|------|----------------|--------|
| META ANUAL por cliente | PROJECAO col L (12) | PRONTO - 534 valores |
| META JAN-DEZ por cliente | PROJECAO cols M:X (13:24) | PRONTO - 534 x 12 = 6.408 valores |
| REALIZADO JAN-DEZ por cliente | PROJECAO cols AA:AL (27:38) | PARCIAL - so OUT/NOV/DEZ 2025 |
| % YTD atingimento | PROJECAO col AN (40) | PRONTO - formula |
| SINAL META (emoji) | PROJECAO col AO (41) | PRONTO - formula IF |
| GAP (meta - real) | PROJECAO col AP (42) | PRONTO - formula |
| RANKING | PROJECAO col AQ (43) | PRONTO - formula RANK |
| META IGUALITARIA | PROJECAO cols BB:BN (54:66) | PRONTO - formulas |
| META COMPENSADA DINAMICA | PROJECAO cols BP:CB (68:80) | PRONTO - formulas SUMPRODUCT |
| CONSULTOR por cliente | PROJECAO col D (4) | PRONTO - 534 valores |
| REDE/GRUPO CHAVE | PROJECAO col C (3) | PRONTO - 534 valores |
| LOG de atendimentos | LOG tab, 20.830 registros | PRONTO |
| Contatos/vendas/motivos | LOG cols A-U | PRONTO |
| Sinaleiro de rede | REDES_FRANQUIAS_v2 tab | PRONTO |

## Analise dos Consultores

| Consultor | Clientes | META ANUAL (R$) | % do Total | REALIZADO (R$) | % Ating. |
|-----------|----------|-----------------|------------|----------------|----------|
| LARISSA PADILHA | 212 | 2.543.747 | 53.2% | 955.040 | 37.5% |
| HEMANUELE DITZEL (MANU) | 170 | 1.552.437 | 32.5% | 619.077 | 39.9% |
| JULIO GADRET | 63 | 412.014 | 8.6% | 165.698 | 40.2% |
| DAIANE STAVICKI | 47 | 260.205 | 5.4% | 318.183 | 122.3% |
| MANU DITZEL (alias antigo) | 1 | 10.601 | 0.2% | 23.033 | 217.3% |
| **TOTAL** | **493** | **4.779.003** | **100%** | **2.081.030** | **43.5%** |

**NOTA:** 534 clientes na PROJECAO mas 41 sem consultor atribuido (provavelmente Leandro Garcia=1, Lorrany=1, +39 sem valor). Os 493 com consultor valido representam 92% da carteira.

**NOTA 2:** O % atingimento esta baixo (43.5%) porque REALIZADO so tem dados OUT/NOV/DEZ 2025 (3 meses) vs META para 2026 inteiro (12 meses). Isso e ESPERADO e sera corrigido conforme dados 2026 forem alimentados.

**NOTA 3:** DAIANE e MANU DITZEL (alias) estao >100% porque sao poucos clientes com vendas concentradas nos 3 meses disponiveis. A meta anualizada para 3 meses seria ~25% (3/12), entao DAIANE com 122% esta na verdade muito acima da meta mensal.

## Recomendacoes para Decisoes Discricionarias

### 1. Quantos blocos na aba COMITE (Recomendacao: 5 blocos)
Os 5 blocos do CONTEXT.md sao viaveis e suficientes:
1. **BLOCO 1: META vs REALIZADO** (~rows 5-15) -- tabela 7 consultores + TOTAL, 12+ colunas
2. **BLOCO 2: CAPACIDADE/PRODUTIVIDADE** (~rows 19-29) -- carga/dia, vendas/dia, conversao
3. **BLOCO 3: ALERTAS VISUAIS** (~rows 33-43) -- flags de risco, sobrecarga, gaps criticos
4. **BLOCO 4: FUNIL CONSOLIDADO** (~rows 47-58) -- tipo x resultado (matriz do FORMATO_APROVADO)
5. **BLOCO 5: MOTIVOS NAO COMPRA** (~rows 62-75) -- top 10 motivos + % + dono

Total estimado: ~75 linhas, cabe em 1 tela com scroll moderado.

### 2. Quais visoes do V12 HTML sao viaveis (Recomendacao: 5 de 8)

| Tab V12 HTML | Viavel em Excel? | Onde fica? | Justificativa |
|--------------|-----------------|------------|---------------|
| Resumo | SIM | COMITE Bloco 1 | SUMIFS simples |
| Operacional | SIM | COMITE Bloco 2 | COUNTIFS + calculos |
| Funil & Canais | SIM | COMITE Bloco 4 | Ja existe na DASH (replicar estilo) |
| Performance | SIM | COMITE Blocos 1+2 | Subdividido nos 2 primeiros blocos |
| Tendencias | NAO nesta fase | Deferred | Precisaria de 12 linhas por consultor (explosao de formulas) |
| Sinaleiro | SIM | REDES_FRANQUIAS_v2 | JA EXISTE (Phase 7) |
| Eficiencia | NAO nesta fase | Deferred | CAC/ROI requer dados de custo nao disponiveis |
| Produtividade | SIM | COMITE Bloco 2 | Merge com capacidade |

### 3. Ordem dos blocos (Recomendacao: manter a ordem do CONTEXT)
A ordem proposta no CONTEXT segue a logica gerencial:
1. Meta (o que espero) -> 2. Capacidade (consigo atender?) -> 3. Alertas (o que esta errado?) -> 4. Funil (como estao os contatos?) -> 5. Motivos (por que nao compram?)

### 4. Toggle de versao de rateio (Recomendacao: celula de controle)
Usar uma celula de controle no header (ex: I2) com dropdown "PROPORCIONAL" / "IGUALITARIO" / "COMPENSADO".
As formulas do Bloco 1 usariam:
```
=IF($I$2="IGUALITARIO", SUMIFS(BB col), IF($I$2="COMPENSADO", SUMIFS(BP col), SUMIFS(L col)))
```
Onde: L=proporcional, BB=igualitario, BP=compensado dinamico. Todas essas colunas ja existem na PROJECAO.

### 5. Formatacao condicional (Recomendacao: combinar formula + condicional)
- **Semaforo META:** Usar emoji na formula (padrao ja existente) + FormulaRule para background color
- **Barra de volume:** DataBarRule nas colunas de R$ (META ANUAL, REALIZADO, GAP)
- **Capacidade:** FormulaRule com 3 cores (verde/amarelo/vermelho baseado em contatos/dia)

## Analise da Fonte de Dados SAP

### BASE_SAP_META_PROJECAO_2026.xlsx
- **7 abas:** Carteira (81 rows, 22 cols), Historico-FAT (1521 rows, 41 cols), Leads (83 rows, 26 cols), Positivacao (83 rows, 31 cols), Faturamento (1523 rows, 35 cols), Balizador da Meta (22 rows, 21 cols), Resumo (23 rows, 17 cols)
- **Meta por GRUPO CHAVE (rede):** Nao por consultor individual. A aba "Carteira" tem 80 grupos com DAIANE STAVICKI como gerente de todos (campo "ZP - GERENTE NACIONAL")
- **Faturamento:** 1523 rows, colunas JAN-DEZ 2026, filtro "TOTAIS=SIM" + "01. TOTAL" para aggregate por grupo, soma = R$ 4.747.200
- **Leads:** Projecao de crescimento de leads por rede por mes
- **Positivacao:** % positivacao mensal por rede com classificacao (MADURO/EM CRESCIMENTO/NOVO)
- **Balizador:** Distribuicao da meta por grupo de produto (MAIS GRANEL 32%, BISCOITO 7%, etc.)

### Como a meta chegou na PROJECAO (historico Phase 1)
A Phase 1 ja fez o rateio: meta total R$ 4.747.200 -> distribuida por rede (SAP Faturamento) -> distribuida por cliente dentro de cada rede (proporcional ao historico 2025). O resultado sao os 534 valores individuais na coluna L. A diferenca de R$ 31.803 (4.779.003 vs 4.747.200) vem de arredondamento no rateio proporcional.

## Layout Detalhado da Aba COMITE (Proposta)

### Cabecalho (Rows 1-2)
```
Row 1: [merge A1:Q1] "COMITE COMERCIAL -- VITAO ALIMENTOS 360"
Row 2: VENDEDOR [C2=dropdown] | PERIODO [E2=date] [F2=date] | RATEIO [I2=dropdown PROPORCIONAL/IGUALITARIO/COMPENSADO]
```

### BLOCO 1: META vs REALIZADO (Rows 4-14)
```
Row 4: [titulo] META vs REALIZADO POR CONSULTOR
Row 5: [headers] CONSULTOR | META ANUAL | REAL ANUAL | % ATING | GAP R$ | SEMAFORO | META MES | REAL MES | % MES | GAP MES | CLIENTES | RANKING
Row 6-9: MANU | LARISSA | JULIO | DAIANE (4 consultores)
Row 10: [vazio para MANU DITZEL alias se necessario]
Row 11: TOTAL EQUIPE
Row 12: META SAP OFICIAL (valor fixo R$ 4.747.200 para referencia)
```
Formulas: SUMIFS referenciando PROJECAO cols L,Z por consultor. Semaforo via condicional.

### BLOCO 2: CAPACIDADE/PRODUTIVIDADE (Rows 16-26)
```
Row 16: [titulo] CAPACIDADE E PRODUTIVIDADE POR CONSULTOR
Row 17: [headers] CONSULTOR | TOTAL CONTATOS | CONTATOS/DIA | VENDAS | VENDAS/DIA | % CONVERSAO | ORCAMENTOS | CADASTROS | FOLLOW-UPS | PROSPECCOES | SUPORTE | % MERCOS | CARGA %
Row 18-21: 4 consultores
Row 22: TOTAL EQUIPE
```
Formulas: COUNTIFS referenciando LOG. Capacidade = contatos/22 dias / 50 (limite).

### BLOCO 3: ALERTAS VISUAIS (Rows 29-40)
```
Row 29: [titulo] ALERTAS E RISCOS
Row 30: [headers] CONSULTOR | STATUS | CARGA/DIA | ALERTA CARGA | META % | ALERTA META | CLIENTES INATIVOS | CLIENTES SEM CONTATO | RISCO PRINCIPAL
Row 31-34: 4 consultores
Row 35: [vazio]
Row 36: [sub-titulo] CLIENTES CRITICOS (TOP 5 GAPS)
Row 37: [headers] CLIENTE | CONSULTOR | META | REALIZADO | GAP | RANKING
Row 38-42: Top 5 por GAP (via LARGE/INDEX/MATCH)
```

### BLOCO 4: FUNIL CONSOLIDADO (Rows 45-55)
```
Row 45: [titulo] TIPO DO CONTATO x RESULTADO DO CONTATO
Row 46: [headers] TIPO DO CONTATO | TOTAL | ORCAM. | CADAST. | RELAC. | EM ATEND. | SUPORTE | VENDA | N ATENDE | RECUSOU | N RESP. | PERDA | FOLLOW UP
Row 47-53: 7 tipos de contato
Row 54: TOTAL
```
Formulas: Mesma estrutura da DASH existente, mas filtrada por periodo.

### BLOCO 5: MOTIVOS DE NAO COMPRA (Rows 58-70)
```
Row 58: [titulo] MOTIVOS DE NAO COMPRA + DONO DA ACAO
Row 59: [headers] MOTIVO | QTD | % | PROSP | ATIVOS | INAT | POS-V | DONO DA ACAO
Row 60-69: 10 motivos
Row 70: TOTAL
```
Formulas: Mesma estrutura da DASH existente + coluna DONO DA ACAO (estatica, preenchida pelo gestor).

## Open Questions

1. **Dados REALIZADO 2026 disponiveis?**
   - What we know: Colunas AA-AL na PROJECAO so tem OUT/NOV/DEZ 2025 (ultimos 3 meses de historico)
   - What's unclear: Quando dados JAN/FEV 2026 serao alimentados? O gestor ja tem esses dados?
   - Recommendation: Construir a COMITE com as formulas corretas; os dados aparecem automaticamente quando populados na PROJECAO

2. **Alias MANU DITZEL vs HEMANUELE DITZEL (MANU)**
   - What we know: 10 clientes usam "MANU DITZEL" e 170 usam "HEMANUELE DITZEL (MANU)"
   - What's unclear: Foram normalizados na Phase 4 ou e intencional?
   - Recommendation: Na COMITE, incluir formula que some ambas: `=SUMIFS(...,"HEMANUELE*") + SUMIFS(...,"MANU DITZEL")` ou corrigir os 10 na PROJECAO

3. **Diferenca de R$ 31.803 no total de metas**
   - What we know: PROJECAO soma R$ 4.779.003 vs SAP R$ 4.747.200
   - What's unclear: Origem exata da diferenca (arredondamento no rateio proporcional da Phase 1)
   - Recommendation: Investigar e corrigir no Plan 08-01 se possivel; caso contrario, documentar como margem de arredondamento (0.67%)

4. **41 clientes sem consultor**
   - What we know: 534 na PROJECAO mas so 493 com consultor de vendas (Leandro=1, Lorrany=1, +39 sem valor)
   - What's unclear: Esses clientes devem aparecer na COMITE?
   - Recommendation: Incluir uma linha "OUTROS/SEM CONSULTOR" na COMITE para nao perder dados

## Sources

### Primary (HIGH confidence)
- V13 workbook (CRM_VITAO360_V13_PROJECAO.xlsx) -- inspecionado diretamente via openpyxl
- BASE_SAP_META_PROJECAO_2026.xlsx -- inspecionado diretamente (7 abas, 1523 rows Faturamento)
- scripts/phase07_redes_franquias/02_create_redes_tab.py -- padrao de criacao de aba
- scripts/phase05_dashboard/02_build_dash.py -- padrao de formulas DASH
- scripts/v3_styles.py -- constantes de estilo compartilhadas
- scripts/extract_meta_sap.py -- script de extracao ja existente

### Secondary (MEDIUM confidence)
- DASH_FORMATO_APROVADO_DADOS_REAIS.html -- layout visual aprovado pelo usuario
- DASHBOARD_VITAO360_V12_COMPLETO.html -- 8 tabs de referencia para blocos
- openpyxl 3.1.5 conditional formatting -- testado (DataBarRule, FormulaRule, CellIsRule, IconSetRule OK)

### Tertiary (LOW confidence)
- Nenhum item LOW confidence nesta pesquisa

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- mesmas ferramentas de 7 fases anteriores
- Architecture: HIGH -- padrao estabelecido (Phase 5 DASH + Phase 7 REDES)
- Data availability: HIGH -- toda a infraestrutura de metas ja existe na PROJECAO
- Pitfalls: HIGH -- baseado em experiencia real das 7 fases anteriores
- Layout COMITE: MEDIUM -- proposta detalhada mas depende de aprovacao do numero de blocos

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (estavel -- infraestrutura V13 nao muda)
