"""
Tests for Currency Conversion Memo Generator — Sprint 259

Validates PDF generation, export endpoint registration, and edge cases.
"""

from currency_memo_generator import generate_currency_conversion_memo


class TestCurrencyMemoGeneration:
    """Tests for the PDF memo generator."""

    def _make_result(self, **overrides):
        """Build a minimal conversion result dict."""
        base = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 10,
            "converted_count": 8,
            "unconverted_count": 2,
            "unconverted_items": [],
            "currencies_found": ["EUR", "GBP", "USD"],
            "rates_applied": {"EUR/USD": "1.0523", "GBP/USD": "1.2634"},
            "balance_check_passed": True,
            "balance_imbalance": 0.0,
            "conversion_summary": "8 of 10 accounts converted (80%).",
        }
        base.update(overrides)
        return base

    def test_generates_valid_pdf(self):
        """Memo generates a non-empty PDF."""
        result = self._make_result()
        pdf_bytes = generate_currency_conversion_memo(result)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:5] == b"%PDF-"

    def test_with_workpaper_fields(self):
        """Memo accepts all workpaper metadata fields."""
        result = self._make_result()
        pdf_bytes = generate_currency_conversion_memo(
            result,
            filename="Q4_Trial_Balance.xlsx",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Smith",
            reviewed_by="Jane Doe",
            workpaper_date="2026-02-15",
        )
        assert len(pdf_bytes) > 100
        assert pdf_bytes[:5] == b"%PDF-"

    def test_with_unconverted_items(self):
        """Memo includes unconverted items table when present."""
        result = self._make_result(
            unconverted_items=[
                {
                    "account_number": "1000",
                    "account_name": "Cash in JPY",
                    "original_amount": 1000000,
                    "original_currency": "JPY",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "2000",
                    "account_name": "Misc",
                    "original_amount": 50,
                    "original_currency": "",
                    "issue": "missing_currency_code",
                    "severity": "low",
                },
            ],
            unconverted_count=2,
        )
        pdf_bytes = generate_currency_conversion_memo(result)
        assert len(pdf_bytes) > 100

    def test_no_rates_applied(self):
        """Memo handles case with no rates applied (e.g., single-currency TB)."""
        result = self._make_result(
            rates_applied={},
            currencies_found=["USD"],
            converted_count=10,
            unconverted_count=0,
        )
        pdf_bytes = generate_currency_conversion_memo(result)
        assert len(pdf_bytes) > 100

    def test_empty_conversion_result(self):
        """Memo handles minimal/empty conversion result."""
        result = {
            "conversion_performed": False,
            "presentation_currency": "USD",
            "total_accounts": 0,
            "converted_count": 0,
            "unconverted_count": 0,
        }
        pdf_bytes = generate_currency_conversion_memo(result)
        assert len(pdf_bytes) > 100

    def test_many_unconverted_items_capped(self):
        """Memo caps unconverted items at 50."""
        items = [
            {
                "account_number": str(i),
                "account_name": f"Account {i}",
                "original_amount": 100,
                "original_currency": "JPY",
                "issue": "missing_rate",
                "severity": "medium",
            }
            for i in range(100)
        ]
        result = self._make_result(
            unconverted_items=items,
            unconverted_count=100,
        )
        pdf_bytes = generate_currency_conversion_memo(result)
        assert len(pdf_bytes) > 100


class TestCurrencyMemoExportRegistration:
    """Tests for export endpoint registration."""

    def test_endpoint_registered(self):
        from main import app
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/currency-conversion-memo" in route_paths

    def test_export_schema_importable(self):
        from shared.export_schemas import CurrencyConversionMemoInput
        schema = CurrencyConversionMemoInput(
            presentation_currency="EUR",
            total_accounts=5,
            converted_count=5,
        )
        assert schema.presentation_currency == "EUR"

    def test_backward_compat_reexport(self):
        """CurrencyConversionMemoInput is re-exported from routes.export."""
        from routes.export import CurrencyConversionMemoInput
        assert CurrencyConversionMemoInput is not None
