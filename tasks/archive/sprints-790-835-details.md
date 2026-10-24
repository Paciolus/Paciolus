# Sprints 790–835 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-24.

---

### Sprint 835: Sources & Methodology — every rule says where it comes from
**Status:** COMPLETE 2026-10-24 — CEO direction: "share information from the authorities", be as transparent as possible.

- [x] `frontend/src/content/methodology-sources.ts`: all 18 tools plus the composite score — 219
      rules, each with the rule applied, its key thresholds, a kind (required by a standard or
      statute / described by a standard / published method / **Paciolus convention**), the cited
      codes and a note on which numbers are ours. CI (`test_methodology_sources.py`) checks every
      code is registered, every tool is covered, every testing tool covers every engine test, and
      every code maps to an issuer.
- [x] `content/authorities.ts` + public page **`/sources`** (footer link, sitemap, dark theme): the
      stance ("Paciolus is not an accounting or auditing authority"), the four kinds with counts, each
      issuer with where to read it and how to access it, and a tool-by-tool table.
- [x] Every tool page's citation footer and every testing memo's disclaimer now say Paciolus is not a
      standard-setter, that standards are cited so the reader can consult the source, and that
      thresholds no standard sets are Paciolus conventions, with a pointer to `/sources`.
- [x] Registry rows added for sources the catalog cites (5 U.S.C. §6103, Iglewicz & Hoaglin 1993,
      ASC 850, IRC §3101/§3121/§402(g)/§223(b)(3)/§6049/§6050N/§6045(f)); duplicates with Sprints
      825/826 merged.

**Found while cataloguing (fixed in Sprint 837):** existing code and memos overstated or misattributed
about twenty citations — holiday/weekend postings attributed to ISA 240, unverifiable fraud statistics
shown to customers, confirmation standards (ISA 505 / AS 2310) cited for internal record matching,
paragraph numbers that do not hold up, ASC 230 cited for a forecast, and a 1099 threshold that
2025 legislation appears to have changed.

**Commit SHA:** recorded on merge.


---

### Sprint 832: Equity in the ratios includes unclosed current-period earnings
**Status:** COMPLETE 2026-10-24 — CEO decision 1.
**Priority:** P1 — ROE was overstated, and for a loss-making client leverage was understated.

- [x] `ratio_engine.unclosed_earnings_adjustment()` is the one rule: unclosed earnings = revenue −
      expenses; 0 on a closed TB; and 0 when the totals already balance as A = L + E without them
      (closed equity sent with income-statement figures — Paciolus convention, so nothing is counted
      twice). `validate_balance_sheet_equation` calls the same function.
- [x] Debt-to-equity, ROE (both ends of the prior-period average), equity ratio, DuPont multiplier
      and its ROE cross-check, common-size equity %, the going-concern leverage and net-liability
      tests, and the financial-statements PDF D/E all use effective equity.
- [x] Disclosed beside the ratios: "Equity includes $X of unclosed current-period earnings" in the
      Key Metrics panel, the financial-statements PDF and the Excel ratio sheet; API `analytics`
      gains `equity_includes_current_earnings`, `effective_equity`, `equity_basis_note`. Basis cited
      at topic level (ASC 505 / IAS 1; closing entries move net income to retained earnings).

**Known effects:** saved history and trends mix bases at this sprint (a step change). The equation
check can now read "balanced" where A = L + E holds and revenue ≠ expenses; the separate debit/credit
check still catches a TB that does not balance. Raw `total_equity` variance analysis and
percentage-of-equity materiality are unchanged (not ratios).

**Commit SHA:** recorded on merge.


---

### Sprint 833: SoD single-HIGH tiering; bank-rec split search bounded
**Status:** COMPLETE 2026-10-24 — CEO decision 7 and code-health decision 2.

- [x] **SoD:** any HIGH-severity conflict tiers the user high (score unchanged); the user result
      carries `risk_tier_reason`, users sort by tier first, the CSV gains a "Tier Basis" column and
      the results view explains the floor as a Paciolus convention (COSO 2013 framing, not a COSO
      requirement).
- [x] **Bank rec (Sprint 815 item 2):** Sprint 829 had already made tolerance 0 mean same-day. What
      remained slow was many same-day or undated candidates. Lossless trim first (a single item
      larger than the bank amount cannot be part of a split), then a cap of 20 nearest-dated
      candidates (`split_match_max_candidates`, Paciolus convention). The worst case (200 × 200 on
      one day) went from effectively never finishing to ~1.3s. Nothing is cleared by the cap: a
      capped item stays an open exception flagged `split_search_limited`, and the result, memo and
      page disclose the bound. The date window was deliberately **not** widened — a wider default
      would clear more exceptions.
- [x] **Bug fixed:** the response schema did not allow `match_type: "split"`, so any reconciliation
      with a split match returned a 500. Schema and frontend now handle splits.

**Not fixed (filed here):** the bank-rec CSV export omits split matches; `BankRecResponse` does not
declare `suggested_journal_entries`, so FastAPI drops them.

**Commit SHA:** recorded on merge.


---

### Sprint 825: Sampling methodology decisions (S3, S6)
**Status:** COMPLETE 2026-10-24 — CEO decision 5 (conservative reading); practitioner confirmation items below.

- [x] **S3 — a clean sample still has an upper limit.** MUS already reported basic precision
      (zero-error confidence factor x sampling interval, AICPA Audit Sampling Guide). The random path
      now does too: BP = population value x CF(0) / n, with n = items actually evaluated. That
      substitution of average dollars per item for the interval is a Paciolus convention, chosen
      because it matches how the tool sizes a random sample (n = BV x CF / TM): a clean sample of the
      designed size passes, a smaller one fails. Worked case in the tests: $1M population, TM $50K,
      95% — clean n=20 gives $150,000 (fail; the old code said $0, pass), clean n=60 gives $50,000.
- [x] **S6 — understatements bounded separately, never netted.** Each direction gets its own upper
      limit (BP + projected + incremental) and the conclusion fails if either exceeds tolerable
      misstatement. Existing response fields keep their names and now mean the overstatement side;
      `understatement_*` fields added. Understatement taintings are not capped at 100% (Paciolus
      convention, the conservative reading).
- [x] Memo prints both limits, a calculation section per direction and the source of each formula.

**For a practitioner to confirm:** the random-method basic precision formula and the retained
CF/sqrt(n) allowance; uncapped understatement taintings; stratified random evaluation is still not
modelled. **One way the result can be lower than before:** with mixed errors under MUS, the
overstatement limit alone can be below the old figure, which wrongly counted understatements as
overstatements — the two-sided test is the AICPA approach the CEO chose.

**Commit SHA:** recorded on merge.


---

### Sprint 790: The monthly upload allowance is not enforced on any paid tier
**Status:** COMPLETE 2026-10-24 — CEO decision 9. Summary first; the original analysis follows.

- [x] One successful analysis run = one upload (a two-file run costs one; a 4xx, refused or failed
      run costs nothing). `maybe_record_tool_run(..., consumes_upload=True)` increments on success,
      passed only by the 13 functions that call `check_upload_limit` — all of them already reached the
      recorder, so no route needed rewiring. The increment is one atomic `UPDATE ... SET n = n + 1`.
- [x] Bulk upload consumes nothing (it analyses nothing); its per-file increment is removed.
- [x] Alembic `e7a90c3d5b18` resets every subscription counter to 0 at deploy (single head).
- [x] Symmetry guard (AST over `routes/`, `shared/`, `services/`): every limit-checking function
      reaches an increment on success, only those use the flag, and a failed run never does.
- [x] **Two lock-out bugs fixed on the way:** renewals never reset the counter (the hourly job only
      saw rows already past period end; the Stripe renewal webhook moves it within seconds) — the
      sync now zeroes the counter when the period start moves forward; and past-due/canceled
      subscriptions would have stayed locked — the quota check now uses the subscription counter
      only for active/trialing subscriptions and counts everyone else like Free.

**Effect:** paid caps are now enforced for the first time — 100 runs/month on Solo, 500 on
Professional.

**Commit SHA:** recorded on merge.

**Original analysis (2026-10-21):**
**Priority:** **P1** — revenue-relevant and advertised. Every paid tier's headline quota is
unenforced.
**Source:** PR #182 review finding, verified 2026-10-21. It falsified a claim in Sprint 789.

`check_upload_limit` **reads** `Subscription.uploads_used_current_period` and raises 403 when it
is at the cap. `increment_upload_count` is the only thing that writes it, and its sole caller in
the repository is `routes/bulk_upload.py:154`.

So a Solo, Professional or Enterprise subscriber's counter never moves on normal tool use, and
the advertised allowances — **100/mo (Solo), 500/mo (Professional)**, stated on the pricing page,
in the Terms of Service tier table and in `UpgradeModal` — are not enforced at all. The gate
exists on roughly fifty upload endpoints and is inert on every one of them for paying users.

**Free tier is the exception, and the asymmetry is the giveaway.** With no `Subscription` row the
check falls back to counting `ActivityLog` rows for the current month, which genuinely grows. So
the 10-upload free cap works while the paid caps do not — the tier that generates no revenue is
the only one being metered.

**Two consequences worth stating:**
- This is why Sprint 741a concluded its `reset_upload_quotas` fix had "no realized impact beyond
  there being no paying subscribers yet." The deeper reason is that the counter it resets is
  almost never incremented, so a subscriber would never have hit the cap for the reset to matter.
- Enforcement has never been exercised end to end for a paid tier, so turning it on is a
  behaviour change for existing accounts, not just a bug fix.

**Scope:**
1. Decide the metering unit first, and write it down. "Upload" currently means different things:
   one file, one analysis run, or one bulk-upload member file (the only path that counts today).
   A tool accepting two files in one request — AR aging TB + sub-ledger, three-way match — must
   not silently cost two.
2. Increment on **success**, not on request. A 400 from malformed input should not consume
   allowance. That argues for the same position as the tool-run recorder, which already runs
   there.
3. Preferred shape: fold the increment into `maybe_record_tool_run`'s success path rather than
   adding a call to fifty routes. The recorder already knows the user, the tool and whether the
   run succeeded, already owns a commit after Sprint 787b, and is already called from every
   metered surface. Verify that mapping covers every endpoint that calls `check_upload_limit`
   before relying on it — a route that checks the limit but never records a run would stay
   unmetered and the asymmetry would be invisible again.
4. A test asserting check-and-increment are symmetric: every endpoint depending on
   `check_upload_limit` must reach an increment on its success path. Mechanical, and it is the
   guard whose absence let this sit.

**CEO decision needed before step 2 ships:** existing accounts have arbitrary counter values.
Enforcing from today risks locking out an account whose counter was left high by bulk upload.
Options: reset all counters at deploy; enforce from the next billing period; or enforce
immediately and handle exceptions manually. No paying subscribers yet, so this is cheap now and
expensive later.

**Commit SHA:** TBD.


---

