# Phase XLIX — Diagnostic Feature Expansion (Sprints 356–361)

**Focus:** High-value diagnostic gaps identified by AccountingExpertAuditor review
**Source:** 6-agent council consensus (2026-02-21) — features first
**Strategy:** Highest ROI first (JT-19), then engagement workflow, then TB extensions
**Version:** v2.0.0
**Tests:** 4,102 backend + 995 frontend

## Sprint 356: JE Holiday Posting Detection (JT-19)
> ISA 240.A40 — entries posted on public holidays as fraud risk indicator

- [x] Static holiday calendar module (`shared/holiday_calendar.py`) — 11 US federal holidays
- [x] JT-19 `test_holiday_postings()` in `je_testing_engine.py` — config-driven, severity-weighted
- [x] Registered in `run_test_battery()` after T13
- [x] Memo generator `TEST_DESCRIPTIONS` updated
- [x] 33 tests in `tests/test_je_holiday_postings.py`
- [x] Hardcoded 18→19 updates across 4 backend test files + 3 frontend files

## Sprint 357: Lease Account Diagnostic (IFRS 16 / ASC 842)
> TB diagnostic extension — lease account detection and consistency checking

- [x] `lease_diagnostic_engine.py` — keyword classification, 4 consistency tests
  - Directional consistency (ROU asset ↔ lease liability)
  - Classification check (current/non-current split)
  - Amortization trend (prior period comparison)
  - Expense presence (ROU without amortization)
- [x] 44 tests in `tests/test_lease_diagnostic.py`
- [x] Integrated into `audit_engine.py` → `result["lease_diagnostic"]`

## Sprint 358: Cutoff Risk Indicator (ISA 501)
> TB diagnostic extension — accrual/prepaid/deferred revenue cutoff risk

- [x] `cutoff_risk_engine.py` — 30 cutoff-sensitive keywords, 3 deterministic tests
  - Round number test (divisible by 1,000)
  - Zero balance test (material prior → zero current)
  - Spike test (>3x change from prior)
- [x] 39 tests in `tests/test_cutoff_risk.py`
- [x] Integrated into `audit_engine.py` → `result["cutoff_risk"]`

## Sprint 359: Engagement Completion Gate
> Workflow hardening — status transition enforcement

- [x] `COMPLETED` status added to `EngagementStatus`
- [x] `VALID_ENGAGEMENT_TRANSITIONS` map (active→{completed,archived}, completed→{archived}, archived=terminal)
- [x] `InvalidEngagementTransitionError` + `validate_engagement_transition()` helper
- [x] Completion gate: all active follow-up items must have disposition != NOT_REVIEWED
- [x] `completed_at`/`completed_by` metadata columns on Engagement
- [x] 409 status code for transition violations in API
- [x] EngagementResponse schema updated (status Literal includes "completed")
- [x] API contract test updated
- [x] 26 tests in `tests/test_engagement_completion.py`

## Sprint 360: Going Concern Indicator Profile (ISA 570)
> TB diagnostic extension — 6 ISA 570 indicators with mandatory disclaimer

- [x] `going_concern_engine.py` — 6 deterministic indicators
  - Net liability position (negative equity)
  - Current ratio below 1.0
  - Negative working capital
  - Recurring losses (consecutive-loss escalation with prior period)
  - Revenue decline >10% (prior period required)
  - High leverage (DTE > 3.0)
- [x] Mandatory non-dismissible ISA 570 disclaimer
- [x] Integrated into `audit_engine.py` via `category_totals_pre` → `result["going_concern"]`
- [x] 46 tests in `tests/test_going_concern.py`

## Sprint 361: Phase XLIX Wrap
- [x] Full backend regression: 4,102 passed, 0 failed
- [x] Frontend build: clean
- [x] Pre-existing allowlist bug fixed (approved_by/approved_at from Phase XLVIII)
- [x] CLAUDE.md updated
- [x] todo.md archived
- [x] Version bump: v1.9.5 → v2.0.0
