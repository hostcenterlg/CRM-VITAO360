"""
CRM VITAO360 — Model ScoreHistorico

Armazena o histórico de score calculado pelo Score Engine para cada cliente,
por data de cálculo.  Permite análise de evolução de score ao longo do tempo.

O score (0–100) é composto por fatores ponderados (nomes v2):
  fator_urgencia  — urgência baseada em dias sem compra e ciclo (substitui fator_fase)
  fator_valor     — valor baseado em curva ABC e tipo_cliente (substitui fator_curva)
  fator_followup  — atraso no follow-up agendado (substitui fator_tentativas)
  fator_sinal     — sinaleiro + temperatura comercial (substitui fator_sinaleiro/temperatura)
  fator_tentativa — número de tentativas de contato T1–T4 (substitui fator_tipo_cliente)
  fator_situacao  — situação do cliente (ATIVO, PROSPECT, INAT.REC, INAT.ANT)

Fonte: scripts/motor/score_engine.py
"""

from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from backend.app.database import Base


class ScoreHistorico(Base):
    """
    Snapshot de score de um cliente em uma data específica.

    Permite rastrear evolução de prioridade e identificar tendências.
    Chave técnica: id (autoincrement).
    Chave de negócio: cnpj + data_calculo (combinação única implícita).
    """

    __tablename__ = "score_historico"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuação
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)

    # ------------------------------------------------------------------
    # Score e classificações resultantes
    # ------------------------------------------------------------------
    data_calculo = Column(Date, nullable=False, index=True)
    score = Column(Float, nullable=False)            # 0.0 – 100.0
    prioridade = Column(String(5))                   # P0 – P7
    sinaleiro = Column(String(20))                   # VERDE, AMARELO, VERMELHO, ROXO
    situacao = Column(String(20))                    # ATIVO, PROSPECT, INAT.REC, INAT.ANT

    # ------------------------------------------------------------------
    # Fatores de composição do score v2 (para auditoria e ajuste de pesos)
    # ------------------------------------------------------------------
    fator_urgencia = Column(Float)
    fator_valor = Column(Float)
    fator_followup = Column(Float)
    fator_sinal = Column(Float)
    fator_tentativa = Column(Float)
    fator_situacao = Column(Float)

    # ------------------------------------------------------------------
    # Índices compostos
    # ------------------------------------------------------------------
    __table_args__ = (
        # Consulta principal: histórico de um cliente ordenado por data
        Index("ix_score_hist_cnpj_data", "cnpj", "data_calculo"),
    )

    def __repr__(self) -> str:
        return (
            f"<ScoreHistorico cnpj={self.cnpj!r} data={self.data_calculo} "
            f"score={self.score:.1f} prioridade={self.prioridade!r}>"
        )
