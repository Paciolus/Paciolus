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

### Phase XL (Sprints 292–299) — COMPLETE
> Diagnostic Completeness & Positioning Hardening: Revenue concentration sub-typing, Cash Conversion Cycle (DPO/DIO/CCC — 12 ratios), interperiod reclassification detection, TB-to-FS arithmetic trace (raw_aggregate + sign_correction), account density profile (9-section sparse flagging), ISA 520 expectation documentation scaffold, L1-L4 language fixes, 46 new frontend tests. **v1.8.0. Tests: 3,644 + 987.**

### Phase XLI (Sprints 308–312) — COMPLETE
> Cross-Tool Workflow Integration: A-Z lead sheet codes, FLUX_ANALYSIS ToolName enum + Alembic migration, flux extractor registration + engagement wiring, convergence coverage fields, pre-flight→column passthrough, materiality cascade passthrough (_resolve_materiality), composite score trend (get_tool_run_trends + TrendIndicator). 5 workflow gaps bridged, 0 new tools. **Tests: 3,780 + 995.**

### Phase XLII (Sprints 313–318) — COMPLETE
> Design Foundation Fixes: shadow/border token repair, opacity/contrast audit, typography/spacing, 3-batch light theme semantic token migration (~30 components). **Tests: 3,780 + 995.**

### Phase XLIII (Sprints 319–324) — COMPLETE
> Homepage "Ferrari" Transformation: cinematic hero with animated data visualization, gradient mesh atmosphere, scroll-orchestrated narrative sections, interactive product preview (DemoZone rewrite), tool grid redesign + social proof, marketing page polish. 4 new components (HeroVisualization, GradientMesh, ProductPreview, ToolShowcase). **v1.9.0. Tests: 3,780 + 995.**

### Phase XLIV (Sprints 325–329) — COMPLETE
> Tool Pages "Rolls Royce" Refinement: 3-tier card hierarchy (card/elevated/inset) with warm-toned shadows, left-border accent pattern across 6+ components, tabular-nums for financial data, heading-accent with sage dash, paper texture via SVG feTurbulence, prefers-reduced-motion compliance. **v1.9.1. Tests: 3,780 + 995.**

### Phase XLV (Sprints 340–344) — COMPLETE
> Monetary Precision Hardening: 17 Float→Numeric(19,2) columns, shared `monetary.py` (quantize_monetary ROUND_HALF_UP, monetary_equal, BALANCE_TOLERANCE as Decimal), Decimal-aware balance checks, quantize at all DB write boundaries, Decimal modulo in round_amounts. **v1.9.2. Tests: 3,841 + 995.**

### Phase XLVI (Sprints 345–349) — COMPLETE
> Audit History Immutability: SoftDeleteMixin (archived_at/archived_by/archive_reason) on 5 tables (activity_logs, diagnostic_summaries, tool_runs, follow_up_items, follow_up_item_comments), ORM-level `before_flush` deletion guard, all hard-delete paths converted to soft-delete, all read paths filter `archived_at IS NULL`. **v1.9.3. Tests: 3,867 + 995.**

### Phase XLVII (Sprints 350–353) — COMPLETE
> ASC 606 / IFRS 15 Contract-Aware Revenue Testing: 4 new tests (RT-13 to RT-16), 6 optional contract columns, ContractEvidenceLevel, skip-with-reason degradation. **v1.9.4. Tests: 3,891 + 995.**

### Phase XLVIII (Sprints 354–355) — COMPLETE
> Adjustment Approval Gating: VALID_TRANSITIONS map (proposed→approved→posted, posted terminal), InvalidTransitionError, approved_by/approved_at metadata, official/simulation mode replacing include_proposed, is_simulation flag. **v1.9.5. Tests: 3,911 + 995.**

### Phase XLIX (Sprints 356–361) — COMPLETE
> Diagnostic Feature Expansion: JE Holiday Posting (JT-19, ISA 240.A40), Lease Account Diagnostic (IFRS 16/ASC 842), Cutoff Risk Indicator (ISA 501), Engagement Completion Gate (VALID_ENGAGEMENT_TRANSITIONS), Going Concern Indicator Profile (ISA 570), allowlist bugfix. **v2.0.0. Tests: 4,102 + 995.**

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii, phase-xxxviii, phase-xxxix, phase-xl, phase-xli, phase-xlii, phase-xliii, phase-xliv, phase-xlv, phase-xlvi, phase-xlvii, phase-xlviii, phase-xlix)

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
| Dual-key rate limiting | **RESOLVED** — User-aware keying + tiered policies delivered in Sprint 306 | Phase XX |
| Wire Alembic into startup | Latency + multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` dir | Model count doesn't justify yet | Phase XXII |
| Cookie-based auth (SSR) | Large blast radius; requires JWT → httpOnly cookie migration | Phase XXVII |
| Marketing pages SSG | Requires cookie auth first | Phase XXVII |
| Frontend test coverage (30%+) | **RESOLVED** — 83 suites, 44% statements, 35% branches, 25% threshold | Phase XXXVII |
| ISA 520 Expectation Documentation Framework | **RESOLVED** — Delivered in Phase XL Sprint 297 with blank-only guardrail | Council Review (Phase XL) |
| pandas 3.0 upgrade | CoW + string dtype breaking changes; needs dedicated evaluation sprint | Phase XXXVII |
| React 19 upgrade | Major version with breaking changes; needs own phase | Phase XXXVII |

---

### Phase L (Sprints 362–377) — COMPLETE
> Pricing Strategy & Billing Infrastructure: 5-tier billing (Free/Starter/Professional/Team/Enterprise), Stripe integration, entitlement enforcement, A/B pricing, billing dashboard, UpgradeGate/CancelModal. **v2.1.0. Tests: 4,176 + 995.**

### Phases LI–LV + Standalone Sprints (Sprints 378–400) — COMPLETE
> Phase LI: Accounting-Control Policy Gate (5 AST-based checkers, CI job). Phase LII: Unified Workspace Shell "Audit OS". Phase LIII: Proof Architecture "Institution-Grade Evidence Language" (70 new tests). Phase LIV: Elite Typography System "Optical Precision". Phase LV: Global Command Palette "Command Velocity" (10 new files). Sprint 382: IntelligenceCanvas. Sprint 383: Cinematic Hero Product Film. Sprint 384: BrandIcon decomposition. Sprint 400: Interactive Assurance Center. **Tests: 4,252 + 1,057.**

### Phase LVI (Sprints 401–405) — COMPLETE
> State-Linked Motion Choreography: motionTokens.ts semantic vocabulary, useReducedMotion hook, ToolStatePresence shared wrapper (9 tool pages), severity-linked motion (FlaggedEntriesTable, TestingScoreCard, InsightRail, ProofSummaryBar), export resolution 3-state machine (useTestingExport + DownloadReportButton), shared-axis transitions (ContextPane horizontal, InsightRail vertical), modal framer-motion migration (UpgradeModal + CancelModal), 29 new tests. **Tests: 4,252 + 1,086.**

> **Detailed checklists:** `tasks/archive/` (all phases listed above + phase-lvi + phase-lvii)

### Phase LVII (Sprints 406–410) — COMPLETE
> "Unexpected but Relevant" Premium Moments: feature flags, data sonification toggle, AI-style contextual microcopy (InsightRail), intelligence watermark in 17 PDF memos. **Tests: 4,252 + 1,086.**

### Sprints 411–420 — Lint Remediation + Accessibility + Hardening — COMPLETE
> Stabilization & baseline lock (Sprint 411), ESLint toolchain integrity + 687→0 total lint issues (ruff + eslint), 51→0 accessibility errors, exhaustive-deps fixes, backend ruff auto-fix, EditClientModal infinite loop fix, a11y semantic fixes + keyboard regression tests, column detector convergence (adapter pattern), API client safety (RFC 9110 idempotency, LRU cache, Prometheus-ready), Husky + lint-staged pre-commit hooks, contributor guides (accessible-components.md, retry-policy.md), verification release with 5 shim removals. **Tests: 4,294 + 1,163.**

### Sprints 421–431 — Multi-Format File Handling — COMPLETE
> File format abstraction (`file_formats.py` + `fileFormats.ts` single source of truth), TSV/TXT ingestion (delimiter detection), OFX/QBO parser (SGML v1.x + XML v2.x, hand-rolled), IIF parser (QuickBooks Intuit Interchange Format), PDF table ingestion (pdfplumber, quality gates, preview endpoint, PdfExtractionPreview modal). 7 new format parsers, 10 supported file types. **Tests: ~4,530 + ~1,190.**

### Phase LVIII (Sprints 432–438) — COMPLETE
> ODS support (odfpy, ZIP disambiguation), cross-format malformed fixtures (18 tests across 7 formats), resource guard + performance tests, Prometheus metrics infrastructure (4 metrics, /metrics endpoint), feature flags + tier-gated format access (FREE=5 basic, STARTER=+4, PRO+=all), TOML-based alert thresholds + 8 runbook docs, integration testing. **Tests: ~4,650 + ~1,190.**

> **Detailed checklists:** `tasks/archive/` (all phases listed above + sprints-411-438-details)

### Report Standardization (Sprints 0–8) — COMPLETE
> Report Standards Alignment: FASB/GASB framework resolution (Sprint 1), unified cover page + brand system (Sprint 2), universal scope/methodology with framework-aware citations (Sprint 3), text layout hardening (Sprint 4), heading readability & typographic consistency (Sprint 5), source document transparency (Sprint 6), signoff section deprecation (Sprint 7), QA automation + regression guardrails + rollout playbook (Sprint 8). 79 new tests, CI report-standards gate, policy validation script. **Tests: ~4,730 + ~1,190.**

> **Detailed checklists:** `tasks/archive/report-standardization-details.md`

---

## Active Phase

### Phase LX — Post-Launch Pricing Control System

**Status:** COMPLETE — All 4 sprints delivered, 28 new tests, regression clean
**Goal:** Low-overhead post-launch control system — decision metrics, weekly review, price-change guardrails.

#### Sprint Plan
- [x] **Sprint A:** BillingEvent model + Prometheus lifecycle counters + event taxonomy
- [x] **Sprint B:** Analytics engine (5 decision metrics) + webhook/route instrumentation
- [x] **Sprint C:** Weekly review endpoint + pricing guardrail policy docs
- [x] **Sprint D:** Tests + verification (28/28 passing, frontend build clean)

---

### Phase LIX — Hybrid Pricing Model Overhaul

**Decision Record:** `tasks/decisions/pricing-model-overhaul.md`
**Status:** COMPLETE — All 6 sprints delivered, verified, regression clean

**Migration Strategy:** Option A — Display-Name Only (internal tier IDs unchanged)
**Launch Model:** Solo ($50/$500) / Team ($130/$1,300) / Organization ($400/$4,000) + tiered seats + 7-day trial
**Key Decisions:** No customers → clean professional removal, A/B retired, soft seat enforcement 30 days, contact form for 26+ seats

#### Sprint Plan (6 sprints)
- [x] **Sprint A:** Display-Name Layer + Config Overhaul + Professional Removal
- [x] **Sprint B:** Seat Model + Stripe Product Architecture
- [x] **Sprint C:** Trial + Promo Infrastructure
- [x] **Sprint D:** Frontend Pricing Page Overhaul
- [x] **Sprint E:** Checkout Flow + Seat Management
- [x] **Sprint F:** Integration Testing + Feature Flag Rollout

---

### Billing Launch Configuration Sprint — In Progress

**Goal:** Close the "last mile" — load Stripe Price IDs from env vars (currently hardcoded empty), add startup validation, create deployment runbook.

#### Checklist
- [x] `price_config.py`: Add `_load_stripe_price_ids()` lazy-loader, update `get_stripe_price_id()`
- [x] `price_config.py`: Add `validate_billing_config()` startup validator
- [x] `webhook_handler.py`: Fix `_resolve_tier_from_price()` to use loader instead of empty dict
- [x] `main.py`: Wire `validate_billing_config()` in lifespan
- [x] `config.py`: Add billing lines to `print_config_summary()`
- [x] `.env.example`: Add 6 base + 2 seat price ID env var docs
- [x] `docs/runbooks/billing-launch.md`: Deployment runbook
- [x] Verification: `pytest` billing tests (210 passed) + `npm run build` (clean)

---

### Tier ID Rename: starter → solo — COMPLETE

**Goal:** Align internal tier ID with public display name ("Solo").

#### Checklist
- [x] Alembic migration (`d9e0f1a2b3c4`): PG enum add + data migration
- [x] `models.py`: `UserTier.STARTER` → `UserTier.SOLO`
- [x] `subscription_model.py`: inline Enum string
- [x] `shared/entitlements.py`: `_STARTER_TOOLS/FORMATS` → `_SOLO_*`, enum refs
- [x] `shared/tier_display.py`: enum ref + `PURCHASABLE_TIERS`
- [x] `shared/rate_limits.py`: policy key + backward-compat alias
- [x] `billing/price_config.py`: `PRICE_TABLE`, `_PAID_TIERS`, `TRIAL_ELIGIBLE_TIERS`
- [x] `routes/billing.py`: `CheckoutRequest` regex + seat validation
- [x] `.env.example`: `STRIPE_PRICE_STARTER_*` → `STRIPE_PRICE_SOLO_*`
- [x] Frontend types (`auth.ts`, `commandPalette.ts`)
- [x] Frontend components (`PlanCard`, `UpgradeModal`, `UpgradeGate`)
- [x] Frontend pages (`checkout`, `pricing`)
- [x] Frontend lib (`commandRegistry.ts`)
- [x] 10 backend test files (zero remaining "starter" references)
- [x] 3 frontend test files (zero remaining "starter" references)
- [x] Grep verification: no stale references outside migrations + compat alias

---

### Pricing Launch Validation Matrix — COMPLETE

**Goal:** Fill every automated test gap for pricing launch: checkout flow matrix, webhook lifecycle state-machine, entitlement enforcement, promo policy, old-subscriber regression, plus manual QA + launch sign-off artifacts.

#### Deliverables
- [x] Backend `test_pricing_launch_validation.py` — 188 tests across 7 classes (all passing)
- [x] Frontend `PricingLaunchCheckout.test.tsx` — 28 tests (all passing)
- [x] Frontend `PricingLaunchBillingHook.test.ts` — 20 tests (all passing)
- [x] Manual QA checklist `tasks/pricing-launch-qa.md` — 6 areas, ~100 checkpoints
- [x] Launch readiness report `tasks/pricing-launch-readiness.md` — sign-off document with validation matrix results

#### Verification
- [x] Backend: 188/188 passing
- [x] Frontend: 48/48 passing (28 checkout + 20 billing hook)
- [x] Frontend build: clean (no regressions)
- [x] Readiness report populated with actual test counts
