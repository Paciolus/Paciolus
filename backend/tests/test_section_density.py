"""
Sprint 296: Account Density Profile

Tests:
- SectionDensity dataclass and to_dict()
- compute_section_density() with various groupings
- Sparse flagging: account_count < 3 AND balance > materiality
- Edge cases: empty sections, zero materiality, all-empty grouping
- Integration: section_density in PopulationProfileReport.to_dict()
- DENSITY_SECTIONS constant completeness
"""

import pytest

from population_profile_engine import (
    DENSITY_SECTIONS,
    SPARSE_ACCOUNT_THRESHOLD,
    SectionDensity,
    PopulationProfileReport,
    compute_section_density,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def sample_grouping():
    """Lead sheet grouping with mixed-density sections."""
    return {
        "summaries": [
            {"lead_sheet": "A", "name": "Cash", "net_balance": 50000.0, "account_count": 5},
            {"lead_sheet": "B", "name": "Receivables", "net_balance": 30000.0, "account_count": 3},
            {"lead_sheet": "G", "name": "AP", "net_balance": -25000.0, "account_count": 2},
            {"lead_sheet": "K", "name": "Equity", "net_balance": -75000.0, "account_count": 1},
            {"lead_sheet": "L", "name": "Revenue", "net_balance": -100000.0, "account_count": 1},
            {"lead_sheet": "M", "name": "COGS", "net_balance": 60000.0, "account_count": 4},
            {"lead_sheet": "N", "name": "OpEx", "net_balance": 40000.0, "account_count": 10},
        ],
    }


# ═══════════════════════════════════════════════════════════════
# DENSITY_SECTIONS Constant
# ═══════════════════════════════════════════════════════════════

class TestDensitySections:
    """Verify DENSITY_SECTIONS covers all 15 lead sheet letters A-O."""

    def test_covers_all_letters(self):
        """All letters A through O should be represented."""
        all_letters = set()
        for _, letters in DENSITY_SECTIONS:
            all_letters.update(letters)
        expected = set("ABCDEFGHIJKLMNO")
        assert all_letters == expected

    def test_nine_sections(self):
        """Should have 9 sections matching FS categories."""
        assert len(DENSITY_SECTIONS) == 9

    def test_no_duplicate_letters(self):
        """Each letter should appear in exactly one section."""
        seen: list[str] = []
        for _, letters in DENSITY_SECTIONS:
            for letter in letters:
                assert letter not in seen, f"Duplicate: {letter}"
                seen.append(letter)


# ═══════════════════════════════════════════════════════════════
# compute_section_density()
# ═══════════════════════════════════════════════════════════════

class TestComputeSectionDensity:
    """Verify section density computation."""

    def test_returns_nine_sections(self, sample_grouping):
        """Should always return 9 sections regardless of grouping content."""
        result = compute_section_density(sample_grouping, 10000.0)
        assert len(result) == 9

    def test_current_assets_aggregation(self, sample_grouping):
        """Current Assets section should aggregate A+B."""
        result = compute_section_density(sample_grouping, 10000.0)
        ca = next(s for s in result if s.section_label == "Current Assets")
        assert ca.account_count == 8  # 5 + 3
        assert ca.section_balance == pytest.approx(80000.0)  # |50000| + |30000|

    def test_balance_per_account(self, sample_grouping):
        """balance_per_account = section_balance / account_count."""
        result = compute_section_density(sample_grouping, 10000.0)
        ca = next(s for s in result if s.section_label == "Current Assets")
        assert ca.balance_per_account == pytest.approx(80000.0 / 8)

    def test_empty_section_zero_balance(self, sample_grouping):
        """Sections with no lead sheets in grouping should have 0 balance."""
        result = compute_section_density(sample_grouping, 10000.0)
        # E, F not in sample_grouping
        nca = next(s for s in result if s.section_label == "Non-Current Assets")
        assert nca.account_count == 0
        assert nca.section_balance == 0.0
        assert nca.balance_per_account == 0.0

    def test_sparse_flag_low_count_high_balance(self, sample_grouping):
        """Section with <3 accounts and balance > materiality → sparse."""
        result = compute_section_density(sample_grouping, 10000.0)
        # Equity: 1 account, |75000| > 10000 → sparse
        equity = next(s for s in result if s.section_label == "Equity")
        assert equity.is_sparse is True

    def test_sparse_flag_revenue(self, sample_grouping):
        """Revenue: 1 account, |100000| > 10000 → sparse."""
        result = compute_section_density(sample_grouping, 10000.0)
        rev = next(s for s in result if s.section_label == "Revenue")
        assert rev.is_sparse is True
        assert rev.account_count == 1

    def test_not_sparse_high_count(self, sample_grouping):
        """Section with ≥3 accounts should NOT be sparse."""
        result = compute_section_density(sample_grouping, 10000.0)
        ca = next(s for s in result if s.section_label == "Current Assets")
        assert ca.is_sparse is False

    def test_not_sparse_below_materiality(self):
        """Section with <3 accounts but balance < materiality → not sparse."""
        grouping = {
            "summaries": [
                {"lead_sheet": "K", "name": "Equity", "net_balance": -500.0, "account_count": 1},
            ],
        }
        result = compute_section_density(grouping, 10000.0)
        equity = next(s for s in result if s.section_label == "Equity")
        assert equity.is_sparse is False

    def test_empty_section_not_sparse(self, sample_grouping):
        """Empty sections (0 accounts) are never sparse."""
        result = compute_section_density(sample_grouping, 0.0)
        nca = next(s for s in result if s.section_label == "Non-Current Assets")
        assert nca.is_sparse is False

    def test_absolute_balance_used(self):
        """net_balance is negative for liabilities — section_balance should use absolute value."""
        grouping = {
            "summaries": [
                {"lead_sheet": "G", "name": "AP", "net_balance": -50000.0, "account_count": 2},
                {"lead_sheet": "H", "name": "Other CL", "net_balance": -20000.0, "account_count": 1},
            ],
        }
        result = compute_section_density(grouping, 10000.0)
        cl = next(s for s in result if s.section_label == "Current Liabilities")
        assert cl.section_balance == pytest.approx(70000.0)  # |50000| + |20000|
        assert cl.account_count == 3
        assert cl.is_sparse is False  # 3 accounts ≥ threshold

    def test_zero_materiality_always_sparse_if_low_count(self):
        """With materiality=0, any section with <3 accounts and balance>0 is sparse."""
        grouping = {
            "summaries": [
                {"lead_sheet": "O", "name": "Other", "net_balance": -100.0, "account_count": 1},
            ],
        }
        result = compute_section_density(grouping, 0.0)
        other = next(s for s in result if s.section_label == "Other Income/Expense")
        assert other.is_sparse is True

    def test_empty_grouping(self):
        """Empty grouping should return 9 sections, all with 0 accounts."""
        result = compute_section_density({}, 10000.0)
        assert len(result) == 9
        assert all(s.account_count == 0 for s in result)
        assert all(s.is_sparse is False for s in result)


# ═══════════════════════════════════════════════════════════════
# SectionDensity.to_dict()
# ═══════════════════════════════════════════════════════════════

class TestSectionDensityToDict:
    """Verify serialization."""

    def test_to_dict_keys(self):
        """to_dict() should have all expected keys."""
        sd = SectionDensity(
            section_label="Current Assets",
            section_letters=["A", "B", "C", "D"],
            account_count=5,
            section_balance=100000.0,
            balance_per_account=20000.0,
            is_sparse=False,
        )
        d = sd.to_dict()
        assert set(d.keys()) == {
            "section_label", "section_letters", "account_count",
            "section_balance", "balance_per_account", "is_sparse",
        }

    def test_to_dict_values(self):
        """to_dict() values should be correctly rounded."""
        sd = SectionDensity(
            section_label="Equity",
            section_letters=["K"],
            account_count=1,
            section_balance=75000.123,
            balance_per_account=75000.123,
            is_sparse=True,
        )
        d = sd.to_dict()
        assert d["section_balance"] == 75000.12
        assert d["balance_per_account"] == 75000.12
        assert d["is_sparse"] is True


# ═══════════════════════════════════════════════════════════════
# Integration: PopulationProfileReport
# ═══════════════════════════════════════════════════════════════

class TestPopulationProfileIntegration:
    """Verify section_density appears in PopulationProfileReport.to_dict()."""

    def test_to_dict_includes_section_density(self):
        """to_dict() should include section_density when populated."""
        density = [SectionDensity(
            section_label="Test",
            section_letters=["A"],
            account_count=1,
            section_balance=1000.0,
            balance_per_account=1000.0,
            is_sparse=False,
        )]
        report = PopulationProfileReport(
            account_count=1,
            total_abs_balance=1000.0,
            mean_abs_balance=1000.0,
            median_abs_balance=1000.0,
            std_dev_abs_balance=0.0,
            min_abs_balance=1000.0,
            max_abs_balance=1000.0,
            p25=1000.0,
            p75=1000.0,
            gini_coefficient=0.0,
            gini_interpretation="Low",
            section_density=density,
        )
        d = report.to_dict()
        assert "section_density" in d
        assert len(d["section_density"]) == 1
        assert d["section_density"][0]["section_label"] == "Test"

    def test_to_dict_omits_empty_section_density(self):
        """to_dict() should not include section_density when empty."""
        report = PopulationProfileReport(
            account_count=0,
            total_abs_balance=0.0,
            mean_abs_balance=0.0,
            median_abs_balance=0.0,
            std_dev_abs_balance=0.0,
            min_abs_balance=0.0,
            max_abs_balance=0.0,
            p25=0.0,
            p75=0.0,
            gini_coefficient=0.0,
            gini_interpretation="Low",
        )
        d = report.to_dict()
        assert "section_density" not in d
