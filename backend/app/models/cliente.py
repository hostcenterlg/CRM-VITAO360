"""
CRM VITAO360 — Model Cliente

Tabela principal do CRM.  Mapeia todos os 35 campos produzidos pelo pipeline
motor (pipeline_output.json) + campos de projeção.

REGRAS CRÍTICAS:
  R5  — cnpj: String(14), NUNCA Float.
  R4  — Two-Base: faturamento_total vem APENAS de registros tipo VENDA.
  R9  — Nomes de colunas em português para facilitar manutenção.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from backend.app.database import Base


class Cliente(Base):
    """
    Representa um cliente/prospect na carteira VITAO360.

    Chave de negócio: cnpj (14 dígitos, string, unique).
    Chave técnica:    id  (autoincrement, uso interno do ORM).
    """

    __tablename__ = "clientes"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # R5: CNPJ sempre String(14), zero-padded, sem pontuação.
    cnpj = Column(String(14), unique=True, nullable=False, index=True)

    # ------------------------------------------------------------------
    # Identificação
    # ------------------------------------------------------------------
    nome_fantasia = Column(String(255))
    razao_social = Column(String(255))
    uf = Column(String(2))
    cidade = Column(String(100))
    codigo_cliente = Column(String(20))      # Código SAP (armazenado como str)
    tipo_cliente_sap = Column(String(50))    # REDES/FRANQUIAS, SEM REDE, etc.
    macroregiao = Column(String(50))         # 03 - NACIONAL, 03 - SP CAPITAL, …
    email = Column(String(255), nullable=True)
    telefone = Column(String(20), nullable=True)
    rede_regional = Column(String(100), nullable=True)  # Nome da rede/franquia regional

    # ------------------------------------------------------------------
    # Responsável / Equipe
    # ------------------------------------------------------------------
    consultor = Column(String(50), index=True)   # MANU / LARISSA / DAIANE / JULIO

    # ------------------------------------------------------------------
    # Status comercial
    # ------------------------------------------------------------------
    situacao = Column(String(20), index=True)    # ATIVO / PROSPECT / INAT.REC / INAT.ANT
    tipo_cliente = Column(String(30))            # EM DESENVOLVIMENTO, PROSPECT, …
    classificacao_3tier = Column(String(15))     # REAL / SINTETICO / ALUCINACAO

    # ------------------------------------------------------------------
    # Histórico de compras
    # ------------------------------------------------------------------
    dias_sem_compra = Column(Integer)
    valor_ultimo_pedido = Column(Float)
    ciclo_medio = Column(Float)              # Dias médios entre pedidos
    n_compras = Column(Integer)
    faturamento_total = Column(Float)        # R$ acumulado — APENAS de registros VENDA (R4)

    # ------------------------------------------------------------------
    # Interação CRM
    # ------------------------------------------------------------------
    tipo_contato = Column(String(50))        # LIGACAO, VISITA, WHATSAPP, …
    resultado = Column(String(50))           # Pré Venda / Apresentação, Venda Realizada, …
    estagio_funil = Column(String(50))
    acao_futura = Column(String(100))
    fase = Column(String(30))               # NUTRICAO, ATIVACAO, MANUTENCAO, …

    # ------------------------------------------------------------------
    # Inteligência / Priorização
    # ------------------------------------------------------------------
    temperatura = Column(String(20), index=True)     # QUENTE / MORNO / FRIO / CRITICO
    score = Column(Float)                            # 0–100 (Score Engine)
    prioridade = Column(String(5), index=True)       # P0–P7
    sinaleiro = Column(String(20), index=True)       # VERDE / AMARELO / VERMELHO / ROXO
    curva_abc = Column(String(1), index=True)        # A / B / C

    # ------------------------------------------------------------------
    # Follow-up / CS
    # ------------------------------------------------------------------
    followup_dias = Column(Integer)
    grupo_dash = Column(String(50))
    tipo_acao = Column(String(50))
    tentativas = Column(String(5))           # T1, T2, T3 …
    problema_aberto = Column(Boolean, default=False)
    followup_vencido = Column(Boolean, default=False)
    cs_no_prazo = Column(Boolean, default=False)

    # ------------------------------------------------------------------
    # Projeção / Meta
    # ------------------------------------------------------------------
    meta_anual = Column(Float)
    realizado_acumulado = Column(Float)
    pct_alcancado = Column(Float)            # 0.0–1.0+ (ex.: 0.82 = 82%)
    gap_valor = Column(Float)               # meta_anual - realizado_acumulado
    status_meta = Column(String(10))         # ACIMA / ALERTA / CRITICO

    # ------------------------------------------------------------------
    # Sales Hunter SAP enrichment (Phase 1 — GAP 2C)
    # Alimentado por debitos_*.xlsx + devolucao_cliente_*.xlsx.
    # ------------------------------------------------------------------
    # SUM(debitos_clientes.valor WHERE status='VENCIDO') — atualizado pelo
    # ingest_sales_hunter.py
    total_debitos = Column(Float, default=0)
    # Percentual de devolucao acumulado (ex.: 0.05 = 5%)
    pct_devolucao = Column(Float, nullable=True)
    # Valor total devolvido R$ (acumulado no periodo do relatorio SAP)
    total_devolucao = Column(Float, nullable=True)
    # Risco classificado: 'BAIXO' (<5%) | 'MEDIO' (5-15%) | 'ALTO' (>15%)
    risco_devolucao = Column(String(10), nullable=True)

    # ------------------------------------------------------------------
    # Auditoria de registro
    # ------------------------------------------------------------------
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self) -> str:
        return (
            f"<Cliente cnpj={self.cnpj!r} nome={self.nome_fantasia!r} "
            f"situacao={self.situacao!r} sinaleiro={self.sinaleiro!r}>"
        )
