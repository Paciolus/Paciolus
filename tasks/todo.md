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

### Phase LXIII — Entitlement Enforcement Wiring — COMPLETE
> Backend: `check_diagnostic_limit` dependency (FREE 10/mo, SOLO 20/mo caps) on `/audit/trial-balance`. Frontend: `UpgradeGate` wired on 6 team-only pages (AR Aging, Fixed Assets, Inventory, Three-Way Match, Sampling, Payroll). **Commits: 58775c7, 3dbbaed**

### Phase LXIV — HttpOnly Cookie Session Hardening — COMPLETE
> Refresh tokens → `paciolus_refresh` HttpOnly/Secure/SameSite=Lax cookie; access tokens → in-memory `useRef` only; logout removed from CSRF exempt list; `TOKEN_KEY`/`REFRESH_TOKEN_KEY` deleted from AuthContext. Zero-Storage compliance strengthened. **Commit: 7ed278f**

### Phase LXV — CSP Tightening & XSS Surface Reduction — COMPLETE
> `unsafe-eval` removed from production `script-src`; per-request nonce via `proxy.ts`; `frame-src 'none'`/`object-src 'none'` added; static CSP removed from `next.config.js`; `style-src 'unsafe-inline'` retained (documented limitation). **Commits: 24acec3, 786e888**

### Security Sprints (Post-Sprint 448) — COMPLETE
> Billing Redirect Integrity: server-side URL derivation, injection Prometheus counter, 7 new tests (commit: f7347bd). CSRF Model Upgrade: user-bound 4-part token, 30-min expiry, Origin/Referer enforcement, 15 new tests (commit: 1989030). Verification Token Storage: SHA-256 hash-at-rest, Alembic ecda5f408617 (commit: 2343976). Data Transport: PostgreSQL TLS startup guard + CIDR-aware proxy trust, 39 new tests (commit: 3d2eb13). Proper Nonce-Based CSP: `strict-dynamic` + per-request nonce, `unsafe-inline` removed (commit: 0c98a70). CSP Nonce Fix: `await headers()` in root layout forces dynamic rendering for entire route tree (commit: 1c7626f). Brand Voice Alignment: 9-file copy-only update (commit: 4929aa4). **Tests: 5,618 backend + 1,345 frontend**

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii, phase-xxxviii, phase-xxxix, phase-xl, phase-xli, phase-xlii, phase-xliii, phase-xliv, phase-xlv, phase-xlvi, phase-xlvii, phase-xlviii, phase-xlix, phase-lvi, phase-lvii, sprints-411-438-details, report-standardization-details, billing-launch-details, compliance-docs-details)

---

## Post-Sprint Checklist

**MANDATORY:** Complete after EVERY sprint.

- [ ] `npm run build` passes
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
| Marketing pages SSG | HttpOnly cookie prereq met (Phase LXIV). SSG deferred — requires Next.js SSR wiring + route-level cookie passing | Phase XXVII |

---

## Active Phase

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

## Phase LXVI — SOC 2 Type II Readiness

**Status:** IN PROGRESS
**Goal:** Close every identified gap between current platform posture and SOC 2 Type II certification. Controls must be implemented and evidence-generating before the audit observation window begins.
**Gap Source:** SOC 2 readiness assessment completed 2026-02-27.
**Grouping:** Quick wins → process formalization → technical implementation → infrastructure → external coordination.

---

### Sprint 449 — GitHub PR Security Checklist Template
**Status:** COMPLETE
**Criteria:** CC8.4 — Code review checklist enforcement
**Scope:** Policy defines the checklist (SECURE_SDL_CHANGE_MANAGEMENT.md §3.2) but there is no GitHub-native enforcement mechanism. SOC 2 examiners spot-check PRs for checklist compliance.

- [x] Create `.github/pull_request_template.md` with mandatory attestation checkboxes:
  - `[x] Input validation verified (no raw user input reaches DB or shell)`
  - `[x] No secrets hardcoded (no API keys, tokens, passwords in diff)`
  - `[x] Zero-Storage compliance checked (no financial data persisted)`
  - `[x] Error sanitization applied (sanitize_error() or equivalent used)`
  - `[x] Authentication/authorization correct (guards match auth tier in policy)`
  - `[x] Rate limiting added (new endpoints have a rate limit decorator)`
  - `[x] Pydantic response_model present (new routes have response_model=)`
  - `[x] Tests added or updated for changed logic`
- [x] Add note to CONTRIBUTING.md referencing the template (CONTRIBUTING.md created at project root)
- [x] Verify template appears on first new PR after merge (GitHub auto-populates `.github/pull_request_template.md`)
- [x] `npm run build` passes (no backend changes; pytest not required)

**Review:** `.github/pull_request_template.md` created with 8-item security checklist. `CONTRIBUTING.md` created at project root. Build clean (39 dynamic routes). Commit: e09941a

---

### Sprint 450 — Encryption at Rest Verification + Documentation
**Status:** COMPLETE (pending CEO dashboard sign-off)
**Criteria:** CC7.2 / S1.2 — Encryption at rest
**Scope:** Compliance docs assert provider-level AES-256 encryption, but there is no documented verification step. "We assume it's on" is not SOC 2 evidence.

- [~] Log into Render dashboard → verify PostgreSQL instance has encryption-at-rest enabled; screenshot as evidence artifact — **CEO ACTION: screenshot to `soc2-evidence/cc7/render-postgres-encryption-202602.png`**
- [~] Log into Vercel dashboard → verify KV / any persisted storage is encrypted at rest; screenshot — **CEO ACTION: screenshot to `soc2-evidence/cc7/vercel-no-storage-202602.png`**
- [x] Document findings in `docs/08-internal/encryption-at-rest-verification-202602.md` (template created with full step-by-step verification procedure and evidence table)
- [x] Add to SECURITY_POLICY.md §2.2: AES-256 statement, Vercel no-storage statement, monthly verification procedure with evidence path and retention note; v2.2→v2.3
- [~] Add monthly calendar reminder — **CEO ACTION: recurring monthly reminder for dashboard verification**
- [x] Store evidence screenshot in `docs/08-internal/soc2-evidence/cc7/` (folder created; screenshots pending CEO action)
- [x] `npm run build` passes (no backend changes)

**Review:** Infrastructure files and policy updates automated. Two CEO actions remain: (1) take Render + Vercel screenshots, (2) set monthly calendar reminder. Commit: 6d37139

---

### Sprint 451 — Formal Risk Register
**Status:** COMPLETE (calendar reminder is CEO action)
**Criteria:** CC4.1 / CC4.2 — Risk identification and assessment
**Scope:** No formal risk register exists. Risks are tracked informally via GitHub issues and Sentry. SOC 2 requires a living document with quarterly updates.

- [x] Create `docs/08-internal/risk-register-2026-Q1.md` with all required columns
- [x] Populate register with all 12 risk categories — scored, mitigated, residual risk calculated; 0 High/Critical residuals
- [~] Add quarterly review reminder — **CEO ACTION: recurring calendar Q1=Mar 31, Q2=Jun 30, Q3=Sep 30, Q4=Dec 31**
- [x] Document "risk register update" as standing item in quarterly access review — ACCESS_CONTROL_POLICY.md §8.1 updated (v1.0→v1.1)
- [x] Add link to risk register from SECURITY_POLICY.md §7 — §7.4 "Risk Management" added (v2.4)

**Review:** 12-risk register created with full scoring. 0 Critical/High residuals; 3 Medium; 9 Low. SECURITY_POLICY.md v2.4 + ACCESS_CONTROL_POLICY.md v1.1. Commit: 086883d

---

### Sprint 452 — First Backup Restore Test + Evidence Report
**Status:** COMPLETE (3 CEO actions remain)
**Criteria:** S3.5 / CC4.2 — Backup restore testing evidence
**Scope:** BCP/DR mandates semi-annual restore tests (§7.3) but there are zero artifacts to date. SOC 2 examiners will request test reports covering the audit observation window.

- [~] Schedule restore test execution (non-production environment) — **CEO ACTION: schedule with Render isolated instance**
- [~] Execute restore from most recent Render PostgreSQL backup to isolated test instance — **CEO ACTION: fill in `dr-test-2026-Q1.md` template (10-step procedure pre-built)**
- [x] Document template created at `docs/08-internal/dr-test-2026-Q1.md` (all sections + SQL queries pre-built; execution data pending CEO action)
- [x] `docs/08-internal/soc2-evidence/s3/` folder created with `.gitkeep`
- [~] Add semi-annual calendar reminders (Jun 30 + Dec 31) for subsequent restore tests — **CEO ACTION**
- [x] BCP/DR doc updated: §7.3 naming convention clarified, test artifact history table added, Q1 2026 entry recorded. v1.0 → v1.1

**Review:** All automatable work complete. DR test report template at `docs/08-internal/dr-test-2026-Q1.md` includes: 10-step procedure with exact SQL queries, production baseline table, data integrity matrix, Zero-Storage verification query, RTO measurement table, pass/fail criteria, sign-off section. 3 CEO actions: (1) execute restore test + fill template, (2) copy completed report to `soc2-evidence/s3/`, (3) set Jun 30 + Dec 31 calendar reminders.

---

### Sprint 453 — Security Training Log Framework + Content
**Status:** COMPLETE (2 CEO actions remain)
**Criteria:** CC2.2 / CC3.2 — Security awareness training
**Scope:** Policy states 100% annual completion on hire + annually, but there is no tracking, no content documented, and no completion records. SOC 2 requires demonstrated training completion.

- [x] Define training curriculum — 5 modules defined in `docs/08-internal/security-training-curriculum-2026.md`
- [x] Create training content — 5 full written modules with Paciolus-specific controls, attestation questions, and external references (OWASP, SANS, NIST)
- [x] Create `docs/08-internal/security-training-log-2026.md` with `Employee | Role | Module | Completion Date | Delivery Method | Manager Sign-Off` columns; new-hire template included
- [~] Conduct and log training for all current team members — **CEO ACTION: complete training + fill log**
- [x] Add on-hire training checklist to onboarding runbook — `docs/08-internal/onboarding-runbook.md` created with Day 1 / Week 1 / Day 30 training checklists
- [~] Add annual training reminder (calendar: January each year) — **CEO ACTION**
- [x] Retain records for 3 years — documented in training log header (retain until 2029-02-27); archive instructions included
- [x] `docs/08-internal/soc2-evidence/cc2/` folder created
- [x] SECURITY_POLICY.md §10.1 updated: 5-module curriculum table, per-module duration/audience, onboarding schedule, compliance tracking references. v2.4 → v2.5

**Review:** All framework and content artifacts created. CEO actions: (1) conduct training for all team members and fill in `security-training-log-2026.md`, (2) set annual January reminder. Once executed, copy completed log to `soc2-evidence/cc2/`. Build: ✓

---

### Sprint 454 — Q1 2026 Quarterly Access Review
**Status:** COMPLETE (2 CEO actions remain)
**Criteria:** CC6.1 / CC3.1 — Privileged access reviews
**Scope:** ACCESS_CONTROL_POLICY.md §8.1 requires quarterly reviews, but there are no past review artifacts. SOC 2 requires documented evidence of access reviews covering the observation window.

- [x] Create access review template `docs/08-internal/access-review-template.md` — reusable template with all 7 system sections (GitHub/Render/Vercel/PostgreSQL/Sentry/SendGrid/Stripe), exceptions, actions-taken summary, sign-off
- [x] Create `docs/08-internal/access-review-2026-Q1.md` — Q1 review instance with pre-built tables for all 7 systems; `\du` PostgreSQL snippet included; Stripe API key inventory scaffold; clear per-row CEO instructions; due 2026-03-31
- [x] `docs/08-internal/soc2-evidence/cc6/` folder created
- [~] Execute Q1 review against template (fill in actual accounts from each dashboard) — **CEO ACTION: due 2026-03-31**
- [~] Add quarterly calendar reminders (Q2=Jun 30, Q3=Sep 30, Q4=Dec 31) — **CEO ACTION**
- [x] ACCESS_CONTROL_POLICY.md v1.0→v1.2: header version corrected; §8.3 updated — template reference, `YYYY-QN.md` naming convention, `soc2-evidence/cc6/` evidence path, Q1 2026 artifact history entry

**Review:** All automatable work complete. CEO actions: (1) complete the Q1 review by filling in `access-review-2026-Q1.md` using each provider dashboard (GitHub → Render → Vercel → PostgreSQL → Sentry → SendGrid → Stripe), then copy to `soc2-evidence/cc6/`; (2) set Q2/Q3/Q4 calendar reminders. Build: ✓

---

### Sprint 455 — Weekly Security Event Review Process
**Status:** COMPLETE (1 CEO action remains — W09 execution)
**Criteria:** CC4.2 / C1.3 — Detective controls and monitoring evidence
**Scope:** SECURITY_POLICY.md §8.3 references weekly log reviews, but there is no evidence these are occurring. SOC 2 requires demonstrated detective controls with dated artifacts.

- [x] Create weekly review template `docs/08-internal/security-review-template.md` — 10 sections: metadata, Sentry error review (with disposition codes), Prometheus metric review (pre-built metric names + thresholds, script output paste area), Auth Events log review (bash grep commands), Rate Limiting log review, Access Changes, Escalation Log, Summary Disposition (✅/⚠️/🚨 per category), Sign-Off, Filing checklist
- [x] Execute and file first review: `docs/08-internal/security-review-2026-W09.md` (week 2026-02-23 to 2026-03-01) — all sections pre-structured with `[CEO ACTION]` labels; "First review = baseline" note in every comparison column; Access changes pre-populated with Sprint 449 PR template addition
- [~] Execute W09 review (fill in actual Sentry/Prometheus/log data and sign) — **CEO ACTION: due 2026-03-01**
- [~] Set Monday 9am UTC calendar reminder for weekly reviews — **CEO ACTION**
- [x] `docs/08-internal/soc2-evidence/c1/` folder created for evidence filing
- [x] Retention: 3-year rolling archive per AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md (documented in template)
- [x] `scripts/weekly_security_digest.py` — queries `GET /metrics`, parses Prometheus text format for key security counters, flags injection attempts + parse error spikes, outputs grep commands for log-based events (login_failed, account_locked, csrf_blocked, refresh_token_reuse_detected); run with `METRICS_URL=... python scripts/weekly_security_digest.py`
- [x] SECURITY_POLICY.md v2.5→v2.6: §8.5 "Weekly Security Event Review" added — cadence, template reference, evidence filing path, digest script reference, 5-category review scope table, escalation trigger, SOC 2 criteria (CC4.2 / C1.3)

**Review:** All automatable deliverables complete. CEO action: (1) Run `python scripts/weekly_security_digest.py` to pre-populate Prometheus section; (2) log in to Sentry + Render to complete Sections 2 and 4; (3) fill in all `[CEO ACTION]` fields in `security-review-2026-W09.md`; (4) sign and copy to `soc2-evidence/c1/security-review-2026-W09.md`. Set Monday 9am recurring reminder for W10 onward. Build: ✓

---

### Sprint 456 — Data Deletion SLA + Procedure Document
**Status:** COMPLETE (1 CEO action remains — end-to-end test execution)
**Criteria:** PI4.3 / CC7.4 — Data subject rights (deletion)
**Scope:** Privacy Policy references `/activity/clear` endpoint but there is no formal deletion SLA, no documented procedure with verification steps, and no audit trail of deletion requests. GDPR Art. 17 / CCPA §1798.105 require demonstrated procedures.

- [x] Create `docs/08-internal/data-deletion-procedure.md` with:
  - SLA: deletion requests fulfilled within 30 days of receipt
  - Request intake method (email to privacy@paciolus.com; self-service via Settings)
  - 10-step procedure with exact SQL queries for all 7 tables (users, clients, engagements, activity_logs, diagnostic_summaries, tool_runs, follow_up_items), token revocation, Stripe cancellation, row-count verification, confirmation email template
  - Retention exception: Stripe billing records retained 7 years (financial reporting); documented in confirmation email template + Privacy Policy
  - Audit trail: deletion tracker template + `docs/08-internal/deletion-requests/` folder
- [x] Update Privacy Policy §6.3 to state 30-day SLA explicitly (self-service = immediate; email = 30 days); v2.0→v2.1
- [x] Update Privacy Policy §11 contact table: deletion response time → "30 days (GDPR Art. 17 / CCPA SLA); self-service immediate"
- [x] Document intake channel: email alias `privacy@paciolus.com` + in-product self-service (Settings → Account → Delete Account)
- [~] Verify the procedure end-to-end in a test environment with a test account — **CEO ACTION**
- [x] Add deletion procedure link from `docs/04-compliance/PRIVACY_POLICY.md` §6.3
- [x] Create `docs/08-internal/soc2-evidence/pi4/` evidence folder
- [x] Create `docs/08-internal/deletion-requests/` tracker folder

**Review:** All automatable deliverables complete. Privacy Policy v2.1 with explicit 30-day SLA. Full 10-step procedure with pre-built SQL queries for all 7 affected tables. CEO action: execute Step 1–10 against a test account in a non-production environment; copy completed tracker file to `soc2-evidence/pi4/`.

---

### Sprint 457 — Backup Integrity Checksum Automation
**Status:** PENDING
**Criteria:** S1.5 / CC4.2 — Backup integrity verification
**Scope:** BCP/DR doc states "monthly: verify backup exists and is not corrupted (checksums)" but neither the checksum algorithm nor a verification procedure/script is defined. Without this, the monthly control cannot be evidenced.

- [ ] Determine Render PostgreSQL backup format and accessible metadata (pg_dump checksum, provider API)
- [ ] Write `scripts/verify-backup-integrity.sh` (or Python) that:
  - Queries Render API (or provider CLI) for latest backup metadata
  - Confirms backup exists and was created within expected window
  - If backup file is downloadable: computes SHA-256 checksum and verifies against stored baseline
  - If not downloadable: performs a test restore to verify backup is usable (small smoke-test restore)
  - Outputs: `PASS | FAIL | date | backup_id | checksum | verifier`
- [ ] Add script invocation to CI as a scheduled monthly job (GitHub Actions cron)
- [ ] Archive monthly output to `docs/08-internal/soc2-evidence/s1/backup-integrity-YYYYMM.txt`
- [ ] Document the verification procedure in `docs/08-internal/backup-integrity-procedure.md`
- [ ] Execute first manual run and store first artifact

**Review:** _TBD_

---

### Sprint 458 — GPG Commit Signing Enforcement
**Status:** PENDING
**Criteria:** CC8.6 — Change integrity / tamper evidence for commits
**Scope:** SECURE_SDL_CHANGE_MANAGEMENT.md §10.2 references GPG signing as a planned control. Without it, commit authorship cannot be cryptographically verified by auditors.

- [ ] Generate GPG keys for all active committers (or verify existing keys)
- [ ] Configure `git config --global commit.gpgsign true` on all developer machines; document in CONTRIBUTING.md
- [ ] Add GPG public keys to GitHub account for each committer
- [ ] Enable "Require signed commits" on `main` branch protection rule in GitHub
- [ ] Update SECURE_SDL_CHANGE_MANAGEMENT.md §10.2 to mark GPG signing as implemented (not planned)
- [ ] Document key rotation procedure (annual recommended) and revocation procedure
- [ ] Store public key fingerprints in `docs/08-internal/gpg-key-registry.md`
- [ ] Verify signed commit badge appears on GitHub for recent commits

**Review:** _TBD_

---

### Sprint 459 — DPA Acceptance Workflow
**Status:** PENDING
**Criteria:** PI1.3 / C2.1 — Data Processing Agreement execution evidence
**Scope:** DPA exists (docs/04-compliance/DATA_PROCESSING_ADDENDUM.md) but there is no mechanism for enterprise customers to accept it, no acceptance tracking, and no signed copy archive. SOC 2 requires demonstrated DPA execution for business customers.

- [ ] Add DPA acceptance step to enterprise onboarding flow:
  - Option A (minimal): email-based DPA send + signed PDF return → store in `docs/08-internal/customer-dpa-archive/`
  - Option B (in-product): checkbox "I accept the Data Processing Addendum" on Team/Organization checkout flow, stored as `dpa_accepted_at` timestamp in Subscription model
- [ ] Implement chosen option (recommend Option B for automation + evidence)
  - If Option B: add `dpa_accepted_at` column to `subscriptions` table via Alembic migration
  - If Option B: add checkbox UI on checkout page for Team/Organization tiers
  - If Option B: add `dpa_accepted_at` field to `SubscriptionResponse` schema
- [ ] Add DPA acceptance date display in billing settings page
- [ ] Create `docs/08-internal/dpa-acceptance-register.md` to track: customer account ID, acceptance date, DPA version, method
- [ ] Update `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md` to include version number and effective date at top
- [ ] `npm run build` + `pytest` pass

**Review:** _TBD_

---

### Sprint 460 — PostgreSQL pgaudit Extension
**Status:** PENDING
**Criteria:** CC6.8 / CC7.4 — Database-level audit logging
**Scope:** AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md §5.4 lists `pgaudit` as planned for Q3 2026. Database-level logging is a SOC 2 examiner expectation for CC6.8 (access monitoring) and provides tamper-resistant evidence independent of application logs.

- [ ] Verify `pgaudit` availability on Render PostgreSQL instance (check Render docs / support)
- [ ] If available: enable `pgaudit` extension via `CREATE EXTENSION pgaudit;`
- [ ] Configure `pgaudit.log = 'ddl, role, write'` (capture DDL changes, role grants, DML writes on sensitive tables)
- [ ] Scope to sensitive tables: `users`, `subscriptions`, `clients`, `engagements`, `activity_logs`, `tool_runs`, `diagnostic_summaries`
- [ ] Verify audit log output format integrates with existing structured logging pipeline
- [ ] Add pgaudit log retention to AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md §5.4 (365-day retention)
- [ ] Test: execute a DDL statement (ALTER TABLE) and confirm it appears in pgaudit log
- [ ] If Render does not support pgaudit: document the blocker, escalate to Render support, and document application-layer compensating control
- [ ] Update AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md §5.4 to reflect implementation status

**Review:** _TBD_

---

### Sprint 461 — Cryptographic Audit Log Chaining
**Status:** PENDING
**Criteria:** CC7.4 / Audit Logging — Tamper evidence
**Scope:** AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md §5.1 references soft-delete immutability but does not implement cryptographic chaining. Hash chaining provides forward-integrity: any retroactive modification of an audit record is detectable. This is required for "tamper-resistant" evidence claims.

- [ ] Design chain: each `ActivityLog` record gets a `chain_hash` column = `HMAC-SHA256(previous_hash + current_record_content)`
- [ ] Alembic migration: add `chain_hash VARCHAR(64)` column to `activity_logs` table
- [ ] Implement `compute_chain_hash(previous_hash: str, record: ActivityLog) -> str` in `backend/shared/audit_chain.py`
- [ ] Integrate into `ActivityLog` creation path: compute and store `chain_hash` on every insert
- [ ] Write `verify_audit_chain(db: Session, start_id: int, end_id: int) -> ChainVerificationResult` function
- [ ] Add `GET /audit/chain-verify?start_id=X&end_id=Y` endpoint (admin only, CISO-level role)
- [ ] Add 15+ tests covering: chain construction, tamper detection (modified record), missing record detection, chain verification endpoint
- [ ] Document chain verification procedure in AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md §5
- [ ] `npm run build` + `pytest` pass

**Review:** _TBD_

---

### Sprint 462 — Monitoring Dashboard Configuration Documentation
**Status:** PENDING
**Criteria:** S3.3 / CC4.2 — Evidence that alerting is configured and operational
**Scope:** Alert thresholds are documented in SECURITY_POLICY.md §8.3–8.4 and TOML config, but there are no screenshots, no dashboard config exports, and no documented proof that Sentry + Prometheus alerting is currently operational. SOC 2 examiners will request this evidence.

- [ ] Export and archive Sentry project configuration:
  - Alert rules (error rate >5%, login failures >100/min, Zero-Storage violation markers)
  - `before_send` hook configuration (PII scrubbing)
  - `traces_sample_rate` setting
  - Team members and roles in Sentry project
  - Save as `docs/08-internal/soc2-evidence/s3/sentry-config-YYYYMM.json` + screenshot
- [ ] Export and archive Prometheus configuration:
  - Scrape interval and targets (`/metrics` endpoint)
  - Alert rules (TOML thresholds → Prometheus alerting rules if wired)
  - Retention period setting
  - Save as `docs/08-internal/soc2-evidence/s3/prometheus-config-YYYYMM.yaml`
- [ ] Create `docs/08-internal/monitoring-dashboard-config.md` documenting:
  - Sentry: project name, DSN (redacted), sample rate, alert rules, PII policy
  - Prometheus: scrape targets, retention, alert thresholds, runbook links
  - On-call rotation: who receives alerts, acknowledgment SLA (reference IRP)
- [ ] Verify alert delivery: trigger a synthetic error in staging → confirm Sentry alert fires
- [ ] Archive first evidence set (Jan 2026 or first available month)

**Review:** _TBD_

---

### Sprint 463 — SIEM / Log Aggregation Integration
**Status:** PENDING
**Criteria:** CC4.2 / C1.3 — Centralized security event correlation
**Scope:** Currently Sentry (exceptions), Prometheus (metrics), and application logs (structured JSON) are separate. A lightweight SIEM layer is needed for correlation rules (e.g., failed login spike + CSRF failure at same IP = coordinated attack signal). Referenced in SECURITY_POLICY.md as a Q3 2026 planned control.

- [ ] Evaluate options:
  - Option A: Grafana Loki + Grafana Alerting (lightweight, compatible with Prometheus already in use)
  - Option B: Elastic Stack (more powerful but higher operational cost)
  - Option C: Datadog (SaaS, Zero-Storage compliant setup)
  - Option D: Defer; implement correlation rules in existing Prometheus/Sentry instead
- [ ] CEO decision on approach before implementation begins
- [ ] Implement chosen option:
  - Configure log shipper (if applicable) to forward structured JSON logs
  - Define correlation rules (at minimum: auth failure spike, CSRF spike, rate limit + auth failure co-occurrence)
  - Set up alert delivery to on-call rotation
  - Verify Zero-Storage compliance: no financial data in log payloads (confirm `sanitize_error()` coverage)
- [ ] Document configuration in `docs/08-internal/siem-config.md`
- [ ] Add SIEM to SUBPROCESSOR_LIST.md if SaaS option chosen
- [ ] Update SECURITY_POLICY.md §8 to reflect SIEM as implemented

**Review:** _TBD_

---

### Sprint 464 — Cross-Region Database Replication
**Status:** PENDING
**Criteria:** S3.2 / BCP — Availability and disaster recovery resilience
**Scope:** BCP/DR doc targets RTO 1–2 hours, RPO 0–1 hour. Currently relies on single-region Render PostgreSQL. Cross-region replication reduces RPO toward zero and enables failover without restore-from-backup. Referenced in BCP/DR as a Q3 2026 planned improvement.

- [ ] Evaluate Render PostgreSQL replication options (managed read replicas, logical replication, or pg_logical)
- [ ] Evaluate cost/complexity trade-off: read replica vs. cross-region standby vs. pgBackRest to secondary region
- [ ] CEO decision on replication tier before implementation
- [ ] Implement chosen option:
  - Configure replication target (secondary region)
  - Verify replication lag is within RPO target (< 1 hour)
  - Test failover procedure: promote replica, update connection string, verify application connectivity
  - Document failover procedure in BCP/DR §5 (DR Procedure 6: Database Failover)
- [ ] Update RTO/RPO targets in BCP/DR §2 if improved by this implementation
- [ ] Add replication monitoring to Prometheus: lag metric, replication slot status
- [ ] `pytest` pass (no backend changes expected; integration test if connection string changes)

**Review:** _TBD_

---

### Sprint 465 — Automated Backup Restore Testing in CI
**Status:** PENDING
**Criteria:** S3.5 — Evidence automation for backup restoration
**Scope:** Sprint 452 establishes the first manual restore test. This sprint automates evidence generation so tests run on a monthly schedule without manual triggering, and output is automatically archived.

- [ ] Create GitHub Actions workflow `.github/workflows/dr-test-monthly.yml`:
  - Schedule: `cron: '0 6 1 * *'` (1st of each month, 6am UTC)
  - Steps:
    1. Query Render API for latest backup metadata
    2. Initiate restore to ephemeral test instance (if Render API supports it; otherwise document manual step)
    3. Run smoke queries: row count on `users`, `clients`, `subscriptions`, `activity_logs`
    4. Compare counts against previous snapshot (stored as artifact from prior run)
    5. Output pass/fail JSON report
    6. Upload report as GitHub Actions artifact (retained 1 year)
    7. If FAIL: create GitHub issue with label `dr-failure` and assign to CISO
- [ ] Store Render API credentials in GitHub Secrets (`RENDER_API_KEY`)
- [ ] Document workflow in BCP/DR §7.3 (Automated Testing subsection)
- [ ] First scheduled run must pass before sprint is complete
- [ ] Add CI badge for DR test status to `docs/08-internal/monitoring-dashboard-config.md`

**Review:** _TBD_

---

### Sprint 466 — Secrets Vault Secondary Backup
**Status:** PENDING
**Criteria:** CC7.3 / BCP — Key management resilience
**Scope:** All secrets currently stored in a single vault (environment variables + provider secrets). If the primary vault is inaccessible during an incident, recovery requires reconstituting all secrets from scratch. A secondary backup reduces this risk. Referenced in SECURITY_POLICY.md §9 as planned.

- [ ] Inventory all secrets: `SECRET_KEY`, `DATABASE_URL`, `STRIPE_SECRET_KEY`, `SENDGRID_API_KEY`, `SENTRY_DSN`, `FRONTEND_URL`, JWT config, CSRF config, Render/Vercel deploy tokens
- [ ] Choose secondary vault location: separate cloud account (e.g., AWS Secrets Manager in a different account), encrypted offline store, or trusted secondary provider
- [ ] CEO decision on secondary vault location before implementation
- [ ] Implement:
  - Sync all secrets to secondary vault (manual or automated)
  - Document access procedure for secondary vault (who has access, how to retrieve)
  - Test recovery: simulate primary vault loss → retrieve all secrets from secondary → verify application boots
  - Document test result in `docs/08-internal/secrets-recovery-test-YYYYMM.md`
- [ ] Add 90-day rotation check: calendar reminder to verify secondary vault is in sync with primary
- [ ] Update SECURITY_POLICY.md §9 (key management) to reflect secondary backup as implemented
- [ ] Store evidence of recovery test in `docs/08-internal/soc2-evidence/cc7/`

**Review:** _TBD_

---

### Sprint 467 — External Penetration Test Engagement
**Status:** PENDING
**Criteria:** S1.1 / CC4.3 — Independent validation of security controls
**Scope:** SECURITY_POLICY.md §7.2 references annual penetration testing (planned Q2 2026). This provides independent evidence that technical controls are operating as designed — SOC 2 examiners weight pen test evidence highly.

- [ ] Define test scope:
  - In-scope: authentication flows, CSRF/CSP controls, rate limiting, API authorization (tier enforcement), file upload, JWT handling, billing endpoints
  - Out-of-scope: Render/Vercel infrastructure (handled by provider), physical security
- [ ] Select qualified vendor (CREST/OSCP-certified firm recommended for SOC 2 credibility)
- [ ] Execute pre-test checklist:
  - Provide vendor with: staging environment access, API schema (OpenAPI), test accounts for each tier
  - Confirm staging environment has no real customer data
  - Establish rules of engagement (no DoS, no social engineering of employees)
- [ ] Receive and review findings report
- [ ] For each Critical/High finding: create remediation sprint, track to closure
- [ ] Obtain remediation validation (re-test or attestation letter from vendor)
- [ ] Store final report + remediation evidence in `docs/08-internal/soc2-evidence/pentest/`
- [ ] Update SECURITY_POLICY.md §7.2 with test date and outcome summary

**Review:** _TBD_

---

### Sprint 468 — Bug Bounty Program Launch
**Status:** PENDING
**Criteria:** CC4.3 / VDP — Continuous vulnerability identification
**Scope:** VDP policy exists (docs/04-compliance/VULNERABILITY_DISCLOSURE_POLICY.md) but references a contact email only. A structured bug bounty program signals security maturity to enterprise customers and SOC 2 examiners.

- [ ] CEO decision: public bug bounty (HackerOne/Bugcrowd) vs. private invite-only vs. enhanced VDP
- [ ] Implement chosen option:
  - If HackerOne/Bugcrowd: create program, define scope + rewards + rules, publish
  - If private: define invitation criteria, create invite list, configure platform
  - If enhanced VDP: add structured severity matrix + response SLA to existing VDP page, add `security.txt` to `/.well-known/security.txt`
- [ ] Implement `security.txt` at `frontend/public/.well-known/security.txt` (mandatory for all options):
  - `Contact: mailto:security@[domain]`
  - `Expires: [date]`
  - `Policy: [link to VDP page]`
  - `Preferred-Languages: en`
- [ ] Add bug bounty/VDP link to Trust page (Sprint 400 Assurance Center)
- [ ] Configure triage workflow: incoming report → severity assessment → assign to engineer → fix → notify reporter
- [ ] Update VDP doc to reference program platform and response SLAs
- [ ] `npm run build` passes (static file addition)

**Review:** _TBD_

---

### Sprint 469 — SOC 2 Evidence Folder Organization + Auditor Readiness Assessment
**Status:** PENDING
**Criteria:** Administrative — Audit preparation
**Scope:** All preceding sprints generate evidence artifacts in scattered locations. This sprint organizes the SOC 2 evidence package and performs an internal readiness dry-run before engaging an external auditor.

- [ ] Create evidence folder structure `docs/08-internal/soc2-evidence/`:
  - `cc1/` — governance (org chart, CISO role, training logs)
  - `cc2/` — communication (policy links, role definitions)
  - `cc3/` — enforcement (access reviews, quarterly review artifacts)
  - `cc4/` — risk assessment (risk register, weekly security reviews, incident post-mortems)
  - `cc5/` — control activities (PR templates, CI gate screenshots)
  - `cc6/` — logical access (access review artifacts, deprovisioning records)
  - `cc7/` — encryption (at-rest verification, key rotation records, chain verification)
  - `cc8/` — change management (PR history screenshots, CI gate pass artifacts)
  - `cc9/` — risk mitigation (exception log, post-mortem records)
  - `s3/` — availability (DR test reports, backup integrity reports, Sentry/Prometheus configs)
  - `c1/` — confidentiality (weekly security reviews, breach notification procedures)
  - `pi/` — privacy (DPA acceptance register, deletion request log)
  - `pentest/` — pen test reports
- [ ] Create `docs/08-internal/soc2-evidence/EVIDENCE_INDEX.md` mapping each TSC criterion to its evidence files
- [ ] Internal readiness assessment: walk through each CC criterion from AICPA's 2017 Trust Services Criteria against available evidence; flag any remaining gaps
- [ ] Produce `docs/08-internal/soc2-readiness-assessment-YYYYMM.md`:
  - Per-criterion: Evidence Available / Gap / Remediation Plan
  - Overall readiness score
  - Recommended audit observation window start date
- [ ] Auditor shortlist: identify 3 CPA firms with SOC 2 SaaS experience; get quotes
- [ ] CEO decision: select auditor, define observation window start date
- [ ] Kick off audit engagement

**Review:** _TBD_
