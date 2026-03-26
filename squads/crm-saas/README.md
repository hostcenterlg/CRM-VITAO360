# Squad CRM-SaaS — CRM VITAO360

Squad de desenvolvimento para a plataforma SaaS do CRM VITAO360.

## Agentes

| ID | Role | Persona | Responsabilidade |
|----|------|---------|-----------------|
| `cs-architect` | Architect | Aria | Design de módulos, API contracts, data modeling |
| `cs-backend` | Backend | Dex | FastAPI endpoints, services, SQLAlchemy models |
| `cs-frontend` | Frontend | Uma | Next.js pages, Mantine components, auth UI |
| `cs-data` | Data | Dara | Pipeline import, CNPJ normalização, cruzamento |
| `cs-qa` | QA | Quinn | Testes, Detector de Mentira 3 níveis, validation |

## Ativação

```
/SQUADS:crm-saas:cs-backend "implementar endpoint X"
/SQUADS:crm-saas:cs-frontend "criar página Y"
/SQUADS:crm-saas:cs-data "integrar fonte Z"
/SQUADS:crm-saas:cs-qa "validar feature W"
/SQUADS:crm-saas:cs-architect "design módulo V"
```

## Workflow

```
cs-architect → cs-data → cs-backend → cs-frontend → cs-qa
                                                      │
                                              PASS → Done
                                              FAIL → Fix loop (max 3)
```

## Projeto

- **Repo**: `C:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360`
- **Remote**: `https://github.com/hostcenterlg/CRM-VITAO360.git`
- **Branch**: `master`
- **Stack**: FastAPI + SQLAlchemy + Next.js 14 + Mantine + SQLite/PostgreSQL
