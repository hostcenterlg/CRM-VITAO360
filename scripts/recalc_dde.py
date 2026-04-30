"""
CRM VITAO360 — recalc_dde.py (Onda 3 — OSCAR)

Trigger pós-ingestão: recalcula a cascata DDE para CNPJs afetados.
Popula/atualiza cliente_dre_periodo com os resultados mais recentes.

Uso:
    python scripts/recalc_dde.py --all                     # todos clientes elegíveis
    python scripts/recalc_dde.py --cnpjs CNPJ1,CNPJ2,...  # subset específico
    python scripts/recalc_dde.py --canal DIRETO            # canal específico
    python scripts/recalc_dde.py --ano 2025                # ano específico (default: ano atual)
    python scripts/recalc_dde.py --all --ano 2025          # todos + ano específico

Exemplos:
    python scripts/recalc_dde.py --cnpjs 12345678000100
    python scripts/recalc_dde.py --canal DIRETO --ano 2025
    python scripts/recalc_dde.py --all

Canais DDE: DIRETO, INDIRETO, FOOD_SERVICE (per spec README seção 9)

REGRAS:
  R5 — CNPJ normalizado em toda operação
  R8 — Zero alucinação: engine retorna PENDENTE/NULL onde não há dado real
  R11 — Script idempotente: pode rodar múltiplas vezes com segurança
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

# Adicionar diretório raiz ao path para imports relativos
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.cliente import Cliente
from backend.app.services.dde_engine import calcula_dre_comercial, normaliza_cnpj, CANAIS_DDE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _busca_cnpjs_elegíveis(db: Session, canal: str | None = None) -> list[str]:
    """
    Busca CNPJs de clientes elegíveis para DDE.
    Elegível = canal in CANAIS_DDE (DIRETO, INDIRETO, FOOD_SERVICE).
    Se canal específico, filtra por esse canal.
    """
    query = (
        db.query(Cliente.cnpj)
        .join(Cliente.canal)
        .filter(Cliente.cnpj.isnot(None))
    )

    from backend.app.models.canal import Canal
    if canal:
        query = query.filter(Canal.nome == canal.upper())
    else:
        query = query.filter(Canal.nome.in_(CANAIS_DDE))

    rows = query.all()
    return [row.cnpj for row in rows if row.cnpj]


def _recalc_cnpj(cnpj: str, ano: int, db: Session) -> dict:
    """Recalcula DDE para um CNPJ. Retorna resultado resumido."""
    cnpj_norm = normaliza_cnpj(cnpj)
    try:
        resultado = calcula_dre_comercial(cnpj_norm, ano, db)
        linhas_com_valor = sum(1 for l in resultado.linhas if l.valor is not None)
        return {
            "cnpj": cnpj_norm,
            "status": "OK",
            "veredito": resultado.veredito,
            "linhas_com_valor": linhas_com_valor,
            "total_linhas": len(resultado.linhas),
        }
    except Exception as e:
        return {
            "cnpj": cnpj_norm,
            "status": "ERRO",
            "erro": str(e),
        }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recalcula cascata DDE para clientes VITAO360 pós-ingestão.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_clientes",
        help="Recalcular todos os clientes elegíveis (canais DDE)",
    )
    parser.add_argument(
        "--cnpjs",
        type=str,
        default=None,
        help="Lista de CNPJs separados por vírgula (ex.: 12345678000100,98765432000100)",
    )
    parser.add_argument(
        "--canal",
        type=str,
        default=None,
        choices=["DIRETO", "INDIRETO", "FOOD_SERVICE"],
        help="Filtrar por canal específico",
    )
    parser.add_argument(
        "--ano",
        type=int,
        default=datetime.now().year,
        help=f"Ano de referência (default: {datetime.now().year})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar CNPJs que seriam processados sem executar",
    )

    args = parser.parse_args()

    if not args.all_clientes and not args.cnpjs:
        parser.error("Use --all ou --cnpjs CNPJ1,CNPJ2,...")

    db: Session = SessionLocal()
    try:
        # Determinar lista de CNPJs
        if args.cnpjs:
            cnpjs = [normaliza_cnpj(c.strip()) for c in args.cnpjs.split(",") if c.strip()]
        else:
            print(f"[recalc_dde] Buscando clientes elegíveis canal={args.canal or 'TODOS_DDE'}...")
            cnpjs = _busca_cnpjs_elegíveis(db, canal=args.canal)

        print(f"[recalc_dde] {len(cnpjs)} CNPJs para processar | ano={args.ano}")

        if args.dry_run:
            print("[recalc_dde] DRY RUN — CNPJs que seriam processados:")
            for cnpj in cnpjs:
                print(f"  {cnpj}")
            return

        # Processar
        t_inicio = time.time()
        resultados = {"OK": 0, "ERRO": 0, "erros": []}

        for i, cnpj in enumerate(cnpjs, 1):
            r = _recalc_cnpj(cnpj, args.ano, db)
            if r["status"] == "OK":
                resultados["OK"] += 1
                print(
                    f"  [{i}/{len(cnpjs)}] {cnpj} → "
                    f"{r['veredito']} ({r['linhas_com_valor']}/{r['total_linhas']} linhas)"
                )
            else:
                resultados["ERRO"] += 1
                resultados["erros"].append(r)
                print(f"  [{i}/{len(cnpjs)}] {cnpj} → ERRO: {r.get('erro', '?')}")

        t_total = time.time() - t_inicio
        print(
            f"\n[recalc_dde] CONCLUÍDO em {t_total:.1f}s — "
            f"OK={resultados['OK']} ERRO={resultados['ERRO']}"
        )

        if resultados["erros"]:
            print("\n[recalc_dde] ERROS DETALHADOS:")
            for e in resultados["erros"]:
                print(f"  CNPJ={e['cnpj']} → {e.get('erro', '?')}")
            sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
