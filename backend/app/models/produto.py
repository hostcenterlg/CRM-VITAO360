"""
CRM VITAO360 — Model Produto

Catálogo de produtos VITAO Alimentos para associação com itens de venda (VendaItem).

R1 — Two-Base: este model NÃO armazena valores de transação. O valor monetário
     das vendas fica em VendaItem.valor_total (metade VENDA). Produto armazena
     apenas preços de tabela/referência (não transacionais).
R8 — Zero fabricação: produtos DEVEM ser importados de SAP/Mercos, nunca inventados.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Produto(Base):
    """
    Produto do catálogo VITAO Alimentos.

    Fonte canônica: SAP (código interno) ou Mercos (importação de itens de pedido).
    Chave de negócio: codigo (código SAP/Mercos, ex.: "GRAO-001", "FRU-042").
    Chave técnica:    id (autoincrement).
    """

    __tablename__ = "produtos"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Código SAP/Mercos — identificador canônico do produto no ERP
    codigo = Column(String(50), unique=True, index=True, nullable=False)

    # ------------------------------------------------------------------
    # Identificação
    # ------------------------------------------------------------------
    nome = Column(String(255), nullable=False)

    # Categoria comercial (ex.: "Cereais", "Frutas Secas", "Proteínas")
    categoria = Column(String(100), index=True, nullable=True)

    # Fabricante — default VITAO para produtos próprios
    fabricante = Column(String(100), nullable=False, default="VITAO")

    # Unidade de medida: UN (unidade), CX (caixa), KG (quilograma)
    unidade = Column(String(10), nullable=False, default="UN")

    # ------------------------------------------------------------------
    # Precificação (valores de tabela/referência — não transacionais)
    # ------------------------------------------------------------------
    # Preço base de tabela comercial
    preco_tabela = Column(Float, nullable=False, default=0.0)

    # Preço mínimo permitido (piso de desconto — aplicado nas regras do motor)
    preco_minimo = Column(Float, nullable=False, default=0.0)

    # ------------------------------------------------------------------
    # Parâmetros fiscais e comerciais
    # ------------------------------------------------------------------
    # Percentual de comissão sobre este produto (ex.: 3.5 = 3,5%)
    comissao_pct = Column(Float, nullable=False, default=0.0)

    # Percentual de IPI — imposto sobre produtos industrializados
    ipi_pct = Column(Float, nullable=False, default=0.0)

    # Peso em kg (usado para cálculo de fretes)
    peso = Column(Float, nullable=True)

    # EAN/barcode do produto
    ean = Column(String(20), nullable=True)

    # ------------------------------------------------------------------
    # Sales Hunter SAP enrichment (Phase 1 — GAP 2C)
    # Alimentado por fat_produto_*.xlsx e fat_nf_det_*.xlsx
    # ------------------------------------------------------------------
    # Subcategoria SAP (ex.: "AÇÚCAR", "AVEIA", "BISCOITO")
    subcategoria = Column(String(100), nullable=True)
    # SAP UM/embalagem comercial (ex.: "Caixa", "Fardo", "Unidade")
    unidade_embalagem = Column(String(20), nullable=True)
    # Quantidade por embalagem (ex.: 12 frascos por caixa)
    qtd_por_embalagem = Column(Integer, nullable=True)
    # Peso bruto kg da unidade comercial
    peso_bruto_kg = Column(Float, nullable=True)
    # Codigo NCM (Nomenclatura Comum do Mercosul, 8 digitos)
    codigo_ncm = Column(String(10), nullable=True)
    # Faturamento total acumulado R$ (Sales Hunter)
    fat_total_historico = Column(Float, default=0)
    # Curva ABC do produto: 'A' | 'B' | 'C'
    # Calculada por fat_total_historico decrescente:
    #   top 20% acumulado de faturamento -> A
    #   proximos 30% -> B
    #   resto -> C
    curva_abc_produto = Column(String(1), nullable=True)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    ativo = Column(Boolean, nullable=False, default=True)

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Relacionamentos ORM
    # ------------------------------------------------------------------
    # Itens de venda que referenciam este produto
    itens_venda = relationship("VendaItem", back_populates="produto")

    # Tabela de preços regionais (por UF)
    precos_regionais = relationship(
        "PrecoRegional",
        back_populates="produto",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Produto id={self.id} codigo={self.codigo!r} "
            f"nome={self.nome!r} ativo={self.ativo}>"
        )
