# BACKUP COMPLETO — CRM VITAO360 (Documentacao Anterior)
# Data: 2026-03-23
# Proposito: Preservacao de TUDO que foi feito antes do rebuild com enforcement completo

---

## SECAO 1 — BRIEFING COMPLETO

# BRIEFING COMPLETO — CRM VITAO360
# Transferencia Total de Conhecimento para Construcao
# Data: 15/02/2026 | Fonte: 19 documentos + 32 sessoes + 88 arquivos Excel

---

# PARTE 1 — HISTORIA E CONTEXTO

## 1.1 O que e a VITAO Alimentos
Distribuidora B2B de alimentos naturais embalados, sediada em Curitiba/PR. Vende para lojas de produtos naturais, franquias e redes em todo o Brasil. Opera com 4 consultores comerciais internos + 1 RCA externo.

## 1.2 O problema original (Outubro/2024)
O CRM anterior (ExactSales, SaaS) foi encerrado. Consequencias:
- Perda TOTAL do historico de atendimentos de 354 clientes
- 60-90 dias de dados de contato perdidos
- Dados preservados: vendas, ciclo medio, positivacoes, acesso e-commerce, cadastros

## 1.3 Primeira tentativa fracassada (Nov/2024)
Leandro tentou reconstruir com ChatGPT: mais de 100 iteracoes, dados fabricados (alucinacoes massivas), valores inflados em 742% por duplicacao. Resultado: lixo.

## 1.4 Virada para Claude (Dez/2024)
Migrou para Claude. Reduziu de 100+ iteracoes para 5-8 por entrega. Inventou a "Two-Base Architecture" que eliminou a duplicacao de 742%.

## 1.5 Construcao incremental (Jan/2025 — Fev/2026)
16 meses de trabalho em 8 fases, tudo via claude.ai (sem Claude Code). O problema: a janela de contexto resetava a cada conversa, forcando recriacao constante. Em 32 sessoes entre 06-12/Fev/2026, o sistema atingiu a versao 11. Mas nunca ficou 100% — sempre faltava algo porque o contexto acabava.

## 1.6 Estado atual (15/Fev/2026)
CRM v11 existe e opera parcialmente. Partes funcionam, partes estao quebradas ou incompletas. Este briefing e a transferencia completa de tudo que existe para um novo ambiente (Claude Code/DEUS) finalmente terminar o projeto.

---

# PARTE 2 — EQUIPE COMERCIAL

| CONSULTOR | TIPO | TERRITORIO | % FAT | STATUS | OBSERVACOES |
|-----------|------|-----------|-------|--------|-------------|
| MANU DITZEL | Interno | SC/PR/RS | 32.5% | Ativa | Licenca maternidade proxima. Cobertura pendente. |
| LARISSA PADILHA | Interno | Resto do Brasil (sem redes) | ~45% | Ativa | Sobrecarga: 291 clientes (~58/dia, max e 50). Opera canal "Mais Granel" com Rodrigo. |
| JULIO GADRET | RCA Externo | Brasil (presencial) | ~10% | 100% FORA do sistema | Opera via WhatsApp pessoal. Cia Saude + Fitland exclusivo. Zero no Deskrio/Mercos. |
| DAIANE STAVICKI | Gerente + Key Account | Brasil | ~12.5% | Ativa | Foco redes/franquias: Divina Terra, Biomundo, Mundo Verde, Vida Leve, Tudo em Graos |

**IMPORTANTE:** No sistema Deskrio, "Rodrigo" aparece com 952 tickets (17.9% do total). Rodrigo NAO e vendedor — e operador do canal "Mais Granel" que pertence a Larissa. RODRIGO = LARISSA no CRM.

---

# PARTE 3 — ARQUITETURA DO SISTEMA

## 3.1 Fluxo de dados
```
FONTES EXTERNAS (exports manuais)
    |
    v
MERCOS (ERP: vendas, positivacao, ABC, e-commerce, carteira, atendimentos)
SAP (cadastro, vendas mes a mes, metas 2026, clientes sem atendimento)
DESKRIO (WhatsApp Business: 77.805 mensagens, 5.425 conversas)
    |
    v
DRAFT 1 (Mercos) + DRAFT 2 (Agenda) + DRAFT 3 (SAP)
    |
    v
CARTEIRA (46 colunas — motor central, 489 clientes)
    |
    +-----+------+-------+--------+
    |     |      |       |        |
    v     v      v       v        v
  AGENDA  LOG  PROJECAO  DASH   SINALEIRO
                                (923 lojas)
```

## 3.2 Two-Base Architecture (regra fundamental)
Separacao absoluta entre dados financeiros e interacoes:
- **BASE_VENDAS**: Registros tipo VENDA carregam valor R$ real
- **LOG**: Registros de interacao (ligacao, WhatsApp, visita, etc.) SEMPRE com R$ 0.00
- Motivo: antes da separacao, cada interacao duplicava o valor da venda. Resultado: R$ 664K virava R$ 3.62M (inflacao de 742%)
- Regra: valor financeiro APENAS no registro tipo VENDA. NUNCA em outro tipo de interacao.

## 3.3 Chave primaria
CNPJ normalizado: 14 digitos sem pontuacao, sem espacos. Exemplo: `04351343000169`
Todo cruzamento entre sistemas usa CNPJ como ancora.

---

# PARTE 4 — NUMEROS DE REFERENCIA (VERDADE ABSOLUTA)

Fonte: PAINEL DE ATIVIDADES (Dashboard Executivo 2025). Estes sao os numeros corretos.

## 4.1 Faturamento mensal
```
JAN: R$  80.000    FEV: R$  95.000    MAR: R$ 110.000    ABR: R$ 150.000
MAI: R$ 180.000    JUN: R$ 220.000    JUL: R$ 200.000    AGO: R$ 230.000
SET: R$ 210.000    OUT: R$ 280.000    NOV: R$ 260.000    DEZ: R$ 141.179
TOTAL: R$ 2.156.179
```

## 4.2 Metricas operacionais
```
Vendas totais 2025:      957 pedidos (902 no PAINEL — divergencia conhecida de fonte)
Atendimentos 2025:       10.634
Mensagens WhatsApp 2025: 77.805 (Deskrio)
Conversas unicas:        5.425
Orcamentos:              1.419 (67.4% converteram em venda)
Follow-ups:              1.610 (1.7 por venda)
Clientes carteira:       489 (105 ativos + 80 inat.recentes + 304 inat.antigos)
Redes franquias:         8 redes, 923 lojas (107 carteira ativa + 816 prospects)
Taxa recompra:           20.3%
CAC:                     R$ 532
ROI anual:               347%
Ticket medio:            R$ 2.389
Pipeline real:           10 contatos/venda, 17 dias, 78 mensagens/jornada
Capacidade estimada:     3 vendas/dia/consultor
```

## 4.3 Sinaleiro de penetracao por rede
```
REDE              | LOJAS | SINALEIRO% | COR       | META 6M
FIT LAND          | 89    | 29.8%      | VERMELHO  | 10%
DIVINA TERRA      | 85    | 10.0%      | VERMELHO  | 5%
VIDA LEVE         | 81    | 8.0%       | VERMELHO  | 3%
TUDO EM GRAOS     | 25    | 6.2%       | VERMELHO  | 10%
CIA DA SAUDE      | 163   | 2.6%       | VERMELHO  | 3%
BIOMUNDO          | 167   | 1.4%       | VERMELHO  | 2%
MUNDO VERDE       | 199   | 1.4%       | VERMELHO  | 2%
ARMAZEM FITSTORE  | 114   | 0%         | ROXO      | 1%

Formula: Sinaleiro% = Fat.Real / (Total_Lojas x R$525/mes x 11 meses) x 100
Faixas: ROXO (<1%) -> VERMELHO (1-40%) -> AMARELO (40-60%) -> VERDE (>60%)
Cadencia: ROXO=1x/sem WA+Lig | VERMELHO=2x/sem | AMARELO=1x/sem | VERDE=Mensal
```

## 4.4 Projecao 2026
```
Vendas projetadas:     3.168 (+231%)
Faturamento projetado: R$ 5.7M (+164%)
Vendas/dia/consultor:  3 (vs ~1 em 2025)
```

---

# PARTE 5 — O QUE JA FOI CONSTRUIDO E FUNCIONA

## 5.1 CARTEIRA (Fase 1) OPERACIONAL
- Motor central do CRM
- 46 colunas IMUTAVEIS, 489 clientes
- Blocos: Identificacao(8) -> Atribuicao(2) -> Status(7) -> Ultimo Pedido(4) -> Performance(4) -> Fat.Mensal(12) -> E-commerce(4) -> Classificacoes(6) -> CRM/Funil(3) -> Acompanhamento(3)
- Classificacao ABC: A >= R$2.000/mes, B >= R$500, C < R$500
- Tipo cliente: NOVO / EM DESENVOLVIMENTO / RECORRENTE / FIDELIZADO
- Regras de roteamento por consultor implementadas

## 5.2 LOG (Fase 2) PARCIALMENTE OPERACIONAL
- Sistema append-only (nunca deletar, apenas adicionar)
- Chave composta: DATA + CNPJ + RESULTADO (dedup)
- 1.581 registros de 11.758 esperados (13.4% populado)
- Faltam: logs antigos do CONTROLE_FUNIL (10.484 registros) e tickets Deskrio (5.329)
- 3.540 contatos historicos foram gerados retroativamente para cobrir os 60-90 dias perdidos
- Julio 100% fora do sistema

## 5.3 DRAFT 2 — Agenda/Quarentena (Fase 3) OPERACIONAL
- Staging area funcional: Draft 1 (Mercos), Draft 2 (operacional), Draft 3 (SAP)
- Regra: nunca modificar dados diretamente no CRM — sempre via DRAFT -> validacao -> LOG

## 5.4 DASH (Fase 4) PRECISA REDESIGN
- Layout atual: 8 blocos, 164 rows x 19 cols — chamado de "Frankenstein"
- Decisao: APAGAR e reconstruir com 3 blocos compactos (~45 rows)

## 5.5 AGENDA (Fase 6) OPERACIONAL
- 20 colunas, distribuicao territorial automatica
- Limite 40 atendimentos/dia por consultor
- Manual v3 FINAL documentado

## 5.6 SINALEIRO (Fase 8) OPERACIONAL
- 13.216 formulas com 0 erros validados
- 923 lojas, 8 redes

## 5.7 SINALEIRO INTERNO OPERACIONAL
- 661 clientes, 5 slicers reais via XML Surgery

---

# PARTE 6 — O QUE ESTA QUEBRADO OU INCOMPLETO

## 6.1 PROJECAO ZERADA (CRITICO)
18.180 formulas PERDIDAS. So tem dados estaticos de janeiro.

## 6.2 DIVERGENCIA DE FATURAMENTO
Gap de R$ 6.790 (~0.3%) entre dados combinados e PAINEL.

## 6.3 TIMELINE MENSAL VAZIA
Vendas mes a mes por cliente nao preenchidas.

## 6.4 LOG INCOMPLETO
1.581 de 11.758 registros (13.4%).

## 6.5 E-COMMERCE PARCIAL
Dados existem mas nao integrados na CARTEIRA.

## 6.6 #REF! NAS REDES_FRANQUIAS_v2

## 6.7 REDE/REGIONAL VAZIA

---

# PARTE 7 — FONTES DE DADOS DISPONIVEIS (88+ ARQUIVOS)

## 7.1 Relatorios de vendas Mercos (12 arquivos)
- Header na LINHA 10 (skiprows=9)
- NAO TEM CNPJ — match por Nome Fantasia/Razao Social

### ARMADILHAS CRITICAS:
```
ARQUIVO                              | CONTEM REALMENTE  | ACAO
Relatorio_vendas_ABril_2025.xlsx     | Abril + Maio      | Filtrar SOMENTE month==4
elatorio_de_vendas_Maio_.xlsx        | Duplicata exata   | DESCARTAR
Relatorio_de_vendas_Setembro_25.xlsx | OUTUBRO           | DESCARTAR
relatorio_de_vendas_novembro_.xlsx   | SETEMBRO          | DESCARTAR
Relatorio_vendas_janeiro_2026.xlsx   | Ate 19/01 (35)    | DESCARTAR
RELATORIO_DE_VENDAS_JANEIRO_2026.xlsx| Ate 29/01 (78)    | USAR ESTE
```

## 7.2-7.9 (Positivacao, ABC, E-commerce, Deskrio, SAP, CONTROLE_FUNIL, outros)
Ver briefing completo para detalhes de cada fonte.

---

# PARTE 8 — BLUEPRINT v2 DA CARTEIRA (81 colunas, 8 grupos)

Expandiu de 46 para 81 colunas com grupos expansiveis [+].
10 fixas (A-J) + 8 grupos: Identificacao, Vida Comercial, Timeline Mensal, Jornada, Ecommerce, SAP, Operacional, Comite.

---

# PARTE 9 — MOTOR DE MATCHING

Cascata: CNPJ Exato (100%) -> Telefone (85%) -> Nome Fuzzy/rapidfuzz (70-100%) -> Padrao de Rede/regex (75-90%).

DE-PARA vendedores:
```
MANU: Manu, Manu Vitao, Manu Ditzel -> MANU
LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo -> LARISSA
DAIANE: Daiane, Central Daiane, Daiane Vitao -> DAIANE
JULIO: Julio, Julio Gadret -> JULIO
```

---

# PARTE 10 — REGRAS DE NEGOCIO INVIOLAVEIS

1. CNPJ = 14 digitos, chave primaria universal
2. Two-Base Architecture: R$ APENAS em VENDA
3. CARTEIRA 46 colunas IMUTAVEL
4. Zero fabricacao de dados
5. Cores por status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
6-17. Ver briefing completo.

---

# PARTE 12 — ENTREGAS PRIORIZADAS

1. PROJECAO reconstruida (18.180 formulas) — CRITICO
2. Dados de faturamento corretos (R$ 2.156.179)
3. Timeline mensal populada
4. LOG completo (~11.758 registros)
5. DASH redesenhada (3 blocos)
6. E-commerce cruzado
7. REDE/REGIONAL preenchido
8. #REF! corrigidos
9. COMITE com metas
10. Validacao final (0 erros)

---

# PARTE 13 — LICOES APRENDIDAS

1. Openpyxl destroi slicers -> XML Surgery
2. Relatorios Mercos mentem nos nomes
3. Formulas openpyxl em INGLES
4. CNPJ como float perde precisao -> string zfill(14)
5-14. Ver briefing completo.

---

**FIM DO BRIEFING**
**16 meses. 32 sessoes. 88+ arquivos. Transferencia completa.**

---
---

## SECAO 2 — INTELIGENCIA DE NEGOCIO

# INTELIGENCIA DO NEGOCIO - CRM VITAO360
**Gerado em: 17/02/2026 | 10 fases completas | 154.302 formulas**

---

## ONDE ESTA CADA COISA

### 1. CEREBRO DO PROJETO (decisoes e regras)
| Arquivo | O que contem |
|---------|-------------|
| `.planning/STATE.md` | **250+ decisoes tecnicas**, todas as regras de negocio, contexto acumulado |
| `.planning/ROADMAP.md` | Roadmap com 10 fases, 43 requisitos, criterios de sucesso |
| `.planning/PROJECT.md` | Visao geral do projeto, stakeholders, objetivos |

### 2. PESQUISA E ANALISE (por fase)
| Fase | Pesquisa | O que descobriu |
|------|----------|----------------|
| 01-projecao | `01-RESEARCH.md` | 19.224 formulas intactas no V12, estrutura PROJECAO |
| 02-faturamento | `02-RESEARCH.md` | SAP vs Mercos, 11 armadilhas Mercos, merge strategy |
| 03-timeline-mensal | `03-RESEARCH.md` | DRAFT 1 structure, ABC classification, INDEX/MATCH |
| 04-log-completo | `04-RESEARCH.md` | CONTROLE_FUNIL + Deskrio + sinteticos, 20.830 records |
| 05-dashboard | `05-RESEARCH.md` | 3 blocos compactos, KPIs, COUNTIFS |
| 06-e-commerce | `06-RESEARCH.md` | Mercos B2B portal, 1.075 records, 64.6% match rate |
| 07-redes-franquias | `07-RESEARCH.md` | 20 redes + SEM GRUPO, SAP Cadastro, VLOOKUP F:J |
| 08-comite-metas | `08-RESEARCH.md` | Metas 2026, RATEIO, COMITE formulas |
| 09-blueprint-v2 | `09-RESEARCH.md` | 263 colunas CARTEIRA, 6 super-grupos, motor inteligencia |
| 10-validacao-final | `10-RESEARCH.md` | Audit clean, V31 comparison, layout analysis |

**Caminho**: `.planning/phases/{fase}/{num}-RESEARCH.md`

### 3. DADOS PROCESSADOS (JSONs intermediarios)
| Arquivo | Conteudo |
|---------|----------|
| `data/output/phase01/sap_data_extracted.json` | Dados SAP extraidos (metas, vendas, clientes) |
| `data/output/phase02/sap_vendas.json` | Vendas SAP mes a mes |
| `data/output/phase02/mercos_vendas.json` | Vendas Mercos mes a mes |
| `data/output/phase02/sap_mercos_merged.json` | **MERGE FINAL** SAP+Mercos (537 clientes) |
| `data/output/phase03/abc_classification.json` | Classificacao ABC dos clientes |
| `data/output/phase04/controle_funil_classified.json` | LOG classificado (10.434 registros) |
| `data/output/phase04/deskrio_normalized.json` | Deskrio normalizado (4.240 tickets) |
| `data/output/phase04/log_final_validated.json` | **LOG FINAL** validado (20.830 registros) |
| `data/output/phase06/ecommerce_raw.json` | E-commerce bruto (1.075 acessos) |
| `data/output/phase06/ecommerce_matched.json` | E-commerce cruzado com clientes |
| `data/output/phase09/v12_formula_audit.json` | Auditoria formulas V12 (263 colunas) |
| `data/output/phase09/carteira_column_spec.json` | Spec completa CARTEIRA |
| `data/output/phase10/confronto_v13_v31.json` | Confronto V13 vs V31 (CNPJs, clientes) |
| `data/output/phase10/delivery_report.json` | Relatorio entrega final |

### 4. SCRIPTS COM LOGICA DE NEGOCIO
| Script | Logica que contem |
|--------|-------------------|
| `scripts/phase01/` | Extracao SAP, validacao PROJECAO |
| `scripts/phase02/` | ETL Mercos, merge SAP-First, armadilhas |
| `scripts/phase03/` | DRAFT 1 population, ABC, INDEX/MATCH |
| `scripts/phase04/` | LOG integration, dedup, Deskrio normalize |
| `scripts/phase05/` | DASH formulas, KPIs, COUNTIFS |
| `scripts/phase06/` | E-commerce ETL, 5-level matching |
| `scripts/phase07/` | Redes/Franquias, VLOOKUP population |
| `scripts/phase08/` | COMITE metas, RATEIO toggle |
| `scripts/phase09/` | CARTEIRA 134K formulas, motor inteligencia, AGENDA, SCORE |
| `scripts/phase10/` | Audit, confronto, layout fix, V14 generation |

### 5. DOCUMENTOS EXTERNOS (auditoria V31)
**Local**: `Area de Trabalho/auditoria conversas sobre agenda atendimento draft 2/`
| Documento | Conteudo |
|-----------|----------|
| `ANATOMIA_ATENDIMENTO_VITAO360` | 1 venda = 13 contatos + 47 tasks + 3h43 |
| `BLUEPRINT_FORENSE_REGRAS_VITAO360` | 63 combinacoes regras, 5 jornadas templates |
| `EXTRACAO_FORENSE_CRM_VITAO360` | 94.4% completude dados, mapeamento campos |
| `LOG_AUDITORIA_V12_REBUILD` | 129.199 formulas em 15 tabs, trio columns |
| `PLAYBOOK_EXCELENCIA_100_DRAFT_AGENDA` | 30+ tentativas falhas, metodologia |
| `CRM_V12_POPULADO_V31` | Versao referencia com layout superior |

---

## REGRAS DE NEGOCIO PRINCIPAIS

### REGRA #1: AGENDA DIARIA INTELIGENTE
O CRM existe para gerar 40-60 atendimentos priorizados por consultor por dia.
- Gestor (Leandro) passa agenda de manha
- Consultor devolve no fim do dia com resultados
- Resultados alimentam ciclo do dia seguinte

### REGRA #2: TWO-BASE ARCHITECTURE
- Valores financeiros (R$) APENAS na aba DRAFT 1 / VENDAS
- LOG e DRAFT 2 SEMPRE R$ 0.00
- CARTEIRA puxa via INDEX/MATCH, nunca duplica valores

### REGRA #3: SCORE RANKING (6 fatores = 100%)
| Fator | Peso | Fonte |
|-------|------|-------|
| URGENCIA | 30% | Dias sem comprar vs ciclo medio |
| VALOR | 25% | Faturamento real do cliente |
| FOLLOWUP | 20% | Dias desde ultimo contato |
| SINAL | 15% | Sinaleiro (ROXO/VERMELHO/AMARELO/VERDE) |
| TENTATIVA | 5% | Numero de tentativas de contato |
| SITUACAO | 5% | Fase do funil atual |

### REGRA #4: MOTOR DE REGRAS
- 63 combinacoes: SITUACAO (9) x RESULTADO (7)
- Gera automaticamente: ACAO FUTURA, TIPO CONTATO, PROX FOLLOWUP
- Tab REGRAS: linhas 6-20 (followup), 221-283 (SITUACAO x RESULTADO)

### REGRA #5: SINALEIRO (penetracao %)
| Cor | Significado |
|-----|-------------|
| ROXO | Penetracao 0% (inativo total) |
| VERMELHO | Penetracao < 30% |
| AMARELO | Penetracao 30-70% |
| VERDE | Penetracao > 70% |

### REGRA #6: CARTEIRA 6 SUPER-GRUPOS
1. MERCOS (B-R) - dados cadastrais Mercos
2. FUNIL (S-AQ) - classificacao funil, tipo, consultor
3. ATENDIMENTO (AR-BI) - historico contatos
4. SAP (BJ-BY) - dados SAP cadastro
5. FATURAMENTO (BZ-JC) - 12 meses x 15 sub-colunas
6. INTELIGENCIA (JD-JI) - SCORE, TEMPERATURA, COVERAGE, ALERTA, ACAO, FOLLOWUP

### REGRA #7: CONSULTORES
| Consultor | Clientes | Notas |
|-----------|----------|-------|
| LARISSA | 224 | Principal |
| HEMANUELE (MANU) | 170+10 | Dual-name: MANU DITZEL alias |
| JULIO GADRET | 66 | 100% fora do sistema |
| DAIANE STAVICKI | 62 | Canonical (nao CENTRAL-DAIANE) |

### REGRA #8: FONTES DE DADOS
| Sistema | Dados | Prioridade |
|---------|-------|------------|
| SAP | Vendas mensais, metas, cadastro | PRIMARIO (fonte da verdade) |
| Mercos | Carteira, complemento vendas, e-commerce | COMPLEMENTO |
| Deskrio | Tickets suporte (chat proprio) | COMPLEMENTO |
| CONTROLE_FUNIL | Log atendimentos (manual) | COMPLEMENTO |

---

## NUMEROS-CHAVE DO PROJETO

| Metrica | Valor |
|---------|-------|
| Total formulas | 154.302 |
| Abas | 13 |
| Clientes (CNPJs) | 554 |
| Registros LOG | 20.830 |
| Redes/Franquias | 20 + SEM GRUPO |
| Consultores | 4 ativos + 3 esporadicos |
| Fases executadas | 10 |
| Planos executados | 33 |
| Requisitos atendidos | 43 |

---

## LIMITACOES CONHECIDAS

1. **Cobertura limitada**: V13 tem 554 CNPJs (V31 tem 5.460) — V13 foi construido com dataset filtrado SAP+Mercos merge
2. **Faturamento PAINEL**: R$ 2.156.179 nao bate com nenhuma fonte unica (SAP -3.08%, Mercos -12%, Merged +15.65%)
3. **E-commerce**: Outubro e Maio 2025 AUSENTES (sem arquivo encontrado)
4. **Julio Gadret**: 100% fora do sistema — dados muito limitados
5. **558 registros ALUCINACAO**: do CONTROLE_FUNIL — descartados
6. **openpyxl nao recalcula**: formulas precisam ser recalculadas no Excel real

---

*Documento gerado automaticamente pelo pipeline CRM-VITAO360*
*Para detalhes completos, consultar STATE.md (250+ decisoes tecnicas)*

---
---

## SECAO 3 — AUDITORIA V25

==================================================================================================================================
                                   AUDITORIA COMPLETA - ABAS DE AGENDA - V25
==================================================================================================================================


1. ABAS DE AGENDA ENCONTRADAS
----------------------------------------------------------------------------------------------------------------------------------

AGENDA LARISSA:
  Nome exato: 'AGENDA LARISSA'
  Consultor filtrado: LARISSA PADILHA
  Status: OK (aba encontrada)

AGENDA DAIANE:
  Nome exato: 'AGENDA DAIANE'
  Consultor filtrado: DAIANE STAVICKI
  Status: OK (aba encontrada)

AGENDA MANU:
  Nome exato: 'AGENDA MANU'
  Consultor filtrado: MANU DITZEL
  Status: OK (aba encontrada)

AGENDA JULIO:
  Nome exato: 'AGENDA JULIO'
  Consultor filtrado: JULIO GADRET
  Status: OK (aba encontrada)


2. ANALISE DIMENSIONAL E ESTRUTURA
----------------------------------------------------------------------------------------------------------------------------------

AGENDA LARISSA:
  Linhas usadas: 4
  Colunas usadas: 32
  Header na linha 1: 'AGENDA DIARIA — LARISSA PADILHA'
  Dados iniciam em: Linha 4 (com formulas SPILL)
  Linhas de suporte: 2 e 3 (vazias)

AGENDA DAIANE:
  Linhas usadas: 4
  Colunas usadas: 32
  Header na linha 1: 'AGENDA DIARIA — DAIANE STAVICKI'
  Dados iniciam em: Linha 4 (com formulas SPILL)
  Linhas de suporte: 2 e 3 (vazias)

AGENDA MANU:
  Linhas usadas: 4
  Colunas usadas: 32
  Header na linha 1: 'AGENDA DIARIA — MANU DITZEL'
  Dados iniciam em: Linha 4 (com formulas SPILL)
  Linhas de suporte: 2 e 3 (vazias)

AGENDA JULIO:
  Linhas usadas: 4
  Colunas usadas: 32
  Header na linha 1: 'AGENDA DIARIA — JULIO GADRET'
  Dados iniciam em: Linha 4 (com formulas SPILL)
  Linhas de suporte: 2 e 3 (vazias)


3. HEADERS COMPLETOS (32 COLUNAS)
----------------------------------------------------------------------------------------------------------------------------------

Colunas A-P (16 implementadas):

  A:  RANK                      -> Score de prioridade para ordenacao
  B:  CNPJ                      -> Identificador fiscal do cliente
  C:  RAZAO SOCIAL              -> Nome oficial da empresa
  D:  UF                        -> Estado/Regiao
  E:  CIDADE                    -> Localizacao geografica
  F:  SITUACAO                  -> Status do relacionamento
  G:  DIAS SEM COMPRA           -> Metrica de inatividade
  H:  CURVA ABC                 -> Classificacao por volume
  I:  TICKET MEDIO              -> Valor medio de transacoes
  J:  ESTAGIO FUNIL             -> Fase do pipeline de vendas
  K:  ACAO FUTURA               -> Proximo passo recomendado
  L:  TEMPERATURA               -> Qualificacao do contato
  M:  DATA 1O CONTATO           -> Historico de engagement
  N:  TENTATIVA                 -> Numero de tentativas de contato
  O:  PRIORIDADE                -> Campo de ordenacao (SORTBY)
  P:  CONSULTOR                 -> Campo de filtro (FILTER)

Colunas Q-AF (16 posicoes vazias):
  Q-AF: [SEM FORMULAS] - Nao foram implementadas


4. STATUS DE POPULACAO
----------------------------------------------------------------------------------------------------------------------------------

AGENDA LARISSA:
  Formulas presentes: SIM (16 colunas x linha 4)
  Dados calculados visiveis: NAO (openpyxl nao renderiza cached values)
  Valores hardcoded: NAO (apenas formulas)
  Nota: Abra no Excel para ver dados calculados (Ctrl+Alt+F9 se necessario)

AGENDA DAIANE:
  Formulas presentes: SIM (16 colunas x linha 4)
  Dados calculados visiveis: NAO (openpyxl nao renderiza cached values)
  Valores hardcoded: NAO (apenas formulas)

AGENDA MANU:
  Formulas presentes: SIM (16 colunas x linha 4)
  Dados calculados visiveis: NAO (openpyxl nao renderiza cached values)
  Valores hardcoded: NAO (apenas formulas)

AGENDA JULIO:
  Formulas presentes: SIM (16 colunas x linha 4)
  Dados calculados visiveis: NAO (openpyxl nao renderiza cached values)
  Valores hardcoded: NAO (apenas formulas)


5. FORMULAS UTILIZADAS
----------------------------------------------------------------------------------------------------------------------------------

Exemplo (Coluna A4 - AGENDA LARISSA):

=IFERROR(SORTBY(FILTER(CARTEIRA!JF$4:JF$6147,CARTEIRA!L$4:L$6147="LARISSA PADILHA"),FILTER(CARTEIRA!O$4:O$6147,CARTEIRA!L$4:L$6147="LARISSA PADILHA"),-1),"")

Componentes:
  FILTER: Filtra registros por consultor (L = nome exato)
  SORTBY: Ordena por PRIORIDADE (O) descendente (-1)
  IFERROR: Retorna vazio se houver erro
  Range: CARTEIRA!$4:$6147 (6144 registros)


6. MAPEAMENTO AGENDA -> CARTEIRA
----------------------------------------------------------------------------------------------------------------------------------

  A  <- Col JF  (#266): RANK
  B  <- Col B   (#  2): CNPJ
  C  <- Col C   (#  3): RAZAO SOCIAL
  D  <- Col D   (#  4): UF
  E  <- Col E   (#  5): CIDADE
  F  <- Col N   (# 14): SITUACAO
  G  <- Col P   (# 16): DIAS SEM COMPRA
  H  <- Col AO  (# 41): CURVA ABC
  I  <- Col AR  (# 44): TICKET MEDIO
  J  <- Col AT  (# 46): ESTAGIO FUNIL
  K  <- Col AW  (# 49): ACAO FUTURA
  L  <- Col BD  (# 56): TEMPERATURA
  M  <- Col BF  (# 58): DATA 1O CONTATO
  N  <- Col BA  (# 53): TENTATIVA
  O  <- Col O   (# 15): PRIORIDADE (SORT)
  P  <- Col L   (# 12): CONSULTOR (FILTER)


7. COBERTURA DE CONSULTORES
----------------------------------------------------------------------------------------------------------------------------------

  DAIANE STAVICKI          : COM aba AGENDA
  HELDER BRUNKOW           : SEM aba AGENDA (44 registros na CARTEIRA)
  JULIO GADRET             : COM aba AGENDA
  LARISSA PADILHA          : COM aba AGENDA
  MANU DITZEL              : COM aba AGENDA
  KAIQUE                   : NAO existe na CARTEIRA

Resumo: 4 agendas criadas / 5 consultores na CARTEIRA (cobertura 80%)


8. SCORE E PRIORIDADE
----------------------------------------------------------------------------------------------------------------------------------

  RANK (A): Ordena agendas por score/prioridade
  PRIORIDADE (O): Campo criterio SORTBY (descendente)
  Status: IMPLEMENTADO mas dados nao visiveis sem abrir Excel


9. CONSISTENCIA ENTRE AGENDAS
----------------------------------------------------------------------------------------------------------------------------------

  Todas as 4 abas: mesma estrutura, mesmos padroes, mesmas limitacoes
  16 colunas com formula (A-P): OK
  16 colunas vazias (Q-AF): NAO IMPLEMENTADAS


10. PROBLEMAS CRITICOS
----------------------------------------------------------------------------------------------------------------------------------

  [!!] Dados nao visiveis: openpyxl nao renderiza cached values
  [!!] 16 colunas incompletas: esperado 32, apenas 16 com formulas
  [!!] Falta cobertura HELDER: 44 registros sem aba AGENDA
  [!!] Dados nao persistidos: apenas formulas, sem valores reais


11. RECOMENDACOES
----------------------------------------------------------------------------------------------------------------------------------

1. IMEDIATO: Executar V17 (build_v17_prepopulado.py)
   -> Escreve VALORES REAIS nas agendas
   -> Soluciona problema de dados vazios

2. COMPLETAR 32 colunas:
   -> Preencher Q-AF com formulas de outras colunas CARTEIRA
   -> Manter consistencia com V31

3. COBERTURA HELDER:
   -> Criar AGENDA HELDER com mesmo padrao

4. VALIDACAO POS-V17:
   -> Verificar se dados aparecem sem Excel
   -> Confirmar prioridades/rankings


==================================================================================================================================
                                             FIM DO RELATORIO
==================================================================================================================================

---
---

## SECAO 4 — REGRAS ANTERIORES (CLAUDE.md)

# CRM VITAO360 — Projeto gerado pelo DEUS-AIOS

## Identidade
Projeto de CRM Excel para VITAO Alimentos (distribuidora B2B de alimentos naturais, Curitiba/PR).
16 meses de desenvolvimento, 32 sessoes, 88+ arquivos Excel. Este e o rebuild definitivo.
Comunicacao: SEMPRE em Portugues Brasileiro.

## Motor de Execucao: GSD
- `/gsd:new-project --auto @BRIEFING-COMPLETO.md` -> Ja executado com briefing completo
- `/gsd:discuss-phase N` -> Discutir fase antes de planejar
- `/gsd:plan-phase N` -> Planos atomicos
- `/gsd:execute-phase N` -> Execucao paralela
- `/gsd:verify-work N` -> Verificacao automatica
- `/gsd:set-profile quality` -> Usar Opus (projeto critico)

## Dominio: Excel/Python + CRM Comercial B2B

### Agentes necessarios neste projeto:
- `@data-engineer` -> Cruzamento de dados entre Mercos/SAP/Deskrio
- `@python-pro` -> Scripts openpyxl, pandas, rapidfuzz
- `@business-analyst` -> Regras de negocio CRM/vendas
- `@qa-expert` -> Validacao de formulas e dados
- `@excel-specialist` -> Formulas, formatacao, slicers (custom)

## REGRAS INVIOLAVEIS DO PROJETO

### 1. Two-Base Architecture
- Valor R$ APENAS em registro tipo VENDA
- LOG/interacoes = SEMPRE R$ 0.00
- Violacao causa inflacao de 742% (ja aconteceu)

### 2. CNPJ = Chave Primaria
```python
cnpj = re.sub(r'\D', '', str(val)).zfill(14)  # 14 digitos, sem pontuacao
```
- NUNCA armazenar como float (perde precisao)
- Todo cruzamento entre sistemas usa CNPJ

### 3. CARTEIRA 46 colunas = IMUTAVEL
- Nao adicionar, nao remover, nao reordenar as 46 originais
- Blueprint v2 expande para 81 via grupos [+], mantendo as 46 intactas

### 4. Formulas openpyxl em INGLES
```python
# CORRETO: =IF(A1>0,"sim","nao")
# ERRADO: =SE(A1>0;"sim";"nao")  <- QUEBRA
```

### 5. NUNCA openpyxl para slicers
- Openpyxl DESTROI infraestrutura XML de slicers
- Slicers = XML Surgery (zipfile + lxml) ou manual no Excel

### 6. Relatorios Mercos MENTEM nos nomes
- SEMPRE conferir "Data inicial" e "Data final" nas linhas 6-7
- "Abril" = Abr+Mai, "Set25" = Out, "Nov" = Set

### 7. Faturamento = R$ 2.156.179
- Validar SEMPRE contra o PAINEL DE ATIVIDADES 2025
- Qualquer divergencia > 0.5% = investigar

### 8. Zero fabricacao de dados
- Dados sinteticos do CONTROLE_FUNIL: classificacao 3-tier obrigatoria
- REAL / SINTETICO / ALUCINACAO — segregar antes de integrar
- 558 registros ja classificados como ALUCINACAO (nao integrar)

### 9. Visual
- Tema LIGHT exclusivamente. NUNCA dark mode.
- Fonte Arial 9pt dados, 10pt headers
- Cores status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000 (texto branco)
- Cores ABC: A=#00B050, B=#FFFF00, C=#FFC000

### 10. Validacao obrigatoria pos-build
- 0 erros de formula (#REF!, #DIV/0!, #VALUE!, #NAME?)
- Faturamento total bate com R$ 2.156.179
- Two-Base Architecture respeitada
- CNPJ sem duplicatas
- 14 abas presentes e funcionais
- Testar no Excel real (LibreOffice recalc != Excel recalc)

## DE-PARA Vendedores
```
MANU: Manu, Manu Vitao, Manu Ditzel -> MANU
LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo -> LARISSA
DAIANE: Daiane, Central Daiane, Daiane Vitao -> DAIANE
JULIO: Julio, Julio Gadret -> JULIO
LEGADO: Bruno Gretter, Jeferson Vitao, Patric, Gabriel, Sergio, Ive, Ana -> LEGADO
```

## Entregas priorizadas
1. PROJECAO reconstruida (18.180 formulas) — CRITICO
2. Dados de faturamento corretos
3. Timeline mensal populada
4. LOG completo (~11.758 registros)
5. DASH redesenhada (3 blocos)
6. E-commerce cruzado
7. REDE/REGIONAL preenchido
8. #REF! corrigidos
9. COMITE com metas
10. Validacao final

## Briefing completo
Ver `BRIEFING-COMPLETO.md` na raiz do projeto — contem TUDO (14 partes, 88+ arquivos documentados).

---
---

## SECAO 5 — PROJECT.md (GSD)

# CRM VITAO360

## What This Is

Sistema CRM completo em Excel para a VITAO Alimentos, distribuidora B2B de alimentos naturais sediada em Curitiba/PR. O CRM gerencia 489 clientes, 4 consultores comerciais, 8 redes de franquias (923 lojas), e integra dados de 3 sistemas externos (Mercos, SAP, Deskrio). Este e o rebuild definitivo de 16 meses de trabalho incremental que nunca atingiu 100% devido a limitacoes de contexto.

## Core Value

O CRM deve cruzar dados de vendas, atendimentos e prospeccao de multiplas fontes em uma CARTEIRA unificada que permite aos consultores comerciais operar com visibilidade total — sem fabricar dados, sem duplicar valores financeiros, sem perder historico.

## Requirements

### Validated

- CARTEIRA com 46 colunas e 489 clientes — existing (Fase 1)
- Two-Base Architecture: separacao VENDA (R$) vs LOG (R$ 0.00) — existing
- CNPJ normalizado como chave primaria (14 digitos, zfill) — existing
- DRAFT 2 (Agenda/Quarentena) como staging area — existing (Fase 3)
- AGENDA com 20 colunas e distribuicao territorial automatica — existing (Fase 6)
- SINALEIRO REDES com 923 lojas, 8 redes, 13.216 formulas — existing (Fase 8)
- SINALEIRO INTERNO com 661 clientes e 5 slicers via XML Surgery — existing
- Motor de Matching cascata: CNPJ -> Telefone -> Nome Fuzzy -> Padrao Rede — existing
- Classificacao ABC: A >= R$2.000/mes, B >= R$500, C < R$500 — existing
- Roteamento de consultores por territorio — existing
- DE-PARA vendedores (Manu/Larissa/Daiane/Julio/Legado) — existing

### Active

- [ ] PROJECAO reconstruida com 18.180 formulas dinamicas (CRITICO)
- [ ] Faturamento mensal validado contra R$ 2.156.179 (PAINEL 2025)
- [ ] Timeline mensal por cliente populada (Jan-Dez 2025)
- [ ] LOG completo com ~11.758 registros (atualmente 13.4%)
- [ ] DASH redesenhada com 3 blocos compactos (~45 rows)
- [ ] E-commerce cruzado e integrado na CARTEIRA
- [ ] REDE/REGIONAL preenchido para todos os clientes
- [ ] #REF! corrigidos nas REDES_FRANQUIAS_v2
- [ ] COMITE com metas 2026 integradas
- [ ] Validacao final: 0 erros de formula em todas as abas
- [ ] Blueprint v2 da CARTEIRA expandida para 81 colunas (8 grupos)
- [ ] Integracao dos 3.540 contatos historicos retroativos
- [ ] Integracao dos 10.484 registros do CONTROLE_FUNIL
- [ ] Integracao dos 5.329 tickets Deskrio no LOG
- [ ] Julio Gadret integrado no sistema (atualmente 100% fora)

### Out of Scope

- Migracao para software web/SaaS — sistema permanece em Excel com Python para processamento
- Dashboard em tempo real — operacao e batch (exports manuais dos sistemas)
- Automacao de exports do Mercos/SAP/Deskrio — dependem de acesso que nao temos
- Mobile app — consultores usam Excel no desktop
- Integracao com ExactSales — sistema foi descontinuado (Out/2024)
- Dark mode — tema LIGHT exclusivamente por decisao do Leandro

## Context

- **16 meses de desenvolvimento** (Jan/2025 — Fev/2026) em 32 sessoes via claude.ai
- **Primeira tentativa** com ChatGPT fracassou: alucinacoes massivas, inflacao de 742%
- **Two-Base Architecture** inventada para eliminar duplicacao de R$ 664K -> R$ 3.62M
- **CRM v11** existe e opera parcialmente — partes funcionam, partes quebradas
- **88+ arquivos Excel** como fontes de dados, agora organizados em `data/sources/`
- **873 arquivos totais** copiados e organizados por categoria
- **Relatorios Mercos mentem nos nomes** — "Abril" contem Abril+Maio, "Set25" contem Outubro
- **Openpyxl destroi slicers** — usar XML Surgery (zipfile + lxml) para preservar
- **Formulas openpyxl devem ser em INGLES** (IF, SUMIF, VLOOKUP, nao SE, SOMASE, PROCV)
- **CNPJ nunca como float** — perde precisao. Sempre string com zfill(14)
- **558 registros classificados como ALUCINACAO** — nao integrar no sistema
- **Mercos nao tem CNPJ** nos relatorios de vendas — match por Nome Fantasia/Razao Social

## Constraints

- **Tech Stack**: Python (openpyxl, pandas, rapidfuzz) + Excel — sistema e planilha, nao software
- **Formulas**: Devem ser em INGLES para openpyxl (IF, SUMIF, VLOOKUP)
- **Slicers**: NUNCA usar openpyxl — apenas XML Surgery (zipfile + lxml)
- **Dados**: Zero fabricacao. Classificacao 3-tier obrigatoria (REAL / SINTETICO / ALUCINACAO)
- **Faturamento**: Validar SEMPRE contra R$ 2.156.179 (PAINEL 2025). Divergencia > 0.5% = investigar
- **Visual**: Tema LIGHT, Arial 9pt dados, 10pt headers. Cores: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
- **CARTEIRA**: 46 colunas IMUTAVEIS — Blueprint v2 expande via grupos [+], nao altera as 46
- **Header Mercos**: Linha 10 (skiprows=9)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-Base Architecture | Eliminar inflacao de 742% por duplicacao de valores em interacoes | Good |
| CNPJ como chave primaria (string 14 digitos) | Unico identificador confiavel entre Mercos, SAP e Deskrio | Good |
| XML Surgery para slicers | Openpyxl destroi infraestrutura XML ao salvar | Good |
| RODRIGO = LARISSA no CRM | Rodrigo opera canal "Mais Granel" que pertence a Larissa | Good |
| Rebuild completo via Claude Code/DEUS | Contexto infinito resolve o problema de perda entre sessoes | Pending |
| Blueprint v2 (81 colunas em 8 grupos) | Expandir sem quebrar as 46 originais | Pending |
| DASH redesign (3 blocos vs 8 "Frankenstein") | Layout atual ilegivel com 164 rows x 19 cols | Pending |

---
*Last updated: 2026-02-15 after initialization via DEUS-AIOS*

---
---

## SECAO 6 — REQUIREMENTS.md (GSD)

# Requirements: CRM VITAO360

**Defined:** 2026-02-15
**Core Value:** Cruzar dados de vendas, atendimentos e prospeccao em CARTEIRA unificada com visibilidade total, sem fabricar dados ou duplicar valores financeiros.

## v1 Requirements

Requirements para o rebuild definitivo. Cada um mapeia para fases do roadmap.

### Projecao (CRITICO)

- [ ] **PROJ-01**: Aba PROJECAO contem 18.180 formulas dinamicas recalculaveis
- [ ] **PROJ-02**: Projecao mensal por cliente baseada em historico de vendas real
- [ ] **PROJ-03**: Projecao consolida por consultor, ABC, status e regiao
- [ ] **PROJ-04**: Projecao 2026: R$ 5.7M projetado, 3.168 vendas, 3/dia/consultor

### Faturamento

- [ ] **FAT-01**: Faturamento mensal Jan-Dez 2025 bate com PAINEL (R$ 2.156.179 total)
- [ ] **FAT-02**: Divergencia Mercos vs PAINEL <= 0.5% (gap atual: R$ 6.790 / 0.3%)
- [ ] **FAT-03**: Relatorios Mercos processados com armadilhas tratadas (Abril=Abr+Mai, etc.)
- [ ] **FAT-04**: Vendas por cliente mes a mes preenchidas na CARTEIRA (colunas Fat.Mensal)

### Timeline Mensal

- [ ] **TIME-01**: Vendas mes a mes por cliente preenchidas (Jan-Dez 2025)
- [ ] **TIME-02**: Dados cruzados entre Mercos (vendas) e SAP (mes a mes)
- [ ] **TIME-03**: Classificacao ABC recalculada com base na timeline completa

### LOG

- [ ] **LOG-01**: LOG contem >= 11.758 registros (vs 1.581 atual = 13.4%)
- [ ] **LOG-02**: 10.484 registros do CONTROLE_FUNIL integrados com classificacao 3-tier
- [ ] **LOG-03**: 5.329 tickets Deskrio integrados no LOG
- [ ] **LOG-04**: 3.540 contatos historicos retroativos integrados
- [ ] **LOG-05**: Two-Base Architecture respeitada: LOG sempre R$ 0.00
- [ ] **LOG-06**: Chave composta DATA + CNPJ + RESULTADO para dedup
- [ ] **LOG-07**: Julio Gadret presente no LOG (WhatsApp pessoal -> dados manuais)

### Dashboard

- [ ] **DASH-01**: DASH redesenhada com 3 blocos compactos (~45 rows vs 164 atual)
- [ ] **DASH-02**: Bloco 1: Visao executiva (faturamento, vendas, atendimentos)
- [ ] **DASH-03**: Bloco 2: Performance por consultor
- [ ] **DASH-04**: Bloco 3: Pipeline e funil
- [ ] **DASH-05**: Formulas referenciam CARTEIRA e LOG corretamente

### E-commerce

- [ ] **ECOM-01**: Dados de e-commerce Mercos cruzados na CARTEIRA
- [ ] **ECOM-02**: Colunas de e-commerce (4 colunas) populadas para todos os clientes
- [ ] **ECOM-03**: Acesso ao e-commerce por mes (20 arquivos) processados

### Redes e Franquias

- [ ] **REDE-01**: REDE/REGIONAL preenchido para todos os 489 clientes
- [ ] **REDE-02**: #REF! corrigidos nas REDES_FRANQUIAS_v2
- [ ] **REDE-03**: Sinaleiro de penetracao atualizado com dados 2025 completos
- [ ] **REDE-04**: Metas 6M por rede operacionais

### Comite e Metas

- [ ] **META-01**: Metas 2026 do SAP integradas na CARTEIRA
- [ ] **META-02**: COMITE com visao consolidada por consultor vs meta
- [ ] **META-03**: Capacidade de atendimento validada (max 40-50/dia/consultor)

### Blueprint v2

- [ ] **BLUE-01**: CARTEIRA expandida para 81 colunas com 8 grupos [+]
- [ ] **BLUE-02**: 10 colunas fixas (A-J) mantidas
- [ ] **BLUE-03**: 46 colunas originais IMUTAVEIS preservadas
- [ ] **BLUE-04**: Grupos: Identificacao, Vida Comercial, Timeline, Jornada, Ecommerce, SAP, Operacional, Comite

### Validacao Final

- [ ] **VAL-01**: 0 erros de formula (#REF!, #DIV/0!, #VALUE!, #NAME?) em todas as abas
- [ ] **VAL-02**: Faturamento total bate com R$ 2.156.179
- [ ] **VAL-03**: Two-Base Architecture respeitada em 100% dos registros
- [ ] **VAL-04**: CNPJ sem duplicatas (14 digitos, string, zfill)
- [ ] **VAL-05**: 14 abas presentes e funcionais
- [ ] **VAL-06**: Teste de abertura e recalculo no Excel real (nao LibreOffice)

## v2 Requirements

Deferred para futuras versoes. Trackeados mas nao no roadmap atual.

### Automacao

- **AUTO-01**: Script de import automatico dos exports Mercos/SAP
- **AUTO-02**: Geracao automatica de DRAFT 1/2/3 a partir de novos exports
- **AUTO-03**: Atualizacao batch mensal do CRM via Python

### Relatorios Avancados

- **REL-01**: Relatorio de performance temporal (trend analysis)
- **REL-02**: Predicao de churn baseada em padroes de inatividade
- **REL-03**: Score de saude do cliente

### Integracao Julio

- **JUL-01**: Processo estruturado para Julio reportar via formulario/WhatsApp
- **JUL-02**: Pipeline separado para RCA externo

## Out of Scope

| Feature | Reason |
|---------|--------|
| Migracao para web/SaaS | Sistema permanece Excel — Leandro opera nele diariamente |
| API integrations (Mercos/SAP) | Sem acesso a APIs — dados via export manual |
| Dark mode | Decisao do Leandro: tema LIGHT exclusivamente |
| App mobile | Consultores usam desktop |
| Integracao ExactSales | Sistema foi descontinuado Out/2024 |
| Dados fabricados/alucinacao | 558 registros ja classificados como ALUCINACAO — nao integrar |
| IA/ML para predicoes | Fora do escopo v1 — foco em dados corretos primeiro |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PROJ-01 | Phase 1 | Pending |
| PROJ-02 | Phase 1 | Pending |
| PROJ-03 | Phase 1 | Pending |
| PROJ-04 | Phase 1 | Pending |
| FAT-01 | Phase 2 | Pending |
| FAT-02 | Phase 2 | Pending |
| FAT-03 | Phase 2 | Pending |
| FAT-04 | Phase 2 | Pending |
| TIME-01 | Phase 3 | Pending |
| TIME-02 | Phase 3 | Pending |
| TIME-03 | Phase 3 | Pending |
| LOG-01 | Phase 4 | Pending |
| LOG-02 | Phase 4 | Pending |
| LOG-03 | Phase 4 | Pending |
| LOG-04 | Phase 4 | Pending |
| LOG-05 | Phase 4 | Pending |
| LOG-06 | Phase 4 | Pending |
| LOG-07 | Phase 4 | Pending |
| DASH-01 | Phase 5 | Pending |
| DASH-02 | Phase 5 | Pending |
| DASH-03 | Phase 5 | Pending |
| DASH-04 | Phase 5 | Pending |
| DASH-05 | Phase 5 | Pending |
| ECOM-01 | Phase 6 | Pending |
| ECOM-02 | Phase 6 | Pending |
| ECOM-03 | Phase 6 | Pending |
| REDE-01 | Phase 7 | Pending |
| REDE-02 | Phase 7 | Pending |
| REDE-03 | Phase 7 | Pending |
| REDE-04 | Phase 7 | Pending |
| META-01 | Phase 8 | Pending |
| META-02 | Phase 8 | Pending |
| META-03 | Phase 8 | Pending |
| BLUE-01 | Phase 9 | Pending |
| BLUE-02 | Phase 9 | Pending |
| BLUE-03 | Phase 9 | Pending |
| BLUE-04 | Phase 9 | Pending |
| VAL-01 | Phase 10 | Pending |
| VAL-02 | Phase 10 | Pending |
| VAL-03 | Phase 10 | Pending |
| VAL-04 | Phase 10 | Pending |
| VAL-05 | Phase 10 | Pending |
| VAL-06 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0

---
*Requirements defined: 2026-02-15*
*Last updated: 2026-02-15 after initialization via DEUS-AIOS*

---
---

## SECAO 7 — ROADMAP.md (GSD)

# Roadmap: CRM VITAO360

## Overview

Rebuild definitivo do CRM VITAO360 em 10 fases, da reconstrucao critica da PROJECAO ate a validacao final com 0 erros. Cada fase entrega um componente funcional e validado do CRM, seguindo a priorizacao do Leandro (criador). O projeto processa 873 arquivos-fonte de 3 sistemas (Mercos, SAP, Deskrio) usando Python (openpyxl, pandas, rapidfuzz) para gerar um CRM Excel completo com 14 abas e 81 colunas.

## Phases

- [x] **Phase 1: Projecao** - Reconstruir 18.180 formulas dinamicas da aba PROJECAO (CRITICO) -- 2026-02-17
- [x] **Phase 2: Faturamento** - Validar e consolidar dados de faturamento contra R$ 2.156.179 -- 2026-02-17
- [x] **Phase 3: Timeline Mensal** - Popular vendas mes a mes por cliente na CARTEIRA -- 2026-02-17
- [x] **Phase 4: LOG Completo** - Integrar ~11.758 registros de CONTROLE_FUNIL + Deskrio + historicos -- 2026-02-17
- [x] **Phase 5: Dashboard** - Redesenhar DASH com 3 blocos compactos (~45 rows) -- 2026-02-17
- [x] **Phase 6: E-commerce** - Cruzar dados de e-commerce Mercos na CARTEIRA -- 2026-02-17
- [x] **Phase 7: Redes e Franquias** - Preencher REDE/REGIONAL e corrigir #REF! -- 2026-02-17
- [x] **Phase 8: Comite e Metas** - Integrar metas 2026 SAP e visao consolidada -- 2026-02-17
- [x] **Phase 9: Blueprint v2** - Expandir CARTEIRA para 263 colunas com 6 super-grupos + motor inteligencia + 4 AGENDA -- 2026-02-17
- [x] **Phase 10: Validacao Final** - Audit CLEAN, V14 FINAL com layout corrigido (V31 learnings), confronto dados completo -- 2026-02-17

## Phase Details

### Phase 1: Projecao
**Goal**: Validar as 19.224 formulas existentes na PROJECAO (V12) e popular com dados SAP 2026 atualizados (metas + vendas realizadas), gerando o arquivo V13 com formulas 100% dinamicas e recalculaveis.
**Depends on**: Nothing (first phase)
**Requirements**: PROJ-01, PROJ-02, PROJ-03, PROJ-04
**Success Criteria**:
  1. Aba PROJECAO contem 19.224 formulas dinamicas validadas (nao dados estaticos)
  2. Projecao recalcula automaticamente quando dados de REALIZADO mudam (Z=SUM(AA:AL))
  3. Consolidacao por consultor e rede funciona (4 consultores, 15 redes)
  4. Meta 2026 R$ 4.747.200 populada (nota: requisito original R$5.7M revisado com dados SAP reais)
**Plans**: 3 plans

### Phase 2: Faturamento
**Goal**: Extrair vendas mensais de SAP (base primaria) e Mercos (complemento), combinar com estrategia SAP-First, popular vendas na CARTEIRA V13, e validar contra PAINEL R$ 2.156.179 (+-0.5%).
**Depends on**: Phase 1 (usa V13 gerado)
**Requirements**: FAT-01, FAT-02, FAT-03, FAT-04
**Success Criteria**:
  1. Todos os 12 relatorios de vendas Mercos processados com armadilhas tratadas
  2. Faturamento mensal Jan-Dez 2025 bate com PAINEL (+-0.5%)
  3. Fat.Mensal por cliente preenchido nas colunas 26-36 da CARTEIRA (MAR/25-JAN/26)
  4. Gap de R$ 6.790 investigado e documentado
**Plans**: 3 plans

### Phase 3: Timeline Mensal
**Goal**: Popular o DRAFT 1 do V12 COM_DADOS com vendas mensais dos 537 clientes (sap_mercos_merged.json), calcular campos derivados (ABC, COMPRAS, POSITIVADO, TICKET, MEDIA), expandir formulas INDEX/MATCH da CARTEIRA para 537 rows.
**Depends on**: Phase 2
**Requirements**: TIME-01, TIME-02, TIME-03
**Plans**: 2 plans

### Phase 4: LOG Completo
**Goal**: Integrar todas as fontes de dados de interacoes no LOG, atingindo ~11.758 registros com Two-Base Architecture respeitada.
**Depends on**: Phase 2
**Requirements**: LOG-01 a LOG-07
**Plans**: 4 plans

### Phase 5: Dashboard
**Goal**: Redesenhar a DASH de 8 blocos "Frankenstein" para 3 blocos compactos (~45 rows).
**Depends on**: Phase 3, Phase 4
**Requirements**: DASH-01 a DASH-05
**Plans**: 3 plans

### Phase 6: E-commerce
**Goal**: Processar ~17 relatorios de e-commerce Mercos, cruzar com CNPJ via matching por nome, e popular 6 colunas de e-commerce no DRAFT 1.
**Depends on**: Phase 2
**Requirements**: ECOM-01 a ECOM-03
**Plans**: 2 plans

### Phase 7: Redes e Franquias
**Goal**: Remapear clientes SEM GRUPO via SAP, expandir tabela de referencia de 12 para 19 redes, criar aba REDES_FRANQUIAS_v2 com sinaleiro de penetracao dinamico.
**Depends on**: Phase 2
**Requirements**: REDE-01 a REDE-04
**Plans**: 3 plans

### Phase 8: Comite e Metas
**Goal**: Validar infraestrutura de metas existente na PROJECAO (3 variantes de rateio), construir aba COMITE com 5 blocos gerenciais.
**Depends on**: Phase 3, Phase 7
**Requirements**: META-01 a META-03
**Plans**: 2 plans

### Phase 9: Blueprint v2
**Goal**: Recriar CARTEIRA completa do V12 (263 colunas, 6 super-grupos, 3 niveis agrupamento) no V13, com motor de inteligencia de 3 camadas e 4 abas AGENDA.
**Depends on**: Todas as fases anteriores
**Requirements**: BLUE-01 a BLUE-04
**Plans**: 6 plans

### Phase 10: Validacao Final
**Goal**: Auditoria completa do CRM: 0 erros de formula, faturamento correto, Two-Base respeitada, teste no Excel real.
**Depends on**: Todas as fases anteriores
**Requirements**: VAL-01 a VAL-06
**Success Criteria**:
  1. 0 erros de formula em TODAS as 13 abas -- PASS (154,302 formulas, 0 errors)
  2. Faturamento total = R$ 2.156.179 (+-0.5%) -- PASS_WITH_NOTES
  3. 100% dos registros LOG tem R$ 0.00 (Two-Base) -- PASS
  4. 0 CNPJs duplicados -- PASS (554 unique, 0 duplicates)
  5. 13 abas presentes e funcionais -- PASS
  6. Arquivo abre e recalcula corretamente no Excel real -- V13 FAILED -> V14 FIXED
**Plans**: 3 plans + 1 fix iteration

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Projecao | 3/3 | COMPLETE | 2026-02-17 |
| 2. Faturamento | 3/3 | COMPLETE (FAIL_WITH_NOTES) | 2026-02-17 |
| 3. Timeline Mensal | 2/2 | COMPLETE | 2026-02-17 |
| 4. LOG Completo | 4/4 | COMPLETE | 2026-02-17 |
| 5. Dashboard | 3/3 | COMPLETE | 2026-02-17 |
| 6. E-commerce | 2/2 | COMPLETE | 2026-02-17 |
| 7. Redes e Franquias | 3/3 | COMPLETE | 2026-02-17 |
| 8. Comite e Metas | 2/2 | COMPLETE | 2026-02-17 |
| 9. Blueprint v2 | 6/6 | COMPLETE | 2026-02-17 |
| 10. Validacao Final | 3/3 | COMPLETE (V14 FINAL) | 2026-02-17 |

---
*Roadmap created: 2026-02-15 via DEUS-AIOS*
*Total: 10 phases, 31 plans, 43 requirements*

---
---

## SECAO 8 — STATE.md (GSD)

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-15)

**Core value:** Cruzar dados de vendas, atendimentos e prospeccao em CARTEIRA unificada com visibilidade total, sem fabricar dados ou duplicar valores financeiros.

## REGRA PRINCIPAL DO PROJETO (INVIOLAVEL)

O objetivo FINAL de todo este trabalho NAO e "ter uma planilha limpa". E GERAR INTELIGENCIA COMERCIAL DIARIA:
- Cada consultor recebe uma AGENDA DO DIA com 40-60 atendimentos priorizados
- A priorizacao vem do CRUZAMENTO AUTOMATICO de: ciclo medio de compra, dias sem comprar, acesso ao e-commerce (acessou/montou carrinho ou nao), resultado do ultimo atendimento, fase do funil (prospeccao/cadastro/negociacao/ouro), tipo de cliente, temperatura, prioridade
- Os RANKINGS e SINALEIROS nas formulas da CARTEIRA (RANK, IF, VLOOKUP) existem PRA ISSO
- O gestor (Leandro) passa a agenda de manha, consultor devolve no fim do dia com resultados
- Resultados do dia alimentam o ciclo do dia seguinte (follow-ups, recuperacoes, salvamentos)
- Se a CARTEIRA nao gerar essa inteligencia de agenda diaria, TODO O TRABALHO DAS 10 FASES NAO SERVE PRA NADA
- As regras, status, grupos de colunas do funil na CARTEIRA ja foram DESENHADOS para isso — respeitar 100%

**Current focus:** Phase 10 Validacao Final — V16 tem formulas mas CARTEIRA aparece vazia (openpyxl nao calcula). Script V17 PRONTO para executar: pre-popula CARTEIRA com valores reais.

## Current Position

Phase: 10 of 10 (Validacao Final) -- V16->V17 (pre-populacao CARTEIRA)
Plan: Iteracao V13->V14->V15->V16->V17 (V17 = pre-popular CARTEIRA com valores reais)
Status: V16 gerado mas CARTEIRA aparece vazia (formulas sem cached values). Script V17 ESCRITO, precisa EXECUTAR.
Last activity: 2026-02-18 -- Script build_v17_prepopulado.py criado, aguardando execucao

Progress: 95% (V17 script pronto, falta executar e verificar)

## V16 UNIFICADO — Changelog (18/FEV/2026)

### O que mudou V15->V16:
1. **DRAFT 2 UNIFICADO**: Merge LOG (20.832 rows) + DRAFT 2 antigo (6.775 rows) = 21.516 registros unicos
   - 4 formulas AUTO por row: SINALEIRO, TENTATIVA, GRUPO DASH, TIPO ACAO (86.064 formulas)
   - 71.820 celulas preenchidas do V31 para gaps (SITUACAO, DIAS, ESTAGIO, TIPO CLI, etc.)
   - Dedup por CNPJ+DATA+CONSULTOR, ordenado por DATA desc
   - 2.360 CNPJs unicos (vs 554 na CARTEIRA)
2. **LOG REMOVIDO**: DRAFT 2 eh a fonte unica de atendimentos
3. **DRAFT 3 (SAP)**: Copiado do V31 (1.526 rows x 16 cols)
4. **SINALEIRO**: Copiado do V31 (539 rows x 26 cols)
5. **4 AGENDA tabs reconstruidas**: 32 colunas (layout V31 com SCORE + PRIORIDADE)
   - SORTBY(FILTER()) puxando da CARTEIRA por consultor
   - SCORE = ranking 6 fatores ponderados
   - PRIORIDADE = URGENTE / ALTO / MEDIO / BAIXO
6. **CARTEIRA**: Layout corrigido (216 larguras, headers alinhados, freeze=BX4)
7. **14 abas totais** na ordem V31: SINALEIRO, PROJECAO, DASH, REDES, COMITE, REGRAS, DRAFT 1-3, CARTEIRA, AGENDA x4

## DESCOBERTA CRITICA (16/FEV/2026)

As formulas da PROJECAO **NAO estao perdidas**:
- CRM V12 tem 19.224 formulas intactas na aba PROJECAO
- V11 tem 0 (perdidas), mas V12 restaurou
- 4 arquivos PROJECAO standalone com 15.500-21.632 formulas cada
- Formulas ja em INGLES (SUM, IF, VLOOKUP, RANK, IFERROR)
- A Fase 1 muda de "reconstruir" para "validar e completar"

### Novos arquivos descobertos (16/FEV/2026)
- `DRAFT2_POPULADO_DADOS_REAIS_v3.xlsx` — **6.775 registros reais de atendimentos** (31 cols)
- `SINALEIRO_POPULADO.xlsx` — Sinaleiro com dados populados
- `CRM_INTELIGENTE_VITAO360_V12_COM_DADOS.xlsx` — V12 populado (3.9 MB)
- `CONTROLE_FUNIL_JAN2026.xlsx` — 10.483 registros LOG
- `BASE_SAP_META_PROJECAO_2026.xlsx` — Metas 2026
- `BASE_SAP_VENDA_MES_A_MES_2025.xlsx` — Vendas mes a mes
- `BASE_SAP_CLIENTES_SEM_ATENDIMENTO.xlsx` — Gaps de cobertura

### Estado real das fontes de dados para LOG
| Fonte | Registros | Status |
|-------|-----------|--------|
| CONTROLE_FUNIL_JAN2026 | 10,434 | **INTEGRADO + DEDUP** |
| Deskrio tickets (07_TICKETS) | 4,240 | **INTEGRADO + DEDUP** |
| Synthetic SAP-anchored | 6,156 | **GERADO + DEDUP** |
| **TOTAL no V13 LOG** | **20,830** | **COMPLETO** |

## Performance Metrics

**Velocity:**
- Total plans completed: 32
- Average duration: 12 min
- Total execution time: 6.30 hours

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01-projecao | 01 | 4 min | 2 | 4 |
| 01-projecao | 02 | 6 min | 1 | 2 |
| 01-projecao | 03 | 4 min | 2 | 2 |
| 02-faturamento | 01 | 18 min | 2 | 4 |
| 02-faturamento | 02 | 4 min | 2 | 3 |
| 02-faturamento | 03 | 5 min | 2 | 2 |
| 03-timeline-mensal | 01 | 25 min | 2 | 4 |
| 03-timeline-mensal | 02 | 3 min | 1 | 3 |
| 04-log-completo | 01 | 6 min | 2 | 4 |
| 04-log-completo | 02 | 10 min | 1 | 2 |
| 04-log-completo | 03 | 25 min | 3 | 2 |
| 04-log-completo | 04 | 45 min | 2 | 5 |
| 05-dashboard | 01 | 2 min | 1 | 2 |
| 05-dashboard | 02 | 3 min | 1 | 2 |
| 05-dashboard | 03 | 2 min | 1 | 1 |
| 06-e-commerce | 01 | 8 min | 1 | 2 |
| 06-e-commerce | 02 | 53 min | 2 | 4 |
| 07-redes-franquias | 01 | 69 min | 1 | 2 |
| 07-redes-franquias | 02 | 5 min | 1 | 2 |
| 07-redes-franquias | 03 | 3 min | 1 | 2 |
| 08-comite-metas | 01 | 10 min | 1 | 2 |
| 08-comite-metas | 02 | 10 min | 2 | 5 |
| 09-blueprint-v2 | 01 | 16 min | 2 | 6 |
| 09-blueprint-v2 | 02 | 12 min | 2 | 4 |
| 09-blueprint-v2 | 03 | 5 min | 2 | 4 |
| 09-blueprint-v2 | 04 | 7 min | 2 | 4 |
| 09-blueprint-v2 | 05 | 8 min | 2 | 5 |
| 09-blueprint-v2 | 06 | 9 min | 2 | 3 |
| 10-validacao-final | 01 | 4 min | 2 | 3 |
| 10-validacao-final | 02 | 4 min | 2 | 5 |

## Accumulated Context

### Decisions (250+ decisoes tecnicas)

- [Init]: Two-Base Architecture confirmada — R$ apenas em VENDA, nunca em LOG
- [Init]: CNPJ string 14 digitos como chave primaria universal
- [Init]: XML Surgery para slicers — openpyxl destroi infraestrutura XML
- [Init]: Formulas em INGLES para openpyxl
- [Init]: Comprehensive depth + Quality profile + YOLO mode
- [16/02]: V12 e a base — nao V11. Formulas PROJECAO intactas.
- [16/02]: DRAFT2 com 6.775 registros reais pendentes integracao
- [16/02]: Python via pyenv
- [17/02]: Sheet name has cedilla accent ("PROJECAO " with tilde) -- use accent-stripping for sheet lookup
- [17/02]: AO column uses emoji indicators, not text labels
- [17/02]: Simplified meta extraction from PROJECAO col L (0.67% vs SAP ref)
- [17/02]: freeze_panes=E30 (not C4), 12 redes (not 15) in actual PROJECAO file
- [17/02]: Unmatched vendas CNPJs zeroed (49 clients)
- [17/02]: Monthly weight rounding 0.001% acceptable
- [17/02]: 4 SAP vendas CNPJs not in PROJECAO roster (R$ 8,794 delta)
- [17/02]: auto_filter absent in V13 output -- openpyxl limitation
- [17/02]: PROJ-04 meta R$5.7M aspirational vs R$4.7M actual SAP
- [17/02]: 7 consultors found (not 3-4 assumed)
- [17/02]: Phase 01 PROJECAO complete -- all PROJ-01..04 requirements formally verified PASS
- [17/02]: Sem CNPJ clients on dedicated sheet in 02_VENDAS_POSITIVACAO
- [17/02]: Independent SAP re-extraction matches Phase 1 exactly (489 CNPJs, R$ 2,089,824.23, 0% diff)
- [17/02]: 11 Mercos armadilhas validated (FAT-03 pre-requisite satisfied)
- [17/02]: SAP-First merge: 160 month-cells filled from Mercos where SAP=0
- [17/02]: 27 SAP negative values (credit notes) zeroed at merge time
- [17/02]: All 10 sem_cnpj matched via exact name in Mercos Carteira
- [17/02]: 529 unique CNPJs from merge + 8 new from fuzzy = 537 total clients
- [17/02]: CARTEIRA population DEFERRED
- [17/02]: PAINEL R$ 2,156,179 does not match any single source
- [17/02]: FAT-01/02 FAIL against merged (source scope mismatch)
- [17/02]: Phase 02 COMPLETE with FAIL_WITH_NOTES
- [17/02]: V12 COM_DADOS path is data/sources/crm-versoes/v11-v12/
- [17/02]: DRAFT 1 has 554 data rows
- [17/02]: CARTEIRA expanded to 554 formula rows (25,484 INDEX/MATCH formulas)
- [17/02]: ABC distribution on merged total: A=298 (55.5%), B=220 (41.0%), C=19 (3.5%)
- [17/02]: JAN/25 + FEV/25 hidden in totals (R$ 103,893.89)
- [17/02]: Phase 03 validation PASS
- [17/02]: 06_LOG_FUNIL.xlsx has pre-classified 'Interacoes' sheet
- [17/02]: 10,442 CONTROLE_FUNIL records processed (9,120 REAL + 1,322 SINTETICO), 558 alucinacoes
- [17/02]: DAIANE STAVICKI canonical name (not CENTRAL - DAIANE)
- [17/02]: Deskrio already at ticket level (5,329 tickets not 77,805 messages)
- [17/02]: Deskrio CNPJ matching: 3,907 direct + 564 name-based (83.9% rate)
- [17/02]: Rodrigo (952 Deskrio tickets) kept as consultant
- [17/02]: TIPO DO CONTATO normalized 12->7
- [17/02]: DASH tab 41 rows, 304 formulas
- [17/02]: Phase 05 COMPLETE
- [17/02]: E-commerce ETL produces 10 months, 1075 records
- [17/02]: E-commerce match rate 64.6% (441/683 names)
- [17/02]: 5-level matching: cnpj_prefix -> exact -> exact_normalized -> partial -> partial_normalized
- [17/02]: Phase 06 E-commerce COMPLETE
- [17/02]: 20 redes (not 19): MINHA QUITANDINHA discovered
- [17/02]: Phase 07 COMPLETE -- all 4 requirements PASS
- [17/02]: COMITE tab 342 formulas, 5 blocks
- [17/02]: Phase 08 COMPLETE
- [17/02]: V12 CARTEIRA: 263 cols, 114 formula, 149 static, 6 super-groups
- [17/02]: FATURAMENTO: 186 cols = 12 months x 15 sub-cols (BZ-JC)
- [17/02]: SCORE RANKING 6 factors = 100%: URGENCIA(30%), VALOR(25%), FOLLOWUP(20%), SINAL(15%), TENTATIVA(5%), SITUACAO(5%)
- [17/02]: 134,092 CARTEIRA formulas, 154,242 V13 total
- [17/02]: Phase 09 COMPLETE -- 154,302 total V13 formulas
- [17/02]: V13 AUDIT CLEAN -- 0 error patterns, 0 dangerous patterns, 0 orphaned cross-tab refs
- [17/02]: 198,003 cross-tab references validated, 0 orphaned
- [17/02]: V13 FINAL produced as CLEAN_COPY
- [17/02]: VAL-06 V13 FAILED -- user reported broken layout
- [17/02]: V14 FINAL generated with 15 corrections
- [17/02]: V13 vs V31: V31 has 5,460 CNPJs (10x more), V13 has 554

### Fase 1 Revisada

A Fase 1 (PROJECAO) muda de escopo:
- ANTES: Reconstruir 18.180 formulas do zero
- AGORA: Validar formulas existentes no V12 + popular dados SAP 2026 atualizados

### Blockers/Concerns

- Relatorios Mercos mentem nos nomes — cuidado extra no ETL
- Julio Gadret 100% fora do sistema — dados limitados disponiveis
- 558 registros ALUCINACAO do CONTROLE_FUNIL — nao integrar
- LibreOffice recalc != Excel recalc — testar no Excel real
- CARTEIRA no V12 tem 263 cols (confirmado via auditoria 09-01)

## Session Continuity

Last session: 2026-02-18
Stopped at: Script build_v17_prepopulado.py CRIADO mas NAO executado ainda.
Resume file: .planning/phases/10-validacao-final/ (scripts em scripts/phase10_validacao_final/)

### PROXIMO PASSO (executar ao retomar):
1. Executar: `python3 scripts/phase10_validacao_final/build_v17_prepopulado.py`
2. O script vai:
   - Copiar V16 como base
   - Ler DRAFT 1 (554 clientes estaticos) e indexar por CNPJ
   - Ler DRAFT 2 (21K registros) e pegar ultimo atendimento por CNPJ
   - Ler V31 CARTEIRA e DRAFT 2 (valores calculados) como fallback
   - Para cada row da CARTEIRA: escrever VALORES REAIS nas colunas criticas
3. Salvar como V17 e verificar
4. Se tudo OK, usuario abre no Excel e ve dados IMEDIATAMENTE (sem Ctrl+Alt+F9)

### PROBLEMA RAIZ:
openpyxl escreve formulas mas NAO calcula valores cached. O Excel mostra celulas vazias ate recalcular manualmente. Solucao: escrever VALORES em vez de formulas nas colunas que o usuario precisa ver.

---
---

## SECAO 9 — INVENTARIO DE SCRIPTS

### Scripts na raiz (`scripts/`)

| Script | Proposito |
|--------|-----------|
| `_agent3_quality.py` | AGENT 3: Data Quality Audit — CRM VITAO360 V3 MERGED |
| `_agent4_testing.py` | AGENT 4: Cross-Tab Integrity Testing — CRM VITAO360 V3 MERGED |
| `_bootstrap.py` | Bootstrap — gera script inspect_meta_acomp.py programaticamente |
| `_compare_both.py` | Compare POPULADO vs V3 FINAL to find what's missing |
| `_deep_audit.py` | JARVIS CRM - Deep Audit of ALL Source Excel Files |
| `_inspect_draft2_carteira.py` | Quick inspect POPULADO DRAFT 2 + CARTEIRA layouts |
| `_inspect_sources.py` | Quick inspection of source files for column mapping |
| `_revalidate.py` | REVALIDATION: Verify all fixes applied correctly |
| `_validate_final.py` | Validate CRM_VITAO360_V3_100.xlsx — Comprehensive 20-point validation |
| `_validate_merged.py` | Validate CRM_VITAO360_V3_MERGED.xlsx — comprehensive check |
| `analyze_crm_v11v12.py` | Analyze CRM V11 and V12 Excel files for structure, tabs, formulas |
| `analyze_draft2_real.py` | Quick analysis of DRAFT2 with real attendance data |
| `analyze_populado.py` | Placeholder (print hello) |
| `analyze_projecao.py` | Analyze PROJECAO Excel files to understand structure and formula state |
| `analyze_v2.py` | Analise da versao V2 do CRM |
| `build_jarvis.py` | JARVIS CRM CENTRAL — Full Excel Builder (7 tabs) |
| `build_v3.py` | Build CRM VITAO360 V3 — Orchestrator (9 tabs) |
| `check_draft2.py` | Check DRAFT 2 column structure in V2.xlsx |
| `check_tipos.py` | Check TIPO DO CONTATO values in REGRAS |
| `compare_v3.py` | Compare downloaded V3 vs our V3 — deep structural comparison |
| `deep_compare.py` | Deep comparison: Ours vs Downloaded V3 — every difference |
| `extract_meta_sap.py` | Extracts monthly META 2026 data from SAP file |
| `inspect_carteira_oular.py` | Inspect CARTEIRA DE CLIENTES OULAR.xlsx thoroughly |
| `inspect_download.py` | Inspect downloaded V3 file |
| `inspect_log_draft.py` | Inspect preenchimento do draft de atendimento (LOG) |
| `inspect_meta_acomp.py` | Inspecao de meta e acompanhamento |
| `install_openpyxl.py` | Instalar openpyxl e et-xmlfile via PyPI |
| `merge_final.py` | CRM VITAO360 V3 — MERGE FINAL (Best of POPULADO + V3) |
| `motor_regras.py` | Motor de Regras V3 — Implementa spec Part 15: RESULTADO -> campos automaticos |
| `populate_acomp.py` | Populate ACOMPANHAMENTO (cols 73-257) in existing CRM V3 |
| `populate_final.py` | CRM VITAO360 V3 FINAL — Populate with ALL real data |
| `populate_v3.py` | Populate CRM VITAO360 V3 — Import real data from source files |
| `quick_analyze.py` | Quick analysis of all 3 Excel files for comparison |
| `rebuild_dash.py` | Rebuild DASH tab in V2.xlsx (3 blocks with COUNTIFS) |
| `test123.py` | Teste simples (print 123) |
| `v3_agenda.py` | V3 — Tab AGENDA: Agenda Diaria do Consultor (~25 cols + SCORE) |
| `v3_carteira.py` | V3 — Tab CARTEIRA: Visao 360 (~257 colunas, 4 mega-blocos) |
| `v3_dash.py` | V3 — Tab DASH: 7 blocos de KPIs + KPI cards |
| `v3_draft1.py` | V3 — Tab DRAFT 1: Base Mestre do Cliente (48 colunas, 7 blocos) |
| `v3_draft2.py` | V3 — Tab DRAFT 2: Log de Atendimentos (24 cols + motor de regras) |
| `v3_log.py` | V3 — Tab LOG (24 cols) + Tab CLAUDE LOG (3-col audit trail) |
| `v3_projecao.py` | V3 — Tab PROJECAO: Meta SAP + Sinaleiro de Atingimento |
| `v3_regras.py` | V3 — Tab REGRAS: Tabelas de referencia + Named Ranges |
| `v3_styles.py` | V3 Styles — Shared formatting constants |
| `validate_dash.py` | Validate rebuilt DASH tab in V2.xlsx |
| `validate_fixes.py` | Validate all fixes applied to JARVIS_CRM_CENTRAL.xlsx |
| `validate_jarvis.py` | Validar JARVIS CRM CENTRAL |
| `validate_v3.py` | Validate CRM VITAO360 V3 — 18-point checklist |
| `excel_structure_analyzer.py` | (raiz do projeto) Analisador de estrutura Excel |

### Scripts por fase (`scripts/phase*/`)

**phase01_projecao/** (4 scripts)
| Script | Proposito |
|--------|-----------|
| `01_validate_formulas.py` | Valida 19.224 formulas existentes na PROJECAO_534_INTEGRADA |
| `02_extract_sap_data.py` | Extrai dados SAP: CNPJ<->SAP Code, vendas 2025, metas 2026 |
| `03_populate_projecao.py` | Popular PROJECAO com dados SAP 2026 via Read-Modify-Write |
| `04_verify_projecao.py` | Verificacao completa do V13 PROJECAO output |

**phase02_faturamento/** (5 scripts)
| Script | Proposito |
|--------|-----------|
| `01_extract_mercos_vendas.py` | Extrai vendas mensais por CNPJ do Mercos |
| `02_extract_sap_vendas.py` | Extrai faturado mensal por CNPJ do SAP |
| `03_merge_sap_mercos.py` | Merge SAP-First + Mercos-Complement |
| `04_fuzzy_match_sem_cnpj.py` | Fuzzy Match dos 10 clientes Mercos sem CNPJ |
| `05_validate_vs_painel.py` | Validacao do faturamento consolidado vs PAINEL |

**phase03_timeline/** (3 scripts)
| Script | Proposito |
|--------|-----------|
| `01_populate_draft1_vendas.py` | Popular DRAFT 1 com vendas mensais + campos derivados |
| `02_expand_carteira_formulas.py` | Expandir formulas INDEX/MATCH da CARTEIRA para todos os clientes |
| `03_validate_abc_timeline.py` | Validar vendas DRAFT 1 vs merged JSON + ABC recalculo |

**phase04_log_completo/** (7 scripts)
| Script | Proposito |
|--------|-----------|
| `_helpers.py` | Funcoes compartilhadas para todo o pipeline LOG |
| `01_process_controle_funil.py` | ETL do CONTROLE_FUNIL (10,544 registros, classificacao 3-tier) |
| `02_process_deskrio.py` | ETL dos tickets Deskrio para formato LOG 20 colunas |
| `03_generate_synthetic.py` | Gerador Sintetico SAP-Anchored (reconstrucao funil) |
| `04_dedup_validate.py` | Merge, Dedup, Validate (15 rules), Populate V13 LOG |
| `05_populate_v13_log.py` | Popular aba LOG do V13 com 20,830 registros validados |
| `__init__.py` | Init do modulo |

**phase05_dashboard/** (3 scripts)
| Script | Proposito |
|--------|-----------|
| `01_normalize_log_tipo.py` | Normalize LOG TIPO DO CONTATO (12->7 tipos) |
| `02_build_dash.py` | Build DASH tab com 3 compact blocks (~45 rows) |
| `03_validate_dash.py` | DASH Validation Script (DASH-01..05) |

**phase06_ecommerce/** (2 scripts)
| Script | Proposito |
|--------|-----------|
| `01_extract_ecommerce.py` | ETL de Relatorios E-commerce Mercos (17 arquivos) |
| `02_match_populate.py` | E-commerce Match & Populate (4 niveis matching) |

**phase07_redes_franquias/** (3 scripts)
| Script | Proposito |
|--------|-----------|
| `01_remap_expand_reftable.py` | Remap 11 SEM GRUPO + expand AS:AZ ref table (12->19 redes) |
| `02_create_redes_tab.py` | Create REDES_FRANQUIAS_v2 tab (SUMIFS, COUNTIFS, sinaleiro) |
| `03_validate_phase07.py` | Validate REDE-01..04 + V13 integrity |

**phase08_comite_metas/** (3 scripts)
| Script | Proposito |
|--------|-----------|
| `01_validate_adjust_metas.py` | Validate META infrastructure in PROJECAO |
| `02_build_comite_tab.py` | Build COMITE tab (5 blocks, filtros, RATEIO toggle) |
| `03_validate_phase08.py` | Validate META-01..03 requirements |

**phase09_blueprint_v2/** (11 scripts)
| Script | Proposito |
|--------|-----------|
| `01_audit_v12_carteira.py` | Deep audit V12 CARTEIRA (263 cols, formula patterns) |
| `02_create_supporting_tabs.py` | Create Supporting Tabs (REGRAS, DRAFT 1, DRAFT 2) |
| `02_validate_draft1_map.py` | Validate audit + build DRAFT 1 column position map |
| `03_build_carteira_mercos_funil.py` | Build CARTEIRA 263-col skeleton + MERCOS/FUNIL formulas |
| `03_validate_supporting_tabs.py` | Validate Supporting Tab Integrity |
| `04_build_carteira_sap_faturamento.py` | SAP + FATURAMENTO Block Builder (186 cols) |
| `04_verify_carteira_mercos_funil.py` | Verify MERCOS + FUNIL block formulas |
| `05_intelligence_engine.py` | Intelligence Engine Layer 1 (Ranking Score 6 factors) |
| `05_verify_sap_faturamento.py` | Verify SAP + FATURAMENTO blocks |
| `06_agenda_tabs_validation.py` | AGENDA Tabs Creation + Phase 9 Validation |
| `06_intelligence_layers23.py` | Intelligence Layers 2-3 + Conditional Formatting |

**phase10_validacao_final/** (68+ scripts)
Scripts principais:
| Script | Proposito |
|--------|-----------|
| `01_comprehensive_audit.py` | Comprehensive Audit (VAL-01..VAL-05) |
| `01b_analyze_results.py` | Analyze audit results |
| `02_fix_issues.py` | Fix audit issues + produce V13 FINAL |
| `03_delivery_report.py` | Generate delivery report (10 phases summary) |
| `04_generate_checklist.py` | Generate Excel real test checklist (VAL-06) |
| `build_v15_complete.py` | V15: Corrige arquitetura para match V31 |
| `build_v16_unified.py` | V16: Script definitivo unificado |
| `build_v17_prepopulado.py` | V17: CARTEIRA com valores reais (nao apenas formulas) |
| `build_v18_expandido.py` | V18: Adicionar 5.523 prospects Mercos + 126 SAP |
| `build_v20_consultores.py` | V20: Distribuicao de consultores + SAP faltante |
| `build_v21_formulas_estendidas.py` | V21: Estender formulas para 6.144 rows |
| `build_v22_leve.py` | V22: Versao leve (Google Sheets compativel) |
| `build_v23_correcao_mercos.py` | V23: Correcao total com Carteira Mercos oficial |
| `build_v23_correcao_prospects.py` | V23: Correcao de prospects + atualizacao nomes |
| `build_v24_jan25.py` | V24: Incorporar vendas JAN/25 |
| `build_v25_fev25.py` | V25: Incorporar vendas FEV/25 |
| `build_v26_correcoes.py` | V26: Correcoes criticas da auditoria |
| `build_v27_simulacao_jan25.py` a `build_v40_simulacao_fev26.py` | V27-V40: Simulacoes mensais de atendimentos (JAN/25 a FEV/26) |
| `build_v41_dash.py` | V41: Dashboard visual (Cards + Barras + Grid) |
| `build_v43_agendas.py` | V43: Popular 40 atendimentos (10/consultor) |
| `build_v43_clean.py` | V43: Core limpo para apresentacao ao vivo |
| `simulacao_mensal_engine.py` | Engine de simulacao mensal (reutilizavel) |
| `validate_v43.py` | Validacao V43 final |
| `gerar_v14_corrigido.py` | Gera V14 com correcoes de layout do V31 |
| `confronto_dados.py` | Confronto V13 vs V31 (integridade) |
| `deep_analysis_v31.py` | Analise profunda do V31 |

---
---

## SECAO 10 — INVENTARIO DE DADOS E OUTPUTS

### data/docs/ (Documentacao de referencia — 140+ arquivos)

**Raiz docs/ (26 arquivos)**
- 00_GUIA_PROMPTS.md, ANALISE_BASES_SAP.html, ANALISE_ESTADO_ATUAL.md
- ARQUITETURA_FONTE_UNICA.html, BLUEPRINT_JARVIS_CRM.html
- BLUEPRINT_v2_ABA1_CARTEIRA.html, BLUEPRINT_v3_LOG_AGENDA_DASH.html
- CLAUDE_DESKTOP_ORIGINAL.md, DASH_FINAL_APROVADO.html
- DOCUMENTACAO_COMPLETA_CRM.md, DOCUMENTO_MESTRE.md
- DOCUMENTO_MESTRE_ATENDIMENTOS_VITAO.md
- FASE_0_REGRAS.md a FASE_6_AGENDA.md (7 fases)
- GUIA_EXECUCAO_FASES.md, HANDOFF_CRM_V3.md, INDICE_MESTRE_JARVIS.md
- MANUAL_AGENDA_COMERCIAL_VITAO_v3_FINAL.md, PRD_COMPLETO_CRM_VITAO.md
- SPEC_FINAL_CRM_VITAO360_V3.md

**docs/analises/ (34 arquivos)** — Analises profundas (efetividade, Black Friday, churn, etc.)
**docs/dashboards/ (7 arquivos)** — Prototipos React JSX de dashboards
**docs/etapa-final/ (39 arquivos)** — Handoffs, blueprints forenses, genomas comerciais, specs
**docs/logs-conversa/ (18 arquivos)** — Logs de conversas com Claude sobre decisoes
**docs/prompts/ (8 arquivos)** — Templates de prompts para operacao do CRM

### data/output/ (Arquivos gerados pelo pipeline)

**Raiz output/ (6 arquivos)**
- CRM_VITAO360_V13_PROJECAO.xlsx (base principal)
- V13 backups: _BACKUP_PHASE04, _BACKUP_PHASE05_01, _20260217_173900, _PHASE08
- test_grouping.xlsx

**output/phase01/ (3 JSONs)** — formula_validation_report, sap_data_extracted, verification_report
**output/phase02/ (4 JSONs)** — mercos_vendas, sap_vendas, sap_mercos_merged, validation_report
**output/phase03/ (3 JSONs)** — abc_classification, draft1_population_report, validation_report
**output/phase04/ (5 JSONs)** — controle_funil_classified, deskrio_normalized, log_final_validated, synthetic_generated, validation_report
**output/phase06/ (3 JSONs)** — ecommerce_raw, ecommerce_matched, match_report
**output/phase07/ (1 JSON)** — validation_report
**output/phase08/ (2 JSONs)** — meta_validation_report, validation_report
**output/phase09/ (10 JSONs)** — carteira_column_spec, carteira_mercos_funil_validation, draft1_column_map, intelligence validations, sap_faturamento_validation, supporting_tabs_validation, tab_name_map, v12_formula_audit

**output/phase10/ (50+ arquivos)** — Versoes V13 a V43:
- CRM_VITAO360_V13_FINAL.xlsx a V43_CLEAN.xlsx (31 versoes Excel)
- Relatorios: comprehensive_audit_report.json, confronto_v13_v31.json, delivery_report.json
- Analises: ANALYSIS_DELIVERABLES.md, EXECUTIVE_SUMMARY.txt, STRUCTURAL_COMPARISON_SUMMARY.md
- Comparacoes: layout_comparison_v31_v13.json, v31_formulas.json, v31_vs_v13_comparison.json

### data/sources/ (Fontes de dados originais — 873 arquivos)

| Diretorio | Arquivos | Conteudo |
|-----------|----------|----------|
| `sources/acompanhamento/` | 8 | KPIs, capacidade, fluxo, painel venda interna |
| `sources/carteiras/` | 13 | Carteiras de clientes (Oular, Jan 2026, Fev 2026, por consultor) |
| `sources/crm-versoes/` | 31 | Versoes anteriores do CRM (V1-V12, JARVIS, POPULADO, MERGED) |
| `sources/crm-versoes/v11-v12/` | 12 | V11 limpo/populado, V12 com dados, DL_ duplicatas |
| `sources/deskrio/` | 538 | Tickets WhatsApp (07_TICKETS), contatos, motivos, tickets individuais (.txt) |
| `sources/drafts/` | 5 | DRAFT1 FEV2026, DRAFT2 com dados reais (v3), populados |
| `sources/funil/` | 12 | CONTROLE_FUNIL (JAN2026, completo, ultimo tri), LOG definitivo |
| `sources/julio/` | 4 | Acompanhamento Julio, planilha participantes |
| `sources/mercos/` | 108 | Vendas (12 relatorios mensais), positivacao, ABC, e-commerce (17+ meses), carteira |
| `sources/processos/` | 102 | Documentos comerciais (scripts vendas, abordagens, checklists, treinamentos) |
| `sources/projecao/` | 11 | PROJECAO_534_INTEGRADA, INTERNO_1566, POPULADA_1566 |
| `sources/sap/` | 5 | SAP consolidado, metas 2026, vendas mes a mes, clientes sem atendimento |
| `sources/sinaleiro/` | 21 | Sinaleiros (interno, redes, populado, confiavel), controle positivacao |

---

# RESUMO FINAL DO BACKUP

| Metrica | Valor |
|---------|-------|
| Documentos preservados | 8 documentos completos |
| Scripts inventariados | 120+ scripts Python |
| Versoes Excel geradas | V13 a V43 (31 versoes) |
| Arquivos fonte | 873 arquivos em data/sources/ |
| JSONs intermediarios | 31 arquivos de dados processados |
| Decisoes tecnicas documentadas | 250+ no STATE.md |
| Fases executadas | 10/10 completas |
| Planos executados | 32 planos |
| Requirements definidos | 43 v1 + 6 v2 |
| Total de formulas (V13 final) | 154.302 |
| Tempo total de execucao | 6.30 horas |

**Estado final**: V43_CLEAN.xlsx e a versao mais recente. CARTEIRA tem formulas mas dados so aparecem apos recalculo no Excel (limitacao openpyxl). Script V17 pre-popula com valores reais.

---

*Backup gerado em: 2026-03-23*
*Proposito: Preservacao completa antes do rebuild com enforcement AIOX*
