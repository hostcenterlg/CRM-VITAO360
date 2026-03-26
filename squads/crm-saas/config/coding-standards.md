# CRM SaaS Squad — Coding Standards

## Python (Backend)
- Python 3.12+, type hints obrigatórios
- FastAPI com async endpoints
- SQLAlchemy 2.0 (mapped_column, Mapped types)
- Pydantic v2 para schemas
- CNPJ sempre string 14 dígitos: `re.sub(r'\D', '', str(val)).zfill(14)`
- Two-Base: VENDA=R$, LOG=R$0.00
- Commits atômicos: 1 task = 1 commit

## TypeScript (Frontend)
- Next.js 14 App Router, strict mode
- Mantine UI v7 para componentes
- Tema LIGHT exclusivamente
- Fonte Arial, cores padronizadas (status/ABC/sinaleiro)

## Geral
- Idioma do código: inglês
- Idioma dos comentários/docs: português brasileiro
- Fórmulas openpyxl: INGLÊS (IF, VLOOKUP, SUMIF)
- Separador: vírgula (,) nunca ponto-e-vírgula
