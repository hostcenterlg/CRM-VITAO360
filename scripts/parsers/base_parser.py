"""
CRM VITAO360 — base_parser.py
================================
BaseParser ABC para parsers de arquivos XLSX do pipeline DDE/AC.

Pipeline padrao (run):
  validate_file(path) -> ValidationResult
    -> extract(path)     -> list[dict]    (raw rows do XLSX)
    -> normalize(raw)    -> list[Model]   (modelos SQLAlchemy)
    -> upsert(models, db) -> int          (registros persistidos)
  -> dict de resultado

Cada parser especifico herda BaseParser e implementa extract() e normalize().

Referencia: docs/specs/cowork/README_TIME_TECNICO_DDE_AC.md secao 7.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Tamanho maximo tolerado para upload (50 MB — proteção contra arquivos gigantes)
_MAX_FILE_BYTES = 50 * 1024 * 1024

# Extensoes aceitas pelos parsers DDE
_ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}


@dataclass
class ValidationResult:
    """
    Resultado da validacao de arquivo pre-parse.

    Atributos:
      ok     — True se arquivo passou em todas as verificacoes
      errors — lista de mensagens de erro (vazia se ok=True)
      warnings — avisos nao-bloqueantes
    """

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.ok = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


class BaseParser(ABC):
    """
    Classe base para todos os parsers DDE/AC.

    Subclasses devem implementar:
      extract(path)    — le o XLSX e retorna linhas como list[dict]
      normalize(raw)   — converte list[dict] em list[Model SQLAlchemy]

    Atributo de classe:
      FONTE — string que identifica a fonte de upload (ex.: 'LOG_UPLOAD', 'SAP')
    """

    FONTE: str = "LOG_UPLOAD"

    # -----------------------------------------------------------------------
    # Validacao de arquivo
    # -----------------------------------------------------------------------

    def validate_file(self, path: str | Path) -> ValidationResult:
        """
        Valida pre-condicoes do arquivo antes do parse:
          1. Existencia
          2. Extensao (.xlsx ou .xlsm)
          3. Tamanho > 0 bytes
          4. Tamanho <= _MAX_FILE_BYTES

        Retorna ValidationResult com ok=True se tudo passou.
        """
        result = ValidationResult(ok=True)
        p = Path(path)

        if not p.exists():
            result.add_error(f"Arquivo nao encontrado: {p}")
            return result

        if p.suffix.lower() not in _ALLOWED_EXTENSIONS:
            result.add_error(
                f"Extensao invalida: {p.suffix!r}. "
                f"Aceito: {sorted(_ALLOWED_EXTENSIONS)}"
            )

        size = p.stat().st_size
        if size == 0:
            result.add_error(f"Arquivo vazio (0 bytes): {p.name}")
        elif size > _MAX_FILE_BYTES:
            result.add_error(
                f"Arquivo muito grande: {size / 1024 / 1024:.1f} MB "
                f"(limite: {_MAX_FILE_BYTES // 1024 // 1024} MB)"
            )

        return result

    # -----------------------------------------------------------------------
    # Metodos abstratos (implementar em cada parser)
    # -----------------------------------------------------------------------

    @abstractmethod
    def extract(self, path: str | Path) -> list[dict]:
        """
        Le o arquivo XLSX e retorna lista de dicionarios com as linhas brutas.

        Cada dict deve conter as colunas relevantes sem transformacoes.
        Linhas invalidas devem ser puladas com log WARNING (nunca crashar).
        """

    @abstractmethod
    def normalize(self, raw: list[dict]) -> list[Any]:
        """
        Converte lista de dicts brutos em lista de modelos SQLAlchemy.

        Deve aplicar:
          - Normalizacao CNPJ (R5: 14 digitos string zero-padded)
          - Conversao de valores para Decimal
          - classificacao='REAL' por padrao
          - Filtragem de linhas com dados insuficientes (log WARNING)
        """

    # -----------------------------------------------------------------------
    # Upsert generico
    # -----------------------------------------------------------------------

    def upsert(self, models: list[Any], db: Any) -> int:
        """
        Persiste lista de modelos no banco usando UPSERT via db.merge().

        db.merge() faz INSERT OR UPDATE baseado nas UNIQUE constraints
        ja definidas nos modelos SQLAlchemy (equivalente a ON CONFLICT DO UPDATE).

        Retorna numero de registros persistidos com sucesso.
        """
        if not models:
            logger.warning("[%s] upsert chamado com lista vazia", self.__class__.__name__)
            return 0

        count = 0
        errors = 0
        for model in models:
            try:
                db.merge(model)
                count += 1
            except Exception as exc:
                errors += 1
                logger.error(
                    "[%s] Erro ao persistir %r: %s",
                    self.__class__.__name__,
                    model,
                    exc,
                )

        if count > 0:
            try:
                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error("[%s] Erro no commit: %s", self.__class__.__name__, exc)
                raise

        if errors:
            logger.warning(
                "[%s] %d registros falharam de %d tentados",
                self.__class__.__name__,
                errors,
                len(models),
            )

        logger.info("[%s] Upsert: %d registros persistidos", self.__class__.__name__, count)
        return count

    # -----------------------------------------------------------------------
    # Pipeline completo
    # -----------------------------------------------------------------------

    def run(self, path: str | Path, db: Any) -> dict:
        """
        Executa o pipeline completo: validate -> extract -> normalize -> upsert.

        Retorna dict com:
          status    — 'OK' | 'ERRO'
          registros — int (0 em caso de erro)
          warnings  — list[str]
          errors    — list[str] (vazio se OK)
          fonte     — self.FONTE
        """
        result: dict = {
            "status": "OK",
            "registros": 0,
            "warnings": [],
            "errors": [],
            "fonte": self.FONTE,
        }

        # --- 1. Validacao
        validation = self.validate_file(path)
        result["warnings"].extend(validation.warnings)
        if not validation.ok:
            result["status"] = "ERRO"
            result["errors"].extend(validation.errors)
            logger.error(
                "[%s] Validacao falhou: %s",
                self.__class__.__name__,
                validation.errors,
            )
            return result

        # --- 2. Extract
        try:
            raw = self.extract(path)
        except Exception as exc:
            result["status"] = "ERRO"
            result["errors"].append(f"Erro na extracao: {exc}")
            logger.error("[%s] extract falhou: %s", self.__class__.__name__, exc)
            return result

        if not raw:
            result["warnings"].append("Nenhuma linha extraida do arquivo")
            logger.warning("[%s] extract retornou lista vazia", self.__class__.__name__)
            return result

        # --- 3. Normalize
        try:
            models = self.normalize(raw)
        except Exception as exc:
            result["status"] = "ERRO"
            result["errors"].append(f"Erro na normalizacao: {exc}")
            logger.error("[%s] normalize falhou: %s", self.__class__.__name__, exc)
            return result

        if not models:
            result["warnings"].append("Normalizacao produziu lista vazia (dados invalidos?)")
            return result

        # --- 4. Upsert
        try:
            count = self.upsert(models, db)
            result["registros"] = count
        except Exception as exc:
            result["status"] = "ERRO"
            result["errors"].append(f"Erro no upsert: {exc}")
            logger.error("[%s] upsert falhou: %s", self.__class__.__name__, exc)
            return result

        logger.info(
            "[%s] Pipeline concluido: %d registros | fonte=%s",
            self.__class__.__name__,
            count,
            self.FONTE,
        )
        return result
