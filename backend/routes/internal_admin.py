"""
Internal admin routes — Sprint 590: Superadmin customer console.

All endpoints require `is_superadmin` platform-level access.
Customer list, detail, admin actions (plan override, trial extension,
credit, refund, cancel, impersonation), and audit log.

Route group prefix: /internal/admin
"""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from auth import require_superadmin
from database import get_db
from models import User
from schemas.admin_customer_schemas import (
    AdminActionResponse,
    AuditLogResponse,
    CreditRequest,
    CustomerDetailResponse,
    CustomerListResponse,
    ForceCancelRequest,
    ImpersonationResponse,
    PlanOverrideRequest,
    RefundRequest,
    TrialExtensionRequest,
)
from security_middleware import get_client_ip
from shared.rate_limits import RATE_LIMIT_DEFAULT, RATE_LIMIT_WRITE, limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/admin", tags=["internal-admin"])


# ---------------------------------------------------------------------------
# Customer List & Detail
# ---------------------------------------------------------------------------


@router.get("/customers/", response_model=CustomerListResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def list_customers(
    request: Request,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sort_by: str = Query(default="created_at", pattern="^(created_at|last_login|email)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    plan: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None, max_length=200),
    signup_after: str | None = Query(default=None),
    signup_before: str | None = Query(default=None),
) -> dict[str, Any]:
    """Paginated customer list with sorting, filtering, and search."""
    from billing.admin_customers import get_customer_list

    parsed_after = None
    parsed_before = None
    if signup_after:
        try:
            parsed_after = datetime.strptime(signup_after, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid signup_after format. Use YYYY-MM-DD.")
    if signup_before:
        try:
            parsed_before = datetime.strptime(signup_before, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid signup_before format. Use YYYY-MM-DD.")

    return get_customer_list(
        db,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_dir=sort_dir,
        plan=plan,
        status=status_filter,
        search=search,
        signup_after=parsed_after,
        signup_before=parsed_before,
    )


@router.get("/customers/{org_id}", response_model=CustomerDetailResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_customer_detail(
    request: Request,
    org_id: int,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Full customer account profile."""
    from billing.admin_customers import get_customer_detail as _get_detail

    result = _get_detail(db, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return result


# ---------------------------------------------------------------------------
# Admin Actions
# ---------------------------------------------------------------------------


@router.post("/customers/{org_id}/plan-override", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def plan_override(
    request: Request,
    org_id: int,
    body: PlanOverrideRequest,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Override a customer's plan."""
    from billing.admin_customers import admin_plan_override

    try:
        result = admin_plan_override(
            db,
            org_id,
            body.new_plan,
            body.reason,
            body.effective_immediately,
            admin_user_id=admin.id,
            ip_address=get_client_ip(request),
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/customers/{org_id}/extend-trial", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def extend_trial(
    request: Request,
    org_id: int,
    body: TrialExtensionRequest,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Extend a customer's trial period."""
    from billing.admin_customers import admin_extend_trial

    try:
        result = admin_extend_trial(
            db,
            org_id,
            body.days,
            body.reason,
            admin_user_id=admin.id,
            ip_address=get_client_ip(request),
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/customers/{org_id}/credit", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def issue_credit(
    request: Request,
    org_id: int,
    body: CreditRequest,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Issue a credit to a customer's Stripe balance."""
    from billing.admin_customers import admin_issue_credit

    try:
        result = admin_issue_credit(
            db,
            org_id,
            body.amount_cents,
            body.reason,
            admin_user_id=admin.id,
            ip_address=get_client_ip(request),
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to issue credit for org %d", org_id)
        raise HTTPException(status_code=502, detail="Payment provider error.")


@router.post("/customers/{org_id}/refund", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def issue_refund(
    request: Request,
    org_id: int,
    body: RefundRequest,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Issue a partial or full refund."""
    from billing.admin_customers import admin_issue_refund

    try:
        result = admin_issue_refund(
            db,
            org_id,
            body.payment_intent_id,
            body.amount_cents,
            body.reason,
            admin_user_id=admin.id,
            ip_address=get_client_ip(request),
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to issue refund for org %d", org_id)
        raise HTTPException(status_code=502, detail="Payment provider error.")


@router.post("/customers/{org_id}/cancel", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def force_cancel(
    request: Request,
    org_id: int,
    body: ForceCancelRequest,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Force cancel a customer's subscription."""
    from billing.admin_customers import admin_force_cancel

    try:
        result = admin_force_cancel(
            db,
            org_id,
            body.reason,
            body.immediate,
            admin_user_id=admin.id,
            ip_address=get_client_ip(request),
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/customers/{org_id}/revoke-sessions", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def revoke_sessions(
    request: Request,
    org_id: int,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Revoke all active sessions for a customer."""
    from billing.admin_customers import admin_revoke_sessions

    result = admin_revoke_sessions(
        db,
        org_id,
        admin_user_id=admin.id,
        ip_address=get_client_ip(request),
    )
    db.commit()
    return result


@router.post("/dunning/{episode_id}/resolve", response_model=AdminActionResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def resolve_dunning(
    request: Request,
    episode_id: int,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
    reason: str = Query(default="Manual resolution", max_length=500),
) -> dict[str, Any]:
    """Manually resolve a dunning episode."""
    from billing.admin_customers import admin_resolve_dunning

    try:
        result = admin_resolve_dunning(
            db,
            episode_id,
            reason,
            admin_user_id=admin.id,
            ip_address=get_client_ip(request),
        )
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Impersonation
# ---------------------------------------------------------------------------


@router.post("/customers/{org_id}/impersonate", response_model=ImpersonationResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def impersonate_customer(
    request: Request,
    org_id: int,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Generate a time-boxed read-only impersonation token (15-minute TTL)."""
    from admin_audit_model import AdminActionType
    from auth import create_impersonation_token
    from billing.admin_customers import _create_audit_entry
    from organization_model import Organization

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org:
        target_user = db.query(User).filter(User.id == org.owner_user_id).first()
    else:
        target_user = db.query(User).filter(User.id == org_id).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Customer not found.")

    token, expires = create_impersonation_token(
        target_user_id=target_user.id,
        target_email=target_user.email,
        admin_user_id=admin.id,
        tier=target_user.tier.value if target_user.tier else "free",
    )

    _create_audit_entry(
        db,
        admin.id,
        AdminActionType.IMPERSONATION_START,
        target_org_id=org.id if org else None,
        target_user_id=target_user.id,
        details={"expires_at": expires.isoformat()},
        ip_address=get_client_ip(request),
    )
    db.commit()

    return {
        "access_token": token,
        "expires_at": expires.isoformat(),
        "target_user_id": target_user.id,
        "target_email": target_user.email,
        "is_impersonation": True,
    }


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------


@router.get("/audit-log", response_model=AuditLogResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
def get_audit_log(
    request: Request,
    admin: Annotated[User, Depends(require_superadmin)],
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    action_type: str | None = Query(default=None),
    admin_id: int | None = Query(default=None),
    target_org_id: int | None = Query(default=None),
    since: str | None = Query(default=None),
    until: str | None = Query(default=None),
) -> dict[str, Any]:
    """Paginated admin audit log with filters."""
    from billing.admin_customers import get_admin_audit_log

    parsed_since = None
    parsed_until = None
    if since:
        try:
            parsed_since = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid since format. Use YYYY-MM-DD.")
    if until:
        try:
            parsed_until = datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid until format. Use YYYY-MM-DD.")

    return get_admin_audit_log(
        db,
        offset=offset,
        limit=limit,
        action_type=action_type,
        admin_user_id=admin_id,
        target_org_id=target_org_id,
        since=parsed_since,
        until=parsed_until,
    )
