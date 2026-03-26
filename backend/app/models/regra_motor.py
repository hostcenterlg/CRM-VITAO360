"""
CRM VITAO360 — Model RegraMotor

Armazena as regras de mapeamento do Motor de Regras CRM.
Cada regra define o que fazer quando uma interação tem determinada
combinação de situacao + resultado.

Fonte de verdade: scripts/motor/motor_regras.py
A chave composta (situacao, resultado) é única — enforçado por UniqueConstraint.

Exemplo de regra:
  situacao="ATIVO"   + resultado="Venda Realizada"
  → estagio_funil="PÓS-VENDA", temperatura="QUENTE", follow_up_dias=30
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from backend.app.database import Base


class RegraMotor(Base):
    """
    Regra de mapeamento situacao+resultado → campos de inteligência CRM.

    chave: campo desnormalizado "SITUACAO|RESULTADO" para busca rápida
           sem necessidade de concatenar na query.
    """

    __tablename__ = "regras_motor"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Inputs da regra (combinação única — ver UniqueConstraint abaixo)
    # ------------------------------------------------------------------
    situacao = Column(String(20), nullable=False)    # ATIVO, PROSPECT, INAT.REC, INAT.ANT, …
    resultado = Column(String(50), nullable=False)   # Venda Realizada, Sem Contato, …

    # ------------------------------------------------------------------
    # Outputs da regra (campos calculados aplicados ao LogInteracao)
    # ------------------------------------------------------------------
    estagio_funil = Column(String(50), nullable=False)
    fase = Column(String(30), nullable=False)
    tipo_contato = Column(String(50), nullable=False)
    acao_futura = Column(String(100), nullable=False)
    temperatura = Column(String(20), nullable=False)
    follow_up_dias = Column(Integer, nullable=False, default=0)
    grupo_dash = Column(String(50))
    tipo_acao = Column(String(50))

    # Chave desnormalizada para lookup direto (ex.: "ATIVO|Venda Realizada")
    chave = Column(String(80), unique=True, nullable=False)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        # Garante que não existam duas regras para o mesmo par situacao+resultado
        UniqueConstraint("situacao", "resultado", name="uq_regra_sit_res"),
    )

    def __repr__(self) -> str:
        return (
            f"<RegraMotor id={self.id} chave={self.chave!r} "
            f"temperatura={self.temperatura!r} follow_up={self.follow_up_dias}d>"
        )
