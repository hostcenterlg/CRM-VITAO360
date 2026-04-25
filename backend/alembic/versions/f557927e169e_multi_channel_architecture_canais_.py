"""multi-channel architecture: canais + usuario_canal + clientes.canal_id

Revision ID: f557927e169e
Revises: 05d2bb411591
Create Date: 2026-04-25 19:33:43.222824

Implements DECISAO L3 (aprovada Leandro 25/Abr/2026): arquitetura multi-canal.

- Tabela canais: 7 registros oficiais com seed inicial
    INTERNO       ATIVO     (canal funcional VITAO)
    FOOD_SERVICE  ATIVO     (canal foco operacional atual)
    DIRETO        EM_BREVE  (Manu/Larissa/Daiane/Julio — proxima onda)
    INDIRETO      EM_BREVE  (distribuidores)
    FARMA         EM_BREVE  (farmacias/drogarias)
    BODY          EM_BREVE  (lojas body/academia)
    DIGITAL       EM_BREVE  (e-commerce/B2C)

- Tabela usuario_canal: N:N entre usuarios e canais. Admin define quem ve
    quais canais via essa associacao.

- clientes.canal_id: FK -> canais.id, nullable (legados sem classificacao).
    Backfilled via clientes.canal (string criada na migracao anterior),
    depois clientes.canal eh dropada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f557927e169e"
down_revision: Union[str, Sequence[str], None] = "05d2bb411591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Seed dos 7 canais — referencia para upgrade e downgrade
CANAIS_SEED = [
    ("INTERNO",      "ATIVO",    "Canal funcional interno VITAO"),
    ("FOOD_SERVICE", "ATIVO",    "Food service (industria, distribuidor, varejo)"),
    ("DIRETO",       "EM_BREVE", "Direto: redes, atacarejos (Manu/Larissa/Daiane/Julio)"),
    ("INDIRETO",     "EM_BREVE", "Distribuidores indiretos regionais"),
    ("FARMA",        "EM_BREVE", "Farmacias e drogarias"),
    ("BODY",         "EM_BREVE", "Lojas body / academias"),
    ("DIGITAL",      "EM_BREVE", "E-commerce e B2C digital"),
]


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Tabela canais
    op.create_table(
        "canais",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("nome", sa.String(length=20), nullable=False, unique=True),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="EM_BREVE"),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_canais_nome", "canais", ["nome"], unique=True)
    op.create_index("idx_canais_status", "canais", ["status"])

    # 2. Tabela usuario_canal (N:N)
    op.create_table(
        "usuario_canal",
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("canal_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("usuario_id", "canal_id"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["canal_id"], ["canais.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_usuario_canal_usuario", "usuario_canal", ["usuario_id"])
    op.create_index("idx_usuario_canal_canal", "usuario_canal", ["canal_id"])

    # 3. Seed dos 7 canais
    canais_table = sa.table(
        "canais",
        sa.column("nome", sa.String),
        sa.column("status", sa.String),
        sa.column("descricao", sa.String),
    )
    op.bulk_insert(
        canais_table,
        [
            {"nome": nome, "status": status, "descricao": desc}
            for nome, status, desc in CANAIS_SEED
        ],
    )

    # 4. Adiciona clientes.canal_id (FK)
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("canal_id", sa.Integer(), nullable=True))
        batch_op.create_index("idx_clientes_canal_id", ["canal_id"])
        batch_op.create_foreign_key(
            "fk_clientes_canal_id",
            "canais",
            ["canal_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # 5. Backfill: copia clientes.canal (string) -> clientes.canal_id (FK)
    op.execute(
        """
        UPDATE clientes
        SET canal_id = (
            SELECT id FROM canais WHERE canais.nome = clientes.canal
        )
        WHERE clientes.canal IS NOT NULL
        """
    )

    # 6. Drop clientes.canal (string) — substituida pela FK
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_index("idx_clientes_canal")
        batch_op.drop_column("canal")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Recria clientes.canal (string) e copia de volta
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("canal", sa.String(length=20), nullable=True))
        batch_op.create_index("idx_clientes_canal", ["canal"])

    op.execute(
        """
        UPDATE clientes
        SET canal = (
            SELECT nome FROM canais WHERE canais.id = clientes.canal_id
        )
        WHERE clientes.canal_id IS NOT NULL
        """
    )

    # 2. Remove canal_id (FK)
    with op.batch_alter_table("clientes", schema=None) as batch_op:
        batch_op.drop_constraint("fk_clientes_canal_id", type_="foreignkey")
        batch_op.drop_index("idx_clientes_canal_id")
        batch_op.drop_column("canal_id")

    # 3. Drop usuario_canal
    op.drop_index("idx_usuario_canal_canal", table_name="usuario_canal")
    op.drop_index("idx_usuario_canal_usuario", table_name="usuario_canal")
    op.drop_table("usuario_canal")

    # 4. Drop canais
    op.drop_index("idx_canais_status", table_name="canais")
    op.drop_index("idx_canais_nome", table_name="canais")
    op.drop_table("canais")
