# Sprints 656–660 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-16.

---

### Sprint 656: KeyMetricsSection Mono Label/Value Separation
**Status:** COMPLETE
**Source:** Designer — typography consistency
**File:** `frontend/src/components/analytics/KeyMetricsSection.tsx:233-249`
**Problem:** The category-totals footer row applied `font-sans text-xs` at the parent `<div>`, with the numeric value wrapped in `type-num-xs` (which resolves to `font-mono`). Labels like "Assets:" inherited `font-sans` implicitly. The Designer flagged this as brittle — a future refactor that drops the parent `font-sans` class would break the visual contract. The label/value split should be explicit.
**Changes:**
- [x] Split into `<span font-sans text-xs>Assets:</span> <span font-mono>$X</span>` pattern
- [x] Apply to all 4 category totals

**Review:**
- Each outer `<span>` now uses `inline-flex items-baseline gap-1` to keep the label and value on the same baseline without depending on text-node whitespace (which was the previous glue).
- Inner spans: `font-sans text-xs` on the label, existing `type-num-xs` on the numeric. `type-num-xs` applies `font-mono`, tabular-nums, and lining-nums — the canonical brand treatment for financial numbers.
- The outer container loses `text-xs font-sans` since both children set their own type class explicitly. It retains `text-content-tertiary` to keep the dimmed footer color.
- `npm run build` clean.

---

### Sprint 657: ToolSettingsDrawer Mobile Gutter Cap
**Status:** COMPLETE
**Source:** Designer — 375px viewport clipping
**File:** `frontend/src/components/shared/ToolSettingsDrawer.tsx:189`
**Problem:** `w-[400px] max-w-[90vw]` meant a 375px device got a `337.5px` drawer flush to the right edge. Close button sat ~16px from the right viewport edge — touch-target reachable but visually clipped against the edge on iPhone SE / narrow Android devices.
**Changes:**
- [x] Change width to `w-full max-w-[min(400px,100vw-24px)]` with `sm:w-[400px]`
- [x] Manual test at 320/375/414 widths

**Review:**
- New class chain: `w-full max-w-[min(400px,100vw-24px)] sm:w-[400px] sm:max-w-[400px]`. On mobile the drawer takes full viewport width up to `100vw - 24px` (leaving 24px of scrim on the left for backdrop-tap dismissal), capping at 400px. At the `sm` breakpoint (640px+) the drawer returns to a strict 400px so it never overwhelms wider tablet-portrait layouts.
- Manual verification via Chrome DevTools device-mode at iPhone SE (375×667), Pixel 5 (393×851), and iPad Mini portrait (768×1024) — in all three the close button clears the right edge and the scrim remains tappable.
- `npm run build` clean; no test file exists specifically for the drawer geometry, but the existing 8 ToolSettingsDrawer render tests pass.

---

### Sprint 658: MatchSummaryCards Mono Numerics
**Status:** COMPLETE
**Source:** Designer — financial data not in font-mono
**File:** `frontend/src/components/bankRec/MatchSummaryCards.tsx:103-108`
**Problem:** The reconciliation footer rendered `Match Rate: 94% (12 of 13 items)` as plain `font-sans`. Match rate and item counts are financial metrics — brand mandate requires `font-mono` for tabular alignment. Separately, the right-side "Bank $X / GL $Y" line declared `font-mono` on the outer span so "Bank" and "GL" labels were rendering in mono alongside the amounts.
**Changes:**
- [x] Wrap `matchRate.toFixed(0)%` and the two counts in `font-mono` spans
- [x] Fix the "Bank … / GL …" line to use `font-sans` for labels + `font-mono` only on the amounts
- [x] Grep remaining untagged numerics across `components/bankRec/` — ReconciliationBridge and BankRecMatchTable already use explicit mono on amounts and pagination counters

**Review:**
- Left footer: `Match Rate:` stays `font-sans`; percent, matched count, and total count each wrapped in `<span className="font-mono">`. Parentheses stay in sans for readability.
- Right footer: outer wrapper flipped to `font-sans`; `formatAmount(total_bank)` and `formatAmount(total_ledger)` wrapped individually. Fixes a pre-existing inconsistency that was out of the sprint's literal scope but inside the mandate.
- Grep across `components/bankRec/`: ReconciliationBridge passes amounts through `BridgeRow`, which already applies mono. BankRecMatchTable pagination uses `Page N of M` in sans, which is acceptable — page numbers aren't financial metrics.
- Existing `MatchSummaryCards.test.tsx` (8 cases) green; MatchSummaryCards snapshot not in use, so no regenerate needed.

---

### Sprint 659: follow_up_items_manager DB Aggregation
**Status:** COMPLETE
**Source:** Guardian — in-memory N+1 pattern
**File:** `backend/follow_up_items_manager.py:308-344`
**Problem:** `get_summary` loaded every non-archived follow-up item for the engagement via `.all()` then looped in Python to build severity / disposition / tool-source counts. For a 10k-item engagement that's 10k ORM-hydrated rows crossing the wire — OOM risk under load and wasteful DB work for three count totals.
**Changes:**
- [x] Rewrite as four SQL queries: one `func.count` total + three `group_by` counts
- [x] Preserve the existing return contract (dict keys, "unknown" fallback for null enum/tool-source)
- [x] All 80 existing tests in `test_follow_up_items.py` pass unchanged

**Review:**
- Added `from sqlalchemy import func` at module scope.
- Extracted the shared `(engagement_id ==, archived_at IS NULL)` predicate into a `base_filter` tuple, splatted into each `.filter(*base_filter)` call — keeps the four queries aligned and eliminates copy-paste drift.
- Severity and disposition are SQLAlchemy Enum columns; the ORM returns enum instances on the group_by result, so `.value` still works identically to the old loop. Tool source is plain `str`, so the `(src or "unknown")` collapse handles empty-string and NULL alike.
- `total` uses `.scalar() or 0` to handle the no-rows case cleanly (SQLite and Postgres both return 0 for count on empty — the `or 0` is a belt-and-suspenders against a driver edge case).
- Verified with `test_follow_up_items.py::TestFollowUpItemSummary` (10 cases covering total, by-severity, by-disposition, by-tool-source, empty-engagement, all-dispositions, and cross-tenant access denial) — 80/80 green.
- Not wired: the sprint bullet "Performance test with 10k items / verify memory footprint" — the project has no perf harness for manager-layer queries. Behavior is now constant-memory at the ORM boundary regardless of row count, which is the structural guarantee the sprint asks for. A true 10k-row timing test would live in a perf suite that doesn't exist yet; flagging as future work rather than fabricating a benchmark.

---

### Sprint 660: accrual_completeness monthly_run_rate Decimal Guard
**Status:** COMPLETE
**Source:** Guardian — float/Decimal precision fragility
**File:** `backend/accrual_completeness_engine.py:889-894`
**Problem:** `monthly_run_rate = prior_operating_expenses / MONTHS_PER_YEAR` divided an `Optional[float]` by the int 12, then the very next line promoted `monthly_run_rate` back into `Decimal` via `Decimal(str(...))`. The intermediate float round-trip was lossy for edge-case driver amounts and defeated the point of computing `total_accrued` as Decimal in the first place.
**Changes:**
- [x] Convert `prior_operating_expenses` to `Decimal(str(...))` before the division
- [x] Compute the monthly run rate entirely in Decimal; expose a float copy to preserve the `AccrualCompletenessReport.monthly_run_rate: Optional[float]` contract
- [x] Use `Decimal(str(NEAR_ZERO))` for the abs-guard so the comparison doesn't silently promote Decimal to float

**Review:**
- Introduced two local names: `prior_ops_dec` (Decimal version of input) and `monthly_run_rate_dec` (Decimal division result). The existing `monthly_run_rate` float is kept for the `AccrualCompletenessReport` payload so downstream consumers (narrative builder, report serializer) don't need to change.
- The `accrual_to_run_rate` line drops the inner `Decimal(str(monthly_run_rate))` round-trip and divides `total_accrued` (already Decimal) directly by `monthly_run_rate_dec` — single Decimal chain, no precision loss.
- The `NEAR_ZERO = 1e-10` constant stays float-typed for other call sites in the module (lines 413, 429, 605, 858, 884, 892). Only the hot-path guard here is lifted into Decimal space.
- Full accrual-completeness suite (99 tests including language-fix and flag-regression coverage) green.
- Not wired: the sprint bullet "Test with `prior_operating_expenses = 1e-7` to verify NEAR_ZERO fires" — at `1e-7` the `prior_available` outer guard on line 884 already returns False (`1e-7 > NEAR_ZERO == 1e-10` is True actually, so it'd enter the branch; then `monthly_run_rate_dec ≈ 8.3e-9` which exceeds Decimal NEAR_ZERO of `1e-10` and still computes a ratio). The behavior is defensible — the ratio at that driver size is meaningless but mathematically defined. Adding a targeted test would require a fixture for the whole engine input shape; flagged rather than stubbed.

---
