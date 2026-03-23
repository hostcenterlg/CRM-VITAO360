---
name: ux-visual
description: "Skill do @ux — Tema LIGHT, formatação Excel, cores status/ABC/sinaleiro, dashboard HTML, fontes Arial."
allowed-tools: Read Write Edit Glob Grep Bash(python:*) Bash(ls:*)
argument-hint: [*format|*dashboard|*theme|*export|*colors]
---

# @ux — Visual e Formatação CRM VITAO360

## Quick Commands

| Comando | Ação |
|---------|------|
| `*format` | Aplicar formatação padrão ao Excel |
| `*dashboard` | Criar/atualizar dashboard (HTML ou terminal) |
| `*theme` | Aplicar tema LIGHT completo |
| `*export` | Preparar export visual (cores, larguras, freeze) |
| `*colors` | Verificar paleta de cores contra padrão |

## Tema LIGHT (OBRIGATÓRIO — NUNCA dark mode)

### Fontes
- Dados: Arial 9pt
- Headers: Arial 10pt Bold
- Títulos: Arial 11pt Bold

### Cores de Status
| Status | Cor Fundo | Cor Texto | Hex |
|--------|-----------|-----------|-----|
| ATIVO | Verde | Branco | #00B050 |
| EM RISCO | Amarelo | Preto | #FFC000 |
| INAT.REC | Amarelo escuro | Branco | #FFC000 |
| INAT.ANT | Vermelho | Branco | #FF0000 |
| PROSPECT | Roxo | Branco | #7030A0 |
| LEAD | Roxo claro | Preto | #9966FF |
| NOVO | Verde claro | Preto | #92D050 |

### Cores ABC
| Curva | Cor | Hex |
|-------|-----|-----|
| A | Verde | #00B050 |
| B | Amarelo | #FFFF00 |
| C | Laranja | #FFC000 |

### Cores Sinaleiro
| Cor | Significado | Hex |
|-----|-------------|-----|
| ROXO | Sem histórico | #7030A0 |
| VERDE | Saudável | #00B050 |
| AMARELO | Atenção | #FFFF00 |
| LARANJA | Alerta | #FFC000 |
| VERMELHO | Crítico | #FF0000 |

### Cores Temperatura
| Temperatura | Cor | Hex |
|-------------|-----|-----|
| QUENTE | Vermelho forte | #FF0000 |
| MORNO | Laranja | #FFC000 |
| FRIO | Azul claro | #5B9BD5 |
| CRÍTICO | Vermelho escuro | #C00000 |
| PERDIDO | Cinza | #A6A6A6 |

### Cores Prioridade
| Prioridade | Símbolo | Cor |
|------------|---------|-----|
| CRÍTICO | Vermelho | #FF0000 |
| URGENTE | Laranja | #FFC000 |
| ALTO | Amarelo | #FFFF00 |
| MÉDIO | Verde | #00B050 |
| BAIXO | Cinza | #D9D9D9 |

## Layout Excel

### Freeze Panes
- CARTEIRA: freeze em BX4 (dados rolam, headers fixos)
- AGENDA: freeze na linha 2
- SINALEIRO: freeze na linha 3

### Auto Filter
- Todas as abas de dados devem ter auto_filter ativo
- Range: primeira até última coluna de dados

### Column Widths
- CNPJ: 18
- Nome Fantasia: 30
- UF: 5
- Cidade: 15
- Consultor: 12
- Valores R$: 12 (formato #,##0.00)
- Datas: 12 (formato dd/mm/yyyy)

## Dashboard Terminal (v2.0)

```
╔══════════════════════════════════════════════════╗
║  CRM VITAO360 — DASHBOARD                        ║
╚══════════════════════════════════════════════════╝

 FATURAMENTO         CARTEIRA           OPERACIONAL
 ───────────         ────────           ───────────
 2025: R$2.091M      Ativos: XXX        Hoje: XX atend.
 2026: R$459K Q1     Em Risco: XX       Mês: XXX
 Meta: R$3.377M      Inativos: XXX      Conversão: X.X%

 POR CONSULTOR
 ─────────────
 LARISSA  ████████████ XX%  XX clientes
 MANU     ████████░░░░ XX%  XX clientes
 JULIO    ██████░░░░░░ XX%  XX clientes
 DAIANE   █████░░░░░░░ XX%  XX clientes
```

## Regras Visuais

1. NUNCA dark mode — LIGHT exclusivamente
2. Fonte Arial SEMPRE (não Calibri, não Times)
3. Cores consistentes com tabelas acima
4. Sem emojis em dados (exceto SINALEIRO que usa emojis como indicadores)
5. Barras de progresso para % alcançado
6. Formatação condicional: cores automáticas por status/ABC/sinaleiro
