"""
CRM VITAO360 — Tests LLMClient (Onda 6 — ROMEO)

Cobertura:
  1. Sem API key: available_providers() retorna lista vazia
  2. Sem API key: generate() lança RuntimeError com mensagem informativa
  3. Com API key mockada (deepinfra): available_providers() inclui provider
  4. generate() com mock httpx: chama endpoint correto e retorna LLMResponse
  5. generate() com mock Anthropic: usa _call_anthropic corretamente
  6. Fallback: provider primário falha, usa fallback_fast
  7. Cache: segunda chamada igual retorna cached=True

Pattern: mesmo estilo dos outros testes de serviço — sem chamada real de API.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.llm_client import (
    LLMClient,
    LLMResponse,
    _detect_available_providers,
    _hash_prompt,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(text: str = "resposta mock") -> MagicMock:
    """Cria mock de resposta httpx para endpoint OpenAI-compatible."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 100},
    }
    return mock_resp


def _mock_anthropic_response(text: str = "resposta anthropic") -> MagicMock:
    """Cria mock de resposta httpx para endpoint Anthropic."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "content": [{"type": "text", "text": text}],
        "usage": {"input_tokens": 60, "output_tokens": 120},
    }
    return mock_resp


# ---------------------------------------------------------------------------
# Test 1 — Sem API key: available_providers() vazio
# ---------------------------------------------------------------------------

def test_sem_api_key_available_providers_vazio():
    """Sem nenhuma env var de API key: lista de providers deve ser vazia."""
    # Limpa todas as keys de API para este teste
    env_limpo = {
        k: v for k, v in os.environ.items()
        if not k.endswith("_API_KEY")
    }
    with patch.dict(os.environ, env_limpo, clear=True):
        client = LLMClient()
        assert client.available_providers() == []


# ---------------------------------------------------------------------------
# Test 2 — Sem API key: generate() lança RuntimeError
# ---------------------------------------------------------------------------

def test_sem_api_key_generate_levanta_runtime_error():
    """Sem provider disponível, generate() deve levantar RuntimeError."""
    env_limpo = {
        k: v for k, v in os.environ.items()
        if not k.endswith("_API_KEY")
    }
    with patch.dict(os.environ, env_limpo, clear=True):
        client = LLMClient(cache_enabled=False)
        with pytest.raises(RuntimeError, match="Nenhum provider"):
            client.generate("teste", model_tier="cheap")


# ---------------------------------------------------------------------------
# Test 3 — Com DEEPINFRA_API_KEY: provider detectado
# ---------------------------------------------------------------------------

def test_com_deepinfra_key_provider_detectado():
    """Com DEEPINFRA_API_KEY setada: available_providers inclui 'deepinfra'."""
    with patch.dict(os.environ, {"DEEPINFRA_API_KEY": "fake-key-12345678901234"}):
        providers = _detect_available_providers()
        assert "deepinfra" in providers


# ---------------------------------------------------------------------------
# Test 4 — generate() com mock httpx (deepinfra): retorna LLMResponse
# ---------------------------------------------------------------------------

def test_generate_deepinfra_mock():
    """generate() com deepinfra mockado deve retornar LLMResponse com texto."""
    with patch.dict(
        os.environ,
        {
            "DEEPINFRA_API_KEY": "fake-deepinfra-key-1234567890",
            "LLM_PROVIDER": "deepinfra",
        },
    ):
        client = LLMClient(cache_enabled=False)

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _mock_openai_response("texto gerado deepinfra")

        with patch("backend.app.services.llm_client.httpx.Client", return_value=mock_http):
            resp = client.generate("gere um resumo", model_tier="cheap", max_tokens=100)

        assert isinstance(resp, LLMResponse)
        assert resp.text == "texto gerado deepinfra"
        assert resp.tokens_input == 50
        assert resp.tokens_output == 100
        assert resp.provider == "deepinfra"
        assert resp.cached is False


# ---------------------------------------------------------------------------
# Test 5 — generate() com Anthropic mockado: usa _call_anthropic
# ---------------------------------------------------------------------------

def test_generate_anthropic_mock():
    """generate() com Anthropic mockado deve retornar LLMResponse correto."""
    with patch.dict(
        os.environ,
        {
            "ANTHROPIC_API_KEY": "fake-anthropic-key-1234567890",
            "LLM_PROVIDER": "anthropic",
        },
    ):
        client = LLMClient(cache_enabled=False)

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _mock_anthropic_response("texto gerado anthropic")

        with patch("backend.app.services.llm_client.httpx.Client", return_value=mock_http):
            resp = client.generate("gere análise", model_tier="premium", max_tokens=200)

        assert isinstance(resp, LLMResponse)
        assert resp.text == "texto gerado anthropic"
        assert resp.provider == "anthropic"
        assert resp.tokens_input == 60
        assert resp.tokens_output == 120


# ---------------------------------------------------------------------------
# Test 6 — Fallback: primário falha, usa segundo provider
# ---------------------------------------------------------------------------

def test_fallback_provider():
    """Quando provider primário falha, deve usar fallback."""
    with patch.dict(
        os.environ,
        {
            "DEEPINFRA_API_KEY": "fake-deepinfra-12345678901",
            "GROQ_API_KEY": "fake-groq-key-1234567890123",
            "LLM_PROVIDER": "deepinfra",
            "LLM_PROVIDER_FAST": "groq",
        },
    ):
        client = LLMClient(cache_enabled=False)
        chamadas = []

        def mock_post_seletivo(url, **kwargs):
            """Falha para deepinfra, sucesso para groq."""
            if "deepinfra" in url:
                raise RuntimeError("deepinfra timeout simulado")
            chamadas.append(url)
            return _mock_openai_response("resposta groq fallback")

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.side_effect = mock_post_seletivo

        with patch("backend.app.services.llm_client.httpx.Client", return_value=mock_http):
            resp = client.generate("teste fallback", model_tier="cheap")

        # Deve ter recebido resposta do groq (fallback)
        assert resp.text == "resposta groq fallback"
        assert "groq" in resp.provider


# ---------------------------------------------------------------------------
# Test 7 — Cache: segunda chamada idêntica retorna cached=True
# ---------------------------------------------------------------------------

def test_cache_hit():
    """Segunda chamada com mesmo prompt deve retornar cached=True."""
    with patch.dict(
        os.environ,
        {
            "DEEPINFRA_API_KEY": "fake-deepinfra-key-1234567890",
            "LLM_PROVIDER": "deepinfra",
        },
    ):
        client = LLMClient(cache_enabled=True)

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = _mock_openai_response("resposta cacheada")

        with patch("backend.app.services.llm_client.httpx.Client", return_value=mock_http):
            resp1 = client.generate("mesmo prompt para cache", model_tier="cheap")
            resp2 = client.generate("mesmo prompt para cache", model_tier="cheap")

        assert resp1.cached is False
        assert resp2.cached is True
        # Só deve ter chamado o httpx uma vez (segunda foi do cache)
        assert mock_http.post.call_count == 1


# ---------------------------------------------------------------------------
# Test 8 — _hash_prompt: hashes diferentes para prompts diferentes
# ---------------------------------------------------------------------------

def test_hash_prompt_diferente():
    """Dois prompts diferentes devem gerar hashes diferentes."""
    h1 = _hash_prompt("prompt A")
    h2 = _hash_prompt("prompt B")
    assert h1 != h2


# ---------------------------------------------------------------------------
# Test 9 — LLMResponse dataclass fields corretos
# ---------------------------------------------------------------------------

def test_llm_response_dataclass():
    """LLMResponse deve ter todos os campos esperados."""
    resp = LLMResponse(
        text="teste",
        tokens_input=10,
        tokens_output=20,
        cost_usd=0.001,
        provider="deepinfra",
        model="Qwen/Qwen2.5-72B-Instruct",
        duration_ms=500,
        cached=False,
        tier="cheap",
    )
    assert resp.text == "teste"
    assert resp.tokens_input == 10
    assert resp.tokens_output == 20
    assert resp.cost_usd == 0.001
    assert resp.provider == "deepinfra"
    assert resp.cached is False
