"""Inventory Testing anomaly generators — 9 detectors.

Each generator injects a specific anomaly pattern into clean inventory
data and returns an AnomalyRecord describing the expected detection.

Generators that require large populations (statistical outlier tests) are
marked with `requires_large_population = True` and are excluded from the
small registry.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class INVGeneratorBase:
    """Base class for Inventory anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject(self, rows: list[dict], seed: int = 42) -> tuple[list[dict], list[AnomalyRecord]]:
        """Inject anomaly into inventory rows.

        Returns:
            Tuple of (mutated_rows, anomaly_records).
        """
        raise NotImplementedError


class INVMissingFieldsGenerator(INVGeneratorBase):
    """IN-01: Inject an item with blank required fields."""

    name = "inv_missing_fields"
    target_test_key = "missing_fields"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-099",
                "Description": "",
                "Category": "",
                "Unit Cost": 50.00,
                "Quantity": 10,
                "Extended Value": 500.00,
                "Last Transaction Date": "",
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_missing_fields",
            report_targets=["IN-01"],
            injected_at="Item INV-099 with blank Description, Category, and Last Transaction Date",
            expected_field="missing_fields",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class INVNegativeValuesGenerator(INVGeneratorBase):
    """IN-02: Inject an item with negative quantity or cost."""

    name = "inv_negative_values"
    target_test_key = "negative_values"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-098",
                "Description": "Negative Quantity Item",
                "Category": "Raw Materials",
                "Unit Cost": 75.00,
                "Quantity": -25,
                "Extended Value": -1875.00,
                "Last Transaction Date": "2025-05-20",
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_negative_values",
            report_targets=["IN-02"],
            injected_at="Item INV-098 with quantity -25",
            expected_field="negative_values",
            expected_condition="entries_flagged > 0",
            metadata={"quantity": -25, "unit_cost": 75.00},
        )
        return rows, [record]


class INVExtendedValueMismatchGenerator(INVGeneratorBase):
    """IN-03: Inject item where extended_value != unit_cost * quantity."""

    name = "inv_extended_value_mismatch"
    target_test_key = "value_mismatch"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-097",
                "Description": "Mismatched Extension Item",
                "Category": "Finished Goods",
                "Unit Cost": 150.00,
                "Quantity": 20,
                "Extended Value": 4500.00,  # Should be 3000.00
                "Last Transaction Date": "2025-06-01",
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_extended_value_mismatch",
            report_targets=["IN-03"],
            injected_at="Item INV-097: extended $4,500 != $150 * 20 = $3,000",
            expected_field="value_mismatch",
            expected_condition="entries_flagged > 0",
            metadata={"unit_cost": 150.00, "quantity": 20, "extended_value": 4500.00, "expected": 3000.00},
        )
        return rows, [record]


class INVUnitCostOutliersGenerator(INVGeneratorBase):
    """IN-04: Inject item with very high unit cost (z-score outlier)."""

    name = "inv_unit_cost_outliers"
    target_test_key = "unit_cost_outliers"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-096",
                "Description": "Premium Custom Component XR-9000",
                "Category": "Finished Goods",
                "Unit Cost": 25000.00,
                "Quantity": 3,
                "Extended Value": 75000.00,
                "Last Transaction Date": "2025-06-05",
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_unit_cost_outliers",
            report_targets=["IN-04"],
            injected_at="Item INV-096 with $25,000 unit cost (extreme z-score outlier)",
            expected_field="unit_cost_outliers",
            expected_condition="entries_flagged > 0",
            metadata={"unit_cost": 25000.00},
        )
        return rows, [record]


class INVQuantityOutliersGenerator(INVGeneratorBase):
    """IN-05: Inject item with very high quantity (z-score outlier)."""

    name = "inv_quantity_outliers"
    target_test_key = "quantity_outliers"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-095",
                "Description": "Standard Bolt M8x25mm",
                "Category": "Raw Materials",
                "Unit Cost": 0.15,
                "Quantity": 500000,
                "Extended Value": 75000.00,
                "Last Transaction Date": "2025-05-10",
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_quantity_outliers",
            report_targets=["IN-05"],
            injected_at="Item INV-095 with quantity 500,000 (extreme z-score outlier)",
            expected_field="quantity_outliers",
            expected_condition="entries_flagged > 0",
            metadata={"quantity": 500000},
        )
        return rows, [record]


class INVSlowMovingGenerator(INVGeneratorBase):
    """IN-06: Inject item with last transaction > 12 months ago."""

    name = "inv_slow_moving"
    target_test_key = "slow_moving"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-094",
                "Description": "Obsolete Widget Model W-100",
                "Category": "Finished Goods",
                "Unit Cost": 95.00,
                "Quantity": 45,
                "Extended Value": 4275.00,
                "Last Transaction Date": "2024-01-15",  # ~18 months old
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_slow_moving",
            report_targets=["IN-06"],
            injected_at="Item INV-094 with last transaction 2024-01-15 (~18 months ago)",
            expected_field="slow_moving",
            expected_condition="entries_flagged > 0",
            metadata={"last_transaction_date": "2024-01-15"},
        )
        return rows, [record]


class INVCategoryConcentrationGenerator(INVGeneratorBase):
    """IN-07: Concentrate >60% of inventory value in one category."""

    name = "inv_category_concentration"
    target_test_key = "category_concentration"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Move all items to a single category
        for row in rows:
            row["Category"] = "Raw Materials"
        record = AnomalyRecord(
            anomaly_type="inv_category_concentration",
            report_targets=["IN-07"],
            injected_at="All items moved to 'Raw Materials' category (100% concentration)",
            expected_field="category_concentration",
            expected_condition="entries_flagged > 0",
            metadata={"category": "Raw Materials", "concentration_pct": 1.0},
        )
        return rows, [record]


class INVDuplicateItemsGenerator(INVGeneratorBase):
    """IN-08: Inject duplicate Item IDs."""

    name = "inv_duplicate_items"
    target_test_key = "duplicate_items"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Duplicate an existing item with the same ID
        dup = dict(rows[0])
        dup["Description"] = "Duplicate of " + dup["Description"]
        rows.append(dup)
        record = AnomalyRecord(
            anomaly_type="inv_duplicate_items",
            report_targets=["IN-08"],
            injected_at=f"Duplicated item {rows[0]['Item ID']}",
            expected_field="duplicate_items",
            expected_condition="entries_flagged > 0",
            metadata={"duplicated_id": rows[0]["Item ID"]},
        )
        return rows, [record]


class INVZeroValueItemsGenerator(INVGeneratorBase):
    """IN-09: Inject item with quantity > 0 but extended value = 0."""

    name = "inv_zero_value_items"
    target_test_key = "zero_value_items"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Item ID": "INV-093",
                "Description": "Free Sample Promotional Item",
                "Category": "Finished Goods",
                "Unit Cost": 0.00,
                "Quantity": 100,
                "Extended Value": 0.00,
                "Last Transaction Date": "2025-06-01",
            }
        )
        record = AnomalyRecord(
            anomaly_type="inv_zero_value_items",
            report_targets=["IN-09"],
            injected_at="Item INV-093 with quantity 100 but $0 extended value",
            expected_field="zero_value_items",
            expected_condition="entries_flagged > 0",
            metadata={"quantity": 100, "extended_value": 0.00},
        )
        return rows, [record]


# =============================================================================
# Registry of all Inventory generators
# =============================================================================

INV_REGISTRY: list[INVGeneratorBase] = [
    INVMissingFieldsGenerator(),
    INVNegativeValuesGenerator(),
    INVExtendedValueMismatchGenerator(),
    INVUnitCostOutliersGenerator(),
    INVQuantityOutliersGenerator(),
    INVSlowMovingGenerator(),
    INVCategoryConcentrationGenerator(),
    INVDuplicateItemsGenerator(),
    INVZeroValueItemsGenerator(),
]

# Small-population-safe generators (work with 15-item baseline)
INV_REGISTRY_SMALL = [g for g in INV_REGISTRY if not g.requires_large_population]
