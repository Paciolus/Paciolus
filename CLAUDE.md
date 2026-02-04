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
**Phase:** Phase II Active — Sprint 28 Complete, Sprint 29 Next
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** 🟢 PRODUCTION READY
**Version:** 0.20.0
**Audit Score:** 8.2/10 (Professional Accounting Evaluation 2026-02-04)
**Test Coverage:** 109 backend tests (74 ratio_engine + 31 audit_engine + 4 other)
**Ratios Available:** 8 (Current, Quick, D/E, Gross Margin, Net Profit, Operating, ROA, ROE)
**Dashboard:** All 8 ratios visible with tooltips, trend indicators, collapsible advanced section

### Phase II Overview (Sprints 25-39)
| Block | Sprints | Theme | Agent Lead |
|-------|---------|-------|------------|
| Foundation | 25-27 | Test Suite + Ratio Expansion | QualityGuardian + BackendCritic |
| User Experience | 28-30 | Dashboard + Classification | FrontendExecutor + FintechDesigner |
| Professional | 29, 31 | IFRS/GAAP + Materiality | ProjectAuditor + BackendCritic |
| Trends | 32-33 | Historical Analysis + Viz | BackendCritic + FintechDesigner |
| Industry | 34-35 | Sector-Specific Ratios | BackendCritic + FrontendExecutor |
| Advanced | 36-38 | Rolling Windows + Batch | FrontendExecutor + QualityGuardian |
| Phase III Prep | 39 | Benchmark Framework | BackendCritic + ProjectAuditor |

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

### Unresolved Tensions
| Tension | Resolution Sprint | Status |
|---------|-------------------|--------|
| Diagnostic zone protection disabled | Post-Phase II | Ready to enable |
| No multi-period trend analysis | 32-33 | Infrastructure + viz planned |
| No industry-specific ratios | 34-35 | Manufacturing/Retail/Services |
| No batch multi-file upload | 37-38 | Foundation + UI planned |
| No benchmark comparison | 39 | RFC design sprint |

### Project Status
**Phase I Complete (24 Sprints).** Paciolus is production-ready.
**Phase II Planned (15 Sprints).** Agent council consensus achieved.

### Agent Council Summary (2026-02-04)
6 agents evaluated planned items. Consensus:
1. **Sprint 25:** Test suite + multi-sheet fix (5/6 agents ranked top 3)
2. **Sprints 26-27:** Ratio expansion (low complexity, high value)
3. **Sprint 28:** Dashboard enhancement (highest user visibility)
4. **Sprints 32-33:** Trend analysis (FintechDesigner's top visual priority)
5. **Sprints 37-38:** Batch upload (high complexity, careful sequencing)

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