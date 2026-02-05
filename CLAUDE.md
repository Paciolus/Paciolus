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

**AUDIT FINDING (2026-02-04):** Only 3 commits exist for 24 sprints of work. Each sprint should have at least one commit to build proper history trail.

**FAILURE TO FOLLOW THIS PROTOCOL WILL RESULT IN AUDIT SCORE PENALTIES.**

---

## Current Project State

**Project:** Paciolus — Trial Balance Diagnostic Intelligence Platform for Financial Professionals
**Phase:** Phase IV Active — Sprint 52 Complete, Adjusting Entry Module
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** 🟢 PRODUCTION READY
**Version:** 0.42.0
**Audit Score:** 8.2/10 (Professional Accounting Evaluation 2026-02-04)
**Test Coverage:** 584 backend tests (105 ratio_engine + 61 industry_ratios + 79 audit_engine + 68 benchmark_engine + 32 benchmark_api + 33 security + 45 adjusting_entries + 41 prior_period + 77 lead_sheet + 43 other)
**Ratios Available:** 8 core + 8 industry (Manufacturing: 3, Retail: 2, Professional Services: 3)
**Benchmark Industries:** 6 (Retail, Manufacturing, Professional Services, Technology, Healthcare, Financial Services)
**Benchmark API:** 4 endpoints (industries, sources, {industry}, compare)
**Benchmark UI:** PercentileBar, BenchmarkCard, BenchmarkSection, industry selector + useBenchmarks hook
**Dashboard:** All 8 ratios visible with tooltips, trends, industry metrics, rolling window analysis, benchmark comparison
**Settings:** Separated User Profile Settings + Practice Settings pages
**Security:** Security headers, CSRF protection, Account lockout mechanism
**Lead Sheets:** A-Z lead sheet mapping with 100+ keyword rules, UI grouping
**Prior Period:** Side-by-side comparison with variance analysis, period saving
**Adjusting Entries:** Multi-line journal entries with status workflow, apply to TB
**Next Priority:** Sprint 53 - DSO Ratio + Workpaper Fields (Phase IV)

### Phase II Overview (Sprints 25-39) — COMPLETE
| Block | Sprints | Theme | Agent Lead |
|-------|---------|-------|------------|
| Foundation | 25-27 | Test Suite + Ratio Expansion | QualityGuardian + BackendCritic |
| User Experience | 28-30 | Dashboard + Classification | FrontendExecutor + FintechDesigner |
| Professional | 29, 31 | IFRS/GAAP + Materiality | ProjectAuditor + BackendCritic |
| Trends | 32-33 | Historical Analysis + Viz | BackendCritic + FintechDesigner |
| Industry | 34-35 | Sector-Specific Ratios | BackendCritic + FrontendExecutor |
| Advanced | 36-38 | Rolling Windows + Batch | FrontendExecutor + QualityGuardian |
| Phase III Prep | 39-40 | Benchmark RFC | BackendCritic + ProjectAuditor |

### Phase III Overview (Sprints 41-47) — ACTIVE
> **Source:** Agent Council Discussion (2026-02-04) + Accounting Expert Auditor

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 41 | Suspense Account Detector | 2/10 | BackendCritic + FrontendExecutor | ✅ |
| 42 | Concentration Risk + Rounding Anomaly | 4-5/10 | BackendCritic + FintechDesigner | ✅ |
| 43 | Balance Sheet Validator | 1/10 | BackendCritic | ✅ |
| 44 | Benchmark Schema Implementation | 3/10 | BackendCritic | ✅ |
| 45 | Benchmark Comparison Engine | 4/10 | BackendCritic + QualityGuardian | ✅ |
| 46 | Benchmark Frontend Components | 3/10 | FrontendExecutor + FintechDesigner | ✅ |
| 47 | Benchmark Integration & Testing | 2/10 | QualityGuardian | ✅ |

**Phase III Complete.** All 7 sprints delivered. Deferred to later: Contra-Account Validator (high complexity, industry-specific)

### Phase IV Overview (Sprints 48-55) — ACTIVE
> **Source:** Agent Council Discussion (2026-02-05) + Accounting Expert Auditor Review (2026-02-05)
> **Reprioritized:** Based on auditor findings - professional adoption features first

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 48 | User Profile Settings + Page Separation | 3/10 | FrontendExecutor + BackendCritic | ✅ |
| 49 | Security Hardening (Headers, CSRF, Lockout) | 4/10 | BackendCritic + QualityGuardian | ✅ |
| 50 | **Lead Sheet Mapping** | 5/10 | BackendCritic + FrontendExecutor | ✅ |
| 51 | **Prior Period Comparison** | 4/10 | BackendCritic + FintechDesigner | ✅ |
| 52 | **Adjusting Entry Module** | 6/10 | BackendCritic + FrontendExecutor | ✅ |
| 53 | DSO Ratio + Workpaper Fields | 3/10 | BackendCritic + FintechDesigner | Planned |
| 54 | Export Enhancement (CSV, Custom Templates) | 3/10 | BackendCritic + FrontendExecutor | Planned |
| 55 | Frontend Test Foundation (Jest/RTL) | 4/10 | QualityGuardian + FrontendExecutor | Planned |

**Phase IV Focus:** Professional Adoption Features (Lead Sheets, Prior Period, Adjustments), then Polish

**Auditor Score Impact:**
- Current: 7.8/10
- With Sprints 50-52: **9.0/10** (professional adoption ready)

### Completed Features
- Zero-Storage trial balance analysis
- Streaming processing for large files (50K+ rows)
- Materiality thresholds with Material/Immaterial classification
- Environment configuration with hard-fail protection
- Reactive UI with debounced threshold updates
- Automated Test Suite (Day 8)
- Account Classification System with Core 80 keywords (Day 9)
- Paciolus Brand Foundation with Oat & Obsidian theme (Day 9.1)
- Intelligent Column Detection with confidence scoring (Day 9.2)
- Manual Column Mapping Modal for non-standard CSVs (Day 9.2)
- Surgical Risk Dashboard with animated Anomaly Cards (Day 10)
- "Premium Restraint" design: Clay Red left-border accents (Day 10)
- framer-motion staggered animations for smooth UX (Day 10)
- Multi-Sheet Excel Support with Workbook Inspector (Day 11)
- Summation Consolidation for multi-sheet trial balances (Day 11)
- Two-phase upload flow: inspect → select → audit (Day 11)
- PDF Export with Zero-Storage streaming (Day 12)
- ReportLab PDF generation with Oat & Obsidian palette (Day 12)
- JWT Authentication with SQLite user database (Day 13)
- "Obsidian Vault" Login/Register pages with premium animations (Day 13)
- AuthContext for centralized auth state management (Day 13)
- ProfileDropdown component for logged-in users (Day 13)
- Password strength indicator with 5-requirement checklist (Day 13)
- Activity Logging with GDPR/CCPA-compliant metadata storage (Day 14)
- Heritage Timeline UI with ledger aesthetic (Day 14)
- SHA-256 filename hashing for privacy protection (Day 14)
- Quick Re-Run functionality with Zero-Storage reassurance (Day 14)
- **Sprint 15 Stability Fixes:**
  - Fixed AuditResults referential loop with useRef deep comparison
  - Tier 1 Skeleton Loaders with shimmer animation for layout stability
  - PDF Generator "Get or Create" pattern for style collision fix
  - Semantic color enforcement (Clay #BC4749 for errors, Sage #4A7C59 for success)
- **Sprint 16 Client Infrastructure:**
  - Client SQLAlchemy model with multi-tenant isolation (user_id FK)
  - Industry enum with 12 standard categories
  - ClientManager with full CRUD operations
  - 6 REST API endpoints for client management
  - useClients React hook for frontend state
  - Zero-Storage compliance: only client metadata stored, never financial data
- **Sprint 17 Portfolio Dashboard:**
  - /portfolio page with responsive client card grid (1-3 columns)
  - ClientCard with "Premium Bound Ledger" aesthetic
  - CreateClientModal with Tier 2 Form Validation
  - Tier 1 staggered entrance animations (40ms delay)
  - Button micro-interactions (translateY hover, scale tap)
- **Sprint 18 Diagnostic Fidelity:**
  - Global terminology: "Audit" → "Diagnostic/Assessment/Intelligence"
  - PDF filename: [Client]_[Domain]_Diagnostic_[Date].pdf
  - PDF logo fixed: LightBG variant, preserveAspectRatio
  - PDF text: Paragraph wrapping for anomaly descriptions (no cutoff)
  - Legal disclaimer on every PDF page
  - UI disclaimer banner in results view
  - "Export Diagnostic Summary" button (was "Download PDF Report")
- **Sprint 19 Analytics & Ratio Intelligence:**
  - ratio_engine.py: RatioEngine, CommonSizeAnalyzer, VarianceAnalyzer classes
  - 4 core financial ratios: Current, Quick, Debt-to-Equity, Gross Margin
  - DiagnosticSummary model for storing aggregate category totals
  - Variance Intelligence: compare current vs previous stored metadata
  - MetricCard component with Tier 2 semantic colors (Sage/Clay)
  - KeyMetricsSection dashboard with Tier 1 staggered animations
  - Zero-Storage variance: only aggregate totals compared, never raw data
  - 3 new API endpoints for diagnostic summary storage/retrieval
- **Sprint 20 Document Hardening & Loop Resolution:**
  - Deep-Hash Comparison state guard for UI stability
  - computeAuditInputHash() prevents unnecessary re-audits
  - Excel Workpaper Generator (openpyxl) with 4-tab structure
  - Multi-tab workpaper: Summary, Standardized TB, Flagged Anomalies, Key Ratios
  - /export/excel endpoint with Zero-Storage streaming
  - Terminology scrub: "Trial Balance Audits" → "Trial Balance Diagnostics"
  - Oat & Obsidian theme applied to Excel workpapers
- **Sprint 21 Customization & Practice Settings:**
  - practice_settings.py: MaterialityFormula, PracticeSettings, ClientSettings, MaterialityCalculator
  - 4 materiality formula types: fixed, percentage_of_revenue, percentage_of_assets, percentage_of_equity
  - Priority chain: session override → client settings → practice settings → system default
  - /settings page with Tier 2 Form Validation (Oat & Obsidian)
  - MaterialityFormulaEditor with formula type dropdown and live preview
  - useSettings React hook for settings API integration
  - Settings prepopulate Diagnostic view threshold on page load
  - 6 new API endpoints for practice/client settings management
  - Zero-Storage: formulas stored, financial data never stored
- **Sprint 22 Live Sensitivity Tuning & UI Hardening:**
  - SensitivityToolbar "Control Surface" component for real-time threshold adjustment
  - Display mode toggle: Strict (material only) vs Lenient (all anomalies)
  - Inline edit mode with framer-motion transitions
  - Hash-guard integration for efficient recalculation
  - Fixed dropzone "ghost click" issue with pointer-events control
  - Global terminology: "Fractional CFO" → "Financial Professional"
  - Documented "Contextual Parameter Tuning" UX pattern in dev-log.md
- **Sprint 23 The Marketing Front & Brand Hardening:**
  - FeaturePillars component: Three key value propositions with Tier 1 animations
  - ProcessTimeline component: Visual transformation flow (Upload → Analyze → Export)
  - Redesigned landing page with marketing sections between Hero and Diagnostic Zone
  - Removed redundant Features Section (replaced by FeaturePillars)
  - Fixed Sprint 17 Industry type mismatch (ClientCreateInput type)
  - Fixed framer-motion type assertion in CreateClientModal
  - Documented "Brand-Integrated Feature Set" in dev-log.md
- **Sprint 24 Production Deployment Prep (FINAL SPRINT):**
  - Backend Dockerfile: Multi-stage Python 3.11-slim build with Gunicorn
  - Frontend Dockerfile: Multi-stage Node 20-alpine build with standalone output
  - docker-compose.yml: Local-to-cloud development orchestration
  - secrets_manager.py: Production credential management (AWS/GCP/Azure support)
  - Enhanced CORS policy: Wildcard blocking and HTTPS validation in production
  - Next.js standalone output mode for optimized Docker deployments
  - DEPLOYMENT.md: Comprehensive guide for Vercel, Render, DigitalOcean
  - Documented "Production-Grade Stateless Infrastructure" in dev-log.md
- **Sprint 25 Foundation Hardening:**
  - Comprehensive ratio_engine test suite (47 tests)
  - Per-sheet column detection for multi-sheet audits
  - Column order mismatch warnings for user awareness
  - 82 total backend tests
- **Sprint 26 Profitability Ratios:**
  - Net Profit Margin ratio: (Revenue - Total Expenses) / Revenue
  - Operating Margin ratio: (Revenue - COGS - Operating Expenses) / Revenue
  - OPERATING_EXPENSE_KEYWORDS (30+ terms) for expense classification
  - NON_OPERATING_KEYWORDS to exclude interest/tax/extraordinary
  - 96 total backend tests (61 ratio_engine)
- **Sprint 27 Return Metrics:**
  - Return on Assets (ROA): Net Income / Total Assets
  - Return on Equity (ROE): Net Income / Total Equity
  - 8 ratios now available for comprehensive analysis
  - 109 total backend tests (74 ratio_engine)
- **Sprint 28 Ratio Dashboard Enhancement:**
  - All 8 ratios visible in KeyMetricsSection (Core 4 + Advanced 4)
  - 2-column responsive grid layout (1 col mobile, 2 col desktop)
  - Formula tooltips on hover with formula + description
  - Collapsible "Advanced Ratios" section with framer-motion
  - Trend indicators (↑↓→) with animated entrance
  - Animated value transitions on ratio changes
- **Sprint 29 Classical PDF Enhancement — "Renaissance Ledger":**
  - Complete pdf_generator.py rewrite with institutional aesthetic
  - ClassicalColors palette: GOLD_INSTITUTIONAL, OATMEAL_PAPER, LEDGER_RULE
  - DoubleRule and LedgerRule custom Flowables
  - Leader dots for financial summaries: `Total Debits ... $1,234,567.89`
  - Pacioli watermark at 4% opacity, 45° rotation
  - Section ornaments: fleuron (❧) and diamond (◆)
  - Ledger-style tables: horizontal rules only, left accent border
  - Classical date format: "4th February 2026" with ordinal suffix
  - Reference numbers: PAC-YYYY-MMDD-NNN format
  - Status badge seal with checkmark/warning symbols
  - Footer with Pacioli motto: "Particularis de Computis et Scripturis"
- **Sprint 30 IFRS/GAAP Documentation:**
  - docs/STANDARDS.md: Comprehensive framework comparison document
  - Enhanced ratio_engine.py docstrings with IFRS/GAAP notes for all 8 ratios
  - Enhanced classification_rules.py with framework-specific comments
  - MetricCard tooltips now display IFRS/GAAP standard notes
  - Coverage: LIFO, revaluations, R&D capitalization, leases, provisions
- **Sprint 31 Classification Intelligence:**
  - Levenshtein distance fuzzy matching for misspelled account names
  - Top 3 alternative suggestions when confidence < 50%
  - ClassificationSuggestion dataclass with category, confidence, reason
  - "Did you mean?" collapsible UI in AnomalyCard
  - One-click suggestion acceptance
  - Zero-Storage compliant (session-only mappings)
- **Sprint 32 Weighted Materiality by Account Type:**
  - WeightedMaterialityConfig with per-category weights (asset, liability, equity, revenue, expense)
  - WeightedMaterialityEditor component for settings UI
  - Weight multiplier inverse: higher weight = lower threshold (more scrutiny)
  - Zero-Storage compliant (weights are configuration only)
- **Sprint 33 Trend Analysis Foundation:**
  - PeriodType enum (monthly, quarterly, annual) in models.py
  - DiagnosticSummary extended with period_date, period_type, and 4 additional ratios
  - TrendAnalyzer class for multi-period comparison
  - PeriodSnapshot, TrendPoint, TrendSummary dataclasses
  - GET /clients/{client_id}/trends API endpoint
  - Period-over-period change calculation with direction (POSITIVE/NEGATIVE/NEUTRAL)
  - 14 new TrendAnalyzer tests (147 total backend tests)
  - Zero-Storage compliant (metadata only)
- **Sprint 34 Trend Visualization:**
  - recharts library integration for lightweight charting
  - TrendSparkline component with animated line drawing
  - TrendSparklineMini for compact inline display
  - TrendSummaryCard with min/max/avg statistics
  - TrendSection dashboard component with collapsible categories
  - useTrends hook for API integration
  - Oat & Obsidian chart palette (sage/clay/obsidian colors)
  - Responsive 2-column grid layout
  - framer-motion staggered entrance animations
- **Sprint 35 Industry Ratio Foundation:**
  - industry_ratios.py with factory pattern architecture
  - IndustryRatioCalculator abstract base class
  - ManufacturingRatioCalculator: Inventory Turnover, DIO, Asset Turnover
  - RetailRatioCalculator: Inventory Turnover (retail benchmarks), GMROI
  - GenericIndustryCalculator fallback for unmapped industries
  - INDUSTRY_CALCULATOR_MAP for type-safe dispatching
  - IndustryRatioResult with benchmark_note field
  - IndustryTotals extends CategoryTotals with average_inventory, fixed_assets
  - 44 new industry ratio tests (191 total backend tests)
  - IFRS/GAAP notes for inventory valuation methods
- **Sprint 36 Industry Ratio Expansion:**
  - ProfessionalServicesRatioCalculator: Revenue/Employee, Utilization Rate, Revenue/Hour
  - Extended IndustryTotals with employee_count, billable_hours, total_hours
  - Placeholder messaging ("Data Required") for metrics needing additional data
  - GET /clients/{id}/industry-ratios API endpoint
  - IndustryMetricsSection frontend component with industry icons
  - Benchmark tooltips with industry context
  - useIndustryRatios hook for API integration
  - 61 industry ratio tests (208 total backend tests)
  - Oat & Obsidian theme compliance
- **Sprint 37 Rolling Window Analysis:**
  - RollingWindowAnalyzer class with 3/6/12 month window support
  - MomentumType enum: ACCELERATING, DECELERATING, STEADY, REVERSING
  - Momentum confidence calculation based on rate consistency
  - RollingAverage and MomentumIndicator dataclasses
  - GET /clients/{id}/rolling-analysis API endpoint
  - RollingWindowSection component with period selector
  - useRollingWindow hook for API integration
  - 17 new rolling window tests (225 total backend tests)
  - Momentum indicators with trend direction display
- **Sprint 38 Batch Upload Foundation:**
  - `types/batch.ts`: FileStatus, BatchStatus, FileQueueItem type definitions
  - FileError codes: INVALID_TYPE, FILE_TOO_LARGE, PROCESSING_FAILED, CANCELLED
  - File validation utilities: isValidFileType, isValidFileSize, formatFileSize
  - FILE_SIZE_LIMITS: 50MB per file, 200MB total, 10 files max
  - `BatchUploadContext.tsx`: Reducer-based state management with queue operations
  - Actions: addFiles, removeFile, clearQueue, processAll, cancelProcessing, retryFailed
  - `useBatchUpload.ts`: Convenience hook with BatchStats and derived state
  - Zero-Storage compliance: All files in React state (memory only)
- **Sprint 39 Batch Upload UI:**
  - `BatchDropZone.tsx`: Multi-file drag-and-drop with validation feedback
  - `FileQueueItem.tsx`: File row with status badge, progress bar, remove button
  - `FileQueueList.tsx`: Scrollable queue with staggered animations, empty state
  - `BatchProgressBar.tsx`: Overall progress with animated gradient bar
  - `BatchUploadControls.tsx`: Process All, Clear Queue, Cancel, Retry buttons
  - `BatchUploadPanel.tsx`: Composite panel combining all batch UI elements
  - Zero-Storage notice with privacy reassurance
- **Sprint 40 Benchmark Framework RFC:**
  - `docs/BENCHMARKS.md`: Comprehensive RFC document (700+ lines)
  - Data schema: IndustryBenchmark, BenchmarkComparison, BenchmarkSet models
  - Sources: RMA, SEC EDGAR, BLS, FRED with licensing notes
  - Percentile calculation with linear interpolation algorithm
  - Zero-Storage compliance: Benchmarks as reference data (not client data)
  - API design: /benchmarks/{industry}, /benchmarks/compare endpoints
  - Frontend components: BenchmarkCard, PercentileBar mockups
  - Phase III roadmap: Sprints 41-47 implementation plan
- **Sprint 41 Suspense Account Detector:**
  - SUSPENSE_KEYWORDS list in classification_rules.py (25+ keywords)
  - Keyword categories: suspense, clearing, unallocated, unidentified, pending, temporary
  - Confidence-weighted detection with threshold (0.60 minimum)
  - detect_suspense_accounts() method in StreamingAuditor class
  - Integration with both single-file and multi-sheet audit pipelines
  - risk_summary includes suspense_account anomaly type count
  - medium_severity classification for immaterial suspense accounts
  - Merged handling for accounts that are both abnormal AND suspense
  - 17 new suspense detection tests (242 total backend tests)
  - Zero-Storage compliant (detection only, no data stored)
  - GAAP/IFRS notes: Both frameworks require proper classification
- **Sprint 42 Concentration Risk + Rounding Anomaly:**
  - **Concentration Risk Detection:**
    - CONCENTRATION_THRESHOLD_HIGH (50%) and CONCENTRATION_THRESHOLD_MEDIUM (25%)
    - detect_concentration_risk() method analyzes accounts by category
    - Flags accounts representing large percentage of category total
    - Configurable minimum category total ($1,000) to avoid false positives
    - GAAP/IFRS notes: ASC 275 / IFRS 7 disclosure requirements
  - **Rounding Anomaly Detection:**
    - ROUNDING_PATTERNS for $100K, $50K, $10K round amounts
    - detect_rounding_anomalies() method with severity levels
    - ROUNDING_EXCLUDE_KEYWORDS for legitimate round amounts (loans, stock, etc.)
    - Minimum threshold ($10,000) and max anomalies (20) to reduce noise
    - Sorted by amount (highest first) for prioritization
  - risk_summary includes concentration_risk and rounding_anomaly counts
  - 21 new detection tests (263 total backend tests)
  - Zero-Storage compliant (analysis only, no data stored)
- **Sprint 43 Balance Sheet Validator:**
  - validate_balance_sheet_equation() standalone function
  - Validates: Assets = Liabilities + Equity
  - Severity levels: high (>$10K), medium ($1K-$10K), low (<$1K)
  - Integration with single-file and multi-sheet audit pipelines
  - balance_sheet_validation object added to audit results
  - risk_summary includes balance_sheet_imbalance count when applicable
  - Actionable recommendations based on imbalance direction
  - 10 new validator tests (273 total backend tests)
  - GAAP/IFRS compliant (fundamental double-entry bookkeeping)
- **Sprint 44 Benchmark Schema Implementation:**
  - benchmark_engine.py: Complete benchmark framework
  - IndustryBenchmark dataclass with percentile distribution (p10-p90)
  - BenchmarkComparison dataclass with percentile position and interpretation
  - BenchmarkSet dataclass for industry-specific benchmark collections
  - RATIO_DIRECTION mapping (higher_better vs lower_better)
  - calculate_percentile() with linear interpolation algorithm
  - generate_interpretation() for human-readable comparisons
  - 6 industry benchmarks: Retail, Manufacturing, Professional Services, Technology, Healthcare, Financial Services
  - 8+ ratios per industry with source attribution
  - 68 new benchmark tests (357 total backend tests)
  - Zero-Storage compliant: Benchmarks as reference data (persistent), comparisons ephemeral
- **Sprint 45 Benchmark Comparison Engine:**
  - 4 new API endpoints in main.py
  - GET /benchmarks/industries - List available industries (public)
  - GET /benchmarks/sources - Source attribution and disclaimers (public)
  - GET /benchmarks/{industry} - Full benchmark set for industry (public)
  - POST /benchmarks/compare - Compare client ratios to benchmarks (authenticated)
  - Pydantic response models: BenchmarkSetResponse, BenchmarkComparisonResponse
  - Overall score calculation with health assessment
  - Rate limiting on compare endpoint
  - 32 new API tests with async httpx client (389 total backend tests)
  - Zero-Storage compliant: Client ratios ephemeral, benchmarks are reference data
- **Sprint 46 Benchmark Frontend Components:**
  - useBenchmarks hook for API integration (fetchIndustries, fetchBenchmarks, compareToBenchmarks)
  - PercentileBar component with animated position indicator, quartile markers, color-coded health
  - BenchmarkCard component with percentile display, interpretation, expandable benchmark values
  - BenchmarkSection component with overall score, health badge, collapsible grid, disclaimer
  - Oat & Obsidian theme compliance throughout
  - framer-motion animations for entrance and state transitions
  - Zero-Storage compliant: Display components only, no data persistence
- **Sprint 47 Benchmark Integration & Testing:**
  - Industry selector dropdown integrated into diagnostic results flow
  - Automatic ratio extraction from audit results (extractRatiosForBenchmark utility)
  - useBenchmarks hook wired to trigger comparison on industry selection
  - BenchmarkSection rendered after KeyMetricsSection in both guest and authenticated views
  - Industries fetched automatically when audit completes
  - State cleanup when starting new audit (clearBenchmarks, reset selectedIndustry)
  - End-to-end flow: Upload file → Audit → Select Industry → View Benchmark Comparison
  - Zero-Storage compliant: Benchmark comparisons computed in real-time, never persisted
- **Sprint 48 User Profile Settings + Page Separation:**
  - User model extended with `name` field for display name
  - Database migration script for adding name column to existing databases
  - UserProfileUpdate and PasswordChange Pydantic schemas in auth.py
  - PUT /users/me endpoint for updating profile (name, email)
  - PUT /users/me/password endpoint for password changes with current password verification
  - AuthContext extended with updateProfile() and changePassword() methods
  - ProfileUpdate and PasswordChange TypeScript interfaces
  - `/settings` hub page with two navigation cards (Profile Settings, Practice Settings)
  - `/settings/profile` page: display name, email, password change, account info
  - `/settings/practice` page: materiality formulas, weighted thresholds, export preferences
  - ProfileDropdown updated with separate links for Profile and Practice Settings
  - WorkspaceHeader shows user name if available (falls back to email prefix)
  - Clean separation: User Settings (personal) vs Practice Settings (business)
  - Zero-Storage compliant: Profile data in database, never includes financial data
- **Sprint 49 Security Hardening:**
  - SecurityHeadersMiddleware: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy
  - Production-only headers: Strict-Transport-Security (HSTS), Content-Security-Policy
  - CSRF protection with double-submit cookie pattern
  - GET /auth/csrf endpoint for CSRF token generation
  - Account lockout mechanism: 5 failed attempts = 15 minute lockout
  - Lockout status returned in failed login responses
  - Failed attempt tracking with automatic reset on success
  - Privacy-compliant IP hashing for security logging
  - 33 new security tests covering all new functionality
  - Zero-Storage compliant: Lockout tracking is in-memory only
- **Sprint 50 Lead Sheet Mapping:**
  - lead_sheet_mapping.py: LeadSheet enum (A-Z), assign_lead_sheet(), group_by_lead_sheet()
  - 15 lead sheet categories: Cash (A), Receivables (B), Inventory (C), Prepaid (D), Fixed Assets (E), Intangibles (F), Payables (G), Deferred Revenue (H), Long-term Debt (I), Other Liabilities (J), Equity (K), Revenue (L), COGS (M), Operating Expenses (N), Other Income/Expense (O), through Unclassified (Z)
  - 100+ keyword rules for automatic account assignment
  - Category-based fallback for unmatched accounts (Asset→A, Liability→G, etc.)
  - LeadSheetAssignment dataclass with confidence scoring and match reasoning
  - group_by_lead_sheet() creates summaries with totals, net balances, account counts
  - Custom override support for client-specific mappings
  - GET /audit/lead-sheets/options endpoint for UI dropdowns
  - Lead sheet grouping automatically added to audit response
  - LeadSheetSection and LeadSheetCard frontend components
  - Category filter dropdown for filtering by asset/liability/equity/revenue/expense
  - Collapsible drill-down to view individual accounts per lead sheet
  - 77 comprehensive backend tests
  - Zero-Storage compliant: Grouping computed at audit time, never stored
- **Sprint 51 Prior Period Comparison:**
  - prior_period_comparison.py: compare_periods(), calculate_variance(), generate_period_label()
  - CategoryVariance, RatioVariance, DiagnosticVariance, PeriodComparison dataclasses
  - Variance calculation for balance sheet, income statement, ratios, and diagnostic metrics
  - Significance flagging (>10% or >$10K variance)
  - Direction indicators (increase/decrease/unchanged) with color coding
  - period_label field added to DiagnosticSummary model
  - POST /clients/{id}/periods endpoint for saving periods
  - GET /clients/{id}/periods endpoint for listing saved periods
  - POST /audit/compare endpoint for comparing current to prior
  - ComparisonTable component with collapsible sections
  - ComparisonSection component with period selector and save modal
  - usePriorPeriod hook for API integration
  - 41 comprehensive backend tests
  - Zero-Storage compliant: Only aggregate totals stored, comparisons computed on-demand
- **Sprint 52 Adjusting Entry Module:**
  - adjusting_entries.py: AdjustingEntry, AdjustmentLine, AdjustmentSet, AdjustedTrialBalance dataclasses
  - AdjustmentType enum (accrual, deferral, estimate, error_correction, reclassification, other)
  - AdjustmentStatus enum (proposed, approved, rejected, posted)
  - apply_adjustments() function with multi-entry support
  - Debit = Credit validation enforced at entry level
  - 10 API endpoints for full CRUD + apply operations
  - POST /audit/adjustments - Create adjusting entry
  - GET /audit/adjustments - List entries with status/type filters
  - PUT /audit/adjustments/{id}/status - Update entry status
  - POST /audit/adjustments/apply - Apply entries to trial balance
  - AdjustmentEntryForm component with dynamic multi-line input
  - AdjustmentList component with expandable details and status actions
  - AdjustmentSection component (main collapsible section)
  - useAdjustments hook for API integration
  - 45 comprehensive backend tests
  - Zero-Storage compliant: Adjustments stored in session memory only

### Unresolved Tensions
| Tension | Resolution Sprint | Status |
|---------|-------------------|--------|
| Diagnostic zone protection disabled | Post-Phase IV | Ready to enable |
| No multi-period trend analysis | 32-33 | ✅ Complete |
| No industry-specific ratios | 34-36 | ✅ Complete (Manufacturing, Retail, Services) |
| No batch multi-file upload | 38-39 | ✅ Complete (Foundation + UI) |
| No benchmark comparison | 40-47 | ✅ Complete (Schema, API, UI, Integration) |
| No suspense account detection | 41 | ✅ Complete |
| No concentration/rounding detection | 42 | ✅ Complete |
| No balance sheet validation | 43 | ✅ Complete |
| No user profile management | 48 | ✅ Complete |
| No rate limiting/CSRF protection | 49 | ✅ Complete |
| No lead sheet mapping | 50 | ✅ Complete |
| No prior period comparison | 51 | ✅ Complete |
| No adjusting entry support | 52 | ✅ Complete |
| No DSO ratio | 53 | Planned |
| No frontend test coverage | 55 | Planned |

### Project Status
**Phase I Complete (24 Sprints).** Paciolus is production-ready.
**Phase II Complete (15 Sprints).** All planned features delivered.
**Phase III Complete (Sprints 41-47).** All benchmark features delivered.
**Phase IV Active (Sprint 50+).** Professional adoption features in progress.

### Auditor Assessment (2026-02-05)
**Score: 7.8/10** — "Well-architected tool with strong technical execution"
**Projected Score with Sprints 50-52: 9.0/10** — Professional adoption ready

### Agent Council Summary (2026-02-05) — Phase IV Planning
6 agents evaluated Phase IV priorities. Consensus:

**Sprint 48 (Complete):** User Profile Settings + Page Separation
- CEO identified missing feature: no way for users to update display name
- Agent Council recommended separating User Settings from Practice Settings
- FrontendExecutor: "Clean separation improves information architecture"
- BackendCritic: "Profile endpoints follow REST conventions with proper auth"
- FintechDesigner: "Settings hub provides clear navigation hierarchy"

**Sprint 49 (Complete):** Security Hardening
- BackendCritic: Security headers middleware with production-aware configuration
- QualityGuardian: CSRF protection using double-submit cookie pattern
- BackendCritic: Account lockout mechanism (5 attempts = 15 min lockout)
- QualityGuardian: 33 new security tests for comprehensive coverage
- Zero-Storage: Lockout tracking in-memory, no persistent security state

**Phase IV Roadmap (Reprioritized per Accounting Expert Auditor):**

| Priority | Sprint | Feature | Rationale |
|----------|--------|---------|-----------|
| ✅ | 49 | Security Hardening | Complete |
| **HIGH** | 50 | Lead Sheet Mapping | "Auditors think in lead sheets, not raw account lists" |
| **HIGH** | 51 | Prior Period Comparison | "Every audit compares to prior year" |
| **HIGH** | 52 | Adjusting Entry Module | "What-if analysis and adjustment summary" |
| MEDIUM | 53 | DSO Ratio + Workpaper Fields | Prepared/Reviewed fields, missing ratio |
| LOW | 54 | Export Enhancement | Useful but not differentiating |
| LOW | 55 | Frontend Tests | Internal quality (necessary but not user-facing) |

**Deferred:**
- Contra-Account Validator (requires industry-specific accounting rules)
- Print Styles (auditor: "Print is legacy")

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