# CRM VITAO360

**Motor de Inteligencia Comercial para VITAO Alimentos**

CRM inteligente para distribuidora B2B de alimentos naturais. Transforma dados de vendas, WhatsApp e ERP em agenda diaria priorizada, score de clientes e inteligencia artificial para a equipe comercial.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14 (App Router), React 18, Tailwind CSS, Recharts |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic 2 |
| Banco | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose, bcrypt) |
| IA | 10 agentes comerciais (template-based, Anthropic API opcional) |
| WhatsApp | Deskrio API (bidirecional) |
| Deploy | Vercel (frontend + serverless backend) |
| CI/CD | GitHub Actions (pytest + tsc + build) |
| PWA | manifest.json, icones, install prompt |

## Features

### CRM Core
- **Carteira** — 1.581 clientes com 9 dimensoes calculadas automaticamente
- **Motor de Regras** — 92 combinacoes SITUACAO x RESULTADO gerando acoes prescritas
- **Score v2** — 6 fatores ponderados (Urgencia 30%, Valor 25%, Follow-up 20%, Sinal 15%, Tentativa 5%, Situacao 5%)
- **Prioridade P1-P7** — do Namoro Novo ao Prospeccao
- **Agenda Inteligente** — 40 clientes/dia priorizados por Score
- **Sinaleiro** — saude do cliente (VERDE/AMARELO/VERMELHO/ROXO)
- **Pipeline Kanban** — 14 estagios com drag-and-drop

### Dashboard (9 abas)
- Resumo, Operacional, Funil, Performance, Saude, Redes, Motivos, Produtividade, **Indicadores Mercos**
- Filtros globais: mes/ano/vendedor
- Widget "Insight do Dia" com IA

### 10 Agentes IA
1. Briefing pre-ligacao (historico + script + sugestao)
2. Mensagem WhatsApp personalizada por situacao
3. Resumo semanal do consultor
4. Risco de Churn (5 fatores, BAIXO→CRITICO)
5. Sugestao de produto (cross-sell/up-sell)
6. Analise de sentimento WhatsApp
7. Previsao de fechamento (probabilidade %)
8. Coach de vendas (performance + recomendacoes)
9. Alerta de oportunidade (REATIVACAO/UPSELL/PROSPECT/CROSS_SELL)
10. Dashboard IA (KPIs + insight do dia)

### Integracoes
- **Deskrio** — Inbox WA bidirecional (enviar + receber), webhook tempo real
- **Mercos** — Sync diario indicadores/pedidos/carteira
- **Pipeline automatico** — Orquestrador sync Deskrio→Mercos→Recalculate

### Infra
- Notificacoes in-app (sino com badge, 4 tipos alerta)
- Busca global Ctrl+K (clientes/produtos/pedidos)
- Atalhos teclado (N/A/C/I)
- Mobile-first (sidebar colapsavel, bottom sheets)
- Skeleton loading + ErrorBoundary global
- PWA instalavel
- CI/CD GitHub Actions
- Logging JSON estruturado (prod)

## Arquitetura

```
FONTES                          BACKEND (FastAPI)              FRONTEND (Next.js)
Mercos ──┐                      ┌─ /api/clientes              ┌─ Dashboard (9 abas)
SAP    ──┼─→ Pipeline ──→ DB ──→├─ /api/dashboard (18)        ├─ Carteira
Deskrio ─┘   Orchestrator       ├─ /api/ia (10 agentes)       ├─ Pipeline Kanban
                                ├─ /api/whatsapp (7)          ├─ Agenda
             Motor Regras ──→   ├─ /api/pipeline (5)          ├─ Inbox WA
             Score v2     ──→   ├─ /api/projecao              ├─ Projecao
             Sinaleiro    ──→   ├─ /api/sinaleiro             ├─ /ia (9 cards)
             Agenda       ──→   └─ ... (103 rotas total)      └─ /admin (4 paginas)
```

## Setup Local

```bash
# Clone
git clone https://github.com/hostcenterlg/CRM-VITAO360.git
cd CRM-VITAO360

# Backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env  # editar valores
uvicorn backend.app.main:app --reload --port 8000

# Frontend (outro terminal)
cd frontend && npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev  # http://localhost:3000
```

## Login

| Email | Role | Acesso |
|-------|------|--------|
| leandro@vitao.com.br | admin | Tudo |
| daiane@vitao.com.br | gerente | CRM + Gestao |
| manu@vitao.com.br | consultor | CRM |
| larissa@vitao.com.br | consultor | CRM |
| julio@vitao.com.br | consultor_externo | CRM parcial |

## Regras Inviolaveis

| # | Regra |
|---|-------|
| R1 | **Two-Base**: VENDA=R$, LOG=R$0.00 — NUNCA misturar |
| R2 | **CNPJ**: String 14 digitos zero-padded — NUNCA float |
| R7 | **Faturamento 2025**: R$ 2.091.000 (tolerancia 0.5%) |
| R8 | **Zero fabricacao**: 558 registros ALUCINACAO catalogados |

## Testes

```bash
python -m pytest backend/tests/ -q  # 737 testes
python scripts/verify.py --all      # 6 PASS, 0 FAIL
```

## Deploy

- **Frontend**: https://intelligent-crm360.vercel.app
- **Backend API**: Vercel serverless (`api/index.py`)
- **Swagger**: /docs

---

Construido com Claude Code. 257 commits. 16 meses de desenvolvimento.
