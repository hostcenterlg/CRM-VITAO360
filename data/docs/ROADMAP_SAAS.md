# ROADMAP SAAS — CRM VITAO360
# Plano Consolidado de Implementacao 0% → 100%
# Data: 2026-03-25 | Autor: @aios-master (consolidacao de 4 agentes)
# Fontes: PRD_SAAS.md, ARQUITETURA_SAAS.md, GAP_ANALYSIS.md, UX_SPEC_SAAS.md

---

## RESUMO EXECUTIVO

| Dimensao | Valor |
|----------|-------|
| Estado atual do SaaS | ~8-12% (scaffold read-only) |
| Motor Python | 100% (14 modulos, 92 regras, 8 stages) |
| Gap central | Motor nao executa em tempo real no SaaS |
| Epicos totais | 14 (E1-E14) |
| Features totais | 56 (FR-001 a FR-056) |
| Tabelas no banco | 12 (2 existem, 10 novas) |
| Endpoints API | 60+ (9 existem, 51+ novos) |
| Paginas frontend | 10 (4 existem parciais, 6 novas) |
| **MVP funcional** | **~16 dias (Fases 1-6)** |
| **SaaS completo** | **~30 dias (Fases 1-10)** |

---

## GRAFO DE DEPENDENCIAS

```
                    ┌────────┐
                    │ FASE 1 │ Auth + Models + Alembic
                    │ 3 dias │
                    └───┬────┘
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │ FASE 2 │ │ FASE 3 │ │ FASE 6 │
         │ Motor  │ │ Vendas │ │ Front  │
         │ Regras │ │Two-Base│ │ Login  │
         │ 2 dias │ │ 2 dias │ │ 2 dias │
         └───┬────┘ └───┬────┘ └───┬────┘
             │          │          │
             ▼          ▼          │
         ┌────────────────┐        │
         │    FASE 4      │        │
         │ Score+Sinaleiro│        │
         │    2 dias      │        │
         └───────┬────────┘        │
                 │                 │
                 ▼                 │
         ┌────────────────┐        │
         │    FASE 5      │        │
         │ Agenda Service │        │
         │    1 dia       │        │
         └───────┬────────┘        │
                 │                 │
                 ▼                 ▼
         ┌─────────────────────────────┐
         │         FASE 7              │
         │ Frontend Completo           │
         │ (Atendimento + Timeline +   │
         │  Dashboard + Sinaleiro)     │
         │         5 dias              │
         └─────────────┬───────────────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │ FASE 8 │ │ FASE 9 │ │FASE 10 │
         │ Import │ │Deskrio │ │ Deploy │
         │Pipeline│ │WhatsApp│ │CI/CD   │
         │ 3 dias │ │ 2 dias │ │ 2 dias │
         └────────┘ └────────┘ └────────┘
```

---

## FASES DE IMPLEMENTACAO

### FASE 1 — Fundacao: Auth + Models + Alembic + Seed (3 dias)

**Epicos:** E8 (Auth), E1 (Import parcial)
**Prioridade:** P0 — TUDO depende disso
**Agentes:** @dev (implementacao), @architect (revisao)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 1.1 | Instalar Alembic | Substituir `create_all` em main.py por migrations | 2h |
| 1.2 | Model Usuario | email, nome, hashed_password, role, consultor_nome | 2h |
| 1.3 | Model Venda (Two-Base) | CHECK constraint valor_pedido > 0, CNPJ FK | 2h |
| 1.4 | Model LogInteracao (Two-Base) | Campos calculados pelo motor, CNPJ FK | 2h |
| 1.5 | Model RegraMotor | 92 combinacoes, UQ(situacao, resultado) | 1h |
| 1.6 | Model ScoreHistorico | Snapshots para trend analysis | 1h |
| 1.7 | Models Rede, RNC, Meta, ImportJob | Complementares | 3h |
| 1.8 | Migrations 001-009 | Uma migration por model group | 2h |
| 1.9 | security.py (JWT) | create_token, verify_token, get_current_user, require_role | 3h |
| 1.10 | routes_auth.py | POST login, GET /me, POST /users (admin) | 2h |
| 1.11 | Seed usuarios | Leandro (admin), Manu, Larissa, Daiane (consultor) | 1h |
| 1.12 | Seed regras_motor | Portar 92 combinacoes de motor_regras.py | 2h |

**Entregaveis:**
- 12 tabelas no banco com migrations
- JWT auth funcional (login, roles)
- 4 usuarios criados
- 92 regras no banco

**Criterio de aceite:**
- `POST /api/auth/login` retorna JWT
- `GET /api/auth/me` retorna usuario com role
- Endpoint protegido rejeita sem token (401)
- Alembic `upgrade head` cria todas as tabelas

---

### FASE 2 — Motor de Regras no Backend (2 dias)

**Epicos:** E2 (Motor), E7 (LOG parcial)
**Prioridade:** P0 — Core do CRM, sem isso e read-only
**Agentes:** @dev (port), @qa (validacao 92 combinacoes)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 2.1 | motor_regras_service.py | Port de scripts/motor_regras.py (92 combinacoes) | 4h |
| 2.2 | routes_atendimentos.py | POST /api/atendimentos (registrar interacao) | 4h |
| 2.3 | Fluxo completo POST | Recebe {cnpj, resultado, descricao} → busca situacao → motor calcula 9 dimensoes → insere log_interacoes → atualiza cliente | 4h |
| 2.4 | Testes motor_regras | Portar 69 testes existentes de scripts/tests/ | 4h |

**Fluxo critico (POST /api/atendimentos):**
```
1. Consultor envia: { cnpj, resultado, descricao }
2. Backend busca situacao atual do cliente
3. MotorRegrasService.aplicar(situacao, resultado) → 9 dimensoes
4. INSERT log_interacoes com campos calculados
5. UPDATE cliente (temperatura, fase, estagio_funil, acao_futura)
6. RETURN interacao + campos motor
```

**Criterio de aceite:**
- POST /api/atendimentos retorna 9 dimensoes calculadas
- LogInteracao salva com R$ 0.00 (Two-Base enforcement)
- Cliente atualizado com novos valores do motor
- 92/92 combinacoes testadas

---

### FASE 3 — Vendas Two-Base + Dashboard Expandido (2 dias)

**Epicos:** E5 (Dashboard), parte de E6 (CARTEIRA)
**Prioridade:** P0
**Agentes:** @dev (implementacao), @data-engineer (validacao faturamento)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 3.1 | routes_vendas.py | POST /api/vendas (valor > 0 enforced), GET com filtros | 3h |
| 3.2 | Dashboard KPIs reais | Queries reais em vez de dados do JSON | 3h |
| 3.3 | Dashboard distribuicoes | 6 dimensoes com dados reais | 3h |
| 3.4 | Dashboard funil | Pipeline de vendas por estagio | 2h |
| 3.5 | routes_projecao.py | Meta vs realizado por consultor | 3h |
| 3.6 | test_two_base.py | Guardrail: venda R$0 rejeitada, log sem valor | 2h |

**Criterio de aceite:**
- POST /api/vendas com valor <= 0 retorna 400
- KPIs calculados de dados reais (nao JSON estatico)
- Faturamento total = R$ 2.091.000 (tolerancia 0.5%)
- Two-Base: IMPOSSIVEL criar venda com R$ 0

---

### FASE 4 — Score + Sinaleiro em Tempo Real (2 dias)

**Epicos:** E3 (Score+Sinaleiro)
**Prioridade:** P0
**Agentes:** @dev (port), @qa (validacao pesos)
**Dependencias:** Fase 2 (motor), Fase 3 (vendas)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 4.1 | score_service.py | Port de score_engine.py (6 fatores ponderados) | 3h |
| 4.2 | sinaleiro_service.py | Port de sinaleiro_engine.py (4 cores) | 2h |
| 4.3 | Recalculo automatico | Apos POST atendimento → recalcula score + sinaleiro | 3h |
| 4.4 | POST /api/sinaleiro/recalcular | Batch recalculo (admin) | 2h |
| 4.5 | ScoreHistorico | Snapshot apos cada recalculo | 2h |
| 4.6 | GET /api/clientes/{cnpj}/score-history | Evolucao do score | 2h |
| 4.7 | Testes score + sinaleiro | Validar pesos e thresholds | 2h |

**Criterio de aceite:**
- Score 0-100 calculado com 6 fatores e pesos corretos
- Prioridade P0-P7 atribuida corretamente
- Sinaleiro: VERDE/AMARELO/VERMELHO/ROXO por ratio
- Recalculo dispara apos cada atendimento registrado

---

### FASE 5 — Agenda Inteligente Service (1 dia)

**Epicos:** E4 (Agenda)
**Prioridade:** P0
**Agentes:** @dev
**Dependencias:** Fase 4 (score)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 5.1 | agenda_service.py | Port de agenda_engine.py (40/dia, 20 Daiane) | 3h |
| 5.2 | POST /api/agenda/gerar | Trigger manual geracao de agenda | 2h |
| 5.3 | worker_agenda.py | Cron diario 06:00 BRT com APScheduler | 2h |
| 5.4 | GET /api/agenda/{consultor} expandido | Com acao sugerida, score, prioridade | 1h |

**Criterio de aceite:**
- Agenda gerada com max 40 por consultor (20 Daiane)
- P0 pula fila, P7 nunca na agenda regular
- Ordenacao: P0 → P1 → Score desc
- Cron funcional as 06:00

---

### FASE 6 — Frontend: Login + Protecao de Rotas (2 dias)

**Epicos:** E8 (Auth frontend)
**Prioridade:** P0
**Agentes:** @dev (frontend), @ux (revisao visual)
**Dependencias:** Fase 1 (auth backend)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 6.1 | /login page | Formulario email+senha, LIGHT theme | 3h |
| 6.2 | AuthContext + useAuth | JWT storage, refresh, role check | 3h |
| 6.3 | ProtectedRoute | HOC que redireciona para /login | 2h |
| 6.4 | api.ts expandido | Auth header, interceptor 401, mutations | 3h |
| 6.5 | Sidebar expandida | 10 itens com role-based visibility | 2h |
| 6.6 | Header com user menu | Nome do usuario, role badge, logout | 1h |

**Criterio de aceite:**
- Login funcional, token persiste em localStorage
- Rotas protegidas redirecionam sem token
- Sidebar mostra apenas itens permitidos por role
- Consultor ve apenas seus dados

---

### === MVP FUNCIONAL (Fases 1-6 = ~12 dias) ===

Apos Fase 6, o sistema tem:
- Auth com roles (admin + 3 consultoras)
- Motor de regras executando em tempo real
- Registro de atendimentos com 9 dimensoes calculadas
- Score + Sinaleiro recalculados automaticamente
- Agenda inteligente gerada diariamente
- Dashboard com KPIs reais
- Login e rotas protegidas

**FALTA para 100%:** Frontend de atendimento/timeline, import pipeline, Deskrio, deploy

---

### FASE 7 — Frontend Completo (5 dias)

**Epicos:** E4 (Agenda UI), E5 (Dashboard UI), E6 (CARTEIRA UI), E7 (LOG UI)
**Prioridade:** P1
**Agentes:** @dev (frontend), @ux (componentes)
**Dependencias:** Fase 2-5 (backend completo), Fase 6 (auth frontend)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 7.1 | AtendimentoForm | Select resultado (14 opcoes) + descricao + feedback motor | 4h |
| 7.2 | AgendaCard + tela agenda interativa | Card com posicao, score, acao, click → atendimento | 4h |
| 7.3 | /carteira/[cnpj] — Detalhe cliente | Timeline de interacoes + vendas, score breakdown | 4h |
| 7.4 | TimelineEvent | Componente de timeline com icone por tipo | 3h |
| 7.5 | Dashboard expandido | 6 distribuicoes clicaveis, top 10, funil | 4h |
| 7.6 | KpiCard + ProjecaoChart | Graficos barras meta vs realizado (recharts) | 4h |
| 7.7 | /sinaleiro — Painel de redes | SinaleiroGauge, penetracao por rede, 923 lojas | 4h |
| 7.8 | FilterBar reutilizavel | Consultor, status, ABC, sinaleiro, temperatura | 3h |
| 7.9 | DataTable generico | Sort, pagination, column toggle, export | 4h |
| 7.10 | StatusBadge + AbcBadge + ScoreBar | Variantes com cores exatas (R9) | 3h |
| 7.11 | EmptyState + ConfirmDialog + Loading | Estados de feedback | 2h |
| 7.12 | Responsividade | Desktop (1920), Tablet (768), Mobile (375) | 4h |

**Criterio de aceite:**
- Consultora registra atendimento e ve feedback do motor
- Dashboard CEO com 9 KPIs e 6 distribuicoes
- Detalhe do cliente com timeline completa
- Tema LIGHT com cores exatas (R9)
- Funciona em tablet (consultora em campo)

---

### FASE 8 — Import Pipeline (3 dias)

**Epicos:** E1 (Import), E11 (Mercos parcial), E12 (SAP parcial)
**Prioridade:** P1
**Agentes:** @dev (backend), @data-engineer (validacao)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 8.1 | import_service.py | Port de import_pipeline.py (8 stages) | 6h |
| 8.2 | routes_import.py | POST upload xlsx, GET job status | 3h |
| 8.3 | worker_import.py | Background processing com status updates | 4h |
| 8.4 | /import page | Drag-drop xlsx, progress bar 8 stages | 4h |
| 8.5 | Validacoes import | R10 (Mercos mente), R8 (filtra ALUCINACAO), CNPJ normalize | 3h |
| 8.6 | Testes import | Upload real, validacao 3-tier, faturamento check | 4h |

**Criterio de aceite:**
- Upload xlsx → processamento background → dados no banco
- Progress bar mostra stage atual (1-8)
- ALUCINACAO filtrada automaticamente (558 registros)
- Faturamento pos-import = R$ 2.091.000 (±0.5%)

---

### FASE 9 — Integracao Deskrio/WhatsApp (2 dias)

**Epicos:** E9 (Deskrio)
**Prioridade:** P2
**Agentes:** @dev (API client + webhook)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 9.1 | deskrio_client.py | API client (enviar msg, listar contatos, tickets) | 4h |
| 9.2 | routes_webhooks.py | POST webhook receiver (message.received, ticket.*) | 3h |
| 9.3 | Auto-log WhatsApp | Webhook → busca CNPJ por telefone → cria LogInteracao | 3h |
| 9.4 | worker_deskrio.py | Sync periodico (cada 15min) | 3h |
| 9.5 | UI indicador WhatsApp | Badge na timeline + botao enviar no detalhe cliente | 3h |

**Criterio de aceite:**
- Mensagem WhatsApp recebida → log automatico no CRM
- Envio de mensagem pelo CRM via Deskrio API
- Contatos matcheados por telefone → CNPJ

---

### FASE 10 — Deploy + CI/CD (2 dias)

**Epicos:** E10 (Deploy)
**Prioridade:** P1
**Agentes:** @devops (EXCLUSIVO para push/deploy)

| # | Task | Detalhes | Est. |
|---|------|---------|------|
| 10.1 | Dockerfile backend | Python 3.12 + deps + alembic + uvicorn | 2h |
| 10.2 | Railway setup | PostgreSQL + backend container | 2h |
| 10.3 | Vercel setup | Next.js auto-deploy, env vars | 1h |
| 10.4 | GitHub Actions CI | pytest + build + deploy on push to master | 3h |
| 10.5 | .env producao | DATABASE_URL, JWT_SECRET, CORS_ORIGINS, DESKRIO_KEY | 1h |
| 10.6 | Smoke test producao | Health check, login, criar atendimento, ver dashboard | 3h |
| 10.7 | DNS + SSL | Dominio custom (opcional) | 2h |

**Criterio de aceite:**
- Frontend acessivel via Vercel URL
- Backend acessivel via Railway URL
- PostgreSQL com dados migrados
- CI roda testes antes de deploy
- Login funcional em producao

---

## TIMELINE VISUAL

```
Semana 1       Semana 2       Semana 3       Semana 4       Semana 5       Semana 6
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼────────┤
│ FASE 1 (3d)  │ FASE 4 (2d)  │ FASE 7 ─────────────(5d)──│ FASE 8 (3d)  │F10(2d) │
│ Auth+Models  │ Score+Sinal  │ Frontend Completo          │ Import Pipe  │ Deploy │
│──────────────│──────────────│                             │──────────────│────────│
│ FASE 2 (2d)  │ FASE 5 (1d)  │                             │ FASE 9 (2d)  │        │
│ Motor Regras │ Agenda Svc   │                             │ Deskrio/WA   │        │
│──────────────│──────────────│                             │              │        │
│ FASE 3 (2d)  │ FASE 6 (2d)  │                             │              │        │
│ Vendas+Dash  │ Front Login  │                             │              │        │
├──────────────┼──────────────┼─────────────────────────────┼──────────────┼────────┤
     ▲              ▲                    ▲                        ▲            ▲
     │              │                    │                        │            │
  BACKEND        BACKEND+FE          FRONTEND                 INTEG        DEPLOY
  FUNDACAO       MVP FUNCIONAL       COMPLETO                 DADOS        PROD
```

---

## MOSCOW CONSOLIDADO

### MUST HAVE (MVP — Fases 1-6)

| Feature | Epico | Fase |
|---------|-------|------|
| Auth JWT + roles (admin/consultor) | E8 | F1 |
| 12 models SQLAlchemy + Alembic | E1 | F1 |
| POST /api/atendimentos + motor 92 regras | E2 | F2 |
| Two-Base enforcement (constraint SQL) | E6 | F3 |
| Score 6 fatores + P0-P7 | E3 | F4 |
| Sinaleiro 4 cores | E3 | F4 |
| Agenda 40/dia + cron | E4 | F5 |
| Login page + ProtectedRoute | E8 | F6 |
| Dashboard KPIs reais | E5 | F3 |

### SHOULD HAVE (v1.0 — Fases 7-8)

| Feature | Epico | Fase |
|---------|-------|------|
| AtendimentoForm + motor feedback | E4 | F7 |
| Detalhe cliente + timeline | E6 | F7 |
| Sinaleiro redes (923 lojas) | E3 | F7 |
| Import pipeline xlsx | E1 | F8 |
| Dashboard distribuicoes clicaveis | E5 | F7 |
| Agenda historica | E4 | F7 |
| Redistribuicao de carteira | E4 | F7 |

### COULD HAVE (v1.1 — Fases 9-10)

| Feature | Epico | Fase |
|---------|-------|------|
| Deskrio WhatsApp bidirecional | E9 | F9 |
| Deploy Vercel + Railway | E10 | F10 |
| CI/CD GitHub Actions | E10 | F10 |
| Tendencias temporais | E5 | F7 |
| Meta Balance (+20 prospeccao) | E3 | F4 |

### WON'T HAVE (v2 futuro)

- App mobile nativo
- IA preditiva/generativa
- Asana integration
- Mercos API (manter xlsx por ora)
- SAP API (manter xlsx por ora)
- Multi-tenant
- Exportacao Excel com formulas

---

## RISCOS E MITIGACOES

| # | Risco | Impacto | Mitigacao |
|---|-------|---------|-----------|
| 1 | Two-Base violada no SaaS | CRITICO (742%) | CHECK constraint SQL + service validation + test_two_base.py |
| 2 | Motor port diverge do original | ALTO | Portar 69 testes existentes, comparar output com JSON baseline |
| 3 | ALUCINACAO integrada | ALTO | classificacao_3tier enforced, 558 IDs blacklistados |
| 4 | Faturamento diverge >0.5% | ALTO | Validacao automatica pos-import vs R$ 2.091.000 |
| 5 | CNPJ como float no banco | MEDIO | String(14) + normalizacao em todo input |
| 6 | Manu em licenca Q2 | MEDIO | FR-022 redistribuicao de carteira |
| 7 | Deskrio API instavel | BAIXO | Retry com backoff, fallback manual |
| 8 | SQLite → PostgreSQL issues | BAIXO | Alembic desde dia 1, testes em ambos |

---

## DECISOES TECNICAS (CONSOLIDADAS)

| # | Decisao | Escolha | Motivo |
|---|---------|---------|--------|
| D1 | Backend | FastAPI (Python) | Reutiliza 14 modulos motor sem rewrite |
| D2 | DB sync | SQLAlchemy sync | 489 clientes, complexidade async injustificada |
| D3 | Frontend data | SWR | 4KB, 4 usuarios, fetch puro ja existe |
| D4 | Two-Base | DB constraint + service | Defesa em profundidade |
| D5 | Jobs | APScheduler | Zero infra extra |
| D6 | Migrations | Alembic desde dia 1 | Producao requer versionamento |
| D7 | Auth | JWT stateless | Simples, 8h expiry = jornada comercial |
| D8 | Deploy | Vercel + Railway | Auto-deploy, PostgreSQL managed |
| D9 | Charts | Recharts | React nativo, leve, boa API |
| D10 | Tema | LIGHT only | R9 inviolavel |

---

## DOCUMENTOS DE REFERENCIA

| Documento | Autor | Conteudo |
|-----------|-------|---------|
| `data/docs/PRD_SAAS.md` | @pm | 14 epicos, 56 features, MoSCoW, riscos |
| `data/docs/ARQUITETURA_SAAS.md` | @architect | ERD, 60+ endpoints, models, deploy |
| `data/docs/GAP_ANALYSIS.md` | @analyst | Inventario completo, gaps %, priorizacao |
| `data/docs/UX_SPEC_SAAS.md` | @ux | 10 telas, wireframes, componentes, paleta |

---

## PROXIMO PASSO

Leandro aprova este roadmap → @aios-master delega FASE 1 para @dev com escopo fechado.

**Nivel de decisao: L3 (LEANDRO APROVA)** — Novo roadmap de implementacao SaaS, criacao de tabelas, alteracao de arquitetura.

---

*Consolidado por @aios-master a partir de 4 agentes especializados executados em paralelo.*
*Regras R1-R12 verificadas e incorporadas em todas as fases.*
*Faturamento baseline: R$ 2.091.000 | Two-Base: enforcement em nivel de banco.*
