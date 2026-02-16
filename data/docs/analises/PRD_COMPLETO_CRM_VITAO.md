# 📋 PRODUCT REQUIREMENTS DOCUMENT (PRD)
## SISTEMA CRM VITÃO ALIMENTOS - ANÁLISE COMPLETA E REQUISITOS

**Versão:** 2.0  
**Data:** 15/12/2025  
**Autor:** Leandro  
**Status:** Em Desenvolvimento

---

## 🎯 1. SUMÁRIO EXECUTIVO

### 1.1 Contexto

A Vitão Alimentos enfrenta desafios críticos na gestão de relacionamento com clientes após perda de dados do CRM anterior (ExactSales). Este documento consolida análise completa de 867 vendas de 444 clientes em 2025, identificando oportunidades de otimização e requisitos para novo sistema.

### 1.2 Descobertas Críticas

**ALERTAS VERMELHOS:**
- 🔴 **Taxa de Retenção: 20.3%** - Apenas 43 de 212 clientes ativos recompram mensalmente
- 🔴 **169 clientes ativos em risco** - 79.7% dos ativos não compraram em NOV/2025
- 🔴 **Churn mensal: ~30 clientes** - Taxa de perda de 18% dos ativos/mês
- 🔴 **Taxa de positivação caiu 70%** - De 94.4% (MAR) para 28.4% (NOV)

**OPORTUNIDADES:**
- ✅ Crescimento de carteira: 2.289% (18→430 clientes)
- ✅ Receita total 2025: R$ 3.603.246,14
- ✅ 41 clientes VIP (LTV R$10k+) = 44.8% da receita
- ✅ Taxa de reativação crescente: 0%→27.7%

---

## 📊 2. ANÁLISE DE DADOS

### 2.1 Carteira Completa - Evolução Mensal

| MÊS | CARTEIRA | ATIVOS | INAT REC | INAT ANT | POSITIV | Δ CARTEIRA | % POSIT |
|-----|----------|--------|----------|----------|---------|------------|---------|
| MAR/25 | 18 | 18 | 0 | 0 | 17 | - | 94.4% |
| ABR/25 | 57 | 57 | 0 | 0 | 43 | +39 | 75.4% |
| MAI/25 | 115 | 103 | 12 | 0 | 70 | +58 | 60.9% |
| JUN/25 | 186 | 153 | 33 | 0 | 95 | +71 | 51.1% |
| JUL/25 | 225 | 153 | 72 | 0 | 73 | +39 | 32.4% |
| AGO/25 | 280 | 158 | 122 | 0 | 104 | +55 | 37.1% |
| SET/25 | 320 | 172 | 138 | 10 | 97 | +40 | 30.3% |
| OUT/25 | 372 | 189 | 159 | 24 | 116 | +52 | 31.2% |
| NOV/25 | 430 | 212 | 163 | 55 | 122 | +58 | 28.4% |
| **DEZ/25** | **444** | **213** | **161** | **70** | **45*** | **+14** | **10.1%*** |

*DEZ/25 parcial (até 15/12)

### 2.2 Segmentação RFM - Clientes por Valor

| SEGMENTO | QTD | % | VALOR TOTAL | VALOR MÉDIO | RECENCY | FREQ |
|----------|-----|---|-------------|-------------|---------|------|
| CAMPEÕES | 30 | 6.8% | R$ 351.919,65 | R$ 11.730,65 | 16d | 5 |
| CLIENTES FIÉIS | 52 | 11.7% | R$ 414.862,07 | R$ 7.978,12 | 34d | 3 |
| POTENCIAL FIDELIZAÇÃO | 44 | 9.9% | R$ 126.204,42 | R$ 2.868,28 | 21d | 1 |
| NOVOS PROMISSORES | 102 | 23.0% | R$ 212.777,89 | R$ 2.086,06 | 46d | 1 |
| PRECISA ATENÇÃO | 65 | 14.6% | R$ 137.598,22 | R$ 2.116,90 | 132d | 1 |
| CLIENTES EM RISCO | 34 | 7.7% | R$ 246.758,47 | R$ 7.257,60 | 127d | 2 |
| PRESTES A PERDER | 12 | 2.7% | R$ 68.197,67 | R$ 5.683,14 | 213d | 2 |
| HIBERNANDO | 105 | 23.6% | R$ 242.105,64 | R$ 2.305,77 | 189d | 1 |

### 2.3 Lifetime Value (LTV) - Concentração de Receita

| CATEGORIA | CLIENTES | % CLIENTES | VALOR TOTAL | % RECEITA | LTV MÉDIO |
|-----------|----------|------------|-------------|-----------|-----------|
| VIP (R$10k+) | 41 | 9.2% | R$ 807.098,52 | **44.8%** | R$ 19.685,33 |
| GOLD (R$5k-10k) | 46 | 10.4% | R$ 312.809,55 | 17.4% | R$ 6.800,21 |
| SILVER (R$2k-5k) | 136 | 30.6% | R$ 425.811,44 | 23.7% | R$ 3.130,97 |
| BRONZE (<R$2k) | 221 | 49.8% | R$ 254.704,52 | 14.1% | R$ 1.152,51 |

**INSIGHT CRÍTICO:** 9.2% dos clientes (41 VIPs) geram 44.8% da receita!

### 2.4 Taxa de Recompra Mensal

| MÊS BASE | COMPRARAM | RECOMPRARAM M+1 | TAXA RECOMPRA |
|----------|-----------|-----------------|---------------|
| MAR/25 | 17 | 3 | 17.6% |
| ABR/25 | 43 | 10 | 23.3% |
| MAI/25 | 70 | 12 | 17.1% |
| JUN/25 | 95 | 15 | 15.8% |
| JUL/25 | 73 | 19 | 26.0% |
| AGO/25 | 104 | 29 | **27.9%** |
| SET/25 | 97 | 24 | 24.7% |
| OUT/25 | 116 | 26 | 22.4% |

**Média: 21.9% de recompra mês a mês**

### 2.5 Performance por Consultor

| CONSULTOR | VALOR TOTAL | VENDAS | CLIENTES | V/C | TICKET MÉDIO |
|-----------|-------------|--------|----------|-----|--------------|
| Manu Ditzel | R$ 585.936,91 | 290 | 158 | 1.84 | R$ 2.020,47 |
| Larissa Padilha | R$ 425.824,85 | 234 | 156 | 1.50 | R$ 1.819,76 |
| Helder Brunkow | R$ 350.007,33 | 140 | 95 | 1.47 | R$ 2.500,05 |
| Central - Daiane | R$ 248.579,64 | 88 | 81 | 1.09 | R$ 2.824,77 |
| Julio Gadret | R$ 183.249,01 | 105 | 80 | 1.31 | R$ 1.745,23 |

### 2.6 Performance por Rede

| REDE | VALOR | VENDAS | CLIENTES | V/C | TICKET MÉDIO |
|------|-------|--------|----------|-----|--------------|
| Demais clientes | R$ 1.462.205,28 | 648 | 325 | 1.99 | R$ 2.256,49 |
| [Rede] Fit Land | R$ 154.572,38 | 109 | 47 | 2.32 | R$ 1.418,10 |
| [Rede] Vida Leve | R$ 43.042,46 | 27 | 22 | 1.23 | R$ 1.594,17 |
| [Rede] Cia da Saúde | R$ 36.175,77 | 25 | 19 | 1.32 | R$ 1.447,03 |

### 2.7 Sazonalidade - Dia da Semana

| DIA | VENDAS | % | VALOR TOTAL | % VALOR |
|-----|--------|---|-------------|---------|
| Terça | 183 | 21.1% | R$ 387.675,97 | 10.8% |
| Quinta | 184 | 21.2% | R$ 344.240,80 | 9.6% |
| Quarta | 178 | 20.5% | R$ 323.131,06 | 9.0% |
| Segunda | 169 | 19.5% | R$ 447.497,04 | 12.4% |
| Sexta | 149 | 17.2% | R$ 286.625,58 | 8.0% |

**Padrão:** Terça/Quinta são os dias mais fortes (21% cada)

### 2.8 Churn Mensal - Ativos que Viraram Inativos

| MÊS | ATIVOS ANT | ATIVOS ATU | NOVOS | CHURN EST | ENTRARAM | LÍQUIDO |
|-----|------------|------------|-------|-----------|----------|---------|
| ABR/25 | 18 | 57 | 43 | 4 | 43 | +39 |
| MAI/25 | 57 | 103 | 58 | 12 | 59 | +47 |
| JUN/25 | 103 | 153 | 73 | 23 | 80 | +57 |
| JUL/25 | 153 | 153 | 39 | 39 | 49 | +10 |
| AGO/25 | 153 | 158 | 51 | **46** | 71 | +25 |
| SET/25 | 158 | 172 | 46 | 32 | 71 | +39 |
| OUT/25 | 172 | 189 | 50 | 33 | 82 | +49 |
| NOV/25 | 189 | 212 | 58 | 35 | 84 | +49 |
| **DEZ/25** | 212 | 213 | 13 | **12** | 26 | +14 |

**Média de churn: 30 clientes/mês (18% dos ativos)**

---

## 🎯 3. PROBLEMAS IDENTIFICADOS

### 3.1 Críticos (P0)

1. **RETENÇÃO BAIXÍSSIMA**
   - Apenas 20.3% dos ativos recompram
   - 169 ativos em risco imediato (NOV/25)
   - Sem sistema de alerta de inatividade

2. **CHURN ALTO**
   - 30 clientes/mês virando inativos
   - Taxa de 18% de perda mensal
   - Falta de processo de retenção

3. **TAXA DE POSITIVAÇÃO EM QUEDA**
   - 94.4% → 28.4% em 9 meses
   - Indica baixo engajamento
   - Carteira cresceu, mas ativação caiu

### 3.2 Importantes (P1)

4. **SEGMENTAÇÃO INEXISTENTE**
   - Todos tratados iguais
   - VIPs (44.8% receita) sem atenção especial
   - Sem cadências diferenciadas

5. **DADOS HISTÓRICOS PERDIDOS**
   - 354 clientes sem histórico (ExactSales)
   - 60-90 dias de interações perdidas
   - Impossibilita análise de padrões

6. **FALTA DE AUTOMAÇÃO**
   - Alertas manuais
   - Sem triggers automáticos
   - Dependência de Excel

### 3.3 Desejáveis (P2)

7. **ANÁLISE LIMITADA**
   - Sem dashboard em tempo real
   - Relatórios manuais
   - Falta previsibilidade

8. **INTEGRAÇÃO FRACA**
   - CRM isolado do ERP
   - Dados duplicados
   - Processos manuais

---

## 💡 4. REQUISITOS DO SISTEMA

### 4.1 Requisitos Funcionais (RF)

#### RF01 - Gestão de Clientes
- Cadastro completo de clientes
- Histórico de interações
- Status automático (Ativo, Inativo Rec, Inativo Ant)
- Tags e categorização
- Segmentação RFM automática

#### RF02 - Alertas e Notificações
- **CRÍTICO:** Alerta aos 45 dias sem compra
- Notificação de cliente em risco (60 dias)
- Alert de inativação (90 dias)
- Notificação de oportunidade de reativação

#### RF03 - Cadências de Atendimento
- Configuração por segmento:
  - CAMPEÕES: 2x/semana
  - CLIENTES FIÉIS: 1x/semana
  - ATIVOS: 1x/15 dias
  - INATIVOS REC: 1x/mês
  - INATIVOS ANT: 1x/trimestre
- Agenda automática
- Follow-ups programados

#### RF04 - Dashboard e Relatórios
- KPIs em tempo real:
  - Taxa de positivação
  - Taxa de retenção
  - Churn mensal
  - LTV por segmento
- Gráficos de tendência
- Alertas visuais
- Exportação de dados

#### RF05 - Integração com Vendas
- Sincronização automática com ERP
- Registro de pedidos
- Cálculo automático de status
- Histórico de valores

#### RF06 - Campanhase Automações
- Campanhas segmentadas
- Email/WhatsApp marketing
- Sequências automatizadas
- A/B testing

### 4.2 Requisitos Não-Funcionais (RNF)

#### RNF01 - Performance
- Tempo de resposta < 2s
- Processamento de 10.000 clientes
- Dashboard atualizado em tempo real

#### RNF02 - Segurança
- Backup automático diário
- Criptografia de dados
- Logs de auditoria
- Controle de acesso por perfil

#### RNF03 - Usabilidade
- Interface intuitiva
- Mobile-friendly
- Treinamento < 2 horas
- Compatibilidade com Excel (import/export)

#### RNF04 - Escalabilidade
- Suportar crescimento de 500%
- Adicionar novos consultores
- Múltiplas redes/filiais

---

## 🎯 5. CASOS DE USO PRIORITÁRIOS

### UC01 - Reativar 169 Ativos em Risco (NOV/25)
**Prioridade:** CRÍTICA  
**Objetivo:** Reduzir churn de 30→15 clientes/mês

**Fluxo:**
1. Sistema identifica 169 ativos que não compraram
2. Gera lista priorizada por LTV
3. Dispara alertas para consultores
4. Agenda contatos (telefone + WhatsApp)
5. Tracking de follow-ups
6. Métricas de conversão

**Meta:** 50% de reativação = 85 vendas extras

### UC02 - Segmentação VIP
**Prioridade:** ALTA  
**Objetivo:** Aumentar receita dos 41 VIPs

**Fluxo:**
1. Identificar clientes LTV R$10k+
2. Atribuir consultor senior
3. Cadência personalizada (2x/semana)
4. Ofertas exclusivas
5. Atendimento preferencial

**Meta:** +20% em vendas VIP = +R$ 160k/ano

### UC03 - Campanha de Novos (Onboarding)
**Prioridade:** ALTA  
**Objetivo:** Reduzir churn de novos clientes

**Fluxo:**
1. Cliente realiza primeira compra
2. Trigger de boas-vindas automático
3. Sequência de 3 contatos (D+3, D+7, D+15)
4. Incentivo para segunda compra
5. Monitoramento de recompra

**Meta:** Taxa de recompra 30→50%

### UC04 - Recuperação de Hibernando (105 clientes)
**Prioridade:** MÉDIA  
**Objetivo:** Reativar clientes dormentes

**Fluxo:**
1. Identificar 105 clientes hibernando
2. Segmentar por LTV histórico
3. Campanha de reconquista
4. Oferta especial de retorno
5. Tracking de reativação

**Meta:** 20% de reativação = 21 clientes = R$ 50k

---

## 📊 6. MÉTRICAS DE SUCESSO (KPIs)

### 6.1 KPIs Principais

| KPI | ATUAL | META 3M | META 6M | META 12M |
|-----|-------|---------|---------|----------|
| **Taxa de Retenção** | 20.3% | 30% | 40% | 50% |
| **Churn Mensal** | 30 clientes | 20 | 15 | 10 |
| **Taxa de Positivação** | 28.4% | 35% | 40% | 45% |
| **Taxa de Recompra** | 21.9% | 30% | 40% | 50% |
| **LTV Médio** | R$ 8.115 | R$ 9.000 | R$ 10.000 | R$ 12.000 |
| **Receita/Mês** | R$ 255k | R$ 300k | R$ 350k | R$ 400k |

### 6.2 KPIs Secundários

- Tempo médio de resposta a clientes
- Taxa de conversão por campanha
- NPS (Net Promoter Score)
- CAC (Custo de Aquisição de Cliente)
- Ticket médio por segmento
- Tempo médio entre compras

---

## 🗓️ 7. ROADMAP DE IMPLEMENTAÇÃO

### FASE 1 - URGENTE (0-30 dias)

**Objetivo:** Conter churn e salvar 169 ativos em risco

- [ ] Setup básico do CRM
- [ ] Migração de 444 clientes
- [ ] Lista dos 169 em risco + contato imediato
- [ ] Alertas manuais configurados
- [ ] Dashboard básico (Excel/PowerBI)

**Investimento:** Baixo  
**ROI Esperado:** 85 vendas = R$ 177k

### FASE 2 - ESTRUTURAÇÃO (30-90 dias)

**Objetivo:** Implementar sistema completo

- [ ] Segmentação RFM automatizada
- [ ] Cadências por segmento
- [ ] Automação de alertas (45d/60d/90d)
- [ ] Integração com ERP/Mercos
- [ ] Dashboard em tempo real
- [ ] Campanha VIP (41 clientes)

**Investimento:** Médio  
**ROI Esperado:** +R$ 160k VIPs + retenção

### FASE 3 - OTIMIZAÇÃO (90-180 dias)

**Objetivo:** Automação e escala

- [ ] Campanhas automatizadas
- [ ] Sequências de onboarding
- [ ] A/B testing
- [ ] Previsão de churn (ML)
- [ ] WhatsApp Business API
- [ ] Recuperação hibernando (105)

**Investimento:** Médio-Alto  
**ROI Esperado:** +R$ 50k recuperação

### FASE 4 - EXPANSÃO (180-365 dias)

**Objetivo:** Crescimento sustentável

- [ ] Multi-canal (email, SMS, push)
- [ ] Programa de fidelidade
- [ ] Referral program
- [ ] Análise preditiva avançada
- [ ] Expansão para novas regiões

**Investimento:** Alto  
**ROI Esperado:** Crescimento 2x

---

## 💰 8. ANÁLISE DE ROI

### 8.1 Investimento Estimado

| FASE | INVESTIMENTO | PRAZO |
|------|--------------|-------|
| Fase 1 | R$ 5.000 | 30d |
| Fase 2 | R$ 15.000 | 90d |
| Fase 3 | R$ 25.000 | 180d |
| Fase 4 | R$ 40.000 | 365d |
| **TOTAL** | **R$ 85.000** | **1 ano** |

### 8.2 Retorno Esperado

| INICIATIVA | IMPACTO | VALOR ANUAL |
|-----------|---------|-------------|
| Reativar 169 em risco | 50% = 85 clientes | R$ 177.000 |
| Aumentar vendas VIPs (+20%) | 41 clientes | R$ 160.000 |
| Reduzir churn (30→15/mês) | 15 clientes/mês | R$ 180.000 |
| Melhorar recompra (22%→40%) | +18pp | R$ 216.000 |
| Recuperar hibernando (20%) | 21 clientes | R$ 50.000 |
| **TOTAL ANUAL** | | **R$ 783.000** |

**ROI: 821% em 1 ano (R$ 783k retorno / R$ 85k investimento)**

---

## 🚀 9. PRÓXIMOS PASSOS IMEDIATOS

### Esta Semana (15-22/DEZ)

1. ✅ Aprovar PRD com stakeholders
2. ✅ Definir budget para Fase 1
3. ✅ Gerar lista dos 169 clientes em risco
4. ✅ Distribuir lista entre consultores
5. ✅ Iniciar contatos urgentes

### Próximas 2 Semanas (22/DEZ-05/JAN)

1. ✅ Escolher ferramenta CRM (sugestões: Pipedrive, HubSpot, Bitrix24)
2. ✅ Setup inicial
3. ✅ Importar base de 444 clientes
4. ✅ Configurar alertas básicos
5. ✅ Treinamento da equipe

### Primeiro Mês (JAN/2026)

1. ✅ Dashboard operacional
2. ✅ Cadências implementadas
3. ✅ Métricas de baseline capturadas
4. ✅ Primeira campanha VIP
5. ✅ Review de resultados

---

## 📎 10. ANEXOS

### 10.1 Arquivos de Dados

- `analise_rfm.csv` - Segmentação RFM completa
- `lifetime_value.csv` - LTV de todos os clientes
- `top_50_clientes.csv` - Top 50 por valor
- `performance_por_rede.csv` - Performance por rede
- `performance_por_consultor.csv` - Performance individual
- `carteira_completa_mensal.csv` - Evolução da carteira
- `cohort_analysis.csv` - Análise de coortes

### 10.2 Documentos Relacionados

- `ANALISE_DEFINITIVA_100_COMPLETA.md` - Análise técnica detalhada
- `AJUSTE_FUNIL_POR_STATUS.md` - Impacto operacional
- `ATUALIZACAO_DEZEMBRO_2025.md` - Dados mais recentes

### 10.3 Glossário

- **Positivação:** Cliente que realizou compra no período
- **Churn:** Taxa de clientes que deixam de ser ativos
- **LTV (Lifetime Value):** Valor total gerado pelo cliente
- **RFM:** Recency, Frequency, Monetary (método de segmentação)
- **Cadência:** Frequência programada de contatos
- **Retenção:** Percentual de clientes que recompram

---

**Documento preparado por:** Leandro (Eng. IA & Soluções)  
**Última atualização:** 15/12/2025  
**Próxima revisão:** 30/12/2025 (após dados completos de DEZ)
