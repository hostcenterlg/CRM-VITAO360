"""
CRM VITAO360 — FastAPI Application

Ponto de entrada da API REST do CRM.

Routers registrados:
  /api/clientes    — CRUD + filtros de clientes
  /api/agenda      — Agendas diárias por consultor
  /api/dashboard   — KPIs, distribuições, projeção

Startup:
  - Cria tabelas no SQLite se não existirem (sem Alembic por ora)

CORS habilitado para o frontend Next.js em localhost:3000.

Uso em desenvolvimento:
    uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_agenda import router as agenda_router
from backend.app.api.routes_clientes import router as clientes_router
from backend.app.api.routes_dashboard import router as dashboard_router
from backend.app.database import Base, engine


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria tabelas no banco na inicialização se não existirem."""
    Base.metadata.create_all(bind=engine)
    yield
    # Nenhum cleanup necessário por ora


# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CRM VITAO360 API",
    description=(
        "API REST do CRM Inteligente VITAO360 — distribuidora B2B de alimentos naturais.\n\n"
        "Expõe clientes, agendas e KPIs produzidos pelo Motor de Regras (pipeline Python)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — frontend Next.js em dev (porta 3000) e produção
# ---------------------------------------------------------------------------
_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "")
_ORIGINS = (
    [o.strip() for o in _ORIGINS_ENV.split(",") if o.strip()]
    if _ORIGINS_ENV
    else [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(clientes_router)
app.include_router(agenda_router)
app.include_router(dashboard_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Sistema"], summary="Health check")
def health():
    """
    Verifica se a API está no ar.
    Retorna status, versão e nome do banco ativo.
    """
    from backend.app.database import DATABASE_URL

    return {
        "status": "ok",
        "versao": "1.0.0",
        "sistema": "CRM VITAO360",
        "banco": DATABASE_URL.split("///")[-1] if "sqlite" in DATABASE_URL else "postgresql",
    }


@app.get("/", tags=["Sistema"], include_in_schema=False)
def root():
    return {"mensagem": "CRM VITAO360 API — acesse /docs para a documentação."}
