# Sprints 570–571 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-23.

---

### Sprint 570: DEC 2026-03-23 Remediation (5 Findings)
> Source: `reports/council-audit-2026-03-23.md`

#### P2 — Medium
- [x] **F-002:** Alembic migration `b1c2d3e4f5a6` to clean stale `ORGANIZATION` tier values in `users.tier` → `FREE`
- [x] **F-001:** Route-level tests for `audit_flux.py` (5 tests: auth gates, validation, success, error) and `audit_preview.py` (5 tests: auth gates, success, quality gate, error)

#### P3 — Low
- [x] **F-003:** Complete export schema migration — migrated 32 imports across 7 test files from `routes.export` → `shared.export_schemas`; removed re-export shim + TODO from `routes/export.py`
- [x] **F-004:** Replaced 9 `bg-white` instances with `bg-oatmeal-50` in 4 files (HeroFilmFrame, HeroProductFilm, MegaDropdown, VaultTransition)
- [x] **F-005:** Fixed archive script + commit-msg hook pattern — removed `^` anchor so `- **Status:** COMPLETE` is matched

- **Tests:** 7,096 backend (10 new), 1,725 frontend — 0 failures
- **Verification:** pytest PASS, npm run build PASS, npm test PASS (1,725/1,725), 0 `bg-white`, 0 `from routes.export import`, archive pattern verified
- **Status:** COMPLETE
- **Commit:** 2b1cba1

---

### Sprint 571: Launch Readiness Engineering (8 Items)
> Source: `reports/launch-readiness-2026-03-23.md`

#### Legal/Compliance
- [x] **B-11:** Updated ToS Section 8.1 pricing table — Solo/$100, Professional/$500, Enterprise/$1,000 (was Solo/$50, Team/$130, Organization/$400)
- [x] **B-11b:** Updated ToS Section 8.2 seat-based pricing — Team/Organization → Professional/Enterprise

#### SEO/Marketing
- [x] **B-12:** Added `robots.txt` (disallow authenticated routes) + `sitemap.ts` (11 public URLs)
- [x] **B-13:** Added Open Graph image + Twitter card metadata to root layout
- [x] **B-14:** Added per-page SEO metadata to 8 marketing pages (about, pricing, trust, contact, demo, approach, terms, privacy) via route-level `layout.tsx` server components

#### Backend Hardening
- [x] **H-04:** Upgraded CORS non-HTTPS origin from warning → hard fail in production (`config.py`)
- [x] **H-05:** Parameterized SQL in `database.py:191-194` — replaced f-string interpolation with bindparams for `information_schema` query
- [x] **H-02:** Added production guardrail requiring `SENDGRID_API_KEY` in production mode (`config.py`)

#### Frontend UX
- [x] **B-15:** Replaced disabled "Forgot password?" button ("Coming soon") with `mailto:support@paciolus.com` link; updated test

#### Already Implemented (verified, no action needed)
- [x] **H-01:** SQLite rejection in production — already enforced (`config.py:242-247`)
- [x] **H-03:** PostgreSQL TLS enforcement — already enforced (`config.py:249-263`)
- [x] **H-06:** Rate limit on `/auth/resend-verification` — already has `@limiter.limit("3/minute")`

- **Tests:** 7,096 backend, 1,725 frontend — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,725/1,725), backend smoke PASS, auth tests PASS (26/26)
- **Status:** COMPLETE
- **Commit:** 6e89285
