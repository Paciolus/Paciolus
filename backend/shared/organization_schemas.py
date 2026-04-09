"""
Organization, Admin Dashboard, Branding, Bulk Upload, and Export Sharing
response models.

Sprint 576: AUDIT-11-F002/F003 — add Pydantic response_model to all
previously untyped JSON routes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------


class OrganizationResponse(BaseModel):
    """Response for Organization CRUD endpoints."""

    id: int
    name: str
    slug: str
    owner_user_id: int
    subscription_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class OrganizationWithMemberCountResponse(OrganizationResponse):
    """GET /organization — includes member_count."""

    member_count: int = 0


class OrganizationMemberResponse(BaseModel):
    """Single member entry returned by list-members and update-role."""

    id: int
    organization_id: int
    user_id: int
    role: str | None = None
    joined_at: str | None = None
    invited_by_user_id: int | None = None
    # Enriched fields added by the route handler
    user_name: str | None = None
    user_email: str | None = None

    model_config = {"from_attributes": True}


class OrganizationInviteResponse(BaseModel):
    """Single invite entry returned by list-invites."""

    id: int
    organization_id: int
    invitee_email: str
    role: str | None = None
    status: str | None = None
    created_at: str | None = None
    expires_at: str | None = None
    accepted_at: str | None = None

    model_config = {"from_attributes": True}


class OrganizationInviteCreateResponse(OrganizationInviteResponse):
    """POST /organization/invite — includes the plaintext invite_token."""

    invite_token: str


class DetailResponse(BaseModel):
    """Generic response containing a detail message."""

    detail: str


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------


class AdminOverviewResponse(BaseModel):
    """GET /admin/overview — dashboard summary."""

    total_members: int
    uploads_this_month: int
    active_members_30d: int
    tool_usage: dict[str, int] = Field(default_factory=dict)
    organization_name: str


class TeamActivityEntryResponse(BaseModel):
    """Single entry in the team-activity list."""

    id: int
    organization_id: int
    user_id: int
    action_type: str | None = None
    tool_name: str | None = None
    created_at: str | None = None
    # Enriched field
    user_name: str | None = None

    model_config = {"from_attributes": True}


class UsageByMemberResponse(BaseModel):
    """Single entry in the usage-by-member list."""

    user_id: int
    user_name: str
    uploads: int


# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------


class BrandingResponse(BaseModel):
    """Response for branding GET/PUT/POST-logo endpoints."""

    id: int
    organization_id: int
    has_logo: bool = False
    logo_content_type: str | None = None
    logo_size_bytes: int | None = None
    header_text: str | None = None
    footer_text: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Bulk Upload
# ---------------------------------------------------------------------------


class BulkUploadStartResponse(BaseModel):
    """POST /upload/bulk — initiation response."""

    job_id: str
    total_files: int
    status: str


class BulkFileStatusEntry(BaseModel):
    """Single file entry in the bulk job status."""

    filename: str | None = None
    status: str
    error: str | None = None


class BulkUploadStatusResponse(BaseModel):
    """GET /upload/bulk/{job_id}/status — poll response."""

    job_id: str
    status: str
    completed_count: int
    total_count: int
    files: list[BulkFileStatusEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Export Sharing
# ---------------------------------------------------------------------------


class ExportShareResponse(BaseModel):
    """Single export-share entry (list and create)."""

    id: int
    tool_name: str
    export_format: str
    shared_by_name: str | None = None
    created_at: str | None = None
    expires_at: str | None = None
    revoked_at: str | None = None
    access_count: int = 0
    single_use: bool = False
    has_passcode: bool = False

    model_config = {"from_attributes": True}


class ExportShareCreateResponse(ExportShareResponse):
    """POST /export-sharing/create — includes the plaintext share_token."""

    share_token: str
