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

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv)

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
| Frontend test coverage (30%+) | 43 files tested (~15%); next step ~30% needs more component tests | Sprint 249 |

---

## Active Phase

### Phase XXXV: In-Memory State Fix + Codebase Hardening (Sprints 261–267)
> **Focus:** Fix production bugs identified in full-stack audit. No new features.
> **Source:** Phase 1 Audit (2026-02-15)

#### Sprint 261: CSRF Stateless HMAC + DB-Backed Account Lockout — COMPLETE
- [x] CSRF: Replace `_csrf_tokens` in-memory dict with stateless HMAC-signed tokens
- [x] Lockout: Add `failed_login_attempts` + `locked_until` columns to User model
- [x] Lockout: Rewrite `record_failed_login`/`check_lockout_status`/`reset_failed_attempts` to use DB
- [x] Auth: Fix account enumeration leak — uniform response shape for existing/non-existing users
- [x] Auth: Add `get_fake_lockout_info()` for non-existent email responses
- [x] Alembic migration for new User columns
- [x] Update test_security.py (45 tests → DB-backed lockout, stateless CSRF, multi-worker simulation)
- [x] Update test_csrf_middleware.py (remove all `_csrf_tokens` dict references)
- [x] Backend tests: 3,141 passed (was 3,129)
- [x] Frontend tests: 520 passed
- [x] Frontend build: passes

#### Sprint 262: Tool Session Data → DB-Backed (ToolSession) — COMPLETE
- [x] Create `tool_session_model.py`: ToolSession SQLAlchemy model with `server_default=func.now()` timestamps
- [x] Upsert: `INSERT ON CONFLICT UPDATE` via `sqlite_insert.on_conflict_do_update()`
- [x] Add `AdjustmentSet.from_dict()` for JSON round-trip deserialization
- [x] Add `CurrencyRateTable.to_storage_dict()`/`from_storage_dict()` for full rate serialization
- [x] Refactor `routes/adjustments.py`: remove `_session_adjustments`/`_session_timestamps` dicts → DB
- [x] Refactor `routes/currency.py`: remove `_rate_sessions`/`_rate_timestamps` dicts → DB
- [x] Update `routes/audit.py`: pass `db` to `get_user_rate_table()`
- [x] Lazy TTL cleanup on read + startup cleanup in `main.py` lifespan
- [x] Update `database.py`, `conftest.py`, `alembic/env.py` for new model
- [x] Alembic migration `679561a74cc1` for `tool_sessions` table
- [x] Rewrite `test_currency_routes.py` for DB-backed sessions (16 tests)
- [x] New `test_tool_sessions.py`: 39 tests (CRUD, upsert, TTL, cleanup, round-trip edge cases)
- [x] Edge cases: empty sets, special chars, zero rates, 100+ items, multi-user isolation
- [x] Backend tests: 3,181 passed (was 3,141)
- [x] Frontend tests: 520 passed
- [x] Frontend build: passes

#### Sprint 263: Float Precision Fixes in audit_engine.py — COMPLETE
- [x] Fix 1: `check_balance()` — `float(debits.sum())` → `math.fsum(debits.values)`
- [x] Fix 2: `StreamingAuditor` — chunk-list accumulation with `math.fsum()` instead of running float addition
- [x] Fix 3: Concentration percentage — keep division in Decimal, convert to float only at serialization
- [x] Fix 4: Rounding detection — Decimal modulo instead of float `%`
- [x] ActivityLog/DiagnosticSummary Float columns — assessed: Float64 sufficient (15-16 sig digits, values < $10T, metadata-only, not used in downstream calcs)
- [x] 21 new precision edge-case tests (trillions, 0.1+0.2 patterns, streaming cross-chunk, concentration, rounding boundaries)
- [x] 2 existing tests updated (`test_running_totals_single_chunk`, `test_clear_releases_memory` → use public API)
- [x] Backend tests: 3,202 passed (was 3,181)

#### Sprint 264: Database Timestamp Defaults — COMPLETE
- [x] Add `func` import to models.py, engagement_model.py, follow_up_items_model.py
- [x] Add `server_default=func.now()` to 14 timestamp columns (User, ActivityLog, Client, DiagnosticSummary, EmailVerificationToken, RefreshToken, Engagement, ToolRun, FollowUpItem, FollowUpItemComment)
- [x] ToolSession already has server_default — skip
- [x] Alembic migration `0f1346198438` (hand-written, batch_alter_table for SQLite compat)
- [x] 24 new tests: 17 DDL inspection + 5 functional DB-insert + 2 UTC verification
- [x] Backend tests: 3,226 passed (was 3,202)
- [x] Frontend build: passes

#### Sprint 265: Dependency Updates — COMPLETE
- [x] sqlalchemy 2.0.25 → 2.0.46 (3,226 passed)
- [x] alembic 1.13.1 → 1.18.4 (3,226 passed)
- [x] slowapi 0.1.9 — already latest, skipped
- [x] reportlab 4.1.0 → 4.4.10 (3,226 passed)
- [x] pydantic 2.5.3 → 2.10.6 (3,226 passed)
- [x] pandas 2.1.4 → 2.2.3 (3,226 passed)
- [x] uvicorn 0.27.0 → 0.40.0 (3,226 passed)
- [x] fastapi 0.109.0 → 0.129.0 (3,226 passed)
- [x] pip-audit + npm-audit added to CI as non-blocking (continue-on-error: true)
- [x] Backend tests: 3,226 passed (zero regressions across all 8 upgrades)
- [x] Frontend build: passes

#### Sprint T1: Foundation Hardening — COMPLETE
- [x] Deep health probe: `GET /health?deep=true` performs `SELECT 1` DB check, returns 503 on failure
- [x] CI enforcement: split pip-audit/npm-audit into advisory (continue-on-error) + blocking (fail on HIGH/CRITICAL)
- [x] Dependabot: `.github/dependabot.yml` for pip + npm + github-actions, weekly schedule, grouped minor/patch
- [x] SAST: Bandit CI job (`bandit -r . -ll --exclude ./tests,./venv`), blocks on HIGH severity + HIGH/MEDIUM confidence
- [x] Config fix: removed duplicate `ENV_MODE` assignment (was at lines 59 and 92, now only line 59)
- [x] 3 new health tests (shallow no-DB field, deep 200 connected, deep 503 unreachable)
- [x] Backend tests: 3,323 passed (was 3,226)
- [x] Frontend build: passes
- [x] Bandit local run: 0 HIGH findings in source code (22 in venv excluded)

#### Sprint 266: Zero-Storage Language Truthfulness — COMPLETE
- [x] Fix approach/page.tsx: "ALL data is immediately destroyed" → qualified with aggregate metadata caveat
- [x] Fix approach/page.tsx: "All data purged from memory" → "Raw financial data purged from memory"
- [x] Fix approach/page.tsx: "Trial balance data" → "Line-level trial balance rows" in weNeverStore
- [x] Fix approach/page.tsx: "RAM only — never written to disk" → "Raw data in RAM only"
- [x] Fix approach/page.tsx: "financial data was never stored" → "line-level financial data was never stored"
- [x] Fix approach/page.tsx: comparison table qualified (RAM-only, breach, retention, deletion rows)
- [x] Fix approach/page.tsx: hero subtitle qualified ("raw financial data")
- [x] Add "Aggregate diagnostic metadata (category totals, ratios, row counts)" to weStore list
- [x] Align with trust/page.tsx pattern (already accurate: "only aggregate metadata is stored")
- [x] Frontend build: passes
- [x] Validated: P1 (zero-storage language), P3 (zip bomb), P4 (rate limits), P6 (CSRF/JWT), P7 (logging), P8 (retention) — all fully addressed
- [x] Validated: P2 (tool sessions DB), P5 (production DB safety) — addressed with minor SQLite batch_alter_table deferred

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

