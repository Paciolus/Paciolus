"""
Paciolus API — Follow-Up Items Routes
Phase X: Engagement Layer (narrative-only, Zero-Storage compliant)
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User
from auth import require_current_user
from follow_up_items_model import FollowUpSeverity, FollowUpDisposition
from follow_up_items_manager import FollowUpItemsManager

router = APIRouter(tags=["follow-up-items"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FollowUpItemCreate(BaseModel):
    description: str
    tool_source: str
    severity: str = "medium"
    tool_run_id: Optional[int] = None
    auditor_notes: Optional[str] = None


class FollowUpItemUpdate(BaseModel):
    disposition: Optional[str] = None
    auditor_notes: Optional[str] = None
    severity: Optional[str] = None


class FollowUpItemResponse(BaseModel):
    id: int
    engagement_id: int
    tool_run_id: Optional[int] = None
    description: str
    tool_source: str
    severity: str
    disposition: str
    auditor_notes: Optional[str] = None
    created_at: str
    updated_at: str


class FollowUpSummaryResponse(BaseModel):
    total_count: int
    by_severity: dict
    by_disposition: dict
    by_tool_source: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _item_to_response(item) -> FollowUpItemResponse:
    d = item.to_dict()
    return FollowUpItemResponse(
        id=d["id"],
        engagement_id=d["engagement_id"],
        tool_run_id=d["tool_run_id"],
        description=d["description"],
        tool_source=d["tool_source"],
        severity=d["severity"] or "",
        disposition=d["disposition"] or "",
        auditor_notes=d["auditor_notes"],
        created_at=d["created_at"] or "",
        updated_at=d["updated_at"] or "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/engagements/{engagement_id}/follow-up-items",
    response_model=FollowUpItemResponse,
)
async def create_follow_up_item(
    engagement_id: int,
    data: FollowUpItemCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Create a follow-up item for an engagement."""
    log_secure_operation(
        "follow_up_item_create",
        f"User {current_user.id} creating follow-up item for engagement {engagement_id}",
    )

    manager = FollowUpItemsManager(db)

    try:
        severity = FollowUpSeverity(data.severity) if data.severity else FollowUpSeverity.MEDIUM

        item = manager.create_item(
            user_id=current_user.id,
            engagement_id=engagement_id,
            description=data.description,
            tool_source=data.tool_source,
            severity=severity,
            tool_run_id=data.tool_run_id,
            auditor_notes=data.auditor_notes,
        )

        return _item_to_response(item)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/engagements/{engagement_id}/follow-up-items",
    response_model=List[FollowUpItemResponse],
)
async def list_follow_up_items(
    engagement_id: int,
    severity: Optional[str] = Query(default=None),
    disposition: Optional[str] = Query(default=None),
    tool_source: Optional[str] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """List follow-up items for an engagement with optional filters."""
    manager = FollowUpItemsManager(db)

    try:
        severity_enum = FollowUpSeverity(severity) if severity else None
        disposition_enum = FollowUpDisposition(disposition) if disposition else None

        items = manager.get_items(
            user_id=current_user.id,
            engagement_id=engagement_id,
            severity=severity_enum,
            disposition=disposition_enum,
            tool_source=tool_source,
        )

        return [_item_to_response(item) for item in items]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/engagements/{engagement_id}/follow-up-items/summary",
    response_model=FollowUpSummaryResponse,
)
async def get_follow_up_summary(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get follow-up item counts grouped by severity, disposition, and tool source."""
    manager = FollowUpItemsManager(db)

    try:
        summary = manager.get_summary(
            user_id=current_user.id,
            engagement_id=engagement_id,
        )
        return FollowUpSummaryResponse(**summary)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/follow-up-items/{item_id}",
    response_model=FollowUpItemResponse,
)
async def update_follow_up_item(
    item_id: int,
    data: FollowUpItemUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Update a follow-up item's disposition, notes, or severity."""
    log_secure_operation(
        "follow_up_item_update",
        f"User {current_user.id} updating follow-up item {item_id}",
    )

    manager = FollowUpItemsManager(db)

    try:
        disposition_enum = FollowUpDisposition(data.disposition) if data.disposition else None
        severity_enum = FollowUpSeverity(data.severity) if data.severity else None

        item = manager.update_item(
            user_id=current_user.id,
            item_id=item_id,
            disposition=disposition_enum,
            auditor_notes=data.auditor_notes,
            severity=severity_enum,
        )

        if not item:
            raise HTTPException(status_code=404, detail="Follow-up item not found")

        return _item_to_response(item)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/follow-up-items/{item_id}")
async def delete_follow_up_item(
    item_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Delete a follow-up item."""
    log_secure_operation(
        "follow_up_item_delete",
        f"User {current_user.id} deleting follow-up item {item_id}",
    )

    manager = FollowUpItemsManager(db)
    success = manager.delete_item(current_user.id, item_id)

    if not success:
        raise HTTPException(status_code=404, detail="Follow-up item not found")

    return {
        "success": True,
        "message": "Follow-up item deleted",
        "item_id": item_id,
    }
