# HANDOFF — Sessão Interrompida para Reinício

> **Criado:** 2026-04-26 ~15:20 BRT
> **Motivo:** Reinício de máquina solicitado pelo Leandro
> **Próxima sessão:** Continuar BLOCO 2 — finalizar deploy PROD

---

## ✅ ESTADO ATUAL — TUDO ESTÁVEL

### Git (master local)
```
HEAD: e180a1a fix(deploy): Neon batching + Vercel bundle size + status_pedido column
origin/master: e180a1a (sincronizado, 0/0 divergence)
```
- 33 commits da Onda 1 já em origin
- Vercel re-deploy concluído
- Working tree: limpo (só untracked não-bloqueante: data/audits/, data/backups/, data/deskrio/, data/sales_hunter/, .claude/scheduled_tasks.lock)

### PROD Neon (consistent, sem transações abertas)
| Métrica | Valor | Observação |
|---|---|---|
| alembic_version | `4db41d4977b6` | ✅ todas 5 migrations aplicadas |
| clientes | 11.764 | zero CNPJ duplicados |
| clientes NULL canal_id | **6.336** | ⏳ precisam classificar |
| vendas SAP | **500 / R$ 434.776** | ⏳ falta 5.211 (era esperado 5.711 / R$ 5.87M) |
| vendas MERCOS | 1.231 / R$ 2.72M | ✅ preservado |
| venda_itens (total) | 1.593 | só SAP parcial |
| debitos_clientes | **0** | ⏳ Phase 6 não rodou |
| produtos | 274 | ✅ Phase 2 OK |
| usuario_canal ACLs | **0** | ⏳ seed pendente |

### Backend PROD
- URL: https://crm-vitao360.vercel.app
- `/health` retorna `{"status":"ok","banco":"postgresql"}`
- `/api/canais` retorna 8 canais (com auth)
- Login admin OK (`leandro@vitao.com.br` / `vitao2026`)

---

## 🎯 RETOMADA — O QUE FALTA NO BLOCO 2

### 1. Continuar `ingest_sales_hunter.py` em PROD
**Problema descoberto:** Neon free tier corta conexões longas via pooler.
**Solução pronta:** usar `DATABASE_URL_UNPOOLED` (já está no `.env.local`).

```bash
# Passo 1: setar URL não-pooler
export DATABASE_URL=$(grep '^DATABASE_URL_UNPOOLED=' .env.local | cut -d= -f2-)
# Validar: deve conter host SEM '-pooler'

# Passo 2: rodar (idempotente — vai pular as 500 vendas SAP já inseridas via ON CONFLICT)
python scripts/ingest_sales_hunter.py --date 2026-04-25
```

ETA: 10-30min. Esperado pós-execução:
- vendas SAP: 5.711 / R$ 5.872.092 (±0.5%)
- venda_itens SAP: ~21.106
- debitos_clientes: > 0

### 2. Classificar 6.336 clientes NULL em PROD
```bash
# 2.1 — DE-PARA automático (MANU/LARISSA/JULIO → DIRETO)
python scripts/classificar_clientes_legado.py

# 2.2 — DAIANE → INTERNO (id=1) — L3#4 já aprovado
# 2.3 — Restantes órfãos → NAO_CLASSIFICADO (id=8) — L3#3 já aprovado
python -c "
import os
from dotenv import load_dotenv; load_dotenv('.env.local')
from sqlalchemy import create_engine, text
eng = create_engine(os.environ['DATABASE_URL_UNPOOLED'], connect_args={'connect_timeout': 30})
with eng.begin() as c:
    r1 = c.execute(text(\"UPDATE clientes SET canal_id=1 WHERE canal_id IS NULL AND consultor='DAIANE'\"))
    print(f'DAIANE → INTERNO: {r1.rowcount}')
    r2 = c.execute(text('UPDATE clientes SET canal_id=8 WHERE canal_id IS NULL'))
    print(f'órfãos → NAO_CLASSIFICADO: {r2.rowcount}')
"
```
Esperado: 0 NULL canal_id após.

### 3. Seed ACLs `usuario_canal`
```bash
python scripts/seed_usuario_canal.py
```
Esperado: 5+ ACLs (manu/larissa/julio→DIRETO, daiane→INTERNO+FOOD).

### 4. verify.py em PROD
```bash
python scripts/verify.py --all
```
Esperado: 10/10 PASS.

### 5. Smoke test 3 perfis
- Admin via login + curl `/api/canais` + `/api/clientes`
- MANU/LARISSA/DAIANE via SQL: counts visíveis por canal

---

## 📋 DECISÕES L3 JÁ APROVADAS (não pedir de novo)

| # | Decisão | Resposta Leandro |
|---|---|---|
| L3#2 | FARMA (61 clientes / R$ 382K) | (B) Manter EM_BREVE |
| L3#3 | 84 órfãos sem canal/consultor | (A) NAO_CLASSIFICADO |
| L3#4 | 194 clientes DAIANE | (B) Tudo INTERNO |
| L3#5 | Bug SAP duplicado | (A) Investigar agora + (b) ignorar VV |
| L3#6 | Status canais EM_BREVE | Falso alarme — não esconde |
| BLOCO 2 | git push + deploy PROD | GO completo |

---

## 🚨 RED FLAGS / OBSERVAÇÕES

1. **Não usar pooler para batch jobs.** `DATABASE_URL` (.env.local) tem pooler — mata transações longas. `DATABASE_URL_UNPOOLED` resolve.

2. **`.vercelignore` foi alterado** (commit `e180a1a`) — exclui `data/` (1.6GB) para caber no Lambda 245MB. NÃO mexer sem testar deploy.

3. **Migration `d2d415fcc93e` foi tornada idempotente** (commit `93b2914`) — usa `ADD COLUMN IF NOT EXISTS` para Postgres.

4. **Cherry-pick duplicado já resolvido** — rebase fez auto-skip do nosso 008e96b (igual ao 1000a38 do PR #1).

5. **Faturamento Mercos baseline confirmado** — R$ 2.102.419 em 2025, dentro de 0.5% do R$ 2.091.000.

---

## 🚀 PROMPT PARA INICIAR PRÓXIMA SESSÃO

```
@aios-master
Reiniciei a máquina. Lê HANDOFF_REINICIO.md e retoma do BLOCO 2 — finalizar deploy PROD (continuar ingest SAP com DATABASE_URL_UNPOOLED, classificar 6.336 NULL, seed ACLs, verify, smoke test).

Decisões L3 já aprovadas — NÃO pedir de novo.
```

---

## 📂 ARTEFATOS DESTA SESSÃO

- `data/audits/B1_faturamento_reconciliation.md` — investigação faturamento R$ 5M (com seção 7 sobre SAP duplicação)
- `data/backups/pre_b14_b16_20260426_104411.db` — banco local pré-classificação DAIANE
- `data/backups/pre_b17exec_20260426_115822.db` — banco local pré-remediação SAP
- `data/backups/neon/pre_b2_snapshot_20260426_125520.json` — snapshot Neon pré-deploy
- `data/backups/neon/pre_be_20260426_181856_snapshot.json` — snapshot Neon pré-finalização

**Pode reiniciar com segurança.**
