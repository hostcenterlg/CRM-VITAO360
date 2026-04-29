"""
CRM VITAO360 — Tests for Deskrio service inbox fixes.

Covers:
  1. listar_conexoes: extrai whatsappConnections do envelope Deskrio
  2. status_conexoes: alguma_conectada=True quando >= 1 CONNECTED
  3. listar_tickets: auto-trunca range > 6 dias (limite API Deskrio)
  4. listar_tickets: 0/3 ativas=offline, 1/3=online, 3/3=online (via status_conexoes)

Nenhum teste depende de credenciais reais — todos usam mock do _get/_post.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Garante que o service pode ser importado sem DATABASE_URL real
os.environ.setdefault("DATABASE_URL", "sqlite:///test_tmp.db")
os.environ.setdefault("DESKRIO_API_URL", "https://appapi.deskrio.com.br")
os.environ.setdefault("DESKRIO_API_TOKEN", "test-token")

from backend.app.services.deskrio_service import DeskrioService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_service() -> DeskrioService:
    """Cria instancia de DeskrioService para testes (sem singleton global)."""
    return DeskrioService()


def _conexoes_raw_deskrio() -> dict[str, Any]:
    """Simula resposta real da API Deskrio /v1/api/connections."""
    return {
        "whatsappConnections": [
            {"id": 4400008, "name": "Mais Granel", "status": "CONNECTED", "number": "554733075968"},
            {"id": 64000032, "name": "Central Vitao", "status": "CONNECTED", "number": "554135236546"},
            {"id": 64000033, "name": "Daiane Vitao", "status": "INATIVE", "number": ""},
        ],
        "whatsappApiConnections": [],
        "metaConnections": [],
    }


# ---------------------------------------------------------------------------
# Bug 1 — listar_conexoes deve extrair envelope whatsappConnections
# ---------------------------------------------------------------------------

class TestListarConexoes:
    def test_extrai_whatsapp_connections_envelope(self):
        """listar_conexoes extrai corretamente do envelope whatsappConnections."""
        svc = _make_service()
        with patch.object(svc, "_get", return_value=_conexoes_raw_deskrio()):
            conexoes = svc.listar_conexoes()

        assert len(conexoes) == 3
        ids = [c["id"] for c in conexoes]
        assert 4400008 in ids
        assert 64000032 in ids
        assert 64000033 in ids

    def test_retorna_lista_vazia_quando_get_none(self):
        """listar_conexoes retorna [] quando _get retorna None (erro HTTP)."""
        svc = _make_service()
        with patch.object(svc, "_get", return_value=None):
            conexoes = svc.listar_conexoes()
        assert conexoes == []

    def test_retorna_lista_vazia_quando_resposta_lista_direta(self):
        """listar_conexoes aceita lista direta (API alternativa)."""
        raw_list = [
            {"id": 1, "name": "Conn1", "status": "CONNECTED"},
        ]
        svc = _make_service()
        with patch.object(svc, "_get", return_value=raw_list):
            conexoes = svc.listar_conexoes()
        assert len(conexoes) == 1
        assert conexoes[0]["id"] == 1

    def test_envelope_desconhecido_retorna_lista_vazia(self):
        """listar_conexoes retorna [] para envelope sem chave conhecida."""
        svc = _make_service()
        with patch.object(svc, "_get", return_value={"unknownKey": [{"id": 99}]}):
            conexoes = svc.listar_conexoes()
        assert conexoes == []


# ---------------------------------------------------------------------------
# Bug 1 — status_conexoes: alguma_conectada calculado corretamente
# ---------------------------------------------------------------------------

class TestStatusConexoes:
    def _status_from_raw(self, raw_connections: list[dict]) -> dict:
        """Helper: injeta lista de conexoes e chama status_conexoes."""
        svc = _make_service()
        envelope = {"whatsappConnections": raw_connections}
        with patch.object(svc, "_get", return_value=envelope):
            return svc.status_conexoes()

    def test_zero_de_tres_ativas_retorna_offline(self):
        """0/3 conexoes CONNECTED => alguma_conectada=False."""
        raw = [
            {"id": 1, "name": "A", "status": "DISCONNECTED"},
            {"id": 2, "name": "B", "status": "INATIVE"},
            {"id": 3, "name": "C", "status": "DISCONNECTED"},
        ]
        status = self._status_from_raw(raw)
        assert status["alguma_conectada"] is False
        assert status["configurado"] is True
        assert status["total_conexoes"] == 3

    def test_uma_de_tres_ativas_retorna_online(self):
        """1/3 conexoes CONNECTED => alguma_conectada=True."""
        raw = [
            {"id": 1, "name": "A", "status": "CONNECTED"},
            {"id": 2, "name": "B", "status": "INATIVE"},
            {"id": 3, "name": "C", "status": "DISCONNECTED"},
        ]
        status = self._status_from_raw(raw)
        assert status["alguma_conectada"] is True

    def test_tres_de_tres_ativas_retorna_online(self):
        """3/3 conexoes CONNECTED => alguma_conectada=True."""
        raw = [
            {"id": 1, "name": "A", "status": "CONNECTED"},
            {"id": 2, "name": "B", "status": "CONNECTED"},
            {"id": 3, "name": "C", "status": "CONNECTED"},
        ]
        status = self._status_from_raw(raw)
        assert status["alguma_conectada"] is True
        assert status["total_conexoes"] == 3

    def test_nao_configurado_retorna_offline(self):
        """Sem credenciais => configurado=False, alguma_conectada=False.

        Simula ausencia de credenciais zerando as env vars temporariamente.
        """
        svc = _make_service()
        # Mock via patch na class-level property (funciona com @property)
        with patch.object(type(svc), "configurado", new_callable=lambda: property(lambda self: False)):
            status = svc.status_conexoes()
        assert status["configurado"] is False
        assert status["alguma_conectada"] is False

    def test_inative_mapeado_para_legivel(self):
        """Status INATIVE deve ser mapeado para 'inativo' no status_legivel."""
        raw = [
            {"id": 1, "name": "Daiane", "status": "INATIVE"},
        ]
        status = self._status_from_raw(raw)
        conn = status["conexoes"][0]
        assert conn["status"] == "INATIVE"
        assert conn["status_legivel"] == "inativo"


# ---------------------------------------------------------------------------
# Bug 2+3 — listar_tickets auto-trunca range > 6 dias
# ---------------------------------------------------------------------------

class TestListarTickets:
    def test_7_dias_truncado_para_6(self):
        """
        Range de 7 dias deve ser auto-truncado para 6 antes de chamar _get.
        Verifica que startDate enviado e <= 6 dias antes de endDate.
        """
        svc = _make_service()
        hoje = date.today()
        inicio7 = hoje - timedelta(days=7)
        fim = hoje

        captured_params: list[dict] = []

        def fake_get(path: str, params: dict | None = None, **kw) -> list:
            if params:
                captured_params.append(dict(params))
            return []

        with patch.object(svc, "_get", side_effect=fake_get):
            svc.listar_tickets(inicio7.isoformat(), fim.isoformat())

        assert len(captured_params) == 1
        start_sent = date.fromisoformat(captured_params[0]["startDate"])
        end_sent = date.fromisoformat(captured_params[0]["endDate"])
        diff = (end_sent - start_sent).days
        assert diff <= 6, f"Range enviado foi {diff} dias, esperado <= 6"

    def test_6_dias_nao_truncado(self):
        """Range de 6 dias deve passar sem modificacao."""
        svc = _make_service()
        hoje = date.today()
        inicio6 = hoje - timedelta(days=6)

        captured_params: list[dict] = []

        def fake_get(path: str, params: dict | None = None, **kw) -> list:
            if params:
                captured_params.append(dict(params))
            return []

        with patch.object(svc, "_get", side_effect=fake_get):
            svc.listar_tickets(inicio6.isoformat(), hoje.isoformat())

        assert captured_params[0]["startDate"] == inicio6.isoformat()

    def test_retorna_lista_quando_api_retorna_lista(self):
        """listar_tickets retorna lista quando API retorna lista direta."""
        raw_tickets = [
            {"id": 100, "status": "open", "contact": {"name": "Cliente A", "number": "5541999999999"}},
            {"id": 101, "status": "closed", "contact": {"name": "Cliente B", "number": "5542888888888"}},
        ]
        svc = _make_service()
        hoje = date.today()
        inicio = hoje - timedelta(days=3)
        with patch.object(svc, "_get", return_value=raw_tickets):
            result = svc.listar_tickets(inicio.isoformat(), hoje.isoformat())
        assert len(result) == 2
        assert result[0]["id"] == 100

    def test_retorna_lista_vazia_quando_api_retorna_none(self):
        """listar_tickets retorna [] gracefully quando _get retorna None (HTTP error)."""
        svc = _make_service()
        hoje = date.today()
        inicio = hoje - timedelta(days=3)
        with patch.object(svc, "_get", return_value=None):
            result = svc.listar_tickets(inicio.isoformat(), hoje.isoformat())
        assert result == []

    def test_retorna_lista_vazia_quando_api_retorna_dict_erro(self):
        """listar_tickets retorna [] quando Deskrio retorna {'message': 'ERR_...'}."""
        svc = _make_service()
        hoje = date.today()
        inicio = hoje - timedelta(days=3)
        with patch.object(svc, "_get", return_value={"message": "ERR_DATE_LIMIT_OFF_1_WEEK"}):
            result = svc.listar_tickets(inicio.isoformat(), hoje.isoformat())
        assert result == []

    def test_90_dias_via_buscar_tickets_por_contato_truncado(self):
        """
        buscar_tickets_por_contato usa 90 dias internamente;
        listar_tickets deve auto-truncar para 6 — smoke sem chamada real.
        """
        svc = _make_service()
        captured_params: list[dict] = []

        def fake_get(path: str, params: dict | None = None, **kw) -> list:
            if params:
                captured_params.append(dict(params))
            return []

        with patch.object(svc, "_get", side_effect=fake_get):
            svc.buscar_tickets_por_contato(contact_id=123, limite=5)

        # Deve ter sido chamado pelo menos uma vez (listar_tickets)
        tickets_call = next((p for p in captured_params if "startDate" in p), None)
        assert tickets_call is not None
        start_sent = date.fromisoformat(tickets_call["startDate"])
        end_sent = date.fromisoformat(tickets_call["endDate"])
        diff = (end_sent - start_sent).days
        assert diff <= 6, f"buscar_tickets_por_contato enviou range de {diff} dias, esperado <= 6"
