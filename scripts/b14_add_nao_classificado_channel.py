#!/usr/bin/env python3
"""
CRM VITAO360 — b14_add_nao_classificado_channel.py
====================================================

Missao (B1.4-EXEC — L3#3 aprovado por Leandro 26/Abr/2026):
  1. Canal NAO_CLASSIFICADO (id=8) ja inserido via migration Alembic
     4db41d4977b6. Este script atribui os clientes orfaos ao canal 8.

  2. Atribuir canal_id=8 a TODOS os clientes com canal_id IS NULL
     (84 clientes apos a execucao de B1.6 que classificou DAIANE).

Visibilidade do canal 8:
  - Admin: ve automaticamente (get_user_canal_ids retorna None -> sem filtro;
    get_user_canal_ids_strict faz SELECT id FROM canais -> inclui 8).
  - Consultor: nao ve (nenhuma ACL em usuario_canal para canal 8 sera inserida).
  - Nenhuma alteracao em backend/app/api/deps.py necessaria.

REGRAS INVIOLAVEIS:
  R4  Two-Base: este script NAO toca valores monetarios.
  R5  CNPJ: string 14 digitos, nunca alterado.
  R8  Nenhum cliente e deletado — apenas canal_id e atualizado.
  R11 Idempotente: re-executar nao altera clientes ja com canal_id != NULL.
  R12 L3 aprovado — Leandro 26/Abr/2026.

Pre-condicao:  migration 4db41d4977b6 aplicada (canal id=8 existe).
Pos-condicao:  SELECT COUNT(*) FROM clientes WHERE canal_id IS NULL = 0.

Uso:
  python scripts/b14_add_nao_classificado_channel.py
  python scripts/b14_add_nao_classificado_channel.py --dry-run
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
logger = logging.getLogger("b14_nao_classificado")

CANAL_NAO_CLASSIFICADO_ID = 8


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
        # Pre-condicao: canal 8 deve existir (migration aplicada)
        canal = session.execute(
            text("SELECT id, nome, status FROM canais WHERE id = :id"),
            {"id": CANAL_NAO_CLASSIFICADO_ID},
        ).fetchone()
        if canal is None:
            logger.error(
                f"Canal id={CANAL_NAO_CLASSIFICADO_ID} nao encontrado. "
                "Aplicar migration 4db41d4977b6 antes de rodar este script."
            )
            sys.exit(1)
        logger.info(f"Canal encontrado: id={canal[0]}, nome={canal[1]}, status={canal[2]}")

        # Contar orfaos
        count_null = session.execute(
            text("SELECT COUNT(*) FROM clientes WHERE canal_id IS NULL")
        ).scalar()
        logger.info(f"Pre: clientes com canal_id NULL = {count_null}")

        if count_null == 0:
            logger.info("Nenhum orfao encontrado (idempotente). Nada a fazer.")
            return

        if dry_run:
            logger.info(
                f"[DRY-RUN] Seriam atribuidos {count_null} clientes orfaos "
                f"-> canal_id={CANAL_NAO_CLASSIFICADO_ID} (NAO_CLASSIFICADO)."
            )
            # Detalhar os consultores envolvidos
            resultado = session.execute(
                text(
                    "SELECT consultor, COUNT(*) as qt FROM clientes "
                    "WHERE canal_id IS NULL GROUP BY consultor ORDER BY qt DESC"
                )
            ).fetchall()
            for consultor, qt in resultado:
                logger.info(f"  [DRY-RUN] {consultor or 'NULL':<20} {qt:>5}")
            return

        # UPDATE
        result = session.execute(
            text(
                "UPDATE clientes SET canal_id = :canal_id "
                "WHERE canal_id IS NULL"
            ),
            {"canal_id": CANAL_NAO_CLASSIFICADO_ID},
        )
        session.commit()
        logger.info(f"UPDATE aplicado: {result.rowcount} rows afetadas.")

        # Pos-validacao
        count_null_pos = session.execute(
            text("SELECT COUNT(*) FROM clientes WHERE canal_id IS NULL")
        ).scalar()
        count_8 = session.execute(
            text("SELECT COUNT(*) FROM clientes WHERE canal_id = :id"),
            {"id": CANAL_NAO_CLASSIFICADO_ID},
        ).scalar()

        logger.info(f"Pos: canal_id NULL = {count_null_pos} (esperado 0)")
        logger.info(f"Pos: canal_id=8 total = {count_8} (esperado {count_null})")

        if count_null_pos != 0:
            logger.error("FALHA: ainda ha clientes com canal_id NULL apos update!")
            sys.exit(1)

        print()
        print("=" * 60)
        print("B1.4-EXEC CONCLUIDO — L3#3")
        print("=" * 60)
        print(f"  Canal NAO_CLASSIFICADO (id={CANAL_NAO_CLASSIFICADO_ID}) ativo")
        print(f"  Clientes orfaos atribuidos:    {result.rowcount}")
        print(f"  Total canal NAO_CLASSIFICADO:  {count_8}")
        print(f"  NULL restantes:                {count_null_pos}")
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
        description=(
            "B1.4: Atribui clientes orfaos (canal_id IS NULL) "
            "ao canal NAO_CLASSIFICADO (id=8)."
        )
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
