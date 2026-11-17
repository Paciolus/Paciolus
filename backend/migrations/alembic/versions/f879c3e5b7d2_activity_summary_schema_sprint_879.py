"""Sprint 879c: remove stored activity summaries that are not approved aggregates.

Revision ID: f879c3e5b7d2
Revises: e879b2d4a6c1
Create Date: 2026-11-16

WHY
---
``tool_activities.summary_json`` accepted any string from ``POST
/activity/tool-log`` and any dict from the internal recorder (review DH-05).
Both now pass ``shared.activity_summary.validate_activity_summary``. This
clears (sets NULL) every stored summary that would fail it; the activity row
itself — tool, time, record count — is kept. There is no customer data yet
(CEO, 2026-11-16), so only test rows are affected.

The rules are frozen here as they stood in Sprint 879 rather than imported, so
the migration does not change if the schema module does.

Downgrade is a no-op: cleared values are not restored.
"""

import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "f879c3e5b7d2"
down_revision: str | Sequence[str] | None = "e879b2d4a6c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COUNT = ("int",)
_SCORE = ("int", "float")
_TESTING = {"flagged_count": _COUNT, "composite_score": _SCORE}
_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    **{
        t: _TESTING
        for t in (
            "multi_period",
            "journal_entry_testing",
            "ap_testing",
            "bank_reconciliation",
            "payroll_testing",
            "three_way_match",
            "revenue_testing",
            "ar_aging",
            "fixed_asset_testing",
            "inventory_testing",
            "statistical_sampling",
            "flux_analysis",
            "sod_checker",
            "intercompany_elimination",
            "w2_reconciliation",
            "form_1099",
            "book_to_tax",
            "cash_flow_projector",
        )
    },
    "trial_balance": {"was_balanced": ("bool",), "anomaly_count": _COUNT},
    **{
        t: {"flagged_count": _COUNT}
        for t in ("preflight", "population_profile", "expense_category", "accrual_completeness")
    },
}


def _kind(v: Any) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    return "other"


def _valid(tool: str, raw: str) -> bool:
    rules = _RULES.get(tool)
    if rules is None:
        return False
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return False
    if not isinstance(data, dict):
        return False
    for key, value in data.items():
        if value is None:
            continue
        allowed = rules.get(key)
        if allowed is None or _kind(value) not in allowed:
            return False
        if key != "composite_score" and _kind(value) == "int" and not 0 <= value <= 10_000_000:
            return False
        if key == "composite_score" and not 0 <= value <= 100:
            return False
    return True


def upgrade() -> None:
    bind = op.get_bind()
    if "tool_activities" not in sa.inspect(bind).get_table_names():
        return
    rows = bind.execute(
        sa.text("SELECT id, tool_name, summary_json FROM tool_activities WHERE summary_json IS NOT NULL")
    )
    bad = [r.id for r in rows if not _valid(r.tool_name, r.summary_json)]
    for i in range(0, len(bad), 500):
        bind.execute(
            sa.text("UPDATE tool_activities SET summary_json = NULL WHERE id IN :ids").bindparams(
                sa.bindparam("ids", expanding=True)
            ),
            {"ids": bad[i : i + 500]},
        )


def downgrade() -> None:
    pass
