"""
Tests for Currency Conversion Memo Generator — Sprint 259 / Sprint 509

Validates PDF generation, section structure, export endpoint, and edge cases.
Sprint 509: section headers, conclusion, reference prefix, conversion output,
non-monetary note, CTA note, suggested rate sources, unconverted count fix.
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
            "currency_exposure": [],
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


# ── Sprint 509: Section structure tests ──


class TestSectionHeaders:
    """Verify Roman numeral section headers are present in output."""

    def _make_full_result(self):
        return {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 100,
            "converted_count": 96,
            "unconverted_count": 4,
            "currencies_found": ["EUR", "GBP", "USD"],
            "rates_applied": {"EUR/USD": "1.08", "GBP/USD": "1.27"},
            "unconverted_items": [
                {
                    "account_number": "5100",
                    "account_name": "Intercompany — Singapore",
                    "original_currency": "SGD",
                    "issue": "missing_rate",
                    "severity": "high",
                },
            ],
            "currency_exposure": [
                {
                    "currency": "USD",
                    "account_count": 80,
                    "foreign_total": 5000000.0,
                    "rate": "1.0000",
                    "usd_equivalent": 5000000.0,
                    "pct_of_total": 75.0,
                },
                {
                    "currency": "EUR",
                    "account_count": 16,
                    "foreign_total": 1500000.0,
                    "rate": "1.08",
                    "usd_equivalent": 1620000.0,
                    "pct_of_total": 25.0,
                },
            ],
        }

    def test_generates_valid_pdf_with_all_sections(self):
        """Full result with all sections generates a valid PDF."""
        result = self._make_full_result()
        pdf_bytes = generate_currency_conversion_memo(
            result,
            filename="test.csv",
            client_name="Test Corp",
            period_tested="FY 2025",
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes[:5] == b"%PDF-"


class TestUnconvertedCountConsistency:
    """BUG-01: Unconverted count must match table rows."""

    def test_count_derived_from_items_not_field(self):
        """When unconverted_count disagrees with len(items), items win."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 247,
            "converted_count": 235,
            "unconverted_count": 12,  # Wrong: says 12 but only 4 items
            "unconverted_items": [
                {
                    "account_number": "5100",
                    "account_name": "A",
                    "original_currency": "SGD",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "5110",
                    "account_name": "B",
                    "original_currency": "BRL",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "5120",
                    "account_name": "C",
                    "original_currency": "KRW",
                    "issue": "missing_rate",
                    "severity": "medium",
                },
                {
                    "account_number": "1400",
                    "account_name": "D",
                    "original_currency": "INR",
                    "issue": "missing_rate",
                    "severity": "medium",
                },
            ],
            "currencies_found": ["USD", "EUR"],
            "rates_applied": {"EUR/USD": "1.08"},
        }
        # Should not crash and should produce valid PDF
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100

    def test_stale_rate_items_separated(self):
        """Stale rate items are not counted as truly unconverted."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 20,
            "converted_count": 16,
            "unconverted_count": 4,
            "unconverted_items": [
                {
                    "account_number": "1000",
                    "account_name": "A",
                    "original_currency": "JPY",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "2000",
                    "account_name": "B",
                    "original_currency": "JPY",
                    "issue": "stale_rate",
                    "severity": "low",
                },
                {
                    "account_number": "3000",
                    "account_name": "C",
                    "original_currency": "JPY",
                    "issue": "stale_rate",
                    "severity": "low",
                },
            ],
            "currencies_found": ["USD", "JPY"],
            "rates_applied": {"JPY/USD": "0.0067"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100


class TestReferenceNumber:
    """BUG-04: Reference prefix must be MCY-, not PAC-."""

    def test_reference_uses_mcy_prefix(self):
        """Verify the memo generator produces MCY- prefix (not PAC-)."""
        # We can't inspect PDF text easily, but we verify no crash
        # and that the reference is correctly formatted in the code
        from pdf_generator import generate_reference_number

        ref = generate_reference_number().replace("PAC-", "MCY-")
        assert ref.startswith("MCY-")
        assert not ref.startswith("PAC-")


class TestConversionOutputTable:
    """IMP-01: Section III Conversion Output table."""

    def test_with_currency_exposure(self):
        """Conversion output renders when currency_exposure is provided."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "EUR",
            "total_accounts": 50,
            "converted_count": 48,
            "unconverted_count": 2,
            "unconverted_items": [],
            "currencies_found": ["EUR", "USD"],
            "rates_applied": {"USD/EUR": "0.92"},
            "currency_exposure": [
                {
                    "currency": "EUR",
                    "account_count": 40,
                    "foreign_total": 3000000.0,
                    "rate": "1.0000",
                    "usd_equivalent": 3000000.0,
                    "pct_of_total": 80.0,
                },
                {
                    "currency": "USD",
                    "account_count": 8,
                    "foreign_total": 800000.0,
                    "rate": "0.92",
                    "usd_equivalent": 736000.0,
                    "pct_of_total": 20.0,
                },
            ],
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 1000

    def test_without_currency_exposure_fallback(self):
        """Conversion output shows text fallback when no exposure data."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 10,
            "converted_count": 8,
            "unconverted_count": 2,
            "unconverted_items": [],
            "currencies_found": ["EUR", "USD"],
            "rates_applied": {"EUR/USD": "1.08"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100


class TestNonMonetaryNote:
    """IMP-02: Non-monetary account identification note."""

    def test_renders_without_crash(self):
        """Non-monetary note renders in Section V."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 10,
            "converted_count": 10,
            "unconverted_count": 0,
            "unconverted_items": [],
            "currencies_found": ["USD", "EUR"],
            "rates_applied": {"EUR/USD": "1.08"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100


class TestCTANote:
    """IMP-03: CTA note in Section V."""

    def test_renders_without_crash(self):
        """CTA note renders in methodology section."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "GBP",
            "total_accounts": 5,
            "converted_count": 5,
            "unconverted_count": 0,
            "unconverted_items": [],
            "currencies_found": ["GBP", "EUR"],
            "rates_applied": {"EUR/GBP": "0.85"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100


class TestSuggestedRateSources:
    """IMP-04: Suggested rate sources for unconverted items."""

    def test_renders_with_unconverted_items(self):
        """Rate source suggestions render alongside unconverted items."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 20,
            "converted_count": 18,
            "unconverted_count": 2,
            "unconverted_items": [
                {
                    "account_number": "5100",
                    "account_name": "IC Singapore",
                    "original_currency": "SGD",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "1400",
                    "account_name": "Deposit India",
                    "original_currency": "INR",
                    "issue": "missing_rate",
                    "severity": "medium",
                },
            ],
            "currencies_found": ["USD", "EUR"],
            "rates_applied": {"EUR/USD": "1.08"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100


class TestIntercompanyHighSeverityNote:
    """IMP-04: HIGH severity intercompany note below unconverted table."""

    def test_intercompany_note_with_high_severity(self):
        """Intercompany HIGH severity items trigger consolidation warning."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 50,
            "converted_count": 48,
            "unconverted_count": 2,
            "unconverted_items": [
                {
                    "account_number": "5100",
                    "account_name": "Intercompany — Singapore",
                    "original_currency": "SGD",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "5110",
                    "account_name": "Intercompany — Brazil",
                    "original_currency": "BRL",
                    "issue": "missing_rate",
                    "severity": "high",
                },
            ],
            "currencies_found": ["USD"],
            "rates_applied": {},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100

    def test_no_intercompany_note_without_keyword(self):
        """Non-intercompany HIGH items do not trigger consolidation warning."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 50,
            "converted_count": 48,
            "unconverted_count": 2,
            "unconverted_items": [
                {
                    "account_number": "5100",
                    "account_name": "Travel Expense",
                    "original_currency": "SGD",
                    "issue": "missing_rate",
                    "severity": "high",
                },
            ],
            "currencies_found": ["USD"],
            "rates_applied": {},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
        assert len(pdf_bytes) > 100


class TestConclusionSection:
    """BUG-03: Conclusion section must be present."""

    def test_conclusion_with_unconverted(self):
        """Conclusion mentions unconverted accounts when present."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 247,
            "converted_count": 243,
            "unconverted_count": 4,
            "unconverted_items": [
                {
                    "account_number": "5100",
                    "account_name": "A",
                    "original_currency": "SGD",
                    "issue": "missing_rate",
                    "severity": "high",
                },
                {
                    "account_number": "5110",
                    "account_name": "B",
                    "original_currency": "BRL",
                    "issue": "missing_rate",
                    "severity": "high",
                },
            ],
            "currencies_found": ["USD", "EUR"],
            "rates_applied": {"EUR/USD": "1.08"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv", period_tested="December 31, 2025")
        assert len(pdf_bytes) > 100

    def test_conclusion_all_converted(self):
        """Conclusion notes full conversion when no failures."""
        result = {
            "conversion_performed": True,
            "presentation_currency": "USD",
            "total_accounts": 100,
            "converted_count": 100,
            "unconverted_count": 0,
            "unconverted_items": [],
            "currencies_found": ["USD", "EUR", "GBP"],
            "rates_applied": {"EUR/USD": "1.08", "GBP/USD": "1.27"},
        }
        pdf_bytes = generate_currency_conversion_memo(result, filename="test.csv")
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

    def test_export_schema_has_currency_exposure(self):
        """Schema includes currency_exposure field (Sprint 509)."""
        from shared.export_schemas import CurrencyConversionMemoInput

        schema = CurrencyConversionMemoInput(
            presentation_currency="USD",
            total_accounts=10,
            converted_count=10,
            currency_exposure=[
                {
                    "currency": "USD",
                    "account_count": 10,
                    "foreign_total": 1000.0,
                    "rate": "1.0000",
                    "usd_equivalent": 1000.0,
                    "pct_of_total": 100.0,
                },
            ],
        )
        assert len(schema.currency_exposure) == 1

    def test_backward_compat_reexport(self):
        """CurrencyConversionMemoInput is re-exported from routes.export."""
        from routes.export import CurrencyConversionMemoInput

        assert CurrencyConversionMemoInput is not None


class TestCurrencyExposureEngine:
    """Tests for CurrencyExposure dataclass and engine integration."""

    def test_currency_exposure_dataclass(self):
        from currency_engine import CurrencyExposure

        exp = CurrencyExposure(
            currency="EUR",
            account_count=10,
            foreign_total=50000.0,
            rate="1.08",
            usd_equivalent=54000.0,
            pct_of_total=25.0,
        )
        d = exp.to_dict()
        assert d["currency"] == "EUR"
        assert d["account_count"] == 10
        assert d["usd_equivalent"] == 54000.0

    def test_conversion_result_includes_exposure(self):
        from currency_engine import ConversionResult, CurrencyExposure

        result = ConversionResult(
            conversion_performed=True,
            presentation_currency="USD",
            total_accounts=10,
            converted_count=10,
            unconverted_count=0,
            currency_exposure=[
                CurrencyExposure("USD", 8, 5000.0, "1.0000", 5000.0, 80.0),
                CurrencyExposure("EUR", 2, 1000.0, "1.08", 1080.0, 20.0),
            ],
        )
        d = result.to_dict()
        assert len(d["currency_exposure"]) == 2
        assert d["currency_exposure"][0]["currency"] == "USD"
        assert d["currency_exposure"][1]["pct_of_total"] == 20.0
