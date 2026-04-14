"""
CRM VITAO360 — Cache em memória com TTL (sem Redis, sem dependência externa).

Design:
  - Thread-safe via threading.Lock
  - TTL por entrada (time-to-live em segundos)
  - Decorador @cached(ttl_seconds=N) para endpoints FastAPI
  - Cache key = path + query params (configurável)
  - Invalidação manual por chave ou limpeza total
  - Prune passivo de entradas expiradas para evitar vazamento de memória

Uso:
    from backend.app.utils.cache import cache, cached

    # Como decorador em um endpoint FastAPI:
    @router.get("/kpis")
    @cached(ttl_seconds=60)
    def kpis(...):
        ...

    # Invalidação manual (ex.: após POST /vendas):
    cache.invalidate_prefix("/api/dashboard")
    cache.clear()

Thread-safety: todas as operações lêem/escrevem sob o mesmo Lock interno.
Memória: entradas expiradas são purgadas na leitura (lazy) e no prune periódico.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Estrutura de entrada de cache
# ---------------------------------------------------------------------------

class _CacheEntry:
    """Uma entrada de cache com valor e timestamp de expiração."""

    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl_seconds: float) -> None:
        self.value = value
        self.expires_at: float = time.monotonic() + ttl_seconds

    @property
    def is_expired(self) -> bool:
        return time.monotonic() >= self.expires_at


# ---------------------------------------------------------------------------
# Cache principal
# ---------------------------------------------------------------------------

class InMemoryCache:
    """
    Cache em memória thread-safe com TTL por entrada.

    Características:
      - Lock único protege todas as operações (read/write/invalidate)
      - Lazy expiry: entradas expiradas são detectadas na leitura e removidas
      - Prune periódico para garantir liberação de memória mesmo sem leituras
      - get() retorna (hit: bool, value: Any)
      - set(), invalidate(key), invalidate_prefix(prefix), clear()
    """

    def __init__(self, prune_interval_seconds: float = 300.0) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()
        self._prune_interval = prune_interval_seconds
        self._last_prune: float = time.monotonic()

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def get(self, key: str) -> tuple[bool, Any]:
        """
        Retorna (True, valor) se hit válido; (False, None) se miss ou expirado.
        Remove a entrada se expirada (lazy expiry).
        """
        with self._lock:
            self._maybe_prune()
            entry = self._store.get(key)
            if entry is None:
                return False, None
            if entry.is_expired:
                del self._store[key]
                return False, None
            return True, entry.value

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Armazena valor com TTL. Substitui entrada existente."""
        with self._lock:
            self._store[key] = _CacheEntry(value, ttl_seconds)

    # ------------------------------------------------------------------
    # Invalidação
    # ------------------------------------------------------------------

    def invalidate(self, key: str) -> bool:
        """Remove entrada pela chave exata. Retorna True se existia."""
        with self._lock:
            return self._store.pop(key, None) is not None

    def invalidate_prefix(self, prefix: str) -> int:
        """
        Remove todas as entradas cujo key começa com prefix.
        Retorna o número de entradas removidas.
        """
        with self._lock:
            keys_to_remove = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._store[k]
            return len(keys_to_remove)

    def clear(self) -> int:
        """Remove todas as entradas. Retorna quantas foram removidas."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    # ------------------------------------------------------------------
    # Estatísticas
    # ------------------------------------------------------------------

    def size(self) -> int:
        """Número de entradas (incluindo possivelmente expiradas)."""
        with self._lock:
            return len(self._store)

    def stats(self) -> dict[str, Any]:
        """Informações de diagnóstico do cache."""
        with self._lock:
            now = time.monotonic()
            valid = sum(1 for e in self._store.values() if not e.is_expired)
            expired = len(self._store) - valid
            return {
                "total_entries": len(self._store),
                "valid_entries": valid,
                "expired_entries": expired,
            }

    # ------------------------------------------------------------------
    # Prune interno
    # ------------------------------------------------------------------

    def _maybe_prune(self) -> None:
        """
        Remove entradas expiradas periodicamente.
        Deve ser chamado com o lock já adquirido.
        """
        now = time.monotonic()
        if now - self._last_prune < self._prune_interval:
            return
        expired_keys = [k for k, e in self._store.items() if e.is_expired]
        for k in expired_keys:
            del self._store[k]
        self._last_prune = now
        if expired_keys:
            logger.debug("[cache] Prune: %d entradas expiradas removidas", len(expired_keys))


# ---------------------------------------------------------------------------
# Singleton global — compartilhado por todos os módulos
# ---------------------------------------------------------------------------

cache = InMemoryCache(prune_interval_seconds=300.0)


# ---------------------------------------------------------------------------
# Função auxiliar para gerar cache key
# ---------------------------------------------------------------------------

def make_cache_key(prefix: str, params: Optional[dict] = None) -> str:
    """
    Gera uma chave de cache determinística a partir de um prefixo e parâmetros.

    A chave é: "{prefix}:{hash_hex_8}" quando params não está vazio,
    ou apenas "{prefix}" quando não há parâmetros.

    O hash garante que diferentes combinações de parâmetros geram chaves distintas
    sem expor os valores (segurança e tamanho de chave controlado).
    """
    if not params:
        return prefix
    # Serializar parâmetros de forma determinística (sorted keys)
    raw = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]  # noqa: S324 — não criptográfico
    return f"{prefix}:{digest}"


# ---------------------------------------------------------------------------
# Decorador @cached(ttl_seconds=N)
# ---------------------------------------------------------------------------

def cached(
    ttl_seconds: float,
    key_prefix: Optional[str] = None,
    key_params: Optional[Callable[..., dict]] = None,
) -> Callable:
    """
    Decorador para endpoints FastAPI (funções síncronas).

    Parâmetros:
      ttl_seconds:  tempo de vida da entrada em segundos
      key_prefix:   prefixo da chave (padrão: nome da função)
      key_params:   callable(kwargs) -> dict que extrai parâmetros relevantes
                    para a chave; se None, usa todos os parâmetros não-injetados

    Comportamento:
      1. Gera cache key a partir de prefix + params
      2. Verifica se há hit válido → retorna valor cached
      3. Se miss → executa função original → armazena resultado
      4. Sempre repassa kwargs à função original sem modificação

    NOTA: não suporta funções async (endpoints FastAPI síncronos apenas).
    Para async, use @cached_async (não implementado — FastAPI sync é o padrão aqui).

    Exemplo:
        @router.get("/kpis")
        @cached(ttl_seconds=60)
        def kpis(user=Depends(...), db=Depends(...)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        _prefix = key_prefix or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Desabilitar cache em ambiente de testes para evitar poluição entre testes
            if os.getenv("TESTING", "").lower() in ("1", "true"):
                return func(*args, **kwargs)

            # Extrair parâmetros relevantes para a chave
            if key_params is not None:
                params = key_params(**kwargs)
            else:
                # Ignorar objetos de dependência FastAPI (Session, Usuario, etc.)
                # que não são serializáveis e mudam a cada request
                params = {
                    k: v for k, v in kwargs.items()
                    if isinstance(v, (str, int, float, bool, type(None)))
                }

            key = make_cache_key(_prefix, params or None)

            hit, value = cache.get(key)
            if hit:
                logger.debug("[cache] HIT  key=%s", key)
                return value

            logger.debug("[cache] MISS key=%s", key)
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result

        # Expor método para invalidação direta pelo nome do endpoint
        wrapper.cache_prefix = _prefix  # type: ignore[attr-defined]
        wrapper.invalidate_cache = lambda: cache.invalidate_prefix(_prefix)  # type: ignore[attr-defined]

        return wrapper

    return decorator
