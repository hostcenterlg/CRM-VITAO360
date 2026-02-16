# GUIA DE PROMPTS — ETL JARVIS v2.2
## Filosofia: LIMPAR E CONSOLIDAR mantendo identidade da fonte

### PIPELINE COMPLETO

```
FASE 1 — EXTRAÇÃO (paralelo, cada fonte separada)
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ 01 SAP   │  │ 02 VENDAS│  │ 04 CURVA │  │ 05B ECOM │
│ 4 arq→1  │  │ +POSIT   │  │ ABC      │  │ ERCE     │
│           │  │ 24 arq→1 │  │ 12 arq→1 │  │ 12 arq→1 │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ 03 ATEND │  │ 06 LOG   │  │ 07 DESK  │  │ 08 CART  │
│ MERCOS   │  │ FUNIL    │  │ RIO      │  │ MERCOS   │
│ 3 arq→1  │  │ multi→1  │  │ 12 arq→1 │  │ 7 arq→1  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

FASE 2 — CRUZAMENTO (depende de 03 + 06 + 07 + 08)
┌─────────────────────────────────────────────────────┐
│ 09 ATENDIMENTOS CONSOLIDADO                         │
│ Cruza: Deskrio (tel) + Mercos (CNPJ) + Log (CNPJ)  │
│ → ID unificado por cliente                          │
│ → Histórico mês a mês + detalhe semanal             │
│ → FONTE ÚNICA DA VERDADE de interações              │
└─────────────────────────────────────────────────────┘

FASE 3 — CRM (depende de todos)
Claude Code consome os arquivos tratados → JARVIS
```

### PROMPTS DISPONÍVEIS

| # | Arquivo | Fonte | Input | Output | O que faz |
|---|---------|-------|-------|--------|-----------|
| 01 | PROMPT_01_SAP.txt | SAP | 4 arq | 01_SAP_CONSOLIDADO.xlsx | Base cadastral SAP unificada |
| 02 | PROMPT_02_VENDAS_POSITIVACAO.txt | Mercos | 24 arq | 02_VENDAS_POSITIVACAO_MERCOS.xlsx | Valor por mês (>0 = positivou) |
| 03 | PROMPT_03_ATENDIMENTOS_MERCOS.txt | Mercos | 3 arq | 03_ATENDIMENTOS_MERCOS.xlsx | Atendimentos registrados no ERP |
| 04 | PROMPT_04_CURVA_ABC.txt | Mercos | 12+ arq | 04_CURVA_ABC_MERCOS.xlsx | A/B/C por mês |
| 05B | PROMPT_05B_ECOMMERCE.txt | Mercos | 12+ arq | 05B_ECOMMERCE_MERCOS.xlsx | Acessos portal B2B mês a mês |
| 06 | PROMPT_06_LOG_HISTORICO.txt | Funil | 1 arq (multi-aba) | 06_LOG_FUNIL.xlsx | ~11K interações limpas |
| 07 | PROMPT_07_TICKETS_DESKRIO.txt | Deskrio | 12 arq | 07_TICKETS_DESKRIO.xlsx | 4.885 tickets WhatsApp |
| 08 | PROMPT_08_CARTEIRA_MERCOS.txt | Mercos | 7 arq | 08_CARTEIRA_MERCOS.xlsx | Cadastro completo + prospects |
| **09** | **PROMPT_09_ATENDIMENTOS_CONSOLIDADO.txt** | **Todos** | **03+06+07+08** | **09_ATENDIMENTOS_CONSOLIDADO.xlsx** | **Fonte única interações 12 meses** |

### PADRÃO MÊS A MÊS (4 arquivos seguem a mesma lógica)

```
02_VENDAS:     Cliente | R$_MAR | R$_ABR | ... | (valor > 0 = positivou)
04_CURVA_ABC:  Cliente | A/B/C  | A/B/C  | ... | (classificação por mês)
05B_ECOMMERCE: Cliente | 4      | 0      | 2   | (acessos > 0 = acessou)
09_ATENDIM:    Cliente | 3      | 1      | 5   | (interações por mês + detalhe semanal)
```

Cruzamento: acessou em maio (05B) + não comprou (02) + conversou no WhatsApp (09) = oportunidade real com contexto

### SEQUÊNCIA DE EXECUÇÃO

PARALELO (Fase 1):
- 01, 02, 03, 04, 05B, 06, 07, 08 → rodam independentes

SEQUENCIAL (Fase 2):
- 09 depende de: 03 + 06 + 07 + 08 (usa telefone da carteira pra cruzar com Deskrio)

DEPOIS:
- Claude Code consome tudo → JARVIS CRM

### COMO USAR

1. Abra conversa nova NESTE MESMO PROJETO
2. Cole o conteúdo do prompt .txt
3. Claude explora, mostra estrutura, pede aprovação
4. Processa e gera o .xlsx
5. Baixe e salve

### DADOS DISPONÍVEIS (confirmados)

| Fonte | Arquivos | Registros estimados |
|-------|----------|---------------------|
| SAP (cadastro) | 4 | ~1.701 CNPJs (pós limpeza de vazios) |
| Vendas Mercos | 12 meses | variável |
| Positivação Mercos | 12 meses | variável |
| Curva ABC Mercos | 12 meses | variável |
| E-commerce Mercos | 12 meses | variável |
| Atendimentos Mercos | ~1.591 registros | 1 ano |
| Log Funil antigo | ~10.484 + 586 + 96 + 529 | ~11.700 interações |
| Tickets Deskrio WhatsApp | 4.885 tickets | 12 arquivos, Mar 2025-Jan 2026 |
| Carteira Mercos | ~490 clientes | múltiplas versões |
