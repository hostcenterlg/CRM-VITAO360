---
name: dev-motor
description: "Skill do @dev — Motor de Regras, Score, Sinaleiro, Agenda, build Excel. Ativa quando implementar qualquer lógica do CRM VITAO360."
allowed-tools: Read Write Edit Glob Grep Bash(python:*) Bash(pip:*) Bash(git:add) Bash(git:commit) Bash(git:status) Bash(git:diff) Bash(ls:*) Bash(mkdir:*)
argument-hint: [*motor|*score|*sinaleiro|*agenda|*build|*export|*implement|*fix]
---

# @dev — Motor Operacional CRM VITAO360

## Quick Commands

| Comando | Ação |
|---------|------|
| `*motor` | Implementar/testar Motor de Regras (92 combinações) |
| `*score` | Implementar/testar Score Ranking (6 fatores) |
| `*sinaleiro` | Implementar/testar Sinaleiro (saúde cliente) |
| `*agenda` | Implementar/testar Agenda Inteligente (40-60/consultor) |
| `*build` | Build completo: import → motor → score → sinaleiro → agenda → export |
| `*export` | Exportar base processada para xlsx |
| `*implement` | Implementar feature/script específico |
| `*fix` | Corrigir bug |

## Motor de Regras (92 Combinações)

### Input
- SITUAÇÃO: ATIVO, EM RISCO, INAT.REC, INAT.ANT, PROSPECT, LEAD, NOVO
- RESULTADO: 14 tipos (VENDA/PEDIDO, ORÇAMENTO, PÓS-VENDA, CS, RELACIONAMENTO, FOLLOW UP 7/15, EM ATENDIMENTO, SUPORTE, NÃO ATENDE, NÃO RESPONDE, RECUSOU LIGAÇÃO, CADASTRO, PERDA/FECHOU LOJA)

### Output (9 dimensões)
Estágio Funil, Fase, Tipo Contato, Ação Futura, Temperatura, Follow-up Racional, Grupo Dash, Tipo Ação, Chave

### Regra SITUAÇÃO (calcular)
```python
def calcular_situacao(n_compras, dias_sem_compra):
    if not n_compras or n_compras == 0: return "PROSPECT"
    if not dias_sem_compra or dias_sem_compra == 0: return "ATIVO"
    if dias_sem_compra <= 50: return "ATIVO"
    if dias_sem_compra <= 60: return "EM RISCO"
    if dias_sem_compra <= 90: return "INAT.REC"
    return "INAT.ANT"
```

### Referência completa: `data/docs/MOTOR_COMPLETO_CRM_VITAO360.md`

## Score Ranking (6 Fatores = 100%)

| Fator | Peso | Cálculo |
|-------|------|---------|
| URGÊNCIA | 30% | INAT.ANT=100, INAT.REC=90, EM RISCO=70, ATIVO=40, NOVO=30, PROSPECT/LEAD=10 |
| VALOR | 25% | A+FIDELIZADO=100, A=80, B+MADURO=70, B=50, C=30, sem ABC=10 |
| FOLLOW-UP | 20% | >30d=100, 15-30=75, 7-15=50, <7=25, sem FU=50 |
| SINAL | 15% | CRÍTICO=90, QUENTE+ecomm=100, QUENTE=80, MORNO+ecomm=70, MORNO=50, FRIO=20 |
| TENTATIVA | 5% | T4+=100, T3=75, T2=50, T1=25, sem=10 |
| SITUAÇÃO | 5% | EM RISCO=80, ATIVO=40, INAT=20, outros=10 |

## Sinaleiro (Saúde)

```python
def calcular_sinaleiro(situacao, dias_sem_compra, ciclo_medio):
    if situacao in ("PROSPECT", "LEAD"): return "ROXO"
    if situacao == "NOVO": return "VERDE"
    if not dias_sem_compra or not ciclo_medio: return "ROXO"
    ratio = dias_sem_compra / ciclo_medio
    if ratio <= 0.5: return "VERDE"
    if ratio <= 1.0: return "AMARELO"
    if ratio <= 1.5: return "LARANJA"
    return "VERMELHO"
```

## Pipeline Completo

```
import xlsx → normalizar CNPJ → DE-PARA vendedores
    → calcular SITUAÇÃO → aplicar MOTOR (92 regras)
    → calcular SCORE (6 fatores) → gerar P1-P7
    → calcular SINALEIRO → gerar CADÊNCIA
    → gerar AGENDA (40-60/consultor, Score desc)
    → exportar xlsx
```

## Regras INVIOLÁVEIS

- Two-Base: VENDA=R$, LOG=R$0.00 — NUNCA misturar
- CNPJ: `re.sub(r'\D', '', str(val)).zfill(14)` — SEMPRE string
- Fórmulas openpyxl: INGLÊS (IF, VLOOKUP, SUMIF), vírgula
- openpyxl NÃO toca slicers (XML Surgery)
- 558 registros ALUCINAÇÃO = NUNCA integrar
- Commit atômico: 1 task = 1 commit
- verify.py --all ANTES de done

## Thresholds

| Métrica | Mínimo | Bloqueante |
|---------|--------|------------|
| Motor coberto | 92/92 combinações | < 92 |
| Score calculado | 100% clientes | < 95% |
| Fórmulas com erro | 0 | > 0 |
| Two-Base violações | 0 | > 0 |
| CNPJ como float | 0 | > 0 |
| Testes passando | 100% | < 100% |
