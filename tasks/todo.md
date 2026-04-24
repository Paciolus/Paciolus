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

## Active Phase
> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). **Recommended path: ship on ~3-week ETA** with two engineering amendments — Sprint 673 below removes the 2026-05-09 TLS-override fuse before it collides with launch week, and Guardian's 5-item production-behavior checklist runs in parallel with Phase 3/4.1 (tracked in [`ceo-actions.md`](ceo-actions.md) "This Week's Action Map"). Full verdict tradeoff map in conversation transcript.
> **Prior sprint detail:** All pre-Sprint-673 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers.
> **CEO remediation brief 2026-04-15** — Sprints 665–671 cleared the blocking TB-intake issues from the six-file test sweep. Sprints 668–671 remaining pending items archived alongside — no longer blocking launch.
> Sprints 673–677 archived to `tasks/archive/sprints-673-677-details.md`.
> Sprint 611 + Sprints 677–714 archived 2026-04-24 to `tasks/archive/sprints-611-714-details.md` (eight post-Sprint-673 batches: Post-Audit Remediation, Anomaly Framework Hardening, Security Hardening Follow-Ups, Design Refresh, Production Bug Triage, Nightly Agent Remediation, Branding Coverage Completion, P2 Sentry Sweep). Only Sprint 715 remains pending.

### Sprint 715: SendGrid 403 root-cause investigation (24h post-deploy watch)
**Status:** PENDING — investigable starting **2026-04-25 ~14:29 UTC** (24h after Sprint 713 merge `2b92b771` on 2026-04-24 14:29 UTC).
**Priority:** P2 (observability follow-up — no user-facing impact, but worth knowing which recipient/path triggers the 403)
**Source:** Sprint 713 Bug C review — the fix caught the exception but did not investigate the root cause. The 403 means SendGrid is refusing a specific send; until we know *why*, users on the affected path silently never receive their email.

**Why pending (not "now"):** Sprint 713's warn-path (`log_secure_operation("email_error", f"SendGrid HTTPError status=403")`) is what makes the root cause investigable. We need 24h of production traffic with the new logs in place to see *which* send triggers the 403 and *how often*. Pre-deploy, we'd be guessing.

**Plan when triggered (CEO signal: if warn log count > 0 after 24h):**
- Pull Render logs for `"SendGrid HTTPError status=403"` over the post-deploy window. Identify the sender function (verification / password-reset / contact / email-change) and recipient masking pattern.
- Check SendGrid Dashboard → Suppressions → Blocks / Bounces / Spam Reports for the 403 recipients. Most likely cause: addresses on the global bounce list from the pre-Domain-Authentication era (SendGrid carried the `@gmail.com` bounce history into the paciolus.com domain).
- Check SendGrid API key scope on the Paciolus production key — `Mail Send: Full Access` is required; a read-only or Marketing-scoped key would 403 on transactional sends.
- Fix depends on finding: suppression-list cleanup (one-time; then add a `/admin/email-suppressions` endpoint to view current state), API key re-scope, or sender-domain re-verification.

**Out of scope:**
- Proactive suppression-list sync (would need a scheduled cron polling SendGrid API; not worth the infrastructure until we see meaningful 403 volume).
- Email deliverability SLA tracking (a separate observability sprint if Sentry breadcrumbs aren't sufficient).

---

### Sprint 716: Observability — Grafana Loki log aggregation (free tier)
**Status:** IN PROGRESS — Grafana Cloud provisioning + app-side handler landed 2026-04-24. Remaining: CEO sets 3 Render env vars (`LOKI_URL`, `LOKI_USER`, `LOKI_TOKEN`), post-restart ingest verification, and six saved queries authored in Grafana Logs Explorer. Runbook live at `docs/runbooks/observability-loki.md`.
**Priority:** P3 (operational quality-of-life; additive to Sentry; not launch-blocking)
**Source:** Executive Blocker Sprint 463 reclassified 2026-04-24 — CEO directive 2026-04-24 to schedule any deferred items that are free. Reframed from "SOC 2 SIEM" to "free-tier production log search" — same engineering, different framing. The remaining SOC 2 deferrals (464 pgBackRest, 466 Secrets Manager, 467 pen test, 468 paid bounty, 469 SOC 2 auditor) all incur cost and stay deferred.

**Why this matters now:** Render's log tail is live-only with no search, no filters, no retention, and no saved-query workflow. Sentry catches exceptions but misses quiet anomalies (elevated 4xx rates, scheduler delays, slow audit endpoints). Phase 3 functional validation will surface bugs that are easier to triage with searchable historical logs than with `grep` over a tail buffer.

**Integration approach — revised 2026-04-24 mid-provisioning:** Render's native Log Streams integration expects TCP/syslog destinations (Papertrail/Datadog/Logtail pattern). Grafana Cloud Loki only accepts HTTPS push at `/loki/api/v1/push`. Rather than introduce a protocol-bridging sidecar (Alloy/Cribl) that adds infra, we ship an in-process Python handler on FastAPI that pushes to Loki HTTPS directly. Logs continue to flow to Render stdout exactly as today — this is purely additive.

**Plan when implemented:**
- Add `python-logging-loki` (or equivalent thin handler — pick the maintained one at implementation time) to `backend/requirements.txt`.
- Extend `backend/logging_setup.py` with a `LokiHandler` attached alongside the existing stdout handler. Wire it behind a config flag so the app still runs locally with no Loki config. Labels: `service="paciolus-api"`, `env=ENV_MODE`, `logger=<record.name>`, `level=<record.levelname>`. Batch push (default ~1 s flush) to avoid per-log HTTPS overhead.
- Three new env vars on Render `paciolus-api` (CEO action):
  - `LOKI_URL=https://logs-prod-042.grafana.net/loki/api/v1/push`
  - `LOKI_USER=1566612`
  - `LOKI_TOKEN=<glc_… token from password manager>`
- Add 6 saved queries under a "Paciolus Production" Grafana folder:
  1. Auth failures (`{service="paciolus-api"} |~ "status=(401|403)" |~ "path=/auth/"`)
  2. 5xx errors (`{service="paciolus-api"} |~ "status=5\\d\\d"`)
  3. Slow requests (`{service="paciolus-api"} | json | duration_ms > 5000`)
  4. Scheduler errors (`{service="paciolus-api", logger="cleanup_scheduler", level="ERROR"}`)
  5. SendGrid HTTPError 403 (folds into Sprint 715 investigation — gives us the recipient/path histogram immediately rather than 24h after the fact)
  6. Audit-engine warnings (`{service="paciolus-api", logger="audit_engine", level="WARNING"}`)
- Add `docs/05-runbooks/observability-loki.md` documenting: handler config, env var set, saved queries with copy-paste LogQL, current free-tier limits (verify at implementation time — Grafana Cloud Free is roughly 50 GB ingest / 14-day retention as of last check, may have changed), escalation path if limits are hit (downgrade volume by tightening log levels, or upgrade to Pro at ~$0.50/GB ingested).
- Verification: deploy, tail Render logs to confirm no regression, open Grafana Logs explorer to confirm ingest, run each saved query against real traffic.

**Out of scope:**
- Custom dashboards (saved queries only — promote a query to a dashboard panel if it gets reused enough to warrant)
- Alerting rules (separate sprint if Sentry alerts prove insufficient)
- Bridging Render's native Log Streams to Loki via sidecar — not worth the moving part for Phase 3
- pgBackRest (Sprint 464), Secrets Manager (Sprint 466), or any cost-bearing observability work — still deferred per CEO directive 2026-04-24
- Replacing Sentry — strictly additive

---
