"""
Paciolus Flux Engine
Sprint 25: Automated Flux & Variance Intelligence

Compares two trial balances (current period vs prior period) to identify
significant changes and assigns risk flags.

Zero-Storage Compliance:
- Operates entirely on in-memory dictionary structures
- No persistence of period data
- Returns ephemeral specific results for UI/Export
"""

from dataclasses import dataclass, field
from typing import Any

NEAR_ZERO = 0.005  # Below any meaningful financial balance; guards division-by-near-zero
from enum import Enum

from security_utils import log_secure_operation


class FluxRisk(str, Enum):
    """Risk classification for flux items."""
    HIGH = "high"       # Significant unexplained variance
    MEDIUM = "medium"   # Moderate variance
    LOW = "low"         # Expected / immaterial variance
    NONE = "none"       # Immaterial

@dataclass
class FluxItem:
    """
    Represents a single account's period-over-period comparison.
    """
    account_name: str
    account_type: str  # e.g., "Asset", "Liability"
    
    current_balance: float
    prior_balance: float
    
    # Calculated deltas
    delta_amount: float
    delta_percent: float
    
    # Flags
    is_new_account: bool = False
    is_removed_account: bool = False
    has_sign_flip: bool = False  # e.g., Debit to Credit
    
    # Risk Assessment
    risk_level: FluxRisk = FluxRisk.NONE
    variance_indicators: list[str] = field(default_factory=list)

    # Sprint 294: Reclassification detection
    has_reclassification: bool = False
    prior_type: str = ""

    @property
    def display_delta_percent(self) -> str:
        """Safe display string for percentage."""
        if self.prior_balance == 0:
            return "N/m"  # Not meaningful
        return f"{self.delta_percent:.1f}%"

@dataclass
class FluxResult:
    """
    Aggregate result of a flux analysis.
    """
    items: list[FluxItem]
    
    # Summary stats
    total_items: int
    high_risk_count: int
    medium_risk_count: int
    new_accounts_count: int
    removed_accounts_count: int
    
    # Metadata
    materiality_threshold: float

    # Sprint 294: Reclassification detection
    reclassification_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "items": [
                {
                    "account": item.account_name,
                    "type": item.account_type,
                    "current": item.current_balance,
                    "prior": item.prior_balance,
                    "delta_amount": item.delta_amount,
                    "delta_percent": item.delta_percent if abs(item.prior_balance) > NEAR_ZERO else None,
                    "display_percent": item.display_delta_percent,
                    "is_new": item.is_new_account,
                    "is_removed": item.is_removed_account,
                    "sign_flip": item.has_sign_flip,
                    "risk_level": item.risk_level.value,
                    "variance_indicators": item.variance_indicators,
                    "has_reclassification": item.has_reclassification,
                    "prior_type": item.prior_type,
                }
                for item in self.items
            ],
            "summary": {
                "total_items": self.total_items,
                "high_risk_count": self.high_risk_count,
                "medium_risk_count": self.medium_risk_count,
                "new_accounts": self.new_accounts_count,
                "removed_accounts": self.removed_accounts_count,
                "reclassification_count": self.reclassification_count,
                "threshold": self.materiality_threshold
            }
        }

class FluxEngine:
    """
    Engine for processing period-over-period comparisons.
    """
    
    def __init__(self, materiality_threshold: float = 0.0):
        self.materiality_threshold = materiality_threshold

    def compare(
        self, 
        current_balances: dict[str, dict[str, Any]], 
        prior_balances: dict[str, dict[str, Any]]
    ) -> FluxResult:
        """
        Compare current and prior period balances.
        
        Args:
            current_balances: Dict of account_name -> {"net": float, "type": str, ...}
            prior_balances: Dict of account_name -> {"net": float, "type": str, ...}
            
        Returns:
            FluxResult containing detailed comparison
        """
        log_secure_operation("flux_compare", f"Comparing {len(current_balances)} current vs {len(prior_balances)} prior items")
        
        flux_items: list[FluxItem] = []
        
        # Get superset of all accounts
        all_accounts = set(current_balances.keys()) | set(prior_balances.keys())
        
        high_risk = 0
        medium_risk = 0
        new_accts = 0
        removed_accts = 0
        reclass_count = 0

        for account in all_accounts:
            # Extract current data
            curr_data = current_balances.get(account)
            curr_bal = curr_data.get("net", 0.0) if curr_data else 0.0
            # Fallback to dictionary lookups if "net" isn't pre-calculated
            if curr_data and "net" not in curr_data:
                curr_bal = curr_data.get("debit", 0.0) - curr_data.get("credit", 0.0)

            curr_type = curr_data.get("type", "Unknown") if curr_data else "Unknown"

            # Extract prior data
            prior_data = prior_balances.get(account)
            prior_bal = prior_data.get("net", 0.0) if prior_data else 0.0
            if prior_data and "net" not in prior_data:
                prior_bal = prior_data.get("debit", 0.0) - prior_data.get("credit", 0.0)

            # Sprint 294: Capture prior type for reclassification detection
            prior_type_str = prior_data.get("type", "Unknown") if prior_data else "Unknown"

            # If account removed, use prior type for display
            if not curr_data and prior_data:
                curr_type = prior_type_str

            # Calculations
            delta_amt = curr_bal - prior_bal
            delta_pct = 0.0
            if abs(prior_bal) > NEAR_ZERO:
                delta_pct = (delta_amt / abs(prior_bal)) * 100.0

            # Flags
            is_new = (prior_data is None)
            is_removed = (curr_data is None)

            # Sign flip check (e.g. 100 to -50)
            # Only relevant if both balances are non-zero
            sign_flip = False
            if abs(curr_bal) > NEAR_ZERO and abs(prior_bal) > NEAR_ZERO:
                if (curr_bal > 0 and prior_bal < 0) or (curr_bal < 0 and prior_bal > 0):
                    sign_flip = True

            # Sprint 294: Reclassification detection
            has_reclass = False
            if (curr_data is not None and prior_data is not None
                    and curr_type != "Unknown" and prior_type_str != "Unknown"
                    and curr_type.lower() != prior_type_str.lower()):
                has_reclass = True
                reclass_count += 1

            # Risk Assessment
            risk = FluxRisk.LOW
            indicators: list[str] = []

            abs_delta = abs(delta_amt)

            # Threshold Check
            if abs_delta >= self.materiality_threshold:
                # Material change
                if is_new or is_removed:
                    risk = FluxRisk.HIGH
                    indicators.append("New/Removed Account")
                elif sign_flip:
                    risk = FluxRisk.HIGH
                    indicators.append("Sign Flip")
                elif abs(delta_pct) > 20.0: # Arbitrary heuristic: >20% change is significant
                    risk = FluxRisk.HIGH
                    indicators.append("Large % Variance")
                else:
                    risk = FluxRisk.MEDIUM
                    indicators.append("Material Variance")
            else:
                risk = FluxRisk.LOW

            # Sprint 294: Add reclassification indicator and escalate
            if has_reclass:
                indicators.append(
                    f"Account Type Reclassification: {prior_type_str} → {curr_type}"
                )
                # Escalate to at least MEDIUM
                if risk == FluxRisk.LOW or risk == FluxRisk.NONE:
                    risk = FluxRisk.MEDIUM

            # Override for zero-balance insignificant matches
            if curr_bal == 0 and prior_bal == 0 and not has_reclass:
                risk = FluxRisk.NONE

            # Add to stats
            if risk == FluxRisk.HIGH:
                high_risk += 1
            elif risk == FluxRisk.MEDIUM:
                medium_risk += 1

            if is_new: new_accts += 1
            if is_removed: removed_accts += 1

            item = FluxItem(
                account_name=account,
                account_type=curr_type,
                current_balance=curr_bal,
                prior_balance=prior_bal,
                delta_amount=delta_amt,
                delta_percent=delta_pct,
                is_new_account=is_new,
                is_removed_account=is_removed,
                has_sign_flip=sign_flip,
                risk_level=risk,
                variance_indicators=indicators,
                has_reclassification=has_reclass,
                prior_type=prior_type_str if has_reclass else "",
            )
            flux_items.append(item)

        # Sort by delta amount (descending absolute)
        flux_items.sort(key=lambda x: abs(x.delta_amount), reverse=True)

        return FluxResult(
            items=flux_items,
            total_items=len(flux_items),
            high_risk_count=high_risk,
            medium_risk_count=medium_risk,
            new_accounts_count=new_accts,
            removed_accounts_count=removed_accts,
            materiality_threshold=self.materiality_threshold,
            reclassification_count=reclass_count,
        )
