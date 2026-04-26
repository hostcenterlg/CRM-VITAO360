# SPEC ONDA 1B — Pipeline Diário Automático (Scheduler)

> Sem dados frescos, o CRM é uma foto velha. Este spec resolve a automação.
> Gerado: 26/Abr/2026 | Autor: Cowork (professor/revisor)

---

## CONTEXTO

### O que JÁ existe (não refazer)
- `scripts/daily_pipeline.py` — orquestrador (4 etapas em sequência)
- `scripts/deskrio_daily_snapshot.py` — extrai dados Deskrio API → JSON
- `scripts/ingest_sales_hunter.py` — processa 13 XLSX SAP → banco (1.757 linhas)
- `scripts/sync_deskrio_to_db.py` — sincroniza JSON Deskrio → banco
- `scripts/recalc_score_batch.py` — recalcula score/sinaleiro de todos clientes

### O que FALTA
1. **Scheduler externo** que chame `daily_pipeline.py` automaticamente
2. **Notificação de falha** (se pipeline quebrar, Leandro precisa saber)
3. **`scripts/download_sales_hunter.py`** — PRECISA SER CRIADO (hoje é curl manual)
4. **Log persistente** para debug pós-mortem

---

## OPÇÕES DE SCHEDULER (escolher UMA)

### Opção A: GitHub Actions Cron (RECOMENDADA)

**Por que:** Já tem repo no GitHub. Zero infraestrutura extra. Gratuito (2.000 min/mês).

```yaml
# .github/workflows/daily-pipeline.yml
name: Daily Pipeline CRM

on:
  schedule:
    # 07:00 BRT = 10:00 UTC (antes da equipe comercial começar)
    - cron: '0 10 * * 1-5'  # Seg-Sex apenas
  workflow_dispatch:  # Permite rodar manualmente

env:
  DATABASE_URL: ${{ secrets.DATABASE_URL_NEON }}
  DESKRIO_TOKEN: ${{ secrets.DESKRIO_TOKEN }}
  SALES_HUNTER_USER: ${{ secrets.SALES_HUNTER_USER }}
  SALES_HUNTER_PASS: ${{ secrets.SALES_HUNTER_PASS }}

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Step 1 — Deskrio Snapshot
        run: python scripts/deskrio_daily_snapshot.py
        continue-on-error: false

      - name: Step 2 — Sales Hunter Download
        run: python scripts/download_sales_hunter.py
        continue-on-error: true  # OK se falhar (dados SAP atualizam semanalmente)

      - name: Step 3 — Sales Hunter Ingest
        run: python scripts/ingest_sales_hunter.py --skip-validation
        continue-on-error: true

      - name: Step 4 — Deskrio Sync to DB
        run: python scripts/sync_deskrio_to_db.py

      - name: Step 5 — Recalc Scores
        run: python scripts/recalc_score_batch.py

      - name: Step 6 — Verify
        run: python scripts/verify.py --all

      - name: Notify on failure
        if: failure()
        run: |
          echo "Pipeline falhou em $(date)" >> $GITHUB_STEP_SUMMARY
          # TODO: webhook para Slack/WhatsApp do Leandro
```

**Secrets necessários no GitHub:**
| Secret | Valor | Onde encontrar |
|--------|-------|---------------|
| DATABASE_URL_NEON | `postgresql://...@...neon.tech/...` | Dashboard Neon |
| DESKRIO_TOKEN | JWT token (exp Set/2028) | Já extraído, verificar validade |
| SALES_HUNTER_USER | `leandro@maisgranel.com.br` | Login Sales Hunter |
| SALES_HUNTER_PASS | senha | Leandro sabe |

### Opção B: Vercel Cron (alternativa se já usa Vercel Pro)

```json
// vercel.json
{
  "crons": [{
    "path": "/api/cron/daily-pipeline",
    "schedule": "0 10 * * 1-5"
  }]
}
```

**Problema:** Vercel cron tem timeout de 60s (free) ou 300s (Pro). Pipeline demora ~5-10min. Não é viável sem Pro.

### Opção C: Render Cron Job

Se migrar backend para Render no futuro, usar Cron Job nativo.

**RECOMENDAÇÃO FINAL: Opção A (GitHub Actions).** Zero custo, zero infraestrutura, já integrado.

---

## SCRIPT FALTANTE: download_sales_hunter.py

### O que faz
Automatiza o download dos 13 XLSX do Sales Hunter via curl (hoje é manual).

### Spec

```python
# scripts/download_sales_hunter.py
"""
Baixa relatórios SAP via Sales Hunter API.
Salva em data/sales_hunter/{YYYY-MM-DD}/morning/

Auth: POST https://api.saleshunter.com.br/login
  body: {"email": SALES_HUNTER_USER, "password": SALES_HUNTER_PASS}
  response: {"token": "..."}

Download: GET https://api.saleshunter.com.br/reports/{tipo}
  headers: Authorization: Bearer {token}
  params: empresa=[12,13], dataInicio=YYYY-MM-DD, dataFim=YYYY-MM-DD

Tipos de relatório (DECORAR):
  - RelatorioDeFaturamentoPorCliente (fat_cliente)
  - RelatorioDeFaturamentoNotaFiscalDetalhado (fat_nf_det)
  - RelatorioDeFaturamentoPorProduto (fat_produto)
  - RelatorioDeFaturamentoPorEmpresa (fat_empresa)
  - RelatorioDeDebitos (debitos)
  - RelatorioDeDevolucaoPorCliente (devolucao_cliente)
  - RelatorioDePedidosPorProduto (pedidos_produto)

Empresas: 12 (CWB), 13 (VV)
Datas: formato YYYY-MM-DD (NÃO DD/MM/YYYY — bug já resolvido)

Idempotente: se arquivo já existe para hoje, skip.
"""

RELATORIOS = [
    ("fat_cliente", "RelatorioDeFaturamentoPorCliente"),
    ("fat_nf_det", "RelatorioDeFaturamentoNotaFiscalDetalhado"),
    ("fat_produto", "RelatorioDeFaturamentoPorProduto"),
    ("fat_empresa", "RelatorioDeFaturamentoPorEmpresa"),
    ("debitos", "RelatorioDeDebitos"),
    ("devolucao_cliente", "RelatorioDeDevolucaoPorCliente"),
    ("pedidos_produto", "RelatorioDePedidosPorProduto"),
]

EMPRESAS = [
    ("cwb", 12),
    ("vv", 13),
]

# Total: 7 tipos × 2 empresas = 14 downloads
# Timeout por download: 120s (fat_nf_det é grande, ~2.4MB)
# Retry: 2 tentativas com 30s intervalo
# Se HTML retornado ao invés de XLSX: log warning, skip (bug conhecido)
```

### Referência: SALES_HUNTER_EXTRACTION_SPEC.md
Já existe spec detalhada com endpoints, formato de resposta, e exemplos.

---

## NOTIFICAÇÃO DE FALHA

### Mínimo viável (GitHub Actions)
O próprio GitHub envia email se workflow falha. Leandro (hostcenter.lg@gmail.com) precisa ter notificações ativadas no repo.

### Futuro (quando tiver WhatsApp integrado)
Webhook POST para número do Leandro via API Deskrio ou Evolution API.

---

## LOGS

### Formato
```
[2026-04-26 07:00:01] PIPELINE INÍCIO
[2026-04-26 07:00:05] [snapshot] OK — 15.632 contatos, 445 tickets
[2026-04-26 07:02:30] [sales_hunter] OK — 13 XLSX baixados (10.2MB)
[2026-04-26 07:05:45] [ingest] OK — 5.711 vendas, 8.164 clientes, 312 produtos
[2026-04-26 07:06:10] [recalc] OK — 661 scores recalculados
[2026-04-26 07:06:15] PIPELINE CONCLUÍDO em 374s
```

### Persistência
- GitHub Actions: logs ficam no Actions tab (90 dias de retenção)
- Opcional: salvar em `data/pipeline_logs/{YYYY-MM-DD}.log`

---

## CRONOGRAMA DE EXECUÇÃO

| Horário BRT | Ação | Duração |
|-------------|------|---------|
| 07:00 | Pipeline inicia (GitHub Actions) | — |
| 07:01 | Snapshot Deskrio | ~60s |
| 07:02 | Download Sales Hunter | ~150s |
| 07:05 | Ingest Sales Hunter | ~180s |
| 07:08 | Sync Deskrio → DB | ~60s |
| 07:09 | Recalc Scores | ~30s |
| 07:10 | Verify | ~15s |
| 07:10 | Pipeline concluído | ~10min total |

Equipe comercial começa ~08:00. Dados frescos disponíveis 1h antes.

---

## VALIDAÇÃO

### Nível 1 — Existência
- [ ] `.github/workflows/daily-pipeline.yml` existe
- [ ] `scripts/download_sales_hunter.py` existe
- [ ] Secrets configurados no GitHub repo

### Nível 2 — Substância
- [ ] Workflow roda manualmente (workflow_dispatch) sem erro
- [ ] Dados no banco são mais recentes que ontem
- [ ] Nenhum step é stub (todos processam dados reais)

### Nível 3 — Conexão
- [ ] Pipeline atualiza banco Neon PROD
- [ ] Frontend mostra dados atualizados após pipeline
- [ ] Falha no pipeline envia notificação
- [ ] verify.py roda e passa no final

---

*Spec revisada. VSCode implementa: 1) download_sales_hunter.py, 2) daily-pipeline.yml, 3) testar manualmente.*
