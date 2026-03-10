# Paciolus Daily Digital Excellence Council Report
Date: 2026-03-10
Commit/Branch: ffe316f / main
Files Changed Since Last Audit: 149 (across 16 commits, Sprints 516–526 + hotfixes)

## 1) Executive Summary
- Total Findings: 15
  - P0 (Stop-Ship): 0
  - P1 (High): 0
  - P2 (Medium): 6
  - P3 (Low): 7
  - Informational: 2
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Classification Pipeline Hardcoding**: F-001, F-002 (2 findings — new detection keywords bypass `classification_rules.py`; concentration benchmarks hardcode thresholds that imported constants already define)
  - **Residual Code Duplication**: F-003 (1 finding — `_standard_table_style()` still duplicated in 3 diagnostic memos after Sprint 516 remediation)
  - **Type Safety Gaps**: F-004, F-008 (2 findings — wide `AuditResult` type cast in upload hook; `unknown[]` cast in BatchUploadContext)
  - **Test Coverage Gaps**: F-005, F-009 (2 findings — no unit tests for `uploadTransport.ts`; 5 memo test files still deferred)
  - **Dead/Stale Code**: F-006, F-007 (2 findings — unused `provided_account_types` attributes; `loadFromLocalStorage()` name stale after sessionStorage migration)
  - **Defensive Programming**: F-010 (1 finding — post-processors assume result structure without validation)
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — All new files audited (engine_framework, checkout_orchestrator, usage_service, tb_post_processor, materiality_resolver, uploadTransport, 4 decomposed hooks). No financial data persistence. `useActivityHistory` confirmed on `sessionStorage`. HTTP metrics middleware strips all IDs via path normalization. No new data pathways.
  - Auth/CSRF Integrity: **PASS** — F-002 (export_sharing auth) fixed. All audit endpoints use `require_verified_user`. Stripe webhook CSRF exemption justified by signature verification. New `uploadTransport.ts` properly injects Authorization + CSRF-Token headers.
  - Observability Data Leakage: **PASS** — `beforeBreadcrumb` added to both Sentry configs (F-009 fixed). `before_send_transaction` added to backend. HTTP metrics middleware normalizes all dynamic path segments. No PII or financial data in logs/metrics.

## 2) Daily Checklist Status

1. **Zero-storage enforcement (backend/frontend/logs/telemetry/exports):** PASS — All 149 changed files audited. 7 new backend modules maintain ephemeral processing. `sessionStorage` confirmed for anonymous activity history. `checkout_orchestrator` stores only Stripe IDs/tier metadata.

2. **Upload pipeline threat model (size limits, bombs, MIME, memory):** PASS — New `uploadTransport.ts` delegates to existing `validate_file_size()` pipeline. `execute_file_tool()` scaffold wraps all tool endpoints with `memory_cleanup()` context manager.

3. **Auth + refresh + CSRF lifecycle coupling:** PASS — `uploadTransport.ts` correctly injects both Authorization and CSRF-Token headers. 401/403 error codes properly surfaced including `EMAIL_NOT_VERIFIED` structured code.

4. **Observability data leakage (Sentry/logs/metrics):** PASS — F-008, F-009, F-017 all fixed. HTTP RED metrics with path normalization. Structured access logs with request_id correlation. Sentry breadcrumb/transaction sanitization complete.

5. **OpenAPI/TS type generation + contract drift:** AT RISK (unchanged) — No automated pipeline. F-004 notes new wide type cast in upload hook. Manual sync risk persists.

6. **CI security gates (Bandit/pip-audit/npm audit/policy):** PASS — pytest-cov added (F-007 fixed). Jest `--no-coverage` removed. 15-job pipeline intact with new mypy blocking gate.

7. **APScheduler safety under multi-worker:** PASS — No scheduler changes. Singleton pattern unchanged.

8. **Next.js CSP nonce + dynamic rendering:** PASS — `proxy.ts` unchanged. Per-request nonce intact.

## 3) Findings Table (Core)

### F-001: Detection Keywords Hardcoded in StreamingAuditor — Bypass classification_rules.py
- **Severity**: P2
- **Category**: Architecture / Consistency
- **Evidence**:
  - `backend/audit_engine.py` — `detect_related_party_accounts()` defines `_RELATED_PARTY_KEYWORDS` as class attribute tuples: ("related party", 0.95), ("affiliate", 0.90), ("officer", 0.85), etc.
  - `detect_intercompany_imbalances()` defines `_INTERCOMPANY_KEYWORDS` as class attribute: ("intercompany", 0.95), ("ic receivable", 0.90), etc.
  - `detect_equity_signals()` uses inline string containment checks for "retained earnings", "accumulated deficit", "dividend", "treasury" — no weighting.
  - All other keyword-driven detection (suspense, lead sheet mapping, rounding exclusions) uses `classification_rules.py` tuples with `(keyword, weight, is_phrase)` format.
  - The 3 new detectors introduced in Sprint 526 bypassed this established pattern.
- **Impact**: Keyword maintenance now split across 2 locations. Future classification updates may miss the hardcoded lists. Weight calibration inconsistent (new detectors use 2-tuples, existing rules use 3-tuples).
- **Recommendation**: Move `_RELATED_PARTY_KEYWORDS`, `_INTERCOMPANY_KEYWORDS`, and equity signal keywords to `classification_rules.py` with `(keyword, weight, is_phrase)` format. Import in `StreamingAuditor`.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Centralize detection keywords in classification_rules.py
  Files in scope: backend/classification_rules.py, backend/audit_engine.py
  Approach: Define RELATED_PARTY_KEYWORDS, INTERCOMPANY_KEYWORDS, EQUITY_SIGNAL_KEYWORDS in classification_rules.py using existing (keyword, weight, is_phrase) tuple format. Import in StreamingAuditor and replace class-attribute/inline definitions.
  Acceptance criteria:
  - No keyword definitions in audit_engine.py (only imports)
  - All 3 keyword lists in classification_rules.py
  - pytest tests/test_audit_anomalies.py passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-002: Concentration Benchmark Thresholds Inconsistent with Imported Constants
- **Severity**: P2
- **Category**: Architecture / Correctness
- **Evidence**:
  - `backend/shared/tb_diagnostic_constants.py` — `CONCENTRATION_BENCHMARKS` dict hardcodes "30%" (revenue), "40%" (expense), "100%" (intercompany) as inline text strings.
  - `backend/classification_rules.py` defines `CONCENTRATION_THRESHOLD_HIGH` and `CONCENTRATION_THRESHOLD_MEDIUM` as numeric constants.
  - The hardcoded percentages in `CONCENTRATION_BENCHMARKS` do not reference the imported constants, creating two sources of truth.
- **Impact**: If concentration thresholds change in `classification_rules.py`, the benchmark descriptions in `tb_diagnostic_constants.py` would display stale percentages in reports.
- **Recommendation**: Generate benchmark text dynamically using the imported threshold constants, or at minimum add a comment linking to the canonical source.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Align concentration benchmark text with imported threshold constants
  Files in scope: backend/shared/tb_diagnostic_constants.py
  Approach: Import CONCENTRATION_THRESHOLD_HIGH, CONCENTRATION_THRESHOLD_MEDIUM from classification_rules. Use f-strings in CONCENTRATION_BENCHMARKS to reference these constants (e.g., f"Single-account revenue concentration exceeding {CONCENTRATION_THRESHOLD_HIGH*100:.0f}%...").
  Acceptance criteria:
  - CONCENTRATION_BENCHMARKS uses imported thresholds
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Performance Alchemist (B): "Benchmark text is descriptive prose, not code — coupling to constants is overengineering."
- **Chair Rationale**: P2 sustained. Two sources of truth for the same numeric threshold is a correctness risk, even if one is prose.

---

### F-003: `_standard_table_style()` Still Duplicated in 3 Diagnostic Memos (Carryover)
- **Severity**: P2
- **Category**: Architecture / Code Duplication
- **Evidence**:
  - `backend/accrual_completeness_memo.py` (lines 44-66): `_standard_table_style(courier_cols=None, right_align_from=99)`
  - `backend/expense_category_memo.py` (lines 46+): `_standard_table_style(*, right_align_from=1, courier_cols=None)` — different parameter order and defaults
  - `backend/population_profile_memo.py` (lines 46+): Identical to expense_category_memo.py
  - Sprint 516 fixed `_roman()` and `_fmt_currency()` duplication but missed `_standard_table_style()` in diagnostic memos.
  - Canonical `ledger_table_style()` exists in `shared/report_styles.py:69`.
- **Impact**: ~70 lines of duplicated code. Signature inconsistency (right_align_from defaults differ: 99 vs 1) means behavior diverges silently.
- **Recommendation**: Extract to `shared/memo_base.py` with compatible signature. Standardize default `right_align_from=1` and use keyword-only arguments.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Eliminate remaining _standard_table_style() duplication
  Files in scope: backend/accrual_completeness_memo.py, backend/expense_category_memo.py, backend/population_profile_memo.py, backend/shared/memo_base.py
  Approach: Add standard_table_style(*, right_align_from: int = 1, courier_cols: list[int] | None = None) to shared/memo_base.py. Replace local definitions in all 3 diagnostic memos with imports. Reconcile default right_align_from (accrual used 99; normalize to explicit per-call).
  Acceptance criteria:
  - No local _standard_table_style() in diagnostic memos
  - All imports reference shared/memo_base
  - pytest passes for affected test files
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-004: Wide Type Intersection Cast in useTrialBalanceUpload — Missing `AuditResultResponse` Type
- **Severity**: P2
- **Category**: Types / Contracts
- **Evidence**:
  - `frontend/src/hooks/useTrialBalanceUpload.ts:201` — `const data = result.data as AuditResult & { status?: string; column_detection?: ColumnDetectionInfo & { requires_mapping?: boolean } }`
  - Backend response includes `status` and `column_detection` fields not in the `AuditResult` frontend type.
  - This inline intersection type is not reusable and obscures the actual API contract.
- **Impact**: Type safety weakened at the primary data boundary. If backend response shape changes, the inline cast silently becomes incorrect.
- **Recommendation**: Extract `AuditResultResponse` type in `types/diagnostic.ts` that extends `AuditResult` with the additional backend-specific fields.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Create explicit AuditResultResponse type
  Files in scope: frontend/src/types/diagnostic.ts (or appropriate type file), frontend/src/hooks/useTrialBalanceUpload.ts
  Approach: Define AuditResultResponse extending AuditResult with { status?: string; column_detection?: ColumnDetectionInfo & { requires_mapping?: boolean } }. Replace inline cast.
  Acceptance criteria:
  - No inline type intersections for API responses
  - npm run build passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Type & Contract Purist (H)
- **Supporting Agents**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Performance Alchemist (B): "P3 — inline cast works and is local."
- **Chair Rationale**: P2 sustained. API response types must be explicit for contract drift detection.

---

### F-005: No Unit Tests for uploadTransport.ts Error Scenarios
- **Severity**: P2
- **Category**: Verification / Critical Path Coverage
- **Evidence**:
  - `frontend/src/utils/uploadTransport.ts` (79 lines) — shared upload primitive used by 4+ consumers (useTrialBalanceUpload, useAuditUpload, BatchUploadContext, usePreflight).
  - No dedicated test file (`__tests__/uploadTransport.test.ts`) exists.
  - Error handling for 401, 403 (EMAIL_NOT_VERIFIED), network failure, and JSON parse failure is untested directly.
  - Tested only indirectly via composite hook tests.
- **Impact**: A regression in auth header injection, CSRF token handling, or error code mapping would propagate to all 4 upload consumers without direct test detection.
- **Recommendation**: Add dedicated unit test file with mock fetch covering: success, 401, 403 + EMAIL_NOT_VERIFIED, 500, network failure, JSON parse failure.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P0/P1]
  Goal: Add unit tests for uploadTransport.ts
  Files in scope: frontend/src/__tests__/uploadTransport.test.ts (new)
  Approach: Mock global.fetch. Test 6 scenarios: (1) successful upload returns data, (2) 401 returns auth error, (3) 403 with EMAIL_NOT_VERIFIED code, (4) 403 generic, (5) 500 server error, (6) network failure (fetch throws). Verify Authorization and X-CSRF-Token headers are injected.
  Acceptance criteria:
  - 6+ test methods covering all error branches
  - npm test passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Verification Marshal (I)
- **Supporting Agents**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 7/9 Approve P2 | Dissent: Systems Architect (A): "Indirect coverage via integration tests is sufficient." Modernity Curator (E): "P3."
- **Chair Rationale**: P2 sustained. Transport layer is shared infrastructure — direct coverage required for regression safety.

---

### F-006: Post-Processor Result Structure Assumptions — No Defensive Checks
- **Severity**: P2
- **Category**: Correctness / Defense-in-Depth
- **Evidence**:
  - `backend/shared/tb_post_processor.py` — `apply_lead_sheet_grouping()` assumes `result["abnormal_balances"]` exists without validation.
  - `apply_currency_conversion()` assumes `result["accounts"]` exists without validation.
  - Both functions mutate the result dict in place. If called with a partial or malformed result (e.g., from an early error exit in `audit_trial_balance_streaming()`), they would raise `KeyError`.
- **Impact**: Unhandled `KeyError` would propagate as 500 to the client instead of a graceful degradation. Risk elevated because `execute_file_tool()` now routes all tool endpoints through a shared scaffold.
- **Recommendation**: Add `if "abnormal_balances" not in result: return` guard at top of each function. Log a warning for missing keys.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P2/P3]
  Goal: Add defensive key checks to post-processors
  Files in scope: backend/shared/tb_post_processor.py
  Approach: Add early-return guard at top of each function: if required keys missing, log warning and return without mutation. Example: if "abnormal_balances" not in result: logger.warning("Skipping lead sheet grouping: missing abnormal_balances"); return
  Acceptance criteria:
  - Functions handle missing keys gracefully
  - No KeyError possible from post-processor calls
  - pytest passes
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-007: Dead Attributes `provided_account_types` / `provided_account_names` in StreamingAuditor
- **Severity**: P3
- **Category**: Code Quality / Dead Code
- **Evidence**:
  - `backend/audit_engine.py` — StreamingAuditor `__init__` defines:
    - `self.account_type_col: Optional[str] = None`
    - `self.account_name_col: Optional[str] = None`
    - `self.provided_account_types: dict[str, str] = {}`
    - `self.provided_account_names: dict[str, str] = {}`
  - These attributes are initialized but never populated or read in any visible code path.
  - Column detector now outputs `account_type_column` and `account_name_column` fields, but the auditor does not consume them.
- **Impact**: Dead code suggests incomplete feature (column mapping → auditor integration). No functional risk, but creates confusion for maintainers.
- **Recommendation**: Either wire these attributes to the column detection pipeline or remove them. If planned for a future sprint, add `# TODO(Sprint N):` comments.
- **Primary Agent**: Systems Architect (A)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-008: `unknown[]` Cast for abnormal_balances in BatchUploadContext
- **Severity**: P3
- **Category**: Types / Contracts
- **Evidence**:
  - `frontend/src/contexts/BatchUploadContext.tsx:275-276` — `const abnormalBalances = result.abnormal_balances as unknown[] | undefined`
  - No compile-time validation that API response contains `abnormal_balances` field or its shape.
  - Pre-existing issue (same assumption existed before refactor), but now surfaced by the `uploadTransport` migration.
- **Impact**: Low — field exists in all audit responses and is consumed only for length check. But `unknown[]` bypasses type checking.
- **Recommendation**: Type `result.data as AuditResult` at the response boundary instead of casting individual fields.
- **Primary Agent**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-009: 5 Memo Generators Still Lack Dedicated Test Files (Carryover — F-018)
- **Severity**: P3
- **Category**: Verification / Coverage Gap
- **Evidence**:
  - Missing test files (deferred from Sprint 516):
    - `test_ap_testing_memo.py`
    - `test_je_testing_memo.py`
    - `test_payroll_testing_memo.py`
    - `test_preflight_memo.py`
    - `test_engagement_dashboard_memo.py`
  - 11 other memo generators have dedicated test files. These 5 remain covered only by smoke tests.
- **Impact**: Regressions in enriched sections (Sprints 489–500) not caught at unit level.
- **Recommendation**: Create dedicated test files following `test_sampling_memo.py` pattern.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-010: Duplicate Null-Checking Logic in preflight_engine.py
- **Severity**: P3
- **Category**: Code Quality / DRY
- **Evidence**:
  - `backend/preflight_engine.py` — `_coerce_to_float()` and `_is_cell_empty()` both independently check for `None`, empty string, and `NaN` (via `val != val` pattern).
  - Logic overlap: `_coerce_to_float()` could call `_is_cell_empty()` for its guard checks.
- **Impact**: Minor maintenance burden. If NaN-check logic changes, both functions must be updated.
- **Recommendation**: Have `_coerce_to_float()` call `_is_cell_empty()` for its initial guard, then proceed with conversion.
- **Primary Agent**: Modernity & Consistency Curator (E)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-011: `loadFromLocalStorage()` Function Name Stale After sessionStorage Migration
- **Severity**: P3
- **Category**: Code Quality / Naming
- **Evidence**:
  - `frontend/src/hooks/useActivityHistory.ts:86` — Function named `loadFromLocalStorage()` but implementation uses `sessionStorage.getItem()`.
  - Function was renamed in implementation (F-011 fix, Sprint 516) but the function name was not updated.
- **Impact**: Cosmetic. Implementation is correct. Name creates confusion for maintainers.
- **Recommendation**: Rename to `loadFromSessionStorage()`.
- **Primary Agent**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-012: String-Based Risk Tiers in tb_diagnostic_constants — Should Use Enum
- **Severity**: P3
- **Category**: Types / Consistency
- **Evidence**:
  - `backend/shared/tb_diagnostic_constants.py` — `get_risk_tier()` returns plain strings: "low", "moderate", "elevated", "high".
  - `backend/shared/testing_enums.py` defines `RiskTier` enum with the same 4 values for testing tools.
  - TB Diagnostics risk tiers are string-based while testing tool risk tiers are enum-based — inconsistent type representation.
- **Impact**: No runtime risk (strings match). But prevents IDE autocomplete and compile-time checks for TB diagnostic risk tiers.
- **Recommendation**: Import and return `RiskTier` enum from `testing_enums.py` in `get_risk_tier()`.
- **Primary Agent**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 8/9 Approve P3 | Dissent: Performance Alchemist (B): "Informational — strings serialize cleanly."

---

### F-013: OpenAPI/TS Contract Drift Detection Still Deferred (Carryover — F-020)
- **Severity**: P3
- **Category**: Types / Contracts
- **Evidence**:
  - No automated OpenAPI→TS pipeline exists. 16 commits in this cycle changed backend schemas and frontend types independently.
  - Sprint 516 commit explicitly deferred this to Sprint 517+.
  - F-004 (wide type cast) is a direct symptom of this systemic gap.
- **Impact**: Potential runtime type mismatches. Currently mitigated by manual sync and tests.
- **Recommendation**: Add CI drift detection job (compare OpenAPI spec output against frontend type definitions).
- **Primary Agent**: Type & Contract Purist (H)
- **Supporting Agents**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 7/9 Approve P3 | Dissent: Modernity Curator (E): "P2 — F-004 proves the risk is materializing." Performance Alchemist (B): "Manual sync works."

---

### F-014: StreamingAuditor Class Size — 28+ Methods Across 6 Functional Domains
- **Severity**: Informational
- **Category**: Architecture / Monitoring
- **Evidence**:
  - `backend/audit_engine.py` — `StreamingAuditor` class spans ~1,091 lines with 28+ methods across:
    1. Core processing (process_chunk, _discover_columns)
    2. Balance validation (get_balance_result, detect_suspense_accounts)
    3. Anomaly detection (6 detectors: concentration, rounding, related party, intercompany, equity, revenue/expense)
    4. Classification (5 methods)
    5. State queries (4 methods)
    6. Lifecycle (clear)
  - Sprint 526 added 3 new detection methods, growing the class from ~25 to 28+ methods.
- **Impact**: No immediate issue — methods are cohesive around trial balance streaming. But continued growth risks Single Responsibility Principle violation.
- **Recommendation**: Monitor. If class exceeds ~35 methods, consider extracting anomaly detectors into an `AnomalyDetectorRegistry` composition pattern.
- **Primary Agent**: Systems Architect (A)
- **Vote** (9 members; quorum=6): 9/9 Approve Informational

---

### F-015: Prior DEC Findings — Remediation Status
- **Severity**: Informational
- **Category**: Process / Verification
- **Evidence**:

  | Prior Finding | Status |
  |---------------|--------|
  | F-001: Memo utility duplication | **PARTIALLY FIXED** → F-003 (_standard_table_style remains) |
  | F-002: Export sharing auth | **FIXED** |
  | F-003: Skip navigation link | **FIXED** |
  | F-004: Command palette ARIA | **FIXED** |
  | F-005: Nav aria-labels | **FIXED** |
  | F-006: Stripe webhook test | **FIXED** |
  | F-007: CI coverage measurement | **FIXED** |
  | F-008: HTTP RED metrics | **FIXED** |
  | F-009: Sentry breadcrumb filtering | **FIXED** |
  | F-010: .env.example cleanup | **FIXED** |
  | F-011: localStorage→sessionStorage | **FIXED** |
  | F-012: sanitize_exception context | **FIXED** |
  | F-013: TestingRiskTier 'critical' | **FIXED** |
  | F-014: Anomaly summary reference | **FIXED** |
  | F-015: ProfileDropdown ARIA + version | **FIXED** |
  | F-016: UsageMeter amber colors | **FIXED** |
  | F-017: Structured access log | **FIXED** |
  | F-018: 5 memo test files | **DEFERRED** → F-009 (carryover) |
  | F-019: Sprint 481 documentation | **FIXED** |
  | F-020: OpenAPI drift CI | **DEFERRED** → F-013 (carryover) |
  | F-021: Prior remediation status | **SUPERSEDED** (this finding) |

  **Remediation Rate**: 18/21 fixed (86%), 1 partially fixed, 2 deferred.

- **Primary Agent**: Verification Marshal (I)

---

## 4) Council Tensions & Resolution

### Tension 1: Detection Keywords — classification_rules.py vs. Class Attributes
- **Systems Architect (A)** and **Modernity Curator (E)** insist all keyword-driven detection must use `classification_rules.py` for consistency.
- **Performance Alchemist (B)** argues class attributes are acceptable for domain-specific detection methods that have different weighting semantics (2-tuples vs 3-tuples).
- **Resolution**: P2 sustained (9/0 vote). The existing pattern is established and documented. New detectors should follow it. The 2-tuple vs 3-tuple difference is resolvable by adding `is_phrase=True` to the new keyword lists.

### Tension 2: uploadTransport Test Coverage — P2 vs P3
- **Verification Marshal (I)** wants P2: "Shared infrastructure with 4 consumers and zero direct test coverage."
- **Systems Architect (A)** supports P3: "Indirect coverage via integration tests covers the happy path."
- **Resolution**: P2 sustained (7/9 vote). Transport layer error handling (401, 403 codes, network failure) is critical path — indirect tests don't exercise all branches.

### Tension 3: Concentration Benchmark Prose — Engineering vs. Documentation
- **Performance Alchemist (B)** argues benchmark descriptions are documentation prose, not code, and coupling them to constants is overengineering.
- **Systems Architect (A)** insists two sources of truth for the same threshold is a correctness risk regardless of medium.
- **Resolution**: P2 sustained (8/9 vote). The numbers in prose must match the numbers in code.

## 5) Discovered Standards — Proposed Codification

- **Existing standards verified**:
  - `as const` convention: **100% compliant**
  - Sprint commit convention: **100% compliant** for Sprints 516–526
  - Post-sprint checklist: **100% followed**
  - Auth classification: **100% compliant** (F-002 fixed)
  - Theme palette: **100% compliant** (F-016 fixed)
  - ARIA navigation landmarks: **100% compliant** (F-003/F-004/F-005 fixed)

- **Proposed standard codifications**:
  - **Detection keyword location rule**: All keyword-driven detection MUST define keywords in `classification_rules.py`. No class attributes or inline definitions. Format: `(keyword, weight, is_phrase)` tuples.
  - **Post-processor defensive check rule**: Functions that mutate result dicts MUST validate required keys before access. Guard pattern: `if key not in result: log + return`.
  - **API response type rule**: Frontend code receiving API responses MUST type the response at the boundary using a named type (no inline `as` intersection casts).
  - **Transport layer test rule**: Shared HTTP primitives (apiClient, uploadTransport) MUST have dedicated unit tests covering all error branches.

- **Proposed enforcement mechanisms**:
  - Grep guard in CI: reject `_KEYWORDS` patterns in `audit_engine.py`
  - ESLint rule: flag `as ... & {` intersection casts in hooks
  - Test coverage gate: require test files for files in `utils/` directory

## 6) Agent Coverage Report

- **Systems Architect (A) — "The Stalwart"**:
  - Touched areas: engine_framework.py, audit_engine.py, routes/audit.py, shared/ modules, classification pipeline, post-processors
  - Top 3 findings contributed: F-001 (primary), F-002 (primary), F-003 (primary), F-006 (primary)
  - Non-obvious risk: `execute_file_tool()` scaffold creates a single failure point for all tool endpoints. If scaffold logic has a bug, all tools break simultaneously.

- **Performance & Cost Alchemist (B) — "The Optimizer"**:
  - Touched areas: HTTP metrics middleware, engine hot paths, pandas operations, memo generation
  - Top 3 findings contributed: F-001 (dissent), F-002 (dissent), F-014 (supporting)
  - Non-obvious risk: `compute_tb_risk_score()` caps at 100 via `min(score, 100)` — scores above 100 are silently truncated. If 3+ high-severity anomalies co-occur, the score saturates and loses discriminatory power.

- **DX & Accessibility Lead (C) — "The Diplomat"**:
  - Touched areas: All navigation components, command palette, profile dropdown, new diagnostic components, toolbar
  - Top 3 findings contributed: F-011 (primary), F-004 (supporting)
  - Non-obvious risk: `EngagementDetailsPanel` uses local `useState` for all metadata fields — if the page remounts (route change), all engagement metadata is lost. Consider lifting to context or URL state for persistence.

- **Security & Privacy Lead (D) — "Digital Fortress"**:
  - Touched areas: uploadTransport.ts, Sentry configs, auth flows, CSRF lifecycle, export sharing
  - Top 3 findings contributed: F-005 (supporting), F-006 (supporting)
  - Non-obvious risk: `uploadTransport.ts` reads CSRF token from a module-level variable. If the token expires mid-session and the refresh mechanism fails silently, all uploads fail with 403 until page reload.

- **Modernity & Consistency Curator (E) — "The Trendsetter"**:
  - Touched areas: Hook decomposition patterns, code duplication scans, naming conventions
  - Top 3 findings contributed: F-003 (supporting), F-010 (primary), F-013 (dissent on P3)
  - Non-obvious risk: Trial balance hook decomposition (4 hooks + 1 composite) is the most granular decomposition in the codebase. If other tool pages follow this pattern, the hooks directory will grow significantly. Consider a `hooks/trial-balance/` subdirectory convention.

- **Observability & Incident Readiness (F) — "The Detective"**:
  - Touched areas: http_metrics_middleware.py, logging_config.py, Sentry configs, parser_metrics.py
  - Top 3 findings contributed: F-006 (supporting)
  - Non-obvious risk: HTTP metrics histogram uses 11 buckets (0.005s–30s). If audit_engine processing time exceeds 30s (possible for large files), it falls into the `+Inf` bucket and becomes invisible to latency percentile dashboards.

- **Data Governance & Zero-Storage Warden (G) — "The Auditor"**:
  - Touched areas: All new persistence paths, sessionStorage, checkout_orchestrator, usage_service, post-processors
  - Top 3 findings contributed: Zero-Storage checklist verification
  - Non-obvious risk: `checkout_orchestrator.py` stores DPA acceptance timestamp (`dpa_accepted_at`) — this is PII-adjacent (consent record). If retention policy changes, this field needs explicit TTL or audit trail.

- **Type & Contract Purist (H) — "The Pedant"**:
  - Touched areas: Frontend type definitions, API response shapes, risk tier enums, TestingRiskTier
  - Top 3 findings contributed: F-004 (primary), F-008 (primary), F-012 (primary), F-013 (primary)
  - Non-obvious risk: `AuditEngineBase.run_pipeline()` returns `Any` — all engine subclass results bypass type checking at the framework level. Consider generic return type `T` on the base class.

- **Verification Marshal (I) — "The Skeptic"**:
  - Touched areas: Test files, CI pipeline, coverage measurement, memo test gap analysis
  - Top 3 findings contributed: F-005 (primary), F-009 (primary)
  - Non-obvious risk: `pytest-cov` added without `--cov-fail-under` threshold. Coverage can still regress silently — the gate measures but does not enforce. Recommend establishing a baseline threshold (e.g., 60%) in the next sprint.
