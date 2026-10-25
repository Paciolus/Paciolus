# Incident Response Plan

**Version:** 2.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

Version 1.0 described PagerDuty and Datadog alerting, a two-engineer on-call rotation, five-minute
acknowledgement, a status page and published post-incident reports. None of those exist. This version
is what a solo-operated service actually does. The previous text is in
[`archive/INCIDENT_RESPONSE_PLAN_pre-sprint-845_2026-10-24.md`](archive/INCIDENT_RESPONSE_PLAN_pre-sprint-845_2026-10-24.md).

## How incidents are noticed

- **Errors:** Sentry captures unhandled errors (alert routing is per the Sentry project settings).
- **Availability:** a GitHub Actions probe checks the live site and its readiness endpoint every
  15 minutes and fails visibly when either is wrong. (Its deploy-version check needs a
  `RENDER_API_KEY` repository secret, which is not yet set.) GitHub can delay scheduled runs, so this
  is a coarse signal, not real-time paging.
- **Security events:** failed logins, lockouts, refresh-token reuse, impersonation and account erasure
  are logged; the critical ones are stored in the `security_events` table for 365 days.
- **Reports:** security@paciolus.com (see the [Vulnerability Disclosure Policy](VULNERABILITY_DISCLOSURE_POLICY.md)).

There is **no 24/7 on-call**. Incidents are handled by the founder as soon as they are seen, which
outside working hours may be the next morning.

## What happens

1. **Assess** what is affected and whether personal data may have been exposed.
2. **Contain**: revoke sessions (password-change and reuse detection already revoke all of a user's
   sessions), rotate secrets on Render, block the cause, or take the affected feature offline.
3. **Fix and verify**, including confirming that the live deploy is the fixed version.
4. **Notify** if personal data was or may have been exposed:
   - affected customers, by email, without undue delay;
   - regulators as the law requires — for example within 72 hours to an EU supervisory authority
     under GDPR Article 33, and as state breach-notification laws require.
5. **Record** what happened and what changed in `tasks/` and, for affected customers, send them a
   written summary.

## Contacts

security@paciolus.com for security reports; privacy@paciolus.com for data questions. Providers'
own status pages (Render, Neon, Vercel, Cloudflare, Stripe, SendGrid) are checked during an incident.
