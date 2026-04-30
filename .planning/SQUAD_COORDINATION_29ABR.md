# Squad Coordination — 29/Abr/2026

> **Orquestrador:** @aios-master
> **Objetivo:** Manter múltiplos squads trabalhando em paralelo SEM conflito de merge.
> **Princípio:** cada squad tem **arquivos exclusivos**. Se precisar tocar fora da lista, escala ao orquestrador.

---

## SQUADS ATIVOS

### 🟢 SQUAD ALPHA — Visual UX Audit (read-only)
- **Status:** running
- **Tipo:** gsd-ui-auditor
- **Goal:** Auditoria 6-pillar de TODAS as páginas frontend; lista priorizada de problemas (tipografia, contraste, spacing, hierarquia, mobile, acessibilidade)
- **Arquivos exclusivos (write):**
  - `.planning/AUDIT_VISUAL_29ABR.md`
- **Arquivos read-only (toda a app):** sim, lê tudo — só não modifica código
- **ETA:** ~1h
- **Output esperado:** matriz de problemas → tickets para SQUAD DELTA + Wave 2

### 🟢 SQUAD BRAVO — RBAC / Níveis de Acesso
- **Status:** running
- **Tipo:** deep-executor (opus → sonnet por modelo do agent)
- **Goal:** Implementar 4 roles (ADMIN, GERENTE, CONSULTOR, VENDEDOR) com decoradores de endpoint, RoleGuard frontend, AuthContext expandido, e migration Alembic.
- **Arquivos exclusivos (write):**
  - `backend/app/security.py`
  - `backend/app/models/usuario.py` (campo `role` se ausente)
  - `backend/app/auth.py` (se existir)
  - `backend/app/api/dependencies.py` (novo se ausente, com `require_role(...)` decorators)
  - `backend/alembic/versions/*_rbac_*.py` (nova migration se necessária)
  - `backend/tests/test_rbac.py` (novo)
  - `frontend/src/contexts/AuthContext.tsx`
  - `frontend/src/components/auth/RoleGuard.tsx` (novo)
  - `frontend/src/components/auth/RequireRole.tsx` (novo)
  - `frontend/src/lib/permissions.ts` (novo)
- **Arquivos read-only:** `backend/app/api/routes_*.py` (somente para mapear endpoints e ver dependencies atuais; mudanças serão coordenadas em Wave 2 ou em squad subsequente)
- **NÃO TOCA:** tailwind, design tokens, filtros de cliente, layout das páginas
- **ETA:** ~3h

### 🟢 SQUAD CHARLIE — Filtros Canal/Food
- **Status:** running
- **Tipo:** executor (sonnet)
- **Goal:** Corrigir filtro `canal=Food` (e demais canais) para retornar clientes corretos. Investigar quebra reportada por Leandro: ao filtrar "Food", lista vem vazia mesmo havendo clientes do canal Food.
- **Arquivos exclusivos (write):**
  - `backend/app/api/routes_clientes.py` (lógica de filtro)
  - `backend/app/services/cliente_service.py` (se existir, ou função interna de filtro)
  - `backend/app/api/routes_canais.py` (se relevante para listagem de canais)
  - `frontend/src/lib/api.ts` (apenas tipos e params do filter — não tocar funções de outros squads)
  - `backend/tests/test_filtro_canal.py` (novo)
- **Arquivos parciais (apenas lógica, NÃO visual):**
  - `frontend/src/app/carteira/page.tsx` (state de filtro + chamada API; não tocar markup/classes)
- **NÃO TOCA:** RBAC, design tokens, header global
- **ETA:** ~2h

### 🟢 SQUAD DELTA — Design System Tokens
- **Status:** running
- **Tipo:** ui-designer
- **Goal:** Estabelecer base de tipografia (fontes proporcionais), paleta densa (não só cores claras), spacing tokens, contraste WCAG AA. Preparar a base; aplicação nas páginas vira Wave 2.
- **Arquivos exclusivos (write):**
  - `frontend/tailwind.config.ts` (extend tokens — preservar `vitao` palette existente)
  - `frontend/src/app/globals.css` (CSS variables)
  - `frontend/src/styles/tokens.ts` (novo — TS exports dos tokens)
  - `frontend/src/components/ui/typography/Heading.tsx` (novo)
  - `frontend/src/components/ui/typography/Text.tsx` (novo)
  - `frontend/src/components/ui/typography/index.ts` (novo barrel)
  - `frontend/src/components/ui/index.ts` (apenas adicionar export do typography barrel — coordenar via merge final)
- **NÃO TOCA:** páginas, lógica, RBAC, filtros
- **ETA:** ~2h

---

## REGRAS DE OURO

1. **Cada squad só mexe nos arquivos da SUA lista.** Se precisar de outro arquivo, PARE e escale ao orquestrador.
2. **Commit atômico R11** com prefixo do squad: `[ALPHA] ...`, `[BRAVO] feat(rbac): ...`, etc.
3. **NUNCA `git push`** — só orquestrador faz, ao final de cada wave.
4. **NUNCA `git pull`** — squads trabalham no estado em que receberam o repo. Conflitos são resolvidos pelo orquestrador.
5. **TSC + verify.py** após cada commit do squad. Se falhar, squad PARA e reporta.
6. **Mensagens de commit em inglês**, R11 atômicos.
7. **Pré-commit hook** roda automaticamente. Se falhar, **NÃO use `--no-verify`** — corrija o problema.
8. **Detector de Mentira N1+N2+N3** antes de declarar tarefa concluída (existência → substância → conexão).

## REGRAS PARA SQUADS FUTUROS (ECHO, FOXTROT, ...)

Quando o Leandro mandar nova demanda enquanto squads atuais ainda rodam:
1. Orquestrador atualiza este doc adicionando o novo squad antes de despachar.
2. Verificar lista de arquivos exclusivos contra squads ativos. Conflito = ajustar antes de despachar.
3. Se conflito for inevitável, novo squad espera o squad concorrente terminar.
4. Manter naming OTAN: ALPHA, BRAVO, CHARLIE, DELTA, ECHO, FOXTROT, GOLF, HOTEL, ...

## STATUS POR WAVE

### WAVE 1 — Audit + Foundation ✅ CONCLUÍDA (29/Abr 21:10 UTC)
- ALPHA ✅ — 47 issues priorizadas em `.planning/AUDIT_VISUAL_29ABR.md`
- BRAVO ✅ — RBAC + migration + 26 pytest
- CHARLIE ✅ — bug Food (0→29 clientes)
- DELTA ✅ — design tokens + Inter + typography
- Push: `127d450..b6887eb` (14 commits) — Vercel READY

### WAVE 2 — Application ✅ CONCLUÍDA (29/Abr 21:30 UTC)
- ECHO ✅ — 3 commits (FollowUpBadge, AcaoPrescrita, IA contrast)
- FOXTROT ✅ — 4 commits (Sidebar useRoleGuard + RequireRole em 10 páginas)
- + 4 commits paralelos do Leandro [WAVE2] (Badge, StatusPill, meta R8, sub-12px sweep 48 arquivos)
- Push: `b6887eb..079951e` (12 commits) — Vercel READY

### WAVE 3 — P1 Sweep + DDE/Análise Fix + Inbox Real (rodando)

#### 🏌️ SQUAD GOLF — P1 Visual Sweep (resíduos do audit)
- **Tipo:** ui-designer (sonnet)
- **Goal:** Resolver 11 P1 restantes do audit (verde duplicado, Kanban mobile, dashboard tabs, loading states, pedidos cores hardcoded, emoji vs SVG, skeleton, avatar 10px, breadcrumb, sidebar width mobile)
- **Arquivos exclusivos (write):**
  - `frontend/src/components/AppShell.tsx`
  - `frontend/src/components/Sidebar.tsx` (width mobile, group labels, footer — NÃO mexer em useRoleGuard que FOXTROT colocou)
  - `frontend/src/components/ClienteTable.tsx`
  - `frontend/src/components/ClienteDetalhe.tsx`
  - `frontend/src/components/ClienteModal.tsx`
  - `frontend/src/components/ui/*` (refinos pontuais — verde duplicado)
  - `frontend/src/app/page.tsx` (dashboard tabs truncadas)
  - `frontend/src/app/carteira/page.tsx`
  - `frontend/src/app/agenda/page.tsx` (tag amarelo puro, idx)
  - `frontend/src/app/pedidos/page.tsx` (STATUS_CONFIG → tokens)
  - `frontend/src/app/produtos/page.tsx` (BadgeAtivo + Skeleton)
  - `frontend/src/app/pipeline/page.tsx` (Kanban mobile scroll)
  - `frontend/src/app/manual/page.tsx`
  - `frontend/src/app/atualizacoes/page.tsx`
- **NÃO TOCA:** `/inbox/*` (INDIA), `/gestao/*` (HOTEL), `/admin/*`, `/redes`, `/sinaleiro`, `/relatorios`, backend, tailwind/tokens
- **ETA:** ~3-4h

#### 🚨 REGRA DE NEGÓCIO CRÍTICA PARA HOTEL (adicionada 29/Abr 21:50)

**DDE/Análise Crítica NÃO se aplica a todos os clientes.** Confirmado por Leandro:

- ✅ **Aplicável**: canal **Direto**, **Indireto**, **Food Service** (com dados estruturados)
- ❌ **NÃO aplicável**: **Varejo**, **PME**, **Interno** (sem contrato, sem verba, sem frete dedicado)

**Por quê:** R8 zero alucinação. Calcular cascata P&L para cliente sem contrato/verba/promotor seria forçar dados inexistentes (foi o erro do ChatGPT que inflou faturamento 742%).

**Como aplicar na reformulação:**
- Banner de preview já planejado deve incluir nota "**DDE aplicável apenas a clientes com contrato estruturado** (Direto/Indireto/Food Service)"
- Se a UI tem dropdown ou seletor de cliente, **filtrar canais aplicáveis**
- Em `analise-critica/page.tsx`, preparar fallback "Análise Crítica não aplicável a clientes do canal X" (mock pode mostrar isso para um exemplo de varejo)

Memória completa: `memory/project_dde_aplicabilidade_canais.md`

#### 🏨 SQUAD HOTEL — DDE + Análise Crítica fix
- **Tipo:** deep-executor (sonnet)
- **Goal:** Reformular `/gestao/dde` e `/gestao/analise-critica` (Leandro chamou de "péssimos"). Alinhar com `docs/specs/cowork/SPEC_DDE_CASCATA_REAL.md`, `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md`, `BRIEFING_UI_ABA_ANALISE_CRITICA.md`. **Preservar `RequireRole(GERENTE)` que FOXTROT envolveu.**
- **Arquivos exclusivos (write):**
  - `frontend/src/app/gestao/dde/page.tsx`
  - `frontend/src/app/gestao/analise-critica/page.tsx`
  - `frontend/src/app/gestao/_components/*` (novo — componentes locais se ajudar)
- **Pode READ:** `docs/specs/cowork/*` (SPEC_DDE_CASCATA_REAL, BRIEFING_UI_ABA_ANALISE_CRITICA, dde_engine.py, GOLDEN_MASTER_REFERENCIA.md)
- **NÃO TOCA:** Componentes globais (criar novos em /gestao/_components/), backend, RequireRole wrapper (preservar do FOXTROT)
- **ETA:** ~3-4h

#### 🔥 SQUAD KILO — DDE/Análise REBUILD honesto (delete+recreate)
- **Tipo:** deep-executor (sonnet)
- **Goal:** **DELETAR** as 2 pages do HOTEL e **RECRIAR** seguindo `docs/specs/cowork/BRIEFING_REBUILD_DDE_ANALISE_CRITICA.md`. Filosofia: zero R$, zero CNPJ/nomes, zero mockups. Páginas EXPLICATIVAS sobre o que a feature É e o que vai aparecer.
- **Arquivos exclusivos (write):**
  - `frontend/src/app/gestao/dde/page.tsx` (DELETE + RECREATE)
  - `frontend/src/app/gestao/dde/layout.tsx` (manter ou ajustar)
  - `frontend/src/app/gestao/analise-critica/page.tsx` (DELETE + RECREATE)
  - `frontend/src/app/gestao/analise-critica/layout.tsx`
  - `frontend/src/app/gestao/_components/*` (deletar componentes do HOTEL não usados na nova abordagem)
- **NÃO TOCA:** Sidebar (mantém links + badges), backend, outras páginas
- **Preserva:** `<RequireRole minRole="GERENTE">` wrapper + badges "EM CONSTRUÇÃO"/"BLOQUEADO" na sidebar
- **Embute regra de canais**: páginas devem mencionar que feature atende Direto/Indireto/Food Service apenas
- **ETA:** ~3-4h

### 🌊 ONDAS DE IMPLEMENTAÇÃO DDE/AC (sequencial cronológica)

> **Spec**: `docs/specs/cowork/README_TIME_TECNICO_DDE_AC.md`
> **Filosofia**: cada onda depende da anterior. Notification automática encadeia.

#### 🅼 SQUAD MIKE — Onda 1: Schema PostgreSQL + Migration
- **Tipo:** deep-executor (sonnet)
- **Goal:** Criar 4 tabelas (cliente_frete_mensal, cliente_verba_anual, cliente_promotor_mensal, cliente_dre_periodo) + ALTERs em clientes/vendas (D1) via Alembic; criar 4 modelos SQLAlchemy; atualizar `ingest_sales_hunter.py` para persistir 4 campos D1
- **Arquivos exclusivos:**
  - `backend/alembic/versions/<auto>_add_dde_tables.py` (NOVO)
  - `backend/app/models/cliente_frete.py` (NOVO)
  - `backend/app/models/cliente_verba.py` (NOVO)
  - `backend/app/models/cliente_promotor.py` (NOVO)
  - `backend/app/models/cliente_dre.py` (NOVO)
  - `backend/app/models/__init__.py` (registrar novos)
  - `backend/app/models/cliente.py` (ALTER colunas D1)
  - `backend/app/models/venda.py` (ALTER colunas D1)
  - `scripts/ingest_sales_hunter.py` (persistir 4 campos)
  - `backend/tests/test_dde_schema.py` (NOVO)
- **NÃO TOCA:** /gestao (KILO), /inbox (LIMA), /admin, frontend, tailwind
- **Dispara em PARALELO** com KILO/LIMA (sem conflito — backend exclusivo)
- **ETA:** ~2-3h

#### 🅽 SQUAD NOVEMBER — Onda 2: Parsers + 22 regex DRE
- **Tipo:** deep-executor (sonnet)
- **Goal:** BaseParser + 5 parsers específicos + 22 regex DRE + endpoint upload + testes com fixtures
- **Pré-requisito:** MIKE concluído (modelos disponíveis)
- **Arquivos exclusivos:**
  - `scripts/parsers/__init__.py` (NOVO)
  - `scripts/parsers/base_parser.py` (NOVO)
  - `scripts/parsers/parser_zsdfat.py` (NOVO — 22 regex)
  - `scripts/parsers/parser_verbas.py` (NOVO)
  - `scripts/parsers/parser_frete.py` (NOVO)
  - `scripts/parsers/parser_contratos.py` (NOVO)
  - `scripts/parsers/parser_promotores.py` (NOVO)
  - `scripts/parsers/dre_corrections.py` (NOVO — 22 regex)
  - `backend/app/api/routes_upload_dde.py` (NOVO)
  - `backend/tests/test_parsers.py` (NOVO)
- **ETA:** ~3-4h

#### 🅾 SQUAD OSCAR — Onda 3: Engine DDE
- **Tipo:** deep-executor (sonnet)
- **Goal:** dde_engine.py com calcula_dre_comercial + indicadores + veredito determinístico + recalc_dde.py
- **Pré-requisito:** MIKE concluído (tabelas para queries)
- **Arquivos exclusivos:**
  - `backend/app/services/dde_engine.py` (NOVO)
  - `scripts/recalc_dde.py` (NOVO — trigger pós-ingestão)
  - `backend/tests/test_dde_engine.py` (NOVO)
- **ETA:** ~3-4h

#### 🅿 SQUAD PAPA — Onda 4: API REST 5 endpoints
- **Tipo:** deep-executor (sonnet)
- **Goal:** routes_dde.py com 5 endpoints + canal scoping + testes integração
- **Pré-requisito:** OSCAR concluído (engine para chamar)
- **Arquivos exclusivos:**
  - `backend/app/api/routes_dde.py` (NOVO)
  - `backend/app/main.py` (registrar router)
  - `backend/tests/test_routes_dde.py` (NOVO)
- **ETA:** ~2-3h

#### 🆀 SQUAD QUEBEC — Onda 5: UI React (DDE + AC plug API real)
- **Tipo:** deep-executor (sonnet)
- **Goal:** Substituir páginas honestas do KILO por dashboard real consumindo API. Cascata 25 linhas + veredito + 9 indicadores + comparativo.
- **Pré-requisito:** PAPA concluído (API disponível) + KILO concluído (páginas honestas em produção como base)
- **Arquivos exclusivos:**
  - `frontend/src/app/gestao/dde/page.tsx` (substitui KILO)
  - `frontend/src/app/gestao/analise-critica/page.tsx` (substitui KILO)
  - `frontend/src/app/gestao/_components/CascadeP&L.tsx`, `ScoreGauge.tsx`, `KPIGrid.tsx`, etc.
  - `frontend/src/lib/api.ts` (adicionar fetchDDE*, sendDDEParams — NÃO mexer em outras funções)
- **ETA:** ~3-4h

#### 🆁 SQUAD ROMEO — Onda 6: LLM + PDF Resumo CEO (futuro)
- **Status:** AGUARDANDO Sprint 2+
- **ETA:** futuro

#### 🔧 SQUAD LIMA — Inbox visual residual (3 P1 do audit)
- **Tipo:** ui-designer (sonnet)
- **Goal:** Resolver os 3 P1 visuais de `/inbox/page.tsx` que sobraram (avatar 10px linha 509, badge "Recompra próxima" 9px linha 901, preview text-[11px] linha 462). NÃO mexer em lógica de fetch (INDIA acabou de aplicar SSR).
- **Arquivos exclusivos (write):**
  - `frontend/src/app/inbox/page.tsx` (apenas classes Tailwind de tipografia)
- **NÃO TOCA:** `_mockData.ts`, lógica de hooks, fetch, layout
- **ETA:** ~30min

#### 📋 SQUAD JULIET — Auditoria Paridade Mercos (read-only)
- **Tipo:** general-purpose (sonnet)
- **Goal:** Comparar `docs/specs/MERCOS_PARIDADE_SPEC.md` (40 itens-chave + 11 seções) contra estado atual do CRM. Gerar matriz `implementado/parcial/ausente` com referências a arquivos+linhas. **NÃO IMPLEMENTAR NADA** — apenas mapear gaps.
- **Arquivos exclusivos (write):**
  - `.planning/AUDITORIA_PARIDADE_MERCOS_29ABR.md`
- **Pode READ:** todo `frontend/`, `backend/`, `.planning/`, `docs/`, `memory/`
- **NÃO TOCA:** nenhum código — read-only puro
- **ETA:** ~2h

#### 🇮🇳 SQUAD INDIA — Inbox Fase 2a Real
- **Tipo:** deep-executor (sonnet)
- **Goal:** Implementar SSR migration + 3 endpoints backend + integração Deskrio + remover mocks. Preserva os 3 P1 do audit no inbox (avatar 10px linha 509, badge "Recompra próxima" 9px linha 901, preview text-[11px] linha 462).
- **Arquivos exclusivos (write):**
  - `backend/app/api/routes_inbox.py` (NOVO)
  - `backend/app/main.py` (apenas registrar router novo — coordenar)
  - `backend/tests/test_inbox_routes.py` (NOVO)
  - `frontend/src/app/inbox/page.tsx` (SSR migration + plug endpoints reais)
  - `frontend/src/app/inbox/_mockData.ts` (manter como fallback OU deletar)
  - `frontend/src/app/inbox/layout.tsx` (se SSR exigir)
  - `frontend/src/lib/api.ts` (adicionar fetchInboxConversas, fetchInboxMensagens, sendInboxMensagem — NÃO mexer em outras funções)
- **Pode READ:** `backend/app/services/deskrio_service.py` (reusar funções existentes)
- **NÃO TOCA:** `routes_whatsapp.py` (legacy — INDIA cria endpoints novos sem mexer nos antigos), `/gestao/*`, `/admin/*`, componentes globais, tailwind
- **ETA:** ~5-6h

#### 🌊 SQUAD ECHO — Visual Sweep (P0/P1 do audit ALPHA)
- **Tipo:** ui-designer (sonnet)
- **Arquivos exclusivos (write):**
  - `frontend/src/components/ui/Badge.tsx` (token xs)
  - `frontend/src/components/ui/StatusPill.tsx` (R9 INAT.ANT)
  - `frontend/src/components/ui/CurvaPill.tsx`
  - `frontend/src/components/ui/PriorityPill.tsx`
  - `frontend/src/components/ui/ScoreBar.tsx`
  - `frontend/src/components/ui/ProgressBar.tsx`
  - `frontend/src/components/ui/Tabs.tsx`
  - `frontend/src/components/ui/Sinaleiro.tsx`
  - `frontend/src/components/ClienteDetalhe.tsx`
  - `frontend/src/components/ClienteTable.tsx`
  - `frontend/src/components/ClienteModal.tsx`
  - `frontend/src/components/dashboard/CurvaABCBars.tsx`
  - `frontend/src/components/dashboard/Top5ClientesTable.tsx`
  - `frontend/src/components/TarefasPanel.tsx`
  - `frontend/src/app/page.tsx`
  - `frontend/src/app/carteira/page.tsx`
  - `frontend/src/app/inbox/page.tsx`
  - `frontend/src/app/agenda/page.tsx`
  - `frontend/src/app/pedidos/page.tsx`
  - `frontend/src/app/produtos/page.tsx`
  - `frontend/src/app/manual/page.tsx`
  - `frontend/src/app/pipeline/page.tsx`
  - `frontend/src/app/atualizacoes/page.tsx`
- **NÃO TOCA:** `Sidebar.tsx`, `AppShell.tsx`, `/gestao/*`, `/admin/*`, `/redes`, `/sinaleiro`, `/relatorios` (FOXTROT)
- **ETA:** ~3h

#### 🦊 SQUAD FOXTROT — RBAC Application + Shell Cleanup
- **Tipo:** deep-executor (sonnet)
- **Arquivos exclusivos (write):**
  - `frontend/src/components/Sidebar.tsx` (RoleGuard nos groups + esconder meta hardcoded)
  - `frontend/src/components/AppShell.tsx` (esconder meta hardcoded R$ 187k)
  - `frontend/src/app/gestao/dde/page.tsx` (RequireRole + visual sweep local)
  - `frontend/src/app/gestao/analise-critica/page.tsx` (idem)
  - `frontend/src/app/redes/page.tsx` (RequireRole min=GERENTE + sweep)
  - `frontend/src/app/sinaleiro/page.tsx` (RequireRole min=GERENTE + sweep)
  - `frontend/src/app/relatorios/page.tsx` (RequireRole min=GERENTE + sweep)
  - `frontend/src/app/admin/redistribuir/page.tsx` (RequireRole min=ADMIN + sweep)
  - `frontend/src/app/admin/**/page.tsx` (qualquer outro admin/*)
- **NÃO TOCA:** páginas core, componentes UI genéricos (ECHO)
- **ETA:** ~2h

---

*Documento mantido pelo orquestrador. Atualizar a cada novo squad/wave.*
