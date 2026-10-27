"""Form 1099 preparation generators (Sprint 823 item 3) — 5 generators.

Baseline year 2025 (``FORM_1099_TAX_YEAR``). Thresholds are read from the
engine's table for that year, not typed here.
"""

from decimal import Decimal

from form_1099_engine import (
    EntityType,
    FormType,
    PaymentCategory,
    PaymentMethod,
    VendorPayment,
    VendorRecord,
    prepare_1099s,
    thresholds_for_year,
)
from tests.anomaly_framework.fixtures.base_config_tools import form_1099_baseline
from tests.anomaly_framework.generators.config_tool_base import ConfigGenerator, ToolHarness

FORM_1099_HARNESS = ToolHarness(
    tool="form_1099",
    engine="form_1099_engine.prepare_1099s",
    baseline=form_1099_baseline,
    run=lambda config: prepare_1099s(config).to_dict(),
)


def _candidate(result: dict, vendor_id: str) -> dict | None:
    return next((c for c in result["candidates"] if c["vendor_id"] == vendor_id), None)


class Form1099MissingTinGenerator(ConfigGenerator):
    """A reportable payee with no TIN must go on the W-9 collection list."""

    name = "f1099_missing_tin"
    target = "w9_collection_list"
    injected_at = "V1 TIN removed"

    def mutate(self, config):
        config.vendors[0].tin = None

    def detected(self, result):
        return any(w["vendor_id"] == "V1" for w in result["w9_collection_list"])


class Form1099InvalidTinGenerator(ConfigGenerator):
    """A TIN that is not 9 digits is a data-quality issue."""

    name = "f1099_invalid_tin"
    target = "data_quality[invalid_tin_format]"
    injected_at = "V2 TIN set to '45-67890' (7 digits)"

    def mutate(self, config):
        config.vendors[1].tin = "45-67890"

    def detected(self, result):
        return any(d["vendor_id"] == "V2" and d["invalid_tin_format"] for d in result["data_quality"])


class Form1099ProcessorPaymentGenerator(ConfigGenerator):
    """Card payments are reported by the processor on a 1099-K, not by the payer."""

    name = "f1099_processor_payment_excluded"
    target = "candidates[excluded_amount]"
    injected_at = "V2 also paid $3,000 by credit card"

    def mutate(self, config):
        config.payments.append(
            VendorPayment("V2", Decimal("3000"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CREDIT_CARD)
        )

    def detected(self, result):
        c = _candidate(result, "V2")
        return (
            c is not None
            and Decimal(c["excluded_amount"]) >= Decimal("3000")
            and Decimal(c["total_reportable"]) == Decimal("8000")
        )


class Form1099RoyaltyBelowGeneralThresholdGenerator(ConfigGenerator):
    """F1/F6 (Sprint 826): a royalty below the general threshold is still due.

    Royalties report at the box-2 figure ($10), not the NEC/MISC general one,
    so a payment between the two must produce a 1099-MISC.
    """

    name = "f1099_royalty_low_threshold"
    target = "candidates[1099-MISC box 2]"
    injected_at = "new individual payee V4 paid royalties of half the general MISC threshold"

    def mutate(self, config):
        schedule = thresholds_for_year(config.tax_year)
        amount = schedule.form_threshold(FormType.MISC) / 2
        assert amount >= schedule.box_threshold(FormType.MISC, 2), "fixture premise: above the royalty figure"
        config.vendors.append(
            VendorRecord("V4", "Quill Author", "321-54-9876", EntityType.INDIVIDUAL, "9 Elm", "Austin", "TX", "73301")
        )
        config.payments.append(VendorPayment("V4", amount, PaymentCategory.ROYALTIES, PaymentMethod.CHECK))

    def detected(self, result):
        c = _candidate(result, "V4")
        return c is not None and c["form_type"] == "1099-MISC" and any(b["box"] == 2 for b in c["box_amounts"])


class Form1099AttorneyFeesToCorporationGenerator(ConfigGenerator):
    """F4 (Sprint 826): legal fees are reportable even to a corporate law firm."""

    name = "f1099_attorney_fees_corporation"
    target = "candidates[1099-NEC, corporation]"
    injected_at = "corporate law firm V5 paid $12,000 of attorney fees"

    def mutate(self, config):
        config.vendors.append(
            VendorRecord(
                "V5", "Baxter Law LLP Inc", "77-1234567", EntityType.CORPORATION, "5 Court", "Albany", "NY", "12207"
            )
        )
        config.payments.append(
            VendorPayment("V5", Decimal("12000"), PaymentCategory.ATTORNEY_FEES, PaymentMethod.CHECK)
        )

    def detected(self, result):
        c = _candidate(result, "V5")
        return c is not None and c["form_type"] == "1099-NEC"


FORM_1099_REGISTRY = [
    Form1099MissingTinGenerator(),
    Form1099InvalidTinGenerator(),
    Form1099ProcessorPaymentGenerator(),
    Form1099RoyaltyBelowGeneralThresholdGenerator(),
    Form1099AttorneyFeesToCorporationGenerator(),
]
