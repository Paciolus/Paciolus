/**
 * Standard disclaimer set — Sprint 843 (claims review Part 4).
 *
 * Adopted verbatim from `reports/claims-review-2026-10-24.md` ("Standard
 * disclaimer set"); the CEO may edit, and counsel reviews at website-final.
 * One source, so the footer, tool pages and tax tools cannot drift apart.
 * The memo cover and footer equivalents live in the backend
 * (`shared/report_chrome.py`, `shared/memo_base.py`).
 */

export const SITE_FOOTER_DISCLAIMER =
  'Paciolus is data-analytics software for accounting and audit professionals. It does not perform audits, ' +
  'reviews, compilations or attestation, give opinions or tax advice, or produce audit evidence. Paciolus is ' +
  'not affiliated with or endorsed by the IAASB, PCAOB, AICPA, FASB, IASB or IRS. We cite their standards so ' +
  'you can read the source; thresholds no standard sets are our own conventions (Sources & Methodology). ' +
  'You remain responsible for every judgment and conclusion.'

/** Shown on every tool page, above the tool's own disclaimer. */
export const TOOL_RESULTS_DISCLAIMER =
  'Results are automated flags for you to review, not findings or conclusions. A flag doesn’t mean ' +
  'something is wrong, and no flag doesn’t mean nothing is. Decide what to rely on after your own procedures.'

/** 1099, W-2/W-3, Book-to-Tax, Depreciation (MACRS), Loan Amortization. */
export const TAX_TOOL_DISCLAIMER =
  'This is a calculator, not tax advice or a tax return. Paciolus is not a tax preparer and does not file ' +
  'anything with the IRS, SSA or any state. Thresholds, limits and rates come from the tax year you select and ' +
  'may change. Check them against current IRS guidance. Classification, filing decisions and any position taken ' +
  'are yours. If the entity is your attest client, check your independence rules before preparing entries or ' +
  'provisions for it.'

/** Intercompany eliminations, adjusting entries, book-to-tax, financial statements. */
export const INDEPENDENCE_NOTE =
  'If the entity is your attest client, preparing entries or a tax provision is a nonattest service — ' +
  'check your independence rules first.'
