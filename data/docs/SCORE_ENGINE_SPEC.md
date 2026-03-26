# SCORE PONDERADO E MOTOR DE PRIORIDADES

**CRM VITAO360** | 6 dimensoes | Pesos somam 100% | P0-P7

---

## 1. DIMENSOES E PESOS

| # | DIMENSAO | PESO | LOGICA |
|---|----------|------|--------|
| 1 | FASE | 25% | RECOMPRA(100) > NEGOCIAÇÃO(80) > SALVAMENTO(60) > RECUPERAÇÃO(40) > PR |
| 2 | SINALEIRO | 20% | VERMELHO(100) > AMARELO(60) > VERDE(30) > ROXO(0) |
| 3 | CURVA ABC | 20% | A(100) > B(60) > C(30) |
| 4 | TEMPERATURA | 15% | QUENTE(100) > MORNO(60) > FRIO(30) > CRITICO(20) > PERDIDO(0) |
| 5 | TIPO CLIENTE | 10% | MADURO(100) > FIDELIZADO(85) > RECORRENTE(70) > EM DESENV(50) > NOVO(3 |
| 6 | TENTATIVAS | 10% | T1(100) > T2(70) > T3(40) > T4(10) > NUTRICAO(5) |

## 2. CALCULO

SCORE = Sum(dimensao_score x peso) para as 6 dimensoes

Exemplo: RECOMPRA(100x0.25) + AMARELO(60x0.20) + A(100x0.20) + QUENTE(100x0.15) + RECORRENTE(70x0.10) + T1(100x0.10) = 89.0 = P2

## 3. PRIORIDADES P0-P7

| P | NOME | COMO GERA | SCORE | DISTRIBUICAO |
|---|------|-----------|-------|-------------|
| P0 | IMEDIATA | BLOQUEIO: SUPORTE com problema aberto | N/A | Pula fila |
| P1 | URGENTE | BLOQUEIO: EM ATENDIMENTO + FU vencido + CS no praz | N/A | Ate 15/dia |
| P2 | ALTA | Score ponderado 80-100 | 80-100 | 15-20/dia |
| P3 | MEDIA-ALTA | Score ponderado 60-79 | 60-79 | 15-20/dia |
| P4 | MEDIA | Score ponderado 45-59 | 45-59 | 5-10/dia |
| P5 | MEDIA-BAIXA | Score ponderado 30-44 | 30-44 | 5-10/dia |
| P6 | BAIXA | Score ponderado 15-29 | 15-29 | 0-5/dia |
| P7 | NUTRICAO | Score 0-14. Campanha mensal. | 0-14 | 0 (campanha) |

## 4. DESEMPATE

- 1. CURVA ABC (A primeiro)
- 2. TICKET MEDIO (maior primeiro)
- 3. TIPO CLIENTE (mais maduro primeiro)
- 4. FOLLOW-UP mais vencido primeiro

## 5. META BALANCE

Se P2-P5 nao cobrem 80% meta mensal, PROSPECCAO ganha +20 pontos.

## 6. AS 9 DIMENSOES

| # | DIMENSAO | DESCRICAO | VALORES | QUEM PREENCHE |
|---|----------|-----------|---------|---------------|
| 1 | SITUACAO | Status do cliente no Mercos. Read-only. | 4 | Mercos (automatico) |
| 2 | ESTAGIO FUNIL | Posicao no Kanban de atendimento. Sequencial, | 14 | Motor sugere + Consultor  |
| 3 | RESULTADO | O que aconteceu no atendimento. Unico por con | 9 | Consultor (dropdown) |
| 4 | TIPO CLIENTE | Maturidade na carteira. Muda devagar (meses). | 7 | Motor calcula (historico  |
| 5 | FASE | Estrategia comercial do momento. Muda rapido. | 6 | Motor gera (SITUACAO x TI |
| 6 | CURVA ABC | Classificacao por faturamento. | 3 | Motor calcula (faturament |
| 7 | TEMPERATURA | Sinal de engajamento. Motor gera. | 5 | Motor gera (RESULTADO) |
| 8 | SINALEIRO | Saude do cliente (dias sem comprar vs ciclo). | 4 | Motor calcula |
| 9 | TENTATIVAS | Sequencia de contato do consultor. | 6 | Motor incrementa |

## 7. PSEUDOCODIGO

