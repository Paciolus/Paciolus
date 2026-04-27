"""
Uncorrected Misstatements management — Sprint 729a (ISA 450).

CRUD + aggregation logic for the SUM schedule. Mirrors the
AnalyticalExpectationsManager shape: engagement-scoped multi-tenant
ownership, soft-delete via SoftDeleteMixin, manager-layer validation
for invariants the model can't express.

The aggregation surface (``compute_sum_schedule``) returns the rows,
the per-classification subtotals, the aggregate, and the materiality
bucket — used by the API + the SUM memo PDF generator.
"""

import json
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from engagement_manager import EngagementManager
from engagement_model import Engagement
from models import Client, User
from security_utils import log_secure_operation
from shared.monetary import quantize_monetary
from shared.soft_delete import soft_delete
from uncorrected_misstatements_model import (
    MaterialityBucket,
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
    UncorrectedMisstatement,
)


def _quantize(value: Optional[float | Decimal]) -> Optional[Decimal]:
    if value is None:
        return None
    return quantize_monetary(value)


def _validate_accounts_affected(payload: list[dict]) -> list[dict]:
    """Validate the JSON shape of accounts_affected.

    Each entry must be ``{"account": str, "debit_credit": "DR"|"CR", "amount": str|float}``.
    Returns a normalized copy with amount stringified.
    """
    if not isinstance(payload, list):
        raise ValueError("accounts_affected must be a list")
    if not payload:
        raise ValueError("at least one account row is required")

    cleaned: list[dict] = []
    for idx, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise ValueError(f"accounts_affected[{idx}] must be an object")
        account = entry.get("account")
        debit_credit = entry.get("debit_credit")
        amount = entry.get("amount")
        if not isinstance(account, str) or not account.strip():
            raise ValueError(f"accounts_affected[{idx}].account must be a non-empty string")
        if debit_credit not in {"DR", "CR"}:
            raise ValueError(f"accounts_affected[{idx}].debit_credit must be 'DR' or 'CR'")
        try:
            amount_dec = Decimal(str(amount))
        except Exception as exc:  # pragma: no cover — defensive
            raise ValueError(f"accounts_affected[{idx}].amount is not numeric") from exc
        if amount_dec <= 0:
            raise ValueError(f"accounts_affected[{idx}].amount must be positive (sign comes from debit_credit)")
        cleaned.append(
            {
                "account": account.strip(),
                "debit_credit": debit_credit,
                "amount": str(quantize_monetary(amount_dec)),
            }
        )
    return cleaned


def compute_materiality_bucket(
    aggregate: Decimal,
    overall_materiality: Decimal,
    performance_materiality: Decimal,
    trivial_threshold: Decimal,
) -> MaterialityBucket:
    """Compute the SUM bucket from |aggregate| against the materiality cascade.

    Boundaries (per the Sprint 728/729 plan):
      - |agg| <= trivial_threshold      → CLEARLY_TRIVIAL
      - |agg| <= performance_materiality → IMMATERIAL
      - |agg| <= overall_materiality     → APPROACHING_MATERIAL
      - |agg| >  overall_materiality     → MATERIAL

    "Approaching material" is the platform's UX bucket between performance
    and overall materiality — documented in docs/04-compliance/isa-450-coverage.md.
    """
    abs_agg = abs(aggregate)
    if abs_agg <= trivial_threshold:
        return MaterialityBucket.CLEARLY_TRIVIAL
    if abs_agg <= performance_materiality:
        return MaterialityBucket.IMMATERIAL
    if abs_agg <= overall_materiality:
        return MaterialityBucket.APPROACHING_MATERIAL
    return MaterialityBucket.MATERIAL


class UncorrectedMisstatementsManager:
    """CRUD + aggregation for the SUM schedule with engagement-scoped access."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Ownership helpers
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

    def _verify_misstatement_access(self, user_id: int, misstatement_id: int) -> Optional[UncorrectedMisstatement]:
        accessible_ids = self._get_accessible_user_ids(user_id)
        return (
            self.db.query(UncorrectedMisstatement)
            .join(Engagement, UncorrectedMisstatement.engagement_id == Engagement.id)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                UncorrectedMisstatement.id == misstatement_id,
                Client.user_id.in_(accessible_ids),
                UncorrectedMisstatement.archived_at.is_(None),
            )
            .first()
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_misstatement(
        self,
        user_id: int,
        engagement_id: int,
        source_type: MisstatementSourceType,
        source_reference: str,
        description: str,
        accounts_affected: list[dict],
        classification: MisstatementClassification,
        fs_impact_net_income: float | Decimal,
        fs_impact_net_assets: float | Decimal,
        cpa_disposition: MisstatementDisposition = MisstatementDisposition.NOT_YET_REVIEWED,
        cpa_notes: Optional[str] = None,
    ) -> UncorrectedMisstatement:
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        if not source_reference or not source_reference.strip():
            raise ValueError("source_reference is required")
        if not description or not description.strip():
            raise ValueError("description is required")

        cleaned_accounts = _validate_accounts_affected(accounts_affected)

        misstatement = UncorrectedMisstatement(
            engagement_id=engagement_id,
            source_type=source_type,
            source_reference=source_reference.strip(),
            description=description.strip(),
            accounts_affected_json=json.dumps(cleaned_accounts),
            classification=classification,
            fs_impact_net_income=quantize_monetary(fs_impact_net_income),
            fs_impact_net_assets=quantize_monetary(fs_impact_net_assets),
            cpa_disposition=cpa_disposition,
            cpa_notes=cpa_notes.strip() if cpa_notes else None,
            created_by=user_id,
        )
        self.db.add(misstatement)
        self.db.commit()
        self.db.refresh(misstatement)

        log_secure_operation(
            "uncorrected_misstatement_created",
            f"Misstatement {misstatement.id} for engagement {engagement_id} by user {user_id}",
        )
        return misstatement

    def get_misstatement(self, user_id: int, misstatement_id: int) -> Optional[UncorrectedMisstatement]:
        return self._verify_misstatement_access(user_id, misstatement_id)

    def list_misstatements(
        self,
        user_id: int,
        engagement_id: int,
        classification: Optional[MisstatementClassification] = None,
        source_type: Optional[MisstatementSourceType] = None,
        disposition: Optional[MisstatementDisposition] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[UncorrectedMisstatement], int]:
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        query = self.db.query(UncorrectedMisstatement).filter(
            UncorrectedMisstatement.engagement_id == engagement_id,
            UncorrectedMisstatement.archived_at.is_(None),
        )
        if classification is not None:
            query = query.filter(UncorrectedMisstatement.classification == classification)
        if source_type is not None:
            query = query.filter(UncorrectedMisstatement.source_type == source_type)
        if disposition is not None:
            query = query.filter(UncorrectedMisstatement.cpa_disposition == disposition)

        total = query.count()
        items = query.order_by(UncorrectedMisstatement.created_at.asc()).offset(offset).limit(limit).all()
        return items, total

    def update_misstatement(
        self,
        user_id: int,
        misstatement_id: int,
        *,
        source_reference: Optional[str] = None,
        description: Optional[str] = None,
        accounts_affected: Optional[list[dict]] = None,
        classification: Optional[MisstatementClassification] = None,
        fs_impact_net_income: Optional[float | Decimal] = None,
        fs_impact_net_assets: Optional[float | Decimal] = None,
        cpa_disposition: Optional[MisstatementDisposition] = None,
        cpa_notes: Optional[str] = None,
    ) -> Optional[UncorrectedMisstatement]:
        m = self._verify_misstatement_access(user_id, misstatement_id)
        if m is None:
            return None

        if source_reference is not None:
            if not source_reference.strip():
                raise ValueError("source_reference cannot be empty")
            m.source_reference = source_reference.strip()
        if description is not None:
            if not description.strip():
                raise ValueError("description cannot be empty")
            m.description = description.strip()
        if accounts_affected is not None:
            cleaned = _validate_accounts_affected(accounts_affected)
            m.accounts_affected_json = json.dumps(cleaned)
        if classification is not None:
            m.classification = classification
        if fs_impact_net_income is not None:
            m.fs_impact_net_income = quantize_monetary(fs_impact_net_income)
        if fs_impact_net_assets is not None:
            m.fs_impact_net_assets = quantize_monetary(fs_impact_net_assets)
        if cpa_disposition is not None:
            m.cpa_disposition = cpa_disposition
        if cpa_notes is not None:
            m.cpa_notes = cpa_notes.strip() if cpa_notes else None

        m.updated_by = user_id
        self.db.commit()
        self.db.refresh(m)

        log_secure_operation(
            "uncorrected_misstatement_updated",
            f"Misstatement {misstatement_id} updated by user {user_id}",
        )
        return m

    def archive_misstatement(
        self, user_id: int, misstatement_id: int, reason: Optional[str] = None
    ) -> Optional[UncorrectedMisstatement]:
        m = self._verify_misstatement_access(user_id, misstatement_id)
        if m is None:
            return None
        soft_delete(self.db, m, user_id=user_id, reason=reason or "")
        log_secure_operation(
            "uncorrected_misstatement_archived",
            f"Misstatement {misstatement_id} archived by user {user_id}",
        )
        return m

    # ------------------------------------------------------------------
    # Aggregation — SUM schedule view
    # ------------------------------------------------------------------

    def compute_sum_schedule(self, user_id: int, engagement_id: int) -> dict:
        """Build the SUM schedule payload for an engagement.

        Per ISA 450 §A4: factual + judgmental misstatements are evaluated
        together; projected misstatements (sampling extrapolations) are
        reported separately. Both groups feed the materiality bucket.
        """
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        items, _ = self.list_misstatements(user_id, engagement_id, limit=10_000)

        factual_judgmental_income = Decimal("0.00")
        factual_judgmental_assets = Decimal("0.00")
        projected_income = Decimal("0.00")
        projected_assets = Decimal("0.00")

        for m in items:
            if m.classification == MisstatementClassification.PROJECTED:
                projected_income += m.fs_impact_net_income
                projected_assets += m.fs_impact_net_assets
            else:
                factual_judgmental_income += m.fs_impact_net_income
                factual_judgmental_assets += m.fs_impact_net_assets

        aggregate_income = factual_judgmental_income + projected_income
        aggregate_assets = factual_judgmental_assets + projected_assets

        materiality = EngagementManager(self.db).compute_materiality(engagement)
        overall = Decimal(str(materiality["overall_materiality"]))
        performance = Decimal(str(materiality["performance_materiality"]))
        trivial = Decimal(str(materiality["trivial_threshold"]))

        # Bucket uses the LARGER of |agg_income| and |agg_assets| as the
        # driver — both are F/S-relevant; the auditor needs the worst-case.
        driver = max(abs(aggregate_income), abs(aggregate_assets))
        bucket = compute_materiality_bucket(driver, overall, performance, trivial)

        unreviewed_count = sum(1 for m in items if m.cpa_disposition == MisstatementDisposition.NOT_YET_REVIEWED)

        return {
            "items": [m.to_dict() for m in items],
            "subtotals": {
                "factual_judgmental_net_income": quantize_monetary(factual_judgmental_income),
                "factual_judgmental_net_assets": quantize_monetary(factual_judgmental_assets),
                "projected_net_income": quantize_monetary(projected_income),
                "projected_net_assets": quantize_monetary(projected_assets),
            },
            "aggregate": {
                "net_income": quantize_monetary(aggregate_income),
                "net_assets": quantize_monetary(aggregate_assets),
                "driver": quantize_monetary(driver),
            },
            "materiality": {
                "overall": quantize_monetary(overall),
                "performance": quantize_monetary(performance),
                "trivial": quantize_monetary(trivial),
            },
            "bucket": bucket.value,
            "unreviewed_count": unreviewed_count,
            "engagement_id": engagement_id,
        }

    # ------------------------------------------------------------------
    # Completion-gate support
    # ------------------------------------------------------------------

    def count_unreviewed(self, engagement_id: int) -> int:
        return (
            self.db.query(UncorrectedMisstatement)
            .filter(
                UncorrectedMisstatement.engagement_id == engagement_id,
                UncorrectedMisstatement.archived_at.is_(None),
                UncorrectedMisstatement.cpa_disposition == MisstatementDisposition.NOT_YET_REVIEWED,
            )
            .count()
        )

    def has_material_aggregate(self, engagement_id: int, user_id: int) -> bool:
        """True if the SUM aggregate is in the MATERIAL bucket.

        Used by the completion gate's override-required-when-MATERIAL rule.
        Returns False for engagements with no items or no materiality set.
        """
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if engagement is None or engagement.materiality_amount is None:
            return False
        try:
            schedule = self.compute_sum_schedule(user_id, engagement_id)
        except ValueError:
            return False
        return schedule["bucket"] == MaterialityBucket.MATERIAL.value

    def has_documented_override(self, engagement_id: int) -> bool:
        """True if at least one non-archived misstatement carries CPA notes
        documenting an override decision (used when MATERIAL aggregate is
        accepted as immaterial per CPA judgment).
        """
        return (
            self.db.query(UncorrectedMisstatement)
            .filter(
                UncorrectedMisstatement.engagement_id == engagement_id,
                UncorrectedMisstatement.archived_at.is_(None),
                UncorrectedMisstatement.cpa_notes.isnot(None),
                UncorrectedMisstatement.cpa_notes != "",
            )
            .count()
        ) > 0
