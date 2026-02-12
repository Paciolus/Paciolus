"""
Paciolus API — Client Management Routes
"""
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User, Client, Industry
from auth import require_current_user
from client_manager import ClientManager, get_industry_options
from lead_sheet_mapping import get_lead_sheet_options
from shared.helpers import require_client

router = APIRouter(tags=["clients"])


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = "other"
    fiscal_year_end: Optional[str] = "12-31"
    settings: Optional[str] = "{}"


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    settings: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    user_id: int
    name: str
    industry: str
    fiscal_year_end: str
    created_at: str
    updated_at: str
    settings: str


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total_count: int
    page: int
    page_size: int


class IndustryOption(BaseModel):
    value: str
    label: str


@router.get("/clients/industries", response_model=List[IndustryOption])
def get_industries(response: Response):
    """Get available industry options. Static data, cached aggressively."""
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400"
    return get_industry_options()


@router.get("/audit/lead-sheets/options", response_model=list, tags=["reference"])
def get_lead_sheet_options_endpoint(response: Response):
    """Get available lead sheet options for UI dropdowns."""
    response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=86400"
    return get_lead_sheet_options()


@router.get("/clients", response_model=ClientListResponse)
def get_clients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of clients for the user."""
    log_secure_operation("clients_list", f"User {current_user.id} fetching client list (page {page})")

    manager = ClientManager(db)

    if search:
        clients = manager.search_clients(current_user.id, search, limit=page_size)
        total_count = len(clients)
    else:
        offset = (page - 1) * page_size
        clients, total_count = manager.get_clients_with_count(
            current_user.id, limit=page_size, offset=offset
        )

    return ClientListResponse(
        clients=[
            ClientResponse(
                id=c.id,
                user_id=c.user_id,
                name=c.name,
                industry=c.industry.value if c.industry else "other",
                fiscal_year_end=c.fiscal_year_end,
                created_at=c.created_at.isoformat() if c.created_at else "",
                updated_at=c.updated_at.isoformat() if c.updated_at else "",
                settings=c.settings or "{}"
            )
            for c in clients
        ],
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.post("/clients", response_model=ClientResponse, status_code=201)
def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Create a new client for the authenticated user."""
    log_secure_operation(
        "client_create",
        f"User {current_user.id} creating client: {client_data.name[:20]}..."
    )

    manager = ClientManager(db)

    try:
        industry = Industry(client_data.industry) if client_data.industry else Industry.OTHER

        client = manager.create_client(
            user_id=current_user.id,
            name=client_data.name,
            industry=industry,
            fiscal_year_end=client_data.fiscal_year_end or "12-31",
            settings=client_data.settings or "{}"
        )

        return ClientResponse(
            id=client.id,
            user_id=client.user_id,
            name=client.name,
            industry=client.industry.value if client.industry else "other",
            fiscal_year_end=client.fiscal_year_end,
            created_at=client.created_at.isoformat() if client.created_at else "",
            updated_at=client.updated_at.isoformat() if client.updated_at else "",
            settings=client.settings or "{}"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client(
    client: Client = Depends(require_client)
):
    """Get a specific client by ID."""
    return ClientResponse(
        id=client.id,
        user_id=client.user_id,
        name=client.name,
        industry=client.industry.value if client.industry else "other",
        fiscal_year_end=client.fiscal_year_end,
        created_at=client.created_at.isoformat() if client.created_at else "",
        updated_at=client.updated_at.isoformat() if client.updated_at else "",
        settings=client.settings or "{}"
    )


@router.put("/clients/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Update a client's information."""
    log_secure_operation(
        "client_update",
        f"User {current_user.id} updating client {client_id}"
    )

    manager = ClientManager(db)

    try:
        industry = None
        if client_data.industry is not None:
            industry = Industry(client_data.industry)

        client = manager.update_client(
            user_id=current_user.id,
            client_id=client_id,
            name=client_data.name,
            industry=industry,
            fiscal_year_end=client_data.fiscal_year_end,
            settings=client_data.settings
        )

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        return ClientResponse(
            id=client.id,
            user_id=client.user_id,
            name=client.name,
            industry=client.industry.value if client.industry else "other",
            fiscal_year_end=client.fiscal_year_end,
            created_at=client.created_at.isoformat() if client.created_at else "",
            updated_at=client.updated_at.isoformat() if client.updated_at else "",
            settings=client.settings or "{}"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/clients/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Delete a client."""
    log_secure_operation(
        "client_delete",
        f"User {current_user.id} deleting client {client_id}"
    )

    manager = ClientManager(db)
    deleted = manager.delete_client(current_user.id, client_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Client not found")
