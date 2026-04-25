# Sprints 716–720 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-25.

---

### Sprint 716: Observability — Grafana Loki log aggregation (free tier)
**Status:** COMPLETE 2026-04-24 — PR #103 merged as `6802bd63`, Render auto-deploy brought the in-process handler live at 12:51 UTC. Grafana Logs Explorer confirmed 40 initial log lines flowing with `service=paciolus-api`, `env=production` labels. All 6 saved queries authored under `paciolus.grafana.net` Explore. Runbook live at `docs/runbooks/observability-loki.md`. CI fix `24ae9fcf` was squashed into the same PR (pip-audit ignore for unpatched CVE-2026-3219 — revisit 2026-05-22).
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

### Sprint 717: Catalog & Citation Single-Source-of-Truth
**Status:** COMPLETE 2026-04-24 — commit `35c9e709`. `backend/tools_registry.py` + `backend/standards_registry.py` are the canonical sources; frontend ledger expanded 12 → 18; AS 1215 mis-citations corrected on 5 customer-facing surfaces; PR-T12/T13 backfilled in payroll memo; CI tests `test_catalog_consistency.py` (42 cases) + `test_citation_consistency.py` (4 cases) green on first cross-check (caught 4 unregistered standards — ASC 842, IFRS 16, ASC 326, IAS 1 — and added them). Backend pytest 5,478 passed (+50 new from this sprint), frontend Jest 1,915 passed, `npm run build` clean.


---

### Sprint 720: Multi-Worker State Discipline (Bulk Upload)
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 4, the production-bug fix.
**Priority:** P0 (CEO blocked from running Phase 3 bulk-upload step until this lands)
**Source:** 8-agent sweep 2026-04-24. Guardian audit #1.4 — `_bulk_jobs` in `routes/bulk_upload.py:37` was a process-local `OrderedDict`; POST hits Worker A, status poll hits Worker B → 404.

**Problem class:** Mutable state in route modules is per-worker, per-process, and lost on deploy. Bulk upload was the symptom; the bug class is "in-process state in a request handler under multi-worker." Sprint 720 closes the symptom AND makes the bug class mechanically uncatchable going forward.

**Scope landed:**
- [x] `backend/shared/bulk_job_store.py` — Redis-backed shared store (mirrors `ip_failure_tracker.py` and `impersonation_revocation.py` pattern). `put` / `get` / `delete` / `reset_all_for_tests`. Job state serialized as JSON per Redis key with TTL = 2h. In-memory fallback for local dev / single-worker.
- [x] `backend/routes/bulk_upload.py` — `_bulk_jobs` OrderedDict + `_evict_stale_jobs` removed. All state reads/writes go through `bulk_job_store`. Route docstring documents the cross-worker semantics + the remaining single-worker affinity for processing tasks.
- [x] CI test `tests/test_no_module_global_state_in_routes.py` — AST scan over all 59 route files. Module-level mutable containers (dict/list/set literals + factory calls) are forbidden unless: (a) the name is SCREAMING_SNAKE_CASE constant, or (b) an inline `# allow-module-mutable: <reason>` comment is present.
- [x] All 66 existing bulk-upload-API tests pass without changes (the public API is identical).

**Recurrence prevention (the durable artifact):**
1. **`shared/bulk_job_store.py` is the third instance of the Redis-with-fallback pattern** (after `ip_failure_tracker.py` Sprint 718 and `impersonation_revocation.py` Sprint 590). The pattern is now load-bearing — any future cross-worker counter / cache should follow it.
2. **AST lint rule scoped to `backend/routes/`** — every route file is parametrically scanned. A future PR that re-introduces `_bulk_jobs = OrderedDict()` (or any equivalent) fails CI at PR time.
3. **Same prevention shape Sprint 718 used for `auth.py` + `security_middleware.py`** — module-level mutable state is now mechanically forbidden in two of the highest-blast-radius directories.

**Out of scope (deferred):**
- True queue-driven processing (Celery / RQ / custom Redis queue). Processing tasks still have single-worker affinity via `asyncio.create_task`; cross-worker visibility is on the *status-poll* side, which is where the bug manifested. Defer the queue work until Enterprise volume warrants the infra.
- Multi-worker live integration test (would need spinning up 2 FastAPI app instances + shared Postgres in a CI fixture). The lint rule + the cross-worker storage pattern + the existing 66-case API test are sufficient guardrails for now.

**Validation:**
- 66/66 existing bulk-upload-API tests pass (no public-API changes)
- 60/60 routes scanned by lint rule (59 route files + scan-existence smoke check), all clean
- 224/224 Sprint 717–720 surface tests pass

**Lesson tie-in:** Continues the Sprint 718 "AST guardrail for easy-to-reintroduce bugs" pattern. Pre-Sprint-720 a developer could re-introduce `_some_cache: dict = {}` in any route file. Post-Sprint-720 that fails CI in `tests/test_no_module_global_state_in_routes.py` until they either move it to a shared store or document the local-only scope.


---

### Sprint 719: Stripe Live-Mode Webhook Resilience
**Status:** COMPLETE 2026-04-24 — agent-sweep wave 3, the pre-cutover Stripe fixes.
**Priority:** P0 (real-money traffic about to fly through this code path)
**Source:** 8-agent sweep 2026-04-24. Guardian audit findings 1.5 (silent webhook secret mismatch) and 1.6 (off-by-one in stale-event guard).

**Problem class:** Stripe live-mode misconfiguration is silent — a test-mode webhook secret pasted into the live env var rejects every event with 400. Customers don't appear in the admin dashboard, dispute events miss SLA, churn doesn't downgrade. Companion problem: equal-second event timestamps bypass the stale-event guard at `webhook_handler.py:978` due to a `<` instead of `<=`.

**Scope landed:**
- [x] Off-by-one fix at `backend/billing/webhook_handler.py:978` — `event_time < sub_updated` → `event_time <= sub_updated`. Equal-second events are now skipped as stale (they are overwhelmingly Stripe redeliveries of an event we already processed).
- [x] Production startup format guard — `_stripe_secret_format_violations` pure function in `backend/config.py` checks for `sk_test_*`, `pk_test_*`, `_test_` patterns when `ENV_MODE=production`. Hard-fails at boot with actionable error messages.
- [x] CI test `tests/test_webhook_event_ordering.py` — proves equal/older/newer events are handled correctly.
- [x] CI test `tests/test_stripe_secret_format_guard.py` — exercises the format-check function across production/dev/staging modes and live/test secret patterns. 11 cases.
- [x] `scripts/stripe_live_preflight.sh` — pre-cutover runner that fires every WEBHOOK_HANDLERS event type via Stripe CLI and bails on the first non-200. Now a mandatory step in `tasks/ceo-actions.md` Phase 4.1.

**Recurrence prevention (the durable artifact):**
1. **Pure-function format check** — `_stripe_secret_format_violations` is unit-testable without spinning up the full config module. Same shape reusable for any future env-var format guard (sentry DSN, sendgrid key, etc.).
2. **Equal-time fixture** — `test_equal_time_event_is_skipped` is the regression test for the off-by-one. Any future "let's relax the staleness guard" change will need to flip this expected behavior.
3. **Phase 4.1 checklist gate** — preflight runner is now a checklist requirement, not optional. The script's exit code is the gate, not engineering judgment.
4. **Startup hard-fail** — misconfiguration is blocked at boot, not surfaced 24h later when the first dispute event fires.

**Out of scope (deferred):**
- Webhook handler coverage to ≥80% (currently 57.4%). Sprint 723's explicit charter is per-file coverage floors with `coverage_floors.yaml`; that sprint will own this.
- Sentry alert on "Webhook signature verification failed" + 24h 4xx-rate alert. Sprint 730 (Operational Observability Polish) owns alerting; the format guard makes this less urgent because misconfig now hard-fails at boot.

**Validation:**
- 14/14 new tests pass (3 event-ordering + 11 secret-format)
- Existing webhook tests unchanged

**Lesson tie-in:** Continues the Sprint 718 "two-form parity" pattern — equal-time is the third surface form alongside older and newer. Same pattern applied as a parametrized event-time test.


---

### Sprint 718: Auth Surface Hardening + Cookie/Bearer Parity
**Status:** COMPLETE 2026-04-24 — agent-sweep wave 2, the pre-Stripe-cutover auth fixes.
**Priority:** P0 (single High-severity finding from 2026-04-24 security review; blocks Stripe cutover credibility)
**Source:** 8-agent sweep 2026-04-24. Security Review H-01/M-02/M-03 + Guardian admin-unlock gap.

**Problem class:** Auth helpers were written assuming Bearer-token clients (CLI/test) and never updated when production browser path moved to HttpOnly cookies. The mismatch silently degrades CSRF user-binding. Companion problem: per-IP throttle was a process-local dict — per-worker, lost on deploy. Sprint 718 closes both bug classes with parity-test infrastructure and shared Redis-backed storage.

**Scope landed:**
- [x] `_extract_user_id_from_auth` at `security_middleware.py:485` reads ACCESS_COOKIE_NAME cookie when no Bearer header present (H-01 fix). Same precedence as `auth.resolve_access_token`.
- [x] Per-IP failure tracker migrated from process-local `_ip_failure_tracker` dict to `shared/ip_failure_tracker.py` — Redis backend with in-memory fallback (M-03 fix). Public API (`record_ip_failure`, `check_ip_blocked`, `reset_ip_failures`) preserved for call-site stability.
- [x] `routes/export_sharing.py:471` GET endpoint now returns 404 for passcode-protected shares (was 403 with "passcode required") — closes the existence-leak / token-enumeration vector (M-02 fix).
- [x] Admin lockout-recovery endpoint `POST /internal/admin/security/clear-throttle` — superadmin-only, audit-logged, rate-limited 1/min, supports per-IP and reset-all modes (Guardian admin-unlock gap).
- [x] CI test `tests/test_auth_parity.py` (8 cases) — parametrizes Bearer + cookie inputs through every auth-extracting helper, asserts equivalence. The durable guardrail against the H-01 class.
- [x] CI test `tests/test_no_process_local_auth_state.py` (2 cases) — AST-scan that fails if any module-level mutable container is added to `auth.py` or `security_middleware.py`. Constants in SCREAMING_SNAKE_CASE exempt.
- [x] Existing test files updated: `test_security.py` (53 passed), `test_export_sharing_routes.py` (404 expectation), `test_export_sharing_ip_throttle.py` (6 cases reworked to use shared module).

**Recurrence prevention (the durable artifact):**
1. **Parity test pattern** — `test_auth_parity.py` parametrizes over `(bearer, cookie)` inputs. Adding a new auth-extracting helper without the symmetric path will fail the test.
2. **AST guardrail** — module-level mutable state in auth modules is mechanically forbidden. Pattern reusable for Sprint 720's `routes/` lint.
3. **Shared store pattern** — `shared/ip_failure_tracker.py` is the template for any cross-worker counter (mirrors `shared/impersonation_revocation.py`). Sprint 720 will follow same shape for bulk-upload state.
4. **Sentinel for the H-01 class** — the cookie-path test would have caught the original bug; same shape catches the next variant.

**Validation:**
- 256/256 impacted backend tests pass (all of Sprint 717 + Sprint 718 surface)
- Full backend pytest sweep exit code 0 (Windows-only atexit tmpdir cleanup quirk; not a test failure)
- Frontend Jest 1,915/1,915 (no frontend changes in this sprint)

**Lesson captured:** "Two-form code paths need parity tests, not just a one-form test."


---

