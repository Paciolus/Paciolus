"""
Analytical Expectations management — Sprint 728a (ISA 520).

CRUD operations for AnalyticalExpectation entities with engagement-scoped
multi-tenant isolation. Mirrors the FollowUpItemsManager pattern: ownership
flows through engagement → client.user_id (direct or org-based).

ZERO-STORAGE EXCEPTION: This module persists only auditor expectation
metadata + comparison results. Underlying tool data stays ephemeral.
"""

import json
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from analytical_expectations_model import (
    VALID_CORROBORATION_TAGS,
    AnalyticalExpectation,
    ExpectationResultStatus,
    ExpectationTargetType,
)
from engagement_model import Engagement
from models import Client, User
from security_utils import log_secure_operation
from shared.monetary import quantize_monetary
from shared.soft_delete import soft_delete


def _quantize(value: Optional[float | Decimal]) -> Optional[Decimal]:
    """Coerce a numeric input to monetary precision, returning None if absent."""
    if value is None:
        return None
    return quantize_monetary(value)


def _validate_threshold(amount: Optional[Decimal | float], percent: Optional[float]) -> None:
    """Precision threshold is amount XOR percent, not both, not neither."""
    has_amount = amount is not None
    has_percent = percent is not None
    if has_amount and has_percent:
        raise ValueError("precision threshold accepts either amount or percent, not both")
    if not has_amount and not has_percent:
        raise ValueError("precision threshold (amount or percent) is required")
    if has_percent and (percent is None or percent <= 0):
        raise ValueError("precision_threshold_percent must be positive")
    if has_amount and amount is not None and Decimal(str(amount)) <= 0:
        raise ValueError("precision_threshold_amount must be positive")


def _validate_expected(
    expected_value: Optional[Decimal | float],
    expected_range_low: Optional[Decimal | float],
    expected_range_high: Optional[Decimal | float],
) -> None:
    """Either a single expected value OR a (low, high) range — not both, not neither."""
    has_value = expected_value is not None
    has_range = expected_range_low is not None or expected_range_high is not None

    if has_value and has_range:
        raise ValueError("provide either expected_value or expected_range_low/high, not both")
    if not has_value and not has_range:
        raise ValueError("expected_value or expected_range_low/high is required")
    if has_range:
        if expected_range_low is None or expected_range_high is None:
            raise ValueError("expected_range_low and expected_range_high must both be provided")
        if Decimal(str(expected_range_high)) <= Decimal(str(expected_range_low)):
            raise ValueError("expected_range_high must be greater than expected_range_low")


def _validate_tags(tags: list[str]) -> list[str]:
    """Validate and de-dupe corroboration tags against the enum."""
    if not isinstance(tags, list):
        raise ValueError("corroboration_tags must be a list")
    cleaned: list[str] = []
    for t in tags:
        if not isinstance(t, str):
            raise ValueError("corroboration_tags entries must be strings")
        if t not in VALID_CORROBORATION_TAGS:
            raise ValueError(f"unknown corroboration tag '{t}'. Valid tags: {sorted(VALID_CORROBORATION_TAGS)}")
        if t not in cleaned:
            cleaned.append(t)
    return cleaned


def evaluate_status(
    actual_value: Decimal | float,
    expected_value: Optional[Decimal] = None,
    expected_range_low: Optional[Decimal] = None,
    expected_range_high: Optional[Decimal] = None,
    precision_threshold_amount: Optional[Decimal] = None,
    precision_threshold_percent: Optional[float] = None,
) -> tuple[Decimal, ExpectationResultStatus]:
    """Compute (variance, within/exceeds) for an actual against an expectation.

    Pure function — no DB access. Used by the manager when CPAs PATCH
    a result, and (in 728c) by tool wiring to auto-populate result fields.

    Variance is signed (actual - expected for value mode; nearest-edge
    distance for range mode). Status compares |variance| against the
    precision threshold.
    """
    actual = Decimal(str(actual_value))

    if expected_value is not None:
        expected = Decimal(str(expected_value))
        variance = actual - expected
        ref_for_percent = expected
    else:
        if expected_range_low is None or expected_range_high is None:
            raise ValueError("either expected_value or both expected_range_low/high must be supplied")
        low = Decimal(str(expected_range_low))
        high = Decimal(str(expected_range_high))
        if low <= actual <= high:
            variance = Decimal("0")
        elif actual < low:
            variance = actual - low
        else:
            variance = actual - high
        ref_for_percent = (low + high) / Decimal("2")

    abs_variance = abs(variance)

    if precision_threshold_amount is not None:
        threshold_dec = Decimal(str(precision_threshold_amount))
    else:
        if precision_threshold_percent is None:
            raise ValueError("precision_threshold_amount or precision_threshold_percent is required")
        # Percent thresholds are computed against the absolute reference value
        # so that a percent threshold against an expected of 0 raises rather
        # than silently rounding to "always within" — caller must use an
        # amount threshold when expected is 0.
        if ref_for_percent == 0:
            raise ValueError(
                "percent threshold cannot be evaluated against a zero reference; use precision_threshold_amount instead"
            )
        threshold_dec = abs(ref_for_percent) * Decimal(str(precision_threshold_percent)) / Decimal("100")

    status = (
        ExpectationResultStatus.WITHIN_THRESHOLD
        if abs_variance <= threshold_dec
        else ExpectationResultStatus.EXCEEDS_THRESHOLD
    )

    return quantize_monetary(variance), status


class AnalyticalExpectationsManager:
    """CRUD operations for analytical expectations with engagement-scoped access."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Ownership helpers — mirrored from FollowUpItemsManager
    # ------------------------------------------------------------------

    def _get_accessible_user_ids(self, user_id: int) -> list[int]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.organization_id:
            return [user_id]

        from organization_model import OrganizationMember

        member_ids = (
            self.db.query(OrganizationMember.user_id)
            .filter(OrganizationMember.organization_id == user.organization_id)
            .all()
        )
        return [m[0] for m in member_ids] if member_ids else [user_id]

    def _verify_engagement_access(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        accessible_ids = self._get_accessible_user_ids(user_id)
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id.in_(accessible_ids),
            )
            .first()
        )

    def _verify_expectation_access(self, user_id: int, expectation_id: int) -> Optional[AnalyticalExpectation]:
        accessible_ids = self._get_accessible_user_ids(user_id)
        return (
            self.db.query(AnalyticalExpectation)
            .join(Engagement, AnalyticalExpectation.engagement_id == Engagement.id)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                AnalyticalExpectation.id == expectation_id,
                Client.user_id.in_(accessible_ids),
                AnalyticalExpectation.archived_at.is_(None),
            )
            .first()
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_expectation(
        self,
        user_id: int,
        engagement_id: int,
        procedure_target_type: ExpectationTargetType,
        procedure_target_label: str,
        corroboration_basis_text: str,
        corroboration_tags: list[str],
        expected_value: Optional[float | Decimal] = None,
        expected_range_low: Optional[float | Decimal] = None,
        expected_range_high: Optional[float | Decimal] = None,
        precision_threshold_amount: Optional[float | Decimal] = None,
        precision_threshold_percent: Optional[float] = None,
        cpa_notes: Optional[str] = None,
    ) -> AnalyticalExpectation:
        """Create a new analytical expectation. Validates ownership + XOR rules."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        if not procedure_target_label or not procedure_target_label.strip():
            raise ValueError("procedure_target_label is required")
        if not corroboration_basis_text or not corroboration_basis_text.strip():
            raise ValueError("corroboration_basis_text is required")

        _validate_expected(expected_value, expected_range_low, expected_range_high)
        _validate_threshold(precision_threshold_amount, precision_threshold_percent)
        cleaned_tags = _validate_tags(corroboration_tags)
        if not cleaned_tags:
            raise ValueError("at least one corroboration_tag is required")

        expectation = AnalyticalExpectation(
            engagement_id=engagement_id,
            procedure_target_type=procedure_target_type,
            procedure_target_label=procedure_target_label.strip(),
            expected_value=_quantize(expected_value),
            expected_range_low=_quantize(expected_range_low),
            expected_range_high=_quantize(expected_range_high),
            precision_threshold_amount=_quantize(precision_threshold_amount),
            precision_threshold_percent=precision_threshold_percent,
            corroboration_basis_text=corroboration_basis_text.strip(),
            corroboration_tags_json=json.dumps(cleaned_tags),
            cpa_notes=cpa_notes.strip() if cpa_notes else None,
            result_status=ExpectationResultStatus.NOT_EVALUATED,
            created_by=user_id,
        )

        self.db.add(expectation)
        self.db.commit()
        self.db.refresh(expectation)

        log_secure_operation(
            "analytical_expectation_created",
            f"Expectation {expectation.id} for engagement {engagement_id} by user {user_id}",
        )
        return expectation

    def get_expectation(self, user_id: int, expectation_id: int) -> Optional[AnalyticalExpectation]:
        return self._verify_expectation_access(user_id, expectation_id)

    def list_expectations(
        self,
        user_id: int,
        engagement_id: int,
        result_status: Optional[ExpectationResultStatus] = None,
        target_type: Optional[ExpectationTargetType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AnalyticalExpectation], int]:
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        query = self.db.query(AnalyticalExpectation).filter(
            AnalyticalExpectation.engagement_id == engagement_id,
            AnalyticalExpectation.archived_at.is_(None),
        )
        if result_status is not None:
            query = query.filter(AnalyticalExpectation.result_status == result_status)
        if target_type is not None:
            query = query.filter(AnalyticalExpectation.procedure_target_type == target_type)

        total = query.count()
        items = query.order_by(AnalyticalExpectation.created_at.asc()).offset(offset).limit(limit).all()
        return items, total

    def update_expectation(
        self,
        user_id: int,
        expectation_id: int,
        *,
        procedure_target_label: Optional[str] = None,
        expected_value: Optional[float | Decimal] = None,
        expected_range_low: Optional[float | Decimal] = None,
        expected_range_high: Optional[float | Decimal] = None,
        precision_threshold_amount: Optional[float | Decimal] = None,
        precision_threshold_percent: Optional[float] = None,
        corroboration_basis_text: Optional[str] = None,
        corroboration_tags: Optional[list[str]] = None,
        cpa_notes: Optional[str] = None,
        result_actual_value: Optional[float | Decimal] = None,
        clear_result: bool = False,
    ) -> Optional[AnalyticalExpectation]:
        """Update fields on an existing expectation.

        ``result_actual_value`` triggers a status recompute via
        ``evaluate_status``; ``clear_result=True`` resets the row to
        NOT_EVALUATED. Other fields are simple overwrites; XOR rules are
        re-validated when the affected fields change.
        """
        expectation = self._verify_expectation_access(user_id, expectation_id)
        if expectation is None:
            return None

        if procedure_target_label is not None:
            if not procedure_target_label.strip():
                raise ValueError("procedure_target_label cannot be empty")
            expectation.procedure_target_label = procedure_target_label.strip()

        # Re-validate expected value/range as a unit if any of those three change
        expected_changed = (
            expected_value is not None or expected_range_low is not None or expected_range_high is not None
        )
        if expected_changed:
            new_value = (
                expected_value
                if expected_value is not None
                else (
                    None
                    if expected_range_low is not None or expected_range_high is not None
                    else expectation.expected_value
                )
            )
            new_low = (
                expected_range_low
                if expected_range_low is not None
                else (None if expected_value is not None else expectation.expected_range_low)
            )
            new_high = (
                expected_range_high
                if expected_range_high is not None
                else (None if expected_value is not None else expectation.expected_range_high)
            )
            _validate_expected(new_value, new_low, new_high)
            expectation.expected_value = _quantize(new_value)
            expectation.expected_range_low = _quantize(new_low)
            expectation.expected_range_high = _quantize(new_high)

        threshold_changed = precision_threshold_amount is not None or precision_threshold_percent is not None
        if threshold_changed:
            new_amt = (
                precision_threshold_amount
                if precision_threshold_amount is not None
                else (None if precision_threshold_percent is not None else expectation.precision_threshold_amount)
            )
            new_pct = (
                precision_threshold_percent
                if precision_threshold_percent is not None
                else (None if precision_threshold_amount is not None else expectation.precision_threshold_percent)
            )
            _validate_threshold(new_amt, new_pct)
            expectation.precision_threshold_amount = _quantize(new_amt)
            expectation.precision_threshold_percent = new_pct

        if corroboration_basis_text is not None:
            if not corroboration_basis_text.strip():
                raise ValueError("corroboration_basis_text cannot be empty")
            expectation.corroboration_basis_text = corroboration_basis_text.strip()

        if corroboration_tags is not None:
            cleaned = _validate_tags(corroboration_tags)
            if not cleaned:
                raise ValueError("at least one corroboration_tag is required")
            expectation.corroboration_tags_json = json.dumps(cleaned)

        if cpa_notes is not None:
            expectation.cpa_notes = cpa_notes.strip() if cpa_notes else None

        if clear_result:
            expectation.result_actual_value = None
            expectation.result_variance_amount = None
            expectation.result_status = ExpectationResultStatus.NOT_EVALUATED
        elif result_actual_value is not None:
            variance, status = evaluate_status(
                actual_value=result_actual_value,
                expected_value=expectation.expected_value,
                expected_range_low=expectation.expected_range_low,
                expected_range_high=expectation.expected_range_high,
                precision_threshold_amount=expectation.precision_threshold_amount,
                precision_threshold_percent=expectation.precision_threshold_percent,
            )
            expectation.result_actual_value = _quantize(result_actual_value)
            expectation.result_variance_amount = variance
            expectation.result_status = status

        expectation.updated_by = user_id
        self.db.commit()
        self.db.refresh(expectation)

        log_secure_operation(
            "analytical_expectation_updated",
            f"Expectation {expectation_id} updated by user {user_id}",
        )
        return expectation

    def archive_expectation(
        self, user_id: int, expectation_id: int, reason: Optional[str] = None
    ) -> Optional[AnalyticalExpectation]:
        """Soft-delete an expectation."""
        expectation = self._verify_expectation_access(user_id, expectation_id)
        if expectation is None:
            return None
        soft_delete(self.db, expectation, user_id=user_id, reason=reason or "")
        log_secure_operation(
            "analytical_expectation_archived",
            f"Expectation {expectation_id} archived by user {user_id}",
        )
        return expectation

    # ------------------------------------------------------------------
    # Completion-gate support
    # ------------------------------------------------------------------

    def count_unevaluated(self, engagement_id: int) -> int:
        """Active (non-archived) expectations still in NOT_EVALUATED status.

        Used by the engagement-completion gate to block engagement transition
        to COMPLETED when expectations remain unevaluated.
        """
        return (
            self.db.query(AnalyticalExpectation)
            .filter(
                AnalyticalExpectation.engagement_id == engagement_id,
                AnalyticalExpectation.archived_at.is_(None),
                AnalyticalExpectation.result_status == ExpectationResultStatus.NOT_EVALUATED,
            )
            .count()
        )
