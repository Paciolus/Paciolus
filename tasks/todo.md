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
> Sprints 517–531 archived to `tasks/archive/sprints-517-531-details.md`.
> Sprints 532–536 archived to `tasks/archive/sprints-532-536-details.md`.

### Sprint 539 — Comprehensive Remediation (Security, Correctness, Architecture)

**Status:** COMPLETE
**Goal:** Fix critical security, billing correctness, auth concurrency, webhook idempotency, and architectural quality issues identified by 3 independent audits.

#### Section 1 — Authorization & Billing Correctness
- [x] 1.1: Refactor `check_seat_limit()` to accept org context, not caller identity
- [x] 1.2: `handle_subscription_deleted()` downgrades ALL org members to FREE
- [x] 1.3: Implement `is_authorized_for_client()` helper for org-aware access
- [x] 1.4: Backfill `org.subscription_id` on checkout for org-first lifecycle

#### Section 2 — Authentication
- [x] 2.1: Replace read-then-write in `rotate_refresh_token()` with CAS guard

#### Section 3 — Webhook Idempotency
- [x] 3.1: Atomic deduplication — insert dedup marker before business logic
- [x] 3.2: Stale event ordering guard — reject out-of-order subscription events

#### Section 4 — Data Integrity
- [x] 4.1: DPA timestamp normalization — `.astimezone(UTC)` for offset-aware inputs

#### Section 5 — Architectural Refactoring
- [x] 5.1: Split `apiClient.ts` into transport/authMiddleware/cachePlugin/downloadAdapter
- [x] 5.8: Split `engagements.py` into CRUD/analytics/exports + tool_taxonomy config
- [x] 5.10: Audit back-compat shims in `export.py` — added removal plan (Sprint 545)

#### Section 6 — Test Coverage
- [x] 15 new tests: seat enforcement, cancellation entitlement, refresh race, webhook dedup, event ordering, DPA timestamps, org-first lifecycle, shared access

#### Verification
- [x] `pytest` passes (6,522 tests — 15 new)
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)

#### Review
- 6 critical/high security bugs fixed across auth, billing, webhooks
- Org member collaborative access implemented across 4 managers
- apiClient.ts split from 1,141-line monolith into 5 composable modules
- engagements.py decomposed into 3 focused route files + centralized tool taxonomy
- Zero regressions in existing 6,507 + 1,339 test suites

---

### Sprint 538 — DEC 2026-03-16 Remediation

**Status:** COMPLETE
**Goal:** Fix 2 P2 + 7 P3 findings from Digital Excellence Council audit.

#### P2 Fixes
- [x] F-001: Reorder `classify_round_number_tier()` — informational check before 10%-TB escalation
- [x] F-002: Cap informational risk score contribution at 5 points

#### P3 Fixes
- [x] F-003: Narrow bare `"cash"` keyword in TIER2_INFORMATIONAL (5 specific variants)
- [x] F-004: Add 'informational' to severity filter dropdowns (FlaggedEntriesTable, FollowUpItemsTable)
- [x] F-005: Contra-equity detection in multi-period credit-normal sign flip
- [x] F-006: Replace "potential adjusting entry" language with neutral wording (4 occurrences)
- [x] F-007: Add related-party loan variants to ROUND_NUMBER_TIER1_CARVEOUTS (5 entries)
- [x] F-009: Benford MAD digit filter `>` → `>=`
- [x] F-014: Add `__test__ = False` to TestTier enum

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)
- [x] `pytest` passes (6,507 tests)
- [x] QA: Cash at >10% TB total returns "informational" (not "material")
- [x] QA: 20 informational findings produce max 5 risk score points

#### Review
- 9 findings fixed across 8 files (2 P2, 7 P3)
- F-001: Moved informational keyword check to Step 5e, before 10%-TB escalation (Step 5f)
- F-002: `min(informational_count, 5)` with "(capped)" label when cap applies
- F-003: Replaced bare "cash" with 5 specific variants: cash and cash equivalents, operating cash, petty cash, cash on hand, cash in bank
- F-005: Added `is_contra_account()` check in `_is_credit_normal` property — contra-equity excluded from sign flip
- F-006: Removed "potential adjusting entry" from 4 procedure texts; replaced with "further investigation/evaluation"
- F-007: Added 5 related-party loan keywords to carve-outs (shareholder/officer/employee/director/related party)
- Lessons captured in `tasks/lessons.md`
- Commit: c47cd28

---

### Sprint 540 — Report QA Bug Fixes (Meridian FY2025)

**Status:** COMPLETE
**Goal:** Fix 12 confirmed bugs across 8 report generators identified during QA review of Meridian Capital Group FY2025 sample output.

#### Priority 1 — Critical: Proof Summary Metrics
- [x] 1a: Bank rec proof summary shows 0%/0% — add `data_quality` and `column_detection` keys to bank rec result dict
- [x] 1b: Data Completeness/Column Confidence hardcoded 94%/92% — parameterize `_make_testing_result()`, pass distinct per-tool values

#### Priority 2 — High: Calculation and Reference Errors
- [x] 2a: Benford digit 9 deviation off by 10x — fix sample data from -0.0004 to -0.00406; add regression test
- [x] 2b: Bank rec AR aging cross-ref mismatch — share reference via `_SHARED_REFS` between gen_ar_aging and gen_bank_rec
- [x] 2c: ASC 240-10 incorrect in JE testing — replace with ASC 850-10 (Related Party Disclosures) in YAML

#### Priority 3 — Medium: Data Consistency
- [x] 3a: Financial statements cover page missing client/period — pass `entity_name` as `client_name` in `FSReportMetadata`
- [x] 3b: Payroll headcount non-agreement — add variance footnote in roll-forward + reconciliation note in department summary
- [x] 3c: AR aging missing test descriptions — add 5 alternate test_key aliases to `AR_AGING_TEST_DESCRIPTIONS`

#### Priority 4 — Low: Presentation and UX
- [x] 4a: Revenue cut-off negative amounts — apply `abs()` in `_build_cutoff_table`
- [x] 4b: Inventory risk score vs test pass rate — add interpretive note via `_build_risk_score_note` post-results callback
- [x] 4c: IFRS citations on US GAAP engagement — replace IAS 16 → ASC 360-10, IAS 2 → ASC 330-10 in methodology intros
- [x] 4d: Financial statement notes placeholder — replace inline italic with bordered callout box

#### Verification
- [x] `pytest` (401 affected tests pass)
- [x] `npm run build` passes
- [x] Benford regression test (28 tests pass)
- [x] All 21 sample reports regenerated successfully

#### Review
- 8 files modified: `generate_sample_reports.py`, `fasb_scope_methodology.yml`, `pdf_generator.py`, `payroll_testing_memo_generator.py`, `ar_aging_memo_generator.py`, `revenue_testing_memo_generator.py`, `inventory_testing_memo_generator.py`, `fixed_asset_testing_memo_generator.py`
- 1 test file modified: `test_benford.py` (+1 regression test)

---

### Sprint 537 — Informational Note Tier

**Status:** COMPLETE
**Goal:** Add third severity level (Informational Note) for low-signal findings that require no procedure.

#### Backend
- [x] Add `ROUND_NUMBER_TIER2_INFORMATIONAL` list to `classification_rules.py`
- [x] Update `classify_round_number_tier()` to return `"informational"` for matching accounts
- [x] Handle `tier == "informational"` in `detect_rounding_anomalies()` (severity, text template)
- [x] Add `informational_count` to `_build_risk_summary()` and risk_summary dict
- [x] Update `compute_tb_risk_score()` for informational (+1 each, grouped summary line)
- [x] Update PDF generator: four-column risk table, third section for informational notes
- [x] Change classification_validator number_gap severity to `"informational"`
- [x] Add DEPLOY-VERIFY-537 log line
- [x] Fix stale test assertion in `test_contra_and_detection_fixes.py` (contra-asset → minor, not suppressed)

#### Frontend
- [x] Add `'informational'` to Severity type in `types/shared.ts`
- [x] Add `informational_count` to RiskSummary in `types/mapping.ts`
- [x] Update `DisplayMode` to include `'all'` in SensitivityToolbar
- [x] Three-section split in RiskDashboard (High / Medium / Notes)
- [x] Informational card variant in AnomalyCard (grey border, collapsed, no procedure)
- [x] Pass displayMode to RiskDashboard for filtering
- [x] Add informational severity color to ClassificationQualitySection
- [x] Add `informational` to all `Record<Severity, ...>` across 7 files

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)
- [x] `pytest` passes (6,507 tests)
- [x] Cascade QA: 3 informational (Cash, AR Trade, AP Trade), Accrued Bonuses stays Minor
- [x] Meridian QA: 1 informational (Rent — Office), 2520 suppressed, CV-4 gaps informational

#### Review
- Fixed false positive: "rent" substring matched "current" in "2520 — Current Portion — Long Term Debt". Added "current portion" and "long term debt" to TIER1_SUPPRESS.
- Fixed stale test: `test_allowance_round_suppressed` was already failing pre-537 (Sprint 536 changed contra-asset from suppress to minor).
- Lessons captured in `tasks/lessons.md`.
- Commit: c394549

---

### Sprint 541 — Report QA Round 2: Fiscal Year End on Testing Memos

**Status:** COMPLETE
**Goal:** Fix fiscal_year_end rendering as "—" on all testing memo cover pages, and confirm proof summary metrics are dynamically computed.

#### Fix 1 — Fiscal Year End on Testing Memo Cover Pages
- [x] Add `fiscal_year_end: Optional[str] = None` to `WorkpaperMetadata` schema
- [x] Add `fiscal_year_end` to `common_kwargs` in `_memo_export_handler`
- [x] Add `fiscal_year_end` param to `generate_testing_memo()` and pass to `ReportMetadata`
- [x] Update 7 standard testing generators (JE, AP, Payroll, Revenue, AR Aging, Fixed Asset, Inventory)
- [x] Update 2 custom generators (Bank Rec, Three-Way Match) — signature + `ReportMetadata` wiring
- [x] Update 8 remaining generators (Multi-Period, Currency, Sampling ×2, Preflight, PopProfile, Expense, Accrual, Flux) to prevent `**common_kwargs` crash

#### Fix 2 — Proof Summary Metrics (Dynamic Computation)
- [x] Confirmed: `completeness_score` computed dynamically per-file by `shared/data_quality.py`
- [x] Confirmed: `overall_confidence` computed dynamically per-file by `column_detector.py`
- [x] Confirmed: `build_proof_summary_section()` extracts from result dict — no hardcoded values
- [x] No code change needed — metrics are already dynamic

#### Verification
- [x] All 18 generator function signatures verified via `inspect.signature()`
- [x] `pytest -k memo` passes (867 tests, 0 failures)
- [x] Proof summary tests pass (8/8)

#### Review
- 18 files modified across export schema, route handler, shared template, and all memo generators
- Root cause: `generate_testing_memo()` never received `fiscal_year_end` — only financial statements builder did
- Proof metrics (Fix 2) were already correct — dynamic computation via `data_quality.py` and `column_detector.py`

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

