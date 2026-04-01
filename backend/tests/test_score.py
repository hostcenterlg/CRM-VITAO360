"""
CRM VITAO360 — Tests for Score Engine v2.

Covers:
  - Score range is always 0-100
  - All 6 factor weights sum exactly to 1.0 (100%)
  - Each factor returns a value in [0, 100]
  - Prioridade mapping: correct P0-P7 labels
  - prioridade_curta is max 5 chars (fits String(5) in DB model)
  - URGENCIA factor: INAT.ANT=100, INAT.REC=90, PROSPECT=10, ratio logic
  - VALOR factor: A+MADURO=100, C=20, no ABC=10
  - FOLLOWUP factor: None=50 (neutral), 7+ days late=100, future=-3=40
  - SINAL factor: QUENTE=80, FRIO=10, CRITICO=90
  - TENTATIVA factor: T4=100, T3=50, T1/T2=10
  - SITUACAO factor: ATIVO=40, EM RISCO=80, PROSPECT=10

These tests are pure unit tests — no DB fixture needed.
ScoreService.calcular() is deterministic given a Cliente object.
"""

from __future__ import annotations

import pytest

from backend.app.models.cliente import Cliente
from backend.app.services.score_service import (
    PESOS,
    ScoreService,
    _calcular_followup,
    _calcular_sinal,
    _calcular_situacao_fator,
    _calcular_tentativa,
    _calcular_urgencia,
    _calcular_valor,
)


# ---------------------------------------------------------------------------
# Helper to build minimal Cliente objects
# ---------------------------------------------------------------------------

def _make_cliente(
    cnpj: str = "12345678000100",
    situacao: str = "ATIVO",
    curva_abc: str = "A",
    tipo_cliente: str = "MADURO",
    temperatura: str = "QUENTE",
    tentativas: str = "T1",
    dias_sem_compra: int | None = None,
    ciclo_medio: float | None = None,
    followup_dias: int | None = None,
    resultado: str = "",
    problema_aberto: bool = False,
) -> Cliente:
    """Factory: creates a minimal Cliente for score calculation (no DB needed)."""
    return Cliente(
        cnpj=cnpj,
        situacao=situacao,
        curva_abc=curva_abc,
        tipo_cliente=tipo_cliente,
        temperatura=temperatura,
        tentativas=tentativas,
        dias_sem_compra=dias_sem_compra,
        ciclo_medio=ciclo_medio,
        followup_dias=followup_dias,
        resultado=resultado,
        problema_aberto=problema_aberto,
        classificacao_3tier="REAL",
    )


# ---------------------------------------------------------------------------
# Peso (weight) invariants
# ---------------------------------------------------------------------------

class TestPesos:

    def test_pesos_sum_exactly_to_one(self):
        """All 6 factor weights must sum to exactly 1.0 (= 100%)."""
        soma = sum(PESOS.values())
        assert abs(soma - 1.0) < 1e-9, f"Weights sum to {soma}, expected 1.0"

    def test_pesos_contains_all_six_factors(self):
        """PESOS dict must define all 6 score factors."""
        expected = {"URGENCIA", "VALOR", "FOLLOWUP", "SINAL", "TENTATIVA", "SITUACAO"}
        assert set(PESOS.keys()) == expected

    def test_individual_peso_values_match_spec(self):
        """Each weight must match the Score v2 specification."""
        assert PESOS["URGENCIA"] == 0.30
        assert PESOS["VALOR"] == 0.25
        assert PESOS["FOLLOWUP"] == 0.20
        assert PESOS["SINAL"] == 0.15
        assert PESOS["TENTATIVA"] == 0.05
        assert PESOS["SITUACAO"] == 0.05


# ---------------------------------------------------------------------------
# Score range invariant
# ---------------------------------------------------------------------------

class TestScoreRange:

    def test_score_is_always_between_zero_and_one_hundred(self):
        """score must be clamped to [0, 100] for all situacao combinations."""
        svc = ScoreService()
        situacoes = ["ATIVO", "INAT.ANT", "INAT.REC", "PROSPECT", "LEAD", "EM RISCO"]
        for situacao in situacoes:
            c = _make_cliente(situacao=situacao)
            r = svc.calcular(c)
            assert 0.0 <= r["score"] <= 100.0, (
                f"Score {r['score']} out of range for situacao={situacao}"
            )

    def test_score_with_all_nulls_is_between_zero_and_one_hundred(self):
        """Cliente with all None fields still returns a valid score."""
        svc = ScoreService()
        c = Cliente(cnpj="00000000000001", classificacao_3tier="REAL")
        r = svc.calcular(c)
        assert 0.0 <= r["score"] <= 100.0

    def test_score_result_contains_all_required_keys(self):
        """calcular() must return all 6 factor keys plus score and prioridade."""
        svc = ScoreService()
        c = _make_cliente()
        r = svc.calcular(c)
        required = {
            "score", "prioridade", "prioridade_curta",
            "fator_urgencia", "fator_valor", "fator_followup",
            "fator_sinal", "fator_tentativa", "fator_situacao",
        }
        missing = required - r.keys()
        assert not missing, f"calcular() result missing keys: {missing}"


# ---------------------------------------------------------------------------
# URGENCIA factor
# ---------------------------------------------------------------------------

class TestFatorUrgencia:

    def test_inat_ant_returns_100(self):
        """INAT.ANT always maps to urgencia=100 (highest urgency)."""
        assert _calcular_urgencia("INAT.ANT", None, None) == 100.0

    def test_inat_rec_returns_90(self):
        """INAT.REC maps to urgencia=90."""
        assert _calcular_urgencia("INAT.REC", None, None) == 90.0

    def test_em_risco_returns_70(self):
        """EM RISCO maps to urgencia=70."""
        assert _calcular_urgencia("EM RISCO", None, None) == 70.0

    def test_prospect_returns_10(self):
        """PROSPECT maps to urgencia=10 (low urgency — no history)."""
        assert _calcular_urgencia("PROSPECT", None, None) == 10.0

    def test_lead_returns_10(self):
        """LEAD maps to urgencia=10 (same as PROSPECT)."""
        assert _calcular_urgencia("LEAD", None, None) == 10.0

    def test_ativo_ratio_above_1_5_returns_100(self):
        """Ratio dias/ciclo >= 1.5 means overdue -> urgencia=100."""
        # ratio = 60/30 = 2.0 >= 1.5
        assert _calcular_urgencia("ATIVO", 60, 30.0) == 100.0

    def test_ativo_ratio_between_1_and_1_5_returns_60(self):
        """Ratio 1.0 <= r < 1.5 -> urgencia=60."""
        # ratio = 32/30 ≈ 1.07
        assert _calcular_urgencia("ATIVO", 32, 30.0) == 60.0

    def test_ativo_ratio_below_0_7_returns_20(self):
        """Ratio < 0.7 -> urgencia=20 (well within cycle)."""
        # ratio = 15/30 = 0.5
        assert _calcular_urgencia("ATIVO", 15, 30.0) == 20.0

    def test_ativo_no_ciclo_dias_above_50_returns_60(self):
        """No ciclo_medio, dias > 50 -> urgencia=60 (fallback)."""
        assert _calcular_urgencia("ATIVO", 60, None) == 60.0

    def test_ativo_no_ciclo_dias_below_50_returns_30(self):
        """No ciclo_medio, dias <= 50 -> urgencia=30 (default)."""
        assert _calcular_urgencia("ATIVO", 30, None) == 30.0


# ---------------------------------------------------------------------------
# VALOR factor
# ---------------------------------------------------------------------------

class TestFatorValor:

    def test_a_maduro_returns_100(self):
        """Curva A + MADURO = 100 (best client category)."""
        assert _calcular_valor("A", "MADURO") == 100.0

    def test_a_fidelizado_returns_100(self):
        """Curva A + FIDELIZADO = 100 (premium category)."""
        assert _calcular_valor("A", "FIDELIZADO") == 100.0

    def test_a_outros_returns_80(self):
        """Curva A without premium type = 80."""
        assert _calcular_valor("A", "RECORRENTE") == 80.0

    def test_b_recorrente_returns_60(self):
        """Curva B + RECORRENTE = 60."""
        assert _calcular_valor("B", "RECORRENTE") == 60.0

    def test_b_outros_returns_50(self):
        """Curva B without premium = 50."""
        assert _calcular_valor("B", "NOVO") == 50.0

    def test_c_returns_20(self):
        """Curva C always = 20."""
        assert _calcular_valor("C", "MADURO") == 20.0

    def test_no_abc_returns_low_score(self):
        """No ABC classification returns low score (10 default)."""
        assert _calcular_valor("", "") == 10.0


# ---------------------------------------------------------------------------
# FOLLOWUP factor
# ---------------------------------------------------------------------------

class TestFatorFollowup:

    def test_none_returns_50_neutral(self):
        """No follow-up scheduled = 50 (neutral, does not penalise)."""
        assert _calcular_followup(None) == 50.0

    def test_7_days_late_returns_100(self):
        """7+ days overdue -> urgency = 100."""
        assert _calcular_followup(7) == 100.0
        assert _calcular_followup(10) == 100.0

    def test_3_days_late_returns_80(self):
        """3-6 days overdue -> 80."""
        assert _calcular_followup(3) == 80.0
        assert _calcular_followup(6) == 80.0

    def test_1_day_late_returns_70(self):
        """1-2 days overdue -> 70."""
        assert _calcular_followup(1) == 70.0

    def test_same_day_returns_60(self):
        """0 days = follow-up is today -> 60."""
        assert _calcular_followup(0) == 60.0

    def test_3_days_future_returns_40(self):
        """3 days in the future (atraso=-3) -> 40."""
        assert _calcular_followup(-3) == 40.0

    def test_far_future_returns_20(self):
        """More than 3 days in the future -> 20."""
        assert _calcular_followup(-10) == 20.0


# ---------------------------------------------------------------------------
# SINAL factor
# ---------------------------------------------------------------------------

class TestFatorSinal:

    def test_quente_sem_carrinho_returns_80(self):
        """QUENTE without e-commerce cart = 80."""
        assert _calcular_sinal("QUENTE", 0.0) == 80.0

    def test_quente_com_carrinho_returns_100(self):
        """QUENTE with active cart = 100."""
        assert _calcular_sinal("QUENTE", 100.0) == 100.0

    def test_morno_returns_40(self):
        """MORNO without cart = 40."""
        assert _calcular_sinal("MORNO", 0.0) == 40.0

    def test_frio_returns_10(self):
        """FRIO = 10."""
        assert _calcular_sinal("FRIO", 0.0) == 10.0

    def test_critico_returns_90(self):
        """CRITICO = 90 (high urgency but negative signal)."""
        assert _calcular_sinal("CRITICO", 0.0) == 90.0

    def test_temperatura_with_emoji_stripped_correctly(self):
        """Emoji prefix on temperatura is stripped before lookup."""
        svc = ScoreService()
        c_emoji = _make_cliente(temperatura="🔥 QUENTE")
        c_clean = _make_cliente(temperatura="QUENTE")
        assert svc.calcular(c_emoji)["fator_sinal"] == svc.calcular(c_clean)["fator_sinal"]


# ---------------------------------------------------------------------------
# TENTATIVA factor
# ---------------------------------------------------------------------------

class TestFatorTentativa:

    def test_t1_returns_10(self):
        """T1 = 10 (first unanswered attempt, low weight)."""
        assert _calcular_tentativa("T1") == 10.0

    def test_t2_returns_10(self):
        """T2 = 10 (still early in the sequence)."""
        assert _calcular_tentativa("T2") == 10.0

    def test_t3_returns_50(self):
        """T3 = 50 (getting persistent)."""
        assert _calcular_tentativa("T3") == 50.0

    def test_t4_returns_100(self):
        """T4 = 100 (max persistence, maximum urgency)."""
        assert _calcular_tentativa("T4") == 100.0

    def test_empty_returns_zero(self):
        """No tentativa = 0."""
        assert _calcular_tentativa("") == 0.0

    def test_none_str_returns_zero(self):
        """None tentativa = 0."""
        assert _calcular_tentativa(None) == 0.0


# ---------------------------------------------------------------------------
# SITUACAO factor
# ---------------------------------------------------------------------------

class TestFatorSituacao:

    def test_em_risco_returns_80(self):
        """EM RISCO situation gets highest situacao factor = 80."""
        assert _calcular_situacao_fator("EM RISCO") == 80.0

    def test_ativo_returns_40(self):
        """ATIVO = 40 (healthy, moderate urgency)."""
        assert _calcular_situacao_fator("ATIVO") == 40.0

    def test_inat_rec_returns_20(self):
        """INAT.REC = 20."""
        assert _calcular_situacao_fator("INAT.REC") == 20.0

    def test_inat_ant_returns_20(self):
        """INAT.ANT = 20."""
        assert _calcular_situacao_fator("INAT.ANT") == 20.0

    def test_prospect_returns_10(self):
        """PROSPECT = 10."""
        assert _calcular_situacao_fator("PROSPECT") == 10.0

    def test_unknown_returns_zero(self):
        """Unknown situacao = 0."""
        assert _calcular_situacao_fator("DESCONHECIDO") == 0.0


# ---------------------------------------------------------------------------
# Prioridade mapping (P0-P7)
# ---------------------------------------------------------------------------

class TestPrioridade:

    def test_prioridade_curta_max_5_chars_for_all_situacoes(self):
        """prioridade_curta must fit in String(5) in the DB model."""
        svc = ScoreService()
        for situacao in ["ATIVO", "INAT.REC", "INAT.ANT", "PROSPECT", "LEAD"]:
            c = _make_cliente(situacao=situacao)
            r = svc.calcular(c)
            assert len(r["prioridade_curta"]) <= 5, (
                f"prioridade_curta='{r['prioridade_curta']}' exceeds String(5) for situacao={situacao}"
            )

    def test_p0_for_problema_aberto(self):
        """problema_aberto=True must always return P0 IMEDIATA regardless of score."""
        svc = ScoreService()
        c = _make_cliente(situacao="PROSPECT", problema_aberto=True)
        r = svc.calcular(c)
        assert r["prioridade"] == "P0 IMEDIATA"
        assert r["prioridade_curta"] == "P0"

    def test_p2_for_orcamento_resultado(self):
        """resultado=ORCAMENTO -> P2 NEGOCIACAO ATIVA."""
        svc = ScoreService()
        c = _make_cliente(resultado="ORCAMENTO")
        r = svc.calcular(c)
        assert r["prioridade"] == "P2 NEGOCIACAO ATIVA"
        assert r["prioridade_curta"] == "P2"

    def test_p3_for_suporte_resultado(self):
        """resultado=SUPORTE -> P3 PROBLEMA."""
        svc = ScoreService()
        c = _make_cliente(resultado="SUPORTE")
        r = svc.calcular(c)
        assert r["prioridade"] == "P3 PROBLEMA"
        assert r["prioridade_curta"] == "P3"

    def test_p7_for_prospect_situacao(self):
        """situacao=PROSPECT -> P7 PROSPECCAO."""
        svc = ScoreService()
        c = _make_cliente(situacao="PROSPECT")
        r = svc.calcular(c)
        assert r["prioridade"] == "P7 PROSPECCAO"
        assert r["prioridade_curta"] == "P7"

    def test_p6_for_inat_ant_low_score(self):
        """INAT.ANT with low score -> P6 INAT. ANTIGO."""
        svc = ScoreService()
        # Force low score: C + FRIO + T1 + no FU
        c = _make_cliente(situacao="INAT.ANT", curva_abc="C", temperatura="FRIO", tentativas="T1")
        r = svc.calcular(c)
        # Verify score < 80 (required for P6)
        assert r["score"] < 80
        assert r["prioridade"] == "P6 INAT. ANTIGO"
        assert r["prioridade_curta"] == "P6"

    def test_p5_for_inat_rec_low_score(self):
        """INAT.REC with low score (<75) -> P5 INAT. RECENTE."""
        svc = ScoreService()
        c = _make_cliente(situacao="INAT.REC", curva_abc="C", temperatura="FRIO", tentativas="T1")
        r = svc.calcular(c)
        assert r["score"] < 75
        assert r["prioridade"] == "P5 INAT. RECENTE"
        assert r["prioridade_curta"] == "P5"

    def test_weighted_score_formula_known_values(self):
        """
        Verify the weighted score formula with a hand-calculated case.

        ATIVO, B, NOVO, MORNO, T2, dias=15, ciclo=30, no FU:
          urgencia  = 20  (ratio=0.5 < 0.7)
          valor     = 50  (B, no premium)
          followup  = 50  (None -> neutral)
          sinal     = 40  (MORNO)
          tentativa = 10  (T2)
          situacao  = 40  (ATIVO)

          score = 20*0.30 + 50*0.25 + 50*0.20 + 40*0.15 + 10*0.05 + 40*0.05
                = 6.0 + 12.5 + 10.0 + 6.0 + 0.5 + 2.0 = 37.0
        """
        svc = ScoreService()
        c = _make_cliente(
            situacao="ATIVO",
            curva_abc="B",
            tipo_cliente="NOVO",
            temperatura="MORNO",
            tentativas="T2",
            dias_sem_compra=15,
            ciclo_medio=30.0,
            followup_dias=None,
        )
        r = svc.calcular(c)
        assert r["score"] == 37.0, f"Expected 37.0, got {r['score']}"
