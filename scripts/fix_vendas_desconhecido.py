"""
CRM VITAO360 — Fix vendas com consultor=DESCONHECIDO
=====================================================
Para cada venda com consultor='DESCONHECIDO', busca o CNPJ correspondente
na tabela clientes e copia o campo consultor do cliente para a venda.

Se o cliente não existir no banco, marca a venda como 'LEGADO'.

Idempotente: opera APENAS sobre vendas com consultor='DESCONHECIDO'.
Executar repetidamente é seguro — não duplica nem altera registros já corrigidos.

R2 — CNPJ: string 14 dígitos, nunca float.
R4 — Two-Base: este script não toca valores monetários.
R11 — Commits atômicos: 1 task = 1 commit.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "crm_vitao360.db"

FALLBACK_CONSULTOR = "LEGADO"


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # --- Diagnóstico inicial ------------------------------------------------
    cur.execute(
        "SELECT COUNT(*), ROUND(SUM(valor_pedido), 2) "
        "FROM vendas WHERE consultor='DESCONHECIDO'"
    )
    total_count, total_valor = cur.fetchone()
    print(f"Vendas DESCONHECIDO encontradas: {total_count} | R$ {total_valor or 0:.2f}")

    if total_count == 0:
        print("Nada a corrigir. Banco já está consistente.")
        conn.close()
        return

    # --- Buscar todas as vendas DESCONHECIDO com cnpj do cliente ------------
    cur.execute(
        """
        SELECT
            v.id,
            v.cnpj,
            COALESCE(c.consultor, ?) AS consultor_destino,
            c.nome_fantasia,
            v.valor_pedido
        FROM vendas v
        LEFT JOIN clientes c ON v.cnpj = c.cnpj
        WHERE v.consultor = 'DESCONHECIDO'
        ORDER BY c.consultor, v.cnpj
        """,
        (FALLBACK_CONSULTOR,),
    )
    rows = cur.fetchall()

    # --- Aplicar correções --------------------------------------------------
    counts: dict[str, int] = {}
    valores: dict[str, float] = {}

    for venda_id, cnpj, consultor_destino, nome_fantasia, valor_pedido in rows:
        cur.execute(
            "UPDATE vendas SET consultor=? WHERE id=? AND consultor='DESCONHECIDO'",
            (consultor_destino, venda_id),
        )
        counts[consultor_destino] = counts.get(consultor_destino, 0) + 1
        valores[consultor_destino] = valores.get(consultor_destino, 0.0) + (valor_pedido or 0.0)

        nome_display = (nome_fantasia or cnpj or "")[:40]
        print(f"  id={venda_id:<6} | {cnpj} | {nome_display:<40} | -> {consultor_destino}")

    conn.commit()

    # --- Relatório final ----------------------------------------------------
    print(f"\n{'='*60}")
    print(f"Total corrigido: {sum(counts.values())} vendas | R$ {sum(valores.values()):.2f}")
    print(f"{'='*60}")
    print(f"{'Consultor':<12} | {'Vendas':>6} | {'Faturamento':>14}")
    print(f"{'-'*12}-+-{'-'*6}-+-{'-'*14}")
    for consultor in sorted(counts):
        print(
            f"{consultor:<12} | {counts[consultor]:>6} | R$ {valores[consultor]:>11.2f}"
        )

    # --- Verificação pós-correção -------------------------------------------
    cur.execute(
        "SELECT COUNT(*) FROM vendas WHERE consultor='DESCONHECIDO'"
    )
    (restantes,) = cur.fetchone()
    print(f"\nVerificação: vendas DESCONHECIDO restantes = {restantes}")
    if restantes == 0:
        print("OK — banco consistente.")
    else:
        print(f"ATENCAO — ainda existem {restantes} vendas DESCONHECIDO.")

    conn.close()


if __name__ == "__main__":
    main()
