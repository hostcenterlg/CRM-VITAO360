#!/usr/bin/env python3
"""
CRM VITAO360 — classificar_clientes_legado.py
==============================================
Reclassifica clientes Mercos pre-SAP (canal_id IS NULL) atribuindo
canal_id baseado no consultor responsavel.

DECISAO L3 (Leandro 25/Apr/2026):
  Daiane = INTERNO + FOOD_SERVICE (gerente desses canais)
  Manu / Larissa / Julio = DIRETO (vendedores B2B classicos)

Heuristica aplicada:
  consultor IN ('MANU', 'LARISSA', 'JULIO') AND canal_id IS NULL
    -> canal=DIRETO (id=3)

  DAIANE: NAO reclassifica automaticamente. Razao: Daiane hoje atende
  INTERNO + FOOD, mas seus clientes Mercos historicos podem pertencer a
  qualquer canal antigo. Atribuir DIRETO seria incorreto para os de
  INTERNO/FOOD; atribuir INTERNO/FOOD para todos seria igualmente
  incorreto. Daiane reclassifica manualmente via CRM (TODO admin UI).

Idempotente: rerun nao re-classifica (WHERE canal_id IS NULL).
Modo --dry-run: mostra o impacto sem persistir.

REGRAS:
  R8 — nao inventa: somente atribui DIRETO se consultor mapear
  R11 — idempotencia: rerun nao duplica nem reescreve canal_id != NULL

Uso:
  python scripts/classificar_clientes_legado.py
  python scripts/classificar_clientes_legado.py --dry-run
  python scripts/classificar_clientes_legado.py --db-path data/crm_vitao360.db
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _load_env_file(path: Path, override_when_empty: bool = True) -> None:
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if not v:
                continue
            atual = os.environ.get(k, "")
            if not atual or override_when_empty:
                os.environ[k] = v
    except OSError:
        pass


_load_env_file(PROJECT_ROOT / ".env", override_when_empty=False)
_load_env_file(PROJECT_ROOT / ".env.local", override_when_empty=True)

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"sqlite:///{PROJECT_ROOT / 'data' / 'crm_vitao360.db'}"


from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
log = logging.getLogger("classificar_legado")


# DECISAO L3: consultores que mapeiam diretamente para DIRETO
CONSULTORES_DIRETO = ("MANU", "LARISSA", "JULIO")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Nao grava no banco")
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path SQLite arbitrario (override de DATABASE_URL)",
    )
    args = parser.parse_args()

    if args.db_path:
        db_path = Path(args.db_path)
        if not db_path.is_absolute():
            db_path = PROJECT_ROOT / db_path
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        log.info("DATABASE_URL override: sqlite:///%s", db_path)

    db_url = os.environ["DATABASE_URL"]
    log.info("Conectando: %s", db_url.split("@")[-1] if "@" in db_url else db_url)

    engine = create_engine(db_url, future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()

    try:
        # 1. Resolve canal DIRETO id
        diretto_id = session.execute(
            text("SELECT id FROM canais WHERE nome = 'DIRETO'")
        ).scalar()
        if diretto_id is None:
            log.error(
                "Canal DIRETO nao encontrado em canais. "
                "Aplicar migration multi-canal antes de rodar este script."
            )
            return 1

        # 2. Snapshot pre-execucao
        log.info("=== SNAPSHOT PRE-EXECUCAO ===")
        for r in session.execute(text("""
            SELECT
              COALESCE(consultor, '(sem consultor)') AS cons,
              COUNT(*) AS n,
              ROUND(COALESCE(SUM(faturamento_total), 0), 2) AS fat
            FROM clientes
            WHERE canal_id IS NULL
            GROUP BY consultor
            ORDER BY n DESC
        """)).fetchall():
            log.info("  consultor=%s n=%d fat=R$ %.2f", r[0], r[1], r[2] or 0)

        # 3. Conta quantos vao ser afetados
        sql_target = """
            SELECT COUNT(*) FROM clientes
            WHERE canal_id IS NULL
              AND consultor IN ('MANU', 'LARISSA', 'JULIO')
        """
        n_alvo = session.execute(text(sql_target)).scalar() or 0
        log.info(
            "=== ALVO: %d clientes (canal NULL + consultor in MANU/LARISSA/JULIO) -> DIRETO id=%d ===",
            n_alvo, diretto_id,
        )

        if n_alvo == 0:
            log.info("Nada a fazer (idempotente).")
            return 0

        # 4. Executa o UPDATE (ou simula em dry-run)
        if args.dry_run:
            log.info("[DRY RUN] UPDATE seria executado em %d linhas, sem gravar.", n_alvo)
        else:
            result = session.execute(text("""
                UPDATE clientes
                SET canal_id = :canal_id,
                    updated_at = CURRENT_TIMESTAMP
                WHERE canal_id IS NULL
                  AND consultor IN ('MANU', 'LARISSA', 'JULIO')
            """), {"canal_id": diretto_id})
            session.commit()
            log.info("UPDATE OK: %d linhas afetadas (commit)", result.rowcount)

        # 5. Snapshot pos-execucao
        log.info("=== SNAPSHOT POS-EXECUCAO ===")
        for r in session.execute(text("""
            SELECT
              COALESCE(ca.nome, '(sem canal)') AS canal,
              COUNT(*) AS n,
              ROUND(COALESCE(SUM(c.faturamento_total), 0), 2) AS fat
            FROM clientes c LEFT JOIN canais ca ON ca.id = c.canal_id
            GROUP BY ca.nome
            ORDER BY fat DESC
        """)).fetchall():
            log.info("  canal=%s n=%d fat=R$ %.2f", r[0], r[1], r[2] or 0)

        # 6. Daiane breakdown (informativo — TODO manual)
        n_daiane_null = session.execute(text("""
            SELECT COUNT(*) FROM clientes
            WHERE canal_id IS NULL AND consultor = 'DAIANE'
        """)).scalar() or 0
        if n_daiane_null:
            log.info(
                "DAIANE: %d clientes legados ainda canal=NULL — Daiane reclassifica manualmente "
                "(INTERNO/FOOD/DIRETO conforme caso).",
                n_daiane_null,
            )

        return 0

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
