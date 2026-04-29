-- ============================================================
-- MIGRATION DDE #002 — Tabela produto_custo_comercial (CMV)
-- CRM VITAO360 — Neon PostgreSQL
-- Golden Master: ZSD062 "Custo Comercial" por SKU
-- Data: 29/04/2026
-- ============================================================
-- INSTRUÇÕES:
--   1. Rodar APÓS DDE_MIGRATION_001.sql
--   2. Fonte dos dados: planilha ZSD062 (exportação SAP)
--   3. Coluna custo_comercial = valor unitário por SKU/ano
--   4. Engine usa: SUM(custo_comercial × qty vendida) = CMV total
-- ============================================================

BEGIN;

-- ============================================================
-- TABELA: produto_custo_comercial
-- Fonte: ZSD062 (SAP) — coluna "Custo Comercial" por SKU
-- Alimenta: L12 (CMV) via _get_cmv() no dde_engine.py
-- ============================================================
CREATE TABLE IF NOT EXISTS produto_custo_comercial (
    id                  SERIAL PRIMARY KEY,
    codigo_produto      VARCHAR(20)     NOT NULL,
    descricao           VARCHAR(200),
    ano                 INT             NOT NULL,
    custo_comercial     NUMERIC(12,4)   NOT NULL,   -- R$/unidade
    custo_tabela        NUMERIC(12,4),               -- preço tabela referência
    preco_medio_venda   NUMERIC(12,4),               -- preço médio praticado
    margem_sku_pct      NUMERIC(6,2),                -- (preco_venda - custo) / preco_venda
    fonte               VARCHAR(30)     NOT NULL DEFAULT 'ZSD062',
    atualizado_em       TIMESTAMP       DEFAULT NOW(),
    UNIQUE(codigo_produto, ano, fonte)
);

CREATE INDEX IF NOT EXISTS idx_custo_prod_ano
    ON produto_custo_comercial(codigo_produto, ano);

COMMENT ON TABLE produto_custo_comercial IS
    'CMV unitário por SKU/ano. Fonte: ZSD062 Custo Comercial (SAP). '
    'Usado pelo dde_engine L12 = SUM(custo_comercial × qty vendida por NF).';

-- ============================================================
-- ALTER TABLE vendas — adicionar codigo_produto para JOIN com custo
-- Necessário para: _get_cmv() fazer JOIN vendas × produto_custo_comercial
-- ============================================================
ALTER TABLE vendas
    ADD COLUMN IF NOT EXISTS codigo_produto VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_vendas_codigo_produto
    ON vendas(codigo_produto);

COMMENT ON COLUMN vendas.codigo_produto IS
    'Código SAP do produto (ex: 7898403010101). JOIN com produto_custo_comercial.';

-- ============================================================
-- ALTER TABLE clientes — adicionar comissao_pct per-client
-- Golden Master: Coelho Diniz = 4.6%, não usar hardcoded 3%
-- ============================================================
ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS comissao_pct NUMERIC(5,2);

COMMENT ON COLUMN clientes.comissao_pct IS
    'Comissão % do cliente (ex: 4.6 para Coelho Diniz). Fonte: contrato. '
    'Engine usa /100 como decimal. Fallback = 3% se NULL.';

COMMIT;

-- ============================================================
-- VERIFICAÇÃO PÓS-MIGRATION
-- ============================================================
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name = 'produto_custo_comercial';
-- → Deve retornar 1 linha
--
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'vendas' AND column_name = 'codigo_produto';
-- → Deve retornar 1 linha
--
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'clientes' AND column_name = 'comissao_pct';
-- → Deve retornar 1 linha
