# Emergency Playbook

Break-glass procedures for production incidents. Each section is a
self-contained runbook — read the top, decide whether the situation
matches, then execute.

All break-glass overrides in this system follow the **dated-ticket
pattern**: `TICKET-ID:YYYY-MM-DD`. The date is the **hard** expiry — the
app refuses to start once the date has passed, so there is no indefinite
escape hatch. Pick the shortest expiry that gives you time to ship a
permanent fix.

---

## 1. Rate-limit backend unavailable (Redis outage)

**Symptom:** Startup log line `Rate-limit storage is 'memory' in production`
and/or Redis health check failing.

**Risk of doing nothing:** App refuses to start in production with
`RATE_LIMIT_STRICT_MODE=true` (the default), because per-worker memory
storage can't enforce cross-worker rate limits — the limiter would silently
degrade under load.

**Risk of the override:** Rate limits degrade to per-worker accuracy for
the override window. A motivated attacker can get ~N× the throughput they'd
otherwise be limited to (where N = worker count). For Render Standard with
the current Gunicorn config, that's ~4×.

### Procedure

1. **Diagnose first.** Is Redis actually down, or is there a connectivity /
   credential issue? If the fix is < 15 minutes, fix Redis. Skip this runbook.
2. **File a ticket** describing the root cause + ETA to restore.
3. **Choose an expiry** — max 3 days out, prefer 1 day.
4. **Set the Render env vars:**

   ```
   RATE_LIMIT_STRICT_MODE=false
   RATE_LIMIT_STRICT_OVERRIDE=ORG-NNN:2026-05-02
   ```

5. **Restart the service.** Confirm the startup log shows
   `SECURITY: RATE_LIMIT_STRICT_MODE override active — ticket=ORG-NNN
   expiry=2026-05-02`.
6. **Work the ticket.** When Redis is back:
   - Delete `RATE_LIMIT_STRICT_OVERRIDE`.
   - Set (or remove) `RATE_LIMIT_STRICT_MODE=true`.
   - Restart. Confirm `Rate-limit storage backend: redis`.

**Do not** renew the override. If the underlying issue persists past the
ETA, that is a separate decision deserving a new ticket and a new override.

See also: `docs/runbooks/rate-limiter-modernization.md` for architecture.

---

## 2. Database TLS verification blind-spot (Neon pooler)

**Symptom:** Startup log line `CRITICAL: Production DB connection is NOT
using TLS` — on a deployment where the `DATABASE_URL` points at Neon's
pooled endpoint (hostname contains `-pooler`).

**Why:** Neon's pooler is a transparent connection pool; the underlying
connection IS TLS-encrypted, but `pg_stat_ssl` reports the pooler-to-backend
hop, not the client-to-pooler hop, and the check returns `ssl=false` on a
correctly encrypted connection.

**Permanent fix:** Sprint 673 added pooler-aware detection in
`backend/database.py` (`_is_pooled_hostname`). On pooled hostnames the
assertion is skipped and `tls=pooler-skip` is logged instead. Once the
Sprint 673 deploy lands, this runbook should no longer be needed.

### Procedure (pre-Sprint-673 only)

```
DB_TLS_OVERRIDE=NEON-POOLER-PGSSL-BLINDSPOT:YYYY-MM-DD
```

Maximum expiry: 30 days. The startup path emits `db_tls_override` to
secure-operations so log audits can tell "TLS verification blindspot
acknowledged" apart from "TLS is actually off."

---

## 3. Export-share passcode lockout (legitimate owner locked out)

**Symptom:** A share creator reports their recipients are all seeing
"Too many failed passcode attempts" on an actively-shared token.

**Possible causes:**
- Credential-stuffing bot hit the share's per-token limiter (Sprint 696).
- Bug in recipient-side logic replaying a bad passcode.
- Per-IP throttle (Sprint 698) hit from a shared-NAT corporate network.

### Procedure

1. Confirm the share is passcode-protected and the passcode distributed by
   the owner is actually correct. (Most lockouts are the owner mis-typed
   the passcode when sending.)
2. Check the secure-operations log for the share_id:
   - `passcode_mismatch` events name the failing share + masked IP.
   - `legacy_passcode_invalidation` means Sprint 700 cleanup revoked it —
     the owner must re-create a fresh share.
3. **Revoke and re-issue** is the answer in nearly every case. From the
   owner's "Shares" dashboard, revoke the affected share and create a new
   one with a strong passcode delivered over a separate channel.
4. **If credential-stuffing is suspected at scale**, enable a targeted
   network-level block via Render; do not weaken the per-IP throttle.

No break-glass override exists for the passcode throttle — by design.
Permitting a runtime bypass would re-open the exact exposure the lockout
was added to close.

---

## 4. Production deploy refuses to start on `alembic upgrade head`

**Symptom:** Dockerfile entrypoint exits before Gunicorn starts, logs show
`alembic.util.exc.CommandError: Multiple head revisions are present for
given argument 'head'` or a SQL error mid-migration.

### Procedure

1. **Check `alembic heads` locally** against the commit that was deployed.
   Single head = good. Multiple heads = diverging migration branches
   checked in, need a merge migration.
2. **If multi-head:**
   - Open a hotfix branch.
   - Run `alembic merge -m "merge hotfix" heads`.
   - Commit the merge migration.
   - Deploy the hotfix.
3. **If single-head but a migration body failed:**
   - Inspect the logs for the SQL error + dialect.
   - Most commonly: a Postgres-only DDL statement (`ALTER TYPE`) without a
     dialect guard. Fix in a hotfix migration; do not edit the offending
     migration in place if it has already run successfully against any
     deployed environment.
   - As a last resort, mark the migration as applied with `alembic stamp`
     after a manual DB patch — but only if you can reason precisely about
     what state the DB is in.

### Preventive

- CI should include `alembic upgrade head` against a fresh SQLite to
  catch missing dialect guards. Sprint 710's `c1d2e3f4a5b6` fix closed
  the last known SQLite-breaking migration.
- Never check in a migration whose `down_revision` is not an actual head
  of the chain at commit time — it produces a divergent head that breaks
  the next deploy. Sprint 710 caught one such case (`c1a5f0d7b4e2`
  incorrectly parented to a branchpoint instead of the Sprint 594 head
  `f7b3c91a04e2`).

---

## Index of break-glass env vars

| Variable | Purpose | Max expiry | Used in §|
|----------|---------|------------|---------|
| `RATE_LIMIT_STRICT_OVERRIDE` | Allow prod to run with memory rate-limit storage | 3 days (prefer 1) | 1 |
| `DB_TLS_OVERRIDE` | Allow prod to run past the `pg_stat_ssl` check | 30 days | 2 |

Every override emits a secure-operations event at startup; log-audit is
how you know an override is active without grep'ing env vars on the host.
