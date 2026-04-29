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

- [2026-04-28] nightly QA Warden green-restore — `test_security_hardening_2026_04_20.py::TestRateLimitFailClosed` `_prod_env()` fixture now sets `STRIPE_PUBLISHABLE_KEY` and `STRIPE_WEBHOOK_SECRET` placeholders alongside `STRIPE_SECRET_KEY`. Without them, the subprocess env was missing those vars, python-dotenv backfilled from `backend/.env` (developer's test-mode Stripe key), and Sprint 719's production format guard hard-failed config import — surfacing as 2 test failures in the 2026-04-28 nightly. Companion to `e6627567` (helpers-allowlist) — together both nightly RED items resolved. File: `backend/tests/test_security_hardening_2026_04_20.py`.
- [2026-04-24] record Sprint 716 COMPLETE — PR #103 merged as `6802bd63`, Render auto-deploy landed 12:51 UTC, Loki Logs Explorer confirmed 40 ingested lines with correct labels, all 6 saved queries authored. Runbook (`docs/runbooks/observability-loki.md`) §4 LogQL corrected to reflect what actually works against our ingested streams (line-filter + `| json | level="…"` instead of indexed-label selectors for level/logger, since Grafana Cloud's ingest layer doesn't index those at our volume). Lesson captured in `tasks/lessons.md` about verifying deployed code before debugging runtime (I burned ~15 min on label hypotheses before discovering the commit was local-only and Render was still running Sprint 713's image). Files: `tasks/todo.md`, `tasks/lessons.md`, `docs/runbooks/observability-loki.md`.
- [2026-04-23] archive_sprints.sh number-extraction fix + archive of Sprints 673–677 — replaced broken grep-pipeline (which filtered to Status lines first, losing the Sprint number on the preceding header) with an awk block that pairs each `### Sprint NNN` header to its Status body and emits the number when COMPLETE. Dry-run confirmed extraction (673, 674, 675, 676, 677); archival produced `tasks/archive/sprints-673-677-details.md` (142 lines, 5 sprint bodies) and reduced Active Phase to just Sprint 611 (PENDING). Unblocks Sprint 689a's `Sprint 689a:` commit under the archival gate. Files: `scripts/archive_sprints.sh`, `tasks/todo.md`, `tasks/archive/sprints-673-677-details.md`.
- [2026-04-23] Sprint 689 Path B decision — CEO chose full expansion (all 6 hidden backend tools + Multi-Currency standalone → 18-tool catalog). Execution split into 689a–g (one tool per session, single marketing-flip at 689g). Defaults rejected on evidence that the 6 routes carry ~4,500 LoC of real engine code + tests. Plan + deliverables template captured in Sprint 689 entry. Pre-requisite flagged: `scripts/archive_sprints.sh` grep-pipeline bug must be fixed (or sprints 673–677 manually archived) before the first `Sprint 689a:` commit can clear the archival gate.
- [2026-04-23] R2 provisioning — Cloudflare R2 buckets `paciolus-backups` + `paciolus-exports` (ENAM, Standard, private), two Account API tokens (Object R&W, per-bucket scoped). 8 env vars wired on Render `paciolus-api` (`R2_{BACKUPS,EXPORTS}_{BUCKET,ENDPOINT,ACCESS_KEY_ID,SECRET_ACCESS_KEY}`) — 19→27 vars, deploy live in 1 min, zero service disruption (9× /health all 200 <300ms). Unblocks Sprint 611 ExportShare migration + Phase 4.4 pg_dump cron. Mid-provisioning incident: screenshotted Render edit form while EXPORTS credentials were unmasked → rolled `paciolus-exports-rw` token before saving, only uncompromised values persisted. Full pattern captured in `tasks/lessons.md` (2026-04-23 entry). Details in `tasks/ceo-actions.md` "Backlog Blockers" section.
- [2026-04-23] d74db7c: record Sprint 673 COMPLETE — DB_TLS_OVERRIDE removed from Render prod, 2026-05-09 fuse cleared (tasks/todo.md, tasks/ceo-actions.md)
- [2026-04-22] b0ddbf6: dep hygiene + Sprint 684 tail — 3 backend pins bumped (uvicorn 0.44.0→0.45.0, pydantic 2.13.2→2.13.3, psycopg2-binary 2.9.11→2.9.12), 3 backend transitives refreshed in venv (idna 3.11→3.13, pydantic_core 2.46.2→2.46.3, pypdfium2 5.7.0→5.7.1), mypy dev-pin bumped 1.20.1→1.20.2; 4 frontend caret pins bumped (@typescript-eslint/eslint-plugin + parser ^8.58.0→^8.59.0, @tailwindcss/postcss + tailwindcss ^4.2.2→^4.2.4). Sprint 684 deferred memo-copy item landed: `sampling_memo_generator.py` Expected Misstatement Derivation section now cites AICPA Audit Sampling Guide Table A-1 explicitly. Backend `pytest` 8046 passed / 0 failed; frontend `jest` 1887 passed / 0 failed; `npm run build` clean.
- [2026-04-22] nightly audit artifacts — 2026-04-22 batch (original RED report + 4 sentinel JSONs + run_log). Preserved as historical evidence of the false-green incident that motivated Sprint 712. `.qa_warden_2026-04-22.json`, `.coverage_sentinel_2026-04-22.json`, and `.baseline.json` were committed in Sprint 712 (5d29cce) with the post-fix genuine-green values.
- [2026-04-21] 9820bb2: nightly audit artifacts — 2026-04-19, 2026-04-20, 2026-04-21 batch. Commits daily report .md + 6 sentinel JSONs + run_log per day, plus .baseline.json update to capture the Sprints 677–710 test-count growth (8028 backend / 1845 frontend).
- [2026-04-19] 9f00070: nightly dep hygiene (part 2) — remaining 3 majors cleared in venv (numpy 1.26→2.4, pip 25.3→26.0.1, pytz 2025.2→2026.1.post1). Verified zero direct imports for numpy/pytz; pandas 3.0.2 compatible with numpy 2.x; pytz has no current dependents. pytest 7836 passed / 0 failed. Venv-only change (no requirements.txt edits needed).
- [2026-04-19] 8fd93bb: nightly dep hygiene — 26 safe package bumps (19 backend venv: anthropic, anyio, docstring_parser, greenlet, hypothesis, jiter, librt, lxml, Mako, mypy, packaging, prometheus_client, pypdf, pypdfium2, pytest, python-multipart, ruff, sentry-sdk, uvicorn; 6 frontend via npm update: @sentry/nextjs, eslint-plugin-react-hooks, @typescript-eslint/*, postcss, typescript). Deferred: numpy 2.x, pip 26, pytz 2026 (majors). frontend/package-lock.json only.
- [2026-04-18] 7915d77: nightly audit artifacts — commit 2026-04-18 report + sentinel JSONs (qa_warden, coverage, dependency, scout, sprint_shepherd, report_auditor) + run_log (reports/nightly/)
- [2026-04-16] 22e16dc: backlog hygiene — Sprint 611 R2/S3 bucket added to ceo-actions Backlog Blockers; Sprint 672 placeholder for Loan Amortization XLSX/PDF export (Sprint 625 deferred work)
- [2026-04-14] a32f566: hallucination audit hotfix — /auth/refresh handler 401→403 for X-Requested-With mismatch (aligns with CSRF middleware); added .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
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
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| Move client-access helpers (`is_authorized_for_client`, `get_accessible_client`, `require_client`) out of `shared/helpers.py` shim | Three helpers depend on `User` / `Client` / `OrganizationMember` / `require_current_user`; a dedicated `shared/client_access.py` module isn't justified under the "prefer moving code, avoid new abstractions" guidance. Revisit if a fourth helper joins them, or if the shim grows another responsibility. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |

---

## Architectural Remediation Initiative

> **Source:** 8-phase remediation strategy (transcript 2026-04-29) translated into Paciolus sprint format. Stays in this backlog section until launch-readiness work clears (post Phase 4.1 Stripe cutover). Sprints are numbered + reserved but not in `## Active Phase` until promoted one batch at a time.
> **Guiding principle:** stabilize → standardize → modularize → deepen. Phases 0–1 are non-negotiable prerequisites; Phases 2–7 can re-order based on incident pressure; Phase 8 is the convergence audit.
> **Sprint 741 reserved** for cleanup-scheduler root-cause work (Sprint 740 follow-up — see Active Phase). Initiative starts at 742.
> **Cross-cutting deferred-items honored:** Sprint 746 must respect the auth cookie/CSRF helper deferral (don't touch security primitives without an audit finding); Sprint 750 coordinates with the deferred `useTrialBalanceUpload` decomposition; Sprint 745/Phase 2 spirit covers the deferred `stripe_webhook` decomposition; Sprint 754 absorbs the deferred client-access helper relocation.

### Sprint 742: ADRs + quality thresholds (Phase 0 — Baseline & Guardrails 1/2)
**Status:** COMPLETE 2026-04-29. Documents patterns Sprint 744–746a already established (ADR-014, 015) + sets target for Sprint 748–749 (ADR-016).
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 0.

**What landed:**
- `docs/03-engineering/adr-014-canonical-frontend-network-layer.md` — Accepted (Sprint 744). Direct `fetch()` banned outside the 6-file allowlist; ESLint rule enforces. Documents the canonical entrypoints (`apiGet`/`apiPost`/`apiDownload`/`uploadFetch`) and the rationale for each allowlist entry.
- `docs/03-engineering/adr-015-backend-route-service-boundaries.md` — Accepted (Sprint 745 + 746a). Three patterns: `db_transaction` for DB writes, `raise_http_error` for non-DB error paths, `services/<domain>/<workflow>.py` for multi-step business logic. Honors the cookie/CSRF boundary deferral.
- `docs/03-engineering/adr-016-export-architecture.md` — Proposed (target for Sprint 748+749). Mapper / generator separation. Routes become slim controllers. `export_memos.py` dynamic-vs-explicit ambiguity must be resolved (pick one strategy).
- `docs/03-engineering/quality-thresholds.md` — Module size targets (route 500/800, service 300/500, page 400/700, hook 200/400), function complexity (cyclomatic 8/12), hook surface (4/8 useState declarations), advisory until Sprint 756 wires CI.
- `CONTRIBUTING.md` — new "Architectural Patterns" section linking to all 4 docs.

**Out of scope:**
- Numbering — only ADR-013 existed previously, so the new 014/015/016 sit naturally next to it. No retroactive numbering of pre-existing implicit decisions.
- CI enforcement — quality thresholds remain advisory until Sprint 756.

**Exit met:** ADRs merged; threshold defaults documented; Sprints 743–759 can reference these as authority.

---

### Sprint 743: Characterization test gap analysis (Phase 0 — Baseline & Guardrails 2/2)
**Status:** COMPLETE 2026-04-29. One filed gap-fill (DashboardPage smoke test); all other surfaces sufficiently covered.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 0.

**What landed:**
- `reports/test-coverage-gap-analysis-2026-04-29.md` — full gap report. Inventoried 199 frontend test files + relevant backend modules against surfaces named in Sprints 747–752.
- `frontend/src/__tests__/DashboardPage.test.tsx` — smoke test for `app/dashboard/page.tsx` (519 lines, target of Sprint 751 decomposition). Pins: three GET requests on mount, welcome header + Quick Launch render, unauthenticated → `/login` redirect, stats-failure toast handling. 4/4 tests pass.

**Coverage findings:**
- **Auth (Sprints 746b/c/d, 747):** 214 backend tests across 13 routes + frontend `AuthContext.test.tsx`, `useAuthSession.test.ts`, `LoginPage.test.tsx`, `ForgotPasswordPage.test.tsx`. Strong regression net.
- **Exports (Sprints 748, 749):** 173 backend tests + per-page interaction tests. Sprint 749's contract tests are not pre-existing gaps (Sprint 749 produces them).
- **Dashboard + tool pages (Sprints 750, 751):** 18 tool-page tests cover Sprint 750's surface; **dashboard frontend was the one genuine gap** — backed up by 30 backend dashboard/activity tests but no targeted `app/dashboard/page.tsx` test until this sprint.
- **API error envelope:** Sprint 745's `test_route_errors.py` + `test_db_unit_of_work.py` (14 tests) + `test_log_sanitizer.py`. Covered.
- **Hooks for Sprint 752:** all named candidates (`useStatisticalSampling`, `useAccountRiskHeatmap`, `useUncorrectedMisstatements`, `useAnalyticalExpectations`) have direct tests.

**Non-gaps (rejected as pre-existing):**
- Memo PDF schema contract tests (Sprint 749 produces them).
- Export endpoint contract tests (same).
- API error envelope snapshot test (existing route tests exercise the envelope).
- `useFetchData` decomposition coverage (Sprint 752 hasn't picked the candidate yet).

**Methodology note:** the Sprint 744 test churn (4 test files pinning pre-Sprint-661 Bearer-header behavior) was a separate class of issue — outdated assertions, not missing coverage. That class self-corrects when migrations run (assertions fail loudly, get fixed). Sprint 743 does not address it.

**Exit met:** Gap report filed; one gap-fill landed; pre-refactor regression net acknowledged sufficient.

---

### Sprint 744: Frontend canonical `apiClient` enforcement (Phase 1 — Cross-Cutting 1/2)
**Status:** COMPLETE 2026-04-29. Phase 0 ADR skipped per CEO directive — proceeded directly to enforcement.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 1.

**What landed:**
- Migrated 4 direct-`fetch` outliers to canonical layers:
  - `hooks/useAccountRiskHeatmap.ts` `downloadCsv` → `apiDownload` + `downloadBlob` (was 27 lines of manual blob-anchor handling).
  - `app/tools/depreciation/page.tsx` `onDownloadCsv` → `apiDownload` + `downloadBlob`.
  - `app/tools/loan-amortization/page.tsx` `downloadExport` → `apiDownload` + `downloadBlob`.
  - `hooks/useStatisticalSampling.ts` `executeSamplingUpload` → `uploadFetch` from `uploadTransport`.
- Renamed shadowed local `fetch` in `hooks/useRollingWindow.ts` → `fetchRollingData` (was destructured from `useFetchData`, tripping the new lint rule).
- ESLint rule (`no-restricted-syntax` `CallExpression[callee.name="fetch"]`) banning direct `fetch()` outside the allowlist. Per-file override block exempts the canonical transport/auth modules.
- Allowlist (escaped `[token]` for minimatch): `utils/transport.ts`, `utils/authMiddleware.ts`, `utils/downloadAdapter.ts`, `utils/uploadTransport.ts`, `contexts/AuthSessionContext.tsx`, `app/shared/[token]/page.tsx` (public passcode-flow share page — intentionally low-level for 429 Retry-After parsing).
- Updated 4 affected test files to mock at the `apiDownload`/`downloadBlob` boundary instead of `global.fetch` (the old assertions checked `Authorization: Bearer` headers, but the canonical pattern uses HttpOnly cookie auth via `credentials: 'include'` — tests were pinning obsolete behavior).

**Verification:**
- `npx eslint src/**/*.{ts,tsx}` → exit 0 (clean).
- `npx tsc --noEmit` → exit 0.
- 4 affected jest suites: 26/26 passing (`useAccountRiskHeatmap`, `useStatisticalSampling`, `DepreciationPage`, `AccountRiskHeatmapPage`); `LoanAmortizationPage`: 8/8.

**Out of scope (deferred):**
- Unify user-facing error normalization through one path — partially achieved (the canonical `apiDownload`/`uploadFetch`/`apiPost` already return structured `{ ok, error }`), but consumer-side error UX is still per-page. Full unification is bundled into Sprint 752 (render-perf + decomposition pass).
- ADR document (Phase 0 deliverable) — skipped. The lint rule + allowlist comments serve as the canonical record.

**Exit met:** Single fetch pattern; CI enforces it via ESLint rule.

---

### Sprint 745: Backend transaction + route-error standardization (Phase 1 — Cross-Cutting 2/2)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 1.

**What landed:**
- `backend/shared/db_unit_of_work.py` — `db_transaction(db, *, log_label, log_message=None)` context manager. Replaces the `try: db.commit(); except SQLAlchemyError as e: db.rollback(); logger.exception(...); raise HTTPException(500, detail=sanitize_error(e, log_label=...))` triad copy-pasted across ~12 route modules.
- `backend/shared/route_errors.py` — `raise_http_error(status_code, *, label, user_message, exception, operation, allow_passthrough)` helper. Centralizes 4xx + non-DB 5xx error responses with sanitized detail + structured-log metadata. Complements `db_transaction` (DB) with the non-DB error path.
- Pilot migration on `routes/activity.py` — 4 sites (`db_activity_create`, `db_activity_clear`, `db_tool_activity`, `db_prefs_update`) converted to `with db_transaction(...)`. Removed unused `SQLAlchemyError` + `sanitize_error` imports. Net `-30` lines on activity.py.

**Verification:**
- `tests/test_db_unit_of_work.py` — 7 tests covering: clean commit, SQLAlchemyError rollback+500, non-SQLAlchemy propagation (no rollback), IntegrityError handling, sanitization (no SQL/PII leak), log message override, default log message.
- `tests/test_route_errors.py` — 7 tests covering: user_message wins, default fallback, exception-only path uses `sanitize_error`, passthrough returns safe original message, passthrough blocks internal-detail leakage, status code propagation across 9 codes.
- `tests/test_activity_api.py` (13) + `tests/qa/test_activity_recent.py` (5) — all 18 pre-existing route tests still pass post-migration. 32/32 total.

**Out of scope (deferred to Sprint 755 or later):**
- Migrating the remaining ~11 route modules (`auth_routes.py`, `billing.py`, `diagnostics.py`, etc.) to `db_transaction`. Sprint 745 ships the pattern + pilot; broad adoption is incremental and naturally folds into Sprints 746–747 (auth) and follow-up cleanup work.
- The deferred `routes/billing.py::stripe_webhook` decomposition can now use both helpers — re-evaluate that deferred item once the auth refactor (Sprint 746) lands.

**Exit met:** One transaction pattern + one route-error pattern; pilot on `activity.py` demonstrates parity (18/18 pre-existing tests pass); pattern documented for incremental adoption via module docstrings.

---

### Sprint 746: Auth service-layer extraction (Phase 2 — Auth Decomposition 1/2)
**Status:** **COMPLETE** 2026-04-29 — All four sub-sprints (746a recovery, 746b identity, 746c registration, 746d sessions) shipped this session.
**Priority:** **P2** — security-sensitive surface; highest-risk refactor in plan.
**Source:** Architectural Remediation Plan phase 2.

Extract service layer from `auth_routes.py` into focused subdomains:
- ✅ **Sprint 746a — `services/auth/recovery.py`** (password reset lifecycle). Shipped 2026-04-29. `forgot_password` and `reset_password` routes are now ~10 lines each (validate → call service → return response). Service exposes `initiate_password_reset(db, email) → PasswordResetInitiation` and `complete_password_reset(db, token, new_password) → User` (raises `PasswordResetError` for invalid/used/expired/inactive — route maps to `HTTPException(400)`). Both 41 pre-existing password tests pass.
- ✅ **Sprint 746b — `services/auth/identity.py`** (login/logout/refresh + token issuance/rotation). Shipped 2026-04-29. `IdentityIssuance` dataclass + `authenticate_login`, `refresh_session`, `revoke_session_token`. login route shrunk 60 → 22 lines; refresh ~30 → ~22 lines. `/auth/me` already thin (no extraction needed). Cookie writes stay in route. 10 unused imports removed from `auth_routes.py`. 219 auth tests pass (172 + 47 verification).
- ✅ **Sprint 746c — `services/auth/registration.py`** (registration + verification lifecycle). Shipped 2026-04-29. `register_user`, `complete_email_verification`, `resend_verification_email` + 4 domain exception classes (`RegistrationError`, `EmailVerificationError`, `EmailAlreadyVerifiedError`, `VerificationCooldownError`). register route shrunk 86 → 33 lines; verify-email 40 → 9 lines; resend-verification 53 → 27 lines. 11 unused imports removed (`EmailVerificationToken`, `is_disposable_email`, `generate_verification_token`, `ENV_MODE`, `hash_token`, `create_user`, `create_access_token`, `create_refresh_token`, `sanitize_error`, `SQLAlchemyError`, `get_user_by_email`). Two test patches updated to point at `services.auth.registration` instead of `routes.auth_routes`. 189/189 auth tests pass.
- ✅ **Sprint 746d — `services/auth/sessions.py`** (session inventory + revocation). Shipped 2026-04-29. `list_user_sessions` (returns `SessionEntry` list), `revoke_session_by_id` (raises `SessionNotFoundError` for unknown / cross-user / already-revoked), `revoke_all_user_sessions`. list_sessions route 32 → 16 lines; revoke_session 22 → 12 lines; revoke_all_sessions 12 → 7 lines. Removed 4 unused imports (`datetime`, `UTC`, `_revoke_all_user_tokens`, `RefreshToken`). 233/233 auth + helper tests pass.

**Honors deferred-items boundary:** Sprint 746a moves only business logic. Cookie/CSRF primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) remain in the route layer per the deferred-items guidance. Token issuance + cookie writes will need careful handling in Sprint 746b.

**What landed in 746a:**
- `backend/services/auth/__init__.py` — package marker + roadmap docstring.
- `backend/services/auth/recovery.py` — 156 lines. `PasswordResetError` (subclass of `ValueError`), `PasswordResetInitiation` dataclass, `initiate_password_reset`, `complete_password_reset`. Uses `db_transaction` from Sprint 745 for the commit/rollback path. Preserves Sprint 594/595 diagnostic (total-user-count log on unknown-email lookup).
- `backend/routes/auth_routes.py` — `forgot_password` shrunk from 60 → 19 lines; `reset_password` from 50 → 14 lines. Removed unused imports (`generate_password_reset_token`).
- 41/41 pre-existing password tests still pass.

**Exit (partial):** One auth subdomain (recovery) extracted as proof-of-pattern. Identity / registration / sessions remaining.

---

### Sprint 747: Auth route thinning + security response normalization (Phase 2 — Auth Decomposition 2/2)
**Status:** **COMPLETE** 2026-04-29. Sprint 747a (enumeration-safe helper) + Sprints 746b/c/d (which fully thinned login/refresh/logout/register/verify-email/resend/sessions handlers as a side effect of service extraction) collectively delivered the sprint's scope.
**Priority:** P2.
**Source:** Architectural Remediation Plan phase 2.

**What landed in 747a:**
- `backend/services/auth/security_responses.py` — `raise_invalid_credentials()` helper. Single source of truth for the AUDIT-07 F4 enumeration-safe 401 response (same body + `WWW-Authenticate: Bearer` header for wrong-password / unknown-email / locked-account / IP-blocked).
- `routes/auth_routes.py::login` — three duplicated `HTTPException(401, ...)` raises (lines 276/289/301) collapsed to `raise_invalid_credentials()` calls. Behavior preserved verbatim.
- `backend/tests/test_auth_security_responses.py` — 3 tests pinning the stable body, header, and inter-call-shape consistency. Plus 36 pre-existing auth route + parity tests still pass (39/39).

**Final state (after 746b/c/d):**
- All 13 auth route handlers are now orchestration-only (~10–25 lines each). Cookie writes + HTTP plumbing in routes; business logic + DB persistence in services.
- AUDIT-07 F4 enumeration-safe 401 response is a single helper (`raise_invalid_credentials`) called from inside the identity service.
- 4 service modules in `backend/services/auth/`: `recovery`, `identity`, `registration`, `sessions` (+ `security_responses` shared helper).
- 233/233 auth + helper tests pass after the full Phase 2 sweep.

**Out of scope (deferred to a future cleanup sprint, low priority):**
- `check_ip_blocked` + `check_lockout_status` consolidation into a single `pre_auth_check_or_raise()` helper. Sequential calls in `authenticate_login` are clear in context; consolidation would be cosmetic, and the two calls have distinct logging + recording semantics (only the lockout-failure branch calls `record_ip_failure`). Revisit only if a fifth pre-auth check joins them.

**Exit met:** All auth handlers are thin orchestration layers; security-critical behaviors covered by focused service-level tests; no monolithic-route assumptions remain.

---

### Sprint 748: Export mapper layer + diagnostics refactor (Phase 3 — Export Rationalization 1/2)
**Status:** **PARTIAL** 2026-04-29 — 6/10 routes migrated. PDF/Excel/Leadsheets/FinancialStatements (4 routes) deferred to Sprint 748b because they need user/branding context to flow through the pipeline (the existing `export.pipeline` functions don't yet accept `User`/`Session` for `apply_pdf_branding`).
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 3.

**Discovery:** `backend/export/` package already exists (Sprint 539+) with `pipeline.py` + `serializers/` implementing the mapper/generator separation per ADR-016. Routes had drifted into a parallel inline implementation. Sprint 748 is therefore a delegation migration, not a new layer build.

**What landed in 748a:**
- 6 CSV routes in `routes/export_diagnostics.py` migrated to delegate to `export.pipeline`:
  - `export_csv_trial_balance` (66 lines → 2)
  - `export_csv_anomalies` (71 lines → 2)
  - `export_csv_preflight_issues` (24 lines → 2)
  - `export_csv_population_profile` (58 lines → 2)
  - `export_csv_expense_category` (64 lines → 2)
  - `export_csv_accrual_completeness` (45 lines → 2)
- Net `export_diagnostics.py` shrunk 661 → 358 lines (~46% reduction).
- Removed unused `sanitize_csv_value` import (no longer referenced after migration).
- 119/119 export tests pass (`test_export_diagnostics_routes`, `test_export_routes`, `test_export_csv_serializers`).

**Deferred to Sprint 748b:**
- PDF, Excel, Leadsheets, Financial Statements routes (4 endpoints). The pipeline's `export_diagnostic_pdf` / `export_diagnostic_excel` don't accept `User`/`Session` — they can't apply Sprint 679's Enterprise PDF branding via `apply_pdf_branding(load_pdf_branding_context(current_user, db))`. Sprint 748b extends the pipeline signatures to accept optional branding context, then completes the migration.

**Exit (partial):** 6 of 10 diagnostic routes are slim controllers delegating to the existing pipeline. Transformation logic is consistently owned by `export.serializers.*`. Branding-aware routes await pipeline signature extension.

---

### Sprint 749: Export endpoint skeleton standardization + memos harmonization (Phase 3 — Export Rationalization 2/2)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 3.

**What landed:**
- **ADR-016 promoted from Proposed → Accepted.** Documents the registry-driven memo dispatch as canonical: standard memos use `_STANDARD_REGISTRY` + `_register_standard_routes()` (16 routes today, 1-line entry per memo); non-standard memos that need custom Pydantic preprocessing get an explicit `@router.post(...)` decorator that calls the shared `_memo_export_handler` with a `CustomPreprocessor` (2 routes today: sampling-evaluation, flux-expectations). The mixed-style pattern is intentional, not drift.
- **PDF contract test pattern demonstrated.** New `backend/tests/test_export_pdf_contract.py` extracts text from generated memo PDFs via `pypdf.PdfReader` and asserts required section labels appear. Catches regressions where a section is silently removed or renamed (which CI/lint cannot detect). Sprint 749 ships the pattern with the JE Testing memo (5 required labels: title, "Tier", "Conclusion", "Findings", "Composite"); subsequent sprints extend to the remaining 17 memos as they're touched.
- Inline note on the contract-test file documents the multi-column PDF layout caveat: `pypdf` can split phrases across column boundaries, so prefer single-word anchors over multi-word phrases.

**Out of scope (deferred or covered elsewhere):**
- Standardize endpoint skeleton across PDF/Excel/Leadsheets/FinStmts routes — Sprint 748b's scope (needs pipeline branding-context plumbing).
- Move existing tests into a dedicated `tests/contract/` directory — pure churn; the per-file `_export_pdf_contract.py` naming is sufficient signal.
- Contract tests for all 18 memos — demonstrate the pattern, extend incrementally.

**Verification:** `tests/test_export_pdf_contract.py` 2/2 pass.

**Exit met:** Export endpoint shape consistency landed via Sprint 748a + memo registry pattern; ADR-016 documents the canonical strategy; PDF contract-test pattern in place with one demo memo.

---

### Sprint 750: Tool page architecture template + multi-period refactor (Phase 4 — Frontend Decomposition 1/3)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 4.

**What landed:**
- **ADR-017** (`docs/03-engineering/adr-017-tool-page-architecture-template.md`) — documents the canonical tool-page composition pattern: domain workflow hooks (uploads / comparison / export) + local UI/form state + thin orchestration callbacks + render-only JSX. Defines the local-state-vs-hook decision criteria (>15 lines, reused, async op, must be unit-testable).
- **`frontend/src/hooks/usePeriodUploads.ts`** (142 lines) — owns the three-slot `PeriodState` upload state machine for multi-period: prior / current / budget. Exposes derived `canCompare` / `anyLoading`, `toggleBudget` (clears stale state on OFF), `reset`, and an optional `onBeforeUpload` callback so consumers can clear stale comparison results when a new file lands.
- **`frontend/src/hooks/useMultiPeriodMemoExport.ts`** (81 lines) — owns the memo PDF export workflow: lead-sheet field stripping, metadata fallback to "Not specified", `apiDownload` invocation, `downloadBlob` trigger. Tracks `exporting` for button disabling.
- **Multi-period page refactored to composition root** — 501 → 423 lines. Inline 30-line `auditFile` machine, three `setPeriod` state buckets, `showBudget` toggle, and 44-line memo export gone. Page is now: auth + 3 hook calls + form state + thin orchestration callbacks + JSX.
- **8 hook tests for `usePeriodUploads`** (`__tests__/usePeriodUploads.test.ts`) covering: idle init, success transition, error transition, canCompare without/with budget, toggleBudget OFF clears state, reset, onBeforeUpload callback hook.
- **8 hook tests for `useMultiPeriodMemoExport`** (`__tests__/useMultiPeriodMemoExport.test.ts`) covering: starts idle, no-op on null token, lead-sheet stripping, metadata fallback, server filename use, default filename fallback, ok=false skip, error reset.
- Existing 8 multi-period page tests updated to mock the two new hooks. All 24 tests pass.

**Out of scope (deferred):**
- The deferred `useTrialBalanceUpload` decomposition — Sprint 750 didn't touch it. Multi-period uses the `uploadTrialBalance` utility function, not the `useTrialBalanceUpload` hook. The deferred-items entry remains valid as separate scope.
- Filter/metadata state extraction. Per ADR-017's local-state criteria, simple `useState` for filter strings and form labels stays inline — wrapping in a hook would be aesthetic-only.

**Verification:** `tsc --noEmit` clean, ESLint clean, 24/24 affected jest tests pass.

**Exit met:** Multi-period page is composition-only; ADR-017 documents the template; both pilot hooks have direct unit tests. Sprint 751 (dashboard decomposition) replicates the pattern next.

---

### Sprint 751: Dashboard decomposition (Phase 4 — Frontend Decomposition 2/3)
**Status:** COMPLETE 2026-04-29. Applies the ADR-017 template to `app/dashboard/page.tsx`.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 4.

**What landed:**
- **`frontend/src/content/dashboard-tools.ts`** — `DASHBOARD_TOOLS` (13 entries) + `DEFAULT_FAVORITES` + types. Single SoT for the dashboard's view of the catalog (decoupled from marketing `tool-ledger.ts`).
- **`frontend/src/components/dashboard/ToolIcon.tsx`** — `<ToolIcon iconKey={...} />` presentational component wrapping `TOOL_ICON_PATHS`. The 14 SVG path strings live here instead of inline in the page. Unknown keys fall back to `cube`.
- **3 new hooks** (`frontend/src/hooks/`):
  - `useDashboardStats(token, { onError })` → `{ stats, loading, error, retry }`. Auto-fetches `/dashboard/stats` on mount.
  - `useActivityFeed(token, { limit?, onError })` → `{ activity, loading, error, retry }`. Default `limit=8`.
  - `useUserPreferences(token, { onError })` → `{ favorites, toggleFavorite }`. Optimistic update + revert on PUT failure.
- **`app/dashboard/page.tsx` refactored to composition root** — 519 → 383 lines (-26%). Inline 78-line `TOOLS` catalog, 22-line `getToolIcon` SVG dump, two retry callbacks, three-fetch `useEffect`, and `toggleFavorite` machine all gone.
- **17 new hook tests** (4 + 5 + 8) covering happy path, null-token no-op, error → onError, retry, custom limit, optimistic-add/remove, revert on PUT failure.
- **DashboardPage smoke test (Sprint 743) still passes 4/4** — test mocks `apiGet`/`apiPut` directly, so the new hooks work transparently.

**Verification:** `tsc --noEmit` clean, ESLint clean, 21/21 affected jest tests pass.

**Exit met:** Dashboard logic in 3 narrow workflow hooks + presentational icon component + content-layer catalog. Tool metadata cannot drift across surfaces.

---

### Sprint 752: Oversized hook decomposition + render-perf guards (Phase 4 — Frontend Decomposition 3/3)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 4.

**Hook decomposition (`useFormValidation` 516 → 280 lines):**
- **`frontend/src/lib/validation/engine.ts`** (95 lines) — pure validation engine. No React imports. `validateFieldValue`, `validateAllFields`, `isFormValid`, `isFormDirty` + the type union (`ValidationRule`, `ValidationRules`, `FormErrors`, `TouchedFields`, `FormValues`). Deterministic, side-effect-free, reusable outside React (CLI scripts, server-side validation).
- **`frontend/src/lib/validation/validators.ts`** (87 lines) — `commonValidators` factory exports (8 reusable rules: required, minLength, maxLength, email, matches, min, max, pattern). Decoupled from the hook so they're unit-testable as plain function calls.
- **`frontend/src/hooks/useFormValidation.ts`** (280 lines, was 516) — React adapter. Owns `useState` slots + event handlers + render-stable getters. Delegates all validation to the pure engine. Re-exports types + `commonValidators` for backward compatibility (existing call sites unchanged).
- **Bug fix bundled in:** the legacy `setValue`'s `setTimeout(() => ..., 0)` for `validateOnChange` captured stale `values` in closure. The adapter now validates inside the `setValuesState` callback against the post-update values — eliminates the stale-closure race the timer was masking.
- **19 new pure-engine tests** (`__tests__/validationEngine.test.ts`) covering each pure function + every commonValidator. Existing 47 useFormValidation tests still pass without rewrites.

**Render-perf guards (dashboard hot path):**
- **`app/dashboard/page.tsx`** — memoized 3 derivations that previously reallocated on every render:
  - `summaryLine` (depends on `stats`)
  - `displayTools` (depends on `favorites`)
  - `toolByKey` Map for activity-feed lookup (constant — was O(n) `DASHBOARD_TOOLS.find` per row, now O(1) `toolByKey.get`)
- The activity feed renders up to 8 rows; the find-per-row pattern was negligible alone but compounded with mega-component rerenders. Memoized once at composition root.
- Hooks declared BEFORE the `if (!authenticated) return …` early return per `react-hooks/rules-of-hooks` (caught by ESLint).

**Verification:** `tsc --noEmit` clean, ESLint clean (3 violations caught + fixed during the sprint), 112/112 affected jest tests pass (47 useFormValidation + 19 validationEngine + 4 DashboardPage smoke + 42 consumer tests across LoginPage / RegisterPage / CreateClientModal / EditClientModal).

**Out of scope (deferred):**
- `getFieldProps(field)` allocates a new options object per call — child components rerender even when nothing relevant changed because the prop object identity changes. Per-field memoization via a Map is non-trivial because `field` is a runtime parameter; defer until profiling actually surfaces it as a hotspot.

**Exit met:** Form validation engine is testable without React; commonValidators are independently importable; dashboard derivations no longer reallocate per render. Hook responsibilities are narrow.

---

### Sprint 753: Domain package relocation (Phase 5 — Domain Consolidation 1/2)
**Status:** PENDING. Depends on Sprint 745 (route patterns landed first).
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 5.

Per-tool layout:
- `services/<domain>/analysis.py`
- `services/<domain>/schemas.py`
- `services/<domain>/export.py`

Relocate large top-level engines (e.g., `audit_engine.py`, tool-specific engines) into consistent domain modules. Routes update imports only — no behavior changes.

**Exit:** Domain logic consistently organized; top-level `backend/*.py` engine files emptied or shrunk to thin re-exports.

---

### Sprint 754: Common analysis interfaces + helper dedup (Phase 5 — Domain Consolidation 2/2)
**Status:** PENDING. Depends on Sprint 753.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 5.

- Shared interfaces: input contract, result envelope, error semantics for tool services.
- Consolidate duplicated helpers (numeric normalization, risk-band parsing, threshold handling) into one module.
- Module-boundary tests: routes don't bypass domain contracts (e.g., importing engine internals directly).

**Absorbs deferred item:** the deferred move of client-access helpers (`is_authorized_for_client`, `get_accessible_client`, `require_client`) out of `shared/helpers.py` is in scope here if a fourth helper has joined them by the time this sprint runs.

**Exit:** Tool services follow shared contracts; cross-tool duplication materially reduced; boundary discipline test-enforced.

---

### Sprint 755: Dead code + duplicate type cleanup (Phase 6 — Drift Elimination 1/2)
**Status:** PENDING. Depends on Sprints 744, 745, 750–754 (so we know what's actually obsolete).
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 6.

- Audit dead utilities, duplicate DTOs/types, commented legacy code paths.
- Remove deprecated adapters and one-off helpers superseded by Phase 1–5 standard layers.
- Consolidate duplicated constants/magic strings into typed config modules.

**Exit:** Legacy parallel patterns removed; the standard layer is the only path.

---

### Sprint 756: Architecture conformance CI + docs refresh (Phase 6 — Drift Elimination 2/2)
**Status:** PENDING. Depends on Sprint 755.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 6.

- CI checks: forbidden imports/layers (route → engine internals), duplicate route patterns, banned direct network calls (extends Sprint 744's lint rule to repo-wide coverage).
- Update `CONTRIBUTING.md` + `CLAUDE.md` architecture sections + relevant runbooks to reflect new structure.

**Exit:** Drift detectors enforced in CI; contributor docs match reality.

---

### Sprint 757: Network duplication + transformation hotspot audit (Phase 7 — Performance Hardening 1/2)
**Status:** PENDING.
**Priority:** P3 — structural perf only; not a micro-tuning sprint.
**Source:** Architectural Remediation Plan phase 7.

- Instrument frontend network duplication / over-fetching (Sentry breadcrumbs + browser perf-panel sample).
- Consolidate repeated transformations into memoized/shared selectors.
- Audit backend endpoints for heavy synchronous shaping in routes; relocate to services/mappers per Sprints 745, 748.

**Exit:** Duplicate requests reduced; expensive transformations off render paths.

---

### Sprint 758: Pagination + cache invalidation coherence (Phase 7 — Performance Hardening 2/2)
**Status:** PENDING.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 7.

- Standardize pagination/limit conventions for activity/history feeds and other high-volume endpoints.
- Audit cache invalidation across mutation endpoints; ensure no stale reads after mutations.

**Exit:** Pagination + cache-invalidation patterns predictable and bounded.

---

### Sprint 759: Convergence scorecard + governance lane (Phase 8 — Convergence)
**Status:** PENDING. Final sprint of Architectural Remediation Initiative.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 8.

- Repo-wide consistency review against the original 8-phase weakness list.
- Scorecard each weakness: resolved / partial / open with rationale → file in `reports/architectural-remediation-scorecard-YYYY-MM-DD.md`.
- Define ongoing governance cadence: periodic architecture health review, complexity-budget checks, "no new god files" policy.
- Establish refactor intake lane in backlog so debt remains visible and prioritized.

**Exit:** Every weakness in the original plan has a mapped outcome; governance prevents relapse.

---

## Active Phase
> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). **Recommended path: ship on ~3-week ETA** with two engineering amendments — Sprint 673 below removes the 2026-05-09 TLS-override fuse before it collides with launch week, and Guardian's 5-item production-behavior checklist runs in parallel with Phase 3/4.1 (tracked in [`ceo-actions.md`](ceo-actions.md) "This Week's Action Map"). Full verdict tradeoff map in conversation transcript.
> **Prior sprint detail:** All pre-Sprint-673 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers.
> **CEO remediation brief 2026-04-15** — Sprints 665–671 cleared the blocking TB-intake issues from the six-file test sweep. Sprints 668–671 remaining pending items archived alongside — no longer blocking launch.
> Sprints 673–677 archived to `tasks/archive/sprints-673-677-details.md`.
> Sprint 611 + Sprints 677–714 archived 2026-04-24 to `tasks/archive/sprints-611-714-details.md` (eight post-Sprint-673 batches: Post-Audit Remediation, Anomaly Framework Hardening, Security Hardening Follow-Ups, Design Refresh, Production Bug Triage, Nightly Agent Remediation, Branding Coverage Completion, P2 Sentry Sweep). Only Sprint 715 remains pending.
> Sprints 716–720 archived to `tasks/archive/sprints-716-720-details.md`.
> Sprints 721–725 archived to `tasks/archive/sprints-721-725-details.md`.
> Sprints 726–731 archived to `tasks/archive/sprints-726-731-details.md`.
> Sprints 715–729 archived to `tasks/archive/sprints-715-729-details.md`.
> Sprints 733–737 archived to `tasks/archive/sprints-733-737-details.md`.

### Sprint 732: cleanup_scheduler recurring InternalError triage
**Status:** **STEPS 1-3 COMPLETE 2026-04-28 — Sprint 740 ships the structural fix; awaits next post-deploy cycle to surface the actual root psycopg2 class for Sprint 741.** Initial post-Sprint-737-deploy silence (13:00–16:08 UTC, ~3h) was deployment-churn artifact: each merged PR (#117 13:00, #120 13:47, #119 14:13, #121 15:08) reset the cleanup_scheduler's 60-min interval timer, and the first post-deploy cycle on Sprint 739's deploy at 15:08 UTC fired at 16:08 UTC and **hit the failure with the new `error_orig_fqn` field populated**. The verification-window approach paid off — silence was coincidental (deploy churn, not structural fix), pattern resumed once a deploy had a clean 60-min window. Sprint 737 was NOT the fix. Sprint 740 (immediately below) addresses the cascade-masking that hid the real root class; Sprint 741 will address whatever Sprint 740 unmasks.

**Leaf class identified (16:08:55 UTC `reset_upload_quotas` + 16:09:28 UTC `dunning_grace_period`):**
```
error_type_fqn:    sqlalchemy.exc.InternalError    (SQLAlchemy wrapper)
error_cause_fqn:   psycopg2.errors.InFailedSqlTransaction
error_orig_fqn:    psycopg2.errors.InFailedSqlTransaction
error_orig_pgcode: 25P02                            ← SQLSTATE: in_failed_sql_transaction
```

**SQLSTATE 25P02** ("current transaction is aborted, commands ignored until end of transaction block") means a prior statement in the cleanup job's session/transaction failed, and subsequent statements are rejected until rollback. **The real failing statement is masked by this cascade** — likely the lock-release `DELETE FROM scheduler_locks` in `with_scheduler_lock`'s finally block (`backend/cleanup_scheduler.py:154-157`) firing on a session whose actual cleanup work already failed silently. Step 3's fix needs to rollback the session BEFORE the lock release tries to use it.
**Priority:** P2 → P1 once Phase 4.1 lands (silent recurring failure on `dunning_grace_period` blocks delinquent-subscription auto-cancellation, which becomes customer-visible the moment real money flows).
**Source:** Sprint 715 Render-log sweep 2026-04-26.

**Observed signal (2026-04-25 to 2026-04-26 in Render logs, srv-d6ie9l56ubrc73c7eq2g):**
```
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'reset_upload_quotas',  'error': 'InternalError: scheduled cleanup failed'}
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'dunning_grace_period', 'error': 'InternalError: scheduled cleanup failed'}
```
Both jobs fire roughly every hour; each invocation completes in 30–80ms with `records_processed: 0` and the same `InternalError`. **Diagnosis (2026-04-27):** the bare class name `InternalError` is ambiguous — Python's `builtins`, `sqlalchemy.exc`, and `psycopg2` all expose it. `cleanup_scheduler._run_cleanup_job` was using `sanitize_exception(exc, context="scheduled cleanup")` (correct PII-safe choice) but that strips both the message and the module path, leaving the log fingerprint useless for triage.

**Step 1 — Observability fix (DONE):**
- `backend/cleanup_scheduler.py::CleanupTelemetry` — added `error_type_fqn` field (e.g. `sqlalchemy.exc.InternalError`, `psycopg2.errors.SerializationFailure`). Module-path metadata only; no PII risk.
- `_run_cleanup_job` populates `error_type_fqn` from `caught_exc` so the structured log carries the disambiguating fingerprint without leaking exception messages.
- `tests/test_cleanup_scheduler.py::test_failure_log_includes_traceback_exc_info` extended to assert `error_type_fqn` appears with the FQN (`builtins.RuntimeError` for the test's deliberate `RuntimeError`). 28/28 cleanup-scheduler tests passing.

**Step 2 — Root cause investigation (DONE 2026-04-28):**
- Sub-step 2a (DONE 2026-04-27 17:14 UTC): Pulled Render logs filtered to `error_type_fqn` after Step 1's deploy (`dep-d7nom57avr4c73fgn9ig`, live 16:14:41 UTC). **Result: `sqlalchemy.exc.InternalError` on both jobs** (`reset_upload_quotas` + `dunning_grace_period`, both at 17:14 UTC). This is the SQLAlchemy wrapper — the leaf cause sits one level deeper inside `caught_exc.__cause__` / `caught_exc.orig`.
- Sub-step 2b (DONE 2026-04-27 via PR #117): Extended cleanup_scheduler observability to also capture `__cause__` (raise-from chain), `.orig` (SQLAlchemy DBAPIError attribute holding the wrapped psycopg2 exception), and `orig.pgcode` (Postgres SQLSTATE — standardized 5-char code, no PII). 29/29 cleanup-scheduler tests passing.
- **Sub-step 2c (DONE 2026-04-28 16:08 UTC): leaf class identified via the new fields.** First post-deploy cycle on Sprint 739's deploy (15:08 UTC) fired at 16:08 UTC for `reset_upload_quotas` and 16:09 UTC for `dunning_grace_period` — both with full new-field population. Leaf: `psycopg2.errors.InFailedSqlTransaction` (SQLSTATE 25P02). The intervening 13:00–16:08 UTC silence was deploy-churn artifact (4 successive PR merges each reset the cleanup_scheduler's 60-min interval timer; first uninterrupted 60-min window was Sprint 739's deploy → 16:08 cycle).
- Sub-step 2d (Sentry cross-check — NO LONGER NEEDED): root cause now identified directly from Render logs via the Sprint 732 step 2b new fields. Sentry tracebacks for past 48h would corroborate if needed, but the SQLSTATE + class-name pair is unambiguous.

**Step 3 — Fix + coverage (REQUIRED, file as Sprint 740):**

The InFailedSqlTransaction error is a **cascade symptom**, not the root failure. SQLSTATE 25P02 means "the prior statement in this transaction failed; subsequent statements are rejected." The visible failure is whatever statement fired AFTER the actual root failure on the same session — most likely the lock-release `DELETE FROM scheduler_locks` in `backend/cleanup_scheduler.py::with_scheduler_lock`'s finally block (line 154–157). The real first failure (in `cleanup_func` body) is masked.

Sprint 740 fix outline:
1. **Save & rollback:** wrap the `cleanup_func(db)` invocation inside `_run_cleanup_job` in its own `try/except` that calls `db.rollback()` on any exception BEFORE the `with_scheduler_lock` finally block runs. That way the lock release runs on a clean session, the InFailedSqlTransaction cascade is broken, and the original exception (with its real class + traceback) surfaces in the log + Sentry instead of the generic 25P02.
2. **Or:** use a separate `SessionLocal()` for the lock acquire/release vs. the cleanup work. Two sessions = lock-release session is unaffected by cleanup-session aborts. Slightly heavier infra change but eliminates the failure mode entirely.
3. **Either way, add an integration test** (`tests/test_cleanup_scheduler_session_isolation.py` or extend the existing file) that injects a deliberate IntegrityError mid-cleanup and asserts: (a) the original exception class surfaces in logs (not InFailedSqlTransaction), (b) the lock is still released, (c) subsequent cleanup cycles run normally.
4. **Verify dunning escalation end-to-end** on a staging-equivalent fixture once the cascade is fixed — was originally blocked by the masked failure; now actionable.

**Effort estimate:** Step 3 work as Sprint 740 = 0.5–1 sprint. Total Sprint 732 = ~1 sprint (Steps 1–2 done) + Sprint 740's 0.5–1 sprint for the structural fix.

**Pre-requisites for Sprint 740:** None — observability is already shipped, root cause is named, fix path is mechanical.

---

### Sprint 738: Alembic migration drift cleanup
**Status:** PENDING — pre-4.1 sequence position 1.5 (immediately after Sprint 737, before Sprint 733). Could slip post-4.1 if priority shifts; not customer-visible either way.
**Priority:** P3. Catches up on dormant tech debt surfaced by Sprint 737's drift test. Does not block any sprint.
**Source:** Sprint 737's parity test (`backend/tests/test_alembic_models_parity.py`) discovered 4 tables and 6 columns defined on models with no corresponding Alembic migration. Filed as a follow-up sprint so Sprint 737 itself stayed in scope (delete dead code + add drift detection).

Write Alembic migrations for the documented drift in `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS`. As each migration lands, remove the corresponding entry from the allow-list. When both allow-lists are empty, the parity test enforces full Alembic-models equivalence going forward.

**Tables needing CREATE TABLE migrations (4):**
- `password_reset_tokens` — defined in `backend/models.py`
- `processed_webhook_events` — defined in `backend/subscription_model.py`
- `tool_activities` — defined in `backend/models.py`
- `waitlist_signups` — defined in `backend/models.py`

**Columns needing ADD COLUMN migrations (6):**
- `engagements.completed_at` + `engagements.completed_by` — defined in `backend/engagement_model.py`
- `diagnostic_summaries.ccc` + `dio` + `dpo` + `dso` (cash-conversion-cycle ratios) — defined in `backend/models.py`

**Step 1 — production verification gate (FIRST, DO NOT SKIP):** Before writing any migration, query production Postgres via Render MCP `query_render_postgres` (or `psql` against `paciolus-api-db`) to confirm whether each of these 10 schema objects already exists in production. Three possible outcomes per object:
1. **Object exists in production but not in Alembic** → write a migration whose `op.create_table` / `op.add_column` is wrapped in an existence check (or use Alembic's `op.execute` with `IF NOT EXISTS`) so it's idempotent on re-run. The migration's job is to bring Alembic's recorded history into sync with production reality, not to actually mutate production schema.
2. **Object missing in production** → write a normal `op.create_table` / `op.add_column` migration; production gains the column on next deploy.
3. **Object never accessed in production** (model is dead code) → consider removing the model definition instead of writing the migration. Verify via grep + Render request-log analysis.

**Out of scope:**
- No model-side changes (the models are the source of truth; Alembic catches up to them).
- No removal of `Base.metadata.create_all()` from `init_db()` — it currently creates the 4 orphan tables on fresh DBs, and removing it before the migrations exist would break local dev / CI fixtures.

**Verification:**
- After Sprint 738 lands, `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS` are both empty in `test_alembic_models_parity.py`.
- Test still passes (full parity now enforced).
- Production deploy logs after the migrations run show the relevant `op.create_table` / `op.add_column` log lines (or `already exists, skipping` for outcome (1) cases).

---

### Sprint 739: Remove orphaned `bulk_upload_cleanup` job (post-Sprint-720 dead code)
**Status:** COMPLETE 2026-04-28. Deleted `_job_bulk_upload_cleanup` (~22 lines) + its scheduler registration (~7 lines) from `backend/cleanup_scheduler.py`. 29/29 cleanup_scheduler tests passing post-deletion. Production verification post-deploy: `Bulk upload cleanup failed: ImportError` log pattern should drop to zero firings.
**Priority:** P3 (production noise; not customer-facing). Surfaced during Sprint 732 Step 2c log analysis 2026-04-28.
**Source:** Sprint 720's `bulk_job_store` refactor removed `_evict_stale_jobs` from `routes/bulk_upload.py` (the new store handles eviction internally — `routes/bulk_upload.py:74` comment: *"bulk_job_store handles eviction itself (Redis TTL or in-memory LRU+age cap); no explicit _evict_stale_jobs call needed"*). The cleanup_scheduler call site at `cleanup_scheduler.py:403` was orphaned with `from routes.bulk_upload import _evict_stale_jobs`, raising `ImportError` on every scheduled run since Sprint 720's deploy. Render logs confirm firings going back at least 11:54 UTC 2026-04-28 today (and through Sprint 732 Step 2c's window).

**What landed:**
- Deleted `_job_bulk_upload_cleanup` function from `backend/cleanup_scheduler.py:390-411`.
- Removed scheduler registration block at `cleanup_scheduler.py:636-642` (the `_scheduler.add_job(_job_bulk_upload_cleanup, ...)` entry).
- Net: ~30 lines removed; no replacement needed (per Sprint 720's own design).

**Why it took 8 sprints to surface:** the failure log message starts with "Bulk upload cleanup failed", not "Cleanup job failed" — Sprint 732's investigation queries filtered for the latter. Sprint 732 Step 2c's broader cleanup_scheduler-logger query caught it.

**Out of scope:**
- No regression test added — the absence of the schedule registration *is* the test. Adding `_scheduler.add_job(_job_bulk_upload_cleanup, ...)` back would fail because the function doesn't exist.

**Verification:**
- 29/29 `test_cleanup_scheduler.py` tests passing.
- Production deploy after Sprint 739 lands: zero `Bulk upload cleanup failed` log entries on the next 30-min cycle window.

---

### Sprint 740: rollback before lock release in `_run_cleanup_job` (Sprint 732 Step 3 fix)
**Status:** COMPLETE 2026-04-28. 3-line fix added to `_run_cleanup_job` + 1 new contract test pinning the rollback-ordering invariant. 30/30 cleanup_scheduler tests passing locally. Ships the structural fix Sprint 732 Step 3 was waiting on.
**Priority:** P2 (cleanup-scheduler is failing every ~60 min in production with masked-symptom 25P02; Sprint 740 unmasks the real root cause for the next investigation sprint).
**Source:** Sprint 732 Step 2c (2026-04-28 16:08 UTC) identified the leaf class as `psycopg2.errors.InFailedSqlTransaction` (SQLSTATE 25P02). Investigation revealed this was a cascade symptom — the cleanup_func body fails first (real root, masked), session enters aborted state, `with_scheduler_lock`'s finally executes `DELETE FROM scheduler_locks` on the same aborted session, that DELETE fails with 25P02, and the 25P02 propagates out as the visible exception.

**The fix:** wrap `cleanup_func(db)` in a try/except inside the `with with_scheduler_lock(...)` block. On any exception, call `db.rollback()` BEFORE re-raising. The lock-release DELETE in `with_scheduler_lock`'s finally then runs on a clean session, the DELETE succeeds, and the original `cleanup_func` exception class propagates out unmasked.

**Side benefit beyond stability:** Sprint 732 step 2b's leaf-class observability fields (`error_orig_fqn`, `error_cause_fqn`, `error_orig_pgcode`) now capture the ACTUAL root psycopg2 class instead of the cascade symptom. Sprint 740's first post-deploy cleanup cycle will reveal what's truly failing inside the cleanup_func body — the data Sprint 732 was originally chasing.

**What landed:**
- `backend/cleanup_scheduler.py::_run_cleanup_job` — inner try/except around `cleanup_func(db)` invocation; rollback-then-raise on exception. ~10 lines added (mostly comment explaining the cascade and why this ordering matters).
- `backend/tests/test_cleanup_scheduler.py::test_session_rollback_runs_before_lock_release_on_cleanup_failure` — new contract test mocks the session and asserts the FIRST rollback call's index < the DELETE FROM scheduler_locks call's index. A regression that moves rollback after the lock release fails this test loudly.
- Existing `test_session_rollback_before_close_on_failure` updated: it asserted `rollback.assert_called_once()`; Sprint 740 makes rollback called twice (Sprint 740's inner + Sprint 711's outer-finally). Test now asserts `call_count >= 1` — the original "rollback before close" semantic intent is preserved.

**Verification:**
- 30/30 cleanup_scheduler tests passing locally.
- Post-Sprint-740 production deploy + 1h: pull `error_orig_fqn` from the next cleanup cycle's failure log. Expected: a non-cascade psycopg2 class (likely `psycopg2.errors.SerializationFailure`, `psycopg2.OperationalError` with pgcode `08006` matching Sentry's SSLEOFError signal, or something genuinely surprising). That class names the real root for **Sprint 741** — the actual structural fix to the cleanup_func body's failing statement.

**Out of scope:**
- The actual root-cause fix for whatever cleanup_func is doing wrong — that's Sprint 741, contingent on Sprint 740's first post-deploy log read.
- Approach 2 from the close-out doc (separate session for lock vs cleanup) — not adopted; Approach 1 (inner rollback) is sufficient and 1/3 the diff.

---

