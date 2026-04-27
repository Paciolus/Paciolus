"""
Expectation evaluation helper — Sprint 728c (ISA 520).

Bridges zero-storage tool engines (flux, ratio, multi-period TB) to the
persisted ``AnalyticalExpectation`` workpaper. The route layer calls this
helper after running the engine: it extracts measurements from the engine's
output, matches them to NOT_EVALUATED expectations on the supplied
engagement, computes variance + status, persists the result, and returns
records the route can surface inline in the API response.

This keeps entity types out of engine internals — the engines stay
zero-storage and tool-agnostic.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from analytical_expectations_manager import (
    AnalyticalExpectationsManager,
    evaluate_status,
)
from analytical_expectations_model import (
    AnalyticalExpectation,
    ExpectationResultStatus,
    ExpectationTargetType,
)
from engagement_model import Engagement
from models import Client


def _normalize_label(label: str) -> str:
    """Case-insensitive, whitespace-tolerant comparison key."""
    return label.strip().lower()


def evaluate_expectations_against_measurements(
    db: Session,
    user_id: int,
    engagement_id: int,
    measurements: list[tuple[ExpectationTargetType, str, float | Decimal]],
) -> list[dict[str, Any]]:
    """Match measurements to expectations, persist results, return records.

    ``measurements`` is a flat list of ``(target_type, target_label, actual)``
    triples. Multiple triples may map to a single expectation if the auditor
    used the same label across types (e.g., a "Revenue" account *and* a
    "Revenue" balance) — first match wins, ordered by ``measurements`` input.

    Only expectations currently in ``NOT_EVALUATED`` status are evaluated.
    Expectations already within/exceeds are left untouched (the auditor
    must explicitly clear via ``PATCH ... clear_result=true`` to re-run).

    Returns a list of {expectation_id, target_type, target_label, actual,
    variance, status} dicts in the order they were evaluated.
    """
    # Verify ownership before any DB mutations
    accessible_engagement = (
        db.query(Engagement)
        .join(Client, Engagement.client_id == Client.id)
        .filter(Engagement.id == engagement_id, Client.user_id == user_id)
        .first()
    )
    if accessible_engagement is None:
        # Org-based access path mirrors the manager helper
        from analytical_expectations_manager import AnalyticalExpectationsManager as _Mgr

        if _Mgr(db)._verify_engagement_access(user_id, engagement_id) is None:
            return []

    # Pull all NOT_EVALUATED expectations for this engagement once
    open_expectations = (
        db.query(AnalyticalExpectation)
        .filter(
            AnalyticalExpectation.engagement_id == engagement_id,
            AnalyticalExpectation.archived_at.is_(None),
            AnalyticalExpectation.result_status == ExpectationResultStatus.NOT_EVALUATED,
        )
        .all()
    )
    if not open_expectations:
        return []

    # Index by (target_type, normalized_label) for O(1) lookup
    index: dict[tuple[ExpectationTargetType, str], AnalyticalExpectation] = {}
    for exp in open_expectations:
        key = (exp.procedure_target_type, _normalize_label(exp.procedure_target_label))
        # Keep the first registered expectation for a (type,label) pair if
        # the auditor accidentally duplicated; the second one stays unevaluated
        # and the auditor can re-evaluate manually via PATCH.
        index.setdefault(key, exp)

    results: list[dict[str, Any]] = []
    consumed: set[int] = set()
    mgr = AnalyticalExpectationsManager(db)

    for target_type, label, actual in measurements:
        key = (target_type, _normalize_label(label))
        exp = index.get(key)
        if exp is None or exp.id in consumed:
            continue

        try:
            variance, status = evaluate_status(
                actual_value=actual,
                expected_value=exp.expected_value,
                expected_range_low=exp.expected_range_low,
                expected_range_high=exp.expected_range_high,
                precision_threshold_amount=exp.precision_threshold_amount,
                precision_threshold_percent=exp.precision_threshold_percent,
            )
        except ValueError:
            # Skip evaluations that hit edge conditions (e.g. percent vs zero)
            continue

        # Persist via the manager so the audit-trail log_secure_operation
        # fires consistently with manual updates.
        mgr.update_expectation(
            user_id=user_id,
            expectation_id=exp.id,
            result_actual_value=actual,
        )

        results.append(
            {
                "expectation_id": exp.id,
                "target_type": target_type.value,
                "target_label": exp.procedure_target_label,
                "actual": float(actual),
                "variance": float(variance),
                "status": status.value,
            }
        )
        consumed.add(exp.id)

    return results


# ---------------------------------------------------------------------------
# Tool-output extractors — emit (target_type, label, actual) triples
# ---------------------------------------------------------------------------


def extract_flux_measurements(
    flux_dict: dict[str, Any],
) -> list[tuple[ExpectationTargetType, str, float]]:
    """Pull both BALANCE and FLUX_LINE measurements from a flux result.

    For each flux item, emits two triples:
      - (BALANCE, account_name, current_balance) — for "what's the year-end balance"
      - (FLUX_LINE, account_name, delta_amount) — for "what's the period-over-period change"

    The auditor's expectation may target either; whichever matches by
    label gets evaluated. If the auditor recorded both an account-level
    and a flux-line expectation with the same label, both fire (separate
    rows).
    """
    items = flux_dict.get("items", [])
    out: list[tuple[ExpectationTargetType, str, float]] = []
    for item in items:
        account = item.get("account") or item.get("account_name")
        if not account or not isinstance(account, str):
            continue
        current = item.get("current") if "current" in item else item.get("current_balance")
        delta = item.get("delta_amount")
        if current is not None:
            out.append((ExpectationTargetType.BALANCE, account, float(current)))
            out.append((ExpectationTargetType.ACCOUNT, account, float(current)))
        if delta is not None:
            out.append((ExpectationTargetType.FLUX_LINE, account, float(delta)))
    return out


def extract_multi_period_measurements(
    result_dict: dict[str, Any],
) -> list[tuple[ExpectationTargetType, str, float]]:
    """Pull BALANCE/ACCOUNT measurements from a multi-period comparison result.

    Multi-period comparisons emit per-account current values; the auditor's
    expectation can target either an ACCOUNT or a BALANCE label.
    """
    items = result_dict.get("all_movements") or result_dict.get("movements") or result_dict.get("items") or []
    out: list[tuple[ExpectationTargetType, str, float]] = []
    for item in items:
        account = item.get("account") or item.get("account_name")
        if not account or not isinstance(account, str):
            continue
        # Multi-period uses "current_balance" or whichever-period-label-balance
        current = item.get("current_balance") or item.get("current") or item.get("current_period_balance")
        if current is not None:
            try:
                val = float(current)
            except (TypeError, ValueError):
                continue
            out.append((ExpectationTargetType.BALANCE, account, val))
            out.append((ExpectationTargetType.ACCOUNT, account, val))
    return out


def extract_ratio_measurements(
    ratios: dict[str, Any] | list[dict[str, Any]],
) -> list[tuple[ExpectationTargetType, str, float]]:
    """Pull RATIO measurements from a ratio computation result.

    Accepts either a flat ``{ratio_name: value}`` dict, or a list of
    ``{name, value}`` dicts (matching either of the two ratio response
    shapes the platform emits today).
    """
    out: list[tuple[ExpectationTargetType, str, float]] = []
    if isinstance(ratios, dict):
        for name, value in ratios.items():
            if isinstance(value, (int, float)):
                out.append((ExpectationTargetType.RATIO, name, float(value)))
            elif isinstance(value, dict) and "value" in value:
                try:
                    out.append((ExpectationTargetType.RATIO, name, float(value["value"])))
                except (TypeError, ValueError):
                    continue
    elif isinstance(ratios, list):
        for entry in ratios:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("ratio") or entry.get("label")
            value = entry.get("value")
            if isinstance(name, str) and isinstance(value, (int, float)):
                out.append((ExpectationTargetType.RATIO, name, float(value)))
    return out
