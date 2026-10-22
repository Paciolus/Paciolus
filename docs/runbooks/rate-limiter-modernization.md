# Rate Limiter Modernization Playbook

## Current State

| Component | Version | Status |
|-----------|---------|--------|
| slowapi | 0.1.10 | Low-frequency upstream (0.1.10 released 2026-06-13, after a two-year gap) |
| limits | >=3.0.0 | Actively maintained |

slowapi is a thin Starlette middleware wrapper around the `limits` library.
The actual rate-limiting logic (token bucket, sliding window, storage backends)
lives entirely in `limits`. slowapi adds ~200 lines of Starlette integration glue.

## Decision: Keep slowapi (Sprint 444)

**Rationale:**
- 123 `@limiter.limit()` decorator sites across 31 route files
- Custom `TieredLimit` str subclass deeply integrated with slowapi's resolution
- `limits` library (the actual engine) is actively maintained
- No known CVEs in slowapi
- No functional bugs in current usage

**Risk:** Future Starlette major versions may break slowapi's middleware registration.

## Operator Posture (security remediation note)

`shared/rate_limits.py` emits a startup banner on import:

- **Production:** `WARNING` log line `"PRODUCTION rate-limiter dependency
  notice: slowapi is unmaintained ..."` — intended for oncall log
  visibility, not an incident alert.
- **Non-production:** `INFO` line of the same form.

This is **temporary** posture. The framework is not replaced in this
remediation patch — full migration is deferred until one of the
`Trigger Conditions` below fires. Until then, the supporting `limits`
library is the security-critical dependency (it is actively maintained
and pinned `>=3.0.0`); slowapi is a thin glue layer with no known CVEs.

Entry criteria for the deferred migration sprint:

1. Any canary test in `test_rate_limit_slowapi_health.py` fails on a
   green main branch (i.e., a real regression, not a flake).
2. A CVE with CVSS ≥ 7.0 is published against slowapi.
3. Starlette major-version upgrade renders slowapi's middleware
   registration incompatible.

Production rate-limit fail-closed posture is enforced by:

- `config.RATE_LIMIT_STRICT_MODE=true` (production default; hard-fail
  override gated by `RATE_LIMIT_STRICT_OVERRIDE=TICKET:YYYY-MM-DD`).
- `shared/rate_limits._resolve_storage_uri()` raises `RuntimeError`
  when Redis is unreachable under strict mode (covered by
  `test_rate_limit_strict_mode.py::TestStrictModeFailClosed*`).

## Canary Tests

`backend/tests/test_rate_limit_slowapi_health.py` runs 5 checks in CI:
1. slowapi imports work
2. limits imports work
3. Limiter construction succeeds
4. limits version >= 3.0.0
5. Rate limit string parsing works

If any canary test fails, execute the migration below.

## Migration Plan (When Needed)

### Trigger Conditions
- slowapi fails to import with a new Starlette version
- A CVE is found in slowapi
- `limits` drops backward compatibility that slowapi depends on

### Step 1: Create Custom Middleware (~50 lines)

Replace slowapi's `Limiter` with a custom Starlette middleware that calls
`limits` directly:

```python
from limits import parse
from limits.storage import MemoryStorage
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, storage=None):
        super().__init__(app)
        self.storage = storage or MemoryStorage()

    async def dispatch(self, request: Request, call_next):
        key = _get_rate_limit_key(request)
        limit_string = _resolve_limit(request)
        rate = parse(limit_string)
        if not self.storage.test(rate, key):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        self.storage.hit(rate, key)
        return await call_next(request)
```

### Step 2: Migrate Decorators to Route Metadata

Replace `@limiter.limit(RATE_LIMIT_AUDIT)` with route metadata:

```python
@router.post("/upload", tags=["audit"], rate_limit="audit")
```

The middleware reads `rate_limit` from route metadata and applies the
appropriate tier policy from `_DEFAULT_POLICIES`.

### Step 3: Preserve TieredLimit Resolution

The `TieredLimit` class and `_current_tier` ContextVar stay unchanged.
Only the middleware integration layer changes.

### Step 4: Test Verification

- Run `pytest tests/test_rate_limit_enforcement.py` — all 429 tests must pass
- Run `pytest tests/test_rate_limit_slowapi_health.py` — update to test new middleware
- Verify rate limit headers in response (X-RateLimit-Limit, X-RateLimit-Remaining)

### Estimated Effort
- Middleware: 1 sprint
- Decorator migration (123 sites): 1-2 sprints
- Testing: 1 sprint
- Total: 3-4 sprints

---

## Storage Outage Posture (Sprint 774, 2026-10-19)

> **Read this before the Sprint 696 section below.** Sprint 774 narrowed what
> strict mode controls. Strict mode is now purely a *configuration* guardrail;
> runtime unreachability is governed by a separate setting.

### The incident this came from

The configured Upstash Redis host stopped resolving in DNS some time after
2026-05-01. Consequences, in order:

1. Every rate-limited route raised out of slowapi's limit check. That is
   essentially the whole API — **including `/health`, `/health/live`,
   `/health/ready`, and `/metrics`** — so every request returned HTTP 500.
2. Because the probes themselves 500'd, nothing reported *why*. Render showed
   the service as healthy and unsuspended the entire time.
3. The outage ran roughly 5.5 months.

Two latent bugs made it worse than it had to be:

- **The fail-closed check never fired.** `limits`' `Storage.check()` signals
  failure by *returning False*, not by raising (`try: return ping() except:
  return False`). The old code only caught exceptions, so a dead backend was
  silently treated as healthy at boot. The tests passed only because they
  mocked `check()` to raise — something real `RedisStorage` never does.
- **There was no self-heal path.** Even had fail-closed fired, the process
  would have exited and the orchestrator would have restart-looped until a
  human intervened.

### What the posture is now

`RATE_LIMIT_STORAGE_FAILURE_POLICY` controls behavior when `REDIS_URL` is
configured but the backend is **unreachable**:

| Value | Behavior |
|-------|----------|
| `degrade` (default) | Serve using slowapi's in-memory fallback. Limit **values** are unchanged and still enforced; they are just no longer shared across workers. slowapi re-probes the primary and restores shared counters automatically, with no restart. |
| `fail_closed` | Refuse to start (pre-Sprint-774 behavior). Choose only where under-enforcement is worse than being offline. |

This is **not** slowapi's `swallow_errors`. Limits remain enforced while
degraded; `swallow_errors` would let unlimited traffic through.

Rationale: rate limiting is an abuse control, not an integrity control.
Losing cross-worker sharing briefly is strictly less harmful than total
unavailability — provided the degradation is loud and self-healing. At
`numInstances: 1` the enforcement difference is zero.

### How to detect degradation

- **`GET /health/ready`** → overall `status: "degraded"` (still HTTP 200, so a
  healthy instance is not pulled from the load balancer over a cache outage)
  with a `rate_limit_storage` dependency reporting `degraded: true` plus
  `configured_backend` / `active_backend`.
- **Logs** → `CRITICAL` containing `DEGRADED: Redis configured but
  unreachable`, and slowapi's own `Rate limit storage unreachable - falling
  back to in-memory storage`. Recovery logs `Rate limit storage recovered`.
- **`GET /health/redis`** → direct backend probe.

**Alert on `/health/ready` returning `status: "degraded"`.** The whole point
of this design is that the signal survives the outage it describes.

### Restoring Redis

Rate-limit counters are disposable, so replacing the instance is safe:

1. Provision a Key Value instance in the **same region** as `paciolus-api`
   (currently `virginia`) — an in-provider private hostname removes the
   cross-provider DNS dependency that caused this incident.
2. Set `REDIS_URL` to its internal URL (`redis://red-<id>:6379`).
3. No redeploy is needed for slowapi to pick it up — its re-probe restores
   shared counters within a few requests. Changing the env var on Render
   triggers a deploy anyway.
4. Confirm `/health/ready` reports `status: "healthy"`.

---

## Strict-Mode Production Fail-Closed (Sprint 696, 2026-04-20)

> **Superseded in part by Sprint 774 (above).** `RATE_LIMIT_STRICT_MODE` still
> governs whether Redis must be **configured**, and the break-glass override
> below still applies to that. It no longer decides what happens when a
> configured backend is **unreachable** — that is
> `RATE_LIMIT_STORAGE_FAILURE_POLICY`.

### What it does

`config.py` enforces that production deployments run with a shared rate-limit
storage backend (Redis via `REDIS_URL`). If an operator sets
`RATE_LIMIT_STRICT_MODE=false` in a production deployment, the app **refuses
to start** unless a time-boxed break-glass is also set:

```
RATE_LIMIT_STRICT_OVERRIDE=TICKET-ID:YYYY-MM-DD
```

The override follows the same shape as `DB_TLS_OVERRIDE`:

- **`TICKET-ID`** — your ticket system identifier (Linear, Jira, Notion page, etc.)
  so the secure-operations log can be joined back to a decision record.
- **`YYYY-MM-DD`** — the date the override expires. After this date, startup
  hard-fails on the override parse; there is no way to set an indefinite
  override.

At startup, if `ENV_MODE=production` and `RATE_LIMIT_STRICT_MODE=false`:
1. If `RATE_LIMIT_STRICT_OVERRIDE` is missing → hard-fail with an operator-
   actionable error.
2. If it parses but the expiry date has passed → hard-fail with the same
   error, naming the expired ticket.
3. If it parses and is in the future → log `rate_limit_strict_override_active`
   to secure-operations with the ticket + expiry and boot with the warning
   that rate limits may degrade to memory backend under Redis outage.

### When to issue an override

Only when **both** of the following are true:

- Redis is unavailable and cannot be restored within the next 15 minutes.
- Refusing traffic while Redis is down is worse than allowing per-worker
  rate-limit drift for the override window.

For any other reason, **fix Redis**. The override exists to unblock a live
incident, not as a comfort knob.

### How to issue an override

1. File a ticket describing the root cause and the ETA to restore Redis.
2. Pick an expiry date at most **3 days** out; shorter is better. The longer
   the window, the more production runs with weakened per-worker rate limits.
3. Set the env var on Render (or equivalent):

   ```
   RATE_LIMIT_STRICT_OVERRIDE=ORG-NNN:2026-05-02
   ```

4. Restart the service. The startup log line `rate_limit_strict_override_active`
   confirms the override is in effect; `rate_limit_fail_closed` appears instead
   if startup refused (override missing or expired).
5. Track the ticket; remove the env var and the `RATE_LIMIT_STRICT_MODE=false`
   setting within the window. Do **not** renew — if the underlying issue
   persists past the ETA, that is a separate decision that deserves a new
   ticket and a new override.

### How to retire an override

- Restore Redis connectivity.
- In Render env vars, delete `RATE_LIMIT_STRICT_OVERRIDE` and set
  `RATE_LIMIT_STRICT_MODE=true` (or remove it — `production` defaults to
  `true`).
- Restart the service. Startup log line `Rate-limit storage backend: redis`
  confirms strict mode is back.

### Related secure-operations events

| Event | Meaning |
|-------|---------|
| `rate_limit_strict_override_active` | Override accepted at startup; tier degraded. |
| `rate_limit_fail_closed` | Startup refused: prod + non-Redis + no active override. |
| `rate_limit_degraded` | Informational: Redis unreachable in non-production. |

