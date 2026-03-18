"""
Paciolus API — Client Management Routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from auth import require_current_user
from client_manager import ClientManager, get_industry_options
from database import get_db
from lead_sheet_mapping import get_lead_sheet_options
from models import Client, EntityType, Industry, ReportingFramework, User
from schemas.client_schemas import (  # noqa: F401 — backward compat re-exports
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    IndustryOption,
    ResolvedFrameworkResponse,
)
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.framework_resolution import resolve_reporting_framework
from shared.helpers import require_client
from shared.pagination import PaginatedResponse, PaginationParams
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(tags=["clients"])

# Backward compat alias — existing code may reference ClientListResponse
ClientListResponse = PaginatedResponse[ClientResponse]


def _client_to_response(c: Client) -> ClientResponse:
    """Convert a Client ORM object to a ClientResponse schema."""
    return ClientResponse(
        id=c.id,
        user_id=c.user_id,
        name=c.name,
        industry=c.industry.value if c.industry else "other",
        fiscal_year_end=c.fiscal_year_end,
        reporting_framework=c.reporting_framework.value if c.reporting_framework else "auto",
        entity_type=c.entity_type.value if c.entity_type else "other",
        jurisdiction_country=c.jurisdiction_country or "US",
        jurisdiction_state=c.jurisdiction_state,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
        settings=c.settings or "{}",
    )


@router.get("/clients/industries", response_model=list[IndustryOption])
def get_industries(response: Response):
    """Get available industry options. Static data, cached aggressively."""
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400"
    return get_industry_options()


@router.get("/audit/lead-sheets/options", response_model=list, tags=["reference"])
def get_lead_sheet_options_endpoint(response: Response):
    """Get available lead sheet options for UI dropdowns."""
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400"
    return get_lead_sheet_options()


@router.get("/clients", response_model=PaginatedResponse[ClientResponse])
def get_clients(
    search: Optional[str] = Query(default=None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated list of clients for the user."""
    log_secure_operation("clients_list", f"User {current_user.id} fetching client list (page {pagination.page})")

    manager = ClientManager(db)

    if search:
        clients = manager.search_clients(current_user.id, search, limit=pagination.page_size)
        total_count = len(clients)
    else:
        clients, total_count = manager.get_clients_with_count(
            current_user.id, limit=pagination.page_size, offset=pagination.offset
        )

    return PaginatedResponse[ClientResponse](
        items=[_client_to_response(c) for c in clients],
        total_count=total_count,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("/clients", response_model=ClientResponse, status_code=201)
@limiter.limit(RATE_LIMIT_WRITE)
def create_client(
    request: Request,
    client_data: ClientCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Create a new client for the authenticated user."""
    # Sprint 367: Client limit check (AUDIT-06 FIX 2: subscription-status-aware)
    from sqlalchemy import func as sa_func

    from shared.entitlement_checks import get_effective_entitlements

    entitlements = get_effective_entitlements(current_user, db)
    if entitlements.max_clients > 0:
        client_count = (db.query(sa_func.count(Client.id)).filter(Client.user_id == current_user.id).scalar()) or 0
        if client_count >= entitlements.max_clients:
            from config import ENTITLEMENT_ENFORCEMENT

            if ENTITLEMENT_ENFORCEMENT == "hard":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "code": "TIER_LIMIT_EXCEEDED",
                        "message": f"Client limit reached ({client_count}/{entitlements.max_clients}). Upgrade your plan to add more clients.",
                        "resource": "clients",
                        "current_tier": current_user.tier.value,
                        "upgrade_url": "/pricing",
                    },
                )

    log_secure_operation("client_create", f"User {current_user.id} creating client: {client_data.name[:20]}...")

    manager = ClientManager(db)

    try:
        industry = Industry(client_data.industry) if client_data.industry else Industry.OTHER
        reporting_framework = (
            ReportingFramework(client_data.reporting_framework)
            if client_data.reporting_framework
            else ReportingFramework.AUTO
        )
        entity_type = EntityType(client_data.entity_type) if client_data.entity_type else EntityType.OTHER

        client = manager.create_client(
            user_id=current_user.id,
            name=client_data.name,
            industry=industry,
            fiscal_year_end=client_data.fiscal_year_end or "12-31",
            reporting_framework=reporting_framework,
            entity_type=entity_type,
            jurisdiction_country=client_data.jurisdiction_country or "US",
            jurisdiction_state=client_data.jurisdiction_state,
            settings=client_data.settings or "{}",
        )

        return _client_to_response(client)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(
                e,
                log_label="client_validation",
                allow_passthrough=True,
            ),
        )


@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(client: Client = Depends(require_client)):
    """Get a specific client by ID."""
    return _client_to_response(client)


@router.put("/clients/{client_id}", response_model=ClientResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def update_client(
    request: Request,
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Update a client's information."""
    log_secure_operation("client_update", f"User {current_user.id} updating client {client_id}")

    manager = ClientManager(db)

    try:
        industry = None
        if client_data.industry is not None:
            industry = Industry(client_data.industry)

        reporting_framework = None
        if client_data.reporting_framework is not None:
            reporting_framework = ReportingFramework(client_data.reporting_framework)

        entity_type_val = None
        if client_data.entity_type is not None:
            entity_type_val = EntityType(client_data.entity_type)

        client = manager.update_client(
            user_id=current_user.id,
            client_id=client_id,
            name=client_data.name,
            industry=industry,
            fiscal_year_end=client_data.fiscal_year_end,
            reporting_framework=reporting_framework,
            entity_type=entity_type_val,
            jurisdiction_country=client_data.jurisdiction_country,
            jurisdiction_state=client_data.jurisdiction_state,
            settings=client_data.settings,
        )

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return _client_to_response(client)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=sanitize_error(
                e,
                log_label="client_validation",
                allow_passthrough=True,
            ),
        )


@router.delete("/clients/{client_id}", status_code=204)
@limiter.limit(RATE_LIMIT_WRITE)
def delete_client(
    request: Request, client_id: int, current_user: User = Depends(require_current_user), db: Session = Depends(get_db)
):
    """Delete a client."""
    log_secure_operation("client_delete", f"User {current_user.id} deleting client {client_id}")

    manager = ClientManager(db)
    deleted = manager.delete_client(current_user.id, client_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("/clients/{client_id}/resolved-framework", response_model=ResolvedFrameworkResponse)
def get_resolved_framework(
    client: Client = Depends(require_client),
):
    """Resolve the reporting framework for a client based on its metadata."""
    result = resolve_reporting_framework(
        reporting_framework=client.reporting_framework.value if client.reporting_framework else "auto",
        entity_type=client.entity_type.value if client.entity_type else "other",
        jurisdiction_country=client.jurisdiction_country or "US",
        jurisdiction_state=client.jurisdiction_state,
    )
    return ResolvedFrameworkResponse(
        framework=result.framework.value,
        resolution_reason=result.resolution_reason.value,
        warnings=list(result.warnings),
    )
