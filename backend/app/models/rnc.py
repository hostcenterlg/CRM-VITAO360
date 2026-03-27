"""
CRM VITAO360 — Model RNC

RNC = Registro de Não Conformidade.

Representa um problema aberto (reclamação, entrega incorreta, qualidade, etc.)
vinculado a um cliente.  O campo problema_aberto no model Cliente é atualizado
pelo pipeline quando existe ao menos um RNC com status != "RESOLVIDO".

Ciclo de vida:
  ABERTO → EM_ANDAMENTO → RESOLVIDO
  ABERTO → CANCELADO (cancelado antes de resolucao — PRD FR-028)
  ABERTO → ENCERRADO  (alias legado — aceito para dados existentes)

Categorias (alinhadas PRD FR-028):
  ATRASO ENTREGA (TRANSPORTADORA)
  PRODUTO AVARIADO (FABRICA/TRANSPORTE)
  ERRO SEPARAÇÃO (EXPEDIÇÃO)
  ERRO NOTA FISCAL (FATURAMENTO)
  DIVERGÊNCIA PREÇO (FATURAMENTO)
  COBRANÇA INDEVIDA (FINANCEIRO)
  RUPTURA ESTOQUE (FABRICA/PCP)
  PROBLEMA SISTEMA (TI)

R5: cnpj = String(14), nunca float.
"""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func

from backend.app.database import Base


class RNC(Base):
    """
    Registro de Não Conformidade vinculado a um cliente.

    Chave técnica: id (autoincrement).
    R5: cnpj = String(14), nunca float.
    """

    __tablename__ = "rnc"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuação
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Dados da ocorrência
    # ------------------------------------------------------------------
    data_abertura = Column(Date, nullable=False)
    consultor = Column(String(50), nullable=False, index=True)   # Consultor responsável

    # Categorias PRD FR-028 (8 com área responsável):
    #   ATRASO ENTREGA (TRANSPORTADORA), PRODUTO AVARIADO (FABRICA/TRANSPORTE),
    #   ERRO SEPARAÇÃO (EXPEDIÇÃO), ERRO NOTA FISCAL (FATURAMENTO),
    #   DIVERGÊNCIA PREÇO (FATURAMENTO), COBRANÇA INDEVIDA (FINANCEIRO),
    #   RUPTURA ESTOQUE (FABRICA/PCP), PROBLEMA SISTEMA (TI)
    tipo_problema = Column(String(60), nullable=False)

    descricao = Column(Text, nullable=False)

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    # Status: ABERTO, EM_ANDAMENTO, RESOLVIDO, CANCELADO, ENCERRADO (legado)
    status = Column(String(20), nullable=False, default="ABERTO")
    prazo_resolucao = Column(Date, nullable=True)
    responsavel = Column(String(100), nullable=True)    # Quem vai resolver internamente

    # ------------------------------------------------------------------
    # Resolução
    # ------------------------------------------------------------------
    resolucao = Column(Text, nullable=True)
    data_resolucao = Column(Date, nullable=True)

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<RNC id={self.id} cnpj={self.cnpj!r} "
            f"tipo={self.tipo_problema!r} status={self.status!r}>"
        )
