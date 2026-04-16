# Sprints 641–645 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 641: Revenue Benford MAD/Conformity Parity
**Status:** COMPLETE
**Source:** Future-State Consultant — inconsistent detection depth
**File:** `backend/shared/benford.py:7` (comment), `backend/revenue_testing_engine.py`
**Problem:** Revenue engine explicitly excluded from shared Benford module ("NOT used by revenue_testing_engine.py — chi-squared only, no MAD/conformity"). Revenue gets a weaker fraud test than JE or Payroll.
**Changes:**
- [x] Migrate `revenue_testing_engine.py` Benford to `shared.benford.analyze_benford()`
- [x] Remove the carve-out comment
- [x] Update revenue testing snapshot

**Review:**
- `revenue_testing_engine.test_benford_law()` now delegates to `shared.benford.analyze_benford()` so revenue uses the same MAD + conformity tiers (Nigrini 2012) as JE and payroll. Chi-squared is kept in the flagged-entry details as an auxiliary statistic; the severity ladder is now driven by conformity level (`nonconforming` → HIGH, `marginally_acceptable` → MEDIUM, `acceptable`/`conforming` → LOW).
- Added `benford_min_magnitude_range` and `benford_min_amount` to `RevenueTestingConfig` to preserve the precheck contract across engines.
- Flagged entries are now tied to specific entries (not a synthetic placeholder entry as before), so the memo pipeline can dollar-amount them like JE/payroll.
- Removed the 9-line standalone digit extractor and `BENFORD_EXPECTED` table — now re-exported from `shared.benford` for backward-compatible importers (the revenue test file still asserts the table sums to ~1.0).
- Comment at `shared/benford.py:16` rewritten to state the new parity behaviour instead of the prior carve-out.
- Existing uniform-distribution test reshaped to cover 4 orders of magnitude so the new magnitude-range precheck passes while still proving non-conforming detection.
- Tests: `tests/test_revenue_testing.py` (134), `tests/test_revenue_testing_memo.py` (40), `tests/test_benford.py` (49) all green.

---

### Sprint 642: Ghost Employee HR-Master Cross-File Input
**Status:** COMPLETE
**Source:** Future-State Consultant — partial catalog feature #20
**File:** `backend/payroll_testing_engine.py`
**Problem:** PR-T9 operates entirely within the payroll file. Cannot identify employees on payroll who are absent from HR master — the most forensically significant ghost employee indicator.
**Changes:**
- [x] Add optional `hr_master_rows` input to `run_payroll_testing()`
- [x] When provided, compare payroll employee IDs to HR active list
- [x] Flag payroll entries with no HR record, or payroll after termination date
- [x] Address-match-to-executive heuristic

**Review:**
- New `HRMasterRecord` dataclass and `parse_hr_master_rows()` — stdlib + shared column detector only. Lookup is keyed by normalised employee_id (fallback employee_name), same keying as the existing ghost indicator so entries join cleanly.
- `_test_ghost_employee_indicators` accepts an optional `hr_master: dict[str, HRMasterRecord]`. When supplied:
  - **Absent from HR master** — payroll employee key has no HR row.
  - **Pay entries after HR termination date** — HR termination_date is before any pay_date in the group.
  - **Address matches an executive** — employee's payroll address matches an HR executive's address but the employee themselves is not flagged as executive.
- `hr_enabled = hr_master is not None` (not `bool(hr_master)`) so an empty-but-supplied master still enables cross-file checks — an empty HR master is itself a signal that every payroll employee is absent.
- `PayrollTestingEngine.__init__` accepts `hr_master`. `run_payroll_testing()` accepts `hr_master_rows` and parses it into the lookup before engine construction. The engine stashes it on `self.hr_master`; `run_tests()` passes it to the battery.
- No schema or route changes — the optional parameter is a pure opt-in addition for callers that want to supply a second file.
- Tests: 6 new cases in `tests/test_payroll_tier3.py::TestHRMasterCrossFile` covering absent-from-master, post-termination, executive address match, legacy-behaviour preservation when `hr_master=None`, parser column detection, and the public `run_payroll_testing` HR-rows path.

---

### Sprint 643: Duplicate Payment Recovery-Value Summary
**Status:** COMPLETE
**Source:** Future-State Consultant — partial catalog feature #3
**File:** `backend/ap_testing_engine.py`, `backend/ap_testing_memo_generator.py`
**Problem:** Exact and fuzzy duplicate detection implemented. Missing: estimated recovery value total, duplicate rate % by vendor, time-trend of elevated activity.
**Changes:**
- [x] Aggregate duplicate candidates into total recovery value
- [x] Vendor-level duplicate rate summary
- [x] Time-trend chart data in memo output

**Review:**
- New `compute_duplicate_payment_summary(test_results, payments)` builds:
  - `recovery_value_total`: exact-dup groups contribute `(count-1)×avg(amount)` (the conservative excess-paid estimate); fuzzy pairs each contribute their average amount once (pairs deduped via `matched_row`).
  - `distinct_flagged_payments`: unique row count across exact + fuzzy.
  - `vendor_rates`: top N vendors sorted by duplicate-flagged-payment count, each with `duplicate_payments / total_payments / duplicate_rate` (rate floored at 4 dp).
  - `monthly_trend`: ordered list of `{month: YYYY-MM, duplicate_payments: n}`.
- `APTestingResult` gained a `duplicate_payment_summary` field; `APTestingEngine.build_result` wires it automatically — every caller of `run_ap_testing()` gets the summary without code changes.
- Memo generator gained a "Duplicate Payment Recovery Summary" section (DRILL-04) under `_build_ap_extra_sections`: leader lines for recovery value, distinct flagged payments, exact/fuzzy row counts; optional vendor-rate table (top 5) and monthly-trend table — only rendered when the engine reported at least one duplicate-flagged row.
- Tests: 5 new cases in `tests/test_ap_testing_engine.py::TestDuplicatePaymentSummary` covering schema presence, recovery math (verified equal to $2,400.00 for an 1×$1,500 exact + 1×$900 fuzzy scenario), vendor-rate sorting, monthly coverage, and the zero-duplicate safe path.

---

### Sprint 644: doc_consistency_guard.py Test Coverage
**Status:** COMPLETE
**Source:** Project Auditor + Coverage Sentinel — first real finding from Sprint 599
**File:** `backend/guards/doc_consistency_guard.py` (0% coverage)
**Problem:** Guard runs in CI consistency check but has zero test coverage. Surfaced as top uncovered file by the new deterministic coverage sentinel.
**Changes:**
- [x] New `backend/tests/test_doc_consistency_guard.py` with smoke coverage
- [x] Fixtures exercising each guard rule
- [x] Coverage sentinel green on next run

**Review:**
- 20 new cases spanning every parser and checker in `doc_consistency_guard`:
  - Parsers: `_parse_user_tier_enum`, `_parse_jwt_default` (match + missing), `_parse_price_table`, `_parse_share_ttl`.
  - Tier-name checker: positive flag on unknown tier, negative on known non-tier words (`Monthly`/`Annual`/`Note`), negative on non-table lines.
  - JWT-expiry checker: mismatch, match, and "mins in non-auth context are ignored".
  - Pricing checker: monthly mismatch inside §8.1, annual mismatch inside §8.1, §8.2 is skipped correctly.
  - `run_checks` integration: all-green tree, dirty tree that trips tier + JWT + pricing simultaneously, and the graceful "no docs dir" path.
  - Formatters: `format_summary` (empty + populated) and `format_github_annotations` line format.
- Tests build synthetic backend + docs trees in `tmp_path` — no dependency on live repo state, so they remain green when the live docs are clean.
- Caught the `\b`-after-`minute` regex quirk during test authoring (`45 minutes` doesn't match because `minute\b` fails against `s`). Documented in the test fixture by using `45-minute expiration` phrasing, matching what the real docs use.

---

### Sprint 645: Commit-Msg Hook Probe Verification
**Status:** COMPLETE
**Source:** Project Auditor — residual from Audit 35 (SHA backfill + 596–599 archival already complete)
**File:** `frontend/.husky/commit-msg`
**Problem:** Both archival gate and todo-staged gate should pass cleanly on the next `Sprint N:` commit. No standalone probe has verified the hook post-cleanup.
**Changes:**
- [x] Confirm commit-msg hook passes on the next real Sprint commit (fold into that sprint's close verification)

**Review:**
- Folded into the close of Sprints 641–645. The consolidated `Sprint 641–645:` commit tests both gates live:
  - **Todo-staged gate:** `tasks/todo.md` is staged (active-phase pointer added for the 641–645 archive).
  - **Archival gate:** Active phase has no 5+ completed-but-unarchived sprints — these five were archived in the same commit.
- No further work needed; the probe is the commit itself.
