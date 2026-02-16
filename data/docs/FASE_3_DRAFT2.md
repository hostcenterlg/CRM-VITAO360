# FASE 3 — ABA DRAFT 2 (27 Colunas — Quarentena de Atendimentos)
## JARVIS CRM CENTRAL — VITAO Alimentos

---

## CONTEXTO RÁPIDO

A **aba DRAFT 2** é a zona de quarentena. Quando consultores devolvem a agenda do dia preenchida, o Leandro (operador) cola os dados aqui. Fórmulas de validação automática verificam se os dados estão corretos antes de migrar para o LOG oficial.

**Princípio:** Consultor NUNCA toca o LOG diretamente. Tudo passa pelo DRAFT 2 primeiro.

**Pré-requisitos:** Abas REGRAS, CARTEIRA e LOG já existem.

**Ferramenta:** openpyxl
**Arquivo:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx`
**Aba:** `DRAFT 2` (inserir após LOG)
**Font:** Arial 10 | Tema: Light

---

## FLUXO OPERACIONAL

```
AGENDA (arquivo externo .xlsx)
    ↓ consultor preenche durante o dia
    ↓ devolve por WhatsApp
DRAFT 2 (quarentena)
    ↓ Leandro cola dados
    ↓ validação automática (cols Y-AA)
    ↓ apenas linhas "OK" migram
LOG (histórico oficial)
```

**Regra de ouro:** Só linhas com Y="OK" e AA=vazio entram no LOG.
Após migrar, marca AA="SIM". NUNCA deletar DRAFT 2 — é backup auditável.

---

## 27 COLUNAS — ESTRUTURA

### Colunas A-X: Espelho da AGENDA (24 colunas)

**Colunas 1-14 (read-only, vieram da agenda gerada pelo Leandro):**

| COL | HEADER | TIPO | LARGURA |
|-----|--------|------|---------|
| A | NOME FANTASIA | Texto | 30 |
| B | CNPJ | Texto | 20 |
| C | UF | Texto | 5 |
| D | REDE/REGIONAL | Texto | 20 |
| E | TELEFONE | Texto | 18 |
| F | EMAIL | Texto | 25 |
| G | SITUAÇÃO | Texto | 12 |
| H | DIAS SEM COMPRA | Número | 15 |
| I | 🚦 SINALEIRO | Texto | 10 |
| J | FASE | Texto | 15 |
| K | TENTATIVA | Texto | 12 |
| L | AÇÃO SUGERIDA | Texto | 30 |
| M | BLOCO | Texto | 12 |
| N | ÚLTIMO RESULTADO | Texto | 20 |

**Colunas 15-24 (editável, preenchidas pelo consultor):**

| COL | HEADER | TIPO | LARGURA | VALIDAÇÃO |
|-----|--------|------|---------|-----------|
| O | WHATSAPP | Dropdown | 12 | TAB_SIM_NAO |
| P | LIGAÇÃO | Dropdown | 12 | TAB_SIM_NAO |
| Q | LIGAÇÃO ATENDIDA | Dropdown | 15 | SIM / NÃO / N/A |
| R | TIPO AÇÃO | Dropdown | 12 | TAB_TIPO_ACAO |
| S | TIPO DO CONTATO | Dropdown | 30 | TAB_TIPO_CONTATO |
| T | RESULTADO | Dropdown | 25 | TAB_RESULTADO |
| U | MOTIVO | Dropdown | 30 | TAB_MOTIVO |
| V | AÇÃO FUTURA | Texto | 30 | Texto livre |
| W | MERCOS ATUALIZADO | Dropdown | 15 | TAB_SIM_NAO |
| X | NOTA DO DIA | Texto | 50 | Texto livre |

---

### Colunas Y-AA: VALIDAÇÃO AUTOMÁTICA (3 colunas)

| COL | HEADER | TIPO | LARGURA | FÓRMULA |
|-----|--------|------|---------|---------|
| Y | ✅ VÁLIDO | Fórmula | 10 | Ver abaixo |
| Z | ⚠ ERRO | Fórmula | 25 | Ver abaixo |
| AA | 📝 MIGRADO | Dropdown | 12 | SIM / vazio |

### Fórmula Y (VÁLIDO):
```excel
=SE(E(B2<>"", T2<>"", S2<>""), "OK", "ERRO")
```
Verifica: CNPJ preenchido E RESULTADO preenchido E TIPO DO CONTATO preenchido.

### Fórmula Z (ERRO — diagnóstico):
```excel
=SE(B2="","CNPJ VAZIO",
  SE(ÉERROS(CORRESP(B2,CARTEIRA!$K:$K,0)),"CNPJ NÃO ENCONTRADO",
    SE(T2="","SEM RESULTADO",
      SE(S2="","SEM TIPO CONTATO",""))))
```

### Formatação condicional:
- Y="OK" → fill `#C6EFCE` (verde)
- Y="ERRO" → fill `#FFC7CE` (vermelho)
- AA="SIM" → linha inteira fill `#D9E2F3` (azul claro, cinza — "já migrado")

---

## FORMATAÇÃO VISUAL

### Header (linha 1):
- Colunas A-N (read-only): Fill `#8DB4E2` (azul claro), font preta bold
- Colunas O-X (editável): Fill `#E2EFDA` (verde claro), font preta bold
- Colunas Y-AA (validação): Fill `#F4B084` (laranja), font preta bold
- Todas: Arial 10, center, wrap text, border thin

### Dados:
- Colunas A-N: font `#808080` (cinza — read-only visual)
- Colunas O-X: font preta normal
- Colunas Y-AA: font preta bold

---

## CONGELAMENTO E FILTRO

```python
ws.freeze_panes = 'C2'  # Nome Fantasia e CNPJ sempre visíveis
ws.auto_filter.ref = 'A1:AA1'
```

---

## PROCESSO DE MIGRAÇÃO (DRAFT 2 → LOG)

Quando Leandro migra dados validados pro LOG:

1. Filtrar DRAFT 2 por Y="OK" e AA=vazio
2. Para cada linha válida, criar nova linha no LOG com mapeamento:

| DRAFT 2 → | LOG |
|------------|-----|
| (data de hoje) | A: DATA |
| (consultor da agenda) | B: CONSULTOR |
| (auto via CNPJ) | C: NOME FANTASIA |
| B: CNPJ | D: CNPJ |
| (auto) | E: UF |
| (auto) | F: REDE/REGIONAL |
| (auto) | G: SITUAÇÃO |
| O: WHATSAPP | H: WHATSAPP |
| P: LIGAÇÃO | I: LIGAÇÃO |
| Q: LIGAÇÃO ATENDIDA | J: LIGAÇÃO ATENDIDA |
| R: TIPO AÇÃO | K: TIPO AÇÃO |
| S: TIPO DO CONTATO | L: TIPO DO CONTATO |
| T: RESULTADO | M: RESULTADO |
| U: MOTIVO | N: MOTIVO |
| (auto via REGRAS) | O: FOLLOW-UP |
| (auto via REGRAS) | P: AÇÃO |
| W: MERCOS ATUALIZADO | Q: MERCOS ATUALIZADO |
| (auto) | R: FASE |
| (auto) | S: TENTATIVA |
| X: NOTA DO DIA | T: NOTA DO DIA |

3. Marcar AA="SIM" nas linhas migradas

**Este processo é manual (Leandro copia). Futuramente pode ser automatizado com VBA/macro.**

---

## INSTRUÇÕES PARA O CLAUDE

1. Abrir workbook existente
2. Criar aba "DRAFT 2" após LOG
3. Escrever 27 headers (linha 1) com formatação tri-color (azul/verde/laranja)
4. Aplicar fórmulas de validação (Y, Z)
5. Criar Data Validations com Named Ranges
6. Configurar formatação condicional (OK/ERRO, MIGRADO)
7. Freeze panes em C2
8. AutoFilter
9. Inserir 3 linhas exemplo (1 OK, 1 CNPJ inválido, 1 sem resultado) para testar
10. Rodar `python scripts/recalc.py`

**CRÍTICO:**
- A coluna B (CNPJ) é a chave de validação — verifica se existe na CARTEIRA
- Fórmulas em PORTUGUÊS
- NUNCA deletar linhas do DRAFT 2 — backup auditável
- Linhas migradas (AA=SIM) ficam cinza

---

## VALIDAÇÃO (checklist)

- [ ] 27 colunas (A-AA) com headers corretos
- [ ] Headers tri-color (read-only azul, editável verde, validação laranja)
- [ ] Fórmula VÁLIDO funciona (Y)
- [ ] Fórmula ERRO diagnostica corretamente (Z)
- [ ] Formatação condicional OK/ERRO/MIGRADO
- [ ] Dropdowns nas colunas editáveis
- [ ] Freeze panes em C2
- [ ] AutoFilter ativo
- [ ] Zero erros (recalc.py)
