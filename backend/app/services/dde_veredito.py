"""
CRM VITAO360 — DDE Veredito (Onda 3 — OSCAR)

Regras determinísticas para classificar a saúde econômica do cliente.
6 outcomes possíveis: SAUDAVEL | REVISAR | RENEGOCIAR | SUBSTITUIR | ALERTA_CREDITO | SEM_DADOS

Implementa SPEC_DDE_CASCATA_REAL.md Bloco 7.
Engine Python puro, sem LLM. Testável e determinístico.

REGRAS:
  R8 — Se MC% ausente (SEM_DADOS), não fabrica veredito — diz honestamente.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.services.dde_engine import ResultadoDDE

# ---------------------------------------------------------------------------
# Thresholds de veredito (per spec — L3: não alterar sem aprovação)
# ---------------------------------------------------------------------------

MC_SUBSTITUIR: float = 0.0    # Margem < 0% → SUBSTITUIR
MC_RENEGOCIAR: float = 0.05   # Margem 0..5% → RENEGOCIAR
MC_REVISAR: float = 0.15      # Margem 5..15% → REVISAR
AGING_CRITICO: float = 90.0   # Dias de atraso críticos
INADIMP_CRITICA: float = 0.10 # 10% inadimplência → ALERTA_CREDITO


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def veredito(dre: "ResultadoDDE") -> tuple[str, str]:
    """
    Determina o veredito da saúde econômica do cliente.

    Prioridade de avaliação (aplicada em ordem):
      1. SEM_DADOS: MC% ausente (L11 ou L21 não calculável)
      2. SUBSTITUIR: MC% < 0 (cliente destrói valor)
      3. RENEGOCIAR: MC% entre 0% e 5% (abaixo do custo de capital)
      4. REVISAR: MC% entre 5% e 15% (atenção necessária)
      5. ALERTA_CREDITO: MC% saudável, mas aging > 90d E inadimp > 10%
      6. SAUDAVEL: cliente rentável e crédito em dia

    Args:
        dre: ResultadoDDE com indicadores populados pelo dde_engine.

    Returns:
        Tupla (veredito_str, descricao_str)
    """
    mc_pct: float | None = dre.indicadores.get("I2")
    aging: float | None = dre.indicadores.get("I8")
    inadimp_pct: float | None = dre.indicadores.get("I6")

    # SEM_DADOS — Margem de Contribuição não calculável
    if mc_pct is None:
        return (
            "SEM_DADOS",
            "Margem de Contribuição não calculável (L11 ou dados insuficientes). "
            "Necessário L1 (faturamento) para veredito.",
        )

    # SUBSTITUIR — MC negativa: cliente destrói valor
    if mc_pct < MC_SUBSTITUIR:
        return (
            "SUBSTITUIR",
            f"Margem de Contribuição negativa ({mc_pct*100:.1f}%) — cliente destrói valor. "
            "Ação imediata: renegociar ou descontinuar relacionamento.",
        )

    # RENEGOCIAR — MC abaixo do custo de capital
    if mc_pct < MC_RENEGOCIAR:
        return (
            "RENEGOCIAR",
            f"Margem de Contribuição ({mc_pct*100:.1f}%) abaixo de 5% — "
            "abaixo do custo de capital. Renegociar verbas, frete ou preço.",
        )

    # REVISAR — MC entre 5% e 15%: atenção em verba/devolução
    if mc_pct < MC_REVISAR:
        return (
            "REVISAR",
            f"Margem de Contribuição ({mc_pct*100:.1f}%) entre 5% e 15% — "
            "atenção às verbas, devolução e frete. Analisar oportunidades de melhoria.",
        )

    # ALERTA_CREDITO — MC saudável mas crédito comprometido
    if (
        aging is not None
        and inadimp_pct is not None
        and aging > AGING_CRITICO
        and inadimp_pct > INADIMP_CRITICA
    ):
        return (
            "ALERTA_CREDITO",
            f"Margem OK ({mc_pct*100:.1f}%) mas crédito comprometido: "
            f"aging={aging:.0f}d (>{AGING_CRITICO:.0f}d) e "
            f"inadimplência={inadimp_pct*100:.1f}% (>{INADIMP_CRITICA*100:.0f}%). "
            "Revisar limite de crédito e cobrança.",
        )

    # SAUDAVEL — rentável e crédito em dia
    return (
        "SAUDAVEL",
        f"Cliente rentável: margem {mc_pct*100:.1f}% e crédito em dia. "
        "Manter relacionamento — avaliar expansão de mix ou cobertura.",
    )
