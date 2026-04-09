"""Multi-Period Comparison anomaly generators.

Each generator injects a specific period-over-period anomaly into clean
prior and current period trial balance data, returning AnomalyRecords
describing the expected detection outcome.

Generators match the MovementType classifications from
multi_period_comparison.py: NEW_ACCOUNT, CLOSED, SIGN_CHANGE,
SIGNIFICANT_INCREASE, SIGNIFICANT_DECREASE, and budget variance.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class MultiPeriodGeneratorBase:
    """Base class for multi-period comparison anomaly generators."""

    name: str
    target_test_key: str

    def inject(
        self,
        prior_period: list[dict],
        current_period: list[dict],
        seed: int = 42,
    ) -> tuple[list[dict], list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


class NewAccountGenerator(MultiPeriodGeneratorBase):
    """Inject an account that exists in current period but not prior.

    Adds a new expense account to the current period with no prior-period
    counterpart, simulating a newly opened account.
    """

    name = "new_account"
    target_test_key = "new_accounts"

    def inject(self, prior_period, current_period, seed=42):
        prior_period = deepcopy(prior_period)
        current_period = deepcopy(current_period)

        # Add new account to current period only
        current_period.append(
            {
                "account": "6700",
                "account_name": "Marketing & Advertising",
                "type": "Expense",
                "debit": 18395.50,
                "credit": 0.00,
            }
        )

        # Rebalance current period: reduce Cash to offset
        for acct in current_period:
            if acct["account"] == "1000":
                acct["debit"] -= 18395.50
                break

        record = AnomalyRecord(
            anomaly_type="new_account",
            report_targets=["MPTB-01"],
            injected_at="Account 6700 Marketing & Advertising appears only in current period",
            expected_field="new_accounts",
            expected_condition="items_count > 0",
            metadata={
                "account": "6700",
                "account_name": "Marketing & Advertising",
                "current_balance": 18395.50,
            },
        )
        return prior_period, current_period, [record]


class ClosedAccountGenerator(MultiPeriodGeneratorBase):
    """Inject an account that exists in prior period but not current.

    Removes an account from the current period, simulating an account
    that was closed or discontinued.
    """

    name = "closed_account"
    target_test_key = "closed_accounts"

    def inject(self, prior_period, current_period, seed=42):
        prior_period = deepcopy(prior_period)
        current_period = deepcopy(current_period)

        # Remove Inventory (account 1300) from current period
        removed_balance = None
        current_period_new = []
        for acct in current_period:
            if acct["account"] == "1300":
                removed_balance = acct["debit"] - acct["credit"]
            else:
                current_period_new.append(acct)
        current_period = current_period_new

        # Rebalance: add removed balance to Cash
        for acct in current_period:
            if acct["account"] == "1000":
                acct["debit"] += removed_balance
                break

        record = AnomalyRecord(
            anomaly_type="closed_account",
            report_targets=["MPTB-02"],
            injected_at="Account 1300 Inventory present in prior but absent from current",
            expected_field="closed_accounts",
            expected_condition="items_count > 0",
            metadata={
                "account": "1300",
                "account_name": "Inventory",
                "prior_balance": 41350.00,
            },
        )
        return prior_period, current_period, [record]


class SignChangeGenerator(MultiPeriodGeneratorBase):
    """Inject a balance sign flip from debit to credit.

    Changes an asset account from a normal debit balance to a credit
    balance, simulating an overdrawn or negative asset condition.
    """

    name = "sign_change"
    target_test_key = "sign_changes"

    def inject(self, prior_period, current_period, seed=42):
        prior_period = deepcopy(prior_period)
        current_period = deepcopy(current_period)

        # Flip Accounts Receivable to credit balance in current period
        for acct in current_period:
            if acct["account"] == "1100":
                old_debit = acct["debit"]  # 83900.84
                acct["debit"] = 0.00
                acct["credit"] = 15234.00  # Negative AR = customer overpayment
                # Rebalance: add the swing to Cash
                swing = old_debit + 15234.00
                break

        for acct in current_period:
            if acct["account"] == "1000":
                acct["debit"] -= swing
                break

        record = AnomalyRecord(
            anomaly_type="sign_change",
            report_targets=["MPTB-03"],
            injected_at="Account 1100 AR flipped from $83,901 debit to $15,234 credit",
            expected_field="sign_changes",
            expected_condition="items_count > 0",
            metadata={
                "account": "1100",
                "account_name": "Accounts Receivable",
                "prior_balance": 83900.84,
                "current_balance": -15234.00,
            },
        )
        return prior_period, current_period, [record]


class LargeIncreaseGenerator(MultiPeriodGeneratorBase):
    """Inject a >50% increase in an account balance.

    Inflates an expense account significantly, simulating an unusual
    spike in spending.
    """

    name = "large_increase"
    target_test_key = "significant_increases"

    def inject(self, prior_period, current_period, seed=42):
        prior_period = deepcopy(prior_period)
        current_period = deepcopy(current_period)

        # Increase Rent Expense by 75%: 36179 -> 59813.25
        for acct in current_period:
            if acct["account"] == "6100":
                old_amount = acct["debit"]  # 36179.00
                new_amount = round(old_amount * 1.75, 2)  # 63313.25
                increase = new_amount - old_amount
                acct["debit"] = new_amount
                break

        # Rebalance: reduce Cash
        for acct in current_period:
            if acct["account"] == "1000":
                acct["debit"] -= increase
                break

        record = AnomalyRecord(
            anomaly_type="large_increase",
            report_targets=["MPTB-04"],
            injected_at="Account 6100 Rent Expense increased 75% ($36,179 -> $63,313)",
            expected_field="significant_increases",
            expected_condition="items_count > 0",
            metadata={
                "account": "6100",
                "account_name": "Rent Expense",
                "prior_balance": 34150.00,
                "current_balance": 63313.25,
                "percent_change": 75.0,
            },
        )
        return prior_period, current_period, [record]


class LargeDecreaseGenerator(MultiPeriodGeneratorBase):
    """Inject a >50% decrease in an account balance.

    Reduces a revenue account significantly, simulating a major
    revenue decline.
    """

    name = "large_decrease"
    target_test_key = "significant_decreases"

    def inject(self, prior_period, current_period, seed=42):
        prior_period = deepcopy(prior_period)
        current_period = deepcopy(current_period)

        # Decrease Consulting Revenue by 60%: 106029 -> 42411.60
        for acct in current_period:
            if acct["account"] == "4100":
                old_credit = acct["credit"]  # 106029.00
                new_credit = round(old_credit * 0.40, 2)  # 42411.60
                decrease = old_credit - new_credit
                acct["credit"] = new_credit
                break

        # Rebalance: reduce Cash (less revenue means less cash)
        for acct in current_period:
            if acct["account"] == "1000":
                acct["debit"] -= decrease
                break

        record = AnomalyRecord(
            anomaly_type="large_decrease",
            report_targets=["MPTB-05"],
            injected_at="Account 4100 Consulting Revenue decreased 60% ($106,029 -> $42,412)",
            expected_field="significant_decreases",
            expected_condition="items_count > 0",
            metadata={
                "account": "4100",
                "account_name": "Consulting Revenue",
                "prior_balance": 98175.00,
                "current_balance": 42411.60,
                "percent_change": -60.0,
            },
        )
        return prior_period, current_period, [record]


class BudgetVarianceGenerator(MultiPeriodGeneratorBase):
    """Inject a budget column with actual >> budget.

    Adds a budget column to current period data and sets an expense
    account actual well above budget, simulating a budget overrun.
    """

    name = "budget_variance"
    target_test_key = "budget_variances"

    def inject(self, prior_period, current_period, seed=42):
        prior_period = deepcopy(prior_period)
        current_period = deepcopy(current_period)

        # Add budget column to all current period accounts
        for acct in current_period:
            net = acct["debit"] - acct["credit"]
            # Budget equals actual for most accounts
            acct["budget"] = abs(net)

        # Set Salaries budget well below actual (actual is ~$95,498, budget is $70,000)
        for acct in current_period:
            if acct["account"] == "6000":
                acct["budget"] = 70000.00
                break

        record = AnomalyRecord(
            anomaly_type="budget_variance",
            report_targets=["MPTB-06"],
            injected_at="Account 6000 Salaries: actual=$95,498 vs budget=$70,000 (36% over)",
            expected_field="budget_variances",
            expected_condition="items_count > 0",
            metadata={
                "account": "6000",
                "account_name": "Salaries & Wages",
                "actual": 95497.50,
                "budget": 70000.00,
                "variance_percent": 36.4,
            },
        )
        return prior_period, current_period, [record]


MULTI_PERIOD_REGISTRY: list[MultiPeriodGeneratorBase] = [
    NewAccountGenerator(),
    ClosedAccountGenerator(),
    SignChangeGenerator(),
    LargeIncreaseGenerator(),
    LargeDecreaseGenerator(),
    BudgetVarianceGenerator(),
]
