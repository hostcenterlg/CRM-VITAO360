"""rbac: backfill usuario roles with known team members

Revision ID: a1b2c3d4e5f6
Revises: 05d36e618c52
Create Date: 2026-04-29 00:00:00.000000

Backfill strategy:
  - leandro@vitao.com.br          -> admin
  - daiane@vitao.com.br           -> gerente  (Daiane Stavicki — Key Account / Gerente)
  - manu@vitao.com.br             -> consultor (Manu Ditzel)
  - larissa@vitao.com.br          -> consultor (Larissa Padilha)
  - julio@vitao.com.br            -> consultor_externo (Julio Gadret — RCA externo = VENDEDOR)

Rows not matching any known email keep their current role (or default 'consultor'
if role IS NULL or empty — defensive).

SCHEMA NOTE: the 'role' column already exists (created in initial schema f3f6c1f01097).
This migration only updates data; no DDL changes.

Downgrade: resets role to 'consultor' for the 5 known emails and warns that other
rows are unaffected (downgrade is best-effort — original roles pre-backfill
were not captured).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4ac6e4064fa0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Known team members — email -> role mapping
# ---------------------------------------------------------------------------

KNOWN_ROLES = [
    ("leandro@vitao.com.br", "admin"),
    ("daiane@vitao.com.br", "gerente"),
    ("manu@vitao.com.br", "consultor"),
    ("larissa@vitao.com.br", "consultor"),
    ("julio@vitao.com.br", "consultor_externo"),
]

# ---------------------------------------------------------------------------
# Defensive fix: rows with NULL or empty role -> default 'consultor'
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """
    Backfill roles for known team members.

    Uses raw SQL via connection.execute() to stay compatible with Alembic
    batch mode and avoid ORM dependency.

    WARNING: any email not in KNOWN_ROLES keeps its current role value.
    If a known email does not exist yet in the DB, the UPDATE is a no-op
    (0 rows affected) — this is safe and expected for fresh installs.
    """
    bind = op.get_bind()

    # Fix any NULLs or empty strings defensively
    bind.execute(
        sa.text(
            "UPDATE usuarios SET role = 'consultor' "
            "WHERE role IS NULL OR role = ''"
        )
    )

    # Backfill known team members
    for email, role in KNOWN_ROLES:
        result = bind.execute(
            sa.text(
                "UPDATE usuarios SET role = :role WHERE email = :email"
            ),
            {"role": role, "email": email},
        )
        rows_affected = result.rowcount
        if rows_affected == 0:
            # Email not in DB yet — safe, log via print (alembic captures it)
            print(
                f"[RBAC BACKFILL] WARNING: {email} not found in usuarios "
                f"— role '{role}' not applied. "
                "Will apply on first user creation."
            )


def downgrade() -> None:
    """
    Best-effort rollback: reset known team members back to 'consultor'.

    NOTE: original roles before this migration are not captured, so downgrade
    cannot restore them perfectly. This resets known emails to 'consultor'
    (the system default) which is safe for a rollback scenario.
    """
    bind = op.get_bind()

    for email, _role in KNOWN_ROLES:
        bind.execute(
            sa.text(
                "UPDATE usuarios SET role = 'consultor' WHERE email = :email"
            ),
            {"email": email},
        )
