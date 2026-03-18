# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Marketing pages SSG | **Not feasible** — CSP nonce (`await headers()` in root layout) forces dynamic rendering; Vercel edge caching provides near-static perf | Phase XXVII |
| Test file mypy — full cleanup | 804 errors across 135 files (expanded from 68); `python_version` updated to 3.12 in Sprint 543 | Sprint 475/543 |

---

## Active Phase
> Sprints 478–497 archived to `tasks/archive/sprints-478-497-details.md`.
> Sprints 499–515 archived to `tasks/archive/sprints-499-515-details.md`.
> Sprints 516–526 archived to `tasks/archive/sprints-516-526-details.md`.
> Sprints 517–531 archived to `tasks/archive/sprints-517-531-details.md`.
> Sprints 532–536 archived to `tasks/archive/sprints-532-536-details.md`.
> Sprints 537–541 archived to `tasks/archive/sprints-537-541-details.md`.
> Sprints 542–546 archived to `tasks/archive/sprints-542-546-details.md`.
> Sprints 547–551 archived to `tasks/archive/sprints-547-551-details.md`.

### Sprint 556 — AUDIT-05 Error Handling and Information Leakage Remediation
**Status:** COMPLETE
**Scope:** 5 fixes from AUDIT-05 Error Handling and Information Leakage review

- [x] **FIX 1 (HIGH):** Make traceback redaction the production default — invert opt-in to opt-out, add Dockerfile env
- [x] **FIX 2 (MEDIUM):** Add custom RequestValidationError handler — opaque 422 responses, no Pydantic loc/msg leakage
- [x] **FIX 3 (MEDIUM):** Replace role-disclosing 403 messages with generic "Access denied." in organization and admin routes
- [x] **FIX 4 (MEDIUM):** Centralize API error normalization — safe passthrough allowlist in transport layer, dev-only error details in batch UI
- [x] **FIX 5 (MEDIUM):** Remove raw error objects from production console output — strip all console methods in prod, sanitize dev-mode calls

**Review:**
- FIX 1: `TracebackRedactionFilter` now activates by default when `ENV_MODE=production`; opt-out via `REDACT_LOG_TRACEBACKS=false`. Dockerfile declares `REDACT_LOG_TRACEBACKS=true` as belt-and-suspenders.
- FIX 2: `RequestValidationError` handler returns `{error_code, message, request_id}` — no `loc`, `msg`, or field names. Full validation errors logged at DEBUG level.
- FIX 3: All 3 role-disclosing 403 raises (`organization.py` ×2, `admin_dashboard.py` ×1) replaced with `"Access denied."`. Original role specificity retained in WARNING-level log entries.
- FIX 4: `normalizeApiError()` in `transport.ts` is the single point for backend→UI error string mapping. 422 responses mapped to static message. `BatchUploadContext` uses static error messages; `FileQueueItem` gates `error.details` on `NODE_ENV === 'development'`.
- FIX 5: `removeConsole` in `next.config.js` now strips ALL console methods (including `error`/`warn`) in production. `AuthSessionContext` and `useTrialBalancePreflight` sanitize logged errors to `error.name` only.
- Verification: `npm run build` passes, 1,426 frontend tests pass (118 suites), 1,995 backend tests pass (1 pre-existing failure unrelated: `test_email_verification` SQLite schema mismatch from Sprint 553)
- Files: `logging_config.py`, `Dockerfile`, `main.py`, `transport.ts`, `organization.py`, `admin_dashboard.py`, `BatchUploadContext.tsx`, `FileQueueItem.tsx`, `apiClient.test.ts`, `next.config.js`, `AuthSessionContext.tsx`, `useTrialBalancePreflight.ts`

### Sprint 555 — AUDIT-04 CI/CD Pipeline Security Remediation
**Status:** COMPLETE
**Scope:** 5 fixes from AUDIT-04 CI/CD Pipeline Security review

- [x] **FIX 1 (HIGH):** Pin all GitHub Actions to full commit SHAs (3 workflow files)
- [x] **FIX 2 (HIGH):** Replace TruffleHog curl|sh with pinned checksum-verified binary
- [x] **FIX 3 (MEDIUM):** Pin Docker base images to immutable digests (2 Dockerfiles)
- [x] **FIX 4 (MEDIUM):** Harden .dockerignore against key/cert material
- [x] **FIX 5 (MEDIUM):** Document deployment governance and enforce branch protection status checks

**Review:**
- All `uses:` entries across 3 workflows pinned to 40-char commit SHAs (7 unique actions)
- TruffleHog installer replaced with pinned v3.93.8 binary + sha256sum verification
- Docker FROM statements pinned: `python:3.12-slim-bookworm@sha256:31c0...` and `node:22-alpine@sha256:8094...`
- Both .dockerignore files hardened with 15 key/cert exclusion patterns
- `DEPLOYMENT_GOVERNANCE.md` created documenting branch protection, deployment pipeline, override policy
- `actions-pin-registry.md` created documenting all pinned SHAs, digests, and rotation procedure
- Verification: `grep -rE "uses:.*@v[0-9]"` = 0 results, `grep -rE "curl.*\|.*sh"` = 0 results
- Files: `ci.yml`, `backup-integrity-check.yml`, `dr-test-monthly.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `backend/.dockerignore`, `frontend/.dockerignore`, `DEPLOYMENT_GOVERNANCE.md`, `actions-pin-registry.md`

### Sprint 554 — AUDIT-03 Runtime Browser Storage Remediation
**Status:** COMPLETE
**Scope:** 6 fixes from AUDIT-03 Runtime Browser Storage review

- [x] **FIX 1 (CRITICAL):** MappingContext sessionStorage — remove all sessionStorage persistence of account mapping data
- [x] **FIX 2 (HIGH):** User Object sessionStorage — remove PII (User object) from sessionStorage across 3 auth contexts
- [x] **FIX 3 (HIGH):** Email in Registration URL — strip email from redirect query parameter
- [x] **FIX 4 (HIGH):** Verification Token in URL — strip token from URL after consumption
- [x] **FIX 5 (MEDIUM):** Materiality Threshold sessionStorage — remove threshold from sessionStorage
- [x] **FIX 6 (MEDIUM):** Sentry URL Scrubbing — scrub page URL query strings in beforeSend

**Review:**
- All 6 fixes verified: `sessionStorage.setItem` across `src/` shows only 3 allowed entries (mute flag, redirect path, command palette recency)
- Build passes with zero type errors
- All 1,426 frontend tests pass across 118 suites
- Files: `MappingContext.tsx`, `AuthSessionContext.tsx`, `UserProfileContext.tsx`, `VerificationContext.tsx`, `register/page.tsx`, `verification-pending/page.tsx`, `verify-email/page.tsx`, `history/page.tsx`, `sentry.client.config.ts`, `authFlowState.ts`

### Sprint 553 — AUDIT-02 Authentication Lifecycle Remediation
**Status:** COMPLETE
**Scope:** 2 fixes from AUDIT-02 Authentication Lifecycle review

- [x] **FIX 1 (MEDIUM):** CSRF Logout Binding — bind logout CSRF validation to refresh-cookie owner via DB lookup, preventing cross-user CSRF token reuse on logout
- [x] **FIX 2 (LOW):** Session Inventory & Revocation — add session metadata columns (last_used_at, user_agent, ip_address) + 3 new API endpoints (GET/DELETE /auth/sessions)

**Review:**
- FIX 1: 3 new tests (cross-user rejected, same-user passes, no-cookie fallback) + 65 existing CSRF tests pass
- FIX 2: 12 new tests (list sessions, ownership enforcement, single/bulk revocation, route registration) + 26 existing auth route tests pass
- All 106 auth tests pass with zero regressions
- Files: `security_middleware.py`, `auth.py`, `models.py`, `routes/auth_routes.py`, migration `b6c7d8e9f0a1`

### Sprint 552 — AUDIT-01 Calculation Correctness Fixes
**Status:** COMPLETE
**Scope:** 5 confirmed defects from AUDIT-01 Financial Calculation Correctness review

- [x] **RPT-12 (CRITICAL):** Multi-Period duplicate normalized account overwrite — aggregate debits/credits instead of single-row overwrite
- [x] **RPT-07 (HIGH):** AR Aging `date.today()` fallback — add `as_of_date` config field, propagate through route → engine → `_compute_aging_days`
- [x] **RPT-10a (HIGH):** Bank Rec hardcoded $50k materiality — add `materiality`/`performance_materiality` to `BankRecConfig`, thread from route Form params
- [x] **RPT-10b (HIGH):** Bank Rec composite risk score missing from API — compute `composite_score` in `reconcile_bank_statement()`, serialize from `BankRecResult.to_dict()`, update `BankRecResponse` schema
- [x] **DASH-01 (HIGH):** Dashboard zero-score fallback — derive risk score from `rec_tests` when `composite_score` absent instead of hardcoding 0

**Review:**
- All 4 affected test suites pass (273 targeted + 278 broad = 551 tests verified)
- Files: `multi_period_comparison.py`, `ar_aging_engine.py`, `routes/ar_aging.py`, `bank_reconciliation.py`, `routes/bank_reconciliation.py`, `engagement_dashboard_engine.py`, `shared/testing_response_schemas.py`

