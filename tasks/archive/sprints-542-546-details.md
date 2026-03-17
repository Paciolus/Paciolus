# Sprints 542–546 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-17.

---

### Sprint 543 — Dependency Bumps + Mypy Annotations

**Status:** COMPLETE
**Goal:** bcrypt 5.0 bump, test file mypy annotations, marketing SSG dropped.

- [x] 543a: Bump bcrypt>=5.0.0, add transitive-only comment for numpy/chardet
- [x] 543b: Update mypy.ini python_version 3.11→3.12 (804 errors found — full cleanup deferred)
- [x] 543c: Deferred items cleaned: Marketing SSG dropped, resolved items removed

#### Review
- bcrypt 5.0 uses stable `hashpw/checkpw/gensalt` API — zero code changes needed
- mypy test errors expanded from expected 68 to 804 across 135 files; config updated, full cleanup deferred
- Deferred items table cleaned: 5 items removed (3 being implemented, 1 resolved, 1 dropped)


---

### Sprint 544 — Backend Refactors

**Status:** COMPLETE
**Goal:** PaginatedResponse[T] generic, dedicated schemas/ directory, Alembic in Dockerfile.

- [x] 544a: Create `shared/pagination.py`, migrate 4 routes (clients, activity, engagements, follow_up_items) + 4 frontend hooks + 3 frontend types
- [x] 544b: Create `backend/schemas/` with 5 schema files extracted from routes; backward-compat re-exports preserved
- [x] 544c: Wire Alembic into Dockerfile CMD (`alembic upgrade head &&` before gunicorn)

#### Review
- **Breaking change:** List endpoint responses use `items` key instead of `clients`/`engagements`/`activities`. Frontend hooks + types + tests all updated simultaneously.
- 5 schema files: client_schemas, billing_schemas, adjustment_schemas, settings_schemas, follow_up_schemas
- All backward-compat re-exports verified: `from routes.billing import CheckoutRequest` still works
- 1 API contract test updated (`engagements` → `items`)
- Dockerfile now runs `alembic upgrade head` exactly once before workers spawn


---

### Sprint 545 — Phase LXIX Frontend Pages

**Status:** COMPLETE
**Goal:** Admin Dashboard, PDF Branding, Export Sharing pages + settings hub update.

- [x] 545a: Admin Dashboard — types/hook/page with 4 metric cards, 2 tables, CSV export, filters
- [x] 545b: Branding Settings — types/hook/page with header/footer form, logo upload/delete
- [x] 545c: Export Sharing — types/hook/modal/page with share list, revoke, expiry countdown
- [x] 545d: Settings Hub — 3 new FeatureGate-wrapped cards (Team Dashboard, PDF Branding, Export Sharing)

#### Review
- 3 new types files, 3 new hooks, 1 new modal component, 3 new pages
- 18 new hook tests (6 per hook), all passing
- All pages use Oat & Obsidian tokens, font-serif headers, Reveal wrapper
- FeatureGate with `hidden` prop hides cards for lower-tier users on settings hub
- Grid expanded to 3-col on large screens to accommodate 6 cards
- **Tests:** 1,357 frontend (was 1,339 — +18 new hook tests)
- Commit: f5e76b7


---

### Sprint 542 — Nightly Report Bug Fixes + Dependency Updates

**Status:** COMPLETE
**Goal:** Fix 5 confirmed-open bugs from the 2026-03-17 nightly report and update outdated packages (5 security-relevant + all minor/patch).

#### Bug Fixes
- [x] BUG-001: Suggested procedures rotation — add alternate procedures and `rotation_index` param to `get_follow_up_procedure()` (20 alternates across JE/AP/Revenue/Payroll; all 7 callers updated)
- [x] BUG-002: Hardcoded risk tier labels — `_compute_engagement_risk()` returns tier keys, display via `RISK_TIER_DISPLAY` lookup
- [x] BUG-003: PDF cell overflow — wrap plain strings in `Paragraph()` across 4 generators (bank rec, currency, accrual, anomaly summary)
- [x] BUG-006: Identical data quality scores — redistribute optional weight pool proportionally instead of flat bonus
- [x] BUG-007: Empty drill-down stubs — add `flagged_entries` guard to JE/AP high-severity section filters

#### Confirmed Already Fixed (No Action Needed)
- [x] BUG-004: Orphaned ASC 250-10 — fixed in Sprint 506 with test coverage
- [x] BUG-005: PP&E ampersand escaping — fixed in Sprint 502 with test coverage

#### Dependency Updates — Security-Relevant
- [x] fastapi: 0.133.1 → 0.135.1 (minor)
- [x] PyJWT: 2.11.0 → 2.12.1 (minor)
- [x] SQLAlchemy: 2.0.47 → 2.0.48 (patch)
- [x] stripe: 14.4.0 → 14.4.1 (patch, now pinned in requirements.txt)
- [x] next: 16.1.6 → 16.1.7 (patch)

#### Dependency Updates — Minor/Patch
- [x] Backend: uvicorn 0.41→0.42, sentry-sdk 2.53→2.54
- [x] Frontend: @sentry/nextjs 10.40→10.43, framer-motion 12.34→12.37, recharts 3.7→3.8, jest 30.2→30.3, lint-staged 16.2→16.4, @types/node 25.3→25.5, @typescript-eslint/* 8.56→8.57, @eslint/eslintrc 3.3.3→3.3.5

#### Verification
- [x] `pytest` passes (867 memo tests, 65 anomaly+dq tests)
- [x] `npm run build` passes
- [x] `npm test` passes (1,339 tests)
- [x] BUG-001 rotation verified: different indices produce different procedures
- [x] BUG-006 score differentiation verified: 100.0 vs 82.4 for different fill rates

#### Review
- 14 backend files modified across 5 bug fixes + 2 dependency files
- BUG-001 adds `FOLLOW_UP_PROCEDURES_ALT` dict with 20 alternates; backward-compatible API
- BUG-002 normalizes to lowercase tier keys consumed by existing `RISK_TIER_DISPLAY` infrastructure
- BUG-006 eliminates flat bonus that compressed score variance across datasets
- Major version packages (bcrypt 5.0, numpy 2.x, chardet 7.x) deferred — breaking API changes


---

### Sprint 546 — Comprehensive Audit Remediation (Phase 1: Bug Fixes + Phase 2: Architecture)

**Status:** COMPLETE
**Commit:** eadd9bb
**Goal:** Fix 8 critical/high bugs from formal audit + 9 architectural decompositions.

#### Phase 1 — Critical & High Bug Fixes (8 bugs)
- [x] Bug 1: Webhook dedup — narrow catch from Exception → IntegrityError; operational errors return 500
- [x] Bug 2: Webhook atomicity — replace all internal db.commit() with db.flush(); single outer commit
- [x] Bug 3: Admin overview — fix ActivityLog.created_at → .timestamp; tool_usage uses TeamActivityLog
- [x] Bug 4: Client cartesian join — rewrite get_clients_with_count to two-query approach
- [x] Bug 5: Seat removal — remove max(1,...) clamp; delete Stripe item when quantity reaches 0
- [x] Bug 6: Invite acceptance — add exclude_invite_id param to check_seat_limit_for_org
- [x] Bug 7: Webhook metadata — add try/except ValueError,TypeError around int() cast
- [x] Bug 8: Tool run numbering — add unique constraint + retry loop on IntegrityError
- [x] 23 new tests in test_phase1_bug_fixes.py

#### Phase 2 — Architectural Decomposition (9 refactors)
- [x] Refactor 1: audit_engine.py → backend/audit/ pipeline (6 modules)
- [x] Refactor 2: pdf_generator.py → backend/pdf/ package (styles, chrome, components, sections)
- [x] Refactor 3: export_diagnostics.py → backend/export/ pipeline (validators, serializers, transport)
- [x] Refactor 4: billing.py → billing_checkout/analytics/webhooks + billing/guards.py
- [x] Refactor 5: organization.py → services/organization_service.py + thin routes
- [x] Refactor 6: AuthContext.tsx → AuthSession/UserProfile/Verification contexts + hooks
- [x] Refactor 7: Unified frontend transport — eliminated direct fetch()
- [x] Refactor 8: HeroProductFilm.tsx → hero/ directory (animation, telemetry, frames)
- [x] Refactor 9: Pricing page → domain/pricing.ts + PricingCard/Estimator/Comparison components


---

