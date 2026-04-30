"""
CRM VITAO360 — Model ClienteDrePeriodo (DDE — cache da cascata)

Cache calculado da cascata DDE por cliente/período/linha.
Recalculado pelo dde_engine.py (Onda 3 — OSCAR).

Linhas da cascata: L1..L25, I1..I9.
Classificação 3-tier: REAL | SINTETICO | PENDENTE | NULL.
Fase: 'A' (implementável hoje) | 'B' (espera SAP) | 'C' (espera BI).

REGRAS:
  R5  — cnpj: VARCHAR(14), NUNCA Float.
  R8  — classificacao obrigatória — PENDENTE/NULL são válidos (honestidade > inventar).
  R12 — sem canal_id (filtro via JOIN clientes.canal_id).
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from backend.app.database import Base


class ClienteDrePeriodo(Base):
    """
    Cache da cascata DDE por cliente, período e linha (DDE L1..L25, I1..I9).

    valor_brl nullable: PENDENTE = NULL (honestidade — não inventar valor).
    Chave de negócio: (cnpj, ano, mes, linha) — UNIQUE.
      mes = NULL indica consolidado anual.
    """

    __tablename__ = "cliente_dre_periodo"

    # ------------------------------------------------------------------
    # Chave técnica
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre VARCHAR(14), zero-padded, sem pontuação.
    cnpj = Column(String(14), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Período  (mes=NULL → consolidado anual)
    # ------------------------------------------------------------------
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=True)

    # ------------------------------------------------------------------
    # Linha da cascata DDE
    # ------------------------------------------------------------------
    # Ex.: 'L1', 'L11', 'L21', 'I2' — ref. SPEC_DDE_CASCATA_REAL.md
    linha = Column(String(10), nullable=False)
    conta = Column(String(80), nullable=False)

    # ------------------------------------------------------------------
    # Valor calculado (nullable = PENDENTE / NULL honesto)
    # ------------------------------------------------------------------
    valor_brl = Column(Numeric(14, 2), nullable=True)
    pct_sobre_receita = Column(Numeric(6, 3), nullable=True)

    # ------------------------------------------------------------------
    # Metadados da linha
    # ------------------------------------------------------------------
    # Fonte da linha: SH | SAP | LOG | MERCOS | CALC | MANUAL
    fonte = Column(String(20), nullable=True)

    # Classificação 3-tier: REAL | SINTETICO | PENDENTE | NULL
    classificacao = Column(String(10), nullable=True)

    # Fase de implementação: 'A' | 'B' | 'C'
    fase = Column(String(2), nullable=True)

    observacao = Column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Auditoria de cálculo
    # ------------------------------------------------------------------
    calculado_em = Column(DateTime, server_default=func.now())

    # ------------------------------------------------------------------
    # Constraints e índices
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("cnpj", "ano", "mes", "linha", name="uq_dre_cnpj_ano_mes_linha"),
        Index("idx_dre_cnpj_ano", "cnpj", "ano"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClienteDrePeriodo cnpj={self.cnpj!r} "
            f"periodo={self.ano}/{self.mes} linha={self.linha!r} "
            f"valor={self.valor_brl} classificacao={self.classificacao!r}>"
        )
