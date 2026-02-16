# PROMPT — GERAR AGENDA SEMANAL DE ATENDIMENTOS
## CRM INTELIGENTE VITAO 360 — V11 LIMPO

> **Copie este prompt inteiro e cole no Claude junto com o arquivo CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx + Carteira Mercos atualizada**

---

## CONTEXTO

Sou Leandro, AI Solutions Engineer da VITAO Alimentos. Preciso gerar a AGENDA SEMANAL de atendimentos para a semana de [DD/MM a DD/MM de 2026].

A AGENDA fica na aba AGENDA do CRM V11. Ela contém o roteiro diário de cada consultor — quais clientes contatar, em qual ordem, com qual ação sugerida. Após execução, o consultor preenche o resultado, que é depois transferido para o DRAFT 2 (log permanente).

---

## ARQUIVOS ENVIADOS

1. **CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx** — CRM completo (DRAFT 1 com 502 clientes, DRAFT 2 limpo, CARTEIRA, PROJEÇÃO)
2. **Carteira detalhada de clientes Mercos** — relatório mais recente exportado do Mercos (para DIAS SEM COMPRA atualizado)
3. **(Opcional) Acesso ao E-commerce** — relatório mensal de acessos B2B
4. **(Opcional) Export Deskrio** — tickets WhatsApp recentes

---

## LAYOUT AGENDA — 30 COLUNAS (NÃO ALTERAR ORDEM)

### Colunas de CONTEXTO (pré-preenchidas pelo Claude):

| COL | HEADER | FONTE | DESCRIÇÃO |
|-----|--------|-------|-----------|
| A | 📅 DATA | Gerada | Data do atendimento planejado (dd/mm/aaaa) |
| B | NOME FANTASIA | DRAFT 1 col A | Nome do cliente |
| C | CNPJ | DRAFT 1 col B | 14 dígitos sem pontuação |
| D | UF | DRAFT 1 col D | Estado |
| E | REDE / REGIONAL | DRAFT 1 col I | Rede/franquia |
| F | DIAS SEM COMPRA | DRAFT 1 col L (ou Mercos atualizado) | Dias desde última compra |
| G | SITUAÇÃO | Derivado de F | ATIVO / INAT.REC / INAT.ANT / PROSPECT |
| H | ESTÁGIO FUNIL | Derivado de G | CS/RECOMPRA, ATENÇÃO/SALVAR, PERDA/NUTRIÇÃO |
| I | TIPO CLIENTE | DRAFT 1 col AP (fórmula) | PROSPECT/NOVO/EM DESENV./RECORRENTE/FIDELIZADO |
| J | FASE | Derivado | Fase no pipeline |
| K | 🔥 TEMPERATURA | Derivado | 🔥QUENTE / 🟡MORNO / ❄️FRIO |
| L | 🚦 SINALEIRO | Derivado de F+G | 🟢 / 🟡 / 🔴 / 🟣 |
| M | PRÓX. AÇÃO | Sugerida | Ação recomendada pelo sistema |
| N | TENTATIVA | Calculado | T1, T2, T3... (quantas vezes na semana) |
| O | TIPO ATENDIMENTO | Pré-definido | ATIVO (outbound) |

### Colunas de EXECUÇÃO (preenchidas pelo consultor durante o dia):

| COL | HEADER | VALORES | DESCRIÇÃO |
|-----|--------|---------|-----------|
| P | WHATSAPP | SIM/NÃO | Enviou mensagem WhatsApp? |
| Q | LIGAÇÃO | SIM/NÃO | Fez ligação? |
| R | LIGAÇÃO ATENDIDA | SIM/NÃO | Ligação foi atendida? |
| S | TIPO DO CONTATO | Lista fixa | PROSPECÇÃO/VENDA/PÓS-VENDA/SUPORTE/etc |
| T | RESULTADO | Lista fixa REGRAS | Resultado do atendimento (ver lista abaixo) |
| U | MOTIVO | Lista fixa REGRAS | Motivo quando negativo |
| V | FOLLOW-UP | Data ou "SEM" | Data para recontato |
| W | 💡 AÇÃO SUGERIDA | Texto | Sugestão personalizada |
| X | AÇÃO FUTURA | Texto | Próxima ação a executar |
| Y | AÇÃO DETALHADA | Texto livre | Detalhes do contato |
| Z | MERCOS ATUALIZADO | SIM/NÃO | Registrou no Mercos? |
| AA | NOTA DO DIA | Texto livre | Observações |
| AB | TIPO AÇÃO | Derivado | Classificação da ação |
| AC | TIPO PROBLEMA | Texto | Se houve problema |
| AD | TAREFA/DEMANDA | Texto | Demanda específica |

---

## REGRAS DE GERAÇÃO DA AGENDA

### 1. TERRITÓRIOS (quem atende quem)
```
PRIORIDADE 1: Rede = CIA DA SAUDE ou FITLAND           → JULIO GADRET
PRIORIDADE 2: Rede = Divina Terra, Biomundo,
              Mundo Verde, Vida Leve, Tudo em Grãos     → DAIANE STAVICKI
PRIORIDADE 3: UF in (SC, PR, RS) sem rede              → MANU DITZEL
PRIORIDADE 4: Resto do Brasil                           → LARISSA PADILHA
```

### 2. PRIORIZAÇÃO (ordem de atendimento no dia)
```
NÍVEL 1 — URGÊNCIA (atender PRIMEIRO):
  • 🔥 QUENTE: Acessou e-commerce + itens no carrinho + não comprou
  • EM RISCO: Ativo mas com sinais de churn (dias perto do ciclo médio)
  • FOLLOW-UP vencido: Data de follow-up já passou

NÍVEL 2 — ATIVOS (bloco MANHÃ):
  • ATIVO ordenado por DIAS SEM COMPRA crescente (quem vai vencer primeiro)
  • Priorizar CURVA A > B > C

NÍVEL 3 — INATIVOS RECENTES (bloco MANHÃ):
  • INAT.REC ordenado por DIAS SEM COMPRA crescente
  • Priorizar quem já comprou mais (Nº COMPRAS desc)

NÍVEL 4 — INATIVOS ANTIGOS (bloco TARDE):
  • INAT.ANT ordenado por DIAS SEM COMPRA crescente
  • Priorizar CURVA A > B > C
```

### 3. CAPACIDADE DIÁRIA POR CONSULTOR
```
Máximo: 40 atendimentos/dia
Distribuição sugerida:
  • MANHÃ (8h-12h): 20-25 atendimentos (ATIVOS + INAT.REC)
  • TARDE (13h-17h): 15-20 atendimentos (INAT.ANT + PROSPECTS)
```

### 4. DISTRIBUIÇÃO SEMANAL (5 dias)
```
SEGUNDA a QUINTA: Atendimento normal (40/dia)
SEXTA: Consolidação + follow-ups pendentes (20-30/dia)

Meta semanal por consultor: ~180 atendimentos
Meta semanal equipe (4 consultores): ~720 atendimentos
```

### 5. AÇÃO SUGERIDA (col W) — Personalizar por contexto:
```
ATIVO + DIAS < 30:
  → "CS - Confirmar satisfação último pedido"

ATIVO + DIAS 30-50:
  → "Reposição - Oferecer catálogo atualizado + lançamentos"

ATIVO + DIAS 50-60 (RISCO):
  → "⚠️ URGENTE - Ligar antes de virar inativo"

INAT.REC + DIAS 61-90:
  → "Resgate - Oferecer condição especial de retorno"

INAT.REC + DIAS 91-120:
  → "Salvar - Entender motivo do afastamento"

INAT.ANT + DIAS 121-180:
  → "Reativação - Apresentar novidades e lançamentos"

INAT.ANT + DIAS > 180:
  → "Nutrição - Manter contato leve, enviar catálogo"

PROSPECT:
  → "Prospecção - Primeiro contato, apresentar VITAO"

ACESSO E-COMMERCE (sem compra):
  → "🔥 PRIORIDADE - Cliente acessou B2B, fechar pedido"
```

### 6. ESTÁGIO FUNIL (col H):
```
ATIVO              → CS / RECOMPRA
INAT.REC           → ATENÇÃO / SALVAR
INAT.ANT           → PERDA / NUTRIÇÃO
PROSPECT/LEAD      → PROSPECÇÃO
NOVO               → ONBOARDING
```

### 7. SINALEIRO (col L):
```
PROSPECT/LEAD      → 🟣
NOVO (< 30 dias)   → 🟢
DIAS ≤ 50          → 🟢
DIAS 51-90         → 🟡
DIAS > 90          → 🔴
```

---

## INSERÇÃO NO CRM

### Onde inserir:
- Aba: **AGENDA**
- R1-R2: Título do bloco (não tocar)
- R3-R4: Headers (não tocar)
- **R5 em diante**: Dados da agenda semanal

### Ordenação das linhas:
```
1º Agrupar por CONSULTOR
2º Dentro do consultor, agrupar por DATA (seg→sex)
3º Dentro do dia, ordenar por PRIORIDADE:
   URGÊNCIA > ATIVO > INAT.REC > INAT.ANT > PROSPECT
```

### Colunas de execução (P-AD):
- Deixar **VAZIAS** na geração — consultor preenche durante o dia
- Exceção: W (AÇÃO SUGERIDA) é pré-preenchida com a sugestão

---

## FLUXO SEMANAL COMPLETO

```
┌─────────────────────────────────────────────────────────────────┐
│  SEXTA (preparação)                                             │
│  1. Exportar Carteira Mercos atualizada                         │
│  2. Rodar este prompt com CRM + Carteira                        │
│  3. Claude gera AGENDA para próxima semana                      │
│  4. Validar totais e distribuir para consultores                │
├─────────────────────────────────────────────────────────────────┤
│  SEGUNDA a QUINTA (execução)                                    │
│  1. Consultor abre AGENDA, filtra por seu nome + data           │
│  2. Executa atendimentos na ordem                               │
│  3. Preenche colunas P-AD com resultado real                    │
│  4. Registra no Mercos (W=SIM)                                  │
├─────────────────────────────────────────────────────────────────┤
│  SEXTA (consolidação)                                           │
│  1. Transferir registros executados da AGENDA → DRAFT 2         │
│  2. Rodar próximo prompt de atualização                         │
│  3. DASH atualiza KPIs automaticamente                          │
│  4. CARTEIRA atualiza lookups automaticamente                   │
│  5. Gerar nova AGENDA para semana seguinte                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## TRANSFERÊNCIA AGENDA → DRAFT 2

Após a semana executada, os registros preenchidos da AGENDA (onde T/RESULTADO não é vazio) devem ser copiados para o DRAFT 2. O mapeamento de colunas é:

| AGENDA → | DRAFT 2 |
|----------|---------|
| A (DATA) | A (DATA) |
| — | B (CONSULTOR) → derivar do território |
| B (NOME FANTASIA) | C (NOME FANTASIA) |
| C (CNPJ) | D (CNPJ) |
| D (UF) | E (UF) |
| E (REDE) | F (REDE) |
| G (SITUAÇÃO) | G (SITUAÇÃO) |
| F (DIAS SEM COMPRA) | H (DIAS SEM COMPRA) |
| P (WHATSAPP) | N (WHATSAPP) |
| Q (LIGAÇÃO) | O (LIGAÇÃO) |
| R (LIGAÇÃO ATENDIDA) | P (LIGAÇÃO ATENDIDA) |
| S (TIPO DO CONTATO) | Q (TIPO DO CONTATO) |
| T (RESULTADO) | R (RESULTADO) |
| U (MOTIVO) | S (MOTIVO) |
| Y (AÇÃO DETALHADA) | V (AÇÃO DETALHADA) |
| Z (MERCOS ATUALIZADO) | W (MERCOS ATUALIZADO) |
| AA (NOTA DO DIA) | X (NOTA DO DIA) |
| AC (TIPO PROBLEMA) | AC (TIPO PROBLEMA) |
| AD (TAREFA/DEMANDA) | AD (DEMANDA) |
| O (TIPO ATENDIMENTO) | AE (TIPO ATENDIMENTO) |

---

## VALIDAÇÃO PÓS-GERAÇÃO

```
□ Total de clientes na AGENDA = cobertura esperada (~180/consultor/semana)
□ Todos os CNPJs existem no DRAFT 1
□ Nenhum CNPJ duplicado no MESMO DIA (pode repetir em dias diferentes)
□ Distribuição por consultor equilibrada (±10%)
□ Todos os ATIVOS foram cobertos
□ INAT.REC com follow-up vencido estão no NÍVEL 1
□ Clientes com acesso e-commerce estão marcados como 🔥
□ Ações sugeridas (col W) são personalizadas por contexto
□ PROSPECT nunca no bloco MANHÃ (sempre TARDE)
□ Máximo 40 atendimentos/dia por consultor
```

---

## COMANDO FINAL

Gerar a AGENDA de atendimentos para a semana de [DD/MM a DD/MM de 2026]. Usar DRAFT 1 do CRM V11 como base de clientes (502). Distribuir por consultor conforme territórios. Priorizar por urgência, depois status, depois curva. Pré-preencher ação sugerida personalizada. Inserir na aba AGENDA a partir de R5. Reportar: total de atendimentos gerados, breakdown por consultor, breakdown por dia, e breakdown por tipo (recompra/resgate/reativação/prospecção).
