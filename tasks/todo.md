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

### Sprint 532 — Framer-Motion Type Safety Sweep + CI Threshold Hardening

**Status:** COMPLETE
**Goal:** Fix all 6 actionable findings from DEC 2026-03-11 evening session.
**Complexity Score:** 2/10

#### F-001: Add `as const` to 31 framer-motion variant objects across 17 files
- [x] ProfileDropdown.tsx — `dropdownVariants`
- [x] DownloadReportButton.tsx — `buttonVariants`, `spinnerVariants`, `textVariants`
- [x] FinancialStatementsPreview.tsx — `spinnerVariants`
- [x] FeaturePillars.tsx — `cardHoverVariants`
- [x] ProcessTimeline.tsx — `iconVariants`, `numberVariants`
- [x] ToolSlideshow.tsx — `slideVariants`
- [x] ClientCard.tsx — `buttonVariants`
- [x] AnomalyCard.tsx — `cardVariants`
- [x] RiskDashboard.tsx — `containerVariants`
- [x] SensitivityToolbar.tsx — `containerVariants`, `editModeVariants`, `displayModeVariants`
- [x] PdfExtractionPreview.tsx — `overlayVariants`, `modalVariants`
- [x] WorkbookInspector.tsx — `overlayVariants`, `modalVariants`, `listItemVariants`
- [x] pricing/page.tsx — `containerVariants`, `cardVariants`, `fadeUp`
- [x] trust/page.tsx — `containerVariants`, `fadeUp`, `scaleIn`, `lineGrow`, `vertLineGrow`
- [x] portfolio/page.tsx — `buttonVariants`
- [x] history/page.tsx — `pageVariants`
- [x] HeritageTimeline.tsx — `containerVariants`
- [x] UnifiedToolbar.tsx — already compliant (verified)

#### F-002: Update test counts in CLAUDE.md + MEMORY.md
- [x] CLAUDE.md: 6,188 → 6,507 backend, 1,345 → 1,339 frontend
- [x] MEMORY.md: 6,223 → 6,507 backend, 1,345 → 1,339 frontend

#### F-003: Sync ceo-actions.md
- [x] Update sync date from 2026-02-27 to 2026-03-11

#### F-004: Raise CI coverage thresholds
- [x] pytest: `--cov-fail-under=60` → `--cov-fail-under=80`
- [x] Jest: `coverageThreshold` 25% → 35%

#### F-006: Fix PytestCollectionWarning
- [x] Add `__test__ = False` to `TestingMemoConfig` class

#### Verification
- [x] `npm run build` passes (42 routes, all dynamic)
- [x] `npm test` — 1,339 passed
- [x] `pytest` — 6,507 passed (0 failures)
- [x] PytestCollectionWarning for TestingMemoConfig — suppressed

**Review:** 31 `as const` additions across 17 frontend files, CI coverage gates raised (pytest 60→80%, Jest 25→35%), PytestCollectionWarning suppressed, test counts synchronized, CEO actions sync date updated. Zero regressions.
**Commit:** f37a8c5

---

### Sprint 533 — CI Parity + Lint Baseline + Accessibility Polish

**Status:** COMPLETE
**Goal:** Fix all 3 actionable findings from DEC 2026-03-15.
**Complexity Score:** 2/10

#### F-001: Add `--cov-fail-under=80` to PostgreSQL CI job
- [x] `.github/workflows/ci.yml` line 171 — append `--cov-fail-under=80` to pytest command

#### F-002: Recapture lint baseline date
- [x] `.github/lint-baseline.json` — update `"updated"` field from `2026-02-23` to `2026-03-15`

#### F-003: Add `aria-label` to icon-only interactive elements (7 instances)
- [x] `AdjustmentEntryForm.tsx` — remove line button: `aria-label="Remove line"`
- [x] `FileQueueItem.tsx` — delete file button: `aria-label` matching title
- [x] `ProfileDropdown.tsx` — avatar button: `aria-label="User menu"`
- [x] `ToolLinkToast.tsx` — dismiss button: `aria-label="Dismiss notification"`
- [x] `UnifiedToolbar.tsx` — search button: `aria-label="Open command palette"`
- [x] `UnifiedToolbar.tsx` — settings link: `aria-label="Settings"`
- [x] `UnifiedToolbar.tsx` — sign in link: `aria-label="Sign in"`

#### Verification
- [x] `npm run build` passes (all routes dynamic)
- [x] `npm test` — 1,339 passed (112 suites)

**Review:** PostgreSQL CI coverage threshold aligned with SQLite (80%), lint baseline date refreshed, 7 icon-only buttons/links now have `aria-label` for screen reader accessibility. Zero regressions.

---

### Sprint 534 — Multi-Period Comparison: 8-Bug Fix Batch

**Status:** COMPLETE
**Goal:** Fix 8 bugs identified in multi-period comparison test session.
**Complexity Score:** 5/10

#### Bug 1: Unicode escape rendering in summary header
- [x] Replace literal `\u00B7` in JSX text content with actual `·` character (page.tsx line 366)

#### Bug 2: CSV parsing incompleteness / hard account limit
- [x] Root cause: `lead_sheet_grouping.summaries` only contains abnormal/flagged accounts, not all parsed accounts
- [x] Add `all_accounts` field to single-sheet audit result (`audit_engine.py`)
- [x] Add `all_accounts` field to multi-sheet audit result (`audit_engine.py`)
- [x] Update `extractAccounts` in `useMultiPeriodComparison.ts` to prefer `all_accounts`
- [x] Update `AuditResultForComparison` type to include `all_accounts`
- [x] Remove hard 100-account display limit in `AccountMovementTable.tsx`

#### Bug 3: "Closed Account" false positives
- [x] Confirmed: downstream symptom of Bug 2 — now resolved. Accounts present with zero balance have `current_acct != None`, so they are not classified as CLOSED.
- [x] Classification logic already correct: `is_closed = current_acct is None` (absent from file, not zero balance)

#### Bug 4: Suggested procedures template mismatch (rotation bug)
- [x] Expand `_MOVEMENT_PROCEDURES` dict from 6 to 24 entries covering all (category, direction) combos
- [x] Add 6 new procedure texts to `FOLLOW_UP_PROCEDURES` (revenue_decrease, cogs_decrease, asset_decrease, cash_decrease, liability_increase, expense_decrease)
- [x] Fix direction logic: credit-nature accounts (revenue, liability) — negative change = economic increase
- [x] Handle new_account, closed_account, sign_change movement types explicitly

#### Bug 5: Ratio calculations (GPM=100%, COGS%=0%)
- [x] Root cause: `is_cogs = acct_type == "cogs" if acct_type else ...` short-circuits when acct_type is any non-empty string (e.g., "expense")
- [x] Fix: use `acct_type == "cogs" or _match_keyword(name, _COGS_KEYWORDS)` (OR instead of exclusive fallback)
- [x] Same fix for `is_revenue`: OR-based check

#### Bug 6: Lead sheet accordion expand throws frontend error
- [x] Root cause: `ThreeWayLeadSheetSummary` missing `movements` field — `.map()` on undefined
- [x] Add `movements: list[dict]` to `ThreeWayLeadSheetSummary` dataclass + `to_dict()`
- [x] Pass enriched movements through in `compare_three_periods` lead sheet loop
- [x] Add `movements` to `ThreeWayLeadSheetSummaryResponse` schema
- [x] Add null guard `(ls.movements ?? [])` in `CategoryMovementSection.tsx`

#### Bug 7: Blank engagement metadata in downloaded PDF
- [x] Add Client Name, Fiscal Year End, Engagement Practitioner, Engagement Reviewer inputs to config screen
- [x] Pass metadata values to `/export/multi-period-memo` endpoint body
- [x] Default to "Not specified" for blank fields

#### Bug 8: Upload UX blocks concurrent zone interaction
- [x] Replace shared `isProcessing` blocking with per-zone disabled logic
- [x] Each zone disabled only during its own loading or during comparison — not blocked by other zones
- [x] Compare button remains gated on all required zones being ready

#### Verification
- [x] `npm run build` passes (all routes dynamic)
- [x] `npm test` — 1,339 passed (112 suites)
- [x] `pytest tests/test_multi_period_comparison.py` — 65 passed
- [x] `pytest tests/test_multi_period_memo.py` — 75 passed

**Review:** 8 bugs fixed across 9 files (3 backend engine/route, 2 backend shared modules, 4 frontend components/hooks). Key root causes: (1) account extraction from audit result only included abnormal accounts, not full TB; (2) sign convention not respected in procedure/ratio logic; (3) 3-way comparison dropped movements from lead sheet summaries. Zero regressions.

---

