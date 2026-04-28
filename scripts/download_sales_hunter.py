#!/usr/bin/env python3
"""
CRM VITAO360 - download_sales_hunter.py
========================================
Download diario automatizado dos relatorios SAP via interface web Sales Hunter.

Salva XLSX em: data/sales_hunter/{YYYY-MM-DD}/morning/
Formato:       {tipo}_{empresa}_all_{YYYY-MM-DD}_0800.xlsx

Spec autoritativa: SALES_HUNTER_EXTRACTION_SPEC.md (raiz do projeto).
A interface NAO e REST/JSON — e formulario web Laravel com CSRF token.
Fluxo: GET /login -> POST /login -> GET /relatorios -> POST /relatorios/gerar/excel

REGRAS RESPEITADAS:
  R8  - Zero fabricacao: dados vem direto do SAP via web. Tier=REAL.
  R11 - Idempotente: arquivo ja baixado (>500B e <6h) e skipado, exceto --force.
  R12 - L2: novo script (refactor / nova ferramenta), nao toca estrutura nem
        Two-Base. Apenas baixa arquivos brutos, nao mexe no banco com
        valores monetarios — apenas registra job de download.

ENV VARS:
  SALES_HUNTER_USER  (login, ex: leandro@maisgranel.com.br)
  SALES_HUNTER_PASS  (senha)
  SALES_HUNTER_URL   (opcional, default http://saleshunter.vitao.com.br)

USO:
  python scripts/download_sales_hunter.py                    # hoje
  python scripts/download_sales_hunter.py --date 2026-04-25
  python scripts/download_sales_hunter.py --force            # re-download
  python scripts/download_sales_hunter.py --dry-run          # planeja, nao baixa

EXIT CODES:
  0 = sucesso (todos relatorios criticos baixados ou ja existentes)
  1 = falha critica (login falhou, sem credenciais, erro IO)
  2 = sucesso parcial (alguns relatorios falharam, ex: pedidos_vv 302)
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Setup de paths — script chamavel de qualquer diretorio
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Carregamento de .env / .env.local — antes de imports dependentes
# (mesmo padrao de ingest_sales_hunter.py)
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


# ---------------------------------------------------------------------------
# Imports tardios
# ---------------------------------------------------------------------------
try:
    import httpx
except ImportError:
    print("ERRO: httpx nao instalado. Execute: pip install httpx")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
log = logging.getLogger("download_sales_hunter")


# ---------------------------------------------------------------------------
# Constantes (alinhadas com SALES_HUNTER_EXTRACTION_SPEC.md)
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "http://saleshunter.vitao.com.br"

SALES_HUNTER_ROOT = PROJECT_ROOT / "data" / "sales_hunter"

# Validacao basica de XLSX baixado: bytes minimos para nao ser pagina HTML
# de erro / login redirect (login HTML completo tem ~30KB, mas o gerador
# devolve XLSX >5KB ate para fat_empresa que e o menor — 6.7KB segundo a spec).
MIN_XLSX_BYTES = 500

# Idempotencia: se arquivo existe e foi modificado nas ultimas 6h, skip
IDEMPOTENT_MAX_AGE_HOURS = 6.0

# Timeout HTTP por request
HTTP_TIMEOUT_SEC = 120.0

# Retries com backoff
HTTP_RETRIES = 2
HTTP_RETRY_GAP_SEC = 30.0

# Pausa entre downloads para nao martelar o servidor Laravel
DOWNLOAD_DELAY_SEC = 1.0

# Tipos de relatorio P1 (diarios) — tipo_relatorio, short_name
# Spec autoritativa: SALES_HUNTER_EXTRACTION_SPEC.md sec "P1 — Diario"
RELATORIOS = [
    ("RelatorioDeFaturamentoPorCliente", "fat_cliente"),
    ("RelatorioDeFaturamentoPorNotaFiscalDetalhada", "fat_nf_det"),
    ("RelatorioDeFaturamentoPorProduto", "fat_produto"),
    ("RelatorioDeFaturamentoPorEmpresa", "fat_empresa"),
    ("RelatorioDeDebitos", "debitos"),
    ("RelatorioDeDevolucaoPorCliente", "devolucao_cliente"),
    ("RelatorioDePedidos", "pedidos_produto"),
]

# Empresas (id no Sales Hunter, codigo curto)
EMPRESAS = [
    (12, "cwb"),  # VITAO Curitiba
    (13, "vv"),   # VITAO Vila Velha
    # NOTA: ingest_sales_hunter.py ignora VV (dataset identico a CWB —
    # decisao L3#5b 2026-04-26). Mantemos o download para rastreabilidade.
]

# Sufixo horario fixo (compativel com pipeline existente que ja gravou
# arquivos como fat_cliente_cwb_all_2026-04-25_0800.xlsx)
FILENAME_HOUR_SUFFIX = "0800"


# ---------------------------------------------------------------------------
# CSRF token extractor (Laravel: <input name="_token" value="...">)
# ---------------------------------------------------------------------------
_CSRF_RE = re.compile(
    r'name="_token"\s+(?:[^>]*?\s+)?value="([^"]+)"|'
    r'value="([^"]+)"\s+(?:[^>]*?\s+)?name="_token"',
    re.IGNORECASE,
)


def extract_csrf_token(html: str) -> Optional[str]:
    """Extrai o primeiro CSRF _token do HTML retornado pelo Laravel.

    Aceita ambas ordens de atributo (name antes/depois de value) — alguns
    templates Blade emitem em ordem nao-padrao.
    """
    if not html:
        return None
    m = _CSRF_RE.search(html)
    if not m:
        return None
    return m.group(1) or m.group(2)


# ---------------------------------------------------------------------------
# Cliente Sales Hunter
# ---------------------------------------------------------------------------
class SalesHunterClient:
    """Wrapper minimo sobre httpx.Client com fluxo de auth Laravel."""

    def __init__(self, base_url: str, user: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        # follow_redirects True replica o comportamento da spec
        # (curl segue redirect 302 do GET / apos login).
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=HTTP_TIMEOUT_SEC,
            follow_redirects=True,
            headers={
                "User-Agent": "CRM-VITAO360/download_sales_hunter (httpx)",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            },
        )

    def __enter__(self) -> "SalesHunterClient":
        return self

    def __exit__(self, *exc) -> None:  # type: ignore[no-untyped-def]
        try:
            self.client.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Auth flow
    # ------------------------------------------------------------------
    def login(self) -> None:
        """Executa fluxo de login Laravel (4 requests).

        1. GET /login -> coleta cookies + extrai _token CSRF
        2. POST /login -> envia credenciais com mesmos cookies
        3. GET / -> follow redirect (valida sessao autenticada)
        Levanta RuntimeError se qualquer etapa falhar.
        """
        log.info("Login: GET /login...")
        r1 = self.client.get("/login")
        if r1.status_code >= 400:
            raise RuntimeError(f"GET /login falhou: HTTP {r1.status_code}")

        token = extract_csrf_token(r1.text)
        if not token:
            raise RuntimeError("GET /login: CSRF _token nao encontrado no HTML")

        log.info("Login: POST /login (credenciais)...")
        r2 = self.client.post(
            "/login",
            data={
                "_token": token,
                "email": self.user,
                "password": self.password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r2.status_code >= 400:
            raise RuntimeError(f"POST /login falhou: HTTP {r2.status_code}")

        # Heuristica: apos login com sucesso, o redirect leva ao dashboard.
        # Se a resposta final ainda contiver o form de login, credenciais
        # estao erradas.
        if "name=\"password\"" in r2.text.lower() or "/login" in str(r2.url):
            raise RuntimeError(
                "Login rejeitado (resposta ainda mostra form). "
                "Verifique SALES_HUNTER_USER / SALES_HUNTER_PASS."
            )

        log.info("Login: GET / (valida sessao)...")
        r3 = self.client.get("/")
        if r3.status_code >= 400:
            raise RuntimeError(f"GET / pos-login falhou: HTTP {r3.status_code}")

        log.info("Login: OK (sessao autenticada)")

    # ------------------------------------------------------------------
    # Token CSRF para download (precisa pegar novo a cada POST)
    # ------------------------------------------------------------------
    def get_relatorios_token(self) -> str:
        """GET /relatorios para extrair novo _token CSRF de download."""
        r = self.client.get("/relatorios")
        if r.status_code >= 400:
            raise RuntimeError(f"GET /relatorios falhou: HTTP {r.status_code}")
        token = extract_csrf_token(r.text)
        if not token:
            raise RuntimeError("GET /relatorios: CSRF _token nao encontrado")
        return token

    # ------------------------------------------------------------------
    # Download de um relatorio
    # ------------------------------------------------------------------
    def download_excel(
        self,
        tipo_relatorio: str,
        empresa_id: int,
        data_inicial: str,
        data_final: str,
        output_path: Path,
    ) -> tuple[bool, int, str]:
        """Baixa um XLSX. Retorna (sucesso, bytes, motivo).

        - sucesso=True somente se HTTP 200 + bytes > MIN_XLSX_BYTES + assinatura PK.
        - HTML retornado em vez de XLSX -> log WARN, sucesso=False, arquivo removido.
        """
        # Pega novo CSRF token a cada download (Laravel consome a cada POST)
        try:
            csrf = self.get_relatorios_token()
        except Exception as exc:
            return False, 0, f"csrf-fetch-error: {exc}"

        payload = {
            "_token": csrf,
            "tipo_relatorio": tipo_relatorio,
            # Laravel espera array com colchetes no nome
            "empresa_faturamento[]": str(empresa_id),
            "data_inicial": data_inicial,
            "data_final": data_final,
        }

        last_exc: Optional[Exception] = None
        for tentativa in range(1, HTTP_RETRIES + 2):  # 1..(retries+1)
            try:
                r = self.client.post(
                    "/relatorios/gerar/excel",
                    data=payload,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/vnd.openxmlformats-officedocument"
                                  ".spreadsheetml.sheet,application/octet-stream,*/*",
                    },
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                log.warning(
                    "Download %s/%s tentativa %d falhou: %s",
                    tipo_relatorio, empresa_id, tentativa, exc,
                )
                if tentativa <= HTTP_RETRIES:
                    time.sleep(HTTP_RETRY_GAP_SEC)
                continue

            if r.status_code != 200:
                # 302/redirect = sessao expirou ou empresa nao tem dados
                if tentativa <= HTTP_RETRIES and r.status_code in (500, 502, 503, 504):
                    log.warning(
                        "Download %s/%s HTTP %d, retry em %.0fs...",
                        tipo_relatorio, empresa_id, r.status_code, HTTP_RETRY_GAP_SEC,
                    )
                    time.sleep(HTTP_RETRY_GAP_SEC)
                    continue
                return False, 0, f"http-{r.status_code}"

            content = r.content
            n = len(content)

            if n < MIN_XLSX_BYTES:
                return False, n, "tamanho-minimo"

            # Assinatura XLSX = ZIP = "PK\x03\x04"
            if not content.startswith(b"PK\x03\x04"):
                # Provavelmente HTML de erro. Loga primeiros 200 chars para diag.
                preview = content[:200].decode("utf-8", errors="replace").replace("\n", " ")
                log.warning(
                    "Download %s/%s: resposta NAO e XLSX (preview: %s...)",
                    tipo_relatorio, empresa_id, preview[:120],
                )
                return False, n, "html-em-vez-de-xlsx"

            # Sucesso: grava
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(content)
            except OSError as exc:
                return False, n, f"io-error: {exc}"

            return True, n, "ok"

        return False, 0, f"esgotou-retries: {last_exc}"


# ---------------------------------------------------------------------------
# Idempotencia helper
# ---------------------------------------------------------------------------
def arquivo_recente(path: Path, max_age_hours: float) -> bool:
    """True se arquivo existe, tem >MIN_XLSX_BYTES e foi modificado em <max_age_hours."""
    if not path.exists():
        return False
    try:
        size = path.stat().st_size
        if size < MIN_XLSX_BYTES:
            return False
        age_sec = time.time() - path.stat().st_mtime
        return age_sec < max_age_hours * 3600.0
    except OSError:
        return False


# ---------------------------------------------------------------------------
# ImportJob helpers (mesmo padrao de ingest_sales_hunter.py)
# ---------------------------------------------------------------------------
def criar_import_job(arquivo_nome: str) -> Optional[int]:
    """Cria ImportJob tipo SALES_HUNTER_DOWNLOAD em status PROCESSANDO. Retorna id.

    Falhas sao tratadas como WARNING (download nao depende disso para funcionar).
    """
    if not os.environ.get("DATABASE_URL"):
        return None
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.models.import_job import ImportJob

        engine = create_engine(os.environ["DATABASE_URL"])
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            job = ImportJob(
                tipo="SALES_HUNTER_DOWNLOAD",
                arquivo_nome=arquivo_nome[:255],
                status="PROCESSANDO",
                iniciado_em=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.add(job)
            session.commit()
            jid = job.id
            log.info("ImportJob criado: id=%s tipo=SALES_HUNTER_DOWNLOAD", jid)
            return jid
        finally:
            session.close()
            engine.dispose()
    except Exception as exc:
        log.warning("Nao consegui criar ImportJob (seguindo sem tracking): %s", exc)
        return None


def finalizar_import_job(
    job_id: Optional[int],
    baixados: int,
    skipados: int,
    falhados: int,
    erro_msg: Optional[str] = None,
) -> None:
    """Atualiza ImportJob com contadores finais."""
    if job_id is None:
        return
    if not os.environ.get("DATABASE_URL"):
        return
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.models.import_job import ImportJob

        engine = create_engine(os.environ["DATABASE_URL"])
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            job = session.query(ImportJob).filter(ImportJob.id == job_id).first()
            if not job:
                return
            job.registros_lidos = baixados + skipados + falhados
            job.registros_inseridos = baixados
            job.registros_atualizados = 0
            job.registros_ignorados = skipados
            job.concluido_em = datetime.now(timezone.utc).replace(tzinfo=None)
            if erro_msg or falhados > 0:
                # Mantem CONCLUIDO se houve sucesso parcial — falhados como ignorados.
                # Soh marca ERRO se nada foi baixado e havia erro_msg.
                if erro_msg and baixados == 0:
                    job.status = "ERRO"
                    job.erro_mensagem = erro_msg[:2000]
                else:
                    job.status = "CONCLUIDO"
                    if erro_msg:
                        job.erro_mensagem = erro_msg[:2000]
            else:
                job.status = "CONCLUIDO"
            session.commit()
            log.info(
                "ImportJob %s -> %s (baixados=%d skipados=%d falhados=%d)",
                job_id, job.status, baixados, skipados, falhados,
            )
        finally:
            session.close()
            engine.dispose()
    except Exception as exc:
        log.warning("Nao consegui finalizar ImportJob %s: %s", job_id, exc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download diario dos relatorios SAP via Sales Hunter.",
    )
    p.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Data alvo no formato YYYY-MM-DD (default: hoje).",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Re-download mesmo se arquivo existir e estiver recente.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista o que faria, sem login nem download.",
    )
    p.add_argument(
        "--periodo-inicio",
        default=None,
        help="Data inicial do relatorio (default: dia 1 do mes do --date).",
    )
    p.add_argument(
        "--periodo-fim",
        default=None,
        help="Data final do relatorio (default: --date).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Resolve datas
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        log.error("Formato de --date invalido: %s (esperado YYYY-MM-DD)", args.date)
        return 1

    data_final = (args.periodo_fim or target_date.isoformat())
    data_inicial = args.periodo_inicio or target_date.replace(day=1).isoformat()

    # Validacao basica de datas
    for label, val in (("periodo_inicio", data_inicial), ("periodo_fim", data_final)):
        try:
            datetime.strptime(val, "%Y-%m-%d")
        except ValueError:
            log.error("Formato invalido em %s: %s", label, val)
            return 1

    # Output dir
    morning_dir = SALES_HUNTER_ROOT / target_date.isoformat() / "morning"

    # Plano: lista (tipo, empresa_id, empresa_short, output_path)
    plano: list[tuple[str, str, int, str, Path]] = []
    for tipo_relatorio, short_name in RELATORIOS:
        for empresa_id, empresa_short in EMPRESAS:
            fname = (
                f"{short_name}_{empresa_short}_all_"
                f"{target_date.isoformat()}_{FILENAME_HOUR_SUFFIX}.xlsx"
            )
            plano.append((
                tipo_relatorio, short_name, empresa_id, empresa_short,
                morning_dir / fname,
            ))

    log.info("Planejamento: %d downloads (%d tipos x %d empresas)",
             len(plano), len(RELATORIOS), len(EMPRESAS))
    log.info("Output: %s", morning_dir)
    log.info("Periodo: %s a %s", data_inicial, data_final)

    if args.dry_run:
        print()
        print("=" * 70)
        print(f"  DOWNLOAD SALES HUNTER [DRY RUN]")
        print(f"  Data alvo    : {target_date.isoformat()}")
        print(f"  Periodo      : {data_inicial} -> {data_final}")
        print(f"  Output       : {morning_dir}")
        print("=" * 70)
        for tipo, short, emp_id, emp_short, out_path in plano:
            existe = arquivo_recente(out_path, IDEMPOTENT_MAX_AGE_HOURS)
            status = "SKIP (recente)" if existe and not args.force else "BAIXARIA"
            print(f"  [{status:>14}] {short}/{emp_short} -> {out_path.name}")
        print("=" * 70)
        return 0

    # Credenciais
    user = os.environ.get("SALES_HUNTER_USER", "").strip()
    pw = os.environ.get("SALES_HUNTER_PASS", "").strip()
    base_url = os.environ.get("SALES_HUNTER_URL", DEFAULT_BASE_URL).strip()
    if not user or not pw:
        log.error(
            "Credenciais ausentes. Defina SALES_HUNTER_USER e "
            "SALES_HUNTER_PASS em .env ou ambiente."
        )
        return 1

    # ImportJob inicial
    arquivo_label = (
        str(morning_dir.relative_to(PROJECT_ROOT))
        if morning_dir.is_relative_to(PROJECT_ROOT)
        else str(morning_dir)
    )
    job_id = criar_import_job(arquivo_label)

    baixados = 0
    skipados = 0
    falhados = 0
    erro_critico: Optional[str] = None
    detalhes: list[str] = []
    inicio = time.time()

    try:
        # Filtra plano: skipa arquivos recentes a menos de --force
        a_baixar: list[tuple[str, str, int, str, Path]] = []
        for item in plano:
            tipo, short, emp_id, emp_short, out_path = item
            if not args.force and arquivo_recente(out_path, IDEMPOTENT_MAX_AGE_HOURS):
                age_h = (time.time() - out_path.stat().st_mtime) / 3600.0
                log.info(
                    "SKIP %s/%s (existe, %.1fh < %.1fh)",
                    short, emp_short, age_h, IDEMPOTENT_MAX_AGE_HOURS,
                )
                skipados += 1
                detalhes.append(f"SKIP {short}/{emp_short} (recente)")
                continue
            a_baixar.append(item)

        if not a_baixar:
            log.info("Nada a baixar — todos arquivos recentes. Use --force para re-download.")
        else:
            with SalesHunterClient(base_url, user, pw) as cli:
                cli.login()

                for idx, (tipo, short, emp_id, emp_short, out_path) in enumerate(a_baixar, 1):
                    log.info(
                        "[%d/%d] Baixando %s/%s -> %s",
                        idx, len(a_baixar), short, emp_short, out_path.name,
                    )
                    ok, n, motivo = cli.download_excel(
                        tipo_relatorio=tipo,
                        empresa_id=emp_id,
                        data_inicial=data_inicial,
                        data_final=data_final,
                        output_path=out_path,
                    )
                    if ok:
                        baixados += 1
                        detalhes.append(f"OK   {short}/{emp_short} ({n} bytes)")
                        log.info("  OK (%d bytes)", n)
                    else:
                        falhados += 1
                        detalhes.append(f"FAIL {short}/{emp_short} ({motivo})")
                        log.warning("  FALHA: %s", motivo)
                    time.sleep(DOWNLOAD_DELAY_SEC)
    except Exception as exc:
        erro_critico = str(exc)
        log.error("Erro critico: %s", exc)

    duracao = time.time() - inicio

    # Finaliza ImportJob
    finalizar_import_job(job_id, baixados, skipados, falhados, erro_critico)

    # Relatorio final
    print()
    print("=" * 70)
    print(f"  DOWNLOAD SALES HUNTER -> {morning_dir.relative_to(PROJECT_ROOT)}")
    if job_id is not None:
        print(f"  ImportJob id : {job_id}")
    print(f"  Duracao      : {duracao:.1f}s")
    print(f"  Baixados     : {baixados}")
    print(f"  Skipados     : {skipados}")
    print(f"  Falhados     : {falhados}")
    print("-" * 70)
    for d in detalhes:
        print(f"  {d}")
    if erro_critico:
        print("-" * 70)
        print(f"  ERRO CRITICO: {erro_critico}")
    print("=" * 70)

    # Exit code
    if erro_critico:
        return 1
    if falhados > 0 and baixados == 0 and skipados == 0:
        return 1
    if falhados > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
