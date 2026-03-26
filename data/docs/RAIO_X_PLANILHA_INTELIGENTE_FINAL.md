# Raio-X Completo — CRM_VITAO360 INTELIGENTE FINAL OK.xlsx

**Gerado:** 2026-03-25
**Fonte:** `"C:\Users\User\OneDrive\Area de Trabalho\CRM_VITAO360  INTELIGENTE   FINAL OK .xlsx"`
**Tamanho:** 5.8 MB | 40 abas (16 visiveis + 24 ocultas)
**Proposito:** Fonte de verdade para o UX Design do SaaS — cada aba sera uma tela/modulo

---

## MAPA COMPLETO DAS 40 ABAS

### ABAS VISIVEIS (16) — Interface do Usuario

| # | Aba | Rows x Cols | Funcao no SaaS | Epico PRD |
|---|-----|-------------|----------------|-----------|
| 15 | **OPERACIONAL** | 663 x 23 | Visao operacional por cliente: CNPJ, Semaforo, Faturamento, Rede, Consultor, Classificacao | E6 CARTEIRA |
| 16 | **PROJECAO** | 662 x 80 | Meta SAP vs Realizado por mes, Sinaleiro Rede, % Atingimento, Indicadores | E13 PROJECAO |
| 17 | **RESUMO META** | 23 x 17 | KPIs consolidados por consultor: Meta, Realizado, Gap, Status | E5 DASHBOARD |
| 18 | **PAINEL SINALEIRO** | 55 x 14 | Painel resumo do Sinaleiro com distribuicao por cor | E5 DASHBOARD |
| 19 | **SINALEIRO** | 665 x 26 | Sinaleiro por cliente: Meta, Real, % Ating, Gap, Cor, Maturidade, Acao, Grupo Chave | E3 SCORE+SINALEIRO |
| 21 | **DRAFT 1** | 566 x 60 | Dados Mercos brutos: Identidade, Compras, E-commerce, Vendas mes a mes | E1 IMPORT |
| 22 | **DRAFT 2** | 1001 x 40 | Log de atendimentos com TODAS as dimensoes do Motor | E7 LOG |
| 23 | **DRAFT 3** | 1542 x 18 | Historico condensado | E7 LOG |
| 24 | **CARTEIRA** | 1593 x 144 | ABA MESTRE — 144 colunas em 7 blocos: Mercos, Vendas 2025, Vendas 2026, Recorrencia, Funil, SAP, Metas | E6 CARTEIRA |
| 25 | **RNC** | 1503 x 15 | Registro Nao-Conformidade: tipo problema, area responsavel, status, SLA | E14 RNC |
| 26 | **AGENDA** | 670 x 18 | Agenda diaria priorizada por Score: Consultor, Score, Sinaleiro, Temperatura, Fase, Prox Acao | E4 AGENDA |
| 27 | **LARISSA** | 1767 x 40 | LOG da Larissa: 40 colunas de atendimento com Motor completo | E7 LOG |
| 28 | **MANU** | 1767 x 40 | LOG da Manu: mesmo layout | E7 LOG |
| 29 | **JULIO** | 1765 x 40 | LOG do Julio: mesmo layout | E7 LOG |
| 30 | **DAIANE** | 1765 x 40 | LOG da Daiane: mesmo layout | E7 LOG |
| 36 | **MANUAL ATENDIMENTO** | 381 x 6 | Guia operacional: Tipo Atendimento, Resultado tipico, Tarefa, Tipo Acao | Documentacao |

### ABAS OCULTAS (24) — Motor de Inteligencia

| # | Aba | Rows x Cols | Funcao | Epico PRD |
|---|-----|-------------|--------|-----------|
| 1 | **CHECKLIST MOTOR (2)** | 100 x 16 | 92 regras com checklist de validacao (OK/NOK por dimensao) + coluna COMENTARIO LEANDRO | E2 MOTOR |
| 2 | **CHECKLIST REGRAS (2)** | 28 x 7 | Validacao das regras de dropdown | E2 MOTOR |
| 3 | **GAPS MOTOR vs MANUAL (2)** | 49 x 6 | Gaps entre motor automatico e operacao manual | E2 MOTOR |
| 4 | **DECISOES PENDENTES (2)** | 30 x 8 | Decisoes L3 pendentes de Leandro | Governanca |
| 5 | **CHECKLIST MOTOR** | 100 x 16 | Versao anterior do checklist | E2 MOTOR |
| 6 | **CHECKLIST REGRAS** | 28 x 7 | Versao anterior | E2 MOTOR |
| 7 | **GAPS MOTOR vs MANUAL** | 49 x 6 | Versao anterior | E2 MOTOR |
| 8 | **DECISOES PENDENTES** | 30 x 8 | Versao anterior | Governanca |
| 9 | **ARQUITETURA 9 DIMENSOES** | 43 x 7 | CEREBRO: 9 dimensoes + Score ponderado + Prioridades P0-P7 + Desempate | E2+E3 MOTOR+SCORE |
| 10 | **ESTAGIOS DO FUNIL** | 27 x 7 | 14 estagios do Kanban com fluxo sequencial | E2 MOTOR |
| 11 | **FASES ESTRATEGICAS** | 12 x 7 | 6 fases do ciclo comercial | E2 MOTOR |
| 12 | **MAPA MOTOR NOVO** | 41 x 8 | 36 combinacoes (4 situacoes simplificadas x 9 resultados) — draft do motor | E2 MOTOR |
| 13 | **CRUZAMENTO MES A MES** | 550 x 85 | Cruzamento temporal de vendas | E1 IMPORT |
| 14 | **Venda Mes a Mes** | 571 x 71 | Vendas detalhadas por mes | E1 IMPORT |
| 20 | **OPERACIONAL_TEMP** | 663 x 23 | Copia temporaria do OPERACIONAL | Staging |
| 31 | **MOTOR DE REGRAS** | 96 x 12 | AS 92 COMBINACOES OFICIAIS v4 (7 SITUACOES x ~14 RESULTADOS = 92 regras) | E2 MOTOR |
| 32 | **REGRAS** | 496 x 13 | Todas as tabelas de lookup: Resultado, Tipo Contato, Motivo, Situacao, Fase, Tipo Cliente | E2 MOTOR |
| 33 | **README** | 602 x 7 | Documentacao interna da planilha | Documentacao |
| 34 | **STATUS** | 197 x 7 | Status tracking | Governanca |
| 35 | **DASHBOARD** | 54 x 14 | Dashboard Master: KPIs Macro, Sinaleiro por cor, Performance por Consultor | E5 DASHBOARD |
| 37 | **REGRAS VISUAL** | 532 x 9 | Regras com referencias de formulas Excel (XLOOKUP, named ranges) | E2 MOTOR |
| 38 | **Claude Log** | 540 x 6 | Log de sessoes Claude/ChatGPT | Historico |
| 39 | **REDES v2** | 307 x 12 | Sinaleiro por Rede/Franquia: lojas, fat, meta, gap, distribuicao por cor | E5 DASHBOARD |
| 40 | **AUDITORIA** | 97 x 8 | Auditoria forense completa: metricas, erros, links, CNPJs, validacao | QA |

---

## ARQUITETURA — AS 9 DIMENSOES (ABA 9)

O cerebro do CRM. Cada cliente tem 9 dimensoes calculadas:

| # | Dimensao | Quem Preenche | Valores |
|---|----------|---------------|---------|
| 1 | **SITUACAO** | Mercos (automatico) | ATIVO, EM RISCO, INAT.REC, INAT.ANT, PROSPECT, LEAD, NOVO |
| 2 | **ESTAGIO FUNIL** | Motor sugere + Consultor move | 14 estagios (Inicio→Tentativa→Prospeccao→...→Nutricao) |
| 3 | **RESULTADO** | Consultor (dropdown) | VENDA, ORCAMENTO, EM ATENDIMENTO, POS-VENDA, CS, RELACIONAMENTO, FU7, FU15, SUPORTE, NAO ATENDE, NAO RESPONDE, RECUSOU, CADASTRO, PERDA |
| 4 | **TIPO CLIENTE** | Motor calcula | PROSPECT, LEAD, NOVO, EM_DESENV, RECORRENTE, FIDELIZADO, MADURO |
| 5 | **FASE** | Motor gera (SITUACAO x TIPO) | PROSPECCAO, NEGOCIACAO, RECOMPRA, SALVAMENTO, RECUPERACAO, NUTRICAO |
| 6 | **CURVA ABC** | Motor calcula (faturamento) | A (top 20%), B (prox 30%), C (restante 50%) |
| 7 | **TEMPERATURA** | Motor gera (RESULTADO) | QUENTE, MORNO, FRIO, CRITICO, PERDIDO |
| 8 | **SINALEIRO** | Motor calcula | VERDE (<=0.5x ciclo), AMARELO (<=1x), VERMELHO (>1x), ROXO (sem historico) |
| 9 | **TENTATIVAS** | Motor incrementa | T1, T2, T3, T4, NUTRICAO. Reset apos VENDA |

### Output: SCORE PONDERADO → PRIORIDADE P0-P7

| Dimensao | Peso | Escala |
|----------|------|--------|
| FASE | 25% | RECOMPRA(100) > NEGOCIACAO(80) > SALVAMENTO(60) > RECUPERACAO(40) > PROSPECCAO(30) > NUTRICAO(10) |
| SINALEIRO | 20% | VERMELHO(100) > AMARELO(60) > VERDE(30) > ROXO(0) |
| CURVA ABC | 20% | A(100) > B(60) > C(30) |
| TEMPERATURA | 15% | QUENTE(100) > MORNO(60) > FRIO(30) > CRITICO(20) > PERDIDO(0) |
| TIPO CLIENTE | 10% | MADURO(100) > FIDELIZADO(85) > RECORRENTE(70) > EM_DESENV(50) > NOVO(30) > LEAD(15) > PROSPECT(10) |
| TENTATIVAS | 10% | T1(100) > T2(70) > T3(40) > T4(10) > NUTRICAO(5) |

### Prioridades

| Prioridade | Label | Score | Distribuicao/dia | Regra |
|-----------|-------|-------|-----------------|-------|
| **P0** | IMEDIATA | N/A | Pula fila | SUPORTE com problema aberto |
| **P1** | URGENTE | N/A | Ate 15/dia | EM ATENDIMENTO + follow-up vencido |
| **P2** | ALTA | 80-100 | 15-20/dia | Top da lista apos bloqueios |
| **P3** | MEDIA-ALTA | 60-79 | 15-20/dia | Segundo bloco |
| **P4** | MEDIA | 45-59 | 5-10/dia | Corpo da agenda |
| **P5** | MEDIA-BAIXA | 30-44 | 5-10/dia | Se sobrar tempo |
| **P6** | BAIXA | 15-29 | 0-5/dia | Ultima prioridade |
| **P7** | NUTRICAO | 0-14 | 0 (campanha) | Nunca entra nos 40/dia |

### Desempate (quando score empata)
1. CURVA ABC (A primeiro)
2. TICKET MEDIO (maior primeiro)
3. TIPO CLIENTE (mais maduro primeiro)
4. FOLLOW-UP mais vencido primeiro

### Meta Balance
Se P2-P5 nao cobrem 80% da meta mensal, PROSPECCAO ganha +20 pontos bonus.

---

## MOTOR DE REGRAS v4 — 92 COMBINACOES (ABA 31)

**7 SITUACOES x ~14 RESULTADOS = 92 regras**

Cada combinacao (SITUACAO, RESULTADO) gera automaticamente 9 outputs:
1. ESTAGIO FUNIL
2. FASE
3. TIPO CONTATO
4. ACAO FUTURA (texto prescritivo)
5. TEMPERATURA
6. FOLLOW-UP (dias)
7. GRUPO DASH
8. TIPO ACAO
9. CHAVE (concatenacao SITUACAO|RESULTADO)

### Distribuicao por SITUACAO

| SITUACAO | Regras | Threshold | Estagios gerados |
|----------|--------|-----------|-----------------|
| ATIVO | 14 | dias_sem_compra <= 50 | POS-VENDA, ORCAMENTO, EM ATENDIMENTO, CS/RECOMPRA, NAO ATENDE/RESPONDE, PERDA |
| EM RISCO | 13 | dias 51-60 | POS-VENDA, ORCAMENTO, EM ATENDIMENTO, PERDA |
| INAT.REC | 14 | dias 61-90 | REATIVACAO + todos acima |
| INAT.ANT | 14 | dias > 90 | RESGATE + todos acima |
| PROSPECT | 12 | n_compras = 0 | PROSPECCAO, ORCAMENTO, POS-VENDA |
| LEAD | 12 | lead qualificado | PROSPECCAO, ORCAMENTO, POS-VENDA |
| NOVO | 13 | primeiro pedido recente | POS-VENDA, EM ATENDIMENTO, CS/RECOMPRA |

---

## 14 ESTAGIOS DO FUNIL — Kanban (ABA 10)

### Jornada Pre-Venda
1. **INICIO CONTATO** → Primeiro contato
2. **TENTATIVA** → T1-T4 em andamento
3. **PROSPECCAO** → Nao respondeu, continuamos

### Jornada Venda
4. **EM ATENDIMENTO** → Respondeu, conversa ativa
5. **CADASTRO** → Fazendo cadastro
6. **ORCAMENTO** → Proposta enviada
7. **PEDIDO** → Venda fechada (MARCO)

### Jornada Pos-Venda
8. **ACOMP POS-VENDA** → D+4: faturou? saiu da expedicao?
9. **POS-VENDA** → D+15: recebeu? chegou bem?
10. **CS** → D+30: tentativa de recompra

### Loop Follow-Up
11. **FOLLOW-UP** → D+15 ou D+30 apos CS

### Auxiliares
12. **SUPORTE** → Problema a resolver
13. **RELACIONAMENTO** → Manutencao de ativo
14. **NUTRICAO** → T4+ sem resposta, campanha mensal

### Fluxo Sequencial
```
PRE-VENDA: INICIO → TENTATIVA → PROSPECCAO → EM ATENDIMENTO
VENDA:     EM ATENDIMENTO → CADASTRO → ORCAMENTO → PEDIDO
POS-VENDA: PEDIDO → ACOMP D+4 → POS-VENDA D+15 → CS D+30
LOOP:      CS nao vendeu → FOLLOW-UP D+15/D+30 → repete
RESET:     Qualquer estagio + VENDA → volta para POS-VENDA
```

---

## 6 FASES ESTRATEGICAS (ABA 11)

| # | Fase | Descricao | Score Base | Situacao Tipica |
|---|------|-----------|-----------|-----------------|
| 1 | **PROSPECCAO** | Nunca comprou, tentando conquistar | 30 | PROSPECT + T1-T4 |
| 2 | **NEGOCIACAO** | Ativo, em conversa, namoro novo | 80 | ATIVO + EM ATENDIMENTO/ORCAMENTO |
| 3 | **RECOMPRA** | Ativo, no ciclo. CULTIVAR e prioridade | 100 | RECORRENTE/FIDELIZADO + SINALEIRO VERDE/AMARELO |
| 4 | **SALVAMENTO** | Inativo recente, salvar antes que piore | 60 | INAT.REC |
| 5 | **RECUPERACAO** | Inativo antigo, trazer de volta | 40 | INAT.ANT |
| 6 | **NUTRICAO** | Esgotou tentativas, campanha 1x/mes | 10 | Qualquer + nao respondeu |

**Filosofia:** CULTIVAR (recompra) > SALVAR (inativos recentes) > CONQUISTAR (prospects)

---

## CARTEIRA — 144 COLUNAS EM 7 BLOCOS (ABA 24)

### Bloco 1: MERCOS — Identidade (cols 1-27)
- ANCORA (nome fantasia)
- IDENTIDADE: CNPJ, Razao Social, UF, Cidade, Email, Telefone, Data Cadastro
- REDE: Rede Regional, Ult Registro Mercos
- EQUIPE: Consultor, Vendedor Ultimo Pedido
- STATUS: Situacao, Prioridade
- COMPRA: Dias Sem Compra, Data Ultimo Pedido, Valor Ultimo Pedido, Ciclo Medio
- ECOMMERCE: Acesso B2B, Acessos Portal, Itens Carrinho, Valor B2B, Oportunidade
- ATENDIMENTO MERCOS: Tipo Contato, Resultado, Motivo, Descricao

### Bloco 2: VENDAS 2025 (cols 28-40)
- TOTAL 2025 + 12 meses (jan-dez 2025)

### Bloco 3: VENDAS 2026 (cols 41-53)
- TOTAL 2026 + 12 meses (jan-dez 2026)

### Bloco 4: RECORRENCIA (cols 54-61)
- TICKET MEDIO, TIPO CLIENTE, N COMPRAS, CURVA ABC, MESES POSITIVADO, MEDIA MENSAL, MESES LISTA

### Bloco 5: FUNIL (cols 62-80)
- ANCORA (ancora funil)
- PIPELINE: Estagio Funil, Prox Follow-up, Data Ult Atendimento, Acao Futura, Ultimo Resultado, Motivo
- PERFIL: Tipo Cliente, Tentativa
- MATURIDADE: Fase, Ultima Recompra
- CONVERSAO: Temperatura, Dias Ate Conversao, Data 1o Contato, Data 1o Orcamento, Data 1a Venda, Total Tentativas
- ACAO: Prox Acao, Acao Detalhada
- SINAL: Sinaleiro

### Bloco 6: SAP (cols 81-95)
- CODIGO DO CLIENTE, CNPJ, RAZAO SOCIAL
- STATUS SAP: Cadastro, Atendimento, Bloqueio
- DADOS CADASTRAIS: Grupo Cliente, Gerente Nacional, Representante, Vend Interno, Canal, Tipo Cliente, Macroregiao, Microregiao, Grupo Chave

### Bloco 7: METAS + SCORE (cols 96-144)
- ANUAL: Meta, Realizado, % Alcancado
- Q1: Meta SAP Tri, Meta Igualitaria Tri, % Alcancado Tri
- JANEIRO: Meta SAP, Meta Igualitaria, Data Pedido, Justificativa (Sem 1-5), Realizado, % SAP
- FEVEREIRO: idem
- MARCO: idem
- Q1 ANCORA: Realizado Tri, % Tri SAP
- SCORE & PRIORIDADE v2: Urgencia(30%), Valor(25%), Follow-up(20%), Sinal(15%), Tentativa(5%), Situacao(5%), Score, Prioridade v2

**NOTA:** A CARTEIRA tem um Score alternativo v2 nas ultimas colunas com pesos DIFERENTES do Score oficial da aba ARQUITETURA 9 DIMENSOES. O Score oficial usa: FASE(25%), SINALEIRO(20%), ABC(20%), TEMPERATURA(15%), TIPO_CLIENTE(10%), TENTATIVAS(10%).

---

## LOG DOS CONSULTORES — 40 COLUNAS (ABAS 27-30)

Layout identico para LARISSA, MANU, JULIO, DAIANE:

| # | Coluna | Tipo |
|---|--------|------|
| 1 | DATA | datetime |
| 2 | CONSULTOR | text |
| 3 | NOME FANTASIA | text |
| 4 | CNPJ | text |
| 5 | UF | text |
| 6 | REDE / REGIONAL | text |
| 7 | DIAS SEM COMPRA | number |
| 8 | SITUACAO | dropdown |
| 9 | ESTAGIO FUNIL | Motor |
| 10 | TIPO CLIENTE | Motor |
| 11 | FASE | Motor |
| 12 | TEMPERATURA | Motor |
| 13 | SINALEIRO | Motor |
| 14 | PROX. ACAO | Motor |
| 15 | TENTATIVA | Motor |
| 16 | TIPO ATENDIMENTO | dropdown (ATIVO/RECEPTIVO) |
| 17 | WHATSAPP | boolean |
| 18 | LIGACAO | boolean |
| 19 | LIGACAO ATENDIDA | boolean |
| 20 | TIPO DO CONTATO | dropdown |
| 21 | RESULTADO | dropdown (14 opcoes) |
| 22 | MOTIVO | dropdown |
| 23 | FOLLOW-UP | dias |
| 24 | ACAO SUGERIDA | Motor |
| 25 | ACAO FUTURA | Motor |
| 26 | ACAO DETALHADA | Motor |
| 27 | MERCOS ATUALIZADO | boolean |
| 28 | NOTA DO DIA | text |
| 29 | TIPO ACAO | Motor |
| 30 | TIPO PROBLEMA | dropdown (RNC) |
| 31 | TAREFA/DEMANDA | text |
| 32 | SCORE | number |
| 33 | PRIORIDADE | text (P0-P7) |
| 34 | CICLO | number |
| 35 | CURVA | A/B/C |
| 36 | CARRINHO | number |
| 37 | RANKING | number |
| 38-40 | (vazios) | — |

### Two-Base Architecture ENFORCED
- Nenhum campo monetario no LOG (R$ 0.00 sempre)
- Vendas = registradas na CARTEIRA (bloco VENDAS)
- LOG = append-only (imutavel)

---

## DASHBOARD MASTER (ABA 35)

3 blocos:
1. **KPIs MACRO**: Fat Realizado R$2.101.741, Meta 2026 R$4.747.200, Realizado 2026 R$118.735, % Atingimento 35.6%
2. **SINALEIRO**: VERDE 134 (20.3%), AMARELO 63 (9.5%), VERMELHO 299 (45.2%), ROXO 165 (25.0%)
3. **PERFORMANCE POR CONSULTOR**:

| Consultor | Territorio | Clientes | Fat Real | Meta 2026 | % Ating | Status |
|-----------|-----------|----------|----------|-----------|---------|--------|
| MANU | SC/PR/RS | 165 | R$777.656 | R$926.557 | 83.9% | BOM |
| LARISSA | Brasil sem rede | 222 | R$964.073 | R$1.246.641 | 77.3% | BOM |
| DAIANE | Redes/Franquias | 164 | R$210.316 | R$1.400.219 | 15.0% | CRITICO |
| JULIO | Cia Saude+Fitland | 110 | R$149.695 | R$1.188.181 | 12.6% | CRITICO |
| **TOTAL** | — | **661** | **R$2.101.741** | **R$4.761.598** | **44.1%** | — |

---

## SINALEIRO DE REDES (ABA 39)

| Rede | Consultor | Lojas | Fat Real | Meta | % Ating | Gap | Distribuicao Cor |
|------|-----------|-------|----------|------|---------|-----|-----------------|
| FITLAND | JULIO | 58 | R$129.989 | R$621.000 | 20.9% | -R$491K | 5V 4A 35Vm 14Rx |
| CIA DA SAUDE | JULIO | 72 | R$36.465 | R$783.000 | 4.7% | -R$746K | 1V 0A 18Vm 53Rx |

---

## MAPEAMENTO ABA → TELA SaaS

| Aba Excel | Tela SaaS | Rota API | Notas |
|-----------|-----------|----------|-------|
| CARTEIRA (144 cols) | `/clientes` — tabela filtrada | GET /api/clientes | Dividir em blocos colapsaveis |
| CARTEIRA detalhe | `/clientes/{cnpj}` — modal | GET /api/clientes/{cnpj} | Todos os 7 blocos |
| AGENDA | `/agenda` — lista priorizada | GET /api/agenda/{consultor} | Cards com Score + Sinaleiro |
| LARISSA/MANU/JULIO/DAIANE | `/atendimentos` — timeline | GET /api/atendimentos | Unificar 4 abas em 1 com filtro consultor |
| DRAFT 2 | Mesmo que atendimentos | — | Historico (append-only) |
| DASHBOARD | `/dashboard` — KPIs | GET /api/dashboard/kpis | 3 blocos: KPIs, Sinaleiro, Performance |
| SINALEIRO | `/sinaleiro` — lista | GET /api/clientes?with_sinaleiro | Cores por cor |
| PROJECAO | `/projecao` — metas | GET /api/projecao | Meta vs Real por mes |
| RESUMO META | Widget no Dashboard | — | Cards consolidados |
| PAINEL SINALEIRO | Widget no Dashboard | — | Donut chart por cor |
| REDES v2 | `/redes` — painel redes | GET /api/redes | Tabela por rede/franquia |
| RNC | `/rnc` — registro problemas | GET /api/rnc | CRUD com SLA tracking |
| OPERACIONAL | Merge com CARTEIRA | — | Dados ja estao na CARTEIRA |
| MOTOR DE REGRAS | `/admin/motor` — read-only | GET /api/motor/regras | 92 combinacoes |
| REGRAS | Embedded nos dropdowns | — | Alimenta dropdowns do LOG |
| MANUAL ATENDIMENTO | `/ajuda` — inline | — | Tooltips + modal de ajuda |

---

## AUDITORIA (ABA 40) — Estado Atual

| Metrica | Valor | Status |
|---------|-------|--------|
| Total abas | 40 (16+24) | OK |
| Erros formula | 2 (#VALUE! em REGRAS VISUAL) | ATENCAO |
| Links externos | 0 (3.986 corrigidos) | OK |
| Clientes CARTEIRA | 1.581 (9 CNPJs vazios + 1 em branco) | OK |
| CNPJ formato CARTEIRA | 100% numerico 14 digitos | OK |
| CNPJ formato OPERACIONAL | com pontos/tracos | RISCO |
| CNPJ formato PROJECAO | sem zeros a esquerda | RISCO |
| Clientes SINALEIRO | 661 | OK |
| Meta anual 2026 | R$4.747.200 | OK |
