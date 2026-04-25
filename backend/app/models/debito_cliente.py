"""
CRM VITAO360 — Model DebitoCliente

Inadimplencia (debitos abertos) por cliente, alimentada pelos relatorios
debitos_*.xlsx do Sales Hunter (SAP).

REGRAS CRITICAS:
  R1 — Two-Base: cada registro representa um valor R$ devido — VENDA-side.
       Esta tabela NUNCA mistura LOG.
  R2 — cnpj: String(14), zero-padded, NUNCA Float.
  R8 — classificacao_3tier: REAL para registros oriundos do SAP.

Status (calculado):
  PAGO       -> data_pagamento IS NOT NULL
  VENCIDO    -> data_vencimento < hoje E data_pagamento IS NULL
  A_VENCER   -> data_vencimento >= hoje E data_pagamento IS NULL

dias_atraso (calculado):
  PAGO    -> 0
  VENCIDO -> (hoje - data_vencimento).days
  A_VENCER -> 0

Idempotencia: chave logica (cnpj, nro_nfe, parcela) — script ingest_sales_hunter.py
faz SELECT antes de INSERT para evitar duplicar.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.sql import func

from backend.app.database import Base


class DebitoCliente(Base):
    """
    Debito (titulo a receber) de um cliente.

    Fonte canonica: SAP via Sales Hunter (debitos_cwb_all_*.xlsx,
    debitos_vv_all_*.xlsx).

    Chave de negocio: (cnpj, nro_nfe, parcela) — usada para idempotencia
    no ingest. Sem UNIQUE constraint pq SAP pode emitir parcelas com
    mesmo numero em momentos distintos (defensivo).
    Chave tecnica: id (autoincrement).
    """

    __tablename__ = "debitos_clientes"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R2: CNPJ sempre String(14), zero-padded, sem pontuacao.
    # Index idx_debitos_cnpj criado via migration alembic.
    cnpj = Column(String(14), nullable=False)

    # ------------------------------------------------------------------
    # Identificacao do titulo
    # ------------------------------------------------------------------
    cod_pedido = Column(String(50), nullable=True)
    nro_nfe = Column(String(50), nullable=True)
    parcela = Column(String(5), nullable=True)

    # ------------------------------------------------------------------
    # Datas
    # ------------------------------------------------------------------
    data_lancamento = Column(Date, nullable=True)
    data_vencimento = Column(Date, nullable=True)
    # NULL = nao pago (cliente devendo)
    data_pagamento = Column(Date, nullable=True)

    # ------------------------------------------------------------------
    # Valor (R1: Two-Base — VENDA-side)
    # ------------------------------------------------------------------
    valor = Column(Float, nullable=False)

    # ------------------------------------------------------------------
    # Calculados pelo ingest
    # ------------------------------------------------------------------
    dias_atraso = Column(Integer, nullable=True)
    # 'PAGO' | 'VENCIDO' | 'A_VENCER'
    # Index idx_debitos_status criado via migration alembic.
    status = Column(String(20), nullable=True)

    # ------------------------------------------------------------------
    # Origem / Classificacao 3-tier (R8)
    # ------------------------------------------------------------------
    fonte = Column(String(20), nullable=True, default="SAP")
    classificacao_3tier = Column(String(15), nullable=True, default="REAL")

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # NOTA: indexes idx_debitos_cnpj e idx_debitos_status sao criados pela
    # migration alembic 05d36e618c52. Nao redeclarar aqui para evitar
    # conflito de nome em autogenerate.

    def __repr__(self) -> str:
        return (
            f"<DebitoCliente id={self.id} cnpj={self.cnpj!r} "
            f"valor=R${self.valor:.2f} status={self.status!r} "
            f"dias_atraso={self.dias_atraso}>"
        )
