"""Sprint 634 — Form 1099 Preparation engine tests."""

from decimal import Decimal

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
                _payment(amount="500", category=PaymentCategory.RENTS),
                _payment(amount="400", category=PaymentCategory.LEGAL),
            ],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        candidate = result.candidates[0]
        assert candidate.form_type == "1099-MISC"
        assert candidate.total_reportable == Decimal("900.00")
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
                _vendor(vendor_id="V2", name="Vendor B"),
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
