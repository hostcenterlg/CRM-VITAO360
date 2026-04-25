#!/usr/bin/env python3
"""
CRM VITAO360 — seed_usuario_canal.py
=====================================
Popula a tabela usuario_canal com as associacoes iniciais de canais
por usuario (DECISAO L3 Leandro 25/Apr/2026).

Mapeamento:
  Daiane Stavicki  (gerente)        -> INTERNO + FOOD_SERVICE
  Manu Ditzel      (consultor)      -> DIRETO
  Larissa Padilha  (consultor)      -> DIRETO
  Julio Gadret     (consultor_ext)  -> DIRETO
  Leandro          (admin)          -> nenhuma (role=admin ve tudo via dependency)

Identificacao do usuario eh por email (chave de negocio).
Idempotente: skipa associacoes ja existentes.

Uso:
  python scripts/seed_usuario_canal.py
  python scripts/seed_usuario_canal.py --dry-run
  python scripts/seed_usuario_canal.py --db-path data/crm_vitao360.db
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
log = logging.getLogger("seed_usuario_canal")


# DECISAO L3 — mapeamento email -> [canais]
SEED_MAPPING: list[tuple[str, list[str]]] = [
    ("daiane@vitao.com.br",  ["INTERNO", "FOOD_SERVICE"]),
    ("manu@vitao.com.br",    ["DIRETO"]),
    ("larissa@vitao.com.br", ["DIRETO"]),
    ("julio@vitao.com.br",   ["DIRETO"]),
    # leandro@vitao.com.br: role=admin, sem associacao (deps=None)
]


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
        # Pre-load: canais (nome -> id) e usuarios (email -> id)
        canais_map = dict(
            session.execute(text("SELECT nome, id FROM canais")).fetchall()
        )
        usuarios_map = dict(
            session.execute(text("SELECT email, id FROM usuarios")).fetchall()
        )

        if not canais_map:
            log.error("Tabela canais vazia. Aplicar migration multi-canal antes.")
            return 1
        if not usuarios_map:
            log.error("Tabela usuarios vazia.")
            return 1

        criadas = 0
        ja_existentes = 0
        ignoradas = 0

        for email, canais_nomes in SEED_MAPPING:
            user_id = usuarios_map.get(email)
            if user_id is None:
                log.warning("Usuario %s nao encontrado — skip", email)
                ignoradas += len(canais_nomes)
                continue

            for canal_nome in canais_nomes:
                canal_id = canais_map.get(canal_nome)
                if canal_id is None:
                    log.warning(
                        "Canal %s nao encontrado em canais — skip user=%s",
                        canal_nome, email,
                    )
                    ignoradas += 1
                    continue

                existente = session.execute(text("""
                    SELECT 1 FROM usuario_canal
                    WHERE usuario_id = :uid AND canal_id = :cid
                """), {"uid": user_id, "cid": canal_id}).fetchone()

                if existente:
                    log.info("[skip] %s -> %s (ja existe)", email, canal_nome)
                    ja_existentes += 1
                    continue

                if args.dry_run:
                    log.info(
                        "[DRY RUN] %s -> %s (user_id=%d, canal_id=%d) seria inserido",
                        email, canal_nome, user_id, canal_id,
                    )
                    criadas += 1
                else:
                    session.execute(text("""
                        INSERT INTO usuario_canal (usuario_id, canal_id, created_at)
                        VALUES (:uid, :cid, CURRENT_TIMESTAMP)
                    """), {"uid": user_id, "cid": canal_id})
                    log.info(
                        "[INSERT] %s -> %s (user_id=%d, canal_id=%d)",
                        email, canal_nome, user_id, canal_id,
                    )
                    criadas += 1

        if not args.dry_run:
            session.commit()

        log.info("")
        log.info("=" * 60)
        log.info(
            "Seed usuario_canal: criadas=%d ja_existentes=%d ignoradas=%d %s",
            criadas, ja_existentes, ignoradas,
            "[DRY RUN]" if args.dry_run else "[GRAVADO]",
        )
        log.info("=" * 60)

        # Visao final
        log.info("\nEstado atual usuario_canal:")
        for r in session.execute(text("""
            SELECT u.email, c.nome, c.status
            FROM usuario_canal uc
            JOIN usuarios u ON u.id = uc.usuario_id
            JOIN canais c ON c.id = uc.canal_id
            ORDER BY u.email, c.nome
        """)).fetchall():
            log.info("  %-30s -> %-15s [%s]", r[0], r[1], r[2])

        return 0

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
