# PRD — CRM VITAO360
## Motor de Inteligência Comercial para Distribuidora B2B

**Data:** 23/03/2026
**Versão:** 1.0
**Status:** Aprovado
**Proprietário:** VITAO Alimentos

---

## SUMÁRIO EXECUTIVO

**Produto:** CRM VITAO360 — Sistema inteligente de gestão comercial com 92 combinações de regras, motor de priorização automática e dashboard executivo.

**Problema:** A distribuidora VITAO Alimentos sofre com churn estrutural de 80%, falta de pós-venda e retenção crítica: 57% dos clientes compram apenas uma vez. Sem inteligência comercial, a equipe trabalha de forma reativa.

**Solução:** Motor ponderado de 9 dimensões gerando 8 níveis de prioridade (P0-P7), scoring automático, agenda inteligente com limite de 40 atendimentos/dia por consultor, e sinaleiro de penetração de redes.

**Resultado Esperado (2026):**
- Faturamento: R$ 3.157M (+51% vs 2025)
- Ativos P12: 684 clientes
- ROI: 7,4x (R$ 375K investimento → R$ 2,78M sobra)
- Churn: 80% → 50% (com pós-venda Q3)
- CAC: R$ 426/cliente

---

## 1. CONTEXTO E PROBLEMA

### 1.1 Situação Inicial
VITAO Alimentos é uma distribuidora B2B de alimentos naturais embalados, sediada em Curitiba/PR, com 4 consultores comerciais internos + 1 RCA externo. Em outubro de 2024, o CRM anterior (ExactSales SaaS) foi encerrado, resultando em:
- Perda total do histórico de 354 clientes (60-90 dias)
- Faturamento 2025: R$ 2.091.000 (PAINEL CEO auditado)
- Taxa de recompra: apenas 20,3% ao ano
- Churn mensal: 80% (confirmado em Q1 2026: 83%)

### 1.2 Diagnóstico Crítico
A auditoria forense de 68 arquivos revelou:
- 57% dos clientes (279 de 488) realizaram apenas 1 compra
- Ticket médio anual: R$ 4.285/cliente
- Ciclo médio observado: 1,9 meses entre pedidos
- CAC estimado: R$ 426
- LTV: R$ 2.792 (insuficiente)

### 1.3 Raiz do Problema
Sem sistema de priorização e acompanhamento estruturado, consultores não fazem:
- Follow-up automático D+4 (pós-venda imediato)
- Alertas de ciclo (D+45 para recompra)
- Segmentação por potencial
- Ações por fase do funil (prospecção ≠ recompra)

---

## 2. EQUIPE COMERCIAL

| CONSULTOR | CARGO | TERRITÓRIO | STATUS 2026 | % FAT 2025 |
|-----------|-------|-----------|-----------|-----------|
| LARISSA PADILHA | Rep PDV | Brasil Interior | Ativa | 45% |
| JULIO GADRET | Rep PDV | Cia Saúde + Fitland | Ativo | 10% |
| DAIANE STAVICKI | Gerente Redes | Franquias Nacionais | Nova atribuição | 12,5% |
| MANU DITZEL | Rep PDV | SC/PR/RS | Licença Q2 | 32,5% |
| **NOVA REP** | Rep PDV | SC/PR/RS (Manu) | Contratar Q2 | — |
| **PÓS-VENDA** | CS + Suporte | Todos 661 | Contratar Q3 | — |

**Notas:**
- Rodrigo (952 tickets Deskrio) = operador do canal "Mais Granel" (Larissa)
- Manu entra em licença maternidade Q2 → carteira descoberta
- Pós-venda é crítico para reduzir churn de 80% → 50% em 90 dias

### 2.1 Funil Diário Esperado
- **22 contatos/rep/dia** (489/mês) → 100% base
- **7 visitas/rep/dia** (147/mês) → 30% conversão
- **3 propostas/rep/dia** (73/mês) → 50% das visitas
- **1 fechamento/rep/dia** (22/mês) → 30% das propostas
- **12-15 follow-ups PV/dia** → D+4 obrigatório (Q3)

---

## 3. ARQUITETURA DO SISTEMA

### 3.1 Fluxo de Dados (Two-Base Architecture)

```
MERCOS (vendas)        SAP (ERP)          DESKRIO (WhatsApp)
         |                  |                     |
         +------ DRAFT 1,2,3 ------+
                                   |
                          CARTEIRA (46 colunas)
                                   |
          +--------+--------+-------+-------+
          |        |        |       |       |
        AGENDA    LOG    PROJEÇÃO  DASH   SINALEIRO
```

**Princípio fundamental:** Separação absoluta de VENDA (R$ real) e LOG (R$ 0.00 sempre).

### 3.2 CARTEIRA — Motor Central
- 46 colunas imutáveis (A-AT)
- 489 clientes operacionais
- Blocos: Identificação → Atribuição → Status → Último Pedido → Performance → Faturamento Mensal → E-commerce → Classificações → Funil → Acompanhamento

### 3.3 Chave Primária
CNPJ normalizado: 14 dígitos, string, zero-padded (ex: `04351343000169`). Obrigatório em todos os cruzamentos de dados.

---

## 4. MOTOR DE REGRAS — CORE DO PRODUTO

### 4.1 Arquitetura de 9 Dimensões

| # | DIMENSÃO | VALORES | QUEM PREENCHE | REGRA |
|---|----------|---------|---------------|-------|
| 1 | SITUAÇÃO | ATIVO, INAT.REC, INAT.ANT, PROSPECT | Mercos (auto) | Read-only |
| 2 | ESTÁGIO FUNIL | 14 posições sequenciais | Motor + Consultor | Fluxo Kanban |
| 3 | RESULTADO | 9 tipos (VENDA, ORÇAMENTO, etc) | Consultor (dropdown) | 1 por atendimento |
| 4 | TIPO CLIENTE | 7 estágios maturidade | Motor (histórico) | Baseado pedidos |
| 5 | FASE | 6 estratégias comerciais | Motor | SITUAÇÃO × TIPO |
| 6 | CURVA ABC | A (20%), B (30%), C (50%) | Motor | Faturamento |
| 7 | TEMPERATURA | QUENTE, MORNO, FRIO, CRÍTICO, PERDIDO | Motor (auto) | Engajamento |
| 8 | SINALEIRO | VERDE, AMARELO, VERMELHO, ROXO | Motor | Dias vs ciclo |
| 9 | TENTATIVAS | T1, T2, T3, T4, NUTRIÇÃO, RESET | Motor (incrementa) | Sequência contato |

### 4.2 Score Ponderado (6 dimensões)

```
PRIORIDADE = (FASE × 25%) + (SINALEIRO × 20%) + (ABC × 20%) +
             (TEMPERATURA × 15%) + (TIPO CLIENTE × 10%) + (TENTATIVAS × 10%)
```

**Scoring por dimensão:**
- FASE: RECOMPRA=100 > NEGOCIAÇÃO=80 > SALVAMENTO=60 > RECUPERAÇÃO=40 > PROSPECÇÃO=30 > NUTRIÇÃO=10
- SINALEIRO: VERMELHO=100 > AMARELO=60 > VERDE=30 > ROXO=0
- ABC: A=100 > B=60 > C=30
- TEMPERATURA: QUENTE=100 > MORNO=60 > FRIO=30 > CRÍTICO=20 > PERDIDO=0
- TIPO CLIENTE: MADURO=100 > FIDELIZADO=85 > RECORRENTE=70 > EM DESENV=50 > NOVO=30 > LEAD=15 > PROSPECT=10
- TENTATIVAS: T1=100 > T2=70 > T3=40 > T4=10 > NUTRIÇÃO=5

### 4.3 Prioridades (P0-P7)

| Nível | Nome | Como Gera | Score | Distribuição Diária | Regra |
|-------|------|-----------|-------|-------------------|-------|
| P0 | IMEDIATA | SUPORTE com problema aberto | N/A | Pula fila | Risco perda |
| P1 | URGENTE | EM ATENDIMENTO + FU vencido | N/A | ≤15/dia | Namoro não esfriar |
| P2 | ALTA | Score 80-100 | 80-100 | 15-20/dia | Top lista |
| P3 | MÉDIA-ALTA | Score 60-79 | 60-79 | 15-20/dia | Segundo bloco |
| P4 | MÉDIA | Score 45-59 | 45-59 | 5-10/dia | Corpo agenda |
| P5 | MÉDIA-BAIXA | Score 30-44 | 30-44 | 5-10/dia | Se sobrar |
| P6 | BAIXA | Score 15-29 | 15-29 | 0-5/dia | Última prioridade |
| P7 | NUTRIÇÃO | Score 0-14 | 0-14 | 0 (campanha) | Fora dos 40/dia |

### 4.4 Os 14 Estágios do Funil

**Pré-venda:** INÍCIO CONTATO → TENTATIVA → PROSPECÇÃO → EM ATENDIMENTO
**Venda:** CADASTRO → ORÇAMENTO → PEDIDO
**Pós-venda:** ACOMP POS-VENDA (D+4) → POS-VENDA (D+15) → CS (D+30)
**Loops:** FOLLOW-UP → NUTRICAO
**Auxiliares:** SUPORTE, RELACIONAMENTO

### 4.5 As 6 Fases Estratégicas

| FASE | SITUAÇÃO TÍPICA | SCORE | AÇÃO |
|------|-----------------|-------|------|
| PROSPECÇÃO | Prospect + T1-T4 | 30 | 1ª conquista |
| NEGOCIAÇÃO | Ativo em conversa | 80 | Namoro novo |
| RECOMPRA | Ativo no ciclo | 100 | Cultivar |
| SALVAMENTO | INAT.REC (parou) | 60 | Salvar antes piorar |
| RECUPERAÇÃO | INAT.ANT (sumiu) | 40 | Trazer volta |
| NUTRIÇÃO | T4+ sem resposta | 10 | Campanha 1x/mês |

---

## 5. REQUISITOS FUNCIONAIS

### RF01 — Import Pipeline
Integração automatizada Mercos → SAP → Deskrio com normalização CNPJ, matching fuzzy/rigorous, e classificação 3-tier (REAL/SINTÉTICO/ALUCINAÇÃO).

### RF02 — Motor de Regras
92 combinações de regras ponderadas que geram ESTÁGIO, FASE, TEMPERATURA, AÇÃO automáticas baseadas nas 9 dimensões.

### RF03 — Score Engine
Cálculo ponderado em tempo real com 6 dimensões; resultado → Prioridades P0-P7.

### RF04 — Agenda Inteligente
40 atendimentos/dia/consultor, priorizados automaticamente, com remoção de duplicatas por CNPJ.

### RF05 — Sinaleiro de Redes
923 lojas em 8 redes (Fitland, Divina Terra, Vida Leve, Tudo em Grãos, Cia Saúde, Biomundo, Mundo Verde, Armazém Fitstore). Fórmula: (Fat.Real / (Total_Lojas × R$525/mês × 11 meses)) × 100. Cores ROXO (<1%) → VERMELHO → AMARELO → VERDE (>60%).

### RF06 — Projeção Mensal
12 meses de projeção com componentes: Base Orgânica, Novos PDVs, Recompras, Redes, Custo Equipe. Resultado: Faturamento, Sobra, Acumulado, Ativos, Unit Economics.

### RF07 — Dashboard PAINEL CEO
3 blocos compactos (~45 linhas): KPIs Executivos (FAT, ATIVOS, CHURN, CAC, ROI), Sinaleiro CRM (distribuição por cor), Ramp-up Equiper (fases F1-F4).

### RF08 — LOG (Append-only)
1.581+ registros de interações (ligação, WhatsApp, visita, etc). Chave: DATA + CNPJ + RESULTADO. Two-Base: SEMPRE R$ 0.00.

### RF09 — RNC (Registro Não Conformidades)
Rastreamento de problemas reportados (entrega, qualidade, NF) com status e resolução.

### RF10 — Abas por Consultor
LARISSA, JULIO, DAIANE: carteira filtrada, agenda própria, KPIs individuais.

---

## 6. REQUISITOS NÃO-FUNCIONAIS

### RNF01 — Fórmulas openpyxl em INGLÊS
IF, VLOOKUP, SUMIF, COUNTIF. Separador: vírgula (,). Nunca português.

### RNF02 — CNPJ String Normalizado
14 dígitos, sem pontuação. Nunca float/int. `re.sub(r'\D', '', str(val)).zfill(14)`.

### RNF03 — Two-Base Architecture Inviolável
VENDA = R$ real; LOG = R$ 0.00 SEMPRE. Violação = inflação de 742%.

### RNF04 — Zero Dados Fabricados
3-tier obrigatória: REAL (rastreável) / SINTÉTICO (fórmula de REAL) / ALUCINAÇÃO (nunca). 558 registros já catalogados como ALUCINAÇÃO.

### RNF05 — Faturamento Baseline = R$ 2.091.000
Tolerância ±0.5%. Corrigido após auditoria forense de 68 arquivos (era R$ 2.156.179 — superseded).

### RNF06 — Visual LIGHT Exclusivamente
Sem dark mode. Fonte Arial 9pt (dados), 10pt (headers). Cores status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000. ABC: A=#00B050, B=#FFFF00, C=#FFC000.

### RNF07 — Validação Pós-Build Obrigatória
- 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?)
- Faturamento = R$ 2.091.000 (±0.5%)
- Two-Base respeitada
- CNPJ sem duplicatas
- 14 abas presentes
- Testar no Excel real (LibreOffice ≠ Excel recalc)

---

## 7. MODELO FINANCEIRO

### 7.1 Ramp-up de 12 Meses (F1-F4)

**Fases:**
- **F1 (P1-P3, Q1):** 2 Reps + Daiane | R$ 22K/mês | Operação atual
- **F2 (P4-P6, Q2):** 3 Reps + Daiane (Nova Rep) | R$ 29K/mês | Substituição Manu
- **F3 (P7-P9, Q3):** 3 Reps + Daiane + Pós-Venda | R$ 34K/mês | CRÍTICO: churn 75%→50%
- **F4 (P10-P12, Q4):** 4 Reps + Daiane + PV | R$ 40K/mês | Aceleração

**Custo Total 2026:** R$ 375.000 (R$ 22K×3 + R$ 29K×3 + R$ 34K×3 + R$ 40K×3)

### 7.2 Projeção de Receita

**Componentes mensais:**
- **Base Orgânica:** R$ 120K-122K (clientes mantidos)
- **Novos PDVs:** R$ 66K-132K (ticket R$ 1.500)
- **Recompras PDV:** R$ 0-30K (ciclo 60 dias)
- **Redes + Recompra Redes:** R$ 12K-42K (ticket R$ 2.500)

**Resultado anual:**
- **FAT 2026:** R$ 3.156.614 (+51% vs 2025)
- **CUSTO:** -R$ 375.000
- **SOBRA:** R$ 2.781.614
- **ATIVOS P12:** 684
- **ROI:** 7,4x (Sobra / Investimento)
- **CAC:** R$ 426/cliente
- **Payback:** Mês 1

### 7.3 Unit Economics

| Métrica | P1 | P6 | P12 | Ano |
|---------|----|----|-----|-----|
| Ticket Médio | R$ 1.965 | R$ 1.013 | R$ 479 | R$ 4.615 |
| CAC | R$ 449 | R$ 392 | R$ 408 | R$ 426 |
| Novos/mês | 49 | 66 | 88 | 65 |
| Ativos | 101 | 253 | 684 | 684 |

### 7.4 Validação Q1 2026

**Real vs Modelo:**
- Faturamento: Modelo R$ 503K | Real R$ 459K* (Março parcial — 13 de 22 dias)
- Ticket 1ª compra: Modelo R$ 1.500 | Real R$ 1.569 ✓ (+4,6%)
- Churn: Modelo 80% | Real 83% ✓ (confirmado)
- Novos clientes: Modelo 22/mês | Real 59/mês ✓✓ (+168% SEM vendedora)
- Recompras: Modelo ~10 | Real 30 ✓✓ (+200%)

**Veredito:** Modelo CONSERVADOR. 4 de 5 premissas confirmadas ou superadas.

---

## 8. VALIDAÇÃO E QUALIDADE

### 8.1 Detector de Mentira (3 Níveis)

**Nível 1 — Existência:**
- Arquivo existe no path esperado?
- Formato correto (.xlsx, .json, .py)?
- Pode ser aberto sem erro?

**Nível 2 — Substância (Anti-Stub):**
- Fórmulas retornam valores (0 #REF!, #DIV/0!)?
- Dados vêm de fonte rastreável?
- Classificação 3-tier presente?
- CNPJ = string 14 dígitos?
- Fórmulas em INGLÊS?
- Two-Base respeitada?

**Nível 3 — Conexão (Wired):**
- Fórmulas referenciam abas que existem?
- INDEX-MATCH bate com range real?
- Named Ranges apontam para válidas?

### 8.2 Tresholds de Qualidade

| Métrica | Mínimo | Ideal | Bloqueante se |
|---------|--------|-------|---------------|
| Fórmulas com erro | 0 | 0 | > 0 |
| Two-Base violações | 0 | 0 | > 0 |
| CNPJ como float | 0 | 0 | > 0 |
| Fórmulas português | 0 | 0 | > 0 |
| Fat. vs baseline | ±0.5% | ±0.1% | > 0.5% |
| Dados ALUCINAÇÃO | 0 | 0 | > 0 |
| Abas presentes | 14 | 14 | < 14 |
| CNPJ duplicados | 0 | 0 | > 0 |
| Coverage clientes | > 90% | 100% | < 80% |
| Coverage fat. | > 95% | 100% | < 90% |

### 8.3 Conflitos Resolvidos (Auditoria Forense)

| Tema | Valores Conflitantes | Decisão | Justificativa |
|------|---------------------|---------|---------------|
| Receita 2025 | R$ 2.091M vs R$ 2.156M | R$ 2.091M | PAINEL CEO definitivo |
| Receita 2026 | R$ 3.354M vs R$ 3.377M | R$ 3.377M | Motor mês a mês completo |
| Ativos P12 | 207 vs 546 vs 684 | 684 | Churn 80% real validado |
| ROI | 2,9x vs 10,2x | 7,4x | Eq. nova: R$ 375K inv |
| Churn Q3 meta | 52% vs 65% | 50% | PV reduz 75%→50% em 90d |

---

## 9. ROADMAP E FASES

### Fase Atual (Marco/2026)
- Motor de Regras 92 combinações ✓
- CARTEIRA 46 colunas ✓
- SINALEIRO redes ✓
- AGENDA inteligente ✓
- LOG 1.581+ registros (13,4% populado)

### Próximo Sprint (Abr/2026)
- Import Pipeline Python (Mercos → SAP → Deskrio)
- LOG completo (~11.758 registros)
- Projeção reconstruída (18.180 fórmulas)
- DASH redesign (3 blocos compactos)

### Q2-Q3 (Abr-Set/2026)
- Python motor de regras v2 (input/output JSON)
- Integração Mercos API (real-time)
- Pós-venda CS estruturado (F3, Q3)
- Churn reduction 80%→50%

### Q4+ (Out/2026+)
- Migração SaaS (Deskrio API + Mercos API)
- Mobile consultor
- WhatsApp integrado
- BI avançado

---

## 10. RISCOS E PREMISSAS

### Premissas Críticas
1. **Custo mensal equipe:** ~R$ 27.200/mês (estimado) — validar com RH
2. **Food Channel Daiane:** Não modelado — potencial incremental
3. **Ramp Nova Rep Q2:** 2 meses até capacidade plena
4. **Churn com PV Q3:** 50% em 90 dias (vs 80% atual)

### Riscos Principais
- Manu não retorna de licença → carteira vira orfã
- Pós-venda não implementada → churn fica 80%
- Mercos API instável → delay import
- Churn não reduz como esperado → sobra cai R$ 200K+

---

## 11. GLOSSÁRIO

| Termo | Definição |
|-------|-----------|
| TWO-BASE | Separação VENDA (R$) vs LOG (R$ 0.00) |
| SINALEIRO | Saúde do cliente: dias sem comprar vs ciclo médio |
| FASE | Estratégia comercial (PROSPECÇÃO, NEGOCIAÇÃO, RECOMPRA, etc) |
| ESTÁGIO | Posição no funil (INÍCIO CONTATO, EM ATENDIMENTO, PEDIDO, etc) |
| TEMPERATURA | Engajamento (QUENTE, MORNO, FRIO, CRÍTICO, PERDIDO) |
| TIPO CLIENTE | Maturidade (PROSPECT, LEAD, NOVO, EM DESENV, RECORRENTE, FIDELIZADO, MADURO) |
| CURVA ABC | Classificação por faturamento (A=20%, B=30%, C=50%) |
| CAC | Customer Acquisition Cost (custo por cliente novo) |
| LTV | Lifetime Value (valor total do cliente) |
| CHURN | Taxa de clientes que deixam de comprar (mensal) |
| FUNIL | Etapas do processo comercial (CONTATO → VENDA → RECOMPRA) |
| P0-P7 | Níveis de prioridade (P0=imediata, P7=nutrição) |
| MERCOS | ERP de vendas (fontes: relatórios .xlsx) |
| SAP | ERP corporativo (faturamento, metas, cadastros) |
| DESKRIO | CRM WhatsApp Business (77.805 mensagens, 5.425 conversas) |
| ALUCINAÇÃO | Dados fabricados (ChatGPT) — NUNCA integrar |
| REAL | Dados rastreáveis a Mercos, SAP ou Deskrio |
| SINTÉTICO | Dados derivados por fórmula de REAL |
| Q1-Q4 | Trimestres (Q1=Jan-Mar, Q2=Abr-Jun, etc) |
| P1-P12 | Períodos/meses (P1=Jan, P2=Fev, ..., P12=Dez) |
| F1-F4 | Fases de ramp-up de equipe |

---

## DECISÃO FINAL

Produto aprovado. Investimento inicial: R$ 375.000 (12 meses equipe ampliada). Retorno esperado: R$ 2.781.614 em sobra + 684 clientes ativos P12. ROI 7,4x com payback imediato (mês 1). Gating de entrada: validação Q1 2026 com modelo conservador. 4 de 5 premissas já confirmadas.

---

**Fonte dos dados:**
- painel_ceo.json: VITAO360_ULTRA_FINAL (5).xlsx
- diagnostico_2025.json: Auditoria forense 68 arquivos
- motor_regras_v4.json: 92 combinações, 9 dimensões
- equipe_2026.json: Organograma + roadmap contratações
- arquitetura_9_dimensoes.json: 9 dimensões + scoring
- estagios_funil.json: 14 estágios sequenciais
- fases_estrategicas.json: 6 fases comerciais
- motor_rampup.json: 12 meses projeção
- q1_2026_real.json: SAP Vendas Jan-Mar 2026
- conflitos_resolvidos.json: Auditoria decisões
- premissas.json: Fundamentação modelo
- BRIEFING-COMPLETO.md: 16 meses, 32 sessões, 88+ arquivos
