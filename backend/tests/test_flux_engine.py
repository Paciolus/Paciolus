import pytest
from flux_engine import FluxEngine, FluxRisk

def test_flux_comparison():
    engine = FluxEngine(materiality_threshold=100.0)
    
    current = {
        "Cash": {"net": 1200.0, "type": "Asset"},
        "Sales": {"net": -5000.0, "type": "Revenue"},
        "NewAccount": {"net": 100.0, "type": "Asset"}
    }
    
    prior = {
        "Cash": {"net": 1000.0, "type": "Asset"},
        "Sales": {"net": -4000.0, "type": "Revenue"},
        "OldAccount": {"net": 200.0, "type": "Liability"} # Positive liability? usually credit (negative), but let's assume net logic handles it
    }
    
    result = engine.compare(current, prior)
    
    assert result.total_items == 4
    
    # Check Cash (Delta +200) -> Material (>100) -> Medium Risk
    cash_item = next(i for i in result.items if i.account_name == "Cash")
    assert cash_item.delta_amount == 200.0
    assert cash_item.risk_level == FluxRisk.MEDIUM
    
    # Check NewAccount (New) -> Material (100 >= 100) -> High Risk
    new_item = next(i for i in result.items if i.account_name == "NewAccount")
    assert new_item.is_new_account
    assert new_item.risk_level == FluxRisk.MEDIUM or new_item.risk_level == FluxRisk.HIGH
    # Logic check: is_new or is_removed -> High risk if material. 100 >= 100 -> Material. So High.
    assert new_item.risk_level == FluxRisk.HIGH
    
    # Check OldAccount (Removed) -> Material (200) -> High Risk
    old_item = next(i for i in result.items if i.account_name == "OldAccount")
    assert old_item.is_removed_account
    assert old_item.risk_level == FluxRisk.HIGH

def test_sign_flip():
    engine = FluxEngine(materiality_threshold=10.0)
    current = {"Test": {"net": 50.0, "type": "Asset"}}
    prior = {"Test": {"net": -50.0, "type": "Asset"}}
    
    result = engine.compare(current, prior)
    item = result.items[0]
    
    assert item.has_sign_flip
    assert item.risk_level == FluxRisk.HIGH
