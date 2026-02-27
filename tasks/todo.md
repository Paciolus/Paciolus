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
> Multi-Currency Conversion: python-jose → PyJWT, closing-rate MVP, currency engine (ISO 4217 + vectorized conversion), 4 API endpoints, CurrencyRatePanel, conversion memo PDF, auto-conversion in TB upload. **v1.3.0. Tests: 3,129 + 520.**

### Phase XXXV (Sprints 261–266 + T1) — COMPLETE
> In-Memory State Fix + Codebase Hardening: stateless HMAC CSRF, DB-backed lockout + tool sessions, float precision (math.fsum/Decimal), server_default timestamps, 8 dependency upgrades, deep health probe, CI security gates (Bandit/Dependabot/pip-audit), zero-storage language truthfulness. **Tests: 3,323 + 724.**

### Phase XXXVI (Sprints 268–272) — COMPLETE
> Statistical Sampling Module (Tool 12): ISA 530 / PCAOB AS 2315, MUS + random sampling, 2-tier stratification, Stringer bound evaluation, two-phase workflow (design + evaluate), PDF memo, CSV export, 12-tool nav. **v1.4.0. Tests: 3,391 + 745.**

### Phase XXXVII (Sprints 273–278) — COMPLETE
> Deployment Hardening: dependency version bumps, PostgreSQL pool tuning + CI job, Sentry APM (Zero-Storage compliant), 23 new frontend test files (173 new tests), coverage threshold 25%. **v1.5.0. Tests: 3,396 + 918.**

### Phase XXXVIII (Sprints 279–286) — COMPLETE
> Security & Accessibility Hardening + Lightweight Features: passlib→bcrypt, CVE patches, typing modernization, ruff rules, back_populates migration, WCAG modals/labels/images/CSP, focus trap, eslint-plugin-jsx-a11y, Data Quality Pre-Flight Report, Account-to-Statement Mapping Trace. **v1.6.0. Tests: 3,440 + 931.**

### Phase XXXIX (Sprints 287–291) — COMPLETE
> Diagnostic Intelligence Features: TB Population Profile (Gini, magnitude buckets), Cross-Tool Account Convergence Index, Expense Category Analytical Procedures (5-category ISA 520), Accrual Completeness Estimator. 11 new API endpoints, 4 new TB sections, 4 PDF memos. **v1.7.0. Tests: 3,547 + 931.**

### Phase XL (Sprints 292–299) — COMPLETE
> Diagnostic Completeness & Positioning Hardening: Revenue concentration sub-typing, Cash Conversion Cycle (DPO/DIO/CCC — 12 ratios), interperiod reclassification detection, TB-to-FS arithmetic trace, account density profile (9-section sparse flagging), ISA 520 expectation documentation scaffold, L1-L4 language fixes, 46 new frontend tests. **v1.8.0. Tests: 3,644 + 987.**

### Phase XLI (Sprints 308–312) — COMPLETE
> Cross-Tool Workflow Integration: A-Z lead sheet codes, FLUX_ANALYSIS ToolName enum + Alembic migration, flux extractor registration + engagement wiring, convergence coverage fields, pre-flight→column passthrough, materiality cascade passthrough, composite score trend. 5 workflow gaps bridged. **Tests: 3,780 + 995.**

### Phase XLII (Sprints 313–318) — COMPLETE
> Design Foundation Fixes: shadow/border token repair, opacity/contrast audit, typography/spacing, 3-batch light theme semantic token migration (~30 components). **Tests: 3,780 + 995.**

### Phase XLIII (Sprints 319–324) — COMPLETE
> Homepage "Ferrari" Transformation: cinematic hero (HeroVisualization), scroll-orchestrated narrative sections, interactive product preview (ProductPreview), tool grid redesign + social proof (ToolShowcase), marketing page polish. 4 new components. **v1.9.0. Tests: 3,780 + 995.**

### Phase XLIV (Sprints 325–329) — COMPLETE
> Tool Pages "Rolls Royce" Refinement: 3-tier card hierarchy with warm-toned shadows, left-border accent pattern, tabular-nums for financial data, heading-accent with sage dash, paper texture via SVG feTurbulence, prefers-reduced-motion compliance. **v1.9.1. Tests: 3,780 + 995.**

### Phase XLV (Sprints 340–344) — COMPLETE
> Monetary Precision Hardening: 17 Float→Numeric(19,2) columns, shared `monetary.py` (quantize_monetary ROUND_HALF_UP, BALANCE_TOLERANCE as Decimal), Decimal-aware balance checks, quantize at all DB write boundaries. **v1.9.2. Tests: 3,841 + 995.**

### Phase XLVI (Sprints 345–349) — COMPLETE
> Audit History Immutability: SoftDeleteMixin (archived_at/archived_by/archive_reason) on 5 tables, ORM-level `before_flush` deletion guard, all hard-delete paths converted to soft-delete, all read paths filter `archived_at IS NULL`. **v1.9.3. Tests: 3,867 + 995.**

### Phase XLVII (Sprints 350–353) — COMPLETE
> ASC 606 / IFRS 15 Contract-Aware Revenue Testing: 4 new tests (RT-13 to RT-16), 6 optional contract columns, ContractEvidenceLevel, skip-with-reason degradation. **v1.9.4. Tests: 3,891 + 995.**

### Phase XLVIII (Sprints 354–355) — COMPLETE
> Adjustment Approval Gating: VALID_TRANSITIONS map (proposed→approved→posted, posted terminal), InvalidTransitionError, approved_by/approved_at metadata, official/simulation mode, is_simulation flag. **v1.9.5. Tests: 3,911 + 995.**

### Phase XLIX (Sprints 356–361) — COMPLETE
> Diagnostic Feature Expansion: JE Holiday Posting (JT-19, ISA 240.A40), Lease Account Diagnostic (IFRS 16/ASC 842), Cutoff Risk Indicator (ISA 501), Engagement Completion Gate (VALID_ENGAGEMENT_TRANSITIONS), Going Concern Indicator Profile (ISA 570), allowlist bugfix. **v2.0.0. Tests: 4,102 + 995.**

### Phase L (Sprints 362–377) — COMPLETE
> Pricing Strategy & Billing Infrastructure: 5-tier billing (Free/Starter/Professional/Team/Enterprise), Stripe integration, entitlement enforcement, A/B pricing, billing dashboard, UpgradeGate/CancelModal. **v2.1.0. Tests: 4,176 + 995.**

### Phases LI–LV + Standalone Sprints (Sprints 378–400) — COMPLETE
> Phase LI: Accounting-Control Policy Gate (5 AST-based checkers, CI job). Phase LII: Unified Workspace Shell "Audit OS". Phase LIII: Proof Architecture "Institution-Grade Evidence Language" (70 new tests). Phase LIV: Elite Typography System "Optical Precision". Phase LV: Global Command Palette "Command Velocity" (10 new files). Sprint 382: IntelligenceCanvas. Sprint 383: Cinematic Hero Product Film. Sprint 384: BrandIcon decomposition. Sprint 400: Interactive Assurance Center. **Tests: 4,252 + 1,057.**

### Phase LVI (Sprints 401–405) — COMPLETE
> State-Linked Motion Choreography: motionTokens.ts semantic vocabulary, useReducedMotion hook, ToolStatePresence shared wrapper (9 tool pages), severity-linked motion, export resolution 3-state machine (useTestingExport + DownloadReportButton), shared-axis transitions (ContextPane + InsightRail), modal framer-motion migration (UpgradeModal + CancelModal), 29 new tests. **Tests: 4,252 + 1,086.**

### Phase LVII (Sprints 406–410) — COMPLETE
> "Unexpected but Relevant" Premium Moments: feature flags, data sonification toggle, AI-style contextual microcopy (InsightRail), intelligence watermark in 17 PDF memos. **Tests: 4,252 + 1,086.**

### Sprints 411–420 — Lint Remediation + Accessibility + Hardening — COMPLETE
> Stabilization & baseline lock (Sprint 411), 687→0 total lint issues (ruff + eslint), 51→0 accessibility errors, exhaustive-deps fixes, EditClientModal infinite loop fix, column detector convergence (adapter pattern), API client safety (RFC 9110 idempotency, LRU cache), Husky + lint-staged pre-commit hooks, contributor guides, 5 shim removals. **Tests: 4,294 + 1,163.**

### Sprints 421–431 — Multi-Format File Handling — COMPLETE
> File format abstraction (`file_formats.py` + `fileFormats.ts`), TSV/TXT ingestion (delimiter detection), OFX/QBO parser (SGML v1.x + XML v2.x), IIF parser (QuickBooks), PDF table ingestion (pdfplumber, quality gates, preview endpoint + modal). 7 new format parsers, 10 supported file types. **Tests: ~4,530 + ~1,190.**

### Phase LVIII (Sprints 432–438) — COMPLETE
> ODS support (odfpy, ZIP disambiguation), cross-format malformed fixtures (18 tests, 7 formats), resource guards + performance baselines, Prometheus metrics (4 counters, /metrics endpoint), feature flags + tier-gated format access (FREE=5 basic, SOLO=+4, PRO+=all), TOML alert thresholds + 8 runbook docs, integration testing. **Tests: ~4,650 + ~1,190.**

### Report Standardization (Sprints 0–8) — COMPLETE
> FASB/GASB framework resolution, unified cover page + brand system, universal scope/methodology with framework-aware citations, text layout hardening, heading readability, source document transparency, signoff section deprecation, QA automation + CI report-standards gate. 79 new tests. **Tests: ~4,730 + ~1,190.**

### Phase LIX + Billing Standalones — COMPLETE
> Hybrid Pricing Model Overhaul: Solo/Team/Organization tiers (display-name-only migration), seat-based pricing (4–25 seats, tiered $80/$70), 7-day trial, promo infrastructure (MONTHLY20/ANNUAL10), checkout flow overhaul, `starter`→`solo` tier rename (Alembic + full codebase), pricing launch validation (216+ tests), BillingEvent table migration (b590bb0555c3), billing runbooks, Stripe test-mode configuration (4 products, 8 prices, 2 coupons).

### Phase LX (Sprints 439–440) — COMPLETE
> Post-Launch Pricing Control System: BillingEvent append-only model (10 event types), billing analytics engine (5 decision metrics + weekly review aggregation), 3 Prometheus counters, webhook + cancel endpoint instrumentation, `GET /billing/analytics/weekly-review`, pricing guardrails doc (90-day freeze, one-lever rule, decision rubric), weekly review template. Sprint 439: BillingEvent migration + runbook env var fix. Sprint 440: Billing E2E smoke test (27/27 passed), Stripe error handling (6 endpoints). **28 new backend tests.**

### Phase LXI (Sprints 441–444) — COMPLETE
> Technical Upgrades: React 19 (19.2.4, removed 11 JSX.Element annotations), Python 3.12-slim-bookworm + Node 22-alpine Docker images, fastapi 0.133.1 + sqlalchemy 2.0.47, rate limiter risk documentation + 5 canary tests.

### Compliance Documentation Pack — COMPLETE
> Security Policy v2.0 (JWT 30-min/7-day rotation, DB lockout, HMAC CSRF, rate limit table, Docker 3.12/22, Bandit/pip-audit scanning, structured logging), Zero-Storage Architecture v2.0+v2.1 (multi-format, engagement/billing tables, terminology clarity, control verification), Compliance Index + Changelog (versioning/archival process), User Guide v3.0 (12 tools, 10 formats, 3 billing tiers), DPA + Subprocessor List v1.0, Operational Governance Pack v1.0 (6 docs: IRP, BCP/DR, Access Control, Secure SDL, VDP, Audit Logging).

### Sprints 445–446 — Coverage Analysis + Usage Metrics Review — COMPLETE
> Backend 92.8% coverage (5,444 tests); frontend 42.9% (1,333 tests; 1 pre-existing failure fixed). coverage-gap-report.md + usage-metrics-review.md produced. Phase LXII — Export & Billing Test Coverage deferred. ODS alert threshold flagged for production review.

### Phase LXII — Export & Billing Test Coverage — COMPLETE
> 113 new backend tests across 3 files: test_export_diagnostics_routes.py (45 tests, 10 endpoints), test_export_testing_routes.py (36 tests, 9 endpoints), test_entitlement_checks_unit.py (32 tests, 6 functions). Coverage: export_diagnostics.py 17%→90%, export_testing.py 19%→87%, entitlement_checks.py 40%→99%. Backend total: 92.8%→94% (5,557 tests).

### Brand Voice Alignment — COMPLETE
> 9 files updated (string literals only, no logic changes): FeaturePillars (factual fix: "Zero-Knowledge" → "Zero-Storage"; server-side processing correctly described; subtitle, all 3 pillar titles/taglines/descriptions), ProofStrip (4th metric: "Built for auditors" → "140+ automated tests", section label), MarketingFooter (tagline), about/page.tsx (hero subtitle, blockquote, CTA h2 + subtitle), contact/page.tsx (page subtitle), pricing/page.tsx (hero headline + subtitle), register/page.tsx (page subtitle), README.md (opening paragraph, Next.js 16/Python 3.12/Node 22 versions), USER_GUIDE.md (welcome paragraph + Zero-Storage bullet). Build: ✓ 39/39 static pages, no errors.

### Sprint 448 — pandas 3.0 Evaluation — COMPLETE
> CoW + string dtype evaluation against pandas 3.0.1. 1 breaking change found: `dtype == object` guard in `shared/helpers.py:571` bypassed cell-length protection because pandas 3.0 uses `pd.StringDtype()` ("str") for CSV string columns instead of `object`. Fixed to `pd.api.types.is_string_dtype()`. CoW patterns verified (explicit `.copy()`, `iloc` slice `.copy()`, dict assignments — all safe). `inplace=True` for `df.drop()` confirmed safe in pandas 3.0. Perf baseline: 10k-row TB parse @ 46ms avg (3 trials). All 5,557 tests pass, 1 skipped. **Commit: 0cbc8ab**

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii, phase-xxxviii, phase-xxxix, phase-xl, phase-xli, phase-xlii, phase-xliii, phase-xliv, phase-xlv, phase-xlvi, phase-xlvii, phase-xlviii, phase-xlix, phase-lvi, phase-lvii, sprints-411-438-details, report-standardization-details, billing-launch-details, compliance-docs-details)

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
- [ ] `pytest` passes (if tests modified)
- [ ] Zero-Storage compliance verified (if new data handling)
- [ ] Sprint status → COMPLETE, Review section added
- [ ] Lessons added to `lessons.md` (if corrections occurred)
- [ ] `git add <files> && git commit -m "Sprint X: Description"`
- [ ] Record commit SHA in sprint Review section (e.g., `Commit: abc1234`)

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
| Cookie-based auth (SSR) | **RESOLVED — Phase LXIV** — HttpOnly cookie session hardening complete: refresh tokens in `paciolus_refresh` HttpOnly/Secure/SameSite=Lax cookie, access tokens in React `useRef` (in-memory only), `remember_me` via `max_age` policy. Commit: 7ed278f | Phase XXVII |
| Marketing pages SSG | Cookie auth prerequisite now met (Phase LXIV). SSG itself still deferred — requires Next.js SSR wiring + route-level cookie passing | Phase XXVII |
| Frontend test coverage (30%+) | **RESOLVED** — 83 suites, 44% statements, 35% branches, 25% threshold | Phase XXXVII |
| ISA 520 Expectation Documentation Framework | **RESOLVED** — Delivered in Phase XL Sprint 297 with blank-only guardrail | Council Review (Phase XL) |
| pandas 3.0 upgrade | **RESOLVED — Sprint 448** — 1 breaking change found and fixed: `dtype == object` guard in `shared/helpers.py` replaced with `pd.api.types.is_string_dtype()`. All 5,557 tests pass. CoW patterns verified clean. inplace=True drop confirmed safe. Perf baseline: 10k rows @ 46ms avg. | Phase XXXVII |
| React 19 upgrade | **RESOLVED** — Delivered in Phase LXI Sprint 441 | Phase XXXVII |
| Phase LXII — Export & Billing Test Coverage | **COMPLETE** — export_diagnostics.py 17%→90%, export_testing.py 19%→87%, entitlement_checks.py 40%→99%. 113 new tests. Backend total: 92.8%→94%. | Sprint 445 → Sprint 447 |

---

## Active Phase

### Security Sprint — Billing Redirect Integrity & Checkout Anti-Abuse — COMPLETE

**Status:** COMPLETE
**Goal:** Eliminate open-redirect / URL injection attack surface in the Stripe checkout flow.

#### Implementation Checklist
- [x] `backend/shared/parser_metrics.py` — add `billing_redirect_injection_attempt_total` Prometheus counter (label: `field`)
- [x] `backend/billing/checkout.py` — remove `success_url`/`cancel_url` params; derive from `FRONTEND_URL` with fail-safe guard
- [x] `backend/routes/billing.py` — `CheckoutRequest`: remove URL fields, add `ConfigDict(extra="ignore")`, add `model_validator(mode='before')` Prometheus monitor; remove args from endpoint call
- [x] `frontend/src/hooks/useBilling.ts` — remove `successUrl`/`cancelUrl` params from `createCheckoutSession()`; remove from request body
- [x] `frontend/src/app/(auth)/checkout/page.tsx` — remove URL args from `createCheckoutSession()` call
- [x] Backend tests updated: `test_billing_routes.py` (+7 new `TestCheckoutRedirectIntegrity` tests), `test_seat_management.py`, `test_trial_promo.py`, `test_pricing_integration.py`, `test_pricing_launch_validation.py` (2 obsolete URL-validation tests replaced with new-behavior assertions)
- [x] Frontend tests updated: `PricingLaunchBillingHook.test.ts` (URL args removed, no-URL-in-body assertion added)

#### Verification
- [x] `pytest backend/tests/test_billing_routes.py` — 58 passed (7 new)
- [x] `pytest backend/tests/` — 5,564 passed, 1 skipped
- [x] `npm run build` — clean
- [x] `npx jest PricingLaunchBillingHook PricingLaunchCheckout` — 48 passed

#### Review
- All 7 `TestCheckoutRedirectIntegrity` tests pass: derived URLs, injection stripping, Prometheus monitoring (per-field, both fields), malicious scheme, data: URI, FRONTEND_URL guard
- 2 stale tests in `test_pricing_launch_validation.py` replaced with correct new-behavior assertions
- Attack surface eliminated: no user input reaches Stripe's `success_url`/`cancel_url` parameters
- **Tests: 5,564 backend + 1,345 frontend**

---

### Security Sprint — Verification Token Storage Hardening — COMPLETE

**Status:** COMPLETE
**Goal:** Eliminate plaintext email verification tokens at rest. SHA-256 hash at write time, hash-then-compare at read time. Mirror the refresh token pattern.

#### Implementation Checklist
- [x] `backend/auth.py` — `_hash_token` → `hash_token` (public); update `update_user_profile` to store `token_hash` and remove `user.email_verification_token` assignment
- [x] `backend/models.py` — `EmailVerificationToken.token` → `token_hash` (String(64), unique, indexed); remove `User.email_verification_token` column
- [x] `backend/routes/auth_routes.py` — import `hash_token`; store `token_hash=hash_token(raw)` in `register` + `resend_verification`; lookup by `token_hash == hash_token(token)` in `verify_email`; remove `user.email_verification_token` assignments
- [x] `backend/migrations/alembic/versions/ecda5f408617_hash_email_verification_tokens.py` — DELETE existing tokens; rename column; swap index; drop `users.email_verification_token`
- [x] `backend/tests/test_email_verification.py` — token_hash field names; remove stale User.email_verification_token assertions
- [x] `backend/tests/test_sprint202_cleanup.py` — token_hash field names + hash_token() calls
- [x] `backend/tests/test_email_change.py` — query by token_hash + hash_token(token) in 3 places
- [x] `backend/tests/test_refresh_tokens.py` — `_hash_token` → `hash_token`
- [x] `backend/tests/test_sprint201_cleanup.py` — `_hash_token` → `hash_token`

#### Verification
- [x] `alembic upgrade head` — applied ecda5f408617 cleanly
- [x] `pytest tests/test_email_verification.py tests/test_sprint202_cleanup.py tests/test_email_change.py` — 60 passed
- [x] `pytest tests/test_auth_routes_api.py` — 21 passed
- [x] `pytest -x -q` — 5,579 passed, 1 skipped
- [x] `npm run build` — clean

#### Review
- Verification tokens now stored as SHA-256 hashes, identical to refresh token pattern
- `users.email_verification_token` column removed — was a denormalized sprint 57 artifact never used for lookup
- All existing in-flight verification links invalidated on migration (users must resend — trivial UX cost)
- `hash_token` is now public API; internal `_hash_token` name retired across 3 test files
- **Tests: 5,579 backend + 1,345 frontend. Commit: 2343976**

---

### Security Sprint — Data Transport & Infrastructure Trust Controls — COMPLETE

**Status:** COMPLETE
**Goal:** Harden backend trust boundaries: PostgreSQL TLS enforcement + CIDR-aware proxy trust.

#### Implementation Checklist
- [x] `backend/config.py` — TLS startup guard: production PostgreSQL without `?sslmode=require` (or verify-ca/verify-full) hard-fails at boot
- [x] `backend/database.py` — `init_db()` logs TLS status from `pg_stat_ssl` (active/INACTIVE + warning if inactive)
- [x] `backend/security_middleware.py` — `import ipaddress`; new `is_trusted_proxy(peer_ip, trusted)` helper (exact IP + CIDR); `get_client_ip()` updated to use helper
- [x] `backend/shared/rate_limits.py` — `from security_middleware import is_trusted_proxy`; `_get_client_ip()` updated to use helper
- [x] `backend/tests/test_rate_limit_tiered.py` — `test_proxy_aware_extraction` renamed → `test_proxy_aware_extraction_exact_ip`; 2 new CIDR tests added (`test_proxy_aware_extraction_cidr`, `test_proxy_cidr_not_honored_when_outside_range`)
- [x] `backend/tests/test_transport_hardening.py` — 39 new tests (19 `is_trusted_proxy` + 6 `get_client_ip` middleware + 4 rate-limit CIDR + 10 TLS config guard)

#### Verification
- [x] `pytest tests/test_transport_hardening.py` — 39 passed
- [x] `pytest tests/test_rate_limit_tiered.py` — 38 passed

#### Review
- `is_trusted_proxy()` handles exact IPs, CIDR ranges, and silently skips invalid entries
- `TRUSTED_PROXY_IPS` comment (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) now matches actual implementation
- TLS guard covers `disable`, `prefer`, `allow` (all insecure modes); passes `require`, `verify-ca`, `verify-full`; SQLite + non-production are exempt
- `init_db()` queries `pg_stat_ssl` so ops can see TLS status in startup logs
- Backward compatible: exact-IP deployments continue to work unchanged
- **Tests: 5,618 backend + 1,345 frontend**

---

### Sprint 447 — Stripe Production Cutover

**Status:** PENDING
**Goal:** Complete Stripe Dashboard configuration and cut over to live mode.
**Context:** Sprint 440 E2E smoke test passed (27/27). Phase LX analytics + guardrails committed. All billing code is production-ready.

#### Stripe Dashboard Configuration
- [ ] **Stripe Dashboard:** Confirm `STRIPE_SEAT_PRICE_MONTHLY` is graduated pricing: Tier 1 (qty 1–7) = $80, Tier 2 (qty 8–22) = $70
- [ ] **Customer Portal** (Stripe Dashboard > Settings > Customer Portal): enable payment method updates, invoice viewing, cancellation at period end
- [ ] Verify "Manage Billing" button opens portal from `/settings/billing`
- [ ] Update `tasks/pricing-launch-readiness.md` deployment checklist (env vars + Stripe objects checked off)
- [ ] CEO signs readiness report → mark as GO

#### Production Cutover
- [ ] Create production Stripe products/prices/coupons (`sk_live_` key, same structure as test mode)
- [ ] Set production env vars + deploy with `alembic upgrade head`
- [ ] Smoke test with real card on lowest tier (Solo monthly)
- [ ] Monitor webhook delivery in Stripe Dashboard for 24h

---

### Pending Legal Sign-Off

- [ ] **Terms of Service v2.0** — legal owner sign-off with new effective date
- [ ] **Privacy Policy v2.0** — legal owner sign-off with new effective date

---

### Sprint 445 — Test Coverage Analysis

**Status:** COMPLETE
**Goal:** Produce a full coverage gap report for backend and frontend, identify the highest-priority uncovered modules, and produce an action list ranked by risk.

#### Backend
- [x] Run `pytest --cov=backend --cov-report=term-missing --cov-report=json` and capture summary
- [x] Identify modules with <60% line coverage
- [x] Flag untested route handlers and shared utilities
- [x] Note which gaps correspond to billing, soft-delete, or immutability logic (highest risk)

#### Frontend
- [x] Run `npm test -- --coverage --watchAll=false` and capture summary
- [x] Identify components/hooks with <50% statement coverage
- [x] Flag uncovered edge-case branches (error states, empty states, tier-gated paths)
- [x] Note hooks with no test file at all

#### Deliverable
- [x] Produce `tasks/coverage-gap-report.md` listing top 10 backend gaps + top 10 frontend gaps, each with a suggested test type and priority (P1/P2/P3)
- [x] Deferred phase added: "Phase LXII — Export & Billing Test Coverage" in Deferred table below

#### Verification
- [x] `npm run build` passes
- [x] `pytest` passes (5,444 passed, 1 skipped — no regressions)
- [x] `tasks/coverage-gap-report.md` committed

#### Review
- Backend: 92.8% statements overall; top gaps are export routes (17-19%), billing routes (35%), and secrets_manager (33%)
- Frontend: 42.9% statements overall; top gaps are useStatementBuilder (0%, 169 stmts) and FlaggedEntriesTable (0%, 101 stmts)
- Fixed 1 pre-existing test failure: CreateClientModal min-length test (userEvent → fireEvent, React 19 compat)

---

### Sprint 446 — Review Usage Metrics

**Status:** COMPLETE (partial — live Sentry/Stripe data requires dashboard access)
**Goal:** Audit all observable signals (Prometheus, Sentry, Stripe, backend logs) and produce a prioritized action list for performance, reliability, and product improvements.

#### Prometheus / Backend Observability
- [x] Verified all 8 metrics defined in `shared/parser_metrics.py` — all wired, no dead counters
- [x] Reviewed `backend/guards/parser_alerts.toml` — thresholds appropriate; ODS at 15% flagged for rollout review
- [x] Confirmed no dead-code metrics (static analysis)
- [x] Request-ID correlation confirmed in `logging_config.py` + `middleware/request_id.py`

#### Sentry APM
- [x] Zero-Storage compliance confirmed in code (log_sanitizer allow-list reviewed)
- [x] `test_sentry_integration.py` at 94% — 2 uncovered lines in Sentry `before_send` callback (low risk)
- [ ] **PENDING:** Review top 5 errors in live Sentry dashboard (requires dashboard access)
- [ ] **PENDING:** P95 response time outliers (requires dashboard access)

#### Stripe Billing Analytics
- [x] `BillingEvent` model verified append-only, all 10 event types covered
- [x] Alembic migration `b590bb0555c3` confirmed
- [x] `billing/webhook_handler.py` at 85.2% — edge case paths untested (P2 gap)
- [ ] **PENDING:** MRR/tier breakdown (requires Stripe Dashboard access)
- [ ] **PENDING:** Trial conversion rate, webhook delivery rate (requires Stripe Dashboard access)

#### Deliverable
- [x] Produced `tasks/usage-metrics-review.md` with local signal snapshot, 3 reliability risks, 3 product signals, ranked action list
- [x] No P0 risks found from local analysis

#### Verification
- [x] `npm run build` passes
- [x] `tasks/usage-metrics-review.md` committed

---

### Operational Governance Pack v1.0 — Final Step

- [x] `npm run build` passes — VERIFIED 2026-02-26 (Sprint 445 verification run)

---

## Phase LXIII — Entitlement Enforcement Wiring — COMPLETE

### Sprint LXIII-1 — Backend: diagnostic limit pre-flight on TB endpoint — COMPLETE

**Status:** COMPLETE
**Files:** `backend/routes/audit.py`, `backend/tests/test_audit_api.py`

- [x] Add `from shared.entitlement_checks import check_diagnostic_limit` import
- [x] Replace `current_user: User = Depends(require_verified_user)` with `current_user: User = Depends(check_diagnostic_limit)` + `_verified: User = Depends(require_verified_user)` (email verification preserved)
- [x] Remove inline no-op `enforce_tool_access(current_user, "trial_balance")` call
- [x] Update `override_auth` fixture to also override `require_current_user`
- [x] Add `TestDiagnosticLimitEnforcement` class: 4 new tests (FREE@10→403, FREE@9→200, SOLO@20→403, TEAM@100→200)
- [x] `pytest tests/test_audit_api.py -v` — 8/8 passed
- [x] Full `pytest` — 5,561 passed, 1 skipped

### Sprint LXIII-2 — Frontend: UpgradeGate wiring on 6 team-only tool pages — COMPLETE

**Status:** COMPLETE
**Files:** `frontend/src/components/shared/index.ts`, 6 tool pages

- [x] Add `export { UpgradeGate } from './UpgradeGate'` to `shared/index.ts`
- [x] `app/tools/ar-aging/page.tsx` — wrapped with `<UpgradeGate toolName="ar_aging">`
- [x] `app/tools/fixed-assets/page.tsx` — wrapped with `<UpgradeGate toolName="fixed_asset_testing">`
- [x] `app/tools/inventory-testing/page.tsx` — wrapped with `<UpgradeGate toolName="inventory_testing">`
- [x] `app/tools/three-way-match/page.tsx` — wrapped with `<UpgradeGate toolName="three_way_match">`
- [x] `app/tools/statistical-sampling/page.tsx` — wrapped with `<UpgradeGate toolName="sampling">`
- [x] `app/tools/payroll-testing/page.tsx` — wrapped with `<UpgradeGate toolName="payroll_testing">`
- [x] `npm run build` — 0 errors, all 39 routes compiled

#### Review
- Backend gap closed: FREE (10/mo) + SOLO (20/mo) monthly caps now enforced on TB audit run endpoint
- Frontend gap closed: FREE/SOLO users see upgrade prompt immediately on 6 team-only tool pages instead of submitting and receiving a 403
- Pre-existing `override_auth` fixture updated to also override `require_current_user` (required after adding `check_diagnostic_limit` dep which internally uses `require_current_user`)
- Commit: 58775c7 (entitlement wiring), 3dbbaed (UpgradeGate test fixes)

---

## Phase LXIV — HttpOnly Cookie Session Hardening — COMPLETE

**Status:** COMPLETE
**Goal:** Eliminate XSS-readable token storage. Move refresh tokens to HttpOnly server-set cookies; move access tokens to in-memory React `useRef` only. Preserve "Remember Me" via cookie `max_age`. Harden CSRF by removing `/auth/logout` from the exempt list.

**Files:** `backend/config.py`, `backend/auth.py`, `backend/routes/auth_routes.py`, `backend/security_middleware.py`, `frontend/src/types/auth.ts`, `frontend/src/contexts/AuthContext.tsx`, `backend/tests/test_auth_routes_api.py`, `backend/tests/test_csrf_middleware.py`, `backend/tests/test_refresh_tokens.py`

- [x] `backend/config.py` — add `COOKIE_SECURE = ENV_MODE == "production"` and `REFRESH_COOKIE_NAME = "paciolus_refresh"`
- [x] `backend/auth.py` — remove `refresh_token` from `AuthResponse`; add `remember_me: bool = False` to `UserLogin`; delete `RefreshRequest` and `LogoutRequest` classes
- [x] `backend/routes/auth_routes.py` — add `_set_refresh_cookie` / `_clear_refresh_cookie` helpers; rewrite login/register/refresh/logout to set/read/clear cookie; inject `response: Response` param
- [x] `backend/security_middleware.py` — remove `/auth/logout` from `CSRF_EXEMPT_PATHS`; update policy comment
- [x] `frontend/src/types/auth.ts` — remove `refresh_token` from `AuthResponse`; add `remember_me?: boolean` to `LoginCredentials`
- [x] `frontend/src/contexts/AuthContext.tsx` — remove all storage-based token handling; add `tokenRef = useRef<string | null>(null)`; rewrite refresh/login/register/logout to cookie-native flows with `credentials: 'include'`
- [x] `backend/tests/test_auth_routes_api.py` — remove `refresh_token` body assertions; add cookie set/clear assertions
- [x] `backend/tests/test_csrf_middleware.py` — update 4 test cases for new CSRF policy (logout no longer exempt)
- [x] `backend/tests/test_refresh_tokens.py` — remove `RefreshRequest`/`LogoutRequest` imports; update `AuthResponse` schema test
- [x] `pytest` — 5,557 passed, 0 failed (4 CSRF test cases fixed before final run)
- [x] `npm run build` — 0 errors

#### Review
- `refresh_token` removed from JSON response body — no longer JS-readable
- `paciolus_refresh` HttpOnly cookie: `secure=True` in production, `samesite="lax"`, `path="/auth"` scoped
- `remember_me: true` → `max_age=7*24*3600`; `false` → session cookie (`max_age=None`)
- Known simplification: rotation always issues a session cookie (not re-propagating original `remember_me` max_age — acceptable security posture)
- `TOKEN_KEY`, `REFRESH_TOKEN_KEY`, `REMEMBER_ME_KEY` constants deleted from AuthContext; `localStorage.*` and `sessionStorage.*` token writes eliminated
- `USER_KEY` (non-sensitive user metadata) retained in sessionStorage for UI hydration
- Zero-Storage compliance strengthened: no financial data ever touched; token XSS attack surface eliminated
- Commit: 7ed278f

---

## Phase LXV — CSP Tightening & XSS Surface Reduction — COMPLETE

**Status:** COMPLETE
**Goal:** Move to high-assurance CSP. Remove `unsafe-eval` entirely. Replace `unsafe-inline` in `script-src` with per-request nonce (Next.js App Router nonce infrastructure). Keep `unsafe-inline` in `style-src` (required for React inline style props — not removable without full inline-style refactor). Add missing `frame-src 'none'` and `object-src 'none'` directives.

**Agents:** guardian (CSP audit), executor (implementation), critic (regression risk)

**Files:**
- `frontend/src/middleware.ts` (NEW — per-request nonce generation + dynamic CSP)
- `frontend/next.config.js` (remove static CSP header; keep other security headers)
- `docs/04-compliance/SECURITY_POLICY.md` (update CSP documentation)

### Sprint LXV-1 — Nonce Infrastructure + CSP Enforcement — COMPLETE

- [x] Create `frontend/src/proxy.ts` — crypto nonce per request via `crypto.randomUUID()` → base64; `script-src 'self' 'nonce-{n}'` (no unsafe-eval in prod, unsafe-eval kept in dev for webpack HMR); `frame-src 'none'`; `object-src 'none'`; `x-nonce` forwarded on request headers for Next.js RSC streaming script auto-nonce
- [x] `middleware.ts` naming: Next.js 16 deprecated `middleware.ts` in favour of `proxy.ts` (`export function proxy`) — file created as `proxy.ts` with correct convention; deprecation warning eliminated
- [x] Remove static `Content-Security-Policy` header from `frontend/next.config.js` (now owned by `proxy.ts`)
- [x] Update `docs/04-compliance/SECURITY_POLICY.md` — new CSP directive table with nonce explanation and style-src limitation documented
- [x] `npm run build` — 0 errors, 39/39 routes, `ƒ Proxy (Middleware)` listed

#### Acceptance Criteria — MET
- ✅ Enforced CSP without `unsafe-eval` in production `script-src`
- ✅ Enforced CSP without global `unsafe-inline` in `script-src` (nonce present → `unsafe-inline` ignored by CSP3 browsers)
- ✅ `style-src 'unsafe-inline'` retained (necessary; documented as known limitation)
- ✅ `frame-src 'none'` and `object-src 'none'` added (previously missing)
- ✅ No regressions — build clean, CSP is frontend-only change

#### Review
- CSP was a static string in `next.config.js headers()` — nonces require dynamic generation, so moved to `proxy.ts`
- `script-src 'unsafe-eval'` removed from production CSP; webpack dev server retains it via `isDev` guard
- `script-src 'unsafe-inline'` eliminated from production CSP; CSP3-compliant browsers (Chrome 61+, Firefox 55+, Edge 79+, Safari 15.4+) ignore `unsafe-inline` when a nonce is present per the CSP Level 3 spec
- `style-src 'unsafe-inline'` documented limitation: React `style` prop → HTML `style=""` attributes cannot be nonce-tagged; removing requires full elimination of dynamic inline styles across ~100+ components — out of scope
- Next.js 16 proxy convention: `proxy.ts` + `export function proxy(...)` replaces deprecated `middleware.ts`
- Next.js reads `x-nonce` request header automatically and applies it to RSC streaming inline scripts
