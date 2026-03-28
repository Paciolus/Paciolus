"""Anomaly generator registry.

Central registry of all available anomaly generators. Used by test
parametrization to run detection tests against every generator.

Each entry in ANOMALY_REGISTRY_META exposes a ``min_detectable_threshold``
(the production constant that governs the detection floor) so that tests can
verify injection magnitudes are appropriate.  When no single constant governs
the threshold, the value is ``None`` and a ``threshold_note`` explains where
the detection boundary is determined.
"""

from classification_rules import (
    CONCENTRATION_THRESHOLD_MEDIUM,
    ROUNDING_MIN_AMOUNT,
    SUSPENSE_CONFIDENCE_THRESHOLD,
)
from shared.monetary import BALANCE_TOLERANCE
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

ANOMALY_REGISTRY: list = [
    RoundNumberGenerator(),
    DuplicateEntryGenerator(),
    WeekendPostingGenerator(),
    SuspenseAccountGenerator(),
    AbnormalBalanceGenerator(),
    MissingOffsetGenerator(),
    RelatedPartyActivityGenerator(),
    RevenueConcentrationGenerator(),
    ExpenseConcentrationGenerator(),
    BalanceSheetImbalanceGenerator(),
    EquitySignalGenerator(),
    AssetConcentrationGenerator(),
    LiabilityConcentrationGenerator(),
]

ANOMALY_REGISTRY_META: dict = {
    "round_number": {
        "generator": RoundNumberGenerator,
        "min_detectable_threshold": ROUNDING_MIN_AMOUNT,
        "threshold_note": (
            "Balance must be >= ROUNDING_MIN_AMOUNT (10000.0) AND divisible by a "
            "ROUNDING_PATTERNS divisor (10k/50k/100k). Tier 1 accounts are suppressed."
        ),
    },
    "duplicate_entry": {
        "generator": DuplicateEntryGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "TB-level: detects imbalance caused by duplicates (BALANCE_TOLERANCE = 0.01) "
            "but not the duplicates themselves. JE/AP tools detect exact duplicates via "
            "key matching — no minimum amount threshold. See DUPLICATE_ENTRY_CONTRACT.md."
        ),
    },
    "weekend_posting": {
        "generator": WeekendPostingGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "Detection requires: (1) account name matches INTERCOMPANY_KEYWORDS, "
            "(2) abs(net) >= BALANCE_TOLERANCE (0.01), (3) counterparty extracted from "
            "account name via separator heuristic, (4) counterparty group net != 0. "
            "No single constant — boundary is emergent from keyword + extraction logic. "
            "See audit/rules/relationships.py :: detect_intercompany_imbalances()."
        ),
    },
    "suspense_account": {
        "generator": SuspenseAccountGenerator,
        "min_detectable_threshold": SUSPENSE_CONFIDENCE_THRESHOLD,
        "threshold_note": (
            "Sum of matched SUSPENSE_KEYWORDS weights must reach "
            "SUSPENSE_CONFIDENCE_THRESHOLD (0.60). Keywords defined in "
            "classification_rules.py."
        ),
    },
    "abnormal_balance": {
        "generator": AbnormalBalanceGenerator,
        "min_detectable_threshold": float(BALANCE_TOLERANCE),
        "threshold_note": (
            "Accounts with abs(net) < BALANCE_TOLERANCE (0.01) are skipped. "
            "Detection also requires classification confidence >= CONFIDENCE_MEDIUM (0.4) "
            "and known AccountCategory (UNKNOWN is never flagged)."
        ),
    },
    "missing_offset": {
        "generator": MissingOffsetGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "Detection relies on total_debits != total_credits (TB balance check). "
            "Tolerance is BALANCE_TOLERANCE (0.01) applied to overall TB comparison. "
            "Any orphan entry > $0.01 that unbalances the TB will be detected, but the "
            "specific entry is not individually identified."
        ),
    },
    "related_party_activity": {
        "generator": RelatedPartyActivityGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "Detection relies on RELATED_PARTY_KEYWORDS in classification_rules.py. "
            "Account names must contain keywords like 'intercompany', 'affiliate', "
            "'related party', 'due from/to'. No minimum balance threshold."
        ),
    },
    "revenue_concentration": {
        "generator": RevenueConcentrationGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "Detection relies on single-account share of total revenue category. "
            "Concentration threshold is determined by detect_revenue_concentration() "
            "in audit/rules/concentration.py."
        ),
    },
    "expense_concentration": {
        "generator": ExpenseConcentrationGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "Detection relies on single-account share of total expense category. "
            "Concentration threshold is determined by detect_expense_concentration() "
            "in audit/rules/concentration.py."
        ),
    },
    "balance_sheet_imbalance": {
        "generator": BalanceSheetImbalanceGenerator,
        "min_detectable_threshold": float(BALANCE_TOLERANCE),
        "threshold_note": (
            "Detection relies on total_debits != total_credits check. "
            "Tolerance is BALANCE_TOLERANCE (0.01). Any imbalance > $0.01 "
            "causes balanced=False in the audit result."
        ),
    },
    "equity_signal": {
        "generator": EquitySignalGenerator,
        "min_detectable_threshold": None,
        "threshold_note": (
            "Detection requires: (1) Retained Earnings account with debit balance "
            "(deficit), (2) Dividends account present. Both conditions must be met. "
            "Fixed confidence of 0.90. See audit/rules/equity.py :: detect_equity_signals()."
        ),
    },
    "asset_concentration": {
        "generator": AssetConcentrationGenerator,
        "min_detectable_threshold": float(CONCENTRATION_THRESHOLD_MEDIUM),
        "threshold_note": (
            "Single asset account must represent >= 25% (MEDIUM) or >= 50% (HIGH) "
            "of total asset category. Minimum category total: "
            "CONCENTRATION_MIN_CATEGORY_TOTAL (1000.0). "
            "See audit/rules/concentration.py :: detect_concentration_risk()."
        ),
    },
    "liability_concentration": {
        "generator": LiabilityConcentrationGenerator,
        "min_detectable_threshold": float(CONCENTRATION_THRESHOLD_MEDIUM),
        "threshold_note": (
            "Single liability account must represent >= 25% (MEDIUM) or >= 50% (HIGH) "
            "of total liability category. Minimum category total: "
            "CONCENTRATION_MIN_CATEGORY_TOTAL (1000.0). "
            "See audit/rules/concentration.py :: detect_concentration_risk()."
        ),
    },
}


def get_generator(name: str) -> object:
    """Look up a generator by name.

    Args:
        name: The generator's name attribute.

    Returns:
        The matching AnomalyGenerator instance.

    Raises:
        KeyError: If no generator matches the name.
    """
    for g in ANOMALY_REGISTRY:
        if g.name == name:
            return g
    raise KeyError(f"No generator named '{name}'")
