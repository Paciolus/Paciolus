# Data Handling Architecture

**Version:** 3.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

*(Filename kept for link stability. Paciolus no longer describes itself as "Zero-Storage": the word read
as a promise about all data, and the database does store summaries and engagement content. The earlier
versions are in [`archive/`](archive/).)*

## In one sentence

Your uploaded files are processed in memory and not kept after analysis; we save your account, client
list, analysis summaries and anything you enter in an engagement.

## The life of an upload

1. **Receive.** The file arrives in the request body (capped at 110 MB; files at 100 MB / 500,000
   rows). Multipart parts are kept in memory up to the request cap rather than spooled to disk.
2. **Validate.** Signature, size, row/column/cell limits, archive-bomb limits per format, `defusedxml`.
3. **Analyse** in memory. If you previewed the file first, its bytes are held in an in-memory cache for
   up to 10 minutes, bound to your account and consumable once.
4. **Respond** with the results.
5. **Release.** The file and its rows leave memory. A **summary** is saved to your history: category
   totals, ratios, row counts, total debits and credits, materiality, anomaly counts, the first
   characters of the filename and its hash — and, when a tool flags accounts, their **names** (no amounts).

Nothing from the upload is written to disk, and nothing from it reaches the logs or Sentry: application
logs carry exception type names only, and Sentry events have request bodies, local variables, exception
messages and breadcrumbs removed before they are sent.

## What is stored, and where

| Data | Store | Retention |
|------|-------|-----------|
| Account (email, name, bcrypt hash), settings | Neon PostgreSQL, us-east-1 | Until account deletion |
| Client metadata | Neon | Until deleted |
| Analysis summaries, flagged account names, activity history | Neon | 365 days, then archived; deleted with the account |
| Engagement entries you type (materiality, follow-ups, intercompany mappings, analytical expectations, uncorrected misstatements) | Neon | Until you delete them or the account |
| Session tokens (hashed), security events (hashed IP) | Neon | Sessions until expiry; security events 365 days |
| Shared report files | Cloudflare R2 `paciolus-exports`, keyed by a hash of the share token | 24 h (Professional) / 48 h (Enterprise); the DB row is removed only after R2 confirms deletion |
| Tool session state (adjusting entries, currency rates) | Neon `tool_sessions` | 1–2 hours |
| Rate-limit counters | Render Key Value | Short-lived |

Exported PDFs, Excel and CSV files are generated on request and sent to the browser without being
saved — except a report you share by link, as above.

## Deletion

"Clear history" and "delete engagement" **archive** records. **Deleting your account**
(Settings → Profile → Your Data) physically removes everything above that belongs to you, cancels
your subscription with Stripe and removes your shared files from R2; billing history is kept with your
identity removed. You can download everything first from the same page.

## Why it matters, accurately stated

Not keeping uploads means there are no uploaded files or ledger rows at rest to leak. It does **not**
mean there is nothing to protect: the summaries and engagement entries above are client financial
content and are protected as described in the [Security Policy](SECURITY_POLICY.md).
