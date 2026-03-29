"""Fixed Asset Testing anomaly generators — 10 detectors.

Each generator injects a specific anomaly pattern into clean fixed asset
data and returns an AnomalyRecord describing the expected detection.

Generators that require large populations (statistical outlier tests) are
marked with `requires_large_population = True` and are excluded from the
small registry.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class FAGeneratorBase:
    """Base class for Fixed Asset anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject(self, rows: list[dict], seed: int = 42) -> tuple[list[dict], list[AnomalyRecord]]:
        """Inject anomaly into fixed asset rows.

        Returns:
            Tuple of (mutated_rows, anomaly_records).
        """
        raise NotImplementedError


class FAFullyDepreciatedGenerator(FAGeneratorBase):
    """FA-01: Inject a fully depreciated asset (accum_dep == cost)."""

    name = "fa_fully_depreciated"
    target_test_key = "fully_depreciated"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-099",
                "Description": "Obsolete Printer (fully depreciated)",
                "Cost": 5000.00,
                "Accumulated Depreciation": 5000.00,
                "Residual Value": 0.00,
                "Useful Life Years": 5,
                "Acquisition Date": "2019-01-15",
                "Depreciation Method": "Straight-Line",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_fully_depreciated",
            report_targets=["FA-01"],
            injected_at="Asset FA-099 with accum_dep == cost ($5,000)",
            expected_field="fully_depreciated",
            expected_condition="entries_flagged > 0",
            metadata={"cost": 5000.00, "accumulated_depreciation": 5000.00},
        )
        return rows, [record]


class FAMissingFieldsGenerator(FAGeneratorBase):
    """FA-02: Inject an asset with missing required fields."""

    name = "fa_missing_fields"
    target_test_key = "missing_fields"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-098",
                "Description": "",
                "Cost": 7500.00,
                "Accumulated Depreciation": 1500.00,
                "Residual Value": "",
                "Useful Life Years": "",
                "Acquisition Date": "",
                "Depreciation Method": "",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_missing_fields",
            report_targets=["FA-02"],
            injected_at="Asset FA-098 with blank Description, Residual Value, Useful Life, "
            "Acquisition Date, and Depreciation Method",
            expected_field="missing_fields",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class FANegativeValuesGenerator(FAGeneratorBase):
    """FA-03: Inject assets with negative cost or accumulated depreciation."""

    name = "fa_negative_values"
    target_test_key = "negative_values"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-097",
                "Description": "Negative Cost Equipment",
                "Cost": -12000.00,
                "Accumulated Depreciation": 3000.00,
                "Residual Value": 1200.00,
                "Useful Life Years": 5,
                "Acquisition Date": "2023-06-15",
                "Depreciation Method": "Straight-Line",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_negative_values",
            report_targets=["FA-03"],
            injected_at="Asset FA-097 with negative cost -$12,000",
            expected_field="negative_values",
            expected_condition="entries_flagged > 0",
            metadata={"cost": -12000.00},
        )
        return rows, [record]


class FAOverDepreciationGenerator(FAGeneratorBase):
    """FA-04: Inject asset where accum_dep > cost - residual."""

    name = "fa_over_depreciation"
    target_test_key = "over_depreciation"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-096",
                "Description": "Over-Depreciated Forklift",
                "Cost": 25000.00,
                "Accumulated Depreciation": 28000.00,
                "Residual Value": 2500.00,
                "Useful Life Years": 7,
                "Acquisition Date": "2018-04-01",
                "Depreciation Method": "Straight-Line",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_over_depreciation",
            report_targets=["FA-04"],
            injected_at="Asset FA-096 with accum_dep $28,000 > depreciable $22,500",
            expected_field="over_depreciation",
            expected_condition="entries_flagged > 0",
            metadata={
                "cost": 25000.00,
                "accumulated_depreciation": 28000.00,
                "residual_value": 2500.00,
                "depreciable": 22500.00,
            },
        )
        return rows, [record]


class FAUsefulLifeOutliersGenerator(FAGeneratorBase):
    """FA-05: Inject asset with extreme useful life (100 years)."""

    name = "fa_useful_life_outliers"
    target_test_key = "useful_life_outliers"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-095",
                "Description": "Land Improvement - Parking Lot",
                "Cost": 45000.00,
                "Accumulated Depreciation": 450.00,
                "Residual Value": 4500.00,
                "Useful Life Years": 100,
                "Acquisition Date": "2024-01-01",
                "Depreciation Method": "Straight-Line",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_useful_life_outliers",
            report_targets=["FA-05"],
            injected_at="Asset FA-095 with 100-year useful life (z-score outlier)",
            expected_field="useful_life_outliers",
            expected_condition="entries_flagged > 0",
            metadata={"useful_life_years": 100},
        )
        return rows, [record]


class FACostZScoreOutliersGenerator(FAGeneratorBase):
    """FA-06: Inject asset with very high cost (z-score outlier)."""

    name = "fa_cost_zscore_outliers"
    target_test_key = "cost_zscore_outliers"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-094",
                "Description": "Custom Manufacturing Plant Wing",
                "Cost": 5000000.00,
                "Accumulated Depreciation": 250000.00,
                "Residual Value": 500000.00,
                "Useful Life Years": 30,
                "Acquisition Date": "2024-03-01",
                "Depreciation Method": "Straight-Line",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_cost_zscore_outliers",
            report_targets=["FA-06"],
            injected_at="Asset FA-094 with $5,000,000 cost (extreme z-score outlier)",
            expected_field="cost_zscore_outliers",
            expected_condition="entries_flagged > 0",
            metadata={"cost": 5000000.00},
        )
        return rows, [record]


class FAAgeConcentrationGenerator(FAGeneratorBase):
    """FA-07: All assets acquired in the same year."""

    name = "fa_age_concentration"
    target_test_key = "age_concentration"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Move all acquisition dates to 2023
        for row in rows:
            # Preserve month/day, change year to 2023
            orig_date = row["Acquisition Date"]
            row["Acquisition Date"] = "2023" + orig_date[4:]
        record = AnomalyRecord(
            anomaly_type="fa_age_concentration",
            report_targets=["FA-07"],
            injected_at="All 14 assets moved to 2023 acquisition year (100% concentration)",
            expected_field="age_concentration",
            expected_condition="entries_flagged > 0",
            metadata={"year": 2023, "concentration_pct": 1.0},
        )
        return rows, [record]


class FADuplicateAssetsGenerator(FAGeneratorBase):
    """FA-08: Inject duplicate Asset IDs."""

    name = "fa_duplicate_assets"
    target_test_key = "duplicate_assets"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Duplicate an existing asset with same ID
        dup = dict(rows[0])
        dup["Description"] = "Duplicate of " + dup["Description"]
        rows.append(dup)
        record = AnomalyRecord(
            anomaly_type="fa_duplicate_assets",
            report_targets=["FA-08"],
            injected_at=f"Duplicated asset {rows[0]['Asset ID']}",
            expected_field="duplicate_assets",
            expected_condition="entries_flagged > 0",
            metadata={"duplicated_id": rows[0]["Asset ID"]},
        )
        return rows, [record]


class FAResidualValueAnomaliesGenerator(FAGeneratorBase):
    """FA-09: Inject asset where residual value > cost."""

    name = "fa_residual_value_anomalies"
    target_test_key = "residual_value_anomalies"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Asset ID": "FA-093",
                "Description": "Misvalued Office Equipment",
                "Cost": 8000.00,
                "Accumulated Depreciation": 0.00,
                "Residual Value": 12000.00,
                "Useful Life Years": 5,
                "Acquisition Date": "2024-06-01",
                "Depreciation Method": "Straight-Line",
            }
        )
        record = AnomalyRecord(
            anomaly_type="fa_residual_value_anomalies",
            report_targets=["FA-09"],
            injected_at="Asset FA-093 with residual $12,000 > cost $8,000",
            expected_field="residual_value_anomalies",
            expected_condition="entries_flagged > 0",
            metadata={"cost": 8000.00, "residual_value": 12000.00},
        )
        return rows, [record]


# =============================================================================
# Registry of all FA generators
# =============================================================================

FA_REGISTRY: list[FAGeneratorBase] = [
    FAFullyDepreciatedGenerator(),
    FAMissingFieldsGenerator(),
    FANegativeValuesGenerator(),
    FAOverDepreciationGenerator(),
    FAUsefulLifeOutliersGenerator(),
    FACostZScoreOutliersGenerator(),
    FAAgeConcentrationGenerator(),
    FADuplicateAssetsGenerator(),
    FAResidualValueAnomaliesGenerator(),
]

# Small-population-safe generators (work with 14-asset baseline)
FA_REGISTRY_SMALL = [g for g in FA_REGISTRY if not g.requires_large_population]
