# Phase XL: Diagnostic Completeness & Positioning Hardening (Sprints 292–299)

> **Focus:** Close 6 TB-derivable analytical gaps + fix 4 language/positioning risks identified by AccountingExpertAuditor
> **Source:** AccountingExpertAuditor capability gap analysis (2026-02-18) + Agent Council evaluation
> **Strategy:** Quick wins first (F3+language), then ratio extension, then flux enhancements, then FS trace, density, and expectation scaffold last (most guardrail-sensitive)
> **Version:** 1.8.0
> **Guardrail:** All computed output must be factual/numerical — no evaluative language, no auto-suggestions, no audit terminology

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 292 | Revenue Concentration Sub-typing + Language Fixes (L1, L3, L4) | 2/10 | BackendCritic + QualityGuardian | COMPLETE |
| 293 | Cash Conversion Cycle (DPO + DIO + CCC) | 3/10 | BackendCritic | COMPLETE |
| 294 | Interperiod Reclassification Detection + L2: variance_indicators rename | 4/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 295 | TB-to-FS Arithmetic Trace Enhancement | 3/10 | BackendCritic | COMPLETE |
| 296 | Account Density Profile | 3/10 | BackendCritic | COMPLETE |
| 297 | ISA 520 Expectation Documentation Scaffold (frontend fields + export) | 4/10 | FrontendExecutor + QualityGuardian | COMPLETE |
| 298 | Language Fix Cleanup + Frontend Tests for Phase XL features | 3/10 | QualityGuardian + FrontendExecutor | COMPLETE |
| 299 | Phase XL Wrap + v1.8.0 | 2/10 | QualityGuardian | COMPLETE |

---

## Sprint 292: Revenue Concentration Sub-typing + Language Fixes (2/10) — COMPLETE
- [x] F3: In `audit_engine.py` `detect_concentration_risk()`, changed `anomaly_type` from generic `"concentration_risk"` to category-specific `f"{category.value}_concentration"` (yields `"revenue_concentration"`, `"asset_concentration"`, etc.)
- [x] F3: Updated `_build_risk_summary()` to count new sub-types (aggregate `concentration_risk` preserved + 4 sub-type counts)
- [x] F3: Updated `RiskSummaryAnomalyTypesResponse` Pydantic schema with 4 new sub-type fields
- [x] F3: Frontend: RiskDashboard auto-renders new sub-types (no changes needed — confirmed)
- [x] L1: In `accrual_completeness_engine.py`, replaced "appears low" with pure numeric: "below the X% threshold (Y% vs Z% threshold)"
- [x] L1: Added 4 guardrail tests (no "appears", no "warrants", numeric comparison for both above/below)
- [x] L3: In `PopulationProfileSection.tsx`, removed "warrants targeted substantive procedures" and "relatively even" sentences
- [x] L4: Audited all 13+ memo generators — patched 5 missing ISA citations: AP (ISA 240/500/PCAOB 2401), JE (PCAOB 1215/ISA 530), Payroll (ISA 240/500/PCAOB 2401), Currency (IAS 21), TWM (ISA 500/505)
- [x] Tests: 14 new (7 concentration sub-type + 4 narrative guardrail + 3 ISA citation). Updated 1 existing test.
- [x] Verification: 3,561 backend tests passed, frontend build clean (36 pages)
- **Review:** All language changes convert evaluative → factual. No new evaluative text introduced.

## Sprint 293: Cash Conversion Cycle — DPO + DIO + CCC (3/10) — COMPLETE
- [x] Added `accounts_payable: float = 0.0` to `CategoryTotals` + `to_dict()` + `from_dict()`
- [x] Updated `extract_category_totals()` with `ACCOUNTS_PAYABLE_KEYWORDS` (accounts payable, trade payable, vendor payable, a/p)
- [x] Added `calculate_dpo()`: `(AP / COGS) x 365` with zero COGS guard
- [x] Added `calculate_dio()`: `(Inventory / COGS) x 365` with zero COGS guard
- [x] Added `calculate_ccc()`: `DIO + DSO - DPO` with null propagation via component results
- [x] Added threshold constants: DPO (30/60/90), DIO (30/60/90), CCC_NEGATIVE_THRESHOLD = -30
- [x] Updated `calculate_all_ratios()`: 9 → 12 ratios
- [x] Factual interpretations only: "Rapid/Standard/Extended payment cycle", "Short/Standard/Extended cash cycle"
- [x] Frontend auto-renders via existing KeyMetricsSection pattern (no changes needed)
- [x] Tests: 24 new (5 DPO, 5 DIO, 5 CCC, 5 AP extraction, 4 integration). 2 existing tests updated (ratio count 9→12)
- [x] Verification: 3,585 backend tests passed, frontend build clean
- **Review:** All interpretations factual. No evaluative language.

## Sprint 294: Interperiod Reclassification Detection + L2 Rename (4/10) — COMPLETE
- [x] F4: Added `has_reclassification: bool`, `prior_type: str` to `FluxItem` dataclass
- [x] F4: In `FluxEngine.compare()`, compare `curr_type` vs `prior_type` (case-insensitive, both non-Unknown)
- [x] F4: Added "Account Type Reclassification: X → Y" indicator, escalates to MEDIUM minimum
- [x] F4: Case-insensitive type comparison suppresses "Asset" vs "asset" false positives
- [x] F4: Updated `FluxResult.to_dict()` with `has_reclassification`, `prior_type` per item
- [x] F4: Added `reclassification_count` to `FluxResult` summary and `to_dict()`
- [x] L2: Renamed `risk_reasons` → `variance_indicators` in `FluxItem` dataclass
- [x] L2: `to_dict()` emits both `variance_indicators` and `risk_reasons` (backward compat alias — removed in Sprint 298)
- [x] L2: Updated `FluxItemResponse` and `FluxSummaryResponse` Pydantic schemas
- [x] L2: Updated `FluxItem` interface + `FluxSummary` in `diagnostic.ts`
- [x] L2: Updated `export_schemas.py`, `export_diagnostics.py`, `leadsheet_generator.py`
- [x] L2: Updated flux page to use `variance_indicators`, test_recon_engine updated
- [x] Tests: 13 new (9 reclassification + 4 rename/backward compat). 1 existing updated.
- [x] Verification: 3,598 backend tests passed, frontend build clean
- **Review:** Reclassification is factual: "Account Type Reclassification: X → Y". No evaluative language.

## Sprint 295: TB-to-FS Arithmetic Trace Enhancement (3/10) — COMPLETE
- [x] Added `raw_aggregate: float = 0.0` and `sign_correction_applied: bool = False` to `MappingTraceEntry`
- [x] Added `SIGN_CORRECTED_LETTERS = {'G', 'H', 'I', 'J', 'K', 'L', 'O'}` class constant to `FinancialStatementBuilder`
- [x] In `_build_mapping_trace()`, compute `raw_aggregate = math.fsum(net_values)` (compensated summation)
- [x] Set `sign_correction_applied` based on lead sheet letter for both populated and empty entries
- [x] Updated `to_dict()` serialization with `raw_aggregate` and `sign_correction_applied`
- [x] Frontend: Added `rawAggregate` and `signCorrectionApplied` to `MappingTraceEntry` type
- [x] Frontend: Updated `buildMappingTrace()` in `useStatementBuilder.ts` to populate new fields
- [x] Frontend: Added "Raw Aggregate" footer row + "sign-corrected" pill in `MappingTraceTable.tsx`
- [x] Frontend: Updated existing test fixtures in `MappingTraceTable.test.tsx`
- [x] Tests: 17 new (2 constant validation, 10 sign correction per letter, 3 serialization, 1 fsum precision, 1 arithmetic proof)
- [x] Verification: 3,615 backend tests passed, frontend build clean
- **Review:** Pure arithmetic data. No evaluative language. sign_correction_applied is a factual flag.

## Sprint 296: Account Density Profile (3/10) — COMPLETE
- [x] Added `SectionDensity` dataclass with `section_label`, `section_letters`, `account_count`, `section_balance`, `balance_per_account`, `is_sparse`
- [x] Added `DENSITY_SECTIONS` constant (9 sections, A-O coverage) and `SPARSE_ACCOUNT_THRESHOLD = 3`
- [x] Added `compute_section_density(lead_sheet_grouping, materiality_threshold)` function
- [x] Sparse logic: `account_count < 3 AND section_balance > materiality AND account_count > 0`
- [x] Added `section_density: list[SectionDensity]` to `PopulationProfileReport` + conditional `to_dict()`
- [x] Added `SectionDensityResponse` Pydantic schema, `Optional[list[SectionDensityResponse]]` on `PopulationProfileResponse`
- [x] Integration in `routes/audit.py`: compute density after lead sheet grouping, inject into population_profile dict
- [x] Frontend: Added `SectionDensity` type, density table in `PopulationProfileSection.tsx` with sparse badge count
- [x] Tests: 19 new (3 constant validation, 12 density computation, 2 serialization, 2 integration)
- [x] Verification: 3,634 backend tests passed, frontend build clean
- **Review:** Sparse is factual ("Yes"/"No"). No evaluative language.

## Sprint 297: ISA 520 Expectation Documentation Scaffold (4/10) — COMPLETE
- [x] Backend: `ExpectationEntry` + `FluxExpectationsMemoInput` Pydantic schemas in `shared/export_schemas.py`
- [x] Backend: Created `flux_expectations_memo.py` — ISA 520 memo generator (Pattern B, SimpleDocTemplate)
- [x] Backend: Sections: Header → Practitioner Notice → Scope → Expectations vs. Observed Variances → Workpaper Sign-Off → Disclaimer
- [x] Backend: Added `/export/flux-expectations-memo` endpoint in `routes/export_memos.py`
- [x] Frontend: Added `ExpectationEntry` interface, `expectations` state (browser-only, React state)
- [x] Frontend: Collapsible "ISA 520 Expectation Documentation" section on flux page with per-flagged-item textareas
- [x] Frontend: Non-dismissible disclaimer banner: "Practitioner-documented expectations — not generated by Paciolus"
- [x] Frontend: `handleExportExpectationsMemo` passes expectation data to export endpoint at download time
- [x] Tests: 10 new (3 schema validation, 4 PDF generation, 2 no-auto-populate guardrail, 1 route registration)
- [x] Verification: 3,644 backend tests passed, frontend build clean
- **CRITICAL GUARDRAIL ENFORCED:** Fields are blank by default. No auto-suggest, no auto-populate. ExpectationEntry defaults to empty strings. Practitioner Notice section in memo explicitly states expectations are user-authored.
- **Review:** Zero evaluative language. All expectation text is practitioner-authored. Memo is documentation scaffold only.

## Sprint 298: Language Fix Cleanup + Frontend Tests (3/10) — COMPLETE
- [x] L2 cleanup: Removed `risk_reasons` backward compat alias from `flux_engine.py`, `diagnostic_response_schemas.py`, `export_schemas.py`, `export_diagnostics.py`, `flux_expectations_memo.py`, `diagnostic.ts`
- [x] L2 cleanup: Updated `test_reclassification_detection.py` to assert `risk_reasons` NOT in `to_dict()`
- [x] Frontend tests: `AccrualCompletenessSection.test.tsx` — 15 tests (expand/collapse, metrics, table, narrative, exports, edge cases)
- [x] Frontend tests: `ExpenseCategorySection.test.tsx` — 15 tests (expand/collapse, summary, bars, table, prior columns, exports)
- [x] Frontend tests: `PopulationProfileSection.test.tsx` — 16 tests (expand/collapse, Gini badge, stats, buckets, top-10, density table, sparse badges, exports)
- [x] L4 regression: ISA citations verified via full backend regression (all memos tested)
- [x] L1 regression: Narrative guardrail tests pass (full backend regression)
- [x] Verification: 3,644 backend tests passed, 987 frontend tests passed, frontend build clean
- **Review:** L2 alias fully removed. 46 new frontend tests for 3 Phase XXXIX/XL components.

## Sprint 299: Phase XL Wrap + v1.8.0 (2/10) — COMPLETE
- [x] Full backend regression: 3,644 passed
- [x] Full frontend build: clean (36 pages)
- [x] Full frontend test suite: 987 passed
- [x] Version bump: package.json 1.7.0 → 1.8.0
- [x] Archive sprint details to `tasks/archive/phase-xl-details.md`
- [x] Update CLAUDE.md + MEMORY.md
- [x] AccountingExpertAuditor guardrail verification: all features use factual/numerical language only

---

## Test Count Summary

| Sprint | Backend | Frontend |
|--------|---------|----------|
| Pre-Phase XL | 3,547 | 931 |
| Sprint 292 | 3,561 | 931 |
| Sprint 293 | 3,585 | 931 |
| Sprint 294 | 3,598 | 931 |
| Sprint 295 | 3,615 | 931 |
| Sprint 296 | 3,634 | 931 |
| Sprint 297 | 3,644 | 931 |
| Sprint 298 | 3,644 | 987 |
| **Final** | **3,644** | **987** |

## Features Delivered

1. **F3: Revenue Concentration Sub-typing** — 4 category-specific anomaly types
2. **F4: Interperiod Reclassification Detection** — Account Type Reclassification indicator
3. **F5: Cash Conversion Cycle** — DPO + DIO + CCC (12 ratios total)
4. **F6: TB-to-FS Arithmetic Trace** — raw_aggregate + sign_correction_applied
5. **F6b: Account Density Profile** — 9-section density + sparse flagging
6. **F2: ISA 520 Expectation Scaffold** — practitioner-authored fields + PDF memo export

## Language Fixes Delivered

1. **L1: Accrual narrative** — "appears low" → pure numeric comparison
2. **L2: risk_reasons → variance_indicators** — full rename + alias removal
3. **L3: Population Profile** — removed evaluative sentences
4. **L4: ISA citation gaps** — 5 memo generators patched with correct ISA references
