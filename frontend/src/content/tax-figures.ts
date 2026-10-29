/**
 * Tax-figures banners — Sprint 856 (793b: statutory figures awaiting
 * practitioner confirmation).
 *
 * Shown, non-dismissible, on each tool that applies built-in statutory
 * figures, and printed as the first line of that tool's CSV export. The text is
 * per tool because the tables differ: W-2 has a 2025 table only and refuses
 * other years; Form 1099 has 2025 and 2026 tables. Book-to-Tax, Depreciation and
 * Loan Amortization apply no year-indexed figure and carry no banner.
 *
 * Backend source of truth: `backend/tax_figures_status.py`.
 * `backend/tests/test_tax_figures_status.py` fails if these strings drift from it.
 */

export const W2_TAX_FIGURES_BANNER =
  'Statutory limits built in for tax year 2025 only, pending practitioner confirmation — other years are refused unless you supply the figures. Verify before relying.'

export const FORM_1099_TAX_FIGURES_BANNER =
  'Reporting thresholds built in through tax year 2026; the 2026 figures come from secondary sources and await practitioner confirmation, and later years reuse them with a notice. Verify before relying.'
