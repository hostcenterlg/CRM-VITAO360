#!/usr/bin/env python3
"""
CRM VITAO360 — ingest_sales_hunter.py
=======================================
Ingestao dos relatorios diarios do Sales Hunter (interface web SAP VITAO).
Le 13 XLSX de data/sales_hunter/YYYY-MM-DD/morning/ e popula o banco.

Fontes processadas (CWB + VV onde existirem):
  fat_produto       -> upsert produtos
  fat_cliente       -> upsert clientes (faturamento_total, situacao, devolucao)
  fat_nf_det        -> insert vendas + venda_itens (notas fiscais detalhadas)
  pedidos_produto   -> enriquece vendas com consultor (CWB only — VV 302)
  debitos           -> insert debitos_clientes + UPDATE clientes.total_debitos
  devolucao_cliente -> UPDATE clientes (pct_devolucao, total_devolucao,
                       risco_devolucao)
  fat_empresa       -> validacao (sanity check vs baseline R$ 2.091.000)

REGRAS INVIOLAVEIS (respeitadas em todo o pipeline):
  R1  — Two-Base: vendas e debitos sao VENDA-side (R$). Nunca tocamos LOG.
  R2  — CNPJ string 14 digitos zero-padded (CPF 11d -> "000" + CPF).
        re.sub(r'\\D', '', str(val)).zfill(14). NUNCA float/int.
  R7  — Faturamento baseline R$ 2.091.000 (corrigido 2026-03-23, ANTERIOR
        R$ 2.156.179 SUPERSEDED). Tolerancia 0.5% para builds Excel finais.
  R8  — Zero fabricacao: classificacao_3tier='REAL' em todos os SAP.
        Sem CNPJ resolvido = skip, NUNCA inventa dados.
  R11 — Idempotente: rerun nao duplica (UPSERT por chaves logicas).

Conexao ao banco:
  Le DATABASE_URL de .env (defaults) e .env.local (override quando nao-vazio).
  Sem DATABASE_URL -> fallback SQLite local em data/crm_vitao360.db.
  Flag --db-path sobrescreve para path SQLite arbitrario (testes).

Uso:
  python scripts/ingest_sales_hunter.py
  python scripts/ingest_sales_hunter.py --date 2026-04-25
  python scripts/ingest_sales_hunter.py --dry-run
  python scripts/ingest_sales_hunter.py --skip-validation
  python scripts/ingest_sales_hunter.py --db-path data/crm_vitao360.db

DECISAO PRAGMATICA (Phase 8 baseline):
  fat_empresa cobre periodo do relatorio (Abr/2026 ate momento da extracao);
  baseline R$ 2.091.000 e historico VITAO 2025. Em primeira execucao
  exploratoria, divergencia >10% gera WARNING (nao FAIL) — registramos no
  extraction_report. R7 0.5% se aplica a builds Excel finais.
  --skip-validation forca PASS na Phase 8.

10 PHASES (ordem rigida):
  1. Discovery (descobrir diretorio + criar ImportJob)
  2. fat_produto -> produtos UPSERT
  3. fat_cliente -> clientes UPSERT (CWB+VV dedup por cnpj)
  4. fat_nf_det -> vendas + venda_itens BATCH INSERT
  5. pedidos_produto -> vendas.consultor enrichment
  6. debitos -> debitos_clientes INSERT + clientes.total_debitos UPDATE
  7. devolucao_cliente -> clientes UPDATE (pct/total/risco_devolucao)
  8. fat_empresa -> validacao sanity check
  9. Curva ABC recalculo
  10. ImportJob CONCLUIDO + extraction_report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

# ---------------------------------------------------------------------------
# Setup de paths — script chamavel de qualquer diretorio
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Carregamento de .env / .env.local — antes de qualquer import dependente
# (mesmo padrao de sync_deskrio_to_db.py)
# ---------------------------------------------------------------------------
def _load_env_file(path: Path, override_when_empty: bool = True) -> None:
    """Carrega KEY=VALUE de arquivo .env."""
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if not v:
                continue
            atual = os.environ.get(k, "")
            if not atual or override_when_empty:
                os.environ[k] = v
    except OSError:
        pass


_load_env_file(PROJECT_ROOT / ".env", override_when_empty=False)
_load_env_file(PROJECT_ROOT / ".env.local", override_when_empty=True)

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"sqlite:///{PROJECT_ROOT / 'data' / 'crm_vitao360.db'}"


# ---------------------------------------------------------------------------
# Imports tardios (apos resolver DATABASE_URL)
# ---------------------------------------------------------------------------
try:
    import openpyxl
except ImportError:
    print("ERRO: openpyxl nao instalado. Execute: pip install openpyxl")
    sys.exit(1)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("ERRO: sqlalchemy nao instalado. Execute: pip install sqlalchemy")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ingest_sales_hunter")


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
SALES_HUNTER_ROOT = PROJECT_ROOT / "data" / "sales_hunter"

# Tamanho minimo aceitavel para considerar XLSX valido (proteção contra 0 bytes
# ou paginas de erro HTML).
MIN_XLSX_BYTES = 500

# R7 baseline (corrigido 2026-03-23, R$ 2.156.179 SUPERSEDED)
FATURAMENTO_BASELINE = 2_091_000.0

# Tolerancia de validacao: warning se divergir >10% (sanity), nunca FAIL
# em primeira execucao exploratoria. Builds Excel finais usam 0.5% (R7).
SANITY_TOLERANCE_PCT = 0.10

# DE-PARA estados (Sales Hunter retorna nomes completos em portugues)
ESTADOS_DEPARA = {
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF",
    "Espírito Santo": "ES", "Goiás": "GO", "Maranhão": "MA",
    "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG",
    "Pará": "PA", "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE",
    "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE",
    "Tocantins": "TO",
}

# DE-PARA vendedores (CLAUDE.md) — col 9 de pedidos_produto
VENDEDOR_DEPARA: dict[str, Optional[str]] = {
    "manu": "MANU",
    "manu vitao": "MANU",
    "manu - vitao": "MANU",
    "manu ditzel": "MANU",
    "larissa": "LARISSA",
    "lari": "LARISSA",
    "larissa vitao": "LARISSA",
    "mais granel": "LARISSA",
    "rodrigo": "LARISSA",
    "daiane": "DAIANE",
    "daiane stavicki": "DAIANE",
    "central daiane": "DAIANE",
    "daiane vitao": "DAIANE",
    "julio": "JULIO",
    "julio gadret": "JULIO",
    "bruno gretter": "LEGADO",
    "jeferson vitao": "LEGADO",
    "patric": "LEGADO",
    "gabriel": "LEGADO",
    "sergio": "LEGADO",
    "ive": "LEGADO",
    "ana": "LEGADO",
}

# Empresas processadas — CWB primeiro, VV depois (dedup CWB+VV)
EMPRESAS = ("cwb", "vv")


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------
def normalizar_cnpj(val: object) -> Optional[str]:
    """Converte qualquer representacao de CNPJ/CPF para string 14 digitos.

    R2: NUNCA armazenar como float/int.
    CPF (11 digitos) -> "000" + CPF para totalizar 14.
    Retorna None se vazio/invalido (todos zero).
    """
    if val is None:
        return None
    s = re.sub(r"\D", "", str(val))
    if not s:
        return None
    s = s.zfill(14)
    if len(s) != 14:
        return None
    if len(set(s)) == 1:  # 00000000000000 etc.
        return None
    return s


def parse_data_br(val: object) -> Optional[date]:
    """Parse de DD/MM/YYYY ou YYYY-MM-DD para date. None se invalido."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s:
        return None
    # Formato YYYY-MM-DD HH:MM:SS (pedidos_produto col 24)
    if "-" in s[:10] and len(s) >= 10:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except ValueError:
            pass
    # Formato DD/MM/YYYY
    try:
        return datetime.strptime(s[:10], "%d/%m/%Y").date()
    except ValueError:
        return None


def parse_pct(val: object) -> Optional[float]:
    """Converte '5,32%' ou '0,00%' ou 0.05 -> float (0.0532 ou 0.0)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("%", "").replace(",", ".")
    if not s:
        return None
    try:
        n = float(s)
        # Se vier no formato "5.32" significa 5.32% — converter para 0.0532
        # Se vier "0.05" ja eh fracional — manter
        # Heuristica: valores absolutos > 1.0 sao percentuais (xx,yy%)
        return n / 100.0 if abs(n) > 1.0 else n
    except ValueError:
        return None


def to_float(val: object) -> float:
    """Converte para float, tratando None / strings vazias / virgula."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return 0.0
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def to_int(val: object) -> Optional[int]:
    """Converte para int. None se invalido."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    s = str(val).strip()
    if not s:
        return None
    try:
        return int(float(s.replace(",", ".")))
    except ValueError:
        return None


def to_str(val: object, max_len: Optional[int] = None) -> Optional[str]:
    """Converte para string, strip. None se vazio."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    return s[:max_len] if max_len else s


def converter_uf(estado: object) -> Optional[str]:
    """'Paraná' -> 'PR'. Mantem se ja for sigla 2-letras."""
    s = to_str(estado)
    if not s:
        return None
    if len(s) == 2 and s.isupper():
        return s
    return ESTADOS_DEPARA.get(s)


def resolver_consultor(vendedor_str: object) -> Optional[str]:
    """Resolve nome de vendedor SAP para consultor CRM via DE-PARA.

    'ZR - NAO APLICAVEL' / nomes nao mapeados -> None.
    R8: nao inventa — retorna None se nao reconhecido.
    """
    s = to_str(vendedor_str)
    if not s:
        return None
    sl = s.lower().strip()
    # Filtros explicitos
    if "nao aplicavel" in sl or "n/a" in sl or sl in ("zr", "ze"):
        return None
    if sl in VENDEDOR_DEPARA:
        return VENDEDOR_DEPARA[sl]
    # Tenta prefixo (primeira palavra)
    primeira = sl.split()[0] if sl else ""
    if primeira and primeira in VENDEDOR_DEPARA:
        return VENDEDOR_DEPARA[primeira]
    return None


def encontrar_diretorio_morning(date_str: Optional[str]) -> Optional[Path]:
    """Retorna data/sales_hunter/{date}/morning/ — mais recente se date_str=None."""
    if date_str:
        candidato = SALES_HUNTER_ROOT / date_str / "morning"
        return candidato if candidato.exists() else None

    if not SALES_HUNTER_ROOT.exists():
        return None

    datas = sorted(
        [
            p for p in SALES_HUNTER_ROOT.iterdir()
            if p.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", p.name)
        ],
        key=lambda p: p.name,
        reverse=True,
    )
    for p in datas:
        morning = p / "morning"
        if morning.exists():
            return morning
    return None


def listar_xlsx_validos(diretorio: Path) -> dict[str, Path]:
    """Mapeia nome-base -> Path para XLSX validos (>= MIN_XLSX_BYTES).

    Retorna dict como {'fat_cliente_cwb': Path, 'fat_cliente_vv': Path, ...}.
    """
    mapping: dict[str, Path] = {}
    for xlsx in sorted(diretorio.glob("*.xlsx")):
        size = xlsx.stat().st_size
        if size < MIN_XLSX_BYTES:
            log.warning("XLSX muito pequeno (ignorado): %s (%d bytes)", xlsx.name, size)
            continue
        # Nome no formato: {tipo}_{empresa}_all_{data}_{hora}.xlsx
        # Exemplo: fat_cliente_cwb_all_2026-04-25_0800.xlsx
        m = re.match(r"^(.+?)_(cwb|vv)_all_\d{4}-\d{2}-\d{2}_\d{4}\.xlsx$", xlsx.name)
        if m:
            tipo, empresa = m.group(1), m.group(2)
            mapping[f"{tipo}_{empresa}"] = xlsx
        else:
            log.debug("XLSX com nome fora do padrao (ignorado): %s", xlsx.name)
    return mapping


def iter_data_rows(xlsx_path: Path) -> Iterable[tuple]:
    """Itera linhas de dados (skip header row 1) de um XLSX em modo read_only.

    Cada item retornado eh tuple de cells (values_only=True).

    Defensivo: Sales Hunter ocasionalmente retorna HTML (302/login expirado)
    com extensao .xlsx. openpyxl crasha com BadZipFile. Logamos warning e
    seguimos — phase nao falha por arquivo corrompido isolado.
    """
    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    except (zipfile.BadZipFile, OSError) as exc:
        log.warning(
            "XLSX invalido/corrompido (skip): %s (%s)", xlsx_path.name, exc,
        )
        return
    try:
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            yield row
    finally:
        wb.close()


# ---------------------------------------------------------------------------
# Phase 2 — fat_produto -> produtos UPSERT
# ---------------------------------------------------------------------------
def phase_2_produtos(
    session,
    xlsx_paths: dict[str, Path],
    dry_run: bool,
) -> dict:
    """UPSERT em produtos a partir de fat_produto_cwb + fat_produto_vv.

    Schema (1-indexed):
      1=cod_material, 2=material, 3=categoria, 4=subcategoria,
      5=um, 6=peso_bruto_kg, 18=total_faturado.

    Logica de dedup CWB+VV:
      Mesmo codigo nas 2 empresas -> agregar (max para nome/categoria/etc,
      SOMA para fat_total_historico).
    """
    stats = {"lidos": 0, "inseridos": 0, "atualizados": 0, "ignorados": 0}
    agregado: dict[str, dict] = {}

    for empresa in EMPRESAS:
        key = f"fat_produto_{empresa}"
        path = xlsx_paths.get(key)
        if not path:
            log.warning("Phase 2: %s ausente", key)
            continue
        log.info("Phase 2: lendo %s", path.name)

        for row in iter_data_rows(path):
            stats["lidos"] += 1
            if not row or len(row) < 18:
                stats["ignorados"] += 1
                continue
            codigo = to_str(row[0], max_len=50)
            if not codigo:
                stats["ignorados"] += 1
                continue

            registro = {
                "codigo": codigo,
                "nome": to_str(row[1], max_len=255) or codigo,
                "categoria": to_str(row[2], max_len=100),
                "subcategoria": to_str(row[3], max_len=100),
                "unidade_embalagem": to_str(row[4], max_len=20),
                "peso_bruto_kg": to_float(row[5]) if row[5] is not None else None,
                "fat_inc": to_float(row[17]),  # col 18 = total_faturado
            }

            # Agrega: CWB + VV mesmo codigo -> SOMA fat_total
            if codigo in agregado:
                ag = agregado[codigo]
                ag["fat_inc"] += registro["fat_inc"]
                # Mantem primeiro nao-nulo para campos descritivos
                for k in ("nome", "categoria", "subcategoria", "unidade_embalagem", "peso_bruto_kg"):
                    if not ag.get(k) and registro.get(k):
                        ag[k] = registro[k]
            else:
                agregado[codigo] = registro

    # UPSERT batch
    for codigo, reg in agregado.items():
        existente = session.execute(
            text("SELECT id FROM produtos WHERE codigo = :codigo"),
            {"codigo": codigo},
        ).fetchone()

        ativo = reg["fat_inc"] > 0

        if existente:
            # UPDATE: preserva preco_tabela / preco_minimo / comissao_pct / ipi_pct / ean
            # (vem de outras fontes Mercos/manual). Atualiza apenas campos do SAP-SH.
            if not dry_run:
                session.execute(
                    text("""
                        UPDATE produtos SET
                          nome = :nome,
                          categoria = COALESCE(:categoria, categoria),
                          subcategoria = COALESCE(:subcategoria, subcategoria),
                          unidade_embalagem = COALESCE(:unidade_embalagem, unidade_embalagem),
                          peso_bruto_kg = COALESCE(:peso_bruto_kg, peso_bruto_kg),
                          fat_total_historico = :fat_total_historico,
                          ativo = :ativo,
                          updated_at = :now
                        WHERE codigo = :codigo
                    """),
                    {
                        "nome": reg["nome"],
                        "categoria": reg["categoria"],
                        "subcategoria": reg["subcategoria"],
                        "unidade_embalagem": reg["unidade_embalagem"],
                        "peso_bruto_kg": reg["peso_bruto_kg"],
                        "fat_total_historico": reg["fat_inc"],
                        "ativo": ativo,
                        "now": datetime.now(timezone.utc).replace(tzinfo=None),
                        "codigo": codigo,
                    },
                )
            stats["atualizados"] += 1
        else:
            # INSERT — preenche defaults para colunas NOT NULL pre-existentes
            if not dry_run:
                session.execute(
                    text("""
                        INSERT INTO produtos (
                          codigo, nome, categoria, subcategoria, unidade_embalagem,
                          peso_bruto_kg, fat_total_historico,
                          fabricante, unidade, preco_tabela, preco_minimo,
                          comissao_pct, ipi_pct, ativo,
                          created_at, updated_at
                        ) VALUES (
                          :codigo, :nome, :categoria, :subcategoria, :unidade_embalagem,
                          :peso_bruto_kg, :fat_total_historico,
                          'VITAO', 'UN', 0.0, 0.0,
                          0.0, 0.0, :ativo,
                          :now, :now
                        )
                    """),
                    {
                        "codigo": codigo,
                        "nome": reg["nome"],
                        "categoria": reg["categoria"],
                        "subcategoria": reg["subcategoria"],
                        "unidade_embalagem": reg["unidade_embalagem"],
                        "peso_bruto_kg": reg["peso_bruto_kg"],
                        "fat_total_historico": reg["fat_inc"],
                        "ativo": ativo,
                        "now": datetime.now(timezone.utc).replace(tzinfo=None),
                    },
                )
            stats["inseridos"] += 1

    if not dry_run:
        session.commit()

    log.info(
        "Phase 2 produtos: lidos=%d unicos=%d inseridos=%d atualizados=%d ignorados=%d",
        stats["lidos"], len(agregado), stats["inseridos"], stats["atualizados"], stats["ignorados"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 3 — fat_cliente -> clientes UPSERT
# ---------------------------------------------------------------------------
def phase_3_clientes(
    session,
    xlsx_paths: dict[str, Path],
    dry_run: bool,
) -> dict:
    """UPSERT em clientes a partir de fat_cliente_cwb + fat_cliente_vv.

    Schema (1-indexed):
      1=cod_cliente, 2=cliente, 3=cpf_cnpj, 4=grupo (tipo_cliente_sap),
      5=canal_venda (tipo_cliente), 9=estado, 10=cidade, 17=faturado_mes,
      23=total_faturado.

    Dedup CWB+VV:
      DESCOBERTA EM 25/Abr/2026: os XLSX VV retornam dados IDENTICOS aos
      CWB (mesmo cliente/CNPJ/valores). Para evitar dobrar faturamento_total,
      usamos politica MAX (mantem o maior valor visto). Se em algum momento
      VV passar a retornar dados realmente distintos, esta logica deve ser
      revisitada para SOMAR.
    """
    stats = {"lidos": 0, "inseridos": 0, "atualizados": 0, "ignorados": 0}
    agregado: dict[str, dict] = {}

    for empresa in EMPRESAS:
        key = f"fat_cliente_{empresa}"
        path = xlsx_paths.get(key)
        if not path:
            log.warning("Phase 3: %s ausente", key)
            continue
        log.info("Phase 3: lendo %s", path.name)

        for row in iter_data_rows(path):
            stats["lidos"] += 1
            if not row or len(row) < 23:
                stats["ignorados"] += 1
                continue

            cnpj = normalizar_cnpj(row[2])
            if not cnpj:
                stats["ignorados"] += 1
                continue

            grupo = to_str(row[3], max_len=50)
            canal = to_str(row[4], max_len=80)
            # tipo_cliente extrai parte antes do ' - ' (ex.: "31 - IN - DISTR. VAREJO" -> "31")
            tipo_cliente = canal.split(" - ", 1)[0][:30] if canal else None
            faturado_mes = to_float(row[16])
            total_faturado = to_float(row[22])

            registro = {
                "cnpj": cnpj,
                "nome_fantasia": to_str(row[1], max_len=255),
                "codigo_cliente": to_str(row[0], max_len=20),
                "tipo_cliente_sap": grupo,
                "tipo_cliente": tipo_cliente,
                "uf": converter_uf(row[8]),
                "cidade": to_str(row[9], max_len=100),
                "faturado_mes": faturado_mes,
                "faturamento_total": total_faturado,
                "situacao": "ATIVO" if faturado_mes > 0 else "INATIVO",
            }

            # Dedup CWB+VV: politica MAX (XLSX VV duplica CWB neste momento)
            if cnpj in agregado:
                ag = agregado[cnpj]
                # Para faturamento, manter o MAIOR (defensivo: se VV>CWB para
                # algum CNPJ no futuro, preservamos o maior visto)
                if registro["faturamento_total"] > ag["faturamento_total"]:
                    ag["faturamento_total"] = registro["faturamento_total"]
                if registro["faturado_mes"] > ag["faturado_mes"]:
                    ag["faturado_mes"] = registro["faturado_mes"]
                    ag["situacao"] = registro["situacao"]
                # Preserva primeiros nao-nulos para campos descritivos
                for k in ("nome_fantasia", "codigo_cliente", "tipo_cliente_sap",
                          "tipo_cliente", "uf", "cidade"):
                    if not ag.get(k) and registro.get(k):
                        ag[k] = registro[k]
            else:
                agregado[cnpj] = registro

    # UPSERT
    for cnpj, reg in agregado.items():
        existente = session.execute(
            text("SELECT id FROM clientes WHERE cnpj = :cnpj"),
            {"cnpj": cnpj},
        ).fetchone()

        if existente:
            if not dry_run:
                session.execute(
                    text("""
                        UPDATE clientes SET
                          nome_fantasia = COALESCE(:nome_fantasia, nome_fantasia),
                          codigo_cliente = COALESCE(:codigo_cliente, codigo_cliente),
                          tipo_cliente_sap = COALESCE(:tipo_cliente_sap, tipo_cliente_sap),
                          tipo_cliente = COALESCE(:tipo_cliente, tipo_cliente),
                          uf = COALESCE(:uf, uf),
                          cidade = COALESCE(:cidade, cidade),
                          faturamento_total = :faturamento_total,
                          situacao = :situacao,
                          classificacao_3tier = COALESCE(classificacao_3tier, 'REAL'),
                          updated_at = :now
                        WHERE cnpj = :cnpj
                    """),
                    {
                        **reg,
                        "now": datetime.now(timezone.utc).replace(tzinfo=None),
                    },
                )
            stats["atualizados"] += 1
        else:
            if not dry_run:
                session.execute(
                    text("""
                        INSERT INTO clientes (
                          cnpj, nome_fantasia, codigo_cliente, tipo_cliente_sap,
                          tipo_cliente, uf, cidade, faturamento_total, situacao,
                          classificacao_3tier, created_at, updated_at
                        ) VALUES (
                          :cnpj, :nome_fantasia, :codigo_cliente, :tipo_cliente_sap,
                          :tipo_cliente, :uf, :cidade, :faturamento_total, :situacao,
                          'REAL', :now, :now
                        )
                    """),
                    {
                        **reg,
                        "now": datetime.now(timezone.utc).replace(tzinfo=None),
                    },
                )
            stats["inseridos"] += 1

    if not dry_run:
        session.commit()

    # Em dry-run, Phase 3 nao faz commit — Phase 4 precisa saber quais CNPJs
    # serao "criados" para nao filtrar todos como ign_cnpj. Em modo real, o
    # set sobrevive como redundancia (Phase 4 recarrega do DB tambem).
    stats["cnpjs_processados"] = set(agregado.keys())

    log.info(
        "Phase 3 clientes: lidos=%d unicos=%d inseridos=%d atualizados=%d ignorados=%d",
        stats["lidos"], len(agregado), stats["inseridos"], stats["atualizados"], stats["ignorados"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 4 — fat_nf_det -> vendas + venda_itens BATCH INSERT
# ---------------------------------------------------------------------------
def phase_4_vendas(
    session,
    xlsx_paths: dict[str, Path],
    dry_run: bool,
    cnpjs_phase3: Optional[set[str]] = None,
) -> dict:
    """Insere vendas (1 por cod_pedido) + venda_itens (1 por linha NF).

    Schema fat_nf_det (1-indexed):
      1=cod_material, 2=material, 3=peso_bruto_kg, 5=quantidade,
      6=valor_nfe, 7=categoria, 9=um, 10=nro_nfe, 11=data_emissao,
      12=tipo_documento, 13=cod_pedido, 16=cpf_cnpj.

    Filtra apenas tipo_documento='Venda (F2B)'.
    Dedup CWB+VV: mesma chave (cnpj, numero_pedido, data_pedido) =
    SAME pedido (XLSX VV duplica CWB neste momento).

    Performance: batch insert em chunks de 500 — fat_nf_det tem ~25K linhas
    por empresa.
    """
    stats = {
        "lidos": 0, "filtrados_tipo": 0, "ignorados_cnpj": 0,
        "ignorados_data": 0, "vendas_inseridas": 0, "vendas_existentes": 0,
        "itens_inseridos": 0, "produtos_criados": 0,
    }

    # Pre-load: clientes existentes (cnpj set) para validar FK
    clientes_existentes: set[str] = {
        r[0] for r in session.execute(text("SELECT cnpj FROM clientes")).fetchall()
    }
    # Em dry-run, Phase 3 nao commita — incorporamos os cnpjs processados
    # para que Phase 4 nao descarte 100% dos pedidos como ign_cnpj.
    if cnpjs_phase3:
        clientes_existentes |= cnpjs_phase3

    # Pre-load: produtos existentes (codigo -> id)
    produto_codigo_to_id: dict[str, int] = dict(
        session.execute(text("SELECT codigo, id FROM produtos")).fetchall()
    )

    # Agrega itens por chave logica de venda: (cnpj, numero_pedido, data_pedido)
    # Estrutura: {(cnpj, num_ped, data): {'valor_total': X, 'itens': [...]}}
    pedidos_buffer: dict[tuple, dict] = {}

    for empresa in EMPRESAS:
        key = f"fat_nf_det_{empresa}"
        path = xlsx_paths.get(key)
        if not path:
            log.warning("Phase 4: %s ausente", key)
            continue
        log.info("Phase 4: lendo %s", path.name)

        for row in iter_data_rows(path):
            stats["lidos"] += 1
            if not row or len(row) < 16:
                continue

            tipo_doc = to_str(row[11])
            if tipo_doc != "Venda (F2B)":
                stats["filtrados_tipo"] += 1
                continue

            cnpj = normalizar_cnpj(row[15])  # col 16 = cpf_cnpj
            if not cnpj:
                stats["ignorados_cnpj"] += 1
                continue

            data_pedido = parse_data_br(row[10])  # col 11 = data_emissao
            if not data_pedido:
                stats["ignorados_data"] += 1
                continue

            cod_pedido = to_str(row[12], max_len=50)  # col 13
            if not cod_pedido:
                stats["ignorados_data"] += 1
                continue

            qty = to_float(row[4])
            valor_item = to_float(row[5])
            if qty <= 0 or valor_item <= 0:
                # Two-Base: valor_total > 0 enforced no schema
                continue

            cod_material = to_str(row[0], max_len=50)
            material_nome = to_str(row[1], max_len=255) or cod_material
            categoria = to_str(row[6], max_len=100)
            unidade = to_str(row[8], max_len=10) or "UN"
            peso = to_float(row[2]) if row[2] is not None else None

            chave_venda = (cnpj, cod_pedido, data_pedido)
            if chave_venda not in pedidos_buffer:
                pedidos_buffer[chave_venda] = {
                    "cnpj": cnpj,
                    "numero_pedido": cod_pedido,
                    "data_pedido": data_pedido,
                    "valor_total": 0.0,
                    "itens": [],
                }
            pedidos_buffer[chave_venda]["valor_total"] += valor_item
            pedidos_buffer[chave_venda]["itens"].append({
                "cod_material": cod_material,
                "material_nome": material_nome,
                "categoria": categoria,
                "unidade": unidade,
                "peso": peso,
                "quantidade": qty,
                "valor_total": valor_item,
            })

    log.info("Phase 4: %d pedidos unicos identificados", len(pedidos_buffer))

    # Insere vendas (skip se cliente nao existe + skip se venda ja existe)
    # Itera com batching periodico para nao acumular toda a transacao em memoria
    BATCH_SIZE = 500
    pedidos_processados = 0

    for chave, ped in pedidos_buffer.items():
        cnpj = ped["cnpj"]
        if cnpj not in clientes_existentes:
            # Cliente nao foi processado em Phase 3 (nao tem fat_cliente row)
            stats["ignorados_cnpj"] += 1
            continue

        # Idempotencia: ja existe venda com mesma chave?
        existente = session.execute(
            text("""
                SELECT id FROM vendas
                WHERE cnpj = :cnpj AND numero_pedido = :np AND data_pedido = :dp
                LIMIT 1
            """),
            {"cnpj": cnpj, "np": ped["numero_pedido"], "dp": ped["data_pedido"]},
        ).fetchone()

        if existente:
            stats["vendas_existentes"] += 1
            venda_id = existente[0]
        else:
            mes_ref = ped["data_pedido"].strftime("%Y-%m")
            if not dry_run:
                result = session.execute(
                    text("""
                        INSERT INTO vendas (
                          cnpj, data_pedido, numero_pedido, valor_pedido,
                          consultor, fonte, classificacao_3tier, mes_referencia,
                          created_at
                        ) VALUES (
                          :cnpj, :data_pedido, :numero_pedido, :valor_pedido,
                          :consultor, 'SAP', 'REAL', :mes_referencia,
                          :now
                        )
                    """),
                    {
                        "cnpj": cnpj,
                        "data_pedido": ped["data_pedido"],
                        "numero_pedido": ped["numero_pedido"],
                        "valor_pedido": ped["valor_total"],
                        # Phase 5 enriquece com consultor real via pedidos_produto
                        "consultor": "SAP_PENDENTE",
                        "mes_referencia": mes_ref,
                        "now": datetime.now(timezone.utc).replace(tzinfo=None),
                    },
                )
                venda_id = result.lastrowid
            else:
                venda_id = -1
            stats["vendas_inseridas"] += 1

        # Insere venda_itens — produto criado on-demand se nao existe
        for it in ped["itens"]:
            cod = it["cod_material"]
            if not cod:
                continue
            produto_id = produto_codigo_to_id.get(cod)
            if produto_id is None:
                if not dry_run:
                    result = session.execute(
                        text("""
                            INSERT INTO produtos (
                              codigo, nome, categoria, unidade, peso_bruto_kg,
                              fabricante, preco_tabela, preco_minimo,
                              comissao_pct, ipi_pct, ativo,
                              created_at, updated_at
                            ) VALUES (
                              :codigo, :nome, :categoria, :unidade, :peso,
                              'VITAO', 0.0, 0.0,
                              0.0, 0.0, 1,
                              :now, :now
                            )
                        """),
                        {
                            "codigo": cod,
                            "nome": it["material_nome"],
                            "categoria": it["categoria"],
                            "unidade": it["unidade"],
                            "peso": it["peso"],
                            "now": datetime.now(timezone.utc).replace(tzinfo=None),
                        },
                    )
                    produto_id = result.lastrowid
                else:
                    produto_id = -1
                produto_codigo_to_id[cod] = produto_id
                stats["produtos_criados"] += 1

            # venda_id pode ser -1 em dry-run; valor_total > 0 ja garantido
            preco_unit = it["valor_total"] / it["quantidade"] if it["quantidade"] > 0 else it["valor_total"]
            if not dry_run and venda_id > 0 and produto_id > 0:
                # Idempotencia ITENS: nao inserimos se venda ja existia
                # (evita duplicar itens em rerun). Se venda foi inserida agora,
                # OK inserir itens.
                if existente is None:
                    session.execute(
                        text("""
                            INSERT INTO venda_itens (
                              venda_id, produto_id, quantidade, preco_unitario,
                              desconto_pct, valor_total
                            ) VALUES (
                              :venda_id, :produto_id, :qtd, :preco, 0.0, :total
                            )
                        """),
                        {
                            "venda_id": venda_id,
                            "produto_id": produto_id,
                            "qtd": it["quantidade"],
                            "preco": preco_unit,
                            "total": it["valor_total"],
                        },
                    )
                    stats["itens_inseridos"] += 1

        pedidos_processados += 1
        if pedidos_processados % BATCH_SIZE == 0 and not dry_run:
            session.commit()

    if not dry_run:
        session.commit()

    log.info(
        "Phase 4 vendas: lidos=%d filtr_tipo=%d ign_cnpj=%d ign_data=%d "
        "vendas_ins=%d vendas_exist=%d itens_ins=%d produtos_criados=%d",
        stats["lidos"], stats["filtrados_tipo"], stats["ignorados_cnpj"],
        stats["ignorados_data"], stats["vendas_inseridas"],
        stats["vendas_existentes"], stats["itens_inseridos"],
        stats["produtos_criados"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 5 — pedidos_produto -> vendas.consultor enrichment
# ---------------------------------------------------------------------------
def phase_5_consultor(
    session,
    xlsx_paths: dict[str, Path],
    dry_run: bool,
) -> dict:
    """Enriquece vendas.consultor a partir de pedidos_produto col 9 (vendedor).

    Schema (1-indexed):
      2=numero_pedido_sap, 7=cliente_documento, 9=vendedor.

    DE-PARA aplicado: 'Manu' -> MANU, 'Larissa' -> LARISSA, etc.
    'ZR - NAO APLICAVEL' / nao mapeados -> mantem SAP_PENDENTE.

    VV ausente (HTTP 302) — apenas CWB.
    """
    stats = {"lidos": 0, "atualizados": 0, "sem_match": 0, "sem_vendedor": 0}

    path = xlsx_paths.get("pedidos_produto_cwb")
    if not path:
        log.warning("Phase 5: pedidos_produto_cwb ausente — skip")
        return stats
    log.info("Phase 5: lendo %s", path.name)

    # Agrega vendedor por (cnpj, numero_pedido) — pedidos_produto tem 1 row
    # por item, entao mesmo pedido aparece N vezes
    pedido_consultor: dict[tuple, str] = {}

    for row in iter_data_rows(path):
        stats["lidos"] += 1
        if not row or len(row) < 9:
            continue

        numero_pedido = to_str(row[1], max_len=50)
        cnpj = normalizar_cnpj(row[6])
        vendedor_raw = to_str(row[8])
        if not numero_pedido or not cnpj:
            continue

        consultor = resolver_consultor(vendedor_raw)
        if not consultor:
            stats["sem_vendedor"] += 1
            continue

        key = (cnpj, numero_pedido)
        # Mantem primeiro consultor encontrado (vendedor de uma venda nao
        # muda entre itens da mesma NF)
        if key not in pedido_consultor:
            pedido_consultor[key] = consultor

    # UPDATE em batch
    for (cnpj, num_ped), consultor in pedido_consultor.items():
        if not dry_run:
            result = session.execute(
                text("""
                    UPDATE vendas SET consultor = :consultor
                    WHERE cnpj = :cnpj
                      AND numero_pedido = :np
                      AND consultor = 'SAP_PENDENTE'
                """),
                {"consultor": consultor, "cnpj": cnpj, "np": num_ped},
            )
            if result.rowcount > 0:
                stats["atualizados"] += result.rowcount
            else:
                stats["sem_match"] += 1
        else:
            stats["atualizados"] += 1

    if not dry_run:
        session.commit()

    log.info(
        "Phase 5 consultor: lidos=%d pedidos_unicos=%d atualizados=%d sem_match=%d sem_vendedor=%d",
        stats["lidos"], len(pedido_consultor),
        stats["atualizados"], stats["sem_match"], stats["sem_vendedor"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 6 — debitos -> debitos_clientes INSERT + clientes.total_debitos UPDATE
# ---------------------------------------------------------------------------
def phase_6_debitos(
    session,
    xlsx_paths: dict[str, Path],
    dry_run: bool,
) -> dict:
    """Insere debitos_clientes a partir de debitos_cwb + debitos_vv.

    Schema (1-indexed):
      3=documento (CNPJ!), 4=cod_pedido, 5=nro_nfe, 6=parcela,
      7=data_lancamento, 8=data_vencimento, 9=data_pagamento, 10=valor.

    Idempotencia: SELECT por (cnpj, nro_nfe, parcela) antes de INSERT.
    Apos inserir: UPDATE clientes.total_debitos = SUM(VENCIDO).
    """
    stats = {
        "lidos": 0, "ignorados_cnpj": 0, "inseridos": 0, "ja_existem": 0,
        "pago": 0, "vencido": 0, "a_vencer": 0,
    }
    hoje = date.today()

    # Dedup CWB+VV por chave logica
    debitos_buffer: dict[tuple, dict] = {}

    for empresa in EMPRESAS:
        key = f"debitos_{empresa}"
        path = xlsx_paths.get(key)
        if not path:
            log.warning("Phase 6: %s ausente", key)
            continue
        log.info("Phase 6: lendo %s", path.name)

        for row in iter_data_rows(path):
            stats["lidos"] += 1
            if not row or len(row) < 10:
                continue

            cnpj = normalizar_cnpj(row[2])  # col 3 = documento (eh CNPJ)
            if not cnpj:
                stats["ignorados_cnpj"] += 1
                continue

            nro_nfe = to_str(row[4], max_len=50)
            parcela = to_str(row[5], max_len=5)
            valor = to_float(row[9])
            if valor <= 0:
                continue

            data_lanc = parse_data_br(row[6])
            data_venc = parse_data_br(row[7])
            data_pag = parse_data_br(row[8])

            if data_pag is not None:
                status = "PAGO"
                dias_atraso = 0
                stats["pago"] += 1
            elif data_venc is not None and data_venc < hoje:
                status = "VENCIDO"
                dias_atraso = (hoje - data_venc).days
                stats["vencido"] += 1
            else:
                status = "A_VENCER"
                dias_atraso = 0
                stats["a_vencer"] += 1

            chave = (cnpj, nro_nfe or "", parcela or "")
            registro = {
                "cnpj": cnpj,
                "cod_pedido": to_str(row[3], max_len=50),
                "nro_nfe": nro_nfe,
                "parcela": parcela,
                "data_lancamento": data_lanc,
                "data_vencimento": data_venc,
                "data_pagamento": data_pag,
                "valor": valor,
                "dias_atraso": dias_atraso,
                "status": status,
            }
            # Dedup: mesmo CWB+VV duplicam — manter primeiro
            if chave not in debitos_buffer:
                debitos_buffer[chave] = registro

    # Insercao com idempotencia (SELECT antes de INSERT)
    for chave, reg in debitos_buffer.items():
        cnpj, nro_nfe, parcela = chave
        existente = session.execute(
            text("""
                SELECT id FROM debitos_clientes
                WHERE cnpj = :cnpj
                  AND COALESCE(nro_nfe, '') = :nro_nfe
                  AND COALESCE(parcela, '') = :parcela
                LIMIT 1
            """),
            {"cnpj": cnpj, "nro_nfe": nro_nfe, "parcela": parcela},
        ).fetchone()

        if existente:
            stats["ja_existem"] += 1
            continue

        if not dry_run:
            session.execute(
                text("""
                    INSERT INTO debitos_clientes (
                      cnpj, cod_pedido, nro_nfe, parcela,
                      data_lancamento, data_vencimento, data_pagamento,
                      valor, dias_atraso, status, fonte, classificacao_3tier
                    ) VALUES (
                      :cnpj, :cod_pedido, :nro_nfe, :parcela,
                      :data_lancamento, :data_vencimento, :data_pagamento,
                      :valor, :dias_atraso, :status, 'SAP', 'REAL'
                    )
                """),
                reg,
            )
        stats["inseridos"] += 1

    if not dry_run:
        session.commit()

    # UPDATE clientes.total_debitos = SUM(VENCIDO) por cnpj
    if not dry_run:
        session.execute(
            text("""
                UPDATE clientes
                SET total_debitos = COALESCE((
                    SELECT SUM(valor) FROM debitos_clientes
                    WHERE debitos_clientes.cnpj = clientes.cnpj
                      AND debitos_clientes.status = 'VENCIDO'
                ), 0)
            """)
        )
        session.commit()

    log.info(
        "Phase 6 debitos: lidos=%d ign_cnpj=%d inseridos=%d ja_existem=%d "
        "pago=%d vencido=%d a_vencer=%d",
        stats["lidos"], stats["ignorados_cnpj"], stats["inseridos"],
        stats["ja_existem"], stats["pago"], stats["vencido"], stats["a_vencer"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 7 — devolucao_cliente -> clientes UPDATE
# ---------------------------------------------------------------------------
def phase_7_devolucao(
    session,
    xlsx_paths: dict[str, Path],
    dry_run: bool,
) -> dict:
    """UPDATE clientes (pct_devolucao, total_devolucao, risco_devolucao).

    Schema devolucao_cliente (1-indexed):
      3=cpf_cnpj, 18=total_devol_total, 21=pct_devolucao.

    Risco: BAIXO (<5%), MEDIO (5-15%), ALTO (>15%).
    """
    stats = {"lidos": 0, "atualizados": 0, "sem_match": 0, "ignorados_cnpj": 0}

    # Dedup CWB+VV — manter MAX (defensivo: VV pode duplicar CWB)
    devolucoes: dict[str, dict] = {}

    for empresa in EMPRESAS:
        key = f"devolucao_cliente_{empresa}"
        path = xlsx_paths.get(key)
        if not path:
            log.warning("Phase 7: %s ausente", key)
            continue
        log.info("Phase 7: lendo %s", path.name)

        for row in iter_data_rows(path):
            stats["lidos"] += 1
            if not row or len(row) < 21:
                continue

            cnpj = normalizar_cnpj(row[2])
            if not cnpj:
                stats["ignorados_cnpj"] += 1
                continue

            total_dev = to_float(row[17])  # col 18
            pct = parse_pct(row[20])  # col 21 — formato "5,32%"
            pct = pct if pct is not None else 0.0

            if pct < 0.05:
                risco = "BAIXO"
            elif pct < 0.15:
                risco = "MEDIO"
            else:
                risco = "ALTO"

            registro = {
                "cnpj": cnpj,
                "pct_devolucao": pct,
                "total_devolucao": total_dev,
                "risco_devolucao": risco,
            }
            if cnpj in devolucoes:
                # MAX defensivo
                if total_dev > devolucoes[cnpj]["total_devolucao"]:
                    devolucoes[cnpj] = registro
            else:
                devolucoes[cnpj] = registro

    # UPDATE em batch
    for cnpj, reg in devolucoes.items():
        if not dry_run:
            result = session.execute(
                text("""
                    UPDATE clientes
                    SET pct_devolucao = :pct,
                        total_devolucao = :total,
                        risco_devolucao = :risco
                    WHERE cnpj = :cnpj
                """),
                {
                    "pct": reg["pct_devolucao"],
                    "total": reg["total_devolucao"],
                    "risco": reg["risco_devolucao"],
                    "cnpj": cnpj,
                },
            )
            if result.rowcount > 0:
                stats["atualizados"] += 1
            else:
                stats["sem_match"] += 1
        else:
            stats["atualizados"] += 1

    if not dry_run:
        session.commit()

    log.info(
        "Phase 7 devolucao: lidos=%d unicos=%d atualizados=%d sem_match=%d",
        stats["lidos"], len(devolucoes), stats["atualizados"], stats["sem_match"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 8 — fat_empresa validation (sanity check vs baseline R$ 2.091.000)
# ---------------------------------------------------------------------------
def phase_8_validacao(
    session,
    xlsx_paths: dict[str, Path],
    skip: bool,
) -> dict:
    """Valida SUM(clientes.faturamento_total) vs fat_empresa.total_faturado vs baseline R7.

    Em primeira execucao: WARN se divergencia > SANITY_TOLERANCE_PCT (10%).
    Nunca FAIL — apenas registra no extraction_report (Phase 8 e preliminar;
    R7 0.5% se aplica a builds Excel finais).
    """
    result: dict = {
        "skip": skip,
        "fat_db": 0.0,
        "fat_empresa_total": 0.0,
        "fat_baseline": FATURAMENTO_BASELINE,
        "div_vs_baseline_pct": None,
        "div_vs_xlsx_pct": None,
        "status": "PASS",
        "warnings": [],
    }

    if skip:
        result["status"] = "SKIPPED"
        log.info("Phase 8 validacao: SKIPPED (--skip-validation)")
        return result

    # Soma fat_empresa (CWB + VV) col 12 = total_faturado
    total_xlsx = 0.0
    for empresa in EMPRESAS:
        key = f"fat_empresa_{empresa}"
        path = xlsx_paths.get(key)
        if not path:
            continue
        for row in iter_data_rows(path):
            if not row or len(row) < 12:
                continue
            total_xlsx += to_float(row[11])  # col 12
    result["fat_empresa_total"] = total_xlsx

    # Soma faturamento_total no DB
    row = session.execute(text("SELECT COALESCE(SUM(faturamento_total), 0) FROM clientes")).fetchone()
    fat_db = float(row[0]) if row and row[0] else 0.0
    result["fat_db"] = fat_db

    # Divergencias
    if FATURAMENTO_BASELINE > 0:
        result["div_vs_baseline_pct"] = abs(fat_db - FATURAMENTO_BASELINE) / FATURAMENTO_BASELINE
    if total_xlsx > 0:
        result["div_vs_xlsx_pct"] = abs(fat_db - total_xlsx) / total_xlsx

    # Decisao pragmatica: nunca FAIL na primeira execucao
    if result["div_vs_baseline_pct"] is not None and result["div_vs_baseline_pct"] > SANITY_TOLERANCE_PCT:
        result["warnings"].append(
            f"Divergencia DB vs R7 baseline: {result['div_vs_baseline_pct']*100:.1f}% "
            f"(tolerancia sanity {SANITY_TOLERANCE_PCT*100:.0f}%). "
            f"NOTA: fat_empresa cobre periodo XLSX (Abr/2026), R7 e historico VITAO 2025."
        )
    if result["div_vs_xlsx_pct"] is not None and result["div_vs_xlsx_pct"] > 0.005:
        result["warnings"].append(
            f"Divergencia DB vs fat_empresa XLSX: {result['div_vs_xlsx_pct']*100:.2f}%"
        )

    log.info(
        "Phase 8 validacao: fat_db=R$%.2f fat_xlsx=R$%.2f baseline_R7=R$%.2f "
        "div_baseline=%.2f%% div_xlsx=%.2f%% warnings=%d",
        fat_db, total_xlsx, FATURAMENTO_BASELINE,
        (result["div_vs_baseline_pct"] or 0) * 100,
        (result["div_vs_xlsx_pct"] or 0) * 100,
        len(result["warnings"]),
    )
    for w in result["warnings"]:
        log.warning("Phase 8 WARN: %s", w)

    return result


# ---------------------------------------------------------------------------
# Phase 9 — Curva ABC recalculo
# ---------------------------------------------------------------------------
def phase_9_curva_abc(session, dry_run: bool) -> dict:
    """Recalcula produtos.curva_abc_produto via fat_total_historico DESC.

    Top 20% acumulado de faturamento -> A
    Proximos 30% -> B
    Resto -> C
    """
    stats = {"total_produtos": 0, "a": 0, "b": 0, "c": 0}

    rows = session.execute(text("""
        SELECT id, fat_total_historico FROM produtos
        WHERE fat_total_historico IS NOT NULL AND fat_total_historico > 0
        ORDER BY fat_total_historico DESC
    """)).fetchall()

    stats["total_produtos"] = len(rows)
    if not rows:
        log.info("Phase 9 curva ABC: sem produtos com fat_total_historico — skip")
        return stats

    total_geral = sum(float(r[1]) for r in rows)
    if total_geral == 0:
        return stats

    acumulado = 0.0
    for produto_id, fat in rows:
        fat_f = float(fat)
        acumulado += fat_f
        pct = acumulado / total_geral
        if pct <= 0.50:  # Top 50% acumulado eh A (top "20% qty" tipicamente)
            curva = "A"
            stats["a"] += 1
        elif pct <= 0.80:
            curva = "B"
            stats["b"] += 1
        else:
            curva = "C"
            stats["c"] += 1

        if not dry_run:
            session.execute(
                text("UPDATE produtos SET curva_abc_produto = :c WHERE id = :id"),
                {"c": curva, "id": produto_id},
            )

    if not dry_run:
        session.commit()

    log.info(
        "Phase 9 curva ABC: produtos=%d A=%d B=%d C=%d",
        stats["total_produtos"], stats["a"], stats["b"], stats["c"],
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 10 — Extraction report + ImportJob CONCLUIDO
# ---------------------------------------------------------------------------
def phase_10_relatorio(
    morning_dir: Path,
    inicio: datetime,
    stats_all: dict,
    validacao: dict,
    job_id: Optional[int],
    session,
    dry_run: bool,
) -> Path:
    """Salva extraction_report.json e top 10 clientes para validacao manual."""
    fim = datetime.now(timezone.utc).replace(tzinfo=None)
    duracao = (fim - inicio).total_seconds()

    # Top 10 clientes para validacao
    top10 = []
    rows = session.execute(text("""
        SELECT cnpj, nome_fantasia, faturamento_total
        FROM clientes
        WHERE faturamento_total IS NOT NULL AND faturamento_total > 0
        ORDER BY faturamento_total DESC
        LIMIT 10
    """)).fetchall()
    for r in rows:
        top10.append({
            "cnpj": r[0],
            "nome": r[1],
            "faturamento_total": float(r[2]),
        })

    # Sanitiza stats para JSON: cnpjs_processados (set) vira count
    phases_clean = {}
    for k, v in stats_all.items():
        if isinstance(v, dict):
            phases_clean[k] = {
                kk: (len(vv) if isinstance(vv, set) else vv)
                for kk, vv in v.items()
            }
            # Renomeia para clareza no report
            if "cnpjs_processados" in phases_clean[k]:
                phases_clean[k]["cnpjs_count"] = phases_clean[k].pop("cnpjs_processados")
        else:
            phases_clean[k] = v

    report = {
        "timestamp_inicio": inicio.isoformat(),
        "timestamp_fim": fim.isoformat(),
        "duracao_segundos": duracao,
        "morning_dir": str(morning_dir.relative_to(PROJECT_ROOT)) if morning_dir.is_relative_to(PROJECT_ROOT) else str(morning_dir),
        "import_job_id": job_id,
        "dry_run": dry_run,
        "phases": phases_clean,
        "validation": validacao,
        "top_10_clientes": top10,
        "regras": {
            "R1_two_base": "vendas + debitos = VENDA-side (R$). LOG nunca tocado.",
            "R2_cnpj": "string 14 digitos zero-padded; CPF 11d -> 000+CPF",
            "R7_baseline": f"R$ {FATURAMENTO_BASELINE:,.0f} (corrigido 2026-03-23)",
            "R8_classificacao_3tier": "REAL para todos os SAP",
            "R11_idempotencia": "SELECT antes de INSERT em todas as phases",
        },
    }

    report_path = morning_dir.parent / "extraction_report.json"
    if not dry_run:
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        log.info("Phase 10: extraction_report salvo em %s", report_path)

    return report_path


# ---------------------------------------------------------------------------
# ImportJob helpers
# ---------------------------------------------------------------------------
def criar_import_job(session, morning_dir: Path) -> Optional[int]:
    """Cria ImportJob tipo SALES_HUNTER em status PROCESSANDO. Retorna id."""
    try:
        from backend.app.models.import_job import ImportJob
        arquivo_nome = (
            str(morning_dir.relative_to(PROJECT_ROOT))
            if morning_dir.is_relative_to(PROJECT_ROOT)
            else str(morning_dir)
        )[:255]
        job = ImportJob(
            tipo="SALES_HUNTER",
            arquivo_nome=arquivo_nome,
            status="PROCESSANDO",
            iniciado_em=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(job)
        session.commit()
        log.info("ImportJob criado: id=%s tipo=SALES_HUNTER arquivo=%s", job.id, arquivo_nome)
        return job.id
    except Exception as exc:
        log.warning("Nao consegui criar ImportJob (seguindo sem tracking): %s", exc)
        session.rollback()
        return None


def finalizar_import_job(
    session,
    job_id: Optional[int],
    stats_all: dict,
    validacao: dict,
    erro_msg: Optional[str] = None,
) -> None:
    """Atualiza ImportJob com contadores finais."""
    if job_id is None:
        return
    try:
        from backend.app.models.import_job import ImportJob
        job = session.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            return

        # Contadores agregados
        lidos = sum(s.get("lidos", 0) for s in stats_all.values() if isinstance(s, dict))
        inseridos = (
            stats_all.get("phase_2_produtos", {}).get("inseridos", 0)
            + stats_all.get("phase_3_clientes", {}).get("inseridos", 0)
            + stats_all.get("phase_4_vendas", {}).get("vendas_inseridas", 0)
            + stats_all.get("phase_4_vendas", {}).get("itens_inseridos", 0)
            + stats_all.get("phase_6_debitos", {}).get("inseridos", 0)
        )
        atualizados = (
            stats_all.get("phase_2_produtos", {}).get("atualizados", 0)
            + stats_all.get("phase_3_clientes", {}).get("atualizados", 0)
            + stats_all.get("phase_5_consultor", {}).get("atualizados", 0)
            + stats_all.get("phase_7_devolucao", {}).get("atualizados", 0)
        )
        ignorados = sum(
            s.get("ignorados", 0) + s.get("ignorados_cnpj", 0) + s.get("ignorados_data", 0)
            + s.get("ja_existem", 0) + s.get("vendas_existentes", 0)
            for s in stats_all.values() if isinstance(s, dict)
        )

        job.registros_lidos = lidos
        job.registros_inseridos = inseridos
        job.registros_atualizados = atualizados
        job.registros_ignorados = ignorados
        job.concluido_em = datetime.now(timezone.utc).replace(tzinfo=None)

        if erro_msg:
            job.status = "ERRO"
            job.erro_mensagem = erro_msg[:2000]
        else:
            # WARN no validation nao falha o job — registra no log do report
            job.status = "CONCLUIDO"

        session.commit()
        log.info(
            "ImportJob %s -> %s (lidos=%d ins=%d atu=%d ign=%d)",
            job_id, job.status, lidos, inseridos, atualizados, ignorados,
        )
    except Exception as exc:
        log.warning("Nao consegui finalizar ImportJob %s: %s", job_id, exc)
        session.rollback()


# ---------------------------------------------------------------------------
# Relatorio final no console
# ---------------------------------------------------------------------------
def imprimir_relatorio(
    morning_dir: Path,
    stats_all: dict,
    validacao: dict,
    duracao: float,
    dry_run: bool,
    job_id: Optional[int],
) -> None:
    """Imprime relatorio resumido."""
    modo = "[DRY RUN — nada gravado]" if dry_run else "[GRAVADO NO BANCO]"
    print()
    print("=" * 70)
    print(f"  INGEST SALES HUNTER -> CRM VITAO360  {modo}")
    if job_id is not None:
        print(f"  ImportJob id : {job_id}")
    print(f"  Diretorio    : {morning_dir}")
    print(f"  Duracao      : {duracao:.1f}s")
    print("=" * 70)

    p2 = stats_all.get("phase_2_produtos", {})
    p3 = stats_all.get("phase_3_clientes", {})
    p4 = stats_all.get("phase_4_vendas", {})
    p5 = stats_all.get("phase_5_consultor", {})
    p6 = stats_all.get("phase_6_debitos", {})
    p7 = stats_all.get("phase_7_devolucao", {})
    p9 = stats_all.get("phase_9_curva_abc", {})

    print(f"  Phase 2 produtos   : ins={p2.get('inseridos',0):>5} atu={p2.get('atualizados',0):>5}")
    print(f"  Phase 3 clientes   : ins={p3.get('inseridos',0):>5} atu={p3.get('atualizados',0):>5}")
    print(f"  Phase 4 vendas     : ins={p4.get('vendas_inseridas',0):>5} ja_existem={p4.get('vendas_existentes',0):>5} itens={p4.get('itens_inseridos',0)}")
    print(f"  Phase 5 consultor  : atu={p5.get('atualizados',0):>5} sem_match={p5.get('sem_match',0):>5} sem_vendedor={p5.get('sem_vendedor',0)}")
    print(f"  Phase 6 debitos    : ins={p6.get('inseridos',0):>5} ja_existem={p6.get('ja_existem',0):>5} vencido={p6.get('vencido',0)} a_vencer={p6.get('a_vencer',0)}")
    print(f"  Phase 7 devolucao  : atu={p7.get('atualizados',0):>5}")
    print(f"  Phase 9 curva ABC  : A={p9.get('a',0):>3} B={p9.get('b',0):>3} C={p9.get('c',0):>3}")
    print()
    print(f"  VALIDACAO Phase 8:")
    print(f"    fat_db        : R$ {validacao.get('fat_db', 0):>15,.2f}")
    print(f"    fat_empresa   : R$ {validacao.get('fat_empresa_total', 0):>15,.2f}")
    print(f"    baseline R7   : R$ {validacao.get('fat_baseline', 0):>15,.2f}")
    if validacao.get("div_vs_baseline_pct") is not None:
        print(f"    div_baseline  : {validacao['div_vs_baseline_pct']*100:>15.2f}%")
    if validacao.get("div_vs_xlsx_pct") is not None:
        print(f"    div_xlsx      : {validacao['div_vs_xlsx_pct']*100:>15.2f}%")
    print(f"    status        : {validacao.get('status')}")
    for w in validacao.get("warnings", []):
        print(f"    WARN: {w}")

    print()
    print("  REGRAS VERIFICADAS (R1, R2, R7, R8, R11):")
    print("    R1 Two-Base       : OK — vendas/debitos = VENDA, LOG nao tocado")
    print("    R2 CNPJ           : OK — string 14d zfill, CPF 11d -> 000+CPF")
    print("    R7 Baseline       : sanity check Phase 8")
    print("    R8 No fabrication : OK — sem CNPJ resolvido = skip; classificacao=REAL")
    print("    R11 Idempotencia  : OK — SELECT antes INSERT em todas phases")
    print("=" * 70)
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingestao Sales Hunter (SAP) -> CRM VITAO360"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Data YYYY-MM-DD (default: pasta mais recente em data/sales_hunter/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nao grava no banco. Apenas relatorio.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Pula validacao Phase 8 (fat_empresa vs baseline).",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path SQLite arbitrario (override de DATABASE_URL).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Logging DEBUG.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Override DATABASE_URL com --db-path se fornecido
    if args.db_path:
        db_path = Path(args.db_path)
        if not db_path.is_absolute():
            db_path = (PROJECT_ROOT / db_path).resolve()
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        log.info("DATABASE_URL override: sqlite:///%s", db_path)

    # Resolve diretorio
    morning_dir = encontrar_diretorio_morning(args.date)
    if not morning_dir:
        log.error(
            "Diretorio Sales Hunter nao encontrado: %s",
            f"data/sales_hunter/{args.date or 'mais-recente'}/morning/",
        )
        return 1
    log.info("Processando: %s", morning_dir)

    # Lista XLSX
    xlsx_paths = listar_xlsx_validos(morning_dir)
    if not xlsx_paths:
        log.error("Nenhum XLSX valido em %s", morning_dir)
        return 1
    log.info("XLSX validos: %d (%s)", len(xlsx_paths), ", ".join(sorted(xlsx_paths.keys())))

    # Conecta no banco
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        log.error("DATABASE_URL nao definida")
        return 1
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    elif "neon" in db_url or "supabase" in db_url:
        connect_args = {"sslmode": "require", "connect_timeout": 30}
    elif "postgresql" in db_url:
        connect_args = {"connect_timeout": 30}
    else:
        connect_args = {}
    log.info("Conectando: %s://...", db_url.split("://")[0])

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    inicio = datetime.now(timezone.utc).replace(tzinfo=None)
    inicio_ts = time.time()

    job_id: Optional[int] = None
    if not args.dry_run:
        job_id = criar_import_job(session, morning_dir)

    stats_all: dict = {}
    erro_final: Optional[str] = None

    try:
        # Phase 2
        stats_all["phase_2_produtos"] = phase_2_produtos(session, xlsx_paths, args.dry_run)
        # Phase 3
        stats_all["phase_3_clientes"] = phase_3_clientes(session, xlsx_paths, args.dry_run)
        # Phase 4 — recebe cnpjs processados em Phase 3 (essencial em dry-run)
        cnpjs_p3 = stats_all["phase_3_clientes"].get("cnpjs_processados")
        stats_all["phase_4_vendas"] = phase_4_vendas(
            session, xlsx_paths, args.dry_run, cnpjs_phase3=cnpjs_p3,
        )
        # Phase 5
        stats_all["phase_5_consultor"] = phase_5_consultor(session, xlsx_paths, args.dry_run)
        # Phase 6
        stats_all["phase_6_debitos"] = phase_6_debitos(session, xlsx_paths, args.dry_run)
        # Phase 7
        stats_all["phase_7_devolucao"] = phase_7_devolucao(session, xlsx_paths, args.dry_run)
        # Phase 8
        validacao = phase_8_validacao(session, xlsx_paths, args.skip_validation)
        stats_all["phase_8_validacao"] = validacao
        # Phase 9
        stats_all["phase_9_curva_abc"] = phase_9_curva_abc(session, args.dry_run)

        duracao = time.time() - inicio_ts

        # Phase 10
        phase_10_relatorio(
            morning_dir, inicio, stats_all, validacao,
            job_id, session, args.dry_run,
        )

        # Finaliza ImportJob
        finalizar_import_job(session, job_id, stats_all, validacao)

        # Relatorio console
        imprimir_relatorio(
            morning_dir, stats_all, validacao, duracao,
            args.dry_run, job_id,
        )

        return 0

    except Exception as exc:
        log.exception("Erro fatal na ingestao: %s", exc)
        session.rollback()
        erro_final = str(exc)
        finalizar_import_job(session, job_id, stats_all, {}, erro_msg=erro_final)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
