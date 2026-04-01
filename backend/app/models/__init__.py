"""
CRM VITAO360 — Registry de Models SQLAlchemy

Importar todos os models aqui garante que o metadata do Base seja populado
antes de qualquer chamada a Base.metadata.create_all() ou Alembic.

Ordem de importação respeita dependências de FK:
  1. Usuario       — sem FK externa
  2. Cliente       — sem FK externa
  3. AgendaItem    — FK → clientes.cnpj
  4. Venda         — FK → clientes.cnpj        (Two-Base: metade VENDA — R4)
  5. LogInteracao  — FK → clientes.cnpj,        (Two-Base: metade LOG — R4)
                        usuarios.id
  6. RegraMotor    — sem FK externa
  7. ScoreHistorico— FK → clientes.cnpj
  8. Rede          — sem FK externa
  9. RNC           — FK → clientes.cnpj
 10. Meta          — FK → clientes.cnpj
 11. ImportJob     — FK → usuarios.id
 12. AuditLog      — FK → clientes.cnpj, usuarios.id
 13. Produto        — sem FK externa (catálogo de produtos)
 14. PrecoRegional  — FK → produtos.id
 15. VendaItem      — FK → vendas.id, produtos.id  (Two-Base: metade VENDA — R4)
"""

from .cliente import Cliente
from .agenda import AgendaItem
from .usuario import Usuario
from .venda import Venda
from .log_interacao import LogInteracao
from .regra_motor import RegraMotor
from .score_historico import ScoreHistorico
from .rede import Rede
from .rnc import RNC
from .meta import Meta
from .import_job import ImportJob
from .audit_log import AuditLog
from .produto import Produto
from .preco_regional import PrecoRegional
from .venda_item import VendaItem

__all__ = [
    "Cliente",
    "AgendaItem",
    "Usuario",
    "Venda",
    "LogInteracao",
    "RegraMotor",
    "ScoreHistorico",
    "Rede",
    "RNC",
    "Meta",
    "ImportJob",
    "AuditLog",
    "Produto",
    "PrecoRegional",
    "VendaItem",
]
