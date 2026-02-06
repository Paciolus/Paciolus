# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Days

### Day 1-3: Foundation (Pre-Council)
- [x] Backend: FastAPI setup with Zero-Storage architecture
- [x] Backend: Trial balance upload and validation
- [x] Backend: Abnormal balance detection
- [x] Frontend: Next.js landing page
- [x] Frontend: File upload with drag-and-drop
- [x] Frontend: Results display

### Day 4: Guardian Task — Environment Configuration
- [x] Create `.env` configuration system for Backend
- [x] Create `.env.local` configuration for Frontend
- [x] Remove all hardcoded `localhost:8000` references
- [x] Implement hard-fail if `.env` missing
- [x] Create `.env.example` templates
- [x] Update `.gitignore`

### Day 5: Materiality Thresholds & Adaptive Logic
- [x] MarketScout: Define default $500 threshold
- [x] BackendCritic: Add `materiality_threshold` parameter to audit_engine
- [x] FrontendExecutor: Create accessible threshold slider UI
- [x] IntegratorLead: Implement Material vs Immaterial classification
- [x] QualityGuardian: Validate accessibility (no color-only indicators)

### Day 6: High-Performance Data Streaming
- [x] BackendCritic: Implement chunked CSV/Excel reading
- [x] BackendCritic: StreamingAuditor class with running totals
- [x] QualityGuardian: Explicit `gc.collect()` after each chunk
- [x] FrontendExecutor: Add "Scanning Rows: X..." progress indicator
- [x] Generate `large_test.csv` (50,000 rows) for testing

### Day 7: Workflow Infrastructure & Git Initialization
- [x] IntegratorLead: Create `/tasks` directory
- [x] IntegratorLead: Create `todo.md` with roadmap
- [x] IntegratorLead: Create `lessons.md` template
- [x] IntegratorLead: Update CLAUDE.md with Plan/Lesson requirements
- [x] QualityGuardian: Initialize Git repository
- [x] QualityGuardian: Create Zero-Storage .gitignore
- [x] QualityGuardian: First commit "Initial Build: Day 6 Core Architecture"
- [x] BackendCritic: Draft `/test-streaming` specification

---

## Remaining Days (8-18)

### Day 8: Automated Verification Suite ✅ COMPLETE
- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] BackendCritic: Create `backend/tests/test_audit_engine.py`
  - [x] Test small files vs large (chunked) files
  - [x] Test materiality threshold filtering accuracy
  - [x] Test edge cases (empty CSVs, non-numeric columns)
- [x] QualityGuardian: Create Zero-Storage Leak Test
  - [x] Verify no residual CSV data in /tmp after audit
  - [x] Verify no data persists in memory after crash simulation
- [x] FrontendExecutor: Create `/status` page showing last test run
- [x] IntegratorLead: Document lessons learned

### Day 9: Commercial Grade Mapping Logic — Independent Commercial Development
- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] IntegratorLead: Create logs/dev-log.md IP documentation
- [x] MarketScout: Research publicly available COA structures
- [x] BackendCritic: Create classification_rules.py with ~80 weighted keywords
- [x] BackendCritic: Create account_classifier.py weighted heuristic
- [x] BackendCritic: Integrate classifier with StreamingAuditor
- [x] BackendCritic: Add overrides parameter to /audit/trial-balance API
- [x] FrontendExecutor: Create MappingProvider context
- [x] FrontendExecutor: Create AccountTypeDropdown component
- [x] FrontendExecutor: Create MappingIndicator (Auto/Manual badges)
- [x] FrontendExecutor: Add export/import mapping functionality
- [x] QualityGuardian: Verify Zero-Storage compliance (sessionStorage + JSON export only)

### Day 9.1: Paciolus Brand Foundation ✅ COMPLETE
- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] FrontendExecutor: Global replacement CloseSignify → Paciolus (25+ files)
- [x] FrontendExecutor: Deploy logo assets to /frontend/public
- [x] FrontendExecutor: Update favicon with Paciolus logo
- [x] FrontendExecutor: Update Navbar with PaciolusLogo_LightBG
- [x] FrontendExecutor: Refactor Hero Section with "Surgical Precision" headline
- [x] FrontendExecutor: Implement 3-step narrative (Upload → Map → Export)
- [x] QualityGuardian: Verify "Zero-Storage" messaging is reflected in UI
- [x] IntegratorLead: Document IP checkpoint in logs/dev-log.md

### Day 9.2: Hybrid Mapping & Column Detection ✅ COMPLETE
- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] BackendCritic: Add column detection confidence scoring to audit_engine.py
- [x] BackendCritic: Return detected columns and confidence in API response
- [x] BackendCritic: Add column_mapping parameter to /audit/trial-balance API
- [x] BackendCritic: Prioritize user column mappings over auto-detection
- [x] FrontendExecutor: Create ColumnMappingModal component (Oat & Obsidian)
- [x] FrontendExecutor: Trigger modal when column_confidence < 80%
- [x] FrontendExecutor: Store column mappings in React state (Zero-Storage)
- [x] FrontendExecutor: Re-submit audit with user mappings on confirmation
- [x] QualityGuardian: Verify Zero-Storage compliance (no localStorage persistence)
- [x] IntegratorLead: Document friction in tasks/lessons.md

### Day 10: Surgical Risk Dashboard & Brand Refinement ✅ COMPLETE
- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] FintechDesigner/Executor: Logo Hotfix
  - [x] Replace PaciolusLogo_LightBG.png with DarkBG in navigation
  - [x] Apply max-height and object-fit for high-DPI displays
- [x] BackendCritic: Enhance StreamingAuditor for "Structural Anomalies"
  - [x] Flag Natural Balance Violations (Assets with Credit, Liabilities with Debit)
  - [x] Add anomaly_type categorization to response
  - [x] Highlight transactions exceeding materiality threshold (severity field)
- [x] FintechDesigner: Design Anomaly Card
  - [x] Use Clay Red (#BC4749) with "premium restraint" (left-border accent)
  - [x] Add framer-motion staggers for smooth appearance
- [x] FrontendExecutor: Build RiskDashboard.tsx component
  - [x] Create animated AnomalyCard component
  - [x] Integrate into results view (not separate page)
  - [x] Display anomalies with staggered animation
- [x] IntegratorLead: Document IP in logs/dev-log.md
- [x] QualityGuardian: Verify Zero-Storage compliance (all data in memory/React state)
- [x] QualityGuardian: Verify frontend build succeeds (Next.js 16.1.6)

### Day 11: Multi-Sheet Excel Logic & Consolidation ✅ COMPLETE
- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] BackendCritic: Create sheet inspection endpoint
  - [x] Add `/audit/inspect-workbook` endpoint (fast sheet metadata)
  - [x] Return sheet names, row counts, column previews
  - [x] Handle both .xlsx and .xls formats via openpyxl/pandas
- [x] BackendCritic: Implement multi-sheet audit support
  - [x] Add `selected_sheets` parameter to `/audit/trial-balance`
  - [x] Implement "Summation Consolidation" (aggregate multiple sheets)
  - [x] Maintain per-sheet anomaly tracking in response
- [x] FintechDesigner: Design "Workbook Inspector" modal
  - [x] Oat & Obsidian themed sheet selection list
  - [x] Subtle hover effects with Merriweather aesthetic
  - [x] Checkboxes for multi-select with "Select All" option
- [x] FrontendExecutor: Build WorkbookInspector.tsx component
  - [x] Integrate with existing upload flow (detect → inspect → audit)
  - [x] Coordinate with ColumnMappingModal (sheets first, columns second)
  - [x] Preserve userColumnMapping across sheet selections
- [x] IntegratorLead: Document IP in logs/dev-log.md
- [x] QualityGuardian: Verify Zero-Storage compliance (in-memory only)
- [x] QualityGuardian: Verify frontend build (Next.js 16.1.6 Turbopack)

### Day 12: Surgical Export & Report Generation ✅ COMPLETE
> **Note:** CEO pivoted from Authentication to PDF Reports (fulfilling "Close Health Reports" promise)

- [x] IntegratorLead: Update todo.md (Plan Update)
- [x] BackendCritic: Install and configure ReportLab
  - [x] Add reportlab to requirements.txt
  - [x] Create pdf_generator.py module
- [x] BackendCritic: Create /export/pdf endpoint
  - [x] Accept audit result JSON in POST body
  - [x] Generate PDF in BytesIO buffer (Zero-Storage)
  - [x] Stream PDF response to browser
- [x] FintechDesigner: Design PDF Report Template
  - [x] Oat & Obsidian palette (dark headers, oatmeal accents)
  - [x] Paciolus logo at top (DarkBG variant)
  - [x] Risk Summary section mirroring Day 10 dashboard
  - [x] Per-account anomaly table with materiality indicators
- [x] FrontendExecutor: Add "Download PDF Report" button
  - [x] Premium framer-motion loading state ("Generating Surgical Report...")
  - [x] Trigger browser download on completion
- [x] IntegratorLead: Document IP in logs/dev-log.md
- [x] QualityGuardian: Verify Zero-Storage compliance (no temp files)

### Day 13: Secure Commercial Infrastructure ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. Database stores user credentials/settings ONLY — never trial balance data.

#### BackendCritic: User Database & JWT Authentication
- [x] Initialize SQLite database with SQLAlchemy ORM
- [x] Create User model (id, email, hashed_password, created_at, settings)
- [x] Install and configure `python-jose` for JWT token generation
- [x] Install and configure `passlib[bcrypt]` for password hashing
- [x] Implement `/auth/register` endpoint
  - [x] Email validation (Pydantic EmailStr)
  - [x] Password complexity requirements (8+ chars, upper, lower, number, special)
  - [x] Bcrypt password hashing
  - [x] Return JWT token on success
- [x] Implement `/auth/login` endpoint
  - [x] Verify credentials against hashed password
  - [x] Return JWT token on success
  - [ ] Rate limiting consideration (future)
- [x] Create `get_current_user` dependency for protected routes
- [x] Create `/auth/me` endpoint for user info retrieval

#### FintechDesigner: "Obsidian Vault" Login Experience
- [x] Design Login page with Oat & Obsidian palette
  - [x] "Secure Vault" visual metaphor (lock iconography)
  - [x] "Zero-Storage Promise" badge prominently displayed
  - [x] Email and password inputs with premium styling
  - [x] "Remember me" checkbox (client-side only)
- [x] Design Registration page
  - [x] Same vault aesthetic
  - [x] Password strength indicator (5-segment bar)
  - [x] Terms acceptance checkbox
- [x] Design Profile dropdown for logged-in users
  - [x] PaciolusLogo_LightBG in dropdown header
  - [x] "Welcome, [email]" greeting
  - [x] Logout button

#### FrontendExecutor: Auth Context & Protected Routes
- [x] Create `AuthContext` provider
  - [x] Store JWT in sessionStorage (Zero-Storage compliant)
  - [x] `user`, `isAuthenticated`, `login`, `logout`, `register` state/methods
  - [ ] Auto-refresh token logic (optional, future)
- [x] Create `/login` and `/register` pages
- [x] Implement Protected Route wrapper component
  - [x] Redirect unauthenticated users to /login
  - [x] Preserve intended destination after login
- [x] Update Navbar with Profile dropdown (logged in) or Login button (logged out)
- [ ] Protect `/` audit zone for authenticated users only (deferred - see note)

> **Note:** Audit zone protection deferred to allow continued unauthenticated testing during development. Auth infrastructure is complete and ready to enable.

#### QualityGuardian: Security Verification
- [x] Verify passwords are NEVER logged or stored in plaintext
- [x] Verify JWT tokens have appropriate expiration (24h = 1440 minutes)
- [x] Verify CORS still allows local development
- [x] Verify Zero-Storage: no trial balance data touches SQLite

#### IntegratorLead: IP Documentation
- [x] Document in logs/dev-log.md that auth uses industry-standard libraries
- [x] List all auth-related dependencies and their licenses
- [x] Confirm zero proprietary auth patterns used

### Day 14: Activity Logging & Metadata History ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** MANDATORY — Do NOT store actual file content or specific anomaly details. Only high-level summary metadata.
> **Privacy:** Designed to respect GDPR/CCPA by avoiding PII in logs.

#### BackendCritic: ActivityLog Database Schema
- [x] Create `ActivityLog` model in models.py
  - [x] `id` — Primary key
  - [x] `user_id` — Foreign key to User (nullable for anonymous audits)
  - [x] `filename_hash` — SHA-256 hash of filename (NOT the file content)
  - [x] `timestamp` — When the audit was performed
  - [x] `record_count` — Number of rows processed
  - [x] `total_debits` — Summary total (no line-item details)
  - [x] `total_credits` — Summary total
  - [x] `materiality_threshold` — Threshold used for the audit
  - [x] `was_balanced` — Boolean result
  - [x] `anomaly_count` — Count only (no specific anomaly details)
- [x] Create `/activity` endpoints
  - [x] `POST /activity/log` — Record an audit activity (called after successful audit)
  - [x] `GET /activity/history` — Get user's audit history (authenticated)
  - [x] `DELETE /activity/clear` — Clear user's activity history
- [x] Frontend calls /activity/log after successful audits (not in backend /audit endpoint)

#### FintechDesigner: "Heritage Timeline" Professional History View
- [x] Design vertical timeline with Oat & Obsidian palette
  - [x] Traditional ledger aesthetic (ruled lines, columns)
  - [x] Each entry shows: date, filename (hashed preview), record count, balance status
  - [x] "Balanced" entries in Sage, "Unbalanced" entries with Clay accent
- [x] Design "Quick Re-Run" button
  - [x] Populates materiality threshold from history
  - [x] Clear messaging: "Re-upload required" to maintain Zero-Storage
- [x] Design Zero-Storage reassurance banner
  - [x] Prominent badge explaining only metadata is stored
  - [x] "Your financial data was never saved" messaging

#### FrontendExecutor: /history Page Integration
- [x] Create `/history` page route
- [x] Fetch activity history from `/activity/history` endpoint
- [x] Implement Heritage Timeline component
- [x] Implement "Quick Re-Run" functionality
  - [x] Store settings in sessionStorage
  - [x] Redirect to home with pre-filled threshold
  - [x] Prompt for file re-upload
- [x] Add Zero-Storage reassurance banner
- [x] Add link to /history in ProfileDropdown

#### QualityGuardian: Privacy & Compliance Verification
- [x] Verify NO file content is stored in ActivityLog
- [x] Verify NO specific anomaly details are stored
- [x] Verify filename is hashed (not stored in plaintext)
- [x] Verify Zero-Storage messaging is prominent on /history page

#### IntegratorLead: IP & Compliance Documentation
- [x] Update logs/dev-log.md with GDPR/CCPA compliance statement
- [x] Document what IS stored vs what is NOT stored
- [x] Confirm design respects data privacy laws

### Sprint 15: Stability & Architectural Reset ✅ COMPLETE
> **Model Transition:** Moving from 'Day' to '10-Sprint' model (Sprints 15-24)
> **Priority:** Bug triage before new features

#### QualityGuardian: AuditResults Referential Loop Fix
- [x] Implement `useRef` for previous threshold tracking
- [x] Add deep comparison in useEffect to prevent unnecessary re-audits
- [x] Implement Tier 1 Skeleton Loaders (shimmer effect) for layout stability
- [x] Verify UI no longer jitters on threshold changes

#### BackendCritic: PDF Generator Style Collision Fix
- [x] Refactor `create_styles()` to use "Get or Create" singleton pattern
- [x] Fix "Style BodyText already defined" error
- [x] Verify PDF generation works on repeated requests

#### FintechDesigner: Semantic Color Enforcement (Tier 2)
- [x] Verify Clay Red (#BC4749) used for all anomalies/errors in UI
- [x] Verify Sage Green (#4A7C59) used for all success states in UI
- [x] Verify semantic colors consistent in PDF output
- [x] Document color mapping in theme spec (documented in lessons.md)

### Sprint 16: Client Core Infrastructure ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage for transactions remains in effect. Only client name and high-level settings are stored.

#### BackendCritic: Client SQLAlchemy Model
- [x] Add `Client` model to models.py with fields: id, user_id (FK), name, industry (Enum), fiscal_year_end, created_at
- [x] Create Industry enum for standardized industry classification
- [x] Ensure proper foreign key relationship to User

#### BackendCritic: Client Manager & API
- [x] Create `backend/client_manager.py` with CRUD operations
- [x] Add `GET /clients` endpoint (user-scoped, multi-tenant)
- [x] Add `POST /clients` endpoint with validation
- [x] Add `GET /clients/{id}`, `PUT /clients/{id}`, `DELETE /clients/{id}` endpoints
- [x] Add `GET /clients/industries` endpoint for dropdown options
- [x] Ensure all client data is scoped to current_user (multi-tenant isolation)

#### FrontendExecutor: Client Types & Hook
- [x] Define `Client` interface in types/client.ts
- [x] Define `Industry` type and INDUSTRY_LABELS matching backend
- [x] Create `useClients` hook for fetching/storing client list
- [x] Add CRUD methods to hook (createClient, updateClient, deleteClient)

#### IntegratorLead: IP Documentation
- [x] Document in logs/dev-log.md that client architecture is original
- [x] Document separation of user-client metadata from ephemeral transaction data
- [x] Update Zero-Storage compliance documentation

### Sprint 17: Portfolio Dashboard & Entity UX ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. Dashboard displays client metadata only.

#### FintechDesigner: "Ledger/Folder" Card Design
- [x] Design ClientCard component with premium bound ledger aesthetic
- [x] Use Oat & Obsidian palette for card backgrounds and accents
- [x] Add Industry badge with semantic colors
- [x] Display "Last Audit" date and FYE status

#### FrontendExecutor: Portfolio Page (/portfolio)
- [x] Create /portfolio route with client card grid
- [x] Implement responsive grid layout (1-3 columns)
- [x] Add empty state for users with no clients
- [x] Integrate useClients hook for data fetching
- [x] Add delete confirmation modal

#### FrontendExecutor: "New Client" Modal
- [x] Build CreateClientModal component
- [x] Implement Tier 2: Form Focus & Validation
  - [x] Sage Green border shift for active inputs
  - [x] Clay Red for validation errors
- [x] Add industry and fiscal year dropdowns
- [x] Handle form submission with loading state

#### FrontendExecutor: Tier 1 Animations
- [x] Apply staggered entrance to client cards (40ms delay)
- [x] Implement button micro-interactions (translateY on hover)
- [x] Add modal enter/exit animations (spring physics)

#### IntegratorLead: IP Documentation
- [x] Document custom CSS and Framer-Motion logic in dev-log.md
- [x] Certify as original creative work

### Sprint 19: Comparative Analytics & Ratio Engine ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. Compare current run against stored metadata totals, never raw data.

#### BackendCritic: Ratio Intelligence Module
- [x] Create `backend/ratio_engine.py` for financial ratio calculations
  - [x] Current Ratio (Current Assets / Current Liabilities)
  - [x] Quick Ratio ((Current Assets - Inventory) / Current Liabilities)
  - [x] Debt-to-Equity Ratio (Total Liabilities / Total Equity)
  - [x] Gross Margin ((Revenue - COGS) / Revenue)
- [x] Implement Common-Size analysis (line items as % of Total Assets or Revenue)
- [x] Extract category totals from account balances during audit

#### BackendCritic: Persistence-Lite (DiagnosticSummary)
- [x] Create `DiagnosticSummary` model in models.py
  - [x] Store category totals (assets, liabilities, equity, revenue, expenses)
  - [x] Link to client_id for variance comparison
  - [x] Store calculated ratios for trend tracking
- [x] Add API endpoints for diagnostic summary storage/retrieval
- [x] Implement variance calculation against previous run

#### FintechDesigner/FrontendExecutor: Analytics Insight UI
- [x] Create MetricCard component with Tier 2 semantic colors
  - [x] Sage (#4A7C59) for positive trends
  - [x] Clay (#BC4749) for negative trends
- [x] Create KeyMetricsSection for Results view
- [x] Apply Tier 1 staggered entrance animations (40ms delay)
- [x] Integrate with existing results view

#### QualityGuardian: Verification
- [x] Verify ratio calculations are mathematically correct
- [x] Verify variance comparison uses only stored metadata
- [x] Verify Zero-Storage compliance maintained

#### IntegratorLead: IP Documentation
- [x] Document ratio calculation logic as "Mathematical Diagnostic Logic"
- [x] Update version to 0.11.0

### Sprint 18: Diagnostic Fidelity & Batch Intelligence ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Terminology Shift:** "Audit" → "Diagnostic/Assessment/Intelligence"

#### IntegratorLead: Global Linguistic Sweep
- [x] Replace "Audit" terminology throughout codebase:
  - [x] "Download Report" → "Export Diagnostic Summary"
  - [x] "Audit Results" → "Analysis Intelligence"
  - [x] "Audit History" → "Diagnostic History"
  - [x] "New Audit" → "New Diagnostic"
  - [x] Update PDF filename: [Client]_[Domain]_Diagnostic_[Date].pdf
- [x] Update UI labels, comments, and user-facing text
- [x] Preserve backend API routes for backwards compatibility

#### BackendCritic: PDF Generator Fidelity
- [x] Swap logo from DarkBG to LightBG for better contrast
- [x] Fix logo stretching with kind='proportional' (preserves aspect ratio)
- [x] Wrap anomaly descriptions in Paragraph objects (no text cutoff)
- [x] Add mandatory legal disclaimer to every page footer (via onPage callback)
- [x] Test PDF generation with long anomaly descriptions

#### FrontendExecutor: UI Enforcement
- [x] Add legal disclaimer banner to Results view
- [ ] Implement multi-file dropzone (batch ingestion) - DEFERRED
- [ ] Build cross-tab Normal Balance conflict detection - DEFERRED
- [x] Ensure Tier 1/2 UX standards maintained

#### QualityGuardian: Verification
- [x] Verify all "Audit" terminology replaced in user-facing text
- [x] Verify PDF disclaimer appears on every page
- [x] Verify no text truncation in PDF anomaly tables

#### IntegratorLead: IP Documentation
- [x] Update version to 0.10.0

### Sprint 20: Document Hardening & Loop Resolution ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. Excel generation must be performed in-memory.

#### QualityGuardian: UI Loop Fix
- [x] Implement deep-hash comparison state guard in page.tsx
- [x] Compare previous audit input hash with current before calling backend
- [x] Ensure Tier 1 Skeleton Loader is visible during resolution
- [x] Verify no unnecessary re-audits occur

#### BackendCritic: PDF Title Page & Excel Generator
- [x] Scrub "Audits" terminology → "Diagnostics" in PDF title page
- [x] Verify PDF uses v0.12.0 terminology exclusively
- [x] Create backend/excel_generator.py using openpyxl
- [x] Implement multi-tab workpaper: [Summary, Standardized TB, Flagged Anomalies, Key Ratios]
- [x] Add /export/excel endpoint to main.py
- [x] Ensure Zero-Storage compliance (BytesIO, no temp files)

#### FintechDesigner: Terminology Audit
- [x] Audit all exported titles for "Audit" terminology
- [x] Change "Surgical Precision for Trial Balance Audits" → "Diagnostics"
- [x] Verify UI consistency with v0.12.0 messaging

#### IntegratorLead: IP Documentation
- [x] Document "Deep-Hash Comparison" pattern in logs/dev-log.md
- [x] Update version to 0.12.0
- [x] Add lessons learned for this sprint

### Sprint 21: Customization & Practice Settings ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. While we store the formula, we NEVER store the data it is applied to.

#### BackendCritic: Settings Schema & API
- [x] Create PracticeSettings Pydantic model with materiality formula types
- [x] Define MaterialityFormula types: fixed, percentage_of_revenue, percentage_of_assets
- [x] Add /settings endpoints: GET, PUT for user practice settings
- [x] Add /clients/{id}/settings endpoints for client-specific settings
- [x] Validate formula syntax on save

#### FrontendExecutor: Practice Configuration UI
- [x] Create /settings page route
- [x] Build PracticeSettingsForm component with Tier 2 validation
- [x] Implement MaterialityFormulaEditor with dropdown for formula type
- [x] Add preview of calculated threshold (e.g., "0.5% of Revenue = $X")
- [x] Store/retrieve settings via API
- [x] Prepopulate Diagnostic view with global threshold from settings

#### QualityGuardian: Dynamic Materiality Engine
- [x] Refactor StreamingAuditor to accept MaterialityConfig
- [x] Implement formula evaluation: fixed, percentage_of_revenue, percentage_of_assets
- [x] Prioritize user formula over default $500 threshold
- [x] Add category_totals dependency for percentage-based formulas
- [x] Ensure formula evaluation is Zero-Storage (runtime only)

#### IntegratorLead: IP Documentation
- [x] Document "Dynamic Materiality Logic" in logs/dev-log.md
- [x] Update version to 0.13.0
- [x] Add lessons learned for this sprint

### Sprint 22: Live Sensitivity Tuning & UI Hardening ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. All sensitivity adjustments are session-only.

#### FintechDesigner + FrontendExecutor: Sensitivity Toolbar ("Control Surface")
- [x] Create SensitivityToolbar component with "Control Surface" aesthetic
  - [x] Display: "Current Threshold: $X"
  - [x] Display: "Display: [Strict/Lenient]" toggle
  - [x] Obsidian/Oat palette, distinct from data cards
  - [x] Smooth transition to edit mode on click
- [x] Implement Edit Mode
  - [x] Input field replaces text on "Edit" click
  - [x] Apply button triggers recalculation
  - [x] Cancel button reverts to display mode
- [x] Integrate toolbar into AuditResults view (page.tsx)

#### QualityGuardian: Hash-Guard Verification
- [x] Verify "Apply" correctly updates threshold state
- [x] Verify hash-guard triggers recalculation only on actual change
- [x] Verify no loops or unnecessary re-audits occur
- [x] Verify Tier 1 Skeleton Loader visible during recalculation

#### FrontendExecutor: UI Hardening & Generalization
- [x] Fix dropzone "Ghost Click" bleed issue
  - [x] Ensure file input doesn't capture clicks outside dropzone
  - [x] Test drag-and-drop still works correctly
- [x] Replace "Fractional CFO" with "Financial Professional" globally
  - [x] Navigation bar tagline
  - [x] Footer text
  - [x] Any other user-facing references

#### IntegratorLead: IP Documentation
- [x] Document "Contextual Parameter Tuning" UX pattern in logs/dev-log.md
- [x] Update version to 0.14.0
- [x] Add lessons learned for this sprint

### Sprint 23: The Marketing Front & Brand Hardening ✅ COMPLETE
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Maintain Oat & Obsidian palette. Ensure "Diagnostic" terminology consistency.

#### FintechDesigner + FrontendExecutor: Hero Section Redesign
- [x] Redesign Landing Page Hero Section with "Surgical Diagnostic" value proposition
- [x] Create compelling headline and sub-headline for Financial Professionals
- [x] Maintain Zero-Storage Promise badge prominently
- [x] Add animated visual interest without compromising professionalism

#### FintechDesigner + FrontendExecutor: "Three Pillars" Section
- [x] Create FeaturePillars component with 3 key value props:
  - [x] Zero-Knowledge Security (data never stored)
  - [x] Automated Sensitivity (intelligent threshold tuning)
  - [x] Professional-Grade Exports (PDF/Excel workpapers)
- [x] Implement Tier 1 staggered animations for pillar cards
- [x] Ensure Oat & Obsidian palette consistency

#### FrontendExecutor: "Process Timeline" Component
- [x] Create ProcessTimeline component showing transformation flow
  - [x] Step 1: Raw Data (Upload)
  - [x] Step 2: Intelligent Analysis (Map)
  - [x] Step 3: Reclassified Intelligence (Export)
- [x] Implement Tier 1 animations (scroll-triggered or staggered entrance)
- [x] Use visual storytelling to demonstrate value

#### QualityGuardian: Sprint 17 Hotfix
- [x] Fix Industry type mismatch in portfolio/page.tsx line 51
- [x] Change `industry?: string` to `industry?: Industry` (or use ClientCreateInput)
- [x] Fix framer-motion type assertion in CreateClientModal.tsx
- [x] Verify clean frontend build with no type errors

#### IntegratorLead: IP Documentation
- [x] Document "Brand-Integrated Feature Set" in logs/dev-log.md
- [x] Update version to 0.15.0
- [x] Add lessons learned for this sprint

### Sprint 24: Production Deployment Prep ✅ COMPLETE (FINAL SPRINT)
> **Affirmation:** Independent Development on Personal Hardware
> **Constraint:** Zero-Storage. Production database solely for user metadata and settings.

#### BackendCritic: Containerization
- [x] Create Dockerfile for Backend (slim Python image, Gunicorn)
- [x] Create Dockerfile for Frontend (multi-stage Node/Next build)
- [x] Write docker-compose.yml for local-to-cloud mirroring

#### QualityGuardian: Infrastructure Security
- [x] Implement production-grade CORS policy (environment-specific origins)
- [x] Create secrets_manager.py for production credential separation
- [x] Update .env.example with production template annotations

#### FrontendExecutor: Build Optimization
- [x] Verify Next.js production build optimization (standalone output)
- [x] Implement production-safe logging (no sensitive data exposure)

#### IntegratorLead: Deployment Documentation
- [x] Create DEPLOYMENT.md with step-by-step instructions
  - [x] Vercel deployment guide (Frontend)
  - [x] Render/DigitalOcean deployment guide (Backend)
  - [x] Environment variable reference table
- [x] Document "Production-Grade Stateless Infrastructure" in logs/dev-log.md
- [x] Update version to 0.16.0 (Final Sprint)
- [x] Add lessons learned for this sprint

---

## Review Sections

### Day 7 Review
**Status:** Complete
**Blockers:** None
**Notes:**
- Created tasks/ directory with todo.md (18-day roadmap) and lessons.md
- Updated CLAUDE.md with MANDATORY Directive Protocol
- Initialized Git repository with Zero-Storage .gitignore
- First commit: 471934a "Initial Build: Day 6 Core Architecture" (31 files, 5201 insertions)
- BackendCritic drafted test_streaming_spec.md for Day 8 implementation
- Audit score should improve from 🟠 2.9 to 🟡 3.5+ on next run

### Day 8 Review
**Status:** Complete
**Blockers:** None
**Test Results:** 25/25 passed (212 warnings - datetime deprecation)
**Notes:**
- Created backend/tests/test_audit_engine.py with comprehensive test suite
- Tests cover: StreamingAuditor, AuditPipeline, EdgeCases, ZeroStorageLeak, Performance
- Created frontend /status page showing test results and backend health
- Discovered datetime.utcnow() deprecation (documented in lessons.md)
- Added pytest, psutil, httpx to requirements.txt
**Lessons Documented:**
- datetime.utcnow() deprecated in Python 3.12+
- Test fixtures make tests readable and maintainable

### Day 9 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Hybrid (Client stores + API receives overrides for server-side re-analysis)
**Keyword Scope:** Core 80 keywords (high/medium confidence, 5 categories)
**Notes:**
- Created logs/dev-log.md for IP documentation (all sources publicly available)
- Created backend/classification_rules.py with 80+ weighted keywords (standard accounting terminology)
- Created backend/account_classifier.py with weighted heuristic algorithm
- Updated audit_engine.py to use new classifier with confidence scoring
- Updated main.py API to accept account_type_overrides parameter (JSON string)
- Fixed datetime.utcnow() deprecation - now using datetime.now(UTC)
- Created frontend mapping system: MappingProvider, AccountTypeDropdown, MappingIndicator, MappingToolbar
- Zero-Storage compliant: sessionStorage + JSON export to user's local machine
**Files Created:**
- backend/classification_rules.py
- backend/account_classifier.py
- logs/dev-log.md
- frontend/src/types/mapping.ts
- frontend/src/context/MappingContext.tsx
- frontend/src/components/mapping/AccountTypeDropdown.tsx
- frontend/src/components/mapping/MappingIndicator.tsx
- frontend/src/components/mapping/MappingToolbar.tsx
- frontend/src/components/mapping/index.ts
**Lessons Documented:**
- Weighted heuristics beat binary keyword matching for account classification
- Conflict Loop helped clarify hybrid vs client-only architecture decision

### Day 9.1 Review
**Status:** Complete
**Blockers:** None
**Notes:**
- Renamed project from "CloseSignify" to "Paciolus" (named after Luca Pacioli, father of accounting)
- Global replacement across 25+ files (frontend, backend, configs, docs)
- Deployed logo assets to frontend/public (LightBG, DarkBG, main logo)
- Updated navbar with Paciolus logo image
- Refactored Hero Section with "Surgical Precision" headline and 3-step workflow
- Zero-Storage messaging now prominent: badge, audit zone, footer
- IP documentation added to logs/dev-log.md
**Files Modified:**
- All frontend/backend files with CloseSignify references
- frontend/public/* (new logo assets)
- frontend/src/app/layout.tsx (favicon, metadata)
- frontend/src/app/page.tsx (navbar, hero)
- logs/dev-log.md (IP checkpoint)
- CLAUDE.md (project state updated)
**Brand Assets:**
- PaciolusLogo.jpg (main logo)
- PaciolusLogo_LightBG.png (light background variant)
- PaciolusLogo_DarkBG.png (dark background variant)

### Day 9.2 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Two-phase audit (detect → confirm if needed → process)
**Notes:**
- Created backend/column_detector.py with weighted pattern matching for column identification
- Column detection returns confidence scores (0-100%) for Account, Debit, Credit columns
- If overall_confidence < 80%, API response includes `requires_mapping: true`
- Frontend shows ColumnMappingModal when mapping is required
- User selections stored in React state only (Zero-Storage compliant)
- Re-audit with user mapping bypasses auto-detection
- API version bumped to 0.3.0
**Files Created:**
- backend/column_detector.py (weighted pattern matching)
- frontend/src/components/mapping/ColumnMappingModal.tsx (Oat & Obsidian themed)
**Files Modified:**
- backend/audit_engine.py (StreamingAuditor + column_mapping parameter)
- backend/main.py (API accepts column_mapping, returns column_detection)
- frontend/src/app/page.tsx (modal integration, state coordination)
- frontend/src/components/mapping/index.ts (export ColumnMappingModal)
**Lessons Documented:**
- Column Detection vs Account Classification are two different problems
- Modal triggers require careful state coordination (pending/visible/confirmed)

### Day 10 Review
**Status:** Complete
**Blockers:** None
**Design Philosophy:** "Premium Restraint" — Clay Red used sparingly (left-border accent, subtle glow) rather than overwhelming solid blocks
**Notes:**
- Fixed navigation logo to use DarkBG variant on dark obsidian-900 background
- Added image optimization (max-height, object-fit, crisp-edges) for high-DPI displays
- Enhanced StreamingAuditor with anomaly categorization (anomaly_type, severity, expected/actual balance)
- Added risk_summary to API response for dashboard rendering
- Created animated RiskDashboard with AnomalyCard components using framer-motion
- Staggered animations (50ms delay between cards) for smooth visual presentation
- Fixed TypeScript strict mode issues with framer-motion variants (as const)
**Files Created:**
- frontend/src/components/risk/AnomalyCard.tsx (animated card with Clay Red accent)
- frontend/src/components/risk/RiskDashboard.tsx (dashboard container)
- frontend/src/components/risk/index.ts (component exports)
**Files Modified:**
- backend/audit_engine.py (anomaly_type, severity, risk_summary fields)
- frontend/src/app/page.tsx (logo fix, RiskDashboard integration)
- frontend/src/types/mapping.ts (Day 10 type definitions)
- frontend/package.json (framer-motion dependency)
- logs/dev-log.md (IP documentation)
**Test Results:** 25/25 backend tests passed
**Frontend Build:** Success (Next.js 16.1.6 Turbopack)
**Zero-Storage Verified:** All risk data processed in-memory only

### Day 11 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Two-phase flow (inspect → select → audit) following Day 9.2 pattern
**Notes:**
- Created `/audit/inspect-workbook` endpoint for fast sheet metadata extraction
- Uses openpyxl read-only mode for efficient metadata access without loading cell data
- Summation Consolidation aggregates totals across selected sheets
- Per-sheet anomaly tracking with `sheet_name` field on each abnormal balance
- WorkbookInspector modal with Oat & Obsidian theme, framer-motion animations
- Frontend flow: detect Excel → inspect workbook → show modal if multi-sheet → audit selected
- Column mapping preserved across sheet selections (Zero-Storage: React state)
- API version bumped to 0.4.0
**Files Created:**
- backend/workbook_inspector.py (openpyxl/pandas inspection)
- frontend/src/components/workbook/WorkbookInspector.tsx
- frontend/src/components/workbook/index.ts
**Files Modified:**
- backend/security_utils.py (read_excel_multi_sheet_chunked)
- backend/audit_engine.py (audit_trial_balance_multi_sheet)
- backend/main.py (inspect-workbook endpoint, selected_sheets parameter)
- frontend/src/app/page.tsx (two-phase upload flow, WorkbookInspector integration)
- frontend/src/types/mapping.ts (SheetInfo, WorkbookInfo, ConsolidatedAuditResult)
- logs/dev-log.md (IP documentation)
**Test Results:** 25/25 backend tests passed (existing tests)
**Frontend Build:** Success (Next.js 16.1.6 Turbopack)
**Zero-Storage Verified:** BytesIO buffers, explicit gc.collect(), React state only

### Day 12 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Zero-Storage PDF generation using ReportLab + BytesIO streaming
**Notes:**
- Created pdf_generator.py with OatObsidianColors class and PaciolusReportGenerator
- PDF generated entirely in-memory (BytesIO buffer), never touches disk
- Streaming response sends PDF in 8KB chunks directly to browser
- DownloadReportButton with framer-motion loading state ("Generating Surgical Report...")
- Button triggers browser download on completion
- API version bumped to 0.5.0
**Files Created:**
- backend/pdf_generator.py (ReportLab PDF generation)
- frontend/src/components/export/DownloadReportButton.tsx (animated download button)
- frontend/src/components/export/index.ts (component exports)
**Files Modified:**
- backend/main.py (/export/pdf endpoint, AuditResultInput model)
- backend/requirements.txt (reportlab==4.1.0)
- frontend/src/app/page.tsx (DownloadReportButton integration)
- logs/dev-log.md (IP documentation)
**Test Results:** 25/25 backend tests passed
**Frontend Build:** Success (Next.js 16.1.6 Turbopack)
**Zero-Storage Verified:** BytesIO streaming, no temp files, immediate memory release

### Day 13 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** JWT-based stateless authentication with SQLite user database (Zero-Storage exception for credentials only)
**Notes:**
- Created complete JWT authentication system using industry-standard libraries
- User database stores ONLY credentials and settings - NEVER trial balance data
- SQLite for local development, PostgreSQL-compatible for production
- Password hashing with bcrypt (auto-salted, timing-attack resistant)
- JWT tokens expire after 24 hours (configurable via JWT_EXPIRATION_MINUTES)
- Frontend auth context stores JWT in sessionStorage (ephemeral, client-side only)
- "Obsidian Vault" login/register UI with premium framer-motion animations
- Password strength indicator with 5-requirement checklist
- ProfileDropdown component for logged-in users in navbar
- Protected Route wrapper component ready for use
- Audit zone protection deferred to allow continued dev testing
- API version bumped to 0.6.0
**Files Created:**
- backend/database.py (SQLAlchemy engine/session)
- backend/models.py (User model)
- backend/auth.py (JWT, password hashing, dependencies)
- frontend/src/context/AuthContext.tsx (auth state management)
- frontend/src/components/auth/ProtectedRoute.tsx
- frontend/src/components/auth/ProfileDropdown.tsx
- frontend/src/app/login/page.tsx
- frontend/src/app/register/page.tsx
- frontend/src/app/providers.tsx
**Files Modified:**
- backend/main.py (/auth/register, /auth/login, /auth/me endpoints)
- backend/config.py (JWT and database config)
- backend/requirements.txt (python-jose, passlib, sqlalchemy)
- backend/.env.example (auth config variables)
- frontend/src/app/layout.tsx (AuthProvider wrapper)
- frontend/src/app/page.tsx (auth-aware navbar)
- frontend/src/components/auth/index.ts (new exports)
- logs/dev-log.md (IP documentation)
**Test Results:** 25/25 backend tests passed (existing tests)
**Frontend Build:** Success (Next.js 16.1.6 Turbopack)
**Zero-Storage Verified:** User DB contains only auth data; trial balance processing unchanged

### Day 14 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Hybrid storage (backend API for authenticated, localStorage fallback for anonymous)
**Privacy Compliance:** GDPR/CCPA compliant — only aggregate metadata stored, no PII
**Notes:**
- Created ActivityLog model with SHA-256 filename hashing for privacy
- Implemented /activity/log, /activity/history, /activity/clear endpoints
- Frontend logs activity after successful audits (authenticated users only)
- Heritage Timeline component with Oat & Obsidian theme
- Zero-Storage reassurance banner prominently displayed on /history page
- Quick Re-Run stores threshold in sessionStorage, requires file re-upload
- Expanded schema beyond directive: added total_credits, material_count, immaterial_count
- API version bumped to 0.7.0
**Files Created:**
- backend/models.py (ActivityLog model added)
- frontend/src/types/history.ts (activity history types)
- frontend/src/components/history/HeritageTimeline.tsx
- frontend/src/components/history/index.ts
**Files Modified:**
- backend/main.py (activity endpoints, hash utilities)
- frontend/src/app/history/page.tsx (API integration)
- frontend/src/app/page.tsx (activity logging after audit)
- frontend/src/components/auth/ProfileDropdown.tsx (history link)
- logs/dev-log.md (GDPR/CCPA compliance documentation)
**Zero-Storage Verified:** ActivityLog contains only aggregate metadata; no file content, account names, or transaction details stored

### Sprint 15 Review
**Status:** Complete
**Blockers:** None
**Focus:** Stability & Architectural Reset — Bug triage before new features
**Notes:**
- Fixed AuditResults referential loop with useRef deep comparison
- Implemented Tier 1 Skeleton Loaders with shimmer animation
- Fixed PDF Generator "Style BodyText already defined" error with get-or-create pattern
- Verified semantic color enforcement (Clay #BC4749 for errors, Sage #4A7C59 for success)
- Transitioned from 'Day' model to '10-Sprint' model (Sprints 15-24)
**Files Modified:**
- backend/pdf_generator.py (_add_or_replace_style pattern)
- frontend/src/app/page.tsx (useRef deep comparison, skeleton loaders)
- frontend/src/app/globals.css (shimmer keyframes)
- tasks/lessons.md (3 new lessons documented)
- CLAUDE.md (project state updated)
**Lessons Documented:**
- ReportLab style collision: get-or-create pattern
- useEffect referential loop: deep comparison pattern
- Tier 1 skeleton loaders for layout stability

### Sprint 16 Review
**Status:** Complete
**Blockers:** None
**Focus:** Client Core Infrastructure — Multi-tenant client management
**Architecture Decision:** User-scoped client metadata with strict separation from transaction data
**Notes:**
- Created Client model with user_id FK for multi-tenant isolation
- Created Industry enum with 12 standard industry categories
- Created ClientManager with full CRUD operations
- Added 6 client API endpoints: GET/POST /clients, GET/PUT/DELETE /clients/{id}, GET /clients/industries
- All endpoints enforce user-scoped data access (multi-tenant)
- Created useClients hook with auto-fetch and CRUD methods
- API version bumped to 0.8.0
**Files Created:**
- backend/client_manager.py (CRUD operations)
- backend/models.py (Client model, Industry enum)
- frontend/src/types/client.ts (TypeScript interfaces)
- frontend/src/hooks/useClients.ts (React hook)
- frontend/src/hooks/index.ts (exports)
**Files Modified:**
- backend/database.py (init_db includes Client)
- backend/main.py (client endpoints)
- tasks/todo.md (Sprint 16 checklist)
- logs/dev-log.md (IP documentation)
**Zero-Storage Verified:** Client table stores only identification metadata; no financial data, transactions, or audit results

### Sprint 17 Review
**Status:** Complete
**Blockers:** None
**Focus:** Portfolio Dashboard & Entity UX — Premium client management interface
**Design Philosophy:** "Premium Bound Ledger" aesthetic with Tier 1/2 animations
**Notes:**
- Created /portfolio page with responsive client card grid (1-3 columns)
- Implemented ClientCard with left-spine ledger binding effect
- Created CreateClientModal with Tier 2 Form Validation (sage focus, clay errors)
- Applied Tier 1 staggered entrance animations (40ms delay per card)
- Implemented button micro-interactions (translateY hover, scale tap)
- Added delete confirmation modal with clay accent
- Empty state with Zero-Storage badge
- API version bumped to 0.9.0
**Files Created:**
- frontend/src/app/portfolio/page.tsx (Portfolio dashboard)
- frontend/src/components/portfolio/ClientCard.tsx (Ledger-style card)
- frontend/src/components/portfolio/CreateClientModal.tsx (Form modal)
- frontend/src/components/portfolio/index.ts (exports)
**Files Modified:**
- frontend/src/components/auth/ProfileDropdown.tsx (Portfolio link, version)
- backend/main.py (version bump to 0.9.0)
- tasks/todo.md (Sprint 17 checklist)
- logs/dev-log.md (IP documentation for custom CSS/animations)
**Zero-Storage Verified:** Dashboard displays only client metadata; no financial data rendered

### Sprint 18 Review
**Status:** Complete
**Blockers:** None
**Focus:** Diagnostic Fidelity & Global Linguistic Sweep
**Terminology Shift:** "Audit" → "Diagnostic/Assessment/Intelligence"
**Notes:**
- Global linguistic sweep: replaced "Audit" with "Diagnostic" in user-facing text
- PDF Generator: swapped to LightBG logo, fixed aspect ratio with kind='proportional'
- PDF Generator: anomaly descriptions now use Paragraph objects (no text cutoff)
- PDF Generator: legal disclaimer on every page via onPage callback
- Frontend: legal disclaimer banner added to results view
- Frontend: "Export Diagnostic Summary" button (was "Download PDF Report")
- API version bumped to 0.10.0
- Batch processing deferred to future sprint (single-file flow working well)
**Files Modified:**
- backend/pdf_generator.py (logo, Paragraph wrapping, legal disclaimer)
- backend/main.py (version 0.10.0, PDF filename convention)
- frontend/src/app/page.tsx (terminology, disclaimer banner)
- frontend/src/app/history/page.tsx (terminology)
- frontend/src/components/export/DownloadReportButton.tsx (terminology)
- frontend/src/components/auth/ProfileDropdown.tsx (version, terminology)
- frontend/src/components/history/HeritageTimeline.tsx (terminology)
- CLAUDE.md (project state updated)
**Zero-Storage Verified:** No changes to storage architecture; only UI/terminology updates

### Sprint 19 Review
**Status:** Complete
**Blockers:** None
**Focus:** Comparative Analytics & Ratio Engine — Financial ratio intelligence
**Architecture Decision:** Zero-Storage variance — compare against stored metadata totals only, never raw data
**Notes:**
- Created ratio_engine.py with RatioEngine, CommonSizeAnalyzer, VarianceAnalyzer classes
- Implemented 4 core ratios: Current, Quick, Debt-to-Equity, Gross Margin
- Created DiagnosticSummary model for storing category totals linked to client_id
- Added 3 API endpoints: POST/GET /diagnostics/summary, GET history
- Created MetricCard and KeyMetricsSection frontend components
- Applied Tier 1 staggered animations (40ms delay) and Tier 2 semantic colors
- Integrated KeyMetricsSection into results view after RiskDashboard
- API version bumped to 0.11.0
**Files Created:**
- backend/ratio_engine.py (ratio calculations, variance analysis)
- frontend/src/components/analytics/MetricCard.tsx (animated metric card)
- frontend/src/components/analytics/KeyMetricsSection.tsx (ratio dashboard)
- frontend/src/components/analytics/index.ts (component exports)
**Files Modified:**
- backend/models.py (DiagnosticSummary model)
- backend/audit_engine.py (get_category_totals, analytics in response)
- backend/main.py (diagnostic summary endpoints, version 0.11.0)
- frontend/src/types/mapping.ts (Analytics, RatioData, VarianceData types)
- frontend/src/app/page.tsx (KeyMetricsSection integration)
- tasks/todo.md (Sprint 19 checklist)
- logs/dev-log.md (IP documentation)
**Zero-Storage Verified:** DiagnosticSummary stores only aggregate metadata; no account names, transactions, or raw data

### Sprint 20 Review
**Status:** Complete
**Blockers:** None
**Focus:** Document Hardening & Loop Resolution — UI stability and Excel export
**Architecture Decision:** Deep-hash comparison for UI stability; Zero-Storage Excel generation
**Notes:**
- Implemented deep-hash comparison pattern using `computeAuditInputHash()` function
- Hash-based state guard prevents unnecessary re-audits from React referential equality issues
- Belt-and-suspenders approach: hash comparison + individual value checks
- Tier 1 Skeleton Loader visible during legitimate recalculations
- Created excel_generator.py with 4-tab workpaper structure
- Multi-tab workpaper: Summary, Standardized TB, Flagged Anomalies, Key Ratios
- Oat & Obsidian theme applied to Excel via openpyxl named styles
- Terminology scrub: "Trial Balance Audits" → "Trial Balance Diagnostics"
- API version bumped to 0.12.0
**Files Created:**
- backend/excel_generator.py (openpyxl workpaper generation)
**Files Modified:**
- backend/main.py (/export/excel endpoint, version 0.12.0, docstring update)
- frontend/src/app/layout.tsx (metadata terminology update)
- frontend/src/app/page.tsx (computeAuditInputHash, deep-hash comparison)
- tasks/todo.md (Sprint 20 checklist)
- tasks/lessons.md (Deep-Hash Comparison lesson)
- logs/dev-log.md (Sprint 20 IP documentation)
**Zero-Storage Verified:** Excel generated in BytesIO, streamed to browser, never touches disk
**Lessons Documented:**
- Deep-Hash Comparison for UI Stability

### Sprint 21 Review
**Status:** Complete
**Blockers:** None
**Focus:** Customization & Practice Settings — Dynamic materiality formulas
**Architecture Decision:** Zero-Storage for formulas; financial data never stored
**Notes:**
- Created practice_settings.py with MaterialityFormula and PracticeSettings Pydantic models
- Implemented 4 formula types: fixed, percentage_of_revenue, percentage_of_assets, percentage_of_equity
- MaterialityCalculator resolves formula at runtime (Zero-Storage compliant)
- Priority chain: session override → client settings → practice settings → system default
- Created /settings page with Tier 2 Form Validation (Oat & Obsidian)
- MaterialityFormulaEditor with formula type dropdown and value input
- Live preview of calculated threshold with explanation
- Settings prepopulate Diagnostic view threshold on page load
- Enabled Settings link in ProfileDropdown (was "Soon")
- API version bumped to 0.13.0
**Files Created:**
- backend/practice_settings.py (MaterialityFormula, PracticeSettings, ClientSettings, MaterialityCalculator)
- frontend/src/app/settings/page.tsx (Settings page with form validation)
- frontend/src/types/settings.ts (TypeScript types)
- frontend/src/hooks/useSettings.ts (Settings API hook)
**Files Modified:**
- backend/main.py (6 new settings endpoints, version 0.13.0)
- frontend/src/app/page.tsx (useSettings integration, threshold prepopulation)
- frontend/src/components/auth/ProfileDropdown.tsx (Settings link enabled, version 0.13.0)
- tasks/todo.md (Sprint 21 checklist)
- tasks/lessons.md (Dynamic Materiality lesson)
- logs/dev-log.md (Sprint 21 IP documentation)
**Zero-Storage Verified:** Only formulas stored; financial data for formula evaluation is runtime-only
**Lessons Documented:**
- Dynamic Materiality: Formula Storage vs Data Storage

### Sprint 22 Review
**Status:** Complete
**Blockers:** None
**Focus:** Live Sensitivity Tuning & UI Hardening — Real-time parameter adjustment
**Architecture Decision:** Zero-Storage for sensitivity adjustments; session-only state
**Notes:**
- Created SensitivityToolbar "Control Surface" component with framer-motion animations
- Display mode toggle: Strict (material only) vs Lenient (all anomalies)
- Inline edit mode with Apply/Cancel buttons and keyboard support (Enter/Escape)
- Integrated with existing hash-guard pattern for efficient recalculation
- Fixed dropzone "ghost click" issue with pointer-events-none when not in idle state
- Global terminology update: "Fractional CFO" → "Financial Professional" (9 locations)
- API version bumped to 0.14.0
**Files Created:**
- frontend/src/components/sensitivity/SensitivityToolbar.tsx (Control Surface component)
- frontend/src/components/sensitivity/index.ts (Component exports)
**Files Modified:**
- frontend/src/app/page.tsx (Toolbar integration, ghost click fix, terminology)
- frontend/src/app/layout.tsx (Terminology update in metadata)
- frontend/src/app/portfolio/page.tsx (Terminology update in footer)
- frontend/src/components/auth/ProfileDropdown.tsx (Version 0.14.0, terminology)
- backend/main.py (Version 0.14.0, terminology update)
- tasks/todo.md (Sprint 22 checklist)
- logs/dev-log.md (Contextual Parameter Tuning documentation)
- CLAUDE.md (Project state update)
**Zero-Storage Verified:** All sensitivity adjustments are React state only, never persisted
**Lessons Documented:**
- Contextual Parameter Tuning: UX pattern for professional decision support
- Ghost Click Fix: pointer-events control for conditional input activation

### Sprint 23 Review
**Status:** Complete
**Blockers:** None
**Focus:** The Marketing Front & Brand Hardening — Public-facing marketing components
**Architecture Decision:** Component-based marketing sections with Tier 1 animations
**Notes:**
- Created FeaturePillars component: Three pillars (Zero-Knowledge Security, Automated Sensitivity, Professional-Grade Exports)
- Created ProcessTimeline component: Visual transformation flow with horizontal (desktop) and vertical (mobile) layouts
- Integrated marketing sections into landing page between Hero and Diagnostic Zone
- Removed redundant "Why CFOs Choose Paciolus" section (replaced by FeaturePillars)
- Fixed Sprint 17 Industry type mismatch: Changed `industry?: string` to `ClientCreateInput` type
- Fixed framer-motion type assertion in CreateClientModal (`type: 'spring' as const`)
- API version bumped to 0.15.0
**Files Created:**
- frontend/src/components/marketing/FeaturePillars.tsx (Three Pillars component)
- frontend/src/components/marketing/ProcessTimeline.tsx (Visual flow component)
- frontend/src/components/marketing/index.ts (Component exports)
**Files Modified:**
- frontend/src/app/page.tsx (Marketing section integration, removed old Features)
- frontend/src/app/portfolio/page.tsx (ClientCreateInput type fix)
- frontend/src/components/portfolio/CreateClientModal.tsx (framer-motion fix)
- frontend/src/components/auth/ProfileDropdown.tsx (Version 0.15.0)
- backend/main.py (Version 0.15.0)
- tasks/todo.md (Sprint 23 checklist)
- logs/dev-log.md (Brand-Integrated Feature Set documentation)
- CLAUDE.md (Project state update)
**Zero-Storage Verified:** Marketing components are stateless; no new storage introduced
**Lessons Documented:**
- Brand-Integrated Marketing: Component-based approach for consistent branding
- framer-motion Type Assertions: Always use `as const` for transition.type values

---

### Sprint 24 Review (FINAL SPRINT)
**Status:** Complete
**Blockers:** None
**Focus:** Production Deployment Prep — Containerization, security hardening, deployment docs
**Architecture Decision:** Separated frontend/backend deployment with multi-stage Docker builds
**Notes:**
- Created multi-stage Backend Dockerfile with Python 3.11-slim and Gunicorn
- Created multi-stage Frontend Dockerfile with Node 20-alpine and standalone output
- Created docker-compose.yml for local development orchestration
- Created secrets_manager.py with multi-backend support (env, Docker secrets, cloud providers)
- Enhanced CORS policy: blocks wildcards and warns on non-HTTPS in production
- Added Next.js standalone output mode for optimized Docker deployments
- Created comprehensive DEPLOYMENT.md with Vercel, Render, DigitalOcean guides
- Updated .env.example files with extensive production annotations
- API version bumped to 0.16.0 (FINAL)
**Files Created:**
- backend/Dockerfile (Multi-stage Python production image)
- frontend/Dockerfile (Multi-stage Node.js production image)
- docker-compose.yml (Local development orchestration)
- backend/secrets_manager.py (Production credential management)
- DEPLOYMENT.md (Comprehensive deployment guide)
**Files Modified:**
- backend/config.py (Enhanced production CORS validation)
- backend/.env.example (Production template annotations)
- frontend/.env.example (Production template annotations)
- frontend/next.config.js (Added output: 'standalone')
- backend/main.py (Version 0.16.0, Sprint 24 reference)
- frontend/src/components/auth/ProfileDropdown.tsx (Version 0.16.0)
- tasks/todo.md (Sprint 24 checklist)
- logs/dev-log.md (Production-Grade Stateless Infrastructure documentation)
- CLAUDE.md (Project state: PRODUCTION READY)
**Zero-Storage Verified:** All containers process data in-memory only; database stores only metadata
**Lessons Documented:**
- Multi-stage Docker builds for minimal production images
- Next.js standalone output for containerization

---

### Sprint 25 Review (Phase II Start)
**Status:** Complete
**Blockers:** None
**Focus:** Foundation Hardening — Test suite creation and multi-sheet bug fix
**Architecture Decision:** Per-sheet column detection with mismatch warnings
**Notes:**
- Created comprehensive ratio_engine test suite with 47 test cases
- Tests cover all 4 ratios: Current, Quick, Debt-to-Equity, Gross Margin
- Tests cover edge cases: division-by-zero, negative values, boundary conditions
- Tests cover CommonSizeAnalyzer, VarianceAnalyzer, CategoryTotals
- Fixed multi-sheet column detection to run independently per sheet
- Added `sheet_column_detections` field to API response
- Added `column_order_warnings` array when sheets have different column layouts
- Added `has_column_order_mismatch` boolean flag for frontend detection
- Backward compatible: `column_detection` still returns first sheet's detection
- Total backend tests: 82 (up from 31)
**Files Created:**
- backend/tests/test_ratio_engine.py (47 test cases)
**Files Modified:**
- backend/audit_engine.py (per-sheet column detection in audit_trial_balance_multi_sheet)
- backend/tests/test_audit_engine.py (6 new multi-sheet column detection tests)
- tasks/todo.md (Sprint 25 checklist)
**Zero-Storage Verified:** No new storage introduced; column detection remains in-memory only
**Lessons Documented:**
- Per-sheet column detection prevents silent data errors in multi-sheet audits
- Column mismatch warnings enable user awareness without blocking processing

---

### Sprint 26 Review
**Status:** Complete
**Blockers:** None
**Focus:** Profitability Ratios — Net Profit Margin and Operating Margin
**Architecture Decision:** Operating expenses extracted via keyword matching, with non-operating exclusions
**Notes:**
- Added Net Profit Margin: (Revenue - Total Expenses) / Revenue
- Added Operating Margin: (Revenue - COGS - Operating Expenses) / Revenue
- Added `operating_expenses` field to CategoryTotals dataclass
- Added 30+ OPERATING_EXPENSE_KEYWORDS (salaries, rent, utilities, marketing, etc.)
- Added NON_OPERATING_KEYWORDS to exclude interest, tax, extraordinary items
- Operating Margin falls back to (total_expenses - COGS) if operating_expenses is 0
- Interpretation thresholds: Excellent (20%+), Healthy (10%+), Warning (5%+), Concern (<0%)
- Total backend tests: 96 (ratio_engine: 61 tests, up from 47)
**Files Modified:**
- backend/ratio_engine.py (CategoryTotals, RatioEngine, extract_category_totals, keywords)
- backend/tests/test_ratio_engine.py (14 new tests: 6 Net Profit, 6 Operating, 2 extraction)
- tasks/todo.md (Sprint 26 checklist)
**Zero-Storage Verified:** No new storage; ratios calculated in-memory from category totals
**Lessons Documented:**
- Keyword-based expense classification with exclusion lists for clean operating vs non-operating separation

---

### Sprint 27 Review
**Status:** Complete
**Blockers:** None
**Focus:** Return Metrics — ROA and ROE for investor-facing analysis
**Architecture Decision:** Net Income calculated from category totals (Revenue - Total Expenses)
**Notes:**
- Added Return on Assets (ROA): Net Income / Total Assets × 100%
- Added Return on Equity (ROE): Net Income / Total Equity × 100%
- ROA interpretation: Excellent (15%+), Strong (10%+), Adequate (5%+), Warning (0%+), Concern (<0%)
- ROE interpretation: Excellent (20%+), Strong (15%+), Adequate (10%+), Warning (0%+), Concern (<0%)
- Special handling for negative equity (technical insolvency warning)
- Fixed test_roa_zero_assets to use proper zero totals fixture
- Fixed test_very_small_numbers to include total_assets and total_expenses
- Total backend tests: 109 (ratio_engine: 74 tests, up from 61)
- 8 ratios now available: Current, Quick, Debt-to-Equity, Gross Margin, Net Profit Margin, Operating Margin, ROA, ROE
**Files Modified:**
- backend/ratio_engine.py (calculate_return_on_assets, calculate_return_on_equity, calculate_all_ratios)
- backend/tests/test_ratio_engine.py (13 new tests: 6 ROA, 7 ROE)
- tasks/todo.md (Sprint 27 checklist)
**Zero-Storage Verified:** No new storage; ratios calculated in-memory from category totals
**Lessons Documented:**
- Test fixtures must match the data requirements of new ratio calculations

---

### Sprint 28 Review
**Status:** Complete
**Blockers:** None
**Focus:** Ratio Dashboard Enhancement — User-visible UI improvements
**Architecture Decision:** Core 4 ratios always visible, Advanced 4 in collapsible section
**Notes:**
- Updated Analytics interface to support all 8 ratios (with optional advanced ratios)
- Implemented 2-column responsive grid layout (1 col mobile, 2 col sm+)
- Added RATIO_FORMULAS constant with formula + description for all 8 ratios
- Formula tooltips appear on hover with animated entrance/exit
- Collapsible "Advanced Ratios" section with framer-motion expand/collapse
- Added trend indicators (↑↓→) with animated entrance based on variance direction
- Enhanced MetricCard with compact mode for advanced ratios
- Added animated value changes (motion key transitions on value prop)
- TypeScript type guards for proper ratio filtering
**Files Created:**
- None (Sprint 28 is enhancement of existing components)
**Files Modified:**
- frontend/src/types/mapping.ts (Analytics interface with 8 ratios)
- frontend/src/components/analytics/MetricCard.tsx (tooltips, trend indicators, compact mode)
- frontend/src/components/analytics/KeyMetricsSection.tsx (8 ratios, collapsible, 2-column grid)
- tasks/todo.md (Sprint 28 checklist)
**Zero-Storage Verified:** No storage changes; UI-only enhancements
**Lessons Documented:**
- TypeScript type guards with `.filter()` for proper type narrowing

---

## Quick Reference

### Phase I (Sprints 8-24) — COMPLETE ✅

| Sprint | Theme | Primary Agent | Status |
|--------|-------|---------------|--------|
| 8 | Testing | QualityGuardian | ✅ |
| 9 | Mapping Logic | BackendCritic + FrontendExecutor | ✅ |
| 9.1 | Brand Foundation | FrontendExecutor | ✅ |
| 9.2 | Column Detection | BackendCritic | ✅ |
| 10 | Risk Dashboard | BackendCritic + FintechDesigner | ✅ |
| 11 | Multi-Sheet Excel | BackendCritic | ✅ |
| 12 | PDF Export | BackendCritic + FrontendExecutor | ✅ |
| 13 | Authentication | BackendCritic + FintechDesigner | ✅ |
| 14 | Activity Logging | BackendCritic + FrontendExecutor | ✅ |
| 15 | Stability Reset | QualityGuardian | ✅ |
| 16 | Client Infrastructure | BackendCritic + FrontendExecutor | ✅ |
| 17 | Portfolio Dashboard | FintechDesigner + FrontendExecutor | ✅ |
| 18 | Diagnostic Fidelity | IntegratorLead + BackendCritic | ✅ |
| 19 | Analytics & Ratios | BackendCritic + FintechDesigner | ✅ |
| 20 | Document Hardening | QualityGuardian + BackendCritic | ✅ |
| 21 | Practice Settings | BackendCritic + FrontendExecutor | ✅ |
| 22 | Sensitivity Tuning | FintechDesigner + FrontendExecutor | ✅ |
| 23 | Marketing Front | FintechDesigner + FrontendExecutor | ✅ |
| 24 | Production Deployment | BackendCritic + QualityGuardian | ✅ |

### Phase II (Sprints 25-40) — COMPLETE ✅

| Sprint | Theme | Primary Agent | Status |
|--------|-------|---------------|--------|
| 25 | Foundation Hardening | QualityGuardian + BackendCritic | ✅ |
| 26 | Profitability Ratios | BackendCritic + FrontendExecutor | ✅ |
| 27 | Return Metrics | BackendCritic + FrontendExecutor | ✅ |
| 28 | Ratio Dashboard Enhancement | FrontendExecutor + FintechDesigner | ✅ |
| 29 | Classical PDF Enhancement | BackendCritic + FintechDesigner | ✅ |
| 30 | IFRS/GAAP Documentation | ProjectAuditor + BackendCritic | ✅ |
| 31 | Classification Intelligence | BackendCritic + FrontendExecutor | ✅ |
| 32 | Materiality Sophistication | BackendCritic + QualityGuardian | ✅ |
| 33 | Trend Analysis Foundation | BackendCritic + FintechDesigner | ✅ |
| 34 | Trend Visualization | FintechDesigner + FrontendExecutor | ✅ |
| 35 | Industry Ratio Foundation | BackendCritic + FintechDesigner | ✅ |
| 36 | Industry Ratio Expansion | BackendCritic + FrontendExecutor | ✅ |
| 37 | Rolling Window Analysis | BackendCritic + FrontendExecutor | ✅ |
| 38 | Batch Upload Foundation | FrontendExecutor + QualityGuardian | ✅ |
| 39 | Batch Upload UI | FintechDesigner + FrontendExecutor | ✅ |
| 40 | Benchmark Framework Design | BackendCritic + ProjectAuditor | ✅ |

---

## Sprint 25: Foundation Hardening ✅ COMPLETE
> **Agent Lead:** QualityGuardian + BackendCritic
> **Consensus:** 5/6 agents ranked test suite in top 3
> **Risk Mitigation:** Address silent bugs before adding features
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### QualityGuardian: Ratio Engine Test Suite
- [x] Create `backend/tests/test_ratio_engine.py`
- [x] Test Current Ratio formula with standard inputs
- [x] Test Quick Ratio formula with standard inputs
- [x] Test Debt-to-Equity formula with standard inputs
- [x] Test Gross Margin formula with standard inputs
- [x] Test division-by-zero handling for each ratio
- [x] Test edge cases: zero values, negative values, None inputs
- [x] Test interpretation threshold boundaries
- [x] Verify all ratios return N/A gracefully when uncalculable

### BackendCritic: Multi-Sheet Column Detection Fix
- [x] Modify `audit_trial_balance_multi_sheet()` in audit_engine.py
- [x] Apply column detection independently to each sheet
- [x] Track per-sheet column mappings in audit response
- [x] Add detection warning if column orders differ across sheets
- [x] Add tests for multi-sheet column detection scenarios

### Sprint 25 Success Criteria
- [x] 100% test coverage for ratio_engine.py (47 tests)
- [x] Multi-sheet audits handle different column orders
- [x] Frontend build passes
- [x] Backend tests pass (82 tests total)

---

## Sprint 26: Profitability Ratios ✅ COMPLETE
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Low complexity, high user value
> **Pattern:** Extend existing ratio_engine.py structure
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Net Profit Margin
- [x] Add Net Profit Margin to ratio_engine.py
- [x] Formula: (Revenue - Total Expenses) / Revenue × 100%
- [x] Add interpretation thresholds (industry-generic)
- [x] Add unit tests for Net Profit Margin (6 tests)

### BackendCritic: Operating Profit Margin
- [x] Add Operating Profit Margin to ratio_engine.py
- [x] Formula: (Revenue - COGS - Operating Expenses) / Revenue × 100%
- [x] Add `operating_expenses` to CategoryTotals dataclass
- [x] Add OPERATING_EXPENSE_KEYWORDS (30+ keywords)
- [x] Add NON_OPERATING_KEYWORDS to exclude interest/tax/extraordinary
- [x] Update extract_category_totals to identify operating expenses
- [x] Add unit tests for Operating Profit Margin (6 tests)

### Sprint 26 Success Criteria
- [x] 6 ratios available (up from 4)
- [x] All ratio tests pass (61 tests, up from 47)
- [x] Frontend build passes

---

## Sprint 27: Return Metrics ✅ COMPLETE
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Key investor-facing metrics
> **Pattern:** Continue ratio expansion
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Return on Assets (ROA)
- [x] Add ROA to ratio_engine.py
- [x] Formula: Net Income / Total Assets × 100%
- [x] Calculate Net Income from category totals
- [x] Add interpretation thresholds
- [x] Add unit tests for ROA (6 tests)

### BackendCritic: Return on Equity (ROE)
- [x] Add ROE to ratio_engine.py
- [x] Formula: Net Income / Total Equity × 100%
- [x] Add interpretation thresholds
- [x] Add unit tests for ROE (7 tests)

### Sprint 27 Success Criteria
- [x] 8 ratios available (target achieved)
- [x] All ratio tests pass (74 ratio_engine tests, 109 total backend tests)
- [x] Frontend build passes

---

## Sprint 28: Ratio Dashboard Enhancement ✅ COMPLETE
> **Agent Lead:** FrontendExecutor + FintechDesigner
> **Consensus:** MarketScout #1, FrontendExecutor #1
> **Focus:** User-visible improvements to existing UI
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### FrontendExecutor: Enhanced KeyMetricsSection
- [x] Update KeyMetricsSection to display 8 ratios
- [x] Implement 2-column grid layout for ratios (1 col mobile, 2 col sm+)
- [x] Add ratio tooltips with formula explanations (RATIO_FORMULAS constant)
- [x] Implement collapsible "Advanced Ratios" section with framer-motion

### FintechDesigner: Ratio Card Refinement
- [x] Add trend indicators (↑↓→) based on variance data
- [x] Design "healthy/warning/critical" visual states (via getHealthClasses)
- [x] Apply Tier 2 semantic colors (Sage/Clay)
- [x] Add subtle animations for value changes (motion key transitions)

### Sprint 28 Success Criteria
- [x] All 8 ratios visible in dashboard (Core 4 + Advanced 4 collapsible)
- [x] Tooltips display formulas (hover to reveal formula + description)
- [x] Trend indicators functional (↑↓→ with animated entrance)
- [x] Oat & Obsidian compliance verified (frontend build passes)

---

## Sprint 29: Classical PDF Enhancement — "Renaissance Ledger" ✓ COMPLETE
> **Agent Lead:** BackendCritic + FintechDesigner
> **Source:** CEO Directive + FintechDesigner Consultation (2026-02-04)
> **Focus:** Transform PDF reports into classical, institutional documents honoring Luca Pacioli
> **Philosophy:** "Renaissance Ledger Meets Modern Institution"
> **Completed:** 2026-02-04

### Tier 1: Foundation (High Impact, Low Effort)

#### BackendCritic: Typography Upgrade
- [x] Use built-in Times-Roman family for reliable cross-platform rendering
- [x] Update ClassicalTitle style: Times-Bold, 28pt (institutional authority)
- [x] Update SectionHeader style: Times-Bold, 12pt with letterspacing
- [x] Update BodyText style: Times-Roman, 10pt
- [x] Added ClassicalColors class with full palette

#### BackendCritic: Leader Dots for Summary Metrics
- [x] Create `create_leader_dots(label, value, total_chars)` utility function
- [ ] Replace summary table with leader-dot layout:
- [x] Replace summary table with leader-dot layout in executive summary
- [x] Align values to right margin with proper dot spacing

#### BackendCritic: Double-Rule Borders
- [x] Add gold double rule (2pt + 0.5pt gap) at document top (canvas callback)
- [x] Add single hairline rule at document bottom
- [x] Add `GOLD_INSTITUTIONAL` color: #B8934C to ClassicalColors
- [x] Create DoubleRule Flowable class for reusable borders

#### FintechDesigner: Small Caps Section Headers
- [x] Implement letterspaced headers: `E X E C U T I V E   S U M M A R Y`
- [x] Add LedgerRule underline below each section header
- [x] Diamond ornament `─── ◆ ───` under main title

### Tier 2: Ledger Aesthetic (Medium Effort)

#### BackendCritic: Ledger-Style Tables
- [x] Remove vertical grid lines from anomaly tables (ledger aesthetic)
- [x] Use horizontal hairlines only (0.25pt in LEDGER_RULE #D4CFC5)
- [x] Keep left "margin line" as accent rule (CLAY for material, OBSIDIAN for minor)
- [x] Add row totals at bottom of anomaly tables
- [x] Alternating row backgrounds (white/OATMEAL_PAPER)

#### FintechDesigner: Section Ornaments
- [x] Add fleuron ornament `❧` between major sections (in SAGE color)
- [x] Diamond rule `─── ◆ ───` as title break
- [x] Center ornaments with proper spacing (Spacer before/after)

#### BackendCritic: Warm Paper Background
- [x] Add `OATMEAL_PAPER` color: #F7F5F0 to ClassicalColors
- [x] Apply as table cell background and badge background
- [x] Text contrast remains accessible (OBSIDIAN_DEEP for headings)

#### BackendCritic: Classical Formatting
- [x] Page numbers: `— 1 —` format (em dashes, centered)
- [x] Date format: `4th February 2026` (ordinal, spelled month)
- [x] Reference number: `PAC-YYYY-MMDD-NNN` format (generate_reference_number)

### Tier 3: Premium Polish (Higher Effort)

#### BackendCritic: Pacioli Watermark
- [x] Create diagonal watermark text: "Particularis de Computis"
- [x] Opacity: 4% (barely perceptible)
- [x] Position: centered, 45° rotation
- [x] Applied via `_draw_page_decorations` canvas callback

#### FintechDesigner: Status Badge Redesign
- [x] Classical "seal" box with thick border
- [x] SAGE border for balanced, CLAY border for unbalanced
- [x] Checkmark (✓) for balanced, warning (⚠) for unbalanced
- [x] Letterspaced status text: `✓   B A L A N C E D`

#### BackendCritic: Footer Enhancement
- [x] Add Pacioli motto in italic: *"Particularis de Computis et Scripturis"*
- [x] Footer with FooterMotto style (gold, italic)
- [x] Zero-Storage message remains prominent
- [x] Legal disclaimer on every page

### Sprint 29 Success Criteria ✓
- [x] PDF uses classical serif typography (Times family)
- [x] Leader dots replace summary table
- [x] Double-rule gold border at top of document
- [x] Section headers in small caps with letterspacing
- [x] Tables use ledger-style horizontal rules only
- [x] Warm paper background (#F7F5F0) on badges and tables
- [x] Classical page numbers and date format
- [x] Multiple section ornaments implemented (fleuron ❧, diamond ◆)
- [x] PDF feels like "Goldman Sachs meets Renaissance ledger"

### Sprint 29 Review
**Implementation Notes:**
- Used built-in Times fonts instead of custom web fonts for reliability
- ReportLab's Times-Roman/Bold provides consistent cross-platform rendering
- No font file management overhead - simplifies deployment
- All 3 Tiers completed in single sprint (Tier 1 + Tier 2 + Tier 3)

**Key Deliverables:**
1. `ClassicalColors` class with institutional palette
2. `DoubleRule` and `LedgerRule` custom Flowables
3. `create_leader_dots()` utility for financial summaries
4. `format_classical_date()` for ordinal date formatting
5. `generate_reference_number()` for institutional references
6. Complete PDF generator rewrite with Renaissance Ledger aesthetic

**Design Philosophy Achieved:**
- Honors Luca Pacioli (father of accounting)
- Feels like Goldman Sachs/Deloitte institutional quality
- Maintains Oat & Obsidian brand identity
- Zero-Storage compliance preserved

---

## Sprint 30: IFRS/GAAP Documentation ✓ COMPLETE
> **Agent Lead:** ProjectAuditor + BackendCritic
> **Consensus:** Low effort, compliance improvement
> **Focus:** Professional documentation
> **Note:** Renumbered from Sprint 29 to accommodate Classical PDF Enhancement
> **Completed:** 2026-02-04

### ProjectAuditor: IFRS Guidance Notes
- [x] Add IFRS vs GAAP differences to ratio docstrings
- [x] Note classification differences in classification_rules.py comments
- [x] Create STANDARDS.md with framework comparison
- [x] Add tooltips to UI for standard-specific guidance

### BackendCritic: Classification Commentary
- [x] Add docstrings explaining classification logic
- [x] Note where IFRS/GAAP differ in account categorization
- [x] Document deferred revenue, lease accounting considerations

### Sprint 30 Success Criteria ✓
- [x] STANDARDS.md created (docs/STANDARDS.md - comprehensive framework comparison)
- [x] Ratio docstrings include standard references (all 8 ratios documented)
- [x] Classification rules documented (header docstring + section comments)
- [x] Frontend tooltips added (standardNote field in RATIO_FORMULAS)

### Sprint 30 Review
**Deliverables:**
1. `docs/STANDARDS.md` - Comprehensive IFRS/GAAP comparison document
2. Enhanced `ratio_engine.py` - All ratio methods have IFRS/GAAP docstrings
3. Enhanced `classification_rules.py` - Header docs + section comments for IFRS/GAAP
4. Enhanced `MetricCard.tsx` - standardNote field displayed in tooltips

**Key Documentation Added:**
- Ratio-specific framework differences (LIFO, revaluations, R&D capitalization)
- Classification implications (deferred revenue, leases, provisions)
- Cross-standard comparability warnings
- Industry-specific threshold guidance

---

## Sprint 31: Classification Intelligence ✓ COMPLETE
> **Note:** Renumbered from Sprint 30
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Medium priority, reduces user friction
> **Focus:** Smarter auto-classification
> **Completed:** 2026-02-04

### BackendCritic: Classification Suggestions
- [x] When confidence < 50%, return top 3 alternative classifications
- [x] Implement Levenshtein distance for fuzzy matching
- [x] Add "Did you mean?" suggestions to API response
- [ ] Track suggestion acceptance rate (metadata only) — Deferred: requires activity log changes

### FrontendExecutor: Suggestion UI
- [x] Display classification suggestions in UI
- [x] Allow one-click acceptance of suggestions
- [x] Show confidence scores for alternatives
- [x] Maintain Zero-Storage compliance (session only)

### Sprint 31 Success Criteria ✓
- [x] Suggestions appear for low-confidence classifications
- [x] One-click acceptance functional
- [x] Zero-Storage compliance verified

### Sprint 31 Review
**Backend Deliverables:**
1. `levenshtein_distance()` — Edit distance calculation for fuzzy matching
2. `fuzzy_match_score()` — Converts Levenshtein distance to 0-1 score
3. `ClassificationSuggestion` dataclass — Holds suggestion data
4. `_generate_suggestions()` — Top 3 alternatives from keyword scores
5. `_generate_fuzzy_suggestions()` — Fallback using Levenshtein matching
6. Updated `ClassificationResult` — Now includes suggestions list
7. Updated `audit_engine.py` — Includes suggestions in abnormal_balances

**Frontend Deliverables:**
1. `ClassificationSuggestion` type — TypeScript interface
2. Updated `AbnormalBalanceExtended` — Includes suggestions array
3. Updated `AnomalyCard` — "Did you mean?" collapsible suggestions UI
4. One-click suggestion acceptance with visual feedback

**Design:**
- Suggestions only appear for confidence < 50%
- Maximum 3 suggestions per account
- Fuzzy matching catches misspellings (Levenshtein distance ≤ 2)
- Premium styling with Oat & Obsidian theme

---

## Sprint 32: Materiality Sophistication (COMPLETE)
> **Agent Lead:** BackendCritic + QualityGuardian
> **Consensus:** Medium complexity, professional feature
> **Focus:** Weighted materiality by account type
> **Note:** Renumbered from Sprint 31
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Weighted Materiality Schema
- [x] Design weighted materiality configuration
- [x] Define account type weights (Asset 1.0x, Liability 1.2x, Equity 1.5x, Revenue 1.3x, Expense 0.8x)
- [x] Add balance_sheet_weight vs income_statement_weight
- [x] Implement in practice_settings.py (WeightedMaterialityConfig model)

### QualityGuardian: Materiality Edge Cases
- [x] Test weighted materiality calculations (24 tests in test_weighted_materiality.py)
- [x] Test weight priority resolution
- [x] Test override behavior
- [x] Verify Zero-Storage compliance (only weights stored, never financial data)

### Sprint 32 Success Criteria
- [x] Weighted materiality configurable (WeightedMaterialityEditor component)
- [x] Tests pass for edge cases (133 total backend tests passing)
- [x] Settings UI updated (/settings page with expandable weight editor)
- [x] Zero-Storage compliance verified (weights are configuration only)

---

## Sprint 33: Trend Analysis Foundation ✅ COMPLETE
> **Agent Lead:** BackendCritic + FintechDesigner
> **Consensus:** FintechDesigner #2, medium complexity
> **Focus:** Multi-period data infrastructure
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Historical Snapshot Storage
- [x] Extend DiagnosticSummary to store period identifier (period_date, period_type columns)
- [x] Add period_type enum (monthly, quarterly, annual) - PeriodType enum in models.py
- [x] Implement get_historical_snapshots() method - via /clients/{id}/trends endpoint
- [x] Add API endpoint for historical data retrieval - GET /clients/{client_id}/trends

### BackendCritic: Variance Time Series
- [x] Extend VarianceAnalyzer for multi-period comparison - TrendAnalyzer class
- [x] Calculate period-over-period changes - TrendPoint with change_from_previous
- [x] Calculate trend direction (up/down/flat) - TrendDirection enum (POSITIVE/NEGATIVE/NEUTRAL)
- [x] Store trend metadata (not raw data) - TrendSummary with aggregates only

### Sprint 33 Success Criteria
- [x] Historical snapshots retrievable (GET /clients/{id}/trends endpoint)
- [x] Period-over-period variance calculated (TrendAnalyzer with 14 tests)
- [x] API endpoint functional (tested with pytest)
- [x] Zero-Storage compliance (metadata only - no raw data stored)

---

## Sprint 34: Trend Visualization ✅ COMPLETE
> **Agent Lead:** FintechDesigner + FrontendExecutor
> **Consensus:** High visual impact
> **Focus:** Sparkline charts and trend display
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### FintechDesigner: Trend Chart Design
- [x] Design sparkline components for ratio trends - TrendSparkline.tsx
- [x] Define Oat & Obsidian chart palette - CHART_COLORS constant
- [x] Design "trend summary" card layout - TrendSummaryCard.tsx
- [x] Specify animation behavior for chart drawing - framer-motion + recharts animation

### FrontendExecutor: Chart Implementation
- [x] Integrate lightweight chart library (recharts/visx) - recharts installed
- [x] Create TrendSparkline component - TrendSparkline.tsx + TrendSparklineMini
- [x] Create TrendSummaryCard component - with min/max/avg stats
- [x] Create TrendSection component - integrates with dashboard
- [x] Create useTrends hook - API integration for /clients/{id}/trends

### Sprint 34 Success Criteria
- [x] Sparklines display historical trends (recharts LineChart)
- [x] Oat & Obsidian theme applied (sage/clay/obsidian colors)
- [x] Animations smooth and professional (framer-motion + recharts)
- [x] Mobile responsive (sm:grid-cols-2 responsive grid)

---

## Sprint 35: Industry Ratio Foundation (COMPLETE)
> **Agent Lead:** BackendCritic + FintechDesigner
> **Consensus:** Medium priority, differentiation feature
> **Focus:** Industry-specific calculation groundwork
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Industry Ratios Module
- [x] Create backend/industry_ratios.py
- [x] Define base IndustryRatioCalculator class
- [x] Implement Manufacturing ratios:
  - [x] Inventory Turnover (COGS / Average Inventory)
  - [x] Days Inventory Outstanding
  - [x] Asset Turnover (Revenue / Total Assets)
- [x] Map Industry enum to ratio sets
- [x] Implement Retail ratios (bonus):
  - [x] Inventory Turnover (retail benchmarks)
  - [x] GMROI (Gross Margin Return on Inventory)
- [x] Create GenericIndustryCalculator fallback
- [x] Factory pattern for industry-to-calculator mapping

### QualityGuardian: Industry Ratio Tests
- [x] Test all manufacturing ratios (12 tests)
- [x] Test retail ratios (8 tests)
- [x] Test industry-ratio mapping (9 tests)
- [x] Test edge cases per industry (15 tests)
- [x] 44 total industry ratio tests

### Sprint 35 Success Criteria
- [x] Manufacturing ratios implemented (Inventory Turnover, DIO, Asset Turnover)
- [x] Retail ratios implemented (Inventory Turnover, GMROI)
- [x] Tests pass for industry ratios (44/44)
- [x] Industry mapping functional (factory pattern)
- [x] 191 total backend tests pass

### Sprint 35 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Factory pattern with abstract base class for extensible industry calculators
**Notes:**
- Created IndustryRatioCalculator ABC with calculate_all() and get_ratio_names() abstract methods
- ManufacturingRatioCalculator with 3 ratios and industry-specific health thresholds
- RetailRatioCalculator with 2 ratios and higher benchmark expectations
- GenericIndustryCalculator as fallback for unmapped industries
- INDUSTRY_CALCULATOR_MAP for type-safe industry-to-calculator mapping
- Factory function get_industry_calculator() handles case-insensitive matching
- IndustryRatioResult dataclass with benchmark_note for context
- IndustryTotals extends CategoryTotals with average_inventory, fixed_assets, etc.
**Files Created:**
- backend/industry_ratios.py (industry ratio engine)
- backend/tests/test_industry_ratios.py (44 tests)
**Test Results:** 191/191 backend tests passed
**Zero-Storage Verified:** All calculations use aggregate totals only

---

## Sprint 36: Industry Ratio Expansion (COMPLETE)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Continue industry customization
> **Focus:** Additional industry implementations + Dashboard integration
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Retail & Services Ratios
- [x] Implement Retail ratios (completed in Sprint 35):
  - [x] Inventory Turnover (retail benchmarks)
  - [x] Gross Margin Return on Inventory (GMROI)
- [x] Implement Professional Services ratios:
  - [x] Revenue per Employee (requires employee_count)
  - [x] Utilization Rate (requires billable_hours data)
  - [x] Revenue per Billable Hour (bonus ratio)
- [x] Add placeholder messaging for unavailable metrics ("Data Required")
- [x] Add API endpoint for industry ratios

### FrontendExecutor: Industry Dashboard Section
- [x] Create IndustryMetricsSection component
- [x] Display industry-relevant ratios based on client classification
- [x] Show "Data Required" for metrics requiring additional data
- [x] Add industry context tooltip with benchmark notes
- [x] Oat & Obsidian theme compliance
- [x] Create useIndustryRatios hook for API integration

### QualityGuardian: Industry Ratio Tests
- [x] Test Professional Services calculator (17 tests)
- [x] Test placeholder messaging
- [x] Test factory function updates
- [x] 208 total backend tests pass

### Sprint 36 Success Criteria
- [x] Professional Services ratios implemented (3 ratios)
- [x] Placeholder messaging for unavailable metrics
- [x] Industry section dashboard component ready
- [x] API endpoint functional (GET /clients/{id}/industry-ratios)
- [x] Oat & Obsidian compliant

### Sprint 36 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** Extended IndustryTotals with optional fields for services data (employee_count, billable_hours, total_hours)
**Notes:**
- ProfessionalServicesRatioCalculator with 3 ratios: Revenue/Employee, Utilization Rate, Revenue/Hour
- Placeholder messaging guides users on what data is needed for unavailable metrics
- IndustryMetricsSection component with industry icons, benchmark tooltips, collapsible section
- useIndustryRatios hook for clean API integration
- GET /clients/{id}/industry-ratios endpoint returns industry-specific ratios
**Files Created:**
- frontend/src/components/analytics/IndustryMetricsSection.tsx
- frontend/src/hooks/useIndustryRatios.ts
**Files Modified:**
- backend/industry_ratios.py (Professional Services calculator)
- backend/tests/test_industry_ratios.py (17 new tests)
- backend/main.py (industry-ratios endpoint)
- frontend/src/components/analytics/index.ts (exports)
- frontend/src/hooks/index.ts (exports)
**Test Results:** 208/208 backend tests passed
**Frontend Build:** Success (Next.js 16.1.6)
**Zero-Storage Verified:** All calculations use aggregate totals only

---

## Sprint 37: Rolling Window Analysis (COMPLETE)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Advanced analytics feature
> **Focus:** 3/6/12 month rolling calculations
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Rolling Window Calculations
- [x] Create RollingWindowAnalyzer class in ratio_engine.py
- [x] Implement 3-month rolling average
- [x] Implement 6-month rolling average
- [x] Implement 12-month rolling average
- [x] Calculate trend momentum (acceleration/deceleration)
- [x] Add API endpoint for rolling analysis

### FrontendExecutor: Rolling Window UI
- [x] Create RollingWindowSection component
- [x] Add period selector (3/6/12 month)
- [x] Display rolling averages in metric cards
- [x] Show momentum indicators (accelerating/decelerating/steady/reversing)
- [x] Collapsible financial ratios section
- [x] Create useRollingWindow hook

### QualityGuardian: Rolling Window Tests
- [x] Test rolling average calculations (17 tests)
- [x] Test momentum detection
- [x] Test edge cases (insufficient data, empty snapshots)
- [x] Test serialization (to_dict methods)

### Sprint 37 Success Criteria
- [x] Rolling windows calculated correctly (3/6/12 month)
- [x] Period selector functional
- [x] Momentum indicators display (accelerating/decelerating/steady/reversing)
- [x] Tests pass (225 total backend tests)
- [x] Oat & Obsidian compliant

### Sprint 37 Review
**Status:** Complete
**Blockers:** None
**Architecture Decision:** RollingWindowAnalyzer extends TrendAnalyzer pattern with rolling average calculations and momentum detection
**Notes:**
- RollingWindowAnalyzer with support for 3/6/12 month rolling windows
- MomentumType enum: ACCELERATING, DECELERATING, STEADY, REVERSING
- Momentum confidence calculation based on rate consistency
- RollingAverage dataclass with window_months, data_points, date range
- MomentumIndicator with rate_of_change, acceleration, confidence
- GET /clients/{id}/rolling-analysis endpoint with window and period_type filters
- RollingWindowSection component with period selector buttons
- useRollingWindow hook for clean API integration
**Files Created:**
- frontend/src/components/analytics/RollingWindowSection.tsx
- frontend/src/hooks/useRollingWindow.ts
**Files Modified:**
- backend/ratio_engine.py (RollingWindowAnalyzer, MomentumType, dataclasses)
- backend/tests/test_ratio_engine.py (17 new tests)
- backend/main.py (rolling-analysis endpoint)
- frontend/src/components/analytics/index.ts (exports)
- frontend/src/hooks/index.ts (exports)
**Test Results:** 225/225 backend tests passed (17 new rolling window tests)
**Frontend Build:** Success (Next.js 16.1.6)
**Zero-Storage Verified:** All calculations use aggregate totals only

---

## Sprint 38: Batch Upload Foundation (COMPLETE)
> **Agent Lead:** FrontendExecutor + QualityGuardian
> **Consensus:** High complexity, needs careful design
> **Focus:** Multi-file infrastructure (not UI)
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### FrontendExecutor: Batch State Management
- [x] Design multi-file state architecture
- [x] Create BatchUploadContext for file queue
- [x] Define FileQueueItem and BatchStatus types
- [x] Implement useBatchUpload hook
- [x] Handle individual file errors gracefully

### QualityGuardian: Batch Error Handling
- [x] Define error states for batch processing
- [x] Implement partial success handling
- [x] File validation utilities
- [x] Verify Zero-Storage compliance (all files in memory)

### Sprint 38 Success Criteria
- [x] Batch state architecture documented
- [x] BatchUploadContext functional
- [x] File queue management works
- [x] Error handling implemented
- [x] Zero-Storage compliance verified

### Implementation Summary
- `frontend/src/types/batch.ts`: FileStatus, BatchStatus, FileQueueItem types with validation utilities
- `frontend/src/context/BatchUploadContext.tsx`: Reducer-based state management with queue operations
- `frontend/src/hooks/useBatchUpload.ts`: Convenience hook with BatchStats and derived state
- Zero-Storage: All files in React state (memory only), queue cleared on unmount

---

## Sprint 39: Batch Upload UI (COMPLETE)
> **Agent Lead:** FintechDesigner + FrontendExecutor
> **Consensus:** Complete batch feature
> **Focus:** User-facing batch experience
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### FintechDesigner: Batch Upload Design
- [x] Design multi-file dropzone
- [x] Design file queue list with status indicators
- [x] Design batch progress visualization
- [x] Define Oat & Obsidian batch styling

### FrontendExecutor: Batch Upload Implementation
- [x] Implement multi-file dropzone
- [x] Create FileQueueList component
- [x] Implement batch progress bar
- [x] Add "Process All" / "Clear Queue" / "Retry Failed" buttons

### Sprint 39 Success Criteria
- [x] Multi-file upload functional
- [x] File queue displays correctly
- [x] Progress tracking works
- [x] Oat & Obsidian compliant

### Implementation Summary
- `components/batch/BatchDropZone.tsx`: Multi-file drag-and-drop with validation
- `components/batch/FileQueueItem.tsx`: Individual file row with status/progress
- `components/batch/FileQueueList.tsx`: Scrollable queue with staggered animations
- `components/batch/BatchProgressBar.tsx`: Overall progress with animated bar
- `components/batch/BatchUploadControls.tsx`: Process All, Clear, Cancel, Retry buttons
- `components/batch/BatchUploadPanel.tsx`: Composite panel combining all elements

---

## Sprint 40: Benchmark Framework Design (COMPLETE)
> **Agent Lead:** BackendCritic + ProjectAuditor
> **Consensus:** Phase III kickoff
> **Focus:** Architecture design only (not implementation)
> **Started:** 2026-02-04
> **Completed:** 2026-02-04

### BackendCritic: Benchmark Architecture RFC
- [x] Design benchmark data schema
- [x] Define industry benchmark sources (public data)
- [x] Design comparison calculation approach
- [x] Document Zero-Storage implications (benchmark data is reference, not client data)

### ProjectAuditor: Benchmark Documentation
- [x] Create BENCHMARKS.md with framework design
- [x] Document data sources and licensing
- [x] Define Phase III implementation scope
- [x] Add benchmark roadmap to Phase III planning

### Sprint 40 Success Criteria
- [x] Benchmark RFC complete
- [x] Data sources identified
- [x] Architecture documented
- [x] Phase III scope defined

### Implementation Summary
- `docs/BENCHMARKS.md`: Comprehensive RFC document (700+ lines)
- Data schema: IndustryBenchmark, BenchmarkComparison, BenchmarkSet dataclasses
- Sources: RMA, SEC EDGAR, BLS, FRED identified with licensing notes
- Percentile calculation algorithm with linear interpolation
- Zero-Storage compliance architecture documented
- API design: /benchmarks/{industry}, /benchmarks/compare endpoints
- Frontend components: BenchmarkCard, PercentileBar designs
- Phase III roadmap: Sprints 41-47 defined

---

## Phase III: Diagnostic Intelligence & Benchmarks (Sprints 41-47)

> **Source:** Agent Council Discussion (2026-02-04)
> **Input:** Accounting Expert Auditor recommendations evaluated by 5 specialist agents
> **Consensus:** Implement 3 detection features immediately, defer 2 to Phase IV

### Phase III Overview

| Sprint | Feature | Complexity | Tests | Agent Lead | Status |
|--------|---------|:---:|:---:|:---|:---:|
| 41 | Performance & Refactoring | 3/10 | 16 | IntegratorLead | ✅ |
| 42 | Suspense Account Detector | 2/10 | 34 | BackendCritic + FrontendExecutor | Planned |
| 43 | Concentration Risk + Rounding Anomaly | 4-5/10 | 86 | BackendCritic + FintechDesigner | Planned |
| 44 | Balance Sheet Validator (conditional) | 1/10 | 34 | BackendCritic | Planned |
| 45 | Benchmark Schema Implementation | 3/10 | 20 | BackendCritic | Planned |
| 46 | Benchmark Comparison Engine | 4/10 | 30 | BackendCritic + QualityGuardian | Planned |
| 47 | Benchmark Frontend Components | 3/10 | 15 | FrontendExecutor + FintechDesigner | Planned |
| 48 | Benchmark Integration & Testing | 2/10 | 25 | QualityGuardian | Planned |

**Deferred to Phase IV:**
- Contra-Account Validator (High complexity, requires industry-specific logic)

---

## Sprint 42: Suspense Account Detector (PLANNED)
> **Note:** Renumbered from original Sprint 41 plan. Sprint 41 was used for Performance & Refactoring work.
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** High impact, low effort, existing partial code in recon_engine.py
> **Focus:** Detect clearing/suspense accounts with non-zero balances

### Prerequisites (Complete before Sprint 41)
- [ ] Add `category` field to `abnormal_balances` response (5 min)
- [ ] Add `DetectionSettings` to `practice_settings.py` (30 min)
- [ ] Create test fixtures for multi-account scenarios (1 hour)

### BackendCritic: Suspense Detection Engine
- [ ] Create `SuspenseDetector` class in new `detection_engine.py`
- [ ] Define keyword list: "suspense", "clearing", "miscellaneous", "sundry", "other", "unallocated", "temporary", "holding"
- [ ] Logic: If account name contains keyword AND balance != 0, flag
- [ ] Add `AnomalyType.SUSPENSE_ACCOUNT` enum value
- [ ] Integrate with StreamingAuditor response

### FrontendExecutor: Suspense Alert UI
- [ ] Create `SuspenseAlertCard` component (Tier 1 - always visible)
- [ ] Clay-red left border accent (Premium Restraint)
- [ ] Display: account name, balance, suggested action
- [ ] Add to RiskDashboard section

### QualityGuardian: Test Coverage
- [ ] 34 test cases for keyword matching
- [ ] Edge cases: Unicode names, case sensitivity, partial matches
- [ ] Zero-balance accounts (should NOT flag)
- [ ] Verify Zero-Storage compliance

### Sprint 42 Success Criteria
- [ ] Suspense accounts detected and displayed
- [ ] 34 new tests passing
- [ ] Zero-Storage verified
- [ ] Oat & Obsidian compliant

---

## Sprint 43: Concentration Risk & Rounding Anomaly (PLANNED)
> **Agent Lead:** BackendCritic + FintechDesigner + QualityGuardian
> **Consensus:** High market value (Concentration), good detection quality (Rounding)
> **Focus:** Two complementary detection features in single sprint

### Part A: Concentration Risk Detector

#### BackendCritic: Concentration Analysis
- [ ] Create `ConcentrationAnalyzer` class in `detection_engine.py`
- [ ] Calculate per-account percentage of category total
- [ ] Configurable threshold (default 25%, stored in DetectionSettings)
- [ ] Flag accounts exceeding threshold with severity levels:
  - Warning: >25% of category
  - Critical: >50% of category
- [ ] Add `AnomalyType.CONCENTRATION_RISK` enum value

#### FintechDesigner: Concentration UI
- [ ] Create `ConcentrationCard` component (Tier 3 - with analytics)
- [ ] Heatmap visualization with gradient bars (sage → oatmeal → clay)
- [ ] Display: account name, percentage, category context
- [ ] Collapsible section in KeyMetricsSection

### Part B: Rounding Anomaly Scanner

#### BackendCritic: Rounding Detection
- [ ] Create `RoundingScanner` class in `detection_engine.py`
- [ ] Check divisibility by 1000, 10000, 100000
- [ ] Score roundness level (low/medium/high)
- [ ] Exclude expected round items (par value stock, etc.)
- [ ] Add `AnomalyType.ROUNDING_ANOMALY` enum value

#### FintechDesigner: Rounding UI
- [ ] Create `RoundingAlertCard` component (Tier 2 - collapsible)
- [ ] Display: account name, balance, roundness score
- [ ] Severity indicator based on score

### QualityGuardian: Combined Test Coverage
- [ ] 43 tests for Concentration Risk:
  - Single-account category (100% is expected, not anomaly)
  - Multi-account threshold calculations
  - Zero-balance handling
- [ ] 43 tests for Rounding Anomaly:
  - Various roundness patterns
  - Legitimate round numbers (estimates, accruals)
  - Negative balances

### Sprint 43 Success Criteria
- [ ] Both detectors functional
- [ ] 86 new tests passing
- [ ] Threshold configurable in settings
- [ ] Zero-Storage verified
- [ ] Oat & Obsidian compliant

---

## Sprint 44: Balance Sheet Equation Validator (CONDITIONAL)
> **Agent Lead:** BackendCritic
> **Consensus:** Low differentiation per MarketScout; implement only if user testing validates demand
> **Focus:** Verify Assets = Liabilities + Equity

### Condition: User Validation Required
- [ ] Conduct user interviews (3-5 financial professionals)
- [ ] Ask: "Would automated A=L+E validation be valuable?"
- [ ] If YES: Proceed with implementation
- [ ] If NO: Skip sprint, proceed to Sprint 44

### BackendCritic: Equation Validator (If Approved)
- [ ] Create `BalanceSheetValidator` class in `detection_engine.py`
- [ ] Calculate: Assets - (Liabilities + Equity) = difference
- [ ] Tolerance: 0.01 (for floating-point precision)
- [ ] Return: is_valid, difference, percentage_variance

### FrontendExecutor: Equation UI (If Approved)
- [ ] Create `EquationValidatorBadge` component
- [ ] States: Success (sage) → Warning (oatmeal) → Error (clay)
- [ ] Display in KeyMetrics footer

### Sprint 44 Success Criteria
- [ ] User validation complete
- [ ] If implemented: 34 tests passing, Zero-Storage verified
- [ ] If skipped: Document decision in Review section

---

## Sprint 45: Benchmark Schema Implementation (PLANNED)
> **Agent Lead:** BackendCritic
> **Consensus:** Per BENCHMARKS.md RFC
> **Focus:** Python models and database schema for benchmarks

### BackendCritic: Benchmark Models
- [ ] Create `benchmark_engine.py` module
- [ ] Implement `IndustryBenchmark` dataclass
- [ ] Implement `BenchmarkComparison` dataclass
- [ ] Implement `BenchmarkSet` dataclass
- [ ] Add benchmark data loading utilities

### BackendCritic: Static Benchmark Data
- [ ] Create `benchmarks/` directory for static data files
- [ ] Curate benchmark tables for 6 priority industries:
  - Retail
  - Manufacturing
  - Professional Services
  - Technology
  - Healthcare
  - Financial Services
- [ ] Source attribution per RFC requirements

### Sprint 45 Success Criteria
- [ ] All benchmark models implemented
- [ ] 20 tests for model validation
- [ ] 6 industries with benchmark data
- [ ] Zero-Storage: Benchmarks are reference data (persistent OK)

---

## Sprint 46: Benchmark Comparison Engine (PLANNED)
> **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** Percentile calculation and comparison logic

### BackendCritic: Comparison Engine
- [ ] Implement `calculate_percentile()` with linear interpolation
- [ ] Implement `generate_interpretation()` for human-readable output
- [ ] Handle ratio direction (higher_is_better vs lower_is_better)
- [ ] Create `/benchmarks/{industry}` endpoint
- [ ] Create `/benchmarks/compare` endpoint

### QualityGuardian: Comprehensive Testing
- [ ] 30 tests for percentile calculation
- [ ] Edge cases: values below p10, above p90
- [ ] Interpolation accuracy tests
- [ ] Direction-aware interpretation tests

### Sprint 46 Success Criteria
- [ ] Comparison engine functional
- [ ] 30 tests passing
- [ ] API endpoints documented
- [ ] Zero-Storage: Comparisons computed in real-time, not stored

---

## Sprint 46: Benchmark Frontend Components ✅ COMPLETE
> **Agent Lead:** FrontendExecutor + FintechDesigner
> **Focus:** BenchmarkCard and PercentileBar components per RFC

### FintechDesigner: Component Design
- [x] Design `BenchmarkCard` component
- [x] Design `PercentileBar` visualization
- [x] Design `BenchmarkSection` dashboard layout
- [x] Oat & Obsidian color mapping for percentile ranges

### FrontendExecutor: Component Implementation
- [x] Implement `BenchmarkCard` with ratio comparison display
- [x] Implement `PercentileBar` with quartile markers
- [x] Implement `BenchmarkSection` collapsible container
- [x] Create `useBenchmarks` hook for API integration

### Sprint 46 Success Criteria
- [x] All benchmark components functional
- [x] Responsive design verified
- [x] Oat & Obsidian compliant

---

## Sprint 47: Benchmark Integration & Testing ✅ COMPLETE
> **Agent Lead:** QualityGuardian
> **Focus:** End-to-end integration and hardening

### QualityGuardian: Integration Testing
- [x] End-to-end benchmark comparison flow
- [x] Multi-industry benchmark switching
- [x] Error handling for missing benchmark data

### FrontendExecutor: Final Integration
- [x] Integrate BenchmarkSection into diagnostic results view
- [x] Industry selector dropdown for benchmark selection
- [x] Source attribution display per RFC

### Phase III Completion
- [x] All 7 sprints complete (41-47)
- [x] 100 new benchmark tests (68 engine + 32 API)
- [x] Phase III features documented in CLAUDE.md
- [x] Git commits for each sprint

### Sprint 47 Success Criteria
- [x] Full benchmark flow working (Upload → Audit → Select Industry → View Comparison)
- [x] 100 benchmark tests passing
- [x] Phase III declared complete

---

## Phase IV Preview: Deferred Features

> **Status:** Not yet planned in detail
> **Source:** Agent Council recommendation to defer

### Contra-Account Validator (Sprint 49+)
- Validate accumulated depreciation ratios against asset base
- Requires industry-specific knowledge
- Better suited as dedicated fixed asset module
- **Prerequisite:** Industry-specific settings framework

### Account Dormancy Indicator (Sprint 50+)
- Compare current vs prior period accounts
- Flag zeroed or new accounts
- Requires stored DiagnosticSummary comparison

---

## Post-Sprint Checklist (Audit 2026-02-04)

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to ✅ COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

**AUDIT FINDING:** Project had only 3 commits for 24 sprints. Each sprint should have at least one atomic commit.

---

## Audit Improvement Actions (2026-02-04)

Based on the 2026-02-04 audit (Score: 4.7/5.0), these improvements were identified:

| Suggestion | Status | Action |
|------------|--------|--------|
| Increase commit frequency | ✅ Done | Added Git Commit step to CLAUDE.md Directive Protocol |
| Add automated test execution | ✅ Done | Added Verification step to Post-Sprint Checklist |
| Log agent invocations | 💡 Future | Consider adding invocation tracking to agents |
| Atomic commits per feature | ✅ Done | Documented commit conventions below |

### Commit Conventions (New)
- **Format:** `Sprint X: Brief Description`
- **Examples:**
  - `Sprint 24: Production Deployment Prep - Dockerfiles and DEPLOYMENT.md`
  - `Sprint 23: Marketing Components - FeaturePillars and ProcessTimeline`
- **Atomic:** One commit per sprint minimum; additional commits for major features OK
- **Avoid:** `git add -A` (may include sensitive files); use specific file paths

---

## Sprint 41: Performance Quick Wins & Shared Utilities ✅ COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** IntegratorLead (Codebase Audit)
> **Focus:** Performance optimization and code consolidation

### Completed Tasks

#### Performance Optimizations
- [x] Replace `.iterrows()` with vectorized pandas in `audit_engine.py`
  - `process_chunk()`: O(unique_accounts) instead of O(rows)
  - `detect_abnormal_balances()`: Pre-computed vectorized masks
- [x] Add `React.memo()` to expensive frontend components
  - AnomalyCard, MetricCard, KeyMetricsSection
- [x] Move `RATIO_TO_VARIANCE_MAP` outside KeyMetricsSection component

#### Shared Utilities Created
- [x] Create `backend/format_utils.py` with `NumberFormatter` class
  - `fmt.currency()`, `fmt.percentage()`, `fmt.ratio()`, `fmt.days()`
  - Consistent rounding precision across codebase
- [x] Create `frontend/src/components/shared/SectionHeader.tsx`
  - Reusable header for analytics sections
  - Configurable icon, title, subtitle, badge, accent color

### Review
**Files Created:**
- `backend/format_utils.py` (206 LOC)
- `frontend/src/components/shared/SectionHeader.tsx` (107 LOC)
- `frontend/src/components/shared/index.ts`

**Files Modified:**
- `backend/audit_engine.py` - Vectorized pandas operations
- `frontend/src/components/risk/AnomalyCard.tsx` - React.memo
- `frontend/src/components/analytics/MetricCard.tsx` - React.memo
- `frontend/src/components/analytics/KeyMetricsSection.tsx` - React.memo + SectionHeader

**Verification:**
- [x] Backend imports successful
- [x] Format utils tested (`fmt.currency(1234.56)` → `$1,234.56`)
- [x] Frontend build passes
- [x] Backend tests: 29/31 passed (2 pre-existing failures)

**Git Commit:** `4df1886` - Sprint 41: Performance Quick Wins & Shared Utilities

---

## Sprint 25 (Addendum): Stability & Security Hardening ✅ COMPLETE
> **Date:** 2026-02-05
> **Focus:** Previously uncommitted stability improvements

### Completed Tasks
- [x] Streamline docstrings across backend modules (-471 lines)
- [x] Add JWT security validation (weak key warnings, public binding detection)
- [x] Add `slowapi` dependency for rate limiting
- [x] Add global `ErrorBoundary` component
- [x] Remove `console.log` in production builds
- [x] Add `MaterialityControl` diagnostic component (placeholder)
- [x] Add Phase III documentation files
- [x] Add accounting-expert-auditor agent persona

**Git Commits:**
- `688f95d` - Sprint 25: Stability & Security Hardening
- `3b6b3a0` - Sprint 25: Frontend Polish & MaterialityControl Component
- `5ee47aa` - Phase III: Documentation & Agent Tools

---

## Sprint 41 Part 2: Medium Priority Refactoring ✅ COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** IntegratorLead (Codebase Audit Continuation)
> **Focus:** Code deduplication and centralized metadata

### Completed Tasks

#### Frontend Refactoring
- [x] Create generic `useFetchData<T>` hook (`frontend/src/hooks/useFetchData.ts`)
  - Type-safe API fetching with auth token handling
  - Configurable URL builder, transform, and data checks
  - Eliminated ~200 lines of duplicate boilerplate
- [x] Refactor `useIndustryRatios.ts` to use useFetchData (125 → 83 LOC)
- [x] Refactor `useRollingWindow.ts` to use useFetchData (198 → 173 LOC)
- [x] Create centralized `types/metrics.ts` with:
  - `MetricInfo` interface for complete metric metadata
  - `RATIO_METRICS` and `CATEGORY_METRICS` definitions
  - Helper functions: `getMetricInfo()`, `formatMetricValue()`, `isPercentageMetric()`
  - Legacy compatibility exports: `RATIO_FORMULAS`, `METRIC_DISPLAY_NAMES`
- [x] Update `MetricCard.tsx` to import from centralized `@/types/metrics`
- [x] Update `useTrends.ts` to use centralized metric definitions

#### Backend Refactoring
- [x] Create `SerializableMixin` class (`backend/serialization.py`)
  - Automatic `to_dict()` for dataclasses
  - Handles enums, dates, nested dataclasses, optional rounding
  - 16 comprehensive tests in `tests/test_serialization.py`
- [x] Add `serialize_dataclass()` standalone function for ad-hoc use

### Review
**Files Created:**
- `frontend/src/hooks/useFetchData.ts` (114 LOC)
- `frontend/src/types/metrics.ts` (350 LOC)
- `backend/serialization.py` (145 LOC)
- `backend/tests/test_serialization.py` (205 LOC)

**Files Modified:**
- `backend/main.py` - GZipMiddleware added
- `frontend/src/components/analytics/MetricCard.tsx` - Import from centralized source
- `frontend/src/components/analytics/index.ts` - Re-export RATIO_FORMULAS
- `frontend/src/hooks/index.ts` - Export useFetchData
- `frontend/src/hooks/useIndustryRatios.ts` - Use useFetchData
- `frontend/src/hooks/useRollingWindow.ts` - Use useFetchData
- `frontend/src/hooks/useTrends.ts` - Use centralized metrics
- `frontend/src/types/index.ts` - Export metrics types

**Verification:**
- [x] Frontend build passes
- [x] Backend tests: 241 passed (225 existing + 16 new serialization tests)

**Net Reduction:** ~200+ lines across duplicate hook implementations

**Git Commit:** `3d1bf73` - Sprint 41: Medium Priority Refactoring - Centralized Metadata & Serialization

---

## Sprint 48: User Profile Settings ✅ COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** FrontendExecutor + BackendCritic
> **Focus:** User profile management and settings page separation

### Completed Tasks

#### Backend: User Profile Endpoints
- [x] Add `name` field to User model (nullable)
- [x] Create database migration for existing users
- [x] UserProfileUpdate schema for profile changes (name, email)
- [x] PasswordChange schema with current password verification
- [x] PUT /users/me endpoint for profile updates
- [x] PUT /users/me/password endpoint for password changes
- [x] Validate new email uniqueness across users

#### Frontend: Settings Architecture
- [x] Separate /settings as hub page with navigation cards
- [x] Create /settings/profile for user profile management
- [x] Create /settings/practice for business settings (materiality formulas)
- [x] Update ProfileDropdown with separate links
- [x] Update WorkspaceHeader to show user name when available

### Success Criteria
- [x] Users can update display name and email
- [x] Password change requires current password verification
- [x] Clean separation: User Settings vs Practice Settings
- [x] Navigation updated throughout app

---

## Sprint 49: Security Hardening ✅ COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic + QualityGuardian
> **Focus:** CSRF protection, security headers, account lockout
> **Complexity:** 4/10

### BackendCritic: Security Headers Middleware
- [x] Create security_middleware.py with SecurityHeadersMiddleware
- [x] Add X-Frame-Options: DENY (prevent clickjacking)
- [x] Add X-Content-Type-Options: nosniff (prevent MIME sniffing)
- [x] Add X-XSS-Protection: 1; mode=block (legacy XSS protection)
- [x] Add Referrer-Policy: strict-origin-when-cross-origin
- [x] Add Content-Security-Policy header for production
- [x] Conditional HSTS for production (Strict-Transport-Security)

### BackendCritic: CSRF Protection
- [x] Implement double-submit cookie pattern for CSRF
- [x] Add CSRF token generation endpoint (GET /auth/csrf)
- [x] Create CSRF validation middleware
- [x] Exempt authentication endpoints (login, register)
- [x] Add X-CSRF-Token header validation for state-changing requests

### BackendCritic: Account Lockout
- [x] Track failed login attempts per user (in-memory)
- [x] Implement lockout after 5 failed attempts (15 min timeout)
- [x] Return lockout status in login error responses
- [x] Auto-reset counter on successful login
- [x] Privacy-compliant IP hashing for logging

### QualityGuardian: Security Tests
- [x] Test security headers presence in responses (5 tests)
- [x] Test CSRF token generation and validation (9 tests)
- [x] Test account lockout triggers and recovery (12 tests)
- [x] Test utility functions (3 tests)
- [x] Integration tests for protected endpoints (4 tests)

### Sprint 49 Success Criteria
- [x] Security headers on all responses
- [x] CSRF protection for POST/PUT/DELETE endpoints
- [x] Account lockout mechanism functional
- [x] All existing tests pass (421/422)
- [x] New security tests pass (33/34, 1 skipped)
- [x] Frontend build passes

### Sprint 49 Review
**Status:** Complete
**Files Created:**
- `backend/security_middleware.py` (SecurityHeadersMiddleware, CSRFMiddleware, account lockout functions)
- `backend/tests/test_security.py` (34 tests, 33 passed, 1 skipped)

**Files Modified:**
- `backend/main.py` (security middleware imports, CSRF endpoint, account lockout in login)
- `tasks/todo.md` (Sprint 49 checklist)
- `CLAUDE.md` (project state updated, version 0.40.0)

**Test Results:** 422 total backend tests (33 new security tests)
**Frontend Build:** Success (Next.js 16.1.6)
**Zero-Storage Verified:** Account lockout tracking is in-memory only, no persistent state

---

## Phase IV Reprioritization (Accounting Expert Auditor Review)

> **Date:** 2026-02-05
> **Source:** Accounting Expert Auditor Assessment (Score: 7.8/10)
> **Rationale:** Professional adoption features must come before polish features

### Auditor Key Findings

**Critical Gaps for Professional Adoption:**
1. Lead Sheet Mapping - "Auditors think in lead sheets, not raw account lists"
2. Prior Period Comparison - "Every audit compares to prior year"
3. Adjusting Entry Module - "Cannot record proposed adjustments"

**Deferred (Lower Priority):**
- CSV Export → Sprint 54
- Print Styles → Removed (auditor: "Print is legacy")
- Frontend Tests → Sprint 55

---

## Sprint 50: Lead Sheet Mapping — ✅ COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** Group trial balance accounts by lead sheet designation
> **Complexity:** 5/10
> **Auditor Priority:** HIGH

### BackendCritic: Lead Sheet Schema
- [x] Define LeadSheet enum (A=Cash, B=Receivables, C=Inventory, etc.)
- [x] Create lead_sheet_mapping.py with standard COA-to-leadsheet rules
- [x] Add lead_sheet field to account classification output
- [x] Implement automatic lead sheet assignment based on account type
- [x] Support custom lead sheet overrides per client

### BackendCritic: Lead Sheet Grouping API
- [x] Extend audit response to include lead_sheet_summary
- [x] Group accounts by lead sheet in response
- [x] Calculate subtotals per lead sheet
- [x] Add GET /audit/lead-sheets/options endpoint for UI dropdowns

### FrontendExecutor: Lead Sheet View
- [x] Create LeadSheetSection component with collapsible sections
- [x] Display accounts grouped by lead sheet (A, B, C, etc.)
- [x] Show lead sheet subtotals with drill-down
- [x] Add category filter in results view
- [x] Oat & Obsidian theme compliance

### Sprint 50 Success Criteria
- [x] Accounts automatically assigned to lead sheets
- [x] Lead sheet grouping visible in UI
- [x] Subtotals calculated per lead sheet
- [x] Custom overrides supported
- [x] Zero-Storage compliance maintained

### Sprint 50 Review
**Files Created:**
- `backend/lead_sheet_mapping.py` - Lead sheet schema, mapping rules, grouping logic
- `backend/tests/test_lead_sheet.py` - 77 comprehensive tests
- `frontend/src/types/leadSheet.ts` - TypeScript types for lead sheets
- `frontend/src/components/leadSheet/LeadSheetCard.tsx` - Individual lead sheet card
- `frontend/src/components/leadSheet/LeadSheetSection.tsx` - Lead sheet dashboard section
- `frontend/src/components/leadSheet/index.ts` - Component exports

**Files Modified:**
- `backend/main.py` - Added lead sheet imports, API endpoint, audit integration
- `frontend/src/app/page.tsx` - Integrated LeadSheetSection component
- `frontend/src/types/index.ts` - Added leadSheet exports

**Test Results:** 77 lead sheet tests + 33 security tests = 110 tests passing
**Build Status:** Frontend builds successfully

---

## Sprint 51: Prior Period Comparison — ✅ COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic + FintechDesigner
> **Focus:** Side-by-side current vs prior year trial balance comparison
> **Complexity:** 4/10
> **Auditor Priority:** HIGH

### BackendCritic: Prior Period Storage
- [x] Extend DiagnosticSummary to support period snapshots
- [x] Add period_label field (e.g., "FY2025", "Q3 2025")
- [x] Create PriorPeriodComparison dataclass
- [x] Implement variance calculation ($ and %) between periods

### BackendCritic: Comparison API
- [x] Add POST /audit/compare endpoint (current file + prior period ID)
- [x] Return side-by-side comparison with variances
- [x] Calculate significant variance flags (>10% or >$10K)
- [x] Support balance sheet, income statement, and ratio comparison

### FintechDesigner: Comparison UI Design
- [x] Design side-by-side comparison table layout
- [x] Current | Prior | $ Variance | % Variance columns
- [x] Highlight significant variances (Clay Red for adverse)
- [x] Direction arrows with color coding

### FrontendExecutor: Comparison Implementation
- [x] Create PriorPeriodSelector component (dropdown of stored periods)
- [x] Create ComparisonTable component with variance highlighting
- [x] Create ComparisonSection with save modal
- [x] Add "Save as Prior Period" button with label/date/type inputs

### Sprint 51 Success Criteria
- [x] Prior period can be saved from audit results
- [x] Side-by-side comparison displays correctly
- [x] Variances calculated and highlighted
- [x] Significant variances flagged
- [x] Zero-Storage: Only aggregate totals stored, not raw data

### Sprint 51 Review
**Files Created:**
- `backend/prior_period_comparison.py` - Comparison engine with variance calculation
- `backend/tests/test_prior_period.py` - 41 comprehensive tests
- `frontend/src/types/priorPeriod.ts` - TypeScript types for comparison
- `frontend/src/hooks/usePriorPeriod.ts` - Hook for API integration
- `frontend/src/components/comparison/ComparisonTable.tsx` - Variance table
- `frontend/src/components/comparison/ComparisonSection.tsx` - Full comparison UI
- `frontend/src/components/comparison/index.ts` - Component exports

**Files Modified:**
- `backend/models.py` - Added period_label field to DiagnosticSummary
- `backend/main.py` - Added 3 comparison endpoints, imports, version 0.41.0
- `frontend/src/types/index.ts` - Added priorPeriod exports
- `frontend/src/hooks/index.ts` - Added usePriorPeriod export

**Test Results:** 41 prior period tests + 77 lead sheet tests = 118 tests passing
**Build Status:** Frontend builds successfully

---

## Sprint 52: Adjusting Entry Module — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** Record proposed adjustments and show adjusted trial balance
> **Complexity:** 6/10
> **Auditor Priority:** HIGH

### BackendCritic: Adjusting Entry Schema
- [x] Create AdjustingEntry dataclass with multi-line support (AdjustmentLine)
- [x] Create AdjustedTrialBalance dataclass with account-level detail
- [x] Implement adjustment application logic (apply_adjustments function)
- [x] Validate debits = credits for each entry (balanced validation)
- [x] AdjustmentSet for managing collections of entries
- [x] AdjustmentType enum (accrual, deferral, estimate, error_correction, reclassification, other)
- [x] AdjustmentStatus enum (proposed, approved, rejected, posted)

### BackendCritic: Adjustment API
- [x] Add POST /audit/adjustments endpoint (create entry)
- [x] Add GET /audit/adjustments endpoint (list entries with filters)
- [x] Add GET /audit/adjustments/{id} endpoint (get single entry)
- [x] Add PUT /audit/adjustments/{id}/status endpoint (update status)
- [x] Add DELETE /audit/adjustments/{id} endpoint (delete entry)
- [x] Add DELETE /audit/adjustments endpoint (clear all)
- [x] Add POST /audit/adjustments/apply endpoint (apply to trial balance)
- [x] Add GET /audit/adjustments/reference/next endpoint (auto-generate reference)
- [x] Add GET /audit/adjustments/types endpoint (type options)
- [x] Add GET /audit/adjustments/statuses endpoint (status options)

### FrontendExecutor: Adjustment UI
- [x] Create AdjustmentEntryForm component (multi-line debit/credit)
- [x] Create AdjustmentList component with expandable details
- [x] Create AdjustmentSection component (main collapsible section)
- [x] Add status badges with approve/reject/post actions
- [x] Add "Apply Adjustments" and "Clear All" buttons
- [x] useAdjustments hook for API integration
- [x] TypeScript types in types/adjustment.ts
- [x] Session-only storage (Zero-Storage compliant)

### FrontendExecutor: Adjustment Summary Export — DEFERRED
- [ ] Add adjustments to PDF export (Sprint 53+)
- [ ] Add adjustments to Excel workpaper export (Sprint 53+)
- [ ] Generate standalone Journal Entry Summary (Sprint 53+)

### Sprint 52 Success Criteria
- [x] Users can enter proposed adjusting entries
- [x] Multi-line journal entries with dynamic add/remove
- [x] Debits = Credits validation enforced (real-time)
- [x] Status workflow: proposed → approved → posted
- [x] Zero-Storage: Adjustments in session only, never persisted
- [ ] Adjustments included in exports (deferred to Sprint 53)

**Backend Files Created:**
- `backend/adjusting_entries.py` - Core schema and logic
- `backend/tests/test_adjusting_entries.py` - 45 tests

**Frontend Files Created:**
- `frontend/src/types/adjustment.ts` - TypeScript types
- `frontend/src/hooks/useAdjustments.ts` - API hook
- `frontend/src/components/adjustments/AdjustmentEntryForm.tsx` - Entry form
- `frontend/src/components/adjustments/AdjustmentList.tsx` - Entry list
- `frontend/src/components/adjustments/AdjustmentSection.tsx` - Main section
- `frontend/src/components/adjustments/index.ts` - Exports

**Test Results:** 45 adjusting entry tests, 584 total passing
**Build Status:** Frontend builds successfully

---

## Sprint 53: DSO Ratio + Workpaper Fields — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic + FintechDesigner
> **Focus:** Add missing DSO ratio and professional workpaper fields
> **Complexity:** 3/10
> **Auditor Priority:** MEDIUM

### BackendCritic: Days Sales Outstanding (DSO)
- [x] Add DSO calculation to ratio_engine.py
- [x] Formula: (Accounts Receivable / Revenue) × 365
- [x] Add health thresholds (≤30 excellent, ≤45 good, ≤60 adequate, ≤90 slow, >90 concern)
- [x] Include in benchmark sets for all 6 industries

### FintechDesigner: Workpaper Field Design
- [x] Design "Prepared by" and "Reviewed by" fields for exports
- [x] Design reference number system (TB-M001 material, TB-I001 immaterial)
- [x] Design workpaper date field

### FrontendExecutor: Implementation
- [x] Add DSO to KeyMetricsSection (9 ratios now)
- [x] Add ExportOptionsPanel with workpaper fields
- [x] Add reference numbers to PDF and Excel anomaly tabs
- [x] Update PDF generator with signoff section
- [x] Update Excel generator with signoff + Ref column

### Sprint 53 Success Criteria
- [x] DSO ratio calculated and displayed
- [x] Workpaper fields appear in exports
- [x] Anomalies have reference numbers (TB-M001/TB-I001)
- [x] Professional credibility enhanced

**Backend Files Modified:**
- `backend/ratio_engine.py` - DSO calculation with health thresholds
- `backend/benchmark_engine.py` - DSO benchmarks for 6 industries
- `backend/pdf_generator.py` - Workpaper signoff section
- `backend/excel_generator.py` - Signoff + reference numbers
- `backend/main.py` - Export endpoints accept workpaper fields

**Frontend Files Created/Modified:**
- `frontend/src/components/export/ExportOptionsPanel.tsx` - New export panel
- `frontend/src/components/analytics/KeyMetricsSection.tsx` - DSO display

**Test Results:** 591 passing tests (6 new DSO tests)
**Build Status:** Frontend builds successfully

---

## Sprint 54: Export Enhancement — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** CSV export for trial balance and anomalies
> **Complexity:** 3/10
> **Auditor Priority:** LOW (moved from Sprint 50)

### Tasks
- [x] Add CSV export for trial balance data
- [x] Add CSV export for anomaly list
- [x] Reference numbers in CSV exports
- [x] Risk summary in anomaly CSV
- [ ] Create customizable PDF template system (deferred)
- [ ] Allow logo/header customization (deferred)

**Backend Files Modified:**
- `backend/main.py` - Added /export/csv/trial-balance and /export/csv/anomalies endpoints

**Frontend Files Modified:**
- `frontend/src/components/export/ExportOptionsPanel.tsx` - Added CSV export buttons

**Test Results:** 591 passing tests
**Build Status:** Frontend builds successfully

---

## Sprint 55: Frontend Test Foundation — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** QualityGuardian + FrontendExecutor
> **Focus:** Jest/RTL setup and critical path coverage
> **Complexity:** 4/10
> **Auditor Priority:** LOW (internal quality)

### Tasks
- [x] Set up Jest + React Testing Library
- [x] Create test utilities and fixtures
- [x] Test critical components (MetricCard, KeyMetricsSection, ExportOptionsPanel)
- [x] Establish coverage baseline (26 tests)

**Files Created:**
- `frontend/jest.config.js` - Jest configuration for Next.js 16
- `frontend/jest.setup.js` - Test environment setup with DOM mocks
- `frontend/__mocks__/styleMock.js` - CSS module mock
- `frontend/__mocks__/fileMock.js` - Static file mock
- `frontend/src/test-utils/index.tsx` - Custom render with providers
- `frontend/src/test-utils/fixtures.ts` - Sample test data
- `frontend/src/__tests__/MetricCard.test.tsx` - 10 tests
- `frontend/src/__tests__/KeyMetricsSection.test.tsx` - 8 tests
- `frontend/src/__tests__/ExportOptionsPanel.test.tsx` - 8 tests

**Test Results:** 26 frontend tests passing
**Build Status:** Frontend builds successfully

---

## Sprint 56: Portfolio UX Fixes — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** FrontendExecutor
> **Focus:** Agent Council UX feedback implementation
> **Complexity:** 2/10
> **Auditor Priority:** HIGH (CEO-reported issues)

### Tasks
- [x] Fix delete confirmation to only close modal on success
- [x] Add Home link to Portfolio navigation
- [x] Create EditClientModal component for editing clients
- [x] Remove Account ID from Profile Settings (CEO request)
- [x] Unify navigation with ProfileDropdown on settings pages

**Files Modified:**
- `frontend/src/app/portfolio/page.tsx` - Fixed delete handling, added Home link, integrated EditClientModal
- `frontend/src/app/settings/profile/page.tsx` - Removed Account ID, unified nav
- `frontend/src/app/settings/practice/page.tsx` - Unified nav with ProfileDropdown

**Files Created:**
- `frontend/src/components/portfolio/EditClientModal.tsx` - Client editing modal

**Build Status:** Frontend builds successfully

---

## Phase IV Complete

All 9 sprints of Phase IV delivered:
- Sprint 48: User Profile Settings
- Sprint 49: Security Hardening
- Sprint 50: Lead Sheet Mapping
- Sprint 51: Prior Period Comparison
- Sprint 52: Adjusting Entry Module
- Sprint 53: DSO Ratio + Workpaper Fields
- Sprint 54: CSV Export Enhancement
- Sprint 55: Frontend Test Foundation
- Sprint 56: Portfolio UX Fixes

**Total Test Coverage:** 591 backend + 26 frontend = 617 tests

---

## Phase V: Verified-Account-Only Model

> Transform Paciolus from anonymous-use to verified-account-only while maintaining Zero-Storage architecture

### Sprint 57: Email Verification Backend — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** BackendCritic
> **Focus:** Email verification infrastructure
> **Complexity:** 4/10

#### Database Changes
- [x] Add UserTier enum (free, professional, enterprise)
- [x] Add email verification fields to User model
- [x] Create EmailVerificationToken model

#### New Modules
- [x] Create email_service.py with SendGrid integration
- [x] Create disposable_email.py for blocking temp email domains (200+ domains)

#### New Endpoints
- [x] POST /auth/verify-email - Verify with token
- [x] POST /auth/resend-verification - Resend with cooldown (5 min)
- [x] GET /auth/verification-status - Get current verification status

#### Auth Changes
- [x] Add require_verified_user dependency
- [x] Block disposable emails at registration
- [x] Send verification email on registration
- [x] Write comprehensive tests (36 new tests)

**Backend Files Created:**
- `backend/disposable_email.py` - 200+ disposable domain blocking
- `backend/email_service.py` - SendGrid integration with Oat & Obsidian email templates
- `backend/migrations/add_email_verification_fields.py` - Database migration
- `backend/tests/test_email_verification.py` - 36 comprehensive tests

**Backend Files Modified:**
- `backend/models.py` - UserTier enum, User fields, EmailVerificationToken model
- `backend/auth.py` - require_verified_user dependency, UserResponse tier field
- `backend/main.py` - 3 new endpoints, registration with verification
- `backend/requirements.txt` - sendgrid==6.11.0

**Test Results:** 625 backend tests passing (36 new email verification tests)
**Build Status:** Frontend builds successfully

---

### Sprint 58: Email Verification Frontend — COMPLETE
> **Date:** 2026-02-05
> **Agent Lead:** FrontendExecutor
> **Focus:** Verification UI, AuthContext updates, registration flow redirect
> **Complexity:** 3/10

#### New Files Created
- [x] `frontend/src/types/verification.ts` - VerificationStatus, VerifyEmailResponse, ResendResponse types
- [x] `frontend/src/hooks/useVerification.ts` - Reusable resend + countdown timer hook
- [x] `frontend/src/app/verify-email/page.tsx` - Token verification page with auto-redirect
- [x] `frontend/src/app/verification-pending/page.tsx` - Post-registration "check your email" page
- [x] `frontend/src/components/auth/VerificationBanner.tsx` - Dismissible banner for unverified users

#### Files Modified
- [x] `frontend/src/types/auth.ts` - Added tier to User, 3 verification methods to AuthContextType
- [x] `frontend/src/context/AuthContext.tsx` - Implemented verifyEmail, resendVerification, checkVerificationStatus
- [x] `frontend/src/app/register/page.tsx` - Redirect to /verification-pending after registration
- [x] `frontend/src/components/auth/index.ts` - Export VerificationBanner
- [x] `frontend/src/hooks/index.ts` - Export useVerification
- [x] `frontend/src/app/page.tsx` - Added VerificationBanner to authenticated view

**Build Status:** Frontend builds successfully (0 errors)
**Routes Added:** /verify-email, /verification-pending

---

### Sprint 59: Protect Audit Endpoints (COMPLETE)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Focus:** Gate tool access behind email verification

- [x] Backend: Add require_verified_user to 6 unprotected audit/export endpoints
- [x] Backend: Upgrade require_current_user → require_verified_user on 13 endpoints
- [x] Backend: Update test_benchmark_api.py dependency overrides
- [x] Backend: pytest passes (626 passed, 1 pre-existing perf flake)
- [x] Frontend: Fix apiClient.ts structured error handling for object `detail`
- [x] Frontend: Remove DEV MOCK in AuthContext.tsx
- [x] Frontend: Add auth headers to runAudit/handleFileUpload in page.tsx
- [x] Frontend: Replace guest diagnostic zone with sign-in CTA
- [x] Frontend: Add token prop to ExportOptionsPanel + DownloadReportButton
- [x] Frontend: npm run build passes

---

### Sprint 60: Homepage Demo Mode (COMPLETE)
> **Agent Lead:** FrontendExecutor + FintechDesigner
> **Focus:** Interactive demo with synthetic data for Acme Manufacturing Corp

- [x] Create `frontend/src/data/demoData.ts` with synthetic Acme Manufacturing Corp data
  - $5.2M balanced TB, 42 accounts, 3 anomalies, 9 ratios, 8 lead sheets
  - Manufacturing benchmark comparison (score 72/100)
  - All types validated against existing interfaces
- [x] Create `frontend/src/components/marketing/DemoZone.tsx` component
  - Renders RiskDashboard, KeyMetricsSection, BenchmarkSection, LeadSheetSection
  - All components in `disabled={true}` read-only mode
  - framer-motion staggered entrance with whileInView viewport trigger
  - Oat & Obsidian theme compliance throughout
- [x] Update `frontend/src/components/marketing/index.ts` with DemoZone export
- [x] Update `frontend/src/app/page.tsx` - replace Sprint 59 sign-in CTA with DemoZone
- [x] Sign In / Create Account CTAs at bottom of demo zone
- [x] Zero-Storage compliant (hardcoded constants only, no API calls)
- [x] `npm run build` passes with zero errors

