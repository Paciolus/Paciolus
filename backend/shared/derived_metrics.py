"""
Derived metrics — standalone computations that operate on in-session data.
These functions are pure (no DB access) and safe for Zero-Storage use.
"""

from __future__ import annotations

import math
import statistics
from datetime import date, datetime


def compute_payroll_revenue_metrics(
    total_payroll: float,
    total_revenue: float,
    unique_employee_count: int,
) -> dict:
    """
    Compute payroll-to-revenue and revenue-per-employee ratios.

    Args:
        total_payroll: Aggregate payroll expense amount.
        total_revenue: Aggregate revenue amount.
        unique_employee_count: Distinct employee count in the payroll data.

    Returns:
        dict with payroll_burden_ratio, revenue_per_employee,
        cost_per_employee, and interpretive fields.
    """
    payroll_burden_ratio: float | None = None
    revenue_per_employee: float | None = None
    cost_per_employee: float | None = None

    if total_revenue and total_revenue != 0:
        payroll_burden_ratio = round(total_payroll / total_revenue, 4)

    if unique_employee_count and unique_employee_count > 0:
        revenue_per_employee = round(total_revenue / unique_employee_count, 2)
        cost_per_employee = round(total_payroll / unique_employee_count, 2)

    return {
        "total_payroll": total_payroll,
        "total_revenue": total_revenue,
        "unique_employee_count": unique_employee_count,
        "payroll_burden_ratio": payroll_burden_ratio,
        "revenue_per_employee": revenue_per_employee,
        "cost_per_employee": cost_per_employee,
    }


def compute_clearance_velocity(
    matched_items: list[dict],
) -> dict:
    """
    Compute reconciliation clearance velocity from matched bank items.

    Each matched_item must have:
        - transaction_date (str ISO date or date object)
        - clearance_date (str ISO date or date object)

    Returns:
        dict with total_items, avg_days_to_clear, median_days_to_clear,
        max_days_to_clear, items_over_30_days, items_over_30_days_pct.
    """
    if not matched_items:
        return {
            "total_items": 0,
            "avg_days_to_clear": None,
            "median_days_to_clear": None,
            "max_days_to_clear": None,
            "items_over_30_days": 0,
            "items_over_30_days_pct": 0.0,
        }

    days_list: list[int] = []

    for item in matched_items:
        txn_date = _parse_date(item.get("transaction_date"))
        clr_date = _parse_date(item.get("clearance_date"))

        if txn_date is None or clr_date is None:
            continue

        delta = (clr_date - txn_date).days
        # Only include non-negative deltas (clearance on or after transaction)
        days_list.append(max(delta, 0))

    if not days_list:
        return {
            "total_items": len(matched_items),
            "avg_days_to_clear": None,
            "median_days_to_clear": None,
            "max_days_to_clear": None,
            "items_over_30_days": 0,
            "items_over_30_days_pct": 0.0,
        }

    over_30 = sum(1 for d in days_list if d > 30)

    return {
        "total_items": len(days_list),
        "avg_days_to_clear": round(math.fsum(days_list) / len(days_list), 2),
        "median_days_to_clear": round(statistics.median(days_list), 2),
        "max_days_to_clear": max(days_list),
        "items_over_30_days": over_30,
        "items_over_30_days_pct": round((over_30 / len(days_list)) * 100, 2),
    }


def compute_anomaly_density(total_flagged: int, total_rows: int) -> dict:
    """
    Compute anomaly density rate from flagged count and total row count.

    Args:
        total_flagged: Number of flagged/anomalous rows.
        total_rows: Total number of rows in the dataset.

    Returns:
        dict with density_rate, density_pct, and interpretation.
    """
    if total_rows <= 0:
        return {
            "density_rate": None,
            "density_pct": None,
            "interpretation": "N/A",
            "total_flagged": total_flagged,
            "total_rows": total_rows,
        }

    density_rate = total_flagged / total_rows
    density_pct = round(density_rate * 100, 4)

    if density_pct < 1.0:
        interpretation = "Low"
    elif density_pct < 5.0:
        interpretation = "Moderate"
    elif density_pct < 10.0:
        interpretation = "Elevated"
    else:
        interpretation = "High"

    return {
        "density_rate": round(density_rate, 6),
        "density_pct": density_pct,
        "interpretation": interpretation,
        "total_flagged": total_flagged,
        "total_rows": total_rows,
    }


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _parse_date(value: str | date | datetime | None) -> date | None:
    """Parse a date value from string or date/datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        # Try ISO format (YYYY-MM-DD)
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
        # Try common US format (MM/DD/YYYY)
        try:
            return datetime.strptime(value, "%m/%d/%Y").date()
        except ValueError:
            pass
    return None
