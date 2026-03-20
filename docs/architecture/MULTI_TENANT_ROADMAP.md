# Multi-Tenant Roadmap: Firm-Level Isolation

**Source:** AUDIT-08 Phase 3 — org model gap analysis
**Status:** Planning (no code changes)
**Last updated:** 2026-03-20

---

## Section 1 — Current State

### Models Already Org-Aware

| Table | Model File | Scoping |
|-------|------------|---------|
| `organizations` | `organization_model.py` | Root org entity (owns members, invites, subscription) |
| `organization_members` | `organization_model.py` | `organization_id` + `user_id` (unique user FK) |
| `organization_invites` | `organization_model.py` | `organization_id` — invite lifecycle with status enum |
| `export_shares` | `export_share_model.py` | `organization_id` (nullable) + `user_id` — dual-scoped |
| `firm_branding` | `firm_branding_model.py` | `organization_id` (unique FK) — Enterprise feature |
| `team_activity_logs` | `team_activity_model.py` | `organization_id` + `user_id` — admin dashboard |
| `users` | `models.py` | `organization_id` (nullable FK) — allows solo → org transition |

### Access Helpers That Resolve Org Membership

Three manager classes implement identical `_get_accessible_user_ids()` logic:

- `EngagementManager._get_accessible_user_ids()` — `engagement_manager.py:104`
- `FollowUpItemsManager._get_accessible_user_ids()` — `follow_up_items_manager.py:33`
- `ClientManager._accessible_user_ids()` — `client_manager.py:101`

**Pattern:** Query `User.organization_id`, then resolve all `OrganizationMember.user_id` rows for that org. Solo users (no org) get `[user_id]`. This allows org co-members to see each other's clients, engagements, and follow-up items without adding `organization_id` to every table.

### What "Org-Aware" Means Today

Org awareness is **helper-layer resolution**, not **direct FK scoping**. Access is determined by:

1. Look up the requesting user's `organization_id`.
2. Resolve all user IDs in that org via `OrganizationMember`.
3. Filter queries with `WHERE user_id IN (accessible_ids)`.

This approach avoids adding `org_id` to every table but requires all access paths to go through the helper. Any inline `Client.user_id == user_id` check bypasses org sharing.

---

## Section 2 — What Remains User-Centric

| Table | Current Scoping | What Changes for Org Isolation |
|-------|----------------|-------------------------------|
| `activity_logs` | `user_id` (nullable) | Add `organization_id`; firm-level activity feeds require org-scoped queries. Currently only individual user history is queryable. |
| `diagnostic_summaries` | `user_id` + `client_id` | Client is already shareable via helper layer; summary access needs org-aware helper in any direct query path. |
| `subscriptions` | `user_id` (billing entity) | Subscription should be org-owned, not user-owned. Currently org resolves subscription via `organizations.subscription_id` or owner fallback — this is fragile. |
| `billing_events` | `user_id` (nullable) | Tied to Stripe webhook; user is the billing entity. May need `organization_id` for org-level billing dashboards. |
| `clients` | `user_id` only | Core data model. Currently org-shared via accessible-IDs helper. Adding `organization_id` directly would simplify queries and make org scoping explicit rather than inferred. |
| `engagements` | `created_by` (user FK) | No direct `user_id` column; access via `client_id` join. Already org-aware through `EngagementManager`. Optional: denormalize `organization_id` for direct queries. |
| `tool_runs` | `engagement_id` (FK) | Inherits access from engagement. No direct change needed. |
| `follow_up_items` | `engagement_id` + `assigned_to` | Inherits access from engagement. `assigned_to` should accept any org member, which it already does. |
| `follow_up_item_comments` | `user_id` (author) | Per-user authorship. No org scoping needed — access gated by parent follow-up item. |
| `tool_sessions` | `user_id` only | Determine whether firm-level session sharing is intended. Currently ephemeral workflow state — likely per-user is correct. |
| `refresh_tokens` | `user_id` | Per-user auth token. No org scoping needed. |
| `email_verification_tokens` | `user_id` | Per-user auth. No org scoping needed. |

### System Tables (No Tenant Scoping Needed)

| Table | Purpose |
|-------|---------|
| `scheduler_locks` | Distributed job lock (PK: `job_name`) |
| `upload_dedup` | Anti-replay cache (PK: `dedup_key`) |
| `processed_webhook_events` | Stripe webhook dedup (PK: `event_id`) |
| `waitlist_signups` | Marketing — no user FK |

---

## Section 3 — Migration Path

### Priority 1: `activity_logs` — Add `organization_id`

- Add nullable `organization_id` FK column.
- **Backfill:** `UPDATE activity_logs SET organization_id = (SELECT organization_id FROM users WHERE users.id = activity_logs.user_id) WHERE user_id IS NOT NULL`.
- Can be incremental: add nullable → backfill → make non-nullable for org users (solo users remain NULL).
- No coordinated deployment needed — existing queries filter by `user_id` and continue to work.

### Priority 2: `clients` — Add `organization_id`

- Add nullable `organization_id` FK column.
- **Backfill:** `UPDATE clients SET organization_id = (SELECT organization_id FROM users WHERE users.id = clients.user_id)`.
- Incremental: add nullable → backfill → new client creation sets `organization_id` from user context.
- **Important:** The accessible-IDs helper pattern continues to work alongside the new column. Once all query paths use `organization_id`, the helper can be simplified but not removed (it handles solo users).

### Priority 3: `subscriptions` — Org-Owned Billing

- Currently `subscriptions.user_id` is the billing entity. Org resolution goes through `organizations.subscription_id` or owner fallback.
- **Target:** Add `organization_id` FK to `subscriptions`. The Stripe checkout flow should create subscriptions linked to the org, not the individual user.
- **Backfill:** For existing org owners: `UPDATE subscriptions SET organization_id = (SELECT id FROM organizations WHERE owner_user_id = subscriptions.user_id)`.
- **Coordinated deployment:** Stripe webhook handlers must be updated to populate `organization_id` on subscription creation/update.

### Priority 4: `diagnostic_summaries` — Org-Aware Queries

- Currently inherits access via `client_id` join.
- Option A: Add `organization_id` column (denormalization for direct queries).
- Option B: Ensure all query paths use the accessible-IDs helper (current approach, no schema change).
- **Recommendation:** Option B unless direct org-scoped queries become a performance requirement.

### Priority 5: `tool_sessions` — Assess Sharing Intent

- Currently per-user ephemeral state.
- If firm-level session sharing is intended (e.g., handing off an in-progress analysis to a colleague), add `organization_id` and update access logic.
- If per-user is correct (most likely), no change needed.

### No Migration Needed

- `refresh_tokens`, `email_verification_tokens` — per-user auth, no org dimension.
- `tool_runs`, `follow_up_items`, `follow_up_item_comments` — inherit access from parent engagement/client.
- `billing_events` — Stripe audit trail, user-scoped is correct.
- All system tables (`scheduler_locks`, `upload_dedup`, `processed_webhook_events`, `waitlist_signups`).

---

## Section 4 — Regression Test Requirements

Before firm-level accounts go live, the following test cases must pass:

1. **Cross-tenant isolation:** Access to any resource family (client, engagement, diagnostic summary, tool run, follow-up item, export share, branding) by a user in a different organization returns **404** — not 403, not 400, not 500.

2. **Same-org co-member access:** A member of the same organization can view and operate on:
   - Clients created by another org member
   - Engagements linked to those clients
   - Follow-up items assigned to any org member
   - Export shares created by any org member (if `organization_id` matches)
   - Diagnostic summaries for shared clients

3. **Subscription-status enforcement:** A user whose org subscription is past-due or cancelled is denied access to tier-gated features (bulk upload, branding, export sharing, admin dashboard) **without requiring re-login or token refresh**. The DB subscription status is checked on every request.

4. **Solo user invariance:** A user with no `organization_id` (solo user):
   - Sees only their own clients, engagements, and data
   - Cannot access any org-only features (admin dashboard, team activity)
   - Experiences identical behavior to the pre-org codebase

5. **Invite lifecycle:** Accepting an org invite correctly transitions a solo user to org membership without creating duplicate data or losing existing clients/engagements.

6. **Org role enforcement:** Only OWNER and ADMIN roles can access the admin dashboard and modify org settings. MEMBER role has data access but not admin access.

---

## Section 5 — Key Invariants

The following invariants must hold across all current and future org-aware code:

1. **The database, not JWT claims, is authoritative for tier and org membership on every sensitive request.** JWT tokens carry claims for convenience, but entitlement checks must query the database (via `get_effective_entitlements()` with a live `Session`) to ensure subscription status is current.

2. **All entitlement checks must receive a live DB session — no sessionless fallback on authorization-critical paths.** The `get_effective_entitlements()` fallback at line 46-48 of `entitlement_checks.py` (trusting `user.tier` when `db` is not a `Session`) exists only for unit-test compatibility. Production routes must always pass a real session.

3. **Unauthorized access to a valid resource ID returns 404 — never 400, 403, or 500.** This prevents information leakage (the caller cannot distinguish "does not exist" from "exists but you cannot access it"). Exception: entitlement/tier gating returns 403 with an upgrade prompt, since the resource category (not a specific ID) is being denied.

4. **Every org-shareable resource family has one canonical ownership helper that all routes and generators use — no inline `user_id ==` checks on shared resources.** Currently this is the `_get_accessible_user_ids()` pattern in three managers. Long-term, this should be a single shared utility function to prevent drift.

5. **Organization membership changes take effect immediately.** Adding or removing a member from an org must be reflected in the next request — there is no cache or JWT claim that defers the change.

6. **Subscription is org-owned for Professional/Enterprise tiers.** The subscription attached to an org (via `organizations.subscription_id`) is authoritative for all members, not individual user subscriptions.
