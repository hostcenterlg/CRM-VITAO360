"""
CRM VITAO360 — Schemas Pydantic para atendimentos.

Define os contratos de entrada e saida dos endpoints /api/atendimentos:
  - AtendimentoCreate  : corpo do POST /api/atendimentos
  - MotorResultado     : 9 dimensoes calculadas pelo Motor de Regras
  - AtendimentoResponse: resposta do POST com log + resultado do motor
  - AtendimentoListItem: item de lista no GET /api/atendimentos

R4 — Two-Base: AtendimentoCreate nao tem campo de valor monetario.
R5 — CNPJ: String com 14 digitos.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Valores validos para tipo_contato (canal de comunicacao do atendimento)
TIPOS_CONTATO_VALIDOS = {"LIGACAO", "WHATSAPP", "VISITA", "EMAIL", "VIDEOCHAMADA"}


class AtendimentoCreate(BaseModel):
    """
    Dados necessarios para registrar uma interacao com cliente.

    O consultor e preenchido automaticamente a partir do JWT.
    O Motor de Regras e executado automaticamente no backend.

    R4: Nenhum campo de valor monetario aqui — esta e a metade LOG.
    R5: cnpj deve ter exatamente 14 digitos numericos.
    """

    cnpj: str = Field(
        ...,
        min_length=14,
        max_length=14,
        description="CNPJ do cliente — 14 digitos numericos, sem pontuacao",
        examples=["12345678000100"],
    )
    resultado: str = Field(
        ...,
        description=(
            "Resultado da interacao. Valores validos: "
            "VENDA / PEDIDO, ORÇAMENTO, EM ATENDIMENTO, CADASTRO, "
            "RELACIONAMENTO, FOLLOW UP 7, FOLLOW UP 15, SUPORTE, "
            "NÃO ATENDE, NÃO RESPONDE, RECUSOU LIGAÇÃO, PERDA / FECHOU LOJA"
        ),
        examples=["VENDA / PEDIDO"],
    )
    descricao: str = Field(
        default="",
        description="Observacoes livres do consultor sobre a interacao",
        examples=["Cliente fechou pedido de R$ 2.000 em proteinas"],
    )
    tipo_contato: Optional[str] = Field(
        default=None,
        description=(
            "Canal de comunicacao utilizado (opcional — o Motor de Regras calcula "
            "automaticamente se nao informado). Valores validos: "
            "LIGACAO, WHATSAPP, VISITA, EMAIL, VIDEOCHAMADA"
        ),
        examples=["WHATSAPP"],
    )


class MotorResultado(BaseModel):
    """
    As 9 dimensoes calculadas automaticamente pelo Motor de Regras.

    Preenchidas com base na combinacao situacao atual do cliente + resultado informado.
    Campos com emojis (temperatura) sao preservados: 🔥 QUENTE, 🟡 MORNO, ❄️ FRIO, 💀 PERDIDO.
    """

    estagio_funil: str | None = Field(None, description="Estagio no funil de vendas")
    fase: str | None = Field(None, description="Fase comercial atual")
    tipo_contato: str | None = Field(None, description="Tipo de contato realizado")
    acao_futura: str | None = Field(None, description="Proxima acao recomendada")
    temperatura: str | None = Field(None, description="Temperatura do lead (com emoji)")
    follow_up_dias: int | None = Field(None, description="Dias ate proximo follow-up")
    grupo_dash: str | None = Field(None, description="Agrupamento no dashboard")
    tentativa: str | None = Field(None, description="Tentativa atual (T1-T4 ou NUTRIÇÃO)")


class AtendimentoResponse(BaseModel):
    """
    Resposta do POST /api/atendimentos.

    Retorna o log criado + as 9 dimensoes calculadas pelo motor.
    """

    id: int
    cnpj: str
    consultor: str
    resultado: str
    descricao: str | None
    data_interacao: datetime
    motor: MotorResultado

    model_config = {"from_attributes": True}


class AtendimentoListItem(BaseModel):
    """
    Item da lista retornada pelo GET /api/atendimentos.

    Inclui nome_fantasia do cliente para exibicao no frontend sem JOIN adicional.
    """

    id: int
    cnpj: str
    nome_fantasia: str | None = None
    consultor: str
    resultado: str
    descricao: str | None
    data_interacao: datetime
    estagio_funil: str | None
    fase: str | None
    temperatura: str | None
    tentativa: str | None

    model_config = {"from_attributes": True}
