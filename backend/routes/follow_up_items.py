"""
Paciolus API — Follow-Up Items Routes
Phase X: Engagement Layer (narrative-only, Zero-Storage compliant)
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User
from auth import require_current_user
from follow_up_items_model import FollowUpSeverity, FollowUpDisposition, FollowUpItemComment
from follow_up_items_manager import FollowUpItemsManager

router = APIRouter(tags=["follow_up_items"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FollowUpItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)
    tool_source: str = Field(..., min_length=1, max_length=100)
    severity: str = "medium"
    tool_run_id: Optional[int] = None
    auditor_notes: Optional[str] = None


class FollowUpItemUpdate(BaseModel):
    disposition: Optional[str] = None
    auditor_notes: Optional[str] = None
    severity: Optional[str] = None
    assigned_to: Optional[int] = -1  # -1 = unchanged, None = unassign, int = assign


class FollowUpItemResponse(BaseModel):
    id: int
    engagement_id: int
    tool_run_id: Optional[int] = None
    description: str
    tool_source: str
    severity: str
    disposition: str
    auditor_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    created_at: str
    updated_at: str


class FollowUpItemListResponse(BaseModel):
    items: List[FollowUpItemResponse]
    total_count: int
    page: int
    page_size: int


class FollowUpSummaryResponse(BaseModel):
    total_count: int
    by_severity: dict
    by_disposition: dict
    by_tool_source: dict


# Sprint 112: Comment schemas
class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=5000)
    parent_comment_id: Optional[int] = None


class CommentUpdate(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    follow_up_item_id: int
    user_id: int
    author_name: Optional[str] = None
    comment_text: str
    parent_comment_id: Optional[int] = None
    created_at: str
    updated_at: str


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
        assigned_to=d.get("assigned_to"),
        created_at=d["created_at"] or "",
        updated_at=d["updated_at"] or "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/engagements/{engagement_id}/follow-up-items",
    response_model=FollowUpItemResponse,
    status_code=201,
)
def create_follow_up_item(
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
    response_model=FollowUpItemListResponse,
)
def list_follow_up_items(
    engagement_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
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

        offset = (page - 1) * page_size
        items, total = manager.get_items(
            user_id=current_user.id,
            engagement_id=engagement_id,
            severity=severity_enum,
            disposition=disposition_enum,
            tool_source=tool_source,
            limit=page_size,
            offset=offset,
        )

        return FollowUpItemListResponse(
            items=[_item_to_response(item) for item in items],
            total_count=total,
            page=page,
            page_size=page_size,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/engagements/{engagement_id}/follow-up-items/summary",
    response_model=FollowUpSummaryResponse,
)
def get_follow_up_summary(
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
def update_follow_up_item(
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
            assigned_to=data.assigned_to,
        )

        if not item:
            raise HTTPException(status_code=404, detail="Follow-up item not found")

        return _item_to_response(item)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/follow-up-items/{item_id}", status_code=204)
def delete_follow_up_item(
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


# ---------------------------------------------------------------------------
# Assignment endpoints (Sprint 113)
# ---------------------------------------------------------------------------

@router.get(
    "/engagements/{engagement_id}/follow-up-items/my-items",
    response_model=List[FollowUpItemResponse],
)
def get_my_items(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get follow-up items assigned to the current user."""
    manager = FollowUpItemsManager(db)

    try:
        items = manager.get_my_items(
            user_id=current_user.id,
            engagement_id=engagement_id,
        )
        return [_item_to_response(item) for item in items]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/engagements/{engagement_id}/follow-up-items/unassigned",
    response_model=List[FollowUpItemResponse],
)
def get_unassigned_items(
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get follow-up items with no assignee."""
    manager = FollowUpItemsManager(db)

    try:
        items = manager.get_unassigned_items(
            user_id=current_user.id,
            engagement_id=engagement_id,
        )
        return [_item_to_response(item) for item in items]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Comment endpoints (Sprint 112)
# ---------------------------------------------------------------------------

def _comment_to_response(comment) -> CommentResponse:
    d = comment.to_dict()
    return CommentResponse(
        id=d["id"],
        follow_up_item_id=d["follow_up_item_id"],
        user_id=d["user_id"],
        author_name=d.get("author_name"),
        comment_text=d["comment_text"],
        parent_comment_id=d["parent_comment_id"],
        created_at=d["created_at"] or "",
        updated_at=d["updated_at"] or "",
    )


@router.post(
    "/follow-up-items/{item_id}/comments",
    response_model=CommentResponse,
    status_code=201,
)
def create_comment(
    item_id: int,
    data: CommentCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Create a comment on a follow-up item."""
    log_secure_operation(
        "comment_create",
        f"User {current_user.id} creating comment on follow-up item {item_id}",
    )

    manager = FollowUpItemsManager(db)

    try:
        comment = manager.create_comment(
            user_id=current_user.id,
            item_id=item_id,
            comment_text=data.comment_text,
            parent_comment_id=data.parent_comment_id,
        )
        return _comment_to_response(comment)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/follow-up-items/{item_id}/comments",
    response_model=List[CommentResponse],
)
def list_comments(
    item_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """List all comments for a follow-up item."""
    manager = FollowUpItemsManager(db)

    try:
        comments = manager.get_comments(
            user_id=current_user.id,
            item_id=item_id,
        )
        return [_comment_to_response(c) for c in comments]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/comments/{comment_id}",
    response_model=CommentResponse,
)
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Update a comment's text. Only the author can edit."""
    log_secure_operation(
        "comment_update",
        f"User {current_user.id} updating comment {comment_id}",
    )

    manager = FollowUpItemsManager(db)

    try:
        comment = manager.update_comment(
            user_id=current_user.id,
            comment_id=comment_id,
            comment_text=data.comment_text,
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        return _comment_to_response(comment)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Delete a comment. Only the author can delete."""
    log_secure_operation(
        "comment_delete",
        f"User {current_user.id} deleting comment {comment_id}",
    )

    manager = FollowUpItemsManager(db)

    try:
        success = manager.delete_comment(current_user.id, comment_id)
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
