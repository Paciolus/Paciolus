# Sprints 621–625 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 621: h3 font-serif Brand Remediation
**Status:** COMPLETE
**Source:** Designer — brand mandate violation
**File:** `frontend/src/app/dashboard/page.tsx:360, 397`, `frontend/src/app/tools/page.tsx:124`, `frontend/src/app/(diagnostic)/recon/page.tsx:58, 63, 68`, `frontend/src/components/sensitivity/WeightedMaterialityEditor.tsx:100`, `frontend/src/app/status/page.tsx:182`, `frontend/src/app/internal/admin/customers/[orgId]/page.tsx:155`, `frontend/src/components/workspace/RecentHistoryMini.tsx:125`
**Problem:** Seven `<h3>` headings explicitly use `font-sans` — brand mandate requires `font-serif` on all headers. These are labelled section headings, not UI labels.
**Changes:**
- [x] Replace `font-sans` with `font-serif` at all seven sites (or use `type-tool-section` utility)
- [x] Grep remaining `<h[1-6].*font-sans` across `frontend/src/` and fix any stragglers
**Review:** Fixed 10 sites total (7 cited + 3 stragglers in admin customers page and RecentHistoryMini). Grep for `<h[1-6].*font-sans` returns zero across `frontend/src/`. Commit `299175c`.

---

### Sprint 622: Dashboard Favorite Toggle A11y
**Status:** COMPLETE
**Source:** Designer — mobile/screen-reader invisible
**File:** `frontend/src/app/dashboard/page.tsx:364-368`, `frontend/src/app/tools/page.tsx:138-141`
**Problem:** Favorite button uses `opacity-0 group-hover:opacity-100` with only `title=` attribute. Screen readers on mobile (no hover) never surface it. `title` alone fails WCAG 4.1.2 (accessible name).
**Changes:**
- [x] Add `aria-label={favorites.includes(tool.key) ? 'Remove from favorites' : 'Add to favorites'}`
- [x] Add `focus-visible:opacity-100` so keyboard focus surfaces the button
**Review:** Applied to both dashboard and tools page favorite buttons (same a11y pattern). Both retain `title` for cursor hover hint and now expose `aria-label` for screen readers + `focus-visible:opacity-100` for keyboard focus. Commit `94024a8`.

---

### Sprint 623: focus:outline-hidden Uniform Sweep
**Status:** COMPLETE
**Source:** Designer — Tailwind v3/v4 semantic inconsistency
**File:** `frontend/src/app/(auth)/forgot-password/page.tsx:133`, `frontend/src/app/(auth)/reset-password/page.tsx:213, 228`, `frontend/src/app/(marketing)/pricing/page.tsx:302`, `frontend/src/components/pricing/PricingEstimator.tsx:138`
**Problem:** Five inputs use `focus:outline-none` (v3 keyword) while 75 other occurrences across the codebase use `focus:outline-hidden` (v4 alias). Inconsistent semantics; v3 maps to `outline: 0` which removes native outline before the ring renders.
**Changes:**
- [x] Replace all five occurrences with `focus:outline-hidden`
- [x] Grep to confirm no remaining `focus:outline-none` in `frontend/src/`
**Review:** All five replaced. Final grep returns zero `focus:outline-none` matches in `frontend/src/`. Commit `be54bbb`.

---

### Sprint 624: Interest Coverage Ratio
**Status:** COMPLETE
**Source:** Accounting Auditor + Future-State — quick win capability gap (Priority 4.0)
**File:** `backend/ratio_engine.py` (CategoryTotals.interest_expense, INTEREST_EXPENSE_KEYWORDS, RatioEngine.calculate_interest_coverage), `backend/audit/pipeline.py` (consolidation summing), `backend/tests/test_ratio_core.py` (9 new tests), `backend/tests/test_cash_conversion_cycle.py` (count update)
**Problem:** 17+ ratios implemented but no EBIT / interest expense ratio. Interest expense is already extracted from the TB keyword list. Every going concern and solvency engagement requires this.
**Changes:**
- [x] Add `calculate_interest_coverage()` in `ratio_engine.py` returning `RatioResult`
- [x] Logic: EBIT / interest expense. If interest expense = 0, return N/A with "No interest-bearing debt detected"
- [x] Thresholds: <1.5x elevated, 1.5x–3.0x watch, >3.0x adequate
- [x] Include in `calculate_all_ratios()` dict + PDF memo Ratio section (PDF section already had it via financial_statement_builder path)
- [x] Tests for positive, zero, negative EBIT paths
**Review:** `interest_expense` added to `CategoryTotals` with `__post_init__`, `to_dict`, `from_dict` updates. New `INTEREST_EXPENSE_KEYWORDS` list with `income`/`receivable` exclusion to keep interest income/receivables out. Pipeline consolidation now sums `interest_expense` and `operating_expenses` (latter was a pre-existing gap). Total ratios now 18 (was 17). All 163 ratio/CCC tests green; 9 new tests cover adequate, watch, elevated, negative EBIT, zero-interest, derived-opex, calculate_all wiring, extraction, and interest-income-not-misclassified paths. Commit `57af39c`.

---

### Sprint 625: Loan Amortization Generator (Quick Win, Priority 9/2)
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #5
**File:** `backend/loan_amortization_engine.py` (new), `backend/routes/loan_amortization.py` (new), `backend/routes/__init__.py`, `backend/tests/test_loan_amortization_engine.py` (new, 18 tests), `frontend/src/app/tools/loan-amortization/page.tsx` (new), `frontend/src/app/tools/page.tsx` (catalog entry)
**Problem:** Every entity with debt needs this. Universal monthly use, direct revenue driver for Solo/Professional. Deterministic math, form-input only, no upload.
**Changes:**
- [x] New engine `backend/loan_amortization_engine.py` — principal, rate, term, frequency, start date, method (SL/interest-only/balloon), extra payments, variable rate support
- [x] Period-by-period schedule output + total interest + payoff date + annual summary + JE templates
- [x] New route `backend/routes/loan_amortization.py` + schemas
- [x] Frontend: form-only page under `frontend/src/app/tools/loan-amortization/page.tsx`
- [x] CSV export (`/audit/loan-amortization/export.csv`); Excel XLSX and PDF export deferred to a follow-up sprint when the PDF section framework can render schedule tables natively.
- [x] Zero-storage compliant (form input, no upload)
**Review:** Decimal-precision math with HALF_UP quantization at the schedule boundary. Standard 30-yr/6% loan test matches the published $1,199.10/mo textbook payment within $0.05 and ends at exact zero. Balloon, interest-only, variable-rate, extra-payment, and zero-rate paths all have dedicated tests. Frontend page lives at `/tools/loan-amortization` with inputs → summary → annual table → full schedule → JE templates, and a CSV download. Catalog entry added to `tools/page.tsx` under "Advanced". 18/18 engine tests pass; `npm run build` succeeds; `main.py` loads all 216 routes cleanly. **Follow-up:** XLSX + PDF export for this tool — new sprint when scheduled (matches the same deferral pattern we use for other PDF memos).

---
