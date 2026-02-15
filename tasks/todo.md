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

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi)

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
| Multi-Currency Conversion | Detection shipped; conversion logic needs RFC | Phase VII |
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
| Frontend test coverage (30%+) | 33 files tested (11.4%); next step ~30% needs more component tests | Phase XXXI |

---

## Active Phase

### Phase XXXII: Backend Test Suite Hardening (Sprints 241–248)

> **Focus:** Financial edge case tests, route-level integration tests, CSRF fixture hygiene, test file organization
> **Source:** Comprehensive 4-agent test suite analysis (2026-02-14) — 2,977 tests audited
> **Strategy:** Edge cases first (highest ROI), then route tests, then fixture/org cleanup
> **Council Decision:** Path C — full scope (edge cases + route tests + CSRF refactor + file splitting)

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 241 | Financial Calculation Edge Cases | 3/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 242 | Route Tests: Settings + Activity + Dashboard | 4/10 | BackendCritic | PENDING |
| 243 | Route Tests: Diagnostics + Trends + Clients | 4/10 | BackendCritic | PENDING |
| 244 | Route Tests: Audit + Contact + Health | 3/10 | BackendCritic | PENDING |
| 245 | CSRF Fixture Refactor (autouse removal) | 4/10 | QualityGuardian | PENDING |
| 246 | Test File Splitting: JE + Audit Engine | 3/10 | QualityGuardian | PENDING |
| 247 | Test File Splitting: Ratio + AP + Payroll + TOC Comments | 3/10 | QualityGuardian | PENDING |
| 248 | Phase XXXII Wrap — Regression + Documentation | 2/10 | QualityGuardian | PENDING |

---

### Sprint 241: Financial Calculation Edge Cases

**Goal:** Add ~15 targeted edge case tests to existing engine test files, covering gaps identified by AccountingExpertAuditor and BackendCritic.

#### Ratio Engine (`test_ratio_engine.py`)
- [ ] Extreme D/E ratio: 1T liabilities / $1 equity — verify `health_status == "concern"`, no overflow
- [ ] Ratio denominator near-epsilon: `current_liabilities = 1e-10` — should trigger NEAR_ZERO guard or cap display
- [ ] Operating margin: verify behavior when derived opex is negative (COGS > total_expenses in malformed TB)
- [ ] Both numerator and denominator zero (current ratio) — verify returns N/A gracefully

#### Benford Analysis (`test_benford.py`)
- [ ] All-same-digit dataset: 600 entries all digit-5 — verify `conformity_level == "nonconforming"`, `mad > 0.9`
- [ ] Magnitude range boundary: `magnitude_range = 1.999` (just below 2.0 threshold) — verify precheck behavior

#### Anomaly Detection (`test_audit_engine.py`)
- [ ] Zero net balance after offsetting: 10000 debit / 10000 credit on asset — should NOT be flagged abnormal
- [ ] Concentration risk zero divisor: all accounts have $0 balance — verify no division by zero
- [ ] Multiple anomaly merge: account triggers suspense + concentration + abnormal — verify all flags set

#### Materiality & Variance
- [ ] Materiality threshold exactly-at-boundary: amount == threshold — verify `>=` behavior (ISA 320 inclusive)
- [ ] Negative materiality threshold: -1000 — verify raises error or treats as 0
- [ ] Variance engine inf output: prior = 0.005 (exactly NEAR_ZERO), current = 1,000,000 — verify returns None, not inf
- [ ] Variance engine with prior = -0.00001 (negative small) — verify safe handling

#### Verification
- [ ] `pytest tests/test_ratio_engine.py tests/test_benford.py tests/test_audit_engine.py -v` — all pass
- [ ] No regressions in full `pytest` suite

---

### Sprint 242: Route Tests — Settings + Activity + Dashboard Stats

**Goal:** Add AsyncClient integration tests for `settings.py` (6 endpoints) and `activity.py` (4 endpoints) using proven `httpx.AsyncClient(transport=ASGITransport)` pattern.

**Pattern:** Follow `test_benchmark_api.py` — `httpx.AsyncClient` + `ASGITransport(app=app)` + `override_auth` fixture.

#### `test_settings_api.py` (NEW)
- [ ] GET `/settings/practice` — returns practice settings for authenticated user
- [ ] PUT `/settings/practice` — updates materiality formula, verify persistence
- [ ] GET `/clients/{id}/settings` — returns client-specific settings
- [ ] PUT `/clients/{id}/settings` — client override saves correctly
- [ ] POST `/settings/materiality/preview` — calculation preview returns expected values
- [ ] GET `/settings/materiality/resolve` — cascade resolution: session > client > practice
- [ ] 401 on missing auth token (all endpoints)
- [ ] 404 on non-existent client_id

#### `test_activity_api.py` (NEW)
- [ ] POST `/activity/log` — creates activity record
- [ ] GET `/activity/history` — pagination works (page + per_page params)
- [ ] DELETE `/activity/clear` — clears all activity for user
- [ ] GET `/dashboard/stats` — verify aggregation (total_clients, assessments_today, total_assessments)
- [ ] GET `/dashboard/stats` with no activity — verify zero counts, null last_assessment_date
- [ ] 401 on missing auth token (all endpoints)

#### Verification
- [ ] `pytest tests/test_settings_api.py tests/test_activity_api.py -v` — all pass
- [ ] No regressions in full `pytest` suite

---

### Sprint 243: Route Tests — Diagnostics + Trends + Clients

**Goal:** Add AsyncClient integration tests for `diagnostics.py` (3 endpoints), `trends.py` (3 endpoints), and `clients.py` (5 untested endpoints).

#### `test_diagnostics_api.py` (NEW)
- [ ] POST `/diagnostics/summary` — saves diagnostic summary with flat JSON (model_validator)
- [ ] GET `/diagnostics/summary/{id}/previous` — retrieves most recent summary
- [ ] GET `/diagnostics/summary/{id}/history` — pagination of historical summaries
- [ ] 401 on missing auth, 404 on non-existent client

#### `test_trends_api.py` (NEW)
- [ ] GET `/clients/{id}/trends` — returns trend analysis with sufficient diagnostic data
- [ ] GET `/clients/{id}/trends` with <2 periods — verify 422 error
- [ ] GET `/clients/{id}/industry-ratios` — returns industry comparison
- [ ] GET `/clients/{id}/industry-ratios` with no diagnostic summary — verify 422
- [ ] GET `/clients/{id}/rolling-analysis` — returns rolling window data
- [ ] 401 on missing auth, 404 on non-existent client

#### `test_clients_api.py` (NEW)
- [ ] GET `/clients` — pagination + search query
- [ ] POST `/clients` — create client, verify 201
- [ ] GET `/clients/{id}` — retrieve single client
- [ ] PUT `/clients/{id}` — update client name/industry
- [ ] DELETE `/clients/{id}` — delete client, verify 204
- [ ] Cross-user access prevention: User A cannot access User B's client (404)
- [ ] 401 on missing auth

#### Verification
- [ ] `pytest tests/test_diagnostics_api.py tests/test_trends_api.py tests/test_clients_api.py -v` — all pass
- [ ] No regressions in full `pytest` suite

---

### Sprint 244: Route Tests — Audit + Contact + Health

**Goal:** Add AsyncClient integration tests for remaining untested routes.

#### `test_audit_api.py` (NEW)
- [ ] POST `/audit/trial-balance` — file upload with valid CSV, verify 200
- [ ] POST `/audit/trial-balance` — empty file upload, verify 422
- [ ] POST `/audit/trial-balance` — file exceeding column/row limits, verify 422
- [ ] POST `/audit/flux` — flux analysis with valid data
- [ ] POST `/audit/classification-check` — classification validator returns results
- [ ] 401 on missing auth (all endpoints require `require_verified_user`)

#### `test_contact_api.py` (NEW)
- [ ] POST `/contact/submit` — valid submission returns 200
- [ ] POST `/contact/submit` — honeypot field filled → silent rejection (200 but no email)
- [ ] POST `/contact/submit` — missing required fields → 422

#### `test_health_api.py` (NEW)
- [ ] GET `/health` — returns 200 with status
- [ ] POST `/waitlist` — valid email submission

#### Export Error Paths (add to existing `test_export_helpers.py`)
- [ ] 404 on export with non-existent client_id (sample 3 export endpoints)
- [ ] 401 on export without auth token (sample 3 export endpoints)

#### Verification
- [ ] `pytest tests/test_audit_api.py tests/test_contact_api.py tests/test_health_api.py -v` — all pass
- [ ] No regressions in full `pytest` suite

---

### Sprint 245: CSRF Fixture Refactor

**Goal:** Remove `autouse=True` from CSRF bypass fixture. Make it opt-in so CSRF tests run against real validation.

#### Fixture Changes (`conftest.py`)
- [ ] Rename `_bypass_csrf_in_api_tests` → `bypass_csrf` (remove underscore prefix)
- [ ] Remove `autouse=True` — make opt-in only
- [ ] Keep `scope="session"` for performance (one-time setup per session is fine when explicit)
- [ ] Add clear docstring explaining when to use this fixture

#### Test File Migration
- [ ] Identify all test files that make mutation requests (POST/PUT/DELETE via AsyncClient)
- [ ] Add `@pytest.mark.usefixtures("bypass_csrf")` to each affected test class
- [ ] Verify `test_csrf_middleware.py` passes WITHOUT bypass (remove setup/teardown hacks if present)

#### Auth Override Centralization
- [ ] Add shared `override_auth` fixture to `conftest.py` (function-scoped, opt-in)
- [ ] Document in conftest.py that new API tests should use this fixture
- [ ] Do NOT migrate existing working tests — only use for new test files

#### Verification
- [ ] `pytest tests/test_csrf_middleware.py -v` — all 25 CSRF tests pass without bypass
- [ ] Full `pytest` suite passes — no regressions from fixture scope change
- [ ] Grep confirms no remaining `autouse` on CSRF fixture

---

### Sprint 246: Test File Splitting — JE Testing + Audit Engine

**Goal:** Split the two largest test files into logical sub-files for discoverability.

#### `test_je_testing.py` (2,990 lines → 5 files)
- [ ] `test_je_column_detection.py` — GLColumnDetectionResult tests (~400 lines)
- [ ] `test_je_structural.py` — T1-T5 structural tests (~600 lines)
- [ ] `test_je_statistical.py` — T6-T8 statistical tests (~500 lines)
- [ ] `test_je_advanced.py` — T9-T18 advanced + tier 2/3 tests (~700 lines)
- [ ] `test_je_integration.py` — run_test_battery, composite scoring, stratified sampling (~700 lines)
- [ ] Move shared fixtures (`_make_*` helpers, CSV generators) to `tests/conftest.py` or `tests/je_testing_helpers.py`
- [ ] Delete original `test_je_testing.py`

#### `test_audit_engine.py` (1,917 lines → 3 files)
- [ ] `test_audit_core.py` — StreamingAuditor core processing, balance check, classification (~600 lines)
- [ ] `test_audit_anomalies.py` — suspense, concentration, rounding, abnormal balance detection (~800 lines)
- [ ] `test_audit_multisheet.py` — multi-sheet Excel, vectorized matching, Decimal accumulation (~500 lines)
- [ ] Move shared fixtures to `tests/conftest.py` or `tests/audit_engine_helpers.py`
- [ ] Delete original `test_audit_engine.py`

#### Verification
- [ ] `pytest tests/test_je_*.py tests/test_audit_*.py -v` — all tests pass, same count as before split
- [ ] No duplicate test names across split files
- [ ] Full `pytest` suite passes

---

### Sprint 247: Test File Splitting — Ratio + AP + Payroll + TOC Comments

**Goal:** Split remaining 1,000+ line test files and add TOC comments to all large files.

#### `test_ratio_engine.py` (1,879 lines → 3 files)
- [ ] `test_ratios_liquidity.py` — current ratio, quick ratio, DSO (~600 lines)
- [ ] `test_ratios_profitability.py` — gross margin, net profit, operating margin, ROA, ROE (~700 lines)
- [ ] `test_ratios_integration.py` — rolling windows, momentum, full-engine runs (~500 lines)
- [ ] Move shared fixtures (CategoryTotals factories) to conftest or helpers
- [ ] Delete original `test_ratio_engine.py`

#### `test_ap_testing.py` (1,774 lines → 3 files)
- [ ] `test_ap_structural.py` — T1-T5 structural tests
- [ ] `test_ap_statistical.py` — T6-T8 statistical + fraud indicators
- [ ] `test_ap_integration.py` — run_test_battery, composite scoring
- [ ] Delete original `test_ap_testing.py`

#### `test_payroll_testing.py` (1,467 lines → 3 files)
- [ ] `test_payroll_structural.py` — T1-T4 structural tests
- [ ] `test_payroll_statistical.py` — T5-T8 statistical + ghost employee detection
- [ ] `test_payroll_integration.py` — run_test_battery, composite scoring
- [ ] Delete original `test_payroll_testing.py`

#### TOC Comments
- [ ] Add table-of-contents comment block to any remaining test file >500 lines

#### Verification
- [ ] Full `pytest` suite passes — same test count as before splitting
- [ ] No largest test file exceeds 1,000 lines
- [ ] `pytest --collect-only | wc -l` — verify same test count pre/post split

---

### Sprint 248: Phase XXXII Wrap — Regression + Documentation

- [ ] Full `pytest` suite passes — record final test count
- [ ] `npm run build` passes
- [ ] Verify test count increased (target: ~3,050+ backend tests)
- [ ] Archive sprint details to `tasks/archive/phase-xxxii-details.md`
- [ ] Add one-line summary to `## Completed Phases`
- [ ] Clear `## Active Phase`
- [ ] Update `CLAUDE.md` with Phase XXXII completion + new test count
- [ ] Update `MEMORY.md` project status
- [ ] Commit: `Sprint 248: Phase XXXII wrap — regression verified, documentation archived`
