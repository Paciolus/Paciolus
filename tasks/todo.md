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

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii)

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
| Multi-Currency Conversion | **IN PROGRESS — Phase XXXIV** | Phase VII |
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
| Frontend test coverage (30%+) | 43 files tested (~15%); next step ~30% needs more component tests | Sprint 249 |

---

## Active Phase

### Phase XXXIV (Sprints 255–260) — Multi-Currency Conversion
> **Focus:** Deliver Multi-Currency conversion — highest-demand deferred feature + critical security pre-flight
> **Source:** Agent Council assessment (2026-02-15) — Path C selected (Feature Phase First)
> **Strategy:** Pre-flight security fix (python-jose → PyJWT, package rename), then RFC-driven feature delivery
> **Design:** User-provided exchange rates (CSV upload or manual entry), TB-level conversion, Zero-Storage compliant (rate tables ephemeral)
> **Target Version:** 1.3.0
> **Council Tensions Addressed:** #1 python-jose (Sprint 255), #5 package rename (Sprint 255)
> **Council Tensions Deferred:** #2 dependency bumps, #3 PostgreSQL, #4 frontend coverage → Phase XXXVI

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 255 | Security Pre-Flight: python-jose → PyJWT, package.json rename | 3/10 | BackendCritic + QualityGuardian | COMPLETE |
| 256 | Multi-Currency RFC: exchange rate model, IAS 21/ASC 830 scope, rounding rules | 3/10 | AccountingExpertAuditor | COMPLETE |
| 257 | Currency conversion engine: rate lookup, temporal matching, monetary/non-monetary translation | 7/10 | BackendCritic | COMPLETE |
| 258 | API endpoints (rate upload, conversion) + Frontend currency UI | 6/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 259 | Testing suite + memo generator + export integration | 4/10 | QualityGuardian | COMPLETE |
| 260 | Phase XXXIV Wrap — regression, documentation, v1.3.0 | 2/10 | QualityGuardian | PENDING |

#### Sprint 255 Checklist — Security Pre-Flight
- [ ] Replace `python-jose[cryptography]` with `PyJWT[crypto]` in `requirements.txt`
- [ ] Remove `types-python-jose` from `requirements-dev.txt`
- [ ] Update `auth.py`: `from jose import JWTError, jwt` → `import jwt` + `from jwt.exceptions import PyJWTError`
- [ ] Update all `jwt.encode()` / `jwt.decode()` calls (verify parameter name differences: jose uses `algorithms` kwarg, PyJWT uses `algorithms` too but `decode` returns dict directly)
- [ ] Update `tests/test_password_revocation.py`: `from jose import jwt` → `import jwt`
- [ ] Update `tests/test_sprint201_cleanup.py`: 3 occurrences of `from jose import jwt`
- [ ] Rename `"closesignify-frontend"` → `"paciolus-frontend"` in `frontend/package.json`
- [ ] Run full backend test suite (`pytest`)
- [ ] Run frontend build (`npm run build`)

#### Sprint 256 Checklist — Multi-Currency RFC
- [ ] Define exchange rate input model: user-uploaded rate table (CSV: date, from_currency, to_currency, rate)
- [ ] Define manual single-rate entry option (simple same-day conversions)
- [ ] Define functional currency vs presentation currency distinction (IAS 21 / ASC 830)
- [ ] Define scope: TB analysis primary, JE Testing warning enhancement, other tools follow later
- [ ] Define monetary vs non-monetary classification approach (user-driven or rule-based)
- [ ] Define temporal rate vs closing rate application rules
- [ ] Define translation gain/loss (CTA) handling — include or defer to future sprint
- [ ] Define rounding rules for converted amounts
- [ ] Define Zero-Storage compliance: rate tables session-scoped, never persisted
- [ ] Document in `docs/rfc-multi-currency.md`
- [ ] AccountingExpertAuditor review: verify no IAS 21 overreach

#### Sprint 257 Checklist — Conversion Engine
- [ ] Create `backend/currency_engine.py`
- [ ] Exchange rate parser: validate rate table (CSV/Excel), normalize currency codes (ISO 4217)
- [ ] Rate lookup by date + currency pair (exact match → nearest prior date fallback)
- [ ] Single-rate conversion mode (one rate applied uniformly)
- [ ] Multi-rate conversion mode (date-specific rates from table)
- [ ] Convert TB amounts from original currency to functional currency
- [ ] Handle missing rates gracefully (flag unconverted rows, don't fail)
- [ ] Preserve original amounts alongside converted amounts in result
- [ ] Unit tests: single-currency no-op, multi-currency conversion, missing rates, rounding, edge cases
- [ ] Performance: vectorized Pandas — must handle 500K-row TBs

#### Sprint 258 Checklist — API + Frontend
- [ ] Rate table upload endpoint: `POST /audit/currency-rates` (validate, store in session)
- [ ] Manual rate entry endpoint: `POST /audit/currency-rate` (single rate for simple cases)
- [ ] Conversion trigger: integrate into existing TB upload flow (if rates provided, auto-convert)
- [ ] Enhance TB upload response to include currency detection summary
- [ ] Response models (`CurrencyRateResponse`, `ConversionResultResponse`) for all new endpoints
- [ ] Rate limiting: `RATE_LIMIT_AUDIT` on new endpoints
- [ ] Frontend: rate table upload component (CSV drag-and-drop, Oat & Obsidian themed)
- [ ] Frontend: manual rate entry form (from_currency, to_currency, rate, effective_date)
- [ ] Frontend: converted amounts toggle on TB results (original ↔ converted)
- [ ] Frontend: currency-aware number formatting (ISO 4217 symbols)
- [ ] `npm run build` passes

#### Sprint 259 Checklist — Testing + Memo + Export
- [ ] Multi-currency conversion test suite (15+ backend scenarios)
- [ ] Edge cases: zero rates, same-currency no-op, inverse rates, large volumes, missing dates
- [ ] Multi-currency memo generator (document conversion methodology, rates applied, unconverted flags)
- [ ] PDF export with dual-currency columns (original + converted)
- [ ] Excel export with rate table reference sheet
- [ ] CSV export with converted amounts
- [ ] Integration with engagement workspace (ToolRun recorded if engagement active)
- [ ] Workpaper signoff includes conversion parameters used

#### Sprint 260 Checklist — Phase XXXIV Wrap
- [ ] `pytest` full suite passes
- [ ] `npm run build` passes
- [ ] Zero-Storage compliance verified (rate tables ephemeral, no financial data persisted)
- [ ] Update Deferred Items: Multi-Currency → Completed Phases
- [ ] Version bump to 1.3.0 in `backend/version.py`
- [ ] Update CLAUDE.md: add Phase XXXIV to completed list, update version
- [ ] Update MEMORY.md: project status
- [ ] Archive phase details to `tasks/archive/phase-xxxiv-details.md`
- [ ] Lessons learned in `tasks/lessons.md`

---

### Forward Roadmap (Planned)

> High-level outlines. Detailed checklists created when each phase begins.

#### Phase XXXV: Statistical Sampling Module (Tool 12) — PLANNED
> **Focus:** ISA 530 / PCAOB AS 2315 statistical sampling — universal audit requirement
> **Estimated Sprints:** 5–6
> **Scope:**
> - Sample size calculator (confidence level, expected/tolerable misstatement)
> - 4 sampling methods: random, systematic, monetary unit (MUS), stratified
> - Sample selection from uploaded population data
> - Sample evaluation: projected misstatement, upper/lower error bounds
> - Memo generator + export integration
> - Frontend: sampling wizard with method selection and parameter configuration

#### Phase XXXVI: Deployment Hardening — PLANNED
> **Focus:** Address remaining council tensions for production readiness
> **Estimated Sprints:** 4–5
> **Scope:**
> - Selective dependency version bumps (FastAPI, pandas, SQLAlchemy, pydantic, React 18→19 eval)
> - PostgreSQL connection validation + migration guide finalization
> - Frontend test coverage push toward 30% (~30 new test files)
> - APM integration evaluation (Sentry or equivalent)
> - Database backup strategy documentation

