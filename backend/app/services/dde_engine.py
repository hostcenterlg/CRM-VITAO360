"""
CRM VITAO360 — DDE Engine (Onda 3 — OSCAR)

Engine determinística Python puro (sem LLM) para a cascata P&L Fase A por cliente.

Fase A — DDE Comercial (sem CMV, sem impostos fiscais SAP):
  Calcula L1..L21 + I1..I9 com classificação 3-tier honesta (REAL/SINTETICO/PENDENTE/NULL).
  Linhas sem dado real = valor=None, classificacao='PENDENTE' ou 'NULL'. ZERO alucinação.

Funções públicas:
  calcula_dre_comercial(cnpj, ano, db) -> ResultadoDDE
  cliente_elegivel_dde(cliente) -> bool

REGRAS:
  R4 — Two-Base: só lê R$ de tabelas VENDA (vendas). Frete/Verba/Promotor são DESPESA.
  R5 — CNPJ: 14 dígitos, string, zero-padded. normaliza_cnpj() no início de toda operação.
  R8 — Zero alucinação: linha sem dado = valor=None. NUNCA inventar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.models.cliente import Cliente
from backend.app.models.cliente_dre import ClienteDrePeriodo
from backend.app.models.cliente_frete import ClienteFretesMensal
from backend.app.models.cliente_promotor import ClientePromotorMensal
from backend.app.models.cliente_verba import ClienteVerbaAnual
from backend.app.models.debito_cliente import DebitoCliente
from backend.app.models.venda import Venda

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Canais elegíveis para DDE (per spec README seção 9)
CANAIS_DDE: frozenset[str] = frozenset({"DIRETO", "INDIRETO", "FOOD_SERVICE"})

# CDI fixo anual para L20 (custo de capital de giro sintético)
# Atualizar trimestralmente ou substituir por API BCB (PTAX) futuramente
CDI_ANUAL: float = 0.13  # 13% a.a. (2026)

# Comissão padrão sobre vendas quando não há dado granular por produto (L15)
# Status: SINTETICO — substituto até D5 definir se comissao_pct é vendedor ou rebate
COMISSAO_DEFAULT_PCT: float = 0.03  # 3% padrão setor

# Precision para arredondamento de Decimal
DECIMAL_PLACES: int = 2
QUANTIZE_CENTS: Decimal = Decimal("0.01")


# ---------------------------------------------------------------------------
# R5 — CNPJ normalização
# ---------------------------------------------------------------------------

def normaliza_cnpj(raw: object) -> str:
    """
    Normaliza CNPJ para 14 dígitos, string, zero-padded.
    R5: NUNCA float. NUNCA int. NUNCA pontuação.
    """
    digits = re.sub(r"\D", "", str(raw))
    return digits.zfill(14)[:14]


# ---------------------------------------------------------------------------
# Dataclasses de saída
# ---------------------------------------------------------------------------

@dataclass
class LinhaDRE:
    """
    Representa uma linha da cascata DDE P&L.

    codigo: ex. 'L1', 'L11', 'I2'
    conta: nome canônico (conforme 22 regex DRE_CORRECOES da Onda 2 NOVEMBER)
    sinal: '+' (entrada), '−' (dedução), '=' (calculada)
    valor: None = PENDENTE/NULL — R8 honestidade > inventar
    pct_receita: percentual sobre L1 (Faturamento Bruto), None se incalculável
    fonte: 'SH' | 'SAP' | 'LOG' | 'CALC' | 'DB'
    classificacao: 'REAL' | 'SINTETICO' | 'PENDENTE' | 'NULL'
    fase: 'A' | 'B' | 'C'
    observacao: nota de rastreabilidade
    """
    codigo: str
    conta: str
    sinal: str
    valor: Optional[Decimal] = None
    pct_receita: Optional[float] = None
    fonte: str = ""
    classificacao: str = "PENDENTE"
    fase: str = "A"
    observacao: str = ""


@dataclass
class ResultadoDDE:
    """
    Resultado completo da cascata DDE para um cliente/ano.

    linhas: lista ordenada de LinhaDRE (L1..L21 + I1..I9)
    indicadores: dict com I1..I9 (valor float ou None)
    veredito: string one-of (SAUDAVEL|REVISAR|RENEGOCIAR|SUBSTITUIR|ALERTA_CREDITO|SEM_DADOS)
    veredito_descricao: frase descritiva
    fase_ativa: 'A' (implementação atual)
    """
    cnpj: str
    ano: int
    linhas: list[LinhaDRE] = field(default_factory=list)
    indicadores: dict = field(default_factory=dict)
    veredito: str = "SEM_DADOS"
    veredito_descricao: str = "Dados insuficientes para veredito"
    fase_ativa: str = "A"


# ---------------------------------------------------------------------------
# Canal scoping — helper público para PAPA (Onda 4)
# ---------------------------------------------------------------------------

def cliente_elegivel_dde(cliente: Cliente) -> bool:
    """
    Retorna True se o canal do cliente está em CANAIS_DDE.
    PAPA (Onda 4) usa este helper para filtrar requests de DDE.
    Engine não levanta exceção — quem decide é a API.
    """
    if not cliente.canal:
        return False
    return cliente.canal.nome in CANAIS_DDE


# ---------------------------------------------------------------------------
# Helpers internos de query
# ---------------------------------------------------------------------------

def _d(value: object) -> Optional[Decimal]:
    """Converte float/int/str para Decimal(2). None retorna None."""
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(QUANTIZE_CENTS, rounding=ROUND_HALF_UP)
    except Exception:
        return None


def _pct(numerador: Optional[Decimal], denominador: Optional[Decimal]) -> Optional[float]:
    """Calcula percentual de forma segura. Retorna None se denominador = 0 ou None."""
    if numerador is None or denominador is None or denominador == Decimal("0"):
        return None
    return float((numerador / denominador).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP))


def _busca_l1(cnpj: str, ano: int, db: Session) -> Optional[Decimal]:
    """L1 — Faturamento Bruto: SUM(valor_pedido) FROM vendas WHERE cnpj AND YEAR=ano."""
    result = (
        db.query(func.sum(Venda.valor_pedido))
        .filter(
            Venda.cnpj == cnpj,
            func.extract("year", Venda.data_pedido) == ano,
        )
        .scalar()
    )
    return _d(result)


def _busca_cliente(cnpj: str, db: Session) -> Optional[Cliente]:
    return db.query(Cliente).filter(Cliente.cnpj == cnpj).first()


def _busca_frete(cnpj: str, ano: int, db: Session) -> Optional[Decimal]:
    """L14 — Frete CT-e: SUM(valor_brl) FROM cliente_frete_mensal WHERE cnpj AND ano."""
    result = (
        db.query(func.sum(ClienteFretesMensal.valor_brl))
        .filter(
            ClienteFretesMensal.cnpj == cnpj,
            ClienteFretesMensal.ano == ano,
        )
        .scalar()
    )
    return _d(result)


def _busca_verba(cnpj: str, ano: int, db: Session) -> Optional[Decimal]:
    """
    L16 — Verbas: SUM(valor_brl) FROM cliente_verba_anual
    WHERE cnpj AND ano AND tipo='EFETIVADA'.
    Prioriza EFETIVADA (verba real paga) sobre CONTRATO (valor negociado).
    """
    result = (
        db.query(func.sum(ClienteVerbaAnual.valor_brl))
        .filter(
            ClienteVerbaAnual.cnpj == cnpj,
            ClienteVerbaAnual.ano == ano,
            ClienteVerbaAnual.tipo == "EFETIVADA",
        )
        .scalar()
    )
    return _d(result)


def _busca_promotor(cnpj: str, ano: int, db: Session) -> Optional[Decimal]:
    """L17 — Promotor PDV: SUM(valor_brl) FROM cliente_promotor_mensal WHERE cnpj AND ano."""
    result = (
        db.query(func.sum(ClientePromotorMensal.valor_brl))
        .filter(
            ClientePromotorMensal.cnpj == cnpj,
            ClientePromotorMensal.ano == ano,
        )
        .scalar()
    )
    return _d(result)


def _busca_inadimplencia(cnpj: str, db: Session) -> tuple[Optional[Decimal], Optional[float]]:
    """
    L19 — SUM debitos VENCIDOS (provisão inadimplência).
    I8  — Aging médio (DSO) ponderado: SUM(dias_atraso * valor) / SUM(valor).

    Retorna: (valor_inadimplencia, aging_medio_dias)
    """
    rows = (
        db.query(DebitoCliente.valor, DebitoCliente.dias_atraso)
        .filter(
            DebitoCliente.cnpj == cnpj,
            DebitoCliente.status == "VENCIDO",
        )
        .all()
    )
    if not rows:
        return None, None

    total_valor = Decimal("0")
    soma_peso = Decimal("0")
    for row in rows:
        v = _d(row.valor) or Decimal("0")
        d = int(row.dias_atraso) if row.dias_atraso else 0
        total_valor += v
        soma_peso += v * d

    aging = float(soma_peso / total_valor) if total_valor > Decimal("0") else None
    return total_valor, aging


# ---------------------------------------------------------------------------
# Cascata P&L — montagem das linhas
# ---------------------------------------------------------------------------

def _monta_cascata(
    cnpj: str,
    ano: int,
    cliente: Optional[Cliente],
    l1: Optional[Decimal],
    db: Session,
) -> tuple[list[LinhaDRE], dict]:
    """
    Monta as 21 linhas + 9 indicadores da cascata DDE Fase A.
    Retorna (linhas, indicadores_dict).
    """
    linhas: list[LinhaDRE] = []

    # ------------------------------------------------------------------
    # BLOCO 1 — RECEITA BRUTA
    # ------------------------------------------------------------------

    # L1 — Faturamento Bruto
    linhas.append(LinhaDRE(
        codigo="L1",
        conta="FATURAMENTO BRUTO A TABELA",
        sinal="+",
        valor=l1,
        pct_receita=1.0 if l1 else None,
        fonte="SH",
        classificacao="REAL" if l1 is not None else "PENDENTE",
        fase="A",
        observacao="SUM(vendas.valor_pedido) por CNPJ e ano",
    ))

    # L2 — IPI sobre vendas (PENDENTE — ingest não persiste ainda, aguarda D1 completo)
    # Atualizar quando ingest_sales_hunter.py Phase 3 persistir ipi por NF
    linhas.append(LinhaDRE(
        codigo="L2",
        conta="IPI SOBRE VENDAS",
        sinal="+",
        valor=None,
        fonte="SH",
        classificacao="PENDENTE",
        fase="A",
        observacao="Aguardando ingest persistir ipi_total por NF (D1 Phase 3)",
    ))

    # L3 = L1 + L2 (CALC — parcial sem L2)
    l3 = l1  # Fase A: L3 = L1 enquanto L2=NULL
    linhas.append(LinhaDRE(
        codigo="L3",
        conta="= RECEITA BRUTA COM IPI",
        sinal="=",
        valor=l3,
        pct_receita=_pct(l3, l1),
        fonte="CALC",
        classificacao="SINTETICO" if l3 is not None else "PENDENTE",
        fase="A",
        observacao="L1 + L2 (L2=PENDENTE, Fase A usa L3=L1)",
    ))

    # ------------------------------------------------------------------
    # BLOCO 2 — DEDUÇÕES DA RECEITA
    # ------------------------------------------------------------------

    # L4 — Devoluções
    l4_raw = cliente.total_devolucao if cliente else None
    l4 = _d(l4_raw)
    linhas.append(LinhaDRE(
        codigo="L4",
        conta="(-) DEVOLUÇÕES",
        sinal="−",
        valor=l4,
        pct_receita=_pct(l4, l1),
        fonte="SH",
        classificacao="REAL" if l4 is not None else "PENDENTE",
        fase="A",
        observacao="clientes.total_devolucao (SH devolucao_cliente)",
    ))

    # L5 — Desconto comercial (D1: desc_comercial_pct × L1)
    l5: Optional[Decimal] = None
    l5_obs = "Aguardando D1: desc_comercial_pct em clientes"
    l5_class = "PENDENTE"
    if cliente and cliente.desc_comercial_pct is not None and l1 is not None:
        pct = _d(cliente.desc_comercial_pct) or Decimal("0")
        # desc_comercial_pct armazenado como percentual (ex: 5.00 = 5%)
        l5 = (pct / Decimal("100") * l1).quantize(QUANTIZE_CENTS, rounding=ROUND_HALF_UP)
        l5_obs = f"clientes.desc_comercial_pct ({pct}%) × L1"
        l5_class = "SINTETICO"  # É cálculo pct×L1, não valor bruto por NF
    linhas.append(LinhaDRE(
        codigo="L5",
        conta="(-) DESCONTO COMERCIAL",
        sinal="−",
        valor=l5,
        pct_receita=_pct(l5, l1),
        fonte="SH",
        classificacao=l5_class,
        fase="A",
        observacao=l5_obs,
    ))

    # L6 — Desconto financeiro (D1: desc_financeiro_pct × L1)
    l6: Optional[Decimal] = None
    l6_obs = "Aguardando D1: desc_financeiro_pct em clientes"
    l6_class = "PENDENTE"
    if cliente and cliente.desc_financeiro_pct is not None and l1 is not None:
        pct = _d(cliente.desc_financeiro_pct) or Decimal("0")
        l6 = (pct / Decimal("100") * l1).quantize(QUANTIZE_CENTS, rounding=ROUND_HALF_UP)
        l6_obs = f"clientes.desc_financeiro_pct ({pct}%) × L1"
        l6_class = "SINTETICO"
    linhas.append(LinhaDRE(
        codigo="L6",
        conta="(-) DESCONTO FINANCEIRO",
        sinal="−",
        valor=l6,
        pct_receita=_pct(l6, l1),
        fonte="SH",
        classificacao=l6_class,
        fase="A",
        observacao=l6_obs,
    ))

    # L7 — Bonificações (D1: total_bonificacao direto)
    l7_raw = cliente.total_bonificacao if cliente else None
    l7 = _d(l7_raw)
    l7_class = "REAL" if l7 is not None else "PENDENTE"
    l7_obs = "clientes.total_bonificacao (SH fat_cliente)" if l7 is not None else "Aguardando D1: total_bonificacao"
    linhas.append(LinhaDRE(
        codigo="L7",
        conta="(-) BONIFICAÇÕES",
        sinal="−",
        valor=l7,
        pct_receita=_pct(l7, l1),
        fonte="SH",
        classificacao=l7_class,
        fase="A",
        observacao=l7_obs,
    ))

    # L8 — IPI faturado (D1: ipi_total direto)
    l8_raw = cliente.ipi_total if cliente else None
    l8 = _d(l8_raw)
    l8_class = "REAL" if l8 is not None else "PENDENTE"
    l8_obs = "clientes.ipi_total (SH pedidos_produto)" if l8 is not None else "Aguardando D1: ipi_total"
    linhas.append(LinhaDRE(
        codigo="L8",
        conta="(-) IPI FATURADO",
        sinal="−",
        valor=l8,
        pct_receita=_pct(l8, l1),
        fonte="SH",
        classificacao=l8_class,
        fase="A",
        observacao=l8_obs,
    ))

    # L9 — ICMS (NULL Fase B — SAP fiscal)
    linhas.append(LinhaDRE(
        codigo="L9",
        conta="(-) ICMS",
        sinal="−",
        valor=None,
        fonte="SAP",
        classificacao="NULL",
        fase="B",
        observacao="Aguardando SAP fiscal — D3: NULL honesto > sintético (dec. aprovada)",
    ))

    # L10a — PIS (NULL Fase B)
    linhas.append(LinhaDRE(
        codigo="L10a",
        conta="(-) PIS",
        sinal="−",
        valor=None,
        fonte="SAP",
        classificacao="NULL",
        fase="B",
        observacao="Aguardando SAP fiscal (1,65% base COFINS)",
    ))

    # L10b — COFINS (NULL Fase B)
    linhas.append(LinhaDRE(
        codigo="L10b",
        conta="(-) COFINS",
        sinal="−",
        valor=None,
        fonte="SAP",
        classificacao="NULL",
        fase="B",
        observacao="Aguardando SAP fiscal (7,6% base COFINS)",
    ))

    # L10c — ICMS-ST (NULL Fase B)
    linhas.append(LinhaDRE(
        codigo="L10c",
        conta="(-) ICMS-ST",
        sinal="−",
        valor=None,
        fonte="SAP",
        classificacao="NULL",
        fase="B",
        observacao="Aguardando SAP fiscal (alíquota ST por UF)",
    ))

    # L11 — Receita Líquida Comercial (CALC Fase A — parcial sem impostos)
    # L11_comercial = L3 − L4 − L5 − L6 − L7 − L8  (L9-L10c são NULL)
    # Se qualquer componente for None: L11 fica SINTETICO com observacao
    componentes_l11 = [l3, l4, l5, l6, l7, l8]
    nomes_pendentes = [
        ("L2/L3", l3),
        ("L4", l4),
        ("L5", l5),
        ("L6", l6),
        ("L7", l7),
        ("L8", l8),
    ]
    pendentes_l11 = [n for n, v in nomes_pendentes if v is None]

    if l3 is not None:
        # Calcula com os que temos, substituindo None por 0
        def _safe(v: Optional[Decimal]) -> Decimal:
            return v if v is not None else Decimal("0")

        l11 = (
            _safe(l3)
            - _safe(l4)
            - _safe(l5)
            - _safe(l6)
            - _safe(l7)
            - _safe(l8)
        ).quantize(QUANTIZE_CENTS, rounding=ROUND_HALF_UP)
        l11_class = "SINTETICO"  # parcial sem impostos
        if pendentes_l11:
            l11_obs = f"Fase A: L3−L4−L5−L6−L7−L8 (sem impostos SAP). PENDENTES={pendentes_l11}"
        else:
            l11_obs = "Fase A: L3−L4−L5−L6−L7−L8 (Receita Líquida Comercial, sem impostos)"
    else:
        l11 = None
        l11_class = "PENDENTE"
        l11_obs = "PENDENTE — L1 não disponível"

    linhas.append(LinhaDRE(
        codigo="L11",
        conta="= RECEITA LÍQUIDA",
        sinal="=",
        valor=l11,
        pct_receita=_pct(l11, l1),
        fonte="CALC",
        classificacao=l11_class,
        fase="A",
        observacao=l11_obs,
    ))

    # ------------------------------------------------------------------
    # BLOCO 3 — CMV (NULL Fase B — aguarda D6 ou SAP custos)
    # ------------------------------------------------------------------

    linhas.append(LinhaDRE(
        codigo="L12",
        conta="(-) CMV",
        sinal="−",
        valor=None,
        fonte="SAP",
        classificacao="PENDENTE",
        fase="B",
        observacao="D6 URGENTE: RelatorioDeMargemPorProduto — desbloqueia CMV. Sem isso sem Margem Bruta.",
    ))

    linhas.append(LinhaDRE(
        codigo="L13",
        conta="= MARGEM BRUTA",
        sinal="=",
        valor=None,
        fonte="CALC",
        classificacao="PENDENTE",
        fase="B",
        observacao="L11 − L12 — aguarda L12 (CMV). Sem L13 não há Margem Bruta real.",
    ))

    # ------------------------------------------------------------------
    # BLOCO 4 — DESPESAS VARIÁVEIS DO CLIENTE (Custo de Servir)
    # ------------------------------------------------------------------

    # L14 — Frete CT-e
    l14 = _busca_frete(cnpj, ano, db)
    l14_class = "REAL" if l14 is not None else "PENDENTE"
    l14_obs = f"SUM(cliente_frete_mensal.valor_brl) cnpj={cnpj} ano={ano}" if l14 is not None else "PENDENTE — parser_frete.py deve popular cliente_frete_mensal"
    linhas.append(LinhaDRE(
        codigo="L14",
        conta="(-) FRETE CT-e",
        sinal="−",
        valor=l14,
        pct_receita=_pct(l14, l1),
        fonte="LOG",
        classificacao=l14_class,
        fase="A",
        observacao=l14_obs,
    ))

    # L15 — Comissão sobre venda (SINTETICO — L11_comercial × 3% default)
    # D5 aberto: confirmar se comissao_pct = vendedor (L15) ou rebate (L18)
    # Enquanto D5 não decidido: L15 = SINTETICO com % padrão
    l15: Optional[Decimal] = None
    l15_class = "PENDENTE"
    l15_obs = "PENDENTE — base para comissão (L11) não disponível"
    if l11 is not None:
        base_comissao = l11  # comissão sobre receita líquida comercial
        l15 = (base_comissao * Decimal(str(COMISSAO_DEFAULT_PCT))).quantize(
            QUANTIZE_CENTS, rounding=ROUND_HALF_UP
        )
        l15_class = "SINTETICO"
        l15_obs = (
            f"L11 × {COMISSAO_DEFAULT_PCT*100:.1f}% padrão (D5 ABERTO: confirmar se "
            "comissao_pct=vendedor ou rebate — afeta L15 vs L18)"
        )
    linhas.append(LinhaDRE(
        codigo="L15",
        conta="(-) COMISSÃO SOBRE VENDA",
        sinal="−",
        valor=l15,
        pct_receita=_pct(l15, l1),
        fonte="SH",
        classificacao=l15_class,
        fase="A",
        observacao=l15_obs,
    ))

    # L16 — Verbas (contratos efetivados)
    l16 = _busca_verba(cnpj, ano, db)
    l16_class = "REAL" if l16 is not None else "PENDENTE"
    l16_obs = f"SUM(cliente_verba_anual.valor_brl WHERE tipo=EFETIVADA) ano={ano}" if l16 is not None else "PENDENTE — parser_verbas.py/parser_contratos.py deve popular cliente_verba_anual"
    linhas.append(LinhaDRE(
        codigo="L16",
        conta="(-) VERBAS (CONTRATOS)",
        sinal="−",
        valor=l16,
        pct_receita=_pct(l16, l1),
        fonte="LOG",
        classificacao=l16_class,
        fase="A",
        observacao=l16_obs,
    ))

    # L17 — Promotor PDV
    l17 = _busca_promotor(cnpj, ano, db)
    l17_class = "REAL" if l17 is not None else "PENDENTE"
    l17_obs = f"SUM(cliente_promotor_mensal.valor_brl) ano={ano}" if l17 is not None else "PENDENTE — parser_promotores.py deve popular cliente_promotor_mensal"
    linhas.append(LinhaDRE(
        codigo="L17",
        conta="(-) PROMOTOR PDV",
        sinal="−",
        valor=l17,
        pct_receita=_pct(l17, l1),
        fonte="LOG",
        classificacao=l17_class,
        fase="A",
        observacao=l17_obs,
    ))

    # L18 — Bonificação financeira (rebate) — D5 ABERTO
    linhas.append(LinhaDRE(
        codigo="L18",
        conta="(-) BONIFICAÇÃO FINANCEIRA (REBATE)",
        sinal="−",
        valor=None,
        fonte="SH",
        classificacao="PENDENTE",
        fase="A",
        observacao="D5 ABERTO: produtos.comissao_pct = vendedor (→L15) ou rebate (→L18)? Confirmar com SAP.",
    ))

    # L19 — Custo de inadimplência (provisão débitos vencidos)
    l19, aging_medio = _busca_inadimplencia(cnpj, db)
    l19_class = "REAL" if l19 is not None else "REAL"  # REAL mesmo quando zero (nenhum vencido)
    if l19 is None:
        l19 = Decimal("0")
        l19_class = "REAL"
        l19_obs = "SEM débitos vencidos em debitos_clientes (status=VENCIDO)"
    else:
        l19_obs = f"SUM(debitos_clientes.valor WHERE status=VENCIDO) — aging médio: {aging_medio:.0f}d" if aging_medio else "SUM débitos vencidos"
    linhas.append(LinhaDRE(
        codigo="L19",
        conta="(-) CUSTO DE INADIMPLÊNCIA",
        sinal="−",
        valor=l19,
        pct_receita=_pct(l19, l1),
        fonte="DB",
        classificacao=l19_class,
        fase="A",
        observacao=l19_obs,
    ))

    # L20 — Custo financeiro (capital de giro = aging × CDI × valor_em_aberto)
    # SINTETICO porque CDI é fixo (13% a.a.)
    l20: Optional[Decimal] = None
    l20_class = "SINTETICO"
    l20_obs = "aging_medio × CDI(13%a.a.) × l19 / 365"
    if aging_medio is not None and l19 is not None and l19 > Decimal("0"):
        custo_diario = Decimal(str(CDI_ANUAL)) / Decimal("365")
        l20 = (l19 * custo_diario * Decimal(str(aging_medio))).quantize(
            QUANTIZE_CENTS, rounding=ROUND_HALF_UP
        )
        l20_obs = f"CDI={CDI_ANUAL*100:.0f}%a.a. × aging={aging_medio:.0f}d × inadimplência={l19}"
    elif l19 == Decimal("0"):
        l20 = Decimal("0")
        l20_obs = "Zero débitos vencidos → custo financeiro zero"
    linhas.append(LinhaDRE(
        codigo="L20",
        conta="(-) CUSTO FINANCEIRO (CAPITAL GIRO)",
        sinal="−",
        valor=l20,
        pct_receita=_pct(l20, l1),
        fonte="CALC",
        classificacao=l20_class,
        fase="A",
        observacao=l20_obs,
    ))

    # L21 — Margem de Contribuição (CALC parcial sem L13)
    # L21_comercial = L11 − L14 − L15 − L16 − L17 − L18 − L19 − L20
    # L18=None → trata como 0 (PENDENTE declarado)
    if l11 is not None:
        def _s(v: Optional[Decimal]) -> Decimal:
            return v if v is not None else Decimal("0")

        l21 = (
            _s(l11)
            - _s(l14)
            - _s(l15)
            - _s(l16)
            - _s(l17)
            - Decimal("0")  # L18 = PENDENTE/None → 0 conservador
            - _s(l19)
            - _s(l20)
        ).quantize(QUANTIZE_CENTS, rounding=ROUND_HALF_UP)

        pendentes_l21 = [
            n for n, v in [("L14", l14), ("L15", l15), ("L16", l16), ("L17", l17)]
            if v is None
        ]
        l21_class = "SINTETICO"
        l21_obs = "Fase A: L11−L14−L15−L16−L17−L19−L20 (sem L13 CMV, L18 rebate PENDENTE)"
        if pendentes_l21:
            l21_obs += f" — PENDENTES={pendentes_l21} tratados como 0"
    else:
        l21 = None
        l21_class = "PENDENTE"
        l21_obs = "PENDENTE — L11 não disponível"

    linhas.append(LinhaDRE(
        codigo="L21",
        conta="= MARGEM DE CONTRIBUIÇÃO",
        sinal="=",
        valor=l21,
        pct_receita=_pct(l21, l1),
        fonte="CALC",
        classificacao=l21_class,
        fase="A",
        observacao=l21_obs,
    ))

    # ------------------------------------------------------------------
    # BLOCO 6 — INDICADORES DERIVADOS I1..I9
    # ------------------------------------------------------------------

    indicadores: dict = {}

    # I1 — Margem Bruta % = L13/L11 (PENDENTE Fase B)
    indicadores["I1"] = None  # aguarda L13 (CMV)

    # I2 — Margem Contribuição % = L21/L11
    indicadores["I2"] = _pct(l21, l11)

    # I3 — Comissão % = L15/L1
    indicadores["I3"] = _pct(l15, l1)

    # I4 — Frete % = L14/L1
    indicadores["I4"] = _pct(l14, l1)

    # I5 — Verba % = L16/L1
    indicadores["I5"] = _pct(l16, l1)

    # I6 — Inadimplência % = L19/L1
    indicadores["I6"] = _pct(l19, l1) if l1 else None

    # I7 — Devolução % = L4/L1
    indicadores["I7"] = _pct(l4, l1)

    # I8 — DSO/Aging médio (dias médio ponderado dos débitos vencidos)
    indicadores["I8"] = aging_medio

    # I9 — Score Saúde Financeira (0-100, composto ponderado)
    # Ponderação: MC%(30%) + Inadimp%(25%) + Aging(20%) + Frete%(10%) + Devolucao%(10%) + Verba%(5%)
    # Cada indicador normalizado 0-100 contra benchmarks do setor
    indicadores["I9"] = _calcula_score_i9(indicadores)

    return linhas, indicadores


def _calcula_score_i9(indicadores: dict) -> Optional[float]:
    """
    Score I9 (0-100) — saúde financeira composta.

    Ponderação:
      I2 (MC%):         30% — principal driver de rentabilidade
      I6 (Inadimp%):    25% — penalidade: maior inadimplência = menor score
      I8 (Aging dias):  20% — penalidade: mais dias em atraso = menor score
      I4 (Frete%):      10% — informativo: frete alto reduz margem
      I7 (Devol%):      10% — penalidade: devolução alta = problemas
      I5 (Verba%):       5% — informativo

    Benchmarks de normalização (setor alimentos B2B):
      MC%:   0% = 0 pts, 15% = 100 pts, >15% = 100 pts (cap)
      Inadimp%: 0% = 100 pts, 10% = 0 pts (linear inverso)
      Aging:  0d = 100 pts, 90d+ = 0 pts (linear inverso, cap 90d)
      Frete%: 0% = 100 pts, 10% = 0 pts (linear inverso, cap 10%)
      Devol%: 0% = 100 pts, 15% = 0 pts (linear inverso, cap 15%)
      Verba%: 0% = 100 pts, 10% = 0 pts (linear inverso, cap 10%)
    """
    # Requer I2 para calcular — sem MC% não há score
    i2 = indicadores.get("I2")
    if i2 is None:
        return None

    def _normaliza_positivo(val: Optional[float], bench_max: float) -> float:
        """Normaliza indicador positivo: 0..bench_max -> 0..100."""
        if val is None:
            return 50.0  # neutro quando sem dado
        return min(100.0, max(0.0, (val / bench_max) * 100.0))

    def _normaliza_inverso(val: Optional[float], bench_max: float) -> float:
        """Normaliza indicador negativo (maior = pior): 0 -> 100, bench_max -> 0."""
        if val is None:
            return 50.0  # neutro quando sem dado
        return max(0.0, min(100.0, (1.0 - val / bench_max) * 100.0))

    # Normaliza cada indicador
    pts_i2 = _normaliza_positivo(i2, 0.15)      # MC% 0-15% -> 0-100
    pts_i6 = _normaliza_inverso(                 # Inadimp% 0-10% -> 100-0
        indicadores.get("I6"), 0.10
    )
    pts_i8 = _normaliza_inverso(                 # Aging 0-90d -> 100-0
        indicadores.get("I8"), 90.0
    )
    pts_i4 = _normaliza_inverso(                 # Frete% 0-10% -> 100-0
        indicadores.get("I4"), 0.10
    )
    pts_i7 = _normaliza_inverso(                 # Devol% 0-15% -> 100-0
        indicadores.get("I7"), 0.15
    )
    pts_i5 = _normaliza_inverso(                 # Verba% 0-10% -> 100-0
        indicadores.get("I5"), 0.10
    )

    score = (
        pts_i2 * 0.30
        + pts_i6 * 0.25
        + pts_i8 * 0.20
        + pts_i4 * 0.10
        + pts_i7 * 0.10
        + pts_i5 * 0.05
    )

    return round(score, 1)


# ---------------------------------------------------------------------------
# Cache — persiste em cliente_dre_periodo
# ---------------------------------------------------------------------------

def _salva_cache(cnpj: str, ano: int, linhas: list[LinhaDRE], indicadores: dict, db: Session) -> None:
    """
    Persiste linhas da cascata em cliente_dre_periodo (cache).
    Usa upsert: se linha já existe (cnpj, ano, mes=NULL, linha), atualiza.
    mes=NULL indica consolidado anual.
    """
    for linha in linhas:
        # Upsert via merge — SQLAlchemy não tem merge nativo, então delete+insert
        existing = (
            db.query(ClienteDrePeriodo)
            .filter(
                ClienteDrePeriodo.cnpj == cnpj,
                ClienteDrePeriodo.ano == ano,
                ClienteDrePeriodo.mes.is_(None),
                ClienteDrePeriodo.linha == linha.codigo,
            )
            .first()
        )
        valor_float = float(linha.valor) if linha.valor is not None else None
        pct_float = linha.pct_receita

        if existing:
            existing.conta = linha.conta
            existing.valor_brl = valor_float
            existing.pct_sobre_receita = pct_float
            existing.fonte = linha.fonte
            existing.classificacao = linha.classificacao
            existing.fase = linha.fase
            existing.observacao = linha.observacao
            existing.calculado_em = func.now()
        else:
            db.add(ClienteDrePeriodo(
                cnpj=cnpj,
                ano=ano,
                mes=None,
                linha=linha.codigo,
                conta=linha.conta,
                valor_brl=valor_float,
                pct_sobre_receita=pct_float,
                fonte=linha.fonte,
                classificacao=linha.classificacao,
                fase=linha.fase,
                observacao=linha.observacao,
            ))

    # Persistir indicadores como linhas do tipo I1..I9
    for codigo, valor in indicadores.items():
        conta_map = {
            "I1": "MARGEM BRUTA %",
            "I2": "MARGEM CONTRIBUIÇÃO %",
            "I3": "COMISSÃO %",
            "I4": "FRETE %",
            "I5": "VERBA %",
            "I6": "INADIMPLÊNCIA %",
            "I7": "DEVOLUÇÃO %",
            "I8": "AGING MÉDIO (DIAS)",
            "I9": "SCORE SAÚDE FINANCEIRA",
        }
        conta = conta_map.get(codigo, codigo)
        valor_num = float(valor) if valor is not None else None
        class_ = "SINTETICO" if valor is not None else "PENDENTE"
        fase_ = "B" if codigo == "I1" else "A"

        existing = (
            db.query(ClienteDrePeriodo)
            .filter(
                ClienteDrePeriodo.cnpj == cnpj,
                ClienteDrePeriodo.ano == ano,
                ClienteDrePeriodo.mes.is_(None),
                ClienteDrePeriodo.linha == codigo,
            )
            .first()
        )
        if existing:
            existing.conta = conta
            existing.valor_brl = valor_num
            existing.classificacao = class_
            existing.fase = fase_
        else:
            db.add(ClienteDrePeriodo(
                cnpj=cnpj,
                ano=ano,
                mes=None,
                linha=codigo,
                conta=conta,
                valor_brl=valor_num,
                classificacao=class_,
                fase=fase_,
                observacao="Indicador calculado pelo dde_engine.py",
            ))

    db.commit()


# ---------------------------------------------------------------------------
# Função principal pública
# ---------------------------------------------------------------------------

def calcula_dre_comercial(cnpj: str, ano: int, db: Session) -> ResultadoDDE:
    """
    Fase A — DDE Comercial (sem CMV, sem impostos detalhados).

    Calcula a cascata P&L L1..L21 + indicadores I1..I9 + veredito determinístico.
    Linhas sem dado real retornam valor=None, classificacao='PENDENTE'/'NULL'.
    Persiste resultado em cliente_dre_periodo (cache) para acesso rápido.

    Args:
        cnpj: CNPJ do cliente (14 dígitos, qualquer formato — normalizado internamente)
        ano: Ano de referência (ex.: 2025)
        db: Sessão SQLAlchemy ativa

    Returns:
        ResultadoDDE com linhas, indicadores, veredito e fase_ativa='A'
    """
    from backend.app.services.dde_veredito import veredito as calcula_veredito

    # R5: normalizar CNPJ
    cnpj = normaliza_cnpj(cnpj)

    # Buscar dados base
    cliente = _busca_cliente(cnpj, db)
    l1 = _busca_l1(cnpj, ano, db)

    # Montar cascata
    linhas, indicadores = _monta_cascata(cnpj, ano, cliente, l1, db)

    # Montar resultado parcial para calcular veredito
    resultado = ResultadoDDE(
        cnpj=cnpj,
        ano=ano,
        linhas=linhas,
        indicadores=indicadores,
        fase_ativa="A",
    )

    # Calcular veredito
    resultado.veredito, resultado.veredito_descricao = calcula_veredito(resultado)

    # Persistir cache
    _salva_cache(cnpj, ano, linhas, indicadores, db)

    return resultado
