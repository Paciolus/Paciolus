# Sprints 733–737 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-27.

---

### Sprint 733: Stripe webhook unit-coverage gap fill (pre-cutover)
**Status:** COMPLETE 2026-04-27. **Revised scope:** 2 real gaps + 1 bonus, not 4. The pre-flight gap analysis discovered `TestWebhookErrorClassification` in `test_billing_webhooks_routes.py` (Sprint 564) already covered 4 of the 5 boundaries Codex's directive listed — only "missing `stripe-signature` header → 400" and "duplicate event-id (IntegrityError) → 200 without double-processing" needed new coverage. Bonus: `is_stripe_enabled() == False` short-circuit. 8/8 webhook tests passing (5 existing + 3 new). No behavior change on `/billing/webhook`.
**Priority:** P2 → bumps to P1 the moment Phase 4.1 cutover schedule firms up. **Landed BEFORE Phase 4.1 (`sk_live_` keys)** as planned — adds the safety net around the handler about to begin processing live revenue.
**Source:** Refactor pass 2026-04-27 (Codex directive, scope-revised after Sprint 710/724 + `## Deferred Items` reconciliation).

**What landed (2 new tests + 1 bonus):**
- `test_missing_signature_header_returns_400` — POST without `stripe-signature` header → 400 + asserts `construct_event` is never called when the header is absent (signature is the gate, not an after-the-fact check).
- `test_duplicate_event_returns_200_without_double_processing` — IntegrityError on dedup INSERT → 200 + asserts `process_webhook_event.call_count == 0`. **Critical for Stripe retry semantics** — if this regresses, duplicate deliveries cause subscription/payment events to double-run.
- `test_stripe_disabled_returns_200_short_circuit` (bonus) — when `is_stripe_enabled()` returns False, webhook short-circuits to 200 without any verification or processing.

**Already covered (no new tests needed):**
- Invalid JSON payload → 400 (`test_invalid_json_payload_returns_400`)
- ValueError from process_webhook_event → 400 (`test_handler_value_error_returns_400`)
- KeyError from process_webhook_event → 400 (`test_handler_key_error_returns_400`)
- Generic exception from process_webhook_event → 500 (`test_handler_operational_error_returns_500`)
- DB error during dedup INSERT → 500 (`test_db_dedup_error_returns_500`)
- Invalid signature (forged HMAC) → 400 (`test_billing_routes.py::test_webhook_invalid_signature`)
- Valid signature happy path → 200 (`test_billing_routes.py::test_webhook_valid_signature`)

**Out of scope (per Deferred Items policy, line 54):** No handler decomposition. The signature-verify / dedup-claim / error-mapping triad stays in-route until bundled with the deferred webhook-coverage sprint flagged in Sprint 676.

**Verification:** 8/8 webhook tests passing in isolation. Existing 3 webhook test files structurally unchanged (only `test_billing_webhooks_routes.py` gained 3 new test methods inside the existing `TestWebhookErrorClassification` class). No behavioral change on `/billing/webhook`.


---

### Sprint 734: Playwright mapping-required upload flow coverage
**Status:** COMPLETE 2026-04-27. New spec `frontend/e2e/trial-balance-mapping.spec.ts` (2 tests) added against the existing Playwright harness. Strategy: mock `**/audit/trial-balance` with a request counter so the first call returns `requires_mapping=true` and the second (with column_mapping in the form body) returns success — the rest of the request stack (auth, settings, engagement context, CSP/CSRF middleware) hits the real backend so the spec exercises the actual FastAPI dependency tree, not just hook-level state.
**Priority:** P3.
**Source:** Refactor pass 2026-04-27. Prerequisite for the deferred `useTrialBalanceUpload` decomposition (Deferred Items, line 55).

**What landed:**
- `frontend/e2e/trial-balance-mapping.spec.ts` — 2 tests:
  1. **Happy path** — file upload → mapping modal renders → user picks all 3 columns → confirm → second upload fires with `column_mapping` in body → modal closes → success. Critical assertion: **exactly 2 uploads happen** (initial + post-mapping). A 3rd request returns 500 from the test mock so debounce-induced dupes surface as a clear test failure rather than silent extra round-trips. Pins the contract that Sprint 738 / future hook decomposition can rely on.
  2. **Cancel path** — file upload → mapping modal renders → user clicks Cancel → modal closes → debounce window passes → assert no second upload fires. Catches the regression class where cancel leaves stale state that triggers a re-run after the user backs out.

- Both tests follow the existing `smoke.spec.ts` skip-pattern (`SMOKE_USER` + `SMOKE_PASS` env-var gate) so they no-op gracefully on external PRs without credentials and run normally in CI / locally with creds.

- `playwright test --list` confirms both tests visible to the runner; `tsc --noEmit` clean.

**Out of scope (per Deferred Items policy, line 55):** No decomposition of `useTrialBalanceUpload`. This sprint *enables* a future decomposition sprint by closing the coverage gap that currently makes the split unsafe — the deferred-items reason explicitly cited "needs Playwright coverage of the mapping-required flow before a split is safe." That coverage now exists.

**Verification:**
- 2 tests visible to `playwright test --list`.
- TypeScript compile clean.
- Existing `smoke.spec.ts` unaffected (separate file, no shared state).
- Tests will run in CI per existing E2E job config (skip-on-missing-creds pattern matches `smoke.spec.ts`).

**Follow-up unblocked:** A future sprint can now decompose `useTrialBalanceUpload` into:
- upload execution
- recalculation/debounce coordination
- progress indicator state
- telemetry side effects
…with confidence that the mapping-required handoff regression class is caught by E2E.


---

### Sprint 735: `require_client_owner` adoption in diagnostics + trends + prior_period routes
**Status:** COMPLETE 2026-04-27. **Path B chosen:** added stricter `require_client_owner` dependency that enforces direct-ownership only (no org-scoped sharing) and adopted it across 7 endpoints. Path A would have silently broadened authorization to org members on diagnostic outputs — a real behavior change Codex's "syntax cleanup" framing assumed away. Path B preserves current semantics exactly and pins the contract with new tests so a future "let's just merge the helpers" attempt fails loudly.
**Priority:** P3.
**Source:** Refactor pass 2026-04-27. Path B decision documented in conversation transcript and `shared/helpers.py::require_client_owner` docstring.

**Pre-flight call-site map (gap analysis, 2026-04-27):**
8 candidate endpoints surfaced across 3 files via `Client.id == ... user_id == ...` grep. 7 are GET/POST path-parameter endpoints fitting `require_client_owner`'s `PathParam` shape. The 8th (`diagnostics.py:213::save_diagnostic_summary`) takes `client_id` from request body — out of scope until/unless the request signature is reshaped.

**Critical decision point surfaced:** `require_client` calls `get_accessible_client` → `is_authorized_for_client` which OR-checks org membership. `clients.py` and `settings.py` already use `require_client` (org-scoped). The 7 candidate endpoints currently use direct-only inline queries. Adopting `require_client` uniformly = behavior change (org members gain access to teammate diagnostic outputs). CEO chose **Path B**: add `require_client_owner` that preserves direct-only behavior. Rationale: behavior change in production should not be an accidental side effect of a refactor sprint; if org-scope policy is later opened to diagnostic outputs, it should be a separate sprint with explicit customer comms.

**What landed:**

1. **New helper** `backend/shared/helpers.py::require_client_owner` — direct-ownership-only FastAPI dependency. Docstring documents the Sprint 735 decision and the explicit boundary against `require_client`.

2. **Adopted in 7 endpoints across 3 files:**
   - `backend/routes/diagnostics.py` — `get_previous_diagnostic_summary` (GET), `get_diagnostic_history` (GET).
   - `backend/routes/trends.py` — `get_client_trends` (GET), `get_client_industry_ratios` (GET), `get_client_rolling_analysis` (GET).
   - `backend/routes/prior_period.py` — `save_prior_period` (POST), `list_prior_periods` (GET).
   - Each endpoint replaced its inline `db.query(Client).filter(Client.id == ..., Client.user_id == current_user.id).first() / if not client: raise 404` block with a `Depends(require_client_owner)` parameter. Endpoints that consumed the `client` object downstream (e.g., for `client.name` in responses) keep the named binding; endpoints that only needed the existence check use `_client` to mark intent.

3. **Contract test** `backend/tests/test_sprint_735_require_client_owner.py` (4 tests):
   - Direct owner gets the client.
   - Unrelated user → 404.
   - **Org teammate of owner → 404** (the key Sprint 735 contract; pinned so a future helper merge fails loudly).
   - Companion: `require_client` (the existing helper) DOES grant org teammate access, confirming the behavioral split is intentional.

4. **Sprint 724 helper-count tracking** updated in `test_refactor_2026_04_20.py::test_json_form_and_client_access_symbols` to include `require_client_owner`.

**Why a fourth helper despite the "prefer moving code, avoid new abstractions" rule:** The rule's escape valve (`tasks/todo.md` 2026-04-20 deferred-items entry) is "revisit only if a fourth helper joins them." This is that fourth helper. The alternative was a hidden behavior change in 7 endpoints. Documented in the helper's docstring so the next reviewer doesn't try to consolidate it back.

**Verification:**
- 386 existing tests passing across diagnostic / trend / prior_period / industry test selection (no regression).
- 4/4 new contract tests passing.
- No change to any response code, header, or body shape.
- Authorization semantics preserved exactly: direct owner gets 200, all other users (including org teammates) get 404, identical to the inline-query behavior the endpoints had before.

**Out of scope:**
- `diagnostics.py:213::save_diagnostic_summary` (client_id from body) — out of scope; would require reshaping the request payload to put client_id in the path. File a separate sprint if appetite emerges.
- Org-scope policy decision for diagnostic outputs — explicitly NOT decided in Sprint 735. If product wants teammates to see each other's diagnostic outputs, file a separate sprint with explicit framing + customer comms.


---

### Sprint 736: `init_db()` schema-patch inventory (read-only research)
**Status:** COMPLETE 2026-04-27 — deliverable landed at `docs/03-engineering/init-db-inventory.md`. Recommendation: **(b) consolidate behind Alembic-only**, executed via Sprint 737 below. 7 of 10 branches classified `migration-disguised-as-init`; all are dead code in production today (Sprint 544c wired `alembic upgrade head` into Dockerfile CMD) and in CI (`conftest.py` uses `create_all()`). Patches only fire on a stale local dev SQLite path that bypasses both. CEO authorized pre-4.1 execution after blocker audit found no legitimate technical dependencies.
**Priority:** P3 (research-only).
**Source:** Refactor pass 2026-04-27, scope-narrowed from Codex's "startup-path safety hardening" directive after evidence the directive was overscoped.

Read-only inventory of `backend/database.py::init_db()` branches. Classify each as:
- `idempotent-init` (legitimate startup)
- `schema-patch` (ALTER TABLE / ADD COLUMN against existing tables)
- `migration-disguised-as-init` (schema-patch that references a specific Alembic revision and exists because Alembic isn't running on startup)

**Deliverable:** `docs/03-engineering/init-db-inventory.md` — classification table, references to the Alembic revisions involved, cost/risk profile, and a recommendation choosing exactly one of:
- (a) keep current dual-path (Alembic + in-process patcher),
- (b) consolidate behind Alembic-only with a startup migration-version assertion,
- (c) leave alone with documented rationale.

**Out of scope (per "prefer moving code, avoid new abstractions" rule):** No code changes. No structural rewrite of DB bootstrap. No migration-policy decision in this sprint — the inventory is the deliverable; the policy decision is a follow-up sprint if appetite emerges.

**Verification:** Doc exists, classification covers every branch in `init_db()`, recommendation is one of (a)/(b)/(c) with explicit reopen criteria.


---

### Sprint 737: `init_db()` Alembic consolidation (pre-4.1)
**Status:** COMPLETE 2026-04-27. Verification gate passed (9-of-9 last deploys ran `alembic upgrade head`); 7 patch blocks deleted (`backend/database.py` 360→234 lines); CI drift test added at `backend/tests/test_alembic_models_parity.py`; CONTRIBUTING.md gained "Database Migrations" section. Drift test surfaced **pre-existing tech debt** (4 model-defined tables + 6 model-defined columns with no Alembic migration) — allow-listed in the test with explicit reasons + filed as Sprint 738 below for resolution. Allow-list is the *test passing today, full parity enforced as Sprint 738 closes each item out*.
**Priority:** P3 (dead-code removal + drift detection). No customer-visible behavior change.
**Source:** Sprint 736 inventory recommendation (b). Reverses the conservative (c) framing once Sprint 544c + Dockerfile evidence confirmed the in-process patches are dead code in production.

Consolidate database bootstrap behind Alembic-as-single-authority. Remove the 7 schema-patch blocks at `backend/database.py:148–278` that exist as a stale-dev-DB safety net but are dead code in production (Dockerfile CMD runs `alembic upgrade head` on every deploy per Sprint 544c) and in tests (`conftest.py` uses `Base.metadata.create_all()`).

**Step 1 (verification gate, FIRST — DO NOT SKIP):**
- Pull last 3 Render deploys' startup logs (service `srv-d6ie9l56ubrc73c7eq2g`).
- Confirm each shows the Dockerfile CMD's `Running: alembic upgrade head` (or `Running: alembic stamp head` for fresh DBs) before gunicorn starts.
- If yes → proceed to Step 2.
- If no → STOP. Sprint 737 pivots to "restore alembic-on-deploy" before any deletion.

**Step 2 (deletion):**
- Delete the 7 patch blocks in `init_db()` (lines 148–278 of `backend/database.py`, ~130 lines).
- Keep model imports + `Base.metadata.create_all()` (idempotent table creation for fresh DBs — still legitimate).
- Keep TLS verification + version logging (load-bearing startup health check).
- Keep completion log marker.
- Post-deletion `database.py` size estimate: ~230 lines (down from 360).

**Step 3 (drift detection):**
- Add CI test: `alembic upgrade head` against fresh in-memory SQLite produces a schema matching `Base.metadata.create_all()` against the same fresh in-memory SQLite. Compare table set + column set per table via `sqlalchemy.inspect()`.
- Catches "developer added a model column without an Alembic migration" — the only real future risk this consolidation creates.

**Step 4 (documentation):**
- Add note to `CONTRIBUTING.md` (or equivalent dev setup doc): "After pulling, run `python -m alembic upgrade head` if you have a local SQLite file from before the pulled changes. The in-process auto-patch was removed in Sprint 737."
- Update `docs/03-engineering/init-db-inventory.md` to record Sprint 737 outcome (which subset shipped, any deviations from plan).

**Out of scope:**
- No startup migration-version assertion. Dockerfile already fail-closes on alembic failure (emergency-playbook §4); a runtime assertion would duplicate that mode and add operational complexity for marginal benefit.
- No changes to existing Alembic migrations.
- No changes to `conftest.py`. The new CI drift test guarantees Alembic-vs-models parity.

**Verification:**
- All existing tests green (backend `pytest` + frontend `jest`).
- New CI drift test passes on current main.
- Production deploy after Sprint 737 lands shows the Dockerfile alembic step still runs (regression check on the verification gate's premise).
- `init_db()` size drops to ~230 lines.


---

