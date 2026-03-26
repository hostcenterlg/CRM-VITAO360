"""
CRM VITAO360 — Model LogInteracao

R4 — TWO-BASE ARCHITECTURE (SAGRADA):
  Esta tabela representa APENAS registros tipo LOG (interações CRM).
  NUNCA armazenar valor monetário aqui — qualquer R$ nesta tabela = violação grave.
  Ligação, visita, e-mail, WhatsApp → LOG = R$ 0,00 SEMPRE.

R5 — CNPJ: String(14), zero-padded, NUNCA Float.

Os campos calculados pelo Motor de Regras (estagio_funil, fase, tipo_contato, etc.)
são preenchidos automaticamente pelo scripts/motor/motor_regras.py na importação.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class LogInteracao(Base):
    """
    Registro de interação/atendimento CRM (sem valor monetário).

    R4: Esta tabela é a metade LOG da Two-Base Architecture.
        NUNCA incluir campos de valor R$ aqui.
    R5: cnpj = String(14), nunca float.

    Os campos de inteligência (estagio_funil, temperatura, etc.) são
    preenchidos pelo Motor de Regras após a importação via Deskrio/manual.

    Chave técnica: id (autoincrement).
    """

    __tablename__ = "log_interacoes"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuação
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Dados da interação
    # ------------------------------------------------------------------
    data_interacao = Column(DateTime, nullable=False, index=True)
    consultor = Column(String(50), nullable=False, index=True)   # MANU, LARISSA, DAIANE, JULIO

    # Resultado da interação (ex.: "Venda Realizada", "Sem Contato", "Reagendado")
    resultado = Column(String(50), nullable=False)

    # Descrição livre / observações do consultor
    descricao = Column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Campos calculados pelo Motor de Regras (preenchidos automaticamente)
    # Fonte: scripts/motor/motor_regras.py — mapeamento situacao+resultado
    # ------------------------------------------------------------------
    estagio_funil = Column(String(50))       # ex.: PROSPECÇÃO, NEGOCIAÇÃO, PÓS-VENDA
    fase = Column(String(30))               # NUTRICAO, ATIVACAO, MANUTENCAO, REATIVACAO
    tipo_contato = Column(String(50))       # LIGACAO, VISITA, WHATSAPP, EMAIL
    acao_futura = Column(String(100))       # Próxima ação recomendada pelo motor
    temperatura = Column(String(20))        # QUENTE, MORNO, FRIO, CRITICO
    follow_up_dias = Column(Integer)        # Dias até próximo follow-up
    grupo_dash = Column(String(50))         # Agrupamento no dashboard
    tentativa = Column(String(5))           # T1, T2, T3, T4, NUTRICAO

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # ------------------------------------------------------------------
    # Relacionamentos ORM
    # ------------------------------------------------------------------
    cliente = relationship(
        "Cliente",
        backref="interacoes",
        foreign_keys=[cnpj],
        primaryjoin="LogInteracao.cnpj == Cliente.cnpj",
    )

    # ------------------------------------------------------------------
    # Índices compostos para queries frequentes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Busca por cliente + período
        Index("ix_log_cnpj_data", "cnpj", "data_interacao"),
        # Busca por consultor + período (dashboard por vendedor)
        Index("ix_log_consultor_data", "consultor", "data_interacao"),
    )

    def __repr__(self) -> str:
        return (
            f"<LogInteracao id={self.id} cnpj={self.cnpj!r} "
            f"data={self.data_interacao} consultor={self.consultor!r} "
            f"resultado={self.resultado!r}>"
        )
