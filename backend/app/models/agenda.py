"""
CRM VITAO360 — Model AgendaItem

Representa um atendimento priorizado na agenda diária de um consultor.
Gerado pelo Agenda Engine (scripts/motor/agenda_engine.py).

Relacionamento: many AgendaItems → one Cliente (via cnpj como FK).
"""

from __future__ import annotations

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.app.database import Base


class AgendaItem(Base):
    """
    Um item de agenda diária para um consultor específico.

    posicao: ordem no dia (1 = mais prioritário).
    cnpj pode ser nulo para clientes ainda sem CNPJ no sistema.
    """

    __tablename__ = "agenda_items"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: String(14) — pode ser NULL quando agenda_engine não resolveu o CNPJ
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), index=True, nullable=True)

    # ------------------------------------------------------------------
    # Contexto do atendimento
    # ------------------------------------------------------------------
    consultor = Column(String(50), nullable=False, index=True)
    data_agenda = Column(Date, nullable=False, index=True)
    posicao = Column(Integer, nullable=False)     # 1-based ranking no dia

    # ------------------------------------------------------------------
    # Dados de priorização (copiados do pipeline para leitura rápida)
    # ------------------------------------------------------------------
    nome_fantasia = Column(String(255))
    situacao = Column(String(20))
    temperatura = Column(String(20))
    score = Column(Float)
    prioridade = Column(String(5))
    sinaleiro = Column(String(20))
    acao = Column(String(200))       # Ação recomendada para este atendimento
    followup_dias = Column(Integer)

    # ------------------------------------------------------------------
    # Relacionamento ORM (lazy por padrão — não impacta queries simples)
    # ------------------------------------------------------------------
    cliente = relationship(
        "Cliente",
        backref="agenda_items",
        foreign_keys=[cnpj],
        primaryjoin="AgendaItem.cnpj == Cliente.cnpj",
    )

    def __repr__(self) -> str:
        return (
            f"<AgendaItem consultor={self.consultor!r} "
            f"data={self.data_agenda} pos={self.posicao} "
            f"cnpj={self.cnpj!r} score={self.score}>"
        )
