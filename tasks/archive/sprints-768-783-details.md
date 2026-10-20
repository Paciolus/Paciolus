# Sprints 768–783 Details

> Archived from `tasks/todo.md` Active Phase on 2026-10-20.

---

### Sprint 768: Targeted security remediation — auth body-token, audit-chain key separation, /health/live fingerprinting, slowapi posture
**Status:** COMPLETE — landed on branch `sprint-768-security-remediation-auth-config-health-rl`.
**Priority:** P1 (security).
**Source:** External targeted security remediation brief (2026-04-30) — four findings flagged for immediate fix with minimal-change discipline.

**What landed:**

1. **Browser-default auth responses no longer carry `access_token` in JSON.**
   - `AuthResponse.access_token` → `Optional[str] = None` (`backend/auth.py`).
   - `/auth/register`, `/auth/login`, `/auth/refresh` only emit a JSON `access_token` when the caller sends `X-Token-Response: bearer` (default OFF; explicit non-browser API-client opt-in). Cookie issuance (`_set_access_cookie`, `_set_refresh_cookie`) unchanged — the HttpOnly cookie remains the browser carrier.
   - Frontend (`AuthSessionContext`) now uses `data.user` as the success marker instead of `data.access_token`; cookie auth via `credentials: 'include'` is the load-bearing path. `AuthResponse` TypeScript type marks `access_token` optional.
   - 4 new pytest tests pin the opt-in contract; existing register/login/refresh assertions updated.

2. **`AUDIT_CHAIN_SECRET_KEY` cryptographic separation enforced in production.**
   - `backend/config.py` hard-fails when the key is missing/blank in production, *and* when it equals `JWT_SECRET_KEY` (sharing collapses the SOC 2 CC7.4 boundary and ties audit-chain integrity to JWT rotation cadence).
   - Non-production keeps the dev fallback but emits an explicit `WARNING` per boot.
   - 4 new subprocess-based tests in `test_security_hardening_2026_04_20.py::TestAuditChainKeySeparation` cover both failure modes plus the happy path.

3. **Public `/health/live` no longer exposes exact platform version.**
   - `LivenessResponse` no longer includes `version`; `/health/ready` (operationally scoped) continues to expose it.
   - Reduces external fingerprinting surface — orchestrator restart decisions don't need version, scanners no longer pin exploit attempts to a known build.

4. **slowapi unmaintained-status surfaced explicitly + fail-closed coverage strengthened.**
   - `shared/rate_limits.py` emits a startup banner on import: `WARNING` in production, `INFO` in non-production. Substring `"slowapi is unmaintained"` is intentionally pinned for monitoring rules.
   - New `test_rate_limit_strict_mode.py::TestStrictModeFailClosedRedisStorageInit` covers the `RedisStorage` constructor-raises path under strict mode.
   - New `TestSlowApiUnmaintainedWarning` asserts severity-by-env semantics.
   - `docs/runbooks/rate-limiter-modernization.md` adds an "Operator Posture" section documenting the temporary acceptance posture and the entry criteria for the deferred migration sprint (canary failure on green main, slowapi CVE ≥ 7.0, or Starlette major-version incompat).
   - Full slowapi → custom-Starlette migration explicitly **deferred** in this patch (123 decorator sites, no CVE, `limits` engine is actively maintained and pinned `>=3.0.0`).

**Files touched (13):**
- `backend/auth.py`, `backend/routes/auth_routes.py`, `backend/config.py`, `backend/routes/health.py`, `backend/shared/rate_limits.py`
- `backend/tests/test_auth_routes_api.py`, `backend/tests/test_health_api.py`, `backend/tests/test_rate_limit_strict_mode.py`, `backend/tests/test_security_hardening_2026_04_20.py`
- `frontend/src/types/auth.ts`, `frontend/src/contexts/AuthSessionContext.tsx`, `frontend/src/__tests__/AuthContext.test.tsx`
- `docs/runbooks/rate-limiter-modernization.md`

**Verification:**
- `cd backend && python -m pytest -q` → **8,685 passed, 0 failed** (829s).
- `cd backend && python -m pytest tests/test_auth_routes_api.py tests/test_auth_parity.py tests/test_auth_security_responses.py tests/test_health_api.py tests/test_health_redis_r2.py tests/test_rate_limit_*.py tests/test_security_hardening_2026_04_20.py tests/test_audit_chain.py -q` → **216 passed, 0 failed**.
- `cd frontend && npm test -- --watch=false` → **207 suites, 2,013 tests, 0 failed**.
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npm run build` → exit 0; routes correctly dynamic (`ƒ`).

**Out of scope / deferred:**
- Server-side gating of the `X-Token-Response: bearer` opt-in to non-browser User-Agents — out of minimal-change scope; cookie remains authoritative regardless.
- Full slowapi migration — entry criteria documented in the runbook; defer until trigger fires.

**Commit SHA:** `fbec7a61` (branch `sprint-768-security-remediation-auth-config-health-rl`).


---

### Sprint 774: Rate-limit storage outage resilience (P0 production restore)
**Status:** COMPLETE — commit `8601c4ef` on branch `sprint-774-rate-limit-outage-resilience` (was `e848d3c2` before the branch was rebased onto `main`) (not yet pushed/merged; production is restored but still runs `51906004`, so the resilience fix itself is not yet deployed).
**Priority:** P0 (production was down).
**Source:** Production outage discovered 2026-10-19 during a status review after ~5.5 months of repo dormancy (last commit 2026-05-01).

#### What was actually wrong (two independent faults)

1. **`AUDIT_CHAIN_SECRET_KEY` was never set on Render.** The 2026-04-06 hotfix introduced the variable with a silent dev fallback to `JWT_SECRET_KEY`; Sprint 768 correctly turned that fallback into a production hard-fail — but nobody set the variable. The Sprint 768 deploy (`c58cbbb5`, 2026-04-30 22:45 UTC) therefore exited 1 at startup. Render kept the previous instance (Sprint 763, `89ab7902`) serving, so the failure was invisible, and **Sprint 768's P1 security fixes never reached production.** PR #129, merged 80 minutes later, never deployed at all — its files were outside Render's `backend` rootDir, so the commit was ignored.
2. **The Upstash Redis host stopped resolving** (`Error -2 ... Name or service not known`). Every rate-limited route — i.e. the whole API including `/health`, `/health/live`, `/health/ready`, `/metrics` — returned HTTP 500. Because the probes 500'd too, nothing reported why; Render showed the service healthy and unsuspended throughout.

#### Two latent bugs found while fixing it

- **The fail-closed guarantee never worked.** `limits`' `Storage.check()` signals failure by *returning False*, not raising (its body is `try: return ping() except: return False`). `_resolve_storage_uri` only caught exceptions, so a dead backend was silently treated as healthy at boot. The Sprint 696 tests passed only because they mocked `check()` to raise — something real `RedisStorage` never does. The tests encoded a false model of the library.
- **`scripts/smoke_test_render.sh` could never pass.** It registers `smoke-test-<ts>@paciolus.test`, and `email-validator` rejects `.test` as a special-use/reserved TLD, so `/auth/register` returned 422 every time. The post-deploy verification gate had been non-functional. It also still asserted `access_token` in the register/login JSON, which Sprint 768 made opt-in behind `X-Token-Response: bearer`.

#### Conflict Loop — the posture tension

**Tension:** Sprint 696 (2026-04-20) deliberately chose fail-closed — refuse to start rather than under-enforce rate limits — and built a dated break-glass override to go with it. This sprint makes degradation the default, which reverses that decision.

**Steel man for fail-closed:** rate limiting is the only thing between the public internet and expensive audit/export endpoints. Degrading to per-process counters on a multi-worker deployment gives each worker its own bucket — effectively N-times the intended limit. Refusing to boot forces an operator to fix the real problem instead of running indefinitely degraded, and the override exists precisely so degradation is a *deliberate, logged, time-boxed* choice.

**Why degrade still wins:** the incident is the counter-evidence. Fail-closed converted a cache outage into a 5.5-month total outage of a paid product, with no alarm and — critically — **no self-heal path**: the process exits and the orchestrator restart-loops forever. The override requires a human who already knows to look. Meanwhile slowapi's fallback enforces the *same limit values* in-process and restores Redis automatically within a few requests, and at `numInstances: 1` the enforcement delta is exactly zero. Fail-closed bought nothing here and cost everything.

**Synthesis (what shipped):** keep both postures, make the choice explicit rather than implicit in strict mode, default to `degrade`, and make degradation impossible to miss. Rate limiting is an abuse control, not an integrity control; brief under-enforcement beats unavailability *provided* it is loud and self-healing.

#### What landed

- **`backend/config.py`** — new `RATE_LIMIT_STORAGE_FAILURE_POLICY` (`degrade` default, or `fail_closed`), validated with a hard-fail on a bad value. Deliberately separate from `RATE_LIMIT_STRICT_MODE`, which keeps its original meaning: Redis must be *configured* (still a production hard-fail when `REDIS_URL` is unset).
- **`backend/shared/rate_limits.py`**
  - `Limiter(..., in_memory_fallback_enabled=True)` — the core fix. A storage error now degrades to in-process counters instead of raising. This is not `swallow_errors`: limits stay enforced while degraded.
  - `_resolve_storage_uri()` now inspects the **return value** of `check()`, not just exceptions.
  - Distinguishes *unreachable* (keep the Redis URI so slowapi's re-probe can self-heal) from *unusable URI* (degrade to `memory://`, since slowapi would crash at import on the same URI and a bad URI cannot recover anyway).
  - New `get_storage_health()` reporting configured vs. live backend, reading slowapi's `_storage_dead` live so it clears on recovery.
- **`backend/routes/health.py`** — `/health/ready` reports a `rate_limit_storage` soft dependency; degradation downgrades overall status to `degraded` but still returns **200** (503 would evict a healthy instance from the load balancer over a cache outage). Corrected the `/health/live` "zero I/O" docstring, which was false — it passes through the limiter.
- **`scripts/smoke_test_render.sh`** — `@paciolus.test` to `@example.com` (RFC 2606, no MX, so it bounces rather than reaching anyone); register and login now send `X-Token-Response: bearer`.
- **`docs/runbooks/rate-limiter-modernization.md`** — new "Storage Outage Posture" section (incident, policy table, detection, Redis restore procedure); Sprint 696 section marked partially superseded.

#### Production actions taken (2026-10-19)

- Set `AUDIT_CHAIN_SECRET_KEY` on Render (fresh 64-hex key). Safe to introduce: `verify_audit_chain` already tries the audit-chain key first and falls back to `JWT_SECRET_KEY` for pre-rotation records, so existing entries still verify while new ones get real domain separation.
- Provisioned Render Key Value `paciolus-ratelimit` (`red-dbb2gdqjnfac739l4p5g`, free plan, **virginia** — same region as the service, `allkeys_lru`) and repointed `REDIS_URL` at its internal URL. A same-provider private hostname removes the cross-provider DNS dependency that caused the outage.
- Deploy `dep-dbb2glcs728c73a67s5g` went **live**; production now runs `51906004`, which includes Sprint 768 at last.

**Verification:**
- Production: all four health probes 200; `/health/redis` connected (5.76ms); DB 9.96ms. Full auth round-trip green against live prod — register, `/auth/me`, login, wrong-password 401, uppercase-email login, logout, post-logout 401 (14/14 checks).
- `tests/test_rate_limit_storage_outage.py` — **10 new tests.** Proves a rate-limited route served through a genuinely dead Redis returns 200, with a control asserting the same setup fails hard *without* the fallback (so the test cannot silently stop proving anything), plus a test that limits are still enforced while degraded.
- `tests/test_health_api.py` — 3 new tests for the `rate_limit_storage` dependency and degraded-status reporting.
- 4 pre-existing tests updated to the new posture (they asserted the old fail-closed behavior); intent preserved and documented in each.
- Targeted runs: 38 rate-limit, 24 health, 116 security/auth passed.

**Out of scope / follow-ups:**
- Replacing slowapi entirely — unchanged; triggers still documented in the runbook.
- `jq` is unavailable on the Windows dev box, so `smoke_test_render.sh` still cannot run there. The fixes are correct but were verified via an equivalent Python harness. Consider a `jq`-free rewrite.
- Free-plan Key Value has no persistence, so `impersonation_revocation` JTI sets are lost on restart (they already were — it falls back to in-memory). Worth a paid plan if cross-restart revocation durability matters.
- **External uptime monitoring** — nothing alerted for 5.5 months. This is the single highest-value follow-up; see Sprint 775.


---

### Sprint 775: External uptime monitoring + deploy-failure alerting
**Status:** COMPLETE (in-repo half). The external-monitor signup remains a CEO action — see "Residual" below.
**Priority:** P1. The Sprint 774 outage was not caused by missing monitoring, but it lasted 5.5 months because of it.
**Source:** Sprint 774 post-incident.

Two separate blind spots, both of which must close:

1. **Nothing watched the service.** No external probe, so a total API outage was indistinguishable from a quiet period. Add an external HTTP monitor against `/health/ready` that alerts on non-200 **and** on `status != "healthy"` (Sprint 774 made degradation visible in the body; an uptime check that only looks at the status code will miss it). Free options sufficient at this scale: Better Stack, Healthchecks.io, UptimeRobot.
2. **Nothing watched deploys.** The Sprint 768 deploy failed and Render kept serving the old image, so a failed deploy looked identical to a successful one from outside. Render has `notifyOnFail: "default"` on the service — confirm where those notifications actually land and that the address is monitored. A failed deploy on `main` should page.

Also worth filing: the Sprint 768 security fixes sat undeployed for 5.5 months because nobody verified the deploy landed. Post-merge verification should assert that the live deploy SHA equals `main`, not merely that CI was green.


---

### Sprint 783: Zero-Storage documents contradicted each other
**Status:** COMPLETE.
**Priority:** P2 — **downgraded from P1 on re-examination.** No counsel review required; see "Why this did not need a lawyer" below.
**Source:** Discovered 2026-10-19 while verifying the backup blast radius (see Sprint 778).

`docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` §2.2 enumerates exactly **ten** controlled-storage exceptions: Users, Clients, Activity Logs, Diagnostic Summaries, Tool Sessions, Engagements, Tool Runs, Follow-Up Items, Subscriptions, Billing Events.

Two tables persist client financial content and are **not** among the ten:
- **`uncorrected_misstatements`** — `accounts_affected_json` holds a JSON list of `{account, debit_credit, amount}`, plus `fs_impact_net_income` / `fs_impact_net_assets` as `Numeric(19,2)`.
- **`analytical_expectations`** — `expected_value`, `expected_range_low/high`, `precision_threshold_amount`, `result_actual_value`, `result_variance_amount`.

The same document states, without qualification:
- §2.1: *"What Is Never Stored: Raw uploaded files, **line-level account balances**, individual transaction details"*
- Glossary: *"No persistence of line-level financial data — raw uploaded files, **individual account balances**, and transaction details are never written to disk or database"*
- Data-class table: *"**Individual Account Names** | ❌ Never Stored | Ephemeral | 'Accounts Receivable'"*

`accounts_affected_json` stores individual account names with amounts. That is a direct contradiction of the published table.

**The design position is defensible; the documentation is not.** `uncorrected_misstatements_model.py:9` declares a deliberate "ZERO-STORAGE EXCEPTION" reasoned as *"persists only the auditor's documented decisions… a snapshot workpaper of audit decisions, not a database join over raw tool output."* That is a reasonable distinction — auditor-entered conclusions are a different data class from parsed client uploads. The problem is that no public document records the distinction, so a CPA reading the policy would reasonably conclude their client's account names never touch the database.

**One caveat weakens the defence for the second table:** `analytical_expectations.result_actual_value` is documented as populated *"manually or via 728c tool-wiring auto-persist"*. An auto-persisted actual is upload-derived, not auditor-entered, so the "auditor's own decisions" rationale does not fully cover it.

**Scope:**
1. Decide the canonical position: either (a) document both tables as controlled-storage exceptions with the auditor-entered rationale stated explicitly and the data classes enumerated, or (b) stop persisting the account-level detail and hold the SUM/expectations in session only.
2. If (a): update `ZERO_STORAGE_ARCHITECTURE.md` §2.2 and its data-class table, the Privacy Policy retention table, the DPA, and the Trust page. Qualify "Individual Account Names — Never Stored" to distinguish parsed uploads from auditor-entered workpaper entries.
3. Audit `result_actual_value` auto-persist specifically and decide whether upload-derived actuals may be written at all.
4. Add a test asserting every model with a monetary column is listed in the compliance doc's exception table, so this cannot drift again — the same class of guard that now protects the AS 1215 citation.

#### Correction to the original finding

The first version of this entry characterised the persistence as **undisclosed**. That was wrong, and checking the compliance folder more carefully showed why:

- `docs/04-compliance/isa-450-coverage.md` carries an "Architectural decision: snapshot model" section, a data-model table stating `UncorrectedMisstatement` is **"Persisted (Postgres / SQLite)"** with retention "engagement lifecycle", and a dated **"CEO-confirmed 2026-04-26"** decision.
- `docs/04-compliance/isa-520-coverage.md` states `AnalyticalExpectation` is **"Persisted"** and that it "holds **only** the auditor's documented expectation and the comparison result — never raw transactional data."

That second line also resolves the caveat raised about `result_actual_value` auto-persist: an auto-captured actual *is* "the comparison result", which the doc already covers. **Caveat withdrawn.**

So the defect was never undisclosed practice. It was that `ZERO_STORAGE_ARCHITECTURE.md` **contradicted its own compliance folder** — making absolute claims in one document that two sibling documents correctly qualified. That is a document-consistency defect, not a compliance exposure, which is why it drops to P2.

#### Why this did not need a lawyer

CEO asked (2026-10-20) whether renaming "Zero-Storage" to something less absolute would resolve it. It would not, and the term was not the problem:

- A defined term with stated carve-outs is ordinary and defensible; the document already defined one.
- Renaming would not fix a *factual* row asserting account names are never stored while `accounts_affected_json` stores them. The false statement survives any rename.
- The surface is large and legally sensitive: **217 occurrences across 20 compliance files**, including Terms (8), Privacy (13), DPA (9) and Security Policy (22), plus 140 frontend files. Editing the core differentiator across four legally-operative documents is a far larger risk than the inconsistency it would address.

The useful half of the question was that **"Zero" is an absolute, and the absolutes are what forced the document into claims it could not keep.** So the fix tightened the definition once and removed the absolutes — no rename, no churn through legal documents, and nothing left for counsel to adjudicate because the documents now simply state what is true.

#### What landed

**`docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` — five edits:**
1. §1.1 Definition now names three data classes explicitly in a table — upload-derived detail (never persisted), aggregate metadata (persisted), practitioner-entered workpaper entries (persisted, engagement lifecycle) — and states that the distinction *is* the term's whole scope.
2. §2.1 Key Points: "Never Stored" qualified to "**parsed from an upload**"; practitioner-typed conclusions added to "What Is Stored".
3. §2.1 Data Classification Matrix: the contradicting `Individual Account Names | ❌ Never Stored` row split into **Account Names Parsed From an Upload** (never stored) and **Account Names Typed by the Practitioner** (stored, soft-delete), plus explicit rows for both ISA 450 and ISA 520 entities.
4. Glossary: Zero-storage re-scoped to upload-derived detail; new **Practitioner-entered workpaper entry** term defined.
5. §2.2 Controlled Storage Exceptions: **10 → 12** subsections, adding Uncorrected Misstatements and Analytical Expectations with fields stored, why each falls outside the exclusion, what is *not* stored, and cross-references to the two coverage docs.

**Point-of-entry disclosure (the gap that actually mattered most).** Compliance docs were already correct; users read UI. Both entry surfaces now say so, matching the house pattern in `AdjustmentSection.tsx`:
- `CreateMisstatementModal.tsx` — "Saved to this engagement and kept until you delete it. The account names and amounts you enter here are stored; uploaded trial balances are not."
- `AnalyticalExpectationsPanel.tsx` — "…Your expectation and the comparison result are stored; the underlying trial balance rows are not."

**`backend/tests/test_zero_storage_disclosure.py` — 6 tests, the tie that was missing.** Introspects every mapped model for `Numeric` columns or account/amount-named columns and asserts each appears in §2.2. Six models qualify (`activity_logs`, `analytical_expectations`, `diagnostic_summaries`, `engagements`, `tool_runs`, `uncorrected_misstatements`) and all six are documented, so `KNOWN_UNDISCLOSED` ships **empty** — full enforcement from day one. Also pins the two Sprint 783 tables by name and forbids the unqualified "Account Names | Never Stored" row from returning.

**Verification:** guard suite 6/6. Deliberately regression-tested by deleting the Uncorrected Misstatements subsection — the guard failed with the offending columns named, then passed again on restore. `npx tsc --noEmit` exit 0; 4 suites / 36 tests covering the two touched components pass.

**Residual:** none requiring counsel. The term "Zero-Storage" is retained deliberately — it is accurate as now defined, and it remains the product's genuine differentiator.


---

### Sprint 777: Dependency pinning strategy — decide the `==` vs `>=` rule
**Status:** COMPLETE — **option 3 chosen** (explicit split with a written rule). The rule is now documented in-file at the top of `backend/requirements.txt`.
**Priority:** P2. Not urgent, but it is the upstream cause of the 2026-10-19 CVE gate failure and it also changes how Sprint 761 should be executed.
**Source:** 2026-10-19 CVE sweep (see Hotfixes).

`backend/requirements.txt` mixes two incompatible pinning philosophies with no stated rule, and the mix is why the CI compliance gate went red:

- **Exact pins (`==`)** — `fastapi`, `PyJWT`, `python-multipart`, `sqlalchemy`, `stripe`, `pydantic`, `pandas`, `reportlab`, `uvicorn`, … Reproducible, but they rot silently: a CVE published against the pinned version sits there until a human bumps it. PyJWT and python-multipart were the **only** two packages `pip-audit` flagged in CI, and they were exact pins.
- **`>=` floors** — `cryptography>=46.0.7`, `pillow>=12.2.0`, `pypdf>=6.10.0`, `pyasn1>=0.6.3`, `werkzeug>=3.1.8`, `bcrypt>=5.0.0`, `argon2-cffi>=23.1.0`. Each floor's trailing comment names the CVE it was raised for. These self-heal, because every fresh `pip install -r requirements.txt` (CI and the production Docker build) resolves to the latest release — but that also means **production can take an unreviewed upstream major at any time**, with no lockfile and no record of what actually shipped.

Evidence both halves of the tradeoff are live: a `pip-audit` of the long-lived `backend/venv` (pinned-in-place at the floor versions) reports advisories against `cryptography` 46.0.7, `pillow` 12.2.0, `pypdf` 6.10.2, `pyasn1` 0.6.3 and `werkzeug` 3.1.8 — i.e. every floor value is now itself vulnerable. A fresh resolve almost certainly avoids all of them. So the floors are protecting CI/prod while leaving no evidence of what was tested.

**Decide one of:**

1. **Exact pins everywhere + a lockfile + automated bump PRs.** Fully reproducible; requires Dependabot (already configured, 15 PRs open) to actually be merged on a cadence, or the rot problem generalizes to every package.
2. **Floors everywhere, with `pip freeze` captured per deploy as the evidence record.** Keeps CVE currency; needs a recorded resolution so "what shipped" is answerable after the fact.
3. **Explicit split with a written rule** — e.g. exact-pin the framework/runtime surface where a silent major is dangerous (`fastapi`, `pydantic`, `sqlalchemy`, `pandas`), floor the leaf security libraries where currency matters more (`cryptography`, `pillow`, `pypdf`). This is roughly what exists today; the work is to state it, justify each classification in-file, and add the missing piece: a scheduled job that re-audits the exact-pinned set, since that is the half that cannot self-heal.

**Decision (2026-10-19): option 3 — explicit split, written down.**

Why not the others. Option 1 (exact-pin everything + lockfile) generalises the exact-pin rot problem to all 32 requirements and makes CVE currency entirely dependent on Dependabot PRs actually being merged on a cadence — and the current state of that cadence is 15 open Dependabot PRs, the oldest from 2026-04-13. Option 2 (floors everywhere) would let an unreviewed upstream major land straight in the production Docker build for `fastapi`, `pydantic`, `sqlalchemy` and `pandas`, where a silent behavioural change costs far more than a late CVE patch.

**The rule, as written into `backend/requirements.txt`:**
- `==` **exact pin** for the framework/runtime surface, where an unreviewed upstream change is more dangerous than a late CVE patch: web framework, data layer, migrations, money, document generation, scheduler, APM. 17 entries.
- `>=` **floor** for leaf libraries consumed through a narrow, stable API, plus the security block at the bottom of the file, where CVE currency matters more than byte-for-byte reproducibility. 15 entries.

**The load-bearing clause** — and the actual lesson of the incident — is recorded alongside it: exact pins **cannot self-heal**, so they are only safe while the weekly `dependency-compliance` pip-audit is enabled **and** green. That job is the sole mechanism able to catch rot in the `==` half of the file. It had been failing for months and was then auto-disabled by GitHub after 60 days of repo inactivity, which is exactly how PyJWT and python-multipart rotted into two red blocking gates that held up all 13 real PRs. The workflow was re-enabled 2026-10-19.

Also recorded in-file: `starlette` deliberately carries **no** constraint, even though it is the HTTP core beneath FastAPI. Because `fastapi` is exact-pinned its permitted `starlette` range is already fixed, so a second constraint would add no reproducibility while risking resolution conflicts on every FastAPI bump.

**Verified:** `requirements.txt` still parses (32 requirement lines, none unparseable) and `pip install --dry-run -r requirements.txt` resolves clean.

**Consequence for Sprint 761 (cryptography 47 major):** its premise — "majors get pinned exact" — is now explicitly **rejected** for this dependency. `cryptography` is a security leaf and stays a floor; converting it to `==` would make the single most security-critical package in the tree (JWT signing, password hashing, TLS evidence chain) rot exactly the way PyJWT did. Sprint 761 should be rescoped to "verify the floor still resolves to a supported, CVE-free major, and raise the floor if not" rather than pinning it.

**Blocks/alters (now resolved — see Decision above):** Sprint 761 proposes pinning `cryptography==47.0.0` exactly, on the stated convention that "majors get pinned exact." Under option 2 or 3 that is the wrong move — it would convert a self-healing floor into a rotting pin on the single most security-critical dependency in the tree (it underpins JWT signing, password hashing, and the TLS evidence chain). Settle this sprint first.

**Also fix while here:** `requirements.txt` has no `starlette` constraint at all, yet it is the HTTP core underneath FastAPI and the long-lived venv shows 5 advisories against `starlette` 1.0.0. It is currently whatever `fastapi==0.136.1` happens to allow. Decide whether the HTTP layer should be constrained explicitly.


---

