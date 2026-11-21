"""
Trial balance post-processor — Sprint 519 Phase 5

Extracts post-analysis transforms from routes/audit.py:
- Lead sheet grouping from abnormal balances
- Section density computation
- Currency conversion application
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def apply_section_density(result: dict[str, Any], materiality_threshold: float) -> None:
    """Add section density to the population profile, from the engine's lead-sheet grouping.

    Sprint 890 (15D): both engines now group lead sheets themselves; this used to group them
    again (from ``all_accounts``, or from ``abnormal_balances`` as a fallback).
    """
    grouping = result.get("lead_sheet_grouping")
    if grouping is None or result.get("population_profile") is None:
        return
    from population_profile_engine import compute_section_density

    density = compute_section_density(grouping, materiality_threshold)
    result["population_profile"]["section_density"] = [s.to_dict() for s in density]


def apply_currency_conversion(
    result: dict[str, Any],
    user_id: int,
    db: Session,
) -> None:
    """Convert the TB to the user's presentation currency, if they have a rate table and the file has currencies.

    Sprint 890 (15D): this never ran — it looked for an ``accounts`` key the pipeline never emits,
    and the response model had no ``currency_conversion`` field. It now converts every account at
    one closing rate per currency, labelled a convenience conversion (``shared/tb_currency_conversion``).
    Mutates ``result`` in place, adding ``result["currency_conversion"]``.
    """
    if not result.get("account_currencies") or not result.get("all_accounts"):
        return

    from shared.currency_rate_store import get_user_rate_table
    from shared.tb_currency_conversion import accounts_with_currencies, convert_accounts

    rate_table = get_user_rate_table(db, user_id)
    if rate_table is None:
        return
    try:
        result["currency_conversion"] = convert_accounts(accounts_with_currencies(result), rate_table).to_dict()
    except (ValueError, KeyError, TypeError, ArithmeticError):
        logger.warning("Currency conversion failed — returning unconverted results", exc_info=True)
