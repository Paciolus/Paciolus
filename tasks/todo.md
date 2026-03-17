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
- [ ] Verify Active Phase has fewer than 5 completed sprints (the commit-msg hook blocks at 5+; run `sh scripts/archive_sprints.sh` if threshold exceeded)

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
> Sprints 542–546 archived to `tasks/archive/sprints-542-546-details.md`.

### Sprint 547 — Cross-Repository Cohesion Remediation

**Status:** COMPLETE
**Goal:** Resolve 6 architectural decisions from cohesion audit: 12-tool identity, layered retention, workspace-centric navigation, tier label retirement, API reference scaffold, moderate fixes.

#### Phase 1 — Product Identity (12-tool suite)
- [x] README hero: 12-tool AI-powered audit intelligence suite
- [x] Product Vision: 5-tool → 12-tool throughout + version history
- [x] ARCHITECTURE.md: 11-tool → 12-tool, version updated
- [x] Entitlements.py: canonical tool count comment block
- [x] FastAPI app description updated
- [x] EXECUTIVE_SUMMARY_NONTECH.md: 11-tool → 12-tool
- [x] GuestCTA.tsx: comment updated to 12 tools
- [x] Terms page: pricing/tier/tool count corrected

#### Phase 2 — Retention Language (layered)
- [x] User Guide §16: canonical headline + precision copy added
- [x] User Guide §16.3: ephemeral scope clarification
- [x] User Guide FAQ: recovery answer rewritten
- [x] EXECUTIVE_SUMMARY: purged → archived (matches soft-delete implementation)

#### Phase 3 — Navigation Identity (workspace-centric)
- [x] ARCHITECTURE.md: Navigation Model section added
- [x] User Guide: "Diagnostic Workspace" → "Workspace" (2 occurrences)
- [x] ToS draft: "Diagnostic Workspace" → "Workspace" (3 occurrences)

#### Phase 4 — Tier Label Retirement
- [x] User Guide §15: Team/Organization → Professional/Enterprise + pricing corrected
- [x] User Guide FAQ: Team/Organization → Professional/Enterprise
- [x] Access Control Policy: tier table corrected
- [x] rate_limits.py: LEGACY ALIAS comments added
- [x] Terms page: Team/Organization → Professional/Enterprise

#### Phase 5 — API Reference (hybrid)
- [x] Deprecation header added to old API_REFERENCE.md
- [x] Generated skeleton: API_REFERENCE_GENERATED.md from router registry
- [x] Docstrings added to undocumented route handlers

#### Phase 6 — Remaining Fixes
- [x] ARCHITECTURE.md: tech stack versions corrected (React 19, Tailwind 4, framer-motion 12, FastAPI 0.135)
- [x] User Guide: Free tier export entitlement corrected (no exports)
- [x] Historical artifact headers: FEATURE_ROADMAP.md, EXECUTIVE_SUMMARY_NONTECH.md

#### Phase 7 — Deliverable
- [x] COHESION_REMEDIATION.md created

#### Review
- Commit: (pending)

---

### Sprint 548 — Test Suite Remediation

**Status:** COMPLETE
**Goal:** 4-phase test efficiency overhaul: CI optimization, structural dedup, coverage gaps, E2E smoke layer.

#### Phase 1 — Quick Wins
- [x] Register `slow` pytest marker in `backend/pyproject.toml`
- [x] Add `-m "not slow"` to PR CI runs, nightly job for slow tests
- [x] Deduplicate `TestRateLimitTiers` from `test_rate_limit_coverage.py` (6 tests → covered by `test_rate_limit_tiered.py`)
- [x] Raise frontend coverage thresholds with per-directory minimums (`src/hooks/`, `src/app/`)

#### Phase 2 — Structural Improvements
- [x] Extract AP fixtures to `backend/tests/helpers/ap_fixtures.py` (3 files deduped)
- [x] Create `toolPageScenarios.tsx` shared harness for frontend tool page tests
- [x] Refactor 7 tool page tests (AP, AR, JE, Payroll, Revenue, FixedAsset, Inventory) to use harness

#### Phase 3 — Coverage Gaps
- [x] `test_billing_routes.py` — 91 tests (checkout, subscription, cancel, webhook, dedup, seats, portal, usage, analytics)
- [x] `test_entitlement_checks.py` — 52 tests (all 16 check functions, soft/hard mode, seat limits)
- [x] `test_export_routes.py` — 50 tests (PDF/Excel/CSV, auth, validation, financial statements)
- [x] `useStatementBuilder.test.ts` — 56 tests (balance sheet, income statement, cash flow, mapping trace)
- [x] `BillingPage.test.tsx` — 6 tests (plan details, upgrade CTA, usage, error, loading)
- [x] `WorkspaceContext.test.tsx` — 7 tests (providers, selection state, toggles, error boundary)

#### Phase 4 — E2E Smoke Layer
- [x] Install Playwright, configure `playwright.config.ts`
- [x] Create `e2e/smoke.spec.ts` (auth, upload, export flows)
- [x] Add `e2e-smoke` job to CI (depends on backend-tests + frontend-tests, main-only)

#### Review
- Commit: 966000e
- Backend: 6,714 passed (3 pre-existing failures in pagination tests), 5 deselected (slow)
- Frontend: 1,426 passed across 118 suites, coverage thresholds met
- Build: passes

---

### Sprint 549 — Governance Remediation (Codex Review)

**Status:** IN PROGRESS
**Goal:** Resolve 8 governance documentation inconsistencies identified by control-plane audit.

#### Task 1 — Archival threshold normalization
- [x] CLAUDE.md: "4+" → "5+" to match commit-msg hook
- [x] todo.md post-sprint checklist: clarify hook enforcement language

#### Task 2 — PR checklist count mismatch
- [x] CONTRIBUTING.md: "eight" → "ten" to match PR template

#### Task 3 — CI check count in Secure SDL
- [x] SECURE_SDL: executive summary 8 → 14, §4.1 table expanded to 14 checks, ci.yml noted as authoritative

#### Task 4 — Stale sprint state in CLAUDE.md
- [ ] Remove hardcoded sprint number, point to tasks/todo.md as live authority

#### Task 5 — Document Authority Hierarchy
- [ ] Add precedence declaration section to CLAUDE.md

#### Task 6 — Stale path references in retry-policy.md
- [ ] Audit and fix `src/...` paths to `frontend/src/...`

#### Task 7 — Audit ecosystem ownership boundary
- [ ] Create AUDIT_OWNERSHIP.md in .claude/agents/

#### Task 8 — Design instruction tie-break
- [ ] Add brand authority header to designer.md and SKILL.md

#### Review
- Commit: (pending — one commit per task)

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

