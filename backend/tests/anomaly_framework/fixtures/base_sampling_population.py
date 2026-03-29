"""Base sampling population factory for anomaly testing.

Produces a valid population of 50 items with realistic amounts suitable for
statistical sampling by the sampling engine. Uses Meridian Capital Group
naming conventions with sequential Item IDs and realistic descriptions.

Key design decisions:
- 50 items with amounts ranging $100-$50,000 (realistic business transactions)
- No zero or negative amounts
- No duplicate Item IDs
- Amounts follow a roughly log-normal distribution (many small, fewer large)
- All items have meaningful descriptions
- Population total is approximately $500,000
"""

import io

import pandas as pd

# fmt: off
_ITEMS: list[dict] = [
    {"Item ID": "POP-001", "Recorded Amount": 1234.56,   "Description": "Office supplies - Q2 replenishment"},
    {"Item ID": "POP-002", "Recorded Amount": 8923.45,   "Description": "IT equipment maintenance contract"},
    {"Item ID": "POP-003", "Recorded Amount": 345.00,    "Description": "Staff parking permits - June"},
    {"Item ID": "POP-004", "Recorded Amount": 15678.90,  "Description": "Consulting services - Baker & Associates"},
    {"Item ID": "POP-005", "Recorded Amount": 2341.78,   "Description": "Janitorial services - monthly"},
    {"Item ID": "POP-006", "Recorded Amount": 567.25,    "Description": "Courier and delivery charges"},
    {"Item ID": "POP-007", "Recorded Amount": 42315.00,  "Description": "Server hardware upgrade - data center"},
    {"Item ID": "POP-008", "Recorded Amount": 1890.33,   "Description": "Employee training workshop"},
    {"Item ID": "POP-009", "Recorded Amount": 12456.00,  "Description": "Annual software license renewal"},
    {"Item ID": "POP-010", "Recorded Amount": 789.50,    "Description": "Printing and reproduction services"},
    {"Item ID": "POP-011", "Recorded Amount": 6723.15,   "Description": "Marketing collateral design"},
    {"Item ID": "POP-012", "Recorded Amount": 3456.78,   "Description": "Telecommunications - monthly"},
    {"Item ID": "POP-013", "Recorded Amount": 28934.00,  "Description": "Facility renovation - conference room"},
    {"Item ID": "POP-014", "Recorded Amount": 1567.89,   "Description": "Safety equipment inspection"},
    {"Item ID": "POP-015", "Recorded Amount": 890.25,    "Description": "Postage and mailing expenses"},
    {"Item ID": "POP-016", "Recorded Amount": 19875.50,  "Description": "Legal retainer - quarterly payment"},
    {"Item ID": "POP-017", "Recorded Amount": 4523.00,   "Description": "Vehicle fleet maintenance"},
    {"Item ID": "POP-018", "Recorded Amount": 234.15,    "Description": "Breakroom supplies"},
    {"Item ID": "POP-019", "Recorded Amount": 37812.75,  "Description": "HVAC system replacement - Building B"},
    {"Item ID": "POP-020", "Recorded Amount": 2178.60,   "Description": "External audit preparation fees"},
    {"Item ID": "POP-021", "Recorded Amount": 5643.22,   "Description": "Warehouse packing materials"},
    {"Item ID": "POP-022", "Recorded Amount": 11234.00,  "Description": "Insurance premium - general liability"},
    {"Item ID": "POP-023", "Recorded Amount": 678.90,    "Description": "Subscription services - trade journals"},
    {"Item ID": "POP-024", "Recorded Amount": 3212.45,   "Description": "Equipment calibration services"},
    {"Item ID": "POP-025", "Recorded Amount": 45123.00,  "Description": "Capital equipment - CNC machine down payment"},
    {"Item ID": "POP-026", "Recorded Amount": 1456.78,   "Description": "Water and sewer utility"},
    {"Item ID": "POP-027", "Recorded Amount": 8765.43,   "Description": "Temporary staffing services"},
    {"Item ID": "POP-028", "Recorded Amount": 2567.90,   "Description": "Lab testing and analysis"},
    {"Item ID": "POP-029", "Recorded Amount": 456.00,    "Description": "Uniform cleaning service"},
    {"Item ID": "POP-030", "Recorded Amount": 14523.67,  "Description": "Advertising - regional print campaign"},
    {"Item ID": "POP-031", "Recorded Amount": 987.34,    "Description": "Fire extinguisher inspection"},
    {"Item ID": "POP-032", "Recorded Amount": 6234.50,   "Description": "Professional development courses"},
    {"Item ID": "POP-033", "Recorded Amount": 3789.12,   "Description": "Raw materials - aluminum stock"},
    {"Item ID": "POP-034", "Recorded Amount": 21345.00,  "Description": "ERP system module upgrade"},
    {"Item ID": "POP-035", "Recorded Amount": 1123.45,   "Description": "Pest control services - quarterly"},
    {"Item ID": "POP-036", "Recorded Amount": 7891.23,   "Description": "Travel expenses - client site visit"},
    {"Item ID": "POP-037", "Recorded Amount": 345.67,    "Description": "Office chair repairs"},
    {"Item ID": "POP-038", "Recorded Amount": 18234.56,  "Description": "Engineering consultancy - bridge project"},
    {"Item ID": "POP-039", "Recorded Amount": 2345.00,   "Description": "Catering - annual company meeting"},
    {"Item ID": "POP-040", "Recorded Amount": 9876.54,   "Description": "Security monitoring - monthly"},
    {"Item ID": "POP-041", "Recorded Amount": 4567.89,   "Description": "Electrical maintenance"},
    {"Item ID": "POP-042", "Recorded Amount": 567.12,    "Description": "First aid kit replenishment"},
    {"Item ID": "POP-043", "Recorded Amount": 32145.00,  "Description": "Roof repair - warehouse"},
    {"Item ID": "POP-044", "Recorded Amount": 1789.34,   "Description": "Grounds maintenance - landscaping"},
    {"Item ID": "POP-045", "Recorded Amount": 5432.10,   "Description": "Network cabling installation"},
    {"Item ID": "POP-046", "Recorded Amount": 890.00,    "Description": "Window cleaning service"},
    {"Item ID": "POP-047", "Recorded Amount": 13245.78,  "Description": "Forklift rental - peak season"},
    {"Item ID": "POP-048", "Recorded Amount": 2678.90,   "Description": "Quality control testing"},
    {"Item ID": "POP-049", "Recorded Amount": 7654.32,   "Description": "Freight and shipping - outbound"},
    {"Item ID": "POP-050", "Recorded Amount": 3456.12,   "Description": "Plumbing repairs - factory floor"},
]
# fmt: on


def _verify_population(items: list[dict]) -> None:
    """Raise if population has duplicates, zero/negative amounts, or other issues."""
    ids = [r["Item ID"] for r in items]
    assert len(ids) == len(set(ids)), "Duplicate Item IDs found"
    for r in items:
        assert r["Recorded Amount"] > 0, f"Non-positive amount for {r['Item ID']}: {r['Recorded Amount']}"


# Validate at import time
_verify_population(_ITEMS)


class BaseSamplingPopulationFactory:
    """Factory for a clean, valid sampling population."""

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return population items as list of dicts."""
        return [dict(r) for r in _ITEMS]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names for population data."""
        return list(_ITEMS[0].keys())

    @classmethod
    def as_csv_bytes(cls) -> bytes:
        """Return population as CSV bytes suitable for design_sample."""
        df = pd.DataFrame(_ITEMS)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
