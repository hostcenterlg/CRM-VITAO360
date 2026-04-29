# Inbox WhatsApp Status Incident — 29/Apr/2026 — RESOLVED

## Sintoma

`GET https://crm-vitao360.vercel.app/api/whatsapp/status` (autenticado) retornava
`{"configurado":true,"conexoes":[],"alguma_conectada":false,"total_conexoes":0}`
mesmo com `DESKRIO_API_TOKEN` configurado no Vercel. Frontend
`intelligent-crm360.vercel.app/inbox` exibia "Sem conexão ativa".

## Causa Raiz

Token `DESKRIO_API_TOKEN` no Vercel possuía caracter `\n` (newline) ao final.
Quando `httpx` tentava montar o header `Authorization: Bearer <token>\n`,
levantava `LocalProtocolError: Illegal header value`. O bloco
`except Exception` em `DeskrioService._get` capturava e logava a exceção,
mas retornava `None` silenciosamente. `listar_conexoes()` recebia `None`
→ retornava `[]` → `status_conexoes()` reportava 0 conexões.

Diagnóstico via endpoint debug temporário (`/api/whatsapp/_debug_connections`)
revelou:

```json
"direct": {
  "error": "Illegal header value b'Bearer eyJ...Fwsc\\n'",
  "error_type": "LocalProtocolError"
}
```

Token tinha 246 caracteres → após `strip()` ficou 245 (newline removido).

## Fix

`backend/app/services/deskrio_service.py`:

```python
@property
def token(self) -> str:
    return os.getenv("DESKRIO_API_TOKEN", "").strip()

@property
def base_url(self) -> str:
    return os.getenv("DESKRIO_API_URL", "").strip().rstrip("/")
```

Commit: `02c61c3` — `fix(deskrio): strip whitespace from DESKRIO_API_TOKEN env var (fixes Illegal header value)`

## Validação

`GET /api/whatsapp/status` agora retorna:

```json
{
  "configurado": true,
  "conexoes": [
    {"id": 4400008, "nome": "Mais Granel 🧡", "status": "CONNECTED", "status_legivel": "conectado"},
    {"id": 64000032, "nome": "Central Vitao 💚", "status": "CONNECTED", "status_legivel": "conectado"},
    {"id": 64000033, "nome": "Daiane Vitao 💜", "status": "INATIVE", "status_legivel": "inativo"}
  ],
  "alguma_conectada": true,
  "total_conexoes": 3
}
```

Critério atendido: `alguma_conectada=true` e `total_conexoes >= 1`.

## Cleanup

- Endpoint debug `/api/whatsapp/_debug_connections` removido (commit cleanup).
- Import `require_admin` removido de `routes_whatsapp.py` (não usado mais).
- Import `typing.Any` removido (não usado mais).

## Lições Aprendidas

1. **Env vars copiadas pra paineis cloud frequentemente trazem `\n` ou espaço**.
   Aplicar `.strip()` em TODA leitura de `os.getenv` para credenciais e URLs
   é defensiva barata.
2. **`except Exception` em `_get/_post` mascara erros de configuração**.
   `logger.exception` ajuda mas Vercel pode não capturar tracebacks. Considerar
   logar `LocalProtocolError` / `InvalidHeader` como WARNING explícito separado
   para ficar evidente em painel de logs.
3. **Endpoint debug temporário admin-only** foi efetivo para isolar a causa
   em <30 minutos sem expor credenciais. Padrão reutilizável.

## SHAs

- Antes: `de9b4c6`
- Debug endpoint v1: `a3f370d`
- Debug endpoint v2 (httpx direto): `7c9a75c`
- Fix: `02c61c3`
- Cleanup: (next commit)
