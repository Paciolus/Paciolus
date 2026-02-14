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

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md` | `tasks/archive/phases-xiii-xvii-details.md` | `tasks/archive/phase-xviii-details.md` | `tasks/archive/phases-xix-xxiii-details.md` | `tasks/archive/phases-xxiv-xxvi-details.md` | `tasks/archive/phase-xxvii-details.md`

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

> **Status:** IN PROGRESS
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
| 1 | Create `backend/logging_config.py` — structured logger configuration | HIGH | PENDING |
| 2 | Add request ID middleware for log correlation | MEDIUM | PENDING |
| 3 | Add loggers to startup events, auth flows, error handlers | HIGH | PENDING |
| 4 | Add loggers to export routes (where most broad exceptions live) | HIGH | PENDING |

#### Checklist

- [ ] `logging_config.py`: `setup_logging()` — structured JSON format for production, human-readable for dev
- [ ] Per-module loggers: `logger = logging.getLogger(__name__)` pattern
- [ ] Request ID middleware: generate UUID per request, attach to log context
- [ ] Startup logging: server start, DB connection, cleanup job results
- [ ] Auth logging: login success/failure, token refresh, password change (no PII)
- [ ] Export error logging: replace silent `except Exception` with `logger.exception()`
- [ ] Wire `setup_logging()` in `main.py` startup
- [ ] `pytest` — 2,903+ passed, 0 regressions

---

### Sprint 212 — Exception Narrowing (Export Routes)

> **Complexity:** 4/10
> **Goal:** Replace 54 broad `except Exception` blocks with specific exception types. Log actual errors instead of swallowing them.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Audit all 54 `except Exception` locations — categorize by exception type | HIGH | PENDING |
| 2 | Narrow exceptions in `export_testing.py` (~20 locations) | HIGH | PENDING |
| 3 | Narrow exceptions in `export_diagnostics.py` (~8 locations) | HIGH | PENDING |
| 4 | Narrow exceptions in `export_memos.py` (~10 locations) | MEDIUM | PENDING |
| 5 | Narrow exceptions in remaining route files (~16 locations) | MEDIUM | PENDING |

#### Checklist

- [ ] Map each `except Exception` to specific types: `ValueError`, `KeyError`, `pd.errors.*`, `IOError`, `ReportLabError`
- [ ] Pattern: `except (ValueError, KeyError) as e: logger.error(f"Export failed: {e}"); raise HTTPException(500, detail="Export failed")`
- [ ] Remove any bare `pass` in exception handlers — always log
- [ ] Export routes: catch Pandas errors (`pd.errors.EmptyDataError`, `pd.errors.ParserError`) separately
- [ ] PDF routes: catch ReportLab errors separately from data errors
- [ ] `pytest` — 2,903+ passed, 0 regressions

---

### Sprint 213 — Backend Return Type Annotations

> **Complexity:** 3/10
> **Goal:** Add return type annotations to 68+ functions missing them. Improves IDE support and catches type mismatches.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Add return types to `auth.py` functions | MEDIUM | PENDING |
| 2 | Add return types to `shared/` module functions | MEDIUM | PENDING |
| 3 | Add return types to engine module functions | MEDIUM | PENDING |
| 4 | Add return types to route handler helpers | LOW | PENDING |

#### Checklist

- [ ] `auth.py`: all public functions get `-> ReturnType`
- [ ] `shared/*.py`: all exported functions get `-> ReturnType`
- [ ] Engine modules: `audit_engine.py`, `financial_statement_builder.py`, etc.
- [ ] Memo generators: all `generate_*` functions
- [ ] Route helpers: internal functions used by endpoints
- [ ] Use `-> None` for void functions, not omission
- [ ] `pytest` — 2,903+ passed, 0 regressions

---

### Sprint 214 — Deprecated Pattern Migration

> **Complexity:** 3/10
> **Goal:** Migrate 2 deprecated SQLAlchemy/FastAPI patterns to modern equivalents.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Migrate `declarative_base()` → `DeclarativeBase` class (SQLAlchemy 2.0) | MEDIUM | PENDING |
| 2 | Migrate `@app.on_event("startup")` → `lifespan` context manager | MEDIUM | PENDING |
| 3 | Extract hardcoded config values to environment variables | LOW | PENDING |

#### Checklist

- [ ] `database.py`: `Base = declarative_base()` → `class Base(DeclarativeBase): pass`
- [ ] Verify all models still inherit correctly from new `Base`
- [ ] `main.py`: `@app.on_event("startup")` → `@asynccontextmanager async def lifespan(app):`
- [ ] Move startup cleanup jobs (refresh tokens, verification tokens) into lifespan
- [ ] Config: `FRONTEND_URL` default, rate limit strings → `config.py` constants
- [ ] Alembic `env.py`: update `Base` import if changed
- [ ] `pytest` — 2,903+ passed, 0 regressions
- [ ] `npm run build` — passes

---

### Sprint 215 — Frontend Type Safety + TODO Cleanup

> **Complexity:** 2/10
> **Goal:** Eliminate 4 `any` types in production code, resolve 3 TODO comments, assess large components.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Replace 4 `any` types with proper interfaces | MEDIUM | PENDING |
| 2 | Resolve 3 TODO comments (register modals, portfolio lastAuditDate, etc.) | LOW | PENDING |
| 3 | Document 5 components >400 LOC for future decomposition | LOW | PENDING |

#### Checklist

- [ ] `DownloadReportButton.tsx`: replace `any` in interface props with specific types
- [ ] Remaining `any` locations: audit and replace with `unknown` or proper types
- [ ] TODO in `register/page.tsx`: resolve or remove modal comment
- [ ] TODO in `portfolio/`: resolve `lastAuditDate` placeholder
- [ ] TODO #3: resolve or document
- [ ] Large components (>400 LOC): add `// NOTE: Decomposition candidate — Phase XXIX+` comments
- [ ] `npm run build` — passes

---

### Sprint 216 — Phase XXVIII Wrap — Regression + Documentation

> **Complexity:** 2/10
> **Goal:** Full regression, update documentation, archive phase details.

| # | Task | Severity | Status |
|---|------|----------|--------|
| 1 | Full `pytest` regression | HIGH | PENDING |
| 2 | Full `npm run build` verification | HIGH | PENDING |
| 3 | Update CLAUDE.md with Phase XXVIII summary | LOW | PENDING |
| 4 | Archive Phase XXVIII details | LOW | PENDING |
| 5 | Update MEMORY.md | LOW | PENDING |

#### Checklist

- [ ] `pytest` — all tests pass, 0 regressions
- [ ] `npm run build` — 36+ routes, 0 errors
- [ ] CI pipeline green on main branch
- [ ] CLAUDE.md: Phase XXVIII summary added to completed phases
- [ ] Archive detailed checklists to `tasks/archive/phase-xxviii-details.md`
- [ ] MEMORY.md: update project status, add any new patterns/gotchas
