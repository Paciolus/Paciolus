# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Phases

### Phase I (Sprints 1-24) — COMPLETE
> Core platform: Zero-Storage TB analysis, streaming, classification, brand, risk dashboard, multi-sheet Excel, PDF/Excel export, JWT auth, activity logging, client management, practice settings, deployment prep.

### Phase II (Sprints 25-40) — COMPLETE
> Test suite, 9 ratios (Current/Quick/D2E/Gross/Net/Operating/ROA/ROE/DSO), IFRS/GAAP docs, trend analysis + viz, industry ratios (6 industries), rolling windows, batch upload, benchmark RFC.

### Phase III (Sprints 41-47) — COMPLETE
> Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI + integration.

### Phase IV (Sprints 48-55) — COMPLETE
> User profile, security hardening, lead sheets (A-Z), prior period comparison, adjusting entries, DSO ratio, CSV export, frontend test foundation.

### Phase V (Sprints 56-60) — COMPLETE
> UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode. **Tests: 625 backend + 26 frontend.**

### Phase VI (Sprints 61-70) — COMPLETE
> Multi-Period TB Comparison (Tool 2), Journal Entry Testing (Tool 3, 18-test battery + stratified sampling), platform rebrand to suite, diagnostic zone protection. Tests added: 268 JE + multi-period.

### Phase VII (Sprints 71-80) — COMPLETE
> Financial Statement Builder (Tool 1 enhancement), AP Payment Testing (Tool 4, 13-test battery), Bank Reconciliation (Tool 5). Tests added: 165 AP + 55 bank rec.

### Phase VIII (Sprints 81-89) — COMPLETE
> Cash Flow Statement (indirect method, ASC 230/IAS 7), Payroll & Employee Testing (Tool 6, 11-test battery), code quality sprints (81-82). Tests added: 139 payroll.

### Phase IX (Sprints 90-96) — COMPLETE
> Shared testing utilities extraction (enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement). Tests added: 114 three-way match + 52 classification.

### Phase X (Sprints 96.5-102) — COMPLETE
> The Engagement Layer: engagement model + materiality cascade, follow-up items tracker (narratives-only), workpaper index, anomaly summary report (PDF), diagnostic package export (ZIP with SHA-256), engagement workspace frontend. 8 AccountingExpertAuditor guardrails satisfied. Tests added: 158 engagement/follow-up/workpaper/export.

### Phase XI (Sprints 103-110) — COMPLETE
> Tool-Engagement Integration (frontend auto-link via EngagementProvider), Revenue Testing (Tool 8, 12-test battery, ISA 240), AR Aging Analysis (Tool 9, 11-test battery, dual-input TB + sub-ledger). Tests added: 110 revenue + 28 memo + 131 AR + 34 memo.

### Phase XII (Sprints 111-120) — COMPLETE
> Nav overflow infrastructure, FileDropZone extraction, Finding Comments + Assignments (collaboration), Fixed Asset Testing (Tool 10, 9-test battery, IAS 16), Inventory Testing (Tool 11, 9-test battery, IAS 2). Tests added: 41 comments + 15 assignments + 133 FA + 38 FA memo + 136 inventory + 38 inv memo.

### Phase XIII (Sprints 121-130) — COMPLETE
> Platform polish + dual-theme "The Vault Interior" architecture. Security hardening (26 rate-limited exports, upload validation, error sanitization). CSS custom property + Tailwind semantic token infrastructure. Light theme migration (all tool + authenticated pages). VaultTransition login animation. Export consolidation + Bank Rec/Multi-Period memos (11/11 tools with PDF memos). WCAG AAA accessibility + 60 frontend test backfill. **Version: 1.2.0. Tests: 2,593 backend + 128 frontend.**

### Phase XIV (Sprints 131-135) — COMPLETE
> Professional Threshold: 6 public marketing/legal pages (Privacy, Terms, Contact, About, Approach, Pricing, Trust). Shared MarketingNav/Footer. Contact backend with honeypot + rate limiting. All pages dark-themed (vault exterior).

### Phase XV (Sprints 136-141) — COMPLETE
> Code Deduplication: shared parsing helpers, shared types, 4 shared testing components (DataQualityBadge, ScoreCard, TestResultGrid, FlaggedTable), context consolidation. ~4,750 lines removed (81% deduplication), 100% backward compatible.

### Phase XVI (Sprints 142-150) — COMPLETE
> API Hygiene: semantic token migration, API call consolidation (15 direct fetch → apiClient), N+1 query fix, Docker hardening (.dockerignore, multi-stage fix, SQLite path).

### Phase XVII (Sprints 151-163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules (column_detector, data_quality, test_aggregator, benford, export_schemas, testing_route, memo_template), 8 frontend decompositions (TB page 1,219→215, export 1,497→32, practice 1,203→665, multi-period 897→470, FinancialStatements 772→333), hook factory, centralized constants. 15 new shared files, 9,298 added / 8,849 removed. **Tests: 2,716 backend + 128 frontend.**

### Phase XVIII (Sprints 164-170) — COMPLETE
> Async Architecture Remediation: `async def` → `def` for 82+ pure-DB/export endpoints, `asyncio.to_thread()` for CPU-bound Pandas work, `BackgroundTasks` for email/tool-run recording, `memory_cleanup()` context manager, rate limit gap closure. Zero behavioral regressions.

### Phase XIX (Sprints 171-177) — COMPLETE
> API Contract Hardening: 25 endpoints gain response_model, 16 status codes corrected (DELETE→204, POST→201), trends.py error-in-body→HTTPException(422), `/diagnostics/flux`→`/audit/flux` path fix, shared response schemas.

### Phase XX (Sprint 178) — COMPLETE
> Rate Limit Gap Closure: missing limits on verify-email, password-change, waitlist, inspect-workbook; global 60/min default.

### Phase XXI (Sprints 180-183) — COMPLETE
> Migration Hygiene: Alembic env.py model imports, baseline regeneration (e2f21cb79a61), manual script archival, datetime deprecation fix.

### Phase XXII (Sprints 184-190) — COMPLETE
> Pydantic Model Hardening: Field constraints (min_length/max_length/ge/le), 13 str→Enum/Literal migrations, ~100 lines manual validation removed, WorkpaperMetadata base class (10 models), DiagnosticSummaryCreate decomposition, v2 ConfigDict syntax, password field_validators, adjustments bugfix.

### Phase XXIII (Sprints 191-194) — COMPLETE
> Pandas Performance & Precision Hardening: vectorized keyword matching (.apply→.str.contains), filtered-index iteration, Decimal concentration totals, NEAR_ZERO float guards (4 engines), math.fsum compensated summation (8 locations), identifier dtype preservation, dtype passthrough in security_utils. **Tests: 2,731 backend + 128 frontend.**

### Phase XXIV (Sprint 195) — COMPLETE
> Upload & Export Security Hardening: CSV/Excel formula injection sanitization, column/cell limits, global body size middleware. **Tests: 2,750 backend + 128 frontend.**

### Sprint 196 — PDF Generator Critical Fixes — COMPLETE
> Fix `_build_workpaper_signoff()` crash (bad style/color/font refs), dynamic tool count (7→11), BytesIO buffer leak.

### Phase XXV (Sprints 197-201) — COMPLETE
> JWT Authentication Hardening: refresh token rotation (7-day), 30-min access tokens, token reuse detection, password-change revocation, CSRF/CORS hardening, explicit bcrypt rounds, jti claim, startup token cleanup. **Tests: 2,883 backend + 128 frontend.**

### Phase XXVI (Sprints 202-203) — COMPLETE
> Email Verification Hardening: verification token cleanup job (startup), email-change re-verification via pending_email, security notification to old email, disposable email blocking. **Tests: 2,903 backend + 128 frontend.**

### Phase XXVII (Sprints 204-209) — COMPLETE
> Next.js App Router Hardening: 7 error boundaries (global-error, not-found, root, tools, engagements, portfolio, settings, history), 4 route groups ((marketing), (auth), (diagnostic), tools enhanced), ~60 duplicated imports eliminated, DiagnosticProvider scoped, 8 fetch() → apiClient, 5 shared skeleton components, 11 loading.tsx files. **Tests: 2,903 backend + 128 frontend.**

### Phase XXVIII (Sprints 210-216) — COMPLETE
> Production Hardening: GitHub Actions CI pipeline (pytest + build + ruff lint), Python structured logging + request ID correlation, 46 broad exceptions narrowed to specific types, 45 return type annotations added, deprecated pattern migration (DeclarativeBase, lifespan context manager), 5 frontend `any` types eliminated, 3 TODOs resolved. **Tests: 2,903 backend + 128 frontend.**

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md` | `tasks/archive/phases-xiii-xvii-details.md` | `tasks/archive/phase-xviii-details.md` | `tasks/archive/phases-xix-xxiii-details.md` | `tasks/archive/phases-xxiv-xxvi-details.md` | `tasks/archive/phase-xxvii-details.md` | `tasks/archive/phase-xxviii-details.md`

---

## Post-Sprint Checklist

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Multi-Currency Conversion | Detection shipped (Sprint 64); conversion logic needs RFC | Phase VII |
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, deficiency classification is auditor judgment | Phase X |
| Dual-key rate limiting (IP + user_id) | Needs custom JWT key_func; IP-only + lockout is adequate for now | Phase XX |
| Wire Alembic into startup | Adds latency, multi-worker race risk; revisit for PostgreSQL | Phase XXI |
| `PaginatedResponse[T]` generic | Complicates OpenAPI schema generation | Phase XXII |
| Dedicated `backend/schemas/` directory | Model count doesn't justify yet | Phase XXII |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Cookie-based auth (enables SSR) | Requires migrating JWT from sessionStorage to httpOnly cookies; large blast radius | Phase XXVII audit |
| Marketing pages SSG | Requires cookie auth migration first; currently all pages are `'use client'` | Phase XXVII audit |
| Frontend test coverage expansion (4.3% → 30%+) | 302 source files, 13 tested — too large for one phase, needs dedicated multi-sprint effort | Phase XXVIII audit |

---

## Phase XXVIII — Production Hardening (Sprints 210–216)

> **Status:** COMPLETE
> **Source:** Comprehensive 3-agent audit (2026-02-13) — frontend quality, backend code smells, infrastructure gaps
> **Strategy:** CI/CD first (automates existing 2,903 tests), then logging (production blind spot), then exception/type hardening, then deprecated patterns, then frontend cleanup
> **Scope:** GitHub Actions CI, Python logging infrastructure, 54 broad exceptions narrowed, 68+ return type annotations, 2 deprecated patterns migrated, 4 frontend `any` types eliminated, 3 TODOs resolved

### Audit Findings Summary

| Category | Finding | Count | Severity |
|----------|---------|:-----:|----------|
| **Infrastructure** | No CI/CD pipeline (no GitHub Actions, no pre-commit hooks) | — | CRITICAL |
| **Backend** | Zero Python `logging` module usage — silent failures | — | HIGH |
| **Backend** | Broad `except Exception` clauses (mainly export routes) | 54 | HIGH |
| **Backend** | Functions missing return type annotations | 68+ | MEDIUM |
| **Backend** | Deprecated patterns (`declarative_base()`, `@app.on_event`) | 2 | MEDIUM |
| **Backend** | Hardcoded config values (FRONTEND_URL default, rate limits) | ~5 | LOW |
| **Frontend** | `any` types in production code | 4 | MEDIUM |
| **Frontend** | Unresolved TODO comments | 3 | LOW |
| **Frontend** | Components >400 LOC (potential decomposition) | 5 | LOW |
| **Frontend** | Test coverage: 4.3% file coverage, 2% component, 0% hook | — | CRITICAL (deferred to Phase XXIX) |

### Sprint 210 — GitHub Actions CI Pipeline

> **Complexity:** 3/10
> **Goal:** Automate the existing 2,903 backend tests + frontend build on every PR and push to main. Make the test suite an actual regression gate.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `.github/workflows/ci.yml` — pytest on PR/push to main | CRITICAL | COMPLETE |
| 2 | Add frontend build check (`npm run build`) to CI workflow | HIGH | COMPLETE |
| 3 | Add Python linting step (ruff) | MEDIUM | COMPLETE |
| 4 | Cache pip + npm dependencies for fast CI runs | LOW | COMPLETE |

#### Checklist

- [x] `.github/workflows/ci.yml` with matrix: Python 3.11+, Node 22
- [x] Backend job: install deps, create test `.env`, run `pytest`
- [x] Frontend job: install deps, run `npm run build` + `npm run lint`
- [x] Lint job: `ruff check .` (Pyflakes errors only, no auto-fix)
- [x] Dependency caching: `actions/setup-python` + `actions/setup-node` built-in cache
- [x] Branch protection recommendation (documented in workflow header comment)
- [x] `npm run build` — passes (36+ routes)
- [x] `ruff check .` — All checks passed (6 issues fixed: 1 missing import, 2 unused imports, 3 f-strings)
- [x] `pytest` — 2,903 passed, 0 regressions

#### Review — Sprint 210

**Files Created:**
- `.github/workflows/ci.yml` — CI pipeline (backend-tests, frontend-build, backend-lint)
- `backend/ruff.toml` — Conservative ruff config (Pyflakes only)

**Files Modified:**
- `backend/requirements-dev.txt` — Added `ruff>=0.4.0`
- `backend/bank_reconciliation.py` — Removed unused `date` import (F811)
- `backend/fixed_asset_testing_engine.py` — Added missing `import re` (F821 real bug!)
- `backend/generate_large_tb.py` — Removed f-prefix from placeholder-less f-string (F541)
- `backend/practice_settings.py` — Removed f-prefix from placeholder-less f-string (F541)
- `backend/routes/auth_routes.py` — Removed f-prefix from placeholder-less f-string (F541)

**CI Jobs:**
- `backend-tests`: Python 3.11 + 3.12 matrix, in-memory SQLite, 2,903 tests
- `frontend-build`: Node 22, `npm ci` + `npm run build` + `npm run lint`
- `backend-lint`: ruff with Pyflakes rules (real bugs only)
- Concurrency: cancels in-progress runs on same branch

---

### Sprint 211 — Python Logging Infrastructure

> **Complexity:** 4/10
> **Goal:** Add structured logging across the backend. Replace silent failures with logged errors. Enable production debugging.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `backend/logging_config.py` — structured logger configuration | HIGH | COMPLETE |
| 2 | Add request ID middleware for log correlation | MEDIUM | COMPLETE |
| 3 | Add loggers to startup events, auth flows, error handlers | HIGH | COMPLETE |
| 4 | Add loggers to export routes (where most broad exceptions live) | HIGH | COMPLETE |

#### Checklist

- [x] `logging_config.py`: `setup_logging()` — structured JSON format for production, human-readable for dev
- [x] Per-module loggers: `logger = logging.getLogger(__name__)` pattern
- [x] Request ID middleware: generate UUID per request, attach to log context
- [x] Startup logging: server start, DB connection, cleanup job results
- [x] Auth logging: login success/failure, token refresh, password change (no PII)
- [x] Export error logging: replace silent `except Exception` with `logger.exception()`
- [x] Wire `setup_logging()` in `main.py` startup
- [x] `pytest` — 2,903 passed, 0 regressions

#### Review — Sprint 211

**Files Created:**
- `backend/logging_config.py` — Structured logging setup (JSON production, human-readable dev), request ID contextvars, RequestIdFilter

**Files Modified:**
- `backend/main.py` — Wire `setup_logging()`, `RequestIdMiddleware`, startup logging via `logger.info()`
- `backend/security_middleware.py` — Added `RequestIdMiddleware` class (UUID per request, X-Request-ID header)
- `backend/routes/auth_routes.py` — Added `logger` for login/register/refresh events
- `backend/routes/export_testing.py` — Added `logger.exception()` in 8 except blocks
- `backend/routes/export_diagnostics.py` — Added `logger.exception()` in 6 except blocks
- `backend/routes/export_memos.py` — Added `logger.exception()` in 10 except blocks
- `backend/shared/helpers.py` — Added `logger` for `safe_background_email` error/exception logging

**Architecture:**
- `setup_logging()` called at module level in `main.py` (before app creation)
- `RequestIdMiddleware` sets `request_id_var` (contextvars) per request, `RequestIdFilter` injects into log records
- JSON format for `ENV_MODE=production`, human-readable `HH:MM:SS | LEVEL | module | [request_id] message` for dev
- Noisy third-party loggers quieted: uvicorn.access, sqlalchemy.engine, passlib, multipart
- `log_secure_operation()` calls preserved alongside — serves separate in-memory audit trail

---

### Sprint 212 — Exception Narrowing (Export Routes)

> **Complexity:** 4/10
> **Goal:** Replace 54 broad `except Exception` blocks with specific exception types. Log actual errors instead of swallowing them.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Audit all 52 `except Exception` locations — categorize by exception type | HIGH | COMPLETE |
| 2 | Narrow exceptions in export routes (24 blocks) | HIGH | COMPLETE |
| 3 | Narrow exceptions in tool route files (13 blocks) | HIGH | COMPLETE |
| 4 | Narrow exceptions in engine/service files (15 blocks) | MEDIUM | COMPLETE |

#### Checklist

- [x] Map each `except Exception` to specific types: `ValueError`, `KeyError`, `TypeError`, `OSError`, `UnicodeEncodeError`
- [x] Pattern: `except (ValueError, KeyError, TypeError) as e: logger.exception("..."); raise HTTPException(...)`
- [x] Export CSV routes: `except (ValueError, KeyError, TypeError, UnicodeEncodeError)` (8+2+1=11 blocks)
- [x] Export PDF/Excel routes: `except (ValueError, KeyError, TypeError, OSError)` (4+10+2=16 blocks)
- [x] Tool analysis routes: `except (ValueError, KeyError, TypeError)` (audit 2, bank_rec 1, ar_aging 1, je 2, twm 1, testing_route 1)
- [x] Engine/service files: ar_aging_engine→ValueError, workbook_inspector→KeyError/OSError, email_service→OSError/ValueError/RuntimeError, pdf_generator→OSError/ValueError
- [x] Intentionally kept broad (6): secrets_manager cloud SDK (3), security_utils format detection (2), helpers.safe_background_email (1)
- [x] `pytest` — 2,903 passed, 0 regressions
- [x] `ruff check` — All checks passed

#### Review — Sprint 212

**Scope:** 46 of 52 `except Exception` blocks narrowed (88%). 6 intentionally kept broad with comments.

**Files Modified (17):**
- `routes/export_testing.py` — 8 blocks: `(ValueError, KeyError, TypeError, UnicodeEncodeError)`
- `routes/export_diagnostics.py` — 6 blocks: CSV→`UnicodeEncodeError`, PDF/Excel→`OSError`
- `routes/export_memos.py` — 10 blocks: `(ValueError, KeyError, TypeError, OSError)`
- `routes/audit.py` — 3 blocks: workbook→`(KeyError, TypeError, OSError)`, analysis→`(ValueError, KeyError, TypeError)`
- `routes/bank_reconciliation.py` — 2 blocks: analysis→`(ValueError, KeyError, TypeError)`, CSV→`UnicodeEncodeError`
- `routes/ar_aging.py` — 1 block: `(ValueError, KeyError, TypeError)`
- `routes/je_testing.py` — 2 blocks: `(ValueError, KeyError, TypeError)`
- `routes/multi_period.py` — 1 block: `(ValueError, KeyError, TypeError, UnicodeEncodeError)`
- `routes/three_way_match.py` — 1 block: `(ValueError, KeyError, TypeError)`
- `routes/health.py` — 1 block: `OSError`
- `shared/testing_route.py` — 1 block: `(ValueError, KeyError, TypeError)` (affects 6 routes)
- `shared/helpers.py` — 1 block: `(ValueError, KeyError, OSError, UnicodeDecodeError)`
- `email_service.py` — 3 blocks: `(OSError, ValueError, RuntimeError)`
- `pdf_generator.py` — 1 block: `(OSError, ValueError)`
- `workbook_inspector.py` — 2 blocks: `(KeyError, TypeError, OSError)`, `(ValueError, OSError)`
- `ar_aging_engine.py` — 1 block: `(ValueError, TypeError, AttributeError)`
- `secrets_manager.py` — 1 narrowed to `OSError`, 3 kept broad (cloud SDKs)
- `security_utils.py` — 2 kept broad with comments (format detection fallback)

**All modified route files also gained `import logging` + `logger = logging.getLogger(__name__)`.**

---

### Sprint 213 — Backend Return Type Annotations

> **Complexity:** 3/10
> **Goal:** Add return type annotations to 68+ functions missing them. Improves IDE support and catches type mismatches.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Add return types to `auth.py` functions | MEDIUM | ✅ ALREADY COMPLETE |
| 2 | Add return types to `shared/` module functions | MEDIUM | ✅ COMPLETE |
| 3 | Add return types to model `to_dict()` / helpers | MEDIUM | ✅ COMPLETE |
| 4 | Add return types to `database.py`, `pdf_generator.py`, route helpers | LOW | ✅ COMPLETE |

#### Checklist

- [x] `auth.py`: all public functions already had `-> ReturnType`
- [x] `shared/*.py`: `memory_cleanup()`, `write_testing_csv_summary()`
- [x] Engine modules: already had return types (confirmed by audit)
- [x] Memo generators: all `generate_*` already had `-> bytes`
- [x] Models: 9 `to_dict()` + 9 `__repr__()` + 2 `get_*_dict()` methods
- [x] `database.py`: `get_db()`, `init_db()`, `_set_sqlite_pragmas()`
- [x] `pdf_generator.py`: `DoubleRule.draw/wrap`, `LedgerRule.draw/wrap`, `_draw_page_decorations`, `draw_fs_decorations`
- [x] `excel_generator.py`: 6 private methods
- [x] `leadsheet_generator.py`: 3 private methods
- [x] `main.py`: `startup_event()`
- [x] `security_utils.py`: `wrapper()`, `__exit__()`
- [x] `practice_settings.py`: `validate_value()`, `validate_weights()`
- [x] `routes/trends.py`: `_summaries_to_snapshots()`, `_get_client_summaries()`
- [x] `routes/diagnostics.py`: `accept_flat_format()`
- [x] Use `-> None` for void functions, not omission
- [x] `pytest` — 2,903 passed, 0 regressions

---

### Sprint 214 — Deprecated Pattern Migration — COMPLETE

> **Complexity:** 3/10
> **Goal:** Migrate 2 deprecated SQLAlchemy/FastAPI patterns to modern equivalents.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Migrate `declarative_base()` → `DeclarativeBase` class (SQLAlchemy 2.0) | MEDIUM | DONE |
| 2 | Migrate `@app.on_event("startup")` → `lifespan` context manager | MEDIUM | DONE |
| 3 | Extract hardcoded config values to environment variables | LOW | DONE |

#### Checklist

- [x] `database.py`: `Base = declarative_base()` → `class Base(DeclarativeBase): pass`
- [x] Verify all models still inherit correctly from new `Base` (no changes needed — same export name)
- [x] `main.py`: `@app.on_event("startup")` → `@asynccontextmanager async def lifespan(app):`
- [x] Move startup cleanup jobs (refresh tokens, verification tokens) into lifespan
- [x] Config: `FRONTEND_URL` extracted from `email_service.py` to `config.py`
- [x] Alembic `env.py`: no change needed — `from database import Base` unchanged
- [x] `pytest` — 2,903 passed, 0 regressions
- [x] `npm run build` — passes

---

### Sprint 215 — Frontend Type Safety + TODO Cleanup — COMPLETE

> **Complexity:** 2/10
> **Goal:** Eliminate 5 `any` types in production code, resolve 3 TODO comments, document large components.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Replace 5 `any` types with proper interfaces | MEDIUM | DONE |
| 2 | Resolve 3 TODO comments (register modals, portfolio lastAuditDate) | LOW | DONE |
| 3 | Document 5 components >400 LOC for future decomposition | LOW | DONE |

#### Checklist

- [x] `DownloadReportButton.tsx`: replace 5 `any` types → `AbnormalBalanceExtended[]`, `ClassificationSummary`, `ColumnDetectionInfo | null`, `RiskSummary`, `ConsolidatedAuditResult['sheet_results']`
- [x] Remaining `any` locations: 3 with eslint-disable (FlaggedEntriesTable, TestResultGrid, useFormValidation) — intentional generic contracts, left as-is
- [x] TODO in `register/page.tsx`: replaced `<button>` + TODO with `<a href="/terms" target="_blank">` and `<a href="/privacy" target="_blank">` (pages exist from Phase XIV)
- [x] TODO in `portfolio/page.tsx`: removed `lastAuditDate` TODO comment (activity logs not yet implemented)
- [x] Decomposition candidates documented (5 components): practice/page.tsx (665), AdjustmentEntryForm (478), FollowUpItemsTable (428), SensitivityToolbar (415), AdjustmentList (415)
- [x] `npm run build` — passes (36 routes, 0 errors)

---

### Sprint 216 — Phase XXVIII Wrap — Regression + Documentation

> **Complexity:** 2/10
> **Goal:** Full regression, update documentation, archive phase details.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Full `pytest` regression | HIGH | COMPLETE |
| 2 | Full `npm run build` verification | HIGH | COMPLETE |
| 3 | Update CLAUDE.md with Phase XXVIII summary | LOW | COMPLETE |
| 4 | Archive Phase XXVIII details | LOW | COMPLETE |
| 5 | Update MEMORY.md | LOW | COMPLETE |

#### Checklist

- [x] `pytest` — 2,903 passed, 0 regressions
- [x] `npm run build` — 36 routes, 0 errors
- [x] CLAUDE.md: Phase XXVIII summary added to completed phases
- [x] Archive detailed checklists to `tasks/archive/phase-xxviii-details.md`
- [x] MEMORY.md: update project status

#### Review — Sprint 216

**Files Created:**
- `tasks/archive/phase-xxviii-details.md` — Phase XXVIII detailed checklists archive

**Files Modified:**
- `tasks/todo.md` — Sprint 216 marked COMPLETE, Phase XXVIII moved to completed phases
- `CLAUDE.md` — Phase XXVIII summary added, current phase updated
- `memory/MEMORY.md` — Project status updated

---

## Phase XXIX — API Integration Hardening (Sprints 217–223)

> **Status:** PLANNED
> **Source:** Comprehensive 4-agent API integration audit (2026-02-14) — API client consistency, TS/Pydantic type drift, error handling patterns, loading/error/empty state consistency
> **Strategy:** Backend type safety first (highest ROI — silent runtime failures), then frontend error handling, then UI state consistency, then infrastructure guardrails
> **Scope:** 15 `response_model=dict` → typed Pydantic models, Literal/Enum tightening, apiClient 422 parsing, CSRF gaps, UI state standardization, contract test infrastructure

### Audit Findings Summary

| Category | Finding | Count | Severity |
|----------|---------|:-----:|----------|
| **Type Safety** | Testing tool endpoints return `response_model=dict` (no validation) | 15 | CRITICAL |
| **Type Safety** | Engagement/follow-up use `str` where frontend expects `Literal` unions | 5 fields | MEDIUM |
| **Type Safety** | `FluxAnalysisResponse` nested `flux: dict, recon: dict` untyped | 2 fields | HIGH |
| **Error Handling** | No Pydantic 422 validation error parsing in apiClient | 1 | HIGH |
| **Error Handling** | `useSettings` mutations fail silently (no try/catch) | 3+ calls | HIGH |
| **Error Handling** | Missing `isAuthError()` checks in hooks | 3 hooks | MEDIUM |
| **Error Handling** | `downloadBlob.ts` bypasses apiClient — missing CSRF | 1 file | HIGH |
| **Error Handling** | Logout endpoint missing CSRF token | 1 call | MEDIUM |
| **UI States** | Portfolio/Engagements error states lack retry buttons | 2 pages | LOW |
| **UI States** | Trial-balance error styling uses hardcoded colors not theme tokens | 1 page | LOW |
| **UI States** | Settings profile loading spinner has no loading text | 1 page | LOW |
| **Infrastructure** | No API contract tests validating response shapes | — | MEDIUM |
| **Infrastructure** | No OpenAPI → TypeScript generation (types manually maintained) | — | MEDIUM |

### Sprint 217 — Backend Response Models: Diagnostic Tools — COMPLETE

> **Complexity:** 5/10
> **Goal:** Replace `response_model=dict` with typed Pydantic models for Trial Balance, Flux Analysis, Prior Period, Multi-Period, and Adjustments. These are the diagnostic core — highest traffic endpoints.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create Pydantic response models for Trial Balance audit result | CRITICAL | COMPLETE |
| 2 | Type `FluxAnalysisResponse` nested dicts (`flux: FluxData`, `recon: ReconData`) | HIGH | COMPLETE |
| 3 | Create Pydantic response models for Prior Period comparison | HIGH | COMPLETE |
| 4 | Create Pydantic response models for Multi-Period (2-way + 3-way) | HIGH | COMPLETE |
| 5 | Create Pydantic response models for Adjustments (`/{entry_id}` GET + `/apply` POST) | MEDIUM | COMPLETE |
| 6 | Update route decorators with new `response_model=` | HIGH | COMPLETE |

#### Checklist

- [x] Audit `audit_engine.py` `to_dict()` output shape → create `TrialBalanceResponse(BaseModel)` with 12 nested models
- [x] Audit `FluxAnalysisResponse` nested dict shapes → create `FluxDataResponse`, `ReconDataResponse` with `FluxItemResponse`, `ReconScoreResponse`
- [x] Audit `prior_period_comparison.py` → create `PeriodComparisonResponse` with `CategoryVarianceResponse`, `RatioVarianceResponse`, `DiagnosticVarianceResponse`
- [x] Audit `multi_period_comparison.py` → create `MovementSummaryResponse` (2-way), `ThreeWayMovementSummaryResponse` (3-way) with nested movement/lead-sheet models
- [x] Audit `adjusting_entries.py` → create `AdjustingEntryResponse`, `AdjustedTrialBalanceResponse` with line/account/totals sub-models
- [x] New file: `backend/shared/diagnostic_response_schemas.py` (~370 lines, 32 Pydantic models)
- [x] Update 7 route decorators: `response_model=dict` → typed models across 4 files
- [x] `TrialBalanceResponse` and `AbnormalBalanceResponse` use `extra="allow"` for safe migration (extra fields pass through)
- [x] `pytest` — 2,903 passed, 0 regressions
- [x] `npm run build` — passes (36 routes)

#### Review — Sprint 217

**Files Created:**
- `backend/shared/diagnostic_response_schemas.py` — 32 Pydantic response models for 5 diagnostic tools

**Files Modified:**
- `backend/routes/audit.py` — Import new schemas, replace `response_model=dict` on `/audit/trial-balance`, move `FluxAnalysisResponse` to shared schemas
- `backend/routes/prior_period.py` — Import `PeriodComparisonResponse`, replace `response_model=dict` on `/audit/compare`
- `backend/routes/multi_period.py` — Import 2 schemas, replace `response_model=dict` on `/audit/compare-periods` and `/audit/compare-three-way`
- `backend/routes/adjustments.py` — Import 2 schemas, replace `response_model=dict` on `/audit/adjustments/{entry_id}` and `/audit/adjustments/apply`

**Model Inventory (32 models in 5 sections):**
- Flux: `FluxItemResponse`, `FluxSummaryResponse`, `FluxDataResponse`, `ReconScoreResponse`, `ReconStatsResponse`, `ReconDataResponse`, `FluxAnalysisResponse`
- Prior Period: `CategoryVarianceResponse`, `RatioVarianceResponse`, `DiagnosticVarianceResponse`, `PeriodComparisonResponse`
- Multi-Period: `AccountMovementResponse`, `LeadSheetMovementSummaryResponse`, `MovementSummaryResponse`, `BudgetVarianceResponse`, `ThreeWayLeadSheetSummaryResponse`, `ThreeWayMovementSummaryResponse`
- Adjustments: `AdjustmentLineResponse`, `AdjustingEntryResponse`, `AdjustedAccountBalanceResponse`, `AdjustedTBTotalsResponse`, `AdjustedTrialBalanceResponse`
- Trial Balance: `AbnormalBalanceSuggestionResponse`, `AbnormalBalanceResponse`, `RiskSummaryAnomalyTypesResponse`, `RiskSummaryResponse`, `ClassificationIssueResponse`, `ClassificationQualityResponse`, `ColumnDetectionResponse`, `BalanceSheetValidationResponse`, `SheetResultResponse`, `TrialBalanceResponse`

**Endpoints migrated (7):**
- `POST /audit/trial-balance` → `TrialBalanceResponse`
- `POST /audit/flux` → `FluxAnalysisResponse` (typed nested dicts)
- `POST /audit/compare` → `PeriodComparisonResponse`
- `POST /audit/compare-periods` → `MovementSummaryResponse`
- `POST /audit/compare-three-way` → `ThreeWayMovementSummaryResponse`
- `GET /audit/adjustments/{entry_id}` → `AdjustingEntryResponse`
- `POST /audit/adjustments/apply` → `AdjustedTrialBalanceResponse`

---

### Sprint 218 — Backend Response Models: Testing Tools Batch 1 — COMPLETE

> **Complexity:** 5/10
> **Goal:** Add Pydantic response models for JE Testing, AP Testing, Bank Rec, Three-Way Match, and AR Aging. These 5 tools have the most complex nested result structures.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create Pydantic response models for JE Testing result + sampling result | CRITICAL | COMPLETE |
| 2 | Create Pydantic response models for AP Testing result | CRITICAL | COMPLETE |
| 3 | Create Pydantic response models for Bank Rec result | CRITICAL | COMPLETE |
| 4 | Create Pydantic response models for Three-Way Match result | CRITICAL | COMPLETE |
| 5 | Create Pydantic response models for AR Aging result | CRITICAL | COMPLETE |
| 6 | Create shared sub-models: `CompositeScoreResponse`, `DataQualityResponse`, `BenfordAnalysisResponse` | HIGH | COMPLETE |
| 7 | Update 6 route decorators with new `response_model=` | HIGH | COMPLETE |

#### Checklist

- [x] Audit `je_testing_engine.py` result dataclass → create `JETestingResponse` with nested `BenfordAnalysisResponse`, `SamplingResultResponse`
- [x] Audit `ap_testing_engine.py` result dataclass → create `APTestingResponse`
- [x] Audit `bank_reconciliation.py` result shape → create `BankRecResponse`
- [x] Audit `three_way_match_engine.py` result dataclass → create `ThreeWayMatchResponse`
- [x] Audit `ar_aging_engine.py` result dataclass → create `ARAgingResponse`
- [x] Extract shared nested schemas: `CompositeScoreResponse`, `DataQualityResponse`, `BenfordAnalysisResponse`
- [x] Place in `backend/shared/testing_response_schemas.py` (~500 lines, 42 models)
- [x] Update 6 route decorators: add/replace `response_model=` (JE×2, AP, Bank Rec, TWM, AR Aging)
- [x] `pytest` — 2,903 passed, 0 regressions
- [x] `npm run build` — passes (36 routes)

#### Review — Sprint 218

**Files Created:**
- `backend/shared/testing_response_schemas.py` — 42 Pydantic response models for 5 testing tools

**Files Modified:**
- `backend/routes/je_testing.py` — Import `JETestingResponse`, `SamplingResultResponse`; replace `response_model=dict` on 2 endpoints
- `backend/routes/ap_testing.py` — Import `APTestingResponse`; add `response_model=` on 1 endpoint
- `backend/routes/bank_reconciliation.py` — Import `BankRecResponse`; replace `response_model=dict` on 1 endpoint
- `backend/routes/three_way_match.py` — Import `ThreeWayMatchResponse`; replace `response_model=dict` on 1 endpoint
- `backend/routes/ar_aging.py` — Import `ARAgingResponse`; add `response_model=` on 1 endpoint

**Model Inventory (42 models in 6 sections):**
- Shared (3): `CompositeScoreResponse`, `DataQualityResponse`, `BenfordAnalysisResponse`
- JE Testing (9): `JournalEntryResponse`, `JEFlaggedEntryResponse`, `JETestResultResponse`, `GLColumnDetectionResponse`, `MultiCurrencyWarningResponse`, `SamplingStratumResponse`, `SamplingResultResponse`, `JETestingResponse`
- AP Testing (5): `APPaymentResponse`, `APFlaggedEntryResponse`, `APTestResultResponse`, `APColumnDetectionResponse`, `APTestingResponse`
- Bank Rec (5): `TransactionResponse`, `ReconciliationMatchResponse`, `ReconciliationSummaryResponse`, `BankColumnDetectionResponse`, `BankRecResponse`
- Three-Way Match (11): `PurchaseOrderResponse`, `InvoiceResponse`, `ReceiptResponse`, `MatchVarianceResponse`, `ThreeWayMatchItemResponse`, `UnmatchedDocumentResponse`, `ThreeWayMatchSummaryResponse`, `ThreeWayMatchDataQualityResponse`, `ThreeWayMatchConfigResponse`, `POColumnDetectionResponse`, `InvoiceColumnDetectionResponse`, `ReceiptColumnDetectionResponse`, `TWMColumnDetectionResponse`, `ThreeWayMatchResponse`
- AR Aging (9): `AREntryResponse`, `ARFlaggedEntryResponse`, `ARTestResultResponse`, `ARCompositeScoreResponse`, `ARDataQualityResponse`, `ARTBColumnDetectionResponse`, `ARSLColumnDetectionResponse`, `ARSummaryResponse`, `ARAgingResponse`

**Endpoints migrated (6):**
- `POST /audit/journal-entries` → `JETestingResponse` (was `dict`)
- `POST /audit/journal-entries/sample` → `SamplingResultResponse` (was `dict`)
- `POST /audit/ap-payments` → `APTestingResponse` (was missing)
- `POST /audit/bank-reconciliation` → `BankRecResponse` (was `dict`)
- `POST /audit/three-way-match` → `ThreeWayMatchResponse` (was `dict`)
- `POST /audit/ar-aging` → `ARAgingResponse` (was missing)

---

### Sprint 219 — Backend Response Models: Testing Tools Batch 2 + Enum Tightening — COMPLETE

> **Complexity:** 5/10
> **Goal:** Add Pydantic response models for Payroll, Revenue, Fixed Asset, Inventory. Tighten string fields to Literal/Enum types in Engagement and Follow-Up models.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create Pydantic response models for Payroll Testing result | CRITICAL | COMPLETE |
| 2 | Create Pydantic response models for Revenue Testing result | CRITICAL | COMPLETE |
| 3 | Create Pydantic response models for Fixed Asset Testing result | CRITICAL | COMPLETE |
| 4 | Create Pydantic response models for Inventory Testing result | CRITICAL | COMPLETE |
| 5 | Tighten `EngagementResponse.status` to `Literal['active', 'archived']` | MEDIUM | COMPLETE |
| 6 | Tighten `EngagementResponse.materiality_basis` to `Optional[Literal['revenue', 'assets', 'manual']]` | MEDIUM | COMPLETE |
| 7 | Tighten `FollowUpItemResponse.severity` and `.disposition` to Literal types | MEDIUM | COMPLETE |
| 8 | Tighten `settings.py` materiality preview to typed response | LOW | COMPLETE |
| 9 | Tighten `engagements.py` workpaper-index to typed response | LOW | COMPLETE |

#### Checklist

- [x] Audit `payroll_testing_engine.py` result dataclass → create `PayrollTestingResponse(BaseModel)` (7 models)
- [x] Audit `revenue_testing_engine.py` result dataclass → create `RevenueTestingResponse(BaseModel)` (5 models)
- [x] Audit `fixed_asset_testing_engine.py` result dataclass → create `FATestingResponse(BaseModel)` (5 models)
- [x] Audit `inventory_testing_engine.py` result dataclass → create `InvTestingResponse(BaseModel)` (5 models)
- [x] Update 4 route decorators: add `response_model=` (Payroll, Revenue, FA, Inventory)
- [x] `engagements.py`: `status: str` → `status: Literal['active', 'archived']`
- [x] `engagements.py`: `materiality_basis: Optional[str]` → `Optional[Literal['revenue', 'assets', 'manual']]`
- [x] `follow_up_items.py`: `severity: str` → `severity: Literal['high', 'medium', 'low']`
- [x] `follow_up_items.py`: `disposition: str` → `disposition: Literal['not_reviewed', 'investigated_no_issue', 'investigated_adjustment_posted', 'investigated_further_review', 'immaterial']`
- [x] `settings.py`: `/materiality/preview` → `MaterialityPreviewResponse`
- [x] `engagements.py`: `/workpaper-index` → `WorkpaperIndexResponse` (4 nested models)
- [x] `pytest` — 2,903 passed, 0 regressions
- [x] `npm run build` — passes (36 routes)

#### Review — Sprint 219

**Files Modified:**
- `backend/shared/testing_response_schemas.py` — Added 22 Pydantic response models for 4 testing tools (Payroll: 7, Revenue: 5, FA: 5, Inventory: 5)
- `backend/routes/payroll_testing.py` — Import `PayrollTestingResponse`; add `response_model=` on POST endpoint
- `backend/routes/revenue_testing.py` — Import `RevenueTestingResponse`; add `response_model=` on POST endpoint
- `backend/routes/fixed_asset_testing.py` — Import `FATestingResponse`; add `response_model=` on POST endpoint
- `backend/routes/inventory_testing.py` — Import `InvTestingResponse`; add `response_model=` on POST endpoint
- `backend/routes/engagements.py` — Tighten `status`/`materiality_basis` to Literal types; add 4 WorkpaperIndex response models; replace `response_model=dict` on workpaper-index
- `backend/routes/follow_up_items.py` — Tighten `severity`/`disposition` to Literal types (5-value disposition union)
- `backend/routes/settings.py` — Add `MaterialityPreviewResponse`; replace `response_model=dict` on materiality preview

**Model Inventory (22 new models in testing_response_schemas.py):**
- Payroll (7): `PayrollEntryResponse`, `PayrollFlaggedEntryResponse`, `PayrollTestResultResponse`, `PayrollColumnDetectionResponse`, `PayrollCompositeScoreResponse`, `PayrollTestingResponse`
- Revenue (5): `RevenueEntryResponse`, `RevenueFlaggedEntryResponse`, `RevenueTestResultResponse`, `RevenueColumnDetectionResponse`, `RevenueTestingResponse`
- Fixed Asset (5): `FixedAssetEntryResponse`, `FAFlaggedEntryResponse`, `FATestResultResponse`, `FAColumnDetectionResponse`, `FATestingResponse`
- Inventory (5): `InventoryEntryResponse`, `InvFlaggedEntryResponse`, `InvTestResultResponse`, `InvColumnDetectionResponse`, `InvTestingResponse`

**Additional models (6):**
- engagements.py: `WorkpaperDocumentResponse`, `WorkpaperFollowUpSummaryResponse`, `WorkpaperSignOffResponse`, `WorkpaperIndexResponse`
- settings.py: `MaterialityPreviewResponse`

**Endpoints migrated (6):**
- `POST /audit/payroll-testing` → `PayrollTestingResponse` (was missing)
- `POST /audit/revenue-testing` → `RevenueTestingResponse` (was missing)
- `POST /audit/fixed-assets` → `FATestingResponse` (was missing)
- `POST /audit/inventory-testing` → `InvTestingResponse` (was missing)
- `GET /engagements/{id}/workpaper-index` → `WorkpaperIndexResponse` (was `dict`)
- `POST /settings/materiality/preview` → `MaterialityPreviewResponse` (was `dict`)

**Enum tightening (4 fields):**
- `EngagementResponse.status`: `str` → `Literal['active', 'archived']`
- `EngagementResponse.materiality_basis`: `Optional[str]` → `Optional[Literal['revenue', 'assets', 'manual']]`
- `FollowUpItemResponse.severity`: `str` → `Literal['high', 'medium', 'low']`
- `FollowUpItemResponse.disposition`: `str` → `Literal[5 values]`

---

### Sprint 220 — Frontend Error Handling Hardening

> **Complexity:** 4/10
> **Goal:** Fix apiClient 422 parsing, add missing auth error checks, fix silent mutations, migrate legacy download utility, close CSRF gaps.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Fix `apiClient.ts` 422 parsing to handle Pydantic `detail` array format | HIGH | |
| 2 | Add `isAuthError()` checks to `useTrends`, `useSettings`, `useBenchmarks` | MEDIUM | |
| 3 | Add try/catch error surfacing to `useSettings` silent mutations | HIGH | |
| 4 | Migrate `lib/downloadBlob.ts` to use `apiDownload()` | HIGH | |
| 5 | Add CSRF token to logout endpoint in `AuthContext.tsx` | MEDIUM | |
| 6 | Add `instanceof Error` checks in catch blocks (`useBenchmarks`, `useTrends`) | LOW | |

#### Checklist

- [ ] `apiClient.ts` (~line 487): detect `Array.isArray(detail)` → extract first item's `msg` field for Pydantic 422 responses
- [ ] `useTrends.ts`: add `isAuthError(status)` check before generic error message
- [ ] `useSettings.ts`: add `isAuthError(status)` check; wrap `fetchClientSettings`, `updateClientSettings`, `previewMateriality` in try/catch with error state
- [ ] `useBenchmarks.ts`: add `isAuthError(status)` check; use `err instanceof Error ? err.message : String(err)` in catch
- [ ] `lib/downloadBlob.ts`: replace direct `fetch()` with `apiDownload()` call from apiClient (gains CSRF, retry, timeout)
- [ ] `AuthContext.tsx` (~line 293): inject `getCsrfToken()` into logout fetch headers as `'X-CSRF-Token'`
- [ ] `useTrends.ts`: use `err instanceof Error` type guard in catch block
- [ ] `useBenchmarks.ts`: use `err instanceof Error` type guard in catch block
- [ ] `npm run build` — passes
- [ ] Manual smoke test: trigger 422 on login with invalid email → verify user sees field-level message

---

### Sprint 221 — UI State Consistency

> **Complexity:** 3/10
> **Goal:** Standardize loading, error, and empty states across all data-fetching pages. Add missing retry buttons, use theme tokens consistently, add loading text where missing.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Add retry button to Portfolio error state | LOW | |
| 2 | Add retry button to Engagements error state | LOW | |
| 3 | Standardize trial-balance error styling to `theme-error-bg`/`theme-error-border` tokens | LOW | |
| 4 | Add loading text to settings profile spinner | LOW | |
| 5 | Standardize history.tsx spinner from framer-motion to CSS `animate-spin` | LOW | |
| 6 | Add retry actions to settings form error states (profile + practice) | LOW | |

#### Checklist

- [ ] `portfolio/page.tsx` (~line 181): add "Try Again" button with `onClick={refetch}`, clay icon, animation — match tool page error pattern
- [ ] `engagements/page.tsx` (~line 299): add "Try Again" button with `onClick={refetch}`, clay icon, animation — match tool page error pattern
- [ ] `trial-balance/page.tsx` (~line 152): replace `bg-clay-50` with `bg-theme-error-bg border-theme-error-border` semantic tokens
- [ ] `settings/profile/page.tsx` (~line 120): add `<span>Loading profile...</span>` next to spinner
- [ ] `history/page.tsx` (~line 136): replace `motion.div animate={{ rotate: 360 }}` with CSS `animate-spin` class on spinner div
- [ ] `settings/profile/page.tsx`, `settings/practice/page.tsx`: add dismiss or retry button on form error banners
- [ ] Verify all error states have `role="alert"` for accessibility
- [ ] `npm run build` — passes

---

### Sprint 222 — API Contract Tests + Type Generation Infrastructure

> **Complexity:** 4/10
> **Goal:** Add response shape validation tests and set up OpenAPI → TypeScript generation pipeline to prevent future type drift.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Create `backend/tests/test_api_contracts.py` — validate response shapes for all testing tools | MEDIUM | |
| 2 | Add contract tests for engagement + follow-up response shapes | MEDIUM | |
| 3 | Add contract tests for flux/recon/prior-period/multi-period response shapes | MEDIUM | |
| 4 | Set up `frontend/scripts/generate-types.sh` — OpenAPI → TypeScript generation | MEDIUM | |
| 5 | Add `npm run generate:types` script to `package.json` | LOW | |
| 6 | Document type generation workflow in README or developer docs | LOW | |

#### Checklist

- [ ] `test_api_contracts.py`: test each testing tool response contains expected top-level keys (`composite_score`, `test_results`, `data_quality`, etc.)
- [ ] Validate enum values: `risk_tier` in allowed set, `severity` in `['high', 'low']`, `test_tier` in allowed set
- [ ] Validate nested structure: `benford_result` has `mad`, `chi_squared`, `expected_distribution`, `actual_distribution` when present
- [ ] Engagement contract tests: `status` in `['active', 'archived']`, `materiality_basis` in `['revenue', 'assets', 'manual', null]`
- [ ] Follow-up contract tests: `severity` in `['high', 'medium', 'low']`, `disposition` matches frontend union
- [ ] Flux/Recon/Prior/Multi contract tests: validate nested field presence
- [ ] `generate-types.sh`: `npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api-generated.ts`
- [ ] `package.json`: add `"generate:types": "bash scripts/generate-types.sh"` script
- [ ] Document: when to regenerate types (after backend model changes), how to diff against manual types
- [ ] `pytest` — all tests pass including new contract tests

---

### Sprint 223 — Phase XXIX Wrap — Regression + Documentation

> **Complexity:** 2/10
> **Goal:** Full regression, update project documentation, archive phase details.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Full `pytest` regression | HIGH | |
| 2 | Full `npm run build` verification | HIGH | |
| 3 | Run generated types and diff against manual types | MEDIUM | |
| 4 | Update CLAUDE.md with Phase XXIX summary | LOW | |
| 5 | Archive Phase XXIX details | LOW | |
| 6 | Update MEMORY.md | LOW | |

#### Checklist

- [ ] `pytest` — all tests pass, 0 regressions
- [ ] `npm run build` — passes
- [ ] `npm run generate:types` — runs successfully, diff reviewed
- [ ] CLAUDE.md: Phase XXIX summary added to completed phases, current phase updated
- [ ] Archive detailed checklists to `tasks/archive/phase-xxix-details.md`
- [ ] MEMORY.md: update project status, add API contract test patterns
- [ ] Deferred items table: update any resolved/new items
