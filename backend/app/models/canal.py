"""
CRM VITAO360 — Model Canal

Canal de vendas SAP. Atua como "workspace" do CRM: cada usuario ve
apenas os canais que tem permissao via usuario_canal (N:N).

DECISAO L3 (Leandro 25/Apr/2026): canal eh dimensao de primeira classe.
Todo cliente pertence a 1 canal (canal_id NULL = legado/nao-classificado).

Status:
  ATIVO     — operacional, usuarios podem ver clientes desse canal
  EM_BREVE  — proximo a ativar, ainda em onboarding
  BLOQUEADO — pausado por decisao operacional/legal

Canais oficiais (seed em migration f557927e169e):
  INTERNO         — funcional VITAO  (ATIVO)
  FOOD_SERVICE    — industria/distribuidor/varejo food (ATIVO)
  DIRETO          — Manu/Larissa/Daiane/Julio (EM_BREVE)
  INDIRETO        — distribuidores indiretos (EM_BREVE)
  FARMA           — farmacias e drogarias (EM_BREVE)
  BODY            — lojas body / academias (EM_BREVE)
  DIGITAL         — e-commerce/B2C (EM_BREVE)
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Canal(Base):
    """Canal de vendas SAP (workspace dimension do CRM)."""

    __tablename__ = "canais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(15), nullable=False, default="EM_BREVE", index=True)
    descricao = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

    # Relacionamentos N:N
    clientes = relationship("Cliente", back_populates="canal")
    usuarios = relationship(
        "Usuario", secondary="usuario_canal", back_populates="canais"
    )

    def __repr__(self) -> str:
        return f"<Canal id={self.id} nome={self.nome!r} status={self.status!r}>"
