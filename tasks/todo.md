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

> **Detailed checklists:** `tasks/archive/` (phases-vi-ix, phases-x-xii, phases-xiii-xvii, phase-xviii, phases-xix-xxiii, phases-xxiv-xxvi, phase-xxvii, phase-xxviii, phase-xxix, phase-xxx, phase-xxxi, phase-xxxii)

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
| Frontend test coverage (30%+) | 43 files tested (~15%); next step ~30% needs more component tests | Sprint 249 |

---

## Active Phase

### Sprint 249 — Frontend Test Coverage Expansion (High-Value Targets) — COMPLETE

> **Source:** Coverage gap analysis — 37 test files / 389 tests covering ~1% of 200+ components. Identified 10 highest-value untested files by complexity × user impact × blast radius.
> **Strategy:** Write behavior-driven tests (not implementation details) for 10 highest-value gaps.
> **Impact:** 10 new test files, 131 new tests. Frontend tests: 389 → 520. Total: 3,050 backend + 520 frontend.

| # | Test File | Tests | Category |
|---|-----------|:-----:|----------|
| 1 | `FileDropZone.test.tsx` | 10 | Shared component (9 pages) |
| 2 | `RegisterPage.test.tsx` | 14 | Auth page (password strength, validation) |
| 3 | `LoginPage.test.tsx` | 11 | Auth page (VaultTransition, redirect) |
| 4 | `PracticeSettingsPage.test.tsx` | 14 | Settings page (16+ useState, 4 config sections) |
| 5 | `PortfolioPage.test.tsx` | 12 | CRUD page (modals, delete confirm, empty state) |
| 6 | `AdjustmentEntryForm.test.tsx` | 13 | Complex form (dynamic lines, balance validation) |
| 7 | `FollowUpItemsTable.test.tsx` | 14 | Complex table (5 filters, sort, expand, inline edit) |
| 8 | `CreateEngagementModal.test.tsx` | 12 | Modal form (date validation, materiality config) |
| 9 | `EngagementsPage.test.tsx` | 11 | Workspace page (list/detail, tabs, URL sync) |
| 10 | `useTrialBalanceAudit.test.ts` | 20 | Complex hook (40+ state vars, 7 contexts) |

- [x] Coverage gap analysis (exploration agents)
- [x] Write all 10 test files
- [x] Fix 4 test failures (duplicate text queries, barrel import mocks, named vs default export mocks)
- [x] All 43 test suites pass (520 tests)
- [x] `npm run build` passes
- [x] Todo/archive protocol followed

**Review:** Fixes required: (1) `getByText` → `getByRole('heading')` for text appearing in both nav breadcrumb and h1. (2) Barrel import mock (`@/components/engagement`) instead of individual file mocks. (3) Named export mock (`{ CommentThread }`) instead of default export mock (`__esModule: true, default:`). (4) Missing `StatusBadge` mock for FollowUpItemsTable.

### Sprint 250 — Docker Production Tuning — COMPLETE

> **Source:** Docker review — multi-stage build efficiency, healthcheck overhead, Gunicorn tuning, env var drift
> **Impact:** ~20MB smaller backend image, configurable workers, worker recycling, fixed JWT default drift

- [x] Backend Dockerfile: `--prefix=/install` to exclude pip/setuptools from production image (~20MB savings)
- [x] Backend Dockerfile: `curl -f` healthcheck replaces spawning full Python interpreter every 30s
- [x] Backend Dockerfile: Configurable Gunicorn via env vars (`WEB_CONCURRENCY`, `GUNICORN_TIMEOUT`, `GUNICORN_GRACEFUL_TIMEOUT`, `GUNICORN_KEEP_ALIVE`, `GUNICORN_MAX_REQUESTS`)
- [x] Backend Dockerfile: `--max-requests 1000 --max-requests-jitter 50` for Pandas memory leak prevention
- [x] Backend Dockerfile: `--keep-alive 5` for reverse proxy compatibility, `--graceful-timeout 30` explicit
- [x] docker-compose.yml: Removed duplicate healthcheck blocks (Dockerfile HEALTHCHECK used automatically)
- [x] docker-compose.yml: Fixed `JWT_EXPIRATION_MINUTES` default from 1440 → 30 (Phase XXV drift)
- [x] docker-compose.yml: Added `REFRESH_TOKEN_EXPIRATION_DAYS`, `WEB_CONCURRENCY`, `GUNICORN_TIMEOUT`, `GUNICORN_MAX_REQUESTS` passthrough
- [x] `.env.example`: Added Gunicorn Tuning section documenting all Docker-specific env vars

**Review:** Compose `JWT_EXPIRATION_MINUTES` default was 1440 (24h) but backend config.py was hardened to 30 min in Phase XXV Sprint 198 — compose silently overrode the hardening. Always verify compose defaults match backend config after security hardening phases.

### Sprint 251 — Global Exception Handler — COMPLETE

> **Source:** Comprehensive codebase review — error handling, logging, config, secrets audit
> **Impact:** Unhandled 500s now return generic `{"detail": "Internal server error", "request_id": "<uuid>"}` instead of raw stack traces

- [x] Add `@app.exception_handler(Exception)` to `main.py`
- [x] Log full traceback via `logger.exception()` with method, path, request ID
- [x] Return sanitized JSON response with request_id for client-side log correlation
- [x] 3,050 backend tests pass

**Review:** No issues. Single-file change, zero risk. This is a safety net for everything the per-route try/except blocks miss.

### Sprint 252 — Standardize sanitize_error Usage — COMPLETE

> **Source:** Same codebase review — 21 instances of `detail=str(e)` across 6 route files
> **Impact:** All ValueError catches now route through `sanitize_error()` with logging + pattern-based sanitization

- [x] Add `allow_passthrough` keyword-only param to `sanitize_error()` in `shared/error_messages.py`
- [x] Replace 21 `detail=str(e)` across adjustments, audit, clients, engagements, follow_up_items, users
- [x] CRUD routes use `allow_passthrough=True` (preserves "Engagement not found" etc.)
- [x] `audit.py` workbook inspection uses `operation="upload"` without passthrough (file path risk)
- [x] All 21 instances now log via `log_secure_operation` with per-route labels
- [x] 3,050 backend tests pass

**Review:** Key design decision: `allow_passthrough=True` returns original message when no dangerous pattern matches, preserving UX for business-logic ValueErrors. Without this, all validation errors would become generic "An unexpected error occurred."

### Sprint 253 — Database Error Handling Gaps — COMPLETE

> **Source:** Same codebase review — 9 bare `db.commit()` calls with no try/except
> **Impact:** SQLAlchemy errors (IntegrityError, OperationalError) now produce rollback + structured log + sanitized 500 instead of raw tracebacks

- [x] Add `SQLAlchemyError` catch + `db.rollback()` + `logger.exception()` + `sanitize_error()` to 9 commits
- [x] Files: activity.py (2), auth_routes.py (3), diagnostics.py (1), prior_period.py (1), settings.py (2)
- [x] Each file gains `import logging`, `logger`, `SQLAlchemyError`, `sanitize_error` imports
- [x] 3,050 backend tests pass

**Review:** All 9 instances were infrastructure-level operations (create/update/delete) where SQLAlchemy errors are unexpected. 500 status code is correct (not user-correctable). `sanitize_error()` pattern match produces "A database error occurred. Please try again."

### .gitignore Hardening (between Sprints 253–254) — COMPLETE

> **Source:** Same codebase review — certificate file patterns missing from .gitignore
> **Impact:** Defense-in-depth: *.pem, *.key, *.p12, *.crt, *.pfx now excluded

- [x] Add 5 certificate/key patterns to `.gitignore`

### Sprint 254 — Integrate secrets_manager into config.py — COMPLETE

> **Source:** Same codebase review — `secrets_manager.py` existed but was unused by `config.py`
> **Impact:** Unified secret resolution chain (env vars > Docker secrets > AWS/GCP/Azure) with zero behavior change for current deployments

- [x] Import `get_secret` as `_resolve_secret` and `get_secrets_manager` from `secrets_manager`
- [x] Replace `os.getenv()` in `_load_required()` and `_load_optional()` with `_resolve_secret()`
- [x] Replace direct `os.getenv("JWT_SECRET_KEY")` with `_resolve_secret("JWT_SECRET_KEY")`
- [x] Add `Secrets Provider: env` line to `print_config_summary()`
- [x] 3,050 backend tests pass

**Review:** Minimal change (11 insertions, 6 deletions). All existing validation (hard_fail, JWT strength, CORS wildcards) preserved. `load_dotenv()` populates `os.environ` before `_resolve_secret()` runs, so .env values are still picked up via priority 1. Docker secrets and cloud providers are additive — no config changes needed for current deployments.
