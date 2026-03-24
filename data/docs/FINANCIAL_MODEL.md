# MODELO FINANCEIRO CRM VITAO360

> Fonte: VITAO360_ULTRA_FINAL (5).xlsx | Abas 1-7 + PAINEL CEO
> Baseline corrigido: R$ 2.091.000 (auditoria forense 68 arquivos, 2026-03-23)
> Valor anterior R$ 2.156.179 SUPERSEDED

---

## 1. DIAGNOSTICO 2025 -- DADOS REAIS

Faturamento anual auditado: **R$ 2.091.000**

### 1.1 Mes a Mes

| Mes | Faturamento | Cli. Ativos | Novos | Retidos | Churned | Retencao | Acumulado |
|-----|-------------|-------------|-------|---------|---------|----------|-----------|
| Jan | R$ 43.265 | 32 | 32 | 0 | 0 | 0% | R$ 43.265 |
| Fev | R$ 38.004 | 26 | 23 | 3 | -29 | 9,4% | R$ 81.269 |
| Mar | R$ 112.452 | 53 | 49 | 4 | -22 | 15,4% | R$ 193.721 |
| Abr | R$ 170.967 | 63 | 51 | 12 | -41 | 22,6% | R$ 364.688 |
| Mai | R$ 180.112 | 77 | 65 | 12 | -51 | 19,0% | R$ 544.800 |
| Jun | R$ 221.940 | 101 | 87 | 14 | -63 | 18,2% | R$ 766.740 |
| Jul | R$ 160.606 | 77 | 57 | 20 | -81 | 25,9% | R$ 927.346 |
| Ago | R$ 219.364 | 117 | 92 | 25 | -52 | 21,3% | R$ 1.146.710 |
| Set | R$ 201.625 | 93 | 66 | 27 | -90 | 23,1% | R$ 1.348.335 |
| Out | R$ 275.016 | 113 | 88 | 25 | -68 | 15,0% | R$ 1.623.351 |
| Nov | R$ 277.673 | 91 | 74 | 17 | -96 | 13,0% | R$ 1.901.024 |
| Dez | R$ 189.970 | 88 | 76 | 12 | -79 | 11,6% | R$ 2.090.994 |
| **TOTAL** | **R$ 2.091.000** | -- | **760** | **171** | **-672** | **Avg 20%** | **R$ 2.091.000** |

### 1.2 KPIs Reais

| KPI | Valor | Fonte |
|-----|-------|-------|
| Receita anual | R$ 2.091.000 | PAINEL_CEO_DEFINITIVO auditado |
| Melhor mes (Nov/25) | R$ 277.673 | Pico nao sustentado sem estrutura |
| Clientes com compra | 488 | CRM: 661 total (incl. prospects) |
| Ticket medio anual | R$ 4.285 | R$ 2.091K / 488 clientes |
| Ativos medio/mes | 78 | Media Jan(32) a Ago(117) |
| Churn mensal | 80% | Observado real CRM + SAP |
| Retencao mensal | 20% | Inverso do churn |
| LTV estimado | R$ 2.792 | 1,9 meses x ticket medio mensal |
| Compraram 1x so | 57,2% | 279 de 488 clientes |
| Devolucoes | 2,3% | Aceitavel para segmento B2B |

### 1.3 Frequencia de Compra

| Meses Ativo | Clientes | % Total | Interpretacao |
|-------------|----------|---------|---------------|
| 0m | 4 | 0,8% | Zero pedidos -- teste ou prospect puro |
| 1m | 279 | 57,2% | CRITICO: 57% comprou 1x so. Churn estrutural. |
| 2m | 101 | 20,7% | 2 compras -- ciclo ainda curto |
| 3m | 47 | 9,6% | 3 compras -- em fidelizacao |
| 4m | 22 | 4,5% | 4+ meses -- RECORRENTE (meta) |
| 5m | 25 | 5,1% | Recorrente consolidado |
| 6m | 5 | 1,0% | Alta fidelizacao |

---

## 2. PREMISSAS DO MODELO

### 2.1 Base Existente 2025

| Parametro | Valor | Unidade | Fonte/Nota | Tipo |
|-----------|-------|---------|------------|------|
| Faturamento base 2025 | 2.091.000 | R$ | PAINEL_CEO_DEFINITIVO auditado | REAL |
| Media mensal 2025 | 174.250 | R$/mes | Calculado (2.091K / 12) | CALCULADO |
| Base organica P1 | 120.000 | R$/mes | Conservador -31% vs media (sazonalidade Jan) | PREMISSA |
| Ticket VERDE/JBP | 3.611 | R$/cli | SINALEIRO -- 422 client-months / 12 meses | REAL |
| Ticket AMARELO | 1.464 | R$/cli | SINALEIRO -- 127 client-months | REAL |
| Ticket VERMELHO | 1.012 | R$/cli | SINALEIRO -- 375 client-months | REAL |
| Ticket ROXO | 0 | R$/cli | Prospect -- nunca compraram | REAL |
| Ticket Redes/Franquias | 2.500 | R$/cli | FITLAND + CIA + VIDA LEVE + DIVINA | REAL |

### 2.2 Producao Equipe Nova (Validadas por Q1 2026)

| Parametro | Valor | Unidade | Justificativa | Validacao Q1 |
|-----------|-------|---------|---------------|--------------|
| Novos PDVs/vendedora/mes | 22 | cli | 1 fechamento/dia x 22 dias uteis | Real Q1: 59/mes SEM vendedora (+168%) |
| Novos Redes/gerente/mes | 5 | cli | F1:5 / F2:8 / F3-F4:10 | Premissa conservadora |
| Ticket 1a compra PDV | 1.500 | R$ | Media CRM embalados -- sem granel 2026 | Real Q1: R$1.569 (+4,6%) |
| Ticket recompra PDV | 1.800 | R$ | Mix expandido pos-fidelizacao | -- |
| Ticket rede/franquia | 2.500 | R$ | Media redes CRM | -- |
| Churn novos PDV | 75% | -- | CRM real 80% -- modelo conservador | Real Q1: 83% -- confirmado |
| Churn novos Rede | 30% | -- | Redes tem contrato/compromisso | -- |
| Ciclo recompra PDV | 60 | dias | Prazo medio entre pedidos | -- |
| Ciclo recompra Rede | 90 | dias | Prazo medio entre pedidos | -- |
| Conversao contato-venda | 4,5% | -- | 30% x 50% x 30% -- funil auditado | Real Q1 confirmado |

### 2.3 Fases Ramp-Up

| Fase | Periodos | Equipe | Custo/Mes | Gatilho |
|------|----------|--------|-----------|---------|
| F1 | P1-P3 (Q1) | 2 Reps (Larissa+Julio) + Daiane | R$ 22.000 | Operacao atual -- Q1 real confirmado |
| F2 | P4-P6 (Q2) | 3 Reps + Daiane (Nova Rep ramp 2m) | R$ 29.000 | Substituicao Manu + Fat > R$80k/mes |
| F3 | P7-P9 (Q3) | 3 Reps + Daiane + Pos-Venda | R$ 34.000 | Fat > R$180k/mes + churn 75%-50% |
| F4 | P10-P12 (Q4) | 4 Reps + Daiane + Pos-Venda | R$ 40.000 | Fat > R$300k/mes + aceleracao |

---

## 3. MOTOR RAMP-UP 2026 -- 12 MESES

### 3.1 Equipe Mensal

| Metrica | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | ANO |
|---------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| Vendedoras | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 4 | 4 | -- |
| Gerente (redes) | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | -- |
| Pos-Venda/CS | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | -- |
| Custo Equipe R$ | 22K | 22K | 22K | 29K | 29K | 29K | 34K | 34K | 34K | 40K | 40K | 40K | 375K |
| Fase | F1 | F1 | F1 | F2 | F2 | F2 | F3 | F3 | F3 | F4 | F4 | F4 | -- |

### 3.2 Clientes Mensal

| Metrica | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | ANO |
|---------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| Novos PDVs | 44 | 44 | 44 | 55 | 66 | 66 | 66 | 66 | 66 | 88 | 88 | 88 | 781 |
| Novos Redes | 5 | 5 | 5 | 8 | 8 | 8 | 10 | 10 | 10 | 10 | 10 | 10 | 99 |
| Recompras PDVs | 0 | 0 | 4 | 4 | 4 | 5 | 12 | 12 | 13 | 13 | 13 | 17 | 97 |
| Recompras Redes | 0 | 0 | 0 | 3 | 3 | 3 | 5 | 5 | 5 | 7 | 7 | 7 | 45 |
| Churn (saidas) | 29 | 29 | 29 | 37 | 44 | 44 | 30 | 30 | 30 | 39 | 39 | 39 | 419 |
| Ativos/Mes | 101 | 121 | 145 | 178 | 215 | 253 | 316 | 379 | 443 | 522 | 601 | 684 | 684 |

### 3.3 Faturamento Mensal

| Metrica | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | ANO |
|---------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| Base Organica | 120.000 | 120.047 | 120.095 | 120.286 | 120.478 | 120.670 | 120.862 | 121.054 | 121.247 | 121.585 | 121.925 | 122.265 | 1.450.514 |
| Novos PDVs | 66.000 | 66.000 | 66.000 | 82.500 | 99.000 | 99.000 | 99.000 | 99.000 | 99.000 | 132.000 | 132.000 | 132.000 | 1.171.500 |
| Recompras PDVs | 0 | 0 | 7.200 | 7.200 | 7.200 | 9.000 | 21.600 | 21.600 | 23.400 | 23.400 | 23.400 | 30.600 | 174.600 |
| Redes+Rec.Redes | 12.500 | 12.500 | 12.500 | 27.500 | 27.500 | 27.500 | 37.500 | 37.500 | 37.500 | 42.500 | 42.500 | 42.500 | 360.000 |
| **FAT. TOTAL** | **198.500** | **198.547** | **205.795** | **237.486** | **254.178** | **256.170** | **278.962** | **279.154** | **281.147** | **319.485** | **319.825** | **327.365** | **3.156.614** |
| Fat. 2025 ref. | 43.265 | 38.004 | 113.363 | 17.994 | 233.485 | 223.750 | 161.139 | 220.074 | 202.758 | 275.460 | 277.674 | 189.970 | 1.996.936 |

### 3.4 Resultado Mensal

| Metrica | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | ANO |
|---------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| Faturamento | 198.500 | 198.547 | 205.795 | 237.486 | 254.178 | 256.170 | 278.962 | 279.154 | 281.147 | 319.485 | 319.825 | 327.365 | 3.156.614 |
| Custo Equipe | -22.000 | -22.000 | -22.000 | -29.000 | -29.000 | -29.000 | -34.000 | -34.000 | -34.000 | -40.000 | -40.000 | -40.000 | -375.000 |
| Sobra (Fat-Custo) | 176.500 | 176.547 | 183.795 | 208.486 | 225.178 | 227.170 | 244.962 | 245.154 | 247.147 | 279.485 | 279.825 | 287.365 | 2.781.614 |
| Acumulado | 176.500 | 353.047 | 536.842 | 745.328 | 970.506 | 1.197.676 | 1.442.638 | 1.687.792 | 1.934.939 | 2.214.424 | 2.494.249 | 2.781.614 | 2.781.614 |

### 3.5 Unit Economics

| Metrica | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | P12 | ANO |
|---------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| CAC R$ (custo/novos) | 449 | 449 | 449 | 460 | 392 | 392 | 447 | 447 | 447 | 408 | 408 | 408 | 426 |
| Ticket Medio R$ | 1.965 | 1.641 | 1.419 | 1.334 | 1.182 | 1.013 | 883 | 737 | 635 | 612 | 532 | 479 | 4.615 |

---

## 4. EQUIPE 2026

### 4.1 Organograma

| Pessoa | Cargo | Territorio | Status | Meta | Atividade/Dia | Obs |
|--------|-------|-----------|--------|------|---------------|-----|
| LARISSA | Representante PDV | Brasil Interior | ATIVA | 22 novos/mes | 22 cont - 1 fecham./dia | Veterana -- carteira consolidada |
| JULIO | Representante PDV | Cia Saude+Fitland | ATIVO | 22 novos/mes | 22 cont - 1 fecham./dia | Veterano -- foco redes regionais |
| DAIANE | Gerente Redes+Food | Redes Nacionais + Food | NOVA ATRIB. | 8 redes/mes | 2-3 decisores/dia | Novo canal food = upside nao modelado |
| NOVA REP | Representante PDV | A definir | CONTRATAR Q2 | 22 novos/mes | Ramp 2m: 11-22/dia | Substitui Manu -- carteira SC+PR+RS |
| POS-VENDA | CS + Suporte | Todos 661 clientes | CONTRATAR Q3 | Churn 75%-50% | 12 follow-ups D+4/dia | Fecha o ralo -- LTV R$2.850-R$7.200 |

**ALERTA CRITICO:** HEMANUELE (MANU) entra em licenca maternidade Q2/2026. Carteira de 165 clientes / R$778K fat. 2025 / SC+PR+RS. ACAO: contratar Nova Rep Q2 + transferir carteira em 4-6 semanas.

### 4.2 Roadmap Contratacoes Q1-Q4

| Trimestre | Acao | Equipe | Custo/Mes | Gatilho | Porque | Fat. Estimado |
|-----------|------|--------|-----------|---------|--------|---------------|
| Q1 Jan-Mar | Operacao atual | Larissa+Julio+Daiane | R$ 22.000 | Q1 real=R$459K | Base validada pelo SAP real | R$ 603K |
| Q2 Abr-Jun | Substituir Manu | 3 Reps+Daiane | R$ 29.000 | Manu em licenca | Carteira nao pode ficar descoberta | R$ 748K |
| Q3 Jul-Set | PRIORIDADE: Pos-Venda | 3 Reps+Daiane+PV | R$ 34.000 | Fat>R$180K | Sem PV=balde furado. Cohort +55% | R$ 839K |
| Q4 Out-Dez | 4a Rep (aceleracao) | 4 Reps+Daiane+PV | R$ 40.000 | Fat>R$300K | Com PV rodando, cada novo fica 2x mais | R$ 967K |

### 4.3 Funil Diario por Funcao

| Etapa | Meta Mensal | Por Dia | Taxa | Quem | Ferramenta | Obs |
|-------|-------------|---------|------|------|------------|-----|
| Contatos (WA+Tel+Email) | 489/rep/mes | 22/dia | 100% base | Cada Representante | WhatsApp Business + CRM | 1 contato = 1 tentativa de agendar |
| Visitas (agendadas) | 147/rep/mes | 7/dia | 30% dos contatos | Cada Representante | Agenda integrada CRM | Presencial ou videochamada |
| Propostas enviadas | 73/rep/mes | 3/dia | 50% das visitas | Cada Representante | Mercos + CRM | Proposta formal ou amostras |
| Fechamentos (novos cli.) | 22/rep/mes | 1/dia | 30% propostas | Cada Representante | Mercos pedido | contato - visita - proposta - pedido |
| Follow-up D+4 (PV) | 100% pedidos | 12-15/dia | -- | Pos-Venda/CS (Q3) | CRM alertas automaticos | D+4 = confirmar entrega + satisfacao |
| Recompra (PDV) | ciclo 60 dias | alertas D+45 | -- | PV + Rep | CRM motor de regras | Antes do ciclo fechar - reagendar |
| Decisores redes (Daiane) | 8 redes/mes | 2-3/dia | 20% conv. | Daiane (Gerente) | Visita presencial + WhatsApp | Franqueador = multiplas lojas |

### 4.4 KPIs por Funcao

| Funcao | KPI | Meta | Unidade | Periodo | Acao se Nao Atingir | Referencia |
|--------|-----|------|---------|---------|---------------------|------------|
| Representante PDV | Aquisicao | 22 | novos/mes | Mensal | Revisar funil -- ver contatos/dia | Conv. 4,5% auditada |
| Representante PDV | Positivacao | 22 | PDVs/mes | Mensal | Verificar proposta e perfil do cliente | 1 fechamento/dia |
| Representante PDV | Ticket 1a compra | >=R$1.500 | R$/pedido | Por pedido | Mix de produto -- evitar so granel | Real Q1: R$1.569 |
| Representante PDV | Recompra T+60 | D+45 alertar | % | Ciclo | CRM alerta automatico D+45 | Ciclo 1,9m observado |
| Gerente Redes | Redes ativas | 8 | redes/mes | Mensal | Contatar franqueador + visita | Q1: 5 / Q2+: 8 |
| Gerente Redes | Food Channel | pipeline | -- | Trimestral | Reuniao Daiane -- modelar separado | Upside nao capturado |
| Pos-Venda/CS | Follow-up D+4 | 100% | % pedidos | D+4 do pedido | Zero tolerancia -- alerta critico | Protocolo D+4 obrigatorio |
| Pos-Venda/CS | Churn | <=50% | % mensal | Q3 (90 dias) | Revisar protocolo PV | Meta: 75%-50% em 90d |
| Pos-Venda/CS | Fidelizacao VERDE | 20 clientes | JBP ativos | Trimestral | CS individual -- visita mensal | Ticket R$3.000 |

---

## 5. Q1 2026 -- VALIDACAO REAL

Faturamento real SAP: **R$ 459.465**

Nota: Marco parcial (13 de 22 dias uteis). Projecao linear nao recomendada -- FACILITIES distorce.

### 5.1 Faturamento Real Q1

| Mes | Faturamento | Clientes | Pedidos | Ticket Medio | Novos | Recompra | Obs |
|-----|-------------|----------|---------|--------------|-------|----------|-----|
| Janeiro | R$ 108.253 | 64 | 81 | R$ 1.569 | 64 | 0 | -- |
| Fevereiro | R$ 109.531 | 68 | 94 | R$ 1.165 | 57 | 11 | 11 recompraram |
| Marco* | R$ 241.682 | 78 | 102 | R$ 2.912 | 56 | 22 | Parcial 18/03. FACILITIES=R$133k (55%) |
| **TOTAL Q1** | **R$ 459.465** | **178** | **277** | **R$ 1.659** | **178** | **32** | *Marco parcial -- nao extrapolar |

Detalhes: 2.758 itens SAP | 178 clientes F2B | FACILITIES = 29% do Q1

### 5.2 Validacao Modelo vs Real

| Indicador | Modelo | Real | Variacao | Status | Observacao |
|-----------|--------|------|----------|--------|------------|
| Ticket Medio/Pedido | R$ 1.500 | R$ 1.569 | +4,6% | CONFIRMADO | Modelo conservador -- ok |
| Churn 1a compra | 80% | 83% | +3pp | CONFIRMADO | Proximo da premissa |
| Novos clientes/mes | 22 | 59 | +168% | SUPERADO | 59 SEM vendedora estruturada |
| Recompra Q1 | ~10 cli | 30 cli | +200% | SUPERADO | Ciclo menor que esperado |
| Fat. base sem equipe | R$100K/mes | R$109K/mes | +9% | CONFIRMADO | Base organica solida |
| Fat. Q1 total | R$ 503K | R$ 459K* | -8,7% | PARCIAL | Marco 13 de 22 dias uteis |

**VEREDITO:** Modelo CONSERVADOR -- 4 de 5 premissas confirmadas ou superadas. 59 novos/mes ja acontecem SEM equipe. Com equipe: modelo projeta R$3,16M (+58%).

---

## 6. PAINEL CEO

### 6.1 Resumo Executivo

| Indicador | Valor |
|-----------|-------|
| Faturamento anual 2026 (projecao) | R$ 3.156.614 |
| Faturamento P12 | R$ 327.365 |
| Sobra acumulada | R$ 2.781.614 |
| ROI operacional | 7,4x |
| Ativos P12 | 684 |
| CAC medio | R$ 426 |

**DECISAO:** R$375K investimento --> R$2,78M sobra --> ROI 7,4x --> Payback mes 1 --> 684 ativos P12 --> Fat. +58% vs 2025

### 6.2 Evolucao Mensal: Fat 2025 vs 2026

| Periodo | Fat 2025 | Fat 2026 | Var % | Organica | Novos PDV | Recompra | Redes | Custo | Sobra | Acumulado | Ativos |
|---------|----------|----------|-------|----------|-----------|----------|-------|-------|-------|-----------|--------|
| P1 | 43.265 | 198.500 | +359% | 120.000 | 66.000 | 0 | 12.500 | -22.000 | 176.500 | 176.500 | 101 |
| P2 | 38.004 | 198.547 | +422% | 120.047 | 66.000 | 0 | 12.500 | -22.000 | 176.547 | 353.047 | 121 |
| P3 | 113.363 | 205.795 | +82% | 120.095 | 66.000 | 7.200 | 12.500 | -22.000 | 183.795 | 536.842 | 145 |
| P4 | 17.994 | 237.486 | +1220% | 120.286 | 82.500 | 14.700 | 20.000 | -29.000 | 208.486 | 745.328 | 178 |
| P5 | 233.485 | 254.178 | +9% | 120.478 | 99.000 | 14.700 | 20.000 | -29.000 | 225.178 | 970.506 | 215 |
| P6 | 223.750 | 256.170 | +14% | 120.670 | 99.000 | 16.500 | 20.000 | -29.000 | 227.170 | 1.197.676 | 253 |
| P7 | 161.139 | 278.962 | +73% | 120.862 | 99.000 | 34.100 | 25.000 | -34.000 | 244.962 | 1.442.638 | 316 |
| P8 | 220.074 | 279.154 | +27% | 121.054 | 99.000 | 34.100 | 25.000 | -34.000 | 245.154 | 1.687.792 | 379 |
| P9 | 202.758 | 281.147 | +39% | 121.247 | 99.000 | 35.900 | 25.000 | -34.000 | 247.147 | 1.934.939 | 443 |
| P10 | 275.460 | 319.485 | +16% | 121.585 | 132.000 | 40.900 | 25.000 | -40.000 | 279.485 | 2.214.424 | 522 |
| P11 | 277.674 | 319.825 | +15% | 121.925 | 132.000 | 40.900 | 25.000 | -40.000 | 279.825 | 2.494.249 | 601 |
| P12 | 189.970 | 327.365 | +72% | 122.265 | 132.000 | 48.100 | 25.000 | -40.000 | 287.365 | 2.781.614 | 684 |
| **ANO** | **1.996.936** | **3.156.614** | **+58%** | **1.450.514** | **1.171.500** | **287.100** | **360.000** | **-375.000** | **2.781.614** | **2.781.614** | **684** |

### 6.3 Sinaleiro CRM: 661 Clientes por Nivel

| Nivel | Qtd | % Carteira | Ticket Medio | Acao | Perfil |
|-------|-----|------------|-------------|------|--------|
| VERDE (>60% meta) | 134 | 20,3% | R$ 3.000 | JBP + cross-sell + upsell | Maduro recorrente |
| AMARELO (40-60%) | 63 | 9,5% | R$ 1.800 | Fidelizacao + expansao de mix | Em desenvolvimento |
| ROXO (prospects) | 165 | 24,9% | R$ 0 | 1a compra -- campanha entrada | Nunca compraram |
| REDES/FRANQUIAS | 274 | -- | R$ 2.500 | Gerente dedicado + contrato | Franqueados |

---

## 7. CONFLITOS RESOLVIDOS

### 7.1 Conflitos com Decisao Documentada

| # | Tema | Valor A | Valor B | Decisao | Justificativa |
|---|------|---------|---------|---------|---------------|
| 1 | Receita 2025 | R$2.091M | R$2.101M / R$1.997M | R$2.091M | Valor das abas executivas de diagnostico. Outros sao sub-conjuntos ou totais parciais. |
| 2 | Receita 2026 | R$3.354M | R$3.377M | R$3.377M | PAINEL_CEO_DEFINITIVO tem motor mes a mes completo com formulas. Mais preciso. |
| 3 | Ativos P12 | 207 | 546 | 207 | Motor conservador com churn 80% real. 546 seria churn zero -- irreal para o modelo. |
| 4 | ROI 2026 | 2,9x / 10,2x / 11,3x | -- | 7,4x (nova eq.) | Nova estrutura de equipe: R$375K investimento. Formula: Sobra / Investimento. |
| 5 | Churn/Retencao 2026 | 52%/48% | 65%/35% | 50%/50% | Meta do pos-venda Q3. Real Q1 ja indica 83% -- PV reduz para 50% em 90 dias. |
| 6 | DRAFT 2 sintetico | V12 fabricado | V_FINAL_OK real | V_FINAL_OK | V12_1 e V12_2 com CNPJs invalidos e nomes ficticios. Descartados na auditoria. |
| 7 | Duplicatas (MD5) | 8 pares identicos | -- | 1 copia deletada | PROJECAO_534, SINALEIRO_INTERNO, VITAO360_534, PROJECAO_1566. |
| 8 | Custo equipe 2026 | R$300K (modelo orig.) | R$375K (equipe real) | R$375K | Estrutura real: Q1=R$22K, Q2=R$29K, Q3=R$34K, Q4=R$40K x 3 meses cada. |

### 7.2 Premissas Pendentes

| Premissa | Valor Usado | Status | Se Errado | Acao |
|----------|-------------|--------|-----------|------|
| Custo mensal equipe | ~R$27.200/mes (est.) | PENDENTE RH | CAC e ROI mudam proporcionalmente | Confirmar folha real com RH ate Abr/2026 |
| Food Channel Daiane | Nao modelado | PENDENTE Daiane | Revenue incremental puro | Reuniao Daiane: ticket, pipeline, metas |
| Ramp Nova Rep Q2 | 2 meses para plena capac. | PREMISSA | Se >2m: Q2 menor que projetado | Monitorar semana 4-6 da nova contratacao |
| Churn com PV = 50% | Meta Q3 em 90 dias | PREMISSA | Se 60%: sobra cai ~R$200K | KPI semanal pos-contratacao PV |

---

## 8. PROJECAO TRIMESTRAL

### 8.1 Comparativo Q-a-Q: 2025 vs 2026

| Trimestre | Fat 2025 | Fat 2026 | Variacao | Crescimento Q-a-Q |
|-----------|----------|----------|----------|-------------------|
| Q1 (P1-P3) | R$ 194.632 | R$ 602.842 | +210% | -- |
| Q2 (P4-P6) | R$ 475.229 | R$ 747.834 | +57% | +24% vs Q1 |
| Q3 (P7-P9) | R$ 583.971 | R$ 839.263 | +44% | +12% vs Q2 |
| Q4 (P10-P12) | R$ 743.104 | R$ 966.675 | +30% | +15% vs Q3 |
| **ANO** | **R$ 1.996.936** | **R$ 3.156.614** | **+58%** | -- |

Nota: Fat 2025 ref. no motor = R$1.996.936, nao R$2.091.000. A diferenca de R$94K se deve ao fato de que o motor usa dados mes a mes do SAP que excluem ajustes contabeis incluidos no PAINEL CEO DEFINITIVO. O baseline oficial permanece R$2.091.000.

---

*Documento gerado a partir dos JSONs de inteligencia do CRM VITAO360.*
*Fonte primaria: VITAO360_ULTRA_FINAL (5).xlsx*
*Data de referencia: Marco/2026*
```

---

### Documento 2: `C:\\Users\\User\\OneDrive\\Documentos\\GitHub\\CRM-VITAO360\\data\\docs\\CARTEIRA_BLUEPRINT.md`

