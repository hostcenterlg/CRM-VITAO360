"""dedup venda_itens and add unique constraint

Revision ID: 4ac6e4064fa0
Revises: 4db41d4977b6
Create Date: 2026-04-29 17:25:20.147258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ac6e4064fa0'
down_revision: Union[str, Sequence[str], None] = '4db41d4977b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove 2.922 linhas duplicadas em venda_itens e adiciona UNIQUE constraint.

    Estrategia: manter a linha de menor id por par (venda_id, produto_id),
    deletar todas as demais. Em seguida criar unique constraint para impedir
    recorrencia.

    Rollback de dados: apenas via pg_dump em data/backups/venda_itens_pre_dedup_*.json
    O downgrade() abaixo so dropa a constraint — nao restaura linhas deletadas.
    """
    # 1. Dedup: mantém MIN(id) por par, deleta extras
    op.execute("""
        DELETE FROM venda_itens vi
        WHERE vi.id NOT IN (
            SELECT MIN(id) FROM venda_itens
            GROUP BY venda_id, produto_id
        )
    """)
    # 2. Constraint: impede futuras duplicatas
    op.create_unique_constraint(
        "uq_venda_itens_venda_produto",
        "venda_itens",
        ["venda_id", "produto_id"],
    )


def downgrade() -> None:
    """Remove a unique constraint. Linhas deletadas NÃO são restauradas automaticamente.
    Para rollback completo de dados: restaurar de data/backups/venda_itens_pre_dedup_*.json
    """
    op.drop_constraint("uq_venda_itens_venda_produto", "venda_itens", type_="unique")
