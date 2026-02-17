# Phase 7: Redes e Franquias - Research

**Researched:** 2026-02-17
**Domain:** CRM spreadsheet data enrichment -- rede/franquia classification, sinaleiro de penetracao, metas por rede
**Confidence:** HIGH

## Summary

Phase 7 envolve tres eixos: (1) preencher a coluna REDE/GRUPO CHAVE (col C) na PROJECAO do V13 para os 405 clientes atualmente marcados "SEM GRUPO", (2) criar/atualizar a aba REDES_FRANQUIAS_v2 no V13 (que NAO existe ainda -- precisa ser criada como upgrade da SINALEIRO_REDES do V11), e (3) atualizar o sinaleiro de penetracao e metas 6M por rede com dados 2025 atualizados.

A pesquisa revelou que o V13 ja tem um mini-sinaleiro de redes embutido nas colunas AS:AZ (linhas 4-15) com 12 redes, alimentando formulas VLOOKUP nas colunas F:J. As fontes primarias de dados de rede sao: SAP Cadastro Clientes (col AQ = "06 Nome Grupo Chave" com 19 redes unicas e 381 clientes mapeados) e a planilha "REDES E FRANQUIAS 2026" do desktop (620 lojas em 6 redes com CNPJ). Dos 405 clientes "SEM GRUPO", apenas 11 podem ser remapeados via SAP (7 ESMERALDA, 1 DIVINA TERRA, 1 MERCOCENTRO, 1 MINHA QUITANDINHA, 1 VIDA LEVE) -- os outros 394 sao genuinamente "SEM GRUPO" no SAP.

**Recomendacao principal:** Criar aba REDES_FRANQUIAS_v2 no V13 com estrutura expandida (baseada no SINALEIRO_REDES do V11 + PARAMETROS + PLANO_ACAO), atualizar a tabela de referencia AS:AZ com dados 2025 reais, corrigir os 11 clientes mismapeados, e agregar metas 6M do SAP por rede.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.x | Leitura/escrita XLSX com formulas | Ja usado em todas as fases anteriores |
| Python | 3.12.10 | Runtime | Padrao do projeto |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | Ler sap_mercos_merged.json | Quando precisar dados intermediarios |
| re | stdlib | Regex para matching de nomes de rede | Normalizar nomes entre fontes |
| collections | stdlib | Counter/defaultdict para agregacoes | Contagem e agrupamento |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl | pandas | Pandas nao preserva formulas XLSX -- openpyxl obrigatorio |
| Matching manual | fuzzy matching | Nao necessario -- mapping SAP eh por CNPJ exato |

**Installation:**
```bash
# Nenhuma instalacao necessaria -- openpyxl ja esta instalado
```

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  phase07_redes_franquias/
    01_map_rede_clients.py        # Mapear 11 clientes SEM GRUPO -> rede via SAP
    02_create_redes_tab.py        # Criar aba REDES_FRANQUIAS_v2 no V13
    03_update_sinaleiro_metas.py  # Atualizar sinaleiro + metas 6M
    04_validate_phase07.py        # Validacao final
```

### Pattern 1: Preservacao de Formulas (CRITICO)
**What:** Ao editar V13, NUNCA usar data_only=True para escrita. SEMPRE preservar 19.224 formulas existentes.
**When to use:** Qualquer operacao de escrita no V13.
**Example:**
```python
# Source: Padrao estabelecido em fases 1-6
wb = openpyxl.load_workbook('V13.xlsx', data_only=False)
ws = wb['PROJECAO ']
# Editar apenas celulas especificas, preservar formulas
ws.cell(row=4, column=3).value = 'FITLAND'  # Col C = REDE/GRUPO CHAVE
wb.save('V13.xlsx')
```

### Pattern 2: Normalizar Nomes de Rede entre Fontes
**What:** As fontes usam nomes ligeiramente diferentes para a mesma rede.
**When to use:** Ao cruzar dados entre SAP, CONTROLE_FUNIL, V13.
**Example:**
```python
# Mapa de normalizacao (SAP -> V13)
REDE_NORMALIZE = {
    '06 - INTERNA - BIO MUNDO': 'BIO MUNDO',
    '06 - INTERNA - CIA DA SAUDE': 'CIA DA SAUDE',
    '06 - INTERNA - DIVINA TERRA': 'DIVINA TERRA',
    '06 - INTERNA - FITLAND': 'FITLAND',
    '06 - INTERNA - MUNDO VERDE': 'MUNDO VERDE',
    '06 - INTERNA - VIDA LEVE': 'VIDA LEVE',
    '06 - INTERNA - NATURVIDA': 'NATURVIDA',
    '06 - INTERNA - TUDO EM GRAOS / VGA': 'TUDO EM GRAOS',
    '06 - INTERNA - TRIP': 'TRIP',
    '06 - INTERNA - MAIS NATURAL': 'MAIS NATURAL',
    '06 - INTERNA - LIGEIRINHO': 'LIGEIRINHO',
    '06 - INTERNA - PROSAUDE': 'PROSAUDE',
    '06 - INTERNA - ARMAZEM FIT STORE': 'ARMAZEM FIT STORE',
    '06 - INTERNA - ESMERALDA': 'ESMERALDA',
    '06 - INTERNA - NOVA GERACAO': 'NOVA GERACAO',
    '06 - INTERNA - MERCOCENTRO': 'MERCOCENTRO',
    '06 - INTERNA - JARDIM DAS ERVAS': 'JARDIM DAS ERVAS',
    '06 - INTERNA - FEDERZONI': 'FEDERZONI',
    '06 - INTERNA - MIX VALI': 'MIX VALI',
    '06 - INTERNA - MINHA QUITANDINHA - SP': 'MINHA QUITANDINHA',
    '06 - SEM GRUPO': 'SEM GRUPO',
}
```

### Pattern 3: Criar Nova Aba com Formulas
**What:** Criar REDES_FRANQUIAS_v2 com formulas dinâmicas (nao valores estáticos).
**When to use:** Para que o sinaleiro se atualize automaticamente.
**Example:**
```python
# Criar aba baseada na estrutura do SINALEIRO_REDES do V11
ws_new = wb.create_sheet('REDES_FRANQUIAS_v2')
# Formulas referenciam PROJECAO
# =COUNTIF('PROJECAO '!C$4:C$537,"FITLAND")  -> conta lojas da rede
# =SUMIFS('PROJECAO '!Z$4:Z$537,'PROJECAO '!C$4:C$537,A5)  -> fat real
```

### Anti-Patterns to Avoid
- **Usar data_only=True ao salvar:** Destrói todas as formulas. NUNCA fazer isso.
- **Reescrever celulas com formula sem verificar:** As colunas F:J do PROJECAO ja tem VLOOKUPs. Nao sobrescrever.
- **Hardcodar valores no sinaleiro:** Usar formulas para que atualize dinamicamente.
- **Ignorar freeze_panes=E30:** O V13 PROJECAO tem freeze_panes que deve ser preservado.
- **Adicionar redes novas sem atualizar o range de referencia:** O VLOOKUP atual aponta para AS$4:AX$18. Se adicionar mais redes, ajustar o range.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Matching CNPJ entre fontes | Parser de CNPJ customizado | Limpeza simples (remove ./- ) | CNPJ eh sempre 14 digitos, limpeza trivial |
| Sinaleiro de cores | Logica customizada de cores | Copiar formulas do SINALEIRO_REDES_VITAO.xlsx | Formulas ja testadas e aprovadas pelo usuario |
| PARAMETROS do sinaleiro | Inventar valores | Usar PARAMETROS do V11: benchmark=R$525, meses=11 | Valores calibrados pelo negocio |
| Metas 6M por rede | Calcular manualmente | Somar colunas JAN-JUN do SAP Faturamento (01. TOTAL) | Dados oficiais do SAP |

**Key insight:** A maior parte da logica de sinaleiro ja existe no arquivo SINALEIRO_REDES_VITAO.xlsx (5 abas: PAINEL, PARAMETROS, SINALEIRO, PLANO_ACAO, CADENCIA). O trabalho eh PORTAR essa logica para dentro do V13, nao reinventar.

## Common Pitfalls

### Pitfall 1: Confundir os Dois Sinaleiros
**What goes wrong:** O CRM tem DOIS sinaleiros distintos que sao frequentemente confundidos.
**Why it happens:** Ambos usam emojis de cores mas medem coisas diferentes.
**How to avoid:**
- SINALEIRO 1 (Ciclo de Compra): Compara DIAS SEM COMPRA vs CICLO MEDIO por CLIENTE
- SINALEIRO 2 (Atingimento de Meta): Compara REALIZADO vs META por CLIENTE (ja em PROJECAO cols AN:AO)
- SINALEIRO 3 (Penetracao de Rede): Compara FAT.REAL/FAT.POTENCIAL por REDE (este eh o da Phase 7)
**Warning signs:** Se ver "sinaleiro" sem qualificar qual, parar e verificar.

### Pitfall 2: Nome da Rede Inconsistente entre Fontes
**What goes wrong:** A mesma rede tem nomes diferentes conforme a fonte.
**Why it happens:** SAP usa "06 - INTERNA - BIO MUNDO", V13 usa "BIO MUNDO", REDES 2026 usa "BIOMUNDO", CONTROLE_FUNIL usa "BIO MUNDO".
**How to avoid:** Usar mapa de normalizacao (Pattern 2 acima). SEMPRE normalizar antes de comparar.
**Warning signs:** Contagens que nao batem entre fontes diferentes.

### Pitfall 3: Destruir Formulas Existentes no V13
**What goes wrong:** As 19.224 formulas do PROJECAO sao destruidas ao salvar.
**Why it happens:** Abrir com data_only=True, ou usar write_only mode, ou recriar celulas.
**How to avoid:** SEMPRE data_only=False. Editar apenas celulas alvo. Validar apos salvar que formulas permanecem.
**Warning signs:** Colunas F:J mostrando "" ao inves de valores calculados.

### Pitfall 4: Numero Errado de Redes
**What goes wrong:** Planejar para 8 redes (V11 original) mas precisar de 12+ (V13 atual).
**Why it happens:** V11 tinha 8 redes, V13 PROJECAO tem 12 redes na tabela AS:AZ, SAP tem 19 grupos-chave unicos.
**How to avoid:** Usar a lista completa de 12 redes do V13 como base, expandir com as 7 redes extras do SAP que nao aparecem no V13 (ARMAZEM FIT STORE, ESMERALDA, NOVA GERACAO, MERCOCENTRO, JARDIM DAS ERVAS, FEDERZONI, MIX VALI).
**Warning signs:** Range AS$4:AS$18 insuficiente para novas redes.

### Pitfall 5: "489 clientes" vs "534 clientes" Discrepancia
**What goes wrong:** O roadmap diz "489 clientes" mas o V13 PROJECAO tem 534.
**Why it happens:** O numero 489 pode ser de uma versao anterior do planejamento.
**How to avoid:** Usar o numero REAL do V13: 534 clientes (rows 4-537). Documentar a discrepancia.
**Warning signs:** Se alguem mencionar 489, esclarecer que o V13 atual tem 534.

## Dados Detalhados por Fonte

### V13 PROJECAO - Estado Atual
- **Tab:** `PROJECAO ` (com espaco no final)
- **Rows:** 537 (header em row 3, dados em 4-537 = 534 clientes)
- **Col C (REDE/GRUPO CHAVE):** 100% preenchido
  - SEM GRUPO: 405 clientes (75.8%)
  - Com rede atribuida: 129 clientes (24.2%)
  - 12 redes: FITLAND(44), VIDA LEVE(25), CIA DA SAUDE(22), DIVINA TERRA(15), BIO MUNDO(8), MUNDO VERDE(4), NATURVIDA(3), TUDO EM GRAOS(3), TRIP(2), MAIS NATURAL(1), LIGEIRINHO(1), PROSAUDE(1)
- **Cols F:J (SINALEIRO REDE):** Formulas VLOOKUP que referenciam tabela AS$4:AX$18
  - F = TOTAL LOJAS
  - G = SINALEIRO %
  - H = COR SINALEIRO
  - I = MATURIDADE
  - J = ACAO REDE
- **Cols AS:AZ (Tabela referencia):** 12 redes, linhas 4-15, VALORES ESTATICOS (nao formulas!)
  - AS = REDE nome
  - AT = TOTAL LOJAS (int)
  - AU = SINALEIRO % (float)
  - AV = COR (emoji + texto)
  - AW = MATURIDADE (texto)
  - AX = ACAO RECOMENDADA (texto)
  - AY = FAT. REAL (float)
  - AZ = GAP (float)
- **NAO existe aba REDES_FRANQUIAS_v2** -- precisa ser criada

### SAP - Dados Oficiais
- **01_SAP_CONSOLIDADO.xlsx / Cadastro Clientes SAP:**
  - 1698 clientes com CNPJ
  - Col AP = COD. 06 Grupo Chave
  - Col AQ = 06 Nome Grupo Chave
  - 19 grupos-chave unicos (excl. SEM GRUPO)
  - 381 clientes COM grupo, 1317 SEM GRUPO

- **BASE_SAP_META_PROJECAO_2026.xlsx / Faturamento:**
  - Metas mensais por GRUPO CHAVE x GRUPO PRODUTO
  - Filtrar "01. TOTAL" para meta total por rede
  - 19 redes com meta (6 com meta=0: FEDERZONI, MIX VALI, NOVA GERACAO, PROSAUDE, SEM GRUPO vazio)
  - Metas 6M (JAN-JUN) por rede principal:
    - FITLAND: R$ 283.500
    - CIA DA SAUDE: R$ 351.000
    - VIDA LEVE: R$ 154.500
    - DIVINA TERRA: R$ 157.500
    - BIO MUNDO: R$ 42.000
    - MUNDO VERDE: R$ 21.000
    - TUDO EM GRAOS: R$ 31.500
    - NATURVIDA: R$ 18.000
    - TRIP: R$ 9.000
    - LIGEIRINHO: R$ 9.000

- **BASE_SAP_META_PROJECAO_2026.xlsx / Leads:**
  - Total Lojas projetadas por rede (ex: FITLAND=80, CIA DA SAUDE=150, MUNDO VERDE=171)

### SINALEIRO_REDES_VITAO.xlsx - Template de Referencia
- **5 abas:** PAINEL, PARAMETROS, SINALEIRO, PLANO_ACAO, CADENCIA
- **PARAMETROS:** Benchmark R$525/mes/loja, 11 meses, faixas de cor:
  - ROXO: 0-1% (PROSPECCAO)
  - VERMELHO: 1-40% (ATIVACAO/POSITIVACAO)
  - AMARELO: 40-60% (SELL OUT)
  - VERDE: 60-100% (JBP)
- **SINALEIRO:** 8 redes (original V11), 20 colunas (A:T)
  - Colunas: REDE, CONSULTOR, TOTAL LOJAS, ATIVOS, INAT.REC, INAT.ANT, PROSPECT, CLIENTES C/VENDA, N.PEDIDOS, FAT.REAL, TICKET MEDIO, FAT.POTENCIAL, SINALEIRO%, COR, MATURIDADE, GAP, PENETRACAO%, ACAO, ECOM ACESSOS, PRIORIDADE
  - FAT.POTENCIAL = TOTAL_LOJAS * BENCHMARK * MESES
  - SINALEIRO% = FAT.REAL / FAT.POTENCIAL
- **PLANO_ACAO:** Ranking por GAP + meta 6M + acoes prioritarias
- **CADENCIA:** Frequencia de contato por etapa de maturidade

### REDES E FRANQUIAS 2026.xlsx - Dados Mercos
- 620 lojas com CNPJ, organizadas por 6 redes
- BIOMUNDO(167), DIVINA TERRA(82), FITLAND(60), MUNDO VERDE(199), TUDO EM GRAOS(25), VIDA LEVE(81)
- Colunas: MERCOS status, SAP SH, RAZAO SOCIAL, NOME FANTASIA, CNPJ, ESTADO, VENDEDOR, TAGS CLIENTE
- NAO inclui CIA DA SAUDE (que tem 74 clientes no SAP)

### CONTROLE_FUNIL_COMPLETO_FEV2026.xlsx - Dados Operacionais
- 751 clientes em 7 redes (tab REDES E FRANQUIAS)
- Inclui: GRUPO CHAVE, STATUS ATENDIMENTO, ACESSO PORTAL, campanhas
- Zero #REF! nesta versao

### Clientes SEM GRUPO Remapeaveis
- Total SEM GRUPO no V13: 405
- Remapeaveis via SAP CNPJ match: 11
  - ESMERALDA: 7
  - DIVINA TERRA: 1
  - MERCOCENTRO: 1
  - MINHA QUITANDINHA: 1
  - VIDA LEVE: 1
- Genuinamente SEM GRUPO: 394

## Interpretacao: "REDES_FRANQUIAS_v2" e "#REF!"

### Sobre REDES_FRANQUIAS_v2
A aba REDES_FRANQUIAS_v2 **NAO EXISTE** em nenhum arquivo analisado. Com base na investigacao:
- V11 tinha SINALEIRO_REDES (8 redes, 20 cols) + PAINEL_REDES (dashboard)
- V12 NAO tem nenhuma aba de redes (foram removidas)
- V13 NAO tem nenhuma aba de redes (apenas tabela inline AS:AZ no PROJECAO)

**Conclusao:** REDES_FRANQUIAS_v2 eh uma aba que PRECISA SER CRIADA como evolucao (v2) do SINALEIRO_REDES do V11, incorporando dados atualizados 2025, mais redes, e a estrutura da tabela de referencia do PROJECAO.

### Sobre os #REF!
Nenhum #REF! foi encontrado em nenhum dos arquivos analisados:
- V13 PROJECAO: 0 #REF!
- V12 SINALEIRO: 0 #REF!
- SINALEIRO_REDES_VITAO: 0 #REF! (ambas versoes)
- CONTROLE_FUNIL: 0 #REF!
- SINALEIRO_INTERNO_CONFIAVEL: 0 #REF!

**Hipoteses sobre os #REF! mencionados no roadmap:**
1. Os #REF! podem ter existido numa versao anterior que ja foi corrigida
2. Os #REF! podem aparecer ao abrir no Excel (openpyxl nao detecta #REF! de runtime)
3. Os #REF! podem surgir quando a aba REDES_FRANQUIAS_v2 for criada e referenciar dados que nao existem ainda

**Recomendacao:** Ao CRIAR a aba REDES_FRANQUIAS_v2, garantir que TODAS as formulas referenciem ranges corretos. Testar abertura no Excel apos criacao.

## Code Examples

### Exemplo 1: Remapear Clientes SEM GRUPO via SAP
```python
# Source: Padrao do projeto
import openpyxl

def remap_clients():
    # 1. Construir mapa SAP: CNPJ -> Grupo Chave
    sap_wb = openpyxl.load_workbook('01_SAP_CONSOLIDADO.xlsx', data_only=True)
    sap_ws = sap_wb['Cadastro Clientes SAP']
    cnpj_to_rede = {}
    for r in range(2, sap_ws.max_row + 1):
        cnpj = str(sap_ws.cell(row=r, column=5).value or '').replace('.','').replace('-','').replace('/','').strip()
        grupo = sap_ws.cell(row=r, column=43).value  # AQ
        if cnpj and grupo and '06 - SEM GRUPO' not in grupo:
            # Normalizar nome
            rede_nome = grupo.replace('06 - INTERNA - ', '')
            if rede_nome == 'TUDO EM GRAOS / VGA':
                rede_nome = 'TUDO EM GRAOS'
            cnpj_to_rede[cnpj] = rede_nome
    sap_wb.close()

    # 2. Aplicar no V13
    v13_wb = openpyxl.load_workbook('V13.xlsx', data_only=False)
    ws = v13_wb['PROJECAO ']
    updated = 0
    for r in range(4, ws.max_row + 1):
        cnpj = str(ws.cell(row=r, column=1).value or '').strip()
        rede = ws.cell(row=r, column=3).value
        if rede == 'SEM GRUPO' and cnpj in cnpj_to_rede:
            ws.cell(row=r, column=3).value = cnpj_to_rede[cnpj]
            updated += 1
    v13_wb.save('V13.xlsx')
    return updated  # Esperado: 11
```

### Exemplo 2: Criar Aba REDES_FRANQUIAS_v2
```python
# Source: Baseado na estrutura de SINALEIRO_REDES_VITAO.xlsx
def create_redes_tab(wb):
    ws = wb.create_sheet('REDES_FRANQUIAS_v2')

    # Titulo
    ws['A1'] = 'SINALEIRO DE PENETRACAO -- REDES E FRANQUIAS VITAO (v2)'
    ws['A2'] = 'Dados dinamicos | Atualiza automaticamente da aba PROJECAO'

    # Headers (row 3)
    headers = ['REDE', 'CONSULTOR', 'TOTAL LOJAS (SAP)', 'CLIENTES ATIVOS',
               'FAT. REAL (R$)', 'META 6M (R$)', 'SINALEIRO %', 'COR',
               'MATURIDADE', 'GAP (R$)', 'PENETRACAO %', 'ACAO RECOMENDADA',
               'PRIORIDADE']
    for i, h in enumerate(headers, 1):
        ws.cell(row=3, column=i).value = h

    # Dados por rede (row 4+)
    # FAT. REAL = SUMIFS do PROJECAO
    # =SUMIFS('PROJECAO '!Z$4:Z$537,'PROJECAO '!C$4:C$537,A4)
    # SINALEIRO % = FAT.REAL / META 6M
    # COR = IF baseado nos PARAMETROS
    return ws
```

### Exemplo 3: Atualizar Tabela AS:AZ com Dados Reais
```python
# Source: Padrao V13 existente
def update_ref_table(ws, rede_data):
    """
    rede_data: list of dicts com REDE, TOTAL_LOJAS, SINALEIRO, COR, etc.
    Escreve nas colunas AS:AZ, linhas 4-N
    """
    from openpyxl.utils import column_index_from_string
    cols = {
        'AS': 'rede_nome',
        'AT': 'total_lojas',
        'AU': 'sinaleiro_pct',
        'AV': 'cor',
        'AW': 'maturidade',
        'AX': 'acao',
        'AY': 'fat_real',
        'AZ': 'gap',
    }
    for i, rede in enumerate(rede_data):
        row = 4 + i
        for col_letter, key in cols.items():
            col_idx = column_index_from_string(col_letter)
            ws.cell(row=row, column=col_idx).value = rede[key]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| V11: 8 redes no SINALEIRO_REDES separado | V13: 12 redes inline em AS:AZ | Phase 1 (jan 2026) | Redes foram incorporadas no PROJECAO |
| Dados estáticos de penetracao (V11) | Dados devem ser dinamicos (V13 v2) | Phase 7 (fev 2026) | Formulas ao inves de valores hardcoded |
| Sem metas 6M por rede | SAP tem metas mensais por grupo chave | SAP 2026 | Metas 6M calculaveis: SUM(JAN:JUN) do Faturamento |
| 8 redes originais | 19 grupos-chave no SAP | SAP atualizado | Mais 7 redes nao presentes no V13 |

## Open Questions

1. **PARAMETROS: Benchmark R$525 ainda valido?**
   - What we know: V11 usava R$525/mes/loja benchmark, 11 meses de dados
   - What's unclear: Se o benchmark deve ser atualizado para 2025/2026
   - Recommendation: Manter R$525 como default, criar como parametro editavel na nova aba

2. **Redes extras do SAP (ESMERALDA, NOVA GERACAO, etc.) devem entrar?**
   - What we know: SAP tem 19 grupos-chave, V13 tem 12. Ha 7 extras: ARMAZEM FIT STORE, ESMERALDA, NOVA GERACAO, MERCOCENTRO, JARDIM DAS ERVAS, FEDERZONI, MIX VALI
   - What's unclear: Se essas redes menores devem ser incluidas no sinaleiro
   - Recommendation: Incluir TODAS as redes do SAP que tem meta > 0 (14 redes). Redes com meta=0 ficam de fora.

3. **394 clientes genuinamente SEM GRUPO -- o que fazer?**
   - What we know: 394 dos 405 SEM GRUPO nao tem rede no SAP
   - What's unclear: Se deveriam ser agrupados por regiao/consultor/tipo
   - Recommendation: Manter como "SEM GRUPO". A coluna C ja esta preenchida para todos 534, apenas 11 precisam correcao. A REDES_FRANQUIAS_v2 deve agregar os SEM GRUPO separadamente.

4. **Discrepancia "489 clientes" no roadmap vs 534 no V13**
   - What we know: V13 PROJECAO tem 534 clientes (rows 4-537)
   - What's unclear: De onde veio o numero 489
   - Recommendation: Usar 534 como numero correto. Documentar a discrepancia.

5. **O que eh "metas 6M"?**
   - What we know: SAP tem metas mensais (JAN-DEZ). "6M" = 6 meses (provavelmente JAN-JUN 2026)
   - What's unclear: Se eh JAN-JUN ou outro periodo de 6 meses
   - Recommendation: Usar JAN-JUN 2026 (primeiro semestre). Dados ja extraidos do SAP Faturamento.

## Sources

### Primary (HIGH confidence)
- V13 PROJECAO: `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` - estrutura, formulas, tabela AS:AZ, distribuicao REDE/GRUPO CHAVE
- 01_SAP_CONSOLIDADO.xlsx: `data/sources/sap/01_SAP_CONSOLIDADO.xlsx` - Cadastro Clientes SAP com CNPJ -> Grupo Chave (col AP/AQ), 1698 clientes, 19 grupos unicos
- BASE_SAP_META_PROJECAO_2026.xlsx: `data/sources/sap/BASE_SAP_META_PROJECAO_2026.xlsx` - Metas mensais por rede (aba Faturamento), Leads por rede, Positivacao
- SINALEIRO_REDES_VITAO.xlsx: `Desktop/CLAUDE CODE/SINALEIRO_REDES_VITAO.xlsx` - Template de referencia com 5 abas (PAINEL, PARAMETROS, SINALEIRO, PLANO_ACAO, CADENCIA)

### Secondary (MEDIUM confidence)
- CRM_VITAO360_v11_FINAL.xlsx: `data/sources/crm-versoes/v11-v12/CRM_VITAO360_v11_FINAL.xlsx` - SINALEIRO_REDES original (8 redes)
- REDES E FRANQUIAS 2026.xlsx: `Desktop/CLAUDE CODE/REDES E FRANQUAS 2026.xlsx` - 620 lojas em 6 redes com CNPJ
- CONTROLE_FUNIL_COMPLETO_FEV2026.xlsx: `Desktop/CLAUDE CODE/CONTROLE_FUNIL_COMPLETO_FEV2026 (em andamento(.xlsx` - 751 clientes, 7 redes, dados operacionais
- V12 COM_DADOS SINALEIRO: `data/sources/crm-versoes/v11-v12/CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` - 539 rows, mesma distribuicao de redes que V13

### Tertiary (LOW confidence)
- SPEC_FINAL_CRM_VITAO360_V3.md: Design original do CRM, Col 9 = "REDE / REGIONAL" na CARTEIRA
- ROADMAP.md: Mencao a REDES_FRANQUIAS_v2 e #REF! (nao confirmados na pratica)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - openpyxl padrao do projeto, sem dependencias novas
- Architecture: HIGH - estrutura de scripts/abas segue padroes estabelecidos em fases 1-6
- Dados de redes: HIGH - verificados diretamente em 8+ arquivos XLSX
- #REF! issue: MEDIUM - nenhum #REF! encontrado nos arquivos atuais; pode ser issue de runtime do Excel
- Metas 6M: HIGH - dados extraidos diretamente do SAP Faturamento com valores exatos
- REDES_FRANQUIAS_v2 design: MEDIUM - baseado em engenharia reversa do SINALEIRO_REDES V11, nao em spec explicita

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 dias - dados estaveis, estrutura nao muda frequentemente)
