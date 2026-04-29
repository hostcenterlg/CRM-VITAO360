"""
CRM VITAO360 — Model VendaItem

Linha de item de uma venda (pedido). Cada Venda pode ter 1-N VendaItems,
cada um referenciando um Produto do catálogo.

R4 — TWO-BASE ARCHITECTURE (SAGRADA):
  VendaItem é parte da metade VENDA do Two-Base.
  valor_total aqui representa R$ real de transação — correto e esperado.
  NUNCA criar VendaItems sem uma Venda pai válida (venda_id obrigatório).
  NUNCA associar VendaItem a um LogInteracao (seria violação de Two-Base).

R8 — Zero fabricação: itens devem vir de importação Mercos/SAP,
     nunca de estimativas ou placeholders.
"""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class VendaItem(Base):
    """
    Item individual de uma venda (linha do pedido).

    valor_total = quantidade * preco_unitario * (1 - desconto_pct / 100)
    Este cálculo deve ser feito na camada de aplicação antes de persistir,
    garantindo consistência entre os campos.

    R4: valor_total DEVE ser > 0 (CheckConstraint enforça no banco).
    Chave técnica: id (autoincrement).
    """

    __tablename__ = "venda_itens"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # FK para a Venda (pedido) pai — CASCADE: deletar a venda deleta os itens
    venda_id = Column(
        Integer,
        ForeignKey("vendas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FK para o Produto do catálogo
    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Dados do item
    # ------------------------------------------------------------------
    # Quantidade vendida (float para suportar frações: ex.: 1.5 KG)
    quantidade = Column(Float, nullable=False)

    # Preço unitário negociado no momento da venda (não necessariamente = preco_tabela)
    preco_unitario = Column(Float, nullable=False)

    # Percentual de desconto (ex.: 5.0 = 5%). Zero se sem desconto.
    desconto_pct = Column(Float, nullable=False, default=0.0)

    # Valor total do item: quantidade * preco_unitario * (1 - desconto_pct / 100)
    # Calculado e persistido na camada de aplicação para evitar drift.
    valor_total = Column(Float, nullable=False)

    # ------------------------------------------------------------------
    # Relacionamentos ORM
    # ------------------------------------------------------------------
    # Venda pai — permite navegar item → pedido
    venda = relationship("Venda", back_populates="itens")

    # Produto referenciado — permite navegar item → produto.nome, produto.categoria, etc.
    produto = relationship("Produto", back_populates="itens_venda")

    # ------------------------------------------------------------------
    # Constraints e índices
    # ------------------------------------------------------------------
    __table_args__ = (
        # R4: valor_total de item NUNCA pode ser zero ou negativo
        CheckConstraint("valor_total > 0", name="ck_venda_item_valor_positivo"),
        # Índice composto para consultas de itens por venda
        Index("ix_venda_itens_venda_produto", "venda_id", "produto_id"),
        # Constraint de unicidade: um produto aparece no máximo 1x por venda
        # Adicionado via migration 4ac6e4064fa0 (dedup + constraint 2026-04-29)
        UniqueConstraint("venda_id", "produto_id", name="uq_venda_itens_venda_produto"),
    )

    def __repr__(self) -> str:
        return (
            f"<VendaItem id={self.id} venda_id={self.venda_id} "
            f"produto_id={self.produto_id} qty={self.quantidade} "
            f"total=R${self.valor_total:.2f}>"
        )
