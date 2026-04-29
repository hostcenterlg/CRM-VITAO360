#!/usr/bin/env bash
# qa_smoke_post_deploy.sh — Smoke test pós-deploy frontend Vercel
# Uso: ./scripts/qa_smoke_post_deploy.sh [--token <bearer_token>]
# Idempotente: pode ser executado múltiplas vezes sem efeito colateral.
set -uo pipefail

FRONTEND="https://intelligent-crm360.vercel.app"
BACKEND="https://crm-vitao360.vercel.app"
TOKEN=""
PASS=0
FAIL=0

# Parsear argumentos
while [[ $# -gt 0 ]]; do
  case "$1" in
    --token) TOKEN="$2"; shift 2 ;;
    *) echo "Argumento desconhecido: $1"; exit 1 ;;
  esac
done

# Helpers de cor (desabilitado se não for terminal)
if [[ -t 1 ]]; then
  green() { echo -e "\e[32m[PASS] $*\e[0m"; }
  red()   { echo -e "\e[31m[FAIL] $*\e[0m"; }
  yellow(){ echo -e "\e[33m[SKIP] $*\e[0m"; }
  bold()  { echo -e "\e[1m$*\e[0m"; }
else
  green() { echo "[PASS] $*"; }
  red()   { echo "[FAIL] $*"; }
  yellow(){ echo "[SKIP] $*"; }
  bold()  { echo "$*"; }
fi

record_pass() { PASS=$((PASS + 1)); green "$*"; }
record_fail() { FAIL=$((FAIL + 1)); red "$*"; }

# Verifica redirect: espera HTTP 307 ou 308 + Location contendo expected_loc
check_redirect() {
  local label="$1"
  local url="$2"
  local expected_loc="$3"

  local headers
  headers=$(curl -sI --max-time 10 "$url" 2>/dev/null)
  local code
  code=$(echo "$headers" | grep -i '^HTTP/' | tail -1 | awk '{print $2}')
  local loc
  loc=$(echo "$headers" | grep -i '^location:' | tr -d '\r' | awk '{print $2}')

  if [[ "$code" =~ ^30[78]$ ]] && [[ "$loc" == *"$expected_loc"* ]]; then
    record_pass "$label → $code → Location: $loc"
  else
    record_fail "$label → HTTP $code (Location: '$loc', esperado redirect para '$expected_loc')"
  fi
}

# Verifica que URL retorna HTTP 200
check_200() {
  local label="$1"
  local url="$2"

  local code
  code=$(curl -sI --max-time 10 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  if [[ "$code" == "200" ]]; then
    record_pass "$label → 200"
  else
    record_fail "$label → HTTP $code (esperado 200)"
  fi
}

# Verifica que URL retorna HTTP 200 ou 307/308 (aceita auth redirect)
check_200_or_redirect() {
  local label="$1"
  local url="$2"

  local code
  code=$(curl -sI --max-time 10 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  if [[ "$code" == "200" ]] || [[ "$code" =~ ^30[78]$ ]]; then
    record_pass "$label → $code"
  else
    record_fail "$label → HTTP $code (esperado 200 ou 307/308)"
  fi
}

# Verifica campo metricas.vendas_semana_volume na API resumo-semanal
check_api_resumo_semanal() {
  local consultor="$1"
  local token="$2"

  local resp
  resp=$(curl -s --max-time 20 \
    -H "Authorization: Bearer $token" \
    "$BACKEND/api/ia/resumo-semanal/$consultor" 2>/dev/null)

  if [[ -z "$resp" ]]; then
    record_fail "API resumo-semanal/$consultor → resposta vazia (timeout ou conexão recusada)"
    return
  fi

  # Extrai metricas.vendas_semana_volume via python (disponível no ambiente do projeto)
  local vol
  vol=$(echo "$resp" | python -c "
import sys, json, math
try:
    d = json.load(sys.stdin)
    v = d['metricas']['vendas_semana_volume']
    if v is None:
        print('NULL')
    elif isinstance(v, float) and math.isnan(v):
        print('NaN')
    else:
        print(v)
except KeyError as e:
    print(f'KEY_ERROR:{e}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>/dev/null)

  case "$vol" in
    NULL)
      record_fail "API resumo-semanal/$consultor → metricas.vendas_semana_volume é NULL" ;;
    NaN)
      record_fail "API resumo-semanal/$consultor → metricas.vendas_semana_volume é NaN (fix não propagado)" ;;
    KEY_ERROR*)
      record_fail "API resumo-semanal/$consultor → campo ausente: $vol" ;;
    ERROR*)
      record_fail "API resumo-semanal/$consultor → erro ao parsear JSON: $vol" ;;
    "")
      record_fail "API resumo-semanal/$consultor → python falhou ao extrair volume (resp: ${resp:0:200})" ;;
    *)
      record_pass "API resumo-semanal/$consultor → metricas.vendas_semana_volume = $vol" ;;
  esac
}

# Verifica deploy ID recente (sem cache)
check_cache_bust() {
  local url="$1"

  local headers
  headers=$(curl -sI --max-time 10 -H "Cache-Control: no-cache" "$url" 2>/dev/null)
  local deploy_id
  deploy_id=$(echo "$headers" | grep -i 'x-vercel-id\|x-deployment-id\|x-matched-path' | tr -d '\r' | head -3)
  local age
  age=$(echo "$headers" | grep -i '^age:' | tr -d '\r' | awk '{print $2}')
  local code
  code=$(echo "$headers" | grep -i '^HTTP/' | tail -1 | awk '{print $2}')

  if [[ -n "$age" ]] && [[ "$age" -gt 3600 ]] 2>/dev/null; then
    record_fail "Cache $url → Age: ${age}s (>${age}s indica CDN stale — redeploy necessário)"
    echo "         Headers de diagnóstico: $deploy_id"
  else
    record_pass "Cache $url → HTTP $code, Age: ${age:-N/A}s"
    [[ -n "$deploy_id" ]] && echo "         $deploy_id"
  fi
}

# --- Execução ---

bold "=== Smoke Test Pós-Deploy Vercel — $(date '+%Y-%m-%d %H:%M:%S') ==="
bold "Frontend: $FRONTEND"
bold "Backend:  $BACKEND"
echo ""

bold "--- Grupo 1: Redirects ---"
check_redirect "T1: /dashboard → /"     "$FRONTEND/dashboard" "/"
check_redirect "T2: /manual → /docs"    "$FRONTEND/manual"    "/docs"

echo ""
bold "--- Grupo 2: Rotas 200 ---"
check_200              "T3: /docs"      "$FRONTEND/docs"
check_200              "T4: /"          "$FRONTEND/"
check_200_or_redirect  "T5: /carteira"  "$FRONTEND/carteira"

echo ""
bold "--- Grupo 3: API ---"
if [[ -n "$TOKEN" ]]; then
  check_api_resumo_semanal "LARISSA" "$TOKEN"
else
  yellow "T6: API resumo-semanal — SKIPPED (passe --token <bearer> para habilitar)"
fi

echo ""
bold "--- Grupo 4: Cache ---"
check_cache_bust "$FRONTEND/dashboard"

echo ""
bold "=== Resultado: $PASS PASS / $FAIL FAIL ==="

if [[ $FAIL -eq 0 ]]; then
  green "SMOKE TEST: ALL PASS"
  exit 0
else
  red "SMOKE TEST: $FAIL FALHA(S) — ver detalhes acima"
  exit 1
fi
