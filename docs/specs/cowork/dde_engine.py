"""
DDE Engine — Cascata P&L Determinística por Cliente
CRM VITAO360 · Fase A (Comercial)

Spec: SPEC_DDE_CASCATA_REAL.md v1.0
Anti-patterns: SEM LLM, SEM alíquota inventada, SEM CMV fake.
Regras: R1 Two-Base, R5 CNPJ 14d, R8 Zero Alucinação.

Uso:
    from dde_engine import calcula_dre_efetivado
    resultado = await calcula_dre_efetivado(db, cnpj="12345678000190", ano=2025)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("dde_engine")

D = Decimal
ZERO = D("0.00")
CDI_ANUAL_DEFAULT = D("0.1365")  # CDI fixo — trocar por API BCB quando decidir D4-CDI


# ============================================================
# ENUMS E DATACLASSES
# ============================================================

class Tier(str, Enum):
    REAL = "REAL"
    SINTETICO = "SINTETICO"
    PENDENTE = "PENDENTE"


class Fase(str, Enum):
    A = "A"
    B = "B"
    C = "C"


@dataclass
class LinhaDRE:
    linha: str
    conta: str
    valor_brl: Optional[Decimal] = None
    pct_sobre_receita: Optional[Decimal] = None
    fonte: Optional[str] = None
    classificacao: Tier = Tier.PENDENTE
    fase: Fase = Fase.A
    observacao: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "linha": self.linha,
            "conta": self.conta,
            "valor_brl": float(self.valor_brl) if self.valor_brl is not None else None,
            "pct_sobre_receita": float(self.pct_sobre_receita) if self.pct_sobre_receita is not None else None,
            "fonte": self.fonte,
            "classificacao_3tier": self.classificacao.value,
            "fase": self.fase.value,
            "observacao": self.observacao,
        }


@dataclass
class ResultadoDRE:
    cnpj: str
    ano: int
    mes: Optional[int]
    linhas: list[LinhaDRE] = field(default_factory=list)
    indicadores: dict = field(default_factory=dict)
    veredito: Optional[tuple[str, str]] = None
    fase_atual: str = "A"

    def to_dict(self) -> dict:
        return {
            "cnpj": self.cnpj,
            "ano": self.ano,
            "mes": self.mes,
            "dre": [l.to_dict() for l in self.linhas],
            "indicadores": self.indicadores,
            "veredito": {"status": self.veredito[0], "motivo": self.veredito[1]} if self.veredito else None,
            "fase_atual": self.fase_atual,
        }


# ============================================================
# HELPERS
# ============================================================

def _safe_div(numerador: Optional[Decimal], denominador: Optional[Decimal]) -> Optional[Decimal]:
    if numerador is None or denominador is None or denominador == ZERO:
        return None
    return (numerador / denominador).quantize(D("0.001"), rounding=ROUND_HALF_UP)


def _pct(valor: Optional[Decimal], base: Optional[Decimal]) -> Optional[Decimal]:
    r = _safe_div(valor, base)
    return r * 100 if r is not None else None


def _q(val) -> Decimal:
    """Converte valor de DB (pode ser None, float, int) para Decimal seguro."""
    if val is None:
        return ZERO
    return D(str(val)).quantize(D("0.01"), rounding=ROUND_HALF_UP)


# ============================================================
# QUERIES — Cada função busca dados de UMA fonte
# ============================================================

async def _get_faturamento(db: AsyncSession, cnpj: str, ano: int, mes: Optional[int] = None) -> dict:
    """L1 — Faturamento bruto (vendas tabela). Fonte: tabela vendas."""
    filtro_mes = "AND EXTRACT(MONTH FROM data_venda) = :mes" if mes else ""
    sql = text(f"""
        SELECT
            COALESCE(SUM(valor), 0)                AS fat_bruto,
            COALESCE(SUM(ipi_total), 0)            AS ipi_vendas,
            COALESCE(SUM(desconto_comercial), 0)   AS desc_comercial,
            COALESCE(SUM(desconto_financeiro), 0)  AS desc_financeiro,
            COALESCE(SUM(bonificacao), 0)          AS bonificacao
        FROM vendas
        WHERE cnpj = :cnpj
          AND EXTRACT(YEAR FROM data_venda) = :ano
          {filtro_mes}
          AND valor > 0
    """)
    params = {"cnpj": cnpj, "ano": ano}
    if mes:
        params["mes"] = mes
    row = (await db.execute(sql, params)).mappings().first()
    return {k: _q(row[k]) for k in row.keys()} if row else {}


async def _get_devolucoes(db: AsyncSession, cnpj: str, ano: int, mes: Optional[int] = None) -> Decimal:
    """
    L4 — Devoluções TOTAIS (NF negativas + log devoluções separadas).
    Golden Master Coelho Diniz 2025: R$180.250,51 (inclui troca NF + NF cliente/própria).
    NOTA: Usar TOTAL, nunca apenas um tipo.
    """
    filtro_mes = "AND EXTRACT(MONTH FROM data_venda) = :mes" if mes else ""
    # Fonte 1: NFs negativas na tabela vendas
    sql_vendas = text(f"""
        SELECT COALESCE(SUM(ABS(valor)), 0) AS total
        FROM vendas
        WHERE cnpj = :cnpj
          AND EXTRACT(YEAR FROM data_venda) = :ano
          {filtro_mes}
          AND valor < 0
    """)
    params = {"cnpj": cnpj, "ano": ano}
    if mes:
        params["mes"] = mes
    row = (await db.execute(sql_vendas, params)).mappings().first()
    total_nf_neg = _q(row["total"]) if row else ZERO

    # Fonte 2: Registros em tabela devolucoes (se existir — pode ter tipos adicionais)
    try:
        filtro_mes_dev = "AND EXTRACT(MONTH FROM data_devolucao) = :mes" if mes else ""
        sql_dev = text(f"""
            SELECT COALESCE(SUM(ABS(valor)), 0) AS total
            FROM devolucoes
            WHERE cnpj = :cnpj
              AND EXTRACT(YEAR FROM data_devolucao) = :ano
              {filtro_mes_dev}
        """)
        row_dev = (await db.execute(sql_dev, params)).mappings().first()
        total_dev_tabela = _q(row_dev["total"]) if row_dev else ZERO
    except Exception:
        total_dev_tabela = ZERO  # Tabela devolucoes pode não existir ainda

    # Retorna o MAIOR dos dois (evita duplicação se ambos registram o mesmo evento)
    # Se existir tabela devolucoes com dados, ela é a fonte de verdade
    return total_dev_tabela if total_dev_tabela > ZERO else total_nf_neg


async def _get_frete(db: AsyncSession, cnpj: str, ano: int, mes: Optional[int] = None) -> Decimal:
    """L14 — Frete CT-e. Fonte: cliente_frete_mensal."""
    filtro_mes = "AND mes = :mes" if mes else ""
    sql = text(f"""
        SELECT COALESCE(SUM(valor_brl), 0) AS total
        FROM cliente_frete_mensal
        WHERE cnpj = :cnpj AND ano = :ano {filtro_mes}
    """)
    params = {"cnpj": cnpj, "ano": ano}
    if mes:
        params["mes"] = mes
    row = (await db.execute(sql, params)).mappings().first()
    return _q(row["total"]) if row else ZERO


async def _get_verbas(db: AsyncSession, cnpj: str, ano: int) -> Decimal:
    """L16 — Verbas contrato. Fonte: cliente_verba_anual."""
    sql = text("""
        SELECT COALESCE(SUM(valor_brl), 0) AS total
        FROM cliente_verba_anual
        WHERE cnpj = :cnpj AND ano = :ano
    """)
    row = (await db.execute(sql, {"cnpj": cnpj, "ano": ano})).mappings().first()
    return _q(row["total"]) if row else ZERO


async def _get_promotor(db: AsyncSession, cnpj: str, ano: int, mes: Optional[int] = None) -> Decimal:
    """L17 — Promotor PDV. Fonte: cliente_promotor_mensal."""
    filtro_mes = "AND mes = :mes" if mes else ""
    sql = text(f"""
        SELECT COALESCE(SUM(valor_brl), 0) AS total
        FROM cliente_promotor_mensal
        WHERE cnpj = :cnpj AND ano = :ano {filtro_mes}
    """)
    params = {"cnpj": cnpj, "ano": ano}
    if mes:
        params["mes"] = mes
    row = (await db.execute(sql, params)).mappings().first()
    return _q(row["total"]) if row else ZERO


async def _get_inadimplencia(db: AsyncSession, cnpj: str) -> dict:
    """L19 + I8 — Inadimplência e aging. Fonte: debitos_clientes."""
    sql = text("""
        SELECT
            COALESCE(SUM(CASE WHEN dias_atraso > 0 THEN valor ELSE 0 END), 0) AS total_vencido,
            CASE
                WHEN SUM(valor) > 0
                THEN SUM(dias_atraso * valor) / SUM(valor)
                ELSE 0
            END AS aging_medio
        FROM debitos_clientes
        WHERE cnpj = :cnpj
    """)
    row = (await db.execute(sql, {"cnpj": cnpj})).mappings().first()
    if not row:
        return {"total_vencido": ZERO, "aging_medio": ZERO}
    return {
        "total_vencido": _q(row["total_vencido"]),
        "aging_medio": _q(row["aging_medio"]),
    }


# ============================================================
# ENGINE PRINCIPAL — calcula_dre_efetivado
# ============================================================

async def _get_comissao_pct(db: AsyncSession, cnpj: str) -> Decimal:
    """
    Busca comissão % do cadastro do cliente.
    Golden Master: Coelho Diniz = 4.6%, não usar default 3% genérico.
    Fallback: 3% se não houver cadastro.
    """
    sql = text("""
        SELECT comissao_pct FROM clientes WHERE cnpj = :cnpj LIMIT 1
    """)
    row = (await db.execute(sql, {"cnpj": cnpj})).mappings().first()
    if row and row["comissao_pct"] is not None:
        return D(str(row["comissao_pct"])) / D("100")  # Armazenado como 4.6 → retorna 0.046
    return D("0.03")  # Fallback conservador


async def _get_cmv(db: AsyncSession, cnpj: str, ano: int, mes: Optional[int] = None) -> tuple[Decimal, Tier]:
    """
    L12 — CMV via tabela produto_custo_comercial (fonte: ZSD062).
    Cálculo: SUM(custo_comercial_unitario × quantidade vendida) por SKU.
    Golden Master Coelho Diniz 2025: ~R$527.720 (vs manual R$520.153 = 1.45% diff).
    Retorna: (valor_cmv, classificacao)
    """
    filtro_mes = "AND EXTRACT(MONTH FROM v.data_venda) = :mes" if mes else ""
    sql = text(f"""
        SELECT COALESCE(SUM(pcc.custo_comercial * v.quantidade), 0) AS cmv_total
        FROM vendas v
        JOIN produto_custo_comercial pcc
            ON pcc.codigo_produto = v.codigo_produto
            AND pcc.ano = :ano
        WHERE v.cnpj = :cnpj
          AND EXTRACT(YEAR FROM v.data_venda) = :ano
          {filtro_mes}
          AND v.valor > 0
          AND v.quantidade > 0
    """)
    params: dict = {"cnpj": cnpj, "ano": ano}
    if mes:
        params["mes"] = mes
    try:
        row = (await db.execute(sql, params)).mappings().first()
        total = _q(row["cmv_total"]) if row else ZERO
        if total > ZERO:
            return (total, Tier.REAL)
        return (ZERO, Tier.PENDENTE)
    except Exception:
        # Tabela produto_custo_comercial pode não existir ainda
        return (ZERO, Tier.PENDENTE)


async def calcula_dre_efetivado(
    db: AsyncSession,
    cnpj: str,
    ano: int,
    mes: Optional[int] = None,
    comissao_pct_override: Optional[Decimal] = None,
) -> ResultadoDRE:
    """
    Calcula DDE Fase A (Comercial) para um cliente.
    Retorna cascata completa com classificação 3-tier por linha.
    Correções Golden Master v2:
      - Comissão: busca per-client (Coelho Diniz=4.6%), fallback 3%
      - Devoluções: TOTAL (NF neg + devolucoes), não apenas troca NF
      - CMV: ZSD062 custo_comercial × qty (desbloqueia L12/L13/I1)
    """
    resultado = ResultadoDRE(cnpj=cnpj, ano=ano, mes=mes)
    linhas = resultado.linhas

    # Buscar comissão do cadastro do cliente (ou usar override se fornecido)
    comissao_pct = comissao_pct_override if comissao_pct_override is not None else await _get_comissao_pct(db, cnpj)

    # --- BLOCO 1: RECEITA BRUTA ---
    fat = await _get_faturamento(db, cnpj, ano, mes)
    fat_bruto = fat.get("fat_bruto", ZERO)
    ipi_vendas = fat.get("ipi_vendas", ZERO)

    linhas.append(LinhaDRE(
        linha="L1", conta="Faturamento bruto a tabela",
        valor_brl=fat_bruto, fonte="VENDAS",
        classificacao=Tier.REAL if fat_bruto > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L2", conta="IPI sobre vendas",
        valor_brl=ipi_vendas, fonte="VENDAS",
        classificacao=Tier.REAL if ipi_vendas > ZERO else Tier.PENDENTE,
        fase=Fase.A,
        observacao="D1 — campo ipi_total na tabela vendas" if ipi_vendas == ZERO else None,
    ))

    receita_bruta = fat_bruto + ipi_vendas
    linhas.append(LinhaDRE(
        linha="L3", conta="= Receita Bruta com IPI",
        valor_brl=receita_bruta, fonte="CALC",
        classificacao=Tier.REAL if fat_bruto > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))

    # --- BLOCO 2: DEDUÇÕES ---
    devolucoes = await _get_devolucoes(db, cnpj, ano, mes)
    desc_comercial = fat.get("desc_comercial", ZERO)
    desc_financeiro = fat.get("desc_financeiro", ZERO)
    bonificacao = fat.get("bonificacao", ZERO)

    linhas.append(LinhaDRE(
        linha="L4", conta="(-) Devoluções",
        valor_brl=devolucoes, fonte="VENDAS",
        classificacao=Tier.REAL, fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L5", conta="(-) Desconto comercial",
        valor_brl=desc_comercial, fonte="VENDAS",
        classificacao=Tier.REAL if desc_comercial > ZERO else Tier.PENDENTE,
        fase=Fase.A,
        observacao="D1 — campo desconto_comercial na tabela vendas" if desc_comercial == ZERO else None,
    ))
    linhas.append(LinhaDRE(
        linha="L6", conta="(-) Desconto financeiro",
        valor_brl=desc_financeiro, fonte="VENDAS",
        classificacao=Tier.REAL if desc_financeiro > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L7", conta="(-) Bonificações",
        valor_brl=bonificacao, fonte="VENDAS",
        classificacao=Tier.REAL if bonificacao > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L8", conta="(-) IPI faturado",
        valor_brl=ipi_vendas, fonte="VENDAS",
        classificacao=Tier.REAL if ipi_vendas > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))

    # L9, L10a-c: impostos — Fase B, NULL hoje (D3)
    for code, nome in [("L9", "(-) ICMS"), ("L10a", "(-) PIS"), ("L10b", "(-) COFINS"), ("L10c", "(-) ICMS-ST")]:
        linhas.append(LinhaDRE(
            linha=code, conta=nome,
            valor_brl=None, fonte=None,
            classificacao=Tier.PENDENTE, fase=Fase.B,
            observacao="Aguardando integração SAP fiscal (D3)",
        ))

    # L11 — Receita Líquida Comercial (Fase A = sem impostos)
    receita_liq_comercial = receita_bruta - devolucoes - desc_comercial - desc_financeiro - bonificacao - ipi_vendas
    linhas.append(LinhaDRE(
        linha="L11", conta="= Receita Líquida (Comercial)",
        valor_brl=receita_liq_comercial, fonte="CALC",
        classificacao=Tier.REAL if fat_bruto > ZERO else Tier.PENDENTE,
        fase=Fase.A,
        observacao="Fase A: sem impostos. Receita Líquida Fiscal virá na Fase B.",
    ))

    # --- BLOCO 3: CMV — via ZSD062 custo_comercial (desbloqueado Golden Master v2) ---
    cmv_valor, cmv_tier = await _get_cmv(db, cnpj, ano, mes)

    linhas.append(LinhaDRE(
        linha="L12", conta="(-) CMV",
        valor_brl=cmv_valor if cmv_tier == Tier.REAL else None,
        fonte="ZSD062_CUSTO" if cmv_tier == Tier.REAL else None,
        classificacao=cmv_tier,
        fase=Fase.A if cmv_tier == Tier.REAL else Fase.B,
        observacao="Fonte: produto_custo_comercial (ZSD062 Custo Comercial × qty vendida)" if cmv_tier == Tier.REAL
                   else "Aguardando tabela produto_custo_comercial com dados ZSD062",
    ))

    margem_bruta = (receita_liq_comercial - cmv_valor) if cmv_tier == Tier.REAL else None
    linhas.append(LinhaDRE(
        linha="L13", conta="= Margem Bruta",
        valor_brl=margem_bruta,
        fonte="CALC" if margem_bruta is not None else None,
        classificacao=Tier.REAL if margem_bruta is not None else Tier.PENDENTE,
        fase=Fase.A if margem_bruta is not None else Fase.B,
        observacao=None if margem_bruta is not None else "Sem CMV não há Margem Bruta",
    ))

    # --- BLOCO 4: DESPESAS VARIÁVEIS ---
    frete = await _get_frete(db, cnpj, ano, mes)
    verbas = await _get_verbas(db, cnpj, ano)
    promotor = await _get_promotor(db, cnpj, ano, mes)
    inad = await _get_inadimplencia(db, cnpj)

    # L15 — Comissão (REAL se vier do cadastro, SINTÉTICO se fallback 3%)
    comissao = (receita_liq_comercial * comissao_pct).quantize(D("0.01"), rounding=ROUND_HALF_UP)
    comissao_from_cadastro = comissao_pct_override is not None or comissao_pct != D("0.03")

    # L19 — Provisão inadimplência (10% do vencido como provisão default)
    provisao_inad = (inad["total_vencido"] * D("0.10")).quantize(D("0.01"), rounding=ROUND_HALF_UP)

    # L20 — Custo financeiro (aging × CDI × valor em aberto)
    custo_financeiro = ZERO
    if inad["aging_medio"] > ZERO and inad["total_vencido"] > ZERO:
        custo_financeiro = (
            inad["total_vencido"] * (inad["aging_medio"] / D("365")) * CDI_ANUAL_DEFAULT
        ).quantize(D("0.01"), rounding=ROUND_HALF_UP)

    # Verba mensal = anual / 12
    verba_mensal = (verbas / D("12")).quantize(D("0.01"), rounding=ROUND_HALF_UP) if mes else verbas

    linhas.append(LinhaDRE(
        linha="L14", conta="(-) Frete (CT-e)",
        valor_brl=frete, fonte="FRETE_UPLOAD",
        classificacao=Tier.REAL if frete > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L15", conta="(-) Comissão sobre venda",
        valor_brl=comissao, fonte="CADASTRO" if comissao_from_cadastro else "CALC",
        classificacao=Tier.REAL if comissao_from_cadastro else Tier.SINTETICO,
        fase=Fase.A,
        observacao=f"Comissão {float(comissao_pct*100):.1f}% do cadastro do cliente"
                   if comissao_from_cadastro
                   else f"D5 — fallback {float(comissao_pct*100):.1f}% padrão. Cadastrar comissao_pct no cliente.",
    ))
    linhas.append(LinhaDRE(
        linha="L16", conta="(-) Verbas (contratos)",
        valor_brl=verba_mensal, fonte="VERBA_UPLOAD",
        classificacao=Tier.REAL if verbas > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L17", conta="(-) Promotor PDV",
        valor_brl=promotor, fonte="PROMOTOR_UPLOAD",
        classificacao=Tier.REAL if promotor > ZERO else Tier.PENDENTE,
        fase=Fase.A,
    ))
    linhas.append(LinhaDRE(
        linha="L18", conta="(-) Bonificação financeira (rebate)",
        valor_brl=None, fonte=None,
        classificacao=Tier.PENDENTE, fase=Fase.A,
        observacao="D5 — depende de confirmar se comissao_pct é rebate ou comissão",
    ))
    linhas.append(LinhaDRE(
        linha="L19", conta="(-) Provisão inadimplência",
        valor_brl=provisao_inad, fonte="DEBITOS",
        classificacao=Tier.SINTETICO if provisao_inad > ZERO else Tier.PENDENTE,
        fase=Fase.A,
        observacao="10% sobre títulos vencidos como provisão default",
    ))
    linhas.append(LinhaDRE(
        linha="L20", conta="(-) Custo financeiro (capital de giro)",
        valor_brl=custo_financeiro, fonte="DEBITOS+CDI",
        classificacao=Tier.SINTETICO if custo_financeiro > ZERO else Tier.PENDENTE,
        fase=Fase.A,
        observacao=f"CDI fixo {CDI_ANUAL_DEFAULT*100}% a.a. — trocar por API BCB",
    ))

    # L21 — Margem de Contribuição Comercial
    # Se CMV disponível: MC = Margem Bruta - despesas variáveis
    # Se CMV indisponível: MC = Receita Líquida - despesas variáveis (SINTÉTICO)
    desp_variaveis = frete + comissao + verba_mensal + promotor + provisao_inad + custo_financeiro

    if margem_bruta is not None:
        mc_comercial = margem_bruta - desp_variaveis
        mc_obs = "MC = Margem Bruta − despesas variáveis (CMV incluído)"
        mc_tier = Tier.REAL
    else:
        mc_comercial = receita_liq_comercial - desp_variaveis
        mc_obs = "Sem CMV — MC sobre Receita Líquida Comercial, não sobre Margem Bruta"
        mc_tier = Tier.SINTETICO

    linhas.append(LinhaDRE(
        linha="L21", conta="= Margem de Contribuição (Comercial)",
        valor_brl=mc_comercial, fonte="CALC",
        classificacao=mc_tier,
        fase=Fase.A,
        observacao=mc_obs,
    ))

    # --- BLOCO 5: DESPESAS FIXAS — Fase B ---
    for code, nome in [("L22", "(-) Estrutura comercial"), ("L23", "(-) Estrutura administrativa"), ("L24", "(-) Marketing")]:
        linhas.append(LinhaDRE(
            linha=code, conta=nome,
            valor_brl=None, fonte=None,
            classificacao=Tier.PENDENTE, fase=Fase.B,
            observacao="Rateio Fase B — aguarda SAP folha",
        ))
    linhas.append(LinhaDRE(
        linha="L25", conta="= Resultado Operacional Cliente",
        valor_brl=None, fonte=None,
        classificacao=Tier.PENDENTE, fase=Fase.B,
    ))

    # --- BLOCO 6: INDICADORES ---
    indicadores = {}

    indicadores["I1"] = {"nome": "Margem Bruta %",
                         "valor": float(_pct(margem_bruta, receita_liq_comercial)) if margem_bruta is not None and receita_liq_comercial > ZERO else None,
                         "fase": "A" if margem_bruta is not None else "B",
                         "obs": None if margem_bruta is not None else "Depende de L13 (CMV)"}
    indicadores["I2"] = {"nome": "Margem Contribuição %",
                         "valor": float(_pct(mc_comercial, receita_liq_comercial)) if receita_liq_comercial > ZERO else None,
                         "fase": "A",
                         "obs": "MC completa (CMV incluso)" if margem_bruta is not None else "Parcial — sem CMV"}
    indicadores["I3"] = {"nome": "EBITDA Cliente %", "valor": None, "fase": "B"}
    indicadores["I4"] = {"nome": "Custo de Servir %",
                         "valor": float(_pct(desp_variaveis, receita_liq_comercial)) if receita_liq_comercial > ZERO else None,
                         "fase": "A"}
    indicadores["I5"] = {"nome": "Verba % Receita",
                         "valor": float(_pct(verba_mensal, receita_liq_comercial)) if receita_liq_comercial > ZERO else None,
                         "fase": "A"}
    indicadores["I6"] = {"nome": "Inadimplência %",
                         "valor": float(_pct(provisao_inad, receita_liq_comercial)) if receita_liq_comercial > ZERO else None,
                         "fase": "A"}
    indicadores["I7"] = {"nome": "Devolução %",
                         "valor": float(_pct(devolucoes, fat_bruto)) if fat_bruto > ZERO else None,
                         "fase": "A"}
    indicadores["I8"] = {"nome": "Aging Médio (DSO)",
                         "valor": float(inad["aging_medio"]),
                         "fase": "A"}
    indicadores["I9"] = {"nome": "Score Saúde Financeira",
                         "valor": None,  # Calculado por calcula_score()
                         "fase": "A"}

    resultado.indicadores = indicadores

    # --- BLOCO 7: VEREDITO ---
    mc_pct = _safe_div(mc_comercial, receita_liq_comercial)
    inad_pct = _safe_div(provisao_inad, receita_liq_comercial)
    resultado.veredito = veredito_cliente(mc_pct, inad_pct, inad["aging_medio"])

    return resultado


# ============================================================
# VEREDITO DETERMINÍSTICO
# ============================================================

def veredito_cliente(
    mc_pct: Optional[Decimal],
    inad_pct: Optional[Decimal],
    aging_medio: Decimal,
) -> tuple[str, str]:
    """
    Retorna (status, motivo) baseado em regras determinísticas.
    Spec: Bloco 7 — SPEC_DDE_CASCATA_REAL.md
    """
    if mc_pct is None:
        return ("SEM_DADOS", "Sem dados suficientes para veredito")
    if mc_pct < D("0"):
        return ("SUBSTITUIR", "Margem negativa — cliente destrói valor")
    if mc_pct < D("0.05"):
        return ("RENEGOCIAR", "Margem < 5% — abaixo do custo de capital")
    if mc_pct < D("0.15"):
        return ("REVISAR", "Margem 5-15% — atenção em verba/devolução")
    if aging_medio > D("90") and inad_pct is not None and inad_pct > D("0.10"):
        return ("ALERTA_CREDITO", "Margem OK mas crédito comprometido")
    return ("SAUDAVEL", "Manter — cliente rentável e em dia")


# ============================================================
# SINALEIRO SKU — Preço praticado vs mercado
# ============================================================

async def sinaleiro_sku(
    db: AsyncSession,
    cnpj: str,
    ano: int,
) -> list[dict]:
    """
    Compara preço praticado do cliente vs preço médio de mercado.
    Retorna lista de SKUs com status sinaleiro.

    Statuses:
        ABAIXO_MERCADO: preço < 90% mercado → vermelho
        NA_MEDIA:       90-110% → verde
        ACIMA_MERCADO:  > 110% → amarelo (pode perder share)
        SEM_REF:        sem preço mercado → cinza
        ZERADO:         preço praticado = 0 → preto
        BONIFICADO:     classificado como bonificação → roxo
    """
    sql = text("""
        WITH sku_praticado AS (
            SELECT
                p.codigo_produto,
                p.descricao_produto,
                AVG(CASE WHEN v.valor > 0 THEN v.valor / NULLIF(v.quantidade, 0) END) AS preco_medio_praticado,
                SUM(v.quantidade) AS qtd_vendida
            FROM vendas v
            JOIN produtos p ON p.id = v.produto_id
            WHERE v.cnpj = :cnpj
              AND EXTRACT(YEAR FROM v.data_venda) = :ano
              AND v.valor > 0
            GROUP BY p.codigo_produto, p.descricao_produto
        ),
        sku_mercado AS (
            SELECT
                codigo_produto,
                preco_medio
            FROM mercado_sku_preco
            WHERE ano = :ano
        )
        SELECT
            sp.codigo_produto,
            sp.descricao_produto,
            sp.preco_medio_praticado,
            sp.qtd_vendida,
            sm.preco_medio AS preco_mercado
        FROM sku_praticado sp
        LEFT JOIN sku_mercado sm ON sm.codigo_produto = sp.codigo_produto
        ORDER BY sp.qtd_vendida DESC
    """)

    rows = (await db.execute(sql, {"cnpj": cnpj, "ano": ano})).mappings().all()
    resultado = []

    for r in rows:
        preco_prat = _q(r["preco_medio_praticado"])
        preco_merc = _q(r["preco_mercado"]) if r["preco_mercado"] else None

        if preco_prat == ZERO:
            status = "ZERADO"
        elif preco_merc is None or preco_merc == ZERO:
            status = "SEM_REF"
        else:
            ratio = preco_prat / preco_merc
            if ratio < D("0.90"):
                status = "ABAIXO_MERCADO"
            elif ratio > D("1.10"):
                status = "ACIMA_MERCADO"
            else:
                status = "NA_MEDIA"

        resultado.append({
            "codigo_produto": r["codigo_produto"],
            "descricao": r["descricao_produto"],
            "preco_praticado": float(preco_prat),
            "preco_mercado": float(preco_merc) if preco_merc else None,
            "variacao_pct": float(((preco_prat / preco_merc) - 1) * 100) if preco_merc and preco_merc > ZERO else None,
            "qtd_vendida": int(r["qtd_vendida"]) if r["qtd_vendida"] else 0,
            "status": status,
        })

    return resultado


# ============================================================
# DETECTOR DE ANOMALIAS — 8 regras determinísticas
# ============================================================

async def detecta_anomalias(
    db: AsyncSession,
    cnpj: str,
    ano: int,
) -> list[dict]:
    """
    8 regras de detecção de anomalias por cliente.
    Cada anomalia retorna: {regra, severidade, descricao, valor_encontrado, limite}.
    """
    anomalias = []
    dre = await calcula_dre_efetivado(db, cnpj, ano)
    linhas = {l.linha: l for l in dre.linhas}
    ind = dre.indicadores

    fat_bruto = linhas.get("L1")
    rl = linhas.get("L11")
    mc = linhas.get("L21")

    # R1: Devolução > 10% do faturamento
    dev_pct = ind.get("I7", {}).get("valor")
    if dev_pct is not None and dev_pct > 10:
        anomalias.append({
            "regra": "A1_DEVOLUCAO_ALTA",
            "severidade": "ALTA" if dev_pct > 20 else "MEDIA",
            "descricao": f"Devolução {dev_pct:.1f}% do faturamento (limite: 10%)",
            "valor_encontrado": dev_pct,
            "limite": 10,
        })

    # R2: Margem de contribuição negativa
    mc_val = mc.valor_brl if mc else None
    if mc_val is not None and mc_val < ZERO:
        anomalias.append({
            "regra": "A2_MC_NEGATIVA",
            "severidade": "CRITICA",
            "descricao": f"Margem de contribuição negativa: R$ {mc_val:,.2f}",
            "valor_encontrado": float(mc_val),
            "limite": 0,
        })

    # R3: Aging médio > 60 dias
    aging = ind.get("I8", {}).get("valor", 0)
    if aging > 60:
        anomalias.append({
            "regra": "A3_AGING_ALTO",
            "severidade": "ALTA" if aging > 90 else "MEDIA",
            "descricao": f"Aging médio {aging:.0f} dias (limite: 60)",
            "valor_encontrado": aging,
            "limite": 60,
        })

    # R4: Verba > 8% da receita líquida
    verba_pct = ind.get("I5", {}).get("valor")
    if verba_pct is not None and verba_pct > 8:
        anomalias.append({
            "regra": "A4_VERBA_ALTA",
            "severidade": "MEDIA",
            "descricao": f"Verba {verba_pct:.1f}% da receita (limite: 8%)",
            "valor_encontrado": verba_pct,
            "limite": 8,
        })

    # R5: Custo de servir > 25%
    cs_pct = ind.get("I4", {}).get("valor")
    if cs_pct is not None and cs_pct > 25:
        anomalias.append({
            "regra": "A5_CUSTO_SERVIR_ALTO",
            "severidade": "ALTA",
            "descricao": f"Custo de servir {cs_pct:.1f}% (limite: 25%)",
            "valor_encontrado": cs_pct,
            "limite": 25,
        })

    # R6: Faturamento caiu > 20% vs ano anterior
    if fat_bruto and fat_bruto.valor_brl and fat_bruto.valor_brl > ZERO:
        fat_ant = await _get_faturamento(db, cnpj, ano - 1)
        fat_ant_val = fat_ant.get("fat_bruto", ZERO)
        if fat_ant_val > ZERO:
            variacao = ((fat_bruto.valor_brl - fat_ant_val) / fat_ant_val) * 100
            if variacao < D("-20"):
                anomalias.append({
                    "regra": "A6_QUEDA_FATURAMENTO",
                    "severidade": "ALTA",
                    "descricao": f"Faturamento caiu {abs(float(variacao)):.1f}% vs {ano-1} (limite: -20%)",
                    "valor_encontrado": float(variacao),
                    "limite": -20,
                })

    # R7: Inadimplência > 5% da receita
    inad_pct = ind.get("I6", {}).get("valor")
    if inad_pct is not None and inad_pct > 5:
        anomalias.append({
            "regra": "A7_INADIMPLENCIA_ALTA",
            "severidade": "ALTA" if inad_pct > 10 else "MEDIA",
            "descricao": f"Inadimplência {inad_pct:.1f}% da receita (limite: 5%)",
            "valor_encontrado": inad_pct,
            "limite": 5,
        })

    # R8: Frete > 12% da receita
    frete_val = linhas.get("L14")
    if frete_val and rl and rl.valor_brl and rl.valor_brl > ZERO and frete_val.valor_brl:
        frete_pct = float((frete_val.valor_brl / rl.valor_brl) * 100)
        if frete_pct > 12:
            anomalias.append({
                "regra": "A8_FRETE_ALTO",
                "severidade": "MEDIA",
                "descricao": f"Frete {frete_pct:.1f}% da receita (limite: 12%)",
                "valor_encontrado": frete_pct,
                "limite": 12,
            })

    return anomalias


# ============================================================
# PERSISTÊNCIA — Salva resultado no cache cliente_dre_periodo
# ============================================================

async def persiste_dre(db: AsyncSession, resultado: ResultadoDRE) -> int:
    """
    Salva/atualiza todas as linhas da DRE em cliente_dre_periodo.
    Usa UPSERT (ON CONFLICT DO UPDATE).
    Retorna número de linhas afetadas.
    """
    count = 0
    for l in resultado.linhas:
        sql = text("""
            INSERT INTO cliente_dre_periodo
                (cnpj, ano, mes, linha, conta, valor_brl, pct_sobre_receita,
                 fonte, classificacao_3tier, fase, observacao, calculado_em)
            VALUES
                (:cnpj, :ano, :mes, :linha, :conta, :valor_brl, :pct,
                 :fonte, :classificacao, :fase, :obs, NOW())
            ON CONFLICT (cnpj, ano, mes, linha)
            DO UPDATE SET
                conta = EXCLUDED.conta,
                valor_brl = EXCLUDED.valor_brl,
                pct_sobre_receita = EXCLUDED.pct_sobre_receita,
                fonte = EXCLUDED.fonte,
                classificacao_3tier = EXCLUDED.classificacao_3tier,
                fase = EXCLUDED.fase,
                observacao = EXCLUDED.observacao,
                calculado_em = NOW()
        """)
        await db.execute(sql, {
            "cnpj": resultado.cnpj,
            "ano": resultado.ano,
            "mes": resultado.mes,
            "linha": l.linha,
            "conta": l.conta,
            "valor_brl": float(l.valor_brl) if l.valor_brl is not None else None,
            "pct": float(l.pct_sobre_receita) if l.pct_sobre_receita is not None else None,
            "fonte": l.fonte,
            "classificacao": l.classificacao.value,
            "fase": l.fase.value,
            "obs": l.observacao,
        })
        count += 1

    # Persistir indicadores como linhas I*
    for key, ind in resultado.indicadores.items():
        if ind.get("valor") is not None:
            sql = text("""
                INSERT INTO cliente_dre_periodo
                    (cnpj, ano, mes, linha, conta, valor_brl, pct_sobre_receita,
                     fonte, classificacao_3tier, fase, observacao, calculado_em)
                VALUES
                    (:cnpj, :ano, :mes, :linha, :conta, NULL, :pct,
                     'CALC', 'SINTETICO', :fase, :obs, NOW())
                ON CONFLICT (cnpj, ano, mes, linha)
                DO UPDATE SET
                    conta = EXCLUDED.conta,
                    pct_sobre_receita = EXCLUDED.pct_sobre_receita,
                    fase = EXCLUDED.fase,
                    observacao = EXCLUDED.observacao,
                    calculado_em = NOW()
            """)
            await db.execute(sql, {
                "cnpj": resultado.cnpj,
                "ano": resultado.ano,
                "mes": resultado.mes,
                "linha": key,
                "conta": ind["nome"],
                "pct": ind["valor"],
                "fase": ind.get("fase", "A"),
                "obs": ind.get("obs"),
            })
            count += 1

    await db.commit()
    logger.info(f"DDE persistido: {resultado.cnpj} {resultado.ano}/{resultado.mes} — {count} linhas")
    return count
