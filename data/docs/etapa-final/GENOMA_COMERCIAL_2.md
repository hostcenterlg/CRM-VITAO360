# GENOMA COMERCIAL VITAO360
## INVENTÁRIO FORENSE COMPLETO — ARQUIVO MÃE DE TODAS AS MÃES
### VITAO ALIMENTOS | Versão 1.0 | Fevereiro 2026

---

# ÍNDICE

1. PROPÓSITO E ARQUITETURA
2. ANATOMIA DO CLIENTE (5 tipos)
3. JORNADAS COMPLETAS (6 cenários)
4. MOTOR DE REGRAS (matriz completa)
5. FUNIL — ESTÁGIOS E TRANSIÇÕES
6. DISTRIBUIÇÕES ESTATÍSTICAS (dados reais)
7. CATÁLOGO DE NOTAS (200+ templates)
8. CATÁLOGO DE PROBLEMAS E DEMANDAS
9. PLAYBOOK DE OBJEÇÕES
10. REGRAS DE VALIDAÇÃO
11. GERADOR DE ATENDIMENTOS (receita)

---

# 1. PROPÓSITO E ARQUITETURA

## 1.1 O QUE É ESTE DOCUMENTO

Este documento é o DNA da operação comercial da VITAO Alimentos. Ele contém TODAS as regras, padrões, distribuições e templates necessários para:

- Recriar qualquer atendimento real com fidelidade forense
- Gerar atendimentos sintéticos ultra-realistas
- Validar dados do DRAFT 2 e LOG
- Treinar novos consultores
- Alimentar dashboards e projeções

## 1.2 FONTES DE VERDADE

| FONTE | DADO | PERÍODO |
|-------|------|---------|
| Painel de Atividades (real) | 77.805 msgs, 5.425 conversas, 957 vendas | Jan-Dez 2025 |
| Mercos 2025 | 1.581 atendimentos registrados | Mar-Dez 2025 |
| Deskrio WhatsApp | 4.885 tickets | Jan 2025 - Jan 2026 |
| Vendas Mercos | 973 pedidos | Mar 2025 - Jan 2026 |
| DRAFT 1 | 502 clientes (base mestre) | Atualizado Fev 2026 |
| Playbook Vendas | Estratégias e scripts reais | 2025 |
| Árvore de Problemas | 25 demandas + 89 casos | Abr-Dez 2025 |

## 1.3 MÉTRICAS ÂNCORA (PAINEL DE ATIVIDADES REAL)

```
FUNIL ANUAL 2025:
77.805 msgs totais → 5.425 conversas únicas → 10.634 atendimentos qualificados
→ 1.419 orçamentos → 957 vendas fechadas

TAXA CONVERSÃO GERAL: 9,0%
ATENDIMENTOS POR VENDA: 11,1
MENSAGENS POR VENDA: 81
ORÇAMENTOS POR VENDA: 1,48

JORNADA COMPLETA: 10 contatos | 78 msgs | 17 dias
PRÉ-VENDA: 6 contatos | 30-40 msgs | 7 dias
PÓS-VENDA: 4 contatos | 10-15 msgs | 10 dias
```

## 1.4 REGRA DE OURO — TWO-BASE ARCHITECTURE

```
INVIOLÁVEL:
- Valores financeiros APENAS em BASE_VENDAS
- LOG/DRAFT 2 sempre com R$ 0,00
- CNPJ 14 dígitos sem pontuação como chave universal
- Zero fabricação — tudo rastreável
```

---

# 2. ANATOMIA DO CLIENTE (5 TIPOS)

## 2.1 CLASSIFICAÇÃO POR SITUAÇÃO

| SITUAÇÃO | CRITÉRIO | COR | PRIORIDADE | TIPO VENDA | BLOCO | CADÊNCIA |
|----------|---------|-----|------------|------------|-------|----------|
| ATIVO | Comprou < 60 dias | #00B050 🟢 | 1º | RECOMPRA | LIGAÇÃO MANHÃ | 1x/15 dias |
| EM RISCO | 45-59 dias sem compra | #FFC000 🟡 | 1º | RECOMPRA | LIGAÇÃO MANHÃ | 2x/semana |
| INATIVO RECENTE | 60-180 dias | #FFC000 🟠 | 2º | RESGATE | LIGAÇÃO MANHÃ | 1x/mês |
| INATIVO ANTIGO | > 180 dias | #FF0000 🔴 | 3º | REATIVAÇÃO | LIGAÇÃO TARDE | 1x/trimestre |
| PROSPECT | Nunca comprou | #F2F2F2 ⚪ | 4º | 1ª COMPRA | PROSPECÇÃO | 1x/semana |

## 2.2 PERFIL COMPORTAMENTAL

### ATIVO (115 clientes — 23% da base)
- Conhece a VITAO, já comprou, confia
- Responde WhatsApp em 2-4h
- Aceita ligação ~40% das vezes
- Ticket médio: R$ 1.500-3.000
- Ciclo de recompra: 30-45 dias
- Objeção principal: "Ainda tenho estoque"
- PRECISA: manutenção de vínculo, cross-sell, up-sell

### EM RISCO (7 clientes — 1,4% da base)
- Está entre 45-59 dias sem comprar
- Pode estar testando concorrente
- Responde menos (50% das vezes)
- URGÊNCIA MÁXIMA: se passar de 60 dias vira INATIVO
- PRECISA: abordagem proativa, entender motivo da pausa

### INATIVO RECENTE (86 clientes — 17% da base)
- Parou de comprar faz 2-6 meses
- Ainda lembra da VITAO, pode ser resgatado
- Responde ~30% das vezes
- Objeção: "Encontrei mais barato", "Tive problema na entrega"
- PRECISA: oferta de retorno, resolver problema pendente

### INATIVO ANTIGO (294 clientes — 59% da base)
- Não compra há mais de 6 meses
- Pode ter trocado de fornecedor
- Responde ~15% das vezes
- Muitos números desatualizados
- PRECISA: re-apresentação, condições especiais

### PROSPECT (816 prospects franquias + leads)
- Nunca comprou VITAO
- Desconhece catálogo e condições
- Responde ~10-20% no primeiro contato
- Ciclo de conversão: 15-30 dias
- PRECISA: apresentação, catálogo, primeiro orçamento

## 2.3 QUANTIDADE DE ATENDIMENTOS POR TIPO

| TIPO | MÉDIA ATENDIMENTOS/VENDA | PRÉ-VENDA | PÓS-VENDA | TOTAL |
|------|--------------------------|-----------|-----------|-------|
| PROSPECT → 1ª COMPRA | 8-10 | 6-7 | 3-4 | 10 |
| ATIVO → RECOMPRA | 3-5 | 2-3 | 1-2 | 4 |
| INATIVO RECENTE → RESGATE | 5-8 | 4-6 | 2-3 | 7 |
| INATIVO ANTIGO → REATIVAÇÃO | 5-8 | 4-6 | 2-3 | 7 |
| QUALQUER → NÃO VENDA (perda) | 3-5 | 3-5 | 0 | 4 |
| QUALQUER → NUTRIÇÃO (longo prazo) | 2-3 por ciclo | 2-3 | 0 | 3 |

---

# 3. JORNADAS COMPLETAS (6 CENÁRIOS)

## 3.1 JORNADA A — PROSPECT → 1ª COMPRA (sucesso)
### 10 contatos | 17 dias | ~78 mensagens

```
OFFSET  RESULTADO           CANAL              TIPO AÇÃO    TIPO CONTATO                     TEMPERATURA  ESTÁGIO      NOTA TÍPICA
D-7     EM ATENDIMENTO      WhatsApp           ATIVO        PROSPECÇÃO NOVOS CLIENTES         MORNO        QUALIFICAÇÃO  "Primeiro contato. Apresentação VITAO, catálogo e condições enviadas"
D-6     EM ATENDIMENTO      WhatsApp           ATIVO        PROSPECÇÃO NOVOS CLIENTES         MORNO        QUALIFICAÇÃO  "Follow-up 1. Reforço de interesse, perguntou sobre mix de produtos"
D-5     EM ATENDIMENTO      Ligação (70% ñ at) ATIVO        PROSPECÇÃO NOVOS CLIENTES         MORNO        QUALIFICAÇÃO  "Tentativa de ligação, não atendeu. WhatsApp enviado"
D-4     FOLLOW UP 7         WhatsApp           ATIVO        PROSPECÇÃO NOVOS CLIENTES         FRIO         NUTRIÇÃO      "Cliente pediu retorno semana que vem, disse que vai analisar"
D-3     ORÇAMENTO           WhatsApp           ATIVO        PROSPECÇÃO NOVOS CLIENTES         QUENTE       PROPOSTA      "Orçamento enviado. Sugestão de pedido baseada na Curva ABC regional"
D-2     CADASTRO            WhatsApp           ATIVO        PROSPECÇÃO NOVOS CLIENTES         QUENTE       QUALIFICAÇÃO  "Cadastro aprovado no Mercos. Login e senha enviados"
D0      VENDA               WhatsApp+Tel       ATIVO        PROSPECÇÃO NOVOS CLIENTES         QUENTE       FECHAMENTO    "Pedido confirmado e faturado"
D+1     SUPORTE             WhatsApp           RECEPTIVO    ENVIO DE MATERIAL - MKT           MORNO        SUPORTE       "Material de marketing enviado (catálogo + tabela)"
D+3     SUPORTE             WhatsApp           RECEPTIVO    CONTATOS PASSIVO / SUPORTE        MORNO        SUPORTE       "Cliente perguntou prazo de entrega. Rastreio enviado"
D+7     SUPORTE             WhatsApp           RECEPTIVO    CONTATOS PASSIVO / SUPORTE        MORNO        SUPORTE       "NF-e enviada. Cliente confirmou recebimento"
D+10    CS                  WhatsApp           ATIVO        PÓS VENDA / RELACIONAMENTO        MORNO        RELACIONAMENTO "Pesquisa satisfação. Cliente satisfeito, pediu recompra em 30 dias"
```

### VARIAÇÕES DA JORNADA A:

**A1 — Rápido (cliente decidido):** 6 contatos, 10 dias
- Pula FOLLOW UP 7, vai direto de EM ATENDIMENTO → ORÇAMENTO

**A2 — Lento (cliente indeciso):** 12-15 contatos, 25-30 dias  
- Adiciona 2-3 FOLLOW UPs intermediários + "NÃO RESPONDE" no meio

**A3 — Com problema:** adiciona 2-3 SUPORTEs extras (boleto errado, atraso)

## 3.2 JORNADA B — ATIVO → RECOMPRA (sucesso)
### 4 contatos | 5-7 dias | ~25 mensagens

```
OFFSET  RESULTADO           CANAL              TIPO AÇÃO    TIPO CONTATO                     TEMPERATURA  ESTÁGIO      NOTA TÍPICA
D-3     EM ATENDIMENTO      WhatsApp           ATIVO        ATENDIMENTO CLIENTES ATIVOS      MORNO        QUALIFICAÇÃO  "Sugestão de recompra enviada. Ciclo médio atingido"
D-1     ORÇAMENTO           WhatsApp           ATIVO        ATENDIMENTO CLIENTES ATIVOS      QUENTE       PROPOSTA      "Orçamento aprovado pelo cliente. Pedido em andamento"
D0      VENDA               WhatsApp+Tel       ATIVO        ATENDIMENTO CLIENTES ATIVOS      QUENTE       FECHAMENTO    "Recompra confirmada"
D+2     SUPORTE             WhatsApp           RECEPTIVO    ENVIO DE MATERIAL - MKT           MORNO        SUPORTE       "Material MKT atualizado enviado"
D+5     CS                  WhatsApp           ATIVO        PÓS VENDA / RELACIONAMENTO        MORNO        RELACIONAMENTO "Pedido entregue. Tudo OK"
```

### VARIAÇÕES DA JORNADA B:

**B1 — Ultra-rápido:** 3 contatos (ORÇAMENTO → VENDA → MKT)
- Cliente ativo recorrente, já sabe o que quer

**B2 — Com objeção:** 5-6 contatos
- Adiciona "NÃO RESPONDE" ou "FOLLOW UP 7" entre ORÇAMENTO e VENDA

## 3.3 JORNADA C — INATIVO RECENTE → RESGATE (sucesso)
### 7 contatos | 12-15 dias | ~45 mensagens

```
OFFSET  RESULTADO           CANAL              TIPO AÇÃO    TIPO CONTATO                     TEMPERATURA  ESTÁGIO      NOTA TÍPICA
D-12    EM ATENDIMENTO      WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    FRIO         QUALIFICAÇÃO  "Contato de reativação. Identificar motivo da pausa"
D-10    NÃO RESPONDE        WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    FRIO         TENTATIVA     "Sem retorno. Segunda tentativa com áudio"
D-8     EM ATENDIMENTO      Ligação            ATIVO        ATENDIMENTO CLIENTES INATIVOS    MORNO        QUALIFICAÇÃO  "Ligação atendida. Cliente disse que trocou fornecedor por preço"
D-5     ORÇAMENTO           WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    QUENTE       PROPOSTA      "Orçamento com condições especiais de retorno enviado"
D-2     FOLLOW UP 7         WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    MORNO        NUTRIÇÃO      "Cliente analisando orçamento. Vai responder amanhã"
D0      VENDA               WhatsApp+Tel       ATIVO        ATENDIMENTO CLIENTES INATIVOS    QUENTE       FECHAMENTO    "Resgate confirmado! Cliente voltou a comprar"
D+3     SUPORTE             WhatsApp           RECEPTIVO    ENVIO DE MATERIAL - MKT           MORNO        SUPORTE       "Material MKT enviado + catálogo atualizado"
D+7     CS                  WhatsApp           ATIVO        PÓS VENDA / RELACIONAMENTO        MORNO        RELACIONAMENTO "Acompanhamento pós-resgate. Cliente satisfeito"
```

## 3.4 JORNADA D — INATIVO ANTIGO → REATIVAÇÃO (sucesso)
### 7 contatos | 15-20 dias | ~40 mensagens

```
OFFSET  RESULTADO           CANAL              TIPO AÇÃO    TIPO CONTATO                     TEMPERATURA  ESTÁGIO      NOTA TÍPICA
D-18    EM ATENDIMENTO      WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    FRIO         QUALIFICAÇÃO  "Re-apresentação VITAO. Novo catálogo e condições"
D-15    NÃO RESPONDE        WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    FRIO         TENTATIVA     "Sem retorno no WhatsApp"
D-12    NÃO ATENDE          Ligação            ATIVO        ATENDIMENTO CLIENTES INATIVOS    FRIO         TENTATIVA     "Ligação não atendida. Número pode estar desatualizado"
D-8     EM ATENDIMENTO      WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    MORNO        QUALIFICAÇÃO  "Respondeu! Disse que mudou gestão, quer conhecer condições"
D-4     ORÇAMENTO           WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    QUENTE       PROPOSTA      "Orçamento com desconto progressivo de retorno"
D0      VENDA               WhatsApp           ATIVO        ATENDIMENTO CLIENTES INATIVOS    QUENTE       FECHAMENTO    "Reativação! Primeiro pedido em 8 meses"
D+3     SUPORTE             WhatsApp           RECEPTIVO    ENVIO DE MATERIAL - MKT           MORNO        SUPORTE       "Material MKT + onboarding de reativação"
```

## 3.5 JORNADA E — NÃO VENDA / PERDA (fracasso)
### 4-5 contatos | 10-15 dias

```
OFFSET  RESULTADO           CANAL              TIPO AÇÃO    TIPO CONTATO                     TEMPERATURA  ESTÁGIO      NOTA TÍPICA
D-10    EM ATENDIMENTO      WhatsApp           ATIVO        [POR TIPO]                       MORNO        QUALIFICAÇÃO  "Contato inicial/recontato"
D-7     NÃO RESPONDE        WhatsApp           ATIVO        [POR TIPO]                       FRIO         TENTATIVA     "Sem retorno"
D-4     NÃO ATENDE          Ligação            ATIVO        [POR TIPO]                       FRIO         TENTATIVA     "Ligação não atendida"
D-1     NÃO RESPONDE        WhatsApp           ATIVO        [POR TIPO]                       FRIO         TENTATIVA     "Terceira tentativa sem retorno"
D0      PERDA               —                  —            [POR TIPO]                       PERDIDO      PERDA         "Cliente não respondeu após 3 tentativas. Encerrar ciclo"
```

### VARIAÇÕES DE PERDA:

**E1 — Sumiu:** 3 tentativas sem resposta → PERDA
**E2 — Recusou:** respondeu mas disse "não quero" → PERDA
**E3 — Preço:** "encontrei mais barato" → FOLLOW UP 15 → tentativa futura
**E4 — Problema anterior:** "tive problema na última vez" → escalar para Daiane
**E5 — Fechou loja:** "não estamos mais operando" → PERDA/FECHOU LOJA

## 3.6 JORNADA F — NUTRIÇÃO / LONGO PRAZO (sem venda imediata)
### 2-3 contatos por ciclo | Ciclos trimestrais

```
OFFSET  RESULTADO           CANAL              TIPO AÇÃO    TIPO CONTATO                     TEMPERATURA  ESTÁGIO      NOTA TÍPICA
D0      NUTRIÇÃO            WhatsApp           ATIVO        PÓS VENDA / RELACIONAMENTO       FRIO         NUTRIÇÃO      "Envio de novidades do mês. Catálogo atualizado"
D+7     FOLLOW UP 15        WhatsApp           ATIVO        PÓS VENDA / RELACIONAMENTO       FRIO         NUTRIÇÃO      "Reforço: promoção sazonal. Cliente agradeceu"
```

---

# 4. MOTOR DE REGRAS — MATRIZ COMPLETA

## 4.1 RESULTADO → DERIVADOS AUTOMÁTICOS

| RESULTADO | FOLLOW-UP (dias úteis) | ESTÁGIO FUNIL | TEMPERATURA | FASE | AÇÃO FUTURA |
|-----------|----------------------|---------------|-------------|------|-------------|
| EM ATENDIMENTO | 2 | QUALIFICAÇÃO | MORNO | ATIVAÇÃO | DAR CONTINUIDADE AO ATENDIMENTO |
| ORÇAMENTO | 1 | PROPOSTA | QUENTE | ATIVAÇÃO | COBRAR RETORNO ORÇAMENTO |
| CADASTRO | 2 | QUALIFICAÇÃO | QUENTE | ONBOARDING | ACOMPANHAR PRIMEIRO PEDIDO |
| VENDA / PEDIDO | 45 | FECHAMENTO | QUENTE | CONVERSÃO | ACOMPANHAR PÓS-VENDA |
| FOLLOW UP 7 | 7 | NUTRIÇÃO | MORNO | FOLLOW UP | FOLLOW UP EM 7 DIAS |
| FOLLOW UP 15 | 15 | NUTRIÇÃO | FRIO | FOLLOW UP | FOLLOW UP EM 15 DIAS |
| RELACIONAMENTO | 7 | RELACIONAMENTO | MORNO | RETENÇÃO | MANTER CONTATO PERIÓDICO |
| CS (SUCESSO DO CLIENTE) | 7 | RELACIONAMENTO | MORNO | RETENÇÃO | ACOMPANHAR SUCESSO |
| SUPORTE | 0 | SUPORTE | MORNO | SUPORTE | VERIFICAR RESOLUÇÃO |
| NÃO ATENDE | 1 | TENTATIVA | FRIO | RECUPERAÇÃO | TENTAR NOVAMENTE |
| NÃO RESPONDE | 1 | TENTATIVA | FRIO | RECUPERAÇÃO | TROCAR CANAL DE CONTATO |
| RECUSOU LIGAÇÃO | 2 | TENTATIVA | FRIO | RECUPERAÇÃO | CONTATAR POR WHATSAPP |
| PERDA / FECHOU LOJA | 0 | PERDA | PERDIDO | PERDA | ENCERRAR CICLO |
| NUTRIÇÃO | 30 | NUTRIÇÃO | FRIO | PERDA | NUTRIR COM CONTEÚDO |

## 4.2 SITUAÇÃO → DERIVADOS AUTOMÁTICOS

| SITUAÇÃO | BLOCO | ESTÁGIO FUNIL | TIPO VENDA | COR | PRIORIDADE |
|----------|-------|---------------|------------|-----|------------|
| ATIVO | LIGAÇÃO MANHÃ | CS / RECOMPRA | RECOMPRA | #00B050 🟢 | 1º |
| EM RISCO | LIGAÇÃO MANHÃ | ATENÇÃO / SALVAR | RECOMPRA | #FFC000 🟡 | 1º |
| INATIVO RECENTE | LIGAÇÃO MANHÃ | ATENÇÃO / SALVAR | RESGATE | #ED7D31 🟠 | 2º |
| INATIVO ANTIGO | LIGAÇÃO TARDE | PERDA / NUTRIÇÃO | REATIVAÇÃO | #C00000 🔴 | 3º |
| PROSPECT | PROSPECÇÃO | LEADS / PROSPECTS | 1ª COMPRA | #F2F2F2 ⚪ | 4º |

## 4.3 SITUAÇÃO × RESULTADO → TIPO DO CONTATO

| SITUAÇÃO \ RESULTADO | EM ATEND | ORÇAM | CADASTRO | VENDA | FOLLOW | NÃO RESP | SUPORTE | CS |
|---------------------|----------|-------|----------|-------|--------|----------|---------|-----|
| ATIVO | Atend.Ativos | Atend.Ativos | — | Atend.Ativos | Atend.Ativos | Atend.Ativos | Passivo/Suporte | Pós-Venda |
| INATIVO REC | Atend.Inativos | Atend.Inativos | — | Atend.Inativos | Atend.Inativos | Atend.Inativos | Passivo/Suporte | Pós-Venda |
| INATIVO ANT | Atend.Inativos | Atend.Inativos | — | Atend.Inativos | Atend.Inativos | Atend.Inativos | Passivo/Suporte | Pós-Venda |
| PROSPECT | Prospecção | Prospecção | Prospecção | Prospecção | Prospecção | Prospecção | — | — |

## 4.4 CANAIS E PROBABILIDADES

```
WHATSAPP: 98,3% de todos os contatos → campo WHATSAPP = "SIM" (quase sempre)
LIGAÇÃO: 49,7% dos contatos → campo LIGAÇÃO = "SIM" (metade)
LIGAÇÃO ATENDIDA: 20% das ligações → campo LIGAÇÃO ATENDIDA = "SIM" (1 em 5)

LÓGICA:
- Se WHATSAPP = "SIM" e LIGAÇÃO = "NÃO" → contato 100% digital
- Se LIGAÇÃO = "SIM" e LIGAÇÃO ATENDIDA = "NÃO" → tentativa frustrada (80% dos casos)
- Se LIGAÇÃO = "SIM" e LIGAÇÃO ATENDIDA = "SIM" → conversa telefônica (20%)
- LIGAÇÃO = "NÃO" → LIGAÇÃO ATENDIDA = "N/A"
```

## 4.5 TIPO AÇÃO

```
ATIVO: Consultor iniciou o contato (prospecção, follow-up, recompra)
RECEPTIVO: Cliente iniciou o contato (suporte, dúvida, pedido)

DISTRIBUIÇÃO:
- Pré-venda: 100% ATIVO
- Venda: 80% ATIVO, 20% RECEPTIVO (cliente que vem pedir)
- Pós-venda/Suporte: 30% ATIVO (MKT, CS), 70% RECEPTIVO
- Material MKT: 100% RECEPTIVO
```

## 4.6 GRUPO DASH

```
COMERCIAL: Atendimentos que visam gerar venda
- Tipo Contato: Prospecção, Atend. Ativos, Atend. Inativos, Negociação

RELACIONAMENTO: Atendimentos de manutenção e suporte
- Tipo Contato: Pós-Venda, Suporte, Material MKT, CS
```

---

# 5. FUNIL — ESTÁGIOS E TRANSIÇÕES

## 5.1 ESTÁGIOS DO FUNIL

```
PROSPECÇÃO → QUALIFICAÇÃO → PROPOSTA → FECHAMENTO → RETENÇÃO
     ↓              ↓           ↓          ↓           ↓
  TENTATIVA    NUTRIÇÃO      PERDA      SUPORTE    RELACIONAMENTO
```

## 5.2 TRANSIÇÕES PERMITIDAS

| DE → PARA | CONDIÇÃO | AUTOMÁTICO? |
|-----------|---------|-------------|
| QUALIFICAÇÃO → PROPOSTA | RESULTADO = ORÇAMENTO | SIM |
| PROPOSTA → FECHAMENTO | RESULTADO = VENDA | SIM |
| QUALIFICAÇÃO → NUTRIÇÃO | RESULTADO = FOLLOW UP 7/15 | SIM |
| NUTRIÇÃO → QUALIFICAÇÃO | Retorno do follow-up | SIM |
| QUALIFICAÇÃO → TENTATIVA | RESULTADO = NÃO ATENDE/RESPONDE | SIM |
| TENTATIVA → QUALIFICAÇÃO | Cliente respondeu | SIM |
| TENTATIVA → PERDA | 3+ tentativas sem resposta | MANUAL |
| FECHAMENTO → SUPORTE | RESULTADO = SUPORTE pós-venda | SIM |
| FECHAMENTO → RELACIONAMENTO | RESULTADO = CS | SIM |
| RELACIONAMENTO → QUALIFICAÇÃO | Novo ciclo de recompra | MANUAL |

## 5.3 REGRAS DE MUDANÇA DE STATUS

| EVENTO | ANTES | DEPOIS | IMPACTO FUNIL |
|--------|-------|--------|---------------|
| Primeira compra | PROSPECT | ATIVO | Prospecção → Atend.Ativos |
| Recompra | ATIVO | ATIVO | Mantém |
| 60 dias sem compra | ATIVO | INATIVO REC | Atend.Ativos → Atend.Inativos |
| 180 dias sem compra | INATIVO REC | INATIVO ANT | Mantém Atend.Inativos |
| Compra (era inativo) | INATIVO | ATIVO | Atend.Inativos → Atend.Ativos |

## 5.4 DADOS REAIS DO FUNIL (Painel de Atividades 2025)

| MÊS | MSGS TOTAIS | CONVERSAS ÚNICAS | ATEND. QUALIF | ORÇAMENTOS | VENDAS | ATEND/VENDA | CONV % |
|-----|-------------|-----------------|---------------|------------|--------|-------------|--------|
| JAN | 1.141 | 79 | 156 | 23 | 15 | 10,4 | 9,6% |
| FEV | 1.969 | 137 | 269 | 38 | 25 | 10,8 | 9,3% |
| MAR | 3.235 | 225 | 442 | 60 | 40 | 11,1 | 9,0% |
| ABR | 4.363 | 304 | 596 | 80 | 53 | 11,2 | 8,9% |
| MAI | 6.309 | 440 | 862 | 117 | 78 | 11,1 | 9,0% |
| JUN | 8.801 | 614 | 1.203 | 167 | 111 | 10,8 | 9,2% |
| JUL | 7.010 | 489 | 958 | 126 | 84 | 11,4 | 8,8% |
| AGO | 9.104 | 635 | 1.244 | 170 | 113 | 11,0 | 9,1% |
| SET | 8.673 | 605 | 1.185 | 156 | 104 | 11,4 | 8,8% |
| OUT | 10.209 | 712 | 1.395 | 185 | 123 | 11,3 | 8,8% |
| NOV | 11.180 | 779 | 1.528 | 200 | 133 | 11,5 | 8,7% |
| DEZ | 5.811 | 406 | 796 | 97 | 78 | 10,2 | 9,8% |
| **TOTAL** | **77.805** | **5.425** | **10.634** | **1.419** | **957** | **11,1** | **9,0%** |

---

# 6. DISTRIBUIÇÕES ESTATÍSTICAS (DADOS REAIS)

## 6.1 POR CONSULTOR (Carteira + Performance)

| CONSULTOR | TERRITÓRIO | CLIENTES | % RECEITA | ATEND/MÊS | VENDAS/MÊS |
|-----------|-----------|----------|-----------|-----------|-------------|
| MANU DITZEL | SC, PR, RS | 152 | 32,5% | ~500 | ~30 |
| LARISSA PADILHA | Resto do Brasil | 178 | 28% | ~400 | ~25 |
| JULIO GADRET | Cia Saúde + Fitland | 86 | 22% | ~200* | ~18 |
| DAIANE STAVICKI | Redes/Franquias | 73 + 628 prosp | 15% | ~300 | ~10 |
| HELDER BRUNKOW | Backup/histórico | ~15 | 2,5% | ~50 | ~5 |

*Julio: operação 90% via WhatsApp pessoal, sub-registrado no CRM

## 6.2 POR MÊS — POSITIVAÇÃO

| MÊS | TOTAL | NOVOS | ATIVOS PERM | REATV REC | REATV ANT |
|-----|-------|-------|-------------|-----------|-----------|
| MAR | 21 | 21 | 0 | 0 | 0 |
| ABR | 50 | 43 | 7 | 0 | 0 |
| MAI | 73 | 58 | 14 | 1 | 0 |
| JUN | 103 | 73 | 23 | 5 | 2 |
| JUL | 77 | 39 | 28 | 5 | 5 |
| AGO | 107 | 51 | 36 | 10 | 10 |
| SET | 107 | 46 | 36 | 7 | 18 |
| OUT | 119 | 50 | 38 | 11 | 21 |
| NOV | 127 | 58 | 43 | 7 | 19 |

## 6.3 DISTRIBUIÇÃO DE RESULTADOS (benchmark)

```
RESULTADO                    FREQUÊNCIA     CONTEXTO
EM ATENDIMENTO               40-50%         Contatos intermediários, maioria do volume
VENDA / PEDIDO               8-12%          Conversão final
ORÇAMENTO                    10-15%         Sempre antes da venda
SUPORTE                      10-15%         Pós-venda passivo
RELACIONAMENTO / CS          5-8%           Manutenção
CADASTRO                     3-5%           Apenas novos clientes
FOLLOW UP 7                  3-5%           Cliente pediu tempo
FOLLOW UP 15                 1-3%           Cliente mais distante
NÃO RESPONDE                 5-8%           Tentativas frustradas
NÃO ATENDE                   3-5%           Ligações não atendidas
PERDA / FECHOU LOJA          1-2%           Encerramentos
NUTRIÇÃO                     1-2%           Longo prazo
```

## 6.4 DISTRIBUIÇÃO TEMPORAL

```
DIAS DA SEMANA (APENAS ÚTEIS):
- Segunda: 22% (pico — início de semana, planejamento)
- Terça: 21%
- Quarta: 20%
- Quinta: 20%
- Sexta: 17% (menor — fechamento)
- Sábado/Domingo: 0% (PROIBIDO)

HORÁRIOS (DISTRIBUIÇÃO):
- 08:00-09:00: Reunião interna (sem atendimento)
- 09:00-12:00: PICO — Ligações manhã + carteira (55% do volume)
- 12:00-13:30: Almoço + admin (10%)
- 13:30-16:00: Pós-venda + Prospecção (30%)
- 16:00-17:00: Fechamento + CRM (5%)
```

## 6.5 CAPACIDADE DIÁRIA POR CONSULTOR

```
MÁXIMO: 40 atendimentos/dia

DISTRIBUIÇÃO PADRÃO:
MANHÃ (9h-12h): 22 atendimentos
  - 8 clientes novos (prospecção)
  - 7 clientes ativos (recompra)
  - 4 follow-ups (cobranças de orçamento)
  - 3 vendas (fechamento de pipeline antigo)

TARDE (13:30-16h): 18 atendimentos
  - 7 pós-venda obrigatório (boleto, rastreio, NF, satisfação)
  - 5 suporte passivo (quem ligou/mandou msg)
  - 3 MKT/nutrição (envio de material)
  - 3 CS/follow-up (relacionamento longo prazo)
```

---

# 7. CATÁLOGO DE NOTAS (200+ TEMPLATES)

## 7.1 PRÉ-VENDA — PROSPECÇÃO

```
PRIMEIRO CONTATO:
- "Primeiro contato via WhatsApp. Apresentação VITAO, catálogo digital e condições comerciais enviadas"
- "Contato inicial. Cliente encontrado via pesquisa Google. Apresentação da linha completa"
- "Lead Mercos. Primeiro contato, enviou catálogo e tabela de preços"
- "Indicação do [NOME]. Apresentação VITAO realizada, interesse em granéis"

FOLLOW-UP PRÉ-ORÇAMENTO:
- "Follow-up 1. Cliente visualizou catálogo, perguntou sobre mix de produtos naturais"
- "Reforço de interesse. Cliente pediu mais info sobre linha de suplementos"
- "Segunda tentativa de contato. Áudio enviado com destaque de novidades"
- "Follow-up. Cliente disse que vai analisar com sócio"

TENTATIVAS FRUSTRADAS:
- "Tentativa de ligação, não atendeu. WhatsApp enviado como alternativa"
- "Sem retorno no WhatsApp há 3 dias. Nova tentativa com abordagem diferente"
- "Cliente visualizou mas não respondeu. Envio de promoção sazonal"
- "Terceira tentativa. Ligação não atendida, WhatsApp sem retorno"
```

## 7.2 ORÇAMENTO E CADASTRO

```
ORÇAMENTO:
- "Orçamento enviado. Sugestão baseada na Curva ABC da região"
- "Proposta comercial enviada com condições especiais primeiro pedido"
- "Orçamento atualizado após ajuste de mix solicitado pelo cliente"
- "Orçamento com desconto progressivo de retorno (inativo)"
- "Cotação enviada. Cliente comparando com distribuidor local"

CADASTRO (apenas NOVOS):
- "Cadastro aprovado no Mercos. Login e senha enviados por WhatsApp"
- "Cadastro realizado. Aguardando aprovação de crédito"
- "Dados cadastrais atualizados. Cliente pronto para primeiro pedido"
```

## 7.3 VENDA / FECHAMENTO

```
VENDA:
- "Pedido confirmado e faturado. Previsão entrega em [X] dias"
- "Recompra confirmada. Mix mantido do último pedido + novidades"
- "Primeiro pedido aprovado! Cliente entrou na carteira ativa"
- "Venda fechada após negociação. Desconto especial de retorno aplicado"
- "Pedido via e-commerce B2B confirmado automaticamente"
- "Venda por ligação + WhatsApp. Pedido digitado no Mercos"
```

## 7.4 PÓS-VENDA / SUPORTE

```
MATERIAL MKT (obrigatório após toda venda):
- "Material de marketing enviado (catálogo atualizado + tabela)"
- "Kit MKT digital enviado: banner, tabela, catálogo"
- "Material promocional da campanha [MÊS] enviado"

SUPORTE PASSIVO:
- "Cliente solicitou boleto para pagamento"
- "Cliente perguntou prazo de entrega. Rastreio enviado"
- "Envio de NF-e solicitada pelo cliente"
- "Dúvida sobre estoque de [PRODUTO]. Verificado e informado"
- "Cliente questionou atraso na entrega. Status verificado com logística"
- "Solicitação de segunda via de boleto"
- "Cliente pediu ajuste no pedido (trocar item)"
- "Informação sobre prazo de validade de produtos"

CS / SUCESSO:
- "Pesquisa de satisfação pós-entrega. Cliente satisfeito"
- "Acompanhamento de giro dos produtos. Tudo vendendo bem"
- "CS - cliente relatou boa aceitação da linha integral"
- "Contato de relacionamento. Cliente indicou outro lojista"
```

## 7.5 PROBLEMAS REAIS (extraídos dos 89 casos)

```
LOGÍSTICA:
- "Atraso na entrega. Cliente reclamou, prazo excedido em [X] dias"
- "Pedido chegou com item trocado. Abertura de NFD"
- "Produto chegou danificado. Processo de devolução iniciado"
- "Enviado 64 unidades em vez de 16. Devolução parcial necessária"

FINANCEIRO:
- "Protesto indevido. Boleto já estava pago. Solicitar carta anuência"
- "Link de pagamento falhou. Gerando novo link"
- "Cliente sem limite de cartão. Liberação de boleto com diretor"
- "Cobrança de título devedor. Cliente alega já ter pago"

CADASTRAL:
- "Erro na homologação do sistema. Faturamento travado"
- "Cliente com dados desatualizados no Mercos"
- "CNPJ com pendência fiscal. Bloqueio de pedido"

PRODUTO:
- "Produto em ruptura. Cliente substituiu por item similar"
- "Dúvida sobre laudo técnico de produto. Solicitado ao controle de qualidade"
- "Cliente reclamou da qualidade do lote [X]. Encaminhado para análise"
```

## 7.6 INATIVIDADE E PERDA

```
NÃO RESPONDE:
- "Sem retorno há [X] dias. Tentando outro canal"
- "Cliente visualizou mas não respondeu. Último contato há 5 dias"
- "Três tentativas sem resposta. Classificar como inativo se não retornar"

NÃO ATENDE:
- "Ligação não atendida. WhatsApp enviado como alternativa"
- "Número não existe mais. Verificar cadastro atualizado"
- "Caixa postal. Mensagem de voz deixada"

PERDA:
- "Cliente informou que fechou a loja. Encerramento do ciclo"
- "Perdido para concorrente [X] por preço. Mantido em nutrição"
- "Cliente decidiu não trabalhar com VITAO. Motivo: frete alto"
- "Prospect sem potencial para a linha VITAO. Remoção da lista"

RECUSOU LIGAÇÃO:
- "Cliente recusou ligação. Contato exclusivamente por WhatsApp"
- "Pediu para não ligar. Mantido apenas contato digital"
```

---

# 8. CATÁLOGO DE PROBLEMAS E DEMANDAS

## 8.1 AS 25 DEMANDAS OPERACIONAIS

### PROSPECÇÃO (4)
D01: Prospecções clientes base Mais Granel
D02: Pesquisa Google em cidades potenciais
D03: Responder leads com dúvidas (inbound)
D04: Contato com leads do site

### ATENDIMENTO (5)
D05: Atendimento clientes ativos/inativos
D06: Montar orçamentos sugestão (Curva ABC)
D08: Ligações da base (manutenção)
D09: Ligações da prospect (conversão)
D23: Preencher follow-up (gestão pipeline)

### OPERACIONAL (7)
D07: Respostas no grupo alinhamento sobre pedidos
D10: Fazer rastreios
D12: Digitação de pedidos
D16: Responder dúvidas PCV sobre pedidos
D21: Cadastro no Asana
D22: Solicitar material ao trade
D25: Solicitar estoque (sem SAP)

### FINANCEIRO (6)
D11: Cobrança de títulos devedores
D13: Solicitação de NF (sem SAP)
D14: Solicitação de boletos
D17: Ajustes de boletos
D19: Link de cartão de crédito
D20: Valores do PIX após estoque

### CUSTOMER SUCCESS (2)
D15: Resolução de NFD (notas divergentes)
D18: Suporte com dúvidas produto/laudos/tabelas

### CRÉDITO (1)
D24: Análises de crédito

## 8.2 TOP 8 OBJEÇÕES (PLAYBOOK REAL)

| # | OBJEÇÃO | RESPOSTA | CONVERSÃO |
|---|---------|---------|-----------|
| 1 | "Vende só caixa fechada?" | "Consigo por unidade também" | 90% |
| 2 | Link pagamento falhou | Gerar outro link + fracionar | 65% |
| 3 | "Distribuidor mais barato" | Comparar preço real + contrato | 55% |
| 4 | "Sem limite de cartão" | Liberar boleto com diretor | 80% |
| 5 | "Esse produto não gira" | Tirar do pedido, manter resto | 75% |
| 6 | "Controle financeiro travado" | Aguardar + follow-up | 5% |
| 7 | Atraso entrega anterior | Pedir outra chance + rastreio SMS | 40% |
| 8 | Protesto indevido | Carta anuência + resolver pessoalmente | 95% |

---

# 9. REGRAS DE VALIDAÇÃO

## 9.1 REGRAS OBRIGATÓRIAS (TODA VENDA)

```
[✓] Toda venda tem ORÇAMENTO antes (1-3 dias antes)
[✓] Todo cliente NOVO tem CADASTRO antes (1-2 dias antes)
[✓] Toda venda gera MATERIAL MKT depois (2-3 dias depois)
[✓] NOVOS geram suporte passivo 30% das vezes
[✓] ATIVOS geram suporte passivo 20%
[✓] INATIVOS geram suporte passivo 15%
[✓] Nenhum atendimento em sábado/domingo
[✓] Nenhum valor financeiro no LOG (R$ 0,00 sempre)
[✓] CNPJ = 14 dígitos sem pontuação
[✓] Máximo 40 atendimentos/dia por consultor
```

## 9.2 MÉDIAS DE ATENDIMENTOS (FAIXAS ACEITÁVEIS)

```
NOVOS (1ª compra): 8-10 atendimentos por venda
ATIVOS (recompra): 3-5 atendimentos por venda
INATIVOS (resgate/reativação): 5-8 atendimentos por venda
GERAL: 10-12 atendimentos por venda (média ponderada)
```

## 9.3 SEQUÊNCIAS PROIBIDAS

```
[✗] VENDA sem ORÇAMENTO antes
[✗] CADASTRO para cliente que já existe (só NOVOS)
[✗] SUPORTE antes da VENDA (exceto suporte passivo genérico)
[✗] CS antes da VENDA
[✗] MATERIAL MKT sem VENDA antes
[✗] Mais de 1 VENDA no mesmo dia para o mesmo CNPJ
[✗] FOLLOW UP 7 seguido de FOLLOW UP 7 (sem contato intermediário)
[✗] EM ATENDIMENTO por mais de 5 tentativas sem progressão
```

## 9.4 SEQUÊNCIAS OBRIGATÓRIAS

```
[✓] PROSPECT: EM ATEND → [FOLLOW UP] → ORÇAMENTO → CADASTRO → VENDA
[✓] ATIVO: [EM ATEND] → ORÇAMENTO → VENDA → MKT
[✓] INATIVO: EM ATEND → [NÃO RESP] → [FOLLOW UP] → ORÇAMENTO → VENDA
[✓] PÓS-VENDA: VENDA → MKT (D+2/3) → [SUPORTE] → CS (D+10)
```

---

# 10. PLAYBOOK DE RECOMPRA (SEGUNDA A SEXTA)

## CRONOGRAMA SEMANAL DE REATIVAÇÃO/RECOMPRA

| DIA | MANHÃ | TARDE | OBJETIVO |
|-----|-------|-------|----------|
| SEG | 1ª msg WhatsApp + sugestão pedido | Áudio se não respondeu | Abrir conversa |
| TER | Msg celular pessoal (humanizar) | Msg urgência estoque | Intensificar |
| QUA | Ligação direta na loja | Alerta ruptura | Ação direta |
| QUI | Oferecimento de ajuda | Última tentativa | Fechar ou escalar |
| SEX | Direcionar para MKT (anúncio) | Contato redes sociais | Canal alternativo |

## CADÊNCIA POR RESULTADO DO DIA ANTERIOR

```
Se respondeu positivo → manter canal, enviar orçamento
Se respondeu negativo → entender objeção, adaptar abordagem
Se visualizou e não respondeu → áudio + foto visualização única
Se não visualizou → tentar outro canal (ligação, celular pessoal)
Se bloqueou → encerrar ciclo, marcar como PERDA
```

---

# 11. RECEITA PARA GERAR ATENDIMENTOS SINTÉTICOS

## 11.1 ALGORITMO DE GERAÇÃO (PSEUDO-CÓDIGO)

```python
def gerar_atendimentos_para_venda(cliente, data_venda):
    """
    Para cada venda, gerar a jornada completa de trás pra frente.
    """
    registros = []
    situacao = cliente.situacao
    
    # 1. DETERMINAR JORNADA
    if situacao == 'PROSPECT':
        jornada = JORNADA_A  # 8-10 contatos
        qtd_pre = random.randint(6, 7)
    elif situacao == 'ATIVO':
        jornada = JORNADA_B  # 3-5 contatos
        qtd_pre = random.randint(2, 3)
    elif situacao in ('INAT.REC', 'INAT.ANT'):
        jornada = JORNADA_C_ou_D  # 5-8 contatos
        qtd_pre = random.randint(4, 6)
    
    # 2. GERAR PRÉ-VENDA (de trás pra frente)
    # Último pré-venda: ORÇAMENTO (D-1 a D-3)
    # Se PROSPECT: CADASTRO entre ORÇAMENTO e VENDA
    # Antes do ORÇAMENTO: EM ATENDIMENTO e/ou FOLLOW UPs
    # Intercalar NÃO RESPONDE/NÃO ATENDE (realismo)
    
    # 3. REGISTRO DA VENDA (D0)
    registros.append(criar_registro(data_venda, 'VENDA / PEDIDO'))
    
    # 4. PÓS-VENDA
    # D+2/3: MATERIAL MKT (100% obrigatório)
    # D+1/3: SUPORTE se sorteio (30% novos, 20% ativos, 15% inativos)
    # D+7/10: CS (pesquisa satisfação)
    
    return registros
```

## 11.2 CHECKLIST FINAL DE VALIDAÇÃO

```
ANTES DE ENTREGAR QUALQUER GERAÇÃO:
□ Total registros = soma de todas as jornadas
□ Toda venda tem orçamento D-1 a D-3
□ Novos têm cadastro D-1 a D-2
□ Toda venda tem MKT D+2/3
□ Nenhuma data em fim de semana
□ Nenhum valor financeiro (tudo R$ 0)
□ CNPJs 14 dígitos sem pontuação
□ Máximo 40/dia por consultor
□ Média atendimentos/venda dentro da faixa
□ WhatsApp = SIM em 98%+ dos registros
□ Ligação = SIM em ~50% dos registros
□ Ligação atendida = SIM em ~20% das ligações
□ Notas variadas (não repetir mesma nota >3x)
□ Sequências obrigatórias respeitadas
□ Sequências proibidas ausentes
□ Distribuição de resultados dentro do benchmark
```

---

# CHANGELOG

| VERSÃO | DATA | ALTERAÇÃO |
|--------|------|-----------|
| 1.0 | 16/02/2026 | Criação do documento consolidando TODAS as fontes |

# FONTES CONSOLIDADAS

- DOCUMENTACAO_COMPLETA_CRM.md
- MANUAL_AGENDA_COMERCIAL_VITAO_v3_FINAL.md
- AJUSTE_FUNIL_POR_STATUS.md
- ANALISE_MOVIMENTACAO_COMPLETA.md
- ARVORE_PROBLEMAS_CRM_COMPLETA.docx
- Playbook_Vendas_Vitao_2025.docx
- CAPACIDADE_VENDA_CONSULTOR_EXECUTIVO_v2.docx
- PAINEL_DE_ATIVIDADES_ATENDIMENTO_VS_VENDAS.pdf
- AUDITORIA_GLOBAL_CRM_VITAO360_V11.docx
- DOC_SINALEIRO_COMPLETA.docx
- EXTRACAO_COMPLETA_NOTEBOOKLM_VITAO.md
- orchestrator_config.yaml
- README.md

