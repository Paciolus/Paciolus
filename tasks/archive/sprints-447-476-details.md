# Sprints 447–476 + Phase LXVI–LXIX Details

> Archived from `tasks/todo.md` Active Phase — 2026-03-03

---

## Sprint 452 — Proposal C "Audit Maturity" Pricing Restructure

**Status:** COMPLETE
**Goal:** Progressive capability unlock model — Solo (individual analysis), Team (firm-wide testing), Organization (enterprise compliance).

### Backend
- [x] `entitlements.py`: Solo 9→7 tools (drop bank_rec, revenue), add `_TEAM_TOOLS` (11), add `_TEAM_FORMATS` (9)
- [x] `entitlements.py`: Solo excel_export/csv_export → False; Team diagnostics 0→100, clients 0→50; Org seats_included 0→15, max_team_seats 0→75
- [x] `price_config.py`: Team $130→$150, Org $400→$450; `ORG_SEAT_PRICE` $55/seat; `get_max_self_serve_seats()`, tier-aware `get_seat_price_cents()`/`calculate_additional_seats_cost()`; `get_stripe_org_seat_price_id()`
- [x] `routes/billing.py`: CheckoutRequest seat_count le=22→le=60; tier-aware seat validation + Org seat price ID; DPA for team+organization

### Frontend
- [x] `UpgradeGate.tsx`: Organization display name, Solo 7 tools, Team 11 tools explicit set
- [x] Revenue-testing + bank-rec pages: UpgradeGate wrappers added (now Team-gated)
- [x] `commandPalette.ts`: Organization in UserTier; `commandRegistry.ts`: TEAM_TOOLS set, 3-tier toolGuard
- [x] `checkout/page.tsx`: Organization support, maxAdditionalSeats(), flat org seat pricing, DPA for team+org
- [x] `pricing/page.tsx`: Updated tiers ($150/$450), comparison table, FAQ
- [x] `ToolShowcase.tsx`: 3-tier classification (4 solo / 4 team / 4 org), Organization filter tab
- [x] `UpgradeModal.tsx`: Organization tier, seat-aware helpers, correct Solo "20 uploads/mo"
- [x] `PlanCard.tsx`: Organization display name

### Tests
- [x] `test_entitlements.py`: 42 tests — Solo 7 tools, Team 11, format gating, export flags, Org 15 seats
- [x] `test_price_config.py`: 32 tests — new prices, max seats helper
- [x] `test_pricing_launch_validation.py`: 175 tests — all updated expectations

### Verification
- [x] `npm run build` — passes (all routes dynamic)
- [x] `pytest test_entitlements.py test_price_config.py` — 74/74 passed
- [x] `pytest test_pricing_launch_validation.py` — 175/175 passed
- [x] `npm test`: 111 suites, 1,341 tests passing
- Commit: 04e17c2

---

## Phase LXVII — Visual Polish

**Status:** COMPLETE
**Goal:** Complete partial implementations, fix accessibility gaps, and add approved visual enhancements across marketing + tool pages.

### Pre-Sprint — Bugfixes
- [x] Fix shimmer `@keyframes` missing from `prefers-reduced-motion: reduce` block
- [x] Global `:focus:not(:focus-visible)` rule to suppress focus rings on mouse click

### Sprint 1 — Completion Tasks
- [x] B4: `ToolPageSkeleton` shared component + 12 tool `loading.tsx` files
- [x] D4: Tabular-nums audit — 13 files migrated to `type-num-*` classes
- [x] C3: Card hover elevation on pricing cards, ToolShowcase, ToolStatusGrid
- [x] E1: Icon micro-animation on ToolShowcase + ToolStatusGrid

### Sprint 2 — Polish Enhancements
- [x] B2: Unified shimmer overlay; `.shimmer-overlay` reusable CSS class
- [x] A1: `MagneticButton` wrapper on hero CTA
- [x] D2: Already exists in footer + marketing nav

### Sprint 3 — Depth & Atmosphere
- [x] C1: `ParallaxSection` component. Applied to FeaturePillars + EvidenceBand.
- [x] Extended `.lobby-divider-wide` and `.lobby-divider-sage` variants

### Sprint 4 — Tool Page Enrichment
- [x] `CountUp` deployed to TestingScoreCard and DataQualityBadge
- [x] Wider sparkline — deferred (requires backend trend time-series data)

### Regression
- [x] `npm run build` passes; `DESIGN_GUIDELINES.md` updated to v1.1.0

---

## Sprint 451 — Backend Organization Tier Wiring
**Status:** COMPLETE
- [x] `UserTier.ORGANIZATION` enum + display names + price table + entitlements + rate limits
- [x] Alembic migration `d2e3f4a5b6c7`
- [x] Tests: 6 files, 329 tests passing
- Commit: ee6163b

---

## Enterprise/Organization Consolidation
**Status:** COMPLETE — Retire "Enterprise" display name; consistent 3-card layout (Solo/Team/Organization).
- Commits: 561c73c, ff5f817, 67c066a

---

## Sprint 450b — Hero Animation: Diagnostic Intelligence Showcase
**Status:** COMPLETE
- [x] Upload/Analyze/Export layers redesigned with real product capabilities
- [x] StaticFallback updated
- Commit: a5e4bfc

---

## Sprints 453-459 — Marketing Pages Overhaul
**Status:** COMPLETE — ~25 visual/content/UX fixes across Homepage, Pricing, Trust, Privacy, Footer.

- Sprint 453: Section header uniformity (sage dash pattern on all 5 homepage sections)
- Sprint 454: Hero section overhaul (pricing callout, CTA reorder, animation updates)
- Sprint 455: Tool slideshow cards + pricing bar + tool count fixes
- Sprint 456: EvidenceBand + ProcessTimeline + mobile fixes
- Sprint 457: Pricing page fixes (seat calculator, comparison table)
- Sprint 458: Trust page architecture redesign (3-stage pipeline)
- Sprint 459: Cross-page fixes (privacy ToC, footer dead link)
- [x] `npm run build` passes (40 routes, 0 errors)

---

## Phase LXVI — SOC 2 Type II Readiness

### Sprint 449 — GitHub PR Security Checklist Template
**Status:** COMPLETE — `.github/pull_request_template.md` with 8-item checklist + `CONTRIBUTING.md`. Commit: e09941a

### Sprint 450 — Encryption at Rest Verification + Documentation
**Status:** COMPLETE (pending CEO dashboard sign-off) — Template + policy updates. Commit: 6d37139

### Sprint 451 — Formal Risk Register
**Status:** COMPLETE (calendar reminder is CEO action) — 12-risk register, 0 Critical/High. Commit: 086883d

### Sprint 452 — First Backup Restore Test + Evidence Report
**Status:** COMPLETE (3 CEO actions) — DR test template with 10-step procedure.

### Sprint 453 — Security Training Log Framework + Content
**Status:** COMPLETE (2 CEO actions) — 5-module curriculum + training log.

### Sprint 454 — Q1 2026 Quarterly Access Review
**Status:** COMPLETE (2 CEO actions) — Template + Q1 instance for all 7 systems.

### Sprint 455 — Weekly Security Event Review Process
**Status:** COMPLETE (1 CEO action — W09 execution) — Template + digest script + first review pre-structured.

### Sprint 456 — Data Deletion SLA + Procedure Document
**Status:** COMPLETE (1 CEO action — end-to-end test) — 10-step procedure, Privacy Policy v2.1.

### Sprint 457 — Backup Integrity Checksum Automation
**Status:** COMPLETE (1 CEO action — first run) — Script + CI workflow + BCP/DR v1.2.

### Sprint 458 — GPG Commit Signing Enforcement
**Status:** COMPLETE (4 CEO actions — key setup + branch protection) — Docs + procedure.

### Sprint 459 — DPA Acceptance Workflow
**Status:** COMPLETE (1 CEO action — existing customer outreach) — In-product checkbox + Alembic migration.

### Sprint 460 — PostgreSQL pgaudit Extension
**Status:** COMPLETE — Not available on Render; compensating controls documented.

### Sprint 461 — Cryptographic Audit Log Chaining
**Status:** COMPLETE — HMAC-SHA512 chain + verification endpoint + 20 tests.

### Sprint 462 — Monitoring Dashboard Configuration Documentation
**Status:** COMPLETE — 5-section config doc.

### Sprint 465 — Automated Backup Restore Testing in CI
**Status:** COMPLETE — Monthly CI workflow + artifact upload.

### Sprint 469 — SOC 2 Evidence Folder Organization + Auditor Readiness Assessment
**Status:** COMPLETE — 42 criteria assessed (10 Ready / 28 Partial / 4 Gap). Observation window: 2026-04-01 to 2026-09-30.

---

## Phase LXVIII — Python & Full-Stack Code Review Fixes

### Sprint 470 — Security Fixes: XML + npm Dependencies
**Status:** COMPLETE — defusedxml verified + test imports cleaned, Sentry upgraded, serialize-javascript override.

### Sprint 471 — mypy Type Safety: Runtime-Risk Patterns
**Status:** COMPLETE — 9 mypy runtime-risk patterns fixed. No logic changes.

### Sprint 472 — mypy Type Annotations: Route Layer
**Status:** COMPLETE — Top-3 route files annotated; remaining deferred.

### Sprint 473 — mypy Type Annotations: Core Engines
**Status:** COMPLETE — multi_period, pdf_generator, follow_up_items_manager, config, auth, security_middleware annotated.

### Sprint 474 — mypy Type Annotations: Shared Modules + Config
**Status:** COMPLETE — All shared modules + Bandit nosec comments.

### Sprint 475 — mypy Type Annotations: Generators + Test Files
**Status:** COMPLETE — All non-test files annotated. Test file annotations deferred (68 errors, zero runtime risk).

---

## Phase LXIX — Pricing Restructure v3

**Status:** COMPLETE
**Goal:** Replace 5-tier with 4-tier (Free/Solo/Professional/Enterprise). All paid tiers get all 12 tools. New features: Organization entity model, export sharing, admin dashboard, PDF branding, bulk upload.

### Phases 1-9
- [x] Phase 1: DB schema + enum migration (UserTier, Organization models, Alembic)
- [x] Phase 2: Backend entitlements + price config ($100/$500/$1000)
- [x] Phase 3: Frontend types + UpgradeGate + FeatureGate
- [x] Phase 4: Pricing page (4-card) + checkout UI
- [x] Phase 5: Organization CRUD + invite flow + seat integration
- [x] Phase 6: Export sharing (Pro+Enterprise)
- [x] Phase 7: Team activity logs + admin dashboard routes
- [x] Phase 8: Custom PDF branding (Enterprise, S3 storage)
- [x] Phase 9: Bulk upload (Enterprise, up to 5 files)
- [x] 27 backend + 13 frontend test files updated
- [ ] Frontend pages for admin dashboard, branding settings, share UI (deferred)

---

## Motion System — Choreographed Entrance Animation
**Status:** COMPLETE
- `lib/motion.ts` + `components/ui/Reveal.tsx` foundation
- 5 phases: Marketing (~13 files), Workspace/Dashboard/Modals (~20 files), Auth/Settings/Tools (~10 files), Token cleanup (~8 files)
- Commit: eaea42e

---

## VaultTransition Rewrite — "Light Bleeding Through the Seam"
**Status:** COMPLETE — Pure CSS, no framer-motion. Commits: fba2f59, 9deb386

---

## HeroProductFilm Rewrite
**Status:** COMPLETE — New visual storytelling (Drop/Findings/Workpapers). Commit: 7d6941c

---

## About Page — Profession-First Copy Revision
**Status:** COMPLETE — Pacioli Connection + profession-first tone. Commit: 578fed4

---

## Security Hardening Sprint — 7 Fixes
**Status:** COMPLETE — 1 HIGH, 2 MEDIUM, 1 LOW, 3 MAINT fixes.

---

## Sprint 476 — Comprehensive Security Audit
**Status:** COMPLETE — 1 CRITICAL, 4 HIGH, 7 MEDIUM, 8 CVE dep patches. 14/20 auto-fixed.

---

## Documentation Sprint — Consolidated Design Guidelines
**Status:** COMPLETE — `docs/08-internal/DESIGN_GUIDELINES.md` v1.0.0, 600+ lines, 13 sections.
