"""
Regression test for Decimal-to-float serialization in lead sheet responses (NEW-004).

Sprint 884 (TQ-12): the engine now returns exact Decimals; the API converts them
to exact JSON numbers (shared/exact_json.py), so the frontend still gets numbers.
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


def test_monetary_fields_are_exact_decimals_in_the_engine():
    """Sprint 884 (TQ-12): the engine keeps exact Decimals (float() lost digits above ~90 trillion)."""
    result = lead_sheet_grouping_to_dict(_make_grouping())

    assert isinstance(result["total_debits"], Decimal)
    for summary in result["summaries"]:
        for key in ("total_debit", "total_credit", "net_balance"):
            assert isinstance(summary[key], Decimal), f"{key} is {type(summary[key])}"


def test_monetary_values_preserve_precision():
    result = lead_sheet_grouping_to_dict(_make_grouping())

    assert result["total_debits"] == Decimal("150000.50")
    assert result["total_credits"] == Decimal("525000.75")
    assert result["summaries"][0]["net_balance"] == Decimal("124999.75")


def test_api_form_is_json_numbers_not_strings():
    """NEW-004 still holds at the API boundary: exact_numbers() gives JSON numbers, not strings."""
    import json

    from shared.exact_json import exact_numbers

    serialized = json.dumps(exact_numbers(lead_sheet_grouping_to_dict(_make_grouping())))
    assert '"total_debit": 150000.5' in serialized
    assert '"150000.5' not in serialized
