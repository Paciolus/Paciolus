"""
Follow-Up Item Schemas — extracted from routes/follow_up_items.py (Sprint 544).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from follow_up_items_model import FollowUpDisposition, FollowUpSeverity


class FollowUpItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=2000)
    tool_source: str = Field(..., min_length=1, max_length=100)
    severity: FollowUpSeverity = FollowUpSeverity.MEDIUM
    tool_run_id: Optional[int] = None
    auditor_notes: Optional[str] = None


class FollowUpItemUpdate(BaseModel):
    disposition: Optional[FollowUpDisposition] = None
    auditor_notes: Optional[str] = None
    severity: Optional[FollowUpSeverity] = None
    assigned_to: Optional[int] = -1  # -1 = unchanged, None = unassign, int = assign


class FollowUpItemResponse(BaseModel):
    id: int
    engagement_id: int
    tool_run_id: Optional[int] = None
    description: str
    tool_source: str
    severity: Literal["high", "medium", "low"]
    disposition: Literal[
        "not_reviewed",
        "investigated_no_issue",
        "investigated_adjustment_posted",
        "investigated_further_review",
        "immaterial",
    ]
    auditor_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    created_at: str
    updated_at: str


class FollowUpSummaryResponse(BaseModel):
    total_count: int
    by_severity: dict
    by_disposition: dict
    by_tool_source: dict


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
