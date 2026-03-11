# Paciolus Daily Digital Excellence Council Report
Date: 2026-03-11
Commit/Branch: c136eba / main
Files Changed Since Last Audit: 172 (across 24 commits, Sprints 516–530 + hotfixes)

## 1) Executive Summary
- Total Findings: 15
  - P0 (Stop-Ship): 0
  - P1 (High): 0
  - P2 (Medium): 4
  - P3 (Low): 9
  - Informational: 2
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Accounting Methodology Gaps**: F-001, F-002, F-003, F-004 (4 findings — contra-liability omission, AOCI misclassification, bare "non-operating" mismap, missing management fee keyword)
  - **Suspense Detection Calibration**: F-005, F-006 (2 findings — "sundry" false positive risk, "float" below threshold dead code)
  - **Cross-Origin Transport Inconsistency**: F-007 (1 finding — uploadTransport missing `credentials: 'include'`)
  - **CI Coverage Enforcement Gap**: F-008, F-009 (2 findings — no `--cov-fail-under` backend, Jest coverage not triggered in CI)
  - **Type Safety & Code Consistency**: F-010, F-011 (2 findings — MarketingNav `as const`, variant pattern inconsistency)
  - **Operational Noise**: F-012, F-013 (2 findings — deploy-verify log volume, COGS singular/plural inconsistency)
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — All 172 changed files audited. sessionStorage for anonymous history (F-011 fixed). HTTP metrics path-normalized. No new persistence pathways. Sentry breadcrumb filtering active on both client/server.
  - Auth/CSRF Integrity: **PASS** — Export sharing corrected to `require_verified_user`. SameSite=None + Secure conditional on production. HMAC CSRF stateless. Stripe webhook signature + idempotency verified. Commit-msg hook enforces directive protocol.
  - Observability Data Leakage: **PASS** — `beforeBreadcrumb` in both frontend Sentry configs. `before_send_transaction` strips query strings in backend. HTTP RED metrics use bounded labels. Per-request access logs with request_id correlation. No PII or financial data in any log pathway.
- Prior DEC Remediation Rate: **18/21 findings fixed (86%)** — up from 76% at last audit.

## 2) Daily Checklist Status

1. **Zero-storage enforcement (backend/frontend/logs/telemetry/exports):** ✅ PASS — No new data persistence pathways. `useActivityHistory` now uses `sessionStorage` (F-011 fixed). All 19 memo generators use `BytesIO`. HTTP metrics exclude `/health` and `/metrics` from recording. ExportShare 48h TTL exception documented.

2. **Upload pipeline threat model (size limits, bombs, MIME, memory):** ✅ PASS — No upload pipeline changes. 10-step validation pipeline unchanged. `uploadTransport.ts` properly injects Bearer + CSRF tokens. Minor `credentials: 'include'` inconsistency noted (F-007) but does not affect auth correctness.

3. **Auth + refresh + CSRF lifecycle coupling:** ✅ PASS — Cross-origin auth fix (292014e) correctly applies `SameSite=None; Secure` conditionally. Cookie deletion now includes matching attributes. HMAC CSRF is stateless — no cookie dependency.

4. **Observability data leakage (Sentry/logs/metrics):** ✅ PASS — All 3 previous gaps (F-008, F-009, F-017 from DEC 2026-03-08) now fixed. `beforeBreadcrumb` strips URL query params. `before_send_transaction` strips query strings from transaction names. HTTP RED metrics use path normalization with 5 regex patterns.

5. **OpenAPI/TS type generation + contract drift:** ✅ PASS — Sprint 518 added snapshot-based drift detection (309 schemas, 159 paths). CI job configured. `TestingRiskTier` aligned (4 values only). `AuditResultResponse` type added.

6. **CI security gates (Bandit/pip-audit/npm audit/policy):** ⚠️ PARTIAL — `pytest-cov` added to CI and reports coverage. But no `--cov-fail-under` threshold (F-008). Jest coverage measurement not triggered in CI (F-009). Security gates (Bandit, pip-audit, npm-audit, CODEOWNERS) remain active.

7. **APScheduler safety under multi-worker:** ✅ PASS — No scheduler changes. Singleton pattern with global `_scheduler`.

8. **Next.js CSP nonce + dynamic rendering:** ✅ PASS — `proxy.ts` unchanged. Per-request nonce with `crypto.randomUUID()`.

## 3) Findings Table (Core)

### F-001: No Contra-Liability Branch in `is_contra_account()`
- **Severity**: P2
- **Category**: Accounting Methodology
- **Evidence**:
  - `backend/classification_rules.py:551-569` — `is_contra_account()` has branches for `ASSET`, `REVENUE`, and `EQUITY` only. No `LIABILITY` case.
  - Under US GAAP (APB 21, ASC 835-30, ASC 470-20): Discount on Notes Payable, Discount on Bonds Payable, Debt Issuance Costs (post-ASU 2015-03), Unamortized Bond Discount are contra-liabilities with debit normal balances.
  - Without the `LIABILITY` branch, these accounts are flagged as abnormal (debit balance on a liability = abnormal), producing false positives.
- **Impact**: False positive findings on any TB with long-term debt. Affects leveraged entities, bond issuers, and any company with amortized debt issuance costs.
- **Recommendation**: Add `CONTRA_LIABILITY_KEYWORDS` list and a `LIABILITY` branch in `is_contra_account()`. Keywords: `"discount on notes"`, `"discount on bonds"`, `"bond discount"`, `"debt issuance cost"`, `"unamortized discount"`, `"loan origination fee"`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2]
  Goal: Add contra-liability recognition to is_contra_account()
  Files in scope: backend/classification_rules.py
  Approach: Add CONTRA_LIABILITY_KEYWORDS list with debt-related contra keywords. Add LIABILITY branch in is_contra_account(). Add test cases to test_contra_and_detection_fixes.py.
  Acceptance criteria:
  - is_contra_account("Discount on Bonds Payable", LIABILITY) returns True
  - Discount on Bonds Payable with debit balance is NOT flagged as abnormal
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Systems Architect (A), Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-002: AOCI Unconditionally Treated as Contra-Equity
- **Severity**: P2
- **Category**: Accounting Methodology
- **Evidence**:
  - `backend/classification_rules.py` — `CONTRA_EQUITY_KEYWORDS` includes `"accumulated other comprehensive"`.
  - Under ASC 220/IAS 1, AOCI balance alternates between debit (net loss) and credit (net gain) depending on market movements. It is not a consistent contra-equity account.
  - When AOCI carries a debit balance (net unrealized losses), `is_contra_account()` returns True and inverts the expected direction, suppressing the flag — but a large debit AOCI is a legitimate risk signal for going concern analysis.
- **Impact**: Suppresses a meaningful risk indicator on entities with material unrealized losses (investment portfolios, hedge accounting).
- **Recommendation**: Remove `"accumulated other comprehensive"` from `CONTRA_EQUITY_KEYWORDS`. Treasury Stock and Dividends Declared (which are genuinely and consistently contra-equity) remain correct.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2]
  Goal: Remove AOCI from contra-equity keywords
  Files in scope: backend/classification_rules.py
  Approach: Remove "accumulated other comprehensive" from CONTRA_EQUITY_KEYWORDS. AOCI should be evaluated by standard abnormal-balance logic without inversion.
  Acceptance criteria:
  - is_contra_account("Accumulated Other Comprehensive Income", EQUITY) returns False
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Data Governance Warden (G)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Systems Architect (A): "Treat as P3 — niche scenario."
- **Chair Rationale**: P2 sustained. AOCI is common in entities holding available-for-sale securities. Incorrect suppression masks a going concern indicator.

---

### F-003: Bare "non-operating" Maps to EXPENSE Only
- **Severity**: P2
- **Category**: Accounting Methodology / Data Classification
- **Evidence**:
  - `backend/audit_engine.py:~1078,1080` — `_CSV_TYPE_MAP` entries:
    ```python
    "non-operating": AccountCategory.EXPENSE,
    "nonoperating": AccountCategory.EXPENSE,
    ```
  - Qualified entries already exist: `"non-operating revenue"`, `"non-operating income"`, `"nonoperating revenue"`, `"non-operating expense"`.
  - Some accounting systems (Sage, QuickBooks) export bare "non-operating" for both income and expense accounts.
- **Impact**: Non-operating income accounts (interest income, dividend income, gain on disposal) silently misclassified as expenses. Produces incorrect gross margin, operating margin, and net margin ratios.
- **Recommendation**: Remove the bare "non-operating"/"nonoperating" entries. Accounts using this label will fall through to the heuristic classifier which evaluates account name + balance direction.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2]
  Goal: Remove ambiguous bare "non-operating" CSV type entries
  Files in scope: backend/audit_engine.py
  Approach: Delete the "non-operating" and "nonoperating" entries from _CSV_TYPE_MAP. The qualified entries ("non-operating revenue", "non-operating expense") remain.
  Acceptance criteria:
  - _resolve_csv_type("non-operating") returns (None, 0.0)
  - Qualified entries still resolve correctly
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-004: "management fee" Absent from Related Party Keywords
- **Severity**: P2
- **Category**: Accounting Methodology / Detection Coverage
- **Evidence**:
  - `backend/classification_rules.py` — `RELATED_PARTY_KEYWORDS` does not contain `"management fee"`, `"management fee payable"`, or `"management services"`.
  - ASC 850-10-20 explicitly includes management contracts as related party relationships requiring disclosure.
  - Management fees to parent entities are among the most common related party transactions in private company and middle-market audits (LBO structures, family business groups, franchisor-franchisee).
  - An account named "Management Fee Expense — ABC Holdings" has no keyword match.
- **Impact**: Silent non-detection of a high-frequency related party transaction type. Affects leveraged buyout structures and family-owned entities.
- **Recommendation**: Add `("management fee", 0.90, True)` to `RELATED_PARTY_KEYWORDS`. Consider also `("consulting fee", 0.85, True)`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2]
  Goal: Add management fee to related party detection keywords
  Files in scope: backend/classification_rules.py
  Approach: Add ("management fee", 0.90, True) to RELATED_PARTY_KEYWORDS.
  Acceptance criteria:
  - "Management Fee Expense — Parent Co" triggers related party detection
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-005: "sundry" Keyword at Suspense Threshold — False Positive Risk
- **Severity**: P3
- **Category**: Accounting Methodology / Suspense Detection
- **Evidence**:
  - `backend/classification_rules.py` — `SUSPENSE_KEYWORDS` contains `("sundry", 0.60, False)`.
  - `SUSPENSE_CONFIDENCE_THRESHOLD` is 0.60. Any account containing "sundry" with no other keywords will fire at exactly the threshold.
  - "Sundry Debtors", "Sundry Income", "Sundry Creditors" are legitimate account labels in UK GAAP, IFRS, and Commonwealth-jurisdiction accounting systems.
- **Impact**: False positive suspense flags on legitimate accounts. Affects any engagement using a Commonwealth-style chart of accounts.
- **Recommendation**: Remove `"sundry"` from `SUSPENSE_KEYWORDS`. The false-positive cost on legitimate accounts outweighs the detection benefit.
- **Primary Agent**: AccountingExpertAuditor
- **Vote** (9 members; quorum=6): 8/9 Approve P3 | Dissent: Verification Marshal (I): "P2 — affects international users."
- **Chair Rationale**: P3 sustained. Users can dismiss findings individually. The keyword sits exactly at threshold, so any other keyword would already push it above.

---

### F-006: "float" Weight Below Threshold — Dead Code
- **Severity**: P3
- **Category**: Code Quality / Dead Code
- **Evidence**:
  - `backend/classification_rules.py` — `SUSPENSE_KEYWORDS` contains an entry with weight 0.55.
  - `SUSPENSE_CONFIDENCE_THRESHOLD` is 0.60.
  - A single "float" match at 0.55 will never trigger suspense detection by itself.
  - "Petty cash float" is a legitimate current asset account — not a suspense account.
- **Impact**: Misleading code intent. Entry produces no false positives (it never fires) but creates confusion for maintainers.
- **Recommendation**: Remove the entry. Legitimate "float" accounts should not be treated as suspense.
- **Primary Agent**: AccountingExpertAuditor
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-007: `uploadTransport.ts` Missing `credentials: 'include'`
- **Severity**: P3
- **Category**: HTTP Transport / Consistency
- **Evidence**:
  - `frontend/src/utils/uploadTransport.ts:48-52` — `fetch()` call does not include `credentials: 'include'`.
  - `frontend/src/utils/apiClient.ts:599` — `fetch()` call correctly includes `credentials: 'include'`.
  - `frontend/src/contexts/AuthContext.tsx:91,238` — refresh/logout calls include `credentials: 'include'`.
  - Commit 292014e added cross-origin credentials to `apiClient.ts` but did not update `uploadTransport.ts` (introduced later in Sprint 519).
- **Impact**: Functional impact is LOW because: (a) `uploadTransport` uses Bearer token auth (line 43), not cookie-based auth; (b) CSRF validation uses stateless HMAC tokens, not double-submit cookies. However, it creates an inconsistency across fetch utilities and could break if any future middleware relies on cookie presence.
- **Recommendation**: Add `credentials: 'include'` to the fetch call for consistency with the rest of the codebase.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add credentials: 'include' to uploadTransport for consistency
  Files in scope: frontend/src/utils/uploadTransport.ts
  Approach: Add credentials: 'include' to the fetch options object at line 48.
  Acceptance criteria:
  - All fetch calls in the codebase consistently include credentials: 'include'
  - npm run build passes
  - uploadTransport.test.ts passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Security & Privacy Lead (D)
- **Supporting Agents**: Systems Architect (A)
- **Vote** (9 members; quorum=6): 6/9 Approve P3 | Dissent: Security Lead (D): "P2 — defense-in-depth gap." Performance Alchemist (B): "P3 — Bearer + HMAC is sufficient." Verification Marshal (I): "P2 — inconsistency is a maintenance trap."
- **Chair Rationale**: P3 sustained. Bearer token + HMAC CSRF provides complete auth coverage without cookies. The inconsistency is real but not an active vulnerability.

---

### F-008: No `--cov-fail-under` Threshold in Backend CI
- **Severity**: P3
- **Category**: CI/CD / Coverage Enforcement
- **Evidence**:
  - `.github/workflows/ci.yml:96` — `pytest tests/ -v --tb=short -q --cov=. --cov-report=term-missing` runs with coverage measurement but no minimum threshold.
  - `pytest-cov>=6.0.0` correctly added to `backend/requirements-dev.txt`.
  - DEC 2026-03-08 F-007 repair prompt explicitly said: "Do NOT add `--cov-fail-under` yet (establish baseline first)."
  - Baseline has now been established (92.8% per `tasks/usage-metrics-review.md`).
- **Impact**: Coverage can silently regress without CI failure. New features can ship with zero test coverage undetected.
- **Recommendation**: Add `--cov-fail-under=60` to the pytest CI invocation now that baseline is established.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-009: Jest Coverage Not Triggered in CI
- **Severity**: P3
- **Category**: CI/CD / Coverage Enforcement
- **Evidence**:
  - `.github/workflows/ci.yml:252` — `npx jest --ci --forceExit` runs without `--coverage` flag.
  - `frontend/jest.config.js:71-76` defines `coverageThreshold` at 25% (branches, functions, lines, statements) — but thresholds are only enforced when `--coverage` is passed.
  - DEC 2026-03-08 F-007 said to "Remove `--no-coverage` from Jest CI invocation." This was done (no more `--no-coverage`), but `--coverage` was not added.
- **Impact**: Frontend coverage thresholds defined but never enforced. Coverage regressions invisible.
- **Recommendation**: Change CI command to `npx jest --ci --forceExit --coverage` to activate the existing 25% thresholds.
- **Primary Agent**: Verification Marshal (I)
- **Supporting Agents**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-010: MarketingNav framer-motion Missing `as const`
- **Severity**: P3
- **Category**: Type Safety / Code Quality
- **Evidence**:
  - `frontend/src/components/marketing/MarketingNav.tsx:39-48` — `mobileItemVariants` and `mobileContainerVariants` defined without `as const`.
  - `UnifiedToolbar.tsx` (lines 28-41) and `ProfileDropdown.tsx` (line 60) correctly use `as const`.
  - Pre-existing code — not changed in this commit range.
- **Impact**: Type narrowing lost at compile time. Variant type becomes untyped instead of literal union. No runtime impact.
- **Recommendation**: Append `as const` to both variant definition objects.
- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-011: framer-motion Variant Pattern Inconsistency — No Documented Standard
- **Severity**: P3
- **Category**: Code Quality / Documentation
- **Evidence**:
  - Four different approaches in use across changed files:
    1. **Inline + `as const`**: UnifiedToolbar, ProfileDropdown (RECOMMENDED)
    2. **Imported from `lib/motion`**: CommandPalette (CANONICAL — shared module)
    3. **Inline, no `as const`**: MarketingNav (NOT RECOMMENDED — see F-010)
  - No documented style guide for which pattern to use.
- **Impact**: New developers unsure which pattern to follow.
- **Recommendation**: Document preferred pattern in CLAUDE.md or component style guide: use `lib/motion` for reusable animations, inline + `as const` for component-specific animations.
- **Primary Agent**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-012: `is_contra_account()` Deploy-Verify Log Volume
- **Severity**: P3
- **Category**: Observability / Operational
- **Evidence**:
  - `backend/classification_rules.py:560` — `logger.info("[DEPLOY-VERIFY-530] is_contra_account called: ...")` emits on every call.
  - Called once per account per analysis pass. A TB with 500 accounts and 3 sheets generates ~1,500 log entries per upload.
  - The deploy verification log pattern used in `_resolve_csv_type()` (first-N calls) is the appropriate model.
- **Impact**: Degrades log signal-to-noise ratio at production volume. Non-trivial I/O overhead.
- **Recommendation**: Convert to first-N pattern or remove now that Sprint 530 deploy verification is complete.
- **Primary Agent**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-013: "direct cost" vs "direct costs" Singular/Plural Inconsistency
- **Severity**: P3
- **Category**: Code Quality / Data Classification
- **Evidence**:
  - `backend/ratio_engine.py:~2131` — `COGS_KEYWORDS` contains `"direct cost"` (singular).
  - `backend/ratio_engine.py:~2230` — `_COGS_SUBTYPES` contains `"direct costs"` (plural).
  - A CSV type value of "Direct Cost" (singular) won't match `_COGS_SUBTYPES` and falls through to keyword matching, where the account name must also contain "direct cost" for COGS recognition.
- **Impact**: Edge case where a CSV with type "Direct Cost" (singular) and non-descriptive account name misses COGS classification.
- **Recommendation**: Add `"direct cost"` (singular) to `_COGS_SUBTYPES`.
- **Primary Agent**: AccountingExpertAuditor
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-014: Prior DEC Findings — Remediation Status
- **Severity**: Informational
- **Category**: Process / Verification
- **Evidence**:

  | Prior Finding (DEC 2026-03-08) | Status |
  |-------------------------------|--------|
  | F-001: Memo utility duplication | **FIXED** — Sprint 516/527 |
  | F-002: Export sharing auth | **FIXED** — Sprint 516 |
  | F-003: Skip navigation | **FIXED** — Sprint 516 |
  | F-004: Command palette ARIA | **FIXED** — Sprint 516 |
  | F-005: Nav landmarks aria-label | **FIXED** — Sprint 516 |
  | F-006: Stripe webhook HTTP test | **FIXED** — Sprint 520 |
  | F-007: Backend coverage in CI | **FIXED** — Sprint 516 (measurement only; threshold → F-008) |
  | F-008: HTTP request metrics | **FIXED** — Sprint 516 |
  | F-009: Sentry breadcrumb filtering | **FIXED** — Sprint 516 |
  | F-010: .env.example stale defaults | **FIXED** — Sprint 516 |
  | F-011: localStorage→sessionStorage | **FIXED** — Sprint 516 |
  | F-012: sanitize_exception context | **FIXED** — Sprint 516 |
  | F-013: TestingRiskTier 'critical' | **FIXED** — Sprint 516 |
  | F-014: anomaly_summary random.randint | **FIXED** — Sprint 516 |
  | F-015: ProfileDropdown ARIA + version | **FIXED** — Sprint 516 |
  | F-016: UsageMeter amber colors | **FIXED** — Sprint 516 |
  | F-017: Structured access log | **FIXED** — Sprint 516 |
  | F-018: 5 memo generator test files | **FIXED** — Sprint 517 |
  | F-019: Sprint 481 documentation gap | **FIXED** — Hotfix entry added |
  | F-020: OpenAPI drift detection | **FIXED** — Sprint 518 |
  | F-021: Prior remediation tracking | **N/A** — Informational |

  **Remediation Rate**: 18/21 fixed (86%, up from 76%). All 8 P2 findings from prior DEC are fixed.

- **Primary Agent**: Verification Marshal (I)

---

### F-015: Sprint 516–530 Architectural Improvements — Positive Assessment
- **Severity**: Informational
- **Category**: Architecture / Positive
- **Evidence**:
  - **Sprint 516**: 17/21 prior DEC findings fixed. HTTP metrics middleware, Sentry sanitization, WCAG accessibility, theme compliance, coverage measurement.
  - **Sprint 517**: 5 memo generator test files (137 tests) — closes DEC F-018.
  - **Sprint 518**: OpenAPI schema drift detection (309 schemas, 159 paths) — closes DEC F-020.
  - **Sprint 519**: Structural debt remediation (5-phase code quality sweep). `uploadTransport.ts` extraction.
  - **Sprint 520**: Billing security & correctness (webhook idempotency, seat management).
  - **Sprint 521**: Directive Protocol enforcement (commit-msg hook).
  - **Sprint 522–524**: PDF report quality (institutional-grade improvements).
  - **Sprint 526**: Diagnostic engine calibration (7 fixes).
  - **Sprint 527**: DEC 2026-03-10 remediation (6 P2 findings — 100% fixed).
  - **Sprint 528**: CSV account type expansion (56 entries + suffix fallback, 77 tests).
  - **Sprint 529**: CSV account type data flow fix (root cause of Unknown classifications).
  - **Sprint 530**: Contra account recognition, false positive reduction, 9 fixes (68 tests).
  - **Total**: ~500 new backend tests across 8 test files. Zero regressions.
- **Primary Agent**: Systems Architect (A)

## 4) Council Tensions & Resolution

### Tension 1: uploadTransport `credentials: 'include'` — P2 vs P3
- **Security & Privacy Lead (D)** wants P2: "Defense-in-depth gap. Inconsistency with apiClient creates a maintenance trap. If any future middleware checks cookies, uploads break silently."
- **Systems Architect (A)** supports P3: "Bearer token + HMAC CSRF provides complete auth coverage without cookies. No active vulnerability exists today."
- **Resolution**: P3 sustained (6/9 vote). The current auth model (Bearer + HMAC) does not require cookies for upload requests. The inconsistency is real and should be fixed, but it is not an active vulnerability. P2 would require evidence of functional failure, which was not demonstrated.

### Tension 2: AOCI Contra-Equity Classification — P2 vs P3
- **Systems Architect (A)** suggests P3: "Niche scenario — only affects entities with material OCI positions."
- **AccountingExpertAuditor** insists P2: "Any entity holding available-for-sale securities has AOCI. Suppressing the debit-balance flag masks a going concern indicator."
- **Resolution**: P2 sustained (8/9 vote). ASC 220 defines AOCI as a component of equity, not a contra account. The expert assessment is methodologically correct.

### Tension 3: "sundry" Suspense Detection — P2 vs P3
- **Verification Marshal (I)** wants P2: "Affects all international users with Commonwealth-style charts."
- **AccountingExpertAuditor** supports P3: "Users can dismiss individual findings. The keyword sits exactly at threshold."
- **Resolution**: P3 sustained (8/9 vote). Single-finding dismissal is available. The priority ordering (Related Party > Intercompany > Suspense > Round Number) means "sundry" findings would be suppressed if higher-priority keywords match.

## 5) Discovered Standards → Proposed Codification

- **Existing standards verified**:
  - `as const` convention: **99%+ compliant** (1 pre-existing gap: MarketingNav)
  - Sprint commit convention: **100% compliant** for Sprints 516–530
  - Post-sprint checklist: **100% followed**
  - Auth classification: **100% compliant** (export_sharing fixed)
  - Theme palette: **100% compliant** (UsageMeter fixed)
  - Memo generator utility imports: **100% compliant** (all 9 generators verified)
  - Classification rules centralization: **100% compliant** (all keywords in `classification_rules.py`)

- **New standards confirmed in this cycle**:
  - **Sentry breadcrumb policy**: `beforeBreadcrumb` filter required in all Sentry configs ✓
  - **Coverage measurement**: CI now outputs coverage percentages (enforcement thresholds pending → F-008/F-009)
  - **OpenAPI drift detection**: Snapshot-based CI job active
  - **Directive Protocol enforcement**: Commit-msg hook rejects Sprint commits without `tasks/todo.md`

- **Missing standards that should become policy**:
  - **Contra-account keyword coverage**: Review and validate keyword lists against ISA/GAAP references before each release (methodology audit gate).
  - **Coverage enforcement thresholds**: Establish `--cov-fail-under=60` for backend, activate `--coverage` for frontend Jest.
  - **Cross-origin fetch consistency**: All `fetch()` calls in auth-required contexts MUST include `credentials: 'include'`.
  - **Deploy-verify log lifecycle**: Deploy-verify log lines MUST be converted to first-N pattern or removed within 2 sprints of deployment.

## 6) Agent Coverage Report

- **Systems Architect (A) — "The Stalwart"**:
  - Touched areas: All 19 memo generators, `shared/` modules, middleware registration, engine architecture
  - Top 3 findings contributed: F-012 (supporting), F-013 (supporting)
  - Non-obvious risk: `audit_trial_balance_multi_sheet()` at ~283 lines is the longest function. Acceptable for orchestration, but continued growth should be monitored.

- **Performance & Cost Alchemist (B) — "The Optimizer"**:
  - Touched areas: HTTP metrics middleware path normalization, BytesIO memory patterns
  - Non-obvious risk: `BytesIO` → `getvalue()` → return doubles memory for large reports. Current ~100KB/report is safe; monitor if reports exceed 1MB.

- **DX & Accessibility Lead (C) — "The Diplomat"**:
  - Touched areas: All navigation components, command palette, profile dropdown, error boundaries
  - Top 3 findings contributed: F-010 (primary), F-011 (primary)
  - Non-obvious risk: 5 error boundaries all follow identical pattern — consider extracting a shared `ErrorPage` component to eliminate 50+ lines of duplication.

- **Security & Privacy Lead (D) — "Digital Fortress"**:
  - Touched areas: All route files, Sentry configs, auth routes, CSRF middleware, billing security
  - Top 3 findings contributed: F-007 (primary)
  - Non-obvious risk: `ExportShare` stores `shared_by_name = user.name or user.email` — PII persists in DB beyond 48h if cleanup fails. Known documented exception but worth re-evaluating.

- **Modernity & Consistency Curator (E) — "The Trendsetter"**:
  - Touched areas: Package versions, code patterns, variant consistency
  - Top 3 findings contributed: F-011 (primary)
  - Non-obvious risk: `ts-jest` v29 with Jest v30 — version mismatch may cause subtle issues in future.

- **Observability & Incident Readiness (F) — "The Detective"**:
  - Touched areas: `http_metrics_middleware.py`, `logging_config.py`, Sentry configs, health probes
  - Top 3 findings contributed: F-008 (supporting), F-009 (supporting), F-012 (primary)
  - Non-obvious risk: HTTP metrics exclude `/health` and `/metrics` — if health checks fail silently, no RED metric records exist for diagnosis.

- **Data Governance & Zero-Storage Warden (G) — "The Auditor"**:
  - Touched areas: All data persistence paths, frontend storage APIs, DB models, export flows
  - Non-obvious risk: `sessionStorage` clears on tab close — users who accidentally close the tab lose anonymous analysis history. This is by design but worth noting in UX.

- **Type & Contract Purist (H) — "The Pedant"**:
  - Touched areas: Frontend type definitions, `testingShared.ts`, `diagnostic.ts`, OpenAPI snapshot
  - Top 3 findings contributed: F-010 (supporting)
  - Non-obvious risk: OpenAPI snapshot is 309 schemas / 159 paths. Manual snapshot regeneration creates a human-error vector — consider automating in CI.

- **Verification Marshal (I) — "The Skeptic"**:
  - Touched areas: CI pipeline, test files, coverage config, git hooks, sprint documentation
  - Top 3 findings contributed: F-008 (primary), F-009 (primary), F-014 (primary)
  - Non-obvious risk: `commit-msg` hook allows `--no-verify` bypass. Emergency use is documented, but consider logging bypass events.

- **AccountingExpertAuditor — "The Methodologist"**:
  - Touched areas: `classification_rules.py`, `audit_engine.py`, `ratio_engine.py`, `tb_post_processor.py`
  - Top 3 findings contributed: F-001 (primary), F-002 (primary), F-003 (primary), F-004 (primary), F-005 (primary), F-006 (primary), F-013 (primary)
  - Non-obvious risk: The contra account recognition system is keyword-based. Any new account naming convention (e.g., "contra-revenue" as a prefix) would require explicit keyword additions.
