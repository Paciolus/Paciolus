# Paciolus Daily Digital Excellence Council Report
Date: 2026-03-03
Commit/Branch: fc3733b / main
Files Changed Since Last Audit: N/A (first run)

## 1) Executive Summary
- Total Findings: 7
  - P0 (Stop-Ship): 0
  - P1 (High): 0
  - P2 (Medium): 2
  - P3 (Low): 5
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Test Quality & Determinism**: F-001, F-004 (2 findings)
  - **Zero-Storage Boundary**: F-002 (1 finding)
  - **Type Convention Compliance**: F-003 (1 finding)
  - **Defense-in-Depth Hardening**: F-005 (1 finding)
  - **Deployment Documentation**: F-006 (1 finding)
  - **API Style Consistency**: F-007 (1 finding)
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — Uploaded financial data never persisted; all processing in-memory with gc.collect(); Sentry PII disabled + request bodies stripped; 10-step upload validation pipeline; ToolSession dual-layer sanitization (allowlist + recursive forbidden-key stripping). ExportShare stores derived artifacts (PDF/Excel) for 48h with auto-purge — see F-002.
  - Auth/CSRF Integrity: **PASS** — JWT access tokens in-memory only; HttpOnly secure cookie refresh tokens with rotation + reuse detection; stateless HMAC CSRF (user-bound, 30-min TTL); account lockout (5 attempts / 15 min); bcrypt 12-round hashing; production guardrails (32-char minimum secrets, separate JWT/CSRF keys, TLS-only PostgreSQL, no wildcard CORS).
  - Observability Data Leakage: **PASS** — Sentry `send_default_pii=False` + `before_send` strips request bodies; `log_sanitizer.py` masks emails and fingerprints tokens; Prometheus metrics contain only aggregated statistics (format, tier, event_type labels); `console.log` removed from production frontend builds.

## 2) Daily Checklist Status

1. **Zero-storage enforcement (backend/frontend/logs/telemetry/exports):** ✅ PASS — All upload processing via `io.BytesIO()` with explicit `gc.collect()`; ToolSession enforces allowlist + recursive forbidden-key stripping; Sentry `before_send` strips bodies; frontend uses sessionStorage for metadata only (user profile, command IDs, classification overrides); no `localStorage` usage; ExportShare has 48h auto-purge (F-002).

2. **Upload pipeline threat model (size limits, bombs, MIME, memory):** ✅ PASS — 10-step validation in `shared/helpers.py`: extension whitelist, MIME check, 100MB size cap (chunked read), empty file detection, magic byte validation, ZIP entry limit (10K), nested archive blocking, uncompressed size cap (1GB), compression ratio check (>100:1 rejected), XML bomb detection (DOCTYPE/ENTITY scan). `defusedxml` used for OFX parsing. CWE-1236 formula injection sanitization.

3. **Auth + refresh + CSRF lifecycle coupling:** ✅ PASS — Refresh tokens stored as SHA-256 hashes with rotation + reuse detection (compromise → revoke all); CSRF tokens are stateless HMAC (`nonce:timestamp:user_id:signature`) with 30-min TTL and user binding; `X-Requested-With` header required on refresh; Origin/Referer validation against CORS whitelist; account enumeration prevention via fake lockout info for nonexistent users.

4. **Observability data leakage (Sentry/logs/metrics):** ✅ PASS — Sentry opt-in only (empty DSN default); `send_default_pii=False`; `before_send` replaces request bodies with `"[Stripped — Zero-Storage]"`; `log_sanitizer.py` provides `mask_email()`, `token_fingerprint()`, `sanitize_exception()`; Prometheus labels contain only format names, tier enums, event types — no account data.

5. **OpenAPI/TS type generation + contract drift:** ⚠️ AT RISK — All backend endpoints declare Pydantic `response_model` for OpenAPI; `test_api_contracts.py` validates schemas without HTTP; however, no automated OpenAPI→TypeScript generation pipeline detected. Frontend types are manually maintained in `frontend/src/types/`. Manual sync is error-prone.

6. **CI security gates (Bandit/pip-audit/npm audit/policy):** ✅ PASS — 11-job CI pipeline: Bandit SAST (blocks HIGH), pip-audit (blocks HIGH/CRITICAL), npm-audit (blocks HIGH/CRITICAL), ruff + ESLint baseline gates (zero-tolerance), accounting-policy guards, report-standards validation. Action versions pinned (@v4/@v6/@v7). Advisory jobs properly non-blocking.

7. **APScheduler safety under multi-worker:** ✅ PASS — Single `ThreadPoolExecutor(max_workers=1)` + `coalesce=True` + `max_instances=1`; all cleanup functions idempotent (DELETE WHERE ts < cutoff); cold-start cleanup supplements scheduler. Per-instance scheduler documented in code comments but not in deployment docs (F-006).

8. **Next.js CSP nonce + dynamic rendering:** ✅ PASS — Per-request nonce via `crypto.randomUUID()` in `proxy.ts`; `await headers()` in root layout forces dynamic rendering; production CSP: `script-src 'self' 'nonce-{nonce}' 'strict-dynamic'` (no `unsafe-eval`); `style-src 'unsafe-inline'` retained for React style props (documented in SECURITY_POLICY.md); `frame-src 'none'`, `object-src 'none'`, `base-uri 'self'`.

## 3) Findings Table (Core)

### F-001: Time-Based Test Flakiness in Password Revocation Tests
- **Severity**: P2
- **Category**: Reliability/Observability
- **Evidence**:
  - `backend/tests/test_password_revocation.py:454` — `time.sleep(1.1)`
    - Explanation: Test `test_sequential_password_changes_invalidate_older_tokens` uses `time.sleep(1.1)` to create timestamp separation between password changes. Under CI load or slow VMs, 1.1 seconds may be insufficient, causing intermittent failures. JWT `pwd_at` claims depend on second-level timestamp granularity; if sleep doesn't advance the clock enough (due to OS scheduling), tokens won't differ.
- **Impact**: Intermittent CI failures → developer frustration, false negatives in security test coverage, potential for "retry and merge" culture that masks real regressions.
- **Recommendation**: Replace `time.sleep()` with deterministic time mocking. Use `unittest.mock.patch` or `freezegun` to control timestamps explicitly, ensuring tests are independent of wall-clock timing.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Eliminate time.sleep flakiness in password revocation tests by mocking time
  Files in scope: backend/tests/test_password_revocation.py
  Approach: Replace time.sleep(1.1) with freezegun or unittest.mock.patch on datetime/time to advance clock deterministically. Ensure JWT pwd_at claims differ by at least 2 seconds in mock time. Verify test still validates that older tokens are invalidated after password change.
  Acceptance criteria:
  - Test passes deterministically without any time.sleep calls
  - No flakiness in 100 consecutive runs
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Verification Marshal (I)
- **Supporting Agents**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Digital Fortress (D): "Not a security vulnerability; P3 is sufficient for a test convenience issue."

---

### F-002: ExportShare Stores Derived Financial Data for 48 Hours
- **Severity**: P2
- **Category**: Zero-Storage
- **Evidence**:
  - `backend/export_share_model.py:40` — `export_data = Column(LargeBinary, nullable=False)`
    - Explanation: ExportShare model stores generated PDF/Excel/CSV export bytes in a `LargeBinary` database column. While these are derived artifacts (not raw uploads), they contain financial analysis results: account names, balances, anomaly details, ratio calculations. Data persists for up to 48 hours (`expires_at` TTL) before auto-purge by `cleanup_scheduler.py`.
  - `backend/routes/export_sharing.py:56-85` — Export creation flow
    - Explanation: Users on Professional+ tier can create shareable export links. The generated export bytes are stored in the database with a 48h expiry. Access requires a token hash match.
  - `backend/cleanup_scheduler.py` — `_job_expired_export_shares()` runs hourly
    - Explanation: Expired shares are soft-deleted on a 1-hour cleanup cycle. Maximum data lifetime: ~49 hours (48h TTL + up to 1h cleanup lag).
- **Impact**: Temporary departure from zero-storage for derived financial data. If database is compromised during the 48h window, export artifacts containing financial analysis results are exposed. Blast radius limited to Professional/Enterprise tier users who actively create share links.
- **Recommendation**: Document this as an explicit "controlled exception" to zero-storage in the Security Policy. Consider encrypting `export_data` at rest with a per-share key. Add retention monitoring dashboard metrics.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Document ExportShare as a controlled zero-storage exception and add at-rest encryption
  Files in scope: docs/04-compliance/security-policy.md, backend/export_share_model.py, backend/routes/export_sharing.py
  Approach: (1) Add a "Controlled Exceptions" section to the security policy documenting ExportShare's 48h TTL for derived artifacts with justification and compensating controls. (2) Optionally, add Fernet symmetric encryption for export_data column with per-share keys derived from the share token. (3) Add a Prometheus gauge for active (unexpired) export shares.
  Acceptance criteria:
  - Security policy documents the exception with justification
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Data Governance & Zero-Storage Warden (G)
- **Supporting Agents**: Security & Privacy Lead (D), Systems Architect (A)
- **Vote** (9 members; quorum=6): 6/9 Approve P2 | Dissent: Digital Fortress (D): "Financial data in DB for 48h is a P1 — breach-first posture demands encryption at minimum." Performance & Cost Alchemist (B): "Deliberate feature trade-off; P3 with documentation is sufficient." DX & Accessibility Lead (C): "Documented, tier-gated, auto-purged — P3 is appropriate."
- **Chair Rationale**: P2 sustained. While the feature is deliberate and compensating controls exist (TTL, auto-purge, tier-gating, token-based access), the stored data does contain financial analysis results. The zero-storage invariant is the platform's brand promise; any exception warrants Medium severity to ensure it remains actively monitored. Quorum met (6/9).

---

### F-003: framer-motion Transition Type Assertions Missing (`as const`)
- **Severity**: P3
- **Category**: Types/Contracts
- **Evidence**:
  - `frontend/src/components/batch/BatchDropZone.tsx:153` — `transition={{ type: 'spring', stiffness: 300, damping: 25 }}`
  - `frontend/src/components/batch/FileQueueItem.tsx:123,233` — Same pattern
  - `frontend/src/components/batch/BatchProgressBar.tsx:85` — Same pattern
  - `frontend/src/components/benchmark/PercentileBar.tsx:140` — Same pattern
  - `frontend/src/components/marketing/HeroProductFilm.tsx:107,121,157,395` — 4 instances (spring + tween)
  - `frontend/src/components/shared/ToolSettingsDrawer.tsx:188` — Same pattern
    - Explanation: Project convention (CLAUDE.md, MEMORY.md) requires `type: 'spring' as const` on all framer-motion transition properties. 11 instances across 6 files omit the `as const` assertion, allowing TypeScript to infer a broader `string` type instead of the literal union. Existing compliant examples: `FileQueueList.tsx:93`, `ConvergenceTable.tsx:67`, `FeaturePillars.tsx:95`.
- **Impact**: No runtime impact — framer-motion accepts string values. TypeScript type narrowing is weaker, reducing compile-time safety for transition configuration. Convention inconsistency across the codebase.
- **Recommendation**: Add `as const` to all 11 instances. Consider adding an ESLint rule or grep-based CI check to enforce this convention.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add `as const` to all framer-motion transition type properties per project convention
  Files in scope: frontend/src/components/batch/BatchDropZone.tsx, frontend/src/components/batch/FileQueueItem.tsx, frontend/src/components/batch/BatchProgressBar.tsx, frontend/src/components/benchmark/PercentileBar.tsx, frontend/src/components/marketing/HeroProductFilm.tsx, frontend/src/components/shared/ToolSettingsDrawer.tsx
  Approach: Find all `type: 'spring'`, `type: 'tween'`, `type: 'inertia'` in transition props and add `as const`. Verify against existing correct examples (FileQueueList.tsx:93).
  Acceptance criteria:
  - All framer-motion transition type properties use `as const`
  - `npm run build` passes
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Type & Contract Purist (H)
- **Supporting Agents**: DX & Accessibility Lead (C), Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-004: SQL Injection Pattern in Test Fixtures
- **Severity**: P3
- **Category**: Security
- **Evidence**:
  - `backend/tests/test_timestamp_defaults.py:175` — `db_session.execute(text(f"SELECT id FROM clients WHERE user_id = {user_id}")).scalar()`
  - `backend/tests/test_timestamp_defaults.py:184` — `db_session.execute(text(f"SELECT id FROM engagements WHERE client_id = {client_id}")).scalar()`
    - Explanation: Direct f-string interpolation in `text()` SQL queries. Values are integers from ORM inserts (not user input), so exploitation risk is zero. However, this pattern violates SQL injection prevention best practices and could be copy-pasted into production code. All production queries use ORM parameterization.
- **Impact**: Zero production impact — test-only code with integer literals. Risk: establishes a bad pattern that could be cargo-culted into production code during future development.
- **Recommendation**: Replace with parameterized queries using `text().bindparams()` or ORM `.query()`. Enforce via Bandit rule B608 (hardcoded SQL expressions).
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Replace f-string SQL interpolation with parameterized queries in test fixtures
  Files in scope: backend/tests/test_timestamp_defaults.py
  Approach: Replace f-string text() calls with text("SELECT ... WHERE user_id = :uid").bindparams(uid=user_id) or equivalent ORM queries.
  Acceptance criteria:
  - No f-string interpolation in text() calls
  - Tests still pass
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Security & Privacy Lead (D)
- **Supporting Agents**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-005: URL Parameter Encoding Gap in Workspace Layout
- **Severity**: P3
- **Category**: Security
- **Evidence**:
  - `frontend/src/app/(workspace)/layout.tsx:54` — `router.push(\`/login?redirect=${pathname}\`)`
    - Explanation: The `pathname` variable is passed directly into a URL query parameter without `encodeURIComponent()`. While modern browsers auto-encode URL parameters and Next.js routing sanitizes paths, explicit encoding is a defense-in-depth best practice. A pathname containing `?`, `#`, or `&` characters could theoretically corrupt the query string.
- **Impact**: Minimal in practice — Next.js pathnames are pre-validated. A specially-crafted route could corrupt the redirect parameter, leading to a failed redirect (not a security exploit). Open redirect is not possible since the redirect is to an internal path.
- **Recommendation**: Wrap `pathname` in `encodeURIComponent()` for defense-in-depth.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add encodeURIComponent to pathname in workspace layout redirect
  Files in scope: frontend/src/app/(workspace)/layout.tsx
  Approach: Change `router.push(\`/login?redirect=${pathname}\`)` to `router.push(\`/login?redirect=${encodeURIComponent(pathname)}\`)`. Verify the login page decodes the redirect parameter.
  Acceptance criteria:
  - pathname is encoded in redirect URL
  - Login page correctly decodes and redirects
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Security & Privacy Lead (D)
- **Supporting Agents**: None
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-006: APScheduler Multi-Worker Deployment Not Documented in Ops Docs
- **Severity**: P3
- **Category**: Reliability/Observability
- **Evidence**:
  - `backend/cleanup_scheduler.py:4-20` — Inline documentation explains single-threaded executor with coalesce/max_instances safety
    - Explanation: The APScheduler is configured safely for multi-worker deployment (single ThreadPoolExecutor, coalesce=True, max_instances=1, idempotent cleanup functions). However, this safety is only documented in code comments. No deployment documentation or runbook mentions that the scheduler runs per-instance (not cluster-wide). Under Gunicorn with `WEB_CONCURRENCY=4`, four independent scheduler instances will run, each attempting the same cleanup jobs. Idempotency prevents data corruption, but quadruples unnecessary DB load.
  - Deployment docs scanned: `docs/` directory contains compliance docs but no `DEPLOYMENT_ARCHITECTURE.md` or `OPERATIONS.md` with scheduler guidance.
- **Impact**: Unnecessary database load from redundant cleanup executions across workers. Risk of confusion during incident response if operators don't understand the per-instance model. No data corruption risk due to idempotent design.
- **Recommendation**: Add scheduler guidance to deployment documentation. Consider single-instance scheduler via `CLEANUP_SCHEDULER_ENABLED` environment variable (enable on one worker only) or distributed lock (Redis/PostgreSQL advisory lock).
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Document APScheduler deployment model and add single-instance option
  Files in scope: docs/ (new or existing deployment doc), backend/cleanup_scheduler.py, backend/.env.example
  Approach: (1) Add deployment section documenting scheduler per-instance behavior. (2) Document recommendation to set CLEANUP_SCHEDULER_ENABLED=true on only one worker/replica. (3) Optionally add PostgreSQL advisory lock to ensure only one scheduler instance runs cleanup.
  Acceptance criteria:
  - Deployment docs explain scheduler behavior under multi-worker
  - .env.example documents CLEANUP_SCHEDULER_ENABLED clearly
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-007: Redundant `status_code=200` on POST Endpoints
- **Severity**: P3
- **Category**: DX/A11y
- **Evidence**:
  - `backend/routes/audit.py:197` — `@router.post("/audit/preflight", response_model=PreFlightReportResponse, status_code=200)`
  - `backend/routes/audit.py:244` — `@router.post("/audit/population-profile", response_model=PopulationProfileResponse, status_code=200)`
  - `backend/routes/audit.py:293` — `@router.post("/audit/expense-category-analytics", response_model=ExpenseCategoryReportResponse, status_code=200)`
    - Explanation: FastAPI POST endpoints default to `status_code=200`. Explicitly setting `status_code=200` is redundant. Other POST endpoints in the same file (e.g., lines 447, 576) omit this parameter. Inconsistency creates confusion about whether the explicit annotation is intentional (e.g., overriding a different default).
- **Impact**: No functional impact. Minor DX friction — developers may wonder if removing the annotation would change behavior.
- **Recommendation**: Remove explicit `status_code=200` from POST endpoints for consistency. Reserve `status_code=` for non-default codes (201, 204).
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Remove redundant status_code=200 from POST endpoints for consistency
  Files in scope: backend/routes/audit.py
  Approach: Remove `status_code=200` from lines 197, 244, 293. Verify no behavior change via test suite.
  Acceptance criteria:
  - No explicit status_code=200 on POST endpoints (unless non-default)
  - All tests pass unchanged
  - CI passes
  - Tests updated
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

## 4) Discovered Standards → Proposed Codification

- **Existing standards inferred** (from codebase):
  - **Zero-Storage Processing**: All file I/O via `io.BytesIO()` + `gc.collect()`; no `open()` writes in production; Sentry `before_send` strips bodies; ToolSession dual-layer sanitization (allowlist + recursive forbidden-key filter)
  - **Auth Dependency Pattern**: `require_verified_user` for audit/export endpoints; `require_current_user` for client/settings; reference data public
  - **Rate Limit Tiering**: Anonymous (5/min) → Solo (8) → Professional (10) → Enterprise (20); per-user keying via user ID
  - **Error Sanitization**: `sanitize_error()` on all exception-to-HTTP boundaries; no traceback leakage
  - **Audit Trail Immutability**: SoftDeleteMixin on ActivityLog, DiagnosticSummary, ToolRun, FollowUpItem; `AuditImmutabilityError` on physical deletion attempt
  - **framer-motion `as const`**: Convention exists (documented in CLAUDE.md) but not enforced by tooling
  - **Lint Zero-Tolerance Baseline**: `.github/lint-baseline.json` enforces ruff=0 errors, eslint=0 errors/warnings
  - **Monetary Precision**: `Numeric(19,2)` for all monetary columns; `Decimal(str(x))` for calculations

- **Missing standards that should become policy**:
  - **OpenAPI→TypeScript Sync**: No automated generation pipeline; frontend types manually maintained → drift risk
  - **framer-motion Convention Enforcement**: No ESLint/grep CI check for `as const` on transition types
  - **ExportShare Data Retention**: No formal policy document for the 48h derived-data exception to zero-storage
  - **APScheduler Deployment Model**: No ops documentation for per-instance scheduler behavior
  - **SQL Parameterization in Tests**: No Bandit/linting enforcement for test code SQL patterns

- **Proposed enforcement mechanisms**:
  - **Linting/typing**: Add custom ESLint rule or CI grep check for framer-motion `type:` without `as const`; extend Bandit to scan test directories for B608 (hardcoded SQL)
  - **CI checks**: Add OpenAPI schema diff check (generate → compare → fail on drift); add grep-based CI step: `grep -rn "type: 'spring'" --include="*.tsx" | grep -v "as const"` → fail if matches
  - **Repo policy docs**: Create `docs/04-compliance/data-retention-policy.md` documenting ExportShare exception; add `docs/ops/deployment-guide.md` with scheduler section

## 5) Agent Coverage Report

- **Systems Architect (A) — "The Stalwart"**:
  - Touched areas: `backend/routes/__init__.py`, `backend/audit_engine.py`, `backend/shared/`, `backend/database.py`, `backend/cleanup_scheduler.py`, `docker-compose.yml`
  - Top 3 findings contributed: F-006 (primary), F-002 (supporting), F-007 (supporting)
  - One non-obvious risk flagged: Under Gunicorn with WEB_CONCURRENCY=4, four independent APScheduler instances run the same cleanup jobs — idempotent but quadruples DB churn.

- **Performance & Cost Alchemist (B) — "The Optimizer"**:
  - Touched areas: `backend/security_utils.py`, `backend/audit_engine.py`, `backend/currency_engine.py`, `backend/shared/helpers.py`, `frontend/next.config.js`
  - Top 3 findings contributed: F-001 (voter), F-002 (voter/dissent), F-007 (voter)
  - One non-obvious risk flagged: Chunked Excel reading in `security_utils.py` loads full DataFrame first then slices — not true streaming, but acceptable given 100MB file size cap.

- **DX & Accessibility Lead (C) — "The Diplomat"**:
  - Touched areas: `backend/routes/audit.py`, `frontend/src/components/shared/CommandPalette/`, `frontend/src/components/ErrorBoundary.tsx`, `frontend/src/components/shared/ToolSettingsDrawer.tsx`
  - Top 3 findings contributed: F-007 (primary), F-003 (supporting), F-002 (voter/dissent)
  - One non-obvious risk flagged: CommandPalette has excellent ARIA/keyboard support but no screen-reader announcement of result count changes during live filtering.

- **Security & Privacy Lead (D) — "Digital Fortress"**:
  - Touched areas: `backend/auth.py`, `backend/security_middleware.py`, `backend/routes/auth_routes.py`, `backend/config.py`, `frontend/src/proxy.ts`, `frontend/src/app/(workspace)/layout.tsx`
  - Top 3 findings contributed: F-004 (primary), F-005 (primary), F-002 (supporting/dissent)
  - One non-obvious risk flagged: Refresh token rotation detects reuse and revokes ALL tokens (line 559-629 in auth.py) — if an attacker replays a stolen refresh token, the legitimate user's session is also terminated, which is correct fail-safe behavior but could be confusing without user notification.

- **Modernity & Consistency Curator (E) — "The Trendsetter"**:
  - Touched areas: `backend/requirements.txt`, `frontend/package.json`, `backend/routes/audit.py`, `frontend/src/components/batch/`, `frontend/src/components/marketing/`
  - Top 3 findings contributed: F-003 (supporting), F-007 (supporting), F-001 (voter)
  - One non-obvious risk flagged: `slowapi` (rate limiter) last published Oct 2022 — wraps actively-maintained `limits` library, but the wrapper itself may not keep pace with FastAPI evolution.

- **Observability & Incident Readiness (F) — "The Detective"**:
  - Touched areas: `backend/logging_config.py`, `backend/shared/log_sanitizer.py`, `backend/main.py` (Sentry), `backend/routes/health.py`, `backend/routes/metrics.py`, `backend/shared/parser_metrics.py`
  - Top 3 findings contributed: F-006 (supporting), F-001 (supporting), F-002 (voter)
  - One non-obvious risk flagged: Cleanup scheduler telemetry logs job names and record counts but not the specific records deleted — during incident forensics, this makes it impossible to determine which specific expired tokens/shares were purged.

- **Data Governance & Zero-Storage Warden (G) — "The Auditor"**:
  - Touched areas: `backend/models.py`, `backend/engagement_model.py`, `backend/follow_up_items_model.py`, `backend/tool_session_model.py`, `backend/export_share_model.py`, `backend/retention_cleanup.py`, `backend/shared/soft_delete.py`
  - Top 3 findings contributed: F-002 (primary), F-006 (voter), F-004 (voter)
  - One non-obvious risk flagged: FollowUpItem `description` field is freeform TEXT — an auditor could inadvertently type financial data (account numbers, amounts) into narrative fields, bypassing the 13-field prohibition list. No input validation enforces the boundary at write time.

- **Type & Contract Purist (H) — "The Pedant"**:
  - Touched areas: `frontend/src/components/batch/`, `frontend/src/components/marketing/`, `frontend/src/components/benchmark/`, `frontend/src/components/shared/`, `frontend/src/types/`, `backend/tests/test_api_contracts.py`
  - Top 3 findings contributed: F-003 (primary), F-005 (voter), F-007 (voter)
  - One non-obvious risk flagged: No automated OpenAPI→TypeScript generation pipeline exists — frontend types are hand-maintained, creating drift risk. `test_api_contracts.py` validates backend schemas but doesn't cross-check against frontend type definitions.

- **Verification Marshal (I) — "The Skeptic"**:
  - Touched areas: `backend/tests/` (161 files), `frontend/src/__tests__/` (72 files), `.github/workflows/ci.yml`, `backend/tests/conftest.py`
  - Top 3 findings contributed: F-001 (primary), F-004 (supporting), F-002 (voter)
  - One non-obvious risk flagged: Test suite uses SQLite in local runs vs PostgreSQL in CI — SQLite lacks enum type enforcement, advisory locks, and concurrent access patterns, meaning some PostgreSQL-specific bugs could pass local tests.
