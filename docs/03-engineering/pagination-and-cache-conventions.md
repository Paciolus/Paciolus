# Pagination + Cache Invalidation Conventions

**Sprint:** 758 — Phase 7.2 of the Architectural Remediation Initiative.

This doc captures the two server-side pagination patterns and the
client-side cache invalidation contract. Sprint 758 is a documentation
sprint — survey confirmed both patterns are already coherent and no
code changes were warranted. The doc exists so new endpoints / new
mutations pick the right pattern instead of inventing a third one.

## Server-side pagination — two patterns

### Pattern A: `PaginationParams` for browsable lists

Use when the surface is a **browsable, multi-page list** with a total
count for pagination controls. Established in Sprint 544.

```python
from shared.pagination import PaginatedResponse, PaginationParams

@router.get("/clients", response_model=PaginatedResponse[ClientSummary])
def list_clients(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ClientSummary]:
    items, total = ClientManager(db).list_paginated(
        current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginatedResponse(
        items=items,
        total_count=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
```

`PaginationParams` exposes `page` (1-indexed, default 1, ≥ 1) and
`page_size` (default 50, 1–100). Use `pagination.offset` for the SQL
offset.

`PaginatedResponse[T]` is the shape for every list response: `items`,
`total_count`, `page`, `page_size`. Frontends rely on `total_count` to
render pagination controls.

Adopters today: `routes/activity.py` (history), `routes/clients.py`,
`routes/analytical_expectations.py`, `routes/follow_up_items.py`.

### Pattern B: bare `limit` for feed endpoints

Use when the surface is a **bounded recent-items feed** with no paging
UI. Caller controls the cap; no `total_count` is meaningful because the
feed is already truncated.

```python
@router.get("/activity/tool-feed", response_model=list[ToolActivityResponse])
def get_tool_activity_feed(
    limit: int = Query(default=8, ge=1, le=50),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> list[ToolActivityResponse]:
    activities = (
        db.query(ToolActivity)
        .filter(ToolActivity.user_id == current_user.id)
        .order_by(ToolActivity.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [_to_response(a) for a in activities]
```

Adopters today: `routes/activity.py::get_tool_activity_feed`,
`routes/diagnostics.py::recent_diagnostics`,
`routes/prior_period.py`, `routes/trends.py`,
`routes/internal_admin.py`.

### Picking between A and B

| Question | Pattern A (`PaginationParams`) | Pattern B (bare `limit`) |
|----------|-------------------------------|-------------------------|
| User browses with prev/next? | ✅ | ❌ |
| Total count drives UI? | ✅ | ❌ |
| Bounded "latest N" feed? | ❌ | ✅ |
| Frontend renders all returned items? | depends | ✅ |
| Endpoint emits paged response model? | ✅ `PaginatedResponse[T]` | ❌ plain `list[T]` |

The two patterns are **intentionally different**, not drift. Don't
merge them. Don't add a third.

## Client-side cache invalidation contract

`frontend/src/utils/apiClient.ts` exposes `apiPost`, `apiPut`,
`apiPatch`, `apiDelete` — every mutation method calls
`invalidateRelatedCaches(endpoint)` on success.

`invalidateRelatedCaches` clears both:

1. **The endpoint itself.** Any cached entry whose key contains the
   endpoint path (e.g., `apiPut('/settings/preferences', ...)` clears
   any cached `GET /settings/preferences` entry).
2. **The parent collection.** Any cached entry whose key contains the
   path one segment up (e.g., the same call also clears
   `/settings`).

This catches the common "PUT a single resource → list view goes
stale" pattern automatically. List-fetching components don't need to
manually invalidate after a mutation.

### What it does NOT do

- **It does not refresh React `useState` in already-mounted
  components.** If `/tools` and `/dashboard` both compose
  `useUserPreferences` and the user toggles a favorite on `/tools`,
  apiClient invalidates the cache, but `/dashboard`'s local
  `useState<string[]>` stays stale until the component remounts or
  re-fetches. Cross-component live-sync would need a shared store
  (Zustand, etc.) — out of scope for this initiative.
- **It does not cascade across unrelated endpoints.** A mutation to
  `/clients/123` does not invalidate `/dashboard/stats`, even though
  the stats page reads aggregates that include client 123. If a
  cross-cascade matters, the route handler can return a richer
  response that the caller consumes; otherwise, the staleness window
  is the cache TTL (typically 30s).
- **It does not guarantee linearizability.** A `apiPost` followed
  immediately by `apiGet` on the same endpoint may return cached
  pre-mutation data if the GET is in-flight when the POST resolves —
  apiClient deduplicates in-flight GETs and serves the in-flight
  promise. This is rare and self-heals on the next mount.

### When to bypass the cache

Use `apiGet(endpoint, token, { skipCache: true })` when the caller
needs an authoritative read regardless of cached state — e.g., the
status page (`app/status/page.tsx`) skips cache so it always shows
current health.

## Auditing checklist for new endpoints

When adding a new list-or-feed endpoint:

1. [ ] Pick Pattern A or B per the table above.
2. [ ] If Pattern A: return `PaginatedResponse[T]`, accept
       `PaginationParams = Depends()`.
3. [ ] If Pattern B: return `list[T]`, accept `limit: int = Query(...)`
       with explicit `ge=` and `le=` bounds.
4. [ ] If the endpoint reads cached data, verify any sibling
       mutation endpoint targets the same path (so
       `invalidateRelatedCaches` covers it).
5. [ ] If the staleness window matters more than the network savings,
       use `{ skipCache: true }` on the GET.

## Survey results (Sprint 758)

**Pagination.** Inventoried all `Query(...)` parameters across
`backend/routes/`. 4 routes use Pattern A (`PaginationParams`). 7
routes use Pattern B (bare `limit`). No routes mix the two. No third
pattern detected. **No code changes warranted.**

**Cache invalidation.** Inventoried apiClient mutation methods —
`apiPost`, `apiPut`, `apiPatch`, `apiDelete` all call
`invalidateRelatedCaches` after `result.ok` returns true. Edge cases
documented above. **No code changes warranted.**

The deliverable is this doc — Sprint 758 ships convention clarity.
