# Sprints 836–840 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-24.

---

### Sprint 840: Security defects found by the claims review
**Status:** COMPLETE 2026-10-24. **Priority:** P0 (S1, S2) / P1 — fix before launch; several honest claims depend on these.
**Source:** `reports/claims-review-2026-10-24.md` Part 1 (file:line for each).

- [x] **S1** `/internal/metrics/*` → `Depends(require_superadmin)`; `_require_owner` deleted. Auth tests now run real
      tokens (overriding `require_verified_user` never reached `require_superadmin`, which calls it directly):
      org owner, member, paying Solo and Free all 403; superadmin 200.
- [x] **S2** Scrubber moved to `shared/sentry_scrubber.py` (the old test exercised a hand-copied mirror):
      `include_local_variables=False`, `include_source_context=False`, `max_value_length=1024`, `max_breadcrumbs=0`;
      `before_send` redacts exception values, drops frame vars/source, breadcrumbs, cookies, non-safe headers and log
      arguments (keeps the template). `export_sharing.py` R2 failure no longer passes `exc_info`.
- [x] **S3** `require_current_user` refuses `imp` tokens on POST/PUT/PATCH/DELETE (403) and revoked/jti-less ones on
      every method (401); middleware now resolves the token like `resolve_access_token` (any-case scheme, then cookie)
      and never releases a revoked token. Stop endpoint takes the token in the body (admin authenticates with their
      own session) — it was unreachable; the banner's End Session now calls it. Impersonate requires
      `target_user_id` and 409s on an org/user ID mismatch; superadmins can't be impersonated.
- [x] **S4** `shared.filenames.safe_csv_writer` escapes every text cell (plain-number strings like `-1,234.56` stay
      numeric); all 21 raw `csv.writer` sites moved onto it. `tests/test_csv_formula_guard.py` AST-scans tracked
      files and fails on any raw writer outside the wrapper.
- [x] **S5** `log_secure_operation` → `paciolus.security` logger (WARNING, details redacted: quoted text removed,
      emails masked) for a curated `SECURITY_EVENTS` set; routine tracing logs at DEBUG **without details** (many name
      the upload). `PERSISTED_EVENTS` (auth failures, lockouts, IP blocks, token reuse/race, session revocation,
      password change/reset, email change, impersonation) write to the new `security_events` table (migration
      `a8c4e2f19d07`, single head; hashed IP only; 365-day purge in retention cleanup).
- [x] **S6** The 8 listed sites log `type(e).__name__` only. Production already strips tracebacks
      (`TracebackRedactionFilter`), so `logger.exception` sites were safe once the arguments were.
- [x] **S7** Measured first (50k-row ledger): openpyxl peaks ~6× the XML, odfpy ~19×; real XLSX compresses 10–13:1,
      real ODS ~37:1. Caps: XLSX/DOCX 200 MB uncompressed at ≤50:1; ODS 50 MB at ≤100:1 (a 20:1 ODS cap would reject
      real files).
- [x] **S8** The sweep deletes a row only after R2 confirms; a failed DELETE keeps the row for the next pass. **CEO:**
      add an R2 lifecycle rule (≤ 2 days) on `paciolus-exports` as the backstop.
- [x] **Lows:** dummy bcrypt check for unknown emails and locked accounts; `SlowAPIMiddleware` applies the 60/min
      per-route default to the 52 undecorated routes (+ test that floods one to 429; not the ASGI variant — slowapi
      0.1.9's re-sends `http.response.start` per body chunk); passcode throttle + refresh-token IP use
      `get_client_ip()` (**CEO:** confirm `TRUSTED_PROXY_IPS` is set on Render, or this still sees the proxy);
      preflight token is owner-bound and taken atomically; Starlette's spool threshold raised to the 110 MB body cap
      so uploads stay in memory; adjustment approver is the session user.
- **Not done, deliberately:** *uniform registration response* — `/auth/register` logs the user in, so a duplicate
      email cannot get the same response without redesigning signup as "check your email" for both cases (a product
      change; left for Sprint 844's account work). *No self-approval* — each adjustment set belongs to one user, so
      the preparer is the only possible approver; refusing it would make posting impossible. Needs org-shared sets.
      *MFA* — its own future sprint.

**Commit SHA:** TBD.


---

### Sprint 837: Citation corrections; 1099 thresholds by tax year
**Status:** COMPLETE 2026-10-24 — found by the Sprint 835 catalog; practitioner confirmation items below.
**Priority:** P1 — customer-visible text cited standards for things they do not say.

- [x] **About 40 citation corrections**, each to the strength the source supports and without
      unconfirmed paragraph numbers. Highlights: weekend/after-hours/holiday tests labelled Paciolus
      conventions (ISA 240 / AS 2401 do not name them); Benford's 300-entry minimum is ours (Nigrini's
      MAD bands stay attributed); unverifiable statistics removed from customer text (ACFE "26%" and
      "~19%", "BLS 2023 ~17%"); an "AICPA Audit Guide for Receivables §5.11" reference removed;
      "allowance required under IFRS 9 / ASC 326" corrected (the standards require ECL measurement, not
      a named account); bank rec and three-way match no longer presented as ISA 505 / AS 2310
      confirmations (they reconcile client records, ISA 500); ISA 501 no longer cited for cut-off or for
      inventory tests that involve no count; ISA 570 "¶16" references removed; SoD no longer "required
      for SOC 1"; ASC 230 no longer cited for a forecast; sampling no longer claims classical-variables
      and attribute methods; multi-period no longer claims reclassification detection; W-2 941
      comparison described as what the code does (payroll YTD); benchmark figures no longer attributed
      to RMA / SEC EDGAR; revenue RT-01/06/07/14/15/16/17 text made to match the code (RT-17 renamed
      "Contract Data Completeness"). Seven memo intros now say "with reference to" rather than "in
      accordance with" professional auditing standards.
- [x] **1099 thresholds by year** (`form_1099_engine.thresholds_for_year`): through 2025 NEC and MISC
      boxes $600; **2026 NEC and MISC boxes 1/3/6 $2,000** (2025 legislation, per secondary sources —
      confirm against the IRS instructions); box 10 attorney proceeds kept at $600 (unclear whether the
      change reaches it; the lower figure cannot miss a filing); royalties and interest $10. 2027+ uses
      the 2026 figures with a notice that the indexed figure must be confirmed. Payees from $600 up to
      the year's threshold are listed as "not required, shown for review" (API, CSV, results view) and
      the result states every threshold applied and its basis.

**For a practitioner to confirm:** the 2026 1099 figures and their statutory basis, box 10, the ASC 606
paragraph numbers that were kept (606-10-25-12, -25-13, -25-30), and the benchmark sample sizes still
returned by the benchmarks API (unverifiable; not changed).

**Commit SHA:** 4ed14103 (PR #228).


---

### Sprint 836: Saved testing thresholds are applied, and disclosed
**Status:** COMPLETE 2026-10-24 — found during Sprint 831.
**Priority:** P1 — a customer who changed a threshold in the tool settings drawer saw no effect.

- [x] `shared/saved_testing_config.py` builds each engine's config from the saved practice settings:
      known fields only, type- and range-checked (finite, non-negative, 0–1 shares, 0–23 hours); anything
      else is reported in `settings_ignored` and never fails a run.
- [x] Wired into JE (per-run holiday calendar stays on top), AP, Payroll and Three-Way Match (a value
      supplied for the run replaces the saved one, and says so).
- [x] Transparency: each result reports `settings_applied` (only values that differ from the engine
      default) and `settings_ignored`; a notice on all four results views; memos gain a "Thresholds from
      saved settings" table (setting, this run, Paciolus default).
- [x] **Settings-screen drift fixed:** JE `benford_min_entries` defaulted to 500 in the frontend vs 300
      in the engine (a saved hidden 500 is reported as ignored, not applied); **five Payroll toggles were
      saved under names the engine never read** (`check_gap_enabled`, `benford_enabled`, `ghost_enabled`,
      `duplicate_bank_enabled`, `duplicate_tax_enabled`) — renamed to the engine names, old names still
      accepted; Payroll `ghost_min_indicators` default 2 vs engine 1 aligned. Tests now fail if the
      frontend defaults drift from the engine again.
- [x] `methodology-sources.ts`: 33 rules marked configurable.

**Effect to know:** old saved values now take effect, and are disclosed on every result (e.g. an old
Payroll "Standard" save shows "Ghost employee min indicators: 2 (default 1)").

**Commit SHA:** 66693307 (PR #229).


---

### Sprint 838: Loose ends from the methodology sweep
**Status:** COMPLETE 2026-10-24.

- [x] Bank-rec CSV now includes split matches (a section grouped per bank item, each bank amount counted
      once), marks bank-only items whose split search was capped, and escapes every user cell. The export
      route had also been discarding `ledger_txns` / `split_search_limited` from the browser's JSON.
- [x] `BankRecResponse` declares `suggested_journal_entries`, which FastAPI had been dropping.
- [x] W-2 CSV escapes employee IDs, names and messages against spreadsheet-formula injection.
- [x] Memo descriptions added for AP-T14, RT-09b and RT-17; a test now fails if any engine test ships
      without a memo description.
- [x] USER_GUIDE §17 callout rewritten for per-year statutory limits and the catch-up "check not run" notice.
- [x] Admin customer views show the window-aware upload count (Sprint 790) instead of the raw counter.

**Commit SHA:** 66693307 (PR #229).


---

### Sprint 839: API inputs with no path from the app
**Status:** COMPLETE 2026-10-24 — found in Sprint 838. Column-mapping UI for bank rec / TWM still needs its own design.

- [x] **Bank rec:** per-run materiality and performance materiality in a "Run settings" panel (validated
      in the app and the route — `nan`/`inf` now refused); a "Thresholds applied" card shows each figure and
      whether it was entered for the run or is the Paciolus default (`active_thresholds.threshold_sources`;
      the old single `materiality_source` called a defaulted performance materiality "caller").
- [x] **Three-Way Match:** per-run panel for all seven tolerances, prefilled from saved settings, sending
      only changed values; per-run values disclosed in `settings_run_overrides` (results notice + memo
      table); `fuzzy_composite_threshold` added to the frontend config. PO / invoice / receipt column
      mappings are now applied to detection (400 on bad JSON, unknown fields or missing columns) instead of
      being parsed and ignored.
- [x] **W-2:** public `GET /audit/w2-reconciliation/supported-years`; the page states the supported years
      before upload and blocks an unsupported year with a plain message. No override form (2026 figures
      await Sprint 793b).
- [ ] Column-mapping UI for bank rec and TWM (the TB `ColumnMappingModal` is hard-wired to
      account/debit/credit). The bank-rec memo does not print `active_thresholds` although a comment says it
      does.

**Commit SHA:** 5f82d818 (PR #230).


---

