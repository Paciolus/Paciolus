# Sprints 665–667 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-15.
> CEO remediation brief v6 — diagnostic harness + intake hardening + risk
> scoring/conclusion logic. Sprints 668–671 remain pending in Active Phase.

---

### Sprint 665: Diagnostic Remediation Test Harness
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — pre-req for sprints 666–671
**File:** `tests/qa/run_remediation_sweep.py` (new), `reports/remediation/baseline/` (new)
**Problem:** No end-to-end harness runs preflight + diagnostic on a TB file and dumps the sections the remediation brief asks about (intake summary, column detection, conclusion, risk score, exception details). Without one, we cannot mechanically validate each fix against its Expected Result, and we cannot diff before/after on the six test files.

**Decision:** Build a read-only Python script, not a pytest case. The harness is a CEO-facing validator, not a regression gate — pytest would force us to hardcode expected values that are about to change over the next six sprints. A script that writes structured JSON per test file lets us eyeball the diff each sprint and keeps the evolving expectations in the sprint review sections, not in assertion code.

**Changes:**
- [x] `tests/qa/run_remediation_sweep.py` (new) — `--out <subdir>` flag, iterates the six files in `tests/evaluatingfiles/`, runs `parse_uploaded_file_by_format` → `run_preflight` → `audit_trial_balance_streaming`, writes one JSON dump per file to `reports/remediation/<subdir>/<stem>.json`. Each record captures: parse (columns, row_count, first/last row samples), full preflight `to_dict()`, slimmed diagnostic (risk_score, risk_tier, risk_factors, coverage_pct, anomaly_types, top 25 abnormal_balances), and a structured `errors[]` array with stage + type + traceback for any pipeline stage that raised. On failure, other stages still run so we can see partial success.
- [x] `reports/remediation/baseline/` — six JSONs captured against pre-remediation code. Each subsequent sprint will write to `reports/remediation/sprint-NNN/` and diff.
- [x] Script prints a one-line summary per file so the CEO can scan without opening JSON.
- [x] Harness installed `python-docx` into the backend venv (the package was missing and the docx parser raised HTTP 500 before it could reach the data-extraction layer). That install is the reason the brief's Issue 14 is now reproducible end-to-end; without python-docx the failure mode was "parse errors before diagnostic ever ran," which would have hidden the downstream pipeline routing bug.

**Review:**
- [x] Ran clean from `D:\Dev\Paciolus` with the backend venv. Elapsed 2.6s across all 6 files.
- [x] Baseline reproduces every issue in the remediation brief:
  - **Issue 1** — `clean.csv` → diagnostic `elevated(42)` with 4 material exceptions on a perfectly clean TB
  - **Issue 2** — `outofbalance.csv` → `diff=$200,000.00` (brief says should be $100k); `clean.csv` → `rows=41` (brief says should be 40 + 1 totals row)
  - **Issue 3** — `outofbalance.csv` → `elevated(42)`, exactly the same score as `clean.csv`; out-of-balance condition contributes zero risk points
  - **Issue 5 (BLOCKING)** — `no_headers.csv` → diagnostic `low(0)` with `mat=0 anom=0` on a file where ingestion dropped rows; silent success confirmed
  - **Issue 6** — `no_headers.csv` → account column = `"Cash - Operating Account"` at 0.7 confidence (row-1 data treated as header)
  - **Issue 7** — `no_headers.csv` → `rows=39` (file has 40 data rows; one lost to pandas header inference)
  - **Issue 9** — `unusual_accounts.csv` → `diff=$306,262.00` on a file built to balance; confirms RFC 4180 quoted-field corruption
  - **Issue 10** — `unusual_accounts.csv` → `mat=5` but the file contains ~10 genuinely suspicious accounts
  - **Issue 11** — `adjusted.pdf` → debit column mapped to `"Beg Balance\nDebit"` instead of Ending Balance
  - **Issue 12** — `adjusted.pdf` → `diff=$-67,000.00` despite the file being built to balance; artifact of incomplete column mapping
  - **Issue 16** — `hartwell.docx` → debit column = `"Dr / Cr"` at 0.7, credit column = `missing`; net-balance layout not recognized

- **Bonus finding — broadens Sprint 671 scope:** The diagnostic ingestion layer at `backend/security_utils.py:201` (`process_tb_chunked`) only dispatches CSV then Excel — it has no path for PDF, DOCX, ODS, OFX, QBO, IIF, TSV, or TXT. Both `adjusted.pdf` and `hartwell.docx` fail the diagnostic with the same downstream error (`OptionError: No such keys(s): 'io.excel.zip.reader'` / `ValueError: Excel file format cannot be determined`). Preflight handles these formats correctly via `parse_uploaded_file_by_format` in `shared/helpers.py:797`, but the diagnostic never calls that dispatcher — it routes straight to `process_tb_chunked`. Sprint 671 was originally scoped as "docx pipeline + duplicate UX"; the real fix is to route *all* non-CSV/non-Excel formats through the parser dispatch at the diagnostic ingestion layer. We'll confirm exact approach when we get to Sprint 671, but noting it now so the scope is not underestimated.

- **Note on harness limitation** — the harness runs each file in isolation, so the brief's Issue 15 (duplicate detection blocking after session-prior CSVs) cannot be exercised by the current sweep. Sprint 671 will need a supplementary test case for sequential uploads, or validation against the live API. Filing for attention at that sprint.

- Commit SHA: `4263c6c`

---

### Sprint 666: Intake Hardening — Zero-Row Block, Totals Row Exclusion, Row Reconciliation
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — Issues 5 (BLOCKING), 9, 2, 7
**Files:** `backend/shared/intake_utils.py` (new), `backend/preflight_engine.py`, `backend/audit/pipeline.py`, `backend/audit/streaming_auditor.py`, `backend/routes/audit_diagnostics.py`, `backend/tests/test_intake_utils.py` (new), `backend/tests/test_audit_core.py` (test_empty_file rewritten for new behavior)
**Problem:** Four related intake failures surfaced by the Sprint 665 baseline sweep. (5) `tb_no_headers.csv` → diagnostic `low(0)` with `mat=0 anom=0`: ingestion dropped all rows because column detection failed, and the pipeline silently returned "balanced / no exceptions." (9) `tb_unusual_accounts.csv` → preflight diff=$306,262 attributed to "RFC 4180 quoted-field parse corruption." (2) Summary totals row treated as a data row — `clean.csv` → false null warning; `outofbalance.csv` → variance doubled from $100k to $200k because the totals row sum was added to the real data sum on both sides. (7) `no_headers.csv` → preflight reports 39 rows on a 40-row file; one row silently consumed by pandas header inference.

**Issue 9 finding — brief was misdiagnosed:**
A direct audit of the CSV parser against `tb_unusual_accounts.csv` confirmed pandas' default QUOTE_MINIMAL handling is correct. Every quoted field in the file (`"Temp Clearing - DO NOT USE"`, `"A/P - K.H. Owner Loan (personal?)"`, `"Meals/Ent 50% (non-ded?)"`) parses without column shift — those fields contain no embedded commas, only parentheses/slashes/question marks which are not CSV-special characters. A manual sum of the 53 non-totals data rows produces debit=$5,796,762 and credit=$5,490,500 — a genuine $306,262 imbalance that is NOT a parsing artifact. The brief's claim that "the file was built to balance" did not match the actual file contents. After this sprint the reported variance for that file is $306,262 — unchanged from baseline, but for the right reason now: the totals row is correctly excluded and the variance reflects real ledger data, which is exactly what the Issue 9 Expected Result asks for ("reports an accurate variance that reflects actual ledger data, not parsing artifacts").

**Decision:**
Push totals-row detection and row reconciliation into a new `shared/intake_utils.py` module that both pipelines import, rather than duplicating heuristics in preflight and diagnostic. The tight heuristic — "last three rows, every account-identifier column blank, both debit AND credit non-zero" — safely distinguishes totals rows from legitimate one-sided data rows (like row 6055 in `unusual_accounts.csv` which has a blank account name but only a debit populated). Two-sided contra-accounts like Accumulated Depreciation are never mistaken for totals rows because they have non-blank names.

**Changes:**
- [x] `backend/shared/intake_utils.py` (new, ~210 lines) — `IntakeSummary` dataclass with `reconciles()` invariant, `count_raw_data_rows()` for CSV/TSV/TXT raw line counting (returns None for binary formats), `detect_totals_row()` and `exclude_totals_row()` helpers with the tight heuristic above. Every account-identifier column (`account`, `acct`, `gl *`, `code`, `no`, `number`, `name`) must be blank for a candidate to qualify — multi-column TBs with both Account No and Account Name are handled correctly.
- [x] `backend/preflight_engine.py` — added `intake: IntakeSummary | None` to `PreFlightReport`, accept optional `rows_submitted: int | None` kwarg on `run_preflight`, apply totals-row exclusion before every downstream check (`_check_tb_balance`, `_check_null_values`, `_check_duplicates`, `_check_encoding`, `_check_mixed_signs`, `_check_zero_balances`). Row reconciliation uses the column-detection result to decide whether a real header was consumed: if both Debit and Credit columns resolved to real names, subtract 1 from `rows_submitted` for the header line; otherwise leave it full so the header-less case (`tb_no_headers.csv`) is reconciled as `submitted=40, accepted=39, rejected=1` rather than `submitted=39, accepted=39, rejected=0`.
- [x] `backend/audit/pipeline.py` — Issue 5 BLOCKING guard: after Stage 1 ingestion, if `auditor.total_rows == 0` OR `auditor.debit_col is None` OR `auditor.credit_col is None`, short-circuit the pipeline and return a `TrialBalanceResponse`-compatible failure dict with `analysis_failed=True`, `failure_reason=("zero_rows_ingested" | "columns_not_detected")`, and `error_message="ANALYSIS COULD NOT BE COMPLETED — ..."`. The safe-default fields (`balanced=False`, empty `classification_quality`, empty `balance_sheet_validation`, etc.) satisfy the Pydantic response schema so FastAPI can serialize the failure; downstream consumers MUST check `analysis_failed` before interpreting any other field.
- [x] `backend/audit/streaming_auditor.py` — `process_chunk` now detects totals rows (blank account name + both debit and credit non-zero) and zeroes their debit/credit values before `math.fsum`, so they do not contribute to the balance check or account-level aggregates. Excluded rows are tracked via `self.totals_rows_excluded` and surfaced through `get_balance_result()` as a new `totals_rows_excluded` field. `missing_names_count` is corrected to subtract totals rows (they are a pipeline artifact, not a data quality issue).
- [x] `backend/routes/audit_diagnostics.py` — `preflight_check` now passes `rows_submitted=count_raw_data_rows(file_bytes, filename)` so the intake summary reconciles correctly for production uploads.
- [x] `tests/qa/run_remediation_sweep.py` — harness also passes `rows_submitted` and captures `intake`, `analysis_failed`, `failure_reason`, `totals_rows_excluded` in the slim diagnostic dump. The one-line summary now shows `intake=S/A/R/X` format (submitted/accepted/rejected/excluded).
- [x] `backend/tests/test_intake_utils.py` (new, 29 tests) — full coverage of `count_raw_data_rows` (CSV/TSV/TXT/XLSX/PDF/DOCX/missing/empty/Latin-1), `detect_totals_row` (all-blank vs one-sided, position scan, multi-id-column, NaN handling, currency strings), `exclude_totals_row` (non-mutating), and `IntakeSummary.reconciles()` invariant.
- [x] `backend/tests/test_audit_core.py::test_empty_file` — rewritten. The old assertion was validating the silent-success bug itself (expected `status="success"`, `balanced=True`, `row_count=0` on a headers-only file). The new assertion enforces the post-fix contract: `status="failed"`, `analysis_failed=True`, `failure_reason="zero_rows_ingested"`, `balanced=False`, and the blocking error message contains the mandated "ANALYSIS COULD NOT BE COMPLETED" prefix.

**Validation (via Sprint 665 harness, `reports/remediation/sprint-666/`):**
- [x] `tb_hartwell_clean.csv` — intake=41/40/0/1, preflight `Ready(100.0)`, balance `diff=$0.00`. Totals row excluded, false null warning gone.
- [x] `tb_hartwell_outofbalance.csv` — intake=41/40/0/1, balance **`diff=$100,000.00`** (was $200,000 in baseline). Real data variance, not doubled.
- [x] `tb_no_headers.csv` — intake=40/39/1/0 with note "1 row consumed as header row," diagnostic **`DIAG_FAILED[zero_rows_ingested]`** with the full blocking error message. Silent success eliminated — this was the BLOCKING issue.
- [x] `tb_unusual_accounts.csv` — intake=54/53/0/1, balance `diff=$306,262.00`. Same number as baseline, but now reflects the real data imbalance (rows 0–52 after excluding totals row 53) rather than a totals-inclusive miscalculation. Brief's RFC 4180 claim is misdiagnosed; documented in Review above and in a new lesson.
- [x] `tb_hartwell_adjusted.pdf` — unchanged by this sprint. Preflight `diff=$-67,000.00` (Issue 12, Sprint 667). Diagnostic still fails at `process_tb_chunked` because the ingestion layer doesn't route PDFs (bonus finding from Sprint 665 — Sprint 671 territory).
- [x] `tb_hartwell.docx` — unchanged. Preflight parses (37 rows), diagnostic fails at routing layer. Sprint 671 territory.
- [x] Backend test suite: 125 audit/preflight tests pass (`test_preflight`, `test_audit_core`, `test_audit_anomalies`, `test_audit_api`, `test_audit_pipeline_routes`, `test_audit_validation`); 29 new `test_intake_utils` tests pass; total 154 green.
- [x] Commit SHA: `9a25077`

---

### Sprint 667: Risk Scoring + Conclusion Logic
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — Issues 3, 4, 12
**Files:** `backend/shared/tb_diagnostic_constants.py`, `backend/audit/pipeline.py`, `backend/pdf/sections/diagnostic.py`, `backend/preflight_memo_generator.py`, `backend/preflight_engine.py`, `backend/tests/test_preflight_memo.py`, `tests/qa/run_remediation_sweep.py`
**Problem:** (3) TB out-of-balance condition appears only in the executive banner and contributes nothing to risk score — clean and out-of-balance files both return 42/ELEVATED with the same four findings. (4) PreFlight Downstream Impact correctly marks issues as invalidating, then Conclusion says testing can proceed anyway (appeared in 4 of 6 test runs). (12) Balance check runs even when balance columns are Unmapped, producing a $67k artifact on `tb_hartwell_adjusted.pdf`.

**Decision:**
The remediation brief frames Issue 3 as "add OOB to the score." We went one step further and made it a *dominant* +60 signal that anchors the factor decomposition as P1 — a TB that does not reconcile invalidates every downstream test by definition, and no combination of "clean" exception counts should be allowed to obscure that. On Issue 4 the historic conclusion text was readiness-score-keyed, which is why "Ready with minor issues" rendered on files with high-severity column-detection failures; we re-keyed it on highest severity present, so the conclusion can no longer contradict the Downstream Impact section. On Issue 12 we considered (a) inferring multi-column layouts from the column names and silently picking ending-balance columns, (b) emitting a partial variance with a caveat, or (c) skipping the check entirely. Picked (c) for Sprint 667: it is the smallest correct fix and the full multi-column detector is Sprint 669 territory. The balance check now returns a `skipped=True` sentinel, the conclusion suppresses the OOB blocker on skipped runs, and the user-visible message names the unmapped columns so the next step is obvious.

**Changes:**
- [x] `backend/shared/tb_diagnostic_constants.py` — added `tb_out_of_balance` entries to `SUGGESTED_PROCEDURES` and `MATERIAL_PROCEDURE_UPGRADES` (STOP-and-escalate language, calls out partner escalation in the material variant); routed `anomaly_type == "tb_out_of_balance"` through `get_tb_suggested_procedure()`; extended `compute_tb_diagnostic_score()` with `tb_out_of_balance: bool` and `tb_imbalance_amount: float | Decimal` kwargs that prepend a `("Trial balance out of balance by $X", 60)` factor — dominant over every other contributor (60 alone lands in High; combined with material findings escalates further). Decimal coercion is defensive against any caller that hands us a non-numeric.
- [x] `backend/audit/pipeline.py` — Stage-3.5 OOB injection: when `result["balanced"] is False` AND the difference is non-zero, synthesise a P1 abnormal-balance entry (`account="Trial Balance — Overall"`, `anomaly_type="tb_out_of_balance"`, severity high, confidence 1.0) and prepend it to `abnormal_balances` so it renders as the first material exception. The injected entry is excluded from coverage_pct denominators and from the material count passed to `compute_tb_diagnostic_score()` so it isn't double-weighted (60 from the flag + 8 per material entry would have inflated the score). The companion flag is passed to scoring so the +60 factor anchors the decomposition.
- [x] `backend/pdf/sections/diagnostic.py` — material findings sort key changed to `(anomaly_type != "tb_out_of_balance", -abs(amount))` so the OOB entry pins to the top of the Exception Details table regardless of per-account amount.
- [x] `backend/preflight_engine.py` — added `_has_unmapped_balance_columns()` helper that recognises debit/credit/balance/dr/cr tokens in unmapped column names; `_check_tb_balance()` accepts an optional `all_columns` kwarg and, when extra balance-like columns are present, appends a medium-severity `tb_balance` issue ("Balance check skipped — one or more balance columns are unmapped … unmapped balance-like columns: 'X', 'Y' …") and returns a `BalanceCheck` sentinel with `balanced=False, difference=0.0, skipped=True`. Added `skipped: bool = False` field to the `BalanceCheck` dataclass and surfaced it through `to_dict()`. The single call site at `run_preflight()` now passes `all_columns=column_names`.
- [x] `backend/preflight_memo_generator.py::_build_conclusion()` — fully rewritten and re-keyed off severity:
  - No issues → `"Ready"`
  - Medium-only (no high) → `"Ready with caveats"`
  - Any high → `"Review Required"` (forbidden phrase `"do not prevent diagnostic testing from proceeding"` removed; replaced with `"do not record conclusions against the affected figures until the issues are remediated"`)
  - Hard OOB blocker preserved but suppressed when `balance_check.skipped is True` so a skipped multi-column run cannot render `"out of balance by $0.00"`
  - Per-issue caveats now include a `tb_balance` clause for the Sprint 667 skip case
- [x] `tests/qa/run_remediation_sweep.py` — harness now imports `_build_conclusion`, calls it against the preflight dict, and stores the rendered text under `preflight.rendered_conclusion`. Lets Issue 4 be validated mechanically by grepping the JSON for the forbidden phrase across all six test files.
- [x] `backend/tests/test_preflight_memo.py` — added 3 contract tests under `TestPreflightConclusion`: (a) high-severity → `"Review Required"` and forbidden phrase absent, (b) medium-only → `"Ready with caveats"` and not `"Review Required"`, (c) skipped balance check → no `"out of balance"` text.

**Validation (via Sprint 665 harness, `reports/remediation/sprint-667/`):**
- [x] `tb_hartwell_outofbalance.csv` → `diag=high(100)` (was `elevated(42)`); P1 abnormal balance is the injected `tb_out_of_balance` entry with `amount=$100,000`; conclusion = critical OOB blocker
- [x] `tb_hartwell_clean.csv` → conclusion = `"Ready"` ("suitable for all downstream diagnostic testing with no caveats"); diagnostic still `elevated(42)` because the four large-account "exceptions" are Sprint 668 territory (materiality-coverage vs. structural-anomaly split)
- [x] `tb_hartwell_adjusted.pdf` → preflight `diff=$0.00` (was `$-67,000.00`); balance check `skipped=True`; conclusion = `"Ready with caveats"` and explicitly does NOT report out-of-balance
- [x] **All six rendered conclusions** grep clean for the forbidden phrase `"do not prevent diagnostic testing from proceeding"` (validated programmatically against `reports/remediation/sprint-667/*.json`)
- [x] `tb_no_headers.csv` and `tb_hartwell.docx` correctly route to `"Review Required"` because of high-severity column-detection failures
- [x] Backend test suite — 186 green: 154 audit/preflight regression (`test_preflight`, `test_audit_core`, `test_audit_anomalies`, `test_audit_api`, `test_audit_pipeline_routes`, `test_audit_validation`, `test_intake_utils`), 29 preflight memo, 3 new Sprint 667 contract tests
- [x] Commit SHA: _pending this commit_

**Note on Issue 1 (clean TB scoring 42/ELEVATED):**
Sprint 667 deliberately did not touch the four-fake-exceptions contribution on the clean file. That's the materiality-coverage-vs-structural-anomaly split which is Sprint 668's scope. The clean file still reads `elevated(42)` after this sprint, but that score is now correct relative to the *current* model: there are 4 abnormal_balances on the file at material level, each contributing 8 risk points. Sprint 668 will reclassify those as "materiality coverage analysis" rather than exceptions, after which the clean file will land below the elevated threshold.

---
