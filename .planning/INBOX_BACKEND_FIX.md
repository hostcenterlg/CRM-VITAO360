# INBOX_BACKEND_FIX — Fix 3 Bugs Deskrio Inbox

**Data:** 2026-04-29
**Autor:** @data-engineer
**Status:** APLICADO — commit pendente

---

## Antes / Depois

### Bug 1 — "WhatsApp Deskrio offline" falso

| | Antes | Depois |
|---|---|---|
| **Arquivo** | `backend/app/services/deskrio_service.py` | idem |
| **Função** | `listar_conexoes()` | idem |
| **Causa raiz** | `listar_conexoes()` procurava envelope keys `data, connections, items, results` mas a API Deskrio retorna `{"whatsappConnections": [...], "whatsappApiConnections": [...], "metaConnections": [...]}` — nenhuma chave batia, lista retornava `[]` | Adicionada `"whatsappConnections"` como primeira chave no loop de envelope |
| **Efeito** | `alguma_conectada=False` mesmo com 2/3 conexões CONNECTED | `alguma_conectada=True` quando >= 1 CONNECTED |
| **Smoke test** | `conexoes=[]`, `alguma_conectada=False` | `conexoes=3`, `alguma_conectada=True` |

Adicionado também `INATIVE` e `INACTIVE` ao mapa `_STATUS_LEGIVEL` — status real observado na API para conexão sem número ativo (Daiane Vitao).

---

### Bug 2+3 — Zero conversas / "Sem tickets nos últimos 7 dias"

| | Antes | Depois |
|---|---|---|
| **Arquivo** | `backend/app/services/deskrio_service.py` | idem |
| **Função** | `listar_tickets()` | idem |
| **Causa raiz** | `get_inbox` chama `listar_tickets(hoje-7, hoje)` = range de 7 dias. A API Deskrio retorna HTTP 400 `ERR_DATE_LIMIT_OFF_1_WEEK` para qualquer range >= 7 dias. `_get()` captura o 400 como erro não retryable e retorna `None`. `listar_tickets` recebia `None` e retornava `[]`. | Auto-truncagem: se `(data_fim - data_inicio).days > 6`, trunca `data_inicio = data_fim - 6 dias`. Log estruturado quando retorna `None` ou `dict` inesperado. |
| **Efeito** | Inbox sempre vazia | 53 tickets retornados no smoke test com dados reais |

---

## Como rodar smoke test

```bash
# 1. Certifique-se que .env tem DESKRIO_API_TOKEN e DESKRIO_API_URL
cd /path/to/CRM-VITAO360

# 2. Teste conexões (Bug 1)
python -c "
import os; os.environ.setdefault('DATABASE_URL','sqlite:///tmp.db')
from backend.app.services.deskrio_service import deskrio_service
s = deskrio_service.status_conexoes()
print('configurado:', s['configurado'])
print('alguma_conectada:', s['alguma_conectada'])
print('total:', s['total_conexoes'])
for c in s['conexoes']:
    print(' ', c['nome'], '|', c['status'], '|', c['status_legivel'])
"

# 3. Teste tickets (Bug 2+3)
python -c "
import os; os.environ.setdefault('DATABASE_URL','sqlite:///tmp.db')
from backend.app.services.deskrio_service import deskrio_service
from datetime import date, timedelta
hoje = date.today()
tickets = deskrio_service.listar_tickets((hoje-timedelta(days=7)).isoformat(), hoje.isoformat())
print('tickets count:', len(tickets))
"

# 4. Testes unitários (mock — sem chamada real)
python -m pytest backend/tests/test_deskrio_inbox.py -v
```

Resultado esperado:
- `alguma_conectada: True` (Mais Granel + Central Vitao CONNECTED)
- `tickets count: ~50` (últimos 6 dias)
- `15 passed` nos testes unitários

---

## Variáveis de ambiente necessárias (Vercel backend)

| Variável | Valor | Status |
|---|---|---|
| `DESKRIO_API_TOKEN` | JWT Bearer (exp 2026-12-11) | Configurado na Vercel |
| `DESKRIO_API_URL` | `https://appapi.deskrio.com.br` | Configurado na Vercel |
| `DESKRIO_COMPANY_ID` | `38` | Configurado no .env |

**NOTA:** `config.py` declara `deskrio_api_key` e `deskrio_base_url` mas o `deskrio_service.py` lê `DESKRIO_API_TOKEN` e `DESKRIO_API_URL` diretamente via `os.getenv()` — não há conflito, mas o `config.py` pode ser atualizado em refactor futuro (L2).

---

## Limites de rate Deskrio

| Endpoint | Limite confirmado |
|---|---|
| `GET /v1/api/tickets` | Range máximo **6 dias** (retorna 400 com range >= 7 dias) |
| `GET /v1/api/connections` | Sem limite identificado |
| `GET /v1/api/messages/{ticketId}` | Sem limite identificado |

---

## Decisão: SSR não migrada

Conforme R103 da sessão 29/Abr/2026: **NUNCA migrar /inbox para SSR**.
A página já usa `'use client'` + `useAuth()` + guard `if (authLoading || !user) return`.
O token está em `localStorage` e é injetado corretamente após auth resolver.
O 401 reportado no briefing era sintoma da inbox vazia (sem dados), não de token ausente.

---

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `backend/app/services/deskrio_service.py` | Fix `listar_conexoes()` + `listar_tickets()` + `_STATUS_LEGIVEL` |
| `backend/tests/test_deskrio_inbox.py` | 15 testes unitários novos (CRIADO) |
| `.planning/INBOX_BACKEND_FIX.md` | Esta documentação (CRIADO) |
