# 📋 HANDOFF — CRM INTELIGENTE VITAO360 V3

> **Data:** 09/02/2026
> **Arquivo:** `CRM_INTELIGENTE_VITAO360_V3.xlsx`
> **Status:** Estrutura 100% pronta. Falta popular dados reais nas abas DRAFT 1 e DRAFT 2.

---

## 1. CONTEXTO DO PROJETO

A VITAO Alimentos é uma distribuidora B2B de alimentos naturais (Curitiba/PR) com ~661 clientes internos + 923 lojas de franquia em 8 redes. O CRM VITAO360 é a planilha central de inteligência comercial que conecta dados de vendas (Mercos ERP), atendimentos (WhatsApp/Deskrio), SAP (metas/carteira) e sinaleiro de penetração em redes.

### Equipe comercial (4 consultores):
| CONSULTOR | TERRITÓRIO |
|-----------|-----------|
| HEMANUELE DITZEL (MANU) | SC / PR / RS |
| LARISSA PADILHA | Restante do Brasil |
| JULIO GADRET | CIA da Saúde + Fitland |
| DAIANE STAVICKI | Franquias + operacional |

### Números-chave:
- **661 clientes** no sinaleiro interno (129 verde, 65 amarelo, 298 vermelho, 169 roxo)
- **923 lojas** em 8 redes de franquia
- **META 2026:** R$ 4.747.200 (SAP)
- **Faturamento 2025:** R$ 1.914.745,74

---

## 2. ARQUITETURA DO ARQUIVO (9 abas)

```
REGRAS → DRAFT 1 → PROJEÇÃO → DRAFT 2 → LOG → CARTEIRA → AGENDA → DASH → Claude Log
```

### Fluxo de dados:
```
FONTES EXTERNAS          PROCESSAMENTO           VISÃO GERENCIAL
─────────────          ─────────────           ───────────────
Mercos ERP ────→ DRAFT 1 (base mestre) ──→ CARTEIRA (visão 360°)
SAP vendas ────→ PROJEÇÃO (meta×real) ────→ CARTEIRA acompanhamento
Deskrio/WPP ──→ DRAFT 2 (log diário) ────→ CARTEIRA funil
Sinaleiro ────→ PROJEÇÃO (rede/meta) ────→ DASH (KPIs)
                                    └────→ AGENDA (priorização)
```

---

## 3. MAPA COMPLETO DE CADA ABA

---

### 3.1 ABA REGRAS (209 linhas × 7 colunas)

**Função:** Tabela de referência central. Todas as fórmulas de DRAFT 2, CARTEIRA e AGENDA puxam daqui.

#### Seção 1: Listas de validação (R1-R120) — ✅ PRONTO, NÃO MEXER
| BLOCO | LINHAS | CONTEÚDO |
|-------|--------|----------|
| RESULTADO | R2-R13 | 12 opções + dias follow-up + GRUPO DASH |
| TIPO CONTATO | R17-R24 | 7 opções |
| MOTIVO | R27-R37 | 10 opções |
| SITUAÇÃO | R40-R47 | 7 opções + cores |
| FASE | R50-R59 | 9 opções |
| TENTATIVA | R62-R68 | 6 cadências (T1-T6) |
| SINALEIRO CICLO | R71-R75 | 4 regras |
| TIPO CLIENTE | R78-R84 | 6 critérios |
| CONSULTOR | R87-R91 | 4 territórios |
| DROPDOWNS | R94-R120 | Listas para validação |

#### Seção 2: MOTOR DE REGRAS (R125-R190) — ✅ PRONTO, NÃO MEXER
Tabela cruzada **SITUAÇÃO × RESULTADO → 5 campos automáticos**:
- **63 combinações** cobrindo 7 situações × ~9 resultados
- Colunas: `A=SITUAÇÃO | B=RESULTADO | C=ESTÁGIO | D=FASE | E=TIPO CONTATO | F=AÇÃO FUTURA | G=TEMPERATURA`
- Cores por situação: ATIVO=verde, EM RISCO/INAT.REC=amarelo, INAT.ANT=laranja, PROSPECT/LEAD=roxo, NOVO=azul

**Como funciona:** DRAFT 2 faz `INDEX/MATCH(SITUAÇÃO&RESULTADO)` contra essa tabela para calcular automaticamente ESTÁGIO, FASE, TIPO CONTATO, AÇÃO FUTURA e TEMPERATURA.

#### Seção 3: SCORE RANKING (R193-R200) — ✅ PRONTO
6 fatores com pesos para priorização da AGENDA:
| FATOR | PESO |
|-------|------|
| Urgência temporal (dias÷ciclo) | 30% |
| Valor do cliente (curva+tipo) | 25% |
| Follow-up vencido | 20% |
| Sinal de compra (ecom+temp) | 15% |
| Tentativa | 5% |
| Situação | 5% |

#### Seção 4: SINALEIRO META (R202-R207) — ✅ PRONTO
| COR | FAIXA | SIGNIFICADO |
|-----|-------|------------|
| 🟢 | ≥100% | Batendo meta |
| 🟡 | 50-99% | Precisa acelerar |
| 🔴 | <50% | Alerta crítico |
| ⚫ | 0% | Nenhuma venda |

---

### 3.2 ABA DRAFT 1 (500 linhas × 45 colunas)

**Função:** BASE MESTRE de clientes. Uma linha por CNPJ. Dados estáticos + vendas mensais.

#### Layout de colunas:
| BLOCO | COLUNAS | COLS EXCEL | CONTEÚDO |
|-------|---------|------------|----------|
| IDENTIDADE | 1-11 | A-K | NOME, CNPJ, RAZÃO, UF, CIDADE, EMAIL, TELEFONE, DATA CADASTRO, REDE, CONSULTOR, VENDEDOR |
| COMPRAS | 12-14 | L-N | DIAS SEM COMPRA, DATA ÚLT. PEDIDO, VALOR ÚLT. PEDIDO |
| ECOMMERCE | 15-20 | O-T | ACESSOS SEMANA, ACESSO B2B, ACESSOS PORTAL, ITENS CARRINHO, VALOR B2B, OPORTUNIDADE |
| VENDAS MÊS A MÊS | 21-32 | U-AF | MAR/25, ABR/25, MAI/25, JUN/25, JUL/25, AGO/25, SET/25, OUT/25, NOV/25, DEZ/25, JAN/26, FEV/26 |
| RECORRÊNCIA | 33-37 | AG-AK | CICLO MÉDIO, Nº COMPRAS, CURVA ABC, MESES POSITIVADO, TICKET MÉDIO |
| ATENDIMENTO MERCOS | 38-41 | AL-AO | ÚLT. REGISTRO, DATA ÚLT. ATEND, TIPO ATEND, OBS ATEND |
| **NOVOS V3** | **42-43** | **AP-AQ** | **TIPO CLIENTE** (fórmula), **MÉDIA MENSAL** (fórmula) |
| FONTE | 44-45 | AR-AS | Descrição da fonte de dados |

#### Fórmulas V3 adicionadas:
```
AP (TIPO CLIENTE) = IF(AJ="","", IF(AJ=0,"PROSPECT", IF(AJ=1,"NOVO", IF(AJ<=3,"EM DESENVOLVIMENTO", IF(AJ<=6,"RECORRENTE","FIDELIZADO")))))

AQ (MÉDIA MENSAL) = IF(AJ=0, 0, SUM(U:AF)/AJ)
```
- `AJ` = MESES POSITIVADO (col 36)
- `U:AF` = vendas mês a mês (cols 21-32)

#### ⚠️ O QUE PRECISA POPULAR:
- **Linhas R4-R500:** Colar dados reais dos clientes
- **Fontes:** Carteira Detalhada (Mercos), Relatórios de vendas mensais, Curva ABC, Positivação, Acessos E-commerce, Atendimentos Mercos
- **CNPJ é a chave primária (col B)** — tudo referencia essa coluna

---

### 3.3 ABA PROJEÇÃO (503 linhas × 49 colunas)

**Função:** Meta SAP distribuída por cliente + sinaleiro de atingimento + dados de rede.

#### Layout de colunas:
| BLOCO | COLUNAS | CONTEÚDO | STATUS |
|-------|---------|----------|--------|
| 🔵 IDENTIFICAÇÃO | 1-4 | CNPJ, NOME, REDE, CONSULTOR | ✅ Fórmulas puxam do DRAFT 1 |
| 🟡 SINALEIRO REDE | 5-9 | TOTAL LOJAS, SINALEIRO%, COR, MATURIDADE, AÇÃO | ✅ VLOOKUP para tabela ref (cols AP+) |
| 📊 META MENSAL | 10-22 | META ANUAL + JAN-DEZ | ✅ Fórmula proporcional ao histórico |
| 💰 REALIZADO | 23-35 | REAL ANUAL + JAN-DEZ | ✅ JAN/FEV puxam DRAFT 1, MAR-DEZ aguardam |
| 🚦 INDICADORES | 36-39 | %YTD, SINALEIRO META, GAP, RANKING | ✅ Fórmulas prontas |
| 📋 REF REDES | 42-49 | Tabela referência 8 redes (14 linhas) | ✅ Dados reais do sinaleiro |

#### Dados de referência já populados (cols AP+):
**8 REDES:**
| REDE | LOJAS | SINALEIRO | COR | MATURIDADE |
|------|-------|-----------|-----|------------|
| FIT LAND | 89 | 29.8% | 🔴 VERMELHO | POSITIVAÇÃO |
| DIVINA TERRA | 85 | 10.0% | 🔴 VERMELHO | POSITIVAÇÃO |
| VIDA LEVE | 81 | 8.0% | 🔴 VERMELHO | ATIVAÇÃO |
| CIA DA SAUDE | 163 | 2.6% | 🔴 VERMELHO | ATIVAÇÃO |
| MUNDO VERDE | 199 | 1.4% | 🔴 VERMELHO | ATIVAÇÃO |
| BIOMUNDO | 167 | 1.4% | 🔴 VERMELHO | ATIVAÇÃO |
| TUDO EM GRAOS | 25 | 6.2% | 🔴 VERMELHO | ATIVAÇÃO |
| ARMAZEM FITSTORE | 114 | 0.0% | 🟣 ROXO | PROSPECÇÃO |

**META 2026 MENSAL (SAP):**
| MÊS | META R$ |
|-----|---------|
| JAN | 333.600 |
| FEV | 348.600 |
| MAR | 357.000 |
| ABR | 366.300 |
| MAI | 378.300 |
| JUN | 388.200 |
| JUL | 403.200 |
| AGO | 413.100 |
| SET | 422.400 |
| OUT | 432.900 |
| NOV | 444.300 |
| DEZ | 459.300 |
| **TOTAL** | **4.747.200** |

#### Fórmula de distribuição de META:
```
META_CLIENT_MÊS = META_GLOBAL_MÊS × (SUM(vendas_client_2025) / SUM(vendas_total_2025))
```
- Clientes com vendas altas recebem meta maior
- Clientes com zero vendas recebem meta zero (ajustar manualmente se necessário)

#### ⚠️ O QUE PRECISA AJUSTAR DEPOIS DE POPULAR DRAFT 1:
- As metas se recalculam automaticamente conforme os dados de vendas do DRAFT 1 forem preenchidos
- Meses futuros de REALIZADO (MAR-DEZ 2026) ficam vazios até acontecerem

---

### 3.4 ABA DRAFT 2 (502 linhas × 24 colunas)

**Função:** LOG DIÁRIO de atendimentos. Uma linha por contato realizado. Alimenta CARTEIRA e AGENDA.

#### Layout — 13 colunas manuais (🟢) + 11 automáticas (🔵):
| COL | EXCEL | HEADER | TIPO | DETALHE |
|-----|-------|--------|------|---------|
| 1 | A | DATA | 🟢 manual | Data do contato |
| 2 | B | CONSULTOR | 🟢 dropdown | REGRAS!A88:A91 |
| 3 | C | NOME FANTASIA | 🟢 manual | Nome do cliente |
| 4 | D | CNPJ | 🟢 manual | **Chave primária** |
| 5 | E | UF | 🟢 manual | Estado |
| 6 | F | REDE / REGIONAL | 🟢 manual | Rede de franquia ou região |
| 7 | G | SITUAÇÃO | 🟢 dropdown | ATIVO, EM RISCO, INAT.REC, INAT.ANT, PROSPECT, NOVO, LEAD |
| 8 | H | DIAS SEM COMPRA | 🟢 manual | Puxar do Mercos ou DRAFT 1 |
| **9** | **I** | **ESTÁGIO FUNIL** | **🔵 auto** | `INDEX/MATCH(G&R, REGRAS motor)` → col C |
| **10** | **J** | **TIPO CLIENTE** | **🔵 auto** | `INDEX/MATCH(CNPJ, DRAFT 1!AP)` |
| **11** | **K** | **FASE** | **🔵 auto** | `INDEX/MATCH(G&R, REGRAS motor)` → col D |
| **12** | **L** | **SINALEIRO** | **🔵 auto** | Usa CICLO MÉDIO real do DRAFT 1!AG |
| 13 | M | TENTATIVA | 🟢 manual | T1, T2, T3, T4, T5, T6 |
| 14 | N | WHATSAPP | 🟢 dropdown | SIM/NÃO |
| 15 | O | LIGAÇÃO | 🟢 dropdown | SIM/NÃO |
| 16 | P | LIGAÇÃO ATENDIDA | 🟢 dropdown | SIM/NÃO/N/A |
| **17** | **Q** | **TIPO DO CONTATO** | **🔵 auto** | `INDEX/MATCH(G&R, REGRAS motor)` → col E |
| 18 | R | RESULTADO | 🟢 dropdown | 12 opções do REGRAS |
| 19 | S | MOTIVO | 🟢 dropdown | 10 opções do REGRAS |
| **20** | **T** | **FOLLOW-UP** | **🔵 auto** | `DATA + VLOOKUP(RESULTADO, dias)` |
| **21** | **U** | **AÇÃO FUTURA** | **🔵 auto** | `INDEX/MATCH(G&R, REGRAS motor)` → col F |
| **22** | **V** | **AÇÃO DETALHADA** | **🔵 auto** | `RESULTADO & " → " & AÇÃO FUTURA` |
| 23 | W | MERCOS ATUALIZADO | 🟢 dropdown | SIM/NÃO |
| 24 | X | NOTA DO DIA | 🟢 manual | Texto livre |

#### ⚠️ IMPORTANTE — ARRAY FORMULAS:
As fórmulas dos campos automáticos usam `MATCH(G&R, A&B)` que é **array formula**:
- **Excel 365:** Funciona direto (enter normal)
- **Excel antigo:** Precisa de **Ctrl+Shift+Enter** em cada célula

#### ⚠️ O QUE PRECISA POPULAR:
- **Cada atendimento = 1 linha nova**
- Preencher apenas as 13 colunas verdes
- Os 11 campos azuis calculam sozinhos baseado em SITUAÇÃO (G) + RESULTADO (R)

#### Exemplos de como o motor funciona:
```
SITUAÇÃO=ATIVO + RESULTADO=VENDA → ESTÁGIO=PÓS-VENDA, FASE=PÓS-VENDA, AÇÃO=PÓS-VENDA, TEMP=🔥
SITUAÇÃO=INAT.ANT + RESULTADO=EM ATEND → ESTÁGIO=EM ATENDIMENTO, FASE=RECUPERAÇÃO, AÇÃO=REATIVAÇÃO, TEMP=🟡
SITUAÇÃO=PROSPECT + RESULTADO=ORÇAMENTO → ESTÁGIO=ORÇAMENTO, FASE=ORÇAMENTO, AÇÃO=PROSPECÇÃO, TEMP=🔥
SITUAÇÃO=ATIVO + RESULTADO=NÃO ATENDE → ESTÁGIO=ANTERIOR, FASE=RECOMPRA, AÇÃO=RECOMPRA, TEMP=❄️
```

---

### 3.5 ABA LOG (9 linhas × 24 colunas)

**Função:** Histórico consolidado. Headers idênticos ao DRAFT 2 (24 cols). Os registros do DRAFT 2 são movidos pra cá periodicamente pra manter o DRAFT 2 leve.

**Status:** ✅ Headers V3 alinhados. Pronto pra receber dados.

---

### 3.6 ABA CARTEIRA (200 linhas × 257 colunas)

**Função:** Visão 360° do cliente. Uma linha por CNPJ. 4 mega-blocos.

#### Mega-bloco 1: MERCOS (cols 1-43)
| CONTEÚDO | STATUS |
|----------|--------|
| Âncora: col 1 = NOME FANTASIA, col 2 = CNPJ | Dados do DRAFT 1 via INDEX/MATCH |
| Vendas mensais, recorrência, ecommerce | Fórmulas prontas |
| Col 10: TIPO CLIENTE | ✅ V3 adicionado (puxa DRAFT 1!AP) |
| Col 14: SITUAÇÃO | Manual (ATIVO, INAT.REC, etc.) |

#### Mega-bloco 2: FUNIL (cols 44-61)
| COL | HEADER | FÓRMULA |
|-----|--------|---------|
| 44 | ESTÁGIO FUNIL | ✅ Último do DRAFT 2 (INDEX/MATCH por CNPJ+data) |
| 45 | PRÓX. FOLLOW-UP | ✅ Último do DRAFT 2 |
| 46 | DATA ÚLT. ATENDIMENTO | ✅ MAX(datas do DRAFT 2 por CNPJ) |
| 47 | ÚLTIMO RESULTADO | ✅ Último do DRAFT 2 |
| 48 | MOTIVO | ✅ Último do DRAFT 2 |
| 49 | TIPO CLIENTE | ✅ Do DRAFT 1!AP |
| 50 | TENTATIVA | ✅ Último do DRAFT 2 |
| 51 | FASE | ✅ Último do DRAFT 2 |
| 53 | TEMPERATURA | ✅ Motor REGRAS (SITUAÇÃO×RESULTADO) |
| 59 | PRÓX. AÇÃO | ✅ Último do DRAFT 2 |
| 60 | AÇÃO DETALHADA | ✅ Último do DRAFT 2 |
| 61 | 🚦 SINALEIRO | ✅ Ciclo médio real (não mais 50/90 fixo) |

**⚠️ As fórmulas do bloco FUNIL são array formulas (mesmo aviso do DRAFT 2).**

#### Mega-bloco 3: SAP (cols 62-72)
| CONTEÚDO | STATUS |
|----------|--------|
| Código cliente, grupo, gerente, representante, vendedor interno, canal, tipo, região | ⚠️ Sem fórmulas — popular manualmente da BASE SAP |

#### Mega-bloco 4: ACOMPANHAMENTO (cols 73-257)
| CONTEÚDO | STATUS |
|----------|--------|
| Col 73: % ATINGIMENTO GERAL | ✅ Fórmula (PROJEÇÃO real/meta) |
| Cols 74/120/166/212: Q1/Q2/Q3/Q4 | ✅ Fórmula (real_q/meta_q) |
| 12 meses × 15 cols cada: %YTD, META YTD, REAL YTD, %TRI, META TRI, REAL TRI, %MÊS, META, REALIZADO, DATA PEDIDO, JUST SEM1-4, JUST MENSAL | ✅ %YTD/%TRI/%MÊS = fórmulas prontas, META/REAL puxam da PROJEÇÃO |

#### ⚠️ O QUE PRECISA POPULAR:
- **Bloco MERCOS (1-43):** Popular conforme DRAFT 1 for preenchido (INDEX/MATCH)
- **Bloco SAP (62-72):** Colar dados da BASE SAP manualmente
- **Bloco ACOMPANHAMENTO:** As fórmulas calculam sozinhas a partir da PROJEÇÃO
- **DATA PEDIDO + JUSTIFICATIVAS:** Manual, conforme consultores preenchem

---

### 3.7 ABA AGENDA (5000 linhas × 24 colunas)

**Função:** Agenda diária dos consultores. Mesma estrutura do DRAFT 2 (24 cols). Área azul = contexto pré-preenchido, área verde = resultado a registrar.

**Status:** ✅ Estrutura + dropdowns prontos. SCORE referenciado na col 7.

**Como usar:**
1. Filtrar por CONSULTOR
2. Ordenar por SCORE (decrescente) ou FOLLOW-UP (crescente)
3. Máximo ~40 contatos/dia por consultor
4. Após preencher resultado, mover linha para DRAFT 2

---

### 3.8 ABA DASH (164 linhas × 19 colunas)

**Função:** Dashboard de KPIs do time. Blocos padronizados 15×17 com fórmulas dinâmicas.

**KPIs rastreados:**
💬 WhatsApp enviados | 📱 Ligações feitas | ✅ Ligações atendidas | 🔍 Prospecções | 📋 Orçamentos | 🔄 Follow ups | 🤝 Pós-venda | 📊 Cadastros

**Status:** ✅ V2 refinado (17 iterações). Cores padronizadas (#1F4E79 títulos, #4472C4 sub-headers, #D9D9D9 totais).

---

### 3.9 ABA Claude Log (27 linhas × 6 colunas)

**Função:** Registro de todas as alterações feitas pelo Claude. Rastreabilidade completa.

---

## 4. CHECKLIST: O QUE FALTA PREENCHER

### 🔴 PRIORIDADE 1 — Sem isso nada funciona:

- [ ] **DRAFT 1 linhas 4-500:** Colar base de clientes com CNPJ, nome, UF, rede, consultor, vendas mês a mês, curva ABC, ciclo médio, dias sem compra, etc.
  - **Fontes:** `Carteira_detalhada_de_clientes_atualizado_janeiro_2026.xlsx` + `Relatorio_vendas_janeiro_2026.xlsx` + `Curva_ABC_janeiro_2026.xlsx` + `Positivacao_de_Clientes_Janeiro_2026.xlsx`

### 🟡 PRIORIDADE 2 — Após DRAFT 1:

- [ ] **DRAFT 2:** Começar a registrar atendimentos diários (mínimo: DATA, CONSULTOR, CNPJ, SITUAÇÃO, RESULTADO)
- [ ] **CARTEIRA bloco SAP (cols 62-72):** Colar dados da `BASE_SAPE__CARTEIRA_CLIENTE_INTERNO_COM_VENDA_.xlsx`
- [ ] **PROJEÇÃO:** Verificar se metas distribuídas fazem sentido. Ajustar manualmente prospects/novos se necessário

### 🟢 PRIORIDADE 3 — Refinamento:

- [ ] **CARTEIRA bloco ACOMPANHAMENTO:** Justificativas semanais/mensais (manual)
- [ ] **AGENDA:** Popular com clientes prioritários, ordenar por SCORE
- [ ] **DASH:** Validar que fórmulas estão puxando corretamente do DRAFT 2

---

## 5. REGRAS QUE NÃO PODEM SER QUEBRADAS

1. **CNPJ é a chave primária** — col B do DRAFT 1, col D do DRAFT 2, col B da CARTEIRA, col A da PROJEÇÃO. Tudo cruza por CNPJ.

2. **Layout de 46 colunas do DRAFT 1 é IMUTÁVEL** — não inserir/deletar colunas. Adicionar só no final.

3. **Motor de regras (REGRAS R128-R190) é IMUTÁVEL** — as fórmulas do DRAFT 2 referenciam $A$128:$A$190 e $B$128:$B$190. Se adicionar linhas, atualizar os ranges.

4. **Tabela ref PROJEÇÃO (cols AP+) é IMUTÁVEL** — VLOOKUP das cols 5-9 referenciam esse range.

5. **Array formulas** — no Excel antigo, Ctrl+Shift+Enter. No 365, funciona direto.

6. **Cores de SITUAÇÃO:**
| SITUAÇÃO | COR HEX | COR |
|----------|---------|-----|
| ATIVO | #00B050 | Verde |
| EM RISCO | #FFC000 | Amarelo |
| INAT.REC | #FFC000 | Amarelo |
| INAT.ANT | #FF0000 | Vermelho |
| PROSPECT | #7030A0 | Roxo |
| NOVO | #4472C4 | Azul |
| LEAD | #7030A0 | Roxo |

7. **Nunca fabricar dados** — se não tem dado real, deixar vazio.

8. **HTML/dashboards sempre em light theme** — nunca dark mode.

---

## 6. FONTES DE DADOS DISPONÍVEIS NO PROJETO

### Para popular DRAFT 1:
| DADO | ARQUIVO |
|------|---------|
| Base clientes (CNPJ, nome, UF, rede, consultor) | `Carteira_detalhada_de_clientes_atualizado_janeiro_2026.xlsx` |
| Vendas mês a mês | `Relatorio_vendas_*.xlsx` (um por mês, mar/25 a jan/26) |
| Curva ABC | `Curva_ABC_*.xlsx` (mensal) ou `Curva_ABC_2025_Anual.xlsx` |
| Positivação | `Positivacao_de_Clientes_*.xlsx` (mensal) |
| E-commerce acessos | `Acesso_ao_Ecomerce_*.xlsx` (mensal) |
| Atendimentos Mercos | `Relatorio_de_Atendimentos_Mercos_2025.xlsx` |
| Dias sem compra, ciclo | `Carteira_detalhada_de_clientes_atualizado_janeiro_2026.xlsx` |

### Para popular CARTEIRA bloco SAP:
| DADO | ARQUIVO |
|------|---------|
| Código, grupo, gerente, representante | `BASE_SAPE__CARTEIRA_CLIENTE_INTERNO_COM_VENDA_.xlsx` |
| Meta 2026 | `BASE_SAP__META_E_PROJEÇÃO_2026___02__INTERNO__2026.xlsx` |
| Clientes sem atendimento | `BASE_SAP_CLIENTES_SEM_ATENDIMENTO_.xlsx` |
| Vendas SAP | `BASE_SAP__VENDA_MES_A_MES_2025.xlsx` |

### Sinaleiro (já integrado):
| DADO | ARQUIVO |
|------|---------|
| 8 redes de franquia | `SINALEIRO_REDES_VITAO.xlsx` |
| 661 clientes interno | `SINALEIRO_INTERNO_CONFIAVEL.xlsx` |

### Tickets WhatsApp / Deskrio:
| DADO | ARQUIVO |
|------|---------|
| Conversas WPP | `exporttickets19012026_*.xlsx` (11 arquivos) |

---

## 7. PROMPT PARA NOVA CONVERSA

Cole isto no início da nova conversa:

```
Estou continuando o preenchimento do CRM VITAO360 V3.
O arquivo CRM_INTELIGENTE_VITAO360_V3.xlsx já tem toda a estrutura pronta (9 abas, motor de regras, fórmulas).

TAREFA ATUAL: Popular a aba DRAFT 1 com dados reais.

REGRAS:
- CNPJ é chave primária (col B do DRAFT 1)
- Layout de 45 colunas é IMUTÁVEL — não inserir/deletar colunas
- Não fabricar dados — só usar o que vem dos arquivos
- Array formulas: Excel 365 funciona direto

Vou colar os dados fonte e preciso que você:
1. Leia a estrutura do arquivo colado
2. Mapeie quais colunas vão para quais colunas do DRAFT 1
3. Gere o código Python (openpyxl) para popular as linhas
4. Entregue a planilha atualizada

[Colar aqui o HANDOFF_CRM_V3.md como contexto]
[Fazer upload da CRM_V3 + arquivo(s) fonte]
```

---

## 8. ESPECIFICAÇÃO TÉCNICA DAS FÓRMULAS V3

### DRAFT 2 — Fórmulas automáticas (referem REGRAS R128:R190)

```excel
# ESTÁGIO FUNIL (col I / 9):
=IF(R{r}="","",IFERROR(INDEX(REGRAS!$C$128:$C$190,MATCH(G{r}&R{r},REGRAS!$A$128:$A$190&REGRAS!$B$128:$B$190,0)),""))

# TIPO CLIENTE (col J / 10):
=IF(D{r}="","",IFERROR(INDEX('DRAFT 1'!$AP:$AP,MATCH(D{r},'DRAFT 1'!$B:$B,0)),""))

# FASE (col K / 11):
=IF(R{r}="","",IFERROR(INDEX(REGRAS!$D$128:$D$190,MATCH(G{r}&R{r},REGRAS!$A$128:$A$190&REGRAS!$B$128:$B$190,0)),""))

# SINALEIRO CICLO (col L / 12):
=IF(H{r}="","",IF(OR(G{r}="PROSPECT",G{r}="LEAD"),"🟣",IF(G{r}="NOVO","🟢",
  LET(ciclo,IFERROR(INDEX('DRAFT 1'!$AG:$AG,MATCH(D{r},'DRAFT 1'!$B:$B,0)),0),
  IF(ciclo=0,IF(H{r}<=50,"🟢",IF(H{r}<=90,"🟡","🔴")),
  IF(H{r}<=ciclo,"🟢",IF(H{r}<=ciclo+30,"🟡","🔴")))))))

# TIPO DO CONTATO (col Q / 17):
=IF(R{r}="","",IFERROR(INDEX(REGRAS!$E$128:$E$190,MATCH(G{r}&R{r},REGRAS!$A$128:$A$190&REGRAS!$B$128:$B$190,0)),""))

# AÇÃO FUTURA (col U / 21):
=IF(R{r}="","",IFERROR(INDEX(REGRAS!$F$128:$F$190,MATCH(G{r}&R{r},REGRAS!$A$128:$A$190&REGRAS!$B$128:$B$190,0)),""))

# AÇÃO DETALHADA (col V / 22):
=IF(R{r}="","",R{r}&" → "&IFERROR(INDEX(REGRAS!$F$128:$F$190,MATCH(G{r}&R{r},REGRAS!$A$128:$A$190&REGRAS!$B$128:$B$190,0)),""))
```

### PROJEÇÃO — Meta distribuída

```excel
# META MÊS (cols K-V / 11-22):
=IF(A{r}="","",IFERROR($AS${meta_row}*(SUM('DRAFT 1'!$U{r}:$AF{r})/SUM('DRAFT 1'!$U$4:$AF$503)),0))

# Onde $AS${meta_row} contém o valor da META global do mês (da tabela ref)
# meta_row varia: JAN=R20, FEV=R21, ..., DEZ=R31 (na tabela ref cols AP+)
```

### CARTEIRA FUNIL — Último registro por CNPJ

```excel
# Padrão usado em cols 44-60 (exemplo ESTÁGIO FUNIL col 44):
=IFERROR(INDEX('DRAFT 2'!$I:$I,MATCH(1,INDEX(('DRAFT 2'!$D:$D=$B{r})*('DRAFT 2'!$A:$A=MAX(IF('DRAFT 2'!$D:$D=$B{r},'DRAFT 2'!$A:$A))),0,1),0)),"")

# Lógica: encontra a linha com CNPJ=$B{r} E data=MAX(datas desse CNPJ)
```

---

## 9. SINALEIRO INTERNO — RESUMO DOS DADOS

### Distribuição por cor (661 clientes):
| COR | QTD | % |
|-----|-----|---|
| 🟢 VERDE | 129 | 19.5% |
| 🟡 AMARELO | 65 | 9.8% |
| 🔴 VERMELHO | 298 | 45.1% |
| 🟣 ROXO | 169 | 25.6% |

### Por consultor:
| CONSULTOR | VERDE | AMARELO | VERMELHO | ROXO | TOTAL |
|-----------|-------|---------|----------|------|-------|
| MANU | 157 | 18 | 0 | 30 | 205 |
| LARISSA | 164 | 34 | 0 | 26 | 224 |
| JULIO | 64 | 11 | 0 | 67 | 142 |
| DAIANE | 42 | 2 | 0 | 46 | 90 |

### Por UF (top 6):
| UF | QTD | REALIZADO | POTENCIAL |
|----|-----|-----------|-----------|
| SC | 203 | R$ 396.871 | R$ 1.750.070 |
| SP | 99 | R$ 320.538 | R$ 615.474 |
| PR | 85 | R$ 308.408 | R$ 563.427 |
| MG | 34 | R$ 152.788 | R$ 211.122 |
| RS | 73 | R$ 125.853 | R$ 530.465 |
| PE | 16 | R$ 123.572 | R$ 90.514 |

---

## 10. ARQUIVOS FONTE NO PROJETO CLAUDE

Todos os arquivos estão em `/mnt/project/` e podem ser lidos com `view` ou processados com Python:

```
/mnt/project/Carteira_detalhada_de_clientes_atualizado_janeiro_2026.xlsx
/mnt/project/Relatorio_vendas_janeiro_2026.xlsx
/mnt/project/Curva_ABC_janeiro_2026.xlsx
/mnt/project/Positivacao_de_Clientes_Janeiro_2026.xlsx
/mnt/project/Relatorio_de_Atendimentos_Mercos_2025.xlsx
/mnt/project/BASE_SAPE__CARTEIRA_CLIENTE_INTERNO_COM_VENDA_.xlsx
/mnt/project/BASE_SAP__META_E_PROJEÇÃO_2026___02__INTERNO__2026.xlsx
/mnt/project/BASE_SAP__VENDA_MES_A_MES_2025.xlsx
/mnt/project/SINALEIRO_REDES_VITAO.xlsx (upload separado)
/mnt/project/SINALEIRO_INTERNO_CONFIAVEL.xlsx (upload separado)
```

---

*Documento gerado em 09/02/2026. Versão V3 final.*
