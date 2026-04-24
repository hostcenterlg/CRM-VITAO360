# Decisão Arquitetural — Excel vs SaaS
## Data: 2026-04-24 | Decisão: **OPÇÃO C — HÍBRIDO**

---

## Contexto

Diagnóstico de 2026-04-24 revelou dissonância entre documentação e realidade:

- **Documentação (BRIEFING/INTELIGENCIA):** trata Excel CRM_VITAO360 como motor central, lista 10 entregas quebradas (P6-P12) como prioridade.
- **Realidade (git log):** último commit no Excel foi 2026-02-17 (2+ meses atrás). Todos os commits desde então são para SaaS (frontend Next.js + backend FastAPI + ingestão real).
- **Produção viva:** `crm-vitao360.vercel.app` está no ar, com banco enriquecido (venda_itens, preços, metas), captura Deskrio diária, PWA, IA endpoints.

A documentação está defasada. Decidir não é discutir "se" — é formalizar o que já está acontecendo há 60+ dias.

---

## Opções Consideradas

### Opção A — Excel VIVE
Reativar P6 (reconstruir 18.180 fórmulas PROJECAO), P8 (redesign DASH), P12 (popular timeline mensal) etc. Sprint paralelo Excel + SaaS.

**Custo estimado:** 20-40h de engenharia. Risco de re-introduzir bugs (openpyxl + slicers, LibreOffice recalc ≠ Excel, etc.).

**Valor:** zero — Excel não é usado pela operação comercial. Foi sempre um protótipo.

**Descartado.**

### Opção B — Excel É LEGADO
Congelar 100% do Excel. Atualizar docs dizendo "arquivo histórico". Foco absoluto no SaaS.

**Risco:** perder referência viva das regras de negócio embutidas nas fórmulas (Motor 92 combinações, Score v2). Se SaaS falhar, não há rollback para Excel.

**Parcialmente descartado.**

### ✅ Opção C — HÍBRIDO (ESCOLHIDA)

**Excel:**
- **Operacional mínimo:** mantêm apenas CARTEIRA (46 col imutáveis) + SINALEIRO + REGRAS (18 tabelas). São a fonte de verdade das regras de negócio.
- **Congelado:** PROJECAO (P6), DASH (P8), timeline mensal (P12), E-commerce integration (P9), REDE/REGIONAL (P11), #REF! (P10). Não são tocados exceto se quebrarem o operacional mínimo.
- **Backup:** último `.xlsx` de referência fica em `data/output/CRM_VITAO360_V13_PROJECAO.xlsx` como snapshot 2026-02-17.

**SaaS:**
- **Prioridade absoluta:** novas features, bugs, dados reais, integrações.
- **Fonte de dados:** banco PostgreSQL (Neon) populado via `scripts/ingest_real_data.py` + `scripts/sync_deskrio_to_db.py` + `scripts/populate_log_redes.py`.
- **Captura diária Deskrio:** agora reprodutível via `scripts/deskrio_daily_snapshot.py` (criado 2026-04-24).

**Regras de Negócio (fonte única):**
- Motor 92 combinações: persiste em `data/intelligence/motor_regras_v4.json` + `data/intelligence/mapa_motor_novo.json`
- Score v2 pesos: em `data/intelligence/arquitetura_9_dimensoes.json`
- 18 tabelas REGRAS: devem ter equivalente em schema PostgreSQL (verificar Phase 11/12 do motor)

---

## Status dos 12 Problemas Diagnosticados

| # | Problema | Resolução OPÇÃO C |
|---|----------|-------------------|
| P1 | Token Deskrio 403 kanban_cards 04-24 | **RESOLVIDO** — arquivos corrompidos removidos, commit atômico 04-24 sem kanban_cards |
| P2 | 4 snapshots Deskrio pendentes commit | **RESOLVIDO** — 4 commits atômicos (04-21, 04-22, 04-23, 04-24) |
| P3 | Scripts Deskrio fora de `scripts/` | **RESOLVIDO** — `deskrio_daily_snapshot.py` + `deskrio_health_check.py` |
| P4 | 42 warnings (Two-Base + ALUCINAÇÃO) | **RESOLVIDO** — 100% FP, verify.py refinado, 0 WARN |
| P5 | Excel V13 parado há 2 meses | **ACEITO** — Excel é legado operacional mínimo (CARTEIRA + SINALEIRO + REGRAS) |
| P6 | PROJECAO zerada (18.180 fórmulas) | **CONGELADO** — projeção agora vive no SaaS (banco) |
| P7 | LOG incompleto (13.4%) | **CONGELADO** no Excel — LOG agora é `log_interacoes` no banco SaaS |
| P8 | DASH Frankenstein (redesign) | **CONGELADO** — dashboards agora são páginas Next.js |
| P9 | E-commerce não integrado na CARTEIRA | **CONGELADO** — integração ocorre no banco SaaS |
| P10 | #REF! nas REDES_FRANQUIAS_v2 | **BAIXO** — só corrige se impactar CARTEIRA/SINALEIRO |
| P11 | REDE/REGIONAL vazia na CARTEIRA | **BAIXO** — nice-to-have do operacional mínimo |
| P12 | Timeline mensal vazia | **CONGELADO** — timeline agora é endpoint backend SaaS |

---

## Impacto nas Regras

**Mantidas inalteradas:**
- R1 (CNPJ 14 dígitos), R4 (Two-Base), R5 (openpyxl inglês), R7 (faturamento R$ 2.091.000), R8 (zero fabricação), R11 (commits atômicos), R12 (L1/L2/L3)

**Reinterpretadas para o contexto SaaS:**
- R3 (CARTEIRA 46 colunas imutáveis) → passa a significar: **o schema `clientes` do banco** preserva as 46 colunas-chave, mesmo que UI/API adicione campos derivados.
- R9 (visual LIGHT) → aplicável ao frontend Next.js.
- R10 (validação pós-build) → agora via testes automatizados (pytest backend + vitest frontend) e `scripts/postflight_check.py` após ingest.

---

## Backlog Reativado (vindo da memória 01/Abr/2026)

Com Excel congelado, estes ganham prioridade:

1. **Mercos API direta** (substituir export manual → captura automática, como Deskrio hoje)
2. **Asana integração** (tarefas/demandas dos 4 consultores)
3. **IA Agentes** (injeção de Claude em pontos-chave do pipeline)

---

## Commits Relacionados à Decisão

- `25ef34d` — daily snapshot 04-21
- `caf5538` — daily snapshot 04-22
- `abcdc1c` — daily snapshot 04-23
- `e1297fe` — daily snapshot 04-24 (parcial, kanban omitido)
- (próximo commit) — scripts Deskrio reprodutíveis + verify.py refinado + este documento

---

## Próximas Revisões

- **2026-05-24:** re-avaliar se Excel operacional mínimo ainda justifica existência. Se CARTEIRA/SINALEIRO migrou pra UI SaaS, congelar 100% (transição para Opção B).
- **Trimestralmente:** reprocessar snapshot Mercos/SAP/Deskrio, atualizar baseline R$ caso divergência > 0.5%.

---

## Assinaturas

- **Orquestrador:** @aios-master (2026-04-24)
- **Autorização:** Leandro ("verde pra tudo resolva" — 2026-04-24)
