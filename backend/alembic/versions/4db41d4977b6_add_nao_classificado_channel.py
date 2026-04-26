"""add NAO_CLASSIFICADO channel (id=8) for orphan clients

Revision ID: 4db41d4977b6
Revises: d2d415fcc93e
Create Date: 2026-04-26 10:46:13.328093

DECISAO L3 (aprovado Leandro 26/Abr/2026) — B1.4-EXEC:
  Criar canal NAO_CLASSIFICADO para absorver 84 clientes orfaos
  (canal_id IS NULL) que nao pertencem a DAIANE nem a nenhum canal SAP.

  Status ADMIN_ONLY: invisivel para consultores via ACL (usuario_canal).
  Admin ve automaticamente (get_user_canal_ids retorna None para admin
  e get_user_canal_ids_strict faz SELECT id FROM canais — inclui todos).
  Consultores: NAO recebem ACL para canal 8 -> list[int] nao contem 8.

  Downgrade:
    1. Reatribuir canal_id=NULL nos clientes do canal 8
    2. DELETE canal 8
  (ordem obrigatoria para nao violar FK ondelete=SET NULL — mas como
   SQLite nao aplica FKs por padrao, seguranca adicional de fazer a
   limpeza manual antes do DELETE.)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4db41d4977b6"
down_revision: Union[str, Sequence[str], None] = "d2d415fcc93e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Canal seed — referencia para upgrade e downgrade
CANAL_NAO_CLASSIFICADO = {
    "id": 8,
    "nome": "NAO_CLASSIFICADO",
    "status": "ADMIN_ONLY",
    "descricao": "Clientes sem canal SAP identificado — visivel apenas para admin",
}


def upgrade() -> None:
    """Insere canal NAO_CLASSIFICADO (id=8)."""
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO canais (id, nome, status, descricao) "
            "VALUES (:id, :nome, :status, :descricao)"
        ),
        CANAL_NAO_CLASSIFICADO,
    )


def downgrade() -> None:
    """Remove canal NAO_CLASSIFICADO.

    ORDEM OBRIGATORIA:
      1. Retorna clientes do canal 8 para NULL (evita orfaos com FK invalida)
      2. Deleta o canal
    """
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE clientes SET canal_id = NULL WHERE canal_id = 8")
    )
    bind.execute(
        sa.text("DELETE FROM canais WHERE id = 8")
    )
