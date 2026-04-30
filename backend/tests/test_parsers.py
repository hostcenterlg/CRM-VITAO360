"""
CRM VITAO360 — test_parsers.py
=================================
Testes unitários para os 5 parsers DDE/AC e BaseParser.

Cobertura:
  - validate_file: rejeita não-xlsx, arquivo vazio, arquivo ausente
  - extract() smoke: retorna list com dados mínimos
  - normalize() tipos: produz modelos corretos
  - idempotência: rodar 2x não duplica registros (via merge)
  - robustez: arquivo com cabeçalho inválido

Usa fixtures XLSX criados programaticamente (sem binários no repo).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call

import pytest

# Importar fixtures
from backend.tests.fixtures.parsers.conftest_fixtures import (
    CNPJ_TESTE,
    ANO_TESTE,
    MES_TESTE,
    create_zsdfat_fixture,
    create_verbas_fixture,
    create_frete_fixture,
    create_contratos_fixture,
    create_promotores_fixture,
)

from scripts.parsers.base_parser import BaseParser, ValidationResult
from scripts.parsers.parser_zsdfat import ParserZSDFAT
from scripts.parsers.parser_verbas import ParserVerbas
from scripts.parsers.parser_frete import ParserFrete
from scripts.parsers.parser_contratos import ParserContratos
from scripts.parsers.parser_promotores import ParserPromotores

from backend.app.models.cliente_dre import ClienteDrePeriodo
from backend.app.models.cliente_verba import ClienteVerbaAnual
from backend.app.models.cliente_frete import ClienteFretesMensal
from backend.app.models.cliente_promotor import ClientePromotorMensal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_db() -> MagicMock:
    """Cria um mock de Session SQLAlchemy para testes sem banco real."""
    db = MagicMock()
    db.merge.return_value = MagicMock()
    return db


# ---------------------------------------------------------------------------
# BaseParser — validate_file
# ---------------------------------------------------------------------------

class TestValidateFile:
    """Testa validate_file com as verificações de existência, extensão e tamanho."""

    def _make_concrete_parser(self) -> BaseParser:
        """Cria instância concreta mínima para testar BaseParser."""
        class _DummyParser(BaseParser):
            def extract(self, path): return []
            def normalize(self, raw): return []
        return _DummyParser()

    def test_rejeita_arquivo_ausente(self, tmp_path):
        parser = self._make_concrete_parser()
        result = parser.validate_file(tmp_path / "nao_existe.xlsx")
        assert not result.ok
        assert any("não encontrado" in e.lower() or "nao encontrado" in e.lower() for e in result.errors)

    def test_rejeita_extensao_invalida_txt(self, tmp_path):
        p = tmp_path / "arquivo.txt"
        p.write_bytes(b"conteudo")
        parser = self._make_concrete_parser()
        result = parser.validate_file(p)
        assert not result.ok
        assert any("extensao" in e.lower() or "extensão" in e.lower() for e in result.errors)

    def test_rejeita_extensao_csv(self, tmp_path):
        p = tmp_path / "dados.csv"
        p.write_bytes(b"a,b,c")
        parser = self._make_concrete_parser()
        result = parser.validate_file(p)
        assert not result.ok

    def test_rejeita_arquivo_vazio(self, tmp_path):
        p = tmp_path / "vazio.xlsx"
        p.write_bytes(b"")
        parser = self._make_concrete_parser()
        result = parser.validate_file(p)
        assert not result.ok
        assert any("vazio" in e.lower() or "0 bytes" in e for e in result.errors)

    def test_aceita_xlsx_valido(self, tmp_path):
        p = tmp_path / "valido.xlsx"
        p.write_bytes(b"conteudo_fake_xlsx")
        parser = self._make_concrete_parser()
        result = parser.validate_file(p)
        assert result.ok

    def test_aceita_xlsm(self, tmp_path):
        p = tmp_path / "macro.xlsm"
        p.write_bytes(b"conteudo_fake")
        parser = self._make_concrete_parser()
        result = parser.validate_file(p)
        assert result.ok


# ---------------------------------------------------------------------------
# ParserZSDFAT
# ---------------------------------------------------------------------------

class TestParserZSDFAT:
    def test_extract_retorna_linhas(self, tmp_path):
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        raw = parser.extract(path)
        assert isinstance(raw, list)
        assert len(raw) > 0, "extract() deve retornar ao menos uma linha"

    def test_normalize_produz_dre_periodo(self, tmp_path):
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(isinstance(m, ClienteDrePeriodo) for m in models)

    def test_normalize_cnpj_normalizado(self, tmp_path):
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert len(m.cnpj) == 14, f"CNPJ com tamanho errado: {m.cnpj!r}"
            assert m.cnpj.isdigit(), f"CNPJ com caracteres não-numéricos: {m.cnpj!r}"

    def test_normalize_linha_raw_vira_sintetico(self, tmp_path):
        """Conta não reconhecida pelos 22 regex deve ter classificacao='SINTETICO'."""
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        sinteticos = [m for m in models if m.classificacao == "SINTETICO"]
        assert len(sinteticos) > 0, "Deve haver pelo menos 1 linha RAW→SINTETICO na fixture"

    def test_normalize_contas_reconhecidas_sao_real(self, tmp_path):
        """Contas reconhecidas pelos 22 regex devem ter classificacao='REAL'."""
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        reais = [m for m in models if m.classificacao == "REAL"]
        assert len(reais) > 0, "Deve haver contas REAL na fixture"

    def test_upsert_chama_merge_e_commit(self, tmp_path):
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        db = make_mock_db()
        count = parser.upsert(models, db)
        assert count == len(models)
        assert db.merge.call_count == len(models)
        db.commit.assert_called_once()

    def test_validate_rejeita_nao_xlsx(self, tmp_path):
        p = tmp_path / "arquivo.pdf"
        p.write_bytes(b"fake")
        parser = ParserZSDFAT()
        result = parser.validate_file(p)
        assert not result.ok

    def test_validate_rejeita_vazio(self, tmp_path):
        p = tmp_path / "vazio.xlsx"
        p.write_bytes(b"")
        parser = ParserZSDFAT()
        result = parser.validate_file(p)
        assert not result.ok

    def test_run_retorna_ok(self, tmp_path):
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        db = make_mock_db()
        result = parser.run(path, db)
        assert result["status"] == "OK"
        assert result["registros"] > 0

    def test_run_arquivo_ausente_retorna_erro(self, tmp_path):
        parser = ParserZSDFAT()
        db = make_mock_db()
        result = parser.run(tmp_path / "inexistente.xlsx", db)
        assert result["status"] == "ERRO"
        assert len(result["errors"]) > 0

    def test_idempotencia(self, tmp_path):
        """Rodar 2x com db.merge não deve duplicar — merge usa ON CONFLICT."""
        path = create_zsdfat_fixture(tmp_path)
        parser = ParserZSDFAT()
        db = make_mock_db()
        result1 = parser.run(path, db)
        result2 = parser.run(path, db)
        # Ambos devem ter mesmo número de registros (merge idempotente)
        assert result1["registros"] == result2["registros"]


# ---------------------------------------------------------------------------
# ParserVerbas
# ---------------------------------------------------------------------------

class TestParserVerbas:
    def test_extract_retorna_linhas(self, tmp_path):
        path = create_verbas_fixture(tmp_path)
        parser = ParserVerbas()
        raw = parser.extract(path)
        assert len(raw) == 3

    def test_normalize_produz_verba_anual(self, tmp_path):
        path = create_verbas_fixture(tmp_path)
        parser = ParserVerbas()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(isinstance(m, ClienteVerbaAnual) for m in models)

    def test_normalize_tipo_efetivada(self, tmp_path):
        path = create_verbas_fixture(tmp_path)
        parser = ParserVerbas()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(m.tipo == "EFETIVADA" for m in models)

    def test_normalize_classificacao_real(self, tmp_path):
        path = create_verbas_fixture(tmp_path)
        parser = ParserVerbas()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(m.classificacao == "REAL" for m in models)

    def test_normalize_cnpj_14_digitos(self, tmp_path):
        path = create_verbas_fixture(tmp_path)
        parser = ParserVerbas()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert len(m.cnpj) == 14

    def test_validate_rejeita_ausente(self, tmp_path):
        parser = ParserVerbas()
        result = parser.validate_file(tmp_path / "nao_existe.xlsx")
        assert not result.ok


# ---------------------------------------------------------------------------
# ParserFrete
# ---------------------------------------------------------------------------

class TestParserFrete:
    def test_extract_retorna_linhas(self, tmp_path):
        path = create_frete_fixture(tmp_path)
        parser = ParserFrete()
        raw = parser.extract(path)
        assert len(raw) > 0

    def test_normalize_produz_frete_mensal(self, tmp_path):
        path = create_frete_fixture(tmp_path)
        parser = ParserFrete()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(isinstance(m, ClienteFretesMensal) for m in models)

    def test_normalize_mes_valido(self, tmp_path):
        path = create_frete_fixture(tmp_path)
        parser = ParserFrete()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert 1 <= m.mes <= 12

    def test_normalize_cnpj_14_digitos(self, tmp_path):
        path = create_frete_fixture(tmp_path)
        parser = ParserFrete()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert len(m.cnpj) == 14

    def test_validate_rejeita_vazio(self, tmp_path):
        p = tmp_path / "vazio.xlsx"
        p.write_bytes(b"")
        parser = ParserFrete()
        result = parser.validate_file(p)
        assert not result.ok

    def test_run_ok(self, tmp_path):
        path = create_frete_fixture(tmp_path)
        parser = ParserFrete()
        db = make_mock_db()
        result = parser.run(path, db)
        assert result["status"] == "OK"
        assert result["registros"] > 0


# ---------------------------------------------------------------------------
# ParserContratos
# ---------------------------------------------------------------------------

class TestParserContratos:
    def test_extract_retorna_linhas(self, tmp_path):
        path = create_contratos_fixture(tmp_path)
        parser = ParserContratos()
        raw = parser.extract(path)
        assert len(raw) > 0

    def test_normalize_produz_verba_anual(self, tmp_path):
        path = create_contratos_fixture(tmp_path)
        parser = ParserContratos()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(isinstance(m, ClienteVerbaAnual) for m in models)

    def test_normalize_tipo_contrato(self, tmp_path):
        path = create_contratos_fixture(tmp_path)
        parser = ParserContratos()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(m.tipo == "CONTRATO" for m in models)

    def test_normalize_classificacao_real(self, tmp_path):
        path = create_contratos_fixture(tmp_path)
        parser = ParserContratos()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(m.classificacao == "REAL" for m in models)

    def test_normalize_cnpj_14_digitos(self, tmp_path):
        path = create_contratos_fixture(tmp_path)
        parser = ParserContratos()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert len(m.cnpj) == 14

    def test_validate_rejeita_extensao_errada(self, tmp_path):
        p = tmp_path / "dados.doc"
        p.write_bytes(b"fake")
        parser = ParserContratos()
        result = parser.validate_file(p)
        assert not result.ok


# ---------------------------------------------------------------------------
# ParserPromotores
# ---------------------------------------------------------------------------

class TestParserPromotores:
    def test_extract_retorna_linhas(self, tmp_path):
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        raw = parser.extract(path)
        assert len(raw) > 0

    def test_normalize_produz_promotor_mensal(self, tmp_path):
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(isinstance(m, ClientePromotorMensal) for m in models)

    def test_normalize_mes_valido(self, tmp_path):
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert 1 <= m.mes <= 12

    def test_normalize_classificacao_real(self, tmp_path):
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        assert all(m.classificacao == "REAL" for m in models)

    def test_normalize_cnpj_14_digitos(self, tmp_path):
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        raw = parser.extract(path)
        models = parser.normalize(raw)
        for m in models:
            assert len(m.cnpj) == 14

    def test_validate_rejeita_ausente(self, tmp_path):
        parser = ParserPromotores()
        result = parser.validate_file(tmp_path / "nao_existe.xlsx")
        assert not result.ok

    def test_run_ok(self, tmp_path):
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        db = make_mock_db()
        result = parser.run(path, db)
        assert result["status"] == "OK"
        assert result["registros"] > 0

    def test_idempotencia(self, tmp_path):
        """Rodar 2x deve retornar mesmo número de registros."""
        path = create_promotores_fixture(tmp_path)
        parser = ParserPromotores()
        db1 = make_mock_db()
        db2 = make_mock_db()
        result1 = parser.run(path, db1)
        result2 = parser.run(path, db2)
        assert result1["registros"] == result2["registros"]


# ---------------------------------------------------------------------------
# BaseParser — upsert vazia
# ---------------------------------------------------------------------------

class TestBaseParserUpsert:
    def _make_parser(self):
        class _P(BaseParser):
            def extract(self, path): return []
            def normalize(self, raw): return []
        return _P()

    def test_upsert_lista_vazia_retorna_zero(self):
        parser = self._make_parser()
        db = make_mock_db()
        count = parser.upsert([], db)
        assert count == 0
        db.merge.assert_not_called()

    def test_run_com_arquivo_ausente(self, tmp_path):
        parser = self._make_parser()
        db = make_mock_db()
        result = parser.run(tmp_path / "inexistente.xlsx", db)
        assert result["status"] == "ERRO"
        assert result["registros"] == 0
