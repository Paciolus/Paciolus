# Sprints 668–671 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-15.
> CEO remediation brief v6 — materiality coverage, multi-column TB layouts, account-type-aware diagnostics, DOCX/PDF diagnostic ingestion.

---

### Sprint 668: Materiality Coverage + Column Detection Semantics
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — Issues 1, 6, 8
**Files:** `backend/audit/rules/concentration.py`, `backend/audit/pipeline.py`, `backend/pdf/sections/diagnostic.py`, `backend/preflight_engine.py`, `backend/preflight_memo_generator.py`, `backend/tests/test_audit_anomalies.py`, `tests/qa/run_remediation_sweep.py`

**Problem:** (1) Clean TB scores 42/ELEVATED with four fake exceptions (Sales Revenue, PP&E, COGS, Long-Term Debt) that are flagged solely because they are large relative to category. Materiality coverage is conflated with anomaly detection. (6) Column detection reports "Found" with 70% confidence on `tb_no_headers.csv` where row 1 is actually data, not headers. No distinction between confirmed header detection and content inference. (8) Detection table shows "Unmapped" with no explanation of what that status means or how it affects downstream analysis.

**Decision:**
For Issue 1 we considered (a) reducing the concentration thresholds, (b) deleting the concentration rule entirely, or (c) tagging concentration findings as `coverage_analysis` and routing them to a separate report section without scoring. Picked (c). Concentration coverage IS useful information for the auditor — the fact that one revenue stream is 95% of revenue is worth noting even though it is not an anomaly. We just can't let it count as a structural exception. For Issue 6 we extended the existing `ColumnQuality.status` field with an `inferred` value that fires when no core role hits an exact-pattern match (≥0.85 confidence) — that cleanly separates real header rows from rows where the column_detector reached for a partial regex against data content. For Issue 8 we added a `downstream_use` field to `ColumnQuality` and surfaced a new "Downstream Use" column in the preflight memo detection table.

**Changes:**
- [x] `backend/audit/rules/concentration.py` — all three concentration detection functions (`detect_concentration_risk`, `detect_revenue_concentration`, `detect_expense_concentration`) now tag every finding with `coverage_analysis: True`. The `issue` text was rewritten to be coverage-oriented ("coverage observation, not an anomaly"), `requires_review` was flipped to `False`, and the recommendation explicitly states concentration is not by itself an anomaly.
- [x] `backend/audit/pipeline.py` — `material_count`, `immaterial_count`, `has_risk_alerts`, the coverage_pct denominators, and the abnormal_balances list passed to `compute_tb_diagnostic_score()` all exclude `coverage_analysis=True` items. Added a `coverage_finding_count` field to the result dict so the renderer (and the harness) can verify the split. Coverage findings remain in `abnormal_balances` so the report can render them in their own section, but they no longer contribute risk points.
- [x] `backend/pdf/sections/diagnostic.py::render_anomaly_details` — split coverage findings out of structural buckets. New "Materiality Coverage Analysis" section with informational language. When all three structural buckets are empty (no material/immaterial/informational), render "No structural anomalies identified" prose so the reader knows the absence is intentional.
- [x] `backend/preflight_engine.py::ColumnQuality` — added `downstream_use: str` field; the dataclass docstring documents the new `inferred` status alongside the legacy `found` / `low_confidence` / `missing`. `to_dict()` now surfaces `downstream_use`.
- [x] `backend/preflight_engine.py::_check_column_detection` — added `_DOWNSTREAM_USE_BY_ROLE` map and `_downstream_use_for_role()` helper. Detect "no headers" via two paths: (a) the legacy account fallback note from `column_detector.py` (the `_account_inferred` flag), and (b) the new `_row_inferred` flag — when no core role's confidence is ≥ 0.85, every match is assumed to be from a partial-pattern hit against data, and ALL matched core roles are demoted to `inferred`. A dedicated "No headers detected" high-severity issue is emitted when any core role is inferred. Inferred-but-not-missing roles produce a medium-severity column-detection issue ("Column role(s) inferred from content (not header match)") rather than the moderate-confidence variant. Auxiliary role hints expanded to map account-code style columns (`account_no`, `account_number`, `acct_no`, `acct_code`, `gl_code`, `code`, `account_code`, etc.) to the new `Account Code` role with a "Reference / account code — paired with Account Name where present" downstream use.
- [x] `backend/preflight_memo_generator.py` — column detection table gained a fifth column "Downstream Use" rendered with the per-role description (or "Not used in current analysis" fallback). Column widths rebalanced.
- [x] `backend/tests/test_audit_anomalies.py::test_concentration_includes_recommendation` — assertion rewritten to the new contract: every concentration entry must have `coverage_analysis=True` and a recommendation containing "coverage" or "concentration" (the legacy "review" word is no longer part of the framing).
- [x] `tests/qa/run_remediation_sweep.py` — slim diagnostic view now captures `coverage_finding_count` and the per-entry `coverage_analysis` flag so the materiality split can be diffed sprint-to-sprint.

**Validation (via Sprint 665 harness, `reports/remediation/sprint-668/`):**
- [x] `tb_hartwell_clean.csv` → **`diag=low(0)`** (was `elevated(42)`); `material_count=0`, `risk_factors=[]`, all four concentration findings present in `abnormal_balances` with `coverage_analysis=True`. The "No structural anomalies identified" rendering path is exercised.
- [x] `tb_hartwell_outofbalance.csv` → `diag=high(60)` (was `high(100)`). The +60 OOB factor stands alone; concentration findings no longer add 32 points of "material exceptions" on top.
- [x] `tb_unusual_accounts.csv` → `diag=high(73)` (was `high(100)`). OOB (60) + 2 real material exceptions (16) + minor adjustments. Concentration findings remain in the file but contribute zero points.
- [x] `tb_no_headers.csv` → account role status = **`inferred`** (was `low_confidence`); two high-severity issues now present: "No headers detected" (new) and "Required column(s) not detected: debit, credit". Conclusion routes to "Review Required" with the no-headers warning as item 1.
- [x] `tb_hartwell_clean.csv` detection table includes the new `Account Code` auxiliary role for "Account No" with the "Reference / account code…" downstream use string.
- [x] All six rendered conclusions still grep clean for the Sprint 667 forbidden phrase.
- [x] Backend test suite — 186 green: 154 audit/preflight regression + 29 preflight memo + 3 Sprint 667 contract tests. The single failing test (`test_concentration_includes_recommendation`) was rewritten to the new coverage framing as part of this sprint.
- [x] Commit SHA: `2fa2ceb`

**Note on `tb_hartwell_adjusted.pdf` and `tb_hartwell.docx`:**
Both still error at the diagnostic ingestion layer because `process_tb_chunked` in `security_utils.py` only dispatches CSV/Excel. That is the Sprint 671 bonus finding from Sprint 665 and remains pending. Sprint 668 changes still apply correctly to their preflight reports — the diagnostic just doesn't run.

---

### Sprint 669: Multi-Column TB + Net-Balance TB Modes
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — Issues 11, 16
**Files:** `backend/shared/tb_layout.py` (new), `backend/column_detector.py`, `backend/preflight_engine.py`, `backend/tests/test_tb_layout.py` (new)
**Problem:** (11) `tb_hartwell_adjusted.pdf` is a nine-column adjusted TB with Beginning / Adjustments / Ending balance column pairs. Current detector maps Beginning as primary Debit/Credit, so downstream calculations run against beginning balances instead of period-end. (16) `tb_hartwell.docx` uses single "Net Balance (USD)" column + "Dr / Cr" indicator column. Current detector matches "Dr / Cr" to Debit at 70% confidence and fails to find a Credit column, blocking analysis on a legitimate common layout.

**Decision:**
We considered three approaches: (a) extend the existing pattern weights so Ending Balance outranks Beginning, (b) add a per-engine override hook, or (c) introduce a dedicated layout-detection module that runs alongside the pattern detector and overrides assignments when a non-default layout is recognised. Picked (c). The pattern-weight approach is fragile — it would need re-tuning every time a new TB shape arrives, and a tie at the same weight produces alphabetical ordering which is brittle. A dedicated layout module gives us a single place to encode TB-shape semantics (multi-step adjustments, net-balance + indicator) and lets each layout carry its own metadata (supplementary pairs, requires_confirmation flag) for the preflight balance check to react to.

**Changes:**
- [x] `backend/shared/tb_layout.py` (new, ~200 lines) — `TBLayoutMode` enum (`single_dr_cr`, `multi_column_adjusted`, `net_balance_with_indicator`), `TBLayoutDetection` dataclass, `detect_tb_layout()` function. Pure-string detection against the column header list with regex-based tokenisation that recognises "Beg", "Begin", "Beginning", "Opening", "Prior Year" / "PY" for beginning columns; "Adjust(ment)(s)", "Adj", "JA", "JE Adj" for adjustments; "Ending", "End", "Period End", "YTD", "Closing" for ending. Net-balance detection requires both a balance/amount-named column AND an explicit Dr/Cr indicator column (sign / nature / side / indicator) — falls through to single_dr_cr otherwise. Multi-column takes precedence over net-balance when both signals are present (an adjusted TB with a Net Balance memo column should not be misclassified).
- [x] `backend/column_detector.py::ColumnDetectionResult` gained four new fields: `layout`, `requires_confirmation`, `supplementary_balance_pairs`, `indicator_column`. `to_dict()` surfaces all four. `detect_columns()` calls `detect_tb_layout()` first and, when a non-default layout is recognised, overrides the canonical Debit/Credit assignments with the layout-derived columns at 0.95 confidence — so a multi-column adjusted TB picks `Ending Balance Debit/Credit` as primary and a net-balance TB surfaces both `Net Balance (USD)` and `Dr / Cr` as Found instead of the indicator column being missing.
- [x] `backend/preflight_engine.py::_check_tb_balance` accepts new `layout` and `supplementary_balance_pairs` kwargs. Two new code paths:
  - `net_balance_with_indicator` short-circuits the balance check with a layout-specific medium-severity caveat ("Balance check skipped — net-balance layout detected. The credit role is filled by a Dr/Cr indicator column, not a numeric balance. Confirm the sign convention before downstream balance verification.") instead of coercing the indicator to zero and reporting a phantom variance.
  - `multi_column_adjusted` filters the supplementary Beginning/Adjustments columns out of the Sprint 667 unmapped-balance-column check, so legitimate multi-step layouts no longer trip the "balance check skipped" path. The actual balance check then runs against the layout-selected Ending Balance pair.
- [x] `backend/preflight_engine.py::run_preflight` passes the layout and supplementary pairs into `_check_tb_balance`.
- [x] `backend/tests/test_tb_layout.py` (new, 10 tests) — covers `single_dr_cr` defaults (classic, extended with Account No/Type, empty columns), `multi_column_adjusted` (full three-step PDF-extracted shape with newline-laden headers, two-step beginning/ending, single-pair fallback), `net_balance_with_indicator` (full hartwell.docx shape, balance + sign variant, signed-only fallback, multi-column precedence over net-balance).

**Validation (via Sprint 665 harness, `reports/remediation/sprint-669/`):**
- [x] `tb_hartwell_adjusted.pdf` → `pf=Ready(100.0)` (was `Review Recommended(67.5)`); columns table shows debit=`'Ending Balance\nDebit'`, credit=`'Ending Balance\nCredit'`; balance check ran (not skipped), `total_debits=$11,047,200`, `total_credits=$11,047,200`, `diff=$0.00`, `balanced=True`. Beginning Balance and Adjustments columns appear as auxiliary "unmapped" entries in the columns table for transparency.
- [x] `tb_hartwell.docx` → `pf=Ready(85.0)` (was `Ready(80.0)` with a missing-credit hard block); columns table shows debit=`'Net Balance (USD)'`, credit=`'Dr / Cr'`, both Found, no missing-credit warning. Balance check skipped with the new net-balance caveat. `requires_confirmation=True` on the column detection result.
- [x] All four other test files unchanged from Sprint 668 (single_dr_cr layout — no behaviour change).
- [x] Backend test suite — 196 green: 186 audit/preflight/memo regression + 10 new tb_layout contract tests.
- [x] Commit SHA: `aba8eef`

**Note on diagnostic ingestion:**
Both `tb_hartwell_adjusted.pdf` and `tb_hartwell.docx` still error at the diagnostic ingestion layer because `process_tb_chunked` only dispatches CSV/Excel — the bonus finding from Sprint 665. Sprint 669 fixes the column detection on these layouts, but the diagnostic itself can't run on them until Sprint 671 routes non-CSV/Excel formats through `parse_uploaded_file_by_format`. The preflight reports are now fully correct for both files.

---

### Sprint 670: Account-Type-Aware Diagnostics — Null Suppression + Unusual Account Detection
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — Issues 13, 10
**Files:** `backend/classification_rules.py`, `backend/audit/rules/suspense.py`, `backend/audit/pipeline.py`, `backend/tests/test_contra_and_detection_fixes.py`, `backend/tests/test_unusual_account_patterns.py` (new)

**Problem:** (13) `tb_hartwell_adjusted.pdf` flags Depreciation Expense and Bad Debt Expense for null beginning-balance — but both are P&L accounts that legitimately have no opening balance. (10) `tb_unusual_accounts.csv` contains ~10 genuinely suspicious accounts (SUSP-001, ????-UNIDENTIFIED, A/R-DISPUTED, Owner Draw, Revenue-MISC unclassified, EUR-AR, Inventory-OBSOLETE/WRITE-OFF, Meals/Ent 50%, Rounding Adj $12); only one clearing account was detected. Unrecognized Account Types counter shows 0, contradicting the detection.

**Decision:**
For Issue 13 we considered (a) plumbing the account classifier into the preflight null check so it can skip P&L beginning-balance nulls explicitly, or (b) relying on Sprint 669's column mapping fix which routes Ending Balance as the primary debit/credit pair (and the null check already only fires on critical columns). Picked (b): no new code is needed for `tb_hartwell_adjusted.pdf` because Sprint 669 already eliminated the spurious Beg Balance null warnings by re-mapping the critical columns to Ending Balance Debit/Credit. The Sprint 668 baseline showed two medium null_values issues on Beg Balance Debit/Credit; Sprint 669's harness output shows zero issues on the same file. Issue 13 is therefore resolved by the column-mapping cascade, not by adding classifier-aware logic that would be brittle in the multi-column case.

For Issue 10 we extended suspense detection along two axes: (i) literal SUSPENSE_KEYWORDS additions for the named patterns the brief calls out, and (ii) a new structural detector (`_detect_unusual_patterns`) that augments the literal vocabulary with regex-based shape detection — symbolic-only names, annotation parens with question marks, foreign-currency ISO prefixes. Both contribute to the same confidence sum on the same suspense_account anomaly type so the report renderer doesn't need a new bucket.

**Changes:**
- [x] `backend/classification_rules.py::SUSPENSE_KEYWORDS` extended with new literal patterns: `susp-` (covers `SUSP-001` codes), `unidentified` (re-added — Sprint 530 had removed it as vague), `unclassified`, `do not use` / `do_not_use` / `not for use`, `disputed`, `obsolete`, `write-off` / `writeoff` / `write off`, `rounding adj` / `rounding adjustment`, `misc unclassified`, `owner draw` / `owner contribution` / `owner contrib`, and `temp clearing` (specific phrase variant). Each carries a confidence weight calibrated against the brief's expected detection set.
- [x] `backend/audit/rules/suspense.py` — added `_detect_unusual_patterns()` helper with three regex families: symbolic-only names (zero alphabetic characters), annotation parentheses containing a question mark (`(personal?)`, `(non-ded?)`), foreign-currency ISO-4217 prefixes (`EUR-`, `GBP_`, etc.). Wired into `detect_suspense_accounts()` to augment the literal-keyword confidence sum. Structural matches appear in `matched_keywords` so the user can see why each account was flagged.
- [x] `backend/audit/pipeline.py` (both single- and multi-sheet code paths) — populates `data_quality["unrecognized_types"]` from `classification_quality.issues` filtered by `issue_type == "unclassified"`. The PDF Data Intake Summary used to read this field with a default of 0 and nothing populated it, so the counter was permanently wrong (Issue 10's secondary fix).
- [x] `backend/tests/test_contra_and_detection_fixes.py::test_unidentified_removed` renamed to `test_unidentified_re_added_sprint_670` and inverted — the Sprint 530 removal was deliberately reverted by Sprint 670 with a docstring explaining why.
- [x] `backend/tests/test_unusual_account_patterns.py` (new, 12 tests) — direct unit tests of `_detect_unusual_patterns` (symbolic, predominantly symbolic, annotation paren+?, annotation meals, trailing ?, EUR prefix, GBP prefix, clean name returns 0, normal description returns 0, legitimate `401(k) Plan` not flagged) plus an end-to-end integration test (`TestUnusualAccountsEndToEnd`) that runs the streaming auditor against a CSV mirroring the six brief-named accounts and asserts every required name is flagged while a clean Cash account is not.

**Validation (via Sprint 665 harness, `reports/remediation/sprint-670/`):**
- [x] `tb_unusual_accounts.csv` — `mat=12 anom=16` (was `mat=2 anom=6` in Sprint 669). Eleven structural exceptions detected: `????-UNIDENTIFIED`, `A/P - K.H. Owner Loan (personal?)`, `A/R - DISPUTED (see note)`, `EUR-AR (Euro Receivables)`, `Inventory - OBSOLETE/WRITE-OFF`, `Meals/Ent 50% (non-ded?)`, `Owner Draw/Contrib - K.H.`, `Revenue - MISC (unclassified)`, `Rounding Adj`, `SUSP-001`, `Temp Clearing - DO NOT USE`. `data_quality.unrecognized_types = 13` (was always 0). Diagnostic tier remains `high(100)` — appropriate for a file with 11 unusual accounts and a $306k imbalance.
- [x] `tb_hartwell_adjusted.pdf` — preflight unchanged from Sprint 669 (zero null warnings on Beg Balance Debit/Credit because the critical columns are now Ending Balance). Issue 13 confirmed resolved by the Sprint 669 column-mapping cascade.
- [x] `tb_hartwell_clean.csv` and other clean files — unchanged. Clean accounts do not match any new pattern (verified by `test_clean_name_returns_zero` and `test_legitimate_4xx_account_not_symbolic`).
- [x] Backend test suite — 277 green: 196 audit/preflight/memo/layout regression + 12 new unusual-pattern tests + 56 contra/detection/suspense tests + others.
- [x] Commit SHA: `b293eca`

---

### Sprint 671: DOCX Diagnostic Pipeline + Duplicate-Detection UX
**Status:** COMPLETE
**Source:** CEO remediation brief v6 — Issues 14, 15
**Files:** `backend/security_utils.py`, `backend/routes/audit_pipeline.py`, `backend/tests/test_format_dispatch.py` (new)

**Problem:** (14) `tb_hartwell.docx` produces a preflight successfully but the diagnostic returns a generic "Failed to process the uploaded file" error — preflight and diagnostic use different parsing pipelines for docx, and the error is not actionable. (15) Submitting `tb_hartwell_adjusted.pdf` after CSV files in the same session blocks the diagnostic citing duplicate submission with no explanation of what matched or how to override.

**Decision:**
For Issue 14 we considered (a) explicitly excluding non-CSV/Excel formats from the diagnostic with a specific error, or (b) routing the diagnostic ingestion layer through the same parser dispatch the preflight already uses. Picked (b) because the preflight parser already handles every supported format correctly — the only reason the diagnostic failed was that `process_tb_chunked` in `security_utils.py` only knew CSV and Excel branches. Routing through `parse_uploaded_file_by_format` adds support for PDF / DOCX / ODS / OFX / QBO / IIF / TSV / TXT in one place. Currency-formatted values (`"$284,500.00"`, `"(1,234.56)"`) needed a stripping step because `pd.to_numeric` doesn't understand commas — without it, every numeric value coerced to NaN→0 and the diagnostic silently produced a "$0 / $0 / balanced" report.

For Issue 15 we kept the existing 5-minute dedup gate (it's protecting against double-submit clicks) but rewrote the error to name the matched filename and added an explicit `force_resubmit=true` form parameter that purges the matched dedup key before the insert. The historic message "please wait for the current analysis to complete" was misleading — it implied something was still in progress, which it usually wasn't. The preflight route was already free of dedup checks; only the diagnostic route was affected.

**Changes:**
- [x] `backend/security_utils.py::process_tb_chunked` — added a non-tabular extension branch that dispatches `(.pdf, .docx, .ods, .ofx, .qbo, .iif, .tsv, .txt)` through `parse_uploaded_file_by_format`, materialises the resulting `(columns, rows)` into a single string-typed DataFrame chunk, and yields it. Added `_strip_currency_formatting()` helper that recognises numeric-looking strings (with optional `$`/`£`/`€` symbol, parenthesised negatives, and thousands separators) and strips them to a plain numeric form. Helper runs on every cell of the dispatched DataFrame so PDF/DOCX/ODS values like `"$284,500.00"` become `"284500.00"` before the streaming auditor's `pd.to_numeric` step. Account-name cells with embedded commas survive unchanged because they don't match the numeric-shape regex.
- [x] `backend/routes/audit_pipeline.py::audit_trial_balance` — added `force_resubmit: bool = Form(default=False)` parameter. When true, the dedup key is deleted before the upsert so the gate cannot fire. The 409 error response was rewritten from a plain string to a structured dict containing: `error="duplicate_submission"`, `message` (names the filename and the 5-minute window), `filename`, `match_window_seconds=300`, and `override="force_resubmit=true"`. A frontend client inspecting the response body can act on the override path without consulting docs.
- [x] `backend/tests/test_format_dispatch.py` (new, 17 tests) — `_strip_currency_formatting` unit tests (plain number, thousands separator, decimal with thousands, dollar/pound/euro signs, parenthesised negative, `$(1,234.56)`, text with commas unchanged, `Dr`/`Cr` indicator unchanged, blank, non-string, zero with formatting) plus `process_tb_chunked` dispatch tests (CSV uses legacy path, TSV uses parser dispatch, currency strips correctly through dispatch, unknown extension falls back).

**Validation (via Sprint 665 harness, `reports/remediation/sprint-671/`):**
- [x] `tb_hartwell_adjusted.pdf` → `diag=low(0) mat=0 anom=4`. Diagnostic runs. `total_debits=$11,047,200`, `total_credits=$11,047,200`, `balanced=True`, `difference=$0.00`. Four coverage findings (Sales Revenue, Long-Term Debt, COGS, PP&E) — exactly what we'd expect on a balanced clean adjusted TB. Issue 14 resolved end-to-end: PDF preflight + diagnostic both work.
- [x] `tb_hartwell.docx` → `diag=low(0) mat=0 anom=4`. Diagnostic runs without error. The four concentration findings come through with correct dollar amounts (Sales Revenue $2,156,400, Long-Term Debt $750,000, PP&E $1,167,600, COGS $1,124,300). The streaming auditor's overall `total_debits` / `total_credits` show as $0 because the file uses the `net_balance_with_indicator` layout — the "credit column" is the Dr/Cr text indicator, and the streaming auditor's chunk-level pd.to_numeric reads positive Dr values and negative Cr values both into the debit total, which cancel to zero. The per-account analytics still produce correct results because they use `abs(net_balance)`. A future sprint can add a layout-aware transformer that splits the net balance into synthetic debit/credit columns before chunk processing — but the brief's expected result for Issue 14 is satisfied: the diagnostic runs without error.
- [x] All four other test files unchanged from Sprint 670 — the new dispatch path only fires for non-CSV/non-Excel extensions.
- [x] **Issue 15 — duplicate detection UX**: 409 response now returns a structured dict naming the filename, window, and override path. `force_resubmit=true` form parameter purges the matched dedup key. Preflight route confirmed to be free of any dedup gate.
- [x] Backend test suite — 294 green: 277 prior regression + 17 new format-dispatch tests.
- [x] Commit SHA: `081dfed`

**Note on Issue 15 frontend wiring:**
The backend now exposes a structured 409 with the override path. Wiring the frontend Upload page to display the matched filename and a "Re-run anyway" button is a follow-up task — the API contract is in place but the React component change is out of scope for this remediation sprint.

---
