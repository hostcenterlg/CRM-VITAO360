# SPEC: Pipeline de Produtos + Pedidos + Exportação SAP TXT

> Spec técnica para VSCode implementar a aba de produtos, criação de pedidos,
> e exportação em PDF, Excel e TXT (formato SAP/Sales Hunter).
> Gerado: 25/Abr/2026 | Autor: Cowork (professor/revisor)
> Referência: arquivo real `19465816.txt` (pedido SAP decodificado campo a campo)

---

## 1. CONTEXTO E MOTIVAÇÃO

### Problema atual
O vendedor recebe pedido via WhatsApp do cliente. Hoje, precisa digitar MANUALMENTE
cada item no Sales Hunter para gerar a NF no SAP. Com 41 itens por pedido (caso real
do arquivo 19465816.txt), isso leva ~30 minutos por pedido.

### Solução
CRM captura o pedido → Exporta TXT no formato SAP → Importa no Sales Hunter automaticamente.
Tempo: ~2 minutos (montar pedido no CRM) + 30 segundos (importar TXT).

### Fluxo completo
```
WhatsApp → Vendedor abre CRM → Seleciona cliente (CNPJ)
→ Busca produtos no catálogo → Define qtd, preço, desconto
→ CRM calcula totais → Exporta em 3 formatos:
   1. PDF (para o cliente confirmar)
   2. Excel (para controle interno)
   3. TXT SAP (para importar no Sales Hunter → SAP)
```

---

## 2. CATÁLOGO DE PRODUTOS

### 2.1 Fonte de dados
A tabela `produtos` já existe no banco com 242 produtos. Mas precisa ser ENRIQUECIDA
com dados do `fat_produto` (Sales Hunter) que traz:
- Categoria e subcategoria SAP reais
- Peso bruto (kg)
- Unidade de medida (Fardo, Caixa, etc.)
- Faturamento histórico por produto

### 2.2 Schema atual da tabela `produtos` (15 colunas)
```sql
-- JÁ EXISTE, NÃO RECRIAR
produtos (
    id INTEGER PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,        -- código SAP (ex: 300035305)
    nome VARCHAR(255) NOT NULL,         -- descrição do produto
    categoria VARCHAR(100),             -- categoria (ex: REEMBALADOS, MARCAS PROPRIAS)
    fabricante VARCHAR(100) NOT NULL,   -- sempre VITAO
    unidade VARCHAR(10) NOT NULL,       -- UN, CX, FD
    preco_tabela FLOAT NOT NULL,        -- preço tabela (bruto) por UNIDADE
    preco_minimo FLOAT NOT NULL,        -- preço mínimo permitido
    comissao_pct FLOAT NOT NULL,        -- % comissão vendedor
    ipi_pct FLOAT NOT NULL,             -- % IPI
    peso FLOAT,                         -- peso em kg (HOJE NULL, precisa popular)
    ean VARCHAR(20),                    -- EAN-13 (HOJE NULL, precisa popular)
    ativo BOOLEAN NOT NULL,             -- 1=ativo, 0=descontinuado
    created_at DATETIME,
    updated_at DATETIME
)
```

### 2.3 Colunas a ADICIONAR na tabela `produtos`
```sql
ALTER TABLE produtos ADD COLUMN subcategoria VARCHAR(100);
ALTER TABLE produtos ADD COLUMN unidade_embalagem VARCHAR(20);  -- Fardo, Caixa, Display
ALTER TABLE produtos ADD COLUMN qtd_por_embalagem INTEGER;      -- unidades por caixa/fardo (EA)
ALTER TABLE produtos ADD COLUMN peso_bruto_kg FLOAT;            -- peso bruto da embalagem
ALTER TABLE produtos ADD COLUMN codigo_ncm VARCHAR(10);         -- NCM fiscal (se disponível)
ALTER TABLE produtos ADD COLUMN fat_total_historico FLOAT DEFAULT 0;  -- total faturado lifetime
ALTER TABLE produtos ADD COLUMN curva_abc_produto VARCHAR(1);   -- A/B/C baseado em faturamento
```

### 2.4 Popular EAN-13 dos produtos
O arquivo TXT decodificado tem 41 produtos com EAN real. TODOS os EANs começam com `789`
(prefixo Brasil). O campo `ean` da tabela `produtos` está NULL para todos os 242 registros.

**Fonte de EAN:** O arquivo TXT do pedido (e futuros pedidos) contém o EAN na posição 18-30
(13 dígitos) de cada linha tipo "04". Ao processar os TXTs recebidos, popular o campo `ean`
via UPDATE usando o `codigo` SAP como chave de cruzamento.

**Match:** `line[71:91].strip()` do TXT = `produtos.codigo`

### 2.5 Popular dados do fat_produto (Sales Hunter XLSX)
O relatório `fat_produto_cwb_all_*.xlsx` tem 275 produtos com:

| Coluna XLSX | Campo DB | Notas |
|-------------|----------|-------|
| CÓD. Material | codigo | Chave de JOIN |
| Material | nome | Atualizar se diferente |
| Categoria | categoria | Ex: REEMBALADOS, MARCAS PROPRIAS |
| Subcategoria | subcategoria | Ex: AÇÚCAR, AVEIA, BISCOITO |
| Unidade de medida U.M. | unidade_embalagem | Fardo, Caixa, Display |
| Peso bruto kg | peso_bruto_kg | Peso por embalagem |
| Total faturado | fat_total_historico | Faturamento lifetime |

**CUIDADO:** fat_produto tem CWB + VV. Deduplica por código, SOMA faturamento.

---

## 3. TABELA DE PEDIDOS (NOVA)

### 3.1 Schema `pedidos`
```sql
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_pedido VARCHAR(20) NOT NULL UNIQUE, -- gerado pelo CRM: "CRM-YYYYMMDD-NNNN"
    cnpj VARCHAR(14) NOT NULL,                 -- CNPJ do cliente (FK clientes)
    consultor VARCHAR(50) NOT NULL,            -- MANU, LARISSA, DAIANE, JULIO
    data_pedido DATE NOT NULL,                 -- data de criação
    data_entrega_solicitada DATE,              -- quando o cliente quer receber
    data_faturamento DATE,                     -- previsão de faturamento
    tipo_frete VARCHAR(3) DEFAULT 'CIF',       -- CIF ou FOB
    observacoes TEXT,                           -- notas do vendedor
    status VARCHAR(20) DEFAULT 'rascunho',     -- rascunho → confirmado → exportado → faturado
    total_bruto FLOAT DEFAULT 0,               -- soma dos itens (sem desconto)
    total_liquido FLOAT DEFAULT 0,             -- soma dos itens (com desconto)
    total_itens INTEGER DEFAULT 0,             -- count de linhas
    exportado_txt BOOLEAN DEFAULT 0,           -- já gerou TXT?
    exportado_pdf BOOLEAN DEFAULT 0,           -- já gerou PDF?
    exportado_xlsx BOOLEAN DEFAULT 0,          -- já gerou Excel?
    numero_pedido_sap VARCHAR(20),             -- número do pedido no SAP (após import)
    fonte VARCHAR(20) DEFAULT 'CRM',
    classificacao_3tier VARCHAR(15) DEFAULT 'REAL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Schema `pedido_itens`
```sql
CREATE TABLE IF NOT EXISTS pedido_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,                -- FK pedidos.id
    produto_id INTEGER NOT NULL,               -- FK produtos.id
    seq INTEGER NOT NULL,                      -- sequência no pedido (1, 2, 3...)
    codigo_sap VARCHAR(50) NOT NULL,           -- produtos.codigo
    ean VARCHAR(20),                           -- produtos.ean (pode ser NULL)
    descricao VARCHAR(255) NOT NULL,           -- produtos.nome
    unidade VARCHAR(10) DEFAULT 'EA',          -- unidade
    qtd_por_embalagem INTEGER DEFAULT 1,       -- unidades por caixa
    qtd_caixas FLOAT NOT NULL,                 -- quantidade de caixas/fardos
    qtd_unidades FLOAT NOT NULL,               -- qtd_caixas × qtd_por_embalagem
    preco_tabela FLOAT NOT NULL,               -- preço bruto por caixa
    desconto_pct FLOAT DEFAULT 0,              -- % desconto aplicado
    preco_liquido FLOAT NOT NULL,              -- preco_tabela × (1 - desconto_pct/100)
    total_bruto FLOAT NOT NULL,                -- qtd_caixas × preco_tabela
    total_liquido FLOAT NOT NULL,              -- qtd_caixas × preco_liquido
    ipi_pct FLOAT DEFAULT 0,                   -- % IPI do produto
    observacao VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
```

---

## 4. FORMATO SAP TXT — ESPECIFICAÇÃO POSICIONAL COMPLETA

> Decodificado do arquivo real `19465816.txt` (pedido com 41 itens, CNPJ 04869719000178).
> Cada linha tem comprimento FIXO. Charset: ASCII/Latin-1. Line ending: CRLF ou LF.

### 4.1 Estrutura geral do arquivo
```
Linha 1: HEADER     (tipo 019, 315 chars fixos)
Linha 2: SUBHEADER  (tipo 021, 45 chars fixos)
Linha 3: CONTROLE   (tipo 03, 122 chars — todos zeros)
Linhas 4..N: ITENS  (tipo 04, 330 chars cada)
Linha N+1: FOOTER   (tipo 09, 122 chars)
```

### 4.2 HEADER — Tipo 019 (315 chars)

| Pos Início | Pos Fim | Tam | Campo | Formato | Exemplo |
|-----------|---------|-----|-------|---------|---------|
| 0 | 2 | 3 | tipo | "019" fixo | 019 |
| 3 | 4 | 2 | espaços | "  " | |
| 5 | 7 | 3 | sequencia | "001" fixo | 001 |
| 8 | 15 | 8 | numero_pedido | numérico, left-pad zeros | 19465816 |
| 16 | 27 | 12 | espaços | padding | |
| 28 | 35 | 8 | numero_pedido_dup | repetição do número | 19465816 |
| 36 | 47 | 12 | espaços | padding | |
| 48 | 55 | 8 | data_pedido | YYYYMMDD | 20260423 |
| 56 | 59 | 4 | zeros | "0000" | 0000 |
| 60 | 67 | 8 | data_entrega | YYYYMMDD | 20260427 |
| 68 | 71 | 4 | zeros | "0000" | 0000 |
| 72 | 79 | 8 | data_faturamento | YYYYMMDD | 20260507 |
| 80 | 83 | 4 | zeros | "0000" | 0000 |
| 84 | 114 | 31 | padding | espaços + zeros | |
| 115 | 128 | 14 | cnpj_cliente | 14 dígitos, sem pontuação | 04869719000178 |
| 129 | 268 | 140 | campos_auxiliares | IEs, códigos internos SAP | (copiar do template) |
| 269 | 271 | 3 | tipo_frete | "CIF" ou "FOB" | CIF |
| 272 | 314 | 43 | padding_final | zeros + espaços | |

**NOTA IMPORTANTE:** Os campos auxiliares (pos 129-268) contêm inscrições estaduais e
códigos internos SAP que são FIXOS por cliente. Para a primeira versão, usar template
fixo baseado no arquivo de referência. Futuramente, criar tabela `clientes_sap_config`
com esses dados por CNPJ.

### 4.3 SUBHEADER — Tipo 021 (45 chars)

| Pos | Tam | Campo | Exemplo |
|-----|-----|-------|---------|
| 0-2 | 3 | tipo | "021" |
| 3-4 | 2 | espaços | "  " |
| 5 | 1 | flag1 | "5" |
| 6-7 | 2 | espaços | "  " |
| 8 | 1 | flag2 | "1" |
| 9-10 | 2 | espaços | "  " |
| 11-12 | 2 | codigo_cd | "CD" (centro distribuição) |
| 13 | 1 | espaço | " " |
| 14-16 | 3 | codigo_filial | "045" (Curitiba) |
| 17-24 | 8 | data_validade | YYYYMMDD | 20260607 |
| 25-34 | 10 | codigo_pagamento | "0000001029" |
| 35-44 | 10 | valor_referencia | "150510000" |

**Para a v1:** Copiar literalmente do template, alterando apenas `data_validade`
(= data_faturamento + 30 dias) e `codigo_filial` (045=CWB, outro para VV).

### 4.4 CONTROLE — Tipo 03 (122 chars)

Linha fixa: `"03" + "0" × 120`

Sempre igual, sem variação entre pedidos.

### 4.5 ITENS — Tipo 04 (330 chars cada) ⭐ CAMPO MAIS IMPORTANTE

| Pos Início | Pos Fim | Tam | Campo | Formato | Exemplo (Item 1) |
|-----------|---------|-----|-------|---------|-------------------|
| 0 | 1 | 2 | tipo | "04" fixo | 04 |
| 2 | 5 | 4 | seq | sequência 0001-9999 | 0001 |
| 6 | 10 | 5 | sub_seq | sempre "00000" | 00000 |
| 11 | 13 | 3 | espaços | "   " | |
| 14 | 15 | 2 | tipo_item | "EN" (entrada normal) | EN |
| 16 | 16 | 1 | espaço | " " | |
| 17 | 17 | 1 | ean_flag | dígito flag do EAN | 1 |
| 18 | 30 | 13 | ean_13 | código de barras EAN-13 | 7896063200651 |
| 31 | 70 | 40 | descricao | nome do produto, right-pad espaços | BISC VITAO VICCIO... |
| 71 | 90 | 20 | codigo_sap | código material SAP, right-pad | 300035305 |
| 91 | 93 | 3 | unidade_marca | "EA " (each = unidade) | EA |
| 94 | 98 | 5 | qtd_por_embalagem | unidades por caixa, left-pad zeros | 00040 |
| 99 | 143 | 45 | bloco_qtd_pre_bx | qtd em unidades + padding zeros | 000000000001800... |
| 144 | 146 | 3 | marcador_bx | "BX " (box = caixa) | BX |
| 147 | 153 | 7 | qtd_caixas | caixas × 100 (2 dec implícitos) | 0001800 → 18.00 |
| 154 | 168 | 15 | total_bruto | R$ × 10000 (4 dec implícitos) | 000000034020000 → R$ 3.402,00 |
| 169 | 183 | 15 | total_liquido | R$ × 10000 | 000000034020000 → R$ 3.402,00 |
| 184 | 198 | 15 | preco_unit_bruto | R$ × 10000 (preço por caixa) | 000000001890000 → R$ 189,00 |
| 199 | 213 | 15 | preco_unit_liq | R$ × 10000 (preço por caixa c/ desc) | 000000001890000 → R$ 189,00 |
| 214 | 216 | 3 | padding1 | "000" | 000 |
| 217 | 219 | 3 | espaços | "   " | |
| 220 | 329 | 110 | campos_fiscais | impostos/descontos (ver 4.5.1) | zeros se sem imposto |

#### 4.5.1 Campos Fiscais (pos 220-329) — Opcional v1

Para itens COM desconto (15%, 10%), os campos fiscais contêm:

| Pos Relativa | Tam | Campo | Exemplo |
|-------------|-----|-------|---------|
| 220-232 | 13 | base_calc_zeros | "0000000000000" |
| 233-245 | 13 | preco_tabela_orig | preço tabela original × 100 | 
| 246-247 | 2 | pct_desconto | percentual × 10 (15% = "15", 10% = "10") |
| 248-329 | 82 | campos_ipi_icms | IPI/ICMS (zeros se não aplicável) |

**Para a v1:** Preencher pos 220-329 com zeros. Desconto já está embutido
nos campos `total_liquido` e `preco_unit_liq`.

#### 4.5.2 Bloco pré-BX (pos 99-143) — 45 chars

Contém a quantidade em unidades (não caixas) no formato:
`qtd_unidades × 100` (7 dígitos) + 38 zeros de padding.

Exemplo: 18 caixas × 40 EA = 720 unidades → `000000000072000` + zeros
Mas no arquivo real mostra `000000000001800...` que é 18.00 (caixas, não unidades).

**Na prática:** Este campo é REDUNDANTE com o `qtd_caixas` após BX.
Repetir o mesmo valor: `qtd_caixas × 100` left-padded em 13 chars + 32 zeros.

### 4.6 FOOTER — Tipo 09 (122 chars)

| Pos | Tam | Campo | Formato |
|-----|-----|-------|---------|
| 0-1 | 2 | tipo | "09" |
| 2-9 | 8 | qtd_itens | count de linhas tipo 04, left-pad zeros |
| 10-24 | 15 | total_liquido | R$ × 100 (2 dec implícitos) |
| 25-39 | 15 | total_bruto_alt | formato alternativo (verificar) |
| 40-109 | 70 | zeros | padding |
| 110-121 | 12 | checksum | total_liquido × 100 (sem decimais) ou similar |

**Exemplo real:** `09|00000001|0209928|00000000008156600000...10291494`
- 10209928 ÷ 100 = R$ 102.099,28 (total líquido do pedido) ✓

### 4.7 Regras de formatação numérica

| Campo | Largura | Alinhamento | Decimal implícito | Exemplo |
|-------|---------|-------------|-------------------|---------|
| qtd_caixas | 7 | left-pad zeros | ÷ 100 (2 dec) | 0001800 = 18.00 |
| valores R$ | 15 | left-pad zeros | ÷ 10000 (4 dec) | 000000034020000 = 3402.00 |
| qtd_por_emb | 5 | left-pad zeros | inteiro | 00040 = 40 |
| seq | 4 | left-pad zeros | inteiro | 0001 |
| datas | 8 | YYYYMMDD | sem separador | 20260423 |
| CNPJ | 14 | sem pontuação | string | 04869719000178 |

### 4.8 EAN Flag Digit (pos 17)

O dígito na posição 17 NÃO faz parte do EAN-13 real do produto.
É um flag do sistema SAP que varia (1, 7, 8, 9). O EAN real está em pos 18-30.

Na GERAÇÃO do TXT, usar `1` como flag default (mais comum no arquivo de referência).

---

## 5. GERAÇÃO DO TXT — FUNÇÃO PYTHON

### 5.1 Assinatura
```python
def gerar_txt_sap(
    pedido_id: int,
    db_path: str = "data/crm_vitao360.db",
    output_dir: str = "exports/txt/"
) -> str:
    """
    Gera arquivo TXT no formato SAP/Sales Hunter para importação.
    
    Args:
        pedido_id: ID do pedido na tabela 'pedidos'
        db_path: caminho do banco SQLite
        output_dir: diretório de saída
    
    Returns:
        Caminho do arquivo TXT gerado
    
    Raises:
        ValueError: se pedido não existe, está vazio, ou tem produto sem código SAP
    """
```

### 5.2 Lógica de geração

```
1. Buscar pedido + itens no banco
2. Validar:
   a. Pedido existe e tem status != 'cancelado'
   b. Todos os itens têm codigo_sap preenchido
   c. CNPJ do cliente é válido (14 dígitos)
   d. Ao menos 1 item no pedido
3. Gerar HEADER (315 chars)
   - numero_pedido: usar pedido.id ou gerar sequencial
   - datas: pedido.data_pedido, data_entrega, data_faturamento
   - CNPJ: pedido.cnpj
   - tipo_frete: pedido.tipo_frete
4. Gerar SUBHEADER (45 chars) — template fixo
5. Gerar CONTROLE (122 chars) — "03" + 120 zeros
6. Para cada item, gerar linha de 330 chars:
   - seq: 1, 2, 3...
   - EAN: do produto (ou "0000000000000" se NULL)
   - descricao: truncar/pad em 40 chars
   - codigo_sap: pad em 20 chars
   - EA: qtd_por_embalagem
   - BX: qtd_caixas, total_bruto, total_liq, preco_unit_bruto, preco_unit_liq
   - campos_fiscais: zeros na v1
7. Gerar FOOTER (122 chars)
   - count de itens
   - total líquido × 100
8. Salvar arquivo: "{output_dir}/{numero_pedido}.txt"
9. Atualizar pedido.exportado_txt = 1
```

### 5.3 Funções auxiliares necessárias

```python
def fmt_val_10000(valor: float) -> str:
    """Formata valor monetário em 15 chars com 4 decimais implícitos.
    Ex: 3402.00 → '000000034020000'
    """
    return str(int(round(valor * 10000))).zfill(15)

def fmt_qty_100(qty: float) -> str:
    """Formata quantidade em 7 chars com 2 decimais implícitos.
    Ex: 18.0 → '0001800'
    """
    return str(int(round(qty * 100))).zfill(7)

def fmt_int(val: int, width: int) -> str:
    """Formata inteiro com left-pad zeros.
    Ex: fmt_int(40, 5) → '00040'
    """
    return str(val).zfill(width)

def pad_right(text: str, width: int) -> str:
    """Pad com espaços à direita.
    Ex: pad_right("BISC VITAO", 40) → 'BISC VITAO                              '
    """
    return text[:width].ljust(width)

def pad_left_zero(text: str, width: int) -> str:
    """Pad com zeros à esquerda.
    Ex: pad_left_zero("300035305", 20) → '300035305           '
    """
    return text[:width].ljust(width)
```

---

## 6. EXPORTAÇÃO PDF

### 6.1 Conteúdo do PDF de pedido
```
CABEÇALHO:
  Logo VITAO (se disponível) | "Pedido Nº CRM-20260423-0001"
  Data: 23/04/2026 | Vendedor: MANU
  
DADOS DO CLIENTE:
  Razão Social: XXXXX | CNPJ: 04.869.719/0001-78
  Endereço: (se disponível no cadastro)
  
TABELA DE ITENS:
  | # | Código | Descrição | UN | Qtd Cx | Preço/Cx | Desc% | Total |
  |---|--------|-----------|-----|--------|----------|-------|-------|
  | 1 | 300035305 | BISC VITAO VICCIO WAF... | CX/40 | 18 | 189,00 | 0% | 3.402,00 |
  | 2 | ... | ... | ... | ... | ... | 15% | 517,65 |
  
TOTAIS:
  Subtotal (bruto): R$ 113.061,09
  Descontos: R$ -10.961,81
  Total Líquido: R$ 102.099,28
  
OBSERVAÇÕES:
  {pedido.observacoes}
  
RODAPÉ:
  "Frete: CIF" | "Previsão entrega: 27/04/2026"
```

### 6.2 Biblioteca sugerida
`reportlab` para geração programática. Alternativa: `weasyprint` (HTML → PDF).

---

## 7. EXPORTAÇÃO EXCEL

### 7.1 Layout da planilha
Aba única "Pedido" com:
- Cabeçalho mergado (A1:H1): "Pedido CRM-20260423-0001"
- Dados do cliente: A3:H4
- Tabela de itens: A6:H(N+6)
- Totais: abaixo da tabela
- Formatação: fonte Arial 9pt, cores padrão CRM (R9 — visual LIGHT)

### 7.2 Regras de formatação
- Valores monetários: formato "R$ #.##0,00"
- Percentuais: formato "0%"
- Fórmulas em INGLÊS (R7): =SUM(), =IF()
- NUNCA fórmulas em português

---

## 8. PÁGINA DE PRODUTOS NO FRONTEND

### 8.1 Componentes necessários

```
/app/produtos/page.tsx          — Catálogo de produtos (listagem + busca)
/app/produtos/[id]/page.tsx     — Detalhe do produto
/app/pedidos/page.tsx           — Lista de pedidos
/app/pedidos/novo/page.tsx      — Criar novo pedido
/app/pedidos/[id]/page.tsx      — Detalhe do pedido + exportar
```

### 8.2 Catálogo de produtos
- Tabela paginada com busca por nome/código/EAN
- Filtros: categoria, subcategoria, ativo/inativo, curva ABC
- Colunas: Código | Nome | Categoria | Preço Tabela | Preço Mín | Estoque (futuro) | EAN
- Ação: "Adicionar ao pedido" (abre modal de quantidade)

### 8.3 Criação de pedido
- Step 1: Selecionar cliente (busca por CNPJ/nome, autocomplete)
- Step 2: Adicionar produtos (busca no catálogo, define qtd e desconto)
- Step 3: Revisar (tabela com totais, editar quantidades)
- Step 4: Confirmar e exportar (botões PDF, Excel, TXT)

### 8.4 API endpoints necessários

```
GET    /api/produtos                — Listar produtos (com paginação/filtro)
GET    /api/produtos/:id            — Detalhe do produto
POST   /api/pedidos                 — Criar pedido (com itens)
GET    /api/pedidos                 — Listar pedidos
GET    /api/pedidos/:id             — Detalhe do pedido
PATCH  /api/pedidos/:id             — Atualizar status
POST   /api/pedidos/:id/exportar    — Gerar exportação (body: {formato: "txt"|"pdf"|"xlsx"})
GET    /api/pedidos/:id/download/:formato — Baixar arquivo gerado
```

---

## 9. SCRIPT DE ENRIQUECIMENTO: `enrich_produtos.py`

### 9.1 Objetivo
Popular campos NULL da tabela `produtos` usando dados de `fat_produto` e arquivos TXT SAP.

### 9.2 Lógica
```
1. Ler fat_produto_cwb_all_*.xlsx + fat_produto_vv_all_*.xlsx
2. Para cada produto no XLSX:
   a. Buscar por codigo (CÓD. Material) na tabela produtos
   b. UPDATE: subcategoria, unidade_embalagem, peso_bruto_kg
   c. fat_total_historico = SUM(Total faturado) de CWB + VV
3. Calcular curva ABC:
   - Top 20% faturamento → A
   - Próximos 30% → B
   - Resto → C
4. Ler arquivos TXT SAP (quando disponíveis):
   a. Extrair EAN-13 (pos 18-30) + codigo_sap (pos 71-90)
   b. UPDATE produtos SET ean = ? WHERE codigo = ?
   c. Extrair qtd_por_embalagem (pos 94-98)
   d. UPDATE produtos SET qtd_por_embalagem = ? WHERE codigo = ?
```

### 9.3 Idempotência
UPSERT: rodar múltiplas vezes sem duplicar. Usar ON CONFLICT ou UPDATE WHERE.

---

## 10. VALIDAÇÕES OBRIGATÓRIAS (DETECTOR DE MENTIRA)

### 10.1 Antes de exportar TXT
- [ ] Todos os itens têm codigo_sap NOT NULL
- [ ] CNPJ do cliente = 14 dígitos, string
- [ ] Nenhum valor negativo em qtd ou preço
- [ ] total_bruto = SUM(itens.total_bruto) ± R$ 0.01
- [ ] total_liquido = SUM(itens.total_liquido) ± R$ 0.01
- [ ] Linha do TXT tem EXATAMENTE 330 chars (itens)
- [ ] Header tem EXATAMENTE 315 chars
- [ ] Footer tem EXATAMENTE 122 chars

### 10.2 Após gerar TXT
- [ ] Arquivo não está vazio
- [ ] Primeira linha começa com "019"
- [ ] Última linha começa com "09"
- [ ] Count de linhas "04" = pedido.total_itens
- [ ] Total no footer = pedido.total_liquido × 100
- [ ] Reimportar e comparar: parse do TXT gerado deve bater com dados do banco

### 10.3 Two-Base Architecture
- Pedido = tipo VENDA → TEM valor R$
- NUNCA misturar com LOG (interações)
- `pedidos` e `pedido_itens` são entidades VENDA

---

## 11. CRONOGRAMA DE IMPLEMENTAÇÃO

### Onda 1 — Backend (prioridade máxima)
1. Criar tabelas `pedidos` + `pedido_itens` (migration)
2. ALTER TABLE `produtos` (novas colunas)
3. Script `enrich_produtos.py`
4. Função `gerar_txt_sap()` + testes unitários
5. Função `gerar_pdf_pedido()` + testes
6. Função `gerar_xlsx_pedido()` + testes

### Onda 2 — API
7. Endpoints CRUD de produtos
8. Endpoints CRUD de pedidos
9. Endpoint de exportação (POST + GET download)

### Onda 3 — Frontend
10. Página catálogo de produtos
11. Página criação de pedido (wizard 4 steps)
12. Página lista de pedidos
13. Botões de exportação com download

### Onda 4 — Validação
14. Testes E2E: criar pedido → exportar TXT → validar formato
15. Teste com arquivo real: gerar TXT para o pedido 19465816 e comparar
16. Teste de importação no Sales Hunter (Leandro faz manualmente)

---

## 12. ARQUIVO DE REFERÊNCIA

O arquivo `19465816.txt` está em `/mnt/uploads/19465816.txt` e contém:
- 1 header + 1 subheader + 1 controle + 41 itens + 1 footer = 45 linhas
- CNPJ: 04869719000178
- Total líquido: R$ 102.099,28
- 41 produtos VITAO (biscoitos, chocolates, doces, barras proteína, aveias, etc.)
- Descontos: 0%, 10%, 15%
- Este arquivo é o GROUND TRUTH para validação do gerador de TXT

### Produtos do pedido de referência (41 itens decodificados)
```
Seq  EAN-13          Descrição                                   SAP Code    EA  Qtd  Total Líq  Desc%
  1  7896063200651   BISC VITAO VICCIO WAF COB ZERO 30G CHOC     300035305   40   18  3.402,00    0%
  2  7896063220048   BISC VITAO COOKIES S ACU COB PC120G MACA     300000227    8    7    517,65   15%
  3  7896063220093   BISC VITAO COOKIES INT ZERO PC 120G CAST     300000219    8   10    603,90   15%
  4  7896063282510   BISC VITAO COOKIES INT PC 120G CASTANHA      300000179    8   25  1.386,50   15%
  5  7896863461619   DOCE LEITE VITAO S ACU VD 200G COCO          300000246    8   33  5.375,70   10%
  6  7896063285146   CHOC VITAO MARCANTE BCO S ACU BR70G MGO      300019998   24    1    324,50   15%
  7  7896063201337   BISC VITAO DISNEY ROSQ CHOC PC 60G LEITE     300040806   20    4    405,00    0%
  8  7896063201306   SNACK SALG VITAO DISNEY PC 30G PIZZA         300040803   24   10    837,00    0%
  9  7896063281939   DOCE VITAO COCADA ZERO VD 200G C MARACUJ     300000140    8    7  1.140,30   10%
 10  8960632446106   LINHACA VITAO PC 150G                        300000397   12   45  2.662,20   15%
 11  7896063285160   CHOC VITAO MARCANTE S ACUR BR 70G 40  AO     300019993   24    1    324,50   15%
 12  7896063201241   BARRA PROTEINA WHEY SOULPRO PC 40G CHOC      300039473   72   11  7.573,50    0%
 13  7896063201320   BISC VITAO DISNEY COOKIES S GLU 60G BAUN     300040805   20    4    405,00    0%
 14  7896063201290   SNACK SALG VITAO DISNEY PC 30G CHEDDAR       300040802   24   10    837,00    0%
 15  7896063280264   MIX DE GRAOS SEM VITAO 120G                  300000362   12   83  6.342,86   15%
 16  7896063200279   CHOC VITAO MARCANTE S ACUR BR 70G 70  NI     300019994   24    2    649,00   15%
 17  7896063201227   BARRA PROTEINA WHEY SOULPRO PC 40G MEIO      300039472   72   12  8.262,00    0%
 18  7896063243610   GIRASSOL VITAO TOST SALG PC 60G              300000393   17   20  1.485,00    0%
 19  7896063285870   BISC VITAO WAFER INT ZERO PC 90G TORTA L     300035212   20    8  1.009,84   15%
 20  7896063220017   BISC VITAO COOKIES S ACU COB PC120G BANA     300000214    8   10    739,50   15%
 21  7896063282527   BISC VITAO COOKIES INT PC 120G CASTANHA      300000182    8   31  1.719,26   15%
 22  7896063281946   GERGELIM VITAO PC 150G                       300000288   12   37  4.442,22   10%
 23  7896063201429   BISC VITAO DISNEY ROSQ CHOC PC 60G SEM G     300041367   20    4    405,00    0%
 24  7896063201344   BISC VITAO DISNEY COOKIES S GLU 60G CHOC     300040807   20    8    810,00    0%
 25  7896063220079   BISC VITAO COOKIES S ACU COB PC120G MORA     300000230    8   14  1.035,30   15%
 26  7896863499978   CHOC VITAO DIET BR 22G AO LEITE              300000105   48   20  4.326,60   15%
 27  7896063284954   DOCE LEITE VITAO S ACU VD 200G TRADICION     300000248    8   68 11.077,20   10%
 28  7896863432153   GOIABADA VITAO S ACU PT 270G                 300000298   12    1    216,00    0%
 29  7896063285061   CHOC VITAO ZERO BR 70G CAPPUCCINO            300019996   24    7  2.271,50   15%
 30  7896063285207   CHOC VITAO ZERO BR 70G COOKIES CREAM         300019992   24    8  2.596,00   15%
 31  7896063201180   BARRA PROTEINA WHEY SOULPRO PC 40G AO LE     300039471   72    7  4.819,50    0%
 32  7896063282541   BISC VITAO COOKIES INT PC 120G CACAU         300000176    8   41  2.273,86   15%
 33  7896863499961   CHOC VITAO S ACU BR22G LEITE CEREAIS         300000108   36   24  5.191,92   15%
 34  7896063281915   DOCE VITAO COCADA ZERO VD 200G AO LEITE      300000135    8    5    814,50   10%
 35  7896063281056   PROTEINA SOJA VITAO PC 200G MEDIA            300000385   12   14  1.404,20   15%
 36  7896863499916   AVEIA VITAO S GLU CX 170G FLOCOS FINOS       300015499   12   23  1.956,15   10%
 37  7896063285085   CHOC VITAO MARCANTE S ACUR BR 70G 60  MI     300019995   24   10  3.245,00   15%
 38  7896063285184   CHOC VITAO ZERO BR 70G CAFE ESPRESSO         300019991   24    7  2.271,50   15%
 39  7896063201313   SNACK SALG VITAO DISNEY PC 30G REQUEIJAO     300040804   24   16  1.339,20    0%
 40  7896063244624   FAR LINHACA VITAO MARRON PC 150G             300000260   12   31  1.707,48   15%
 41  7896063280424   CHOC VITAO S ACU BCO BR 22G                  300000077   48   18  3.893,94   15%
```

---

## REGRAS DO PROJETO QUE SE APLICAM

- **R4 (Two-Base):** Pedidos = VENDA. Tem valor R$. Nunca misturar com LOG.
- **R5 (CNPJ):** Sempre string 14 dígitos, zero-padded. `re.sub(r'\D', '', str(val)).zfill(14)`
- **R7 (Fórmulas inglês):** Se gerar Excel com fórmulas, usar IF/SUM/VLOOKUP.
- **R8 (Nunca inventar):** Preços vêm do catálogo. NUNCA placeholder. Tier = REAL.
- **R9 (Visual LIGHT):** Fonte Arial 9pt, cores status padrão, NUNCA dark mode.
- **R11 (Commits atômicos):** 1 task = 1 commit.
- **R12 (Níveis):** Criar tabelas novas = L3 (LEANDRO já aprovou nesta sessão).

---

*Este documento é a spec que o VSCode segue. Cowork = professor/revisor.*
