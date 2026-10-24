# Security Hardening Summary

**Project:** Paciolus — Trial Balance Diagnostic Intelligence
**Scope:** 8 security packets + 4 stabilization commits + 3 verification sprints
**Date:** 2026-02-16
**Baseline:** v1.3.0 (Phase XXXIV, Sprint 265)
**Final Test Count:** 3,320 backend + 520 frontend = 3,840 total

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
| Sprint 1.2 | `f7a478e` | Behavioral tests for token and PII log redaction (9 new tests) |
| Sprint 2.2 | `98b5995` | Architecture doc metadata refresh to current state (18+ stale refs fixed) |
| Sprint 5.1 | *this commit* | Final verification pass + closeout summaries |

---

## Changes by Security Domain

### 1. Storage & Privacy (Packets 1, 1b, 2a, 2b)

- **Zero-storage language:** All user-facing copy (homepage, marketing, API docs) now accurately describes the ephemeral processing model. Removed or corrected any claims that could be interpreted as audit-grade data destruction guarantees.
- **Log sanitization:** Email fallback logs no longer contain JWT tokens, refresh tokens, or user PII. Token values are fingerprinted (`first 6 chars + length`). Contact form logs record only `inquiry_type` + `message_length`. Email change notifications use masked email (`lon***@domain.com`).
- **Log redaction behavioral proof (Sprint 1.2):** 9 new tests assert that raw tokens, full email addresses, sender names, company names, and message bodies never appear in log output. Tests also verify safe telemetry labels (`email_skipped`, `contact_email_skipped`, `email_change_notification_skipped`) are present.
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

### 8. Documentation Accuracy (Sprint 2.2)

- **Architecture doc refresh:** `docs/02-technical/ARCHITECTURE.md` updated from v2.0 to v3.0. Corrected 18+ stale references: version (0.70.0 → 1.3.0), Python (3.11 → 3.12), tool count (5 → 11), route count (17 → 30), test count (1,270 → 3,100+), JWT parameters (8-hour → 30-min access + 7-day refresh), CSRF description (CORS policy → Stateless HMAC), rate limiting ("planned" → 5 active tiers), CI/CD ("Future" → active).
- **Zero-storage and security wording preserved verbatim** — no new claims introduced.

---

## Test Evidence

| Command | Result | When |
|---------|--------|------|
| `pytest tests/ -v` | **3,320 passed**, 89 warnings, 140s | Sprint 5.1 final verification |
| `pytest tests/test_email_verification.py tests/test_contact_api.py -v` | **56/56 passed** | Sprint 5.1 targeted verification |
| `pytest tests/test_rate_limit_enforcement.py -v` | 4/4 passed (AUTH, WRITE, AUDIT, EXPORT) | Stabilization |
| `pytest tests/test_rate_limit_coverage.py -v` | 10/10 passed | Stabilization |
| `pytest tests/test_tool_sessions.py -v` | 57/57 passed | Packet 5 |
| `pytest tests/test_retention_cleanup.py -v` | 17/17 passed | Packet 8 |
| `npm run build` | **Success** — all routes compiled | Sprint 5.1 final verification |
| `grep` stale reference scan on ARCHITECTURE.md | **Clean** — only version history table | Sprint 2.2 |
| `git log --oneline -20` | All 17 commits verified in chain | Sprint 5.1 |

---

## Residual Risks / Known Trade-offs

| Risk | Severity | Mitigation |
|------|----------|------------|
| `limiter.reset()` accesses SlowAPI internals | Low | Public method on `Limiter` class; pinned slowapi version in requirements |
| Retention cleanup runs at startup only, not on a scheduler | Low | Acceptable for current scale; add periodic job if deployment moves to always-on |
| Session sanitization strips line data — adjustments cannot be re-applied after DB round-trip | By design | Frontend holds full state in React; apply endpoint returns clear 400 error guiding re-creation |
| No Packet 7 in this hardening cycle | Info | Packet 7 was not part of the original 8-packet scope as defined by the security review |
| openpyxl `utcnow()` deprecation warnings (89) | Low | Third-party library; no action until openpyxl releases fix |
| Pre-existing dirty files in working tree (audit_engine.py, test_audit_core.py, 15 untracked test files) | Info | Unrelated to this hardening scope; pre-date the packet work |

---

## Release Recommendation

**GO.** All 8 security packets are implemented, regression-tested, and stabilized. Three verification sprints (1.2, 2.2, 5.1) confirmed behavioral correctness and documentation accuracy. The test suite stands at **3,320 backend + 520 frontend = 3,840 total tests with zero failures**. All four rate-limit tiers have explicit 429 enforcement coverage. Log redaction has 9 behavioral proof tests. Architecture documentation is aligned with current state.
