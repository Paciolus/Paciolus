"""Sprint 634 — Form 1099 Preparation engine tests."""

from decimal import Decimal

import pytest

from form_1099_engine import (
    FORM_THRESHOLDS,
    EntityType,
    Form1099Config,
    Form1099InputError,
    FormType,
    PaymentCategory,
    PaymentMethod,
    VendorPayment,
    VendorRecord,
    prepare_1099s,
)


def _vendor(
    vendor_id: str = "V1",
    name: str = "Test Vendor",
    tin: str | None = "12-3456789",
    entity: EntityType = EntityType.INDIVIDUAL,
    address: str = "123 Main",
    state: str = "NY",
    postal: str = "10001",
) -> VendorRecord:
    return VendorRecord(
        vendor_id=vendor_id,
        vendor_name=name,
        tin=tin,
        entity_type=entity,
        address_line_1=address,
        city="New York",
        state=state,
        postal_code=postal,
    )


def _payment(
    vendor_id: str = "V1",
    amount: str = "1000",
    category: PaymentCategory = PaymentCategory.NONEMPLOYEE_COMP,
    method: PaymentMethod = PaymentMethod.CHECK,
) -> VendorPayment:
    return VendorPayment(
        vendor_id=vendor_id,
        amount=Decimal(amount),
        payment_category=category,
        payment_method=method,
    )


class TestThresholds:
    def test_nec_at_600_fires(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[_payment(amount="600")],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].form_type == "1099-NEC"
        assert result.candidates[0].total_reportable == Decimal("600.00")

    def test_nec_below_600_does_not_fire(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[_payment(amount="599.99")],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []

    def test_int_threshold_ten_dollars(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[_payment(amount="10", category=PaymentCategory.INTEREST)],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].form_type == "1099-INT"


class TestExemptions:
    def test_corporation_not_reported(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000")],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []

    def test_corporation_still_reported_for_legal(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000", category=PaymentCategory.LEGAL)],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].form_type == "1099-MISC"

    def test_corporation_still_reported_for_medical(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000", category=PaymentCategory.MEDICAL)],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1

    def test_credit_card_excluded(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[
                _payment(amount="5000", method=PaymentMethod.CREDIT_CARD),
            ],
        )
        result = prepare_1099s(cfg)
        # No candidate — entirely below the (remaining-payment) threshold
        # because the credit card payment was excluded from the aggregate.
        assert result.candidates == []

    def test_paypal_excluded(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[_payment(amount="5000", method=PaymentMethod.PAYPAL)],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []


class TestAggregation:
    def test_multiple_payments_aggregated_per_form(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[
                _payment(amount="300"),
                _payment(amount="300"),
                _payment(amount="100"),
            ],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].total_reportable == Decimal("700.00")
        assert result.candidates[0].payment_count == 3

    def test_boxes_split_by_category(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[
                # Sprint 826 (F6): rents must reach $600 on their own — this test
                # used $500 + $400, which is not a filing at all under per-box
                # thresholds. Once one box qualifies, every box is reported.
                _payment(amount="700", category=PaymentCategory.RENTS),
                _payment(amount="400", category=PaymentCategory.LEGAL),
            ],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        candidate = result.candidates[0]
        assert candidate.form_type == "1099-MISC"
        assert candidate.total_reportable == Decimal("1100.00")
        boxes = {b.category: b for b in candidate.box_amounts}
        assert boxes["rents"].box == 1
        assert boxes["legal"].box == 10

    def test_different_form_types_are_separate_candidates(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[
                _payment(amount="700"),  # NEC
                _payment(amount="800", category=PaymentCategory.RENTS),  # MISC
            ],
        )
        result = prepare_1099s(cfg)
        form_types = {c.form_type for c in result.candidates}
        assert form_types == {"1099-NEC", "1099-MISC"}


class TestDataQuality:
    def test_missing_tin_flags_for_w9(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor(tin=None)],
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        assert len(result.w9_collection_list) == 1
        assert result.w9_collection_list[0].reason == "TIN missing"

    def test_invalid_tin_format_flags_for_w9(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor(tin="123")],  # too short
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        assert len(result.w9_collection_list) == 1
        assert result.w9_collection_list[0].reason == "TIN format invalid"

    def test_missing_address_flagged_on_quality_report(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor(address="", state="")],
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        dq = result.data_quality[0]
        assert dq.missing_address is True
        assert dq.has_issue is True


class TestSummary:
    def test_summary_aggregates_totals_and_counts(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[
                _vendor(vendor_id="V1", name="Vendor A"),
                # Distinct TIN: with the shared default these are one payee
                # (Sprint 826, F3 — filing is per TIN, not per vendor record).
                _vendor(vendor_id="V2", name="Vendor B", tin="98-7654321"),
            ],
            payments=[
                _payment(vendor_id="V1", amount="1000"),
                _payment(vendor_id="V2", amount="2000"),
            ],
        )
        result = prepare_1099s(cfg)
        summary = result.summary
        assert summary["total_candidates"] == 2
        assert summary["counts_by_form"]["1099-NEC"] == 2
        assert Decimal(summary["totals_by_form"]["1099-NEC"]) == Decimal("3000.00")


class TestInputValidation:
    def test_invalid_tax_year_rejected(self):
        try:
            prepare_1099s(Form1099Config(tax_year=1999, vendors=[], payments=[]))
        except Form1099InputError:
            return
        raise AssertionError("expected Form1099InputError")


class TestSerialisation:
    def test_to_dict_roundtrip(self):
        cfg = Form1099Config(
            tax_year=2026,
            vendors=[_vendor()],
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        d = result.to_dict()
        assert d["tax_year"] == 2026
        assert isinstance(d["candidates"], list)
        assert "summary" in d


class TestThresholdConstants:
    def test_thresholds_match_irs_standards(self):
        assert FORM_THRESHOLDS[FormType.NEC] == Decimal("600")
        assert FORM_THRESHOLDS[FormType.MISC] == Decimal("600")
        assert FORM_THRESHOLDS[FormType.INT] == Decimal("10")


class TestSprint826:
    """Sprint 823 discovery findings F1, F2, F3, F6, F7."""

    def test_royalties_report_at_ten_dollars(self):
        """F1: a $450 royalty produced no 1099-MISC (it used the $600 threshold)."""
        cfg = Form1099Config(
            tax_year=2025, vendors=[_vendor()], payments=[_payment(amount="450", category=PaymentCategory.ROYALTIES)]
        )
        (candidate,) = prepare_1099s(cfg).candidates
        assert candidate.form_type == "1099-MISC"
        assert candidate.box_amounts[0].box == 2

    def test_misc_threshold_is_per_box_not_combined(self):
        """F6: rents $400 + medical $300 is not a $700 filing."""
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor()],
            payments=[
                _payment(amount="400", category=PaymentCategory.RENTS),
                _payment(amount="300", category=PaymentCategory.MEDICAL),
            ],
        )
        assert prepare_1099s(cfg).candidates == []

    def test_other_income_is_misc_box_3(self):
        """F7: it was reported in box 0, which does not exist."""
        cfg = Form1099Config(
            tax_year=2025, vendors=[_vendor()], payments=[_payment(amount="900", category=PaymentCategory.OTHER)]
        )
        (candidate,) = prepare_1099s(cfg).candidates
        assert candidate.box_amounts[0].box == 3

    def test_payments_dated_outside_the_tax_year_are_excluded(self):
        """F2: payment_date was never read; Dec 2024 and Jan 2026 counted toward 2025."""
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor()],
            payments=[
                VendorPayment(vendor_id="V1", amount=Decimal("400"), payment_date="2024-12-20"),
                VendorPayment(vendor_id="V1", amount=Decimal("400"), payment_date="2025-03-01"),
                VendorPayment(vendor_id="V1", amount=Decimal("400"), payment_date="2026-01-05"),
            ],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []
        assert result.summary["payments_outside_tax_year"] == 2

    def test_vendor_records_sharing_a_tin_are_one_payee(self):
        """F3: $400 + $400 under two vendor IDs with one TIN produced no 1099."""
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(vendor_id="V1"), _vendor(vendor_id="V1-OLD", name="Test Vendor (old record)")],
            payments=[_payment(vendor_id="V1", amount="400"), _payment(vendor_id="V1-OLD", amount="400")],
        )
        (candidate,) = prepare_1099s(cfg).candidates
        assert candidate.total_reportable == Decimal("800.00")
        assert candidate.payment_count == 2
        assert any("V1, V1-OLD" in reason for reason in candidate.review_reasons)

    @pytest.mark.parametrize("entity", [EntityType.GOVERNMENT, EntityType.TAX_EXEMPT])
    def test_governments_and_tax_exempt_payees_are_not_reported(self, entity):
        """F8: $5,000 to each was reported as 1099-NEC."""
        cfg = Form1099Config(tax_year=2025, vendors=[_vendor(entity=entity)], payments=[_payment(amount="5000")])
        assert prepare_1099s(cfg).candidates == []
