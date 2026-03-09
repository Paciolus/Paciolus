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
> Pending items below.

### Sprint 524 — PDF Report Quality: Remaining Fixes (A/B/C)

**Status:** COMPLETE
**Commit:** 051e2f4
**Goal:** Complete three incomplete implementations from Sprint 522's institutional-grade PDF improvements.

#### Fix A: Risk Score Decomposition — Plain-Language Named Factors
- [x] Add `_describe_material_factor()` helper for plain-language labels from anomaly data
- [x] Rewrite `compute_tb_risk_score()` to accept `abnormal_balances` kwarg
- [x] Material findings listed individually by account name (not "3 × 8" aggregate)
- [x] Minor observations use clean count ("5 findings"), no multiplier notation
- [x] Coverage factors use "exceeds" instead of "≥" symbol
- [x] Total line added below decomposition with ledger rule separator

#### Fix B: Differentiated Minor Observation Procedures
- [x] Split `round_dollar` into `round_dollar_single` (one-time) and `round_dollar_repeated` (pattern)
- [x] Add `credit_balance_ar` for AR-specific credit balance language (unapplied payments, credit memos)
- [x] Dispatch logic inspects `transaction_count`, issue text ("occurrences"/"multiple"), and account name
- [x] Five sample findings (TB-I001 through TB-I005) each produce individually tailored procedures

#### Fix C: Inline Amount Qualifier — Per-Transaction Breakdown
- [x] Amount annotation shows "(8 transactions × $5,000.00)" instead of "(sum of 8 flagged txns)"
- [x] Computes `per_transaction_amount` from `amount / transaction_count` when not explicitly provided
- [x] Added `transaction_count` and `per_transaction_amount` fields to sample data
- [x] Single-occurrence rounding anomalies show no qualifier (clean amount)

#### Verification
- [x] 152 report tests pass (0 regressions)
- [x] Diagnostic sample PDF generated (49,968 bytes) — all three fixes verified in output

---

### Sprint 523 — Cover Page Liability Framing

**Status:** COMPLETE
**Commit:** b59b89d
**Goal:** Remove implied co-preparer liability from cover page CPA credential fields.

- [x] Part 1: Rename "Prepared By" → "Engagement Practitioner", "Reviewed By" → "Engagement Reviewer", "Status" → "Report Status"
- [x] Part 2: Add "Generated by Paciolus® Diagnostic Intelligence. Engagement information entered by user." separator below metadata
- [x] Part 3: Add practitioner liability boundary paragraph to Limitations section (both diagnostic and memo reports)
- [x] Part 4: Audit footer — confirmed "Prepared using" (not "Prepared by") — no change needed
- [x] 142 report tests pass
- [x] 21 sample reports regenerated

---

### Sprint 522 — PDF Report Quality: Institutional Grade

**Status:** COMPLETE
**Commit:** 158a0a1
**Goal:** Audit and improve PDF report generation to institutional-grade standard (12 fixes).

#### Priority 1: Accuracy Fixes
- [x] Fix 1: Minor Observations total — sum signed values, not absolute values; add signed-balance footnote
- [x] Fix 2: Population Composition — rename "Total Balance" to "Gross Balance"; add footnote clarifying non-additive sum

#### Priority 2: Intelligence & Analytical Depth
- [x] Fix 3: Priority ranking — sort findings by amount descending; add P1/P2/P3 rank column
- [x] Fix 4: Risk score decomposition — show factor-level score contributions beneath composite score
- [x] Fix 9: Suggested procedures — differentiate language by amount magnitude, account type, and exception nature

#### Priority 3: Presentation & Professional Format
- [x] Fix 5: Table of Contents — add TOC page after cover with section names and page numbers
- [x] Fix 6: Engagement context fields — add Fiscal Year End, Prepared By, Reviewed By, Report Status to cover metadata
- [x] Fix 7: Interior page design — gold section dividers, row banding on data tables, increased section header spacing
- [x] Fix 8: Trial Balance Status — formal status badge with label + detail replacing casual checkmark

#### Priority 4: Disclosure & Integrity
- [x] Fix 10: Upgrade disclaimer — full Limitations section on final page + upgraded footer language
- [x] Fix 11: Amount column clarity — annotate pattern-based findings with what the amount represents
- [x] Fix 12: Data Quality / Scope section — add Data Intake Summary between cover and Executive Summary

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (515 memo tests + 123 report tests + 46 diagnostic tests — all green)
- [x] Generate test report and verify all 12 fixes render correctly (48,808 byte PDF generated)

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

### Sprint 521 — Directive Protocol Enforcement + Audit 29 Recovery

**Status:** COMPLETE
**Commit:** 83d2313
**Goal:** Make the Directive Protocol mechanically enforced (not discipline-dependent) and complete retroactive documentation for Sprints 516 and 520.

- [x] Add `commit-msg` hook (`frontend/.husky/commit-msg`) — rejects `Sprint N:` commits unless `tasks/todo.md` is staged
- [x] Verified hook rejects Sprint commits without todo.md staged (exit code 1)
- [x] Verified hook allows hotfix commits through (exit code 0)
- [x] Add retroactive Sprint 516 entry to `tasks/todo.md` (DEC remediation, 17 findings, commit 20396fd)
- [x] Add retroactive Sprint 520 entry to `tasks/todo.md` (billing security, 4 findings, commit 7391f56)
- [x] Capture Sprint 520 security lessons in `tasks/lessons.md` (4 patterns: tenant isolation, Stripe line items, webhook idempotency, event enum semantics)
- [x] Capture protocol bypass lesson in `tasks/lessons.md` (urgency does not waive documentation)
- [x] Update CLAUDE.md Directive Protocol step 5 with hook enforcement reference
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] Update MEMORY.md with hook enforcement note + test count (6,223)

**Review:** Audit 29 identified that 50% of sprints (516, 520) bypassed the Directive Protocol — including the most critical security fix in the project's history (CRITICAL cross-tenant data leakage). Root cause: urgency bias with no mechanical enforcement. Fix: a commit-msg hook that makes the protocol a hard gate. The hook is the backstop; the lesson and CLAUDE.md update address the behavioral pattern.

---

### Sprint 516 — DEC 2026-03-08 Remediation

**Status:** COMPLETE
**Commit:** 20396fd
**Goal:** Fix 17 of 21 findings from Digital Excellence Council audit 2026-03-08.
**Context:** DEC audit identified 21 findings (8 P2, 12 P3, 1 info). 4 findings deferred to Sprints 517-518.

- [x] 17 findings remediated (methodology corrections, test fixes, content additions)
- [x] 4 findings deferred with explicit Sprint assignments (F-018 → Sprint 517, F-020 → Sprint 518)
- [x] `pytest` passes
- [x] `npm run build` passes
- [x] `npm test` passes

**Review:** Retroactive entry per Audit 29 (protocol bypass identified). All 17 fixes verified via full test suite. Remaining 4 findings have dedicated sprint plans in READY status.

---

### Sprint 520 — Billing Security & Correctness

**Status:** COMPLETE
**Commit:** 7391f56
**Goal:** Fix 4 billing audit findings spanning CRITICAL to MEDIUM severity.

#### Findings Fixed
- [x] **CRITICAL:** Cross-tenant data leakage in billing analytics — scoped all 5 metric queries + weekly review by user_id/org_id; added `_resolve_scoped_user_ids()` for org member resolution
- [x] **HIGH:** Seat mutation targets wrong Stripe line item — `_find_seat_addon_item()` using price ID match; falls back to `items[0]` only for single-item subscriptions
- [x] **MEDIUM:** Webhook replay gap — `ProcessedWebhookEvent` model with stripe_event_id PK; duplicate deliveries return 200 with no side effects
- [x] **MEDIUM:** Semantic event mismatch — added `TRIAL_ENDING` enum variant; `TRIAL_EXPIRED` reserved for actual expiration

#### Verification
- [x] `pytest` — 6,223 passed, 0 regressions
- [x] 10 new tests: 3 tenant isolation, 2 dual-line-item seat targeting, 1 webhook dedup, 2 semantic event, 2 enum updates
- [x] `npm run build` passes
- [x] `npm test` passes (1,345 tests)

**Review:** Retroactive entry per Audit 29 (protocol bypass identified). Most critical finding was cross-tenant data leakage — billing analytics queries were unscoped, allowing any verified user to see global metrics. Fixed by scoping all queries to user_id with org_id expansion via `_resolve_scoped_user_ids()`. Lessons captured in `lessons.md`.

---

### Sprint 519 — Structural Debt Remediation (Code Quality)

**Status:** COMPLETE (all 5 phases implemented)
**Commit:** 39fdc30 (Phases 1–4), 6f9ffd9 (Phase 5)
**Goal:** Reduce structural debt and consolidation drift across 5 phases without changing observable behavior.

#### Phase 1 — Quick Wins ✓
- [x] 1A: Frontend upload transport consolidation (`uploadTransport.ts`) — 4 files deduped
- [x] 1B: API client mutation cache invalidation dedup (`invalidateRelatedCaches`)
- [x] 1C: Backend billing endpoint boilerplate (`stripe_endpoint_guard`) — 5 endpoints
- [x] 1D: Backend audit route execution scaffold (`execute_file_tool`) — 4 endpoints
- [x] Tests pass after Phase 1

#### Phase 2 — Hook Decomposition ✓
- [x] Extract `useTrialBalanceUpload`, `useTrialBalancePreflight`, `useTrialBalanceExports`, `useTrialBalanceBenchmarks`
- [x] `useTrialBalanceAudit` reduced from 680→110 LOC (thin composite)
- [x] Tests pass after Phase 2

#### Phase 3 — Backend Engine Unification ✓
- [x] Create `engine_framework.py` with `AuditEngineBase` (10-step pipeline)
- [x] `JETestingEngine`, `APTestingEngine`, `PayrollTestingEngine` extend base
- [x] All 6,215 backend tests pass (3 pre-existing failures unrelated)

#### Phase 4 — Settings Page Decomposition ✓
- [x] Extract `MaterialitySection`, `ExportPreferencesSection`, `testingConfigFields`
- [x] Page reduced from 635→415 LOC
- [x] Build + tests pass after Phase 4

#### Phase 5 — Route/Service Boundary ✓ (CEO override)

**Council deliberation (2026-03-09):** Critic + Guardian recommended deferral (low ROI on stable files). **CEO overrode** — "I also want architectural purity."

Extracted:
- [x] `billing/checkout_orchestrator.py` — checkout business logic with domain exceptions (Validation/Provider/Unavailable → 400/502/503)
- [x] `billing/usage_service.py` — UsageStats dataclass + `get_usage_stats()` helper
- [x] `shared/materiality_resolver.py` — `resolve_materiality()` from private `_resolve_materiality` in audit.py
- [x] `shared/tb_post_processor.py` — `apply_lead_sheet_grouping()` + `apply_currency_conversion()`
- [x] `routes/billing.py` updated — create_checkout + get_usage delegate to services (515 → 515 LOC, cleaner)
- [x] `routes/audit.py` updated — removed `_resolve_materiality`, inline grouping/currency (691 → 623 LOC)
- [x] `tests/test_materiality_cascade.py` updated — imports from shared module
- [x] All 5,299 backend tests pass (1 pre-existing YAML coverage failure unrelated)

---

### Sprint 525 — TB Diagnostics Page: Bug Fixes and Content Improvements

**Status:** COMPLETE
**Goal:** Resolve 1 interaction bug and 5 content/logic issues on the Trial Balance Diagnostics upload and data readiness page.

#### Fix 1: Button Click Hijacking (CRITICAL)
- [x] File input pointer-events disabled when preflight/results are showing
- [x] Export PDF, Export CSV, and Proceed buttons all function correctly

#### Fix 2: Null/Empty Cell Handling — One-Sided TB (CRITICAL)
- [x] Coerce null/empty debit/credit to 0 before balance check (`_coerce_to_float` helper)
- [x] Distinguish structural nulls (one-sided) from true nulls (both empty)
- [x] Remove false HIGH severity flags for one-sided null patterns

#### Fix 3: Materiality Slider — Dynamic Range
- [x] Calculate recommended materiality from TB population (0.5% of total)
- [x] Dynamic slider range (max = 2% of TB population, static $500K default before file load)
- [x] Show recommended value indicator on slider

#### Fix 4: Column Detection — Fuzzy Matching and Full Column Display
- [x] Add 14 new account column synonyms (account_code, acct, gl_code, acct_no, etc.) → ≥95% confidence
- [x] Display all file columns in detection panel with inferred role labels (not just 3 core)

#### Fix 5: Engagement Metadata Entry Point
- [x] Collapsible "Engagement Details (Optional)" section with 6 fields
- [x] Fields: Entity Name, Fiscal Year End, Engagement Period, Practitioner, Reviewer, Report Status
- [x] State persists through analysis flow (available at PDF generation time)

#### Fix 6: "Indistinct" Terminology
- [x] Replaced all 7 instances across 4 files (audit_engine.py, practice_settings.py, MaterialityControl.tsx, RiskDashboard.tsx)
- [x] New language: "below materiality threshold" / "Below Materiality"

#### Verification
- [x] `npm run build` passes
- [x] `npm test` passes (1,329 tests, 111 suites)
- [x] `pytest` passes (115 tests: preflight, column detector, report chrome)

**Review:** All 6 fixes implemented. Fix 1 root cause: file input's `pointer-events` condition only checked `auditStatus` but not `showPreflight`/`preflightStatus`, so the invisible input overlay intercepted clicks on preflight action buttons. Fix 2 root cause: preflight null detection counted one-sided empties as data quality issues; now uses two-pass approach (raw null count → true null count for debit/credit). Fix 3 changes static $10K slider to dynamic range based on TB population. Fix 4 adds 14 account column synonyms and displays all file columns. Fix 5 adds collapsible engagement metadata panel. Fix 6 eliminates all "Indistinct" terminology.

---

### Sprint 517 — Memo Generator Test Coverage (DEC F-018)

**Status:** READY
**Goal:** Add dedicated test files for the 5 memo generators that lack deep coverage.
**Context:** DEC 2026-03-08 finding F-018. 13 other memo generators have dedicated tests; these 5 were enriched in Sprints 489–500 but tests were not expanded. `engagement_dashboard_memo.py` has zero test coverage.

- [ ] `tests/test_ap_testing_memo.py` — section headers, risk scoring, suggested procedures (5+ tests)
- [ ] `tests/test_je_testing_memo.py` — section headers, Benford analysis rendering, risk scoring (5+ tests)
- [ ] `tests/test_payroll_testing_memo.py` — section headers, enriched sections from Sprint 500 (5+ tests)
- [ ] `tests/test_preflight_memo.py` — section headers, data quality rendering (5+ tests)
- [ ] `tests/test_engagement_dashboard_memo.py` — PDF generation, cover page metadata, section headers (5+ tests)
- [ ] `pytest` passes for all new test files
- [ ] Pattern: follow `test_bank_rec_memo.py` or `test_sampling_memo.py` structure

---

### Sprint 518 — OpenAPI→TypeScript Drift Detection (DEC F-020)

**Status:** READY
**Goal:** Add a CI job that detects schema drift between backend OpenAPI spec and frontend TypeScript types.
**Context:** DEC 2026-03-08 finding F-020 (P3, systemic). 34 commits changed backend schemas and frontend types independently with no automated sync verification.

- [ ] Add CI job that generates OpenAPI spec from FastAPI (`/openapi.json`)
- [ ] Compare key response schemas against frontend `types/` definitions
- [ ] Fail CI on drift (or warn-only initially)
- [ ] Document the sync workflow in CLAUDE.md or a README
- [ ] Verify CI pipeline passes
