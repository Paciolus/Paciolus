"""Statistical Sampling anomaly generators.

Each generator injects a specific population anomaly into clean sampling
population data, returning AnomalyRecords describing the expected detection
outcome. These anomalies test the sampling engine's ability to handle
edge cases in population data.
"""

import io
from copy import deepcopy

import pandas as pd

from tests.anomaly_framework.base import AnomalyRecord


class SamplingGeneratorBase:
    """Base class for sampling population anomaly generators."""

    name: str
    target_test_key: str

    def inject(
        self,
        rows: list[dict],
        seed: int = 42,
    ) -> tuple[list[dict], list[AnomalyRecord]]:
        raise NotImplementedError

    @staticmethod
    def rows_to_csv_bytes(rows: list[dict]) -> bytes:
        """Convert rows to CSV bytes for design_sample input."""
        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()


class HighValueItemGenerator(SamplingGeneratorBase):
    """Inject an item exceeding materiality threshold.

    Adds an extremely high-value item that should be 100% selected in
    MUS sampling regardless of sample size (top-stratum item).
    """

    name = "high_value_item"
    target_test_key = "high_value_items"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)

        rows.append(
            {
                "Item ID": "POP-HV1",
                "Recorded Amount": 275000.00,
                "Description": "Capital equipment acquisition - Building A expansion",
            }
        )

        record = AnomalyRecord(
            anomaly_type="high_value_item",
            report_targets=["SAMP-01"],
            injected_at="Item POP-HV1 with $275,000 (exceeds typical materiality)",
            expected_field="high_value_items",
            expected_condition="items_count > 0",
            metadata={"item_id": "POP-HV1", "amount": 275000.00},
        )
        return rows, [record]


class ZeroAmountItemGenerator(SamplingGeneratorBase):
    """Inject an item with zero recorded amount.

    Adds a population item with $0 amount, testing the engine's handling
    of zero-value items (typically excluded from MUS sampling).
    """

    name = "zero_amount_item"
    target_test_key = "zero_amount_items"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)

        rows.append(
            {
                "Item ID": "POP-ZRO",
                "Recorded Amount": 0.00,
                "Description": "Fully credited return - customer refund processed",
            }
        )

        record = AnomalyRecord(
            anomaly_type="zero_amount_item",
            report_targets=["SAMP-02"],
            injected_at="Item POP-ZRO with $0.00 recorded amount",
            expected_field="zero_amount_items",
            expected_condition="items_count >= 0",
            metadata={"item_id": "POP-ZRO", "amount": 0.00},
        )
        return rows, [record]


class NegativeAmountItemGenerator(SamplingGeneratorBase):
    """Inject an item with negative recorded amount.

    Adds a population item with a negative amount, testing the engine's
    handling of credit memos or adjustments in the population.
    """

    name = "negative_amount_item"
    target_test_key = "negative_amount_items"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)

        rows.append(
            {
                "Item ID": "POP-NEG",
                "Recorded Amount": -4523.78,
                "Description": "Credit memo - returned defective materials",
            }
        )

        record = AnomalyRecord(
            anomaly_type="negative_amount_item",
            report_targets=["SAMP-03"],
            injected_at="Item POP-NEG with -$4,523.78 recorded amount",
            expected_field="negative_amount_items",
            expected_condition="items_count > 0",
            metadata={"item_id": "POP-NEG", "amount": -4523.78},
        )
        return rows, [record]


class DuplicateItemIdGenerator(SamplingGeneratorBase):
    """Inject duplicate Item IDs in the population.

    Adds an item with the same Item ID as an existing population item,
    testing the engine's duplicate detection or handling.
    """

    name = "duplicate_item_id"
    target_test_key = "duplicate_item_ids"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)

        # Duplicate POP-015 with a different amount and description
        rows.append(
            {
                "Item ID": "POP-015",
                "Recorded Amount": 1245.67,
                "Description": "Duplicate entry - postage mailing second batch",
            }
        )

        record = AnomalyRecord(
            anomaly_type="duplicate_item_id",
            report_targets=["SAMP-04"],
            injected_at="Duplicate Item ID POP-015 (original=$890.25, duplicate=$1,245.67)",
            expected_field="duplicate_item_ids",
            expected_condition="items_count > 0",
            metadata={
                "item_id": "POP-015",
                "original_amount": 890.25,
                "duplicate_amount": 1245.67,
            },
        )
        return rows, [record]


class ExtremeOutlierGenerator(SamplingGeneratorBase):
    """Inject an amount approximately 100x the population mean.

    Adds an item with an extreme value relative to the population,
    testing the engine's outlier handling in stratification.
    """

    name = "extreme_outlier"
    target_test_key = "extreme_outliers"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)

        # Population mean is ~$10,000; inject ~$1,000,000
        rows.append(
            {
                "Item ID": "POP-OUT",
                "Recorded Amount": 987654.32,
                "Description": "Land acquisition - adjacent parcel for expansion",
            }
        )

        record = AnomalyRecord(
            anomaly_type="extreme_outlier",
            report_targets=["SAMP-05"],
            injected_at="Item POP-OUT with $987,654.32 (~100x population mean)",
            expected_field="extreme_outliers",
            expected_condition="items_count > 0",
            metadata={"item_id": "POP-OUT", "amount": 987654.32},
        )
        return rows, [record]


SAMPLING_REGISTRY: list[SamplingGeneratorBase] = [
    HighValueItemGenerator(),
    ZeroAmountItemGenerator(),
    NegativeAmountItemGenerator(),
    DuplicateItemIdGenerator(),
    ExtremeOutlierGenerator(),
]
