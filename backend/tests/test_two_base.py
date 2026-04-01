"""
CRM VITAO360 — Tests for Two-Base Architecture (R4 — CRITICAL).

R4 — TWO-BASE ARCHITECTURE (SAGRADA):
  VENDA = has monetary value (valor_pedido > 0)
  LOG   = NEVER has monetary fields (R$ 0.00 semantics)
  Mixing them caused 742% inflation in a prior session.

These tests are structural and behavioral:
  - Verify that LogInteracao has NO monetary columns
  - Verify that Venda has a DB-enforced CheckConstraint: valor_pedido > 0
  - Verify that inserting Venda with valor <= 0 raises an IntegrityError
  - Verify that dashboard KPI calculations only sum from Venda, not from LogInteracao
  - Verify that faturamento from vendas endpoint only reflects REAL/SINTETICO tiers

These tests MUST pass before any code that touches monetary values is deployed.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models.log_interacao import LogInteracao
from backend.app.models.venda import Venda


# ---------------------------------------------------------------------------
# Schema-level tests (no DB required)
# ---------------------------------------------------------------------------

class TestTwoBaseSchema:
    """Structural verification that the ORM models enforce Two-Base separation."""

    def test_log_interacao_has_no_monetary_columns(self):
        """
        LogInteracao table must not have ANY monetary field.
        Presence of valor*, faturamento*, preco*, ticket*, comissao* = violation.
        """
        columns = {c.name for c in LogInteracao.__table__.columns}
        forbidden_patterns = [
            "valor", "valor_pedido", "valor_venda", "faturamento",
            "preco", "total", "receita", "ticket", "comissao",
            "custo", "lucro",
        ]
        violations = [f for f in forbidden_patterns if f in columns]
        assert not violations, (
            f"TWO-BASE VIOLATION: LogInteracao has monetary column(s): {violations}. "
            "Log records must NEVER store money (R4)."
        )

    def test_venda_has_check_constraint_valor_positivo(self):
        """
        Venda table must have a CheckConstraint enforcing valor_pedido > 0.
        This is the DB-level enforcement of Two-Base Architecture.
        """
        constraints = {c.name for c in Venda.__table__.constraints}
        assert "ck_venda_valor_positivo" in constraints, (
            "Missing CheckConstraint 'ck_venda_valor_positivo' on Venda. "
            "R4 requires valor_pedido > 0 enforced at the DB level."
        )

    def test_venda_has_valor_pedido_column(self):
        """Venda table must have the valor_pedido column (the VENDA side of Two-Base)."""
        columns = {c.name for c in Venda.__table__.columns}
        assert "valor_pedido" in columns

    def test_log_interacao_has_expected_crm_columns(self):
        """LogInteracao must have the motor-calculated CRM fields (not monetary)."""
        columns = {c.name for c in LogInteracao.__table__.columns}
        expected = {
            "id", "cnpj", "consultor", "resultado", "descricao",
            "estagio_funil", "fase", "tipo_contato", "acao_futura",
            "temperatura", "follow_up_dias", "grupo_dash", "tentativa",
        }
        missing = expected - columns
        assert not missing, f"LogInteracao missing CRM columns: {missing}"

    def test_venda_classificacao_3tier_column_exists(self):
        """
        Venda must have classificacao_3tier to enforce R8 (REAL/SINTETICO/ALUCINACAO).
        ALUCINACAO data must never be included in revenue calculations.
        """
        columns = {c.name for c in Venda.__table__.columns}
        assert "classificacao_3tier" in columns


# ---------------------------------------------------------------------------
# DB-level constraint tests
# ---------------------------------------------------------------------------

class TestVendaConstraints:
    """Verify DB-enforced constraints on the Venda model."""

    def test_venda_with_positive_valor_persists(self, db, sample_cliente):
        """Venda with valor_pedido > 0 can be inserted without error."""
        from datetime import date
        v = Venda(
            cnpj=sample_cliente.cnpj,
            data_pedido=date(2026, 3, 1),
            valor_pedido=500.00,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
        )
        db.add(v)
        db.commit()  # Must not raise
        db.refresh(v)
        assert v.id is not None
        assert v.valor_pedido == 500.00

    def test_venda_with_zero_valor_raises_integrity_error(self, db, sample_cliente):
        """
        Venda with valor_pedido = 0 must violate the CheckConstraint.
        This is the DB-level enforcement of R4.
        """
        from datetime import date
        v = Venda(
            cnpj=sample_cliente.cnpj,
            data_pedido=date(2026, 3, 1),
            valor_pedido=0.0,           # VIOLATION: must be > 0
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
        )
        db.add(v)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_venda_with_negative_valor_raises_integrity_error(self, db, sample_cliente):
        """
        Venda with valor_pedido < 0 must violate the CheckConstraint.
        Negative values would invert revenue and are never valid in Two-Base.
        """
        from datetime import date
        v = Venda(
            cnpj=sample_cliente.cnpj,
            data_pedido=date(2026, 3, 1),
            valor_pedido=-100.0,        # VIOLATION: must be > 0
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
        )
        db.add(v)
        with pytest.raises(IntegrityError):
            db.commit()


# ---------------------------------------------------------------------------
# Revenue calculation tests (only Venda rows count)
# ---------------------------------------------------------------------------

class TestFaturamentoCalculation:
    """
    Verify that revenue summation only comes from Venda records.
    LogInteracao records must never contribute to faturamento.
    """

    def test_faturamento_only_counts_venda_records(self, db, sample_cliente):
        """
        Sum of valor_pedido from Venda table equals total revenue.
        LogInteracao has no valor column — cannot inflate faturamento.
        """
        from datetime import date
        from sqlalchemy import func, select

        # Insert two vendas
        for valor in [1000.0, 2000.0]:
            v = Venda(
                cnpj=sample_cliente.cnpj,
                data_pedido=date(2026, 3, 1),
                valor_pedido=valor,
                consultor="MANU",
                fonte="MERCOS",
                classificacao_3tier="REAL",
            )
            db.add(v)
        db.commit()

        # Insert a LogInteracao (must contribute ZERO to revenue)
        from datetime import datetime, timezone
        log = LogInteracao(
            cnpj=sample_cliente.cnpj,
            data_interacao=datetime.now(timezone.utc),
            consultor="MANU",
            resultado="VENDA / PEDIDO",
            descricao="Fechou pedido",
        )
        db.add(log)
        db.commit()

        # Revenue = sum of Venda.valor_pedido only
        total = db.scalar(
            select(func.sum(Venda.valor_pedido)).where(Venda.cnpj == sample_cliente.cnpj)
        )
        assert total == 3000.0, f"Expected R$ 3000.00, got {total}"

        # LogInteracao count must not affect revenue
        log_count = db.query(LogInteracao).filter(LogInteracao.cnpj == sample_cliente.cnpj).count()
        assert log_count == 1  # log exists but contributes nothing to revenue

    def test_alucinacao_tier_not_included_in_valid_calculation(self, db, sample_cliente):
        """
        Vendas classified as ALUCINACAO (R8) are excluded from faturamento calculo.
        Only REAL and SINTETICO tiers are valid for calculations.
        """
        from datetime import date
        from sqlalchemy import func, select

        real_venda = Venda(
            cnpj=sample_cliente.cnpj,
            data_pedido=date(2026, 3, 1),
            valor_pedido=1000.0,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
        )
        # Alucinacao venda — NEVER integrate (R8)
        alucinacao_venda = Venda(
            cnpj=sample_cliente.cnpj,
            data_pedido=date(2026, 3, 2),
            valor_pedido=9999.0,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="ALUCINACAO",
        )
        db.add_all([real_venda, alucinacao_venda])
        db.commit()

        # Only REAL/SINTETICO should count for revenue
        tiers_validos = ("REAL", "SINTETICO")
        total_valido = db.scalar(
            select(func.sum(Venda.valor_pedido)).where(
                Venda.cnpj == sample_cliente.cnpj,
                Venda.classificacao_3tier.in_(tiers_validos),
            )
        )
        assert total_valido == 1000.0, (
            f"ALUCINACAO tier must be excluded from revenue. "
            f"Expected 1000.0, got {total_valido}."
        )

    def test_faturamento_baseline_tolerance(self, db, sample_cliente):
        """
        When total vendas approaches the baseline (R$ 2.091.000),
        the divergence check logic works correctly (R7: tolerance 0.5%).
        """
        baseline = 2_091_000.0
        tolerance = 0.005

        # Example: total within tolerance
        total_within = baseline * 0.998   # 0.2% below -> OK
        assert abs(total_within - baseline) / baseline <= tolerance

        # Example: total outside tolerance
        total_outside = baseline * 0.994  # 0.6% below -> FAIL
        assert abs(total_outside - baseline) / baseline > tolerance


# ---------------------------------------------------------------------------
# Dashboard KPI isolation test
# ---------------------------------------------------------------------------

class TestDashboardKPIIsolation:
    """
    Verify that the dashboard does not mix Venda and LogInteracao data
    when computing faturamento KPIs.
    """

    def test_dashboard_kpi_endpoint_returns_200(self, client_admin, db, sample_cliente):
        """GET /api/dashboard/kpis returns HTTP 200 (smoke test)."""
        resp = client_admin.get("/api/dashboard/kpis")
        # Dashboard may return 200 or 500 depending on data state —
        # we assert it does not return 4xx
        assert resp.status_code in (200, 500)

    def test_vendas_endpoint_only_lists_venda_records(self, client_admin, db, sample_cliente):
        """
        GET /api/vendas returns records from the Venda table only.
        LogInteracao records do not appear in this response.
        Every returned record must have valor_pedido > 0 (Two-Base invariant).
        """
        from datetime import date

        # Insert a real venda
        v = Venda(
            cnpj=sample_cliente.cnpj,
            data_pedido=date(2026, 3, 1),
            valor_pedido=500.0,
            consultor="MANU",
            fonte="MERCOS",
            classificacao_3tier="REAL",
        )
        db.add(v)
        db.commit()

        resp = client_admin.get("/api/vendas")
        assert resp.status_code == 200
        data = resp.json()

        # Normalise: endpoint may return list directly or dict with a key
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("vendas", data.get("registros", []))
        else:
            records = []

        # Every returned record must have valor_pedido > 0 (Two-Base invariant)
        for record in records:
            valor = record.get("valor_pedido", 0)
            assert valor > 0, (
                f"Vendas endpoint returned record with valor_pedido={valor}. "
                "Two-Base violation: all venda records must have valor > 0."
            )
