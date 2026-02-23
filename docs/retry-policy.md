# API Retry Policy

> Contributor reference for the Paciolus API client retry and caching behavior.
> Implementation: `src/utils/apiClient.ts` and `src/utils/constants.ts`.

---

## HTTP Method Classification (RFC 9110)

| Method | Idempotent | Auto-Retries | Notes |
|--------|-----------|-------------|-------|
| GET | Yes | 3 | Safe, cacheable |
| PUT | Yes | 3 | Full replacement — server state is same after 1 or N calls |
| HEAD | Yes | 3 | Same as GET, no body |
| OPTIONS | Yes | 3 | Preflight / discovery |
| POST | No | 0 | Creates resources — retrying may duplicate |
| DELETE | No | 0 | May have side effects on repeated calls |
| PATCH | No | 0 | Partial update — may not be idempotent |

> Source: RFC 9110 Section 9.2.2. The `IDEMPOTENT_METHODS` set in `apiClient.ts` gates automatic retries.

---

## Constants

Defined in `src/utils/constants.ts`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_RETRIES` | 3 | Maximum retry attempts for idempotent methods |
| `BASE_RETRY_DELAY` | 1,000 ms | Starting delay for exponential backoff |
| `DEFAULT_REQUEST_TIMEOUT` | 30,000 ms | Request abort timeout |
| `DOWNLOAD_TIMEOUT` | 60,000 ms | Extended timeout for file downloads |
| `DEFAULT_CACHE_TTL` | 300,000 ms (5 min) | Default cache entry lifetime |
| `MAX_CACHE_ENTRIES` | 100 | LRU cache capacity |

---

## Retryable vs Non-Retryable Errors

| Status | Retryable | Reason |
|--------|-----------|--------|
| 0 (network error) | Yes | Transient connectivity issue |
| 429 | Yes | Rate limit — back off and retry |
| 500-599 | Yes | Server-side transient failures |
| 400 | No | Client error — request is malformed |
| 401 | No* | Auth error — triggers token refresh instead |
| 403 | No | Permission denied |
| 404 | No | Resource not found |
| 422 | No | Validation error — request data is invalid |

*401 responses trigger a silent token refresh via the registered `_tokenRefreshCallback`. If the refresh succeeds, the original request is retried once with the new token.

---

## Exponential Backoff Schedule

| Attempt | Delay | Cumulative Wait |
|---------|-------|-----------------|
| 1st retry | 1,000 ms | 1.0 s |
| 2nd retry | 2,000 ms | 3.0 s |
| 3rd retry | 4,000 ms | 7.0 s |

Formula: `BASE_RETRY_DELAY * 2^attempt` where attempt is 0-indexed.

After the final retry fails, the last error response is returned to the caller.

---

## Mutation Retries with Idempotency Keys

Non-idempotent methods (POST, DELETE, PATCH) default to 0 retries. To opt in to retries safely:

```typescript
const result = await apiPost<Order>('/orders', token, orderData, {
  retries: 2,
  idempotencyKey: `create-order-${crypto.randomUUID()}`,
});
```

The `idempotencyKey` is sent as the `Idempotency-Key` HTTP header. The server must deduplicate requests sharing the same key.

A dev-mode `console.warn` fires if `retries > 0` on a non-idempotent method without an `idempotencyKey`.

---

## User-Initiated vs Auto-Retry

| Scenario | Strategy | Reason |
|----------|----------|--------|
| GET data fetch | Auto-retry (3 attempts) | Idempotent, no side effects |
| File upload (POST) | No auto-retry | May create duplicate uploads |
| Delete resource | No auto-retry | Side effects unclear on retry |
| Export download (POST) | No auto-retry | Server generates file per request |
| User clicks "Retry" button | New request | Explicit user intent |

For user-initiated retries, hooks expose retry functions (e.g., `retryFn` in testing hooks). These create fresh requests rather than replaying failed ones.

---

## Token Refresh Flow

When a request returns 401:

1. The `_tokenRefreshCallback` (registered by `AuthContext`) is called
2. If the refresh token exchange succeeds, a new access token is returned
3. A fresh CSRF token is fetched via `fetchCsrfToken()`
4. The original request is retried once with the new tokens
5. If the refresh fails, the 401 response is returned to the caller

Auth endpoints (`/auth/refresh`, `/auth/login`, `/auth/register`) are excluded from this flow to prevent infinite loops.

---

## Cache Behavior

### Stale-While-Revalidate (SWR)

When `staleWhileRevalidate: true` is passed:

1. Fresh cache hit: Returns cached data immediately
2. Stale cache hit: Returns stale data immediately, triggers background revalidation
3. Cache miss: Makes a normal network request

The `onRevalidate` callback fires when background revalidation completes:

```typescript
const result = await apiGet<Client[]>('/clients', token, {
  staleWhileRevalidate: true,
  onRevalidate: (fresh) => {
    if (fresh.ok) setClients(fresh.data);
  },
});
```

### Cache Invalidation

Successful mutations automatically invalidate related cache entries:

- **Exact path**: `/clients/1` invalidates cache keys containing `/clients/1`
- **Parent path**: `/clients/1` also invalidates cache keys containing `/clients`

Manual invalidation is available via `invalidateCache(pattern?)`.

### LRU Eviction

The cache is bounded at `MAX_CACHE_ENTRIES` (100). When full:

1. The oldest entry (first in Map insertion order) is evicted
2. Accessed entries are moved to the end of the insertion order (LRU touch)
3. Expired entries are swept every 60 seconds by a background timer

### Cache Telemetry

Debug cache behavior in development:

```typescript
import { getCacheTelemetry } from '@/utils/apiClient';

console.log(getCacheTelemetry());
// { hits: 42, misses: 8, evictions: 0, staleReturns: 3 }
```
