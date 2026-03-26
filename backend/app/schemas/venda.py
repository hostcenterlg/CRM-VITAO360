"""
CRM VITAO360 — Schemas Pydantic para vendas.

R4 — TWO-BASE ARCHITECTURE (SAGRADA):
  Esta e a metade VENDA do Two-Base. Todos os registros DEVEM ter valor_pedido > 0.
  A metade LOG (log_interacoes, atendimentos) NUNCA carrega valor monetario.
  Misturar as duas metades causou inflacao de 742% em sessao anterior.

R5 — CNPJ: String com 14 digitos, zero-padded, NUNCA float.
R8 — classificacao_3tier: REAL / SINTETICO / ALUCINACAO.
     Dados ALUCINACAO NUNCA entram em producao (558 registros catalogados).

Fontes validas: MERCOS, SAP, MANUAL.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class VendaCreate(BaseModel):
    """
    Dados necessarios para registrar uma venda.

    R4: valor_pedido > 0 e obrigatorio. Pydantic rejeita imediatamente valores <= 0.
    R5: cnpj deve ter exatamente 14 digitos numericos, sem pontuacao.
    R8: classificacao_3tier padrao = REAL. NUNCA informar ALUCINACAO.

    O motor NAO e executado em vendas — este registro e puramente financeiro.
    """

    cnpj: str = Field(
        ...,
        min_length=14,
        max_length=14,
        description="CNPJ do cliente — 14 digitos numericos, sem pontuacao (R5)",
        examples=["12345678000100"],
    )
    data_pedido: date = Field(
        ...,
        description="Data em que o pedido foi realizado (YYYY-MM-DD)",
        examples=["2026-03-01"],
    )
    numero_pedido: str | None = Field(
        default=None,
        max_length=50,
        description="Numero do pedido no sistema de origem (Mercos, SAP). Opcional para entradas MANUAL.",
        examples=["MRC-00123"],
    )
    valor_pedido: float = Field(
        ...,
        gt=0,
        description="Valor do pedido em R$. DEVE ser > 0 — Two-Base Architecture (R4).",
        examples=[2500.00],
    )
    consultor: str | None = Field(
        default=None,
        max_length=50,
        description=(
            "Consultor responsavel pela venda. Se None, usa o consultor do usuario logado. "
            "Valores validos: MANU, LARISSA, DAIANE, JULIO."
        ),
        examples=["MANU"],
    )
    fonte: str = Field(
        default="MANUAL",
        description="Origem do registro. Valores validos: MERCOS, SAP, MANUAL.",
        examples=["MERCOS"],
    )

    @field_validator("cnpj")
    @classmethod
    def cnpj_deve_ser_numerico(cls, v: str) -> str:
        """R5: CNPJ deve conter apenas digitos numericos."""
        if not v.isdigit():
            raise ValueError(
                "CNPJ deve conter apenas digitos numericos (14 caracteres, sem pontuacao). "
                f"Recebido: {v!r}"
            )
        return v

    @field_validator("fonte")
    @classmethod
    def fonte_valida(cls, v: str) -> str:
        fontes_validas = {"MERCOS", "SAP", "MANUAL"}
        v_upper = v.upper()
        if v_upper not in fontes_validas:
            raise ValueError(
                f"Fonte invalida: {v!r}. Valores permitidos: {sorted(fontes_validas)}"
            )
        return v_upper


class VendaResponse(BaseModel):
    """
    Resposta de uma venda registrada ou consultada.

    Inclui nome_fantasia do cliente para exibicao no frontend sem JOIN adicional.
    classificacao_3tier sempre presente — garante rastreabilidade dos dados (R8).
    """

    id: int
    cnpj: str
    nome_fantasia: str | None = None
    data_pedido: date
    numero_pedido: str | None = None
    valor_pedido: float = Field(description="Sempre > 0 (Two-Base, R4)")
    consultor: str
    fonte: str
    classificacao_3tier: str = Field(
        description="REAL | SINTETICO | ALUCINACAO. Nunca deve ser ALUCINACAO em producao (R8)."
    )
    mes_referencia: str | None = Field(
        default=None,
        description='Periodo de referencia no formato "AAAA-MM". Atencao R6: Mercos mente nos nomes.',
    )
    created_at: datetime

    model_config = {"from_attributes": True}


class VendaTotais(BaseModel):
    """
    Agregado de faturamento para o painel gerencial (somente admin).

    Baseline de referencia: R$ 2.091.000 (CORRIGIDO 2026-03-23, R7).
    Apenas registros REAL e SINTETICO entram no calculo — ALUCINACAO e excluido (R8).
    """

    faturamento_total: float = Field(
        description=(
            "Soma de valor_pedido de todos os registros REAL + SINTETICO. "
            "Baseline: R$ 2.091.000. Divergencia > 0.5% = investigar (R7)."
        )
    )
    total_vendas: int = Field(description="Quantidade de registros de venda incluidos no calculo.")
    ticket_medio: float = Field(description="faturamento_total / total_vendas. Zero se sem vendas.")
    por_consultor: list[dict] = Field(
        description="Lista de {consultor, faturamento, qtd} ordenada por faturamento desc."
    )
    por_mes: list[dict] = Field(
        description="Lista de {mes, faturamento, qtd} ordenada por mes desc (formato AAAA-MM)."
    )
