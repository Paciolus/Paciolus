"""
Paciolus Recon Engine
Sprint 25: Account Reconciliation Readiness Scoring

Estimates the "Reconciliation Risk" of accounts to help CFOs prioritize work.
Scores accounts (0-100) based on:
- Magnitude (Materiality)
- Roundedness (Round numbers often indicate estimates/suspense)
- Volatility (from Flux results)
- Natural Balance (Sign checks)

Zero-Storage Compliance:
- Stateless execution
- Consumes FluxResult, produces ReconResult
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import math

from security_utils import log_secure_operation
from flux_engine import FluxResult, FluxItem

class RiskBand(str, Enum):
    """Recon risk categorization."""
    HIGH = "high"       # Needs immediate attention / detailed rec
    MEDIUM = "medium"   # Needs review
    LOW = "low"         # Likely standard/automated

@dataclass
class ReconScore:
    """
    Score details for a single account.
    """
    account_name: str
    risk_score: int  # 0 to 100
    risk_band: RiskBand
    
    # Factor breakdown (for UI tooltips)
    factors: List[str] = field(default_factory=list)
    suggested_action: str = "Standard Reconciliation"

@dataclass
class ReconResult:
    """
    Aggregate reconciliation analysis.
    """
    scores: List[ReconScore]
    
    # Stats
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": [
                {
                    "account": s.account_name,
                    "score": s.risk_score,
                    "band": s.risk_band.value,
                    "factors": s.factors,
                    "action": s.suggested_action
                }
                for s in self.scores
            ],
            "stats": {
                "high": self.high_risk_count,
                "medium": self.medium_risk_count,
                "low": self.low_risk_count
            }
        }

class ReconEngine:
    """
    Engine for calculating reconciliation readiness scores.
    """
    
    def __init__(self, materiality_threshold: float = 0.0):
        self.materiality_threshold = materiality_threshold

    def calculate_scores(self, flux_result: FluxResult) -> ReconResult:
        """
        Calculate risk scores for all accounts in a Flux result.
        
        Args:
            flux_result: Output from FluxEngine
            
        Returns:
            ReconResult with scored accounts
        """
        log_secure_operation("recon_score", f"Scoring {len(flux_result.items)} accounts")
        
        scores: List[ReconScore] = []
        high_risk = 0
        med_risk = 0
        low_risk = 0
        
        for item in flux_result.items:
            # Skip zero-balance items that didn't move
            if item.current_balance == 0 and item.prior_balance == 0:
                continue
                
            score = 0
            factors = []
            
            # --- FACTOR 1: Magnitude vs Materiality (Max 40 pts) ---
            balance_abs = abs(item.current_balance)
            if self.materiality_threshold > 0:
                ratio = balance_abs / self.materiality_threshold
                if ratio >= 10.0:
                    score += 40
                    factors.append("Very High Magnitude (>10x Materiality)")
                elif ratio >= 5.0:
                    score += 30
                    factors.append("High Magnitude (>5x Materiality)")
                elif ratio >= 1.0:
                    score += 20
                    factors.append("Material Balance")
                else:
                    score += 5 # Base score for existence
            
            # --- FACTOR 2: Roundedness (Max 30 pts) ---
            # Checks if balance is perfectly round (e.g. 1000.00, 50000.00)
            # Suspicion: often manual JE or estimate
            if balance_abs > 1000 and balance_abs % 1000 == 0:
                score += 30
                factors.append("Perfectly Round Number (1000s)")
            elif balance_abs > 100 and balance_abs % 100 == 0:
                score += 15
                factors.append("Round Number (100s)")
                
            # --- FACTOR 3: Volatility/Flux (Max 20 pts) ---
            if item.is_new_account or item.is_removed_account:
                score += 20
                factors.append("New/Removed Account")
            elif item.has_sign_flip:
                score += 20
                factors.append("Balance Sign Flip")
            elif item.delta_percent and abs(item.delta_percent) > 50.0:
                score += 15
                factors.append("High Volatility (>50%)")
                
            # --- FACTOR 4: Account Type Specifics (Max 10 pts) ---
            # e.g., "Suspense", "Clearing", "Intercompany" are risky
            name_lower = item.account_name.lower()
            if "suspense" in name_lower or "clearing" in name_lower or "ask" in name_lower:
                score += 10
                factors.append("High Risk Keyword (Suspense/Clearing)")
            elif "reconciliation" in name_lower or "diff" in name_lower:
                score += 10
                factors.append("Reconciliation Discrepancy Account")
            
            # Cap score at 100
            score = min(score, 100)
            
            # Determine Band
            if score >= 70:
                band = RiskBand.HIGH
                high_risk += 1
            elif score >= 30:
                band = RiskBand.MEDIUM
                med_risk += 1
            else:
                band = RiskBand.LOW
                low_risk += 1
            
            # Suggested Action
            action = "Standard Rec"
            if band == RiskBand.HIGH:
                action = "Detailed Tie-Out & Evidence"
            elif "suspense" in name_lower:
                action = "Investigate & Reclass"
            elif item.is_new_account:
                action = "Verify Opening Balance"
                
            scores.append(ReconScore(
                account_name=item.account_name,
                risk_score=score,
                risk_band=band,
                factors=factors,
                suggested_action=action
            ))
            
        scores.sort(key=lambda x: x.risk_score, reverse=True)
        
        return ReconResult(
            scores=scores,
            high_risk_count=high_risk,
            medium_risk_count=med_risk,
            low_risk_count=low_risk
        )
