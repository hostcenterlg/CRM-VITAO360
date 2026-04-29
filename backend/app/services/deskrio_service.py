"""
CRM VITAO360 — Servico Deskrio (WhatsApp Business)

Cliente HTTP síncrono para a API Deskrio, plataforma de WhatsApp Business
usada pela VITAO Alimentos.

Comportamento sem configuracao:
  - configurado == False quando DESKRIO_API_URL ou DESKRIO_API_TOKEN estao ausentes.
  - Todos os metodos retornam None / [] de forma graceful — nunca levantam
    excecao por ausencia de credenciais.
  - Erros HTTP sao capturados, logados e retornam None / [] para nao bloquear
    o CRM principal.

R5 — CNPJ: normalizado para string 14 digitos antes de qualquer filtragem.
R8 — Nenhum dado e fabricado: se nao encontrar contato, retorna None.

Nota de implementacao:
  O backend usa FastAPI síncrono (nao async). O IA Service usa httpx.AsyncClient
  porque e chamado em endpoints async. Este servico usa httpx.Client (síncrono)
  para compatibilidade direta com rotas FastAPI normais (def, nao async def).

Dependencias:
  - httpx (já em requirements.txt)
  - DESKRIO_API_TOKEN, DESKRIO_API_URL, DESKRIO_COMPANY_ID no .env
"""

from __future__ import annotations

import logging
import os
import re
import time
import threading
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_TIMEOUT_SEGUNDOS: float = 15.0

# Retry configuration for 503/5xx resilience
_MAX_RETRIES: int = 3
_RETRY_BACKOFF_BASE: float = 1.0  # 1s, 2s, 4s exponential backoff
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({502, 503, 504})

# In-memory cache configuration (TTL-based, no external dependencies)
_CACHE_TTL_SECONDS: float = 300.0  # 5 minutes

# Mapeamento de status de conexao do Deskrio para texto legivel.
# Inclui INATIVE (variante real observada na API — conexao sem numero ativo).
_STATUS_LEGIVEL: dict[str, str] = {
    "CONNECTED": "conectado",
    "DISCONNECTED": "desconectado",
    "CONNECTING": "conectando",
    "INATIVE": "inativo",
    "INACTIVE": "inativo",
}


# ---------------------------------------------------------------------------
# Simple thread-safe TTL cache (stdlib only, no new dependencies)
# ---------------------------------------------------------------------------

class _TTLCache:
    """
    Minimal thread-safe in-memory cache with TTL expiration.

    Used to reduce load on the Deskrio API which frequently returns 503.
    Keys are strings (e.g., "GET:/v1/api/contact/5541999999999").
    Values are stored with their insertion timestamp and evicted on read
    if expired.
    """

    def __init__(self, ttl: float = _CACHE_TTL_SECONDS, max_size: int = 500):
        self._store: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> tuple[bool, Any]:
        """Return (hit, value). If expired or missing, returns (False, None)."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False, None
            ts, value = entry
            if time.monotonic() - ts > self._ttl:
                del self._store[key]
                return False, None
            return True, value

    def set(self, key: str, value: Any) -> None:
        """Store value with current timestamp. Evicts oldest if at capacity."""
        with self._lock:
            # Simple eviction: drop oldest 25% when at max capacity
            if len(self._store) >= self._max_size and key not in self._store:
                sorted_keys = sorted(
                    self._store, key=lambda k: self._store[k][0]
                )
                for k in sorted_keys[: self._max_size // 4]:
                    del self._store[k]
            self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        """Flush all cached entries."""
        with self._lock:
            self._store.clear()


# Module-level cache instance shared by all DeskrioService calls
_cache = _TTLCache()


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _normalizar_cnpj(cnpj: str) -> str:
    """R5: remove pontuacao e zero-pad para 14 digitos."""
    return re.sub(r"\D", "", str(cnpj)).zfill(14)


def _normalizar_numero(numero: str) -> str:
    """
    Normaliza numero de telefone para formato internacional (sem + ou espacos).
    Ex.: '+55 41 99999-9999' -> '5541999999999'
    """
    return re.sub(r"\D", "", str(numero))


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class DeskrioService:
    """
    Cliente síncrono para a API Deskrio (WhatsApp Business).

    Instanciado como singleton em modulo-level. Lê credenciais do ambiente
    no momento da chamada (permite hot-reload sem reiniciar o processo).
    """

    # ------------------------------------------------------------------
    # Configuracao
    # ------------------------------------------------------------------

    @property
    def base_url(self) -> str:
        # strip() defensivo: env vars copiadas pra Vercel podem trazer
        # whitespace ou newline residual que quebra a request HTTP.
        return os.getenv("DESKRIO_API_URL", "").strip().rstrip("/")

    @property
    def token(self) -> str:
        # strip() obrigatorio: tokens copiados manualmente para o painel
        # Vercel frequentemente trazem '\n' no final, causando
        # httpx LocalProtocolError "Illegal header value" e falha
        # silenciosa em _get/_post (incident 29/Apr/2026).
        return os.getenv("DESKRIO_API_TOKEN", "").strip()

    @property
    def company_id(self) -> int:
        try:
            return int(os.getenv("DESKRIO_COMPANY_ID", "38"))
        except ValueError:
            return 38

    @property
    def configurado(self) -> bool:
        """True somente se base_url e token estiverem presentes."""
        return bool(self.base_url and self.token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        use_cache: bool = True,
    ) -> Any | None:
        """
        Executa GET na API Deskrio with retry and caching.

        Retry: exponential backoff (1s, 2s, 4s) on 502/503/504.
        Cache: in-memory TTL cache (5 min) to reduce API load.
        Fallback: returns None gracefully on persistent failure.
        """
        if not self.configurado:
            logger.debug("Deskrio nao configurado — GET %s ignorado", path)
            return None

        # Build cache key from path + sorted params
        cache_key = f"GET:{path}"
        if params:
            sorted_params = "&".join(
                f"{k}={v}" for k, v in sorted(params.items())
            )
            cache_key = f"{cache_key}?{sorted_params}"

        # Check cache first
        if use_cache:
            hit, cached_value = _cache.get(cache_key)
            if hit:
                logger.debug("Deskrio cache HIT | %s", cache_key)
                return cached_value

        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=_TIMEOUT_SEGUNDOS) as client:
                    resp = client.get(
                        url, headers=self._headers(), params=params or {}
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    # Cache successful responses
                    if use_cache:
                        _cache.set(cache_key, data)

                    return data

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status_code = exc.response.status_code
                if status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "Deskrio %d (retryable) | GET %s | attempt %d/%d | "
                        "retrying in %.1fs",
                        status_code, path, attempt + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue
                # Non-retryable HTTP error or final attempt
                logger.warning(
                    "Deskrio HTTP error | GET %s | status=%d | body=%.300s",
                    path, status_code, exc.response.text,
                )
                return None

            except httpx.TimeoutException:
                last_exc = None
                if attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "Deskrio timeout | GET %s | attempt %d/%d | "
                        "retrying in %.1fs",
                        path, attempt + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue
                logger.warning(
                    "Deskrio timeout | GET %s | all %d attempts exhausted",
                    path, _MAX_RETRIES,
                )
                return None

            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Deskrio erro inesperado | GET %s | %s", path, exc
                )
                return None

        # Should not reach here, but safety fallback
        logger.warning(
            "Deskrio all retries exhausted | GET %s | last_exc=%s",
            path, last_exc,
        )
        return None

    def _post(self, path: str, payload: dict[str, Any]) -> Any | None:
        """
        Executa POST na API Deskrio with retry on 5xx.

        POST requests are NOT cached (mutations must not be replayed from cache).
        Retry: exponential backoff (1s, 2s, 4s) on 502/503/504 only.
        """
        if not self.configurado:
            logger.debug("Deskrio nao configurado — POST %s ignorado", path)
            return None

        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=_TIMEOUT_SEGUNDOS) as client:
                    resp = client.post(
                        url, headers=self._headers(), json=payload
                    )
                    resp.raise_for_status()
                    return resp.json()

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status_code = exc.response.status_code
                if status_code in _RETRYABLE_STATUS_CODES and attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "Deskrio %d (retryable) | POST %s | attempt %d/%d | "
                        "retrying in %.1fs",
                        status_code, path, attempt + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue
                logger.warning(
                    "Deskrio HTTP error | POST %s | status=%d | body=%.300s",
                    path, status_code, exc.response.text,
                )
                return None

            except httpx.TimeoutException:
                last_exc = None
                if attempt < _MAX_RETRIES - 1:
                    wait = _RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "Deskrio timeout | POST %s | attempt %d/%d | "
                        "retrying in %.1fs",
                        path, attempt + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    continue
                logger.warning(
                    "Deskrio timeout | POST %s | all %d attempts exhausted",
                    path, _MAX_RETRIES,
                )
                return None

            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Deskrio erro inesperado | POST %s | %s", path, exc
                )
                return None

        logger.warning(
            "Deskrio all retries exhausted | POST %s | last_exc=%s",
            path, last_exc,
        )
        return None

    # ------------------------------------------------------------------
    # Metodos publicos
    # ------------------------------------------------------------------

    def buscar_contato(self, numero: str) -> dict[str, Any] | None:
        """
        Busca um contato Deskrio pelo numero de telefone.

        Args:
            numero: Numero de telefone (qualquer formato — sera normalizado).

        Returns:
            Dict com dados do contato ou None se nao encontrado.
        """
        numero_norm = _normalizar_numero(numero)
        if not numero_norm:
            logger.warning("buscar_contato: numero invalido '%s'", numero)
            return None

        logger.info("Deskrio buscar_contato | numero=%s", numero_norm)
        data = self._get(f"/v1/api/contact/{numero_norm}")

        if data is None:
            return None

        # A API pode retornar lista ou objeto; normalizar para dict
        if isinstance(data, list):
            return data[0] if data else None

        return data if isinstance(data, dict) else None

    def buscar_contato_por_cnpj(self, cnpj: str) -> dict[str, Any] | None:
        """
        Busca contato Deskrio cujo campo extra 'CNPJ' bate com o CNPJ fornecido.

        O Deskrio armazena campos customizados em extraInfo:
          [{"name": "CNPJ", "value": "12345678000100"}, ...]

        Args:
            cnpj: CNPJ do cliente (qualquer formato — sera normalizado R5).

        Returns:
            Dict com dados do contato (incluindo numero de telefone) ou None.
        """
        cnpj_norm = _normalizar_cnpj(cnpj)
        logger.info("Deskrio buscar_contato_por_cnpj | cnpj=%s", cnpj_norm)

        # Buscar todos os contatos e filtrar pelo CNPJ
        data = self._get("/v1/api/contacts")
        if not isinstance(data, list):
            return None

        for contato in data:
            extra_info = contato.get("extraInfo", []) or []
            for campo in extra_info:
                if (
                    isinstance(campo, dict)
                    and campo.get("name", "").upper() in ("CNPJ", "CNPJ:")
                    and _normalizar_cnpj(str(campo.get("value", ""))) == cnpj_norm
                ):
                    logger.info(
                        "Deskrio contato encontrado por CNPJ | cnpj=%s id=%s numero=%s",
                        cnpj_norm,
                        contato.get("id"),
                        contato.get("number"),
                    )
                    return contato

        logger.info("Deskrio contato nao encontrado por CNPJ | cnpj=%s", cnpj_norm)
        return None

    def enviar_mensagem(
        self,
        numero: str,
        texto: str,
        conexao_id: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Envia mensagem de texto via WhatsApp para o numero informado.

        R8 — Two-Base: mensagens WA sao operacoes de LOG (R$ 0.00).

        Args:
            numero:     Numero de telefone do destinatario (sera normalizado).
            texto:      Texto da mensagem (max recomendado: 4096 chars).
            conexao_id: ID da conexao Deskrio (None = selecao automatica).

        Returns:
            Dict com resultado do envio (incluindo ID da mensagem) ou None em erro.
        """
        numero_norm = _normalizar_numero(numero)
        if not numero_norm:
            logger.warning("enviar_mensagem: numero invalido '%s'", numero)
            return None

        payload: dict[str, Any] = {
            "number": numero_norm,
            "body": texto,
            "companyId": self.company_id,
        }
        if conexao_id is not None:
            payload["connectionId"] = conexao_id

        logger.info(
            "Deskrio enviar_mensagem | numero=%s texto_len=%d conexao=%s",
            numero_norm,
            len(texto),
            conexao_id,
        )
        return self._post("/v1/api/messages/send", payload)

    def listar_conexoes(self) -> list[dict[str, Any]]:
        """
        Lista conexoes WhatsApp disponiveis na conta Deskrio.

        Defensiva: a API Deskrio retorna um envelope com multiplas chaves:
          {"whatsappConnections": [...], "whatsappApiConnections": [...], "metaConnections": [...]}
        Concatenamos whatsappConnections (principal) e tratamos outros formatos
        conhecidos para garantir robustez.

        Returns:
            Lista de dicts com {id, name, status, ...}. Lista vazia em erro.
        """
        logger.info("Deskrio listar_conexoes")
        data = self._get("/v1/api/connections")

        if isinstance(data, list):
            logger.debug("Deskrio listar_conexoes raw=list count=%d", len(data))
            return data

        if isinstance(data, dict):
            # Envelope primario Deskrio: chave whatsappConnections
            # (confirmado via smoke test 2026-04-29)
            for envelope_key in (
                "whatsappConnections",
                "data",
                "connections",
                "items",
                "results",
            ):
                inner = data.get(envelope_key)
                if isinstance(inner, list):
                    logger.info(
                        "Deskrio listar_conexoes raw=dict.%s count=%d",
                        envelope_key,
                        len(inner),
                    )
                    return inner
            logger.warning(
                "Deskrio listar_conexoes envelope desconhecido keys=%s",
                list(data.keys()),
            )

        return []

    def listar_tickets(
        self,
        data_inicio: str,
        data_fim: str,
        numero: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Lista tickets de atendimento no periodo informado.

        LIMITE DESKRIO: a API rejeita ranges >= 7 dias com HTTP 400
        ERR_DATE_LIMIT_OFF_1_WEEK. O caller deve garantir que
        (data_fim - data_inicio) <= 6 dias.

        Args:
            data_inicio: Data no formato 'YYYY-MM-DD'.
            data_fim:    Data no formato 'YYYY-MM-DD'.
            numero:      Filtrar por numero de telefone (opcional).

        Returns:
            Lista de dicts de tickets. Lista vazia em erro.
        """
        # Guard: calcular diferenca de dias e truncar inicio se necessario
        # para nunca exceder o limite estrito de 6 dias da API Deskrio
        # (HTTP 400 ERR_DATE_LIMIT_OFF_1_WEEK se range >= 7 dias).
        try:
            from datetime import date as _dt_date, timedelta as _timedelta
            d_inicio = _dt_date.fromisoformat(data_inicio)
            d_fim = _dt_date.fromisoformat(data_fim)
            diff_dias = (d_fim - d_inicio).days
            if diff_dias > 6:
                # Truncar para os 6 dias mais recentes (mais relevantes para Inbox)
                d_inicio_truncado = d_fim - _timedelta(days=6)
                logger.info(
                    "Deskrio listar_tickets range truncado | "
                    "original_inicio=%s novo_inicio=%s fim=%s diff_dias=%d",
                    data_inicio,
                    d_inicio_truncado.isoformat(),
                    data_fim,
                    diff_dias,
                )
                data_inicio = d_inicio_truncado.isoformat()
        except (ValueError, TypeError) as exc:
            logger.warning(
                "Deskrio listar_tickets parse de datas falhou | "
                "inicio=%s fim=%s exc=%s — usando valores originais",
                data_inicio,
                data_fim,
                exc,
            )

        params: dict[str, str] = {
            "startDate": data_inicio,
            "endDate": data_fim,
        }
        if numero:
            params["number"] = _normalizar_numero(numero)

        logger.info(
            "Deskrio listar_tickets | inicio=%s fim=%s numero=%s",
            data_inicio,
            data_fim,
            numero,
        )
        data = self._get("/v1/api/tickets", params=params)

        if isinstance(data, list):
            logger.info(
                "Deskrio listar_tickets OK | count=%d inicio=%s fim=%s",
                len(data),
                data_inicio,
                data_fim,
            )
            return data

        if data is None:
            logger.warning(
                "Deskrio listar_tickets retornou None | "
                "provavel HTTP 400/5xx — inicio=%s fim=%s",
                data_inicio,
                data_fim,
            )
        elif isinstance(data, dict):
            logger.warning(
                "Deskrio listar_tickets retornou dict inesperado | "
                "keys=%s | inicio=%s fim=%s",
                list(data.keys()),
                data_inicio,
                data_fim,
            )

        return []

    def obter_ticket(self, ticket_id: int) -> dict[str, Any] | None:
        """
        Busca detalhes de um ticket especifico.

        Args:
            ticket_id: ID do ticket Deskrio.

        Returns:
            Dict com dados do ticket ou None se nao encontrado.
        """
        logger.info("Deskrio obter_ticket | ticket_id=%d", ticket_id)
        data = self._get(f"/v1/api/ticket/{ticket_id}")

        if isinstance(data, dict):
            return data

        return None

    def listar_mensagens(
        self,
        ticket_id: int,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Busca mensagens reais de um ticket Deskrio (conversa WhatsApp).

        Endpoint: GET /v1/api/messages/{ticketId}?pageNumber={page}

        Args:
            ticket_id: ID do ticket Deskrio.
            page:      Pagina (paginacao do Deskrio).

        Returns:
            Dict com {count, messages[], hasMore} ou dict vazio em erro.
        """
        logger.info("Deskrio listar_mensagens | ticket_id=%d page=%d", ticket_id, page)
        data = self._get(
            f"/v1/api/messages/{ticket_id}",
            params={"pageNumber": str(page)},
        )

        if isinstance(data, dict):
            return data

        # Fallback: API pode retornar lista diretamente
        if isinstance(data, list):
            return {"count": len(data), "messages": data, "hasMore": False}

        return {"count": 0, "messages": [], "hasMore": False}

    def buscar_tickets_por_contato(
        self,
        contact_id: int,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Busca tickets recentes de um contato especifico.

        Filtra listar_tickets pelo contactId (ultimos 90 dias).

        Args:
            contact_id: ID do contato Deskrio.
            limite:     Maximo de tickets a retornar.

        Returns:
            Lista de tickets do contato, ordenados por data desc.
        """
        from datetime import date, timedelta

        hoje = date.today()
        inicio = hoje - timedelta(days=90)

        todos = self.listar_tickets(
            data_inicio=inicio.isoformat(),
            data_fim=hoje.isoformat(),
        )

        # Filtrar por contactId
        do_contato = [
            t for t in todos
            if t.get("contactId") == contact_id
        ]

        # Ordenar por data desc (mais recente primeiro)
        do_contato.sort(
            key=lambda t: t.get("updatedAt") or t.get("createdAt") or "",
            reverse=True,
        )

        return do_contato[:limite]

    def obter_conversa_completa(
        self,
        cnpj: str,
        max_mensagens: int = 50,
    ) -> dict[str, Any]:
        """
        Busca a conversa WhatsApp completa de um cliente pelo CNPJ.

        Fluxo:
          1. Busca contato por CNPJ
          2. Busca tickets do contato
          3. Busca mensagens do ticket mais recente (ou aberto)

        Args:
            cnpj: CNPJ do cliente (sera normalizado).
            max_mensagens: Maximo de mensagens a retornar.

        Returns:
            Dict com {contato, ticket, mensagens[], total, configurado}.
        """
        cnpj_norm = _normalizar_cnpj(cnpj)
        resultado: dict[str, Any] = {
            "configurado": self.configurado,
            "contato": None,
            "ticket": None,
            "mensagens": [],
            "total": 0,
        }

        if not self.configurado:
            return resultado

        # 1. Buscar contato
        contato = self.buscar_contato_por_cnpj(cnpj_norm)
        if contato is None:
            logger.info("Conversa: contato nao encontrado | cnpj=%s", cnpj_norm)
            return resultado

        resultado["contato"] = {
            "id": contato.get("id"),
            "nome": contato.get("name"),
            "numero": contato.get("number"),
        }

        # 2. Buscar tickets do contato
        contact_id = contato.get("id")
        if not contact_id:
            return resultado

        tickets = self.buscar_tickets_por_contato(contact_id, limite=5)
        if not tickets:
            logger.info("Conversa: sem tickets | cnpj=%s contact_id=%s", cnpj_norm, contact_id)
            return resultado

        # Preferir ticket aberto, senao o mais recente
        ticket = next(
            (t for t in tickets if t.get("status") in ("open", "pending")),
            tickets[0],
        )

        resultado["ticket"] = {
            "id": ticket.get("id"),
            "status": ticket.get("status"),
            "criado_em": ticket.get("createdAt"),
            "atualizado_em": ticket.get("updatedAt"),
            "ultima_mensagem": ticket.get("lastMessage"),
        }

        # 3. Buscar mensagens do ticket
        ticket_id = ticket.get("id")
        if not ticket_id:
            return resultado

        msgs_data = self.listar_mensagens(ticket_id)
        mensagens_raw = msgs_data.get("messages", [])

        # Normalizar mensagens para formato padrao
        mensagens: list[dict[str, Any]] = []
        for m in mensagens_raw[:max_mensagens]:
            mensagens.append({
                "id": m.get("id"),
                "texto": m.get("body") or m.get("message") or "",
                "de_cliente": not bool(m.get("fromMe")),
                "timestamp": m.get("createdAt") or m.get("timestamp") or "",
                "tipo": m.get("mediaType") or "chat",
                "media_url": m.get("mediaUrl"),
                "nome_contato": m.get("contact", {}).get("name") if isinstance(m.get("contact"), dict) else None,
            })

        resultado["mensagens"] = mensagens
        resultado["total"] = msgs_data.get("count", len(mensagens))

        return resultado

    def listar_kanban_boards(self) -> list[dict[str, Any]]:
        """
        Lista boards Kanban disponiveis na conta.

        Returns:
            Lista de dicts com dados dos boards. Lista vazia em erro.
        """
        logger.info("Deskrio listar_kanban_boards")
        data = self._get("/v1/api/kanban-boards")

        if isinstance(data, list):
            return data

        return []

    def status_conexoes(self) -> dict[str, Any]:
        """
        Retorna resumo do status das conexoes WhatsApp.

        Usado pelo endpoint GET /api/whatsapp/status.

        Returns:
            Dict com:
              - configurado (bool): credenciais presentes
              - conexoes (list): [{nome, status, status_legivel}]
              - alguma_conectada (bool): pelo menos 1 conexao CONNECTED
              - total_conexoes (int): total de conexoes
        """
        if not self.configurado:
            return {
                "configurado": False,
                "conexoes": [],
                "alguma_conectada": False,
                "total_conexoes": 0,
            }

        conexoes_raw = self.listar_conexoes()
        logger.info(
            "Deskrio status_conexoes raw count=%d sample_keys=%s",
            len(conexoes_raw),
            list(conexoes_raw[0].keys()) if conexoes_raw else [],
        )

        conexoes: list[dict[str, Any]] = []

        for c in conexoes_raw:
            # Deskrio API pode reportar status em diferentes campos/formatos.
            # Buscamos defensivamente em todos os campos conhecidos antes de
            # cair no default DISCONNECTED. Aceitamos tambem boolean explicito
            # (connected: true) que algumas APIs WhatsApp retornam.
            status_raw_value: Any = (
                c.get("status")
                or c.get("state")
                or c.get("connectionStatus")
                or c.get("connection_status")
            )

            if status_raw_value is None:
                # Boolean fallback: se ha campo connected/isConnected, usa
                connected_flag = c.get("connected", c.get("isConnected"))
                if connected_flag is True:
                    status_raw_value = "CONNECTED"
                elif connected_flag is False:
                    status_raw_value = "DISCONNECTED"

            status_raw = str(status_raw_value or "DISCONNECTED").upper().strip()

            conexoes.append(
                {
                    "id": c.get("id") or c.get("_id"),
                    "nome": c.get("name") or c.get("nome") or "Sem nome",
                    "status": status_raw,
                    "status_legivel": _STATUS_LEGIVEL.get(status_raw, status_raw.lower()),
                }
            )

        # Comparacao defensiva case-insensitive contra valores normalizados
        alguma_conectada = any(
            str(c.get("status", "")).upper() == "CONNECTED" for c in conexoes
        )

        logger.info(
            "Deskrio status_conexoes total=%d conectadas=%d alguma_conectada=%s",
            len(conexoes),
            sum(1 for c in conexoes if c["status"] == "CONNECTED"),
            alguma_conectada,
        )

        return {
            "configurado": True,
            "conexoes": conexoes,
            "alguma_conectada": alguma_conectada,
            "total_conexoes": len(conexoes),
        }


# ---------------------------------------------------------------------------
# Instancia singleton
# ---------------------------------------------------------------------------

deskrio_service = DeskrioService()
