"""
CRM VITAO360 — Model ScoreHistorico

Armazena o histórico de score calculado pelo Score Engine para cada cliente,
por data de cálculo.  Permite análise de evolução de score ao longo do tempo.

O score (0–100) é composto por fatores ponderados:
  fator_fase        — peso da fase do funil (NUTRICAO, ATIVACAO, …)
  fator_sinaleiro   — peso do sinaleiro atual (VERDE, AMARELO, VERMELHO, ROXO)
  fator_curva       — peso da curva ABC (A, B, C)
  fator_temperatura — peso da temperatura comercial (QUENTE, MORNO, FRIO, CRITICO)
  fator_tipo_cliente— peso do tipo de cliente (EM DESENVOLVIMENTO, PROSPECT, …)
  fator_tentativas  — peso pelo número de tentativas de contato (T1–T4)

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
    # Fatores de composição do score (para auditoria e ajuste de pesos)
    # ------------------------------------------------------------------
    fator_fase = Column(Float)
    fator_sinaleiro = Column(Float)
    fator_curva = Column(Float)
    fator_temperatura = Column(Float)
    fator_tipo_cliente = Column(Float)
    fator_tentativas = Column(Float)

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
