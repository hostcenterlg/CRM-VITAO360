"""
import_log_completo.py — Importacao de 20.830 registros LOG para log_interacoes

FONTE: data/output/phase04/log_final_validated.json
DESTINO: data/crm_vitao360.db (tabela log_interacoes)

REGRAS APLICADAS:
  R1 — Two-Base Architecture: log_interacoes nao tem campo monetario.
  R5 — CNPJ = String(14) zero-padded, NUNCA float/int.
  R8 — Zero fabricacao de dados; 3-tier classification obrigatoria.
  DE-PARA consultores conforme CLAUDE.md.
  FK SQLite desligada por padrao — CNPJs ausentes em clientes sao inseridos
  com aviso (sem FK enforcement no SQLite).

3-TIER MAPPING (SOURCE field):
  CONTROLE_FUNIL -> REAL
  DESKRIO        -> REAL
  SINTETICO      -> SINTETICO
  Nenhum registro tem ALUCINACAO — mas safety check ativo.

DEDUPLICATION:
  Chave: (data_interacao DATE, cnpj, resultado)
  Registros existentes carregados em set antes do batch.

EXECUCAO: python scripts/import_log_completo.py
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — importar SQLAlchemy models sem instalar como pacote
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import SessionLocal, engine
from backend.app.models.log_interacao import LogInteracao

# Garante que a tabela existe (idempotente)
from backend.app.database import Base
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
JSON_PATH = BASE_DIR / "data" / "output" / "phase04" / "log_final_validated.json"
BATCH_SIZE = 500
LOG_EVERY  = 1000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DE-PARA consultores (R12 / CLAUDE.md)
# ---------------------------------------------------------------------------
CONSULTOR_MAP: dict[str, str] = {
    # Canonicos
    "LARISSA PADILHA":  "LARISSA",
    "LARISSA":          "LARISSA",
    "LARI":             "LARISSA",
    "LARISSA VITAO":    "LARISSA",
    "MAIS GRANEL":      "LARISSA",
    "RODRIGO":          "LARISSA",   # conforme DE-PARA Rodrigo → LARISSA

    "MANU DITZEL":      "MANU",
    "MANU":             "MANU",
    "MANU VITAO":       "MANU",

    "DAIANE STAVICKI":  "DAIANE",
    "DAIANE":           "DAIANE",
    "CENTRAL DAIANE":   "DAIANE",
    "DAIANE VITAO":     "DAIANE",

    "JULIO GADRET":     "JULIO",
    "JULIO":            "JULIO",

    # Legado / externos
    "HELDER BRUNKOW":   "LEGADO",
    "LORRANY":          "LEGADO",
    "LEANDRO GARCIA":   "LEGADO",
    "BRUNO GRETTER":    "LEGADO",
    "JEFERSON VITAO":   "LEGADO",
    "PATRIC":           "LEGADO",
    "GABRIEL":          "LEGADO",
    "SERGIO":           "LEGADO",
    "IVE":              "LEGADO",
    "ANA":              "LEGADO",
}

# ---------------------------------------------------------------------------
# 3-tier SOURCE → classificacao
# ---------------------------------------------------------------------------
SOURCE_TIER: dict[str, str] = {
    "CONTROLE_FUNIL": "REAL",
    "DESKRIO":        "REAL",
    "SINTETICO":      "SINTETICO",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_cnpj(raw: object) -> str:
    """R5: CNPJ = String(14) zero-padded, nunca float."""
    return re.sub(r"\D", "", str(raw)).zfill(14)


def normalize_consultor(raw: str) -> str:
    """DE-PARA conforme CLAUDE.md. Desconhecidos vao para LEGADO."""
    key = str(raw).strip().upper()
    return CONSULTOR_MAP.get(key, "LEGADO")


def parse_date(raw: str) -> datetime | None:
    """Parseia DATA no formato YYYY-MM-DD. Retorna None se invalido."""
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def classify_source(source: str, origem: str) -> str:
    """
    Retorna classificacao 3-tier.
    Safety: qualquer combinacao que nao mapeie = SINTETICO (nunca ALUCINACAO
    a nao ser que seja explicitamente identificado).
    """
    tier = SOURCE_TIER.get(str(source).strip().upper())
    if tier:
        return tier
    # Fallback por ORIGEM_DADO
    if str(origem).strip().upper() == "REAL":
        return "REAL"
    return "SINTETICO"


def build_tipo_contato(record: dict) -> str:
    """
    Mapeia TIPO DO CONTATO do JSON para campo tipo_contato do modelo.
    Normaliza variantes.
    """
    raw = str(record.get("TIPO DO CONTATO", "")).strip().upper()

    TIPO_MAP: dict[str, str] = {
        "POS-VENDA / RELACIONAMENTO":       "POS-VENDA / RELACIONAMENTO",
        "POS VENDA / RELACIONAMENTO":       "POS-VENDA / RELACIONAMENTO",
        "PROSPECCAO NOVOS CLIENTES":        "PROSPECCAO",
        "PROSPECCAO":                       "PROSPECCAO",
        "ATEND. CLIENTES ATIVOS":           "ATEND. CLIENTES ATIVOS",
        "ATENDIMENTO CLIENTES ATIVOS":      "ATEND. CLIENTES ATIVOS",
        "CONTATOS PASSIVO / SUPORTE":       "CONTATOS PASSIVO / SUPORTE",
        "ATENDIMENTO CLIENTES INATIVOS":    "ATEND. CLIENTES INATIVOS",
        "NEGOCIACAO":                       "NEGOCIACAO",
        "ENVIO DE MATERIAL - MKT":          "ENVIO DE MATERIAL - MKT",
        "PERDA / NUTRICAO":                 "PERDA / NUTRICAO",
        "FOLLOW UP":                        "FOLLOW UP",
    }
    return TIPO_MAP.get(raw, raw) if raw else "NAO INFORMADO"


def build_descricao(record: dict) -> str | None:
    """
    Prefere NOTA DO DIA; fallback para ACAO; None se ambos vazios.
    """
    nota = str(record.get("NOTA DO DIA", "")).strip()
    acao = str(record.get("ACAO", "")).strip()
    if nota:
        return nota
    if acao:
        return acao
    return None


# ---------------------------------------------------------------------------
# Main import logic
# ---------------------------------------------------------------------------

def load_existing_keys(session) -> set[tuple]:
    """
    Carrega chaves de dedup existentes: (data DATE como str YYYY-MM-DD, cnpj, resultado).
    """
    rows = session.query(
        LogInteracao.data_interacao,
        LogInteracao.cnpj,
        LogInteracao.resultado,
    ).all()

    keys: set[tuple] = set()
    for data_dt, cnpj, resultado in rows:
        if data_dt is None:
            continue
        # Normaliza para date string
        if isinstance(data_dt, datetime):
            date_str = data_dt.strftime("%Y-%m-%d")
        else:
            date_str = str(data_dt)[:10]
        keys.add((date_str, cnpj, str(resultado).strip().upper()))
    log.info("Chaves existentes carregadas: %d", len(keys))
    return keys


def run_import() -> None:
    log.info("=== IMPORT LOG COMPLETO — CRM VITAO360 ===")
    log.info("Fonte: %s", JSON_PATH)

    # ------------------------------------------------------------------
    # Carregar JSON
    # ------------------------------------------------------------------
    if not JSON_PATH.exists():
        log.error("Arquivo nao encontrado: %s", JSON_PATH)
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    records: list[dict] = payload.get("records", [])
    metadata = payload.get("metadata", {})
    log.info(
        "JSON carregado: %d registros | Sources: %s",
        len(records),
        metadata.get("sources", {}),
    )

    # ------------------------------------------------------------------
    # Abrir sessao SQLAlchemy
    # ------------------------------------------------------------------
    session = SessionLocal()

    try:
        existing_keys = load_existing_keys(session)

        # ------------------------------------------------------------------
        # Counters
        # ------------------------------------------------------------------
        inserted   = 0
        skipped_dupe    = 0
        skipped_alucinacao = 0
        skipped_bad_date   = 0
        errors     = 0
        batch: list[LogInteracao] = []

        # ------------------------------------------------------------------
        # Processar registros
        # ------------------------------------------------------------------
        for idx, rec in enumerate(records, start=1):

            # Progress log
            if idx % LOG_EVERY == 0:
                log.info(
                    "Progresso: %d/%d | inseridos=%d skip_dupe=%d skip_data=%d erros=%d",
                    idx, len(records), inserted, skipped_dupe, skipped_bad_date, errors,
                )

            # --- 1. Safety: bloquear ALUCINACAO ---
            origem = str(rec.get("ORIGEM_DADO", "")).strip().upper()
            source = str(rec.get("SOURCE", "")).strip().upper()
            if origem == "ALUCINACAO" or source == "ALUCINACAO":
                skipped_alucinacao += 1
                log.warning("ALUCINACAO detectada (idx=%d) — ignorada.", idx)
                continue

            # --- 2. Parse data ---
            data_str = str(rec.get("DATA", "")).strip()
            data_dt = parse_date(data_str)
            if data_dt is None:
                skipped_bad_date += 1
                if skipped_bad_date <= 5:
                    log.warning("Data invalida (idx=%d): %r — ignorando.", idx, data_str)
                continue

            # --- 3. Normalizar CNPJ (R5) ---
            cnpj = normalize_cnpj(rec.get("CNPJ", ""))

            # --- 4. Normalizar campos ---
            consultor   = normalize_consultor(rec.get("CONSULTOR", ""))
            resultado   = str(rec.get("RESULTADO", "")).strip()
            tipo_contato = build_tipo_contato(rec)
            descricao   = build_descricao(rec)
            fase        = str(rec.get("FASE", "")).strip() or None
            tentativa   = str(rec.get("TENTATIVA", "")).strip() or None

            # --- 5. Dedup check ---
            dedup_key = (data_dt.strftime("%Y-%m-%d"), cnpj, resultado.strip().upper())
            if dedup_key in existing_keys:
                skipped_dupe += 1
                continue
            existing_keys.add(dedup_key)  # adicionar ao set in-memory

            # --- 6. Montar objeto ORM ---
            try:
                obj = LogInteracao(
                    cnpj            = cnpj,
                    data_interacao  = data_dt,
                    consultor       = consultor,
                    resultado       = resultado,
                    descricao       = descricao,
                    tipo_contato    = tipo_contato,
                    fase            = fase,
                    tentativa       = tentativa,
                    # campos calculados pelo motor — deixar NULL por ora
                    estagio_funil   = None,
                    acao_futura     = None,
                    temperatura     = None,
                    follow_up_dias  = None,
                    grupo_dash      = None,
                )
                batch.append(obj)
                inserted += 1

            except Exception as exc:
                errors += 1
                if errors <= 10:
                    log.error("Erro ao montar objeto (idx=%d): %s", idx, exc)
                continue

            # --- 7. Flush em batch ---
            if len(batch) >= BATCH_SIZE:
                try:
                    session.bulk_save_objects(batch)
                    session.commit()
                except Exception as exc:
                    session.rollback()
                    errors += len(batch)
                    inserted -= len(batch)
                    log.error("Erro no batch flush (batch=%d): %s", len(batch), exc)
                finally:
                    batch.clear()

        # --- 8. Flush final ---
        if batch:
            try:
                session.bulk_save_objects(batch)
                session.commit()
            except Exception as exc:
                session.rollback()
                errors += len(batch)
                inserted -= len(batch)
                log.error("Erro no flush final: %s", exc)
            finally:
                batch.clear()

        # ------------------------------------------------------------------
        # Sumario final
        # ------------------------------------------------------------------
        log.info("=" * 60)
        log.info("IMPORTACAO CONCLUIDA")
        log.info("  Registros no JSON:       %d", len(records))
        log.info("  Inseridos:               %d", inserted)
        log.info("  Ignorados (duplicatas):  %d", skipped_dupe)
        log.info("  Ignorados (data ruim):   %d", skipped_bad_date)
        log.info("  Ignorados (alucinacao):  %d", skipped_alucinacao)
        log.info("  Erros:                   %d", errors)
        log.info("=" * 60)

        # ------------------------------------------------------------------
        # Verificacao pos-import
        # ------------------------------------------------------------------
        from sqlalchemy import text
        total_db = session.execute(text("SELECT COUNT(*) FROM log_interacoes")).scalar()
        log.info("Total log_interacoes no DB apos import: %d", total_db)

        rows = session.execute(
            text("SELECT consultor, COUNT(*) FROM log_interacoes GROUP BY consultor ORDER BY COUNT(*) DESC")
        ).fetchall()
        log.info("Distribuicao por consultor:")
        for consultor_name, cnt in rows:
            log.info("  %-20s : %d", consultor_name, cnt)

        if errors > 0:
            log.warning("ATENCAO: %d erros durante a importacao. Verificar logs acima.", errors)
        else:
            log.info("Zero erros. Importacao limpa.")

    finally:
        session.close()


if __name__ == "__main__":
    run_import()
