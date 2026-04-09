"""Base fixed asset factory for anomaly testing.

Produces a valid, clean set of 14 fixed asset records that trigger zero flags
in the Fixed Asset testing engine. Uses Meridian Capital Group naming
conventions.

Key design decisions:
- No fully depreciated assets (accum_dep < cost - residual for all)
- No over-depreciation (accum_dep <= cost - residual for all)
- No negative values in any numeric field
- No duplicate Asset IDs
- Useful lives between 3 and 40 years (no outliers)
- Acquisition dates spread over 5 years (2020-2025)
- Mix of Straight-Line and Declining Balance methods
- No single year has >50% of assets (avoids age concentration)
- Residual values < cost for all assets
"""

import io

import pandas as pd

# fmt: off
_ASSETS: list[dict] = [
    # Office furniture & fixtures
    {"Asset ID": "FA-001", "Description": "Executive Office Furniture Set",         "Cost": 12500.00,  "Accumulated Depreciation": 5000.00,   "Residual Value": 1250.00,  "Useful Life Years": 10, "Acquisition Date": "2021-03-15", "Depreciation Method": "Straight-Line"},
    {"Asset ID": "FA-002", "Description": "Conference Room Table & Chairs",         "Cost": 8750.00,   "Accumulated Depreciation": 2625.00,   "Residual Value": 875.00,   "Useful Life Years": 10, "Acquisition Date": "2022-06-01", "Depreciation Method": "Straight-Line"},
    {"Asset ID": "FA-003", "Description": "Reception Area Furnishings",             "Cost": 6200.00,   "Accumulated Depreciation": 1240.00,   "Residual Value": 620.00,   "Useful Life Years": 10, "Acquisition Date": "2023-01-10", "Depreciation Method": "Straight-Line"},
    # IT equipment
    {"Asset ID": "FA-004", "Description": "Dell PowerEdge Server Rack",             "Cost": 28750.00,  "Accumulated Depreciation": 14375.00,  "Residual Value": 2875.00,  "Useful Life Years": 5,  "Acquisition Date": "2022-09-20", "Depreciation Method": "Declining Balance"},
    {"Asset ID": "FA-005", "Description": "Cisco Network Infrastructure",           "Cost": 18500.00,  "Accumulated Depreciation": 5550.00,   "Residual Value": 1850.00,  "Useful Life Years": 7,  "Acquisition Date": "2023-04-12", "Depreciation Method": "Declining Balance"},
    {"Asset ID": "FA-006", "Description": "Employee Laptop Fleet (25 units)",       "Cost": 37500.00,  "Accumulated Depreciation": 25000.00,  "Residual Value": 3750.00,  "Useful Life Years": 3,  "Acquisition Date": "2023-07-01", "Depreciation Method": "Straight-Line"},
    # Vehicles
    {"Asset ID": "FA-007", "Description": "Ford Transit Cargo Van",                 "Cost": 42300.00,  "Accumulated Depreciation": 16920.00,  "Residual Value": 8460.00,  "Useful Life Years": 7,  "Acquisition Date": "2022-01-15", "Depreciation Method": "Straight-Line"},
    {"Asset ID": "FA-008", "Description": "Toyota Camry Company Sedan",             "Cost": 32150.00,  "Accumulated Depreciation": 6430.00,   "Residual Value": 6430.00,  "Useful Life Years": 5,  "Acquisition Date": "2024-02-28", "Depreciation Method": "Declining Balance"},
    # Building improvements
    {"Asset ID": "FA-009", "Description": "Office Renovation - 3rd Floor",          "Cost": 85000.00,  "Accumulated Depreciation": 11333.00,  "Residual Value": 0.00,     "Useful Life Years": 15, "Acquisition Date": "2023-11-01", "Depreciation Method": "Straight-Line"},
    {"Asset ID": "FA-010", "Description": "HVAC System Replacement",                "Cost": 64500.00,  "Accumulated Depreciation": 3225.00,   "Residual Value": 6450.00,  "Useful Life Years": 20, "Acquisition Date": "2024-05-15", "Depreciation Method": "Straight-Line"},
    # Manufacturing / specialized
    {"Asset ID": "FA-011", "Description": "CNC Milling Machine",                    "Cost": 125000.00, "Accumulated Depreciation": 50000.00,  "Residual Value": 12500.00, "Useful Life Years": 10, "Acquisition Date": "2020-08-20", "Depreciation Method": "Straight-Line"},
    {"Asset ID": "FA-012", "Description": "Industrial Packaging System",            "Cost": 45800.00,  "Accumulated Depreciation": 13740.00,  "Residual Value": 4580.00,  "Useful Life Years": 8,  "Acquisition Date": "2022-03-01", "Depreciation Method": "Declining Balance"},
    # Recent acquisitions
    {"Asset ID": "FA-013", "Description": "Security Camera System",                 "Cost": 15200.00,  "Accumulated Depreciation": 1520.00,   "Residual Value": 1520.00,  "Useful Life Years": 5,  "Acquisition Date": "2024-10-01", "Depreciation Method": "Straight-Line"},
    {"Asset ID": "FA-014", "Description": "Warehouse Pallet Racking System",        "Cost": 22000.00,  "Accumulated Depreciation": 1100.00,   "Residual Value": 2200.00,  "Useful Life Years": 20, "Acquisition Date": "2025-01-15", "Depreciation Method": "Straight-Line"},
]
# fmt: on


def _verify_no_full_depreciation(assets: list[dict]) -> None:
    """Raise if any asset is fully depreciated."""
    for a in assets:
        depreciable = a["Cost"] - a["Residual Value"]
        assert a["Accumulated Depreciation"] < depreciable, (
            f"Asset {a['Asset ID']} is fully depreciated: "
            f"accum={a['Accumulated Depreciation']}, depreciable={depreciable}"
        )


def _verify_no_over_depreciation(assets: list[dict]) -> None:
    """Raise if accum_dep > cost - residual."""
    for a in assets:
        depreciable = a["Cost"] - a["Residual Value"]
        assert a["Accumulated Depreciation"] <= depreciable, (
            f"Asset {a['Asset ID']} is over-depreciated: "
            f"accum={a['Accumulated Depreciation']}, depreciable={depreciable}"
        )


def _verify_no_negatives(assets: list[dict]) -> None:
    """Raise if any numeric field is negative."""
    for a in assets:
        for field in ("Cost", "Accumulated Depreciation", "Residual Value", "Useful Life Years"):
            assert a[field] >= 0, f"Negative {field} in {a['Asset ID']}: {a[field]}"


def _verify_no_duplicates(assets: list[dict]) -> None:
    """Raise if any Asset IDs are duplicated."""
    ids = [a["Asset ID"] for a in assets]
    assert len(ids) == len(set(ids)), "Duplicate Asset IDs found"


def _verify_useful_life_range(assets: list[dict]) -> None:
    """Raise if any useful life is outside 3-40 years."""
    for a in assets:
        assert 3 <= a["Useful Life Years"] <= 40, (
            f"Asset {a['Asset ID']} useful life {a['Useful Life Years']} outside 3-40 range"
        )


def _verify_residual_below_cost(assets: list[dict]) -> None:
    """Raise if any residual value >= cost."""
    for a in assets:
        assert a["Residual Value"] < a["Cost"], (
            f"Asset {a['Asset ID']} residual ({a['Residual Value']}) >= cost ({a['Cost']})"
        )


# Validate at import time
_verify_no_full_depreciation(_ASSETS)
_verify_no_over_depreciation(_ASSETS)
_verify_no_negatives(_ASSETS)
_verify_no_duplicates(_ASSETS)
_verify_useful_life_range(_ASSETS)
_verify_residual_below_cost(_ASSETS)


class BaseFixedAssetFactory:
    """Factory for clean, flag-free fixed asset test data."""

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return the base assets as a list of dicts."""
        return [dict(a) for a in _ASSETS]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names matching the asset dicts."""
        return list(_ASSETS[0].keys())

    @classmethod
    def as_dataframe(cls) -> pd.DataFrame:
        """Return the base assets as a pandas DataFrame."""
        return pd.DataFrame(_ASSETS)

    @classmethod
    def as_csv_bytes(cls) -> bytes:
        """Return the base assets as CSV bytes."""
        df = cls.as_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
