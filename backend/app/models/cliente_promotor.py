"""
CRM VITAO360 — Model ClientePromotorMensal (DDE L17)

Despesas com promotor PDV por cliente, mensais.
Fonte: "Despesas Clientes V2.xlsx" (upload manual CFO).

REGRAS:
  R5  — cnpj: VARCHAR(14), NUNCA Float.
  R8  — classificacao: REAL | SINTETICO | PENDENTE
  R12 — sem canal_id (filtro via JOIN clientes.canal_id)
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.sql import func

from backend.app.database import Base


class ClientePromotorMensal(Base):
    """
    Despesa com promotor PDV mensal por cliente (DDE linha L17).

    Fonte: LOG_UPLOAD — arquivo "Despesas Clientes V2.xlsx".
    Chave de negócio: (cnpj, agencia, ano, mes) — UNIQUE.
    """

    __tablename__ = "cliente_promotor_mensal"

    # ------------------------------------------------------------------
    # Chave técnica
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre VARCHAR(14), zero-padded, sem pontuação.
    cnpj = Column(String(14), nullable=False, index=True)

    # Nome da agência/empresa de promotoria
    agencia = Column(String(80), nullable=True)

    # ------------------------------------------------------------------
    # Período
    # ------------------------------------------------------------------
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)

    # ------------------------------------------------------------------
    # Dados financeiros
    # ------------------------------------------------------------------
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
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("cnpj", "agencia", "ano", "mes", name="uq_promotor_cnpj_agencia_ano_mes"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClientePromotorMensal cnpj={self.cnpj!r} "
            f"agencia={self.agencia!r} periodo={self.ano}/{self.mes:02d} "
            f"valor=R${self.valor_brl}>"
        )
