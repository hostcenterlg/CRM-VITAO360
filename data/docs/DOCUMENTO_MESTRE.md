# JARVIS CRM — DOCUMENTO MESTRE DEFINITIVO
## Fonte Única da Verdade do Projeto

**Versão:** 1.0 FINAL  
**Data:** 08/02/2026  
**Autor:** Leandro Garcia × Claude Opus  
**Empresa:** VITAO Alimentos — Canal Venda Interna B2B  

---

## SUMÁRIO

1. [EVOLUÇÃO DO PROJETO — O QUE ACONTECEU](#1-evolução-do-projeto)
2. [INVENTÁRIO DE ARTEFATOS — O QUE É OFICIAL](#2-inventário-de-artefatos)
3. [FASE 1 — CARTEIRA DE CLIENTES (Blueprint v2)](#3-fase-1--carteira-de-clientes)
4. [FASE 2 — LOG + AGENDA + DRAFT (Blueprint v3)](#4-fase-2--log--agenda--draft)
5. [FASE 3 — DASHBOARDS](#5-fase-3--dashboards)
6. [FASE 4 — REGRAS DE NEGÓCIO](#6-fase-4--regras-de-negócio)
7. [PIPELINE ETL — EXTRAÇÃO E TRATAMENTO](#7-pipeline-etl)
8. [ANOMALIAS CONHECIDAS](#8-anomalias-conhecidas)
9. [ROADMAP DE IMPLEMENTAÇÃO](#9-roadmap-de-implementação)

---

# 1. EVOLUÇÃO DO PROJETO

### Linha do tempo da conversa de construção (06-08/Fev/2026)

| ETAPA | DATA | O QUE ACONTECEU | DECISÃO-CHAVE |
|-------|------|-----------------|---------------|
| 1 | 06/Fev manhã | Frustração com LOG/CRM bagunçados. Planilhas de vai e vem sem solução | Começar do zero, arrumar estrutura |
| 2 | 06/Fev | Estratégia de 3 documentos (Agenda, Controle Diário, Dash Gerencial) | Separar responsabilidades |
| 3 | 06/Fev | Evolução: 3 docs separados → ARQUIVO ÚNICO com filtros e agrupamentos | Fonte única da verdade com [+] expansíveis |
| 4 | 06/Fev | Análise dos 4 arquivos SAP (1.701 CNPJs, zero overlap) | Two-Base: COM_VENDA + SEM_ATENDIMENTO = universo completo |
| 5 | 07/Fev manhã | Design da ABA 1 CARTEIRA: 10 colunas fixas + 8 grupos [+] | 81 colunas totais, 18 visíveis tudo fechado |
| 6 | 07/Fev | Sistema FASE + TENTATIVA (cadência T1→T4→Nutrição) | Cada atendimento gera ação futura automática |
| 7 | 07/Fev | Bloco COMITÊ para reunião de quarta (Meta × Realizado × Justificativa) | % Ating. Mês como coluna visível do [+8] |
| 8 | 07/Fev | Versão 10/10: SINALEIRO 🟢🟡🔴🟣 + PRIORIDADE (score 1-100) | 4 melhorias finais aplicadas |
| 9 | 07/Fev | Análise de 4 arquivos de referência (CRM Food, Manu, Gestão Tempo, Rotina) | Best-of-breed de cada sistema |
| 10 | 07/Fev | Blueprint v3: LOG (20 cols) + AGENDA (24 cols) + DRAFT 2 + DASH (7 seções) | Consultor nunca toca o LOG |
| 11 | 07/Fev tarde | Pipeline ETL: 9 prompts de extração e tratamento | 88 arquivos → 8 staging → GOLDEN |
| 12 | 07/Fev | Classificação 3-tier: REAL / SINTÉTICO / ALUCINAÇÃO para dados do LOG | Preservar dados sintéticos como aproximação |
| 13 | 08/Fev manhã | Auditoria AIOS/GSM: Score 87.4% (BRONZE) | 3 ações para chegar a 95%+ (SILVER) |
| 14 | 08/Fev | Tentativa de gerar Excel completo → reconheceu risco de alucinação | Decisão: fazer passo a passo, fase por fase |
| 15 | 08/Fev | **ESTE DOCUMENTO** — organizar tudo, criar fonte única da verdade | Parar, organizar, depois construir |

### Decisões arquiteturais irreversíveis (não mudam mais)

1. **ARQUIVO ÚNICO** — Todo o CRM vive em 1 Excel com abas e filtros
2. **TWO-BASE** — Valores financeiros NUNCA no LOG (evita duplicação 742%)
3. **DRAFT como quarentena** — Nada entra no LOG sem validação
4. **[+] Expansíveis** — Dados agrupados com botões Excel, minimizáveis
5. **Consultor nunca toca o LOG** — Recebe agenda, devolve preenchida, Leandro cola no DRAFT
6. **CNPJ como chave primária** — 14 dígitos, UNIQUE, 1 linha = 1 cliente
7. **Zero fabricação** — Dados reais ou flaggados como sintéticos, nunca inventados
8. **Tema claro** — Todos os outputs em light mode, nunca dark
9. **Nomes originais das fontes** — SAP com cara de SAP, Mercos com cara de Mercos nos staging

---

# 2. INVENTÁRIO DE ARTEFATOS

### Status de cada documento gerado na conversa

| # | ARTEFATO | STATUS | OBSERVAÇÃO |
|---|----------|--------|------------|
| 1 | ANALISE_BASES_SAP.html | 🟡 PRECURSOR | Análise válida, incorporada no Blueprint v2 |
| 2 | ARQUITETURA_FONTE_UNICA.html | 🟡 PRECURSOR | Conceito inicial, superado pelo Blueprint v2 |
| 3 | BLUEPRINT_JARVIS_CRM.html | ⛔ SUPERADO | v1 com 49 colunas, substituído pelo v2 (81 cols) |
| 4 | **BLUEPRINT_v2_ABA1_CARTEIRA.html** | ✅ **OFICIAL** | Especificação definitiva da ABA 1 |
| 5 | **BLUEPRINT_v3_LOG_AGENDA_DASH.html** | ✅ **OFICIAL** | Especificação definitiva de LOG, AGENDA, DASH, REGRAS |
| 6 | KICKOFF_JARVIS_IMPLEMENTACAO.md | 🟡 COMPLEMENTAR | Resumo executivo, referencia v2 e v3 |
| 7 | 00_GUIA_PROMPTS.md | ✅ **OFICIAL** | Mapa dos 9 prompts ETL |
| 8 | PROMPTS_ETL_JARVIS.md | ✅ **OFICIAL** | Os 9 prompts completos |
| 9 | AUDITORIA_AIOS_GSM.md | 🟡 COMPLEMENTAR | Snapshot de qualidade |
| 10 | orchestrator_config.yaml | ✅ **OFICIAL** | Equipe, territórios, regras |
| 11 | PRD_COMPLETO_CRM_VITAO.md | ✅ **OFICIAL** | Requisitos do produto (histórico) |
| 12 | DOCUMENTACAO_COMPLETA_CRM.md | ✅ **OFICIAL** | Referência técnica, funis, cadências |
| 13 | MANUAL_AGENDA_v3_FINAL.md | ⚠️ PARCIAL | 20 colunas — superado pela AGENDA de 24 cols do v3 |
| 14 | DOCUMENTO_MESTRE_ATENDIMENTOS.md | ✅ **OFICIAL** | 21.965 interações, padrões WhatsApp |
| 15 | 9 prompts .txt individuais | ✅ **OFICIAL** | Cada prompt de extração ETL |

### O que usar para construir

Para construir o JARVIS_CRM_CENTRAL.xlsx, os documentos obrigatórios são:

```
OBRIGATÓRIOS (sem eles não constrói):
├── BLUEPRINT_v2_ABA1_CARTEIRA.html    ← ABA 1: 81 colunas, 8 grupos
├── BLUEPRINT_v3_LOG_AGENDA_DASH.html  ← ABAs 2-7: LOG, AGENDA, DRAFT, DASH, REGRAS
└── orchestrator_config.yaml           ← Equipe, territórios, regras de atribuição

REFERÊNCIA (consultar quando necessário):
├── DOCUMENTACAO_COMPLETA_CRM.md       ← Funis, cadências, Two-Base
├── DOCUMENTO_MESTRE_ATENDIMENTOS.md   ← Padrões WhatsApp, volumes
└── PRD_COMPLETO_CRM_VITAO.md         ← Requisitos formais

DADOS (alimentar o Excel):
├── 8 arquivos staging (das extrações ETL)
└── Excels brutos do projeto (SAP, Mercos, Carteira, etc.)
```

---

# 3. FASE 1 — CARTEIRA DE CLIENTES

**Fonte:** BLUEPRINT_v2_ABA1_CARTEIRA.html  
**ABA:** CARTEIRA (primeira aba do arquivo central)  
**Função:** Fonte única da verdade sobre TODOS os clientes  

### 3.1 Colunas sempre visíveis (A-J) — CONGELADAS

| COL | NOME | TIPO | EXEMPLO | REGRA |
|-----|------|------|---------|-------|
| A | NOME FANTASIA | TEXT | DIVINA TERRA CURITIBA | Mercos col 4 → SAP. UPPER |
| B | REDE / REGIONAL | TEXT | DIVINA TERRA | Se tem rede → nome. Se não → região (SUL/SUDESTE/etc). Nunca vazio |
| C | UF | TEXT(2) | PR | 27 UFs válidas |
| D | CONSULTOR | TEXT | DAIANE | Regra: CIA DA SAUDE/FIT LAND→JULIO. Outras redes→DAIANE. SC/PR/RS sem rede→MANU. Resto→LARISSA |
| E | SITUAÇÃO | TEXT | ATIVO | Calculada por DIAS SEM COMPRA (ver regras seção 6) |
| F | DIAS SEM COMPRA | INT | 12 | HOJE - DATA_ÚLTIMO_PEDIDO |
| G | 🚦 SINALEIRO | EMOJI | 🟢 | 🟢 ≤ ciclo, 🟡 ciclo+1 a ciclo+30, 🔴 > ciclo+30, 🟣 nunca comprou |
| H | TIPO CLIENTE | TEXT | EM DESENVOLVIMENTO | NOVO/EM DESENVOLVIMENTO/RECORRENTE/FIDELIZADO/PROSPECT/LEAD |
| I | FASE | TEXT | CS | PÓS-VENDA/CS/RECOMPRA/SALVAMENTO/RECUPERAÇÃO/PROSPECÇÃO/NUTRIÇÃO/EM ATENDIMENTO/ORÇAMENTO |
| J | TENTATIVA | TEXT | T1 | T1(WhatsApp) → T2(Ligação +1d) → T3(WhatsApp +2d) → T4(Ligação +2d) → NUTRIÇÃO |

### 3.2 Grupos expansíveis [+]

#### [+1] IDENTIDADE — Cols K a Q (7 colunas)
Visível quando fechado: **K = CNPJ**

| COL | CAMPO | TIPO | FONTE |
|-----|-------|------|-------|
| K | CNPJ | TEXT(14) | Mercos/SAP. Chave primária universal |
| L | RAZÃO SOCIAL | TEXT | Carteira col 3 |
| M | CIDADE | TEXT | Carteira col 6 |
| N | EMAIL | TEXT | Carteira col 8 |
| O | TELEFONE | TEXT | Carteira col 7. Formato: 55+DDD+num |
| P | COD_FONTE | TEXT | SAP_ATIVO / SAP_INATIVO / MERCOS / PROSPECT / REDE_ONLY / LEAD_MANUAL |
| Q | DATA CADASTRO | DATE | Carteira col 16 |

#### [+2] VIDA COMERCIAL — Cols R a Z (9 colunas)
Visível quando fechado: **R = CICLO MÉDIO**

| COL | CAMPO | TIPO | FONTE |
|-----|-------|------|-------|
| R | CICLO MÉDIO | NUM | Carteira col 13. Sem dado = 45 dias padrão |
| S | DATA ÚLTIMO PEDIDO | DATE | Carteira col 14 |
| T | VALOR ÚLTIMO PEDIDO | MONEY | Carteira col 15 |
| U | VENDEDOR ÚLTIMO PEDIDO | TEXT | Carteira col 17 |
| V | Nº DE COMPRAS | INT | Carteira col 18 |
| W | CURVA ABC | TEXT(1) | Carteira col 38 (A/B/C) |
| X | TICKET MÉDIO | MONEY | = TOTAL_PERÍODO / Nº_COMPRAS |
| Y | MESES POSITIVADO | INT | Carteira col 20 |
| Z | MÉDIA MENSAL | MONEY | = TOTAL_PERÍODO / MESES_POSITIVADO |

#### [+3] TIMELINE MENSAL — Cols AA a AM (13 colunas)
Visível quando fechado: **AA = TOTAL PERÍODO (R$)**

| COL | CAMPO | FONTE |
|-----|-------|-------|
| AA | TOTAL PERÍODO | Carteira col 33 |
| AB | MAR/25 | Carteira col 22 |
| AC | ABR/25 | Carteira col 23 |
| AD | MAI/25 | Carteira col 24 |
| AE | JUN/25 | Carteira col 25 |
| AF | JUL/25 | Carteira col 26 |
| AG | AGO/25 | Carteira col 27 |
| AH | SET/25 | Carteira col 28 |
| AI | OUT/25 | Carteira col 29 |
| AJ | NOV/25 | Carteira col 30 |
| AK | DEZ/25 | Carteira col 31 |
| AL | JAN/26 | Carteira col 32 |
| AM | MESES LISTA | Carteira col 21. Texto: "JAN/26, OUT/25, SET/25" |

Evolução: quando FEV/26 fechar, adicionar col AN. TOTAL PERÍODO se atualiza automaticamente.

#### [+4] JORNADA DO CLIENTE — Cols AN a AS (6 colunas)
Visível quando fechado: **AN = DIAS ATÉ CONVERSÃO**

⚠️ BLOCO NOVO — minerado do LOG. Campos sem dados ficam vazios.

| COL | CAMPO | COMO POPULAR |
|-----|-------|-------------|
| AN | DIAS ATÉ CONVERSÃO | = DATA_1ª_VENDA - DATA_1º_CONTATO |
| AO | DATA 1º CONTATO | MIN(DATA) no LOG para este CNPJ |
| AP | DATA 1º ORÇAMENTO | MIN(DATA) no LOG onde RESULTADO="ORÇAMENTO" |
| AQ | DATA 1ª VENDA | MIN(DATA) no LOG onde RESULTADO="VENDA" |
| AR | TOTAL TENTATIVAS ATÉ VENDA | COUNT no LOG entre 1º contato e 1ª venda |
| AS | DATA ÚLTIMA RECOMPRA | MAX(DATA) no LOG onde RESULTADO="VENDA" e DATA > 1ª venda |

#### [+5] ECOMMERCE — Cols AT a AX (5 colunas)
Visível quando fechado: **AT = ACESSO B2B**

| COL | CAMPO | FONTE |
|-----|-------|-------|
| AT | ACESSO B2B | SIM/NÃO |
| AU | ACESSOS PORTAL | Carteira col 34 |
| AV | ITENS CARRINHO | Carteira col 35 |
| AW | VALOR PORTAL B2B | Carteira col 36 |
| AX | OPORTUNIDADE ECOM | CONVERTIDO / QUENTE / vazio |

#### [+6] SAP — Cols AY a BI (11 colunas)
Visível quando fechado: **AY = COD_SAP**

| COL | CAMPO | FONTE |
|-----|-------|-------|
| AY | COD_SAP | SAP col 2 / Carteira col 1 |
| AZ | STATUS PARCEIRO | SAP |
| BA | ENDEREÇO | SAP Endereço + Bairro |
| BB | CEP | SAP Código_Postal |
| BC | CONDIÇÃO PAGAMENTO | SAP Cond.Pagto |
| BD | LISTA PREÇOS | SAP |
| BE | GRUPO CLIENTE | SAP |
| BF | BLOQUEIO VENDAS | SAP (X = bloqueado) |
| BG | BLOQUEIO GERAL | SAP |
| BH | DESC. COMERCIAL | SAP % |
| BI | MACRORREGIÃO | SAP 03_Nome_Macro |

#### [+7] OPERACIONAL — Cols BJ a BR (9 colunas)
Visível quando fechado: **BJ = PRÓX. FOLLOW-UP**

| COL | CAMPO | REGRA |
|-----|-------|-------|
| BJ | PRÓX. FOLLOW-UP | DATA_ÚLT_ATENDIMENTO + dias do RESULTADO. Se ultrapassou = VERMELHO |
| BK | BLOCO | MANHÃ / TARDE |
| BL | ESTÁGIO FUNIL | CS/RECOMPRA, ATENÇÃO/SALVAR, PERDA/NUTRIÇÃO, ABERTURA/ATIVAÇÃO |
| BM | AÇÃO DETALHADA | "LIGAÇÃO - OFERECER REPOSIÇÃO", "1º CONTATO", etc. |
| BN | DATA ÚLT. ATENDIMENTO | MAX(DATA) no LOG para este CNPJ |
| BO | ÚLTIMO RESULTADO | Último RESULTADO no LOG |
| BP | MOTIVO | 10 opções padronizadas (ver seção 6) |
| BQ | PRIORIDADE | Score 1-100: Curva(A=30,B=15,C=5) + Sinal(🔴=40,🟡=25,🟢=10,🟣=5) + Fase(RECOMPRA=25,CS=20,PROSP=10,NUTR=5) |
| BR | OBSERVAÇÃO | Texto livre |

#### [+8] COMITÊ — Cols BS a CC (11 colunas)
Visível quando fechado: **BS = % ATING. MÊS**

| COL | CAMPO | REGRA |
|-----|-------|-------|
| BS | % ATING. MÊS | = REALIZADO/META × 100. ≥80% verde, 50-79% amarelo, <50% vermelho |
| BT | META MÊS (R$) | Do arquivo META por grupo chave |
| BU | REALIZADO MÊS (R$) | Soma pedidos mês atual via DRAFT |
| BV | % ATING. TRI | = REALIZADO_TRI/META_TRI × 100 |
| BW | META TRI (R$) | Soma metas dos 3 meses |
| BX | REALIZADO TRI (R$) | Soma realizado trimestre |
| BY | % ATING. YTD | = REALIZADO_YTD/META_YTD × 100 |
| BZ | META YTD (R$) | Soma metas jan até mês atual |
| CA | REALIZADO YTD (R$) | Soma realizado jan até mês atual |
| CB | DATA ÚLTIMO PEDIDO | Referência cruzada de col S |
| CC | JUSTIFICATIVA SEMANAL | Único campo manual. Preenchido antes da quarta |

### 3.3 Resumo estrutural ABA 1

| GRUPO | COLUNAS | QTD | VISÍVEL (fechado) |
|-------|---------|-----|-------------------|
| Fixas (congeladas) | A-J | 10 | NOME, REDE, UF, CONSULTOR, SITUAÇÃO, DIAS, SINALEIRO, TIPO, FASE, TENTATIVA |
| [+1] IDENTIDADE | K-Q | 7 | CNPJ |
| [+2] VIDA COMERCIAL | R-Z | 9 | CICLO MÉDIO |
| [+3] TIMELINE | AA-AM | 13 | TOTAL PERÍODO |
| [+4] JORNADA | AN-AS | 6 | DIAS ATÉ CONVERSÃO |
| [+5] ECOMMERCE | AT-AX | 5 | ACESSO B2B |
| [+6] SAP | AY-BI | 11 | COD_SAP |
| [+7] OPERACIONAL | BJ-BR | 9 | PRÓX. FOLLOW-UP |
| [+8] COMITÊ | BS-CC | 11 | % ATING. MÊS |
| **TOTAL** | **A-CC** | **81** | **18 visíveis tudo fechado** |

### 3.4 Preview — como fica com tudo fechado (18 colunas)

```
NOME         | REDE          | UF | CONS.  | SIT.     | DIAS | 🚦 | TIPO   | FASE     | T  | CNPJ            | CICLO | TOTAL  | CONV. | B2B | SAP        | F-UP     | %MÊS
-------------|---------------|----|--------|----------|------|----|---------|-----------|----|-----------------|-------|--------|-------|-----|------------|----------|------
DIV.TERRA CWB| DIVINA TERRA  | PR | DAIANE | ATIVO    | 12   | 🟢 | DESENV  | CS       | T1 | 32828171000108  | —     | 767    | —     | Não | 1000105451 | 05/02    | 82%
ALICE GRAOS  | TUDO EM GRAOS | RS | MANU   | EM RISCO | 53   | 🟡 | RECOR   | RECOMPRA | T1 | 41626544000140  | 31    | 9.808  | 15d   | Sim | 1000105678 | 07/02    | 45%
BIO SC       | BIOMUNDO      | SC | DAIANE | INAT.ANT | 99   | 🔴 | RECOR   | RECUPER  | T2 | 46945954000178  | 60    | 6.829  | 8d    | Não | 1000101541 | ATRASADO | 0%
AFS ALDEIA   | ARMAZEM FIT   | SP | DAIANE | PROSPECT | —    | 🟣 | PROSP   | PROSPECÇÃO| T1 | 39915172000120  | —     | —      | —     | Não | —          | 10/02    | —
```

---

# 4. FASE 2 — LOG + AGENDA + DRAFT

**Fonte:** BLUEPRINT_v3_LOG_AGENDA_DASH.html  

### 4.1 Fluxo diário completo

```
MANHÃ (Leandro):
  1. Extrai relatório Mercos → cola no DRAFT 1
  2. Fórmulas atualizam a CARTEIRA (novos pedidos, status)
  3. Filtra CARTEIRA por consultor → gera AGENDA do dia
  4. Envia agenda por WhatsApp (.xlsx) para cada consultor

FINAL DO DIA (Leandro):
  5. Consultores devolvem planilhas preenchidas
  6. Cola no DRAFT 2 (zona de quarentena)
  7. Validação automática → flui para LOG oficial
  8. LOG alimenta DASH + atualiza próximos follow-ups na CARTEIRA
```

### 4.2 ABA LOG — 20 colunas

Princípio: cada linha = 1 interação com 1 cliente em 1 data. Append-only. Zero valores financeiros.

| # | COL | CAMPO | PREENCHIDO POR | OBRIGATÓRIO |
|---|-----|-------|----------------|-------------|
| 1 | A | DATA | Auto | ✅ |
| 2 | B | CONSULTOR | Auto (puxa CARTEIRA col D) | ✅ |
| 3 | C | NOME FANTASIA | Auto (puxa CARTEIRA col A) | ✅ |
| 4 | D | CNPJ | Auto (chave primária) | ✅ |
| 5 | E | UF | Auto (puxa CARTEIRA col C) | ✅ |
| 6 | F | REDE / REGIONAL | Auto (puxa CARTEIRA col B) | ✅ |
| 7 | G | SITUAÇÃO | Auto (ATIVO/EM RISCO/INAT.REC/INAT.ANT/PROSPECT/LEAD) | ✅ |
| 8 | H | WHATSAPP | Consultor (dropdown SIM/NÃO) | ✅ |
| 9 | I | LIGAÇÃO | Consultor (dropdown SIM/NÃO) | ✅ |
| 10 | J | LIGAÇÃO ATENDIDA | Consultor (dropdown SIM/NÃO/N/A) | ✅ |
| 11 | K | TIPO AÇÃO | Consultor (dropdown ATIVO/RECEPTIVO) | ✅ |
| 12 | L | TIPO DO CONTATO | Consultor (dropdown 7 opções) | ✅ |
| 13 | M | RESULTADO | Consultor (dropdown 12 opções) | ✅ |
| 14 | N | MOTIVO | Consultor (dropdown 10 opções) | ✅ |
| 15 | O | FOLLOW-UP | Auto (= DATA + dias do RESULTADO) | ✅ |
| 16 | P | AÇÃO | Consultor (dropdown próxima ação) | ✅ |
| 17 | Q | MERCOS ATUALIZADO | Consultor (SIM/NÃO) | ✅ |
| 18 | R | FASE | Auto (puxa CARTEIRA col I) | ✅ |
| 19 | S | TENTATIVA | Auto (puxa CARTEIRA col J) | ✅ |
| 20 | T | NOTA DO DIA / AÇÃO | Consultor (texto livre) | ❌ |

### 4.3 ABA AGENDA — 24 colunas (arquivo separado por consultor)

Colunas 1-14 = contexto (read-only). Colunas 15-24 = ação do consultor (dropdowns).

**Contexto (🔒 read-only):**
1. NOME FANTASIA, 2. CNPJ, 3. UF, 4. REDE/REGIONAL, 5. TELEFONE, 6. EMAIL, 7. SITUAÇÃO, 8. DIAS SEM COMPRA, 9. SINALEIRO, 10. FASE, 11. TENTATIVA, 12. AÇÃO SUGERIDA, 13. BLOCO, 14. ÚLTIMO RESULTADO

**Ação do consultor (✏️ dropdowns):**
15. WHATSAPP, 16. LIGAÇÃO, 17. LIGAÇÃO ATENDIDA, 18. TIPO AÇÃO, 19. TIPO DO CONTATO, 20. RESULTADO, 21. MOTIVO, 22. AÇÃO FUTURA, 23. MERCOS ATUALIZADO, 24. NOTA DO DIA

**Cabeçalho da Agenda:**
```
Linha 1: 📋 AGENDA DD/MM/AAAA — NOME DO CONSULTOR
Linha 2: Cart:XX | Prosp:XX | Follow-ups:XX | Novos:XX
Linha 3: ⏰ 8:00 Reunião | ☀ 9-12 CARTEIRA (manhã) | 🌙 13-17 PROSPECÇÃO (tarde)
Linha 4: ⚠ REGISTRAR TUDO: Mercos + Kanban WhatsApp + Esta planilha
Linha 5: (vazia)
Linha 6: Headers (24 colunas)
Linha 7+: Dados dos clientes
```

### 4.4 ABA DRAFT 2 — Quarentena de atendimentos

Espelho da AGENDA (24 colunas) + 3 de validação:

| COL | CAMPO | REGRA |
|-----|-------|-------|
| A-X | Mesmas 24 cols da AGENDA | Cola direto do arquivo devolvido |
| Y | ✅ VÁLIDO | SE(E(CNPJ≠"", RESULTADO≠"", TIPO_CONTATO≠""), "OK", "ERRO") |
| Z | ⚠ ERRO | Tipo do erro: "CNPJ INVÁLIDO", "SEM RESULTADO", etc. |
| AA | 📝 MIGRADO | SIM/NÃO. Após migrar pro LOG, marca SIM (evita duplicatas) |

**Regra de ouro:** Só linhas com Y="OK" e AA=vazio entram no LOG.

---

# 5. FASE 3 — DASHBOARDS

**Layout:** Vertical infinito, horizontal fixo. CEO rola pra baixo.

### 5.1 Ordem vertical no Excel

| POS | SEÇÃO | LINHAS | O QUE MOSTRA |
|-----|-------|--------|-------------|
| 1 | FILTROS | 3 | Dropdown vendedor + período |
| 2 | KPIs RESUMO | 5 | 6 cards: Contatos, Vendas, Orçamentos, Não Atende, % Conversão, Mercos OK |
| 3 | DASH CONTATOS & FUNIL | 12 | Matriz TIPO × (Contatos + Funil + Relacionamento + Não Venda) |
| 4 | DASH TIPO × RESULTADO | 12 | Cruzamento completo tipo/resultado |
| 5 | DASH MOTIVOS | 14 | Por que não compram — inteligência para diretoria |
| 6 | DASH FORMA DO CONTATO | 6 | WhatsApp vs Ligação vs ambos |
| 7 | DASH PRODUTIVIDADE | 8 | Comparativo entre consultores |
| **TOTAL** | | **~60 linhas** | |

### 5.2 Fórmula-base dos DASHs

```excel
=COUNTIFS(LOG!$L:$L, TIPO_CONTATO, LOG!$M:$M, RESULTADO, LOG!$B:$B, VENDEDOR, 
          LOG!$A:$A, ">="&DATA_INICIO, LOG!$A:$A, "<="&DATA_FIM)
```

### 5.3 DASH MOTIVOS (novo, não existe nos sistemas de referência)

Responde: POR QUE os clientes não compram?

| MOTIVO | DONO DA AÇÃO | INSIGHT |
|--------|-------------|---------|
| PRODUTO NÃO VENDEU / SEM GIRO | DIRETORIA / FÁBRICA | ⚠️ Sinal crítico: produto sem fit no PDV |
| PREÇO ALTO / MARGEM | COMERCIAL | Competitividade — revisar tabela |
| PREFERIU CONCORRENTE | COMERCIAL / MKT | Qual concorrente? Qual produto? |
| PROBLEMA LOGÍSTICO | LOGÍSTICA | Atraso, avaria, falta |
| PROBLEMA FINANCEIRO | FINANCEIRO | Bloqueado ou sem crédito |
| AINDA TEM ESTOQUE | Normal | Ajustar CICLO MÉDIO |
| FECHOU LOJA | PERDA | Atualizar status |
| SEM INTERESSE | NUTRIÇÃO | Ir pra nutrição |
| VIAJANDO / INDISPONÍVEL | Normal | Reagendar |
| 1º CONTATO / SEM MOTIVO | Normal | Prospecção inicial |

**Flag automático:** Se "PRODUTO NÃO VENDEU" > 35% → alerta pro comitê de quarta.

### 5.4 Futuro (próxima fase)

- DASH SINALEIRO (aba separada) — penetração por rede, visão 🟢🟡🔴🟣
- DASH REDES — performance por rede de franquia
- DASH PRODUTO / OPORTUNIDADES — matriz produto × status por cliente

---

# 6. FASE 4 — REGRAS DE NEGÓCIO

### 6.1 RESULTADO → Follow-Up (dias)

| # | RESULTADO | FOLLOW-UP | GRUPO DASH | QUANDO USAR |
|---|-----------|-----------|-----------|-------------|
| 1 | EM ATENDIMENTO | +2 dias | FUNIL | Negociação ativa |
| 2 | ORÇAMENTO | +1 dia | FUNIL | Proposta enviada |
| 3 | CADASTRO | +2 dias | FUNIL | Em processo de cadastro |
| 4 | VENDA / PEDIDO | +45 dias | FUNIL | Pedido fechado |
| 5 | RELACIONAMENTO | +7 dias | RELAC. | Pós-venda, CS |
| 6 | FOLLOW UP 7 | +7 dias | RELAC. | Retomar em 1 semana |
| 7 | FOLLOW UP 15 | +15 dias | RELAC. | Retomar em 2 semanas |
| 8 | SUPORTE | SEM | RELAC. | Problema resolvido |
| 9 | NÃO ATENDE | +1 dia | NÃO VENDA | Escalona T+1 |
| 10 | NÃO RESPONDE | +1 dia | NÃO VENDA | WhatsApp sem resposta |
| 11 | RECUSOU LIGAÇÃO | +2 dias | NÃO VENDA | Mudança de canal |
| 12 | PERDA / FECHOU LOJA | SEM | NÃO VENDA | Perdido definitivamente |

### 6.2 TIPO DO CONTATO (7 opções)

| # | TIPO | QUANDO |
|---|------|--------|
| 1 | PROSPECÇÃO | 1º contato com prospect/lead |
| 2 | NEGOCIAÇÃO | Em negociação ativa (orçamento, amostra) |
| 3 | FOLLOW UP | Retorno agendado |
| 4 | ATEND. CLIENTES ATIVOS | Dentro do ciclo de compra |
| 5 | ATEND. CLIENTES INATIVOS | Ultrapassou ciclo |
| 6 | PÓS-VENDA / RELACIONAMENTO | CS, verificar PDV |
| 7 | MOTIVO / PAROU DE COMPRAR | Investigar — feedback para fábrica |

### 6.3 SITUAÇÃO (auto-calculada)

| DIAS SEM COMPRA | SITUAÇÃO | COR |
|----------------|----------|-----|
| ≤ 50 | ATIVO | #00B050 (verde) |
| 51-60 | EM RISCO | #FFC000 (amarelo) |
| 61-90 | INATIVO RECENTE | #FF6600 (laranja) |
| > 90 | INATIVO ANTIGO | #FF0000 (vermelho) |
| Nunca comprou | PROSPECT / LEAD / NOVO | #BDD7EE (roxo/azul) |

### 6.4 CADÊNCIA DE TENTATIVA (T1→T4→NUTRIÇÃO)

| TENTATIVA | CANAL | INTERVALO | COMPORTAMENTO |
|-----------|-------|-----------|---------------|
| T1 | WhatsApp | Dia 0 | Primeira abordagem |
| T2 | Ligação | +1 dia útil | Se não respondeu T1 |
| T3 | WhatsApp | +2 dias | Mudança de abordagem |
| T4 | Ligação final | +2 dias | Última tentativa ativa |
| NUTRIÇÃO | Email + WhatsApp esporádico | Ciclo 15 dias | Após T4 sem resposta |
| ↩️ RESET | — | — | Quando responde em qualquer T → volta pra T1 |

### 6.5 FASE (auto-calculada)

| CONDIÇÃO | FASE |
|----------|------|
| ATIVO com 0-10 dias | PÓS-VENDA |
| ATIVO com 10-25 dias | CS (verificar PDV) |
| ATIVO perto do ciclo (-7 dias) | RECOMPRA (momento ouro) |
| INATIVO RECENTE | SALVAMENTO |
| INATIVO ANTIGO | RECUPERAÇÃO |
| PROSPECT / LEAD | PROSPECÇÃO |
| Após T4 sem resposta | NUTRIÇÃO |
| Qualquer fase com resposta | EM ATENDIMENTO |
| Com orçamento aberto | ORÇAMENTO |

### 6.6 PRIORIDADE (score 1-100)

| COMPONENTE | VALOR | PESO |
|-----------|-------|------|
| Curva A | +30 pts | |
| Curva B | +15 pts | |
| Curva C | +5 pts | |
| 🔴 Vermelho | +40 pts | |
| 🟡 Amarelo | +25 pts | |
| 🟢 Verde | +10 pts | |
| 🟣 Roxo | +5 pts | |
| RECOMPRA/SALVAMENTO | +25 pts | |
| CS | +20 pts | |
| PROSPECÇÃO | +10 pts | |
| NUTRIÇÃO | +5 pts | |
| **Máximo possível** | **95 pts** | (A + 🔴 + SALVAMENTO) |

---

# 7. PIPELINE ETL

### 7.1 Visão geral

```
88 ARQUIVOS BRUTOS → 8 STAGING (1 por categoria) → GOLDEN → JARVIS CRM CENTRAL
```

### 7.2 Os 8 prompts de extração

| # | PROMPT | INPUT | OUTPUT | COMPLEXIDADE |
|---|--------|-------|--------|-------------|
| 01 | SAP | 4 arquivos SAP | 01_CARTEIRA_SAP.xlsx | Média |
| 02 | VENDAS + POSITIVAÇÃO | 12+ meses vendas + 12 positivação | 02_VENDAS_POSITIVACAO.xlsx | Média |
| 03 | ATENDIMENTOS MERCOS | 12 meses + extras | 03_ATENDIMENTOS_MERCOS.xlsx | Média |
| 04 | CURVA ABC | 12+ arquivos | 04_CURVA_ABC.xlsx | Simples |
| 05B | ECOMMERCE | 12+ arquivos acessos | 05B_ECOMMERCE.xlsx | Simples |
| 06 | LOG HISTÓRICO | ~11K registros + funil + CRM | 06_LOG_HISTORICO.xlsx | ⚠️ ALTA |
| 07 | TICKETS DESKRIO | 12 arquivos WhatsApp (4.885 tickets) | 07_TICKETS_DESKRIO.xlsx | Média |
| 08 | CARTEIRA MERCOS | 7+ versões carteira | 08_CARTEIRA_MERCOS.xlsx | Média |
| 09 | CONSOLIDAÇÃO | Os 8 staging | 09_ATENDIMENTOS_CONSOLIDADO.xlsx | ⚠️ ALTA |

### 7.3 Decisões do ETL

- **Vendas + Positivação = 1 arquivo** (valor > 0 = positivou)
- **E-commerce** segue mesma lógica mês a mês de pivô
- **Nomes originais** preservados (SAP com cara de SAP, Mercos com cara de Mercos)
- **Mapeamento DE→PARA** só no momento de popular o JARVIS, não no staging
- **Classificação 3-tier** para dados do LOG: 🟢 REAL / 🟡 SINTÉTICO / 🔴 ALUCINAÇÃO

### 7.4 Estrutura de pastas

```
/jarvis-data/
  /01_raw/          ← arquivos originais (nunca alterar)
  /02_staging/      ← 1 arquivo tratado por categoria
  /03_golden/       ← consolidado final (pronto pro JARVIS)
  /04_output/       ← JARVIS CRM CENTRAL + agendas exportadas
```

---

# 8. ANOMALIAS CONHECIDAS

| # | SEVERIDADE | ANOMALIA | QTD | CORREÇÃO |
|---|-----------|----------|-----|----------|
| A1 | ALTA | COD_SAP diverge entre Carteira e SAP | 28 | Usar COD_SAP da Carteira como master |
| A2 | ALTA | Clientes Carteira sem match SAP | 20 | COD_FONTE = "MERCOS_ONLY" |
| A3 | MÉDIA | COD_SAP ausente na Carteira | 36 | XLOOKUP por CNPJ na base SAP |
| A4 | MÉDIA | CNPJs duplicados SAP SEM ATEND | 57 | Deduplicar (manter mais recente) |
| A5 | MÉDIA | Mercos sem CNPJ | 219 | Excluir (sem CNPJ não entra) |
| A6 | ALTA | TIPO_CONTATO no LOG com notas livres | ~30 | Normalizar pra 7 categorias |
| A7 | MÉDIA | RESULTADO no LOG fora do padrão | ~36 | PERCA→PERDA, padronizar |
| A8 | BAIXA | LOG CNPJs órfãos (sem base) | 453 | Reconciliar por nome fantasia |
| A9 | ALTA | 84% das redes sem COD_SAP | 754 | XLOOKUP. Se não achar: COD_FONTE="REDE_ONLY" |
| A10 | MÉDIA | 77% da Carteira com "SEM REDE" | 376 | Cruzar CNPJ com GRUPO_CHAVE. Sem rede = REGIONAL |
| A11 | ALTA | ~3.540 registros fabricados por VBA/IA no LOG | 3.540 | Classificar como SINTÉTICO, não descartar |
| A12 | ALTA | Duplicação 742% valores financeiros | — | Two-Base resolve (zero R$ no LOG) |

---

# 9. ROADMAP DE IMPLEMENTAÇÃO

### Ordem de construção do JARVIS_CRM_CENTRAL.xlsx

```
PASSO 1: ABA REGRAS
  → Tabelas de validação (RESULTADO, TIPO CONTATO, MOTIVO, SITUAÇÃO)
  → Menor, mais simples, base para validação de tudo

PASSO 2: ABA CARTEIRA (81 colunas)
  → Popular com dados reais da Carteira Mercos Jan/2026
  → Aplicar agrupamentos [+], congelamento, cores
  → Validar: CNPJs únicos, status calculados, sinaleiro

PASSO 3: ABA LOG (20 colunas)
  → Migrar dados históricos tratados (staging 06_LOG_HISTORICO)
  → Validar: zero R$ no LOG, datas coerentes, resultados válidos

PASSO 4: ABA DRAFT 1 (Mercos) + DRAFT 2 (Atendimentos)
  → Zona de quarentena com validações
  → Testar fluxo: colar → validar → migrar

PASSO 5: ABA DASH (7 seções verticais)
  → COUNTIFS/SUMIFS referenciando LOG
  → Filtros por vendedor e período
  → Validar KPIs contra Painel de Atividades (referência)

PASSO 6: ABA AGENDA (template exportável)
  → Template 24 colunas com dropdowns
  → Macro ou processo para gerar 1 arquivo por consultor

PASSO 7: VALIDAÇÃO END-TO-END
  → Simular 1 dia completo do fluxo
  → Agenda → Consultor preenche → DRAFT 2 → LOG → DASH atualiza → CARTEIRA atualiza
```

### Critérios de qualidade por passo

| PASSO | VALIDAÇÃO | ACEITE |
|-------|-----------|--------|
| 1 | Todas as listas de dropdown funcionam | 100% |
| 2 | CNPJs únicos, sinaleiro bate com dias, fase bate com situação | 100% |
| 3 | Zero R$ no LOG, nenhum RESULTADO fora das 12 opções | 100% |
| 4 | CNPJ inválido = "ERRO", migração marca "SIM" | 100% |
| 5 | KPIs consistentes com dados do LOG | ±5% |
| 6 | Dropdowns funcionam, cabeçalho correto | 100% |
| 7 | Fluxo completo sem quebrar | Funcional |

---

## EQUIPE COMERCIAL (referência)

| CONSULTOR | TERRITÓRIO | TIPO |
|-----------|-----------|------|
| MANU DITZEL | SC, PR, RS (sem rede) | Regional |
| LARISSA PADILHA | Resto do Brasil (sem rede) | Regional |
| JULIO GADRET | CIA DA SAUDE + FIT LAND (exclusivo) | Rede |
| DAIANE STAVICKI | Outras redes de franquia + Gestão | Rede + Central |

**Redes de franquia:** Mundo Verde, Biomundo, CIA DA SAUDE, FIT LAND, Divina Terra, Vida Leve, Tudo em Grãos, Armazém Fitstore

**Universo:** 488 clientes carteira ativa + 923 lojas redes/franquias + ~5.500 prospects Mercos

---

## NÚMEROS-CHAVE DE REFERÊNCIA

| MÉTRICA | VALOR | FONTE |
|---------|-------|-------|
| Total CNPJs SAP | 1.701 | SAP COM_VENDA (661) + SEM_ATEND (1.040) |
| Total CNPJs Mercos | 6.078 | 395 clientes reais + 5.675 prospects |
| Carteira operacional | 488 | Clientes com atividade recente |
| Registros LOG histórico | 11.758 | Fev/2025 → Fev/2026 |
| Tickets Deskrio | 4.885 | WhatsApp Business 12 meses |
| Mensagens WhatsApp totais | 77.805 | Painel de Atividades |
| Vendas fechadas 2025 | 957 | Painel de Atividades |
| Taxa conversão geral | 9.0% | Vendas/Atendimentos qualificados |
| Atendimentos por venda | ~11 | Média de contatos até converter |
| Meta anual 2026 | R$ 4.747.200 | BASE SAP META |
| Lojas redes mapeadas | 923 | 107 ativas + 816 prospects |
| Penetração redes | ~11% | Receita real / Potencial |

---

**FIM DO DOCUMENTO MESTRE DEFINITIVO**

Este documento é a FONTE ÚNICA DA VERDADE do projeto JARVIS CRM.  
Qualquer divergência com outros documentos, este prevalece.  
Versões anteriores dos blueprints ficam como referência histórica apenas.

*VITAO Alimentos — JARVIS CRM — 08/02/2026*
