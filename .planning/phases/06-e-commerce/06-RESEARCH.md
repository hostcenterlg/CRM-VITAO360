# Phase 6: E-commerce - Research

**Researched:** 2026-02-17
**Domain:** ETL de relatorios Mercos e-commerce B2B + cruzamento por nome (sem CNPJ direto) + populacao de colunas no DRAFT 1
**Confidence:** HIGH

## Summary

Phase 6 processa os relatorios de acesso ao e-commerce B2B Mercos e cruza os dados com a CARTEIRA (via DRAFT 1) para popular colunas que indicam engajamento digital dos clientes. A pesquisa revelou que os arquivos-fonte tem problemas GRAVES de nomenclatura e duplicacao -- confirmando a decisao previa "Relatorios Mercos mentem nos nomes". Dos 17 arquivos encontrados (nao 20 como estimado), pelo menos 3 sao duplicatas identicas com nomes de meses diferentes, 2 sao versoes do mesmo mes (janeiro), e nao existe arquivo de Outubro.

O desafio central e que os relatorios de e-commerce **nao contem CNPJ** -- apenas Razao Social e Nome Fantasia. O matching com a CARTEIRA (que usa CNPJ como chave primaria) precisa de um passo intermediario: lookup nome->CNPJ via 08_CARTEIRA_MERCOS.xlsx, similar ao motor de matching usado na Phase 2 (04_fuzzy_match_sem_cnpj.py).

Outro ponto critico: o DRAFT 1 (DL_DRAFT1_FEV2026.xlsx) JA possui 6 colunas de e-commerce (cols 15-20: ACESSOS SEMANA, ACESSO B2B, ACESSOS PORTAL, ITENS CARRINHO, VALOR B2B, OPORTUNIDADE), e a especificacao FASE_1_CARTEIRA.md define 6 colunas (AR-AW: ACESSA E-COMMERCE, DATA ULT.ACESSO, QTD ACESSOS MES, PEDIDO VIA E-COMMERCE, % PEDIDOS E-COMMERCE, CATALOGO VISUALIZADO). As duas definicoes tem campos DIFERENTES. A pesquisa recomenda produzir um JSON intermediario com os campos consolidados para ambas as estruturas, que Phase 9 consumira para populacao final.

**Primary recommendation:** ETL em 2 scripts Python (extract + match/aggregate), output para JSON intermediario, seguindo exatamente o padrao estabelecido nas Phases 2-4. NAO popular V13 diretamente (CARTEIRA tem 0 rows). Popular DRAFT 1 como destino alternativo viavel.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1+ | Leitura de .xlsx (e-commerce reports) | Ja em uso em todas as 5 phases anteriores |
| json | stdlib | Output intermediario em JSON | Padrao do projeto para dados intermediarios |
| re | stdlib | Normalizacao de nomes para matching | Ja em uso no motor de matching |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| xlrd | 2.0+ | Leitura de .xls (relatorio.xls, relatorio (1).xls) | Somente se os 2 arquivos .xls forem relevantes |
| rapidfuzz | 3.0+ | Fuzzy matching nome->nome (fallback) | Se exact/partial match nao resolver >80% |
| unicodedata | stdlib | Strip accents para comparacao de nomes | Nomes com acentos vs sem acentos |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl read_only | pandas read_excel | pandas nao esta instalado; openpyxl ja e padrao do projeto |
| rapidfuzz | Levenshtein manual | rapidfuzz ja e dependencia do projeto e mais preciso |
| JSON intermediario | Popular V13 direto | V13 CARTEIRA tem 0 rows -- Phase 9 e responsavel pela populacao |

**Installation:**
```bash
# openpyxl ja instalado; rapidfuzz ja instalado (Phase 2)
# xlrd pode ser necessario se .xls files forem relevantes:
pip install xlrd
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  phase06_ecommerce/
    01_extract_ecommerce.py    # ETL: ler todos os XLSX, normalizar, dedup, output JSON
    02_match_populate.py       # Match: cruzar com Mercos Carteira, agregar, popular DRAFT 1
data/
  output/
    phase06/
      ecommerce_raw.json       # Dados brutos extraidos (por mes, por nome)
      ecommerce_matched.json   # Dados cruzados com CNPJ (por CNPJ, agregado)
      match_report.json        # Relatorio de matching (taxa, falhas)
```

### Pattern 1: ETL com Header Detection Dinamica
**What:** Os reports Mercos tem headers na ROW 6 (nao row 1), precedidos por "Relatorio clientes" (row 2) e "Emitido em DD/MM/YYYY" (row 3). Alem disso, ha 2 formatos: 9 colunas (antigo) e 11 colunas (novo, com E-mail e Telefone).
**When to use:** Sempre que ler um arquivo de e-commerce.
**Example:**
```python
def find_header_row(ws):
    """Encontra a row com headers (Razao Social na col 1)."""
    for r in range(1, 10):
        val = ws.cell(row=r, column=1).value
        if val and 'Raz' in str(val):
            return r
    return 6  # fallback

def get_emission_date(ws):
    """Extrai data de emissao do relatorio (row 3 tipicamente)."""
    for r in range(1, 6):
        val = str(ws.cell(row=r, column=1).value or '')
        if 'Emitido em' in val:
            # 'Emitido em 15/12/2025' -> '15/12/2025'
            match = re.search(r'(\d{2}/\d{2}/\d{4})', val)
            if match:
                return match.group(1)
    return None

def detect_format(ws, header_row):
    """Detecta formato: 9 cols (antigo) ou 11 cols (novo com Email+Telefone)."""
    col3_header = ws.cell(row=header_row, column=3).value
    if col3_header and 'mail' in str(col3_header).lower():
        return 'NEW_11COL'  # Email no col 3
    return 'OLD_9COL'  # Acessos no col 3
```

### Pattern 2: Nome-based Matching (sem CNPJ)
**What:** E-commerce reports contem apenas Razao Social e Nome Fantasia. Matching com CARTEIRA requer passo intermediario via Mercos Carteira (08_CARTEIRA_MERCOS.xlsx) que tem Razao Social + Nome Fantasia + CNPJ.
**When to use:** Sempre que cruzar dados de e-commerce com CNPJ.
**Example:**
```python
def build_name_to_cnpj_lookup():
    """
    Constroi lookup bidirecional nome->CNPJ usando:
    1. Mercos Carteira (08_CARTEIRA_MERCOS.xlsx) - Razao Social + Nome Fantasia
    2. SAP Cadastro (01_SAP_CONSOLIDADO.xlsx) - Nome Cliente
    3. DRAFT 1 - CNPJ + Razao Social

    Reutiliza padrao de Phase 2 (04_fuzzy_match_sem_cnpj.py).
    """
    lookup = {}
    # Mercos Carteira: ~497 entries com CNPJ
    # ... (ver 04_fuzzy_match_sem_cnpj.py para implementacao)
    return lookup

def match_ecommerce_to_cnpj(razao_social, nome_fantasia, lookup):
    """
    Tenta match em 3 niveis:
    1. Exact match (uppercase, stripped)
    2. Partial match (um contido no outro)
    3. Fuzzy match (rapidfuzz, threshold 85+)
    """
    # ... (ver try_match() em 04_fuzzy_match_sem_cnpj.py)
    pass
```

### Pattern 3: Agregacao Temporal por CNPJ
**What:** Cada arquivo de e-commerce cobre um mes. A agregacao consolida por CNPJ: total acessos, ultimo acesso, itens carrinho, pedidos B2B.
**When to use:** Apos matching, para calcular campos derivados da CARTEIRA.
**Example:**
```python
def aggregate_by_cnpj(matched_records):
    """
    Agrega dados mensais por CNPJ para popular CARTEIRA:
    - ACESSA E-COMMERCE: SIM se qualquer mes teve acesso
    - DATA ULT.ACESSO: max(emission_date) entre meses com acesso
    - QTD ACESSOS MES: media ou ultimo mes
    - PEDIDO VIA E-COMMERCE: SIM se algum 'Valor em pedidos B2B' > 0
    - % PEDIDOS E-COMMERCE: calculado via cross-ref com faturamento total
    - CATALOGO VISUALIZADO: SIM se 'Todas as atividades' > 0
    """
    pass
```

### Anti-Patterns to Avoid
- **Confiar no nome do arquivo para determinar o mes:** Arquivos "Abril", "Maio" e "junho " contem dados IDENTICOS. Usar data de emissao e/ou conteudo para determinar o mes real.
- **Assumir formato uniforme:** Existem 2 formatos (9 e 11 colunas). Detectar dinamicamente.
- **Inserir dados direto no V13:** CARTEIRA no V13 tem 0 rows de dados. Output deve ser JSON intermediario para Phase 9.
- **Ignorar duplicatas de arquivos:** Existem pares de arquivos que cobrem o mesmo periodo com dados diferentes (versoes parcial vs completa).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Name matching | Custom string distance | Reutilizar build_mercos_lookup() + try_match() de Phase 2 | Ja testado com 10 clientes sem CNPJ, 100% match rate |
| CNPJ normalization | Custom parser | normalize_cnpj() de _helpers.py (Phase 4) | Ja validado, handles edge cases |
| Accent stripping | Manual char map | strip_accents() de Phase 2 ou _remover_acentos() de Phase 4 | Unicode-compliant |
| Excel sheet finding | ws[name] direto | find_sheet() de Phase 2 (ignora acentos e espacos) | Sheets Mercos tem espacos trailing |

**Key insight:** 70%+ do codigo necessario para Phase 6 ja existe em scripts de Phases 2 e 4. A fase e primariamente "cola" entre ETL existente e um novo dominio de dados.

## Common Pitfalls

### Pitfall 1: Arquivos com Nomes Errados (CRITICO)
**What goes wrong:** Tratar nome do arquivo como verdade para determinar o mes dos dados.
**Why it happens:** Os relatorios Mercos sao exportados manualmente e renomeados pelo usuario. "Relatorios Mercos mentem nos nomes" e uma decisao registrada no projeto.
**How to avoid:**
1. Extrair data de emissao do relatorio (row 3: "Emitido em DD/MM/YYYY")
2. Comparar conteudo (razao social + acessos) entre arquivos para detectar duplicatas
3. Nao confiar no nome do arquivo para nada alem de localizacao
**Warning signs:** Arquivos com tamanhos identicos, mesmos primeiros registros, nomes que nao batem com a data de emissao.
**Evidencia encontrada:**
- "Abril", "Maio", "junho " (com espaco) = dados IDENTICOS (mesmos 3 primeiros registros, mesmos counts)
- "Dezembro " e "Acessos Dezembro " = dados IDENTICOS (24 rows cada, mesma emissao)
- "janeiro 2026" (66 rows, 11 cols) e "rELATORIO JANEIRO 2026" (134 rows, 9 cols) = dados DIFERENTES para o mesmo mes

### Pitfall 2: Matching por Nome sem CNPJ
**What goes wrong:** Taxa de match baixa porque nomes na e-commerce nao batem exatamente com a Mercos Carteira.
**Why it happens:** E-commerce reports usam Razao Social do cadastro Mercos, mas pode haver variantes (abreviacoes, acentos, CNPJ no prefixo do nome em arquivos mais novos).
**How to avoid:**
1. Usar matching em 3 niveis: exact -> partial -> fuzzy (rapidfuzz >= 85)
2. Normalizar: uppercase, strip, collapse spaces, remove acentos
3. Tratar prefixo numerico: arquivos novos tem CNPJ no inicio do nome (ex: "48.144.171 ROSANGELA...")
4. Construir lookup bidirecional: Razao Social -> CNPJ E Nome Fantasia -> CNPJ
**Warning signs:** Taxa de match abaixo de 80%.

### Pitfall 3: Formato Inconsistente entre Versoes
**What goes wrong:** Parser quebra porque assume formato fixo.
**Why it happens:** Mercos mudou o formato do relatorio entre 2025 e 2026:
- Formato antigo (9 cols): Razao Social, Nome Fantasia, Num.acessos, Itens adicionados, Orcamentos finalizados, Atividades, Valor carrinho, Valor orc.nao finalizados, Valor pedidos B2B
- Formato novo (11 cols): Razao Social, Nome Fantasia, **E-mail, Telefone**, Num.acessos, Itens adicionados, Orcamentos finalizados, Atividades, Valor carrinho, Valor orc.nao finalizados, Valor pedidos B2B
**How to avoid:** Detectar formato pela presenca de "E-mail" na coluna 3 do header row.
**Warning signs:** Dados de acessos aparecendo como emails ou vice-versa.

### Pitfall 4: Dupla Contagem por Duplicatas de Arquivos
**What goes wrong:** Somar acessos/valores duas vezes porque dois arquivos cobrem o mesmo periodo.
**Why it happens:** Ha pares de duplicatas:
- "Dezembro " e "Acessos Dezembro " = identicos (usar apenas 1)
- "junho " e "Abril" e "Maio" = identicos (usar apenas 1, determinar mes real)
- "janeiro 2026" e "rELATORIO JANEIRO 2026" = versoes diferentes (um parcial com 66 rows, outro completo com 134 rows)
**How to avoid:**
1. Fase de dedup ANTES do processamento: comparar primeiros 5 registros + count
2. Quando houver duplicata, manter o arquivo com MAIS dados
3. Documentar cada decisao de dedup no match_report.json
**Warning signs:** Total de acessos irrealisticamente alto.

### Pitfall 5: Meses Faltantes
**What goes wrong:** Assumir que todos os 12 meses estao cobertos quando na verdade faltam meses.
**Why it happens:** Nao existe arquivo para Janeiro/25, Fevereiro/25, e Outubro/25 (e possivelmente outros se as duplicatas absorverem meses).
**How to avoid:**
1. Mapear mes real de cada arquivo ANTES de processar
2. Documentar meses faltantes explicitamente
3. Usar "N/A" ou null para meses sem dados (nao zero -- zero significa "0 acessos")
**Warning signs:** Gap no timeline de meses.

### Pitfall 6: Arquivos .xls (formato antigo)
**What goes wrong:** openpyxl nao le .xls (formato Excel 97-2003). Script falha.
**Why it happens:** 2 dos 17 arquivos sao .xls (relatorio.xls, relatorio (1).xls).
**How to avoid:** Instalar xlrd e tratar separadamente, OU converter manualmente para .xlsx, OU ignorar se forem duplicatas de arquivos .xlsx existentes.
**Warning signs:** Erro "openpyxl does not support .xls" ou ImportError xlrd.

## Inventario Completo dos Arquivos E-commerce

### Arquivos Encontrados (17 + 1 em fev2026/)

| # | Arquivo | Localizacao | Emissao | Rows | Cols | Mes Provavel | Status |
|---|---------|-------------|---------|------|------|--------------|--------|
| 1 | Acesso ao Ecomerce Marco .xlsx | ecommerce/ | 15/12/2025 | 44 | 9 | MAR/25 | UNICO |
| 2 | Acessop ao Ecomerce Abril .xlsx | ecommerce/ | 15/12/2025 | 84 | 9 | ???  | DUPLICATA (=junho =maio) |
| 3 | Acessop ao Ecomerce Maio.xlsx | ecommerce/ | 15/12/2025 | 84 | 9 | ??? | DUPLICATA (=junho =abril) |
| 4 | Acesso ao Ecomerce junho .xlsx | ecommerce/ | 15/12/2025 | 84 | 9 | ??? | DUPLICATA (=abril =maio) |
| 5 | Acesso ao Ecomerce junho.xlsx | ecommerce/ | 15/12/2025 | 133 | 9 | JUN/25 | UNICO (dados diferentes) |
| 6 | Acesso ao Ecomerce Julho .xlsx | ecommerce/ | 15/12/2025 | 95 | 9 | JUL/25 | UNICO |
| 7 | Acesso ao Ecomerce Agosto.xlsx | ecommerce/ | 15/12/2025 | 124 | 9 | AGO/25 | UNICO |
| 8 | Acesso ao Ecomerce Setembro .xlsx | ecommerce/ | 15/12/2025 | 133 | 9 | SET/25 | UNICO |
| 9 | (OUTUBRO) | N/A | N/A | N/A | N/A | OUT/25 | AUSENTE |
| 10 | Acesso ao Ecomerce Novembro .xlsx | ecommerce/ | 15/12/2025 | 192 | 9 | NOV/25 | UNICO |
| 11 | Acesso ao Ecomerce Dezembro .xlsx | ecommerce/ | 15/12/2025 | 24 | 9 | DEZ/25 (parcial) | VER NOTA |
| 12 | Acessos ao Ecomerce Dezembro .xlsx | ecommerce/ | 15/12/2025 | 24 | 9 | DEZ/25 (parcial) | DUPLICATA de #11 |
| 13 | Acesso ao ecomerce Dezembro 2025.xlsx | ecommerce/ | 15/01/2026 | 108 | 11 | DEZ/25 (completo) | UNICO - VERSAO MAIS COMPLETA |
| 14 | Acesso ao ecomerce janeiro 2026.xlsx | ecommerce/ | 15/01/2026 | 66 | 11 | JAN/26 (parcial) | VER NOTA |
| 15 | rELATORIO DE ACESSOS NO ECOMERCE JANEIRO 2026.xlsx | ecommerce/ | 30/01/2026 | 134 | 9 | JAN/26 (completo) | PREFERIR - MAIS DADOS |
| 16 | Acesso ao ecomerce b2b - fevereiro 2026.xlsx | ecommerce/ | 06/02/2026 | 50 | 9 | FEV/26 (parcial) | VER NOTA |
| 17 | relatorio.xls | ecommerce/ | ??? | ??? | ??? | ??? | PRECISA xlrd |
| 18 | relatorio (1).xls | ecommerce/ | ??? | ??? | ??? | ??? | PRECISA xlrd |
| 19 | acesso ao ecomerce fevereiro 2026.xlsx | fev2026/ | 15/02/2026 | 98 | 11 | FEV/26 (mais completo) | PREFERIR |

### Notas Criticas sobre o Inventario

1. **Trio duplicata (Abril/Maio/junho com espaco):** Estes 3 arquivos tem EXATAMENTE os mesmos dados (primeiros 3 registros identicos: DIONEI ARMACHUKI acessos=11, A.M.MENDANHA acessos=1, SAMUELL CARVALHO acessos=5). Nao e possivel determinar qual mes cobrem sem investigacao adicional. Recomendacao: tratar como 1 unico arquivo e tentar determinar mes real pelo conteudo.

2. **Dezembro: 3 versoes, 2 duplicatas.** "Acesso Dezembro " e "Acessos Dezembro " sao identicos (24 rows). "Dezembro 2025" tem 108 rows (formato novo com Email/Telefone, emitido 15/01/2026). Usar APENAS "Dezembro 2025.xlsx" (versao completa).

3. **Janeiro 2026: 2 versoes.** "Acesso janeiro 2026" (66 rows, formato novo, emitido 15/01) e "rELATORIO JANEIRO 2026" (134 rows, formato antigo, emitido 30/01). Preferir o rELATORIO (mais dados, emitido mais tarde). MAS: pode ser que os 2 arquivos tenham sets diferentes de clientes -- investigar merge.

4. **Fevereiro 2026: 2 versoes.** "b2b fevereiro 2026" (50 rows, formato antigo, emitido 06/02) na pasta ecommerce/ e "fevereiro 2026" (98 rows, formato novo, emitido 15/02) na pasta fev2026/. Preferir o da fev2026/ (mais dados).

5. **Outubro AUSENTE:** Nenhum arquivo encontrado em nenhuma localizacao.

6. **Contagem real apos dedup:** ~10-12 meses unicos (MAR, ???, ???, JUN, JUL, AGO, SET, NOV, DEZ, JAN/26, FEV/26) -- nao 20 como estimado.

### Colunas dos Relatorios E-commerce

**Formato antigo (9 colunas):**
| Col | Header | Tipo | Descricao |
|-----|--------|------|-----------|
| 1 | Razao Social | Texto | Nome juridico completo |
| 2 | Nome Fantasia | Texto | Nome comercial (pode ser None) |
| 3 | Num. de acessos | Inteiro | Quantidade de logins no portal B2B |
| 4 | Num. de itens adicionados | Inteiro | Itens colocados no carrinho |
| 5 | Num. de orcamentos finalizados | Inteiro | Orcamentos/pedidos concluidos |
| 6 | Todas as atividades | Inteiro | Total de acoes no portal |
| 7 | Valor no carrinho | Decimal | R$ valor dos itens no carrinho |
| 8 | Valor em orcamentos nao finalizados | Decimal | R$ orc. abandonados |
| 9 | Valor em pedidos B2B | Decimal | R$ pedidos efetivamente feitos via B2B |

**Formato novo (11 colunas) - adiciona Email e Telefone:**
| Col | Header | Tipo | Descricao |
|-----|--------|------|-----------|
| 1 | Razao Social | Texto | (igual) |
| 2 | Nome Fantasia | Texto | (igual) |
| 3 | E-mail | Texto | **NOVO** |
| 4 | Telefone | Texto | **NOVO** |
| 5-11 | (mesmos 7 campos de dados) | | (offset +2 colunas) |

## Mapeamento DRAFT 1 vs Blueprint CARTEIRA

### DRAFT 1 - Colunas E-commerce Existentes (cols 15-20)
| Col DRAFT1 | Header | Conteudo Observado |
|------------|--------|--------------------|
| 15 | ACESSOS SEMANA | Inteiro ou None |
| 16 | ACESSO B2B | "Sim" ou None |
| 17 | ACESSOS PORTAL | Inteiro ou None |
| 18 | ITENS CARRINHO | Inteiro ou None |
| 19 | VALOR B2B | Decimal (R$) ou None |
| 20 | OPORTUNIDADE | "COMPRA B2B" ou None |

### Blueprint CARTEIRA (FASE_1_CARTEIRA.md) - Grupo [+5] E-COMMERCE (cols AR-AW)
| Col CART | Header | Tipo | Mapeamento do E-commerce Report |
|----------|--------|------|---------------------------------|
| AR | ACESSA E-COMMERCE | SIM/NAO | SIM se qualquer acesso > 0 em qualquer mes |
| AS | DATA ULT.ACESSO | Data | Max emission_date entre meses com acessos > 0 |
| AT | QTD ACESSOS MES | Numero | Ultimo mes disponivel: Num.de acessos |
| AU | PEDIDO VIA E-COMMERCE | SIM/NAO | SIM se "Valor em pedidos B2B" > 0 em algum mes |
| AV | % PEDIDOS E-COMMERCE | Percentual | Requer cross-ref com Fat.Total (Phase 2 merged) |
| AW | CATALOGO VISUALIZADO | SIM/NAO | SIM se "Todas as atividades" > 0 |

### Mapeamento Report -> DRAFT 1
| DRAFT 1 Col | E-commerce Report Field | Logica |
|-------------|-------------------------|--------|
| ACESSOS SEMANA (15) | Num. de acessos | Ultimo mes (ou media) |
| ACESSO B2B (16) | Valor em pedidos B2B | "Sim" se > 0 |
| ACESSOS PORTAL (17) | Todas as atividades | Ultimo mes |
| ITENS CARRINHO (18) | Num. de itens adicionados | Ultimo mes |
| VALOR B2B (19) | Valor em pedidos B2B | Ultimo mes (R$) |
| OPORTUNIDADE (20) | Derivado | "COMPRA B2B" se tem atividade |

## Estrategia de Output

### Decisao: JSON intermediario + DRAFT 1 populado

Dado que:
- V13 CARTEIRA tem 0 rows de dados (populacao adiada para Phase 9)
- DRAFT 1 JA tem colunas de e-commerce (15-20) e ~500 rows de clientes
- Phase 9 precisa de JSON intermediario para popular a CARTEIRA expandida (81 cols)

**Output primario:** `data/output/phase06/ecommerce_matched.json`
```json
{
  "cnpj_to_ecommerce": {
    "32387943000105": {
      "acessa_ecommerce": true,
      "data_ult_acesso": "2025-11-15",
      "qtd_acessos_ultimo_mes": 38,
      "pedido_via_ecommerce": true,
      "valor_pedidos_b2b_total": 791.12,
      "catalogo_visualizado": true,
      "meses_com_acesso": ["MAR/25", "JUN/25", "NOV/25"],
      "total_atividades": 230,
      "total_itens_carrinho": 21,
      "total_orcamentos": 2,
      "valor_carrinho_total": 0.0,
      "monthly_data": {
        "2025-03": {"acessos": 2, "itens": 0, "orcamentos": 0, ...},
        "2025-11": {"acessos": 38, "itens": 21, ...}
      }
    }
  },
  "unmatched": [...],
  "stats": {...},
  "file_inventory": {...}
}
```

**Output secundario (opcional):** Popular DRAFT 1 colunas 15-20 com dados mais recentes.

## Code Examples

### Leitura de Arquivo E-commerce (ambos formatos)
```python
def read_ecommerce_file(path):
    """
    Le um arquivo de e-commerce Mercos (.xlsx).
    Retorna lista de dicts com campos normalizados.
    Detecta formato (9 ou 11 colunas) automaticamente.
    """
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    header_row = find_header_row(ws)
    emission_date = get_emission_date(ws)
    fmt = detect_format(ws, header_row)

    # Offset para campos de dados
    if fmt == 'NEW_11COL':
        offset = 2  # Email + Telefone adicionados
    else:
        offset = 0

    records = []
    for row in range(header_row + 1, ws.max_row + 1):
        razao = ws.cell(row=row, column=1).value
        if not razao or str(razao).strip() == '':
            continue

        fantasia = ws.cell(row=row, column=2).value
        acessos = ws.cell(row=row, column=3 + offset).value or 0
        itens = ws.cell(row=row, column=4 + offset).value or 0
        orcamentos = ws.cell(row=row, column=5 + offset).value or 0
        atividades = ws.cell(row=row, column=6 + offset).value or 0
        valor_carrinho = ws.cell(row=row, column=7 + offset).value or 0.0
        valor_orc_nf = ws.cell(row=row, column=8 + offset).value or 0.0
        valor_b2b = ws.cell(row=row, column=9 + offset).value or 0.0

        # Extrair CNPJ do prefixo do nome (formato novo: "48.144.171 NOME")
        cnpj_from_name = extract_cnpj_prefix(str(razao))

        records.append({
            'razao_social': str(razao).strip(),
            'nome_fantasia': str(fantasia or '').strip(),
            'cnpj_from_name': cnpj_from_name,
            'acessos': safe_int(acessos),
            'itens_adicionados': safe_int(itens),
            'orcamentos_finalizados': safe_int(orcamentos),
            'atividades': safe_int(atividades),
            'valor_carrinho': safe_float(valor_carrinho),
            'valor_orc_nao_finalizados': safe_float(valor_orc_nf),
            'valor_pedidos_b2b': safe_float(valor_b2b),
            'emission_date': emission_date,
        })

    wb.close()
    return records, emission_date, fmt
```

### Dedup de Arquivos
```python
def detect_duplicates(file_records):
    """
    Detecta arquivos duplicados comparando primeiros N registros.
    Retorna lista de grupos de duplicatas.
    """
    signatures = {}
    for path, records in file_records.items():
        # Signature: primeiros 5 razao_social + acessos
        sig = tuple(
            (r['razao_social'].upper()[:30], r['acessos'])
            for r in records[:5]
        )
        if sig not in signatures:
            signatures[sig] = []
        signatures[sig].append((path, len(records)))

    duplicates = []
    for sig, files in signatures.items():
        if len(files) > 1:
            # Manter o arquivo com mais rows
            files.sort(key=lambda x: -x[1])
            keep = files[0]
            discard = files[1:]
            duplicates.append({
                'keep': keep,
                'discard': discard,
                'reason': 'Same first 5 records'
            })
    return duplicates
```

### Matching com Mercos Carteira
```python
def match_ecommerce_name(razao, fantasia, cnpj_prefix, lookup):
    """
    Tenta match de nome do e-commerce para CNPJ.
    Estrategia:
    1. Se tem CNPJ no prefixo do nome, usa direto
    2. Exact match por Razao Social
    3. Exact match por Nome Fantasia
    4. Partial match (um contido no outro)
    5. Fuzzy match (rapidfuzz, threshold 85)
    """
    # 1. CNPJ do prefixo
    if cnpj_prefix and len(cnpj_prefix) >= 11:
        cnpj = cnpj_prefix.zfill(14)
        return cnpj, 'cnpj_prefix', 'Extracted from name'

    # 2-5: Reutilizar try_match() de Phase 2
    # ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Relatorios sem CNPJ, formato 9 cols | Relatorios com CNPJ no nome, formato 11 cols | ~Jan/2026 | Matching mais facil para arquivos novos |
| Export manual mes a mes | Mesmo (sem API) | N/A | ETL permanece manual, batch processing |

**Deprecated/outdated:**
- Formato 9 colunas: ainda funcional mas sem Email/Telefone (util como bonus)
- .xls files: formato Excel 97-2003, precisa de xlrd separado

## Open Questions

1. **Qual mes cobrem "Abril", "Maio", "junho " (dados identicos)?**
   - What we know: Dados sao 100% identicos entre os 3 arquivos. Todos emitidos 15/12/2025.
   - What's unclear: Qual e o mes real dos dados. Poderia ser qualquer um dos 3, ou nenhum (pode ser uma versao parcial de outro mes).
   - Recommendation: Investigar no ETL comparando com arquivos adjacentes (Marco, Julho). Se nenhum match, tratar como "MES DESCONHECIDO" e usar como fallback. Perguntar ao usuario se critico.

2. **Os 2 arquivos .xls contem dados de meses faltantes?**
   - What we know: relatorio.xls (34KB) e relatorio (1).xls (22KB). Nao foi possivel ler sem xlrd.
   - What's unclear: Conteudo, formato, mes coberto.
   - Recommendation: Instalar xlrd no ETL e inspecionar. Se forem meses novos (ex: Outubro), integrar. Se duplicatas, descartar.

3. **"4 colunas" ou "6 colunas" de e-commerce?**
   - What we know: Roadmap menciona "4 colunas", Blueprint define 6 (AR-AW), DRAFT 1 tem 6 (15-20) com nomes diferentes.
   - What's unclear: Se "4 colunas" no roadmap e apenas uma estimativa inicial ou se ha colunas que nao devem ser populadas.
   - Recommendation: Popular todas as 6 colunas do Blueprint (AR-AW) no JSON intermediario. Phase 9 decidira o mapeamento final. Tambem popular as 6 colunas do DRAFT 1 como output secundario.

4. **% PEDIDOS E-COMMERCE (AV) precisa de cross-ref com faturamento**
   - What we know: Requer dividir valor B2B pelo faturamento total do cliente (disponivel em sap_mercos_merged.json).
   - What's unclear: Periodo para calculo (ultimo mes? total acumulado?).
   - Recommendation: Calcular usando total acumulado (sum de monthly_data valor_b2b / sum de sap_mercos 12 meses). Armazenar ambos os valores no JSON para flexibilidade.

5. **Prefixo numerico nos nomes (formato novo) -- e sempre CNPJ?**
   - What we know: Arquivos novos (Dez/2025, Jan/2026, Fev/2026) tem nomes como "48.144.171 ROSANGELA..." onde o numero parece ser CNPJ parcial ou raiz.
   - What's unclear: Se o numero e sempre CNPJ valido (14 digits) ou pode ser CPF ou outro.
   - Recommendation: Extrair e validar: se >= 11 digits, tratar como CNPJ/CPF. Se < 11, ignorar.

## Sources

### Primary (HIGH confidence)
- Arquivos-fonte inspecionados diretamente via openpyxl (17 xlsx + 2 xls catalogados)
- FASE_1_CARTEIRA.md -- definicao das 6 colunas E-COMMERCE (AR-AW)
- DL_DRAFT1_FEV2026.xlsx -- estrutura existente das 6 colunas e-commerce (cols 15-20)
- 08_CARTEIRA_MERCOS.xlsx -- lookup Razao Social / Nome Fantasia -> CNPJ (497 entries)
- scripts/phase02_faturamento/04_fuzzy_match_sem_cnpj.py -- motor de matching existente
- scripts/phase04_log_completo/_helpers.py -- funcoes utilitarias reutilizaveis
- sap_mercos_merged.json -- 537 CNPJs com dados de faturamento
- .planning/STATE.md -- decisoes acumuladas e restricoes do projeto

### Secondary (MEDIUM confidence)
- Determinacao de meses reais dos arquivos via data de emissao e comparacao de conteudo
- Deteccao de duplicatas via comparacao de primeiros registros

### Tertiary (LOW confidence)
- Conteudo dos 2 arquivos .xls (nao inspecionados -- xlrd nao disponivel)
- Mes real do trio duplicata Abril/Maio/junho

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - mesmas ferramentas das 5 fases anteriores
- Architecture: HIGH - padrao ETL + JSON intermediario ja validado
- Data quality/dedup: MEDIUM - duplicatas detectadas por comparacao, mas meses reais do trio incertos
- Matching: HIGH - motor Phase 2 com 100% hit rate em 10 clientes, extensivel
- Pitfalls: HIGH - todos baseados em evidencia direta dos arquivos

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (estavel -- dados fonte nao mudam retroativamente)
