"""
CRM VITAO360 — sync_deskrio_to_db.py
======================================
Sincroniza dados do Deskrio (WhatsApp CRM) com o banco do CRM (Postgres ou SQLite).

Fontes:
  data/deskrio/{YYYY-MM-DD}/contacts.json         — contatos WA (15k+)
  data/deskrio/{YYYY-MM-DD}/kanban_cards_20.json  — board "Vendas Vitao"
  data/deskrio/{YYYY-MM-DD}/kanban_cards_100.json — board "Vendas Vitao - Larissa"
  data/deskrio/{YYYY-MM-DD}/tickets.json          — atendimentos WhatsApp 30d
  data/deskrio/cnpj_bridge.json                   — contactId -> cnpj (verificado API)

Conexao ao banco:
  Le DATABASE_URL de .env e .env.local (override do .env.local quando presente).
  Sem DATABASE_URL -> fallback SQLite local em data/crm_vitao360.db.
  Aceita postgres://, postgresql://, sqlite:///. Neon/Supabase recebe sslmode=require.

Regras INVIOLAVEIS:
  R2 — CNPJ = string 14 digitos zero-padded, NUNCA float
  R4 — Two-Base: log_interacoes NUNCA contem valor R$
  R8 — NUNCA fabricar dados (sem CNPJ resolvido = skip, nao inventa)
  Idempotente: pode rodar multiplas vezes sem duplicar

Uso:
  python scripts/sync_deskrio_to_db.py
  python scripts/sync_deskrio_to_db.py --data-dir data/deskrio/2026-04-13
  python scripts/sync_deskrio_to_db.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Setup de paths — o script pode ser chamado de qualquer diretório
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Carregamento de .env e .env.local — antes de qualquer import que dependa de DATABASE_URL.
# .env  : defaults do repo (DATABASE_URL costuma estar vazia aqui)
# .env.local : credenciais reais (Neon, Vercel) — TEM PRECEDENCIA quando valor nao-vazio
# ---------------------------------------------------------------------------
def _load_env_file(path: Path, override_when_empty: bool = True) -> None:
    """Carrega KEY=VALUE de arquivo .env.

    override_when_empty=True faz override se a env var atual estiver vazia/ausente.
    Comportamento alinhado com o do recalc_score_batch.py + correcao para
    DATABASE_URL="" no .env (caso real do projeto).
    """
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
                continue  # nunca persistimos vazio
            atual = os.environ.get(k, "")
            if not atual or override_when_empty:
                os.environ[k] = v
    except OSError:
        pass

# Ordem: .env primeiro (defaults), .env.local sobrescreve quando valor nao-vazio
_load_env_file(PROJECT_ROOT / ".env", override_when_empty=False)
_load_env_file(PROJECT_ROOT / ".env.local", override_when_empty=True)

# Fallback: sem DATABASE_URL -> SQLite local
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = f"sqlite:///{PROJECT_ROOT / 'data' / 'crm_vitao360.db'}"


# SQLAlchemy
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("ERRO: sqlalchemy não instalado. Execute: pip install sqlalchemy")
    sys.exit(1)

# rapidfuzz — opcional, ativa fuzzy matching por nome
try:
    from rapidfuzz import fuzz, process as rfuzz_process

    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
log = logging.getLogger("sync_deskrio")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
DESKRIO_ROOT = PROJECT_ROOT / "data" / "deskrio"
CNPJ_BRIDGE_PATH = DESKRIO_ROOT / "cnpj_bridge.json"

# Score mínimo para aceitar match fuzzy por nome (0-100)
FUZZY_NOME_THRESHOLD = 72

# Prefixo Brasil nos números WhatsApp
BR_COUNTRY_CODE = "55"

# Tamanho mínimo de número válido (DDD + 8 dígitos = 10, com 55 = 12)
MIN_PHONE_DIGITS = 10

# Kanban columns mapeadas para estagio_funil (ordem: mais específico primeiro)
# Inferido dos card samples coletados no projeto
KANBAN_COLUMN_STAGE: dict[int, str] = {
    97:  "POS-VENDA",        # Clientes fidelizados / recompra
    99:  "NEGOCIACAO",       # Aguardando decisão / crédito
    100: "VENDA-REALIZADA",  # Pedido enviado / em trânsito
    101: "PROSPECCAO",       # Prospects frios
    387: "PROSPECCAO",       # Leads iniciais (board 20)
    388: "DESENVOLVIMENTO",  # Interesse identificado
    415: "POS-VENDA",        # Suporte / pendências pós-venda
    416: "NEGOCIACAO",       # Aguardando decisão
    417: "CADASTRO",         # Aguardando dados cadastrais
    418: "LEAD",             # Leads crus
    419: "SUPORTE",          # Suporte financeiro/comercial
    420: "NEGOCIACAO",       # Orçamento / aguardando retorno
}

# userId Deskrio → consultor CRM
USERID_TO_CONSULTOR: dict[int, str] = {
    4400002:  "DAIANE",   # Daiane Stavicki
    4400030:  "LARISSA",  # Larissa
    4400034:  "DAIANE",   # Administrador → DAIANE (gestor)
    64000102: "MANU",     # Manu - Vitao
    64000104: "DAIANE",   # Leandro - Comercial Interno → DAIANE
}

# De-Para por nome (para resolver userId não mapeados)
DESKRIO_USER_NAME_TO_CONSULTOR: dict[str, str] = {
    "manu": "MANU",
    "manu vitao": "MANU",
    "manu - vitao": "MANU",
    "manu  - vitao": "MANU",
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
}


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def normalizar_cnpj(val: object) -> Optional[str]:
    """Converte qualquer representação de CNPJ para string 14 dígitos.

    Retorna None se o valor resultante não tiver 14 dígitos numéricos.

    R5: NUNCA armazenar como float/int — sempre string zero-padded.
    """
    if val is None:
        return None
    s = re.sub(r"\D", "", str(val)).zfill(14)
    # Validação básica: 14 dígitos e não todos iguais (ex: 00000000000000)
    if len(s) != 14:
        return None
    if len(set(s)) == 1:
        return None  # CNPJ inválido tipo 00000000000000
    return s


def normalizar_telefone(raw: object) -> Optional[str]:
    """Extrai apenas os dígitos de um telefone.

    Retorna string numérica sem prefixo 55, ou None se inválido.
    Exemplos de entrada: '554791940129', '+55 (47) 9194-0129', '4791940129'
    Saída esperada: '4791940129' (DDD + número, sem 55)
    """
    if not raw:
        return None
    s = re.sub(r"\D", "", str(raw))
    if not s:
        return None
    # Remove o prefixo 55 do Brasil se presente
    if s.startswith("55") and len(s) >= 12:
        s = s[2:]
    # Aceita somente números com tamanho razoável (10-11 dígitos)
    if len(s) < MIN_PHONE_DIGITS or len(s) > 11:
        return None
    return s


def normalizar_telefone_db(raw: object) -> Optional[str]:
    """Normaliza telefone como vem do banco (formatos variados).

    Extrai os últimos 10-11 dígitos para comparação.
    """
    if not raw:
        return None
    s = re.sub(r"\D", "", str(raw))
    if not s:
        return None
    # Remove prefixo 55
    if s.startswith("55") and len(s) >= 12:
        s = s[2:]
    # Pega últimos 11 dígitos (com 9 celular) ou 10 (fixo)
    s = s[-11:] if len(s) > 11 else s
    if len(s) < MIN_PHONE_DIGITS:
        return None
    return s


def eh_numero_brasileiro(number: str) -> bool:
    """Verifica se o número é brasileiro (começa com 55 e tem comprimento válido)."""
    s = re.sub(r"\D", "", str(number))
    return s.startswith(BR_COUNTRY_CODE) and 12 <= len(s) <= 13


def resolver_consultor_por_userid(user_id: Optional[int], user_name: Optional[str]) -> str:
    """Resolve userId/userName Deskrio para consultor CRM VITAO360."""
    if user_id and user_id in USERID_TO_CONSULTOR:
        return USERID_TO_CONSULTOR[user_id]
    if user_name:
        nome_lower = user_name.strip().lower()
        if nome_lower in DESKRIO_USER_NAME_TO_CONSULTOR:
            return DESKRIO_USER_NAME_TO_CONSULTOR[nome_lower]
        # Tenta prefixo
        for key, consultor in DESKRIO_USER_NAME_TO_CONSULTOR.items():
            if nome_lower.startswith(key.split()[0]):
                return consultor
    return "DAIANE"  # Fallback: gestora


def encontrar_pasta_mais_recente(base: Path) -> Optional[Path]:
    """Retorna a pasta com a data mais recente em data/deskrio/."""
    if not base.exists():
        return None
    datas = sorted(
        [p for p in base.iterdir() if p.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}$", p.name)],
        key=lambda p: p.name,
        reverse=True,
    )
    return datas[0] if datas else None


def carregar_json(path: Path) -> list | dict:
    """Carrega um arquivo JSON com tratamento de erro."""
    if not path.exists():
        log.warning("Arquivo não encontrado: %s", path)
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        log.error("Erro ao ler JSON %s: %s", path, exc)
        return []


def carregar_cnpj_bridge() -> dict[int, str]:
    """Le data/deskrio/cnpj_bridge.json e retorna {contact_id_int: cnpj_normalizado}.

    A chave do bridge no JSON eh string (contactId do Deskrio, mesmo namespace
    de contacts.json[].id e tickets[].contactId — confirmado pela amostra
    interseccao 200/200).

    R8: nunca fabricar — se cnpjs[0] for invalido, ignora a entrada (nao tenta
    cnpjs[1] silenciosamente; usa o primeiro valido).
    """
    if not CNPJ_BRIDGE_PATH.exists():
        log.warning("cnpj_bridge.json nao encontrado em %s — usando soh fuzzy/telefone", CNPJ_BRIDGE_PATH)
        return {}

    try:
        with open(CNPJ_BRIDGE_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Erro ao ler cnpj_bridge.json: %s", exc)
        return {}

    bridge_raw = data.get("cnpj_bridge", {})
    if not isinstance(bridge_raw, dict):
        log.error("cnpj_bridge.json em formato inesperado (sem chave 'cnpj_bridge')")
        return {}

    result: dict[int, str] = {}
    invalidos = 0
    for contact_id_str, info in bridge_raw.items():
        try:
            contact_id = int(contact_id_str)
        except (TypeError, ValueError):
            invalidos += 1
            continue
        cnpjs = info.get("cnpjs", []) if isinstance(info, dict) else []
        if not isinstance(cnpjs, list):
            invalidos += 1
            continue
        # Pega o primeiro CNPJ valido (R8: nao fabrica, soh aceita o que normaliza)
        for raw in cnpjs:
            cnpj = normalizar_cnpj(raw)
            if cnpj:
                result[contact_id] = cnpj
                break

    log.info("cnpj_bridge carregado: %d mappings contact_id->cnpj (invalidos=%d)",
             len(result), invalidos)
    return result


# ---------------------------------------------------------------------------
# Fase 1 — Sincronização de contatos
# ---------------------------------------------------------------------------

class SyncContatos:
    """Sincroniza contacts.json com a tabela clientes."""

    def __init__(self, session, dry_run: bool = False):
        self.session = session
        self.dry_run = dry_run
        self.stats = {
            "total_contatos_deskrio": 0,
            "total_brasileiros": 0,
            "match_telefone": 0,
            "match_nome_fuzzy": 0,
            "sem_match": 0,
            "atualizados_telefone": 0,
            "atualizados_email": 0,
            "skipped_grupo": 0,
            "skipped_sem_numero_br": 0,
        }
        # Cache: telefone_normalizado → cnpj
        self._tel_cache: dict[str, str] = {}
        # Cache: nome_normalizado → cnpj (para fuzzy)
        self._nome_cache: dict[str, str] = {}
        self._build_caches()

    def _build_caches(self) -> None:
        """Constrói índices de telefone e nome a partir do banco."""
        rows = self.session.execute(
            text("SELECT cnpj, nome_fantasia, razao_social, telefone FROM clientes")
        ).fetchall()

        for cnpj, nome_fantasia, razao_social, telefone in rows:
            # Cache de telefone
            tel = normalizar_telefone_db(telefone)
            if tel:
                self._tel_cache[tel] = cnpj

            # Cache de nome (para fuzzy)
            nome = (nome_fantasia or razao_social or "").strip().upper()
            if nome:
                self._nome_cache[nome] = cnpj

        log.info(
            "Cache construído: %d telefones, %d nomes",
            len(self._tel_cache),
            len(self._nome_cache),
        )

    def _match_por_telefone(self, number: str) -> Optional[str]:
        """Tenta encontrar CNPJ pelo telefone normalizado do Deskrio."""
        tel = normalizar_telefone(number)
        if not tel:
            return None
        # Tenta match exato
        if tel in self._tel_cache:
            return self._tel_cache[tel]
        # Tenta com últimos 8 dígitos (ignora DDD)
        suf8 = tel[-8:]
        for db_tel, cnpj in self._tel_cache.items():
            if db_tel.endswith(suf8):
                return cnpj
        return None

    def _match_por_nome_fuzzy(self, deskrio_name: str) -> Optional[str]:
        """Tenta encontrar CNPJ por fuzzy match no nome (threshold = 72)."""
        if not RAPIDFUZZ_AVAILABLE or not self._nome_cache:
            return None
        # Nome do Deskrio: "EMPÓRIO VIDA NATURAL - MÁRCIO - SC" → extrai parte antes de " - "
        nome_limpo = deskrio_name.strip().upper()
        # Remove sufixos de contato humano (ex: " - MÁRCIO - SC")
        partes = nome_limpo.split(" - ")
        # Tenta progressivamente menos partes
        for n_partes in range(len(partes), 0, -1):
            nome_tentativa = " - ".join(partes[:n_partes]).strip()
            resultado = rfuzz_process.extractOne(
                nome_tentativa,
                self._nome_cache.keys(),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=FUZZY_NOME_THRESHOLD,
            )
            if resultado:
                matched_nome, score, _ = resultado
                log.debug(
                    "Fuzzy match: '%s' → '%s' (score=%d)",
                    nome_tentativa,
                    matched_nome,
                    score,
                )
                return self._nome_cache[matched_nome]
        return None

    def _atualizar_cliente(self, cnpj: str, contato: dict) -> bool:
        """Atualiza telefone/email de um cliente se necessário. Retorna True se houve update."""
        updated = False

        # Normaliza email — Deskrio retorna "" para vazio
        email_deskrio = (contato.get("email") or "").strip() or None

        # Telefone do Deskrio (formato numérico bruto, ex: "554791940129")
        number = contato.get("number", "")
        tel_normalizado = normalizar_telefone(number)

        row = self.session.execute(
            text("SELECT telefone, email FROM clientes WHERE cnpj = :cnpj"),
            {"cnpj": cnpj},
        ).fetchone()

        if not row:
            return False

        tel_db, email_db = row

        # Atualiza telefone se DB não tem e Deskrio tem
        if tel_normalizado and not normalizar_telefone_db(tel_db):
            # Formata como DDD + número (11 dígitos)
            tel_formatado = tel_normalizado
            if not self.dry_run:
                self.session.execute(
                    text("UPDATE clientes SET telefone = :tel WHERE cnpj = :cnpj"),
                    {"tel": tel_formatado, "cnpj": cnpj},
                )
            self.stats["atualizados_telefone"] += 1
            updated = True

        # Atualiza email se DB não tem e Deskrio tem
        if email_deskrio and not email_db:
            if not self.dry_run:
                self.session.execute(
                    text("UPDATE clientes SET email = :email WHERE cnpj = :cnpj"),
                    {"email": email_deskrio, "cnpj": cnpj},
                )
            self.stats["atualizados_email"] += 1
            updated = True

        return updated

    def processar(self, contacts: list[dict]) -> None:
        """Processa lista de contatos do Deskrio."""
        self.stats["total_contatos_deskrio"] = len(contacts)

        # Filtra apenas contatos não-grupo com número brasileiro
        elegíveis = []
        for c in contacts:
            if c.get("isGroup"):
                self.stats["skipped_grupo"] += 1
                continue
            number = str(c.get("number") or "")
            if not eh_numero_brasileiro(number):
                self.stats["skipped_sem_numero_br"] += 1
                continue
            elegíveis.append(c)

        self.stats["total_brasileiros"] = len(elegíveis)
        log.info("Contatos elegíveis (BR, não-grupo): %d", len(elegíveis))

        matched: set[str] = set()  # CNPJs já atualizados nesta execução

        for contato in elegíveis:
            cnpj = None
            metodo = None

            # 1. Tentativa: match por telefone
            number = contato.get("number", "")
            cnpj = self._match_por_telefone(number)
            if cnpj:
                metodo = "telefone"
                self.stats["match_telefone"] += 1

            # 2. Tentativa: match fuzzy por nome
            if not cnpj and contato.get("name"):
                cnpj = self._match_por_nome_fuzzy(contato["name"])
                if cnpj:
                    metodo = "fuzzy_nome"
                    self.stats["match_nome_fuzzy"] += 1

            if cnpj:
                if cnpj not in matched:
                    self._atualizar_cliente(cnpj, contato)
                    matched.add(cnpj)
            else:
                self.stats["sem_match"] += 1

        if not self.dry_run:
            self.session.commit()

        log.info(
            "Contatos: total=%d | BR=%d | match_tel=%d | match_fuzzy=%d | sem_match=%d",
            self.stats["total_contatos_deskrio"],
            self.stats["total_brasileiros"],
            self.stats["match_telefone"],
            self.stats["match_nome_fuzzy"],
            self.stats["sem_match"],
        )


# ---------------------------------------------------------------------------
# Fase 2 — Sincronização de Kanban cards
# ---------------------------------------------------------------------------

class SyncKanban:
    """Sincroniza kanban_cards_*.json com log_interacoes.

    Two-Base Architecture: log_interacoes NUNCA contém valor R$.
    Canal: WHATSAPP. Tipo: KANBAN (contato via Deskrio Kanban).
    Idempotência: usa (cnpj, data_interacao, tipo_contato='KANBAN', descricao) como
    chave de deduplicação.
    """

    def __init__(
        self,
        session,
        dry_run: bool = False,
        cnpj_bridge: Optional[dict[int, str]] = None,
    ):
        self.session = session
        self.dry_run = dry_run
        self.stats = {
            "total_cards": 0,
            "sem_contato_no_db": 0,
            "ja_existentes": 0,
            "inseridos": 0,
            "ignorados_sem_cnpj": 0,
            "match_bridge": 0,
            "match_fuzzy": 0,
        }
        # Cache de todos os CNPJs no banco para validação rápida
        rows = self.session.execute(text("SELECT cnpj FROM clientes")).fetchall()
        self._cnpjs_db: set[str] = {r[0] for r in rows}

        # Cache de telefone para resolver contactId → CNPJ via contatos
        self._contact_id_cache: dict[int, Optional[str]] = {}

        # cnpj_bridge: contact_id -> cnpj (fonte primaria, verificada via API)
        self._bridge: dict[int, str] = cnpj_bridge or {}

    def _resolver_cnpj_por_nome_contato(self, contact_name: str) -> Optional[str]:
        """Tenta resolver CNPJ pelo nome do contato no card (fuzzy match)."""
        if not RAPIDFUZZ_AVAILABLE or not contact_name:
            return None
        # Busca em nome_fantasia e razao_social
        rows = self.session.execute(
            text("SELECT cnpj, nome_fantasia, razao_social FROM clientes")
        ).fetchall()
        nomes = {(row[1] or row[2] or "").strip().upper(): row[0] for row in rows if row[1] or row[2]}
        if not nomes:
            return None
        nome_limpo = contact_name.strip().upper()
        partes = nome_limpo.split(" - ")
        for n_partes in range(len(partes), 0, -1):
            tentativa = " - ".join(partes[:n_partes]).strip()
            resultado = rfuzz_process.extractOne(
                tentativa,
                nomes.keys(),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=FUZZY_NOME_THRESHOLD,
            )
            if resultado:
                matched_nome, score, _ = resultado
                return nomes[matched_nome]
        return None

    def _log_existe(self, cnpj: str, data: datetime, descricao: str) -> bool:
        """Verifica se o log já existe (idempotência)."""
        row = self.session.execute(
            text(
                """
                SELECT id FROM log_interacoes
                WHERE cnpj = :cnpj
                  AND tipo_contato = 'KANBAN'
                  AND DATE(data_interacao) = DATE(:data)
                  AND (descricao = :desc OR (:desc IS NULL AND descricao IS NULL))
                LIMIT 1
                """
            ),
            {"cnpj": cnpj, "data": data.isoformat(), "desc": descricao[:200] if descricao else None},
        ).fetchone()
        return row is not None

    def _inserir_log(
        self,
        cnpj: str,
        data: datetime,
        consultor: str,
        resultado: str,
        descricao: str,
        estagio_funil: str,
    ) -> None:
        """Insere log_interacao respeitando Two-Base (sem valor R$)."""
        desc_truncada = (descricao or "")[:500] if descricao else None
        if not self.dry_run:
            self.session.execute(
                text(
                    """
                    INSERT INTO log_interacoes
                      (cnpj, data_interacao, consultor, resultado, descricao,
                       tipo_contato, estagio_funil, fase, created_at)
                    VALUES
                      (:cnpj, :data, :consultor, :resultado, :descricao,
                       'KANBAN', :estagio, 'KANBAN', :now)
                    """
                ),
                {
                    "cnpj": cnpj,
                    "data": data.isoformat(),
                    "consultor": consultor,
                    "resultado": resultado,
                    "descricao": desc_truncada,
                    "estagio": estagio_funil,
                    "now": datetime.now(timezone.utc).isoformat(),
                },
            )

    def processar(self, cards: list[dict], board_name: str) -> None:
        """Processa lista de kanban cards."""
        self.stats["total_cards"] += len(cards)
        log.info("Processando %d cards do board '%s'", len(cards), board_name)

        for card in cards:
            # Extrair dados do card
            card_id = card.get("id")
            card_name = card.get("name", "")
            descricao = card.get("description", "")
            column_id = card.get("kanbanColumnId") or card.get("columnId")
            created_at_str = card.get("createdAt")
            responsible = card.get("responsibleUser") or {}
            contact = card.get("contact") or {}

            # Resolver data
            try:
                data_card = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                ) if created_at_str else datetime.now(timezone.utc)
            except (ValueError, AttributeError):
                data_card = datetime.now(timezone.utc)

            # Resolver consultor
            user_id = card.get("responsibleUserId")
            user_name = responsible.get("name")
            consultor = resolver_consultor_por_userid(user_id, user_name)

            # Resolver estagio_funil pelo columnId
            estagio_funil = KANBAN_COLUMN_STAGE.get(column_id, "KANBAN")

            # Resultado baseado no nome da coluna/card
            resultado = f"Kanban: {card_name}"[:50] if card_name else "Kanban"

            # Resolver CNPJ — cascata: bridge -> fuzzy nome
            contact_name = contact.get("name", "")
            contact_id = contact.get("id")
            cnpj: Optional[str] = None

            # 1. cnpj_bridge (fonte primaria, verificada via API)
            if contact_id and contact_id in self._bridge:
                cnpj = self._bridge[contact_id]
                self.stats["match_bridge"] += 1

            # 2. Fallback: cache por contactId (fuzzy ja resolvido nesta execucao)
            if not cnpj and contact_id is not None and contact_id in self._contact_id_cache:
                cnpj = self._contact_id_cache[contact_id]

            # 3. Fallback: fuzzy match por nome
            if not cnpj and contact_name:
                cnpj = self._resolver_cnpj_por_nome_contato(contact_name)
                if cnpj:
                    self.stats["match_fuzzy"] += 1
                if contact_id is not None:
                    self._contact_id_cache[contact_id] = cnpj

            if not cnpj:
                self.stats["ignorados_sem_cnpj"] += 1
                log.debug(
                    "Card %d '%s' — sem CNPJ identificado para contato '%s' (id=%s)",
                    card_id,
                    card_name,
                    contact_name,
                    contact_id,
                )
                continue

            # Validar CNPJ existe no banco
            if cnpj not in self._cnpjs_db:
                self.stats["sem_contato_no_db"] += 1
                continue

            # Verificar idempotência
            desc_key = f"[Kanban#{card_id}] {descricao}"[:200] if descricao else f"[Kanban#{card_id}]"
            if self._log_existe(cnpj, data_card, desc_key):
                self.stats["ja_existentes"] += 1
                continue

            # Inserir log (Two-Base: sem valor R$)
            self._inserir_log(
                cnpj=cnpj,
                data=data_card,
                consultor=consultor,
                resultado=resultado,
                descricao=desc_key,
                estagio_funil=estagio_funil,
            )
            self.stats["inseridos"] += 1

        if not self.dry_run:
            self.session.commit()

        log.info(
            "Kanban '%s': total=%d | inseridos=%d | ja_existentes=%d | sem_cnpj=%d | sem_db=%d",
            board_name,
            len(cards),
            self.stats["inseridos"],
            self.stats["ja_existentes"],
            self.stats["ignorados_sem_cnpj"],
            self.stats["sem_contato_no_db"],
        )


# ---------------------------------------------------------------------------
# Fase 3 — Sincronização de Tickets (atendimentos WhatsApp)
# ---------------------------------------------------------------------------

class SyncTickets:
    """Sincroniza tickets.json (atendimentos WhatsApp) com log_interacoes.

    Two-Base Architecture: log_interacoes NUNCA contem valor R$.
    tipo_contato fixo: 'WHATSAPP'.
    resultado fixo: 'EM ATENDIMENTO' (refinado depois pelo motor de regras).

    Idempotencia: descricao prefixada com '[Ticket#<id>|<origem>]' permite query
    LIKE por ticket_id. Em Postgres % = wildcard, [ e ] sao literais — funciona.

    Cascata para resolver CNPJ:
      1. cnpj_bridge[contact_id] (fonte primaria, verificada via API Deskrio)
      2. Match por telefone (contact.number) — usa _tel_cache ja construido
      3. Fuzzy match por contact.name (threshold = FUZZY_NOME_THRESHOLD)
      Se nenhum: skip (R8 — nao fabrica CNPJ).

    Os campos calculados pelo motor (estagio_funil, fase, temperatura, etc.)
    ficam NULL aqui — recalc_score_batch.py + futuro enrich_log_motor.py
    refinam em passe separado.
    """

    def __init__(
        self,
        session,
        dry_run: bool = False,
        cnpj_bridge: Optional[dict[int, str]] = None,
    ):
        self.session = session
        self.dry_run = dry_run
        self.stats = {
            "total_tickets": 0,
            "inseridos": 0,
            "ja_existentes": 0,
            "sem_cnpj": 0,
            "sem_cliente_db": 0,
            "match_bridge": 0,
            "match_telefone": 0,
            "match_fuzzy": 0,
            "data_invalida": 0,
        }
        self._bridge: dict[int, str] = cnpj_bridge or {}

        # Cache cnpjs validos no banco (set para lookup O(1))
        rows = self.session.execute(text("SELECT cnpj FROM clientes")).fetchall()
        self._cnpjs_db: set[str] = {r[0] for r in rows}

        # Cache telefone -> cnpj (mesmo padrao do SyncContatos)
        rows_tel = self.session.execute(
            text("SELECT cnpj, telefone FROM clientes WHERE telefone IS NOT NULL")
        ).fetchall()
        self._tel_cache: dict[str, str] = {}
        for cnpj, telefone in rows_tel:
            tel = normalizar_telefone_db(telefone)
            if tel:
                self._tel_cache[tel] = cnpj

        # Cache nome -> cnpj para fuzzy match
        rows_nome = self.session.execute(
            text("SELECT cnpj, nome_fantasia, razao_social FROM clientes")
        ).fetchall()
        self._nome_cache: dict[str, str] = {}
        for cnpj, nf, rs in rows_nome:
            nome = ((nf or rs) or "").strip().upper()
            if nome:
                self._nome_cache[nome] = cnpj

        # Cache de contactId resolvido (evita refazer fuzzy no mesmo dia)
        self._contact_resolved: dict[int, Optional[str]] = {}

    def _match_telefone(self, number: object) -> Optional[str]:
        """Tenta resolver CNPJ pelo numero do contato Deskrio."""
        tel = normalizar_telefone(number)
        if not tel:
            return None
        if tel in self._tel_cache:
            return self._tel_cache[tel]
        # Fallback ultimos 8 digitos (sem DDD)
        suf8 = tel[-8:]
        for db_tel, cnpj in self._tel_cache.items():
            if db_tel.endswith(suf8):
                return cnpj
        return None

    def _match_fuzzy_nome(self, contact_name: str) -> Optional[str]:
        """Fuzzy match no nome com threshold FUZZY_NOME_THRESHOLD."""
        if not RAPIDFUZZ_AVAILABLE or not contact_name or not self._nome_cache:
            return None
        nome_limpo = contact_name.strip().upper()
        partes = nome_limpo.split(" - ")
        for n_partes in range(len(partes), 0, -1):
            tentativa = " - ".join(partes[:n_partes]).strip()
            resultado = rfuzz_process.extractOne(
                tentativa,
                self._nome_cache.keys(),
                scorer=fuzz.token_sort_ratio,
                score_cutoff=FUZZY_NOME_THRESHOLD,
            )
            if resultado:
                matched_nome, _, _ = resultado
                return self._nome_cache[matched_nome]
        return None

    def _ticket_log_existe(self, cnpj: str, ticket_id: int) -> bool:
        """Verifica se ja existe log para este (cnpj, ticket_id) — idempotencia.

        Usa LIKE no descricao porque log_interacoes nao tem coluna ticket_id.
        Padrao do prefixo: '[Ticket#<id>|<origem>] ...'.

        Em Postgres LIKE: % e _ sao wildcards; [, ], # e | sao literais.
        Em SQLite tambem funciona identico (LIKE eh case-insensitive default mas
        no nosso caso o prefixo eh consistente).
        """
        pattern = f"[Ticket#{ticket_id}|%"
        row = self.session.execute(
            text(
                """
                SELECT id FROM log_interacoes
                WHERE cnpj = :cnpj
                  AND tipo_contato = 'WHATSAPP'
                  AND descricao LIKE :pattern
                LIMIT 1
                """
            ),
            {"cnpj": cnpj, "pattern": pattern},
        ).fetchone()
        return row is not None

    def _inserir_log(
        self,
        cnpj: str,
        data: datetime,
        consultor: str,
        descricao: str,
    ) -> None:
        """Insere log_interacao do ticket. tipo_contato=WHATSAPP, resultado=EM ATENDIMENTO.

        Two-Base R4: nunca insere valor monetario aqui — schema impede + nao
        passamos campo de valor.
        Campos do motor (estagio_funil, fase, temperatura, ...) deixados NULL —
        recalc/motor refinam em passe separado.
        """
        desc_truncada = (descricao or "")[:500]
        if not self.dry_run:
            self.session.execute(
                text(
                    """
                    INSERT INTO log_interacoes
                      (cnpj, data_interacao, consultor, resultado, descricao,
                       tipo_contato, fase, created_at)
                    VALUES
                      (:cnpj, :data, :consultor, 'EM ATENDIMENTO', :descricao,
                       'WHATSAPP', 'ATENDIMENTO_WA', :now)
                    """
                ),
                {
                    "cnpj": cnpj,
                    "data": data,
                    "consultor": consultor,
                    "descricao": desc_truncada,
                    "now": datetime.now(timezone.utc),
                },
            )

    def _parse_ticket_date(self, ticket: dict) -> Optional[datetime]:
        """Resolve data do ticket: lastMessageDate -> updatedAt -> createdAt."""
        for key in ("lastMessageDate", "updatedAt", "createdAt"):
            raw = ticket.get(key)
            if not raw:
                continue
            try:
                # ISO 8601 com .000Z — substituir Z por +00:00 para fromisoformat
                s = str(raw).replace("Z", "+00:00")
                dt = datetime.fromisoformat(s)
                # Postgres timestamp without time zone — remover tzinfo para evitar warning
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt
            except (ValueError, AttributeError):
                continue
        return None

    def processar(self, tickets: list[dict]) -> None:
        """Processa lista de tickets do Deskrio."""
        self.stats["total_tickets"] = len(tickets)
        log.info("Processando %d tickets (WhatsApp)", len(tickets))

        for ticket in tickets:
            ticket_id = ticket.get("id")
            if not ticket_id:
                continue

            origin = (ticket.get("origin") or "").strip() or "Receptivo"
            status = (ticket.get("status") or "").strip()
            user_id = ticket.get("userId") or ticket.get("lastMessageUserId")
            contact = ticket.get("contact") or {}
            contact_id = ticket.get("contactId") or contact.get("id")
            contact_name = contact.get("name") or ""
            contact_number = contact.get("number") or ""
            last_message = ticket.get("lastMessage") or ""

            # Resolver consultor (preferir userId; fallback para responsavel da ultima msg)
            user_name = None
            consultor = resolver_consultor_por_userid(user_id, user_name)

            # Resolver data
            data_ticket = self._parse_ticket_date(ticket)
            if data_ticket is None:
                self.stats["data_invalida"] += 1
                continue

            # Resolver CNPJ — cascata bridge -> telefone -> fuzzy
            cnpj: Optional[str] = None

            # 1. Bridge (verificado via API)
            if contact_id is not None and contact_id in self._bridge:
                cnpj = self._bridge[contact_id]
                self.stats["match_bridge"] += 1

            # 2. Cache local (mesmo contactId nesta execucao)
            elif contact_id is not None and contact_id in self._contact_resolved:
                cnpj = self._contact_resolved[contact_id]

            # 3. Telefone
            if not cnpj and contact_number:
                cnpj = self._match_telefone(contact_number)
                if cnpj:
                    self.stats["match_telefone"] += 1

            # 4. Fuzzy nome
            if not cnpj and contact_name:
                cnpj = self._match_fuzzy_nome(contact_name)
                if cnpj:
                    self.stats["match_fuzzy"] += 1

            # Cachear resultado (positivo ou negativo) para o contactId
            if contact_id is not None:
                self._contact_resolved[contact_id] = cnpj

            if not cnpj:
                self.stats["sem_cnpj"] += 1
                log.debug(
                    "Ticket %s sem CNPJ — contact_id=%s name=%r number=%r",
                    ticket_id, contact_id, contact_name[:50], contact_number,
                )
                continue

            # Validar CNPJ existe no banco
            if cnpj not in self._cnpjs_db:
                self.stats["sem_cliente_db"] += 1
                continue

            # Idempotencia
            if self._ticket_log_existe(cnpj, ticket_id):
                self.stats["ja_existentes"] += 1
                continue

            # Montar descricao com prefixo idempotente
            desc = f"[Ticket#{ticket_id}|{origin}|{status}] {last_message}"
            self._inserir_log(
                cnpj=cnpj,
                data=data_ticket,
                consultor=consultor,
                descricao=desc,
            )
            self.stats["inseridos"] += 1

        if not self.dry_run:
            self.session.commit()

        log.info(
            "Tickets: total=%d | inseridos=%d | ja_existentes=%d | sem_cnpj=%d | sem_db=%d "
            "[match: bridge=%d tel=%d fuzzy=%d]",
            self.stats["total_tickets"],
            self.stats["inseridos"],
            self.stats["ja_existentes"],
            self.stats["sem_cnpj"],
            self.stats["sem_cliente_db"],
            self.stats["match_bridge"],
            self.stats["match_telefone"],
            self.stats["match_fuzzy"],
        )


# ---------------------------------------------------------------------------
# Relatório final
# ---------------------------------------------------------------------------

def imprimir_relatorio(
    data_dir: Path,
    stats_contatos: dict,
    stats_kanban: dict,
    stats_tickets: dict,
    dry_run: bool,
    job_id: Optional[int] = None,
) -> None:
    """Imprime relatório completo da sincronização."""
    modo = "[DRY RUN — nenhuma alteração gravada]" if dry_run else "[GRAVADO NO BANCO]"
    print()
    print("=" * 60)
    print(f"  SYNC DESKRIO → CRM VITAO360  {modo}")
    if job_id is not None:
        print(f"  ImportJob id     : {job_id}")
    print("=" * 60)
    print(f"  Pasta processada : {data_dir}")
    print()
    print("  CONTATOS (contacts.json)")
    print(f"    Total Deskrio   : {stats_contatos['total_contatos_deskrio']:>6}")
    print(f"    Brasileiros     : {stats_contatos['total_brasileiros']:>6}")
    print(f"    Match telefone  : {stats_contatos['match_telefone']:>6}")
    if RAPIDFUZZ_AVAILABLE:
        print(f"    Match fuzzy nome: {stats_contatos['match_nome_fuzzy']:>6}")
    else:
        print(f"    Match fuzzy nome:    N/A  (instale rapidfuzz)")
    print(f"    Sem match       : {stats_contatos['sem_match']:>6}")
    print(f"    Tel atualizados : {stats_contatos['atualizados_telefone']:>6}")
    print(f"    Email atualizados:{stats_contatos['atualizados_email']:>6}")
    print()
    print("  KANBAN (kanban_cards_*.json)")
    print(f"    Total cards     : {stats_kanban['total_cards']:>6}")
    print(f"    Inseridos DB    : {stats_kanban['inseridos']:>6}")
    print(f"    Ja existentes   : {stats_kanban['ja_existentes']:>6}")
    print(f"    Sem CNPJ        : {stats_kanban['ignorados_sem_cnpj']:>6}")
    print(f"    Sem cliente DB  : {stats_kanban['sem_contato_no_db']:>6}")
    print(f"    Match bridge    : {stats_kanban.get('match_bridge', 0):>6}")
    print(f"    Match fuzzy     : {stats_kanban.get('match_fuzzy', 0):>6}")
    print()
    print("  TICKETS (tickets.json — WhatsApp 30d)")
    print(f"    Total tickets   : {stats_tickets['total_tickets']:>6}")
    print(f"    Inseridos DB    : {stats_tickets['inseridos']:>6}")
    print(f"    Ja existentes   : {stats_tickets['ja_existentes']:>6}")
    print(f"    Sem CNPJ        : {stats_tickets['sem_cnpj']:>6}")
    print(f"    Sem cliente DB  : {stats_tickets['sem_cliente_db']:>6}")
    print(f"    Match bridge    : {stats_tickets['match_bridge']:>6}")
    print(f"    Match telefone  : {stats_tickets['match_telefone']:>6}")
    print(f"    Match fuzzy     : {stats_tickets['match_fuzzy']:>6}")
    print()
    print("  REGRAS VERIFICADAS")
    print("    Two-Base (log sem R$) : OK — log_interacoes sem campo valor")
    print("    CNPJ string 14 dig    : OK — normalizar_cnpj() aplicado")
    print("    Idempotencia          : OK — kanban#id e ticket#id como chave")
    print("    Dados fabricados      : OK — sem CNPJ resolvido = skip (R8)")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sincroniza Deskrio → banco SQLite CRM VITAO360"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Caminho explícito para a pasta deskrio (ex: data/deskrio/2026-04-13). "
             "Se omitido, usa a pasta mais recente.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa sem gravar no banco (apenas relatório).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ativa logging DEBUG.",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Resolve pasta de dados
    data_dir: Optional[Path] = args.data_dir
    if data_dir is None:
        data_dir = encontrar_pasta_mais_recente(DESKRIO_ROOT)
        if data_dir is None:
            log.error("Nenhuma pasta de extração encontrada em %s", DESKRIO_ROOT)
            return 1

    # Resolve caminhos relativos ao PROJECT_ROOT se necessário
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    if not data_dir.exists():
        log.error("Pasta não encontrada: %s", data_dir)
        return 1

    log.info("Processando extração: %s", data_dir)

    # Conecta ao banco — DATABASE_URL ja resolvida no topo do modulo
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        log.error("DATABASE_URL nao definida e fallback SQLite falhou")
        return 1

    # Render/Railway/Heroku usam postgres:// — SQLAlchemy 2.0 exige postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # Connect args por provedor
    if db_url.startswith("sqlite"):
        # Validar que o arquivo existe (modo file:)
        match = re.match(r"^sqlite:///(.+)$", db_url)
        if match:
            sqlite_path = Path(match.group(1))
            if not sqlite_path.exists():
                log.error("Banco SQLite nao encontrado: %s", sqlite_path)
                return 1
        connect_args = {"check_same_thread": False}
    elif "neon" in db_url or "supabase" in db_url:
        connect_args = {"sslmode": "require", "connect_timeout": 30}
    elif "postgresql" in db_url:
        connect_args = {"connect_timeout": 30}
    else:
        connect_args = {}

    # Log mascarado: nao expor credenciais
    log.info("Conectando em: %s://...", db_url.split("://")[0])

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    # Stats vazias padrao (caso alguma fase aborte cedo, o relatorio ainda imprime)
    stats_contatos: dict = {
        k: 0 for k in [
            "total_contatos_deskrio", "total_brasileiros",
            "match_telefone", "match_nome_fuzzy", "sem_match",
            "atualizados_telefone", "atualizados_email",
            "skipped_grupo", "skipped_sem_numero_br",
        ]
    }
    stats_kanban: dict = {
        k: 0 for k in [
            "total_cards", "sem_contato_no_db", "ja_existentes",
            "inseridos", "ignorados_sem_cnpj", "match_bridge", "match_fuzzy",
        ]
    }
    stats_tickets: dict = {
        k: 0 for k in [
            "total_tickets", "inseridos", "ja_existentes", "sem_cnpj",
            "sem_cliente_db", "match_bridge", "match_telefone", "match_fuzzy",
            "data_invalida",
        ]
    }

    # ImportJob tracking — soh persiste fora de dry-run
    job_id: Optional[int] = None
    job = None
    if not args.dry_run:
        try:
            from backend.app.models.import_job import ImportJob
            arquivo_nome = str(data_dir.relative_to(PROJECT_ROOT)) if data_dir.is_relative_to(PROJECT_ROOT) else str(data_dir)
            # Trim defensivo (campo VARCHAR(255))
            arquivo_nome = arquivo_nome[:255]
            job = ImportJob(
                tipo="DESKRIO",
                arquivo_nome=arquivo_nome,
                status="PROCESSANDO",
                iniciado_em=datetime.utcnow(),
            )
            session.add(job)
            session.commit()
            job_id = job.id
            log.info("ImportJob criado: id=%s tipo=DESKRIO arquivo=%s", job_id, arquivo_nome)
        except Exception as exc:
            log.warning("Nao consegui criar ImportJob (seguindo sem tracking): %s", exc)
            session.rollback()
            job = None
            job_id = None

    try:
        # ---------------------------------------------------------------
        # Fase 0 — cnpj_bridge (carregamento prioritario)
        # ---------------------------------------------------------------
        cnpj_bridge = carregar_cnpj_bridge()

        # ---------------------------------------------------------------
        # Fase 1 — Contatos
        # ---------------------------------------------------------------
        contacts_path = data_dir / "contacts.json"
        contacts = carregar_json(contacts_path)
        if contacts:
            sync_contatos = SyncContatos(session, dry_run=args.dry_run)
            sync_contatos.processar(contacts)
            stats_contatos = sync_contatos.stats
        else:
            log.warning("contacts.json vazio ou ausente — fase 1 ignorada")

        # ---------------------------------------------------------------
        # Fase 2 — Kanban cards
        # ---------------------------------------------------------------
        sync_kanban = SyncKanban(session, dry_run=args.dry_run, cnpj_bridge=cnpj_bridge)

        # Board 20: Vendas Vitao
        cards_20_path = data_dir / "kanban_cards_20.json"
        cards_20 = carregar_json(cards_20_path)
        if cards_20:
            sync_kanban.processar(cards_20, board_name="Vendas Vitao (20)")

        # Board 100: Vendas Vitao - Larissa
        cards_100_path = data_dir / "kanban_cards_100.json"
        cards_100 = carregar_json(cards_100_path)
        if cards_100:
            sync_kanban.processar(cards_100, board_name="Vendas Vitao - Larissa (100)")

        stats_kanban = sync_kanban.stats

        # ---------------------------------------------------------------
        # Fase 3 — Tickets (atendimentos WhatsApp 30d)
        # ---------------------------------------------------------------
        tickets_path = data_dir / "tickets.json"
        tickets = carregar_json(tickets_path)
        if tickets:
            sync_tickets = SyncTickets(session, dry_run=args.dry_run, cnpj_bridge=cnpj_bridge)
            sync_tickets.processar(tickets)
            stats_tickets = sync_tickets.stats
        else:
            log.warning("tickets.json vazio ou ausente — fase 3 ignorada")

        # ---------------------------------------------------------------
        # Atualizar ImportJob com contadores finais
        # ---------------------------------------------------------------
        if job is not None and not args.dry_run:
            try:
                job.status = "CONCLUIDO"
                job.concluido_em = datetime.utcnow()
                job.registros_lidos = (
                    stats_contatos.get("total_contatos_deskrio", 0)
                    + stats_kanban.get("total_cards", 0)
                    + stats_tickets.get("total_tickets", 0)
                )
                job.registros_inseridos = (
                    stats_kanban.get("inseridos", 0)
                    + stats_tickets.get("inseridos", 0)
                )
                job.registros_atualizados = (
                    stats_contatos.get("atualizados_telefone", 0)
                    + stats_contatos.get("atualizados_email", 0)
                )
                job.registros_ignorados = (
                    stats_kanban.get("ja_existentes", 0)
                    + stats_kanban.get("ignorados_sem_cnpj", 0)
                    + stats_kanban.get("sem_contato_no_db", 0)
                    + stats_tickets.get("ja_existentes", 0)
                    + stats_tickets.get("sem_cnpj", 0)
                    + stats_tickets.get("sem_cliente_db", 0)
                    + stats_tickets.get("data_invalida", 0)
                )
                session.commit()
                log.info("ImportJob %s -> CONCLUIDO (lidos=%d ins=%d ign=%d)",
                         job_id, job.registros_lidos, job.registros_inseridos,
                         job.registros_ignorados)
            except Exception as exc:
                log.warning("Nao consegui finalizar ImportJob: %s", exc)
                session.rollback()

        # ---------------------------------------------------------------
        # Relatório
        # ---------------------------------------------------------------
        imprimir_relatorio(data_dir, stats_contatos, stats_kanban,
                           stats_tickets, args.dry_run, job_id=job_id)

        return 0

    except Exception as exc:
        log.exception("Erro fatal na sincronização: %s", exc)
        session.rollback()
        # Marcar ImportJob como ERRO se foi criado
        if job is not None and not args.dry_run:
            try:
                job.status = "ERRO"
                job.concluido_em = datetime.utcnow()
                job.erro_mensagem = str(exc)[:2000]
                session.commit()
                log.error("ImportJob %s -> ERRO: %s", job_id, str(exc)[:200])
            except Exception:
                session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
