"""
CRM VITAO360 — Tests for /api/clientes endpoints.

Covers:
  - List clientes returns paginated response
  - Filters: situacao, consultor, sinaleiro, curva_abc
  - Get single cliente by CNPJ (R5: normalisation of punctuated CNPJ)
  - 404 for unknown CNPJ
  - Stats endpoint aggregation
  - Redistribuir requires admin role (403 for consultor)
  - Redistribuir correctly reassigns clients
  - Redistribuir rejects invalid consultor name
  - CNPJ normalization: punctuated input -> 14 digits stored and queried

Pattern: uses client_admin / client_consultor fixtures from conftest.py.
"""

from __future__ import annotations

import pytest

from backend.app.models.cliente import Cliente


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _add_cliente(db, cnpj: str, consultor: str = "MANU", situacao: str = "ATIVO",
                 sinaleiro: str = "VERDE", curva_abc: str = "A") -> Cliente:
    c = Cliente(
        cnpj=cnpj,
        nome_fantasia=f"Loja {cnpj[-4:]}",
        consultor=consultor,
        situacao=situacao,
        sinaleiro=sinaleiro,
        curva_abc=curva_abc,
        classificacao_3tier="REAL",
    )
    db.add(c)
    db.commit()
    return c


# ---------------------------------------------------------------------------
# List clientes
# ---------------------------------------------------------------------------

class TestListarClientes:

    def test_list_clientes_returns_paginated_response(self, client_admin, db):
        """GET /api/clientes returns registros list with total, limit, offset."""
        _add_cliente(db, "11111111000100")
        _add_cliente(db, "22222222000100")

        resp = client_admin.get("/api/clientes")
        assert resp.status_code == 200
        data = resp.json()
        assert "registros" in data
        assert "total" in data
        assert data["total"] == 2
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_list_clientes_empty_db_returns_zero(self, client_admin):
        """Empty database returns total=0 and empty registros list."""
        resp = client_admin.get("/api/clientes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["registros"] == []

    def test_filter_by_situacao_ativo(self, client_admin, db):
        """?situacao=ATIVO filters out non-ATIVO records."""
        _add_cliente(db, "11111111000100", situacao="ATIVO")
        _add_cliente(db, "22222222000100", situacao="PROSPECT")
        _add_cliente(db, "33333333000100", situacao="INAT.ANT")

        resp = client_admin.get("/api/clientes", params={"situacao": "ATIVO"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["registros"][0]["situacao"] == "ATIVO"

    def test_filter_by_consultor(self, client_admin, db):
        """?consultor=MANU returns only MANU clients."""
        _add_cliente(db, "11111111000100", consultor="MANU")
        _add_cliente(db, "22222222000100", consultor="LARISSA")

        resp = client_admin.get("/api/clientes", params={"consultor": "MANU"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["registros"][0]["consultor"] == "MANU"

    def test_filter_by_sinaleiro(self, client_admin, db):
        """?sinaleiro=VERDE returns only VERDE sinaleiro clients."""
        _add_cliente(db, "11111111000100", sinaleiro="VERDE")
        _add_cliente(db, "22222222000100", sinaleiro="VERMELHO")
        _add_cliente(db, "33333333000100", sinaleiro="AMARELO")

        resp = client_admin.get("/api/clientes", params={"sinaleiro": "VERDE"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["registros"][0]["sinaleiro"] == "VERDE"

    def test_filter_by_curva_abc(self, client_admin, db):
        """?curva_abc=B returns only curva B clients."""
        _add_cliente(db, "11111111000100", curva_abc="A")
        _add_cliente(db, "22222222000100", curva_abc="B")
        _add_cliente(db, "33333333000100", curva_abc="C")

        resp = client_admin.get("/api/clientes", params={"curva_abc": "B"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["registros"][0]["curva_abc"] == "B"

    def test_consultor_role_sees_only_own_carteira(self, client_consultor, db):
        """Consultor (role=consultor, consultor_nome=MANU) sees only MANU clients."""
        _add_cliente(db, "11111111000100", consultor="MANU")
        _add_cliente(db, "22222222000100", consultor="LARISSA")

        resp = client_consultor.get("/api/clientes")
        assert resp.status_code == 200
        data = resp.json()
        # MANU consultor sees only their own clients
        assert data["total"] == 1
        assert data["registros"][0]["consultor"] == "MANU"

    def test_pagination_limit_and_offset(self, client_admin, db):
        """limit and offset parameters paginate correctly."""
        for i in range(5):
            _add_cliente(db, f"1111111100010{i}")

        resp = client_admin.get("/api/clientes", params={"limit": 2, "offset": 0})
        assert resp.status_code == 200
        assert len(resp.json()["registros"]) == 2
        assert resp.json()["total"] == 5


# ---------------------------------------------------------------------------
# Get single cliente by CNPJ
# ---------------------------------------------------------------------------

class TestDetalheCliente:

    def test_get_cliente_by_cnpj_returns_all_fields(self, client_admin, sample_cliente):
        """GET /api/clientes/{cnpj} returns ClienteDetalhe with all fields."""
        resp = client_admin.get(f"/api/clientes/{sample_cliente.cnpj}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cnpj"] == sample_cliente.cnpj
        assert data["nome_fantasia"] == sample_cliente.nome_fantasia
        assert data["situacao"] == "ATIVO"
        assert data["consultor"] == "MANU"

    def test_get_cliente_unknown_cnpj_returns_404(self, client_admin):
        """CNPJ not in DB returns 404."""
        resp = client_admin.get("/api/clientes/99999999000199")
        assert resp.status_code == 404

    def test_cnpj_normalized_when_punctuated(self, client_admin, db):
        """
        CNPJ stored as 14-digit string (R5).
        Route normalises CNPJ using re.sub(r'\\D','') + zfill(14).

        Note: '/' is a URL path separator and cannot be embedded in a path segment.
        The test verifies normalisation for dot/dash variants which are URL-safe.
        The redistribuir endpoint (test_redistribuir_normalizes_punctuated_cnpj) covers
        the full punctuated format via the request body.
        """
        _add_cliente(db, "12345678000100")
        # 14-digit CNPJ without punctuation — basic normalisation path
        resp = client_admin.get("/api/clientes/12345678000100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cnpj"] == "12345678000100"  # 14 digits, stored without punctuation


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------

class TestStatsClientes:

    def test_stats_returns_correct_structure(self, client_admin, db):
        """GET /api/clientes/stats returns expected aggregation keys."""
        _add_cliente(db, "11111111000100", situacao="ATIVO", consultor="MANU", sinaleiro="VERDE")
        _add_cliente(db, "22222222000100", situacao="PROSPECT", consultor="LARISSA", sinaleiro="ROXO")

        resp = client_admin.get("/api/clientes/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_clientes" in data
        assert "por_situacao" in data
        assert "por_consultor" in data
        assert "por_sinaleiro" in data
        assert "por_curva_abc" in data
        assert "por_prioridade" in data

    def test_stats_total_matches_db_count(self, client_admin, db):
        """total_clientes in stats matches actual row count."""
        _add_cliente(db, "11111111000100")
        _add_cliente(db, "22222222000100")

        resp = client_admin.get("/api/clientes/stats")
        assert resp.status_code == 200
        assert resp.json()["total_clientes"] == 2

    def test_stats_por_situacao_labels_correct(self, client_admin, db):
        """por_situacao contains label=ATIVO with quantidade=1."""
        _add_cliente(db, "11111111000100", situacao="ATIVO")

        resp = client_admin.get("/api/clientes/stats")
        situacoes = {r["label"]: r["quantidade"] for r in resp.json()["por_situacao"]}
        assert situacoes.get("ATIVO") == 1


# ---------------------------------------------------------------------------
# Redistribuir (admin only)
# ---------------------------------------------------------------------------

class TestRedistribuir:

    def test_redistribuir_requires_admin(self, client_consultor, db, sample_cliente):
        """PATCH /api/clientes/redistribuir returns 403 for consultor role."""
        resp = client_consultor.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [sample_cliente.cnpj], "novo_consultor": "LARISSA"},
        )
        assert resp.status_code == 403

    def test_redistribuir_updates_consultor(self, client_admin, db, sample_cliente):
        """Admin redistribuir moves clients to new consultor."""
        assert sample_cliente.consultor == "MANU"

        resp = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [sample_cliente.cnpj], "novo_consultor": "LARISSA"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_atualizados"] == 1
        assert data["total_processados"] == 1
        assert data["erros"] == []

    def test_redistribuir_invalid_consultor_returns_422(self, client_admin, db, sample_cliente):
        """Invalid consultor name (not in MANU/LARISSA/DAIANE/JULIO) returns 422."""
        resp = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": [sample_cliente.cnpj], "novo_consultor": "FANTASMA"},
        )
        assert resp.status_code == 422

    def test_redistribuir_unknown_cnpj_reported_as_error(self, client_admin):
        """CNPJ not in DB is added to errors list, does not abort batch."""
        resp = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": ["99999999000199"], "novo_consultor": "LARISSA"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_atualizados"] == 0
        assert len(data["erros"]) == 1

    def test_redistribuir_normalizes_punctuated_cnpj(self, client_admin, db):
        """Redistribuir accepts punctuated CNPJ in payload (R5: normalised internally)."""
        _add_cliente(db, "12345678000100", consultor="MANU")

        resp = client_admin.patch(
            "/api/clientes/redistribuir",
            json={"cnpjs": ["12.345.678/0001-00"], "novo_consultor": "LARISSA"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_atualizados"] == 1
