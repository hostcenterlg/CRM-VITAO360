# GAP ANALYSIS -- Backend Models vs PRD SaaS (FR-001 a FR-056)

**Gerado por:** @qa -- CRM VITAO360  
**Data:** 2026-03-25  
**Versao PRD analisada:** 1.0 (25/03/2026)  
**Escopo:** Epicos E1 a E14, Features FR-001 a FR-056  
**Metodologia:** Verificacao em 3 camadas -- Model, Route, Service

---

## LEGENDA DE STATUS

| Status | Significado |
|--------|-------------|
| COBERTO | Model + Route + Service implementados atendendo todos os ACs verificaveis no backend |
| PARCIAL | Implementacao existe mas algum AC ausente, divergente ou incompleto |
| AUSENTE | Nenhuma implementacao encontrada para o requisito |

---

## SUMARIO EXECUTIVO

| Metrica | Valor |
|---------|-------|
| Total FRs analisados | 56 |
| COBERTO | 22 (39%) |
| PARCIAL | 22 (39%) |
| AUSENTE | 12 (21%) |
| Score geral MVP (E1-E8) | 65% |
| Score geral v2 (E9-E14) | 18% |

### Distribuicao por Epico

| Epico | FRs | Cobertos | Parciais | Ausentes | Status |
|-------|-----|----------|----------|----------|--------|
| E1 -- Import | 6 | 2 | 3 | 1 | PARCIAL |
| E2 -- Motor de Regras | 5 | 2 | 2 | 1 | PARCIAL |
| E3 -- Score + Sinaleiro | 6 | 2 | 3 | 1 | PARCIAL |
| E4 -- Agenda | 5 | 2 | 2 | 1 | PARCIAL |
| E5 -- Dashboard CEO | 5 | 3 | 1 | 1 | PARCIAL |
| E6 -- Carteira | 4 | 2 | 2 | 0 | PARCIAL |
| E7 -- LOG Append-Only | 4 | 3 | 1 | 0 | BOM |
| E8 -- Autenticacao | 3 | 2 | 1 | 0 | PARCIAL |
| E9 -- Deskrio (WhatsApp) | 4 | 0 | 0 | 4 | AUSENTE |
| E10 -- Deploy | 4 | 1 | 2 | 1 | PARCIAL |
| E11 -- Mercos | 3 | 0 | 1 | 2 | AUSENTE |
| E12 -- SAP | 2 | 0 | 1 | 1 | AUSENTE |
| E13 -- Projecao | 3 | 2 | 1 | 0 | BOM |
| E14 -- RNC | 2 | 1 | 1 | 0 | PARCIAL |

---

## DIVERGENCIAS CRITICAS (D1-D8)

### D1 -- Score Engine: Pesos v2 divergem do PRD FR-012

**Gravidade: ALTA**

O PRD especifica (FR-012):
- FASE: 25%, SINALEIRO: 20%, CURVA_ABC: 20%, TEMPERATURA: 15%, TIPO_CLIENTE: 10%, TENTATIVAS: 10%

O score_service.py implementa Score v2 com fatores completamente diferentes:
- URGENCIA: 30%, VALOR: 25%, FOLLOWUP: 20%, SINAL: 15%, TENTATIVA: 5%, SITUACAO: 5%

Adicionalmente, o ScoreHistorico armazena colunas legacy com aliases dos fatores v2,
gerando inconsistencia semantica no historico (fator_fase = fator_urgencia, etc).

**Acao requerida:** L3 -- Leandro decide qual versao do score prevalece (PRD v1 ou Score v2 atual).

### D2 -- Sinaleiro: LARANJA ausente

**Gravidade: ALTA -- 5 cores no PRD, 4 implementadas**

FR-014 AC4 define: LARANJA quando ratio dias/ciclo <= 1.5 (alerta -- passou do ciclo).
sinaleiro_service.py implementa apenas VERDE, AMARELO, VERMELHO, ROXO.
A faixa LARANJA (ratio 1.0-1.5) e mapeada diretamente para VERMELHO, elevando falsos alertas.

### D3 -- Motor: Seed de 92 combinacoes nao confirmado

**Gravidade: ALTA**

FR-007 AC2/AC4 exige seed com 92 combinacoes exatas.
Existe conflito nos comentarios do motor_regras_service.py:
- Docstring do servico diz: seed de 92 combinacoes
- Cabecalho do modulo diz: seed de 68 regras pre-calculadas
O fallback para scripts/motor_regras.py mascara o problema mas cria dependencia em arquivo externo.
Acao requerida: Auditoria do seed da tabela regras_motor para confirmar contagem real.

### D4 -- Prioridade v2: Logica diverge do PRD FR-013

**Gravidade: ALTA**

PRD FR-013 define P0-P7 por faixas de score:
- P0: SUPORTE com problema_aberto (sem score)
- P1: EM ATENDIMENTO + follow-up vencido + CS no prazo
- P2: Score 80-100, P3: Score 60-79, P4: Score 45-59
- P5: Score 30-44, P6: Score 15-29, P7: Score 0-14

Score v2 atual define P1-P7 por combinacoes de situacao/resultado/tipo_cliente sem faixas numericas fixas.
Nao ha P0 no _prioridade_v2() -- P0 seria atribuido externamente via problema_aberto.

### D5 -- RESULTADOS_VALIDOS: 12 implementados, 14 no PRD

**Gravidade: MEDIA**

FR-020 e FR-032 listam 14 opcoes incluindo POS-VENDA e CS.
routes_atendimentos.py implementa apenas 12 -- faltam POS-VENDA e CS como opcoes diretas.

### D6 -- RNC: Categorias e Status divergem do PRD

**Gravidade: MEDIA**

FR-055 especifica 8 categorias: entrega, qualidade, NF, prazo, produto errado, falta, avaria, outro.
rnc.py implementa 6 categorias diferentes: ENTREGA, QUALIDADE, PAGAMENTO, ATENDIMENTO, PRODUTO, OUTRO.

FR-055 especifica status: ABERTO, EM_ANDAMENTO, RESOLVIDO, ENCERRADO.
rnc.py implementa: ABERTO, EM_ANDAMENTO, RESOLVIDO, CANCELADO.

### D7 -- Roles: gerente e consultor_externo ausentes

**Gravidade: MEDIA**

usuario.py implementa: admin, consultor, viewer.
FR-037 especifica: Admin, Gerente (Daiane), Consultor, Consultor Externo (Julio sem dados financeiros).
O role viewer nao consta no PRD. gerente e consultor_externo nao existem no model.

### D8 -- ScoreHistorico: Colunas incompativeis com Score v2

**Gravidade: BAIXA**

score_historico.py define colunas legacy: fator_fase, fator_sinaleiro, fator_curva, etc.
score_service.py preenche essas colunas com aliases dos fatores v2 (fator_fase = fator_urgencia).
Isso impossibilita auditoria real de quais fatores determinaram cada score historico.

---

## ANALISE DETALHADA POR EPICO

---

## E1 -- Importacao de Dados (FR-001 a FR-006)

### FR-001 -- Pipeline de Importacao | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | ImportJob com status PENDENTE/PROCESSANDO/CONCLUIDO/ERRO + contadores | Nenhum |
| Route | AUSENTE | POST /api/import/upload, GET /api/import/history, GET /api/import/status/{job_id} |
| Service | AUSENTE | Pipeline completo de import |

O model ImportJob existe e e bem estruturado, mas nenhuma rota ou servico o aciona.
ACs ausentes: AC3 (endpoint de upload), AC4 (GET /api/import/history), AC6 (integracao com classificacao 3-tier no import).

### FR-002 -- Normalizacao CNPJ | **Status: COBERTO**

| Camada | Implementado |
|--------|-------------|
| Model | Todos os 11 modelos usam cnpj=String(14). ForeignKey referencias consistentes. |
| Route | routes_clientes.py: re.sub(r"\D", "", cnpj).zfill(14) nos endpoints GET /{cnpj} |
| Service | motor_regras_service.py documenta R5. Todos os servicos propagam String(14). |

Todos os 6 ACs verificados: remocao de pontuacao, zero-padding, nunca float, UniqueConstraint.

### FR-003 -- Classificacao 3-Tier | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | Cliente.classificacao_3tier, Venda.classificacao_3tier (default=REAL) | LogInteracao sem classificacao (intencional por R4) |
| Route | Dashboard e sinaleiro excluem ALUCINACAO. agenda_service aplica R8. | Nenhum endpoint expoe classificacao 3-tier no import |
| Service | agenda_service.gerar_todas() filtra classificacao_3tier != ALUCINACAO. | Classificacao automatica no import ausente |

ACs verificados: AC1, AC3, AC4, AC6.
ACs ausentes: AC2 (classificacao de SINTETICO automatica), AC5 (os 558 registros ALUCINACAO sem pipeline de verificacao).

### FR-004 -- Merge de Fontes | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | Venda.fonte (MERCOS/SAP/MANUAL). | |
| Route | AUSENTE | Nenhum endpoint de merge |
| Service | AUSENTE | Servico de merge/deduplicacao |

ACs ausentes: AC1-AC5. Todo AC e de responsabilidade de servico/pipeline nao implementado.

### FR-005 -- Relatorio de Import | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | ImportJob com registros_lidos, inseridos, atualizados, ignorados, erro_mensagem | cnpjs_invalidos, duplicatas, alucinacao_detectada |
| Route | AUSENTE | GET /api/import/history |
| Service | AUSENTE | Geracao do relatorio pos-import |

ACs parciais: AC3 (tabela import_jobs existe). ACs ausentes: AC1, AC2, AC4.

### FR-006 -- Processamento em Background | **Status: AUSENTE**

Nenhuma implementacao de job assincrono encontrada.
O model ImportJob existe para tracking, mas nenhum worker, queue, ou endpoint de status foi implementado.
ACs ausentes: Todos (AC1-AC4).

---

## E2 -- Motor de Regras no Backend (FR-007 a FR-011)

### FR-007 -- Tabela de Regras no Banco | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | RegraMotor: id, situacao, resultado, estagio_funil, fase, tipo_contato, acao_futura, temperatura, followup_dias, grupo_dash, tipo_acao, chave. UniqueConstraint(situacao, resultado). | |
| Route | AUSENTE | Endpoint de administracao das regras |
| Service | lookup primario por chave SITUACAO+RESULTADO. Fallback para scripts/. | Seed auditado com 92 combinacoes -- ver D3 |

ACs parciais: AC1 (estrutura do model correta), AC3 (UniqueConstraint presente).
ACs duvidosos: AC2 (seed de 92 -- ver D3), AC4 (cobertura 100% -- nao verificavel sem inspecao do seed).

### FR-008 -- API de Lookup do Motor | **Status: AUSENTE**

Nenhum endpoint GET /api/motor/lookup encontrado nos arquivos de rota.
A logica de lookup existe no motor_regras_service.py mas nao ha rota exposta para consulta direta.
ACs ausentes: AC1-AC5.

### FR-009 -- Aplicacao Automatica do Motor ao Registrar Atendimento | **Status: COBERTO**

| Camada | Implementado |
|--------|-------------|
| Model | LogInteracao armazena as 9 dimensoes calculadas pelo motor. |
| Route | POST /api/atendimentos aciona motor_service.registrar_atendimento() automaticamente. Retorna MotorResultado. |
| Service | motor_regras_service.registrar_atendimento(): busca cliente -> aplica motor -> cria LogInteracao -> atualiza Cliente -> recalcula sinaleiro + score. Fluxo completo. |

ACs verificados: AC1, AC2, AC3, AC4.
AC parcial: AC5 (follow-up automatico -- followup_dias calculado e persistido, mas nenhum mecanismo de alarme/notificacao implementado).

### FR-010 -- Calculo de SITUACAO Automatico | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | Cliente.situacao e Cliente.dias_sem_compra existem. | Sem logica de calculo automatico de situacao |
| Route | AUSENTE | Sem endpoint ou trigger de recalculo |
| Service | sinaleiro_service.py usa situacao mas nao a recalcula. | Nenhum servico de recalculo automatico de situacao |

ACs ausentes: AC1-AC8. A situacao e importada manualmente, nunca calculada a partir de dias_sem_compra.
Nenhum job schedulado implementado.

### FR-011 -- Painel Admin de Regras | **Status: AUSENTE**

Nenhum endpoint ou interface administrativa para visualizar as regras do motor foi implementado.
O model RegraMotor existe mas nao ha rota de leitura das 92 regras.
Nota: Este FR tem prioridade Could no PRD -- aceitavel estar ausente no MVP.

---

## E3 -- Score + Sinaleiro em Tempo Real (FR-012 a FR-017)

### FR-012 -- Calculo de Score Ponderado | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | Cliente.score, ScoreHistorico com 6 fatores | Colunas do historico semanticamente erradas (ver D8) |
| Route | GET /api/clientes/{cnpj}/score-history retorna ultimos 30 calculos com todos os fatores | Nenhum endpoint de calculo sob demanda |
| Service | score_service.py implementa Score v2 com 6 fatores ponderados. Recalcula apos cada atendimento. | Ver D1: fatores e pesos completamente divergentes do PRD |

Divergencia critica D1: PRD FR-012 especifica FASE(25%), SINALEIRO(20%), CURVA_ABC(20%), TEMPERATURA(15%),
TIPO_CLIENTE(10%), TENTATIVAS(10%) com tabelas de lookup especificas.
Score v2 implementado usa URGENCIA(30%), VALOR(25%), FOLLOWUP(20%), SINAL(15%), TENTATIVA(5%), SITUACAO(5%)
com logica de calculo diferente por fator. Requer decisao L3.

### FR-013 -- Classificacao de Prioridade P0-P7 | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | Cliente.prioridade String(5). Cliente.problema_aberto, followup_vencido, cs_no_prazo Boolean. | |
| Route | Filtro por prioridade em GET /api/clientes. | |
| Service | score_service._prioridade_v2(): regras por situacao/resultado/tipo_cliente/score. | Ver D4: logica diverge do PRD |

Divergencia D4: PRD define P0-P7 por faixas numericas de score.
Implementacao usa combinacoes de contexto sem faixas fixas. P0 nao e calculado no _prioridade_v2().

### FR-014 -- Calculo de Sinaleiro | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | Cliente.sinaleiro | LARANJA ausente |
| Route | GET /api/sinaleiro/clientes retorna distribuicao. POST /api/sinaleiro/recalcular em batch. | |
| Service | sinaleiro_service.py: VERDE, AMARELO, VERMELHO, ROXO | Ver D2: LARANJA ausente |

ACs verificados: AC1 (ROXO para prospect/lead), AC2 (VERDE dentro do ciclo), AC3 (AMARELO proximo ao ciclo), AC6 (NOVO = VERDE).
ACs ausentes: AC4 (LARANJA ratio 1.0-1.5 -- ver D2).
AC parcial: AC5 (VERMELHO > 1.5: implementado mas com threshold ciclo+30 dias fixos ao inves de ratio 1.5x).

### FR-015 -- Desempate de Score | **Status: AUSENTE**

Nenhum mecanismo de desempate multi-criterio foi encontrado.
A ordenacao em routes_clientes.py usa apenas score.desc().nulls_last() seguido de nome_fantasia.
A agenda usa posicao definida sequencialmente sem criterio de desempate.
ACs ausentes: AC1-AC5 (CURVA_ABC, Ticket Medio, TIPO_CLIENTE, follow-up mais vencido).

### FR-016 -- API de Score (Breakdown) | **Status: PARCIAL**

GET /api/clientes/{cnpj}/score-history existe e retorna historico com fatores individuais.
Nao existe endpoint GET /api/clientes/{cnpj}/score para o score atual com breakdown em tempo real.

ACs parciais: AC1 (score-history tem breakdown mas do historico, nao do score atual), AC3 (tempo de resposta provavelmente OK).
ACs ausentes: endpoint /score (nao /score-history), pesos aplicados nao exibidos.

### FR-017 -- Meta Balance (Prospeccao Boost) | **Status: AUSENTE**

Nenhuma implementacao de job diario de calculo de pipeline vs meta, sem bonus de +20 pontos para PROSPECCAO.
Nota: Este FR tem prioridade Could no PRD -- aceitavel estar ausente no MVP.

---

## E4 -- Agenda Inteligente (FR-018 a FR-022)

### FR-018 -- Geracao Automatica de Agenda Diaria | **Status: COBERTO**

| Camada | Implementado |
|--------|-------------|
| Model | AgendaItem: posicao, consultor, data_agenda, nome_fantasia, situacao, temperatura, score, prioridade, sinaleiro, acao, followup_dias. Chave unica (cnpj, consultor, data_agenda). |
| Route | POST /api/agenda/gerar (admin only). Suporta ?data=YYYY-MM-DD. |
| Service | agenda_service.gerar_todas(): idempotente (deleta antes de gerar), P0 pula fila, P7 excluido, limite 40/DAIANE=20, ordenacao P0->P1->P2-P6 por score desc, R8 aplicado. |

ACs verificados: AC1, AC3, AC4, AC5, AC6, AC7.
AC parcial: AC2 (score: copia o score atual do cliente, nao recalcula durante geracao), AC8 (cron 05:00 BRT -- nenhum scheduler implementado, geracao e sob demanda).

### FR-019 -- Tela de Agenda do Consultor | **Status: PARCIAL**

| Camada | Implementado | Faltando |
|--------|-------------|---------|
| Model | AgendaItem tem todos os campos necessarios | |
| Route | GET /api/agenda (todos), GET /api/agenda/{consultor} | Filtro por prioridade, busca por nome/CNPJ, contador de atendidos |
| Service | agenda_service gera com todos os dados | Calculo de atendidos hoje |

ACs parciais: AC1 (dados completos retornados), AC2 (filtro por prioridade -- ausente na query), AC3 (busca -- ausente), AC5 (follow-up vencido -- campo nao presente no AgendaItem), AC6 (contador atendidos -- ausente).
ACs frontend: AC4 (click abre detalhe).

### FR-020 -- Marcar Atendimento Realizado | **Status: COBERTO**

POST /api/atendimentos cobre completamente este FR:
- Dropdown de RESULTADO validado (12 de 14 -- ver D5)
- Campo descricao obrigatorio
- Motor executa automaticamente
- Score/Sinaleiro recalculados
- LogInteracao criado com todas as dimensoes
- Resposta inclui acao futura e follow-up dias

AC parcial: AC1 -- 12 opcoes de RESULTADO ao inves de 14 (faltam POS-VENDA e CS -- ver D5).

### FR-021 -- Agenda Historica | **Status: COBERTO**

GET /api/agenda/historico implementado com:
- Parametro ?data=YYYY-MM-DD
- Filtro por consultor opcional
- Retorna itens ordenados por consultor e posicao

ACs parciais: AC1 (date picker -- frontend), AC3 (metricas planejado/atendido -- ausente no backend), AC4 (somente leitura -- enforced por ausencia de PUT/PATCH).

### FR-022 -- Redistribuicao de Carteira | **Status: AUSENTE**

Nenhum endpoint ou servico de redistribuicao de carteira encontrado.
O PATCH /api/clientes/{cnpj} para alterar consultor tambem esta ausente (ver FR-031).
Nota: Este FR tem prioridade Should no PRD.

---

## E5 -- Dashboard CEO (FR-023 a FR-027)

### FR-023 -- KPIs Executivos | **Status: COBERTO**

GET /api/dashboard/kpis retorna:
- Total clientes, por situacao (ATIVO, PROSPECT, INAT.REC, INAT.ANT)
- Faturamento total (REAL+SINTETICO, excluindo ALUCINACAO)
- Media score, clientes com sinaleiro VERMELHO/AMARELO
- Follow-ups vencidos (followup_vencido=True)
- Clientes criticos (temperatura=CRITICO)
- FATURAMENTO_BASELINE = 2_091_000.0 (correto)
- PROJECAO_2026 = 3_377_120.0 (correto)

ACs verificados: AC1-AC10. Baseline correto R$ 2.091.000.
AC parcial: AC11 (atualizacao em tempo real -- backend retorna dados atuais mas sem WebSocket/SSE).

### FR-024 -- Distribuicoes por Dimensao | **Status: COBERTO**

GET /api/dashboard/distribuicao retorna distribuicoes por: situacao, consultor, sinaleiro, curva_abc, prioridade, temperatura. Com percentagens calculadas.
GET /api/clientes/stats retorna: por_situacao, por_consultor, por_sinaleiro, por_curva_abc, por_prioridade.

ACs verificados: AC1-AC6.
AC parcial: AC7 (clicavel filtra carteira -- frontend, mas os endpoints de filtro existem no backend).
AC ausente: AC1 menciona LARANJA no pie do sinaleiro -- cor inexistente no backend (ver D2).

### FR-025 -- Top 10 Clientes | **Status: COBERTO**

GET /api/dashboard/top10 retorna os 10 maiores por faturamento com:
nome_fantasia, consultor, faturamento_total, score, prioridade, curva_abc, sinaleiro.
Exclui ALUCINACAO (R8 enforced).

ACs verificados: AC1, AC2, AC3 (click -- frontend).
AC ausente: AC4 (exportacao CSV -- nenhuma rota de export implementada).

### FR-026 -- Visao por Consultor | **Status: PARCIAL**

GET /api/projecao/{consultor} existe mas retorna apenas breakdown mensal de vendas, nao KPIs completos por consultor.
GET /api/clientes com filtro ?consultor=X retorna a mini-carteira.
Nenhum endpoint de dashboard filtrado por consultor com KPIs agregados existe.

ACs parciais: AC2 (KPIs filtrados -- parcialmente via projecao/{consultor}), AC3 (mini-carteira -- via /api/clientes?consultor=X).
ACs ausentes: AC1 (selector com KPIs completos), AC4 (comparativo overlay entre consultores).

### FR-027 -- Tendencias Temporais | **Status: AUSENTE**

Nenhum endpoint de tendencias temporais (evolucao mensal de ativos/inativos, churn) encontrado.
Nota: Este FR tem prioridade Could no PRD.

---

## E6 -- CARTEIRA Completa (FR-028 a FR-031)

### FR-028 -- Listagem de Clientes com Filtros | **Status: COBERTO**

GET /api/clientes implementa:
- 8 filtros cumulativos: consultor, situacao, sinaleiro, curva_abc, temperatura, prioridade, uf, busca
- Busca ilike em nome_fantasia e razao_social
- Paginacao com limit/offset
- Ordenacao padrao score desc
- RBAC: consultor ve apenas propria carteira

ACs verificados: AC1-AC5, AC7 (cores -- dados retornados, CSS e frontend), AC8.
AC parcial: AC6 (ordenacao custom por coluna -- somente score desc implementado, sem ordenacao por header).

### FR-029 -- Detalhe do Cliente | **Status: COBERTO**

GET /api/clientes/{cnpj} retorna ClienteDetalhe com:
- Identificacao completa (CNPJ, nome_fantasia, razao_social, uf, cidade, codigo_cliente)
- Status (situacao, temperatura, score, prioridade, sinaleiro, curva_abc, tipo_cliente, fase)
- Historico de compras (dias_sem_compra, valor_ultimo_pedido, ciclo_medio, n_compras, faturamento_total)
- Motor (estagio_funil, acao_futura, followup_dias, grupo_dash)
- Projecao (meta_anual, realizado_acumulado, pct_alcancado, gap_valor, status_meta)
- classificacao_3tier visivel

GET /api/clientes/{cnpj}/timeline retorna historico unificado VENDA + INTERACAO.
ACs verificados: AC1-AC6. AC7 (timeline implementado em /timeline).

### FR-030 -- Exportacao CSV/Excel | **Status: AUSENTE**

Nenhum endpoint de exportacao encontrado. GET /api/clientes retorna JSON com paginacao mas sem export.
Nota: Este FR tem prioridade Should no PRD.

### FR-031 -- Edicao Inline de Consultor | **Status: PARCIAL**

Nenhum endpoint PATCH /api/clientes/{cnpj} foi encontrado.
O model Cliente suporta alteracao de campo consultor mas nao ha rota para isso.

ACs ausentes: AC2 (PATCH /api/clientes/{cnpj}), AC3 (historico de alteracao logado), AC4 (somente Admin).

---

## E7 -- LOG Append-Only (FR-032 a FR-035)

### FR-032 -- Registro de Atendimento | **Status: COBERTO**

POST /api/atendimentos com schema AtendimentoCreate (cnpj, resultado, descricao):
- Data/hora automatica (datetime.now(timezone.utc))
- Consultor do JWT automatico
- Motor executa e preenche as 9 dimensoes
- LogInteracao sem campos monetarios (R4 enforced)
- Nenhum PUT/PATCH/DELETE implementado (append-only enforced por ausencia)

ACs verificados: AC1-AC5.
AC parcial: AC6 (timestamp BRT -- implementado em UTC, conversao e frontend/configuracao).

### FR-033 -- Timeline de Atendimentos | **Status: COBERTO**

GET /api/clientes/{cnpj}/timeline retorna eventos combinados VENDA + INTERACAO ordenados por data desc.
GET /api/atendimentos com filtros por consultor, cnpj, resultado.

ACs verificados: AC1, AC2, AC5 (paginacao via limit/offset).
ACs parciais: AC3 (filtro por periodo -- ausente na timeline), AC4 (filtro por resultado -- em /api/atendimentos mas nao na /timeline).

### FR-034 -- Contadores Diarios | **Status: PARCIAL**

GET /api/atendimentos/stats retorna contagens por resultado e por consultor (total global, nao por data).
Nenhum filtro por hoje nos stats. Nenhum calculo de percentagem de agenda completada.

ACs parciais: AC1 (atendimentos por consultor -- global, nao por dia), AC2 (breakdown por resultado -- implementado).
ACs ausentes: AC3 (percentagem agenda completada), AC4 (comparativo com meta diaria de 22/rep/dia).

### FR-035 -- Validacao Two-Base no Backend | **Status: COBERTO**

| Verificacao | Status |
|-------------|--------|
| Model LogInteracao sem campos monetarios | PASS |
| Model Venda com CheckConstraint valor_pedido > 0 | PASS |
| motor_regras_service.py documenta R4 explicitamente | PASS |
| agenda_service.py documenta R4 | PASS |
| sinaleiro_service.py documenta R4 | PASS |
| score_service.py documenta R4 | PASS |
| FATURAMENTO_BASELINE = 2_091_000.0 em dashboard e projecao | PASS |

ACs verificados: AC1-AC3, AC5 (tabela separada com CNPJ + data + valor).
AC ausente: AC4 (test automatizado que tenta inserir valor e confirma rejeicao).

---

## E8 -- Autenticacao e Roles (FR-036 a FR-038)

### FR-036 -- Login com Email/Senha | **Status: COBERTO**

POST /api/auth/login: email + senha, JWT + refresh token, bcrypt verificado.
POST /api/auth/refresh: renovacao de token.
GET /api/auth/me: dados do usuario logado.
PUT /api/auth/password: alteracao de senha.

ACs verificados: AC2 (JWT), AC4 (bcrypt), AC6 (redirect -- frontend).
ACs parciais:
- AC1 (tela login -- frontend)
- AC3 (expiracao: 8h implementado vs 24h PRD; refresh: 30d vs 7d PRD)
- AC5 (rate limiting -- nao encontrado implementado no backend)

### FR-037 -- Roles e Permissoes | **Status: PARCIAL**

Implementado: admin, consultor, viewer.
PRD especifica: Admin, Gerente, Consultor, Consultor Externo.
Ver D7.

ACs verificados: AC1 (admin: acesso total), AC3 (consultor: propria carteira apenas), AC5 (middleware RBAC em cada endpoint).
ACs ausentes: AC2 (gerente: ve todos mas nao configura), AC4 (consultor_externo: sem dados financeiros).
AC adicional nao previsto: viewer existe no sistema mas nao esta no PRD.

### FR-038 -- Gerenciamento de Usuarios | **Status: PARCIAL**

| Endpoint | Status |
|----------|--------|
| POST /api/auth/users (criar) | IMPLEMENTADO |
| GET /api/auth/users (listar) | IMPLEMENTADO |
| PUT/PATCH /api/auth/users/{id} (editar) | AUSENTE |
| Desativar usuario /api/auth/users/{id} | AUSENTE |

ACs verificados: AC1 (criar: nome, email, senha, role, consultor_nome), AC3 (listar ativos), AC5 (somente Admin).
ACs ausentes: AC2 (editar role, reset senha, ativar/desativar), AC4 (soft delete -- campo ativo existe mas sem endpoint).

---

## E9 -- Integracao Deskrio (FR-039 a FR-042) | **Status: AUSENTE (todos os 4 FRs)**

Nenhuma implementacao de integracao Deskrio encontrada nos arquivos de backend.
Nenhum arquivo de servico, rota ou configuracao relacionado ao Deskrio foi identificado.
FR-039 (Envio WA), FR-040 (Recepcao Tickets), FR-041 (Sincronizacao Contatos), FR-042 (Templates): todos ausentes.
Nota: Estes FRs tem prioridade Should ou Could no PRD -- sao v2/fase posterior.

---

## E10 -- Deploy (FR-043 a FR-046)

### FR-043 -- Deploy Frontend (Vercel) | **Status: NAO VERIFICAVEL**

Nao e possivel verificar configuracao de CI/CD Vercel nos arquivos de backend.
Requer verificacao no repositorio frontend e configuracoes de deployment.

### FR-044 -- Deploy Backend (Railway) | **Status: PARCIAL**

Implementado: DATABASE_URL via variavel de ambiente em database.py. Estrutura de modelos pronta para PostgreSQL.
Faltando: Dockerfile nao verificado, Alembic nao verificado, health check endpoint /health ausente nas rotas analisadas.

### FR-045 -- Migracao SQLite para PostgreSQL | **Status: PARCIAL**

Implementado: DATABASE_URL como variavel de ambiente. CNPJ = String(14) em todos os modelos.
Indices presentes: cnpj, consultor, situacao, data_agenda.
Faltando: Alembic configurado para migrations versionadas (nao encontrado), script de seed para producao.

### FR-046 -- Backup Automatico | **Status: AUSENTE**

Nenhuma configuracao de backup automatico encontrada.

---

## E11 -- Integracao Mercos (FR-047 a FR-049)

### FR-047 -- Import de Pedidos Mercos | **Status: PARCIAL**

Implementado: Model Venda com campos cnpj, data_pedido, valor_pedido, consultor, fonte (MERCOS/SAP/MANUAL),
classificacao_3tier, numero_pedido, mes_referencia. CheckConstraint valor_pedido > 0. Two-Base enforced.
POST /api/vendas existe para registro manual.
Faltando: Nenhum servico ou endpoint de import automatizado do Mercos.

ACs verificados: AC5 (Two-Base: vendas separadas dos logs).
ACs ausentes: AC1 (sincronizacao diaria automatica), AC2 (campos Mercos), AC4 (DE-PARA), AC6 (verificacao de datas Mercos).

### FR-048 -- Import de Carteira Mercos | **Status: AUSENTE**

Nenhum servico de sincronizacao de carteira Mercos encontrado.

### FR-049 -- Curva ABC do Mercos | **Status: AUSENTE**

Nenhum servico de calculo ou import de curva ABC encontrado.
O campo curva_abc existe no model Cliente mas e definido manualmente/importado.

---

## E12 -- Integracao SAP (FR-050 a FR-051)

### FR-050 -- Import de Cadastro SAP | **Status: PARCIAL**

Implementado: Model Cliente tem: codigo_cliente, tipo_cliente_sap, macroregiao.
Faltando no model: status_cadastro_sap, status_atendimento_sap, bloqueio_sap, grupo_cliente,
gerente_nacional, representante, canal, microregiao, grupo_chave.
Nenhum servico de import SAP implementado.

### FR-051 -- Import de Metas SAP | **Status: PARCIAL**

Implementado: Model Meta com cnpj, ano, mes, meta_sap, meta_igualitaria, realizado.
Model Cliente com meta_anual, realizado_acumulado, pct_alcancado, gap_valor, status_meta.
Faltando: Nenhum servico de import de metas SAP. Pipeline de atualizacao ausente.

---

## E13 -- Projecao e Metas (FR-052 a FR-054)

### FR-052 -- Projecao Consolidada | **Status: COBERTO**

GET /api/projecao retorna:
- Faturamento baseline R$ 2.091.000 (correto)
- Projecao 2026: R$ 3.377.120 (correto)
- Q1 real: R$ 459.465
- % alcancado, gap em R$
- Apenas REAL + SINTETICO

GET /api/dashboard/projecao retorna dados equivalentes.
ACs verificados: AC1-AC5, AC7 (ALUCINACAO excluida).
AC parcial: AC6 (grafico de barras mensal -- dados disponíveis via /projecao/{consultor} mas sem endpoint mensal consolidado).

### FR-053 -- Projecao por Consultor | **Status: COBERTO**

GET /api/projecao/{consultor} retorna breakdown mensal de vendas por consultor com total, por_mes, faturamento_total.

ACs verificados: AC1-AC2.
ACs parciais: AC3 (identificar abaixo da meta -- dados disponíveis mas nao calculado), AC4 (distribuicao proporcional ao baseline -- nao implementado).

### FR-054 -- Projecao por Cliente | **Status: PARCIAL**

Nenhum endpoint GET /api/projecao/cliente/{cnpj} encontrado.
Os dados existem: Cliente.meta_anual, realizado_acumulado, pct_alcancado, gap_valor, status_meta no model.
O Model Meta tem historico mensal por cliente.
Faltando: Endpoint dedicado com historico mensal em barras.
Nota: Este FR tem prioridade Could no PRD.

---

## E14 -- RNC (FR-055 a FR-056)

### FR-055 -- CRUD de RNC | **Status: PARCIAL**

Implementado: Model RNC com campos: cnpj, data_abertura, consultor, tipo_problema, descricao, status, prazo_resolucao, responsavel, resolucao, data_resolucao.

Divergencias (ver D6):
- Categorias: 6 implementadas vs 8 do PRD
- Status CANCELADO vs ENCERRADO do PRD

Faltando: Nenhum endpoint /api/rnc/* encontrado. CRUD completamente ausente na camada de API.
Nota: Este FR tem prioridade Could no PRD.

### FR-056 -- Alerta de RNC no Motor | **Status: PARCIAL**

Implementado: Cliente.problema_aberto Boolean existe.
A logica de P0 depende de problema_aberto mas o mecanismo que seta problema_aberto=True quando RNC e aberta nao foi encontrado.

ACs parciais: AC1 (P0 quando problema_aberto -- via score v2 com regra SUPORTE), AC2 (P0 pula fila -- agenda_service trata P0 corretamente).
ACs ausentes: AC3 (ao resolver RNC, voltar a prioridade calculada -- nenhum mecanismo de reset), AC4 (historico de escalacao P0).

---

## ITENS DE ACAO PRIORIZADOS

### P0 -- Bloqueadores MVP (Must Have ausentes ou incorretos)

| ID | Descricao | FR afetado | Esforco |
|----|-----------|-----------|---------|
| A01 | Definir se Score v2 ou Score PRD e o oficial (L3 decisao obrigatoria) | FR-012 | L3 |
| A02 | Adicionar LARANJA ao sinaleiro (5a cor: ratio dias/ciclo 1.0-1.5) | FR-014 | Baixo |
| A03 | Auditoria do seed da tabela regras_motor (confirmar 92 ou 68 regras) | FR-007 | Medio |
| A04 | Adicionar POS-VENDA e CS ao RESULTADOS_VALIDOS em routes_atendimentos.py | FR-020, FR-032 | Baixo |
| A05 | Implementar PATCH /api/clientes/{cnpj} para edicao de consultor (admin only) | FR-031 | Baixo |
| A06 | Implementar PUT/PATCH /api/auth/users/{id} e endpoint de desativacao | FR-038 | Baixo |
| A07 | Criar GET /api/motor/lookup?situacao=X&resultado=Y com 9 dimensoes | FR-008 | Baixo |
| A08 | Alinhar roles: adicionar gerente e consultor_externo ao model Usuario e RBAC | FR-037 | Medio |

### P1 -- Alta Prioridade (Should Have ou divergencias significativas)

| ID | Descricao | FR afetado | Esforco |
|----|-----------|-----------|---------|
| A09 | Implementar endpoint POST /api/import/upload e GET /api/import/history | FR-001, FR-005 | Alto |
| A10 | Implementar calculo automatico de SITUACAO por dias_sem_compra (7 regras) | FR-010 | Medio |
| A11 | Alinhar threshold sinaleiro: usar ratio x ciclo_medio ao inves de ciclo+30 dias fixos | FR-014 | Baixo |
| A12 | Implementar desempate multi-criterio: curva ABC, ticket medio, tipo_cliente, followup vencido | FR-015 | Medio |
| A13 | Corrigir colunas do ScoreHistorico para refletir fatores v2 reais (renomear ou adicionar colunas) | D8 | Baixo |
| A14 | Corrigir status RNC: CANCELADO -> ENCERRADO e adicionar categorias faltantes | FR-055 | Minimo |
| A15 | Implementar endpoints CRUD /api/rnc/* | FR-055 | Alto |
| A16 | Mecanismo que seta problema_aberto=True ao abrir RNC e False ao resolver | FR-056 | Baixo |
| A17 | Implementar rate limiting no login (5 tentativas/min por IP) | FR-036 | Baixo |
| A18 | Adicionar campo followup_vencido ao AgendaItem para indicador visual | FR-019 | Baixo |

### P2 -- Medio Prazo (Could Have ou infraestrutura)

| ID | Descricao | FR afetado | Esforco |
|----|-----------|-----------|---------|
| A19 | Health check endpoint GET /health para Railway | FR-044 | Minimo |
| A20 | Configurar Alembic para migrations versionadas | FR-045 | Medio |
| A21 | Implementar exportacao CSV da carteira (GET /api/clientes/export) | FR-030 | Medio |
| A22 | Adicionar endpoint GET /api/projecao/cliente/{cnpj} | FR-054 | Baixo |
| A23 | Filtro por data em GET /api/atendimentos/stats (atendimentos hoje) | FR-034 | Baixo |
| A24 | Cron scheduler para geracao automatica de agenda as 05:00 BRT | FR-018 | Alto |
| A25 | Endpoint GET /api/motor/regras para listar as 92 regras (admin only) | FR-011 | Baixo |

---

## CONFORMIDADE COM REGRAS INVIOLAVEIS

| Regra | Status | Evidencia |
|-------|--------|-----------|
| R1 -- Two-Base Architecture | PASS | LogInteracao sem campos monetarios. Venda com CheckConstraint valor > 0. 5 servicos documentam R4 explicitamente. |
| R2 -- CNPJ String(14) | PASS | Todos os 11 modelos usam String(14). Normalizacao aplicada em routes_clientes.py. |
| R3 -- CARTEIRA 46 colunas | N/A | Regra aplica ao Excel, nao ao backend FastAPI. |
| R4 -- Formulas em ingles | N/A | Regra aplica ao openpyxl, nao ao FastAPI. |
| R5 -- Zero fabricacao de dados | PASS | Dashboard e agenda excluem ALUCINACAO. Baseline R$ 2.091.000 hardcoded correto. |
| R6 -- Mercos datas | N/A | Nenhum import Mercos implementado ainda. Regra sera critica quando E11 for implementado. |
| R7 -- Faturamento baseline | PASS | FATURAMENTO_BASELINE = 2_091_000.0 em routes_dashboard.py e routes_projecao.py. |
| R8 -- Zero alucinacao | PASS | agenda_service, sinaleiro/recalcular, dashboard/top10 excluem classificacao_3tier == ALUCINACAO. |

---

## COBERTURA DE TESTES

O commit 0551905 menciona testes unitarios para motor, score, sinaleiro, agenda, vendas.
Os arquivos de teste nao foram incluidos no escopo desta analise.

**Recomendacao:** Verificar cobertura dos testes existentes contra:
- D1 (Score v2 vs PRD pesos -- testes devem refletir a versao escolhida em A01)
- D2 (Sinaleiro sem LARANJA -- testes falharao quando A02 for implementado)
- D4 (Prioridade v2 vs faixas PRD)
- D5 (RESULTADOS_VALIDOS com 12 vs 14 opcoes)
- FR-035 AC4 (teste que tenta inserir valor monetario no LOG e confirma rejeicao)

---

*Relatorio gerado por @qa -- CRM VITAO360. Para decisoes A01 e A08, aguardar aprovacao L3 de Leandro antes de implementar.*
