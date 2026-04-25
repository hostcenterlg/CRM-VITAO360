#!/usr/bin/env python3
"""
CRM VITAO360 — recalc_score_batch.py
======================================
Recalcula Score v2 (6 fatores) + prioridade P1-P7 + estagio_funil para TODOS
os clientes no banco. Preenche campos que o seed nao popula.

Uso:
  python scripts/recalc_score_batch.py                    # usa DATABASE_URL do .env
  python scripts/recalc_score_batch.py --db <url>         # override de URL
  python scripts/recalc_score_batch.py --dry-run          # nao commita
  python scripts/recalc_score_batch.py --limit 100        # primeiros N clientes

O que faz:
  1. estagio_funil — fallback por situacao quando ausente
     (PROSPECT -> PROSPECCAO, ATIVO -> EM ATENDIMENTO, INAT.REC/ANT -> RECUPERACAO, etc.)
  2. score_service.aplicar_e_salvar — preenche score + prioridade + historico
  3. Imprime distribuicao final por prioridade

Seguro: idempotente, respeita R8 (zero fabricacao — campos ausentes ficam None).

Regras:
  R4 Two-Base: nao toca valores monetarios
  R5 CNPJ: opera apenas em string 14-digit (ja persistida)
  R8: nao fabrica dado — se nao da pra calcular, deixa None
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Setup paths — pode ser rodado de qualquer lugar
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Carregar .env antes de importar backend (para DATABASE_URL)
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

# Fallback: se DATABASE_URL vazia, usar SQLite local
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"sqlite:///{PROJECT_ROOT / 'data' / 'crm_vitao360.db'}"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models.cliente import Cliente
from backend.app.services.score_service import score_service

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
log = logging.getLogger("recalc_score")


# Fallback estagio_funil por situacao — quando cliente nunca teve interacao,
# mapeia situacao Mercos -> estagio inicial plausivel (sera refinado no
# primeiro atendimento real via motor_regras_service.aplicar).
ESTAGIO_POR_SITUACAO: dict[str, str] = {
    "ATIVO": "EM ATENDIMENTO",
    "EM RISCO": "RECOMPRA",
    "INAT.REC": "SALVAMENTO",
    "INAT.ANT": "RECUPERACAO",
    "PROSPECT": "PROSPECCAO",
    "LEAD": "PROSPECCAO",
    "NOVO": "POS-VENDA",
}


def infer_estagio(cliente: Cliente) -> str | None:
    """Retorna estagio plausivel baseado na situacao. None se sem situacao."""
    if cliente.estagio_funil:
        return cliente.estagio_funil  # ja setado — nao sobrepoe
    if not cliente.situacao:
        return None
    return ESTAGIO_POR_SITUACAO.get(cliente.situacao.upper().strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", help="DATABASE_URL override", default=None)
    ap.add_argument("--dry-run", action="store_true", help="Nao commita")
    ap.add_argument("--limit", type=int, default=None, help="Limita N clientes")
    args = ap.parse_args()

    db_url = args.db or os.environ.get("DATABASE_URL", "")
    log.info("Conectando em: %s", db_url.replace("@", "@***/").split("://")[0] + "://…")

    # pool_pre_ping detecta conexões mortas (Neon serverless agressivo).
    # pool_recycle reabre conexão antes de provedor matar.
    engine = create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 30} if "postgresql" in db_url else {},
    )
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        q = db.query(Cliente)
        if args.limit:
            q = q.limit(args.limit)
        clientes = q.all()
        total = len(clientes)
        log.info("Clientes a processar: %d", total)

        if total == 0:
            log.warning("Nenhum cliente no banco — seed primeiro com populate_saas_db.py")
            return 1

        atualizados_estagio = 0
        atualizados_score = 0
        erros = 0
        # Commit em chunks pra evitar timeout em provedores serverless (Neon).
        COMMIT_EVERY = 100

        for i, cliente in enumerate(clientes, 1):
            # 1. Preencher estagio_funil se ausente
            estagio_inferido = infer_estagio(cliente)
            if estagio_inferido and not cliente.estagio_funil:
                cliente.estagio_funil = estagio_inferido
                atualizados_estagio += 1

            # 2. Calcular score + prioridade (nao cria historico em dry-run)
            try:
                if args.dry_run:
                    resultado = score_service.calcular(cliente)
                    cliente.score = resultado["score"]  # em memoria, nao persiste
                    cliente.prioridade = resultado["prioridade_curta"]
                else:
                    score_service.aplicar_e_salvar(db, cliente)
                atualizados_score += 1
            except Exception as e:
                erros += 1
                log.warning("Erro em cliente %s (%s): %s", cliente.cnpj, cliente.nome_fantasia, e)

            # Progress + commit periodico
            if i % COMMIT_EVERY == 0:
                if not args.dry_run:
                    try:
                        db.commit()
                        log.info("  commit chunk: %d/%d", i, total)
                    except Exception as e:
                        log.error("Erro ao commitar chunk %d: %s — rollback parcial", i, e)
                        db.rollback()
                        erros += 1
                else:
                    log.info("  progresso: %d/%d", i, total)

        # Commit final
        if args.dry_run:
            log.info("DRY-RUN: rollback")
            db.rollback()
        else:
            db.commit()
            log.info("COMMIT FINAL: %d atualizacoes persistidas", atualizados_score)

        # Distribuicao final
        from collections import Counter
        prioridades = Counter(c.prioridade for c in clientes if c.prioridade)
        temperaturas = Counter(c.temperatura for c in clientes if c.temperatura)
        estagios = Counter(c.estagio_funil for c in clientes if c.estagio_funil)

        log.info("=" * 60)
        log.info("RESULTADO:")
        log.info("  estagio_funil preenchidos: %d", atualizados_estagio)
        log.info("  score + prioridade:        %d", atualizados_score)
        log.info("  erros:                     %d", erros)
        log.info("")
        log.info("Distribuicao prioridade: %s", dict(prioridades))
        log.info("Distribuicao estagio:    %s", dict(estagios))
        log.info("Distribuicao temperatura:%s", dict(temperaturas))
        log.info("=" * 60)

        return 0 if erros == 0 else 2

    except Exception as e:
        log.exception("Erro inesperado: %s", e)
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
