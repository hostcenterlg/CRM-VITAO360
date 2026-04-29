-- ============================================================
-- MIGRATION DDE #001 — Schema Cascata P&L por Cliente
-- CRM VITAO360 — Neon PostgreSQL
-- Spec: SPEC_DDE_CASCATA_REAL.md v1.0
-- Data: 29/04/2026
-- ============================================================
-- INSTRUÇÕES:
--   1. Rodar no Neon Console ou via psql conectado ao banco prod
--   2. Verificar que tabelas clientes e vendas existem ANTES
--   3. Idempotente: usa IF NOT EXISTS / ADD COLUMN IF NOT EXISTS
-- ============================================================

BEGIN;

-- ============================================================
-- TABELA 1: cliente_frete_mensal
-- Fonte: Upload CFO "Frete por Cliente.xlsx"
-- Alimenta: L14 (Frete CT-e por cliente)
-- ============================================================
CREATE TABLE IF NOT EXISTS cliente_frete_mensal (
    id              SERIAL PRIMARY KEY,
    cnpj            VARCHAR(14)     NOT NULL,
    ano             INT             NOT NULL,
    mes             INT             NOT NULL,
    qtd_ctes        INT,
    valor_brl       NUMERIC(14,2)   NOT NULL,
    fonte           VARCHAR(20)     NOT NULL DEFAULT 'LOG_UPLOAD',
    classificacao_3tier VARCHAR(10) NOT NULL DEFAULT 'REAL',
    created_at      TIMESTAMP       DEFAULT NOW(),
    UNIQUE(cnpj, ano, mes, fonte)
);

CREATE INDEX IF NOT EXISTS idx_frete_cnpj
    ON cliente_frete_mensal(cnpj, ano);

COMMENT ON TABLE cliente_frete_mensal IS
    'L14 — Frete CT-e mensal por cliente. Fonte: upload CFO ou integração logística.';

-- ============================================================
-- TABELA 2: cliente_verba_anual
-- Fonte: Upload CFO "Controle de Contratos.xlsx" + "Verbas.xlsx"
-- Alimenta: L16 (Verbas contratos + efetivadas)
-- ============================================================
CREATE TABLE IF NOT EXISTS cliente_verba_anual (
    id              SERIAL PRIMARY KEY,
    cnpj            VARCHAR(14)     NOT NULL,
    ano             INT             NOT NULL,
    tipo            VARCHAR(20)     NOT NULL,   -- 'CONTRATO' | 'EFETIVADA'
    valor_brl       NUMERIC(14,2)   NOT NULL,
    desc_total_pct  NUMERIC(5,2),               -- só tipo='CONTRATO'
    inicio_vigencia DATE,
    fim_vigencia    DATE,
    fonte           VARCHAR(20)     NOT NULL,
    classificacao_3tier VARCHAR(10) NOT NULL DEFAULT 'REAL',
    observacao      TEXT,
    created_at      TIMESTAMP       DEFAULT NOW(),
    UNIQUE(cnpj, ano, tipo, fonte)
);

CREATE INDEX IF NOT EXISTS idx_verba_cnpj
    ON cliente_verba_anual(cnpj, ano);

COMMENT ON TABLE cliente_verba_anual IS
    'L16 — Verba anual (contrato e efetivada). Tipos: CONTRATO, EFETIVADA.';

-- ============================================================
-- TABELA 3: cliente_promotor_mensal
-- Fonte: Upload CFO "Despesas Clientes.xlsx"
-- Alimenta: L17 (Promotor PDV)
-- ============================================================
CREATE TABLE IF NOT EXISTS cliente_promotor_mensal (
    id              SERIAL PRIMARY KEY,
    cnpj            VARCHAR(14)     NOT NULL,
    agencia         VARCHAR(80),
    ano             INT             NOT NULL,
    mes             INT             NOT NULL,
    valor_brl       NUMERIC(14,2)   NOT NULL,
    fonte           VARCHAR(20)     NOT NULL DEFAULT 'LOG_UPLOAD',
    classificacao_3tier VARCHAR(10) NOT NULL DEFAULT 'REAL',
    created_at      TIMESTAMP       DEFAULT NOW(),
    UNIQUE(cnpj, agencia, ano, mes)
);

CREATE INDEX IF NOT EXISTS idx_promotor_cnpj
    ON cliente_promotor_mensal(cnpj, ano);

COMMENT ON TABLE cliente_promotor_mensal IS
    'L17 — Custo promotor PDV mensal por agência. Fonte: upload CFO.';

-- ============================================================
-- TABELA 4: cliente_dre_periodo
-- Cache da cascata DDE, recalculado pelo engine
-- Alimenta: Todos os endpoints /api/dde/*
-- ============================================================
CREATE TABLE IF NOT EXISTS cliente_dre_periodo (
    id              SERIAL PRIMARY KEY,
    cnpj            VARCHAR(14)     NOT NULL,
    ano             INT             NOT NULL,
    mes             INT,                        -- NULL = consolidado anual
    linha           VARCHAR(10)     NOT NULL,   -- 'L1','L11','L21','I2'...
    conta           VARCHAR(80)     NOT NULL,   -- nome legível da linha
    valor_brl       NUMERIC(14,2),              -- NULL se PENDENTE
    pct_sobre_receita NUMERIC(6,3),
    fonte           VARCHAR(20),
    classificacao_3tier VARCHAR(10),             -- REAL|SINTETICO|PENDENTE|NULL
    fase            VARCHAR(2),                 -- 'A'|'B'|'C'
    observacao      TEXT,
    calculado_em    TIMESTAMP       DEFAULT NOW(),
    UNIQUE(cnpj, ano, mes, linha)
);

CREATE INDEX IF NOT EXISTS idx_dre_cnpj_ano
    ON cliente_dre_periodo(cnpj, ano);

CREATE INDEX IF NOT EXISTS idx_dre_linha
    ON cliente_dre_periodo(linha, ano);

COMMENT ON TABLE cliente_dre_periodo IS
    'Cache da cascata P&L (DDE) por cliente/período. Recalculado pelo dde_engine.py.';

-- ============================================================
-- ALTER TABLE clientes — 4 campos do Sales Hunter (D1)
-- Alimenta: L5 (desc comercial), L6 (desc financeiro),
--           L7 (bonificação), L2/L8 (IPI)
-- ============================================================
ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS desc_comercial_pct   NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS desc_financeiro_pct   NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS total_bonificacao     NUMERIC(14,2),
    ADD COLUMN IF NOT EXISTS ipi_total             NUMERIC(14,2);

COMMENT ON COLUMN clientes.desc_comercial_pct IS
    'D1 — % desconto comercial médio do cliente (Sales Hunter fat_cliente col 7)';
COMMENT ON COLUMN clientes.desc_financeiro_pct IS
    'D1 — % desconto financeiro médio (Sales Hunter fat_cliente col 8)';
COMMENT ON COLUMN clientes.total_bonificacao IS
    'D1 — Total bonificações acumulado (Sales Hunter fat_cliente col 16)';
COMMENT ON COLUMN clientes.ipi_total IS
    'D1 — Total IPI acumulado (Sales Hunter pedidos_produto col 19)';

-- ============================================================
-- ALTER TABLE vendas — granularidade mensal para cascata
-- Alimenta: L2, L5, L6, L7, L8 por venda individual
-- ============================================================
ALTER TABLE vendas
    ADD COLUMN IF NOT EXISTS ipi_total             NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS desconto_comercial    NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS desconto_financeiro   NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS bonificacao           NUMERIC(12,2);

COMMENT ON COLUMN vendas.ipi_total IS
    'IPI por venda/NF (Sales Hunter pedidos_produto col 19)';
COMMENT ON COLUMN vendas.desconto_comercial IS
    'Desconto comercial por venda (preco_tabela - preco_pratico) × qtd';
COMMENT ON COLUMN vendas.desconto_financeiro IS
    'Desconto financeiro por venda (Sales Hunter fat_cliente col 8)';
COMMENT ON COLUMN vendas.bonificacao IS
    'Bonificação por venda (Sales Hunter fat_cliente col 16)';

-- ============================================================
-- VIEW auxiliar: resumo DDE por cliente (facilita queries)
-- ============================================================
CREATE OR REPLACE VIEW v_dde_resumo_cliente AS
SELECT
    d.cnpj,
    d.ano,
    d.mes,
    MAX(CASE WHEN d.linha = 'L1'  THEN d.valor_brl END) AS faturamento_bruto,
    MAX(CASE WHEN d.linha = 'L3'  THEN d.valor_brl END) AS receita_bruta,
    MAX(CASE WHEN d.linha = 'L4'  THEN d.valor_brl END) AS devolucoes,
    MAX(CASE WHEN d.linha = 'L11' THEN d.valor_brl END) AS receita_liquida,
    MAX(CASE WHEN d.linha = 'L13' THEN d.valor_brl END) AS margem_bruta,
    MAX(CASE WHEN d.linha = 'L14' THEN d.valor_brl END) AS frete,
    MAX(CASE WHEN d.linha = 'L15' THEN d.valor_brl END) AS comissao,
    MAX(CASE WHEN d.linha = 'L16' THEN d.valor_brl END) AS verbas,
    MAX(CASE WHEN d.linha = 'L17' THEN d.valor_brl END) AS promotor,
    MAX(CASE WHEN d.linha = 'L19' THEN d.valor_brl END) AS inadimplencia,
    MAX(CASE WHEN d.linha = 'L20' THEN d.valor_brl END) AS custo_financeiro,
    MAX(CASE WHEN d.linha = 'L21' THEN d.valor_brl END) AS margem_contribuicao,
    MAX(CASE WHEN d.linha = 'I2'  THEN d.pct_sobre_receita END) AS margem_contribuicao_pct,
    MAX(CASE WHEN d.linha = 'I4'  THEN d.pct_sobre_receita END) AS custo_servir_pct,
    MAX(CASE WHEN d.linha = 'I7'  THEN d.pct_sobre_receita END) AS devolucao_pct,
    MAX(CASE WHEN d.linha = 'I8'  THEN d.valor_brl END)         AS aging_medio_dso,
    MAX(CASE WHEN d.linha = 'I9'  THEN d.valor_brl END)         AS score_saude
FROM cliente_dre_periodo d
GROUP BY d.cnpj, d.ano, d.mes;

COMMENT ON VIEW v_dde_resumo_cliente IS
    'Pivô da cascata DDE — uma linha por cliente/período com todas as métricas principais.';

-- ============================================================
-- GRANT (ajustar role conforme ambiente)
-- ============================================================
-- GRANT SELECT, INSERT, UPDATE ON cliente_frete_mensal TO vitao_api;
-- GRANT SELECT, INSERT, UPDATE ON cliente_verba_anual TO vitao_api;
-- GRANT SELECT, INSERT, UPDATE ON cliente_promotor_mensal TO vitao_api;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cliente_dre_periodo TO vitao_api;
-- GRANT SELECT ON v_dde_resumo_cliente TO vitao_api;

COMMIT;

-- ============================================================
-- VERIFICAÇÃO PÓS-MIGRATION
-- ============================================================
-- Rodar após o COMMIT para confirmar:
--
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN (
--   'cliente_frete_mensal','cliente_verba_anual',
--   'cliente_promotor_mensal','cliente_dre_periodo'
-- );
-- → Deve retornar 4 linhas
--
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'clientes'
-- AND column_name IN ('desc_comercial_pct','desc_financeiro_pct','total_bonificacao','ipi_total');
-- → Deve retornar 4 linhas
--
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'vendas'
-- AND column_name IN ('ipi_total','desconto_comercial','desconto_financeiro','bonificacao');
-- → Deve retornar 4 linhas
