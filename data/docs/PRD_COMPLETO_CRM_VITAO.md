# ðŸ“‹ PRODUCT REQUIREMENTS DOCUMENT (PRD)
## SISTEMA CRM VITÃƒO ALIMENTOS - ANÃLISE COMPLETA E REQUISITOS

**VersÃ£o:** 2.0  
**Data:** 15/12/2025  
**Autor:** Leandro  
**Status:** Em Desenvolvimento

---

## ðŸŽ¯ 1. SUMÃRIO EXECUTIVO

### 1.1 Contexto

A VitÃ£o Alimentos enfrenta desafios crÃ­ticos na gestÃ£o de relacionamento com clientes apÃ³s perda de dados do CRM anterior (ExactSales). Este documento consolida anÃ¡lise completa de 867 vendas de 444 clientes em 2025, identificando oportunidades de otimizaÃ§Ã£o e requisitos para novo sistema.

### 1.2 Descobertas CrÃ­ticas

**ALERTAS VERMELHOS:**
- ðŸ”´ **Taxa de RetenÃ§Ã£o: 20.3%** - Apenas 43 de 212 clientes ativos recompram mensalmente
- ðŸ”´ **169 clientes ativos em risco** - 79.7% dos ativos nÃ£o compraram em NOV/2025
- ðŸ”´ **Churn mensal: ~30 clientes** - Taxa de perda de 18% dos ativos/mÃªs
- ðŸ”´ **Taxa de positivaÃ§Ã£o caiu 70%** - De 94.4% (MAR) para 28.4% (NOV)

**OPORTUNIDADES:**
- âœ… Crescimento de carteira: 2.289% (18â†’430 clientes)
- âœ… Receita total 2025: R$ 3.603.246,14
- âœ… 41 clientes VIP (LTV R$10k+) = 44.8% da receita
- âœ… Taxa de reativaÃ§Ã£o crescente: 0%â†’27.7%

---

## ðŸ“Š 2. ANÃLISE DE DADOS

### 2.1 Carteira Completa - EvoluÃ§Ã£o Mensal

| MÃŠS | CARTEIRA | ATIVOS | INAT REC | INAT ANT | POSITIV | Î” CARTEIRA | % POSIT |
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

*DEZ/25 parcial (atÃ© 15/12)

### 2.2 SegmentaÃ§Ã£o RFM - Clientes por Valor

| SEGMENTO | QTD | % | VALOR TOTAL | VALOR MÃ‰DIO | RECENCY | FREQ |
|----------|-----|---|-------------|-------------|---------|------|
| CAMPEÃ•ES | 30 | 6.8% | R$ 351.919,65 | R$ 11.730,65 | 16d | 5 |
| CLIENTES FIÃ‰IS | 52 | 11.7% | R$ 414.862,07 | R$ 7.978,12 | 34d | 3 |
| POTENCIAL FIDELIZAÃ‡ÃƒO | 44 | 9.9% | R$ 126.204,42 | R$ 2.868,28 | 21d | 1 |
| NOVOS PROMISSORES | 102 | 23.0% | R$ 212.777,89 | R$ 2.086,06 | 46d | 1 |
| PRECISA ATENÃ‡ÃƒO | 65 | 14.6% | R$ 137.598,22 | R$ 2.116,90 | 132d | 1 |
| CLIENTES EM RISCO | 34 | 7.7% | R$ 246.758,47 | R$ 7.257,60 | 127d | 2 |
| PRESTES A PERDER | 12 | 2.7% | R$ 68.197,67 | R$ 5.683,14 | 213d | 2 |
| HIBERNANDO | 105 | 23.6% | R$ 242.105,64 | R$ 2.305,77 | 189d | 1 |

### 2.3 Lifetime Value (LTV) - ConcentraÃ§Ã£o de Receita

| CATEGORIA | CLIENTES | % CLIENTES | VALOR TOTAL | % RECEITA | LTV MÃ‰DIO |
|-----------|----------|------------|-------------|-----------|-----------|
| VIP (R$10k+) | 41 | 9.2% | R$ 807.098,52 | **44.8%** | R$ 19.685,33 |
| GOLD (R$5k-10k) | 46 | 10.4% | R$ 312.809,55 | 17.4% | R$ 6.800,21 |
| SILVER (R$2k-5k) | 136 | 30.6% | R$ 425.811,44 | 23.7% | R$ 3.130,97 |
| BRONZE (<R$2k) | 221 | 49.8% | R$ 254.704,52 | 14.1% | R$ 1.152,51 |

**INSIGHT CRÃTICO:** 9.2% dos clientes (41 VIPs) geram 44.8% da receita!

### 2.4 Taxa de Recompra Mensal

| MÃŠS BASE | COMPRARAM | RECOMPRARAM M+1 | TAXA RECOMPRA |
|----------|-----------|-----------------|---------------|
| MAR/25 | 17 | 3 | 17.6% |
| ABR/25 | 43 | 10 | 23.3% |
| MAI/25 | 70 | 12 | 17.1% |
| JUN/25 | 95 | 15 | 15.8% |
| JUL/25 | 73 | 19 | 26.0% |
| AGO/25 | 104 | 29 | **27.9%** |
| SET/25 | 97 | 24 | 24.7% |
| OUT/25 | 116 | 26 | 22.4% |

**MÃ©dia: 21.9% de recompra mÃªs a mÃªs**

### 2.5 Performance por Consultor

| CONSULTOR | VALOR TOTAL | VENDAS | CLIENTES | V/C | TICKET MÃ‰DIO |
|-----------|-------------|--------|----------|-----|--------------|
| Manu Ditzel | R$ 585.936,91 | 290 | 158 | 1.84 | R$ 2.020,47 |
| Larissa Padilha | R$ 425.824,85 | 234 | 156 | 1.50 | R$ 1.819,76 |
| Helder Brunkow | R$ 350.007,33 | 140 | 95 | 1.47 | R$ 2.500,05 |
| Central - Daiane | R$ 248.579,64 | 88 | 81 | 1.09 | R$ 2.824,77 |
| Julio Gadret | R$ 183.249,01 | 105 | 80 | 1.31 | R$ 1.745,23 |

### 2.6 Performance por Rede

| REDE | VALOR | VENDAS | CLIENTES | V/C | TICKET MÃ‰DIO |
|------|-------|--------|----------|-----|--------------|
| Demais clientes | R$ 1.462.205,28 | 648 | 325 | 1.99 | R$ 2.256,49 |
| [Rede] Fit Land | R$ 154.572,38 | 109 | 47 | 2.32 | R$ 1.418,10 |
| [Rede] Vida Leve | R$ 43.042,46 | 27 | 22 | 1.23 | R$ 1.594,17 |
| [Rede] Cia da SaÃºde | R$ 36.175,77 | 25 | 19 | 1.32 | R$ 1.447,03 |

### 2.7 Sazonalidade - Dia da Semana

| DIA | VENDAS | % | VALOR TOTAL | % VALOR |
|-----|--------|---|-------------|---------|
| TerÃ§a | 183 | 21.1% | R$ 387.675,97 | 10.8% |
| Quinta | 184 | 21.2% | R$ 344.240,80 | 9.6% |
| Quarta | 178 | 20.5% | R$ 323.131,06 | 9.0% |
| Segunda | 169 | 19.5% | R$ 447.497,04 | 12.4% |
| Sexta | 149 | 17.2% | R$ 286.625,58 | 8.0% |

**PadrÃ£o:** TerÃ§a/Quinta sÃ£o os dias mais fortes (21% cada)

### 2.8 Churn Mensal - Ativos que Viraram Inativos

| MÃŠS | ATIVOS ANT | ATIVOS ATU | NOVOS | CHURN EST | ENTRARAM | LÃQUIDO |
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

**MÃ©dia de churn: 30 clientes/mÃªs (18% dos ativos)**

---

## ðŸŽ¯ 3. PROBLEMAS IDENTIFICADOS

### 3.1 CrÃ­ticos (P0)

1. **RETENÃ‡ÃƒO BAIXÃSSIMA**
   - Apenas 20.3% dos ativos recompram
   - 169 ativos em risco imediato (NOV/25)
   - Sem sistema de alerta de inatividade

2. **CHURN ALTO**
   - 30 clientes/mÃªs virando inativos
   - Taxa de 18% de perda mensal
   - Falta de processo de retenÃ§Ã£o

3. **TAXA DE POSITIVAÃ‡ÃƒO EM QUEDA**
   - 94.4% â†’ 28.4% em 9 meses
   - Indica baixo engajamento
   - Carteira cresceu, mas ativaÃ§Ã£o caiu

### 3.2 Importantes (P1)

4. **SEGMENTAÃ‡ÃƒO INEXISTENTE**
   - Todos tratados iguais
   - VIPs (44.8% receita) sem atenÃ§Ã£o especial
   - Sem cadÃªncias diferenciadas

5. **DADOS HISTÃ“RICOS PERDIDOS**
   - 354 clientes sem histÃ³rico (ExactSales)
   - 60-90 dias de interaÃ§Ãµes perdidas
   - Impossibilita anÃ¡lise de padrÃµes

6. **FALTA DE AUTOMAÃ‡ÃƒO**
   - Alertas manuais
   - Sem triggers automÃ¡ticos
   - DependÃªncia de Excel

### 3.3 DesejÃ¡veis (P2)

7. **ANÃLISE LIMITADA**
   - Sem dashboard em tempo real
   - RelatÃ³rios manuais
   - Falta previsibilidade

8. **INTEGRAÃ‡ÃƒO FRACA**
   - CRM isolado do ERP
   - Dados duplicados
   - Processos manuais

---

## ðŸ’¡ 4. REQUISITOS DO SISTEMA

### 4.1 Requisitos Funcionais (RF)

#### RF01 - GestÃ£o de Clientes
- Cadastro completo de clientes
- HistÃ³rico de interaÃ§Ãµes
- Status automÃ¡tico (Ativo, Inativo Rec, Inativo Ant)
- Tags e categorizaÃ§Ã£o
- SegmentaÃ§Ã£o RFM automÃ¡tica

#### RF02 - Alertas e NotificaÃ§Ãµes
- **CRÃTICO:** Alerta aos 45 dias sem compra
- NotificaÃ§Ã£o de cliente em risco (60 dias)
- Alert de inativaÃ§Ã£o (90 dias)
- NotificaÃ§Ã£o de oportunidade de reativaÃ§Ã£o

#### RF03 - CadÃªncias de Atendimento
- ConfiguraÃ§Ã£o por segmento:
  - CAMPEÃ•ES: 2x/semana
  - CLIENTES FIÃ‰IS: 1x/semana
  - ATIVOS: 1x/15 dias
  - INATIVOS REC: 1x/mÃªs
  - INATIVOS ANT: 1x/trimestre
- Agenda automÃ¡tica
- Follow-ups programados

#### RF04 - Dashboard e RelatÃ³rios
- KPIs em tempo real:
  - Taxa de positivaÃ§Ã£o
  - Taxa de retenÃ§Ã£o
  - Churn mensal
  - LTV por segmento
- GrÃ¡ficos de tendÃªncia
- Alertas visuais
- ExportaÃ§Ã£o de dados

#### RF05 - IntegraÃ§Ã£o com Vendas
- SincronizaÃ§Ã£o automÃ¡tica com ERP
- Registro de pedidos
- CÃ¡lculo automÃ¡tico de status
- HistÃ³rico de valores

#### RF06 - Campanhase AutomaÃ§Ãµes
- Campanhas segmentadas
- Email/WhatsApp marketing
- SequÃªncias automatizadas
- A/B testing

### 4.2 Requisitos NÃ£o-Funcionais (RNF)

#### RNF01 - Performance
- Tempo de resposta < 2s
- Processamento de 10.000 clientes
- Dashboard atualizado em tempo real

#### RNF02 - SeguranÃ§a
- Backup automÃ¡tico diÃ¡rio
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
- MÃºltiplas redes/filiais

---

## ðŸŽ¯ 5. CASOS DE USO PRIORITÃRIOS

### UC01 - Reativar 169 Ativos em Risco (NOV/25)
**Prioridade:** CRÃTICA  
**Objetivo:** Reduzir churn de 30â†’15 clientes/mÃªs

**Fluxo:**
1. Sistema identifica 169 ativos que nÃ£o compraram
2. Gera lista priorizada por LTV
3. Dispara alertas para consultores
4. Agenda contatos (telefone + WhatsApp)
5. Tracking de follow-ups
6. MÃ©tricas de conversÃ£o

**Meta:** 50% de reativaÃ§Ã£o = 85 vendas extras

### UC02 - SegmentaÃ§Ã£o VIP
**Prioridade:** ALTA  
**Objetivo:** Aumentar receita dos 41 VIPs

**Fluxo:**
1. Identificar clientes LTV R$10k+
2. Atribuir consultor senior
3. CadÃªncia personalizada (2x/semana)
4. Ofertas exclusivas
5. Atendimento preferencial

**Meta:** +20% em vendas VIP = +R$ 160k/ano

### UC03 - Campanha de Novos (Onboarding)
**Prioridade:** ALTA  
**Objetivo:** Reduzir churn de novos clientes

**Fluxo:**
1. Cliente realiza primeira compra
2. Trigger de boas-vindas automÃ¡tico
3. SequÃªncia de 3 contatos (D+3, D+7, D+15)
4. Incentivo para segunda compra
5. Monitoramento de recompra

**Meta:** Taxa de recompra 30â†’50%

### UC04 - RecuperaÃ§Ã£o de Hibernando (105 clientes)
**Prioridade:** MÃ‰DIA  
**Objetivo:** Reativar clientes dormentes

**Fluxo:**
1. Identificar 105 clientes hibernando
2. Segmentar por LTV histÃ³rico
3. Campanha de reconquista
4. Oferta especial de retorno
5. Tracking de reativaÃ§Ã£o

**Meta:** 20% de reativaÃ§Ã£o = 21 clientes = R$ 50k

---

## ðŸ“Š 6. MÃ‰TRICAS DE SUCESSO (KPIs)

### 6.1 KPIs Principais

| KPI | ATUAL | META 3M | META 6M | META 12M |
|-----|-------|---------|---------|----------|
| **Taxa de RetenÃ§Ã£o** | 20.3% | 30% | 40% | 50% |
| **Churn Mensal** | 30 clientes | 20 | 15 | 10 |
| **Taxa de PositivaÃ§Ã£o** | 28.4% | 35% | 40% | 45% |
| **Taxa de Recompra** | 21.9% | 30% | 40% | 50% |
| **LTV MÃ©dio** | R$ 8.115 | R$ 9.000 | R$ 10.000 | R$ 12.000 |
| **Receita/MÃªs** | R$ 255k | R$ 300k | R$ 350k | R$ 400k |

### 6.2 KPIs SecundÃ¡rios

- Tempo mÃ©dio de resposta a clientes
- Taxa de conversÃ£o por campanha
- NPS (Net Promoter Score)
- CAC (Custo de AquisiÃ§Ã£o de Cliente)
- Ticket mÃ©dio por segmento
- Tempo mÃ©dio entre compras

---

## ðŸ—“ï¸ 7. ROADMAP DE IMPLEMENTAÃ‡ÃƒO

### FASE 1 - URGENTE (0-30 dias)

**Objetivo:** Conter churn e salvar 169 ativos em risco

- [ ] Setup bÃ¡sico do CRM
- [ ] MigraÃ§Ã£o de 444 clientes
- [ ] Lista dos 169 em risco + contato imediato
- [ ] Alertas manuais configurados
- [ ] Dashboard bÃ¡sico (Excel/PowerBI)

**Investimento:** Baixo  
**ROI Esperado:** 85 vendas = R$ 177k

### FASE 2 - ESTRUTURAÃ‡ÃƒO (30-90 dias)

**Objetivo:** Implementar sistema completo

- [ ] SegmentaÃ§Ã£o RFM automatizada
- [ ] CadÃªncias por segmento
- [ ] AutomaÃ§Ã£o de alertas (45d/60d/90d)
- [ ] IntegraÃ§Ã£o com ERP/Mercos
- [ ] Dashboard em tempo real
- [ ] Campanha VIP (41 clientes)

**Investimento:** MÃ©dio  
**ROI Esperado:** +R$ 160k VIPs + retenÃ§Ã£o

### FASE 3 - OTIMIZAÃ‡ÃƒO (90-180 dias)

**Objetivo:** AutomaÃ§Ã£o e escala

- [ ] Campanhas automatizadas
- [ ] SequÃªncias de onboarding
- [ ] A/B testing
- [ ] PrevisÃ£o de churn (ML)
- [ ] WhatsApp Business API
- [ ] RecuperaÃ§Ã£o hibernando (105)

**Investimento:** MÃ©dio-Alto  
**ROI Esperado:** +R$ 50k recuperaÃ§Ã£o

### FASE 4 - EXPANSÃƒO (180-365 dias)

**Objetivo:** Crescimento sustentÃ¡vel

- [ ] Multi-canal (email, SMS, push)
- [ ] Programa de fidelidade
- [ ] Referral program
- [ ] AnÃ¡lise preditiva avanÃ§ada
- [ ] ExpansÃ£o para novas regiÃµes

**Investimento:** Alto  
**ROI Esperado:** Crescimento 2x

---

## ðŸ’° 8. ANÃLISE DE ROI

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
| Reduzir churn (30â†’15/mÃªs) | 15 clientes/mÃªs | R$ 180.000 |
| Melhorar recompra (22%â†’40%) | +18pp | R$ 216.000 |
| Recuperar hibernando (20%) | 21 clientes | R$ 50.000 |
| **TOTAL ANUAL** | | **R$ 783.000** |

**ROI: 821% em 1 ano (R$ 783k retorno / R$ 85k investimento)**

---

## ðŸš€ 9. PRÃ“XIMOS PASSOS IMEDIATOS

### Esta Semana (15-22/DEZ)

1. âœ… Aprovar PRD com stakeholders
2. âœ… Definir budget para Fase 1
3. âœ… Gerar lista dos 169 clientes em risco
4. âœ… Distribuir lista entre consultores
5. âœ… Iniciar contatos urgentes

### PrÃ³ximas 2 Semanas (22/DEZ-05/JAN)

1. âœ… Escolher ferramenta CRM (sugestÃµes: Pipedrive, HubSpot, Bitrix24)
2. âœ… Setup inicial
3. âœ… Importar base de 444 clientes
4. âœ… Configurar alertas bÃ¡sicos
5. âœ… Treinamento da equipe

### Primeiro MÃªs (JAN/2026)

1. âœ… Dashboard operacional
2. âœ… CadÃªncias implementadas
3. âœ… MÃ©tricas de baseline capturadas
4. âœ… Primeira campanha VIP
5. âœ… Review de resultados

---

## ðŸ“Ž 10. ANEXOS

### 10.1 Arquivos de Dados

- `analise_rfm.csv` - SegmentaÃ§Ã£o RFM completa
- `lifetime_value.csv` - LTV de todos os clientes
- `top_50_clientes.csv` - Top 50 por valor
- `performance_por_rede.csv` - Performance por rede
- `performance_por_consultor.csv` - Performance individual
- `carteira_completa_mensal.csv` - EvoluÃ§Ã£o da carteira
- `cohort_analysis.csv` - AnÃ¡lise de coortes

### 10.2 Documentos Relacionados

- `ANALISE_DEFINITIVA_100_COMPLETA.md` - AnÃ¡lise tÃ©cnica detalhada
- `AJUSTE_FUNIL_POR_STATUS.md` - Impacto operacional
- `ATUALIZACAO_DEZEMBRO_2025.md` - Dados mais recentes

### 10.3 GlossÃ¡rio

- **PositivaÃ§Ã£o:** Cliente que realizou compra no perÃ­odo
- **Churn:** Taxa de clientes que deixam de ser ativos
- **LTV (Lifetime Value):** Valor total gerado pelo cliente
- **RFM:** Recency, Frequency, Monetary (mÃ©todo de segmentaÃ§Ã£o)
- **CadÃªncia:** FrequÃªncia programada de contatos
- **RetenÃ§Ã£o:** Percentual de clientes que recompram

---

**Documento preparado por:** Leandro (Eng. IA & SoluÃ§Ãµes)  
**Ãšltima atualizaÃ§Ã£o:** 15/12/2025  
**PrÃ³xima revisÃ£o:** 30/12/2025 (apÃ³s dados completos de DEZ)
