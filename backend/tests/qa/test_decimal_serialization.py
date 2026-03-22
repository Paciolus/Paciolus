"""
Regression test for Decimal-to-float serialization in lead sheet responses (NEW-004).

Verifies that lead_sheet_grouping_to_dict serializes monetary fields as
float (JSON number), not string, so frontend consumers can do arithmetic.
"""

from decimal import Decimal

from lead_sheet_mapping import (
    LeadSheet,
    LeadSheetGrouping,
    LeadSheetSummary,
    lead_sheet_grouping_to_dict,
)


def _make_grouping() -> LeadSheetGrouping:
    """Create a minimal LeadSheetGrouping with Decimal values."""
    return LeadSheetGrouping(
        summaries=[
            LeadSheetSummary(
                lead_sheet=LeadSheet.A,
                name="Cash & Cash Equivalents",
                category="asset",
                total_debit=Decimal("150000.50"),
                total_credit=Decimal("25000.75"),
                net_balance=Decimal("124999.75"),
                account_count=3,
                accounts=[],
            ),
            LeadSheetSummary(
                lead_sheet=LeadSheet.E,
                name="Revenue",
                category="revenue",
                total_debit=Decimal("0"),
                total_credit=Decimal("500000.00"),
                net_balance=Decimal("-500000.00"),
                account_count=5,
                accounts=[],
            ),
        ],
        total_debits=Decimal("150000.50"),
        total_credits=Decimal("525000.75"),
        unclassified_count=0,
    )


def test_monetary_fields_are_float_not_string():
    """Monetary fields must serialize as float, not Decimal/string."""
    result = lead_sheet_grouping_to_dict(_make_grouping())

    # Top-level totals
    assert isinstance(result["total_debits"], float)
    assert isinstance(result["total_credits"], float)

    # Per-summary fields
    for summary in result["summaries"]:
        assert isinstance(summary["total_debit"], float), f"total_debit is {type(summary['total_debit'])}"
        assert isinstance(summary["total_credit"], float), f"total_credit is {type(summary['total_credit'])}"
        assert isinstance(summary["net_balance"], float), f"net_balance is {type(summary['net_balance'])}"


def test_monetary_values_preserve_precision():
    """Float conversion should preserve at least 2 decimal places."""
    result = lead_sheet_grouping_to_dict(_make_grouping())

    assert result["total_debits"] == 150000.50
    assert result["total_credits"] == 525000.75
    assert result["summaries"][0]["net_balance"] == 124999.75


def test_json_serializable():
    """The dict must be JSON-serializable without custom encoders."""
    import json

    result = lead_sheet_grouping_to_dict(_make_grouping())
    serialized = json.dumps(result)
    assert '"total_debit": 150000.5' in serialized or '"total_debit": 150000.50' in serialized
