# PROMPT — CONSOLIDAÇÃO SEMANAL (AGENDA → DRAFT 2)
## Transferir resultados executados para o log permanente

> **Copie este prompt no Claude junto com o CRM V11 atualizado (após a semana executada)**

---

## CONTEXTO

Final de semana — os consultores preencheram a AGENDA com resultados reais dos atendimentos. Preciso consolidar: transferir todos os registros executados (onde col T/RESULTADO não está vazio) da aba AGENDA para a aba DRAFT 2 (log permanente).

---

## ARQUIVO ENVIADO

- **CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx** — com aba AGENDA preenchida pelos consultores

---

## REGRAS DE TRANSFERÊNCIA

### 1. O que transferir:
- Apenas linhas da AGENDA onde col T (RESULTADO) NÃO está vazio
- Cada linha da AGENDA vira uma linha no DRAFT 2

### 2. Mapeamento AGENDA → DRAFT 2:

| AGENDA | DRAFT 2 | Notas |
|--------|---------|-------|
| A (📅 DATA) | A (DATA) | Manter formato data |
| Derivar do território | B (CONSULTOR) | UPPER CASE |
| B (NOME FANTASIA) | C (NOME FANTASIA) | |
| C (CNPJ) | D (CNPJ) | 14 dígitos |
| D (UF) | E (UF) | |
| E (REDE / REGIONAL) | F (REDE / REGIONAL) | |
| G (SITUAÇÃO) | G (SITUAÇÃO) | |
| F (DIAS SEM COMPRA) | H (DIAS SEM COMPRA) | |
| I (TIPO CLIENTE) | J (TIPO CLIENTE) | |
| P (WHATSAPP) | N (WHATSAPP) | SIM/NÃO |
| Q (LIGAÇÃO) | O (LIGAÇÃO) | SIM/NÃO |
| R (LIGAÇÃO ATENDIDA) | P (LIGAÇÃO ATENDIDA) | |
| S (TIPO DO CONTATO) | Q (TIPO DO CONTATO) | |
| T (RESULTADO) | R (RESULTADO) | ⚠️ Validar vs REGRAS |
| U (MOTIVO) | S (MOTIVO) | ⚠️ Validar vs REGRAS |
| Y (AÇÃO DETALHADA) | V (AÇÃO DETALHADA) | |
| Z (MERCOS ATUALIZADO) | W (MERCOS ATUALIZADO) | |
| AA (NOTA DO DIA) | X (NOTA DO DIA) | |
| — | AA (SINALEIRO META) | PENDENTE |
| AC (TIPO PROBLEMA) | AC (TIPO PROBLEMA) | |
| AD (TAREFA/DEMANDA) | AD (DEMANDA) | |
| O (TIPO ATENDIMENTO) | AE (TIPO ATENDIMENTO) | |

### 3. NÃO tocar nestas 9 colunas do DRAFT 2 (fórmulas automáticas):
I (ESTÁGIO FUNIL), K (FASE), L (SINALEIRO), M (TENTATIVA), T (FOLLOW-UP), U (AÇÃO FUTURA), Y (TEMPERATURA), Z (GRUPO DASH), AB (TIPO AÇÃO)

### 4. Inserção no DRAFT 2:
- Inserir após a última linha com dados (append)
- Ordenar por DATA desc (mais recente primeiro)
- Se fórmulas nas 9 colunas não existirem nas novas linhas, copiar de R3

### 5. Após transferir:
- Limpar apenas as colunas de EXECUÇÃO da AGENDA (P-AD) para a próxima semana
- Manter colunas de CONTEXTO (A-O) para referência
- OU: limpar AGENDA inteira para gerar nova na próxima sexta

### 6. Validação:
```
□ Total transferido = total de linhas com RESULTADO na AGENDA
□ Todos CNPJs validados contra DRAFT 1
□ Todos RESULTADO validados contra REGRAS
□ Fórmulas do DRAFT 2 (9 cols) calculando nas novas linhas
□ DASH recalculou KPIs
□ CARTEIRA lookups atualizados
□ Zero duplicatas exatas (CNPJ + DATA + RESULTADO)
```

---

## COMANDO FINAL

Transferir todos os atendimentos executados da aba AGENDA para a aba DRAFT 2. Validar contra REGRAS. Confirmar integridade das fórmulas. Reportar: total transferido, breakdown por consultor, breakdown por resultado, e confirmar que DASH+CARTEIRA recalcularam.
