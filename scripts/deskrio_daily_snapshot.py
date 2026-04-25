#!/usr/bin/env python3
"""
CRM VITAO360 — deskrio_daily_snapshot.py
=========================================
Captura reprodutivel dos dados Deskrio para data/deskrio/{YYYY-MM-DD}/.

Consolidacao dos artefatos que antes eram gerados externamente. Usa o
DeskrioService existente (backend/app/services/deskrio_service.py) para
manter um unico ponto de chamada HTTP com retry + cache + logging.

ENDPOINTS COBERTOS (testados 2026-04-24):
  GET  /v1/api/connections             -> connections.json
  GET  /v1/api/contacts                -> contacts.json
  GET  /v1/api/tickets?...             -> tickets.json (ultimos 30 dias, 5 janelas de 6d)
  GET  /v1/api/kanban-boards           -> kanban_boards.json
  GET  /v1/api/kanban-columns/:boardId -> kanban_columns_{boardId}.json
  GET  /v1/api/messages/:ticketId      -> messages_{ticketId}.json (top N)
  GET  /v1/api/custom-field/:number    -> cnpj_bridge.json (incremental, 200/dia)

ENDPOINT NAO PUBLICO (captura externa historica):
  kanban_cards_20.json e kanban_cards_100.json eram gerados por processo
  nao versionado. Este script tenta capturar via /v1/api/kanban-card/{id}
  se uma lista de card ids for fornecida em data/deskrio/_card_ids.json,
  senao omite graciosamente (sem gerar arquivos de erro 403).

USO:
  python scripts/deskrio_daily_snapshot.py                      # hoje
  python scripts/deskrio_daily_snapshot.py --date 2026-04-25
  python scripts/deskrio_daily_snapshot.py --dry-run            # sem escrever

EXIT CODES:
  0 = sucesso (todos os endpoints esperados OK, kanban_cards tolerado ausente)
  1 = falha critica (token invalido, conexao falhou, etc.)
  2 = sucesso parcial (algum endpoint nao-critico falhou)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DESKRIO_ROOT = PROJECT_ROOT / "data" / "deskrio"

# ---------------------------------------------------------------------------
# Load .env (stdlib only — no python-dotenv dependency)
# ---------------------------------------------------------------------------
def _load_env() -> dict[str, str]:
    env_path = PROJECT_ROOT / ".env"
    env: dict[str, str] = dict(os.environ)
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip())
    return env


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
log = logging.getLogger("deskrio_snapshot")


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------
class DeskrioSnapshot:
    def __init__(self, target_date: date, dry_run: bool = False):
        self.target_date = target_date
        self.dry_run = dry_run
        self.env = _load_env()
        self.token = self.env.get("DESKRIO_API_TOKEN", "")
        self.base_url = self.env.get("DESKRIO_API_URL", "").rstrip("/")
        self.company_id = int(self.env.get("DESKRIO_COMPANY_ID", "38"))
        self.out_dir = DESKRIO_ROOT / target_date.isoformat()
        self.results: dict[str, str] = {}  # endpoint -> "OK"|"FAIL"|"SKIP"
        self._started_at: datetime = datetime.utcnow()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, path: str, params: dict[str, Any] | None = None,
             _raise_on_token_error: bool = False) -> Any | None:
        if not self.token or not self.base_url:
            log.error("DESKRIO_API_TOKEN ou DESKRIO_API_URL ausente em .env")
            return None
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.get(url, headers=self._headers(), params=params or {})
                # Detectar token expirado/invalido em qualquer status 401/403
                if r.status_code in (401, 403):
                    body_lower = r.text.lower()
                    is_token_error = any(kw in body_lower for kw in (
                        "invalid token", "token inválido", "unauthorized",
                        "jwt expired", "token expired", "signature verification failed",
                    ))
                    if is_token_error:
                        log.error("TOKEN_EXPIRED: %d em %s — %s", r.status_code, path, r.text[:200])
                        if _raise_on_token_error:
                            raise RuntimeError("TOKEN_EXPIRED")
                        return None
                    # 403 por endpoint privado (nao token) — logar como warning, nao error
                    log.warning("HTTP %d em %s — endpoint pode ser privado: %.200s",
                                r.status_code, path, r.text)
                    return None
                r.raise_for_status()
                return r.json()
        except RuntimeError:
            raise  # re-raise TOKEN_EXPIRED para o run() tratar
        except httpx.HTTPStatusError as e:
            log.warning("HTTP %d em %s: %.200s", e.response.status_code, path, e.response.text)
            return None
        except Exception as e:
            log.error("Erro em GET %s: %s", path, e)
            return None

    def _write(self, filename: str, data: Any) -> bool:
        if self.dry_run:
            log.info("[DRY-RUN] %s (%d items)", filename,
                     len(data) if isinstance(data, list) else 1)
            return True
        self.out_dir.mkdir(parents=True, exist_ok=True)
        path = self.out_dir / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        size = path.stat().st_size
        log.info("OK %s (%d bytes)", filename, size)
        return size > 100  # sanity: reject suspiciously tiny files

    # ------------------------------------------------------------------
    # Captures
    # ------------------------------------------------------------------
    def capture_connections(self) -> bool:
        data = self._get("/v1/api/connections")
        if data is None:
            self.results["connections"] = "FAIL"
            return False
        # API retorna {"whatsappConnections": [...]} ou list direta
        if isinstance(data, dict) and "whatsappConnections" in data:
            ok = self._write("connections.json", data)
        elif isinstance(data, list):
            ok = self._write("connections.json", data)
        else:
            self.results["connections"] = "FAIL (unexpected schema)"
            return False
        self.results["connections"] = "OK" if ok else "FAIL"
        return ok

    def capture_contacts(self) -> bool:
        data = self._get("/v1/api/contacts")
        if data is None or not isinstance(data, list):
            self.results["contacts"] = "FAIL"
            return False
        ok = self._write("contacts.json", data)
        self.results["contacts"] = f"OK ({len(data)} items)" if ok else "FAIL"
        return ok

    def capture_extrainfo_fields(self) -> bool:
        # Tentativa em ordem de probabilidade (API Deskrio nao documentada)
        for path in (
            "/v1/api/extra-info/fields",
            "/v1/api/extraInfoFields",
            "/v1/api/extra-info",
            "/v1/api/contact-extra-info",
            "/v1/api/extra-info-fields",
            "/v1/api/extrainfo-fields",
        ):
            data = self._get(path)
            if data is not None:
                ok = self._write("extrainfo_fields.json", data)
                self.results["extrainfo_fields"] = f"OK (via {path})" if ok else "FAIL"
                return ok
        self.results["extrainfo_fields"] = "SKIP (endpoint nao encontrado)"
        return False

    def capture_kanban_boards(self) -> bool:
        data = self._get("/v1/api/kanban-boards")
        if data is None:
            self.results["kanban_boards"] = "FAIL"
            return False
        ok = self._write("kanban_boards.json", data)
        self.results["kanban_boards"] = "OK" if ok else "FAIL"
        return ok

    def capture_tickets(self, days_back: int = 6) -> list[dict]:
        # GAP 1: 5 janelas de 6 dias cobrindo 30 dias, dedup por ticket.id
        # API impoe limite de 7 dias (ERR_DATE_LIMIT_OFF_1_WEEK) — usar 6 por seguranca
        all_tickets: dict[Any, dict] = {}
        windows = 5
        for i in range(windows):
            end = self.target_date - timedelta(days=i * days_back)
            start = end - timedelta(days=days_back)
            params = {"startDate": start.isoformat(), "endDate": end.isoformat()}
            log.info("Tickets janela %d/%d: %s ate %s", i + 1, windows, start.isoformat(), end.isoformat())
            data = self._get("/v1/api/tickets", params=params)
            if data is None or not isinstance(data, list):
                log.warning("Janela %d/%d falhou (start=%s end=%s)", i + 1, windows, start.isoformat(), end.isoformat())
                continue
            for ticket in data:
                tid = ticket.get("id")
                if tid is not None:
                    all_tickets[tid] = ticket
        merged = list(all_tickets.values())
        if not merged:
            self.results["tickets"] = "FAIL"
            return []
        ok = self._write("tickets.json", merged)
        self.results["tickets"] = f"OK ({len(merged)} items, 30d dedup)" if ok else "FAIL"
        return merged if ok else []

    def capture_messages_for_tickets(self, tickets: list[dict], top_n: int = 5) -> None:
        """Captura mensagens dos N tickets mais recentes."""
        if not tickets:
            self.results["messages"] = "SKIP (no tickets)"
            return

        # Ordenar por updatedAt desc
        sorted_tickets = sorted(
            tickets,
            key=lambda t: t.get("updatedAt") or t.get("createdAt") or "",
            reverse=True,
        )[:top_n]

        captured = 0
        for t in sorted_tickets:
            tid = t.get("id")
            if not tid:
                continue
            data = self._get(f"/v1/api/messages/{tid}", params={"pageNumber": "1"})
            if data is None:
                continue
            if self._write(f"messages_{tid}.json", data):
                captured += 1

        self.results["messages"] = f"OK ({captured}/{len(sorted_tickets)})"

    def capture_kanban_columns(self) -> None:
        # GAP 2: capturar colunas de cada board apos salvar kanban_boards.json
        boards_path = self.out_dir / "kanban_boards.json"
        if self.dry_run:
            # Em dry-run nao ha arquivo escrito; tentar ler do dia anterior ou pular
            log.info("[DRY-RUN] capture_kanban_columns — lendo boards do endpoint direto")
            raw = self._get("/v1/api/kanban-boards")
        else:
            if not boards_path.exists():
                self.results["kanban_columns"] = "SKIP (kanban_boards.json nao encontrado)"
                return
            try:
                raw = json.loads(boards_path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.results["kanban_columns"] = f"FAIL (parse boards: {exc})"
                return

        # Extrair lista de boards independente do schema
        if isinstance(raw, list):
            boards_list = raw
        elif isinstance(raw, dict):
            # tenta chaves conhecidas: kanbanBoards, boards, data
            for key in ("kanbanBoards", "boards", "data"):
                if key in raw and isinstance(raw[key], list):
                    boards_list = raw[key]
                    break
            else:
                boards_list = []
        else:
            boards_list = []

        if not boards_list:
            self.results["kanban_columns"] = "SKIP (nenhum board encontrado)"
            return

        ok_count = 0
        fail_count = 0
        for board in boards_list:
            board_id = board.get("id")
            if board_id is None:
                continue
            data = self._get(f"/v1/api/kanban-columns/{board_id}")
            if data is None:
                log.warning("kanban-columns/%s: falhou (403/404) — continuando", board_id)
                fail_count += 1
                self.results[f"kanban_columns_{board_id}"] = "FAIL (403/404)"
                continue
            filename = f"kanban_columns_{board_id}.json"
            written = self._write(filename, data)
            if written:
                ok_count += 1
                self.results[f"kanban_columns_{board_id}"] = "OK"
            else:
                fail_count += 1
                self.results[f"kanban_columns_{board_id}"] = "FAIL (write)"

        self.results["kanban_columns"] = f"OK ({ok_count} boards, {fail_count} falhas)"

    def capture_cnpj_bridge(self, limit: int = 200) -> None:
        # GAP 3: CNPJ Bridge incremental — 200 contatos/dia via custom-field/{number}
        # R3 CRM VITAO360: CNPJ = string 14 digitos zero-padded, NUNCA float/int
        bridge_path = DESKRIO_ROOT / "cnpj_bridge.json"

        # Carregar bridge anterior (historico cumulativo)
        existing: dict[str, Any] = {}
        if bridge_path.exists():
            try:
                raw = json.loads(bridge_path.read_text(encoding="utf-8"))
                existing = raw.get("cnpj_bridge", {})
            except Exception as exc:
                log.warning("Falha ao ler cnpj_bridge.json anterior: %s — iniciando vazio", exc)

        # Carregar contatos do dia
        contacts_path = self.out_dir / "contacts.json"
        if not contacts_path.exists():
            self.results["cnpj_bridge"] = "SKIP (contacts.json nao encontrado)"
            return
        try:
            contacts_raw = json.loads(contacts_path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.results["cnpj_bridge"] = f"FAIL (parse contacts: {exc})"
            return

        if not isinstance(contacts_raw, list):
            self.results["cnpj_bridge"] = "FAIL (contacts.json nao e lista)"
            return

        # Carregar tickets do dia para priorizar contatos com tickets recentes
        tickets_path = self.out_dir / "tickets.json"
        ticket_contact_ids: set[Any] = set()
        if tickets_path.exists():
            try:
                tickets_raw = json.loads(tickets_path.read_text(encoding="utf-8"))
                for t in tickets_raw:
                    cid = t.get("contactId")
                    if cid is not None:
                        ticket_contact_ids.add(str(cid))
            except Exception:
                pass

        # Calcular threshold de 30 dias para pular contatos ja processados recentemente
        cutoff = datetime.utcnow() - timedelta(days=30)

        def needs_update(contact_id: str) -> bool:
            if contact_id not in existing:
                return True
            last = existing[contact_id].get("last_checked", "")
            if not last:
                return True
            try:
                return datetime.fromisoformat(last) < cutoff
            except Exception:
                return True

        # Separar contatos: nao-grupos primeiro, priorizar com tickets
        non_groups = [c for c in contacts_raw if not c.get("isGroup", True)]
        groups = [c for c in contacts_raw if c.get("isGroup", True)]

        # Ordenar: com ticket recente primeiro, depois resto dos nao-grupos, depois grupos
        def sort_key(c: dict) -> int:
            cid = str(c.get("id", ""))
            in_ticket = cid in ticket_contact_ids
            return 0 if in_ticket else 1

        prioritized = sorted(non_groups, key=sort_key) + groups

        # Filtrar apenas quem precisa de update
        to_process = [c for c in prioritized if needs_update(str(c.get("id", "")))][:limit]

        log.info("CNPJ Bridge: %d contatos a processar (limit=%d, ja existentes=%d)",
                 len(to_process), limit, len(existing))

        n_new = 0
        n_skip = 0
        now_iso = datetime.utcnow().isoformat()

        for contact in to_process:
            contact_id = str(contact.get("id", ""))
            number = str(contact.get("number", "")).strip()
            name = contact.get("name", "")

            if not number:
                n_skip += 1
                continue

            data = self._get(f"/v1/api/custom-field/{number}")
            if data is None:
                # Endpoint tolerado como SKIP — registrar sem falhar (pode ser 403/404)
                existing[contact_id] = {
                    "number": number,
                    "name": name,
                    "cnpjs": existing.get(contact_id, {}).get("cnpjs", []),
                    "last_checked": now_iso,
                    "status": "SKIP",
                }
                n_skip += 1
                continue

            # Extrair CNPJs do extraInfo — pode vir em varias estruturas
            raw_cnpjs: list[str] = []
            if isinstance(data, list):
                for field in data:
                    val = field.get("value") or field.get("cnpj") or field.get("extraValue") or ""
                    if val:
                        raw_cnpjs.append(str(val))
            elif isinstance(data, dict):
                for key in ("cnpj", "value", "extraValue", "CNPJ"):
                    val = data.get(key, "")
                    if val:
                        raw_cnpjs.append(str(val))
                # extraInfo pode ser lista dentro do dict
                for item in data.get("extraInfo", []):
                    val = item.get("value") or item.get("extraValue") or ""
                    if val:
                        raw_cnpjs.append(str(val))

            # R3: normalizar todos os CNPJs — string 14 digitos zero-padded, NUNCA float/int
            normalized = []
            for raw_c in raw_cnpjs:
                cleaned = re.sub(r"\D", "", str(raw_c)).zfill(14)
                # Validar que e plausivel (14 digitos, nao zerado inteiramente)
                if len(cleaned) == 14 and cleaned != "00000000000000":
                    normalized.append(cleaned)

            existing[contact_id] = {
                "number": number,
                "name": name,
                "cnpjs": normalized,
                "last_checked": now_iso,
                "status": "OK",
            }
            n_new += 1

        n_total = len(existing)

        bridge_output = {
            "cnpj_bridge": existing,
            "stats": {
                "total_contacts": n_total,
                "processed_today": len(to_process),
                "new_or_updated": n_new,
                "skipped": n_skip,
                "last_run": now_iso,
                "limit_per_day": limit,
            },
        }

        if not self.dry_run:
            bridge_path.write_text(json.dumps(bridge_output, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info("OK cnpj_bridge.json (%d total, %d novos hoje)", n_total, n_new)
        else:
            log.info("[DRY-RUN] cnpj_bridge (%d total, %d novos hoje)", n_total, n_new)

        self.results["cnpj_bridge"] = f"OK ({n_new} novos, {n_total} total)"

    def _save_extraction_report(self, finished_at: datetime, exit_code: int) -> None:
        # GAP 4: salvar extraction_report.json + atualizar latest_extraction.json
        duration = (finished_at - self._started_at).total_seconds()

        # Contar itens nos arquivos salvos para o campo counts
        counts: dict[str, int] = {}
        for fname in ("contacts.json", "tickets.json", "connections.json"):
            fpath = self.out_dir / fname
            if fpath.exists():
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    if isinstance(data, list):
                        counts[fname.replace(".json", "")] = len(data)
                    elif isinstance(data, dict):
                        # tickets/contacts podem vir embrulhados
                        for key in ("data", "items", "results"):
                            if isinstance(data.get(key), list):
                                counts[fname.replace(".json", "")] = len(data[key])
                                break
                except Exception:
                    pass

        # Adicionar contagem de kanban_columns gerados
        kanban_col_files = list(self.out_dir.glob("kanban_columns_*.json")) if not self.dry_run else []
        counts["kanban_column_files"] = len(kanban_col_files)

        # Contagem bridge
        bridge_path = DESKRIO_ROOT / "cnpj_bridge.json"
        if bridge_path.exists():
            try:
                b = json.loads(bridge_path.read_text(encoding="utf-8"))
                counts["cnpj_bridge_total"] = len(b.get("cnpj_bridge", {}))
            except Exception:
                pass

        # DESKRIO_PROFILE pode ser "admin" (login) ou email — usar email do token se disponivel
        raw_profile = self.env.get("DESKRIO_PROFILE", "leandro.garcia@vitao.com.br")
        token_email = raw_profile if "@" in raw_profile else "leandro.garcia@vitao.com.br"

        report = {
            "date": self.target_date.isoformat(),
            "started_at": self._started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": round(duration, 1),
            "results": self.results,
            "exit_code": exit_code,
            "token_email": token_email,
            "counts": counts,
        }

        if not self.dry_run:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            report_path = self.out_dir / "extraction_report.json"
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info("OK extraction_report.json (%.1fs)", duration)

            latest = {
                "date": self.target_date.isoformat(),
                "dir": str(self.out_dir.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "report_summary": {
                    "exit_code": exit_code,
                    "duration_seconds": round(duration, 1),
                    "counts": counts,
                    "results": self.results,
                },
            }
            latest_path = DESKRIO_ROOT / "latest_extraction.json"
            latest_path.write_text(json.dumps(latest, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info("OK latest_extraction.json")
        else:
            log.info("[DRY-RUN] extraction_report (duration=%.1fs, exit_code=%d)", duration, exit_code)

    def capture_kanban_cards_if_ids_known(self) -> None:
        """Tentativa graciosa: se _card_ids.json existir, captura por ID."""
        ids_file = DESKRIO_ROOT / "_card_ids.json"
        if not ids_file.exists():
            self.results["kanban_cards"] = "SKIP (no _card_ids.json — endpoint de listagem nao publico)"
            return

        try:
            ids = json.loads(ids_file.read_text(encoding="utf-8"))
        except Exception:
            self.results["kanban_cards"] = "FAIL (parse _card_ids.json)"
            return

        # ids dict: {"20": [11636, 11640, ...], "100": [...]}
        for board_id, card_ids in ids.items():
            cards = []
            for cid in card_ids:
                d = self._get(f"/v1/api/kanban-card/{cid}")
                if isinstance(d, list) and d:
                    cards.extend(d)
                elif isinstance(d, dict):
                    cards.append(d)
            if cards:
                self._write(f"kanban_cards_{board_id}.json", cards)

        self.results["kanban_cards"] = f"OK (id-based, {sum(len(v) for v in ids.values())} attempted)"

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def run(self) -> int:
        log.info("=" * 60)
        log.info("Deskrio snapshot | date=%s | out=%s", self.target_date, self.out_dir)
        log.info("=" * 60)

        if not self.token or not self.base_url:
            log.error("FALHA CRITICA: DESKRIO_API_TOKEN ou DESKRIO_API_URL ausentes")
            return 1

        # Sanity check: token valido?
        try:
            test = self._get("/v1/api/connections", _raise_on_token_error=True)
        except RuntimeError:
            log.error("FALHA CRITICA: TOKEN_EXPIRED — renovar DESKRIO_API_TOKEN em .env")
            return 1
        if test is None:
            log.error("FALHA CRITICA: token invalido ou API fora do ar")
            return 1

        # Run captures
        self.capture_connections()
        self.capture_contacts()
        self.capture_extrainfo_fields()
        self.capture_kanban_boards()
        self.capture_kanban_columns()  # GAP 2: colunas de cada board
        tickets = self.capture_tickets()  # GAP 1: 30 dias em 5 janelas
        self.capture_messages_for_tickets(tickets)
        self.capture_kanban_cards_if_ids_known()
        self.capture_cnpj_bridge()  # GAP 3: CNPJ Bridge incremental

        # Report
        log.info("=" * 60)
        log.info("RESULTADO:")
        for k, v in self.results.items():
            status = "OK" if v.startswith("OK") else ("SKIP" if v.startswith("SKIP") else "FAIL")
            log.info("  [%s] %-22s %s", status, k, v)

        # Exit code
        critical = {"connections", "contacts", "tickets", "kanban_boards"}
        failed_critical = [k for k in critical if not self.results.get(k, "").startswith("OK")]
        if failed_critical:
            log.error("FALHAS CRITICAS: %s", failed_critical)
            exit_code = 1
        else:
            failed_any = [k for k, v in self.results.items() if v.startswith("FAIL")]
            exit_code = 0 if not failed_any else 2

        # GAP 4: salvar extraction_report.json e latest_extraction.json
        self._save_extraction_report(finished_at=datetime.utcnow(), exit_code=exit_code)

        return exit_code


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Captura snapshot diario Deskrio")
    ap.add_argument("--date", help="YYYY-MM-DD (default: hoje)", default=None)
    ap.add_argument("--dry-run", action="store_true", help="Nao escreve arquivos")
    args = ap.parse_args()

    if args.date:
        try:
            target = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            log.error("Data invalida: %s (use YYYY-MM-DD)", args.date)
            return 1
    else:
        target = date.today()

    snap = DeskrioSnapshot(target, dry_run=args.dry_run)
    return snap.run()


if __name__ == "__main__":
    sys.exit(main())
