# Sprint 689 Decision Brief — Six Hidden Backend Tools

> **Purpose:** turn the CEO's Sprint 689 decision (promote / defer / remove for six orphaned backend tools) from "decide blind" into "approve or override six recommendations with evidence." Each tool has a backend implementation, tests, and a CSV export — none are discoverable on the frontend.
>
> **Scope:** `book_to_tax`, `cash_flow_projector`, `intercompany_elimination`, `form_1099`, `w2_reconciliation`, `sod`. Plus the Multi-Currency "Tool #12" marketing claim that the sprint flagged as separately-broken.
>
> **Date:** 2026-04-22 — prepared during the launch-readiness cleanup pass.

---

## Executive summary

| Tool | Recommendation | Effort | Rationale |
|---|---|---|---|
| `sod` | **Promote minimal** | ~1 sprint (UI only) | Already Enterprise tier-gated; clear audience fit (SOC 1 / internal-audit); the sprint brief itself flagged this as the default promote candidate. |
| `book_to_tax` | **Defer** | 0 sprints (no-op) | Tax-season tool, narrow window; CSV export already works for power users via API; promotion cost (UI + marketing) exceeds near-term value. |
| `cash_flow_projector` | **Defer** | 0 sprints | Short-horizon projection (30/60/90d) is SMB-oriented, not the auditor ICP. Keep live for API users. |
| `intercompany_elimination` | **Defer (review at Enterprise push)** | 0 sprints now | Strong Enterprise fit, but not differentiated vs. legacy tools (Caseware, CCH); revisit as part of Enterprise feature bundle. |
| `form_1099` | **Defer** | 0 sprints | Annual-seasonality, narrow use window; pair with `w2_reconciliation` if either is promoted later. |
| `w2_reconciliation` | **Defer** | 0 sprints | Payroll-audit niche; largest engine (946 lines) of the six, highest removal cost if reversed. |

| Marketing-claim item | Recommendation | Effort |
|---|---|---|
| "Tool #12" label | **Correct in CLAUDE.md + marketing copy** | 15 min | The label currently points at Statistical Sampling, not Multi-Currency. Fix the doc; no code changes. Multi-Currency remains a deliberate side-car on TB upload (not a standalone tool). |

**Net actions if CEO approves the defaults:**
- One mini-sprint to promote `sod` with Enterprise badge.
- One doc-drift fix for the "Tool #12" label.
- Five routes remain live but undiscoverable — effectively free (no ongoing maintenance, no UI surface to degrade).

---

## Per-tool detail

### 1. `sod` — Segregation of Duties checker

**Recommendation: PROMOTE (minimal UI, Enterprise tier).**

| Dimension | State |
|-----------|-------|
| Backend complete? | Yes — 452-line engine, 186-line route, 13 tests, 19+ AICPA/SOX 404 rule library. |
| Tier-gating? | **Already Enterprise-only** (route enforces `UserTier.ENTERPRISE`). |
| Frontend? | None. No page, no catalog entry, no marketing copy. |
| Added | Sprint 630 — stable since. |

**Why promote.** The sprint brief specifically named `sod` as the default promote candidate. Enterprise tier already has the seat infrastructure + priority-support framing that SoD fits into. SoD is a recognizable auditor primitive ("who can post a JE *and* approve it?") and shows up on SOC 1 scope conversations — having it surfaced gives the Enterprise pitch a concrete artifact.

**Why not wait.** Leaving it live-but-invisible means the Enterprise tier's landing page lists "all 12 tools" but the catalog only shows 12 of 13 live tools. A future audit will flag the inconsistency.

**Promote effort estimate.** One mini-sprint.
- `/tools/sod` page mirroring `/tools/composite-risk` shape (~300 lines).
- Rule-library reference card + analysis matrix rendering from the existing CSV export.
- Catalog entry + command palette registration.
- Enterprise badge.
- Jest tests for hook + page happy path.

### 2. `book_to_tax` — Book-to-Tax adjustment calculator

**Recommendation: DEFER.**

| Dimension | State |
|-----------|-------|
| Backend complete? | Yes — 511-line engine, 18 tests, M-1/M-3 schedule logic, deferred tax rollforward. |
| Tier-gating? | None — available to all paid tiers via route. |
| Frontend? | None. |
| Added | Sprint 635 — stable, no subsequent edits. |

**Why defer.** Book-to-tax is a tax-season tool (Jan–Apr usage window); Paciolus's pitch is audit-forensic, not tax-prep. Promotion cost (tool page + catalog + marketing mention + test coverage) doesn't match near-term ROI. Existing engine runs fine for API integrators if any exist.

**Risk of deferral.** None active. The `M-3 > $10M assets` threshold is pinned in the engine and will eventually need updating per IRS revision, but that's years out; the deferral doesn't create urgency.

**Alternative — remove.** Would save ~717 lines. If the CEO wants the codebase tighter, removal is safe (no cross-dependencies per the explore pass). But removal also costs a sprint of its own (tests, route cleanup, migration if any rows exist), so saving lines isn't free.

### 3. `cash_flow_projector` — 30/60/90-day cash projection

**Recommendation: DEFER.**

| Dimension | State |
|-----------|-------|
| Backend complete? | Yes — 525-line engine, 13 tests, scenario modeling (base / stress / best). |
| Tier-gating? | None. |
| Frontend? | None. |
| Added | Sprint 633 — stable. |

**Why defer.** Short-horizon cash projection (30/60/90-day) is an SMB CFO tool, not an audit-forensic tool. Auditors do cash-flow *analysis* (indirect method, ASC 230 classification) — and that's already in TB Diagnostics. A projector doesn't land in the ICP's value frame.

**Why not remove.** API surface is tiny; keeping it live-but-invisible costs nothing. A future "CFO advisory" product line could consume it without rebuilding.

### 4. `intercompany_elimination` — Multi-entity consolidation

**Recommendation: DEFER with a review trigger.**

| Dimension | State |
|-----------|-------|
| Backend complete? | Yes — 669-line engine, 13 tests, consolidation worksheet + elimination-JE matching + tolerance reconciliation. |
| Tier-gating? | None. |
| Frontend? | None. |
| Added | Sprint 637 — latest of the six (2026-04-17). |

**Why defer.** Intercompany elimination is a clear Enterprise fit (multi-entity implies firms auditing groups, not single LLCs) — but it's not a *signature* differentiation. Caseware, CCH, and every Big-4 tool have consolidation engines; promoting ours makes us look like a legacy-tool knock-off, not a new kind of instrument.

**Review trigger.** If/when Enterprise tier gets a first-class feature bundle (bulk upload, PDF branding, SOC-2 evidence pack), intercompany-elimination slots in there as table-stakes. Don't promote standalone.

### 5. `form_1099` — 1099 candidate identification

**Recommendation: DEFER.**

| Dimension | State |
|-----------|-------|
| Backend complete? | Yes — 463-line engine, 18 tests, 1099-NEC/MISC box mapping + reportable thresholds. |
| Tier-gating? | None. |
| Frontend? | None. |
| Added | Sprint 634 — stable. |

**Why defer.** 1099 prep is January-February, annual. Narrow audience (firms handling client AP); narrow window. Same CFO-advisory framing as `cash_flow_projector` — not the audit-forensic ICP.

**Packaging note.** If promoting `w2_reconciliation` later, consider bundling `form_1099` + `w2_reconciliation` into a "Tax Prep Lane" on the catalog — the two share the same January timing and the same tax-accountant audience.

### 6. `w2_reconciliation` — W-2/W-3 + Form 941 reconciliation

**Recommendation: DEFER.**

| Dimension | State |
|-----------|-------|
| Backend complete? | Yes — **946 lines (largest engine of the six)**, 19 tests, employee discrepancy + W-3 totals + Form 941 quarterly mismatch. |
| Tier-gating? | None. |
| Frontend? | None. |
| Added | Sprint 636 — stable. |

**Why defer.** Same logic as `form_1099` — narrow annual window (January), payroll-audit niche. Deep backend investment suggests this was written for a specific engagement; worth confirming whether the original requestor still has a use.

**Sunk-cost consideration.** At 946 lines + 349 test lines = 1,295 LOC, this is the most expensive tool to remove cleanly. Deferral is cheaper even if the tool never sees production use.

---

## Multi-Currency — "Tool #12" marketing claim

**Recommendation: CORRECT THE CLAIM (docs only).**

**Finding.** The Sprint 689 brief stated "Multi-Currency is marketed as Tool #12 but is only a side-car on TB upload — no standalone card." After investigation:

- **The "Tool #12" label actually points at Statistical Sampling**, not Multi-Currency. Statistical Sampling has a full tool page at `/tools/statistical-sampling`. The file comment confirms: `Tool 12`.
- **Multi-Currency is indeed a deliberate side-car** — `CurrencyRatePanel` is a collapsible side panel inside the TB upload flow, integrated into post-processing. No standalone `/tools/multi-currency` page exists, and none was planned.
- **The sprint brief's premise was partially wrong.** Multi-Currency isn't currently-marketed as a standalone tool; the confusion likely came from CLAUDE.md's "Multi-Currency (Tool 12, ISA 530)" line in Era 6 of COMPLETED_ERAS.md — which is historical and doesn't reflect current marketing.

**Net action.**
1. No product work. Multi-Currency stays a side-car.
2. Grep CLAUDE.md + marketing copy for any lingering "Tool 12 = Multi-Currency" language; the canonical count has always been 12 and Statistical Sampling is the 12th.
3. If any CEO-facing materials say "12 tools including Multi-Currency," that's the drift to fix; otherwise this is already correct.

---

## Default-approval path

If the CEO approves every recommendation above:

1. **Open Sprint 689.5 — Promote `sod` as Enterprise feature.** One sprint of UI work, tests, catalog entry.
2. **Doc drift hotfix** — audit CLAUDE.md for the "Tool #12" attribution, confirm Statistical Sampling is correctly credited. One commit.
3. **No-op on the other five** — routes remain live, undiscoverable; zero maintenance cost.

If the CEO wants **removal** instead of defer on any of the five:

- Each removal is ~3–5 hours of careful work (route deletion, engine deletion, test deletion, verification that no other engine imports from it).
- Net LOC savings per removal:
  - `book_to_tax`: 717 lines
  - `cash_flow_projector`: 692 lines
  - `intercompany_elimination`: 871 lines
  - `form_1099`: 654 lines
  - `w2_reconciliation`: **946 lines** (largest)
- Total if all five removed: ~3,880 lines.

If the CEO wants **promote** instead of defer on any of the five (beyond `sod`):

- Each promote is ~1 sprint (~200–300 lines of UI + tests).
- Good candidates for future: `intercompany_elimination` if/when the Enterprise bundle gets a sprint; `form_1099` + `w2_reconciliation` as a paired "Tax Prep Lane" if tax-firm marketing becomes a priority.

---

## Appendix — where each lives

| Tool | Route | Engine | Tests | Lines (route + engine) |
|------|-------|--------|-------|------------------------|
| `book_to_tax` | `backend/routes/book_to_tax.py` | `backend/book_to_tax_engine.py` | `backend/tests/test_book_to_tax_engine.py` | 717 |
| `cash_flow_projector` | `backend/routes/cash_flow_projector.py` | `backend/cash_flow_projector_engine.py` | `backend/tests/test_cash_flow_projector_engine.py` | 692 |
| `intercompany_elimination` | `backend/routes/intercompany_elimination.py` | `backend/intercompany_elimination_engine.py` | `backend/tests/test_intercompany_elimination_engine.py` | 871 |
| `form_1099` | `backend/routes/form_1099.py` | `backend/form_1099_engine.py` | `backend/tests/test_form_1099_engine.py` | 654 |
| `w2_reconciliation` | `backend/routes/w2_reconciliation.py` | `backend/w2_reconciliation_engine.py` | `backend/tests/test_w2_reconciliation_engine.py` | 946 |
| `sod` | `backend/routes/sod.py` | `backend/sod_engine.py` | `backend/tests/test_sod_engine.py` | 638 |

All six routes are registered in `backend/routes/__init__.py` and live at `/audit/*` endpoints. All six have CSV export capability; none have PDF or memo generators.
