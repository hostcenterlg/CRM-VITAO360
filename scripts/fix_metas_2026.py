"""
CRM VITAO360 — Fix metas anuais 2026 (mes=0) → metas mensais (mes=1..12)
=========================================================================
Registros com ano=2026 e mes=0 representam metas ANUAIS importadas do SAP.
O endpoint /api/projecao/{consultor} espera metas mensais (mes=1 a 12).

Para cada registro (cnpj, ano=2026, mes=0):
  1. Divide o valor anual por 12 (distribuição linear proporcional).
  2. Cria 12 novos registros mensais (mes=1 a mes=12) com valor/12.
  3. Remove o registro original com mes=0.

Idempotente:
  - Verifica se já existem mensais para (cnpj, 2026, mes) antes de inserir.
  - Se todos os 12 meses já existirem para um CNPJ, pula aquele CNPJ.
  - Não altera registros já existentes com mes > 0.

Constraint de unicidade: uq_meta_cnpj_periodo (cnpj, ano, mes) — respeitada.

R2 — CNPJ: string 14 dígitos, nunca float.
R4 — Two-Base: este script não toca vendas, apenas metas.
R11 — Commits atômicos: 1 task = 1 commit.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "crm_vitao360.db"


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # --- Diagnóstico inicial ------------------------------------------------
    cur.execute(
        "SELECT COUNT(*), ROUND(SUM(meta_sap), 2) "
        "FROM metas WHERE ano=2026 AND mes=0"
    )
    row = cur.fetchone()
    total_anuais = row[0]
    total_meta_anual = row[1] or 0.0
    print(f"Metas anuais 2026 (mes=0): {total_anuais} registros | meta_sap total = R$ {total_meta_anual:.2f}")

    cur.execute("SELECT COUNT(*) FROM metas WHERE ano=2026 AND mes>0")
    (ja_mensais,) = cur.fetchone()
    print(f"Metas mensais 2026 (mes>0) existentes: {ja_mensais}")

    if total_anuais == 0:
        print("Nada a corrigir. Banco já está consistente.")
        conn.close()
        return

    # --- Buscar todos os registros anuais -----------------------------------
    cur.execute(
        """
        SELECT id, cnpj, ano, meta_sap, meta_igualitaria, realizado, fonte
        FROM metas
        WHERE ano=2026 AND mes=0
        ORDER BY cnpj
        """
    )
    registros_anuais = cur.fetchall()

    # --- Processar cada registro anual --------------------------------------
    criados = 0
    pulados = 0
    removidos = 0
    cnpjs_processados: list[str] = []
    cnpjs_pulados: list[str] = []

    for reg in registros_anuais:
        reg_id = reg["id"]
        cnpj = reg["cnpj"]
        meta_anual = reg["meta_sap"] or 0.0
        meta_igualitaria_anual = reg["meta_igualitaria"]
        realizado_anual = reg["realizado"] or 0.0
        fonte = reg["fonte"] or "SAP"

        # Valor mensal = distribuição linear por 12 meses
        meta_mensal = round(meta_anual / 12, 4)

        # meta_igualitaria também distribuída se existir
        meta_ig_mensal: float | None = None
        if meta_igualitaria_anual is not None:
            meta_ig_mensal = round(meta_igualitaria_anual / 12, 4)

        # Verificar idempotência: contar meses já existentes para este CNPJ em 2026
        cur.execute(
            "SELECT mes FROM metas WHERE cnpj=? AND ano=2026 AND mes>0",
            (cnpj,),
        )
        meses_existentes = {r[0] for r in cur.fetchall()}

        # Se todos os 12 meses já existem, pular este CNPJ (já foi processado)
        if len(meses_existentes) == 12:
            pulados += 1
            cnpjs_pulados.append(cnpj)
            # Remover o anual se ainda existir (caso tenha sido interrompido anteriormente)
            cur.execute("DELETE FROM metas WHERE id=?", (reg_id,))
            removidos += 1
            continue

        # Inserir apenas os meses que ainda não existem
        meses_a_criar = [m for m in range(1, 13) if m not in meses_existentes]

        for mes in meses_a_criar:
            cur.execute(
                """
                INSERT INTO metas (cnpj, ano, mes, meta_sap, meta_igualitaria, realizado, fonte)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cnpj,
                    2026,
                    mes,
                    meta_mensal,
                    meta_ig_mensal,
                    0.0,   # realizado começa em zero por mês
                    fonte,
                ),
            )
            criados += 1

        # Remover o registro anual original (mes=0)
        cur.execute("DELETE FROM metas WHERE id=?", (reg_id,))
        removidos += 1
        cnpjs_processados.append(cnpj)

    conn.commit()

    # --- Relatório final ----------------------------------------------------
    print(f"\n{'='*60}")
    print(f"CNPJs processados:  {len(cnpjs_processados)}")
    print(f"CNPJs pulados (já mensalizados): {pulados}")
    print(f"Registros mensais criados: {criados}")
    print(f"Registros anuais removidos: {removidos}")
    print(f"{'='*60}")

    # --- Verificação pós-correção -------------------------------------------
    cur.execute("SELECT COUNT(*) FROM metas WHERE ano=2026 AND mes=0")
    (restantes_anuais,) = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*), ROUND(SUM(meta_sap), 2) FROM metas WHERE ano=2026 AND mes>0"
    )
    row2 = cur.fetchone()
    total_mensais = row2[0]
    soma_mensais = row2[1] or 0.0

    print(f"\nVerificação pós-correção:")
    print(f"  Registros anuais (mes=0) restantes: {restantes_anuais}")
    print(f"  Registros mensais (mes>0) criados:  {total_mensais}")
    print(f"  Soma meta_sap mensal total:  R$ {soma_mensais:.2f}")
    print(f"  Soma meta_sap anual original: R$ {total_meta_anual:.2f}")

    # Verificar conservação de valor (dentro de tolerância de arredondamento)
    diferenca = abs(soma_mensais - total_meta_anual)
    tolerancia = 0.01 * total_anuais  # 1 centavo por CNPJ de tolerância de arredondamento
    if diferenca <= tolerancia:
        print(f"  Conservacao de valor: OK (diferença de arredondamento R$ {diferenca:.4f})")
    else:
        print(f"  ATENCAO — diferença de valor: R$ {diferenca:.2f} (verificar)")

    if restantes_anuais == 0:
        print("\nOK — banco consistente. Todas as metas anuais foram mensalizadas.")
    else:
        print(f"\nATENCAO — ainda existem {restantes_anuais} metas anuais (mes=0).")

    conn.close()


if __name__ == "__main__":
    main()
