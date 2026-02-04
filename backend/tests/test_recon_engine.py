import pytest
from flux_engine import FluxItem, FluxResult, FluxRisk
from recon_engine import ReconEngine, RiskBand

def test_recon_scoring_high_risk():
    engine = ReconEngine(materiality_threshold=1000.0)
    
    # Create a high risk item (Round number, high magnitude)
    item = FluxItem(
        account_name="Suspense Account",
        account_type="Liability",
        current_balance=50000.0, # 50x materiality -> +40 pts
        prior_balance=0.0,
        delta_amount=50000.0,
        delta_percent=0.0,
        is_new_account=True, # +20 pts
        is_removed_account=False,
        has_sign_flip=False,
        risk_level=FluxRisk.HIGH,
        risk_reasons=[]
    )
    # Total score expectation:
    # Magnitude: >10x -> 40 pts
    # Roundedness: 50000 % 1000 == 0 -> +30 pts
    # Volatility: New -> +20 pts
    # Keyword: "Suspense" -> +10 pts
    # Total: 100 pts
    
    flux_result = FluxResult(
        items=[item],
        total_items=1,
        high_risk_count=1,
        medium_risk_count=0,
        new_accounts_count=1,
        removed_accounts_count=0,
        materiality_threshold=1000.0
    )
    
    result = engine.calculate_scores(flux_result)
    score = result.scores[0]
    
    assert score.risk_score == 100
    assert score.risk_band == RiskBand.HIGH
    assert "Very High Magnitude (>10x Materiality)" in score.factors
    assert "Perfectly Round Number (1000s)" in score.factors

def test_recon_scoring_low_risk():
    engine = ReconEngine(materiality_threshold=1000.0)
    
    item = FluxItem(
        account_name="Petty Cash",
        account_type="Asset",
        current_balance=123.45, # < Materiality -> +5 pts (base)
        prior_balance=100.00,
        delta_amount=23.45,
        delta_percent=23.45,
        is_new_account=False,
        is_removed_account=False,
        has_sign_flip=False
    )
    
    flux_result = FluxResult([item], 1, 0, 0, 0, 0, 1000.0)
    result = engine.calculate_scores(flux_result)
    score = result.scores[0]
    
    # Base score 5. No other triggers.
    assert score.risk_score == 5
    assert score.risk_band == RiskBand.LOW
