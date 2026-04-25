# GAPS PARA EXCELÊNCIA MÁXIMA — CRM VITAO360

> Spec técnica para atingir 100%. Cada gap tem instruções precisas para o VSCode implementar.
> Gerado: 25/Abr/2026 | Atualizado: 25/Abr/2026 19:30 | GAP 2C completo (Sales Hunter XLSX → DB)

---

## STATUS ATUAL: ~55% (atualizado 25/Abr)

| Camada | Estado | Score |
|--------|--------|-------|
| Extração Deskrio | ✅ 24 dias rodando, 15.632 contatos | 100% |
| Extração Mercos | ⚠️ 17 dias de pastas mas dados escassos (só 2026-04-06 tem JSONs) | 40% |
| Extração Sales Hunter | ✅ Auth resolvida, 13/16 XLSX baixados (10MB+ dados SAP) | 85% |
| Banco de dados | ⚠️ SQLite com 2.695 clientes REAIS Mercos, vendas Mercos R$ 2.725K | 50% |
| Scripts de sync | ✅ sync_deskrio (797L), sync_mercos (682L), ingest_real (1055L) | 70% |
| Backend API | ⚠️ 17 routers, 22 pages, mas SEM dados SAP/Sales Hunter | 75% estrutura |
| Frontend | ⚠️ 22 páginas, 509+ testes, mas dados incompletos | 75% estrutura |
| Deploy | ❌ Indefinido (Render SQLite + Vercel) | 10% |

### O que JÁ FUNCIONA (não refazer):
- **2.695 clientes REAIS** no banco (Mercos), todos CNPJ 14 dígitos, tier=REAL
- **1.233 vendas REAIS** (Mercos), total R$ 2.725.649 — NOTA: é Mercos, NÃO SAP
- **clientes.faturamento_total** = R$ 2.102.420 (perto do baseline R$ 2.091.000)
- **21.345 log_interacoes** com Two-Base respeitada (sem coluna valor)
- **Sync scripts** existentes e substanciais (não são stubs)
- **13 relatórios Sales Hunter** XLSX baixados em `data/sales_hunter/2026-04-25/`

### O que FALTA (ordem de prioridade):
1. Script de ingestão Sales Hunter XLSX → DB (vendas SAP = fonte de verdade)
2. Rodar sync_deskrio no banco (24 dias de dados acumulados sem usar)
3. Migrar SQLite → PostgreSQL (Neon)
4. CNPJ crosswalk completo (3 fontes reconciliadas)
5. Frontend conectado a dados reais
6. Deploy produção

---

## GAP 1: SALES HUNTER AUTH ✅ RESOLVIDO (25/Abr/2026)

### Solução Implementada
Login via curl funciona. Bug era formato de data (YYYY-MM-DD, não DD/MM/YYYY)
e nomes de relatório longos (ex: `RelatorioDeFaturamentoPorCliente`).

**Spec completa:** `SALES_HUNTER_EXTRACTION_SPEC.md`

### Resultados da Primeira Extração
| Relatório | CWB | VV | Linhas (CWB) |
|-----------|-----|----|-------------|
| fat_cliente | 853KB ✅ | 853KB ✅ | 5.514 |
| fat_nf_det | 2.4MB ✅ | 2.4MB ✅ | ~15K |
| fat_produto | 35KB ✅ | 35KB ✅ | ~300 |
| fat_empresa | 6.7KB ✅ | 6.7KB ✅ | ~20 |
| debitos | 388KB ✅ | 388KB ✅ | ~3K |
| devolucao_cliente | 519KB ✅ | 184KB ✅ | ~2K |
| pedidos_produto | 2.0MB ✅ | 302 ❌ | ~8K |
| carteira | 500 ❌ | 500 ❌ | - |

**13/16 relatórios OK — 10MB+ de dados REAIS do SAP.**
Carteira e pedidos_vv precisam debug adicional (filtros especiais).

---

## GAP 2: INGESTÃO JSON → BANCO

### O Problema Central
24 dias de dados Deskrio extraídos. 6.429 clientes Mercos extraídos.
**NENHUM dado entrou no banco.** Os JSONs estão acumulando sem uso.

### Scripts Necessários (VSCode implementa)

#### 2A. `backend/scripts/ingest_deskrio.py`

**Fonte:** `data/deskrio/YYYY-MM-DD/contacts.json`
**Destino:** tabela `clientes` (upsert via CNPJ)

Mapeamento Deskrio → clientes:
```python
# Deskrio contacts NÃO têm CNPJ direto no JSON principal.
# CNPJ está nos campos extras (extrainfo).
# Precisa chamar GET /v1/api/custom-field/{number} por contato
# OU usar o dump de extrainfo_fields.json

MAPPING_CONTACTS = {
    # Deskrio field → DB field
    'id': None,  # referência interna Deskrio
    'name': 'nome_fantasia',  # ex: "QUINTAL DA NONA - LUCAS - SC"
    'number': 'telefone',  # WhatsApp: "554791940129"
    'email': 'email',
    'channel': None,  # sempre "whatsapp"
    'createdAt': None,  # data cadastro Deskrio
    'updatedAt': None,
    # Campos extras (via extrainfo):
    'extrainfo.CNPJ': 'cnpj',  # ← CHAVE PRIMÁRIA
    'extrainfo.Código SAP': 'codigo_cliente',
    'extrainfo.Estado': 'uf',
}
```

**Fonte:** `data/deskrio/YYYY-MM-DD/tickets.json`
**Destino:** tabela `log_interacoes`

```python
MAPPING_TICKETS = {
    'id': None,  # referência ticket
    'contact.name': None,  # nome do contato
    'contact.id': None,  # ID do contato → buscar CNPJ
    'status': 'resultado',  # open/closed → Ativo/Concluido
    'origin': 'tipo_contato',  # "Receptivo"/"Ativo" → "WHATSAPP"
    'createdAt': 'data_interacao',
    'lastMessage': 'descricao',  # última mensagem
    'userId': 'consultor',  # 4400002=Daiane, 4400030=Larissa
}

# REGRA TWO-BASE: tickets Deskrio = LOG → R$ 0.00 SEMPRE
# NUNCA colocar valor monetário em log_interacoes
```

**Fonte:** `data/deskrio/YYYY-MM-DD/kanban_cards_20.json`
**Destino:** nova tabela `pipeline_cards` ou campo `estagio_funil` em clientes

```python
MAPPING_KANBAN = {
    'name': None,  # nome do card (empresa)
    'description': None,  # notas
    'kanbanColumnId': 'estagio_funil',  # ID coluna → nome estágio
    'responsibleUser.name': 'consultor',
    'contact.id': None,  # → buscar CNPJ
    'value': None,  # valor do deal (pode ser R$ 0)
    'expectedAt': None,  # data esperada
}

# Colunas do Board 20 (Vendas Vitao):
KANBAN_COLUMNS = {
    387: 'INICIO DE CONTATO',
    # ... (buscar via GET /kanban-columns/20)
}
```

#### 2B. `backend/scripts/ingest_mercos.py`

**Fonte:** `data/mercos_clientes_completo.json`
**Destino:** tabela `clientes` (upsert via CNPJ)

```python
MAPPING_MERCOS = {
    'razao_social': 'razao_social',
    'nome_fantasia': 'nome_fantasia',
    'cnpj': 'cnpj',  # NORMALIZAR: "31.983.992/0001-48" → "31983992000148"
    'inscricao_estadual': None,
    'endereco': None,
    'bairro': None,
    'cidade': 'cidade',
    'estado': 'uf',
    'cep': None,
    'segmento_nome': 'tipo_cliente',  # "Produtos Naturais"
    'rede_nome': 'rede_regional',
    'emails[0]': 'email',
    'telefones[0]': 'telefone',
    'bloqueado': 'situacao',  # "Não" → "ATIVO", "Sim" → "INATIVO"
    'colaboradores': 'consultor',  # DE-PARA vendedores
    'data_cadastro': 'created_at',
}

# DE-PARA VENDEDORES (do CLAUDE.md):
VENDEDOR_MAP = {
    'Central - Daiane': 'DAIANE',
    'Daiane': 'DAIANE',
    'Larissa Padilha': 'LARISSA',
    'Larissa': 'LARISSA',
    'Mais Granel': 'LARISSA',
    'Rodrigo': 'LARISSA',
    'Manu Ditzel': 'MANU',
    'Manu': 'MANU',
    'Julio Gadret': 'JULIO',
    'Leandro Garcia': None,  # admin, não vendedor
}
```

#### 2C. `scripts/ingest_sales_hunter.py` ← SPEC COMPLETA (25/Abr/2026)

> **CONTEXTO:** Sales Hunter = interface web do SAP VITAO. Os XLSX baixados via curl
> são relatórios do SAP real — fonte de verdade para faturamento.
> O `ingest_real_data.py` atual usa um `01_SAP_CONSOLIDADO.xlsx` estático (dados 2025).
> Este novo script usa os XLSX diários baixados em `data/sales_hunter/`.

**Fonte:** `data/sales_hunter/YYYY-MM-DD/morning/*.xlsx`
**Destino:** tabelas `clientes`, `vendas`, `venda_itens`, `produtos`, `debitos_clientes` (NOVA)
**Formato nomes:** `{tipo}_{empresa}_all_{data}_{hora}.xlsx`
**Empresas:** CWB (12=Curitiba) e VV (13=Vila Velha) — PROCESSAR AMBAS, UNIFICAR

---

##### 2C.1 — fat_cliente (PRINCIPAL — faturamento por cliente)

**Arquivo:** `fat_cliente_cwb_all_*.xlsx` + `fat_cliente_vv_all_*.xlsx`
**Rows:** ~5.514 por empresa | **Cols:** 30
**Destino:** tabela `clientes` (upsert) + tabela `vendas` (insert)

```python
# ============================================
# SCHEMA REAL DO XLSX (verificado 25/Abr/2026)
# ============================================
FAT_CLIENTE_COLS = {
    1:  'cod_cliente',        # int: 2000000107 (código SAP do cliente)
    2:  'cliente',            # str: "MEGAMIX DISTRIBUIDORA LTDA"
    3:  'cpf_cnpj',           # str: "05549422000134" ← CHAVE PRIMÁRIA
    4:  'grupo',              # str: "06 - INDIRETO - MEGAMIX - CASCAVEL"
    5:  'canal_venda',        # str: "31 - IN - DISTR. VAREJO"
    6:  'lista_preco',        # str: "42 - DISTRIBUIDOR NIVEL 3"
    7:  'desc_comercial',     # str: "0,00%"
    8:  'desc_financeiro',    # str: "0,00%"
    9:  'estado',             # str: "Paraná" ← CONVERTER p/ UF (PR, SP, SC...)
    10: 'cidade',             # str: "Cascavel"
    11: 'bairro',             # str
    12: 'endereco',           # str
    13: 'cep',                # int/str: 85807970
    14: 'venda_mes',          # float: 340855.56 ← VENDA do mês atual
    15: 'devolucao_mes',      # float: 0
    16: 'bonificacao_mes',    # float: -35662.33
    17: 'faturado_mes',       # float: 340855.56 ← VENDA - DEVOL + BONIF
    18: 'pct_devolucao_mes',  # str: "0,00%"
    19: 'pct_bonif_mes',      # str: "-10,46%"
    20: 'total_venda',        # float: 340855.56 ← ACUMULADO período
    21: 'total_devolucao',    # float
    22: 'total_bonificacao',  # float
    23: 'total_faturado',     # float ← ESTE É O FATURAMENTO TOTAL
    24: 'media_faturamento',  # float
    25: 'pct_devolucao',      # str
    26: 'pct_bonificacao',    # str
    27: 'cod_sap_zr',         # int ou None
    28: 'razao_social_zr',    # str ou None
    29: 'cod_sap_zx',         # int ou None
    30: 'razao_social_zx',    # str ou None
}

# MAPEAMENTO fat_cliente → tabela clientes (UPSERT por CNPJ)
MAPPING_FAT_CLIENTE_TO_CLIENTES = {
    'cpf_cnpj':       'cnpj',              # normalize_cnpj()
    'cliente':        'nome_fantasia',
    'cod_cliente':    'codigo_cliente',     # str(val)
    'grupo':          'tipo_cliente_sap',   # "06 - INDIRETO - MEGAMIX"
    'canal_venda':    'tipo_cliente',       # extrair parte antes do " - "
    'estado':         'uf',                 # CONVERTER: "Paraná" → "PR"
    'cidade':         'cidade',
    'total_faturado': 'faturamento_total',  # ESTE É O VALOR DE VERDADE
    'media_faturamento': None,              # calcular depois (faturamento/meses)
}

# MAPEAMENTO fat_cliente → tabela vendas (INSERT por mês)
# Cada row com venda_mes > 0 vira um registro em vendas
MAPPING_FAT_CLIENTE_TO_VENDAS = {
    'cpf_cnpj':    'cnpj',          # normalize_cnpj()
    'faturado_mes': 'valor_pedido', # valor do mês ← TWO-BASE: é VENDA, tem R$
    # consultor: não vem no fat_cliente — usar Mercos/DE-PARA
    # mes_referencia: extrair do período do relatório (ex: "2026-04")
    # fonte: 'SAP'
    # classificacao_3tier: 'REAL'
}

# ESTADOS BRASILEIROS — DE-PARA nome → sigla
ESTADOS_DEPARA = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM',
    'Bahia': 'BA', 'Ceará': 'CE', 'Distrito Federal': 'DF',
    'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA',
    'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG',
    'Pará': 'PA', 'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE',
    'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 'Rio Grande do Norte': 'RN',
    'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR',
    'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE',
    'Tocantins': 'TO',
}
```

**REGRAS CRÍTICAS fat_cliente:**
1. CPF/CNPJ col 3 pode ser CPF (11 dígitos) → normalizar para 14 com zfill
2. Se CPF (pessoa física), CNPJ fica como "000" + CPF (11 dígitos) = 14
3. Colunas 14-19 = dados do MÊS ATUAL (abril/2026 na extração de 25/Abr)
4. Colunas 20-26 = TOTAIS ACUMULADOS no período do relatório
5. Col 23 (total_faturado) = FONTE DE VERDADE para faturamento_total
6. CWB e VV são empresas diferentes — SOMAR faturamento se mesmo CNPJ em ambas
7. Muitos rows têm faturamento = 0 (clientes inativos) → incluir com situacao="INATIVO"
8. `situacao` derivar: faturado_mes > 0 → "ATIVO", senão → "INATIVO"

---

##### 2C.2 — fat_nf_det (notas fiscais detalhadas)

**Arquivo:** `fat_nf_det_cwb_all_*.xlsx` + `fat_nf_det_vv_all_*.xlsx`
**Rows:** ~24.792 por empresa | **Cols:** 26
**Destino:** tabela `vendas` + `venda_itens` + `produtos`

```python
FAT_NF_DET_COLS = {
    1:  'cod_material',       # int: 300019992
    2:  'material',           # str: "CHOC COOKIES CREAM ZERO 70G D04X06 C24"
    3:  'peso_bruto_kg',      # float: 1.95
    4:  'cod_num_item',       # str: "000010"
    5:  'quantidade',         # float: 0.04
    6:  'valor_nfe',          # float: 24.89 ← TWO-BASE: VENDA
    7:  'categoria',          # str: "CHOCOLATES"
    8:  'subcategoria',       # str: "CHOCOLATES"
    9:  'um',                 # str: "Caixa"
    10: 'nro_nfe',            # str: "000460892-0"
    11: 'data_emissao',       # str: "01/04/2026" (DD/MM/YYYY)
    12: 'tipo_documento',     # str: "Venda (F2B)" / "Devolução" / "Bonificação"
    13: 'cod_pedido',         # str: "0001231143"
    14: 'cod_cliente',        # int: 1000258479
    15: 'cliente',            # str: "IGOR MONTEIRO"
    16: 'cpf_cnpj',           # int(!) ou str: 54667748800 ← NORMALIZAR
    17: 'lista_preco',        # str: "11 - E-COMMERCE"
    18: 'desc_comercial',     # str: "0,00%"
    19: 'desc_financeiro',    # str: "0,00%"
    20: 'cep',                # int: 12420680
    21: 'cidade',             # str: "Pindamonhangaba"
    22: 'estado',             # str: "São Paulo"
    23: 'cod_sap_zr',         # int ou None
    24: 'razao_social_zr',    # str
    25: 'cod_sap_zx',         # int ou None
    26: 'razao_social_zx',    # str
}

# MAPEAMENTO fat_nf_det → vendas (1 NF = 1 venda)
MAPPING_NF_TO_VENDAS = {
    'cpf_cnpj':       'cnpj',           # normalize_cnpj()
    'data_emissao':   'data_pedido',     # parse DD/MM/YYYY → date
    'cod_pedido':     'numero_pedido',
    'valor_nfe':      'valor_pedido',    # ← TWO-BASE: VENDA, tem R$
    # consultor: buscar na tabela clientes pelo CNPJ
    # fonte: 'SAP'
    # classificacao_3tier: 'REAL'
    # mes_referencia: extrair de data_emissao (YYYY-MM)
}

# MAPEAMENTO fat_nf_det → produtos (UPSERT por codigo)
MAPPING_NF_TO_PRODUTOS = {
    'cod_material': 'codigo',
    'material':     'nome',
    'categoria':    'categoria',
    'um':           'unidade',
    'peso_bruto_kg': 'peso',
}

# MAPEAMENTO fat_nf_det → venda_itens
MAPPING_NF_TO_ITENS = {
    # venda_id: FK → vendas.id (buscar pelo numero_pedido)
    # produto_id: FK → produtos.id (buscar pelo codigo)
    'quantidade':  'quantidade',
    'valor_nfe':   'valor_total',
    # preco_unitario: calcular valor_nfe / quantidade
}
```

**REGRAS CRÍTICAS fat_nf_det:**
1. Col 16 (cpf_cnpj) vem como INT — CONVERTER para string ANTES de normalizar
2. Col 11 (data_emissao) = formato DD/MM/YYYY — parsear com strptime
3. Col 12 (tipo_documento): filtrar apenas "Venda (F2B)" para vendas. "Devolução" e "Bonificação" = registros separados
4. DEDUPLICAR: agrupar por cod_pedido para não criar vendas duplicadas
5. Cada NF pode ter múltiplos itens (mesmo cod_pedido, diferentes cod_material)
6. PRIORIDADE: usar fat_nf_det para vendas detalhadas, fat_cliente para totais de controle
7. VALIDAÇÃO CRUZADA: soma de fat_nf_det por CNPJ ≈ total_faturado de fat_cliente

---

##### 2C.3 — debitos (inadimplência)

**Arquivo:** `debitos_cwb_all_*.xlsx` + `debitos_vv_all_*.xlsx`
**Rows:** ~6.385 por empresa | **Cols:** 10
**Destino:** NOVA tabela `debitos_clientes`

```python
DEBITOS_COLS = {
    1:  'cod_cliente',     # int: 2000000024
    2:  'cliente',         # str: "B&B DISTRIBUIDORA COMERCIAL BRASIL LTDA"
    3:  'documento',       # int/str: 13272892000121 ← É O CNPJ!
    4:  'cod_pedido',      # int: 637607
    5:  'nro_nfe',         # str: "000245627-0"
    6:  'parcela',         # str: "001"
    7:  'data_lancamento', # str: "24/04/2026" (DD/MM/YYYY)
    8:  'data_vencimento', # str: "05/09/2023" ← PODE SER MUITO ANTIGA
    9:  'data_pagamento',  # str ou None (None = NÃO PAGO = DEVENDO)
    10: 'valor',           # float: 76884.39 ← TWO-BASE: VENDA (é dívida)
}

# NOVA TABELA (VSCode deve criar via Alembic)
CREATE_DEBITOS = """
CREATE TABLE debitos_clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj VARCHAR(14) NOT NULL,
    cod_pedido VARCHAR(50),
    nro_nfe VARCHAR(50),
    parcela VARCHAR(5),
    data_lancamento DATE,
    data_vencimento DATE,
    data_pagamento DATE,          -- NULL = não pago
    valor FLOAT NOT NULL,
    dias_atraso INTEGER,          -- CALCULADO: hoje - data_vencimento
    status VARCHAR(20),           -- 'PAGO', 'VENCIDO', 'A_VENCER'
    fonte VARCHAR(20) DEFAULT 'SAP',
    classificacao_3tier VARCHAR(15) DEFAULT 'REAL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_debitos_cnpj ON debitos_clientes(cnpj);
CREATE INDEX idx_debitos_status ON debitos_clientes(status);
"""

# MAPEAMENTO debitos → debitos_clientes
MAPPING_DEBITOS = {
    'documento':       'cnpj',              # normalize_cnpj(str(val))
    'cod_pedido':      'cod_pedido',        # str(val)
    'nro_nfe':         'nro_nfe',
    'parcela':         'parcela',
    'data_lancamento': 'data_lancamento',   # parse DD/MM/YYYY
    'data_vencimento': 'data_vencimento',   # parse DD/MM/YYYY
    'data_pagamento':  'data_pagamento',    # parse DD/MM/YYYY ou None
    'valor':           'valor',
    # dias_atraso: calcular (date.today() - data_vencimento).days se não pago
    # status: 'PAGO' se data_pagamento, 'VENCIDO' se vencimento < hoje, 'A_VENCER'
}
```

**REGRAS CRÍTICAS debitos:**
1. Col 3 (documento) É O CNPJ do cliente — NÃO é número de documento
2. Col 9 (data_pagamento) = None significa NÃO PAGO → cliente devendo
3. `dias_atraso` = (hoje - data_vencimento).days — pode ser MUITO alto (ex: 2023)
4. `status` derivar: pago? → "PAGO"; vencido < hoje? → "VENCIDO"; futuro → "A_VENCER"
5. Adicionar campo `total_debitos` na tabela `clientes` (SUM de débitos VENCIDOS)
6. IMPORTANTE para Sinaleiro: clientes com débitos antigos = bandeira vermelha

---

##### 2C.4 — devolucao_cliente (devoluções por cliente)

**Arquivo:** `devolucao_cliente_cwb_all_*.xlsx` + `devolucao_cliente_vv_all_*.xlsx`
**Rows:** ~5.514 por empresa | **Cols:** 21
**Destino:** enriquece tabela `clientes` (campos de devolução)

```python
DEVOLUCAO_COLS = {
    1:  'cod_cliente',       # int
    2:  'cliente',           # str
    3:  'cpf_cnpj',          # str: "05549422000134"
    4:  'canal_venda',       # str
    5:  'lista_preco',       # str
    6:  'desc_comercial',    # str %
    7:  'desc_financeiro',   # str %
    8:  'estado',            # str (nome completo)
    9:  'cidade',            # str
    10: 'venda_mes',         # float
    11: 'devol_parcial_mes', # float (REB)
    12: 'devol_total_mes',   # float (ROB)
    13: 'bonificacao_mes',   # float
    14: 'faturado_mes',      # float
    15: 'pct_devolucao_mes', # str %
    16: 'total_venda',       # float
    17: 'total_devol_parcial', # float (REB acumulado)
    18: 'total_devol_total',   # float (ROB acumulado)
    19: 'total_bonificacao',   # float
    20: 'total_faturado',      # float
    21: 'pct_devolucao',       # str %
}

# ENRIQUECE tabela clientes com métricas de devolução
# Não cria registros novos — apenas UPDATE onde CNPJ existe
# Campos sugeridos para adicionar em clientes (ou tabela separada):
#   pct_devolucao FLOAT      — percentual de devolução acumulado
#   total_devolucao FLOAT    — valor total devolvido
#   risco_devolucao VARCHAR  — 'BAIXO' (<5%), 'MEDIO' (5-15%), 'ALTO' (>15%)
```

**REGRAS CRÍTICAS devolucao:**
1. Mesma estrutura de clientes que fat_cliente — usar CNPJ para cruzar
2. Col 21 (pct_devolucao) = métrica de qualidade do cliente
3. Devoluções ALTAS (>15%) = alerta no Sinaleiro
4. Dados complementam fat_cliente — NÃO duplicar o faturamento

---

##### 2C.5 — fat_produto (faturamento por produto)

**Arquivo:** `fat_produto_cwb_all_*.xlsx` + `fat_produto_vv_all_*.xlsx`
**Rows:** ~275 por empresa | **Cols:** 20
**Destino:** tabela `produtos` (upsert por codigo)

```python
FAT_PRODUTO_COLS = {
    1:  'cod_material',        # int: 300000002
    2:  'material',            # str: "ACUCAR MASCAVO 500g F12"
    3:  'categoria',           # str: "REEMBALADOS"
    4:  'subcategoria',        # str: "AÇÚCAR"
    5:  'um',                  # str: "Fardo"
    6:  'peso_bruto_kg',       # float: 6
    7:  'qtd_mes',             # float: 965.17
    8:  'venda_mes',           # float: 66675.06
    9:  'devolucao_mes',       # float
    10: 'bonificacao_mes',     # float
    11: 'faturado_mes',        # float
    12: 'pct_devolucao_mes',   # str
    13: 'pct_bonif_mes',       # str
    14: 'total_qtd',           # float
    15: 'total_venda',         # float
    16: 'total_devolucao',     # float
    17: 'total_bonificacao',   # float
    18: 'total_faturado',      # float ← faturamento total do produto
    19: 'pct_devolucao_total', # str
    20: 'pct_bonif_total',     # str
}

# MAPEAMENTO → produtos
MAPPING_FAT_PRODUTO = {
    'cod_material': 'codigo',      # str(val)
    'material':     'nome',
    'categoria':    'categoria',   # SAP > Mercos para categoria
    'um':           'unidade',
    'peso_bruto_kg': 'peso',
    # ativo: True (se tem faturamento no mês)
}
```

---

##### 2C.6 — fat_empresa (faturamento por empresa — CONTROLE)

**Arquivo:** `fat_empresa_cwb_all_*.xlsx` + `fat_empresa_vv_all_*.xlsx`
**Rows:** 2 (1 header + 1 data) | **Cols:** 12
**Destino:** NENHUMA tabela — usado apenas para VALIDAÇÃO

```python
FAT_EMPRESA_COLS = {
    1:  'empresa',           # str: "VITAO - Curitiba"
    2:  'centro',            # int: 7000
    3:  'venda_mes',         # float: 5872092.97
    7:  'faturado_mes',      # float: 5473659.87
    8:  'total_venda',       # float: 5872092.97
    12: 'total_faturado',    # float: 5358467.99
}

# VALIDAÇÃO: SUM(fat_cliente.total_faturado) deve = fat_empresa.total_faturado
# Se divergir > 0.5% → PARAR e investigar (R9)
```

---

##### 2C.7 — pedidos_produto (pedidos detalhados)

**Arquivo:** `pedidos_produto_cwb_all_*.xlsx` (VV falha com 302)
**Rows:** ~23.782 | **Cols:** 26
**Destino:** tabela `vendas` (enriquece com vendedor) + `venda_itens`

```python
PEDIDOS_PRODUTO_COLS = {
    1:  'numero_pedido_cliente', # str: "INFLUENCER"
    2:  'numero_pedido_sap',     # str: "0001231531" ← cruza com fat_nf_det
    3:  'tipo_pedido',           # str: "ZRBD"
    4:  'data_criacao',          # str: "06/04/2026" (DD/MM/YYYY)
    5:  'status_pedido',         # str: "Pedido faturado"
    6:  'cliente_razao_social',  # str
    7:  'cliente_documento',     # int(!): 12492242927 ← CNPJ/CPF como número
    8:  'cliente_grupo',         # str: "06 - NAO APLICAVEL"
    9:  'vendedor',              # str: "ZR - NAO APLICAVEL" ← TEM VENDEDOR!
    10: 'condicao_pagamento',    # str: "A VISTA"
    11: 'tipo_frete',            # str: "CIF"
    12: 'empresa',               # str: "VITAO - Curitiba"
    13: 'produto_descricao',     # str
    14: 'produto_peso',          # float
    15: 'produto_codigo',        # str: "000000000300004345" ← LONG CODE
    16: 'recusa_codigo',         # int ou None
    17: 'recusa_descricao',      # str ou None
    18: 'quantidade',            # int: 1
    19: 'ipi',                   # float: 0
    20: 'unitario',              # float: 0.01 ← preço unitário
    21: 'desconto_acordado',     # float ou None
    22: 'desconto_comercial',    # float: 0
    23: 'numero_item',           # str: "000010"
    24: 'prazo_entrega',         # str: "2026-04-06 00:00:00" (YYYY-MM-DD!)
    25: 'grupo',                 # str: "REEMBALADOS"
    26: 'sub_grupo',             # str: "FARINHAS E FIBRAS"
}

# VALOR PRINCIPAL: col 9 (vendedor) permite mapear consultor
# Cruza com fat_nf_det via numero_pedido_sap = cod_pedido
# Enriquece vendas com campo consultor que não vem nos outros relatórios
```

**REGRAS CRÍTICAS pedidos_produto:**
1. Col 7 (cliente_documento) vem como INT — converter para str + normalize_cnpj
2. Col 9 (vendedor) = primeiro relatório que TEM vendedor SAP → aplicar DE-PARA
3. Col 15 (produto_codigo) = código longo "000000000300004345" → strip zeros à esquerda
4. Col 24 (prazo_entrega) = formato YYYY-MM-DD (diferente dos outros!)
5. Pedidos VV não baixa (HTTP 302) → usar apenas CWB por enquanto

---

##### 2C.8 — LÓGICA DE EXECUÇÃO DO SCRIPT

```python
#!/usr/bin/env python3
"""
ingest_sales_hunter.py — Ingestão de relatórios Sales Hunter (SAP) no CRM VITAO360
==================================================================================
Lê XLSX de data/sales_hunter/YYYY-MM-DD/morning/ e alimenta o banco.

REGRAS SAGRADAS:
  R1  — Two-Base: fat_* = VENDA (tem R$). NUNCA misturar com LOG.
  R2  — CNPJ = string 14 dígitos, zero-padded, NUNCA float/int
  R5  — classificacao_3tier = 'REAL' (dados diretos do SAP)
  R8  — NUNCA fabricar dados
  R11 — Idempotente: pode rodar N vezes sem duplicar

FASES DE EXECUÇÃO (nesta ordem):
  Phase 1 — Descobrir último diretório de extração
  Phase 2 — fat_produto → upsert produtos (275 SKUs por empresa)
  Phase 3 — fat_cliente CWB+VV → upsert clientes (dados cadastrais + faturamento)
  Phase 4 — fat_nf_det CWB+VV → insert vendas + venda_itens (notas fiscais)
  Phase 5 — pedidos_produto CWB → enriquece vendas com vendedor
  Phase 6 — debitos CWB+VV → insert debitos_clientes
  Phase 7 — devolucao CWB+VV → update clientes (métricas devolução)
  Phase 8 — fat_empresa → VALIDAÇÃO (soma confere?)
  Phase 9 — Curva ABC (recalcular com dados SAP)
  Phase 10 — Relatório de execução

VALIDAÇÃO FINAL:
  - SUM(clientes.faturamento_total) ≈ R$ 2.091.000 (tolerância 0.5%)
  - 0 CNPJs como float
  - 0 duplicatas de CNPJ
  - Classificação 3-tier = REAL em todos os registros SAP

USO:
  python scripts/ingest_sales_hunter.py                    # último dia disponível
  python scripts/ingest_sales_hunter.py --date 2026-04-25  # dia específico
  python scripts/ingest_sales_hunter.py --dry-run           # só mostra o que faria
"""

# ARGUMENTOS CLI:
#   --date YYYY-MM-DD   Dia específico (default: último disponível)
#   --dry-run            Não grava no banco, só imprime
#   --skip-validation    Pula validação fat_empresa (NÃO RECOMENDADO)
#   --db-path PATH       Caminho do banco (default: data/crm_vitao360.db)

import argparse
import glob
import logging
import os
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

import openpyxl

# ... (implementação completa pelo VSCode)
```

##### 2C.9 — CUIDADOS ESPECIAIS

1. **CPF vs CNPJ:** fat_nf_det e pedidos têm CPFs (11 dígitos) misturados com CNPJs (14). 
   Normalizar AMBOS para 14 dígitos: `str(val).zfill(14)`. CPF "54667748800" → "00054667748800"
   
2. **Dados duplicados CWB+VV:** Mesmo CNPJ pode aparecer em CWB e VV (multinacional com filiais em PR e ES).
   fat_cliente: SOMAR faturamento. fat_nf_det: manter como vendas separadas.
   
3. **Idempotência:** Script DEVE poder rodar múltiplas vezes sem duplicar.
   - clientes: UPSERT por CNPJ
   - vendas: UPSERT por (cnpj, numero_pedido, data_pedido)
   - produtos: UPSERT por codigo
   - debitos: UPSERT por (cnpj, nro_nfe, parcela)
   
4. **Performance:** fat_nf_det tem ~25K rows × 2 empresas = ~50K registros.
   Usar batch insert com transação, não row-by-row.
   
5. **Período do relatório:** Os dados de Abr/2026 cobrem 01/Abr a 25/Abr (até a data da extração).
   O campo `mes_referencia` deve ser "2026-04" para vendas deste período.

6. **RELAÇÃO COM ingest_real_data.py:** O script existente usa `01_SAP_CONSOLIDADO.xlsx` (dados 2025).
   Este novo script usa dados DIÁRIOS do Sales Hunter (2026+). 
   NÃO DELETAR o antigo — ele serve de fallback e referência.
   Hierarquia: Sales Hunter (mais recente) > SAP Consolidado > Mercos

### Lógica de Upsert

```python
import re

def normalize_cnpj(val):
    """R5: CNPJ 14 dígitos, string, zero-padded"""
    if val is None:
        return None
    cleaned = re.sub(r'\D', '', str(val))
    if len(cleaned) == 0:
        return None
    return cleaned.zfill(14)

def upsert_cliente(db, data, fonte):
    """Upsert em clientes via CNPJ como chave primária"""
    cnpj = normalize_cnpj(data.get('cnpj'))
    if not cnpj:
        return None  # sem CNPJ = não insere
    
    existing = db.query(Cliente).filter(Cliente.cnpj == cnpj).first()
    if existing:
        # Atualizar campos que vieram desta fonte
        # Mercos = dados cadastrais (nome, cidade, uf)
        # SAP = dados financeiros (faturamento, classificação)
        # Deskrio = dados de atendimento (telefone, email WhatsApp)
        for key, val in data.items():
            if val is not None:
                setattr(existing, key, val)
        existing.updated_at = datetime.now()
    else:
        cliente = Cliente(**data)
        cliente.classificacao_3tier = 'REAL'
        db.add(cliente)
```

### Ordem de Execução

1. **Mercos primeiro** (dados cadastrais mais ricos: CNPJ, razão social, cidade, UF)
2. **SAP/Sales Hunter segundo** (enriquece com faturamento, classificação)
3. **Deskrio por último** (enriquece com telefone WhatsApp, status atendimento)

Cada fonte tem prioridade diferente por campo:
- `nome_fantasia`: Mercos > SAP > Deskrio
- `faturamento_total`: SAP (ÚNICA fonte válida)
- `telefone`: Deskrio (WhatsApp direto)
- `situacao`: SAP (ATIVO/INATIVO baseado em faturamento)
- `consultor`: Mercos (colaboradores) > SAP

---

## GAP 3: SQLITE → POSTGRESQL (Neon)

### Provider Escolhido: Neon

### Passos

1. **Criar projeto Neon** (https://console.neon.tech)
   - Projeto: `crm-vitao360`
   - Região: São Paulo (sa-east-1)
   - Banco: `crm_vitao360`

2. **Obter connection string**
   ```
   DATABASE_URL=postgresql://user:pass@ep-xxx.sa-east-1.aws.neon.tech/crm_vitao360?sslmode=require
   ```

3. **Atualizar backend**
   ```python
   # backend/app/database.py
   # Trocar:
   #   engine = create_engine("sqlite:///data/crm_vitao360.db")
   # Por:
   #   engine = create_engine(os.environ["DATABASE_URL"])
   ```

4. **requirements.txt** — adicionar `psycopg2-binary`

5. **Rodar Alembic migration**
   ```bash
   alembic upgrade head
   ```

6. **Seed data** — rodar scripts de ingestão

7. **Env vars** — configurar em Render + .env local

### Cuidados
- SQLite usa `DATETIME`, PostgreSQL usa `TIMESTAMP`
- SQLite `BOOLEAN` é `INTEGER`, PostgreSQL tem `BOOLEAN` nativo
- `VARCHAR(14)` para CNPJ funciona igual
- Alembic deve gerar migration automática

---

## GAP 4: CRUZAMENTO CNPJ 3 FONTES

### O Bridge

```
MERCOS (cnpj formatado)  ──┐
                           ├──→ CNPJ normalizado (14 dígitos) ──→ tabela clientes
SAP/SALES HUNTER (cnpj)  ──┤
                           │
DESKRIO (extrainfo.CNPJ) ──┘
```

### Tabela Bridge (opcional)

```sql
CREATE TABLE cnpj_bridge (
    cnpj VARCHAR(14) PRIMARY KEY,
    mercos_id INTEGER,       -- ID do cliente no Mercos
    deskrio_contact_id INTEGER, -- ID do contato no Deskrio
    sap_codigo VARCHAR(20),   -- Código SAP
    deskrio_phone VARCHAR(20), -- WhatsApp number
    sources TEXT,             -- "mercos,deskrio,sap"
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Cobertura Estimada

| Fonte | Total | Com CNPJ | % |
|-------|-------|----------|---|
| Mercos | 6.429 | 6.429 | 100% (campo obrigatório) |
| SAP/Sales Hunter | ~2.695 | ~2.695 | ~100% |
| Deskrio | 15.632 | ~4.800 | ~31% (via extrainfo) |

### Reconciliação

```python
def reconcile_sources():
    """Cruza as 3 fontes via CNPJ e enriquece cada cliente"""
    
    # 1. Mercos como base (6.429 clientes com dados cadastrais)
    mercos_map = {normalize_cnpj(c['cnpj']): c for c in mercos_clients}
    
    # 2. SAP enriquece com faturamento
    for row in sap_data:
        cnpj = normalize_cnpj(row['cnpj'])
        if cnpj in mercos_map:
            mercos_map[cnpj]['faturamento'] = row['valor']
        else:
            # Cliente SAP sem Mercos → criar
            mercos_map[cnpj] = {'cnpj': cnpj, 'fonte': 'SAP', ...}
    
    # 3. Deskrio enriquece com WhatsApp
    for contact in deskrio_contacts:
        cnpj = get_cnpj_from_extrainfo(contact)
        if cnpj and cnpj in mercos_map:
            mercos_map[cnpj]['telefone_whatsapp'] = contact['number']
            mercos_map[cnpj]['deskrio_id'] = contact['id']
    
    # 4. Resultado: visão 360° por CNPJ
    return mercos_map
```

---

## GAP 5: FRONTEND COM DADOS REAIS

### 22 Páginas — Checklist de Validação

| Página | Endpoint Backend | Dado Atual | Precisa |
|--------|-----------------|------------|---------|
| / (Dashboard) | /api/dashboard/kpis | SEED | Dados reais de vendas/clientes |
| /carteira | /api/clientes | SEED 2.695 | Mercos+SAP (6.429+) |
| /pipeline | /api/pipeline | SEED | Kanban Deskrio real |
| /agenda | /api/agenda | SEED 340 | Agenda real dos vendedores |
| /pedidos | /api/vendas | SEED 1.233 | Pedidos Mercos reais |
| /sinaleiro | /api/sinaleiro/kpis | SEED | Score calculado sobre dados reais |
| /ia | /api/ia/* | Graceful degradation | Precisa dados reais + modelo |
| /inbox | ? | ? | Mensagens Deskrio reais |
| /projecao | /api/projecao | SEED | Projeção baseada em SAP real |
| /relatorios | /api/relatorios | SEED | Relatórios SAP reais |
| /produtos | /api/produtos | SEED 242 | Catálogo SAP real |
| /redes | /api/redes | SEED 17 | Redes Mercos reais |
| /rnc | /api/rnc | 0 registros | RNC real (quando operacional) |
| /tarefas | ? | ? | Tarefas Mercos |
| /atualizacoes | ? | ? | Feed de atividades |
| /admin/import | /api/import | 0 jobs | Importação funcionando |
| /admin/motor | /api/motor | SEED 92 regras | Motor scoring real |
| /admin/pipeline | ? | ? | Config pipeline |
| /admin/redistribuir | ? | ? | Redistribuição carteira |
| /admin/usuarios | /api/auth | SEED 5 | Usuários reais |
| /login | /api/auth/login | Funciona | OK |
| /docs | N/A | Estático | OK |

### Prioridade de Validação

1. **Dashboard** — é a primeira coisa que o CEO vê
2. **Carteira** — é onde o vendedor trabalha todo dia
3. **Pipeline** — funil de vendas visual
4. **Pedidos** — acompanhamento de vendas
5. **Sinaleiro** — alertas inteligentes

---

## GAP 6: DEPLOY PRODUÇÃO

### Stack Final

| Componente | Provider | Tier | Custo |
|-----------|----------|------|-------|
| Backend (FastAPI) | Render | Free/Starter | $0-7/mês |
| Banco (PostgreSQL) | Neon | Free | $0 (0.5GB) |
| Frontend (Next.js) | Vercel | Free | $0 |
| Domínio | Já tem? | - | - |

### Env Vars Necessárias

```bash
# Backend (Render)
DATABASE_URL=postgresql://...@neon.tech/crm_vitao360
SECRET_KEY=...
DESKRIO_TOKEN=eyJ...  # JWT Deskrio
MERCOS_ACCOUNT_ID=399424
ENVIRONMENT=production

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://crm-vitao360.onrender.com
```

### Deploy Steps

1. Criar banco Neon → obter DATABASE_URL
2. Configurar env vars no Render
3. Push código → Render auto-deploy
4. Rodar `alembic upgrade head` no Render
5. Rodar scripts de ingestão (popular banco)
6. Configurar env vars no Vercel
7. Push frontend → Vercel auto-deploy
8. Testar end-to-end

---

## ORDEM DE EXECUÇÃO (Roadmap)

```
SEMANA 1: Fundação
├── [1] Senha Sales Hunter → testar auth via curl
├── [2] Criar ingest_deskrio.py (contatos + tickets → DB)
├── [3] Criar ingest_mercos.py (clientes → DB)
└── [4] Setup Neon PostgreSQL + migração Alembic

SEMANA 2: Dados Fluindo
├── [5] Criar ingest_sales_hunter.py (vendas → DB)
├── [6] Implementar CNPJ bridge (reconciliação 3 fontes)
├── [7] Rodar ingestão completa → validar faturamento = R$ 2.091.000
└── [8] Deploy backend + banco Neon em Render

SEMANA 3: Frontend Real
├── [9] Dashboard com dados reais
├── [10] Carteira com 6.429+ clientes
├── [11] Pipeline com Kanban Deskrio
└── [12] Deploy frontend Vercel

SEMANA 4: Polish
├── [13] Sinaleiro + Score com dados reais
├── [14] Inbox com mensagens Deskrio
├── [15] Relatórios SAP
└── [16] Testes E2E + validação final
```

---

## GAP 7: PIPELINE DE PRODUTOS + PEDIDOS + EXPORTAÇÃO SAP TXT ⚠️ SPEC SEPARADA

**Spec completa em:** `SPEC_PIPELINE_PRODUTOS.md` (mesmo diretório)

**Resumo:** Catálogo de produtos com EAN, criação de pedidos no CRM, exportação em 3 formatos
(PDF, Excel, TXT SAP). O TXT segue formato posicional fixo decodificado do arquivo real
`19465816.txt` (41 itens, R$ 102.099,28). Elimina digitação manual no Sales Hunter.

**Tabelas novas:** `pedidos` (21 cols), `pedido_itens` (18 cols)
**ALTER TABLE:** `produtos` ganha 7 colunas (subcategoria, EAN, qtd_embalagem, etc.)
**Scripts novos:** `gerar_txt_sap()`, `gerar_pdf_pedido()`, `gerar_xlsx_pedido()`, `enrich_produtos.py`

**Status:** SPEC COMPLETA ✅ | Implementação: PENDENTE

---

## DIVISÃO COWORK vs VSCODE

| Responsável | Tarefas |
|-------------|---------|
| **Cowork** | Specs, extração diária (pipeline 7h), revisão, validação |
| **VSCode** | Código (ingestão, migração, endpoints, frontend), commits, testes |

O Cowork é o **professor/revisor**. O VSCode é o **executor**.
Este documento é a spec que o VSCode segue.
