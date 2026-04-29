# BRIEFING: Reconstruir Inbox/Conversas — Seguir o Demo MVP

> **⚠️ SIDEBAR ATUALIZADA:** A sidebar mostrada no layout abaixo (seção "Layout Completo")
> está DESATUALIZADA. Usar a nova sidebar definida em `BRIEFING_SIDEBAR_REESTRUTURADA.md`.
> Nova ordem: Inbox → Inteligência IA → Agenda → Pedidos → Clientes → Produtos → Manual.

> **Data:** 29/Abr/2026 · **Prioridade:** MÁXIMA
> **De:** Leandro (via Cowork)
> **Para:** VSCode Claude Code
> **Referência visual:** `vitao-demo-mvp-complete.html` (copiado na pasta CRM 360)
> **Status atual:** Página /inbox mostra "WhatsApp desconectado" + 0 conversas = INUTILIZÁVEL

---

## OBJETIVO

Reconstruir a página `/inbox` para ser igual ao **Inbox WhatsApp** do demo MVP.
O demo já foi o que Leandro aprovou como visão do produto. O CRM hoje está PIOR que o demo em UX.
Esta é a tela mais usada pelo vendedor — precisa funcionar e parecer profissional.

---

## LAYOUT: 3 COLUNAS (exatamente como o demo)

```
┌─────────────┬──────────────────────────┬───────────────────┐
│  LISTA       │     CHAT                 │  PAINEL LATERAL   │
│  CONVERSAS   │     WhatsApp-like        │  Dados + IA       │
│  (w-80/320px)│     (flex-1)             │  (w-96/384px)     │
│              │                          │                   │
│  avatar      │  header: nome + online   │  Dados Mercos:    │
│  nome        │  + botões Ligar/Pedidos  │  - Ticket médio   │
│  preview msg │                          │  - Ciclo compra   │
│  hora        │  bolhas verdes/brancas   │  - Última compra  │
│  badge temp  │  typing indicator        │  - Curva ABC      │
│  badge count │                          │                   │
│              │  input + enviar          │  Produtos Foco:   │
│              │  quick replies           │  - upsell cards   │
│              │                          │                   │
│              │                          │  Tarefas cliente  │
└─────────────┴──────────────────────────┴───────────────────┘
```

**Mobile:** Lista conversas fullscreen. Ao clicar numa conversa, mostra o chat fullscreen com botão voltar. Painel lateral vira aba ou sheet.

---

## PRÉ-REQUISITOS TÉCNICOS (fazer ANTES do UI)

### Passo 0 — Null-safety sweep (se não feito ainda)
Todos os `useState(null)` trocados por `useState([])`. Sem isso, NADA avança.

### Passo 1 — Migrar para SSR (OBRIGATÓRIO)

O Inbox atual faz fetch client-side e recebe `{"detail":"Not authenticated"}`.
Carteira e Agenda já funcionam com SSR. Copiar o padrão delas:

```tsx
// Usar getServerSideProps ou Server Components com cookies
// NUNCA fetch client-side sem token
export async function getServerSideProps(ctx) {
  const token = ctx.req.cookies['token'] // ou como Carteira faz
  const res = await fetch(`${BACKEND_URL}/api/inbox/conversas`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  const conversas = await res.json()
  return { props: { conversas: conversas ?? [] } }
}
```

### Passo 2 — Corrigir lógica de conexão Deskrio

```python
# backend/app/api/routes_inbox.py (ou onde verifica status)

# ERRADO (atual):
# se QUALQUER conexão != CONNECTED → "desconectado"

# CERTO:
alguma_conectada = any(c['status'] == 'CONNECTED' for c in connections)
if alguma_conectada:
    return {"status": "connected", "connections": [c for c in connections if c['status'] == 'CONNECTED']}
```

Resultado esperado: 2 conexões CONNECTED (Mais Granel + Central Vitao).

### Passo 3 — Criar endpoint backend que alimenta a lista de conversas

O backend precisa de um endpoint que retorne conversas formatadas para o frontend:

```python
# GET /api/inbox/conversas
# Fonte: Deskrio API → GET /v1/api/tickets + GET /v1/api/messages/{ticketId}

@router.get("/api/inbox/conversas")
async def listar_conversas(current_user = Depends(get_current_user)):
    # 1. Buscar tickets abertos da Deskrio
    tickets = await deskrio_client.get_tickets(days=30)
    
    # 2. Para cada ticket, pegar última mensagem e dados do contato
    conversas = []
    for ticket in tickets:
        contato = await deskrio_client.get_contact(ticket['contactId'])
        ultima_msg = await deskrio_client.get_last_message(ticket['id'])
        
        # 3. Cruzar com banco local para enriquecer com dados Mercos
        cliente_db = await db.query(
            "SELECT * FROM clientes WHERE telefone = $1 OR cnpj = $2",
            contato.get('number'), contato.get('cnpj')
        )
        
        conversas.append({
            "id": ticket['id'],
            "nome": contato.get('name', 'Sem nome'),
            "numero": contato.get('number'),
            "ultima_mensagem": ultima_msg.get('body', ''),
            "hora": ultima_msg.get('createdAt'),
            "nao_lidas": ticket.get('unreadMessages', 0),
            "temperatura": cliente_db.get('temperatura', 'morno') if cliente_db else 'novo',
            "curva_abc": cliente_db.get('curva_abc') if cliente_db else None,
            "ticket_medio": cliente_db.get('ticket_medio') if cliente_db else None,
            "ticket_id": ticket['id'],
            "contact_id": contato.get('id'),
            "status": ticket.get('status'),
        })
    
    return sorted(conversas, key=lambda c: c['hora'], reverse=True)
```

### Passo 4 — Endpoint de mensagens de uma conversa

```python
# GET /api/inbox/conversas/{ticket_id}/mensagens
# Fonte: Deskrio API → GET /v1/api/messages/{ticketId}?pageNumber=1

@router.get("/api/inbox/conversas/{ticket_id}/mensagens")
async def mensagens_conversa(ticket_id: int, page: int = 1):
    msgs = await deskrio_client.get_messages(ticket_id, page)
    return [{
        "id": m['id'],
        "body": m['body'],
        "fromMe": m['fromMe'],  # True = enviada, False = recebida
        "timestamp": m['createdAt'],
        "mediaType": m.get('mediaType'),
        "mediaUrl": m.get('mediaUrl'),
    } for m in msgs]
```

### Passo 5 — Endpoint para enviar mensagem

```python
# POST /api/inbox/conversas/{ticket_id}/enviar
# Fonte: Deskrio API → POST /v1/api/messages/send

@router.post("/api/inbox/conversas/{ticket_id}/enviar")
async def enviar_mensagem(ticket_id: int, body: dict):
    result = await deskrio_client.send_message(
        ticket_id=ticket_id,
        message=body['message']
    )
    return result
```

---

## COMPONENTES FRONTEND (copiar padrão visual EXATO do demo)

### Coluna 1 — Lista de Conversas (w-80 = 320px)

```
Para cada conversa:
┌────────────────────────────────────────┐
│ [Avatar 48px]  Nome Fantasia    10:32  │
│                Preview mensag...       │
│                🔥 Quente    [3]        │
└────────────────────────────────────────┘
```

**Specs exatas do demo:**

| Elemento | Valor |
|----------|-------|
| Container | `w-80 bg-white border-r border-gray-200 overflow-y-auto` |
| Header lista | `p-4 border-b bg-gray-50` — "💬 Conversas Ativas" + badge count verde |
| Item conversa | `p-4 hover:bg-gray-50 cursor-pointer` |
| Item selecionado | `bg-green-50 border-l-4 border-vitao-green` |
| Avatar | `w-12 h-12 rounded-full` — cor por temperatura (verde=quente, amarelo=morno, cinza=frio) |
| Nome | `font-semibold text-gray-900 truncate` |
| Preview | `text-sm text-gray-600 truncate` |
| Hora | `text-xs text-gray-500` |
| Badge temperatura | Pill colorida: `🔥 Quente` (bg-green-100 text-green-700), `⚠️ Morno` (bg-yellow-100 text-yellow-700), `❄️ Frio` (bg-gray-100 text-gray-600) |
| Badge não lidas | `bg-vitao-blue text-white text-xs rounded-full font-bold px-2 py-0.5` |

### Coluna 2 — Chat WhatsApp-like (flex-1)

**Header do chat:**
```
[Avatar 40px] Nome Fantasia          [Ligar] [Ver Pedidos]
              ● Online agora
```

| Elemento | Valor |
|----------|-------|
| Container | `bg-white border-b p-4` |
| Avatar | `w-10 h-10 rounded-full bg-vitao-green text-white` |
| Nome | `font-semibold text-gray-900` |
| Status | `text-xs text-green-600` + dot verde 8px |
| Botão Ligar | `px-4 py-2 bg-vitao-blue text-white rounded-lg` |
| Botão Pedidos | `px-4 py-2 bg-vitao-green text-white rounded-lg` |

**Bolhas de mensagem:**

```css
/* Mensagem RECEBIDA (do cliente) */
.chat-bubble-received {
    background: white;
    border-radius: 16px 16px 16px 4px;  /* ponta embaixo-esquerda */
    border: 1px solid #E5E7EB;
    max-width: 28rem;  /* max-w-md */
}

/* Mensagem ENVIADA (pelo vendedor) */
.chat-bubble-sent {
    background: #00A859;  /* verde Vitão */
    color: white;
    border-radius: 16px 16px 4px 16px;  /* ponta embaixo-direita */
    max-width: 28rem;
}
```

| Elemento | Valor |
|----------|-------|
| Área mensagens | `flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50` |
| Bolha recebida | Alinhada à esquerda (`flex justify-start`) |
| Bolha enviada | Alinhada à direita (`flex justify-end`) |
| Texto mensagem | `text-sm` |
| Hora | `text-xs opacity-80 mt-1` (branco em bolha verde, gray-500 em bolha branca) |
| Typing indicator | 3 dots cinza com `animate-pulse` |

**Input e quick replies:**

| Elemento | Valor |
|----------|-------|
| Container input | `bg-white border-t p-4` |
| Input texto | `flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-vitao-green` |
| Botão enviar | `px-6 py-2 gradient-vitao text-white rounded-lg font-medium` |
| Quick replies | 3 pills: `📋 Catálogo`, `💰 Tabela`, `🚚 Prazo Entrega` — `px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full` |

### Coluna 3 — Painel Lateral (w-96 = 384px, `hidden lg:block`)

**Seção 1 — Dados do Cliente (Mercos)**

Título: "📊 Dados do Cliente (Mercos)"

4 rows com fundo colorido claro:

| Dado | Fundo | Cor valor |
|------|-------|-----------|
| Ticket Médio: R$ 12.450 | `bg-blue-50` | `text-vitao-blue font-semibold` |
| Ciclo de Compra: 18 dias | `bg-purple-50` | `text-vitao-purple font-semibold` |
| Última Compra: há 22 dias | `bg-orange-50` | `text-vitao-orange font-semibold` |
| Curva ABC: A | `bg-green-50` | Badge `bg-vitao-green text-white rounded-full` |

**Fonte dos dados:** tabela `clientes` no PostgreSQL — campos `ticket_medio`, `ciclo_medio_dias`, `ultima_compra`, `curva_abc`. Esses dados já existem no banco (vieram do Mercos/Sales Hunter). O endpoint `/api/inbox/conversas` já deve retornar esses campos cruzando telefone/CNPJ do contato Deskrio com a tabela `clientes`.

**Seção 2 — Produtos de Foco (FASE 2 — simplificar agora)**

No demo tem 3 cards de produtos com margem e oportunidade de upsell/cross-sell.
**Para agora:** mostrar os top 3 produtos mais vendidos para o cliente (da tabela `vendas`), com:
- Nome produto
- Quantidade comprada
- Último pedido
- Badge "Recompra próxima" se ciclo_medio_dias ultrapassado

**Fase futura:** IA sugere cross-sell/upsell com margem %.

**Seção 3 — Tarefas do cliente**

Listar tarefas pendentes filtradas pelo cliente selecionado (da tabela `tarefas`):
- Checkbox + título + prazo
- Destaque vermelho se atrasada

---

## CORES OFICIAIS VITÃO (usar em TUDO)

```javascript
// tailwind.config.js — adicionar/confirmar
vitao: {
    green: '#00A859',
    darkgreen: '#008C4A',
    lightgreen: '#E6F7EF',
    blue: '#0066CC',
    purple: '#7C3AED',
    orange: '#F59E0B',
    red: '#EF4444',
}
```

**REGRA:** Toda cor hard-coded genérica no frontend deve migrar para a paleta Vitão. Verde Vitão (#00A859) é a cor primária, não verde genérico do Tailwind.

---

## DESKRIO API — Endpoints para usar

| O que | Endpoint Deskrio | Auth |
|-------|------------------|------|
| Listar tickets (conversas) | `GET /v1/api/tickets?startDate=DD/MM/YYYY&endDate=DD/MM/YYYY` | Bearer JWT |
| Dados do contato | `GET /v1/api/contact/id/{contactId}` | Bearer JWT |
| Mensagens de um ticket | `GET /v1/api/messages/{ticketId}?pageNumber=1` | Bearer JWT |
| Enviar mensagem | `POST /v1/api/messages/send` | Bearer JWT |
| Status conexões | `GET /v1/api/connections` | Bearer JWT |

**Token:** env `DESKRIO_API_TOKEN` (JWT, expira Dez/2026)
**Base URL:** env `DESKRIO_API_URL` = `https://appapi.deskrio.com.br/v1/api`
**CompanyId:** 38

---

## SEQUÊNCIA DE IMPLEMENTAÇÃO

```
Passo 0: Null-safety sweep (se não feito)         [10 min]
Passo 1: SSR auth na página /inbox                 [30 min]
Passo 2: Fix lógica conexão (any CONNECTED)        [10 min]
Passo 3: Backend endpoint /api/inbox/conversas     [1-2h]
Passo 4: Backend endpoint mensagens + enviar       [1h]
Passo 5: Frontend — Coluna 1 (lista conversas)     [1h]
Passo 6: Frontend — Coluna 2 (chat WhatsApp)       [1-2h]
Passo 7: Frontend — Coluna 3 (dados Mercos)        [1h]
Passo 8: Quick replies + typing indicator          [30 min]
Passo 9: Mobile responsivo (lista → chat → voltar) [30 min]
Passo 10: Teste com dados reais Deskrio             [30 min]
```

**Total estimado:** 6-8 horas de dev

---

## O QUE NÃO FAZER

1. **NÃO** inventar dados mock. Usar API Deskrio real + cruzar com banco local.
2. **NÃO** fazer Inbox client-side. SSR obrigatório (como Carteira).
3. **NÃO** implementar "IA Sugere" agora. Painel lateral mostra dados Mercos + produtos + tarefas. IA = fase futura (LLMClient Sprint 4).
4. **NÃO** usar cores genéricas. Paleta Vitão em tudo.
5. **NÃO** esquecer de null-safety: `(conversas ?? []).map(...)`, `(mensagens ?? []).map(...)`.
6. **NÃO** colocar `useState(null)` em NENHUM lugar. Sempre `useState([])` ou `useState('')`.

---

## VALIDAÇÃO FINAL

Após implementar, abrir `/inbox` em produção e confirmar:

- [ ] Status mostra "WhatsApp conectado" (verde)
- [ ] Lista de conversas aparece com dados reais do Deskrio
- [ ] Cada conversa tem avatar + nome + preview + hora + badge temperatura
- [ ] Ao clicar numa conversa, chat abre com bolhas verdes (enviadas) e brancas (recebidas)
- [ ] Painel lateral mostra dados reais do cliente (ticket médio, curva ABC, etc.)
- [ ] Quick replies aparecem abaixo do input
- [ ] Console F12: ZERO erros
- [ ] F5 rápido 10x: NUNCA crash

---

---

## ⚠️ ADDENDUM v2 — DETALHES DO SCREENSHOT DO DEMO (29/Abr, 08:17)

Leandro enviou screenshot do demo rodando. Elementos que o briefing original NÃO cobriu com detalhe suficiente:

### A. SIDEBAR NAVEGAÇÃO (esquerda, w-48/192px, bg-white, border-r)

```
┌──────────────────┐
│ [V] Vitão CRM Hub│  ← Logo verde + "Sistema Unificado"
│     Sistema Unif. │
│                   │
│ 💬 Inbox WhatsApp [3] │  ← Ativo: text-vitao-green, font-semibold, badge verde
│ 📊 Pipeline       │  ← Inativo: text-gray-600
│ 📈 Indicadores    │
│ ✅ Tarefas      [5]│  ← Badge vermelho (pendentes)
│ 👥 Clientes       │
│                   │
│ ┌───────────────┐ │
│ │ Meta Mensal   │ │  ← Widget fixo no bottom da sidebar
│ │ 75%           │ │     text-3xl font-bold text-white
│ │ ████████░░░░  │ │     Progress bar branca sobre fundo verde
│ │ R$187k/R$250k │ │     text-sm text-white/80
│ │ Faltam R$63k  │ │
│ │ 🚀            │ │
│ └───────────────┘ │
└──────────────────┘
```

| Elemento | Spec |
|----------|------|
| Sidebar container | `w-48 bg-white border-r border-gray-200 flex flex-col h-screen` |
| Logo | `p-4 border-b` — ícone verde "V" + "Vitão CRM Hub" bold + "Sistema Unificado" text-xs gray |
| Nav item ativo | `px-4 py-3 text-vitao-green font-semibold bg-green-50 border-r-4 border-vitao-green` |
| Nav item inativo | `px-4 py-3 text-gray-600 hover:bg-gray-50` |
| Badge count (inbox) | `bg-vitao-green text-white text-xs rounded-full px-2 py-0.5 font-bold` |
| Badge count (tarefas) | `bg-red-500 text-white text-xs rounded-full px-2 py-0.5 font-bold` |
| Meta Mensal widget | `m-3 p-4 bg-gradient-to-br from-vitao-green to-vitao-darkgreen rounded-xl text-white` |
| Meta % | `text-3xl font-bold` |
| Progress bar track | `w-full bg-white/30 rounded-full h-2` |
| Progress bar fill | `bg-white rounded-full h-2` width=75% |
| Meta texto | `text-sm text-white/80` — "R$ 187k de R$ 250k" |
| Meta faltam | `text-xs text-white/60` — "Faltam R$ 63k para bater a meta! 🚀" |

**Fonte:** tabela `metas` (se existir) ou `SUM(valor_total) FROM vendas WHERE mês_atual` vs meta definida.

### B. HEADER TOP BAR (fixed, h-16, bg-white, border-b, shadow-sm)

```
[V logo] Vitão CRM Hub          [🔍 Buscar cliente, conversa...]          Helder Dias  [HD]
         Sistema Unificado                                                R$ 187k / R$ 250k (75%)
```

| Elemento | Spec |
|----------|------|
| Container | `h-16 bg-white border-b border-gray-200 shadow-sm flex items-center justify-between px-6` |
| Search bar | `w-96 px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-500 border-none` placeholder="Buscar cliente, conversa..." |
| User info (direita) | Nome do vendedor logado + avatar circular (iniciais) |
| Meta inline | `text-sm text-gray-600` — "R$ 187k / R$ 250k (75%)" ao lado do nome |
| Avatar | `w-10 h-10 rounded-full bg-vitao-green text-white font-bold flex items-center justify-center` |

### C. PAINEL "IA SUGERE" (topo da coluna 3 — FASE 2, mas documentar spec)

**⚠️ NÃO implementar agora** — essa seção usa LLMClient que é Sprint 4+. Mas o VSCode precisa saber o que vem aqui para RESERVAR O ESPAÇO no layout.

```
┌─────────────────────────────────────┐
│ ✨ IA Sugere                        │  ← Header com gradiente roxo→azul
│                                      │
│ ✅ Próxima Ação:                    │  ← Badge verde
│ Ofereça desconto de 8% para 50     │
│ caixas. Cliente está pronto para    │
│ fechar. Envie proposta formal       │
│ até 17h hoje.                       │
│                                      │
│ [    Gerar Proposta Automática    ] │  ← Botão branco com border, text-center
│                                      │
│ 💡 Probabilidade de fechamento: 92% │  ← text-sm text-white/80
└─────────────────────────────────────┘
```

| Elemento | Spec |
|----------|------|
| Container | `bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl p-5 text-white` |
| Título | `font-semibold text-lg` — "✨ IA Sugere" |
| Badge ação | `bg-green-400/20 text-green-200 text-xs rounded px-2 py-1` — "✅ Próxima Ação:" |
| Texto sugestão | `text-sm text-white/90 mt-2 leading-relaxed` |
| Botão proposta | `w-full mt-4 py-2 bg-white/20 border border-white/40 rounded-lg text-white font-medium hover:bg-white/30` |
| Probabilidade | `mt-3 text-sm text-white/70` — "💡 Probabilidade de fechamento: 92%" |

**Para AGORA:** no lugar do "IA Sugere", colocar placeholder:
```
┌─────────────────────────────────────┐
│ ✨ Inteligência (Em breve)          │
│                                      │
│ Sugestões de IA para este cliente   │
│ serão exibidas aqui.                │
│                                      │
│ 📊 Dados do cliente abaixo ↓       │
└─────────────────────────────────────┘
```
Usar `bg-gray-100 rounded-xl p-5 text-gray-500 text-center` — discreto mas marca o espaço.

### D. DETALHE INPUT — ÍCONE ANEXO (paperclip)

No demo, o input de mensagem tem um ícone de clip (📎) à esquerda para anexos:

```
[📎]  [Digite sua mensagem...................................] [Enviar]
      [📋 Catálogo]  [💰 Tabela]  [🚚 Prazo Entrega]
```

| Elemento | Spec |
|----------|------|
| Botão clip | `p-2 text-gray-400 hover:text-gray-600` — ícone Paperclip do Lucide ou 📎 |
| Funcionalidade | Fase 2 — por agora o botão aparece mas abre alert("Em breve: envio de arquivos") |

### E. TYPING INDICATOR (3 dots)

Visível no screenshot — 3 bolinhas cinza com animação pulse:

```html
<div class="flex justify-start">
    <div class="bg-white rounded-2xl px-4 py-3 border border-gray-200">
        <div class="flex space-x-1">
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
        </div>
    </div>
</div>
```

Mostrar quando: último evento do ticket indica que o contato está digitando (se a Deskrio API suportar webhook de typing). Se não suportar, NÃO mostrar — não inventar.

---

## LAYOUT COMPLETO ATUALIZADO (4 áreas, não 3)

```
┌──────────┬───────────┬────────────────────────────┬───────────────────┐
│ SIDEBAR  │  LISTA     │     CHAT                   │  PAINEL LATERAL   │
│ NAV      │  CONVERSAS │     WhatsApp-like           │  IA + Dados       │
│ (w-48)   │  (w-80)    │     (flex-1)                │  (w-96)           │
│          │            │                             │                   │
│ Logo     │  avatar    │  header: nome + online      │  [IA Sugere]      │
│ Inbox [3]│  nome      │  + botões Ligar/Ver Pedidos │  placeholder      │
│ Pipeline │  preview   │                             │                   │
│ Indicad. │  hora      │  bolhas verdes/brancas      │  Dados Mercos:    │
│ Tarefas  │  badge     │  typing indicator           │  - Ticket médio   │
│ Clientes │  temp      │                             │  - Ciclo compra   │
│          │            │  [📎] input + enviar        │  - Última compra  │
│ ┌──────┐ │            │  quick replies              │  - Curva ABC      │
│ │Meta  │ │            │                             │                   │
│ │75%   │ │            │                             │  Produtos Foco    │
│ │R$187k│ │            │                             │                   │
│ └──────┘ │            │                             │  Tarefas cliente  │
└──────────┴───────────┴────────────────────────────┴───────────────────┘
           ↑                                          ↑
           HEADER TOP BAR (fixed, w-full, h-16) — acima de tudo
           [search bar central]  [user info + meta à direita]
```

**IMPORTANTE PARA O VSCODE:** A sidebar nav e o header top bar NÃO são exclusivos do Inbox — são o **shell da aplicação inteira** (todas as páginas). Se o CRM já tem sidebar/header, apenas confirmar que segue essa spec. Se não tem, implementar como layout global (layout.tsx ou similar).

---

**Versão:** 2.0 — 29/Abr/2026 (atualizada com screenshot do demo)
**Referência visual:** `vitao-demo-mvp-complete.html` + screenshot 29/Abr 08:17
**Autor:** Cowork (revisor) + Leandro
