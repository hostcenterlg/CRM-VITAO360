---
description: "Professor, guardião e motor operacional do CRM VITAO360. Ensina regras, metodologias, enforcement gates, pipelines, thresholds e lições aprendidas. Use SEMPRE que trabalhar no CRM VITAO360."
allowed-tools: Read Write Edit Glob Grep Bash(python:*) Bash(git:*) Bash(ls:*) Bash(mkdir:*)
argument-hint: [command] [args]
---

# CRM VITAO360 — Professor, Guardião e Motor Operacional

## Ativação
Use SEMPRE que trabalhar no CRM VITAO360 — scripts, Excel, dados, fórmulas, motor, integrações.

## Quick Commands

| Comando | Ação | Agente |
|---------|------|--------|
| `*motor` | Aplicar Motor de Regras (92 combinações) | @dev |
| `*score` | Calcular Score Ranking (6 fatores) | @dev |
| `*agenda` | Gerar Agenda Inteligente (40-60/consultor) | @dev |
| `*sinaleiro` | Calcular Sinaleiro (saúde do cliente) | @dev |
| `*projecao` | Calcular Projeção vs Meta SAP | @data-engineer |
| `*import` | Importar dados xlsx (Mercos/SAP/Deskrio) | @data-engineer |
| `*audit` | Auditoria completa (verify.py + 3 níveis) | @qa |
| `*validate` | Validar Two-Base + CNPJ + fórmulas | @qa |
| `*export` | Exportar CRM atualizado para xlsx | @dev |
| `*status` | Status do projeto completo | @aios-master |
| `*dashboard` | Gerar dashboard HTML/terminal | @ux |

## Pipeline Operacional

```
IMPORT (fontes) → NORMALIZAR (CNPJ) → CRUZAR (merge) → MOTOR (92 regras)
    → SCORE (6 fatores) → SINALEIRO (saúde) → AGENDA (priorizada)
    → PROJEÇÃO (meta) → EXPORT (xlsx) → VALIDATE (3 níveis)
```

## Thresholds de Qualidade

| Métrica | Mínimo | Bloqueante |
|---------|--------|------------|
| Fórmulas com erro | 0 | > 0 |
| Two-Base violações | 0 | > 0 |
| CNPJ como float | 0 | > 0 |
| Fórmulas em português | 0 | > 0 |
| Faturamento vs R$2.091.000 | ±0.5% | > 0.5% |
| Dados ALUCINAÇÃO integrados | 0 | > 0 |
| Coverage clientes | >90% | < 80% |
| Coverage faturamento | >95% | < 90% |
| Motor regras coberto | 92/92 | < 92 |
| Score calculado | 100% clientes | < 95% |

## Motor de Regras (92 Combinações)

**Input**: SITUAÇÃO + RESULTADO
**Output**: 9 dimensões (Estágio Funil, Fase, Tipo Contato, Ação Futura, Temperatura, Follow-up, Grupo Dash, Tipo Ação, Chave)

### SITUAÇÃO (7 estados)
- ATIVO: ≤50 dias sem compra
- EM RISCO: 51-60 dias
- INAT.REC: 61-90 dias
- INAT.ANT: >90 dias
- PROSPECT: sem compra
- LEAD: lead qualificado
- NOVO: primeiro pedido

### RESULTADO (14 tipos)
VENDA/PEDIDO, ORÇAMENTO, PÓS-VENDA, CS, RELACIONAMENTO, FOLLOW UP 7, FOLLOW UP 15, EM ATENDIMENTO, SUPORTE, NÃO ATENDE, NÃO RESPONDE, RECUSOU LIGAÇÃO, CADASTRO, PERDA/FECHOU LOJA

### Documentação completa: `data/docs/MOTOR_COMPLETO_CRM_VITAO360.md`

## Score Ranking (6 Fatores = 100%)

| Fator | Peso | Fonte |
|-------|------|-------|
| URGÊNCIA | 30% | Dias sem compra vs ciclo |
| VALOR | 25% | Curva ABC + Tipo Cliente |
| FOLLOW-UP | 20% | Dias desde último FU |
| SINAL | 15% | Temperatura + ecommerce |
| TENTATIVA | 5% | Protocolo T1-T4+ |
| SITUAÇÃO | 5% | Status simplificado |

## Pirâmide P1-P7
- P1 NAMORO NOVO (novo em pós-venda)
- P2 NEGOCIAÇÃO ATIVA (orçamento aberto)
- P3 PROBLEMA (suporte/RNC)
- P4 CULTIVAR (ativo em manutenção)
- P5 CONQUISTAR (prospect/lead)
- P6 RECUPERAR (inativo)
- P7 NUTRIÇÃO (perda, passivo)

## Regras Invioláveis (12)

### Two-Base Architecture (SAGRADA)
- VENDA = tem valor R$
- LOG = R$ 0.00 SEMPRE
- Misturar = inflação de 742%

### CNPJ = Chave Primária
- 14 dígitos, string, zero-padded
- `re.sub(r'\D', '', str(val)).zfill(14)`
- NUNCA float/int

### 46 Colunas CARTEIRA = IMUTÁVEIS
- Blueprint v2 expande para 81 via grupos [+]

### Fórmulas openpyxl em INGLÊS
- IF, VLOOKUP, SUMIF, COUNTIF
- Separador: vírgula (,)

### Faturamento Baseline
- 2025: R$ 2.091.000 (PAINEL CEO auditado — 68 arquivos)
- 2026: R$ 3.377.120 projetado (+69%)
- Q1 2026 real: R$ 459.465

### 558 Registros ALUCINAÇÃO = NUNCA integrar
- Classificação 3-tier: REAL / SINTÉTICO / ALUCINAÇÃO

### Mercos MENTE nos nomes de relatório
- SEMPRE verificar linhas 6-7 (Data Inicial / Data Final)

## DE-PARA Vendedores
- MANU: Manu, Manu Vitao, Manu Ditzel → MANU
- LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo → LARISSA
- DAIANE: Daiane, Central Daiane, Daiane Vitao → DAIANE
- JULIO: Julio, Julio Gadret → JULIO
- LEGADO: Bruno Gretter, Jeferson Vitao, Patric, Gabriel, Sergio, Ive, Ana → LEGADO

## Equipe 2026 (Atualizado)
- LARISSA: Brasil Interior, ATIVA, 22 novos/mês
- JULIO: Cia Saúde + Fitland, ATIVO, 22 novos/mês
- DAIANE: Gerente Redes + Food Channel, NOVA ATRIB., 8 redes/mês
- MANU: LICENÇA MATERNIDADE Q2/2026 — 165 clientes descobertos
- NOVA REP: Contratar Q2, substituir Manu (SC+PR+RS)
- PÓS-VENDA/CS: Contratar Q3, churn 75%→50%

## Métricas Chave (2025 Real)
- Churn: 80% (8 de 10 não recompram)
- 57% dos clientes compraram 1x só
- LTV: R$ 2.792
- CAC: R$ 433
- Funil: 22 contatos/dia → 1 fechamento (4.5% conversão)

## Fontes de Dados
| Sistema | Dados | Prioridade |
|---------|-------|------------|
| SAP | Vendas, metas, cadastro | PRIMÁRIO |
| Mercos | Carteira, vendas, ABC, ecommerce | COMPLEMENTO |
| Deskrio | WhatsApp (15.468 contatos, API aberta) | COMPLEMENTO |
| Sales Hunter | Prospecção | COMPLEMENTO |

## Documentação Obrigatória
1. BACKUP_DOCUMENTACAO_ANTIGA.md
2. BRIEFING-COMPLETO.md
3. INTELIGENCIA_NEGOCIO_CRM360.md
4. data/docs/MOTOR_COMPLETO_CRM_VITAO360.md
5. data/docs/BLUEPRINT_SKILLS_SAAS.md

## Verificação (Detector de Mentira)
3 níveis OBRIGATÓRIOS antes de "done":
1. EXISTÊNCIA — artefato existe e não está vazio
2. SUBSTÂNCIA — implementação real, não stub/placeholder
3. CONEXÃO — integrado com resto do sistema

Regra completa: `.claude/rules/detector-de-mentira.md`
