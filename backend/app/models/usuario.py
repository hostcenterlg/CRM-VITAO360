"""
CRM VITAO360 — Model Usuario

Representa um usuário autenticado do sistema SaaS.

Roles possíveis:
  admin              — acesso total, sem restrição por consultor
  gerente            — vê todos os consultores, sem permissão de configuração (Daiane)
  consultor          — acesso restrito à sua própria carteira (campo consultor_nome)
  consultor_externo  — carteira própria, sem acesso a dados financeiros (Julio)

Relacionamento: um Usuario pode ser criado_por de ImportJob e LogInteracao.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
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

    # Role: admin | gerente | consultor | consultor_externo
    role = Column(String(20), nullable=False, default="consultor")

    # DE-PARA vendedor: MANU, LARISSA, DAIANE, JULIO — NULL para admin/gerente
    consultor_nome = Column(String(50), nullable=True)

    # ------------------------------------------------------------------
    # Status / Auditoria
    # ------------------------------------------------------------------
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

    # Relacionamento N:N com canais (DECISAO L3 — quem ve o que)
    canais = relationship(
        "Canal", secondary="usuario_canal", back_populates="usuarios"
    )

    def __repr__(self) -> str:
        return (
            f"<Usuario id={self.id} email={self.email!r} "
            f"role={self.role!r} ativo={self.ativo}>"
        )
