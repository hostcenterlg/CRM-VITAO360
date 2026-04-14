"""
CRM VITAO360 — sync_mercos_to_db.py
=====================================
Sincroniza dados Mercos (extrações diárias) com o banco SQLite local.

Fontes (data/mercos/{YYYY-MM-DD}/):
  carteira_summary.json  — amostra de clientes + contagens de carteira
  indicadores.json       — KPIs do período (evolução de venda, positivação, ABC)
  pedidos_ativos.json    — pedidos ativos da primeira página do Mercos

Regras INVIOLÁVEIS:
  R2  — CNPJ = string 14 dígitos zero-padded, NUNCA float
  R4  — Two-Base: tabela vendas TEM valor > 0; este script NÃO toca log_interacoes
  R8  — NUNCA fabricar dados (se campo ausente, fica None/skip)
  R10 — Mercos mente nos nomes: sempre usar extraction_date do JSON, não nome da pasta
  Idempotente: pode rodar múltiplas vezes sem duplicar

Uso:
  python scripts/sync_mercos_to_db.py
  python scripts/sync_mercos_to_db.py --data-dir data/mercos/2026-04-06
  python scripts/sync_mercos_to_db.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "crm_vitao360.db"
MERCOS_ROOT = PROJECT_ROOT / "data" / "mercos"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sync_mercos")

# ---------------------------------------------------------------------------
# DE-PARA vendedores Mercos → consultor CRM (R1 do enunciado)
# ---------------------------------------------------------------------------
VENDEDOR_DEPARA: dict[str, str] = {
    # DAIANE
    "central - daiane": "DAIANE",
    "central daiane": "DAIANE",
    "daiane": "DAIANE",
    "daiane stavicki": "DAIANE",
    "daiane vitao": "DAIANE",
    # MANU
    "manu": "MANU",
    "manu vitao": "MANU",
    "manu ditzel": "MANU",
    "manu - vitao": "MANU",
    # LARISSA
    "larissa": "LARISSA",
    "larissa padilha": "LARISSA",
    "lari": "LARISSA",
    "larissa vitao": "LARISSA",
    "mais granel": "LARISSA",
    "rodrigo": "LARISSA",
    # JULIO
    "julio": "JULIO",
    "julio gadret": "JULIO",
}

# Situacao dos clientes: mapeamento Mercos → CRM
# Mercos conta ativos / inativos_recentes / inativos_antigos / prospects
# Mas sem CNPJ individual, usamos só o total para log — não alteramos situacao individual
# (só via carteira_summary que tem CNPJ, veja _processar_carteira_amostra)
MERCOS_STATUS_MAP: dict[str, str] = {
    "ativo": "ATIVO",
    "inativos_recentes": "INAT.REC",
    "inativos_antigos": "INAT.ANT",
    "prospect": "PROSPECT",
}

# Threshold fuzzy matching para nome de cliente
FUZZY_THRESHOLD = 72

# ---------------------------------------------------------------------------
# Opcional: rapidfuzz
# ---------------------------------------------------------------------------
try:
    from rapidfuzz import fuzz, process as rfuzz_process

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("rapidfuzz não instalado — fuzzy match por nome DESABILITADO. "
                "Execute: pip install rapidfuzz")


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def normalizar_cnpj(val: object) -> Optional[str]:
    """R2: CNPJ → string 14 dígitos zero-padded. Retorna None se inválido."""
    if val is None:
        return None
    s = re.sub(r"\D", "", str(val)).zfill(14)
    if len(s) != 14:
        return None
    if len(set(s)) == 1:
        return None  # tipo 00000000000000 — inválido
    return s


def resolver_consultor(vendedor_raw: Optional[str]) -> str:
    """Normaliza nome de vendedor Mercos para consultor CRM."""
    if not vendedor_raw:
        return "DESCONHECIDO"
    chave = vendedor_raw.strip().lower()
    return VENDEDOR_DEPARA.get(chave, "DESCONHECIDO")


def parse_date(raw: Optional[str]) -> Optional[date]:
    """Converte string ISO-8601 (YYYY-MM-DD) para datetime.date."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def encontrar_dir_mercos_mais_recente(mercos_root: Path) -> Optional[Path]:
    """Busca o subdiretório YYYY-MM-DD mais recente com pelo menos um JSON."""
    candidatos = []
    for d in mercos_root.iterdir():
        if d.is_dir():
            try:
                datetime.strptime(d.name, "%Y-%m-%d")
                jsons = list(d.glob("*.json"))
                if jsons:
                    candidatos.append(d)
            except ValueError:
                pass
    if not candidatos:
        return None
    return max(candidatos, key=lambda p: p.name)


# ---------------------------------------------------------------------------
# Matching de clientes no banco
# ---------------------------------------------------------------------------

def buscar_cliente_por_cnpj(cur: sqlite3.Cursor, cnpj: str) -> Optional[dict]:
    """Retorna row do cliente como dict, ou None se não encontrado."""
    cur.execute(
        "SELECT cnpj, nome_fantasia, razao_social, telefone, email, cidade, situacao "
        "FROM clientes WHERE cnpj = ?",
        (cnpj,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    cols = ["cnpj", "nome_fantasia", "razao_social", "telefone", "email", "cidade", "situacao"]
    return dict(zip(cols, row))


def buscar_cliente_por_nome_fuzzy(
    cur: sqlite3.Cursor, nome_mercos: str
) -> Optional[dict]:
    """
    Tenta encontrar cliente no banco via fuzzy match por nome.

    Retorna o melhor match acima de FUZZY_THRESHOLD, ou None.
    Apenas ativado se rapidfuzz estiver disponível.
    """
    if not RAPIDFUZZ_AVAILABLE:
        return None

    # Carrega todos os nomes do banco (apenas id, cnpj, nome, razao)
    cur.execute(
        "SELECT cnpj, nome_fantasia, razao_social FROM clientes "
        "WHERE nome_fantasia IS NOT NULL OR razao_social IS NOT NULL"
    )
    rows = cur.fetchall()
    if not rows:
        return None

    # Constrói lista de nomes para comparar
    candidatos = []
    for cnpj_db, nf, rs in rows:
        for nm in [nf, rs]:
            if nm:
                candidatos.append((nm.upper(), cnpj_db))

    nome_upper = nome_mercos.upper()
    nomes_lista = [c[0] for c in candidatos]

    resultado = rfuzz_process.extractOne(
        nome_upper,
        nomes_lista,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=FUZZY_THRESHOLD,
    )
    if resultado is None:
        return None

    nome_match, score, idx = resultado
    cnpj_match = candidatos[idx][1]
    logger.debug("  fuzzy match '%s' → '%s' (score=%d)", nome_mercos, nome_match, score)

    cur.execute(
        "SELECT cnpj, nome_fantasia, razao_social, telefone, email, cidade, situacao "
        "FROM clientes WHERE cnpj = ?",
        (cnpj_match,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    cols = ["cnpj", "nome_fantasia", "razao_social", "telefone", "email", "cidade", "situacao"]
    return dict(zip(cols, row))


# ---------------------------------------------------------------------------
# Processadores
# ---------------------------------------------------------------------------

def _processar_indicadores(
    cur: sqlite3.Cursor,
    indicadores: dict,
    dry_run: bool,
) -> dict:
    """
    Lê indicadores.json e loga o snapshot.

    NÃO altera situacao de clientes individualmente (sem CNPJ por cliente).
    Apenas registra o estado agregado para o relatório.

    Retorna dict com summary dos indicadores lidos.
    """
    carteira = indicadores.get("carteira_clientes", {})
    evolucao = indicadores.get("evolucao_venda", {})
    positivacao = indicadores.get("positivacao", {})
    curva_abc = indicadores.get("curva_abc", {})
    periodo = indicadores.get("period", indicadores.get("extraction_date", "?"))
    data_extracao = indicadores.get("extraction_date", "?")

    logger.info("  Indicadores Mercos [%s — extraido %s]:", periodo, data_extracao)
    logger.info("    Carteira: total=%s | ativos=%s | inat.rec=%s | inat.ant=%s | prospects=%s",
             carteira.get("total", "?"),
             carteira.get("ativos", "?"),
             carteira.get("inativos_recentes", "?"),
             carteira.get("inativos_antigos", "?"),
             carteira.get("prospects", "?"))
    logger.info("    Vendas no mês: R$ %.2f", evolucao.get("vendido_no_mes", 0.0))
    logger.info("    Positivação: %s clientes (%.1f%%)",
             positivacao.get("clientes_positivados", 0),
             positivacao.get("positivados_pct", 0.0))
    logger.info("    Curva ABC: %s clientes | A=%.1f%% | B=%.1f%%",
             curva_abc.get("total_clientes", "?"),
             curva_abc.get("a_pct", 0.0),
             curva_abc.get("b_pct", 0.0))

    return {
        "periodo": periodo,
        "data_extracao": data_extracao,
        "total_carteira": carteira.get("total", 0),
        "ativos": carteira.get("ativos", 0),
        "inativos_recentes": carteira.get("inativos_recentes", 0),
        "inativos_antigos": carteira.get("inativos_antigos", 0),
        "prospects": carteira.get("prospects", 0),
        "vendido_no_mes": evolucao.get("vendido_no_mes", 0.0),
    }


def _processar_carteira_amostra(
    cur: sqlite3.Cursor,
    carteira_data: dict,
    dry_run: bool,
) -> dict:
    """
    Para cada cliente da amostra (carteira_summary.json), normaliza o CNPJ,
    busca no banco e atualiza telefone/email/cidade se encontrar.

    Não cria novos clientes — apenas atualiza os existentes.
    Retorna stats de matches/updates.
    """
    amostra = carteira_data.get("amostra_clientes_primeira_pagina", [])
    stats = {
        "total_amostra": len(amostra),
        "matched_cnpj": 0,
        "updated": 0,
        "not_found": 0,
        "cnpj_invalido": 0,
    }

    for item in amostra:
        cnpj_raw = item.get("cnpj")
        cnpj = normalizar_cnpj(cnpj_raw)

        if cnpj is None:
            logger.warning("  CNPJ inválido na amostra: %r", cnpj_raw)
            stats["cnpj_invalido"] += 1
            continue

        cliente_db = buscar_cliente_por_cnpj(cur, cnpj)
        if cliente_db is None:
            logger.debug("  Cliente não encontrado no DB: CNPJ=%s nome=%s", cnpj, item.get("nome"))
            stats["not_found"] += 1
            continue

        stats["matched_cnpj"] += 1

        # Campos que podemos atualizar com dados Mercos
        updates: dict[str, str] = {}

        tel_mercos = item.get("telefone", "").strip() if item.get("telefone") else None
        email_mercos = item.get("email", "").strip() if item.get("email") else None
        cidade_mercos = item.get("cidade", "").strip() if item.get("cidade") else None

        # Atualizar telefone se Mercos tem dado e DB está vazio ou diferente
        if tel_mercos and tel_mercos != cliente_db.get("telefone"):
            updates["telefone"] = tel_mercos

        # Atualizar email se Mercos tem dado e DB está vazio
        if email_mercos and not cliente_db.get("email"):
            updates["email"] = email_mercos

        # Atualizar cidade se DB está vazio
        if cidade_mercos and not cliente_db.get("cidade"):
            updates["cidade"] = cidade_mercos

        if not updates:
            logger.debug("  CNPJ=%s — sem alterações necessárias", cnpj)
            continue

        logger.info("  UPDATE cliente CNPJ=%s (%s): %s",
                 cnpj, cliente_db.get("nome_fantasia"), updates)

        if not dry_run:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            valores = list(updates.values()) + [cnpj]
            cur.execute(
                f"UPDATE clientes SET {set_clause}, updated_at = CURRENT_TIMESTAMP "
                f"WHERE cnpj = ?",
                valores,
            )
        stats["updated"] += 1

    return stats


def _processar_pedidos_ativos(
    cur: sqlite3.Cursor,
    pedidos_data: dict,
    dry_run: bool,
) -> dict:
    """
    Insere pedidos ativos do Mercos na tabela vendas (idempotente por numero_pedido).

    R4 Two-Base: valor_pedido DEVE ser > 0.
    R2: CNPJ normalizado como string 14 dígitos.
    R8: fonte='MERCOS', classificacao_3tier='REAL'.

    Pedidos sem CNPJ no JSON são matchados por nome (fuzzy) para obter o CNPJ do banco.
    Se não encontrar cliente → pedido SKIPPED (sem fabricação de dado).
    """
    pedidos = pedidos_data.get("pedidos", [])
    extraction_date = pedidos_data.get("extraction_date", "")
    mes_ref = extraction_date[:7] if len(extraction_date) >= 7 else None  # "2026-04"

    stats = {
        "total_pedidos": len(pedidos),
        "inseridos": 0,
        "ja_existiam": 0,
        "sem_cliente_match": 0,
        "valor_zero_skip": 0,
        "consultor_desconhecido": 0,
    }

    for pedido in pedidos:
        numero = pedido.get("numero")
        data_raw = pedido.get("data")
        vendedor_raw = pedido.get("vendedor")
        nome_cliente = pedido.get("cliente") or pedido.get("razao_social") or ""
        valor = pedido.get("valor", 0.0)
        status_mercos = pedido.get("status", "Em orçamento")

        # R4: valor deve ser > 0
        if not valor or float(valor) <= 0:
            logger.warning("  Pedido #%s com preco=0 ou ausente — SKIP (R4 Two-Base)", numero)
            stats["valor_zero_skip"] += 1
            continue

        data_pedido = parse_date(data_raw)
        if data_pedido is None:
            # Fallback: usar data de extração
            data_pedido = parse_date(extraction_date)
            logger.warning("  Pedido #%s sem data — usando data_extracao=%s", numero, extraction_date)

        consultor = resolver_consultor(vendedor_raw)
        if consultor == "DESCONHECIDO":
            logger.warning("  Pedido #%s — vendedor não mapeado: '%s'", numero, vendedor_raw)
            stats["consultor_desconhecido"] += 1
            # Não pula — ainda tenta inserir com DESCONHECIDO

        # Idempotência: verificar se pedido já existe pelo numero_pedido
        if numero is not None:
            cur.execute(
                "SELECT id FROM vendas WHERE numero_pedido = ?",
                (str(numero),),
            )
            row = cur.fetchone()
            if row:
                logger.debug("  Pedido #%s já existe (id=%s) — SKIP", numero, row[0])
                stats["ja_existiam"] += 1
                continue

        # Buscar CNPJ do cliente: pedidos Mercos não trazem CNPJ diretamente
        # Tentativa 1: match exato por nome na coluna nome_fantasia / razao_social
        cnpj = None
        cliente_db = None

        # Tenta match exato (SQL LIKE)
        nome_upper = nome_cliente.upper()
        cur.execute(
            "SELECT cnpj, nome_fantasia FROM clientes "
            "WHERE UPPER(nome_fantasia) = ? OR UPPER(razao_social) = ? LIMIT 1",
            (nome_upper, nome_upper),
        )
        exact_row = cur.fetchone()
        if exact_row:
            cnpj = exact_row[0]
            logger.debug("  Pedido #%s — match exato: '%s' → CNPJ=%s", numero, nome_cliente, cnpj)
        else:
            # Tentativa 2: fuzzy match
            cliente_db = buscar_cliente_por_nome_fuzzy(cur, nome_cliente)
            if cliente_db:
                cnpj = cliente_db["cnpj"]
                logger.info("  Pedido #%s — fuzzy match: '%s' → '%s' CNPJ=%s",
                         numero, nome_cliente, cliente_db.get("nome_fantasia"), cnpj)

        if cnpj is None:
            logger.warning("  Pedido #%s — cliente não encontrado no DB: '%s' — SKIP",
                        numero, nome_cliente)
            stats["sem_cliente_match"] += 1
            continue

        # Normalizar CNPJ (segurança, já deve estar normalizado no banco)
        cnpj = normalizar_cnpj(cnpj)
        if cnpj is None:
            logger.error("  Pedido #%s — CNPJ inválido após normalização — SKIP", numero)
            stats["sem_cliente_match"] += 1
            continue

        logger.info("  INSERT venda: pedido=#%s data=%s cliente='%s' CNPJ=%s R$%.2f consultor=%s",
                 numero, data_pedido, nome_cliente, cnpj, float(valor), consultor)

        if not dry_run:
            cur.execute(
                """
                INSERT INTO vendas
                    (cnpj, data_pedido, numero_pedido, valor_pedido, consultor,
                     fonte, classificacao_3tier, mes_referencia, created_at)
                VALUES (?, ?, ?, ?, ?, 'MERCOS', 'REAL', ?, CURRENT_TIMESTAMP)
                """,
                (
                    cnpj,
                    data_pedido.isoformat(),
                    str(numero) if numero is not None else None,
                    float(valor),
                    consultor,
                    mes_ref,
                ),
            )
        stats["inseridos"] += 1

    return stats


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sincroniza extrações Mercos com o banco CRM VITAO360."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Diretório com os JSONs Mercos (padrão: mais recente em data/mercos/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas lê e loga — não grava nada no banco.",
    )
    args = parser.parse_args(argv)

    # -----------------------------------------------------------------------
    # 1. Localizar diretório de dados Mercos
    # -----------------------------------------------------------------------
    if args.data_dir:
        data_dir = args.data_dir
        if not data_dir.is_absolute():
            data_dir = PROJECT_ROOT / data_dir
    else:
        data_dir = encontrar_dir_mercos_mais_recente(MERCOS_ROOT)
        if data_dir is None:
            logger.error("Nenhum diretório Mercos encontrado em %s", MERCOS_ROOT)
            return 1

    logger.info("=" * 60)
    logger.info("sync_mercos_to_db — diretório: %s", data_dir)
    if args.dry_run:
        logger.info("  MODO DRY-RUN — nenhuma gravação será feita")
    logger.info("=" * 60)

    # -----------------------------------------------------------------------
    # 2. Carregar JSONs
    # -----------------------------------------------------------------------
    arquivo_indicadores = data_dir / "indicadores.json"
    arquivo_carteira = data_dir / "carteira_summary.json"
    arquivo_pedidos = data_dir / "pedidos_ativos.json"

    indicadores: dict = {}
    carteira_data: dict = {}
    pedidos_data: dict = {}

    for arquivo, container, nome in [
        (arquivo_indicadores, None, "indicadores"),
        (arquivo_carteira, None, "carteira_summary"),
        (arquivo_pedidos, None, "pedidos_ativos"),
    ]:
        if arquivo.exists():
            with open(arquivo, encoding="utf-8") as f:
                data = json.load(f)
            if nome == "indicadores":
                indicadores = data
            elif nome == "carteira_summary":
                carteira_data = data
            elif nome == "pedidos_ativos":
                pedidos_data = data
            logger.info("  Carregado: %s", arquivo.name)
        else:
            logger.warning("  Arquivo não encontrado: %s", arquivo)

    if not indicadores and not carteira_data and not pedidos_data:
        logger.error("Nenhum dado encontrado em %s", data_dir)
        return 1

    # -----------------------------------------------------------------------
    # 3. Conectar ao banco
    # -----------------------------------------------------------------------
    if not DB_PATH.exists():
        logger.error("Banco não encontrado: %s", DB_PATH)
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()

    stats_total: dict = {}

    try:
        # -----------------------------------------------------------------------
        # 4. Processar indicadores (snapshot — não altera banco, apenas loga)
        # -----------------------------------------------------------------------
        if indicadores:
            logger.info("")
            logger.info("--- [1/3] INDICADORES ---")
            stats_indicadores = _processar_indicadores(cur, indicadores, args.dry_run)
            stats_total["indicadores"] = stats_indicadores
        else:
            logger.info("[1/3] indicadores.json ausente — skip")

        # -----------------------------------------------------------------------
        # 5. Processar amostra da carteira (atualiza telefone/email/cidade)
        # -----------------------------------------------------------------------
        if carteira_data:
            logger.info("")
            logger.info("--- [2/3] CARTEIRA AMOSTRA ---")
            stats_carteira = _processar_carteira_amostra(cur, carteira_data, args.dry_run)
            stats_total["carteira"] = stats_carteira
            logger.info("  Resultado: %s clientes na amostra | %s com CNPJ válido | "
                     "%s encontrados no DB | %s atualizados | %s não encontrados",
                     stats_carteira["total_amostra"],
                     stats_carteira["total_amostra"] - stats_carteira["cnpj_invalido"],
                     stats_carteira["matched_cnpj"],
                     stats_carteira["updated"],
                     stats_carteira["not_found"])
        else:
            logger.info("[2/3] carteira_summary.json ausente — skip")

        # -----------------------------------------------------------------------
        # 6. Processar pedidos ativos (insere em vendas)
        # -----------------------------------------------------------------------
        if pedidos_data:
            logger.info("")
            logger.info("--- [3/3] PEDIDOS ATIVOS ---")
            stats_pedidos = _processar_pedidos_ativos(cur, pedidos_data, args.dry_run)
            stats_total["pedidos"] = stats_pedidos
            logger.info("  Resultado: %s pedidos | %s inseridos | %s já existiam | "
                     "%s sem match cliente | %s valor=0 skip | %s consultor desconhecido",
                     stats_pedidos["total_pedidos"],
                     stats_pedidos["inseridos"],
                     stats_pedidos["ja_existiam"],
                     stats_pedidos["sem_cliente_match"],
                     stats_pedidos["valor_zero_skip"],
                     stats_pedidos["consultor_desconhecido"])
        else:
            logger.info("[3/3] pedidos_ativos.json ausente — skip")

        # -----------------------------------------------------------------------
        # 7. Commit
        # -----------------------------------------------------------------------
        if not args.dry_run:
            conn.commit()
            logger.info("")
            logger.info("COMMIT concluído.")
        else:
            conn.rollback()
            logger.info("")
            logger.info("DRY-RUN — rollback executado, banco inalterado.")

    except Exception as exc:
        conn.rollback()
        logger.error("ERRO durante sync: %s — rollback executado", exc, exc_info=True)
        return 1
    finally:
        conn.close()

    # -----------------------------------------------------------------------
    # 8. Relatório final
    # -----------------------------------------------------------------------
    logger.info("")
    logger.info("=" * 60)
    logger.info("RELATÓRIO FINAL — sync_mercos_to_db")
    logger.info("=" * 60)

    if "indicadores" in stats_total:
        ind = stats_total["indicadores"]
        logger.info("Indicadores (%s): vendido_mes=R$%.2f ativos=%s inat.rec=%s inat.ant=%s prospects=%s",
                 ind.get("periodo", "?"),
                 ind.get("vendido_no_mes", 0.0),
                 ind.get("ativos", 0),
                 ind.get("inativos_recentes", 0),
                 ind.get("inativos_antigos", 0),
                 ind.get("prospects", 0))

    if "carteira" in stats_total:
        c = stats_total["carteira"]
        logger.info("Carteira amostra: %s clientes | %s matched | %s atualizados",
                 c["total_amostra"], c["matched_cnpj"], c["updated"])

    if "pedidos" in stats_total:
        p = stats_total["pedidos"]
        logger.info("Pedidos ativos: %s total | %s inseridos | %s já existiam | %s sem match",
                 p["total_pedidos"], p["inseridos"], p["ja_existiam"], p["sem_cliente_match"])

    logger.info("=" * 60)
    logger.info("sync_mercos_to_db concluído com SUCESSO.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
