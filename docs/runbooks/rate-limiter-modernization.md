# Rate Limiter Modernization Playbook

## Current State

| Component | Version | Status |
|-----------|---------|--------|
| slowapi | 0.1.9 | Unmaintained (last release Oct 2022) |
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

## Strict-Mode Production Fail-Closed (Sprint 696, 2026-04-20)

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

