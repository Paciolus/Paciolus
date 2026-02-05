"""
Client management with multi-tenant isolation.
Stores only client metadata, never financial data.
"""

from datetime import datetime, UTC
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func, over

from models import Client, Industry, User
from security_utils import log_secure_operation


class ClientManager:
    """CRUD operations for clients with user-scoped data isolation."""

    def __init__(self, db: Session):
        self.db = db

    def create_client(
        self,
        user_id: int,
        name: str,
        industry: Industry = Industry.OTHER,
        fiscal_year_end: str = "12-31",
        settings: str = "{}"
    ) -> Client:
        """Create a new client. Raises ValueError if user doesn't exist or name is empty."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist")

        if not name or not name.strip():
            raise ValueError("Client name cannot be empty")

        if not self._validate_fiscal_year_end(fiscal_year_end):
            raise ValueError("fiscal_year_end must be in MM-DD format (e.g., '12-31')")

        client = Client(
            user_id=user_id,
            name=name.strip(),
            industry=industry,
            fiscal_year_end=fiscal_year_end,
            settings=settings,
        )

        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)

        log_secure_operation(
            "client_created",
            f"Client '{name[:20]}...' created for user {user_id}"
        )

        return client

    def get_client(self, user_id: int, client_id: int) -> Optional[Client]:
        """
        Get a specific client by ID, scoped to the user.

        Args:
            user_id: The ID of the user (for multi-tenant isolation)
            client_id: The ID of the client to retrieve

        Returns:
            Client object if found and owned by user, None otherwise
        """
        return self.db.query(Client).filter(
            Client.id == client_id,
            Client.user_id == user_id  # Multi-tenant isolation
        ).first()

    def get_clients_for_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[Client]:
        """Get all clients for a user with pagination."""
        return self.db.query(Client).filter(
            Client.user_id == user_id
        ).order_by(
            Client.name.asc()
        ).offset(offset).limit(limit).all()

    def get_client_count(self, user_id: int) -> int:
        return self.db.query(Client).filter(
            Client.user_id == user_id
        ).count()

    def get_clients_with_count(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Client], int]:
        """Get paginated clients with total count in single query using window function."""
        subquery = self.db.query(
            Client,
            func.count(Client.id).over().label('total_count')
        ).filter(
            Client.user_id == user_id
        ).order_by(
            Client.name.asc()
        ).offset(offset).limit(limit).subquery()

        # Execute and extract results
        results = self.db.query(Client, subquery.c.total_count).select_from(
            subquery
        ).all()

        if not results:
            return [], 0

        clients = [row[0] for row in results]
        total_count = results[0][1] if results else 0
        return clients, total_count

    def update_client(
        self,
        user_id: int,
        client_id: int,
        name: Optional[str] = None,
        industry: Optional[Industry] = None,
        fiscal_year_end: Optional[str] = None,
        settings: Optional[str] = None
    ) -> Optional[Client]:
        """Update client. Returns None if not found, raises ValueError on validation failure."""
        client = self.get_client(user_id, client_id)
        if not client:
            return None

        # Update fields if provided
        if name is not None:
            if not name.strip():
                raise ValueError("Client name cannot be empty")
            client.name = name.strip()

        if industry is not None:
            client.industry = industry

        if fiscal_year_end is not None:
            if not self._validate_fiscal_year_end(fiscal_year_end):
                raise ValueError("fiscal_year_end must be in MM-DD format (e.g., '12-31')")
            client.fiscal_year_end = fiscal_year_end

        if settings is not None:
            client.settings = settings

        # Update timestamp
        client.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(client)

        log_secure_operation(
            "client_updated",
            f"Client {client_id} updated for user {user_id}"
        )

        return client

    def delete_client(self, user_id: int, client_id: int) -> bool:
        """Delete client. Returns True if deleted, False if not found."""
        client = self.get_client(user_id, client_id)
        if not client:
            return False

        client_name = client.name
        self.db.delete(client)
        self.db.commit()

        log_secure_operation(
            "client_deleted",
            f"Client '{client_name[:20]}...' (ID: {client_id}) deleted for user {user_id}"
        )

        return True

    def search_clients(
        self,
        user_id: int,
        query: str,
        limit: int = 20
    ) -> list[Client]:
        """Search clients by name (case-insensitive)."""
        return self.db.query(Client).filter(
            Client.user_id == user_id,
            Client.name.ilike(f"%{query}%")
        ).order_by(
            Client.name.asc()
        ).limit(limit).all()

    @staticmethod
    def _validate_fiscal_year_end(fiscal_year_end: str) -> bool:
        """Validate MM-DD format."""
        if not fiscal_year_end or len(fiscal_year_end) != 5:
            return False

        if fiscal_year_end[2] != '-':
            return False

        try:
            month = int(fiscal_year_end[:2])
            day = int(fiscal_year_end[3:])

            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False

            # Basic validation for days in month
            days_in_month = {
                1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
                7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
            }
            if day > days_in_month[month]:
                return False

            return True
        except ValueError:
            return False


_INDUSTRY_OPTIONS: list[dict] = [
    {"value": Industry.TECHNOLOGY.value, "label": "Technology"},
    {"value": Industry.HEALTHCARE.value, "label": "Healthcare"},
    {"value": Industry.FINANCIAL_SERVICES.value, "label": "Financial Services"},
    {"value": Industry.MANUFACTURING.value, "label": "Manufacturing"},
    {"value": Industry.RETAIL.value, "label": "Retail"},
    {"value": Industry.PROFESSIONAL_SERVICES.value, "label": "Professional Services"},
    {"value": Industry.REAL_ESTATE.value, "label": "Real Estate"},
    {"value": Industry.CONSTRUCTION.value, "label": "Construction"},
    {"value": Industry.HOSPITALITY.value, "label": "Hospitality"},
    {"value": Industry.NONPROFIT.value, "label": "Nonprofit"},
    {"value": Industry.EDUCATION.value, "label": "Education"},
    {"value": Industry.OTHER.value, "label": "Other"},
]


def get_industry_options() -> list[dict]:
    """Get industry options for dropdowns."""
    return _INDUSTRY_OPTIONS
