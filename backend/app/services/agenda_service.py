"""
CRM VITAO360 — Servico de geracao de agenda inteligente.

Responsabilidades:
  - Gerar agenda diaria priorizada por consultor
  - Aplicar regras de limite: 40 atendimentos (Daiane: 20)
  - Garantir ordem: P0 (pula fila, nao conta) -> P1 -> P2-P6 por score desc
  - Excluir P7 (CAMPANHA) da agenda regular
  - Excluir dados classificados como ALUCINACAO (R8)

Regras de negocio:
  P0 — IMEDIATA: pula fila, nao conta no limite de 40
  P1 — URGENTE: conta no limite, entra antes dos regulares
  P2-P6 — REGULAR: conta no limite, ordenado por score desc
  P7 — CAMPANHA: NUNCA entra na agenda regular

Integracao:
  - Cron (FASE 10 — deploy) deve chamar agenda_service.gerar_todas() diariamente
  - Exemplo: `python -c "from backend.app.services.agenda_service import agenda_service; ..."`
  - Ver FASE 10 para configuracao do scheduler em producao

R8 — Zero alucinacao: classificacao_3tier != "ALUCINACAO" e nao-nulo.
R4 — Two-Base: este servico nao toca valores monetarios.
R5 — CNPJ: copiado do Cliente como String(14).
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.agenda import AgendaItem
from backend.app.models.cliente import Cliente

# ---------------------------------------------------------------------------
# Constantes — extraidas de scripts/motor/agenda_engine.py
# ---------------------------------------------------------------------------

CONSULTORES: dict[str, dict] = {
    "LARISSA": {"max": 40},
    "MANU":    {"max": 40},
    "JULIO":   {"max": 40},
    "DAIANE":  {"max": 20},
}

# Prioridades que entram na agenda e contam no limite (ordenadas por urgencia)
_PRIORIDADES_REGULARES = ("P1", "P2", "P3", "P4", "P5", "P6")

# P0 pula fila e nao conta no limite
_PRIORIDADE_IMEDIATA = "P0"

# P7 NUNCA entra na agenda regular
_PRIORIDADE_CAMPANHA = "P7"


# ---------------------------------------------------------------------------
# Servico
# ---------------------------------------------------------------------------

class AgendaService:
    """
    Gera e persiste agendas diarias priorizadas para os consultores VITAO360.

    Uso tipico (chamada via endpoint ou cron):
        resultado = agenda_service.gerar_todas(db, date.today())
        db.commit()
    """

    def gerar_agenda_consultor(
        self,
        db: Session,
        consultor: str,
        data: date,
    ) -> list[AgendaItem]:
        """
        Gera lista de AgendaItems priorizados para um consultor em uma data.

        A lista NAO e persistida aqui — o caller deve chamar db.add() em cada
        item e db.commit() ao final (permite operacoes em batch).

        Ordem de montagem:
          1. P0 (IMEDIATA) — todos entram, nao contam no limite
          2. P1 (URGENTE) — ate o limite max
          3. P2-P6 (REGULAR) — por score desc, ate o limite max

        P7 (CAMPANHA) — NUNCA incluido.

        Args:
            db: Sessao SQLAlchemy ativa.
            consultor: Nome do consultor (MANU, LARISSA, DAIANE, JULIO).
            data: Data de referencia da agenda.

        Returns:
            Lista de AgendaItem (nao persistida, sem id).
        """
        max_items = CONSULTORES.get(consultor, {}).get("max", 40)

        # Buscar clientes do consultor — excluir ALUCINACAO (R8)
        clientes: list[Cliente] = (
            db.query(Cliente)
            .filter(
                Cliente.consultor == consultor,
                Cliente.classificacao_3tier != "ALUCINACAO",
                Cliente.classificacao_3tier.isnot(None),
            )
            .all()
        )

        # Separar por prioridade
        p0 = [c for c in clientes if c.prioridade == _PRIORIDADE_IMEDIATA]
        p1 = [c for c in clientes if c.prioridade == "P1"]
        regulares = [c for c in clientes if c.prioridade in ("P2", "P3", "P4", "P5", "P6")]
        # P7 explicitamente ignorado — CAMPANHA nao entra na agenda regular

        # P1 e regulares ordenados por score desc (maior score = maior urgencia)
        p1.sort(key=lambda c: (c.score or 0.0), reverse=True)
        regulares.sort(key=lambda c: (c.score or 0.0), reverse=True)

        agenda_items: list[AgendaItem] = []
        posicao = 1

        # P0 — pula fila, todos entram, NAO contam no limite
        for c in p0:
            agenda_items.append(self._criar_item(c, consultor, data, posicao))
            posicao += 1

        # P1 + regulares — ate max_items (contados juntos)
        contados = 0
        for c in p1 + regulares:
            if contados >= max_items:
                break
            agenda_items.append(self._criar_item(c, consultor, data, posicao))
            posicao += 1
            contados += 1

        return agenda_items

    def gerar_todas(
        self,
        db: Session,
        data: Optional[date] = None,
    ) -> dict[str, int]:
        """
        Gera agenda para TODOS os consultores em uma data.

        Limpa os itens existentes para a data antes de gerar novos —
        idempotente: rodar duas vezes na mesma data nao cria duplicatas.

        O commit NAO e feito aqui — responsabilidade do caller (endpoint ou cron).

        Args:
            db: Sessao SQLAlchemy ativa.
            data: Data de referencia. Padrao: date.today().

        Returns:
            Dict {consultor: qtd_itens_gerados} para log e resposta de API.
        """
        data = data or date.today()

        # Limpar agenda existente para esta data (idempotencia)
        db.query(AgendaItem).filter(AgendaItem.data_agenda == data).delete(
            synchronize_session="fetch"
        )

        resultado: dict[str, int] = {}
        for consultor in CONSULTORES:
            items = self.gerar_agenda_consultor(db, consultor, data)
            for item in items:
                db.add(item)
            resultado[consultor] = len(items)

        db.flush()
        return resultado

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _criar_item(
        self,
        cliente: Cliente,
        consultor: str,
        data: date,
        posicao: int,
    ) -> AgendaItem:
        """
        Cria um AgendaItem a partir de um Cliente.

        Copia apenas os campos necessarios para leitura rapida na agenda —
        nao cria referencia direta ao objeto Cliente para evitar lazy load
        em contextos de serializacao.
        """
        return AgendaItem(
            cnpj=cliente.cnpj,
            consultor=consultor,
            data_agenda=data,
            posicao=posicao,
            nome_fantasia=cliente.nome_fantasia,
            situacao=cliente.situacao,
            temperatura=cliente.temperatura,
            score=cliente.score,
            prioridade=cliente.prioridade,
            sinaleiro=cliente.sinaleiro,
            acao=cliente.acao_futura,
            followup_dias=cliente.followup_dias,
        )


# Instancia singleton — importar e usar diretamente nas rotas e no cron
agenda_service = AgendaService()
