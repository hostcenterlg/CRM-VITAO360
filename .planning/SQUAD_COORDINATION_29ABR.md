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

### WAVE 1 — Audit + Foundation (rodando)
- ALPHA, BRAVO, CHARLIE, DELTA em paralelo

### WAVE 2 — Application (após WAVE 1)
- Aplicar design tokens (DELTA outputs) nas páginas
- Aplicar `RequireRole` (BRAVO outputs) nas rotas e componentes
- Resolver os Top-N issues do AUDIT (ALPHA outputs)
- Smoke test PROD + push

---

*Documento mantido pelo orquestrador. Atualizar a cada novo squad/wave.*
