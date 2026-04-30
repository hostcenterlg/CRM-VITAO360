"""[MIKE] add DDE tables + D1 ALTERs on clientes/vendas

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-29 00:00:00.000000

Onda 1 — Schema PostgreSQL para DDE (Demonstração de Desempenho Econômico):
  - CREATE TABLE cliente_frete_mensal     (DDE L14 — Frete CT-e)
  - CREATE TABLE cliente_verba_anual      (DDE L16 — Verbas contratos)
  - CREATE TABLE cliente_promotor_mensal  (DDE L17 — Promotor PDV)
  - CREATE TABLE cliente_dre_periodo      (DDE cache cascata L1-L25, I1-I9)
  - ALTER TABLE clientes ADD COLUMNS D1   (desc_comercial_pct, desc_financeiro_pct,
                                           total_bonificacao, ipi_total)
  - ALTER TABLE vendas ADD COLUMNS D1     (ipi_total, desconto_comercial,
                                           desconto_financeiro, bonificacao)
  - CREATE INDEX idx_frete_cnpj, idx_dre_cnpj_ano

REGRAS:
  R5  — cnpj: VARCHAR(14) em todas as tabelas novas.
  R8  — coluna classificacao com 3-tier (REAL|SINTETICO|PENDENTE).
  R12 — tabelas DDE sem canal_id (filtro via JOIN clientes.canal_id).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria 4 tabelas DDE + adiciona colunas D1 em clientes e vendas."""

    # ------------------------------------------------------------------
    # T1 — cliente_frete_mensal (DDE L14 — Frete CT-e mensal por cliente)
    # ------------------------------------------------------------------
    op.create_table(
        "cliente_frete_mensal",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("qtd_ctes", sa.Integer(), nullable=True),
        sa.Column("valor_brl", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("fonte", sa.String(length=20), nullable=False, server_default="LOG_UPLOAD"),
        sa.Column("classificacao", sa.String(length=10), nullable=False, server_default="REAL"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj", "ano", "mes", "fonte", name="uq_frete_cnpj_ano_mes_fonte"),
    )
    op.create_index("idx_frete_cnpj", "cliente_frete_mensal", ["cnpj", "ano"], unique=False)

    # ------------------------------------------------------------------
    # T2 — cliente_verba_anual (DDE L16 — Verbas contrato + efetivada)
    # ------------------------------------------------------------------
    op.create_table(
        "cliente_verba_anual",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("valor_brl", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("desc_total_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("inicio_vigencia", sa.Date(), nullable=True),
        sa.Column("fim_vigencia", sa.Date(), nullable=True),
        sa.Column("fonte", sa.String(length=20), nullable=False),
        sa.Column("classificacao", sa.String(length=10), nullable=False, server_default="REAL"),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj", "ano", "tipo", "fonte", name="uq_verba_cnpj_ano_tipo_fonte"),
    )

    # ------------------------------------------------------------------
    # T3 — cliente_promotor_mensal (DDE L17 — Promotor PDV mensal)
    # ------------------------------------------------------------------
    op.create_table(
        "cliente_promotor_mensal",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("agencia", sa.String(length=80), nullable=True),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("valor_brl", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("fonte", sa.String(length=20), nullable=False, server_default="LOG_UPLOAD"),
        sa.Column("classificacao", sa.String(length=10), nullable=False, server_default="REAL"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj", "agencia", "ano", "mes", name="uq_promotor_cnpj_agencia_ano_mes"),
    )

    # ------------------------------------------------------------------
    # T4 — cliente_dre_periodo (DDE cache cascata — recalculado pelo engine)
    # ------------------------------------------------------------------
    op.create_table(
        "cliente_dre_periodo",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=True),  # NULL = anual
        sa.Column("linha", sa.String(length=10), nullable=False),
        sa.Column("conta", sa.String(length=80), nullable=False),
        sa.Column("valor_brl", sa.Numeric(precision=14, scale=2), nullable=True),  # NULL = PENDENTE
        sa.Column("pct_sobre_receita", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column("fonte", sa.String(length=20), nullable=True),
        sa.Column("classificacao", sa.String(length=10), nullable=True),
        sa.Column("fase", sa.String(length=2), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("calculado_em", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj", "ano", "mes", "linha", name="uq_dre_cnpj_ano_mes_linha"),
    )
    op.create_index("idx_dre_cnpj_ano", "cliente_dre_periodo", ["cnpj", "ano"], unique=False)

    # ------------------------------------------------------------------
    # ALTER TABLE clientes — D1: 4 campos Sales Hunter fat_cliente
    # ------------------------------------------------------------------
    op.add_column("clientes", sa.Column("desc_comercial_pct", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column("clientes", sa.Column("desc_financeiro_pct", sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column("clientes", sa.Column("total_bonificacao", sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column("clientes", sa.Column("ipi_total", sa.Numeric(precision=14, scale=2), nullable=True))

    # ------------------------------------------------------------------
    # ALTER TABLE vendas — D1: 4 campos Sales Hunter fat_nf_det
    # ------------------------------------------------------------------
    op.add_column("vendas", sa.Column("ipi_total", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("vendas", sa.Column("desconto_comercial", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("vendas", sa.Column("desconto_financeiro", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("vendas", sa.Column("bonificacao", sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    """Remove tudo criado no upgrade — totalmente reversível."""

    # ------------------------------------------------------------------
    # DROP colunas D1 de vendas
    # ------------------------------------------------------------------
    op.drop_column("vendas", "bonificacao")
    op.drop_column("vendas", "desconto_financeiro")
    op.drop_column("vendas", "desconto_comercial")
    op.drop_column("vendas", "ipi_total")

    # ------------------------------------------------------------------
    # DROP colunas D1 de clientes
    # ------------------------------------------------------------------
    op.drop_column("clientes", "ipi_total")
    op.drop_column("clientes", "total_bonificacao")
    op.drop_column("clientes", "desc_financeiro_pct")
    op.drop_column("clientes", "desc_comercial_pct")

    # ------------------------------------------------------------------
    # DROP tabelas DDE (ordem inversa da criação para satisfazer FK lógicas)
    # ------------------------------------------------------------------
    op.drop_index("idx_dre_cnpj_ano", table_name="cliente_dre_periodo")
    op.drop_table("cliente_dre_periodo")

    op.drop_table("cliente_promotor_mensal")

    op.drop_table("cliente_verba_anual")

    op.drop_index("idx_frete_cnpj", table_name="cliente_frete_mensal")
    op.drop_table("cliente_frete_mensal")
