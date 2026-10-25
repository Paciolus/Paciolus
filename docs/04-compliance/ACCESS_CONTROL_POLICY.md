# Access Control Policy

**Version:** 2.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

Version 1.2 required MFA for all production and admin access, described quarterly access reviews and
said no employee could possibly access customer data and there was
"no admin override". The app has no MFA, the first quarterly review was never completed, and a platform
administrator can view customer accounts and start a read-only impersonation session. This version
states that. The previous text is in
[`archive/ACCESS_CONTROL_POLICY_pre-sprint-845_2026-10-24.md`](archive/ACCESS_CONTROL_POLICY_pre-sprint-845_2026-10-24.md).

## Customer access

| Tier | Access |
|------|--------|
| **Free** | Trial balance diagnostics and flux analysis; 10 uploads a month; 3 clients; no exports |
| **Solo** | All tools; one seat |
| **Professional** | All tools; up to 20 seats; organization features and export sharing |
| **Enterprise** | All tools; up to 100 seats; custom PDF branding |

Every request is authenticated (15-minute access token + rotating refresh cookie) and every database
query is scoped to the signed-in account or its organization in application code. Organization roles
are owner, admin and member. Audit and export endpoints require a verified email.

## Operator access

- **One platform administrator role (superadmin).** It can list and view customer accounts, adjust
  plans, issue credits and refunds, revoke sessions, erase an account on request, and start a
  **read-only, 15-minute impersonation session**. Impersonation cannot write — the auth layer refuses
  every POST, PUT, PATCH and DELETE — and start/end are recorded in the admin audit log.
- Internal revenue metrics are visible only to that role.
- **No multi-factor authentication exists in the app**, including for the administrator. MFA on the
  infrastructure accounts (GitHub, Render, Neon, Vercel, Cloudflare, Stripe, SendGrid, Sentry) is
  being confirmed account by account; in-app MFA is planned.
- Production secrets live in the Render and Vercel dashboards, not in the repository.

## Reviews

There is no formal periodic access review today. Operator access is the founder's; it is reviewed when
anyone else is given access.
