# Sprints 516–526 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-10.
> Era: DEC Remediation + PDF Quality + Diagnostic Engine Calibration

---

## Sprint 516 — DEC 2026-03-08 Remediation

**Status:** COMPLETE
**Commit:** 20396fd
**Goal:** Fix 17 of 21 findings from Digital Excellence Council audit 2026-03-08.
**Context:** DEC audit identified 21 findings (8 P2, 12 P3, 1 info). 4 findings deferred to Sprints 517-518.

- [x] 17 findings remediated (methodology corrections, test fixes, content additions)
- [x] 4 findings deferred with explicit Sprint assignments (F-018 → Sprint 517, F-020 → Sprint 518)
- [x] `pytest` passes
- [x] `npm run build` passes
- [x] `npm test` passes

**Review:** Retroactive entry per Audit 29 (protocol bypass identified). All 17 fixes verified via full test suite. Remaining 4 findings have dedicated sprint plans in READY status.

---

## Sprint 519 — Structural Debt Remediation (Code Quality)

**Status:** COMPLETE (all 5 phases implemented)
**Commit:** 39fdc30 (Phases 1–4), 6f9ffd9 (Phase 5)
**Goal:** Reduce structural debt and consolidation drift across 5 phases without changing observable behavior.

### Phase 1 — Quick Wins
- [x] 1A: Frontend upload transport consolidation (`uploadTransport.ts`) — 4 files deduped
- [x] 1B: API client mutation cache invalidation dedup (`invalidateRelatedCaches`)
- [x] 1C: Backend billing endpoint boilerplate (`stripe_endpoint_guard`) — 5 endpoints
- [x] 1D: Backend audit route execution scaffold (`execute_file_tool`) — 4 endpoints

### Phase 2 — Hook Decomposition
- [x] Extract `useTrialBalanceUpload`, `useTrialBalancePreflight`, `useTrialBalanceExports`, `useTrialBalanceBenchmarks`
- [x] `useTrialBalanceAudit` reduced from 680→110 LOC (thin composite)

### Phase 3 — Backend Engine Unification
- [x] Create `engine_framework.py` with `AuditEngineBase` (10-step pipeline)
- [x] `JETestingEngine`, `APTestingEngine`, `PayrollTestingEngine` extend base

### Phase 4 — Settings Page Decomposition
- [x] Extract `MaterialitySection`, `ExportPreferencesSection`, `testingConfigFields`
- [x] Page reduced from 635→415 LOC

### Phase 5 — Route/Service Boundary (CEO override)
- [x] `billing/checkout_orchestrator.py`, `billing/usage_service.py`
- [x] `shared/materiality_resolver.py`, `shared/tb_post_processor.py`
- [x] `routes/billing.py` and `routes/audit.py` updated

---

## Sprint 520 — Billing Security & Correctness

**Status:** COMPLETE
**Commit:** 7391f56
**Goal:** Fix 4 billing audit findings spanning CRITICAL to MEDIUM severity.

- [x] **CRITICAL:** Cross-tenant data leakage in billing analytics — scoped all queries by user_id/org_id
- [x] **HIGH:** Seat mutation targets wrong Stripe line item — `_find_seat_addon_item()` using price ID match
- [x] **MEDIUM:** Webhook replay gap — `ProcessedWebhookEvent` dedup model
- [x] **MEDIUM:** Semantic event mismatch — added `TRIAL_ENDING` enum variant
- [x] 10 new tests, 6,223 total passing

---

## Sprint 521 — Directive Protocol Enforcement + Audit 29 Recovery

**Status:** COMPLETE
**Commit:** 83d2313
**Goal:** Make the Directive Protocol mechanically enforced.

- [x] `commit-msg` hook rejects `Sprint N:` commits without `tasks/todo.md` staged
- [x] Retroactive Sprint 516 and 520 entries added
- [x] Lessons captured in `lessons.md`

---

## Sprint 522 — PDF Report Quality: Institutional Grade

**Status:** COMPLETE
**Commit:** 158a0a1
**Goal:** 12 institutional-grade PDF improvements.

- [x] Fix 1–2: Accuracy (signed values, gross balance footnote)
- [x] Fix 3–4, 9: Intelligence (priority ranking, risk decomposition, differentiated procedures)
- [x] Fix 5–8: Presentation (TOC, engagement fields, interior design, status badge)
- [x] Fix 10–12: Disclosure (limitations, amount annotations, data intake summary)

---

## Sprint 523 — Cover Page Liability Framing

**Status:** COMPLETE
**Commit:** b59b89d
**Goal:** Remove implied co-preparer liability from cover page.

- [x] "Prepared By" → "Engagement Practitioner", "Reviewed By" → "Engagement Reviewer"
- [x] Practitioner liability boundary paragraph in Limitations section
- [x] 21 sample reports regenerated

---

## Sprint 524 — PDF Report Quality: Remaining Fixes (A/B/C)

**Status:** COMPLETE
**Commit:** 051e2f4
**Goal:** Complete three incomplete implementations from Sprint 522.

- [x] Fix A: Risk score decomposition — plain-language named factors
- [x] Fix B: Differentiated minor observation procedures (5 distinct procedure variants)
- [x] Fix C: Inline amount qualifier — per-transaction breakdown

---

## Sprint 525 — TB Diagnostics Page: Bug Fixes and Content Improvements

**Status:** COMPLETE
**Commit:** 914784b
**Goal:** 6 bug fixes and content improvements.

- [x] Fix 1: Button click hijacking (pointer-events)
- [x] Fix 2: Null/empty cell handling for one-sided TBs
- [x] Fix 3: Dynamic materiality slider range
- [x] Fix 4: Column detection fuzzy matching + full column display
- [x] Fix 5: Engagement metadata entry point (6 fields)
- [x] Fix 6: "Indistinct" → "below materiality threshold" terminology

---

## Sprint 526 — Diagnostic Engine Calibration and Critical Fixes

**Status:** COMPLETE
**Commit:** c256521
**Goal:** Classification pipeline fix, 8 new anomaly categories, risk scoring, PDF fixes.

- [x] Fix 1: Logo on cover page (Dockerfile path fix)
- [x] Fix 2: Account classification pipeline (type/name column detection + priority ordering)
- [x] Fix 3: Round-number detection tiered calibration (suppress/minor/material)
- [x] Fix 4: 8 missing anomaly detection categories (credit balance, debit balance, suspense, related party, intercompany, equity, revenue concentration, expense concentration)
- [x] Fix 5: Risk score reconciliation (pre-computed, capped, new anomaly types scored)
- [x] Fix 6: Differentiated procedure language (5 new anomaly types)
- [x] Fix 7: Engagement metadata em-dash fallbacks
