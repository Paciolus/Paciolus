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
