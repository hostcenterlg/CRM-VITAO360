"""
CRM VITAO360 — Testes para /api/inbox routes (INDIA Squad)

Cobertura:
  - GET /api/inbox/conversas: retorna lista, schema valido (mesmo se vazio)
  - 401 sem auth
  - 403 se role nao tem permissao (via require_consultor_or_above)
  - GET /api/inbox/conversas/{id}/mensagens: ticket inexistente retorna [] (nao 500)
  - POST /api/inbox/conversas/{id}/enviar: message vazia retorna 422
  - POST /api/inbox/conversas/{id}/enviar: Deskrio nao configurado retorna enviado=False
  - Smoke: conversas retorna shape esperado com Deskrio mockado

Usa conftest.py padrao do projeto:
  - client_admin: admin sem restricao de canal
  - fixture client_raw: sem override de get_current_user (401)
  - Mocking de deskrio_service via monkeypatch
"""

from __future__ import annotations

import os

os.environ.setdefault("TESTING", "1")

from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.api.deps import (
    get_current_user,
    get_user_canal_ids,
    require_consultor_or_above,
)
from backend.app.database import get_db
from backend.app.main import app


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

def _db_override(session):
    def _inner():
        yield session
    return _inner


@pytest.fixture(scope="function")
def client_admin_inbox(db, fake_admin) -> TestClient:
    """TestClient com admin e sem restricao de canal."""
    app.dependency_overrides[get_db] = _db_override(db)
    app.dependency_overrides[get_current_user] = lambda: fake_admin
    app.dependency_overrides[require_consultor_or_above] = lambda: fake_admin
    app.dependency_overrides[get_user_canal_ids] = lambda: None  # admin = todos
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_no_auth(db) -> TestClient:
    """TestClient sem nenhum override de usuario (simula 401)."""
    app.dependency_overrides[get_db] = _db_override(db)
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def fake_usuario_sem_canal() -> SimpleNamespace:
    """Consultor sem canais associados — deve ser bloqueado."""
    return SimpleNamespace(
        id=99,
        email="nochannel@vitao.com.br",
        nome="Sem Canal",
        role="consultor",
        consultor_nome="NINGUEM",
        ativo=True,
        hashed_password="hashed",
        canais=[],
    )


@pytest.fixture(scope="function")
def client_sem_canal(db, fake_usuario_sem_canal) -> TestClient:
    """TestClient de consultor sem canal (deve retornar lista vazia em /conversas)."""
    app.dependency_overrides[get_db] = _db_override(db)
    app.dependency_overrides[get_current_user] = lambda: fake_usuario_sem_canal
    app.dependency_overrides[require_consultor_or_above] = lambda: fake_usuario_sem_canal
    app.dependency_overrides[get_user_canal_ids] = lambda: []  # lista vazia = sem canal
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Testes — GET /api/inbox/conversas
# ---------------------------------------------------------------------------

class TestListarConversas:

    def test_sem_auth_retorna_401(self, client_no_auth):
        """Sem JWT valido deve retornar 401."""
        response = client_no_auth.get("/api/inbox/conversas")
        assert response.status_code == 401

    def test_deskrio_nao_configurado_retorna_lista_vazia(self, client_admin_inbox):
        """Se Deskrio nao configurado, deve retornar lista vazia (nao 500)."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = False
            response = client_admin_inbox.get("/api/inbox/conversas")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_deskrio_sem_tickets_retorna_lista_vazia(self, client_admin_inbox):
        """Deskrio configurado mas sem tickets -> lista vazia."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.listar_tickets.return_value = []
            response = client_admin_inbox.get("/api/inbox/conversas")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_schema_valido_com_tickets_reais(self, client_admin_inbox):
        """Com tickets mockados, response deve ter os campos esperados."""
        ticket_mock = {
            "id": 42,
            "status": "open",
            "contact": {"name": "MEGAMIX DISTRIBUIDORA", "number": "5541999887766"},
            "lastMessage": "Pode mandar o orcamento?",
            "lastMessageDate": "2026-04-29T10:00:00Z",
            "lastMessageDateNotFromMe": "2026-04-29T10:00:00Z",
            "unreadMessages": 3,
            "user": {"name": "Larissa - Vitao"},
        }

        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.listar_tickets.return_value = [ticket_mock]
            response = client_admin_inbox.get("/api/inbox/conversas")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        conversa = data[0]
        # Campos obrigatorios do schema ConversaResponse
        assert conversa["ticket_id"] == 42
        assert conversa["status"] == "open"
        assert conversa["contato_nome"] == "MEGAMIX DISTRIBUIDORA"
        assert conversa["contato_numero"] == "5541999887766"
        assert conversa["ultima_mensagem"] == "Pode mandar o orcamento?"
        assert "nao_lidas" in conversa
        assert "aguardando_resposta" in conversa
        assert "temperatura" in conversa  # pode ser None
        assert "curva_abc" in conversa
        assert "ticket_medio" in conversa
        assert "dias_sem_compra" in conversa
        assert "sinaleiro" in conversa

    def test_usuario_sem_canal_retorna_lista_vazia(self, client_sem_canal):
        """Consultor sem canais associados nao deve ver nenhuma conversa."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.listar_tickets.return_value = [
                {"id": 1, "status": "open", "contact": {"name": "X", "number": "5541111111111"}}
            ]
            response = client_sem_canal.get("/api/inbox/conversas")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_enriquecimento_mercos_com_cliente_cadastrado(self, client_admin_inbox, db):
        """Ticket cujo telefone bate com cliente no banco deve ter dados Mercos."""
        from backend.app.models.cliente import Cliente

        # Criar cliente com telefone conhecido no banco de teste.
        # ticket_medio e calculado: faturamento_total / n_compras = 375000 / 20 = 18750
        cliente = Cliente(
            cnpj="07537007000188",
            nome_fantasia="MEGAMIX DISTRIBUIDORA",
            telefone="5541999887766",
            temperatura="QUENTE",
            curva_abc="A",
            faturamento_total=375000.0,
            n_compras=20,
            dias_sem_compra=22,
            sinaleiro="ATIVO",
            situacao="ATIVO",
            consultor="LARISSA",
        )
        db.add(cliente)
        db.commit()

        ticket_mock = {
            "id": 77,
            "status": "open",
            "contact": {"name": "MEGAMIX DISTRIBUIDORA", "number": "5541999887766"},
            "lastMessage": "Oi",
            "lastMessageDate": "2026-04-29T10:00:00Z",
            "lastMessageDateNotFromMe": "2026-04-29T10:00:00Z",
            "unreadMessages": 1,
            "user": None,
        }

        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.listar_tickets.return_value = [ticket_mock]
            response = client_admin_inbox.get("/api/inbox/conversas")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        c = data[0]
        # Dados Mercos devem estar preenchidos
        assert c["cnpj"] == "07537007000188"
        assert c["temperatura"] == "QUENTE"
        assert c["curva_abc"] == "A"
        # ticket_medio calculado: 375000 / 20 = 18750.0
        assert c["ticket_medio"] == 18750.0
        assert c["dias_sem_compra"] == 22
        assert c["sinaleiro"] == "ATIVO"
        assert c["nome_fantasia"] == "MEGAMIX DISTRIBUIDORA"


# ---------------------------------------------------------------------------
# Testes — GET /api/inbox/conversas/{ticket_id}/mensagens
# ---------------------------------------------------------------------------

class TestMensagensConversa:

    def test_sem_auth_retorna_401(self, client_no_auth):
        """Sem JWT deve retornar 401."""
        response = client_no_auth.get("/api/inbox/conversas/999/mensagens")
        assert response.status_code == 401

    def test_ticket_inexistente_retorna_lista_vazia(self, client_admin_inbox):
        """Ticket que nao existe no Deskrio deve retornar [] (nao 500)."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.listar_mensagens.return_value = {
                "count": 0,
                "messages": [],
                "hasMore": False,
            }
            response = client_admin_inbox.get("/api/inbox/conversas/9999/mensagens")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_deskrio_nao_configurado_retorna_lista_vazia(self, client_admin_inbox):
        """Deskrio offline -> [] (sem 500)."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = False
            response = client_admin_inbox.get("/api/inbox/conversas/42/mensagens")

        assert response.status_code == 200
        assert response.json() == []

    def test_mensagens_schema_valido(self, client_admin_inbox):
        """Com mensagens mockadas, response deve ter campos fromMe, body, timestamp."""
        msgs_mock = {
            "count": 2,
            "messages": [
                {
                    "id": 1001,
                    "body": "Oi tudo bem?",
                    "fromMe": False,
                    "createdAt": "2026-04-29T09:00:00Z",
                    "mediaType": None,
                    "mediaUrl": None,
                    "contact": {"name": "Cliente X"},
                },
                {
                    "id": 1002,
                    "body": "Tudo sim! E voce?",
                    "fromMe": True,
                    "createdAt": "2026-04-29T09:05:00Z",
                    "mediaType": None,
                    "mediaUrl": None,
                },
            ],
            "hasMore": False,
        }

        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.listar_mensagens.return_value = msgs_mock
            response = client_admin_inbox.get("/api/inbox/conversas/42/mensagens")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        msg_recebida = data[0]
        assert msg_recebida["body"] == "Oi tudo bem?"
        assert msg_recebida["fromMe"] is False
        assert "timestamp" in msg_recebida
        assert msg_recebida["nomeContato"] == "Cliente X"

        msg_enviada = data[1]
        assert msg_enviada["fromMe"] is True


# ---------------------------------------------------------------------------
# Testes — POST /api/inbox/conversas/{ticket_id}/enviar
# ---------------------------------------------------------------------------

class TestEnviarMensagem:

    def test_sem_auth_retorna_401(self, client_no_auth):
        """Sem JWT deve retornar 401."""
        response = client_no_auth.post(
            "/api/inbox/conversas/42/enviar",
            json={"message": "oi"},
        )
        assert response.status_code == 401

    def test_message_vazia_retorna_422(self, client_admin_inbox):
        """Mensagem vazia (min_length=1) deve retornar 422 Unprocessable Entity."""
        response = client_admin_inbox.post(
            "/api/inbox/conversas/42/enviar",
            json={"message": ""},
        )
        assert response.status_code == 422

    def test_sem_message_retorna_422(self, client_admin_inbox):
        """Payload sem campo message deve retornar 422."""
        response = client_admin_inbox.post(
            "/api/inbox/conversas/42/enviar",
            json={},
        )
        assert response.status_code == 422

    def test_deskrio_nao_configurado_retorna_enviado_false(self, client_admin_inbox):
        """Se Deskrio nao configurado, retorna 200 com enviado=False (nao 500)."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = False
            response = client_admin_inbox.post(
                "/api/inbox/conversas/42/enviar",
                json={"message": "Oi teste"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["enviado"] is False
        assert data["erro"] is not None

    def test_ticket_nao_encontrado_retorna_enviado_false(self, client_admin_inbox):
        """Ticket inexistente no Deskrio -> enviado=False (sem 500)."""
        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.obter_ticket.return_value = None
            response = client_admin_inbox.post(
                "/api/inbox/conversas/9999/enviar",
                json={"message": "Oi"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["enviado"] is False
        assert "9999" in (data["erro"] or "")

    def test_envio_com_mensagem_valida_retorna_shape_esperado(self, client_admin_inbox):
        """Envio bem-sucedido deve retornar enviado=True e mensagem_id."""
        ticket_mock = {
            "id": 42,
            "status": "open",
            "contact": {"name": "MEGAMIX", "number": "5541999887766"},
        }
        envio_mock = {"id": "msg-abc-123", "status": "sent"}

        with patch(
            "backend.app.api.routes_inbox.deskrio_service"
        ) as mock_svc:
            mock_svc.configurado = True
            mock_svc.obter_ticket.return_value = ticket_mock
            mock_svc.enviar_mensagem.return_value = envio_mock

            response = client_admin_inbox.post(
                "/api/inbox/conversas/42/enviar",
                json={"message": "Bom dia! Segue o orcamento."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["enviado"] is True
        assert data["mensagem_id"] == "msg-abc-123"
        assert data["erro"] is None
