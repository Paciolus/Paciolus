# Weekly Security Event Review — Template

**Document Classification:** Internal — SOC 2 Evidence Artifact
**Control Reference:** CC4.2 / C1.3 — Detective controls and monitoring evidence
**Template Version:** 1.0
**Source policy:** `docs/04-compliance/SECURITY_POLICY.md` §8.5
**Retention:** 3 years (52 reviews/year × 3 years = 156 files)

> **Usage:** Copy to `docs/08-internal/security-review-YYYY-WNN.md`, fill in all sections, sign off, then file a copy in `docs/08-internal/soc2-evidence/c1/`. Run `scripts/weekly_security_digest.py` first to pre-populate Prometheus data.

---

## 1. Review Metadata

| Field | Value |
|-------|-------|
| **Week ending** | [YYYY-MM-DD] (Sunday of the review week) |
| **ISO week** | [YYYY-WNN] (e.g., 2026-W09) |
| **Reviewer name** | [name] |
| **Reviewer role** | [e.g., CISO / CTO] |
| **Review date** | [YYYY-MM-DD] (date this form was completed) |
| **Prior review** | [YYYY-WNN or "First review"] |

---

## 2. Sentry — Application Error Review

**How to access:** sentry.io → [org] → [project] → Issues (filter: last 7 days)

| Metric | This Week | Prior Week | Trend | Disposition |
|--------|----------|-----------|-------|-------------|
| Total new issues | | | ↑/↓/→ | |
| Unresolved P0 issues (critical) | | | | |
| Unresolved P1 issues (error) | | | | |
| New token reuse events (`refresh_token_reuse_detected`) | | | | |
| New Zero-Storage violation markers | | | | |
| New account lockout events | | | | |

**Disposition codes:** `False alarm` / `Expected load` / `Investigated` / `Escalated`

**Notable issues this week** (list any new P0/P1 or security-relevant issues):

| Issue title | Sentry ID | First seen | Count | Disposition | Action taken |
|-------------|----------|-----------|-------|-------------|-------------|
| | | | | | |

_If no notable issues: write "None — no P0/P1 issues this week."_

---

## 3. Prometheus — Security Metric Review

**How to access:** Run `scripts/weekly_security_digest.py` or query `GET /metrics` directly.

> **Note:** Rate limit hit counts and CSRF failure counts are in application logs (JSON), not in Prometheus. See Section 5 for log-based review.

| Metric | This Week delta | Cumulative | Threshold | Status |
|--------|----------------|-----------|---------- |--------|
| `paciolus_billing_redirect_injection_attempt_total` | | | >0 = investigate | |
| `paciolus_parse_errors_total` (all formats) | | | spike = investigate | |
| `paciolus_billing_events_total{event_type="subscription_canceled"}` | | | spike = investigate | |
| `paciolus_pricing_v2_checkouts_total` | | | baseline | |
| `paciolus_active_trials` (gauge) | | | — | |
| `paciolus_active_subscriptions` (gauge, by tier) | | | — | |

**Prometheus digest output** (paste output from `weekly_security_digest.py` here):
```
[paste script output]
```

---

## 4. Auth Events — Log Review

**How to access:** Render log stream → filter by `"operation":` → grep for security operation names below.

```bash
# Useful log queries (run against structured JSON log output):
grep '"operation":"login_failed"'          # Failed login attempts
grep '"operation":"account_locked"'        # Accounts locked out
grep '"operation":"csrf_blocked"'          # CSRF validation failures
grep '"operation":"csrf_validation_failed"' # CSRF token invalid
grep '"operation":"refresh_token_reuse"'   # Token reuse attempts
grep '"operation":"request_body_too_large"' # Oversized requests
```

| Event type | Count this week | Alert threshold | Status | Disposition |
|-----------|----------------|-----------------|--------|-------------|
| `login_failed` | | >100/min = P1 | | |
| `account_locked` | | Any = investigate | | |
| `csrf_blocked` | | >10/min = P2 | | |
| `csrf_validation_failed` | | Spike = investigate | | |
| `refresh_token_reuse_detected` | | Any = P0 | | |
| `request_body_too_large` | | Spike = investigate | | |

**Notable auth events** (describe any accounts locked, IPs with repeated failures, etc.):

_[None / describe events]_

---

## 5. Rate Limiting — Log Review

**How to access:** Render log stream → look for HTTP 429 responses in access logs.

| Metric | Count this week | Threshold | Status |
|--------|----------------|---------- |--------|
| HTTP 429 responses total | | >50/min = P2 | |
| Distinct IPs receiving 429 | | >5 unique = investigate | |
| Endpoints most frequently rate-limited | | | |

**Notable rate limit events:**

_[None / describe]_

---

## 6. Access Changes

Any new access grants or removals since the prior review.

| Date | System | Account | Change | Authorized by |
|------|--------|---------|--------|--------------|
| | | | | |

_If no changes: write "No access changes this week."_

---

## 7. Escalation Log

> Complete this section only if any P1/P2 items were identified.

| # | Issue description | Severity | Date identified | Action taken | Status |
|---|-----------------|---------|----------------|-------------|--------|
| | | | | | |

_If no escalations: write "No escalations this week."_

---

## 8. Summary Disposition

| Category | Status |
|----------|--------|
| Sentry errors | ✅ No issues / ⚠️ Issues investigated / 🚨 Escalated |
| Prometheus metrics | ✅ Normal / ⚠️ Anomaly investigated / 🚨 Escalated |
| Auth events | ✅ Normal / ⚠️ Anomaly investigated / 🚨 Escalated |
| Rate limiting | ✅ Normal / ⚠️ Spike investigated / 🚨 Escalated |
| Access changes | ✅ No changes / ℹ️ Changes logged above |

**Overall: ✅ CLEAN / ⚠️ ITEMS INVESTIGATED / 🚨 ESCALATED**

---

## 9. Sign-Off

| Reviewer | Date | Initials |
|----------|------|---------|
| [name] | [YYYY-MM-DD] | |

By signing, the reviewer attests that all sections above were reviewed and all anomalies were dispositioned.

---

## 10. Filing

After completion:
1. Save this file as `docs/08-internal/security-review-YYYY-WNN.md`
2. Copy to `docs/08-internal/soc2-evidence/c1/security-review-YYYY-WNN.md`

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
*SOC 2 Type II evidence template — CC4.2 / C1.3*
