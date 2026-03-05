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
| Deprecated alias migration | 21 deprecated exports across 6 files; see Sprint 478 plan below | Sprint 477 |

---

## Active Phase

> Sprints 477–487 completed and archived to `tasks/archive/`. Next pending items below.

### Sprint 488 — Financial Statements Report Improvements

**Status:** COMPLETE
**Goal:** Enhance Report 02 (Financial Statements) with 5 changes: 4 new ratios, prior year comparative columns, footnote placeholders, cross-reference legend, Quality of Earnings expansion.
**Complexity Score:** Medium-High

#### Changes
- [x] CHANGE 1: Add Quick Ratio, EBITDA, EBITDA Margin, Interest Coverage to Key Financial Ratios (reorder to 12 ratios)
- [x] CHANGE 2: Prior year comparative columns on BS/IS/ratios when prior_lead_sheet_grouping available
- [x] CHANGE 3: Notes to Financial Statements section (5 placeholder notes)
- [x] CHANGE 4: Cross-Reference Index legend after BS and IS
- [x] CHANGE 5: Quality of Earnings — rename to Cash Conversion Ratio, add benchmark sentence

#### Files Modified
- `backend/financial_statement_builder.py` — Add depreciation_amount, interest_expense, prior period fields to FinancialStatements
- `backend/pdf_generator.py` — All 5 rendering changes
- `backend/generate_sample_reports.py` — Update Meridian sample data
- `backend/tests/test_financial_statements.py` — New tests for added fields

#### Verification
- [x] `npm run build` passes
- [x] `pytest tests/test_financial_statements.py -v` passes (46/46)
- [x] Regenerate sample report 02 (50,183 bytes)

#### Review
- All 5 changes implemented, 11 new tests added (35 → 46)
- Ratio computations verified: Quick=2.05x, EBITDA=$1,745,000, EBITDA Margin=25.5%, Interest Coverage=15.9x
- Prior period comparative columns render as table format when prior data available, leader-dot format when not
- Footnotes section renders 5 placeholder stubs with disclaimer
- Cross-reference legends render dynamically based on non-zero lead sheet refs

---

### Sprint 478 — Deprecated Alias Migration

**Status:** PLANNED
**Goal:** Remove 21 deprecated exports across 6 utility files. Migrate consumers to canonical `@/lib/motion` and `ThresholdStatus` APIs.
**Complexity Score:** Low-Medium (most are zero-consumer deletions; 2 components + 3 test files need updating)

#### Wave 1: Zero-Consumer Deletions (safe, no migration needed)
- [ ] `themeUtils.ts`: Delete `MODAL_OVERLAY_VARIANTS` (ln 244), `MODAL_CONTENT_VARIANTS` (ln 250), `createContainerVariants` (ln 267), `CONTAINER_VARIANTS` (ln 284), `createCardStaggerVariants` (ln 294)
- [ ] `marketingMotion.tsx`: Delete `STAGGER` (ln 55), `SectionReveal` (ln 264)
- [ ] `types/mapping.ts`: Delete `HealthStatus` type alias (ln 147)
- [ ] `HeroProductFilm.tsx` + `components/marketing/index.ts`: Remove `HeroProductFilm` alias export (ln 991) and barrel re-export

#### Wave 2: Health → Threshold Rename (2 components + barrel + test)
- [ ] `MetricCard.tsx`: Change `HealthStatus` → `ThresholdStatus`, `getHealthClasses` → `getThresholdClasses`, `getHealthLabel` → `getThresholdLabel`
- [ ] `IndustryMetricsSection.tsx`: Same renames
- [ ] `utils/index.ts`: Remove deprecated re-exports (lines 57–60, 86–87); add `ThresholdStatus`, `ThresholdClasses`, `THRESHOLD_STATUS_CLASSES`, `getThresholdClasses`, `getThresholdLabel` re-exports
- [ ] `themeUtils.test.ts`: Update test imports to use canonical names
- [ ] `themeUtils.ts`: Delete `HealthStatus`, `HealthClasses`, `HEALTH_STATUS_CLASSES`, `getHealthClasses`, `getHealthLabel`

#### Wave 3: Motion Token Internals (internal rewiring)
- [ ] `motionTokens.ts`: Inline `DURATION` values into `TIMING` (remove `import { DURATION } from './animations'` + spread). Inline `OFFSET` values into `DISTANCE` (remove `import { OFFSET } from './marketingMotion'` + spread)
- [ ] `marketingMotion.tsx`: Inline `DURATION.hero` value (remove `import { DURATION } from './animations'`)
- [ ] `animations.ts`: Delete `fadeInUp`, `fadeInUpSpring`, `fadeIn`, `DURATION`
- [ ] `animations.test.ts`: Delete deprecated export tests (keep non-deprecated `dataFillTransition`, `scoreCircleTransition` tests)
- [ ] `motionTokens.ts`: Delete `DISTANCE` deprecated export
- [ ] `utils/index.ts`: Remove `DISTANCE` re-export
- [ ] `motionTokens.test.ts`: Update `DISTANCE` tests to test via `STATE_CROSSFADE` or remove

#### Wave 4: ENTER.clipReveal Migration (1 consumer)
- [ ] `FeaturePillars.tsx`: Replace `ENTER.clipReveal` with equivalent inline variant or move `clipReveal` to `@/lib/motion`
- [ ] `marketingMotion.tsx`: Delete `ENTER` and `OFFSET` exports

#### Verification
- [ ] `npm run build` passes
- [ ] `npx jest --no-coverage` passes (full suite)
- [ ] `grep -r "@deprecated" src/utils/themeUtils.ts src/utils/animations.ts src/utils/motionTokens.ts src/utils/marketingMotion.tsx src/types/mapping.ts` returns zero results

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
