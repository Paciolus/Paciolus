"""
Concentration metrics — HHI and related measures.
Shared across AP, AR, and Revenue testing engines.
"""

import math


def compute_hhi(shares: list[float]) -> dict:
    """
    Compute Herfindahl-Hirschman Index from market/revenue shares.

    Args:
        shares: List of absolute amounts (will be normalized to percentages internally)

    Returns:
        dict with hhi (0-10000), concentration_level ("competitive"/"moderate"/"concentrated"),
        top_share_pct, effective_n (1/HHI normalized equivalent count)
    """
    # Edge case: empty list
    if not shares:
        return {
            "hhi": 0.0,
            "concentration_level": "competitive",
            "top_share_pct": 0.0,
            "effective_n": None,
            "entity_count": 0,
        }

    # Filter out non-positive values
    positive_shares = [s for s in shares if s > 0]

    # Edge case: all zeros or no positive values
    if not positive_shares:
        return {
            "hhi": 0.0,
            "concentration_level": "competitive",
            "top_share_pct": 0.0,
            "effective_n": None,
            "entity_count": 0,
        }

    # Compute total using compensated summation for precision
    total = math.fsum(positive_shares)

    # Edge case: single entity = perfect monopoly
    if len(positive_shares) == 1:
        return {
            "hhi": 10000.0,
            "concentration_level": "concentrated",
            "top_share_pct": 100.0,
            "effective_n": 1.0,
            "entity_count": 1,
        }

    # Normalize to percentage shares and compute HHI
    pct_shares = [(s / total) * 100.0 for s in positive_shares]
    hhi = math.fsum(p * p for p in pct_shares)

    # Clamp to valid range
    hhi = min(hhi, 10000.0)

    # Top share percentage
    top_share_pct = round(max(pct_shares), 2)

    # Effective N (theoretical equivalent number of equal-sized entities)
    effective_n = round(10000.0 / hhi, 2) if hhi > 0 else None

    # Concentration level thresholds (DOJ/FTC guidelines)
    if hhi < 1500:
        concentration_level = "competitive"
    elif hhi <= 2500:
        concentration_level = "moderate"
    else:
        concentration_level = "concentrated"

    return {
        "hhi": round(hhi, 2),
        "concentration_level": concentration_level,
        "top_share_pct": top_share_pct,
        "effective_n": effective_n,
        "entity_count": len(positive_shares),
    }
