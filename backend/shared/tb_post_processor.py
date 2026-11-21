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
    """Apply multi-currency conversion to TB result if user has a rate table.

    Mutates `result` in place, adding result["currency_conversion"].
    """
    if "accounts" not in result:
        logger.warning("Skipping currency conversion: missing 'accounts' key")
        return

    from currency_engine import convert_trial_balance
    from shared.currency_rate_store import get_user_rate_table

    rate_table = get_user_rate_table(db, user_id)
    if rate_table is None or not result.get("accounts"):
        return

    try:
        conversion = convert_trial_balance(
            tb_rows=result["accounts"],
            rate_table=rate_table,
            amount_column="net_balance"
            if "net_balance" in (result["accounts"][0] if result["accounts"] else {})
            else "amount",
        )
        result["currency_conversion"] = conversion.to_dict()
    except (ValueError, KeyError, TypeError, AttributeError, ArithmeticError):
        logger.warning("Currency conversion failed — returning unconverted results", exc_info=True)
