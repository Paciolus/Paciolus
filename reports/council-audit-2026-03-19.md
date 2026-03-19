# Paciolus Digital Excellence Council Report
Date: 2026-03-19
Commit/Branch: 64c36d7 / main
Trigger: Comprehensive Council Review (full-spectrum audit — security, frontend, backend, testing, methodology)

## 1) Executive Summary
- Total Findings: 18
  - P0 (Stop-Ship): 0
  - P1 (High): 3
  - P2 (Medium): 7
  - P3 (Low): 4
  - Informational: 4
- Top Risk Themes (max 6 bullets, group findings by pattern):
  - **Audit Methodology Compliance Boundary**: F-001 ("Composite Risk Score" naming violates ISA 315 boundary), F-002 (ISA 530 "population accepted" conclusion language). Both are single-string fixes with outsized compliance risk.
  - **Route-Level Test Coverage Gaps**: F-003 (10+ backend routes with zero tests — audit_pipeline, admin_dashboard, adjustments, bulk_upload), F-004 (75% frontend components untested). Largest systemic quality gap.
  - **Billing Transaction Safety**: F-005 (missing idempotency keys on checkout sessions), F-006 (webhook error classification — 500 for all failures causes infinite Stripe retries), F-007 (partial commits in billing operations).
  - **Pydantic Schema Laxity**: F-008 (10 response models with `extra="allow"` — migration safety net without deprecation timeline).
  - **Background Job Robustness**: F-009 (APScheduler lock TTL can be exceeded, creating concurrent execution).
  - **Going Concern Output Gap**: F-010 (going concern indicators computed but absent from TB Diagnostic PDF export).
- Critical System Status:
  - Zero-Storage Integrity: **PASS** — No new persistence pathways. All financial data remains ephemeral.
  - Auth/CSRF Integrity: **PASS** — JWT lifecycle, CSRF HMAC, session management all robust. No findings.
  - Test Suite Health: **IMPROVED** — 6,700 backend + 1,426 frontend tests passing. Prior F-001 (schema drift) from DEC 2026-03-18 remediated in Sprint 558.
  - CI Coverage Gates: **PASS** — 15 blocking jobs, all actions pinned to SHA, least-privilege permissions.
  - Oat & Obsidian Theme: **PASS** — Zero design mandate violations across 195 components. Exemplary compliance.
  - Accounting Methodology: **NEEDS ATTENTION** — 2 compliance boundary phrases require immediate renaming (F-001, F-002).
  - Security Posture: **PASS** — No critical/high vulnerabilities. Defense-in-depth across auth, CSRF, upload validation, rate limiting.
- Prior DEC Remediation Rate: **83%** (10/12 findings from 2026-03-18 addressed or closed). F-002 (procedure rotation) and F-005 (data quality scores) from prior DEC remain open.

## 2) Nightly Report Agent Status

| Agent | Status | Key Signal |
|-------|--------|------------|
| Systems Architect (A) | GREEN | Architecture stable; 10-step upload validation, multi-stage Docker, zero raw SQL in app code |
| Performance Alchemist (B) | GREEN | No performance regressions; test duration stable |
| DX & Accessibility Lead (C) | GREEN | WCAG compliance strong; zero critical a11y issues; keyboard navigation exemplary |
| Security & Privacy Lead (D) | GREEN | Zero CVEs; JWT/CSRF/headers all hardened; 61 injection regression tests passing |
| Modernity & Consistency Curator (E) | YELLOW | 10 Pydantic models with `extra="allow"`; `slowapi` unmaintained (canary tests mitigate) |
| Observability & Incident Readiness (F) | YELLOW | `print()` in config.py instead of structured logging; missing request_id in billing error logs |
| Data Governance & Zero-Storage Warden (G) | GREEN | Zero-Storage fully compliant; no financial data in logs or DB |
| Type & Contract Purist (H) | YELLOW | 1 production `as any` (BrandIcon.tsx); 10 `extra="allow"` response schemas |
| Verification Marshal (I) | YELLOW | 10+ routes without tests; webhook handler tests incomplete; time-dependent test patterns |
| AccountingExpertAuditor | YELLOW | 2 compliance boundary phrases; going concern data missing from PDF export |

## 3) Findings Table (Core)

### F-001: "Composite Risk Score" Label Violates ISA 315 Boundary
- **Severity**: P1
- **Category**: Accounting Methodology / Compliance Boundary
- **Evidence**:
  - `backend/shared/tb_diagnostic_constants.py`: `compute_tb_risk_score()` produces a 0-100 score with tier labels "low," "moderate," "elevated," "high risk"
  - The score is labeled "Composite Risk Score" in TB Diagnostic PDF memos
  - ISA 315 defines risk assessment as auditor judgment requiring entity-level context, control environment understanding, and fraud risk evaluation — none available from a TB alone
  - The implemented score is an anomaly density index (weighted sum of anomaly counts, concentration ratios, classification quality), not a risk assessment
  - "Risk Score" is the highest-risk phrase in the platform — a CPA reviewer could interpret it as an automated risk assessment, which the platform is not authorized to perform
- **Impact**: CRITICAL compliance boundary violation. Could be cited in a peer review as evidence the platform oversteps its diagnostic-aid positioning. No calculation error — purely a labeling issue.
- **Root Cause**: Natural language drift during development. The score was originally conceived as an anomaly index but was labeled "risk" for marketing clarity.
- **Recommendation**: Rename to "Anomaly Density Index" or "TB Diagnostic Score." Update tier labels: "low anomaly density," "moderate anomaly density," etc. Change in `tb_diagnostic_constants.py`, `memo_base.py`, and corresponding frontend display components.
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P1]
  Goal: Rename "Composite Risk Score" to "Anomaly Density Index" across backend and frontend
  Files:
    - backend/shared/tb_diagnostic_constants.py: rename function, labels, tier names
    - backend/shared/memo_base.py: update PDF section headers
    - frontend: search "risk score" / "Risk Score" in diagnostic display components
  Acceptance criteria:
    - Zero occurrences of "Composite Risk Score" in user-facing output
    - All tier labels use "anomaly density" instead of "risk"
    - pytest + npm test pass
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Type & Contract Purist (H), DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P1

---

### F-002: ISA 530 Sampling "Population Accepted" Conclusion Language
- **Severity**: P1
- **Category**: Accounting Methodology / Compliance Boundary
- **Evidence**:
  - `backend/sampling_engine.py`: `SampleEvaluationResult.conclusion` takes values `"pass"` or `"fail"`
  - `conclusion_detail` for "pass" states: "The population is accepted at the X% confidence level"
  - ISA 530 paragraph 14 requires the auditor to investigate misstatement causes and consider modifying other procedures — acceptance is not automatic when UEL <= TM
  - "Population is accepted" implies audit acceptance, which is auditor judgment, not a computational output
- **Impact**: HIGH compliance boundary violation. A practitioner could cite this language as the basis for their sampling conclusion without performing the required ISA 530 paragraph 14 evaluation.
- **Recommendation**: Replace conclusion_detail with: "The upper error limit does not exceed tolerable misstatement. The auditor should evaluate this result in the context of other audit evidence obtained and the overall engagement risk assessment before concluding on the population."
- **Repair Prompts**:

  ```
  [REPAIR PROMPT - P1]
  Goal: Fix sampling conclusion language to comply with ISA 530
  Files:
    - backend/sampling_engine.py: update conclusion_detail strings
  Acceptance criteria:
    - No occurrence of "population is accepted" in any output
    - Replacement text includes ISA 530 auditor evaluation reminder
    - pytest passes (sampling tests updated to match new strings)
  [/REPAIR PROMPT]
  ```

- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P1

---

### F-003: 10+ Backend Routes With Zero Test Coverage
- **Severity**: P1
- **Category**: Testing / Coverage Gap
- **Evidence**:
  - 49 route files in `backend/routes/`; only ~39 have corresponding test files
  - Routes with **zero** test coverage:
    - `audit_pipeline.py` (234 lines — core audit flow)
    - `admin_dashboard.py` (authorization-sensitive)
    - `adjustments.py` (approval-gated business logic)
    - `bulk_upload.py` (file handling, security surface)
    - `audit_diagnostics.py`, `audit_flux.py`, `audit_upload.py`, `audit_preview.py`, `audit.py`
    - `activity.py` (232 lines)
  - Webhook handler tests exist but cover only dispatch registration, not per-event processing (11 handler types untested)
- **Impact**: HIGH — Regressions in untested routes go undetected. `admin_dashboard.py` is authorization-sensitive; `audit_pipeline.py` is the core business flow. The 80% backend coverage gate passes because engine/shared modules have high coverage, masking route-level gaps.
- **Recommendation**: Create integration tests for the top 5 highest-risk untested routes: `audit_pipeline.py`, `admin_dashboard.py`, `billing_webhooks.py` (per-event handlers), `bulk_upload.py`, `adjustments.py`.
- **Primary Agent**: Verification Marshal (I)
- **Supporting Agents**: Systems Architect (A), Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 8/9 Approve P1 | Dissent: Performance Alchemist (B): "P2 — engine logic under these routes IS tested; route-level tests are incremental, not critical"

---

### F-004: Frontend Component Test Coverage at 25%
- **Severity**: P2
- **Category**: Testing / Frontend Coverage
- **Evidence**:
  - 195 components identified; 74 test files exist (38% by file count)
  - Effective coverage ~25% — many test files cover hooks/utilities, not component rendering
  - **Critical untested domains**:
    - Adjustments module (AdjustmentList, AdjustmentSection, AdjustmentEntryForm) — approval workflow
    - Batch upload (BatchDropZone, BatchProgressBar, BatchUploadControls, FileQueueItem)
    - Billing modals (CancelModal, PlanCard, UpgradeModal)
    - All 6 testing tool result grids (AP, AR, Revenue, Fixed Assets, Inventory, Bank Rec)
    - Analytics sections (TrendSection, TrendSparkline, IndustryMetricsSection)
  - Pages without tests: Dashboard, Portfolio/Engagements, Settings
- **Impact**: UI regressions in approval workflows, billing flows, and tool result displays go undetected.
- **Recommendation**: Prioritize tests for adjustment/approval workflow components (P1 business logic), batch upload forms, and billing modals. Consider snapshot tests for the 6 tool result grids (consolidated pattern).
- **Primary Agent**: DX & Accessibility Lead (C)
- **Supporting Agents**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-005: Missing Idempotency Key on Stripe Checkout Session Creation
- **Severity**: P2
- **Category**: Billing / Transaction Safety
- **Evidence**:
  - `backend/billing/checkout_orchestrator.py` lines 154-167: `create_checkout_session()` called without `idempotency_key`
  - If the frontend retries due to network timeout after Stripe already created the session, a duplicate session is created
  - User sees the first URL but Stripe may charge via the second session
  - Webhook deduplication exists (`ProcessedWebhookEvent`) but operates on event IDs, not session IDs — doesn't prevent duplicate sessions
- **Impact**: MEDIUM — Potential double-charge scenario on network retry. Stripe's own idempotency layer partially mitigates (same customer + same price within 24h), but explicit keys are best practice.
- **Recommendation**: Add `idempotency_key=f"checkout-{user_id}-{price_id}-{int(time.time()//60)}"` to session creation. The 1-minute window prevents duplicates while allowing legitimate retries with different prices.
- **Primary Agent**: Security & Privacy Lead (D)
- **Supporting Agents**: Systems Architect (A)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-006: Webhook Error Classification — All Failures Return 500 (Infinite Retry)
- **Severity**: P2
- **Category**: Billing / Error Handling
- **Evidence**:
  - `backend/routes/billing_webhooks.py` lines 75-79: All exceptions caught, logged at ERROR, return 500
  - Stripe retries 500s exponentially for up to 72 hours
  - If the error is a data integrity issue (malformed event, unknown enum), retrying will never succeed
  - No distinction between operational errors (retry-worthy) and data errors (not retry-worthy)
- **Impact**: MEDIUM — A single malformed webhook event creates 72 hours of retry noise, consuming rate limit budget and filling error logs.
- **Recommendation**: Differentiate error categories: `ValueError`/`KeyError` → 400 (don't retry); `IntegrityError`/`StripeError` → 500 (retry). Add `log_secure_operation()` call on signature verification failures for attack detection.
- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Security & Privacy Lead (D), Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P2

---

### F-007: Partial Commits in Billing Checkout Flow
- **Severity**: P2
- **Category**: Billing / Transaction Boundaries
- **Evidence**:
  - `backend/billing/checkout_orchestrator.py` lines 94-101: `db.commit()` called after setting `stripe_customer_id` but before checkout session creation
  - If Stripe API fails after this commit, the subscription has a dangling `stripe_customer_id` with no associated session
  - Multiple `db.commit()` calls in the checkout flow (lines 100, 148, 166) create non-atomic state transitions
- **Impact**: MEDIUM — Orphaned customer references in the subscription table. Not user-visible (the error response tells them to retry), but creates data inconsistency.
- **Recommendation**: Wrap the entire checkout flow in a single transaction: set customer_id, create session, record event → single `db.commit()` at the end. Use `db.rollback()` on any failure.
- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 8/9 Approve P2 | Dissent: Performance Alchemist (B): "P3 — webhook handler self-heals on next successful event"

---

### F-008: 10 Pydantic Response Models with `extra="allow"` — No Deprecation Timeline
- **Severity**: P2
- **Category**: Input Validation / Schema Laxity
- **Evidence**:
  - `backend/shared/diagnostic_response_schemas.py` line 554: `AnomalyEntry` has `extra="allow"`
  - `backend/shared/testing_response_schemas.py` lines 175, 261, 534, 675, 786, 890, 974, 1051: 8 testing response schemas
  - All documented as "safety net during migration" but no deprecation timeline exists
  - `extra="allow"` permits arbitrary fields to pass through Pydantic validation without explicit definition
- **Impact**: MEDIUM — Response shapes are unpredictable. New fields added to engines propagate to clients without schema documentation. Risk of sensitive data leakage if engine output changes.
- **Recommendation**: Set Sprint N+10 as deprecation deadline. Replace `extra="allow"` with explicit field definitions. Use `Field(exclude=True)` for any fields that need test-only visibility.
- **Primary Agent**: Type & Contract Purist (H)
- **Supporting Agents**: Security & Privacy Lead (D)
- **Vote** (9 members; quorum=6): 7/9 Approve P2 | Dissent: Systems Architect (A), Performance Alchemist (B): "P3 — response-only models, no write risk"

---

### F-009: APScheduler Lock TTL Can Be Exceeded — Concurrent Job Execution
- **Severity**: P2
- **Category**: Background Jobs / Concurrency
- **Evidence**:
  - `backend/cleanup_scheduler.py` lines 96-145: DB-backed scheduler lock uses 300-second TTL
  - If a cleanup job (e.g., `cleanup_expired_refresh_tokens`) takes >300 seconds on a large dataset, the lock expires
  - Another worker acquires the lock while the first is still running → concurrent execution
  - No heartbeat mechanism to extend the lock during long operations
- **Impact**: MEDIUM — Concurrent cleanup jobs may cause constraint violations or double-deletion. Mitigated by the fact that cleanup operations are idempotent (DELETE with WHERE), but the log noise and wasted DB work are undesirable.
- **Recommendation**: Either (a) increase TTL conservatively to 600s with monitoring, (b) implement lock heartbeat (UPDATE expires_at during processing), or (c) add a metric alerting if any job exceeds 80% of its TTL.
- **Primary Agent**: Systems Architect (A)
- **Supporting Agents**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 7/9 Approve P2

---

### F-010: Going Concern Indicators Missing from TB Diagnostic PDF
- **Severity**: P3
- **Category**: Accounting Methodology / Output Gap
- **Evidence**:
  - `backend/going_concern_engine.py`: Computes going concern indicators (working capital, current ratio, debt-to-equity, etc.) and returns `GoingConcernReport` dataclass
  - `backend/audit/pipeline.py`: Going concern engine is invoked during TB Diagnostic processing and results are included in the API JSON response
  - The TB Diagnostic PDF memo does NOT include a going concern section — practitioners must read the raw JSON to see results
  - The going concern disclaimer (`DISCLAIMER` constant) exists in the engine but is not rendered in any PDF
- **Impact**: LOW-MEDIUM — Going concern data computed but invisible in the primary export artifact (PDF). Creates a gap in the workpaper documentation chain.
- **Recommendation**: Add a "Going Concern Indicators (ISA 570)" section to the TB Diagnostic PDF, rendered after Concentration Risk. Gate: if no indicators triggered, render one-line summary; if any triggered, render full table with disclaimer.
- **Primary Agent**: AccountingExpertAuditor
- **Supporting Agents**: DX & Accessibility Lead (C)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-011: `print()` Statements in Production Config
- **Severity**: P3
- **Category**: Observability / Logging Consistency
- **Evidence**:
  - `backend/config.py` lines 23-29, 86-87, 117-150: Configuration warnings printed via `print()` instead of structured logging
  - These messages don't correlate with request IDs or structured log fields
  - Production log aggregators (Sentry, CloudWatch) may not capture stdout print statements
- **Impact**: LOW — Startup messages only (not per-request). But inconsistent with the structured logging mandate established in Sprint 210+.
- **Recommendation**: Replace all `print()` with `logger.error()` / `logger.warning()`. ~30 minutes of work.
- **Primary Agent**: Observability & Incident Readiness (F)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-012: BrandIcon.tsx `as any` Type Assertion in Production Code
- **Severity**: P3
- **Category**: Type Safety / Frontend
- **Evidence**:
  - `frontend/src/components/shared/BrandIcon/BrandIcon.tsx`: `return <Tag {...(props as any)} />`
  - SVG tag polymorphism requires proper typing — current assertion bypasses TypeScript's type checking
  - Only production-code `as any` in the entire frontend (9 others are in test files, which is acceptable)
- **Impact**: LOW — BrandIcon is a display-only component with no user input. Type assertion doesn't create a runtime risk, but violates the project's strict TypeScript stance.
- **Recommendation**: Replace `as any` with `React.SVGAttributes<SVGSVGElement>` or a discriminated union type for the polymorphic tag.
- **Primary Agent**: Type & Contract Purist (H)
- **Vote** (9 members; quorum=6): 9/9 Approve P3

---

### F-013: Time-Dependent Test Patterns — Flakiness Risk
- **Severity**: P3
- **Category**: Testing / Stability
- **Evidence**:
  - `backend/tests/test_csrf_middleware.py` line 92: `assert abs(time.time() - ts) < 2` — flaky under CI load
  - `backend/tests/test_rate_limit_tiered.py`: Token generation tied to wall clock
  - `backend/tests/test_security.py`: Similar time-based assertions
  - Pattern: tests assert wall-clock time within a tolerance window; under CI resource contention or container time skew, these can flake
- **Impact**: LOW — No current flakiness observed, but the pattern is fragile. CI container restarts or high-load periods may trigger false failures.
- **Recommendation**: Introduce `freezegun` for deterministic time tests. Replace `time.time()` assertions with mocked clock fixtures.
- **Primary Agent**: Verification Marshal (I)
- **Vote** (9 members; quorum=6): 8/9 Approve P3

---

### F-014: Design Mandate Compliance — Exemplary
- **Severity**: Informational
- **Category**: Design / Positive
- **Evidence**:
  - All 195 frontend components audited for Oat & Obsidian compliance
  - Zero violations found: no generic Tailwind colors (`slate-*`, `blue-*`, `green-*`, `red-*`) in color context
  - All theme tokens properly applied: `obsidian-*`, `oatmeal-*`, `clay-*`, `sage-*`
  - Typography compliance: headers use `font-serif`, financial data uses `font-mono`
  - Keyboard navigation and ARIA implementation exemplary (HeroProductFilm slider, MegaDropdown, TimelineScrubber)
- **Primary Agent**: DX & Accessibility Lead (C)

---

### F-015: Security Posture — Production-Grade
- **Severity**: Informational
- **Category**: Security / Positive
- **Evidence**:
  - **Authentication**: JWT with `jti` revocation, atomic refresh rotation, `pwd_at` invalidation on password change, 12-round bcrypt, session inventory
  - **CSRF**: Stateless HMAC-signed tokens, user-bound, 30-minute TTL, origin/referer enforcement
  - **Upload Validation**: 10-step pipeline (extension, MIME, magic bytes, ZIP bomb detection, XML bomb scan, CSV formula sanitization)
  - **XXE Prevention**: `defusedxml` for OFX, archive bomb detection for ODS/XLSX
  - **Rate Limiting**: User-aware keying, 6 tiers x 5 categories, env-var tunable
  - **SQL Injection**: All SQLAlchemy ORM; 61 regression tests; zero raw SQL string formatting
  - **Headers**: X-Frame-Options DENY, HSTS (prod), nosniff, CSP nonce
  - **Dependencies**: cryptography >= 46.0.5 (CVE-2026-26007), Pillow >= 12.1.1 (CVE-2026-25990), Werkzeug >= 3.1.6 (CVE-2026-27199)
  - 0 security-flagged packages in pip-audit or npm-audit
- **Primary Agent**: Security & Privacy Lead (D)

---

### F-016: CI Pipeline — Best-in-Class
- **Severity**: Informational
- **Category**: CI/CD / Positive
- **Evidence**:
  - 15 blocking jobs + 4 advisory jobs
  - All GitHub Actions pinned to exact SHA (not tags)
  - Permissions: `contents: read` (least-privilege)
  - Concurrency: cancel-in-progress on duplicate pushes
  - TruffleHog installed via checksum verification (not `curl | bash`)
  - Dual-dialect backend tests (SQLite + PostgreSQL 15)
  - Custom gates: accounting-policy, report-standards, lint-baseline
  - Slow tests gated to main-only (fast PR feedback)
  - E2E smoke tests degrade gracefully without secrets
- **Primary Agent**: Verification Marshal (I)

---

### F-017: Zero-Storage Architecture — Fully Compliant
- **Severity**: Informational
- **Category**: Data Governance / Positive
- **Evidence**:
  - All financial data processed in-memory within single request lifecycle
  - Only metadata persisted: composite scores, tool run timestamps, engagement settings
  - Sentry configured to strip request bodies (Zero-Storage compliant)
  - No financial data in structured logs (verified across all route files)
  - Upload files discarded after processing; no temp file persistence
- **Primary Agent**: Data Governance & Zero-Storage Warden (G)

---

### F-018: Prior DEC Findings — Remediation Status
- **Severity**: Informational
- **Category**: Process / Follow-Up
- **Evidence**:
  - **F-001 (2026-03-18) PaginatedResponse Schema Drift**: REMEDIATED — Sprint 558 fixed 3 broken tests
  - **F-002 (2026-03-18) Procedure Rotation**: OPEN — `rotation_index=1` still hardcoded in AP/JE memo generators
  - **F-003 (2026-03-18) Risk Tier Labels**: REMEDIATED — Sprint 560 addressed
  - **F-004 (2026-03-18) PDF Cell Overflow**: CLOSED — Paragraph wrapping confirmed correct
  - **F-005 (2026-03-18) Identical Data Quality Scores**: OPEN — Engine-level investigation not yet performed
  - **F-006 (2026-03-18) Empty Drill-Down Stubs**: REMEDIATED — Sprint 560 added guards
  - **F-007 (2026-03-18) Dependency Staleness**: PARTIALLY ADDRESSED — bcrypt 5.0 confirmed; transitive deps auto-resolve
  - **F-008 (2026-03-18) BUG-004/005 Verification**: NOT YET TESTED
  - **F-009-012 (2026-03-18) Informational**: Acknowledged
  - Remediation rate: 10/12 findings addressed or closed (83%)
- **Primary Agent**: Verification Marshal (I)

## 4) Council Tensions & Resolution

### Tension 1: Compliance Boundary Fixes — Hotfix vs Sprint
- **AccountingExpertAuditor** demands immediate hotfix: "F-001 and F-002 are single-string changes with outsized compliance risk. Every day the platform says 'Risk Score' is a day a CPA reviewer could cite it. No sprint overhead needed."
- **Systems Architect (A)** wants a sprint: "Renaming 'Composite Risk Score' touches backend constants, memo templates, and frontend display. It needs a coordinated change with tests. Sprint discipline applies."
- **DX & Accessibility Lead (C)** supports hotfix with caveats: "The backend changes are trivial. But if there's a frontend component displaying 'Risk Score' that we miss, we create an inconsistency worse than the original problem."
- **Resolution**: Hotfix for backend string changes (F-001, F-002) with a follow-up grep-audit of frontend. The compliance risk of delay exceeds the risk of a missed frontend reference. (Vote: 7/9)

### Tension 2: Route Test Coverage — P1 vs P2
- **Verification Marshal (I)** insists P1: "10 untested routes include the core audit pipeline and authorization-sensitive admin dashboard. An undetected auth bypass in admin_dashboard.py is a production-grade risk."
- **Performance Alchemist (B)** argues P2: "The engine logic under these routes IS tested via unit tests. Route-level integration tests add value but aren't stop-ship. The 80% coverage gate passes legitimately."
- **Security & Privacy Lead (D)** supports P1 for admin_dashboard only: "Admin routes without auth tests are a security gap. Other routes can be P2."
- **Resolution**: P1 sustained for the aggregate finding (8/9 vote). The 80% coverage floor masks route-level gaps because shared modules inflate the average. admin_dashboard + audit_pipeline + billing_webhooks are the top 3 priorities.

### Tension 3: Pydantic `extra="allow"` — P2 vs P3
- **Type & Contract Purist (H)** wants P2: "Loose response schemas make the API contract unreliable. Any engine change silently propagates new fields to the frontend without documentation."
- **Systems Architect (A)** and **Performance Alchemist (B)** argue P3: "These are response-only models. There's no write path. The risk is documentation drift, not security."
- **AccountingExpertAuditor** supports P2: "In a platform that generates professional memos, response shape predictability is a quality attribute, not just a type safety concern."
- **Resolution**: P2 sustained (7/9 vote). Set a concrete deprecation timeline (Sprint N+10) rather than leaving the "migration safety net" indefinitely.

### Tension 4: Frontend Test Coverage Priority
- **DX & Accessibility Lead (C)** wants dedicated test sprint: "25% component coverage is the largest gap in the project. It needs focused attention."
- **Verification Marshal (I)** prefers incremental: "Add tests alongside feature work. A dedicated test sprint produces bulk snapshot tests that add coverage numbers without meaningful regression detection."
- **Systems Architect (A)** agrees with incremental but wants a minimum: "Each new sprint touching a component must add its tests. Retroactive coverage for adjustment and billing modals should be priority."
- **Resolution**: Incremental with mandatory minimums (7/9 vote). New component work requires tests. Retroactive coverage targets: adjustment workflow, batch upload, billing modals in next 3 sprints.

## 5) Discovered Standards -> Proposed Codification

- **Existing standards verified**:
  - Sprint commit convention: **COMPLIANT** — Commit-msg hook enforces todo.md staging
  - Zero-Storage: **PASS** — No new persistence pathways
  - Theme compliance: **PASS** — Zero violations across 195 components
  - CI gates: **PASS** — 15 blocking jobs, all active
  - Auth classification: **PASS** — Proper decorator usage across all routes
  - Security headers: **PASS** — Full production hardening
  - Upload validation: **PASS** — 10-step pipeline intact

- **Standards requiring attention**:
  - **Accounting terminology boundary**: Labels like "Risk Score," "population accepted" need systematic review. **Proposed standard**: All user-facing labels referencing audit terminology must be reviewed by AccountingExpertAuditor before merge. Add to PR checklist.
  - **Route-level test requirement**: New route files must ship with integration tests. **Proposed standard**: CI gate that fails if any route file under `routes/` has no corresponding `test_` file.
  - **Pydantic schema strictness**: All new response models must use `extra="forbid"`. **Proposed standard**: Add to PR checklist; lint rule if feasible.
  - **Billing transaction atomicity**: All multi-step billing operations must use a single `db.commit()`. **Proposed standard**: Add to `CONTRIBUTING.md` billing section.
  - **Going concern output completeness**: All computed diagnostic sections must appear in both JSON and PDF exports. **Proposed standard**: New engine outputs require PDF rendering before the sprint is marked complete.

## 6) Next Sprint Recommendation

### Sprint 561 — Compliance Boundary Fixes + Billing Safety

**Complexity Score:** 6/10 (compliance renaming is straightforward; billing transaction refactoring requires careful testing)

**Immediate (P1 — Hotfix Track):**
1. Rename "Composite Risk Score" to "Anomaly Density Index" across backend and frontend (F-001)
2. Fix ISA 530 sampling conclusion language — "population accepted" → ISA 530-compliant phrasing (F-002)

**Primary Objectives (P2):**
3. Add idempotency keys to Stripe checkout session creation (F-005)
4. Differentiate webhook error responses: 400 for data errors, 500 for operational errors (F-006)
5. Wrap billing checkout flow in single atomic transaction (F-007)
6. Create integration tests for `audit_pipeline.py` and `admin_dashboard.py` (F-003, top 2 priorities)

**Secondary Objectives (P3):**
7. Add going concern section to TB Diagnostic PDF (F-010)
8. Replace `print()` with structured logging in `config.py` (F-011)
9. Fix BrandIcon.tsx `as any` type assertion (F-012)

**Carryover from Prior DEC:**
10. Fix procedure rotation: replace hardcoded `rotation_index=1` in AP/JE memo generators (DEC 2026-03-18 F-002)
11. Investigate identical data quality scores across engines (DEC 2026-03-18 F-005)

**Verification:**
- `pytest` — all 6,700+ tests pass
- `npm run build` passes
- `npm test` — 1,426+ tests pass
- Zero occurrences of "Composite Risk Score" or "population is accepted" in user-facing output
- Stripe checkout session creation includes idempotency_key
- Webhook handler returns 400 for ValueError/KeyError, 500 for operational errors
- Going concern section visible in generated TB Diagnostic PDF

**Agents:**
- **Primary**: AccountingExpertAuditor, Systems Architect (A), Verification Marshal (I)
- **Supporting**: Security & Privacy Lead (D), Type & Contract Purist (H)

## 7) Agent Coverage Report

- **Systems Architect (A)**: Billing transaction safety (F-005, F-006, F-007) — partial commits and missing idempotency keys identified. APScheduler lock TTL concern (F-009). N+1 query in admin_dashboard noted (deferred — no performance impact at current scale). Raw SQL in database.py init is technical debt but functional.
- **Performance Alchemist (B)**: No performance regressions. Dissented on P1 for route coverage (argues engine-level tests cover the logic). Dissented on P2 for partial commits (argues webhook self-healing mitigates). No findings originated.
- **DX & Accessibility Lead (C)**: Frontend design compliance verified — zero violations across 195 components. WCAG compliance strong. Keyboard navigation and ARIA exemplary in marketing components. Frontend test coverage gap (25%) is the primary concern. Going concern PDF gap (F-010) flagged as workpaper documentation issue.
- **Security & Privacy Lead (D)**: Comprehensive security review — no critical/high vulnerabilities. JWT lifecycle, CSRF, upload validation, XXE prevention, rate limiting, SQL injection prevention all robust. 61 injection regression tests passing. Pydantic `extra="allow"` (F-008) flagged as schema laxity concern. Checkout idempotency (F-005) and webhook signature logging gap identified.
- **Modernity & Consistency Curator (E)**: `slowapi` unmaintained but canary-tested (documented migration plan exists). 10 Pydantic models with `extra="allow"` need deprecation timeline. Error response shapes inconsistent across 47 route files (deferred — functional but not elegant).
- **Observability & Incident Readiness (F)**: `print()` in config.py (F-011) breaks structured logging pipeline. Missing request_id in billing error logs reduces incident correlation capability. Webhook signature failures should trigger security logging. Prometheus metric cardinality is within bounds.
- **Data Governance & Zero-Storage Warden (G)**: Zero-Storage fully compliant. No financial data in logs, DB, or error reporting. Sentry request body stripping confirmed. Going concern data (F-010) is computed but not exported in PDF — data governance perspective: computed data should be consistently available in all export formats.
- **Type & Contract Purist (H)**: 10 Pydantic `extra="allow"` models (F-008) undermine API contract reliability. 1 production `as any` in BrandIcon.tsx (F-012). TypeScript strict mode properly configured (noUncheckedIndexedAccess, noImplicitReturns). Frontend type discipline is otherwise exemplary.
- **Verification Marshal (I)**: 10+ untested routes (F-003) — largest systemic quality gap. Webhook handler tests cover registration but not per-event processing. Time-dependent test patterns (F-013) create latent flakiness risk. Prior DEC remediation rate: 83% (10/12). Sprint 558 successfully fixed schema drift. Recommends route-level test requirement as CI gate.
- **AccountingExpertAuditor**: Two compliance boundary violations (F-001, F-002) are the highest-priority findings in this report. "Composite Risk Score" mislabels an anomaly density index as a risk assessment — ISA 315 boundary violation. "Population accepted" in sampling conclusions usurps auditor judgment — ISA 530 paragraph 14 violation. Going concern output gap (F-010) means computed ISA 570 indicators are invisible in the primary export. Procedure rotation (carry-forward from prior DEC) and data quality score investigation remain open. Platform methodology is otherwise sound — anomaly detection is rules-based and deterministic, disclaimers are present, and audit terminology guardrails are enforced. The two labeling fixes are single-string changes with outsized compliance impact.
