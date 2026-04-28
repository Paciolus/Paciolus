# Security Review — Paciolus v2.1.0
**Date:** 2026-04-24
**Reviewer:** IntegratorLead (security-review skill)
**Branch:** `sprint-716-complete-status`
**Scope:** Auth surface, upload surface, export/share surface, billing webhook, SQL injection, XSS/CSP, secret exposure
**Mode:** Pre-Stripe-cutover hardening (CEO Phase 3 functional validation underway)

---

## Findings Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 1 |
| Medium   | 3 |
| Low      | 3 |
| Info     | 2 |

The codebase shows mature defense-in-depth: HMAC-signed CSRF, Argon2id passcode KDF (Sprint 697), per-IP + per-token brute-force throttle on share downloads (Sprints 697/698), defusedxml on OFX, archive-bomb detection on XLSX, parameterized SQL throughout audit ingest, formula-injection sanitizer on CSV/Excel exports, refresh-token rotation with reuse detection + atomic CAS, fail-closed Redis rate limiter in production. Origin/Referer allow-list + Sec-Fetch-Site fallback close the cookie-only CSRF gap that the user-binding miss (H-01) opens.

The most actionable finding (H-01) is one missed code path in the CSRF middleware — it reads only the `Authorization: Bearer` header to derive `expected_user_id`, so production browsers (which use the HttpOnly `paciolus_access` cookie and never send Bearer) silently bypass the user-binding check the rest of the system advertises.

---

## H-01 (HIGH) — CSRF user-binding silently disabled for browser cookie auth

**File:** `backend/security_middleware.py:485-509` (`_extract_user_id_from_auth`) → consumed at lines 537, 562, 595
**Frontend confirmation:** `frontend/src/utils/authMiddleware.ts:71-83` (`injectAuthHeaders` deliberately omits `Authorization`)
**Severity:** HIGH (defense-in-depth bypass; not directly exploitable today, becomes exploitable on first XSS or token-leak)

### Vulnerability
`_extract_user_id_from_auth` only inspects `Authorization: Bearer …` to recover the user_id used in CSRF token binding. The production browser path mints HttpOnly `paciolus_access` and `paciolus_refresh` cookies (see `backend/routes/auth_routes.py:107-122`) and the frontend explicitly does NOT inject a Bearer header (`authMiddleware.ts:64-67`). Result: for every browser POST/PUT/DELETE/PATCH, `expected_user_id = None` is passed into `validate_csrf_token` (line 537/595), which then short-circuits the binding check at `security_middleware.py:427` (`if expected_user_id is not None …`).

The CSRF token format is documented (line 357) as `{nonce}:{ts}:{user_id}:{hmac}` and the per-request mint embeds the issuing user. That binding is the entire reason the token is user-scoped rather than session-scoped. Today, in production, any leaked/stolen valid CSRF token is replayable against any other authenticated user's cookie session for 30 minutes (the token TTL).

### Exploit scenario
1. Attacker obtains *any* valid CSRF token issued in the last 30 min (XSS payload that can read DOM but not the HttpOnly cookie, log scraping of `console.log(headers)` from a partner integration, accidental Sentry breadcrumb leak, etc.).
2. Victim browser also has a live `paciolus_access` cookie session (different user).
3. Attacker convinces victim to load attacker-controlled page on a same-site subdomain that bypasses Origin allow-listing (e.g. SSRF on a Sentry DSN-style endpoint, or a future subdomain misconfiguration).
4. Page POSTs to `/clients`, `/engagements/{id}` etc. carrying the leaked CSRF token. CSRF middleware accepts it (origin allow-listed, HMAC valid, not-expired) and the request mutates state under the victim's identity.

The HMAC + 30-min expiry + Origin allow-list still hold, so this is not a 1-click compromise. But the user-binding is the documented ceiling of CSRF defense and it is silently a no-op.

### Remediation
Augment `_extract_user_id_from_auth` to read the access cookie when no Bearer is present:

```python
def _extract_user_id_from_auth(self, request: Request) -> Optional[str]:
    import jwt as _jwt
    from config import ACCESS_COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET_KEY

    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = _jwt.decode(
            token, JWT_SECRET_KEY or "",
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        sub = payload.get("sub")
        return str(sub) if sub else None
    except Exception:
        return None
```

Add a regression test that exercises a cookie-only POST with a CSRF token issued for a different user_id and asserts a 403.

---

## M-01 (MEDIUM) — Refresh cookie uses `SameSite=None` in production

**File:** `backend/routes/auth_routes.py:76-94` (`_set_refresh_cookie`), 107-122 (`_set_access_cookie`)
**Severity:** MEDIUM (CSRF backstop weakened; Origin/Referer enforcement compensates)

### Vulnerability
The reviewer's stated requirement is `SameSite=Lax` in production. The code unconditionally selects `SameSite=None` whenever `COOKIE_SECURE` is true (production), to support cross-origin AJAX from `paciolus.com` → `paciolus-api.onrender.com`. The trade-off is documented (lines 80-85), but `SameSite=None` means the cookie is attached to *any* cross-site request the browser initiates to the API — including the cross-site GET that some forge-cookie attacks rely on.

### Why it's MEDIUM not HIGH
1. The CSRF middleware (`security_middleware.py:434-606`) enforces Origin/Referer allow-listing on every mutation method, blocking cross-site forgery even when the cookie is attached.
2. Sec-Fetch-Site fallback (line 474-483) catches the rare browser that suppresses Origin/Referer.
3. The refresh cookie is `path=/auth` only.

### Exploit scenario
Combined with H-01, a cross-site GET from a malicious page on a subdomain that ends up in `CORS_ORIGINS` (e.g. a future `staging.paciolus.com` slip-up) auto-attaches the refresh cookie, and a token with no user binding is replayable.

### Remediation
- Move the API to a same-site domain (`api.paciolus.com`) so `SameSite=Lax` becomes viable. CEO has been planning custom domain anyway; this is the security argument for prioritizing it before scale-out.
- Until then: keep H-01 fixed (user binding is the real backstop), and document this in `docs/04-compliance/SECURITY_POLICY.md` as a known trade-off.

---

## M-02 (MEDIUM) — Share endpoint leaks existence of passcode-protected shares

**File:** `backend/routes/export_sharing.py:471-481` (`download_share` GET handler)
**Severity:** MEDIUM (information disclosure → enables targeted brute-force)

### Vulnerability
`GET /export-sharing/{token}` distinguishes three states:
- 404 — token doesn't exist or is revoked
- 410 — exists but expired
- 403 — exists, valid, has a passcode

An attacker sweeping share-token guesses can enumerate which (small fraction of) tokens are passcode-protected vs. open. A 403 result tells them "this token exists and is worth sustained brute-force on POST /download" — collapsing a 256-bit search down to whichever tokens they happened to hit. Token brute-force is bounded by 32-byte URL-safe random (`secrets.token_urlsafe(32)`), which is comfortably out of reach in absolute terms — but the asymmetry encourages targeted abuse where `RATE_LIMIT_EXPORT` (20-120/min) becomes the only barrier.

### Exploit scenario
Attacker scripts random-token GET requests from a botnet. Each 403 response identifies a real passcode share. They concentrate POST /download attacks on those tokens, riding under the per-token throttle (5 attempts before lockout) by switching tokens often.

### Remediation
Return 404 unconditionally on GET when a passcode is required, and surface the "use POST" hint only on the POST path. The information leakage from the 403 message ("This share link requires a passcode...") provides no usability benefit — legitimate users always have the share URL+passcode together because the creator gave them both.

```python
if share.passcode_hash:
    # Sprint 698: do not differentiate from "no such share" — enumeration defense
    raise HTTPException(status_code=404, detail="Share link not found.")
```

Update the frontend share-recipient UI to always POST first; if 404, show "link expired/invalid"; if 403, show passcode prompt.

---

## M-03 (MEDIUM) — Per-IP failure tracker is in-memory only, resets on restart

**File:** `backend/security_middleware.py:619-674` (`record_ip_failure`, `check_ip_blocked`, `_ip_failure_tracker`)
**Severity:** MEDIUM (rate-limit weakened by deploys/scale-out)

### Vulnerability
`_ip_failure_tracker` is a process-local `dict[str, list[float]]`. Under Render's auto-restart on deploy and Gunicorn's multi-worker model, the per-IP brute-force gate (Sprint 697 finding #2 / Sprint 698) is reset every deploy and is not shared across workers. An attacker who notices a deploy can reset their counter; an attacker hitting a different worker also gets a fresh counter.

The auth-failure DB-backed lockout (`record_failed_login` line 677) is not affected — it persists in `users.failed_login_attempts`. But the IP-level guard for `/auth/login` and `/export-sharing/{token}/download` only applies in-memory.

### Exploit scenario
Attacker times credential-stuffing against `/auth/login` to coincide with deploy windows (Render shows deploy times). 20 failures per IP per worker per 15 minutes × N workers × M deploys/day grants meaningful throughput.

### Remediation
Move `_ip_failure_tracker` to Redis using the same backend that backs `slowapi`. The existing storage URI is already resolved in `shared/rate_limits.py:207-249`. Use a sliding-window key per IP with TTL = `IP_FAILURE_WINDOW_SECONDS`.

---

## L-01 (LOW) — Org co-members can delete each other's clients without role check

**File:** `backend/client_manager.py:69-100` (`get_client`), `285-299` (`delete_client`)
**Routes:** `backend/routes/clients.py:272-284` (DELETE), `216-269` (PUT)
**Severity:** LOW (could be intentional org-sharing policy; depends on PM intent)

### Vulnerability
`get_client(user_id, client_id)` returns the client whether the caller is the direct owner OR any organization co-member of the owner. Both `update_client` and `delete_client` build on `get_client`, so any org member (regardless of `OrgRole`) can mutate or delete clients owned by another org member.

In the admin dashboard endpoints (`routes/admin_dashboard.py:60-62`), there's an explicit `OWNER`/`ADMIN` check. No equivalent check exists in the client routes — an `OrgRole.MEMBER` can delete the org owner's client.

### Exploit scenario
Disgruntled junior auditor at a 10-seat firm deletes the partner's clients minutes before resigning. Soft-delete may save the data (per Sprint 360 immutability guarantees) but workflow disruption is real.

### Remediation
Decide PM intent first. If write operations should require role ≥ ADMIN within the org, add a role check in `update_client`/`delete_client`. If shared write is intentional (likely), add an audit log entry per mutation that records both the actor and the owner so post-incident attribution is unambiguous.

---

## L-02 (LOW) — Excel `.upper()` on materiality without sanitization

**File:** `backend/excel_generator.py:321-322`
**Severity:** LOW (data path is engine-controlled; not user-injectable today)

### Vulnerability
`materiality = ab.get("materiality", "unknown"); ws.cell(...).value = materiality.upper()` writes a raw string to an Excel cell without `sanitize_csv_value`. Today the materiality values come from `audit_engine.py` as a fixed enum (`material`/`immaterial`/`unknown`), so this isn't exploitable. But the rest of the file consistently calls `sanitize_csv_value` on user-derived strings, and the inconsistency would mask formula injection if the contract ever loosens.

### Remediation
Wrap with `sanitize_csv_value(materiality.upper())` for consistency and defense-in-depth.

---

## L-03 (LOW) — Login response timing can leak account existence under load

**File:** `backend/routes/auth_routes.py:268-301`
**Severity:** LOW (mitigated by lockout returning identical 401; timing channel is narrow)

### Vulnerability
The login flow conditionally calls `record_failed_login(db, existing_user.id)` on line 295 when an existing user supplies a wrong password, but skips the DB write when the email is unknown. Under load this yields a measurable timing difference (DB UPDATE vs. branch skip), which could be used for slow account enumeration.

### Why it's LOW
- The 401 detail is identical for both paths (line 297-301).
- bcrypt verification on the existing-but-wrong-password path dominates timing (~250ms) and itself differentiates from "user not found, no bcrypt call" — that's the bigger leak.
- Public guidance: do a fake bcrypt verify on the unknown-email path to equalize. Code already does this implicitly via `authenticate_user` returning `None` early.

Actually re-reading: `authenticate_user` does NOT call bcrypt when the user doesn't exist (line 528-530 returns immediately). So unknown-email is much faster than known-email-wrong-password.

### Remediation
Add a fake bcrypt comparison in `authenticate_user` when the user doesn't exist:

```python
if user is None:
    # Constant-time defense against account enumeration via timing
    _bcrypt.checkpw(b"dummy", b"$2b$12$" + b"X" * 53)  # ~same cost as real verify
    log_secure_operation(...)
    return None
```

---

## INFO-01 — Stripe webhook handler is solid

**File:** `backend/routes/billing.py:345-449` (`stripe_webhook`)

Signature verification via `stripe.Webhook.construct_event` (line 375), atomic dedup via `INSERT ... ON CONFLICT DO NOTHING` on `ProcessedWebhookEvent` (lines 396-414), correct 400/500 status discrimination so Stripe retries operational errors but not malformed/forged ones, CSRF-exempt by allowlist (`security_middleware.py:314`). No findings.

## INFO-02 — Upload pipeline is well-defended

**File:** `backend/shared/upload_pipeline.py`, `backend/shared/ofx_parser.py`, `backend/shared/pdf_parser.py`

10-step ingress validation (size, content-type, extension, magic bytes, archive-bomb, XML-bomb, row/col/cell caps, formula-injection sanitization on export). XLSX archive inspection enforces ≤10K entries, ≤1GB uncompressed, ≤100:1 ratio, and scans embedded XML for `<!DOCTYPE>`/`<!ENTITY>`. OFX uses `defusedxml.ElementTree` with explicit XML-bomb prefix scan. openpyxl loaded with `read_only=True, data_only=True, keep_vba=False, keep_links=False`. xlrd 2.x dropped formula support. PDF parsed via pdfplumber with per-page 5s timeout and 500-page cap. No findings on this surface.

---

## Notes on Anti-patterns NOT found

- No `dangerouslySetInnerHTML` anywhere in `frontend/src` (clean).
- No f-string SQL with user input. The two `f"ALTER TABLE ... ADD COLUMN {col_name} {col_type}"` sites in `database.py:190` and `:251` use a hardcoded allowlist — safe DDL.
- No hardcoded secrets, Stripe keys, or AWS credentials in source. `.env.example` files contain only placeholder text (`sk_test_...`, `whsec_...`).
- CSP nonce-based, dynamic per-request via `frontend/src/proxy.ts`. `'strict-dynamic'` removes host-allowlist attack surface. No `'unsafe-eval'` in production.
- Refresh-token rotation includes atomic CAS (`auth.py:738-752`) — race-safe against concurrent refresh.
- Account lockout and IP-failure tracking compose correctly (`auth_routes.py:281-302`).
- Argon2id parameters meet OWASP 2024 (time_cost=3, memory=64MiB, parallelism=4) per `passcode_security.py:51-63`.

---

## Recommended Triage Order

1. **H-01** — fix before Stripe cutover. ~1 hour: edit `_extract_user_id_from_auth`, add cookie-fallback test, redeploy.
2. **M-02** — cheap UX improvement that closes an enumeration channel. ~1 hour.
3. **M-03** — Redis migration for IP failure tracker. ~2-4 hours, requires storage-key collision design with slowapi prefix.
4. **L-03** — fake bcrypt verify on unknown-email login. ~30 min.
5. **L-01** — clarify org-RBAC intent with CEO before coding.
6. **M-01** — track as known trade-off; tie to api.paciolus.com domain migration.
7. **L-02** — drop into next batch refactor.

---

*End of report.*
