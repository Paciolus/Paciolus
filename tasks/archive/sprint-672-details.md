# Sprint 672 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 672: Loan Amortization XLSX + PDF Export
**Status:** COMPLETE
**Source:** Sprint 625 follow-up — XLSX and PDF deferred at sprint close
**File:** `backend/routes/loan_amortization.py`, `backend/loan_amortization_excel.py` (new), `backend/pdf/sections/loan_amortization.py` (new), `frontend/src/app/tools/loan-amortization/page.tsx`, `backend/tests/test_loan_amortization_exports.py` (new)
**Problem:** Sprint 625 shipped the loan amortization engine, route, CSV export, and frontend in a single sprint and deferred the XLSX and PDF exports. Auditors routinely paste amortization schedules into engagement workpapers — XLSX preserves cell formatting and lets preparers roll up totals with `SUM()`, and PDF produces a pagination-clean evidence document for the workpaper file.
**Changes:**
- [x] `loan_amortization_excel.py` — openpyxl workbook with three sheets (Schedule, Annual Summary, Inputs), currency number-format on monetary columns, percentage format on rate cells, frozen schedule header row, and auto-sized columns
- [x] `pdf/sections/loan_amortization.py` — landscape-letter SimpleDocTemplate, inputs table + 4-card summary + annual summary table + period-by-period table using `repeatRows=1` so the schedule header re-renders on every page
- [x] `POST /audit/loan-amortization/export.xlsx` and `POST /audit/loan-amortization/export.pdf` — `require_verified_user`, rate-limited under `RATE_LIMIT_AUDIT`
- [x] Frontend: generalized `downloadCsv` into `downloadExport(format)` accepting `csv | xlsx | pdf`, added three download buttons that appear once a schedule has been generated
- [x] 12 new tests in `test_loan_amortization_exports.py` — sheet count, row count, frozen-panes assertion, currency format check, total-interest cell round-trip, inputs-sheet echo, extra-payments rendering, PDF magic header, multi-page page-count check, interest-only method, and route-registration assertion

**Review:**
- The XLSX "totals" row mirrors the CSV's trailing totals convention — `Totals` label in column 1, `total_interest` in the interest column, `total_payments` in the ending-balance column. Locating the row by label in the test rather than row index keeps the assertion stable if future rows are inserted above it.
- The PDF uses landscape letter because eight numeric columns at 360 rows need ~8.4" of horizontal space. Portrait crammed the "Date" and "Period" columns unreadably narrow in spike testing.
- PDF pagination is driven by ReportLab's natural flow + `repeatRows=1` — no manual page-break logic. The test counts `/Type /Page\n` occurrences in the raw PDF bytes to confirm >1 page; at 360 rows the document lands around 42 KB across ~11 pages.
- Row backgrounds in the schedule alternate white/oatmeal-paper so long tables remain readable when scanned row-by-row in print. Colors come from `ClassicalColors` (pdf.styles) — no ad-hoc hex codes.
- Frontend: the refactor from a single `downloadCsv` to `downloadExport(format)` removes three near-identical `fetch` blocks in favor of one parameterized function. Buttons share the sage-600 pill style for CSV/XLSX and obsidian-700 for PDF so the PDF (evidence-grade output) visually anchors the set.
- Total coverage added: 269 backend tests pass across the Sprint 661-664 + 672 change surface. Loan amortization engine tests (pre-existing 30+) untouched.
