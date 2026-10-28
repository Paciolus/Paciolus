# Vibecoder Security Review: Paciolus

**Date:** 2026-10-27
**Scope:** `main` @ `48c17626` — FastAPI backend (47 route modules), Next.js 16 frontend, GitHub Actions, git history
**Method:** Vibecoder triage checklist (8 core checks). Four parallel reviewers covered auth, data access, injection/uploads, and hygiene. Secrets and dependency scans were run directly. Every Medium finding below was confirmed by reading the code path; findings marked *(verified)* were re-read independently by the integrator.

## Summary

There are **0 critical, 0 high, 9 medium and 14 low** findings. The vibecoder checklist found none of its usual problems: there are no hardcoded secrets, client-trusted identity, cross-tenant IDOR, raw SQL, eval/pickle, `dangerouslySetInnerHTML`, wildcard CORS or debug backdoors. What remains is subtler: session-lifecycle edges, PDF rendering, entitlement propagation, and how roles and access work inside an organization.

| Check | Result |
|---|---|
| Secrets & keys | **Clean.** No live keys or production DSNs in tracked files or in all of git history. Only `.env.example` placeholders, local docker-compose DSNs and test fixtures were found. |
| Dependencies | **Clean.** `npm audit --omit=dev`: 0 vulnerabilities. `pip-audit -r requirements.txt`: no known vulnerabilities. |
| Auth & accounts | 4 medium, 5 low |
| User data / IDOR | No cross-tenant IDOR. 2 medium and 3 low inside an organization |
| Test vs production | 1 low (fail-open `ENV_MODE`) |
| File uploads | 1 medium (PDF bomb), 2 low |
| Hygiene | 1 medium (client-IP derivation), 4 low |
| Injection / RCE | 1 medium (ReportLab markup injection). SQL, RCE, XSS, SSRF and XXE are sound; there is no LLM usage. |

---

## Medium findings

### M1. ReportLab markup injection in memo PDFs *(verified)*

**Location:** `backend/shared/memo_base.py:91` (`wrap_table_strings`) and `:288` (`build_memo_header`). The same raw-string `Paragraph()` pattern appears in `fixed_asset_testing_memo_generator.py`, `currency_memo_generator.py`, `accrual_completeness_memo.py`, `multi_period_memo_generator.py`, `bank_reconciliation_memo_generator.py`, `expense_category_memo.py` and `flux_expectations_memo.py`.

**Issue:** ReportLab's `Paragraph` parses its input as markup. Account names and descriptions from uploaded files reach it without escaping. Only `memo_base.py` and `bank_reconciliation_memo_generator.py` import `xml_escape`, and `wrap_table_strings` does not use it.

**Attack:**
1. A client hands the auditor a ledger with the description `<a href="https://evil.example/login" color="blue">View source ledger</a>`.
2. The exported memo now carries a working, Paciolus-branded phishing link. It can also be shared through export-sharing.
3. The same technique can hide text with `<font size=0>`. An `<img src=...>` tag makes the export fail.

**Not possible:** SSRF (ReportLab `trustedHosts` is `None`) and code execution (CVE-2023-33733 is fixed in reportlab 5.x).

**Fix:** Escape untrusted strings before they reach `Paragraph`. First check which callers pass intentional `<b>`/`<i>` markup through `wrap_table_strings`. They need a separate path, such as pre-built `Paragraph` objects. Then add a markup payload to `tests/test_injection_regression.py`; it currently tests only `{{7*7}}`-style payloads.

### M2. Client IP is the leftmost `X-Forwarded-For` entry, so it is spoofable or collapses to one shared IP

**Location:** `backend/security_middleware.py:848-851`, `backend/config.py:279`

```python
if is_trusted_proxy(peer_ip, TRUSTED_PROXY_IPS):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
```

**Issue:** Render's proxy appends the real IP to the header. The leftmost entry is therefore whatever the client sent.

**Impact depends on how `TRUSTED_PROXY_IPS` is set on Render:**
- **Set:** an attacker rotates spoofed XFF values. That bypasses the per-IP login failure block (20 failures in 15 minutes), every slowapi IP limit, and the register and forgot-password limits.
- **Unset:** every user shares the proxy's IP. About 20 bad logins in 15 minutes would then lock **all** users out of login.

**Fix:** Use the rightmost untrusted hop, or Render's or Cloudflare's single-value client-IP header. Check the Render console for both `TRUSTED_PROXY_IPS` and `FORWARDED_ALLOW_IPS`. The `TRUSTED_PROXY_IPS` check is already an open item in `tasks/ceo-actions.md`.

**Do not** "fix" this by setting `FORWARDED_ALLOW_IPS='*'`. Uvicorn would then let `X-Forwarded-For: 127.0.0.1` pass the loopback gate on `/metrics` (`routes/metrics.py:45`).

### M3. Refresh-token reuse detection expires after about 60 minutes *(verified)*

**Location:** `backend/auth.py:908-918` (`cleanup_expired_refresh_tokens`), scheduled every `CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES=60` (`config.py:668`)

**Issue:** The cleanup job deletes **revoked** rows as well as expired ones. Reuse detection (`auth.py:755`) only works if the revoked row still exists.

**Attack:**
1. An attacker steals a refresh cookie and rotates it first.
2. More than an hour later, the victim's tab presents the old token.
3. The row is gone, so the server returns a plain "Invalid refresh token" and never revokes the token family.
4. The attacker's chain keeps rolling forward 7 days at a time.

**Fix:** Delete revoked rows only once `expires_at < now`.

### M4. Email change requires no current password, so a stolen session becomes a permanent takeover *(verified)*

**Location:** `backend/auth.py:461-470` (`UserProfileUpdate`), `routes/users.py:27-38`, `services/auth/registration.py:201-204`

**Attack:**
1. With a stolen session, the attacker sends `PUT /users/me {"email":"atk@evil"}` and confirms the verification link.
2. They call `/auth/forgot-password` for the new address and reset the password.
3. The email swap revokes no sessions. The original address is notified but cannot undo the change.

Password change already requires the current password (`auth.py:662`); this is the weaker path.

**Fix:** Require `current_password` for an email change, and revoke all refresh tokens when the email swap completes.

### M5. Org members keep a paid tier after the owner downgrades *(verified)*

**Location:** `shared/organization_policy.py:149-150` copies `sub.tier` onto each member. `shared/entitlement_checks.py:86-88` treats a missing Subscription row as "trust the tier".

**Issue:** Members have no Subscription row. An active plan change such as Enterprise→Solo goes through `sync_subscription_from_stripe`, which updates only the owner. `_downgrade_org_members_to_free` runs only for non-entitled statuses. `admin_force_cancel(immediate=True)` (`billing/admin_customers.py:551-554`) has the same gap: it makes no Stripe call, so no webhook arrives.

**Impact:**
1. The owner buys Enterprise and members join.
2. The owner downgrades to Solo.
3. Members keep Enterprise entitlements (bulk upload, branding) indefinitely.

**Fix:** Resolve member entitlements from the org owner's live subscription instead of a copied tier, or propagate every tier change to all members.

### M6. PDF upload decompression bomb / unbounded CPU

**Location:** `backend/shared/pdf_parser.py:120-136`. pdfminer runs `zlib.decompress` with no output cap.

**Issue:**
- The 5-second per-page "timeout" is checked *after* `extract_table()` returns, so it never interrupts a slow page.
- The ZIP ratio and size limits (`upload_pipeline.py:126-186`) do not apply to PDF streams.
- Parsing has no overall time limit.

**Attack:** A verified paid user uploads a roughly 5 MB PDF whose FlateDecode stream expands to gigabytes. The Render worker runs out of memory, and repeated uploads take the API down.

**Fix:** Parse PDFs in a subprocess with `RLIMIT_AS` and a hard wall-clock timeout, or cap total decoded stream bytes.

### M7. A removed member keeps every client they created, with all its engagement data

**Location:** `routes/organization.py:406-441`, `shared/organization_policy.py:162`. The access computation is in `client_manager.py:102-118` and `engagement_manager.py:104-119`.

**Issue:** Clients are owned per user (`Client.user_id`), not per org. Removing a member deletes only the membership row.

**Impact:**
- The departed staffer keeps full read and export access, including the `/export/package` ZIP, to every client and engagement they created, along with colleagues' follow-ups, comments and misstatements.
- At the same moment, the firm **loses** access to those records.
- In reverse, a user who joins an org exposes all their earlier clients to that org.

**Fix:** This is a data-model decision: give clients an `organization_id`, or reassign ownership on removal. It is better as a sprint than a hotfix.

### M8. Any org member can rewrite firm branding *(verified)*

**Location:** `routes/branding.py:45-61` (`_get_branding`), used by `PUT /branding/`, `POST /branding/logo` and `DELETE /branding/logo`

**Issue:** The helper checks the Enterprise tier and org membership, but not the member's role.

**Attack:** A plain `member` changes the header/footer text or uploads a logo. Every memo PDF the firm exports afterwards carries it (`shared/pdf_branding.py:218`).

**Fix:** Require the owner or admin role on the three write routes.

### M9. "Read-only" impersonation can open the customer's Stripe billing portal

**Location:** `routes/billing.py:273-292`

**Issue:** `GET /billing/portal-session` uses `require_current_user`, and GET requests are not blocked for impersonation tokens (`auth.py:303`). The returned portal URL allows plan changes, cancellation and payment-method changes. A superadmin is needed, but this breaks the documented read-only guarantee.

**Fix:** Reject tokens carrying an `imp` claim on this route.

---

## Low findings

| # | Finding | Location | Fix |
|---|---|---|---|
| L1 | `/activity/tool-log` stores an unvalidated `engagement_id` *(verified)*. It works as an existence oracle (500 vs 201) and pollutes data. Sprint 787b fixed the same bug elsewhere. | `routes/activity.py:459-481` | Resolve the engagement through `maybe_record_tool_run`'s ownership check |
| L2 | `ENV_MODE` fails open: an unset or misspelled value means `development`, which silently disables the prod guards (Secure cookies, HSTS, secret hard-fails, `/docs` hiding, the `/metrics` gate, CSRF fallback, email auto-verify) | `config.py:66` | Accept only `{development,test,production}`; refuse to start when `RENDER` is set and the mode is not `production` |
| L3 | Access JWTs stay valid for up to 15 minutes after logout or "revoke all sessions" | `auth_routes.py:440-449, 518-531` | Accept the gap, or add a per-user `sessions_revoked_at` check like `pwd_at` |
| L4 | Older password-reset tokens are not invalidated by a new request, a successful reset, or an email change | `services/auth/recovery.py:94-158` | Mark all of the user's outstanding reset tokens used |
| L5 | Admin plan-override and force-cancel fall back from org_id to user_id, so a stale ID can hit a different customer (Sprint 840 fixed this only for impersonation) | `billing/admin_customers.py:366-371, 539` | Remove the fallback |
| L6 | Share tokens appear in raw gunicorn/uvicorn access logs | `Dockerfile:124`, `routes/export_sharing.py:467` | Disable the gunicorn access log (the app already has a normalized one) |
| L7 | Raw client IP logged when a share passcode doesn't match | `routes/export_sharing.py:300-304` | Use `hash_ip_address` |
| L8 | Export-sharing serves client-supplied bytes (only magic bytes are checked), so a crafted CSV or PDF can be hosted on a Paciolus link | `routes/export_sharing.py:331-341` | Generate shared exports on the server, or run CSV shares through `SafeCsvWriter` |
| L9 | Branding logo dimensions are not checked: a 500 KB PNG can declare 100M+ pixels, decoded on every branded PDF | `routes/branding.py:114-127` | Check dimensions with Pillow at upload |
| L10 | The in-memory rate-limit fallback (during a Redis outage) multiplies every limit by the worker count, about 4× | `shared/rate_limits.py:424` | Intended (Sprint 774); make the uptime check alert on `"degraded"` |
| L11 | Account enumeration via `PUT /users/me` ("Email already in use") | `auth.py:607-609` | Low marginal risk, since registration leaks the same |
| L12 | Org `member` has the same write/archive/hard-delete rights as owner/admin over all clients and engagements; an admin can remove another admin | `client_manager.py:226,285`, `organization.py:413` | Product decision: role-gate destructive operations |
| L13 | `dependency-compliance.yml` has no `permissions:` block | `.github/workflows/dependency-compliance.yml` | Add `permissions: contents: read` |
| L14 | Impersonation tokens omit `pwd_at`, so impersonating any user who has ever changed their password returns 401 (a functional bug, not a hole) | `auth.py:199-208` | Include `pwd_at` |

---

## Quick wins

These are small, contained changes, each roughly a one-sprint batch:

1. Escape memo `Paragraph` inputs (M1) and add a markup regression test.
2. Keep revoked refresh tokens until they expire (M3). This is a one-line filter change.
3. Require `current_password` to change email, and revoke sessions on the swap (M4).
4. Add the role check to branding writes (M8) and block `imp` tokens on the portal route (M9).
5. Validate `engagement_id` on tool-log (L1), whitelist `ENV_MODE` (L2), and invalidate sibling reset tokens (L4).
6. Hash the IP in the passcode log (L7), add `permissions:` to the workflow (L13), and add `pwd_at` to impersonation tokens (L14).

These need a decision or a design:
- **M2:** first check `TRUSTED_PROXY_IPS` and `FORWARDED_ALLOW_IPS` on Render, then change the IP derivation.
- **M5:** how member entitlements should derive from the owner's subscription.
- **M6:** subprocess isolation for the PDF parser.
- **M7 and L12:** the org data-ownership model and role-gating. These need a product call.

## Verified sound (not findings)

- **JWT and CSRF:**
  - JWT: HS256 pinned, `exp`/`iat`/`jti`, prod hard-fails on weak or shared secrets.
  - CSRF: HMAC + `compare_digest`, user-bound, origin allow-list, narrow exempt list.
- **Cookies and passwords:**
  - Cookies: HttpOnly + Secure + SameSite=None in prod; refresh cookie scoped to `/auth`.
  - Login: timing-equalized with generic errors; DB-backed lockout.
  - Reset and verification tokens: 256-bit, hashed, single-use, expiring.
- **Admin, billing and tiers:**
  - Superadmin is granted only by CLI script, and every internal route uses `require_superadmin`.
  - Stripe webhook signature is verified, with atomic dedup.
  - Tier is never accepted from the client.
- **Tenant isolation:**
  - No cross-tenant IDOR in any of the 47 route modules.
  - Child records chain item → engagement → client → accessible user IDs.
  - Share tokens are 256-bit, hashed, expiring, with Argon2id passcodes.
- **Uploads and file parsing:**
  - Body caps: 110 MB global, 100 MB per file.
  - ZIP-bomb limits on XLSX/ODS.
  - defusedxml for OFX/QBO, openpyxl and odfpy.
  - Magic-byte checks; filenames are never used in filesystem paths.
- **Injection:**
  - `SafeCsvWriter` plus a guard test cover CSV/XLSX formula injection.
  - All `text()` SQL uses bound parameters.
  - No eval, pickle, `shell=True`, `dangerouslySetInnerHTML` or SSRF sinks.
- **Hygiene and infrastructure:**
  - Explicit CORS origin list.
  - Nonce-based CSP with `strict-dynamic`, `frame-ancestors 'none'`, and HSTS.
  - Every mutating route has a rate limit.
  - The 500 handler is generic; Sentry scrubs PII.
  - `/docs` is hidden in prod.
  - GitHub Actions are SHA-pinned, with no `pull_request_target`.

## Context

- **Stack:** FastAPI 0.135 / SQLAlchemy 2.0 / Python 3.12 on Render; Next.js 16 / React 19 on Vercel; Neon Postgres; Redis rate limiting; Stripe; R2.
- **Auth pattern:** short-lived in-memory access JWT plus a rotating HttpOnly refresh cookie, and an HMAC CSRF token.
- **Not covered:** runtime or penetration testing, Render and Vercel console settings (except as noted in M2), and third-party provider configuration.
