/**
 * Storage statement — every sentence the site says about customer data (Sprint 841, Sprint 861).
 *
 * CEO decision 2026-10-24 (claims review, Option B): "Zero-Storage" (a retired term) is no
 * longer a promise. CEO decision 2026-11-14 (website review): a claim we
 * cannot prove from the code is removed, not reworded. Every surface that
 * talks about customer data uses the constants below, and the lists here are
 * the single source for both the Trust page and the Approach page.
 *
 * Facts these sentences rest on (re-check them before changing any wording):
 * - Uploads are parsed in memory and not saved. A PDF or workbook the user
 *   previews is held in memory for up to 10 minutes so the tool can reuse it
 *   (`backend/shared/preflight_cache.py`, TTL_SECONDS = 600).
 * - A report shared by link is the complete export file, stored with
 *   Cloudflare R2 for 24 h (Professional) or 48 h (Enterprise), then deleted
 *   (`backend/routes/export_sharing.py`).
 * - Analysis summaries are archived (hidden) after RETENTION_DAYS, not
 *   deleted; deleting the account deletes them from the database
 *   (`backend/retention_cleanup.py`).
 * - The database is backed up daily to Cloudflare R2 `paciolus-backups`:
 *   30 daily + 12 monthly copies (`.github/workflows/backup-pg-dump.yml`), so
 *   a deleted account stays in older backups for up to 12 months.
 * - Flagged account names come from the client's chart of accounts and can
 *   contain a person's name.
 *
 * `backend/tests/test_storage_claims.py` fails the build if the retired
 * absolutes reappear in customer-facing copy.
 */

/** Uploads only — true as written: files are parsed in memory and not kept. */
export const UPLOAD_HANDLING = 'Your uploaded files are processed in memory and not kept after analysis.'

/** What the database does hold, in one sentence. */
export const WHAT_WE_KEEP =
  'We save your account, client list, analysis summaries and anything you enter in an engagement.'

/** Both halves together — the CEO-approved wording, used verbatim wherever there is room. */
export const STORAGE_STATEMENT = `${UPLOAD_HANDLING} ${WHAT_WE_KEEP}`

export const STORAGE_DETAIL_HREF = '/trust#transparency'
export const STORAGE_DETAIL_LABEL = 'See exactly what we keep'

/** Shared-link retention, by plan. */
export const SHARE_RETENTION =
  'up to 24 hours (Professional) or 48 hours (Enterprise), then deleted'

/** The preview cache — the one case where an upload stays in memory after the request. */
export const PREVIEW_CACHE =
  'A PDF or workbook you preview before running a tool is held in memory for up to 10 minutes so the tool can reuse it, then released.'

/** How long what we keep is kept. */
export const RETENTION_STATEMENT =
  'Analysis summaries and engagement entries are kept while your account is open. Deleting your account deletes them from our database; copies in our database backups are deleted as those backups age out, within 12 months.'

/** Division of responsibility — CEO-approved wording. */
export const RESPONSIBILITY_STATEMENT =
  'Paciolus produces PDF memos and Excel/CSV workpapers. Your firm keeps them in its own documentation system; Paciolus is not a workpaper archive.'

/** Documentation obligations — CEO-approved wording; names no standard. */
export const DOCUMENTATION_STATEMENT =
  'Paciolus is not a substitute for your firm’s audit documentation and retention obligations.'

/** What the database and our storage provider hold. Single source for Trust and Approach. */
export const WE_KEEP: readonly string[] = [
  'Your account information (name, email)',
  'Client metadata (names, industries, fiscal year-ends)',
  'A summary of each analysis: category totals, ratios, row counts, total debits and credits',
  'Names of accounts a tool flagged, without amounts. Account names come from your chart of accounts and can include a person’s name',
  'What you enter in an engagement: materiality, follow-up items, intercompany account mappings, analytical-expectation workpapers (expected and actual values) and misstatement workpapers (account, debit or credit, amount)',
  `Reports you share by link: the complete file, stored with our storage provider for ${SHARE_RETENTION}`,
  'Counts of which tools you run and how many uploads you make (for your upload allowance)',
  'A daily backup of everything above except shared reports, kept with a separate storage provider as 30 daily and 12 monthly copies',
]

/** What we don't keep — each line true as written, exceptions stated. */
export const WE_DONT_KEEP: readonly string[] = [
  'Uploaded files (CSV, Excel, PDF or any other format)',
  'The rows in your uploads — balances, journal entries, invoices, payments or payroll records — unless they are in a report you share by link',
  'The entries and amounts behind a flag, unless they are in a report you share by link',
]
