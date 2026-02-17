"""
Tests for shared/data_quality.py — Sprint 152

Tests the config-driven data quality assessment shared across
JE, AP, Revenue, FA, Inventory, and Payroll engines.
"""

from dataclasses import dataclass

from shared.data_quality import (
    FieldQualityConfig,
    assess_data_quality,
)


# Simple mock entry for testing
@dataclass
class MockEntry:
    name: str = ""
    amount: float = 0.0
    date: str = ""
    description: str = ""
    category: str = ""


def _make_entries(n: int, **overrides) -> list[MockEntry]:
    """Create n MockEntry objects with optional field overrides."""
    entries = []
    for i in range(n):
        kwargs = {}
        for k, v in overrides.items():
            if callable(v):
                kwargs[k] = v(i)
            else:
                kwargs[k] = v
        entries.append(MockEntry(**kwargs))
    return entries


# Standard field configs for testing
REQUIRED_CONFIGS = [
    FieldQualityConfig(
        field_name="name",
        accessor=lambda e: e.name,
        weight=0.30,
        issue_threshold=0.95,
        issue_template="Missing name on {unfilled} entries",
    ),
    FieldQualityConfig(
        field_name="amount",
        accessor=lambda e: e.amount != 0,
        weight=0.30,
        issue_threshold=0.90,
        issue_template="{unfilled} entries have zero amount",
    ),
    FieldQualityConfig(
        field_name="date",
        accessor=lambda e: e.date,
        weight=0.25,
        issue_threshold=0.95,
        issue_template="Missing date on {unfilled} entries",
    ),
]

OPTIONAL_CONFIGS = [
    FieldQualityConfig(
        field_name="description",
        accessor=lambda e: e.description,
        issue_threshold=0.80,
        issue_template="Low description fill rate: {fill_pct} ({unfilled} blank)",
    ),
    FieldQualityConfig(
        field_name="category",
        accessor=lambda e: e.category,
    ),
]


class TestAssessDataQuality:
    """Tests for the assess_data_quality function."""

    def test_empty_entries(self):
        """Empty list returns zero score."""
        result = assess_data_quality([], REQUIRED_CONFIGS)
        assert result.completeness_score == 0.0
        assert result.total_rows == 0
        assert result.field_fill_rates == {}
        assert result.detected_issues == []

    def test_perfect_fill_required_only(self):
        """All required fields filled, no optional configs."""
        entries = _make_entries(10, name="Alice", amount=100.0, date="2024-01-01")
        result = assess_data_quality(entries, REQUIRED_CONFIGS)

        # Required weights sum to 0.85, optional pool = 0.15 bonus
        # Score = (1.0*0.30 + 1.0*0.30 + 1.0*0.25) * 100 + 0.15*100 = 85 + 15 = 100
        assert result.completeness_score == 100.0
        assert result.total_rows == 10
        assert result.field_fill_rates["name"] == 1.0
        assert result.field_fill_rates["amount"] == 1.0
        assert result.field_fill_rates["date"] == 1.0
        assert result.detected_issues == []

    def test_perfect_fill_with_optionals(self):
        """All fields filled including optionals."""
        entries = _make_entries(
            10, name="Alice", amount=100.0, date="2024-01-01",
            description="Payment", category="Expense",
        )
        configs = REQUIRED_CONFIGS + OPTIONAL_CONFIGS
        result = assess_data_quality(entries, configs)

        # Required: 0.30+0.30+0.25 = 0.85. Optional pool: 0.15 / 2 = 0.075 each
        # Score = (0.30+0.30+0.25+0.075+0.075) * 100 = 100.0
        assert result.completeness_score == 100.0
        assert result.total_rows == 10
        assert len(result.detected_issues) == 0

    def test_partial_fill_required(self):
        """Partial fill on required fields reduces score."""
        entries = _make_entries(10, name=lambda i: "Alice" if i < 5 else "", amount=100.0, date="2024-01-01")
        result = assess_data_quality(entries, REQUIRED_CONFIGS)

        # name fill = 0.5, amount = 1.0, date = 1.0
        # Score = (0.5*0.30 + 1.0*0.30 + 1.0*0.25) * 100 + 15 = (0.15+0.30+0.25)*100+15 = 70+15 = 85
        assert result.completeness_score == 85.0
        assert result.field_fill_rates["name"] == 0.5
        # name at 0.5 < 0.95 threshold, so issue generated
        assert any("Missing name" in issue for issue in result.detected_issues)

    def test_issue_detection(self):
        """Fields below threshold generate issues with correct message."""
        entries = _make_entries(
            10, name="Alice", amount=100.0, date="2024-01-01",
            description=lambda i: "desc" if i < 7 else "",
        )
        configs = REQUIRED_CONFIGS + OPTIONAL_CONFIGS
        result = assess_data_quality(entries, configs)

        # description fill = 7/10 = 0.70 < 0.80 threshold
        assert any("Low description fill rate" in issue for issue in result.detected_issues)
        assert any("3 blank" in issue for issue in result.detected_issues)

    def test_no_issue_when_above_threshold(self):
        """Fields at or above threshold don't generate issues."""
        entries = _make_entries(
            10, name="Alice", amount=100.0, date="2024-01-01",
            description="Payment",
        )
        configs = REQUIRED_CONFIGS + [OPTIONAL_CONFIGS[0]]  # description only
        result = assess_data_quality(entries, configs)

        assert result.detected_issues == []

    def test_optional_weight_distribution(self):
        """Optional fields share the optional weight pool equally."""
        entries = _make_entries(
            10, name="Alice", amount=100.0, date="2024-01-01",
            description="Payment", category="Expense",
        )
        configs = REQUIRED_CONFIGS + OPTIONAL_CONFIGS
        result = assess_data_quality(entries, configs)

        assert result.completeness_score == 100.0

        # Now make one optional empty
        entries2 = _make_entries(
            10, name="Alice", amount=100.0, date="2024-01-01",
            description="", category="Expense",
        )
        result2 = assess_data_quality(entries2, configs)
        # description=0, category=1.0. Optional pool = 0.15/2 = 0.075 each
        # Score = (0.30+0.30+0.25+0.0*0.075+1.0*0.075) * 100 = (0.85+0.075)*100 = 92.5
        assert result2.completeness_score == 92.5

    def test_custom_optional_weight_pool(self):
        """Custom optional weight pool is respected."""
        entries = _make_entries(
            10, name="Alice", amount=100.0, date="2024-01-01",
            description="Payment",
        )
        configs = REQUIRED_CONFIGS + [OPTIONAL_CONFIGS[0]]
        result = assess_data_quality(entries, configs, optional_weight_pool=0.10)

        # Required: 0.85. Optional: description=1.0 * 0.10 = 0.10
        # Score = (0.85 + 0.10) * 100 = 95.0
        assert result.completeness_score == 95.0

    def test_score_capped_at_100(self):
        """Score never exceeds 100.0 even with high weights."""
        entries = _make_entries(5, name="Alice", amount=100.0, date="2024-01-01")
        # Weights sum to more than 1.0
        heavy_configs = [
            FieldQualityConfig("name", lambda e: e.name, weight=0.50),
            FieldQualityConfig("amount", lambda e: e.amount != 0, weight=0.40),
            FieldQualityConfig("date", lambda e: e.date, weight=0.30),
        ]
        result = assess_data_quality(entries, heavy_configs, optional_weight_pool=0.0)
        assert result.completeness_score == 100.0

    def test_to_dict_shape(self):
        """to_dict returns correct structure with rounded values."""
        entries = _make_entries(3, name="Alice", amount=100.0, date="2024-01-01")
        result = assess_data_quality(entries, REQUIRED_CONFIGS)
        d = result.to_dict()

        assert "completeness_score" in d
        assert "field_fill_rates" in d
        assert "detected_issues" in d
        assert "total_rows" in d
        assert isinstance(d["completeness_score"], float)
        assert isinstance(d["field_fill_rates"], dict)
        assert isinstance(d["detected_issues"], list)
        assert d["total_rows"] == 3

    def test_zero_amount_accessor(self):
        """Amount accessor checks != 0, not just truthy."""
        entries = _make_entries(10, name="Alice", amount=0.0, date="2024-01-01")
        result = assess_data_quality(entries, REQUIRED_CONFIGS)

        assert result.field_fill_rates["amount"] == 0.0
        assert any("zero amount" in issue for issue in result.detected_issues)

    def test_single_entry(self):
        """Works correctly with a single entry."""
        entries = [MockEntry(name="Alice", amount=100.0, date="2024-01-01")]
        result = assess_data_quality(entries, REQUIRED_CONFIGS)
        assert result.total_rows == 1
        assert result.completeness_score == 100.0

    def test_field_no_issue_template(self):
        """Fields with no issue_template don't generate issues even below threshold."""
        entries = _make_entries(10, name="Alice", amount=100.0, date="2024-01-01", category="")
        config_no_template = FieldQualityConfig(
            field_name="category",
            accessor=lambda e: e.category,
            issue_threshold=0.80,
            issue_template=None,
        )
        configs = REQUIRED_CONFIGS + [config_no_template]
        result = assess_data_quality(entries, configs)
        # category at 0% < 0.80 but no template, so no issue
        assert not any("category" in issue.lower() for issue in result.detected_issues)
