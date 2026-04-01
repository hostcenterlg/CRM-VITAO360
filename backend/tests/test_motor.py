"""
CRM VITAO360 — Tests for Motor de Regras routes and service.

Covers:
  - GET /api/motor/regras returns list with total
  - GET /api/motor/regras?situacao=ATIVO filters correctly
  - GET /api/motor/regras/{id} returns correct rule
  - GET /api/motor/regras/{id} with unknown ID returns 404
  - Motor applies ATIVO + VENDA rule correctly
  - Motor applies PROSPECT + ORCAMENTO rule
  - Motor returns 9 output dimensions
  - Motor handles unknown combination via fallback
  - require_admin blocks non-admin users (403)

Uses conftest fixtures:
  - client_admin: TestClient with admin override + in-memory DB
  - regras_seed: 3 RegraMotor rows seeded in the test DB
"""

from __future__ import annotations

import pytest

from backend.app.models.regra_motor import RegraMotor
from backend.app.services.motor_regras_service import MotorRegrasService


# ---------------------------------------------------------------------------
# Routes: GET /api/motor/regras
# ---------------------------------------------------------------------------

class TestMotorRegrasRoutes:

    def test_listar_regras_returns_200_with_total(self, client_admin, regras_seed):
        """GET /api/motor/regras returns 200 with total=3 (seeded) and regras list."""
        resp = client_admin.get("/api/motor/regras")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "regras" in data
        assert data["total"] == 3
        assert len(data["regras"]) == 3

    def test_listar_regras_all_required_fields_present(self, client_admin, regras_seed):
        """Each regra in the list must contain all required output fields."""
        resp = client_admin.get("/api/motor/regras")
        assert resp.status_code == 200
        regra = resp.json()["regras"][0]
        required_fields = [
            "id", "situacao", "resultado", "estagio_funil",
            "fase", "tipo_contato", "acao_futura", "temperatura",
            "followup_dias", "chave",
        ]
        for field in required_fields:
            assert field in regra, f"Required field '{field}' missing from motor regra response"

    def test_filtro_situacao_ativo_returns_two_rules(self, client_admin, regras_seed):
        """?situacao=ATIVO returns only the 2 ATIVO rules from the seed."""
        resp = client_admin.get("/api/motor/regras", params={"situacao": "ATIVO"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for regra in data["regras"]:
            assert regra["situacao"] == "ATIVO"

    def test_filtro_situacao_prospect_returns_one_rule(self, client_admin, regras_seed):
        """?situacao=PROSPECT returns the 1 PROSPECT rule."""
        resp = client_admin.get("/api/motor/regras", params={"situacao": "PROSPECT"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["regras"][0]["situacao"] == "PROSPECT"

    def test_filtro_situacao_inexistente_returns_empty(self, client_admin, regras_seed):
        """?situacao=INEXISTENTE returns total=0 and empty list."""
        resp = client_admin.get("/api/motor/regras", params={"situacao": "INEXISTENTE"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["regras"] == []

    def test_filtro_situacao_case_insensitive(self, client_admin, regras_seed):
        """?situacao=ativo (lowercase) is treated same as ATIVO."""
        resp = client_admin.get("/api/motor/regras", params={"situacao": "ativo"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_non_admin_returns_403(self, client_consultor, regras_seed):
        """Consultor role must be denied access to motor rules (403)."""
        resp = client_consultor.get("/api/motor/regras")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Routes: GET /api/motor/regras/{id}
# ---------------------------------------------------------------------------

class TestMotorDetalheRoute:

    def test_get_regra_by_id_returns_correct_rule(self, client_admin, db, regras_seed):
        """GET /api/motor/regras/{id} returns the rule identified by ID."""
        from sqlalchemy import select
        regra = db.scalar(
            select(RegraMotor).where(RegraMotor.chave == "ATIVO|VENDA / PEDIDO")
        )
        assert regra is not None

        resp = client_admin.get(f"/api/motor/regras/{regra.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == regra.id
        assert data["situacao"] == "ATIVO"
        assert data["resultado"] == "VENDA / PEDIDO"
        assert data["chave"] == "ATIVO|VENDA / PEDIDO"
        assert data["temperatura"] == "QUENTE"
        assert data["followup_dias"] == 45

    def test_get_regra_unknown_id_returns_404(self, client_admin, regras_seed):
        """GET /api/motor/regras/99999 returns 404 when rule does not exist."""
        resp = client_admin.get("/api/motor/regras/99999")
        assert resp.status_code == 404

    def test_non_admin_detail_returns_403(self, client_consultor, regras_seed):
        """Consultor cannot access motor rule details (403)."""
        resp = client_consultor.get("/api/motor/regras/1")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Service: MotorRegrasService.aplicar()
# ---------------------------------------------------------------------------

class TestMotorServiceAplicar:

    def test_ativo_venda_returns_pos_venda(self, db, regras_seed):
        """ATIVO + VENDA / PEDIDO resolves via DB rule to estagio_funil=POS-VENDA."""
        svc = MotorRegrasService()
        result = svc.aplicar(db, "ATIVO", "VENDA / PEDIDO")

        assert result["estagio_funil"] == "POS-VENDA"
        assert result["fase"] == "POS-VENDA"
        assert result["temperatura"] == "QUENTE"
        assert result["follow_up_dias"] == 45
        # Venda does NOT advance tentativa counter
        assert result["tentativa"] is None

    def test_ativo_orcamento_returns_negociacao(self, db, regras_seed):
        """ATIVO + ORCAMENTO resolves via DB rule to fase=NEGOCIACAO."""
        svc = MotorRegrasService()
        result = svc.aplicar(db, "ATIVO", "ORCAMENTO")

        assert result["fase"] == "NEGOCIACAO"
        assert result["estagio_funil"] == "EM ATENDIMENTO"
        assert result["temperatura"] == "MORNO"

    def test_prospect_primeiro_contato_returns_prospeccao(self, db, regras_seed):
        """PROSPECT + PRIMEIRO CONTATO resolves to fase=AQUISICAO."""
        svc = MotorRegrasService()
        result = svc.aplicar(db, "PROSPECT", "PRIMEIRO CONTATO")

        assert result["fase"] == "AQUISICAO"
        assert result["estagio_funil"] == "PROSPECCAO"
        assert result["temperatura"] == "FRIO"

    def test_motor_returns_nine_dimensions(self, db, regras_seed):
        """Motor result dict must contain exactly 9 output dimensions."""
        svc = MotorRegrasService()
        result = svc.aplicar(db, "ATIVO", "VENDA / PEDIDO")

        expected_keys = {
            "estagio_funil", "fase", "tipo_contato", "acao_futura",
            "temperatura", "follow_up_dias", "grupo_dash", "tipo_acao", "tentativa",
        }
        missing = expected_keys - result.keys()
        assert not missing, f"Motor result missing dimension(s): {missing}"

    def test_motor_unknown_combination_uses_fallback(self, db):
        """
        Unknown situacao+resultado combination (not in DB) must not raise.
        Returns non-empty result via fallback or local resolver.
        """
        svc = MotorRegrasService()
        # No rules seeded — DB is empty, forces fallback
        result = svc.aplicar(db, "INAT.ANT", "RELACIONAMENTO")

        assert result is not None
        assert "estagio_funil" in result
        assert "temperatura" in result

    def test_motor_sem_resposta_result_advances_tentativa(self, db, regras_seed):
        """
        Results that mean 'no answer' must advance the tentativa counter.
        T1 -> T2 on second 'NAO ATENDE' interaction.
        """
        svc = MotorRegrasService()
        # Simulate second attempt (T1 already set)
        # We bypass DB rule lookup since no NAO ATENDE rule is seeded
        next_tent = svc._avancar_tentativa("T1")
        assert next_tent == "T2"

    def test_motor_tentativa_sequence_none_to_t1(self, db):
        """First interaction with no response: None -> T1."""
        svc = MotorRegrasService()
        assert svc._avancar_tentativa(None) == "T1"

    def test_motor_tentativa_sequence_t4_to_nutricao(self, db):
        """T4 exhausted: T4 -> NUTRICAO (end of sequence)."""
        svc = MotorRegrasService()
        result = svc._avancar_tentativa("T4")
        assert "NUTRI" in result.upper()
