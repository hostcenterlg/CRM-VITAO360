# Agent Authority — CRM VITAO360

## Delegation Matrix

### @devops — EXCLUSIVE Authority
| Operation | Exclusive? |
|-----------|-----------|
| `git push` / `git push --force` | YES |
| `gh pr create` / `gh pr merge` | YES |
| Release management | YES |

### @pm — Product Management
| Operation | Exclusive? |
|-----------|-----------|
| Requirements gathering | YES |
| Epic/story creation | YES |
| Priorização de entregas | YES |

### @dev — Implementation
| Allowed | Blocked |
|---------|---------|
| `git add`, `git commit`, `git status` | `git push` → @devops |
| Scripts Python (openpyxl, pandas) | Mudar 46 colunas → L3 |
| Fórmulas Excel (em INGLÊS) | Two-Base alteração → L3 |

### @data-engineer — Dados
| Owns | Does NOT Own |
|------|-------------|
| Cruzamento Mercos/SAP/Deskrio | Estrutura de abas |
| CNPJ normalization | Git operations |
| Validação de faturamento | UI/formatação |

### @qa — Quality Assurance
| Owns |
|------|
| Validação pós-build (0 erros fórmula) |
| Two-Base Architecture check |
| Faturamento = R$ 2.091.000 |
| CNPJ duplicatas check |
| 14 abas presentes check |

### @analyst — Pesquisa
| Owns |
|------|
| Análise de dados Mercos/SAP |
| Regras de negócio CRM |
| Inteligência comercial |

### @architect — Design
| Owns |
|------|
| Estrutura de abas (com aprovação L3) |
| Blueprint v2 (81 colunas) |
| XML Surgery para slicers |

### @ux — Interface
| Owns |
|------|
| Formatação Excel (cores, fontes) |
| Dashboard HTML |
| Tema LIGHT (NUNCA dark) |

## Escalation
1. Agent não consegue → Escalar para Leandro
2. Quality gate falha → Voltar para @dev
3. Two-Base violada → BLOQUEAR tudo
