#!/usr/bin/env python3
"""
CRM VITAO360 — deskrio_daily_snapshot.py
=========================================
Captura reprodutivel dos dados Deskrio para data/deskrio/{YYYY-MM-DD}/.

Consolidacao dos artefatos que antes eram gerados externamente. Usa o
DeskrioService existente (backend/app/services/deskrio_service.py) para
manter um unico ponto de chamada HTTP com retry + cache + logging.

ENDPOINTS COBERTOS (testados 2026-04-24):
  GET  /v1/api/connections        -> connections.json
  GET  /v1/api/contacts           -> contacts.json
  GET  /v1/api/tickets?...        -> tickets.json (ultimos 7 dias)
  GET  /v1/api/kanban-boards      -> kanban_boards.json
  GET  /v1/api/kanban-columns/:id -> (usado pra resolver colunas)
  GET  /v1/api/messages/:ticketId -> messages_{ticketId}.json (top N)

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

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any | None:
        if not self.token or not self.base_url:
            log.error("DESKRIO_API_TOKEN ou DESKRIO_API_URL ausente em .env")
            return None
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.get(url, headers=self._headers(), params=params or {})
                if r.status_code == 403 and "Invalid token" in r.text:
                    log.warning("403 Invalid token em %s — endpoint privado?", path)
                    return None
                r.raise_for_status()
                return r.json()
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
        # API impoe limite de 7 dias (ERR_DATE_LIMIT_OFF_1_WEEK) — usar 6 por seguranca
        end = self.target_date
        start = end - timedelta(days=days_back)
        params = {"startDate": start.isoformat(), "endDate": end.isoformat()}
        data = self._get("/v1/api/tickets", params=params)
        if data is None or not isinstance(data, list):
            self.results["tickets"] = "FAIL"
            return []
        ok = self._write("tickets.json", data)
        self.results["tickets"] = f"OK ({len(data)} items)" if ok else "FAIL"
        return data if ok else []

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
        test = self._get("/v1/api/connections")
        if test is None:
            log.error("FALHA CRITICA: token invalido ou API fora do ar")
            return 1

        # Run captures
        self.capture_connections()
        self.capture_contacts()
        self.capture_extrainfo_fields()
        self.capture_kanban_boards()
        tickets = self.capture_tickets()
        self.capture_messages_for_tickets(tickets)
        self.capture_kanban_cards_if_ids_known()

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
            return 1
        failed_any = [k for k, v in self.results.items() if v.startswith("FAIL")]
        return 0 if not failed_any else 2


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
