# Sprints 626–630 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 626: Depreciation Calculator (Book + MACRS)
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #6 (Quick Win, Priority 8/3)
**File:** `backend/depreciation_engine.py` (new), `backend/routes/depreciation.py` (new), `backend/routes/__init__.py`, `backend/tests/test_depreciation_engine.py` (new, 21 tests), `frontend/src/app/tools/depreciation/page.tsx` (new), `frontend/src/app/tools/page.tsx`
**Problem:** Existing `fixed_asset_testing_engine.py` reads `depreciation_method` to verify it — does NOT calculate schedules. No SL, DDB, SYD, or MACRS generator exists.
**Changes:**
- [x] New engine `backend/depreciation_engine.py` — SL, declining balance (with switch to SL), SYD, units of production, MACRS
- [x] MACRS tables hardcoded from IRS Pub 946 (Table A-1 HY 200%/150% DB for classes 3, 5, 7, 10, 15, 20; Table A-2/3/4/5 mid-quarter for 5-year)
- [x] Conventions: half-year, mid-quarter, mid-month (for real property)
- [x] Book vs tax comparison + per-year deferred tax change + cumulative DTL/DTA bridge
- [x] New route `/audit/depreciation` + CSV export `/audit/depreciation/export.csv`
- [x] Frontend page `/tools/depreciation` with form, summary cards, three tables
- [x] Catalog entry under Advanced
- [ ] PDF and XLSX export deferred to a follow-up sprint (matches loan-amortization deferral pattern)
**Review:** Decimal-precision math with HALF_UP cents quantization. Standard MACRS 5-year HY 200%DB returns the published [20.00, 32.00, 19.20, 11.52, 11.52, 5.76]% schedule on $10k = $2k/$3.2k/$1.92k/$1.152k/$1.152k/$576. Final-year clamp guarantees ending book value matches salvage exactly under all book methods. Book/tax timing differences net to zero at maturity (verified). 21/21 engine tests pass; backend loads 218 routes (was 216); `npm run build` succeeds with `/tools/depreciation` listed. Commit `98b6d87`.

---

### Sprint 627: Account-Level Risk Signal Heatmap
**Status:** COMPLETE
**Source:** Accounting Auditor — highest-audit-workflow-value capability gap
**File:** `backend/account_risk_heatmap_engine.py` (new), `backend/routes/account_risk_heatmap.py` (new), `backend/routes/__init__.py`, `backend/tests/test_account_risk_heatmap_engine.py` (new, 13 tests)
**Problem:** Composite risk scoring operates at engagement level. No output collects all signals (anomaly flags, classification issues, cutoff risk, lease indicator, accrual gaps) against a single account row for triage density scanning. Auditor opens five separate views instead of one.
**Changes:**
- [x] New `backend/account_risk_heatmap_engine.py` aggregating outputs via adapter functions for `audit_engine`, `classification_validator`, `cutoff_risk_engine`, `accrual_completeness_engine`, `composite_risk_engine`
- [x] Per-account: signal count, materiality-weighted signal score (sev × log10(materiality+10) × confidence), source list, severity counts, priority tier (Top 10% High, next 20% Moderate, rest Low)
- [x] JSON + CSV export endpoints (`/audit/account-risk-heatmap` + `/export.csv`)
- [x] In-memory aggregation only (zero-storage)
- [ ] Diagnostic Canvas frontend integration deferred to a follow-up sprint
**Review:** Pure aggregation design — adapters translate concrete engine outputs into a generic `RiskSignal` interface, so the engine is testable independently of upstream changes. Composite risk adapter excludes `low` combined-risk assessments to avoid noise. Top 10%/next 20% bucketing uses ceiling on small lists so even a 3-account input gets at least one High. 13/13 engine tests pass; backend loads 220 routes (was 218). Commit `1ebf81b`.

---

### Sprint 628: Benford Second-Digit + First-Two-Digit Extension
**Status:** COMPLETE
**Source:** Accounting Auditor + Future-State — spec deviation in shared Benford module
**File:** `backend/shared/benford.py` (extended), `backend/tests/test_benford.py` (21 new tests)
**Problem:** Only first-digit analysis implemented. Second-digit catches round-number manipulation invisible to first-digit tests. Standard complementary test, trivial extension.
**Changes:**
- [x] Add `digit_position: Literal["first", "second", "first_two"] = "first"` parameter to `analyze_benford()`
- [x] Add expected distributions for second-digit (10 buckets, 0–9) and first-two-digit (90 buckets, 10–99); both verified to integrate to 1.0
- [x] Position-specific Nigrini MAD thresholds (first: 0.006/0.012/0.015; second: 0.008/0.010/0.012; F2D: 0.0012/0.0018/0.0022)
- [x] Tests for second-digit detection of rounding patterns (forced 2nd-digit-5 dataset triggers nonconforming and most_deviated_digits includes 5)
- [x] `digit_position` round-trips into the result dict for downstream consumers
- [ ] JE/Payroll panel integration deferred — engines continue to call `analyze_benford(... digit_position="first")` (default); panels can add second/first_two side-by-side in a follow-up
**Review:** Backwards-compatible — existing callers don't change. New `get_second_digit()` and `get_first_two_digits()` extractors handle decimals, negatives, and zero correctly. F2D needs ≥1000 samples per Nigrini guidance; engine doesn't refuse small samples but the caller's `min_entries` controls the gate. 49/49 Benford tests pass (28 existing + 21 new); JE + Payroll engine tests still pass. Commit `01ea813`.

---

### Sprint 629: ASC 842 Lease Calculator
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #17 (Strategic Bet, Priority 8/6)
**File:** `backend/lease_accounting_engine.py` (new), `backend/routes/lease_accounting.py` (new), `backend/routes/__init__.py`, `backend/tests/test_lease_accounting_engine.py` (new, 24 tests)
**Problem:** Lease diagnostic flags audit risk only — no ROU asset, no PV of lease payments, no classification tests, no amortization schedule, no disclosure support. ASC 842 is mandatory for non-micro entities.
**Changes:**
- [x] New `backend/lease_accounting_engine.py` — 5-criteria classification test (ASC 842-10-25-2 (a)–(e)), initial measurement (PV of payments → liability; liability + IDC + prepaid – incentives → ROU), liability amortization (effective interest), ROU amortization
- [x] Operating vs finance lease separation: operating uses straight-line lease cost (ROU plugs SL minus interest); finance uses straight-line ROU amortization with separate interest
- [x] Disclosure tables: 5-year + thereafter maturity analysis, weighted-average remaining term, weighted-average discount rate
- [x] Defer modification/remeasurement to future sprint (documented in module docstring)
- [x] Route `/audit/lease-accounting` + CSV export
- [x] Annual escalation (CPI/fixed step-up) supported
- [ ] PDF memo + Excel export deferred to a follow-up sprint (matches loan-amortization deferral)
- [ ] Frontend page deferred to a follow-up sprint
**Review:** Decimal-precision math; in-advance amortization correctly skips post-final-period interest accrual. Liability schedule reconciles: sum(principal) ≈ initial liability (within $0.01 across quantized rows); sum(payments) - sum(principal) = total interest. Operating lease produces uniform period_lease_cost; finance lease produces interest-front-loaded period_lease_cost. 24/24 engine tests pass; backend loads 222 routes (was 220). Commit `ef3429f`.

---

### Sprint 630: Segregation of Duties Checker
**Status:** COMPLETE
**Source:** Future-State Consultant — missing catalog feature #19 (Enterprise differentiator)
**File:** `backend/sod_engine.py` (new), `backend/routes/sod.py` (new), `backend/routes/__init__.py`, `backend/tests/test_sod_engine.py` (new, 13 tests)
**Problem:** JE-T9 flags single-user high-volume as an SoD indicator but there is no user-role matrix analysis tool. Required for every SOC 1 / internal audit engagement.
**Changes:**
- [x] New `backend/sod_engine.py` ingesting user-role matrix + role-permission matrix; case- and whitespace-insensitive permission matching
- [x] Hardcoded SoD rule library: 11 rules covering AP (vendor+invoice, invoice+payment, payment+bank rec), JE (create+post, post+close), Payroll (master+payment, rate+payment), Revenue (customer+credit memo, invoice+cash receipt), Inventory (custody+adjustment), and System Admin (admin+transactional)
- [x] Per-user risk ranking (high*3 + med*2 + low*1) with high/moderate/low tier mapping; conflict matrix with triggering permissions and roles
- [x] Mitigating control suggestions per rule (compensating-control framework per COSO 2013)
- [x] `extra_rules` parameter for engagement-specific rule additions
- [x] Routes: `/audit/sod/rules` (rule library), `/audit/sod/analyze` (JSON), `/audit/sod/analyze.csv` (CSV export)
- [x] Enterprise-tier gated via `require_enterprise_tier` dependency (returns 403 with `tier_locked` error code on non-Enterprise tiers)
- [ ] PDF export deferred to a follow-up sprint (matches loan-amortization deferral)
- [ ] Frontend page deferred to a follow-up sprint
**Review:** Engine separates the rule library from the matching logic — `extra_rules` lets engagements add custom rules without changing the library. Mitigation text and rationale included on every conflict for auditor copy-paste into workpapers. ADM-01 correctly distinguishes a pure-admin user (no transactional access → no conflict) from an admin with transactional access (conflict). 13/13 engine tests pass; backend loads 225 routes (was 222). Commit pending.

---
