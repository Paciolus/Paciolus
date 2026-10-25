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

## 2. What is stored, and where

### 2.1 Summary

| Data | Store | Retention |
|------|-------|-----------|
| **Accounts and settings** | Neon PostgreSQL, us-east-1 | Until account deletion |
| **Client metadata** | Neon | Until deleted |
| **Analysis summaries** | Neon | 365 days, then archived; deleted with the account |
| **Tool Run Records** | Neon | Run status, score and the flagged account names (no amounts) for each tool run in an engagement |
| **Engagement entries** (materiality, follow-ups, intercompany mappings, analytical expectations, uncorrected misstatements) | Neon | Until you delete them or the account |
| **Sessions and security events** | Neon | Session tokens hashed, until expiry; security events (hashed IP) 365 days |
| **Shared report files** | Cloudflare R2 `paciolus-exports`, keyed by a hash of the share token | 24 h (Professional) / 48 h (Enterprise); the DB row is removed only after R2 confirms deletion |
| **Rate-limit counters** | Render Key Value | Short-lived |

Exported PDFs, Excel and CSV files are generated on request and sent to the browser without being
saved — except a report you share by link, as above.

### 2.2 Controlled Storage Exceptions

Every table that holds amounts or account identifiers, so nothing is stored that this page does not
name. (`backend/tests/test_zero_storage_disclosure.py` fails the build if a table with money or account
columns is missing here.)

#### Users Table

Email, name, bcrypt password hash, tier, settings. Until account deletion.

#### Clients Table

Client name, industry, fiscal year-end. Until deleted.

#### Activity Logs Table

Per analysis: row count, total debits and credits, materiality, balanced flag, anomaly counts, first characters of the filename and its hash. Archived after 365 days.

#### Diagnostic Summaries Table

Per analysis: category totals (assets, liabilities, revenue, expenses …), ratios, total debits and credits. Archived after 365 days.

#### Tool Sessions Table

Saved adjusting entries (accounts and amounts) and currency rate tables, for 1–2 hours.

#### Engagements Table

Period, status, materiality amounts the user sets. Until deleted.

#### Tool Runs Table

Per tool run in an engagement: status, composite score and the names of flagged accounts (no amounts).

#### Follow-Up Items Table

Narratives the user writes about flagged items, and comments.

#### Subscriptions Table

Plan, status, seats, Stripe IDs, upload counts.

#### Billing Events Table

Plan changes and payments (tier, interval, amounts in metadata); kept with the user unlinked after erasure.

#### Uncorrected Misstatements Table

What the user enters: accounts affected with debit/credit and amount, F/S impact.

#### Analytical Expectations Table

What the user enters: expected values, precision thresholds, actual values and variances.

#### Admin Audit Logs Table

Superadmin actions, including credit and refund amounts. Append-only.

#### Tool Activities Table

Per tool use: tool name, first characters of the filename, and a short caller-supplied summary (up to 2,000 characters).

### 2.3 What is never kept

Uploaded files, and the line-level rows in them — individual balances, journal entries, invoices,
payments and payroll records.

## Deletion

"Clear history" and "delete engagement" **archive** records. **Deleting your account**
(Settings → Profile → Your Data) physically removes everything above that belongs to you, cancels
your subscription with Stripe and removes your shared files from R2; billing history is kept with your
identity removed. You can download everything first from the same page.

## Why it matters, accurately stated

Not keeping uploads means there are no uploaded files or ledger rows at rest to leak. It does **not**
mean there is nothing to protect: the summaries and engagement entries above are client financial
content and are protected as described in the [Security Policy](SECURITY_POLICY.md).
