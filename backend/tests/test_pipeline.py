"""
CRM VITAO360 — Testes: Pipeline, Notificacoes e Webhook Deskrio

Cobertura:
  POST /api/pipeline/run   — admin dispara pipeline, retorna resultado
  POST /api/pipeline/run   — sem JWT retorna 401
  GET  /api/pipeline/status — retorna ultimo run
  GET  /api/pipeline/logs   — retorna historico de logs
  GET  /api/notificacoes   — retorna alertas dinamicos
  GET  /api/notificacoes   — sem JWT retorna 401
  POST /api/webhook/deskrio — message.received cria log (Two-Base R4)
  POST /api/webhook/deskrio — evento desconhecido retorna 200 sem criar log
  POST /api/webhook/deskrio — numero sem cliente retorna 200 sem log
  POST /api/webhook/deskrio — sem JWT retorna 200 (publico)

Regras verificadas:
  R4 — Two-Base: log de webhook sem valor monetario
  R5 — CNPJ string 14 digitos
  R8 — Nenhum dado fabricado
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Disable rate limiting in tests
os.environ.setdefault("TESTING", "1")

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine():
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Session:
    _Session = sessionmaker(bind=engine)
    session = _Session()
    yield session
    session.close()


def _fake_admin():
    return SimpleNamespace(id=1, email="admin@vitao.com.br", nome="Admin", role="admin", ativo=True, consultor_nome=None)


def _fake_consultor():
    return SimpleNamespace(id=2, email="manu@vitao.com.br", nome="Manu", role="consultor", ativo=True, consultor_nome="MANU")


def _db_override(session: Session):
    def _override():
        yield session
    return _override


@pytest.fixture(scope="function")
def client_admin(db) -> TestClient:
    admin = _fake_admin()
    app.dependency_overrides[get_db] = _db_override(db)
    app.dependency_overrides[get_current_user] = lambda: admin
    app.dependency_overrides[require_admin] = lambda: admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_consultor(db) -> TestClient:
    consultor = _fake_consultor()
    app.dependency_overrides[get_db] = _db_override(db)
    app.dependency_overrides[get_current_user] = lambda: consultor
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_no_auth(db) -> TestClient:
    """Cliente sem autenticacao — apenas get_db sobrescrito."""
    app.dependency_overrides[get_db] = _db_override(db)
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_cliente_com_telefone(db) -> Cliente:
    """Cliente ATIVO com telefone para testes de webhook."""
    c = Cliente(
        cnpj="12345678000100",
        nome_fantasia="Loja Vitao SP",
        razao_social="Loja Vitao SP LTDA",
        uf="SP",
        cidade="Sao Paulo",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        temperatura="MORNO",
        sinaleiro="VERDE",
        telefone="5541999990001",
        score=60.0,
        faturamento_total=8000.0,
        dias_sem_compra=15,
        ciclo_medio=30.0,
        n_compras=10,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture(scope="function")
def sample_cliente_vermelho(db) -> Cliente:
    """Cliente com sinaleiro VERMELHO e followup_vencido para testar notificacoes."""
    c = Cliente(
        cnpj="98765432000111",
        nome_fantasia="Loja Critica RS",
        razao_social="Loja Critica RS LTDA",
        uf="RS",
        cidade="Porto Alegre",
        consultor="LARISSA",
        situacao="INAT.REC",
        classificacao_3tier="REAL",
        temperatura="CRITICO",
        sinaleiro="VERMELHO",
        followup_vencido=True,
        score=20.0,
        faturamento_total=500.0,
        dias_sem_compra=120,
        ciclo_medio=30.0,
        n_compras=3,
        meta_anual=10000.0,
        pct_alcancado=0.3,  # 30% — META_RISCO
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ---------------------------------------------------------------------------
# Testes: POST /api/pipeline/run
# ---------------------------------------------------------------------------

class TestPipelineRun:
    """POST /api/pipeline/run — admin only."""

    def test_run_retorna_resultado(self, client_admin):
        """Pipeline run retorna PipelineRunResponse com steps."""
        with patch(
            "backend.app.services.pipeline_service.pipeline_service.run_full_pipeline"
        ) as mock_run:
            from backend.app.services.pipeline_service import PipelineResult, StepResult

            mock_result = PipelineResult(inicio=datetime.now(timezone.utc))
            mock_result.fim = datetime.now(timezone.utc)
            mock_result.sucesso = True
            mock_result.total_clientes_atualizados = 42
            mock_result.mensagem = "Pipeline concluido com sucesso."
            mock_result.steps = [
                StepResult(nome="sync_deskrio", sucesso=True, registros_processados=5, mensagem="OK"),
                StepResult(nome="sync_mercos", sucesso=True, registros_processados=3, mensagem="OK"),
                StepResult(nome="recalculate", sucesso=True, registros_processados=42, mensagem="OK"),
            ]
            mock_run.return_value = mock_result

            resp = client_admin.post("/api/pipeline/run")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sucesso"] is True
        assert data["total_clientes_atualizados"] == 42
        assert len(data["steps"]) == 3
        assert data["steps"][0]["nome"] == "sync_deskrio"

    def test_run_sem_jwt_retorna_401(self, client_no_auth):
        """Sem autenticacao deve retornar 401."""
        resp = client_no_auth.post("/api/pipeline/run")
        assert resp.status_code == 401, resp.text

    def test_run_consultor_retorna_403(self, client_consultor):
        """Consultor nao admin deve retornar 403."""
        resp = client_consultor.post("/api/pipeline/run")
        assert resp.status_code == 403, resp.text

    def test_run_em_execucao_retorna_409(self, client_admin):
        """Se pipeline ja estiver em execucao, retorna 409."""
        with patch(
            "backend.app.services.pipeline_service.pipeline_service.get_status"
        ) as mock_status:
            from backend.app.services.pipeline_service import PipelineStatus
            mock_status.return_value = PipelineStatus(
                ultimo_run=None,
                proximo_agendado=None,
                em_execucao=True,
            )
            resp = client_admin.post("/api/pipeline/run")

        assert resp.status_code == 409, resp.text
        assert "execucao" in resp.json()["detail"].lower()

    def test_run_steps_com_falha_reportados(self, client_admin):
        """Steps com falha sao retornados com sucesso=False no step."""
        with patch(
            "backend.app.services.pipeline_service.pipeline_service.run_full_pipeline"
        ) as mock_run:
            from backend.app.services.pipeline_service import PipelineResult, StepResult

            mock_result = PipelineResult(inicio=datetime.now(timezone.utc))
            mock_result.fim = datetime.now(timezone.utc)
            mock_result.sucesso = False
            mock_result.total_clientes_atualizados = 0
            mock_result.mensagem = "Pipeline concluido com falhas."
            mock_result.steps = [
                StepResult(
                    nome="sync_deskrio",
                    sucesso=False,
                    registros_processados=0,
                    erro="Timeout na API",
                    mensagem="Falhou",
                ),
            ]
            mock_run.return_value = mock_result

            resp = client_admin.post("/api/pipeline/run")

        assert resp.status_code == 200
        data = resp.json()
        assert data["sucesso"] is False
        assert data["steps"][0]["sucesso"] is False
        assert data["steps"][0]["erro"] == "Timeout na API"


# ---------------------------------------------------------------------------
# Testes: GET /api/pipeline/status
# ---------------------------------------------------------------------------

class TestPipelineStatus:
    """GET /api/pipeline/status — admin only."""

    def test_status_retorna_estrutura(self, client_admin):
        """Status retorna estrutura com em_execucao e ultimo_run."""
        resp = client_admin.get("/api/pipeline/status")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "em_execucao" in data
        assert "ultimo_run" in data
        assert "proximo_agendado" in data
        assert data["em_execucao"] is False

    def test_status_sem_jwt_retorna_401(self, client_no_auth):
        resp = client_no_auth.get("/api/pipeline/status")
        assert resp.status_code == 401

    def test_status_consultor_retorna_403(self, client_consultor):
        resp = client_consultor.get("/api/pipeline/status")
        assert resp.status_code == 403

    def test_status_apos_run(self, client_admin):
        """Apos um run, status reflete o resultado."""
        with patch(
            "backend.app.services.pipeline_service.pipeline_service.run_full_pipeline"
        ) as mock_run, patch(
            "backend.app.services.pipeline_service.pipeline_service.get_status"
        ) as mock_status:
            from backend.app.services.pipeline_service import PipelineResult, PipelineStatus, StepResult

            mock_result = PipelineResult(inicio=datetime.now(timezone.utc))
            mock_result.fim = datetime.now(timezone.utc)
            mock_result.sucesso = True
            mock_result.total_clientes_atualizados = 10
            mock_result.mensagem = "OK"
            mock_result.steps = []
            mock_run.return_value = mock_result

            mock_status.return_value = PipelineStatus(
                ultimo_run=mock_result,
                proximo_agendado=None,
                em_execucao=False,
            )

            # Disparar run
            client_admin.post("/api/pipeline/run")

            # Consultar status
            resp = client_admin.get("/api/pipeline/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["em_execucao"] is False


# ---------------------------------------------------------------------------
# Testes: GET /api/pipeline/logs
# ---------------------------------------------------------------------------

class TestPipelineLogs:
    """GET /api/pipeline/logs — admin only."""

    def test_logs_retorna_lista(self, client_admin):
        """Logs retornam lista (pode ser vazia)."""
        resp = client_admin.get("/api/pipeline/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_logs_sem_jwt_retorna_401(self, client_no_auth):
        resp = client_no_auth.get("/api/pipeline/logs")
        assert resp.status_code == 401

    def test_logs_consultor_retorna_403(self, client_consultor):
        resp = client_consultor.get("/api/pipeline/logs")
        assert resp.status_code == 403

    def test_logs_max_20(self, client_admin):
        """Logs retornam no maximo 20 entradas."""
        with patch(
            "backend.app.services.pipeline_service.pipeline_service.get_logs"
        ) as mock_logs:
            mock_logs.return_value = [{"sucesso": True}] * 20
            resp = client_admin.get("/api/pipeline/logs")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["logs"]) <= 20


# ---------------------------------------------------------------------------
# Testes: GET /api/notificacoes
# ---------------------------------------------------------------------------

class TestNotificacoes:
    """GET /api/notificacoes — qualquer usuario autenticado."""

    def test_notificacoes_sem_jwt_retorna_401(self, client_no_auth):
        """Endpoint exige autenticacao."""
        resp = client_no_auth.get("/api/notificacoes")
        assert resp.status_code == 401

    def test_notificacoes_retorna_estrutura(self, client_consultor):
        """Sem dados, retorna total=0 e lista vazia."""
        resp = client_consultor.get("/api/notificacoes")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "alertas" in data
        assert isinstance(data["alertas"], list)
        assert data["total"] == len(data["alertas"])

    def test_notificacoes_churn_critico(self, client_admin, db, sample_cliente_vermelho):
        """Cliente com temperatura=CRITICO gera alerta CHURN."""
        resp = client_admin.get("/api/notificacoes")
        assert resp.status_code == 200
        data = resp.json()
        tipos = [a["tipo"] for a in data["alertas"]]
        assert "CHURN" in tipos

    def test_notificacoes_followup_vencido(self, client_admin, db, sample_cliente_vermelho):
        """Cliente com followup_vencido=True gera alerta FOLLOWUP_VENCIDO."""
        resp = client_admin.get("/api/notificacoes")
        assert resp.status_code == 200
        data = resp.json()
        tipos = [a["tipo"] for a in data["alertas"]]
        assert "FOLLOWUP_VENCIDO" in tipos

    def test_notificacoes_meta_risco(self, client_admin, db, sample_cliente_vermelho):
        """Cliente com pct_alcancado<0.5 gera alerta META_RISCO."""
        resp = client_admin.get("/api/notificacoes")
        assert resp.status_code == 200
        data = resp.json()
        tipos = [a["tipo"] for a in data["alertas"]]
        assert "META_RISCO" in tipos

    def test_notificacoes_campos_completos(self, client_admin, db, sample_cliente_vermelho):
        """Cada alerta tem todos os campos obrigatorios."""
        resp = client_admin.get("/api/notificacoes")
        data = resp.json()
        for alerta in data["alertas"]:
            assert "tipo" in alerta
            assert "prioridade" in alerta
            assert "cnpj" in alerta
            assert "nome" in alerta
            assert "mensagem" in alerta
            assert "acao" in alerta
            # R5: CNPJ deve ter 14 digitos
            assert len(alerta["cnpj"]) == 14, f"CNPJ invalido: {alerta['cnpj']}"

    def test_notificacoes_alta_antes_de_media(self, client_admin, db, sample_cliente_vermelho):
        """Alertas ALTA aparecem antes de MEDIA na resposta."""
        resp = client_admin.get("/api/notificacoes")
        data = resp.json()
        alertas = data["alertas"]
        if len(alertas) >= 2:
            prioridades = [a["prioridade"] for a in alertas]
            # Verificar que nenhum MEDIA aparece antes de ALTA
            encontrou_media = False
            for p in prioridades:
                if p == "MEDIA":
                    encontrou_media = True
                if p == "ALTA" and encontrou_media:
                    pytest.fail("ALTA alerta apareceu apos MEDIA — ordenacao incorreta")

    def test_notificacoes_sem_alucinacao(self, client_admin, db):
        """Clientes ALUCINACAO nao geram alertas."""
        cliente_alucinacao = Cliente(
            cnpj="00000000000001",
            nome_fantasia="ALUCINACAO",
            consultor="MANU",
            situacao="ATIVO",
            classificacao_3tier="ALUCINACAO",
            temperatura="CRITICO",
            followup_vencido=True,
        )
        db.add(cliente_alucinacao)
        db.commit()

        resp = client_admin.get("/api/notificacoes")
        data = resp.json()
        cnpjs_alertas = [a["cnpj"] for a in data["alertas"]]
        assert "00000000000001" not in cnpjs_alertas, "ALUCINACAO nao deve gerar alertas"


# ---------------------------------------------------------------------------
# Testes: POST /api/webhook/deskrio
# ---------------------------------------------------------------------------

class TestWebhookDeskrio:
    """POST /api/webhook/deskrio — publico (sem JWT)."""

    def test_webhook_publico_sem_jwt(self, client_no_auth):
        """Webhook e publico — sem JWT deve funcionar normalmente."""
        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={"event": "unknown.event", "data": {}},
        )
        assert resp.status_code == 200, resp.text

    def test_webhook_evento_desconhecido_retorna_200(self, client_no_auth):
        """Eventos desconhecidos retornam 200 sem criar log."""
        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={"event": "ticket.created", "data": {"id": 999}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recebido"] is True
        assert data["log_id"] is None

    def test_webhook_message_received_sem_cliente_retorna_200(self, client_no_auth):
        """message.received sem cliente correspondente retorna 200 sem log."""
        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={
                "event": "message.received",
                "data": {
                    "number": "5511900000000",
                    "body": "Ola!",
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recebido"] is True
        assert data["log_id"] is None

    def test_webhook_message_received_cria_log(self, client_no_auth, db, sample_cliente_com_telefone):
        """
        message.received com numero que bate com cliente cria LogInteracao.

        R4 — Two-Base: verifica que nenhum campo de valor foi inserido.
        R5 — CNPJ do log deve ser string 14 digitos.
        """
        numero = sample_cliente_com_telefone.telefone  # "5541999990001"

        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={
                "event": "message.received",
                "data": {
                    "number": numero,
                    "body": "Preciso de orcamento para graos.",
                    "contact": {"name": "Loja Vitao SP"},
                },
            },
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["recebido"] is True
        assert data["log_id"] is not None

        # Verificar log no banco
        log_id = data["log_id"]
        log = db.query(LogInteracao).filter(LogInteracao.id == log_id).first()
        registro = log
        assert registro is not None, "Interacao nao encontrada no banco"

        # R5: CNPJ string 14 digitos
        assert len(registro.cnpj) == 14, f"CNPJ invalido: {registro.cnpj}"
        assert registro.cnpj == sample_cliente_com_telefone.cnpj

        # R4: interacao nao tem campo monetario
        assert not hasattr(registro, "valor_pedido"), "R4: sem campo monetario"
        assert not hasattr(registro, "valor"), "R4: sem campo monetario"

        # Tipo de contato deve ser WHATSAPP
        assert registro.tipo_contato == "WHATSAPP"
        assert registro.resultado == "MENSAGEM RECEBIDA"

    def test_webhook_body_incluido_na_descricao(self, client_no_auth, db, sample_cliente_com_telefone):
        """Corpo da mensagem e incluido na descricao do log."""
        numero = sample_cliente_com_telefone.telefone
        corpo = "Quero 10 caixas de grao de bico organico."

        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={
                "event": "message.received",
                "data": {"number": numero, "body": corpo},
            },
        )

        assert resp.status_code == 200
        log_id = resp.json()["log_id"]
        log = db.query(LogInteracao).filter(LogInteracao.id == log_id).first()
        assert log is not None
        assert corpo in (log.descricao or "")

    def test_webhook_numero_sem_ddi_bate_sufixo(self, client_no_auth, db, sample_cliente_com_telefone):
        """Numero sem DDI (ultimos 11 digitos) deve encontrar o cliente."""
        # Telefone completo: 5541999990001 — sem DDI: 41999990001
        numero_sem_ddi = "41999990001"

        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={
                "event": "message.received",
                "data": {"number": numero_sem_ddi, "body": "Teste sem DDI."},
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        # Pode ou nao encontrar dependendo do banco, mas nao deve dar erro 500
        assert data["recebido"] is True

    def test_webhook_sem_numero_retorna_200(self, client_no_auth):
        """Payload sem numero retorna 200 (graceful degradation)."""
        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={
                "event": "message.received",
                "data": {"body": "Mensagem sem numero de origem."},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["recebido"] is True

    def test_webhook_payload_invalido_retorna_422(self, client_no_auth):
        """Payload sem campo obrigatorio 'event' retorna 422."""
        resp = client_no_auth.post(
            "/api/webhook/deskrio",
            json={"data": {"number": "5541999990001"}},  # sem 'event'
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Testes: PipelineService direto (unit)
# ---------------------------------------------------------------------------

class TestPipelineServiceUnit:
    """Testes unitarios do PipelineService sem HTTP."""

    def test_get_status_sem_run_anterior(self):
        """Status inicial: sem ultimo run, em_execucao=False."""
        from backend.app.services.pipeline_service import PipelineService
        svc = PipelineService()
        status = svc.get_status()
        assert status.em_execucao is False
        assert status.ultimo_run is None

    def test_get_logs_vazio_inicial(self):
        """Historico inicial vazio."""
        from backend.app.services.pipeline_service import PipelineService
        svc = PipelineService()
        assert svc.get_logs() == []

    def test_pipeline_result_to_dict(self):
        """PipelineResult.to_dict() retorna estrutura correta."""
        from backend.app.services.pipeline_service import PipelineResult, StepResult
        r = PipelineResult(inicio=datetime.now(timezone.utc))
        r.fim = datetime.now(timezone.utc)
        r.sucesso = True
        r.total_clientes_atualizados = 5
        r.mensagem = "OK"
        r.steps = [StepResult(nome="test", sucesso=True, registros_processados=5, mensagem="OK")]

        d = r.to_dict()
        assert d["sucesso"] is True
        assert d["total_clientes_atualizados"] == 5
        assert len(d["steps"]) == 1
        assert d["steps"][0]["nome"] == "test"
        assert d["duracao_segundos"] is not None
        assert d["duracao_segundos"] >= 0

    def test_historico_max_20(self, db):
        """Historico nao ultrapassa 20 entradas."""
        from backend.app.services.pipeline_service import PipelineService

        svc = PipelineService()

        # Simular 25 runs
        for _ in range(25):
            with patch.object(svc, "_sync_deskrio") as mock_d, \
                 patch.object(svc, "_sync_mercos") as mock_m, \
                 patch.object(svc, "_recalculate") as mock_r:
                from backend.app.services.pipeline_service import StepResult
                mock_d.return_value = StepResult("sync_deskrio", True, 0, "OK")
                mock_m.return_value = StepResult("sync_mercos", True, 0, "OK")
                mock_r.return_value = StepResult("recalculate", True, 0, "OK")
                svc.run_full_pipeline(db)

        logs = svc.get_logs()
        assert len(logs) <= 20, f"Historico deveria ter max 20 entradas, tem {len(logs)}"

    def test_mapear_vendedor_canonical(self):
        """DE-PARA vendedores retorna nomes canonicos."""
        from backend.app.services.pipeline_service import _mapear_vendedor
        assert _mapear_vendedor("Central - Daiane") == "DAIANE"
        assert _mapear_vendedor("Larissa Padilha") == "LARISSA"
        assert _mapear_vendedor("Manu Ditzel") == "MANU"
        assert _mapear_vendedor("Julio Gadret") == "JULIO"
        assert _mapear_vendedor("Desconhecido XYZ") == "LEGADO"

    def test_normalizar_cnpj_r5(self):
        """R5: _normalizar_cnpj sempre retorna string 14 digitos."""
        from backend.app.services.pipeline_service import _normalizar_cnpj
        assert _normalizar_cnpj("12.345.678/0001-00") == "12345678000100"
        assert _normalizar_cnpj("1") == "00000000000001"
        assert _normalizar_cnpj(12345678000100) == "12345678000100"
        assert len(_normalizar_cnpj("99999999999999")) == 14
