"""
CRM VITAO360 — Model Meta

Armazena a meta mensal de faturamento por cliente, por período (ano + mes).

Fontes de meta:
  SAP      — meta oficial importada do ERP SAP
  MANUAL   — meta ajustada manualmente pela gerência

meta_igualitaria: redistribuição igualitária da meta total entre clientes
                  ativos do consultor (campo opcional, calculado pelo pipeline).

R4: realizado é calculado APENAS sobre registros tipo VENDA (Two-Base).
R5: cnpj = String(14), nunca float.
R7: Baseline faturamento 2025 = R$ 2.091.000 (PAINEL CEO DEFINITIVO, corrigido 2026-03-23).
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)

from backend.app.database import Base


class Meta(Base):
    """
    Meta mensal de faturamento por cliente.

    Chave de negócio: (cnpj, ano, mes) — única por período.
    Chave técnica:    id (autoincrement).

    R4: realizado = soma de vendas.valor_pedido APENAS (nunca log_interacoes).
    R5: cnpj = String(14), nunca float.
    """

    __tablename__ = "metas"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuação
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Período
    # ------------------------------------------------------------------
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)    # 1–12

    # ------------------------------------------------------------------
    # Valores de meta e realizado
    # ------------------------------------------------------------------
    # Meta oficial SAP (ou MANUAL quando fonte = "MANUAL")
    meta_sap = Column(Float, nullable=False, default=0.0)

    # Meta redistribuída igualmente entre clientes ativos do consultor (opcional)
    meta_igualitaria = Column(Float, nullable=True)

    # Realizado acumulado no período — calculado APENAS sobre registros VENDA (R4)
    realizado = Column(Float, nullable=False, default=0.0)

    # Fonte da meta: SAP (importado do ERP) ou MANUAL (ajuste gerencial)
    fonte = Column(String(20), nullable=False, default="SAP")

    # ------------------------------------------------------------------
    # Constraints e índices
    # ------------------------------------------------------------------
    __table_args__ = (
        # Garante unicidade por cliente + período
        UniqueConstraint("cnpj", "ano", "mes", name="uq_meta_cnpj_periodo"),
        # Índice para consultas por período (relatórios mensais/anuais)
        Index("ix_meta_periodo", "ano", "mes"),
    )

    def __repr__(self) -> str:
        return (
            f"<Meta cnpj={self.cnpj!r} periodo={self.ano}-{self.mes:02d} "
            f"meta_sap=R${self.meta_sap:.2f} realizado=R${self.realizado:.2f}>"
        )
