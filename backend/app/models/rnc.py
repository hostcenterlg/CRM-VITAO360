"""
CRM VITAO360 — Model RNC

RNC = Registro de Não Conformidade.

Representa um problema aberto (reclamação, entrega incorreta, qualidade, etc.)
vinculado a um cliente.  O campo problema_aberto no model Cliente é atualizado
pelo pipeline quando existe ao menos um RNC com status != "RESOLVIDO".

Ciclo de vida:
  ABERTO → EM_ANDAMENTO → RESOLVIDO
  ABERTO → CANCELADO (quando o problema não se confirma)

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

    # Categorias: ENTREGA, QUALIDADE, PAGAMENTO, ATENDIMENTO, PRODUTO, OUTRO
    tipo_problema = Column(String(50), nullable=False)

    descricao = Column(Text, nullable=False)

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    # Status: ABERTO, EM_ANDAMENTO, RESOLVIDO, CANCELADO
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
