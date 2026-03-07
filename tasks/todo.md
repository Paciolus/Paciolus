# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md). Engineering adds to it automatically at the end of each sprint.

---

## Phase Lifecycle Protocol

**MANDATORY:** Follow this lifecycle for every phase. This eliminates manual archive requests.

### During a Phase
- Active phase details (audit findings, sprint checklists, reviews) live in this file under `## Active Phase`
- Each sprint gets a checklist section with tasks, status, and review

### On Phase Completion (Wrap Sprint)
1. **Regression:** `pytest` + `npm run build` + `npm test` must pass
2. **Archive:** Move all sprint checklists/reviews to `tasks/archive/phase-<name>-details.md`
3. **Summarize:** Add a one-line summary to `## Completed Phases` below (with test count if changed)
4. **Clean this file:** Delete the entire `## Active Phase` section content, leaving only the header ready for the next phase
5. **Update CLAUDE.md:** Add phase to completed list, update test count + current phase
6. **Update MEMORY.md:** Update project status
7. **Commit:** `Sprint X: Phase Y wrap — regression verified, documentation archived`

**The `## Active Phase` section should ONLY contain the current in-progress phase. Once complete, it becomes empty until the next phase begins.**

**Archival threshold:** If the Active Phase accumulates 5+ completed sprints without a named phase wrap, archive them immediately as a standalone batch to `tasks/archive/`. Do not wait for a phase boundary.

---

## Completed Phases

> **Full sprint checklists:** `tasks/archive/` (per-phase detail files)

### Era 1: Core Platform — Phases I–IX (Sprints 1–96)
> TB analysis, streaming, classification, 9 ratios, anomaly detection, benchmarks, lead sheets, adjusting entries, email verification, Multi-Period TB (Tool 2), JE Testing (Tool 3), Financial Statements (Tool 1), AP Testing (Tool 4), Bank Rec (Tool 5), Cash Flow, Payroll Testing (Tool 6), Three-Way Match (Tool 7), Classification Validator.

### Era 2: Engagement & Growth — Phases X–XII (Sprints 96.5–120)
> Engagement layer + materiality cascade, tool-engagement integration, Revenue Testing (Tool 8), AR Aging (Tool 9), Fixed Asset Testing (Tool 10), Inventory Testing (Tool 11). **v1.1.0**

### Era 3: Polish & Hardening — Phases XIII–XVI (Sprints 121–150)
> Dual-theme "The Vault", WCAG AAA, 11 PDF memos, 24 exports, marketing/legal pages, code dedup (~4,750 lines removed), API hygiene. **v1.2.0. Tests: 2,593 + 128.**

### Era 4: Architecture — Phases XVII–XXVI (Sprints 151–209)
> 7 backend shared modules, async remediation, API contract hardening, rate limits, Pydantic hardening, Pandas precision, upload/export security, JWT hardening, email verification hardening, Next.js App Router. **Tests: 2,903 + 128.**

### Era 5: Production Readiness — Phases XXVIII–XXXIII (Sprints 210–254)
> CI pipeline, structured logging, type safety, frontend test expansion (389→520 tests), backend test hardening (3,050 tests), error handling, Docker tuning. **Tests: 3,050 + 520.**

### Era 6: v1.3–v1.8 Features — Phases XXXIV–XLI (Sprints 255–312)
> Multi-Currency (Tool 12, ISA 530), in-memory state fix, Statistical Sampling, deployment hardening, Sentry APM, security/accessibility hardening, TB Population Profile, Convergence Index, Expense Category, Accrual Completeness, Cash Conversion Cycle, cross-tool workflow integration. **v1.8.0. Tests: 3,780 + 995.**

### Era 7: Design System — Phases XLII–LV + Standalone Sprints (Sprints 313–400)
> Oat & Obsidian token migration, homepage "Ferrari" transformation, tool pages refinement, IntelligenceCanvas, Workspace Shell "Audit OS", Proof Architecture, typography system, command palette, BrandIcon. **v1.9.0–v1.9.5. Tests: 4,252 + 1,057.**

### Era 8: Data Integrity & Billing — Phases XLV–L (Sprints 340–377)
> Monetary precision (Float→Numeric), soft-delete immutability, ASC 606/IFRS 15 contract testing, adjustment approval gating, diagnostic features (lease/cutoff/going concern), Stripe integration, tiered billing. **v2.0.0–v2.1.0. Tests: 4,176 + 995.**

### Era 9: Refinement & Formats — Phases LVI–LVIII + Standalone (Sprints 401–438)
> State-linked motion, premium moments, lint remediation (687→0), accessibility (51→0), Husky hooks, 10 file format parsers (TSV/TXT/OFX/QBO/IIF/PDF/ODS), Prometheus metrics, tier-gated formats. **Tests: ~4,650 + ~1,190.**

### Era 10: Pricing & Coverage — Sprints 439–448 + Phases LIX–LXIII
> Hybrid pricing overhaul (Solo/Team/Organization), billing analytics, React 19, Python 3.12, pandas 3.0 eval, entitlement wiring, export test coverage (17%→90%), report standardization (79 new tests), compliance documentation pack. **Tests: 5,618 + 1,345.**

### Era 11: Security & SOC 2 — Phases LXIV–LXVI (Sprints 449–469)
> HttpOnly cookie sessions, CSP nonce, billing redirect integrity, CSRF model upgrade, verification token hashing, PostgreSQL TLS guard, SOC 2 readiness (42 criteria assessed: 10 Ready/28 Partial/4 Gap), PR security template, risk register, training framework, access review, weekly security review, DPA workflow, audit chain, GPG signing docs. **Tests: 5,618 + 1,345.**

### Era 12: Code Quality & Pricing v3 — Phases LXVII–LXIX + Standalone (Sprints 450b–476)
> Visual polish (ToolPageSkeleton, CountUp, MagneticButton, ParallaxSection), marketing pages overhaul (7 sprints), mypy type annotations (214 errors → 0 non-test), Pricing Restructure v3 (Free/Solo/Professional/Enterprise, all paid = all tools, org entities, export sharing, admin dashboard, PDF branding, bulk upload), motion system consolidation (lib/motion.ts + Reveal.tsx), VaultTransition/HeroProductFilm/About rewrites, security hardening (7 fixes), comprehensive security audit (14 fixes incl. 1 critical). **Tests: 5,618 + 1,345.**

### Era 13: Report Engine & UX Polish — Sprints 477–487
> Copy consistency remediation, Digital Excellence Council audits (2 rounds, 24 findings fixed), pricing page redesign, HeroProductFilm rewrite, homepage atmospheric backgrounds, report engine content audit (4 bug fixes, 6 drill-downs, 11 content additions, 1 new report, 5 enhancements), TB Diagnostic enrichment (suggested procedures, risk scoring, population composition, concentration benchmarks, cross-references). **Tests: 5,618 + 1,345.**

### Era 14: Security Hardening & Quality — Sprints 478, 488–497
> Deprecated alias migration (21 exports), financial statements enrichment (4 new ratios, prior year columns, footnotes), JE/AP report fixes (7 bugs + 5 improvements), Digital Excellence Council remediations (2 rounds: 42 findings fixed, 10 methodology corrections, 26 test fixes), security audit quadrilogy (data 11 fixes, access 8 fixes, surface area 9 fixes, engineering process 7 fixes), 61 injection regression tests, CI hardening (secrets scanning, frontend tests, mypy gate, CODEOWNERS), logging/observability audit (26 fixes), formula consistency hardening. **Tests: 5,776 + 1,345.**

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
- [ ] `npm test` passes (frontend Jest suite)
- [ ] `pytest` passes (if tests modified)
- [ ] Zero-Storage compliance verified (if new data handling)
- [ ] Sprint status → COMPLETE, Review section added
- [ ] Lessons added to `lessons.md` (if corrections occurred)
- [ ] **If sprint produced CEO actions:** add them to [`tasks/ceo-actions.md`](ceo-actions.md)
- [ ] `git add <files> && git commit -m "Sprint X: Description"`
- [ ] Record commit SHA in sprint Review section (e.g., `Commit: abc1234`)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Wire Alembic into startup | Latency + multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` dir | Model count doesn't justify yet | Phase XXII |
| Marketing pages SSG | HttpOnly cookie prereq met. SSG deferred — requires Next.js SSR wiring | Phase XXVII |
| Phase LXIX frontend pages | Admin dashboard, branding settings, share UI components | Phase LXIX |
| Test file mypy annotations | 68 errors across 2 files — zero runtime risk | Sprint 475 |
| Deprecated alias migration | **RESOLVED** — Completed in Sprint 478/491 (commit 6a2f66b) | Sprint 477 |

---

## Active Phase

> Sprints 478, 488–497 archived to `tasks/archive/sprints-478-497-details.md`. Pending items below.


### Sprint 512 — Expense Category Report Enrichment
**Status:** COMPLETE
**Goal:** Fix 3 bugs and add 4 new sections to the Expense Category Analytical Procedures report (Report 18): doubled word fix, reference number addition, authoritative reference correction, % Change column, period-over-period build-out, expense ratio analysis, findings register, suggested audit procedures.

#### Bug Fixes
- [x] BUG-01: Fix doubled word "procedures procedures" in Scope narrative — changed domain_label from "expense category analytical procedures" to "expense category analytical" so template produces correct text
- [x] BUG-02: Add reference number to cover page — ECA- prefix (e.g., `ECA-2026-0307-694`), passed to ReportMetadata and header
- [x] BUG-03: Fix authoritative references — replaced single ASC 720-10 with AU-C § 520 (AICPA), AS 2305 (PCAOB), ASC 220-10, ASC 720-10. No ASC 250-10 present. Updated both FASB and GASB YAMLs.

#### New Sections
- [x] SEC-01: Section II enhancement — % Change column with directional indicators (↑/↓), ⚠ marker for >15% changes, prior period source footnote
- [x] SEC-02: Section III — Period-Over-Period Comparison build-out: III-A Variance Summary table (6 columns with risk level assignment), III-B Per-Category Variance Commentary (dynamic text per category type), III-C Other Operating Expenses decomposition flag (triggers at >10% revenue + >15% YoY growth)
- [x] SEC-03: Section IV — Expense Ratio Analysis with benchmark comparison (5 ratio types, benchmark ranges for professional services/capital management, Within/Below/Above Range flags, benchmark caveat footnote)
- [x] SEC-04: Section V — Findings register consolidating variance and benchmark findings, sorted by priority (High → Moderate → Low)
- [x] SEC-05: Section VI — Suggested Audit Procedures dynamically generated from findings, with specific dollar amounts and percentages, sorted by priority

#### Enhancements
- [x] ENH-01: Risk level assignment: High (≥20% + exceeds materiality), Moderate (≥10% or exceeds materiality), Low (otherwise)
- [x] ENH-02: Benchmark ranges: COGS (30-55%), Payroll (15-35%), D&A (2-8%), Interest & Tax (3-10%), Other Operating (5-12%)
- [x] ENH-03: Dynamic commentary generation per expense category type (COGS → gross margin, Payroll → headcount, D&A → capex, Interest/Tax → debt/rate, Other → sub-ledger)

#### Files Modified
- `shared/authoritative_language/fasb_scope_methodology.yml` — expense_category: ASC 720-10 → AU-C § 520 (AICPA) + AS 2305 (PCAOB) + ASC 220-10 + ASC 720-10
- `shared/authoritative_language/gasb_scope_methodology.yml` — expense_category: Statement No. 62 → AU-C § 520 (AICPA) + AS 2305 (PCAOB) + Statement No. 62
- `expense_category_memo.py` — Complete rewrite: ECA- reference prefix, fixed domain_label, 7-column category table with % Change, variance summary table, per-category commentary, decomposition flag, expense ratio table with benchmarks, findings register, suggested procedures, `_pct_change()`, `_pct_change_str()`, `_assign_risk()`, `_benchmark_flag()`, `_generate_variance_commentary()`, `_generate_procedures()`, `_standard_table_style()`
- `generate_sample_reports.py` — gen_expense_category: added prior_pct_of_revenue for all 5 categories, added prior_revenue ($6,200,000) and prior_total_expenses ($4,880,000)
- `tests/test_expense_category_memo.py` — 44 new tests: pct_change (5), pct_change_str (4), assign_risk (5), benchmark_flag (6), variance_commentary (6), generate_procedures (6), PDF generation (7), scope statement (1), authoritative references (4)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (6,094+44 new = 6,138 total)
- [x] Regenerated all 21 sample PDFs — expense category: 45,939 bytes (up from ~30KB), 5 pages (up from 3)
- [x] No other reports unintentionally modified
- **Commit:** `5fa510b`

#### Acceptance Criteria
- [x] Doubled word "procedures procedures" removed from Section I narrative
- [x] Reference number (ECA- prefix) added to cover page
- [x] % Change column added to Category Breakdown table with directional indicators
- [x] Prior period source footnote added to Category Breakdown table
- [x] Section III fully built out: variance summary table, per-category commentary, Other Operating decomposition flag
- [x] Section IV — Expense Ratio Analysis present with benchmark comparison
- [x] Section V — Findings register present, sourced from Sections III and IV
- [x] Section VI — Suggested Procedures present, dynamically generated from findings
- [x] Authoritative references corrected: AU-C § 520, AS 2305, ASC 220-10, ASC 720-10
- [x] No ASC 250-10 reference present
- [x] All commentary and procedures reference actual computed values, not hardcoded text

---

### Sprint 511 — TB Population Profile Report Enrichment
**Status:** COMPLETE
**Goal:** Fix 2 systemic bugs and add 6 new sections to the Population Profile Report (Report 17): authoritative reference correction, magnitude bucket math fix, account type stratification, Benford's Law analysis, exception flags, suggested procedures, concentration table enhancement, data quality score computation.

#### Bug Fixes
- [x] BUG-01: Remove ASC 250-10 from FASB/GASB YAMLs; add AU-C § 520, AU-C § 530, AS 2305 (AICPA/PCAOB body overrides)
- [x] BUG-02: Fix >$1M magnitude bucket sum in sample data — redesigned self-consistent sample data (bucket sums verified equal total: $12,847,392.50). Added totals verification row in memo PDF. Reduced >$1M count from 7 to 3 (minimum-sum consistency).

#### New Sections
- [x] SEC-01: Section IV-A — Account Type Stratification (5 types: Asset/Liability/Equity/Revenue/Expense + Unknown, with count, % of accounts, total balance, % of population, >40% disproportionate flag)
- [x] SEC-02: Section IV-B — Benford's Law Analysis (reuses `shared/benford.py` with relaxed min_entries=10; digit table 1-9, expected/observed/variance; chi-square, MAD, conformity level; Nigrini threshold footnote)
- [x] SEC-03: Section V — Exception Flags (V-A: Normal Balance Violations per NORMAL_BALANCE_SIGN map with introductory narrative, V-B: Zero ($0) and Near-Zero (≤$100) balances, V-C: Dominant Accounts >10% with risk notes)
- [x] SEC-04: Section VI — Suggested Audit Procedures (dynamically generated: Benford deviation, normal balance violations, concentration risk, dominant accounts, zero/near-zero accounts; sorted by priority High→Low; references AS 2305)

#### Enhancements
- [x] ENH-01: Concentration table — account_number column added to TopAccount dataclass and concentration table (conditional rendering when data present)
- [x] ENH-02: Gini thresholds — updated from (0.3/Low, 0.5/Moderate, 0.7/High, Very High) to (0.40/Low, 0.65/Moderate, High). "Very High" label removed. Threshold footnote rendered in Scope section.
- [x] ENH-03: Data Quality Score — dynamically computed from 3 weighted components: Completeness 40%, Normal Balance Compliance 35%, Active Balances 25%. Score breakdown table in Section II. Score displayed in Scope leader dots.

#### Files Modified
- `shared/authoritative_language/fasb_scope_methodology.yml` — population_profile: ASC 250-10 → AU-C § 520 + AU-C § 530 + AS 2305
- `shared/authoritative_language/gasb_scope_methodology.yml` — population_profile: GASB 34 → AU-C § 520 + AU-C § 530 + AS 2305
- `population_profile_engine.py` — complete rewrite: 8 new dataclasses (AccountTypeStratum, NormalBalanceViolation, ZeroBalanceAccount, DominantAccountFlag, ExceptionFlags, SuggestedProcedure, DataQualityScore, BucketBreakdown updated), 5 new computation functions (_compute_account_type_stratification, _compute_exception_flags, _generate_suggested_procedures, _compute_data_quality, Benford integration), updated GINI_THRESHOLDS, TopAccount.account_number field
- `population_profile_memo.py` — complete rewrite: 6 new sections (IV-A Stratification, IV-B Benford, V Exception Flags with 3 subsections, VI Procedures), data quality breakdown table, interpretive narrative after Descriptive Statistics/Magnitude/Concentration, Gini threshold footnote, bucket totals verification row, dynamic disclaimer references
- `shared/diagnostic_response_schemas.py` — PopulationProfileResponse: gini_interpretation Literal updated (removed "Very High"), added account_type_stratification, benford_analysis, exception_flags, suggested_procedures, data_quality fields. TopAccountResponse: added account_number.
- `shared/export_schemas.py` — PopulationProfileMemoInput: 5 new fields (account_type_stratification, benford_analysis, exception_flags, suggested_procedures, data_quality)
- `generate_sample_reports.py` — gen_population_profile: complete rewrite with self-consistent sample data (10 top accounts, 6 magnitude buckets, 5 account type strata, Benford analysis, 3 normal balance violations, 4 zero-balance + 2 near-zero, 2 dominant accounts, 5 suggested procedures, data quality score)
- `tests/test_population_profile_engine.py` — 54 tests (up from 22): +5 Gini threshold tests, +3 stratification tests, +8 exception flag tests, +4 suggested procedure tests, +4 data quality tests, +4 profile integration tests, +2 bucket verification tests, +2 account number tests

#### Verification
- [x] `npm run build` passes (all ƒ Dynamic)
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (6,094 passed, 0 failures — up from 6,068)
- [x] Regenerated all 21 sample PDFs — population profile: 49,477 bytes (up from ~30KB), 6 pages (up from 3). Suite range: 3–8 pages.
- [x] No other reports unintentionally modified

#### Acceptance Criteria
- [x] ASC 250-10 reference removed; AU-C § 520, AU-C § 530, AS 2305 substituted (FASB + GASB YAMLs)
- [x] Magnitude bucket sums verified to aggregate correctly; >$1M bucket no longer shows single-account value
- [x] All bucket sums equal total population value (totals row added in PDF)
- [x] Account type stratification table present with per-type count, balance, and % of population
- [x] Benford's Law table present: digits 1–9, observed %, expected %, variance; chi-square, MAD, and conformance conclusion
- [x] Gini thresholds (Low/Moderate/High) defined explicitly in report (Scope section footnote)
- [x] Normal balance violations flagged (3 in sample) with introductory narrative
- [x] Zero-balance (4) and near-zero (2) accounts flagged
- [x] Concentration table includes account numbers (conditional column)
- [x] Section VI procedures dynamically generated from findings (5 procedures in sample), sorted by priority
- [x] Data quality score computed dynamically (94.8% in sample), not hardcoded — breakdown table in Section II
- [x] Report renders to 6 pages (vs. current 3) — consistent with suite range (3–8 pages)

---

### Sprint 508 — Statistical Sampling Evaluation Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix 6 bugs and add 2 improvements to the Statistical Sampling Evaluation memo: phase-specific titles, evaluation next steps, UEL derivation, PASS/FAIL visual, error nature/direction columns, correction status conditional, error summary statistics, ASC 450-20 footnote.

#### Bug Fixes
- [x] BUG-01: Phase-specific titles — "STATISTICAL SAMPLING MEMO — DESIGN" vs "— EVALUATION" on cover page and header
- [x] BUG-02: Evaluation-phase next steps — 5 post-evaluation steps (communicate errors, obtain correction, assess uncorrected, update rep letter, cross-reference) replace design-phase testing instructions. Dynamic intro text with UEL/TM/confidence. PASS intro says "accepted", FAIL intro says "cannot be accepted" + ISA 530.17.
- [x] BUG-03: UEL derivation block — full Stringer bound computation showing Basic Precision (SI × CF), Projected Misstatement (per-error tainting × SI), Incremental Allowance (per-error tainting × SI × (factor - 1.0) with Poisson factors), UEL sum, and PASS/FAIL inline. Self-consistent sample data: SI = $16,666.67 (corrected from $25,000), BP = $50,000, Projected = $10,036.67, Incremental = $4,135.02, UEL = $64,171.69 < TM $75,000.
- [x] BUG-04: PASS/FAIL visual conclusion block — styled table with checkmark/X symbol, UEL vs TM comparison, confidence + error count. Sage border for PASS, clay for FAIL. Computed from `uel < tm`, never hardcoded.
- [x] BUG-05: Error Nature + Direction columns — 8-column table (with Nature/Direction) when fields present, 6-column fallback for legacy data. Totals row with direction summary ("All overstated"/"Mixed"). ERROR_NATURE_OPTIONS constant: Pricing error, Cut-off, Existence, Valuation, Classification, Other.
- [x] BUG-06: Correction status conditional — "Not confirmed" default when no practitioner input; "confirmed" path with ISA 450 documentation note. Removed auto-generated "corrected in subsequent period" from conclusion_detail.

#### Improvements
- [x] IMP-01: Error summary statistics block — error rate (3/207 = 1.4%), total actual misstatement, direction summary, nature summary, largest error (INV-4102 $3,580 = 84.6%), projected vs expected ($4,964.33 below expected — favorable), UEL headroom ($10,828.31 = 14.4% remaining).
- [x] IMP-02: ASC 450-20 relevance footnote — evaluation-only footnote: "ASC 450-20 applies when identified misstatements indicate a probable loss contingency..."

#### Arithmetic Resolution
- [x] Investigated projected misstatement discrepancy: original sample data had SI = $25,000 (EM=0 case) but with CF=3.0, BP = SI×CF = $75,000 = TM, making PASS impossible with any errors. Root cause: hardcoded values not computed from Stringer bound formula.
- [x] Fixed: SI recomputed via engine formula with EM = $15,000: SI = (TM-EM)/(CF×(1+EM/TM)) = 60000/3.6 = $16,666.67. All Stringer bound components now self-consistent. Verified: BP($50,000) + Projected($10,036.67) + Incremental($4,135.02) = UEL($64,171.69) < TM($75,000) = PASS.

#### Files Modified
- `sampling_memo_generator.py` — complete rewrite: phase-specific titles, PASS/FAIL visual block (`_build_pass_fail_block`), error summary (`_build_error_summary`), UEL derivation (`_build_uel_derivation`), evaluation next steps (`_build_evaluation_next_steps`), 8-column error table with Nature/Direction + totals row, correction status conditional, ASC 450-20 footnote, sample preview excluded from evaluation reports, `ERROR_NATURE_OPTIONS` constant, `_INCREMENTAL_FACTORS_95` for derivation display
- `generate_sample_reports.py` — gen_sampling_design: SI $25,000→$16,666.67, calc_size 194→291. gen_sampling_evaluation: BP $25,000→$50,000, projected $12,480→$10,036.67, incremental $8,750→$4,135.02, UEL $46,230→$64,171.69, added error_nature/direction/sampling_interval/expected_misstatement, removed "corrected in subsequent period" from conclusion_detail, added Stringer bound computation comment block
- `tests/test_sampling_memo.py` — 40 new tests (98 total, up from 58): phase titles (3), evaluation next steps (12), UEL derivation (6), PASS/FAIL block (3), error nature/direction (5), correction status (3), error summary (5), ASC 450-20 footnote (2), preview exclusion (2)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (6,041 passed, 0 skipped, 0 errors — up from 6,001)
- [x] Regenerate all 21 sample PDFs — all OK, design 46,406 bytes, evaluation 48,278 bytes (up from 45,845)

#### Review
All verification items confirmed:
- Report title: "STATISTICAL SAMPLING MEMO — EVALUATION" (design shows "— DESIGN")
- Section VII: 5 evaluation-phase next steps (communicate errors, obtain correction, assess uncorrected, update rep letter, cross-reference)
- Step 1 references "3 identified errors ($4,230.00 total)"
- Step 3 references ISA 450
- Step 4 references ISA 580
- UEL Derivation block: Basic Precision ($50,000 = $16,666.67 × 3.0000), 3 projected errors, 3 incremental allowance lines with Poisson factors (1.58, 1.30, 1.15), UEL sum $64,171.69
- Derivation reconciles: $50,000 + $10,036.67 + $4,135.02 = $64,171.69 ✓
- Projected misstatement discrepancy resolved: original $12,480 was hardcoded with wrong SI ($25,000 for EM=0); corrected to $10,036.67 with SI=$16,666.67 (EM=$15,000)
- PASS/FAIL visual block: sage border, checkmark, "UEL $64,171.69 < TM $75,000.00"
- Error detail table: 8 columns (Nature + Direction), all "Pricing error" + "Overstatement"
- Totals row: $4,230.00 total, "All overstated"
- "Corrected in subsequent period" replaced: "Correction status: Not confirmed"
- Error summary: 1.4% error rate, INV-4102 84.6% of total, $4,964.33 below expected (favorable), headroom $10,828.31 (14.4%)
- ASC 450-20 footnote present (evaluation only, not design)
- Sample Selection Preview excluded from evaluation report
- Section numbering: I Scope, II Design Parameters, III Stratification, IV Evaluation Results, V Methodology, VI Conclusion, VII Next Steps
- No other reports unintentionally modified (all 21 regenerated)
- Test count: 6,041 backend (up from 6,001 — +40 new) + 1,329 frontend
- **Commit:** `9fa1ed8`

---

### Sprint 510 — Data Quality Pre-Flight Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix 4 bugs and add 4 improvements to the Data Quality Pre-Flight Report: severity column word-wrap, wrong authoritative reference, missing conclusion, missing TB balance check, score derivation, low-confidence remediation, named account lists, downstream impact ranking.

#### Bug Fixes
- [x] BUG-01: Widen severity column from 0.55 to 0.75 inch to prevent "MEDI UM" word-wrap. Added "Tests" column (0.4 inch). Redistributed column widths across 7 columns summing to 7.0 inch.
- [x] BUG-02: Replace ASC 250-10 with ISA 500, ISA 330, ISA 315 in both FASB and GASB YAMLs for data_quality_preflight. Per-reference body overrides (IAASB). Disclaimer updated to reference ISA 500/330/315.
- [x] BUG-03: Add dynamic Conclusion section with caveats built from issue list. Balanced TB → caveats from issues sorted by tests_affected. Unbalanced TB → blocker message (no caveats, just "obtain corrected TB").
- [x] BUG-04: Add `_check_tb_balance()` as Check 0 (weight 25%). `BalanceCheck` dataclass with total_debits, total_credits, difference, balanced, tolerance. Renders as Section II "Trial Balance Integrity Check" with leader dots and status indicator. Unbalanced → HIGH severity issue (tests_affected=12).

#### Improvements
- [x] IMP-01: `ScoreComponent` dataclass. `_calculate_readiness()` now returns `(score, breakdown)` tuple. 7 weighted components: TB Balance (25%), Column Detection (20%), Data Completeness (15%), Duplicate Detection (10%), Encoding Quality (5%), Sign Convention (15%), Active Balances (10%). Renders as "Readiness Score Breakdown" table in Scope section with component names, weights, scores, contributions, and bold total row.
- [x] IMP-02: Low-confidence column remediation notes. After Column Detection table, any column with confidence < 80% gets italic remediation note with role name, confidence, detected column name, and recommendation to use column override.
- [x] IMP-03: `affected_items: list[str]` field on `PreFlightIssue`. Each check function now collects identifiers: account names for encoding/mixed_signs/duplicates/zero_balance, row identifiers for null_values. `to_dict()` caps at 10 items with `affected_items_truncated` flag and `affected_items_total` count. Renders as italic footnotes below issues table.
- [x] IMP-04: `tests_affected: int` field on `PreFlightIssue`. `TESTS_AFFECTED_BY_CATEGORY` dict maps each issue category to downstream test count (e.g., column_detection=12, encoding=3). Issues table sorted by tests_affected descending. New "Tests" column in PDF table.

#### Weight Redistribution
Old weights: column_detection=30, null_values=20, duplicates=15, encoding=10, mixed_signs=15, zero_balance=10 (total=100)
New weights: tb_balance=25, column_detection=20, null_values=15, duplicates=10, encoding=5, mixed_signs=15, zero_balance=10 (total=100)

#### Files Modified
- `shared/authoritative_language/fasb_scope_methodology.yml` — data_quality_preflight: ASC 250-10 → ISA 500 + ISA 330 + ISA 315 (IAASB body overrides)
- `shared/authoritative_language/gasb_scope_methodology.yml` — data_quality_preflight: GASB 34 → ISA 500 + ISA 330 + ISA 315 (IAASB body overrides)
- `shared/diagnostic_response_schemas.py` — `PreFlightIssueResponse`: +downstream_impact, +affected_items, +affected_items_truncated, +affected_items_total, +tests_affected. New `PreFlightBalanceCheckResponse` and `PreFlightScoreComponentResponse` models. `PreFlightReportResponse`: +balance_check, +score_breakdown
- `preflight_engine.py` — `BalanceCheck`, `ScoreComponent` dataclasses. `_check_tb_balance()` function. `_calculate_readiness()` returns breakdown. `TESTS_AFFECTED_BY_CATEGORY` and `DOWNSTREAM_IMPACT` dicts updated. `affected_items` populated in all check functions. `LOW_CONFIDENCE_THRESHOLD` constant. Weight redistribution.
- `preflight_memo_generator.py` — Complete restructure: Section numbering (I Scope w/ breakdown, II Balance Check, III Column Detection w/ low-conf notes, IV Issues w/ Tests column + affected items, V References, VI Conclusion). Severity column 0.55→0.75 inch. `_build_conclusion()` dynamic text builder. `_COMPONENT_DISPLAY_NAMES` dict.
- `generate_sample_reports.py` — Enriched preflight data: balance_check, score_breakdown (7 components), 4 issues with downstream_impact/affected_items/tests_affected, updated categories and severity labels
- `tests/test_preflight.py` — 22 tests (up from 14): +3 balance check, +2 score breakdown, +2 affected items, +1 tests_affected, +3 to_dict serialization. Fixed test data: balanced TB in clean file test, adjusted assertion for new weight distribution.

#### Verification
- [x] `npm run build` passes (all Dynamic)
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (6,068 passed, 0 failures — up from 6,041)
- [x] Regenerated all 21 sample PDFs — preflight report 44,550 bytes (enriched)
- [x] No other reports unintentionally modified (all 21 regenerated, timestamp-only on non-preflight)
- **Commit:** `b70f9b4`

---

### Sprint 509 — Multi-Currency Conversion Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix 5 bugs and add 4 improvements to the Multi-Currency Conversion memo: unconverted count consistency, Roman numeral section headers, conclusion section, reference number collision, rate source contradiction, conversion output table, non-monetary account identification, CTA note, suggested rate sources.

#### Bug Fixes
- [x] BUG-01: Unconverted count in Scope derived from `len(truly_unconverted)` — separates stale_rate warnings from true failures. Sample data fixed: `unconverted_count` 12→4 to match 4 items.
- [x] BUG-02: Roman numeral section headers I–VII: I. Scope, II. Exchange Rates Applied, III. Conversion Output, IV. Unconverted Items, V. Methodology & Limitations, VI. Authoritative References, VII. Conclusion
- [x] BUG-03: Section VII Conclusion with conversion success rate, missing currency list, unconverted summary, and IAS 21/ASC 830-30 non-monetary reminder
- [x] BUG-04: Reference prefix changed from PAC- to MCY- (unique, non-colliding). Cross-reference in sample reports updated. All 17 report prefixes verified unique.
- [x] BUG-05: Rate source: methodology says "closing exchange rates provided by the practitioner" (accurate). Sample data `source_context_note` changed from "Reuters" to "provided by practitioner".

#### Improvements
- [x] IMP-01: Section III Conversion Output — `CurrencyExposure` dataclass in engine, per-currency aggregation (account count, foreign total, rate, USD equivalent, % of total), totals row. Fallback text when no exposure data.
- [x] IMP-02: Non-monetary account identification in Section V — metadata-unavailable variant lists Inventory, PP&E, Intangible Assets, Goodwill, Prepaid Expenses as likely requiring historical rate treatment
- [x] IMP-03: CTA note in Section V — manual-required variant: "CTA computation requires prior period closing rates... The practitioner should compute the CTA manually and record the adjusting entry to AOCI"
- [x] IMP-04: Suggested Rate Source column (6th column) in unconverted items table: "Federal Reserve H.10 or Reuters for [CCY]/USD". HIGH severity intercompany note below table when applicable. Rate source note below table.

#### Files Modified
- `currency_memo_generator.py` — complete rewrite: 7 Roman-numeral sections, MCY- prefix, `_build_conversion_output_table()`, `_build_unconverted_items_table()` with 6 columns, `_roman()` helper, `_format_currency_amount()`, non-monetary note, CTA note, conclusion section, stale_rate separation, intercompany HIGH severity warning
- `currency_engine.py` — `CurrencyExposure` dataclass, `_build_currency_exposure()` aggregation, `currency_exposure` field on `ConversionResult` + `to_dict()`
- `shared/export_schemas.py` — `currency_exposure: list = []` field on `CurrencyConversionMemoInput`
- `tests/test_currency_memo.py` — 25 tests (up from 8): section headers, unconverted count consistency (2), reference prefix, conversion output (2), non-monetary note, CTA note, suggested rate sources, intercompany HIGH severity (2), conclusion (2), export schema (4), engine dataclass (2)
- `generate_sample_reports.py` — sample data: `unconverted_count` 12→4, added `currency_exposure` (5 currencies), `source_context_note` Reuters→practitioner, cross-reference prefix PAC-→MCY-

#### Verification
- [x] `npm run build` passes (all ƒ Dynamic)
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (6,057 passed, 0 skipped, 0 errors — up from 6,041)
- [x] Regenerated sample PDF: 15_currency_conversion.pdf (44,901 bytes)
- [x] All 17 report reference prefixes verified unique (no collisions)
- **Commit:** `8a74690`

---

### Sprint 507 — Test Suite Fixes (Error + Skip)
**Status:** COMPLETE
**Goal:** Fix 1 error and 1 skipped test from Sprint 506 verification run.

#### Fixes
- [x] FIX-01: `test_workpaper_index_route_registered` teardown error — `Base.metadata.drop_all()` failed with `OperationalError: no such table: main.follow_up_items` due to circular FK cycle (organizations ↔ subscriptions ↔ users) with SQLite `PRAGMA foreign_keys=ON`. Fix: disable FK constraints before `drop_all` by removing the pragma event listener and executing `PRAGMA foreign_keys=OFF` explicitly.
- [x] FIX-02: `test_large_file_completes_in_time` unconditionally skipped — removed `@pytest.mark.skip` decorator and increased budget from 15s to 30s (actual runtime ~12-27s depending on machine load).

#### Files Modified
- `tests/conftest.py` — changed `@event.listens_for` to `event.listen()` for removable reference; added `event.remove()` + `PRAGMA foreign_keys=OFF` before `drop_all`; imported `text` from sqlalchemy
- `tests/test_audit_core.py` — removed `@pytest.mark.skip` from `test_large_file_completes_in_time`, increased budget 15s → 30s

#### Verification
- [x] `pytest tests/test_workpaper_index.py` — 17 passed, 0 errors
- [x] `pytest tests/test_audit_core.py -k large_file` — 2 passed (12-27s)
- [x] Full suite: **6,001 passed, 0 skipped, 0 errors** (up from 6,000 passed, 1 skipped, 1 error)

#### Review
- Circular FK warning persists (SAWarning about organizations/subscriptions/users cycle) — harmless since FKs are OFF during drop
- Test count: 6,001 backend + 1,345 frontend (net +1 from un-skipping)
- **Commit:** `d7a699f`

---

### Sprint 506 — Statistical Sampling Memo Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix authoritative references (BUG-01), population value discrepancy (BUG-02), sample size gap (BUG-03), confidence factor explanation (BUG-04), plus 3 improvements (EM derivation, sample listing preview, AR-specific next steps).

#### Bug Fixes
- [x] BUG-01: Replace ASC 250-10 with ISA 530, PCAOB AS 2315, AU-C 530, ASC 450-20 in FASB/GASB YAMLs. Per-reference `body` override added to `scope_methodology.py` (line 158: `body=ref.get("body", body)`). Global orphaned reference check completed — remaining ASC 250-10 in 6 diagnostic tools is contextually valid; ASC 230-10 in bank rec is valid.
- [x] BUG-02: Add `population_value_note` field to design result — renders italic clarifying note below Population Value. Sample data explains $4,850,000 = gross AR invoice activity vs $892,000 ending balance.
- [x] BUG-03: Auto-generates sample size gap note from stratification arithmetic (42 HV + 165 remainder = 207 vs calculated 194). Custom `sample_size_note` override supported.
- [x] BUG-04: `CONFIDENCE_FACTOR_NOTES` dict (6 levels: 80%–99%) with Poisson derivation (-ln(1-α)). Renders italic note below confidence factor in Design Parameters.

#### Improvements
- [x] IMP-01: Expected Misstatement Derivation block after TM derivation — shows EM as % of TM (e.g., "20.0% of tolerable misstatement"), ISA 530.A4 reference. Custom `expected_misstatement_note` override supported. Skipped when EM = 0.
- [x] IMP-02: Section "Sample Selection Preview" — first 10 items table (Item Ref, Description, Amount, Stratum), full export note with ISA 530 defensible randomness language. `selected_items` field added to `SamplingDesignMemoInput` schema. 12 sample items in gen_sampling_design() (5 HV + 7 remainder).
- [x] IMP-03: `NEXT_STEPS_BY_POPULATION_TYPE` dict with AR/AP/INVENTORY/REVENUE templates (5 steps each). AR steps: client request, ISA 505 confirmation, assertion testing (existence/valuation/cut-off), result recording, Paciolus UEL evaluation. `population_type` field added to design result + export schema. Generic fallback for unknown types.

#### Files Modified
- `shared/authoritative_language/fasb_scope_methodology.yml` — statistical_sampling: ASC 250-10 → ISA 530 + AS 2315 + AU-C 530 + ASC 450-20 (with per-ref body overrides)
- `shared/authoritative_language/gasb_scope_methodology.yml` — statistical_sampling: GASB 62 → ISA 530 + AS 2315 + AU-C 530 + GASB 62 (with per-ref body overrides)
- `shared/scope_methodology.py` — per-reference body override: `body=ref.get("body", body)`
- `shared/export_schemas.py` — added `selected_items: list = []` and `population_type: str = ""` to SamplingDesignMemoInput
- `sampling_memo_generator.py` — complete enrichment: CONFIDENCE_FACTOR_NOTES (6 levels), NEXT_STEPS_BY_POPULATION_TYPE (4 types + generic), population_value_note, sample_size_note, EM derivation, sample preview table, _format_stratum helper
- `generate_sample_reports.py` — enriched gen_sampling_design(): population_type, population_value_note, high_value_count, remainder_sample_size, 12 selected_items. Enriched gen_sampling_evaluation(): same design context fields.
- `tests/test_sampling_memo.py` (NEW) — 58 tests: PDF generation (5), authoritative references (10), population note (2), sample size gap (3), confidence factor (4), EM derivation (4), sample preview (5), next steps (13), section numbering (5), helpers (4), guardrails (5)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (6,000 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs — all OK, sampling design 46,324 bytes (up from ~30KB), sampling evaluation 45,845 bytes

#### Review
All verification items confirmed:
- Authoritative References: ISA 530, PCAOB AS 2315, AU-C 530, ASC 450-20 — ASC 250-10 removed
- Per-reference body override: IAASB for ISA 530, PCAOB for AS 2315, AICPA for AU-C 530, FASB for ASC 450-20
- GASB variant: ISA 530, AS 2315, AU-C 530, GASB Statement No. 62
- Global orphaned reference check completed (6 remaining ASC 250-10 in diagnostic tools are contextually valid)
- Population value note present: "$4,850,000.00 represents aggregate invoice activity for FY2025..."
- Sample size gap note: "Actual sample size increased from calculated 194 to 207 (+13 items, +6.7%) due to stratification. All 42 items in the High Value stratum..."
- Confidence factor note: "3.0000 corresponds to the 3.0000 (-ln(0.05), rounded) — 95% confidence level"
- EM derivation: "$15,000.00...represents 20.0% of tolerable misstatement ($75,000.00)"
- Sample Selection Preview: 10-item table with Item Ref, Description, Amount, Stratum
- Full export note: "Full sample listing (207 items) should be exported..."
- Next Steps: 5 AR-specific steps with ISA 505 confirmation, assertion testing (existence/valuation/cut-off), Paciolus evaluation module reference
- Step 5 references TM of $75,000.00 and ISA 530.17
- Section numbering: I Scope, II Design Parameters, III Stratification, IV Methodology, V Status, VI Sample Preview, VII Next Steps
- No other reports unintentionally modified (all 21 regenerated, timestamp-only on non-sampling)
- Test count: 6,000 backend (up from 5,942 — +58 new) + 1,329 frontend
- **Commit:** `ceaf061`

---

### Sprint 505 — Analytical Procedures Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix gross profit margin calculation (BUG-01), add results summary with risk score (BUG-02), surface sign change account names (BUG-03), surface dormant account names with balances (BUG-04), plus 5 improvements (expanded ratios, suggested procedures, cash contextualization, lead sheet legend, new/closed account detail).

#### Bug Fixes
- [x] BUG-01: Fix GPM — use account_type + all_movements (full TB population) not significant_movements subset. Added `_REVENUE_EXCLUSIONS` to prevent "Deferred Revenue" from matching revenue. Revenue: $5.8M/$6.85M → GPM 58.6%/57.8% (was 33.3%/32.0%)
- [x] BUG-02: Add Results Summary (Section III) with `compute_apc_risk_score()` (8 weighted components, max 100), `_RISK_CONCLUSIONS` (4 tiers), `RISK_TIER_DISPLAY` and `RISK_SCALE_LEGEND` from shared memo_base. Auto-computes from data when composite not pre-provided.
- [x] BUG-03: Add Sign Change Detail subsection in Section IV with account names, prior/current balances, nature of change (Debit→Credit/Credit→Debit), suggested procedure from follow_up_procedures
- [x] BUG-04: Add Dormant Account Detail subsection in Section IV with prior balances, $0 current balance, "Confirm: closed?" status, suggested procedure. Backward-compatible with legacy string-only dormant lists.

#### Improvements
- [x] IMP-01: Expand Ratio Trends to 6 ratios (GPM, COGS%, Salary%, Marketing%, Revenue Growth, Cash%Assets) with Flag column. COGS flagged "Margin compression", Marketing flagged "Material increase". Narrative paragraph covers margin compression, marketing intensity, and cash increase.
- [x] IMP-02: Suggested procedures on material movements — `_MOVEMENT_PROCEDURES` dict keyed by (account_type, direction), maps to `FOLLOW_UP_PROCEDURES` entries. 9 new APC procedures added to follow_up_procedures.py.
- [x] IMP-03: Cash increase contextualization — italic cross-reference to Cash Flow Statement for any cash movement >50%
- [x] IMP-04: Lead Sheet legend text ("Letters correspond to the cross-reference index...") + % Change column (7 columns: Lead, Sheet Name, Accounts, Prior Total, Current Total, Net Change, % Change)
- [x] IMP-05: New Account Detail (4 items with current balance + account type) and Closed Account Detail (2 items with prior balance + account type). Combined suggested procedure text.

#### Files Modified
- `multi_period_memo_generator.py` — complete rewrite: 8-section structure (Scope, Movement Summary, Results Summary, Significant Account Movements, Lead Sheet Summary, Methodology, Authoritative References, Conclusion), `compute_apc_risk_score()` (8 components), `_RISK_CONCLUSIONS` (4 tiers), `_REVENUE_EXCLUSIONS`, `_MARKETING_KEYWORDS`, `_CASH_KEYWORDS`, `_ASSET_KEYWORDS`, `_MOVEMENT_PROCEDURES`, `_ACCOUNT_TYPE_KEYWORDS`, 9 builder functions, account_type-aware ratio computation
- `generate_sample_reports.py` — enriched gen_multi_period(): 14 all_movements (3 revenue, 1 COGS, 2 expenses, 5 assets, 2 liabilities, 1 sign_change), pre-computed risk score (68.0 HIGH), 3 dormant accounts with prior balances, 4 new accounts with current balances + types, 2 closed accounts with prior balances + types
- `shared/follow_up_procedures.py` — added 9 new APC procedures (apc_revenue_increase, apc_cogs_increase, apc_asset_increase, apc_cash_increase, apc_liability_decrease, apc_expense_increase, apc_sign_change, apc_dormant_account, apc_closed_account)
- `tests/test_multi_period_memo.py` — 51 new tests (75 total, up from 24): risk scoring (12), risk conclusions (5), results summary (3), ratio trends (6), sign change detail (3), dormant account detail (5), new/closed account detail (6), suggested procedures (6), lead sheet summary (2), conclusion tiers (5), guardrails (5)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (5,942 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs — all OK, multi-period 47,618 bytes (up from ~30KB)

#### Review
All 52 verification checks confirmed in PDF output:
- GPM: 58.6% (FY2024) / 57.8% (FY2025) — not 33.3%/32.0% (FIXED)
- Proxy caveat note removed (ratios now from full TB population)
- Results Summary: Score 68.0/100, Risk Tier HIGH RISK, Risk Scale legend
- Sign Change Detail: "Deferred Revenue — Project Alpha", -$85,000 → $42,000, "Credit to Debit"
- Dormant Account Detail: 3 accounts with prior balances ($28,500, $12,200, $3,850)
- 6 ratios: GPM, COGS%, Salary%, Marketing%, Revenue Growth, Cash%Assets
- COGS +0.8pp flagged "Margin compression"
- Marketing +0.8pp flagged "Material increase"
- Narrative: COGS outpaced revenue, marketing intensity, cash reference
- 5 suggested procedures: revenue, COGS, cash, salary/expense, asset
- Cash cross-reference: "Cross-reference to Cash Flow Statement"
- Lead Sheet: 7-column table with % Change, cross-reference legend
- New Accounts: 4 items (Cloud Infrastructure, API Subscriptions, Deferred Rev, Intangibles)
- Closed Accounts: 2 items (Legacy Software, Lease Obligation)
- Section numbering: I-VII (Scope, Movement Summary, Results Summary, Significant Movements, Lead Sheet, Auth References, Conclusion)
- Risk tier HIGH consistent between Results Summary and Conclusion
- No other reports modified (all 21 regenerated, timestamp-only on non-APC)
- Test count: 5,942 backend (up from 5,891 — +51 new) + 1,329 frontend
- **Commit:** `03e26c2`

---

### Sprint 504 — Three-Way Match Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix risk tier label (BUG-01), add results summary with risk score (BUG-02), add methodology section (BUG-03), add key findings with suggested procedures (BUG-04), plus 5 improvements (vendor columns, net variance direction, match rate benchmark, unmatched detail tables, source file extension).

#### Bug Fixes
- [x] BUG-01: Map engine "MEDIUM" risk tier to standard "MODERATE" — `_ENGINE_TIER_MAPPING` dict maps low→low, medium→moderate, high→elevated, critical→high. Conclusion text uses 4-tier scale (LOW/MODERATE/ELEVATED/HIGH). No "MEDIUM" in any rendered text.
- [x] BUG-02: Add Results Summary (Section IV) with Composite Risk Score, Risk Tier, severity counts, Risk Scale legend — uses `RISK_TIER_DISPLAY` and `RISK_SCALE_LEGEND` from shared memo_base. New `compute_twm_risk_score()` function with 8 weighted components (max 89 practical, capped at 100).
- [x] BUG-03: Add Section II Methodology table with all 6 tests — `_TEST_DESCRIPTIONS` dict with structural/statistical/advanced descriptions, no banned assertive language
- [x] BUG-04: Add Key Findings (Section VI) — 4 findings with suggested procedures from `follow_up_procedures.py` (twm_net_overbilling, twm_full_match_rate, twm_unmatched_invoice, twm_date_gap)

#### Improvements
- [x] IMPROVEMENT-01: Variance table now 8 columns: Vendor, PO Number, Invoice Number, Field, PO Value, Invoice Value, Variance, Severity — sorted by variance desc (HIGH first)
- [x] IMPROVEMENT-02: Net Variance Direction block — PO-Authorized Total, Invoice Total, Net Overbilling/Underbilling with direction label derived from signed value
- [x] IMPROVEMENT-03: Match rate benchmark — "85–95% (best practice)" with 4-tier assessment (≥90% no concern, 85-90% monitor, 80-85% investigate, <80% systemic review)
- [x] IMPROVEMENT-04: 3 unmatched document detail tables — Invoices (HIGHEST RISK, 5 items), POs (9 items), Receipts (3 items) with vendor/date/amount and advisory text per table
- [x] IMPROVEMENT-05: Source file extension fixed — `meridian_procurement_fy2025.csv`

#### Files Modified
- `three_way_match_memo_generator.py` — complete rewrite: 9-section structure (Scope, Methodology, Match Results, Results Summary, Material Variances, Key Findings, Unmatched Documents, Authoritative References, Conclusion), `_ENGINE_TIER_MAPPING`, `_TEST_DESCRIPTIONS` (6 tests), `compute_twm_risk_score()`, `_MATCH_RATE_THRESHOLDS`, `_RISK_CONCLUSIONS` (4 tiers), 7 section builder functions
- `generate_sample_reports.py` — enriched gen_three_way_match(): vendor/po_number/invoice_number on all 7 variances, 6 test_results, composite_score (66.0 HIGH), 4 top_findings, 9 enriched unmatched POs, 5 enriched unmatched invoices, 3 enriched unmatched receipts, source filename with .csv extension
- `shared/follow_up_procedures.py` — added 6 new TWM procedures (twm_full_match_rate, twm_unmatched_receipt, twm_date_gap, twm_duplicate_invoice, twm_quantity_variance, twm_net_overbilling)
- `tests/test_twm_memo.py` — 45 new tests: PDF generation (4), methodology (3), match results (2), results summary (2), risk tier mapping (5), risk scoring (6), key findings (5), material variances (4), unmatched documents (6), conclusion (5), guardrails (3)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (5,891 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs — all OK, TWM 49,183 bytes (up from ~30KB)

#### Review
All verification items confirmed:
- Risk tier shows MODERATE (not MEDIUM) — `_ENGINE_TIER_MAPPING["medium"] == "moderate"`
- No "MEDIUM" in any conclusion text (guardrail test confirms)
- Results Summary present: Score 66.0/100, Risk Tier HIGH RISK, 18 high/38 medium/6 low flags, Risk Scale legend
- Section II Methodology with 6 tests (Three-Way Full Match, Amount Variance, Date Variance, Unmatched Documents, Duplicate Invoice Numbers, Quantity Variance)
- Key Findings: 4 findings all with suggested procedures
- Variance table: 8 columns with vendor names and document numbers, sorted by variance desc
- Net overbilling: $1,842,000 PO vs $1,865,450 Invoice = $23,450 overbilling
- Match rate benchmark: 75.6% flagged as "Below 80% threshold — systemic review"
- Unmatched Invoices: 5 rows with vendor/date/amount
- Unmatched POs: 9 rows with vendor/date/amount
- Unmatched Receipts: 3 rows with vendor/date/amount
- Source file: meridian_procurement_fy2025.csv (with extension)
- No banned assertive language in descriptions
- No other reports modified (all 21 regenerated, timestamp-only on non-TWM)
- Test count: 5,891 backend (up from 5,846 — +45 new) + 1,329 frontend
- **Commit:** `30a79de`

---

### Sprint 503 — Bank Reconciliation Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix missing methodology section (BUG-01), missing risk score/results summary (BUG-02), implement 5 additional tests in memo (BUG-03), add key findings section (BUG-04), plus 3 content improvements (aging tables, ending balance reconciliation, reconciling difference characterization).

#### Bug Fixes
- [x] BUG-01: Add Section II Methodology table with all 8 tests documented — 8 test descriptions in `_TEST_DESCRIPTIONS` dict, methodology table uses shared `build_methodology_section` pattern
- [x] BUG-02: Add Results Summary (Section V) with Composite Risk Score, Risk Tier, severity counts, Risk Scale legend — uses `RISK_TIER_DISPLAY` and `RISK_SCALE_LEGEND` from shared memo_base
- [x] BUG-03: Wire 5 engine tests into memo — engine already had tests, added `rec_tests` + `test_results` + `composite_score` to sample data, expanded NSF keywords (INSUFFICIENT, R01, R02, REVERSED), fixed interbank tolerance to $1.00, added per-item severity, added `compute_bank_rec_risk_score()`, fixed high-value to use `>=`
- [x] BUG-04: Add Key Findings (Section VI) — Finding 1: reconciling difference with dollar amounts and AR cross-reference, Finding 2: outstanding items volume, dynamic findings for each test with flagged items > 0, all with suggested procedures from `follow_up_procedures.py`

#### Improvements
- [x] IMPROVEMENT-01: Outstanding Items Aging Tables (Section IV) — deposits and checks sorted by days outstanding desc, priority flags (HIGH/MEDIUM/LOW), max 20 rows with overflow message, aging summary block (deposits >10/>30 days, checks >30/>90 days with percentages)
- [x] IMPROVEMENT-02: Ending Balance Reconciliation in Section III — bank balance adjusted for outstanding items, GL balance from engagement context, variance check with reconciled/not-reconciled indicator, graceful fallback when either balance is missing
- [x] IMPROVEMENT-03: Reconciling Difference Characterization in Section III — amount, direction, % of activity, potential explanations checklist (GL omission, bank error, timing difference, fraud), conditional AR cross-reference note

#### Files Modified
- `bank_reconciliation.py` — severity field on RecFlaggedItem, expanded NSF regex (+5 keywords), interbank tolerance $0.01→$1.00, per-item severity for stale deposits (HIGH >30d, MEDIUM 11-30d), NSF always HIGH, interbank always HIGH, high-value uses `>=`, new `compute_bank_rec_risk_score()` function
- `bank_reconciliation_memo_generator.py` — complete rewrite: 8-section structure (Scope, Methodology, Reconciliation Results, Outstanding Items, Results Summary, Key Findings, Authoritative References, Conclusion), `_TEST_DESCRIPTIONS` dict, `_build_methodology_table`, `_build_reconciliation_results` (with ending balance + characterization), `_build_outstanding_aging_tables`, `_build_key_findings`, 4 risk tier conclusion texts
- `generate_sample_reports.py` — enriched gen_bank_rec() with 18 outstanding deposits, 12 outstanding checks (all with dates/amounts/descriptions), 8 test_results, 5 rec_tests with flagged_items, composite_score (33.0 ELEVATED), aging_summary, ending_balance_reconciliation ($1,251,750 bank / $1,245,000 GL), ar_cross_reference ($8,450)
- `shared/follow_up_procedures.py` — expanded from 4 to 13 bank reconciliation procedures (exact_match, bank_only_items, ledger_only_items, stale_deposits, stale_checks, nsf_items, interbank_transfers, high_value_transactions, reconciling_difference, outstanding_volume + enhanced existing 4)
- `tests/test_bank_rec_memo.py` — 58 tests (up from 22): enriched report, methodology (3), results summary (3), risk conclusions (4), key findings (5), aging tables (5), ending balance (5), characterization (3), guardrails (5), engine risk score (4), flagged item severity (5)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (5,846 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs — all OK, bank rec 51,346 bytes (up from ~30KB)

#### Review
All verification items confirmed:
- Section II Methodology present with all 8 tests documented (Exact Match, Bank-Only, Ledger-Only, Stale Deposits, Stale Checks, NSF, Interbank, High Value)
- Section V Results Summary: Composite Risk Score 33.0/100, Risk Tier ELEVATED, Risk Scale legend present, severity counts (4 high, 37 medium, 3 low)
- Section VI Key Findings: Finding 1 ($6,750 reconciling difference, HIGH), Finding 2 (30 outstanding items, MEDIUM), Finding 3 (Stale Deposits, HIGH), Finding 4 (Stale Checks, MEDIUM) — all with suggested procedures
- AR cross-reference: $8,450 unreconciled AR subledger difference (Ref: ARA-2026-0306-494) rendered in both Key Findings and Characterization
- Outstanding Deposits aging table: 18 items with dates, days outstanding, priority flags, sorted by age desc
- Outstanding Checks aging table: 12 items with dates, days outstanding, priority flags (3 HIGH >90 days)
- Aging summary block: deposits >10 days (11, $19,520, 42.7%), >30 days (4, $4,600); checks >90 days (3, $5,770, 14.8%)
- Ending balance reconciliation: bank $1,251,750 - $45,670 deposits + $38,920 checks = adjusted, GL $1,245,000
- Reconciling difference characterization: $6,750, Bank > GL, 0.14% of activity, 4 potential explanations checklist
- Risk tier ELEVATED consistent between Results Summary (33.0) and Conclusion
- Footer: "bank reconciliation analysis testing procedures"
- 8 methodology descriptions all substantive (>20 chars each)
- NSF keywords expanded: INSUFFICIENT, R01, R02, REVERSED now detected
- High-value test uses >= (not >) for materiality threshold
- Interbank tolerance: $1.00 (was $0.01)
- Stale deposit per-item severity: HIGH >30 days, MEDIUM 11-30 days
- No other reports unintentionally modified (all 21 regenerated, timestamp-only changes on non-bank-rec reports)
- Test count: 5,846 backend (up from 5,808 — +38 net) + 1,329 frontend
- **Commit:** `f74c771`

---

### Sprint 502 — Fixed Asset Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix PP&E ampersand rendering (BUG-01), blank methodology descriptions (BUG-02), missing high severity detail (BUG-03), orphaned ASC 842 reference (BUG-04), and 4 content improvements to the Fixed Asset Register Analysis memo.

#### Bug Fixes
- [x] BUG-01: Fix PP&E ampersand rendering — escaped `&` as `&amp;` in fixed_asset_testing_memo_generator.py (6 occurrences) and currency_memo_generator.py (2 occurrences: PP&E + "Methodology & Limitations")
- [x] BUG-02: Fix blank methodology descriptions — root cause was sample data test_keys not matching engine canonical keys (`cost_outliers` → `cost_zscore_outliers`, `residual_anomalies` → `residual_value_anomalies`). Enhanced both descriptions.
- [x] BUG-03: Add Section V High Severity Asset Detail with 3 per-test table builders (over_depreciation sorted by excess desc, duplicate_assets with pair grouping + capitalization total, negative_values with "Data entry error" likely cause)
- [x] BUG-04: Add FA-10 lease indicator test (Option A) — keyword scan for lease/ROU/right-of-use/leasehold in asset descriptions; ASC 842 reference now justified

#### Improvements
- [x] IMPROVEMENT-01: Fixed Asset Roll-Forward with gross cost + accumulated depreciation sections, TB reconciliation, variance flagging
- [x] IMPROVEMENT-02: Depreciation Rate Analysis — effective rate, implied average useful life, prior period comparison with pp change flag
- [x] IMPROVEMENT-03: Fully depreciated finding enriched with aggregate original cost $187,500 and NBV $0
- [x] IMPROVEMENT-04: Asset Register Composition table by category (5 categories in sample data) with count, gross cost, accum depr, NBV, avg age

#### Files Modified
- `fixed_asset_testing_memo_generator.py` — complete rewrite: custom scope builder, 3 detail table builders, roll-forward, depr rate, category summary, finding formatter, 10 test descriptions
- `fixed_asset_testing_engine.py` — FA-10 lease indicator test (keyword regex), battery updated to 10 tests
- `generate_sample_reports.py` — fixed 2 test_keys, added flagged_entries for 3 HIGH tests, roll-forward data, category summary, fully-depreciated aggregate cost
- `currency_memo_generator.py` — PP&E ampersand + "Methodology & Limitations" ampersand fix
- `shared/follow_up_procedures.py` — added lease_indicators procedure
- `tests/test_fixed_asset_testing_memo.py` — 26 new tests (58 total, up from 32)
- `tests/test_fixed_asset_testing.py` — updated 4 assertions from 9→10 tests

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (5,808 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs

#### Review
All verification items confirmed:
- PP&E renders without semicolon (XML-escaped `&amp;` in all 6 risk_assessment occurrences + 2 currency memo occurrences)
- Cost Z-Score Outliers has substantive methodology description (z-score + threshold + overstatement language)
- Residual Value Anomalies has substantive methodology description (salvage value + ISA 540 + 30% threshold)
- Section V present with 3 detail tables: Depreciation Exceeds Cost (2 items, sorted by excess desc), Duplicate Assets (2 items with pair grouping), Negative Cost (1 item)
- Duplicate Assets table shows "Dell Latitude 5540" with $1,250.00 cost and capitalization total
- Negative Cost table shows -$15,400.00 with "Data entry error" likely cause
- ASC 842 justified by FA-10 lease indicator test (keyword scan, 0 flagged in sample = clean result)
- Roll-forward present: $3,420,000 gross cost, $1,180,000 accum depr, $420,000 additions, $285,000 depr expense, ✓ reconciles
- Depreciation rate: 8.3% effective, 12 year implied life
- Finding 2 includes "$187,500.00 (net book value: $0)" aggregate cost
- Category table: 5 categories (Building Improvements, Equipment, IT Equipment, Furniture, Vehicles)
- Risk tier MODERATE consistent (21.5 score)
- Lease indicator: 10th test, 0 flagged, "No lease indicator keywords detected"
- Test count: 5,808 backend (up from 5,788 — 20 new) + 1,329 frontend
- **Commit:** `b4b2984` — pushed to main

---

### Sprint 501 — Revenue Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix methodology table empty descriptions (BUG-01), missing suggested procedures (BUG-02), missing dollar amounts in findings (BUG-03), and 4 content improvements to the Revenue Recognition Testing memo.

#### Bug Fixes
- [x] BUG-01: Fix empty test descriptions — root cause was sample data test_keys not matching engine canonical keys (e.g., `round_amounts` → `round_revenue_amounts`, `cut_off_risk` → `cutoff_risk`). Fixed 8 test_keys + enhanced all 16 descriptions.
- [x] BUG-02: Add suggested procedures for all key findings — added `recognition_before_satisfaction` + 3 contract-test entries to follow_up_procedures.py, enhanced 7 existing revenue entries
- [x] BUG-03: Add aggregate dollar amounts inline in key finding text ($647,500 cutoff, $567,000 recognition, $2,192,000 December, $2,603,000 concentration)

#### Improvements
- [x] IMPROVEMENT-01: Section V High Severity Entry Detail with 4 per-test table builders (cutoff sorted by date desc, recognition timing, sign anomalies, concentration risk) + preparer concentration
- [x] IMPROVEMENT-02: Benford pass note with MAD conformity + SSP Allocation pass note (post-results)
- [x] IMPROVEMENT-03: Revenue Quality Indicators block in Scope (total revenue, high-risk %, December concentration, cut-off window, single-customer concentration)
- [x] IMPROVEMENT-04: Contra-Revenue Ratio with 3-tier interpretation (<2% normal, 2-5% inquiry, >5% elevated)

#### Files Modified
- `shared/follow_up_procedures.py` — enhanced 7 revenue procedures, added 4 new contract test entries
- `revenue_testing_memo_generator.py` — custom scope builder, 4 detail table builders, post-results notes, contra-revenue ratio
- `generate_sample_reports.py` — fixed 8 test_keys, added flagged_entries for 4 HIGH tests, total_revenue/contra enrichment, dollar amounts in findings, Benford MAD description
- `tests/test_revenue_testing_memo.py` — 12 new tests (40 total, up from 28)

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (5,788 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs

#### Review
All verification items confirmed:
- All 16 tests in methodology table have non-empty descriptions
- 8 previously blank tests (Round Amounts, Z-Score, Trend Variance, Cut-Off, Recognition, Obligation Linkage, Modification, SSP) now show descriptions
- All 4 findings have suggested procedures (cutoff: ASC 606-10-25-23; recognition: ASC 606-10-25; year-end: seasonal inquiry; concentration: ASC 275-10)
- All 4 findings include aggregate dollar amounts
- Section V present with 4 tables: Cut-Off Risk (7 rows, sorted date desc), Recognition Timing (4 rows), Sign Anomalies (2 rows), Concentration Risk (1 row)
- Benford note with MAD=0.0038 present below results table
- SSP Allocation pass note present below results table
- Revenue Quality Indicators block in Section I with 5 metrics
- Contra-revenue ratio: $89,050 / $6,850,000 = 1.3% (within normal range)
- Risk tier MODERATE consistent between Results Summary and Conclusion
- No other reports unintentionally modified (all 21 regenerated, timestamp-only changes on non-revenue reports)
- Commit: 71a6821

---

### Sprint 500 — Payroll Report Fixes & Improvements
**Status:** COMPLETE
**Goal:** Fix risk tier mismatch (BUG-01), add high severity detail tables (BUG-02), and 5 content improvements to the Payroll & Employee Testing memo.

#### Bug Fixes
- [x] BUG-01: Fix risk_tier across all 7 sample reports to match score_to_risk_tier scale
- [x] BUG-02: Add Section V High Severity Employee Detail with per-test tables

#### Improvements
- [x] IMPROVEMENT-01: Payroll Register-to-GL Reconciliation in scope
- [x] IMPROVEMENT-02: Headcount Roll-Forward (if hire/term dates available)
- [x] IMPROVEMENT-03: Benford pass positive interpretation note
- [x] IMPROVEMENT-04: Departmental Salary Summary table
- [x] IMPROVEMENT-05: EMP-4421 overpayment quantification in finding text

#### Files Modified
- `generate_sample_reports.py` — risk_tiers, flagged_entries, enriched payroll data
- `payroll_testing_memo_generator.py` — custom scope, extra sections, finding formatter
- `shared/memo_template.py` — add build_post_results callback
- `payroll_testing_engine.py` — hire_date detection, register total, department summary, headcount

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (5,776 passed, 1 skipped, 1 pre-existing error)
- [x] Regenerate all 21 sample PDFs

#### Review
All verification items confirmed in PDF output:
- Risk Tier "ELEVATED" matches 28.3 score (scale: 26-50 = Elevated)
- 6 other reports corrected from "elevated" to "moderate" (scores 15.2-24.7)
- Section V with 4 detail tables: Duplicate IDs, Pay After Termination, Ghost Employee, Duplicate Bank
- Pay After Termination table shows $8,400 total overpayment
- Ghost Employee table shows ✓ for all 3 indicators on EMP-3187
- GL reconciliation: $1,387,450 register vs $1,420,000 GL with $32,550 variance
- Headcount roll-forward: 112 → 118 with 1 variance
- Department summary: 6 departments, no concentration >40%
- Benford note: MAD=0.0042, positive conformity interpretation
- EMP-4421 finding text includes $8,400 total amount
- Commit: 0529356

---

### Sprint 499 — Toolbar Refactor: Three-Zone Model
**Status:** COMPLETE
**Goal:** Refactor authenticated app top navbar to professional SaaS three-zone layout (Identity | Primary Nav | User/System).

#### Changes
- [x] Zone 1 (Left): Logo only — removed "Paciolus" text label
- [x] Zone 2 (Center): Horizontally centered nav with icon+label items (Dashboard, Tools, Workspaces, Portfolio, History) — 5 items, under max 7
- [x] Zone 2 active state: bold label + bottom border indicator in sage accent
- [x] Zone 3 (Right): Icon-only search, settings, and avatar with tooltips — no labels
- [x] MegaDropdown repositioned to center under toolbar (fixed positioning)
- [x] ProfileDropdown trigger: icon-only avatar circle, light-theme, tooltip
- [x] Mobile drawer updated with Navigation section (icons + labels)
- [x] Background preserved: toolbar-marble bg-oatmeal-100/95 backdrop-blur-lg unchanged
- [x] No routing, auth, or functionality changes

#### Verification
- [x] `npm run build` — passes
- [x] `npm test` — 1,329 tests pass (111 suites), including all 12 ProfileDropdown tests

---

### Sprint 447 — Stripe Production Cutover

**Status:** PENDING (CEO action required)
**Goal:** Complete Stripe Dashboard configuration and cut over to live mode.
**Context:** Sprint 440 E2E smoke test passed (27/27). All billing code is production-ready.

#### Stripe Dashboard Configuration
- [ ] Confirm `STRIPE_SEAT_PRICE_MONTHLY` is graduated pricing: Tier 1 (qty 1–7) = $80, Tier 2 (qty 8–22) = $70
- [ ] Enable Customer Portal: payment method updates, invoice viewing, cancellation at period end
- [ ] Verify "Manage Billing" button opens portal from `/settings/billing`
- [ ] CEO signs `tasks/pricing-launch-readiness.md` → mark as GO

#### Production Cutover
- [ ] Create production Stripe products/prices/coupons (`sk_live_` key)
- [ ] Set production env vars + deploy with `alembic upgrade head`
- [ ] Smoke test with real card on lowest tier (Solo monthly)
- [ ] Monitor webhook delivery in Stripe Dashboard for 24h

---

### Pending Legal Sign-Off

- [ ] **Terms of Service v2.0** — legal owner sign-off with new effective date
- [ ] **Privacy Policy v2.0** — legal owner sign-off with new effective date

---

### Sprint 463 — SIEM / Log Aggregation Integration
**Status:** PENDING (CEO decision required)
**Criteria:** CC4.2 / C1.3

Options: A: Grafana Loki, B: Elastic Stack, C: Datadog, D: Defer (use existing Prometheus/Sentry)

---

### Sprint 464 — Cross-Region Database Replication
**Status:** PENDING (CEO decision required)
**Criteria:** S3.2 / BCP

Options: read replica vs. cross-region standby vs. pgBackRest to secondary region

---

### Sprint 466 — Secrets Vault Secondary Backup
**Status:** PENDING (CEO decision required)
**Criteria:** CC7.3 / BCP

Options: AWS Secrets Manager (separate account), encrypted offline store, secondary cloud provider

---

### Sprint 467 — External Penetration Test Engagement
**Status:** PENDING (CEO decision required)
**Criteria:** S1.1 / CC4.3

Scope: auth flows, CSRF/CSP, rate limiting, API authorization, file upload, JWT, billing. Target: Q2 2026.

---

### Sprint 468 — Bug Bounty Program Launch
**Status:** PARTIAL (security.txt + VDP deployed; CEO decision pending on program model)
**Criteria:** CC4.3 / VDP

- [x] `frontend/public/.well-known/security.txt` (RFC 9116)
- [x] VDP doc updated (v1.0→v1.1)
- [ ] CEO decision: public bounty (HackerOne/Bugcrowd) vs. private invite-only vs. enhanced VDP
