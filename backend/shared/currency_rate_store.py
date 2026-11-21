"""The user's saved exchange-rate table (Sprint 890, CEO brief 15D).

Moved out of ``routes/currency.py`` so the trial balance post-processor no longer imports from a
route module. The table is kept in ``tool_sessions`` for up to two hours after the last save
(``tool_session_model``); the routes re-export these names unchanged.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from currency_engine import CurrencyRateTable
from tool_session_model import delete_tool_session, load_tool_session, save_tool_session

TOOL_NAME = "currency_rates"


def get_user_rate_table(db: Session, user_id: int) -> Optional[CurrencyRateTable]:
    """Load rate table from DB, or return None if missing/expired."""
    data = load_tool_session(db, user_id, TOOL_NAME)
    if data is None:
        return None
    return CurrencyRateTable.from_storage_dict(data)


def set_user_rate_table(db: Session, user_id: int, table: CurrencyRateTable) -> None:
    """Persist rate table to DB via upsert."""
    save_tool_session(db, user_id, TOOL_NAME, table.to_storage_dict())


def clear_user_rate_table(db: Session, user_id: int) -> bool:
    """Clear rate table from DB. Returns True if it existed."""
    return delete_tool_session(db, user_id, TOOL_NAME)
