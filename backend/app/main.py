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
  /api/relatorios  — Motor XLSX: vendas, positivacao, atividades, inativos, metas

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
import time
import threading
from collections import defaultdict
from contextlib import asynccontextmanager

# Setup structured logging BEFORE any other imports that create loggers.
# JSON in production, human-readable in development.
from backend.app.logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.api.routes_agenda import router as agenda_router
from backend.app.api.routes_canais import router as canais_router
from backend.app.api.routes_pipeline import router as pipeline_router
from backend.app.api.routes_atendimentos import router as atendimentos_router
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_clientes import router as clientes_router
from backend.app.api.routes_dashboard import router as dashboard_router
from backend.app.api.routes_ia import router as ia_router
from backend.app.api.routes_import import router as import_router
from backend.app.api.routes_relatorios import router as relatorios_router
from backend.app.api.routes_inbox import router as inbox_router
from backend.app.api.routes_whatsapp import router as whatsapp_router
from backend.app.api.routes_motor import router as motor_router
from backend.app.api.routes_projecao import router as projecao_router
from backend.app.api.routes_redes import router as redes_router
from backend.app.api.routes_rnc import router as rnc_router
from backend.app.api.routes_sinaleiro import router as sinaleiro_router
from backend.app.api.routes_usuarios import router as usuarios_router
from backend.app.api.routes_vendas import router as vendas_router
from backend.app.api.routes_produtos import router as produtos_router
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
    try:
        # Dev convenience: auto-create tables without running migrations.
        # TODO: Replace with `alembic upgrade head` in production deployments.
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
    except Exception as e:
        logger.error("[STARTUP] DB init failed: %s", e)

    yield


# ---------------------------------------------------------------------------
# Security Headers Middleware (no external dependencies)
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects standard security headers into every HTTP response.

    Headers applied:
      - X-Content-Type-Options: nosniff       — prevents MIME-type sniffing
      - X-Frame-Options: DENY                 — prevents clickjacking
      - X-XSS-Protection: 1; mode=block       — legacy XSS filter
      - Strict-Transport-Security             — enforces HTTPS (31536000s = 1 year)
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: camera=(), microphone=(), geolocation=()
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response


# ---------------------------------------------------------------------------
# Rate Limiting Middleware (in-memory, no external dependencies)
# ---------------------------------------------------------------------------

class _RateLimitBucket:
    """
    Thread-safe sliding-window rate limiter per IP address.

    Uses a simple token-bucket approach with per-minute windows.
    Tracks request counts in 1-minute buckets keyed by IP.
    Automatically prunes expired entries to prevent memory leaks.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # {ip: [(timestamp, count_in_window)]}
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._last_prune: float = time.monotonic()
        self._prune_interval: float = 60.0  # prune stale IPs every 60s

    def is_allowed(self, ip: str, limit: int, window: float = 60.0) -> tuple[bool, int]:
        """
        Check if IP is within rate limit.

        Returns:
            (allowed, retry_after_seconds)
            - (True, 0) if request is allowed
            - (False, N) if rate limited, with N seconds until window resets
        """
        now = time.monotonic()

        with self._lock:
            # Periodic prune of stale entries (avoid unbounded growth)
            if now - self._last_prune > self._prune_interval:
                self._prune(now, window)
                self._last_prune = now

            # Filter to requests within the current window
            timestamps = self._requests[ip]
            cutoff = now - window
            # Remove expired timestamps
            self._requests[ip] = [ts for ts in timestamps if ts > cutoff]
            current = self._requests[ip]

            if len(current) >= limit:
                # Calculate when the oldest request in the window expires
                oldest = min(current) if current else now
                retry_after = int(oldest + window - now) + 1
                return False, max(retry_after, 1)

            current.append(now)
            return True, 0

    def _prune(self, now: float, window: float) -> None:
        """Remove IPs with no recent requests (called under lock)."""
        cutoff = now - window
        stale_ips = [
            ip for ip, timestamps in self._requests.items()
            if not timestamps or max(timestamps) < cutoff
        ]
        for ip in stale_ips:
            del self._requests[ip]


# Shared rate-limit state (module-level singleton)
_rate_limiter = _RateLimitBucket()

# Rate limit configuration
_RATE_LIMIT_GENERAL: int = 100      # requests/minute for authenticated endpoints
_RATE_LIMIT_AUTH: int = 10          # requests/minute for /api/auth/login (brute force)
_RATE_LIMIT_WINDOW: float = 60.0    # window in seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory per-IP rate limiter.

    Limits:
      - /api/auth/login:  10 req/min (brute force protection)
      - All other routes: 100 req/min

    Returns HTTP 429 with retry-after information when exceeded.
    """

    async def dispatch(self, request: Request, call_next):
        # Allow disabling rate limiting in test environments
        if os.getenv("TESTING", "").lower() in ("1", "true"):
            return await call_next(request)

        # Extract client IP (respect X-Forwarded-For behind reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Determine rate limit tier based on path
        path = request.url.path
        if path.rstrip("/") == "/api/auth/login":
            limit = _RATE_LIMIT_AUTH
            bucket_key = f"auth:{client_ip}"
        else:
            limit = _RATE_LIMIT_GENERAL
            bucket_key = f"general:{client_ip}"

        allowed, retry_after = _rate_limiter.is_allowed(
            bucket_key, limit, _RATE_LIMIT_WINDOW
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded | ip=%s path=%s limit=%d/min",
                client_ip, path, limit,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": f"Muitas requisicoes. Tente novamente em {retry_after} segundos."
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all — loga traceback mas nunca expoe ao cliente."""
    logger.error("Unhandled: %s", traceback.format_exc())
    return JSONResponse(status_code=500, content={"error": "Erro interno do servidor."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security headers on every response (clickjacking, MIME sniffing, HSTS)
app.add_middleware(SecurityHeadersMiddleware)

# Per-IP rate limiting (brute force protection on /api/auth/login)
app.add_middleware(RateLimitMiddleware)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(canais_router)
app.include_router(usuarios_router)
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
app.include_router(inbox_router)
app.include_router(whatsapp_router)
app.include_router(produtos_router)
app.include_router(relatorios_router)
app.include_router(pipeline_router)


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


