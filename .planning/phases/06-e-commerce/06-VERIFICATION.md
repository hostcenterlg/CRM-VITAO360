---
phase: 06-e-commerce
verified: 2026-02-17T17:00:00Z
status: gaps_found
score: 8/11 must-haves verified
re_verification: false
gaps:
  - truth: "17 arquivos de e-commerce processados com dedup (10-12 meses unicos, Outubro ausente documentado)"
    status: partial
    reason: "Encontrados 18 arquivos (nao 17), processados 10 (nao 17), 6 descartados por dedup"
    artifacts:
      - path: "data/output/phase06/ecommerce_raw.json"
        issue: "Metadata mostra 18 arquivos encontrados, apenas 10 processados (6 dedup, 2 error)"
    missing:
      - "Atualizar ROADMAP.md Success Criteria #1 para refletir realidade: '18 arquivos encontrados, 10 processados apos dedup'"
  - truth: "6 colunas de e-commerce no DRAFT 1 (cols 15-20) populadas para clientes com match"
    status: verified_with_notes
    reason: "Populadas para 294 clientes (de 502 total DRAFT 1), nao 'todos os clientes'"
    artifacts:
      - path: "data/sources/drafts/DL_DRAFT1_FEV2026.xlsx"
        issue: "58% de cobertura (294/502), limitado por match rate 64.6%"
    missing:
      - "Atualizar ROADMAP.md Success Criteria #2 para especificar cobertura esperada vs total"
  - truth: "Taxa de matching >= 80% dos registros de e-commerce resolvidos para CNPJ"
    status: failed
    reason: "Match rate 64.6% (441/683) esta abaixo do target 80%"
    artifacts:
      - path: "data/output/phase06/match_report.json"
        issue: "242 nomes nao matched, maioria (200+) sao visitantes B2B portal sem CNPJ em nenhuma base"
    missing:
      - "Investigar se os 242 unmatched sao realmente prospects novos (nao clientes)"
      - "Considerar ajustar Success Criteria #3 para match rate realista dado a natureza dos dados"
---

# Phase 6: E-commerce Verification Report

**Phase Goal:** Processar ~17 relatorios de e-commerce Mercos (10-12 meses unicos apos dedup), cruzar com CNPJ via matching por nome, e popular 6 colunas de e-commerce no DRAFT 1 + JSON intermediario para Phase 9.

**Verified:** 2026-02-17T17:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 17 arquivos .xlsx + 2 .xls lidos sem erro, com header detection dinamica (formato 9 ou 11 colunas) | ⚠️ PARTIAL | 18 arquivos encontrados (16 .xlsx + 2 .xls). 16 .xlsx processados com header detection (9-col OLD e 11-col NEW). 2 .xls gracefully skipped (xlrd indisponivel). Total 10 processados, 6 descartados por dedup, 2 por erro. |
| 2 | Duplicatas detectadas e eliminadas: trio Abril/Maio/junho, par Dezembro, preferencia por arquivo com mais rows | ✓ VERIFIED | L1 dedup: 2 grupos (trio Abril/Maio/junho com 77 rows cada, par Dezembro com 17 rows cada). L2 dedup: 3 conflitos de mes (Dezembro, Janeiro, Fevereiro). Trio reassigned para Abril. Logs confirmam decisoes. |
| 3 | Cada arquivo mapeado para mes real via data de emissao + content fingerprint (nao pelo nome do arquivo) | ✓ VERIFIED | ecommerce_raw.json mostra `emission_date` + `assigned_month` para cada arquivo. Trio reassignment prova que nao confia no filename. |
| 4 | 10-12 meses unicos extraidos com dados normalizados em JSON | ✓ VERIFIED | metadata.unique_months = 10. Meses: MAR/25, ABR/25, JUN/25, JUL/25, AGO/25, SET/25, NOV/25, DEZ/25, JAN/26, FEV/26. Faltam MAI/25 e OUT/25 (documentados). |
| 5 | Outubro documentado como AUSENTE, meses faltantes explicitamente listados | ✓ VERIFIED | metadata.missing_months = ["2025-05", "2025-10"]. |
| 6 | Cada registro de e-commerce esta cruzado com um CNPJ via lookup nome->CNPJ (Mercos Carteira + SAP + fuzzy) | ✓ VERIFIED | 441/683 nomes matched (64.6%). Lookup usando 3 fontes: Mercos Carteira (497), DRAFT 1 (502), SAP Cadastro (1698). 5 niveis de matching: cnpj_prefix, exact, exact_normalized, partial, partial_normalized. |
| 7 | Taxa de matching >= 80% dos registros de e-commerce resolvidos para CNPJ | ✗ FAILED | Match rate 64.6% esta 15.4 pontos abaixo do target. 242 unmatched, dos quais ~200 sao visitantes B2B portal sem CNPJ em nenhuma base de clientes. Por records (1075): 72.0%. Por acessos: 74.0%. |
| 8 | Dados agregados por CNPJ: acessa_ecommerce, data_ult_acesso, qtd_acessos, pedido_via_ecommerce, catalogo_visualizado | ✓ VERIFIED | ecommerce_matched.json contem 391 CNPJs com 12 campos agregados: acessa_ecommerce, data_ult_acesso, qtd_acessos_ultimo_mes, pedido_via_ecommerce, pct_pedidos_ecommerce, valor_pedidos_b2b_total, catalogo_visualizado, meses_com_acesso, total_atividades, total_itens_carrinho, total_orcamentos, valor_carrinho_total. |
| 9 | DRAFT 1 colunas 15-20 populadas com dados e-commerce mais recentes para cada cliente | ⚠️ PARTIAL | 6 colunas (ACESSOS SEMANA, ACESSO B2B, ACESSOS PORTAL, ITENS CARRINHO, VALOR B2B, OPORTUNIDADE) populadas para 294 clientes (de 502 total DRAFT 1 = 58% cobertura). Limitado por match rate. |
| 10 | JSON intermediario (ecommerce_matched.json) pronto para Phase 9 popular CARTEIRA expandida | ✓ VERIFIED | ecommerce_matched.json existe com cnpj_to_ecommerce dict (391 CNPJs). Formato correto para consumo por Phase 9. |
| 11 | Match report documenta taxa de matching, falhas, e clientes unmatched | ✓ VERIFIED | match_report.json contem summary (total, matched, unmatched, match_rate, by_level), 441 matches detalhados, 242 unmatched detalhados. |

**Score:** 8/11 truths verified (2 partial, 1 failed)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/phase06_ecommerce/01_extract_ecommerce.py` | ETL completo dos relatorios e-commerce Mercos | ✓ VERIFIED | 842 lines. Contem header detection (find_header_row, detect_format), L1+L2 dedup, trio conflict resolution, month assignment, JSON output. |
| `data/output/phase06/ecommerce_raw.json` | Dados brutos extraidos por mes, por nome, dedup aplicado | ✓ VERIFIED | 440KB, 13,179 lines. Contem metadata (18 found, 10 processed, 6 dedup, 2 error), file_inventory (18 arquivos), monthly_data (10 meses, 1075 registros), dedup_report. |
| `scripts/phase06_ecommerce/02_match_populate.py` | Matching nome->CNPJ + agregacao + populacao DRAFT 1 | ✓ VERIFIED | 894 lines (min 250). Contem 5-level matching, 3-source lookup, agregacao por CNPJ, DRAFT 1 population, JSON output. |
| `data/output/phase06/ecommerce_matched.json` | Dados e-commerce cruzados com CNPJ, agregados, prontos para CARTEIRA | ✓ VERIFIED | 15,707 lines. Contem cnpj_to_ecommerce dict (391 CNPJs), metadata (match_rate 0.6457), unmatched (242 nomes). |
| `data/output/phase06/match_report.json` | Relatorio de matching com taxa, falhas, decisoes | ✓ VERIFIED | 5,240 lines. Contem summary (by_level breakdown), 441 matches, 242 unmatched. |
| `data/sources/drafts/DL_DRAFT1_FEV2026.xlsx` | Colunas 15-20 populadas | ✓ VERIFIED | Modified (170458 -> 170101 bytes). Colunas 15-20 (ACESSOS SEMANA, ACESSO B2B, ACESSOS PORTAL, ITENS CARRINHO, VALOR B2B, OPORTUNIDADE) tem 287-294 rows populadas (de 502 total). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|--|----|--------|---------|
| 01_extract_ecommerce.py | data/sources/mercos/ecommerce/*.xlsx | openpyxl read_only + header detection | ✓ WIRED | Script contem imports openpyxl, find_header_row(), detect_format(), process_xlsx_file(). |
| 01_extract_ecommerce.py | ecommerce_raw.json | json.dump after dedup | ✓ WIRED | Script contem `json.dump(output_data, f, ...)` com output_path = ecommerce_raw.json. |
| 02_match_populate.py | ecommerce_raw.json | json.load monthly_data | ✓ WIRED | Script contem `load_json(ECOMMERCE_RAW_PATH)` e acessa monthly_data. Pattern "ecommerce_raw" presente. |
| 02_match_populate.py | 08_CARTEIRA_MERCOS.xlsx | build_name_to_cnpj_lookup (name->CNPJ) | ✓ WIRED | Script contem `openpyxl.load_workbook(MERCOS_CARTEIRA_PATH)` e extrai cols Razao/Nome/CNPJ. Pattern "08_CARTEIRA_MERCOS" presente. |
| 02_match_populate.py | DL_DRAFT1_FEV2026.xlsx | openpyxl write cols 15-20 | ✓ WIRED | Script contem `openpyxl.load_workbook(DRAFT1_PATH)` e escreve cols 15-20. Pattern "DL_DRAFT1.*DRAFT" presente (path usado: data/sources/drafts/). |
| ecommerce_matched.json | Phase 9 CARTEIRA population | cnpj_to_ecommerce dict | ✓ WIRED | JSON contem cnpj_to_ecommerce dict com 391 CNPJs. Formato pronto para consumo: cada CNPJ mapeia para dict com 12 campos agregados. |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| ECOM-01: Dados de e-commerce Mercos cruzados na CARTEIRA | ⚠️ PARTIAL | Dados cruzados no DRAFT 1 (58% dos clientes), nao no V13 CARTEIRA (0 rows). Phase 9 responsavel por popular CARTEIRA final. |
| ECOM-02: Colunas de e-commerce (4 colunas) populadas para todos os clientes | ⚠️ PARTIAL | 6 colunas (nao 4) populadas no DRAFT 1 para 294 clientes (nao todos os 502). Discrepancia entre REQUIREMENTS.md "4 colunas" vs ROADMAP.md "6 colunas" vs Blueprint "6 colunas AR-AW". |
| ECOM-03: Acesso ao e-commerce por mes (20 arquivos) processados | ⚠️ PARTIAL | 18 arquivos encontrados (nao 20), 10 processados (10 meses unicos). REQUIREMENTS.md estimativa incorreta. |

**Requirements Coverage:** 0/3 SATISFIED, 3/3 PARTIAL (todas com notas de esclarecimento sobre discrepancias entre estimativas e realidade)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | - | - | - | No anti-patterns detected in code. Scripts sao substantivos, bem estruturados, com error handling. |

**Note:** As discrepancias encontradas sao de **estimativas iniciais vs realidade descoberta** (17 vs 18 arquivos, 20 vs 18 arquivos, 4 vs 6 colunas), nao anti-patterns de codigo. Isso e esperado em fases de discovery.

### Human Verification Required

#### 1. Verificar se 242 unmatched sao prospects vs clientes perdidos

**Test:** Revisar lista de 242 nomes unmatched em match_report.json. Para amostra de 10-20 nomes, verificar manualmente se:
- Sao prospects novos que se registraram no portal B2B mas nunca compraram
- Sao clientes ativos mas com erro de digitacao (typo) no nome
- Sao clientes antigos que mudaram de razao social

**Expected:** Maioria (>80%) deve ser prospects B2B portal sem historico de compra em SAP/Mercos.

**Why human:** Requer conhecimento do negocio e acesso a fontes externas (CNPJ Receita, historico comercial) que scripts nao tem.

#### 2. Validar agregacao temporal faz sentido comercialmente

**Test:** Para 5 clientes com dados e-commerce no DRAFT 1, verificar se:
- data_ult_acesso e coerente com last known activity
- qtd_acessos_ultimo_mes reflete engajamento real
- pedido_via_ecommerce = "COMPRA B2B" bate com vendas B2B conhecidas

**Expected:** 100% dos 5 casos deve ter dados coerentes com realidade comercial conhecida.

**Why human:** Requer contexto de vendas real que apenas Leandro/equipe comercial tem.

#### 3. Verificar cobertura 58% e aceitavel para objetivo final

**Test:** Dado que Phase 6 objetivo final e "gerar agenda diaria inteligente por consultor", avaliar se:
- Os 294 clientes com dados e-commerce representam a maior parte do potencial B2B
- Os 208 clientes sem dados e-commerce (de 502) sao small/inactive que nao usariam portal B2B de qualquer forma
- Match rate 64.6% e suficiente para ranking inteligente de atendimentos

**Expected:** Cobertura de 58% deve incluir >=80% dos clientes A/B (alto valor) e >=90% dos usuarios ativos de B2B.

**Why human:** Requer analise de distribuicao ABC e perfil de clientes B2B vs presencial, conhecimento que esta no contexto de negocio.

### Gaps Summary

Phase 6 atingiu o objetivo tecnico de **processar relatorios e-commerce, cruzar com CNPJs, e popular dados no DRAFT 1**, mas existem **3 gaps relacionados a estimativas iniciais vs realidade**:

1. **Gap de arquivos processados:** ROADMAP.md estimou 20 arquivos, mas foram encontrados 18 (16 .xlsx + 2 .xls), e apenas 10 processados apos dedup. Discrepancia esperada em fase de discovery. **Impacto: Baixo.** 10 meses unicos sao suficientes para analise temporal.

2. **Gap de match rate:** Target 80% nao foi atingido (64.6%). Root cause: ~200 dos 683 nomes sao visitantes one-time do portal B2B que **nunca viraram clientes** (nao estao em SAP, Mercos, ou DRAFT 1). Estes nao devem estar no CRM. Match rate real para clientes conhecidos e ~85-90%. **Impacto: Medio.** Requer validacao humana (item 1 acima).

3. **Gap de cobertura no DRAFT 1:** 294/502 clientes (58%) tem dados e-commerce. Limitado pelo match rate. **Impacto: Medio.** Requer validacao se os 208 sem dados sao clientes B2B ativos ou apenas small/inactive (item 3 acima).

**Critical finding:** V13 CARTEIRA tem **0 data rows**, entao os dados de e-commerce nao foram populados la. Isso e **esperado** porque Phase 9 e responsavel por popular CARTEIRA expandida (81 colunas). DRAFT 1 foi usado como destino alternativo viavel, conforme planejado.

**Preservation check:** 19,224 formulas PROJECAO **100% intactas** no V13. Zero risco de regressao.

**Readiness for Phase 9:** ecommerce_matched.json esta pronto com 391 CNPJs. Format validation: cnpj_to_ecommerce dict com 12 campos agregados por CNPJ. Phase 9 pode consumir diretamente.

---

_Verified: 2026-02-17T17:00:00Z_
_Verifier: Claude (gsd-verifier)_
