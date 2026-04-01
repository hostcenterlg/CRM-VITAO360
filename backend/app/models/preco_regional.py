"""
CRM VITAO360 — Model PrecoRegional

Preço específico de um produto por UF (estado brasileiro).

Quando existe um PrecoRegional para produto+UF, ele sobrepõe o preco_tabela
padrão do Produto nas consultas de preço para aquela região.

R8 — Zero fabricação: preços regionais devem vir de tabelas SAP/Mercos,
     nunca de estimativas ou placeholders.
"""

from __future__ import annotations

from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.app.database import Base


class PrecoRegional(Base):
    """
    Preço regional de um produto para uma UF específica.

    Constraint UNIQUE(produto_id, uf) garante que cada produto tem no máximo
    um preço por estado — evita duplicatas silenciosas em importações.

    Chave técnica: id (autoincrement).
    """

    __tablename__ = "precos_regionais"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # FK para o produto ao qual este preço pertence
    produto_id = Column(
        Integer,
        ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Região e preço
    # ------------------------------------------------------------------
    # Código de 2 letras da UF brasileira (ex.: "SC", "PR", "SP")
    uf = Column(String(2), nullable=False)

    # Preço regional em R$ — sobrepõe preco_tabela do Produto para esta UF
    preco = Column(Float, nullable=False)

    # ------------------------------------------------------------------
    # Relacionamentos ORM
    # ------------------------------------------------------------------
    produto = relationship("Produto", back_populates="precos_regionais")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        # Unicidade produto+UF: um preço regional por estado por produto
        UniqueConstraint("produto_id", "uf", name="uq_produto_uf"),
    )

    def __repr__(self) -> str:
        return (
            f"<PrecoRegional id={self.id} produto_id={self.produto_id} "
            f"uf={self.uf!r} preco=R${self.preco:.2f}>"
        )
