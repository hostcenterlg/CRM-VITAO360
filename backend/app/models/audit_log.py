"""
CRM VITAO360 — Model AuditLog

Registro de auditoria para operacoes de edicao inline de clientes.

R12 — Nivel de Decisao: toda alteracao de campo de cliente feita via PATCH
      e registrada aqui com: quem alterou, quando, o que mudou (campo,
      valor_anterior, valor_novo).

R4 — Two-Base Architecture: este log NAO armazena valores monetarios.
R5 — CNPJ: String(14), zero-padded, nunca Float.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from backend.app.database import Base


class AuditLog(Base):
    """
    Registro de auditoria para alteracoes inline de clientes (PATCH).

    Cada alteracao de campo gera um registro separado, permitindo rastreabilidade
    granular: quem mudou o que, quando, e qual era o valor anterior.

    Chave tecnica: id (autoincrement).
    """

    __tablename__ = "audit_logs"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuacao
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Contexto da operacao
    # ------------------------------------------------------------------
    # Campo alterado (ex.: "consultor", "rede_regional")
    campo = Column(String(50), nullable=False)

    # Valores antes/depois — armazenados como string para genericidade
    valor_anterior = Column(String(255), nullable=True)
    valor_novo = Column(String(255), nullable=True)

    # ------------------------------------------------------------------
    # Autoria
    # ------------------------------------------------------------------
    # ID do usuario que fez a alteracao (FK usuarios.id)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Nome/email do usuario para leitura rapida (denormalizado intencionalmente)
    usuario_nome = Column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} cnpj={self.cnpj!r} "
            f"campo={self.campo!r} por={self.usuario_nome!r} "
            f"em={self.created_at}>"
        )
