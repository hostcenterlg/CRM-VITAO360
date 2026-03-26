"""
CRM VITAO360 — Model ImportJob

Rastreia cada job de importação de dados executado no sistema.

Tipos de importação:
  MERCOS        — relatório de vendas do Mercos (cuidado: R6, nomes mentem nas datas)
  SAP           — exportação do ERP SAP (faturamento, produtos, clientes)
  DESKRIO       — histórico de atendimentos do CRM legado
  XLSX_COMPLETO — importação do Excel master (pipeline_output.json → banco)

Ciclo de vida do status:
  PENDENTE → PROCESSANDO → CONCLUIDO
  PENDENTE → PROCESSANDO → ERRO

Os contadores permitem auditoria pós-importação sem precisar reler os dados:
  registros_lidos      — total de linhas no arquivo de origem
  registros_inseridos  — novos registros criados no banco
  registros_atualizados— registros existentes atualizados
  registros_ignorados  — linhas puladas (duplicatas, dados inválidos, ALUCINACAO — R8)
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from backend.app.database import Base


class ImportJob(Base):
    """
    Job de importação de dados com rastreamento de progresso e erros.

    Chave técnica: id (autoincrement).
    created_by: FK para usuarios.id (permite auditar quem disparou a importação).
    """

    __tablename__ = "import_jobs"

    # ------------------------------------------------------------------
    # Chaves
    # ------------------------------------------------------------------
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ------------------------------------------------------------------
    # Identificação do job
    # ------------------------------------------------------------------
    # Tipo de fonte: MERCOS, SAP, DESKRIO, XLSX_COMPLETO
    tipo = Column(String(20), nullable=False)

    # Nome do arquivo importado (opcional para jobs programáticos)
    arquivo_nome = Column(String(255), nullable=True)

    # ------------------------------------------------------------------
    # Status do processamento
    # ------------------------------------------------------------------
    # PENDENTE → PROCESSANDO → CONCLUIDO | ERRO
    status = Column(String(20), nullable=False, default="PENDENTE")

    # ------------------------------------------------------------------
    # Contadores de resultado
    # ------------------------------------------------------------------
    registros_lidos = Column(Integer, default=0)
    registros_inseridos = Column(Integer, default=0)
    registros_atualizados = Column(Integer, default=0)
    # Ignorados incluem: duplicatas, CNPJs inválidos, dados classificados ALUCINACAO (R8)
    registros_ignorados = Column(Integer, default=0)

    # ------------------------------------------------------------------
    # Detalhes de erro (preenchido apenas quando status = ERRO)
    # ------------------------------------------------------------------
    erro_mensagem = Column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Timestamps de execução
    # ------------------------------------------------------------------
    iniciado_em = Column(DateTime, nullable=True)
    concluido_em = Column(DateTime, nullable=True)

    # ------------------------------------------------------------------
    # Auditoria
    # ------------------------------------------------------------------
    # Quem disparou o job (NULL para jobs automáticos/schedulados)
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return (
            f"<ImportJob id={self.id} tipo={self.tipo!r} "
            f"status={self.status!r} "
            f"inseridos={self.registros_inseridos} "
            f"ignorados={self.registros_ignorados}>"
        )
