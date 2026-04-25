"""
CRM VITAO360 — Model UsuarioCanal (associacao N:N)

Tabela de associacao entre usuarios e canais. Admin define quem ve
quais canais via inserts/deletes nessa tabela.

PK composta: (usuario_id, canal_id).
ON DELETE CASCADE em ambos os lados (cleanup automatico).
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func

from backend.app.database import Base


class UsuarioCanal(Base):
    """Associacao N:N entre usuarios e canais."""

    __tablename__ = "usuario_canal"

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    canal_id = Column(
        Integer,
        ForeignKey("canais.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<UsuarioCanal usuario_id={self.usuario_id} canal_id={self.canal_id}>"
