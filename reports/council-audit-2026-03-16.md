# Paciolus Digital Excellence Council Report
Date: 2026-03-16
Commit/Branch: c394549 / main
Files Changed Since Last Audit: 43 files (Sprints 533–537 + hotfixes)

## 1) Executive Summary
- Total Findings: 14
  - P0 (Stop-Ship): 0
  - P1 (High): 0
  - P2 (Medium): 2
  - P3 (Low): 7
  - Informational: 5
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Informational Tier Calibration**: F-001 (cascade ordering lets 10%-TB escalation override informational intent), F-002 (uncapped informational risk score inflates clean TBs)
  - **Keyword Scope Ambiguity**: F-003 (bare "cash" keyword matches cash clearing/suspense accounts), F-007 (bare "loan" in suppress list swallows related-party loans)
  - **Frontend Filter Parity**: F-004 (severity dropdowns missing 'informational' option in 2 data tables)
  - **Contra-Equity Sign Convention**: F-005 (multi-period credit-normal sign flip applies to debit-normal contra-equity accounts)
  - **ISA 265 Language Proximity**: F-006 ("potential adjusting entry" language in escalated procedures approaches assurance boundary)
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — No new persistence pathways. All financial data ephemeral.
  - Auth/CSRF Integrity: **PASS** — JWT (HS256, bcrypt rounds=12), refresh token rotation, stateless HMAC CSRF, `credentials: 'include'` consistent.
  - Observability Data Leakage: **PASS** — Zero `console.log` in frontend production code. Sentry sanitization intact. DEPLOY-VERIFY-535/536/537 active.
  - CI Coverage Gates: **PASS** — `--cov-fail-under=80` active for both SQLite AND PostgreSQL (Sprint 533 parity fix). Jest 35% global.
  - Framer-motion `as const` Compliance: **PASS** — 34/34 variant declarations compliant.
  - Oat & Obsidian Theme: **PASS** — Zero generic Tailwind color violations.
  - Accounting Methodology: **2 P2 findings** — tier cascade ordering (F-001) and risk score calibration (F-002) require attention.
  - Security Posture: **PASS** — Zero SQL injection vectors, zero hardcoded secrets, zero bare `except:`, all 11 CI gates active.
- Prior DEC Remediation Rate: **3/3 actionable findings fixed (100%)** — Sprint 533 resolved all findings from DEC 2026-03-15.

## 2) Daily Checklist Status

1. **Zero-storage enforcement (backend/frontend/logs/telemetry/exports):** PASS — No new data persistence. Financial calculation engines process data in-memory without persistence. All 199 backend test files use real SQLite in-memory with transactional rollback.

2. **Upload pipeline threat model (size limits, bombs, MIME, memory):** PASS — No upload pipeline changes. Archive bomb detection active (entry count ≤ 10K, compression ratio ≤ 100:1, XML bomb scan). 110MB global body limit enforced.

3. **Auth + refresh + CSRF lifecycle coupling:** PASS — Password changes revoke all tokens. Refresh token rotation with reuse detection. Disposable email blocking. Account enumeration prevention.

4. **Observability data leakage (Sentry/logs/metrics):** PASS — Zero `console.log` in production frontend. DEPLOY-VERIFY log lines active for Sprints 535–537. All sanitization filters intact.

5. **OpenAPI/TS type generation + contract drift:** PASS — Snapshot-based drift detection CI job active (309 schemas, 159 paths). No schema changes in Sprints 533–537.

6. **CI security gates (Bandit/pip-audit/npm audit/policy):** PASS — 11 gates active: trufflehog, bandit, pip-audit, npm audit, ruff, eslint, mypy, accounting policy, report standards, pytest (80%), jest (35%). All gates confirmed post-Sprint 537.

7. **APScheduler safety under multi-worker:** PASS — No scheduler changes. ExportShare cleanup scheduler active.

8. **Next.js CSP nonce + dynamic rendering:** PASS — `proxy.ts` generates per-request nonce. `await headers()` forces dynamic rendering. `style-src 'unsafe-inline'` retained (React style props limitation). All `useSearchParams()` pages wrapped in `<Suspense>` (5 verified).

## 3) Findings Table (Core)

### F-001: Tier Cascade Ordering — Informational Check Fires After 10%-TB Escalation
- **Severity**: P2
- **Category**: Accounting Methodology / Classification Logic
- **Evidence**:
  - `backend/classification_rules.py` lines 653–661
  - Step 5e (line 654): `if tb_total > 0 and balance > 0.10 * tb_total: return "material"` — fires BEFORE informational check
  - Step 5f (line 660): `if any(kw in lower for kw in ROUND_NUMBER_TIER2_INFORMATIONAL): return "informational"` — fires AFTER
  - Sprint 537 QA passed because test data had cash/AR/AP balances below 10% of TB total
  - For entities with concentrated cash positions (tech companies, banks, holding companies), cash can easily exceed 10% of TB total
- **Impact**: A Cash account exceeding 10% of TB total will be escalated to "material" instead of the intended "informational" tier, producing a false positive that Sprint 537 was specifically designed to prevent. The QA regression data did not exercise this edge case.
- **Recommendation**: Move the Informational keyword scan (Step 5f, line 660) BEFORE the >10%-of-TB check (Step 5e, line 654). An account explicitly listed in `ROUND_NUMBER_TIER2_INFORMATIONAL` should not be escalated to material by the general-purpose 10% rule.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2]
  Goal: Reorder classify_round_number_tier() so informational check precedes 10%-TB escalation
  File: backend/classification_rules.py lines 653-661
  Approach: Move lines 657-661 (Step 5f informational check) before lines 653-655 (Step 5e)
  Acceptance criteria:
  - Cash account at 15% of TB total → returns "informational" (not "material")
  - Non-informational account at 15% of TB total → still returns "material"
  - All existing QA assertions still pass
  - New test: cash account at >10% TB total returns "informational"
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-002: Uncapped Informational Risk Score — Can Inflate Clean TBs to "Elevated"
- **Severity**: P2
- **Category**: Accounting Methodology / Risk Calibration
- **Evidence**:
  - `backend/shared/tb_diagnostic_constants.py` lines 410–414
  - `informational_pts = informational_count * 1` — no cap on accumulation
  - `get_risk_tier()` (line 478): "elevated" starts at score 26
  - A 50-account TB where 15 accounts are cash/AR/AP with round balances: 15 informational points + 10 coverage penalty = 25 (just below elevated). Add 1 minor observation = 27 = "elevated"
  - For a bank/distributor with 30+ transactional accounts: 30 informational + 10 coverage = 40 = "elevated" from informational alone
- **Impact**: TB diagnostic risk scores will be systematically inflated for entities with many transactional accounts (banks, distributors, high-transaction service firms). A TB where all rounding signals are informational (by design) should not produce an "elevated" risk tier.
- **Recommendation**: Cap informational contributions at 5 points regardless of count: `informational_pts = min(informational_count * 1, 5)`. Informational findings are definitionally low-signal; their aggregate should not push scores into "elevated."
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2]
  Goal: Cap informational risk score contribution at 5 points
  File: backend/shared/tb_diagnostic_constants.py line 411
  Approach: Replace `informational_pts = informational_count * 1` with
            `informational_pts = min(informational_count, 5)`
  Acceptance criteria:
  - TB with 20 informational findings scores max 5 informational points
  - TB with 3 informational findings scores 3 points (below cap)
  - Factor line shows "N informational notes (capped at 5)" when cap applies
  - Risk tier unchanged for TBs with <5 informational findings
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Data Governance & Zero-Storage Warden (G)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-003: Bare "cash" Keyword in TIER2_INFORMATIONAL Matches Too Broadly
- **Severity**: P3
- **Category**: Accounting Methodology / Keyword Scope
- **Evidence**:
  - `backend/classification_rules.py` line 503: `"cash"` as bare substring in `ROUND_NUMBER_TIER2_INFORMATIONAL`
  - Matches: "Cash and Cash Equivalents" (intended), but also "Petty Cash Clearing" (suspense concern), "Cash — Intercompany" (related-party concern), "Restricted Cash" (covenant concern)
  - `SUSPENSE_KEYWORDS` (line 325) includes `"cash clearing"` at 0.85 weight — direct conflict
  - An account named "Cash Clearing" produces an "informational" rounding finding AND a suspense flag simultaneously. The informational finding may cause users to dismiss the more significant suspense concern.
- **Impact**: Low — both findings appear in the merged anomaly list. However, the informational tier's "no procedure required" guidance conflicts with the suspense finding's "investigate further" guidance for the same account.
- **Recommendation**: Replace bare `"cash"` with more specific entries: `"cash and cash equivalents"`, `"operating cash"`, `"petty cash"` (if intended). Add "cash clearing" and "cash — intercompany" exclusion or rely on the existing carve-out mechanism.
- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 8/9 Approve P3 | Dissent: Performance Alchemist (B): "Informational — rare edge case"

---

### F-004: Missing 'informational' Option in Severity Filter Dropdowns
- **Severity**: P3
- **Category**: Frontend / UX Completeness
- **Evidence**:
  - `frontend/src/components/shared/testing/FlaggedEntriesTable.tsx` lines 220–228 — severity filter `<select>` shows High, Medium, Low only
  - `frontend/src/components/engagement/FollowUpItemsTable.tsx` lines 189–192 — severity filter `<select>` shows High, Medium, Low only
  - Backend produces 'informational' severity findings (Sprint 537)
  - Frontend `Severity` type in `types/shared.ts` correctly includes `'informational'`
  - All `Record<Severity, ...>` color/border/label mappings include informational
  - Items render correctly but users cannot filter to isolate them
- **Impact**: Users cannot filter to view informational-tier items in data tables despite the system displaying them. The RiskDashboard has a dedicated "Notes" section with proper filtering; the gap is in the testing/engagement table views.
- **Recommendation**: Add `<option value="informational">Informational</option>` to both severity filter dropdowns.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P3]
  Goal: Add informational option to severity filter dropdowns
  Files: frontend/src/components/shared/testing/FlaggedEntriesTable.tsx (~line 228)
         frontend/src/components/engagement/FollowUpItemsTable.tsx (~line 192)
  Approach: Add <option value="informational">Informational</option> after the Low option
  Acceptance criteria:
  - Filter dropdown shows 4 options: High, Medium, Low, Informational
  - Selecting Informational filters to show only informational items
  - npm run build passes
  - npm test passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-005: Credit-Normal Sign Flip Applied to Contra-Equity Accounts
- **Severity**: P3
- **Category**: Accounting Methodology / Multi-Period Display
- **Evidence**:
  - `backend/multi_period_comparison.py` lines 113–118: `_CREDIT_NORMAL_CATEGORIES` includes `"Equity"`
  - Treasury stock and accumulated deficit are classified under `lead_sheet_category = "Equity"` but carry debit-normal balances (contra-equity)
  - The sign flip at lines 126–128 inverts `change_amount` and `change_percent` for all Equity accounts, including contra-equity
  - A treasury stock increase (debit increase → equity decreases) would display as a positive change, which is directionally backward
- **Impact**: Low — treasury stock accounts in multi-period comparison reports may display sign-inverted changes. The raw `change_amount` and `change_percent` fields are correct; only `display_*` fields are affected.
- **Recommendation**: Add contra-equity detection using `is_contra_account()` from `classification_rules.py` and exclude contra-equity accounts from the credit-normal sign flip. Alternatively, add "Equity — Contra" as a separate lead_sheet_category.
- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 7/9 Approve P3 | Dissent: Performance Alchemist (B), Systems Architect (A): "Informational — contra-equity in multi-period is extremely rare in practice"

---

### F-006: "Potential Adjusting Entry" Language Approaches ISA 265 Boundary
- **Severity**: P3
- **Category**: Accounting Methodology / Assurance Language
- **Evidence**:
  - `backend/shared/tb_diagnostic_constants.py` line 104: `"consider whether the balance represents a potential adjusting entry"`
  - Line 248: `"escalate to engagement partner for assessment of potential adjusting entry"`
  - Line 126: `"determine whether a reclassification to liabilities is required"`
  - `MEMORY.md` guardrail: "NEVER auto-classify deficiencies"
  - The current wording uses conditional language ("consider whether") but "potential adjusting entry" implies the system is diagnosing what correction is needed
- **Impact**: Language risk, not functional error. A user interpreting "potential adjusting entry" as the system recommending a correction would cross the ISA 265 assurance boundary.
- **Recommendation**: Replace "potential adjusting entry" with "items requiring auditor follow-up" or "balance warranting further investigation." Preserves procedural intent without approaching assurance language.
- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 7/9 Approve P3 | Dissent: Verification Marshal (I), Systems Architect (A): "Informational — language is sufficiently conditional"
- **Chair Rationale**: P3 sustained. ISA 265 boundary compliance is a documented project standard. Even conditional language that includes "adjusting entry" as a diagnostic output creates regulatory positioning risk.

---

### F-007: "loan" Bare Keyword in TIER1_SUPPRESS Swallows Related-Party Loans
- **Severity**: P3
- **Category**: Accounting Methodology / Keyword Scope
- **Evidence**:
  - `backend/classification_rules.py` line 448: `"loan"` in `ROUND_NUMBER_TIER1_SUPPRESS`
  - `ROUND_NUMBER_TIER1_CARVEOUTS` (lines 489–498): Contains `"note payable — shareholder"`, `"note payable - officer"`, etc. but NO loan variants
  - `RELATED_PARTY_KEYWORDS` (lines 692–704): Contains `"shareholder loan"`, `"officer loan"`, `"employee loan"` — confirming these ARE in scope for scrutiny
  - "Shareholder Loan Payable — $500,000" matches "loan" → suppressed entirely, with no carve-out
  - The related-party detection module would flag this account, but rounding detection would suppress it — inconsistent signals
- **Impact**: Related-party loan accounts with exactly round balances will have their rounding anomaly suppressed. Round balances on related-party loans are specifically concerning (ISA 550 / ASC 850) because they suggest estimated rather than arm's-length pricing.
- **Recommendation**: Add `"shareholder loan"`, `"officer loan"`, `"employee loan"`, `"director loan"`, `"related party loan"` to `ROUND_NUMBER_TIER1_CARVEOUTS` to prevent suppression. These terms already exist in `RELATED_PARTY_KEYWORDS`, confirming they should receive scrutiny.
- **Primary Agent**: AccountingExpertAuditor
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-008: QA Automation (`run_qa_sweep.py`) Not in CI Pipeline
- **Severity**: P3
- **Category**: Testing / Regression Coverage
- **Evidence**:
  - `tests/qa/run_qa_sweep.py` — 778 lines of comprehensive QA regression testing across all tools
  - 5 QA CSV datasets in `tests/qa/`
  - Sprint 537 verification used QA sweep manually with excellent results (Cascade + Meridian datasets)
  - Not referenced in `.github/workflows/ci.yml`
  - Manual execution only — regressions in tool output would not be caught by CI
- **Impact**: Low — the QA sweep is effective but labor-intensive. Tool output regressions (false positive/negative classification, ratio calculation errors) could slip through CI.
- **Recommendation**: Add optional CI job to run `run_qa_sweep.py` as advisory-only (not blocking). Run weekly or post-deployment. This leverages Sprint 535's investment in QA data without adding CI fragility.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 8/9 Approve P3 | Dissent: Performance Alchemist (B): "Informational — QA sweep is manual by design"

---

### F-009: Benford's Law MAD Digit Filter Off-by-One at Boundary
- **Severity**: P3
- **Category**: Accounting Methodology / Precision
- **Evidence**:
  - `backend/shared/benford.py` line 189: `abs(deviation[d]) > mad` — strict inequality
  - A digit with deviation exactly equal to MAD would not appear in `most_deviated_digits`
  - Nigrini (2012) MAD thresholds use strict inequality for conformity classification but inclusive for digit flagging
- **Impact**: Negligible — the off-by-one would suppress one digit in an extreme edge case where deviation equals MAD exactly. No practical impact on audit conclusions.
- **Recommendation**: Change to `abs(deviation[d]) >= mad` to include boundary cases. One-character change.
- **Primary Agent**: AccountingExpertAuditor
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-010: Prior DEC Findings — 100% Remediation Rate
- **Severity**: Informational
- **Category**: Process / Verification
- **Evidence**:

  | Prior Finding (DEC 2026-03-15) | Status |
  |----------------------------------|--------|
  | F-001: PostgreSQL CI coverage missing `--cov-fail-under=80` | **FIXED** — Sprint 533 (commit a8df61a) added enforcement to both jobs |
  | F-002: Lint baseline stale (2026-02-22) | **FIXED** — Sprint 533 updated to 2026-03-15 |
  | F-003: Icon-only buttons missing `aria-label` | **FIXED** — Sprint 533 added `aria-label` to 7 elements across 5 files |

  **Remediation Rate**: 3/3 actionable findings fixed (100%).
  **DEC Remediation Trajectory**: 76% → 86% → 100% → 100% → 100% (five consecutive DEC cycles tracked).

- **Primary Agent**: Verification Marshal (I)

---

### F-011: Security Posture — Clean Bill of Health
- **Severity**: Informational
- **Category**: Security / Positive
- **Evidence**:
  - Zero SQL injection vectors: all queries use SQLAlchemy ORM parameterized queries
  - Zero `eval()`, `exec()`, `pickle.loads()`, unsafe deserialization
  - Zero bare `except:` clauses — all exceptions specific
  - Zero `TODO`/`FIXME`/`HACK` markers in production code
  - Zero hardcoded secrets — multi-backend secrets manager
  - JWT: 32+ char key validation, bcrypt rounds=12, refresh token hashing (SHA-256)
  - CSRF: stateless HMAC for POST/PUT/DELETE/PATCH
  - Rate limiting: user-aware tiered policies (5 tiers)
  - Archive bomb + XML entity expansion + formula injection all mitigated
  - Request ID injection prevention active; body size 110MB limit
  - All 199 test files use real SQLite in-memory (zero database mocking)
- **Primary Agent**: Security & Privacy Lead (D)

---

### F-012: Frontend Code Quality — 100% Compliance
- **Severity**: Informational
- **Category**: Code Quality / Positive
- **Evidence**:
  - **Framer-motion**: 34/34 variant declarations compliant (32 `as const` + 2 `satisfies Transition`)
  - **TypeScript**: Zero `any` annotations, zero `@ts-ignore`/`@ts-expect-error` in production code
  - **Theme**: Zero generic Tailwind color violations across all component files
  - **Severity type**: `'informational'` added to all 7 `Record<Severity, ...>` mappings (colors, borders, labels, sort order)
  - **console.log**: Zero instances in production frontend code
  - **Next.js 16**: `proxy.ts` correct, `useSearchParams()` Suspense wrappers verified (5/5)
  - **Tests**: 112 test files, 1,339 test cases, 35% coverage threshold
- **Primary Agent**: DX & Accessibility Lead (C), Type & Contract Purist (H)

---

### F-013: NEAR_ZERO Duplicates BALANCE_TOLERANCE from shared/monetary.py
- **Severity**: Informational
- **Category**: Code Hygiene / Consistency
- **Evidence**:
  - `backend/multi_period_comparison.py` line 39: `NEAR_ZERO = 0.005` defined locally
  - `backend/shared/monetary.py`: canonical `BALANCE_TOLERANCE` used consistently in `audit_engine.py`
  - Two near-zero constants exist independently — future changes to `BALANCE_TOLERANCE` won't propagate
- **Impact**: None at current values. Maintenance risk if tolerance is tightened.
- **Recommendation**: Consider importing `BALANCE_TOLERANCE` to replace `NEAR_ZERO`, or document why a different constant is appropriate.
- **Primary Agent**: Modernity & Consistency Curator (E)

---

### F-014: PytestCollectionWarning on TestTier Enum
- **Severity**: Informational
- **Category**: Testing / Hygiene
- **Evidence**:
  - `backend/shared/testing_enums.py` line 26: `class TestTier(str, Enum)`
  - Pytest warns: "cannot collect test class 'TestTier' because it has a __init__ constructor"
  - Sprint 532 added `__test__ = False` to `TestingMemoConfig` but not to `TestTier`
- **Impact**: CI output includes harmless warning. No functional impact.
- **Recommendation**: Add `__test__ = False` class attribute to `TestTier` enum.
- **Primary Agent**: Modernity & Consistency Curator (E)

## 4) Council Tensions & Resolution

### Tension 1: Informational Tier Ordering — Keyword Priority vs. Balance Significance
- **AccountingExpertAuditor** wants keyword priority: "Sprint 537's design intent is that Cash/AR/AP are always informational. The 10% rule should not override an explicit keyword assignment."
- **Verification Marshal (I)** agrees: "The QA data passed because balances were below 10%. A bank's TB where cash is 40% would produce a material false positive."
- **Systems Architect (A)** raises concern: "If we move informational before the 10% check, a $5M cash balance on a $10M TB gets 'informational' treatment. Should there be a secondary materiality gate?"
- **Resolution**: Keyword priority wins (8/9 vote). The informational tier is an explicit classification decision — if Cash is explicitly listed as informational, the 10% general-purpose rule should not override it. For extreme concentrations, the materiality cascade in the engagement layer provides the secondary gate. The informational tier note will surface the balance for awareness without generating a "material finding" procedure burden.

### Tension 2: Risk Score Cap — Where to Set It
- **AccountingExpertAuditor** recommends 5-point cap: "Informational findings are definitionally low-signal. Their aggregate contribution shouldn't move the tier needle."
- **Performance Alchemist (B)** suggests 3-point cap: "Even 5 points from informational is generous. Cap at 3 to match the 'low' severity contribution model."
- **Data Governance Warden (G)** suggests 10-point cap: "Some visibility in the risk score is warranted. A TB with 30 informational items is different from one with 0."
- **Resolution**: 5-point cap adopted (6/9 vote). Rationale: 5 points can contribute to but never independently trigger a tier change (need 26 for "elevated"). The cap provides meaningful signal differentiation (0 vs 5 informational items) without the inflation problem (30 informational items capped at 5).

### Tension 3: ISA 265 Language — Fix Now or Defer?
- **AccountingExpertAuditor** wants immediate fix: "Any language that includes 'adjusting entry' as system output creates regulatory positioning risk."
- **Systems Architect (A)** wants deferral: "The language is conditional ('consider whether'). No user has flagged it. Fix in the next DEC remediation cycle."
- **DX & Accessibility Lead (C)** agrees with fix: "It's a string replacement. Trivial implementation cost, meaningful compliance benefit."
- **Resolution**: Fix in remediation sprint (7/9 vote). The language change is a string replacement with no behavioral impact. Include in the next sprint alongside F-001 and F-002.

## 5) Discovered Standards → Proposed Codification

- **Existing standards verified**:
  - Sprint commit convention: **100% compliant** for Sprints 532–537
  - Post-sprint checklist: **100% followed** (all verification boxes checked, commit SHAs recorded)
  - Directive Protocol enforcement: **AUTOMATED** (commit-msg hook: todo staging + archival gate)
  - Auth classification: **100% compliant** (`require_verified_user` for audit/export, `require_current_user` for client/user/settings)
  - Theme palette: **100% compliant** (zero violations across all component files)
  - Classification rules centralization: **100% compliant** (all keywords in `classification_rules.py`)
  - Framer-motion `as const`: **100% compliant** (34/34 declarations)
  - Coverage enforcement: **ACTIVE** (pytest 80% both jobs, Jest 35%)
  - Cross-origin fetch credentials: **100% compliant**
  - ISA 265 boundary: **P3 gap identified** (F-006 — "potential adjusting entry" language)
  - Division-by-zero protection: **100% compliant** (all 14 ratios + DuPont)
  - Zero-Storage: **100% compliant**
  - Archival enforcement: **AUTOMATED** (commit-msg hook + `scripts/archive_sprints.sh`)

- **Standards requiring attention**:
  - **Informational tier cascade**: Keyword assignment should precede general-purpose escalation → F-001
  - **Risk score calibration**: New severity tiers require score contribution caps → F-002
  - **Keyword carve-outs**: Related-party loan variants missing from carve-out list → F-007
  - **Filter UI parity**: New severity values must propagate to all filter controls → F-004

## 6) Next Sprint Recommendation

### Sprint 538 — Informational Tier Calibration + DEC 2026-03-16 Remediation

**Complexity Score:** 4/10 (targeted fixes, no architectural changes, well-defined scope)

**Primary Objectives (P2):**
1. Reorder `classify_round_number_tier()`: move informational keyword check before 10%-TB escalation (F-001)
2. Cap informational risk score contribution at 5 points (F-002)

**Secondary Objectives (P3):**
3. Add 'informational' option to severity filter dropdowns in `FlaggedEntriesTable` and `FollowUpItemsTable` (F-004)
4. Replace "potential adjusting entry" language with "items requiring auditor follow-up" in `tb_diagnostic_constants.py` (F-006)
5. Add related-party loan variants to `ROUND_NUMBER_TIER1_CARVEOUTS` (F-007)
6. Fix Benford MAD digit filter: `>` → `>=` (F-009)

**Optional (P3, may defer):**
7. Narrow bare `"cash"` keyword scope in `ROUND_NUMBER_TIER2_INFORMATIONAL` (F-003)
8. Add contra-equity detection to multi-period credit-normal sign flip (F-005)
9. Add `__test__ = False` to `TestTier` enum (F-014)

**Verification:**
- `npm run build` passes
- `npm test` — 1,339 tests pass
- `pytest` — 6,507 tests pass (at 80% threshold)
- QA sweep: Cascade + Meridian datasets — informational tier assertions stable
- New test: Cash account at >10% TB total returns "informational" (not "material")
- New test: 20 informational findings produce max 5 risk score points

**Agents:**
- **Primary**: AccountingExpertAuditor, DX & Accessibility Lead (C)
- **Supporting**: Verification Marshal (I), Type & Contract Purist (H)

## 7) Agent Coverage Report

- **Systems Architect (A)**: Architecture stable. No functions exceed 300 lines. Largest modules (`audit_engine.py` 2,421 lines, `pdf_generator.py` 2,367 lines) well-decomposed. Zero circular imports. No N+1 query patterns. `NEAR_ZERO`/`BALANCE_TOLERANCE` duplication flagged (F-013).
- **Performance Alchemist (B)**: No performance concerns. BytesIO memory patterns safe (500 instances, properly scoped). Rate limiting tiered appropriately (5 tiers). No memory leaks detected. Informational tier adds negligible compute overhead.
- **DX & Accessibility Lead (C)**: Sprint 533 fixed all 7 aria-label gaps from prior DEC. Framer-motion 34/34 compliant. WCAG compliance maintained. Severity filter gap identified (F-004) — informational option missing from 2 data table dropdowns.
- **Security & Privacy Lead (D)**: Zero OWASP Top 10 vectors detected. All 11 CI security gates active. No hardcoded secrets. Multi-backend secrets manager. Archive bomb + XML bomb + formula injection all mitigated. CSRF HMAC + rate limiting intact. Zero `eval()`/`exec()`/`pickle.loads()`. Zero bare `except:`.
- **Modernity & Consistency Curator (E)**: Lint baseline current (2026-03-15). Zero `console.log` in production. Zero deprecated imports. TypeScript strict compliance: zero `any`, zero `@ts-ignore`. `NEAR_ZERO` duplication flagged (F-013). `TestTier` warning flagged (F-014).
- **Observability & Incident Readiness (F)**: DEPLOY-VERIFY log infrastructure active (Sprints 535–537). Sentry sanitization unchanged. Prometheus metrics active (2 counters). Zero hot-path logging. QA sweep automation recommended (F-008).
- **Data Governance & Zero-Storage Warden (G)**: All persistence pathways verified. Financial data ephemeral. Metadata-only persistence confirmed. Risk score calibration concern raised (F-002) — informational tier should not inflate scores beyond intent.
- **Type & Contract Purist (H)**: OpenAPI snapshot stable (309 schemas, 159 paths). TypeScript type safety at 100%. `Severity` type correctly extended with `'informational'` across all 7 `Record<Severity, ...>` mappings. Filter dropdown parity gap identified (F-004).
- **Verification Marshal (I)**: 100% DEC remediation rate sustained across 3 consecutive cycles. CI gates comprehensive (11 active + 3 advisory). Coverage thresholds at appropriate levels. Sprint 533 verification complete — all 3 prior findings confirmed fixed. QA automation CI integration recommended (F-008).
- **AccountingExpertAuditor**: Two P2 methodology findings (tier cascade ordering, risk score calibration). ISA 265 boundary mostly maintained with one P3 language gap. Classification rules comprehensive but keyword scope needs tightening (F-003, F-007). Benford's Law ISA 520 compliant with minor precision correction (F-009). GAAP/IFRS compatibility maintained. All 14 ratios mathematically correct with division-by-zero protection. Contra-equity sign convention gap in multi-period (F-005).
