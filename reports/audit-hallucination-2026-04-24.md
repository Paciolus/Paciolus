# Hallucination Audit — 2026-04-24

> Sweep target: codebase, marketing copy, docs, memo templates, MEMORY.md, hotfix SHAs.
> Methodology: Read protocol at `.claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md`,
> then verify priority area claims against actual code. All file:line citations
> reference the snapshot at HEAD `acfa06c6` on branch `sprint-716-complete-status`.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 4 |
| Medium   | 10 |
| Low      | 5 |
| **Total** | **19** |

Two themes dominate: (1) the homepage / pricing / terms pages have a partial
"12 → 18 tools" rebrand from Sprint 689 Path B that landed marketing prose flips
on some surfaces but **not** the underlying data (ToolLedger renders 12 tools
behind copy that says "Eighteen"), and (2) `frontend/src/app/tools/page.tsx`
holds stale hard-coded test counts that drift below the actual engine numbers
by 1–3 tests per tool.

---

## Critical Findings (user trust / accounting citations / legal copy)

### C-1. ToolLedger renders 12 tools behind "Eighteen Tools" header
**Source:** `frontend/src/components/marketing/ToolLedger.tsx:69` plus
`frontend/src/content/tool-ledger.ts:155` (`CANONICAL_TOOL_COUNT = 12`)
**Claim:** Homepage section heading reads "Eighteen Tools · One Platform" and
component docstring says "all 18 tools visible at once" (line 8).
**Truth:** `TOOL_LEDGER` array contains 12 entries; the runtime assertion at
`tool-ledger.ts:157-161` enforces `length === 12`; the `ROMAN` map in
`ToolLedger.tsx:37-40` only goes up to XII. Customers landing on the homepage
read "Eighteen tools" but see 12 rows.
**Severity:** Critical — direct contradiction visible to every visitor.

### C-2. Pricing page advertises "All 18 diagnostic tools" on every paid tier
**Source:** `frontend/src/app/(marketing)/pricing/page.tsx:381, 402, 482, 608`;
`frontend/src/app/(marketing)/pricing/layout.tsx:5,8`;
`frontend/src/app/(marketing)/terms/page.tsx:616,621,626`.
**Claim:** Solo / Professional / Enterprise feature lists each say "All 18
diagnostic tools"; Terms of Service tier table repeats "All 18 tools" three
times.
**Truth:** Only 12 tools render in the canonical catalog (`TOOL_LEDGER`,
`CANONICAL_TOOL_COUNT = 12` in both `frontend/src/content/tool-ledger.ts` and
implicitly via the comment `# CANONICAL TOOL COUNT: 18` in
`backend/shared/entitlements.py:14` — note the backend source-of-truth comment
disagrees with the frontend canonical count). 23 tool route pages exist under
`frontend/src/app/tools/` but only 12 are surfaced as "in the catalog."
**Severity:** Critical — contractually-relevant copy in Terms of Service (legal
surface) overstates entitlements.

### C-3. tools/page.tsx test counts are stale across 6 tools
**Source:** `frontend/src/app/tools/page.tsx:47-52`
**Claim vs. truth (verified by counting `def _test_…` / `def test_…` in the engine files):**
- Line 47: AP `testCount: 13` → actual **14** (`backend/ap_testing_engine.py`)
- Line 48: Revenue `testCount: 16` → actual **18** (`backend/revenue_testing_engine.py`)
- Line 49: AR `testCount: 11` → actual **12** (`backend/ar_aging_engine.py`)
- Line 50: Payroll `testCount: 11` → actual **13** (`backend/payroll_testing_engine.py`)
- Line 51: Fixed Assets `testCount: 9` → actual **11** (`backend/fixed_asset_testing_engine.py`)
- Line 52: Inventory `testCount: 9` → actual **10** (`backend/inventory_testing_engine.py`)
**Severity:** Critical — every authenticated user lands on `/tools` and reads
test counts that understate platform depth by ~13 tests cumulatively.

### C-4. CLAUDE.md cites "PCAOB AS 1215" but no memo references it
**Source:** `CLAUDE.md` Key Capabilities → "PCAOB AS 1215/2401/2501"
**Truth:** `Grep "AS 1215"` across `backend/` returns **zero matches**. AS 2401
(fraud) and AS 2501 (estimates) are cited in the JE and AR memos respectively.
AS 1215 (Audit Documentation) is plausible but never actually cited in any
generated memo.
**Severity:** Critical — accounting-citation hallucination in the operator
manual feeds downstream marketing/sales claims that the engine doesn't back.

---

## Medium Findings (marketing drift)

### M-1. ProofStrip / EvidenceBand / BottomProof claim "140+ automated tests across all 18 diagnostic tools"
**Source:** `frontend/src/components/marketing/ProofStrip.tsx:43`,
`EvidenceBand.tsx:30-33`, `BottomProof.tsx:30-35`.
**Truth:** Sum of test-batteries in code: JE 19 + AP 14 + Revenue 18 + AR 12 +
Payroll 13 + Fixed Asset 11 + Inventory 10 = **97**. "140+" is overstated by
~45%. (Plausible if individual sub-checks are counted, but the engines define
97 numbered tests.)
**Severity:** Medium — marketing puffery, contradicted by the catalog itself.

### M-2. BottomProof has internal contradiction — "12" + "all 18" in adjacent metrics
**Source:** `frontend/src/components/marketing/BottomProof.tsx:32-49,69`
**Claim:** Metric tile target value `12` labelled "Audit Tools", but
neighboring tile says "Across all 18 diagnostic tools", and section paragraph
on line 69 says "Twelve audit-focused tools."
**Severity:** Medium — visible contradiction in the closing-proof section.

### M-3. ToolSlideshow / ToolShowcase mix "12" and "18"
**Source:** `frontend/src/components/marketing/ToolSlideshow.tsx:418,511,514,581`;
`frontend/src/components/marketing/ToolShowcase.tsx:30,139,156,284,328`.
**Claim:** Components carry both "Eighteen Tools. One Platform." heading and
copy reading "Twelve purpose-built tools" within ~3 lines of each other.
**Severity:** Medium — same dual-rebrand drift pattern as C-1/C-2.

### M-4. Demo / dashboard pages call out "12+ tools" while pricing says "18"
**Source:** `frontend/src/app/(marketing)/demo/layout.tsx:5,8`;
`frontend/src/app/dashboard/page.tsx:11`; `frontend/src/app/tools/page.tsx:6`.
**Truth:** Pricing/Terms say 18; demo metadata + dashboard comment say "12+ tools";
TOOLS array at `tools/page.tsx:39-67` enumerates 24 tools.
**Severity:** Medium — three different counts surfacing on three different pages.

### M-5. Workspace shows "/18 tools" denominator
**Source:** `frontend/src/app/(workspace)/portfolio/[clientId]/workspace/[engagementId]/page.tsx:188`
**Claim:** `{toolRuns.length}/18 tools` denominator implies 18 tools per engagement.
**Truth:** `engagement_model.py:74` `ToolName` enum has only **13** entries
(12 + flux_analysis); workspace numerator is bounded by the enum, so progress
bar will never exceed 13/18.
**Severity:** Medium — a customer running every tool will see "13/18" forever.

### M-6. CLAUDE.md "17 core ratios" claim
**Source:** `CLAUDE.md` Key Capabilities → "17 core ratios"
**Truth:** `RatioEngine.calculate_all_ratios()`
(`backend/ratio_engine.py:1450-1483`) returns **18** keyed ratios:
current_ratio, quick_ratio, debt_to_equity, gross_margin, net_profit_margin,
operating_margin, interest_coverage, return_on_assets, return_on_equity, dso,
dpo, dio, ccc, equity_ratio, long_term_debt_ratio, asset_turnover,
inventory_turnover, receivables_turnover.
**Severity:** Medium — internal-doc undercount; contradicts itself.

### M-7. CLAUDE.md "Revenue Testing (18 tests — 14 core … 4 contract-aware)"
**Source:** `CLAUDE.md` Key Capabilities
**Truth:** `revenue_testing_engine.py` `def test_…` count is **18**, but the
breakdown is 14 core + 4 contract-aware (`test_contract_validity`,
`test_recognition_before_satisfaction`, `test_missing_obligation_linkage`,
`test_modification_treatment_mismatch`) — call it 14 core + 4 + an extra
allocation_inconsistency that lives in a different bucket. Total of 18 holds;
sub-categorization is fuzzy. Verified, count is correct.
**Severity:** Low — leaving as-is; partial-claim verifiable.

### M-8. CLAUDE.md "AP Testing (14 tests incl. AP-T14 Invoice-Without-PO per ACFE 2024)"
**Source:** `CLAUDE.md` Key Capabilities
**Truth:** Verified at `backend/ap_testing_engine.py:1700`
(`def test_invoice_without_po`). Count of 14 confirmed. **Citation OK.**
**Severity:** N/A (verified).

### M-9. MEMORY.md describes archive_sprints.sh fix as "pending pre-requisite" for Sprint 689a
**Source:** `memory/MEMORY.md` "Sprint 689 Path B locked 2026-04-23" entry —
"Pre-requisite: fix `scripts/archive_sprints.sh` or manually archive sprints
673–677 at start of 689a session."
**Truth:** `tasks/todo.md` Hotfix entry dated 2026-04-23 records that the fix
landed and Sprints 673–677 were archived to
`tasks/archive/sprints-673-677-details.md` (142 lines). PR #100 then merged
689a–g. MEMORY.md is two days stale.
**Severity:** Medium — operator memory drift; misleading for a fresh session.

### M-10. CLAUDE.md "Tests: 6,188 + 1,345" vs MEMORY.md "7,363 + 1,751" vs current ~6,965
**Source:** `CLAUDE.md` Sprint 499–515 era line; `memory/MEMORY.md` line 4.
**Truth:** Actual `^\s*def test_` count in `backend/tests/` = **6,965** as of
HEAD. CLAUDE.md last-updated era footer is stale; MEMORY.md likely overcounts
by ~5% (probably from a `pytest --collect-only` count which includes
parametrize expansions).
**Severity:** Medium — internal-doc inconsistency; affects Sprint review claims.

---

## Low Findings (internal-doc drift)

### L-1. CLAUDE.md "8 industry ratios"
**Source:** `CLAUDE.md` Key Capabilities
**Truth:** `industry_ratios.py` has 9 `def calculate_…` methods (excluding
`calculate_all`): inventory_turnover x2 (Mfg+Retail), days_inventory_outstanding,
asset_turnover x2 (Mfg+Generic), gmroi, revenue_per_employee,
utilization_rate, revenue_per_billable_hour. "8" is a defensible deduplicated
count but actual surface area is 9 distinct methods.
**Severity:** Low.

### L-2. CLAUDE.md "21+ router files"
**Source:** `CLAUDE.md` Architecture section
**Truth:** `backend/routes/*.py` = **58 files**. "21+" was correct ages ago.
**Severity:** Low — undercount understates architectural scope.

### L-3. CLAUDE.md "~49 export endpoints across 7 route modules"
**Source:** `CLAUDE.md` Key Capabilities
**Truth:** Likely correct order of magnitude. Verified `export_memos.py` has
18 routes, `export_testing.py` has 9 CSV routes — count of 49 across all is
plausible but unverified.
**Severity:** Low — flagged for next deep audit.

### L-4. CLAUDE.md SoD page "Twelve standards-backed SoD rules"
**Source:** `frontend/src/app/tools/sod/page.tsx:93`
**Truth:** Not verified against `sod_engine.py` rule library this pass — but
worth a follow-up; SoD-rule counts are exactly the kind of marketing-prose
hallucination this audit targets.
**Severity:** Low — flagged as TODO.

### L-5. tasks/todo.md hotfix `d74db7c` SHA
**Source:** `tasks/todo.md:23`
**Claim:** "[2026-04-23] d74db7c: record Sprint 673 COMPLETE — DB_TLS_OVERRIDE
removed from Render prod"
**Truth:** `git rev-parse d74db7c` resolves to
`d74db7c14331a89dfe5ed959fe2d11277c192a8c` — exists. Verified.
**Severity:** N/A (verified).

---

## Verified-Clean Spot Checks (no drift found)

- JE Testing claim of **19 tests** → `je_testing_engine.py` has 19 `def test_…` symbols
- AR Aging claim of **12 tests** → `ar_aging_engine.py` has 12 underscore-prefixed test methods
- Fixed Assets claim of **11 tests** → `fixed_asset_testing_engine.py` 11 methods
- Inventory claim of **10 tests** → `inventory_testing_engine.py` 10 methods
- Sampling memo claim of "ISA 530 + PCAOB AS 2315" → cited literally on `sampling_memo_generator.py:573`
- Multi-period memo claim of "ISA 520 + PCAOB AS 2305" → cited at line 1403
- AR memo claim of "ISA 540 + PCAOB AS 2501" → cited at lines 5, 56, 84, 215
- 18 memo PDF endpoints → confirmed in `backend/routes/export_memos.py` (18 `route_path=`)
- 9 testing-tool CSV exports → confirmed in `backend/routes/export_testing.py`
- 6 benchmark industries → confirmed in `benchmark_engine.py:1107-1112`
- LOKI_URL `logs-prod-042.grafana.net` → confirmed in `backend/config.py:464` and runbook
- R2 endpoint URL → confirmed in MEMORY.md vs `export_share_storage.py`
- Hotfix SHAs `6802bd63`, `9820bb2f`, `9f000703`, `8fd93bb5`, `7915d779`,
  `22e16dc6`, `a32f5669`, `73aaa519`, `39791eca`, `29f768ed`, `e04e63e2`,
  `8b3f76d0`, `8372073a`, `5fc04534`, `52ddfe03`, `7fa8a211`, `fb8a1fa8`,
  `e3d6c885`, `d74db7c1`, `b0ddbf69` → all resolve in `git log --all`

---

## Recommended Remediation Priority

1. **Critical → fix in next hotfix sprint:**
   - Update `frontend/src/content/tool-ledger.ts` to 18 entries (the actual
     promoted catalog from Sprint 689 Path B), or revert all "Eighteen Tools"
     copy back to "Twelve" until catalog data lands. The half-done state is
     worse than either consistent state.
   - Bump test counts in `frontend/src/app/tools/page.tsx:47-52` to the
     verified engine values.
   - Either remove `PCAOB AS 1215` from `CLAUDE.md` Key Capabilities or add it
     as a citation in the audit-engine memo template.
2. **Medium → fold into next marketing-copy sweep:**
   - Reconcile "140+ automated tests" claim — either count granular sub-checks
     and document the methodology, or update prose to "97 + analytical procedures".
   - Update MEMORY.md Sprint 689 entry to reflect that pre-requisite cleared.
   - Reconcile Tests count across CLAUDE.md / MEMORY.md / nightly artifacts.
3. **Low → defer to next audit:**
   - SoD rule count
   - Export-endpoint total count
   - Router-file count in CLAUDE.md

---

*Audit run by Claude (Opus 4.7, 1M context) on 2026-04-24.
Protocol: `.claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md`.
Branch: `sprint-716-complete-status`. HEAD: `acfa06c6`.*
