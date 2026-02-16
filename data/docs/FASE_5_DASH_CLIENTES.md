# FASE 5 — ABA DASH CLIENTES (4 Blocos — Visão por Cliente)
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

A **aba DASH CLIENTES** é complementar ao DASH ATENDIMENTOS. Enquanto o DASH principal mede atividades (contatos, resultados), este mede a **saúde da carteira** — quantos clientes ativos, inativos, em risco, positivação.

**Pré-requisitos:** Abas REGRAS, CARTEIRA, LOG e DASH existem.

**Ferramenta:** openpyxl
**Arquivo:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
**Aba:** `DASH CLIENTES` (inserir após DASH)
**Font:** Arial 10 | Tema: Light
**Layout:** Vertical, 4 blocos, ~40 linhas

---

## BLOCO 1 — SAÚDE DA CARTEIRA (linhas 1-12)

**Título:** "📊 SAÚDE DA CARTEIRA" | fill `#1F4E79`, font branca

| | A: INDICADOR | B: QTD | C: % | D: META | E: GAP |
|---|------------|-------|------|---------|--------|
| 3 | CLIENTES ATIVOS | COUNTIFS SITUAÇÃO="ATIVO" | % do total | — | — |
| 4 | EM RISCO | COUNTIFS SITUAÇÃO="EM RISCO" | % | ≤5% | =C4-D4 |
| 5 | INAT.REC (61-90d) | COUNTIFS SITUAÇÃO="INAT.REC" | % | ≤15% | =C5-D5 |
| 6 | INAT.ANT (>90d) | COUNTIFS SITUAÇÃO="INAT.ANT" | % | — | — |
| 7 | PROSPECTS | COUNTIFS TIPO_CLIENTE="PROSPECT" | % | — | — |
| 8 | (vazio) | | | | |
| 9 | **TOTAL CARTEIRA** | SOMA | 100% | | |
| 10 | **TAXA RETENÇÃO** | =ATIVOS/(ATIVOS+INAT.REC+INAT.ANT) | — | ≥50% | =C10-D10 |

**Fórmula B3:**
```excel
=CONT.SES(CARTEIRA!$E:$E,"ATIVO")
```

**Fórmula C3:**
```excel
=SE($B$9>0,B3/$B$9,0)
```

**Formatação condicional col E (GAP):**
- Positivo (acima da meta) → fill `#FFC7CE` (ruim — acima do limite)
- Negativo (abaixo da meta) → fill `#C6EFCE` (bom — dentro do limite)
- TAXA RETENÇÃO: inverso (positivo=bom, negativo=ruim)

---

## BLOCO 2 — FUNIL POR FASE (linhas 14-24)

**Título:** "🔄 FUNIL POR FASE" | fill `#1F4E79`

| | A: FASE | B: QTD | C: % | D: TICKET MÉDIO | E: R$ POTENCIAL |
|---|--------|-------|------|----------------|----------------|
| 16 | ABERTURA | COUNTIFS FASE | % | MÉDIASES | =B*D |
| 17 | ATIVAÇÃO | | | | |
| 18 | CS/RECOMPRA | | | | |
| 19 | ATENÇÃO | | | | |
| 20 | SALVAR | | | | |
| 21 | PERDA | | | | |
| 22 | NUTRIÇÃO | | | | |
| 23 | **TOTAL** | | | | |

**Fórmula B16:**
```excel
=CONT.SES(CARTEIRA!$I:$I,"ABERTURA")
```

**Fórmula D16 (Ticket Médio da fase):**
```excel
=SE(B16>0,MÉDIASES(CARTEIRA!$AH:$AH,CARTEIRA!$I:$I,"ABERTURA"),0)
```

**Fórmula E16:**
```excel
=B16*D16
```

**Cores das FASES (col A, fill):**
- ABERTURA/ATIVAÇÃO = `#BDD7EE`
- CS/RECOMPRA = `#C6EFCE`
- ATENÇÃO/SALVAR = `#FFC000`
- PERDA/NUTRIÇÃO = `#FFC7CE`

---

## BLOCO 3 — POSITIVAÇÃO MENSAL (linhas 26-36)

**Título:** "📅 POSITIVAÇÃO MENSAL (clientes que compraram)" | fill `#1F4E79`

| | A: MÊS | B: POSITIVADOS | C: CARTEIRA ATIVA | D: % POSITIVAÇÃO | E: Δ MÊS ANT. |
|---|-------|-------------|-----------------|-----------------|-------------|
| 28 | JAN | COUNTIFS POSIT.JAN="SIM" | (fixo) | =B/C | =D28-D(anterior) |
| 29 | FEV | | | | |
| ... | ... | | | | |
| 39 | DEZ | | | | |
| 40 | **MÉDIA** | MÉDIA | | MÉDIA | |

**Fórmula B28:**
```excel
=CONT.SES(CARTEIRA!$AX:$AX,"SIM")
```
B29 = CONT.SES(CARTEIRA!$AY:$AY,"SIM") ... etc para cada mês

**Fórmula C28:**
```excel
=CONT.SES(CARTEIRA!$H:$H,"CLIENTE")
```

**Fórmula D28:**
```excel
=SE(C28>0,B28/C28,0)
```

**Formatação condicional D (% POSITIVAÇÃO):**
- ≥30% → `#C6EFCE` (bom)
- 20-29% → `#FEF3C7` (médio)
- <20% → `#FFC7CE` (ruim — atual taxa é ~20.3%)

---

## BLOCO 4 — SINALEIRO RESUMO (linhas 42-50)

**Título:** "🚦 DISTRIBUIÇÃO SINALEIRO" | fill `#1F4E79`

| | A: SINALEIRO | B: QTD | C: % | D: R$ ACUMULADO | E: TICKET MÉDIO |
|---|------------|-------|------|----------------|----------------|
| 44 | 🟢 OK (dentro do ciclo) | COUNTIFS | % | SOMASES | MÉDIASES |
| 45 | 🟡 ATENÇÃO (ciclo+30) | | | | |
| 46 | 🔴 CRÍTICO (>ciclo+30) | | | | |
| 47 | 🟣 NUNCA COMPROU | | | | |
| 48 | **TOTAL** | | | | |

**Fórmula B44:**
```excel
=CONT.SES(CARTEIRA!$G:$G,"🟢")
```

**Fórmula D44 (R$ acumulado dos 🟢):**
```excel
=SOMASES(CARTEIRA!$AF:$AF,CARTEIRA!$G:$G,"🟢")
```

**Formatação:**
- Linha 🟢 → fill `#D1FAE5`
- Linha 🟡 → fill `#FEF3C7`
- Linha 🔴 → fill `#FEE2E2`
- Linha 🟣 → fill `#EDE9FE`

---

## INSTRUÇÕES PARA O CLAUDE

1. Abrir workbook existente
2. Criar aba "DASH CLIENTES" após DASH
3. Implementar 4 blocos sequencialmente
4. Fórmulas CONT.SES e SOMASES referenciando CARTEIRA
5. Formatação condicional onde especificado
6. Layout vertical, máximo 6 colunas (A-E ou A-F)
7. Rodar `python scripts/recalc.py`

**CRÍTICO:**
- Fórmulas em PORTUGUÊS
- Referências CARTEIRA: E=SITUAÇÃO, G=SINALEIRO, H=TIPO CLIENTE, I=FASE, AH=TICKET MÉDIO, AF=R$ TOTAL, AX-BI=POSITIVAÇÃO
- Sem filtro de vendedor nesta aba (visão global)

---

## VALIDAÇÃO (checklist)

- [ ] 4 blocos verticais na ordem
- [ ] Saúde carteira calcula corretamente
- [ ] Funil por fase com 7 fases
- [ ] Positivação 12 meses
- [ ] Sinaleiro 4 categorias
- [ ] Formatação condicional (cores fases, sinaleiro, positivação)
- [ ] Zero erros (recalc.py)
