# FASE 6 — AGENDA (24 Colunas — Template Diário para Consultores)
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

A **AGENDA** NÃO é uma aba fixa no workbook master. É um **arquivo .xlsx separado** gerado diariamente por Leandro, 1 por consultor, enviado via WhatsApp. O consultor preenche durante o dia e devolve.

Este documento especifica o template + um script Python que gera as agendas automaticamente a partir da CARTEIRA.

**Ferramenta:** openpyxl (Python)
**Output:** `AGENDA_[CONSULTOR]_[DDMMAAAA].xlsx` (arquivo separado)
**Font:** Arial 10 | Tema: Light
**Linhas:** ~15-40 clientes/dia por consultor

---

## CABEÇALHO (linhas 1-5, merge)

| LINHA | CONTEÚDO | FORMATAÇÃO |
|-------|----------|------------|
| 1 | 📋 AGENDA DD/MM/AAAA — NOME CONSULTOR | Merge A1:X1, font 14 bold, fill `#1F4E79`, font branca |
| 2 | Cart:XX \| Prosp:XX \| Follow-ups:XX \| Novos:XX | Merge A2:X2, font 10 bold, fill `#D9E2F3` |
| 3 | ⏰ 8:00 Reunião \| ☀ 9-12 CARTEIRA \| 🌙 13-17 PROSPECÇÃO | Merge A3:X3, font 9, fill `#FEF3C7` |
| 4 | ⚠ REGISTRAR: Mercos + Kanban WhatsApp + Esta planilha | Merge A4:X4, font 9 bold, fill `#FFC7CE` (vermelho claro) |
| 5 | (vazio — separador) | |
| 6 | **HEADERS** | Headers das 24 colunas |

**Contadores da linha 2:**
- Cart = total clientes na agenda
- Prosp = clientes com TIPO_CLIENTE="PROSPECT"
- Follow-ups = clientes com follow-up ≤ HOJE
- Novos = clientes sem atendimento anterior

---

## 24 COLUNAS

### Colunas 1-14: READ-ONLY (preenchido por Leandro antes de enviar)

| COL | HEADER | TIPO | LARGURA | ORIGEM (CARTEIRA) |
|-----|--------|------|---------|-------------------|
| A | NOME FANTASIA | Texto | 30 | Col A |
| B | CNPJ | Texto | 20 | Col K |
| C | UF | Texto | 5 | Col C |
| D | REDE/REGIONAL | Texto | 20 | Col B |
| E | TELEFONE | Texto | 18 | Col R |
| F | EMAIL | Texto | 25 | Col T |
| G | SITUAÇÃO | Texto | 12 | Col E |
| H | DIAS SEM COMPRA | Número | 15 | Col F |
| I | 🚦 SINALEIRO | Texto | 10 | Col G |
| J | FASE | Texto | 15 | Col I |
| K | TENTATIVA | Texto | 12 | Col J |
| L | AÇÃO SUGERIDA | Texto | 30 | Col da REGRAS (PROCV resultado → ação) |
| M | BLOCO | Texto | 12 | "MANHÃ" ou "TARDE" (baseado em TIPO_CLIENTE) |
| N | ÚLTIMO RESULTADO | Texto | 20 | Col BK |

### Colunas 15-24: EDITÁVEL (consultor preenche com dropdowns)

| COL | HEADER | TIPO | LARGURA | VALIDAÇÃO |
|-----|--------|------|---------|-----------|
| O | WHATSAPP | Dropdown | 12 | SIM / NÃO |
| P | LIGAÇÃO | Dropdown | 12 | SIM / NÃO |
| Q | LIGAÇÃO ATENDIDA | Dropdown | 15 | SIM / NÃO / N/A |
| R | TIPO AÇÃO | Dropdown | 12 | ATIVO / RECEPTIVO |
| S | TIPO DO CONTATO | Dropdown | 30 | 7 opções (ver REGRAS) |
| T | RESULTADO | Dropdown | 25 | 12 opções (ver REGRAS) |
| U | MOTIVO | Dropdown | 30 | 10 opções (ver REGRAS) |
| V | AÇÃO FUTURA | Texto | 30 | Texto livre |
| W | MERCOS ATUALIZADO | Dropdown | 15 | SIM / NÃO |
| X | NOTA DO DIA | Texto | 50 | Texto livre |

---

## FORMATAÇÃO

### Headers (linha 6):
- Colunas A-N (read-only): Fill `#8DB4E2` (azul claro), font preta bold
- Colunas O-X (editável): Fill `#E2EFDA` (verde claro), font preta bold
- Todas: Arial 10, center, wrap text, border thin

### Dados (linha 7+):
- Colunas A-N: font `#808080` (cinza — read only)
- Colunas O-X: font preta, fill branco (campo editável)
- Border: thin all

### Formatação condicional SINALEIRO (col I):
- 🟢 → fill `#D1FAE5`
- 🟡 → fill `#FEF3C7`
- 🔴 → fill `#FEE2E2`
- 🟣 → fill `#EDE9FE`

### Formatação condicional SITUAÇÃO (col G):
- ATIVO → fill `#C6EFCE`
- EM RISCO → fill `#FFC000`
- INAT.REC → fill `#FFC000`
- INAT.ANT → fill `#FFC7CE`
- PROSPECT → fill `#BDD7EE`

### Freeze panes: A7 (header + 5 linhas cabeçalho)

---

## LÓGICA DE SELEÇÃO (quem entra na agenda?)

### Prioridade 1 — Follow-ups do dia:
```
CARTEIRA onde CONSULTOR = [consultor] E PRÓX.FOLLOW-UP ≤ HOJE()
Ordenar por: PRIORIDADE (desc)
```

### Prioridade 2 — Clientes em risco sem follow-up:
```
CARTEIRA onde CONSULTOR = [consultor] E SITUAÇÃO IN ("EM RISCO", "INAT.REC") E PRÓX.FOLLOW-UP é vazio
Ordenar por: R$ TOTAL ACUMULADO (desc)
```

### Prioridade 3 — Prospects agendados:
```
CARTEIRA onde CONSULTOR = [consultor] E TIPO_CLIENTE = "PROSPECT" E PRÓX.FOLLOW-UP ≤ HOJE()
```

### Limite: ~40 clientes/dia (capacidade realista consultor)

### Atribuição BLOCO (col M):
- MANHÃ (9-12): Clientes carteira (TIPO_CLIENTE="CLIENTE")
- TARDE (13-17): Prospects (TIPO_CLIENTE="PROSPECT")

---

## SCRIPT GERADOR (pseudocódigo)

```python
def gerar_agenda(consultor, data, workbook_master):
    """
    Gera arquivo AGENDA_[CONSULTOR]_[DATA].xlsx
    """
    # 1. Filtrar CARTEIRA pelo consultor
    # 2. Selecionar clientes (prioridade 1, 2, 3)
    # 3. Limitar a ~40 linhas
    # 4. Criar workbook com cabeçalho (5 linhas)
    # 5. Popular colunas A-N (read-only) 
    # 6. Criar dropdowns O-X (editável)
    # 7. Aplicar formatação
    # 8. Salvar AGENDA_{consultor}_{ddmmaaaa}.xlsx
```

---

## DROPDOWNS NO ARQUIVO SEPARADO

Como a AGENDA é um arquivo .xlsx separado (sem aba REGRAS), os dropdowns precisam ser criados com listas inline:

```python
from openpyxl.worksheet.datavalidation import DataValidation

# Exemplo: dropdown RESULTADO
dv_resultado = DataValidation(
    type="list",
    formula1='"EM ATENDIMENTO,ORÇAMENTO,CADASTRO,VENDA/PEDIDO,RELACIONAMENTO,FOLLOW UP 7,FOLLOW UP 15,SUPORTE,NÃO ATENDE,NÃO RESPONDE,RECUSOU LIGAÇÃO,PERDA/FECHOU LOJA"'
)
dv_resultado.error = "Selecione um resultado válido"
dv_resultado.errorTitle = "Resultado Inválido"
ws.add_data_validation(dv_resultado)
dv_resultado.add('T7:T100')
```

Repetir para: SIM/NÃO (O,P,Q,W), TIPO AÇÃO (R), TIPO CONTATO (S), RESULTADO (T), MOTIVO (U)

---

## INSTRUÇÕES PARA O CLAUDE

1. Criar script Python `gerar_agenda.py` que:
   - Lê o workbook master
   - Recebe parâmetro: consultor e data
   - Filtra CARTEIRA pela lógica de seleção
   - Gera arquivo separado com 5 linhas cabeçalho + headers + dados
   - Cria dropdowns inline (sem referência a Named Ranges externos)
   - Aplica toda formatação
2. Criar também um **template vazio** `TEMPLATE_AGENDA.xlsx` para referência
3. Rodar `python scripts/recalc.py` no template

**CRÍTICO:**
- Arquivo SEPARADO do master (não é aba)
- Dropdowns INLINE (sem Named Ranges — arquivo standalone)
- Read-only visual (cinza) mas sem proteção de sheet
- Cabeçalho com contadores dinâmicos
- Máximo ~40 linhas por agenda

---

## VALIDAÇÃO (checklist)

- [ ] 24 colunas com headers corretos
- [ ] Cabeçalho 5 linhas com informações do dia
- [ ] Read-only (A-N) em cinza, editável (O-X) em branco
- [ ] Dropdowns inline funcionando (SIM/NÃO, RESULTADO, etc.)
- [ ] Formatação condicional (SINALEIRO, SITUAÇÃO)
- [ ] Freeze panes após cabeçalho
- [ ] Script gerador funcional
- [ ] Arquivo separado (não aba do master)
