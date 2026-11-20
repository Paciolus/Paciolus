# Subprocessor List

**Version:** 2.2 · **Last updated:** 2026-11-20 · **Owner:** privacy@paciolus.com · **Classification:** Public

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
| **Render Key Value** | Rate limiting and security counters | Request counters keyed by user ID or IP address; failed sign-ins by IP address; revoked admin-impersonation tokens | United States |
| **Vercel** | Frontend hosting and CDN | IP address, browser details, access logs | United States / global edge |
| **Cloudflare** | R2 object storage for shared reports (`paciolus-exports`) and database backups (`paciolus-backups`) | The PDF / Excel / CSV file a user shares by link, for 24 hours (Professional) or 48 hours (Enterprise); keys are hashes of the share token. A daily copy of the whole database, kept as 30 daily and 12 monthly copies | Eastern North America |
| **GitHub** | Runs the daily database backup and the restore tests (GitHub Actions) | The whole database, in transit, while a backup or restore test runs on a GitHub-hosted runner | Chosen by GitHub |
| **Amazon Web Services (S3)** | Storage for the firm logo used in Enterprise PDF branding | The logo image a firm uploads, stored under its organization ID | United States (region set in configuration; default us-east-1) |
| **Stripe** | Payments and subscriptions | Email, billing details, payment method (card data never reaches Paciolus) | United States |
| **SendGrid** | Transactional email, and delivery of contact-form messages to Paciolus | Email address, name, message content (verification, password reset, billing notices); for the contact form, the sender's name, email, company, inquiry type and message | United States |
| **Sentry** | Error monitoring | User ID, error type and stack location; request bodies, local variables, exception messages and breadcrumbs are stripped before sending | United States |

**Grafana Cloud (Loki)** receives a copy of the application logs only if log shipping is enabled in
production; it is listed here when it is.

Each provider's standard data processing terms apply. Which terms have been formally accepted, and the
transfer mechanism each uses, is being confirmed and will be recorded here.

## Not subprocessors

GitHub's source-code hosting, Cloudflare DNS and Dependabot handle no customer data. (GitHub Actions does, for backups — listed above.)

## Change log

| Date | Change |
|------|--------|
| 2026-11-20 | v2.2 — checked against the code (Sprint 888): Amazon S3 added (firm logos); Render Key Value's security counters and SendGrid's contact-form use stated. |
| 2026-11-14 | v2.1 — database backups added: Cloudflare R2 `paciolus-backups` and GitHub Actions (which runs the backup and restore tests) listed; share-link retention stated per plan. |
| 2026-10-24 | v2.0 — rewritten to the facts (Sprint 845): Neon and Render Key Value added, regions corrected, unverified "DPA Signed" and certification columns removed. |
| 2026-10-23 | v1.1 — Cloudflare R2 added; Google Fonts eliminated (fonts self-hosted). |
