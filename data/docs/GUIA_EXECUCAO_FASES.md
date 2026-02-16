# 🚀 GUIA DE EXECUÇÃO — O QUE COLAR E ANEXAR EM CADA FASE
## Claude AI (Chat) vs Claude Code — Passo a Passo Exato

---

## REGRA GERAL

```
CLAUDE AI  = Cola texto do prompt + Anexa arquivos (.md + .xlsx)
CLAUDE CODE = Cola texto do prompt (arquivos ficam no projeto/pasta)
```

**Em AMBOS:** Sempre começa com o ÍNDICE MESTRE + documento da FASE.
**A partir da FASE 1:** Adiciona o .xlsx gerado na fase anterior como "prova" de que existe.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 0 — REGRAS (Foundation)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI (Chat)

**COLAR no campo de texto:**
```
Preciso que você construa a aba REGRAS de uma planilha CRM Excel (.xlsx).
Leia o ÍNDICE MESTRE para entender o projeto completo, depois siga
EXATAMENTE as instruções do documento FASE 0 REGRAS.

Use openpyxl (Python). Fórmulas em PORTUGUÊS. Font Arial 10. Tema light.
Crie o arquivo e me entregue para download.
```

**ANEXAR (arrastar para o chat):**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_0_REGRAS.md`

**RESULTADO ESPERADO:** Download do `JARVIS_CRM_CENTRAL_FEV2026.xlsx` (com 1 aba: REGRAS)

---

### 💻 CLAUDE CODE (Terminal)

**COLAR no terminal:**
```
Leia os arquivos INDICE_MESTRE_JARVIS.md e FASE_0_REGRAS.md que estão
na pasta do projeto. Construa a aba REGRAS conforme especificado.

Use openpyxl. Fórmulas em PORTUGUÊS. Crie Named Ranges. 
Salve como JARVIS_CRM_CENTRAL_FEV2026.xlsx
Rode python scripts/recalc.py para validar.
```

**ARQUIVOS NA PASTA DO PROJETO:**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_0_REGRAS.md`

**RESULTADO:** Arquivo .xlsx criado na pasta do projeto

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 1 — CARTEIRA (81 Colunas)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI (Chat) — CONVERSA NOVA

**COLAR no campo de texto:**
```
Continuando a construção do CRM JARVIS. A FASE 0 (aba REGRAS) já foi 
construída — o arquivo está anexado. Agora preciso da FASE 1: aba CARTEIRA.

Leia o ÍNDICE MESTRE para contexto geral, depois siga EXATAMENTE o 
documento FASE 1 CARTEIRA. Adicione a aba CARTEIRA ao arquivo existente.

IMPORTANTE: A aba REGRAS já tem Named Ranges que a CARTEIRA vai referenciar
para dropdowns. NÃO recrie a aba REGRAS — apenas adicione CARTEIRA.

Use openpyxl. Fórmulas em PORTUGUÊS. Rode recalc.py ao final.
```

**ANEXAR (3 arquivos):**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_1_CARTEIRA.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← **resultado da FASE 0**

**RESULTADO ESPERADO:** .xlsx atualizado (2 abas: CARTEIRA + REGRAS)

---

### 💻 CLAUDE CODE (Terminal)

**COLAR no terminal:**
```
O arquivo JARVIS_CRM_CENTRAL_FEV2026.xlsx já existe com a aba REGRAS.
Leia INDICE_MESTRE_JARVIS.md e FASE_1_CARTEIRA.md.

Adicione a aba CARTEIRA ao arquivo existente conforme especificado.
81 colunas, 8 grupos expansíveis, freeze panes K2, fórmulas em PORTUGUÊS.
Referencia Named Ranges da aba REGRAS para dropdowns.

Rode python scripts/recalc.py e corrija todos os erros.
```

**ARQUIVOS NA PASTA:**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_1_CARTEIRA.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← copiar resultado FASE 0 pra cá

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 2 — LOG (20 Colunas)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI — CONVERSA NOVA

**COLAR:**
```
Continuando CRM JARVIS. As FASES 0 (REGRAS) e 1 (CARTEIRA) já foram
construídas — arquivo anexado tem 2 abas. Agora preciso da FASE 2: aba LOG.

Leia o ÍNDICE MESTRE + FASE 2 LOG. Adicione a aba LOG ao arquivo existente.

O LOG usa ÍNDICE+CORRESP para buscar dados da CARTEIRA pelo CNPJ.
O LOG usa TAB_RESULTADO_FOLLOWUP da REGRAS para calcular follow-ups.
NÃO recrie as abas existentes.

Fórmulas em PORTUGUÊS. Rode recalc.py ao final.
```

**ANEXAR (3 arquivos):**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_2_LOG.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← **resultado da FASE 1** (2 abas)

**RESULTADO:** .xlsx com 3 abas (CARTEIRA + LOG + REGRAS)

---

### 💻 CLAUDE CODE

**COLAR:**
```
Arquivo JARVIS tem REGRAS + CARTEIRA. Leia FASE_2_LOG.md.
Adicione aba LOG (20 colunas). ÍNDICE+CORRESP buscam CARTEIRA pelo CNPJ.
PROCV busca TAB_RESULTADO_FOLLOWUP da REGRAS. Fórmulas PORTUGUÊS.
Rode recalc.py.
```

**PASTA:** INDICE + FASE_2_LOG.md + .xlsx da FASE 1

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 3 — DRAFT 2 (Quarentena, 27 cols)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI — CONVERSA NOVA

**COLAR:**
```
CRM JARVIS — FASES 0-2 prontas (REGRAS + CARTEIRA + LOG). 
Agora FASE 3: aba DRAFT 2 (quarentena de atendimentos, 27 colunas).

Leia ÍNDICE MESTRE + FASE 3 DRAFT2. Adicione aba "DRAFT 2" ao arquivo.

O DRAFT 2 valida se CNPJ existe na CARTEIRA antes de migrar pro LOG.
Fórmulas de validação nas colunas Y-AA.
NÃO recrie abas existentes.
```

**ANEXAR:**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_3_DRAFT2.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← **resultado FASE 2** (3 abas)

**RESULTADO:** .xlsx com 4 abas

---

### 💻 CLAUDE CODE

**COLAR:**
```
Arquivo JARVIS tem REGRAS + CARTEIRA + LOG. Leia FASE_3_DRAFT2.md.
Adicione aba "DRAFT 2" (27 cols). Validação CNPJ contra CARTEIRA.
Colunas Y=VÁLIDO, Z=ERRO, AA=MIGRADO. Fórmulas PORTUGUÊS. Recalc.
```

**PASTA:** INDICE + FASE_3_DRAFT2.md + .xlsx da FASE 2

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 4 — DASH ATENDIMENTOS (7 Blocos)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI — CONVERSA NOVA

**COLAR:**
```
CRM JARVIS — FASES 0-3 prontas. Agora FASE 4: aba DASH (dashboard
de atendimentos com 7 blocos verticais, ~60 linhas).

Leia ÍNDICE MESTRE + FASE 4 DASH. Adicione aba "DASH" ao arquivo.

Todas fórmulas = CONT.SES referenciando a aba LOG.
Filtros: vendedor (dropdown) + período (datas).
Layout VERTICAL — CEO prefere rolar pra baixo.
Máximo 16 colunas (sem scroll horizontal).
NÃO recrie abas existentes.
```

**ANEXAR:**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_4_DASH.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← **resultado FASE 3** (4 abas)

**RESULTADO:** .xlsx com 5 abas

---

### 💻 CLAUDE CODE

**COLAR:**
```
Arquivo JARVIS tem 4 abas. Leia FASE_4_DASH.md.
Adicione aba DASH: 7 blocos verticais, CONT.SES do LOG.
Filtros vendedor + período. Max 16 cols. Fórmulas PORTUGUÊS. Recalc.
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 5 — DASH CLIENTES (4 Blocos)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI — CONVERSA NOVA

**COLAR:**
```
CRM JARVIS — FASES 0-4 prontas. Agora FASE 5: aba DASH CLIENTES
(saúde da carteira, funil por fase, positivação, sinaleiro).

Leia ÍNDICE MESTRE + FASE 5 DASH CLIENTES. Adicione a aba.

Fórmulas CONT.SES e SOMASES referenciando CARTEIRA (não LOG).
4 blocos verticais. Sem filtro de vendedor (visão global).
NÃO recrie abas existentes.
```

**ANEXAR:**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_5_DASH_CLIENTES.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← **resultado FASE 4** (5 abas)

**RESULTADO:** .xlsx com 6 abas (FINAL do master!)

---

### 💻 CLAUDE CODE

**COLAR:**
```
Arquivo JARVIS tem 5 abas. Leia FASE_5_DASH_CLIENTES.md.
Adicione aba "DASH CLIENTES": 4 blocos, CONT.SES/SOMASES da CARTEIRA.
Fórmulas PORTUGUÊS. Recalc.
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## FASE 6 — AGENDA (Arquivo Separado)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🖥️ CLAUDE AI — CONVERSA NOVA

**COLAR:**
```
CRM JARVIS — O arquivo master está COMPLETO (6 abas). Agora FASE 6:
script Python que GERA agendas diárias para consultores.

Leia ÍNDICE MESTRE + FASE 6 AGENDA.

O script deve:
1. Ler o arquivo master JARVIS_CRM_CENTRAL_FEV2026.xlsx
2. Filtrar CARTEIRA por consultor + regras de prioridade
3. Gerar arquivo SEPARADO: AGENDA_[CONSULTOR]_[DATA].xlsx
4. Com 5 linhas cabeçalho + 24 colunas (14 read-only + 10 editável)
5. Dropdowns INLINE (sem Named Ranges — arquivo standalone)

Também crie um TEMPLATE_AGENDA.xlsx vazio como referência.
```

**ANEXAR:**
1. `INDICE_MESTRE_JARVIS.md`
2. `FASE_6_AGENDA.md`
3. `JARVIS_CRM_CENTRAL_FEV2026.xlsx` ← **resultado FASE 5** (6 abas, COMPLETO)

**RESULTADO:** Script `gerar_agenda.py` + `TEMPLATE_AGENDA.xlsx`

---

### 💻 CLAUDE CODE

**COLAR:**
```
Arquivo JARVIS master está completo. Leia FASE_6_AGENDA.md.
Crie script gerar_agenda.py que lê o master, filtra CARTEIRA por
consultor, gera AGENDA_[CONSULTOR]_[DATA].xlsx separado.
24 colunas, dropdowns inline, cabeçalho 5 linhas. Teste com dados.
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## RESUMO VISUAL — FLUXO COMPLETO
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```
┌─────────────────────────────────────────────────────┐
│ FASE 0: REGRAS                                       │
│ ┌─────────────┐  ┌──────────────┐                   │
│ │ ÍNDICE.md   │ +│ FASE_0.md    │ = JARVIS.xlsx v0  │
│ └─────────────┘  └──────────────┘   (1 aba)         │
└────────────────────────┬────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ FASE 1: CARTEIRA                                     │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ ÍNDICE.md   │ +│ FASE_1.md    │ +│ .xlsx v0   │  │
│ └─────────────┘  └──────────────┘  └────────────┘  │
│ = JARVIS.xlsx v1 (2 abas)                           │
└────────────────────────┬────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ FASE 2: LOG                                          │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ ÍNDICE.md   │ +│ FASE_2.md    │ +│ .xlsx v1   │  │
│ └─────────────┘  └──────────────┘  └────────────┘  │
│ = JARVIS.xlsx v2 (3 abas)                           │
└────────────────────────┬────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ FASE 3: DRAFT 2                                      │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ ÍNDICE.md   │ +│ FASE_3.md    │ +│ .xlsx v2   │  │
│ └─────────────┘  └──────────────┘  └────────────┘  │
│ = JARVIS.xlsx v3 (4 abas)                           │
└────────────────────────┬────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ FASE 4: DASH                                         │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ ÍNDICE.md   │ +│ FASE_4.md    │ +│ .xlsx v3   │  │
│ └─────────────┘  └──────────────┘  └────────────┘  │
│ = JARVIS.xlsx v4 (5 abas)                           │
└────────────────────────┬────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ FASE 5: DASH CLIENTES                                │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ ÍNDICE.md   │ +│ FASE_5.md    │ +│ .xlsx v4   │  │
│ └─────────────┘  └──────────────┘  └────────────┘  │
│ = JARVIS.xlsx v5 (6 abas) ★ MASTER COMPLETO        │
└────────────────────────┬────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│ FASE 6: AGENDA (arquivo separado)                    │
│ ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│ │ ÍNDICE.md   │ +│ FASE_6.md    │ +│ .xlsx v5   │  │
│ └─────────────┘  └──────────────┘  └────────────┘  │
│ = gerar_agenda.py + TEMPLATE_AGENDA.xlsx            │
└─────────────────────────────────────────────────────┘
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## DIFERENÇAS CLAUDE AI vs CLAUDE CODE
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| ASPECTO | CLAUDE AI (Chat) | CLAUDE CODE (Terminal) |
|---------|-----------------|----------------------|
| **Como entregar docs** | ANEXAR (arrastar) | COLOCAR NA PASTA do projeto |
| **Prompt** | Texto + anexos | Texto (referencia arquivos na pasta) |
| **Resultado** | Botão download | Arquivo na pasta |
| **Recalc.py** | Claude roda automaticamente | Você pede ou ele roda |
| **Debugging** | Pede pra corrigir no chat | Vê o terminal, corrige ali |
| **Vantagem** | Visual, fácil de usar | Mais controle, iterativo |
| **Limite** | Pode truncar código longo | Sem limite de código |

### DICA ESTRATÉGICA:
Rodar as **mesmas fases em paralelo** nas duas plataformas. Comparar resultados. Usar o MELHOR .xlsx de cada fase como input da próxima.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CHECKLIST POR FASE (validar antes de avançar)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Após CADA fase, verificar:

```
□ Arquivo abre no Excel sem erro?
□ Abas anteriores continuam intactas?
□ Nova aba tem todas as colunas especificadas?
□ Fórmulas calculam (não mostra texto da fórmula)?
□ Dropdowns funcionam (clica e aparece lista)?
□ Formatação está correta (cores, headers, zebra)?
□ Congelamento de painéis funciona?
□ recalc.py retornou "status": "success"?
```

**Se ALGUM item falhar:** NÃO avance. Peça correção na mesma conversa.
**Se TUDO OK:** Baixe/copie o .xlsx e avance pra próxima fase.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## MENSAGEM DE EMERGÊNCIA (se Claude se perder)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Se em qualquer fase o Claude começar a inventar dados, mudar estrutura ou não seguir o documento, cole isso:

```
PARE. Releia o documento FASE_X que te entreguei. 
NÃO invente dados. NÃO mude a estrutura das colunas.
NÃO recrie abas que já existem no arquivo.
Siga EXATAMENTE o que está no documento .md.
Use fórmulas em PORTUGUÊS (SE, PROCV, ÍNDICE, CORRESP, CONT.SES).
NUNCA calcule em Python e hardcode — use fórmulas Excel reais.
```

---

## TEMPO ESTIMADO

| FASE | COMPLEXIDADE | TEMPO ESTIMADO |
|------|-------------|----------------|
| FASE 0 | Simples | 5-10 min |
| FASE 1 | **ALTA** (81 cols, 8 grupos) | 20-30 min |
| FASE 2 | Média (20 cols, PROCV) | 10-15 min |
| FASE 3 | Simples (27 cols, validação) | 10 min |
| FASE 4 | **ALTA** (7 blocos, muitas COUNTIFS) | 20-30 min |
| FASE 5 | Média (4 blocos) | 10-15 min |
| FASE 6 | Média (script + template) | 15-20 min |
| **TOTAL** | | **~1.5 - 2 horas** |
