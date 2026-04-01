"""
CRM VITAO360 — Schemas Pydantic para Produtos e PrecoRegional.

R8 — Zero fabricação: campos obrigatórios refletem os campos do model ORM.
     Nenhum campo permite valores placeholder ou dummy.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# PrecoRegional (aninhado em ProdutoResponse)
# ---------------------------------------------------------------------------

class PrecoRegionalResponse(BaseModel):
    """Preço regional de um produto para uma UF, usado dentro de ProdutoResponse."""

    id: int
    uf: str = Field(description="Código da UF (ex.: 'SC', 'PR', 'SP')")
    preco: float = Field(description="Preço regional em R$")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Produto — schemas de entrada e saída
# ---------------------------------------------------------------------------

class ProdutoCreate(BaseModel):
    """
    Dados para cadastrar um produto no catálogo.

    Apenas admin pode criar produtos. O campo codigo é a chave de negócio
    (código SAP ou Mercos) e não pode ser duplicado.
    """

    codigo: str = Field(
        ...,
        max_length=50,
        description="Código SAP/Mercos do produto (identificador único de negócio)",
        examples=["GRAO-001"],
    )
    nome: str = Field(
        ...,
        max_length=255,
        description="Nome comercial do produto",
        examples=["Aveia em Flocos Finos 500g"],
    )
    categoria: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Categoria comercial (ex.: 'Cereais', 'Frutas Secas')",
        examples=["Cereais"],
    )
    fabricante: str = Field(
        default="VITAO",
        max_length=100,
        description="Fabricante do produto",
        examples=["VITAO"],
    )
    unidade: str = Field(
        default="UN",
        max_length=10,
        description="Unidade de medida: UN, CX ou KG",
        examples=["UN"],
    )
    preco_tabela: float = Field(
        default=0.0,
        ge=0,
        description="Preço base de tabela em R$",
        examples=[12.50],
    )
    preco_minimo: float = Field(
        default=0.0,
        ge=0,
        description="Preço mínimo permitido (piso de desconto) em R$",
        examples=[10.00],
    )
    comissao_pct: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Percentual de comissão sobre este produto (ex.: 3.5 = 3,5%)",
        examples=[3.5],
    )
    ipi_pct: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Percentual de IPI (ex.: 5.0 = 5%)",
        examples=[0.0],
    )
    peso: Optional[float] = Field(
        default=None,
        gt=0,
        description="Peso em kg (para cálculo de frete)",
        examples=[0.5],
    )
    ean: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Código EAN/barcode do produto",
        examples=["7891234567890"],
    )
    ativo: bool = Field(default=True, description="Se False, produto não aparece em listagens")

    @field_validator("unidade")
    @classmethod
    def unidade_valida(cls, v: str) -> str:
        validas = {"UN", "CX", "KG"}
        v_upper = v.upper()
        if v_upper not in validas:
            raise ValueError(
                f"Unidade invalida: {v!r}. Valores permitidos: {sorted(validas)}"
            )
        return v_upper


class ProdutoUpdate(BaseModel):
    """
    Campos opcionais para atualização parcial de um produto (PATCH).
    Apenas campos informados são atualizados — campos ausentes mantêm o valor atual.
    """

    nome: Optional[str] = Field(default=None, max_length=255)
    categoria: Optional[str] = Field(default=None, max_length=100)
    fabricante: Optional[str] = Field(default=None, max_length=100)
    unidade: Optional[str] = Field(default=None, max_length=10)
    preco_tabela: Optional[float] = Field(default=None, ge=0)
    preco_minimo: Optional[float] = Field(default=None, ge=0)
    comissao_pct: Optional[float] = Field(default=None, ge=0, le=100)
    ipi_pct: Optional[float] = Field(default=None, ge=0, le=100)
    peso: Optional[float] = Field(default=None, gt=0)
    ean: Optional[str] = Field(default=None, max_length=20)
    ativo: Optional[bool] = None

    @field_validator("unidade")
    @classmethod
    def unidade_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        validas = {"UN", "CX", "KG"}
        v_upper = v.upper()
        if v_upper not in validas:
            raise ValueError(
                f"Unidade invalida: {v!r}. Valores permitidos: {sorted(validas)}"
            )
        return v_upper


class ProdutoResponse(BaseModel):
    """
    Resposta de um produto consultado.
    Inclui precos_regionais quando endpoint de detalhe (/produtos/{id}).
    """

    id: int
    codigo: str
    nome: str
    categoria: Optional[str] = None
    fabricante: str
    unidade: str
    preco_tabela: float
    preco_minimo: float
    comissao_pct: float
    ipi_pct: float
    peso: Optional[float] = None
    ean: Optional[str] = None
    ativo: bool
    created_at: datetime
    updated_at: datetime
    precos_regionais: list[PrecoRegionalResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProdutoListResponse(BaseModel):
    """
    Resposta de produto em listagens (sem precos_regionais para performance).
    """

    id: int
    codigo: str
    nome: str
    categoria: Optional[str] = None
    fabricante: str
    unidade: str
    preco_tabela: float
    ativo: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Mais vendidos (agregado)
# ---------------------------------------------------------------------------

class ProdutoMaisVendido(BaseModel):
    """Item do ranking de produtos mais vendidos."""

    produto_id: int
    codigo: str
    nome: str
    categoria: Optional[str] = None
    quantidade_total: float = Field(description="Soma de VendaItem.quantidade")
    valor_total: float = Field(description="Soma de VendaItem.valor_total em R$")
    num_pedidos: int = Field(description="Número de pedidos distintos que incluíram este produto")
