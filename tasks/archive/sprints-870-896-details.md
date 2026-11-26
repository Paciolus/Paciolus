# Sprints 870–896 Details

> Archived from `tasks/todo.md` Active Phase on 2026-11-25.

---

### Sprint 879: Logs, saved records and caches match the data statement (DH-03..07)
**Status:** COMPLETE — 2026-11-16 on local branch `sprint-879-data-statement` (stacked on Sprint 878, which is
stacked on 872 → #331; not pushed). **Priority:** P0/P1 (freeze-exempt: security defects). **Source:** read-only review at
`ef5e567`. **Agents:** Guardian (lead), Executor, Critic.

**The statement:** uploaded files are processed in memory and not kept after analysis (up to 10 minutes in memory);
we save the account, client list, analysis summaries (totals, ratios, counts, flagged account names — never balances,
transaction rows or file contents) and anything the user enters in an engagement.

**CEO decisions (2026-11-16):** analysis no longer saves an account's actual balance into an expectation; the auditor
captures it with an explicit action. The preview cache stays in each worker's memory (no Redis/disk); on a miss at
analysis time the browser re-sends the file.

**879a — uploaded values reach the application logs (DH-03, Critical)**
- [x] Confirmed: the TB and file-tool rejection handlers logged the exception object (`%s`, `exc_info=True`); the OFX
      parser logged currency, account suffix, account type and date range; DEBUG logged the upload's filename
      (`upload_pipeline.validate_file_size`) and 422 inputs (`main.validation_exception_handler`); a PDF page failure
      logged the filename. `TracebackRedactionFilter` ran on two handlers, only in production, and
      `REDACT_LOG_TRACEBACKS=false` turned it off.
- [x] `logging_config.install_safe_log_records()` — a log-record factory (installed on import and by `setup_logging`):
      an exception object passed as the message or an argument becomes its type name; `exc_text` is pre-set to type +
      innermost frame, so no formatter renders the message or traceback. `exc_info` stays on the record for Sentry
      (its scrubber already blanks the message). The filter and the env opt-out are removed (Dockerfile, env docs).
- [x] Call sites: fixed event + type name only in both rejection handlers; OFX logs dialect + counts; no filename in
      the format-detection or PDF-page lines; the 422 debug line logs a count.
- [x] Tests: `test_sprint_879_log_redaction.py` — OFX (SGML) and QBO (XML) bank statements with marker account
      suffix/currency/type and filenames, a malformed OFX, an out-of-balance TB with marker cell and account name, parser
      errors quoting a marker on both rejection handlers, a 422 carrying a marker; through the real `setup_logging()` at
      INFO/DEBUG × production/development, with Loki's push and a Sentry transport captured (logging integration at
      DEBUG, stricter than production). No marker anywhere. Failed first with 6 markers leaking.
- Found, not fixed (out of scope): an out-of-balance TB returns a **500** — the `tb_out_of_balance` structural anomaly
  lacks six fields `TrialBalanceResponse.abnormal_balances` requires (`debit`, `credit`, `category`,
  `matched_keywords`, `requires_review`, `suggestions`). Needs its own sprint.

**Verification (879a):** full backend suite 10,822 passed / 1 skipped / 1 failed — the failure
(`test_cleanup_scheduler::test_failure_log_includes_traceback_exc_info`) caught the first version stripping `exc_info`,
which would have cost Sentry its stack frames; fixed (pre-set `exc_text` instead), and the logging/Sentry/Loki/cleanup
suites re-run green (103 passed). ruff clean; mypy 212 (gate 1,011), none in changed files.

**879b — analysis saves account balances into expectations (DH-04, Critical)**
- [x] Confirmed: `shared/expectation_evaluation.evaluate_expectations_against_measurements` called
      `update_expectation(result_actual_value=…)` for every match, committed in the analysis request — from
      `/audit/flux`, both multi-period routes, **and** `/clients/{id}/industry-ratios` (`routes/trends.py`, not in the
      review). No frontend screen read the result, so the save was silent.
- [x] `propose_expectation_actuals` reads only and returns `proposed_actuals` (replaces `expectations_evaluated`), each
      with a signed `capture_token` (HMAC over user, engagement, expectation, actual, source tool, run, 24 h expiry —
      `shared/expectation_capture.py`), so the saved value and its run cannot be substituted by the browser.
      `maybe_record_tool_run` now returns the run id.
- [x] `POST /engagements/{id}/analytical-expectations/capture-actuals` (workspace-gated, like every workspace write):
      one token or a whole run's; all verified before any save; an already-captured expectation is skipped, never
      overwritten. New columns `actual_source` / `actual_source_tool_run_id` / `actual_captured_at` /
      `actual_captured_by` (migration `e879b2d4a6c1`); a typed-in actual records `manual`; clearing clears them.
- [x] Memo: no actual → "not captured" in Actual and Variance; each row says where its actual came from. Expectations
      panel no longer shows `$0.00` for a missing actual. Multi-period page: `ProposedActualsPanel` — "Save actual value
      for <account>" and "Save all N actual values from this run".
- [x] Tests: `test_sprint_879_expectation_capture.py` (run + rerun save nothing; failed run saves nothing; capture one
      records the run; capture all; forged/other-user/Free refused; helper writes nothing; manual source; memo PDF text),
      `ProposedActualsPanel.test.tsx`; 728c tests converted; 878's workspace matrix now covers the capture route.
- Not changed: actuals auto-saved before this sprint stay, with a NULL source (indistinguishable from typed ones).
  The flux page does not send an engagement id, so flux proposals have no UI yet (API only).

**Verification (879b):** expectation/flux/multi-period/trends/memo/snapshot/parity/workspace suites 351 + 103 passed;
memo render snapshot re-recorded (analytical-expectations entries only: "—" → "not captured"); ruff clean; mypy 212;
frontend `tsc` + eslint clean, 4 suites / 32 tests.

**879c — the activity summary accepts any content (DH-05, Critical)**
- [x] Confirmed: `POST /activity/tool-log` took `summary` as a free 2,000-char query string and stored it verbatim;
      `_log_tool_activity` serialised any dict. Only `trial_balance` passes a summary internally
      (`was_balanced`, `anomaly_count`). **No frontend code calls `/activity/tool-log`** — no caller to update.
- [x] `shared/activity_summary.py`: one schema per tool (18 engagement tools + 4 diagnostics), approved scalar
      aggregates only (`extra="forbid"`, strict types, bounded counts, score 0–100); unknown tools, unknown/nested
      fields, lists and strings rejected; the error lists allowed fields and never echoes input. Used by the API
      (typed JSON body `ToolLogRequest`, query parameters gone) and the recorder (raises before writing). The feed
      drops any stored summary that fails it. Migration `f879c3e5b7d2` sets every failing stored summary to NULL (rows
      kept — less destructive than the permitted delete).
- [x] Tests: `test_sprint_879_activity_summary.py` — balances, transaction/payroll rows, file text, nested, key-as-value
      rejected at both entry points with nothing stored; valid round-trip through API and feed; query string ignored;
      no submitted value in logs at DEBUG; migration run against SQLite. 7 failed before the fix.
- [x] `scripts/openapi-snapshot.json` regenerated — covers 879b's fields too (879b's commit left it stale; the drift
      check is advisory in CI).

**Verification (879c):** activity/authorization/route-snapshot/parity suites 86 + 69 passed; OpenAPI drift clean;
ruff clean; mypy 212.

**879d — previewed files outlive 10 minutes (DH-07, High)**
- [x] Confirmed: `_evict_expired()` ran only inside `put()`; `get`/`take` expired only the token read; cap 100 entries,
      no byte limit; per-process cache × 4 Gunicorn workers.
- [x] `shared/preflight_cache.py`: a daemon sweeper per process (started by the first `put`, again after a fork) removes
      expired entries every 15 s, so a preview is gone within 10 min + 15 s with no other cache call; 256 MiB byte
      budget per process (oldest evicted; a file over the budget is not cached → no token); 2 previews per user
      (their oldest evicted). Owner binding and single use unchanged.
- [x] Logout and account deletion: `shared/preflight_purge.request_purge` drops the user's previews in the handling
      worker at once and writes `preview_purge_requests` (user id + time, migration `a879d4f6c8e3`); every other
      worker's sweeper applies it on its next tick (DB read only when that worker holds previews) and deletes requests
      older than the lifetime. Logout purges only after 872's CSRF-owner check has passed.
- [x] Miss path — **already handled, no new response**: the browser always sends the file with the token
      (`buildTrialBalanceFormData` appends `file`), and the route falls back to it on a miss. Pinned by a test.
- [x] Tests: `test_sprint_879_preview_cache.py` — abandoned preview swept with no cache calls (fake clock); fork starts a
      new sweeper; byte budget under six large previews; over-budget file not cached; per-user limit; wrong owner;
      single use; purge_owner; another worker's purge request; logout and deletion through the app; miss completes.
      11 of 12 failed before the fix (the miss test passes on the old code by design).
- Observation for the CEO: because the browser always re-sends the file, the cache saves a re-parse at most, never a
  re-upload. Removing it would retire DH-07 entirely; kept per the 2026-11-16 decision.

**Verification (879d):** preview-cache + preflight/preview/workbook/auth/erasure/CSRF/parity suites 12 + 191 passed;
ruff clean; mypy 212.

**879e — XLSX exports write worksheet XML to temp files (DH-06, High)**
- [x] Confirmed in the installed openpyxl 3.1.5: `ExcelWriter.write_worksheet` builds `WorksheetWriter(ws)` with no
      `out`, so `create_temporary_file()` → `NamedTemporaryFile(prefix='openpyxl.', delete=False)`; removed on success or
      at exit only. Every export wrote one per sheet; a forced worksheet failure left `openpyxl.*` on disk.
- [x] Approach approved by the CEO 2026-11-16: `shared/xlsx_in_memory.workbook_to_bytes` — an `ExcelWriter` subclass
      writes each sheet into a `BytesIO` and `writestr`s it (nothing on disk, nothing to clean up on failure); on import,
      openpyxl's temp-file factory is replaced by one that raises. Used by `excel_generator` (workpaper + financial
      statements), `leadsheet_generator`, `loan_amortization_excel`, and the unused `security_utils.dataframe_to_bytes`
      Excel branch (pandas' writer would have hit the guard). Output unchanged (Excel render snapshot identical).
- [x] Tests: `test_sprint_879_xlsx_no_disk.py` — a Python audit hook records every write-open and temp file during each
      of the four exports with marker names/amounts (none), forced failures inside worksheet writing and inside
      packaging (none), the guard raises on a bypassing `wb.save`, the override is pinned to openpyxl 3.1.5, an AST scan
      finds no other workbook save / `to_excel` in production code, `dataframe_to_bytes` writes nothing. Red before.
- Test-only exemption: `conftest._allow_openpyxl_tempfiles_for_fixtures` lifts the guard for the session, because 15
  test files build XLSX *uploads* with `wb.save()`/`to_excel`. The guard test re-enables it; the bypass scan covers
  production code.

**Verification (879e):** 879e + export/excel/leadsheet/loan/financial-statement/memo-render + every XLSX-fixture suite
640 passed; ruff clean; mypy 212.

**Commit SHA:** 879a `a8970d8a` · 879b `918037d9` · 879c `925fcc05` · 879d `59497810` · 879e `88d3776d`.
**Final verification (2026-11-16, on `88d3776d`, detached check worktree):** full backend suite **10,897 passed /
1 skipped / 0 failed** (18m29s). Alembic single head `a879d4f6c8e3`. Migrations to apply on deploy: `e879b2d4a6c1`,
`f879c3e5b7d2`, `a879d4f6c8e3`.
**Open (CEO):** pre-879 auto-saved actuals with NULL `actual_source` (clear or keep); flux proposals have no UI (the
flux page sends no engagement id); the preview cache never saves an upload (the browser re-sends the file), so removing
it would retire DH-07 — kept per CEO decision; remove `REDACT_LOG_TRACEBACKS` on Render if set (now a no-op).


---

### Sprint 880: Shared export links — retention, cleanup and file provenance (DH-08, DH-09, OUT-03)
**Status:** COMPLETE — 2026-11-16 on local branch `sprint-880-share-links` (stacked on Sprint 879; not pushed).
**Priority:** P0/P1 (freeze-exempt: security defects). **Source:** read-only review at `ef5e567`.
**Agents:** Guardian (lead), Executor, Critic.

**Decisions (CEO, 2026-11-16):** a link stops working after 24 h (Professional) / 48 h (Enterprise) and its stored
file is deleted within one hour after that. A link is revoked when its creator is removed from the firm or closes
the account; a downgrade or cancellation does not revoke — links run to expiry. Only files Paciolus generated can be
shared.

- [x] **5A (DH-08)** — share purge every 10 min (was hourly); opening an expired link deletes its file then; gauge
      `paciolus_export_share_oldest_undeleted_seconds` + `export_share_file_overdue` warning past one hour; member
      removal deletes the revoked files at once; every download rechecks the creator is still in the firm and the
      account is open.
- [x] **5B (DH-09)** — durable pending record (`export_shares.upload_pending`, migration `b880e5a7d9f1`) committed
      before the bytes are stored; cleared once the upload lands; pending rows never served or listed; the purge
      removes a pending row's file then the row after 10 min; hourly `reconcile_export_share_objects` deletes
      `shares/` objects no row points at (warns `export_share_untracked_objects`).
- [x] **5C (OUT-03)** — shared PDF/XLSX/CSV must match a signed, short-lived digest the server issued to that user
      when it produced the export (`shared/export_provenance.py`, 15-min HMAC token in `X-Paciolus-Export-Token`,
      issued by `SecurityHeadersMiddleware` from the digest `attachment_response` records; CORS exposes it). Share
      create requires `export_token`; the stored file is byte-for-byte the export. Sprint 852's CSV re-write is
      retired (generated CSVs are already escaped by `SafeCsvWriter`). OpenAPI snapshot regenerated.

**Commit SHA:** 5A `3afb5f93` · 5B `d6666e17` · 5C `5a29fc38`.
**Verification (2026-11-16, on `5a29fc38`, detached check worktree):** full backend suite **10,921 passed / 1 skipped /
0 failed**; frontend Jest 216 suites / 2,130 tests, `tsc` clean; `npm run build` compiles, then stops only at Next's
advisory check (known; hotfix: next >= 16.4.5); ruff 0; mypy 212; Alembic single head `b880e5a7d9f1`; OpenAPI drift clean.
**Outside the code:** R2 lifecycle rule on prefix `shares/` in `paciolus-exports` (backstop, e.g. delete after 3 days);
apply migration `b880e5a7d9f1`; after deploy, check logs for `R2 export-share list failed` (the token must allow listing).
**Follow-ups found:** `useExportSharing.createShare` posts the wrong field names and no UI calls it; a sharing UI must
send `export_token` from the export response. XLSX exports escape formula triggers per call, with no writer-level
guard or test like `SafeCsvWriter`'s.


---

### Sprint 896: Council 2026-11-25 — the urgent fixes
**Status:** COMPLETE (2026-11-25) — merged #338 (`3b0bf414`…`38516b0c`), live. Review fix: the account export keeps its
own scope (a member's firm-client work stays in their download). **Priority:** P0/P1 security and data loss
(freeze-exempt). **Source:** `reports/council-audit-2026-11-25.md` (G-01, G-02, G-03, C-01, C-02, C-03), each verified
in the code before fixing. **Agents:** Guardian, Critic, Executor.
- [x] **G-01 (P0) — passcode-protected share links could not be downloaded.** The GET answers a passcode share with
      404 (Sprint 718, no existence leak) while the page showed the passcode form only on 403; and the passcode POST
      was CSRF-checked although an anonymous recipient cannot get a CSRF token. Fix: `CSRF_EXEMPT_PATTERNS` exempts
      exactly `/export-sharing/<token>/download` (protected by the passcode, its throttles and the export limit); the
      page shows the passcode form on a GET 404 and lets the POST decide. Tests without `bypass_csrf`.
- [x] **G-02 (P1) — signed-in browsers were rate-limited as anonymous, by IP.** `RateLimitIdentityMiddleware` read only
      a Bearer header; browsers send the HttpOnly access cookie. Paid plans got anonymous limits and a firm behind one
      office address shared one bucket — invisible until Sprint 870 made limits fire. Now `_extract_access_token`.
- [x] **G-03 (P2) — Stripe webhook limit 10/minute per source address** would 429 Stripe's own bursts now that limits
      fire. Raised to 300/minute; signature checks and event dedup guard abuse.
- [x] **C-01 (P1) — a member's account deletion deleted the firm's clients and colleagues' engagements.** Erasure
      scoped clients by `user_id`; Sprint 853 made them the firm's. Now: personal clients plus all clients of a firm the
      user owns (dissolved with the account); firm clients elsewhere stay, `user_id` passes to the firm owner. A member
      with their own engagements on a firm client is refused (`ERASURE_FOREIGN_ENGAGEMENTS`) rather than wiped.
- [x] **C-02 (P2)** — sole owner's erasure failed on the firm's RESTRICT key after Stripe was cancelled (clients a
      removed member created). Covered by C-01's owned-firm scope.
- [x] **C-03 (P2)** — `analytical_expectations.actual_captured_by` (Sprint 879) was not cleared → 500 on erasure. Added,
      plus a guard test: every column referencing `users.id` must be cleared, deleted or cascade.
- [x] Remaining council findings: filed as Sprints 897–899 (2026-11-25).

**Commit SHA:** TBD.


---

### Sprint 870: Rate limits never fire in production (#274)
**Status:** COMPLETE on production 2026-11-25 (config); guard + regression tests in PR. Part A merged 2026-11-24 (#333).
Was: part A (probe) in a PR awaiting CEO merge; part B (fix) waited on its log
output. Filed 2026-11-14 as "Sprint 861" in PR #312; renumbered 2026-11-15 because 861 was used for the
website claims sprint on `main`. **Priority:** P0 security (freeze-exempt). **Source:** issue #274 (2026-10-27).
**Agents:** Guardian (lead), Executor, Critic.

**Diagnosis so far (2026-11-16, on `ef5e5676`, live):**
- A burst of **300** GETs to `/benchmarks/industries` (60/minute default) from one client in ~10 s got **300 × 200**.
  Boot log shows 4 workers, each `Rate-limit storage backend: redis`. Per-worker memory counters (hypothesis 3) would
  have started 429ing near 240, so (3) is ruled out unless the instance runs more than 5 workers.
- slowapi's fallback path was read (`extension.py` `_check_request_limit`): when storage is dead it still evaluates the
  default limits on the in-memory limiter, so a silent fallback would still limit. Not the cause.
- `TRUSTED_PROXY_IPS` has never been confirmed set on Render (open CEO action since Sprint 851). Unset, the key is the
  TCP peer — Render's proxy. A single proxy address would put all traffic in one bucket and 429 constantly, which is
  the opposite of what is seen, so the peer must vary per request: hypothesis (1), not yet proven.
- Nothing logs the computed key, and Key Value `paciolus-ratelimit` has an empty IP allow-list (no outside access), so
  neither (1) nor (2) can be observed without a deploy. Opening Key Value to the internet was rejected.

**Part A — probe (this PR):** `shared/rate_limits._probe_key_derivation` logs the first 100 anonymous key derivations
per worker (`rate_limit_key_probe …`): the peer, each `X-Forwarded-For` / `CF-Connecting-IP` / `True-Client-IP` /
`X-Real-IP` entry and the key. Non-global addresses (RFC 1918, CGNAT, loopback) are logged raw — they are Render's
proxies; global addresses only as `hash_ip_address()` digests. `/health/ready` → `rate_limit_storage.details` gains
`trusted_proxies_configured` (a count, never values). **After deploy:** burst ~70 requests, then read the probe lines
and compare the public hashes with `sha256(<your IP>)[:16]`.

Production has returned **zero 429s since 2026-10-01**: 80 requests in 3 s to an undecorated route all got 200. The
same commit run locally returns 60 × 200 then 429s, so the code works and the production environment differs. Every
limit is affected — login, password reset, export-share passcode brute-force (Sprints 697/698), uploads — because
they share the key function and storage.

- [x] Part A probe + health count, with tests (`test_rate_limit_key_probe.py`, 10; watched 2 fail when public
      addresses were logged raw). Caught on the way: Python treats TEST-NET `203.0.113.0/24` as `is_private`, so the
      raw/hashed split is `is_global`, not `is_private`.
- [x] **CEO:** merge part A; confirm deploy SHA; then the burst + log read above (Claude can do the read). Merged in #333,
      live at `209e5039` 2026-11-25.
- [x] **Diagnose on production first, don't guess.** **Result (2026-11-25): hypothesis (1).** A 75-request burst got
      75 × 200. Probe: every request came from a Render internal proxy (`10.x`, at least 7 rotating addresses),
      `peer_trusted=False`, `trusted_proxies=0`, so `key = peer`: one client in ~7 buckets of ~11 requests, under 60.
      `X-Forwarded-For = [client, edge]`; the client hash matched the burst machine's address, and all 9 logged edge
      hashes matched an address in Cloudflare's published IPv4 ranges (1,524,736 hashed). Chain: client → Cloudflare →
      Render proxy → app. Hypotheses (2) and (3) not needed. Hypotheses from #274, in order:
      (1) rate-limit **key**: `security_middleware.get_client_ip` trusts `X-Forwarded-For` only from `TRUSTED_PROXY_IPS`;
      behind Cloudflare + Render the peer may differ per request, so every request gets its own bucket;
      (2) **Redis counters** on Render Key Value `paciolus-ratelimit` not written/read — inspect `LIMITS:` keys + TTLs during a burst;
      (3) gunicorn's 4 workers silently falling back to per-worker memory.
- [x] Fix the cause; keep the Sprint 774 `degrade` storage-failure policy intact. **Config, not code:** Sprint 851's
      right-to-left read is correct once both hops are trusted. `TRUSTED_PROXY_IPS` = `10.0.0.0/8` + Cloudflare v4/v6
      ranges (23 entries, value in `docs/ops/ENVIRONMENT_VARIABLES.md`), set on Render 2026-11-25 03:10 UTC. Verified
      locally first against the observed header shape and a spoofed `X-Forwarded-For`. Guard: `/health/ready`
      reports `degraded` with `client_key_unreliable` when production has no trusted proxies.
- [x] Regression test for the identified cause: `test_sprint870_proxy_chain.py` (rotating peers and edges → one key;
      spoof ignored; the empty value reproduces seven keys; readiness guard).
- [x] **Verify on production:** a burst on an undecorated public route returns 429 after 60, and Render logs show the 429s. Close #274.
      2026-11-25 03:12 UTC: 60 × 200 then 15 × 429; Render request log shows the 429s; probe shows `peer_trusted=True`,
      `key=public:<client hash>`. Every limit (login, reset, share passcodes, uploads) uses this key, so all are live again.
- [ ] Yearly (Nov 1): re-check Cloudflare's published ranges against the documented value.

**Commit SHA:** TBD.


---

### Sprint 894: Todo bookkeeping, Next.js security upgrade, exact amounts in response schemas
**Status:** COMPLETE (2026-11-24) — merged with the 2026-11-24 integration chain.
**Agents:** Executor (lead), Guardian (Next.js advisory), Critic (amount sweep).
- [x] A. Checkboxes Sprint 893 already closed but left open under 888, 889, 890 and 892 ticked, with where each was done.
- [x] B. Next.js 16.4.3 → 16.4.6 (in range): clears the advisories that make `next build` exit on Next's
      `SecurityFatalError` on alternate runs (884 follow-up and "Then (C)"). Lockfile: only `next` and its `@next/*`
      binaries changed. `npm audit`: `next` gone; the 26 moderates left are Jest's `glob`/`minimatch` chain (needs a
      Jest major, already on `main`). `next build` run twice back to back: both exit 0, pages `ƒ` as before.
- [x] C. Remaining `float` monetary fields in `shared/*response_schemas.py` move to exact amounts (884 follow-up);
      finding `details` stay floats by design (Sprint 829). 122 fields (80 diagnostic, 42 testing): balances, totals,
      debits/credits, adjustments, variances in currency, sampling misstatements and limits. A float the engine sends
      goes out unchanged (same JSON); a Decimal now keeps its cents above 2^53. Left as `float` on purpose: ratios,
      percentages, scores, confidences, quantities, hours, statistics (mean, median, std dev, Gini), bucket bounds,
      and three mixed fields that can hold a count or a quantity (`DiagnosticVarianceResponse`, ISA 520
      `ExpectationEvaluationResponse`, three-way-match `MatchVarianceResponse`). Note: `ExactMoney` refuses `inf`/`NaN`
      where `float` let them through, so no ratio-like field was moved. Test: `TestSprint894AmountFields` (63 fail on
      the old schemas). mypy unchanged (289, baseline 1,011).
      Full backend run (`-m "not slow"`): 11,510 passed, 2 failed — two sampling tests compared the model's attribute
      (now a Decimal) with a float; updated to compare exactly. The JSON they check is unchanged.

**Review (2026-11-24).** Commits: `59f9b679` A · `f67e5d97` B · `0c8375d1` C · `9604ce44` C test follow-up.
Verification: backend `-m "not slow"` on the 894 tip 11,510 passed, 2 failed (the two sampling attribute tests, fixed
in `9604ce44`); `next build` twice, both exit 0; mypy 289 (baseline 1,011). The full chain was verified again after
integration (see the START HERE block).


---

