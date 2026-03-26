"""
CRM VITAO360 — Model Rede

Representa uma rede/franquia de lojas atendidas pela VITAO.

O potencial máximo de uma rede é calculado como:
  total_lojas * R$525 (ticket médio mensal por loja) * 11 meses

O percentual de penetração indica quantas lojas já são clientes ativos:
  pct_penetracao = lojas_ativas / total_lojas

Sinaleiro indica o status consolidado da rede:
  VERDE  — penetração >= 70% e cadência regular
  AMARELO— penetração 30–70% ou cadência irregular
  VERMELHO— penetração < 30% ou churn recente
  ROXO   — rede estratégica com atenção especial da gerência
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from backend.app.database import Base


class Rede(Base):
    """
    Rede ou franquia de lojas com gestão consolidada.

    Chave de negócio: nome (único por rede).
    Chave técnica:    id (autoincrement).
    """

    __tablename__ = "redes"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Nome único da rede (ex.: "Mundo Verde", "Rei do Mate", "Natural da Terra")
    nome = Column(String(100), unique=True, nullable=False)

    # ------------------------------------------------------------------
    # Composição da rede
    # ------------------------------------------------------------------
    total_lojas = Column(Integer, nullable=False, default=0)
    lojas_ativas = Column(Integer, nullable=False, default=0)

    # Consultor responsável pelo relacionamento com a rede (ex.: DAIANE)
    consultor_responsavel = Column(String(50), nullable=True)

    # ------------------------------------------------------------------
    # Indicadores financeiros
    # ------------------------------------------------------------------
    # Faturamento real acumulado (somente de registros tipo VENDA — R4)
    faturamento_real = Column(Float, default=0.0)

    # Potencial máximo: total_lojas * R$525 * 11 meses
    potencial_maximo = Column(Float, default=0.0)

    # Percentual de penetração: lojas_ativas / total_lojas (0.0 – 1.0+)
    pct_penetracao = Column(Float, default=0.0)

    # ------------------------------------------------------------------
    # Inteligência comercial
    # ------------------------------------------------------------------
    sinaleiro = Column(String(20))    # VERDE, AMARELO, VERMELHO, ROXO
    cadencia = Column(String(50))     # Frequência de visita/contato esperada

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self) -> str:
        return (
            f"<Rede id={self.id} nome={self.nome!r} "
            f"lojas={self.lojas_ativas}/{self.total_lojas} "
            f"sinaleiro={self.sinaleiro!r}>"
        )
