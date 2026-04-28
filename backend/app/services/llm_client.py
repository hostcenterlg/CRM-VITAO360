"""
llm_client — Camada LLM provider-agnostic (reutilizável)
============================================================================

ORIGEM: US County Radar (testado em produção com 60K+ chamadas)
ADAPTADO PARA: CRM360 ou qualquer projeto Python

Código NUNCA chama provider direto. Sempre via este módulo.

Strategy:
  - cheap   -> DeepInfra (Qwen/Qwen2.5-72B-Instruct, $0.13/$0.40 por 1M)
  - fast    -> Groq (llama-3.3-70b-versatile, $0.59/$0.79, latência <500ms)
  - premium -> Anthropic Claude Sonnet (opcional, mais caro)

Cascata fallback automática: primary -> fast -> premium.
Toda chamada logada em llm_calls (se conn fornecido).
Memo cache opcional via LLM_CACHE_ENABLED=true (default).

ENV vars relevantes (todas opcionais — usa quem tiver key):
  LLM_PROVIDER          (default 'deepinfra')
  LLM_PROVIDER_FAST     (default 'groq')
  LLM_PROVIDER_PREMIUM  (default 'anthropic')
  LLM_CACHE_ENABLED     (default 'true')
  DEEPINFRA_API_KEY
  GROQ_API_KEY
  ANTHROPIC_API_KEY
  OPENAI_API_KEY
  DEEPSEEK_API_KEY

API pública:
  client = LLMClient(conn)                      # conn psycopg2 opcional p/ logging
  resp = client.generate("explique X", model_tier="cheap")
  resp = client.generate_with_vision("o que vê?", image_url="https://...", model_tier="cheap")

Dataclass LLMResponse:
  text, tokens_input, tokens_output, cost_usd, provider, model, duration_ms, cached

INSTALAÇÃO:
  pip install httpx
  (psycopg2-binary se quiser logging em PostgreSQL)

TABELA DE LOGGING (opcional — criar no seu banco):
  CREATE TABLE llm_calls (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT now(),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    tier TEXT,
    prompt_hash TEXT,
    prompt_preview TEXT,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    cost_usd NUMERIC(10,6) DEFAULT 0,
    duration_ms INT DEFAULT 0,
    cached BOOLEAN DEFAULT false,
    success BOOLEAN DEFAULT true,
    error TEXT,
    use_case TEXT,
    property_id UUID,      -- adaptar: entity_id, lead_id, etc.
    user_id UUID
  );
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from uuid import UUID

import httpx


# ============================================================================
# Configuração
# ============================================================================

ModelTier = Literal["cheap", "fast", "premium"]

# Modelos default por provider/tier
PROVIDER_MODELS: dict[str, dict[str, str]] = {
    "deepinfra": {
        "cheap": "Qwen/Qwen2.5-72B-Instruct",
        "fast": "Qwen/Qwen2.5-72B-Instruct",
        "premium": "meta-llama/Meta-Llama-3.1-405B-Instruct",
        "vision-cheap": "meta-llama/Llama-3.2-90B-Vision-Instruct",
        "vision-fast": "meta-llama/Llama-3.2-90B-Vision-Instruct",
    },
    "groq": {
        "cheap": "llama-3.3-70b-versatile",
        "fast": "llama-3.3-70b-versatile",
        "premium": "llama-3.3-70b-versatile",
        "vision-cheap": "llama-3.2-90b-vision-preview",
        "vision-fast": "llama-3.2-90b-vision-preview",
    },
    "anthropic": {
        "cheap": "claude-haiku-4-5-20251001",
        "fast": "claude-haiku-4-5-20251001",
        "premium": "claude-sonnet-4-6",
        "vision-cheap": "claude-haiku-4-5-20251001",
        "vision-fast": "claude-haiku-4-5-20251001",
    },
    "openai": {
        "cheap": "gpt-4o-mini",
        "fast": "gpt-4o-mini",
        "premium": "gpt-4o",
        "vision-cheap": "gpt-4o-mini",
        "vision-fast": "gpt-4o-mini",
    },
    "deepseek": {
        "cheap": "deepseek-chat",
        "fast": "deepseek-chat",
        "premium": "deepseek-chat",
    },
}

# Preços $/1M tokens (input, output) — atualizado 04/2026
PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "deepinfra": {
        "Qwen/Qwen2.5-72B-Instruct":                        (0.13, 0.40),
        "meta-llama/Meta-Llama-3.1-70B-Instruct":           (0.23, 0.40),
        "meta-llama/Meta-Llama-3.1-405B-Instruct":          (1.79, 1.79),
        "meta-llama/Llama-3.2-90B-Vision-Instruct":         (0.35, 0.40),
    },
    "groq": {
        "llama-3.3-70b-versatile":                          (0.59, 0.79),
        "llama-3.2-90b-vision-preview":                     (0.90, 0.90),
    },
    "anthropic": {
        "claude-haiku-4-5-20251001":                        (1.00, 5.00),
        "claude-sonnet-4-6":                                (3.00, 15.00),
    },
    "openai": {
        "gpt-4o-mini":                                      (0.15, 0.60),
        "gpt-4o":                                           (2.50, 10.00),
    },
    "deepseek": {
        "deepseek-chat":                                    (0.14, 0.28),
    },
}

# Endpoints OpenAI-compatible (Anthropic usa native)
ENDPOINTS: dict[str, str] = {
    "deepinfra": "https://api.deepinfra.com/v1/openai",
    "groq":      "https://api.groq.com/openai/v1",
    "openai":    "https://api.openai.com/v1",
    "deepseek":  "https://api.deepseek.com/v1",
}

ENV_KEYS: dict[str, str] = {
    "deepinfra": "DEEPINFRA_API_KEY",
    "groq":      "GROQ_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "deepseek":  "DEEPSEEK_API_KEY",
}

ANTHROPIC_VERSION = "2023-06-01"

# Retry / timeout
RETRY_MAX = 3
RETRY_BACKOFF_BASE = 2.0  # 2s, 4s, 8s
TIMEOUT_TEXT = 30.0
TIMEOUT_VISION = 60.0

# Memo cache em processo (lru-like, max 500 entries)
_MEMO_CACHE: dict[str, "LLMResponse"] = {}
_MEMO_MAX = 500


# ============================================================================
# Dataclass
# ============================================================================

@dataclass
class LLMResponse:
    text: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    provider: str
    model: str
    duration_ms: int
    cached: bool = False
    tier: str | None = None


# ============================================================================
# Helpers
# ============================================================================

def _hash_prompt(*parts: str | None) -> str:
    h = hashlib.sha256()
    for p in parts:
        if p:
            h.update(p.encode("utf-8", errors="replace"))
            h.update(b"\x1e")
    return h.hexdigest()


def _calc_cost(provider: str, model: str, tin: int, tout: int) -> float:
    rates = PRICING.get(provider, {}).get(model)
    if not rates:
        return 0.0
    input_rate, output_rate = rates
    return (tin * input_rate + tout * output_rate) / 1_000_000


def _detect_available_providers() -> list[str]:
    avail: list[str] = []
    for provider, env_key in ENV_KEYS.items():
        key = os.getenv(env_key) or ""
        if key and len(key.strip()) > 10:
            avail.append(provider)
    return avail


def _memo_get(key: str) -> Optional["LLMResponse"]:
    if not _MEMO_CACHE:
        return None
    hit = _MEMO_CACHE.get(key)
    if hit is None:
        return None
    return LLMResponse(
        text=hit.text, tokens_input=hit.tokens_input, tokens_output=hit.tokens_output,
        cost_usd=0.0, provider=hit.provider, model=hit.model,
        duration_ms=0, cached=True, tier=hit.tier,
    )


def _memo_put(key: str, resp: "LLMResponse") -> None:
    if len(_MEMO_CACHE) >= _MEMO_MAX:
        try:
            first_key = next(iter(_MEMO_CACHE))
            _MEMO_CACHE.pop(first_key, None)
        except StopIteration:
            pass
    _MEMO_CACHE[key] = resp


# ============================================================================
# Provider callers
# ============================================================================

def _call_openai_compatible(
    *, provider: str, api_key: str, model: str,
    system_prompt: str | None, user_prompt: str,
    max_tokens: int, temperature: float, image_url: str | None = None,
    timeout: float = TIMEOUT_TEXT,
) -> tuple[str, int, int]:
    """OpenAI-compatible (DeepInfra/Groq/OpenAI/DeepSeek). Retorna (text, tin, tout)."""
    base_url = ENDPOINTS[provider]
    url = f"{base_url}/chat/completions"

    messages: list[dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if image_url:
        content = [
            {"type": "text", "text": user_prompt},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": user_prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_err: Exception | None = None
    for attempt in range(RETRY_MAX):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                text = (msg.get("content") or "").strip()
                usage = data.get("usage") or {}
                tin = int(usage.get("prompt_tokens") or 0)
                tout = int(usage.get("completion_tokens") or 0)
                return text, tin, tout
        except httpx.HTTPStatusError as e:
            last_err = e
            status = e.response.status_code
            if status == 429 or status >= 500:
                wait = RETRY_BACKOFF_BASE ** (attempt + 1)
                time.sleep(wait)
                continue
            raise
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_err = e
            wait = RETRY_BACKOFF_BASE ** (attempt + 1)
            time.sleep(wait)
            continue

    raise RuntimeError(f"{provider} API failed after {RETRY_MAX} retries: {last_err}")


def _call_anthropic(
    *, api_key: str, model: str,
    system_prompt: str | None, user_prompt: str,
    max_tokens: int, temperature: float, image_url: str | None = None,
    timeout: float = TIMEOUT_TEXT,
) -> tuple[str, int, int]:
    """Anthropic native API. Retorna (text, tin, tout)."""
    url = "https://api.anthropic.com/v1/messages"

    if image_url:
        content = [
            {"type": "image", "source": {"type": "url", "url": image_url}},
            {"type": "text", "text": user_prompt},
        ]
        messages = [{"role": "user", "content": content}]
    else:
        messages = [{"role": "user", "content": user_prompt}]

    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system_prompt:
        payload["system"] = system_prompt

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    last_err: Exception | None = None
    for attempt in range(RETRY_MAX):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                blocks = data.get("content") or []
                text_parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
                text = "\n".join(text_parts).strip()
                usage = data.get("usage") or {}
                tin = int(usage.get("input_tokens") or 0)
                tout = int(usage.get("output_tokens") or 0)
                return text, tin, tout
        except httpx.HTTPStatusError as e:
            last_err = e
            status = e.response.status_code
            if status == 429 or status >= 500:
                wait = RETRY_BACKOFF_BASE ** (attempt + 1)
                time.sleep(wait)
                continue
            raise
        except (httpx.RequestError, httpx.TimeoutException) as e:
            last_err = e
            wait = RETRY_BACKOFF_BASE ** (attempt + 1)
            time.sleep(wait)
            continue

    raise RuntimeError(f"anthropic API failed after {RETRY_MAX} retries: {last_err}")


# ============================================================================
# Logger (PostgreSQL)
# ============================================================================

def _log_call(
    conn,
    *, provider: str, model: str, tier: str | None,
    prompt_hash: str, prompt_preview: str | None,
    tokens_input: int, tokens_output: int, cost_usd: float,
    duration_ms: int, cached: bool,
    success: bool, error: str | None,
    use_case: str | None, entity_id: str | UUID | None, user_id: str | UUID | None,
) -> None:
    """Insere row em llm_calls. Falha silenciosa."""
    if conn is None:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO llm_calls (
                    provider, model, tier, prompt_hash, prompt_preview,
                    tokens_input, tokens_output, cost_usd, duration_ms, cached,
                    success, error, use_case, entity_id, user_id
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """, (
                provider, model, tier, prompt_hash,
                (prompt_preview or "")[:200] if prompt_preview else None,
                tokens_input, tokens_output, cost_usd, duration_ms, cached,
                success, error, use_case,
                str(entity_id) if entity_id else None,
                str(user_id) if user_id else None,
            ))
        conn.commit()
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"  WARN: llm_calls log failed: {exc}")


# ============================================================================
# LLMClient
# ============================================================================

class LLMClient:
    """
    Cliente provider-agnostic para LLM.

    Uso:
        client = LLMClient()
        resp = client.generate("Resuma este contrato", model_tier="cheap")
        print(resp.text, resp.cost_usd)

    Args:
        conn:           conexão psycopg2 opcional. Se fornecida, loga em llm_calls.
        cache_enabled:  override de LLM_CACHE_ENABLED. Default True.
    """

    def __init__(self, conn: Any = None, cache_enabled: bool | None = None):
        self.conn = conn
        if cache_enabled is None:
            cache_enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() not in ("false", "0", "no")
        self.cache_enabled = cache_enabled

        self.primary           = os.getenv("LLM_PROVIDER", "deepinfra").lower()
        self.fallback_fast     = os.getenv("LLM_PROVIDER_FAST", "groq").lower()
        self.fallback_premium  = os.getenv("LLM_PROVIDER_PREMIUM", "anthropic").lower()

        self._available = _detect_available_providers()

    def _provider_cascade(self, tier: ModelTier) -> list[str]:
        if tier == "cheap":
            order = [self.primary, self.fallback_fast, self.fallback_premium]
        elif tier == "fast":
            order = [self.fallback_fast, self.primary, self.fallback_premium]
        else:
            order = [self.fallback_premium, self.primary, self.fallback_fast]

        seen: set[str] = set()
        result: list[str] = []
        for p in order:
            p = (p or "").lower()
            if p in self._available and p not in seen:
                result.append(p)
                seen.add(p)
        for p in self._available:
            if p not in seen:
                result.append(p)
                seen.add(p)
        return result

    def available_providers(self) -> list[str]:
        return list(self._available)

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model_tier: ModelTier = "cheap",
        max_tokens: int = 500,
        temperature: float = 0.2,
        use_case: str | None = None,
        entity_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> LLMResponse:
        """Geração texto. Retorna LLMResponse com cost, tokens, provider."""
        return self._generate_internal(
            user_prompt=prompt, system_prompt=system_prompt,
            model_tier=model_tier, max_tokens=max_tokens, temperature=temperature,
            image_url=None, use_case=use_case, entity_id=entity_id, user_id=user_id,
        )

    def generate_with_vision(
        self,
        prompt: str,
        image_url: str,
        *,
        system_prompt: str | None = None,
        model_tier: ModelTier = "cheap",
        max_tokens: int = 800,
        temperature: float = 0.1,
        use_case: str | None = None,
        entity_id: str | UUID | None = None,
        user_id: str | UUID | None = None,
    ) -> LLMResponse:
        """Geração multimodal com imagem."""
        return self._generate_internal(
            user_prompt=prompt, system_prompt=system_prompt,
            model_tier=model_tier, max_tokens=max_tokens, temperature=temperature,
            image_url=image_url, use_case=use_case,
            entity_id=entity_id, user_id=user_id,
            vision=True,
        )

    def _generate_internal(
        self,
        *, user_prompt: str, system_prompt: str | None,
        model_tier: ModelTier, max_tokens: int, temperature: float,
        image_url: str | None,
        use_case: str | None,
        entity_id: str | UUID | None,
        user_id: str | UUID | None,
        vision: bool = False,
    ) -> LLMResponse:
        prompt_hash = _hash_prompt(system_prompt, user_prompt, image_url)
        cache_key = f"{model_tier}:{prompt_hash}" if not vision else f"vision:{model_tier}:{prompt_hash}"

        # Memo cache check
        if self.cache_enabled and not vision:
            hit = _memo_get(cache_key)
            if hit is not None:
                _log_call(
                    self.conn, provider=hit.provider, model=hit.model, tier=hit.tier,
                    prompt_hash=prompt_hash,
                    prompt_preview=user_prompt[:200] if user_prompt else None,
                    tokens_input=hit.tokens_input, tokens_output=hit.tokens_output,
                    cost_usd=0.0, duration_ms=0, cached=True,
                    success=True, error=None,
                    use_case=use_case, entity_id=entity_id, user_id=user_id,
                )
                return hit

        # Resolve cascata
        cascade = self._provider_cascade(model_tier)
        if not cascade:
            raise RuntimeError(
                "Nenhum provider LLM disponível. Configure pelo menos uma de: "
                + ", ".join(ENV_KEYS.values())
            )

        last_err: Exception | None = None
        for provider in cascade:
            api_key = os.getenv(ENV_KEYS[provider]) or ""
            if not api_key:
                continue

            tier_key = ("vision-" + model_tier) if vision else model_tier
            model = (
                PROVIDER_MODELS.get(provider, {}).get(tier_key)
                or PROVIDER_MODELS.get(provider, {}).get(model_tier)
                or PROVIDER_MODELS.get(provider, {}).get("cheap")
            )
            if not model:
                continue

            t0 = time.monotonic()
            try:
                if provider == "anthropic":
                    text, tin, tout = _call_anthropic(
                        api_key=api_key, model=model,
                        system_prompt=system_prompt, user_prompt=user_prompt,
                        max_tokens=max_tokens, temperature=temperature,
                        image_url=image_url,
                        timeout=TIMEOUT_VISION if vision else TIMEOUT_TEXT,
                    )
                else:
                    text, tin, tout = _call_openai_compatible(
                        provider=provider, api_key=api_key, model=model,
                        system_prompt=system_prompt, user_prompt=user_prompt,
                        max_tokens=max_tokens, temperature=temperature,
                        image_url=image_url,
                        timeout=TIMEOUT_VISION if vision else TIMEOUT_TEXT,
                    )

                duration_ms = int((time.monotonic() - t0) * 1000)
                cost = _calc_cost(provider, model, tin, tout)

                resp = LLMResponse(
                    text=text, tokens_input=tin, tokens_output=tout,
                    cost_usd=cost, provider=provider, model=model,
                    duration_ms=duration_ms, cached=False, tier=tier_key,
                )

                _log_call(
                    self.conn, provider=provider, model=model, tier=tier_key,
                    prompt_hash=prompt_hash,
                    prompt_preview=user_prompt[:200] if user_prompt else None,
                    tokens_input=tin, tokens_output=tout,
                    cost_usd=cost, duration_ms=duration_ms, cached=False,
                    success=True, error=None,
                    use_case=use_case, entity_id=entity_id, user_id=user_id,
                )

                if self.cache_enabled and not vision and text:
                    _memo_put(cache_key, resp)

                return resp

            except Exception as exc:
                last_err = exc
                duration_ms = int((time.monotonic() - t0) * 1000)
                _log_call(
                    self.conn, provider=provider, model=model, tier=tier_key,
                    prompt_hash=prompt_hash,
                    prompt_preview=user_prompt[:200] if user_prompt else None,
                    tokens_input=0, tokens_output=0,
                    cost_usd=0.0, duration_ms=duration_ms, cached=False,
                    success=False, error=str(exc)[:500],
                    use_case=use_case, entity_id=entity_id, user_id=user_id,
                )
                continue

        raise RuntimeError(
            f"Todos providers da cascata falharam ({', '.join(cascade)}): {last_err}"
        )


# ============================================================================
# Convenience (módulo-level)
# ============================================================================

_DEFAULT_CLIENT: LLMClient | None = None


def get_default_client(conn: Any = None) -> LLMClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        _DEFAULT_CLIENT = LLMClient(conn=conn)
    elif conn is not None and _DEFAULT_CLIENT.conn is None:
        _DEFAULT_CLIENT.conn = conn
    return _DEFAULT_CLIENT


def generate(prompt: str, **kw: Any) -> LLMResponse:
    return get_default_client().generate(prompt, **kw)


def generate_with_vision(prompt: str, image_url: str, **kw: Any) -> LLMResponse:
    return get_default_client().generate_with_vision(prompt, image_url, **kw)


__all__ = [
    "LLMClient",
    "LLMResponse",
    "ModelTier",
    "PROVIDER_MODELS",
    "PRICING",
    "get_default_client",
    "generate",
    "generate_with_vision",
]
