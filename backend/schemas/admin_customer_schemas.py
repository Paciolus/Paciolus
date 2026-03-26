"""
Pydantic schemas for internal admin customer console.

Sprint 590: Superadmin CRM — customer list, detail, admin actions, audit log.
"""

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Customer List
# ---------------------------------------------------------------------------


class CustomerSummary(BaseModel):
    """Summary row for the customer list view."""

    user_id: int
    org_id: int | None = None
    org_name: str | None = None
    owner_email: str
    owner_name: str | None = None
    plan: str = "free"
    status: str = "active"
    billing_interval: str | None = None
    mrr: float = 0.0
    signup_date: str
    last_login: str | None = None
    uploads_this_period: int = 0
    total_reports_generated: int = 0
    is_verified: bool = False


class CustomerListResponse(BaseModel):
    """Paginated customer list response."""

    items: list[CustomerSummary]
    total: int
    offset: int
    limit: int


# ---------------------------------------------------------------------------
# Customer Detail
# ---------------------------------------------------------------------------


class MemberInfo(BaseModel):
    user_id: int
    email: str
    name: str | None = None
    role: str
    joined_at: str | None = None


class BillingEventEntry(BaseModel):
    id: int
    event_type: str
    tier: str | None = None
    interval: str | None = None
    metadata_json: str | None = None
    created_at: str


class ActivityEntry(BaseModel):
    id: int
    filename_display: str | None = None
    record_count: int = 0
    timestamp: str


class SubscriptionDetail(BaseModel):
    id: int | None = None
    tier: str = "free"
    status: str = "active"
    billing_interval: str | None = None
    seat_count: int = 1
    additional_seats: int = 0
    total_seats: int = 1
    uploads_used_current_period: int = 0
    cancel_at_period_end: bool = False
    current_period_start: str | None = None
    current_period_end: str | None = None
    stripe_customer_id: str | None = None
    created_at: str | None = None


class CustomerDetailResponse(BaseModel):
    """Full customer account profile."""

    user_id: int
    org_id: int | None = None
    org_name: str | None = None
    owner_email: str
    owner_name: str | None = None
    is_verified: bool = False
    signup_date: str
    last_login: str | None = None

    members: list[MemberInfo] = Field(default_factory=list)
    subscription: SubscriptionDetail | None = None
    billing_events: list[BillingEventEntry] = Field(default_factory=list)
    recent_activity: list[ActivityEntry] = Field(default_factory=list)
    usage_stats: dict = Field(default_factory=dict)
    active_session_count: int = 0


# ---------------------------------------------------------------------------
# Admin Action Requests
# ---------------------------------------------------------------------------


class PlanOverrideRequest(BaseModel):
    new_plan: str = Field(pattern="^(solo|professional|enterprise)$")
    reason: str = Field(min_length=1, max_length=500)
    effective_immediately: bool = True


class TrialExtensionRequest(BaseModel):
    days: int = Field(ge=1, le=90)
    reason: str = Field(min_length=1, max_length=500)


class CreditRequest(BaseModel):
    amount_cents: int = Field(ge=1, le=1_000_000)
    reason: str = Field(min_length=1, max_length=500)


class RefundRequest(BaseModel):
    payment_intent_id: str = Field(min_length=1, max_length=255)
    amount_cents: int = Field(ge=1, le=1_000_000)
    reason: str = Field(min_length=1, max_length=500)


class ForceCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    immediate: bool = False


# ---------------------------------------------------------------------------
# Admin Action Responses
# ---------------------------------------------------------------------------


class AdminActionResponse(BaseModel):
    """Standard response for admin actions."""

    success: bool = True
    message: str
    audit_log_id: int


# ---------------------------------------------------------------------------
# Impersonation
# ---------------------------------------------------------------------------


class ImpersonationResponse(BaseModel):
    access_token: str
    expires_at: str
    target_user_id: int
    target_email: str
    is_impersonation: bool = True


# ---------------------------------------------------------------------------
# Admin Audit Log
# ---------------------------------------------------------------------------


class AuditLogEntry(BaseModel):
    id: int
    admin_user_id: int
    admin_email: str | None = None
    action_type: str
    target_org_id: int | None = None
    target_user_id: int | None = None
    details_json: str | None = None
    ip_address: str | None = None
    created_at: str


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    offset: int
    limit: int
