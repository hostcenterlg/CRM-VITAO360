"""
CRM VITAO360 — Model Venda

R4 — TWO-BASE ARCHITECTURE (SAGRADA):
  Esta tabela representa APENAS registros tipo VENDA.
  valor_pedido DEVE ser > 0. NUNCA registrar LOG aqui.
  Misturar VENDA + LOG causa inflação de 742% (já aconteceu).

R5 — CNPJ: String(14), zero-padded, NUNCA Float.

R8 — classificacao_3tier: REAL / SINTETICO / ALUCINACAO.
     Dados do ChatGPT = ALUCINACAO por padrão — NUNCA integrar sem auditoria.

Fontes válidas: MERCOS, SAP, MANUAL.
"""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Venda(Base):
    """
    Registro de pedido/venda realizada por um cliente.

    R4: valor_pedido SEMPRE > 0. CheckConstraint enforça no banco.
    R5: cnpj = String(14), nunca float.
    R8: classificacao_3tier obrigatória.

    Chave de negócio: numero_pedido (quando disponível, ex.: Mercos/SAP).
    Chave técnica:    id (autoincrement).
    """

    __tablename__ = "vendas"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuação
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Dados do pedido
    # ------------------------------------------------------------------
    data_pedido = Column(Date, nullable=False, index=True)
    numero_pedido = Column(String(50), nullable=True)

    # R4: valor_pedido DEVE ser > 0 — CheckConstraint abaixo enforça isso
    valor_pedido = Column(Float, nullable=False)

    # ------------------------------------------------------------------
    # Origem / Responsável
    # ------------------------------------------------------------------
    consultor = Column(String(50), nullable=False, index=True)  # MANU, LARISSA, DAIANE, JULIO

    # Fonte de importação: MERCOS, SAP ou MANUAL
    fonte = Column(String(20), nullable=False, default="MERCOS")

    # ------------------------------------------------------------------
    # Classificação de qualidade do dado (R8)
    # ------------------------------------------------------------------
    # REAL      = rastreável a Mercos/SAP
    # SINTETICO = derivado por fórmula de dados REAL
    # ALUCINACAO= fabricado — NUNCA deve estar aqui
    classificacao_3tier = Column(String(15), nullable=False, default="REAL")

    # ------------------------------------------------------------------
    # Período de referência (formato "AAAA-MM", ex.: "2026-03")
    # Atenção R6: Mercos MENTE nos nomes de arquivo — sempre verificar
    # Data inicial/Data final nas linhas 6-7 do relatório.
    # ------------------------------------------------------------------
    mes_referencia = Column(String(7), nullable=True)

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now())

    # ------------------------------------------------------------------
    # Relacionamentos ORM
    # ------------------------------------------------------------------
    cliente = relationship(
        "Cliente",
        backref="vendas",
        foreign_keys=[cnpj],
        primaryjoin="Venda.cnpj == Cliente.cnpj",
    )

    # ------------------------------------------------------------------
    # Constraints e índices compostos
    # ------------------------------------------------------------------
    __table_args__ = (
        # R4: Two-Base enforcement — valor NUNCA pode ser <= 0 nesta tabela
        CheckConstraint("valor_pedido > 0", name="ck_venda_valor_positivo"),
        # Índice composto para consultas por cliente + período
        Index("ix_vendas_cnpj_data", "cnpj", "data_pedido"),
    )

    def __repr__(self) -> str:
        return (
            f"<Venda id={self.id} cnpj={self.cnpj!r} "
            f"data={self.data_pedido} valor=R${self.valor_pedido:.2f} "
            f"consultor={self.consultor!r}>"
        )
