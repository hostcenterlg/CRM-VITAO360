"""
CRM VITAO360 — Pydantic Schemas DDE (Onda 4 — PAPA)

Serializa ResultadoDDE (dataclass do OSCAR) para JSON via FastAPI.
Converte Decimal → float e Optional fields corretamente.

R8 — Zero alucinação: valor=None → null no JSON. Frontend renderiza visualmente.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class LinhaDREResponse(BaseModel):
    """
    Uma linha da cascata DDE P&L (L1..L21) serializada para JSON.

    valor: None quando classificacao in ('PENDENTE', 'NULL') — R8 honesto.
    pct_receita: percentual sobre L1. None se L1 não disponível.
    """

    model_config = ConfigDict(from_attributes=True)

    codigo: str
    conta: str
    sinal: str
    valor: Optional[float] = None      # Decimal → float. None = PENDENTE/NULL (R8)
    pct_receita: Optional[float] = None
    fonte: str
    classificacao: str                  # REAL | SINTETICO | PENDENTE | NULL
    fase: str
    observacao: str


class IndicadoresDDE(BaseModel):
    """
    Indicadores derivados I1..I9 da cascata DDE.

    Todos opcionais — None indica ausência de dado (R8).
    I1: margem bruta % (PENDENTE Fase B — aguarda CMV)
    I2: margem contribuição %
    I3: comissão %
    I4: frete %
    I5: verba %
    I6: inadimplência %
    I7: devolução %
    I8: DSO/aging médio (dias)
    I9: score saúde financeira (0-100)
    """

    I1: Optional[float] = None  # margem bruta % — PENDENTE Fase B
    I2: Optional[float] = None  # margem contribuição %
    I3: Optional[float] = None  # comissão %
    I4: Optional[float] = None  # frete %
    I5: Optional[float] = None  # verba %
    I6: Optional[float] = None  # inadimplência %
    I7: Optional[float] = None  # devolução %
    I8: Optional[float] = None  # DSO/aging médio (dias)
    I9: Optional[float] = None  # score 0-100


class ResultadoDDEResponse(BaseModel):
    """
    Resposta completa da cascata DDE para um cliente/ano.

    Serializa ResultadoDDE (dataclass OSCAR) para o contrato JSON da API.
    """

    cnpj: str
    ano: int
    linhas: list[LinhaDREResponse]
    indicadores: IndicadoresDDE
    veredito: str                    # SAUDAVEL | REVISAR | RENEGOCIAR | SUBSTITUIR | ALERTA_CREDITO | SEM_DADOS
    veredito_descricao: str
    fase_ativa: str                  # 'A' na implementação atual


class DDEComparativoItem(BaseModel):
    """
    Item do comparativo DDE — resumo por CNPJ para listagem.

    Extrai os campos-chave de ResultadoDDE para comparação lado a lado.
    """

    cnpj: str
    razao_social: Optional[str] = None
    receita_bruta: Optional[float] = None    # L1 — Faturamento Bruto
    margem_contribuicao: Optional[float] = None  # L21
    mc_pct: Optional[float] = None           # I2
    score: Optional[float] = None            # I9
    veredito: str


class DDEComparativoResponse(BaseModel):
    """
    Resposta de endpoints de comparativo/consolidado DDE.

    Usado por: /consultor, /canal, /comparativo
    """

    ano: int
    items: list[DDEComparativoItem]


class DDEScoreResponse(BaseModel):
    """
    Resposta do endpoint /score — apenas I9 + breakdown dos 9 indicadores.

    breakdown: dict I1..I9 com valores float ou null.
    """

    cnpj: str
    score: Optional[float]
    breakdown: dict[str, Any]    # I1..I9 com seus valores
    veredito: str
