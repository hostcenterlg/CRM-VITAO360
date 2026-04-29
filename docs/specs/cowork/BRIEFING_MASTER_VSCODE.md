# BRIEFING MASTER — Sequência Completa de Execução
# CRM VITAO360 — VSCode Claude Code

> **Data:** 29/Abr/2026 · **De:** Leandro + Cowork (revisor)
> **Para:** VSCode Claude Code (executor)
> **Status banco:** Neon Launch plan (100GB), sem quota blocker
> **Status deploy:** 11 commits em PROD (Vercel), sidebar reestruturada, deploy OK
> **GitHub Secrets:** DATABASE_URL_NEON ✅ | DESKRIO_API_URL ✅ | DESKRIO_API_TOKEN ✅ | SALES_HUNTER_URL ✅ | SALES_HUNTER_USER ✅ | SALES_HUNTER_PASS ✅

---

## REGRA ZERO — LEIA ANTES DE CODAR

1. **Ler o briefing individual de cada fase INTEIRO antes de começar**
2. **Uma fase por vez** — não pule pra próxima até a atual estar 100% funcional
3. **Testar depois de cada commit** — `npm run build` deve passar, zero erros
4. **Não inventar features** — se não está no briefing, não implementa
5. **Null-safety sweep** — todo `useState(null)` vira `useState([])` ANTES de qualquer feature
6. **SSR obrigatório** — copiar padrão da Carteira/Agenda para auth, NUNCA fetch client-side sem token

---

## FASE 1 — SIDEBAR REESTRUTURADA ✅ JÁ FEITA

> **Commits:** c04e64e, c879f6f, fa3eb86, 03cb6c3, d723d2a
> **Status:** Em produção, validado

Nova sidebar com 7 itens: Inbox → Inteligência IA → Agenda+Tarefas (tabs) → Pedidos → Clientes → Produtos → Manual.
Pipeline e RNC removidos. /clientes é alias de /carteira. Badges dinâmicos.

**Referência:** `BRIEFING_SIDEBAR_REESTRUTURADA.md`

---

## FASE 2 — INBOX DEMO-QUALITY 🔥 PRÓXIMO

> **Briefing completo:** `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md` (530 linhas — LER INTEIRO)
> **Referência visual:** `vitao-demo-mvp-complete.html`
> **Tempo estimado:** 6-8h
> **Prioridade:** MÁXIMA — tela mais usada pelo vendedor

### O que precisa acontecer (resumo — detalhes no briefing):

**Pré-requisitos técnicos (fazer PRIMEIRO):**
1. Null-safety sweep em toda a app
2. Migrar Inbox para SSR (copiar padrão Carteira)
3. Corrigir lógica de conexão Deskrio (`alguma_conectada` em vez de `todas_conectadas`)
4. Criar endpoint backend `GET /api/inbox/conversas` que puxa da Deskrio API

**Layout 3 colunas:**
```
┌─────────────┬──────────────────────────┬───────────────────┐
│  LISTA       │     CHAT                 │  PAINEL LATERAL   │
│  CONVERSAS   │     WhatsApp-like        │  Dados + IA       │
│  (w-80)      │     (flex-1)             │  (w-96)           │
└─────────────┴──────────────────────────┴───────────────────┘
```

**Coluna 1 — Lista de Conversas:**
- Avatar + nome + preview última msg + hora + badge contagem
- Badge temperatura (quente/morno/frio)
- Search bar no topo (filtrar por nome/CNPJ)
- Fonte: `GET /v1/api/tickets` da Deskrio + `GET /v1/api/contact/{number}`

**Coluna 2 — Chat WhatsApp-like:**
- Header: nome cliente + status online + botões Ligar/Ver Pedidos
- Bolhas verdes (enviadas) e brancas (recebidas) com hora
- Input com paperclip (📎 → alert "Em breve") + botão Enviar
- Quick replies: [📋 Catálogo] [💰 Tabela] [🚚 Prazo Entrega]
- Typing indicator (3 dots) — só se Deskrio API suportar
- Fonte: `GET /v1/api/messages/{ticketId}` + `POST /v1/api/messages/send`

**Coluna 3 — Painel Lateral:**
- Placeholder "✨ Inteligência (Em breve)" no topo (bg-gray-100)
- Dados Mercos: ticket médio, ciclo compra, última compra, curva ABC
- Produtos foco (upsell suggestions)
- Tarefas do cliente

**Shell global (se não existe):**
- Header top bar: logo + search central + user info + meta mensal
- Sidebar: usar a nova (Fase 1 já implementou)

**Deskrio API — credenciais:**
- Base URL: `https://appapi.deskrio.com.br/v1/api`
- Auth: Bearer JWT (env `DESKRIO_API_TOKEN`)
- CompanyId: 38
- Endpoints chave:
  - `GET /v1/api/tickets?startDate=DD/MM/YYYY&endDate=DD/MM/YYYY` (max 7 dias)
  - `GET /v1/api/messages/{ticketId}?pageNumber=1`
  - `GET /v1/api/contact/{number}` (dados do contato)
  - `GET /v1/api/connections` (status WhatsApp)
  - `POST /v1/api/messages/send` (enviar msg, multipart/form-data)

**Mobile:** Lista fullscreen → tap → chat fullscreen com botão voltar. Painel = aba/sheet.

### Checklist de entrega Fase 2:
- [ ] Null-safety sweep
- [ ] SSR migrado (sem "Not authenticated")
- [ ] Status Deskrio mostra "conectado" (2 conexões)
- [ ] Lista de conversas com dados reais
- [ ] Chat WhatsApp-like funcional (ler + enviar)
- [ ] Painel lateral com dados Mercos
- [ ] Quick replies funcionais
- [ ] Mobile responsivo
- [ ] `npm run build` sem erros

---

## FASE 3a — DDE ENGINE + MIGRATIONS

> **Briefing:** `SPEC_DDE_CASCATA_REAL.md` (spec da cascata P&L)
> **Engine:** `dde_engine.py` (já corrigido com 3 Golden Master fixes)
> **Migrations:** `DDE_MIGRATION_001.sql` + `DDE_MIGRATION_002_CMV.sql`
> **Endpoints:** `routes_dde.py` (5 rotas FastAPI)
> **Tempo estimado:** 4-6h

### Sequência:

**Passo 1 — Rodar migrations no Neon:**
```sql
-- Conectar via psql ou Neon Console
-- Rodar em ordem:
\i DDE_MIGRATION_001.sql   -- 9 tabelas (frete, rebate, impostos, etc.)
\i DDE_MIGRATION_002_CMV.sql  -- produto_custo_comercial + ALTER vendas/clientes
```

**Passo 2 — Verificar schema:**
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('cliente_frete_mensal', 'cliente_rebate', 'cliente_impostos_estimados',
                    'cliente_dde_resultado', 'dde_anomalia', 'dde_acao', 'dde_score',
                    'dde_comparativo_snapshot', 'produto_custo_comercial');
-- Deve retornar 9 linhas
```

**Passo 3 — Integrar engine no backend:**
- Copiar `dde_engine.py` para `backend/app/services/`
- Copiar `routes_dde.py` para `backend/app/api/`
- Registrar router no `main.py`
- Testar: `GET /api/dde/cliente/{cnpj}?ano=2025`

**Passo 4 — Calibrar com Golden Master:**
- Coelho Diniz CNPJ: verificar que engine retorna valores dentro de 0.5% do GOLDEN_MASTER
- L1 (Receita Bruta), L5 (Receita Líquida), L21 (Margem de Contribuição)

**Arquivos de referência:**
- `SPEC_DDE_CASCATA_REAL.md` — cascata P&L completa (7 blocos, 25 linhas)
- `dde_engine.py` — engine Python com _get_comissao_pct(), _get_cmv(), _get_devolucoes()
- `routes_dde.py` — 5 endpoints FastAPI
- `GOLDEN_MASTER_MAPEAMENTO_COELHO_DINIZ.md` — valores de referência

### Checklist de entrega Fase 3a:
- [ ] 9 tabelas criadas no Neon
- [ ] `dde_engine.py` integrado no backend
- [ ] `routes_dde.py` registrado e respondendo
- [ ] `GET /api/dde/cliente/{cnpj}?ano=2025` retorna JSON com cascata
- [ ] Golden Master Coelho Diniz valida (±0.5%)
- [ ] `comissao_pct` per-client funcional (fallback 3%)
- [ ] CMV calcula quando produto_custo_comercial tem dados, degrada graceful quando não

---

## FASE 3b — ANÁLISE CRÍTICA DO CLIENTE (UI)

> **Spec completa:** `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md`
> **Briefing UI:** `BRIEFING_UI_ABA_ANALISE_CRITICA.md`
> **Depende de:** Fase 3a (DDE engine rodando)
> **Tempo estimado:** 4-6h

### O que construir:

Nova aba "ANÁLISE" na ficha do cliente (`/clientes/[cnpj]`):

```
[DADOS]  [VENDAS]  [CONTATO]  [HISTÓRICO]  [✦ ANÁLISE]
```

**Seção 1 — Header Score + Veredito:**
- Gauge 0-100 com cores (verde/amarelo/vermelho)
- Veredito: SAUDÁVEL / REVISAR / CRÍTICO
- Frase explicativa
- Botões: [↻ Recalcular] e seletor de Ano

**Seção 2 — Cascata P&L:**
- Tabela com 25 linhas da DDE (7 blocos)
- Colunas: Linha | Valor R$ | % Receita | Tier | Fonte
- Cores por tier: REAL (verde), SINTÉTICO (amarelo), PENDENTE (cinza)
- Cada bloco colapsável

**Seção 3 — Anomalias + Ações:**
- Top 3 anomalias detectadas com ícones e impacto R$
- 5 ações priorizadas com impacto estimado
- Checkbox para marcar como "Em andamento"

**Seção 4 — Indicadores (9 KPIs):**
- I1-I9 em cards pequenos (Margem Bruta %, Comissão %, etc.)
- Sinaleiro por indicador (verde/amarelo/vermelho)

**Fonte de dados:** `GET /api/dde/cliente/{cnpj}?ano=2025` (Fase 3a)

### Checklist de entrega Fase 3b:
- [ ] Aba "ANÁLISE" aparece na ficha do cliente
- [ ] Score + veredito renderiza corretamente
- [ ] Cascata P&L mostra 25 linhas com cores por tier
- [ ] Anomalias e ações exibidas
- [ ] 9 KPIs com sinaleiros
- [ ] Seletor de ano funcional
- [ ] Botão recalcular funcional
- [ ] Mobile: seções empilhadas, scrolláveis

---

## RESUMO EXECUTIVO

| Fase | O quê | Briefing | Tempo | Status |
|------|--------|----------|-------|--------|
| 1 | Sidebar reestruturada | `BRIEFING_SIDEBAR_REESTRUTURADA.md` | — | ✅ FEITO |
| 2 | Inbox demo-quality | `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md` | 6-8h | 🔥 PRÓXIMO |
| 3a | DDE engine + migrations | `SPEC_DDE_CASCATA_REAL.md` + migrations | 4-6h | ⏳ |
| 3b | Análise Crítica UI | `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md` | 4-6h | ⏳ |

**Total estimado:** 14-20h de trabalho de executor.

**Ordem:** 2 → 3a → 3b (sequencial, sem pular)

---

## NÃO FAZER (NUNCA)

- ❌ Não inventar features que não estão nos briefings
- ❌ Não usar fetch client-side sem SSR/token
- ❌ Não pular null-safety sweep
- ❌ Não misturar fases — terminar uma antes de começar outra
- ❌ Não commitar com erros de build
- ❌ Não implementar "IA Sugere" com LLM real — é placeholder por enquanto
- ❌ Não deletar Pipeline/RNC do código — só saíram da sidebar
- ❌ Não hardcodar comissão 3% — usar `clientes.comissao_pct` com fallback

---

**Versão:** 1.0 — 29/Abr/2026
**Autor:** Cowork (revisor/professor) + Leandro (owner)
**Validação:** Leandro aprovou sequência e prioridades
