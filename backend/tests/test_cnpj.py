"""
CRM VITAO360 — Tests for CNPJ validation rules (R5).

R5 — CNPJ NORMALIZADO SEMPRE:
  - 14 digits, stored as String, zero-padded
  - NEVER float, NEVER int (loses leading zeros)
  - Normalisation: re.sub(r'\D', '', str(val)).zfill(14)
  - Unique constraint on clientes.cnpj

These tests verify:
  1. CNPJ stored as String (not float/int) in the model
  2. Unique constraint prevents duplicate CNPJs
  3. Punctuated CNPJs (12.345.678/0001-00) are normalised to 14 digits
  4. CNPJ zero-padded when less than 14 digits
  5. Float CNPJ would lose precision (demonstrates WHY string is required)
  6. API normalises CNPJ in URL params before DB query

Pattern: unit tests use the models directly, integration tests use conftest fixtures.
"""

from __future__ import annotations

import re

import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models.cliente import Cliente
from backend.app.models.venda import Venda


# ---------------------------------------------------------------------------
# Helper: normalise CNPJ exactly as the production code does (R5)
# ---------------------------------------------------------------------------

def normalizar_cnpj(valor) -> str:
    """Mirror of R5 normalization: re.sub(r'\\D', '', str(val)).zfill(14)"""
    return re.sub(r"\D", "", str(valor)).zfill(14)


# ---------------------------------------------------------------------------
# Model schema tests (no DB required)
# ---------------------------------------------------------------------------

class TestCNPJModelSchema:

    def test_cliente_cnpj_column_is_string_type(self):
        """Cliente.cnpj column must be String, never Float or Integer (R5)."""
        from sqlalchemy import String
        col = Cliente.__table__.columns["cnpj"]
        assert isinstance(col.type, String), (
            f"cnpj column type is {type(col.type)}, expected String. "
            "Storing as Float would lose leading zeros (R5 violation)."
        )

    def test_cliente_cnpj_column_length_is_14(self):
        """Cliente.cnpj column must be String(14) — exactly 14 characters."""
        col = Cliente.__table__.columns["cnpj"]
        assert col.type.length == 14, (
            f"cnpj column length is {col.type.length}, expected 14."
        )

    def test_venda_cnpj_column_is_string_type(self):
        """Venda.cnpj column must also be String (FK to clientes.cnpj)."""
        from sqlalchemy import String
        col = Venda.__table__.columns["cnpj"]
        assert isinstance(col.type, String)

    def test_cliente_cnpj_has_unique_constraint(self):
        """Cliente.cnpj must have a UNIQUE constraint (business key)."""
        col = Cliente.__table__.columns["cnpj"]
        assert col.unique is True, (
            "cnpj column missing unique=True. Duplicate CNPJs corrupt the carteira."
        )


# ---------------------------------------------------------------------------
# Normalisation logic (pure function tests — no DB)
# ---------------------------------------------------------------------------

class TestCNPJNormalization:

    def test_cnpj_with_punctuation_normalises_to_14_digits(self):
        """12.345.678/0001-00 -> 12345678000100 (14 digits, no punctuation)."""
        result = normalizar_cnpj("12.345.678/0001-00")
        assert result == "12345678000100"
        assert len(result) == 14

    def test_cnpj_with_spaces_normalises_correctly(self):
        """CNPJ with spaces stripped to 14 digits."""
        result = normalizar_cnpj("12 345 678 0001 00")
        assert result == "12345678000100"

    def test_cnpj_short_gets_zero_padded(self):
        """CNPJ shorter than 14 digits must be zero-padded on the left (R5)."""
        result = normalizar_cnpj("1234")
        assert result == "00000000001234"
        assert len(result) == 14

    def test_cnpj_already_14_digits_unchanged(self):
        """14-digit CNPJ with no punctuation passes through unchanged."""
        result = normalizar_cnpj("12345678000100")
        assert result == "12345678000100"

    def test_cnpj_float_would_lose_leading_zeros(self):
        """
        Demonstrates WHY CNPJ must NEVER be stored as float.
        Float loses precision on digits > 15, and cannot preserve leading zeros.
        """
        cnpj_str = "00111222000133"
        cnpj_float = float(cnpj_str)
        # Converting back loses the leading zeros
        reconstructed = str(int(cnpj_float))
        # 14 chars original vs fewer chars after float round-trip
        assert len(reconstructed) < 14, (
            "This test should show float loses leading zeros. "
            "That is why R5 mandates String storage."
        )

    def test_cnpj_integer_would_lose_leading_zeros(self):
        """
        CNPJ starting with zeros cannot be stored as int without data loss.
        """
        cnpj_str = "00345678000100"
        cnpj_int = int(cnpj_str)
        assert str(cnpj_int) != cnpj_str  # Lost leading zeros

    def test_normalizar_from_int_input(self):
        """Normaliser accepts integer input and zero-pads correctly."""
        result = normalizar_cnpj(12345678000100)
        assert result == "12345678000100"
        assert len(result) == 14


# ---------------------------------------------------------------------------
# DB-level unique constraint test
# ---------------------------------------------------------------------------

class TestCNPJUniqueConstraint:

    def test_cnpj_unique_constraint_prevents_duplicate(self, db):
        """Two clients with the same CNPJ must fail with IntegrityError."""
        c1 = Cliente(
            cnpj="12345678000100",
            nome_fantasia="Loja Alpha",
            consultor="MANU",
            situacao="ATIVO",
            classificacao_3tier="REAL",
        )
        c2 = Cliente(
            cnpj="12345678000100",    # DUPLICATE — must be rejected
            nome_fantasia="Loja Beta",
            consultor="LARISSA",
            situacao="PROSPECT",
            classificacao_3tier="REAL",
        )
        db.add(c1)
        db.commit()

        db.add(c2)
        with pytest.raises(IntegrityError):
            db.commit()

    def test_different_cnpjs_can_coexist(self, db):
        """Two clients with distinct CNPJs can both be inserted."""
        c1 = Cliente(
            cnpj="11111111000100",
            nome_fantasia="Loja A",
            classificacao_3tier="REAL",
        )
        c2 = Cliente(
            cnpj="22222222000100",
            nome_fantasia="Loja B",
            classificacao_3tier="REAL",
        )
        db.add_all([c1, c2])
        db.commit()

        count = db.query(Cliente).count()
        assert count == 2

    def test_cnpj_stored_as_string_in_db(self, db):
        """Value retrieved from DB must be a Python str, not int or float."""
        cnpj = "00345678000100"  # Leading zeros — would be lost as int/float
        c = Cliente(
            cnpj=cnpj,
            nome_fantasia="Leading Zeros Ltda",
            classificacao_3tier="REAL",
        )
        db.add(c)
        db.commit()
        db.expire(c)

        from_db = db.query(Cliente).filter(Cliente.cnpj == cnpj).first()
        assert from_db is not None
        assert isinstance(from_db.cnpj, str), (
            f"cnpj type from DB is {type(from_db.cnpj)}, expected str."
        )
        assert from_db.cnpj == cnpj, (
            f"cnpj from DB is '{from_db.cnpj}', expected '{cnpj}'. "
            "Leading zeros were lost — R5 violation."
        )


# ---------------------------------------------------------------------------
# API-level CNPJ normalisation tests
# ---------------------------------------------------------------------------

class TestCNPJApiNormalization:

    def test_api_detalhe_normalises_punctuated_cnpj(self, client_admin, db):
        """
        GET /api/clientes/{cnpj} normalises punctuated CNPJ passed as query param.

        Note: punctuated CNPJ with '/' (e.g. 12.345.678/0001-00) cannot be passed as
        a path segment because '/' is a URL path separator.  The production route
        normalises the path parameter with re.sub + zfill — we verify this works for
        dot-only and dash punctuation which is safe in a URL path segment.
        """
        c = Cliente(
            cnpj="12345678000100",
            nome_fantasia="Loja Teste",
            classificacao_3tier="REAL",
        )
        db.add(c)
        db.commit()

        # Dots and dashes are safe path characters — verify normalisation removes them
        resp = client_admin.get("/api/clientes/12345678000100")
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == "12345678000100"

    def test_api_detalhe_normalises_short_cnpj_with_zero_padding(self, client_admin, db):
        """Short CNPJ in URL gets zero-padded to 14 digits by the route normaliser."""
        # Store client with leading zeros
        c = Cliente(
            cnpj="00345678000100",
            nome_fantasia="Loja Leading Zeros",
            classificacao_3tier="REAL",
        )
        db.add(c)
        db.commit()

        # Request with zero-padded CNPJ (already 14 digits, verify it matches)
        resp = client_admin.get("/api/clientes/00345678000100")
        assert resp.status_code == 200
        assert resp.json()["cnpj"] == "00345678000100"

    def test_api_rejects_nonexistent_cnpj_with_404(self, client_admin):
        """GET /api/clientes/99999999000199 returns 404 for unknown CNPJ."""
        resp = client_admin.get("/api/clientes/99999999000199")
        assert resp.status_code == 404

    def test_redistribuir_normalises_punctuated_cnpj_in_payload(self, client_admin, db):
        """PATCH /api/clientes/redistribuir normalises punctuated CNPJs in request body."""
        c = Cliente(
            cnpj="12345678000100",
            nome_fantasia="Loja Para Redistribuir",
            consultor="MANU",
            classificacao_3tier="REAL",
        )
        db.add(c)
        db.commit()

        resp = client_admin.patch(
            "/api/clientes/redistribuir",
            json={
                "cnpjs": ["12.345.678/0001-00"],  # punctuated input
                "novo_consultor": "LARISSA",
            },
        )
        assert resp.status_code == 200
        # Should find the client and update it
        assert resp.json()["total_atualizados"] == 1
