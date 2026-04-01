"""
Alembic migration environment for CRM VITAO360.

Reads DATABASE_URL from environment (same logic as backend/app/database.py).
Falls back to SQLite dev DB if not set.

All models are imported below so Alembic can detect schema changes via
autogenerate. Do NOT remove any import — missing imports = missing tables
in generated migrations.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Ensure the repo root (one level above backend/) is on sys.path so that
# "from backend.app.xxx import ..." resolves correctly when running alembic
# from inside the backend/ directory.
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parents[1]   # backend/
_REPO_ROOT = _BACKEND_DIR.parent                     # repo root
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Resolve DATABASE_URL — identical logic to backend/app/database.py
# ---------------------------------------------------------------------------
_DATA_DIR = _REPO_ROOT / "data"
_DEFAULT_DB_URL = f"sqlite:///{_DATA_DIR / 'crm_vitao360.db'}"

_db_url: str = os.getenv("DATABASE_URL", "") or _DEFAULT_DB_URL
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)

# Override the ini-file value with the runtime URL
config.set_main_option("sqlalchemy.url", _db_url)

# ---------------------------------------------------------------------------
# Import Base and ALL models so Alembic sees every table for autogenerate
# ---------------------------------------------------------------------------
from backend.app.database import Base  # noqa: E402

# Models must be imported for their tables to appear in Base.metadata.
# Order follows FK dependency chain documented in models/__init__.py.
import backend.app.models  # noqa: E402, F401  — registers all 12 models

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in offline mode (generates SQL without a live connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render ALTER TABLE for column changes rather than drop/recreate
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode (uses a live DB connection)."""
    _connect_args: dict = {}
    if _db_url.startswith("sqlite"):
        _connect_args = {"check_same_thread": False}

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
