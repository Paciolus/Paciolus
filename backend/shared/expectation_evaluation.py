"""
Expectation evaluation helper — Sprint 728c (ISA 520); proposals only since Sprint 879b.

Bridges zero-storage tool engines (flux, ratio, multi-period TB) to the
``AnalyticalExpectation`` workpaper. The route layer calls this helper after
running the engine: it extracts measurements from the engine's output, matches
them to NOT_EVALUATED expectations on the supplied engagement, computes
variance + status, and returns **proposals** the route surfaces in the
response. Nothing is persisted here: the auditor captures a proposal
explicitly (``shared.expectation_capture``).

This keeps entity types out of engine internals — the engines stay
zero-storage and tool-agnostic.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

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


def _normalize_label(label: str) -> str:
    """Case-insensitive, whitespace-tolerant comparison key."""
    return label.strip().lower()


def propose_expectation_actuals(
    db: Session,
    user_id: int,
    engagement_id: int,
    measurements: list[tuple[ExpectationTargetType, str, float | Decimal]],
    *,
    source: str,
    tool_run_id: Optional[int],
) -> list[dict[str, Any]]:
    """Match measurements to open expectations and propose an actual for each.

    **Writes nothing** (Sprint 879b, review DH-04). The previous helper saved
    each match's value — an account's balance — into the workpaper during the
    analysis request. Each proposal now carries a signed ``capture_token``; the
    auditor saves it with ``POST .../analytical-expectations/capture-actuals``.

    ``measurements`` is a flat list of ``(target_type, target_label, actual)``
    triples; first match wins per expectation. Only ``NOT_EVALUATED``
    expectations get a proposal — a captured actual is cleared explicitly
    ("Re-evaluate") before it can be replaced.

    Returns {expectation_id, target_type, target_label, actual, variance,
    status, capture_token} dicts in match order.
    """
    from shared.expectation_capture import sign_capture

    # Verify access before reading — the manager's rule, the same one every
    # engagement route uses (Sprint 853).
    if AnalyticalExpectationsManager(db)._verify_engagement_access(user_id, engagement_id) is None:
        return []

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

    # Index by (target_type, normalized_label); keep the first registered
    # expectation if the auditor duplicated a (type, label) pair.
    index: dict[tuple[ExpectationTargetType, str], AnalyticalExpectation] = {}
    for exp in open_expectations:
        index.setdefault((exp.procedure_target_type, _normalize_label(exp.procedure_target_label)), exp)

    results: list[dict[str, Any]] = []
    consumed: set[int] = set()
    for target_type, label, actual in measurements:
        exp = index.get((target_type, _normalize_label(label)))
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
        results.append(
            {
                "expectation_id": exp.id,
                "target_type": target_type.value,
                "target_label": exp.procedure_target_label,
                "actual": float(actual),
                "variance": float(variance),
                "status": status.value,
                "capture_token": sign_capture(
                    user_id=user_id,
                    engagement_id=engagement_id,
                    expectation_id=exp.id,
                    actual=actual,
                    source=source,
                    tool_run_id=tool_run_id,
                ),
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
