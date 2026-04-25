"""add status_pedido + condicao_pagamento + observacao to vendas

Revision ID: d2d415fcc93e
Revises: f557927e169e
Create Date: 2026-04-25 20:51:55.648874

Resolves schema drift: backend/app/models/venda.py declares
status_pedido, condicao_pagamento and observacao but the previous
initial migration (f3f6c1f01097) created the vendas table without
them. SELECT statements via the ORM raise OperationalError because
the columns do not exist.

Backfills status_pedido='FATURADO' for existing SAP-sourced rows
(vendas inserted by ingest_sales_hunter.py before status was a NOT
NULL column). Other rows default to 'DIGITADO'.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2d415fcc93e"
down_revision: Union[str, Sequence[str], None] = "f557927e169e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("vendas", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "status_pedido",
                sa.String(length=20),
                nullable=False,
                server_default="DIGITADO",
            )
        )
        batch_op.add_column(
            sa.Column("condicao_pagamento", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(sa.Column("observacao", sa.Text(), nullable=True))
        batch_op.create_index("ix_vendas_status_pedido", ["status_pedido"])

    # Backfill: vendas SAP existentes ja foram faturadas
    op.execute(
        """
        UPDATE vendas
        SET status_pedido = 'FATURADO'
        WHERE fonte = 'SAP' AND status_pedido = 'DIGITADO'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("vendas", schema=None) as batch_op:
        batch_op.drop_index("ix_vendas_status_pedido")
        batch_op.drop_column("observacao")
        batch_op.drop_column("condicao_pagamento")
        batch_op.drop_column("status_pedido")
