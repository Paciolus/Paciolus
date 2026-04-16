# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-04-16] 22e16dc: backlog hygiene — Sprint 611 R2/S3 bucket added to ceo-actions Backlog Blockers; Sprint 672 placeholder for Loan Amortization XLSX/PDF export (Sprint 625 deferred work)
- [2026-04-14] a32f566: hallucination audit hotfix — /auth/refresh handler 401→403 for X-Requested-With mismatch (aligns with CSRF middleware); added .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
- [2026-04-07] 73aaa51: dependency patch — uvicorn 0.44.0, python-multipart 0.0.24 (nightly report remediation)
- [2026-04-06] 39791ec: secret domain separation — AUDIT_CHAIN_SECRET_KEY independent from JWT, backward-compat verification fallback, TLS evidence signing updated
- [2026-04-04] 29f768e: dependency upgrades — 14 packages updated, 3 security-relevant (fastapi 0.135.3, SQLAlchemy 2.0.49, stripe 15.0.1), tzdata 2026.1, uvicorn 0.43.0, pillow 12.2.0, next watchlist patch
- [2026-03-26] e04e63e: full sweep remediation — sessionStorage financial data removal, CSRF on /auth/refresh, billing interval base-plan fix, Decimal float-cast elimination (13 files, 16 tests added)
- [2026-03-21] 8b3f76d: resolve 25 test failures (4 root causes: StyleSheet1 iteration, Decimal returns, IIF int IDs, ActivityLog defaults), 5 report bugs (procedure rotation, risk tier labels, PDF overflow, population profile, empty drill-downs), dependency updates (Next.js 16.2.1, Sentry, Tailwind, psycopg2, ruff)
- [2026-03-21] 8372073: resolve all 1,013 mypy type errors — Mapped annotations, Decimal/float casts, return types, stale ignores (#49)
- [2026-03-20] AUDIT-07-F5: rate-limit 5 unprotected endpoints — webhook (10/min), health (60/min), metrics (30/min); remove webhook exemption from coverage test
- [2026-03-19] CI fix: 8 test failures — CircularDependencyError (use_alter), scheduler_locks mock, async event loop, rate limit decorators, seat enforcement assertion, perf budget, PG boolean literals
- [2026-03-18] 7fa8a21: AUDIT-07-F1 bind Docker ports to loopback only (docker-compose.yml)
- [2026-03-18] 52ddfe0: AUDIT-07-F2 replace curl healthcheck with python-native probe (backend/Dockerfile)
- [2026-03-18] 5fc0453: AUDIT-07-F3 create /app/data with correct ownership before USER switch (backend/Dockerfile)
- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.
> Sprints 570–571 archived to `tasks/archive/sprints-570-571-details.md`.
> Sprints 572–578 archived to `tasks/archive/sprints-572-578-details.md`.
> Sprints 579–585 archived to `tasks/archive/sprints-579-585-details.md`.
> Sprints 586–591 archived to `tasks/archive/sprints-586-591-details.md`.
> Sprints 592–595 archived to `tasks/archive/sprints-592-595-details.md`.
> Sprints 596–599 archived to `tasks/archive/sprints-596-599-details.md`.
> Sprints 600–603 archived to `tasks/archive/sprints-600-603-details.md`.
> Sprints 604–607 archived to `tasks/archive/sprints-604-607-details.md`.
> Sprints 608–609 archived to `tasks/archive/sprints-608-609-details.md`.
> Sprints 665–667 archived to `tasks/archive/sprints-665-667-details.md` (CEO remediation brief v6 — harness, intake hardening, risk scoring/conclusion).
> Sprints 668–671 archived to `tasks/archive/sprints-668-671-details.md` (materiality coverage, multi-column TB, account-type-aware diagnostics, DOCX/PDF ingestion).
> Sprints 610, 612–615 archived to `tasks/archive/sprints-610-615-details.md`.
> Sprints 616–620 archived to `tasks/archive/sprints-616-620-details.md`.
> Sprints 621–625 archived to `tasks/archive/sprints-621-625-details.md`.
> Sprints 626–630 archived to `tasks/archive/sprints-626-630-details.md`.

> **Multi-agent review 2026-04-14 — Sprints 600–664 seeded from 8 parallel agent reviews (Critic, Designer, Executor, Guardian, Scout, Accounting Auditor, Project Auditor, Future-State Consultant). Each sprint cites its originating agent. Ordered by severity, not discovery order.**

> **CEO remediation brief 2026-04-15 — Sprints 665–671 inserted ahead of the seeded 610–664 backlog. Source: six-file TB test sweep (`tests/evaluatingfiles/`) surfacing 16 issues across intake, scoring, column detection, and multi-format handling. Issues 5 (BLOCKING), 9, 2, 7, 3, 4, 12 cleared by Sprints 665–667; Sprints 668–671 remain pending.**

---



### Sprint 611: ExportShare Object Store Migration
**Status:** PENDING
**Source:** Critic — DB bloat risk
**File:** `backend/export_share_model.py:43`
**Problem:** `export_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)` stores up to 50 MB per shared export in primary Neon Postgres. 20 concurrent shares = 1 GB of binary row storage; Neon Launch tier cap is 10 GB. Also bloats every DB backup — unclear whether zero-storage policy permits this.
**Changes:**
- [ ] Provision object store bucket (R2 or S3) with pre-signed URL pattern
- [ ] Store `export_data` in bucket keyed by `share_token_hash`; DB row keeps metadata + object key only
- [ ] Extend cleanup scheduler to delete object when share revoked/expired
- [ ] Backfill migration for existing shares

---

### Sprint 631: Balance Sheet Assertion Completeness Checker
**Status:** COMPLETE
**Source:** Accounting Auditor — preflight capability gap
**File:** `backend/preflight_engine.py` extension
**Problem:** Classification validator checks individual accounts but does not assert population-level completeness — no engine verifies the uploaded TB has at least one account in each GAAP category (Assets/Liabilities/Equity/Revenue/Expenses) before downstream tools run.
**Changes:**
- [x] After classification, check all 5 categories have ≥1 mapped account
- [x] Emit preflight warning: "No [category] accounts detected — financial statement output will be incomplete"
- [x] Secondary check: Revenue > 0 but COGS = 0 → flag classification gap
- [x] Surface in preflight gate UI (via new `category_completeness` block on the preflight response; response schema wired for frontend consumption)

**Review:**
- Ran classifier inline in preflight (after column detection). `CategoryCompleteness` dataclass on `PreFlightReport`; `category_completeness` JSON block on the to_dict output and the Pydantic response schema.
- `category_completeness` added to `_CHECK_WEIGHTS` (10% weight); issues surface at high severity for missing categories, medium for the Revenue > 0 / COGS = 0 classification gap.
- COGS gap is skipped when no expense activity exists, so service-business TBs (no COGS) don't get false-positive warnings.
- Existing clean-file test updated to include all 5 GAAP categories; 5 new tests added covering complete TB, missing equity, COGS gap, service business no-op, and to_dict shape.
- All 27 preflight tests pass.

---

### Sprint 632: Account Sequence Gap Detector
**Status:** PENDING
**Source:** Accounting Auditor — TB-only fraud signal not currently surfaced
**File:** new engine under `backend/audit/rules/`
**Problem:** Gaps in numeric account number sequences can reveal suppressed accounts. No existing tool surfaces this.
**Changes:**
- [ ] Parse numeric component from account numbers, sort, detect gaps
- [ ] Configurable tolerance (default: gaps of 10+ where adjacent within 5 of boundary)
- [ ] Exclude category boundary gaps (1xxx→2xxx)
- [ ] Integrate into Classification Validator output
- [ ] Test against fabricated TB with suppressed account ranges

---

### Sprint 633: Cash Flow Projector (30/60/90-Day)
**Status:** PENDING
**Source:** Future-State Consultant — missing catalog feature #16 (Strategic Bet, Priority 7/4)
**File:** new engine; reuses AR/AP aging parsers
**Problem:** Existing `financial_statement_builder.py` cash flow statement is historical indirect-method only. No forward-looking AR/AP-based projector. Operational finance teams need this.
**Changes:**
- [ ] New `backend/cash_flow_projector_engine.py`
- [ ] Inputs: AR aging, AP aging (both already parsed by existing engines), recurring cash flows, opening balance
- [ ] Base/stress/best-case scenarios
- [ ] Daily/weekly 30/60/90-day forecast
- [ ] Collection probability analysis, suggested AR priorities, AP deferral candidates
- [ ] Route + PDF + Excel

---

### Sprint 634: 1099 Preparation Helper
**Status:** PENDING
**Source:** Future-State Consultant — missing catalog feature #12
**File:** new engine + route
**Problem:** Not in any route or engine file. 1099 prep is annual pain point with intense Oct–Jan demand.
**Changes:**
- [ ] New `backend/form_1099_engine.py` — aggregate AP payments by vendor, apply 1099 reporting rules, validate vendor data (TIN, address)
- [ ] Output: 1099 candidate listing with amounts by box, data quality report, IRS-ready file format, W-9 collection list
- [ ] Route + PDF + CSV export
- [ ] Seasonal marketing hook (release before October)

---

### Sprint 635: Book-to-Tax Adjustment Calculator
**Status:** PENDING
**Source:** Future-State Consultant — missing catalog feature #13
**File:** new engine + route
**Problem:** Not present. M-1/M-3, UNICAP, meals/entertainment — none implemented.
**Changes:**
- [ ] New `backend/book_to_tax_engine.py` — permanent differences (meals 50%, fines, life insurance, tax-exempt interest), temporary differences (depreciation, bad debt, prepaids, accruals, UNICAP, stock comp)
- [ ] M-1/M-3 formatted output based on entity size
- [ ] Deferred tax asset/liability rollforward
- [ ] Route + PDF

---

### Sprint 636: W-2/W-3 Reconciliation Tool
**Status:** PENDING
**Source:** Future-State Consultant — missing catalog feature #14
**File:** new engine + route
**Problem:** Not present. Payroll testing tests data integrity, not W-2 reconciliation. W-2 errors create amended filings + penalties.
**Changes:**
- [ ] New `backend/w2_reconciliation_engine.py` — reconcile payroll system → draft W-2 → quarterly 941s
- [ ] Validate SS wage base, HSA, retirement plan limits
- [ ] Employee-level discrepancy report
- [ ] Route + PDF

---

### Sprint 637: Multi-Entity Intercompany Elimination
**Status:** PENDING
**Source:** Future-State Consultant — partial catalog feature #11
**File:** `backend/audit/rules/relationships.py:81` currently single-TB only
**Problem:** Existing single-TB intercompany imbalance detection exists. Missing: multi-entity TB input, elimination JE generation, consolidation worksheet.
**Changes:**
- [ ] Accept multiple TB uploads in one session
- [ ] Extract intercompany balances per entity, match reciprocal pairs
- [ ] Calculate elimination JEs
- [ ] Flag timing/currency/error imbalances
- [ ] Consolidation worksheet output (pre-elim, elim, post-elim)

---

### Sprint 638: Statement Of Changes In Equity
**Status:** PENDING
**Source:** Future-State Consultant — partial catalog feature #7
**File:** `backend/financial_statement_builder.py:275`
**Problem:** TB → Financial Statements mapper builds BS, IS, Cash Flow. Statement of Changes in Equity is missing from spec output.
**Changes:**
- [ ] Extend `financial_statement_builder.py` to generate equity rollforward from TB equity accounts
- [ ] Include in PDF financial statement package
- [ ] Explicit unmapped-accounts report alongside the mapping trace

---

### Sprint 639: Bank Reconciliation One-to-Many + Suggested JEs
**Status:** PENDING
**Source:** Future-State Consultant — partial catalog feature #2
**File:** `backend/bank_reconciliation.py:399-518, 1201`
**Problem:** V1 exact + tolerance matching only. No one-to-many matching (one bank txn → multiple GL entries). No suggested JE templates for common reconciling items (fees, interest, bank charges).
**Changes:**
- [ ] Add split-matching pass after greedy pass
- [ ] Emit `suggested_journal_entries` field on `BankRecResult` for BANK_ONLY items classified as fees/interest
- [ ] Tests for split-match scenarios

---

### Sprint 640: Budget vs Actual Favorable/Unfavorable Classification
**Status:** PENDING
**Source:** Future-State Consultant — partial catalog feature #8
**File:** `backend/multi_period_comparison.py:707-934`
**Problem:** Computes variance amount/percent but never classifies favorable/unfavorable. Opposite signs mean different things for revenue vs expense — expense underage is favorable, revenue underage is unfavorable. Currently ambiguous.
**Changes:**
- [ ] Add `variance_direction: Literal["favorable", "unfavorable"]` derived from account type + sign
- [ ] Add `commentary_prompt` field for `SignificanceTier.CRITICAL` movements
- [ ] Update PDF and CSV exports

---

### Sprint 641: Revenue Benford MAD/Conformity Parity
**Status:** PENDING
**Source:** Future-State Consultant — inconsistent detection depth
**File:** `backend/shared/benford.py:7` (comment), `backend/revenue_testing_engine.py`
**Problem:** Revenue engine explicitly excluded from shared Benford module ("NOT used by revenue_testing_engine.py — chi-squared only, no MAD/conformity"). Revenue gets a weaker fraud test than JE or Payroll.
**Changes:**
- [ ] Migrate `revenue_testing_engine.py` Benford to `shared.benford.analyze_benford()`
- [ ] Remove the carve-out comment
- [ ] Update revenue testing snapshot

---

### Sprint 642: Ghost Employee HR-Master Cross-File Input
**Status:** PENDING
**Source:** Future-State Consultant — partial catalog feature #20
**File:** `backend/payroll_testing_engine.py:1339-1418`
**Problem:** PR-T9 operates entirely within the payroll file. Cannot identify employees on payroll who are absent from HR master — the most forensically significant ghost employee indicator.
**Changes:**
- [ ] Add optional `hr_master_rows` input to `run_payroll_testing()`
- [ ] When provided, compare payroll employee IDs to HR active list
- [ ] Flag payroll entries with no HR record, or payroll after termination date
- [ ] Address-match-to-executive heuristic

---

### Sprint 643: Duplicate Payment Recovery-Value Summary
**Status:** PENDING
**Source:** Future-State Consultant — partial catalog feature #3
**File:** `backend/ap_testing_engine.py:671, 1014`
**Problem:** Exact and fuzzy duplicate detection implemented. Missing: estimated recovery value total, duplicate rate % by vendor, time-trend of elevated activity.
**Changes:**
- [ ] Aggregate duplicate candidates into total recovery value
- [ ] Vendor-level duplicate rate summary
- [ ] Time-trend chart data in memo output

---

### Sprint 644: doc_consistency_guard.py Test Coverage
**Status:** PENDING
**Source:** Project Auditor + Coverage Sentinel — first real finding from Sprint 599
**File:** `backend/guards/doc_consistency_guard.py` (0% coverage)
**Problem:** Guard runs in CI consistency check but has zero test coverage. Surfaced as top uncovered file by the new deterministic coverage sentinel.
**Changes:**
- [ ] New `backend/tests/test_doc_consistency_guard.py` with smoke coverage
- [ ] Fixtures exercising each guard rule
- [ ] Coverage sentinel green on next run

---

### Sprint 645: Commit-Msg Hook Probe Verification
**Status:** PENDING
**Source:** Project Auditor — residual from Audit 35 (SHA backfill + 596–599 archival already complete)
**File:** `frontend/.husky/commit-msg`
**Problem:** Both archival gate and todo-staged gate should pass cleanly on the next `Sprint N:` commit. No standalone probe has verified the hook post-cleanup.
**Changes:**
- [ ] Confirm commit-msg hook passes on the next real Sprint commit (fold into that sprint's close verification)

---

### Sprint 646: PeriodFileDropZone Deferred Item Tracking
**Status:** PENDING
**Source:** Project Auditor — 3 consecutive audit mention
**File:** `frontend/src/components/multiPeriod/PeriodFileDropZone.tsx:10`, `tasks/todo.md` Deferred Items table
**Problem:** `// TODO: type as AuditResult after full migration` has appeared in three consecutive audits without being added to the Deferred Items table. Untracked deferrals are a tracking liability.
**Changes:**
- [ ] Add row to Deferred Items table: `| PeriodFileDropZone type migration | Full AuditResult typing deferred until multi-period migration completes | Sprint 596+ |`

---

### Sprint 647: PeriodFileDropZone AuditResult Type Migration
**Status:** PENDING
**Source:** Executor — type-safety escape hatch
**File:** `frontend/src/components/multiPeriod/PeriodFileDropZone.tsx:10`, `frontend/src/app/tools/multi-period/page.tsx:116-141`
**Problem:** `result: Record<string, unknown> | null` forces `as unknown as AuditResult` casts in 6 places. Type-unsafe.
**Changes:**
- [ ] Change property type to `AuditResult | null`
- [ ] Remove all 6 cast sites
- [ ] Update consumers to use typed access

---

### Sprint 648: useTrialBalanceUpload Error Response Typing
**Status:** PENDING
**Source:** Executor — error shape untyped
**File:** `frontend/src/hooks/useTrialBalanceUpload.ts:247`
**Problem:** `data as unknown as Record<string, string>` on the error path — typed as `TrialBalanceResponse` elsewhere, double-cast indicates untyped error response.
**Changes:**
- [ ] Add discriminated union for success vs error response
- [ ] Replace the cast with a type guard
- [ ] Apply pattern to other hooks with similar escape hatches

---

### Sprint 649: Export Filename Context
**Status:** PENDING
**Source:** Scout — 10 identical `Paciolus_Report.pdf` downloads
**File:** `frontend/src/components/export/DownloadReportButton.tsx:73`, `frontend/src/components/preflight/PreFlightSummary.tsx:186`, `frontend/src/components/trialBalance/AccrualCompletenessSection.tsx:138`
**Problem:** Default filename is `Paciolus_Report.pdf`. A CPA running 10 engagements gets 10 identical filenames in their Downloads folder. Also: no adjacent micro-copy explaining what the export contains.
**Changes:**
- [ ] Dynamic filename: `Paciolus_<Tool>_<Client>_<YYYYMMDD>.pdf`
- [ ] Micro-copy under each export button: "PDF — full diagnostic memo" / "CSV — raw findings"

---

### Sprint 650: PricingComparison Duplicate Render Cleanup
**Status:** PENDING
**Source:** Designer — duplicated table markup
**File:** `frontend/src/app/(marketing)/pricing/page.tsx:789-790`, `frontend/src/components/pricing/PricingComparison.tsx:50`
**Problem:** Pricing page renders an inline table identical to the `PricingComparison` component, then has the component elsewhere. Two separate `min-w-[700px]` tables on the same page.
**Changes:**
- [ ] Delete inline duplicate at `pricing/page.tsx:789-790`, render `<PricingComparison />` in its place
- [ ] Add CSS fade-edge scroll hint on overflow container

---

### Sprint 651: UnifiedToolbar Responsive Zone Collapse
**Status:** PENDING
**Source:** Designer — 768px breakpoint overflow
**File:** `frontend/src/components/shared/UnifiedToolbar/UnifiedToolbar.tsx:86, 140`
**Problem:** Both action zones fixed at `w-[120px] flex-shrink-0`. At 640–768px the zones consume 240px of a ~640px bar, leaving only ~160px for logo+nav. Center nav has no `min-w-0 overflow-hidden` guard.
**Changes:**
- [ ] Add `min-w-0 overflow-hidden` to center nav container
- [ ] Scale zones: `w-[80px] sm:w-[120px]`
- [ ] Visual regression test at 375/640/768/1024

---

### Sprint 652: Frontend Hook Test Coverage Backfill
**Status:** PENDING
**Source:** Guardian — 20+ hooks without dedicated tests
**File:** `frontend/src/hooks/` (20+ untested)
**Problem:** Untested hooks include `useAuthSession` (token refresh race potential), `useExportSharing` (sensitive delivery), all 5 tool-specific testing hooks, `useActivityHistory`, `useBatchUpload`, `useCommandPalette`, `useFeatureFlag`, `useInternalAdmin`, `useWorkspaceInsights`, etc.
**Changes:**
- [ ] Prioritize by risk: `useAuthSession` → `useExportSharing` → 5 tool hooks
- [ ] Test: concurrent refresh, 401 mid-session, network error path
- [ ] One test file per hook with at minimum happy path + error path

---

### Sprint 653: CSRF Middleware Connection Pool Bypass
**Status:** PENDING
**Source:** Critic — low severity architectural debt
**File:** `backend/security_middleware.py:476-512`
**Problem:** `_extract_user_id_from_refresh_cookie` opens fresh `SessionLocal()` per `/auth/logout` and `/auth/refresh` call, outside `get_db()` lifetime. Bypasses connection pool accounting. Silently swallows DB exceptions, degrading CSRF to signature-only on DB outage.
**Changes:**
- [ ] For `/auth/refresh`, skip the DB lookup entirely (already covered by `X-Requested-With` header proof at lines 566-576)
- [ ] For `/auth/logout`, accept CSRF token via request body alongside cookie
- [ ] Remove the session-factory helper

---

### Sprint 654: Trust Page Self-Assessed Disclosure Prominence
**Status:** PENDING
**Source:** Scout — omission-by-silence trust gap
**File:** `frontend/src/app/(marketing)/trust/page.tsx:151-159`
**Problem:** GDPR/CCPA show green "Compliant" badge with self-assessed detail text, but the visual treatment doesn't prominently mark it as self-assessed. SOC 2 absence is correct per CEO deferral but unspoken — creates trust gap when enterprise buyer asks.
**Changes:**
- [ ] Add "Self-assessed — no third-party audit" callout directly adjacent to each compliance badge
- [ ] Add single sentence: "No SOC 2 audit completed — planned for 2026"
- [ ] Match Oat & Obsidian tokens

---

### Sprint 655: Zip-Bomb Test Determinism
**Status:** PENDING
**Source:** Guardian — silent CI skip of a security guard
**File:** `backend/tests/test_parser_resource_guards.py:163`
**Problem:** `pytest.skip`s itself when compression ratio isn't high enough — in constrained CI envs the guard is never exercised. Production guard logic is real but CI hides it.
**Changes:**
- [ ] Replace skip with a deterministic synthetic buffer guaranteed to trigger >100:1 ratio
- [ ] Or use `hypothesis` strategy to build the input
- [ ] Ensure test runs (not skipped) on all CI environments

---

### Sprint 656: KeyMetricsSection Mono Label/Value Separation
**Status:** PENDING
**Source:** Designer — typography consistency
**File:** `frontend/src/components/analytics/KeyMetricsSection.tsx:235-245`
**Problem:** Labels like "Assets:" render inside the `font-mono` span alongside the numeric value, making labels look mechanical. Should be `font-sans` label + `font-mono` number.
**Changes:**
- [ ] Split into `<span font-sans text-xs>Assets:</span> <span font-mono>$X</span>` pattern
- [ ] Apply to all 4 category totals

---

### Sprint 657: ToolSettingsDrawer Mobile Gutter Cap
**Status:** PENDING
**Source:** Designer — 375px viewport clipping
**File:** `frontend/src/components/shared/ToolSettingsDrawer.tsx:189`
**Problem:** `w-[400px] max-w-[90vw]` means on a 375px device the drawer is `337px` — close button clipped.
**Changes:**
- [ ] Change to `w-full max-w-[400px]` with `sm:w-[400px]`, or `max-w-[min(400px,100vw-24px)]`
- [ ] Manual test at 320/375/414 widths

---

### Sprint 658: MatchSummaryCards Mono Numerics
**Status:** PENDING
**Source:** Designer — financial data not in font-mono
**File:** `frontend/src/components/bankRec/MatchSummaryCards.tsx:104`
**Problem:** `Match Rate: X% (N of M items)` renders as plain text. Match rate is a financial metric that should use `font-mono` per brand mandate.
**Changes:**
- [ ] Wrap `matchRate.toFixed(0)%` and counts in `font-mono` spans
- [ ] Grep remaining untagged numeric metrics across bankRec and other tool summaries

---

### Sprint 659: follow_up_items_manager DB Aggregation
**Status:** PENDING
**Source:** Guardian — in-memory N+1 pattern
**File:** `backend/follow_up_items_manager.py:314-337`
**Problem:** `get_summary_for_engagement` loads all items into Python memory first (`.all()`) then aggregates. For high-volume engagements this is an in-memory N+1 — OOM risk on large engagements.
**Changes:**
- [ ] Rewrite as `db.query(func.count(), FollowUpItem.severity).group_by(...)`
- [ ] Performance test with 10k items
- [ ] Verify memory footprint unchanged at 10k vs 100 items

---

### Sprint 660: accrual_completeness monthly_run_rate Decimal Guard
**Status:** PENDING
**Source:** Guardian — float/Decimal precision fragility
**File:** `backend/accrual_completeness_engine.py:891-892`
**Problem:** `monthly_run_rate = prior_operating_expenses / MONTHS_PER_YEAR` uses raw `float`. `NEAR_ZERO` guard then compares `float` to `Decimal` constant. Works today but fragile at exact boundary values.
**Changes:**
- [ ] Convert `prior_operating_expenses` to `Decimal` before the division
- [ ] Use `Decimal(str(...))` guard consistently
- [ ] Test with `prior_operating_expenses = 1e-7` to verify NEAR_ZERO fires

---

### Sprint 661: Impersonation Token Expiry Asymmetry
**Status:** PENDING
**Source:** Critic — asymmetric revocation risk
**File:** `backend/security_middleware.py:869`
**Problem:** `ImpersonationMiddleware` uses `verify_exp=False` to block mutations. If a 15-minute impersonation token leaks (logs/proxies), the blocking path is effectively permanent for the impersonated user — no server-side revocation, `jti` claim exists but is not registered in any revocation store.
**Changes:**
- [ ] Add `jti` to a Redis revocation set on token revocation
- [ ] Check revocation set in the mutation-blocking path
- [ ] Document the asymmetric behavior in `SECURE_SDL_CHANGE_MANAGEMENT.md`
- [ ] Test: revoked impersonation token stops blocking mutations

---

### Sprint 662: Payroll Memo "Physical Existence" Language Reframe
**Status:** PENDING
**Source:** Accounting Auditor — assurance-adjacent procedure language
**File:** `backend/payroll_testing_memo_generator.py:387-390`
**Problem:** "Confirm physical existence of employee and legitimacy of the payment" is a field audit procedure, not a TB diagnostic. Parenthetical qualifier exists but phrasing blurs diagnostic output vs audit instruction.
**Changes:**
- [ ] Reframe as "Suggested Auditor Procedure — practitioner to consider whether physical verification is warranted based on engagement risk"
- [ ] Audit all memo generators for similar assurance-voice drift

---

### Sprint 663: Anomaly Generator "Control Testing" Checkbox Reframe
**Status:** PENDING
**Source:** Accounting Auditor — platform-directed audit methodology implication
**File:** `backend/anomaly_summary_generator.py:635`
**Problem:** "[ ] Add control testing procedures" appears as a platform-suggested next step. Control testing is auditor-judgment and engagement scope — platform should not direct methodology.
**Changes:**
- [ ] Remove the checkbox line
- [ ] Replace with free-text "Planned Response" field for practitioner use

---

### Sprint 664: accrual_completeness "Legal Counsel" Language Reframe
**Status:** PENDING
**Source:** Accounting Auditor — legal-adjacency risk
**File:** `backend/accrual_completeness_engine.py:487`, `backend/generate_sample_reports.py:3716`
**Problem:** `driver_source = "Requires legal counsel confirmation"` embeds a legal-requirement determination in automated engine output. Reliance on this could create liability if auditor treats the platform's output as authoritative.
**Changes:**
- [ ] Rephrase to "Legal obligations may be present — practitioner should evaluate whether legal confirmation is warranted"
- [ ] Apply same softening pattern across all engine `driver_source` strings that reference legal/regulatory determinations

---

### Sprint 672: Loan Amortization XLSX + PDF Export
**Status:** PENDING
**Source:** Sprint 625 follow-up — XLSX and PDF deferred at sprint close
**File:** `backend/routes/loan_amortization.py` (extend), new `backend/pdf/sections/loan_amortization.py`, possibly new `backend/loan_amortization_excel.py`
**Problem:** Sprint 625 shipped CSV export only. Auditors and operational finance teams routinely paste these schedules into engagement workpapers — XLSX preserves cell formatting and PDF locks the schedule for evidence. Both were deferred so the engine, route, and frontend could land in one sprint.
**Changes:**
- [ ] XLSX export endpoint `/audit/loan-amortization/export.xlsx` — schedule sheet + annual summary sheet + inputs sheet, currency-formatted columns, frozen header row
- [ ] PDF section module rendering the inputs block, summary cards, annual table, and the period schedule (paginated — 30-yr monthly = 360 rows, must page cleanly)
- [ ] PDF endpoint `/audit/loan-amortization/export.pdf`
- [ ] Frontend: add XLSX and PDF download buttons next to the existing CSV button on `/tools/loan-amortization`
- [ ] Tests: row count + total-interest cell match the JSON response for both formats

---
