"""What an activity summary may hold (Sprint 879c, review DH-05).

The data statement says a saved analysis summary may hold totals, ratios,
counts and the names of flagged accounts — never account balances,
transaction rows or file contents. ``ToolActivity.summary_json`` used to take
any string (``POST /activity/tool-log``) or any dict (the internal recorder),
so nothing stopped a balance, a row array or file text from being saved.

Every summary now passes :func:`validate_activity_summary`, used by both entry
points. Each tool has an explicit schema of approved aggregate fields:

- unknown tools are rejected;
- unknown fields are rejected (``extra="forbid"``);
- every field is a scalar — a list, dict or string is rejected, so a row array,
  a nested object or quoted file text cannot be smuggled in;
- strict types — ``"12"`` is not an int, ``1`` is not a bool;
- counts are non-negative and bounded; scores are 0–100.

Adding a field is a deliberate change here, reviewed against the statement.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from engagement_model import ToolName

MAX_COUNT = 10_000_000


class ActivitySummaryError(ValueError):
    """A summary that is not an approved aggregate for its tool."""


class _Summary(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


Count = Field(default=None, ge=0, le=MAX_COUNT)


class TrialBalanceSummary(_Summary):
    was_balanced: Optional[bool] = None
    anomaly_count: Optional[int] = Count


class TestingToolSummary(_Summary):
    """Testing tools: how many items were flagged, and the composite score."""

    flagged_count: Optional[int] = Count
    composite_score: Optional[float] = Field(default=None, ge=0, le=100)


class DiagnosticSummary(_Summary):
    """Side diagnostics (pre-flight, population profile, …): counts only."""

    flagged_count: Optional[int] = Count


# Diagnostics recorded by ``services/audit/file_tool_scaffold.execute_file_tool``
# that are not engagement tools.
DIAGNOSTIC_TOOLS = ("preflight", "population_profile", "expense_category", "accrual_completeness")

SUMMARY_SCHEMAS: dict[str, type[_Summary]] = {
    **{t.value: TestingToolSummary for t in ToolName},
    ToolName.TRIAL_BALANCE.value: TrialBalanceSummary,
    **{t: DiagnosticSummary for t in DIAGNOSTIC_TOOLS},
}

KNOWN_TOOLS = frozenset(SUMMARY_SCHEMAS)


def validate_activity_summary(tool_name: str, summary: Any) -> Optional[dict[str, Any]]:
    """Return the summary as a clean dict, or raise :class:`ActivitySummaryError`.

    ``None`` and ``{}`` mean "no summary" and return ``None``. The error message
    lists the allowed fields and never echoes anything submitted.
    """
    schema = SUMMARY_SCHEMAS.get(tool_name)
    if schema is None:
        raise ActivitySummaryError("Unknown tool for an activity summary.")
    if summary is None or summary == {}:
        return None
    if not isinstance(summary, dict):
        raise ActivitySummaryError("An activity summary must be an object of approved fields.")
    try:
        model = schema.model_validate(summary)
    except ValidationError:
        # No field names either: a submitted key can itself carry a value.
        allowed = ", ".join(sorted(schema.model_fields))
        raise ActivitySummaryError(f"Activity summary rejected. Allowed fields for this tool: {allowed}.") from None
    clean = model.model_dump(exclude_none=True)
    return clean or None


def load_stored_summary(tool_name: str, summary_json: Optional[str]) -> Optional[dict[str, Any]]:
    """Parse a stored summary for display; anything that fails the schema is dropped."""
    if not summary_json:
        return None
    import json

    try:
        return validate_activity_summary(tool_name, json.loads(summary_json))
    except (ValueError, TypeError):
        return None
