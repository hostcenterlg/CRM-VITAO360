"""
CRM VITAO360 — Testes de integracao dos endpoints /api/whatsapp.

Estrategia: banco SQLite em memoria com seed minimo.
Deskrio nao configurado por padrao -> graceful degradation em todos os testes.
Testes de envio real sao feitos com mock do DeskrioService.

Cobertura:
  1. GET  /api/whatsapp/status      — sem configuracao, com configuracao mock
  2. GET  /api/whatsapp/contato/{cnpj} — sem configuracao, com configuracao mock
  3. POST /api/whatsapp/enviar      — sem configuracao, contato nao encontrado, sucesso
  4. GET  /api/whatsapp/tickets     — sem configuracao, com configuracao mock
  5. GET  /api/whatsapp/conexoes    — sem configuracao, com configuracao mock
  6. Autenticacao obrigatoria em todos os endpoints

Garantias verificadas:
  R5  — CNPJ normalizado para 14 digitos nas respostas
  R8  — Nunca fabrica dados (enviado=false se contato nao encontrado)
  R10 — Two-Base: nenhum valor monetario nos payloads de WhatsApp
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.usuario import Usuario
from backend.app.security import hash_password


# ---------------------------------------------------------------------------
# Garantia: Deskrio nao configurado por padrao nos testes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="module")
def _sem_deskrio():
    """Remove variaveis Deskrio para forcar graceful degradation."""
    vars_originais = {}
    for var in ("DESKRIO_API_TOKEN", "DESKRIO_API_URL", "DESKRIO_COMPANY_ID"):
        vars_originais[var] = os.environ.pop(var, None)

    yield

    for var, val in vars_originais.items():
        if val is not None:
            os.environ[var] = val


# ---------------------------------------------------------------------------
# Fixtures: banco em memoria
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine_mem():
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="module")
def SessionLocal_mem(engine_mem):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine_mem)


@pytest.fixture(scope="module")
def db_session(SessionLocal_mem):
    session = SessionLocal_mem()
    yield session
    session.close()


@pytest.fixture(scope="module")
def seed_usuario(db_session: Session):
    """Seed de usuario admin para autenticacao nos testes."""
    usuario = Usuario(
        nome="Teste WhatsApp",
        email="test_wa@vitao.com.br",
        hashed_password=hash_password("senha123"),
        role="admin",
        ativo=True,
    )
    db_session.add(usuario)
    db_session.commit()
    db_session.refresh(usuario)
    return usuario


@pytest.fixture(scope="module")
def client(engine_mem, SessionLocal_mem, seed_usuario):
    def override_get_db():
        sess = SessionLocal_mem()
        try:
            yield sess
        finally:
            sess.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def token(client):
    """Token JWT valido para testes autenticados."""
    res = client.post(
        "/api/auth/login",
        json={"email": "test_wa@vitao.com.br", "senha": "senha123"},
    )
    assert res.status_code == 200, f"Login falhou: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def auth(token):
    """Cabecalho de autenticacao pronto."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Testes: autenticacao obrigatoria
# ---------------------------------------------------------------------------

class TestAutenticacao:
    def test_status_sem_auth(self, client: TestClient):
        res = client.get("/api/whatsapp/status")
        assert res.status_code == 401

    def test_contato_sem_auth(self, client: TestClient):
        res = client.get("/api/whatsapp/contato/12345678000100")
        assert res.status_code == 401

    def test_enviar_sem_auth(self, client: TestClient):
        res = client.post(
            "/api/whatsapp/enviar",
            json={"cnpj": "12345678000100", "mensagem": "Ola"},
        )
        assert res.status_code == 401

    def test_tickets_sem_auth(self, client: TestClient):
        res = client.get("/api/whatsapp/tickets?cnpj=12345678000100")
        assert res.status_code == 401

    def test_conexoes_sem_auth(self, client: TestClient):
        res = client.get("/api/whatsapp/conexoes")
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# Testes: graceful degradation (sem configuracao Deskrio)
# ---------------------------------------------------------------------------

class TestSemConfiguracao:
    def test_status_retorna_nao_configurado(self, client: TestClient, auth: dict):
        res = client.get("/api/whatsapp/status", headers=auth)
        assert res.status_code == 200
        data = res.json()
        assert data["configurado"] is False
        assert data["conexoes"] == []
        assert data["alguma_conectada"] is False
        assert data["total_conexoes"] == 0

    def test_contato_retorna_nao_encontrado(self, client: TestClient, auth: dict):
        res = client.get("/api/whatsapp/contato/12345678000100", headers=auth)
        assert res.status_code == 200
        data = res.json()
        assert data["encontrado"] is False
        # R5: CNPJ normalizado na resposta
        assert data["cnpj"] == "12345678000100"

    def test_contato_cnpj_formatado_normaliza(self, client: TestClient, auth: dict):
        """R5: CNPJ formatado (pontos e traco, sem barra) deve ser normalizado."""
        # Nota: a barra '/' nao pode ser usada em segmentos de URL sem encode;
        # usamos CNPJ com pontos e traco apenas (formato comum de entrada)
        res = client.get("/api/whatsapp/contato/12.345.678000100", headers=auth)
        assert res.status_code == 200
        data = res.json()
        assert data["encontrado"] is False
        # R5: apenas os digitos sao mantidos e zero-padded
        assert data["cnpj"] == "12345678000100"

    def test_enviar_retorna_nao_enviado(self, client: TestClient, auth: dict):
        res = client.post(
            "/api/whatsapp/enviar",
            json={"cnpj": "12345678000100", "mensagem": "Ola, tudo bem?"},
            headers=auth,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["enviado"] is False
        assert data["erro"] is not None
        assert "nao configurado" in data["erro"].lower() or "configurado" in data["erro"].lower()

    def test_tickets_retorna_vazio(self, client: TestClient, auth: dict):
        res = client.get("/api/whatsapp/tickets?cnpj=12345678000100", headers=auth)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 0
        assert data["tickets"] == []

    def test_conexoes_retorna_lista_vazia(self, client: TestClient, auth: dict):
        res = client.get("/api/whatsapp/conexoes", headers=auth)
        assert res.status_code == 200
        assert res.json() == []


# ---------------------------------------------------------------------------
# Testes: com mock do DeskrioService (simula Deskrio configurado)
# ---------------------------------------------------------------------------

def _patch_configurado(svc, value: bool = True):
    """
    Context manager para simular deskrio_service.configurado como propriedade.
    Usa patch no env para forcar a propriedade a retornar o valor desejado.
    """
    import os
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        original_url = os.environ.get("DESKRIO_API_URL", "")
        original_token = os.environ.get("DESKRIO_API_TOKEN", "")
        if value:
            os.environ["DESKRIO_API_URL"] = "https://fake.deskrio.com.br"
            os.environ["DESKRIO_API_TOKEN"] = "fake-token-for-test"
        else:
            os.environ.pop("DESKRIO_API_URL", None)
            os.environ.pop("DESKRIO_API_TOKEN", None)
        try:
            yield
        finally:
            if original_url:
                os.environ["DESKRIO_API_URL"] = original_url
            else:
                os.environ.pop("DESKRIO_API_URL", None)
            if original_token:
                os.environ["DESKRIO_API_TOKEN"] = original_token
            else:
                os.environ.pop("DESKRIO_API_TOKEN", None)

    return _ctx()


class TestComMock:
    def test_status_com_conexoes(self, client: TestClient, auth: dict):
        """Status retorna conexoes quando Deskrio esta configurado e responde."""
        mock_status = {
            "configurado": True,
            "conexoes": [
                {"id": 1, "nome": "Vitao Principal", "status": "CONNECTED", "status_legivel": "conectado"},
                {"id": 2, "nome": "Vitao Backup", "status": "DISCONNECTED", "status_legivel": "desconectado"},
            ],
            "alguma_conectada": True,
            "total_conexoes": 2,
        }
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "status_conexoes", return_value=mock_status):
                res = client.get("/api/whatsapp/status", headers=auth)

        assert res.status_code == 200
        data = res.json()
        assert data["configurado"] is True
        assert len(data["conexoes"]) == 2
        assert data["alguma_conectada"] is True

    def test_contato_encontrado(self, client: TestClient, auth: dict):
        """Endpoint retorna contato quando encontrado no Deskrio."""
        contato_mock = {
            "id": 12345,
            "name": "Supermercado ABC",
            "number": "5541999999999",
            "extraInfo": [{"name": "CNPJ", "value": "12345678000100"}],
        }
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "buscar_contato_por_cnpj", return_value=contato_mock):
                res = client.get("/api/whatsapp/contato/12345678000100", headers=auth)

        assert res.status_code == 200
        data = res.json()
        assert data["encontrado"] is True
        assert data["numero"] == "5541999999999"
        assert data["nome"] == "Supermercado ABC"
        assert data["deskrio_id"] == 12345
        assert data["cnpj"] == "12345678000100"

    def test_enviar_com_contato_e_sucesso(self, client: TestClient, auth: dict):
        """Envio com contato encontrado e API Deskrio respondendo com sucesso."""
        contato_mock = {
            "id": 12345,
            "name": "Supermercado ABC",
            "number": "5541999999999",
        }
        envio_mock = {"id": "msg-abc-123", "status": "sent"}
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "buscar_contato_por_cnpj", return_value=contato_mock):
                with patch.object(svc, "enviar_mensagem", return_value=envio_mock):
                    res = client.post(
                        "/api/whatsapp/enviar",
                        json={
                            "cnpj": "12345678000100",
                            "mensagem": "Ola! Temos novidades para voce.",
                        },
                        headers=auth,
                    )

        assert res.status_code == 200
        data = res.json()
        assert data["enviado"] is True
        assert data["mensagem_id"] == "msg-abc-123"
        assert data["numero"] == "5541999999999"
        assert data["erro"] is None

    def test_enviar_contato_nao_encontrado(self, client: TestClient, auth: dict):
        """Envio retorna enviado=false quando contato nao existe no Deskrio."""
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "buscar_contato_por_cnpj", return_value=None):
                res = client.post(
                    "/api/whatsapp/enviar",
                    json={
                        "cnpj": "99988877000100",
                        "mensagem": "Mensagem de teste",
                    },
                    headers=auth,
                )

        assert res.status_code == 200
        data = res.json()
        assert data["enviado"] is False
        assert data["erro"] is not None
        assert "nao encontrado" in data["erro"].lower()

    def test_enviar_falha_api_deskrio(self, client: TestClient, auth: dict):
        """Envio retorna enviado=false quando Deskrio retorna None (erro HTTP)."""
        contato_mock = {
            "id": 1,
            "name": "Loja X",
            "number": "5541988888888",
        }
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "buscar_contato_por_cnpj", return_value=contato_mock):
                with patch.object(svc, "enviar_mensagem", return_value=None):
                    res = client.post(
                        "/api/whatsapp/enviar",
                        json={
                            "cnpj": "12345678000100",
                            "mensagem": "Mensagem que vai falhar",
                        },
                        headers=auth,
                    )

        assert res.status_code == 200
        data = res.json()
        assert data["enviado"] is False
        assert data["erro"] is not None

    def test_tickets_com_contato(self, client: TestClient, auth: dict):
        """Tickets retorna lista quando contato e encontrado."""
        contato_mock = {"id": 1, "number": "5541999999999"}
        tickets_mock = [
            {"id": 101, "status": "OPEN", "createdAt": "2026-03-20T10:00:00Z", "contactId": 1},
            {"id": 102, "status": "CLOSED", "createdAt": "2026-03-22T14:00:00Z", "contactId": 1},
        ]
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "buscar_contato_por_cnpj", return_value=contato_mock):
                with patch.object(svc, "listar_tickets", return_value=tickets_mock):
                    res = client.get(
                        "/api/whatsapp/tickets?cnpj=12345678000100&dias=7",
                        headers=auth,
                    )

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["tickets"]) == 2
        assert data["cnpj"] == "12345678000100"
        assert data["numero"] == "5541999999999"

    def test_conexoes_com_deskrio(self, client: TestClient, auth: dict):
        """Conexoes retorna lista quando Deskrio esta configurado."""
        conexoes_mock = [
            {"id": 1, "name": "Principal", "status": "CONNECTED"},
        ]
        from backend.app.services.deskrio_service import deskrio_service as svc
        with _patch_configurado(svc, True):
            with patch.object(svc, "listar_conexoes", return_value=conexoes_mock):
                res = client.get("/api/whatsapp/conexoes", headers=auth)

        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["nome"] == "Principal"
        assert data[0]["status"] == "CONNECTED"
        assert data[0]["status_legivel"] == "conectado"


# ---------------------------------------------------------------------------
# Testes: validacoes de payload
# ---------------------------------------------------------------------------

class TestValidacaoPayload:
    def test_enviar_mensagem_vazia_rejeitada(self, client: TestClient, auth: dict):
        """Mensagem vazia deve ser rejeitada com 422."""
        res = client.post(
            "/api/whatsapp/enviar",
            json={"cnpj": "12345678000100", "mensagem": ""},
            headers=auth,
        )
        assert res.status_code == 422

    def test_enviar_sem_cnpj_rejeitado(self, client: TestClient, auth: dict):
        """CNPJ ausente deve ser rejeitado com 422."""
        res = client.post(
            "/api/whatsapp/enviar",
            json={"mensagem": "Ola"},
            headers=auth,
        )
        assert res.status_code == 422

    def test_tickets_dias_invalido(self, client: TestClient, auth: dict):
        """Dias fora do range (0 ou >90) deve ser rejeitado com 422."""
        res = client.get(
            "/api/whatsapp/tickets?cnpj=12345678000100&dias=0",
            headers=auth,
        )
        assert res.status_code == 422

        res2 = client.get(
            "/api/whatsapp/tickets?cnpj=12345678000100&dias=91",
            headers=auth,
        )
        assert res2.status_code == 422


# ---------------------------------------------------------------------------
# Teste: R8 — Two-Base (nenhum valor monetario em payloads WA)
# ---------------------------------------------------------------------------

class TestTwoBase:
    def test_enviar_sem_valor_monetario(self, client: TestClient, auth: dict):
        """R10 — Two-Base: payload de envio nao deve conter campo de valor R$."""
        payload = {"cnpj": "12345678000100", "mensagem": "Ola cliente!"}
        # Verificar que o schema nao aceita campos de valor
        for campo_proibido in ("valor", "valor_pedido", "faturamento"):
            assert campo_proibido not in EnviarWhatsAppInput.model_fields

    def test_resposta_enviar_sem_valor_monetario(self, client: TestClient, auth: dict):
        """Resposta de envio nao deve conter campo de valor monetario."""
        res = client.post(
            "/api/whatsapp/enviar",
            json={"cnpj": "12345678000100", "mensagem": "Ola!"},
            headers=auth,
        )
        data = res.json()
        for campo in ("valor", "valor_pedido", "faturamento", "preco"):
            assert campo not in data


# Importar o schema para teste de Two-Base
from backend.app.api.routes_whatsapp import EnviarWhatsAppInput  # noqa: E402
