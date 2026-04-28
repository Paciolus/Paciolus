# QualityGuardian Audit — Phase 3 Validation + Stripe Cutover Failure-Mode Analysis

**Date:** 2026-04-24
**Persona:** QualityGuardian (Failure-Mode Analyst)
**Audit scope:** (1) Phase 3 walkthrough risk, (2) Stripe live cutover, (3) prod-only failure modes not in test suite, (4) coverage blind spots in 10 weakest files.
**Posture:** Pessimistic about first versions. Anything that can break, will break under production load on a real CEO clicking through 18 memos plus a real-money Stripe charge.

Test baseline: 8095 backend + 1915 frontend tests, 92.89% backend line coverage.

---

## 1. Phase 3 walkthrough risk surface

### 1.1 Back-to-back generation of 18 memo PDFs + 3 report PDFs on a single engagement

- **Failure Mode:** Memory pressure on Render Standard (2 GB RAM single worker). `ReportLab` + `openpyxl` + `pdfminer` are all cumulative — each PDF build holds Story objects, embedded fonts, images (logo via `find_logo`), and rendered table styles in RAM until `doc.build()` flushes. Generating 21 PDFs back-to-back without a yield/restart cycle can OOM-kill the worker mid-engagement, causing a 502 on memo #15 with no clean rollback. Compounded by `excel_generator.py` using openpyxl Workbook objects (45.7% covered) and `leadsheet_generator.py` instantiating fresh NamedStyles every call (11.4% covered). NamedStyle name collisions raise `ValueError` (silently caught — but other workbook operations on the same in-process module may share state in cached `_register_styles()`).
- **Test Scenario Checklist:**
  1. Loadtest: trigger all 18 memo endpoints + 3 report endpoints sequentially against a single `engagement_id`, with TB containing 2,000+ rows. Watch RSS in `/health/metrics` for monotonic growth across the run; assert worker doesn't restart.
  2. Concurrent test: 2 users on same instance each running 5 memos in parallel (Enterprise CEO + impersonator). Confirm slowapi rate limit isn't exceeded but assert no 502/503.
  3. NamedStyle pollution: render Lead Sheets twice in the same worker — second call must not raise on `add_named_style` collisions.
- **Defense Strategy:** Add an explicit `gc.collect()` between memo generations in `routes/export_memos.py` after each PDF write. Move PDF generation to a streaming generator (yield bytes chunks) where `reportlab` allows. Set Render `maxRequestsPerWorker` recycling so a worker handling 21 memos is recycled cleanly. Add a per-request RSS log via `resource.getrusage()` so Phase 3 surfaces the memory curve.
- **Severity:** **High** (CEO will hit this and it looks worse than it is).
- **Fix-before-launch?:** **Yes** — at minimum the gc.collect + worker-recycle config.

### 1.2 Bulk upload (Enterprise tier) — in-memory job store, single-worker assumption

- **Failure Mode:** `backend/routes/bulk_upload.py:37` defines `_bulk_jobs: OrderedDict[str, dict]` as a **module-global, per-worker** structure. Render Standard runs gunicorn with multiple workers on a single instance. CEO uploads 5 TBs → request hits Worker A, which spawns `asyncio.create_task(_process_bulk_files(...))`. CEO polls `GET /upload/bulk/{job_id}/status` → request hits Worker B → 404 "Job not found." Worse: if Render scales horizontally or recycles the worker mid-job, the job dict is dropped and the in-flight asyncio task disappears with it. Also: `asyncio.create_task` in a request scope is **not** awaited — if the event loop closes (graceful shutdown during deploy), the bulk task is silently abandoned, files marked "processing" forever, upload counter potentially under-incremented.
- **Test Scenario Checklist:**
  1. Two-worker integration test: start uvicorn with `--workers 2`, POST a bulk job, then poll `/status` 10x. Assert ≥1 of the 10 polls returns 404 (proves the bug exists today) — then fix and assert all 10 return 200.
  2. Worker-restart test: start a job, send SIGHUP to the worker mid-processing, confirm job state is recoverable or surfaces an explicit "lost" error rather than perpetual "processing".
  3. Quota test: queue 5 files, kill the worker before any complete; assert `increment_upload_count` was either fully applied or fully rolled back (no half-counted quota).
- **Defense Strategy:** Move bulk job state to Postgres (it's an Enterprise feature — durability is expected). Use a `BulkUploadJob` model with `(job_id, user_id, status, file_descriptors_jsonb)`. Replace `asyncio.create_task` with a proper background-task pattern (Celery / RQ / Render cron worker) or persist progress to DB on each file completion so any worker can serve `/status`. Until that's done, document Phase 3 limitation: bulk upload only stable on single-worker Render Standard.
- **Severity:** **Critical** for Enterprise UX, **Medium** for launch-blocking (Enterprise tier launches with 0 customers).
- **Fix-before-launch?:** **Yes** if any Enterprise customer signs up Day 1; otherwise document as known limitation and gate behind a feature flag.

### 1.3 Engagement layer end-to-end — completion gate edge cases

- **Failure Mode:** Completion gate logic (`engagement_manager.py`) checks open follow-up items + materiality + workpaper completion before marking complete. Edge cases: (a) follow-up item soft-deleted while completion-gate query is in flight (no row lock — race window), (b) materiality cascade re-run mid-engagement changes thresholds and previously "passed" tools now fail their threshold but the gate has already been crossed, (c) workpaper index built before final TB upload — completion gate references stale TB metadata.
- **Test Scenario Checklist:**
  1. Open follow-up item, start the completion-gate request, soft-delete the item before the gate query commits — assert gate output reflects pre-delete state OR re-queries.
  2. Run completion gate with materiality cascade modified between two gate calls; assert the second call recomputes thresholds rather than serving cached state.
  3. Diagnostic package ZIP — bulk-export with one tool's results stale (TB re-uploaded after tool ran). Assert ZIP includes a "stale data" disclaimer banner per CLAUDE.md guardrails.
- **Defense Strategy:** Wrap the completion-gate query in a serializable transaction. Add a `last_tb_uploaded_at` watermark — any tool whose `created_at` < watermark must be flagged as stale in the diagnostic package ZIP.
- **Severity:** **Medium**.
- **Fix-before-launch?:** No (CEO can rebuild engagement if it trips). Track for Sprint 718.

### 1.4 Export sharing — passcode brute-force lockout & R2 connectivity

- **Failure Mode 1:** **Self-DoS lockout** — CEO testing a passcode share types it wrong twice fat-fingered → 5+ failures escalate to 60s-per-failure lockout per-token, then per-IP throttle compounds (`security_middleware.check_ip_blocked` returns 429 with 15-min Retry-After). CEO can't unlock without Postgres surgery on `passcode_locked_until` column. There is no admin "unlock share" endpoint.
- **Failure Mode 2:** **R2 outage during share creation** — `export_share_storage.upload()` raises → 503. But what if R2 GET fails AFTER share creation succeeded? `_resolve_export_bytes()` returns 410 "no longer available" — correct, but logs only `share_id`, not enough to alert on a regional R2 outage vs a single missing object.
- **Failure Mode 3:** **Stale R2 client cache** — `_get_client()` caches `_s3_client` and `_configured` as module globals. If R2 credentials are rotated mid-flight (incident response), workers hold the old client until restart. `_reset_for_tests()` exists but isn't exposed via admin/health.
- **Test Scenario Checklist:**
  1. Submit 12 wrong passcodes from one IP across 3 different shares; assert per-IP `check_ip_blocked` triggers, then assert (manual) admin unlock path exists.
  2. Mock R2 download to return None for a valid `object_key`; assert 410 returned with structured log including `bucket`, `key`, and a Sentry tag for grouping.
  3. Rotate `R2_EXPORTS_SECRET_ACCESS_KEY`, hit a share without restart — confirm whether stale client errors out cleanly.
- **Defense Strategy:** Add a CEO-only `POST /admin/share/{id}/unlock` clearing `passcode_locked_until`. Add a healthcheck endpoint `/health/r2` that runs a GET on a sentinel object so monitoring catches R2 regional outages before users do. Add `record_billing_event`-style telemetry on R2 5xx rate.
- **Severity:** **Medium** (passcode lockout self-DoS is annoying but recoverable via DB).
- **Fix-before-launch?:** Yes for the admin unlock endpoint; the rest can wait.

### 1.5 Admin dashboard — impersonation read-only enforcement

- **Failure Mode:** `ImpersonationMiddleware` is registered but its enforcement is method-based, not endpoint-aware. Any future endpoint that uses GET for a side-effect operation (e.g., `/diagnostic/run?recompute=1`) bypasses the read-only mute. Audit log writes during impersonation also need to record the actor pair (admin + impersonated_user) — if only the impersonated user is logged, an audit reviewer cannot tell who actually clicked.
- **Test Scenario Checklist:**
  1. As impersonator, attempt `POST /clients` (must 403), `DELETE /clients/{id}` (must 403), `GET /admin/audit-log` (must 200, with the actor pair fields populated on every row generated under the session).
  2. Negative test: impersonator hits a hypothetical GET-with-side-effect — confirm middleware doesn't accidentally bless it.
- **Defense Strategy:** Move impersonation read-only enforcement onto a route-decorator allowlist rather than method-based. Add explicit `actor_user_id` + `effective_user_id` columns in `ActivityLog`.
- **Severity:** **Medium** (compliance — affects audit-trail quality, not user-visible).
- **Fix-before-launch?:** No — verify Phase 3 walkthrough surfaces no such GET endpoints, then track.

---

## 2. Stripe live cutover failure modes

### 2.1 Webhook signature verification with the wrong secret

- **Failure Mode:** `STRIPE_WEBHOOK_SECRET` env var is per-environment. If CEO copies the **test** webhook secret into the live env vars (or vice versa), `stripe.Webhook.construct_event` raises `SignatureVerificationError` and returns 400. **Stripe will retry for 3 days with exponential backoff, but ALL events fail** — paid customers won't appear in the admin dashboard, trial conversions won't fire emails, churn events won't downgrade tiers. Worst: this is silent. The 400 looks like normal noise in logs.
- **Test Scenario Checklist:**
  1. Smoke test in Phase 4.1: configure live webhook, fire a test event from Stripe Dashboard ("Send test webhook"), assert backend returns **200**. If 400 → secret mismatch.
  2. Add a webhook-health metric: 24h rolling 4xx rate on `/billing/webhook` should alert at >5%.
  3. CI gate: assert `STRIPE_WEBHOOK_SECRET` starts with `whsec_` (live + test both use this prefix, but at least catches blanks).
- **Defense Strategy:** Add Sentry alert rule on `Webhook signature verification failed` log message. After Phase 4.1 cutover, manually fire a Stripe CLI test event and assert delivery before doing the real-money smoke test.
- **Severity:** **Critical**.
- **Fix-before-launch?:** **Yes — operational checklist item.** Add to Phase 4.1 step list.

### 2.2 Coupon stacking / promo code validation

- **Failure Mode:** `validate_promo_for_interval(promo_code, interval)` — `MONTHLY_20_3MO` is monthly-only, `ANNUAL_10_1YR` is annual-only. If validator allows the wrong combo, customer pays 80% of an annual plan on first invoice ($800 not $1000). Also: Stripe Customer Portal allows the customer to apply additional coupons themselves on invoice — does our local subscription state reflect this discount on the next invoice's billing event? `handle_invoice_paid` records `PAYMENT_RECOVERED` but doesn't capture amount discrepancies vs catalog price.
- **Test Scenario Checklist:**
  1. POST `/billing/create-checkout-session` with `tier=solo, interval=monthly, promo=ANNUAL_10_1YR`; assert 400.
  2. POST with `tier=enterprise, interval=annual, promo=MONTHLY_20_3MO`; assert 400.
  3. Reconciliation test: every `invoice.paid` event's `amount_paid` should be within 5% of the expected catalog price for that tier × interval (after announced discounts). Anything outside is a fraud or coupon-stacking signal — flag in `BillingEvent`.
- **Defense Strategy:** Already implemented at the validator. Add the reconciliation telemetry as a post-launch metric.
- **Severity:** **Medium** (revenue leak if validator has a hole, fraud signal if Customer Portal bypass exists).
- **Fix-before-launch?:** No — keep monitoring as post-launch metric.

### 2.3 Seat add-on proration races

- **Failure Mode:** `add_seats` / `remove_seats` calls Stripe with proration. If two API calls land within milliseconds (CEO double-clicking the "Add seat" button), Stripe processes both, each prorated against the previous state. Result: customer gets billed for the same seat twice. `idempotency_key` is set on `create_checkout_session` but I don't see one on the seat-mutation paths — verify in `subscription_manager.add_seats`.
- **Test Scenario Checklist:**
  1. Concurrent call: send two `POST /billing/add-seats` with `{seats: 1}` from same user with same idempotency key; assert second call is idempotent (returns same SubscriptionItem ID).
  2. UI test: button must disable on click and re-enable on response. (Frontend concern — confirm.)
  3. Webhook ordering test: `customer.subscription.updated` fires twice for back-to-back seat changes; out-of-order guard at `process_webhook_event` line 960 covers this — assert it triggers under the test.
- **Defense Strategy:** Audit `subscription_manager.add_seats` for an `idempotency_key` parameter on the Stripe call. Add UI debounce. Frontend "Add seat" button must be visibly disabled during the API round-trip.
- **Severity:** **High** (revenue + customer trust).
- **Fix-before-launch?:** **Yes** for idempotency key on the Stripe mutation; UI debounce is launch-week polish.

### 2.4 Customer Portal cancel-at-period-end race

- **Failure Mode:** Customer cancels via Customer Portal → `customer.subscription.updated` fires with `cancel_at_period_end=true`. Then `customer.subscription.deleted` fires when the period actually ends. Between those two events, the customer still has paid access. Concurrent `customer.subscription.updated` ordering bug: the existing guard at line 960 only kicks in if `event_created < sub.updated_at`. If two webhooks land in the same second (event_time == sub_updated), the guard does NOT fire (`<` not `<=`), and a stale "active" event can re-activate a CANCELED subscription. The handler at line 311 also checks `sub.status == CANCELED and new_status == active`, mitigating this — but a two-step (`canceled → past_due → active`) sequence escapes that guard.
- **Test Scenario Checklist:**
  1. Replay test: pre-load DB with a CANCELED subscription, then process a stale `customer.subscription.updated` event with `status=past_due` (older event_created) — assert no state change.
  2. Same-timestamp test: event_created == sub.updated_at exactly; assert event is rejected as stale (currently it isn't — boundary bug).
- **Defense Strategy:** Change `event_time < sub_updated` to `event_time <= sub_updated` at `routes/billing.py:978`. Document the intent: "We treat exactly-equal timestamps as stale because Stripe sub-second resolution is not guaranteed."
- **Severity:** **Medium** (rare race, recoverable).
- **Fix-before-launch?:** Yes — one-line fix.

---

## 3. Production-only failure modes not covered by tests

### 3.1 Redis (Upstash) intermittent disconnect under sustained load

- **Failure Mode:** `RATE_LIMIT_STRICT_MODE=true` in production. `get_storage_backend()` checks Redis at startup but doesn't probe again. If Upstash hiccups mid-day, slowapi's RedisStorage client will raise — what does slowapi do under exception? Most slowapi RedisStorage failures fail-OPEN (allow the request through), which is the OPPOSITE of fail-closed. A Redis blip during a brute-force window means the attacker has unlimited attempts.
- **Test Scenario Checklist:**
  1. Chaos test: kill Redis connectivity (block egress to Upstash) for 30s mid-load; assert either (a) all requests fail-closed with 503 from slowapi, or (b) the limiter has a documented degraded mode that still tracks counters in-memory per-process and doesn't allow unlimited.
  2. Health endpoint: `/health` should report Redis liveness so Render auto-restart fires on Redis loss.
- **Defense Strategy:** Add a Redis ping in `/health` (already present? verify). Document slowapi failure mode and accept it OR replace slowapi with a cap-then-fail-closed wrapper.
- **Severity:** **High** (security regression on Redis blip).
- **Fix-before-launch?:** No — verify `/health` covers Redis, then track for Sprint 718.

### 3.2 Neon pooler intermittent disconnect

- **Failure Mode:** Neon pooled endpoint occasionally drops connections in pgbouncer-style transaction-pooling mode. SQLAlchemy's connection pool retries via `pool_pre_ping=True` (verify in `database.py`). If this isn't set, requests get `OperationalError: server closed the connection` randomly. Webhook handlers especially — losing a webhook to a transient DB error returns 500, Stripe retries, but if our dedup row was also lost in rollback, we now process duplicate side effects.
- **Test Scenario Checklist:**
  1. Verify `database.py` engine has `pool_pre_ping=True` and `pool_recycle <= 300` for Neon (their pooler drops idle ~5 min).
  2. Inject a `OperationalError` mid-webhook in tests; assert (a) DB rollback runs, (b) `ProcessedWebhookEvent` is not committed, (c) a 500 is returned to Stripe (so it retries).
- **Defense Strategy:** Already mitigated by the dedup commit being atomic with the handler logic. Verify.
- **Severity:** **Medium**.
- **Fix-before-launch?:** No — verify `pool_pre_ping`, then track.

### 3.3 SendGrid outage during trial-ending email

- **Failure Mode:** `handle_subscription_trial_will_end` already wraps email in try/except (line 593) — so the webhook returns 200 even on email failure. **But:** the failure is logged as `WARNING`, not `ERROR`, so Sentry won't surface it. Customers get no 3-day warning, churn rate spikes silently. Sprint 715 tracks SendGrid 403 specifically.
- **Test Scenario Checklist:**
  1. Inject SendGrid 403; assert log emitted at ERROR level (not WARNING) so Sentry catches it.
  2. Add a metric `email_send_failures_total{template="trial_ending"}` to Prometheus.
- **Defense Strategy:** Upgrade the log level on email failure to ERROR. Add Prometheus counter. (Already partially tracked in Sprint 715.)
- **Severity:** **Medium**.
- **Fix-before-launch?:** No — Sprint 715 active.

### 3.4 Sentry outage — error visibility loss

- **Failure Mode:** Sentry SDK is best-effort, so an outage doesn't break the app. But if Sentry is down during the live-Stripe smoke test, a real bug appears with zero visibility. Sentry's own status page is the only canary.
- **Test Scenario Checklist:** N/A — accept as residual.
- **Defense Strategy:** Mirror critical errors to Loki (Sprint 716 deployed) so dual visibility exists. Confirm Loki ingest path is independent of Sentry.
- **Severity:** **Low** (Loki backstops it).
- **Fix-before-launch?:** No — Sprint 716 covers it.

### 3.5 R2 connectivity loss during export-share download

- **Failure Mode:** R2 GET fails, returns 410 "Shared export is no longer available." Customer thinks their export is permanently gone. There's no retry, no fallback to inline blob (correctly — the row has only `object_key` after Sprint 611 flip).
- **Test Scenario Checklist:**
  1. Inject 503 from boto3 GET; assert response is 503 (transient) NOT 410 (permanent), and customer can retry.
  2. Add a 1-attempt retry with 1s backoff on the GET path.
- **Defense Strategy:** Distinguish transient (5xx, timeout) from permanent (404 NoSuchKey) in `export_share_storage.download()`. Return None for permanent, raise for transient. Caller maps transient → 503, permanent → 410.
- **Severity:** **Medium**.
- **Fix-before-launch?:** Yes — small change, big UX win.

---

## 4. Coverage blind-spot analysis — top 10 weakest files

### 4.1 `excel_generator.py` (45.7%, 328 missing) — **High**

- **Failure mode:** Uncovered paths likely include error-recovery branches in workbook serialization (broken styles, openpyxl save errors on exotic Excel content). Exception handling around `Workbook.save(buffer)` may leak the buffer or partial-write a corrupt XLSX.
- **Test:** Generate an XLSX with 100k rows (TB at scale); assert no MemoryError and the file opens in Excel.
- **Defense:** Wrap save in try/except, ensure `buffer.close()` on failure, return 503 to user.
- **Fix-before-launch?:** No — current 6,188 backend tests have surfaced no Excel issues.

### 4.2 `billing/webhook_handler.py` (57.4%, 185 missing) — **Critical**

- **Failure mode:** Specific uncovered branches: dispute handlers, invoice.created analytics, the trial_will_end email try/except path (line 593 explicitly marked `# pragma: no cover`), the proration-detection branch at line 364 (`old_tier and old_tier != tier`), the `ValueError` catch at `_apply_dpa_from_metadata`. In live mode, dispute events WILL fire (chargeback fraud is real).
- **Test:** Replay a fixture for each: `charge.dispute.created` (won), `charge.dispute.created` (lost), `invoice.created` proration, `customer.subscription.updated` upgrade Solo→Professional, downgrade Pro→Solo.
- **Defense:** Add an integration test that loops through every WEBHOOK_HANDLERS entry with a representative event, asserts no unhandled exception. Targets 80%+ coverage of this file.
- **Fix-before-launch?:** **Yes** — at minimum, dispute handler smoke test before live keys.

### 4.3 `population_profile_memo.py` (39.7%, 170 missing) — **Medium**

- **Failure mode:** Uncovered = exception paths in PDF rendering. With realistic TBs that have Unicode account names or huge magnitude distributions, ReportLab Paragraph rendering can raise `LayoutError`. Lands as 500 on `/audit/population-profile/pdf`.
- **Test:** Render with a TB containing `™`, `é`, `中文`, and a 50k-row population.
- **Defense:** Wrap memo build in try/except → log and return 503.
- **Fix-before-launch?:** No — Phase 3 will catch if real.

### 4.4 `workbook_inspector.py` (18.6%, 136 missing) — **High**

- **Failure mode:** This is the FIRST file run on every uploaded xlsx/xls/ods. 18.6% coverage means parsing-error paths are largely untested. A malicious or malformed xlsx (XML bomb, ZIP slip, password-protected) hits this file first. `InvalidFileException` is imported but the catch path is uncovered. Phase 3 CEO uploads "real" client TBs — many will have weird formatting.
- **Test:** Upload (a) password-protected xlsx, (b) xlsx with circular references, (c) xlsx with 1M empty rows, (d) ods file masquerading as xlsx by extension.
- **Defense:** Already has `MaxBodySizeMiddleware` upstream. Add explicit `InvalidFileException` → 400 with message "File appears corrupted or password-protected."
- **Fix-before-launch?:** **Yes** — first-touch upload path; 18.6% is too low.

### 4.5 `pdf/sections/diagnostic.py` (64.9%, 134 missing) — **Medium**

- **Failure mode:** Uncovered branches likely include: missing-data placeholders, ratio-rendering with None values, framework-resolution edge cases (GAAP vs IFRS toggle).
- **Test:** Generate diagnostic PDF on a TB missing one ratio's required accounts.
- **Defense:** Already has framework resolution module. Verify all rendering paths handle None gracefully.
- **Fix-before-launch?:** No.

### 4.6 `leadsheet_generator.py` (11.4%, 124 missing) — **High**

- **Failure mode:** The lowest-covered file in the report set. Lead sheet Excel generation: `_register_styles` swallows ValueError on duplicate styles. If two requests share a process and both register the same NamedStyle, the SECOND call's exception is caught and styles are silently incomplete on the workbook → corrupt-looking Excel.
- **Test:** Call `LeadSheetGenerator(...)` twice in the same Python process; assert second workbook has all expected styles applied.
- **Defense:** Use a fresh openpyxl Workbook per request (already does), and rely on the per-Workbook style namespace rather than the swallowed exception. Refactor `_register_styles` to be idempotent, not exception-swallowing.
- **Fix-before-launch?:** **Yes** — 11.4% coverage on a customer-facing PDF/Excel artifact is unacceptable.

### 4.7 `config.py` (54.5%, 96 missing) — **Low** (boot-time only)

- **Failure mode:** Uncovered = startup-fail branches that run once and exit. They've been exercised by every CI run and by Render boot. Real risk: a NEW required var added without test coverage that hard-fails in prod when the env doesn't have it.
- **Test:** Add a unit test that imports `config` with each required var unset, asserts SystemExit.
- **Defense:** Already hard-fails. Acceptable to leave.
- **Fix-before-launch?:** No.

### 4.8 `main.py` (44.2%, 92 missing) — **Low** (lifespan only)

- **Failure mode:** Uncovered = lifespan startup branches (cleanup_scheduler, Stripe validation, RL backend probe). Same as config.py — these run once at boot. Real risk: rate-limit fail-closed branch (line 209-219) — if the misconfiguration is ever real, app refuses to start, which is intended behavior. Already exercised on every Render deploy.
- **Test:** Start app with REDIS_URL unreachable + RATE_LIMIT_STRICT_MODE=true; assert RuntimeError on lifespan start.
- **Defense:** Already implemented.
- **Fix-before-launch?:** No.

### 4.9 `preflight_engine.py` (84.1%, 79 missing) — **Low**

- **Failure mode:** Edge cases in column detection on non-English headers, weird CSV separators, mixed-sign accounts. Already 84% covered, well-exercised.
- **Test:** Upload TB with German headers ("Soll", "Haben"), Spanish ("Debe", "Haber").
- **Defense:** Acceptable as-is.
- **Fix-before-launch?:** No.

---

## Summary tables

### Top 5 fix-before-launch (Phase 3 + Phase 4.1 blockers)

| # | Issue | File / Path | Severity | Effort |
|---|---|---|---|---|
| 1 | Stripe webhook secret mismatch silent failure | `routes/billing.py` + Phase 4.1 checklist | Critical | 1 line + ops checklist |
| 2 | Bulk upload in-memory job state breaks on multi-worker | `routes/bulk_upload.py:37` | Critical (Enterprise) | 1 sprint to migrate to DB |
| 3 | Memo back-to-back memory pressure (gc + worker recycle) | `routes/export_memos.py` | High | 1 day |
| 4 | Webhook handler dispute / upgrade path coverage 57.4% | `billing/webhook_handler.py` | High | 1 day to add fixture replay |
| 5 | Workbook-inspector 18.6% coverage on upload-first path | `workbook_inspector.py` | High | 1 day |

### Top 3 post-launch monitoring gaps

| # | Gap | Mitigation |
|---|---|---|
| 1 | Redis (Upstash) blip → slowapi fail-OPEN, brute-force window | Add `/health` Redis ping + Sentry alert on RedisStorage error |
| 2 | Stripe webhook 4xx silent — wrong secret would brick all events | Add 24h rolling `4xx_rate{path=/billing/webhook}` alert at >5% |
| 3 | R2 regional outage → mass 410s look like permanent data loss | Add `/health/r2` sentinel GET + Sentry alert; distinguish 5xx vs 404 in `export_share_storage.download()` |

### Tensions surfaced

- **MarketScout speed vs Guardian rigor:** Phase 3 is days away. Top 5 fix-before-launch list is achievable in 3–4 days. Items 4 and 5 (coverage on webhook + workbook_inspector) compete with Phase 4.1 timeline. Recommend completing 1–3 hard, accepting 4–5 as Sprint 718 immediately post-launch.
- **Bulk upload (#2):** Conflicts with "all paid tiers get all 18 tools" promise. If launch ships with Enterprise feature broken on multi-worker scale, Enterprise tier is effectively defective from Day 1. **Defer Enterprise tier marketing** OR **fix bulk job state** are the two options.

---

*Prepared by: QualityGuardian persona, 2026-04-24. Steel-manned the originating Sprint 716 + Phase 3 plan (8095 tests + Loki + Sentry are strong foundations) before identifying defense gaps. No new sprint authored — output is risk register + test scenarios for IntegratorLead to triage with CEO.*
