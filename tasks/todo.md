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

### Phase II (Sprints 25-39) — IN PROGRESS 🔄

| Sprint | Theme | Primary Agent | Status |
|--------|-------|---------------|--------|
| 25 | Foundation Hardening | QualityGuardian + BackendCritic | ✅ |
| 26 | Profitability Ratios | BackendCritic + FrontendExecutor | ✅ |
| 26 | Profitability Ratios | BackendCritic + FrontendExecutor | Low complexity |
| 27 | Return Metrics | BackendCritic + FrontendExecutor | Investor readiness |
| 28 | Ratio Dashboard Enhancement | FrontendExecutor + FintechDesigner | User visibility |
| 29 | IFRS/GAAP Documentation | ProjectAuditor + BackendCritic | Compliance |
| 30 | Classification Intelligence | BackendCritic + FrontendExecutor | UX friction |
| 31 | Materiality Sophistication | BackendCritic + QualityGuardian | Professional feature |
| 32 | Trend Analysis Foundation | BackendCritic + FintechDesigner | Multi-period infra |
| 33 | Trend Visualization | FintechDesigner + FrontendExecutor | Visual impact |
| 34 | Industry Ratio Foundation | BackendCritic + FintechDesigner | Differentiation |
| 35 | Industry Ratio Expansion | BackendCritic + FrontendExecutor | Industry coverage |
| 36 | Rolling Window Analysis | BackendCritic + FrontendExecutor | Advanced analytics |
| 37 | Batch Upload Foundation | FrontendExecutor + QualityGuardian | Infrastructure |
| 38 | Batch Upload UI | FintechDesigner + FrontendExecutor | User feature |
| 39 | Benchmark Framework Design | BackendCritic + ProjectAuditor | Phase III setup |

---

## Sprint 25: Ratio Intelligence Enhancement (PLANNED)
> **Source:** Accounting Expert Auditor Evaluation (2026-02-04)
> **Audit Score:** 8.2/10 — Core functionality production-ready
> **Priority:** Address high-priority gaps identified in professional audit

### HIGH PRIORITY — Immediate Implementation

#### BackendCritic: Expanded Ratio Coverage
- [ ] Add Net Profit Margin ratio to ratio_engine.py
  - Formula: (Revenue - Total Expenses) / Revenue × 100%
  - Include interpretation thresholds
- [ ] Add Operating Profit Margin ratio
  - Formula: (Revenue - COGS - Operating Expenses) / Revenue × 100%
  - Distinguish operating vs total expenses
- [ ] Add Return on Assets (ROA) ratio
  - Formula: Net Income / Total Assets × 100%
  - Standard profitability metric
- [ ] Add Return on Equity (ROE) ratio
  - Formula: Net Income / Total Equity × 100%
  - Key investor metric

#### BackendCritic: Multi-Sheet Column Detection Fix
- [ ] Modify `audit_trial_balance_multi_sheet()` in audit_engine.py
- [ ] Apply column detection independently to each sheet (not just first)
- [ ] Track per-sheet column mappings in audit response
- [ ] Add detection warning if column orders differ across sheets
- [ ] Update tests for multi-sheet column detection

#### QualityGuardian: Ratio Engine Test Suite
- [ ] Create `backend/tests/test_ratio_engine.py`
- [ ] Test all ratio formulas with standard inputs
- [ ] Test division-by-zero handling for each ratio
- [ ] Test interpretation threshold boundaries
- [ ] Test edge cases: zero revenue, negative equity, etc.
- [ ] Verify all ratios return N/A gracefully when uncalculable

### MEDIUM PRIORITY — Sprint 26 Candidates

#### BackendCritic: Multi-Period Trend Analysis
- [ ] Extend VarianceAnalyzer to support multiple historical snapshots
- [ ] Implement rolling window calculations (3, 6, 12 month)
- [ ] Calculate trend momentum (acceleration/deceleration)
- [ ] Add trend direction prediction indicators
- [ ] Store multiple DiagnosticSummary records per client

#### BackendCritic: Industry-Specific Ratio Dashboards
- [ ] Create industry_ratios.py with sector-specific calculations
- [ ] Manufacturing: Inventory Turnover, Days Inventory Outstanding, Asset Turnover
- [ ] Retail: Inventory-to-Sales ratio, Same-store growth placeholders
- [ ] Professional Services: Realization Rate placeholders
- [ ] Map Industry enum to relevant ratio sets
- [ ] Frontend: Display industry-relevant ratios based on client classification

#### FrontendExecutor: Enhanced Ratio Display
- [ ] Update KeyMetricsSection to show expanded ratios
- [ ] Add ratio tooltips with formula explanations
- [ ] Implement collapsible "Advanced Ratios" section
- [ ] Add trend indicators (↑↓→) based on variance data

### LOW PRIORITY — Future Enhancement

#### Documentation: IFRS Guidance Notes
- [ ] Add IFRS vs GAAP differences to ratio docstrings
- [ ] Note classification differences in classification_rules.py
- [ ] Document IFRS considerations in logs/dev-log.md

#### Enhancement: Materiality by Account Type
- [ ] Design weighted materiality schema
- [ ] Allow different thresholds for critical vs non-critical accounts
- [ ] Consider: Balance sheet items vs Income statement items

#### Enhancement: Account Classification Suggestions
- [ ] When confidence < 50%, suggest top 3 alternative classifications
- [ ] Implement fuzzy matching for "Did you mean?" UX
- [ ] Add user feedback loop for improving classifier

### Sprint 25 Success Criteria
- [ ] 8+ ratios available (up from 4)
- [ ] Multi-sheet audits handle different column orders
- [ ] 100% test coverage for ratio_engine.py
- [ ] Frontend build passes with no errors
- [ ] Backend tests pass (29+ tests)
- [ ] Zero-Storage compliance maintained

### Sprint 25 Review
**Status:** PLANNED
**Blockers:** None
**Notes:**
- Identified via professional accounting audit evaluation
- Gaps are enhancements, not blockers for production use
- Core 4 ratios remain the foundation; new ratios are additive

---

## Phase II Roadmap (Sprints 25-39)
> **Source:** Agent Council Priority Assessment (2026-02-04)
> **Model:** 15 focused sprints based on multi-agent consensus
> **Scoring:** MarketScout, QualityGuardian, BackendCritic, FrontendExecutor, FintechDesigner, ProjectAuditor

### Agent Consensus Summary
| Agent | Top Priority | Rationale |
|-------|-------------|-----------|
| MarketScout | Enhanced ratio display | User-visible value first |
| QualityGuardian | Ratio test suite | Zero test coverage is critical gap |
| BackendCritic | Test suite + Multi-sheet fix | Low complexity, high value |
| FrontendExecutor | Ratio display + Backend ratios | Clear implementation path |
| FintechDesigner | Trend visualizations | Highest visual impact |
| ProjectAuditor | Test suite + IFRS docs | Compliance gaps |

**Consensus Winner:** Ratio Engine Test Suite + Multi-Sheet Bug Fix (Sprint 25)

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

## Sprint 27: Return Metrics (PLANNED)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Key investor-facing metrics
> **Pattern:** Continue ratio expansion

### BackendCritic: Return on Assets (ROA)
- [ ] Add ROA to ratio_engine.py
- [ ] Formula: Net Income / Total Assets × 100%
- [ ] Calculate Net Income from category totals
- [ ] Add interpretation thresholds
- [ ] Add unit tests for ROA

### BackendCritic: Return on Equity (ROE)
- [ ] Add ROE to ratio_engine.py
- [ ] Formula: Net Income / Total Equity × 100%
- [ ] Add interpretation thresholds
- [ ] Add unit tests for ROE

### Sprint 27 Success Criteria
- [ ] 8 ratios available (target achieved)
- [ ] All ratio tests pass
- [ ] Frontend build passes

---

## Sprint 28: Ratio Dashboard Enhancement (PLANNED)
> **Agent Lead:** FrontendExecutor + FintechDesigner
> **Consensus:** MarketScout #1, FrontendExecutor #1
> **Focus:** User-visible improvements to existing UI

### FrontendExecutor: Enhanced KeyMetricsSection
- [ ] Update KeyMetricsSection to display 8 ratios
- [ ] Implement 2-column grid layout for ratios
- [ ] Add ratio tooltips with formula explanations
- [ ] Implement collapsible "Advanced Ratios" section

### FintechDesigner: Ratio Card Refinement
- [ ] Add trend indicators (↑↓→) based on variance data
- [ ] Design "healthy/warning/critical" visual states
- [ ] Apply Tier 2 semantic colors (Sage/Clay)
- [ ] Add subtle animations for value changes

### Sprint 28 Success Criteria
- [ ] All 8 ratios visible in dashboard
- [ ] Tooltips display formulas
- [ ] Trend indicators functional
- [ ] Oat & Obsidian compliance verified

---

## Sprint 29: IFRS/GAAP Documentation (PLANNED)
> **Agent Lead:** ProjectAuditor + BackendCritic
> **Consensus:** Low effort, compliance improvement
> **Focus:** Professional documentation

### ProjectAuditor: IFRS Guidance Notes
- [ ] Add IFRS vs GAAP differences to ratio docstrings
- [ ] Note classification differences in classification_rules.py comments
- [ ] Create STANDARDS.md with framework comparison
- [ ] Add tooltips to UI for standard-specific guidance

### BackendCritic: Classification Commentary
- [ ] Add docstrings explaining classification logic
- [ ] Note where IFRS/GAAP differ in account categorization
- [ ] Document deferred revenue, lease accounting considerations

### Sprint 29 Success Criteria
- [ ] STANDARDS.md created
- [ ] Ratio docstrings include standard references
- [ ] Classification rules documented
- [ ] Frontend tooltips added

---

## Sprint 30: Classification Intelligence (PLANNED)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Medium priority, reduces user friction
> **Focus:** Smarter auto-classification

### BackendCritic: Classification Suggestions
- [ ] When confidence < 50%, return top 3 alternative classifications
- [ ] Implement Levenshtein distance for fuzzy matching
- [ ] Add "Did you mean?" suggestions to API response
- [ ] Track suggestion acceptance rate (metadata only)

### FrontendExecutor: Suggestion UI
- [ ] Display classification suggestions in UI
- [ ] Allow one-click acceptance of suggestions
- [ ] Show confidence scores for alternatives
- [ ] Maintain Zero-Storage compliance (session only)

### Sprint 30 Success Criteria
- [ ] Suggestions appear for low-confidence classifications
- [ ] One-click acceptance functional
- [ ] Zero-Storage compliance verified

---

## Sprint 31: Materiality Sophistication (PLANNED)
> **Agent Lead:** BackendCritic + QualityGuardian
> **Consensus:** Medium complexity, professional feature
> **Focus:** Weighted materiality by account type

### BackendCritic: Weighted Materiality Schema
- [ ] Design weighted materiality configuration
- [ ] Define account type weights (e.g., Cash 1.5x, Prepaid 0.5x)
- [ ] Add balance_sheet_weight vs income_statement_weight
- [ ] Implement in practice_settings.py

### QualityGuardian: Materiality Edge Cases
- [ ] Test weighted materiality calculations
- [ ] Test weight priority resolution
- [ ] Test override behavior
- [ ] Verify Zero-Storage compliance

### Sprint 31 Success Criteria
- [ ] Weighted materiality configurable
- [ ] Tests pass for edge cases
- [ ] Settings UI updated
- [ ] Zero-Storage compliance verified

---

## Sprint 32: Trend Analysis Foundation (PLANNED)
> **Agent Lead:** BackendCritic + FintechDesigner
> **Consensus:** FintechDesigner #2, medium complexity
> **Focus:** Multi-period data infrastructure

### BackendCritic: Historical Snapshot Storage
- [ ] Extend DiagnosticSummary to store period identifier
- [ ] Add period_type enum (monthly, quarterly, annual)
- [ ] Implement get_historical_snapshots() method
- [ ] Add API endpoint for historical data retrieval

### BackendCritic: Variance Time Series
- [ ] Extend VarianceAnalyzer for multi-period comparison
- [ ] Calculate period-over-period changes
- [ ] Calculate trend direction (up/down/flat)
- [ ] Store trend metadata (not raw data)

### Sprint 32 Success Criteria
- [ ] Historical snapshots retrievable
- [ ] Period-over-period variance calculated
- [ ] API endpoint functional
- [ ] Zero-Storage compliance (metadata only)

---

## Sprint 33: Trend Visualization (PLANNED)
> **Agent Lead:** FintechDesigner + FrontendExecutor
> **Consensus:** High visual impact
> **Focus:** Sparkline charts and trend display

### FintechDesigner: Trend Chart Design
- [ ] Design sparkline components for ratio trends
- [ ] Define Oat & Obsidian chart palette
- [ ] Design "trend summary" card layout
- [ ] Specify animation behavior for chart drawing

### FrontendExecutor: Chart Implementation
- [ ] Integrate lightweight chart library (recharts/visx)
- [ ] Create TrendSparkline component
- [ ] Create TrendSummaryCard component
- [ ] Integrate into KeyMetricsSection

### Sprint 33 Success Criteria
- [ ] Sparklines display historical trends
- [ ] Oat & Obsidian theme applied
- [ ] Animations smooth and professional
- [ ] Mobile responsive

---

## Sprint 34: Industry Ratio Foundation (PLANNED)
> **Agent Lead:** BackendCritic + FintechDesigner
> **Consensus:** Medium priority, differentiation feature
> **Focus:** Industry-specific calculation groundwork

### BackendCritic: Industry Ratios Module
- [ ] Create backend/industry_ratios.py
- [ ] Define base IndustryRatioCalculator class
- [ ] Implement Manufacturing ratios:
  - [ ] Inventory Turnover (COGS / Average Inventory)
  - [ ] Days Inventory Outstanding
  - [ ] Asset Turnover (Revenue / Total Assets)
- [ ] Map Industry enum to ratio sets

### QualityGuardian: Industry Ratio Tests
- [ ] Test all manufacturing ratios
- [ ] Test industry-ratio mapping
- [ ] Test edge cases per industry

### Sprint 34 Success Criteria
- [ ] Manufacturing ratios implemented
- [ ] Tests pass for industry ratios
- [ ] Industry mapping functional

---

## Sprint 35: Industry Ratio Expansion (PLANNED)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Continue industry customization
> **Focus:** Additional industry implementations

### BackendCritic: Retail & Services Ratios
- [ ] Implement Retail ratios:
  - [ ] Inventory-to-Sales ratio
  - [ ] Gross Margin Return on Inventory
- [ ] Implement Professional Services ratios:
  - [ ] Revenue per Employee (placeholder)
  - [ ] Utilization Rate (placeholder)
- [ ] Add placeholder messaging for unavailable metrics

### FrontendExecutor: Industry Dashboard Section
- [ ] Create IndustryMetricsSection component
- [ ] Display industry-relevant ratios based on client classification
- [ ] Show "Not applicable" for irrelevant ratios
- [ ] Add industry context tooltip

### Sprint 35 Success Criteria
- [ ] Retail ratios implemented
- [ ] Services placeholders defined
- [ ] Industry section in dashboard
- [ ] Oat & Obsidian compliant

---

## Sprint 36: Rolling Window Analysis (PLANNED)
> **Agent Lead:** BackendCritic + FrontendExecutor
> **Consensus:** Advanced analytics feature
> **Focus:** 3/6/12 month rolling calculations

### BackendCritic: Rolling Window Calculations
- [ ] Implement 3-month rolling average
- [ ] Implement 6-month rolling average
- [ ] Implement 12-month rolling average
- [ ] Calculate trend momentum (acceleration/deceleration)

### FrontendExecutor: Rolling Window UI
- [ ] Add period selector (3/6/12 month)
- [ ] Display rolling averages in trend cards
- [ ] Show momentum indicators
- [ ] Integrate with existing trend visualization

### Sprint 36 Success Criteria
- [ ] Rolling windows calculated correctly
- [ ] Period selector functional
- [ ] Momentum indicators display
- [ ] Tests pass for rolling calculations

---

## Sprint 37: Batch Upload Foundation (PLANNED)
> **Agent Lead:** FrontendExecutor + QualityGuardian
> **Consensus:** High complexity, needs careful design
> **Focus:** Multi-file infrastructure (not UI)

### FrontendExecutor: Batch State Management
- [ ] Design multi-file state architecture
- [ ] Create BatchUploadContext for file queue
- [ ] Implement file validation queue
- [ ] Handle individual file errors gracefully

### QualityGuardian: Batch Error Handling
- [ ] Define error states for batch processing
- [ ] Implement partial success handling
- [ ] Test batch state cleanup
- [ ] Verify Zero-Storage compliance (all files in memory)

### Sprint 37 Success Criteria
- [ ] Batch state architecture documented
- [ ] File queue management functional
- [ ] Error handling tested
- [ ] Zero-Storage compliance verified

---

## Sprint 38: Batch Upload UI (PLANNED)
> **Agent Lead:** FintechDesigner + FrontendExecutor
> **Consensus:** Complete batch feature
> **Focus:** User-facing batch experience

### FintechDesigner: Batch Upload Design
- [ ] Design multi-file dropzone
- [ ] Design file queue list with status indicators
- [ ] Design batch progress visualization
- [ ] Define Oat & Obsidian batch styling

### FrontendExecutor: Batch Upload Implementation
- [ ] Implement multi-file dropzone
- [ ] Create FileQueueList component
- [ ] Implement batch progress bar
- [ ] Add "Run All" / "Run Selected" buttons

### Sprint 38 Success Criteria
- [ ] Multi-file upload functional
- [ ] File queue displays correctly
- [ ] Progress tracking works
- [ ] Oat & Obsidian compliant

---

## Sprint 39: Benchmark Framework Design (PLANNED)
> **Agent Lead:** BackendCritic + ProjectAuditor
> **Consensus:** Phase II finale, sets up Phase III
> **Focus:** Architecture design only (not implementation)

### BackendCritic: Benchmark Architecture RFC
- [ ] Design benchmark data schema
- [ ] Define industry benchmark sources (public data)
- [ ] Design comparison calculation approach
- [ ] Document Zero-Storage implications (benchmark data is reference, not client data)

### ProjectAuditor: Benchmark Documentation
- [ ] Create BENCHMARKS.md with framework design
- [ ] Document data sources and licensing
- [ ] Define Phase III implementation scope
- [ ] Add benchmark roadmap to Phase III planning

### Sprint 39 Success Criteria
- [ ] Benchmark RFC complete
- [ ] Data sources identified
- [ ] Architecture documented
- [ ] Phase III scope defined

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
