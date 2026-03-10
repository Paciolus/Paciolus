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


def apply_lead_sheet_grouping(result: dict[str, Any], materiality_threshold: float) -> None:
    """Add lead sheet grouping and section density to a TB analysis result.

    Mutates `result` in place:
    - result["lead_sheet_grouping"] = grouped accounts by lead sheet letter
    - result["population_profile"]["section_density"] = density per section
    """
    if "abnormal_balances" not in result:
        logger.warning("Skipping lead sheet grouping: missing 'abnormal_balances' key")
        return

    from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict

    accounts_for_grouping = []
    for ab in result.get("abnormal_balances", []):
        accounts_for_grouping.append(
            {
                "account": ab.get("account", ""),
                "debit": ab.get("amount", 0) if ab.get("amount", 0) > 0 else 0,
                "credit": abs(ab.get("amount", 0)) if ab.get("amount", 0) < 0 else 0,
                "type": ab.get("type", "unknown"),
                "issue": ab.get("issue", ""),
                "materiality": ab.get("materiality", ""),
                "severity": ab.get("severity", "low"),
                "anomaly_type": ab.get("anomaly_type", "unknown"),
            }
        )

    lead_sheet_grouping = group_by_lead_sheet(accounts_for_grouping)
    grouping_dict = lead_sheet_grouping_to_dict(lead_sheet_grouping)
    result["lead_sheet_grouping"] = grouping_dict

    # Section density profile (Sprint 296)
    if result.get("population_profile") is not None:
        from population_profile_engine import compute_section_density

        density = compute_section_density(grouping_dict, materiality_threshold)
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
    from routes.currency import get_user_rate_table

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
    except (ValueError, KeyError, TypeError, AttributeError):
        logger.warning("Currency conversion failed — returning unconverted results", exc_info=True)
