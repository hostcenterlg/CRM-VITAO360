# Estado do Projeto — CRM VITAO360

> **Atualizado:** 2026-04-29
> **HEAD atual:** `d8485fb`
> **Idioma:** Português Brasileiro
> **Regra:** Nunca leia apenas este arquivo. Leia também `.planning/MASTER_PLAN.md` e as memórias de sessão.

---

## POSIÇÃO ATUAL

**Milestone ativo:** v3.0 — Excelência (Master Plan)
**Fase atual:** Entre Fase 0 e Fase 1 — verificar gates antes de avançar
**Status geral:** Sistema SaaS funcional em PROD. Backend + Frontend deployados na Vercel. Banco Neon desbloqueado. Master Plan ativo com 8 fases (~28h restantes).

```
Progresso Master Plan:
FASE 0 [##########] PARCIAL (backfill Deskrio pendente, 2 GitHub Secrets faltando)
FASE 1 [          ] PENDENTE (Sales Hunter SAP ingest)
FASE 2 [          ] PENDENTE (Backfill Deskrio total)
FASE 3 [          ] PENDENTE (CNPJ Bridge)
FASE 4 [          ] PENDENTE (Pedidos + TXT SAP)
FASE 5 [          ] PENDENTE (PostgreSQL formalizado)
FASE 6 [          ] PENDENTE (Frontend dados reais)
FASE 7 [          ] PENDENTE (Schedule + Deploy)
FASE 8 [          ] PENDENTE (Validação E2E + Aceitação Leandro)
```

---

## MASTER PLAN ATIVO — v3.0 Excelência

**Arquivo fonte:** `.planning/MASTER_PLAN.md` (versão 1.0, criado 25/Abr/2026)
**Esforço total estimado:** ~28h
**Decisões L3 aprovadas:** D1=b, D2=a, D3=a, D4=a, D5=b, D6=b (25/Abr/2026, Leandro)

### Decisões L3 aprovadas (decorar)

| # | Decisão | Resposta |
|---|---|---|
| D1 | Importar logs SQLite local → Postgres? | (b) Filtrar REAL+SINTÉTICO, descartar ALUCINACAO |
| D2 | Schedule provider para daily_pipeline | (a) GitHub Actions cron |
| D3 | Schema debitos_clientes | (a) Alembic migration |
| D4 | Schema pedidos/pedido_itens | (a) Alembic |
| D5 | Frontend Sales Hunter /sap/relatorios? | (b) Esperar Fase 6 |
| D6 | Backfill 21 dias restantes | (b) --skip-contatos (~30min vs 5h) |

---

## FASE 0 — PREPARAÇÃO (PARCIALMENTE COMPLETA)

| Item | Status |
|---|---|
| 0.1 Backfill 3 dias Deskrio | status desconhecido — verificar `import_jobs` antes de prosseguir |
| 0.2 Snapshot estado pré-Fase1 | status desconhecido |
| 0.3 Corrigir datetime.utcnow() | COMPLETO (commit `db29952`, 25/Abr) |
| 0.4 Aplicar decisões L3 | COMPLETO (D1-D6 aprovadas 25/Abr) |
| 0.5 Atualizar docs desatualizados | COMPLETO (PROJECT.md baseline + scope, 25/Abr) |
| 0.6 Commitar specs Cowork | COMPLETO (commits `08572b0`, `3509b33`, `2607bd3`, 25/Abr) |

**Gate Fase 0 pendente:**
- [ ] `SELECT COUNT(*) FROM import_jobs WHERE tipo='DESKRIO'` — confirmar 3+ CONCLUIDO
- [ ] verify.py --all PASS

---

## FASE 1 — SALES HUNTER SAP INGEST (PENDENTE)

**Goal:** 13 XLSX SAP populados em Postgres como fonte de verdade do faturamento.
**Validação principal:** `SUM(faturamento_total) FROM clientes` ≈ R$ 2.091.000 ± 0.5%
**Esforço estimado:** ~4h (subagent deep-executor opus)

Status: **NÃO INICIADA**

---

## FASE 2 — BACKFILL DESKRIO COMPLETO (PENDENTE)

**Goal:** 24 dias de Deskrio em Postgres, idempotente.
**Bloqueador ativo:** Backfill de 5 dias (22, 24, 26, 27, 28/Abr) precisa rodar **manualmente por Leandro** no terminal local (~1h). Subagent não funciona para processos longos no Windows.

Comando para Leandro:
```bash
cp .env.local .env.local.bak
sed -i 's/anxji5ci-pooler/anxji5ci/' .env.local
for D in 22 24 26 27 28; do python scripts/sync_deskrio_to_db.py --data-dir "data/deskrio/2026-04-$D"; done
mv .env.local.bak .env.local
```

Status: **NÃO INICIADA**

---

## FASE 3 — CNPJ BRIDGE UNIFICADO (PENDENTE)

Bloqueia: Fases 1 e 2 completas.
Status: **NÃO INICIADA**

---

## FASE 4 — PEDIDOS + TXT SAP (PENDENTE)

**Alta complexidade:** TXT byte-a-byte contra `19465816.txt`.
**Esforço estimado:** ~8h
Status: **NÃO INICIADA**

---

## FASES 5-8 (PENDENTES)

| Fase | Goal | Esforço |
|---|---|---|
| 5 | PostgreSQL formalizado (SQLite descontinuado) | 2h |
| 6 | Frontend dados reais (22 páginas) | 6h |
| 7 | Schedule + Deploy PROD | 2h |
| 8 | Validação E2E + Aceitação Leandro | 2h |

---

## BLOQUEADORES ATIVOS (2026-04-29)

1. **Backfill 5 dias Deskrio** — manual, Leandro precisa rodar no terminal local
2. **GitHub Secrets faltando (2/6):** `DESKRIO_API_TOKEN` e `SALES_HUNTER_PASS` não configurados
3. **Inbox v2.0 UX** — 5 adendos do briefing NÃO implementados (Meta Widget, Search bar, IA Sugere placeholder, Paperclip, Typing indicator)
4. **Reconectar WhatsApp Deskrio** — `/api/whatsapp/status` pode retornar `conexoes:[]` após expiração
5. **Curva ABC NULL** — ~8164 clientes sem curva_abc (gap de dados, script derivação pendente)

---

## ESTADO DO BANCO PROD (Neon — aged-rain-76792018)

Última verificação conhecida: 29/Abr/2026

| Tabela | Contagem |
|---|---|
| clientes | 6.318 |
| log_interacoes | ~741 (191 WHATSAPP + 75 KANBAN + 474 sem tipo) |
| import_jobs | 3+ (DESKRIO) |
| vendas (SAP) | status desconhecido — verificar antes de Fase 1 |

---

## REGRAS DE NEGÓCIO CRÍTICAS (DECORAR)

- **Faturamento baseline:** R$ 2.091.000 (PAINEL CEO, corrigido 23/Mar/2026 — anterior R$ 2.156.179 SUPERSEDED)
- **Projeção 2026:** R$ 3.377.120 (+69%)
- **Q1 2026 real:** R$ 459.465
- **Two-Base Architecture:** VENDA = tem valor R$, LOG = sempre R$ 0,00. Violação = inflação 742%.
- **CNPJ:** string 14 dígitos, zero-padded, nunca float. `re.sub(r'\D', '', str(val)).zfill(14)`
- **Fórmulas Excel:** inglês no openpyxl (IF, VLOOKUP, SUMIF), separador vírgula, nunca português.

---

## ARQUITETURA (CRÍTICO — não confundir)

- **crm-vitao360.vercel.app** = backend FastAPI puro (rotas /api/*, /docs, /health)
- **intelligent-crm360.vercel.app** = frontend Next.js (onde o usuário entra: /carteira, /agenda, /inbox, etc.)
- **Login PROD:** leandro@vitao.com.br / vitao2026
- **DB PROD:** Neon ep-purple-cloud-anxji5ci-pooler.c-6.us-east-1.aws.neon.tech/neondb

---

## COMO RETOMAR PRÓXIMA SESSÃO

```bash
# 1. Boot obrigatório
python scripts/session_boot.py
python scripts/compliance_gate.py

# 2. Verificar Fase 0 gate fechado
python scripts/verify.py --all
# psql: SELECT tipo, status, COUNT(*) FROM import_jobs GROUP BY tipo, status

# 3. Confirmar com Leandro:
#    - Backfill 5 dias rodou?
#    - 2 GitHub Secrets configurados?
#    - WhatsApp reconectado?

# 4. Próxima ação: Fase 1 (Sales Hunter ingest)
#    Subagent: deep-executor opus
#    Briefing: GAPS_EXCELENCIA_SPEC.md GAP 2C
```

---

## MILESTONES CONCLUIDOS

### v2.0 — Motor Operacional SaaS (concluído 2026-03-24)

**Fases 11-15 completas — Motor Python com pipeline 8 stages operacional.**

| Fase | Entrega | Commit |
|---|---|---|
| 11 | Import Pipeline (config + helpers + classify + run_import) | 864e28f, 55f43c3, 539f3cf, 7b37658, 2219c8c |
| 12 | Motor de Regras (92 combinações, 9 dimensões, 99.2% match) | 2219c8c |
| 13 | Score + Sinaleiro (6 fatores ponderados, P0-P7, VERDE/AMARELO/VERMELHO/ROXO) | 2219c8c |
| 14 | Agenda Inteligente (40-60 atendimentos/dia, xlsx 8 abas, 69 testes) | 2219c8c |
| 15 | Projeção + Export (8 stages, dashboard ASCII) | 4f2bae1 |

**Métricas v2.0:**
- Plans completed: 2 (11-01, 11-02)
- QA audit 12 commits atômicos: 24/Mar
- Pipeline stages: 7→8

---

### v1.0 — Excel Rebuild (concluído 2026-02-17)

**10 fases completas — planilha Excel final com 40 abas.**

- 31 planos, 43 requisitos, 154.302 fórmulas
- V13→V43 iterações
- Planilha FINAL: 40 abas, 210K+ fórmulas, 263 colunas na CARTEIRA
- Velocidade média: 12 min/plano, 6.3h total
- Two-Base Architecture confirmada
- CNPJ string 14 dígitos como chave primária universal

---

## SESSÕES RECENTES

| Data | HEAD | Destaques |
|---|---|---|
| 29/Abr/2026 | d8485fb | Redesign UX Wave 1-4 (16 commits) + Neon upgrade + Inbox Deskrio fix |
| 29/Abr/2026 | 5cb3787 | 28 commits totais no dia, PROD estável, Briefing Inbox v2.0 pendente |
| 28/Abr/2026 | db820f3 | 23 commits, daily pipeline GitHub Actions, CanalSelector, LLM infra dormente |
| 25/Abr/2026 | f7cb4ab | Master Plan criado, D1-D6 aprovadas, sync_deskrio expandido, 10 commits |

---

*Gerado por @pm em 2026-04-29. Próxima atualização: ao fechar Fase 1 (Sales Hunter ingest).*
