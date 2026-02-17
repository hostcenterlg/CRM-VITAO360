# Phase 4: LOG Completo - Research

**Researched:** 2026-02-17
**Domain:** Data integration, synthetic data generation, Excel automation (openpyxl), deduplication
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

1. **10 PRINCIPIOS INVIOLAVEIS** (REGRAS_INTELIGENCIA_CRM_VITAO_v2):
   - P1: ZERO DADOS FABRICADOS — toda info de fonte real. IA nunca inventa dados. Campo sem dado = vazio.
   - P2: TWO-BASE ARCHITECTURE — valores financeiros NUNCA no LOG. Separacao absoluta BASE_VENDAS vs LOG. CNPJ como chave.
   - P3: CARTEIRA IMUTAVEL — layout base (46 cols MERCOS) nao pode ser alterado. Extensoes APOS as 46.
   - P4: LOG APPEND-ONLY — so recebe novas linhas. Nunca editar, nunca deletar.
   - P5: CONSULTOR NUNCA TOCA O LOG — preenche AGENDA, devolve, Leandro cola no DRAFT 2, validacao, LOG.
   - P6: CNPJ COMO CHAVE PRIMARIA — 14 digitos sem pontuacao (ex: 32387943000105). Match secundario: RAZAO SOCIAL.
   - P7: PARA CADA ACAO UMA REACAO — RESULTADO determina automaticamente: Estagio, Fase, Tipo Contato, Follow-up, Acao Futura, Temperatura, Tentativa.
   - P8: VITAO SEMPRE SEM ACENTO — em todo documento, planilha, HTML, codigo.
   - P9: LIGHT THEME + HTML RESPONSIVO — nunca dark mode.
   - P10: 100% RASTREABILIDADE — cada dado tem rastreabilidade para fonte original.

2. **Classificacao 3-tier** (criterios JA documentados na auditoria):
   - REAL: Notas contextuais >15 chars com detalhes especificos. Referencias a valores R$, "FECHADO", boleto, rastreamento, XML, negociacao, reuniao. Nao se enquadra em padrao sintetico.
   - SINTETICO: 12 padroes de notas genericas. Sequencias regulares de 8-10 contatos com offsets padronizados. Notas curtas sem contexto especifico.
   - ALUCINACAO: CNPJ invalido (<14 digitos), nome padrao "CLIENTE + numero", vendedores ficticios (JOAO SILVA, PEDRO OLIVEIRA, etc.). 558 registros JA identificados e separados.
   - 558 alucinacoes: Descartar totalmente e recriar dados com qualidade 100/100.
   - Visibilidade da classificacao no CRM: Claude decide (coluna visivel filtravel vs metadata interna).

3. **Pipeline Completo:** CARTEIRA -> AGENDA -> DRAFT 2 -> LOG -> retroalimenta CARTEIRA.

4. **Estruturas EXATAS das Abas:**
   - LOG: 20 colunas, 5 blocos (IDENTIFICACAO A-G, CONTATO H-K, CLASSIFICACAO L-N, ACAO FUTURA O-P, CONTROLE Q-T) -- conforme SKILL_LOG_DRAFT_PIPELINE.md
   - DRAFT 2: 24 colunas operacionais -- conforme DOC_DEFINITIVA_AGENDA_DRAFT2.md

5. **Volume e Dados Sinteticos:**
   - Meta: 10.634 atendimentos qualificados em 2025 + Jan-Fev 2026
   - Logica: 957 vendas x 11,1 atendimentos/venda = 10.634
   - ANCORA: Usar vendas SAP REAIS (866 vendas com datas e valores) como ancora. Reconstruir funil de tras pra frente (D-7 a D+10 da venda).
   - Ultra-realista: Respeitar calendario real (feriados, ferias, ausencias, capacidade reduzida).
   - PADRAO HUMANO OBRIGATORIO: Variacao realista — nada de padrao robotico serial.

6. **Motor de Regras:** 13 resultados possiveis, cada resultado gera automaticamente follow-up, estagio funil, temperatura, fase, acao futura.

7. **Jornadas Completas (GENOMA COMERCIAL):** 6 tipos (A-F), 200+ templates de notas, distribuicoes estatisticas reais.

8. **Dedup key:** DATA (YYYY-MM-DD) + CNPJ (14 digitos, zero-padded) + RESULTADO (uppercase, trimmed).

9. **Equipe:** 4 consultores com territorios definidos + Helder (saiu Ago/2025) + Lorrany (marginal). Julio Gadret tem 2 grafias a normalizar.

10. **Tratamento de Conflitos:** Dado de melhor qualidade prevalece. Multiplos contatos mesmo dia mesmo cliente = ambos ficam (registros separados).

### Claude's Discretion

- Tratamento dos 558 alucinados (fora do LOG ou marcados com flag)
- Visibilidade da classificacao 3-tier (coluna filtravel ou metadata)
- Granularidade Deskrio (1 registro por conversa vs por mensagem)
- Nivel de detalhe das colunas auxiliares
- Algoritmo de variacao humana para sinteticos (baseado no pseudo-codigo do GENOMA secao 11)

### Deferred Ideas (OUT OF SCOPE)

- Aba SINALEIRO/SEMAFORO com filtros — Phase 5/9
- Aba PROJECAO/META por cliente (refinar) — Phase 8
- Agendas individuais por consultor — Phase 9/10
- Unificacao AGENDA + DRAFT 2 — Phase 9
- Logica de retroalimentacao CARTEIRA <-> DRAFT 2 — Phase 9
- Inteligencia de capacidade de atendimento — Phase 8/9
- Dashboard com ligacoes, atendimentos, tarefas, motivos — Phase 5
- Redistribuicao da Manu (maternidade) — Phase 8/9
- VBA/Macro PROCESSAR (DRAFT -> LOG automatico) — Phase 10

</user_constraints>

---

## Summary

Phase 4 is the **data integration and synthetic generation phase** of the CRM VITAO360 project. Its core mission is to populate the LOG tab from ~1,581 current records to 11,758+ records by integrating three primary data sources (CONTROLE_FUNIL with 10,544 clean records, Deskrio tickets with 5,329 tickets, and 3,540 retroactive contacts) while generating ultra-realistic synthetic data anchored to 866 real SAP sales.

The technical challenge is threefold: (1) **Extract, Transform, Load (ETL)** from heterogeneous sources (Excel files with inconsistent schemas, CSV message exports, text files) into a standardized 20-column LOG format; (2) **Generate synthetic attendance records** that reconstruct complete sales funnels backwards from real SAP sales (D-7 to D+10), following the GENOMA COMERCIAL's 6 journey types, 200+ note templates, and statistical distributions; (3) **Deduplicate and validate** across all sources using the composite key DATA+CNPJ+RESULTADO while enforcing Two-Base Architecture (R$ 0.00 always in LOG).

The existing codebase provides solid foundations: Python scripts using openpyxl (Phase 1-3 patterns), a fully implemented `motor_regras.py` with all rule engine functions, established `v3_styles.py` formatting constants, and a proven CNPJ normalization pipeline. The LOG tab structure (v3_log.py) already exists in the CRM V13 but is currently empty -- this phase fills it.

**Primary recommendation:** Use a 4-plan sequential approach: Plan 04-01 processes CONTROLE_FUNIL (the bulk), Plan 04-02 integrates Deskrio, Plan 04-03 generates retroactive synthetic data anchored to SAP sales, and Plan 04-04 performs cross-source dedup and final validation.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.x | Read/write Excel files (.xlsx) | Already used in all Phase 1-3 scripts; preserves XML infrastructure |
| Python | 3.12.10 | Runtime | Installed via pyenv at `C:/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe` |
| json | stdlib | Intermediate data storage | Used in Phase 2 for SAP/Mercos merge pipeline |
| pathlib | stdlib | Cross-platform path handling | Used in all existing scripts |
| datetime | stdlib | Date math (business days, follow-ups) | Used in motor_regras.py `dia_util()` function |
| re | stdlib | CNPJ normalization, pattern matching | Used in Phase 2 for `normalize_cnpj()` |
| random | stdlib | Human-like variation in synthetic data | Needed for GENOMA COMERCIAL algorithm |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| csv | stdlib | Parse Deskrio CSV exports (14MB message files) | Plan 04-02 for Deskrio integration |
| collections | stdlib | Counter, defaultdict for statistics | Dedup counting, distribution analysis |
| hashlib | stdlib | Deterministic hashing for dedup keys | Plan 04-04 for composite key generation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl | pandas + openpyxl | pandas adds dependency; project already standardized on pure openpyxl |
| json intermediate | SQLite | SQLite is better for large datasets but adds complexity; JSON matches existing pattern |
| random module | numpy.random | numpy provides better distributions but is not installed; stdlib random is sufficient |

**Installation:**
```bash
# No new packages needed -- all stdlib + openpyxl already installed
/c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe -c "import openpyxl; print(openpyxl.__version__)"
```

---

## Architecture Patterns

### Recommended Project Structure

```
scripts/
  phase04_log_completo/
    01_process_controle_funil.py    # Plan 04-01: Extract + classify 10,544 records
    02_process_deskrio.py           # Plan 04-02: Parse Deskrio tickets -> LOG format
    03_generate_synthetic.py        # Plan 04-03: SAP-anchored funnel reconstruction
    04_dedup_validate.py            # Plan 04-04: Cross-source dedup + final validation
    _helpers.py                     # Shared: CNPJ normalization, classification, note templates
data/
  output/
    phase04/
      controle_funil_classified.json   # Intermediate: classified CONTROLE_FUNIL records
      deskrio_normalized.json          # Intermediate: normalized Deskrio records
      synthetic_generated.json         # Intermediate: generated synthetic records
      log_final_validated.json         # Final: deduplicated, validated LOG records
      validation_report.json           # Audit: stats, warnings, distribution analysis
```

### Pattern 1: SAP-Anchored Backward Funnel Reconstruction

**What:** For each of the 866 SAP sales, generate the complete attendance journey backwards from the sale date, using the GENOMA COMERCIAL journey templates.

**When to use:** Generating synthetic data for all 2025 sales that need attendance records.

**Example:**

```python
# Source: GENOMA_COMERCIAL_VITAO360.md Section 11
import random
from datetime import date, timedelta

def reconstruct_funnel_for_sale(cnpj, sale_date, situacao, consultor, templates):
    """
    Given a real SAP sale, reconstruct the full funnel backwards.
    Returns list of attendance records (D-7 to D+10).
    """
    records = []

    # 1. Determine journey type based on client situation
    if situacao == 'PROSPECT':
        journey = 'A'  # 8-10 contacts
        pre_count = random.randint(6, 7)
    elif situacao == 'ATIVO':
        journey = 'B'  # 3-5 contacts
        pre_count = random.randint(2, 3)
    elif situacao in ('INAT.REC',):
        journey = 'C'  # 5-8 contacts
        pre_count = random.randint(4, 6)
    elif situacao in ('INAT.ANT',):
        journey = 'D'  # 5-8 contacts
        pre_count = random.randint(4, 6)
    else:
        journey = 'B'
        pre_count = random.randint(2, 3)

    # 2. Generate pre-sale contacts (backwards from D0)
    # Last pre-sale = ORCAMENTO (D-1 to D-3)
    orcamento_offset = random.randint(1, 3)

    # If PROSPECT, add CADASTRO between ORCAMENTO and VENDA
    if situacao == 'PROSPECT':
        cadastro_offset = random.randint(1, 2)
        records.append(make_record(
            date=subtract_business_days(sale_date, cadastro_offset),
            resultado='CADASTRO',
            consultor=consultor,
            cnpj=cnpj,
            nota=random.choice(templates['cadastro'])
        ))

    records.append(make_record(
        date=subtract_business_days(sale_date, orcamento_offset),
        resultado='ORCAMENTO',
        consultor=consultor,
        cnpj=cnpj,
        nota=random.choice(templates['orcamento'])
    ))

    # Earlier contacts: EM ATENDIMENTO, FOLLOW UPs, interspersed NÃO RESPONDE
    # ... (generate with variacao humana)

    # 3. Sale record (D0)
    records.append(make_record(
        date=sale_date,
        resultado='VENDA / PEDIDO',
        consultor=consultor,
        cnpj=cnpj,
        nota=random.choice(templates['venda'])
    ))

    # 4. Post-sale: MKT (D+2/3), SUPORTE (conditional), CS (D+7/10)
    mkt_offset = random.randint(2, 3)
    records.append(make_record(
        date=add_business_days(sale_date, mkt_offset),
        resultado='SUPORTE',
        tipo_contato='ENVIO DE MATERIAL - MKT',
        consultor=consultor,
        cnpj=cnpj,
        nota=random.choice(templates['material_mkt'])
    ))

    # Suporte passivo (30% new, 20% active, 15% inactive)
    suporte_prob = {'PROSPECT': 0.30, 'ATIVO': 0.20}.get(situacao, 0.15)
    if random.random() < suporte_prob:
        records.append(make_record(
            date=add_business_days(sale_date, random.randint(3, 5)),
            resultado='SUPORTE',
            tipo_contato='CONTATOS PASSIVO / SUPORTE',
            consultor=consultor,
            cnpj=cnpj,
            nota=random.choice(templates['suporte_passivo'])
        ))

    # CS (D+7 to D+10)
    cs_offset = random.randint(7, 10)
    records.append(make_record(
        date=add_business_days(sale_date, cs_offset),
        resultado='CS',
        consultor=consultor,
        cnpj=cnpj,
        nota=random.choice(templates['cs'])
    ))

    return records
```

### Pattern 2: Composite Key Deduplication

**What:** Use DATA + CNPJ + RESULTADO as composite dedup key across all sources.

**When to use:** Plan 04-04 when merging CONTROLE_FUNIL, Deskrio, and synthetic records.

**Example:**

```python
def make_dedup_key(data, cnpj, resultado):
    """
    Create composite deduplication key.
    DATA: normalized to YYYY-MM-DD string
    CNPJ: 14-digit zero-padded string
    RESULTADO: uppercase trimmed
    """
    if isinstance(data, date):
        data_str = data.strftime('%Y-%m-%d')
    else:
        data_str = str(data).strip()[:10]

    cnpj_str = re.sub(r'[^0-9]', '', str(cnpj)).zfill(14)
    resultado_str = str(resultado).strip().upper()

    return f"{data_str}|{cnpj_str}|{resultado_str}"


def deduplicate_records(all_records, priority_order):
    """
    Deduplicate by composite key, keeping highest-priority source.
    priority_order: e.g. ['SAP', 'CONTROLE_FUNIL', 'DESKRIO', 'SINTETICO']
    """
    seen = {}
    for record in sorted(all_records, key=lambda r: priority_order.index(r['source'])):
        key = make_dedup_key(record['data'], record['cnpj'], record['resultado'])
        if key not in seen:
            seen[key] = record
        # else: lower priority, skip
    return list(seen.values())
```

### Pattern 3: CNPJ Normalization (Established Pattern)

**What:** Normalize all CNPJ values to 14-digit zero-padded strings, matching the `normalize_cnpj()` function from Phase 2.

**When to use:** Every time a CNPJ is read from any source.

**Example:**

```python
# Source: scripts/phase02_faturamento/03_merge_sap_mercos.py
def normalize_cnpj(raw):
    """Normalize CNPJ to 14-digit string."""
    return re.sub(r'[^0-9]', '', str(raw)).zfill(14)
```

### Pattern 4: Business Day Math (Established Pattern)

**What:** Calculate follow-up dates using business days (Mon-Fri only), matching `dia_util()` from motor_regras.py.

**When to use:** When calculating follow-up dates and reconstructing journey timelines.

**Example:**

```python
# Source: scripts/motor_regras.py
def dia_util(data_base, dias):
    """Calcula data futura em dias uteis (seg-sex)."""
    if dias == 0:
        return data_base
    atual = data_base
    contados = 0
    while contados < dias:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            contados += 1
    return atual

# For backward calculation (pre-sale contacts):
def subtract_business_days(data_base, dias):
    """Calcula data anterior em dias uteis (seg-sex)."""
    if dias == 0:
        return data_base
    atual = data_base
    contados = 0
    while contados < dias:
        atual -= timedelta(days=1)
        if atual.weekday() < 5:
            contados += 1
    return atual
```

### Pattern 5: Consultant Attribution (Established Pattern)

**What:** Determine which consultant handles a client based on UF + REDE rules.

**When to use:** Assigning synthetic records and validating existing data.

**Example:**

```python
# Source: scripts/motor_regras.py
def definir_consultor(uf, rede, vendedor_ultimo=""):
    rede_upper = (rede or "").upper()
    if "CIA DA SAUDE" in rede_upper or "FITLAND" in rede_upper:
        return "JULIO GADRET"
    redes_daiane = [
        "DIVINA TERRA", "BIOMUNDO", "BIO MUNDO", "MUNDO VERDE",
        "TUDO EM GRAOS", "VIDA LEVE", "ARMAZEM", "NATURVIDA",
        "LIGEIRINHO", "TRIP", "ESMERALDA",
    ]
    if any(r in rede_upper for r in redes_daiane):
        return "DAIANE STAVICKI"
    if uf in ["SC", "PR", "RS"]:
        return "MANU DITZEL"
    return "LARISSA PADILHA"
```

### Anti-Patterns to Avoid

- **Robotic serial patterns:** NEVER generate synthetic data with predictable sequences (e.g., exactly 8 contacts every time, same offsets). The GENOMA COMERCIAL explicitly requires human-like variation: some clients 3 contacts, others 14, others 1.
- **Fabricated financial data:** NEVER put R$ values in LOG records. Two-Base Architecture violation is the #1 historical error (742% inflation bug).
- **Overwriting existing LOG data:** LOG is append-only (P4). Even during population, never modify existing rows.
- **Weekend/holiday data:** NEVER generate attendance records on Saturday/Sunday. Check with `date.weekday() < 5`.
- **Duplicate note repetition:** NEVER use the same note template more than 3 times. Vary across 200+ templates.
- **CNPJ without normalization:** ALWAYS normalize to 14 digits zero-padded before any comparison or storage.
- **Ignoring Julio Gadret dual spelling:** ALWAYS normalize "Julio  Gadret" (double space) to "Julio Gadret" (single space).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Motor de Regras | Custom rule engine | `scripts/motor_regras.py` (existing) | Already implements all 13 RESULTADO -> derived fields logic with business day calculations. Tested in Phase 1-3. |
| Consultant attribution | Custom CNPJ->Consultant mapping | `motor_regras.definir_consultor()` (existing) | Handles UF, REDE, and priority rules. Already validated. |
| CNPJ normalization | Regex per-script | `normalize_cnpj()` from Phase 2 | Consistent 14-digit zero-padded format. Extract to shared _helpers.py. |
| Excel styling | Per-tab styling code | `scripts/v3_styles.py` (existing) | Fonts, fills, borders, colors all standardized. Reuse for LOG formatting. |
| Classification 3-tier | New classification rules | Reuse criteria from CONTROLE_FUNIL extraction (LOG_CONVERSA doc) | Criteria already documented: REAL/SINTETICO/ALUCINACAO patterns are locked. |
| Date business day math | Custom calendar handling | `motor_regras.dia_util()` (existing) | Already handles Mon-Fri only. Add `subtract_business_days()` as mirror. |

**Key insight:** The project already has a mature motor_regras.py and v3_styles.py that handle the hardest logic. Phase 4 should reuse these modules extensively, only adding ETL and synthetic generation on top.

---

## Common Pitfalls

### Pitfall 1: Two-Base Architecture Violation (742% Bug)

**What goes wrong:** Financial values (R$) leak into LOG records, causing 742% inflation when dashboards aggregate.
**Why it happens:** Source data (CONTROLE_FUNIL, SAP) contains financial columns that can accidentally be copied.
**How to avoid:** Explicit step in every ETL pipeline that sets all financial columns to 0 or removes them. Validation pass at the end checking that NO record in LOG has R$ > 0.
**Warning signs:** Any column named "VALOR", "PEDIDO", "FATURAMENTO", or any number > 0 in non-count columns.

### Pitfall 2: Weekend Attendance Records

**What goes wrong:** Synthetic records generated on Saturday/Sunday violate business rules.
**Why it happens:** Simple date arithmetic doesn't account for weekdays.
**How to avoid:** Always use `dia_util()` / `subtract_business_days()`. Add validation pass: assert all dates have `weekday() < 5`.
**Warning signs:** Any record with date.weekday() >= 5.

### Pitfall 3: VENDA Without ORCAMENTO Before It

**What goes wrong:** A VENDA record appears without a preceding ORCAMENTO (D-1 to D-3), violating mandatory sequence.
**Why it happens:** When generating synthetic data for real SAP sales, forgetting to create the prerequisite ORCAMENTO record.
**How to avoid:** The funnel reconstruction algorithm MUST always generate ORCAMENTO before VENDA. For PROSPECTS, also CADASTRO before VENDA. Validation pass: for every VENDA record, check that same CNPJ has ORCAMENTO in D-1 to D-3.
**Warning signs:** VENDA records without any prior ORCAMENTO for same CNPJ in the preceding 3 business days.

### Pitfall 4: Exceeding 40 Attendances/Day/Consultant

**What goes wrong:** A consultant has >40 records on a single date, violating capacity constraints.
**Why it happens:** When distributing synthetic records across dates, not checking daily capacity per consultant.
**How to avoid:** Maintain a daily counter per consultant. When counter hits 40, roll to next business day. Validation pass: GROUP BY (CONSULTOR, DATA) and assert COUNT <= 40.
**Warning signs:** Any consultant-date pair with count > 40.

### Pitfall 5: Julio Gadret Duplicate Spelling

**What goes wrong:** "Julio  Gadret" (double space) and "Julio Gadret" (single space) create split records.
**Why it happens:** SAP data has inconsistent spelling. The CONTROLE_FUNIL has 963 + 851 records under two different names.
**How to avoid:** Normalize consultant names early in ETL: `consultor.strip().replace('  ', ' ')`. Map all variants to canonical form.
**Warning signs:** Consultant count showing 5+ consultants when there should be 4 (+Helder historical).

### Pitfall 6: Deskrio Granularity Mismatch

**What goes wrong:** Deskrio has 77,805 messages across 5,425 conversations across 5,329 tickets. Mapping 1:1 message-to-LOG would create massive duplication.
**Why it happens:** Deskrio tracks individual messages, but LOG tracks attendances (1 attendance = 1 complete interaction with result).
**How to avoid:** Aggregate Deskrio data at the CONVERSATION level (5,425 records), not message level (77,805). Each conversation = 1 LOG record. Dedup against CONTROLE_FUNIL records for same date+CNPJ.
**Warning signs:** LOG count suddenly jumping by 77K+ records.

### Pitfall 7: Note Template Repetition

**What goes wrong:** The same note appears hundreds of times, making synthetic data obviously fake.
**Why it happens:** Random selection from a small template pool without tracking usage.
**How to avoid:** Track note usage with a counter. When a template has been used 3 times, remove it from the pool temporarily. Use 200+ templates from GENOMA COMERCIAL sections 7.1-7.6. Add slight variations (client name, product, date references).
**Warning signs:** Any note appearing >3 times in the full dataset.

### Pitfall 8: openpyxl XML Destruction

**What goes wrong:** openpyxl destroys Excel XML infrastructure (slicers, pivot tables, named ranges) when modifying an existing workbook.
**Why it happens:** openpyxl's parser doesn't preserve all XML elements.
**How to avoid:** For Phase 4, generate LOG data as a SEPARATE intermediary file, then use XML Surgery (established in prior phases) to inject data into the master CRM workbook. Never open-modify-save the master CRM directly with openpyxl.
**Warning signs:** Slicers, filters, or pivot tables breaking after openpyxl modification.

### Pitfall 9: Helder Brunkow Timeline Error

**What goes wrong:** Generating synthetic records for Helder after August 2025 when he left the company.
**Why it happens:** Not respecting the consultant timeline: Helder exited in August 2025.
**How to avoid:** Hard-code consultant availability windows: Helder = Feb-Aug/2025 only, Julio = Sep/2025 onwards.
**Warning signs:** Any Helder record after Aug 31, 2025 or any Julio record before Sep 1, 2025.

---

## Data Source Analysis

### Source 1: CONTROLE_FUNIL (Plan 04-01)

**File:** `data/sources/funil/CONTROLE_FUNIL_JAN2026.xlsx` + `06_LOG_FUNIL.xlsx`
**Records:** 10,544 clean (after removal of 558 alucinacoes + 589 duplicatas)
**Classification:** 9,195 REAL (87.2%) + 1,349 SINTETICO (12.8%)
**Period:** All of 2025
**Schema:** 42 columns in main LOG tab (needs mapping to 20-column LOG format)
**Key columns to map:**
- DATA -> LOG.A (DATA)
- CNPJ/CPF -> LOG.D (CNPJ) -- normalize to 14 digits
- NOME FANTASIA -> LOG.C (formula, but store as text for historical data)
- VENDEDOR DO ULTIMO PEDIDO -> LOG.B (CONSULTOR) -- apply definir_consultor()
- RESULTADO -> LOG.M (RESULTADO) -- normalize values to 12 standard options
- WHATSAPP/LIGACAO/LIG.ATENDIDA -> LOG.H/I/J
- TIPO ACAO -> LOG.K
- TIPO DO CONTATO -> LOG.L
- MOTIVO -> LOG.N
- NOTA DO DIA -> LOG.T
- MERCOS ATUALIZADO -> LOG.Q

**Sub-sources within CONTROLE_FUNIL (4 tabs, priority order):**
1. LOG tab (10,484 rows x 42 cols) -- primary
2. Manu log (586 rows x 23 cols) -- exclusive EXACTSALES column
3. Planilha5 (96 rows x 27 cols)
4. Planilha4 (529 rows x 27 cols)

**Confidence:** HIGH -- data already extracted and classified in prior session.

### Source 2: Deskrio (Plan 04-02)

**Location:** `c:/Users/User/OneDrive/Area de Trabalho/PASTA G (CENTRAL INTERNO)/EXTRACAO DE DADOS/DesckRio/`
**Records:** 5,329 tickets / 77,805 messages / 5,425 conversations
**Period:** Jan 2025 - Jan 2026
**Files found:**
- `CONTATOS DESKRIO .xlsx` (1MB) -- structured ticket data
- `Contatos Mais Granel.xlsx` (914KB) -- related contacts
- `EXPORT TICKTES/` folder with subfolders: Atendimento Dezembro 1, Atendimento Dezembro 2, Atendimentos Dai, mensagens-maisgranel-vitao, Notebooklm
- `ANALISES 2025/` folder with:
  - `jK5Yn_1750852676007_Messages - Central Vitao.csv` (13MB) -- raw message export
  - `analise txt deskrio.xlsx` (3.6MB) -- analyzed data
  - `analise txt deskrio.txt` (12.7MB) -- raw text analysis
  - `Relatorio de Atendimento e Estatisticas Tickets DeskRio 2025.xlsx` (26KB) -- statistics
  - Various consultant-specific files (manu, helder)

**Granularity decision (Claude's discretion):** Use CONVERSATION level (5,425 records), NOT message level. Each conversation = 1 LOG record with aggregated outcome.

**Confidence:** MEDIUM -- files exist and are mapped, but exact schema of ticket exports needs inspection during implementation.

### Source 3: Retroactive Contacts + Julio (Plan 04-03)

**Records target:** 3,540 contacts to generate synthetically
**Logic:** 866 SAP sales x ~11.1 attendances/sale = ~9,612 total needed. After CONTROLE_FUNIL (10,544) and Deskrio overlap, remaining gap = ~3,540 synthetic records.
**Anchor:** 866 real SAP sales from `data/sources/sap/BASE_SAP_VENDA_MES_A_MES_2025.xlsx`
**Julio special case:** 105 SAP sales confirmed. 1,814 interactions in CONTROLE_FUNIL. Need complete synthetic history since Sep/2025 (prospection, contacts, funnel).
**GENOMA COMERCIAL templates:** 200+ notes across 6 categories, 6 journey types (A-F), statistical distributions for channels, results, time-of-day.

**Confidence:** HIGH for SAP anchor data. MEDIUM for synthetic generation quality (depends on algorithm implementation).

### Source 4: DRAFT2 Real Data

**File:** `data/sources/drafts/DRAFT2_POPULADO_DADOS_REAIS_v3.xlsx`
**Records:** 6,775 real records (440 confirmed from Feb/2026)
**Role:** Validation reference. Distribution benchmarks for synthetic calibration:
- CONSULTOR: Manu 30.2%, Larissa 25.0%, Daiane 25.2%, Julio 19.5%
- SITUACAO: ATIVO 34.3%, INAT.ANT 18.6%, EM RISCO 15.0%, NOVO 12.5%, INAT.REC 11.8%, PROSPECT 7.7%
- RESULTADO: RELACIONAMENTO 13.2%, ORCAMENTO 12.0%, EM ATENDIMENTO 10.7%, VENDA/PEDIDO 10.7%, etc.

**Confidence:** HIGH -- already validated and analyzed.

---

## Code Examples

### Example 1: 3-Tier Classification (from CONTROLE_FUNIL extraction)

```python
# Source: LOG_CONVERSA_EXTRACAO_CONTROLE_FUNIL_JAN2026.md, Marco 4
import re

VENDEDORES_FICTICIOS = [
    "JOAO SILVA", "PEDRO OLIVEIRA", "MARIA SANTOS",
    "ANA COSTA", "CARLOS FERREIRA", "LUCAS ALMEIDA"
]

VENDEDORES_REAIS = [
    "LARISSA PADILHA", "MANU DITZEL", "JULIO GADRET",
    "CENTRAL - DAIANE", "DAIANE STAVICKI", "HELDER BRUNKOW",
    "LORRANY", "LEANDRO GARCIA", "TIME"
]

NOTAS_SINTETICAS_PADROES = [
    "primeiro contato com prospect",
    "follow-up apos primeiro contato",
    "material de marketing enviado",
    "apresentacao de catalogo",
    "envio de proposta comercial",
    "acompanhamento da proposta",
    "negociacao em andamento",
    "suporte pos-venda",
    "cliente solicitou 2a via",
    "cliente pediu rastreamento",
    "follow-up cs",
    "verificar reposicao"
]

def classify_record(cnpj, nome, vendedor, nota):
    """Classify a record as REAL, SINTETICO, or ALUCINACAO."""
    cnpj_clean = re.sub(r'[^0-9]', '', str(cnpj))

    # ALUCINACAO checks
    if len(cnpj_clean) < 14:
        return 'ALUCINACAO', 'CNPJ invalido (<14 digitos)'
    if re.match(r'CLIENTE\s*\d+', str(nome).upper()):
        return 'ALUCINACAO', 'Nome padrao CLIENTE+numero'
    if str(vendedor).upper().strip() in [v.upper() for v in VENDEDORES_FICTICIOS]:
        return 'ALUCINACAO', 'Vendedor ficticio'

    # SINTETICO checks
    nota_lower = str(nota).lower().strip()
    for padrao in NOTAS_SINTETICAS_PADROES:
        if padrao in nota_lower:
            return 'SINTETICO', f'Nota generica: {padrao}'
    if len(str(nota).strip()) < 15:
        return 'SINTETICO', 'Nota curta (<15 chars)'

    # REAL: passes all checks
    return 'REAL', 'Contextual note with specific details'
```

### Example 2: LOG 20-Column Record Construction

```python
# Source: SKILL_LOG_DRAFT_PIPELINE.md
from motor_regras import motor_de_regras, dia_util, definir_consultor

LOG_COLUMNS = [
    'DATA',              # A - date
    'CONSULTOR',         # B - dropdown
    'NOME FANTASIA',     # C - formula/text
    'CNPJ',              # D - text 14 digits
    'UF',                # E - formula/text
    'REDE/REGIONAL',     # F - formula/text
    'SITUACAO',          # G - formula/text
    'WHATSAPP',          # H - SIM/NAO
    'LIGACAO',           # I - SIM/NAO
    'LIGACAO ATENDIDA',  # J - SIM/NAO/N/A
    'TIPO ACAO',         # K - ATIVO/RECEPTIVO
    'TIPO DO CONTATO',   # L - 7 options
    'RESULTADO',         # M - 12 options
    'MOTIVO',            # N - 10 options
    'FOLLOW-UP',         # O - date (calculated)
    'ACAO',              # P - text (calculated)
    'MERCOS ATUALIZADO', # Q - SIM/NAO
    'FASE',              # R - formula/text
    'TENTATIVA',         # S - formula/text
    'NOTA DO DIA',       # T - text
]

def make_log_record(data, cnpj, consultor, resultado, nota,
                    whatsapp='SIM', ligacao='NAO', lig_atendida='N/A',
                    tipo_acao='ATIVO', motivo='', mercos='SIM',
                    nome='', uf='', rede='', situacao=''):
    """Create a single LOG record in the 20-column format."""

    # Run motor de regras for derived fields
    regras = motor_de_regras(situacao, resultado)

    # Calculate follow-up date
    follow_up = dia_util(data, regras.get('follow_up_dias', 0)) if regras.get('follow_up_dias', 0) > 0 else None

    return {
        'DATA': data,
        'CONSULTOR': consultor,
        'NOME FANTASIA': nome,
        'CNPJ': normalize_cnpj(cnpj),
        'UF': uf,
        'REDE/REGIONAL': rede or 'DEMAIS CLIENTES',
        'SITUACAO': situacao,
        'WHATSAPP': whatsapp,
        'LIGACAO': ligacao,
        'LIGACAO ATENDIDA': lig_atendida if ligacao == 'SIM' else 'N/A',
        'TIPO ACAO': tipo_acao,
        'TIPO DO CONTATO': regras.get('tipo_contato', ''),
        'RESULTADO': resultado,
        'MOTIVO': motivo,
        'FOLLOW-UP': follow_up,
        'ACAO': regras.get('acao_futura', ''),
        'MERCOS ATUALIZADO': mercos,
        'FASE': regras.get('fase', ''),
        'TENTATIVA': regras.get('tentativa', ''),
        'NOTA DO DIA': nota,
    }
```

### Example 3: Channel Probability for Synthetic Records

```python
# Source: GENOMA_COMERCIAL_VITAO360.md Section 4.4
import random

def generate_channels():
    """Generate realistic WhatsApp/Ligacao/Lig.Atendida combination."""
    # WhatsApp: 98.3% SIM
    whatsapp = 'SIM' if random.random() < 0.983 else 'NAO'

    # Ligacao: 49.7% SIM
    ligacao = 'SIM' if random.random() < 0.497 else 'NAO'

    # Ligacao Atendida: 20% of ligacoes atendidas
    if ligacao == 'SIM':
        lig_atendida = 'SIM' if random.random() < 0.20 else 'NAO'
    else:
        lig_atendida = 'N/A'

    return whatsapp, ligacao, lig_atendida

def generate_tipo_acao(resultado):
    """
    ATIVO (consultant initiated) vs RECEPTIVO (client initiated).
    Pre-sale: 100% ATIVO
    Sale: 80% ATIVO, 20% RECEPTIVO
    Post-sale/Support: 30% ATIVO, 70% RECEPTIVO
    Material MKT: 100% RECEPTIVO
    """
    RECEPTIVO_RESULTS = ['SUPORTE']
    MIXED_RESULTS = ['VENDA / PEDIDO']

    if resultado in RECEPTIVO_RESULTS:
        return 'RECEPTIVO' if random.random() < 0.70 else 'ATIVO'
    elif resultado in MIXED_RESULTS:
        return 'ATIVO' if random.random() < 0.80 else 'RECEPTIVO'
    else:
        return 'ATIVO'
```

### Example 4: Monthly Distribution Enforcement

```python
# Source: GENOMA_COMERCIAL_VITAO360.md Section 5.4 / CONTEXT.md
MONTHLY_TARGETS_2025 = {
    1: 156, 2: 269, 3: 442, 4: 596, 5: 862,
    6: 1203, 7: 958, 8: 1244, 9: 1185, 10: 1395,
    11: 1528, 12: 796
}

MONTHLY_SALES_2025 = {
    2: 1, 3: 17, 4: 53, 5: 78, 6: 111,
    7: 84, 8: 113, 9: 104, 10: 123, 11: 133, 12: 49
}

def validate_monthly_distribution(records):
    """Ensure generated records match expected monthly distribution."""
    from collections import Counter
    monthly = Counter()
    for r in records:
        if hasattr(r['DATA'], 'month'):
            monthly[r['DATA'].month] += 1

    for month, target in MONTHLY_TARGETS_2025.items():
        actual = monthly.get(month, 0)
        tolerance = 0.15  # 15% tolerance
        if abs(actual - target) / target > tolerance:
            print(f"WARNING: Month {month}: {actual} records vs {target} target "
                  f"(deviation {abs(actual-target)/target:.1%})")
```

---

## Existing Codebase Analysis

### What Already Exists (REUSE)

| Module | Path | What It Does | Reuse How |
|--------|------|-------------|-----------|
| `motor_regras.py` | `scripts/motor_regras.py` | Full rule engine: RESULTADO -> all derived fields | Import directly in Phase 4 scripts |
| `v3_styles.py` | `scripts/v3_styles.py` | All Excel formatting constants | Import for LOG tab formatting |
| `v3_log.py` | `scripts/v3_log.py` | LOG tab structure builder (24 cols) | **CONFLICT: Uses 24-col layout (REGRAS v2) but SKILL_LOG_DRAFT_PIPELINE.md specifies 20 cols. See Open Questions.** |
| `v3_draft2.py` | `scripts/v3_draft2.py` | DRAFT 2 tab builder | Reference for column structure |
| Phase 2 merge scripts | `scripts/phase02_faturamento/` | SAP+Mercos merge pipeline | Reuse `normalize_cnpj()`, JSON intermediate pattern |
| Phase 3 populate scripts | `scripts/phase03_timeline/` | CARTEIRA formula population | Reference for openpyxl formula patterns |

### What Needs To Be Built (NEW)

| Component | Purpose | Dependencies |
|-----------|---------|-------------|
| `_helpers.py` | Shared utilities: classify_record(), make_dedup_key(), note_template_manager | motor_regras.py |
| `01_process_controle_funil.py` | ETL from 42-col CONTROLE_FUNIL to 20-col LOG format | _helpers.py, motor_regras.py |
| `02_process_deskrio.py` | Parse Deskrio tickets/conversations to LOG format | _helpers.py |
| `03_generate_synthetic.py` | SAP-anchored funnel reconstruction + non-sale activities | _helpers.py, motor_regras.py, GENOMA templates |
| `04_dedup_validate.py` | Cross-source dedup + validation + write to LOG | All above + v3_styles.py |

---

## Key Discrepancies Found

### LOG Column Count: 20 vs 24

**SKILL_LOG_DRAFT_PIPELINE.md** specifies LOG with **20 columns** (A-T), 5 blocks.
**v3_log.py** (existing code) builds LOG with **24 columns** matching DRAFT 2 structure.
**REGRAS_INTELIGENCIA_CRM_VITAO_v2.md** says LOG = "same structure as DRAFT 2 24 columns."

**Resolution:** The CONTEXT.md states "LOG = 20 columns, 5 blocks" as a locked decision. The SKILL_LOG_DRAFT_PIPELINE.md (most recent technical spec) defines the 20-column LOG. The 24-column LOG in v3_log.py was built to mirror DRAFT 2 but the user has since refined the spec.

**Recommendation:** Use 20-column LOG structure from SKILL_LOG_DRAFT_PIPELINE.md. The 4 columns removed vs DRAFT 2 are:
- TEMPERATURA (stays in CARTEIRA/AGENDA only, not in LOG)
- GRUPO DASH (calculated for DASH, not stored in LOG)
- SINALEIRO CICLO (stays in CARTEIRA)
- SINALEIRO META (stays in CARTEIRA)

The existing v3_log.py will need to be updated to match the 20-column spec.

### DRAFT 2 Column Order: v2 Doc vs Real Files

The REGRAS v2 document (section 8) uses a different column order than the real DRAFT 2 files. The DOC_DEFINITIVA (11/02/2026) is authoritative. Key differences:
- v2: DATA, CNPJ, NOME, UF, CONSULTOR, RESULTADO...
- Real/DOC_DEFINITIVA: DATA, CONSULTOR, NOME, CNPJ, UF, REDE...

**Resolution:** Follow DOC_DEFINITIVA column order. This is already stated in CONTEXT.md.

### Consultant Name: "CENTRAL - DAIANE" vs "DAIANE STAVICKI"

CONTEXT.md uses both interchangeably. The motor_regras.py returns "DAIANE STAVICKI" but some data has "CENTRAL - DAIANE".

**Recommendation:** Standardize on "DAIANE STAVICKI" in the LOG (matching motor_regras.py output). Add normalization: if input is "CENTRAL - DAIANE" -> output "DAIANE STAVICKI".

### RESULTADO Options: 12 vs 13 vs 14

Different documents list different counts:
- DOC_DEFINITIVA Section 3: 12 options (no CS, no NUTRICAO)
- GENOMA COMERCIAL Section 4.1: 14 options (includes CS, NUTRICAO)
- CONTEXT.md: 13 options

**Recommendation:** Use DOC_DEFINITIVA's 12 options for the LOG dropdown, since CS and NUTRICAO can be represented within the existing 12 (CS maps to RELACIONAMENTO, NUTRICAO maps to FOLLOW UP 15 or PERDA/FECHOU LOJA context).

---

## Validation Rules Summary

### Mandatory Validations (run in Plan 04-04)

1. **Two-Base Architecture:** ZERO financial values in LOG (no column should contain R$, all amounts = 0)
2. **CNPJ Format:** All CNPJs are exactly 14 digits, zero-padded, no punctuation
3. **No Weekends:** All DATA values have weekday() < 5
4. **Max 40/day/consultant:** GROUP BY (CONSULTOR, DATA) -- COUNT <= 40
5. **VENDA needs ORCAMENTO:** Every VENDA/PEDIDO record must have an ORCAMENTO for same CNPJ within D-1 to D-3
6. **PROSPECT needs CADASTRO:** Every VENDA/PEDIDO for a PROSPECT must have CADASTRO for same CNPJ before VENDA
7. **No duplicate dedup key:** DATA+CNPJ+RESULTADO must be unique
8. **Julio Gadret normalized:** Only one spelling of "JULIO GADRET"
9. **Helder timeline:** No Helder records after 2025-08-31
10. **Julio timeline:** No Julio records before 2025-09-01
11. **Monthly distribution:** Within 15% of target for each month
12. **Note variety:** No note template used more than 3 times
13. **MOTIVO only when needed:** MOTIVO only filled when RESULTADO is a non-sale outcome
14. **LIGACAO ATENDIDA logic:** If LIGACAO=NAO then LIG.ATENDIDA=N/A. If LIGACAO=SIM then LIG.ATENDIDA is SIM or NAO.
15. **Total count >= 11,758:** Final LOG must have at least 11,758 records

### Distribution Validations (benchmarks from DRAFT 2 real data)

| Dimension | Expected Distribution | Tolerance |
|-----------|----------------------|-----------|
| WhatsApp = SIM | 98.3% | +/- 2% |
| Ligacao = SIM | ~50% | +/- 5% |
| Ligacao Atendida = SIM (of ligacoes) | ~20% | +/- 5% |
| MERCOS ATUALIZADO = SIM | ~65% | +/- 5% |
| Resultado EM ATENDIMENTO | 40-50% | - |
| Resultado VENDA/PEDIDO | 8-12% | - |
| Resultado ORCAMENTO | 10-15% | - |
| Resultado SUPORTE | 10-15% | - |
| Day-of-week Mon | ~22% | +/- 3% |
| Day-of-week Fri | ~17% | +/- 3% |

---

## Open Questions

1. **LOG Column Count: 20 or 24?**
   - What we know: SKILL_LOG_DRAFT_PIPELINE.md says 20, v3_log.py implements 24, CONTEXT.md says 20.
   - What's unclear: Whether the user explicitly confirmed 20 vs 24 as final.
   - Recommendation: Use 20 columns (SKILL_LOG_DRAFT_PIPELINE.md) since CONTEXT.md references "LOG = 20 columns, 5 blocks" as a decision. Update v3_log.py accordingly.

2. **Deskrio Data Format**
   - What we know: Files exist in multiple formats (xlsx, csv, txt). The main CSV is 13MB with message-level data.
   - What's unclear: Exact column schema of the ticket export xlsx files. Whether CNPJs are present in Deskrio data or only phone numbers.
   - Recommendation: During Plan 04-02 implementation, first inspect the CONTATOS DESKRIO.xlsx headers and sample data to determine matching strategy (CNPJ direct match vs phone-to-CNPJ lookup).

3. **CONTROLE_FUNIL SINTETICO Records (1,349)**
   - What we know: Classified as SINTETICO but not ALUCINACAO. They have valid CNPJs.
   - What's unclear: Should they be included in the LOG as-is, regenerated with better quality, or excluded?
   - Recommendation: Include them but upgrade their notes using GENOMA COMERCIAL templates. Their structural data (DATE, CNPJ, RESULTADO) is valid -- only the notes are generic.

4. **Consultant Name for LOG: "DAIANE STAVICKI" or "CENTRAL - DAIANE"?**
   - What we know: Both forms appear in different sources. motor_regras.py uses "DAIANE STAVICKI".
   - What's unclear: Which form the user wants in the final LOG.
   - Recommendation: Use "DAIANE STAVICKI" (matching motor_regras.py), but confirm with user during planning.

5. **Jan-Feb 2026 Data Volume**
   - What we know: 440 real records exist for Feb/2026 in DRAFT2. Jan/2026 had consultants starting on different dates (Manu+Larissa Jan 5, Daiane+Julio Jan 12).
   - What's unclear: Exact target record count for Jan+Feb 2026. Whether they should use same synthetic generation or just integrate real DRAFT2 data.
   - Recommendation: For Jan 2026, use partial month based on SAP data. For Feb 2026, integrate the 440 real DRAFT2 records + any additional SAP-anchored generation.

---

## Discretion Recommendations

### 1. Treatment of 558 Hallucinations

**Recommendation: Completely exclude from LOG.** Do not include as flagged records. They have invalid CNPJs, fictional consultant names, and fake client names. Including them even with a flag would pollute the data. Instead, the synthetic generation in Plan 04-03 will replace their volume with properly generated records anchored to real SAP sales.

### 2. 3-Tier Classification Visibility

**Recommendation: Metadata column (hidden by default).** Add column U "ORIGEM_DADO" to LOG (making it 21 columns, or integrate into the NOTA DO DIA prefix). Values: "REAL", "SINTETICO". This enables filtering for audits without cluttering the daily view. Apply conditional formatting: REAL cells = green background, SINTETICO = yellow background. ALUCINACAO never enters LOG.

Alternative considered: Completely invisible. Rejected because P10 (100% rastreabilidade) requires knowing data origin.

### 3. Deskrio Granularity

**Recommendation: 1 record per conversation (not per message).** The 5,425 conversations map naturally to LOG records (1 attendance = 1 interaction unit). Messages within a conversation are detail that belongs in the NOTA DO DIA text, not separate records. This avoids 77K record inflation.

### 4. Algorithm for Human Variation in Synthetics

**Recommendation: Weighted random with constraints.** Use the GENOMA COMERCIAL Section 11 pseudo-code as the base algorithm, with these enhancements:
- Journey length: Use normal distribution around the expected mean (e.g., Journey A: mean=10, std=2, min=6, max=15)
- Day offsets: Add jitter (+/- 1 day) to standard offsets
- Channel selection: Per-record random with documented probabilities
- Note selection: Weighted random without replacement (reset pool after exhaustion)
- Missing data: 5-10% of optional fields (MOTIVO, MERCOS ATUALIZADO) left intentionally blank to simulate human omission
- Consultant capacity: Respect daily 40-record cap with realistic variance (average 25-35/day, not always 40)

---

## Sources

### Primary (HIGH confidence)

- `GENOMA_COMERCIAL_VITAO360.md` (c:/Users/User/Downloads/) -- Complete operational DNA: journeys, templates, rules, distributions
- `DOC_DEFINITIVA_AGENDA_DRAFT2.md` (PASTA DE APOIO PROJETO/) -- Authoritative column specs (24 cols DRAFT 2, 24 cols AGENDA)
- `SKILL_LOG_DRAFT_PIPELINE.md` (CONSTURCAO DRAFT/) -- Technical spec: LOG 20 cols, DRAFT 2 27 cols, formulas
- `REGRAS_INTELIGENCIA_CRM_VITAO_v2.md` (PASTA DE APOIO PROJETO/) -- Master document: 33 sections, full motor de regras
- `CORRECAO_ALUCINACOES_DADOS_REAIS.md` (PASTA G/ANALISES/) -- Verified real data: 866 sales, vendor performance
- `LOG_CONVERSA_EXTRACAO_CONTROLE_FUNIL_JAN2026.md` (AUDITORIA/) -- Extraction methodology and classification criteria
- `scripts/motor_regras.py` -- Existing Python motor implementation
- `scripts/v3_log.py` -- Existing LOG tab builder
- `scripts/v3_draft2.py` -- Existing DRAFT 2 tab builder
- `scripts/v3_styles.py` -- Existing formatting constants
- `scripts/phase02_faturamento/` -- Existing SAP+Mercos merge pipeline

### Secondary (MEDIUM confidence)

- `04-CONTEXT.md` -- User decisions aggregated from /gsd:discuss-phase (enriched from 95 documents)
- `DRAFT2_POPULADO_DADOS_REAIS_v3.xlsx` -- Real Feb/2026 distribution benchmarks (440 records)

### Tertiary (LOW confidence)

- Deskrio file schemas -- Inspected folder structure but not parsed actual data. Schema confirmation needed during implementation.
- Jan-Feb 2026 target volumes -- Extrapolated from 2025 patterns. Need user confirmation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools are already in use in the project (openpyxl, Python 3.12, stdlib)
- Architecture: HIGH -- patterns established in Phases 1-3; motor_regras.py and v3_styles.py are proven
- Data sources: HIGH for CONTROLE_FUNIL (already extracted), MEDIUM for Deskrio (folder mapped, schema unconfirmed)
- Synthetic generation: MEDIUM -- algorithm design is sound (GENOMA COMERCIAL provides complete spec) but implementation quality depends on execution
- Pitfalls: HIGH -- documented from real project history (742% bug, weekend bug, alucinacao patterns)

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (30 days -- stable domain, no external dependency changes expected)
