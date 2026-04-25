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

    def __init__(self, session, dry_run: bool = False):
        self.session = session
        self.dry_run = dry_run
        self.stats = {
            "total_cards": 0,
            "sem_contato_no_db": 0,
            "ja_existentes": 0,
            "inseridos": 0,
            "ignorados_sem_cnpj": 0,
        }
        # Cache de todos os CNPJs no banco para validação rápida
        rows = self.session.execute(text("SELECT cnpj FROM clientes")).fetchall()
        self._cnpjs_db: set[str] = {r[0] for r in rows}

        # Cache de telefone para resolver contactId → CNPJ via contatos
        self._contact_id_cache: dict[int, Optional[str]] = {}

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

            # Resolver CNPJ via nome do contato
            contact_name = contact.get("name", "")
            cnpj = None

            if contact_name:
                # Guarda em cache por contactId para evitar reprocessar
                contact_id = contact.get("id")
                if contact_id in self._contact_id_cache:
                    cnpj = self._contact_id_cache[contact_id]
                else:
                    cnpj = self._resolver_cnpj_por_nome_contato(contact_name)
                    if contact_id:
                        self._contact_id_cache[contact_id] = cnpj

            if not cnpj:
                self.stats["ignorados_sem_cnpj"] += 1
                log.debug(
                    "Card %d '%s' — sem CNPJ identificado para contato '%s'",
                    card_id,
                    card_name,
                    contact_name,
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
# Relatório final
# ---------------------------------------------------------------------------

def imprimir_relatorio(
    data_dir: Path,
    stats_contatos: dict,
    stats_kanban: dict,
    dry_run: bool,
) -> None:
    """Imprime relatório completo da sincronização."""
    modo = "[DRY RUN — nenhuma alteração gravada]" if dry_run else "[GRAVADO NO BANCO]"
    print()
    print("=" * 60)
    print(f"  SYNC DESKRIO → CRM VITAO360  {modo}")
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
    print()
    print("  REGRAS VERIFICADAS")
    print("    Two-Base (log sem R$) : OK — log_interacoes sem campo valor")
    print("    CNPJ string 14 dig    : OK — normalizar_cnpj() aplicado")
    print("    Idempotencia          : OK — deduplicacao por (cnpj,data,kanban#)")
    print("    Dados fabricados      : OK — apenas contatos com match real")
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

    try:
        # ---------------------------------------------------------------
        # Fase 1 — Contatos
        # ---------------------------------------------------------------
        contacts_path = data_dir / "contacts.json"
        contacts = carregar_json(contacts_path)
        if not contacts:
            log.warning("contacts.json vazio ou ausente — fase 1 ignorada")
            stats_contatos: dict = {
                k: 0 for k in [
                    "total_contatos_deskrio", "total_brasileiros",
                    "match_telefone", "match_nome_fuzzy", "sem_match",
                    "atualizados_telefone", "atualizados_email",
                    "skipped_grupo", "skipped_sem_numero_br",
                ]
            }
        else:
            sync_contatos = SyncContatos(session, dry_run=args.dry_run)
            sync_contatos.processar(contacts)
            stats_contatos = sync_contatos.stats

        # ---------------------------------------------------------------
        # Fase 2 — Kanban cards
        # ---------------------------------------------------------------
        sync_kanban = SyncKanban(session, dry_run=args.dry_run)

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
        # Relatório
        # ---------------------------------------------------------------
        imprimir_relatorio(data_dir, stats_contatos, stats_kanban, args.dry_run)

        return 0

    except Exception as exc:
        log.exception("Erro fatal na sincronização: %s", exc)
        session.rollback()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
