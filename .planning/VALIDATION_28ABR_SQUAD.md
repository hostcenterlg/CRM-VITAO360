# VALIDATION_28ABR_SQUAD — Matriz Pós-Deploy 28/Abr/2026

**Gerado por:** @qa  
**Ref commit:** db820f3 (HEAD master)  
**Data:** 2026-04-28  
**Status deploy:** SUSPEITO — Vercel serving Last-Modified 26/Abr (Age: 216994s ≈ 60h)

---

## Seção A — Matriz de Testes Pós-Deploy

| # | Cenário | Comando/Ação | Expected | Real (preencher) |
|---|---------|--------------|----------|-----------------|
| 1 | /dashboard redirect | `curl -sI https://intelligent-crm360.vercel.app/dashboard` | HTTP 307 ou 308 com `Location: /` | |
| 2 | /manual redirect | `curl -sI https://intelligent-crm360.vercel.app/manual` | HTTP 307 ou 308 com `Location: /docs` | |
| 3 | /docs renderiza | `curl -sI https://intelligent-crm360.vercel.app/docs` | HTTP 200 | |
| 4 | / homepage | `curl -sI https://intelligent-crm360.vercel.app/` | HTTP 200 | |
| 5 | /carteira | `curl -sI https://intelligent-crm360.vercel.app/carteira` | HTTP 200 (pode ser 200 com auth redirect) | |
| 6 | API resumo-semanal LARISSA | `curl -s -H "Authorization: Bearer <TOKEN>" https://crm-vitao360.vercel.app/api/ia/resumo-semanal/LARISSA` | JSON com `metricas.vendas_semana_volume` número finito (não NaN, não null) | |
| 7 | Visual: Card Resumo Semanal | Browser: /ia → consultor LARISSA → aguardar card | "Volume R$" exibe valor monetário (ex: R$ 48.731,75), não "R$ NaN" | preencher manual |
| 8 | Cache busted dashboard | `curl -sI -H "Cache-Control: no-cache" https://intelligent-crm360.vercel.app/dashboard` | `x-vercel-id` com deployment recente pós-db820f3 | |

**Nota BUG 6 (schema mismatch):** O componente `CardResumoSemanal` em `frontend/src/app/ia/page.tsx:669` acessa `data.valor_vendas` (campo top-level que NÃO existe). A interface `ResumoSemanalIAResponse` em `api.ts:1569` define `metricas.vendas_semana_volume`. O fix do backend (commit 3462799) protege contra NaN mas o frontend ainda lerá `undefined` enquanto acessar o campo errado. Fix pendente: `data.valor_vendas` → `data.metricas.vendas_semana_volume`.

---

## Seção B — Hipóteses Vercel Cache Stale (prioridade decrescente)

1. **Hipótese C (MAIS PROVÁVEL): Deploy db820f3 não está como Production** — Vercel pode ter feito build mas não promoveu para Production, ou o deploy falhou silenciosamente. Checar em Vercel Dashboard > Deployments se db820f3 aparece como "Production" ou apenas "Preview".

2. **Hipótese D: CDN edge cache TTL travado no 404** — `Age: 216994` indica edge cache servindo resposta antiga de 60h para rotas 404. Redeploy com "Invalidate Cache" ou `vercel --prod --force` limpa o CDN. Mesmo que o deploy tenha ocorrido, o edge pode estar preso.

3. **Hipótese B: rootDirectory configurado incorretamente no projeto intelligent-crm360** — Se o projeto Vercel aponta para `/` em vez de `/frontend`, os arquivos `frontend/src/app/dashboard/page.tsx` e `manual/page.tsx` ficam fora do build artifact. Verificar em Settings > General > Root Directory.

4. **Hipótese A: Vercel auto-build desativado para master** — Se "Deploy on Push" estiver desabilitado, nenhum push aciona build. Empty commit + push confirmará: se não aparecer novo build em Deployments em 60s, esta hipótese é válida.

---

## Seção C — Plano de Ação (sequencial)

1. [ ] **Empty commit + push** (squad executor): `git commit --allow-empty -m "chore: trigger vercel redeploy" && git push` — aguardar 90s
2. [ ] **Verificar Deployments no Vercel Dashboard** (Leandro): confirmar se novo build aparece para intelligent-crm360; checar se está como "Production" após build
3. [ ] **Repetir Seção A completa** após build confirmado — script `scripts/qa_smoke_post_deploy.sh --token <TOKEN>`
4. [ ] **Se /dashboard ainda 404 após novo deploy**: Leandro abrir Vercel Dashboard > Settings > General > Root Directory — confirmar que aponta para `frontend` (não para raiz `/`)
5. [ ] **Se Root Directory errado**: corrigir para `frontend`, clicar "Save", depois Redeploy com "Clear Build Cache"
6. [ ] **Se deploy falhar com erro de build**: copiar log completo do Vercel e reportar — provavelmente erro TypeScript (campo `valor_vendas` inexistente em `ResumoSemanalIAResponse` pode causar type error no build)
7. [ ] **Fix frontend BUG 6 (schema mismatch)**: substituir `data.valor_vendas` por `data.metricas.vendas_semana_volume` em `frontend/src/app/ia/page.tsx:669`
8. [ ] **Após todos os fixes**: rodar `scripts/qa_smoke_post_deploy.sh --token <TOKEN>` e validar 100% PASS

---

## Seção D — Métricas de Aceitação Final

| Métrica | Critério | Como verificar |
|---------|----------|----------------|
| Faturamento baseline | R$ 2.091.000 ± 0.5% (≤ R$ 10.455 de desvio) | `python scripts/verify.py --all` |
| log_interacoes range | Cobre 28/Abr/2026 após backfill | `SELECT MAX(data_interacao) FROM log_interacoes` |
| API health | `{"status":"ok"}` | `curl https://crm-vitao360.vercel.app/health` |
| Dashboard CEO | Sem console errors (F12) | Browser manual |
| /dashboard redirect | HTTP 307/308 → `/` | Teste #1 da Seção A |
| /manual redirect | HTTP 307/308 → `/docs` | Teste #2 da Seção A |
| Volume R$ Resumo Semanal | Número finito formatado (não NaN) | Teste #7 da Seção A |
| Build TypeScript | 0 erros type | `cd frontend && npx tsc --noEmit` |

---

## Evidências de Diagnóstico Coletadas

- `frontend/src/app/dashboard/page.tsx` — EXISTS (commit 309a9fd), contém `redirect('/')` correto
- `frontend/src/app/manual/page.tsx` — EXISTS (commit 5f037a3), contém `redirect('/docs')` correto
- `backend/app/services/ia_service.py:996` — `"vendas_semana_volume": total_vendas_semana` (fix 3462799 aplicado, OR-0 guard presente)
- `frontend/src/lib/api.ts:1569` — interface define `metricas.vendas_semana_volume: number` (correto)
- `frontend/src/app/ia/page.tsx:669` — acessa `data.valor_vendas` (CAMPO ERRADO — mismatch não resolvido)
- Vercel response header `Last-Modified: Sun, 26 Apr 2026 12:06:21 GMT` + `Age: 216994` — deploy não propagado ou CDN stale
