# FASE 1 — ABA CARTEIRA (81 Colunas, 8 Grupos [+])
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

Você vai construir a **aba CARTEIRA** — a fonte única da verdade do CRM VITAO. Contém 81 colunas organizadas em **10 colunas sempre visíveis** + **8 grupos expansíveis [+]** que podem ser recolhidos/expandidos.

**Pré-requisito:** A aba REGRAS já existe no workbook (FASE 0). Você vai ADICIONAR esta aba ao arquivo existente.

**Ferramenta:** openpyxl (Python)
**Arquivo:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx` (já criado na FASE 0)
**Aba:** `CARTEIRA` (inserir como 1ª aba visível, REGRAS fica no final)
**Font padrão:** Arial 10
**Tema:** Light (nunca dark mode)
**Linhas estimadas:** ~6.500 (489 clientes + 5.540 prospects + margem)
**CNPJ = chave primária** (formato 00.000.000/0000-00, 14 dígitos)

---

## ESTRUTURA GERAL

```
CONGELAMENTO: Linha 1 (header) + Colunas A-J (sempre visíveis)
→ Freeze panes em K2

AGRUPAMENTO EXCEL (Group/Outline):
[+1] Colunas K-Q   → IDENTIDADE
[+2] Colunas R-W   → CONTATO
[+3] Colunas X-AE  → CLASSIFICAÇÃO
[+4] Colunas AF-AQ → FINANCEIRO — VENDAS
[+5] Colunas AR-AW → E-COMMERCE
[+6] Colunas AX-BI → POSITIVAÇÃO
[+7] Colunas BJ-BW → OPERACIONAL
[+8] Colunas BX-CC → COMITÊ
```

---

## 10 COLUNAS SEMPRE VISÍVEIS (A-J) — CONGELADAS

| COL | HEADER | TIPO | LARGURA | FÓRMULA/VALIDAÇÃO |
|-----|--------|------|---------|-------------------|
| A | NOME FANTASIA | Texto | 30 | Manual — nome comercial do cliente |
| B | REDE/REGIONAL | Texto | 20 | Manual — rede de franquia ou regional |
| C | UF | Texto | 5 | Manual — sigla estado (2 chars) |
| D | CONSULTOR | Dropdown | 20 | Data Validation → TAB_CONSULTOR (REGRAS) |
| E | SITUAÇÃO | Fórmula | 12 | `=SE(F2="","PROSPECT",SE(F2<=50,"ATIVO",SE(F2<=60,"EM RISCO",SE(F2<=90,"INAT.REC","INAT.ANT"))))` |
| F | DIAS SEM COMPRA | Fórmula | 15 | `=SE(AO2="","",(HOJE()-AO2))` — referencia Data Últ.Pedido em [+4] |
| G | 🚦 SINALEIRO | Fórmula | 10 | Ver regra abaixo |
| H | TIPO CLIENTE | Fórmula | 15 | `=SE(AF2>0,"CLIENTE","PROSPECT")` — AF2 = R$ Total Acumulado |
| I | FASE | Fórmula | 15 | Ver regra abaixo |
| J | TENTATIVA | Fórmula | 12 | `=SE(BQ2>=4,"NUTRIÇÃO","T"&BQ2)` — BQ2 = Tentativas Falhas em [+7] |

### Fórmula SINALEIRO (col G):
```excel
=SE(F2="","🟣",
  SE(F2<=AP2,"🟢",
    SE(F2<=AP2+30,"🟡","🔴")))
```
Onde AP2 = Ciclo Médio em [+4].
- 🟢 dias ≤ ciclo médio → OK
- 🟡 ciclo < dias ≤ ciclo+30 → ATENÇÃO
- 🔴 dias > ciclo+30 → CRÍTICO
- 🟣 nunca comprou (sem data)

### Fórmula FASE (col I):
```excel
=SE(H2="PROSPECT",
  SE(J2="T0","ABERTURA","ATIVAÇÃO"),
  SE(E2="ATIVO","CS/RECOMPRA",
    SE(E2="EM RISCO","ATENÇÃO",
      SE(E2="INAT.REC","SALVAR",
        SE(J2="NUTRIÇÃO","NUTRIÇÃO","PERDA")))))
```

---

## [+1] IDENTIDADE (K-Q, 7 colunas)

| COL | HEADER | TIPO | LARGURA |
|-----|--------|------|---------|
| K | CNPJ | Texto | 20 |
| L | RAZÃO SOCIAL | Texto | 35 |
| M | INSCRIÇÃO ESTADUAL | Texto | 18 |
| N | CIDADE | Texto | 20 |
| O | BAIRRO | Texto | 20 |
| P | ENDEREÇO | Texto | 35 |
| Q | CEP | Texto | 12 |

**Formatação CNPJ:** Texto (não número). Formato display: XX.XXX.XXX/XXXX-XX

---

## [+2] CONTATO (R-W, 6 colunas)

| COL | HEADER | TIPO | LARGURA |
|-----|--------|------|---------|
| R | TELEFONE 1 | Texto | 18 |
| S | TELEFONE 2 | Texto | 18 |
| T | EMAIL | Texto | 30 |
| U | CONTATO PRINCIPAL | Texto | 25 |
| V | CARGO | Texto | 20 |
| W | WHATSAPP | Texto | 18 |

**Formatação telefone:** (XX) XXXXX-XXXX ou +55XXXXXXXXXXX

---

## [+3] CLASSIFICAÇÃO (X-AE, 8 colunas)

| COL | HEADER | TIPO | LARGURA | VALIDAÇÃO |
|-----|--------|------|---------|-----------|
| X | STATUS | Dropdown | 12 | TAB_SITUACAO (REGRAS) |
| Y | CLASSIFICAÇÃO FUNIL | Dropdown | 20 | TAB_FASE (REGRAS) |
| Z | CONSULTOR RESP. | Dropdown | 20 | TAB_CONSULTOR (REGRAS) |
| AA | REDE | Texto | 20 | — |
| AB | SEGMENTO | Texto | 20 | — |
| AC | ORIGEM | Texto | 15 | — |
| AD | DATA CADASTRO | Data | 12 | dd/mm/aaaa |
| AE | CURVA ABC | Texto | 10 | A, B, C ou vazio |

**Formatação condicional CURVA ABC:**
- A = fill `#00B050` (verde), font branca
- B = fill `#FFFF00` (amarelo), font preta
- C = fill `#FFC000` (laranja), font preta

---

## [+4] FINANCEIRO — VENDAS (AF-AQ, 12 colunas)

| COL | HEADER | TIPO | LARGURA | FÓRMULA |
|-----|--------|------|---------|---------|
| AF | R$ TOTAL ACUMULADO | Moeda | 18 | Manual (ETL popula) |
| AG | QTD PEDIDOS | Número | 12 | Manual (ETL popula) |
| AH | TICKET MÉDIO | Moeda | 15 | `=SE(AG2>0,AF2/AG2,0)` |
| AI | R$ ÚLT.PEDIDO | Moeda | 15 | Manual |
| AJ | DATA ÚLT.PEDIDO | Data | 15 | Manual |
| AK | R$ PENÚLT.PEDIDO | Moeda | 15 | Manual |
| AL | DATA PENÚLT.PEDIDO | Data | 15 | Manual |
| AM | CICLO MÉDIO (dias) | Número | 15 | `=SE(AG2>=2,ARREDONDAR((AJ2-AL2),0),45)` |
| AN | DIAS S/COMPRAR | Fórmula | 15 | `=SE(AJ2="","",(HOJE()-AJ2))` |
| AO | MIX PRODUTOS | Número | 12 | Manual (ETL popula) |
| AP | POTENCIAL ESTIMADO | Moeda | 18 | Manual |
| AQ | META MENSAL | Moeda | 15 | Manual |

**IMPORTANTE:** col F (DIAS SEM COMPRA, visível) = espelho de AN. Usar: `=AN2`
**IMPORTANTE:** col AM (CICLO MÉDIO) usado pelo SINALEIRO (col G). Default 45 dias se <2 pedidos.

**Formato moeda:** `R$ #.##0,00` (brasileiro)

---

## [+5] E-COMMERCE (AR-AW, 6 colunas)

| COL | HEADER | TIPO | LARGURA |
|-----|--------|------|---------|
| AR | ACESSA E-COMMERCE | Dropdown | 15 | SIM/NÃO (TAB_SIM_NAO) |
| AS | DATA ÚLT.ACESSO | Data | 15 |
| AT | QTD ACESSOS MÊS | Número | 15 |
| AU | PEDIDO VIA E-COMMERCE | Dropdown | 18 | SIM/NÃO |
| AV | % PEDIDOS E-COMMERCE | Percentual | 18 |
| AW | CATÁLOGO VISUALIZADO | Dropdown | 18 | SIM/NÃO |

---

## [+6] POSITIVAÇÃO (AX-BI, 12 colunas)

| COL | HEADER | TIPO | LARGURA |
|-----|--------|------|---------|
| AX | POSIT.JAN | Dropdown | 8 | SIM/NÃO/vazio |
| AY | POSIT.FEV | Dropdown | 8 | SIM/NÃO/vazio |
| AZ | POSIT.MAR | Dropdown | 8 | SIM/NÃO/vazio |
| BA | POSIT.ABR | Dropdown | 8 | SIM/NÃO/vazio |
| BB | POSIT.MAI | Dropdown | 8 | SIM/NÃO/vazio |
| BC | POSIT.JUN | Dropdown | 8 | SIM/NÃO/vazio |
| BD | POSIT.JUL | Dropdown | 8 | SIM/NÃO/vazio |
| BE | POSIT.AGO | Dropdown | 8 | SIM/NÃO/vazio |
| BF | POSIT.SET | Dropdown | 8 | SIM/NÃO/vazio |
| BG | POSIT.OUT | Dropdown | 8 | SIM/NÃO/vazio |
| BH | POSIT.NOV | Dropdown | 8 | SIM/NÃO/vazio |
| BI | POSIT.DEZ | Dropdown | 8 | SIM/NÃO/vazio |

**Formatação condicional:** SIM = fill `#C6EFCE`, NÃO = fill `#FFC7CE`

---

## [+7] OPERACIONAL (BJ-BW, 14 colunas)

| COL | HEADER | TIPO | LARGURA | FÓRMULA |
|-----|--------|------|---------|---------|
| BJ | DATA ÚLT.ATENDIMENTO | Data | 18 | Manual (atualiza do LOG) |
| BK | ÚLTIMO RESULTADO | Dropdown | 20 | TAB_RESULTADO |
| BL | ÚLTIMO TIPO CONTATO | Dropdown | 25 | TAB_TIPO_CONTATO |
| BM | PRÓX.FOLLOW-UP | Data | 15 | `=SE(BJ2="","",BJ2+PROCV(BK2,TAB_RESULTADO_FOLLOWUP,2,0))` |
| BN | QTD ATEND. MÊS | Número | 12 | Manual (COUNTIFS do LOG) |
| BO | QTD ATEND. TOTAL | Número | 12 | Manual (COUNTIFS do LOG) |
| BP | DIAS DESDE ÚLT.ATEND | Fórmula | 18 | `=SE(BJ2="","",(HOJE()-BJ2))` |
| BQ | TENTATIVAS FALHAS | Número | 15 | Manual (conta NÃO ATENDE + NÃO RESPONDE + RECUSOU) |
| BR | MERCOS ATUALIZADO | Dropdown | 15 | SIM/NÃO |
| BS | ÚLTIMA AÇÃO/NOTA | Texto | 40 | Manual |
| BT | MOTIVO PAROU | Dropdown | 25 | TAB_MOTIVO |
| BU | STATUS FOLLOW-UP | Fórmula | 15 | `=SE(BM2="","SEM FU",SE(BM2<HOJE(),"ATRASADO",SE(BM2=HOJE(),"HOJE","AGENDADO")))` |
| BV | PRIORIDADE | Fórmula | 12 | Ver fórmula abaixo |
| BW | EM RISCO | Fórmula | 10 | `=SE(E(G2="🔴",AF2>1000),"⚠ SIM","NÃO")` |

### Fórmula PRIORIDADE (col BV) — Score 1-100:
```excel
=ARREDONDAR(
  (SE(AF2>10000,30,SE(AF2>5000,20,SE(AF2>1000,10,5))))*0.3 +
  (SE(AN2>90,40,SE(AN2>60,30,SE(AN2>30,20,10))))*0.4 +
  (SE(I2="PERDA",30,SE(I2="SALVAR",25,SE(I2="ATENÇÃO",20,SE(I2="NUTRIÇÃO",10,15)))))*0.3
,0)
```

---

## [+8] COMITÊ (BX-CC, 6 colunas)

| COL | HEADER | TIPO | LARGURA | FÓRMULA |
|-----|--------|------|---------|---------|
| BX | META MÊS | Moeda | 15 | Manual |
| BY | REALIZADO MÊS | Moeda | 15 | Manual |
| BZ | % ATING. MÊS | Percentual | 12 | `=SE(BX2>0,BY2/BX2,0)` |
| CA | META YTD | Moeda | 15 | Manual |
| CB | REALIZADO YTD | Moeda | 15 | Manual |
| CC | % ATING. YTD | Percentual | 12 | `=SE(CA2>0,CB2/CA2,0)` |

**Formatação condicional % ATING:**
- ≥100% = fill `#C6EFCE` (verde claro)
- 70-99% = fill `#FFC000` (amarelo)
- <70% = fill `#FFC7CE` (vermelho claro)

---

## FORMATAÇÃO CONDICIONAL GLOBAL

### Linha inteira baseada na SITUAÇÃO (col E):
- ATIVO → borda esquerda `#00B050` (verde), 3px
- EM RISCO → borda esquerda `#FFC000` (amarelo), 3px
- INAT.REC → borda esquerda `#FFC000` (amarelo), 3px
- INAT.ANT → borda esquerda `#FF0000` (vermelho), 3px
- PROSPECT → borda esquerda `#BDD7EE` (azul), 3px

### Header (linha 1):
- Font: Arial 10, Bold, branca
- Fill: `#1F4E79` (azul escuro)
- Alignment: center, wrap text
- Border: thin all
- Altura linha: 30

### Dados (linha 2+):
- Font: Arial 10
- Alignment: left (texto), center (números/datas), right (moeda)
- Border: thin all
- Zebra: linhas pares `#F2F2F2`

---

## AGRUPAMENTO EXCEL (CRITICAL)

```python
# Grupos expansíveis — colunas (1-indexed)
ws.column_dimensions.group('K', 'Q', hidden=True)    # [+1] IDENTIDADE
ws.column_dimensions.group('R', 'W', hidden=True)    # [+2] CONTATO
ws.column_dimensions.group('X', 'AE', hidden=True)   # [+3] CLASSIFICAÇÃO
ws.column_dimensions.group('AF', 'AQ', hidden=True)  # [+4] FINANCEIRO
ws.column_dimensions.group('AR', 'AW', hidden=True)  # [+5] E-COMMERCE
ws.column_dimensions.group('AX', 'BI', hidden=True)  # [+6] POSITIVAÇÃO
ws.column_dimensions.group('BJ', 'BW', hidden=True)  # [+7] OPERACIONAL
ws.column_dimensions.group('BX', 'CC', hidden=True)  # [+8] COMITÊ

# Outline settings: botões [+] acima
ws.sheet_properties.outlinePr = OutlinePr(summaryBelow=False, summaryRight=False)
```

---

## DATA VALIDATIONS (Dropdowns)

```python
from openpyxl.worksheet.datavalidation import DataValidation

# Aplicar para linhas 2 até 7000 (margem)
dv_consultor = DataValidation(type="list", formula1="TAB_CONSULTOR")
dv_situacao = DataValidation(type="list", formula1="TAB_SITUACAO")
dv_resultado = DataValidation(type="list", formula1="TAB_RESULTADO")
dv_tipo_contato = DataValidation(type="list", formula1="TAB_TIPO_CONTATO")
dv_motivo = DataValidation(type="list", formula1="TAB_MOTIVO")
dv_fase = DataValidation(type="list", formula1="TAB_FASE")
dv_sim_nao = DataValidation(type="list", formula1="TAB_SIM_NAO")

# Colunas que usam cada dropdown:
# D (CONSULTOR), Z (CONSULTOR RESP)  → dv_consultor
# X (STATUS)                          → dv_situacao
# BK (ÚLTIMO RESULTADO)               → dv_resultado
# BL (ÚLTIMO TIPO CONTATO)            → dv_tipo_contato
# BT (MOTIVO PAROU)                   → dv_motivo
# Y (CLASSIFICAÇÃO FUNIL)             → dv_fase
# AR,AU,AW,BR (SIM/NÃO)              → dv_sim_nao
# AX-BI (POSITIVAÇÃO)                 → dv_sim_nao
```

---

## INSTRUÇÕES PARA O CLAUDE

1. Abrir o workbook existente `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
2. Criar aba "CARTEIRA" e posicioná-la como 1ª aba
3. Escrever headers (linha 1) com formatação azul escuro
4. Definir larguras de colunas conforme especificado
5. Aplicar TODAS as fórmulas nas colunas calculadas (E, F, G, H, I, J, AH, AM, AN, BM, BP, BU, BV, BW, BZ, CC)
6. Criar Data Validations (dropdowns) referenciando Named Ranges da aba REGRAS
7. Configurar agrupamento de colunas (8 grupos)
8. Configurar freeze panes em K2
9. Aplicar formatação condicional
10. Inserir 5 linhas de exemplo com dados fictícios para testar fórmulas
11. Rodar `python scripts/recalc.py` e corrigir qualquer erro
12. Remover dados fictícios após validação (ou manter como template)

**CRÍTICO:** 
- Use fórmulas Excel (`=SE()`, `=PROCV()`, `=CONT.SES()`), NUNCA calcule em Python
- Todas as referências à aba REGRAS devem usar Named Ranges
- CNPJ como TEXTO (nunca número) — senão perde zeros à esquerda
- Fórmulas devem estar em PORTUGUÊS (SE, PROCV, CONT.SES, HOJE, etc.)

---

## VALIDAÇÃO (checklist)

- [ ] 81 colunas (A até CC) com headers corretos
- [ ] 10 colunas visíveis (A-J) congeladas
- [ ] 8 grupos expansíveis configurados e recolhidos
- [ ] Todas fórmulas em português e funcionando
- [ ] Dropdowns referenciam Named Ranges da REGRAS
- [ ] Formatação condicional aplicada (SITUAÇÃO, CURVA ABC, POSITIVAÇÃO, % ATING)
- [ ] Freeze panes em K2
- [ ] Zero erros (recalc.py status: success)
- [ ] CNPJ formatado como texto
- [ ] Moeda em formato brasileiro R$ #.##0,00
