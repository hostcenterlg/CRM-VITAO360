"""
CRM VITAO360 — Fix 46 DESCONHECIDO clients
==========================================
Assigns consultor based on DE-PARA rules:
  - PR/SC/RS → MANU
  - Rede names (MUNDO VERDE, BIOMUNDO, BIO MUNDO) → DAIANE
  - All others → LARISSA

Idempotent: only updates clients with consultor='DESCONHECIDO'.
"""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "crm_vitao360.db"

# DE-PARA: Redes that belong to DAIANE
DAIANE_REDE_PATTERNS = [
    "MUNDO VERDE", "BIOMUNDO", "BIO MUNDO", "DIVINA TERRA",
    "VIDA LEVE", "FITLAND", "FIT LAND", "TUDO EM GRAOS",
    "ARMAZEM FIT", "CIA DA SAUDE", "CIA SAUDE",
]

# MANU territories (Sul)
MANU_UFS = {"SC", "PR", "RS"}


def classify(nome_fantasia: str, rede_regional: str, uf: str) -> str:
    """Returns the correct consultor for a DESCONHECIDO client."""
    nome = (nome_fantasia or "").upper()
    rede = (rede_regional or "").upper()

    # Check DAIANE redes first (rede field)
    for pattern in DAIANE_REDE_PATTERNS:
        if pattern in rede:
            return "DAIANE"

    # Check DAIANE redes by name
    for pattern in DAIANE_REDE_PATTERNS:
        if pattern in nome:
            return "DAIANE"

    # MANU = Sul
    if uf in MANU_UFS:
        return "MANU"

    # All others = LARISSA (Resto do Brasil)
    return "LARISSA"


def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute(
        "SELECT cnpj, nome_fantasia, rede_regional, uf FROM clientes WHERE consultor='DESCONHECIDO'"
    )
    rows = cur.fetchall()
    print(f"Found {len(rows)} DESCONHECIDO clients")

    if not rows:
        print("Nothing to fix.")
        conn.close()
        return

    counts = {"MANU": 0, "LARISSA": 0, "DAIANE": 0, "JULIO": 0}

    for cnpj, nome, rede, uf in rows:
        dest = classify(nome, rede, uf)
        counts[dest] += 1
        cur.execute(
            "UPDATE clientes SET consultor=? WHERE cnpj=?",
            (dest, cnpj),
        )
        print(f"  {cnpj} | {(nome or '')[:35]:<35} | {uf or '':<2} | -> {dest}")

    conn.commit()
    conn.close()

    print(f"\nDone: {sum(counts.values())} updated")
    for k, v in counts.items():
        if v > 0:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
