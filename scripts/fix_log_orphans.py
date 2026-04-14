"""
fix_log_orphans.py — Corrige registros log_interacoes sem cliente correspondente.

Estratégia:
  - CNPJ válido (14 dígitos numéricos e não genérico): cria cliente PROSPECT mínimo
    com consultor=LARISSA (catch-all).
  - CNPJ inválido: adiciona coluna 'fonte' e marca como 'ORPHAN' (não deleta).

Idempotente: pode ser rodado múltiplas vezes sem efeitos colaterais.
"""

import re
import sqlite3
import sys
from datetime import datetime

DB_PATH = "data/crm_vitao360.db"

# CNPJs genéricos/inválidos que nunca devem virar clientes
CNPJ_BLACKLIST = {
    "00000000000000",
    "11111111111111",
    "22222222222222",
    "33333333333333",
    "44444444444444",
    "55555555555555",
    "66666666666666",
    "77777777777777",
    "88888888888888",
    "99999999999999",
    "99999999999901",  # placeholder detectado nos dados
    "12345678000000",
    "12345678000100",
}


def normalize_cnpj(raw) -> str:
    """Retorna string 14 dígitos ou '' se inválido."""
    if raw is None:
        return ""
    cleaned = re.sub(r"\D", "", str(raw)).zfill(14)
    return cleaned if len(cleaned) == 14 else ""


def is_cnpj_valid(cnpj_14: str) -> bool:
    """CNPJ com 14 dígitos numéricos e não na blacklist."""
    if len(cnpj_14) != 14:
        return False
    if not cnpj_14.isdigit():
        return False
    if cnpj_14 in CNPJ_BLACKLIST:
        return False
    return True


def ensure_fonte_column(conn: sqlite3.Connection):
    """Adiciona coluna 'fonte' em log_interacoes se ainda não existir."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(log_interacoes)")
    cols = [c[1] for c in cur.fetchall()]
    if "fonte" not in cols:
        cur.execute("ALTER TABLE log_interacoes ADD COLUMN fonte TEXT")
        conn.commit()
        print("[schema] Coluna 'fonte' adicionada em log_interacoes.")
    else:
        print("[schema] Coluna 'fonte' já existe.")


def get_orphan_cnpjs(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Retorna lista de (cnpj, count) para logs sem cliente correspondente."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT l.cnpj, COUNT(*) as cnt
        FROM log_interacoes l
        WHERE l.cnpj NOT IN (SELECT cnpj FROM clientes)
        GROUP BY l.cnpj
        ORDER BY cnt DESC
        """
    )
    return cur.fetchall()


def create_prospect_cliente(conn: sqlite3.Connection, cnpj: str) -> bool:
    """
    Cria um registro mínimo em clientes para o CNPJ orphan.
    Retorna False se o cliente já existe (idempotente).
    """
    cur = conn.cursor()

    # Verificação idempotente
    cur.execute("SELECT cnpj FROM clientes WHERE cnpj = ?", (cnpj,))
    if cur.fetchone():
        return False  # já existe

    now = datetime.now().isoformat()
    cur.execute(
        """
        INSERT INTO clientes (
            cnpj, nome_fantasia, razao_social,
            consultor, situacao, tipo_cliente,
            classificacao_3tier, macroregiao,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cnpj,
            f"PROSPECT {cnpj}",      # nome placeholder rastreável
            f"PROSPECT {cnpj}",
            "LARISSA",               # catch-all conforme regra
            "PROSPECT",
            "PROSPECT",
            "REAL",                  # CNPJ existia nos logs — é dado real
            "NACIONAL",
            now,
            now,
        ),
    )
    return True


def mark_logs_orphan(conn: sqlite3.Connection, cnpj: str, count: int):
    """Marca registros com CNPJ inválido como fonte='ORPHAN'."""
    cur = conn.cursor()
    cur.execute(
        "UPDATE log_interacoes SET fonte = 'ORPHAN' WHERE cnpj = ? AND (fonte IS NULL OR fonte != 'ORPHAN')",
        (cnpj,),
    )
    rows = cur.rowcount
    return rows


def main():
    print("=" * 60)
    print("fix_log_orphans.py — Iniciando")
    print(f"DB: {DB_PATH}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    # 1. Garantir coluna fonte
    ensure_fonte_column(conn)

    # 2. Coletar orphans antes do fix
    orphans_before = get_orphan_cnpjs(conn)
    total_logs_orphan = sum(cnt for _, cnt in orphans_before)
    distinct_cnpjs = len(orphans_before)

    print(f"\n[antes] {total_logs_orphan} logs orphan ({distinct_cnpjs} CNPJs distintos)\n")

    stats = {
        "prospects_criados": 0,
        "prospects_ja_existiam": 0,
        "cnpjs_invalidos": 0,
        "logs_marcados_orphan": 0,
    }

    validos = []
    invalidos = []

    for cnpj_raw, cnt in orphans_before:
        cnpj = normalize_cnpj(cnpj_raw)
        if is_cnpj_valid(cnpj):
            validos.append((cnpj, cnt))
        else:
            invalidos.append((cnpj_raw, cnt))

    print(f"[classificacao] {len(validos)} CNPJs válidos → criar PROSPECT")
    print(f"[classificacao] {len(invalidos)} CNPJs inválidos → marcar ORPHAN\n")

    # 3a. Criar clientes PROSPECT para CNPJs válidos
    for cnpj, cnt in validos:
        created = create_prospect_cliente(conn, cnpj)
        if created:
            stats["prospects_criados"] += 1
        else:
            stats["prospects_ja_existiam"] += 1

    # 3b. Marcar inválidos como ORPHAN
    for cnpj_raw, cnt in invalidos:
        rows = mark_logs_orphan(conn, cnpj_raw, cnt)
        stats["cnpjs_invalidos"] += 1
        stats["logs_marcados_orphan"] += rows

    conn.commit()

    # 4. Verificar resultado
    orphans_after = get_orphan_cnpjs(conn)

    # Orphans after = apenas os inválidos que não têm cliente e fonte != ORPHAN
    remaining_without_cliente = []
    for cnpj_raw, cnt in orphans_after:
        # Estes ainda não têm cliente — mas podem estar marcados ORPHAN
        remaining_without_cliente.append((cnpj_raw, cnt))

    # Logs de verificação real: orphans que NÃO são ORPHAN e ainda não têm cliente
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM log_interacoes l
        WHERE l.cnpj NOT IN (SELECT cnpj FROM clientes)
        AND (l.fonte IS NULL OR l.fonte != 'ORPHAN')
        """
    )
    real_remaining = cur.fetchone()[0]

    print("\n" + "=" * 60)
    print("RELATÓRIO")
    print("=" * 60)
    print(f"  Prospects criados:          {stats['prospects_criados']:>6}")
    print(f"  Prospects já existiam:      {stats['prospects_ja_existiam']:>6}")
    print(f"  CNPJs inválidos:            {stats['cnpjs_invalidos']:>6}")
    print(f"  Logs marcados ORPHAN:       {stats['logs_marcados_orphan']:>6}")
    print(f"  Orphans sem cliente/flag:   {real_remaining:>6}  ← deve ser 0")
    print("=" * 60)

    if real_remaining > 0:
        print(f"\n[AVISO] {real_remaining} logs ainda sem cliente nem flag ORPHAN.")
        print("  Investigar manualmente os CNPJs restantes.")
        sys.exit(1)
    else:
        print("\n[OK] Todos os logs orphan resolvidos. Zero pendentes.")

    conn.close()


if __name__ == "__main__":
    main()
