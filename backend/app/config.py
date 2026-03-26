"""
CRM VITAO360 — Configuracao centralizada via variaveis de ambiente.

Usa pydantic-settings para carregar e validar configuracoes do .env.
Todas as configuracoes ficam acessiveis via `from backend.app.config import settings`.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuracoes globais do CRM VITAO360.

    Ordem de resolucao de valores:
      1. Variavel de ambiente do sistema operacional
      2. Arquivo .env na raiz do projeto
      3. Valor padrao definido aqui
    """

    # ------------------------------------------------------------------
    # Banco de dados
    # ------------------------------------------------------------------
    database_url: str = ""  # Sobrescrever via DATABASE_URL no .env
    db_echo: bool = False   # DB_ECHO=1 para logar todas as queries SQL

    # ------------------------------------------------------------------
    # JWT — autenticacao
    # ------------------------------------------------------------------
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    # 8 horas — equivale a uma jornada comercial completa
    jwt_access_token_expire_minutes: int = 480
    # 30 dias — permite renovacao automatica sem novo login
    jwt_refresh_token_expire_days: int = 30

    # ------------------------------------------------------------------
    # CORS — frontend Next.js
    # ------------------------------------------------------------------
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001"

    # ------------------------------------------------------------------
    # Deskrio — integracao WhatsApp (futuro)
    # ------------------------------------------------------------------
    deskrio_api_key: str = ""
    deskrio_base_url: str = "https://api.deskrio.com.br/v1"

    # ------------------------------------------------------------------
    # Constantes de negocio CRM VITAO360
    # Regra R7: faturamento baseline corrigido em 2026-03-23
    # ------------------------------------------------------------------
    faturamento_baseline: float = 2_091_000.0
    faturamento_tolerancia: float = 0.005  # 0.5% de tolerancia
    max_atendimentos_padrao: int = 40      # Limite diario consultores
    max_atendimentos_daiane: int = 20      # Limite Daiane (Key Account)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Ignora variaveis do .env nao declaradas aqui
    }


# Instancia global — importar de qualquer modulo com:
#   from backend.app.config import settings
settings = Settings()
