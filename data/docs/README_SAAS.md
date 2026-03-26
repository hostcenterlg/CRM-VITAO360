# README — CRM VITAO360 SaaS

**Para qualquer dev, coworker, ou agente que abrir este projeto.**

---

## O QUE E ESTE PROJETO

CRM VITAO360 SaaS e a migracao de um CRM Excel operacional (40 abas, 200K+ formulas, 5.8MB) para uma plataforma web de inteligencia comercial.

**NAO e um CRM passivo.** E um sistema AUTONOMO PREDITIVO que decide quem o consultor deve ligar, o que fazer, e quando voltar. O humano executa. A maquina decide.

Leia obrigatoriamente: `data/docs/FILOSOFIA_CRM_AUTONOMO.md`

---

## ORIGENS

A planilha fonte de verdade:
```
"C:\Users\User\OneDrive\Area de Trabalho\CRM_VITAO360  INTELIGENTE   FINAL OK .xlsx"
```
- 40 abas (16 visiveis + 24 ocultas)
- 1.593 clientes na CARTEIRA (144 colunas)
- 92 combinacoes no Motor de Regras
- 661 clientes no Sinaleiro
- Score v2 com 6 fatores ponderados

Raio-X completo: `data/docs/RAIO_X_PLANILHA_INTELIGENTE_FINAL.md`

---

## STACK TECNICA

| Camada | Tecnologia | Status |
|--------|-----------|--------|
| **Backend** | Python 3.12 + FastAPI | Implementado (rotas, models, services) |
| **Motor** | Python (motor_regras.py, score_engine.py, sinaleiro_engine.py, agenda_engine.py) | Implementado (precisa alinhar com Score v2) |
| **Database** | SQLite (dev) → PostgreSQL (prod) | Schema definido |
| **Frontend** | A definir (Next.js ou React + Vite) | Esqueleto com auth |
| **Integracao** | Deskrio (WhatsApp), Mercos (vendas), SAP (cadastro) | APIs mapeadas |
| **Deploy** | Vercel (front) + Railway (back) | Planejado |

---

## ESTRUTURA DO REPO

```
CRM-VITAO360/
├── backend/                    # FastAPI app
│   ├── app/
│   │   ├── api/               # Rotas (clientes, motor, dashboard, etc)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── security.py        # Auth JWT
│   │   └── main.py            # FastAPI app
│   └── tests/                 # 69 testes
├── scripts/
│   ├── motor/                 # Motor Python operacional
│   │   ├── motor_regras.py    # 92 combinacoes (824 linhas)
│   │   ├── score_engine.py    # Score 6 fatores (855 linhas)
│   │   ├── sinaleiro_engine.py # Sinaleiro 4 cores (922 linhas)
│   │   ├── agenda_engine.py   # Agenda 40-60/dia (1014 linhas)
│   │   ├── classify.py        # Classificacao 3-tier
│   │   └── import_pipeline.py # ETL xlsx → banco
│   ├── session_boot.py        # Boot obrigatorio
│   ├── compliance_gate.py     # Compliance check
│   └── verify.py              # Verificacao pos-build
├── data/
│   ├── intelligence/          # 13 JSONs de inteligencia extraida
│   ├── docs/                  # PRD, Raio-X, Filosofia, Inventario
│   └── output/                # Outputs do pipeline
├── squads/
│   └── crm-saas/              # Squad SaaS (5 agentes)
├── .claude/
│   ├── commands/agents/       # 9 agentes AIOX
│   ├── skills/                # 7 skills especializados
│   └── rules/                 # Coleira Suprema + gates
├── INTELIGENCIA_NEGOCIO_CRM360.md  # Inteligencia de negocio ATUALIZADA
├── BRIEFING-COMPLETO.md            # Contexto do negocio
└── BACKUP_DOCUMENTACAO_ANTIGA.md   # Historico completo
```

---

## DOCUMENTOS OBRIGATORIOS (LER NESTA ORDEM)

1. `data/docs/FILOSOFIA_CRM_AUTONOMO.md` — A alma do produto
2. `INTELIGENCIA_NEGOCIO_CRM360.md` — 9 dimensoes, Score v2, Motor, Regras
3. `data/docs/PRD_SAAS.md` — 14 epicos, 60+ features
4. `data/docs/RAIO_X_PLANILHA_INTELIGENTE_FINAL.md` — 40 abas mapeadas
5. `BRIEFING-COMPLETO.md` — Contexto Vitao Alimentos

---

## REGRAS INVIOLAVEIS (RESUMO)

| # | Regra | Consequencia se violar |
|---|-------|----------------------|
| R1 | Two-Base: VENDA=R$, LOG=R$0.00 | Inflacao 742% |
| R2 | CNPJ = string 14 digitos zero-padded | Perda de precisao |
| R3 | Formulas openpyxl em INGLES | Quebra planilha |
| R4 | Zero dados fabricados (3-tier: REAL/SINTETICO/ALUCINACAO) | 558 registros ja perdidos |
| R5 | Faturamento baseline R$ 2.091.000 (tolerancia 0.5%) | Dados corrompidos |
| R6 | Score v2 e o OFICIAL (Urgencia 30%, Valor 25%, FU 20%, Sinal 15%) | Motor desalinhado |
| R7 | Commits atomicos (1 task = 1 commit) | Historico poluido |
| R8 | Niveis de decisao: L1 autonomo, L2 informar, L3 Leandro aprova | Mudanca nao autorizada |

---

## MAPA: ABA EXCEL → TELA SAAS

| Aba Excel | Tela SaaS | Rota API | Epico PRD |
|-----------|-----------|----------|-----------|
| AGENDA | `/agenda` | GET /api/agenda/{consultor} | E4 |
| CARTEIRA | `/clientes` + `/clientes/{cnpj}` | GET /api/clientes | E6 |
| LARISSA/MANU/JULIO/DAIANE | `/atendimentos` | POST /api/atendimentos | E7 |
| DASHBOARD | `/dashboard` | GET /api/dashboard/kpis | E5 |
| SINALEIRO | `/sinaleiro` | GET /api/clientes?sinaleiro | E3 |
| PROJECAO | `/projecao` | GET /api/projecao | E13 |
| MOTOR DE REGRAS | `/admin/motor` | GET /api/motor/regras | E2 |
| REGRAS | Embedded (dropdowns) | — | E2 |
| RNC | `/rnc` | GET /api/rnc | E14 |
| REDES v2 | `/redes` | GET /api/redes | E5 |

---

## COMO RODAR

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Motor (standalone)
cd scripts/motor
python run_pipeline.py

# Testes
cd backend
python -m pytest tests/ -v

# Boot obrigatorio (toda sessao Claude Code)
python scripts/session_boot.py
python scripts/compliance_gate.py
```

---

## PROXIMOS PASSOS

1. Alinhar Score Engine Python com Score v2 da planilha
2. UX Design completo (todas as telas)
3. Frontend implementation
4. Popular banco com dados reais da planilha
5. Integracoes (Deskrio, Mercos, SAP)
6. Deploy (Vercel + Railway)
