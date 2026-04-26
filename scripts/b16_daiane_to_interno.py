#!/usr/bin/env python3
"""
CRM VITAO360 — b16_daiane_to_interno.py
========================================

Missao (B1.6-EXEC — L3#4 aprovado por Leandro 26/Abr/2026):
  Classificar 194 clientes da DAIANE com canal_id IS NULL
  para o canal INTERNO (canal_id=1).

Contexto:
  Apos a migration f557927e169e (multi-canal), clientes DAIANE
  ficaram com canal_id=NULL porque o script classificar_clientes_legado.py
  deliberadamente nao classificou DAIANE automaticamente (aguardando
  decisao manual). Leandro aprovou: DAIANE -> INTERNO.

Regra de negocio:
  DAIANE = gerente de Key Accounts + redes/franquias.
  Seus clientes pertencem ao canal INTERNO (funcional VITAO).

REGRAS INVIOLAVEIS:
  R4  Two-Base: este script NAO toca valores monetarios.
  R5  CNPJ: string 14 digitos, nunca alterado.
  R8  Nenhum cliente e deletado — apenas canal_id e atualizado.
  R11 Idempotente: re-executar nao altera clientes ja classificados.
  R12 L3 aprovado — Leandro 26/Abr/2026.

Uso:
  python scripts/b16_daiane_to_interno.py
  python scripts/b16_daiane_to_interno.py --dry-run

Pre-condicao:  canal INTERNO (id=1) existe em canais.
Pos-condicao:  clientes WHERE consultor='DAIANE' AND canal_id IS NULL = 0.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "crm_vitao360.db"
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("b16_daiane_to_interno")

CANAL_INTERNO_ID = 1
CONSULTOR = "DAIANE"


def run(dry_run: bool = False) -> None:
    if not DB_PATH.exists():
        logger.error(f"Banco nao encontrado: {DB_PATH}")
        sys.exit(1)

    engine = create_engine(
        f"sqlite:///{DB_PATH}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Pre-validacao: verificar canal INTERNO existe
        row = session.execute(
            text("SELECT id, nome FROM canais WHERE id = :id"),
            {"id": CANAL_INTERNO_ID},
        ).fetchone()
        if row is None:
            logger.error(f"Canal INTERNO (id={CANAL_INTERNO_ID}) nao encontrado. Abortando.")
            sys.exit(1)
        logger.info(f"Canal encontrado: id={row[0]}, nome={row[1]}")

        # Contar alvos
        count_pre = session.execute(
            text(
                "SELECT COUNT(*) FROM clientes "
                "WHERE canal_id IS NULL AND consultor = :consultor"
            ),
            {"consultor": CONSULTOR},
        ).scalar()
        logger.info(f"Pre: clientes DAIANE com canal_id NULL = {count_pre}")

        if count_pre == 0:
            logger.info("Nenhum cliente para classificar (idempotente). Nada a fazer.")
            return

        if dry_run:
            logger.info(
                f"[DRY-RUN] Seriam atualizados {count_pre} clientes DAIANE "
                f"-> canal_id={CANAL_INTERNO_ID} (INTERNO)."
            )
            return

        # UPDATE
        result = session.execute(
            text(
                "UPDATE clientes SET canal_id = :canal_id "
                "WHERE canal_id IS NULL AND consultor = :consultor"
            ),
            {"canal_id": CANAL_INTERNO_ID, "consultor": CONSULTOR},
        )
        session.commit()
        logger.info(f"UPDATE aplicado: {result.rowcount} rows afetadas.")

        # Pos-validacao
        count_pos = session.execute(
            text(
                "SELECT COUNT(*) FROM clientes "
                "WHERE canal_id IS NULL AND consultor = :consultor"
            ),
            {"consultor": CONSULTOR},
        ).scalar()
        logger.info(f"Pos: clientes DAIANE com canal_id NULL = {count_pos} (esperado 0)")

        count_interno = session.execute(
            text("SELECT COUNT(*) FROM clientes WHERE canal_id = :id"),
            {"id": CANAL_INTERNO_ID},
        ).scalar()
        logger.info(f"Pos: total clientes canal INTERNO (id={CANAL_INTERNO_ID}) = {count_interno}")

        if count_pos != 0:
            logger.error("FALHA: ainda ha clientes DAIANE com canal_id NULL apos update!")
            sys.exit(1)

        print()
        print("=" * 60)
        print("B1.6-EXEC CONCLUIDO — L3#4")
        print("=" * 60)
        print(f"  Clientes DAIANE classificados -> INTERNO: {result.rowcount}")
        print(f"  Canal INTERNO total agora:                {count_interno}")
        print(f"  DAIANE NULL restantes:                    {count_pos}")
        print("  STATUS: OK")
        print("=" * 60)

    except Exception:
        session.rollback()
        logger.exception("Erro — rollback executado.")
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="B1.6: Classifica 194 clientes DAIANE NULL -> canal INTERNO."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Mostra o que seria feito sem gravar no banco.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(dry_run=args.dry_run)
