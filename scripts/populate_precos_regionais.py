"""
CRM VITAO360 — Popula tabela precos_regionais

Para cada produto ativo, gera preços para as 5 regiões comerciais VITAO,
mapeadas para os estados (UF) de cada territorio de vendedor:

  SUL         (MANU  — PR/SC/RS)         — preço base (preco_tabela)
  SUDESTE     (LARISSA — SP/RJ/MG/ES)    — +5%
  NORDESTE    (LARISSA — BA/PE/CE/...)   — +8%
  CENTRO-OESTE(LARISSA — GO/DF/MT/MS)    — +7%
  NORTE       (LARISSA — AM/PA/RO/...)   — +10%

Preço base = preco_tabela do produto. Variação aplicada com pequeno ruído
aleatório (±1%) para naturalidade, respeitando preco_minimo como piso.

Modelo: PrecoRegional(produto_id, uf, preco) — UNIQUE(produto_id, uf)
Sem coluna data_vigencia no modelo.

Idempotente: pula pares (produto_id, uf) que já existem no banco.

R8: dados derivados de preco_tabela real dos produtos (tier SINTETICO).
"""

import random
import sqlite3
from pathlib import Path

# ──────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent / "data" / "crm_vitao360.db"
RANDOM_SEED = 42

# Mapeamento regiao -> (multiplicador_base, lista de UFs)
# Multiplicador 1.0 = preço base (tabela), 1.05 = +5%, etc.
REGIOES = {
    "SUL": {
        "multiplicador": 1.00,
        "ufs": ["PR", "SC", "RS"],
    },
    "SUDESTE": {
        "multiplicador": 1.05,
        "ufs": ["SP", "RJ", "MG", "ES"],
    },
    "NORDESTE": {
        "multiplicador": 1.08,
        "ufs": ["BA", "PE", "CE", "MA", "PB", "RN", "AL", "SE", "PI"],
    },
    "CENTRO-OESTE": {
        "multiplicador": 1.07,
        "ufs": ["GO", "DF", "MT", "MS"],
    },
    "NORTE": {
        "multiplicador": 1.10,
        "ufs": ["AM", "PA", "RO", "AC", "AP", "RR", "TO"],
    },
}

# Ruído aleatório por UF (±1%) para naturalidade nos preços
RUIDO_MAX = 0.01


def calcular_preco_regional(preco_tabela, preco_minimo, multiplicador, uf_rng):
    """
    Calcula preço regional aplicando multiplicador + ruído ±RUIDO_MAX.
    Garante que preço >= preco_minimo e arredonda em 2 casas decimais.
    """
    ruido = uf_rng.uniform(-RUIDO_MAX, RUIDO_MAX)
    preco = preco_tabela * (multiplicador + ruido)
    preco = round(preco, 2)
    # Piso: nunca abaixo do preco_minimo do produto
    if preco_minimo and preco_minimo > 0:
        preco = max(preco, round(preco_minimo, 2))
    # Garante > 0
    preco = max(preco, 0.01)
    return preco


def main():
    rng = random.Random(RANDOM_SEED)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Carrega todos os produtos ativos com preco_tabela > 0
    cur.execute(
        "SELECT id, codigo, nome, preco_tabela, preco_minimo "
        "FROM produtos WHERE preco_tabela > 0 AND ativo = 1 ORDER BY id"
    )
    produtos = cur.fetchall()
    print(f"Produtos ativos com preco_tabela > 0: {len(produtos)}")

    # Monta set de pares (produto_id, uf) já existentes (idempotência)
    cur.execute("SELECT produto_id, uf FROM precos_regionais")
    existentes = {(row["produto_id"], row["uf"]) for row in cur.fetchall()}
    print(f"Pares (produto, uf) ja existentes: {len(existentes)}")

    registros = []
    pulados = 0

    for produto in produtos:
        pid = produto["id"]
        preco_tab = produto["preco_tabela"]
        preco_min = produto["preco_minimo"] or 0.0

        for regiao, cfg in REGIOES.items():
            multiplicador = cfg["multiplicador"]
            for uf in cfg["ufs"]:
                if (pid, uf) in existentes:
                    pulados += 1
                    continue

                preco = calcular_preco_regional(preco_tab, preco_min, multiplicador, rng)
                registros.append(
                    {
                        "produto_id": pid,
                        "uf": uf,
                        "preco": preco,
                    }
                )

    if not registros:
        cur.execute("SELECT COUNT(*) FROM precos_regionais")
        total = cur.fetchone()[0]
        print(f"Idempotente: sem novos registros para inserir. Total = {total}.")
        conn.close()
        return

    # Bulk insert com ignore em caso de conflito (UNIQUE produto_id+uf)
    cur.executemany(
        """
        INSERT OR IGNORE INTO precos_regionais (produto_id, uf, preco)
        VALUES (:produto_id, :uf, :preco)
        """,
        registros,
    )
    conn.commit()
    inseridos = cur.rowcount if cur.rowcount >= 0 else len(registros)

    # Relatório final
    cur.execute("SELECT COUNT(*) FROM precos_regionais")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT produto_id) FROM precos_regionais")
    produtos_com_preco = cur.fetchone()[0]
    cur.execute("SELECT uf, COUNT(*) as n, AVG(preco) as media FROM precos_regionais GROUP BY uf ORDER BY uf")
    por_uf = cur.fetchall()

    print()
    print("=" * 55)
    print("RESULTADO populate_precos_regionais")
    print("=" * 55)
    print(f"Registros preparados           : {len(registros)}")
    print(f"Pares pulados (ja existiam)    : {pulados}")
    print(f"Total precos_regionais no banco: {total}")
    print(f"Produtos com preco regional    : {produtos_com_preco}")
    print()
    # Agrupa por regiao para exibicao
    uf_to_regiao = {
        uf: regiao
        for regiao, cfg in REGIOES.items()
        for uf in cfg["ufs"]
    }
    regioes_stats = {}
    for row in por_uf:
        regiao = uf_to_regiao.get(row["uf"], "OUTRA")
        if regiao not in regioes_stats:
            regioes_stats[regiao] = {"count": 0, "precos": []}
        regioes_stats[regiao]["count"] += row["n"]
        regioes_stats[regiao]["precos"].append(row["media"])

    print(f"{'Regiao':<16} {'UFs':>5} {'Registros':>10} {'Preco Medio':>12}")
    print("-" * 46)
    for regiao, cfg in REGIOES.items():
        stats = regioes_stats.get(regiao, {"count": 0, "precos": []})
        n_ufs = len(cfg["ufs"])
        n_reg = stats["count"]
        media = sum(stats["precos"]) / len(stats["precos"]) if stats["precos"] else 0
        mult_pct = (cfg["multiplicador"] - 1) * 100
        label = f"{regiao} (+{mult_pct:.0f}%)" if mult_pct > 0 else f"{regiao} (base)"
        print(f"{label:<16} {n_ufs:>5} {n_reg:>10} R${media:>10.2f}")
    print("=" * 55)

    conn.close()


if __name__ == "__main__":
    main()
