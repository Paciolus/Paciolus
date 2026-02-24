# Report Inventory and Migration Plan

> **Version:** 1.0.0 | **Status:** APPROVED | **Companion:** `REPORT_STANDARDS_SPEC.md`
>
> This document inventories every PDF report generator in the Paciolus codebase, identifies deviations from the target standard, and defines the migration sequence.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Shared Utilities Inventory](#2-shared-utilities-inventory)
3. [Report Generator Inventory](#3-report-generator-inventory)
4. [Deviation Summary](#4-deviation-summary)
5. [Migration Sequence](#5-migration-sequence)
6. [Risk Register](#6-risk-register)

---

## 1. Architecture Overview

### 1.1 Current Architecture (3-tier)

```
Tier 1: Foundation
  pdf_generator.py          -> create_classical_styles() (16 styles)
  shared/memo_base.py       -> create_memo_styles() (11 styles) + 8 builder functions

Tier 2: Template
  shared/memo_template.py   -> generate_testing_memo() orchestrator

Tier 3: Generators
  3A: 7 standard wrappers   -> TestingMemoConfig + generate_testing_memo()
  3B: 10 custom generators  -> memo_base.py builders directly
  3C: 1 standalone class    -> anomaly_summary_generator.py
```

### 1.2 Target Architecture (post-migration)

```
Tier 1: Foundation (UNIFIED)
  shared/report_standardization/styles.py    -> create_report_styles() (14 styles)
  shared/report_standardization/builders.py  -> Unified builder functions
  shared/report_standardization/page.py      -> Page header/footer canvas callbacks
  shared/report_standardization/colors.py    -> Color constants (single source)

Tier 2: Template (UNIFIED)
  shared/report_standardization/template.py  -> generate_report() orchestrator

Tier 3: Generators (unchanged count, new foundation)
  All 20 generators migrate to Tier 1/2 unified modules
```

---

## 2. Shared Utilities Inventory

### 2.1 `backend/pdf_generator.py` — Foundation A (Classical)

| Utility | Used By | Migration Target |
|---------|---------|-----------------|
| `ClassicalColors` (color constants) | TB Diagnostic, Financial Statements | `report_standardization/colors.py` |
| `DoubleRule` (flowable) | TB Diagnostic, Financial Statements + all memos (via memo_base) | `report_standardization/builders.py` |
| `LedgerRule` (flowable) | TB Diagnostic, Financial Statements + all memos (via memo_base) | `report_standardization/builders.py` |
| `create_leader_dots()` | TB Diagnostic + all memos (via memo_base) | `report_standardization/builders.py` |
| `format_classical_date()` | All 20 generators | `report_standardization/builders.py` |
| `generate_reference_number()` | 15 generators (5 diagnostic extensions use hardcoded WP codes) | `report_standardization/builders.py` |
| `create_classical_styles()` | TB Diagnostic, Financial Statements only | **RETIRED** — replaced by `create_report_styles()` |
| `PaciolusReportGenerator` (class) | TB Diagnostic only | Refactor to use unified template |
| `generate_financial_statements_pdf()` | Financial Statements only | Refactor to use unified template |

### 2.2 `backend/shared/memo_base.py` — Foundation B (Memo)

| Utility | Used By | Migration Target |
|---------|---------|-----------------|
| `create_memo_styles()` | All 18 memos | **RETIRED** — replaced by `create_report_styles()` |
| `build_memo_header()` | All 18 memos | `report_standardization/builders.py` → `build_cover_block()` |
| `build_scope_section()` | 12 memos (7 standard + 5 custom) | `report_standardization/builders.py` |
| `build_methodology_section()` | 7 standard memos | `report_standardization/builders.py` |
| `build_results_summary_section()` | 7 standard memos | `report_standardization/builders.py` |
| `build_workpaper_signoff()` | All 18 memos | `report_standardization/builders.py` → `build_signoff()` |
| `build_proof_summary_section()` | 9 memos (7 standard + TWM + Bank Rec) | `report_standardization/builders.py` |
| `build_intelligence_stamp()` | 16 memos (not TB Diagnostic, not FS, not Anomaly Summary) | `report_standardization/builders.py` |
| `build_disclaimer()` | 16 memos | `report_standardization/builders.py` |

### 2.3 `backend/shared/memo_template.py` — Template

| Utility | Used By | Migration Target |
|---------|---------|-----------------|
| `TestingMemoConfig` (dataclass) | 7 standard testing memos | `report_standardization/template.py` → `ReportConfig` |
| `generate_testing_memo()` | 7 standard testing memos | `report_standardization/template.py` → `generate_report()` |

---

## 3. Report Generator Inventory

### 3.1 Category A — Classical Reports

#### A1: TB Diagnostic Intelligence Summary

| Field | Value |
|-------|-------|
| **File** | `backend/pdf_generator.py` (`PaciolusReportGenerator.generate()`) |
| **Lines** | ~450 |
| **Shared Utils** | `ClassicalColors`, `DoubleRule`, `LedgerRule`, `create_leader_dots`, `format_classical_date`, `generate_reference_number`, `create_classical_styles` |
| **Template** | None — standalone class with custom `SimpleDocTemplate` + canvas callbacks |
| **Cover Block** | 28pt title + ornament + subtitle + reference + double rule |
| **Page Decoration** | Watermark, top gold rule, bottom ledger rule, page numbers, every-page disclaimer |
| **Signoff** | Custom inline (1.5"/3.5"/1.5" columns, alternating rows) |
| **Intelligence Stamp** | Missing |
| **Disclaimer** | Custom `_get_legal_disclaimer()` — different text from shared `build_disclaimer()` |
| **Section Naming** | Spaced-letter uppercase (`E X E C U T I V E   S U M M A R Y`) |
| **Deviations** | 8 (see Deviation Summary) |

#### A2: Financial Statements (BS + IS + CFS)

| Field | Value |
|-------|-------|
| **File** | `backend/pdf_generator.py` (`generate_financial_statements_pdf()`) |
| **Lines** | ~300 |
| **Shared Utils** | Same as A1 |
| **Template** | None — standalone function with canvas callbacks |
| **Cover Block** | 28pt title + ornament + subtitle + reference + double rule |
| **Page Decoration** | Same watermark/rules/page numbers as A1 |
| **Signoff** | Custom inline (duplicated from A1) |
| **Intelligence Stamp** | Missing |
| **Disclaimer** | Same custom text as A1 |
| **Section Naming** | Spaced-letter uppercase |
| **Deviations** | 8 (same as A1) |

### 3.2 Category B — Standard Testing Memos (via `memo_template.py`)

All 7 share the same deviation profile:

| Field | JE | AP | Payroll | Revenue | AR Aging | Fixed Asset | Inventory |
|-------|:--:|:--:|:-------:|:-------:|:--------:|:-----------:|:---------:|
| **File** | `je_testing_memo_generator.py` | `ap_testing_memo_generator.py` | `payroll_testing_memo_generator.py` | `revenue_testing_memo_generator.py` | `ar_aging_memo_generator.py` | `fixed_asset_testing_memo_generator.py` | `inventory_testing_memo_generator.py` |
| **Template** | `memo_template` | `memo_template` | `memo_template` | `memo_template` | `memo_template` | `memo_template` | `memo_template` |
| **Page Header** | Missing | Missing | Missing | Missing | Missing | Missing | Missing |
| **Page Footer** | Missing | Missing | Missing | Missing | Missing | Missing | Missing |
| **Margin Top** | 1.0" | 1.0" | 1.0" | 1.0" | 1.0" | 1.0" | 1.0" |
| **Margin Bottom** | 0.8" | 0.8" | 0.8" | 0.8" | 0.8" | 0.8" | 0.8" |
| **Deviations** | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

**Common deviations** (all 7):
1. No page header/footer (no page numbers, no per-page reference, no zero-storage line)
2. Bottom margin 0.8" (target: 0.85")

### 3.3 Category C — Custom Memos

#### C1: Three-Way Match

| Field | Value |
|-------|-------|
| **File** | `backend/three_way_match_memo_generator.py` |
| **Lines** | ~250 |
| **Shared Utils** | `memo_base` (header, scope, proof summary, signoff, stamp, disclaimer), `DoubleRule`, `LedgerRule` |
| **Template** | None — uses `memo_base` builders directly |
| **Page Header/Footer** | Missing |
| **Margins** | 1.0" top, 0.8" bottom |
| **Deviations** | 2 (same as Category B) |

#### C2: Bank Reconciliation

| Field | Value |
|-------|-------|
| **File** | `backend/bank_reconciliation_memo_generator.py` |
| **Lines** | ~280 |
| **Shared Utils** | `memo_base` (header, scope, proof summary, signoff, stamp, disclaimer), `DoubleRule`, `LedgerRule` |
| **Template** | None — uses `memo_base` builders directly |
| **Page Header/Footer** | Missing |
| **Margins** | 1.0" top, 0.8" bottom |
| **Deviations** | 2 (same as Category B) |

#### C3: Multi-Period (Analytical Procedures)

| Field | Value |
|-------|-------|
| **File** | `backend/multi_period_memo_generator.py` |
| **Lines** | ~200 |
| **Shared Utils** | `memo_base` (header, scope, signoff, stamp, disclaimer), `DoubleRule`, `LedgerRule` |
| **Template** | None — uses `memo_base` builders directly |
| **Page Header/Footer** | Missing |
| **Margins** | 1.0" top, 0.8" bottom |
| **Deviations** | 2 (same as Category B) |

#### C4: Statistical Sampling

| Field | Value |
|-------|-------|
| **File** | `backend/sampling_memo_generator.py` |
| **Lines** | ~320 |
| **Shared Utils** | `memo_base` (header, scope, signoff, stamp, disclaimer), `DoubleRule`, `LedgerRule` |
| **Template** | None — uses `memo_base` builders directly |
| **Page Header/Footer** | Missing |
| **Margins** | 0.75" top, 0.75" bottom |
| **Deviations** | 3 (missing page header/footer + non-standard margins) |

#### C5: Multi-Currency

| Field | Value |
|-------|-------|
| **File** | `backend/currency_memo_generator.py` |
| **Lines** | ~200 |
| **Shared Utils** | `memo_base` (header, signoff, stamp, disclaimer), `DoubleRule`, `LedgerRule` |
| **Template** | None — uses `memo_base` builders directly |
| **Page Header/Footer** | Missing |
| **Margins** | 0.75" top, 0.75" bottom |
| **Reference Prefix** | Uses default `PAC-` (should be `CCM-`) |
| **Section Numbering** | No Roman numerals |
| **Table Style** | Helvetica-Bold headers, OBSIDIAN_700 bg, OATMEAL text, GRID lines |
| **Deviations** | 6 (most deviant memo) |

### 3.4 Category D — Diagnostic Extension Memos

All 5 share common deviations:

| Field | Preflight | Population Profile | Expense Category | Accrual Completeness | Flux Expectations |
|-------|:---------:|:------------------:|:----------------:|:--------------------:|:-----------------:|
| **File** | `preflight_memo_generator.py` | `population_profile_memo.py` | `expense_category_memo.py` | `accrual_completeness_memo.py` | `flux_expectations_memo.py` |
| **Lines** | ~180 | ~200 | ~180 | ~160 | ~220 |
| **Shared Utils** | `memo_base` | `memo_base` | `memo_base` | `memo_base` | `memo_base` |
| **Page Header/Footer** | Missing | Missing | Missing | Missing | Missing |
| **Margins** | 0.75"/0.75" | 0.75"/0.75" | 0.75"/0.75" | 0.75"/0.75" | 0.75"/0.75" |
| **Reference** | Hardcoded `WP-PF-001` | Hardcoded `WP-PP-001` | Hardcoded `WP-ECA-001` | Hardcoded `WP-ACE-001` | Hardcoded `WP-FE-001` |
| **Deviations** | 3 | 3 | 3 | 3 | 4 |

**Common deviations** (all 5):
1. No page header/footer
2. Non-standard margins (0.75"/0.75" — target: 1.0"/0.85")
3. Hardcoded workpaper codes instead of dynamic `generate_reference_number()`

**Flux Expectations additional deviation:**
4. Uses Helvetica-Bold in one table (font policy violation)

### 3.5 Category E — Engagement Reports

#### E1: Anomaly Summary

| Field | Value |
|-------|-------|
| **File** | `backend/anomaly_summary_generator.py` |
| **Lines** | ~300 |
| **Shared Utils** | `memo_base.create_memo_styles()` + inline `DisclaimerBanner` style |
| **Template** | None — standalone class (`AnomalySummaryGenerator`) |
| **Page Header/Footer** | Missing |
| **Margins** | 0.75" top, 0.75" bottom |
| **Intelligence Stamp** | Missing |
| **Signoff** | Always-blank (by design — this is correct) |
| **Deviations** | 3 (missing page header/footer, non-standard margins, missing intelligence stamp) |

---

## 4. Deviation Summary

### 4.1 Deviation Counts by Generator

| Generator | Deviations | Severity |
|-----------|:----------:|:--------:|
| TB Diagnostic (`pdf_generator.py`) | 8 | High |
| Financial Statements (`pdf_generator.py`) | 8 | High |
| Currency Memo | 6 | High |
| Flux Expectations Memo | 4 | Medium |
| Preflight Memo | 3 | Low |
| Population Profile Memo | 3 | Low |
| Expense Category Memo | 3 | Low |
| Accrual Completeness Memo | 3 | Low |
| Anomaly Summary | 3 | Low |
| Sampling Memo | 3 | Low |
| JE Testing Memo | 2 | Low |
| AP Testing Memo | 2 | Low |
| Payroll Testing Memo | 2 | Low |
| Revenue Testing Memo | 2 | Low |
| AR Aging Memo | 2 | Low |
| Fixed Asset Testing Memo | 2 | Low |
| Inventory Testing Memo | 2 | Low |
| Three-Way Match Memo | 2 | Low |
| Bank Reconciliation Memo | 2 | Low |
| Multi-Period Memo | 2 | Low |

### 4.2 Deviation Types

| ID | Deviation | Affected Generators | Count |
|----|-----------|---------------------|:-----:|
| D1 | Missing page header/footer (no page numbers, no zero-storage line) | All 18 memos | 18 |
| D2 | Non-standard margins | 7 generators (sampling, currency, 5 diagnostic extensions) | 7 |
| D3 | Hardcoded workpaper codes instead of dynamic reference numbers | 5 diagnostic extensions | 5 |
| D4 | Wrong title size (28pt instead of 24pt) | TB Diagnostic, Financial Statements | 2 |
| D5 | Spaced-letter section headers | TB Diagnostic, Financial Statements | 2 |
| D6 | Section ornament (diamond) | TB Diagnostic, Financial Statements | 2 |
| D7 | Watermark | TB Diagnostic, Financial Statements | 2 |
| D8 | Custom disclaimer text (not shared) | TB Diagnostic, Financial Statements | 2 |
| D9 | Missing intelligence stamp | TB Diagnostic, Financial Statements, Anomaly Summary | 3 |
| D10 | Custom signoff (different column widths) | TB Diagnostic, Financial Statements | 2 |
| D11 | Helvetica font usage | Currency Memo, Flux Expectations Memo | 2 |
| D12 | Dark header table style (GRID + OBSIDIAN_700 bg) | Currency Memo | 1 |
| D13 | No Roman numeral section numbering | Currency Memo | 1 |
| D14 | Wrong reference prefix (`PAC-` instead of `CCM-`) | Currency Memo | 1 |
| D15 | Duplicated signoff code (inline, not shared) | Financial Statements | 1 |
| D16 | Bottom margin inconsistency (0.8" instead of 0.85") | 12 memos (7 standard + 3 custom + 2 classical) | 12 |

---

## 5. Migration Sequence

### 5.1 Sprint Plan

Migration is ordered by: (1) foundation first, (2) highest deviation count, (3) most-reused code.

#### Sprint 1: Unified Foundation Module

**Scope:** Create `backend/shared/report_standardization/` package with unified styles, colors, builders, and page decoration.

| Task | Files | Complexity | Risk |
|------|-------|:----------:|:----:|
| Create `colors.py` — single color constant source | 1 new | Low | Low |
| Create `styles.py` — `create_report_styles()` with 14 unified tokens | 1 new | Medium | Low |
| Create `builders.py` — extract and unify all builder functions (incl. logo in cover block, mandatory alternating row tint) | 1 new | Medium | Medium |
| Create `page.py` — page header/footer canvas callbacks | 1 new | Medium | Low |
| Create `template.py` — `ReportConfig` + `generate_report()` | 1 new | Medium | Medium |
| Add logo asset for PDF embedding (centered, max 1.2" x 0.4") | 1 new | Low | Low |
| Unit tests for all new modules | 1 new | Medium | Low |

**Estimated effort:** Medium. **Risk:** Medium — builders must be backward-compatible during transition.

#### Sprint 2: Category B Migration (7 Standard Testing Memos)

**Scope:** Migrate all 7 standard testing memo wrappers to the new foundation.

| Task | Files Modified | Complexity | Risk |
|------|:-----:|:----------:|:----:|
| Update `TestingMemoConfig` → `ReportConfig` mapping | 7 generators + `memo_template.py` | Low | Low |
| Add page header/footer (D1) | `memo_template.py` | Low | Low |
| Fix bottom margin (D16) | `memo_template.py` | Low | Low |
| Regression: verify all 7 memo PDFs render correctly | 7 test files | Medium | Medium |

**Estimated effort:** Low. **Risk:** Low — these are thin wrappers; changes are centralized in `memo_template.py`.

#### Sprint 3: Category C Migration (5 Custom Memos)

**Scope:** Migrate TWM, Bank Rec, Multi-Period, Sampling, Currency to unified foundation.

| Task | Files Modified | Complexity | Risk |
|------|:-----:|:----------:|:----:|
| TWM: add page header/footer, fix margin | 1 | Low | Low |
| Bank Rec: add page header/footer, fix margin | 1 | Low | Low |
| Multi-Period: add page header/footer, fix margin | 1 | Low | Low |
| Sampling: add page header/footer, fix margins | 1 | Low | Low |
| Currency: fix font (D11), table style (D12), section numbering (D13), reference prefix (D14), add page header/footer, fix margins | 1 | High | Medium |
| Regression: verify all 5 memo PDFs | 5 test files | Medium | Medium |

**Estimated effort:** Medium (currency memo is the main effort). **Risk:** Medium.

#### Sprint 4: Category D Migration (5 Diagnostic Extensions)

**Scope:** Migrate Preflight, Population Profile, Expense Category, Accrual Completeness, Flux Expectations.

| Task | Files Modified | Complexity | Risk |
|------|:-----:|:----------:|:----:|
| All 5: replace hardcoded WP codes with `generate_reference_number()` (D3) | 5 | Low | Low |
| All 5: add page header/footer (D1) | 5 | Low | Low |
| All 5: fix margins (D2) | 5 | Low | Low |
| Flux Expectations: fix Helvetica usage (D11) | 1 | Low | Low |
| Regression: verify all 5 memo PDFs | 5 test files | Medium | Low |

**Estimated effort:** Low. **Risk:** Low — these are independent generators with minimal coupling.

#### Sprint 5: Category A Migration (2 Classical Reports)

**Scope:** Migrate TB Diagnostic and Financial Statements to unified foundation.

| Task | Files Modified | Complexity | Risk |
|------|:-----:|:----------:|:----:|
| Replace `create_classical_styles()` with `create_report_styles()` | `pdf_generator.py` | High | High |
| Remove watermark (D7), ornament (D6), spaced-letter headers (D5) | `pdf_generator.py` | Medium | Medium |
| Downgrade title to 24pt (D4) | `pdf_generator.py` | Low | Low |
| Replace custom disclaimer with shared `build_disclaimer()` (D8) | `pdf_generator.py` | Low | Low |
| Add intelligence stamp (D9) | `pdf_generator.py` | Low | Low |
| Replace custom signoff with shared `build_signoff()` (D10, D15) | `pdf_generator.py` | Medium | Medium |
| Add page header using unified `page.py` callbacks | `pdf_generator.py` | Medium | Medium |
| Regression: verify both PDFs render correctly | 2 test files | High | High |

**Estimated effort:** High. **Risk:** High — `pdf_generator.py` is the most complex file (~750 lines) with the most custom logic. The TB Diagnostic report is the platform's flagship output.

#### Sprint 6: Category E Migration (Anomaly Summary) + Cleanup

**Scope:** Migrate Anomaly Summary, retire deprecated modules, final verification.

| Task | Files Modified | Complexity | Risk |
|------|:-----:|:----------:|:----:|
| Add intelligence stamp (D9) | `anomaly_summary_generator.py` | Low | Low |
| Add page header/footer (D1) | `anomaly_summary_generator.py` | Low | Low |
| Fix margins (D2) | `anomaly_summary_generator.py` | Low | Low |
| Retire `create_classical_styles()` from `pdf_generator.py` | 1 | Low | Low |
| Retire `create_memo_styles()` from `memo_base.py` | 1 | Low | Medium |
| Remove deprecated style references across all generators | All | Medium | Medium |
| Full regression: generate all 20 PDFs, visual comparison | 20 | High | Medium |

**Estimated effort:** Medium. **Risk:** Medium — retirement of old style functions could break any generator not yet migrated.

### 5.2 Migration Order Summary

```
Sprint 1: Foundation Module          ██████████ (new code, 0 generators migrated)
Sprint 2: 7 Standard Testing Memos   ████████████████████████████████████ (7 generators)
Sprint 3: 5 Custom Memos             ████████████████████████████ (5 generators)
Sprint 4: 5 Diagnostic Extensions    ████████████████████████████ (5 generators)
Sprint 5: 2 Classical Reports        ██████████████ (2 generators — highest risk)
Sprint 6: Anomaly Summary + Cleanup  ██████████ (1 generator + retirement)
```

### 5.3 Dependency Chain

```
Sprint 1 ─┬─> Sprint 2 ─┐
           ├─> Sprint 3 ─┤
           ├─> Sprint 4 ─├─> Sprint 6
           └─> Sprint 5 ─┘
```

Sprints 2/3/4/5 can proceed in parallel after Sprint 1. Sprint 6 depends on all others.

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Visual regression in flagship TB Diagnostic report | Medium | High | Generate before/after PDF snapshots; CEO visual review gate on Sprint 5 |
| Breaking `export_memos.py` route wiring during migration | Low | High | Run all 17 export endpoint tests after each sprint |
| `memo_base.py` builder signature changes breaking custom memos | Medium | Medium | Maintain backward-compatible signatures during transition; deprecation warnings first |
| Margin/font changes affecting page breaks in long reports | Medium | Medium | Test with large datasets (500+ row TB, 100+ flagged items) |
| Retirement of `create_classical_styles()` before all consumers migrated | Low | High | Sprint 6 retirement only after all 20 generators confirmed on new foundation |
| Proof Summary section not rendering correctly with new styles | Low | Medium | Dedicated test for each of the 9 proof-adapter memos |

---

*End of Report Inventory and Migration Plan.*
