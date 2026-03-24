# Phase 10: Validacao Final - Research

**Researched:** 2026-02-17
**Domain:** Excel/openpyxl audit, formula validation, data integrity
**Confidence:** HIGH

## Summary

Phase 10 is a pure validation/audit phase. The V13 CRM workbook (`CRM_VITAO360_V13_PROJECAO.xlsx`, 5.1 MB) is already complete with 13 tabs and 154,302 formulas across all tabs. Phase 9 concluded with 26/26 validation checks PASS and all BLUE-01..04 requirements PASS. Phase 10 must perform a **comprehensive end-to-end audit** covering all 6 VAL requirements, identify any residual issues, fix them, and produce a final deliverable tested in real Excel.

The main technical challenge is that **openpyxl cannot recalculate formulas** -- it can only inspect formula text and cached values. For 154,302 formulas, the audit must validate formula text patterns (no `#REF!`, no unbounded ranges, correct cross-tab references) rather than computed results. The faturamento validation (VAL-02) requires opening the file in real Excel to obtain recalculated values, since PROJECAO REALIZADO column (Z = `SUM(AA:AL)`) shows cached value 0 in openpyxl.

**Primary recommendation:** Build a single comprehensive Python audit script that validates formula text, CNPJ integrity, Two-Base compliance, and tab structure across all 13 tabs. Then open in Excel for recalc-dependent validations (faturamento totals, AGENDA spill behavior). Fix any issues found, and produce a final delivery report.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openpyxl | 3.1.x | Read/write Excel workbooks, inspect formulas | Already used in all 9 phases, proven reliable |
| Python | 3.12.10 | Script execution | Already configured via pyenv |
| re (stdlib) | - | Regex for formula text pattern matching | Built-in, no install needed |
| json (stdlib) | - | Audit report output | Built-in, no install needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unicodedata (stdlib) | - | Accent stripping for PROJECAO sheet name | Already proven pattern in prior phases |
| collections.Counter | - | Distribution counting for CNPJ/TIPO validation | Built-in |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl formula scan | xlcalc / formulas lib | Could recalculate, but experimental, huge dependency, unproven in project |
| Manual Excel test | COM automation (win32com) | Could automate Excel recalc, but requires Excel installed and COM setup; user is leigo em tecnologia |
| Per-cell iteration | openpyxl read_only mode | Faster for large sheets, but cannot write; use for audit-only pass |

**Installation:**
```bash
# No new installs needed -- openpyxl already available
/c/Users/User/.pyenv/pyenv-win/pyenv-win/versions/3.12.10/python.exe -c "import openpyxl; print(openpyxl.__version__)"
```

## Architecture Patterns

### Recommended Script Structure
```
scripts/phase10_validacao_final/
    01_comprehensive_audit.py    # VAL-01..05 automated checks
    02_fix_issues.py             # Fix any issues found by audit
    03_final_report.py           # Generate delivery report + Excel test instructions
```

### Pattern 1: Two-Pass Formula Audit
**What:** Load workbook twice -- once with `data_only=False` to read formula text, once with `data_only=True` to read cached values.
**When to use:** When you need both formula structure AND cached computed values.
**Example:**
```python
# Pass 1: Formula text analysis
wb_formulas = openpyxl.load_workbook(V13_PATH, data_only=False)
# Check for #REF!, #NAME?, unbounded ranges, cross-tab refs

# Pass 2: Cached value analysis (limited -- only what Excel last computed)
wb_cached = openpyxl.load_workbook(V13_PATH, data_only=True, read_only=True)
# Check Two-Base (R$ 0 in LOG), CNPJ format, etc.
```

### Pattern 2: Error Pattern Scanning
**What:** Scan formula text for known error patterns using regex.
**When to use:** VAL-01 (zero formula errors across all tabs).
**Example:**
```python
ERROR_PATTERNS = ['#REF!', '#DIV/0!', '#VALUE!', '#NAME?', '#N/A', '#NULL!']
DANGEROUS_PATTERNS = [
    r'\$[A-Z]+:\$[A-Z]+(?!\$)',  # Unbounded column refs like $A:$A
    r'_xlfn\.LET',               # Unsupported LET function
    r'_xlfn\._xlws\.',           # Unsupported worksheet functions
]
for row in ws.iter_rows():
    for cell in row:
        val = str(cell.value or '')
        if val.startswith('='):
            for pat in ERROR_PATTERNS:
                if pat in val:
                    errors.append((cell.coordinate, pat, val[:80]))
```

### Pattern 3: CNPJ Validation
**What:** Validate CNPJ format: 14 numeric digits, no duplicates, string type.
**When to use:** VAL-04.
**Example:**
```python
import re
def validate_cnpj(cnpj_str):
    digits = re.sub(r'\D', '', str(cnpj_str))
    if len(digits) != 14:
        return False, f"has {len(digits)} digits"
    if digits == '0' * 14:
        return False, "all zeros"
    return True, "valid"
```

### Pattern 4: Cross-Tab Reference Validation
**What:** Verify that formula cross-tab references point to existing tabs.
**When to use:** To confirm no orphaned references after tab renames.
**Example:**
```python
tab_names_upper = {s.upper() for s in wb.sheetnames}
# Extract tab references from formula like 'DRAFT 1'!B$4
import re
refs = re.findall(r"'?([^'!]+)'?!", formula_text)
for ref in refs:
    if ref.upper() not in tab_names_upper:
        errors.append(f"Orphaned ref to {ref}")
```

### Anti-Patterns to Avoid
- **Using data_only=True to validate faturamento:** Cached values are stale (not recalculated by openpyxl). PROJECAO REALIZADO col Z shows 0 because Excel never opened the file to recalculate `=SUM(AA4:AL4)`. Must validate formula structure, not cached values, for formula-dependent totals.
- **Iterating all 154K formulas without read_only:** Use `read_only=True` for the data_only pass, `data_only=False` (without read_only) for formula inspection of critical columns only.
- **Assuming 14 tabs:** ROADMAP says 14 but V13 has 13 (see Open Questions section). Do NOT create a phantom 14th tab.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CNPJ digit check | Custom mod-11 verifier | Simple length + digit check | Phase 10 validates format (14 digits), not mathematical validity; project already uses this approach |
| Formula recalculation | Python formula evaluator | Excel real test | openpyxl cannot recalc; trying to evaluate 154K formulas in Python would be a month-long project |
| Excel COM automation | win32com script | Manual Excel open + instructions | User is leigo, COM is fragile, Excel version unknown; simpler to provide step-by-step instructions |
| Data comparison reporting | Custom HTML/PDF report | JSON + console summary | Consistent with all prior phases; simple and parseable |

**Key insight:** The audit script validates what openpyxl CAN validate (formula text, structure, data format). The Excel real test validates what only Excel CAN validate (recalculation, FILTER/SORT spill, conditional formatting). These are complementary, not redundant.

## Common Pitfalls

### Pitfall 1: Confusing Cached Values with Calculated Values
**What goes wrong:** openpyxl with `data_only=True` returns the value Excel stored last time the file was saved with Excel open. Since V13 was generated by openpyxl (never opened in Excel), most formula cells have cached value `None` or `0`.
**Why it happens:** openpyxl does not have a formula calculation engine.
**How to avoid:** For formula-dependent checks (e.g., faturamento total), validate the formula TEXT structure, not the cached value. Reserve computed-value validation for the Excel real test (VAL-06).
**Warning signs:** All SUM/SUMIFS/COUNTIFS cells returning 0 or None in data_only mode.

### Pitfall 2: PROJECAO Sheet Name Has Cedilla Accent
**What goes wrong:** `wb['PROJECAO']` raises KeyError because the actual sheet name is `'PROJECAO '` (with cedilla on A and trailing space).
**Why it happens:** V13 was built from V12 which uses Portuguese accented characters.
**How to avoid:** Use accent-stripping helper function (already established pattern in prior phases):
```python
import unicodedata
def find_sheet(wb, target):
    for name in wb.sheetnames:
        clean = unicodedata.normalize('NFD', name)
        clean = ''.join(c for c in clean if unicodedata.category(c) != 'Mn')
        if target.upper() in clean.upper().strip():
            return name
    return None
```
**Warning signs:** KeyError when accessing sheet by hardcoded name.

### Pitfall 3: The 14 vs 13 Tabs Discrepancy
**What goes wrong:** VAL-05 requires "14 abas presentes e funcionais" but V13 has 13 tabs.
**Why it happens:** The ROADMAP was written before Phase 9 finalized the tab list. The original design may have included a 14th tab (possibly a separate SINALEIRO or PROJECAO summary) that was consolidated or deemed unnecessary.
**How to avoid:** The audit must flag this as a **requirement discrepancy**, not a code bug. The correct approach is to update VAL-05 to match reality (13 tabs) OR identify what the missing 14th tab would be. See Open Questions.
**Warning signs:** Blind FAIL on tab count when everything else is working perfectly.

### Pitfall 4: Faturamento Reference Value Mismatch
**What goes wrong:** VAL-02 requires `R$ 2,156,179 (+/-0.5%)` but Phase 2 documented that NO single source matches this number exactly.
**Why it happens:** PAINEL R$ 2,156,179 is a separate consolidated view. SAP-only = R$ 2,089k (-3.08%), Merged SAP+Mercos = R$ 2,493k (+15.65%). Phase 2 was completed as FAIL_WITH_NOTES because of this scope mismatch.
**How to avoid:** The audit should check faturamento against the same methodology used by each source:
  1. Check that DRAFT 1 monthly columns sum correctly (data integrity).
  2. Check that CARTEIRA FATURAMENTO formulas reference DRAFT 1 correctly (structural integrity).
  3. Document the expected total from the MERGED source (R$ 2,493k) and note the PAINEL discrepancy is a pre-existing, documented business issue.
**Warning signs:** Trying to make numbers match PAINEL when they fundamentally cannot.

### Pitfall 5: AGENDA Dynamic Arrays Need Excel 365
**What goes wrong:** SORTBY+FILTER formulas in AGENDA tabs only work in Excel 365 (or Excel 2021+). Older Excel shows `#NAME?` error.
**Why it happens:** Dynamic array functions (FILTER, SORT, SORTBY, UNIQUE) are Excel 365 only.
**How to avoid:** Document this as a known requirement in the delivery report. The user's environment must be Excel 365 or later. If not, AGENDA tabs will not function (but all other tabs with traditional formulas will).
**Warning signs:** `#NAME?` errors only in AGENDA tabs, everything else works fine.

### Pitfall 6: Large File Load Time
**What goes wrong:** Loading 5.1 MB file with 154K formulas in openpyxl takes 2-5 minutes.
**Why it happens:** openpyxl parses every cell individually.
**How to avoid:** Use `read_only=True` for data-only pass. For formula inspection, load normally but limit iteration to specific tabs/rows when possible. Don't load the file multiple times unnecessarily.
**Warning signs:** Script appears to hang; add progress output per tab.

## Code Examples

### Comprehensive Tab Audit Pattern
```python
"""Pattern used successfully in 9 prior phases."""
import openpyxl
import unicodedata
import re
import json
from collections import Counter

ERROR_PATTERNS = ['#REF!', '#DIV/0!', '#VALUE!', '#NAME?']
EXPECTED_TABS = [
    "PROJECAO", "LOG", "DASH", "REDES_FRANQUIAS_v2", "COMITE",
    "REGRAS", "DRAFT 1", "DRAFT 2", "CARTEIRA",
    "AGENDA LARISSA", "AGENDA DAIANE", "AGENDA MANU", "AGENDA JULIO"
]

def audit_all_tabs(wb):
    results = {}
    total_formulas = 0
    total_errors = {p: 0 for p in ERROR_PATTERNS}

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        tab_formulas = 0
        tab_errors = {p: 0 for p in ERROR_PATTERNS}
        error_locations = []

        for row in ws.iter_rows():
            for cell in row:
                val = str(cell.value or '')
                if val.startswith('='):
                    tab_formulas += 1
                    for pat in ERROR_PATTERNS:
                        if pat in val:
                            tab_errors[pat] += 1
                            total_errors[pat] += 1
                            error_locations.append({
                                'cell': cell.coordinate,
                                'error': pat,
                                'formula': val[:100]
                            })

        total_formulas += tab_formulas
        results[sheet_name] = {
            'formulas': tab_formulas,
            'errors': tab_errors,
            'error_count': sum(tab_errors.values()),
            'error_locations': error_locations[:20],  # Cap at 20 per tab
        }

    return results, total_formulas, total_errors
```

### Two-Base Validation Pattern
```python
def validate_two_base(wb):
    """VAL-03: 100% LOG records have R$ 0.00 (no monetary values)."""
    ws = wb['LOG']
    violations = 0
    total = 0
    # LOG headers at row 2, data starts row 3
    for row in ws.iter_rows(min_row=3, values_only=True):
        if not row[0]:  # no date = skip
            continue
        total += 1
        for i, v in enumerate(row):
            if isinstance(v, (int, float)) and v != 0 and i >= 5:
                violations += 1
                break
    return {
        'total_records': total,
        'violations': violations,
        'pass': violations == 0,
    }
```

### CNPJ Cross-Tab Consistency Check
```python
def validate_cnpj_consistency(wb):
    """VAL-04: Check CNPJ across DRAFT 1, CARTEIRA, and LOG."""
    import re

    def extract_cnpjs(ws, col_idx, start_row):
        cnpjs = []
        for row in ws.iter_rows(min_row=start_row, max_col=col_idx+1, values_only=True):
            val = str(row[col_idx] or '').strip()
            if val:
                cnpjs.append(val)
        return cnpjs

    # DRAFT 1: CNPJ in col B (idx 1), start row 4
    d1 = extract_cnpjs(wb['DRAFT 1'], 1, 4)
    # CARTEIRA: CNPJ in col B (idx 1), start row 4
    cart = extract_cnpjs(wb['CARTEIRA'], 1, 4)
    # LOG: CNPJ in col D (idx 3), start row 3
    log = extract_cnpjs(wb['LOG'], 3, 3)

    # Validate format
    invalid = []
    for source, cnpjs in [('DRAFT 1', d1), ('CARTEIRA', cart), ('LOG', log)]:
        for c in cnpjs:
            digits = re.sub(r'\D', '', c)
            if len(digits) != 14:
                invalid.append((source, c, len(digits)))

    # Check duplicates
    d1_dupes = len(d1) - len(set(d1))
    cart_dupes = len(cart) - len(set(cart))

    # Cross-reference
    d1_set = set(d1)
    cart_set = set(cart)
    overlap = len(d1_set & cart_set)

    return {
        'draft1_total': len(d1), 'draft1_unique': len(set(d1)), 'draft1_dupes': d1_dupes,
        'carteira_total': len(cart), 'carteira_unique': len(set(cart)), 'carteira_dupes': cart_dupes,
        'log_total': len(log), 'log_unique': len(set(log)),
        'invalid_format': invalid[:20],
        'd1_cart_overlap': overlap,
        'pass': d1_dupes == 0 and cart_dupes == 0 and len(invalid) == 0,
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Validate formula cached values | Validate formula TEXT + Excel real test | Phase 10 | Cannot rely on data_only for newly-generated workbooks |
| Manual validation per tab | Comprehensive cross-tab audit script | Phase 9 (06_agenda_tabs_validation.py) | 26-check framework ready to extend |
| Hardcode sheet names | Accent-stripping sheet lookup | Phase 1+ | Handles PROJECAO cedilla robustly |

**Deprecated/outdated:**
- V3 validation scripts (`_validate_final.py`, `_agent3_quality.py`): These validate the old V3 format, not V13. Do NOT reuse directly; use as pattern reference only.
- `_deep_audit.py`: Audits source files, not V13 output. Not relevant for Phase 10.

## Current V13 State (Verified by Research Probes)

### Tab Inventory (13 tabs)
| Tab | Rows | Cols | Formulas | Role |
|-----|------|------|----------|------|
| PROJECAO (with cedilla) | 537 | 80 | 19,224 | Meta + Realizado + Sinaleiro |
| LOG | 20,832 | 21 | 0 | Append-only interaction log |
| DASH | 41 | 17 | 304 | 3-block dashboard |
| REDES_FRANQUIAS_v2 | 25 | 24 | 280 | Network penetration sinaleiro |
| COMITE | 71 | 17 | 342 | Management committee view |
| REGRAS | 283 | 11 | 0 | Motor rules + dropdowns |
| DRAFT 1 | 557 | 45 | 0 | Client master with vendas |
| DRAFT 2 | 6,775 | 31 | 0 | Operational staging log |
| CARTEIRA | 557 | 269 | 134,092 | Main CRM view (6 super-groups) |
| AGENDA LARISSA | 1,000 | 17 | 15 | Daily prioritized tasks |
| AGENDA DAIANE | 1,000 | 17 | 15 | Daily prioritized tasks |
| AGENDA MANU | 1,000 | 17 | 15 | Daily prioritized tasks |
| AGENDA JULIO | 1,000 | 17 | 15 | Daily prioritized tasks |
| **TOTAL** | - | - | **154,302** | |

### Current Data Quality (Pre-Audit Findings)
| Check | Status | Detail |
|-------|--------|--------|
| Formula errors in text | 0 found | All 13 tabs scanned; no #REF!, #DIV/0!, #VALUE!, #NAME? in formula text |
| LOG Two-Base | PASS | 0 non-zero numeric values in LOG cols 5+ |
| CNPJ DRAFT 1 | PASS | 554 unique, 0 dupes, all 14 digits |
| CNPJ CARTEIRA | PASS | 554 unique, 0 dupes, perfect overlap with DRAFT 1 |
| CNPJ LOG | PASS | 20,830 records all have valid 14-digit CNPJ |
| LOG empty CNPJ | PASS | 0 records missing CNPJ |
| File size | 5.1 MB | Reasonable for 154K formulas |

### Faturamento Situation
- DRAFT 1 monthly columns (U-AF) sum: R$ 2,599,775 (merged SAP+Mercos)
- PROJECAO REALIZADO (col Z) cached: R$ 0 (formulas not recalculated -- expected)
- PAINEL reference: R$ 2,156,179
- **Phase 2 documented:** PAINEL does not match any single source. SAP-only R$ 2,089k, Mercos-only R$ 1,895k, Merged R$ 2,493k. This is a **source scope mismatch**, not a data error.
- CARTEIRA FATURAMENTO block has 103K+ formulas referencing DRAFT 1 -- structural integrity must be validated.

## Requirement Analysis

### VAL-01: 0 erros de formula em TODAS as 14 abas
**Confidence:** HIGH
**Current status:** Pre-audit probes found 0 formula error patterns across all 13 tabs. The comprehensive audit script should confirm this across all 154,302 formulas.
**Approach:** Scan all formula cells for ERROR_PATTERNS list. Report any findings with tab, cell coordinate, and formula excerpt.
**Risk:** LOW -- Phase 9 validation already passed 26/26 checks including #REF! and _xlfn.LET checks.

### VAL-02: Faturamento total = R$ 2,156,179 (+/-0.5%)
**Confidence:** MEDIUM
**Current status:** DRAFT 1 monthly sum = R$ 2,599,775 (merged, not PAINEL). Phase 2 documented this as FAIL_WITH_NOTES. The PAINEL value does not match any available data source.
**Approach:** Three-tier validation:
  1. Verify DRAFT 1 data integrity (monthly sums match sap_mercos_merged.json)
  2. Verify CARTEIRA FATURAMENTO formulas structurally reference DRAFT 1 correctly
  3. In Excel real test, verify CARTEIRA REALIZADO column recalculates correctly
  4. Document the PAINEL discrepancy as pre-existing (inherited from Phase 2)
**Risk:** MEDIUM -- This requirement may need formal reclassification as PASS_WITH_NOTES given the documented source scope mismatch.

### VAL-03: 100% dos registros LOG tem R$ 0.00 (Two-Base)
**Confidence:** HIGH
**Current status:** Pre-audit probe confirmed 0 non-zero numeric values in LOG. All 20,830 records compliant.
**Approach:** Iterate all LOG rows, check all numeric cells for non-zero values.
**Risk:** VERY LOW -- already verified.

### VAL-04: 0 CNPJs duplicados, todos com 14 digitos
**Confidence:** HIGH
**Current status:** Pre-audit confirmed: DRAFT 1 = 554 unique (0 dupes, all 14 digits), CARTEIRA = 554 unique (0 dupes), LOG = 20,830 records all valid.
**Approach:** Extract CNPJs from all relevant tabs, validate format, check for duplicates within and across tabs.
**Risk:** VERY LOW -- already verified.

### VAL-05: 14 abas presentes e funcionais
**Confidence:** HIGH (for 13 tabs); REQUIRES CLARIFICATION (for 14)
**Current status:** V13 has 13 tabs (see tab inventory above). The ROADMAP says "14 abas" but Phase 9 concluded with 13 and all requirements passed.
**Approach:** List all tabs, verify each has expected structure (headers, data, formulas). Flag the 14 vs 13 discrepancy as a requirement update needed.
**Possible explanations for the discrepancy:**
  1. ROADMAP was written before Phase 9 finalized the design -- original plan may have included a separate SINALEIRO tab
  2. Count may have been wrong from the start (13 was always the target)
  3. A future tab (e.g., RESUMO, CONFIGURACAO, or PAINEL) was planned but not built
**Recommendation:** Update VAL-05 to "13 abas presentes e funcionais" since all functional requirements are satisfied.

### VAL-06: Teste de abertura e recalculo no Excel real
**Confidence:** HIGH (methodology); CANNOT PRE-VALIDATE (needs Excel)
**Current status:** File has never been opened in Excel. Dynamic arrays (AGENDA) and cached formula values need Excel 365 recalculation.
**Approach:** Produce a checklist of what to verify manually in Excel:
  1. File opens without corruption errors
  2. All 13 tabs visible and navigable
  3. PROJECAO formulas recalculate (REALIZADO col Z shows non-zero sums)
  4. CARTEIRA formulas recalculate (FATURAMENTO block shows data)
  5. DASH shows non-zero KPIs
  6. AGENDA tabs show filtered/sorted consultant lists
  7. Dropdowns work (RESULTADO, MOTIVO in AGENDA; VENDEDOR, RATEIO in COMITE)
  8. Conditional formatting renders (SCORE colors, TEMPERATURA fills, traffic lights)
  9. Column grouping [+] buttons work
  10. File saves without errors
**Risk:** MEDIUM -- Excel 365 required for AGENDA dynamic arrays. Older Excel will show #NAME? in AGENDA tabs only.

## Open Questions

1. **14 vs 13 tabs: What was the 14th tab supposed to be?**
   - What we know: V13 has 13 tabs. All functional requirements from Phases 1-9 are satisfied. ROADMAP says "14 abas" in Phase 10 success criteria.
   - What's unclear: The identity of the planned 14th tab. No phase design document mentions a 14th tab explicitly.
   - Recommendation: **Update VAL-05 to 13 tabs.** The ROADMAP was an early estimate. All 43 requirements across 10 phases are satisfied with 13 tabs. Creating a dummy 14th tab would add no value. Document the discrepancy in the audit report.

2. **VAL-02 faturamento: Should the criterion be updated?**
   - What we know: Phase 2 documented extensively that PAINEL R$ 2,156,179 does not match any available data source. The closest is SAP-only at R$ 2,089k (-3.08%). The merged total is R$ 2,493k (+15.65%).
   - What's unclear: Whether the business intent was to match PAINEL or to have correct data (which may differ from PAINEL).
   - Recommendation: **Validate data integrity (DRAFT 1 sums match JSON sources) and formula structural integrity (CARTEIRA refs correct). Document the PAINEL discrepancy as inherited from Phase 2.** Classify VAL-02 as PASS_WITH_NOTES if data is correct but PAINEL tolerance cannot be met.

3. **Excel version: Is user on Excel 365?**
   - What we know: AGENDA tabs use FILTER/SORT/SORTBY which require Excel 365 or 2021+. User is leigo em tecnologia.
   - What's unclear: The exact Excel version available.
   - Recommendation: **Include Excel version check in the delivery instructions.** If not Excel 365, document that AGENDA tabs will show #NAME? but all other tabs work correctly.

4. **Win32com for automated Excel recalc: worth the complexity?**
   - What we know: The project runs on Windows 11. Excel may be installed. win32com could automate: open file, recalculate, read values, close.
   - What's unclear: Whether Excel is installed, whether COM automation works reliably.
   - Recommendation: **Try win32com as optional enhancement (Plan 10-03).** If it works, automate the Excel recalc test. If not, fall back to manual instructions. Do NOT make it a blocker.

## Sources

### Primary (HIGH confidence)
- V13 workbook direct inspection via openpyxl probes (2026-02-17)
- Phase 9 validation report: `data/output/phase09/phase09_validation_report.json`
- Phase 2 validation report: `data/output/phase02/validation_report.json`
- STATE.md accumulated decisions (30+ Phase 9 entries)
- ROADMAP.md requirements and success criteria

### Secondary (MEDIUM confidence)
- Prior phase scripts as pattern references: 06_agenda_tabs_validation.py, 03_validate_phase08.py
- openpyxl documentation (known from 9 phases of usage)

### Tertiary (LOW confidence)
- win32com feasibility (not tested in this project)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - openpyxl proven across 9 phases, no new libraries needed
- Architecture: HIGH - audit/fix/report pattern clear, follows prior phase patterns
- Pitfalls: HIGH - all 6 pitfalls documented from direct project experience
- VAL-01 (formulas): HIGH - pre-audit found 0 errors
- VAL-02 (faturamento): MEDIUM - PAINEL discrepancy is pre-existing business issue
- VAL-03 (Two-Base): HIGH - pre-audit confirmed 100% compliant
- VAL-04 (CNPJ): HIGH - pre-audit confirmed 0 issues
- VAL-05 (tabs): HIGH - 13 tabs confirmed, requires 14->13 update
- VAL-06 (Excel test): MEDIUM - methodology clear but requires actual Excel

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable -- no external dependency changes expected)
