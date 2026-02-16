# PROMPT — POPULAR DRAFT 2 (LOG DE ATENDIMENTOS REAIS)
## CRM INTELIGENTE VITAO 360 — V11 LIMPO

> **Copie este prompt inteiro e cole no Claude junto com o arquivo CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx**

---

## CONTEXTO

Sou Leandro, AI Solutions Engineer da VITAO Alimentos. O CRM V11 foi auditado e o DRAFT 2 foi limpo — removemos 441 registros sintéticos. Agora preciso popular o DRAFT 2 com dados REAIS de atendimentos.

O DRAFT 2 é o **Log de Atendimentos** — cada linha = 1 contato realizado com 1 cliente. Ele cresce infinitamente para baixo. Os dados do DRAFT 2 alimentam automaticamente:
- **DASH** (336 fórmulas) → KPIs de atendimento, conversão, vendas
- **CARTEIRA** (58 colunas) → Estágio funil, follow-up, resultado, justificativa semanal
- **Fórmulas auto** (9 colunas) → ESTÁGIO FUNIL, FASE, SINALEIRO, TENTATIVA, FOLLOW-UP, AÇÃO FUTURA, TEMPERATURA, GRUPO DASH, TIPO AÇÃO

---

## ARQUIVO CRM ENVIADO

- **CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx** (13 abas, DRAFT 2 limpo)

## FONTES DE DADOS PARA ATENDIMENTOS (enviar junto)

- **Relatório de Atendimentos Mercos** → exportar do Mercos > Relatórios > Atendimentos
- **Export Deskrio WhatsApp** → tickets/conversas do período (se disponível)
- **Registro manual** → atendimentos registrados em planilha avulsa (se houver)

---

## LAYOUT DRAFT 2 — 31 COLUNAS (NÃO ALTERAR ORDEM)

### 22 Colunas de DADOS (preencher):

| COL | HEADER | TIPO | DESCRIÇÃO | OBRIGATÓRIO |
|-----|--------|------|-----------|-------------|
| A | DATA | Data (dd/mm/aaaa) | Data do atendimento | ✅ SIM |
| B | CONSULTOR | Texto UPPER | Quem atendeu | ✅ SIM |
| C | NOME FANTASIA | Texto | Nome do cliente | ✅ SIM |
| D | CNPJ | 14 dígitos (sem pontuação) | Chave primária | ✅ SIM |
| E | UF | 2 letras UPPER | Estado | ✅ SIM |
| F | REDE / REGIONAL | Texto | Rede/franquia ou vazio | Opcional |
| G | SITUAÇÃO | Lista fixa | Status do cliente | ✅ SIM |
| H | DIAS SEM COMPRA | Número inteiro | Da CARTEIRA/DRAFT 1 | ✅ SIM |
| J | TIPO CLIENTE | Texto | PROSPECT/NOVO/EM DESENVOLVIMENTO/RECORRENTE/FIDELIZADO | Opcional |
| N | WHATSAPP | SIM/NÃO | Usou WhatsApp? | ✅ SIM |
| O | LIGAÇÃO | SIM/NÃO | Fez ligação? | ✅ SIM |
| P | LIGAÇÃO ATENDIDA | SIM/NÃO/vazio | Ligação foi atendida? | Se O=SIM |
| Q | TIPO DO CONTATO | Lista fixa | Tipo do contato | ✅ SIM |
| R | RESULTADO | Lista fixa (REGRAS) | Resultado do atendimento | ✅ SIM |
| S | MOTIVO | Lista fixa (REGRAS) | Motivo (quando negativo) | Se aplicável |
| V | AÇÃO DETALHADA | Texto livre | Detalhe da ação tomada | Opcional |
| W | MERCOS ATUALIZADO | SIM/NÃO | Registrou no Mercos? | ✅ SIM |
| X | NOTA DO DIA | Texto livre | Observações do consultor | Opcional |
| AA | SINALEIRO META | PENDENTE/OK/ALERTA | Status meta mensal | Opcional |
| AC | TIPO PROBLEMA | Texto | Se houve problema | Se aplicável |
| AD | DEMANDA | Texto | Demanda específica | Se aplicável |
| AE | TIPO ATENDIMENTO | ATIVO/RECEPTIVO | Quem iniciou contato | Opcional |

### 9 Colunas AUTOMÁTICAS (NÃO TOCAR — fórmulas já existem):

| COL | HEADER | CALCULA A PARTIR DE |
|-----|--------|---------------------|
| I | ESTÁGIO FUNIL | G (Situação) + R (Resultado) → cruza com REGRAS |
| K | FASE | G (Situação) + R (Resultado) → cruza com REGRAS |
| L | SINALEIRO | H (Dias sem compra) + G (Situação) → 🟢🟡🔴🟣 |
| M | TENTATIVA | D (CNPJ) → conta quantas vezes aparece → T1, T2, T3... |
| T | FOLLOW-UP | A (Data) + R (Resultado) → data do próximo follow-up |
| U | AÇÃO FUTURA | G (Situação) + R (Resultado) → cruza com REGRAS |
| Y | TEMPERATURA | R (Resultado) → 🔥QUENTE / 🟡MORNO / ❄️FRIO |
| Z | GRUPO DASH | R (Resultado) → FUNIL / FOLLOW-UP / PERDA/NUTRIÇÃO |
| AB | TIPO AÇÃO | R (Resultado) → VENDA / RESOLUÇÃO DE PROBLEMA / etc |

---

## VALORES PERMITIDOS (da aba REGRAS)

### CONSULTOR (col B) — usar EXATAMENTE:
```
MANU DITZEL
LARISSA PADILHA
JULIO GADRET
DAIANE STAVICKI
HELDER BRUNKOW
LEANDRO GARCIA
LORRANY
```

### SITUAÇÃO (col G):
```
ATIVO          → Cliente comprou nos últimos 60 dias
INAT.REC       → Inativo recente (61-120 dias sem compra)
INAT.ANT       → Inativo antigo (121+ dias sem compra)
PROSPECT       → Nunca comprou, em prospecção
LEAD           → Prospect qualificado
NOVO           → Primeiro pedido recente
EM RISCO       → Ativo com sinais de churn
```

### RESULTADO (col R) — OBRIGATÓRIO, usar EXATAMENTE:
```
EM ATENDIMENTO       → Contato em andamento
ORÇAMENTO            → Proposta/orçamento enviado
CADASTRO             → Registro de dados realizado
VENDA / PEDIDO       → Pedido efetivado e confirmado
PÓS-VENDA           → Acompanhamento pós-venda
CS (SUCESSO DO CLIENTE) → Pesquisa satisfação
NUTRIÇÃO             → Contato de nutrição/manutenção
RELACIONAMENTO       → Contato relacional
FOLLOW UP 7          → Follow-up 7 dias
FOLLOW UP 15         → Follow-up 15 dias
SUPORTE              → Resolução de problema
NÃO ATENDE           → Cliente não atendeu
NÃO RESPONDE         → Sem resposta no WhatsApp
RECUSOU LIGAÇÃO      → Recusou a ligação
PERDA / FECHOU LOJA  → Cliente perdido
PROSPECÇÃO           → Primeiro contato prospect
```

### MOTIVO (col S) — quando aplicável:
```
AINDA TEM ESTOQUE
PRODUTO NÃO VENDEU / SEM GIRO
LOJA ANEXO/PROXIMO - SM
SÓ QUER COMPRAR GRANEL
PROBLEMA LOGÍSTICO / ENTREGA
PROBLEMA FINANCEIRO / CRÉDITO
PROPRIETARIO / INDISPONÍVEL
FECHANDO / FECHOU LOJA
SEM INTERESSE NO MOMENTO
PRIMEIRO CONTATO / SEM RESPOSTA
SEGUNDA VIA DE BOLETO
SEGUNDA VIA DA NFE
XML
STATUS PEDIDO
ATRASO ENTREGA
PROBLEMA COM PEDIDOS
```

### TIPO DO CONTATO (col Q):
```
PROSPECÇÃO
VENDA
PÓS-VENDA
SUPORTE
NUTRIÇÃO
RELACIONAMENTO
FOLLOW UP
```

---

## REGRAS DE PROCESSAMENTO

### 1. CNPJ (col D) — CHAVE PRIMÁRIA
- Formato: 14 dígitos sem pontuação (ex: 01234567000189)
- CPF: 11 dígitos sem pontuação (ex: 09534909475)
- DEVE existir no DRAFT 1 (col B) — se não existir, sinalizar
- O CNPJ é usado pela CARTEIRA para lookups automáticos

### 2. CONSULTOR (col B) — TERRITÓRIOS
```
1º CIA DA SAUDE ou FITLAND        → JULIO GADRET
2º Redes (Divina Terra, Biomundo,
   Mundo Verde, Vida Leve,
   Tudo em Grãos)                  → DAIANE STAVICKI
3º UF in (SC, PR, RS) sem rede    → MANU DITZEL
4º Resto do Brasil                 → LARISSA PADILHA
```

### 3. INSERÇÃO — Crescimento infinito para baixo
- Primeira linha de dados: **R3** (R1=bloco, R2=headers)
- Inserir a partir de R3, empurrando linhas para baixo
- Ordenação: DATA mais recente primeiro (desc)
- As 9 fórmulas automáticas JÁ EXISTEM de R3 a R502
- Se ultrapassar R502, copiar as fórmulas das 9 colunas para as novas linhas

### 4. DADOS DO CLIENTE — Puxar do DRAFT 1
Para cada CNPJ no atendimento, buscar no DRAFT 1:
- C (NOME FANTASIA) → DRAFT 1 col A
- E (UF) → DRAFT 1 col D
- F (REDE) → DRAFT 1 col I
- G (SITUAÇÃO) → Derivar de DRAFT 1 col L (DIAS SEM COMPRA):
  - 0-60 dias → ATIVO
  - 61-120 dias → INAT.REC
  - 121+ dias → INAT.ANT
  - Sem compra → PROSPECT
- H (DIAS SEM COMPRA) → DRAFT 1 col L

### 5. VALIDAÇÃO PÓS-INSERÇÃO
```
□ Todos os CNPJs existem no DRAFT 1?
□ Todos os RESULTADOs são valores da lista REGRAS?
□ Todos os MOTIVOs (quando preenchidos) são valores da lista?
□ Colunas de fórmula (I, K, L, M, T, U, Y, Z, AB) estão calculando?
□ DASH atualiza KPIs ao abrir no Excel?
□ CARTEIRA colunas AR-AZ mostram dados novos?
□ CARTEIRA justificativas semanais (CM+) contam registros da semana correta?
□ Zero linhas com CNPJ vazio
□ Zero duplicatas exatas (mesmo CNPJ + mesma DATA + mesmo RESULTADO)
```

---

## EFEITO CASCATA (o que acontece automaticamente ao popular)

```
DRAFT 2 populado
    ↓
    ├→ DASH (336 fórmulas recalculam)
    │   ├→ Total atendimentos
    │   ├→ Vendas (COUNTIF RESULTADO="VENDA / PEDIDO")
    │   ├→ % Conversão
    │   ├→ Orçamentos, Follow-ups, Quentes/Frios
    │   └→ Breakdown por consultor e por semana
    │
    ├→ CARTEIRA (10 lookups por cliente)
    │   ├→ AR: Estágio funil (mais recente por CNPJ+DATA)
    │   ├→ AS: Próx follow-up
    │   ├→ AT: Data último atendimento
    │   ├→ AU: Ação futura
    │   ├→ AV: Último resultado
    │   ├→ AW: Motivo
    │   ├→ AY: Tentativa (T1, T2, T3...)
    │   ├→ AZ: Fase
    │   ├→ BH: Próx ação
    │   └→ BI: Ação detalhada
    │
    └→ CARTEIRA (48 justificativas semanais)
        ├→ CM-CP: JAN/2026 semanas 1-4
        ├→ DB-DE: FEV/2026 semanas 1-4
        ├→ DQ-DT: MAR/2026 semanas 1-4
        └→ ... (até DEZ/2026)
```

---

## EXEMPLO DE LINHA COMPLETA

| Col | Valor |
|-----|-------|
| A (DATA) | 18/02/2026 |
| B (CONSULTOR) | MANU DITZEL |
| C (NOME FANTASIA) | EMPÓRIO NATURAL BEM VIVER |
| D (CNPJ) | 12345678000195 |
| E (UF) | PR |
| F (REDE) | VIDA LEVE |
| G (SITUAÇÃO) | ATIVO |
| H (DIAS SEM COMPRA) | 34 |
| I | *=fórmula auto* |
| J (TIPO CLIENTE) | RECORRENTE |
| K | *=fórmula auto* |
| L | *=fórmula auto* |
| M | *=fórmula auto* |
| N (WHATSAPP) | SIM |
| O (LIGAÇÃO) | SIM |
| P (LIGAÇÃO ATENDIDA) | SIM |
| Q (TIPO DO CONTATO) | VENDA |
| R (RESULTADO) | ORÇAMENTO |
| S (MOTIVO) | |
| T | *=fórmula auto* |
| U | *=fórmula auto* |
| V (AÇÃO DETALHADA) | Enviou orçamento linha cookies sem glúten |
| W (MERCOS ATUALIZADO) | SIM |
| X (NOTA DO DIA) | Cliente pediu prazo maior, analisar crédito |
| Y | *=fórmula auto* |
| Z | *=fórmula auto* |
| AA (SINALEIRO META) | PENDENTE |
| AB | *=fórmula auto* |
| AC (TIPO PROBLEMA) | |
| AD (DEMANDA) | |
| AE (TIPO ATENDIMENTO) | ATIVO |

---

## COMANDO FINAL

Popular o DRAFT 2 do CRM V11 com os dados reais de atendimento enviados. Inserir a partir de R3, dados mais recentes primeiro. NÃO tocar nas 9 colunas de fórmula (I, K, L, M, T, U, Y, Z, AB). Validar que todos os CNPJs existem no DRAFT 1. Usar EXATAMENTE os valores das listas do REGRAS. Ao final, reportar: total de atendimentos inseridos, breakdown por consultor, breakdown por resultado, e confirmar que DASH + CARTEIRA estão funcionais.
