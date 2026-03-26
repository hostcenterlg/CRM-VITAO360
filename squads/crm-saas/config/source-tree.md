# CRM SaaS Squad — Source Tree

```
CRM-VITAO360/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # Dependency injection
│   │   │   ├── routes_agenda.py     # Agenda endpoints
│   │   │   ├── routes_atendimentos.py
│   │   │   ├── routes_auth.py       # JWT login/register
│   │   │   ├── routes_clientes.py   # CRUD clientes
│   │   │   ├── routes_dashboard.py  # KPIs e métricas
│   │   │   ├── routes_projecao.py   # Projeção vs meta
│   │   │   ├── routes_sinaleiro.py  # Sinaleiro saúde
│   │   │   └── routes_vendas.py     # Vendas CRUD
│   │   ├── models/                  # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── services/                # Business logic
│   │   ├── config.py                # App configuration
│   │   ├── database.py              # DB connection
│   │   ├── main.py                  # FastAPI app
│   │   └── security.py              # JWT + bcrypt
│   ├── tests/                       # pytest
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                     # Next.js pages
│       │   ├── login/
│       │   ├── carteira/
│       │   ├── agenda/
│       │   └── projecao/
│       ├── components/              # Mantine components
│       ├── contexts/                # React contexts
│       └── lib/                     # API + auth utils
├── scripts/                         # Motor Python (v2.0)
├── data/                            # Excel sources + output
└── squads/crm-saas/                 # Esta squad
```
