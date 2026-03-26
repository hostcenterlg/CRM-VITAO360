---
name: qa-validacao
description: "Skill do @qa — Detector de Mentira 3 níveis, validação Two-Base, CNPJ, fórmulas, faturamento, classificação 3-tier."
allowed-tools: Read Glob Grep Bash(python:*) Bash(git:status) Bash(git:diff) Bash(git:log) Bash(ls:*)
argument-hint: [*verify|*audit|*two-base|*cnpj|*formulas|*gate|*compare|*mentira]
---

# @qa — Quality Assurance CRM VITAO360

## Quick Commands

| Comando | Ação |
|---------|------|
| `*verify` | Rodar `python scripts/verify.py --all` |
| `*audit` | Auditoria completa (3 níveis + thresholds) |
| `*two-base` | Verificar Two-Base Architecture |
| `*cnpj` | Verificar normalização CNPJ |
| `*formulas` | Verificar fórmulas em inglês |
| `*gate` | Quality gate final (GO/NO-GO) |
| `*compare` | Comparar duas versões |
| `*mentira` | Rodar Detector de Mentira completo |

## Detector de Mentira — 3 Níveis

### NÍVEL 1 — EXISTÊNCIA
- Arquivo existe no path declarado?
- Não está vazio (>0 bytes)?
- Formato correto?

### NÍVEL 2 — SUBSTÂNCIA (Anti-Stub)
Patterns de MENTIRA:
- TODO, FIXME, PLACEHOLDER, "coming soon"
- `return None`, `return {}`, `pass`, `raise NotImplementedError`
- "teste", "exemplo", "dummy", "fake", "mock"
- CNPJ genérico (12345678000100, 00000000000000)
- R$ em registro LOG (Two-Base violada)
- R$ 0.00 em registro VENDA (Two-Base violada)

### NÍVEL 3 — CONEXÃO (Wired)
- Fórmulas referenciam abas que existem?
- INDEX-MATCH bate com range real?
- Import de módulos que existem?
- Output consumido por próximo script?

## Classificação 3-Tier

| Tier | Critério | Ação |
|------|----------|------|
| REAL | Rastreável a Mercos/SAP/Deskrio | OK |
| SINTÉTICO | Derivado de REAL por fórmula | OK com flag |
| ALUCINAÇÃO | ChatGPT fabricou, sem fonte | **DELETAR** |

**558 registros ALUCINAÇÃO catalogados — NUNCA integrar**

## Quality Gate Checklist

- [ ] 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?)
- [ ] Two-Base Architecture respeitada (VENDA=R$, LOG=R$0.00)
- [ ] Faturamento = R$ 2.091.000 (±0.5%)
- [ ] CNPJ sem duplicatas, todos 14 dígitos string
- [ ] Fórmulas em inglês com separador vírgula
- [ ] Nenhum dado ALUCINAÇÃO integrado
- [ ] Motor 92/92 combinações cobertas
- [ ] Score v2 calculado para 100% dos clientes (6 fatores: URGENCIA 30%, VALOR 25%, FOLLOWUP 20%, SINAL 15%, TENTATIVA 5%, SITUACAO 5%)
- [ ] Detector de Mentira 3 níveis PASS

## Thresholds

| Métrica | Mínimo | Bloqueante |
|---------|--------|------------|
| Fórmulas com erro | 0 | > 0 |
| Two-Base violações | 0 | > 0 |
| CNPJ como float | 0 | > 0 |
| Fórmulas em português | 0 | > 0 |
| Faturamento vs R$2.091.000 | ±0.5% | > 0.5% |
| ALUCINAÇÃO integrados | 0 | > 0 |
| Coverage clientes | >90% | < 80% |
| Motor coberto | 92/92 | < 92 |
| Score calculado | 100% | < 95% |
| Nível 1 (Existência) | 100% | < 100% |
| Nível 2 (Substância) | 100% | < 100% |
| Nível 3 (Conexão) | 100% | < 95% |

## Regra Cardinal

**NENHUM trabalho é "done" sem passar pelo @qa.**
Antes de declarar "pronto/done/OK/completo":
1. Rodar `python scripts/verify.py --all`
2. Aplicar Detector de Mentira 3 níveis
3. Validar thresholds
4. Declarar: "Verificação: N1 OK, N2 OK, N3 OK. Thresholds: X/Y OK."
