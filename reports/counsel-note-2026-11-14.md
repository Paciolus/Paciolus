# Note for counsel — data-handling corrections to the legal documents

**Prepared:** 2026-11-14 (Sprint 863) · **For:** Paciolus LLC's counsel, via the CEO
**Status:** proposed changes. Parts A and B are applied on branch `counsel-redline-863`, which must not be
merged until counsel signs off; the live site is unchanged. The DPA is untouched pending the retention
decision below. The Security Policy, Subprocessor List and Data Handling Architecture were corrected on the
same day (they are now published on the website) and are listed in Part C for review.

## Why

The CEO directed on 2026-11-14 that every customer-facing claim must be provable from the code or a
published document, and that a claim that cannot be proven is removed. A website review
(`WEBSITE_REVIEW.md`) and a check of the backend found that the legal documents still contain statements
that are broader than what the system does. Each item below gives the current text, the fact in the
code that contradicts or limits it, and proposed wording. The proposed wording is a starting point for
counsel, not legal advice.

## Facts established from the code (2026-11-14)

1. **Uploads.** Uploaded files are parsed in memory and not saved to the database or file storage. A PDF
   or workbook the user *previews* is held in memory for up to 10 minutes so the tool can reuse it
   (`backend/shared/preflight_cache.py`). Whether the operating system or host ever writes memory to disk
   (swap, crash dumps) is outside the application's control, so "not written to disk" cannot be proven.
2. **Shared reports.** When a user shares a report by link, the complete export file is stored in
   Cloudflare R2 for **24 hours (Professional) or 48 hours (Enterprise)** (`backend/routes/export_sharing.py`).
   The file can contain rows from the client's upload. Paciolus does not encrypt it itself; any
   encryption at rest is Cloudflare's.
3. **Backups (new, live 2026-11-14).** The whole database is copied daily to Cloudflare R2
   (`paciolus-backups`) by a GitHub Actions job, kept as **30 daily and 12 monthly copies**. A deleted
   account therefore remains in older backups for **up to 12 months**. GitHub Actions processes the data
   in transit while the backup and the monthly restore test run.
4. **Retention.** Analysis summaries are *archived* (hidden), not deleted, after 365 days; "Clear history"
   also only hides. Deleting the account removes them from the live database.
5. **Transport.** HTTPS is provided by Vercel and Render; the TLS versions offered are theirs, not set in
   the code.
6. **Flagged account names** come from the client's chart of accounts and can contain a person's name.

## Part A — Privacy Policy (`frontend/src/app/(marketing)/privacy/page.tsx`)

| Line | Current | Issue | Proposed |
|---|---|---|---|
| 340 | "Our server reads the file into memory (it is not written to disk)" | Fact 1 | "Our server reads the file into memory; it is not saved to our database or file storage" |
| 352 | "When the response completes, the uploaded file is released from memory and not kept." | "Released" is not verifiable | "When the response completes, the uploaded file is not kept." |
| 373 | "…held in server memory for the duration of the request and are not written to disk… stored, encrypted, with our storage provider (Cloudflare R2) for up to 48 hours" | Facts 1, 2 | "…held in server memory for the duration of the request and are not saved to our database or file storage… stored with our storage provider (Cloudflare R2) for up to 24 hours (Professional) or 48 hours (Enterprise)" |
| 230, 420 | "Up to 48 hours" | Fact 2 | "Up to 24 hours (Professional) or 48 hours (Enterprise)" |
| 510 | "…deleting your account removes them." | Fact 3 | "…deleting your account removes them from our database; copies in our database backups are deleted as those backups age out, within 12 months." |
| 551 | "TLS 1.2 or higher (1.3 where supported), terminated at Vercel and Render" | Fact 5 | "HTTPS (TLS), provided by our hosting providers Vercel and Render" |
| 600 | Vercel: "United States (Virginia)" | The Subprocessor List says "United States / global edge" (Vercel serves pages from a global network) | "United States / global edge" |
| ~595–615 | Hosting / provider table | Lacks GitHub (backups) and the backup bucket | Add GitHub Actions and Cloudflare R2 backups, per the Subprocessor List v2.1 |

| ~609 | Neon: "Encryption at rest, TLS in transit" | Provider-managed; Paciolus does not verify it (Security Policy §4 says so) | Counsel to decide whether to keep, or say "provider-managed encryption at rest" |
| ~615 | EEA: "we rely on Standard Contractual Clauses (SCCs)…" | The Subprocessor List says each provider's transfer mechanism "is being confirmed". The two cannot both be right | **Counsel to confirm** which transfer mechanism applies per provider before this sentence stays |

**Question for counsel:** with backups retained up to 12 months, how should the Privacy Policy describe
erasure under GDPR Article 17 and the CCPA right to delete (for example, a statement that backup copies are
deleted on their retention schedule and are not restored except to recover the service)?

## Part B — Terms of Service (`frontend/src/app/(marketing)/terms/page.tsx`)

| Line | Current | Issue | Proposed |
|---|---|---|---|
| 361 | "…held in server memory for the duration of the request and is not written to disk" | Fact 1 | "…held in server memory for the duration of the request and is not saved to our database or file storage" |
| 373 | "The uploaded file and the line-level rows in it are then released from memory and not kept" | Fact 1; shared reports | "The uploaded file and the line-level rows in it are not kept, except inside a report you choose to share by link" |
| 429 | "stored encrypted with our storage provider for up to 48 hours" | Fact 2 | "stored with our storage provider for up to 24 hours (Professional) or 48 hours (Enterprise)" |
| 446 | §5.3 "What We Do Not Store: the line-level rows in your uploads…" | Shared reports | Add: "…except inside a report you choose to share by link" |
| 871 | "Uploaded files were never kept; the analysis summaries and engagement entries we hold are deleted with your other stored data" | Absolute; Fact 3 | "Uploaded files are not kept. The analysis summaries and engagement entries we hold are deleted with your other stored data; copies in database backups are deleted as those backups age out, within 12 months." |

## Part C — Documents corrected 2026-11-14, for counsel's review

These are now published on the website (`/security`, `/subprocessors`, `/data-handling`), so they were
corrected to the facts the same day rather than left stating something untrue:

- **Security Policy 3.1:** backups described (previously "no off-provider backup exists"); "not written to
  disk" → "not saved to the database or file storage"; CSRF scope, query scoping, upload limits and
  transport narrowed to what the code does.
- **Subprocessor List 2.1:** GitHub (Actions, backups) added; Cloudflare's row covers backups.
  **Note:** the list and the draft DPA promise to update the list *before* adding a subprocessor. GitHub
  began processing backups before the list was updated. Paciolus has no customers yet, so no notice was
  owed, but counsel may want this recorded.
- **Data Handling Architecture 3.1:** backups row; deletion section states backup retention.

## Part D — Draft DPA (`docs/04-compliance/DATA_PROCESSING_ADDENDUM.md`, not yet offered)

| Clause | Current | Issue |
|---|---|---|
| §2 | "…24–48 hours and then deleted" | Fine as a range; consider the per-plan wording |
| §6 | "…deletion is immediate. On termination, stored data is deleted within 30 days." | Fact 3: backups keep copies up to 12 months. Either change the retention, or state backup retention in §6 |

## What the CEO needs to decide with counsel

1. Approve or edit the Part A and Part B wording; the changes go live only after sign-off.
2. Backup retention: keep 30 daily + 12 monthly and disclose it (current plan), or shorten it so the DPA's
   30-day deletion promise can hold.
3. Whether the Subprocessor List's pre-notification promise needs any record for the GitHub addition.
