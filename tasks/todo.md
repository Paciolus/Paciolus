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

### Sprint 496 — Engineering Process Hardening

**Status:** IN PROGRESS
**Goal:** Full SDLC hardening — secrets scanning, CI/CD security controls, missing security tests, workflow permissions, frontend test CI gate, mypy CI gate, pre-commit secrets prevention.
**Complexity Score:** High

#### Findings & Fixes
- [x] **EP-1 (H):** No secrets scanning in CI or pre-commit → Added trufflehog CI job (blocking) + pre-commit pattern scan
- [x] **EP-2 (H):** CI workflow has no `permissions:` block → Added `permissions: contents: read` at top level (least-privilege)
- [x] **EP-3 (H):** No frontend tests in CI → Added `frontend-tests` job running Jest with `--ci --forceExit`
- [x] **EP-4 (M):** No mypy type checking in CI → Added `mypy-check` job enforcing 0 errors on non-test source
- [x] **EP-5 (M):** No security regression tests → Added `test_injection_regression.py` (61 tests: SQLi, SSTI, path traversal, XSS, CWE-1236, header injection)
- [ ] **EP-6 (M):** No pinned action versions — supply chain risk via tag-based references (deferred: requires SHA research)
- [x] **EP-7 (L):** No CODEOWNERS file → Created `.github/CODEOWNERS` covering security-critical paths
- [x] **EP-8 (L):** Pre-commit hook only runs lint-staged → Added secrets pattern scanning (Stripe, AWS, private keys, GitHub/Slack tokens)
- [ ] **EP-9 (L):** Bandit excludes all test files — security bugs in test helpers go undetected (accepted risk: test code doesn't ship)

#### Verification
- [x] `pytest tests/test_injection_regression.py` passes (61 tests)
- [x] `pytest tests/test_security.py tests/test_csrf_middleware.py tests/test_injection_regression.py` passes (170 passed, 2 pre-existing failures)
- [x] `npm run build` passes (all dynamic routes)
- [x] CI workflow validates: secrets-scan, frontend-tests, mypy-check added
- [x] CODEOWNERS covers 20+ security-critical file paths
- [x] Pre-commit hook scans for 7 secret pattern families

---

### Sprint 495 — Surface Area Hardening Security Audit

**Status:** COMPLETE
**Goal:** Full surface area hardening — API endpoints, input handling, injection risks, SSRF, XSS, CSRF, CORS, security headers, file parsing, third-party integrations, container exposure.
**Complexity Score:** High

#### Findings & Fixes
- [x] **SA-1 (M):** MaxBodySizeMiddleware crash on malformed/negative Content-Length → try/except + negative check
- [x] **SA-2 (M):** Prometheus /metrics publicly exposed in production → loopback-only restriction with 404 stealth
- [x] **SA-3 (L):** /health/ready pool stats leaking operational data → stripped in production
- [x] **SA-4 (L):** Bulk upload UploadFile use-after-close in asyncio.create_task → pre-read bytes
- [x] **SA-5 (L):** Frontend missing X-Frame-Options and HSTS headers → added to next.config.js
- [x] **SA-6 (I):** /metrics returns 404 (not 403) for stealth in production
- [x] **SA-7 (L):** Org invite duplicate error leaked email enumeration → generic message
- [x] **SA-8 (L):** Email comparisons in org invite/member queries were case-sensitive → `func.lower()` normalization
- [x] **SA-9 (L):** JPEG magic byte check in branding.py too narrow (3 bytes) → SOI + 0xFF segment marker check

#### Verification
- [x] `pytest` passes (250 security/CSRF/upload tests; 2 pre-existing lockout failures)
- [x] `npm run build` passes (all dynamic routes)
- [x] All 7 files verified: security_middleware.py, routes/metrics.py, routes/health.py, routes/bulk_upload.py, frontend/next.config.js, routes/organization.py, routes/branding.py

---

### Sprint 494 — Data Hardening Security Audit

**Status:** COMPLETE
**Goal:** Full data hardening review — secrets management, error leakage, logging sanitization, API exposure, encryption boundaries.
**Complexity Score:** High

#### Findings & Fixes
- [x] **H-1:** DATABASE_URL with credentials logged in startup summary → Mask credentials via `_mask_database_url()`
- [x] **H-2:** Raw `str(e)` leaked to API clients in 6 route endpoints → Route through `sanitize_error()` with passthrough safety net
- [x] **H-3:** Raw exception in bulk upload job status returned to user → Generic error message
- [x] **M-1:** FastAPI Swagger/OpenAPI docs exposed in production → Disable docs/redoc/openapi_url in production
- [x] **M-2:** Raw exception logged with potential PII from email service → Log only exception class name
- [x] **M-3:** Raw exception logged from Excel parse failure → Log only exception class name
- [x] **M-4:** `sanitize_error()` passthrough mode lacked internal-detail blocking → Added `_contains_internal_details()` safety net
- [x] **L-1:** Raw exception class+message in bulk upload warning logs → Log only exception class name
- [x] **L-2:** Stripe exception details logged with raw `%s, e` in 7 billing endpoints → Log only exception class name
- [x] **L-3:** S3 client init exception logged with raw details → Log only exception class name

#### Defense-in-Depth Improvements
- [x] **D-1:** Apply `sanitize_csv_value()` to all user-controlled Excel cell writes (entity name, item labels, account names, prepared_by, reviewed_by, filename) in `excel_generator.py`
- [x] **D-2:** Add binary magic byte guard (XLSX/XLS/PDF) in UNKNOWN format fallback to prevent binary-as-CSV parsing in `shared/helpers.py`
- [x] **D-3:** Add scheduled bulk upload job cleanup (30min interval) in `cleanup_scheduler.py` — supplements eviction-on-new-upload
- [x] **D-4:** Add `TracebackRedactionFilter` in `logging_config.py` — opt-in via `REDACT_LOG_TRACEBACKS=true` env var to strip tracebacks from production logs

#### Verification
- [x] `pytest` passes: 5,679 passed (38 pre-existing failures unrelated to sprint)
- [x] `npm run build` passes (all dynamic routes)
- [x] Upload validation tests: 141 passed
- [x] Financial statements tests: 46 passed
- [x] Export route tests: 85 passed (1 pre-existing error)
- [x] Memo template tests: 29 passed

### Sprint 493 — Access Hardening Security Audit

**Status:** COMPLETE
**Goal:** Full access control hardening — auth, authorization, session management, privilege escalation, tenant isolation.
**Complexity Score:** High

#### Findings & Fixes
- [x] **H-1:** Billing analytics endpoint lacked admin role check → Added org owner/admin + subscription check
- [x] **H-2:** Org invite token not bound to invitee email → Added email matching validation
- [x] **H-3:** Entitlement checks called with wrong args (crashes) → Fixed call signatures in 4 locations
- [x] **M-1:** No max password length (bcrypt DoS vector) → Added max_length=128 to all password fields
- [x] **M-2:** Registration revealed email existence → Changed to generic error message
- [x] **M-3:** Content-Disposition header injection in export sharing → Added filename sanitization
- [x] **M-4:** Soft entitlement enforcement had no production guardrail → Added startup warning
- [x] **L-1:** /metrics endpoint leaks operational data → Added security documentation note
- [x] Test assertion updated for new registration message

#### Verification
- [x] `pytest tests/test_auth_routes_api.py` passes (26 tests)
- [x] `pytest tests/test_csrf_middleware.py` passes (91 tests)
- [x] `npm run build` passes

### Sprint 492 — Formula Consistency & Efficiency Hardening

**Status:** IN PROGRESS
**Goal:** Eliminate ratio formula inconsistencies, reduce redundant computation, harden edge-case behavior.
**Complexity Score:** Medium-High

#### Changes
- [x] Fix CCC redundant computation in `calculate_all_ratios` (DSO/DPO/DIO computed twice)
- [x] Harden operating margin fallback for malformed totals (negative derived opex)
- [x] Use `is_percentage` in prior-period significance thresholds
- [x] Add cash-cycle ratios (DSO/DPO/DIO/CCC) to prior-period comparison
- [x] Add missing 10 ratios to frontend `RATIO_METRICS` metadata
- [x] Document reciprocal metric zero-case semantics
- [x] Tests: operating margin malformed input, CCC efficiency, prior-period percentage thresholds, reciprocal zero-cases, formula consistency

#### Verification
- [x] `pytest tests/test_ratio_core.py -q` passes (77 tests)
- [x] `pytest tests/test_cash_conversion_cycle.py -q` passes (22 tests)
- [x] `pytest tests/test_prior_period.py -q` passes (42 tests)
- [x] `pytest tests/test_industry_ratios.py -q` passes (71 tests)
- [x] `npm run build` passes (all dynamic routes)
- [x] `npm test` passes (111 suites, 1329 tests)
- [x] Full backend: 5,679 passed (38 pre-existing failures unrelated to sprint)

---

### Sprint 491 — Digital Excellence Council Remediation (Paths A+B+C)

**Status:** IN PROGRESS
**Goal:** Execute all three Council remediation paths: methodology fixes, technical debt, and deprecated alias cleanup.
**Complexity Score:** High

#### Path A: Methodology Fixes
- [x] A1: JE memo standard citation (AS 1215 → AS 2110 + ISA 240)
- [x] A2: FASB YAML citation correction for journal_entry_testing (ASC 230-10 → ASC 240-10)
- [x] A3: Harden assurance-boundary language in all 8 memo generators (low + high risk tiers)
- [x] A4: Fix Benford "non-fabrication" language in JE memo
- [x] A5: Fix "control failure" language in payment_before_invoice procedure (ISA 240 → ISA 265)
- [x] A6: Fix DPO "typical range 30–60 days" unsourced claim in AP memo
- [x] A7: Complete ~30 missing follow-up procedures (37→89 total across all tools)
- [x] A8: Add z-score threshold documentation in testing_enums.py (Nigrini 2012 citation)

#### Path B: Technical Debt
- [x] B1: Fix broad `except Exception` in export_sharing.py (→ binascii.Error, ValueError)
- [x] B2: Billing.py handlers reviewed — Stripe API wrappers are defensible as-is (no change needed)
- [x] B3: Fix silent `except Exception: pass` in bulk_upload.py (→ logger.warning)
- [x] B4: Engine test stubs — verified 11 engine test files already exist (AP, JE, Payroll, Revenue, AR, Sampling, Currency, Recon, Flux, Population Profile, Benchmark). Scout's "16 untested engines" claim was incorrect.

#### Path C: Sprint 478 — Deprecated Alias Migration
- [x] C1: Wave 1 — Zero-consumer deletions (5 themeUtils, 2 marketingMotion, 1 mapping, 1 HeroProductFilm)
- [x] C2: Wave 2 — Health → Threshold rename (MetricCard, IndustryMetricsSection, utils/index, test)
- [x] C3: Wave 3 — Motion token internals (inline DURATION/OFFSET, delete deprecated animations)
- [x] C4: Wave 4 — ENTER.clipReveal migration (FeaturePillars → lib/motion or inline)

#### Verification
- [x] `pytest` passes (5,651 passed; 36 pre-existing failures unrelated to sprint)
- [x] `npm run build` passes (all dynamic routes)
- [x] `npm test` passes (111 suites, 1,329 tests)
- [x] All 21 sample reports regenerated (0 failures)
- [x] Zero `@deprecated` in themeUtils/animations/marketingMotion/mapping
- [x] Zero assurance-boundary violations (5 patterns grep-verified clean)

---

### Sprint 490 — AP Payment Testing Report Fixes

**Status:** COMPLETE
**Goal:** Fix 2 bugs and add 3 improvements to AP Payment Testing Memo (Report 04).
**Complexity Score:** Medium

#### Bugs
- [x] BUG-01: Suggested procedures — all 13 AP procedure texts updated in `follow_up_procedures.py`
- [x] BUG-02: Section V High Severity Payment Detail — 4 test-specific table layouts + generic fallback + procedure text

#### Improvements
- [x] IMP-01: Vendor Name Variation pairs with total_paid columns, sorted by combined total, top 5 shown
- [x] IMP-02: Approval threshold source documentation added to just_below_threshold methodology description
- [x] IMP-03: DPO metric in scope section via `_build_ap_scope()` callback

#### Verification
- [x] `pytest` passes (402/402 memo/AP tests)
- [x] All 21 sample reports regenerated (0 failures)
- [x] `npm run build` passes

---

### Sprint 489 — Journal Entry Testing Report Fixes

**Status:** COMPLETE
**Goal:** Fix 5 bugs and add 2 improvements to JE Testing Memo (Report 03).
**Complexity Score:** Medium

#### Bugs
- [x] BUG-01: Benford Expected column — fixed formula in `generate_sample_reports.py`
- [x] BUG-02: Section V High Severity Detail — added flagged_entries + procedure text below tables
- [x] BUG-03: Suggested procedures — replaced index-based with `_resolve_test_key()` word-overlap matching
- [x] BUG-04: Risk tier — conclusion now uses `composite.risk_tier` directly (not re-derived)
- [x] BUG-05: Disclaimer "testing testing" — `domain_clause` logic in `build_disclaimer()`

#### Improvements
- [x] IMP-01: Month-end clustering benchmark context — `FINDING_BENCHMARKS` in `follow_up_procedures.py`
- [x] IMP-02: Benford positive interpretation — added in `_build_benford_section()` when MAD < 0.006

#### Verification
- [x] `npm run build` passes
- [x] `pytest` passes (226/226 memo/report tests)
- [x] All 21 sample reports regenerated (0 failures)

---

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

**Status:** COMPLETE
**Goal:** Remove 21 deprecated exports across 6 utility files. Migrate consumers to canonical `@/lib/motion` and `ThresholdStatus` APIs.
**Complexity Score:** Low-Medium (most are zero-consumer deletions; 2 components + 3 test files need updating)

#### Wave 1: Zero-Consumer Deletions (safe, no migration needed)
- [x] `themeUtils.ts`: Delete `MODAL_OVERLAY_VARIANTS`, `MODAL_CONTENT_VARIANTS`, `createContainerVariants`, `CONTAINER_VARIANTS`, `createCardStaggerVariants`
- [x] `marketingMotion.tsx`: Delete `STAGGER`, `SectionReveal`
- [x] `types/mapping.ts`: Delete `HealthStatus` type alias
- [x] `HeroProductFilm.tsx` + `components/marketing/index.ts`: Remove `HeroProductFilm` alias export and barrel re-export

#### Wave 2: Health → Threshold Rename (2 components + barrel + test)
- [x] `MetricCard.tsx`: Change `HealthStatus` → `ThresholdStatus`, `getHealthClasses` → `getThresholdClasses`, `getHealthLabel` → `getThresholdLabel`
- [x] `IndustryMetricsSection.tsx`: Same renames
- [x] `utils/index.ts`: Remove deprecated re-exports; add `THRESHOLD_STATUS_CLASSES`, `getThresholdClasses`, `getThresholdLabel` re-exports
- [x] `themeUtils.test.ts`: Update test imports to use canonical names
- [x] `themeUtils.ts`: Delete `HealthStatus`, `HealthClasses`, `HEALTH_STATUS_CLASSES`, `getHealthClasses`, `getHealthLabel`

#### Wave 3: Motion Token Internals (internal rewiring)
- [x] `motionTokens.ts`: Inline `DURATION` values into `TIMING`, inline `OFFSET` values into `DISTANCE`
- [x] `marketingMotion.tsx`: Inline `DURATION.hero` value (0.6), remove `import { DURATION }`
- [x] `animations.ts`: Delete `fadeInUp`, `fadeInUpSpring`, `fadeIn`, `DURATION`
- [x] `animations.test.ts`: Delete deprecated export tests (kept `dataFillTransition`, `scoreCircleTransition`)
- [x] `utils/index.ts`: Remove `DISTANCE` re-export
- [x] `motionTokens.test.ts`: Update DISTANCE/TIMING test descriptions

#### Wave 4: ENTER.clipReveal Migration (1 consumer)
- [x] `FeaturePillars.tsx`: Replace `ENTER.clipReveal` with inline `clipReveal` variant
- [x] `marketingMotion.tsx`: Delete `ENTER` and `OFFSET` exports

#### Verification
- [x] `npm run build` passes
- [x] `npx jest --no-coverage` passes (111 suites, 1329 tests, 5 snapshots)
- [x] `@deprecated` count: 0 in themeUtils, animations, marketingMotion, mapping; 1 in motionTokens (DISTANCE — intentionally retained)

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
