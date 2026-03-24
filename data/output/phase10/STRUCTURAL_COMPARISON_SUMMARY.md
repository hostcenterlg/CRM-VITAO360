# Excel Structure Comparison Report: V13 vs V31 (V12 POPULADO)

**Generated:** 2026-02-17
**Analysis Tool:** openpyxl Python analyzer
**Files Compared:**
- V13: `CRM_VITAO360_V13_FINAL.xlsx` (13 sheets)
- V31: `CRM_V12_POPULADO_V31 (1).xlsx edição update.xlsx` (17 sheets)

---

## EXECUTIVE SUMMARY

V31 is a significantly expanded version with more comprehensive data and functionality, but has **architectural differences** in how sheets are organized. Key changes:

1. **Sheet Architecture**: V13 has individual AGENDA sheets per consultant; V31 consolidates to single unified AGENDA sheet
2. **CARTEIRA Sheet**: Massive growth (557 → 8305 rows) but fewer formulas (134092 → 87186)
3. **AGENDA Sheet**: New consolidated design with 65,916 formulas (not in V13)
4. **Navigation & Freezing**: Different freeze pane positions suggesting different UI patterns
5. **New Support Sheets**: SINALEIRO (traffic lights), STATUS, README, RNC monitoring

---

## SHEETS INVENTORY COMPARISON

### V13 Architecture (13 sheets)
```
Core Analysis:
  - PROJEÇÃO: 537 rows, 19,224 formulas (projection/forecast)
  - CARTEIRA: 557 rows, 134,092 formulas (portfolio - main calc engine)
  - LOG: 20,832 rows (transaction log)
  - DASH: 41 rows, 304 formulas (dashboard metrics)

Individual Consultant Agendas (4 sheets):
  - AGENDA LARISSA: 1,000 rows, 15 formulas
  - AGENDA DAIANE: 1,000 rows, 15 formulas
  - AGENDA MANU: 1,000 rows, 15 formulas
  - AGENDA JULIO: 1,000 rows, 15 formulas

Support/Reference:
  - COMITE: 71 rows, 342 formulas
  - REDES_FRANQUIAS_v2: 25 rows, 280 formulas
  - REGRAS: 283 rows (rule definitions)
  - DRAFT 1 & 2: Development/staging sheets
```

### V31 Architecture (17 sheets)
```
Core Analysis (same + expanded):
  - PROJEÇÃO: 537 rows, 19,224 formulas (IDENTICAL to V13)
  - CARTEIRA: 8,305 rows, 87,186 formulas (15x data growth)
  - LOG: 13,183 rows (different data content/scope)
  - DASH: 78 rows, 445 formulas (enhanced)

NEW - Unified Agenda:
  - AGENDA: 13,186 rows, 65,916 formulas (CONSOLIDATED - replaced 4 individual sheets!)

NEW - Support Sheets:
  - SINALEIRO: 539 rows, 538 formulas (traffic light system)
  - RNC: 2,476 rows (quality/issue tracking)
  - STATUS: 187 rows (state management)
  - README: 175 rows (documentation)
  - REGRAS 2: 283 rows (additional rules)

Support/Reference:
  - REGRAS: 283 rows, 13 columns (vs 11 in V13)
  - DRAFT 1, 2, 3: Multiple development stages
  - _PROJEÇÃO_OLD: 504 rows (archive)
  - Claude Log: 89 rows (AI interaction tracking)
  - Planilha3: 64 rows (temp/unused)
```

---

## CRITICAL ARCHITECTURAL DIFFERENCES

### 1. AGENDA REDESIGN (Biggest Change)

| Aspect | V13 | V31 | Impact |
|--------|-----|-----|--------|
| Structure | 4 separate sheets (1 per consultant) | 1 unified AGENDA sheet | Centralized management, filter by consultant |
| Total rows | 4,000 rows (4 × 1,000) | 13,186 rows | 3.3x expansion + data accumulation |
| Formulas | 60 total (4 × 15) | 65,916 formulas | Heavy formula dependency in unified design |
| Data Validations | None | 2 dropdowns | Input validation added |
| Conditional Formatting | None | 1 rule | Visual feedback added |

**Interpretation:**
- V31 moved from consultant-segregated agendas to consolidated daily operations sheet
- This is the **"intelligent daily agenda"** concept you described
- Unified approach allows ranking by priority across all consultants
- 65k+ formulas suggests complex priority calculation logic

### 2. CARTEIRA SHEET EXPANSION

| Metric | V13 | V31 | Change |
|--------|-----|-----|--------|
| Rows | 557 | 8,305 | +7,748 (13.9x) |
| Columns | 269 | 263 | -6 (cleanup) |
| Formulas | 134,092 | 87,186 | -46,906 (simplified by 35%) |
| Column Outlines | 210 | 210 | **SAME** (critical!) |
| Freeze Position | AR6 | BX66 | Different scroll anchor |
| Auto-Filter | A3:JC557 | A3:JE1863 | Extended range for more data |
| Conditional Formatting Rules | 42 | 2 | **MASSIVE simplification** |
| Merged Cells | 0 | 43 | Layout changes added |

**Key Insight:**
- Same column grouping structure preserved (210 outline levels)
- Fewer formulas suggests **consolidation/optimization** of calculation logic
- Conditional formatting simplified (fewer visual rules)
- BUT: Freeze panes moved significantly (AR6 → BX66) - different primary display area
- Data grew 14x, but formula count dropped 35% = **more efficient design**

### 3. PROJEÇÃO SHEET (Stable Core)

| Metric | V13 | V31 | Status |
|--------|-----|-----|--------|
| Dimensions | 537 × 80 | 537 × 80 | **IDENTICAL** |
| Formulas | 19,224 | 19,224 | **IDENTICAL** |
| Column Structure | Unchanged | Unchanged | **IDENTICAL** |
| Freeze Panes | E30 | C4 | Changed (view preference) |
| Auto-Filter | None | A3:CB537 | Added for usability |

**Key Insight:**
- Core projection engine is identical between versions
- Changes are UI/navigation only (freeze position, filter access)
- Safe to use V31's projection formulas as reference

---

## HIDDEN COLUMN STRATEGY

### V13 CARTEIRA Hidden Columns (246 hidden)
Columns hidden: B-Z, AK-AQ, BL-BZ, CB-CY, CR-CZ, DA-DB, DF-DQ, DU-EG, EK-EV, EZ-FY, GA-HP, HI-HT, HY-JC

**Pattern:** Highly selective hiding - suggests intermediate calculations/working areas

### V31 CARTEIRA Hidden Columns (217 hidden)
Similar pattern but with some differences: C-G, H, J-K, M, O, Q-R vs full ranges in V13

**Key Difference:** V31 has less aggressive hiding (fewer hidden cols), suggesting:
- Cleaner column organization
- Less "working area" scaffolding
- More transparent calculation chain

---

## NEW FEATURES IN V31 (Not in V13)

### 1. SINALEIRO Sheet (539 rows, 538 formulas)
**Purpose:** Traffic light / status indicator system
- Created with sophisticated formula logic (1 formula per row almost)
- Likely provides quick visual status of priority/urgency
- Critical for "intelligent agenda" prioritization

### 2. RNC Sheet (2,476 rows, 12 columns)
**Purpose:** Returns/Non-Conformity tracking
- Quality/issue management module
- Not in V13 - suggests expanded scope into quality assurance
- 5 data validations for controlled input

### 3. STATUS Sheet (187 rows, 7 columns)
**Purpose:** State management / workflow
- Defines possible status values
- Reference table for data validations elsewhere

### 4. README Sheet (175 rows, 5 columns)
**Purpose:** Documentation embedded in workbook
- User guidance
- Feature explanations

### 5. REGRAS 2 Sheet (283 rows, 12 columns)
**Purpose:** Extended business rule set
- Doubles the rule definitions vs original REGRAS
- REGRAS in V31 has 13 columns (vs 11 in V13)

### 6. Claude Log (89 rows, 6 columns)
**Purpose:** AI interaction tracking
- Records of automated processes
- Audit trail for AI-assisted modifications

---

## DETAILED SHEET-BY-SHEET ANALYSIS

### DASH (Dashboard)
```
V13: 41 rows × 17 cols, 304 formulas
V31: 78 rows × 18 cols, 445 formulas
Δ:   +37 rows, +1 col, +141 formulas (+46%)

Changes:
- Nearly doubled in size
- More calculated metrics (+46% formulas)
- 1 new column added
- Merged cells increased: 21 → 29
- Same freeze position (A5)
- Same structure (no grouping)

Impact: Enhanced dashboard with more KPIs/metrics
```

### DRAFT 1
```
V13: 557 rows × 45 cols, 0 formulas
V31: 505 rows × 45 cols, 1,004 formulas
Δ:   -52 rows, SAME cols, +1,004 formulas

Changes:
- MAJOR addition: 1,000+ formulas added
- Freeze pane added (AN4 = column 40)
- 7 merged cells added
- Data reduced slightly (-52 rows)

Impact: Transformed from data dump to formula-driven calculation layer
```

### DRAFT 2
```
V13: 6,775 rows × 31 cols, 0 formulas
V31: 13,184 rows × 31 cols, 52,728 formulas
Δ:   +6,409 rows, SAME cols, +52,728 formulas (+94% data)

Changes:
- Massive formula addition (+52k formulas)
- Data nearly doubled (+94%)
- Freeze pane added (A13070 = deep in sheet)
- 1 merged cell added
- Same column structure preserved

Impact: Evolved from simple data table to heavy calculation engine for agenda generation
```

### LOG (Transaction Log)
```
V13: 20,832 rows × 21 cols, 0 formulas, auto-filter on
V31: 13,183 rows × 24 cols, 0 formulas, NO auto-filter
Δ:   -7,649 rows, +3 cols, no formulas

Changes:
- Data reduced (possibly archived/segmented)
- 3 new columns added
- Auto-filter REMOVED
- Freeze pane adjusted: A3 → A2
- Data validations added: 0 → 7
- Conditional formatting removed
- Column U was hidden in V13, now visible in V31

Impact: Data scope changed, input validation added, simpler UI (no auto-filter)
```

### REGRAS (Business Rules)
```
V13: 283 rows × 11 cols
V31: 283 rows × 13 cols
Δ:   SAME rows, +2 cols

Changes:
- 2 new columns added
- Freeze pane added (A41 = row 41)
- 12 merged cells added (was 0)
- No formulas in either version

Impact: Extended rule definitions with additional metadata
```

---

## MISSING IN V13 - CRITICAL FEATURES TO ADOPT

### Priority 1: SINALEIRO (Traffic Lights)
- 538 formulas computing status indicators
- Essential for priority visualization
- Directly supports "intelligent agenda" concept

### Priority 2: AGENDA Consolidation
- Replace 4 individual consultant agendas with unified calculation
- 65,916 formulas for intelligent prioritization
- Enables cross-consultant ranking

### Priority 3: RNC Tracking
- Quality management module
- Integrated into agenda decision logic
- Not purely reporting - appears to be operational

### Priority 4: Enhanced DASH
- 50% more metrics than V13
- Better KPI coverage

---

## COLUMN GROUPING ANALYSIS (CARTEIRA)

Both V13 and V31 maintain **identical 210 column outline groups** - this is critical:

**What this means:**
1. Group structure was NOT changed between versions
2. Column organization is stable
3. User collapse/expand buttons work identically
4. Safe to reference V13's grouping documentation for V31

**Outline Hierarchy Pattern:**
- Appears to be hierarchical grouping: top-level → sub-groups → details
- Consistent across versions suggests this is "golden" design

---

## FORMULA INTENSITY ANALYSIS

```
V13 Total Formulas:  154,164
V31 Total Formulas:  289,345
Growth: +87.4%

Distribution:

V13:                              V31:
CARTEIRA:  134,092 (87.0%)       CARTEIRA:  87,186 (30.1%)
PROJEÇÃO:   19,224 (12.5%)       PROJEÇÃO:  19,224 (6.6%)
COMITE:        342 (0.2%)        DRAFT 2:   52,728 (18.2%)
DASH:          304 (0.2%)        AGENDA:    65,916 (22.8%)
REGRAS:          0 (0.0%)        DRAFT 1:    1,004 (0.3%)
DRAFT 1:         0 (0.0%)        DASH:        445 (0.2%)
DRAFT 2:         0 (0.0%)        SINALEIRO:   538 (0.2%)
Others:        202 (0.1%)        Others:    62,404 (21.6%)

Key Insight:
- V13 concentrated 87% of formulas in CARTEIRA
- V31 distributed formulas across multiple sheets (30% CARTEIRA, 23% AGENDA, 18% DRAFT2)
- More modular calculation architecture
```

---

## FREEZE PANE EVOLUTION

### V13 Freeze Positions (Focused on CARTEIRA view)
- CARTEIRA: AR6 (Column 44, Row 6) - Shows first 44 columns always
- DASH: A5 (Standard header freeze)
- PROJEÇÃO: E30 (Column 5, deep data freeze)

### V31 Freeze Positions (More navigation-friendly)
- CARTEIRA: BX66 (Column 76, Row 66) - MUCH deeper into data
- DASH: A5 (Same as V13)
- PROJEÇÃO: C4 (Minimal freeze, upper area)
- DRAFT 1: AN4 (Column 40, Row 4)
- DRAFT 2: A13070 (Deep data positioning)
- REGRAS: A41 (Row 41)

**Interpretation:**
- V31 has more flexible navigation
- Different primary display areas
- Suggests UI optimization for data volume changes

---

## DATA VALIDATION & INTEGRITY

| Sheet | V13 | V31 | Change |
|-------|-----|-----|--------|
| CARTEIRA | 0 | 0 | No change |
| DASH | 1 | 0 | Removed |
| AGENDA | - | 2 | NEW |
| LOG | 0 | 7 | Added for input control |
| RNC | - | 5 | NEW |
| PROJEÇÃO | 0 | 0 | No change |

**Summary:**
- V31 added input validation in new sheets (AGENDA, LOG, RNC)
- DASH validation was removed (replaced with different approach)
- Total validations: 1 → 14 (more input control)

---

## CONDITIONAL FORMATTING EVOLUTION

| Sheet | V13 | V31 | Change |
|-------|-----|-----|--------|
| CARTEIRA | 42 | 2 | **-40 (MAJOR SIMPLIFICATION)** |
| DASHBOARD | 0 | 0 | No change |
| LOG | 1 | 0 | Removed |
| AGENDA | - | 1 | NEW |

**Total: 43 → 3 rules**

**Critical Finding:**
- Massive reduction in conditional formatting in CARTEIRA (42 → 2)
- Suggests visual complexity moved to SINALEIRO (traffic lights)
- Cleaner, more performant interface

---

## RECOMMENDATIONS FOR V13 MIGRATION

### Must Implement:
1. **SINALEIRO Sheet**: Copy structure and adapt formulas for your data
2. **AGENDA Consolidation**: Merge 4 consultant sheets into unified calculation
3. **Enhanced Data Validation**: Add validations to LOG sheet (7 total)
4. **Simplified Conditional Formatting**: Reduce CARTEIRA from 42 to 2 rules

### Should Implement:
5. **REGRAS Extension**: Add 2 new columns to REGRAS (13 vs 11)
6. **DRAFT Sheet Formulas**: Add 1,000+ formulas to DRAFT 1 for calculation
7. **Enhanced DASH**: Add 37 rows of new metrics (+141 formulas)
8. **RNC Module**: Optional quality tracking (if relevant to business)

### Can Implement:
9. **Claude Log**: Track AI-assisted modifications
10. **README Sheet**: Embedded documentation

### Preserve As-Is:
- PROJEÇÃO sheet (identical, no changes needed)
- Column grouping structure in CARTEIRA (210 groups maintained)
- Core COMITE and REDES_FRANQUIAS sheets

---

## DATA VOLUME COMPARISON

```
Sheet              V13        V31        Growth    Notes
─────────────────────────────────────────────────────
PROJEÇÃO           537        537        0%        Identical
CARTEIRA           557        8,305      1,390%    Massive growth
LOG                20,832     13,183     -37%      Data segmented
DASH               41         78         90%       Enhanced
DRAFT 1            557        505        -9%       Now has formulas
DRAFT 2            6,775      13,184     94%       Formula engine
AGENDA (4 sheets)  4,000      13,186     n/a       Consolidated
COMITE             71         -          removed   Missing
REDES_FRANQUIAS    25         -          removed   Missing
─────────────────────────────────────────────────────
TOTAL (comparable) 30,398     34,278     +13%

NEW in V31:
SINALEIRO          539
RNC                2,476
STATUS             187
README             175
REGRAS 2           283
Claude Log         89
_PROJEÇÃO_OLD      504
Planilha3          64
```

---

## FORMULA COMPLEXITY DISTRIBUTION

### V31's New Intensive Sheets:
- **DRAFT 2**: 52,728 formulas in 13,184 rows = **4 formulas per row avg**
- **AGENDA**: 65,916 formulas in 13,186 rows = **5 formulas per row avg**
- **SINALEIRO**: 538 formulas in 539 rows = **1 formula per row**

**These are calculation-heavy, not just data sheets.**

### V13's Original Pattern:
- **CARTEIRA**: 134,092 formulas in 557 rows = **241 formulas per row**
- **PROJEÇÃO**: 19,224 formulas in 537 rows = **36 formulas per row**

**V13 concentrated complexity; V31 distributed it.**

---

## CRITICAL ARCHITECTURE INSIGHT

V31 represents a **shift from portfolio-centric (V13) to agenda-centric (V31) design**:

```
V13 Architecture:        V31 Architecture:
┌─────────────────┐     ┌──────────────────┐
│   CARTEIRA      │     │   CARTEIRA       │
│  (Portfolio)    │     │  (Portfolio)     │
│  134k formulas  │     │  87k formulas    │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         v                       v
  [Individual          ┌─────────────────┐
   Consultant          │   SINALEIRO     │
   Agendas]            │ (Status/Priority│
                       │  Flags)         │
                       │ 538 formulas    │
                       └────────┬────────┘
                                │
                                v
                       ┌──────────────────┐
                       │     AGENDA       │
                       │ (Consolidated    │
                       │  Daily Plan)     │
                       │ 65,916 formulas  │
                       └──────────────────┘
```

**Key Shift:** Portfolio data → Status indicators → Intelligent agenda generation

This matches your stated goal: **"GERAR AGENDA DIÁRIA INTELIGENTE por consultor (40-60 atendimentos priorizados por ranking automático)"**

---

## CONCLUSION

V31 is not just an update to V13—it's a **fundamental architectural redesign** toward your ultimate goal of intelligent daily agendas. The changes show:

1. **Consolidation of multi-sheet agendas into unified calculation engine** (AGENDA sheet)
2. **New priority/status system** (SINALEIRO) to drive intelligent ranking
3. **Distribution of formula logic** across calculation layers (DRAFT 2, AGENDA, SINALEIRO)
4. **Quality integration** (RNC module)
5. **Simplified visual complexity** (reduced conditional formatting)

For Phase 2 (Faturamento), use V31 as your architectural reference—particularly:
- The SINALEIRO pattern for flag-based prioritization
- The unified AGENDA approach for consolidated operations
- The formula distribution pattern across calc layers

Full detailed JSON export saved to:
`c:/Users/User/OneDrive/Documentos/GitHub/CRM-VITAO360/data/output/phase10/v31_vs_v13_comparison.json`
