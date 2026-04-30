"""
CRM VITAO360 — Tests Resumo CEO (Onda 6 — ROMEO)

Cobertura:
  1. Sem LLM (sem provider disponível): fonte='TEMPLATE', texto não vazio
  2. Validação regex: texto com R$ inventado → validacao='SUSPEITO'
  3. Validação regex: texto com R$ correto → validacao='OK'
  4. ResultadoDDE com veredito SUBSTITUIR: template menciona substituição
  5. ResultadoDDE com veredito RENEGOCIAR: template menciona renegociar
  6. ResultadoDDE SEM_DADOS (l1=None): texto gerado sem erro
  7. Mock LLM available=True: chama generate e retorna fonte='LLM'
  8. Mock LLM falha silenciosa: cai para TEMPLATE
  9. Validação R$ com Decimal None não quebra
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.dde_engine import LinhaDRE, ResultadoDDE
from backend.app.services.resumo_ceo import (
    _template_fallback,
    _validar_regex_rs,
    gerar_resumo_ceo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_dre(
    veredito: str = "SAUDAVEL",
    l1: float | None = 100000.0,
    l11: float | None = 85000.0,
    l21: float | None = 15000.0,
    mc_pct: float | None = 0.18,
    score: float | None = 72.5,
) -> ResultadoDDE:
    """Factory de ResultadoDDE mínimo para testes."""

    def _linha(codigo: str, valor: float | None, pct: float | None = None) -> LinhaDRE:
        v = Decimal(str(valor)) if valor is not None else None
        return LinhaDRE(
            codigo=codigo,
            conta=f"Conta {codigo}",
            sinal="=",
            valor=v,
            pct_receita=pct,
            fonte="CALC",
            classificacao="SINTETICO" if v is not None else "PENDENTE",
            fase="A",
            observacao="",
        )

    linhas = [
        _linha("L1", l1, 1.0 if l1 else None),
        _linha("L11", l11, (l11 / l1) if (l11 and l1) else None),
        _linha("L21", l21, (l21 / l1) if (l21 and l1) else None),
    ]

    veredito_descricao_map = {
        "SAUDAVEL": "Cliente rentável e crédito em dia.",
        "REVISAR": "Margem entre 5% e 15%.",
        "RENEGOCIAR": "Margem abaixo de 5%.",
        "SUBSTITUIR": "Margem negativa — destrói valor.",
        "ALERTA_CREDITO": "Crédito comprometido.",
        "SEM_DADOS": "Dados insuficientes.",
    }

    return ResultadoDDE(
        cnpj="12345678000100",
        ano=2025,
        linhas=linhas,
        indicadores={
            "I1": None,
            "I2": mc_pct,
            "I3": 0.03,
            "I4": 0.04,
            "I5": 0.02,
            "I6": 0.01,
            "I7": 0.02,
            "I8": 15.0,
            "I9": score,
        },
        veredito=veredito,
        veredito_descricao=veredito_descricao_map.get(veredito, ""),
        fase_ativa="A",
    )


# ---------------------------------------------------------------------------
# Test 1 — Sem LLM: fonte=TEMPLATE, texto não vazio
# ---------------------------------------------------------------------------

def test_sem_llm_retorna_template():
    """Sem provider LLM disponível: deve usar TEMPLATE e retornar texto não vazio."""
    dre = _make_dre()

    # Faz LLMClient não ter nenhum provider disponível
    with patch(
        "backend.app.services.resumo_ceo.LLMClient"
    ) as MockLLMClient:
        mock_instance = MagicMock()
        mock_instance.available_providers.return_value = []  # sem providers
        MockLLMClient.return_value = mock_instance

        resultado = gerar_resumo_ceo(dre, "Cliente Teste Ltda")

    assert resultado["fonte"] == "TEMPLATE"
    assert resultado["texto"]
    assert len(resultado["texto"]) > 50
    assert "validacao" in resultado
    assert "divergencias" in resultado


# ---------------------------------------------------------------------------
# Test 2 — Validação regex: R$ inventado → SUSPEITO
# ---------------------------------------------------------------------------

def test_validacao_regex_suspeito():
    """Texto com valor R$ completamente inventado deve retornar SUSPEITO."""
    dre = _make_dre(l1=100000.0, l11=85000.0, l21=15000.0)

    # Valor inventado que não existe no DRE (difere > 1%)
    texto_com_r_inventado = (
        "O cliente gerou receita de R$ 999.888,77 no período, "
        "valor que não existe no DRE real."
    )

    validacao, divergencias = _validar_regex_rs(texto_com_r_inventado, dre)
    assert validacao == "SUSPEITO"
    assert len(divergencias) > 0


# ---------------------------------------------------------------------------
# Test 3 — Validação regex: R$ correto → OK
# ---------------------------------------------------------------------------

def test_validacao_regex_ok():
    """Texto com R$ correto (dentro de 1% do DRE real) deve retornar OK."""
    dre = _make_dre(l1=100000.0, l11=85000.0, l21=15000.0)

    # Usa valor real L1 = 100000.00 → R$ 100.000,00
    texto_com_r_correto = (
        "A receita bruta foi de R$ 100.000,00 conforme apurado no período."
    )

    validacao, divergencias = _validar_regex_rs(texto_com_r_correto, dre)
    assert validacao == "OK"
    assert len(divergencias) == 0


# ---------------------------------------------------------------------------
# Test 4 — Veredito SUBSTITUIR: template menciona substituição
# ---------------------------------------------------------------------------

def test_template_veredito_substituir():
    """Template com veredito SUBSTITUIR deve mencionar substituição ou inativação."""
    dre = _make_dre(veredito="SUBSTITUIR", l21=-5000.0, mc_pct=-0.05)
    texto = _template_fallback(dre, "Cliente Problema SA")

    assert texto
    # Deve conter palavra-chave relacionada a substituição ou inativação
    texto_lower = texto.lower()
    assert any(
        kw in texto_lower
        for kw in ["substitui", "inativi", "substituição", "inativação"]
    )


# ---------------------------------------------------------------------------
# Test 5 — Veredito RENEGOCIAR: template menciona renegociar
# ---------------------------------------------------------------------------

def test_template_veredito_renegociar():
    """Template com veredito RENEGOCIAR deve mencionar renegociação."""
    dre = _make_dre(veredito="RENEGOCIAR", l21=2000.0, mc_pct=0.02)
    texto = _template_fallback(dre, "Cliente Margem Baixa Ltda")

    assert texto
    texto_lower = texto.lower()
    assert any(
        kw in texto_lower
        for kw in ["renegoci", "contrato", "margem"]
    )


# ---------------------------------------------------------------------------
# Test 6 — SEM_DADOS (L1=None): sem erro
# ---------------------------------------------------------------------------

def test_template_sem_dados_nao_quebra():
    """ResultadoDDE com L1=None não deve levantar exceção."""
    dre = _make_dre(
        veredito="SEM_DADOS",
        l1=None,
        l11=None,
        l21=None,
        mc_pct=None,
        score=None,
    )
    resultado = gerar_resumo_ceo(dre, "")
    assert resultado["texto"]
    assert resultado["fonte"] in ("LLM", "TEMPLATE")


# ---------------------------------------------------------------------------
# Test 7 — Mock LLM available=True: fonte='LLM'
# ---------------------------------------------------------------------------

def test_llm_disponivel_retorna_fonte_llm():
    """Quando LLM disponível e retorna texto: fonte deve ser 'LLM'."""
    dre = _make_dre()
    texto_llm = "RESUMO CEO — Cliente Mock\n\nDIAGNÓSTICO:\nCliente saudável."

    with patch(
        "backend.app.services.resumo_ceo.LLMClient"
    ) as MockLLMClient:
        mock_instance = MagicMock()
        mock_instance.available_providers.return_value = ["deepinfra"]
        mock_resp = MagicMock()
        mock_resp.text = texto_llm
        mock_instance.generate.return_value = mock_resp
        MockLLMClient.return_value = mock_instance

        resultado = gerar_resumo_ceo(dre, "Cliente Mock")

    assert resultado["fonte"] == "LLM"
    assert resultado["texto"] == texto_llm


# ---------------------------------------------------------------------------
# Test 8 — Mock LLM falha silenciosa: cai para TEMPLATE
# ---------------------------------------------------------------------------

def test_llm_falha_silenciosa_cai_para_template():
    """Quando LLM lança exceção: deve cair para TEMPLATE sem propagar erro."""
    dre = _make_dre()

    with patch(
        "backend.app.services.resumo_ceo.LLMClient"
    ) as MockLLMClient:
        mock_instance = MagicMock()
        mock_instance.available_providers.return_value = ["deepinfra"]
        mock_instance.generate.side_effect = RuntimeError("API timeout")
        MockLLMClient.return_value = mock_instance

        resultado = gerar_resumo_ceo(dre, "Cliente Mock")

    # Deve ter caído para template sem propagar a exceção
    assert resultado["fonte"] == "TEMPLATE"
    assert resultado["texto"]


# ---------------------------------------------------------------------------
# Test 9 — Validação R$ com todos valores None não quebra
# ---------------------------------------------------------------------------

def test_validacao_regex_sem_valores_reais():
    """DRE com todos valores None: validação retorna OK sem erro."""
    dre = _make_dre(l1=None, l11=None, l21=None)
    texto = "Texto sem valores monetários."
    validacao, divergencias = _validar_regex_rs(texto, dre)
    assert validacao == "OK"
    assert divergencias == []


# ---------------------------------------------------------------------------
# Test 10 — Estrutura do retorno é completa
# ---------------------------------------------------------------------------

def test_retorno_estrutura_completa():
    """gerar_resumo_ceo deve retornar dict com todas as chaves esperadas."""
    dre = _make_dre()

    with patch("backend.app.services.resumo_ceo.LLMClient") as MockLLMClient:
        mock_instance = MagicMock()
        mock_instance.available_providers.return_value = []
        MockLLMClient.return_value = mock_instance

        resultado = gerar_resumo_ceo(dre, "Empresa XYZ")

    assert set(resultado.keys()) == {"texto", "fonte", "validacao", "divergencias"}
    assert isinstance(resultado["texto"], str)
    assert resultado["fonte"] in ("LLM", "TEMPLATE")
    assert resultado["validacao"] in ("OK", "SUSPEITO")
    assert isinstance(resultado["divergencias"], list)
