# Phase XXXVII: Deployment Hardening (Sprints 273–278)

> **Focus:** Deployment readiness — dependency bumps, PostgreSQL pool tuning, Sentry APM, frontend test coverage
> **Version:** 1.4.0 → 1.5.0
> **Tests:** 3,391 backend + 745 frontend → 3,396 backend + 918 frontend

---

## Sprint 273: Dependency Version Bumps (3/10) — COMPLETE

- [x] Bump `pydantic[email]` 2.10.6 → 2.12.5
- [x] Bump `openpyxl` 3.1.2 → 3.1.5
- [x] Bump `PyJWT[crypto]` 2.10.1 → 2.11.0
- [x] Bump `typescript` ^5.3.3 → ^5.9.3
- [x] Raise dev dep floors: `httpx>=0.28.0`, `ruff>=0.15.0`, `mypy>=1.19.0`
- [x] Skip decisions documented: alembic (already latest 1.18.4), reportlab (already latest 4.4.10), sqlalchemy (already latest 2.0.46), pandas 3.0 (breaking CoW), React 19 (major), SQLAlchemy 2.1 (beta)
- [x] All 3,391 backend + 745 frontend tests pass, build clean

**Files:** `backend/requirements.txt`, `backend/requirements-dev.txt`, `frontend/package.json`

---

## Sprint 274: PostgreSQL Connection Hardening + CI (4/10) — COMPLETE

- [x] Add `_load_optional_int()` to config.py
- [x] Add `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE` env vars
- [x] Refactor `database.py`: dialect-conditional engine creation (SQLite vs PostgreSQL)
- [x] PostgreSQL engine gets `pool_pre_ping`, `pool_size`, `max_overflow`, `pool_recycle`
- [x] Add pool config section to `.env.example`
- [x] Add `backend-tests-postgres` CI job with `postgres:15-alpine` service container
- [x] Add optional commented-out `db` service to `docker-compose.yml`
- [x] Fix DEPLOYMENT_ARCHITECTURE.md section 8.2: "Migrations (Future)" → "Migrations (Alembic)"
- [x] Update section 8.3 with actual pool implementation + env var table
- [x] All tests pass

**Files:** `backend/database.py`, `backend/config.py`, `backend/.env.example`, `.github/workflows/ci.yml`, `docker-compose.yml`, `docs/02-technical/DEPLOYMENT_ARCHITECTURE.md`

---

## Sprint 275: Sentry APM Integration (4/10) — COMPLETE

- [x] Add `sentry-sdk[fastapi]==2.53.0` to requirements.txt
- [x] Add `@sentry/nextjs ^10.39.0` to package.json
- [x] Add `SENTRY_DSN` + `SENTRY_TRACES_SAMPLE_RATE` + `_load_optional_float()` to config.py
- [x] Add conditional Sentry init in main.py with `_before_send` stripping request bodies
- [x] Create `sentry.client.config.ts` (Zero-Storage: replaysSessionSampleRate=0, replaysOnErrorSampleRate=0)
- [x] Create `sentry.server.config.ts`
- [x] Wrap `next.config.js` with conditional `withSentryConfig()`
- [x] 5 backend tests in `test_sentry_integration.py`
- [x] Update DEPLOYMENT_ARCHITECTURE.md section 9.1
- [x] Build + tests pass

**Files:** `backend/requirements.txt`, `backend/config.py`, `backend/main.py`, `backend/.env.example`, `backend/tests/test_sentry_integration.py` (new), `frontend/package.json`, `frontend/next.config.js`, `frontend/sentry.client.config.ts` (new), `frontend/sentry.server.config.ts` (new), `docs/02-technical/DEPLOYMENT_ARCHITECTURE.md`

---

## Sprint 276: Frontend Hook Tests Batch 1 (5/10) — COMPLETE

10 new test files, 92 new tests:
- [x] `useActivityHistory.test.ts` (10 tests)
- [x] `useRollingWindow.test.ts` (8 tests)
- [x] `useIndustryRatios.test.ts` (9 tests)
- [x] `useTrends.test.ts` (10 tests)
- [x] `useMultiPeriodComparison.test.ts` (10 tests)
- [x] `useFollowUpItems.test.ts` (10 tests)
- [x] `useFollowUpComments.test.ts` (8 tests)
- [x] `useCurrencyRates.test.ts` (9 tests)
- [x] `useVerification.test.ts` (8 tests)
- [x] `useAuditUpload.test.ts` (10 tests)
- [x] Coverage threshold raised from 10% to 20%
- [x] Full suite: 837 tests pass (70 suites)

**Files:** 10 new test files in `frontend/src/__tests__/`, `frontend/jest.config.js`

---

## Sprint 277: Frontend Component + Hook Tests Batch 2 (5/10) — COMPLETE

13 new test files, 81 new tests:
- [x] `useBatchUpload.test.ts` (11 tests)
- [x] `CollapsibleSection.test.tsx` (7 tests)
- [x] `SectionHeader.test.tsx` (6 tests)
- [x] `DownloadReportButton.test.tsx` (7 tests)
- [x] `ProtectedRoute.test.tsx` (5 tests)
- [x] `GuestCTA.test.tsx` (4 tests)
- [x] `ZeroStorageNotice.test.tsx` (3 tests)
- [x] `EngagementCard.test.tsx` (9 tests)
- [x] `EngagementList.test.tsx` (6 tests)
- [x] `DispositionSelect.test.tsx` (5 tests)
- [x] `ToolLinkToast.test.tsx` (5 tests)
- [x] `TrendSummaryCard.test.tsx` (8 tests)
- [x] `PercentileBar.test.tsx` (5 tests)
- [x] Coverage threshold raised from 20% to 25%
- [x] Full suite: 918 tests pass (83 suites)

**Coverage:** 44.28% statements, 35.15% branches, 35.5% functions, 45.85% lines

**Files:** 13 new test files in `frontend/src/__tests__/`, `frontend/jest.config.js`

---

## Sprint 278: Phase XXXVII Wrap + v1.5.0 (2/10) — COMPLETE

- [x] Backend regression: 3,396 passed
- [x] Frontend regression: 918 passed (83 suites)
- [x] Frontend build: zero errors
- [x] Bump `backend/version.py` to 1.5.0
- [x] Align `frontend/package.json` version to 1.5.0
- [x] Update CLAUDE.md: add Phase XXXVII, update test counts, version
- [x] Archive to `tasks/archive/phase-xxxvii-details.md`
- [x] Update `tasks/todo.md`: move to completed, clear active phase
- [x] Update `MEMORY.md`: project status

---

## Excluded (with rationale)

| Item | Reason |
|------|--------|
| pandas 3.0 | Copy-on-Write + string dtype breaking changes — needs own phase |
| React 19 | Major version, breaking changes — needs own phase |
| SQLAlchemy 2.1 | Still beta only |
| OpenTelemetry/Prometheus | Sentry covers error tracking + basic APM; full observability premature |
| Cookie-based auth | Large blast radius (deferred from Phase XXVII) |
