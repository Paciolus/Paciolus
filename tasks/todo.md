# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Phase Lifecycle Protocol

**MANDATORY:** Follow this lifecycle for every phase. This eliminates manual archive requests.

### During a Phase
- Active phase details (audit findings, sprint checklists, reviews) live in this file under `## Active Phase`
- Each sprint gets a checklist section with tasks, status, and review

### On Phase Completion (Wrap Sprint)
1. **Regression:** `pytest` + `npm run build` must pass
2. **Archive:** Move all sprint checklists/reviews to `tasks/archive/phase-<name>-details.md`
3. **Summarize:** Add a one-line summary to `## Completed Phases` below (with test count if changed)
4. **Clean this file:** Delete the entire `## Active Phase` section content, leaving only the header ready for the next phase
5. **Update CLAUDE.md:** Add phase to completed list, update test count + current phase
6. **Update MEMORY.md:** Update project status
7. **Commit:** `Sprint X: Phase Y wrap — regression verified, documentation archived`

**The `## Active Phase` section should ONLY contain the current in-progress phase. Once complete, it becomes empty until the next phase begins.**

---

## Completed Phases

### Phases I–IX (Sprints 1–96) — COMPLETE
> Core platform through Three-Way Match. TB analysis, streaming, classification, 9 ratios, anomaly detection, benchmarks, lead sheets, prior period, adjusting entries, email verification, Multi-Period TB (Tool 2), JE Testing (Tool 3, 18 tests), Financial Statements (Tool 1), AP Testing (Tool 4, 13 tests), Bank Rec (Tool 5), Cash Flow, Payroll Testing (Tool 6, 11 tests), TWM (Tool 7), Classification Validator.

### Phase X (Sprints 96.5–102) — COMPLETE
> Engagement Layer: engagement model + materiality cascade, follow-up items, workpaper index, anomaly summary report, diagnostic package export, engagement workspace frontend.

### Phase XI (Sprints 103–110) — COMPLETE
> Tool-Engagement Integration, Revenue Testing (Tool 8, 12 tests), AR Aging (Tool 9, 11 tests).

### Phase XII (Sprints 111–120) — COMPLETE
> Nav overflow, Finding Comments + Assignments, Fixed Asset Testing (Tool 10, 9 tests), Inventory Testing (Tool 11, 9 tests). **v1.1.0**

### Phase XIII (Sprints 121–130) — COMPLETE
> Dual-theme "The Vault", security hardening, WCAG AAA, 11 PDF memos, 24 rate-limited exports. **v1.2.0. Tests: 2,593 + 128.**

### Phase XIV (Sprints 131–135) — COMPLETE
> 6 public marketing/legal pages, shared MarketingNav/Footer, contact backend.

### Phase XV (Sprints 136–141) — COMPLETE
> Code deduplication: shared parsing helpers, shared types, 4 shared testing components. ~4,750 lines removed.

### Phase XVI (Sprints 142–150) — COMPLETE
> API Hygiene: 15 fetch → apiClient, semantic tokens, Docker hardening.

### Phase XVII (Sprints 151–163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules, 8 frontend decompositions, 15 new shared files. **Tests: 2,716 + 128.**

### Phase XVIII (Sprints 164–170) — COMPLETE
> Async Architecture: `async def` → `def` for pure-DB, `asyncio.to_thread()` for CPU-bound, `BackgroundTasks`, `memory_cleanup()`.

### Phase XIX (Sprints 171–177) — COMPLETE
> API Contract Hardening: 25 endpoints gain response_model, 16 status codes corrected, trends.py fix, path fixes.

### Phase XX (Sprint 178) — COMPLETE
> Rate Limit Gap Closure: 4 endpoints secured, global 60/min default.

### Phase XXI (Sprints 180–183) — COMPLETE
> Migration Hygiene: Alembic baseline regeneration, datetime deprecation fix.

### Phase XXII (Sprints 184–190) — COMPLETE
> Pydantic Model Hardening: Field constraints, 13 Enum/Literal migrations, model decomposition, v2 syntax.

### Phase XXIII (Sprints 191–194) — COMPLETE
> Pandas Performance: vectorized keyword matching, NEAR_ZERO guards, math.fsum. **Tests: 2,731 + 128.**

### Phase XXIV (Sprint 195) — COMPLETE
> Upload & Export Security: formula injection, column/cell limits, body size middleware. **Tests: 2,750 + 128.**

### Sprint 196 — PDF Generator Critical Fixes — COMPLETE
> Fix `_build_workpaper_signoff()` crash, dynamic tool count, BytesIO leak.

### Phase XXV (Sprints 197–201) — COMPLETE
> JWT Auth Hardening: refresh tokens, CSRF/CORS, bcrypt, jti claim, startup cleanup. **Tests: 2,883 + 128.**

### Phase XXVI (Sprints 202–203) — COMPLETE
> Email Verification Hardening: token cleanup, pending_email re-verification, disposable blocking. **Tests: 2,903 + 128.**

### Phase XXVII (Sprints 204–209) — COMPLETE
> Next.js App Router Hardening: 7 error boundaries, 4 route groups, skeleton components, loading.tsx files.

### Phase XXVIII (Sprints 210–216) — COMPLETE
> Production Hardening: GitHub Actions CI, structured logging + request ID, 46 exceptions narrowed, 45 return types, deprecated patterns migrated.

### Phase XXIX (Sprints 217–223) — COMPLETE
> API Integration Hardening: 102 Pydantic response schemas, apiClient 422 parsing, isAuthError in 3 hooks, downloadBlob→apiClient, CSRF on logout, UI state consistency, 74 contract tests, OpenAPI→TS generation. **Tests: 2,977 + 128.**

### Phase XXX (Sprints 224–230) — COMPLETE
> Frontend Type Safety Hardening: 5 `any` eliminated, 3 tsconfig strict flags, type taxonomy consolidation (Severity/AuditResult/UploadStatus), discriminated unions (BankRec + hook returns), 24 return type annotations, 11 optional chains removed. **Tests: 2,977 + 128.**

### Phase XXXI (Sprints 231–238) — COMPLETE
> Frontend Test Coverage Expansion: 22 pre-existing failures fixed, 20 new test files, 261 new tests added. **Tests: 2,977 + 389.**

### Sprints 239–240 (Standalone) — COMPLETE
> Sprint 239: Tailwind cleanup, 3 shared components (GuestCTA, ZeroStorageNotice, DisclaimerBox), chart theme. Sprint 240: Framer-motion performance & accessibility (MotionConfig, scaleX transforms, CSS keyframes, DURATION/SPRING presets).

### Phase XXXII (Sprints 241–248) — COMPLETE
> Backend Test Suite Hardening: 73 new tests (14 edge case + 59 route integration), 5 monolithic files split into 17 focused files, CSRF fixture opt-in refactor, 1 schema bugfix. **Tests: 3,050 + 389.**

### Phase XXXIII (Sprints 249–254) — COMPLETE
> Error Handling & Configuration Hardening: 131 frontend tests, Docker tuning, global exception handler, 21 sanitize_error migrations, 9 db.commit() gaps closed, secrets_manager integration, .gitignore hardened. **Tests: 3,050 + 520.**

### Phase XXXIV (Sprints 255–260) — COMPLETE
> Multi-Currency Conversion: python-jose → PyJWT security pre-flight, RFC (closing-rate MVP), currency engine with ISO 4217 validation + rate lookup + vectorized conversion, 4 API endpoints, CurrencyRatePanel component, conversion memo PDF, auto-conversion in TB upload. **v1.3.0. Tests: 3,129 + 520.**

### Phase XXXV (Sprints 261–266 + T1) — COMPLETE
> In-Memory State Fix + Codebase Hardening: stateless HMAC CSRF, DB-backed lockout + tool sessions, float precision (math.fsum/Decimal), server_default timestamps, 8 dependency upgrades, deep health probe, CI security gates (Bandit/Dependabot/pip-audit), zero-storage language truthfulness. All 8 SESSION_HANDOFF packets validated. **Tests: 3,323 + 724.**

### Phase XXXVI (Sprints 268–272) — COMPLETE
> Statistical Sampling Module (Tool 12): ISA 530 / PCAOB AS 2315, MUS + random sampling, 2-tier stratification, Stringer bound evaluation, two-phase workflow (design + evaluate), PDF memo, CSV export, 12-tool nav. **v1.4.0. Tests: 3,391 + 745.**

### Phase XXXVII (Sprints 273–278) — COMPLETE
> Deployment Hardening: dependency version bumps (pydantic, openpyxl, PyJWT, TypeScript), PostgreSQL connection pool tuning + CI job, Sentry APM integration (Zero-Storage compliant), 23 new frontend test files (173 new tests), coverage threshold raised to 25%. **v1.5.0. Tests: 3,396 + 918.**

### Phase XXXVIII (Sprints 279–286) — COMPLETE
> Security & Accessibility Hardening + Lightweight Features: passlib→bcrypt, CVE patches, typing modernization, ruff rules, back_populates migration, WCAG modals/labels/images/CSP, focus trap, eslint-plugin-jsx-a11y, Data Quality Pre-Flight Report, Account-to-Statement Mapping Trace, users+auth route tests, exception narrowing. **v1.6.0. Tests: 3,440 + 931.**

### Phase XXXIX (Sprints 287–291) — COMPLETE
> Diagnostic Intelligence Features: TB Population Profile (Gini, magnitude buckets), Cross-Tool Account Convergence Index, Expense Category Analytical Procedures (5-category ISA 520), Accrual Completeness Estimator (run-rate ratio). 11 new API endpoints, 4 new TB sections, 4 PDF memos. **v1.7.0. Tests: 3,547 + 931.**

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii, phase-xxxviii, phase-xxxix)

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
- [ ] `pytest` passes (if tests modified)
- [ ] Zero-Storage compliance verified (if new data handling)
- [ ] Sprint status → COMPLETE, Review section added
- [ ] Lessons added to `lessons.md` (if corrections occurred)
- [ ] `git add <files> && git commit -m "Sprint X: Description"`

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Multi-Currency Conversion | **COMPLETE — Phase XXXIV (v1.3.0)** | Phase VII |
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Dual-key rate limiting | IP-only + lockout adequate for now | Phase XX |
| Wire Alembic into startup | Latency + multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` dir | Model count doesn't justify yet | Phase XXII |
| Cookie-based auth (SSR) | Large blast radius; requires JWT → httpOnly cookie migration | Phase XXVII |
| Marketing pages SSG | Requires cookie auth first | Phase XXVII |
| Frontend test coverage (30%+) | **RESOLVED** — 83 suites, 44% statements, 35% branches, 25% threshold | Phase XXXVII |
| ISA 520 Expectation Documentation Framework | **RESOLVED** — Scheduled as Phase XL Sprint 298 with blank-only guardrail | Council Review (Phase XL) |
| pandas 3.0 upgrade | CoW + string dtype breaking changes; needs dedicated evaluation sprint | Phase XXXVII |
| React 19 upgrade | Major version with breaking changes; needs own phase | Phase XXXVII |

---

## Active Phase

#### Phase XL: Diagnostic Completeness & Positioning Hardening (Sprints 292–299) — PLANNED
> **Focus:** Close 6 TB-derivable analytical gaps + fix 4 language/positioning risks identified by AccountingExpertAuditor
> **Source:** AccountingExpertAuditor capability gap analysis (2026-02-18) + Agent Council evaluation
> **Strategy:** Quick wins first (F3+language), then ratio extension, then flux enhancements, then FS trace, density, and expectation scaffold last (most guardrail-sensitive)
> **Version Target:** 1.8.0
> **Guardrail:** All computed output must be factual/numerical — no evaluative language, no auto-suggestions, no audit terminology

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 292 | Revenue Concentration Sub-typing + Language Fixes (L1, L3, L4) | 2/10 | BackendCritic + QualityGuardian | COMPLETE |
| 293 | Cash Conversion Cycle (DPO + DIO + CCC) | 3/10 | BackendCritic | COMPLETE |
| 294 | Interperiod Reclassification Detection + L2: variance_indicators rename | 4/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 295 | TB-to-FS Arithmetic Trace Enhancement | 3/10 | BackendCritic | COMPLETE |
| 296 | Account Density Profile | 3/10 | BackendCritic | COMPLETE |
| 297 | ISA 520 Expectation Documentation Scaffold (frontend fields + export) | 4/10 | FrontendExecutor + QualityGuardian | PLANNED |
| 298 | Language Fix Cleanup + Frontend Tests for Phase XL features | 3/10 | QualityGuardian + FrontendExecutor | PLANNED |
| 299 | Phase XL Wrap + v1.8.0 | 2/10 | QualityGuardian | PLANNED |

---

**Sprint 292: Revenue Concentration Sub-typing + Language Fixes (2/10) — COMPLETE**
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

**Sprint 293: Cash Conversion Cycle — DPO + DIO + CCC (3/10) — COMPLETE**
- [x] Added `accounts_payable: float = 0.0` to `CategoryTotals` + `to_dict()` + `from_dict()`
- [x] Updated `extract_category_totals()` with `ACCOUNTS_PAYABLE_KEYWORDS` (accounts payable, trade payable, vendor payable, a/p)
- [x] Added `calculate_dpo()`: `(AP / COGS) × 365` with zero COGS guard
- [x] Added `calculate_dio()`: `(Inventory / COGS) × 365` with zero COGS guard
- [x] Added `calculate_ccc()`: `DIO + DSO - DPO` with null propagation via component results
- [x] Added threshold constants: DPO (30/60/90), DIO (30/60/90), CCC_NEGATIVE_THRESHOLD = -30
- [x] Updated `calculate_all_ratios()`: 9 → 12 ratios
- [x] Factual interpretations only: "Rapid/Standard/Extended payment cycle", "Short/Standard/Extended cash cycle"
- [x] Frontend auto-renders via existing KeyMetricsSection pattern (no changes needed)
- [x] Tests: 24 new (5 DPO, 5 DIO, 5 CCC, 5 AP extraction, 4 integration). 2 existing tests updated (ratio count 9→12)
- [x] Verification: 3,585 backend tests passed, frontend build clean
- **Review:** All interpretations factual. No evaluative language.

**Sprint 294: Interperiod Reclassification Detection + L2 Rename (4/10) — COMPLETE**
- [x] F4: Added `has_reclassification: bool`, `prior_type: str` to `FluxItem` dataclass
- [x] F4: In `FluxEngine.compare()`, compare `curr_type` vs `prior_type` (case-insensitive, both non-Unknown)
- [x] F4: Added "Account Type Reclassification: X → Y" indicator, escalates to MEDIUM minimum
- [x] F4: Case-insensitive type comparison suppresses "Asset" vs "asset" false positives
- [x] F4: Updated `FluxResult.to_dict()` with `has_reclassification`, `prior_type` per item
- [x] F4: Added `reclassification_count` to `FluxResult` summary and `to_dict()`
- [x] L2: Renamed `risk_reasons` → `variance_indicators` in `FluxItem` dataclass
- [x] L2: `to_dict()` emits both `variance_indicators` and `risk_reasons` (backward compat alias)
- [x] L2: Updated `FluxItemResponse` and `FluxSummaryResponse` Pydantic schemas
- [x] L2: Updated `FluxItem` interface + `FluxSummary` in `diagnostic.ts`
- [x] L2: Updated `export_schemas.py`, `export_diagnostics.py`, `leadsheet_generator.py`
- [x] L2: Updated flux page to use `variance_indicators`, test_recon_engine updated
- [x] Tests: 13 new (9 reclassification + 4 rename/backward compat). 1 existing updated.
- [x] Verification: 3,598 backend tests passed, frontend build clean
- **Review:** Reclassification is factual: "Account Type Reclassification: X → Y". No evaluative language.

**Sprint 295: TB-to-FS Arithmetic Trace Enhancement (3/10) — COMPLETE**
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

**Sprint 296: Account Density Profile (3/10) — COMPLETE**
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

**Sprint 297: ISA 520 Expectation Documentation Scaffold (4/10)**
- [ ] Frontend: Create `FluxItemWithExpectation` type extending `FluxItem` with `auditor_expectation: string` and `auditor_explanation: string` (browser-only state)
- [ ] Frontend: Add editable text inputs per flagged flux item in Multi-Period comparison results
- [ ] Frontend: Local state management for expectation fields (React state, never sent to backend except at export time)
- [ ] Frontend: Disclaimer watermark on expectation fields: "Practitioner-documented expectation — not generated by Paciolus"
- [ ] Backend: Add optional `expectations: dict[str, ExpectationEntry]` parameter to flux memo export endpoint
- [ ] Backend: Render expectations into PDF memo section titled "Practitioner Expectations vs. Observed Variances"
- [ ] Backend: Update ISA 520 disclaimer to explicitly state expectations are user-authored
- [ ] Frontend: Pass expectation data to export endpoint at download time
- [ ] Tests: ~12 new (blank-only enforcement, export with/without expectations, disclaimer presence, no auto-populate)
- [ ] Verification: pytest + npm run build
- **CRITICAL GUARDRAIL:** Fields MUST be blank. Auto-suggest is FORBIDDEN. Any computed pre-fill crosses the ISA 520 assurance boundary. This is the single highest guardrail-risk feature in Phase XL.

**Sprint 298: Language Fix Cleanup + Frontend Tests (3/10)**
- [ ] L2 cleanup: Remove `risk_reasons` alias from backend (keep only `variance_indicators`)
- [ ] Frontend tests: AccrualCompletenessSection, ExpenseCategorySection, PopulationProfileSection (Phase XXXIX sections with 0 coverage)
- [ ] Frontend tests: New Phase XL components (density callout, expectation fields)
- [ ] Verify all 13+ memos have consistent ISA citation disclaimers (L4 regression check)
- [ ] Verify narrative guardrail tests pass for all engines (L1 regression)
- [ ] Tests: ~15 new frontend tests
- [ ] Verification: full pytest + npm run build + npm test

**Sprint 299: Phase XL Wrap + v1.8.0 (2/10)**
- [ ] Full backend regression
- [ ] Full frontend build
- [ ] Version bump: package.json 1.7.0 → 1.8.0
- [ ] Archive sprint details to `tasks/archive/phase-xl-details.md`
- [ ] Update CLAUDE.md + MEMORY.md
- [ ] AccountingExpertAuditor guardrail verification (6/6 features pass language review)

