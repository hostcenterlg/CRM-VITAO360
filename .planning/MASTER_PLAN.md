# MASTER PLAN — CRM VITAO360 100% Excelência

> **Versão:** 1.0
> **Criado:** 2026-04-25
> **Autor:** @aios-master (orquestrador)
> **Status:** ATIVO — Fase 0 em curso (backfill Deskrio rodando)
> **Decisões L3:** D1=b, D2=a, D3=a, D4=a, D5=b, D6=b (aprovadas pelo Leandro 25/Abr/2026)

Plano sólido, sequenciado, com gates de validação obrigatórios em cada fase. Cobre TUDO: GAPs 1-6 + Sales Hunter SAP + Pedidos+TXT + housekeeping + decisões L3.

Cada fase tem **DONE criteria testáveis** e **rollback strategy**.

---

## REFERÊNCIA RÁPIDA

| Campo | Valor |
|---|---|
| Branch ativa | `master` (4 commits ahead) |
| DB PROD | Postgres Neon (`ep-purple-cloud-anxji5ci-pooler.c-6.us-east-1.aws.neon.tech/neondb`) |
| Token Deskrio | leandro.garcia@vitao.com.br, exp 2026-12-11 (DESKRIO_API_TOKEN no .env) |
| Login PROD | leandro@vitao.com.br / vitao2026 (crm-vitao360.vercel.app) |
| Baseline faturamento | R$ 2.091.000 (PAINEL CEO 2025, corrigido 23/Mar/2026) |
| Tolerância | 0.5% (R9) |
| Q1 2026 real | R$ 459.465 |

---

## PRINCÍPIOS DE EXECUÇÃO

| Princípio | Como se manifesta |
|---|---|
| **Goal-backward** | Cada fase produz artefato verificável antes de avançar |
| **Detector de Mentira N1+N2+N3** | Existência → Substância → Conexão em cada commit |
| **R11 Commits atômicos** | 1 task = 1 commit em inglês |
| **R12 Decisão L3 explícita** | Tabela de decisões pendentes = bloqueante até resolver |
| **Pre-flight check** | Verify.py + counts ANTES de cada fase |
| **Rollback plan** | Alembic downgrade testado para cada migration |
| **Trust but verify** | Após cada subagent: ler diff + rodar smoke test |
| **Two-Base, R5, R8** | Hard-enforced em código + validation final |
| **Sem `git push`** | Só @devops faz deploy de PR aprovado |

---

## DECISÕES L3 APROVADAS (25/Abr/2026)

| # | Decisão | Resposta | Implicação |
|---|---|---|---|
| **D1** | Importar 21.345 logs SQLite local → Postgres? | **(b) Filtrar tier REAL+SINTÉTICO** | Auditar antes; só importa REAL/SINTÉTICO; descarta ALUCINACAO |
| **D2** | Schedule provider para `daily_pipeline.py` | **(a) GitHub Actions cron** | Free, gitops nativo, logs no GitHub |
| **D3** | Schema `debitos_clientes` (FASE 1) | **(a) Alembic migration** | Consistência, migrações tracked |
| **D4** | Schema `pedidos`/`pedido_itens` (FASE 4) | **(a) Alembic** | Mesma lógica D3 |
| **D5** | Frontend Sales Hunter `/sap/relatorios`? | **(b) Esperar fase 6** | Dados primeiro, UI depois |
| **D6** | Backfill 21 dias restantes | **(b) `--skip-contatos`** | ~30min vs 5h |

---

## MAPA DAS FASES

```
FASE 0 (PREPARAÇÃO + decisões L3)         ← em curso
   ↓
FASE 1 (Sales Hunter SAP ingest)           ← prioridade alta
   ↓
FASE 2 (Backfill Deskrio total)
   ↓
FASE 3 (CNPJ Bridge unificado)
   ↓
FASE 4 (Pedidos + TXT SAP)
   ↓
FASE 5 (PostgreSQL formaliza)
   ↓
FASE 6 (Frontend dados reais)
   ↓
FASE 7 (Schedule + Deploy)
   ↓
FASE 8 (Validação E2E + Aceitação)
```

**Esforço total estimado:** ~28h ao longo de 2-3 sessões.

---

## FASE 0 — PREPARAÇÃO & DECISÕES BLOQUEANTES

**Goal:** Estado limpo e decisões L3 resolvidas antes de qualquer trabalho novo.

### 0.1 Aguardar backfill 3 dias terminar (em curso)
- **Status:** ⏳ Dia 23 ✅, dia 24 em curso, dia 25 pendente
- **DONE quando:** `backfill.log` contém "BACKFILL CONCLUIDO" e exit=0
- **Validar:** `SELECT COUNT(*) FROM import_jobs WHERE tipo='DESKRIO'` retorna 3 com status='CONCLUIDO'

### 0.2 Snapshot de estado pós-backfill
- Capturar counts em `.planning/STATE_BEFORE_FASE1.md`
- Métricas: clientes, log_interacoes (por tipo_contato), import_jobs, vendas

### 0.3 Corrigir DeprecationWarning `datetime.utcnow()`
- 2 ocorrências em `scripts/sync_deskrio_to_db.py` (linhas 1226 e 1293)
- Trocar `datetime.utcnow()` → `datetime.now(timezone.utc).replace(tzinfo=None)`
- Commit: `fix(scripts): replace deprecated datetime.utcnow with timezone-aware`

### 0.4 Aplicar decisões L3 (já aprovadas — só executar)
- D1, D2, D3, D4, D5, D6 já decididas (ver tabela acima)
- Nenhuma aprovação adicional necessária para iniciar Fase 1

### 0.5 Atualizar docs desatualizados
- `.planning/PROJECT.md`: remover "Out of Scope: Migração SaaS"
- `.planning/PROJECT.md`: baseline R$ 2.156.179 → R$ 2.091.000
- `.planning/STATE.md`: registrar Phase 16+ em andamento
- Commit: `docs(planning): update PROJECT.md baseline + scope to reflect SaaS reality`

### 0.6 Commitar specs do Cowork
- `GAPS_EXCELENCIA_SPEC.md`, `SPEC_PIPELINE_PRODUTOS.md`, `SALES_HUNTER_EXTRACTION_SPEC.md` (todos untracked)
- Commit: `docs(specs): commit cowork briefing specs (gaps + sales hunter + pedidos+txt)`

### Gate Fase 0 (DONE)
- [ ] Backfill completou sem erro
- [ ] DeprecationWarning corrigido + commit
- [ ] Docs atualizados + commit
- [ ] Specs commitados
- [ ] verify.py 9/9 PASS

---

## FASE 1 — SALES HUNTER INGEST (GAP 2C)

**Goal:** 13 XLSX SAP em `data/sales_hunter/2026-04-25/morning/` populados em Postgres como **fonte de verdade do faturamento**.

### Pre-conditions
- Fase 0 completa
- D3 = (a) Alembic ✅
- 13 XLSX presentes (verificado: 10MB+ dados reais)

### 1.1 Migration Alembic: tabela `debitos_clientes` + colunas extras
- Arquivo: `backend/alembic/versions/<auto>_add_debitos_clientes_and_enrichment.py`
- Schema:
  ```sql
  CREATE TABLE debitos_clientes (
    id, cnpj VARCHAR(14), cod_pedido, nro_nfe, parcela,
    data_lancamento, data_vencimento, data_pagamento,
    valor FLOAT, dias_atraso, status, fonte, classificacao_3tier,
    created_at
  );
  CREATE INDEX idx_debitos_cnpj, idx_debitos_status;
  ```
- ALTER `clientes`: `total_debitos`, `pct_devolucao`, `total_devolucao`, `risco_devolucao`
- ALTER `produtos`: `subcategoria`, `unidade_embalagem`, `qtd_por_embalagem`, `peso_bruto_kg`, `codigo_ncm`, `fat_total_historico`, `curva_abc_produto` (preparando Fase 4)
- **Validar:** `alembic upgrade head` ok + `alembic downgrade -1` testado + `alembic upgrade head` reaplica
- Commit: `feat(db): alembic migration for debitos_clientes + clientes/produtos enrichment`

### 1.2 Backend models + schemas
- `backend/app/models/debito_cliente.py` (novo)
- `backend/app/models/__init__.py` registra
- Atualizar `cliente.py` e `produto.py` com novas colunas
- Commit: `feat(models): DebitoCliente + extra fields on Cliente/Produto`

### 1.3 Script `scripts/ingest_sales_hunter.py` (novo, ~800 linhas)
**Padrão:** mesmo do `sync_deskrio_to_db.py` (env-aware, ImportJob tracking, idempotente)

8 sub-fases:
- **1.3.1** Phase 1: descobrir último diretório `data/sales_hunter/YYYY-MM-DD/morning/`
- **1.3.2** Phase 2: `fat_produto` CWB+VV → upsert `produtos`. Dedup CWB+VV, soma `fat_total_historico`
- **1.3.3** Phase 3: `fat_cliente` CWB+VV → upsert `clientes`. CPF→CNPJ zfill(14). Dedup CWB+VV (somar). DE-PARA estado→UF
- **1.3.4** Phase 4: `fat_nf_det` CWB+VV → insert `vendas` + `venda_itens`. Filtrar tipo_documento="Venda (F2B)". Dedup por (cnpj, numero_pedido, data_pedido). Parse DD/MM/YYYY. Batch insert (~50K)
- **1.3.5** Phase 5: `pedidos_produto` CWB → enriquecer `vendas` com `consultor` (col 9). VV pula
- **1.3.6** Phase 6: `debitos` CWB+VV → insert `debitos_clientes`. Calcular dias_atraso e status. UPDATE `clientes.total_debitos`
- **1.3.7** Phase 7: `devolucao_cliente` CWB+VV → UPDATE `clientes` (pct_devolucao, total_devolucao, risco_devolucao)
- **1.3.8** Phase 8: VALIDAÇÃO `fat_empresa`: `SUM(clientes.faturamento_total) == fat_empresa.total_faturado` ± 0.5%
- **1.3.9** Phase 9: recalcular Curva ABC com dados SAP
- **1.3.10** Phase 10: gerar `extraction_report.json` + atualizar ImportJob

**ImportJob tipo:** `'SALES_HUNTER'`

**Critérios de aceite:**
- Idempotência: rerun não duplica
- CPF (11d) detectado e normalizado para 14 com zfill
- CWB+VV deduplicados em `clientes`/`produtos`, vendas separadas
- Validação fat_empresa passa (divergência <0.5%)
- Sample query: top 10 clientes por faturamento_total reais

**Esforço:** Subagent deep-executor opus, ~2.5h. Briefing exaustivo com mapping field-by-field do Doc 1 GAP 2C.

### 1.4 Smoke tests isolados
- Subprocesso 1: testar Phase 2 (`fat_produto` only)
- Subprocesso 2: testar Phase 3 (`fat_cliente` only)
- Subprocesso 3: testar Phase 4 (`fat_nf_det` parcial 100 NFs)

### 1.5 Run real + validação
```bash
python scripts/ingest_sales_hunter.py --date 2026-04-25
```
- Validar:
  - `SELECT SUM(faturamento_total) FROM clientes` ≈ R$ 2.091.000 ± 0.5%
  - `SELECT COUNT(*) FROM vendas WHERE fonte='SAP'` (esperado ~25-50K)
  - `SELECT COUNT(*) FROM produtos WHERE peso_bruto_kg IS NOT NULL` (esperado ~275)
  - `SELECT COUNT(*) FROM debitos_clientes WHERE status='VENCIDO'`

### 1.6 Adicionar etapa ao `daily_pipeline.py`
- Inserir `('sales_hunter_ingest', [...])` ENTRE snapshot e ingest_deskrio
- Commit: `feat(pipeline): add sales_hunter_ingest step to daily_pipeline`

### 1.7 verify.py update
- Adicionar `[10] Sales Hunter integrity` check
- Commit: `feat(verify): add Sales Hunter integrity check`

### Gate Fase 1 (DONE)
- [ ] Migration aplicada + rollback testado
- [ ] Modelos atualizados, ImportJob `tipo='SALES_HUNTER'` registrado
- [ ] `ingest_sales_hunter.py` rodou full → faturamento ≈ R$ 2.091.000
- [ ] Idempotência: rerun = 0 inseridos novos
- [ ] verify.py 10/10 PASS
- [ ] Commits atômicos (1.1, 1.2, 1.3, 1.6, 1.7)

### Rollback
- `alembic downgrade -1` desfaz schema
- `DELETE FROM vendas WHERE fonte='SAP' AND created_at > '2026-04-25 18:00'`
- Snapshot pré-fase em `data/backups/pre_fase1.json`

---

## FASE 2 — BACKFILL DESKRIO COMPLETO (GAP 2A)

**Goal:** 24 dias de Deskrio em Postgres, idempotente.

### Pre-conditions
- Fase 0 completa
- D6 = (b) `--skip-contatos` ✅

### 2.1 Adicionar flag `--skip-contatos` ao `sync_deskrio_to_db.py`
- SyncContatos é o gargalo (12min fuzzy match). Pular reduz para 30s/dia
- Commit: `feat(scripts): add --skip-contatos flag for fast backfill reruns`

### 2.2 Backfill 21 dias restantes
```bash
python scripts/backfill_deskrio.py --since 2026-04-02 --skip-contatos
```
- ImportJobs: id 4-24
- Esforço wall time: ~30min

### 2.3 Validação
- `SELECT tipo, status, COUNT(*) FROM import_jobs GROUP BY tipo, status` → todos CONCLUIDO
- `SELECT COUNT(DISTINCT cnpj) FROM log_interacoes WHERE tipo_contato='WHATSAPP'`
- Range: `MIN(data_interacao), MAX(data_interacao)`

### 2.4 D1 — Auditar 21.345 logs SQLite local
- Script novo `scripts/audit_legacy_sqlite_logs.py`
- Classificar tier dos 21.345 logs
- Importar só REAL+SINTÉTICO via `scripts/migrate_legacy_logs.py`
- Descartar ALUCINACAO

### Gate Fase 2 (DONE)
- [ ] 24 ImportJobs DESKRIO CONCLUIDO
- [ ] Idempotência cross-day verificada
- [ ] Range datas log_interacoes WHATSAPP cobre 30+ dias
- [ ] Logs legados auditados e migrados
- [ ] verify.py 10/10 PASS

---

## FASE 3 — CNPJ BRIDGE UNIFICADO (GAP 4)

**Goal:** Tabela formal `cnpj_bridge` consolidando Mercos + SAP + Deskrio.

### Pre-conditions
- Fases 1 e 2 completas

### 3.1 Migration Alembic: tabela `cnpj_bridge`
```sql
CREATE TABLE cnpj_bridge (
  cnpj VARCHAR(14) PRIMARY KEY,
  mercos_id INTEGER, deskrio_contact_id INTEGER, sap_codigo VARCHAR(20),
  deskrio_phone VARCHAR(20), sources TEXT,
  created_at, updated_at
);
```
- Commit: `feat(db): alembic migration for cnpj_bridge table`

### 3.2 Script `scripts/build_cnpj_bridge.py`
- Lê `data/mercos_clientes_completo.json`, dados SAP em DB, `data/deskrio/cnpj_bridge.json`
- Cruza por CNPJ normalizado
- Idempotente (UPSERT por cnpj)

### 3.3 Validação
- `SELECT sources, COUNT(*) FROM cnpj_bridge GROUP BY sources`
- Cobertura esperada: ~7.000-8.000 CNPJs únicos

### 3.4 Endpoint backend `/api/cnpj-bridge/{cnpj}`
- Retorna visão 360° de um CNPJ

### Gate Fase 3 (DONE)
- [ ] cnpj_bridge populado, cobertura documentada
- [ ] Endpoint /api/cnpj-bridge/{cnpj} retorna dados consolidados
- [ ] Sample query mostra cnpj com sources='mercos,sap,deskrio'

---

## FASE 4 — PEDIDOS + TXT SAP (Doc 2)

**Goal:** Vendedor cria pedido no CRM → exporta TXT formato SAP → importa Sales Hunter (zero digitação).

### Pre-conditions
- Fase 1 completa (produtos enriquecidos)
- D4 = (a) Alembic ✅
- Arquivo de referência `19465816.txt` disponível

### Onda 1 — Backend (5 commits)

#### 4.1.1 Migration Alembic: `pedidos` + `pedido_itens`
- Schema completo Doc 2 §3.1 e §3.2
- Commit: `feat(db): alembic migration for pedidos + pedido_itens`

#### 4.1.2 Models `Pedido`, `PedidoItem`
- `backend/app/models/pedido.py`
- `backend/app/models/pedido_item.py`
- Two-Base: pedido = VENDA, valor R$ obrigatório

#### 4.1.3 Script `scripts/enrich_produtos.py`
- Popula EAN, peso_bruto_kg, subcategoria, curva_abc_produto

#### 4.1.4 Service `backend/app/services/pedido_export_service.py`
- 3 métodos: `gerar_txt_sap()`, `gerar_pdf()`, `gerar_xlsx()`
- TXT: HEADER 315 + SUBHEADER 45 + CONTROLE 122 + ITENS 330×N + FOOTER 122
- Funções aux: `fmt_val_10000`, `fmt_qty_100`, `fmt_int`, `pad_right`, `pad_left_zero`

#### 4.1.5 **Validação contra arquivo real `19465816.txt`** (CRÍTICO N3)
- `tests/test_txt_sap_format.py`
- Carregar TXT, parsear, criar registros temp
- Regenerar TXT, **comparar BYTE-A-BYTE** com original
- Diff = 0 bytes ✅

### Onda 2 — API (3 commits)

#### 4.2.1 Routes `routes_pedidos.py`
- POST/GET/PATCH `/api/pedidos`
- POST `/api/pedidos/{id}/exportar`
- GET `/api/pedidos/{id}/download/{formato}`

#### 4.2.2 Routes `routes_produtos.py` atualizar
- Filtros: categoria, subcategoria, ativo, curva_abc

#### 4.2.3 Validation gates
- Pre-export: itens com codigo_sap, CNPJ válido, totais batem
- Post-export: arquivo válido, formato correto

### Onda 3 — Frontend (5 commits)

- 4.3.1 `/produtos` (catálogo)
- 4.3.2 `/produtos/[id]` (detalhe)
- 4.3.3 `/pedidos` (lista)
- 4.3.4 `/pedidos/novo` (wizard 4 steps)
- 4.3.5 `/pedidos/[id]` (detalhe + export)

### Onda 4 — Testes E2E (1 commit)

#### 4.4.1 `tests/e2e/test_pedido_completo.py`
1. Criar pedido via API com 41 itens reais
2. Exportar TXT
3. Comparar com `19465816.txt` byte-a-byte
4. Reimportar TXT, validar dados

### Gate Fase 4 (DONE)
- [ ] Migration aplicada + rollback testado
- [ ] TXT gerado IDÊNTICO ao `19465816.txt` (diff=0 bytes)
- [ ] PDF e XLSX renderizam corretamente
- [ ] E2E test passa
- [ ] Frontend wizard funciona em browser real
- [ ] Two-Base respeitada

---

## FASE 5 — POSTGRESQL FORMALIZADO (GAP 3)

**Goal:** SQLite local descontinuado, Postgres Neon = único source.

### Pre-conditions
- Fases 1-4 completas

### 5.1 Audit migrations
- `alembic current` em PROD = head?
- Comparar schema PROD vs models/__init__.py

### 5.2 Decommission SQLite local
- Atualizar `backend/app/database.py`: remover fallback SQLite (env-var only)
- Commit: `refactor(db): require DATABASE_URL, deprecate SQLite local fallback`

### 5.3 Backup automatizado Neon
- Configurar Neon point-in-time recovery (24h)
- Script `scripts/db_backup.py`
- Adicionar etapa ao `daily_pipeline.py`

### Gate Fase 5 (DONE)
- [ ] Backend exige DATABASE_URL
- [ ] Backup diário rodando
- [ ] Disaster recovery testado

---

## FASE 6 — FRONTEND DADOS REAIS (GAP 5)

**Goal:** 22 páginas exibindo dados reais (não SEED).

### Pre-conditions
- Fases 1-4 completas (banco populado)

### 6.1 Mapeamento endpoint × página (audit)
- Tabela completa Doc 1 §GAP 5 — 22 páginas

### 6.2 Priorização
- **P1:** Dashboard, Carteira, Pipeline, Pedidos, Sinaleiro (5)
- **P2:** Produtos, Vendas, Inbox, Projeção, Relatórios (5)
- **P3:** Redes, RNC, Tarefas, Atualizações, Admin × 5 (10)

### 6.3 Validação por página (P1 primeiro)
- Carregar em browser
- Conferir com query SQL direta
- Smoke test: ações principais funcionam

### 6.4 Correção de mismatches
- Schema frontend vs backend desalinhado
- Endpoints retornando NULL inesperado

### 6.5 Testes E2E Playwright
- 1 happy path por página P1 (5 testes)
- 1 erro path por página P1 (5 testes)

### Gate Fase 6 (DONE)
- [ ] 5 páginas P1 com dados 100% reais
- [ ] 5 páginas P2 funcionais
- [ ] 10 páginas P3 sem crash
- [ ] 10 testes E2E passam
- [ ] Smoke test login → carteira → criar atendimento → exportar

---

## FASE 7 — SCHEDULE + DEPLOY PROD (GAP 6)

**Goal:** Pipeline diário rodando automaticamente em PROD.

### Pre-conditions
- Fases 1-6 completas
- D2 = (a) GitHub Actions ✅

### 7.1 Setup GitHub Actions cron
- `.github/workflows/daily_pipeline.yml`
- Cron: `0 10 * * *` (7h Brasília = 10h UTC)
- Secrets: `DATABASE_URL`, `DESKRIO_API_TOKEN`, `SH_PASSWORD`
- Commit: `ci: add daily_pipeline GitHub Action`

### 7.2 Healthcheck endpoint
- `GET /api/health`: status DB + última extração + última ingestão
- Commit: `feat(api): /api/health endpoint`

### 7.3 Monitoring básico
- ImportJob ERRO últimas 24h → alerta
- Faturamento divergência >0.5% → alerta

### 7.4 Deploy formal
- Verificar env vars em Vercel
- Validar deploy de branch master
- Verificar tier Neon (0.5GB suficiente?)

### Gate Fase 7 (DONE)
- [ ] Pipeline rodou ao menos 1x via scheduler
- [ ] /api/health retorna OK
- [ ] Alerta dispara em job ERRO
- [ ] Deploy URL testada com login real

---

## FASE 8 — VALIDAÇÃO E2E + ACEITAÇÃO

**Goal:** 100% precisão confirmada, projeto entregue.

### 8.1 E2E completo manual (Leandro)
1. Login → dashboard com dados reais
2. Carteira → buscar cliente real → ver histórico WhatsApp + vendas
3. Pipeline → mover card kanban
4. Pedidos → criar pedido com 5 produtos → exportar TXT
5. Sales Hunter → importar TXT gerado → validar NF gerada no SAP
6. Inbox → ver mensagens reais via Deskrio LIVE

### 8.2 Performance benchmarks
- `/api/clientes` (lista 6.318): <500ms
- `/api/atendimentos?cnpj=X`: <200ms
- Daily pipeline completo: <30min

### 8.3 Auditoria de regras
- ✅ R1: Two-Base
- ✅ R5: 100% CNPJ string 14d
- ✅ R8: Zero ALUCINACAO em produção
- ✅ R9: Faturamento ≈ R$ 2.091.000 ± 0.5%

### 8.4 Documentação final
- README.md, RUNBOOK.md, .planning/COMPLETED.md

### 8.5 Handoff
- Tour 30min com Leandro
- Vídeo das funcionalidades P1
- Cheatsheet

### Gate Fase 8 (DONE — ACEITAÇÃO FINAL)
- [ ] E2E manual passou em todas as 6 etapas
- [ ] Performance benchmarks OK
- [ ] Auditoria de regras 4/4 PASS
- [ ] Documentação completa
- [ ] Leandro assina aceitação

---

## GATES TRANSVERSAIS

Antes de cada fase declarar DONE, **OBRIGATÓRIO**:

```
1. python scripts/session_boot.py        (7 PASS)
2. python scripts/compliance_gate.py     (9 PASS)
3. python scripts/verify.py --all        (todos PASS)
4. git status                             (working tree limpo OU mudanças intencionais)
5. git log                                (commits atômicos da fase)
6. Smoke test específico da fase         (artefato funciona)
7. Detector de Mentira N1+N2+N3          (existe, real, conectado)
```

Se qualquer falhar: **NÃO AVANÇAR**, corrigir primeiro.

---

## RESUMO EXECUTIVO

| Fase | Goal | Esforço | Bloqueia | Critério DONE |
|---|---|---|---|---|
| 0 | Preparação + L3 | 1h | Tudo | Decisões + boot OK |
| 1 | Sales Hunter SAP | 4h | 3, 6 | Faturamento ≈ R$2.091K |
| 2 | Backfill Deskrio | 1-5h | 6 | 24 jobs CONCLUIDO |
| 3 | CNPJ Bridge | 2h | 4 | Cobertura 360° |
| 4 | Pedidos+TXT | 8h | 6 | TXT idêntico ao original |
| 5 | PG formaliza | 2h | 7 | Backup + DR testado |
| 6 | Frontend real | 6h | 7 | 5 páginas P1 reais |
| 7 | Schedule+Deploy | 2h | 8 | Pipeline auto + health |
| 8 | Validação E2E | 2h | — | Aceitação Leandro |
| **TOTAL** | | **~28h** | | |

---

## MITIGAÇÃO DE RISCOS

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Migration Alembic falha em PROD | Média | Alto | Testar downgrade antes em dev |
| Backfill duplica dados | Baixa | Alto | Idempotência via LIKE pattern, já validada |
| TXT SAP não bate byte-a-byte | Média | Crítico | Comparação direta, fix iterativo |
| Faturamento diverge >0.5% | Baixa | Alto | Validação fat_empresa em Phase 8 |
| Token Deskrio expira | Baixa | Médio | Renovar (já feito hoje), exp Dez/2026 |
| Frontend quebra com schema novo | Média | Médio | Versionar API, deploy gradual |

---

## RETOMADA PÓS-/CLEAR

Caso a sessão atual encerre, próxima sessão deve:

1. Rodar `python scripts/session_boot.py` + `compliance_gate.py`
2. Ler `.planning/MASTER_PLAN.md` (este arquivo) — fonte de verdade
3. Ler `MEMORY.md` (memória de longo prazo)
4. Verificar status do backfill: `tail /tmp/backfill.log` ou rodar dnv `python scripts/backfill_deskrio.py --since 2026-04-02 --skip-contatos`
5. Próxima fase = aquela onde o gate ainda não fechou

**Próxima ação ao retomar:** verificar Fase 0 está DONE, então atacar **Fase 1 (Sales Hunter Ingest)** com subagent deep-executor opus.

---

## REFERÊNCIAS

- **GAPS_EXCELENCIA_SPEC.md** — Doc 1 do Cowork (gaps + mapping field-by-field SAP)
- **SPEC_PIPELINE_PRODUTOS.md** — Doc 2 do Cowork (pedidos + TXT SAP, decode `19465816.txt`)
- **SALES_HUNTER_EXTRACTION_SPEC.md** — Auth + endpoints Sales Hunter
- **BACKUP_DOCUMENTACAO_ANTIGA.md** — Histórico forense
- **BRIEFING-COMPLETO.md** — Contexto de negócio
- **INTELIGENCIA_NEGOCIO_CRM360.md** — Regras de negócio
- **.claude/rules/000-coleira-suprema.md** — 12 regras invioláveis
- **.planning/DECISIONS.md** — 15 decisões técnicas acumuladas

---

*Criado pelo @aios-master em 2026-04-25 durante sessão massiva de evolução do CRM. Plano sólido, testável, rastreável. Cada fase tem rollback, cada commit é atômico, cada gate é verificável.*
