"""Base inventory factory for anomaly testing.

Produces a valid, clean set of 15 inventory records that trigger zero flags
in the Inventory testing engine. Uses Meridian Capital Group naming
conventions.

Key design decisions:
- Extended Value == Unit Cost * Quantity for all items (avoids IN-03)
- No negative values in any numeric field (avoids IN-02)
- No zero-value items (avoids IN-09)
- No duplicate Item IDs (avoids IN-08)
- Reasonable unit costs $5-$500 (avoids IN-04 outliers)
- Last Transaction within 6 months (avoids IN-06 slow-moving)
- Multiple categories, no single category >60% of value (avoids IN-07)
- No blank required fields (avoids IN-01)
"""

import io

import pandas as pd

# fmt: off
_ITEMS: list[dict] = [
    # Raw Materials
    {"Item ID": "INV-001", "Description": "Steel Sheet Stock 4x8",            "Category": "Raw Materials",    "Unit Cost": 125.50,  "Quantity": 80,   "Extended Value": 10040.00,  "Last Transaction Date": "2025-05-28"},
    {"Item ID": "INV-002", "Description": "Aluminum Rod 1-inch Diameter",     "Category": "Raw Materials",    "Unit Cost": 42.75,   "Quantity": 200,  "Extended Value": 8550.00,   "Last Transaction Date": "2025-06-01"},
    {"Item ID": "INV-003", "Description": "Copper Wire Spool 12-gauge",       "Category": "Raw Materials",    "Unit Cost": 87.30,   "Quantity": 50,   "Extended Value": 4365.00,   "Last Transaction Date": "2025-05-15"},
    # Work in Progress
    {"Item ID": "INV-004", "Description": "Subassembly A - Motor Housing",    "Category": "Work in Progress", "Unit Cost": 234.00,  "Quantity": 25,   "Extended Value": 5850.00,   "Last Transaction Date": "2025-06-05"},
    {"Item ID": "INV-005", "Description": "Subassembly B - Control Panel",    "Category": "Work in Progress", "Unit Cost": 312.50,  "Quantity": 15,   "Extended Value": 4687.50,   "Last Transaction Date": "2025-05-22"},
    {"Item ID": "INV-006", "Description": "Wiring Harness Kit WH-200",        "Category": "Work in Progress", "Unit Cost": 78.25,   "Quantity": 40,   "Extended Value": 3130.00,   "Last Transaction Date": "2025-06-02"},
    # Finished Goods
    {"Item ID": "INV-007", "Description": "Motor Assembly Model MA-500",      "Category": "Finished Goods",   "Unit Cost": 489.00,  "Quantity": 12,   "Extended Value": 5868.00,   "Last Transaction Date": "2025-06-10"},
    {"Item ID": "INV-008", "Description": "Control Unit CU-300",              "Category": "Finished Goods",   "Unit Cost": 375.00,  "Quantity": 18,   "Extended Value": 6750.00,   "Last Transaction Date": "2025-05-30"},
    {"Item ID": "INV-009", "Description": "Power Supply Unit PS-150",         "Category": "Finished Goods",   "Unit Cost": 145.75,  "Quantity": 35,   "Extended Value": 5101.25,   "Last Transaction Date": "2025-06-08"},
    # Office & Maintenance Supplies
    {"Item ID": "INV-010", "Description": "Printer Toner Cartridge HP-55A",   "Category": "Supplies",         "Unit Cost": 68.50,   "Quantity": 24,   "Extended Value": 1644.00,   "Last Transaction Date": "2025-06-12"},
    {"Item ID": "INV-011", "Description": "Safety Gloves Industrial Grade",   "Category": "Supplies",         "Unit Cost": 12.75,   "Quantity": 150,  "Extended Value": 1912.50,   "Last Transaction Date": "2025-05-18"},
    {"Item ID": "INV-012", "Description": "Lubricant Oil 5-Gallon Drum",      "Category": "Supplies",         "Unit Cost": 45.00,   "Quantity": 20,   "Extended Value": 900.00,    "Last Transaction Date": "2025-06-03"},
    # Packaging
    {"Item ID": "INV-013", "Description": "Shipping Cartons 24x18x12",        "Category": "Packaging",        "Unit Cost": 5.25,    "Quantity": 500,  "Extended Value": 2625.00,   "Last Transaction Date": "2025-06-07"},
    {"Item ID": "INV-014", "Description": "Bubble Wrap Roll 12-inch",         "Category": "Packaging",        "Unit Cost": 18.90,   "Quantity": 60,   "Extended Value": 1134.00,   "Last Transaction Date": "2025-05-25"},
    {"Item ID": "INV-015", "Description": "Pallet Stretch Wrap 18-inch",      "Category": "Packaging",        "Unit Cost": 32.50,   "Quantity": 30,   "Extended Value": 975.00,    "Last Transaction Date": "2025-06-04"},
]
# fmt: on


def _verify_extended_values(items: list[dict]) -> None:
    """Raise if extended_value != unit_cost * quantity."""
    for item in items:
        expected = item["Unit Cost"] * item["Quantity"]
        assert abs(item["Extended Value"] - expected) < 0.01, (
            f"Item {item['Item ID']} extended value mismatch: "
            f"{item['Extended Value']} != {item['Unit Cost']} * {item['Quantity']} = {expected}"
        )


def _verify_no_negatives(items: list[dict]) -> None:
    """Raise if any numeric field is negative."""
    for item in items:
        for field in ("Unit Cost", "Quantity", "Extended Value"):
            assert item[field] >= 0, f"Negative {field} in {item['Item ID']}: {item[field]}"


def _verify_no_zero_values(items: list[dict]) -> None:
    """Raise if any item has zero extended value with positive quantity."""
    for item in items:
        if item["Quantity"] > 0:
            assert item["Extended Value"] > 0, (
                f"Item {item['Item ID']} has quantity {item['Quantity']} but zero extended value"
            )


def _verify_no_duplicates(items: list[dict]) -> None:
    """Raise if any Item IDs are duplicated."""
    ids = [i["Item ID"] for i in items]
    assert len(ids) == len(set(ids)), "Duplicate Item IDs found"


def _verify_no_blanks(items: list[dict]) -> None:
    """Raise if any required field is blank."""
    for item in items:
        for field in ("Item ID", "Description", "Category", "Last Transaction Date"):
            assert item[field] != "", f"Blank {field} in {item['Item ID']}"


def _verify_category_distribution(items: list[dict]) -> None:
    """Raise if any category > 60% of total value."""
    total = sum(i["Extended Value"] for i in items)
    from collections import defaultdict

    by_cat: dict[str, float] = defaultdict(float)
    for i in items:
        by_cat[i["Category"]] += i["Extended Value"]
    for cat, val in by_cat.items():
        pct = val / total
        assert pct <= 0.60, f"Category '{cat}' has {pct:.1%} concentration (>60%)"


# Validate at import time
_verify_extended_values(_ITEMS)
_verify_no_negatives(_ITEMS)
_verify_no_zero_values(_ITEMS)
_verify_no_duplicates(_ITEMS)
_verify_no_blanks(_ITEMS)
_verify_category_distribution(_ITEMS)


class BaseInventoryFactory:
    """Factory for clean, flag-free inventory test data."""

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return the base items as a list of dicts."""
        return [dict(i) for i in _ITEMS]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names matching the item dicts."""
        return list(_ITEMS[0].keys())

    @classmethod
    def as_dataframe(cls) -> pd.DataFrame:
        """Return the base items as a pandas DataFrame."""
        return pd.DataFrame(_ITEMS)

    @classmethod
    def as_csv_bytes(cls) -> bytes:
        """Return the base items as CSV bytes."""
        df = cls.as_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
