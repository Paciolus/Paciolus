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

### Era 15: Report Enrichment — Sprints 499–515
> Toolbar three-zone refactor, 16 report enrichments (Payroll, Revenue, Fixed Assets, Bank Rec, Three-Way Match, Analytical Procedures, Sampling Design, Sampling Evaluation, Multi-Currency, Data Quality Pre-Flight, Population Profile, Expense Category, Accrual Completeness, Flux Expectations, Anomaly Summary), test suite fixes (SQLite FK teardown, perf budget skip removal), ~300 new backend tests. **Tests: 6,188 + 1,345.**

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
- [ ] Verify Active Phase has fewer than 5 completed sprints (archive if threshold exceeded)

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

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

> Sprints 478–497 archived to `tasks/archive/sprints-478-497-details.md`.
> Sprints 499–515 archived to `tasks/archive/sprints-499-515-details.md`.
> Sprints 516–526 archived to `tasks/archive/sprints-516-526-details.md`.

### Sprint 527 — DEC 2026-03-10 P2 Remediation (6 findings)

**Status:** COMPLETE
**Goal:** Remediate 6 P2 findings from the Digital Excellence Council audit dated 2026-03-10.

#### F-001: Detection Keywords Hardcoded in StreamingAuditor
- [x] Added `RELATED_PARTY_KEYWORDS`, `INTERCOMPANY_KEYWORDS`, `EQUITY_RETAINED_EARNINGS_KEYWORDS`, `EQUITY_DIVIDEND_KEYWORDS`, `EQUITY_TREASURY_KEYWORDS` to `classification_rules.py` using `(keyword, weight, is_phrase)` 3-tuple format
- [x] Imported and used in `audit_engine.py` — removed class-level `_RELATED_PARTY_KEYWORDS` and `_INTERCOMPANY_KEYWORDS`
- [x] Updated `detect_equity_signals()` to use imported keyword lists instead of inline string checks
- [x] 44 anomaly tests pass

#### F-002: Concentration Benchmark Thresholds Inconsistent
- [x] Added `REVENUE_CONCENTRATION_THRESHOLD` (0.30) and `EXPENSE_CONCENTRATION_THRESHOLD` (0.40) to `classification_rules.py`
- [x] `audit_engine.py` `detect_revenue_concentration()` and `detect_expense_concentration()` use imported thresholds
- [x] `tb_diagnostic_constants.py` `CONCENTRATION_BENCHMARKS` uses f-strings referencing the imported constants
- [x] 134 diagnostic tests pass

#### F-003: `_standard_table_style()` Still Duplicated
- [x] Added `standard_table_style()` to `shared/memo_base.py` using `ledger_table_style()` as base
- [x] Replaced local `_standard_table_style()` in `accrual_completeness_memo.py`, `expense_category_memo.py`, `population_profile_memo.py` with aliases to shared function
- [x] 44 expense category memo tests pass

#### F-004: Wide Type Intersection Cast — Missing `AuditResultResponse`
- [x] Added `AuditResultResponse` interface to `types/diagnostic.ts` extending `AuditResult`
- [x] Replaced inline cast in `useTrialBalanceUpload.ts` line 201 with named type
- [x] Removed unused `ColumnDetectionInfo` import
- [x] `npm run build` passes

#### F-005: No Unit Tests for uploadTransport.ts
- [x] Created `frontend/src/__tests__/uploadTransport.test.ts` with 10 tests
- [x] Tests: successful upload, 401, 403 EMAIL_NOT_VERIFIED, 403 generic, 500, network failure, header injection, null token, null CSRF, 403 JSON parse failure
- [x] 10/10 tests pass

#### F-006: Post-Processor Missing Defensive Checks
- [x] `apply_lead_sheet_grouping()`: added `logger.warning()` to existing early return
- [x] `apply_currency_conversion()`: added defensive `if "accounts" not in result` check with `logger.warning()`
- [x] 134 diagnostic tests pass

#### Verification
- [x] `pytest tests/test_audit_anomalies.py` — 44 passed
- [x] `pytest tests/test_expense_category_memo.py` — 44 passed
- [x] `pytest tests/ -k "post_processor or diagnostic"` — 134 passed
- [x] `npm run build` passes
- [x] `npx jest --testPathPatterns uploadTransport --no-coverage` — 10 passed

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

---

### Sprint 517 — Memo Generator Test Coverage (DEC F-018)

**Status:** COMPLETE
**Goal:** Add dedicated test files for the 5 memo generators that lack deep coverage.
**Context:** DEC 2026-03-08 finding F-018. 13 other memo generators have dedicated tests; these 5 were enriched in Sprints 489–500 but tests were not expanded. `engagement_dashboard_memo.py` has zero test coverage.

- [x] `tests/test_ap_testing_memo.py` — 24 tests (risk tiers, 13 test descriptions, drill-down tables, DPO metric, guardrails)
- [x] `tests/test_je_testing_memo.py` — 27 tests (risk tiers, 9 test descriptions, Benford's Law, high-severity detail, guardrails)
- [x] `tests/test_payroll_testing_memo.py` — 34 tests (risk tiers, 11 test descriptions, GL reconciliation, headcount roll-forward, Benford, department summary, guardrails)
- [x] `tests/test_preflight_memo.py` — 29 tests (score breakdown, TB balance check, column detection, data quality, FASB/GASB framework, guardrails)
- [x] `tests/test_engagement_dashboard_memo.py` — 23 tests (risk tiers, report summary, cross-report risk threads, priority actions, edge cases, guardrails)
- [x] `pytest` passes — 137 tests across 5 files
- [x] Pattern: follows `test_bank_rec_memo.py` / `test_sampling_memo.py` structure

---

### Sprint 518 — OpenAPI Schema Drift Detection (DEC F-020)

**Status:** COMPLETE
**Goal:** Add a CI job that detects schema drift between backend OpenAPI spec and committed snapshot.
**Context:** DEC 2026-03-08 finding F-020 (P3, systemic). 34 commits changed backend schemas and frontend types independently with no automated sync verification.

- [x] Create `scripts/generate_openapi_snapshot.py` — extracts OpenAPI spec from FastAPI app
- [x] Create `scripts/check_openapi_drift.py` — compares live spec against committed snapshot
- [x] Generate initial snapshot (`scripts/openapi-snapshot.json` — 309 schemas, 159 paths)
- [x] Add `openapi-drift-check` CI job to `.github/workflows/ci.yml`
- [x] Drift detection tested locally — detects added/removed/changed fields, type changes, required/optional changes
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)

**Review:** Snapshot-based approach (Option A) chosen over key-schema checks — more comprehensive and simpler to maintain. The drift check script imports the FastAPI app, generates the live OpenAPI spec, and compares it field-by-field against a committed JSON snapshot. Reports added/removed/changed paths, schemas, fields, type changes, and required/optional transitions. CI job runs independently (no DB needed) with ~15s execution time. Developers run `generate_openapi_snapshot.py` when intentionally changing schemas.

---

### Sprint 527 — DEC 2026-03-10 Remediation (6 P2 Findings)

**Status:** COMPLETE
**Goal:** Fix all 6 P2 findings from Digital Excellence Council audit 2026-03-10.
**Context:** DEC identified 15 findings (6 P2, 7 P3, 2 info). This sprint addresses the P2s.

#### F-001: Centralize Detection Keywords in classification_rules.py
- [x] Added 5 keyword lists to `classification_rules.py`: `RELATED_PARTY_KEYWORDS` (11), `INTERCOMPANY_KEYWORDS` (6), `EQUITY_RETAINED_EARNINGS_KEYWORDS` (2), `EQUITY_DIVIDEND_KEYWORDS` (1), `EQUITY_TREASURY_KEYWORDS` (1)
- [x] Removed hardcoded class attributes from `StreamingAuditor`
- [x] Updated 3 detection methods to import from `classification_rules`

#### F-002: Concentration Benchmark Threshold Consistency
- [x] Added `REVENUE_CONCENTRATION_THRESHOLD` and `EXPENSE_CONCENTRATION_THRESHOLD` to `classification_rules.py`
- [x] Replaced hardcoded 0.30/0.40 in `audit_engine.py` with imported constants
- [x] Updated `CONCENTRATION_BENCHMARKS` in `tb_diagnostic_constants.py` to use f-strings

#### F-003: Extract `_standard_table_style()` to shared/memo_base.py
- [x] Added `standard_table_style()` to `shared/memo_base.py` built on `ledger_table_style()`
- [x] Replaced local definitions in `accrual_completeness_memo.py`, `expense_category_memo.py`, `population_profile_memo.py`

#### F-004: Create `AuditResultResponse` Type
- [x] Added `AuditResultResponse` interface to `frontend/src/types/diagnostic.ts`
- [x] Replaced inline type intersection cast in `useTrialBalanceUpload.ts`

#### F-005: Add uploadTransport.ts Unit Tests
- [x] Created `frontend/src/__tests__/uploadTransport.test.ts` — 10 tests
- [x] Covers: success, 401, 403, EMAIL_NOT_VERIFIED, 500, network failure, header injection

#### F-006: Post-Processor Defensive Checks
- [x] Added `logger.warning()` + early-return guards to both post-processor functions
- [x] `apply_currency_conversion()` now checks for `"accounts"` key before any work

#### Verification
- [x] `pytest` — 249 affected tests pass (anomalies 44 + memos 44 + diagnostics 134 + sanitizer 27)
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests, 112 suites)
- [x] `uploadTransport` tests pass (10 tests)

**Review:** All 6 P2 findings fixed. F-001 moved 21 keyword entries from 3 hardcoded locations to canonical `classification_rules.py` in standard 3-tuple format. F-002 unified 2 threshold sources. F-003 eliminated ~70 lines of duplication from 3 diagnostic memos. F-004 replaced an unsafe inline type cast with a named `AuditResultResponse` type. F-005 added 10 unit tests for the shared upload transport layer. F-006 added defensive guards preventing `KeyError` in post-processors.

---

### Sprint 528 — Expand CSV Account Type Synonym Map

**Status:** COMPLETE
**Goal:** Expand `_CSV_TYPE_MAP` to recognize compound/qualified account type values (e.g., "Current Asset", "Cost of Goods Sold", "Non-Operating Expense") and add suffix fallback for unlisted variants.

- [x] Expand `_CSV_TYPE_MAP` from 10 entries to 56 entries (compound values for all 5 categories)
- [x] Add `_CSV_TYPE_SUFFIXES` list for suffix-based fallback matching
- [x] Add `_resolve_csv_type()` helper returning `(category, confidence)` — direct=1.0, suffix=0.90
- [x] Update `_resolve_category()` to use `_resolve_csv_type()`
- [x] Update `get_abnormal_balances()` confidence logic to use `_resolve_csv_type()` instead of bare `has_csv_type` check
- [x] Tests pass — 44 anomaly tests + 77 CSV type resolution tests (121 total)
- [x] Created `tests/test_csv_type_resolution.py` — 77 tests (48 direct, 13 suffix, 7 miss, 6 e2e category, 2 e2e confidence, 1 whitespace)
- [x] `npm run build` passes

**Review:** Expanded `_CSV_TYPE_MAP` from 10 bare-word entries to 56 compound-aware entries covering all 5 categories. Added `_CSV_TYPE_SUFFIXES` for suffix-based fallback at 0.90 confidence. Extracted `_resolve_csv_type()` helper to centralize CSV-to-category resolution with tiered confidence. Fixed a latent bug in `get_abnormal_balances()` where `has_csv_type` was True (key existed in `provided_account_types`) but the value didn't match the map — causing confidence=1.0 to be assigned even though the heuristic was used.

---

### Sprint 529 — CSV Account Type Data Flow Fix

**Status:** COMPLETE
**Goal:** Fix the data path disconnect where CSV-provided account types were detected at intake but never reached downstream classification consumers.

#### Root Cause Analysis
Two bugs on separate data paths:

1. **Primary (line 1738-1741):** `audit_trial_balance_streaming()` built `account_classifications` by calling `auditor.classifier.classify()` directly — bypassing `_resolve_category()` and all CSV-provided types. This heuristic-only dict was then passed to every downstream consumer: classification validator, population profile, expense category, accrual completeness, lease diagnostic, cutoff risk. This is why every account displayed as Unknown despite the CSV having valid types.

2. **Secondary (lines 406-438):** The user-provided column mapping path in `_discover_columns()` returned early without setting `self.account_type_col` or `self.account_name_col`. With user mappings, `process_chunk()` never extracted CSV type values because the column reference was None.

#### Fixes Applied
- [x] **Bug 1:** Replace manual `classifier.classify()` loop with `auditor.get_classified_accounts()` which routes through `_resolve_category()` — CSV types now flow to all 6 downstream consumers
- [x] **Bug 2:** User-mapping path now calls `detect_columns()` for supplementary column detection (account_type, account_name) before returning
- [x] **Step 4:** Added `csv_type_trace` log line in `_resolve_csv_type()` — logs first 5 raw values per analysis for deploy verification

#### Verification
- [x] `pytest` — 6,440 passed (full suite, 0 failures)
- [x] `npm run build` passes
- [x] Existing 77 CSV type resolution tests still pass
- [x] All 566 downstream consumer tests pass (diagnostic + classification + lead_sheet + population + expense_category + accrual)
