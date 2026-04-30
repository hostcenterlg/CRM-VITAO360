"""
CRM VITAO360 — Tests DDE Veredito (Onda 3 — OSCAR)

Cobertura:
  1. SEM_DADOS: I2 ausente → SEM_DADOS
  2. SUBSTITUIR: MC% < 0
  3. RENEGOCIAR: MC% entre 0% e 5%
  4. REVISAR: MC% entre 5% e 15%
  5. ALERTA_CREDITO: MC% >= 15%, aging > 90d, inadimp > 10%
  6. SAUDAVEL: MC% >= 15%, sem alertas de crédito
  7. Edge cases: MC% exatamente 0%, 5%, 15%
  8. ALERTA_CREDITO exige AMBOS (aging > 90 E inadimp > 10%) — não só um

Pattern: testa apenas a lógica de veredito, sem DB.
Cria ResultadoDDE com indicadores sintéticos.
"""

from __future__ import annotations

import pytest

from backend.app.services.dde_engine import ResultadoDDE
from backend.app.services.dde_veredito import veredito


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _dre(mc_pct=None, aging=None, inadimp_pct=None) -> ResultadoDDE:
    """Constrói ResultadoDDE mínimo com os indicadores informados."""
    indicadores = {
        "I1": None,
        "I2": mc_pct,
        "I3": None,
        "I4": None,
        "I5": None,
        "I6": inadimp_pct,
        "I7": None,
        "I8": aging,
        "I9": None,
    }
    return ResultadoDDE(
        cnpj="12345678000100",
        ano=2025,
        indicadores=indicadores,
    )


# ---------------------------------------------------------------------------
# 1. SEM_DADOS
# ---------------------------------------------------------------------------

class TestVereditorSemDados:
    """I2 ausente → SEM_DADOS."""

    def test_sem_i2_retorna_sem_dados(self):
        r = _dre(mc_pct=None)
        v, desc = veredito(r)
        assert v == "SEM_DADOS"

    def test_sem_dados_tem_descricao(self):
        r = _dre(mc_pct=None)
        v, desc = veredito(r)
        assert len(desc) > 10

    def test_dicionario_vazio_retorna_sem_dados(self):
        """Indicadores sem I2 → SEM_DADOS."""
        dre = ResultadoDDE(cnpj="12345678000100", ano=2025, indicadores={})
        v, _ = veredito(dre)
        assert v == "SEM_DADOS"


# ---------------------------------------------------------------------------
# 2. SUBSTITUIR — MC < 0
# ---------------------------------------------------------------------------

class TestVereditorSubstituir:
    """MC% negativa → cliente destrói valor."""

    def test_mc_negativo_substituir(self):
        r = _dre(mc_pct=-0.10)
        v, _ = veredito(r)
        assert v == "SUBSTITUIR"

    def test_mc_muito_negativo(self):
        r = _dre(mc_pct=-0.50)
        v, _ = veredito(r)
        assert v == "SUBSTITUIR"

    def test_substituir_descricao_menciona_margem(self):
        r = _dre(mc_pct=-0.10)
        _, desc = veredito(r)
        assert "margem" in desc.lower() or "destrói" in desc.lower()


# ---------------------------------------------------------------------------
# 3. RENEGOCIAR — MC entre 0% e 5%
# ---------------------------------------------------------------------------

class TestVereditorRenegociar:
    """MC% entre 0% e 5% (exclusive) → RENEGOCIAR."""

    def test_mc_001_renegociar(self):
        r = _dre(mc_pct=0.001)
        v, _ = veredito(r)
        assert v == "RENEGOCIAR"

    def test_mc_02_renegociar(self):
        r = _dre(mc_pct=0.02)
        v, _ = veredito(r)
        assert v == "RENEGOCIAR"

    def test_mc_049_renegociar(self):
        r = _dre(mc_pct=0.049)
        v, _ = veredito(r)
        assert v == "RENEGOCIAR"


# ---------------------------------------------------------------------------
# 4. REVISAR — MC entre 5% e 15%
# ---------------------------------------------------------------------------

class TestVereditorRevisar:
    """MC% entre 5% e 15% (exclusive) → REVISAR."""

    def test_mc_06_revisar(self):
        r = _dre(mc_pct=0.06)
        v, _ = veredito(r)
        assert v == "REVISAR"

    def test_mc_10_revisar(self):
        r = _dre(mc_pct=0.10)
        v, _ = veredito(r)
        assert v == "REVISAR"

    def test_mc_149_revisar(self):
        r = _dre(mc_pct=0.149)
        v, _ = veredito(r)
        assert v == "REVISAR"

    def test_revisar_sem_credito_alerta(self):
        """Mesmo com aging alto e inadimp alta, se MC < 15% é REVISAR (não ALERTA_CREDITO)."""
        r = _dre(mc_pct=0.10, aging=120.0, inadimp_pct=0.15)
        v, _ = veredito(r)
        assert v == "REVISAR"


# ---------------------------------------------------------------------------
# 5. ALERTA_CREDITO — MC >= 15%, aging > 90d, inadimp > 10%
# ---------------------------------------------------------------------------

class TestVereditorAlertaCredito:
    """MC saudável mas crédito comprometido."""

    def test_alerta_credito_completo(self):
        r = _dre(mc_pct=0.20, aging=100.0, inadimp_pct=0.12)
        v, _ = veredito(r)
        assert v == "ALERTA_CREDITO"

    def test_alerta_credito_aging_exato_90(self):
        """aging = 90d NÃO aciona ALERTA_CREDITO (threshold > 90)."""
        r = _dre(mc_pct=0.20, aging=90.0, inadimp_pct=0.12)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_alerta_credito_inadimp_exato_10(self):
        """inadimp = 10% NÃO aciona ALERTA_CREDITO (threshold > 10%)."""
        r = _dre(mc_pct=0.20, aging=100.0, inadimp_pct=0.10)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_alerta_credito_exige_ambas_condicoes(self):
        """Só aging alto sem inadimp alta = SAUDAVEL."""
        r = _dre(mc_pct=0.20, aging=120.0, inadimp_pct=0.05)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_alerta_credito_exige_ambas_condicoes_2(self):
        """Só inadimp alta sem aging alto = SAUDAVEL."""
        r = _dre(mc_pct=0.20, aging=30.0, inadimp_pct=0.20)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_alerta_credito_sem_aging_e_saudavel_mc(self):
        """MC >= 15% sem dados de aging → SAUDAVEL (não há como acionar ALERTA_CREDITO)."""
        r = _dre(mc_pct=0.20, aging=None, inadimp_pct=None)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"


# ---------------------------------------------------------------------------
# 6. SAUDAVEL
# ---------------------------------------------------------------------------

class TestVereditorSaudavel:
    """Cliente rentável e em dia."""

    def test_mc_15_saudavel(self):
        r = _dre(mc_pct=0.15)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_mc_alta_saudavel(self):
        r = _dre(mc_pct=0.30)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_saudavel_com_credito_ok(self):
        r = _dre(mc_pct=0.20, aging=20.0, inadimp_pct=0.02)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_saudavel_descricao_menciona_rentavel(self):
        r = _dre(mc_pct=0.20)
        _, desc = veredito(r)
        assert "rentável" in desc.lower() or "saudavel" in desc.lower() or "manter" in desc.lower()


# ---------------------------------------------------------------------------
# 7. Edge cases — thresholds exatos
# ---------------------------------------------------------------------------

class TestVereditorEdgeCases:
    """MC% nos limites exatos dos thresholds."""

    def test_mc_zero_exato_renegociar(self):
        """MC% = 0.0 → RENEGOCIAR (não SUBSTITUIR, pois não é < 0)."""
        r = _dre(mc_pct=0.0)
        v, _ = veredito(r)
        assert v == "RENEGOCIAR"

    def test_mc_cinco_pct_exato_revisar(self):
        """MC% = 5% = 0.05 → REVISAR (não RENEGOCIAR)."""
        r = _dre(mc_pct=0.05)
        v, _ = veredito(r)
        assert v == "REVISAR"

    def test_mc_quinze_pct_exato_saudavel(self):
        """MC% = 15% = 0.15 → SAUDAVEL (não REVISAR)."""
        r = _dre(mc_pct=0.15)
        v, _ = veredito(r)
        assert v == "SAUDAVEL"

    def test_todos_6_outcomes_sao_strings(self):
        """Todos os 6 outcomes retornam (str, str)."""
        casos = [
            _dre(mc_pct=None),
            _dre(mc_pct=-0.01),
            _dre(mc_pct=0.02),
            _dre(mc_pct=0.10),
            _dre(mc_pct=0.20, aging=100.0, inadimp_pct=0.12),
            _dre(mc_pct=0.20),
        ]
        outcomes_esperados = {
            "SEM_DADOS", "SUBSTITUIR", "RENEGOCIAR",
            "REVISAR", "ALERTA_CREDITO", "SAUDAVEL"
        }
        outcomes_obtidos = set()
        for dre in casos:
            v, desc = veredito(dre)
            assert isinstance(v, str)
            assert isinstance(desc, str)
            outcomes_obtidos.add(v)

        assert outcomes_obtidos == outcomes_esperados, (
            f"Outcomes obtidos: {outcomes_obtidos}\n"
            f"Esperados: {outcomes_esperados}"
        )

    def test_veredito_descricao_nunca_vazio(self):
        """Descrição nunca pode ser string vazia."""
        casos = [
            _dre(mc_pct=None),
            _dre(mc_pct=-0.10),
            _dre(mc_pct=0.02),
            _dre(mc_pct=0.10),
            _dre(mc_pct=0.20, aging=100.0, inadimp_pct=0.12),
            _dre(mc_pct=0.25),
        ]
        for dre in casos:
            v, desc = veredito(dre)
            assert desc, f"Veredito {v} tem descrição vazia"
