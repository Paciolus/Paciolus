# Phase XLVI: Audit History Immutability — Sprint Details

## Overview
Converted all hard-delete paths for 5 audit history tables to soft-delete (archive) semantics with an ORM-level deletion guard. Audit evidence is now **append-only at the application level** — once a diagnostic run, follow-up item, or activity log is recorded, it can never be physically erased.

## Protected Tables (5)
| Table | Previous hard-delete path | New behavior |
|-------|--------------------------|-------------|
| `activity_logs` | `DELETE /activity/clear` (bulk wipe) | Bulk `archived_at` update |
| `activity_logs` | Retention cleanup (365-day purge) | Bulk `archived_at` update |
| `diagnostic_summaries` | Retention cleanup (365-day purge) | Bulk `archived_at` update |
| `follow_up_items` | `DELETE /follow-up-items/{id}` | Single-row `archived_at` update |
| `follow_up_item_comments` | `DELETE /comments/{id}` | Single-row `archived_at` update |
| `tool_runs` | No direct delete endpoint (CASCADE theoretical) | ORM guard blocks physical deletion |

## Sprint 345: SoftDeleteMixin + Alembic Migration (4/10) — COMPLETE
- [x] Create `backend/shared/soft_delete.py` with `SoftDeleteMixin`, helper functions, deletion guard
- [x] Add `SoftDeleteMixin` to 5 models (ActivityLog, DiagnosticSummary, ToolRun, FollowUpItem, FollowUpItemComment)
- [x] Update `to_dict()` methods on all 5 models to include archived_at/archived_by/archive_reason
- [x] Create Alembic migration `b2c3d4e5f6a7` (3 columns + index on 5 tables)
- [x] Register `register_deletion_guard()` in `main.py` lifespan
- [x] Register guard in `tests/conftest.py` for test sessions
- [x] Fix AmbiguousForeignKeysError: add `foreign_keys` to ActivityLog.user, DiagnosticSummary.user, FollowUpItemComment.author, and User reverse relationships

## Sprint 346: Route Conversions — Activity + Retention (3/10) — COMPLETE
- [x] `routes/activity.py`: `clear_activity_history()` → `soft_delete_bulk(reason="user_clear_history")`
- [x] `routes/activity.py`: `get_activity_history()` + `get_dashboard_stats()` → `archived_at IS NULL` filter
- [x] `retention_cleanup.py`: Both functions → `.update(archived_at, archive_reason="retention_policy")`
- [x] `cleanup_scheduler.py`: `records_deleted` → `records_processed` telemetry label

## Sprint 347: Route Conversions — FollowUpItems + Comments (4/10) — COMPLETE
- [x] `follow_up_items_manager.py` `delete_item()` → `soft_delete()` + archive child comments
- [x] `follow_up_items_manager.py` `delete_comment()` → `soft_delete()` + archive child replies
- [x] Add `archived_at IS NULL` filter to all read queries (10 methods)

## Sprint 348: Read Path Hardening — Diagnostics + Engagement (4/10) — COMPLETE
- [x] `routes/diagnostics.py` — previous summary, history queries
- [x] `routes/prior_period.py` — list periods, compare queries
- [x] `routes/trends.py` — `_get_client_summaries`, industry ratios latest-summary
- [x] `engagement_manager.py` — `get_tool_runs`, `get_tool_run_trends`, `get_convergence_index`
- [x] `anomaly_summary_generator.py` — ToolRun + FollowUpItem queries
- [x] `workpaper_index_generator.py` — ToolRun + FollowUpItem queries
- [x] `engagement_export.py` — FollowUpItem description lookup

## Sprint 349: Test Suite + Phase Wrap (5/10) — COMPLETE
- [x] Create `test_audit_immutability.py` with 26 tests across 5 classes
  - TestOrmDeletionGuard (7): guard blocks all 5 protected models, allows non-protected
  - TestSoftDeleteBehavior (8): single + bulk soft-delete, parent cascades, retention
  - TestReadPathExclusion (6): archived records excluded from all read paths
  - TestImmutabilityProof (3): records physically exist, row count never decreases, timestamp accurate
  - TestRetentionSoftDelete (3): activity log + diagnostic summary retention archives, idempotent
- [x] Fix `test_retention_cleanup.py` (2 tests): update assertions from physical deletion to soft-delete
- [x] Fix `test_cleanup_scheduler.py` (3 tests): `records_deleted` → `records_processed` field name
- [x] Fix `test_engagement.py` (2 tests): cascade delete → guard verification
- [x] Fix `test_finding_comments.py` (1 test): physical absence → archived_at check
- [x] Fix `test_follow_up_items.py` (1 test): ToolRun delete → guard verification
- [x] Fix `engagement_manager.py` flaky ordering: add `ToolRun.id.desc()` secondary sort
- [x] Full regression: 3,867 backend tests passed, frontend build passed

## Key Files
| File | Action |
|------|--------|
| `backend/shared/soft_delete.py` | CREATED |
| `backend/models.py` | MODIFIED (ActivityLog, DiagnosticSummary + User relationships) |
| `backend/engagement_model.py` | MODIFIED (ToolRun) |
| `backend/follow_up_items_model.py` | MODIFIED (FollowUpItem, FollowUpItemComment) |
| `backend/main.py` | MODIFIED (register guard in lifespan) |
| `backend/tests/conftest.py` | MODIFIED (register guard in test setup) |
| `backend/migrations/alembic/versions/b2c3d4e5f6a7_add_soft_delete_columns.py` | CREATED |
| `backend/routes/activity.py` | MODIFIED |
| `backend/retention_cleanup.py` | MODIFIED |
| `backend/cleanup_scheduler.py` | MODIFIED |
| `backend/follow_up_items_manager.py` | MODIFIED |
| `backend/routes/diagnostics.py` | MODIFIED |
| `backend/routes/prior_period.py` | MODIFIED |
| `backend/routes/trends.py` | MODIFIED |
| `backend/engagement_manager.py` | MODIFIED |
| `backend/anomaly_summary_generator.py` | MODIFIED |
| `backend/workpaper_index_generator.py` | MODIFIED |
| `backend/engagement_export.py` | MODIFIED |
| `backend/tests/test_audit_immutability.py` | CREATED (26 tests) |
| `backend/tests/test_retention_cleanup.py` | MODIFIED (2 tests updated) |
| `backend/tests/test_cleanup_scheduler.py` | MODIFIED (3 tests updated) |
| `backend/tests/test_engagement.py` | MODIFIED (2 tests updated) |
| `backend/tests/test_finding_comments.py` | MODIFIED (1 test updated) |
| `backend/tests/test_follow_up_items.py` | MODIFIED (1 test updated) |
