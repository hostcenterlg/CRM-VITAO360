"""add debitos_clientes and clientes/produtos enrichment

Revision ID: 05d36e618c52
Revises: 97b67bcd926f
Create Date: 2026-04-25 17:58:48.631665

Phase 1 — Sales Hunter ingestion preparation (GAP 2C).

Adds:
  - debitos_clientes table: open invoices (overdue/pending/paid) tracked from
    SAP Sales Hunter `debitos_*.xlsx` reports. CNPJ is VARCHAR(14) (R5).
  - clientes columns (4): total_debitos, pct_devolucao, total_devolucao,
    risco_devolucao — fed from devolucao_cliente_*.xlsx + debitos summary.
  - produtos columns (7): subcategoria, unidade_embalagem, qtd_por_embalagem,
    peso_bruto_kg, codigo_ncm, fat_total_historico, curva_abc_produto — fed
    from fat_produto_*.xlsx and fat_nf_det_*.xlsx.

Compatibility:
  Uses `op.batch_alter_table()` for ALTER COLUMN so the migration works on
  both SQLite (dev) and PostgreSQL (Neon prod). SQLite has no native ALTER
  TABLE ADD COLUMN with constraints; batch mode rebuilds the table.

R3 / R6 NOTES:
  - clientes / produtos pre-existing columns are NOT touched.
  - These are ENRICHMENT columns added at the END of each table — no
    breaking change for existing readers.

Two-Base (R1):
  debitos_clientes contains R$ values — rows are VENDA-side (overdue
  receivables). LOG-side never enters this table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05d36e618c52'
down_revision: Union[str, Sequence[str], None] = '97b67bcd926f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ------------------------------------------------------------------
    # 1) New table: debitos_clientes
    # ------------------------------------------------------------------
    op.create_table(
        "debitos_clientes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # R5: CNPJ string 14 chars zero-padded
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("cod_pedido", sa.String(length=50), nullable=True),
        sa.Column("nro_nfe", sa.String(length=50), nullable=True),
        sa.Column("parcela", sa.String(length=5), nullable=True),
        sa.Column("data_lancamento", sa.Date(), nullable=True),
        sa.Column("data_vencimento", sa.Date(), nullable=True),
        # NULL = unpaid (cliente devendo)
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        # R1: Two-Base — VENDA side: receivable amount in R$
        sa.Column("valor", sa.Float(), nullable=False),
        # Calculated: (today - data_vencimento).days when unpaid; 0 if paid
        sa.Column("dias_atraso", sa.Integer(), nullable=True),
        # 'PAGO' | 'VENCIDO' | 'A_VENCER'
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("fonte", sa.String(length=20), server_default="SAP", nullable=True),
        # R8: REAL/SINTETICO/ALUCINACAO — SAP source = REAL
        sa.Column(
            "classificacao_3tier",
            sa.String(length=15),
            server_default="REAL",
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_debitos_cnpj",
        "debitos_clientes",
        ["cnpj"],
        unique=False,
    )
    op.create_index(
        "idx_debitos_status",
        "debitos_clientes",
        ["status"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # 2) Enrich clientes — devolucao + debitos summary
    # ------------------------------------------------------------------
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "total_debitos",
                sa.Float(),
                server_default="0",
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("pct_devolucao", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("total_devolucao", sa.Float(), nullable=True))
        # 'BAIXO' (<5%) | 'MEDIO' (5-15%) | 'ALTO' (>15%)
        batch_op.add_column(
            sa.Column("risco_devolucao", sa.String(length=10), nullable=True)
        )

    # ------------------------------------------------------------------
    # 3) Enrich produtos — Sales Hunter SAP detail
    # ------------------------------------------------------------------
    with op.batch_alter_table("produtos", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("subcategoria", sa.String(length=100), nullable=True)
        )
        # SAP UM (e.g., "Caixa", "Fardo", "Unidade")
        batch_op.add_column(
            sa.Column("unidade_embalagem", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(
            sa.Column("qtd_por_embalagem", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("peso_bruto_kg", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("codigo_ncm", sa.String(length=10), nullable=True)
        )
        # Acumulated turnover (R$) — preparado para Curva ABC
        batch_op.add_column(
            sa.Column(
                "fat_total_historico",
                sa.Float(),
                server_default="0",
                nullable=True,
            )
        )
        # 'A' | 'B' | 'C' (recalculated from fat_total_historico)
        batch_op.add_column(
            sa.Column("curva_abc_produto", sa.String(length=1), nullable=True)
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse order: produtos -> clientes -> debitos_clientes
    with op.batch_alter_table("produtos", schema=None) as batch_op:
        batch_op.drop_column("curva_abc_produto")
        batch_op.drop_column("fat_total_historico")
        batch_op.drop_column("codigo_ncm")
        batch_op.drop_column("peso_bruto_kg")
        batch_op.drop_column("qtd_por_embalagem")
        batch_op.drop_column("unidade_embalagem")
        batch_op.drop_column("subcategoria")

    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_column("risco_devolucao")
        batch_op.drop_column("total_devolucao")
        batch_op.drop_column("pct_devolucao")
        batch_op.drop_column("total_debitos")

    op.drop_index("idx_debitos_status", table_name="debitos_clientes")
    op.drop_index("idx_debitos_cnpj", table_name="debitos_clientes")
    op.drop_table("debitos_clientes")
