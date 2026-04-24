# Issue: WhatsApp / Inbox — Integração pendente

**Status:** ABERTO (P3 — feature não-core)  
**Criado:** 2026-04-24

## Contexto

O módulo Inbox/WhatsApp no SaaS está conectado ao backend `routes_whatsapp.py` (prefix `/api/whatsapp`), que por sua vez usa `backend/app/services/deskrio_service.py`. A API Deskrio está funcional para:

- Listar conexões (`/v1/api/connections`) ✅
- Buscar contato por número ou CNPJ ✅
- Enviar mensagem de texto via conexão Mais Granel 🧡 ✅
- Listar tickets por período ✅
- Listar mensagens de um ticket ✅
- Obter conversa completa por CNPJ ✅

O token Deskrio (`.env` local) é válido até ~2026-09-10.

## O que falta

Não é falta de integração — é falta de **fluxo de uso operacional** no frontend:

1. **Webhook de mensagens entrantes:** Deskrio pode enviar webhook em `/v1/api/webhook-message` mas backend não expõe endpoint receiver. Consumo atual é pull-based (consulta tickets/mensagens por demanda do frontend).
2. **Persistência local:** mensagens capturadas diariamente via `scripts/sync_deskrio_to_db.py` populam `log_interacoes` como metadados, mas body das mensagens fica em `data/deskrio/{YYYY-MM-DD}/messages_*.json` — frontend não monta timeline por tickets do banco.
3. **UX Inbox:** página /inbox existe (commit `1353eb2 feat(fullstack): rebuild Inbox as real Deskrio WhatsApp interface`) mas cobertura de cenários (sem contato, conexão desconectada, mensagem com mídia) pode estar incompleta.

## Variáveis de ambiente (Railway — verificar)

```
DESKRIO_API_URL=https://appapi.deskrio.com.br  ✅ funciona
DESKRIO_API_TOKEN=<JWT válido até 2026-09-10>  ✅ em .env local
DESKRIO_COMPANY_ID=38                           ✅
DESKRIO_PROFILE=admin                           ✅
```

Confirmar que Railway tem as mesmas variáveis setadas.

## Próximos passos sugeridos (quando priorizar)

1. **[1-2h] Expor endpoint receiver de webhook** em `routes_whatsapp.py` — recebe POST Deskrio e persiste em `log_interacoes` automaticamente.
2. **[2-4h] Redesenhar Inbox** para consumir tickets diretamente do banco local (populados pelo snapshot diário) em vez de chamar API Deskrio a cada acesso.
3. **[1h] Cobertura de erro** — estado "não configurado" visível quando credenciais ausentes (hoje pode aparecer só como carregando infinito).

## Por que SKIP agora

Decidido pela OPÇÃO C (docs/decisao-arquitetura-2026-04-24.md):
- SaaS é prioridade, mas WhatsApp não é bloqueador de adoção (consultores usam celulares pessoais também)
- Deskrio API funciona ponta-a-ponta para os casos de uso principais (enviar/listar/buscar)
- Captura diária já versionada via `scripts/deskrio_daily_snapshot.py`

**Retomar quando:** usuários reais do CRM (consultores VITAO) reportarem necessidade concreta de Inbox como canal primário de atendimento, OU quando a migração para SaaS puro pedir que todas as interações passem pelo app.
