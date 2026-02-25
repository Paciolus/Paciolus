# Report Standardization — Sprints 0–8 Details

> Archived from `tasks/todo.md` Active Phase on completion.

---

### Sprint 0: Report Standards Alignment & Freeze — COMPLETE
> Spec approved, inventory complete, 3 CEO decisions resolved.

---

### Sprint 1: Metadata Foundation (FASB vs GASB Framework Resolution)

**Objective:** Add client/entity metadata and deterministic resolution logic so every report can reliably determine which authoritative framework language to use.

**Status:** COMPLETE

#### Data Model
- [x] Add `ReportingFramework` enum (`AUTO`, `FASB`, `GASB`) to `models.py`
- [x] Add `EntityType` enum (`for_profit`, `nonprofit`, `governmental`, `other`) to `models.py`
- [x] Add 4 new columns to `Client` model: `reporting_framework`, `entity_type`, `jurisdiction_country`, `jurisdiction_state`
- [x] Update `Client.to_dict()` with new fields
- [x] Create Alembic migration `a7b8c9d0e1f2` (down_revision: `d5e6f7a8b9c0`)

#### Framework Resolver
- [x] Create `backend/shared/framework_resolution.py`
- [x] `ResolvedFrameworkResult` frozen dataclass (framework, resolution_reason, warnings)
- [x] `resolve_reporting_framework()` with 6-level precedence: explicit FASB > explicit GASB > governmental > for_profit > nonprofit+US > US default > FASB fallback
- [x] Machine-readable `ResolutionReason` enum (7 values)

#### API Layer
- [x] Update `ClientCreate` / `ClientUpdate` / `ClientResponse` schemas (4 new fields)
- [x] Update `ClientManager.create_client()` and `update_client()` to accept new fields
- [x] Refactored `_client_to_response()` helper to DRY response construction
- [x] `ResolvedFrameworkResponse` schema
- [x] New endpoint: `GET /clients/{id}/resolved-framework`

#### Tests
- [x] 25 unit tests for resolution matrix (6 explicit + 5 entity type + 2 jurisdiction + 2 fallback + 10 edge cases)
- [x] 13 API integration tests (5 create + 4 update + 1 read + 3 resolved-framework)
- [x] Validation tests (invalid enum values rejected with 400)
- [x] Existing 11 client tests still pass

#### Review
- [x] `npm run build` passes
- [x] `pytest tests/test_framework_resolution.py` — 25 passed
- [x] `pytest tests/test_clients_framework_api.py` — 13 passed
- [x] `pytest tests/test_clients_api.py` — 11 passed (backwards compatible)
- [x] Zero-Storage: new fields are metadata only (entity classification, not financial data)

#### Constraints
- No report content rewrite in this sprint
- Keep resolver pure and independently testable
- Backwards compatible — existing clients default to AUTO/other/US

---

### Sprint 2: Unified Cover Page + Brand System

**Objective:** Create shared report chrome (cover page + page header/footer) and integrate into 6 targeted generators.

**Status:** COMPLETE

#### New Files
- [x] `backend/shared/report_styles.py` — Typography & spacing tokens
- [x] `backend/shared/report_chrome.py` — Cover page + page header/footer
- [x] `backend/shared/report_standardization/__init__.py` — Public API re-exports

#### Generator Modifications
- [x] `backend/pdf_generator.py` — Diagnostic PDF (replace _find_logo, _build_classical_header, delegate footer)
- [x] `backend/shared/memo_template.py` — Template-based memos (replace build_memo_header, wire footer)
- [x] `backend/preflight_memo_generator.py` — Replace inline header
- [x] `backend/three_way_match_memo_generator.py` — Replace build_memo_header
- [x] `backend/anomaly_summary_generator.py` — Replace inline header
- [x] `backend/multi_period_memo_generator.py` — Replace build_memo_header

#### Tests
- [x] `backend/tests/test_report_chrome.py` — 24 tests (unit + regression)

#### Verification
- [x] `pytest backend/tests/test_report_chrome.py -v` — 24 passed
- [x] `pytest backend/tests/test_memo_template.py -v` — 29 passed
- [x] `pytest backend/tests/test_multi_period_memo.py -v` — 24 passed
- [x] `pytest backend/tests/test_bank_rec_memo.py -v` — 20 passed (untouched)
- [x] `npm run build` — frontend unaffected

#### Review
- Circular import resolved via lazy imports in `pdf_generator.py` (report_chrome → pdf_generator at module level; pdf_generator → report_chrome inside methods)
- `_safe_style()` helper handles both `StyleSheet1` (classical) and `dict` (memo) style containers
- Diagnostic watermark kept as class method `_draw_diagnostic_watermark()` (diagnostic-only feature)
- `build_memo_header()` in memo_base.py NOT removed — still used by untouched generators (bank rec, sampling, currency)

---

### Sprint 3: Universal Scope/Methodology with Framework-Aware Citations

**Objective:** Ensure every report includes scope statement, methodology statement, and framework-aware citation block (FASB or GASB).

**Status:** COMPLETE

#### Authoritative Content Library
- [x] Create `backend/shared/authoritative_language/` directory
- [x] `fasb_scope_methodology.yml` — FASB ASC citations per tool domain (18 tools)
- [x] `gasb_scope_methodology.yml` — GASB Statement citations per tool domain (18 tools)
- [x] Include: approved text snippets, citation metadata (body, codification/statement, topic, paragraph, status)

#### Shared Builders
- [x] Create `backend/shared/scope_methodology.py`
- [x] `build_scope_statement()` — framework-aware scope paragraph
- [x] `build_methodology_statement()` — interpretive context with non-committal language
- [x] `build_authoritative_reference_block()` — citation table
- [x] `validate_non_committal()` — reject banned assertive patterns (12 patterns)
- [x] YAML loader with LRU caching
- [x] `get_tool_content()` resolver (tool_domain + framework → ToolContent)
- [x] `AuthoritativeReference` + `ToolContent` frozen dataclasses

#### Integration — Standard Testing Memos (7 tools)
- [x] Add `tool_domain` field to `TestingMemoConfig`
- [x] Add `resolved_framework` parameter to `generate_testing_memo()` (default FASB)
- [x] Inject scope statement after existing scope data
- [x] Inject methodology statement after test table
- [x] Inject authoritative reference block before conclusion
- [x] Set `tool_domain` on all 7 configs: JE, AP, Payroll, Revenue, AR Aging, Fixed Asset, Inventory

#### Integration — Custom Pattern B Memos (11 generators)
- [x] `bank_reconciliation_memo_generator.py`
- [x] `three_way_match_memo_generator.py`
- [x] `multi_period_memo_generator.py`
- [x] `sampling_memo_generator.py` (3 functions: design + evaluation + internal)
- [x] `preflight_memo_generator.py`
- [x] `population_profile_memo.py`
- [x] `expense_category_memo.py`
- [x] `flux_expectations_memo.py`
- [x] `accrual_completeness_memo.py`
- [x] `currency_memo_generator.py`
- [x] `anomaly_summary_generator.py`

#### Non-Committal Language Guardrails
- [x] 10 approved phrases ("may indicate", "could suggest", "warrants further procedures", etc.)
- [x] 12 banned assertive patterns ("proves", "confirms", "establishes", "demonstrates that", etc.)
- [x] Tests verify all FASB/GASB scope + methodology templates pass non-committal check

#### Tests — 45 passed
- [x] 7 YAML loading tests (FASB + GASB load, body_full, unknown domain, all 18 domains have refs)
- [x] 11 framework switch tests (FASB vs GASB body, citation format, scope mentions)
- [x] 2 AuthoritativeReference dataclass tests
- [x] 15 non-committal language tests (clean text, 6 banned patterns, multiple, case-insensitive, template validation)
- [x] 6 PDF builder tests (flowable output, section label, empty refs, GASB mention)
- [x] 5 memo presence tests (JE FASB, JE GASB, bank rec GASB, sampling GASB, preflight FASB)

#### Verification
- [x] `pytest tests/test_scope_methodology.py -v` — 45 passed
- [x] `pytest tests/test_memo_template.py -v` — 29 passed (regression)
- [x] `pytest tests/test_bank_rec_memo.py -v` — 20 passed (regression)
- [x] `pytest tests/test_multi_period_memo.py -v` — 24 passed (regression)
- [x] 235 total regression tests pass across 8 existing memo test files
- [x] `npm run build` — frontend unaffected

#### Review
- `scope_methodology.py` uses `@lru_cache(maxsize=2)` for YAML loading (1 FASB + 1 GASB)
- Default framework is FASB (matches Sprint 1 resolver's fallback behavior)
- All 18 report generators accept `resolved_framework` parameter (backward-compatible default)
- YAML files are structured as controlled text artifacts — no fabricated legal claims
- Citation table uses ledger styling consistent with existing memo tables

---

### Sprint 4: Text Layout Hardening for Professional Readability

**Objective:** Eliminate customer-title truncation and layout breakage by replacing ellipsis slicing with robust wrapping and table layout behavior.

**Status:** COMPLETE

#### New Files
- [x] `backend/shared/report_layout.py` — wrap_cell(), MINIMUM_LEADING, TABLE_CELL padding constants

#### Truncation Removal (8 locations)
- [x] `multi_period_memo_generator.py` — account_name[:32]+"..." → Paragraph wrap (movements table)
- [x] `multi_period_memo_generator.py` — lead_sheet_name[:27]+"..." → Paragraph wrap (lead sheet table)
- [x] `pdf_generator.py` — account[:22]+"..." → removed (already Paragraph-wrapped downstream)
- [x] `accrual_completeness_memo.py` — account_name[:50] → removed slice
- [x] `currency_memo_generator.py` — account_name[:40] → Paragraph wrap + VALIGN TOP added
- [x] `population_profile_memo.py` — account[:40] → removed slice (already Paragraph-wrapped)
- [x] `sampling_memo_generator.py` — item_id[:20] → Paragraph wrap + VALIGN TOP added
- [x] `shared/memo_base.py` — desc[:120] → removed slice (4.3-inch column, already Paragraph-wrapped)
- [x] `preflight_memo_generator.py` — remediation[:200] → removed slice

#### Table Layout Improvements
- [x] `repeatRows=1` added to 8 tables across 6 generators (page-break header repetition)
- [x] VALIGN TOP added where missing (currency memo, sampling memo)
- [x] All wrapped cells use MemoTableCell style (leading=11, fontSize=9)

#### Tests — 18 new, 228 regression passed
- [x] `TestMultiPeriodMemoLongInputs` — 4 tests (long account, lead sheet, customer, combined)
- [x] `TestAccrualCompleteMemoLongInputs` — 2 tests (long account, long filename)
- [x] `TestCurrencyMemoLongInputs` — 2 tests (long account, combined long inputs)
- [x] `TestPopulationProfileMemoLongInputs` — 2 tests (long account, long customer)
- [x] `TestSamplingMemoLongInputs` — 2 tests (long item ID, combined)
- [x] `TestMemoBaseLongDescriptions` — 1 test (long description via memo template)
- [x] `TestReportLayoutUtility` — 5 tests (wrap_cell returns/preserves/empty/coerce/constants)

#### Verification
- [x] `pytest tests/test_report_layout_long_inputs.py -v` — 18 passed
- [x] 228 existing memo regression tests pass (9 test files)
- [x] `npm run build` — frontend unaffected

#### Review
- Security masking patterns (email, bank account, tax ID, token) intentionally preserved — these are PII/security controls, not content truncation
- CSV export `[:80]` slices in `export_testing.py` left as-is — spreadsheet readability concern, not PDF layout
- Table display caps ("... and N more") preserved — these are pagination patterns with CSV export references, not text truncation

---

### Sprint 5: Heading Readability & Typographic Consistency

**Objective:** Remove hard-to-read letter-spaced heading conventions and standardize heading hierarchy across all reports.

**Status:** COMPLETE

#### Heading Standard
- [x] Documented H1/H2/H3 hierarchy in `shared/report_styles.py` docstring
- [x] Updated `SectionHeader` style comment from "small caps effect via letterspacing" to "title case, bold serif"
- [x] Updated `create_classical_styles()` docstring (14pt with small caps → 12pt, title case)

#### pdf_generator.py — 13 Patterns Replaced
- [x] "E X E C U T I V E   S U M M A R Y" → "Executive Summary"
- [x] "R I S K   A S S E S S M E N T" → "Risk Assessment"
- [x] "E X C E P T I O N   D E T A I L S" → "Exception Details"
- [x] "W O R K P A P E R   S I G N - O F F" → "Workpaper Sign-Off" (×2)
- [x] "B A L A N C E   S H E E T" → "Balance Sheet"
- [x] "I N C O M E   S T A T E M E N T" → "Income Statement"
- [x] "C A S H   F L O W   S T A T E M E N T" → "Cash Flow Statement"
- [x] "A C C O U N T   M A P P I N G   T R A C E" → "Account Mapping Trace"
- [x] "✓   B A L A N C E D" → "✓  Balanced" (×2)
- [x] "⚠   O U T   O F   B A L A N C E" → "⚠  Out of Balance"
- [x] "✓   R E C O N C I L E D" → "✓  Reconciled"

#### Memo Generators — ALL-CAPS → Title Case (17 files)
- [x] `shared/memo_base.py` — "I. SCOPE" → "I. Scope", "II. METHODOLOGY" → "II. Methodology", "III. RESULTS SUMMARY" → "III. Results Summary", "PROOF SUMMARY" → "Proof Summary"
- [x] `shared/memo_template.py` — "KEY FINDINGS" → "Key Findings", "CONCLUSION" → "Conclusion"
- [x] `shared/scope_methodology.py` — "AUTHORITATIVE REFERENCES" → "Authoritative References"
- [x] `je_testing_memo_generator.py` — "BENFORD'S LAW ANALYSIS" → "Benford's Law Analysis"
- [x] `bank_reconciliation_memo_generator.py` — 4 headings (Scope, Reconciliation Results, Outstanding Items, Conclusion)
- [x] `three_way_match_memo_generator.py` — 5 headings (Scope, Match Results, Material Variances, Unmatched Documents, Conclusion)
- [x] `multi_period_memo_generator.py` — 5 headings (Scope, Movement Summary, Significant Account Movements, Lead Sheet Summary, Conclusion)
- [x] `sampling_memo_generator.py` — 8 headings + 2 status labels (Pass/Fail → title case)
- [x] `preflight_memo_generator.py` — 3 headings (Scope, Column Detection, Data Quality Issues)
- [x] `population_profile_memo.py` — 4 headings (Scope, Descriptive Statistics, Magnitude Distribution, Concentration Analysis)
- [x] `accrual_completeness_memo.py` — 4 headings (Scope, Accrual Accounts, Run-Rate Analysis, Narrative)
- [x] `expense_category_memo.py` — 3 headings (Scope, Category Breakdown, Period-Over-Period Comparison)
- [x] `flux_expectations_memo.py` — 5 headings (Practitioner Notice, Scope, Practitioner Expectations..., Workpaper Sign-Off, Disclaimer)
- [x] `currency_memo_generator.py` — 4 headings (Conversion Parameters, Exchange Rates Applied, Unconverted Items, Methodology & Limitations)
- [x] `anomaly_summary_generator.py` — 3 headings (Scope, Data Anomalies by Tool, For Practitioner Assessment)
- [x] `ar_aging_memo_generator.py` — 1 heading (Scope)

#### Tests — 47 new
- [x] `test_heading_consistency.py`:
  - `TestNoSpacedCapsHeadings` — 22 parametrized tests (1 per generator file)
  - `TestMemoSectionTitleCase` — 22 parametrized tests
  - `TestSectionHeaderTitleCase` — 1 test (pdf_generator)
  - `TestStatusBadgesReadable` — 1 test
  - `TestHeadingHierarchyDocumented` — 1 test

#### Verification
- [x] `pytest tests/test_heading_consistency.py -v` — 47 passed
- [x] `pytest tests/test_report_chrome.py tests/test_report_layout_long_inputs.py -v` — 42 passed (regression)
- [x] `npm run build` — frontend unaffected

#### Review
- Report title ("FINANCIAL STATEMENTS") in ClassicalTitle style intentionally left as-is — H1 titles may use uppercase per convention
- Status labels in sampling memo ("PASS — POPULATION ACCEPTED") converted to title case since they render with MemoSection style
- Legal/disclaimer wording untouched per constraints
- No analytics logic altered

---

### Sprint 6: Source Document Transparency

**Objective:** Ensure every report explicitly identifies the source document context — preferred: source document title from parsed metadata; fallback: uploaded filename.

**Status:** COMPLETE

#### Report Metadata Contract
- [x] Add `source_document_title: str = ""` and `source_context_note: str = ""` to `ReportMetadata` in `report_chrome.py`
- [x] Add `source_document_title: Optional[str] = None` and `source_context_note: Optional[str] = None` to `WorkpaperMetadata` in `export_schemas.py`

#### Rendering Rules
- [x] Update `_append_metadata_table()` in `report_chrome.py`: if title exists, show title + filename; if title missing, show filename only; never truncate
- [x] Add source identifier line in `build_scope_section()` in `memo_base.py`

#### Generator Integration (17 generators + anomaly summary skipped)
- [x] Update `generate_testing_memo()` in `memo_template.py` to accept/pass source metadata
- [x] Update all 7 standard wrapper generators (JE, AP, Payroll, Revenue, AR Aging, Fixed Asset, Inventory)
- [x] Update all custom generators (bank rec, three-way match, multi-period, sampling ×2, preflight, population profile, expense category, accrual completeness, currency, flux expectations)
- [x] Anomaly summary generator — skipped (DB-backed engagement report, no file upload concept)
- [x] Update export routes (`routes/export_memos.py`) — all 17 route handlers pass through new fields

#### Tests — 26 passed
- [x] Title present case (cover page + scope)
- [x] Title absent (filename-only fallback) case
- [x] Long-title wrapping case (no truncation)
- [x] Non-ASCII filename case (cover page + scope + end-to-end)
- [x] Context note rendering
- [x] Backwards compatibility (legacy calls without new fields)
- [x] WorkpaperMetadata schema + inheritance
- [x] End-to-end PDF generation (JE, Preflight, Bank Rec with source metadata)

#### Verification
- [x] `pytest` — 233 passed (26 new + 207 regression), 0 failed
- [x] `npm run build` — passes

#### Review
- `source_document` (existing field) remains as the uploaded filename — fully backwards compatible
- `source_document_title` appears above `source_document` as "Source Document" when present; filename shown as "Source File"
- `source_context_note` adds a "Source Context" row below source fields when present
- Scope sections: source line at top using `create_leader_dots("Source", ...)` format
- Anomaly summary generator not updated — it reads from DB engagement records, not file uploads
- Currency memo required `create_leader_dots` import addition (caught by regression tests)
- All new fields default to empty/None — zero breakage for existing API consumers

---

### Sprint 7: Signoff Section Deprecation

**Objective:** Remove "Prepared By / Reviewed By" signoff sections from default report outputs. These are evidence-support artifacts, not official workpapers. Retain opt-in for backward compatibility.

**Status:** COMPLETE

#### Shared Utility
- [x] Add `include_signoff: bool = False` to `build_workpaper_signoff()` in `shared/memo_base.py` — early return when False
- [x] Add `include_signoff: bool = False` to `WorkpaperMetadata` in `shared/export_schemas.py`
- [x] Add deprecation docstring to `prepared_by`, `reviewed_by`, `workpaper_date` fields
- [x] Add `include_signoff: bool = False` to `AuditResultInput` in `shared/schemas.py`

#### Generator Updates (21 generators)
- [x] `shared/memo_template.py` — thread `include_signoff` through to `build_workpaper_signoff()`
- [x] 10 custom memo generators — add `include_signoff` parameter, pass through
- [x] 7 standard testing memo wrappers (JE, AP, Payroll, Revenue, AR, Fixed Asset, Inventory) — thread `include_signoff`
- [x] `pdf_generator.py` — gate `_build_workpaper_signoff()` (class method), cash flow standalone, `generate_audit_report()` wrapper
- [x] `excel_generator.py` — gate 2 signoff blocks (diagnostics + financial statements) + `generate_workpaper()` wrapper
- [x] `anomaly_summary_generator.py` — remove blank signoff table (no opt-in; this was always blank)

#### API / Schema / Routes
- [x] `shared/export_schemas.py` — `include_signoff: bool = False` on `WorkpaperMetadata` + `FinancialStatementsInput`
- [x] `routes/export_memos.py` — pass `include_signoff` from schema to generator (18 routes)
- [x] `routes/export_diagnostics.py` — pass `include_signoff` for financial statements + diagnostics exports (4 routes)

#### Tests — 29 new
- [x] Schema defaults (WorkpaperMetadata, FinancialStatementsInput, AuditResultInput) — 4 tests
- [x] `build_workpaper_signoff` gate logic (default no-render, explicit False, explicit True, True+no names) — 4 tests
- [x] Default memo no-signoff (size comparison, clean generation) — 2 tests
- [x] Legacy opt-in (size comparison with/without signoff) — 1 test
- [x] Anomaly summary source audit (no signoff_data/signoff_table) — 1 test
- [x] Generator signature audit (17 modules, all generate_* have include_signoff=False) — 17 tests

#### Verification
- [x] `pytest tests/test_signoff_deprecation.py` — 29 passed
- [x] `pytest` regression — 268 passed across 9 test files (memo_template, bank_rec, multi_period, heading_consistency, financial_statements, scope_methodology, report_chrome, report_layout, source_document_transparency)
- [x] `npm run build` — passes

#### Review
- `build_workpaper_signoff()` adds `include_signoff` as keyword-only (after `*`) — backward compatible for all callers
- Anomaly summary blank signoff table removed entirely (was always empty, no legacy value)
- `generate_reference_number()` excluded from signature audit (utility, not memo generator)
- PDF compressed streams prevent direct text search — tests use size comparison instead
- All 22 route handlers updated (18 export_memos + 4 export_diagnostics)

---

### Sprint 8: QA Automation + Regression Guardrails + Rollout

**Objective:** Lock in the professional reporting standard with automated tests, validation tooling, and staged rollout verification.

**Status:** COMPLETE

#### PDF Regression Suite — `backend/tests/test_report_regression.py`
- [x] Primary diagnostic PDF tests (balanced + anomaly + signoff + source metadata) — 6 tests
- [x] Shared-template memo tests via JE (all 4 risk tiers, findings, source doc, signoff, section checks) — 9 tests
- [x] Custom memo tests (preflight, TWM, multi-period) — 6 tests
- [x] Cross-cutting standards compliance (banned language + shared chrome usage) — 36 parametrized tests
- **Total: 57 tests**

#### Structural Snapshot Tests — `backend/tests/test_report_structural_snapshots.py`
- [x] Cover page structure (PageBreak, DoubleRule, metadata table, source transparency, flowable count, title paragraph) — 6 tests
- [x] Table-heavy sections (methodology table, section heading, results table, ledger rule) — 4 tests
- [x] Disclaimer section (paragraph output, text content, domain reference) — 3 tests
- [x] Proof summary section (with data, empty result) — 2 tests
- [x] Intelligence stamp (paragraph output, brand name) — 2 tests
- [x] Scope section (content output, heading) — 2 tests
- [x] Workpaper signoff gate (default off, explicit on, on without names) — 3 tests
- **Total: 22 tests**

#### Policy Validation Script — `backend/scripts/validate_report_standards.py`
- [x] Auto-discovers 25 generator/shared files
- [x] Checks: banned assertive language, spaced-caps headings, ALL-CAPS section headings
- [x] Checks: shared chrome import usage, citation metadata (with template delegation awareness)
- [x] Exit code 0 on pass, 1 on violation — CI-compatible

#### CI Integration — `.github/workflows/ci.yml`
- [x] New `report-standards` job: Python 3.12, installs deps, runs `validate_report_standards.py`
- [x] Blocking gate (fails build on any violation)

#### Rollout Playbook — `docs/runbooks/report-standardization-rollout.md`
- [x] Pilot report list (10 reports across 4 categories with priority ranking)
- [x] Acceptance checklist (structural checks + content standards + framework citations + source transparency + signoff)
- [x] Rollback procedure (trigger conditions + 5-step revert + no-rollback safe zone)
- [x] Owner signoff workflow (roles, process, decision gate, signoff record template)
- [x] CI integration documentation

#### Verification
- [x] `pytest tests/test_report_regression.py` — 57 passed
- [x] `pytest tests/test_report_structural_snapshots.py` — 22 passed
- [x] `python scripts/validate_report_standards.py` — all checks passed (25 files scanned)
- [x] Existing report tests: 147 passed (report_chrome + heading_consistency + signoff_deprecation + report_layout + memo_template)
- [x] `npm run build` — passes
- [x] Zero regressions in existing test suite

#### Review
- Structural snapshots use ReportLab flowable inspection (not pixel comparison) — deterministic, CI-friendly
- Banned language check in regression tests only flags patterns inside string literals (avoids false positives from pattern definitions)
- Policy validator recognizes template delegation: generators that import `memo_template`/`generate_testing_memo` pass citation checks without direct `build_authoritative_reference_block` imports
- Sprint 0–7 standards now have 3 enforcement layers: pytest regression tests (79 new), policy validation script (CI job), acceptance checklist (manual pilot review)
