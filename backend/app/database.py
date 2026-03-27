"""
CRM VITAO360 — Configuração do banco de dados (SQLAlchemy)

SQLite para desenvolvimento local.
Troca para PostgreSQL em produção: definir DATABASE_URL no .env.

Regra R5: CNPJ sempre String(14), nunca Float.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# ---------------------------------------------------------------------------
# Caminho do banco SQLite — dentro de data/ para manter a organização do repo
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # backend/ -> repo root
_DATA_DIR = _PROJECT_ROOT / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

_DEFAULT_DB_URL = f"sqlite:///{_DATA_DIR / 'crm_vitao360.db'}"
DATABASE_URL: str = os.getenv("DATABASE_URL", "") or _DEFAULT_DB_URL

# Render retorna postgres:// mas SQLAlchemy 2.0 exige postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
_connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    # Necessário para SQLite em ambiente com múltiplas threads (FastAPI)
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=bool(os.getenv("DB_ECHO", "")),  # DB_ECHO=1 para debug SQL
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base declarativa — todos os models herdam daqui
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Dependency para injeção nas rotas FastAPI
# ---------------------------------------------------------------------------
def get_db():
    """Gera uma sessão de banco por request e garante fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
