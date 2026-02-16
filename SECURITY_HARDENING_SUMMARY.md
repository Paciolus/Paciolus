# Security Hardening Summary

**Project:** Paciolus — Trial Balance Diagnostic Intelligence
**Scope:** 8 security packets + 4 stabilization commits
**Date:** 2026-02-16
**Baseline:** v1.3.0 (Phase XXXIV, Sprint 265)

---

## Commit Chain

| # | SHA | Description |
|---|-----|-------------|
| P1 | `4b19813` | Truthful zero-storage language baseline |
| P1b | `fd6bafb` | Resolve PR inline comments and tighten copy consistency |
| P2a | `af5c263` | Redact tokens and PII from email fallback logs |
| P3 | `06b86ed` | Harden upload parsing against archive bombs |
| P4 | `2c07f47` | Normalize explicit rate limits on mutating endpoints |
| P5 | `d6a0559` | Enforce production DB guardrails and dialect-safe tool session upsert |
| P6 | `328a02e` | Separate CSRF secret from JWT and harden exemption policy |
| P8 | `eb90a36` | Enforce retention cleanup for activity logs and diagnostic summaries |
| P2b | `80bfcf7` | Remove financial line data from persistent tool sessions |
| Fix | `bcd0484` | Fix regressions from packets 1-8 (rate limit test flakiness) |
| Stab-1 | `b00fed9` | Centralize limiter behavior for deterministic API tests |
| Stab-2 | `ff953b6` | Add explicit 429 enforcement tests for auth/write/audit tiers |
| Stab-3 | `ef19630` | Add explicit 429 enforcement test for export tier |

---

## Changes by Security Domain

### 1. Storage & Privacy (Packets 1, 1b, 2a, 2b)

- **Zero-storage language:** All user-facing copy (homepage, marketing, API docs) now accurately describes the ephemeral processing model. Removed or corrected any claims that could be interpreted as audit-grade data destruction guarantees.
- **Log sanitization:** Email fallback logs no longer contain JWT tokens, refresh tokens, or user PII. Token values are replaced with `[REDACTED]` before writing to logs.
- **Session data sanitization:** `tool_sessions` DB table no longer stores raw financial line data (account names, debit/credit amounts). A two-layer sanitization pipeline strips per-tool financial structures plus a recursive defense-in-depth pass against a `FORBIDDEN_FINANCIAL_KEYS` allowlist. Startup job sanitizes any legacy rows.
- **Apply-endpoint guard:** `POST /audit/adjustments/apply` returns HTTP 400 with clear message when adjustment entries lack line data (expected after DB round-trip sanitization).

### 2. Upload Safety (Packet 3)

- **Archive bomb protection:** Upload parsing rejects nested/recursive archive entries and enforces decompression size limits to prevent denial-of-service via crafted ZIP/archive files.
- **Existing column/cell limits and formula injection sanitization remain unchanged.**

### 3. Authentication & CSRF (Packet 6)

- **CSRF secret separation:** `CSRF_SECRET_KEY` is now a dedicated config variable, required in production, and must differ from `JWT_SECRET_KEY`. Prevents a compromised JWT secret from also defeating CSRF protection.
- **CSRF exemption hardening:** Exemption list reviewed and tightened; only public-facing form endpoints remain exempt.

### 4. Rate Limiting (Packet 4, Stabilization)

- **Explicit limits on all mutating endpoints:** Every POST/PUT/DELETE endpoint now has an explicit `@limiter.limit()` decorator with a tier-appropriate value (AUTH 5/min, AUDIT 10/min, EXPORT 20/min, WRITE 30/min, DEFAULT 60/min).
- **429 enforcement tests:** 4 integration tests fire real HTTP requests through the ASGI stack and assert 429 responses at exact tier boundaries for AUTH, WRITE, AUDIT, and EXPORT tiers.
- **Deterministic test infrastructure:** Global `conftest.py` fixture disables limiter for all tests by default; 429 tests opt-in via `enable_rate_limiter` fixture with `limiter.reset()` for clean state.

### 5. Database Safety (Packet 5)

- **Production DB guardrails:** SQLite is rejected in production mode; PostgreSQL connection parameters validated at startup.
- **Dialect-safe upsert:** `save_tool_session()` uses native `ON CONFLICT` for SQLite/PostgreSQL with a generic ORM fallback for unknown dialects, eliminating raw SQL injection surface.

### 6. Data Retention (Packet 8)

- **Retention cleanup engine:** `retention_cleanup.py` deletes activity logs and diagnostic summaries older than `RETENTION_DAYS` (default 365, configurable via environment). Boundary semantics: rows at exact cutoff are kept; only rows strictly older are purged.
- **Startup integration:** Runs automatically at application startup alongside token and session cleanup jobs. Idempotent — safe to run on every boot.

### 7. Test Reliability (Stabilization)

- **Centralized limiter disable:** Eliminated per-file `disable_rate_limits` fixtures that were band-aids for SlowAPI's in-memory state accumulation.
- **Regression fix:** Commit `bcd0484` resolved 14/27 false 429 failures in `test_compare_periods_api.py` caused by Packet 4's new rate limits.

---

## Test Evidence

| Command | Result |
|---------|--------|
| `pytest tests/ -q --tb=no` | **3,311 passed**, 89 warnings, 136s |
| `pytest tests/test_rate_limit_enforcement.py -v` | 4/4 passed (AUTH, WRITE, AUDIT, EXPORT) |
| `pytest tests/test_rate_limit_coverage.py -v` | 10/10 passed |
| `pytest tests/test_tool_sessions.py -v` | 57/57 passed |
| `pytest tests/test_retention_cleanup.py -v` | 17/17 passed |

Frontend build was verified clean during the release handoff pass.

---

## Residual Risks / Known Trade-offs

| Risk | Severity | Mitigation |
|------|----------|------------|
| `limiter.reset()` accesses SlowAPI internals | Low | Public method on `Limiter` class; pinned slowapi version in requirements |
| Retention cleanup runs at startup only, not on a scheduler | Low | Acceptable for current scale; add periodic job if deployment moves to always-on |
| Session sanitization strips line data — adjustments cannot be re-applied after DB round-trip | By design | Frontend holds full state in React; apply endpoint returns clear 400 error guiding re-creation |
| No Packet 7 in this hardening cycle | Info | Packet 7 was not part of the original 8-packet scope as defined by the security review |
| Pre-existing dirty files in working tree (audit_engine.py, test_audit_core.py, 15 untracked test files) | Info | Unrelated to this hardening scope; pre-date the packet work |

---

## Release Recommendation

**GO.** All 8 security packets are implemented, regression-tested, and stabilized. The test suite stands at 3,311 backend tests with zero failures. All four rate-limit tiers have explicit 429 enforcement coverage. No production code was modified during stabilization — only test infrastructure.
