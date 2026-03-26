# DIVISÃO DE TERRITÓRIO — Cowork vs VSCode

## REGRA CENTRAL
**UM Claude por vez no código.** Não existe trabalho paralelo no mesmo repo.

## COWORK (Claude Desktop / Cowork Mode)
### FAZ:
- Análise, raio-x, diagnóstico
- Documentação (docs/, BRIEFING, INTELIGENCIA, etc.)
- Planejamento e estratégia (PRD, roadmap, specs)
- Dashboards HTML de apresentação (fora do repo, em /CRM 360/)
- Planilhas Excel (análise, extração, painéis CEO)
- Pesquisa e inteligência de negócio

### NÃO FAZ:
- Backend (FastAPI, routers, models, services)
- Frontend (Next.js, components, pages)
- Scripts de pipeline (scripts/*.py que processam dados)
- Migrations de banco de dados
- Testes unitários

## VSCODE (Claude Code)
### FAZ:
- Backend Python (backend/**)
- Frontend Next.js (frontend/**)
- Scripts de automação (scripts/*.py)
- Banco de dados (models, migrations, seeds)
- Testes (tests/**)
- Git operations complexas (rebase, merge, branch)

### NÃO FAZ:
- Documentação estratégica
- Análise de planilhas Excel
- Dashboards de apresentação
- PRD e specs de produto

## ZONA COMPARTILHADA (CUIDADO)
Estes arquivos podem ser tocados por ambos — **nunca ao mesmo tempo**:
- `.claude/CLAUDE.md` — regras do projeto
- `.claude/settings.json` — configuração
- `data/docs/*` — documentação técnica
- `data/intelligence/*` — JSONs de inteligência

## PROTOCOLO DE HANDOFF
1. Cowork termina análise → commita → avisa Leandro "pronto, pode abrir VSCode"
2. VSCode implementa → commita → avisa Leandro "pronto, pode voltar pro Cowork"
3. NUNCA os dois abertos editando o repo ao mesmo tempo

## SE CONFLITAR
1. `git stash` no que tem menos mudanças
2. `git pull` / merge do outro
3. `git stash pop` e resolver conflitos manualmente
