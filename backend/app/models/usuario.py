"""
CRM VITAO360 — Model Usuario

Representa um usuário autenticado do sistema SaaS.

Roles possíveis:
  admin     — acesso total, sem restrição por consultor
  consultor — acesso restrito à sua própria carteira (campo consultor_nome)
  viewer    — somente leitura

Relacionamento: um Usuario pode ser criado_por de ImportJob e LogInteracao.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from backend.app.database import Base


class Usuario(Base):
    """
    Usuário autenticado do CRM VITAO360.

    Chave de negócio: email (único).
    Chave técnica:    id (autoincrement).

    consultor_nome: quando role = 'consultor', vincula ao DE-PARA de vendedores
                    (MANU, LARISSA, DAIANE).  Para admin/viewer fica NULL.
    """

    __tablename__ = "usuarios"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Autenticação
    # ------------------------------------------------------------------
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # ------------------------------------------------------------------
    # Identificação
    # ------------------------------------------------------------------
    nome = Column(String(100), nullable=False)

    # Role: admin | consultor | viewer
    role = Column(String(20), nullable=False, default="consultor")

    # DE-PARA vendedor: MANU, LARISSA, DAIANE — NULL para admin/viewer
    consultor_nome = Column(String(50), nullable=True)

    # ------------------------------------------------------------------
    # Status / Auditoria
    # ------------------------------------------------------------------
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Usuario id={self.id} email={self.email!r} "
            f"role={self.role!r} ativo={self.ativo}>"
        )
