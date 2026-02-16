# FASE 2 — ABA LOG (20 Colunas)
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

A **aba LOG** é o histórico oficial de interações. Cada linha = 1 contato com 1 cliente. Alimenta os dashboards e atualiza a CARTEIRA. Nunca é editada diretamente — dados entram via DRAFT 2 (quarentena validada).

**Pré-requisitos:** Abas REGRAS (FASE 0) e CARTEIRA (FASE 1) já existem no workbook.

**Ferramenta:** openpyxl
**Arquivo:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
**Aba:** `LOG` (inserir após CARTEIRA)
**Font:** Arial 10 | Tema: Light
**Linhas estimadas:** ~5.000-15.000/ano (crescente)

---

## PRINCÍPIO ARQUITETURAL: TWO-BASE

O LOG registra **O QUE ACONTECEU** — a interação em si.
Dados do cliente (nome, CNPJ, status, valores) ficam na CARTEIRA.
O LOG puxa dados da CARTEIRA via PROCV/INDEX, nunca duplica.

**Por isso são 20 colunas (não 28).** Eliminamos: STATUS, ÚLTIMO CONTATO, RESULTADO ATUAL, DATA ÚLTIMO PEDIDO, VALOR PEDIDO, DIAS SEM COMPRAR, CICLO MÉDIO, EXACTSALES ATUALIZADO — já existem na CARTEIRA.

---

## 20 COLUNAS — ESTRUTURA COMPLETA

### BLOCO 1: IDENTIFICAÇÃO (A-G, 7 colunas — auto via PROCV)

| COL | HEADER | TIPO | LARGURA | FÓRMULA |
|-----|--------|------|---------|---------|
| A | DATA | Data | 12 | Manual (data do contato, dd/mm/aaaa) |
| B | CONSULTOR | Dropdown | 20 | Data Validation → TAB_CONSULTOR |
| C | NOME FANTASIA | Fórmula | 30 | `=SE(D2="","",PROCV(D2,CARTEIRA!$K:$A,CORRESP("NOME FANTASIA",CARTEIRA!$1:$1,0)-CORRESP("CNPJ",CARTEIRA!$1:$1,0)+1,0))` |
| D | CNPJ | Texto | 20 | Manual (digitado ou colado) |
| E | UF | Fórmula | 5 | `=SE(D2="","",ÍNDICE(CARTEIRA!C:C,CORRESP(D2,CARTEIRA!K:K,0)))` |
| F | REDE/REGIONAL | Fórmula | 20 | `=SE(D2="","",ÍNDICE(CARTEIRA!B:B,CORRESP(D2,CARTEIRA!K:K,0)))` |
| G | SITUAÇÃO | Fórmula | 12 | `=SE(D2="","",ÍNDICE(CARTEIRA!E:E,CORRESP(D2,CARTEIRA!K:K,0)))` |

**Nota técnica:** As fórmulas PROCV/ÍNDICE buscam pelo CNPJ (col D do LOG) na coluna K da CARTEIRA (CNPJ). Para simplificar, considere usar ÍNDICE+CORRESP que é mais robusto que PROCV quando colunas à esquerda.

**Alternativa simplificada (recomendada):**
```excel
C2: =SE(D2="","",ÍNDICE(CARTEIRA!$A:$A,CORRESP(D2,CARTEIRA!$K:$K,0)))
E2: =SE(D2="","",ÍNDICE(CARTEIRA!$C:$C,CORRESP(D2,CARTEIRA!$K:$K,0)))
F2: =SE(D2="","",ÍNDICE(CARTEIRA!$B:$B,CORRESP(D2,CARTEIRA!$K:$K,0)))
G2: =SE(D2="","",ÍNDICE(CARTEIRA!$E:$E,CORRESP(D2,CARTEIRA!$K:$K,0)))
```

---

### BLOCO 2: CONTATO (H-K, 4 colunas — consultor preenche)

| COL | HEADER | TIPO | LARGURA | VALIDAÇÃO |
|-----|--------|------|---------|-----------|
| H | WHATSAPP | Dropdown | 12 | TAB_SIM_NAO |
| I | LIGAÇÃO | Dropdown | 12 | TAB_SIM_NAO |
| J | LIGAÇÃO ATENDIDA | Dropdown | 15 | SIM / NÃO / N/A |
| K | TIPO AÇÃO | Dropdown | 12 | TAB_TIPO_ACAO (ATIVO / RECEPTIVO) |

**Regra J:** Se I="NÃO" (não ligou), J deve ser "N/A" automaticamente.
**Fórmula sugerida para validação:** Conditional formatting em J — se I="NÃO" e J≠"N/A", highlight vermelho.

---

### BLOCO 3: CLASSIFICAÇÃO (L-N, 3 colunas — consultor preenche)

| COL | HEADER | TIPO | LARGURA | VALIDAÇÃO |
|-----|--------|------|---------|-----------|
| L | TIPO DO CONTATO | Dropdown | 30 | TAB_TIPO_CONTATO (7 opções) |
| M | RESULTADO | Dropdown | 25 | TAB_RESULTADO (12 opções) |
| N | MOTIVO | Dropdown | 30 | TAB_MOTIVO (10 opções) |

**REGRA MOTIVO:** Coluna N só é obrigatória quando L = "MOTIVO/PAROU DE COMPRAR" ou M = "PERDA/FECHOU LOJA". Nos demais casos pode ficar vazia ou "1º CONTATO/SEM MOTIVO".

---

### BLOCO 4: AÇÃO FUTURA (O-P, 2 colunas)

| COL | HEADER | TIPO | LARGURA | FÓRMULA |
|-----|--------|------|---------|---------|
| O | FOLLOW-UP | Data | 15 | `=SE(M2="","",SE(PROCV(M2,TAB_RESULTADO_FOLLOWUP,2,0)=0,"",A2+PROCV(M2,TAB_RESULTADO_FOLLOWUP,2,0)))` |
| P | AÇÃO | Fórmula | 30 | `=SE(M2="","",PROCV(M2,TAB_RESULTADO_FOLLOWUP,3,0))` |

**Lógica:** Busca o RESULTADO (col M) na TAB_RESULTADO_FOLLOWUP da aba REGRAS.
- Coluna 2 = DIAS_FOLLOWUP → soma à DATA (col A) → gera data follow-up
- Coluna 3 = AÇÃO_PADRÃO → texto da próxima ação
- Se DIAS_FOLLOWUP = 0 → sem follow-up (vazio)

---

### BLOCO 5: CONTROLE (Q-T, 4 colunas)

| COL | HEADER | TIPO | LARGURA | FÓRMULA/VALIDAÇÃO |
|-----|--------|------|---------|-------------------|
| Q | MERCOS ATUALIZADO | Dropdown | 15 | TAB_SIM_NAO |
| R | FASE | Fórmula | 15 | `=SE(D2="","",ÍNDICE(CARTEIRA!$I:$I,CORRESP(D2,CARTEIRA!$K:$K,0)))` |
| S | TENTATIVA | Fórmula | 12 | `=SE(D2="","",ÍNDICE(CARTEIRA!$J:$J,CORRESP(D2,CARTEIRA!$K:$K,0)))` |
| T | NOTA DO DIA | Texto | 50 | Texto livre (observações do consultor) |

---

## FORMATAÇÃO VISUAL

### Header (linha 1):
- Font: Arial 10, Bold, branca
- Fill: `#2E75B6` (azul médio — diferente do CARTEIRA para distinguir)
- Alignment: center, wrap text
- Border: thin all
- Altura: 30

### Dados (linha 2+):
- Font: Arial 10
- Border: thin all
- Zebra: linhas pares `#F2F2F2`

### Formatação Condicional por RESULTADO (col M):
- VENDA/PEDIDO → fill `#C6EFCE` (verde claro) na linha inteira
- NÃO ATENDE → fill `#FFC7CE` (vermelho claro) na linha inteira
- NÃO RESPONDE → fill `#FFC7CE`
- RECUSOU LIGAÇÃO → fill `#FFC7CE`
- PERDA/FECHOU LOJA → fill `#FF0000`, font branca
- ORÇAMENTO → fill `#FEF3C7` (amarelo claro)

### Formatação Condicional MERCOS (col Q):
- SIM → fill `#C6EFCE`
- NÃO → fill `#FFC7CE`

---

## CONGELAMENTO E FILTRO

```python
# Freeze panes: header + coluna A-D visíveis
ws.freeze_panes = 'E2'

# AutoFilter em toda a range
ws.auto_filter.ref = 'A1:T1'
```

---

## INSTRUÇÕES PARA O CLAUDE

1. Abrir workbook existente
2. Criar aba "LOG" após CARTEIRA
3. Escrever 20 headers (linha 1) com formatação
4. Aplicar fórmulas ÍNDICE+CORRESP para colunas automáticas (C, E, F, G, O, P, R, S)
5. Criar Data Validations com Named Ranges da REGRAS
6. Aplicar formatação condicional (RESULTADO, MERCOS)
7. Configurar freeze panes em E2
8. Ativar AutoFilter
9. Inserir 3-5 linhas exemplo para testar fórmulas (com CNPJs que existam na CARTEIRA)
10. Rodar `python scripts/recalc.py` e validar zero erros
11. Definir larguras de coluna

**CRÍTICO:**
- Fórmulas em PORTUGUÊS (ÍNDICE, CORRESP, PROCV, SE)
- CNPJ como TEXTO
- Fórmulas ÍNDICE+CORRESP buscam na CARTEIRA pelo CNPJ (col K da CARTEIRA)
- FOLLOW-UP automático busca na TAB_RESULTADO_FOLLOWUP (aba REGRAS)
- LOG nunca duplica informação da CARTEIRA

---

## VALIDAÇÃO (checklist)

- [ ] 20 colunas (A-T) com headers corretos
- [ ] Fórmulas ÍNDICE+CORRESP funcionam (C, E, F, G, R, S)
- [ ] FOLLOW-UP automático calcula corretamente (col O)
- [ ] AÇÃO PADRÃO puxa da REGRAS (col P)
- [ ] Dropdowns funcionam (B, H, I, J, K, L, M, N, Q)
- [ ] Formatação condicional por RESULTADO
- [ ] Freeze panes em E2
- [ ] AutoFilter ativo
- [ ] Zero erros (recalc.py)
- [ ] Font Arial 10, tema light
