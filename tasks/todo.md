# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-04-14] pending: hallucination audit hotfix — /auth/refresh handler 401→403 for X-Requested-With mismatch (aligns with CSRF middleware); added .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
- [2026-04-07] 73aaa51: dependency patch — uvicorn 0.44.0, python-multipart 0.0.24 (nightly report remediation)
- [2026-04-06] 39791ec: secret domain separation — AUDIT_CHAIN_SECRET_KEY independent from JWT, backward-compat verification fallback, TLS evidence signing updated
- [2026-04-04] 29f768e: dependency upgrades — 14 packages updated, 3 security-relevant (fastapi 0.135.3, SQLAlchemy 2.0.49, stripe 15.0.1), tzdata 2026.1, uvicorn 0.43.0, pillow 12.2.0, next watchlist patch
- [2026-03-26] e04e63e: full sweep remediation — sessionStorage financial data removal, CSRF on /auth/refresh, billing interval base-plan fix, Decimal float-cast elimination (13 files, 16 tests added)
- [2026-03-21] 8b3f76d: resolve 25 test failures (4 root causes: StyleSheet1 iteration, Decimal returns, IIF int IDs, ActivityLog defaults), 5 report bugs (procedure rotation, risk tier labels, PDF overflow, population profile, empty drill-downs), dependency updates (Next.js 16.2.1, Sentry, Tailwind, psycopg2, ruff)
- [2026-03-21] 8372073: resolve all 1,013 mypy type errors — Mapped annotations, Decimal/float casts, return types, stale ignores (#49)
- [2026-03-20] AUDIT-07-F5: rate-limit 5 unprotected endpoints — webhook (10/min), health (60/min), metrics (30/min); remove webhook exemption from coverage test
- [2026-03-19] CI fix: 8 test failures — CircularDependencyError (use_alter), scheduler_locks mock, async event loop, rate limit decorators, seat enforcement assertion, perf budget, PG boolean literals
- [2026-03-18] 7fa8a21: AUDIT-07-F1 bind Docker ports to loopback only (docker-compose.yml)
- [2026-03-18] 52ddfe0: AUDIT-07-F2 replace curl healthcheck with python-native probe (backend/Dockerfile)
- [2026-03-18] 5fc0453: AUDIT-07-F3 create /app/data with correct ownership before USER switch (backend/Dockerfile)
- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.
> Sprints 570–571 archived to `tasks/archive/sprints-570-571-details.md`.
> Sprints 572–578 archived to `tasks/archive/sprints-572-578-details.md`.
> Sprints 579–585 archived to `tasks/archive/sprints-579-585-details.md`.
> Sprints 586–591 archived to `tasks/archive/sprints-586-591-details.md`.
> Sprints 592–595 archived to `tasks/archive/sprints-592-595-details.md`.

### Sprint 599: Coverage Sentinel + Subagent-Verification Lesson
**Status:** COMPLETE
**Goal:** Replace the weekly weakness hunt's hallucinated "coverage gap" analysis with a deterministic `pytest --cov` run wired into the nightly brief, and capture the subagent-verification discipline as a reusable lesson. Both are Audit 34 top-priorities.

**Problem:** Sprint 598's weekly hunt dispatched two parallel `Explore` subagents. The security-hunt agent produced verifiable findings at the file:line level; the coverage-hunt agent hallucinated — falsely claiming `ratio_engine.py`, `accrual_completeness_engine.py`, and `three_way_match_engine.py` had no test files (each has 1–3 dedicated ones), and reporting "44,081" / "55,283 lines" which were actually byte counts. The operator caught all three false claims and stripped them before acting, but the underlying workflow is wrong: coverage should stand on `pytest --cov --cov-report=json` data, not LLM introspection.

**Changes:**
- [x] `scripts/overnight/agents/coverage_sentinel.py` (new) — runs `pytest --cov=. --cov-report=json` in `backend/`, parses `totals.percent_covered`, maintains a rolling 7-day history in `reports/nightly/.baseline.json` under the `coverage_sentinel` key, computes delta vs 7-day mean, ranks top 10 uncovered files by missing-line count, writes `.coverage_sentinel_<DATE>.json`. Status rules: ≥90% green, 85–90% yellow, <85% red; additional drift gates (>0.5pp under mean → yellow, >2pp → red).
- [x] `scripts/overnight/orchestrator.py` — added `coverage_sentinel` to `AGENT_SCHEDULE` at 3:00 (between Scout at 2:45 and Sprint Shepherd at 3:30); added `AGENT_TIMEOUT_OVERRIDES` mechanism with `coverage_sentinel: 1700s` (pytest --cov is ~1.3–1.5× slower than the bare run); made the "Run complete: N/M" summary count derive from `len(AGENT_SCHEDULE) + 1` instead of the hardcoded `/6`.
- [x] `scripts/overnight/briefing_compiler.py` — added `coverage_sentinel` to the `AGENTS` list, added `_format_coverage_section()` rendering percentage + 7-day mean + delta arrow + top uncovered files table, inserted the section between Report Auditor and Scout in the daily brief template, changed the "Agents run: N/5" hardcoded denominator to `len(AGENTS)`.
- [x] `tasks/lessons.md` — appended new lesson "Subagent findings must be verified against live code before acting (Sprint 598)" documenting the ratio_engine/accrual/three_way_match hallucinations, the fake line counts, and the `file:line` vs structural-claim trust heuristic.

**Review:**
- Standalone dry-run against the live backend test suite: **92.09% line coverage** (79,816 / 86,671 statements, 6,855 uncovered) — status GREEN, no drift (baseline is building from today).
- `briefing_compiler.py` regenerated `reports/nightly/2026-04-14.md` with `agents_run: 6/6`, new Coverage Sentinel section renders cleanly with the top-uncovered-files table.
- Top uncovered files surfaced by the real data: `guards/doc_consistency_guard.py` (0%), `leadsheet_generator.py` (11.4%), `workbook_inspector.py` (18.6%), `pdf/sections/diagnostic.py` (65.7%). These are the actual coverage gaps — notably NONE of them match the hallucinated agent's claims (ratio/accrual/three_way_match). The hallucinations were total noise.
- `.baseline.json` now carries `coverage_sentinel.history` — on 2026-04-21 this will reach 7 entries and delta tracking will start driving status on its own.
- No changes to the backend test suite itself. No changes to production code. Pure observability infra.

---

### Sprint 598: Middleware Fail-Secure Hardening + Dep Hygiene
**Status:** COMPLETE
**Goal:** Close two latent middleware fail-open handlers uncovered by the weekly nightly review, tighten dev-dep floors

**Problem:** Weekly weakness hunt (2026-04-14) flagged two `except Exception: pass` sites in `security_middleware.py`:
- `RateLimitIdentityMiddleware` (line 263) — any non-JWT exception (e.g., config import failure, non-int `sub` claim, unicode decode error) silently downgrades the request to the anonymous rate-limit tier with no log and no metric. Rate-limit tier bypass was invisible.
- `ImpersonationMiddleware` (line 876) — any non-JWT exception on the pre-dispatch impersonation check was swallowed, bypassing the read-only gate. Downstream `require_current_user` still gates auth, but the defence-in-depth layer is lost when unexpected errors occur.

Both are narrow defence-in-depth issues, not exploitable in the tested happy-path (hence 0/0 test failures), but the fail-open semantics violated the stated intent of both middlewares.

**Changes:**
- [x] `security_middleware.py` — narrow `RateLimitIdentityMiddleware` except to `jwt.PyJWTError`, log non-JWT payload-shape failures (`TypeError`/`ValueError`) at `warning`, preserve anonymous fallthrough for genuine decode errors
- [x] `security_middleware.py` — narrow `ImpersonationMiddleware` except to `jwt.PyJWTError`, restructure so decode failure returns early to downstream auth dependency; unexpected exception types now surface instead of being swallowed
- [x] `backend/tests/test_rate_limit_tiered.py` — added 2 new tests: non-int `sub` triggers a warning log, malformed JWT stays silent (expected-failure path)
- [x] `backend/tests/test_impersonation_middleware.py` (new, 9 tests) — GET pass-through, POST without auth pass-through, valid non-imp token pass-through, `imp: true` blocked on POST/PUT/DELETE, expired imp still blocks, malformed JWT pass-through to downstream, non-Bearer auth pass-through
- [x] `backend/requirements.txt` — `python-multipart` 0.0.24 → 0.0.26 (patch), `sentry-sdk[fastapi]` 2.57.0 → 2.58.0 (minor), `prometheus_client` floor 0.22.0 → 0.25.0, `pypdf` floor 6.9.2 → 6.10.0
- [x] `backend/requirements-dev.txt` — `ruff` floor 0.15.8 → 0.15.10, `mypy` floor 1.19.0 → 1.20.1

**Review:**
- Backend: **7,403 passed, 19 xfailed** (+11 new: 9 impersonation + 2 rate-limit) in 649s — zero regressions
- Frontend: **1,757 passed** in 41s — zero regressions, `npm run build` clean, all 24 pages compile with dynamic CSP
- Scope deliberately narrow: bare `except Exception: pass` was the root cause, fix is to narrow the catch to the expected exception class. Unexpected exception types now bubble up as 500s, which is fail-closed.
- Refresh-token race condition in `auth.py:731-764` (also flagged by the weekly hunt) was left intact — the fail-secure behavior is deliberate and documented. Revisit only if multi-tab UX complaints appear.
- Deferred to future sprint: billing/checkout orchestrator bare-except review (needs deeper saga-compensation analysis), accrual_completeness float-site audit (needs domain-model review), CSRF-exempt `/auth/forgot-password` re-evaluation for authenticated-session case (low risk).

---

### Sprint 597: DOCX File Format Support
**Status:** COMPLETE
**Goal:** Add Word document (.docx) as an 11th supported file format for trial balance uploads

**Changes:**
- [x] `python-docx>=1.1.0` added to `backend/requirements.txt`
- [x] `FileFormat.DOCX` enum + `FormatProfile` in `shared/file_formats.py`
- [x] ZIP disambiguation: `_is_docx_zip()` checks for `word/` directory
- [x] `shared/docx_parser.py` — extracts tables from DOCX via python-docx
- [x] Parser dispatch in `shared/helpers.py` (`_parse_docx` wrapper + magic byte validation)
- [x] `FORMAT_DOCX_ENABLED` feature flag in `config.py` (default: true)
- [x] Frontend: `.docx` extension, MIME type, label in `utils/fileFormats.ts`
- [x] Backend tests: `test_docx_parser.py` (29 tests — disambiguation, parsing, detection, profile)
- [x] Updated `test_file_formats.py` (11 extensions, 13 MIME types)
- [x] Updated `fileFormats.test.ts` (11 entries, 13 types, DOCX acceptance)
- [x] Tier gating: paid tiers only (same as PDF/OFX/IIF/QBO/ODS)

**Review:**
- 89 backend tests pass (test_docx_parser + test_file_formats), 27 ODS tests unaffected
- 27 frontend fileFormats tests pass
- `npm run build` clean — all pages compile
- DOCX parsing extracts first table with data rows; skips header-only tables
- ZIP disambiguation: ODS (mimetype/content.xml) > DOCX (word/) > XLSX (default)

---

### Sprint 596: UnverifiedCTA — Explicit Verification Prompt on All Tool Pages
**Status:** COMPLETE
**Goal:** Replace silent content gating with an explicit "Verify Your Email" card so unverified users understand why tool pages appear blank

**Problem:** 11 of 12 tool pages hid their entire UI behind `isAuthenticated && isVerified` with no explanation. Authenticated users who hadn't verified their email saw only the page title and a blank area below — no upload zone, no controls, no message. The `VerificationBanner` in the top shell existed but was a small dismissible bar, easily overlooked. Users assumed the app was broken.

**Changes:**
- [x] New `UnverifiedCTA` component (`frontend/src/components/shared/UnverifiedCTA.tsx`) — email icon, "Verify Your Email" heading, explanation text, pointer to the resend banner. Oat & Obsidian tokens, motion entrance animation. Parallel to `GuestCTA`.
- [x] Exported from `frontend/src/components/shared/index.ts`
- [x] Added `{isAuthenticated && !isVerified && (<UnverifiedCTA />)}` block to all 11 tool pages: trial-balance, ap-testing, ar-aging, bank-rec, fixed-assets, inventory-testing, journal-entry-testing, payroll-testing, revenue-testing, statistical-sampling, three-way-match
- [x] Multi-period page left untouched — already has its own inline "Verify Your Email" card (Pattern B)
- [x] `npm run build` passes — all 12 tool pages compile cleanly

**Review:**
- Consistent three-state UX across all tools: unauthenticated → GuestCTA, unverified → UnverifiedCTA, verified → full tool UI
- The `VerificationBanner` in `AuthenticatedShell` still renders above the CTA for redundancy (resend button lives there)
- No backend changes; purely frontend UX improvement

