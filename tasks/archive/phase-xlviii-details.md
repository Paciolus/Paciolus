# Phase XLVIII — Adjustment Approval Gating (Sprints 354–355)

> **Focus:** Enforce proposed→approved→posted transition gating, approval metadata, official/simulation mode
> **Source:** Workflow integrity — prevent unapproved proposed entries from contaminating official adjusted TB output

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 354 | Engine + Route + Schema Changes | 5/10 | COMPLETE |
| 355 | Tests + Frontend + Commit | 4/10 | COMPLETE |

## Sprint 354 Checklist
- [x] Add `VALID_TRANSITIONS` dict to `adjusting_entries.py`
- [x] Add `InvalidTransitionError(ValueError)` exception
- [x] Add `validate_status_transition()` function
- [x] Add `approved_by`/`approved_at` fields to `AdjustingEntry`
- [x] Update `AdjustingEntry.to_dict()` with approval fields
- [x] Update `AdjustingEntry.from_dict()` with approval fields (backward-compatible)
- [x] Change `apply_adjustments()` signature: `include_proposed` → `mode`
- [x] Update `apply_adjustments()` logic for official/simulation modes
- [x] Add `is_simulation` to `AdjustedTrialBalance`
- [x] Update `AdjustedTrialBalance.to_dict()` with `is_simulation`
- [x] Update route: transition validation in `update_adjustment_status()`
- [x] Update route: approval metadata on status change
- [x] Update route: `ApplyAdjustmentsRequest` → `mode` field
- [x] Update route: pass `mode` to `apply_adjustments()`
- [x] Add `approved_by`/`approved_at` to `AdjustmentStatusUpdateResponse`
- [x] Update `AdjustingEntryResponse` in response schemas
- [x] Update `AdjustedTrialBalanceResponse` in response schemas

## Sprint 355 Checklist
- [x] Write `TestStatusTransitions` (10 tests)
- [x] Write `TestApprovalMetadata` (4 tests)
- [x] Write `TestApplyMode` (6 tests)
- [x] Update existing `test_apply_with_proposed` to use `mode="simulation"`
- [x] Update frontend `AdjustingEntry` type (approved_by/approved_at)
- [x] Update frontend `ApplyAdjustmentsRequest` (include_proposed → mode)
- [x] Update frontend `AdjustedTrialBalance` (is_simulation)
- [x] Update `AdjustmentSection.tsx` (include_proposed → mode)
- [x] `pytest tests/test_adjusting_entries.py -v` — 67 passed
- [x] `npm run build` — zero errors

## Transition Rules

```
VALID_TRANSITIONS = {
    PROPOSED  → {APPROVED, REJECTED}
    APPROVED  → {POSTED, REJECTED}
    REJECTED  → {PROPOSED}           # re-proposal allowed
    POSTED    → {}                   # terminal, no exits
}
```

| Transition | Metadata Side Effect |
|---|---|
| `proposed → approved` | Sets `approved_by`, `approved_at` |
| `proposed → rejected` | Sets `reviewed_by` |
| `approved → posted` | Requires `approved_by` and `approved_at` already set |
| `approved → rejected` | Clears `approved_by`, `approved_at` |
| `rejected → proposed` | Resets for fresh review cycle |

## Apply Mode

| Mode | Entries Included | Response Tag |
|---|---|---|
| `"official"` (default) | `approved` + `posted` only | `is_simulation: false` |
| `"simulation"` | `approved` + `posted` + `proposed` | `is_simulation: true` |

## Files Changed
- `backend/adjusting_entries.py` — VALID_TRANSITIONS, InvalidTransitionError, validate_status_transition, approved_by/approved_at, mode, is_simulation
- `backend/routes/adjustments.py` — transition validation, approval metadata logic, mode in apply endpoint
- `backend/shared/diagnostic_response_schemas.py` — approved_by/approved_at + is_simulation
- `backend/tests/test_adjusting_entries.py` — 20 new tests (10 transitions + 4 metadata + 6 mode)
- `frontend/src/types/adjustment.ts` — approved_by/approved_at, mode, is_simulation
- `frontend/src/components/adjustments/AdjustmentSection.tsx` — include_proposed → mode
