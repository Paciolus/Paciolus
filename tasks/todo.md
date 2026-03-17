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
| Marketing pages SSG | **Not feasible** — CSP nonce (`await headers()` in root layout) forces dynamic rendering; Vercel edge caching provides near-static perf | Phase XXVII |
| Test file mypy — full cleanup | 804 errors across 135 files (expanded from 68); `python_version` updated to 3.12 in Sprint 543 | Sprint 475/543 |

---

## Active Phase
> Sprints 478–497 archived to `tasks/archive/sprints-478-497-details.md`.
> Sprints 499–515 archived to `tasks/archive/sprints-499-515-details.md`.
> Sprints 516–526 archived to `tasks/archive/sprints-516-526-details.md`.
> Sprints 517–531 archived to `tasks/archive/sprints-517-531-details.md`.
> Sprints 532–536 archived to `tasks/archive/sprints-532-536-details.md`.
> Sprints 537–541 archived to `tasks/archive/sprints-537-541-details.md`.

### Sprint 543 — Dependency Bumps + Mypy Annotations

**Status:** COMPLETE
**Goal:** bcrypt 5.0 bump, test file mypy annotations, marketing SSG dropped.

- [x] 543a: Bump bcrypt>=5.0.0, add transitive-only comment for numpy/chardet
- [x] 543b: Update mypy.ini python_version 3.11→3.12 (804 errors found — full cleanup deferred)
- [x] 543c: Deferred items cleaned: Marketing SSG dropped, resolved items removed

#### Review
- bcrypt 5.0 uses stable `hashpw/checkpw/gensalt` API — zero code changes needed
- mypy test errors expanded from expected 68 to 804 across 135 files; config updated, full cleanup deferred
- Deferred items table cleaned: 5 items removed (3 being implemented, 1 resolved, 1 dropped)

---

### Sprint 544 — Backend Refactors

**Status:** COMPLETE
**Goal:** PaginatedResponse[T] generic, dedicated schemas/ directory, Alembic in Dockerfile.

- [x] 544a: Create `shared/pagination.py`, migrate 4 routes (clients, activity, engagements, follow_up_items) + 4 frontend hooks + 3 frontend types
- [x] 544b: Create `backend/schemas/` with 5 schema files extracted from routes; backward-compat re-exports preserved
- [x] 544c: Wire Alembic into Dockerfile CMD (`alembic upgrade head &&` before gunicorn)

#### Review
- **Breaking change:** List endpoint responses use `items` key instead of `clients`/`engagements`/`activities`. Frontend hooks + types + tests all updated simultaneously.
- 5 schema files: client_schemas, billing_schemas, adjustment_schemas, settings_schemas, follow_up_schemas
- All backward-compat re-exports verified: `from routes.billing import CheckoutRequest` still works
- 1 API contract test updated (`engagements` → `items`)
- Dockerfile now runs `alembic upgrade head` exactly once before workers spawn

---

### Sprint 545 — Phase LXIX Frontend Pages

**Status:** COMPLETE
**Goal:** Admin Dashboard, PDF Branding, Export Sharing pages + settings hub update.

- [x] 545a: Admin Dashboard — types/hook/page with 4 metric cards, 2 tables, CSV export, filters
- [x] 545b: Branding Settings — types/hook/page with header/footer form, logo upload/delete
- [x] 545c: Export Sharing — types/hook/modal/page with share list, revoke, expiry countdown
- [x] 545d: Settings Hub — 3 new FeatureGate-wrapped cards (Team Dashboard, PDF Branding, Export Sharing)

#### Review
- 3 new types files, 3 new hooks, 1 new modal component, 3 new pages
- 18 new hook tests (6 per hook), all passing
- All pages use Oat & Obsidian tokens, font-serif headers, Reveal wrapper
- FeatureGate with `hidden` prop hides cards for lower-tier users on settings hub
- Grid expanded to 3-col on large screens to accommodate 6 cards
- **Tests:** 1,357 frontend (was 1,339 — +18 new hook tests)
- Commit: f5e76b7

---

### Sprint 542 — Nightly Report Bug Fixes + Dependency Updates

**Status:** COMPLETE
**Goal:** Fix 5 confirmed-open bugs from the 2026-03-17 nightly report and update outdated packages (5 security-relevant + all minor/patch).

#### Bug Fixes
- [x] BUG-001: Suggested procedures rotation — add alternate procedures and `rotation_index` param to `get_follow_up_procedure()` (20 alternates across JE/AP/Revenue/Payroll; all 7 callers updated)
- [x] BUG-002: Hardcoded risk tier labels — `_compute_engagement_risk()` returns tier keys, display via `RISK_TIER_DISPLAY` lookup
- [x] BUG-003: PDF cell overflow — wrap plain strings in `Paragraph()` across 4 generators (bank rec, currency, accrual, anomaly summary)
- [x] BUG-006: Identical data quality scores — redistribute optional weight pool proportionally instead of flat bonus
- [x] BUG-007: Empty drill-down stubs — add `flagged_entries` guard to JE/AP high-severity section filters

#### Confirmed Already Fixed (No Action Needed)
- [x] BUG-004: Orphaned ASC 250-10 — fixed in Sprint 506 with test coverage
- [x] BUG-005: PP&E ampersand escaping — fixed in Sprint 502 with test coverage

#### Dependency Updates — Security-Relevant
- [x] fastapi: 0.133.1 → 0.135.1 (minor)
- [x] PyJWT: 2.11.0 → 2.12.1 (minor)
- [x] SQLAlchemy: 2.0.47 → 2.0.48 (patch)
- [x] stripe: 14.4.0 → 14.4.1 (patch, now pinned in requirements.txt)
- [x] next: 16.1.6 → 16.1.7 (patch)

#### Dependency Updates — Minor/Patch
- [x] Backend: uvicorn 0.41→0.42, sentry-sdk 2.53→2.54
- [x] Frontend: @sentry/nextjs 10.40→10.43, framer-motion 12.34→12.37, recharts 3.7→3.8, jest 30.2→30.3, lint-staged 16.2→16.4, @types/node 25.3→25.5, @typescript-eslint/* 8.56→8.57, @eslint/eslintrc 3.3.3→3.3.5

#### Verification
- [x] `pytest` passes (867 memo tests, 65 anomaly+dq tests)
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)
- [x] BUG-001 rotation verified: different indices produce different procedures
- [x] BUG-006 score differentiation verified: 100.0 vs 82.4 for different fill rates

#### Review
- 14 backend files modified across 5 bug fixes + 2 dependency files
- BUG-001 adds `FOLLOW_UP_PROCEDURES_ALT` dict with 20 alternates; backward-compatible API
- BUG-002 normalizes to lowercase tier keys consumed by existing `RISK_TIER_DISPLAY` infrastructure
- BUG-006 eliminates flat bonus that compressed score variance across datasets
- Major version packages (bcrypt 5.0, numpy 2.x, chardet 7.x) deferred — breaking API changes

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

