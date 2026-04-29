# MASTER PLAN v3 REFINADO — CRM VITAO360

> **Versão:** 3.0
> **Criado:** 2026-04-29
> **Autor:** @aios-master (orquestrador)
> **Base:** BRIEFING MASTER do Cowork de 29/Abr/2026 + correções factuais identificadas pelo orquestrador
> **Status:** ✅ DESTRAVADO 29/Abr/2026 — Pré-Fase em execução
> **Specs Cowork**: `docs/specs/cowork/` (12 arquivos, commit 36c9fec)
> **SALES_HUNTER_PASS**: configurado 20:18 UTC
> **Fonte CMV**: ZSD062 (SAP) via planilha exportada

---

## REFERÊNCIA RÁPIDA

| Campo | Valor |
|---|---|
| Branch ativa | `master` |
| HEAD remoto | `ebff502` (lint fix) |
| Deploy PROD | ✅ READY (`dpl_DB4AiuqsrBkw...`) |
| Verify.py | 10/10 PASS |
| Sessão atual | 11 commits hoje, todos em PROD |

---

## DELTA vs Briefing Original Cowork

O briefing master original tem mérito mas contém 2 inconsistências factuais e gaps técnicos. Este plano refinado corrige:

| # | Problema no original | Correção neste plano |
|---|---------------------|---------------------|
| 1 | Afirma `SALES_HUNTER_PASS ✅` (mas falta) | Documenta como pré-requisito BLOQUEANTE |
| 2 | Referencia 9 arquivos que não estão no repo | Lista explícita; aguardar Cowork commitar em `docs/specs/cowork/` |
| 3 | Migrations diretas SQL (`\i ARQUIVO.sql`) | Convertidas para 2 migrations Alembic (D3+D4 do Master Plan v1) |
| 4 | Zero menção a testes automatizados | `pytest` obrigatório por fase com casos críticos |
| 5 | Sem gate explícito entre fases | Gate de validação 6-pontos definido abaixo |
| 6 | Bug `venda_itens` duplicadas ignorado | Pré-Fase para corrigir antes da Fase 3a |
| 7 | Fonte de CMV indefinida | Fase 3a.5 explícita para popular `produto_custo_comercial` |
| 8 | Fase 2 monolítica (~6-8h) com pré-reqs pesados | Split 2a (pré-reqs ~3h) + 2b (UI ~5h) |
| 9 | "IA placeholder" risco demo-vazio | Sub-decisão: regra simples (ticket+dias) em vez de placeholder vazio |

---

## SEQUÊNCIA REFINADA

```
Pré-Fase  → fix venda_itens dedup           ~45min
Fase 2a   → Inbox pré-reqs (null/SSR/conn) ~3h
Fase 2b   → Inbox UI 3-col WhatsApp-like   ~5h
GATE 2 ────────────────────────────────────
Fase 3a   → DDE Engine + 2 Alembic migs    ~4-5h
Fase 3a.5 → Popular produto_custo_comercial ~1h
GATE 3a ──────────────────────────────────
Fase 3b   → Aba ANÁLISE em /clientes/[cnpj] ~4-5h
GATE FINAL ───────────────────────────────

Total estimado: 17.5-19.5h
```

---

## PRÉ-FASE — Fix `venda_itens` Duplicadas

**Goal:** Eliminar 2.922 linhas duplicadas detectadas no audit B4 + adicionar UNIQUE constraint para impedir recorrência.

### Pre-conditions
- Working tree limpo
- verify.py 10/10
- Backup: `pg_dump --table=venda_itens` antes da migration

### Tasks
1. **Migration Alembic**: `alembic revision -m "add unique venda_id_produto_id to venda_itens"`
   - `op.create_unique_constraint("uq_venda_item", "venda_itens", ["venda_id", "produto_id"])`
   - Antes de aplicar: dedup script (ver task 2)
2. **Script dedup**: `scripts/dedup_venda_itens.py`
   - Para cada `(venda_id, produto_id)` com `COUNT > 1`: manter `MIN(id)`, deletar resto
   - Logar contagem antes/depois
3. **Test pytest**: `backend/tests/test_venda_itens_uniqueness.py`
   - `SELECT venda_id, produto_id, COUNT(*) FROM venda_itens GROUP BY 1,2 HAVING COUNT(*) > 1` → 0 rows
4. **Atualizar `ingest_sales_hunter.py`**: adicionar `ON CONFLICT (venda_id, produto_id) DO NOTHING` no insert de venda_itens (idempotência defensiva)

### Gate Pré-Fase
- [ ] Alembic upgrade head + downgrade -1 + upgrade head reaplica sem erro
- [ ] Script dedup retorna 0 duplicatas após execução
- [ ] pytest passa
- [ ] verify.py 10/10
- [ ] Commit atômico: `fix(venda_itens): dedup + add UNIQUE constraint (venda_id, produto_id)`

**Agente designado:** `@data-engineer` (deep-executor sonnet)

---

## FASE 2a — Inbox Pré-Requisitos

**Goal:** Estado técnico saudável antes de tocar UI do Inbox.

### Pre-conditions
- Pré-Fase completa
- 9 arquivos do Cowork em `docs/specs/cowork/` (em especial `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md`)

### Tasks
1. **Null-safety sweep escopado** (não "toda a app" — só rotas críticas):
   - `inbox/page.tsx`, `agenda/page.tsx`, `carteira/page.tsx`, `pedidos/page.tsx`, homepage `page.tsx`, `pipeline/page.tsx`
   - Padrão: `useState<X | null>(null)` → `useState<X>(<empty>)` quando `<empty>` é seguro; senão guardar com `?.` em todos consumidores
   - Verificação: `npm run build` + smoke navegação manual
2. **SSR migration Inbox** — copiar padrão de `carteira/page.tsx` (server component que fetch com cookie/token e passa props para client)
   - Eliminar `"Not authenticated"` em primeira renderização
3. **Fix lógica conexão Deskrio**: `alguma_conectada` em vez de `todas_conectadas` (já há precedente em `INBOX_INCIDENT_29ABR_RESOLUTION.md`)
4. **Endpoint backend** `GET /api/inbox/conversas`:
   - Cabeçalho `Authorization: Bearer ${DESKRIO_API_TOKEN}` server-side
   - Query: `?startDate=DD/MM/YYYY&endDate=DD/MM/YYYY` (clamp 7 dias)
   - Response normalizada: `{ conversas: [...], total: int, has_more: bool }`
   - pytest cobertura: schema response + erro 401 quando token inválido

### Gate Fase 2a
- [ ] `npm run build` 0 erros
- [ ] `pytest backend/tests/test_inbox*.py` 100% PASS
- [ ] verify.py 10/10
- [ ] Smoke PROD: `/inbox` retorna 200 sem erro de auth
- [ ] 4 commits atômicos

**Agente designado:** `@dev` (executor sonnet) com auxílio `@data-engineer` para endpoint

---

## FASE 2b — Inbox UI WhatsApp-like

**Goal:** Layout 3 colunas demo-quality conforme briefing Cowork (a ser fornecido).

### Pre-conditions
- Fase 2a completa
- Briefing `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md` (530 linhas) lido e disponível

### Decisão sobre "IA placeholder"
**NÃO** mostrar bloco vazio "✨ Inteligência (Em breve)". Em vez disso, exibir **uma sugestão concreta** baseada em regra determinística:
- Se `dias_sem_compra > ciclo_medio + 30` → "Cliente em RECUPERAÇÃO. Sugira reativação com promoção produto curva A."
- Se `temperatura == 'QUENTE' && tempo_resposta_media < 1h` → "Cliente engajado. Sugira upsell ticket+20%."
- Etc. Lista de 5-7 regras simples cobrindo casos comuns.

Isso evita "demo-vazio" e usa dados Mercos que **já existem**.

### Tasks (alto-nível — detalhamento depende do briefing 530 linhas)
1. Layout 3 colunas (Lista | Chat | Painel) responsivo
2. Lista conversas com search, badges
3. Chat WhatsApp-like (bolhas, timestamps, scroll)
4. Input com paperclip (upload mock), botão enviar (POST `/v1/api/messages/send`)
5. Quick replies funcionais (templates: catálogo, tabela, prazo)
6. Painel lateral: dados Mercos + sugestão IA (regra)
7. Mobile: lista→chat fullscreen com voltar; painel = sheet bottom

### Gate Fase 2b (= Gate 2)
- [ ] `npm run build` 0 erros
- [ ] `pytest backend/tests/test_inbox*.py` 100% PASS
- [ ] verify.py 10/10
- [ ] Smoke PROD: enviar mensagem real funciona; receber lista conversas funciona
- [ ] Mobile (tela <768px): UX testado em DevTools
- [ ] Validação visual contra `vitao-demo-mvp-complete.html`
- [ ] Commits atômicos múltiplos (1 por seção)

**Agente designado:** Squad `@ux` + `@dev` (deep-executor opus para coordenar)

---

## FASE 3a — DDE Engine + Migrations Alembic

**Goal:** Cascata P&L por cliente operacional via endpoint `/api/dde/cliente/{cnpj}?ano=2025`.

### Pre-conditions
- Gate 2 passa
- 2 arquivos `dde_engine.py` + `routes_dde.py` fornecidos pelo Cowork
- Spec `SPEC_DDE_CASCATA_REAL.md` em `docs/specs/cowork/`
- Golden Master Coelho Diniz disponível

### Tasks
1. **Migration Alembic 1** (substitui `DDE_MIGRATION_001.sql`):
   - 8 tabelas: `cliente_frete_mensal`, `cliente_rebate`, `cliente_impostos_estimados`, `cliente_dde_resultado`, `dde_anomalia`, `dde_acao`, `dde_score`, `dde_comparativo_snapshot`
   - Convertido linha-a-linha do SQL para `op.create_table(...)` Alembic
   - Rollback testado: `alembic downgrade -1` derruba as 8 tabelas
2. **Migration Alembic 2** (substitui `DDE_MIGRATION_002_CMV.sql`):
   - 1 tabela: `produto_custo_comercial`
   - ALTER `vendas` (colunas extras conforme spec)
   - ALTER `clientes` (colunas extras conforme spec)
3. **Integrar engine**:
   - `backend/app/services/dde_engine.py` (cópia do Cowork)
   - `backend/app/api/routes_dde.py` (cópia do Cowork)
   - Registrar router em `backend/app/main.py`
4. **Pytest com Golden Master**:
   - `backend/tests/test_dde_golden_master.py`
   - Asserts L1 (Receita Bruta), L5 (Receita Líquida), L21 (Margem Contribuição) ±0.5% vs valores Coelho Diniz documentados
5. **Validação manual em PROD**:
   - `curl /api/dde/cliente/<cnpj_coelho>?ano=2025` retorna JSON cascata 25 linhas

### Gate Fase 3a
- [ ] Alembic upgrade head + downgrade -1 + upgrade head sem erro
- [ ] Endpoint `/api/dde/cliente/{cnpj}` retorna 200 com JSON válido
- [ ] Golden Master Coelho Diniz dentro de ±0.5% (3 linhas-chave)
- [ ] Comissão `clientes.comissao_pct` com fallback 3% funcional
- [ ] pytest 100% PASS
- [ ] verify.py 10/10 + novo check `[11] DDE engine integrity`
- [ ] 3+ commits atômicos

**Agente designado:** `@data-engineer` deep-executor opus

---

## FASE 3a.5 — Popular `produto_custo_comercial`

**Goal:** CMV deixar de ser "PENDENTE" no Score → veredito mais preciso.

### Pre-conditions
- Fase 3a completa (tabela existe)
- **Decisão L3 do Leandro**: qual a fonte de dados de custo? (planilha SAP? Sales Hunter? planilha manual?)

### Tasks
1. Identificar fonte de dados de custo comercial por SKU
2. Script `scripts/import_produto_custo.py` lendo a fonte e populando a tabela
3. Tier classification: REAL / SINTÉTICO / ALUCINAÇÃO
4. pytest: ≥80% dos SKUs ativos da CARTEIRA têm registro REAL ou SINTÉTICO

### Gate Fase 3a.5
- [ ] `SELECT COUNT(*) FROM produto_custo_comercial WHERE classificacao_3tier IN ('REAL','SINTETICO')` ≥ 80% dos SKUs ativos
- [ ] Endpoint `/api/dde/cliente/<x>` retorna CMV calculado (não "PENDENTE") para clientes com produtos cobertos
- [ ] verify.py 10/10
- [ ] 1 commit atômico

**Agente designado:** `@data-engineer` (executor sonnet)

---

## FASE 3b — Análise Crítica UI

**Goal:** Aba "ANÁLISE" na ficha do cliente com 4 seções (Score, Cascata, Anomalias, KPIs).

### Pre-conditions
- Gate 3a passa (incluindo 3a.5)
- Brief `BRIEFING_UI_ABA_ANALISE_CRITICA.md` + `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md` lidos

### Tasks (alto-nível)
1. Adicionar tab "ANÁLISE" em `/clientes/[cnpj]/page.tsx`
2. Componente `<ScoreGauge />` (0-100, cor por faixa)
3. Componente `<CascataPL />` (25 linhas em 7 blocos colapsáveis, cores por tier)
4. Componente `<AnomaliasAcoes />` (top 3 anomalias + 5 ações)
5. Componente `<KPICards />` (9 indicadores com sinaleiros)
6. Seletor de ano + botão Recalcular
7. Mobile: seções empilhadas

### Gate Fase 3b (= Gate Final)
- [ ] `npm run build` 0 erros
- [ ] pytest 100% PASS (frontend smoke + backend)
- [ ] verify.py 10/10
- [ ] Smoke PROD: rota `/clientes/<cnpj_coelho>` exibe aba ANÁLISE com cascata real
- [ ] Mobile: 4 seções scrolláveis e legíveis
- [ ] Acessibilidade: touch targets ≥44px, contraste OK
- [ ] Commits atômicos

**Agente designado:** Squad `@ux` + `@dev`

---

## GATE PADRÃO (aplicado entre TODAS as fases)

Antes de declarar "fase X completa", os 6 critérios abaixo DEVEM passar:

```
1. npm run build                       → 0 erros
2. pytest backend/tests/                → 100% PASS
3. python scripts/verify.py --all       → 10/10 PASS
4. Smoke PROD: rotas críticas 2xx       → 200/307/308 OK
5. Commit hash em master remoto         → git log origin/master::HEAD == empty
6. Vercel deploy READY (não ERROR)      → API check
```

Sem 6/6 = não é "done". Detector de Mentira N1+N2+N3 aplicado.

---

## PRÉ-REQUISITOS DO LEANDRO (BLOQUEIA INÍCIO)

| # | Item | Como | Estimativa |
|---|------|------|-----------|
| 1 | Fornecer 9 arquivos Cowork em `docs/specs/cowork/` | Colar conteúdo aqui ou commit direto | 15min |
| 2 | Configurar `SALES_HUNTER_PASS` | `gh secret set SALES_HUNTER_PASS -R hostcenterlg/CRM-VITAO360` | 1min |
| 3 | Decidir fonte de dados de custo (Fase 3a.5) | Responder no chat ou criar nota | 5min |

**Os 9 arquivos:**
1. `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md` (530 linhas)
2. `BRIEFING_SIDEBAR_REESTRUTURADA.md` (referência histórica)
3. `BRIEFING_UI_ABA_ANALISE_CRITICA.md`
4. `SPEC_DDE_CASCATA_REAL.md`
5. `GOLDEN_MASTER_MAPEAMENTO_COELHO_DINIZ.md`
6. `dde_engine.py`
7. `routes_dde.py`
8. `DDE_MIGRATION_001.sql` + `DDE_MIGRATION_002_CMV.sql` (vou converter para Alembic)
9. `vitao-demo-mvp-complete.html` (referência visual Inbox)

---

## NÃO FAZER (CONSOLIDADO)

- ❌ Aplicar migrations SQL diretas (usar Alembic — D3/D4)
- ❌ Pular gate entre fases
- ❌ Implementar IA com LLM real na Fase 2 (regra simples, sim)
- ❌ Deletar código de Pipeline/RNC (só removidos da nav)
- ❌ Inventar features além dos briefings
- ❌ `git push` por agente que não seja `@devops` (R11)
- ❌ Misturar VENDA com LOG (R4 Two-Base)
- ❌ CNPJ como float (R5 string 14d)
- ❌ Fórmulas openpyxl em português (R7 inglês)
- ❌ Misturar fases — completar gate antes de avançar

---

*Documento mantido pelo @aios-master. Atualizar a cada gate completo.*
