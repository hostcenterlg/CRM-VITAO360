"""
regenerate_seed.py — Exporta todas as tabelas do SQLite para data/seed_data.json.

Tabelas incluídas:
  clientes, vendas, log_interacoes, metas, regras_motor, score_historico,
  agenda_items, redes, produtos, precos_regionais, venda_itens, usuarios

Tabelas excluídas:
  alembic_version  (controle de migração, irrelevante)
  import_jobs      (sempre vazio)
  audit_logs       (log de auditoria interna, muito grande e irrelevante para seed)
  rnc              (vazio)

Formato de saída:
  {
    "clientes":        [...],
    "vendas":          [...],
    ...
    "_meta": {
      "generated_at": "ISO timestamp",
      "source_db":    "data/crm_vitao360.db",
      "counts": { "clientes": N, ... }
    }
  }
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "data/crm_vitao360.db"
SEED_PATH = "data/seed_data.json"

TABLES_TO_EXPORT = [
    "clientes",
    "vendas",
    "log_interacoes",
    "metas",
    "regras_motor",
    "score_historico",
    "agenda_items",
    "redes",
    "produtos",
    "precos_regionais",
    "venda_itens",
    "usuarios",
]


def fetch_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    """Retorna todos os registros de uma tabela como lista de dicts."""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM [{table}]")
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def main():
    print("=" * 60)
    print("regenerate_seed.py — Iniciando")
    print(f"Fonte: {DB_PATH}")
    print(f"Destino: {SEED_PATH}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Verificar que o DB existe
    if not Path(DB_PATH).exists():
        print(f"[ERRO] DB não encontrado: {DB_PATH}")
        raise SystemExit(1)

    conn = sqlite3.connect(DB_PATH)

    # Verificar tabelas existentes no DB
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    db_tables = {row[0] for row in cur.fetchall()}

    seed = {}
    counts = {}

    for table in TABLES_TO_EXPORT:
        if table not in db_tables:
            print(f"[SKIP] Tabela '{table}' não existe no DB.")
            seed[table] = []
            counts[table] = 0
            continue

        rows = fetch_table(conn, table)
        seed[table] = rows
        counts[table] = len(rows)
        print(f"  {table:<25} {len(rows):>7} registros")

    conn.close()

    # Adicionar metadados
    seed["_meta"] = {
        "generated_at": datetime.now().isoformat(),
        "source_db": DB_PATH,
        "tables_exported": TABLES_TO_EXPORT,
        "counts": counts,
        "total_records": sum(counts.values()),
    }

    # Gravar JSON
    out_path = Path(SEED_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, default=str, indent=None)

    file_size_mb = out_path.stat().st_size / 1024 / 1024
    total_records = sum(counts.values())

    print("\n" + "=" * 60)
    print("RELATÓRIO")
    print("=" * 60)
    for table, count in counts.items():
        print(f"  {table:<25} {count:>7}")
    print("-" * 45)
    print(f"  {'TOTAL':<25} {total_records:>7}")
    print(f"\n  Arquivo: {SEED_PATH}")
    print(f"  Tamanho: {file_size_mb:.1f} MB")
    print("=" * 60)
    print("\n[OK] seed_data.json regenerado com sucesso.")


if __name__ == "__main__":
    main()
