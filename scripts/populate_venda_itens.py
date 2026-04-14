"""
CRM VITAO360 — Popula tabela venda_itens

Para cada venda no banco, gera 1-5 itens aleatórios a partir dos 242 produtos
existentes. A soma dos itens DEVE bater EXATAMENTE com valor_pedido da venda
(Two-Base Architecture, R4 SAGRADA).

Algoritmo:
1. Sorteia n_itens produtos distintos do pool ponderado.
2. Para cada item, sorteia quantidade e desconto e calcula um valor_raw inicial.
3. Escala todos os valor_raw proporcionalmente para que a soma = valor_pedido.
4. Ajusta o último item para absorver diferença de arredondamento de centavos.
5. Recalcula preco_unitario = valor_total / (qty * (1 - desc/100)).

Garante: valor_total > 0 em todos os itens (constraint ck_venda_item_valor_positivo).
Idempotente: pula vendas que já têm itens.
"""

import random
import sqlite3
from pathlib import Path

# ──────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "data" / "crm_vitao360.db"
RANDOM_SEED = 42

# Peso por categoria — reflete mix de vendas VITAO Alimentos
CATEGORIA_PESO = {
    "Açúcares": 4,
    "Outros": 3,
    "Biscoitos": 3,
    "Granolas": 2,
    "Mix e Snacks": 2,
    "Aveias": 2,
    "Sementes": 1,
    "Farinhas": 1,
    "Barras e Cereais": 1,
    "Arroz": 1,
    "Nuts e Castanhas": 1,
}


def build_product_pool(cur):
    """Retorna lista ponderada de (produto_id, preco_tabela, unidade)."""
    cur.execute(
        "SELECT id, categoria, preco_tabela, unidade "
        "FROM produtos WHERE preco_tabela > 0 AND ativo = 1"
    )
    rows = cur.fetchall()
    pool = []
    for pid, cat, preco_tab, unidade in rows:
        peso = CATEGORIA_PESO.get(cat, 1)
        pool.extend([(pid, preco_tab, unidade)] * peso)
    return pool


def gerar_itens_para_venda(venda_id, valor_pedido, pool, rng, produtos_ids):
    """
    Gera itens cujo valor_total soma EXATAMENTE valor_pedido.

    Abordagem de escala proporcional:
    - Calcula valor_raw = qty * preco_tab * (1 - desc/100) para cada item.
    - Escala: fator = valor_pedido / soma_raw
    - valor_total[i] = round(valor_raw[i] * fator, 2)
    - O último item absorve o centavo residual.
    - preco_unitario = valor_total / (qty * (1 - desc/100))
    """
    valor_pedido = round(valor_pedido, 2)

    # Sorteia quantos itens (1–5), sem repetir produto na mesma venda
    n_itens = rng.randint(1, min(5, len(pool)))

    # Sorteia n_itens entradas únicas do pool por produto_id
    candidatos = []
    vistos = set()
    tentativas = 0
    while len(candidatos) < n_itens and tentativas < len(pool) * 2:
        pid, preco_tab, unidade = rng.choice(pool)
        if pid not in vistos:
            vistos.add(pid)
            candidatos.append((pid, preco_tab, unidade))
        tentativas += 1
    if not candidatos:
        candidatos = [rng.choice(pool)]
    n_itens = len(candidatos)

    # Gera parâmetros base de cada item
    params = []
    for pid, preco_tab, unidade in candidatos:
        desconto_pct = rng.choice([j * 0.5 for j in range(0, 31)])  # 0.0–15.0%
        if unidade == "KG":
            qty = round(rng.uniform(0.5, 8.0), 2)
        else:
            qty = float(rng.randint(1, 10))
        fator_desc = 1.0 - desconto_pct / 100.0
        # Valor bruto baseado no preco de tabela
        valor_raw = qty * preco_tab * fator_desc
        # Garante valor_raw > 0 (se desconto absurdo)
        if valor_raw <= 0:
            desconto_pct = 0.0
            fator_desc = 1.0
            valor_raw = qty * preco_tab
        params.append({
            "produto_id": pid,
            "quantidade": qty,
            "desconto_pct": desconto_pct,
            "fator_desc": fator_desc,
            "valor_raw": valor_raw,
        })

    soma_raw = sum(p["valor_raw"] for p in params)
    if soma_raw <= 0:
        soma_raw = 1.0  # fallback teórico (nunca deve ocorrer)

    # Escala proporcional para que a soma bata com valor_pedido
    escala = valor_pedido / soma_raw
    itens = []
    soma_arredondada = 0.0

    for idx, p in enumerate(params):
        e_ultimo = (idx == n_itens - 1)

        if e_ultimo:
            # Último item fecha o restante exato
            valor_total = round(valor_pedido - soma_arredondada, 2)
        else:
            valor_total = round(p["valor_raw"] * escala, 2)

        # Garante > 0 (constraint banco)
        if valor_total <= 0:
            valor_total = 0.01

        # Recalcula preco_unitario a partir de valor_total
        qty = p["quantidade"]
        fator_desc = p["fator_desc"]
        denominador = qty * fator_desc
        if denominador > 0:
            preco_unitario = round(valor_total / denominador, 4)
        else:
            preco_unitario = round(valor_total / qty, 4) if qty > 0 else 0.01

        if preco_unitario <= 0:
            preco_unitario = 0.01

        soma_arredondada = round(soma_arredondada + valor_total, 2)

        itens.append({
            "venda_id": venda_id,
            "produto_id": p["produto_id"],
            "quantidade": qty,
            "preco_unitario": preco_unitario,
            "desconto_pct": p["desconto_pct"],
            "valor_total": valor_total,
        })

    return itens


def main():
    rng = random.Random(RANDOM_SEED)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Idempotência: apenas vendas sem itens
    cur.execute(
        """
        SELECT v.id, v.valor_pedido
        FROM vendas v
        WHERE NOT EXISTS (
            SELECT 1 FROM venda_itens vi WHERE vi.venda_id = v.id
        )
        ORDER BY v.id
        """
    )
    vendas_sem_itens = cur.fetchall()

    if not vendas_sem_itens:
        cur.execute("SELECT COUNT(*) FROM venda_itens")
        total = cur.fetchone()[0]
        print(f"Idempotente: todas as vendas ja tem itens. Total venda_itens = {total}.")
        conn.close()
        return

    pool = build_product_pool(cur)
    cur.execute("SELECT id FROM produtos WHERE preco_tabela > 0 AND ativo = 1")
    produtos_ids = {row["id"] for row in cur.fetchall()}
    print(f"Pool de produtos : {len(pool)} entradas ponderadas ({len(produtos_ids)} produtos ativos).")
    print(f"Vendas sem itens : {len(vendas_sem_itens)}")

    itens_inseridos = 0
    erros = 0

    for venda in vendas_sem_itens:
        venda_id = venda["id"]
        valor_pedido = venda["valor_pedido"]

        try:
            itens = gerar_itens_para_venda(venda_id, valor_pedido, pool, rng, produtos_ids)

            # Sanity check pré-insert: todos valor_total > 0
            for it in itens:
                if it["valor_total"] <= 0:
                    raise ValueError(
                        f"valor_total <= 0 para venda_id={venda_id}: {it}"
                    )

            for it in itens:
                cur.execute(
                    """
                    INSERT INTO venda_itens
                        (venda_id, produto_id, quantidade, preco_unitario, desconto_pct, valor_total)
                    VALUES
                        (:venda_id, :produto_id, :quantidade, :preco_unitario, :desconto_pct, :valor_total)
                    """,
                    it,
                )
            conn.commit()
            itens_inseridos += len(itens)

        except Exception as exc:
            erros += 1
            conn.rollback()
            print(f"  ERRO venda_id={venda_id} valor={valor_pedido:.2f}: {exc}")
            continue

    # Relatório final
    cur.execute("SELECT COUNT(*) FROM venda_itens")
    total_itens = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT venda_id) FROM venda_itens")
    vendas_com_itens = cur.fetchone()[0]
    cur.execute("SELECT SUM(valor_total) FROM venda_itens")
    soma_total_itens = cur.fetchone()[0] or 0.0
    cur.execute("SELECT SUM(valor_pedido) FROM vendas")
    soma_total_vendas = cur.fetchone()[0] or 0.0
    cur.execute(
        "SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM venda_itens GROUP BY venda_id)"
    )
    media_itens = cur.fetchone()[0] or 0.0

    # Verifica quantas vendas têm diferença > R$0.01
    cur.execute(
        """
        SELECT COUNT(*) FROM (
            SELECT v.id, ABS(v.valor_pedido - SUM(vi.valor_total)) as diff
            FROM vendas v
            JOIN venda_itens vi ON vi.venda_id = v.id
            GROUP BY v.id
            HAVING diff > 0.01
        )
        """
    )
    vendas_com_diff = cur.fetchone()[0]

    diff_total = abs(soma_total_itens - soma_total_vendas)

    print()
    print("=" * 57)
    print("RESULTADO populate_venda_itens")
    print("=" * 57)
    print(f"Itens inseridos nesta execucao  : {itens_inseridos}")
    print(f"Erros                           : {erros}")
    print(f"Total venda_itens no banco      : {total_itens}")
    print(f"Vendas com itens                : {vendas_com_itens}")
    print(f"Media itens por venda           : {media_itens:.2f}")
    print(f"Vendas com diff > R$0.01        : {vendas_com_diff}")
    print(f"Soma valor_total (itens)        : R$ {soma_total_itens:>14,.2f}")
    print(f"Soma valor_pedido (vendas)      : R$ {soma_total_vendas:>14,.2f}")
    print(f"Diferenca agregada (Two-Base)   : R$ {diff_total:>14,.2f}")
    if diff_total < 1.00:
        print("Two-Base                        : OK (diff < R$1,00)")
    else:
        print("Two-Base                        : ATENCAO — investigar")
    print("=" * 57)

    conn.close()


if __name__ == "__main__":
    main()
