# ADR-014: Canonical Frontend Network Layer

**Status:** Accepted (Sprint 744)
**Date:** 2026-04-29
**Decision-makers:** Engineering team

## Context

Before Sprint 744, ~5 frontend call sites (hooks + pages) were issuing direct
`fetch()` calls instead of going through the canonical `apiClient` stack
(Sprint 539: `transport.ts` + `authMiddleware.ts` + `cachePlugin.ts` +
`downloadAdapter.ts` + `uploadTransport.ts`).

Drift symptoms:

- **Inconsistent auth.** Direct fetchers added `Authorization: Bearer ${token}`
  headers; the canonical client uses HttpOnly cookies + CSRF (Sprint 661).
  Tests that pinned the Bearer header were silently exercising obsolete
  behavior.
- **Inconsistent error handling.** Each page parsed `response.ok` / `response.status`
  / `response.json()` differently; no shared error-message normalization.
- **No caching, no in-flight dedup, no retry policy.** Direct fetches bypassed
  the `cachePlugin` and idempotent-retry logic baked into the canonical client.
- **No CSRF token injection.** Manual `X-CSRF-Token` plumbing was easy to
  forget, surfacing as 403s under cross-origin POSTs.

## Decision

All frontend HTTP traffic must go through one of the canonical exports from
`@/utils/apiClient`:

| Use case | Canonical entrypoint |
|----------|----------------------|
| GET / POST / PUT / PATCH / DELETE JSON | `apiGet` / `apiPost` / `apiPut` / `apiPatch` / `apiDelete` |
| File / blob download | `apiDownload` + `downloadBlob` |
| FormData upload | `uploadFetch` (from `@/utils/uploadTransport`) |

Direct `fetch()` is **banned** in `app/`, `hooks/`, `components/`, and any
other application-layer code.

### Allowlist

Direct `fetch()` is permitted only in low-level transport / auth / public-share
modules where the canonical client cannot be used by definition:

- `src/utils/transport.ts` — base fetch wrapper used by `apiClient`.
- `src/utils/authMiddleware.ts` — CSRF token bootstrap (`/auth/csrf` —
  cannot use `apiClient` because the client depends on the CSRF state this
  endpoint populates).
- `src/utils/downloadAdapter.ts` — blob/download fetch with custom timeout.
- `src/utils/uploadTransport.ts` — FormData fetch with `credentials: 'include'`
  but no `Content-Type` injection (browser sets multipart boundary).
- `src/contexts/AuthSessionContext.tsx` — `/auth/refresh` and `/auth/logout`
  (HttpOnly cookie semantics; refresh-on-401 cycle would deadlock if it
  routed through the canonical client's own 401 retry logic).
- `src/app/shared/[token]/page.tsx` — public passcode-flow share download
  (no auth, custom 429 `Retry-After` parsing for per-token / per-IP lockout).

## Enforcement

ESLint `no-restricted-syntax` rule (`frontend/eslint.config.mjs`):

```js
{
  selector: 'CallExpression[callee.type="Identifier"][callee.name="fetch"]',
  message: 'Direct fetch() is banned. Use apiClient (apiGet/apiPost/etc.), apiDownload, or uploadFetch from @/utils/apiClient.',
}
```

A per-file override block exempts the allowlist (with escaped brackets for
the `[token]` literal in minimatch).

CI fails on any new violation outside the allowlist.

## Consequences

- New transport/auth modules must be added to the allowlist explicitly,
  forcing a review of whether the canonical client could serve instead.
- Local variables named `fetch` (e.g., destructured from a custom hook)
  trip the rule; rename them at the destructure site.
- Test suites that assert HTTP details (URL, method, body) should mock at
  the `apiClient`/`apiDownload`/`downloadBlob` boundary, not at
  `global.fetch`. Tests pinning the obsolete Bearer-header pattern were
  updated in Sprint 744.

## Alternatives considered

- **Wrapper module that proxies `fetch` and warns at runtime.** Rejected —
  catches violations only when the code runs (production-time), not at
  build/CI time.
- **Codemod-only one-shot migration without a lint rule.** Rejected — drift
  re-emerges within 2-3 sprints without enforcement.

## See also

- Sprint 744 review in `tasks/todo.md`.
- `frontend/src/utils/apiClient.ts` (composes the canonical stack).
- `frontend/src/utils/transport.ts` (base fetch + retry + 401 refresh).
