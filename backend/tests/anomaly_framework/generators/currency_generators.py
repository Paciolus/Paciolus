"""Multi-Currency anomaly generators.

Each generator injects a specific currency-related anomaly into clean
multi-currency trial balance and exchange rate data, returning
AnomalyRecords describing the expected detection outcome.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class CurrencyGeneratorBase:
    """Base class for multi-currency anomaly generators."""

    name: str
    target_test_key: str

    def inject(
        self,
        tb_rows: list[dict],
        rate_rows: list[dict],
        seed: int = 42,
    ) -> tuple[list[dict], list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


class MissingExchangeRateGenerator(CurrencyGeneratorBase):
    """Inject a TB row with a currency that has no exchange rate.

    Adds a TB account denominated in JPY with no JPY->USD rate in the
    rate table, simulating incomplete rate coverage.
    """

    name = "missing_exchange_rate"
    target_test_key = "missing_rates"

    def inject(self, tb_rows, rate_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        rate_rows = deepcopy(rate_rows)

        tb_rows.append(
            {
                "Account": "1030",
                "Account Name": "Cash - Yen Account",
                "Account Type": "Asset",
                "Debit": 5400000.00,
                "Credit": 0.00,
                "Currency": "JPY",
            }
        )

        record = AnomalyRecord(
            anomaly_type="missing_exchange_rate",
            report_targets=["CURR-01"],
            injected_at="Account 1030 in JPY with no JPY->USD rate",
            expected_field="missing_rates",
            expected_condition="items_count > 0",
            metadata={
                "account": "1030",
                "currency": "JPY",
                "amount": 5400000.00,
            },
        )
        return tb_rows, rate_rows, [record]


class InvalidCurrencyCodeGenerator(CurrencyGeneratorBase):
    """Inject a TB row with an invalid ISO 4217 currency code.

    Adds a TB account with currency code "XXX" (no currency), testing
    the engine's validation of currency codes.
    """

    name = "invalid_currency_code"
    target_test_key = "invalid_currencies"

    def inject(self, tb_rows, rate_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        rate_rows = deepcopy(rate_rows)

        tb_rows.append(
            {
                "Account": "1099",
                "Account Name": "Miscellaneous Foreign Cash",
                "Account Type": "Asset",
                "Debit": 12345.67,
                "Credit": 0.00,
                "Currency": "XXX",
            }
        )

        record = AnomalyRecord(
            anomaly_type="invalid_currency_code",
            report_targets=["CURR-02"],
            injected_at="Account 1099 with invalid currency code 'XXX'",
            expected_field="invalid_currencies",
            expected_condition="items_count > 0",
            metadata={
                "account": "1099",
                "currency": "XXX",
                "amount": 12345.67,
            },
        )
        return tb_rows, rate_rows, [record]


class ZeroExchangeRateGenerator(CurrencyGeneratorBase):
    """Inject a rate table entry with rate = 0.

    Modifies an existing rate to zero, testing the engine's handling
    of invalid (zero-division) exchange rates.
    """

    name = "zero_exchange_rate"
    target_test_key = "zero_rates"

    def inject(self, tb_rows, rate_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        rate_rows = deepcopy(rate_rows)

        # Set EUR->USD rate to zero
        for rate in rate_rows:
            if rate["From Currency"] == "EUR":
                rate["Rate"] = 0.0
                break

        record = AnomalyRecord(
            anomaly_type="zero_exchange_rate",
            report_targets=["CURR-03"],
            injected_at="EUR->USD exchange rate set to 0.0",
            expected_field="zero_rates",
            expected_condition="items_count > 0",
            metadata={
                "from_currency": "EUR",
                "to_currency": "USD",
                "rate": 0.0,
            },
        )
        return tb_rows, rate_rows, [record]


class StaleExchangeRateGenerator(CurrencyGeneratorBase):
    """Inject a rate with an old effective date (>90 days stale).

    Changes the effective date of an exchange rate to over 90 days ago,
    simulating outdated rate data that may produce inaccurate conversions.
    """

    name = "stale_exchange_rate"
    target_test_key = "stale_rates"

    def inject(self, tb_rows, rate_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        rate_rows = deepcopy(rate_rows)

        # Set GBP->USD rate effective date to 120 days ago
        for rate in rate_rows:
            if rate["From Currency"] == "GBP":
                rate["Effective Date"] = "2025-02-01"  # ~120 days before June 2025
                break

        record = AnomalyRecord(
            anomaly_type="stale_exchange_rate",
            report_targets=["CURR-04"],
            injected_at="GBP->USD rate effective date set to 2025-02-01 (>90 days stale)",
            expected_field="stale_rates",
            expected_condition="items_count > 0",
            metadata={
                "from_currency": "GBP",
                "to_currency": "USD",
                "effective_date": "2025-02-01",
                "staleness_days": 121,
            },
        )
        return tb_rows, rate_rows, [record]


class NegativeExchangeRateGenerator(CurrencyGeneratorBase):
    """Inject a rate table entry with a negative rate.

    Modifies an existing rate to a negative value, testing the engine's
    validation of rate signs.
    """

    name = "negative_exchange_rate"
    target_test_key = "negative_rates"

    def inject(self, tb_rows, rate_rows, seed=42):
        tb_rows = deepcopy(tb_rows)
        rate_rows = deepcopy(rate_rows)

        # Set EUR->USD rate to negative
        for rate in rate_rows:
            if rate["From Currency"] == "EUR":
                rate["Rate"] = -1.0850
                break

        record = AnomalyRecord(
            anomaly_type="negative_exchange_rate",
            report_targets=["CURR-05"],
            injected_at="EUR->USD exchange rate set to -1.0850",
            expected_field="negative_rates",
            expected_condition="items_count > 0",
            metadata={
                "from_currency": "EUR",
                "to_currency": "USD",
                "rate": -1.0850,
            },
        )
        return tb_rows, rate_rows, [record]


CURRENCY_REGISTRY: list[CurrencyGeneratorBase] = [
    MissingExchangeRateGenerator(),
    InvalidCurrencyCodeGenerator(),
    ZeroExchangeRateGenerator(),
    StaleExchangeRateGenerator(),
    NegativeExchangeRateGenerator(),
]
