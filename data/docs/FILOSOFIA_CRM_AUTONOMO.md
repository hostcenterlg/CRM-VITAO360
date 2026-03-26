# FILOSOFIA DO CRM VITAO360 — Sistema Autonomo Preditivo

**Documento obrigatorio para qualquer dev/coworker/agente que tocar no SaaS.**
**Criado: 25/03/2026 | Autor: @aios-master + Leandro**

---

## PRINCIPIO FUNDAMENTAL

> **O CRM manda. O humano executa.**
>
> O CRM VITAO360 NAO e um sistema passivo onde o consultor decide o que fazer.
> E um sistema AUTONOMO PREDITIVO que DECIDE, PRIORIZA e MANDA.
> O consultor humano APENAS EXECUTA o que o CRM inteligente determina.

---

## O CICLO AUTONOMO DIARIO

```
05:00 BRT — MOTOR RODA SOZINHO (cron/job scheduled):

  1. SITUACAO calculada automaticamente
     → dias_sem_compra vs thresholds (<=50 ATIVO, 51-60 EM RISCO, 61-90 INAT.REC, >90 INAT.ANT)

  2. MOTOR aplica 92 regras (SITUACAO|RESULTADO → 9 outputs)
     → gera ESTAGIO FUNIL, FASE, TEMPERATURA, ACAO FUTURA, FOLLOW-UP

  3. SCORE calcula 6 fatores ponderados (0-100)
     → Urgencia 30% + Valor 25% + Follow-up 20% + Sinal 15% + Tentativa 5% + Situacao 5%

  4. SINALEIRO calcula saude (dias / ciclo medio)
     → VERDE, AMARELO, VERMELHO, ROXO

  5. PRIORIDADE v2 classifica P1-P7
     → P1 NAMORO NOVO, P2 NEGOCIACAO, P3 PROBLEMA, P4 MOMENTO OURO...

  6. AGENDA gera 40-60 clientes PRIORIZADOS por consultor
     → Score desc, com P1/P3 pulando fila

  7. META BALANCE verifica cobertura
     → Se P2-P5 < 80% da meta mensal, PROSPECCAO ganha +20 bonus

07:00 BRT — CONSULTOR ABRE O CRM:

  "Bom dia Larissa. Sua agenda tem 47 atendimentos hoje."

  Para CADA cliente na agenda, o CRM JA DIZ:

  ┌─────────────────────────────────────────────────────────┐
  │ #1 — DISTRIBUIDORA LIGEIRO (CNPJ 04.067.573/0001-93)   │
  │                                                         │
  │ QUEM:     Distribuidora Ligeiro — RJ                    │
  │ POR QUE:  Score 87 | P2 NEGOCIACAO | Sinaleiro VERMELHO │
  │           45 dias sem compra | Ciclo medio 23 dias      │
  │ O QUE:    "Confirmar orcamento enviado, fechar venda"   │
  │ COMO:     Tipo Contato: NEGOCIACAO | Via: Ligacao       │
  │ QUANDO:   Follow-up: AMANHA (1 dia)                     │
  │ TENTATIVA: T2 (segunda tentativa — mudar horario)       │
  └─────────────────────────────────────────────────────────┘

  Consultor NAO PENSA. Consultor EXECUTA:
    1. Liga para o cliente
    2. Registra RESULTADO no dropdown (14 opcoes)
    3. Motor roda de novo INSTANTANEAMENTE
    4. Proximo follow-up e acao futura ja estao calculados
    5. Passa para o proximo da lista

17:00 BRT — FIM DO DIA:

  Consultor completou 42 de 47 atendimentos.
  Cada resultado registrado JA alimentou o Motor.
  Agenda de AMANHA ja esta sendo recalculada automaticamente.
```

---

## O QUE O CONSULTOR VE vs O QUE O MOTOR FAZ

### O consultor VE (interface simples):
- Lista de clientes ordenada (quem ligar primeiro)
- Nome, Score, Prioridade (badge colorido)
- Acao sugerida ("Confirmar orcamento", "Fazer CS", "2a tentativa via WPP")
- Sinaleiro (cor verde/amarelo/vermelho/roxo)
- Formulario de registro (dropdown + texto)

### O consultor NAO VE (motor oculto):
- 92 regras do Motor
- 6 pesos do Score
- Calculo do Sinaleiro (LET com ratio)
- Meta Balance (+20 bonus)
- Logica de Tentativas T1-T4
- XLOOKUP que conecta LOG ao Motor
- 18 tabelas de REGRAS
- Two-Base Architecture
- 14 estagios do Funil com fluxo sequencial

### Principio de design:
**Complexidade ZERO para o usuario. Inteligencia TOTAL no backend.**

---

## OS 4 PILARES DA INTELIGENCIA

### Pilar 1: ANTECIPACAO
O CRM NAO espera o consultor pensar. Ele ANTECIPA:
- Qual cliente vai esfriar (Sinaleiro AMARELO → agir ANTES de virar VERMELHO)
- Qual follow-up esta vencendo (URGENCIA 30% do Score)
- Qual inat.rec esta prestes a virar inat.ant (SALVAMENTO antes dos 90 dias)

### Pilar 2: PRESCRICAO
O CRM NAO sugere. Ele PRESCREVE:
- ACAO FUTURA: texto exato do que fazer ("Confirmar faturamento e expedicao")
- TIPO CONTATO: classificacao do contato (Negociacao, Follow-up, Pos-venda)
- FOLLOW-UP: data exata do proximo contato (TODAY() + dias)
- TENTATIVA: qual tentativa e o canal (T2 = Ligacao, mudar horario)

### Pilar 3: PRIORIZACAO
O CRM NAO deixa o consultor escolher a ordem. Ele PRIORIZA:
- P1 NAMORO NOVO pula fila (cliente quente pos-venda, nao pode esfriar)
- P3 PROBLEMA pula fila (suporte aberto, resolver urgente)
- Score 87 vem antes de Score 45 (matematicamente calculado)
- Desempate: ABC > Ticket > Maturidade > FU vencido

### Pilar 4: AUTO-AJUSTE
O CRM se auto-corrige em tempo real:
- Consultor registra resultado → Motor recalcula instantaneamente
- Cliente comprou → RESET tentativas, volta para POS-VENDA D+4
- Cliente nao respondeu 4x → NUTRICAO (sai da agenda, campanha mensal)
- Meta nao coberta → PROSPECCAO ganha bonus (+20 score)
- Sinaleiro muda → prioridade ajusta automaticamente

---

## MAPA: ABA EXCEL → TELA SAAS → PILARES

| Aba Excel | Tela SaaS | Pilar Ativo |
|-----------|-----------|-------------|
| AGENDA | `/agenda` — lista priorizada | PRIORIZACAO + PRESCRICAO |
| CARTEIRA | `/clientes` — tabela + detalhe | ANTECIPACAO (sinaleiro, score) |
| LARISSA/MANU/... | `/atendimentos` — registro | AUTO-AJUSTE (Motor roda ao registrar) |
| SINALEIRO | `/sinaleiro` — saude | ANTECIPACAO (ratio dias/ciclo) |
| DASHBOARD | `/dashboard` — KPIs CEO | PRIORIZACAO (distribuicao P1-P7) |
| PROJECAO | `/projecao` — metas | ANTECIPACAO (gap, meta balance) |
| MOTOR DE REGRAS | `/admin/motor` — config | PRESCRICAO (92 regras, 9 outputs) |

---

## ANTI-PATTERNS (O QUE O SAAS NAO PODE SER)

| Anti-Pattern | Por Que E Errado |
|-------------|-----------------|
| CRM passivo (consultor decide ordem) | Perde 80% da inteligencia. Manu com 165 clientes nao consegue priorizar sozinha |
| Dashboard sem acao (so mostra graficos) | Informacao sem prescricao = paralisia. O CRM deve MANDAR, nao MOSTRAR |
| Formulario complexo (20 campos) | Consultor faz 40-60 atendimentos/dia. Precisa de dropdown + texto. Nada mais |
| Score visivel com explicacao | Consultor nao precisa saber POR QUE Score = 87. So precisa saber QUE e #1 da lista |
| Edicao de regras pelo consultor | Motor e do gestor (L3). Consultor executa, nao configura |
| Notificacao sem acao | "Cliente X esfriou" sem dizer O QUE FAZER e inutil. Sempre: notificacao + acao prescrita |

---

## METRICAS DE SUCESSO DO CRM AUTONOMO

| Metrica | Situacao Atual (Excel) | Meta SaaS |
|---------|----------------------|-----------|
| Atendimentos/dia/consultor | ~15-20 (manual) | 40-60 (agenda automatica) |
| % Agenda completada | Nao medido | >= 80% |
| Tempo por atendimento | ~5-10 min | ~2-3 min (Motor pre-preenche) |
| Churn mensal | ~30 clientes (18%) | < 15 clientes (<10%) |
| Taxa recompra | 21.9% | >= 35% |
| Cobertura carteira | Parcial (consultor escolhe) | 100% (Motor cobre TODOS) |
| Follow-ups vencidos | Nao rastreado | Zero (Motor alerta automaticamente) |

---

*Este documento e LEI para o UX Designer, Frontend Developer, e qualquer agente.*
*Cada tela deve perguntar: "Isso ajuda o consultor a EXECUTAR mais rapido?"*
*Se a resposta for NAO, a tela esta errada.*
