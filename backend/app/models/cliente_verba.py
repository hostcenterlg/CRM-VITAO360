"""
CRM VITAO360 — Model ClienteVerbaAnual (DDE L16)

Verbas negociadas com o cliente: contrato anual + verba efetivada mensal.
Fontes: "Controle de Contratos.xlsx" (tipo=CONTRATO) e "Verbas.xlsx" (tipo=EFETIVADA).

REGRAS:
  R5  — cnpj: VARCHAR(14), NUNCA Float.
  R8  — classificacao: REAL | SINTETICO | PENDENTE
  R12 — sem canal_id (filtro via JOIN clientes.canal_id)
"""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from backend.app.database import Base


class ClienteVerbaAnual(Base):
    """
    Verba anual por cliente (DDE linha L16).

    tipo: 'CONTRATO' (Controle de Contratos.xlsx) | 'EFETIVADA' (Verbas.xlsx).
    Chave de negócio: (cnpj, ano, tipo, fonte) — UNIQUE.
    """

    __tablename__ = "cliente_verba_anual"

    # ------------------------------------------------------------------
    # Chave técnica
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre VARCHAR(14), zero-padded, sem pontuação.
    cnpj = Column(String(14), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Período e tipo
    # ------------------------------------------------------------------
    ano = Column(Integer, nullable=False)

    # 'CONTRATO' | 'EFETIVADA'
    tipo = Column(String(20), nullable=False)

    # ------------------------------------------------------------------
    # Dados financeiros
    # ------------------------------------------------------------------
    valor_brl = Column(Numeric(14, 2), nullable=False)

    # Percentual de desconto total negociado no contrato (só tipo=CONTRATO)
    desc_total_pct = Column(Numeric(5, 2), nullable=True)

    # Vigência do contrato
    inicio_vigencia = Column(Date, nullable=True)
    fim_vigencia = Column(Date, nullable=True)

    # ------------------------------------------------------------------
    # Metadados de qualidade (R8 — 3-tier)
    # ------------------------------------------------------------------
    fonte = Column(String(20), nullable=False)
    classificacao = Column(String(10), nullable=False, default="REAL")
    observacao = Column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now())

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("cnpj", "ano", "tipo", "fonte", name="uq_verba_cnpj_ano_tipo_fonte"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClienteVerbaAnual cnpj={self.cnpj!r} "
            f"ano={self.ano} tipo={self.tipo!r} valor=R${self.valor_brl}>"
        )
