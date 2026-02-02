# CloseSignify Development Roadmap

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
- [ ] BackendCritic: Draft `/test-streaming` specification

---

## Remaining Days (8-18)

### Day 8: Automated Testing Infrastructure
- [ ] BackendCritic: Implement `test_streaming.py` per specification
- [ ] QualityGuardian: Add pytest test suite for audit_engine
- [ ] QualityGuardian: Add test coverage for security_utils
- [ ] FrontendExecutor: Add basic React component tests
- [ ] IntegratorLead: Create `/test` command for CI validation

### Day 9: PDF Report Generation
- [ ] MarketScout: Define "Close Health Report" requirements
- [ ] BackendCritic: Add ReportLab or WeasyPrint dependency
- [ ] BackendCritic: Create `/audit/report` endpoint returning PDF
- [ ] FrontendExecutor: Add "Download Report" button to results
- [ ] QualityGuardian: Ensure PDF generation is in-memory (Zero-Storage)

### Day 10: Enhanced Account Classification
- [ ] MarketScout: Research Chart of Accounts standards (GAAP/IFRS)
- [ ] BackendCritic: Expand keyword lists for account type detection
- [ ] BackendCritic: Add equity/revenue/expense account classification
- [ ] FrontendExecutor: Show account type breakdown in results
- [ ] QualityGuardian: Test with diverse trial balance formats

### Day 11: Multi-Sheet Excel Support
- [ ] BackendCritic: Handle Excel workbooks with multiple sheets
- [ ] FrontendExecutor: Add sheet selector dropdown in UI
- [ ] QualityGuardian: Test with complex Excel templates
- [ ] IntegratorLead: Document supported file formats

### Day 12: User Authentication (Phase 1)
- [ ] MarketScout: Define MVP auth requirements
- [ ] BackendCritic: Evaluate auth options (JWT vs session)
- [ ] BackendCritic: Implement `/auth/register` and `/auth/login`
- [ ] QualityGuardian: Ensure passwords are hashed (bcrypt)
- [ ] FrontendExecutor: Create login/register pages

### Day 13: User Authentication (Phase 2)
- [ ] BackendCritic: Implement protected routes middleware
- [ ] BackendCritic: Add user-specific waitlist tracking
- [ ] FrontendExecutor: Add auth state management
- [ ] QualityGuardian: Test auth flow security
- [ ] IntegratorLead: Update CORS for production domains

### Day 14: Audit History & Dashboard
- [ ] MarketScout: Define dashboard requirements
- [ ] BackendCritic: Create audit history storage (SQLite/PostgreSQL)
- [ ] BackendCritic: Add `/audits` endpoint for history
- [ ] FrontendExecutor: Create dashboard page with audit history
- [ ] QualityGuardian: Ensure audit data is encrypted at rest

### Day 15: Client Management
- [ ] MarketScout: Define client management workflow
- [ ] BackendCritic: Add client entity and CRUD endpoints
- [ ] FrontendExecutor: Create client list and detail pages
- [ ] QualityGuardian: Test multi-tenant data isolation

### Day 16: Batch Processing
- [ ] BackendCritic: Add `/audit/batch` endpoint for multiple files
- [ ] FrontendExecutor: Add multi-file upload UI
- [ ] FrontendExecutor: Show batch progress with per-file status
- [ ] QualityGuardian: Test memory usage with 10+ files

### Day 17: Production Deployment Prep
- [ ] QualityGuardian: Create Dockerfile for backend
- [ ] QualityGuardian: Create Dockerfile for frontend
- [ ] QualityGuardian: Create docker-compose.yml
- [ ] BackendCritic: Add production CORS configuration
- [ ] IntegratorLead: Document deployment process

### Day 18: Launch Readiness Review
- [ ] IntegratorLead: Final audit with `/audit` command
- [ ] QualityGuardian: Security review checklist
- [ ] MarketScout: Beta user feedback integration
- [ ] BackendCritic: Performance benchmarks documentation
- [ ] IntegratorLead: Update CLAUDE.md with production state

---

## Review Sections

### Day 7 Review
**Status:** In Progress
**Blockers:** None
**Notes:** Establishing workflow infrastructure per audit recommendations.

---

## Quick Reference

| Day | Theme | Primary Agent |
|-----|-------|---------------|
| 8 | Testing | QualityGuardian |
| 9 | PDF Reports | BackendCritic |
| 10 | Classification | BackendCritic |
| 11 | Excel Support | BackendCritic |
| 12-13 | Authentication | BackendCritic |
| 14 | Dashboard | FrontendExecutor |
| 15 | Clients | BackendCritic |
| 16 | Batch | BackendCritic |
| 17 | Deployment | QualityGuardian |
| 18 | Launch | IntegratorLead |
