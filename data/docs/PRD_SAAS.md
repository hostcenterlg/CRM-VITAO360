# PRD -- CRM VITAO360 SaaS

## Motor de Inteligencia Comercial -- Migracao Excel para Plataforma Web

**Versao:** 1.0
**Data:** 25/03/2026
**Status:** Em Revisao
**Autor:** @pm (Product Manager)
**Proprietario:** Leandro -- VITAO Alimentos
**Idioma:** Portugues Brasileiro

---

## INDICE

1. [Visao do Produto](#1-visao-do-produto)
2. [Personas](#2-personas)
3. [Epicos (E1-E14)](#3-epicos)
4. [Features por Epico](#4-features-por-epico)
5. [Requisitos Nao-Funcionais](#5-requisitos-nao-funcionais)
6. [Priorizacao MoSCoW](#6-priorizacao-moscow)
7. [Dependencias entre Epicos](#7-dependencias-entre-epicos)
8. [MVP vs Full](#8-mvp-vs-full)
9. [Modelo Financeiro](#9-modelo-financeiro)
10. [Riscos e Mitigacoes](#10-riscos-e-mitigacoes)
11. [Metricas de Sucesso](#11-metricas-de-sucesso)
12. [Glossario](#12-glossario)

---

## 1. VISAO DO PRODUTO

### 1.1 O Que E

CRM VITAO360 SaaS e uma plataforma web de inteligencia comercial para distribuidoras B2B de alimentos naturais. Transforma o motor de regras ja funcional (92 combinacoes, 9 dimensoes, Score 6 fatores, Sinaleiro, Agenda inteligente) de uma planilha Excel com 40 abas e 200K+ formulas em uma aplicacao web com banco de dados relacional, API REST, integracao WhatsApp (Deskrio), ERP (Mercos/SAP) e automacao de tarefas (Asana).

### 1.2 Para Quem

**Usuarios primarios:**
- 4 consultores comerciais internos (Manu, Larissa, Daiane, Julio)
- 1 gestor comercial (Leandro -- admin)

**Usuarios secundarios (v2):**
- 1 operador pos-venda (contratacao prevista Q3 2026)
- 1 RCA externo (Julio Gadret -- acesso parcial)

### 1.3 Por Que Migrar

| Limitacao Excel | Solucao SaaS |
|-----------------|-------------|
| 40 abas, 200K+ formulas -- planilha travando | Banco relacional + API: performance ilimitada |
| 144 colunas na CARTEIRA -- impossivel manter | Modelo normalizado com entidades relacionadas |
| Sem integracao real-time | APIs Mercos, SAP, Deskrio, Asana |
| 1 usuario por vez edita | Multi-usuario simultaneo com roles |
| Sem mobile | PWA / responsivo para consultores em campo |
| Formulas quebram (XLOOKUP, INDEX-MATCH) | Logica no backend: testavel, versionavel |
| Slicers destroem XML | Filtros nativos na UI |
| Dados em arquivo local | Cloud: backup automatico, acesso remoto |
| 558 registros ALUCINACAO misturados | Classificacao 3-tier enforced no banco |

### 1.4 Visao de Futuro

> Em 12 meses, o CRM VITAO360 SaaS sera a central de inteligencia comercial que:
> 1. Gera agenda diaria automatica para cada consultor (40-60 atendimentos/dia)
> 2. Prioriza clientes por Score ponderado de 6 dimensoes em tempo real
> 3. Dispara e recebe WhatsApp integrado (Deskrio)
> 4. Alimenta-se automaticamente de Mercos (vendas) e SAP (cadastro/metas)
> 5. Reduz churn de 80% para 50% via pos-venda estruturado
> 6. Projeta faturamento 2026 de R$ 3.377.120 (+69% vs 2025)

### 1.5 Principios de Design

1. **Motor primeiro, interface depois** -- A logica de negocios (92 regras, Score, Sinaleiro) e o diferencial. A UI e o canal.
2. **Two-Base Architecture inviolavel** -- VENDA = R$ real; LOG = R$ 0.00. Nunca misturar. Violacao causa inflacao de 742%.
3. **CNPJ como chave primaria de negocio** -- 14 digitos, string, zero-padded. Nunca float.
4. **Dados reais apenas** -- Classificacao 3-tier obrigatoria: REAL / SINTETICO / ALUCINACAO. Zero dados fabricados.
5. **Visual LIGHT exclusivamente** -- Sem dark mode. Cores padronizadas por status e classificacao.
6. **Valor imediato** -- Motor rodando > API perfeita. Pragmatismo sobre perfeccionismo.

---

## 2. PERSONAS

### P1 -- Leandro (Gestor / Admin)

| Atributo | Descricao |
|----------|-----------|
| **Cargo** | Gerente Comercial / Proprietario do produto |
| **Objetivo** | Visibilidade total: faturamento, churn, pipeline, performance por consultor |
| **Frustracao** | Planilha travando, dados desatualizados, decisoes sem evidencia |
| **Funcionalidades-chave** | Dashboard CEO, Projecao, Sinaleiro Redes, Configuracao de regras, Admin users |
| **Frequencia de uso** | Diaria (dashboard), semanal (projecao), mensal (estrategia) |
| **Nivel de acesso** | Admin -- acesso total, configura regras, vê todos os consultores |
| **Dispositivo** | Desktop (principal), mobile (consulta rapida) |

### P2 -- Manu Ditzel (Consultora SC/PR/RS)

| Atributo | Descricao |
|----------|-----------|
| **Cargo** | Representante PDV -- Sul do Brasil |
| **Territorio** | SC, PR, RS |
| **% Faturamento** | 32.5% do total |
| **Objetivo** | Saber quem ligar, em que ordem, com que acao |
| **Frustracao** | Nao saber quem esta esfriando, perder clientes por falta de follow-up |
| **Funcionalidades-chave** | Agenda diaria, Carteira pessoal, LOG de atendimentos, Score do cliente |
| **Observacao** | Entra em licenca maternidade Q2 2026 -- carteira sera redistribuida |
| **Frequencia de uso** | Diaria (agenda + LOG), durante toda jornada comercial |
| **Nivel de acesso** | Consultor -- ve apenas propria carteira |

### P3 -- Larissa Padilha (Consultora Nacional)

| Atributo | Descricao |
|----------|-----------|
| **Cargo** | Representante PDV -- Brasil Interior |
| **Territorio** | Todos os estados exceto SC/PR/RS |
| **% Faturamento** | ~45% do total (maior carteira) |
| **Clientes** | 291 clientes na carteira |
| **Objetivo** | Gerenciar grande volume de clientes com priorizacao automatica |
| **Frustracao** | Volume alto demais para acompanhar manualmente, clientes esfriando sem perceber |
| **Funcionalidades-chave** | Agenda inteligente (essencial pelo volume), filtros por regiao/UF, WhatsApp integrado |
| **Aliases** | Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo (operador do canal Mais Granel) |
| **Frequencia de uso** | Diaria intensiva -- precisa do sistema para priorizar 291 clientes |
| **Nivel de acesso** | Consultor -- ve apenas propria carteira |

### P4 -- Daiane Stavicki (Gerente + Key Account)

| Atributo | Descricao |
|----------|-----------|
| **Cargo** | Gerente Comercial + Key Account Redes/Franquias |
| **Territorio** | Nacional -- foco em 8 redes de franquias (923 lojas) |
| **% Faturamento** | 12.5% |
| **Objetivo** | Aumentar penetracao nas redes (<30% atual), gerenciar equipe |
| **Frustracao** | Nao saber penetracao real por rede, visitas sem priorizacao, Julio fora do sistema |
| **Funcionalidades-chave** | Sinaleiro de Redes, Dashboard por consultor, PAINEL penetracao, Visao gerencial |
| **Observacao** | Tem visao gerencial parcial (ve todos os consultores, nao configura regras) |
| **Frequencia de uso** | Diaria (operacional) + semanal (estrategica redes) |
| **Nivel de acesso** | Gerente -- ve todos consultores, nao configura sistema |

### P5 -- Julio Gadret (RCA Externo)

| Atributo | Descricao |
|----------|-----------|
| **Cargo** | Representante Comercial Autonomo |
| **Territorio** | Cia Saude + Fitland (redes especificas) |
| **% Faturamento** | ~10% |
| **Objetivo** | Ter acesso ao minimo necessario: carteira, agenda, registro de atendimento |
| **Frustracao** | 100% fora do sistema hoje. Nao registra nenhuma interacao. |
| **Funcionalidades-chave** | Agenda pessoal, LOG simplificado, Carteira propria |
| **Restricoes** | Acesso restrito -- nao ve outros consultores, nao ve dados financeiros sensivel |
| **Frequencia de uso** | Diaria (consulta agenda), semanal (registro LOGs acumulados) |
| **Nivel de acesso** | Consultor Externo -- ve apenas propria carteira, sem dados financeiros sensiveis |

---

## 3. EPICOS

### Mapa de Epicos

| Codigo | Nome | Fase | Complexidade | Estimativa |
|--------|------|------|-------------|-----------|
| E1 | Import Pipeline | MVP | Alta | 3-4 sprints |
| E2 | Motor de Regras no Backend | MVP | Alta | 2-3 sprints |
| E3 | Score + Sinaleiro em Tempo Real | MVP | Media | 1-2 sprints |
| E4 | Agenda Inteligente | MVP | Media | 2 sprints |
| E5 | Dashboard CEO | MVP | Media | 2-3 sprints |
| E6 | CARTEIRA Completa | MVP | Alta | 3-4 sprints |
| E7 | LOG Append-Only | MVP | Media | 2 sprints |
| E8 | Autenticacao e Roles | MVP | Media | 1-2 sprints |
| E9 | Integracao Deskrio (WhatsApp) | v2 | Alta | 3-4 sprints |
| E10 | Deploy (Vercel + Railway) | MVP | Baixa-Media | 1-2 sprints |
| E11 | Integracao Mercos (ERP Vendas) | v2 | Media-Alta | 2-3 sprints |
| E12 | Integracao SAP (Cadastro/Metas) | v2 | Media | 2 sprints |
| E13 | Projecao e Metas | v2 | Media | 2 sprints |
| E14 | RNC (Registro Nao-Conformidade) | v2 | Baixa | 1 sprint |

---

## 4. FEATURES POR EPICO

---

### E1 -- Import Pipeline (xlsx para banco)

**Descricao:** Migrar o pipeline Python existente (8 stages) para popular o banco de dados relacional a partir de arquivos xlsx exportados do Mercos, SAP e dados de atendimento. O motor Python ja funcional (`scripts/motor/import_pipeline.py`) sera adaptado para gravar no banco SQLAlchemy ao inves de gerar Excel.

**Referencia tecnica:** Pipeline atual: load -> normalize_cnpj -> classify -> merge -> motor_regras -> score -> sinaleiro -> agenda

#### Features

**FR-001 -- Upload de Arquivo xlsx**

| Campo | Valor |
|-------|-------|
| Descricao | Endpoint POST /api/import/upload que recebe arquivo .xlsx e inicia processamento |
| Prioridade MoSCoW | Must |
| Personas | P1 (Leandro) |
| Acceptance Criteria | 1. Aceita arquivos .xlsx ate 50MB. 2. Valida extensao e integridade do arquivo antes de processar. 3. Retorna job_id para tracking do progresso. 4. Rejeita formatos invalidos com HTTP 422 e mensagem descritiva. 5. Armazena arquivo temporariamente em /tmp com limpeza automatica em 24h. |

**FR-002 -- Normalizacao CNPJ no Import**

| Campo | Valor |
|-------|-------|
| Descricao | Stage que limpa e normaliza todos os CNPJs para string de 14 digitos zero-padded |
| Prioridade MoSCoW | Must |
| Personas | P1 |
| Acceptance Criteria | 1. Remove pontuacao (pontos, barras, hifens) de todo CNPJ. 2. Faz zero-padding para 14 digitos. 3. Nunca armazena CNPJ como float ou int. 4. Loga CNPJs invalidos (< 14 digitos apos limpeza) sem abortar pipeline. 5. Regex: `re.sub(r'\D', '', str(val)).zfill(14)`. 6. CNPJs duplicados no mesmo arquivo sao flaggados no relatorio de import. |

**FR-003 -- Classificacao 3-Tier (REAL/SINTETICO/ALUCINACAO)**

| Campo | Valor |
|-------|-------|
| Descricao | Cada registro importado recebe classificacao de confiabilidade |
| Prioridade MoSCoW | Must |
| Personas | P1 |
| Acceptance Criteria | 1. Dados de Mercos/SAP/Deskrio = REAL por padrao. 2. Dados calculados por formula a partir de REAL = SINTETICO. 3. Dados sem rastreabilidade = ALUCINACAO (nunca integrados). 4. Coluna `classificacao_3tier` obrigatoria em todas as tabelas de dados. 5. 558 registros previamente catalogados como ALUCINACAO continuam bloqueados. 6. Dashboard exclui ALUCINACAO de todos os calculos financeiros. |

**FR-004 -- Merge de Fontes (Mercos + SAP + Deskrio)**

| Campo | Valor |
|-------|-------|
| Descricao | Cruzamento de dados entre fontes usando CNPJ como chave, com matching fuzzy para nomes |
| Prioridade MoSCoW | Must |
| Personas | P1 |
| Acceptance Criteria | 1. Match por CNPJ normalizado (primary). 2. Fuzzy matching por razao social (rapidfuzz, score >= 85) como fallback. 3. De-para de vendedores aplicado automaticamente: Manu/Manu Vitao/Manu Ditzel -> MANU, etc. 4. Conflitos de dados entre fontes logados com origem vencedora (Mercos > SAP > Deskrio para vendas). 5. Relatorio de merge com: matched, unmatched, conflitos. |

**FR-005 -- Relatorio de Import**

| Campo | Valor |
|-------|-------|
| Descricao | Apos cada import, gerar relatorio com estatisticas: registros processados, novos, atualizados, erros, CNPJs invalidos |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. JSON/HTML com: total registros, novos clientes, clientes atualizados, CNPJs invalidos, duplicatas, ALUCINACAO detectada. 2. Warnings para divergencia de faturamento > 0.5% vs baseline R$ 2.091.000. 3. Historico de imports persistido no banco (tabela `import_logs`). 4. Endpoint GET /api/import/history para consultar ultimos imports. |

**FR-006 -- Processamento em Background**

| Campo | Valor |
|-------|-------|
| Descricao | Import de arquivos grandes roda como job assincrono com tracking de progresso |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Endpoint GET /api/import/status/{job_id} retorna progresso (0-100%). 2. Stages reportados individualmente (load 100%, normalize 45%, ...). 3. Timeout de 10 minutos para abort automatico. 4. Notificacao ao completar ou falhar. |

---

### E2 -- Motor de Regras no Backend

**Descricao:** Portar o motor de regras Python (`scripts/motor/motor_regras.py`) com suas 92 combinacoes de SITUACAO x RESULTADO para o backend FastAPI, mantendo todas as 9 dimensoes de saida. O motor e o cerebro do CRM: dado um par (SITUACAO, RESULTADO), retorna automaticamente ESTAGIO_FUNIL, FASE, TIPO_CONTATO, ACAO_FUTURA, TEMPERATURA, FOLLOWUP_DIAS, GRUPO_DASH, TIPO_ACAO e CHAVE.

**Referencia tecnica:** 7 SITUACOES (ATIVO, EM RISCO, INAT.REC, INAT.ANT, PROSPECT, LEAD, NOVO) x 14 RESULTADOS = 92 combinacoes

#### Features

**FR-007 -- Tabela de Regras no Banco**

| Campo | Valor |
|-------|-------|
| Descricao | 92 combinacoes armazenadas em tabela `motor_regras` com todas as 9 dimensoes de saida |
| Prioridade MoSCoW | Must |
| Personas | P1 |
| Acceptance Criteria | 1. Tabela `motor_regras` com colunas: id, situacao, resultado, estagio_funil, fase, tipo_contato, acao_futura, temperatura, followup_dias, grupo_dash, tipo_acao, chave. 2. Seed com as 92 combinacoes exatas do motor v4 auditado. 3. Chave unica em (situacao, resultado). 4. Nenhuma combinacao faltando -- cobertura 100%. 5. Valores identicos ao CHECKLIST MOTOR (2) da planilha FINAL. |

**FR-008 -- API de Lookup do Motor**

| Campo | Valor |
|-------|-------|
| Descricao | Endpoint GET /api/motor/lookup?situacao=X&resultado=Y que retorna as 9 dimensoes |
| Prioridade MoSCoW | Must |
| Personas | P1, P2, P3, P4, P5 |
| Acceptance Criteria | 1. Recebe situacao e resultado como query params. 2. Retorna JSON com todas as 9 dimensoes. 3. Retorna HTTP 404 se a combinacao nao existir. 4. Case-insensitive nos parametros. 5. Tempo de resposta < 50ms (lookup em tabela indexada). |

**FR-009 -- Aplicacao Automatica do Motor ao Registrar Atendimento**

| Campo | Valor |
|-------|-------|
| Descricao | Quando consultor registra um atendimento (LOG), o motor roda automaticamente e preenche as 9 dimensoes |
| Prioridade MoSCoW | Must |
| Personas | P2, P3, P4, P5 |
| Acceptance Criteria | 1. No POST /api/atendimentos, o backend calcula situacao atual do cliente. 2. Combina situacao + resultado informado pelo consultor. 3. Motor retorna e preenche automaticamente: estagio_funil, fase, tipo_contato, acao_futura, temperatura, followup_dias, grupo_dash, tipo_acao. 4. Atualiza o cliente com nova temperatura, estagio, fase. 5. Cria follow-up automatico baseado em followup_dias (ex: D+4 pos-venda, D+7 FU). |

**FR-010 -- Calculo de SITUACAO Automatico**

| Campo | Valor |
|-------|-------|
| Descricao | A SITUACAO do cliente e calculada automaticamente baseada em dias sem compra |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. PROSPECT: sem historico de compra (n_compras = 0 ou NULL). 2. ATIVO: dias_sem_compra <= 50. 3. EM RISCO: dias_sem_compra entre 51-60. 4. INAT.REC: dias_sem_compra entre 61-90. 5. INAT.ANT: dias_sem_compra > 90. 6. LEAD: lead qualificado sem compra. 7. NOVO: primeiro pedido recente (a definir threshold). 8. Recalculado diariamente via job scheduled e em tempo real ao registrar atendimento/venda. |

**FR-011 -- Painel Admin de Regras**

| Campo | Valor |
|-------|-------|
| Descricao | Tela admin para visualizar e (futuramente) editar as 92 regras do motor |
| Prioridade MoSCoW | Could |
| Personas | P1 |
| Acceptance Criteria | 1. Tabela com filtro por situacao mostrando todas as combinacoes. 2. Cada regra exibe as 9 dimensoes de saida. 3. Read-only no MVP. 4. Edicao futura (v2) com auditoria de alteracoes. |

---

### E3 -- Score + Sinaleiro em Tempo Real

**Descricao:** Portar o Score Engine (`scripts/motor/score_engine.py`) com 6 dimensoes ponderadas e o Sinaleiro Engine (`scripts/motor/sinaleiro_engine.py`) para calculo em tempo real no backend. O Score determina a prioridade P0-P7 de cada cliente e o Sinaleiro indica a saude do cliente (dias sem comprar vs ciclo medio).

**Referencia tecnica:**
- Score = (FASE x 25%) + (SINALEIRO x 20%) + (ABC x 20%) + (TEMPERATURA x 15%) + (TIPO_CLIENTE x 10%) + (TENTATIVAS x 10%)
- Sinaleiro = ratio (dias_sem_compra / ciclo_medio): VERDE (<=0.5), AMARELO (<=1.0), LARANJA (<=1.5), VERMELHO (>1.5), ROXO (sem historico)

#### Features

**FR-012 -- Calculo de Score Ponderado**

| Campo | Valor |
|-------|-------|
| Descricao | Calcular Score 0-100 para cada cliente baseado em 6 dimensoes ponderadas |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. FASE: RECOMPRA=100, NEGOCIACAO=80, SALVAMENTO=60, RECUPERACAO=40, PROSPECCAO=30, NUTRICAO=10. Peso 25%. 2. SINALEIRO: VERMELHO=100, AMARELO=60, VERDE=30, ROXO=0. Peso 20%. 3. CURVA ABC: A=100, B=60, C=30. Peso 20%. 4. TEMPERATURA: QUENTE=100, MORNO=60, FRIO=30, CRITICO=20, PERDIDO=0. Peso 15%. 5. TIPO_CLIENTE: MADURO=100, FIDELIZADO=85, RECORRENTE=70, EM_DESENV=50, NOVO=30, LEAD=15, PROSPECT=10. Peso 10%. 6. TENTATIVAS: T1=100, T2=70, T3=40, T4=10, NUTRICAO=5. Peso 10%. 7. Score arredondado para inteiro. 8. Recalculado em tempo real ao registrar atendimento. |

**FR-013 -- Classificacao de Prioridade P0-P7**

| Campo | Valor |
|-------|-------|
| Descricao | Mapear Score calculado para nivel de prioridade P0 a P7 |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. P0 (IMEDIATA): SUPORTE com problema aberto -- pula fila (nao depende de score). 2. P1 (URGENTE): EM ATENDIMENTO + follow-up vencido + CS no prazo (nao depende de score). 3. P2 (ALTA): Score 80-100, distribuicao ate 15-20/dia. 4. P3 (MEDIA-ALTA): Score 60-79, distribuicao 15-20/dia. 5. P4 (MEDIA): Score 45-59, distribuicao 5-10/dia. 6. P5 (MEDIA-BAIXA): Score 30-44, distribuicao 5-10/dia. 7. P6 (BAIXA): Score 15-29, distribuicao 0-5/dia. 8. P7 (NUTRICAO): Score 0-14, campanha mensal (0/dia na agenda regular). |

**FR-014 -- Calculo de Sinaleiro**

| Campo | Valor |
|-------|-------|
| Descricao | Indicador de saude do cliente baseado na relacao dias sem compra vs ciclo medio |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. ROXO: sem historico (prospect, lead). 2. VERDE: ratio <= 0.5 (saudavel -- dentro da metade do ciclo). 3. AMARELO: ratio <= 1.0 (atencao -- proximo ao ciclo). 4. LARANJA: ratio <= 1.5 (alerta -- passou do ciclo). 5. VERMELHO: ratio > 1.5 (critico -- muito atrasado). 6. Cliente NOVO sem ciclo medio recebe VERDE por default. 7. Cores: VERDE=#00B050, AMARELO=#FFC000, VERMELHO=#FF0000, ROXO=#7030A0. |

**FR-015 -- Desempate de Score**

| Campo | Valor |
|-------|-------|
| Descricao | Quando dois clientes tem mesmo Score, aplicar criterios de desempate |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. Primeiro: CURVA ABC (A > B > C). 2. Segundo: Ticket Medio (maior primeiro). 3. Terceiro: TIPO CLIENTE (mais maduro primeiro). 4. Quarto: Follow-up mais vencido primeiro. 5. Implementado na query de ordenacao da agenda. |

**FR-016 -- API de Score**

| Campo | Valor |
|-------|-------|
| Descricao | Endpoint GET /api/clientes/{cnpj}/score com breakdown das 6 dimensoes |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Retorna: score_total, prioridade, e valor de cada dimensao (fase_score, sinaleiro_score, abc_score, temperatura_score, tipo_cliente_score, tentativas_score). 2. Inclui pesos aplicados. 3. Tempo de resposta < 100ms. |

**FR-017 -- Meta Balance**

| Campo | Valor |
|-------|-------|
| Descricao | Se P2-P5 nao cobrem 80% da meta mensal, PROSPECCAO ganha +20 pontos |
| Prioridade MoSCoW | Could |
| Personas | P1 |
| Acceptance Criteria | 1. Job diario calcula se pipeline atual (P2-P5) cobre 80% da meta. 2. Se nao, clientes em fase PROSPECCAO recebem bonus de +20 no score. 3. Bonus removido automaticamente quando meta >= 80% coberta. 4. Flag visual na agenda indicando "Modo Prospeccao ativo". |

---

### E4 -- Agenda Inteligente (40-60/dia)

**Descricao:** Tela principal do consultor: lista priorizada de 40-60 clientes para contatar no dia, ordenada por Score descendente, com acao sugerida pelo Motor e indicadores visuais de urgencia.

**Referencia tecnica:** `scripts/motor/agenda_engine.py` -- gera agenda por consultor filtrando carteira, calculando score e limitando a 40-60.

#### Features

**FR-018 -- Geracao Automatica de Agenda Diaria**

| Campo | Valor |
|-------|-------|
| Descricao | Job que roda diariamente (ou sob demanda) gerando agenda priorizada para cada consultor |
| Prioridade MoSCoW | Must |
| Personas | P2, P3, P4, P5 |
| Acceptance Criteria | 1. Filtra clientes por consultor responsavel. 2. Calcula Score atualizado para todos. 3. Aplica Motor para gerar acao sugerida. 4. Ordena: P0 primeiro (pula fila), P1 segundo, depois por Score desc. 5. Limita entre 40-60 itens por consultor. 6. Remove duplicatas por CNPJ. 7. Persiste em tabela `agenda_items` com data, consultor, posicao. 8. Gera automaticamente as 05:00 BRT (cron). |

**FR-019 -- Tela de Agenda do Consultor**

| Campo | Valor |
|-------|-------|
| Descricao | Interface visual da agenda diaria com cards priorizados |
| Prioridade MoSCoW | Must |
| Personas | P2, P3, P4, P5 |
| Acceptance Criteria | 1. Lista com posicao (1 a N), nome fantasia, CNPJ, Score, Prioridade (badge colorido), Sinaleiro (cor), Temperatura, Acao Sugerida. 2. Filtro por prioridade (P0-P7). 3. Busca por nome/CNPJ. 4. Click no item abre detalhe do cliente + acao para registrar atendimento. 5. Indicador visual de follow-up vencido (destaque vermelho). 6. Contador: "23 de 45 atendidos hoje". |

**FR-020 -- Marcar Atendimento Realizado**

| Campo | Valor |
|-------|-------|
| Descricao | Dentro da agenda, consultor marca item como atendido, registrando resultado |
| Prioridade MoSCoW | Must |
| Personas | P2, P3, P4, P5 |
| Acceptance Criteria | 1. Dropdown de RESULTADO (14 opcoes: VENDA/PEDIDO, ORCAMENTO, POS-VENDA, CS, RELACIONAMENTO, FU 7, FU 15, EM ATENDIMENTO, SUPORTE, NAO ATENDE, NAO RESPONDE, RECUSOU LIGACAO, CADASTRO, PERDA/FECHOU LOJA). 2. Campo descricao (texto livre, obrigatorio). 3. Ao salvar: cria registro no LOG, roda Motor automaticamente, atualiza Score/Sinaleiro. 4. Item muda visual para "concluido" (checkmark verde). 5. Acao futura e proximo follow-up exibidos apos salvar (feedback do motor). |

**FR-021 -- Agenda Historica**

| Campo | Valor |
|-------|-------|
| Descricao | Visualizar agenda de dias anteriores (somente leitura) |
| Prioridade MoSCoW | Should |
| Personas | P1, P2, P3, P4 |
| Acceptance Criteria | 1. Date picker para selecionar data. 2. Exibe agenda do dia com status (atendido/nao atendido). 3. Metricas: total planejado, total atendido, % completude. 4. Somente leitura (nao permite registrar retroativamente). |

**FR-022 -- Redistribuicao de Carteira**

| Campo | Valor |
|-------|-------|
| Descricao | Admin pode redistribuir clientes de um consultor para outro (cenario licenca Manu) |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Tela admin: seleciona consultor origem e consultor destino. 2. Opcao de redistribuir todos ou selecionar por filtro (UF, ABC, situacao). 3. Historico da redistribuicao logado com timestamp e motivo. 4. Agenda regenerada automaticamente apos redistribuicao. |

---

### E5 -- Dashboard CEO

**Descricao:** Painel executivo com KPIs em tempo real para Leandro, mostrando saude do negocio, distribuicoes por dimensao e tendencias. Substitui o PAINEL CEO da planilha (3 blocos: KPIs Executivos, Sinaleiro CRM, Ramp-up Equipe).

**Referencia tecnica:** Endpoints ja existentes em `routes_dashboard.py`: /api/dashboard/kpis, /distribuicao, /top10, /projecao

#### Features

**FR-023 -- KPIs Executivos**

| Campo | Valor |
|-------|-------|
| Descricao | Cards com indicadores principais do negocio |
| Prioridade MoSCoW | Must |
| Personas | P1, P4 |
| Acceptance Criteria | 1. Total Clientes (489 esperado). 2. Ativos (badge verde). 3. Prospects. 4. Inativos (INAT.REC + INAT.ANT). 5. Faturamento Total (apenas REAL + SINTETICO, nunca ALUCINACAO). 6. Media Score. 7. Clientes em Alerta (sinaleiro VERMELHO + AMARELO). 8. Follow-ups Vencidos. 9. Clientes Criticos (temperatura CRITICO). 10. Baseline R$ 2.091.000 como referencia. 11. Atualizacao em tempo real (ou refresh manual). |

**FR-024 -- Distribuicoes por Dimensao**

| Campo | Valor |
|-------|-------|
| Descricao | Graficos de distribuicao da carteira por cada dimensao do Motor |
| Prioridade MoSCoW | Must |
| Personas | P1, P4 |
| Acceptance Criteria | 1. Por Sinaleiro: pie/donut com cores (VERDE, AMARELO, LARANJA, VERMELHO, ROXO). 2. Por Situacao: barras (ATIVO, EM RISCO, INAT.REC, INAT.ANT, PROSPECT, LEAD, NOVO). 3. Por Prioridade: barras horizontais (P0-P7). 4. Por Consultor: barras com faturamento e qtd clientes. 5. Por Curva ABC: pie (A=20%, B=30%, C=50%). 6. Por Temperatura: barras com cores. 7. Todos clicaveis: click filtra a carteira pelo valor selecionado. |

**FR-025 -- Top 10 Clientes**

| Campo | Valor |
|-------|-------|
| Descricao | Ranking dos 10 maiores clientes por faturamento |
| Prioridade MoSCoW | Must |
| Personas | P1 |
| Acceptance Criteria | 1. Tabela com: posicao, nome fantasia, consultor, faturamento, score, prioridade, curva ABC, sinaleiro. 2. Apenas registros REAL ou SINTETICO (R8). 3. Click no cliente abre detalhe. 4. Exportavel para CSV. |

**FR-026 -- Visao por Consultor**

| Campo | Valor |
|-------|-------|
| Descricao | Dashboard filtrado por consultor individual |
| Prioridade MoSCoW | Should |
| Personas | P1, P4 |
| Acceptance Criteria | 1. Selector de consultor (MANU, LARISSA, DAIANE, JULIO). 2. KPIs filtrados: faturamento, ativos, inativos, score medio, completude agenda. 3. Mini-carteira com top 10 do consultor. 4. Comparativo entre consultores (overlay). |

**FR-027 -- Tendencias Temporais**

| Campo | Valor |
|-------|-------|
| Descricao | Graficos de evolucao ao longo do tempo |
| Prioridade MoSCoW | Could |
| Personas | P1 |
| Acceptance Criteria | 1. Evolucao de clientes ativos/inativos por mes (line chart). 2. Evolucao de faturamento mensal. 3. Tendencia de churn. 4. Dados de pelo menos 6 meses historicos. |

---

### E6 -- CARTEIRA Completa

**Descricao:** Tela principal de gestao de clientes, substituindo a aba CARTEIRA (1.593 rows x 144 colunas). Interface tabular com filtros avancados por todas as dimensoes do Motor, busca, paginacao e detalhe expandido do cliente.

**Referencia tecnica:** Endpoint existente: GET /api/clientes com filtros por consultor, situacao, sinaleiro, curva_abc, temperatura, prioridade, UF, busca. Model `Cliente` com 35+ campos.

#### Features

**FR-028 -- Listagem de Clientes com Filtros**

| Campo | Valor |
|-------|-------|
| Descricao | Tabela paginada de clientes com filtros cumulativos por todas as dimensoes |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. Colunas visiveis: CNPJ, Nome Fantasia, UF, Consultor, Situacao (badge colorido), Temperatura, Score, Prioridade, Sinaleiro (icone cor), Curva ABC, Faturamento Total. 2. Filtros: Consultor, Situacao, Sinaleiro, Curva ABC, Temperatura, Prioridade, UF. 3. Busca por nome fantasia ou razao social (ilike). 4. Paginacao: 50 por pagina (configuravel). 5. Ordenacao padrao: Score desc. 6. Ordenacao custom: click no header da coluna. 7. Cores de status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000. 8. Cores ABC: A=#00B050, B=#FFFF00, C=#FFC000. |

**FR-029 -- Detalhe do Cliente**

| Campo | Valor |
|-------|-------|
| Descricao | Modal/pagina com todos os dados de um cliente + historico de interacoes |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. Dados de identificacao: CNPJ, Nome Fantasia, Razao Social, UF, Cidade, Codigo SAP. 2. Status: Situacao, Temperatura, Score (com breakdown), Prioridade, Sinaleiro, Curva ABC, Tipo Cliente, Fase. 3. Historico de compras: dias sem compra, ultimo pedido (data + valor), ciclo medio, n compras, faturamento total. 4. Motor: estagio funil, acao futura, followup dias, grupo dash. 5. Projecao: meta anual, realizado, % alcancado, gap, status meta. 6. Classificacao 3-tier visivel. 7. Timeline de atendimentos (LOG) do cliente -- ultimos 20 ordenados por data desc. |

**FR-030 -- Exportacao CSV/Excel**

| Campo | Valor |
|-------|-------|
| Descricao | Exportar a carteira filtrada para CSV ou Excel |
| Prioridade MoSCoW | Should |
| Personas | P1, P4 |
| Acceptance Criteria | 1. Botao "Exportar" que gera arquivo com os filtros ativos. 2. Formato CSV (default) ou XLSX (opcao). 3. Inclui todas as colunas visiveis + ocultas relevantes. 4. CNPJ exportado como texto (nunca numero). 5. Limite de 10.000 registros por export. |

**FR-031 -- Edicao Inline de Consultor**

| Campo | Valor |
|-------|-------|
| Descricao | Permitir alterar o consultor responsavel diretamente na listagem |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Double-click na coluna Consultor abre dropdown (MANU, LARISSA, DAIANE, JULIO). 2. Alteracao salva imediatamente (PATCH /api/clientes/{cnpj}). 3. Historico de alteracao logado. 4. Somente Admin pode alterar. |

---

### E7 -- LOG Append-Only

**Descricao:** Sistema de registro de interacoes (atendimentos) com regime append-only. Cada contato do consultor com o cliente gera um registro imutavel. Two-Base Architecture enforced: LOG = SEMPRE R$ 0.00. O Motor de Regras e acionado automaticamente a cada registro.

**Referencia tecnica:** Abas LARISSA/MANU/JULIO/DAIANE na planilha (13.159 rows x 40 cols cada) + DRAFT 2 (4.403 registros)

#### Features

**FR-032 -- Registro de Atendimento**

| Campo | Valor |
|-------|-------|
| Descricao | Formulario para registrar interacao com cliente |
| Prioridade MoSCoW | Must |
| Personas | P2, P3, P4, P5 |
| Acceptance Criteria | 1. Campos obrigatorios: CNPJ (autocomplete da carteira), Resultado (dropdown 14 opcoes), Descricao (textarea). 2. Campos automaticos: Data (now), Consultor (usuario logado), Tentativa (calculada pelo motor). 3. Campos preenchidos pelo Motor (read-only apos salvar): Estagio Funil, Fase, Tipo Contato, Acao Futura, Temperatura, Follow-up Dias. 4. Two-Base enforced: nenhum campo de valor monetario no formulario. 5. Append-only: registro salvo nao pode ser editado ou deletado. 6. Timestamp com timezone BRT. |

**FR-033 -- Timeline de Atendimentos**

| Campo | Valor |
|-------|-------|
| Descricao | Visualizacao cronologica dos atendimentos de um cliente |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. Lista vertical cronologica (mais recente primeiro). 2. Cada item: data, resultado (badge colorido), descricao, consultor, acao futura gerada. 3. Filtro por periodo (data inicio/fim). 4. Filtro por resultado. 5. Paginacao (20 por pagina). 6. Indicador visual de tentativas (T1, T2, T3, T4+). |

**FR-034 -- Contadores Diarios**

| Campo | Valor |
|-------|-------|
| Descricao | Metricas diarias de atendimento por consultor |
| Prioridade MoSCoW | Should |
| Personas | P1, P4 |
| Acceptance Criteria | 1. Atendimentos hoje por consultor. 2. Breakdown por resultado (vendas, FUs, nao atende, etc). 3. % da agenda completada. 4. Comparativo com meta diaria (22 contatos/rep/dia). |

**FR-035 -- Validacao Two-Base no Backend**

| Campo | Valor |
|-------|-------|
| Descricao | Garantia que nenhum registro de LOG tem valor monetario associado |
| Prioridade MoSCoW | Must |
| Personas | Sistema |
| Acceptance Criteria | 1. Model `Atendimento` nao possui campo de valor monetario. 2. Se endpoint receber campo de valor, ignora silenciosamente. 3. Validacao na camada de servico que impede associacao de R$ a atendimento. 4. Test automatizado que tenta inserir valor e confirma rejeicao. 5. Vendas sao registradas em tabela separada (`vendas`) com CNPJ + data + valor. |

---

### E8 -- Autenticacao e Roles

**Descricao:** Sistema de login com 3 niveis de acesso (Admin, Gerente, Consultor / Consultor Externo) controlando visibilidade de dados e funcionalidades.

#### Features

**FR-036 -- Login com Email/Senha**

| Campo | Valor |
|-------|-------|
| Descricao | Autenticacao basica com email e senha |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. Tela de login (email + senha). 2. JWT token com expiracao de 24h. 3. Refresh token com expiracao de 7 dias. 4. Senha com hash bcrypt (nunca em texto). 5. Rate limit: 5 tentativas por minuto por IP. 6. Redirect para dashboard apos login. |

**FR-037 -- Roles e Permissoes**

| Campo | Valor |
|-------|-------|
| Descricao | 3 niveis de acesso com permissoes granulares |
| Prioridade MoSCoW | Must |
| Personas | Todos |
| Acceptance Criteria | 1. **Admin** (Leandro): acesso total -- configura regras, ve todos consultores, importa dados, gerencia usuarios, ve dados financeiros sensiveis. 2. **Gerente** (Daiane): ve todos consultores, nao configura sistema, nao importa dados. 3. **Consultor** (Manu, Larissa): ve apenas propria carteira e agenda. 4. **Consultor Externo** (Julio): ve propria carteira, sem dados financeiros sensiveis (faturamento, margem). 5. Middleware FastAPI que valida role em cada endpoint. 6. Frontend esconde elementos conforme role. |

**FR-038 -- Gerenciamento de Usuarios**

| Campo | Valor |
|-------|-------|
| Descricao | CRUD de usuarios do sistema |
| Prioridade MoSCoW | Must |
| Personas | P1 |
| Acceptance Criteria | 1. Criar usuario: nome, email, senha temporaria, role, consultor vinculado. 2. Editar: alterar role, reset senha, ativar/desativar. 3. Listar usuarios ativos. 4. Desativar (soft delete -- nao perde historico). 5. Somente Admin acessa. |

---

### E9 -- Integracao Deskrio (WhatsApp)

**Descricao:** Integracao bidirecional com a API Deskrio para enviar e receber mensagens WhatsApp. A API ja esta conectada e validada (15.468 contatos, 3 conexoes WhatsApp, 26 endpoints). Permite que consultores enviem mensagens direto do CRM e que tickets recebidos alimentem o LOG automaticamente.

**Referencia tecnica:** API Deskrio validada em 2026-03-23. Token JWT admin, companyId=38. Endpoint principal: GET /v1/api/contacts, GET /v1/api/tickets, POST /v1/api/messages/send. Kanban "Vendas Vitao" ja ativo.

#### Features

**FR-039 -- Envio de Mensagem WhatsApp**

| Campo | Valor |
|-------|-------|
| Descricao | Botao "Enviar WhatsApp" no detalhe do cliente / agenda |
| Prioridade MoSCoW | Should |
| Personas | P2, P3, P4 |
| Acceptance Criteria | 1. Botao acessivel no detalhe do cliente e na agenda. 2. Abre composer com templates pre-definidos (boas-vindas, follow-up, pos-venda, reativacao). 3. Envia via POST /v1/api/messages/send. 4. Registra envio no LOG automaticamente com resultado "FOLLOW UP 7" ou "FOLLOW UP 15" conforme template. 5. Status de entrega retornado da API exibido (enviado/entregue/lido). |

**FR-040 -- Recepcao de Tickets**

| Campo | Valor |
|-------|-------|
| Descricao | Webhook/polling que recebe tickets novos do Deskrio e cria atendimentos no LOG |
| Prioridade MoSCoW | Should |
| Personas | Sistema |
| Acceptance Criteria | 1. Polling a cada 5 minutos: GET /v1/api/tickets?startDate&endDate. 2. Match ticket -> cliente via telefone/CNPJ. 3. Ticket aberto cria atendimento no LOG com resultado inferido. 4. Classificacao automatica por IA (Claude API) do resultado baseado no conteudo da mensagem. 5. Tickets sem match logados para revisao manual. 6. Duplicatas detectadas e ignoradas. |

**FR-041 -- Sincronizacao de Contatos**

| Campo | Valor |
|-------|-------|
| Descricao | Sincronizar contatos entre CRM e Deskrio via campo CNPJ |
| Prioridade MoSCoW | Could |
| Personas | P1 |
| Acceptance Criteria | 1. GET /v1/api/contacts retorna 15.468 contatos. 2. Match por campo extra CNPJ. 3. Contatos do CRM sem match no Deskrio sao flaggados. 4. Novos clientes no CRM podem ser criados no Deskrio. 5. Relatorio de sincronizacao com matched/unmatched/errors. |

**FR-042 -- Templates de Mensagem**

| Campo | Valor |
|-------|-------|
| Descricao | CRUD de templates de mensagem WhatsApp por fase do funil |
| Prioridade MoSCoW | Could |
| Personas | P1 |
| Acceptance Criteria | 1. Templates por fase: PROSPECCAO, POS-VENDA (D+4), CS (D+30), FOLLOW-UP, REATIVACAO. 2. Variaveis dinamicas: {nome_fantasia}, {consultor}, {dias_sem_compra}, {ultimo_pedido}. 3. CRUD admin para criar/editar templates. 4. Historico de uso por template (quantas vezes enviado, taxa de resposta). |

---

### E10 -- Deploy (Vercel + Railway)

**Descricao:** Infraestrutura de deploy com frontend no Vercel e backend no Railway (ou Fly.io), banco PostgreSQL em producao, CI/CD automatizado.

#### Features

**FR-043 -- Deploy Frontend (Vercel)**

| Campo | Valor |
|-------|-------|
| Descricao | Deploy do Next.js no Vercel com CI/CD do GitHub |
| Prioridade MoSCoW | Must |
| Personas | P1 (devops) |
| Acceptance Criteria | 1. Push na branch main dispara deploy automatico. 2. Preview deploys em branches de feature. 3. Variavel NEXT_PUBLIC_API_URL configurada para backend de producao. 4. HTTPS habilitado com dominio custom (vitao360.vercel.app ou custom). 5. Build < 3 minutos. |

**FR-044 -- Deploy Backend (Railway)**

| Campo | Valor |
|-------|-------|
| Descricao | Deploy do FastAPI no Railway com PostgreSQL |
| Prioridade MoSCoW | Must |
| Personas | P1 (devops) |
| Acceptance Criteria | 1. Dockerfile configurado para FastAPI + uvicorn. 2. PostgreSQL provisionado no Railway. 3. Migration automatica (Alembic) no startup. 4. Variaveis de ambiente: DATABASE_URL, JWT_SECRET, CORS_ORIGINS, DESKRIO_TOKEN. 5. Health check configurado (/health). 6. Auto-restart em caso de crash. |

**FR-045 -- Migracao SQLite para PostgreSQL**

| Campo | Valor |
|-------|-------|
| Descricao | Trocar banco de desenvolvimento (SQLite) para producao (PostgreSQL) |
| Prioridade MoSCoW | Must |
| Personas | P1 (devops) |
| Acceptance Criteria | 1. DATABASE_URL via variavel de ambiente (ja implementado em database.py). 2. Alembic configurado para migrations versionadas. 3. Indices criados: cnpj, consultor, situacao, temperatura, prioridade, sinaleiro, curva_abc. 4. CNPJ como String(14) no PostgreSQL (nunca numeric). 5. Script de seed para popular dados iniciais em producao. |

**FR-046 -- Backup Automatico**

| Campo | Valor |
|-------|-------|
| Descricao | Backup diario do banco PostgreSQL |
| Prioridade MoSCoW | Should |
| Personas | P1 (devops) |
| Acceptance Criteria | 1. pg_dump diario as 02:00 BRT. 2. Retencao de 30 dias. 3. Armazenamento em bucket S3 ou equivalente. 4. Teste de restore mensal documentado. 5. Alerta se backup falhar. |

---

### E11 -- Integracao Mercos (ERP Vendas)

**Descricao:** Importacao automatizada de dados de vendas do Mercos, substituindo o processo manual de exportar xlsx e importar no pipeline. Inclui pedidos, carteira, classificacao ABC e dados de B2B.

#### Features

**FR-047 -- Import de Pedidos Mercos**

| Campo | Valor |
|-------|-------|
| Descricao | Sincronizacao diaria de pedidos do Mercos via API ou import automatizado de xlsx |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Frequencia: diaria (automatica) ou sob demanda. 2. Campos: CNPJ, data pedido, valor, itens, vendedor, status. 3. Normalizacao CNPJ aplicada. 4. De-para de vendedores aplicado. 5. Registros tipo VENDA com valor R$ (Two-Base respeitada). 6. CUIDADO: nomes de relatorios Mercos MENTEM nas datas -- SEMPRE verificar Data Inicial/Data Final. 7. Duplicatas detectadas por (CNPJ + data + valor). |

**FR-048 -- Import de Carteira Mercos**

| Campo | Valor |
|-------|-------|
| Descricao | Sincronizacao de dados de carteira (clientes ativos, novos, inativos) |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Atualiza dias_sem_compra, ultimo pedido, ciclo medio. 2. Detecta novos clientes (CNPJ nao existente no banco). 3. Atualiza situacao baseado em dias sem compra. 4. Relatorio de mudancas: novos, reativados, inativados. |

**FR-049 -- Curva ABC do Mercos**

| Campo | Valor |
|-------|-------|
| Descricao | Importar/recalcular classificacao ABC baseada em faturamento |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. A = top 20% clientes (80% faturamento). 2. B = proximos 30%. 3. C = ultimos 50%. 4. Recalculado mensalmente. 5. Historico de mudanca de curva registrado. |

---

### E12 -- Integracao SAP (Cadastro/Metas)

**Descricao:** Importacao de dados do SAP corporativo: cadastro de clientes, metas de vendas, status de atendimento. Inicialmente via import de xlsx (Fase 2 do roadmap), depois API direta.

#### Features

**FR-050 -- Import de Cadastro SAP**

| Campo | Valor |
|-------|-------|
| Descricao | Importar dados de cadastro do SAP (codigo cliente, tipo, macroregiao, canal, grupo) |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Campos: codigo_cliente_sap, cnpj_sap, razao_social_sap, status_cadastro, status_atendimento, bloqueio, grupo_cliente, gerente_nacional, representante, vendedor_interno, canal, tipo_cliente_sap, macroregiao, microregiao, grupo_chave. 2. Match por CNPJ normalizado. 3. Atualiza campos SAP do model Cliente. 4. Clientes bloqueados no SAP flaggados no CRM. |

**FR-051 -- Import de Metas SAP**

| Campo | Valor |
|-------|-------|
| Descricao | Importar metas de vendas anuais/mensais do SAP por cliente |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Campos: cnpj, meta_anual, meta_mensal (12 meses), meta_igualitaria. 2. Atualiza meta_anual no model Cliente. 3. Calcula gap_valor = meta_anual - realizado_acumulado. 4. Calcula status_meta: ACIMA (>= 100%), ALERTA (70-99%), CRITICO (< 70%). |

---

### E13 -- Projecao e Metas

**Descricao:** Tela de projecao financeira: realizado vs meta por cliente, por consultor, e consolidado. Substitui as abas PROJECAO (662 x 80, 3.954 formulas XLOOKUP) e RESUMO META.

#### Features

**FR-052 -- Projecao Consolidada**

| Campo | Valor |
|-------|-------|
| Descricao | Visao consolidada: faturamento realizado vs meta por periodo |
| Prioridade MoSCoW | Should |
| Personas | P1 |
| Acceptance Criteria | 1. Faturamento realizado total (baseline R$ 2.091.000 como referencia). 2. Projecao 2026: R$ 3.377.120. 3. Meta Q1: proporcional (R$ 844.280). 4. % alcancado. 5. Gap em R$. 6. Grafico de barras mensal: realizado vs meta. 7. Apenas dados REAL + SINTETICO (ALUCINACAO excluida). |

**FR-053 -- Projecao por Consultor**

| Campo | Valor |
|-------|-------|
| Descricao | Breakdown de projecao por cada consultor |
| Prioridade MoSCoW | Should |
| Personas | P1, P4 |
| Acceptance Criteria | 1. Para cada consultor: faturamento, meta, % alcancado. 2. Ranking por performance. 3. Identificar consultores abaixo da meta. 4. Se meta individual nao disponivel, distribuir proporcional ao baseline. |

**FR-054 -- Projecao por Cliente**

| Campo | Valor |
|-------|-------|
| Descricao | Detalhe de projecao individual de cada cliente |
| Prioridade MoSCoW | Could |
| Personas | P1 |
| Acceptance Criteria | 1. Meta anual do cliente (SAP). 2. Realizado acumulado. 3. % alcancado por mes. 4. Historico mensal (barras empilhadas). 5. Status meta (ACIMA/ALERTA/CRITICO). |

---

### E14 -- RNC (Registro Nao-Conformidade)

**Descricao:** Registro e tracking de problemas reportados por clientes (entrega, qualidade, NF). Substitui a aba RNC (2.476 rows x 15 cols).

#### Features

**FR-055 -- CRUD de RNC**

| Campo | Valor |
|-------|-------|
| Descricao | Criar, visualizar e resolver registros de nao-conformidade |
| Prioridade MoSCoW | Could |
| Personas | P1, P2, P3, P4 |
| Acceptance Criteria | 1. Campos: CNPJ (vincula ao cliente), tipo problema (8 categorias: entrega, qualidade, NF, prazo, produto errado, falta, avaria, outro), descricao, status (ABERTO, EM_ANDAMENTO, RESOLVIDO, ENCERRADO), prazo resolucao, responsavel. 2. Status flow: ABERTO -> EM_ANDAMENTO -> RESOLVIDO -> ENCERRADO. 3. RNC aberta seta `problema_aberto = True` no cliente (alimenta P0). 4. Listagem com filtros por status, tipo, consultor. 5. Metricas: RNCs abertas, tempo medio resolucao, por tipo. |

**FR-056 -- Alerta de RNC no Motor**

| Campo | Valor |
|-------|-------|
| Descricao | RNC aberta eleva cliente automaticamente a P0 (IMEDIATA) |
| Prioridade MoSCoW | Could |
| Personas | Sistema |
| Acceptance Criteria | 1. Cliente com problema_aberto = True recebe P0 automaticamente. 2. P0 pula fila na agenda (aparece no topo). 3. Ao resolver RNC, cliente volta a prioridade calculada pelo Score. 4. Historico de escalacao P0 registrado. |

---

## 5. REQUISITOS NAO-FUNCIONAIS

### NFR-001 -- Performance

| Aspecto | Requisito |
|---------|-----------|
| Tempo de resposta API | < 200ms para endpoints de listagem, < 50ms para lookups |
| Tempo de carregamento pagina | < 2 segundos (First Contentful Paint) |
| Capacidade | Suportar 10.000 clientes sem degradacao |
| Agenda geracao | < 30 segundos para gerar agenda de todos os consultores |
| Import pipeline | < 5 minutos para processar arquivo de 5.000 registros |
| Concurrent users | 10 simultaneos sem degradacao |

### NFR-002 -- Seguranca

| Aspecto | Requisito |
|---------|-----------|
| Autenticacao | JWT + refresh token, bcrypt para senhas |
| Autorizacao | RBAC com 4 roles (admin, gerente, consultor, consultor_externo) |
| CORS | Whitelist de origens permitidas |
| Rate limiting | 100 requests/minuto por usuario, 5 login attempts/minuto |
| Dados sensiveis | CNPJ e dados financeiros nunca em logs de producao |
| Backup | Diario com retencao de 30 dias |
| HTTPS | Obrigatorio em producao |

### NFR-003 -- Usabilidade

| Aspecto | Requisito |
|---------|-----------|
| Tema | Visual LIGHT exclusivamente. Nunca dark mode. |
| Fonte | Arial ou Inter (fallback sans-serif), 9pt dados, 10pt headers |
| Cores status | ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000 |
| Cores ABC | A=#00B050, B=#FFFF00, C=#FFC000 |
| Responsivo | Desktop-first, funcional em tablet e mobile |
| Treinamento | Interface intuitiva -- consultor produtivo em < 2 horas |
| Idioma | 100% Portugues Brasileiro |
| Navegacao | Sidebar com rotas principais: Dashboard, Carteira, Agenda, Projecao |

### NFR-004 -- Confiabilidade de Dados

| Aspecto | Requisito |
|---------|-----------|
| Two-Base Architecture | VENDA = R$ real; LOG = R$ 0.00. Enforced no model e API. |
| CNPJ | String(14), zero-padded, unique. Nunca float/int. |
| Classificacao 3-tier | REAL/SINTETICO/ALUCINACAO em todo registro. |
| Faturamento baseline | R$ 2.091.000 (tolerancia +/- 0.5%). |
| Zero fabricacao | Nenhum dado inventado. 558 ALUCINACAO catalogados nunca integrados. |
| Validacao import | 0 registros ALUCINACAO integrados, 0 CNPJs duplicados, 0 CNPJs float. |

### NFR-005 -- Disponibilidade

| Aspecto | Requisito |
|---------|-----------|
| Uptime | 99% (permite ~7h downtime/mes, aceitavel para escala atual) |
| Horario critico | 08:00-18:00 BRT (jornada comercial) |
| Recovery | RTO < 4 horas, RPO < 24 horas |
| Monitoramento | Health check endpoint + alertas em caso de falha |

### NFR-006 -- Escalabilidade

| Aspecto | Requisito |
|---------|-----------|
| Clientes | Suportar ate 10.000 (20x atual) |
| Consultores | Suportar ate 20 (5x atual) |
| Atendimentos/dia | Suportar 1.000/dia (5 consultores x 50 x margem) |
| Historico | Reter 5+ anos de dados sem degradacao |

### NFR-007 -- Observabilidade

| Aspecto | Requisito |
|---------|-----------|
| Logs | Structured logging (JSON) com request_id |
| Erros | Sentry ou equivalente para tracking de erros em producao |
| Metricas | Latencia, throughput, error rate por endpoint |
| Auditoria | Log de todas as alteracoes de dados com usuario, timestamp, campo alterado |

---

## 6. PRIORIZACAO MoSCoW

### Must Have (MVP -- Lancamento)

| Feature | Epico | Justificativa |
|---------|-------|---------------|
| FR-001 Upload xlsx | E1 | Sem import, sem dados |
| FR-002 Normalizacao CNPJ | E1 | Integridade de dados fundamental |
| FR-003 Classificacao 3-tier | E1 | Prevenir ALUCINACAO (742%) |
| FR-004 Merge fontes | E1 | Dados de multiplas fontes |
| FR-007 Tabela de regras | E2 | Motor e o cerebro do CRM |
| FR-008 API lookup motor | E2 | Motor acessivel via API |
| FR-009 Motor automatico no LOG | E2 | Core: registro -> motor -> acao |
| FR-010 SITUACAO automatica | E2 | Classificacao automatica |
| FR-012 Score ponderado | E3 | Priorizacao e o diferencial |
| FR-013 Prioridade P0-P7 | E3 | Define a agenda |
| FR-014 Sinaleiro | E3 | Saude do cliente |
| FR-015 Desempate | E3 | Agenda justa |
| FR-018 Geracao agenda diaria | E4 | Feature principal do consultor |
| FR-019 Tela agenda | E4 | Interface do consultor |
| FR-020 Marcar atendimento | E4 | Registrar trabalho |
| FR-023 KPIs executivos | E5 | Visibilidade para gestor |
| FR-024 Distribuicoes | E5 | Entender a carteira |
| FR-025 Top 10 | E5 | Foco nos maiores |
| FR-028 Listagem clientes | E6 | Carteira digital |
| FR-029 Detalhe cliente | E6 | Informacao completa |
| FR-032 Registro atendimento | E7 | LOG e obrigatorio |
| FR-033 Timeline atendimentos | E7 | Historico do cliente |
| FR-035 Two-Base enforced | E7 | Prevenir inflacao 742% |
| FR-036 Login | E8 | Seguranca basica |
| FR-037 Roles | E8 | Controle de acesso |
| FR-038 Gerenciar usuarios | E8 | Criar contas dos consultores |
| FR-043 Deploy frontend | E10 | Acessivel na web |
| FR-044 Deploy backend | E10 | API no ar |
| FR-045 PostgreSQL | E10 | Banco de producao |

**Total Must: 29 features**

### Should Have (v1.1 -- Pos-lancamento imediato)

| Feature | Epico | Justificativa |
|---------|-------|---------------|
| FR-005 Relatorio import | E1 | Auditoria de dados |
| FR-006 Background processing | E1 | UX para imports grandes |
| FR-016 API de Score | E3 | Transparencia do calculo |
| FR-021 Agenda historica | E4 | Acompanhar completude |
| FR-022 Redistribuicao carteira | E4 | Cenario licenca Manu |
| FR-026 Visao por consultor | E5 | Gestao de equipe |
| FR-030 Exportacao CSV | E6 | Compatibilidade Excel |
| FR-031 Edicao inline consultor | E6 | Gestao agil de carteira |
| FR-034 Contadores diarios | E7 | Acompanhar produtividade |
| FR-039 Envio WhatsApp | E9 | Acao direta do CRM |
| FR-040 Recepcao tickets | E9 | LOG automatico |
| FR-046 Backup automatico | E10 | Seguranca de dados |
| FR-047 Import pedidos Mercos | E11 | Dados atualizados |
| FR-048 Import carteira Mercos | E11 | Carteira sincronizada |
| FR-049 Curva ABC Mercos | E11 | Classificacao automatica |
| FR-050 Import cadastro SAP | E12 | Dados SAP integrados |
| FR-051 Import metas SAP | E12 | Metas reais |
| FR-052 Projecao consolidada | E13 | Visao de meta |
| FR-053 Projecao por consultor | E13 | Performance individual |

**Total Should: 19 features**

### Could Have (v2 -- Evolucoes)

| Feature | Epico | Justificativa |
|---------|-------|---------------|
| FR-011 Painel admin regras | E2 | Gestao visual |
| FR-017 Meta Balance | E3 | Otimizacao avancada |
| FR-027 Tendencias temporais | E5 | Analytics avancado |
| FR-041 Sync contatos Deskrio | E9 | Base unificada |
| FR-042 Templates WhatsApp | E9 | Automacao comunicacao |
| FR-054 Projecao por cliente | E13 | Detalhe individual |
| FR-055 CRUD RNC | E14 | Qualidade |
| FR-056 Alerta RNC no Motor | E14 | Automacao P0 |

**Total Could: 8 features**

### Won't Have (Fora de Escopo 2026)

| Item | Motivo |
|------|--------|
| App mobile nativo (iOS/Android) | PWA responsivo suficiente para 2026 |
| IA preditiva de churn (ML supervisionado) | Depende de volume de dados historicos |
| Multi-tenant (outras distribuidoras) | Produto custom para VITAO |
| Integracao ERP generico | SAP e Mercos especificos |
| Programa de fidelidade com pontos | Complexidade desnecessaria |
| A/B testing de campanhas | Prematura para o volume atual |
| BI avanacado com cubos OLAP | Dashboards simples atendem |
| Asana full integration | Fase 3+ do roadmap |

---

## 7. DEPENDENCIAS ENTRE EPICOS

### Grafo de Dependencias

```
E8 (Auth) ──────────────────────────────────────┐
  |                                               |
  v                                               |
E1 (Import Pipeline) -----> E2 (Motor Regras) ---+---> E10 (Deploy)
  |                           |                   |
  |                           v                   |
  |                         E3 (Score + Sinaleiro) |
  |                           |                   |
  |                           v                   |
  +----------------------> E4 (Agenda) <----------+
  |                           |
  |                           v
  +----------------------> E7 (LOG)
  |                           |
  |                           v
  +----------------------> E5 (Dashboard)
  |                           |
  v                           v
E6 (Carteira) <-----------+
  |
  v
E11 (Mercos) ---+
E12 (SAP) ------+---> E13 (Projecao)
  |
  v
E9 (Deskrio/WhatsApp)
  |
  v
E14 (RNC)
```

### Tabela de Dependencias

| Epico | Depende De | Motivo |
|-------|-----------|--------|
| E1 (Import) | E8 (Auth) parcial | Upload protegido por role Admin |
| E2 (Motor) | E1 (Import) | Motor precisa de dados importados para operar |
| E3 (Score) | E2 (Motor) | Score usa Fase e Temperatura que vem do Motor |
| E4 (Agenda) | E3 (Score) | Agenda ordena por Score |
| E4 (Agenda) | E2 (Motor) | Agenda exibe acao sugerida do Motor |
| E5 (Dashboard) | E3 (Score) | KPIs usam Score, Sinaleiro |
| E5 (Dashboard) | E1 (Import) | Dashboard precisa de dados |
| E6 (Carteira) | E1 (Import) | Carteira exibe dados importados |
| E6 (Carteira) | E3 (Score) | Carteira exibe Score e Sinaleiro |
| E7 (LOG) | E2 (Motor) | LOG aciona Motor ao registrar |
| E7 (LOG) | E8 (Auth) | LOG identifica consultor logado |
| E8 (Auth) | Nenhum | Independente -- pode comecar primeiro |
| E9 (Deskrio) | E7 (LOG) | WhatsApp gera registros no LOG |
| E9 (Deskrio) | E6 (Carteira) | Precisa de clientes para enviar |
| E10 (Deploy) | E8 (Auth) | Precisa de auth em producao |
| E10 (Deploy) | Todos MVP | Deploy vai ao ar com todas as features Must |
| E11 (Mercos) | E1 (Import) | Usa pipeline de import |
| E12 (SAP) | E1 (Import) | Usa pipeline de import |
| E13 (Projecao) | E11, E12 | Precisa de dados de faturamento e metas |
| E14 (RNC) | E6 (Carteira) | RNC vinculada a cliente |

### Ordem de Implementacao Sugerida

**Sprint 1-2:** E8 (Auth basico) + E1 (Import Pipeline)
**Sprint 3-4:** E2 (Motor de Regras) + Model Atendimento (base para E7)
**Sprint 5-6:** E3 (Score + Sinaleiro) + E7 (LOG com Motor automatico)
**Sprint 7-8:** E4 (Agenda) + E6 (Carteira)
**Sprint 9-10:** E5 (Dashboard) + E10 (Deploy)
**Sprint 11-14:** E9 (Deskrio) + E11 (Mercos) + E12 (SAP) + E13 (Projecao) + E14 (RNC)

---

## 8. MVP vs FULL

### MVP (Minimum Viable Product) -- Lancamento

**Objetivo:** CRM funcional que substitui a planilha para o dia-a-dia dos consultores.

**Prazo estimado:** 10 sprints (20 semanas, ~5 meses)

**O que ENTRA no MVP:**

| Funcionalidade | Descricao |
|----------------|-----------|
| Login com roles | Admin, Gerente, Consultor, Consultor Externo |
| Import xlsx | Upload de arquivo Mercos/SAP com normalizacao CNPJ e classificacao 3-tier |
| Motor de Regras | 92 combinacoes no banco, lookup automatico ao registrar LOG |
| Score + Sinaleiro | Calculo em tempo real, prioridade P0-P7 |
| Agenda diaria | 40-60 itens por consultor, ordenados por Score, com acao sugerida |
| Registro de atendimento | Motor roda automaticamente, Two-Base enforced |
| Carteira | Listagem com filtros, detalhe do cliente, timeline |
| Dashboard | KPIs executivos, distribuicoes, Top 10 |
| Deploy | Frontend Vercel, Backend Railway, PostgreSQL |

**O que NAO ENTRA no MVP:**

| Funcionalidade | Razao | Versao |
|----------------|-------|--------|
| Integracao WhatsApp (Deskrio) | Complexidade + depende de API estavel | v1.1 |
| Import automatico Mercos/SAP | Import manual via xlsx suficiente para MVP | v1.1 |
| Projecao e metas | Dashboard basico atende inicialmente | v1.1 |
| RNC | Processo manual funciona | v2 |
| Templates WhatsApp | Depende de integracao Deskrio | v2 |
| IA preditiva | Precisa de volume de dados | v2+ |
| Mobile nativo | PWA responsivo suficiente | Won't |

### Full Product (v2) -- 6 meses apos MVP

**Objetivo:** CRM inteligente com integracoes reais e automacao.

**Adiciona ao MVP:**
1. Integracao Deskrio bidirecional (WhatsApp envio + recepcao)
2. Import automatico Mercos (pedidos, carteira, ABC)
3. Import automatico SAP (cadastro, metas)
4. Projecao financeira completa (consolidada + por consultor + por cliente)
5. RNC com escalacao automatica P0
6. Exportacao CSV/Excel
7. Redistribuicao de carteira
8. Tendencias temporais no dashboard
9. Templates WhatsApp por fase do funil
10. Backup automatico
11. Contadores diarios de produtividade

### Roadmap Visual

```
Q2 2026 (Abr-Jun)        Q3 2026 (Jul-Set)        Q4 2026 (Out-Dez)
+--------------------+   +--------------------+   +--------------------+
|  MVP (Must Have)   |   | v1.1 (Should Have) |   | v2 (Could Have)    |
|                    |   |                    |   |                    |
| - Auth + Roles     |   | - Mercos API       |   | - Admin regras     |
| - Import Pipeline  |   | - SAP Import       |   | - Meta Balance     |
| - Motor Regras     |   | - Deskrio/WhatsApp |   | - Tendencias       |
| - Score/Sinaleiro  |   | - Projecao/Metas   |   | - RNC completo     |
| - Agenda Intel.    |   | - Export CSV       |   | - Templates WA     |
| - LOG Append-Only  |   | - Agenda historica |   | - Sync contatos    |
| - Carteira         |   | - Redist. carteira |   | - Projecao cliente |
| - Dashboard CEO    |   | - Visao consultor  |   |                    |
| - Deploy Prod      |   | - Backup auto      |   |                    |
|                    |   | - Contadores dia   |   |                    |
+--------------------+   +--------------------+   +--------------------+
    29 features              19 features              8 features
```

---

## 9. MODELO FINANCEIRO

### 9.1 Baseline e Projecao

| Metrica | Valor | Fonte |
|---------|-------|-------|
| Faturamento 2025 (baseline) | R$ 2.091.000 | Painel CEO auditado (68 arquivos) |
| Faturamento 2026 (projecao) | R$ 3.377.120 (+69%) | Motor mes a mes completo |
| Q1 2026 real | R$ 459.465 | SAP Vendas Jan-Mar 2026 |
| Clientes na carteira | 489 | Carteira operacional |
| Clientes ativos | 105 | Status ATIVO |
| Inativos recentes | 80 | INAT.REC |
| Inativos antigos | 304 | INAT.ANT |
| Redes/franquias | 8 redes, 923 lojas | Sinaleiro |
| Penetracao redes | < 30% | Baixa -- oportunidade |

### 9.2 Custo de Equipe 2026 (Ramp-up F1-F4)

| Fase | Periodo | Equipe | Custo/mes |
|------|---------|--------|-----------|
| F1 (Q1) | P1-P3 | 2 Reps + Daiane | R$ 22K |
| F2 (Q2) | P4-P6 | 3 Reps + Daiane (Nova Rep) | R$ 29K |
| F3 (Q3) | P7-P9 | 3 Reps + Daiane + Pos-Venda | R$ 34K |
| F4 (Q4) | P10-P12 | 4 Reps + Daiane + PV | R$ 40K |
| **Total 2026** | | | **R$ 375.000** |

### 9.3 ROI Esperado

| Metrica | Valor |
|---------|-------|
| Faturamento projetado 2026 | R$ 3.377.120 |
| Custo equipe 2026 | R$ 375.000 |
| Sobra projetada | R$ 3.002.120 |
| ROI | 8.0x |
| CAC medio | R$ 426/cliente |
| Payback | Mes 1 |
| Meta ativos P12 | 684 |
| Churn meta (com pos-venda Q3) | 50% (vs 80% atual) |

### 9.4 Custo de Desenvolvimento SaaS

| Item | Estimativa | Observacao |
|------|-----------|-----------|
| Desenvolvimento (solo dev) | R$ 0 (interno) | Leandro + Claude Code |
| Infraestrutura (Vercel) | R$ 0 (free tier) | Suficiente para 5 usuarios |
| Infraestrutura (Railway) | ~R$ 25/mes | Starter plan com PostgreSQL |
| Dominio | ~R$ 50/ano | Custom domain |
| Deskrio API | Ja contratado | Custo existente |
| **Total anual infra** | **~R$ 350/ano** | Insignificante vs ROI |

---

## 10. RISCOS E MITIGACOES

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|---------------|---------|-----------|
| R1 | Manu nao retorna de licenca -- carteira orfa | Media | Alto | FR-022 (redistribuicao), Nova Rep Q2 ja planejada |
| R2 | Pos-venda nao implementada Q3 -- churn fica 80% | Media | Critico | Priorizar contratacao, CRM ja tera pipeline pra CS |
| R3 | Dados Mercos com datas incorretas nos relatorios | Alta | Medio | SEMPRE validar Data Inicial/Final (R6). Import com warnings. |
| R4 | CNPJ armazenado como float em alguma camada | Baixa | Critico | Enforced no model (String 14), validacao no import, tests automaticos |
| R5 | Two-Base violada por bug no backend | Baixa | Critico | Model sem campo de valor no LOG, validacao na API, tests |
| R6 | ALUCINACAO integrada acidentalmente | Baixa | Alto | Classificacao 3-tier obrigatoria, 558 bloqueados, gate no import |
| R7 | Faturamento diverge > 0.5% do baseline | Media | Alto | Validacao pos-import automatica, alerta imediato |
| R8 | Solo developer (bus factor = 1) | Alta | Critico | Documentacao extensa, Claude Code como backup, codigo limpo |
| R9 | API Deskrio instavel ou token expira | Media | Medio | Token expira ~Set/2026, monitorar, renovar proativamente |
| R10 | Consultores resistem a adotar novo sistema | Media | Alto | Interface simples, treinamento < 2h, agenda automatica como gancho |
| R11 | Railway/Vercel mudam pricing | Baixa | Baixo | Alternativas: Fly.io, Render, self-hosted |
| R12 | Volume de dados cresce muito (5+ anos) | Baixa | Medio | PostgreSQL escala bem, particionamento por ano se necessario |

---

## 11. METRICAS DE SUCESSO

### 11.1 Metricas de Produto (Adocao)

| KPI | Baseline | Meta 3 meses | Meta 6 meses | Meta 12 meses |
|-----|----------|-------------|-------------|--------------|
| % consultores usando diariamente | 0% (Excel) | 75% (3 de 4) | 100% (4 de 4) | 100% |
| Atendimentos registrados/dia (total) | ~0 (nao registram) | 40 | 100 | 150+ |
| Agenda completude media | N/A | 50% | 70% | 80% |
| Tempo medio para registrar atendimento | N/A | < 2 minutos | < 1 minuto | < 45 segundos |
| Login diario Leandro (dashboard) | 0 | 5x/semana | Diario | Diario |

### 11.2 Metricas de Negocio (Impacto)

| KPI | Baseline | Meta 3M | Meta 6M | Meta 12M |
|-----|----------|---------|---------|----------|
| Faturamento mensal | R$ 174K | R$ 200K | R$ 250K | R$ 300K+ |
| Clientes ativos | 105 | 150 | 300 | 500+ |
| Taxa recompra mensal | 21.9% | 30% | 40% | 50% |
| Churn mensal | 80% | 70% | 55% | 50% |
| Follow-ups vencidos | N/A | < 20% | < 10% | < 5% |
| Penetracao redes | < 30% | 35% | 45% | 60% |

### 11.3 Metricas Tecnicas (Saude)

| KPI | Requisito |
|-----|-----------|
| Uptime | > 99% horario comercial |
| Tempo resposta API (p95) | < 200ms |
| Erros em producao/semana | < 5 |
| Dados ALUCINACAO integrados | 0 (sempre) |
| Two-Base violacoes | 0 (sempre) |
| CNPJs como float | 0 (sempre) |
| Faturamento vs baseline | +/- 0.5% |
| Cobertura de testes | > 80% |

---

## 12. GLOSSARIO

| Termo | Definicao |
|-------|-----------|
| **Two-Base Architecture** | Separacao inviolavel: VENDA (com valor R$) vs LOG (sempre R$ 0.00). Misturar causa inflacao de 742%. |
| **Motor de Regras** | Cerebro do CRM: 92 combinacoes de SITUACAO x RESULTADO que geram 9 dimensoes automaticamente. |
| **Score Ponderado** | Calculo 0-100 com 6 dimensoes (FASE 25%, SINALEIRO 20%, ABC 20%, TEMPERATURA 15%, TIPO CLIENTE 10%, TENTATIVAS 10%). |
| **Sinaleiro** | Indicador de saude: ratio dias_sem_compra / ciclo_medio. Cores: VERDE, AMARELO, LARANJA, VERMELHO, ROXO. |
| **P0-P7** | 8 niveis de prioridade gerados pelo Score. P0=imediata (suporte), P7=nutricao (campanha). |
| **SITUACAO** | Status do cliente baseado em dias sem compra: ATIVO (<=50d), EM RISCO (51-60d), INAT.REC (61-90d), INAT.ANT (>90d), PROSPECT, LEAD, NOVO. |
| **FASE** | Estrategia comercial: RECOMPRA, NEGOCIACAO, SALVAMENTO, RECUPERACAO, PROSPECCAO, NUTRICAO. |
| **TEMPERATURA** | Engajamento do cliente: QUENTE, MORNO, FRIO, CRITICO, PERDIDO. |
| **CURVA ABC** | Classificacao por faturamento: A (top 20%), B (proximos 30%), C (ultimos 50%). |
| **TIPO CLIENTE** | Maturidade: PROSPECT, LEAD, NOVO, EM DESENVOLVIMENTO, RECORRENTE, FIDELIZADO, MADURO. |
| **TENTATIVAS** | Sequencia de contato: T1, T2, T3, T4, NUTRICAO, RESET. |
| **ESTAGIO FUNIL** | 14 posicoes no pipeline: INICIO CONTATO, TENTATIVA, PROSPECCAO, EM ATENDIMENTO, CADASTRO, ORCAMENTO, PEDIDO, ACOMP POS-VENDA, POS-VENDA, CS, FOLLOW-UP, SUPORTE, RELACIONAMENTO, NUTRICAO. |
| **Classificacao 3-Tier** | REAL (rastreavel a Mercos/SAP/Deskrio), SINTETICO (derivado por formula), ALUCINACAO (fabricado -- NUNCA integrar). |
| **CNPJ Normalizado** | 14 digitos, string, zero-padded, sem pontuacao. Regex: `re.sub(r'\D', '', str(val)).zfill(14)`. |
| **Baseline** | Faturamento referencia 2025: R$ 2.091.000 (corrigido por auditoria forense de 68 arquivos). |
| **CAC** | Customer Acquisition Cost: R$ 426/cliente. |
| **LTV** | Lifetime Value: valor total gerado pelo cliente ao longo do relacionamento. |
| **Churn** | Taxa de clientes que deixam de comprar. Atual: 80% mensal. Meta: 50% com pos-venda. |
| **Mercos** | ERP de vendas. CUIDADO: nomes de relatorios mentem sobre periodos de datas. |
| **SAP** | ERP corporativo: cadastro, metas, faturamento. |
| **Deskrio** | CRM WhatsApp Business: 15.468 contatos, 3 conexoes WA, 26 endpoints API. |
| **De-Para Vendedores** | Mapeamento de nomes para consultores padrao: Manu/Manu Vitao/Manu Ditzel -> MANU, etc. |
| **ALUCINACAO** | Dados fabricados (558 registros do ChatGPT catalogados). NUNCA integrar ao sistema. |
| **F1-F4** | Fases de ramp-up de equipe em 2026 (F1=Q1 R$22K/mes ate F4=Q4 R$40K/mes). |
| **Pipeline Import** | 8 stages: load -> normalize_cnpj -> classify -> merge -> motor_regras -> score -> sinaleiro -> agenda. |

---

## DECISAO E PROXIMO PASSO

### Aprovacao

Este PRD cobre 14 epicos, 56 features com acceptance criteria, priorizacao MoSCoW, grafo de dependencias e separacao clara entre MVP (29 features Must) e versao completa.

### Proximo Passo Imediato

1. **Leandro valida** as prioridades MoSCoW e a definicao de MVP
2. **Sprint 1 inicia** com E8 (Auth) + E1 (Import Pipeline)
3. **Sprint planning** detalhado por epico com estimativas em story points

### Criterios de Aceitacao do MVP

O MVP e considerado "lancavel" quando:

- [ ] 4 consultores conseguem logar com suas credenciais
- [ ] Import de xlsx funcional com normalizacao CNPJ e classificacao 3-tier
- [ ] Motor de Regras retorna 9 dimensoes para todas as 92 combinacoes
- [ ] Score calculado em tempo real com prioridade P0-P7
- [ ] Agenda diaria gerada automaticamente com 40-60 itens por consultor
- [ ] Consultor consegue registrar atendimento e Motor roda automaticamente
- [ ] Dashboard exibe KPIs reais (nao fake/seed)
- [ ] Carteira com filtros funcionais
- [ ] Two-Base Architecture validada: 0 violacoes
- [ ] CNPJ validado: 0 floats, 0 duplicatas
- [ ] Faturamento total dentro de +/- 0.5% do baseline R$ 2.091.000
- [ ] Deploy funcional em producao (Vercel + Railway)
- [ ] 0 dados ALUCINACAO integrados

---

**Documento preparado por:** @pm (Product Manager) -- CRM VITAO360
**Data:** 25/03/2026
**Versao:** 1.0
**Proxima revisao:** Apos validacao de Leandro
**Fontes:** PRD_CRM_VITAO360.md, PRD_COMPLETO_CRM_VITAO.md, MOTOR_COMPLETO_CRM_VITAO360.md, BLUEPRINT_SKILLS_SAAS.md, SCORE_ENGINE_SPEC.md, MOTOR_REGRAS_SPEC.md, backend/app/ (routes, models, database), frontend/src/, project memory (SaaS migration, roadmap 3 fases, Deskrio API)
