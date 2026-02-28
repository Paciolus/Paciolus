# Project Protocol: The Council

## Role: IntegratorLead
You are the synthesis lead. You do not originate large ideas; you resolve deadlocks between sub-agents and the CEO (User).

## Interaction Protocol: The Conflict Loop
When a task is initiated:
1. **Call Specialists:** Use `/agents run` to consult `critic`, `scout`, `executor`, and `guardian`.
2. **Audit for "Hive-Mind":** If agents agree too quickly, you must play devil's advocate.
3. **Identify Tensions:** Explicitly state: "[Agent A] wants X, but [Agent B] insists on Y."
4. **The Tradeoff Map:** Present the CEO with a choice between specific technical/market sacrifices.

## Global Rules
- **No "I Agree":** Forbid agents from simply echoing.
- **Steel Man:** Every critique must acknowledge the merit of the original idea before dismantling it.
- **Decision Rule:** No path is final until an implementation plan exists and a "Complexity Score" is assigned.

---

## MANDATORY: Directive Protocol

**STRICT REQUIREMENT:** Every new directive MUST follow this protocol:

### 1. Plan Update (START of directive)
Before ANY implementation begins:
- [ ] Read `tasks/todo.md`
- [ ] Add/update checklist items for the current directive
- [ ] Mark the directive as "In Progress"
- [ ] Identify which agents are involved

### 2. Implementation
- Follow the Conflict Loop
- Track progress by checking off items in `tasks/todo.md`
- Document blockers in the Review section

### 3. Verification (BEFORE marking complete)
Before declaring a directive complete:
- [ ] Run `npm run build` in frontend (must pass with no errors)
- [ ] Run `pytest` in backend if tests were modified
- [ ] Verify Zero-Storage compliance for any new data handling

### 4. Lesson Learned (END of directive)
After directive completion:
- [ ] Add entry to `tasks/lessons.md` if ANY of these occurred:
  - CEO provided a correction
  - A better pattern was discovered
  - A mistake was made and fixed
  - An assumption proved wrong
- [ ] Update `tasks/todo.md` Review section with completion notes
- [ ] Mark all directive items as complete

### 5. Git Commit (FINAL step)
After ALL directive work is complete:
- [ ] Stage relevant files (avoid `git add -A` to prevent accidental inclusions)
- [ ] Create atomic commit with descriptive message: `Sprint X: [Brief Description]`
- [ ] Commit message should reference the sprint number and key changes

**FAILURE TO FOLLOW THIS PROTOCOL WILL RESULT IN AUDIT SCORE PENALTIES.**

---

## Current Project State

**Project:** Paciolus — Professional Audit Intelligence Platform for Financial Professionals
**Phase:** CSP Nonce Fix COMPLETE — static pre-rendering was preventing nonce injection; root layout now calls `headers()` forcing dynamic rendering across all 38 page routes; nonces now injected at request time
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** PRODUCTION READY
**Version:** 2.1.0
**Test Coverage:** 5,618 backend tests (1 skipped) + 1,345 frontend tests
**Next Phase:** Sprint 447 (Stripe Production Cutover — non-automatable: CEO sign-off + `sk_live_` keys required)

### Completed Phases (details in `tasks/todo.md`)
- **Phase I (Sprints 1-24):** Core platform — Zero-Storage TB analysis, streaming, auth, PDF/Excel export, client management, practice settings, deployment
- **Phase II (Sprints 25-40):** Test suite, 9 ratios, IFRS/GAAP, trend analysis, industry ratios, rolling windows, batch upload, benchmark RFC
- **Phase III (Sprints 41-47):** Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI
- **Phase IV (Sprints 48-55):** User profile, security hardening, lead sheets, prior period comparison, adjusting entries, DSO, CSV export, frontend tests
- **Phase V (Sprints 56-60):** UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode
- **Phase VI (Sprints 61-70):** Multi-Period TB Comparison, Journal Entry Testing (18-test battery + stratified sampling), platform rebrand, diagnostic zone protection
- **Phase VII (Sprints 71-80):** Financial Statements, AP Payment Testing (13-test battery), Bank Reconciliation, 5-tool navigation standardization
- **Phase VIII (Sprints 83-89):** Cash Flow Statement (indirect method), Payroll & Employee Testing (11-test battery), 6-tool navigation, code quality sprints (81-82)
- **Phase IX (Sprints 90-96):** Code quality extraction (shared enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement), 7-tool navigation
- **Phase X (Sprints 96.5-102):** Engagement Layer — engagement model + materiality cascade, follow-up items tracker, workpaper index, anomaly summary report, diagnostic package export, engagement workspace (frontend)
- **Phase XI (Sprints 103-110):** Tool-Engagement Integration, Revenue Testing (Tool 8), AR Aging (Tool 9), 9-tool nav, v1.0.0
- **Phase XII (Sprints 111-120):** Nav overflow, Finding Comments + Assignments, Fixed Asset Testing (Tool 10), Inventory Testing (Tool 11), 11-tool nav, v1.1.0
- **Phase XIII (Sprints 121-130):** Platform polish, dual-theme "The Vault" architecture, security hardening, WCAG AAA accessibility, 11 PDF memos, 24 rate-limited export endpoints, v1.2.0
- **Phase XIV (Sprints 131-135):** Professional Threshold — 6 public marketing/legal pages (Privacy, Terms, Contact, About, Approach, Pricing, Trust), shared MarketingNav/Footer, contact backend
- **Phase XV (Sprints 136-141):** Code Deduplication — shared parsing helpers, shared types, 4 shared testing components (DataQualityBadge, ScoreCard, TestResultGrid, FlaggedTable), context consolidation, ~4,750 lines removed
- **Phase XVI (Sprints 142-147):** API Hygiene — semantic token migration, API call consolidation (15 direct fetch → apiClient)
- **Phase XVII (Sprints 151-163):** Code Smell Refactoring — 7 backend shared modules (column detector, data quality, test aggregator, Benford, export schemas, testing route factory, memo template), 8 frontend decompositions, 15 new shared files, 8,849 lines refactored
- **Phase XVIII (Sprints 164-170):** Async Architecture Remediation — `async def` → `def` for pure-DB routes, `asyncio.to_thread()` for CPU-bound Pandas work, `BackgroundTasks` for email/tool-run recording, `memory_cleanup()` context manager, rate limit gaps closed
- **Phase XIX (Sprints 171-177):** API Contract Hardening — 100% `response_model` coverage, DELETE→204/POST→201 status codes, trends.py error-in-body→HTTPException(422), `/diagnostics/flux`→`/audit/flux` path fix, shared response schemas
- **Phase XX (Sprint 178):** Rate Limit Gap Closure — missing limits on verify-email, password-change, waitlist, inspect-workbook; global 60/min default
- **Phase XXI (Sprints 180-183):** Migration Hygiene — Alembic env.py model imports, baseline regeneration (e2f21cb79a61), manual script archival, datetime deprecation fix
- **Phase XXII (Sprints 184-190):** Pydantic Model Hardening — Field constraints (min_length/max_length/ge/le), str→Enum/Literal migration, manual validation removal (~30 lines try/except), model decomposition (WorkpaperMetadata base, DiagnosticSummaryCreate sub-models), v2 syntax (ConfigDict), password field_validators
- **Phase XXIII (Sprints 191-194):** Pandas Performance & Precision Hardening — Vectorized keyword matching (.apply→.str.contains), filtered-index iteration, Decimal concentration totals, NEAR_ZERO float guards (4 engines), math.fsum compensated summation (8 locations), identifier dtype preservation, dtype passthrough in security_utils
- **Phase XXIV (Sprint 195):** Upload & Export Security Hardening — CSV/Excel formula injection sanitization, column/cell limits, global body size middleware
- **Phase XXV (Sprints 197-201):** JWT Authentication Hardening — Refresh token rotation (7-day), 30-min access tokens, token reuse detection, password-change revocation, CSRF/CORS hardening, explicit bcrypt rounds, jti claim, startup token cleanup
- **Phase XXVI (Sprints 202-203):** Email Verification Hardening — Verification token cleanup job (startup), email-change re-verification via pending_email, security notification to old email, disposable email blocking on email change
- **Phase XXVII (Sprints 204-209):** Next.js App Router Hardening — 7 error boundaries, 4 route groups ((marketing), (auth), (diagnostic), tools enhanced), ~60 duplicated imports eliminated, DiagnosticProvider scoped, 8 fetch() → apiClient, 5 shared skeleton components, 11 loading.tsx files
- **Phase XXVIII (Sprints 210-216):** Production Hardening — GitHub Actions CI pipeline (pytest + build + lint), Python structured logging + request ID correlation, 46 broad exceptions narrowed to specific types, 45 return type annotations, deprecated pattern migration (DeclarativeBase, lifespan), 5 frontend `any` types eliminated, 3 TODOs resolved
- **Phase XXIX (Sprints 217-223):** API Integration Hardening — 102 Pydantic response schemas (32 diagnostic + 64 testing + 6 engagement/settings), apiClient 422 parsing, isAuthError in 3 hooks, downloadBlob migration (lib → apiClient), CSRF on logout, UI state consistency (retry buttons, theme tokens, loading text, role="alert"), 74 API contract tests, OpenAPI→TypeScript generation
- **Phase XXX (Sprints 224-230):** Frontend Type Safety Hardening — 5 `any` eliminated, 3 tsconfig strict flags (noUncheckedIndexedAccess, noFallthroughCasesInSwitch, noImplicitReturns), type taxonomy consolidation (Severity/AuditResult/UploadStatus), discriminated unions (BankRec + hook returns), 24 return type annotations, ~49 optional chains removed, 0 non-null assertions
- **Phase XXXI (Sprints 231-238):** Frontend Test Coverage Expansion — 22 pre-existing failures fixed, 20 new test files, 261 new tests added across utilities, hooks, contexts. Tests: 2,977 backend + 389 frontend
- **Phase XXXII (Sprints 241-248):** Backend Test Suite Hardening — 73 new tests (14 edge case + 59 route integration), 5 monolithic files split into 17 focused files, CSRF fixture opt-in refactor, 1 schema bugfix. Tests: 3,050 backend + 389 frontend
- **Phase XXXIII (Sprints 249-254):** Error Handling & Configuration Hardening — 131 frontend tests, Docker tuning, global exception handler, 21 sanitize_error migrations, 9 db.commit() gaps closed, secrets_manager integration, .gitignore hardened. Tests: 3,050 backend + 520 frontend
- **Phase XXXIV (Sprints 255-260):** Multi-Currency Conversion — python-jose → PyJWT, closing-rate MVP, currency engine (ISO 4217 + rate lookup + vectorized conversion), 4 API endpoints, CurrencyRatePanel, conversion memo PDF, auto-conversion in TB upload. **v1.3.0. Tests: 3,129 backend + 520 frontend**
- **Phase XXXV (Sprints 261-266 + T1):** In-Memory State Fix + Codebase Hardening — stateless HMAC CSRF, DB-backed lockout + tool sessions, float precision (math.fsum/Decimal), server_default timestamps, 8 dependency upgrades, deep health probe, CI security gates (Bandit/Dependabot/pip-audit), zero-storage language truthfulness. **Tests: 3,323 backend + 724 frontend**
- **Phase XXXVI (Sprints 268-272):** Statistical Sampling Module (Tool 12) — ISA 530 / PCAOB AS 2315, MUS + random sampling, 2-tier stratification, Stringer bound evaluation, two-phase workflow (design + evaluate), PDF memo, CSV export, 12-tool nav. **v1.4.0. Tests: 3,391 backend + 745 frontend**
- **Phase XXXVII (Sprints 273-278):** Deployment Hardening — dependency version bumps (pydantic, openpyxl, PyJWT, TypeScript), PostgreSQL connection pool tuning + CI job, Sentry APM integration (Zero-Storage compliant), 23 new frontend test files (173 new tests), coverage threshold 25%. **v1.5.0. Tests: 3,396 backend + 918 frontend**
- **Phase XXXVIII (Sprints 279-286):** Security & Accessibility Hardening + Lightweight Features — passlib→bcrypt, CVE patches, typing modernization (UP006/UP007/UP035), ruff import sorting, back_populates migration, WCAG modals/labels/images/CSP, focus trap, eslint-plugin-jsx-a11y, Data Quality Pre-Flight Report, Account-to-Statement Mapping Trace, users+auth route tests, exception narrowing. **v1.6.0. Tests: 3,440 backend + 931 frontend**
- **Phase XXXIX (Sprints 287-291):** Diagnostic Intelligence Features — TB Population Profile (Gini coefficient, magnitude buckets, top-N), Cross-Tool Account Convergence Index (flagged_accounts column, per-tool extractors, engagement tab), Expense Category Analytical Procedures (5-category ISA 520 decomposition), Accrual Completeness Estimator (run-rate ratio + threshold). 11 new API endpoints, 4 new TB sections, 4 PDF memos. **v1.7.0. Tests: 3,547 backend + 931 frontend**
- **Phase XL (Sprints 292-299):** Diagnostic Completeness & Positioning Hardening — Revenue concentration sub-typing, Cash Conversion Cycle (DPO/DIO/CCC — 12 ratios total), interperiod reclassification detection, TB-to-FS arithmetic trace (raw_aggregate + sign_correction), account density profile (9-section sparse flagging), ISA 520 expectation documentation scaffold, L1-L4 language fixes (evaluative→factual), 46 new frontend tests. **v1.8.0. Tests: 3,644 backend + 987 frontend**
- **Phase XLI (Sprints 308-312):** Cross-Tool Workflow Integration — A-Z lead sheet codes (10 tools), FLUX_ANALYSIS ToolName enum + Alembic migration, flux extractor registration + engagement wiring, convergence coverage fields (tools_covered/tools_excluded), pre-flight→column passthrough (confidence >= 0.8), materiality cascade passthrough (_resolve_materiality helper), composite score trend (get_tool_run_trends + TrendIndicator). 5 workflow gaps bridged, 0 new tools. **Tests: 3,780 backend + 995 frontend**
- **Phase XLII (Sprints 313-318):** Design Foundation Fixes — shadow/border token repair (layered shadows, strengthened borders), opacity/contrast audit (homepage elements raised to functional visibility), typography/spacing (gradient hero text, section breathing room), 3-batch light theme semantic token migration (~30 components migrated from hardcoded obsidian/oatmeal to semantic tokens). **v1.8.1. Tests: 3,780 backend + 995 frontend**
- **Phase XLIII (Sprints 319-324):** Homepage "Ferrari" Transformation — cinematic hero with animated data visualization (HeroVisualization), gradient mesh atmosphere (GradientMesh), scroll-orchestrated narrative sections (per-pillar accents, count-up numbers), interactive product preview (ProductPreview replacing DemoZone), tool grid redesign + social proof (ToolShowcase with categorized groups), marketing page polish (scroll-triggered nav). 4 new components. **v1.9.0. Tests: 3,780 backend + 995 frontend**
- **Phase XLIV (Sprints 325-329):** Tool Pages "Rolls Royce" Refinement — 3-tier card hierarchy (card/elevated/inset) with warm-toned shadows (rgba(139,119,91)), left-border accent pattern (6+ components), tabular-nums for financial data, heading-accent with sage dash, paper texture via SVG feTurbulence, drop-zone sage glow, skeleton shimmer, prefers-reduced-motion compliance. **v1.9.1. Tests: 3,780 backend + 995 frontend**
- **Phase XLV (Sprints 340-344):** Monetary Precision Hardening — 17 Float→Numeric(19,2) columns (ActivityLog 3, DiagnosticSummary 13, Engagement 1), shared `monetary.py` (quantize_monetary ROUND_HALF_UP, monetary_equal, BALANCE_TOLERANCE as Decimal), Decimal-aware balance checks in audit_engine (7 comparisons), quantize at all DB write boundaries (diagnostics, engagements, materiality cascade), Decimal modulo in round_amounts. **v1.9.2. Tests: 3,841 backend + 995 frontend**
- **Phase XLVI (Sprints 345-349):** Audit History Immutability — SoftDeleteMixin (archived_at/archived_by/archive_reason) on 5 tables (activity_logs, diagnostic_summaries, tool_runs, follow_up_items, follow_up_item_comments), ORM-level `before_flush` deletion guard (AuditImmutabilityError), all hard-delete paths converted to soft-delete, all read paths filter `archived_at IS NULL`, 26 immutability tests. **v1.9.3. Tests: 3,867 backend + 995 frontend**
- **Phase XLVII (Sprints 350-353):** ASC 606 / IFRS 15 Contract-Aware Revenue Testing — 4 new contract tests (RT-13 to RT-16): recognition timing, obligation linkage, modification treatment, SSP allocation. 6 optional contract column patterns, ContractEvidenceLevel (full/partial/minimal/none), skip-with-reason degradation, skipped test filtering in composite score. **v1.9.4. Tests: 3,891 backend + 995 frontend**
- **Phase XLVIII (Sprints 354-355):** Adjustment Approval Gating — VALID_TRANSITIONS map enforcing proposed→approved→posted (posted terminal, rejected→proposed re-proposal), InvalidTransitionError, approved_by/approved_at metadata on AdjustingEntry, official/simulation mode replacing include_proposed, is_simulation flag on AdjustedTrialBalance. **v1.9.5. Tests: 3,911 backend + 995 frontend**
- **Phase XLIX (Sprints 356-361):** Diagnostic Feature Expansion — JE Holiday Posting Detection (JT-19, ISA 240.A40), Lease Account Diagnostic (IFRS 16/ASC 842, 4 consistency tests), Cutoff Risk Indicator (ISA 501, 3 deterministic tests), Engagement Completion Gate (VALID_ENGAGEMENT_TRANSITIONS, follow-up resolution check), Going Concern Indicator Profile (ISA 570, 6 indicators with mandatory disclaimer), allowlist bugfix. **v2.0.0. Tests: 4,102 backend + 995 frontend**
- **Phase L (Sprints 362-377):** Pricing Strategy & Billing Infrastructure — 5-tier billing (Free/Starter/Professional/Team/Enterprise), Stripe integration (checkout, webhooks, portal), entitlement enforcement (diagnostic/client limits, tool access gating, soft/hard mode), A/B price testing, billing dashboard, UpgradeGate/CancelModal. **v2.1.0. Tests: 4,176 backend + 995 frontend**
- **Phase LI (Sprints 378-381):** Accounting-Control Policy Gate — 5 AST-based accounting invariant checkers (monetary float, hard delete, contract fields, adjustment gating, framework metadata), TOML config, CI job, 5 control-objective integration test scenarios (45 tests), auditor-ready evidence document, principal-level review. **Tests: 4,244 backend + 995 frontend**
- **Sprint 382:** IntelligenceCanvas — ambient particle background system replacing GradientMesh. Hybrid Canvas 2D + CSS with 3 variants (marketing/workspace/tool), sine-based flow-field particles, accent state system wired to all 12 tool pages via CanvasAccentContext, prefers-reduced-motion compliant. 10 new files, GradientMesh.tsx deleted.
- **Phase LII (Sprints 385-389):** Unified Workspace Shell "Audit OS" — WorkspaceContext shared state provider, dark CommandBar (ToolNav pattern), WorkspaceShell 3-panel layout, ContextPane (collapsible left sidebar), InsightRail (adaptive right sidebar with risk signals), QuickSwitcher (Cmd+K fuzzy search), useKeyboardShortcuts (7 global shortcuts), (workspace) route group. Portfolio + Engagements refactored to shared context. **Tests: 4,244 backend + 995 frontend**
- **Phase LIII (Sprints 390-392):** Proof Architecture "Institution-Grade Evidence Language" — ProofSummaryBar (horizontal 4-metric evidence strip) + ProofPanel (collapsible detail with trace bar + test table + confidence badge) on all 9 testing tool pages, 9 tool-specific adapters (weighted 40/30/30 scoring), ProofReadiness meter in InsightRail, build_proof_summary_section() in PDF memos (7 standard + bank rec + TWM). 13 new files, 70 new tests. **Tests: 4,252 backend + 1,057 frontend**
- **Phase LIV (Sprints 393-395):** Elite Typography System "Optical Precision" — Optical tracking CSS vars, fluid clamp() on display-xl, 4 new type tiers (subtitle/label/tool-title/tool-section), 5-tier numeric emphasis system (type-num-xs through type-num-xl), 6 editorial composition utilities. 10 tool page h1/h2 migrations, 6 shared component font-mono→type-num-* migrations, 5 marketing file updates. **Tests: 4,252 backend + 1,057 frontend**
- **Phase LV (Sprints 396-398):** Global Command Palette "Command Velocity" — Universal Cmd+K command palette (types + registry + context + UI + integration), 24 static commands (7 nav + 12 tools + 1 action + 4 settings), fuzzy search with 3-signal scoring (relevance + recency + priority), tier-gated guards mirroring UpgradeGate, dark-themed UI (data-theme="dark", z-[70]), framer-motion enter/exit, WCAG focus trap, sessionStorage recency (Zero-Storage compliant), scoped command registration (workspace clients/engagements), CommandBar + ToolNav Cmd+K triggers, QuickSwitcher retired from render. 10 new files, 7 modified. **Tests: 4,252 backend + 1,057 frontend**
- **Sprint 400:** Interactive Assurance Center — Trust page rebuilt into 4-module security reference center: interactive architecture diagram (expandable controls, zero-storage boundary visualization), filterable 19-control security matrix across 5 domains (authentication/transport/tenancy/export/data-handling), compliance timeline with artifact links, tabbed incident-preparedness playbook (detection/containment/recovery/communication), downloadable artifacts section, quick-nav anchors. WCAG accessible (aria-expanded, tablist/tabpanel, focus-visible). **Tests: 4,252 backend + 1,057 frontend**
- **Phase LVI (Sprints 401-405):** State-Linked Motion Choreography — motionTokens.ts semantic vocabulary (TIMING/EASE/DISTANCE/STATE_CROSSFADE/RESOLVE_ENTER/EMPHASIS_SETTLE), useReducedMotion hook, ToolStatePresence shared wrapper (AnimatePresence mode="wait" replacing 9 tool pages' inline variants), FlaggedEntriesTable severity-linked left-border animation, TestingScoreCard emphasis settle for high/critical risk, InsightRail risk signal motion.div entrance, ProofSummaryBar emphasis ease, useTestingExport 3-state resolution (idle→exporting→complete→idle), DownloadReportButton resolve animation, ContextPane horizontal shared-axis transition, InsightRail vertical shared-axis transition, UpgradeModal + CancelModal framer-motion migration, 29 new tests (motionTokens + ToolStatePresence + export resolution). **Tests: 4,252 backend + 1,086 frontend**
- **Phase LVII (Sprints 406-410):** "Unexpected but Relevant" Premium Moments — Feature flag infrastructure, data sonification toggle (Web Audio API), AI-style contextual microcopy (InsightRail), intelligence watermark in 17 PDF memos. 14 new files, 37 new tests. **Tests: 4,252 backend + 1,086 frontend**
- **Sprint 411:** Stabilization & Baseline Lock — Lint baselines captured (ruff: 131 errors, eslint: 55 errors + 501 warnings), remediation tracker with 4 buckets (auto-fixable/accessibility/semantic/config), CI `lint-baseline-gate` job enforcing "no increase", ruff statistics + eslint reports as CI artifacts, 8 pre-existing test failures fixed (missing useCanvasAccentSync + proof adapter mocks). **Tests: 4,260 backend + 1,111 frontend**
- **Sprints 412-420:** Lint Remediation + Accessibility + Hardening — 687→0 total lint issues (ruff + eslint), 51→0 accessibility errors, ESLint toolchain integrity, exhaustive-deps fixes, backend ruff auto-fix, EditClientModal infinite loop fix, column detector convergence (adapter pattern), API client safety (RFC 9110 idempotency, LRU cache), Husky + lint-staged pre-commit hooks, contributor guides, verification release with shim removals. **Tests: 4,294 backend + 1,163 frontend**
- **Sprints 421-431:** Multi-Format File Handling — File format abstraction (file_formats.py + fileFormats.ts), TSV/TXT ingestion (delimiter detection), OFX/QBO parser (SGML v1.x + XML v2.x), IIF parser (QuickBooks), PDF table ingestion (pdfplumber, quality gates, preview endpoint + modal). 7 new format parsers, 10 supported file types. **Tests: ~4,530 backend + ~1,190 frontend**
- **Phase LVIII (Sprints 432-438):** ODS support, cross-format hardening, Prometheus metrics, tier-gated format rollout — ODS parser (odfpy, ZIP disambiguation), malformed fixture tests (7 formats), resource guards + performance baselines, Prometheus metrics (4 counters, /metrics endpoint), feature flags + tier-gated format access, TOML alert thresholds + 8 runbook docs, integration testing. **Tests: ~4,650 backend + ~1,190 frontend**
- **Report Standardization (Sprints 0-8):** FASB/GASB framework resolution, unified cover page + brand system, universal scope/methodology with framework-aware citations, text layout hardening, heading readability, source document transparency, signoff section deprecation, QA automation + CI report-standards gate. 79 new tests. **Tests: ~4,729 backend + ~1,190 frontend**
- **Phase LIX (Sprints A-F):** Hybrid Pricing Model Overhaul — Solo/Team/Organization tiers (display-name-only migration), seat-based pricing (4–25 seats, tiered $80/$70), 7-day trial, promo infrastructure (MONTHLY20/ANNUAL10), checkout flow overhaul, `starter`→`solo` tier rename (Alembic + full codebase), pricing launch validation (216+ tests), BillingEvent table migration (b590bb0555c3), billing runbooks, Stripe test-mode configuration (4 products, 8 prices, 2 coupons).
- **Phase LX (Sprints 439-440):** Post-Launch Pricing Control System — BillingEvent append-only model (10 event types), billing analytics engine (5 decision metrics + weekly review aggregation), 3 Prometheus counters, webhook + cancel endpoint instrumentation, `GET /billing/analytics/weekly-review`, pricing guardrails doc (90-day freeze, one-lever rule, decision rubric), weekly review template. Sprint 439: BillingEvent migration + runbook env var fix. Sprint 440: E2E smoke test (27/27 passed), Stripe error handling (6 endpoints). **28 new tests. Tests: ~4,757 backend + ~1,190 frontend**
- **Phase LXI (Sprints 441-444):** Technical Upgrades — React 19 (19.2.4, removed 11 JSX.Element annotations), Python 3.12-slim-bookworm + Node 22-alpine Docker images, fastapi 0.133.1 + sqlalchemy 2.0.47, rate limiter risk documentation + 5 canary tests. **Tests: ~4,762 backend + ~1,190 frontend**
- **Compliance Documentation Pack:** Security Policy v2.0, Zero-Storage Architecture v2.0+v2.1, User Guide v3.0, DPA + Subprocessor List v1.0, Operational Governance Pack v1.0 (IRP, BCP/DR, Access Control, Secure SDL, VDP, Audit Logging). 12 docs total.
- **Sprints 445-446:** Backend coverage analysis (92.8%), frontend coverage analysis (42.9%), usage metrics review. coverage-gap-report.md + usage-metrics-review.md produced.
- **Phase LXII:** Export & Billing Test Coverage — 113 new backend tests across 3 files; export_diagnostics.py 17%→90%, export_testing.py 19%→87%, entitlement_checks.py 40%→99%. **Tests: 5,557 backend + ~1,190 frontend**
- **Sprint 448:** pandas 3.0 Evaluation — CoW audit (all patterns verified safe), 1 breaking change found and fixed (`dtype == object` → `pd.api.types.is_string_dtype()`), performance baseline (10k rows @ 46ms avg). **Commit: 0cbc8ab**
- **Phase LXIII:** Entitlement Enforcement Wiring — backend diagnostic limit pre-flight on TB endpoint (`check_diagnostic_limit` dependency, FREE 10/mo + SOLO 20/mo caps enforced); frontend UpgradeGate wired on 6 team-only tool pages (AR Aging, Fixed Assets, Inventory, Three-Way Match, Sampling, Payroll). **Commits: 58775c7, 3dbbaed**
- **Phase LXIV:** HttpOnly Cookie Session Hardening — refresh tokens moved to `paciolus_refresh` HttpOnly/Secure/SameSite=Lax cookie (`path="/auth"`); access tokens moved to React `useRef` in-memory only; `remember_me` via cookie `max_age`; `/auth/logout` removed from CSRF exempt list; `TOKEN_KEY`/`REFRESH_TOKEN_KEY`/`REMEMBER_ME_KEY` deleted from AuthContext; Zero-Storage compliance strengthened. **Commit: 7ed278f**
- **Phase LXV:** CSP Tightening & XSS Surface Reduction — `unsafe-eval` removed from production `script-src`; per-request crypto nonce (UUID→base64) via Next.js 16 `proxy.ts` (replaces deprecated `middleware.ts`); `frame-src 'none'` and `object-src 'none'` added; static CSP removed from `next.config.js`; `style-src 'unsafe-inline'` retained (React style props → HTML `style=""` attributes; not removable without full inline-style refactor); stale AuthContext test fixed (sessionStorage→silent-refresh pattern). **Commits: 24acec3, 786e888**
- **Security Sprint:** Billing Redirect Integrity & Checkout Anti-Abuse — `success_url`/`cancel_url` removed from `CheckoutRequest` and `create_checkout_session()` signature; redirect URLs derived server-side from `FRONTEND_URL` with fail-safe guard; `model_validator(mode='before')` + `extra="ignore"` on `CheckoutRequest` silently strips injected URL fields; new `billing_redirect_injection_attempt_total` Prometheus counter (labeled by field); 7 new `TestCheckoutRedirectIntegrity` tests; 33 call sites updated across 5 test files; frontend hook + checkout page updated. **Tests: 5,564 backend + 1,345 frontend. Commit: f7347bd**
- **Security Sprint:** CSRF Model Upgrade — 4-part user-bound token format (`nonce:timestamp:user_id:HMAC`); 30-min expiry (was 60); Origin/Referer enforcement in `CSRFMiddleware`; user binding via Bearer sub extraction; `/auth/csrf` auth-guarded (`require_current_user`); `csrf_token` field in login/register/refresh `AuthResponse`; frontend reads CSRF from auth responses (eliminates extra round-trip); `fetchCsrfToken(accessToken?)` updated for edge-case re-fetch; 15 new tests (user binding × 3, origin/referer × 5, auth integration × 4, format × 3). **Tests: 5,579 backend + 1,345 frontend. Commit: 1989030**
- **Security Sprint:** Verification Token Storage Hardening — `_hash_token` → `hash_token` (public); `EmailVerificationToken.token` → `token_hash` (SHA-256 hex); `User.email_verification_token` plaintext column removed; Alembic migration ecda5f408617 (DELETE + rename + index swap + users column drop); all write paths store hash, all read paths compare by hash; 5 test files updated. **Tests: 5,579 backend + 1,345 frontend. Commit: 2343976**
- **Security Sprint:** Data Transport & Infrastructure Trust Controls — PostgreSQL TLS startup guard (production hard-fail if `sslmode` not in `{require, verify-ca, verify-full}`); `init_db()` queries `pg_stat_ssl` and logs TLS status; `is_trusted_proxy()` CIDR+exact-IP helper in `security_middleware.py` (ipaddress module); `get_client_ip()` + `_get_client_ip()` both use helper; 39 new tests + 3 updated proxy tests. **Tests: 5,618 backend + 1,345 frontend. Commit: 3d2eb13**
- **Security Sprint:** Proper Nonce-Based CSP (Phase LXV.1) — `'unsafe-inline'` removed from production `script-src`; per-request nonce (UUID→base64) set on both request headers (for Next.js server-side nonce extraction) and response headers (for browser enforcement); `'strict-dynamic'` added so dynamically-loaded chunks inherit trust without per-chunk nonces; Next.js 16 automatically injects the nonce into all inline scripts (including streaming RSC activation scripts) via regex extraction from the CSP request header; dev mode retains `'unsafe-eval'` + `'unsafe-inline'` (CSP2 fallback, ignored by modern browsers when `'strict-dynamic'` present). **Commit: 0c98a70**
- **fix: CSP Nonce Production Breakage** — Root cause: all 39 routes were `○ (Static)` (pre-rendered at build time with no nonce); the proxy set a fresh per-request nonce in the CSP response header but the cached HTML had no matching nonces in its `<script>` tags → everything blocked. Fix: (1) restored `proxy.ts` (`middleware.ts` is deprecated in Next.js 16 — file must be named `proxy.ts`, function must be named `proxy`); (2) added `await headers()` to root layout — reading from `next/headers` forces dynamic rendering for the entire route tree; all 38 page routes now `ƒ (Dynamic)` so nonces are injected into inline scripts at request time. **Commit: 1c7626f**
- **Brand Voice Alignment** — 9-file copy-only update (string literals only, no logic/styling changes): FeaturePillars factual fix ("Zero-Knowledge" → "Zero-Storage", removed false browser/client-side processing claim); section subtitle, all 3 pillar titles/taglines/descriptions; ProofStrip 4th metric → "140+ automated tests / Across all 12 tools", section label; MarketingFooter tagline → "Twelve tools. Zero data stored. Results in seconds."; about/page hero subtitle + blockquote + CTA; contact/page subtitle; pricing/page headline + subtitle; register/page subtitle; README.md opening paragraph + tech stack (Next.js 16, Python 3.12, Node 22+); USER_GUIDE.md welcome paragraph + Zero-Storage bullet. **Commit: 4929aa4**
- **Sprint 449: Analytics Metrics Assessment** — 5 new financial ratios (equity ratio, long-term debt ratio, asset turnover, inventory turnover, receivables turnover; 12→17 total), DuPont decomposition (NPM × AT × EM = ROE with verification), per-category Gini coefficients in population profile, extended CommonSizeAnalyzer (AR%, non-current assets%, AP%, opex%, operating income%), shared modules (`concentration_metrics.py` HHI, `derived_metrics.py` payroll/clearance/anomaly density). Language hardening: `health_status`→`threshold_status`, `get_overall_health`→`get_percentile_band`, `exceeds_materiality`→`exceeds_threshold`, `GoingConcernIndicator.severity`→`threshold_proximity` (evaluative→factual terminology). **Tests: 5,618 backend + 1,345 frontend. Commit: e2760da**

### Compliance Documentation
- `docs/04-compliance/SECURITY_POLICY.md` — **v2.1** (Request Integrity Controls, Rate Limit Tiers, Log Redaction subsections)
- `docs/04-compliance/PRIVACY_POLICY.md` — **v2.0**
- `docs/04-compliance/TERMS_OF_SERVICE.md` — **v2.0**
- `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` — **v2.1** (Terminology Clarity, Scope Boundaries, Control Verification subsections)
- `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md` — **v1.0** (GDPR Art. 28, controller/processor roles, SCCs, audit rights)
- `docs/04-compliance/SUBPROCESSOR_LIST.md` — **v1.0** (5 providers: Render, Vercel, Stripe, Sentry, SendGrid)
- `docs/04-compliance/INCIDENT_RESPONSE_PLAN.md` — **v1.0** (P0–P3 severity, triage SLAs, comms templates, 4 playbooks, post-mortem process)
- `docs/04-compliance/BUSINESS_CONTINUITY_DISASTER_RECOVERY.md` — **v1.0** (RTO/RPO targets, dependency map, backup strategy, 5 DR procedures)
- `docs/04-compliance/ACCESS_CONTROL_POLICY.md` — **v1.0** (roles, provisioning/deprovisioning SLAs, MFA, privileged access, quarterly reviews)
- `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md` — **v1.0** (branch protection, 10 CI checks, release process, <15-min rollback, hotfix workflow)
- `docs/04-compliance/VULNERABILITY_DISCLOSURE_POLICY.md` — **v1.0** (safe harbor, 90-day coordinated disclosure, CVSS severity, response SLAs)
- `docs/04-compliance/AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md` — **v1.0** (6 event classes, tamper resistance, retention schedule, legal hold process)

### Key Capabilities
- 17 core ratios (liquidity, solvency, profitability, efficiency, cash cycle) + 8 industry ratios across 6 benchmark industries
- A-Z lead sheet mapping, prior period comparison, adjusting entries (approval-gated workflow)
- Multi-Period TB Comparison (2-way + 3-way with budget variance)
- Journal Entry Testing: 19 automated tests (structural + statistical + advanced), Benford's Law, stratified sampling, holiday posting detection (ISA 240.A40)
- AP Payment Testing: 13 automated tests (structural + statistical + fraud indicators), duplicate detection
- Bank Statement Reconciliation: exact matching, auto-categorization, reconciliation bridge
- Financial Statements: Balance Sheet + Income Statement + Cash Flow Statement (indirect method, ASC 230/IAS 7)
- Payroll & Employee Testing: 11 automated tests (structural + statistical + fraud indicators), ghost employee detection
- Three-Way Match Validator: PO→Invoice→Receipt matching with exact PO# linkage + fuzzy fallback, variance analysis
- Revenue Testing: 16 automated tests (5 structural + 4 statistical + 3 advanced + 4 contract-aware), ISA 240 fraud risk in revenue recognition, ASC 606/IFRS 15 contract mechanics (optional)
- AR Aging Analysis: 11 automated tests (4 structural + 5 statistical + 2 advanced), ISA 500/540 receivables valuation, dual-input (TB + optional sub-ledger)
- Fixed Asset Testing: 9 automated tests (4 structural + 3 statistical + 2 advanced), IAS 16/ASC 360 PP&E assertions, depreciation/useful life analysis
- Inventory Testing: 9 automated tests (3 structural + 4 statistical + 2 advanced), IAS 2/ASC 330 inventory assertions, slow-moving/obsolescence indicators
- Statistical Sampling: ISA 530 / PCAOB AS 2315, MUS + random sampling, 2-tier stratification, Stringer bound evaluation, two-phase workflow (design → select → evaluate → Pass/Fail)
- Multi-Currency Conversion: closing-rate MVP, CSV/manual rate entry, auto-conversion in TB upload, unconverted item flagging
- Classification Validator: 6 structural COA checks (duplicates, orphans, unclassified, gaps, naming, sign anomalies) integrated into TB Diagnostics
- PDF/Excel/CSV export with workpaper signoff + JE/AP/Payroll/TWM/Revenue/AR Aging/Fixed Asset/Inventory/Bank Rec/Multi-Period/Sampling Memos (PCAOB AS 1215/2401/2501, ISA 240/500/501/505/520/530/540)
- JWT auth (HttpOnly cookie refresh tokens, in-memory access tokens), email verification, CSRF, account lockout, diagnostic zone protection
- Free/Professional/Enterprise user tiers
- Engagement Layer: Diagnostic Workspace with materiality cascade, follow-up items tracker, workpaper index, anomaly summary report, diagnostic package ZIP export, completion gate (follow-up resolution enforcement)
- TB Diagnostic Extensions: Lease Account Diagnostic (IFRS 16/ASC 842), Cutoff Risk Indicator (ISA 501), Going Concern Indicator Profile (ISA 570)
- Universal command palette (Cmd+K) with fuzzy search, tier-gated actions, recency ranking
- Platform homepage with 13-tool suite + workspace marketing

### Unresolved Tensions
| Tension | Resolution | Status |
|---------|------------|--------|
| Composite Risk Scoring | Rejected by AccountingExpertAuditor (requires ISA 315 inputs) | DEFERRED |
| Management Letter Generator | Rejected permanently (ISA 265 boundary — deficiency classification is auditor judgment) | REJECTED |

> **Detailed phase checklists:** `tasks/todo.md` (active phase) and `tasks/archive/` (completed phases)

---

## Design Mandate: Oat & Obsidian

**STRICT REQUIREMENT:** All UI development MUST adhere to the Oat & Obsidian brand identity.

### Reference
See `skills/theme-factory/themes/oat-and-obsidian.md` for the complete specification.

### Core Colors (Tailwind Tokens)
| Token | Hex | Usage |
|-------|-----|-------|
| `obsidian` | #212121 | Primary dark, headers, backgrounds |
| `oatmeal` | #EBE9E4 | Light backgrounds, secondary text |
| `clay` | #BC4749 | Expenses, errors, alerts, abnormal balances |
| `sage` | #4A7C59 | Income, success, positive states |

### Typography
| Element | Font |
|---------|------|
| Headers | `font-serif` (Merriweather) |
| Body | `font-sans` (Lato) |
| Financial Data | `font-mono` (JetBrains Mono) |

### Enforcement Rules
1. **NO** generic Tailwind colors (`slate-*`, `blue-*`, `green-*`, `red-*`)
2. **USE** theme tokens: `obsidian-*`, `oatmeal-*`, `clay-*`, `sage-*`
3. **SUCCESS** states use `sage-*` (not green-*)
4. **ERROR/EXPENSE** states use `clay-*` (not red-*)
5. **Headers** must use `font-serif` class
6. **Financial numbers** must use `font-mono` class

### Audit Penalty
UI changes that deviate from this palette without CEO approval will result in audit score deductions.
