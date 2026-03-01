"""
Engagement management with multi-tenant isolation.
Stores only engagement metadata, never financial data.
"""

import json
from collections import defaultdict
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from engagement_model import (
    Engagement,
    EngagementStatus,
    MaterialityBasis,
    ToolName,
    ToolRun,
    ToolRunStatus,
    validate_engagement_transition,
)
from follow_up_items_model import FollowUpDisposition, FollowUpItem
from models import Client
from security_utils import log_secure_operation
from shared.monetary import quantize_monetary


class EngagementManager:
    """CRUD operations for engagements with user-scoped data isolation."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Ownership helpers
    # ------------------------------------------------------------------

    def _validate_client_ownership(self, user_id: int, client_id: int) -> Client:
        """Validate that the client exists and belongs to the user."""
        client = (
            self.db.query(Client)
            .filter(
                Client.id == client_id,
                Client.user_id == user_id,
            )
            .first()
        )
        if not client:
            raise ValueError("Client not found or access denied")
        return client

    def _get_engagement_with_ownership(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        """Get engagement, verifying ownership through client join."""
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id == user_id,
            )
            .first()
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_engagement(
        self,
        user_id: int,
        client_id: int,
        period_start: datetime,
        period_end: datetime,
        materiality_basis: Optional[MaterialityBasis] = None,
        materiality_percentage: Optional[float] = None,
        materiality_amount: Optional[float] = None,
        performance_materiality_factor: float = 0.75,
        trivial_threshold_factor: float = 0.05,
    ) -> Engagement:
        """Create a new engagement. Validates client ownership and date order."""
        self._validate_client_ownership(user_id, client_id)

        if period_end <= period_start:
            raise ValueError("period_end must be after period_start")

        if materiality_percentage is not None and materiality_percentage < 0:
            raise ValueError("materiality_percentage cannot be negative")
        if materiality_amount is not None and materiality_amount < 0:
            raise ValueError("materiality_amount cannot be negative")
        if not (0 < performance_materiality_factor <= 1.0):
            raise ValueError("performance_materiality_factor must be between 0 (exclusive) and 1.0")
        if not (0 < trivial_threshold_factor <= 1.0):
            raise ValueError("trivial_threshold_factor must be between 0 (exclusive) and 1.0")

        engagement = Engagement(
            client_id=client_id,
            period_start=period_start,
            period_end=period_end,
            status=EngagementStatus.ACTIVE,
            materiality_basis=materiality_basis,
            materiality_percentage=materiality_percentage,
            materiality_amount=quantize_monetary(materiality_amount) if materiality_amount is not None else None,
            performance_materiality_factor=performance_materiality_factor,
            trivial_threshold_factor=trivial_threshold_factor,
            created_by=user_id,
        )

        self.db.add(engagement)
        self.db.commit()
        self.db.refresh(engagement)

        log_secure_operation(
            "engagement_created",
            f"Engagement {engagement.id} created for client {client_id} by user {user_id}",
        )

        return engagement

    def get_engagement(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        """Get a specific engagement, verifying ownership through client."""
        return self._get_engagement_with_ownership(user_id, engagement_id)

    def get_engagements_for_user(
        self,
        user_id: int,
        client_id: Optional[int] = None,
        status: Optional[EngagementStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Engagement], int]:
        """Get paginated engagements for a user with optional filters."""
        query = (
            self.db.query(Engagement).join(Client, Engagement.client_id == Client.id).filter(Client.user_id == user_id)
        )

        if client_id is not None:
            query = query.filter(Engagement.client_id == client_id)

        if status is not None:
            query = query.filter(Engagement.status == status)

        total = query.count()

        engagements = query.order_by(Engagement.updated_at.desc()).offset(offset).limit(limit).all()

        return engagements, total

    def update_engagement(
        self,
        user_id: int,
        engagement_id: int,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        status: Optional[EngagementStatus] = None,
        materiality_basis: Optional[MaterialityBasis] = None,
        materiality_percentage: Optional[float] = None,
        materiality_amount: Optional[float] = None,
        performance_materiality_factor: Optional[float] = None,
        trivial_threshold_factor: Optional[float] = None,
    ) -> Optional[Engagement]:
        """Update engagement fields. Returns None if not found."""
        engagement = self._get_engagement_with_ownership(user_id, engagement_id)
        if not engagement:
            return None

        if period_start is not None:
            engagement.period_start = period_start
        if period_end is not None:
            engagement.period_end = period_end

        # Validate date order after potential updates
        # Strip tzinfo for comparison (SQLite stores naive datetimes)
        eff_start = engagement.period_start.replace(tzinfo=None) if engagement.period_start else None
        eff_end = engagement.period_end.replace(tzinfo=None) if engagement.period_end else None
        if eff_start and eff_end and eff_end <= eff_start:
            raise ValueError("period_end must be after period_start")

        if status is not None:
            validate_engagement_transition(engagement.status, status)

            # Completion gate: all active follow-up items must be reviewed
            if status == EngagementStatus.COMPLETED:
                unresolved = (
                    self.db.query(FollowUpItem)
                    .filter(
                        FollowUpItem.engagement_id == engagement_id,
                        FollowUpItem.disposition == FollowUpDisposition.NOT_REVIEWED,
                        FollowUpItem.archived_at.is_(None),
                    )
                    .count()
                )
                if unresolved > 0:
                    raise ValueError(
                        f"Cannot complete engagement: {unresolved} follow-up item(s) "
                        f"still have 'not_reviewed' disposition"
                    )
                engagement.completed_at = datetime.now(UTC)
                engagement.completed_by = user_id

            engagement.status = status

        if materiality_basis is not None:
            engagement.materiality_basis = materiality_basis
        if materiality_percentage is not None:
            if materiality_percentage < 0:
                raise ValueError("materiality_percentage cannot be negative")
            engagement.materiality_percentage = materiality_percentage
        if materiality_amount is not None:
            if materiality_amount < 0:
                raise ValueError("materiality_amount cannot be negative")
            engagement.materiality_amount = quantize_monetary(materiality_amount)
        if performance_materiality_factor is not None:
            if not (0 < performance_materiality_factor <= 1.0):
                raise ValueError("performance_materiality_factor must be between 0 (exclusive) and 1.0")
            engagement.performance_materiality_factor = performance_materiality_factor
        if trivial_threshold_factor is not None:
            if not (0 < trivial_threshold_factor <= 1.0):
                raise ValueError("trivial_threshold_factor must be between 0 (exclusive) and 1.0")
            engagement.trivial_threshold_factor = trivial_threshold_factor

        engagement.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(engagement)

        log_secure_operation(
            "engagement_updated",
            f"Engagement {engagement_id} updated by user {user_id}",
        )

        return engagement

    def complete_engagement(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        """Mark engagement as completed. Enforces completion gate."""
        return self.update_engagement(user_id, engagement_id, status=EngagementStatus.COMPLETED)

    def archive_engagement(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        """Soft-delete: set status to ARCHIVED."""
        return self.update_engagement(user_id, engagement_id, status=EngagementStatus.ARCHIVED)

    # ------------------------------------------------------------------
    # Materiality cascade
    # ------------------------------------------------------------------

    def compute_materiality(self, engagement: Engagement) -> dict:
        """
        Compute materiality cascade from engagement parameters.

        Returns dict with:
          - overall_materiality: the base amount
          - performance_materiality: overall * PM factor
          - trivial_threshold: overall * trivial factor
          - basis, percentage, factors
        """
        overall = float(engagement.materiality_amount or 0)

        pm = float(quantize_monetary(overall * engagement.performance_materiality_factor))
        trivial = float(quantize_monetary(overall * engagement.trivial_threshold_factor))

        return {
            "overall_materiality": overall,
            "performance_materiality": pm,
            "trivial_threshold": trivial,
            "materiality_basis": (engagement.materiality_basis.value if engagement.materiality_basis else None),
            "materiality_percentage": engagement.materiality_percentage,
            "performance_materiality_factor": engagement.performance_materiality_factor,
            "trivial_threshold_factor": engagement.trivial_threshold_factor,
        }

    # ------------------------------------------------------------------
    # Tool runs
    # ------------------------------------------------------------------

    def record_tool_run(
        self,
        engagement_id: int,
        tool_name: ToolName,
        status: ToolRunStatus,
        composite_score: Optional[float] = None,
        flagged_accounts: Optional[list[str]] = None,
    ) -> ToolRun:
        """Record a tool run, auto-incrementing run_number per (engagement, tool)."""
        max_run = (
            self.db.query(func.max(ToolRun.run_number))
            .filter(
                ToolRun.engagement_id == engagement_id,
                ToolRun.tool_name == tool_name,
            )
            .scalar()
        )
        next_run = (max_run or 0) + 1

        tool_run = ToolRun(
            engagement_id=engagement_id,
            tool_name=tool_name,
            run_number=next_run,
            status=status,
            composite_score=composite_score,
            flagged_accounts=json.dumps(flagged_accounts) if flagged_accounts else None,
        )

        self.db.add(tool_run)
        self.db.commit()
        self.db.refresh(tool_run)

        log_secure_operation(
            "tool_run_recorded",
            f"Tool run {tool_name.value} #{next_run} for engagement {engagement_id}",
        )

        return tool_run

    def get_tool_runs(self, engagement_id: int) -> list[ToolRun]:
        """Get all active tool runs for an engagement, ordered by run_at."""
        return (
            self.db.query(ToolRun)
            .filter(
                ToolRun.engagement_id == engagement_id,
                ToolRun.archived_at.is_(None),
            )
            .order_by(ToolRun.run_at.desc())
            .all()
        )

    def get_tool_run_trends(self, engagement_id: int) -> list[dict]:
        """Per-tool score trend from completed runs with non-null composite_score.

        For each tool with 1+ qualifying runs:
        - latest_score: most recent composite_score
        - previous_score: second-most-recent (None if only 1 run)
        - score_delta: latest - previous (None if only 1 run)
        - direction: 'improving' (delta < -1), 'degrading' (delta > 1), 'stable'
        - run_count: total qualifying runs

        Scores represent flag density — lower = fewer flags = improving.

        Returns list sorted by tool_name.
        """
        runs = (
            self.db.query(ToolRun)
            .filter(
                ToolRun.engagement_id == engagement_id,
                ToolRun.status == ToolRunStatus.COMPLETED,
                ToolRun.composite_score.isnot(None),
                ToolRun.archived_at.is_(None),
            )
            .order_by(ToolRun.tool_name, ToolRun.run_at.desc(), ToolRun.id.desc())
            .all()
        )

        # Group by tool_name
        runs_by_tool: dict[str, list[ToolRun]] = {}
        for run in runs:
            key = run.tool_name.value if run.tool_name else ""
            runs_by_tool.setdefault(key, []).append(run)

        result = []
        for tool_key in sorted(runs_by_tool.keys()):
            tool_runs = runs_by_tool[tool_key]
            latest = tool_runs[0]
            previous = tool_runs[1] if len(tool_runs) >= 2 else None

            entry: dict = {
                "tool_name": tool_key,
                "latest_score": latest.composite_score,
                "previous_score": previous.composite_score if previous else None,
                "score_delta": None,
                "direction": None,
                "run_count": len(tool_runs),
            }

            if previous is not None and latest.composite_score is not None and previous.composite_score is not None:
                delta = round(latest.composite_score - previous.composite_score, 2)
                entry["score_delta"] = delta
                if delta < -1.0:
                    entry["direction"] = "improving"
                elif delta > 1.0:
                    entry["direction"] = "degrading"
                else:
                    entry["direction"] = "stable"

            result.append(entry)

        return result

    def get_convergence_index(self, engagement_id: int) -> list[dict]:
        """Aggregate flagged accounts across the latest completed run of each tool.

        Returns list of {account, tools_flagging_it, convergence_count} sorted by
        convergence_count desc then account name asc.

        NO composite score, NO risk classification — raw convergence counts only.
        """
        # Get all active completed runs with flagged_accounts for this engagement
        runs = (
            self.db.query(ToolRun)
            .filter(
                ToolRun.engagement_id == engagement_id,
                ToolRun.status == ToolRunStatus.COMPLETED,
                ToolRun.flagged_accounts.isnot(None),
                ToolRun.archived_at.is_(None),
            )
            .order_by(ToolRun.run_at.desc(), ToolRun.run_number.desc())
            .all()
        )

        # Keep only the latest run per tool
        latest_by_tool: dict[str, ToolRun] = {}
        for run in runs:
            tool_key = run.tool_name.value if run.tool_name else ""
            if tool_key not in latest_by_tool:
                latest_by_tool[tool_key] = run

        # Aggregate: account -> set of tool_names
        account_tools: dict[str, set[str]] = defaultdict(set)
        for tool_key, run in latest_by_tool.items():
            accounts = json.loads(run.flagged_accounts) if run.flagged_accounts else []
            for account in accounts:
                if account and isinstance(account, str):
                    account_tools[account.strip()].add(tool_key)

        # Build sorted result
        result = [
            {
                "account": account,
                "tools_flagging_it": sorted(tools),
                "convergence_count": len(tools),
            }
            for account, tools in account_tools.items()
            if account  # skip empty
        ]

        result.sort(key=lambda x: (-int(x["convergence_count"]), x["account"]))
        return result
