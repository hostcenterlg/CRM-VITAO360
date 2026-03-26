"""
Recalcular Motor + Score + Sinaleiro + Prioridade para todos os 1.581 clientes.

Executa:
  1. Motor de Regras: situacao|resultado -> estagio_funil, fase, tipo_contato,
                      acao_futura, temperatura, followup_dias, grupo_dash, tipo_acao
  2. Sinaleiro v2 (5 cores): usa logica oficial de scripts/motor/sinaleiro_engine.py
  3. Score v2 (6 fatores): usa logica oficial de scripts/motor/score_engine.py
  4. Prioridade v2 (P0-P7): extendida com P0 = problema_aberto
  5. gap_valor + status_meta
  6. Agenda diaria (50 itens por consultor)

Regras inviolaveis:
  - Two-Base Architecture: valor R$ apenas em registro VENDA
  - CNPJ = string 14 digitos
  - Dados nao fabricados
  - Faturamento vs baseline R$ 2.091.000 (tolerancia 0.5%)
"""

from __future__ import annotations

import sqlite3
import sys
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuracao de paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "crm_vitao360.db"
MOTOR_DIR = BASE_DIR / "scripts" / "motor"

# Adicionar raiz do projeto e pasta motor ao path para importar engines
# Usar BASE_DIR (raiz) para que imports 'scripts.motor.*' funcionem
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(MOTOR_DIR))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("recalcular_todos")

# ---------------------------------------------------------------------------
# Importar engines oficiais diretamente (sem passar pelo __init__.py do pacote)
# ---------------------------------------------------------------------------
import importlib.util as _ilu

def _load_engine(name: str, path: Path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

_score_mod = _load_engine("_score_engine", MOTOR_DIR / "score_engine.py")
_sinal_mod = _load_engine("_sinaleiro_engine", MOTOR_DIR / "sinaleiro_engine.py")

calcular_score = _score_mod.calcular_score
atribuir_prioridade = _score_mod.atribuir_prioridade
calcular_sinaleiro = _sinal_mod.calcular_sinaleiro

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
BASELINE_FATURAMENTO = 2_091_000.0
TOLERANCIA_FAT = 0.005  # 0.5%
AGENDA_LIMITE = 50
HOJE = date.today().isoformat()

# Consultores principais (em ordem alfabetica)
CONSULTORES_PRINCIPAIS = ["DAIANE", "JULIO", "LARISSA", "MANU"]

# Mapeamento de label longo -> label curto (max 5 chars) para campo prioridade
PRIORIDADE_CURTA: dict[str, str] = {
    "P0 IMEDIATA": "P0",
    "P1 NAMORO NOVO": "P1",
    "P2 NEGOCIACAO ATIVA": "P2",
    "P3 PROBLEMA": "P3",
    "P4 MOMENTO OURO": "P4",
    "P5 INAT. RECENTE": "P5",
    "P6 INAT. ANTIGO": "P6",
    "P7 PROSPECCAO": "P7",
}

# Ordem de prioridade para agenda (menor = mais urgente, pula fila)
PRIORIDADE_ORDEM: dict[str, int] = {
    "P0": 0, "P1": 1, "P3": 3, "P2": 2,
    "P4": 4, "P5": 5, "P6": 6, "P7": 7,
}


# ---------------------------------------------------------------------------
# Motor de Regras
# ---------------------------------------------------------------------------

def lookup_regra(cursor: sqlite3.Cursor, regras: dict, situacao: str, resultado: str) -> Optional[dict]:
    """Busca regra na tabela regras_motor pela chave situacao|resultado.

    Tenta match exato primeiro, depois apenas situacao como fallback.
    """
    chave = f"{situacao}|{resultado}" if resultado else f"{situacao}|"
    if chave in regras:
        return regras[chave]
    # Fallback: qualquer regra com a situacao (pega a primeira)
    for k, v in regras.items():
        if k.startswith(f"{situacao}|"):
            return v
    return None


def carregar_regras(cursor: sqlite3.Cursor) -> dict:
    """Carrega todas as regras_motor em um dict chave -> dados."""
    cursor.execute("""
        SELECT chave, estagio_funil, fase, tipo_contato, acao_futura,
               temperatura, follow_up_dias, grupo_dash, tipo_acao
        FROM regras_motor
    """)
    regras = {}
    for row in cursor.fetchall():
        chave, estagio, fase, tipo_contato, acao, temp, fu_dias, grupo, tipo_acao = row
        regras[chave] = {
            "estagio_funil": estagio,
            "fase": fase,
            "tipo_contato": tipo_contato,
            "acao_futura": acao,
            "temperatura": temp,
            "followup_dias": fu_dias,
            "grupo_dash": grupo,
            "tipo_acao": tipo_acao,
        }
    return regras


# ---------------------------------------------------------------------------
# Sinaleiro v2 — delega para engine oficial
# ---------------------------------------------------------------------------

def calcular_sinaleiro_cliente(situacao: str, dias_sem_compra, ciclo_medio) -> str:
    """Wrapper para engine oficial de sinaleiro."""
    dias = float(dias_sem_compra) if dias_sem_compra is not None else None
    ciclo = float(ciclo_medio) if ciclo_medio is not None else None
    return calcular_sinaleiro(dias, ciclo, situacao or "")


# ---------------------------------------------------------------------------
# Score v2 — delega para engine oficial
# ---------------------------------------------------------------------------

def calcular_score_cliente(row: dict) -> float:
    """Calcula score v2 usando engine oficial com campos do cliente."""
    return calcular_score(
        situacao=row.get("situacao") or "",
        curva_abc=row.get("curva_abc") or "",
        tipo_cliente=row.get("tipo_cliente") or "",
        temperatura=row.get("temperatura") or "",
        tentativas=row.get("tentativas") or "",
        dias_sem_compra=row.get("dias_sem_compra"),
        ciclo_medio=row.get("ciclo_medio"),
        dias_atraso_followup=None,  # campo não disponivel no banco
        ecommerce_carrinho=0.0,
    )


# ---------------------------------------------------------------------------
# Prioridade v2 (P0-P7)
# ---------------------------------------------------------------------------

def calcular_prioridade_v2(row: dict, score: float) -> str:
    """Calcula prioridade P0-P7 com regras contextuais.

    P0 IMEDIATA: problema_aberto=True (pula tudo)
    P1-P7: regras do engine oficial (atribuir_prioridade)
    """
    # P0 — problema aberto (ex.: RNC, suporte critico)
    if row.get("problema_aberto"):
        return "P0"

    prioridade_longa, _ = atribuir_prioridade(
        resultado=row.get("resultado") or "",
        situacao=row.get("situacao") or "",
        curva_abc=row.get("curva_abc") or "",
        tipo_cliente=row.get("tipo_cliente") or "",
        temperatura=row.get("temperatura") or "",
        tentativas=row.get("tentativas") or "",
        dias_sem_compra=row.get("dias_sem_compra"),
        ciclo_medio=row.get("ciclo_medio"),
    )

    # Converter label longo -> curto (max 5 chars)
    return PRIORIDADE_CURTA.get(prioridade_longa, prioridade_longa[:5])


# ---------------------------------------------------------------------------
# Status meta
# ---------------------------------------------------------------------------

def calcular_status_meta(meta_anual: Optional[float], realizado: Optional[float]) -> tuple[Optional[float], Optional[float], Optional[str]]:
    """Calcula gap_valor, pct_alcancado e status_meta."""
    if not meta_anual or meta_anual <= 0:
        return None, None, None
    r = realizado or 0.0
    gap = meta_anual - r
    pct = r / meta_anual
    if pct >= 1.0:
        status = "ACIMA"
    elif pct >= 0.7:
        status = "ALERTA"
    else:
        status = "CRITICO"
    return round(gap, 2), round(pct, 4), status


# ---------------------------------------------------------------------------
# Carrega realizados do banco (soma vendas por CNPJ)
# ---------------------------------------------------------------------------

def carregar_realizados(cursor: sqlite3.Cursor) -> dict[str, float]:
    """Soma valor_pedido por CNPJ na tabela vendas para 2025 (Two-Base: apenas VENDA).
    Filtra pelo ano 2025 para manter compatibilidade com o baseline R$ 2.091M.
    """
    cursor.execute("""
        SELECT cnpj, SUM(valor_pedido)
        FROM vendas
        WHERE strftime('%Y', data_pedido) = '2025'
        GROUP BY cnpj
    """)
    return {row[0]: row[1] or 0.0 for row in cursor.fetchall()}


# ---------------------------------------------------------------------------
# Gerar agenda
# ---------------------------------------------------------------------------

def gerar_agenda(cursor: sqlite3.Cursor, conn: sqlite3.Connection, clientes_atualizados: list[dict]) -> dict[str, int]:
    """Gera agenda diaria para cada consultor (limite AGENDA_LIMITE itens).

    Ordenacao:
      - P0/P1/P3 primeiro (pula fila)
      - Depois por score decrescente
    """
    # Limpar agenda do dia atual para evitar duplicatas
    cursor.execute("DELETE FROM agenda_items WHERE data_agenda = ?", (HOJE,))

    counts: dict[str, int] = {}

    for consultor in CONSULTORES_PRINCIPAIS:
        # Filtrar clientes do consultor
        clientes_consultor = [
            c for c in clientes_atualizados
            if (c.get("consultor") or "").upper() == consultor.upper()
        ]

        if not clientes_consultor:
            counts[consultor] = 0
            continue

        # Ordenar: prioridade (P0/P1/P3 pula fila) depois score desc
        def sort_key(c):
            p = c.get("prioridade", "P7")
            ordem = PRIORIDADE_ORDEM.get(p, 99)
            score = c.get("score", 0) or 0
            return (ordem, -score)

        clientes_ordenados = sorted(clientes_consultor, key=sort_key)
        agenda = clientes_ordenados[:AGENDA_LIMITE]

        inserts = []
        for pos, cl in enumerate(agenda, start=1):
            inserts.append((
                cl["cnpj"],
                consultor,
                HOJE,
                pos,
                cl.get("nome_fantasia"),
                cl.get("situacao"),
                cl.get("temperatura"),
                cl.get("score"),
                cl.get("prioridade"),
                cl.get("sinaleiro"),
                cl.get("acao_futura"),
                cl.get("followup_dias"),
            ))

        cursor.executemany("""
            INSERT OR REPLACE INTO agenda_items
                (cnpj, consultor, data_agenda, posicao, nome_fantasia,
                 situacao, temperatura, score, prioridade, sinaleiro,
                 acao, followup_dias)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, inserts)

        counts[consultor] = len(inserts)

    conn.commit()
    return counts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 60)
    logger.info("RECALCULAR TODOS — Motor + Score + Sinaleiro")
    logger.info(f"DB: {DB_PATH}")
    logger.info(f"Data agenda: {HOJE}")
    logger.info("=" * 60)

    if not DB_PATH.exists():
        logger.error(f"Banco nao encontrado: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Carregar regras do motor
    logger.info("Carregando regras do motor...")
    regras = carregar_regras(cursor)
    logger.info(f"  {len(regras)} regras carregadas")

    # 2. Carregar realizados (vendas por CNPJ)
    logger.info("Carregando realizados (vendas)...")
    realizados = carregar_realizados(cursor)
    logger.info(f"  {len(realizados)} CNPJs com vendas")

    # Verificar faturamento total (Two-Base check)
    fat_total = sum(realizados.values())
    logger.info(f"  Faturamento total no banco: R$ {fat_total:,.2f}")
    logger.info(f"  Baseline esperado:          R$ {BASELINE_FATURAMENTO:,.2f}")
    divergencia = abs(fat_total - BASELINE_FATURAMENTO) / BASELINE_FATURAMENTO
    if divergencia > TOLERANCIA_FAT:
        logger.warning(f"  ATENCAO: divergencia de faturamento = {divergencia:.1%} (limite: 0.5%)")
    else:
        logger.info(f"  Divergencia: {divergencia:.2%} OK")

    # 3. Carregar todos os clientes
    logger.info("Carregando clientes...")
    cursor.execute("""
        SELECT id, cnpj, nome_fantasia, situacao, resultado, tipo_cliente,
               curva_abc, temperatura, tentativas, dias_sem_compra, ciclo_medio,
               score, sinaleiro, prioridade, consultor,
               estagio_funil, fase, tipo_contato, acao_futura, followup_dias,
               grupo_dash, tipo_acao, meta_anual, realizado_acumulado,
               pct_alcancado, gap_valor, status_meta, problema_aberto
        FROM clientes
    """)
    clientes = [dict(row) for row in cursor.fetchall()]
    logger.info(f"  {len(clientes)} clientes carregados")

    # 4. Recalcular cada cliente
    logger.info("Recalculando Motor + Sinaleiro + Score + Prioridade...")
    updates = []
    clientes_atualizados = []

    contadores = {
        "situacao": {},
        "sinaleiro": {},
        "prioridade": {},
    }

    for cl in clientes:
        cnpj = cl["cnpj"]
        situacao = (cl.get("situacao") or "").upper().strip()
        resultado = (cl.get("resultado") or "").upper().strip()

        # --- a) Motor de Regras ---
        regra = lookup_regra(cursor, regras, situacao, resultado)
        if regra:
            estagio_funil = regra["estagio_funil"]
            fase = regra["fase"]
            tipo_contato = regra["tipo_contato"]
            acao_futura = regra["acao_futura"]
            # Motor define temperatura se cliente nao tem temperatura propria
            temperatura = cl.get("temperatura") or regra["temperatura"]
            followup_dias = regra["followup_dias"]
            grupo_dash = regra["grupo_dash"]
            tipo_acao = regra["tipo_acao"]
        else:
            estagio_funil = cl.get("estagio_funil")
            fase = cl.get("fase")
            tipo_contato = cl.get("tipo_contato")
            acao_futura = cl.get("acao_futura")
            temperatura = cl.get("temperatura")
            followup_dias = cl.get("followup_dias")
            grupo_dash = cl.get("grupo_dash")
            tipo_acao = cl.get("tipo_acao")

        # Atualizar temperatura no dict para usar no score
        cl["temperatura"] = temperatura
        cl["acao_futura"] = acao_futura
        cl["followup_dias"] = followup_dias

        # --- b) Sinaleiro v2 ---
        sinaleiro = calcular_sinaleiro_cliente(
            situacao, cl.get("dias_sem_compra"), cl.get("ciclo_medio")
        )

        # --- c) Score v2 ---
        score = calcular_score_cliente(cl)

        # --- d) Prioridade v2 ---
        prioridade = calcular_prioridade_v2(cl, score)

        # --- e) Meta e gap ---
        realizado_acumulado = realizados.get(cnpj, 0.0)
        meta_anual = cl.get("meta_anual")
        gap_valor, pct_alcancado, status_meta = calcular_status_meta(meta_anual, realizado_acumulado)

        # Acumular contadores
        contadores["situacao"][situacao] = contadores["situacao"].get(situacao, 0) + 1
        contadores["sinaleiro"][sinaleiro] = contadores["sinaleiro"].get(sinaleiro, 0) + 1
        contadores["prioridade"][prioridade] = contadores["prioridade"].get(prioridade, 0) + 1

        # Guardar para agenda
        cl_atualizado = {**cl,
            "estagio_funil": estagio_funil,
            "fase": fase,
            "tipo_contato": tipo_contato,
            "acao_futura": acao_futura,
            "temperatura": temperatura,
            "followup_dias": followup_dias,
            "grupo_dash": grupo_dash,
            "tipo_acao": tipo_acao,
            "sinaleiro": sinaleiro,
            "score": score,
            "prioridade": prioridade,
            "realizado_acumulado": realizado_acumulado,
            "gap_valor": gap_valor,
            "pct_alcancado": pct_alcancado,
            "status_meta": status_meta,
        }
        clientes_atualizados.append(cl_atualizado)

        updates.append((
            estagio_funil, fase, tipo_contato, acao_futura, temperatura,
            followup_dias, grupo_dash, tipo_acao,
            sinaleiro, score, prioridade,
            realizado_acumulado, gap_valor, pct_alcancado, status_meta,
            datetime.now().isoformat(),
            cl["id"],
        ))

    # 5. Commit em lote (batch update)
    logger.info("Gravando atualizacoes no banco...")
    cursor.executemany("""
        UPDATE clientes SET
            estagio_funil=?, fase=?, tipo_contato=?, acao_futura=?,
            temperatura=?, followup_dias=?, grupo_dash=?, tipo_acao=?,
            sinaleiro=?, score=?, prioridade=?,
            realizado_acumulado=?, gap_valor=?, pct_alcancado=?, status_meta=?,
            updated_at=?
        WHERE id=?
    """, updates)
    conn.commit()
    logger.info(f"  {len(updates)} clientes atualizados")

    # 6. Gerar agenda
    logger.info("Gerando agenda diaria...")
    agenda_counts = gerar_agenda(cursor, conn, clientes_atualizados)

    # ---------------------------------------------------------------------------
    # 7. Relatorio final
    # ---------------------------------------------------------------------------
    total = len(clientes)
    score_medio = sum(c.get("score") or 0 for c in clientes_atualizados) / total if total else 0

    print("\n" + "=" * 60)
    print("RELATORIO FINAL — RECALCULO CRM VITAO360")
    print("=" * 60)
    print(f"\nTotal clientes recalculados: {total}")

    print("\nDistribuicao por SITUACAO:")
    for sit, cnt in sorted(contadores["situacao"].items(), key=lambda x: -x[1]):
        print(f"  {sit or '(sem situacao)':<20} {cnt:>5}")

    print("\nDistribuicao por SINALEIRO:")
    ordem_sinal = ["VERDE", "AMARELO", "LARANJA", "VERMELHO", "ROXO"]
    for sinal in ordem_sinal:
        cnt = contadores["sinaleiro"].get(sinal, 0)
        print(f"  {sinal:<10} {cnt:>5}")

    print("\nDistribuicao por PRIORIDADE:")
    for pri in ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]:
        cnt = contadores["prioridade"].get(pri, 0)
        print(f"  {pri}  {cnt:>5}")

    print(f"\nScore medio geral: {score_medio:.1f}")

    print("\nAgenda gerada:")
    for consultor in CONSULTORES_PRINCIPAIS:
        cnt = agenda_counts.get(consultor, 0)
        print(f"  {consultor:<10} {cnt:>3} itens")
    total_agenda = sum(agenda_counts.values())
    print(f"  TOTAL      {total_agenda:>3} itens")

    print(f"\nFaturamento no banco: R$ {fat_total:,.2f}")
    print(f"Baseline esperado:    R$ {BASELINE_FATURAMENTO:,.2f}")
    print(f"Divergencia:          {divergencia:.2%}")
    if divergencia <= TOLERANCIA_FAT:
        print("STATUS FATURAMENTO:   OK (dentro de 0.5%)")
    else:
        print("STATUS FATURAMENTO:   ATENCAO (fora de 0.5%)")

    print("\n" + "=" * 60)
    print("RECALCULO CONCLUIDO")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
