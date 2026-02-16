# Phase XXXV: In-Memory State Fix + Codebase Hardening

> **Sprints:** 261–266 + T1
> **Focus:** Fix production bugs identified in full-stack audit. No new features.
> **Source:** Phase 1 Audit (2026-02-15) + SESSION_HANDOFF 8-packet plan
> **Result:** All 8 security packets validated complete. Tests: 3,323 backend + 724 frontend.

---

## Sprint 261: CSRF Stateless HMAC + DB-Backed Account Lockout — COMPLETE
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

## Sprint 262: Tool Session Data → DB-Backed (ToolSession) — COMPLETE
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

## Sprint 263: Float Precision Fixes in audit_engine.py — COMPLETE
- [x] Fix 1: `check_balance()` — `float(debits.sum())` → `math.fsum(debits.values)`
- [x] Fix 2: `StreamingAuditor` — chunk-list accumulation with `math.fsum()` instead of running float addition
- [x] Fix 3: Concentration percentage — keep division in Decimal, convert to float only at serialization
- [x] Fix 4: Rounding detection — Decimal modulo instead of float `%`
- [x] ActivityLog/DiagnosticSummary Float columns — assessed: Float64 sufficient (15-16 sig digits, values < $10T, metadata-only, not used in downstream calcs)
- [x] 21 new precision edge-case tests (trillions, 0.1+0.2 patterns, streaming cross-chunk, concentration, rounding boundaries)
- [x] 2 existing tests updated (`test_running_totals_single_chunk`, `test_clear_releases_memory` → use public API)
- [x] Backend tests: 3,202 passed (was 3,181)

## Sprint 264: Database Timestamp Defaults — COMPLETE
- [x] Add `func` import to models.py, engagement_model.py, follow_up_items_model.py
- [x] Add `server_default=func.now()` to 14 timestamp columns (User, ActivityLog, Client, DiagnosticSummary, EmailVerificationToken, RefreshToken, Engagement, ToolRun, FollowUpItem, FollowUpItemComment)
- [x] ToolSession already has server_default — skip
- [x] Alembic migration `0f1346198438` (hand-written, batch_alter_table for SQLite compat)
- [x] 24 new tests: 17 DDL inspection + 5 functional DB-insert + 2 UTC verification
- [x] Backend tests: 3,226 passed (was 3,202)
- [x] Frontend build: passes

## Sprint 265: Dependency Updates — COMPLETE
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

## Sprint T1: Foundation Hardening — COMPLETE
- [x] Deep health probe: `GET /health?deep=true` performs `SELECT 1` DB check, returns 503 on failure
- [x] CI enforcement: split pip-audit/npm-audit into advisory (continue-on-error) + blocking (fail on HIGH/CRITICAL)
- [x] Dependabot: `.github/dependabot.yml` for pip + npm + github-actions, weekly schedule, grouped minor/patch
- [x] SAST: Bandit CI job (`bandit -r . -ll --exclude ./tests,./venv`), blocks on HIGH severity + HIGH/MEDIUM confidence
- [x] Config fix: removed duplicate `ENV_MODE` assignment (was at lines 59 and 92, now only line 59)
- [x] 3 new health tests (shallow no-DB field, deep 200 connected, deep 503 unreachable)
- [x] Backend tests: 3,323 passed (was 3,226)
- [x] Frontend build: passes
- [x] Bandit local run: 0 HIGH findings in source code (22 in venv excluded)

## Sprint 266: Zero-Storage Language Truthfulness — COMPLETE
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

## SESSION_HANDOFF Packet Validation (8/8 Complete)

| Packet | Description | Resolution |
|--------|-------------|------------|
| P1 | Truthful zero-storage language | Sprint 266 — approach/page.tsx qualified, trust/page.tsx already accurate |
| P2 | Tool sessions → DB | Sprint 262 — ToolSession model, financial key stripping, TTL cleanup |
| P3 | Upload zip bomb resistance | Already complete — multi-layer (110MB body, 100MB file, 10K ZIP entries, 1GB decompressed, 100:1 ratio) |
| P4 | Rate-limit normalization | Already complete — 100% endpoint coverage (84/84), global 60/min default |
| P5 | Production DB safety | Already complete — SQLite block in production, dialect-aware upsert, PostgreSQL documented |
| P6 | CSRF/JWT secret separation | Sprint 261 — stateless HMAC CSRF, separate CSRF_SECRET_KEY, production enforcement |
| P7 | Logging redaction | Sprint T1 — behavioral tests for token/PII redaction |
| P8 | Retention enforcement | Already complete — 365-day configurable retention, startup cleanup job |

---

## Sprint 267: Phase XXXV Wrap — COMPLETE
- [x] Backend regression: 3,323 passed
- [x] Frontend regression: 724 passed (includes 15 previously untracked component test files + float precision tests)
- [x] Frontend build: passes
- [x] Archive sprint checklists to `tasks/archive/phase-xxxv-details.md`
- [x] Add one-line summary to `## Completed Phases` in `tasks/todo.md`
- [x] Clear `## Active Phase` section
- [x] Update CLAUDE.md: phase status, test counts, completed phases list
- [x] Update MEMORY.md: project status
- [x] Fix Forward Roadmap numbering: Phase XXXV → XXXVI (Statistical Sampling), Phase XXXVI → XXXVII (Deployment Hardening)
- [x] Include 15 untracked frontend test files + uncommitted Sprint 263 float precision changes
- [x] Commit all changes
