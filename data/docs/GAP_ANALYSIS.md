# GAP ANALYSIS — CRM VITAO360 SaaS
# De Excel+Python para Aplicacao Web Completa
# Data: 2026-03-25 | Autor: @analyst | Versao: 1.0

---

## SUMARIO EXECUTIVO

O CRM VITAO360 possui um **Motor Python 100% funcional** (8 stages, 1581 registros, 92 combinacoes de regras) e um **scaffold SaaS basico** (~8% pronto). A lacuna principal esta na **integracao Motor -> Backend -> Frontend** e na ausencia completa de funcionalidades de **escrita** (CRUD), **autenticacao**, **LOG de atendimentos**, **WhatsApp/Deskrio** e **motor em tempo real**.

| Dimensao | Motor Python | Backend API | Frontend | Status Geral |
|----------|-------------|-------------|----------|--------------|
| Completude | **100%** | **~15%** | **~12%** | **~25%** |
| Regras de Negocio | 92/92 | 0/92 | 0/92 | **0% no SaaS** |
| CRUD | N/A (batch) | 0% (so GET) | 0% (so leitura) | **0%** |
| Autenticacao | N/A | 0% | 0% | **0%** |
| Integracao APIs | N/A | 0% | 0% | **0%** |

---

## 1. INVENTARIO DO QUE EXISTE

### 1.1 Backend (FastAPI) — `backend/app/`

#### 1.1.1 Models (SQLAlchemy ORM)

| Model | Arquivo | Campos | Completude | Gaps |
|-------|---------|--------|------------|------|
| **Cliente** | `models/cliente.py` | 35 campos | **85%** | Falta: telefone, email, endereco_completo, historico_pedidos, redes/franquias, e-commerce flags, dados Mercos/SAP brutos |
| **AgendaItem** | `models/agenda.py` | 12 campos | **70%** | Falta: status_atendimento (FEITO/PENDENTE/REAGENDADO), observacoes, data_atendido, resultado_registrado |
| **LogAtendimento** | NAO EXISTE | — | **0%** | CRITICO: nao existe model para LOG de atendimentos (20.830 registros historicos) |
| **Pedido/Venda** | NAO EXISTE | — | **0%** | Nao existe model para historico de vendas/pedidos |
| **Rede/Franquia** | NAO EXISTE | — | **0%** | Nao existe model para redes (Divina Terra, Biomundo, etc.) |
| **Meta** | NAO EXISTE | — | **0%** | Nao existe model dedicado para metas SAP por consultor/mes |
| **Usuario** | NAO EXISTE | — | **0%** | Nao existe model de usuario/autenticacao |
| **Configuracao** | NAO EXISTE | — | **0%** | Nao existe model para configuracoes do sistema |

**Observacoes sobre o model Cliente:**
- CNPJ como String(14) -- R5 respeitada
- classificacao_3tier presente -- R8 respeitada
- faturamento_total com comentario Two-Base -- R4 respeitada
- created_at/updated_at com server_default -- OK
- Falta: relacionamento ORM com LogAtendimento, Pedidos, Rede

#### 1.1.2 Rotas API

| Rota | Metodo | Endpoint | O que faz | O que FALTA |
|------|--------|----------|-----------|-------------|
| **Clientes** | GET | `/api/clientes` | Lista paginada com 8 filtros | POST/PUT/DELETE, busca avancada, export CSV |
| **Clientes** | GET | `/api/clientes/stats` | Agregados por 5 dimensoes | — |
| **Clientes** | GET | `/api/clientes/{cnpj}` | Detalhe completo | PUT para atualizar, historico de interacoes |
| **Agenda** | GET | `/api/agenda` | Agenda de todos consultores | POST para criar item, PUT para marcar feito |
| **Agenda** | GET | `/api/agenda/{consultor}` | Agenda de 1 consultor | Filtro por data, status do item |
| **Dashboard** | GET | `/api/dashboard/kpis` | 9 KPIs principais | KPIs historicos (tendencia), filtro por periodo |
| **Dashboard** | GET | `/api/dashboard/distribuicao` | 6 distribuicoes | Filtro por consultor/periodo |
| **Dashboard** | GET | `/api/dashboard/top10` | Top 10 por faturamento | Top N dinamico, filtro por consultor |
| **Dashboard** | GET | `/api/dashboard/projecao` | Realizado vs meta por consultor | Historico mensal, drill-down por cliente |
| **Health** | GET | `/health` | Status do sistema | — |

**Total de endpoints: 9 GET + 0 POST/PUT/DELETE = SOMENTE LEITURA**

**Endpoints que NAO EXISTEM (necessarios):**

| Categoria | Endpoints Necessarios | Prioridade |
|-----------|----------------------|------------|
| **LOG Atendimento** | POST/GET/PUT log de contato | P0 |
| **Motor Regras** | POST executar motor para 1 cliente | P0 |
| **Score** | GET recalcular score individual | P1 |
| **Agenda** | POST criar/PUT atualizar/DELETE remover item | P0 |
| **Cliente CRUD** | POST criar/PUT atualizar cliente | P1 |
| **Autenticacao** | POST login, GET me, refresh token | P0 |
| **Import** | POST importar dados Excel/JSON | P1 |
| **Export** | GET exportar carteira CSV/Excel | P2 |
| **WhatsApp** | POST enviar/GET receber via Deskrio | P2 |
| **Mercos** | GET sincronizar pedidos | P2 |
| **Pipeline** | POST rodar pipeline completo | P1 |

#### 1.1.3 Services

| Service | Arquivo | O que faz | Completude |
|---------|---------|-----------|------------|
| **Seed** | `services/seed.py` | Importa JSON do motor para DB | **90%** — funcional, respeita R5/R8, faz upsert |
| **Motor** | NAO EXISTE | Deveria executar motor_regras em tempo real | **0%** |
| **Score** | NAO EXISTE | Deveria calcular score on-demand | **0%** |
| **Sinaleiro** | NAO EXISTE | Deveria atualizar sinaleiro | **0%** |
| **Agenda** | NAO EXISTE | Deveria gerar agenda automatica | **0%** |
| **Projecao** | NAO EXISTE | Deveria calcular projecao | **0%** |
| **Auth** | NAO EXISTE | Login, JWT, permissoes | **0%** |
| **Deskrio** | NAO EXISTE | Integracao WhatsApp | **0%** |
| **Mercos** | NAO EXISTE | Integracao pedidos B2B | **0%** |

#### 1.1.4 Infraestrutura Backend

| Item | Status | Detalhe |
|------|--------|---------|
| FastAPI app | OK | `main.py` configurado com lifespan |
| CORS | OK | Permite localhost:3000/3001 |
| SQLAlchemy ORM | OK | Engine + SessionLocal + Base |
| SQLite dev | OK | `data/crm_vitao360.db` |
| PostgreSQL prod | PREPARADO | `DATABASE_URL` env var |
| Alembic migrations | NAO EXISTE | `Base.metadata.create_all()` direto |
| Testes unitarios | NAO EXISTE | 0 testes no backend |
| Docker | NAO EXISTE | Sem Dockerfile |
| .env config | NAO EXISTE | Sem arquivo .env template |
| Rate limiting | NAO EXISTE | — |
| Logging estruturado | NAO EXISTE | — |
| Error handling global | NAO EXISTE | Sem middleware de erros |
| Background tasks | NAO EXISTE | Celery/asyncio nao configurados |
| WebSocket | NAO EXISTE | Para notificacoes real-time |

---

### 1.2 Frontend (Next.js 14) — `frontend/src/`

#### 1.2.1 Paginas

| Pagina | Arquivo | O que renderiza | Completude | Gaps |
|--------|---------|-----------------|------------|------|
| **Dashboard** | `app/page.tsx` | 4 KPI cards + 4 graficos de barras + tabela Top 10 | **75%** | Falta: graficos de tendencia, filtro por periodo, drill-down |
| **Carteira** | `app/carteira/page.tsx` | Tabela com 10 colunas + 3 filtros + paginacao + modal detalhe | **60%** | Falta: edicao inline, busca texto, export, filtros avancados (ABC, temperatura, UF) |
| **Agenda** | `app/agenda/page.tsx` | 4 tabs por consultor + tabela com score bar + legenda | **50%** | Falta: marcar como feito, registrar resultado, alterar data, drag-drop reordenacao |
| **Projecao** | `app/projecao/page.tsx` | KPI cards + barra progresso + comparacao baseline + tabela consultores | **65%** | Falta: drill-down por cliente, historico mensal, grafico de tendencia |
| **LOG** | NAO EXISTE | — | **0%** | CRITICO: pagina para registrar atendimentos |
| **Login** | NAO EXISTE | — | **0%** | Tela de autenticacao |
| **Config** | NAO EXISTE | — | **0%** | Configuracoes do sistema |
| **Relatorios** | NAO EXISTE | — | **0%** | Exportacao e relatorios |
| **Redes** | NAO EXISTE | — | **0%** | Painel redes/franquias |
| **WhatsApp** | NAO EXISTE | — | **0%** | Integracao Deskrio |

#### 1.2.2 Componentes

| Componente | Arquivo | Funcionalidade | Completude |
|------------|---------|----------------|------------|
| **AppShell** | `components/AppShell.tsx` | Layout sidebar + header + main content | **80%** — funcional, responsivo |
| **Sidebar** | `components/Sidebar.tsx` | Navegacao com 4 itens (Dashboard, Carteira, Agenda, Projecao) | **70%** — falta items de LOG, Config, etc. |
| **ClienteTable** | `components/ClienteTable.tsx` | Tabela com 10 colunas, skeleton, click handler | **65%** — falta sort, edicao, export |
| **ClienteModal** | `components/ClienteModal.tsx` | Slide-in panel com detalhe do cliente (3 secoes) | **50%** — falta edicao, historico, acoes |
| **KpiCard** | `components/KpiCard.tsx` | Card de metrica com accent color e loading state | **90%** — completo para uso atual |
| **StatusBadge** | `components/StatusBadge.tsx` | Badge colorido para 4 variants (situacao/sinaleiro/prioridade/abc) | **95%** — cores corretas conforme R9 |
| **FormularioLOG** | NAO EXISTE | — | **0%** — CRITICO |
| **GraficoTendencia** | NAO EXISTE | — | **0%** |
| **FiltrosAvancados** | NAO EXISTE | — | **0%** |
| **BuscaGlobal** | NAO EXISTE | — | **0%** |
| **Notificacoes** | NAO EXISTE | — | **0%** |

#### 1.2.3 Camada de API (`lib/api.ts`)

| Funcao | Existe | Metodo | Observacao |
|--------|--------|--------|------------|
| `fetchKPIs()` | SIM | GET | OK |
| `fetchDistribuicao()` | SIM | GET | OK |
| `fetchTop10()` | SIM | GET | OK |
| `fetchProjecao()` | SIM | GET | OK |
| `fetchClientes(params)` | SIM | GET | OK, suporta 5 filtros |
| `fetchCliente(cnpj)` | SIM | GET | OK |
| `fetchAgenda(consultor)` | SIM | GET | OK |
| `formatBRL()` | SIM | — | Helper formatacao |
| `formatPercent()` | SIM | — | Helper formatacao |
| `criarCliente()` | NAO | — | — |
| `atualizarCliente()` | NAO | — | — |
| `registrarAtendimento()` | NAO | — | — |
| `marcarAgendaFeito()` | NAO | — | — |
| `executarMotor()` | NAO | — | — |
| `login()` | NAO | — | — |
| `exportarCSV()` | NAO | — | — |

**Tipagem:** 10 interfaces TypeScript definidas, cobrindo os endpoints existentes. Falta `followups_vencidos` no tipo `KPIs` (existe no backend, ausente no frontend). `ClienteRegistro` tem campos extras (`segmento`, `ticket_medio`, `meta_mensal`, `ultima_compra`) que NAO existem no backend — desalinhamento de tipos.

#### 1.2.4 Infraestrutura Frontend

| Item | Status | Detalhe |
|------|--------|---------|
| Next.js 14 App Router | OK | `layout.tsx` com Inter font |
| Tailwind CSS | OK | Classes utilitarias em uso |
| Tema LIGHT | OK | R9 respeitada — cores corretas |
| Responsivo | PARCIAL | Sidebar mobile OK, tabelas com scroll horizontal |
| Testes | NAO EXISTE | 0 testes no frontend |
| State management | NAO EXISTE | useState local apenas, sem Zustand/Context global |
| Formularios | NAO EXISTE | Sem react-hook-form, validacao, etc. |
| Notificacoes/Toast | NAO EXISTE | — |
| Error boundary | NAO EXISTE | — |
| Loading states | OK | Skeletons implementados em todas as paginas |
| i18n | NAO EXISTE | Textos hardcoded em PT-BR (aceitavel) |
| PWA | NAO EXISTE | — |
| CI/CD | NAO EXISTE | — |

---

### 1.3 Motor Python — `scripts/motor/`

#### 1.3.1 Modulos do Motor Operacional

| Modulo | Arquivo | Funcao | Status | Registros |
|--------|---------|--------|--------|-----------|
| **Config** | `motor/config.py` | Constantes, paths, mapeamento de abas | **100%** | — |
| **Helpers** | `motor/helpers.py` | normalizar_cnpj, normalizar_vendedor, safe_read_sheet | **100%** | — |
| **Import Pipeline** | `motor/import_pipeline.py` | Le xlsx FINAL (40 abas), extrai DataFrames, normaliza | **100%** | 1581 registros |
| **Classify** | `motor/classify.py` | Classificacao 3-tier (REAL/SINTETICO/ALUCINACAO) | **100%** | 1581 |
| **Motor Regras** | `motor/motor_regras.py` | 92 combinacoes SITUACAO x RESULTADO, 8 campos gerados | **100%** | 1581 |
| **Sinaleiro Engine** | `motor/sinaleiro_engine.py` | Sinaleiro (4 cores), tipo_cliente, curva_abc, tentativas, sinaleiro_rede | **100%** | 1581 |
| **Score Engine** | `motor/score_engine.py` | Score ponderado 6 fatores (0-100), prioridade P0-P7, meta balance | **100%** | 1581 |
| **Projecao Engine** | `motor/projecao_engine.py` | Realizado vs meta SAP, % alcancado, consolidacao, dashboard terminal | **100%** | — |
| **Agenda Engine** | `motor/agenda_engine.py` | Gera agenda diaria por consultor, export Excel+JSON | **100%** | 140 (40+40+40+20) |
| **Run Pipeline** | `motor/run_pipeline.py` | Orquestrador das 8 stages em sequencia | **100%** | — |
| **Test Pipeline** | `motor/test_pipeline.py` | Testes do pipeline | **100%** | — |

**Motor Legado (raiz):**

| Modulo | Arquivo | Funcao | Status |
|--------|---------|--------|--------|
| `motor_regras.py` | `scripts/motor_regras.py` | Motor v3 standalone com score 6 fatores inline + validacao | **100%** |

#### 1.3.2 Pipeline (8 Stages) — TODAS PASSANDO

| Stage | Funcao | Tempo | Status |
|-------|--------|-------|--------|
| 1. IMPORT | Ler xlsx, normalizar CNPJs/vendedores | 0.02s | PASS |
| 2. CLASSIFY | 3-tier REAL/SINTETICO/ALUCINACAO | 0.01s | PASS |
| 3. MOTOR | Aplicar 92 regras | 0.02s | PASS |
| 4. SINALEIRO | Calcular sinaleiro, tipo, ABC, tentativas | 0.01s | PASS |
| 5. SCORE | Score ponderado + prioridade | 0.09s | PASS |
| 6. PROJECAO | (rodada separadamente) | — | PASS |
| 7. AGENDA | Gerar agendas 4 consultores | 0.07s | PASS |
| 8. EXPORT | Salvar JSONs de saida | — | PASS |

**Tempo total do pipeline: 0.41s** — extremamente rapido.

#### 1.3.3 Fases de Desenvolvimento (phases/)

15 fases de scripts de desenvolvimento (88+ arquivos):
- `phase01_projecao/` — 4 scripts de validacao/populacao
- `phase02_faturamento/` — 5 scripts de merge SAP+Mercos
- `phase03_timeline/` — 3 scripts de ABC timeline
- `phase04_log_completo/` — 5 scripts de LOG (Deskrio + sintetico)
- `phase05_dashboard/` — 3 scripts de dashboard
- `phase06_ecommerce/` — 2 scripts de e-commerce
- `phase07_redes_franquias/` — 3 scripts de redes
- `phase08_comite_metas/` — 3 scripts de metas
- `phase09_blueprint_v2/` — 6 scripts de carteira expandida
- `phase10_validacao_final/` — 10+ scripts de auditoria

---

### 1.4 Dados — `data/`

#### 1.4.1 Output do Motor (`data/output/motor/`)

| Arquivo | Registros | Conteudo | Usado pelo Backend |
|---------|-----------|----------|-------------------|
| `pipeline_output.json` | 1581 clientes | Base unificada com todos campos do motor | SIM (seed.py) |
| `motor_output.json` | 1581 | Saida do motor com regras aplicadas | NAO |
| `base_unificada.json` | 1581 | Base apos classify | NAO |
| `agenda_LARISSA.json` | 40 itens | Agenda diaria | SIM (seed.py) |
| `agenda_MANU.json` | 40 itens | Agenda diaria | SIM (seed.py) |
| `agenda_JULIO.json` | 40 itens | Agenda diaria | SIM (seed.py) |
| `agenda_DAIANE.json` | 20 itens | Agenda diaria | SIM (seed.py) |
| `pipeline_stats.json` | — | Metricas de execucao | NAO |

#### 1.4.2 Dados de Inteligencia (`data/intelligence/`)

| Arquivo | Conteudo | Usado pelo Motor |
|---------|----------|------------------|
| `arquitetura_9_dimensoes.json` | Framework 9 dimensoes do CRM | SIM (score_engine) |
| `fases_estrategicas.json` | 6 fases do ciclo comercial | SIM (score_engine) |
| `estagios_funil.json` | Estagios do pipeline de vendas | SIM (motor_regras) |
| `motor_regras_v4.json` | 92 combinacoes SITUACAO x RESULTADO | SIM (motor_regras) |
| `mapa_motor_novo.json` | Mapa do motor v4 | SIM |
| `carteira_blueprint.json` | Blueprint 81 colunas | SIM |
| `painel_ceo.json` | Financeiro baseline + projecao | SIM (projecao_engine) |
| `diagnostico_2025.json` | Diagnostico anual | Referencia |
| `conflitos_resolvidos.json` | Resolucoes de conflitos de dados | Referencia |
| `equipe_2026.json` | Equipe comercial 2026 | SIM (agenda_engine) |
| `motor_rampup.json` | Ramp-up de meta | SIM (projecao_engine) |
| `premissas.json` | Premissas de negocio | SIM |
| `q1_2026_real.json` | Q1 2026 realizado: R$459.465 | SIM (projecao_engine) |

#### 1.4.3 Output de Fases (`data/output/phase01-10/`)

13+ JSONs intermediarios de processamento das fases de desenvolvimento. Contem dados validados de Mercos, SAP, ABC, LOG, Dashboard, etc.

#### 1.4.4 Documentacao (`data/docs/`)

60+ arquivos .md cobrindo: PRD, specs, manuais, analises, handoffs, prompts, logs de conversa.

---

## 2. MAPA DE GAPS

### 2.1 Tabela Geral de Funcionalidades

| # | Funcionalidade | Motor Python | Backend API | Frontend | Dados | Status Geral | Prioridade |
|---|----------------|-------------|-------------|----------|-------|--------------|------------|
| 1 | **CARTEIRA visualizacao** | 100% (pipeline_output) | 80% (GET + filtros) | 60% (tabela + modal) | 100% (1581 reg.) | **PARCIAL** | P1 |
| 2 | **CARTEIRA edicao** | N/A | 0% (sem POST/PUT) | 0% (sem formulario) | N/A | **NAO EXISTE** | P1 |
| 3 | **Motor de Regras** | 100% (92 combos) | 0% (nao integrado) | 0% (nao existe) | 100% (JSON) | **GAP CRITICO** | P0 |
| 4 | **Score Engine** | 100% (6 fatores) | 0% (nao integrado) | 0% (nao existe) | 100% (JSON) | **GAP CRITICO** | P0 |
| 5 | **Sinaleiro** | 100% (4 cores + rede) | 0% (nao integrado) | 0% (nao existe) | 100% (JSON) | **GAP CRITICO** | P0 |
| 6 | **Agenda diaria** | 100% (4 consultores) | 50% (GET apenas) | 50% (leitura apenas) | 100% (140 itens) | **PARCIAL** | P0 |
| 7 | **LOG de atendimentos** | N/A (batch offline) | 0% (sem model/route) | 0% (sem pagina) | 0% (no DB) | **NAO EXISTE** | P0 |
| 8 | **Dashboard KPIs** | N/A | 80% (9 KPIs) | 75% (4 cards + graficos) | 100% | **PARCIAL** | P1 |
| 9 | **Dashboard distribuicao** | N/A | 90% (6 dim.) | 70% (4 graficos) | 100% | **PARCIAL** | P2 |
| 10 | **Projecao faturamento** | 100% (SAP vs meta) | 70% (endpoint OK) | 65% (KPIs + tabela) | 100% | **PARCIAL** | P2 |
| 11 | **Classificacao ABC** | 100% (pareto) | Armazenada | Exibida na tabela | 100% | **OK (leitura)** | — |
| 12 | **DE-PARA vendedores** | 100% (agenda_engine) | N/A (seed normaliza) | N/A | 100% | **OK** | — |
| 13 | **CNPJ normalizacao** | 100% (helpers.py) | 100% (route normaliza) | N/A | 100% | **OK** | — |
| 14 | **Two-Base Architecture** | 100% (pipeline) | 100% (R8 no kpis) | N/A | 100% | **OK** | — |
| 15 | **3-tier classificacao** | 100% (classify.py) | 100% (filtro ALUCINACAO) | N/A | 100% | **OK** | — |
| 16 | **Autenticacao/Login** | N/A | 0% | 0% | N/A | **NAO EXISTE** | P0 |
| 17 | **WhatsApp (Deskrio)** | N/A | 0% | 0% | Existe API (26 endpoints) | **NAO EXISTE** | P2 |
| 18 | **Mercos integracao** | 100% (import_pipeline) | 0% (nao exposto) | 0% | 100% (dados brutos) | **NAO EXISTE** | P2 |
| 19 | **SAP integracao** | 100% (projecao_engine) | 0% (nao exposto) | 0% | 100% (dados brutos) | **NAO EXISTE** | P2 |
| 20 | **Redes/Franquias** | 100% (sinaleiro_rede) | 0% (sem model/route) | 0% (sem pagina) | 100% (JSON) | **NAO EXISTE** | P2 |
| 21 | **Export CSV/Excel** | 100% (agenda_engine) | 0% (sem endpoint) | 0% (sem botao) | N/A | **NAO EXISTE** | P2 |
| 22 | **Import dados** | 100% (import_pipeline) | 0% (sem endpoint) | 0% (sem upload) | N/A | **NAO EXISTE** | P1 |
| 23 | **Busca global** | N/A | PARCIAL (busca nome) | 0% (sem campo) | N/A | **PARCIAL** | P2 |
| 24 | **Notificacoes** | N/A | 0% | 0% | N/A | **NAO EXISTE** | P3 |
| 25 | **Relatorios** | N/A | 0% | 0% | N/A | **NAO EXISTE** | P3 |
| 26 | **Migrations DB** | N/A | 0% (sem Alembic) | N/A | N/A | **NAO EXISTE** | P1 |
| 27 | **Testes automatizados** | PARCIAL (test_pipeline) | 0% | 0% | N/A | **NAO EXISTE** | P1 |
| 28 | **Docker/Deploy** | N/A | 0% | 0% | N/A | **NAO EXISTE** | P2 |

### 2.2 Contagem de Gaps

| Categoria | OK | PARCIAL | GAP/NAO EXISTE | Total |
|-----------|-----|---------|----------------|-------|
| Regras de negocio | 5 | 0 | 3 | 8 |
| CRUD/Operacional | 0 | 2 | 5 | 7 |
| Infraestrutura | 2 | 1 | 5 | 8 |
| Integracoes | 0 | 0 | 5 | 5 |
| **TOTAL** | **7** | **3** | **18** | **28** |

---

## 3. REGRAS DE NEGOCIO — COBERTURA NO SaaS

### 3.1 Tabela de Cobertura

| Regra | Motor Python | Backend SaaS | Frontend SaaS | Veredicto |
|-------|-------------|-------------|---------------|-----------|
| **R1 Two-Base Architecture** | 100% — pipeline separa VENDA de LOG | 100% — KPIs excluem ALUCINACAO, faturamento so de REAL/SINTETICO | N/A (leitura) | **COBERTA (leitura)** |
| **R2 CNPJ = Chave Primaria** | 100% — normalizar_cnpj() em helpers.py | 100% — String(14) unique, route normaliza input | N/A | **COBERTA** |
| **R3 CARTEIRA 46 colunas imutavel** | 100% — blueprint preserva 46 | N/A (model tem 35 campos, nao as 46 originais do Excel) | N/A | **N/A no SaaS** |
| **R4 Formulas openpyxl em INGLES** | 100% | N/A (sem openpyxl no backend) | N/A | **N/A no SaaS** |
| **R5 NUNCA openpyxl para slicers** | 100% | N/A | N/A | **N/A no SaaS** |
| **R6 Relatorios Mercos MENTEM** | 100% — import_pipeline verifica datas | N/A | N/A | **N/A no SaaS** |
| **R7 Faturamento = R$ 2.091.000** | 100% — projecao_engine usa FATURAMENTO_BASELINE | 100% — routes_dashboard.py: `FATURAMENTO_BASELINE = 2_091_000.0` | 100% — projecao/page.tsx: `BASELINE_2025 = 2091000` | **COBERTA** |
| **R8 Zero fabricacao de dados** | 100% — classify.py filtra ALUCINACAO | 100% — seed ignora ALUCINACAO, KPIs excluem | N/A | **COBERTA (leitura)** |
| **R9 Visual LIGHT** | N/A | N/A | 100% — cores R9 no StatusBadge, fundo branco | **COBERTA** |

### 3.2 Regras de Motor — Cobertura Detalhada

| Regra de Motor | Motor Python | Integrada no Backend | Executavel via API | Status |
|----------------|-------------|---------------------|-------------------|--------|
| **Score 6 fatores** (FASE 25%, SINALEIRO 20%, ABC 20%, TEMPERATURA 15%, TIPO 10%, TENTATIVAS 10%) | 100% em score_engine.py | NAO — score e calculado offline, resultado apenas lido do JSON | NAO — sem endpoint de recalculo | **GAP** |
| **92 combinacoes SITUACAO x RESULTADO** (7 situacoes x 14 resultados) | 100% em motor_regras.py | NAO — regras nao rodam no backend | NAO — nao existe formulario de resultado | **GAP** |
| **Sinaleiro 4 cores** (VERDE/AMARELO/VERMELHO/ROXO baseado em dias_sem_compra vs ciclo_medio) | 100% em sinaleiro_engine.py | NAO — valor vem do JSON, nao recalculado | NAO | **GAP** |
| **Agenda 40/dia** (P0 ilimitado, P7 nunca, 40 por consultor, 20 Daiane) | 100% em agenda_engine.py | NAO — agenda vem do JSON, nao gerada | NAO | **GAP** |
| **Prioridade P0-P7** (P0/P1 por bloqueio, P2-P6 por score, P7 nutricao) | 100% em score_engine.py | NAO | NAO | **GAP** |
| **Meta Balance** (se P2-P5 nao cobrem 80% da meta, PROSPECCAO recebe +20 no score) | 100% em score_engine.py | NAO | NAO | **GAP** |
| **Tipo Cliente** (PROSPECT -> NOVO -> EM DESENVOLVIMENTO -> RECORRENTE -> FIDELIZADO) | 100% em sinaleiro_engine.py | NAO | NAO | **GAP** |
| **Curva ABC** (Pareto por faturamento: A>=R$2000, B>=R$500, C<R$500) | 100% em sinaleiro_engine.py (e motor_regras.py) | ARMAZENADA — curva_abc vem do JSON | Exibida como badge | **PARCIAL** |
| **Tentativas T1-T4-NUTRICAO** | 100% em motor_regras.py | ARMAZENADA | NAO exibida explicitamente | **PARCIAL** |
| **DE-PARA Vendedores** (11 aliases -> 4 consultores + LEGADO) | 100% em agenda_engine.py + helpers.py | NORMALIZADA pelo seed.py | N/A | **OK** |

**Resumo: 0 de 10 regras de motor executaveis em tempo real no SaaS. Todas operam apenas como dados estaticos importados do JSON.**

---

## 4. DADOS — O QUE MIGRAR

### 4.1 Mapeamento de Fontes para Banco

| Fonte | Registros Estimados | Tabela DB Alvo | Status Migracao |
|-------|--------------------|-----------------|--------------------|
| `pipeline_output.json` | 1.581 clientes | `clientes` | **OK via seed.py** |
| `agenda_*.json` (4 arquivos) | 140 itens | `agenda_items` | **OK via seed.py** |
| LOG atendimentos (Excel/Deskrio) | ~20.830 registros | `log_atendimentos` (NAO EXISTE) | **NAO MIGRADO** |
| Pedidos SAP | ~5.000+ registros | `pedidos` (NAO EXISTE) | **NAO MIGRADO** |
| Vendas Mercos | ~3.000+ registros | `vendas_mercos` (NAO EXISTE) | **NAO MIGRADO** |
| Metas SAP (por cliente/mes) | ~660 x 12 = ~7.920 | `metas` (NAO EXISTE) | **NAO MIGRADO** |
| Redes/Franquias | ~30 redes | `redes` (NAO EXISTE) | **NAO MIGRADO** |
| Contatos Deskrio | 15.468 contatos | `contatos_whatsapp` (NAO EXISTE) | **NAO MIGRADO** |
| intelligence/*.json | 13 JSONs | Pode ficar como JSON no filesystem | **N/A** |

### 4.2 Estimativa de Tabelas Necessarias

| Tabela | Campos Essenciais | Registros Estimados | Prioridade |
|--------|-------------------|---------------------|------------|
| `clientes` (EXISTE) | 35 campos | 1.581 | — |
| `agenda_items` (EXISTE) | 12 campos | 140 por dia (x 260 dias/ano = ~36.400/ano) | — |
| `log_atendimentos` (CRIAR) | id, cnpj, consultor, data_hora, tipo_contato, resultado, estagio_funil, acao_futura, temperatura, tentativa, observacoes, classificacao_3tier, created_at | 20.830 historicos + ~60/dia novos | **P0** |
| `pedidos` (CRIAR) | id, cnpj, numero_pedido, data_pedido, valor, origem (SAP/Mercos), status | ~5.000+ | **P1** |
| `metas` (CRIAR) | id, cnpj, consultor, mes, ano, meta_valor, realizado_valor | ~7.920 | **P1** |
| `redes` (CRIAR) | id, nome_rede, tipo (franquia/rede), cnpjs_filiais[], meta_potencial, realizado_penetracao | ~30 | **P2** |
| `usuarios` (CRIAR) | id, nome, email, senha_hash, role (admin/consultor/gerente), consultor_vinculado | ~6 | **P0** |
| `configuracoes` (CRIAR) | chave, valor, tipo, descricao | ~20 | **P2** |
| `historico_score` (CRIAR) | id, cnpj, data, score, prioridade, sinaleiro | rastreabilidade | **P3** |

### 4.3 Mapeamento Detalhado: pipeline_output.json -> tabela clientes

| Campo JSON (motor) | Coluna DB (cliente.py) | Tipo | Presente |
|---------------------|------------------------|------|----------|
| cnpj_normalizado | cnpj | String(14) | SIM |
| nome_fantasia | nome_fantasia | String(255) | SIM |
| razao_social | razao_social | String(255) | SIM |
| uf | uf | String(2) | SIM |
| cidade | cidade | String(100) | SIM |
| consultor_normalizado | consultor | String(50) | SIM |
| situacao | situacao | String(20) | SIM |
| dias_sem_compra | dias_sem_compra | Integer | SIM |
| valor_ultimo_pedido | valor_ultimo_pedido | Float | SIM |
| ciclo_medio | ciclo_medio | Float | SIM |
| n_compras | n_compras | Integer | SIM |
| faturamento_total | faturamento_total | Float | SIM |
| tipo_contato | tipo_contato | String(50) | SIM |
| resultado | resultado | String(50) | SIM |
| estagio_funil | estagio_funil | String(50) | SIM |
| acao_futura | acao_futura | String(100) | SIM |
| temperatura | temperatura | String(20) | SIM |
| score | score | Float | SIM |
| prioridade | prioridade | String(5) | SIM |
| sinaleiro | sinaleiro | String(20) | SIM |
| curva_abc | curva_abc | String(1) | SIM |
| classificacao_3tier | classificacao_3tier | String(15) | SIM |
| fase | fase | String(30) | SIM |
| followup_dias | followup_dias | Integer | SIM |
| grupo_dash | grupo_dash | String(50) | SIM |
| tipo_acao | tipo_acao | String(50) | SIM |
| tentativas | tentativas | String(5) | SIM |
| problema_aberto | problema_aberto | Boolean | SIM |
| followup_vencido | followup_vencido | Boolean | SIM |
| cs_no_prazo | cs_no_prazo | Boolean | SIM |
| meta_anual | meta_anual | Float | SIM |
| realizado_acumulado | realizado_acumulado | Float | SIM |
| pct_alcancado | pct_alcancado | Float | SIM |
| gap_valor | gap_valor | Float | SIM |
| status_meta | status_meta | String(10) | SIM |
| **telefone** | NAO EXISTE | — | **GAP** |
| **email** | NAO EXISTE | — | **GAP** |
| **endereco_completo** | NAO EXISTE | — | **GAP** |
| **segmento** | NAO EXISTE | — | **GAP** |
| **oportunidade** | NAO EXISTE | — | **GAP** |
| **acesso_b2b** | NAO EXISTE | — | **GAP** |
| **itens_carrinho** | NAO EXISTE | — | **GAP** |

---

## 5. PRIORIZACAO DE GAPS

### P0 — CRITICO (sem isso NAO funciona como SaaS)

| # | Gap | Esforco | Impacto | Dependencias |
|---|-----|---------|---------|--------------|
| 1 | **Model + API + Pagina de LOG de Atendimentos** | ALTO (3-5 dias) | O CRM e sobre registrar interacoes. Sem LOG = nao e CRM. | Model LogAtendimento, POST endpoint, formulario frontend |
| 2 | **Motor de Regras integrado ao backend** | MEDIO (2-3 dias) | Quando consultor registra resultado, motor DEVE rodar automaticamente gerando estagio/fase/acao/temperatura/tentativa | Service que importa motor_regras.py |
| 3 | **Agenda com acoes (marcar feito, registrar resultado)** | MEDIO (2-3 dias) | Agenda sem acao = lista passiva. Consultor precisa marcar "feito" e registrar resultado que alimenta o motor. | PUT agenda, POST log, motor integrado |
| 4 | **Autenticacao basica** | MEDIO (2 dias) | 4 consultores + 1 gerente precisam login individual. Sem auth = dados expostos. | Model Usuario, JWT, middleware, tela login |
| 5 | **Score Engine integrado** | MEDIO (2 dias) | Quando motor roda, score precisa recalcular. Agenda depende do score atualizado. | Service que importa score_engine.py |
| 6 | **Sinaleiro Engine integrado** | BAIXO (1 dia) | Sinaleiro recalcula quando dados de compra mudam. | Service que importa sinaleiro_engine.py |

**Esforco total P0: ~12-16 dias de desenvolvimento**

### P1 — IMPORTANTE (funciona parcialmente sem, mas limita muito)

| # | Gap | Esforco | Impacto |
|---|-----|---------|---------|
| 7 | **CRUD de clientes** (POST/PUT/DELETE) | MEDIO (2 dias) | Gerente precisa criar/editar clientes, corrigir dados |
| 8 | **Alembic migrations** | BAIXO (1 dia) | Sem migrations, cada mudanca de schema = recreate do banco |
| 9 | **Import pipeline via API** | MEDIO (2 dias) | Precisa conseguir importar novos dados sem rodar script manual |
| 10 | **Testes automatizados** (backend + frontend) | MEDIO (3 dias) | Sem testes = regressoes silenciosas |
| 11 | **Agenda com geracao automatica** | MEDIO (2 dias) | Agenda deve ser gerada pelo score_engine diariamente, nao apenas de JSON estatico |
| 12 | **State management frontend** (Zustand/Context) | BAIXO (1 dia) | Estados globais (usuario logado, filtros, notificacoes) |
| 13 | **Formularios e validacao** (react-hook-form + zod) | MEDIO (2 dias) | Para LOG, edicao de cliente, configuracoes |

**Esforco total P1: ~13 dias**

### P2 — DESEJAVEL (melhoria incremental)

| # | Gap | Esforco | Impacto |
|---|-----|---------|---------|
| 14 | **WhatsApp via Deskrio** | ALTO (5 dias) | Integracao com 26 endpoints Deskrio, 15.468 contatos |
| 15 | **Mercos integracao** | MEDIO (3 dias) | Sincronizar pedidos automaticamente |
| 16 | **SAP integracao** | MEDIO (3 dias) | Sincronizar faturamento e metas |
| 17 | **Export CSV/Excel** | BAIXO (1 dia) | Botao de exportar na carteira |
| 18 | **Docker + deploy** | MEDIO (2 dias) | Dockerfile + docker-compose + env config |
| 19 | **Dashboard com graficos de tendencia** | MEDIO (2 dias) | Chart.js/Recharts com historico mensal |
| 20 | **Busca global** | BAIXO (1 dia) | Campo de busca no header com autocomplete |
| 21 | **Pagina de Redes/Franquias** | MEDIO (2 dias) | Painel de penetracao por rede |
| 22 | **Filtros avancados na carteira** | BAIXO (1 dia) | ABC, temperatura, UF, busca texto |

**Esforco total P2: ~20 dias**

### P3 — FUTURO (pode esperar)

| # | Gap | Esforco | Impacto |
|---|-----|---------|---------|
| 23 | **Notificacoes real-time** (WebSocket) | MEDIO (3 dias) | Follow-ups vencidos, alertas de sinaleiro |
| 24 | **Relatorios automaticos** | MEDIO (3 dias) | PDF/Excel semanal para gerencia |
| 25 | **Historico de score** | BAIXO (1 dia) | Rastreabilidade de mudancas de score |
| 26 | **PWA** | BAIXO (1 dia) | Acesso mobile offline |
| 27 | **Asana integracao** | MEDIO (2 dias) | Sincronizar tarefas |
| 28 | **CI/CD pipeline** | MEDIO (2 dias) | GitHub Actions para build/test/deploy |
| 29 | **Multi-tenancy** | ALTO (5 dias) | Suporte a multiplas empresas |
| 30 | **IA preditiva** | ALTO (5 dias) | Modelos ML para previsao de churn/venda |

**Esforco total P3: ~22 dias**

---

## 6. RESUMO QUANTITATIVO

### 6.1 Completude por Camada

| Camada | Existente | Necessario | % Completude |
|--------|-----------|------------|--------------|
| **Motor Python** | 14 modulos, 8 stages, 92 regras | 14 modulos | **100%** |
| **Backend Models** | 2 models (Cliente, AgendaItem) | 9 models | **22%** |
| **Backend Routes** | 9 endpoints GET | ~30 endpoints (GET+POST+PUT+DELETE) | **30%** |
| **Backend Services** | 1 service (seed) | 9 services | **11%** |
| **Backend Infra** | SQLAlchemy+CORS+Health | +Alembic+Auth+Background+Docker | **30%** |
| **Frontend Pages** | 4 paginas (Dashboard, Carteira, Agenda, Projecao) | 10 paginas | **40%** |
| **Frontend Components** | 6 componentes | 12+ componentes | **50%** |
| **Frontend API client** | 7 funcoes + 2 helpers | 15+ funcoes | **47%** |
| **Dados migrados** | 1.721 registros (1581 clientes + 140 agenda) | ~55.000+ registros (LOG+pedidos+metas) | **3%** |
| **Testes** | 1 (test_pipeline.py) | 30+ (unit + integration + e2e) | **3%** |

### 6.2 Esforco Total Estimado

| Prioridade | Dias de Dev | Funcionalidades |
|------------|------------|-----------------|
| **P0 (CRITICO)** | **12-16 dias** | LOG, Motor integrado, Agenda interativa, Auth, Score, Sinaleiro |
| **P1 (IMPORTANTE)** | **13 dias** | CRUD, Alembic, Import, Testes, Agenda auto, State mgmt, Forms |
| **P2 (DESEJAVEL)** | **20 dias** | WhatsApp, Mercos, SAP, Export, Docker, Graficos, Busca, Redes |
| **P3 (FUTURO)** | **22 dias** | Notificacoes, Relatorios, Historico, PWA, Asana, CI/CD, Multi-tenant, IA |
| **TOTAL** | **~67-71 dias** | 30 gaps identificados |

### 6.3 Recomendacao de Ordem de Execucao (Sprint Plan)

**Sprint 1 (Semana 1-2): Fundacao do SaaS**
1. Model LogAtendimento + tabela no banco
2. Autenticacao basica (JWT + login)
3. Alembic setup (migrations)
4. Service de Motor integrado ao backend (importar motor_regras.py como modulo)

**Sprint 2 (Semana 3-4): Fluxo Principal**
5. POST /api/log (registrar atendimento que dispara motor)
6. PUT /api/agenda/{id} (marcar feito com resultado)
7. Pagina de LOG no frontend (formulario + historico)
8. Score Engine integrado (recalcula quando motor roda)
9. Sinaleiro Engine integrado

**Sprint 3 (Semana 5-6): Completar CRUD + Testes**
10. CRUD completo de clientes
11. Agenda com geracao automatica diaria
12. Testes unitarios (backend + frontend)
13. State management frontend
14. Formularios com validacao

**Sprint 4 (Semana 7-8): Integracoes + Polish**
15. Export CSV/Excel
16. Import pipeline via API
17. Dashboard com graficos de tendencia
18. Filtros avancados
19. Docker setup

---

## 7. DESALINHAMENTOS DETECTADOS

### 7.1 Frontend vs Backend — Tipos Desalinhados

| Campo Frontend (`ClienteRegistro`) | Existe no Backend (`ClienteDetalhe`) | Status |
|-------------------------------------|--------------------------------------|--------|
| `segmento` | NAO | **DESALINHADO** — frontend espera, backend nao retorna |
| `ticket_medio` | NAO | **DESALINHADO** |
| `meta_mensal` | NAO (tem `meta_anual`) | **DESALINHADO** |
| `ultima_compra` | NAO | **DESALINHADO** |
| `followups_vencidos` (KPIs) | SIM no backend | **FALTA no tipo frontend** |

### 7.2 Motor vs Backend — Campos Nao Utilizados

O model `Cliente` armazena 35 campos do motor, porem o backend ignora campos de inteligencia para calculos:
- `grupo_dash`, `tipo_acao`, `tentativas` — armazenados mas nao usados em nenhum endpoint
- `fase` — armazenada mas nao exposta na listagem (so no detalhe)
- `estagio_funil` — armazenado mas sem endpoint de funil

### 7.3 Regra R7 — Faturamento Baseline

| Local | Valor | Status |
|-------|-------|--------|
| Motor Python (projecao_engine.py) | R$ 2.091.000 | OK |
| Backend (routes_dashboard.py) | R$ 2.091.000 | OK |
| Frontend (projecao/page.tsx) | R$ 2.091.000 | OK |
| **Consistente em todas as camadas** | | **OK** |

---

## 8. CONCLUSAO

O CRM VITAO360 possui um **motor Python excepcional** — 100% completo com 92 combinacoes de regras, score de 6 fatores, sinaleiro de 4 cores, projecao SAP, e agenda automatica para 4 consultores. O pipeline roda em 0.41s e produz JSONs prontos para consumo.

O **SaaS scaffold** esta em ~8-12% de completude geral. Os **dados fluem em direcao unica**: Motor Python -> JSON -> seed.py -> SQLite -> API GET -> Frontend leitura. **Nao existe fluxo reverso** (usuario registra acao -> motor recalcula -> banco atualiza -> tela reflete).

O gap mais critico e a ausencia do **ciclo operacional completo**: consultor abre agenda -> atende cliente -> registra resultado -> motor roda -> score recalcula -> sinaleiro atualiza -> proxima agenda reflete. Este ciclo e o **coracao** do CRM e requer a integracao dos 6 gaps P0.

**Esforco para MVP funcional (P0): ~12-16 dias de desenvolvimento.**
**Esforco para produto completo (P0+P1+P2): ~45-49 dias.**

---

*Documento gerado por analise forense de 60+ arquivos do codebase CRM VITAO360.*
*Cada arquivo foi lido e catalogado individualmente — nenhum dado foi assumido.*
