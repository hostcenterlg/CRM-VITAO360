"""
CRM VITAO360 — Testes de Cache, Paginação e Bulk Operations.

Cobre:
  1. Cache (InMemoryCache + decorador @cached):
     - TTL: entrada expira após N segundos
     - Invalidação: invalidate(), invalidate_prefix(), clear()
     - Concorrência: múltiplas threads lendo/escrevendo sem corrida
     - Miss e hit retornam corretamente

  2. Paginação (PaginationParams + PaginatedResponse):
     - page/per_page padrão
     - Backward compat com limit/offset
     - Limites e bordas (page=1, last page, total=0)
     - GET /api/clientes com page/per_page e com limit/offset
     - GET /api/vendas com page/per_page

  3. Bulk Operations:
     - POST /api/clientes/bulk-update: campos válidos, CNPJ inválido, admin only
     - POST /api/atendimentos/bulk: Two-Base (R$ 0.00), max 50, resultado inválido

R4 — Two-Base: atendimentos em bulk NUNCA têm valor monetário.
R5 — CNPJ: String(14), zero-padded, nunca float.
"""

from __future__ import annotations

import math
import threading
import time
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.api.deps import (
    get_current_user,
    require_admin,
    require_admin_or_gerente,
    require_consultor_or_admin,
)
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.regra_motor import RegraMotor
from backend.app.models.venda import Venda
from backend.app.schemas.pagination import PaginationParams, PaginatedResponse
from backend.app.utils.cache import InMemoryCache, cache, make_cache_key


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _db_override(session):
    def _override():
        yield session
    return _override


def _make_fake_user(
    id: int = 1,
    email: str = "admin@vitao.com.br",
    nome: str = "Admin Vitao",
    role: str = "admin",
    consultor_nome=None,
    ativo: bool = True,
):
    return SimpleNamespace(
        id=id, email=email, nome=nome, role=role,
        consultor_nome=consultor_nome, ativo=ativo,
        hashed_password="hashed_fake",
    )


def _make_admin_client(db_session):
    """Cria TestClient com role=admin e sessão in-memory."""
    fake = _make_fake_user()
    app.dependency_overrides[get_db] = _db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: fake
    app.dependency_overrides[require_admin] = lambda: fake
    app.dependency_overrides[require_admin_or_gerente] = lambda: fake
    app.dependency_overrides[require_consultor_or_admin] = lambda: fake
    return TestClient(app, raise_server_exceptions=True)


def _make_consultor_client(db_session, consultor_nome="MANU"):
    """Cria TestClient com role=consultor e sessão in-memory."""
    fake = _make_fake_user(id=2, email="manu@vitao.com.br", role="consultor", consultor_nome=consultor_nome)
    app.dependency_overrides[get_db] = _db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: fake
    return TestClient(app, raise_server_exceptions=False)


def _seed_regras(db_session):
    """Seed mínimo de RegraMotor para o Motor de Regras funcionar."""
    regras = [
        RegraMotor(
            situacao="ATIVO",
            resultado="RELACIONAMENTO",
            estagio_funil="ATIVO",
            fase="MANUTENCAO",
            tipo_contato="LIGACAO",
            acao_futura="Ligar novamente",
            temperatura="MORNO",
            follow_up_dias=7,
            grupo_dash="RELAC.",
            tipo_acao="ATENDIMENTO",
            chave="ATIVO|RELACIONAMENTO",
        ),
        RegraMotor(
            situacao="PROSPECT",
            resultado="NÃO ATENDE",
            estagio_funil="PROSPECCAO",
            fase="AQUISICAO",
            tipo_contato="LIGACAO",
            acao_futura="Tentar de novo",
            temperatura="FRIO",
            follow_up_dias=1,
            grupo_dash="NÃO VENDA",
            tipo_acao="ATENDIMENTO",
            chave="PROSPECT|NÃO ATENDE",
        ),
    ]
    db_session.add_all(regras)
    db_session.commit()


# ---------------------------------------------------------------------------
# PARTE 1 — TESTES DE CACHE
# ---------------------------------------------------------------------------

class TestInMemoryCache:
    """Testes unitários do InMemoryCache (sem FastAPI)."""

    def test_miss_retorna_false_none(self):
        c = InMemoryCache()
        hit, val = c.get("chave_inexistente")
        assert hit is False
        assert val is None

    def test_set_e_get_hit(self):
        c = InMemoryCache()
        c.set("k1", {"dados": 42}, ttl_seconds=60)
        hit, val = c.get("k1")
        assert hit is True
        assert val == {"dados": 42}

    def test_ttl_expira(self):
        c = InMemoryCache()
        c.set("k_ttl", "valor", ttl_seconds=0.05)  # 50ms
        hit, _ = c.get("k_ttl")
        assert hit is True  # ainda válido

        time.sleep(0.1)  # esperar expirar
        hit, val = c.get("k_ttl")
        assert hit is False
        assert val is None

    def test_ttl_expira_remove_do_store(self):
        """Lazy expiry deve remover a entrada do store ao detectar expiração."""
        c = InMemoryCache()
        c.set("k_lazy", "x", ttl_seconds=0.05)
        time.sleep(0.1)
        c.get("k_lazy")  # deve remover
        assert c.size() == 0

    def test_set_substitui_entrada_existente(self):
        c = InMemoryCache()
        c.set("k", "v1", ttl_seconds=60)
        c.set("k", "v2", ttl_seconds=60)
        hit, val = c.get("k")
        assert hit is True
        assert val == "v2"

    def test_invalidate_chave_existente(self):
        c = InMemoryCache()
        c.set("k_del", "v", ttl_seconds=60)
        result = c.invalidate("k_del")
        assert result is True
        hit, _ = c.get("k_del")
        assert hit is False

    def test_invalidate_chave_inexistente(self):
        c = InMemoryCache()
        result = c.invalidate("nao_existe")
        assert result is False

    def test_invalidate_prefix(self):
        c = InMemoryCache()
        c.set("/api/dashboard/kpis", 1, ttl_seconds=60)
        c.set("/api/dashboard/distribuicao", 2, ttl_seconds=60)
        c.set("/api/sinaleiro", 3, ttl_seconds=60)

        removed = c.invalidate_prefix("/api/dashboard")
        assert removed == 2

        # Dashboard removido
        hit1, _ = c.get("/api/dashboard/kpis")
        hit2, _ = c.get("/api/dashboard/distribuicao")
        assert hit1 is False
        assert hit2 is False

        # Sinaleiro intacto
        hit3, val3 = c.get("/api/sinaleiro")
        assert hit3 is True
        assert val3 == 3

    def test_clear_remove_tudo(self):
        c = InMemoryCache()
        c.set("a", 1, ttl_seconds=60)
        c.set("b", 2, ttl_seconds=60)
        c.set("c", 3, ttl_seconds=60)

        count = c.clear()
        assert count == 3
        assert c.size() == 0

    def test_stats(self):
        c = InMemoryCache()
        c.set("v1", 1, ttl_seconds=60)
        c.set("v2", 2, ttl_seconds=0.01)
        time.sleep(0.05)

        stats = c.stats()
        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 1
        assert stats["expired_entries"] == 1

    def test_make_cache_key_sem_params(self):
        key = make_cache_key("/api/dashboard/kpis")
        assert key == "/api/dashboard/kpis"

    def test_make_cache_key_com_params(self):
        key1 = make_cache_key("/api/clientes", {"consultor": "MANU", "page": 1})
        key2 = make_cache_key("/api/clientes", {"consultor": "LARISSA", "page": 1})
        key3 = make_cache_key("/api/clientes", {"consultor": "MANU", "page": 1})

        # Parâmetros diferentes → chaves diferentes
        assert key1 != key2
        # Mesmos parâmetros → mesma chave (determinístico)
        assert key1 == key3

    def test_concorrencia_thread_safe(self):
        """
        Múltiplas threads lendo e escrevendo simultaneamente não devem causar
        corridas de dados ou exceções.
        """
        c = InMemoryCache()
        erros: list[Exception] = []

        def writer(chave_base: str, n: int):
            for i in range(n):
                try:
                    c.set(f"{chave_base}:{i}", i, ttl_seconds=10)
                except Exception as exc:
                    erros.append(exc)

        def reader(chave_base: str, n: int):
            for i in range(n):
                try:
                    c.get(f"{chave_base}:{i}")
                except Exception as exc:
                    erros.append(exc)

        def invalidator(prefix: str):
            for _ in range(5):
                try:
                    c.invalidate_prefix(prefix)
                    time.sleep(0.001)
                except Exception as exc:
                    erros.append(exc)

        threads = [
            threading.Thread(target=writer, args=("thread_a", 100)),
            threading.Thread(target=writer, args=("thread_b", 100)),
            threading.Thread(target=reader, args=("thread_a", 50)),
            threading.Thread(target=invalidator, args=("thread_a",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert erros == [], f"Erros de concorrencia: {erros}"


# ---------------------------------------------------------------------------
# PARTE 2 — TESTES DE PAGINAÇÃO
# ---------------------------------------------------------------------------

class TestPaginationParams:
    """Testes unitários de PaginationParams."""

    def test_defaults(self):
        p = PaginationParams()
        assert p.page == 1
        assert p.per_page == 50
        assert p.offset == 0
        assert p.limit == 50

    def test_offset_calculado(self):
        p = PaginationParams(page=3, per_page=25)
        assert p.offset == 50  # (3-1) * 25

    def test_from_limit_offset_legado(self):
        p = PaginationParams.from_limit_offset(limit=25, offset=50)
        assert p.per_page == 25
        assert p.page == 3  # 50 // 25 + 1

    def test_from_limit_offset_page_tem_precedencia(self):
        p = PaginationParams.from_limit_offset(
            limit=50, offset=100,
            page=2, per_page=20,
        )
        assert p.page == 2
        assert p.per_page == 20

    def test_per_page_max_200(self):
        with pytest.raises(Exception):
            PaginationParams(page=1, per_page=201)

    def test_page_ge_1(self):
        with pytest.raises(Exception):
            PaginationParams(page=0, per_page=50)

    def test_from_limit_offset_caps_per_page(self):
        """limit > 200 é arredondado para 200 no from_limit_offset."""
        p = PaginationParams.from_limit_offset(limit=500, offset=0)
        assert p.per_page == 200  # min(500, 200)


class TestPaginatedResponse:
    """Testes unitários de PaginatedResponse.build."""

    def test_build_pagina_1(self):
        params = PaginationParams(page=1, per_page=10)
        resp = PaginatedResponse.build(items=list(range(10)), total=35, params=params)
        assert resp.page == 1
        assert resp.per_page == 10
        assert resp.total == 35
        assert resp.pages == 4  # ceil(35/10)
        assert resp.has_next is True
        assert resp.has_prev is False

    def test_build_ultima_pagina(self):
        params = PaginationParams(page=4, per_page=10)
        resp = PaginatedResponse.build(items=[35], total=35, params=params)
        assert resp.has_next is False
        assert resp.has_prev is True

    def test_build_total_zero(self):
        params = PaginationParams(page=1, per_page=50)
        resp = PaginatedResponse.build(items=[], total=0, params=params)
        assert resp.total == 0
        assert resp.pages == 1  # mínimo 1
        assert resp.has_next is False
        assert resp.has_prev is False

    def test_build_pagina_unica(self):
        params = PaginationParams(page=1, per_page=50)
        resp = PaginatedResponse.build(items=list(range(10)), total=10, params=params)
        assert resp.pages == 1
        assert resp.has_next is False
        assert resp.has_prev is False


# ---------------------------------------------------------------------------
# PARTE 2b — TESTES DE PAGINAÇÃO via API (integração)
# ---------------------------------------------------------------------------

class TestPaginacaoClientesAPI:
    """Testes de integração da paginação em GET /api/clientes."""

    @pytest.fixture(autouse=True)
    def setup(self, engine, db):
        """Seed 5 clientes para testar paginação."""
        self.db = db
        for i in range(5):
            c = Cliente(
                cnpj=f"1234567800{i:04d}",
                nome_fantasia=f"Cliente {i}",
                situacao="ATIVO",
                consultor="MANU",
                classificacao_3tier="REAL",
            )
            db.add(c)
        db.commit()
        self.client = _make_admin_client(db)
        yield
        app.dependency_overrides.clear()

    def test_listagem_padrao_tem_campos_paginacao(self):
        resp = self.client.get("/api/clientes")
        assert resp.status_code == 200
        data = resp.json()
        # Campos novos presentes
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert "has_next" in data
        assert "has_prev" in data
        # Campos legados ainda presentes (backward compat)
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "registros" in data

    def test_page_per_page(self):
        resp = self.client.get("/api/clientes?page=1&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["registros"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["total"] == 5
        assert data["pages"] == 3  # ceil(5/2)
        assert data["has_next"] is True
        assert data["has_prev"] is False

    def test_page_2(self):
        resp = self.client.get("/api/clientes?page=2&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["registros"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is True

    def test_ultima_pagina(self):
        resp = self.client.get("/api/clientes?page=3&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["registros"]) == 1  # sobrou 1
        assert data["has_next"] is False
        assert data["has_prev"] is True

    def test_backward_compat_limit_offset(self):
        """Clientes existentes que usam limit/offset ainda funcionam."""
        resp = self.client.get("/api/clientes?limit=2&offset=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["registros"]) == 2
        # limit/offset legados presentes
        assert data["limit"] == 2
        assert data["offset"] == 2

    def test_page_per_page_tem_precedencia_sobre_limit_offset(self):
        """Se ambos informados, page/per_page tem precedência."""
        resp = self.client.get("/api/clientes?page=1&per_page=3&limit=100&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["per_page"] == 3
        assert len(data["registros"]) == 3

    def test_per_page_max_200(self):
        """per_page > 200 deve ser rejeitado com 422."""
        resp = self.client.get("/api/clientes?per_page=201")
        assert resp.status_code == 422

    def test_pagina_vazia_total_zero(self):
        """Página sem resultados retorna items vazio mas mantém estrutura."""
        resp = self.client.get("/api/clientes?page=99&per_page=50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["registros"] == []
        assert data["total"] == 5


class TestPaginacaoVendasAPI:
    """Testes de integração da paginação em GET /api/vendas."""

    @pytest.fixture(autouse=True)
    def setup(self, engine, db):
        self.db = db
        # Seed cliente + 3 vendas
        c = Cliente(
            cnpj="12345678000199",
            nome_fantasia="Loja Teste",
            situacao="ATIVO",
            consultor="MANU",
            classificacao_3tier="REAL",
        )
        db.add(c)
        db.flush()
        for i in range(3):
            v = Venda(
                cnpj="12345678000199",
                data_pedido=date(2026, 1, i + 1),
                numero_pedido=f"PED-{i:03d}",
                valor_pedido=100.0 + i,
                consultor="MANU",
                fonte="MERCOS",
                classificacao_3tier="REAL",
                mes_referencia="2026-01",
            )
            db.add(v)
        db.commit()
        self.client = _make_admin_client(db)
        yield
        app.dependency_overrides.clear()

    def test_listar_vendas_retorna_paginado(self):
        resp = self.client.get("/api/vendas")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data
        assert "has_next" in data
        assert "has_prev" in data

    def test_vendas_page_per_page(self):
        resp = self.client.get("/api/vendas?page=1&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2
        assert data["has_next"] is True

    def test_vendas_pagina_2(self):
        resp = self.client.get("/api/vendas?page=2&per_page=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["has_next"] is False
        assert data["has_prev"] is True

    def test_vendas_backward_compat_limit_offset(self):
        """limit/offset ainda funciona e retorna dados corretos."""
        resp = self.client.get("/api/vendas?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2

    def test_vendas_per_page_max(self):
        resp = self.client.get("/api/vendas?per_page=201")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PARTE 3 — TESTES DE BULK OPERATIONS
# ---------------------------------------------------------------------------

class TestBulkUpdateClientes:
    """Testes de integração de POST /api/clientes/bulk-update."""

    @pytest.fixture(autouse=True)
    def setup(self, engine, db):
        self.db = db
        # Seed 3 clientes com consultor MANU
        for i in range(3):
            c = Cliente(
                cnpj=f"1111111100{i:04d}",
                nome_fantasia=f"Bulk Cliente {i}",
                situacao="ATIVO",
                consultor="MANU",
                classificacao_3tier="REAL",
            )
            db.add(c)
        db.commit()
        self.client = _make_admin_client(db)
        yield
        app.dependency_overrides.clear()

    def test_bulk_update_consultor(self):
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["11111111000000", "11111111000001"],
                "updates": {"consultor": "LARISSA"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_recebidos"] == 2
        assert data["total_atualizados"] == 2
        assert data["erros"] == []

        # Verificar que o banco foi atualizado
        from sqlalchemy import select as _select
        c = self.db.scalar(_select(Cliente).where(Cliente.cnpj == "11111111000000"))
        assert c.consultor == "LARISSA"

    def test_bulk_update_multiplos_campos(self):
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["11111111000000"],
                "updates": {"cidade": "Joinville", "uf": "SC"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_atualizados"] == 1

    def test_bulk_update_cnpj_inexistente_vira_erro(self):
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["99999999000099"],
                "updates": {"situacao": "ATIVO"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_atualizados"] == 0
        assert len(data["erros"]) == 1
        assert "99999999000099" in data["erros"][0]

    def test_bulk_update_campo_invalido_rejeitado(self):
        """Campos não permitidos (ex.: faturamento_total) devem retornar 422."""
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["11111111000000"],
                "updates": {"faturamento_total": "9999999"},  # campo proibido
            },
        )
        assert resp.status_code == 422

    def test_bulk_update_cnpjs_vazio_rejeitado(self):
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={"cnpjs": [], "updates": {"consultor": "MANU"}},
        )
        assert resp.status_code == 422

    def test_bulk_update_updates_vazio_rejeitado(self):
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={"cnpjs": ["11111111000000"], "updates": {}},
        )
        assert resp.status_code == 422

    def test_bulk_update_requer_admin(self):
        """Consultor não pode executar bulk-update (403)."""
        # Limpar overrides do admin e configurar como consultor (sem bypass de require_admin)
        app.dependency_overrides.clear()
        fake_consultor = _make_fake_user(
            id=2, email="manu@vitao.com.br", role="consultor", consultor_nome="MANU"
        )
        app.dependency_overrides[get_db] = _db_override(self.db)
        app.dependency_overrides[get_current_user] = lambda: fake_consultor
        # NÃO sobrescrever require_admin — deve retornar 403
        consultor_only_client = TestClient(app, raise_server_exceptions=False)
        resp = consultor_only_client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["11111111000000"],
                "updates": {"consultor": "LARISSA"},
            },
        )
        assert resp.status_code == 403
        # Restaurar admin client para os próximos testes do fixture
        self.client = _make_admin_client(self.db)

    def test_bulk_update_max_200_cnpjs(self):
        """Mais de 200 CNPJs deve retornar 422."""
        cnpjs = [f"1234{i:010d}" for i in range(201)]
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={"cnpjs": cnpjs, "updates": {"situacao": "ATIVO"}},
        )
        assert resp.status_code == 422

    def test_bulk_update_sem_mudanca_real_nao_conta(self):
        """Quando consultor já é MANU, não deve contar como atualizado."""
        resp = self.client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["11111111000000"],
                "updates": {"consultor": "MANU"},  # já é MANU
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # total_atualizados == 0 porque não houve mudança real
        assert data["total_atualizados"] == 0

    def test_bulk_update_gera_audit_log(self):
        """Cada campo alterado deve gerar registro em audit_logs."""
        self.client.post(
            "/api/clientes/bulk-update",
            json={
                "cnpjs": ["11111111000000"],
                "updates": {"consultor": "LARISSA"},
            },
        )
        from backend.app.models.audit_log import AuditLog
        from sqlalchemy import select as _select
        logs = self.db.scalars(
            _select(AuditLog).where(
                AuditLog.cnpj == "11111111000000",
                AuditLog.campo == "consultor",
            )
        ).all()
        assert len(logs) >= 1
        assert logs[-1].valor_novo == "LARISSA"
        assert logs[-1].valor_anterior == "MANU"


class TestBulkAtendimentos:
    """Testes de integração de POST /api/atendimentos/bulk."""

    @pytest.fixture(autouse=True)
    def setup(self, engine, db):
        self.db = db
        # Seed cliente ATIVO
        c = Cliente(
            cnpj="22222222000100",
            nome_fantasia="Bulk Atend Cliente",
            situacao="ATIVO",
            consultor="MANU",
            classificacao_3tier="REAL",
        )
        db.add(c)
        # Seed regras do motor
        _seed_regras(db)
        self.client = _make_admin_client(db)
        yield
        app.dependency_overrides.clear()

    def test_bulk_um_atendimento(self):
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {
                        "cnpj": "22222222000100",
                        "resultado": "NÃO ATENDE",
                        "descricao": "Nao atendeu",
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_recebidos"] == 1
        assert data["total_inseridos"] == 1
        assert data["erros"] == []

    def test_bulk_dois_atendimentos(self):
        # Seed segundo cliente
        c2 = Cliente(
            cnpj="22222222000200",
            nome_fantasia="Segundo Cliente",
            situacao="PROSPECT",
            consultor="MANU",
            classificacao_3tier="REAL",
        )
        self.db.add(c2)
        self.db.commit()

        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {"cnpj": "22222222000100", "resultado": "NÃO ATENDE"},
                    {"cnpj": "22222222000200", "resultado": "NÃO ATENDE"},
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_inseridos"] == 2
        assert data["erros"] == []

    def test_bulk_resultado_invalido_vira_erro(self):
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {
                        "cnpj": "22222222000100",
                        "resultado": "RESULTADO_INEXISTENTE",
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_inseridos"] == 0
        assert len(data["erros"]) == 1
        assert data["erros"][0]["index"] == 0

    def test_bulk_cnpj_inexistente_vira_erro_sem_abortar(self):
        """CNPJ inexistente vira erro por item, inserts válidos continuam."""
        # Seed segundo cliente válido
        c2 = Cliente(
            cnpj="22222222000300",
            nome_fantasia="Terceiro Cliente",
            situacao="ATIVO",
            consultor="MANU",
            classificacao_3tier="REAL",
        )
        self.db.add(c2)
        self.db.commit()

        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {"cnpj": "99999999000099", "resultado": "NÃO ATENDE"},  # inexistente
                    {"cnpj": "22222222000300", "resultado": "NÃO ATENDE"},  # válido
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_inseridos"] == 1
        assert len(data["erros"]) == 1
        assert data["erros"][0]["cnpj"] == "99999999000099"

    def test_bulk_max_50(self):
        """Mais de 50 atendimentos deve retornar 422."""
        atendimentos = [
            {"cnpj": "22222222000100", "resultado": "NÃO ATENDE"}
            for _ in range(51)
        ]
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={"atendimentos": atendimentos},
        )
        assert resp.status_code == 422

    def test_bulk_lista_vazia_rejeitada(self):
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={"atendimentos": []},
        )
        assert resp.status_code == 422

    def test_bulk_two_base_sem_valor_monetario(self):
        """
        R4 — Two-Base: LogInteracao criada via bulk NUNCA deve ter valor monetário.
        Verificamos que o banco não persiste valor_pedido ou similar no log.
        """
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {
                        "cnpj": "22222222000100",
                        "resultado": "NÃO ATENDE",
                        "descricao": "Nao atendeu",
                    }
                ]
            },
        )
        assert resp.status_code == 201
        # Verificar que o LogInteracao foi criado sem valor monetário
        from sqlalchemy import select as _select
        log = self.db.scalar(
            _select(LogInteracao)
            .where(LogInteracao.cnpj == "22222222000100")
            .order_by(LogInteracao.id.desc())
        )
        registro = log
        assert registro is not None
        # Two-Base: interacao sem campo monetario
        assert not hasattr(registro, "valor_pedido"), "R4: sem campo monetario"

    def test_bulk_tipo_contato_invalido_vira_erro(self):
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {
                        "cnpj": "22222222000100",
                        "resultado": "NÃO ATENDE",
                        "tipo_contato": "CARRIER_PIGEON",  # inválido
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_inseridos"] == 0
        assert len(data["erros"]) == 1

    def test_bulk_tipo_contato_valido(self):
        resp = self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {
                        "cnpj": "22222222000100",
                        "resultado": "NÃO ATENDE",
                        "tipo_contato": "WHATSAPP",
                    }
                ]
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_inseridos"] == 1

    def test_bulk_persiste_no_banco(self):
        """Verificar que o atendimento realmente foi salvo no banco."""
        self.client.post(
            "/api/atendimentos/bulk",
            json={
                "atendimentos": [
                    {
                        "cnpj": "22222222000100",
                        "resultado": "NÃO ATENDE",
                        "descricao": "Teste bulk persist",
                    }
                ]
            },
        )
        from sqlalchemy import select as _select
        logs = self.db.scalars(
            _select(LogInteracao).where(LogInteracao.cnpj == "22222222000100")
        ).all()
        assert len(logs) >= 1
        assert any(l.resultado == "NÃO ATENDE" for l in logs)
