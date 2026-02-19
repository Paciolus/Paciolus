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

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii, phase-xxxiii, phase-xxxiv, phase-xxxv, phase-xxxvi, phase-xxxvii, phase-xxxviii, phase-xxxix, phase-xl)

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
| ISA 520 Expectation Documentation Framework | **RESOLVED** — Delivered in Phase XL Sprint 297 with blank-only guardrail | Council Review (Phase XL) |
| pandas 3.0 upgrade | CoW + string dtype breaking changes; needs dedicated evaluation sprint | Phase XXXVII |
| React 19 upgrade | Major version with breaking changes; needs own phase | Phase XXXVII |

---

## Active Phase

### Sprint 300 — Token/PII Log Sanitization

| # | Task | Status |
|---|------|--------|
| 1 | Create `backend/shared/log_sanitizer.py` — `token_fingerprint`, `mask_email`, `sanitize_exception` | COMPLETE |
| 2 | Migrate `email_service.py` — replace `_token_fingerprint`, `str(e)` ×3, inline email masking ×6 | COMPLETE |
| 3 | Migrate `auth.py` — replace `str(e)` ×1, inline `email[:10]` ×4 | COMPLETE |
| 4 | Migrate `routes/auth_routes.py` — replace inline `email[:10]` ×4 | COMPLETE |
| 5 | Migrate `routes/health.py` — replace `email[:3]***` ×1 | COMPLETE |
| 6 | Add PII cleanup documentation to `logging_config.py` | COMPLETE |
| 7 | Create `tests/test_log_sanitizer.py` — unit + integration tests | COMPLETE |
| 8 | Update `test_email_verification.py` fingerprint assertion (6→8 char) | COMPLETE |
| 9 | `pytest` + `npm run build` pass | COMPLETE |
| 10 | Git commit | COMPLETE |

**Review:**
- Shared module eliminates all `str(e)` leakage in email exception handlers + auth token decode
- Consistent `mask_email()` replaces ad-hoc `[:10]` and `[:3]***` slicing
- `token_fingerprint()` upgraded from 6-char+length to 8-char+SHA256 prefix
- `EmailResult.message` no longer returns raw exception text to API callers

---

### Sprint 301 — Allowlist Enforcement for Tool Session Sanitization

| # | Task | Status |
|---|------|--------|
| 1 | Add `ALLOWED_ADJUSTMENT_ENTRY_KEYS` + `ALLOWED_ADJUSTMENT_SET_KEYS` frozensets | COMPLETE |
| 2 | Refactor `_sanitize_adjustments_data()` to use allowlist (not blocklist) | COMPLETE |
| 3 | Update docstrings on `_sanitize_session_data` + `_sanitize_adjustments_data` | COMPLETE |
| 4 | Add `TestAllowlistEnforcement` class (5 tests) to `test_tool_sessions.py` | COMPLETE |
| 5 | `pytest` + `npm run build` pass | COMPLETE |
| 6 | Git commit | COMPLETE |

**Review:**
- Allowlist approach: `_sanitize_adjustments_data()` now filters to ONLY `ALLOWED_*_KEYS` instead of removing `_STRIP_KEYS`
- Blocklist constants (`_ADJUSTMENT_ENTRY_STRIP_KEYS`, `_ADJUSTMENT_SET_STRIP_KEYS`) retained for test coverage assertions
- 8 existing CRUD tests updated: `"adjustments"` → `"currency_rates"` for generic data payloads (allowlist strips non-metadata keys)
- 5 new regression tests: raw DB shape, exact output shape, hypothetical field blocking, allowlist-model sync, non-financial coverage
- Defense-in-depth `_strip_forbidden_keys_recursive` unchanged — still catches forbidden keys in all tools
- **Tests: 3,672 backend + 987 frontend**

---

### Sprint 302 — Dialect-Aware Test Infrastructure

| # | Task | Status |
|---|------|--------|
| 1 | `conftest.py`: Read `TEST_DATABASE_URL` env var, dialect-aware `db_engine` + `test_dialect` fixture | COMPLETE |
| 2 | `test_timestamp_defaults.py`: Skip `TestSQLiteCurrentTimestampIsUTC` on non-SQLite | COMPLETE |
| 3 | `ci.yml`: Pass `TEST_DATABASE_URL` to PostgreSQL job step | COMPLETE |
| 4 | `tool_session_model.py`: Expand `save_tool_session()` docstring | COMPLETE |
| 5 | `pytest` + `npm run build` pass | COMPLETE |
| 6 | Git commit | COMPLETE |

**Review:**
- `conftest.py` reads `TEST_DATABASE_URL` env var (default: `sqlite:///:memory:`)
- SQLite path: `check_same_thread=False` + `PRAGMA foreign_keys=ON`
- PostgreSQL path: `pool_pre_ping=True`, no SQLite connect_args
- `test_dialect` session fixture exposes dialect name for conditional test logic
- CI `.env` for PG job uses `DATABASE_URL=sqlite:///./test.db` (config.py module load) + `TEST_DATABASE_URL=postgresql://...` (actual test engine)
- `TestSQLiteCurrentTimestampIsUTC` skipped on PG (strptime vs datetime object)

---

### Sprint 303 — Production DB Guardrails

| # | Task | Status |
|---|------|--------|
| 1 | `database.py`: Add DB info logging to `init_db()` | COMPLETE |
| 2 | `test_db_fixtures.py`: Functional `_hard_fail` test + `init_db()` logging tests | COMPLETE |
| 3 | `pytest` + `npm run build` pass | COMPLETE |
| 4 | Git commit | COMPLETE |

**Review:**
- `init_db()` now logs dialect, pool class, and PG-specific version/pool info
- `test_hard_fail_raises_system_exit`: functional test (imports `_hard_fail`, asserts `SystemExit(1)`)
- `TestInitDbLogging`: 2 tests verify dialect/pool log output and SQLite mode in dev
- **Tests: 3,675 backend + 987 frontend**

---

### Sprint 304 — Upload Pipeline Hardening: XML Bomb Defense

| # | Task | Status |
|---|------|--------|
| 1 | Add `_scan_xlsx_xml_for_bombs()` to `backend/shared/helpers.py` | COMPLETE |
| 2 | Call from `_validate_xlsx_archive()` after structure checks | COMPLETE |
| 3 | Update module docstring with full 10-step pipeline | COMPLETE |
| 4 | Add `TestXmlBombProtection` class (7 tests) to `test_upload_validation.py` | COMPLETE |
| 5 | `pytest backend/tests/test_upload_validation.py -v` passes | COMPLETE |
| 6 | `pytest` full regression passes (3,682 passed) | COMPLETE |
| 7 | `npm run build` passes | COMPLETE |
| 8 | Git commit | PENDING |

**Review:**
- `_scan_xlsx_xml_for_bombs()`: streams first 8KB of each .xml/.rels/.vml entry, case-insensitive scan for `<!doctype>` / `<!entity>`
- Zero false positives: OOXML (ISO/IEC 29500) never uses DTDs in legitimate files
- Integrated after cheap structure checks (entry count, nested archives, size, ratio) for performance
- Handles corrupted entries via `zlib.error` / `KeyError` catch
- **Tests: 3,682 backend + 987 frontend**

