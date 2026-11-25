/**
 * Tax-figures banners — Sprint 856, per-year sign-off from Sprint 860.
 *
 * Shown, non-dismissible, on each tool that applies built-in statutory
 * figures, and printed as the first line of that tool's CSV export. Each banner
 * names the tax years built in and the years a practitioner has signed off, so
 * a sign-off (recorded in `backend/tax_tables/ty<year>.py`) changes this text.
 * Book-to-Tax, Depreciation and Loan Amortization apply no year-indexed figure
 * and carry no banner.
 *
 * Backend source of truth: `backend/tax_figures_status.py`.
 * `backend/tests/test_tax_figures_status.py` fails if these strings drift from it.
 */

export const W2_TAX_FIGURES_BANNER =
  'Statutory limits built in for tax years 2025 and 2026; signed off by a practitioner: none yet. Other years are refused unless you supply the figures. Verify before relying.'

export const FORM_1099_TAX_FIGURES_BANNER =
  'Reporting thresholds built in for tax years through 2026 (years before 2025 use the 2025 figures); signed off by a practitioner: none yet. Later years are refused until their figures are added. Verify before relying.'
