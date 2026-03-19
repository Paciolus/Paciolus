# Sprints 553–561 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-19.

---

### Sprint 561 — DEC 2026-03-19 Full Remediation
**Status:** COMPLETE
**Scope:** 13 findings fixed from Digital Excellence Council 2026-03-19 (18 total; 4 informational/positive)

**P1 — Compliance Boundary (F-001, F-002):**
- [x] **F-001:** Rename "Composite Risk Score" → "Composite Diagnostic Score" across all user-facing output (12 backend files, 8 frontend files). Function renamed to `compute_tb_diagnostic_score` / `get_diagnostic_tier` with backward-compatible aliases. "HIGH RISK" → "HIGH". "Risk Score Scale" → "Diagnostic Score Scale". "Risk Tier" → "Diagnostic Tier" in all PDF memos and CSV exports.
- [x] **F-002:** ISA 530 sampling conclusion language — "population is accepted" replaced with auditor-judgment-compliant phrasing across `sampling_engine.py` (MUS + random) and `sampling_memo_generator.py`. Both pass and fail conclusions now include ISA 530 paragraph 14 evaluation reminder.

**P1 — Testing (F-003):**
- [x] Deferred to dedicated test coverage sprint (per council recommendation). Route-level integration test gap documented. Backward-compatible aliases preserve all 6,706 existing tests.

**P2 — Billing Safety (F-005, F-006, F-007):**
- [x] **F-005:** Idempotency key added to Stripe checkout session creation: `checkout-{user_id}-{price_id}-{minute_bucket}`
- [x] **F-006:** Webhook error classification — `ValueError`/`KeyError` → 400 (Stripe stops retrying); operational errors → 500 (Stripe retries). Signature verification failures now logged at WARNING.
- [x] **F-007:** Atomic transactions — removed intermediate `db.commit()` calls in checkout flow; single atomic commit after checkout session creation succeeds. `db.rollback()` on failure.

**P2 — Schema Hardening (F-008):**
- [x] All 10 Pydantic response models changed from `extra="allow"` → `extra="ignore"` (unknown fields silently dropped). Docstrings updated.

**P2 — Background Jobs (F-009):**
- [x] APScheduler lock TTL increased from 300s → 600s. Added `jitter` (30-120s) to all 9 scheduled jobs to stagger execution across workers.

**P3 — Observability (F-011):**
- [x] All `print()` statements in `config.py` replaced with `_config_logger` structured logging (17 print calls → logger.critical/warning/info).

**P3 — Type Safety (F-012):**
- [x] `BrandIcon.tsx` `as any` replaced with `React.SVGAttributes<SVGElement>`.

**P3 — Methodology (memo_base.py disclaimer):**
- [x] Disclaimer language changed from "procedures per {isa_reference}" → "procedures with reference to {isa_reference}" to avoid implying full ISA framework implementation.

**Review:**
- 6,706 backend tests pass. 1,426 frontend tests pass. Frontend build succeeds.
- Zero remaining occurrences of "Composite Risk Score", "population is accepted", or "population cannot be accepted" in source code.
- Backward-compatible aliases (`compute_tb_risk_score`, `get_risk_tier`) preserve all existing callers/tests.
- Files: `shared/tb_diagnostic_constants.py`, `shared/memo_base.py`, `sampling_engine.py`, `sampling_memo_generator.py`, `billing/checkout_orchestrator.py`, `routes/billing_webhooks.py`, `cleanup_scheduler.py`, `config.py`, `shared/diagnostic_response_schemas.py`, `shared/testing_response_schemas.py`, `pdf/sections/diagnostic.py`, `bank_reconciliation_memo_generator.py`, `multi_period_memo_generator.py`, `three_way_match_memo_generator.py`, `engagement_dashboard_memo.py`, `routes/export_testing.py`, `shared/export_helpers.py`, `frontend: TestingScoreCard.tsx`, `BrandIcon.tsx`, `DemoTabExplorer.tsx`, `ProductPreview.tsx`, `ARScoreCard.tsx`, `FixedAssetScoreCard.tsx`, `InventoryScoreCard.tsx`, `RevenueScoreCard.tsx`

---

