"""
CRM VITAO360 — scripts.parsers
================================
Parsers de arquivos XLSX enviados pelo CFO para o pipeline DDE/AC.

Modulos:
  dre_corrections  — 22 padroes regex de normalizacao de contas DRE
  base_parser      — BaseParser ABC com pipeline validate -> extract -> normalize -> upsert
  parser_zsdfat    — ZSDFAT_<cliente>.xlsx (SAP DRE, 13 abas, usa 22 regex)
  parser_verbas    — Verbas xxxx.xlsx     -> cliente_verba_anual (tipo=EFETIVADA)
  parser_frete     — Frete por Cliente.xlsx -> cliente_frete_mensal
  parser_contratos — Controle Contratos.xlsx -> cliente_verba_anual (tipo=CONTRATO)
  parser_promotores — Despesas Clientes V2.xlsx -> cliente_promotor_mensal
"""

from scripts.parsers.dre_corrections import normaliza_conta_dre, DRE_CORRECOES
from scripts.parsers.base_parser import BaseParser, ValidationResult

__all__ = [
    "normaliza_conta_dre",
    "DRE_CORRECOES",
    "BaseParser",
    "ValidationResult",
]
