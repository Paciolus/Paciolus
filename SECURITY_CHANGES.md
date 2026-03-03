# Security Audit Changes — Sprint 476

**Date:** 2026-03-03
**Auditor:** Claude Opus 4.6
**Scope:** Full codebase audit (FastAPI backend + Next.js frontend + infrastructure)

---

## Summary

| Severity | Found | Fixed | Deferred |
|----------|-------|-------|----------|
| CRITICAL | 1 | 1 | 0 |
| HIGH | 4 | 4 | 0 |
| MEDIUM | 7 | 7 | 0 |
| LOW | 8 | 2 | 6 |
| Dependencies | 8 | 8 | 0 |

---

## Fixes Applied

### CRITICAL

#### 1. Bulk Upload Bypasses File Validation Pipeline
- **File:** `backend/routes/bulk_upload.py`
- **Issue:** The `/upload/bulk` endpoint performed only a basic size check but skipped the entire 10-step file validation pipeline (extension, MIME, magic bytes, archive bomb, XML bomb).
- **Fix:** Replaced manual size check with `validate_file_size()` call for each file. All uploaded files now go through the full validation pipeline.
- **Also fixed:** Added `OrderedDict`-based job store with TTL eviction (2h) and max capacity (100 jobs) to prevent memory exhaustion from unbounded `_bulk_jobs` dict.

### HIGH

#### 2. CSV Injection in Bank Reconciliation Export
- **File:** `backend/bank_reconciliation.py`
- **Issue:** `export_reconciliation_csv()` wrote transaction descriptions and references directly to CSV without formula sanitization. Malicious descriptions like `=CMD|'/C calc'!A0` would execute when opened in Excel.
- **Fix:** Applied `sanitize_csv_value()` to all 6 user-sourced fields (description, reference) across matched, bank-only, and ledger-only sections.

#### 3. CSV Injection in Multi-Period Comparison Export
- **File:** `backend/multi_period_comparison.py`
- **Issue:** `export_movements_csv()` wrote account names, lead sheet names, categories, movement types, and significance directly without sanitization.
- **Fix:** Applied `sanitize_csv_value()` to all 5 user-sourced fields in data rows and 2 fields in lead sheet summary rows.

#### 4. IDOR in Audit Chain Verification (Cross-Tenant Data Leakage)
- **Files:** `backend/shared/audit_chain.py`, `backend/routes/activity.py`
- **Issue:** `verify_audit_chain()` queried `ActivityLog` records by ID range without filtering by `user_id`. Any authenticated user could probe arbitrary ID ranges and learn record counts and broken chain IDs belonging to other users.
- **Fix:** Added mandatory `user_id` parameter to `verify_audit_chain()`. Both the main query and the previous-record lookup now filter by `ActivityLog.user_id == user_id`. Updated route to pass `current_user.id`. Updated all tests.

#### 5. Seat Enforcement Defaults to "Soft" (Revenue Leakage)
- **File:** `backend/config.py`
- **Issue:** `SEAT_ENFORCEMENT_MODE` defaulted to `"soft"` (log-only), meaning organizations could exceed their paid seat allocation indefinitely without being blocked.
- **Fix:** Changed default from `"soft"` to `"hard"`. Operators can still set `SEAT_ENFORCEMENT_MODE=soft` in `.env` for debugging.

### MEDIUM

#### 6. CSV Injection in Admin Dashboard Export
- **File:** `backend/routes/admin_dashboard.py`
- **Issue:** Team activity CSV export wrote user names/emails without formula sanitization.
- **Fix:** Applied `sanitize_csv_value()` to user name, action type, and tool name fields.

#### 7. Missing Pipe Character in Formula Trigger Set
- **File:** `backend/shared/helpers.py`
- **Issue:** `_FORMULA_TRIGGERS` was missing `|` (pipe), which LibreOffice Calc interprets as a macro trigger. OWASP CWE-1236 recommends including it.
- **Fix:** Added `"|"` to the `_FORMULA_TRIGGERS` frozenset.

#### 8. Logo Upload Lacks Magic Byte Validation
- **File:** `backend/routes/branding.py`
- **Issue:** Logo upload validated only the browser-supplied `Content-Type` header, not the actual file content. An attacker could upload HTML/JS disguised as PNG.
- **Fix:** Added magic byte validation: PNG files must start with `\x89PNG\r\n\x1a\n`, JPEG files must start with `\xff\xd8\xff`. Rejects files that don't match either signature.

#### 9. Non-Atomic Webhook Handlers (Race Condition)
- **File:** `backend/billing/webhook_handler.py`
- **Issue:** `handle_subscription_deleted()` called `db.commit()` twice — once for subscription status, once for user tier downgrade. A crash between commits would leave the subscription canceled but the user retaining paid-tier access.
- **Fix:** Consolidated into a single `db.commit()` after both mutations.

#### 10. Session Data Not Cleared on Logout
- **File:** `frontend/src/contexts/AuthContext.tsx`
- **Issue:** `MappingContext` account mapping data and materiality threshold persisted in `sessionStorage` after logout. A different user logging in on the same tab would see residual data.
- **Fix:** Added `sessionStorage.removeItem()` calls for `paciolus_account_mappings` and `paciolus_last_threshold` in `clearAuthSessionData()`.

#### 11. Follow-Up Item Assignee Accepts Any User ID
- **File:** `backend/follow_up_items_manager.py`
- **Issue:** The `assigned_to` field accepted any valid user ID without verifying the assignee belongs to the same organization, enabling cross-tenant user enumeration.
- **Fix:** Added organization membership intersection check — the assignee must share at least one organization with the assigning user (or be the same user).

#### 12. Email Template HTML Injection
- **File:** `backend/email_service.py`
- **Issue:** User names were interpolated into HTML email templates without escaping. A name like `<script>alert(1)</script>` would render as HTML in email clients.
- **Fix:** Added `html.escape()` for user names before interpolation into the HTML template.

### Dependencies

#### 13. Python CVE Patches
- **File:** `backend/requirements.txt`
- **Upgraded:** `cryptography` 46.0.4 → 46.0.5 (CVE-2026-26007), `pillow` 12.1.0 → 12.1.1 (CVE-2026-25990), `werkzeug` 3.1.5 → 3.1.6 (CVE-2026-27199)
- **Removed:** `ecdsa` 0.19.1 (CVE-2024-23342, orphan package with no dependents)

#### 14. npm CVE Patches
- **Fixed via `npm audit fix`:** `minimatch` (high — ReDoS), `rollup` (high — path traversal), `ajv` (moderate — ReDoS)
- **Result:** 0 vulnerabilities remaining

---

## Deferred (LOW — Not Auto-Fixed)

These items are low-risk and documented for future sprints:

| # | File | Issue | Recommendation |
|---|------|-------|----------------|
| L1 | `scripts/create_dev_user.py` | Hardcoded dev credentials (`DevPass1!`) | Add `ENV_MODE != "production"` guard |
| L2 | `routes/metrics.py` | Unauthenticated Prometheus endpoint | Network-restrict in production (firewall/ingress rule) |
| L3 | `routes/health.py` | Pool stats on `/health/ready` | Network-restrict or add basic auth |
| L4 | `docker-compose.yml` | Commented-out `POSTGRES_PASSWORD=password` | Replace with `${POSTGRES_PASSWORD}` |
| L5 | Various diagnostic engines | Intermediate `float()` on raw monetary input | Migrate to `Decimal()` for consistency with monetary.py mandate |
| L6 | `routes/clients.py`, `routes/diagnostics.py` | `user_id` field in API responses | Strip from response schemas (unnecessary) |

---

## Environment Variable Changes

No new environment variables required. One default changed:

| Variable | Old Default | New Default | Impact |
|----------|-------------|-------------|--------|
| `SEAT_ENFORCEMENT_MODE` | `"soft"` | `"hard"` | Seat limits now enforced by default. Set to `"soft"` explicitly if needed during rollout. |

---

## Verification

- `npm run build` — PASS (all routes dynamic)
- `pytest tests/test_audit_chain.py` — 21 passed
- `pytest tests/test_bank_reconciliation.py` — 76 passed
- `pytest tests/test_multi_period_comparison.py` — 65 passed
- `pip-audit` — 0 vulnerabilities (excluding pip itself)
- `npm audit` — 0 vulnerabilities
