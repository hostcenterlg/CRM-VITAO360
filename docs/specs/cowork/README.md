# Cowork Specs — Index

Specs e briefings produzidos pelo **Cowork** (revisor/professor externo) — fonte: `OneDrive/Documentos/Claude/Projects/CRM 360/`.

Importados em 29/Abr/2026 para destravar o MASTER_PLAN_v3_REFINADO. Estes arquivos são **input** para implementação — sempre validar contra o estado real do código antes de aceitar como verdade (ver `memory/project_validar_briefings_externos.md`).

## Ponto de entrada

Comece por `BRIEFING_MASTER_VSCODE.md` — sequência completa de fases.

## Arquivos por fase

### Fase 1 — Sidebar (✅ JÁ FEITA)
- `BRIEFING_SIDEBAR_REESTRUTURADA.md` — referência histórica

### Fase 2 — Inbox demo-quality (PRÓXIMA)
- `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md` — 536 linhas, ler INTEIRO antes de implementar
- `vitao-demo-mvp-complete.html` — referência visual do layout 3 colunas

### Fase 3a — DDE Engine + Migrations
- `SPEC_DDE_CASCATA_REAL.md` — cascata P&L 25 linhas em 7 blocos
- `dde_engine.py` — engine Python (consumido em `backend/app/services/`)
- `routes_dde.py` — 5 endpoints FastAPI (consumido em `backend/app/api/`)
- `DDE_MIGRATION_001.sql` — schema base 8 tabelas (converter para Alembic)
- `DDE_MIGRATION_002_CMV.sql` — `produto_custo_comercial` + ALTER (converter para Alembic)
- `GOLDEN_MASTER_REFERENCIA.md` — valores de validação ±0.5% (cliente referência GMR-001)

### Fase 3b — Análise Crítica UI
- `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md` — spec da feature
- `BRIEFING_UI_ABA_ANALISE_CRITICA.md` — briefing UI da aba

## Notas importantes

- Conforme `MASTER_PLAN_v3_REFINADO.md`, os 2 `.sql` serão **convertidos em migrations Alembic** antes de aplicar. Não rode `\i ARQUIVO.sql` direto no Neon.
- O `BRIEFING_MASTER_VSCODE.md` original tinha inconsistências factuais (secrets e arquivos referenciados) — o plano refinado endereçou.
- **Fonte de dados de `produto_custo_comercial`**: Leandro confirmou — vem do **ZSD062 (SAP)**, importação via planilha exportada.
- **Branding/governança**: nome de cliente real **NUNCA** aparece como nome de método/inteligência/calibração. Aplicado 29/Abr/2026 — referências antigas a "Coelho Diniz" (cliente da carteira) foram substituídas por "Cliente Referência (GMR-001)" em todos os specs e código. Ver `memory/project_nomes_clientes_nao_metodos.md`.
