"""
CRM VITAO360 — Model ClienteFretesMensal (DDE L14)

Frete CT-e mensal por cliente.
Upload manual mensal pelo CFO: "Frete por Cliente.xlsx".

REGRAS:
  R5  — cnpj: VARCHAR(14), NUNCA Float.
  R8  — classificacao: REAL | SINTETICO | PENDENTE
  R12 — sem canal_id (filtro via JOIN clientes.canal_id)
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.sql import func

from backend.app.database import Base


class ClienteFretesMensal(Base):
    """
    Frete CT-e mensal por cliente (DDE linha L14).

    Fonte: LOG_UPLOAD — arquivo "Frete por Cliente.xlsx" enviado pelo CFO.
    Chave de negócio: (cnpj, ano, mes, fonte) — UNIQUE.
    """

    __tablename__ = "cliente_frete_mensal"

    # ------------------------------------------------------------------
    # Chave técnica
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre VARCHAR(14), zero-padded, sem pontuação.
    cnpj = Column(String(14), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Período
    # ------------------------------------------------------------------
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    # ------------------------------------------------------------------
    # Dados de frete
    # ------------------------------------------------------------------
    qtd_ctes = Column(Integer, nullable=True)
    valor_brl = Column(Numeric(14, 2), nullable=False)

    # ------------------------------------------------------------------
    # Metadados de qualidade (R8 — 3-tier)
    # ------------------------------------------------------------------
    fonte = Column(String(20), nullable=False, default="LOG_UPLOAD")
    classificacao = Column(String(10), nullable=False, default="REAL")

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now())

    # ------------------------------------------------------------------
    # Constraints e índices
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("cnpj", "ano", "mes", "fonte", name="uq_frete_cnpj_ano_mes_fonte"),
        Index("idx_frete_cnpj", "cnpj", "ano"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClienteFretesMensal cnpj={self.cnpj!r} "
            f"periodo={self.ano}/{self.mes:02d} valor=R${self.valor_brl}>"
        )
