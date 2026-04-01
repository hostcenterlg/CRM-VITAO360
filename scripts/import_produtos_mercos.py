"""
CRM VITAO360 — Import Produtos from Mercos XLSX
================================================
Source: data/sources/mercos/produtos/Produtos por pedidos 2025.xlsx
Target: produtos table (SQLAlchemy ORM)

Architecture notes:
  - R1 Two-Base: Produto stores only tabela/referência prices (NOT transactional)
  - R2 CNPJ: not applicable here (product codes, not CNPJs)
  - R8 Zero fabrication: all data extracted from real Mercos report
  - R10 Mercos lies: confirmed date range 01/01/2025-15/12/2025 from rows 5-6

Usage:
    python scripts/import_produtos_mercos.py

Idempotent: skips products whose codigo already exists in the DB.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from statistics import median
from typing import Optional

# ---------------------------------------------------------------------------
# Path bootstrap — allow running from repo root without installing the package
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import openpyxl  # noqa: E402

from backend.app.database import SessionLocal, engine  # noqa: E402
from backend.app.models.produto import Produto  # noqa: E402

# Ensure all models are registered so the ORM can introspect them
import backend.app.models  # noqa: E402, F401 (side-effect import)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
XLSX_PATH = PROJECT_ROOT / "data" / "sources" / "mercos" / "produtos" / "Produtos por pedidos 2025.xlsx"

PRODUCT_HEADER_RE = re.compile(r"^Produto:\s*(\d+)\s*-\s*(.+)$")

# Column indices (0-based) — row 10 headers:
# 'Data Emissão', 'Pedido', 'Cliente', 'Criador', 'Preço Líquido (R$)', 'Quantidade', 'Subtotal (R$)'
COL_PRECO_LIQUIDO = 4
COL_QUANTIDADE = 5
COL_SUBTOTAL = 6


# ---------------------------------------------------------------------------
# Category inference
# ---------------------------------------------------------------------------
def infer_categoria(nome: str) -> str:
    """
    Derives product category from the product name using keyword matching.
    Case-insensitive, accent-tolerant via upper ASCII comparison.
    """
    n = nome.upper()

    if "ACUCAR" in n or "MASCAVO" in n or "AÇÚCAR" in n or "MASCAVO" in n:
        return "Açúcares"
    if "GRANOLA" in n:
        return "Granolas"
    if "AVEIA" in n:
        return "Aveias"
    if "BARRA" in n or "CEREAL" in n:
        return "Barras e Cereais"
    if "COOKIE" in n or "BISCOITO" in n:
        return "Biscoitos"
    if "CASTANHA" in n or "AMENDOA" in n or "NOZES" in n or "AMENDOIM" in n:
        return "Nuts e Castanhas"
    if "ARROZ" in n:
        return "Arroz"
    if "FARINHA" in n or "FARELO" in n:
        return "Farinhas"
    if "OLEO" in n or "ÓLEO" in n or "AZEITE" in n:
        return "Óleos"
    if "SEMENTE" in n or "CHIA" in n or "LINHACA" in n or "LINHAÇA" in n:
        return "Sementes"
    if "MIX" in n or "TRAIL" in n:
        return "Mix e Snacks"
    return "Outros"


# ---------------------------------------------------------------------------
# XLSX parsing
# ---------------------------------------------------------------------------
def _is_totals_row(row: tuple) -> bool:
    """
    Mercos appends a product-total row after the last order row.
    Signature: row[0] is None AND row[1] is a number (order count).
    """
    return row[0] is None and isinstance(row[1], (int, float))


def _is_header_row(row: tuple) -> bool:
    """Detects the repeated column-header row ('Data Emissão', ...)."""
    return row[0] == "Data Emissão"


def _is_product_header(val: Optional[str]) -> Optional[re.Match]:
    """Returns a regex Match if val is a product header, else None."""
    if not val or not isinstance(val, str):
        return None
    return PRODUCT_HEADER_RE.match(val.strip())


def parse_xlsx(path: Path) -> list[dict]:
    """
    Parses the Mercos XLSX and returns a list of product dicts:
        {
            "codigo": str,
            "nome": str,
            "precos": list[float],      # Preço Líquido per order row
            "quantidades": list[float], # Quantidade per order row
            "subtotais": list[float],   # Subtotal per order row
        }
    """
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    ws = wb.active

    products: list[dict] = []
    current: Optional[dict] = None

    for row in ws.iter_rows(values_only=True):
        first_cell = row[0]

        # --- Product header line ---
        m = _is_product_header(first_cell)
        if m:
            # Save previous product before starting new one
            if current is not None:
                products.append(current)
            current = {
                "codigo": m.group(1).strip(),
                "nome": m.group(2).strip(),
                "precos": [],
                "quantidades": [],
                "subtotais": [],
            }
            continue

        # Skip column-header rows and totals rows
        if _is_header_row(row) or _is_totals_row(row):
            continue

        # Skip blank rows or rows before first product
        if current is None:
            continue

        # Order data row — validate that we have numeric price and qty
        preco = row[COL_PRECO_LIQUIDO]
        qty = row[COL_QUANTIDADE]
        subtotal = row[COL_SUBTOTAL]

        if preco is not None and qty is not None:
            try:
                current["precos"].append(float(preco))
                current["quantidades"].append(float(qty))
                if subtotal is not None:
                    current["subtotais"].append(float(subtotal))
            except (TypeError, ValueError):
                # Non-numeric cell — skip silently
                pass

    # Don't forget the last product in the sheet
    if current is not None:
        products.append(current)

    wb.close()
    return products


# ---------------------------------------------------------------------------
# DB insertion
# ---------------------------------------------------------------------------
def import_produtos(products: list[dict]) -> tuple[int, int, int]:
    """
    Inserts products into the DB.
    Returns (found, inserted, skipped).
    """
    db = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        # Fetch all existing codigos in one query for O(1) lookup
        existing_codigos: set[str] = {
            row[0] for row in db.query(Produto.codigo).all()
        }

        for p in products:
            codigo = p["codigo"]

            # Idempotency guard
            if codigo in existing_codigos:
                skipped += 1
                continue

            precos = p["precos"]
            quantidades = p["quantidades"]
            subtotais = p["subtotais"]

            # Statistics — only if we have data
            preco_tabela = round(median(precos), 4) if precos else 0.0
            preco_minimo = round(min(precos), 4) if precos else 0.0
            total_vendido = round(sum(quantidades), 2) if quantidades else 0.0
            faturamento = round(sum(subtotais), 2) if subtotais else 0.0

            categoria = infer_categoria(p["nome"])

            produto = Produto(
                codigo=codigo,
                nome=p["nome"],
                categoria=categoria,
                fabricante="VITAO",
                unidade="UN",
                preco_tabela=preco_tabela,
                preco_minimo=preco_minimo,
                ativo=True,
                # Store derived stats in non-transactional fields
                # (comissao_pct reused temporarily as total_vendido placeholder
                #  would violate the model contract — we DON'T do that)
                # R1 Two-Base: faturamento derived here stays in Produto as
                # reference data (preco_tabela/preco_minimo), NOT as a
                # transactional value. total_vendido and faturamento are
                # printed for informational purposes only and NOT stored
                # in the Produto model (no such column exists).
            )

            db.add(produto)
            existing_codigos.add(codigo)  # prevent duplicates within same batch
            inserted += 1

        db.commit()
        print(f"\nCommit OK: {inserted} products inserted.")

    except Exception as exc:
        db.rollback()
        print(f"\nERROR — rollback performed: {exc}", file=sys.stderr)
        raise
    finally:
        db.close()

    return len(products), inserted, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("CRM VITAO360 — Import Produtos Mercos")
    print("=" * 60)
    print(f"Source: {XLSX_PATH}")

    if not XLSX_PATH.exists():
        print(f"\nERROR: file not found: {XLSX_PATH}", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 1: Parse XLSX
    # -----------------------------------------------------------------------
    print("\n[1/3] Parsing XLSX ...")
    products = parse_xlsx(XLSX_PATH)
    print(f"      Products found: {len(products)}")

    if not products:
        print("WARNING: no products parsed — check file structure.", file=sys.stderr)
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 2: Quick diagnostic sample
    # -----------------------------------------------------------------------
    print("\n[2/3] Sample (first 5 products parsed):")
    for p in products[:5]:
        precos = p["precos"]
        qtds = p["quantidades"]
        subs = p["subtotais"]
        med = round(median(precos), 4) if precos else 0.0
        mn = round(min(precos), 4) if precos else 0.0
        total_qty = round(sum(qtds), 2) if qtds else 0.0
        fat = round(sum(subs), 2) if subs else 0.0
        cat = infer_categoria(p["nome"])
        print(
            f"  {p['codigo']} | {p['nome'][:40]:<40} | cat={cat:<20} | "
            f"median_price=R${med:>8.2f} | min=R${mn:>7.2f} | "
            f"qty={total_qty:>8.0f} | fat=R${fat:>10.2f}"
        )

    # Print aggregate totals (informational — NOT stored as transactional data)
    all_fat = sum(
        round(sum(p["subtotais"]), 2) for p in products if p["subtotais"]
    )
    print(f"\n      Total faturamento across all products: R$ {all_fat:,.2f}")
    print(
        "      NOTE: faturamento above is from Mercos 01/01-15/12/2025."
        " Baseline R$ 2.091.000 covers full year — partial overlap expected."
    )

    # -----------------------------------------------------------------------
    # Step 3: DB insertion
    # -----------------------------------------------------------------------
    print("\n[3/3] Inserting into DB ...")
    found, inserted, skipped = import_produtos(products)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Products in XLSX:  {found:>5}")
    print(f"  Inserted (new):    {inserted:>5}")
    print(f"  Skipped (exists):  {skipped:>5}")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # VendaItem note
    # -----------------------------------------------------------------------
    print(
        "\nNOTE — VendaItem population:\n"
        "  Each order row in this file references a pedido number (col 1).\n"
        "  To create VendaItem records we need the Venda.numero_pedido field\n"
        "  populated by a prior Mercos pedidos import. The current vendas\n"
        "  table does not expose numero_pedido in its schema — this step\n"
        "  is deferred to the Mercos pedidos import pipeline (future task)."
    )


if __name__ == "__main__":
    main()
