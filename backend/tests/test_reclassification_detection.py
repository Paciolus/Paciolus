"""
Sprint 294: Interperiod Reclassification Detection + L2 Rename

Tests:
- F4: Reclassification detection (type changed between periods)
- F4: Reclassification escalates to MEDIUM minimum risk
- F4: No false positive when types match or Unknown
- F4: reclassification_count in FluxResult summary
- L2: variance_indicators field exists and aliases risk_reasons in to_dict
"""

from flux_engine import FluxEngine, FluxItem, FluxRisk

# ═══════════════════════════════════════════════════════════════
# F4: Reclassification Detection
# ═══════════════════════════════════════════════════════════════

class TestReclassificationDetection:
    """Verify interperiod account type reclassification detection."""

    def test_detects_reclassification(self):
        """Account changing from Liability to Asset should flag reclassification."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"Deposit Account": {"net": 5000, "type": "Asset"}}
        prior = {"Deposit Account": {"net": 5000, "type": "Liability"}}

        result = engine.compare(current, prior)
        item = next(i for i in result.items if i.account_name == "Deposit Account")

        assert item.has_reclassification is True
        assert item.prior_type == "Liability"
        assert item.account_type == "Asset"

    def test_reclassification_adds_indicator(self):
        """Reclassification should add an indicator with prior→current types."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"Lease Obligation": {"net": 10000, "type": "Liability"}}
        prior = {"Lease Obligation": {"net": 10000, "type": "Expense"}}

        result = engine.compare(current, prior)
        item = next(i for i in result.items if i.account_name == "Lease Obligation")

        reclass_indicators = [
            ind for ind in item.variance_indicators
            if "Reclassification" in ind
        ]
        assert len(reclass_indicators) == 1
        assert "Expense" in reclass_indicators[0]
        assert "Liability" in reclass_indicators[0]

    def test_reclassification_escalates_to_medium(self):
        """Reclassification should escalate low-risk to at least MEDIUM."""
        engine = FluxEngine(materiality_threshold=100000)  # High threshold
        current = {"Cash": {"net": 100, "type": "Asset"}}
        prior = {"Cash": {"net": 100, "type": "Liability"}}

        result = engine.compare(current, prior)
        item = next(i for i in result.items if i.account_name == "Cash")

        # Balance unchanged, below materiality, but reclassified → MEDIUM
        assert item.has_reclassification is True
        assert item.risk_level in (FluxRisk.MEDIUM, FluxRisk.HIGH)

    def test_no_reclassification_same_type(self):
        """Same type between periods should NOT flag reclassification."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"Cash": {"net": 1200, "type": "Asset"}}
        prior = {"Cash": {"net": 1000, "type": "Asset"}}

        result = engine.compare(current, prior)
        item = next(i for i in result.items if i.account_name == "Cash")

        assert item.has_reclassification is False
        assert item.prior_type == ""

    def test_no_reclassification_unknown_type(self):
        """Unknown type should NOT trigger reclassification."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"Misc": {"net": 500, "type": "Asset"}}
        prior = {"Misc": {"net": 500, "type": "Unknown"}}

        result = engine.compare(current, prior)
        item = next(i for i in result.items if i.account_name == "Misc")

        assert item.has_reclassification is False

    def test_no_reclassification_new_account(self):
        """New account (no prior) should NOT trigger reclassification."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"New Acct": {"net": 500, "type": "Asset"}}
        prior = {}

        result = engine.compare(current, prior)
        item = next(i for i in result.items if i.account_name == "New Acct")

        assert item.has_reclassification is False

    def test_reclassification_count_in_summary(self):
        """FluxResult should include reclassification_count in summary."""
        engine = FluxEngine(materiality_threshold=0)
        current = {
            "Acct A": {"net": 100, "type": "Asset"},
            "Acct B": {"net": 200, "type": "Liability"},
            "Acct C": {"net": 300, "type": "Revenue"},
        }
        prior = {
            "Acct A": {"net": 100, "type": "Liability"},  # reclassified
            "Acct B": {"net": 200, "type": "Liability"},    # same
            "Acct C": {"net": 300, "type": "Expense"},      # reclassified
        }

        result = engine.compare(current, prior)
        assert result.reclassification_count == 2

    def test_reclassification_count_in_to_dict(self):
        """reclassification_count should appear in to_dict summary."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"X": {"net": 100, "type": "Asset"}}
        prior = {"X": {"net": 100, "type": "Liability"}}

        result = engine.compare(current, prior)
        d = result.to_dict()

        assert "reclassification_count" in d["summary"]
        assert d["summary"]["reclassification_count"] == 1

    def test_reclassification_case_insensitive(self):
        """Type comparison should be case-insensitive."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"X": {"net": 100, "type": "asset"}}
        prior = {"X": {"net": 100, "type": "Asset"}}

        result = engine.compare(current, prior)
        item = result.items[0]

        assert item.has_reclassification is False


# ═══════════════════════════════════════════════════════════════
# L2: variance_indicators Rename
# ═══════════════════════════════════════════════════════════════

class TestVarianceIndicatorsRename:
    """Verify L2 rename: risk_reasons → variance_indicators."""

    def test_flux_item_has_variance_indicators(self):
        """FluxItem should have variance_indicators field."""
        item = FluxItem(
            account_name="Test",
            account_type="Asset",
            current_balance=100,
            prior_balance=50,
            delta_amount=50,
            delta_percent=100.0,
            variance_indicators=["Large % Variance"],
        )
        assert item.variance_indicators == ["Large % Variance"]

    def test_to_dict_emits_variance_indicators_only(self):
        """to_dict should emit variance_indicators (risk_reasons alias removed in Sprint 298)."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"Cash": {"net": 1000, "type": "Asset"}}
        prior = {"Cash": {"net": 500, "type": "Asset"}}

        result = engine.compare(current, prior)
        d = result.to_dict()
        item_dict = d["items"][0]

        assert "variance_indicators" in item_dict
        assert "risk_reasons" not in item_dict

    def test_to_dict_has_reclassification_fields(self):
        """to_dict items should include has_reclassification and prior_type."""
        engine = FluxEngine(materiality_threshold=0)
        current = {"X": {"net": 100, "type": "Asset"}}
        prior = {"X": {"net": 100, "type": "Liability"}}

        result = engine.compare(current, prior)
        d = result.to_dict()
        item_dict = d["items"][0]

        assert "has_reclassification" in item_dict
        assert "prior_type" in item_dict
        assert item_dict["has_reclassification"] is True
        assert item_dict["prior_type"] == "Liability"

    def test_engine_compare_populates_indicators(self):
        """FluxEngine.compare() should populate variance_indicators (not risk_reasons)."""
        engine = FluxEngine(materiality_threshold=100)
        current = {"Revenue": {"net": -5000, "type": "Revenue"}}
        prior = {"Revenue": {"net": -2000, "type": "Revenue"}}

        result = engine.compare(current, prior)
        item = result.items[0]

        # Large variance (150%) above threshold
        assert len(item.variance_indicators) > 0
        assert "Large % Variance" in item.variance_indicators
