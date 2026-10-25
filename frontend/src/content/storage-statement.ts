/**
 * Storage statement — the one sentence about data handling (Sprint 841).
 *
 * CEO decision 2026-10-24 (claims review, Option B): "Zero-Storage" is no
 * longer a promise. Every surface that talks about what happens to customer
 * data says this, in these words, and links to the Trust page lists that name
 * exactly what is kept (`/trust#transparency`, kept in step with the models
 * since Sprint 834).
 *
 * `backend/tests/test_storage_claims.py` fails the build if the retired absolutes
 * (listed in RETIRED_PHRASES there) reappear in customer-facing
 * copy.
 */

/** Uploads only — true as written: files are parsed in memory and not kept. */
export const UPLOAD_HANDLING = 'Your uploaded files are processed in memory and not kept after analysis.'

/** What the database does hold, in one sentence. */
export const WHAT_WE_KEEP =
  'We save your account, client list, analysis summaries and anything you enter in an engagement.'

/** Both halves together — the default wherever there is room. */
export const STORAGE_STATEMENT = `${UPLOAD_HANDLING} ${WHAT_WE_KEEP}`

export const STORAGE_DETAIL_HREF = '/trust#transparency'
export const STORAGE_DETAIL_LABEL = 'See exactly what we keep'
