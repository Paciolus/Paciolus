# Sprints 849–852 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-27.

---

### Sprint 849: Org members' entitlements follow the owner's live plan (M5)
**Status:** COMPLETE 2026-10-27 (pending CI + merge). **Priority:** P1 (revenue leak). **Source:** security review M5 (verified).

**Defect:**
- `shared/organization_policy.py` (`apply_org_subscription_to_user`) copies `sub.tier` onto `user.tier` when a
  member joins.
- `shared/entitlement_checks.py` (`get_effective_entitlements`) trusts `user.tier` when the user has no
  Subscription row, and members never have one.
- `billing/subscription_manager.py` (`sync_subscription_from_stripe`) updates only the owner.
- `_downgrade_org_members_to_free` (`billing/webhook_handler.py`) runs only for non-entitled statuses.

So when an owner moves Enterprise → Solo, members keep Enterprise (bulk upload, branding) indefinitely.
`admin_force_cancel(immediate=True)` (`billing/admin_customers.py`) has the same gap: it sets `CANCELED`
locally and calls no Stripe API, so no webhook follows and members stay paid.

- [x] In `entitlement_checks`, when the user belongs to an org and is not its owner, use the **owner's**
      Subscription instead of the "no row → trust tier" branch. Active or trialing → the owner's tier; anything
      else → FREE. Keep `user.tier` only as a display cache.
      — New `_org_member_entitlements` resolves the org through the existing seat-check resolver
      (`_resolve_org_subscription`, split into `_resolve_subscription_for_org` so the org is loaded once):
      `org.subscription_id` first, then the owner's ACTIVE/TRIALING row; no row or a non-entitled status → FREE.
      It runs only when the member has **no** Subscription row of their own (as the item says); a member's own row
      keeps the existing rules, and the owner still resolves from their own row. The `user.tier == FREE`
      short-circuit now applies only to users in no org, so a member whose cache says FREE still follows the owner.
      Extra: `apply_org_subscription_to_user` assigned the raw string to `user.tier` (`type: ignore`), so
      `user.tier.value` raised until the row reloaded; it now assigns `UserTier(sub.tier)`.
- [x] Refresh members' cached `tier` in `sync_subscription_from_stripe` whenever the owner's tier changes, so
      `/users/me` shows the right plan.
      — New `_refresh_org_member_tiers(db, owner_id, tier)` runs after the owner's tier is set on every sync (an
      idempotent no-op when nothing changed, or when the user owns no org). It sets each non-owner member to the
      owner's effective tier (FREE for a non-entitled status). It skips members with their own Subscription row,
      because their entitlements read their `tier`.
- [x] Make `admin_force_cancel(immediate=True)` call `_downgrade_org_members_to_free` (or the shared helper the
      webhook uses).
      — Calls `billing.webhook_handler._downgrade_org_members_to_free` (lazy import). Cancel-at-period-end is
      unchanged: Stripe's `customer.subscription.deleted` webhook downgrades the org at period end.
- [x] Check the JWT `tier` claim. It is used for rate-limit tiers only (per the review), so stale claims are fine,
      but confirm.
      — **Confirmed.** The claim is written by `auth.create_access_token` / `create_impersonation_token` from
      `user.tier`. Its only reader is `RateLimitIdentityMiddleware` (`security_middleware.py`,
      `payload.get("tier")`). That reader sets the `shared.rate_limits._current_tier` ContextVar, which
      `TieredLimit` uses, and `request.state.rate_limit_user_tier`, which nothing reads. Entitlement checks and
      `require_current_user` load the `User` row and never read the claim. The frontend does not decode it. A stale
      claim only keeps the old rate-limit tier until the access token expires.
- [x] Tests (`tests/test_sprint_849_org_member_entitlements.py`, 17 tests):
  - owner Enterprise → Solo via the sync path → the member's entitlements equal Solo's (and the cache says Solo);
  - owner past_due → member is FREE (via sync, and with no refresh at all: live read with a stale cache);
  - admin immediate force-cancel → member is FREE (cancel-at-period-end leaves the member paid);
  - a solo user with no org is unchanged (6 parametrised tier/status cases);
  - plus: stale-cache tier change, reactivation restores the member, an org with no subscription → FREE, the owner
    keeps their own rules, and the refresh skips a member with their own row.
  - 10 of the 17 fail on the unfixed code. They were checked by reverting the three source files (the other 7 are
    the solo-user and owner baselines). Two of the 10 failed on the old `str` assignment rather than on the
    entitlement logic.

**Not in scope (noted):** other owner-only cache writes (`admin_plan_override`, `invoice.payment_succeeded` /
dispute-won restores, the dunning-engine cancel) still leave members' *display* cache stale. Their *entitlements*
are correct now, because they read the owner's row live.

**Verification:** ruff check + ruff format --check clean on the 5 touched files; mypy reports no errors in the 4
touched source files; new tests 17/17; full backend suite **9,984 passed, 0 failed** (serial, 18m42s). A first full
run failed 30 tests (compare-periods / three-way / rate-limit). Those tests use `MagicMock` users whose
auto-attribute `organization_id` is truthy. Org membership is now detected by `isinstance(..., int)`.

**Commit SHA:** `ec1c00b2` (stacked on PR #276).

---

### Sprint 850: PDF upload parsing in a resource-limited subprocess (M6)
**Status:** COMPLETE 2026-10-27 (pending CI + merge). **Priority:** P2 (DoS; needs a verified paid account). **Source:** security review M6.

**Defect:**
- `shared/pdf_parser.py` `_extract_tables_from_pages`: the 5 s per-page "timeout" is compared *after*
  `page.extract_table()` returns, so it never interrupts.
- pdfminer's FlateDecode does `zlib.decompress(data)` with no output cap.
- The ZIP ratio and size checks (`shared/upload_pipeline.py`) don't apply to PDF streams.
- Parsing runs in `asyncio.to_thread` with no overall timeout.

A roughly 5 MB PDF whose stream inflates to gigabytes can kill a Render worker; repeated uploads take the API down.
Reproduced on the old code: a 34 KB PDF (32 MiB of deflated zeros) held the API process for 43 s, logged
`took 43.1s (limit 5.0s), dropping` *after the fact*, then returned the generic "No tables" 422.

- [x] Move the PDF parse into a child process: `multiprocessing` with the **spawn** context, so it doesn't fork the
      app. — Extraction core split out to new `shared/pdf_extraction.py` (stdlib + pdfplumber only; no FastAPI,
      pandas or app imports, so the child stays cheap); `shared/pdf_parser.py` is the parent side and re-exports the
      old names, so `routes/audit_preview.py`, `upload_pipeline` and the route-test patches are unchanged.
      `extract_pdf_tables()` checks `%PDF` magic in the parent (no spawn for non-PDFs), then runs
      `pdf_extraction.sandbox_main` in a `spawn`-context `Process`.
  - The child sets `resource.setrlimit(resource.RLIMIT_AS, (1 GiB, 1 GiB))`, guarded by
    `if sys.platform != "win32"`.
  - The parent waits at most 30 s overall (`PDF_PARSE_TIMEOUT_SECONDS`, covering child start-up too), then
    `terminate()` → `kill()` with a 2 s grace each.
  - The parsed rows come back across a one-way `Pipe` as a tagged tuple (`ok` / `rejected` / `aborted` / `error`);
    a corrupt or >500-page PDF still reaches the client as the same 400 (via a FastAPI-free `PdfRejectedError`).
  - Found while testing: pdfplumber re-wraps any interpreter error as `PdfminerException(e)`, and the per-page
    `except Exception` would have swallowed the RLIMIT `MemoryError` as "page dropped". `_is_memory_error()`
    unwraps it and the parse aborts instead.
- [x] On a memory error, a kill or a timeout, return 422 `"This PDF is too complex to parse. Export the trial
      balance as Excel or CSV instead."` (`PDF_TOO_COMPLEX_DETAIL`, raised as `HTTPException(422)` — the same
      path `parse_pdf`'s other 422s use, so `upload_pipeline` also counts it in `parse_errors_total`), and
      increment `pdf_parse_aborted_total{reason}` (`memory` / `killed` / `timeout`). Deviation: the exported
      metric name is `paciolus_pdf_parse_aborted_total` in `PARSER_REGISTRY`, matching every other counter in
      `shared/parser_metrics.py`. `killed` = the child exited without a result (OOM-kill, signal, crash).
- [x] Delete the misleading post-hoc per-page timeout check — deleted with `PER_PAGE_TIMEOUT_SECONDS`; the
      docstring of `_extract_tables_from_pages` says why and what bounds time/work now (parent deadline +
      `MAX_PDF_PAGES`). The old `TestPdfTimeout` (which asserted `dropped_rows >= 0`) went with it.
- [x] Tests (`tests/test_pdf_parser.py::TestPdfSandbox`, 7 new + 1 new 400-translation test):
  - deflate bomb generated in the test from one full-flushed 1 MiB block repeated (a 2 GiB bomb is ~2 MB and no
    big buffer exists in the test process); a 32 MiB bomb with the deadline patched to 3 s → exact 422 message in
    ~3.0 s, `timeout` counter +1, no live children. 32 MiB is harmless on Windows, where only the deadline applies.
  - Linux only (`skipif(sys.platform == "win32")`): a 2 GiB bomb trips the 1 GiB RLIMIT_AS → 422, `memory` +1,
    well inside the deadline. **Not run locally (Windows dev box); first run is CI.**
  - child dying without a result (target swapped for `os._exit`, which dies on the extra args) → 422, `killed` +1;
    a wrapped `MemoryError` inside a page aborts the parse; non-PDF bytes are rejected before spawning; a normal
    PDF parses with the in-process core patched to raise (so it really ran in the child).
  - The existing normal-fixture tests (`extract_pdf_tables` / `parse_pdf`) all go through the sandbox and pass;
    the mocked >500-page test now drives `extract_tables_in_process`, since a mock can't cross the process.
  - Fail-before-fix: the new tests import names that don't exist pre-fix; the bomb case was also run against the
    unfixed parser (43 s, wrong 422 — fails both the 13 s bound and the message assert).
- [x] Measure the latency overhead of spawn on a normal PDF. **~0.40 s** on the Windows dev box (median of 10:
      1-page fixture 17 ms in-process vs 416 ms sandboxed; 3-page 71 ms vs 466 ms); Linux spawn is typically
      faster. Under the ~1 s bar, so **no persistent pool**: one fresh child per parse also means no state or heap
      fragmentation carries between uploads. Caveat found while measuring: `spawn` re-imports the parent's
      `__main__` in the child — when `__main__` imported the app, overhead was 2.2 s. Production's `__main__` is
      the gunicorn launcher (light); running the API as `python main.py` would pay that cost per PDF.

**Not done / follow-up:** no cap on concurrent PDF children per worker — several simultaneous bomb uploads could
still hold 1 GiB each; the per-user rate limit is the only bound today.

**Verification:** `test_pdf_parser.py` + `test_pdf_upload_integration.py` + `test_audit_preview_routes.py`
**73 passed, 1 skipped** (the Linux-only RLIMIT test) in 28.5 s; **full backend suite 9,973 passed, 1 skipped,
0 failed** (serial, 18m59s, origin/main venv: FastAPI 0.162 / SQLAlchemy 2.1.6). `ruff check` + `ruff format --check`
clean on the 4 touched Python files; mypy clean on `shared/pdf_parser.py` + `shared/pdf_extraction.py`.

**Commit SHA:** `3f001479` (stacked on PR #277).

---

### Sprint 851: Client IP derivation behind Render's proxy (M2)
**Status:** COMPLETE 2026-10-27 (code; pending CI + merge) — **one CEO step after deploy** (below). **Priority:** P1. **Source:** security review M2.

**Unblocked because** the code fix is correct whatever `TRUSTED_PROXY_IPS` currently holds; only the post-deploy
setting needs the console. Checked via the Render API 2026-10-27: paciolus-api is a Docker service with an empty
`dockerCommand` (it runs the Dockerfile `CMD`, which passes no `--forwarded-allow-ips`), so uvicorn's
`request.client.host` is the Render proxy. The API can't read env-var values, so whether `TRUSTED_PROXY_IPS` is
set is still unknown.

**Defect:** `get_client_ip` returned the **leftmost** `X-Forwarded-For` entry when the peer was a trusted proxy.
Render's proxy *appends* the real client IP, so the leftmost entry is attacker-controlled. If `TRUSTED_PROXY_IPS` is
set, rotating spoofed values bypasses every per-IP limit; if it is unset, every request's peer is the proxy and all
users share one bucket.

- [x] `get_client_ip` (the single implementation; `shared/rate_limits._get_client_ip` delegates to it) walks
      `X-Forwarded-For` right to left when the peer is trusted, skips trusted-proxy hops and entries that are not
      valid IPs (`ipaddress.ip_address`), and returns the first untrusted entry. No usable entry → the peer.
- [x] Tests (`test_transport_hardening.py`, +7): spoofed leftmost ignored; rotating it keeps one bucket; multi-hop;
      untrusted peer ignores XFF; garbage skipped; IPv6; all-trusted → peer. 4 fail on the old code.
      `test_rate_limit_tiered.py::test_proxy_aware_extraction_exact_ip` encoded the leftmost behaviour; its expected
      value is now the entry the trusted proxy appended.
- [x] Comment at the `/metrics` loopback gate: never set `FORWARDED_ALLOW_IPS='*'` / `--forwarded-allow-ips='*'`.
- [ ] **CEO, after this deploys** (also in `ceo-actions.md`): Render dashboard → paciolus-api → Environment → set
      `TRUSTED_PROXY_IPS` to the address range Render's proxy connects from (confirm with Render support; it is
      not something to guess). Trusting a whole private range is safe with the right-to-left walk, because a client
      cannot append entries after the proxy's. **Never** set `FORWARDED_ALLOW_IPS='*'`. Then confirm in logs that
      hashed client IPs vary per user. Until it is set, behaviour is unchanged from today (all traffic shares the
      proxy's bucket).

**Verification:** ruff clean; targeted 89 passed; full backend suite 9,974 passed (on `main`, before stacking).

**Commit SHA:** `2733c8f1` (stacked on PR #278).

---

### Sprint 852: Security hygiene batch (L2, L6, L7, L8, L9, L10, L13)
**Status:** COMPLETE 2026-10-27 (pending CI + merge). **Priority:** P2. **Source:** security review lows.

> **Checked by Claude via the Render API, 2026-10-27 (no CEO action needed for L2/L6):** the live startup log reads
> `Sentry APM initialized (env=production, ...)`, which prints `ENV_MODE` verbatim, so the new allow-list and the
> `RENDER` check pass in production. paciolus-api is a Docker service with an empty `dockerCommand`, so it runs the
> Dockerfile `CMD` and the `--access-logfile -` removal there fully closes L6.

- [x] **L2: `ENV_MODE` fails open.** `config.py` now accepts only `{"development", "test", "production"}`
      (case-sensitive) and hard-fails on anything else, and hard-fails when `RENDER` is set and `ENV_MODE !=
      "production"`. Repo-wide audit of values set: `ci.yml` ×4 `development`, `dr-test-monthly.yml` `test`,
      `.env.example` / `docker-compose.yml` default `development`, OpenAPI scripts `development`; no workflow or test
      sets `RENDER`. Deviation: `test_security_hardening_2026_04_20.py` used `ENV_MODE=staging` for the
      `create_dev_user` refusal tests → switched to `test`; `docs/ops/ENVIRONMENT_VARIABLES.md` listed `staging` as
      valid → corrected. Tests: `tests/test_env_mode_allowlist.py` (8 of 12 fail on the old config).
- [x] **L6: share tokens appear in raw access logs.** The premise was wrong: the app's access log
      (`http_metrics_middleware.py`) logged the **raw** path, and its share-token pattern was hex-only, while tokens
      are `token_urlsafe(32)`. Fixed first: new `_SECRET_PATH_REDACTIONS` (share token and
      `/organization/invite/accept/{token}`) are applied to the access-log line, with numeric IDs kept for debugging,
      and to metric labels. Then removed `--access-logfile -` from `backend/Dockerfile` and the documented Render
      start command in `DEPLOYMENT_ARCHITECTURE.md`. Tests: `tests/test_access_log_redaction.py` (5 of 6 fail
      before).
- [x] **L7:** the passcode-mismatch log now records `ip_hash=hash_ip_address(ip)`. Test asserts the raw IP is absent
      and the hash is present (fails before).
- [x] **L8: shared exports are client-supplied bytes.** CSV shares are parsed and re-written through `SafeCsvWriter`
      before storage (`_rewrite_csv_share`). Escaping is idempotent, a UTF-8 BOM is kept, and a non-UTF-8 or
      malformed CSV gets a 400. A code comment says PDF and XLSX shares remain client-supplied, with server-side
      generation as the long-term fix. Tests: `tests/test_export_sharing_hygiene.py`.
- [x] **L9: logo dimensions are not checked.** Pillow was already a direct dependency (`pillow>=12.2.0`).
      `routes/branding.py` reads the header only with lazy `Image.open`, rejects over 4000 px per side or over 25 MP
      (Pillow's own `DecompressionBombError` is mapped to the same 400), requires format PNG/JPEG (plus MPO, which is
      how Pillow reports a multi-picture camera JPEG), and keeps the magic-byte allow-list. Tests: a crafted
      20000×20000 IHDR, 4001×10, 10×4001, a truncated PNG, and 4000×4000 plus a real JPEG accepted (4 fail before).
      `test_post_audit_2026_04_20_batch2.py` uploaded magic bytes plus zero padding as a "PNG"; it now uses a real
      4×4 PNG.
- [x] **L10: rate limits loosen during a Redis outage.** The workflow already failed on any body status other than
      `"healthy"` (Sprint 775), so this was already true. Added an explicit `degraded` branch whose verdict names the
      per-worker rate-limit consequence. Kept the existing `python3` parse rather than switching to jq: same
      robustness, and the test can run it. `tests/test_uptime_check_workflow.py` runs the real probe step under bash
      with `curl` stubbed: healthy passes; degraded behind a 200, non-JSON, `{}` and 503 all fail; FAIL reaches
      `exit 1`.
- [x] **L13:** top-level `permissions: contents: read` in `dependency-compliance.yml`. No job needs more: there is
      no issue or PR write, and the artifact upload/download is same-run and uses the runtime token.
      `tests/test_workflow_permissions.py` guards it.

**Verification:** full backend suite run serially in a fresh venv matching origin/main: **10,003 passed, 0 failed**
(14m19s). The first full run caught two `test_post_audit_2026_04_20_batch2` logo tests using fake PNGs, fixed above.
Each new regression test was confirmed failing against the unfixed source (counts per item above).
`ruff check` + `ruff format --check` are clean on touched files. mypy shows no new errors in touched modules
(`config.py:253` is pre-existing).

**Commit SHA:** `7e317874` (stacked on PR #279).

---
