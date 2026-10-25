# Subprocessor List

**Version:** 2.0 · **Last updated:** 2026-10-24 · **Owner:** privacy@paciolus.com · **Classification:** Public

The third parties that process personal data for Paciolus. Version 1.1 listed the database as
"Render (Oregon)" (it is Neon, US East), omitted Neon and Render Key Value, marked every provider's DPA
"Signed" without a record of signature, and described share links as passcode-protected (the passcode is
optional). The previous text is in
[`archive/SUBPROCESSOR_LIST_pre-sprint-845_2026-10-24.md`](archive/SUBPROCESSOR_LIST_pre-sprint-845_2026-10-24.md).

We will update this list before adding a subprocessor and will tell customers who ask to be notified
(privacy@paciolus.com).

## Active Subprocessors

| Provider | What it does | Personal data it processes | Region |
|----------|-------------|----------------------------|--------|
| **Neon** | PostgreSQL database | Accounts (email, name, password hash), client metadata, analysis summaries, flagged account names, engagement entries, activity history, security events | United States (us-east-1) |
| **Render** | Backend hosting and application logs | API requests in transit; logs (no uploaded file contents) | United States |
| **Render Key Value** | Rate limiting | Request counters keyed by user ID or IP address | United States |
| **Vercel** | Frontend hosting and CDN | IP address, browser details, access logs | United States / global edge |
| **Cloudflare** | R2 object storage for shared reports (`paciolus-exports`) | The PDF / Excel / CSV file a user shares by link, for 24–48 hours; keys are hashes of the share token | Eastern North America |
| **Stripe** | Payments and subscriptions | Email, billing details, payment method (card data never reaches Paciolus) | United States |
| **SendGrid** | Transactional email | Email address, name, message content (verification, password reset, billing notices) | United States |
| **Sentry** | Error monitoring | User ID, error type and stack location; request bodies, local variables, exception messages and breadcrumbs are stripped before sending | United States |

**Grafana Cloud (Loki)** receives a copy of the application logs only if log shipping is enabled in
production; it is listed here when it is.

Each provider's standard data processing terms apply. Which terms have been formally accepted, and the
transfer mechanism each uses, is being confirmed and will be recorded here.

## Not subprocessors

GitHub (source code and CI), Cloudflare DNS, and Dependabot handle no customer data.

## Change log

| Date | Change |
|------|--------|
| 2026-10-24 | v2.0 — rewritten to the facts (Sprint 845): Neon and Render Key Value added, regions corrected, unverified "DPA Signed" and certification columns removed. |
| 2026-10-23 | v1.1 — Cloudflare R2 added; Google Fonts eliminated (fonts self-hosted). |
