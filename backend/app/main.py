"""
CRM VITAO360 — FastAPI Application

Ponto de entrada da API REST do CRM.

Routers registrados:
  /api/auth        — Login, refresh, me, CRUD usuarios
  /api/clientes    — CRUD + filtros de clientes, timeline por CNPJ
  /api/agenda      — Agendas diarias por consultor
  /api/dashboard   — KPIs, distribuicoes, projecao, funil
  /api/projecao    — Meta vs realizado por consultor (mensal + resumo)
  /api/vendas      — Registro e consulta de vendas (Two-Base: valor > 0)
  /api/atendimentos — Atendimentos e log de interacoes
  /api/sinaleiro   — Saude de clientes, penetracao de redes, recalculo batch
  /api/redes       — Listagem detalhada de redes com lojas e indicadores
  /api/motor       — Regras do Motor de Inteligencia Comercial (read-only, admin)
  /api/rnc         — Registros de Nao Conformidade (CRUD + ciclo de vida)
  /api/import      — Import pipeline: upload .xlsx Mercos/SAP, historico de jobs
  /api/ia          — Inteligencia Artificial: briefings pre-ligacao, mensagens WA, resumos semanais
  /api/whatsapp    — Integracao Deskrio: status conexoes, busca contato, envio mensagem WA

Startup:
  - Cria tabelas no SQLite se nao existirem (sem Alembic por ora)

CORS habilitado via variavel CORS_ORIGINS (padrão: localhost:3000).
Em Railway: definir CORS_ORIGINS com a URL pública do serviço "web".

Uso em desenvolvimento:
    uvicorn backend.app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_agenda import router as agenda_router
from backend.app.api.routes_atendimentos import router as atendimentos_router
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_clientes import router as clientes_router
from backend.app.api.routes_dashboard import router as dashboard_router
from backend.app.api.routes_ia import router as ia_router
from backend.app.api.routes_import import router as import_router
from backend.app.api.routes_whatsapp import router as whatsapp_router
from backend.app.api.routes_motor import router as motor_router
from backend.app.api.routes_projecao import router as projecao_router
from backend.app.api.routes_redes import router as redes_router
from backend.app.api.routes_rnc import router as rnc_router
from backend.app.api.routes_sinaleiro import router as sinaleiro_router
from backend.app.api.routes_vendas import router as vendas_router
from backend.app.database import Base, SessionLocal, engine
from backend.app.services.seed_auth import seed_regras_motor, seed_usuarios


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializacao do banco na subida da aplicacao:
      1. Cria todas as tabelas (sem Alembic por ora)
      2. Seed automatico de usuarios iniciais (idempotente)
      3. Seed automatico das regras do motor (idempotente)
    """
    Base.metadata.create_all(bind=engine)

    # Seed automatico — ambas as funcoes sao idempotentes
    db = SessionLocal()
    try:
        n_users = seed_usuarios(db)
        n_regras = seed_regras_motor(db)
        if n_users:
            logger.info("[SEED] %d usuario(s) criado(s)", n_users)
        if n_regras:
            logger.info("[SEED] %d regra(s) do motor criada(s)", n_regras)
    finally:
        db.close()

    yield
    # Nenhum cleanup necessario por ora


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
_ORIGINS_ENV = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
_ORIGINS = [o.strip() for o in _ORIGINS_ENV.split(",") if o.strip()]

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

app.include_router(auth_router)
app.include_router(clientes_router)
app.include_router(agenda_router)
app.include_router(dashboard_router)
app.include_router(projecao_router)
app.include_router(atendimentos_router)
app.include_router(vendas_router)
app.include_router(sinaleiro_router)
app.include_router(redes_router)
app.include_router(motor_router)
app.include_router(rnc_router)
app.include_router(import_router)
app.include_router(ia_router)
app.include_router(whatsapp_router)


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
