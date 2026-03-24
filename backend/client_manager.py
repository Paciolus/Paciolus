"""
Client management with multi-tenant isolation.
Stores only client metadata, never financial data.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Client, EntityType, Industry, ReportingFramework, User
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
        reporting_framework: ReportingFramework = ReportingFramework.AUTO,
        entity_type: EntityType = EntityType.OTHER,
        jurisdiction_country: str = "US",
        jurisdiction_state: Optional[str] = None,
        settings: str = "{}",
    ) -> Client:
        """Create a new client. Raises ValueError if user doesn't exist or name is empty."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist")

        if not name or not name.strip():
            raise ValueError("Client name cannot be empty")

        if not self._validate_fiscal_year_end(fiscal_year_end):
            raise ValueError("fiscal_year_end must be in MM-DD format (e.g., '12-31')")

        if jurisdiction_country and len(jurisdiction_country) != 2:
            raise ValueError("jurisdiction_country must be a 2-letter ISO 3166-1 alpha-2 code")

        client = Client(
            user_id=user_id,
            name=name.strip(),
            industry=industry,
            fiscal_year_end=fiscal_year_end,
            reporting_framework=reporting_framework,
            entity_type=entity_type,
            jurisdiction_country=jurisdiction_country,
            jurisdiction_state=jurisdiction_state,
            settings=settings,
        )

        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)

        log_secure_operation("client_created", f"Client '{name[:20]}...' created for user {user_id}")

        return client

    def get_client(self, user_id: int, client_id: int) -> Optional[Client]:
        """
        Get a specific client by ID, with org-aware access check.

        Returns Client if the user is the direct owner or an org co-member
        of the client owner.
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None

        # Direct owner — fast path
        if client.user_id == user_id:
            return client

        # Org-based access: user and client owner in same org
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.organization_id:
            from organization_model import OrganizationMember

            owner_in_org = (
                self.db.query(OrganizationMember)
                .filter(
                    OrganizationMember.user_id == client.user_id,
                    OrganizationMember.organization_id == user.organization_id,
                )
                .first()
            )
            if owner_in_org:
                return client

        return None

    def _accessible_user_ids(self, user_id: int) -> list[int]:
        """Get all user IDs whose clients should be visible to this user.

        Returns [user_id] for solo users, or all org member user_ids for org members.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.organization_id:
            return [user_id]

        from organization_model import OrganizationMember

        member_ids = (
            self.db.query(OrganizationMember.user_id)
            .filter(OrganizationMember.organization_id == user.organization_id)
            .all()
        )
        return [m[0] for m in member_ids] if member_ids else [user_id]

    def get_clients_for_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[Client]:
        """Get all clients accessible to a user (own + org co-members') with pagination."""
        accessible_ids = self._accessible_user_ids(user_id)
        return (
            self.db.query(Client)
            .filter(Client.user_id.in_(accessible_ids))
            .order_by(Client.name.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_client_count(self, user_id: int) -> int:
        accessible_ids = self._accessible_user_ids(user_id)
        return self.db.query(Client).filter(Client.user_id.in_(accessible_ids)).count()

    def get_clients_with_count(self, user_id: int, limit: int = 100, offset: int = 0) -> tuple[list[Client], int]:
        """Get paginated clients with total count using two queries (no cartesian join)."""
        accessible_ids = self._accessible_user_ids(user_id)

        # Separate count query — avoids window function + subquery cartesian product
        total_count = (self.db.query(func.count(Client.id)).filter(Client.user_id.in_(accessible_ids)).scalar()) or 0

        clients = (
            self.db.query(Client)
            .filter(Client.user_id.in_(accessible_ids))
            .order_by(Client.name.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return clients, total_count

    def get_clients_with_engagement_summary(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> tuple[list[dict], int]:
        """Get paginated clients with engagement summary data (Sprint 580).

        Returns (list of dicts with client + engagement_summary, total_count).
        Uses a LEFT JOIN to compute per-client engagement stats in a single pass.
        """
        from sqlalchemy import case, literal_column
        from sqlalchemy.orm import aliased

        from engagement_model import Engagement, EngagementStatus, ToolRun

        accessible_ids = self._accessible_user_ids(user_id)

        total_count = (self.db.query(func.count(Client.id)).filter(Client.user_id.in_(accessible_ids)).scalar()) or 0

        # Subquery: engagement summary per client
        eng_summary = (
            self.db.query(
                Engagement.client_id,
                func.sum(case((Engagement.status == EngagementStatus.ACTIVE, 1), else_=0)).label("active_count"),
                func.sum(case((Engagement.status == EngagementStatus.ARCHIVED, 1), else_=0)).label("archived_count"),
                func.max(Engagement.period_end).label("latest_period_end"),
            )
            .group_by(Engagement.client_id)
            .subquery()
        )

        # Subquery: tool run count per client (via engagement)
        run_count_sq = (
            self.db.query(
                Engagement.client_id,
                func.count(ToolRun.id).label("tool_run_count"),
            )
            .join(ToolRun, ToolRun.engagement_id == Engagement.id)
            .group_by(Engagement.client_id)
            .subquery()
        )

        rows = (
            self.db.query(
                Client,
                eng_summary.c.active_count,
                eng_summary.c.archived_count,
                eng_summary.c.latest_period_end,
                run_count_sq.c.tool_run_count,
            )
            .outerjoin(eng_summary, Client.id == eng_summary.c.client_id)
            .outerjoin(run_count_sq, Client.id == run_count_sq.c.client_id)
            .filter(Client.user_id.in_(accessible_ids))
            .order_by(Client.name.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        results = []
        for client, active_count, archived_count, latest_period_end, tool_run_count in rows:
            results.append({
                "client": client,
                "engagement_summary": {
                    "active_count": active_count or 0,
                    "archived_count": archived_count or 0,
                    "latest_period_end": latest_period_end.isoformat() if latest_period_end else None,
                    "tool_run_count": tool_run_count or 0,
                },
            })

        return results, total_count

    def update_client(
        self,
        user_id: int,
        client_id: int,
        name: Optional[str] = None,
        industry: Optional[Industry] = None,
        fiscal_year_end: Optional[str] = None,
        reporting_framework: Optional[ReportingFramework] = None,
        entity_type: Optional[EntityType] = None,
        jurisdiction_country: Optional[str] = None,
        jurisdiction_state: Optional[str] = None,
        settings: Optional[str] = None,
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

        if reporting_framework is not None:
            client.reporting_framework = reporting_framework

        if entity_type is not None:
            client.entity_type = entity_type

        if jurisdiction_country is not None:
            if len(jurisdiction_country) != 2:
                raise ValueError("jurisdiction_country must be a 2-letter ISO 3166-1 alpha-2 code")
            client.jurisdiction_country = jurisdiction_country

        if jurisdiction_state is not None:
            client.jurisdiction_state = jurisdiction_state

        if settings is not None:
            client.settings = settings

        # Update timestamp
        client.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(client)

        log_secure_operation("client_updated", f"Client {client_id} updated for user {user_id}")

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
            "client_deleted", f"Client '{client_name[:20]}...' (ID: {client_id}) deleted for user {user_id}"
        )

        return True

    def search_clients(self, user_id: int, query: str, limit: int = 20) -> list[Client]:
        """Search clients by name (case-insensitive), including org co-members' clients."""
        accessible_ids = self._accessible_user_ids(user_id)
        return (
            self.db.query(Client)
            .filter(Client.user_id.in_(accessible_ids), Client.name.ilike(f"%{query}%"))
            .order_by(Client.name.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def _validate_fiscal_year_end(fiscal_year_end: str) -> bool:
        """Validate MM-DD format."""
        if not fiscal_year_end or len(fiscal_year_end) != 5:
            return False

        if fiscal_year_end[2] != "-":
            return False

        try:
            month = int(fiscal_year_end[:2])
            day = int(fiscal_year_end[3:])

            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False

            # Basic validation for days in month
            days_in_month = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
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
