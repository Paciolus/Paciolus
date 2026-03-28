"""Property-based tests for anomaly generators.

Uses Hypothesis to verify that anomaly generators produce valid output
across a range of parameters and seeds. These tests focus on robustness
(no crashes, valid structure) rather than detection accuracy.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from audit_engine import audit_trial_balance_streaming
from tests.anomaly_framework.fixtures.base_trial_balance import BaseTrialBalanceFactory
from tests.anomaly_framework.generators.abnormal_balance import AbnormalBalanceGenerator
from tests.anomaly_framework.generators.asset_concentration import AssetConcentrationGenerator
from tests.anomaly_framework.generators.balance_sheet_imbalance import BalanceSheetImbalanceGenerator
from tests.anomaly_framework.generators.duplicate_entry import DuplicateEntryGenerator
from tests.anomaly_framework.generators.equity_signal import EquitySignalGenerator
from tests.anomaly_framework.generators.expense_concentration import ExpenseConcentrationGenerator
from tests.anomaly_framework.generators.liability_concentration import LiabilityConcentrationGenerator
from tests.anomaly_framework.generators.missing_offset import MissingOffsetGenerator
from tests.anomaly_framework.generators.related_party_activity import RelatedPartyActivityGenerator
from tests.anomaly_framework.generators.revenue_concentration import RevenueConcentrationGenerator
from tests.anomaly_framework.generators.round_number import RoundNumberGenerator
from tests.anomaly_framework.generators.suspense_account import SuspenseAccountGenerator
from tests.anomaly_framework.generators.weekend_posting import WeekendPostingGenerator

_SEEDS = st.integers(min_value=0, max_value=9999)
_SETTINGS = settings(max_examples=25, suppress_health_check=[HealthCheck.too_slow])


def _run_engine(df):
    """Run the audit engine on a DataFrame and return the result."""
    csv_bytes = df.to_csv(index=False).encode()
    return audit_trial_balance_streaming(file_bytes=csv_bytes, filename="prop_test.csv")


# --- Existing tests (duplicate + round number) ---


@given(seed=_SEEDS, num_duplicates=st.integers(min_value=2, max_value=8))
@_SETTINGS
def test_duplicate_detection_is_seed_independent(seed, num_duplicates):
    """Verify duplicate injection works across seeds and duplicate counts."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    gen = DuplicateEntryGenerator(num_duplicates=num_duplicates)
    mutated_df, records = gen.inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df) + num_duplicates
    assert len(records) == 1
    assert records[0].anomaly_type == "duplicate_entry"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(amount_scale=st.floats(min_value=100.0, max_value=1_000_000.0))
@_SETTINGS
def test_round_number_detection_across_scales(amount_scale):
    """Verify round number injection works across amount scales."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    gen = RoundNumberGenerator(amount_scale=amount_scale)
    mutated_df, records = gen.inject(base_df, seed=0)

    assert len(mutated_df) == len(base_df)
    assert len(records) == 1
    assert records[0].anomaly_type == "round_number"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


# --- New property tests for remaining generators ---


@given(seed=_SEEDS)
@_SETTINGS
def test_suspense_account_across_seeds(seed):
    """Suspense account generator is robust across seeds."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = SuspenseAccountGenerator().inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df) + 1  # one new account added
    assert len(records) == 1
    assert records[0].anomaly_type == "suspense_account"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_abnormal_balance_across_seeds(seed):
    """Abnormal balance generator is robust across seeds."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = AbnormalBalanceGenerator().inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df)
    assert len(records) == 1
    assert records[0].anomaly_type == "abnormal_balance"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_missing_offset_across_seeds(seed):
    """Missing offset generator adds exactly one orphan row."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = MissingOffsetGenerator().inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df) + 1
    assert len(records) == 1
    assert records[0].anomaly_type == "missing_offset"

    result = _run_engine(mutated_df)
    assert result.get("balanced") is False  # orphan entry unbalances TB


@given(seed=_SEEDS)
@_SETTINGS
def test_weekend_posting_across_seeds(seed):
    """Weekend posting (intercompany) generator adds paired accounts."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = WeekendPostingGenerator().inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df) + 2  # two intercompany accounts
    assert len(records) == 1
    assert records[0].anomaly_type == "weekend_posting"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_related_party_across_seeds(seed):
    """Related party generator adds offsetting pair."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = RelatedPartyActivityGenerator().inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df) + 2  # two related-party accounts
    assert len(records) == 1
    assert records[0].anomaly_type == "related_party_activity"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_revenue_concentration_structural(seed):
    """Revenue concentration replaces revenue with skewed distribution."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = RevenueConcentrationGenerator().inject(base_df, seed=seed)

    # Should have exactly 2 revenue accounts after injection
    rev_count = (mutated_df["Account Type"].str.lower() == "revenue").sum()
    assert rev_count == 2
    assert len(records) == 1
    assert records[0].anomaly_type == "revenue_concentration"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_expense_concentration_structural(seed):
    """Expense concentration replaces expenses with skewed distribution."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = ExpenseConcentrationGenerator().inject(base_df, seed=seed)

    exp_count = (mutated_df["Account Type"].str.lower() == "expense").sum()
    assert exp_count == 2
    assert len(records) == 1
    assert records[0].anomaly_type == "expense_concentration"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_balance_sheet_imbalance_across_seeds(seed):
    """Balance sheet imbalance generator creates unbalanced TB."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = BalanceSheetImbalanceGenerator().inject(base_df, seed=seed)

    assert len(mutated_df) == len(base_df) + 1  # one orphan asset added
    assert len(records) == 1
    assert records[0].anomaly_type == "balance_sheet_imbalance"

    result = _run_engine(mutated_df)
    assert result.get("balanced") is False


@given(seed=_SEEDS)
@_SETTINGS
def test_equity_signal_structural(seed):
    """Equity signal generator creates deficit + dividends pattern."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    gen = EquitySignalGenerator(deficit_amount=35_000.0, dividend_amount=12_431.0)
    mutated_df, records = gen.inject(base_df, seed=seed)

    assert len(records) == 1
    assert records[0].anomaly_type == "equity_signal"

    # Verify RE has debit balance (deficit)
    re_rows = mutated_df[mutated_df["Account Name"].str.contains("Retained Earnings", case=False)]
    assert len(re_rows) >= 1
    assert re_rows.iloc[0]["Debit"] > 0

    # Verify dividends account exists
    div_rows = mutated_df[mutated_df["Account Name"].str.contains("Dividend", case=False)]
    assert len(div_rows) >= 1

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_asset_concentration_structural(seed):
    """Asset concentration replaces assets with skewed distribution."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = AssetConcentrationGenerator().inject(base_df, seed=seed)

    asset_rows = mutated_df[mutated_df["Account Type"].str.lower() == "asset"]
    assert len(asset_rows) == 2
    assert len(records) == 1
    assert records[0].anomaly_type == "asset_concentration"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0


@given(seed=_SEEDS)
@_SETTINGS
def test_liability_concentration_structural(seed):
    """Liability concentration replaces liabilities with skewed distribution."""
    base_df = BaseTrialBalanceFactory.as_dataframe()
    mutated_df, records = LiabilityConcentrationGenerator().inject(base_df, seed=seed)

    liab_rows = mutated_df[mutated_df["Account Type"].str.lower() == "liability"]
    assert len(liab_rows) == 2
    assert len(records) == 1
    assert records[0].anomaly_type == "liability_concentration"

    result = _run_engine(mutated_df)
    assert result.get("row_count", 0) > 0
