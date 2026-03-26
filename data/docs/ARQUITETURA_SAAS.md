# ARQUITETURA SAAS — CRM VITAO360
# Documento Tecnico Completo
# Versao: 1.0 | Data: 2026-03-25
# Autor: @architect | Aprovacao: Leandro (L3)

---

# 1. VISAO GERAL

```
┌─────────────────────────────────────────────────────────────────────┐
│                       INTERNET / USUARIOS                           │
│         Leandro (admin) | Manu | Larissa | Daiane | (Julio=OFF)    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS
┌───────────────────────────────┼─────────────────────────────────────┐
│  FRONTEND — Vercel            │                                     │
│  Next.js 14 (App Router)      │                                     │
│  ┌──────────┬──────────┬──────┴──────┬───────────┬──────────┐       │
│  │Dashboard │Carteira  │Agenda      │Atendimento│Projecao  │       │
│  │(page.tsx)│(page.tsx) │(page.tsx)  │(page.tsx) │(page.tsx)│       │
│  └──────────┴──────────┴────────────┴───────────┴──────────┘       │
│  ┌──────────┬──────────┬────────────┬───────────┬──────────┐       │
│  │Sinaleiro │RNC       │Import      │Login      │Config    │       │
│  │(page.tsx)│(page.tsx) │(page.tsx)  │(page.tsx) │(page.tsx)│       │
│  └──────────┴──────────┴────────────┴───────────┴──────────┘       │
│  Componentes: AppShell, Sidebar, KpiCard, StatusBadge,             │
│               ClienteTable, ClienteModal, AtendimentoForm,         │
│               AgendaCard, SinaleiroGauge, ProjecaoChart            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ REST API (JSON)
                                │ Authorization: Bearer <JWT>
┌───────────────────────────────┼─────────────────────────────────────┐
│  BACKEND — Railway/Render     │                                     │
│  FastAPI 0.115+ / Python 3.12 │                                     │
│                               │                                     │
│  ┌─── API Layer ──────────────┴───────────────────────────────────┐ │
│  │ /api/auth/*        → AuthService                               │ │
│  │ /api/clientes/*    → ClienteService                            │ │
│  │ /api/atendimentos/*→ AtendimentoService (+ MotorRegrasService) │ │
│  │ /api/agenda/*      → AgendaService                             │ │
│  │ /api/dashboard/*   → DashboardService                          │ │
│  │ /api/projecao/*    → ProjecaoService                           │ │
│  │ /api/sinaleiro/*   → SinaleiroService                          │ │
│  │ /api/rnc/*         → RNCService                                │ │
│  │ /api/import/*      → ImportService                             │ │
│  │ /api/config/*      → ConfigService                             │ │
│  │ /api/webhooks/*    → WebhookService (Deskrio)                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─── Services Layer ─────────────────────────────────────────────┐ │
│  │ motor_regras_service.py  — 92 combinacoes (port do motor.py)   │ │
│  │ score_service.py         — 6 fatores ponderados                │ │
│  │ sinaleiro_service.py     — saude cliente + penetracao redes    │ │
│  │ projecao_service.py      — meta vs realizado                   │ │
│  │ agenda_service.py        — geracao diaria priorizada           │ │
│  │ import_service.py        — pipeline xlsx + validacao           │ │
│  │ deskrio_client.py        — API WhatsApp bidirecional           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─── Background Workers (APScheduler / arq) ────────────────────┐ │
│  │ worker_import.py    — processamento xlsx async                 │ │
│  │ worker_motor.py     — recalculo motor/score/sinaleiro          │ │
│  │ worker_agenda.py    — geracao de agendas diarias (cron 06:00)  │ │
│  │ worker_deskrio.py   — sync WhatsApp periodico                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│  DATABASE — PostgreSQL 16     │                                     │
│  (Supabase / Neon / Railway)  │                                     │
│                               │                                     │
│  Tabelas: clientes, vendas, log_interacoes, agenda_items,          │
│           regras_motor, score_historico, sinaleiro_redes, redes,    │
│           rnc, metas, import_jobs, usuarios, sessoes               │
│  Indices: cnpj, consultor, situacao, data_*, sinaleiro             │
│  Alembic: versionamento de schema                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│  INTEGRACOES EXTERNAS                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Deskrio  │  │ Mercos   │  │ SAP      │  │ Asana    │           │
│  │ WhatsApp │  │ Vendas   │  │ Cadastro │  │ Tasks    │           │
│  │ REST API │  │ xlsx/CSV │  │ xlsx/CSV │  │ REST API │           │
│  │ Webhook  │  │ (manual) │  │ (manual) │  │ (futuro) │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 2. BACKEND

## 2.1 Estrutura de Pastas Final

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, lifespan, CORS, routers
│   ├── config.py                  # Settings via pydantic-settings (.env)
│   ├── database.py                # Engine, SessionLocal, Base, get_db
│   ├── security.py                # JWT, password hashing, auth dependencies
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── usuario.py             # NOVO
│   │   ├── cliente.py             # EXISTENTE (expandir)
│   │   ├── venda.py               # NOVO — Two-Base: registros com R$
│   │   ├── log_interacao.py       # NOVO — Two-Base: registros R$ 0.00
│   │   ├── agenda.py              # EXISTENTE (expandir)
│   │   ├── regra_motor.py         # NOVO — 92 combinacoes
│   │   ├── score_historico.py     # NOVO — snapshots de score
│   │   ├── rede.py                # NOVO — redes/franquias
│   │   ├── rnc.py                 # NOVO — registro nao conformidade
│   │   ├── meta.py                # NOVO — metas SAP
│   │   └── import_job.py          # NOVO — rastreabilidade de imports
│   │
│   ├── schemas/                   # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cliente.py
│   │   ├── venda.py
│   │   ├── log_interacao.py
│   │   ├── agenda.py
│   │   ├── dashboard.py
│   │   ├── projecao.py
│   │   ├── sinaleiro.py
│   │   ├── rnc.py
│   │   └── import_job.py
│   │
│   ├── api/                       # Route handlers (thin — delegam para services)
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies compartilhadas (get_current_user)
│   │   ├── routes_auth.py         # NOVO
│   │   ├── routes_clientes.py     # EXISTENTE (expandir com POST/PUT)
│   │   ├── routes_atendimentos.py # NOVO — registro de interacoes + motor
│   │   ├── routes_vendas.py       # NOVO — Two-Base: registros com R$
│   │   ├── routes_agenda.py       # EXISTENTE (expandir)
│   │   ├── routes_dashboard.py    # EXISTENTE (expandir)
│   │   ├── routes_projecao.py     # NOVO (extrair de dashboard)
│   │   ├── routes_sinaleiro.py    # NOVO
│   │   ├── routes_rnc.py          # NOVO
│   │   ├── routes_import.py       # NOVO — upload xlsx
│   │   ├── routes_config.py       # NOVO — listas/dropdowns
│   │   └── routes_webhooks.py     # NOVO — Deskrio incoming
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── cliente_service.py
│   │   ├── motor_regras_service.py  # Port de scripts/motor_regras.py
│   │   ├── score_service.py         # Port de scripts/motor/score_engine.py
│   │   ├── sinaleiro_service.py     # Port de scripts/motor/sinaleiro_engine.py
│   │   ├── projecao_service.py      # Port de scripts/motor/projecao_engine.py
│   │   ├── agenda_service.py        # Port de scripts/motor/agenda_engine.py
│   │   ├── import_service.py        # Port de scripts/motor/import_pipeline.py
│   │   ├── dashboard_service.py
│   │   ├── rnc_service.py
│   │   ├── deskrio_client.py        # API client WhatsApp
│   │   └── seed.py                  # EXISTENTE
│   │
│   └── workers/                   # Background jobs
│       ├── __init__.py
│       ├── worker_import.py       # Processa xlsx upload
│       ├── worker_motor.py        # Recalcula motor batch
│       ├── worker_agenda.py       # Gera agendas diarias
│       └── scheduler.py           # APScheduler para crons
│
├── alembic/                       # Migrations
│   ├── env.py
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── alembic.ini
│
├── tests/
│   ├── conftest.py
│   ├── test_motor_regras.py       # Portar 69 testes existentes
│   ├── test_score_engine.py
│   ├── test_sinaleiro.py
│   ├── test_api_clientes.py
│   ├── test_api_atendimentos.py
│   └── test_two_base.py           # Guardrail critico
│
├── requirements.txt
└── Dockerfile
```

## 2.2 Modelos de Dados (SQLAlchemy)

### 2.2.1 Usuario (NOVO)

```python
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="consultor")
        # Valores: "admin", "consultor", "viewer"
    consultor_nome = Column(String(50), nullable=True)
        # MANU, LARISSA, DAIANE — link para filtro de carteira
        # NULL para admin/viewer
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
```

### 2.2.2 Venda (NOVO — Two-Base: registros com R$)

```python
class Venda(Base):
    """
    TWO-BASE ARCHITECTURE: Esta tabela contem APENAS registros com valor R$.
    NUNCA misturar com log_interacoes (que sao SEMPRE R$ 0.00).
    """
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)
    data_pedido = Column(Date, nullable=False, index=True)
    numero_pedido = Column(String(50), nullable=True)
    valor_pedido = Column(Float, nullable=False)  # R$ — SEMPRE > 0
    consultor = Column(String(50), nullable=False, index=True)
    fonte = Column(String(20), nullable=False, default="MERCOS")
        # MERCOS, SAP, MANUAL
    classificacao_3tier = Column(String(15), nullable=False, default="REAL")
        # REAL, SINTETICO — NUNCA ALUCINACAO
    mes_referencia = Column(String(7), nullable=True)  # "2026-03"
    created_at = Column(DateTime, server_default=func.now())

    cliente = relationship("Cliente", backref="vendas",
                          foreign_keys=[cnpj],
                          primaryjoin="Venda.cnpj == Cliente.cnpj")

    __table_args__ = (
        CheckConstraint("valor_pedido > 0", name="ck_venda_valor_positivo"),
        Index("ix_vendas_cnpj_data", "cnpj", "data_pedido"),
    )
```

### 2.2.3 LogInteracao (NOVO — Two-Base: SEMPRE R$ 0.00)

```python
class LogInteracao(Base):
    """
    TWO-BASE ARCHITECTURE: Esta tabela contem APENAS registros de interacao.
    NUNCA contem valor monetario. Valor = SEMPRE R$ 0.00 (implicito).
    """
    __tablename__ = "log_interacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)
    data_interacao = Column(DateTime, nullable=False, index=True)
    consultor = Column(String(50), nullable=False, index=True)
    resultado = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=True)

    # CAMPOS CALCULADOS PELO MOTOR DE REGRAS (automaticos)
    estagio_funil = Column(String(50))
    fase = Column(String(30))
    tipo_contato = Column(String(50))
    acao_futura = Column(String(100))
    temperatura = Column(String(20))
    follow_up_dias = Column(Integer)
    grupo_dash = Column(String(50))
    tentativa = Column(String(5))  # T1, T2, T3, T4, NUTRICAO

    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    cliente = relationship("Cliente", backref="interacoes",
                          foreign_keys=[cnpj],
                          primaryjoin="LogInteracao.cnpj == Cliente.cnpj")

    __table_args__ = (
        Index("ix_log_cnpj_data", "cnpj", "data_interacao"),
        Index("ix_log_consultor_data", "consultor", "data_interacao"),
    )
```

### 2.2.4 RegraMotor (NOVO — 92 combinacoes)

```python
class RegraMotor(Base):
    __tablename__ = "regras_motor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    situacao = Column(String(20), nullable=False)
    resultado = Column(String(50), nullable=False)
    estagio_funil = Column(String(50), nullable=False)
    fase = Column(String(30), nullable=False)
    tipo_contato = Column(String(50), nullable=False)
    acao_futura = Column(String(100), nullable=False)
    temperatura = Column(String(20), nullable=False)
    follow_up_dias = Column(Integer, nullable=False, default=0)
    grupo_dash = Column(String(50))
    tipo_acao = Column(String(50))
    chave = Column(String(80), unique=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("situacao", "resultado", name="uq_regra_sit_res"),
    )
```

### 2.2.5 ScoreHistorico (NOVO)

```python
class ScoreHistorico(Base):
    __tablename__ = "score_historico"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)
    data_calculo = Column(Date, nullable=False, index=True)
    score = Column(Float, nullable=False)
    prioridade = Column(String(5))
    sinaleiro = Column(String(20))
    situacao = Column(String(20))
    fator_fase = Column(Float)
    fator_sinaleiro = Column(Float)
    fator_curva = Column(Float)
    fator_temperatura = Column(Float)
    fator_tipo_cliente = Column(Float)
    fator_tentativas = Column(Float)

    __table_args__ = (
        Index("ix_score_hist_cnpj_data", "cnpj", "data_calculo"),
    )
```

### 2.2.6 Rede (NOVO)

```python
class Rede(Base):
    __tablename__ = "redes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), unique=True, nullable=False)
    total_lojas = Column(Integer, nullable=False, default=0)
    lojas_ativas = Column(Integer, nullable=False, default=0)
    consultor_responsavel = Column(String(50), nullable=True)
    faturamento_real = Column(Float, default=0.0)
    potencial_maximo = Column(Float, default=0.0)
    pct_penetracao = Column(Float, default=0.0)
    sinaleiro = Column(String(20))
    cadencia = Column(String(50))
    updated_at = Column(DateTime, onupdate=func.now())
```

### 2.2.7 RNC (NOVO)

```python
class RNC(Base):
    __tablename__ = "rnc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)
    data_abertura = Column(Date, nullable=False)
    consultor = Column(String(50), nullable=False, index=True)
    tipo_problema = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ABERTO")
    prazo_resolucao = Column(Date, nullable=True)
    responsavel = Column(String(100), nullable=True)
    resolucao = Column(Text, nullable=True)
    data_resolucao = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

### 2.2.8 Meta (NOVO)

```python
class Meta(Base):
    __tablename__ = "metas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), ForeignKey("clientes.cnpj"), nullable=False, index=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    meta_sap = Column(Float, nullable=False, default=0.0)
    meta_igualitaria = Column(Float, nullable=True)
    realizado = Column(Float, nullable=False, default=0.0)
    fonte = Column(String(20), nullable=False, default="SAP")

    __table_args__ = (
        UniqueConstraint("cnpj", "ano", "mes", name="uq_meta_cnpj_periodo"),
        Index("ix_meta_periodo", "ano", "mes"),
    )
```

### 2.2.9 ImportJob (NOVO)

```python
class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(20), nullable=False)
    arquivo_nome = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="PENDENTE")
    registros_lidos = Column(Integer, default=0)
    registros_inseridos = Column(Integer, default=0)
    registros_atualizados = Column(Integer, default=0)
    registros_ignorados = Column(Integer, default=0)
    erro_mensagem = Column(Text, nullable=True)
    iniciado_em = Column(DateTime, nullable=True)
    concluido_em = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

## 2.3 Schema do Banco (ERD ASCII)

```
┌──────────────────────┐       ┌──────────────────────────┐
│      usuarios        │       │       import_jobs         │
├──────────────────────┤       ├──────────────────────────┤
│ id          PK INT   │       │ id           PK INT      │
│ email       UQ STR   │───┐   │ tipo         STR(20)     │
│ nome        STR(100) │   │   │ status       STR(20)     │
│ hashed_password STR  │   │   │ registros_*  INT         │
│ role        STR(20)  │   │   │ created_by   FK→usuarios │
│ consultor_nome STR   │   │   │ created_at   DATETIME    │
│ ativo       BOOL     │   │   └──────────────────────────┘
│ created_at  DATETIME │   │
│ last_login  DATETIME │   │
└──────────────────────┘   │
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    clientes (PK=id, BK=cnpj UNIQUE)          │
├──────────────────────────────────────────────────────────────┤
│ id, cnpj UQ STR(14), nome_fantasia, razao_social,           │
│ uf, cidade, email, telefone, codigo_cliente, consultor,      │
│ situacao, tipo_cliente, classificacao_3tier,                  │
│ dias_sem_compra, valor_ultimo_pedido, ciclo_medio,           │
│ n_compras, faturamento_total, temperatura, score,            │
│ prioridade, sinaleiro, curva_abc, fase, estagio_funil,       │
│ acao_futura, followup_dias, tentativas, problema_aberto,     │
│ followup_vencido, rede_regional, meta_anual,                 │
│ realizado_acumulado, pct_alcancado, gap_valor, status_meta   │
└────────┬────────────────────────┬────────────────────────────┘
         │ cnpj                    │ cnpj
         ▼                         ▼
┌────────────────────────┐ ┌──────────────────────────┐
│       vendas           │ │    log_interacoes        │
│   (TWO-BASE: R$ > 0)  │ │  (TWO-BASE: R$ = 0.00)  │
├────────────────────────┤ ├──────────────────────────┤
│ id, cnpj FK, data,     │ │ id, cnpj FK, data,       │
│ numero_pedido,         │ │ consultor, resultado,    │
│ valor_pedido FLOAT >0, │ │ descricao, estagio_funil,│
│ consultor, fonte,      │ │ fase, tipo_contato,      │
│ classif_3tier          │ │ acao_futura, temperatura, │
│ CK: valor_pedido > 0  │ │ follow_up_dias, tentativa │
└────────────────────────┘ └──────────────────────────┘

┌────────────────────────┐ ┌──────────────────────────┐
│    agenda_items        │ │    regras_motor          │
├────────────────────────┤ ├──────────────────────────┤
│ id, cnpj FK, consultor,│ │ id, situacao, resultado, │
│ data_agenda, posicao,  │ │ estagio_funil, fase,     │
│ score, prioridade,     │ │ tipo_contato, acao_futura│
│ sinaleiro, acao        │ │ temperatura, follow_up,  │
└────────────────────────┘ │ UQ(situacao, resultado)  │
                           └──────────────────────────┘

┌────────────────────────┐ ┌──────────────────────────┐
│   score_historico      │ │       redes              │
├────────────────────────┤ ├──────────────────────────┤
│ id, cnpj FK,           │ │ id, nome UQ,             │
│ data_calculo, score,   │ │ total_lojas, lojas_ativas│
│ prioridade, sinaleiro, │ │ faturamento_real,        │
│ fator_* (x6)           │ │ pct_penetracao, sinaleiro│
└────────────────────────┘ └──────────────────────────┘

┌────────────────────────┐ ┌──────────────────────────┐
│       metas            │ │       rnc                │
├────────────────────────┤ ├──────────────────────────┤
│ id, cnpj FK, ano, mes, │ │ id, cnpj FK, data,       │
│ meta_sap, realizado,   │ │ consultor, tipo_problema, │
│ UQ(cnpj, ano, mes)     │ │ status, resolucao        │
└────────────────────────┘ └──────────────────────────┘
```

## 2.4 APIs REST Completas

### /api/auth — Autenticacao

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| POST | /api/auth/login | Login (email + senha) → JWT | publico |
| POST | /api/auth/refresh | Refresh token | autenticado |
| GET | /api/auth/me | Dados do usuario logado | autenticado |
| PUT | /api/auth/password | Alterar senha propria | autenticado |
| POST | /api/auth/users | Criar usuario | admin |
| GET | /api/auth/users | Listar usuarios | admin |
| PUT | /api/auth/users/{id} | Editar usuario | admin |

### /api/clientes — Carteira

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| GET | /api/clientes | Listar com filtros + paginacao | consultor+ |
| GET | /api/clientes/stats | Agregados por dimensao | consultor+ |
| GET | /api/clientes/{cnpj} | Detalhe completo | consultor+ |
| GET | /api/clientes/{cnpj}/timeline | Historico vendas + interacoes | consultor+ |
| GET | /api/clientes/{cnpj}/score-history | Evolucao do score | consultor+ |
| PUT | /api/clientes/{cnpj} | Atualizar dados manuais | consultor+ |
| POST | /api/clientes | Cadastrar novo cliente | consultor+ |

### /api/atendimentos — Registro de Interacoes (Core do CRM)

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| POST | /api/atendimentos | Registrar interacao → MOTOR executa | consultor+ |
| GET | /api/atendimentos | Listar com filtros | consultor+ |
| GET | /api/atendimentos/{id} | Detalhe de uma interacao | consultor+ |
| GET | /api/atendimentos/stats | Contagens por resultado/consultor | admin |
| PUT | /api/atendimentos/{id} | Editar descricao (motor imutavel) | admin |

**Fluxo POST /api/atendimentos (critico)**:
```
1. Consultor envia: { cnpj, resultado, descricao }
2. Backend busca situacao atual do cliente
3. Motor de regras calcula: estagio_funil, fase, tipo_contato,
   acao_futura, temperatura, follow_up_dias, grupo_dash, tentativa
4. Insere em log_interacoes com campos calculados
5. Atualiza cliente: temperatura, fase, estagio_funil, acao_futura
6. Se resultado == "VENDA/PEDIDO": solicita dados de venda separado
7. Retorna: interacao completa + campos calculados pelo motor
```

### /api/vendas — Two-Base: Registros com R$

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| POST | /api/vendas | Registrar venda (valor > 0 obrigatorio) | consultor+ |
| GET | /api/vendas | Listar com filtros | consultor+ |
| GET | /api/vendas/totais | Faturamento por consultor/periodo | admin |

### /api/agenda — Agenda Inteligente

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| GET | /api/agenda | Todas as agendas do dia | admin |
| GET | /api/agenda/{consultor} | Agenda de um consultor | consultor+ |
| POST | /api/agenda/gerar | Disparar geracao (background) | admin |
| GET | /api/agenda/historico | Agendas anteriores | admin |

### /api/dashboard — KPIs e Analytics

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| GET | /api/dashboard/kpis | KPIs principais | consultor+ |
| GET | /api/dashboard/distribuicao | Distribuicoes por 6 dimensoes | consultor+ |
| GET | /api/dashboard/top10 | Top 10 clientes por faturamento | consultor+ |
| GET | /api/dashboard/funil | Pipeline de vendas por estagio | admin |

### /api/projecao — Metas e Projecao

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| GET | /api/projecao | Resumo + por consultor | admin |
| GET | /api/projecao/{consultor} | Meta vs realizado | consultor+ |
| GET | /api/projecao/redes | Projecao por rede | admin |

### /api/sinaleiro — Saude Clientes e Redes

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| GET | /api/sinaleiro/clientes | Sinaleiro por cliente | consultor+ |
| GET | /api/sinaleiro/redes | Penetracao por rede | admin |
| POST | /api/sinaleiro/recalcular | Trigger recalculo batch | admin |

### /api/rnc — Registro Nao Conformidade

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| POST | /api/rnc | Abrir RNC | consultor+ |
| GET | /api/rnc | Listar com filtros | consultor+ |
| PUT | /api/rnc/{id} | Atualizar status/resolucao | consultor+ |

### /api/import — Upload e Processamento

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| POST | /api/import/xlsx | Upload xlsx → background job | admin |
| GET | /api/import/jobs | Listar jobs | admin |
| GET | /api/import/jobs/{id} | Status de um job | admin |
| POST | /api/import/recalcular | Recalcular motor+score+sinaleiro | admin |

### /api/config — Listas e Parametros

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| GET | /api/config/listas | Dropdowns (resultados, situacoes) | consultor+ |
| GET | /api/config/regras | 92 regras do motor | admin |
| PUT | /api/config/regras/{id} | Editar regra | admin |

### /api/webhooks — Deskrio (WhatsApp)

| Metodo | Endpoint | Descricao | Role |
|--------|----------|-----------|------|
| POST | /api/webhooks/deskrio | Receber evento WhatsApp | API key |
| GET | /api/webhooks/deskrio/status | Status da conexao | admin |

## 2.5 Services Layer — Integracao do Motor Python

Estrategia: **portar** os modulos Python para services, mantendo logica identica.

### Mapeamento Motor → Services

| Modulo Python (scripts/motor/) | Service Backend | Estrategia |
|-------------------------------|----------------|------------|
| motor_regras.py | motor_regras_service.py | Port direto |
| score_engine.py | score_service.py | Port direto |
| sinaleiro_engine.py | sinaleiro_service.py | Port direto |
| projecao_engine.py | projecao_service.py | Port direto |
| agenda_engine.py | agenda_service.py | Port direto |
| import_pipeline.py | import_service.py | Port + adaptar upload |
| classify.py | import_service.py (stage 2) | Integrar |
| helpers.py | utils.py | Port direto |
| config.py | app/config.py | Merge pydantic-settings |
| run_pipeline.py | worker_import.py | Adaptar async |

### Fluxo de recalculo (background job)

```
POST /api/import/recalcular
  ↓
worker_motor.py:
  1. SELECT * FROM clientes WHERE classificacao_3tier != 'ALUCINACAO'
  2. Para cada cliente:
     a. MotorRegrasService.aplicar(situacao, ultimo_resultado)
     b. SinaleiroService.calcular(dias_sem_compra, ciclo_medio)
     c. ScoreService.calcular(cliente)
  3. UPDATE clientes SET score=?, prioridade=?, sinaleiro=?
  4. INSERT INTO score_historico (snapshot)
  5. AgendaService.gerar_todas() — agenda para amanha
```

## 2.6 Background Jobs

| Job | Trigger | Descricao |
|-----|---------|-----------|
| worker_import | POST /api/import/xlsx | Processa xlsx, 8 stages |
| worker_motor | POST /api/import/recalcular | Recalcula motor+score+sinaleiro |
| worker_agenda | Cron diario 06:00 BRT | Gera agendas priorizadas |
| worker_deskrio | Cron cada 15min | Sync WhatsApp via Deskrio API |

Tecnologia: APScheduler para crons (zero infra extra), arq para filas quando escalar.

---

# 3. FRONTEND

## 3.1 Paginas (App Router)

```
frontend/src/app/
├── layout.tsx                  # EXISTENTE — AppShell
├── page.tsx                    # EXISTENTE — Dashboard
├── login/page.tsx              # NOVO
├── carteira/
│   ├── page.tsx                # EXISTENTE — Lista
│   └── [cnpj]/page.tsx         # NOVO — Detalhe + timeline
├── agenda/page.tsx             # EXISTENTE — Agenda por consultor
├── atendimento/page.tsx        # NOVO — Registro de interacao
├── projecao/page.tsx           # EXISTENTE — Metas vs realizado
├── sinaleiro/page.tsx          # NOVO — Painel sinaleiro + redes
├── rnc/page.tsx                # NOVO — Lista de RNC
├── import/page.tsx             # NOVO — Upload xlsx (admin)
└── config/page.tsx             # NOVO — Regras, pesos, listas
```

## 3.2 Componentes

### Existentes (manter/expandir)
- AppShell, Sidebar, KpiCard, StatusBadge, ClienteTable, ClienteModal

### Novos (criar)
- AtendimentoForm, MotorResultCard, AgendaCard, TimelineEvent
- SinaleiroGauge, ProjecaoChart, FunnelChart, ImportUploader
- ProtectedRoute, FilterBar, DataTable, EmptyState, ConfirmDialog

## 3.3 State Management

- React Context: AuthContext (usuario, role, token), MotorContext (listas dropdown)
- SWR: data fetching com cache, revalidacao, dedup
- useSWRMutation: POST/PUT com invalidacao automatica

## 3.4 Hooks

```
frontend/src/hooks/
├── useAuth.ts           # Login, logout, refresh, role check
├── useClientes.ts       # Lista com filtros (SWR)
├── useCliente.ts        # Detalhe + timeline
├── useAgenda.ts         # Agenda por consultor
├── useKPIs.ts           # Dashboard KPIs
├── useProjecao.ts       # Metas vs realizado
├── useSinaleiro.ts      # Sinaleiro clientes + redes
├── useMotorListas.ts    # Dropdowns (cache longo)
├── useAtendimento.ts    # Mutation: registrar interacao
├── useVenda.ts          # Mutation: registrar venda
└── useImport.ts         # Upload + polling job status
```

---

# 4. DATABASE

## 4.1 SQLite → PostgreSQL Migration Path

| Fase | Banco | Quando |
|------|-------|--------|
| Dev local | SQLite | Agora (ja suportado) |
| Staging | PostgreSQL (Neon free) | Antes do deploy |
| Producao | PostgreSQL (Railway) | Deploy |

## 4.2 Indices Criticos

```sql
CREATE INDEX ix_clientes_consultor ON clientes(consultor);
CREATE INDEX ix_clientes_situacao ON clientes(situacao);
CREATE INDEX ix_clientes_score ON clientes(score DESC NULLS LAST);
CREATE INDEX ix_clientes_prioridade ON clientes(prioridade);
CREATE INDEX ix_vendas_cnpj_data ON vendas(cnpj, data_pedido);
CREATE INDEX ix_log_cnpj_data ON log_interacoes(cnpj, data_interacao);
CREATE INDEX ix_log_consultor_data ON log_interacoes(consultor, data_interacao);
CREATE INDEX ix_agenda_consultor_data ON agenda_items(consultor, data_agenda);
CREATE INDEX ix_score_hist_cnpj_data ON score_historico(cnpj, data_calculo);
-- PostgreSQL only:
CREATE INDEX ix_clientes_nome_trgm ON clientes USING gin(nome_fantasia gin_trgm_ops);
```

## 4.3 Migrations (Alembic)

```
alembic/versions/
├── 001_initial_schema.py       # clientes + agenda_items
├── 002_add_usuarios.py
├── 003_add_vendas.py           # Two-Base
├── 004_add_log_interacoes.py   # Two-Base
├── 005_add_regras_motor.py     # 92 regras
├── 006_add_score_historico.py
├── 007_add_redes_rnc_metas.py
├── 008_add_import_jobs.py
└── 009_add_cliente_fields.py   # email, telefone, rede_regional
```

---

# 5. AUTENTICACAO

## 5.1 JWT (stateless)

- SECRET_KEY via env var (256-bit)
- ACCESS_TOKEN: 8 horas (jornada comercial)
- REFRESH_TOKEN: 30 dias

## 5.2 Roles e Permissoes

| Role | Quem | Permissoes |
|------|------|-----------|
| admin | Leandro | TUDO: CRUD usuarios, config motor, import, recalcular |
| consultor | Manu, Larissa, Daiane | Registrar atendimento, ver carteira filtrada, agenda propria |
| viewer | Futuros | Apenas leitura |

**Julio = SEM ACESSO** (100% fora do sistema)

### Filtro automatico por consultor
Quando role == "consultor", query filtrada automaticamente por `consultor_nome`.

## 5.3 Usuarios Iniciais (seed)

| Email | Nome | Role | consultor_nome |
|-------|------|------|---------------|
| leandro@vitao.com.br | Leandro | admin | NULL |
| manu@vitao.com.br | Manu Ditzel | consultor | MANU |
| larissa@vitao.com.br | Larissa Padilha | consultor | LARISSA |
| daiane@vitao.com.br | Daiane Stavicki | consultor | DAIANE |

---

# 6. INTEGRACOES

## 6.1 Deskrio — WhatsApp Bidirecional

### Webhook Receiver
- POST /api/webhooks/deskrio recebe eventos: message.received, ticket.created, ticket.closed
- Valida API key, extrai telefone → busca CNPJ → cria LogInteracao automatica

### API Client
- DeskrioClient com metodos: enviar_mensagem, listar_contatos, buscar_tickets, criar_ticket
- Base URL: https://api.deskrio.com.br/v1

## 6.2 Import Pipeline (xlsx upload)

```
1. Admin upload via POST /api/import/xlsx
2. Cria ImportJob(status=PENDENTE)
3. Worker executa 8 stages:
   IMPORT → CLASSIFY → MOTOR → SINALEIRO → SCORE → PROJECAO → AGENDA → EXPORT
4. Atualiza ImportJob(status=CONCLUIDO)
5. Frontend poll status
```

---

# 7. DEPLOY

| Camada | Servico | Justificativa |
|--------|---------|---------------|
| Frontend | Vercel | Auto-deploy Next.js, CDN global |
| Backend | Railway | Container Docker, PostgreSQL managed |
| Database | Railway PostgreSQL | Managed, backups, SSL |
| Fila (futuro) | Upstash Redis | Serverless, $0 em uso baixo |

## 7.1 CI/CD

- GitHub Actions: backend-test (pytest + PostgreSQL) → frontend-build → deploy
- Backend: Railway auto-deploy via Dockerfile
- Frontend: Vercel auto-deploy via Git integration

---

# 8. DECISOES TECNICAS

| # | Decisao | Escolha | Motivo |
|---|---------|---------|--------|
| D1 | Backend language | FastAPI (Python) | Reutiliza 14 modulos do motor sem rewrite |
| D2 | Sync vs Async | Sync | 489 clientes nao justifica complexidade async |
| D3 | Frontend data | SWR | Leve (4KB), 4 usuarios, fetch puro ja existe |
| D4 | Two-Base enforcement | DB constraint + service | Defesa em profundidade (R4 sagrada) |
| D5 | Background jobs | APScheduler → arq | Zero infra extra, migra quando escalar |
| D6 | Migrations | Alembic desde dia 1 | create_all inaceitavel em producao |

---

# APENDICE — PRIORIDADE DE IMPLEMENTACAO

| Fase | Scope | Est. | Deps |
|------|-------|------|------|
| F1 | Auth + Models + Alembic + Seed | 3 dias | - |
| F2 | POST /api/atendimentos + MotorRegrasService | 2 dias | F1 |
| F3 | Vendas (Two-Base) + Dashboard expandido | 2 dias | F1 |
| F4 | Score + Sinaleiro services + recalculo | 2 dias | F2, F3 |
| F5 | Agenda service + cron diario | 1 dia | F4 |
| F6 | Frontend: Login + AtendimentoForm + Timeline | 3 dias | F1, F2 |
| F7 | Import pipeline (upload xlsx) | 2 dias | F4 |
| F8 | Sinaleiro redes + RNC + Config | 2 dias | F3 |
| F9 | Deskrio webhook + API client | 2 dias | F2 |
| F10 | Deploy (Vercel + Railway + CI/CD) | 1 dia | F6 |

**Total estimado: ~20 dias de implementacao**

---

# CONSTANTES DE NEGOCIO (source of truth)

```python
FATURAMENTO_BASELINE = 2_091_000.0      # R$ 2025 real (PAINEL CEO)
PROJECAO_2026 = 3_377_120.0             # Meta 2026
Q1_2026_REAL = 459_465.0                # Q1 2026 SAP
ALUCINACAO_COUNT = 558                   # Registros NUNCA integrar
FATURAMENTO_TOLERANCIA = 0.005          # 0.5%
TICKET_REF_REDES = 525.0                # R$/mes por loja
MESES_REF_REDES = 11                    # Meses referencia
MAX_ATENDIMENTOS_PADRAO = 40            # Por consultor/dia
MAX_ATENDIMENTOS_DAIANE = 20            # Daiane (redes)
```

---

*Documento gerado por @architect. Regras R1-R12 verificadas e incorporadas.*
