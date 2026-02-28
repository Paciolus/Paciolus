# Weekly Security Event Review — 2026-W09

**Document Classification:** Internal — SOC 2 Evidence Artifact
**Control Reference:** CC4.2 / C1.3 — Detective controls and monitoring evidence
**Status:** PENDING CEO EXECUTION
**Template source:** `docs/08-internal/security-review-template.md`

> **CEO ACTION:** This is the **first weekly security review** for Paciolus. Complete by 2026-03-01 (end of W09).
> Run `python scripts/weekly_security_digest.py` first to pre-populate the Prometheus section.
> After completing and signing: copy to `docs/08-internal/soc2-evidence/c1/security-review-2026-W09.md`.

---

## 1. Review Metadata

| Field | Value |
|-------|-------|
| **Week ending** | 2026-03-01 (Sunday) |
| **ISO week** | 2026-W09 |
| **Review period** | 2026-02-23 (Mon) – 2026-03-01 (Sun) |
| **Reviewer name** | _[CEO ACTION: your name]_ |
| **Reviewer role** | _[CEO ACTION: e.g., CISO / CTO]_ |
| **Review date** | _[CEO ACTION: date completed]_ |
| **Prior review** | First review — no baseline |

---

## 2. Sentry — Application Error Review

**How to access:** sentry.io → [your org] → Issues → filter "Last 7 days"

> **First review note:** No prior-week baseline exists. Record current counts as the baseline for W10.

| Metric | This Week (W09) | Prior Week | Trend | Disposition |
|--------|----------------|-----------|-------|-------------|
| Total new issues | _[CEO ACTION]_ | — (first review) | — | _[CEO ACTION]_ |
| Unresolved P0 issues | _[CEO ACTION]_ | — | — | _[CEO ACTION]_ |
| Unresolved P1 issues | _[CEO ACTION]_ | — | — | _[CEO ACTION]_ |
| Token reuse events (`refresh_token_reuse_detected`) | _[CEO ACTION]_ | — | — | _[CEO ACTION]_ |
| Zero-Storage violation markers | _[CEO ACTION]_ | — | — | _[CEO ACTION]_ |
| Account lockout events | _[CEO ACTION]_ | — | — | _[CEO ACTION]_ |

**Notable issues this week:**

| Issue title | Sentry ID | First seen | Count | Disposition | Action taken |
|-------------|----------|-----------|-------|-------------|-------------|
| _[CEO ACTION: list any P0/P1 issues, or write "None"]_ | | | | | |

---

## 3. Prometheus — Security Metric Review

**How to access:** Run `python scripts/weekly_security_digest.py` with `METRICS_URL` set, or run:
```bash
curl https://[your-api-domain]/metrics
```

> **First review note:** Record cumulative totals as the W09 baseline. Delta will be measurable from W10 onward.

| Metric | W09 Cumulative (baseline) | Threshold | Status |
|--------|--------------------------|---------- |--------|
| `paciolus_billing_redirect_injection_attempt_total` | _[CEO ACTION]_ | >0 = investigate | _[CEO ACTION]_ |
| `paciolus_parse_errors_total` (all formats combined) | _[CEO ACTION]_ | spike = investigate | _[CEO ACTION]_ |
| `paciolus_billing_events_total{event_type="subscription_canceled"}` | _[CEO ACTION]_ | spike = investigate | _[CEO ACTION]_ |
| `paciolus_pricing_v2_checkouts_total` | _[CEO ACTION]_ | — | _[CEO ACTION]_ |
| `paciolus_active_trials` | _[CEO ACTION]_ | — | _[CEO ACTION]_ |
| `paciolus_active_subscriptions` (solo/team/enterprise) | _[CEO ACTION]_ | — | _[CEO ACTION]_ |

**Script output** (paste `weekly_security_digest.py` output here):
```
_[CEO ACTION: paste output]_
```

---

## 4. Auth Events — Log Review

**How to access:** Render dashboard → your service → Logs tab → search for each operation string below.

```bash
# Search Render logs for these strings:
"login_failed"
"account_locked"
"csrf_blocked"
"refresh_token_reuse_detected"
```

| Event type | Count this week | Threshold | Status | Disposition |
|-----------|----------------|-----------|--------|-------------|
| `login_failed` | _[CEO ACTION]_ | >100/min = P1 | _[CEO ACTION]_ | _[CEO ACTION]_ |
| `account_locked` | _[CEO ACTION]_ | Any = investigate | _[CEO ACTION]_ | _[CEO ACTION]_ |
| `csrf_blocked` | _[CEO ACTION]_ | Spike = P2 | _[CEO ACTION]_ | _[CEO ACTION]_ |
| `csrf_validation_failed` | _[CEO ACTION]_ | Spike = investigate | _[CEO ACTION]_ | _[CEO ACTION]_ |
| `refresh_token_reuse_detected` | _[CEO ACTION]_ | Any = P0 | _[CEO ACTION]_ | _[CEO ACTION]_ |
| `request_body_too_large` | _[CEO ACTION]_ | Spike = investigate | _[CEO ACTION]_ | _[CEO ACTION]_ |

**Notable auth events:** _[CEO ACTION: describe any, or "None"]_

---

## 5. Rate Limiting — Log Review

**How to access:** Render logs → search for `"status":429` or `HTTP 429` in access log lines.

| Metric | W09 Count | Threshold | Status |
|--------|----------|---------- |--------|
| HTTP 429 responses total | _[CEO ACTION]_ | >50/min = P2 | _[CEO ACTION]_ |
| Distinct source IPs receiving 429 | _[CEO ACTION]_ | >5 unique = investigate | _[CEO ACTION]_ |
| Most rate-limited endpoint | _[CEO ACTION]_ | — | _[CEO ACTION]_ |

**Notable rate limit events:** _[CEO ACTION: describe any, or "None"]_

---

## 6. Access Changes

> As this is the **first review**, record any access changes made during the platform build-up period (Sprint 449–454 work, 2026-02-20 onward).

| Date | System | Account | Change | Authorized by |
|------|--------|---------|--------|--------------|
| 2026-02-27 | GitHub | — | PR template added (`.github/pull_request_template.md`) | Engineering sprint |
| _[CEO ACTION: any access grants or removals you made this week]_ | | | | |

---

## 7. Escalation Log

_[CEO ACTION: describe any P1/P2 items, or write "No escalations this week."]_

---

## 8. Summary Disposition

| Category | Status |
|----------|--------|
| Sentry errors | _[CEO ACTION: ✅ No issues / ⚠️ Investigated / 🚨 Escalated]_ |
| Prometheus metrics | _[CEO ACTION: ✅ Normal / ⚠️ Anomaly / 🚨 Escalated]_ |
| Auth events | _[CEO ACTION: ✅ Normal / ⚠️ Anomaly / 🚨 Escalated]_ |
| Rate limiting | _[CEO ACTION: ✅ Normal / ⚠️ Spike / 🚨 Escalated]_ |
| Access changes | _[CEO ACTION: ✅ No changes / ℹ️ Changes logged above]_ |

**Overall: _[CEO ACTION: ✅ CLEAN / ⚠️ ITEMS INVESTIGATED / 🚨 ESCALATED]_**

---

## 9. Sign-Off

| Reviewer | Date | Initials |
|----------|------|---------|
| _[CEO ACTION: name]_ | _[CEO ACTION: date]_ | _[CEO ACTION]_ |

---

## 10. Filing Checklist

- [ ] All sections above completed
- [ ] File saved as `docs/08-internal/security-review-2026-W09.md` ✓
- [ ] Copy filed to `docs/08-internal/soc2-evidence/c1/security-review-2026-W09.md`
- [ ] Monday reminder set for W10 (2026-03-02 at 09:00 UTC)

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
*SOC 2 Type II evidence — CC4.2 / C1.3 | Week 2026-W09*
