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

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii)

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
| Dual-key rate limiting | IP-only + lockout adequate for now | Phase XX |
| Wire Alembic into startup | Latency + multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` dir | Model count doesn't justify yet | Phase XXII |
| Cookie-based auth (SSR) | Large blast radius; requires JWT → httpOnly cookie migration | Phase XXVII |
| Marketing pages SSG | Requires cookie auth first | Phase XXVII |
| Frontend test coverage (30%+) | **RESOLVED** — 83 suites, 44% statements, 35% branches, 25% threshold | Phase XXXVII |
| ISA 520 Expectation Documentation Framework | Needs careful guardrail work; deferred to post-Phase XXXIX | Council Review |
| pandas 3.0 upgrade | CoW + string dtype breaking changes; needs dedicated evaluation sprint | Phase XXXVII |
| React 19 upgrade | Major version with breaking changes; needs own phase | Phase XXXVII |

---

## Active Phase

### Phase XXXVIII: Security & Accessibility Hardening + Lightweight Features (Sprints 279–286)
> **Focus:** Fix CVE-adjacent dependencies, close WCAG accessibility gaps, add 2 high-value features reusing existing infrastructure
> **Source:** 4-agent Council audit (BackendCritic, FrontendScout, QualityGuardian, AccountingExpertAuditor) — 2026-02-17
> **Version Target:** 1.6.0

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 279 | Critical Security Fixes | 3/10 | COMPLETE |
| 280 | Backend Code Modernization | 3/10 | COMPLETE |
| 281 | Frontend Accessibility — Modals & Infrastructure | 4/10 | COMPLETE |
| 282 | Frontend Accessibility — Labels, Images & CSP | 4/10 | COMPLETE |
| 283 | Data Quality Pre-Flight Report | 4/10 | PENDING |
| 284 | Account-to-Statement Mapping Trace | 4/10 | COMPLETE |
| 285 | Backend Test Coverage Gaps | 3/10 | PENDING |
| 286 | Phase XXXVIII Wrap + v1.6.0 | 2/10 | PENDING |

---

#### Sprint 279: Critical Security Fixes (3/10) — COMPLETE

- [x] Migrate `passlib` → raw `bcrypt` in `auth.py` (drop `passlib` dependency entirely)
- [x] Bump `python-multipart` 0.0.6 → 0.0.22 (CVE-2024-53498 ReDoS fix)
- [x] Fix X-Forwarded-For proxy trust: add `TRUSTED_PROXY_IPS` env var to `config.py`, custom `key_func` for slowapi that only trusts `X-Forwarded-For` from known proxies
- [x] Add `max_length=200` to `UserProfileUpdate.name`, `max_length=254` to email field
- [x] Hardcode `JWT_ALGORITHM = "HS256"` in `config.py` (remove operator configurability)
- [x] Bump `uvicorn` 0.40.0 → 0.41.0, `sendgrid` 6.11.0 → 6.12.5
- [x] Fix `datetime.utcnow()` in `test_tool_sessions.py:209`
- [x] Remove stale `sanitize_existing_sessions` full-table scan from `main.py` startup
- [x] All tests pass (3,396 backend)

**Review:** All 8 security items addressed. passlib fully removed (raw bcrypt 4.x), python-multipart CVE patched, X-Forwarded-For now only trusted from configured proxies, JWT algorithm no longer operator-configurable, stale startup scan eliminated. Test suite updated — bcrypt tests rewritten for raw bcrypt API, sanitize wiring test flipped to verify removal.

---

#### Sprint 280: Backend Code Modernization (3/10) — COMPLETE

- [x] Expand `ruff.toml`: add `UP006`, `UP007`, `UP035` (typing modernization) + `I001` (import ordering)
- [x] Auto-fix typing modernization: 587 violations auto-fixed + 28 files manually cleaned (stale `from typing import` lines)
- [x] Remove global `F401` suppression; targeted `# noqa: F401` on `main.py` re-export. `F841` kept global (test fixtures)
- [x] Migrate 12 `backref=` → `back_populates` across `models.py`, `engagement_model.py`, `follow_up_items_model.py`
- [x] Add composite index `ix_diagnostic_summaries_client_user_period(client_id, user_id, period_date)` via Alembic migration
- [x] Fix stray `from typing import Optional` in `auth_routes.py` (auto-cleaned by ruff)
- [x] All tests pass (3,396 backend)

**Review:** Typing modernized across entire backend (~50 files touched). `Optional[X]` → `X | None`, `List[X]` → `list[X]`, `Dict[X]` → `dict[X]`, imports sorted. All 12 implicit `backref=` replaced with explicit `back_populates` — both sides now declare their relationships. Composite index migration added for diagnostic_summaries lookup optimization. Ruff now checks 0 violations.

---

#### Sprint 281: Frontend Accessibility — Modals & Infrastructure (4/10) — COMPLETE

- [x] Install `eslint-plugin-jsx-a11y`, add to `eslint.config.mjs` (recommended rules spread)
- [x] Add `role="dialog"` + `aria-modal="true"` + `aria-labelledby` to 4 modals (CreateClientModal, EditClientModal, CreateEngagementModal, ComparisonSection/SavePeriodModal)
- [x] Implement `useFocusTrap` hook (Tab cycle containment, Escape key dismissal, focus-on-open, restore-on-close)
- [x] Apply `useFocusTrap` to all 5 modals (including ColumnMappingModal which already had dialog roles)
- [x] Add `error.tsx` for `(auth)`, `(diagnostic)`, `(marketing)` route groups
- [x] Delete `ThemeTest.tsx` + `app/theme-test/page.tsx` (dead code removed)
- [x] `npm run build` passes, `npm test` 918 tests pass

**Review:** All 5 modals now have WCAG-compliant `role="dialog"` + `aria-modal="true"` + `aria-labelledby` pointing to heading ids. New `useFocusTrap` hook provides Tab/Shift+Tab cycling, Escape dismissal, auto-focus on open, and focus restoration on close. 3 route group error boundaries added. eslint-plugin-jsx-a11y enforces a11y rules going forward. ThemeTest dead code deleted.

---

#### Sprint 282: Frontend Accessibility — Labels, Images & CSP (4/10) — COMPLETE

- [x] Link ~65 `<label>` elements to `<input>` via `htmlFor`/`id` pairing across all form components
  - 19 files: practice/page, profile/page, CreateEngagementModal, AdjustmentEntryForm, SamplingDesignPanel, SamplingEvaluationPanel, ComparisonSection, multi-period/page, FollowUpItemsTable, WorkpaperIndex, SamplingPanel (JE), WeightedMaterialityEditor, TestingConfigSection, flux/page, MaterialityControl, PeriodFileDropZone, FileDropZone, login/page (already had htmlFor), register/page (already had htmlFor)
- [x] Replace 10 raw `<img>` tags with `next/image <Image>` component across 9 files
  - `ToolNav.tsx` (2, with `priority` flag — LCP element), `MarketingNav.tsx`, `MarketingFooter.tsx`, `ProfileDropdown.tsx`, `settings/page.tsx`, `settings/practice/page.tsx`, `settings/profile/page.tsx`, `portfolio/page.tsx`, `engagements/page.tsx`
- [x] Add `aria-live="polite"` regions on tool page loading states (12/12 now covered)
  - 10 tools already had aria-live; added to multi-period compare button + SamplingDesignPanel + SamplingEvaluationPanel
- [x] Add `aria-label` to `CurrencyRatePanel.tsx` drop zone
- [x] Add CSP headers to Next.js via `next.config.js` `headers()` function
  - CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- [x] Remove `unsafe-inline` from backend CSP `script-src` in `security_middleware.py` (API serves JSON, not HTML)
- [x] `npm run build` passes, `npm test` 918 tests pass

**Review:** 19 files updated with htmlFor/id label accessibility pairing. All 10 raw `<img>` tags migrated to next/image `<Image>` with proper width/height (370x510 actual logo dimensions), ToolNav gets `priority` flag for LCP. All 12 tool pages now have aria-live coverage. CurrencyRatePanel drop zone has descriptive aria-label. Frontend CSP headers added via next.config.js headers(). Backend CSP script-src no longer allows unsafe-inline (API-only, no HTML served).

---

#### Sprint 283: Data Quality Pre-Flight Report (4/10) — COMPLETE

> **Source:** AccountingExpertAuditor Recommendation E — highest leverage, reuses existing `column_detector.py` module

- [x] New endpoint: `POST /audit/preflight` — structured data quality assessment before full TB diagnostic
- [x] `PreFlightReport` dataclass in `preflight_engine.py` with 6 checks:
  - Column detection confidence scores per detected column (weight 30%)
  - Null/empty values per column (weight 20%)
  - Duplicate account code entries (weight 15%)
  - Encoding anomalies — non-ASCII in account names (weight 10%)
  - Mixed debit/credit sign conventions within single accounts (weight 15%)
  - Zero-balance rows count (weight 10%)
  - Overall data readiness score (weighted, 0-100: Ready/Review Recommended/Issues Found)
- [x] Pydantic response schema `PreFlightReportResponse` + 5 nested models
- [x] Frontend: `PreFlightSummary` component (score card + column grid + issues list with expandable remediation)
- [x] Frontend: `usePreflight` hook + integration in `useTrialBalanceAudit` (file drop → preflight → proceed → full analysis)
- [x] PDF export: `POST /export/preflight-memo` via `preflight_memo_generator.py`
- [x] CSV export: `POST /export/csv/preflight-issues`
- [x] Export input schemas: `PreFlightMemoInput`, `PreFlightCSVInput`
- [x] Tests: 11 backend (7 engine + 1 serialization + 3 route registration) + 6 frontend component
- [x] Zero-Storage: all computation in-memory during upload request, readiness score in ToolRun metadata

**Review:** All 6 quality checks implemented with weighted readiness scoring. Pre-flight runs automatically on file drop, displays before full TB analysis. User clicks "Proceed to Full Analysis" to continue to the full diagnostic. PDF memo follows memo_base.py pattern with Header/Scope/Column Detection/Issues/Sign-Off/Disclaimer sections. Tests: 3,407 backend + 924 frontend.

---

#### Sprint 284: Account-to-Statement Mapping Trace (4/10)

> **Source:** AccountingExpertAuditor Recommendation F — zero new computation, reuses existing lead_sheet_grouping + financial_statement_builder

- [ ] Extend TB audit response with `mapping_trace` field
- [ ] Generate line-by-line mapping: each financial statement line → contributing TB accounts + balances
  - Reuse existing `group_by_lead_sheet()` output (already computed)
  - Reuse existing `financial_statement_builder` aggregation (already computed)
  - New layer: emit trace document {statement_line: {accounts: [{code, name, net_balance}], total}}
- [ ] PDF section appended to financial statements memo (workpaper-ready tie-out)
- [ ] Excel tab (5th tab) in existing workpaper export structure
- [ ] Frontend: `MappingTraceTable` component in financial statements view (collapsible per statement line)
- [ ] Tests: mapping trace generation (3-5) + frontend component (3-4)
- [ ] Zero-Storage: all data already in-memory during TB audit run

**Files:** `backend/financial_statement_builder.py`, `backend/routes/audit.py`, `backend/routes/export_diagnostics.py`, new frontend component, test files

---

#### Sprint 285: Backend Test Coverage Gaps (3/10)

- [ ] New `test_users_api.py` for `routes/users.py`:
  - `PUT /users/me` profile update (name, email with re-verification flow)
  - `PUT /users/me/password` password change
  - Route registration assertions + schema validation
- [ ] New `test_auth_routes_integration.py` for HTTP-layer auth endpoints:
  - `POST /auth/register` (disposable email blocking, duplicate email)
  - `POST /auth/login` (lockout behavior)
  - `POST /auth/logout` (CSRF header requirement)
  - `GET /auth/csrf` (token format)
  - `GET /auth/verification-status`
- [ ] Narrow `except Exception:` in `routes/audit.py:211` → `(SQLAlchemyError, OperationalError)`
- [ ] Narrow `except Exception:` in `routes/health.py:59` → `(SQLAlchemyError, OperationalError)`
- [ ] All tests pass

**Files:** 2 new test files in `backend/tests/`, `backend/routes/audit.py`, `backend/routes/health.py`

---

#### Sprint 286: Phase XXXVIII Wrap + v1.6.0 (2/10)

- [ ] `pytest tests/ -v` — all pass
- [ ] `npm test` — all pass
- [ ] `npm run build` — zero errors
- [ ] Bump `backend/version.py` to 1.6.0
- [ ] Align `frontend/package.json` version to 1.6.0
- [ ] Update `CLAUDE.md`: add Phase XXXVIII, update test counts, version
- [ ] Update `tasks/todo.md`: archive to `tasks/archive/phase-xxxviii-details.md`
- [ ] Update `MEMORY.md`: project status
- [ ] Add lessons to `tasks/lessons.md` if any corrections occurred

---

### Forward Roadmap

#### Phase XXXIX: Diagnostic Intelligence Features (Sprints 287–291) — PLANNED
> **Focus:** Transform 12 isolated tool outputs into a coherent diagnostic intelligence network
> **Source:** AccountingExpertAuditor gap analysis — Recommendations A, C, D, G
> **Version Target:** 1.7.0

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 287 | TB Population Profile Report | 4/10 | PLANNED |
| 288 | Cross-Tool Account Convergence Index | 5/10 | PLANNED |
| 289 | Expense Category Analytical Procedures | 5/10 | PLANNED |
| 290 | Accrual Completeness Estimator | 4/10 | PLANNED |
| 291 | Phase XXXIX Wrap + v1.7.0 | 2/10 | PLANNED |

**Sprint 287: TB Population Profile Report (4/10)**
- New endpoint: `POST /audit/population-profile`
- Descriptive statistics: count, sum, mean, median, std dev, min, max, 25th/75th percentile
- Magnitude bucket histogram (zero, <1K, 1K-10K, 10K-100K, 100K-1M, >1M)
- Top-10 accounts by absolute net balance
- Gini coefficient for balance concentration measurement
- Frontend: `PopulationProfilePanel` component
- Feeds Statistical Sampling (Tool 12) parameter design
- PDF/CSV export

**Sprint 288: Cross-Tool Account Convergence Index (5/10)**
- Define shared `FlaggedAccount` schema across all 12 tool result formats
- Engagement-level aggregation endpoint: `GET /engagements/{id}/convergence`
- Parse tool output payloads for account references across all tools run in engagement
- Output: `{account, tools_flagging_it[], convergence_count}` sorted descending
- Frontend: `ConvergenceTable` in Engagement Workspace
- CSV export (navigator artifact, not workpaper — no PDF memo)
- **Guardrail:** NO composite score, NO risk classification — raw convergence count only

**Sprint 289: Expense Category Analytical Procedures (5/10)**
- Decompose expense totals by lead sheet category (COGS, operating, payroll, depreciation, interest)
- Current vs prior ratio-to-revenue for each category
- Period-over-period change vs materiality threshold
- Optional industry benchmark comparison (display only, practitioner decides expectation basis)
- PDF section following ISA 520 documentation structure
- CSV export
- **Guardrail:** Raw metrics ONLY — no "unusual" or "requires explanation" labels

**Sprint 290: Accrual Completeness Estimator (4/10)**
- Identify accrued liability accounts via existing keyword classifier
- Compute monthly expense run-rate from prior-period DiagnosticSummary
- Accrual-to-run-rate ratio with configurable threshold (default 50%)
- Single-metric flag card + narrative description
- **Guardrail:** "Balance appears low relative to run-rate" — NEVER "liabilities may be understated"
- PDF section + CSV export

**Sprint 291: Phase XXXIX Wrap + v1.7.0 (2/10)**
- Full regression, version bump, documentation updates

