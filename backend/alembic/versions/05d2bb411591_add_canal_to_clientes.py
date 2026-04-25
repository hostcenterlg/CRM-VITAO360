"""add canal to clientes

Revision ID: 05d2bb411591
Revises: 05d36e618c52
Create Date: 2026-04-25 19:22:05.512733

Adds the SAP sales channel dimension to clientes. Source of truth:
fat_cliente.grupo (e.g. "06 - DIRETO - CONDOR - PR") plus a fallback
to fat_cliente.canal_venda prefix sigla (DG/DI/FA/IN/FO/VI).

Canonical values: DIRETO, INDIRETO, INTERNO, FOOD_SERVICE, FARMA,
BODY, DIGITAL, NAO_APLICAVEL, OUTROS.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05d2bb411591'
down_revision: Union[str, Sequence[str], None] = '05d36e618c52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("canal", sa.String(length=20), nullable=True))
    op.create_index("idx_clientes_canal", "clientes", ["canal"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_clientes_canal", table_name="clientes")
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_column("canal")
