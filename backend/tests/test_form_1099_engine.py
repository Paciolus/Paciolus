"""Sprint 634 — 1099 Vendor Threshold Review engine tests.

Sprint 837: the original tests ran as tax year 2026 while asserting the $600
rules. For 2026 the 1099-NEC / 1099-MISC threshold is $2,000, so those tests
pinned the stale figure; they now run as 2025, the last year the $600 rules
apply. The 2026+ behaviour is covered by TestSprint837ThresholdsByYear.
"""

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
    thresholds_for_year,
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
            tax_year=2025,
            vendors=[_vendor()],
            payments=[_payment(amount="600")],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].form_type == "1099-NEC"
        assert result.candidates[0].total_reportable == Decimal("600.00")

    def test_nec_below_600_does_not_fire(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor()],
            payments=[_payment(amount="599.99")],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []

    def test_int_threshold_ten_dollars(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor()],
            payments=[_payment(amount="10", category=PaymentCategory.INTEREST)],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].form_type == "1099-INT"


class TestExemptions:
    def test_corporation_not_reported(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000")],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []

    def test_corporation_still_reported_for_legal(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000", category=PaymentCategory.LEGAL)],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1
        assert result.candidates[0].form_type == "1099-MISC"

    def test_corporation_still_reported_for_medical(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000", category=PaymentCategory.MEDICAL)],
        )
        result = prepare_1099s(cfg)
        assert len(result.candidates) == 1

    def test_credit_card_excluded(self):
        cfg = Form1099Config(
            tax_year=2025,
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
            tax_year=2025,
            vendors=[_vendor()],
            payments=[_payment(amount="5000", method=PaymentMethod.PAYPAL)],
        )
        result = prepare_1099s(cfg)
        assert result.candidates == []


class TestAggregation:
    def test_multiple_payments_aggregated_per_form(self):
        cfg = Form1099Config(
            tax_year=2025,
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
            tax_year=2025,
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
            tax_year=2025,
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
            tax_year=2025,
            vendors=[_vendor(tin=None)],
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        assert len(result.w9_collection_list) == 1
        assert result.w9_collection_list[0].reason == "TIN missing"

    def test_invalid_tin_format_flags_for_w9(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(tin="123")],  # too short
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        assert len(result.w9_collection_list) == 1
        assert result.w9_collection_list[0].reason == "TIN format invalid"

    def test_missing_address_flagged_on_quality_report(self):
        cfg = Form1099Config(
            tax_year=2025,
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
            tax_year=2025,
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
            tax_year=2025,
            vendors=[_vendor()],
            payments=[_payment(amount="1000")],
        )
        result = prepare_1099s(cfg)
        d = result.to_dict()
        assert d["tax_year"] == 2025
        assert isinstance(d["candidates"], list)
        assert "summary" in d


class TestThresholdConstants:
    def test_pre_2026_thresholds_match_irs_standards(self):
        """Sprint 837: FORM_THRESHOLDS holds the figures for tax years through 2025."""
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

    def test_attorney_fees_are_nec_even_for_a_corporate_law_firm(self):
        """F4: fees for legal services had no correct path — "legal" went to MISC
        box 10 (gross proceeds) and "nonemployee_comp" excluded the corporation."""
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000", category=PaymentCategory.ATTORNEY_FEES)],
        )
        (candidate,) = prepare_1099s(cfg).candidates
        assert candidate.form_type == "1099-NEC"
        assert candidate.box_amounts[0].box == 1

    def test_gross_proceeds_to_an_attorney_stay_misc_box_10(self):
        cfg = Form1099Config(
            tax_year=2025,
            vendors=[_vendor(entity=EntityType.CORPORATION)],
            payments=[_payment(amount="5000", category=PaymentCategory.LEGAL)],
        )
        (candidate,) = prepare_1099s(cfg).candidates
        assert (candidate.form_type, candidate.box_amounts[0].box) == ("1099-MISC", 10)


class TestSprint837ThresholdsByYear:
    """Sprint 837: 1099 thresholds are keyed by tax year.

    The engine applied $600 to every year. Secondary sources report that the
    One Big Beautiful Bill Act (2025) raised the 1099-NEC / 1099-MISC threshold
    to $2,000 for payments made after December 31, 2025. Each test here fails on
    the pre-837 engine.
    """

    def test_2026_nec_payee_at_1500_is_not_a_candidate_but_is_listed_below_threshold(self):
        result = prepare_1099s(Form1099Config(tax_year=2026, vendors=[_vendor()], payments=[_payment(amount="1500")]))
        assert result.candidates == []
        (payee,) = result.below_threshold_payees
        assert payee.vendor_id == "V1"
        assert payee.form_type == "1099-NEC"
        assert payee.total == Decimal("1500.00")
        assert "below the 2026 reporting threshold" in payee.reason.lower()
        assert "not required, shown for review" in payee.reason
        assert result.summary["below_threshold_count"] == 1
        d = result.to_dict()
        assert d["below_threshold_payees"][0]["total"] == "1500.00"

    def test_2025_nec_payee_at_1500_is_a_candidate(self):
        result = prepare_1099s(Form1099Config(tax_year=2025, vendors=[_vendor()], payments=[_payment(amount="1500")]))
        (candidate,) = result.candidates
        assert candidate.form_type == "1099-NEC"
        assert result.below_threshold_payees == []
        assert result.notices == []

    def test_2026_nec_at_2000_is_a_candidate(self):
        result = prepare_1099s(Form1099Config(tax_year=2026, vendors=[_vendor()], payments=[_payment(amount="2000")]))
        assert len(result.candidates) == 1

    def test_2026_below_600_is_neither_candidate_nor_listed(self):
        result = prepare_1099s(Form1099Config(tax_year=2026, vendors=[_vendor()], payments=[_payment(amount="599.99")]))
        assert result.candidates == []
        assert result.below_threshold_payees == []

    def test_2027_uses_2000_with_a_notice_that_the_indexed_figure_is_not_in_paciolus(self):
        result = prepare_1099s(
            Form1099Config(
                tax_year=2027,
                vendors=[_vendor(), _vendor(vendor_id="V2", tin="98-7654321")],
                payments=[_payment(amount="1999.99"), _payment(vendor_id="V2", amount="2000")],
            )
        )
        assert [c.vendor_id for c in result.candidates] == ["V2"]
        assert [b.vendor_id for b in result.below_threshold_payees] == ["V1"]
        assert any("inflation-adjusted" in n and "2027" in n and "not in Paciolus" in n for n in result.notices)
        d = result.to_dict()
        assert d["thresholds"]["tax_year"] == 2027
        assert d["thresholds"]["figures_from_tax_year"] == 2026
        assert d["notices"] == result.notices

    @pytest.mark.parametrize("year", [2025, 2026, 2027])
    def test_royalties_stay_at_ten_dollars(self, year):
        result = prepare_1099s(
            Form1099Config(
                tax_year=year,
                vendors=[_vendor()],
                payments=[_payment(amount="10", category=PaymentCategory.ROYALTIES)],
            )
        )
        (candidate,) = result.candidates
        assert (candidate.form_type, candidate.box_amounts[0].box) == ("1099-MISC", 2)

    def test_2026_interest_stays_at_ten_dollars(self):
        result = prepare_1099s(
            Form1099Config(
                tax_year=2026,
                vendors=[_vendor()],
                payments=[_payment(amount="10", category=PaymentCategory.INTEREST)],
            )
        )
        assert [c.form_type for c in result.candidates] == ["1099-INT"]

    def test_2026_rents_at_1500_are_listed_below_threshold(self):
        result = prepare_1099s(
            Form1099Config(
                tax_year=2026,
                vendors=[_vendor()],
                payments=[_payment(amount="1500", category=PaymentCategory.RENTS)],
            )
        )
        assert result.candidates == []
        (payee,) = result.below_threshold_payees
        assert payee.form_type == "1099-MISC"
        assert "box 1" in payee.reason

    def test_2026_attorney_gross_proceeds_keep_600_and_are_marked_for_confirmation(self):
        result = prepare_1099s(
            Form1099Config(
                tax_year=2026,
                vendors=[_vendor(entity=EntityType.CORPORATION)],
                payments=[_payment(amount="600", category=PaymentCategory.LEGAL)],
            )
        )
        (candidate,) = result.candidates
        assert candidate.box_amounts[0].box == 10
        box10 = next(i for i in result.thresholds.items if i.form_type == FormType.MISC and i.box == 10)
        assert box10.amount == Decimal("600")
        assert box10.needs_confirmation is True

    def test_result_carries_thresholds_and_basis(self):
        d = prepare_1099s(Form1099Config(tax_year=2026, vendors=[_vendor()], payments=[])).to_dict()
        nec = next(i for i in d["thresholds"]["items"] if i["form_type"] == "1099-NEC")
        assert nec["amount"] == "2000.00"
        assert "One Big Beautiful Bill Act" in nec["basis"]
        assert "IRS Instructions for Forms 1099-MISC" in d["thresholds"]["confirm_against"]
        assert "2026" in d["thresholds"]["confirm_against"]
        assert d["notices"], "2026 runs explain the threshold change"

    @pytest.mark.parametrize(
        ("year", "table_year", "nec"),
        [(2000, 2025, "600"), (2025, 2025, "600"), (2026, 2026, "2000"), (2031, 2026, "2000")],
    )
    def test_thresholds_for_year(self, year, table_year, nec):
        schedule = thresholds_for_year(year)
        assert schedule.table_year == table_year
        assert schedule.form_threshold(FormType.NEC) == Decimal(nec)
        assert schedule.form_threshold(FormType.INT) == Decimal("10")
        assert schedule.box_threshold(FormType.MISC, 2) == Decimal("10")
