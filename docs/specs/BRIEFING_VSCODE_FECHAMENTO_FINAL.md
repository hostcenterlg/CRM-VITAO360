# BRIEFING VSCode — FECHAMENTO FINAL

> **Para:** Claude Code rodando no VSCode do Leandro
> **De:** @aios-master (sessão CLI 28/Abr/2026)
> **Data:** 2026-04-28
> **Objetivo:** fechar 4 itens visíveis do CRM em 6 passos com commits atômicos

---

## REGRAS DURAS — NÃO PODE QUEBRAR

| # | Regra | Consequência se quebrar |
|---|---|---|
| R1 | **1 commit por passo.** Nunca "fix various". | Reverter e refazer |
| R2 | **Não declara passo fechado sem abrir navegador.** HTTP smoke não vale. | Abrir Chrome, executar fluxo, ver visual |
| R3 | **Falhou? PARA e reporta.** Nada de pular pro próximo passo. | Bloqueio explícito até Leandro decidir |
| R4 | **Pre-commit hook bloqueou? Corrige causa.** Nunca usa `--no-verify` | Investigar o motivo, fixar real |
| R5 | **NÃO usa LLMClient.** É só pra Sprint 4 (futura). Não toque. | Reverter import |
| R6 | **NÃO cria arquivo novo sem necessidade.** Se já existe componente similar, edita. | Apagar duplicação |
| R7 | **NÃO mexe** em `backend/app/services/llm_client.py` nem `frontend/src/lib/llm_provider.ts`. Estão dormentes propositais. | Reverter |

---

## ESTADO DE ENTRADA (validado 28/Abr 14h45 BRT)

```
HEAD origin/master = 273ed18 feat(llm): provider-agnostic LLM infra
14 commits desta sessão já pushed
verify.py PROD = 10/10 PASS
Banco PROD: 11.764 clientes / 5.711 vendas SAP / 0 NULLs canal_id / 5 ACLs
Frontend PROD ativo: crm-vitao360.vercel.app + intelligent-crm360.vercel.app
Backfill log_interacoes em background — não bloqueia
```

**Working tree NÃO está zerado.** Tem 11 itens uncommitted que precisam ser categorizados (Passo 0).

---

## PASSO 0 — Organizar working tree (~10min)

**Inventário real:**

```
M  .claude/scheduled_tasks.lock              ← descarte (artefato CLI, automático)
?? .env.local.bak                            ← descarte (backup do backfill em curso)
?? BRIEFING_VSCODE_28ABR2026.md              ← commit como docs/
?? BRIEFING_VSCODE_FECHAMENTO_FINAL.md       ← este arquivo, commit como docs/
?? SPEC_ANALISE_CRITICA_VIVA.md              ← commit como docs/specs/
?? SPEC_DDE_CLIENTE.md                       ← commit como docs/specs/
?? SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md ← commit como docs/specs/
?? data/backups/                             ← adicionar ao .gitignore (já parcialmente ignored)
?? data/deskrio/2026-04-26..28/              ← adicionar ao .gitignore (snapshots regenerável)
?? data/sales_hunter/2026-04-25/             ← adicionar ao .gitignore (XLSX regenerável)
```

**Ações:**

1. **Mover specs/briefings para `docs/specs/`** (criar dir se não existe):
   ```bash
   mkdir -p docs/specs
   git mv BRIEFING_VSCODE_28ABR2026.md docs/specs/ 2>/dev/null || mv BRIEFING_VSCODE_28ABR2026.md docs/specs/
   mv BRIEFING_VSCODE_FECHAMENTO_FINAL.md docs/specs/
   mv SPEC_ANALISE_CRITICA_VIVA.md docs/specs/
   mv SPEC_DDE_CLIENTE.md docs/specs/
   mv SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md docs/specs/
   ```

2. **Atualizar `.gitignore`** (adicionar no final):
   ```
   # Snapshots regeneráveis (gerados por scripts diários)
   data/deskrio/2026-*/
   data/sales_hunter/2026-*/
   data/backups/

   # Backups efêmeros locais
   .env.local.bak
   .env*.bak
   ```

3. **Discartar `.env.local.bak`** (se ainda existir após backfill terminar):
   ```bash
   rm -f .env.local.bak
   ```

4. **Commit:**
   ```
   chore: organize specs into docs/specs + ignore data snapshots
   ```

5. **Push:**
   ```bash
   git push origin master
   ```

**Validação Passo 0:**
- `git status -s` retorna apenas `M .claude/scheduled_tasks.lock` (artefato CLI ignorável) ou está limpo
- `git log -1` mostra commit do passo 0
- Push feito sem erro

**Se falhou:** PARA. Não vai pra Passo 1.

---

## PASSO 1 — Carteira race condition (~30-60min)

**Sintoma reportado:** /carteira em alguns hard refreshes mostra "Erro ao carregar Carteira" (`null.length`). PR #1 (commit `008e96b` em 26/Abr) corrigiu defensivos básicos, mas pode haver corrida residual entre `fetchClientes` async e renders.

**O fix de `008e96b` cobre:**
- `(response?.registros ?? [])` em todos os usos
- `?.length ?? 0` em counts
- `error.tsx` na rota
- `ClienteRegistro[]` typed corretamente

**O que pode ainda falhar:**
- Suspense boundary não envolvendo SearchParams
- Algum subcomponente (`ClienteTable`, `ClienteDetalhe`) acessa propriedade `null` antes de hydratação
- `useMemo` recalculando enquanto `response` é `null`

**Procedimento OBRIGATÓRIO:**

### 1.1 Reproduzir e capturar stack REAL
```
1. Abrir https://crm-vitao360.vercel.app em janela anônima
2. Login: leandro@vitao.com.br / vitao2026
3. Ir para /carteira
4. F12 → console clean (Clear)
5. Hard refresh (Ctrl+Shift+R) 5× SEGUIDOS
6. Anotar:
   - Quantos refreshes deram crash?
   - Stack trace COMPLETO (Error.message + cada linha de Error.stack)
   - Estado do Network tab quando crashou (xhr para /api/clientes)
   - Timestamp do crash relativo ao mount
```

### 1.2 Documentar o trace em `docs/specs/CARTEIRA_RACE_TRACE.md`
Salvar:
- Stack completo (não resumido)
- Hipótese da corrida
- Componente/linha específica que falhou

### 1.3 Fix BASEADO NO TRACE
**NÃO chuta defensivos genéricos.** Adicione guard EXATO no ponto que o trace aponta. Se trace cita `ClienteTable.tsx:123`, abre, lê, ENTENDE, fixa.

Possíveis pontos de corrida (não chute, valide):
- `frontend/src/components/ClienteTable.tsx` — recebe `registros` mas pode ler antes de filtragem
- `frontend/src/components/ClienteDetalhe.tsx` — fetch `cnpj` antes de cliente carregar
- `frontend/src/app/carteira/page.tsx:172` `useState<ClientesResponse | null>(null)` → mudar para `useState<ClientesResponse>(EMPTY_RESPONSE)` com const init pode eliminar nullable downstream

### 1.4 Commit
```
fix(carteira): eliminate race condition between fetch and render

Stack trace captured at <componente>:<linha> when ...
Fix: <descrição do guard exato>

Refs: <link/path para CARTEIRA_RACE_TRACE.md>
```

### 1.5 Push + redeploy

### 1.6 Validação visual OBRIGATÓRIA
```
1. Aguardar Vercel deploy (1-3min após push)
2. Janela anônima → login → /carteira
3. Hard refresh (Ctrl+Shift+R) 10× SEGUIDOS
4. Em todos os 10: tabela carrega sem crash, console sem erros
5. Se crashar 1× em 10: NÃO é fix bom. Voltar a 1.1
```

**Se falhou:** PARA. Reporta o trace + tentativa + porque continuou crashando.

---

## PASSO 2 — Dashboard UX: tabs visíveis + filtros + Projeção (~45-90min)

**Estrutura atual:**
- Dashboard = homepage `frontend/src/app/page.tsx`
- Projeção = rota separada `/projecao` listada no menu lateral
- Filtros existentes no Dashboard: indeterminado (verificar)

**Objetivo:**
1. Reorganizar Dashboard com tabs VISÍVEIS (não link de menu, tabs no topo da página)
2. Tabs sugeridas: "Visão Geral" | "Projeção" | "Indicadores" | "Funil"
3. Mover Projeção do menu lateral para tab dentro do Dashboard
4. Filtros do Dashboard em 3 linhas com hierarquia visual:
   - Linha 1 (mais importante): consultor + canal + período
   - Linha 2: ABC + temperatura + sinaleiro
   - Linha 3 (refinamento): UF + situação + busca

**Estilo das tabs:**
- Tab ativa: fundo `#00B050` (verde VITAO), texto branco, peso 600, border-bottom 2px verde escuro
- Tab inativa: fundo branco, texto cinza-700, peso 500
- Contraste alto, mobile-friendly, no mínimo 44px de altura clicável

**Implementação:**

### 2.1 Mapear o que o Dashboard JÁ tem
```bash
cat frontend/src/app/page.tsx | head -100
ls frontend/src/components/dashboard/ 2>/dev/null
```

### 2.2 Decidir se cria componente `DashboardTabs.tsx` ou edita inline
Critério: se já tem `<Tabs>` shared no projeto, reutilizar; se não, criar `frontend/src/components/dashboard/DashboardTabs.tsx`

### 2.3 Mover lógica da `frontend/src/app/projecao/page.tsx` para tab
Não deletar a rota `/projecao` (compatibilidade), apenas:
- Extrair conteúdo para `frontend/src/components/dashboard/ProjecaoTab.tsx`
- Reusar em ambos: `/page.tsx` (como tab) e `/projecao/page.tsx` (rota standalone)

### 2.4 Filtros 3 linhas
Criar `frontend/src/components/dashboard/FiltrosDashboard.tsx`:
- Grid responsiva: `grid-cols-3 md:grid-cols-3 lg:grid-cols-3`
- Linha 1: consultor + canal + período
- Linha 2: ABC + temperatura + sinaleiro
- Linha 3: UF + situação + busca
- Cada select altura 40px no mobile, 36px no desktop
- Label `text-[10px] uppercase tracking-wide text-gray-500` acima de cada input

### 2.5 Atualizar menu lateral (`AppShell.tsx`)
Remover entrada "Projeção" do menu lateral (mas manter rota viva). Se o menu tem badge ou contador específico para Projeção, migrar para a tab.

### 2.6 Commit
```
feat(dashboard): tabs visíveis (Visão/Projeção/Indicadores/Funil) + filtros 3 linhas

- Projeção movida para tab dentro do Dashboard (rota standalone preservada)
- Filtros reorganizados em 3 linhas com hierarquia (P1 consultor/canal/período,
  P2 ABC/temperatura/sinaleiro, P3 UF/situação/busca)
- Estilo tabs: ativa=verde VITAO, inativa=branca, contraste alto, 44px mínimo
- Menu lateral: removida entrada Projeção
```

### 2.7 Validação visual OBRIGATÓRIA
```
1. Janela anônima → login → /
2. Ver tabs no topo: 4 visíveis com labels claros
3. Clicar cada tab: conteúdo troca SEM reload de página (client-side route)
4. Filtros: 3 linhas verticais, hierarquia visual clara
5. Testar em mobile (Chrome devtools 375px): tabs e filtros legíveis e clicáveis
6. /projecao ainda funciona como rota standalone (compatibilidade)
7. Console limpo
```

**Se falhou:** PARA. Reporta screenshot + diff inteiro.

---

## PASSO 3 — Inbox SSR + cookie httpOnly (~60-120min)

**Sintoma:** `frontend/src/app/inbox/page.tsx` é client component (`'use client'` linha 1). Chamadas `fetchInbox` falham com 401 porque token JWT está no localStorage mas não passa nas requests do hook `useEffect`.

**Outras páginas (Carteira, Agenda) funcionam** porque o Next/Vercel SSR já carrega data + auth no servidor antes de hidratar.

**Solução:**
1. Converter Inbox para **server component** (remover `'use client'`)
2. JWT por **cookie httpOnly** (não localStorage)
3. Componentes interativos isolados em sub-componentes client (`InboxClient.tsx`)
4. Fetch inicial: server-side (com cookie auto-forwarded)

**Pré-requisito:** verificar se backend aceita JWT por cookie. Se não aceita, ajustar `backend/app/api/deps.py::get_current_user` para ler cookie OU header.

**Implementação:**

### 3.1 Confirmar pré-requisito backend
```bash
grep -n "Authorization\|Bearer\|HTTPBearer\|cookie" backend/app/api/deps.py | head -10
```

Se backend SÓ aceita header Bearer:
- Adicionar leitura via `Cookie` (FastAPI: `request.cookies.get("access_token")`)
- Manter compatibilidade com header (existing tests não quebram)
- Commit separado: `feat(auth): support JWT via httpOnly cookie alongside Authorization header`

### 3.2 Converter Inbox
```
frontend/src/app/inbox/page.tsx
  → server component (remove 'use client')
  → async function default export
  → await fetchInbox no server (passa cookie automaticamente)

frontend/src/app/inbox/InboxClient.tsx (novo)
  → 'use client'
  → componente que recebe props initialTickets, initialStatus
  → mantém polling, estado, handlers (tudo o que era no page.tsx)
```

### 3.3 Login flow ajustado
- `frontend/src/lib/auth.ts` — após login, setar cookie httpOnly `access_token` (chamada API a `/api/auth/login` deve setar via header `Set-Cookie`)
- Pode requerer ajuste em `backend/app/api/routes_auth.py::login` para retornar `Set-Cookie` além de body com `access_token`

### 3.4 Commit
```
fix(inbox): SSR with httpOnly cookie auth — eliminate 401 on client fetch

- Inbox converted to server component (await fetchInbox before hydration)
- New InboxClient.tsx for interactive parts
- Backend deps.py reads JWT from cookie OR Authorization header
- Login sets access_token httpOnly cookie alongside body
```

(se conseguir 1 commit; se separar backend/frontend, dois commits, ainda atomic)

### 3.5 Validação visual OBRIGATÓRIA
```
1. Janela anônima → /inbox
   Esperado: redirect para /login (sem cookie)
2. Login → /inbox
   Esperado: lista de tickets carrega no SSR (sem flash de loading)
3. Console: zero 401
4. Network tab: fetch /api/whatsapp/inbox retorna 200 (não 401)
5. Daiane logada → /inbox: vê apenas tickets com CNPJs em INTERNO+FOOD_SERVICE
6. Manu logada → /inbox: vê apenas tickets DIRETO
7. Hard refresh: ainda autenticado (cookie persiste) — Inbox carrega
```

**Se vazio:** OK enquanto conexões Deskrio estiverem offline (backfill enche `log_interacoes`, não Inbox API live). Documentar no relatório do Passo 5 que Inbox depende de WA reconnect manual.

**Se falhou:** PARA. Reporta o trace de 401, o status da conexão WA, e o que tentou.

---

## PASSO 4 — Checklist visual: 3 perfis × 8 páginas = 24 checks (~60min)

**Perfis:**
- ADMIN: leandro@vitao.com.br / vitao2026
- CONSULTORA DIRETO: manu@vitao.com.br / vitao2026
- GERENTE INTERNO+FOOD: daiane@vitao.com.br / vitao2026

**Páginas obrigatórias (8):**
1. `/` (Dashboard com tabs)
2. `/carteira`
3. `/agenda`
4. `/inbox`
5. `/sinaleiro`
6. `/vendas`
7. `/atendimentos`
8. `/admin/usuarios` (só admin acessa — outros perfis devem ver redirect ou 403)

**Para cada combinação (24 checks):**
| Check | Pass se |
|---|---|
| Página carrega | HTTP visual 200, sem tela de erro |
| Console limpo | Zero `Error`/`Warning` no DevTools |
| Auth filtra | Não-admin vê apenas dados do canal permitido |
| Interatividade | Cliques funcionam, sem dead state |
| Mobile (375px) | Layout não quebra horizontalmente |

**Salvar resultado em `docs/specs/SMOKE_VISUAL_28ABR2026.md`** — tabela 24 linhas.

### Commit Passo 4
```
docs: visual smoke matrix 3 profiles × 8 pages
```

(Sem mudança de código aqui, apenas documentação. Se durante o smoke você encontrar bug NOVO, **PARA e abre Passo 4.x novo**, não junta.)

---

## PASSO 5 — Relatório FINAL (formato fixo)

Após Passos 0-4 fechados, criar `docs/specs/RELATORIO_FECHAMENTO_28ABR2026.md` com **EXATAMENTE este formato**:

```markdown
# Relatório de Fechamento — 28/Abr/2026

## Commits desta sessão
| # | SHA | Mensagem | Pushed |
|---|---|---|---|
| ... | ... | ... | ✅/❌ |

## Passo 0 — Organização working tree
- Status: ✅ FECHADO / ❌ FALHOU
- Working tree atual: `git status -s` output
- Arquivos movidos: <lista>
- .gitignore atualizado: SIM / NÃO

## Passo 1 — Carteira race condition
- Status: ✅ FECHADO / ❌ FALHOU
- Stack trace original: <link CARTEIRA_RACE_TRACE.md>
- Componente/linha do bug: <ex: ClienteTable.tsx:123>
- Fix aplicado: <descrição em 1 linha>
- Validação visual: 10/10 hard refreshes sem crash em <data/hora>

## Passo 2 — Dashboard tabs + filtros + Projeção
- Status: ✅ FECHADO / ❌ FALHOU
- Tabs implementadas: <lista>
- Componentes criados: <paths>
- Menu lateral atualizado: SIM / NÃO
- Validação visual: <data/hora> + screenshot opcional

## Passo 3 — Inbox SSR + cookie httpOnly
- Status: ✅ FECHADO / ❌ FALHOU
- Backend cookie support: SIM / NÃO (linha em deps.py)
- Inbox convertida: SIM / NÃO
- Login seta cookie: SIM / NÃO
- Validação visual: 0 erros 401, dados aparecem no SSR

## Passo 4 — Smoke visual 24 checks
- Status: ✅ FECHADO / ❌ FALHOU
- Tabela: <link SMOKE_VISUAL_28ABR2026.md>
- Resultado: X/24 PASS, Y/24 FAIL (descrever cada FAIL)

## Bloqueadores remanescentes
- <descrever cada bloqueador, ou "Nenhum">

## Pendências do usuário (manuais)
- Reconectar conexões WhatsApp Deskrio (Inbox vazia até ser feito)
- Configurar GitHub Secrets (5 vars listadas em docs/LLM_SETUP.md raiz)
- Validar visualmente as 4 mudanças de UX (tabs/filtros/Projeção/Inbox)

## Estado git final
HEAD: <sha>
Origin: <sha>
Divergência: <0 ahead, 0 behind / X ahead>
verify.py PROD: 10/10 PASS / X/10 FAIL
```

---

## ARTEFATOS QUE O VSCode DEVE CRIAR DURANTE A EXECUÇÃO

1. `docs/specs/CARTEIRA_RACE_TRACE.md` (Passo 1)
2. `docs/specs/SMOKE_VISUAL_28ABR2026.md` (Passo 4)
3. `docs/specs/RELATORIO_FECHAMENTO_28ABR2026.md` (Passo 5)
4. **5 commits** (Passo 0, 1, 2, 3, 4) — ou 6 se Passo 3 separar backend/frontend
5. **5+ pushes** correspondentes

---

## SE TUDO ESTIVER FECHADO

Reporta o conteúdo do RELATORIO_FECHAMENTO_28ABR2026.md em mensagem ao Leandro. Tópico: "BRIEFING_VSCODE_FECHAMENTO_FINAL — fechado".

---

## SE ALGUM PASSO FALHAR

Reporta:
1. Qual passo falhou
2. Sintoma exato (com screenshot ou trace literal)
3. O que tentou
4. O que precisa pra resolver

NÃO PULA pra próximo passo. NÃO JUNTA fixes. NÃO usa `--no-verify`.

---

*Briefing gerado por @aios-master em 2026-04-28 14:50 BRT, contexto sessão Claude Code CLI. Validado contra estado real do repo (11 uncommitted, HEAD 273ed18).*
