# Cohesion Remediation Report

**Sprint:** 547
**Date:** 2026-03-17
**Scope:** Documentation, copy normalization, UI label consistency, and API reference scaffolding
**Constraint:** No business logic, entitlement enforcement, pricing values, or route paths were modified

---

## 1. Changes Made

| File | Change Summary | Audit Finding Resolved | Decision Applied |
|------|---------------|------------------------|------------------|
| `README.md` | Hero rewritten: "12-Tool AI-Powered Audit Intelligence Suite", tool list added, retention language layered | Tool count drift (5/11/12), absolute retention claims | #1 (12-tool), #2 (layered retention) |
| `docs/01-product/PRODUCT_VISION.md` | 5-tool → 12-tool throughout, tool table expanded to 12, version/dates updated, inline update comments | Tool count frozen at v0.70.0 | #1 (12-tool) |
| `docs/02-technical/ARCHITECTURE.md` | 11-tool → 12-tool, Navigation Model section added, tech stack versions corrected (React 19, Tailwind 4, framer-motion 12, FastAPI 0.135), version bumped to v2.1.0 | Tool count drift, navigation ambiguity, stale tech versions | #1 (12-tool), #3 (workspace-centric), #6 (tech stack) |
| `docs/02-technical/API_REFERENCE.md` | Deprecation header added (historical snapshot warning) | API ref frozen at v0.70.0, 17 routers (actual: 35) | #6 (hybrid API ref) |
| `docs/02-technical/API_REFERENCE_GENERATED.md` | New file: generated skeleton from all 35 routers with endpoint tables | No API reference for current surface | #6 (hybrid API ref) |
| `docs/01-product/FEATURE_ROADMAP.md` | Historical artifact header added | Frozen at v0.70.0, claims current accuracy | #6 (historical artifacts) |
| `docs/04-compliance/ACCESS_CONTROL_POLICY.md` | Tier table: Team/Org → Professional/Enterprise, limits corrected | Legacy tier labels in compliance docs | #4 (tier retirement) |
| `docs/07-user-facing/USER_GUIDE.md` | §15: pricing table rewritten (tiers, prices, limits), §15.2: tool access corrected (all paid = all 12), §16: layered retention strings, §16.3: ephemeral scope clarification, §17: tier availability corrected, FAQ: recovery answer rewritten, tier references updated | Tool count, tier labels, pricing, retention language, export entitlement | #1, #2, #4, #5 |
| `docs/tos-section-8-draft.md` | "Diagnostic Workspace" → "Workspace" (3 occurrences) | Navigation term inconsistency | #3 (workspace-centric) |
| `EXECUTIVE_SUMMARY_NONTECH.md` | Historical artifact header added, tool count corrected, "purged" → "archived" (matches soft-delete implementation) | Stale doc claiming currency, incorrect terminology | #2 (retention), #6 (artifacts) |
| `backend/shared/entitlements.py` | Canonical tool count comment block added (no logic changes) | No single source of truth for tool count | #1 (12-tool) |
| `backend/shared/rate_limits.py` | LEGACY ALIAS comments on "team" and "organization" backward-compat entries | Undocumented legacy aliases | #4 (tier retirement) |
| `backend/main.py` | FastAPI app description: "Trial Balance Diagnostic Intelligence" → "12-Tool Audit Intelligence Suite" | Product description drift | #1 (12-tool) |
| `frontend/src/app/(marketing)/terms/page.tsx` | Pricing table: Team/Org → Professional/Enterprise, prices/tools/limits corrected | Legacy tier labels + wrong pricing in legal copy | #4 (tier retirement) |
| `frontend/src/components/shared/GuestCTA.tsx` | Comment: "11 tools" → "12 tools" | Tool count in code comment | #1 (12-tool) |
| `tasks/todo.md` | Sprint 547 checklist added, 5 completed sprints archived | Directive protocol compliance | N/A |
| `tasks/archive/sprints-542-546-details.md` | Archived completed sprints from Active Phase | Directive protocol compliance | N/A |
| Multiple `backend/routes/*.py` files | One-line docstrings added to undocumented handlers | API reference needs docstring source | #6 (hybrid API ref) |

---

## 2. Decisions Applied

### Decision #1: Product Scope Framing — 12-Tool Audit Intelligence Suite
Every top-level brand touchpoint now leads with "12-tool" framing. The README hero, Product Vision executive summary, ARCHITECTURE.md executive summary, FastAPI app description, and all marketing-adjacent copy now consistently describe Paciolus as a 12-tool suite. Historical references to 5-tool and 11-tool states are preserved in archive files but marked with inline comments or historical artifact headers. The canonical tool count is locked in `backend/shared/entitlements.py` with a comment block that mandates cross-reference updates if tools are added or removed.

### Decision #2: Retention Language — Layered Approach
Three canonical strings were established and applied: a headline claim ("Your uploaded financial data is never stored"), a precision copy block (distinguishing raw data from aggregate metadata), and an ephemeral scope clarification (explaining that workspace metadata persists). The User Guide's data handling section now opens with the headline, includes the precision detail, and the implications section clarifies that "ephemeral" applies specifically to uploaded financial data, not workspace metadata. The FAQ answer for result recovery was rewritten to match. The term "purged" was corrected to "archived" in the Executive Summary to match the soft-delete implementation (`archived_at` column).

### Decision #3: Navigation Identity — Workspace-Centric
A formal Navigation Model section was added to ARCHITECTURE.md defining Workspaces as the primary organizational unit and Dashboard as a subordinate summary view. "Diagnostic Workspace" was retired from docs (User Guide, ToS draft). No routes, component files, or URL paths were renamed — this was docs-only normalization.

### Decision #4: Tier Label Retirement — Full Retirement
All safe-surface occurrences of "Team" → "Professional" and "Organization"/"Org" → "Enterprise" were updated in: User Guide (pricing table, tool access table, seat pricing, engagement availability, FAQ, error messages), Terms of Service page, and Access Control Policy. Load-bearing aliases in `rate_limits.py` received LEGACY ALIAS comments. DB-stored tier strings in migrations were not touched (see Section 3). The canonical tier vocabulary is now: `Free · Solo · Professional · Enterprise`.

### Decision #5: Ephemeral Scope — Raw Financial Payloads Only
This decision was applied through retention language normalization (Decision #2). The User Guide now explicitly states that "ephemeral" refers to uploaded financial data only, and that workspace metadata (analysis results, findings summaries, report history) is retained for workspace continuity.

### Decision #6: API Reference — Hybrid (Generated Skeleton + Narrative)
The old API_REFERENCE.md received a deprecation header warning that it reflects v0.70.0 with 17 routers. A new `API_REFERENCE_GENERATED.md` was created by reading all 35 registered routers and extracting endpoint signatures and docstrings. Route handlers lacking docstrings received one-line summaries to populate the skeleton and OpenAPI schema. The FEATURE_ROADMAP.md and EXECUTIVE_SUMMARY_NONTECH.md received historical artifact headers. Tech stack versions in ARCHITECTURE.md were corrected to match actual package.json/requirements.txt values.

---

## 3. Load-Bearing Aliases — Migration Required

| File | Line(s) | String | Why Load-Bearing | Recommended Migration Path |
|------|---------|--------|-----------------|---------------------------|
| `backend/shared/rate_limits.py` | 90-96 | `"team": {...}` | Backward-compat rate limit alias; active requests from users with old tier values hit this key | Create Alembic migration to UPDATE users SET tier='professional' WHERE tier='team', then remove alias |
| `backend/shared/rate_limits.py` | 97-103 | `"organization": {...}` | Backward-compat rate limit alias; same as above | Create Alembic migration to UPDATE users SET tier='enterprise' WHERE tier='organization', then remove alias |
| `backend/migrations/.../c1d2e3f4a5b6_remove_enterprise_tier.py` | 22-50 | `'team'`, `'enterprise'` | Historical migration — DB enum manipulation | Do not modify; migration history is immutable |
| `backend/migrations/.../c4d5e6f7a8b9_add_starter_team_usertier.py` | 26 | `'team'` | Historical migration — adds team to enum | Do not modify |
| `backend/migrations/.../d2e3f4a5b6c7_add_organization_tier.py` | 21-22 | `'organization'` | Historical migration — adds organization to enum | Do not modify |
| `backend/migrations/.../d5e6f7a8b9c0_add_subscriptions_table.py` | 26 | `'team'`, `'enterprise'` | Historical migration — creates subscription table | Do not modify |
| `backend/migrations/.../e3f4a5b6c7d8_pricing_v3_enum_restructure.py` | 27-63 | `'team'`, `'organization'` | Historical migration — restructures enums | Do not modify |
| `backend/tests/test_price_config.py` | 31, 35, 115, 120, 156 | `"team"`, `"organization"` | Tests that verify team/organization are REJECTED by current pricing config | Review: these tests validate correct behavior (old tiers rejected) — keep as-is |
| `backend/tests/test_rate_limit_tiered.py` | 500-501 | `"team"`, `"organization"` | Test data for rate limit tier iteration | Review: if backward-compat aliases removed, update test expectations |

---

## 4. Explicitly Not Changed

| Item | Rationale |
|------|-----------|
| All entitlement enforcement logic in `backend/shared/entitlements.py` | Constraint: no business logic changes. Only a comment block was added. |
| All pricing values ($100/$500/$1,000 monthly, $1,000/$5,000/$10,000 annual) | Constraint: no pricing changes. Values in docs were corrected to match code. |
| All route paths and URL paths | Constraint: no route/path renaming. |
| All component filenames | Constraint: no file renaming. |
| All DB-stored tier strings (`UserTier` enum values: free, solo, professional, enterprise) | Already correct in current codebase. Legacy migration references are historical. |
| Stripe integration logic and environment variable names (`STRIPE_PRICE_TEAM_*`) | Load-bearing: Stripe price IDs are mapped by env var name. Requires coordinated Stripe Dashboard + env var rename. |
| `backend/routes/organization.py` router prefix `/organization` | URL paths not in scope; existing clients may depend on this route. |
| Marketing page hero components (`HeroScrollSection`, `ToolSlideshow`, etc.) | These components already reference "twelve tools" correctly in their rendered copy. |
| Archive files (`tasks/archive/*`) | Historical records — never modified. |
| Frontend test files referencing "12 tools" or tool counts | Already correct. |

---

## 5. New Contradictions Discovered

| Location | Contradiction | Severity |
|----------|--------------|----------|
| `frontend/src/app/(marketing)/demo/page.tsx:14` | Comment references "5-tab DemoTabExplorer" — likely stale from 5-tool era | Low (code comment only) |
| `docs/07-user-facing/USER_GUIDE.md:13` | "Twelve specialized tools" in intro but "Ten supported file formats" — both correct but intro doesn't list all 12 tools inline | Low (informational) |
| `docs/website-usability-analysis.md` | References old pricing ($130–400/month), "Team" tier, "5 tools" for Solo — entire doc is stale | Medium (external-facing analysis) |
| `tasks/pricing-launch-qa.md` | References `STRIPE_PRICE_TEAM_*` env vars — Stripe env var names still use "team" | Medium (operational — requires CEO decision on Stripe rename timing) |
| `CLAUDE.md:104` | Era summary references "Solo/Team/Org" in historical context | Low (internal protocol doc, historical reference) |

---

## 6. Remaining Work

| Item | Blocker |
|------|---------|
| Stripe env var rename (`STRIPE_PRICE_TEAM_*` → `STRIPE_PRICE_PROFESSIONAL_*`) | Requires coordinated Stripe Dashboard product rename + env var update + deployment. CEO action. |
| DB migration: remove "team"/"organization" from rate_limits backward-compat aliases | Requires Alembic migration to update any remaining user records with old tier values. Low priority — aliases are harmless. |
| `docs/website-usability-analysis.md` full refresh | Stale external analysis — not urgent, retained for historical reference |
| `API_REFERENCE_GENERATED.md` narrative sections | Each router section has a "Narrative pending" placeholder — requires human-written usage context |
| Frontend component `DemoTabExplorer` comment update | Trivial — "5-tab" comment in demo page |
