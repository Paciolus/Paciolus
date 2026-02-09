"""
Follow-Up Items management with multi-tenant isolation.
Stores only narrative descriptions, never financial data.
"""

from datetime import datetime, UTC
from typing import Optional, Tuple, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Client
from engagement_model import Engagement, ToolRun, ToolName
from follow_up_items_model import (
    FollowUpItem,
    FollowUpItemComment,
    FollowUpSeverity,
    FollowUpDisposition,
)
from security_utils import log_secure_operation


class FollowUpItemsManager:
    """CRUD operations for follow-up items with engagement-scoped access."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Ownership helpers
    # ------------------------------------------------------------------

    def _verify_engagement_access(
        self, user_id: int, engagement_id: int
    ) -> Optional[Engagement]:
        """Verify engagement exists and user has access through client ownership."""
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id == user_id,
            )
            .first()
        )

    def _verify_item_access(
        self, user_id: int, item_id: int
    ) -> Optional[FollowUpItem]:
        """Verify follow-up item exists and user has access."""
        return (
            self.db.query(FollowUpItem)
            .join(Engagement, FollowUpItem.engagement_id == Engagement.id)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                FollowUpItem.id == item_id,
                Client.user_id == user_id,
            )
            .first()
        )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_item(
        self,
        user_id: int,
        engagement_id: int,
        description: str,
        tool_source: str,
        severity: FollowUpSeverity = FollowUpSeverity.MEDIUM,
        tool_run_id: Optional[int] = None,
        auditor_notes: Optional[str] = None,
    ) -> FollowUpItem:
        """Create a follow-up item. Validates engagement ownership."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        if not description or not description.strip():
            raise ValueError("Description is required")

        if not tool_source or not tool_source.strip():
            raise ValueError("Tool source is required")

        # Validate tool_run_id belongs to the same engagement
        if tool_run_id is not None:
            run = self.db.query(ToolRun).filter(
                ToolRun.id == tool_run_id,
                ToolRun.engagement_id == engagement_id,
            ).first()
            if not run:
                raise ValueError("Tool run not found or does not belong to this engagement")

        item = FollowUpItem(
            engagement_id=engagement_id,
            tool_run_id=tool_run_id,
            description=description.strip(),
            tool_source=tool_source.strip(),
            severity=severity,
            disposition=FollowUpDisposition.NOT_REVIEWED,
            auditor_notes=auditor_notes,
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        log_secure_operation(
            "follow_up_item_created",
            f"Follow-up item {item.id} created for engagement {engagement_id}",
        )

        return item

    def get_items(
        self,
        user_id: int,
        engagement_id: int,
        severity: Optional[FollowUpSeverity] = None,
        disposition: Optional[FollowUpDisposition] = None,
        tool_source: Optional[str] = None,
    ) -> List[FollowUpItem]:
        """List follow-up items for an engagement with optional filters."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        query = self.db.query(FollowUpItem).filter(
            FollowUpItem.engagement_id == engagement_id,
        )

        if severity is not None:
            query = query.filter(FollowUpItem.severity == severity)
        if disposition is not None:
            query = query.filter(FollowUpItem.disposition == disposition)
        if tool_source is not None:
            query = query.filter(FollowUpItem.tool_source == tool_source)

        return query.order_by(FollowUpItem.created_at.desc()).all()

    def update_item(
        self,
        user_id: int,
        item_id: int,
        disposition: Optional[FollowUpDisposition] = None,
        auditor_notes: Optional[str] = None,
        severity: Optional[FollowUpSeverity] = None,
    ) -> Optional[FollowUpItem]:
        """Update a follow-up item's disposition, notes, or severity."""
        item = self._verify_item_access(user_id, item_id)
        if not item:
            return None

        if disposition is not None:
            item.disposition = disposition
        if auditor_notes is not None:
            item.auditor_notes = auditor_notes
        if severity is not None:
            item.severity = severity

        item.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(item)

        log_secure_operation(
            "follow_up_item_updated",
            f"Follow-up item {item_id} updated by user {user_id}",
        )

        return item

    def delete_item(self, user_id: int, item_id: int) -> bool:
        """Delete a follow-up item. Returns True if deleted."""
        item = self._verify_item_access(user_id, item_id)
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()

        log_secure_operation(
            "follow_up_item_deleted",
            f"Follow-up item {item_id} deleted by user {user_id}",
        )

        return True

    # ------------------------------------------------------------------
    # Summary / aggregation
    # ------------------------------------------------------------------

    def get_summary(self, user_id: int, engagement_id: int) -> dict:
        """Get follow-up item counts grouped by severity, disposition, and tool source."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        items = self.db.query(FollowUpItem).filter(
            FollowUpItem.engagement_id == engagement_id,
        ).all()

        total = len(items)

        by_severity = {}
        by_disposition = {}
        by_tool_source = {}

        for item in items:
            sev = item.severity.value if item.severity else "unknown"
            by_severity[sev] = by_severity.get(sev, 0) + 1

            disp = item.disposition.value if item.disposition else "unknown"
            by_disposition[disp] = by_disposition.get(disp, 0) + 1

            src = item.tool_source or "unknown"
            by_tool_source[src] = by_tool_source.get(src, 0) + 1

        return {
            "total_count": total,
            "by_severity": by_severity,
            "by_disposition": by_disposition,
            "by_tool_source": by_tool_source,
        }

    # ------------------------------------------------------------------
    # Auto-population from tool runs
    # ------------------------------------------------------------------

    def auto_populate_from_tool_run(
        self,
        engagement_id: int,
        tool_run_id: int,
        tool_name: str,
        findings: List[dict],
    ) -> List[FollowUpItem]:
        """
        Auto-create follow-up items from tool run findings.

        Each finding dict must have:
          - description: str (narrative only — no account numbers or amounts)
          - severity: str ("high", "medium", or "low")

        Guardrail 2: descriptions are NARRATIVE ONLY.
        """
        created_items = []

        for finding in findings:
            description = finding.get("description", "").strip()
            if not description:
                continue

            severity_str = finding.get("severity", "medium").lower()
            try:
                severity = FollowUpSeverity(severity_str)
            except ValueError:
                severity = FollowUpSeverity.MEDIUM

            item = FollowUpItem(
                engagement_id=engagement_id,
                tool_run_id=tool_run_id,
                description=description,
                tool_source=tool_name,
                severity=severity,
                disposition=FollowUpDisposition.NOT_REVIEWED,
            )
            self.db.add(item)
            created_items.append(item)

        if created_items:
            self.db.commit()
            for item in created_items:
                self.db.refresh(item)

            log_secure_operation(
                "follow_up_auto_populated",
                f"{len(created_items)} follow-up items auto-created from {tool_name} for engagement {engagement_id}",
            )

        return created_items

    # ------------------------------------------------------------------
    # Comment CRUD (Sprint 112)
    # ------------------------------------------------------------------

    def _verify_comment_access(
        self, user_id: int, comment_id: int
    ) -> Optional[FollowUpItemComment]:
        """Verify comment exists and user has access through engagement ownership."""
        return (
            self.db.query(FollowUpItemComment)
            .join(FollowUpItem, FollowUpItemComment.follow_up_item_id == FollowUpItem.id)
            .join(Engagement, FollowUpItem.engagement_id == Engagement.id)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                FollowUpItemComment.id == comment_id,
                Client.user_id == user_id,
            )
            .first()
        )

    def create_comment(
        self,
        user_id: int,
        item_id: int,
        comment_text: str,
        parent_comment_id: Optional[int] = None,
    ) -> FollowUpItemComment:
        """Create a comment on a follow-up item. Validates item ownership."""
        item = self._verify_item_access(user_id, item_id)
        if not item:
            raise ValueError("Follow-up item not found or access denied")

        if not comment_text or not comment_text.strip():
            raise ValueError("Comment text is required")

        # Validate parent comment belongs to the same item
        if parent_comment_id is not None:
            parent = self.db.query(FollowUpItemComment).filter(
                FollowUpItemComment.id == parent_comment_id,
                FollowUpItemComment.follow_up_item_id == item_id,
            ).first()
            if not parent:
                raise ValueError("Parent comment not found or does not belong to this item")

        comment = FollowUpItemComment(
            follow_up_item_id=item_id,
            user_id=user_id,
            comment_text=comment_text.strip(),
            parent_comment_id=parent_comment_id,
        )

        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)

        log_secure_operation(
            "comment_created",
            f"Comment {comment.id} created on follow-up item {item_id} by user {user_id}",
        )

        return comment

    def get_comments(
        self,
        user_id: int,
        item_id: int,
    ) -> List[FollowUpItemComment]:
        """Get all comments for a follow-up item, ordered by creation time."""
        item = self._verify_item_access(user_id, item_id)
        if not item:
            raise ValueError("Follow-up item not found or access denied")

        return (
            self.db.query(FollowUpItemComment)
            .filter(FollowUpItemComment.follow_up_item_id == item_id)
            .order_by(FollowUpItemComment.created_at.asc())
            .all()
        )

    def update_comment(
        self,
        user_id: int,
        comment_id: int,
        comment_text: str,
    ) -> Optional[FollowUpItemComment]:
        """Update a comment's text. Only the comment author can edit."""
        comment = self._verify_comment_access(user_id, comment_id)
        if not comment:
            return None

        if comment.user_id != user_id:
            raise ValueError("Only the comment author can edit this comment")

        if not comment_text or not comment_text.strip():
            raise ValueError("Comment text is required")

        comment.comment_text = comment_text.strip()
        comment.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(comment)

        log_secure_operation(
            "comment_updated",
            f"Comment {comment_id} updated by user {user_id}",
        )

        return comment

    def delete_comment(self, user_id: int, comment_id: int) -> bool:
        """Delete a comment. Only the comment author can delete."""
        comment = self._verify_comment_access(user_id, comment_id)
        if not comment:
            return False

        if comment.user_id != user_id:
            raise ValueError("Only the comment author can delete this comment")

        self.db.delete(comment)
        self.db.commit()

        log_secure_operation(
            "comment_deleted",
            f"Comment {comment_id} deleted by user {user_id}",
        )

        return True

    def get_comments_for_engagement(
        self,
        user_id: int,
        engagement_id: int,
    ) -> List[FollowUpItemComment]:
        """Get all comments across all follow-up items for an engagement."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        return (
            self.db.query(FollowUpItemComment)
            .join(FollowUpItem, FollowUpItemComment.follow_up_item_id == FollowUpItem.id)
            .filter(FollowUpItem.engagement_id == engagement_id)
            .order_by(FollowUpItemComment.created_at.asc())
            .all()
        )
