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

### Sprint 480 — HeroProductFilm Redesign
**Status:** COMPLETE
**Goal:** Fix broken animation on PC (reduced-motion fallback hiding scrubber), add rich animations to all 3 slides, invert color scheme to oatmeal.

- [x] Fix reduced-motion: always render ScrubberHero, use `MotionConfig reducedMotion="user"` instead of hiding entire UI
- [x] Upload slide — Cursor + File Card: animated cursor drags file card into drop zone with bounce landing, data cascade
- [x] Analyze slide — Scanning Matrix: scanning line sweep, tile activation with progress bars + checkmarks, counter 0→108, findings badge
- [x] Export slide — Progress Bar Download: file rows slide in, progress bar 0%→100%, checkmark bloom, file size counter
- [x] Film panel color inversion: white/oatmeal film panel + layer backgrounds, dark text inside panel only
- [x] Section/left column/scrubber: kept original dark obsidian theme (not inverted)
- [x] StaticFallback updated: tab navigation with light film panel, dark section background
- [x] Analyze dwell time: 5000ms → 10000ms for richer animation viewing
- [x] Build verification: `npm run build` passes
- [x] Test verification: `npm test` — all suites passing (verified Sprint 482)

**Review:** Complete rewrite of HeroProductFilm.tsx. Color inversion scoped to film panel only (section/left column/scrubber remain dark). Analyze dwell increased to 10s to let viewers absorb the scanning matrix animation. Commits: 78f2d52, fd1a6a0, f4bdf92.

---

### Sprint 482 — Digital Excellence Council Audit #2 Remediation
**Status:** COMPLETE
**Goal:** Fix all 17 findings from the 2026-03-04 Digital Excellence Council audit.

- [x] F-001 (P2): Add retroactive Sprint 481 todo.md entry
- [x] F-002 (P2): Update stale Stripe env var names in `.env.example` (Team→Professional, add Enterprise, fix seat price var names)
- [x] F-003 (P2): Add `scope="col"` to pricing table `<th>`, `scope="row"` to first-column cells, `<caption className="sr-only">`
- [x] F-004 (P2): Add `aria-controls`, `id`, `role="region"`, `aria-labelledby` to FAQ accordion
- [x] F-005 (P2): Replace stale `progress.get()` with `STEPS.indexOf(activeStep)` for `aria-valuenow`
- [x] F-006 (P2): Add `aria-valuetext={STEP_LABELS[activeStep]}` to timeline slider
- [x] F-007 (P3): Convert 3 remaining f-string SQL to `.bindparams()` in `test_timestamp_defaults.py`
- [x] F-008 (P3): Remove `status_code=200` from accrual-completeness endpoint
- [x] F-009 (P3): Replace `animate-pulse` with `motion-safe:animate-pulse` for reduced-motion compliance
- [x] F-010 (P3): Add `as const` to `ease: 'linear'` in HeroProductFilm scanning line transition
- [x] F-011 (P3): Remove `StaticFallback` dead code (136 lines)
- [x] F-012 (P3): Replace `rgba(189,189,189,0.3)` with obsidian-palette `rgba(176,176,176,0.3)`
- [x] F-013 (P3): Interpolate FAQ seat pricing from `SEAT_CONFIGS` constants instead of hardcoded values
- [x] F-014 (P3): Add Sprint 481 entry documenting all 4 orphaned commits
- [x] F-015 (P3): Add `npm test` verification note to Sprint 480 review
- [x] F-016 (P3): Add `role="radiogroup"` / `role="radio"` / `aria-checked` to SegmentedSelector and BillingToggle
- [x] F-017 (P3): Add `aria-hidden="true"` to decorative SVGs (CursorIcon, play/pause, feature checkmarks)
- [x] Update PricingPage test: `getByRole('button')` → `getByRole('radio')` for billing toggle
- [x] Build verification: `npm run build` passes
- [x] Test verification: `npm test` — 111 suites, 1,337 tests passing (full suite, pre-existing EditClientModal failure fixed)
- [x] Audit 25 remediations: EditClientModal React 19 compat fix, remediation completeness lesson added

**Review:** All 17 findings addressed (6 P2 + 11 P3). Key changes: pricing page ARIA overhaul (scope, radiogroup, FAQ disclosure pattern), HeroProductFilm slider accessibility (valuetext, deterministic valuenow), reduced-motion compliance (motion-safe prefix), dead code removal, .env.example Stripe var name correction. Pre-existing EditClientModal test failure fixed (React 19 controlled input compat — `userEvent.type` → `fireEvent.change`). Remediation completeness lesson captured in `tasks/lessons.md`. Council report: `reports/council-audit-2026-03-04.md`

---

### Sprint 481 — Plan Estimator & Pricing Page Redesign
**Status:** COMPLETE
**Goal:** Redesign pricing page Plan Estimator to match tier upload limits, switch tools→features axis, add oatmeal accents across color spectrum, remove Most Popular badge, unify card styling.

- [x] Plan Estimator: uploads selector now matches actual tier limits (Under 10/100/500/Unlimited)
- [x] Tools axis replaced with Features axis (Core tools & exports / + Team & sharing / + Branding & bulk)
- [x] Oatmeal accents introduced across full color spectrum (borders, badges, dividers)
- [x] Most Popular badge removed; all cards use unified sage-accent styling
- [x] Sage divider accents added between sections
- [x] Fix Platform nav link to go to homepage hero instead of #tools anchor
- [x] Build verification: `npm run build` passes

**Review:** Pricing page redesign across 4 commits: d44239f (card styling + sage accents), 2991cfc (oatmeal accents), 893715f (nav link fix), e3d6c88 (estimator redesign). All changes are frontend-only, marketing page scope.

---

### Sprint 479 — Digital Excellence Council Audit Remediation
**Status:** COMPLETE
**Goal:** Fix all 7 findings from the inaugural Digital Excellence Council audit (2026-03-03).

- [x] F-001 (P2): Replace `time.sleep(1.1)` with deterministic timestamp in `test_password_revocation.py`
- [x] F-002 (P2): Document ExportShare as controlled zero-storage exception in `SECURITY_POLICY.md`
- [x] F-003 (P3): Add `as const` to 11 framer-motion transition type properties across 6 files
- [x] F-004 (P3): Replace f-string SQL interpolation with `bindparams()` in `test_timestamp_defaults.py`
- [x] F-005 (P3): Add `encodeURIComponent()` to pathname in workspace layout redirect
- [x] F-006 (P3): Document APScheduler multi-worker deployment model in `.env.example`
- [x] F-007 (P3): Remove redundant `status_code=200` from 3 POST endpoints in `audit.py`
- [x] Build verification: `npm run build` passes, `pytest` passes on modified tests

**Review:** All 7 findings addressed. 0 P0/P1 findings. Both P2 findings resolved (deterministic test + policy documentation). Council report: `reports/council-audit-2026-03-03.md`

---

### Sprint 477 — Copy Consistency & Trust Remediation
**Status:** COMPLETE
**Goal:** Audit and fix trust-eroding inconsistencies across marketing copy, legal pages, and public-facing source files.

- [x] Phase 1: Standardize performance claims (< 2s → < 3s, add "typically" qualifiers)
- [x] Phase 2: Fix false storage claims (browser-only → server in-memory), add qualifiers
- [x] Phase 3: Standardize response SLA (one business day → 1–2 business days)
- [x] Phase 4: Fix email domain (@paciolus.io → @paciolus.com)
- [x] Phase 5: Soften trust/security language (self-assessed GDPR/CCPA, SOC 2 audit in progress)
- [x] Phase 6: Clean sprint references from JSDoc headers and CSS comments (31 files)
- [x] Build verification: `npm run build` passes

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
