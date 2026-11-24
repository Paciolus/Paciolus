"""
Financial Statement Builder Module
Sprint 71: Financial Statements — Backend Builder
Sprint 83: Cash Flow Statement — Indirect Method (ASC 230 / IAS 7)

Transforms lead sheet groupings (A-Z) into formatted Balance Sheet,
Income Statement, and Cash Flow Statement documents.

Data Flow:
    TB → StreamingAuditor → Classification → lead_sheet_grouping dict
                                                    ↓
    lead_sheet_grouping → FinancialStatementBuilder → BS + IS + CF

Cash Flow (Indirect Method):
    Requires current + prior lead sheet groupings to compute working capital changes.
    - Operating: Net Income + Depreciation add-back + Working Capital changes
    - Investing: Change in gross PPE (E) + Other Non-Current Assets (F), at cost —
      accumulated depreciation/amortization excluded (Sprint 882, TQ-03)
    - Financing: Change in Debt (I, J) + change in total equity less net income
      (Sprint 882, TQ-02)

Sign Conventions:
    Lead sheet net_balance = total_debit - total_credit
    - Assets (A-F): positive net_balance → display as-is
    - Liabilities (G-J): negative net_balance → flip sign for display
    - Equity (K): negative net_balance → flip sign for display
    - Revenue (L): negative net_balance → flip sign for display
    - COGS (M): positive net_balance → display as-is
    - Expenses (N): positive net_balance → display as-is
    - Other (O): mixed → flip sign (credits = income, debits = expense)
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from shared.monetary import BALANCE_TOLERANCE, MONETARY_NEAR_ZERO, quantize_monetary
from shared.parsing_helpers import safe_decimal

# Sprint 884: every amount in this module is an exact Decimal. Float never
# touches a monetary value, so e.g. 90071992547409.93 survives unchanged.
ZERO = Decimal("0")

# Interest expense keywords for automatic detection from account descriptions
INTEREST_EXPENSE_KEYWORDS: list[tuple[str, bool]] = [
    ("interest expense", True),
    ("interest paid", True),
    ("interest on debt", True),
    ("interest on loan", True),
    ("interest on note", True),
    ("loan interest", True),
    ("mortgage interest", True),
    ("interest cost", True),
]

# Depreciation keywords for automatic detection from account descriptions
DEPRECIATION_KEYWORDS: list[tuple[str, bool]] = [
    ("depreciation", False),
    ("amortization", False),
    ("deprec", False),
    ("amort", False),
    ("depr exp", True),
    ("accum deprec", True),
    ("accumulated depreciation", True),
    ("depreciation expense", True),
    ("amortization expense", True),
]


@dataclass
class StatementLineItem:
    """A single line on a financial statement."""

    label: str
    amount: Decimal
    indent_level: int = 0  # 0=section header, 1=line item
    is_subtotal: bool = False
    is_total: bool = False
    lead_sheet_ref: str = ""  # "A", "B", etc.
    prior_amount: Optional[Decimal] = None  # Prior period amount (Sprint 488)


@dataclass
class CashFlowLineItem:
    """A single line item on the cash flow statement."""

    label: str
    amount: Decimal
    source: str = ""  # lead_sheet_ref or "computed"
    indent_level: int = 1  # 0=section header, 1=line item


@dataclass
class CashFlowSection:
    """A section of the cash flow statement (Operating, Investing, or Financing)."""

    label: str
    items: list[CashFlowLineItem] = field(default_factory=list)
    subtotal: Decimal = ZERO

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "items": [
                {
                    "label": item.label,
                    "amount": item.amount,
                    "source": item.source,
                    "indent_level": item.indent_level,
                }
                for item in self.items
            ],
            "subtotal": self.subtotal,
        }


@dataclass
class CashFlowStatement:
    """Complete cash flow statement (indirect method per ASC 230 / IAS 7)."""

    operating: CashFlowSection
    investing: CashFlowSection
    financing: CashFlowSection
    net_change: Decimal = ZERO
    beginning_cash: Decimal = ZERO
    ending_cash: Decimal = ZERO
    is_reconciled: bool = False
    reconciliation_difference: Decimal = ZERO
    has_prior_period: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "operating": self.operating.to_dict(),
            "investing": self.investing.to_dict(),
            "financing": self.financing.to_dict(),
            "net_change": self.net_change,
            "beginning_cash": self.beginning_cash,
            "ending_cash": self.ending_cash,
            "is_reconciled": self.is_reconciled,
            "reconciliation_difference": self.reconciliation_difference,
            "has_prior_period": self.has_prior_period,
            "notes": self.notes,
        }


@dataclass
class MappingTraceAccount:
    """An individual TB account contributing to a statement line."""

    account_name: str
    debit: Decimal
    credit: Decimal
    net_balance: Decimal
    confidence: float
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class MappingTraceEntry:
    """Maps a financial statement line to its contributing TB accounts."""

    statement: str  # "Balance Sheet" | "Income Statement"
    line_label: str  # e.g. "Cash and Cash Equivalents"
    lead_sheet_ref: str  # "A"
    lead_sheet_name: str  # "Cash and Cash Equivalents"
    statement_amount: Decimal  # sign-corrected display amount
    account_count: int
    accounts: list[MappingTraceAccount] = field(default_factory=list)
    is_tied: bool = True
    tie_difference: Decimal = ZERO
    raw_aggregate: Decimal = ZERO  # Sprint 295: sum of account net balances (pre-sign-correction)
    sign_correction_applied: bool = False  # Sprint 295: True for credit-normal letters (G-K, L, O)


@dataclass
class EquityComponent:
    """Sprint 638: A single equity component row on the SOCE rollforward.

    ``component_type`` uses the standard SOCE column headers so the
    exporter can render the matrix without re-classifying. Unmapped
    equity accounts fall into ``RETAINED_EARNINGS`` by default but are
    surfaced on ``StatementOfChangesInEquity.unmapped_accounts`` for
    practitioner review.
    """

    component_type: (
        str  # "common_stock" / "additional_paid_in_capital" / "retained_earnings" / "treasury_stock" / "aoci" / "other"
    )
    label: str
    beginning_balance: Decimal
    contributions: Decimal = ZERO  # Owner contributions / stock issuance
    distributions: Decimal = ZERO  # Distributions / share buybacks (negative to equity)
    dividends: Decimal = ZERO  # Dividends declared (negative to retained earnings)
    net_income_allocation: Decimal = ZERO  # Net income attribution (retained earnings only)
    other_comprehensive_income: Decimal = ZERO  # AOCI movement only
    other_movement: Decimal = ZERO  # Catch-all for residuals
    ending_balance: Decimal = ZERO


@dataclass
class StatementOfChangesInEquity:
    """Sprint 638: Equity rollforward produced alongside BS / IS / CF.

    The engine does NOT attempt to distinguish contributions from
    dividends automatically — that is auditor judgement and requires
    supporting documentation. The SOCE is driven from the equity
    balances on the TB: beginning from prior period (if supplied),
    ending from current period, net income flowing into the retained
    earnings component. Extra activity (contributions, distributions,
    dividends) is accepted via ``EquityActivity`` inputs when the
    caller has them.
    """

    components: list[EquityComponent]
    beginning_total_equity: Decimal
    net_income: Decimal
    total_contributions: Decimal
    total_distributions: Decimal
    total_dividends: Decimal
    total_other_comprehensive_income: Decimal
    total_other_movement: Decimal
    ending_total_equity: Decimal
    unmapped_accounts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "components": [
                {
                    "component_type": c.component_type,
                    "label": c.label,
                    "beginning_balance": c.beginning_balance,
                    "contributions": c.contributions,
                    "distributions": c.distributions,
                    "dividends": c.dividends,
                    "net_income_allocation": c.net_income_allocation,
                    "other_comprehensive_income": c.other_comprehensive_income,
                    "other_movement": c.other_movement,
                    "ending_balance": c.ending_balance,
                }
                for c in self.components
            ],
            "beginning_total_equity": self.beginning_total_equity,
            "net_income": self.net_income,
            "total_contributions": self.total_contributions,
            "total_distributions": self.total_distributions,
            "total_dividends": self.total_dividends,
            "total_other_comprehensive_income": self.total_other_comprehensive_income,
            "total_other_movement": self.total_other_movement,
            "ending_total_equity": self.ending_total_equity,
            "unmapped_accounts": list(self.unmapped_accounts),
        }


@dataclass
class EquityActivity:
    """Optional per-account activity passed in when the caller has it.

    Account names are matched case-insensitively against equity accounts
    on the current-period lead sheet. When an account is not supplied
    here, the engine infers movement from the beginning-to-ending delta
    less the net-income share for retained-earnings accounts.
    """

    account: str
    contributions: Decimal = ZERO
    distributions: Decimal = ZERO
    dividends: Decimal = ZERO


# Sprint 867: the balance-sheet equity line for a pre-closing TB's period result.
UNCLOSED_EARNINGS_LABEL = "Current-Period Earnings (Not Yet Closed)"


@dataclass
class FinancialStatements:
    """Complete financial statements built from lead sheet groupings."""

    balance_sheet: list[StatementLineItem]
    income_statement: list[StatementLineItem]
    # Balance Sheet totals
    total_assets: Decimal = ZERO
    total_liabilities: Decimal = ZERO
    total_equity: Decimal = ZERO
    is_balanced: bool = False
    balance_difference: Decimal = ZERO
    # Income Statement totals
    total_revenue: Decimal = ZERO
    gross_profit: Decimal = ZERO
    operating_income: Decimal = ZERO
    net_income: Decimal = ZERO
    # Cash Flow Statement (Sprint 83)
    cash_flow_statement: Optional[CashFlowStatement] = None
    # Statement of Changes in Equity (Sprint 638)
    statement_of_changes_in_equity: Optional[StatementOfChangesInEquity] = None
    # Account-to-Statement Mapping Trace (Sprint 284)
    mapping_trace: list[MappingTraceEntry] = field(default_factory=list)
    # Derived amounts for ratio computation (Sprint 488)
    depreciation_amount: Decimal = ZERO
    interest_expense: Decimal = ZERO
    # Prior period totals (Sprint 488)
    has_prior_period: bool = False
    prior_total_assets: Decimal = ZERO
    prior_total_liabilities: Decimal = ZERO
    prior_total_equity: Decimal = ZERO
    prior_total_revenue: Decimal = ZERO
    prior_gross_profit: Decimal = ZERO
    prior_operating_income: Decimal = ZERO
    prior_net_income: Decimal = ZERO
    # Pre-closing TB note (Sprint 535 P2-3)
    is_pre_closing: bool = False
    pre_closing_note: str = ""
    # Metadata
    entity_name: str = ""
    period_end: str = ""

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""

        def _item_dict(item: StatementLineItem) -> dict:
            d = {
                "label": item.label,
                "amount": item.amount,
                "indent_level": item.indent_level,
                "is_subtotal": item.is_subtotal,
                "is_total": item.is_total,
                "lead_sheet_ref": item.lead_sheet_ref,
            }
            if item.prior_amount is not None:
                d["prior_amount"] = item.prior_amount
            return d

        result = {
            "balance_sheet": [_item_dict(item) for item in self.balance_sheet],
            "income_statement": [_item_dict(item) for item in self.income_statement],
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "is_balanced": self.is_balanced,
            "balance_difference": self.balance_difference,
            "total_revenue": self.total_revenue,
            "gross_profit": self.gross_profit,
            "operating_income": self.operating_income,
            "net_income": self.net_income,
            "depreciation_amount": self.depreciation_amount,
            "interest_expense": self.interest_expense,
            "has_prior_period": self.has_prior_period,
            "is_pre_closing": self.is_pre_closing,
            "pre_closing_note": self.pre_closing_note,
            "entity_name": self.entity_name,
            "period_end": self.period_end,
        }
        if self.cash_flow_statement is not None:
            result["cash_flow_statement"] = self.cash_flow_statement.to_dict()
        if self.statement_of_changes_in_equity is not None:
            result["statement_of_changes_in_equity"] = self.statement_of_changes_in_equity.to_dict()
        if self.mapping_trace:
            result["mapping_trace"] = [
                {
                    "statement": entry.statement,
                    "line_label": entry.line_label,
                    "lead_sheet_ref": entry.lead_sheet_ref,
                    "lead_sheet_name": entry.lead_sheet_name,
                    "statement_amount": entry.statement_amount,
                    "account_count": entry.account_count,
                    "accounts": [
                        {
                            "account_name": acct.account_name,
                            "debit": acct.debit,
                            "credit": acct.credit,
                            "net_balance": acct.net_balance,
                            "confidence": acct.confidence,
                            "matched_keywords": acct.matched_keywords,
                        }
                        for acct in entry.accounts
                    ],
                    "is_tied": entry.is_tied,
                    "tie_difference": entry.tie_difference,
                    "raw_aggregate": entry.raw_aggregate,
                    "sign_correction_applied": entry.sign_correction_applied,
                }
                for entry in self.mapping_trace
            ]
        return result


class FinancialStatementBuilder:
    """
    Builds formatted financial statements from lead sheet groupings.

    Accepts the serialized dict form of LeadSheetGrouping (not the dataclass),
    as produced by lead_sheet_grouping_to_dict().
    """

    # Credit-normal letters: statement displays negated net_balance
    SIGN_CORRECTED_LETTERS: set[str] = {"G", "H", "I", "J", "K", "L", "O"}

    def __init__(
        self,
        lead_sheet_grouping: dict,
        entity_name: str = "",
        period_end: str = "",
        prior_lead_sheet_grouping: Optional[dict] = None,
        equity_activity: Optional[list["EquityActivity"]] = None,
    ):
        self.grouping = lead_sheet_grouping
        self.entity_name = entity_name
        self.period_end = period_end
        self.prior_grouping = prior_lead_sheet_grouping
        self.equity_activity = equity_activity or []
        # Index summaries by lead sheet letter for fast lookup
        # Sprint 884 (OUT-05): every lead-sheet balance is rounded half-up to
        # the cent it is shown at before any subtotal is taken, so each
        # subtotal and total is the sum of the lines printed above it.
        self._balance_map: dict[str, Decimal] = {}
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            self._balance_map[letter] = quantize_monetary(summary.get("net_balance"))
        # Index prior period balances
        self._prior_balance_map: dict[str, Decimal] = {}
        if self.prior_grouping:
            for summary in self.prior_grouping.get("summaries", []):
                letter = summary.get("lead_sheet", "")
                self._prior_balance_map[letter] = quantize_monetary(summary.get("net_balance"))
        # Sprint 803: `_account_descriptions` was built here from the same wrong
        # account-name key as `_extract_depreciation`, and never read by anything.
        # Removed rather than corrected — dead code carrying a live bug.

    def _get_lead_sheet_balance(self, letter: str) -> Decimal:
        """Get net_balance for a lead sheet letter, 0 if missing."""
        return self._balance_map.get(letter, ZERO)

    def _get_prior_balance(self, letter: str) -> Decimal:
        """Get prior period net_balance for a lead sheet letter, 0 if missing."""
        return self._prior_balance_map.get(letter, ZERO)

    def _unclosed_earnings(self, balance: "Callable[[str], Decimal]") -> Decimal:
        """Current-period earnings still open on the TB, i.e. not yet in equity.

        Sprint 867: a pre-closing TB carries the period's revenue and expenses
        on lead sheets L-O, so the equity accounts on K exclude the period's
        result and a balanced TB showed "OUT OF BALANCE" by exactly its net
        income. A balance sheet presents equity including the period's result,
        so the statement adds it as its own equity line. Which TBs count as
        "unclosed" is the shared rule the ratios and the Key Metrics
        disclosure already use (``ratio_engine.unclosed_earnings_adjustment``):
        none when income-statement balances are zero, none when equity already
        balances the sheet without them (earnings already closed), otherwise
        the period's net income.
        """
        from ratio_engine import unclosed_earnings_adjustment

        assets = sum((balance(ls) for ls in ["A", "B", "C", "D", "E", "F"]), ZERO)
        liabilities = sum((-balance(ls) for ls in ["G", "H", "I", "J"]), ZERO)
        equity_accounts = -balance("K")
        net_income = -balance("L") - balance("M") - balance("N") - balance("O")
        return unclosed_earnings_adjustment(assets, liabilities, equity_accounts, net_income)

    def build(self) -> FinancialStatements:
        """Build complete financial statements."""
        balance_sheet = self._build_balance_sheet()
        income_statement = self._build_income_statement()

        # Calculate totals from raw lead sheet balances
        # Assets: A-F, positive net_balance = asset
        current_assets = sum((self._get_lead_sheet_balance(ls) for ls in ["A", "B", "C", "D"]), ZERO)
        noncurrent_assets = sum((self._get_lead_sheet_balance(ls) for ls in ["E", "F"]), ZERO)
        total_assets = current_assets + noncurrent_assets

        # Liabilities: G-J, negative net_balance → flip sign
        current_liabilities = sum((-self._get_lead_sheet_balance(ls) for ls in ["G", "H"]), ZERO)
        noncurrent_liabilities = sum((-self._get_lead_sheet_balance(ls) for ls in ["I", "J"]), ZERO)
        total_liabilities = current_liabilities + noncurrent_liabilities

        # Equity: K, negative net_balance → flip sign, plus current-period
        # earnings not yet closed to retained earnings (Sprint 867).
        equity_accounts = -self._get_lead_sheet_balance("K")
        unclosed_earnings = self._unclosed_earnings(self._get_lead_sheet_balance)
        total_equity = equity_accounts + unclosed_earnings

        # Balance check
        balance_difference = total_assets - (total_liabilities + total_equity)
        is_balanced = abs(balance_difference) < BALANCE_TOLERANCE

        # Income Statement totals
        total_revenue = -self._get_lead_sheet_balance("L")  # Credits → positive
        cogs = self._get_lead_sheet_balance("M")  # Debits → positive
        gross_profit = total_revenue - cogs
        operating_expenses = self._get_lead_sheet_balance("N")  # Debits → positive
        operating_income = gross_profit - operating_expenses
        other_net = -self._get_lead_sheet_balance("O")  # Credits = income
        net_income = operating_income + other_net

        # Derived amounts for ratios (Sprint 488)
        depreciation = self._extract_depreciation()
        interest_expense = self._extract_interest_expense()

        # Prior period totals (Sprint 488)
        has_prior = bool(self.prior_grouping)
        prior_total_assets = ZERO
        prior_total_liabilities = ZERO
        prior_total_equity = ZERO
        prior_total_revenue = ZERO
        prior_gross_profit = ZERO
        prior_operating_income = ZERO
        prior_net_income = ZERO
        if has_prior:
            prior_ca = sum((self._get_prior_balance(ls) for ls in ["A", "B", "C", "D"]), ZERO)
            prior_nca = sum((self._get_prior_balance(ls) for ls in ["E", "F"]), ZERO)
            prior_total_assets = prior_ca + prior_nca
            prior_cl = sum((-self._get_prior_balance(ls) for ls in ["G", "H"]), ZERO)
            prior_ncl = sum((-self._get_prior_balance(ls) for ls in ["I", "J"]), ZERO)
            prior_total_liabilities = prior_cl + prior_ncl
            prior_total_equity = -self._get_prior_balance("K") + self._unclosed_earnings(self._get_prior_balance)
            prior_total_revenue = -self._get_prior_balance("L")
            prior_cogs = self._get_prior_balance("M")
            prior_gross_profit = prior_total_revenue - prior_cogs
            prior_opex = self._get_prior_balance("N")
            prior_operating_income = prior_gross_profit - prior_opex
            prior_other = -self._get_prior_balance("O")
            prior_net_income = prior_operating_income + prior_other

        # Cash Flow Statement (Sprint 83)
        # Sprint 882 (TQ-02): the equity movement is between the two balance
        # sheets' total equity, each including its own unclosed earnings.
        equity_change = (total_equity - prior_total_equity) if has_prior else ZERO
        cash_flow = self._build_cash_flow_statement(net_income, equity_change)

        # Statement of Changes in Equity (Sprint 638)
        # Sprint 867: on a pre-closing TB the period's result is part of
        # retained earnings' ending balance, so the rollforward reconciles and
        # its ending equity equals the balance sheet's.
        prior_unclosed = self._unclosed_earnings(self._get_prior_balance) if has_prior else ZERO
        soce = self._build_soce(
            net_income,
            total_equity,
            prior_total_equity,
            unclosed_earnings=unclosed_earnings,
            prior_unclosed_earnings=prior_unclosed,
        )

        # Sprint 535 P2-3: Detect pre-closing TB imbalance
        # In a pre-closing TB, balance_difference ≈ net_income because
        # revenue/expense accounts haven't been closed to retained earnings.
        # Sprint 867: the period's result is now presented in equity, so a
        # pre-closing TB balances; the note says what was added and why.
        is_pre_closing = abs(unclosed_earnings) > 0.01
        pre_closing_note = ""
        if is_pre_closing:
            result_word = "net loss" if unclosed_earnings < 0 else "net income"
            pre_closing_note = (
                "Revenue and expense accounts carry open balances on this trial balance, so "
                f"Equity includes the period's {result_word} of ${abs(unclosed_earnings):,.2f}, "
                "calculated from lead sheets L-O, as a separate line."
            )

        statements = FinancialStatements(
            balance_sheet=balance_sheet,
            income_statement=income_statement,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            is_balanced=is_balanced,
            balance_difference=balance_difference,
            total_revenue=total_revenue,
            gross_profit=gross_profit,
            operating_income=operating_income,
            net_income=net_income,
            depreciation_amount=depreciation,
            interest_expense=interest_expense,
            has_prior_period=has_prior,
            prior_total_assets=prior_total_assets,
            prior_total_liabilities=prior_total_liabilities,
            prior_total_equity=prior_total_equity,
            prior_total_revenue=prior_total_revenue,
            prior_gross_profit=prior_gross_profit,
            prior_operating_income=prior_operating_income,
            prior_net_income=prior_net_income,
            cash_flow_statement=cash_flow,
            statement_of_changes_in_equity=soce,
            is_pre_closing=is_pre_closing,
            pre_closing_note=pre_closing_note,
            entity_name=self.entity_name,
            period_end=self.period_end,
        )

        # Account-to-Statement Mapping Trace (Sprint 284)
        statements.mapping_trace = self._build_mapping_trace(statements)

        return statements

    def _prior_display(self, letter: str, sign_flip: bool = False) -> Optional[Decimal]:
        """Get prior period display amount, or None if no prior data."""
        if not self.prior_grouping:
            return None
        bal = self._get_prior_balance(letter)
        return -bal if sign_flip else bal

    def _build_balance_sheet(self) -> list[StatementLineItem]:
        """Build Balance Sheet line items from lead sheets A-K."""
        lines: list[StatementLineItem] = []
        has_prior = bool(self.prior_grouping)

        # ── ASSETS ──
        lines.append(StatementLineItem("ASSETS", ZERO, indent_level=0))

        # Current Assets
        lines.append(StatementLineItem("Current Assets", ZERO, indent_level=0))
        cash = self._get_lead_sheet_balance("A")
        receivables = self._get_lead_sheet_balance("B")
        inventory = self._get_lead_sheet_balance("C")
        prepaid = self._get_lead_sheet_balance("D")

        lines.append(
            StatementLineItem(
                "Cash and Cash Equivalents",
                cash,
                indent_level=1,
                lead_sheet_ref="A",
                prior_amount=self._prior_display("A"),
            )
        )
        lines.append(
            StatementLineItem(
                "Receivables", receivables, indent_level=1, lead_sheet_ref="B", prior_amount=self._prior_display("B")
            )
        )
        lines.append(
            StatementLineItem(
                "Inventory", inventory, indent_level=1, lead_sheet_ref="C", prior_amount=self._prior_display("C")
            )
        )
        lines.append(
            StatementLineItem(
                "Prepaid Expenses", prepaid, indent_level=1, lead_sheet_ref="D", prior_amount=self._prior_display("D")
            )
        )

        total_current_assets = cash + receivables + inventory + prepaid
        prior_tca = None
        if has_prior:
            prior_tca = sum((self._get_prior_balance(ls) for ls in ["A", "B", "C", "D"]), ZERO)
        lines.append(
            StatementLineItem(
                "Total Current Assets", total_current_assets, indent_level=1, is_subtotal=True, prior_amount=prior_tca
            )
        )

        # Non-Current Assets
        lines.append(StatementLineItem("Non-Current Assets", ZERO, indent_level=0))
        ppe = self._get_lead_sheet_balance("E")
        intangibles = self._get_lead_sheet_balance("F")

        lines.append(
            StatementLineItem(
                "Property, Plant & Equipment",
                ppe,
                indent_level=1,
                lead_sheet_ref="E",
                prior_amount=self._prior_display("E"),
            )
        )
        lines.append(
            StatementLineItem(
                "Other Assets & Intangibles",
                intangibles,
                indent_level=1,
                lead_sheet_ref="F",
                prior_amount=self._prior_display("F"),
            )
        )

        total_noncurrent_assets = ppe + intangibles
        prior_tnca = None
        if has_prior:
            prior_tnca = sum((self._get_prior_balance(ls) for ls in ["E", "F"]), ZERO)
        lines.append(
            StatementLineItem(
                "Total Non-Current Assets",
                total_noncurrent_assets,
                indent_level=1,
                is_subtotal=True,
                prior_amount=prior_tnca,
            )
        )

        total_assets = total_current_assets + total_noncurrent_assets
        prior_ta = None
        if has_prior:
            prior_ta = (prior_tca or ZERO) + (prior_tnca or ZERO)
        lines.append(
            StatementLineItem("TOTAL ASSETS", total_assets, indent_level=0, is_total=True, prior_amount=prior_ta)
        )

        # ── LIABILITIES & EQUITY ──
        lines.append(StatementLineItem("LIABILITIES & EQUITY", ZERO, indent_level=0))

        # Current Liabilities (flip sign)
        lines.append(StatementLineItem("Current Liabilities", ZERO, indent_level=0))
        ap = -self._get_lead_sheet_balance("G")
        other_cl = -self._get_lead_sheet_balance("H")

        lines.append(
            StatementLineItem(
                "AP & Accrued Liabilities",
                ap,
                indent_level=1,
                lead_sheet_ref="G",
                prior_amount=self._prior_display("G", sign_flip=True),
            )
        )
        lines.append(
            StatementLineItem(
                "Other Current Liabilities",
                other_cl,
                indent_level=1,
                lead_sheet_ref="H",
                prior_amount=self._prior_display("H", sign_flip=True),
            )
        )

        total_current_liabilities = ap + other_cl
        prior_tcl = None
        if has_prior:
            prior_tcl = sum((-self._get_prior_balance(ls) for ls in ["G", "H"]), ZERO)
        lines.append(
            StatementLineItem(
                "Total Current Liabilities",
                total_current_liabilities,
                indent_level=1,
                is_subtotal=True,
                prior_amount=prior_tcl,
            )
        )

        # Non-Current Liabilities (flip sign)
        lines.append(StatementLineItem("Non-Current Liabilities", ZERO, indent_level=0))
        lt_debt = -self._get_lead_sheet_balance("I")
        other_lt = -self._get_lead_sheet_balance("J")

        lines.append(
            StatementLineItem(
                "Long-term Debt",
                lt_debt,
                indent_level=1,
                lead_sheet_ref="I",
                prior_amount=self._prior_display("I", sign_flip=True),
            )
        )
        lines.append(
            StatementLineItem(
                "Other Long-term Liabilities",
                other_lt,
                indent_level=1,
                lead_sheet_ref="J",
                prior_amount=self._prior_display("J", sign_flip=True),
            )
        )

        total_noncurrent_liabilities = lt_debt + other_lt
        prior_tncl = None
        if has_prior:
            prior_tncl = sum((-self._get_prior_balance(ls) for ls in ["I", "J"]), ZERO)
        lines.append(
            StatementLineItem(
                "Total Non-Current Liabilities",
                total_noncurrent_liabilities,
                indent_level=1,
                is_subtotal=True,
                prior_amount=prior_tncl,
            )
        )

        total_liabilities = total_current_liabilities + total_noncurrent_liabilities
        prior_tl = None
        if has_prior:
            prior_tl = (prior_tcl or ZERO) + (prior_tncl or ZERO)
        lines.append(
            StatementLineItem(
                "Total Liabilities", total_liabilities, indent_level=0, is_subtotal=True, prior_amount=prior_tl
            )
        )

        # Equity (flip sign)
        equity = -self._get_lead_sheet_balance("K")
        lines.append(
            StatementLineItem(
                "Stockholders' Equity",
                equity,
                indent_level=1,
                lead_sheet_ref="K",
                prior_amount=self._prior_display("K", sign_flip=True),
            )
        )

        # Sprint 867: current-period earnings not yet closed (see _unclosed_earnings).
        unclosed = self._unclosed_earnings(self._get_lead_sheet_balance)
        prior_unclosed = self._unclosed_earnings(self._get_prior_balance) if has_prior else ZERO
        if abs(unclosed) > 0.01 or abs(prior_unclosed) > 0.01:
            lines.append(
                StatementLineItem(
                    UNCLOSED_EARNINGS_LABEL,
                    unclosed,
                    indent_level=1,
                    prior_amount=prior_unclosed if has_prior else None,
                )
            )

        total_le = total_liabilities + equity + unclosed
        prior_tle = None
        if has_prior:
            prior_tle = (prior_tl or ZERO) + (-self._get_prior_balance("K")) + prior_unclosed
        lines.append(
            StatementLineItem(
                "TOTAL LIABILITIES & EQUITY", total_le, indent_level=0, is_total=True, prior_amount=prior_tle
            )
        )

        return lines

    def _build_income_statement(self) -> list[StatementLineItem]:
        """Build Income Statement line items from lead sheets L-O."""
        lines: list[StatementLineItem] = []
        has_prior = bool(self.prior_grouping)

        # Revenue (flip sign: credits → positive)
        revenue = -self._get_lead_sheet_balance("L")
        lines.append(
            StatementLineItem(
                "Revenue",
                revenue,
                indent_level=0,
                lead_sheet_ref="L",
                prior_amount=self._prior_display("L", sign_flip=True),
            )
        )

        # COGS (debits → positive, displayed as expense)
        cogs = self._get_lead_sheet_balance("M")
        lines.append(
            StatementLineItem(
                "Cost of Goods Sold", cogs, indent_level=0, lead_sheet_ref="M", prior_amount=self._prior_display("M")
            )
        )

        # Gross Profit
        gross_profit = revenue - cogs
        prior_gp = None
        if has_prior:
            prior_gp = (-self._get_prior_balance("L")) - self._get_prior_balance("M")
        lines.append(
            StatementLineItem("GROSS PROFIT", gross_profit, indent_level=0, is_subtotal=True, prior_amount=prior_gp)
        )

        # Operating Expenses (debits → positive)
        opex = self._get_lead_sheet_balance("N")
        lines.append(
            StatementLineItem(
                "Operating Expenses", opex, indent_level=0, lead_sheet_ref="N", prior_amount=self._prior_display("N")
            )
        )

        # Operating Income
        operating_income = gross_profit - opex
        prior_oi = None
        if has_prior:
            prior_oi = (prior_gp or ZERO) - self._get_prior_balance("N")
        lines.append(
            StatementLineItem(
                "OPERATING INCOME", operating_income, indent_level=0, is_subtotal=True, prior_amount=prior_oi
            )
        )

        # Other Income / (Expense), Net (flip sign: credits = income)
        other_net = -self._get_lead_sheet_balance("O")
        lines.append(
            StatementLineItem(
                "Other Income / (Expense), Net",
                other_net,
                indent_level=0,
                lead_sheet_ref="O",
                prior_amount=self._prior_display("O", sign_flip=True),
            )
        )

        # Net Income
        net_income = operating_income + other_net
        prior_ni = None
        if has_prior:
            prior_ni = (prior_oi or ZERO) + (-self._get_prior_balance("O"))
        lines.append(StatementLineItem("NET INCOME", net_income, indent_level=0, is_total=True, prior_amount=prior_ni))

        return lines

    # ─── Account-to-Statement Mapping Trace (Sprint 284) ────────────

    # Maps lead sheet letters to their statement line labels.
    # (statement, line_label, lead_sheet_ref)
    STATEMENT_LINE_MAP: list[tuple[str, str, str]] = [
        ("Balance Sheet", "Cash and Cash Equivalents", "A"),
        ("Balance Sheet", "Receivables", "B"),
        ("Balance Sheet", "Inventory", "C"),
        ("Balance Sheet", "Prepaid Expenses", "D"),
        ("Balance Sheet", "Property, Plant & Equipment", "E"),
        ("Balance Sheet", "Other Assets & Intangibles", "F"),
        ("Balance Sheet", "AP & Accrued Liabilities", "G"),
        ("Balance Sheet", "Other Current Liabilities", "H"),
        ("Balance Sheet", "Long-term Debt", "I"),
        ("Balance Sheet", "Other Long-term Liabilities", "J"),
        ("Balance Sheet", "Stockholders' Equity", "K"),
        ("Income Statement", "Revenue", "L"),
        ("Income Statement", "Cost of Goods Sold", "M"),
        ("Income Statement", "Operating Expenses", "N"),
        ("Income Statement", "Other Income / (Expense), Net", "O"),
    ]

    def _build_mapping_trace(self, statements: "FinancialStatements") -> list[MappingTraceEntry]:
        """Build mapping trace linking each statement line to its contributing TB accounts."""
        # Index summaries by lead sheet letter
        summary_index: dict[str, dict] = {}
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            if letter:
                summary_index[letter] = summary

        # Index statement amounts by lead sheet ref for tie-out comparison
        stmt_amounts: dict[str, Decimal] = {}
        for item in statements.balance_sheet:
            if item.lead_sheet_ref:
                stmt_amounts[item.lead_sheet_ref] = item.amount
        for item in statements.income_statement:
            if item.lead_sheet_ref:
                stmt_amounts[item.lead_sheet_ref] = item.amount

        trace: list[MappingTraceEntry] = []

        for stmt_name, line_label, ref in self.STATEMENT_LINE_MAP:
            summary = summary_index.get(ref)
            statement_amount = stmt_amounts.get(ref, ZERO)

            if summary is None:
                # Lead sheet not present — empty entry, trivially tied
                trace.append(
                    MappingTraceEntry(
                        statement=stmt_name,
                        line_label=line_label,
                        lead_sheet_ref=ref,
                        lead_sheet_name=line_label,
                        statement_amount=statement_amount,
                        account_count=0,
                        is_tied=True,
                        tie_difference=ZERO,
                        sign_correction_applied=ref in self.SIGN_CORRECTED_LETTERS,
                    )
                )
                continue

            lead_sheet_name = summary.get("name", line_label)
            raw_accounts = summary.get("accounts", [])
            accounts: list[MappingTraceAccount] = []
            net_values: list[Decimal] = []

            for acct in raw_accounts:
                if not isinstance(acct, dict):
                    continue
                acct_name = str(acct.get("account", acct.get("name", "Unknown")))
                debit = safe_decimal(acct.get("debit"))
                credit = safe_decimal(acct.get("credit"))
                net = debit - credit
                net_values.append(net)
                confidence = acct.get("confidence", 1.0)
                keywords = acct.get("matched_keywords", [])
                accounts.append(
                    MappingTraceAccount(
                        account_name=acct_name,
                        debit=debit,
                        credit=credit,
                        net_balance=net,
                        confidence=confidence,
                        matched_keywords=keywords,
                    )
                )

            raw_sum = sum(net_values, ZERO)
            sign_corrected = ref in self.SIGN_CORRECTED_LETTERS

            # Tie-out: compare raw account sum to the summary net_balance
            summary_net = safe_decimal(summary.get("net_balance"))
            tie_diff = abs(raw_sum - summary_net)
            is_tied = tie_diff < BALANCE_TOLERANCE

            trace.append(
                MappingTraceEntry(
                    statement=stmt_name,
                    line_label=line_label,
                    lead_sheet_ref=ref,
                    lead_sheet_name=lead_sheet_name,
                    statement_amount=statement_amount,
                    account_count=len(accounts),
                    accounts=accounts,
                    is_tied=is_tied,
                    tie_difference=tie_diff,
                    raw_aggregate=raw_sum,
                    sign_correction_applied=sign_corrected,
                )
            )

        return trace

    # ─── Cash Flow Statement (Sprint 83) ─────────────────────────────

    # Lead sheets scanned for the depreciation add-back, in precedence order.
    # Sprint 803: expense sheets first. A period expense is what the ASC 230 add-back
    # wants; E/F are scanned only as a fallback for charts that park an amortization
    # line on an asset sheet.
    DEPRECIATION_SCAN_ORDER: tuple[tuple[str, ...], ...] = (("N", "O"), ("E", "F"))

    def _extract_depreciation(self) -> Decimal:
        """
        Detect depreciation/amortization from account names in OpEx (N), Other (O),
        and — only if neither carries one — Non-Current Assets (E, F).

        Returns the period depreciation and amortization expense as a positive number,
        summed across every matching account, or 0 if none is separately identifiable.

        Sprint 803 (finding A-5) fixed three defects here:
        - The account name was read from the key ``name``, which the serialized grouping
          never carries — it carries ``account`` (``lead_sheet_mapping.lead_sheet_grouping_to_dict``).
          Every keyword was therefore compared against the empty string and this method
          returned 0.0 for every trial balance ever uploaded. The sibling
          ``_extract_interest_expense`` had already been corrected; this one had not.
        - With the key fixed, lead sheet E matches ``accumulated depreciation`` — a
          *cumulative* contra-asset. Adding that back would be a worse number than 0.0,
          so accumulated accounts are skipped and expense sheets are scanned first.
        - The first match won and returned. A trial balance carrying separate
          depreciation and amortization lines now adds back both.
        """
        for letters in self.DEPRECIATION_SCAN_ORDER:
            total = ZERO
            for summary in self.grouping.get("summaries", []):
                if summary.get("lead_sheet", "") not in letters:
                    continue
                for acct in summary.get("accounts", []):
                    if not isinstance(acct, dict):
                        continue
                    # Serialized groupings key the name as "account"; some callers
                    # (and older fixtures) pass "name". Accept either, as the
                    # interest-expense sibling does.
                    name = (acct.get("name", "") or acct.get("account", "")).lower()
                    if not name:
                        continue
                    # "Accumulated Depreciation" / "Accum Amort" are contra-asset
                    # balances, not period expense. Never add them back.
                    if "accum" in name:
                        continue
                    if any(keyword in name for keyword, _is_phrase in DEPRECIATION_KEYWORDS):
                        balance = safe_decimal(acct.get("net_balance"))
                        if balance == ZERO:
                            balance = safe_decimal(acct.get("debit")) - safe_decimal(acct.get("credit"))
                        total += abs(balance)
            if total > ZERO:
                return quantize_monetary(total)
        return ZERO

    def _extract_interest_expense(self) -> Decimal:
        """
        Detect interest expense from account descriptions in Other Income/Expense (O)
        and Operating Expenses (N).

        Returns the estimated interest expense as a positive number.
        If not separately identifiable, returns 0.
        """
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            if letter not in ("N", "O"):
                continue
            accounts = summary.get("accounts", [])
            for acct in accounts:
                if not isinstance(acct, dict):
                    continue
                name = (acct.get("name", "") or acct.get("account", "")).lower()
                for keyword, is_phrase in INTEREST_EXPENSE_KEYWORDS:
                    if is_phrase and keyword in name:
                        balance = safe_decimal(acct.get("net_balance"))
                        if balance == ZERO:
                            balance = safe_decimal(acct.get("debit")) - safe_decimal(acct.get("credit"))
                        return quantize_monetary(abs(balance))
        return ZERO

    def _compute_balance_change(self, letter: str) -> Decimal:
        """
        Compute the change in a lead sheet balance: current - prior.

        Returns 0 if no prior period is available.
        """
        if not self.prior_grouping:
            return ZERO
        current = self._get_lead_sheet_balance(letter)
        prior = self._get_prior_balance(letter)
        return current - prior

    def _build_operating_items(self, net_income: Decimal, has_prior: bool, notes: list[str]) -> list[CashFlowLineItem]:
        """Build operating activity line items (indirect method).

        Starts with net income, adds back non-cash items (depreciation),
        then adjusts for working capital changes (B, C, D, G, H).
        Mutates notes list with depreciation/prior-period warnings.
        """
        items: list[CashFlowLineItem] = []

        # Net Income (starting point)
        items.append(
            CashFlowLineItem(
                "Net Income",
                net_income,
                source="computed",
                indent_level=1,
            )
        )

        # Adjustments for non-cash items
        depreciation = self._extract_depreciation()
        if depreciation > 0:
            items.append(
                CashFlowLineItem(
                    "Depreciation & Amortization",
                    depreciation,
                    source="E/N",
                    indent_level=1,
                )
            )
        else:
            notes.append("Depreciation not separately identified in trial balance")

        # Working capital changes (require prior period)
        if has_prior:
            # Change in Receivables (B): increase = cash outflow (negative)
            delta_b = self._compute_balance_change("B")
            if abs(delta_b) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Accounts Receivable",
                        -delta_b,  # Asset increase = cash outflow
                        source="B",
                        indent_level=1,
                    )
                )

            # Change in Inventory (C): increase = cash outflow
            delta_c = self._compute_balance_change("C")
            if abs(delta_c) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Inventory",
                        -delta_c,
                        source="C",
                        indent_level=1,
                    )
                )

            # Change in Prepaid Expenses (D): increase = cash outflow
            delta_d = self._compute_balance_change("D")
            if abs(delta_d) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Prepaid Expenses",
                        -delta_d,
                        source="D",
                        indent_level=1,
                    )
                )

            # Change in Accounts Payable (G): liability increase = cash inflow
            # G has negative net_balance (credit), so change is also negative
            # When liability increases: more negative → delta is negative → flip = positive inflow
            delta_g = self._compute_balance_change("G")
            if abs(delta_g) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Accounts Payable",
                        -delta_g,  # Liability: more negative = increase = cash inflow
                        source="G",
                        indent_level=1,
                    )
                )

            # Change in Accrued Liabilities (H): same as AP
            delta_h = self._compute_balance_change("H")
            if abs(delta_h) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Accrued Liabilities",
                        -delta_h,
                        source="H",
                        indent_level=1,
                    )
                )
        else:
            notes.append("Prior period required for working capital changes")

        return items

    # Sprint 882 (TQ-03): accumulated depreciation / amortization accounts sit on
    # the asset lead sheets (E: "accumulated depreciation"; F: "amortization").
    # Same marker _extract_depreciation uses to skip them.
    ACCUMULATED_MARKER = "accum"

    @staticmethod
    def _account_net(acct: dict) -> Decimal:
        """Debit-positive net balance of one serialized account (exact, Sprint 884)."""
        if acct.get("net_balance") is not None:
            return safe_decimal(acct.get("net_balance"))
        return safe_decimal(acct.get("debit")) - safe_decimal(acct.get("credit"))

    def _gross_and_accumulated(self, grouping: Optional[dict], letter: str) -> tuple[Decimal, Decimal]:
        """Split a lead sheet's net balance into (gross cost, accumulated) parts.

        Accumulated is returned debit-positive (so normally negative). A summary
        without per-account detail is all gross — nothing can be split out.
        """
        if not grouping:
            return ZERO, ZERO
        for summary in grouping.get("summaries", []):
            if summary.get("lead_sheet") != letter:
                continue
            accounts = [a for a in summary.get("accounts", []) or [] if isinstance(a, dict)]
            if not accounts:
                return safe_decimal(summary.get("net_balance")), ZERO
            gross = ZERO
            accumulated = ZERO
            for acct in accounts:
                name = str(acct.get("account") or acct.get("name") or "").lower()
                if self.ACCUMULATED_MARKER in name:
                    accumulated += self._account_net(acct)
                else:
                    gross += self._account_net(acct)
            # Keep the summary as the authority on the total; any rounding
            # difference stays with gross cost.
            gross += safe_decimal(summary.get("net_balance")) - (gross + accumulated)
            return gross, accumulated
        return ZERO, ZERO

    def _build_investing_items(self, has_prior: bool, notes: Optional[list[str]] = None) -> list[CashFlowLineItem]:
        """Build investing activity line items.

        Sprint 882 (TQ-03): investing cash is based on movements in *gross*
        fixed assets. Lead sheet E carries accumulated depreciation, so the old
        ``-ΔE`` turned a fall in net PPE caused only by depreciation into a cash
        inflow labelled "Capital Expenditures (PPE)" — on top of the operating
        add-back for the same depreciation.

        - Gross PPE rose (or held) and accumulated depreciation/amortization rose
          by exactly the period's identified charge: the gross increase is
          purchases, shown as "Purchases of Property, Plant & Equipment".
        - Otherwise (gross PPE fell, or accumulated depreciation moved by other
          than the charge — a disposal relieves it): purchases and disposals
          cannot be told apart from the trial balance alone. The line shows the
          movement not explained by depreciation, under a label that says so,
          with a note — never a capital-expenditure figure.
        """
        items: list[CashFlowLineItem] = []
        if not has_prior:
            return items

        gross_e, accum_e = self._gross_and_accumulated(self.grouping, "E")
        prior_gross_e, prior_accum_e = self._gross_and_accumulated(self.prior_grouping, "E")
        gross_f, accum_f = self._gross_and_accumulated(self.grouping, "F")
        prior_gross_f, prior_accum_f = self._gross_and_accumulated(self.prior_grouping, "F")

        gross_ppe_change = gross_e - prior_gross_e
        # Credit-positive: how much accumulated depreciation/amortization grew.
        accumulated_increase = -((accum_e + accum_f) - (prior_accum_e + prior_accum_f))
        depreciation = self._extract_depreciation()
        unexplained = accumulated_increase - depreciation

        separable = gross_ppe_change >= -0.005 and abs(unexplained) < 0.01
        if separable:
            if abs(gross_ppe_change) > 0.005:
                items.append(
                    CashFlowLineItem(
                        "Purchases of Property, Plant & Equipment",
                        -gross_ppe_change,  # Gross asset increase = cash outflow
                        source="E",
                        indent_level=1,
                    )
                )
        else:
            net_movement = -gross_ppe_change + unexplained
            if abs(net_movement) > 0.005:
                items.append(
                    CashFlowLineItem(
                        "Net Change in Property, Plant & Equipment (Purchases and Disposals Not Separable)",
                        net_movement,
                        source="E",
                        indent_level=1,
                    )
                )
            if notes is not None:
                notes.append(
                    "Purchases and disposals of property, plant and equipment cannot be told apart "
                    "from the trial balance alone: gross cost fell, or accumulated depreciation moved "
                    "by other than the period's depreciation. The investing line is the change in "
                    "property, plant and equipment not explained by depreciation; any gain or loss "
                    "on disposal remains in net income under operating activities."
                )

        # Change in Other Non-Current Assets (F), at cost — accumulated
        # amortization is excluded for the same reason as above.
        delta_f = gross_f - prior_gross_f
        if abs(delta_f) > 0.005:
            items.append(
                CashFlowLineItem(
                    "Change in Other Non-Current Assets",
                    -delta_f,
                    source="F",
                    indent_level=1,
                )
            )

        return items

    def _build_financing_items(
        self, net_income: Decimal, has_prior: bool, equity_change: Decimal = ZERO
    ) -> list[CashFlowLineItem]:
        """Build financing activity line items.

        Changes in long-term debt (I, J) and equity excluding retained earnings (K).
        ``equity_change`` is current less prior total equity as the balance
        sheets present it, i.e. each including its own unclosed earnings.
        """
        items: list[CashFlowLineItem] = []

        if has_prior:
            # Change in Long-Term Debt (I): liability increase = cash inflow
            # I has negative net_balance; more negative = increase
            delta_i = self._compute_balance_change("I")
            if abs(delta_i) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Long-Term Debt",
                        -delta_i,  # More negative = increase = cash inflow
                        source="I",
                        indent_level=1,
                    )
                )

            # Change in Short-Term Debt / Other LT Liabilities (J)
            delta_j = self._compute_balance_change("J")
            if abs(delta_j) > MONETARY_NEAR_ZERO:
                items.append(
                    CashFlowLineItem(
                        "Change in Other Long-Term Liabilities",
                        -delta_j,
                        source="J",
                        indent_level=1,
                    )
                )

            # Change in equity excluding the period's result: owner
            # contributions less distributions/dividends.
            # Sprint 882 (TQ-02): this used the change in the equity accounts
            # (K) less net income. On a pre-closing TB the period's earnings are
            # still on L-O and never moved through K, so subtracting them
            # invented a distribution of exactly net income. Both ends now use
            # total equity including unclosed earnings (the balance sheet's
            # figure), so the earnings are in equity on both sides of the
            # subtraction whether or not the books were closed.
            financing_equity_change = equity_change - net_income
            if abs(financing_equity_change) > 0.005:
                items.append(
                    CashFlowLineItem(
                        "Equity Changes (excl. Retained Earnings)",
                        financing_equity_change,
                        source="K",
                        indent_level=1,
                    )
                )

        return items

    # ---------------------------------------------------------------------
    # Sprint 638 — Statement of Changes in Equity
    # ---------------------------------------------------------------------

    # Keyword → component type. Case-insensitive substring match against the
    # account name. First matching rule wins. Unmapped accounts default to
    # retained_earnings AND are added to ``unmapped_accounts`` for review.
    _SOCE_COMPONENT_RULES: tuple[tuple[str, str, str], ...] = (
        ("treasury stock", "treasury_stock", "Treasury Stock"),
        ("treasury shares", "treasury_stock", "Treasury Stock"),
        ("additional paid-in capital", "additional_paid_in_capital", "Additional Paid-In Capital"),
        ("additional paid in capital", "additional_paid_in_capital", "Additional Paid-In Capital"),
        ("paid-in capital", "additional_paid_in_capital", "Additional Paid-In Capital"),
        ("paid in capital", "additional_paid_in_capital", "Additional Paid-In Capital"),
        ("apic", "additional_paid_in_capital", "Additional Paid-In Capital"),
        ("common stock", "common_stock", "Common Stock"),
        ("preferred stock", "common_stock", "Preferred Stock"),
        ("capital stock", "common_stock", "Capital Stock"),
        ("members capital", "common_stock", "Members' Capital"),
        ("members' capital", "common_stock", "Members' Capital"),
        ("partners capital", "common_stock", "Partners' Capital"),
        ("partners' capital", "common_stock", "Partners' Capital"),
        ("owners capital", "common_stock", "Owner's Capital"),
        ("owner's capital", "common_stock", "Owner's Capital"),
        ("retained earnings", "retained_earnings", "Retained Earnings"),
        ("accumulated earnings", "retained_earnings", "Retained Earnings"),
        ("accumulated deficit", "retained_earnings", "Accumulated Deficit"),
        ("accumulated other comprehensive", "aoci", "Accumulated Other Comprehensive Income"),
        ("aoci", "aoci", "Accumulated Other Comprehensive Income"),
        ("oci", "aoci", "Other Comprehensive Income"),
        ("dividends", "retained_earnings", "Dividends"),
        ("distributions", "retained_earnings", "Distributions"),
    )

    @staticmethod
    def _classify_equity_account(account_name: str) -> tuple[str, str, bool]:
        """Return (component_type, default_label, is_explicit_match)."""
        low = (account_name or "").lower()
        for keyword, component_type, label in FinancialStatementBuilder._SOCE_COMPONENT_RULES:
            if keyword in low:
                return component_type, label, True
        return "retained_earnings", "Retained Earnings (unmapped)", False

    @staticmethod
    def _account_name_and_net(acct: dict) -> tuple[str, Decimal]:
        """Name and debit-positive net balance of one lead-sheet account.

        Sprint 867: serialized groupings (``lead_sheet_grouping_to_dict``, i.e.
        every real upload and every export payload) key accounts as
        ``account`` / ``debit`` / ``credit`` with no ``net_balance``. The SOCE
        read only ``name`` / ``net_balance`` — the shape its unit fixtures used
        — so on real data it skipped every equity account. Accept both, as
        the depreciation and interest-expense readers already do.
        """
        name = str(acct.get("account") or acct.get("name") or "").strip()
        if "net_balance" in acct and acct.get("net_balance") is not None:
            net = quantize_monetary(acct.get("net_balance"))
        else:
            net = quantize_monetary(safe_decimal(acct.get("debit")) - safe_decimal(acct.get("credit")))
        return name, net

    def _collect_equity_accounts(self) -> list[dict]:
        """Return the K-lead-sheet account dicts from the current period."""
        for summary in self.grouping.get("summaries", []):
            if summary.get("lead_sheet") == "K":
                accounts = summary.get("accounts", []) or []
                return [a for a in accounts if isinstance(a, dict)]
        return []

    def _collect_prior_equity_accounts(self) -> list[dict]:
        if not self.prior_grouping:
            return []
        for summary in self.prior_grouping.get("summaries", []):
            if summary.get("lead_sheet") == "K":
                accounts = summary.get("accounts", []) or []
                return [a for a in accounts if isinstance(a, dict)]
        return []

    def _build_soce(
        self,
        net_income: Decimal,
        total_equity: Decimal,
        prior_total_equity: Decimal,
        unclosed_earnings: Decimal = ZERO,
        prior_unclosed_earnings: Decimal = ZERO,
    ) -> StatementOfChangesInEquity:
        """Build the Statement of Changes in Equity rollforward.

        Sprint 638: Equity accounts on lead sheet K are classified into
        SOCE components (common stock, APIC, retained earnings, treasury,
        AOCI). Beginning balances come from the prior period lead sheet
        when supplied; ending balances from the current period. Net
        income flows into the retained-earnings component. Explicit
        activity (contributions, distributions, dividends) is accepted
        via ``EquityActivity`` inputs and matched to accounts by name;
        anything not accounted for falls into ``other_movement`` so the
        rollforward balances.

        ``unmapped_accounts`` lists equity accounts whose names didn't
        match any of the SOCE component keywords, so the practitioner
        can review the default classification.
        """
        current_accounts = self._collect_equity_accounts()
        prior_accounts = self._collect_prior_equity_accounts()

        # Build prior-balance lookup by account name (case-insensitive).
        prior_by_name: dict[str, Decimal] = {}
        for acct in prior_accounts:
            prior_name, prior_net = self._account_name_and_net(acct)
            prior_by_name[prior_name.lower()] = prior_net

        # Equity accounts are credit-normal — flip sign so positive values
        # display as equity.
        components: dict[str, EquityComponent] = {}
        unmapped: list[str] = []

        # Explicit activity lookup by account name.
        activity_by_name: dict[str, EquityActivity] = {}
        for act in self.equity_activity:
            activity_by_name[(act.account or "").strip().lower()] = act

        for acct in current_accounts:
            name, account_net = self._account_name_and_net(acct)
            if not name:
                continue
            component_type, label, is_explicit = self._classify_equity_account(name)
            if not is_explicit:
                unmapped.append(name)
            ending = -account_net  # flip sign
            beginning = -prior_by_name.get(name.lower(), ZERO)
            act = activity_by_name.get(name.lower())
            # Callers may still hand in float activity amounts; read them exactly.
            contributions = quantize_monetary(act.contributions) if act else ZERO
            distributions = quantize_monetary(act.distributions) if act else ZERO
            dividends = quantize_monetary(act.dividends) if act else ZERO

            component = components.get(component_type)
            if component is None:
                component = EquityComponent(
                    component_type=component_type,
                    label=label,
                    beginning_balance=beginning,
                    contributions=contributions,
                    distributions=distributions,
                    dividends=dividends,
                    ending_balance=ending,
                )
                components[component_type] = component
            else:
                component.beginning_balance += beginning
                component.contributions += contributions
                component.distributions += distributions
                component.dividends += dividends
                component.ending_balance += ending

        # Attribute net income to retained earnings.
        if net_income:
            re = components.setdefault(
                "retained_earnings",
                EquityComponent(
                    component_type="retained_earnings",
                    label="Retained Earnings",
                    beginning_balance=ZERO,
                    ending_balance=ZERO,
                ),
            )
            re.net_income_allocation += net_income

        # Sprint 867: earnings not yet closed belong to retained earnings —
        # this period's in its ending balance, an unclosed prior period's in
        # its beginning balance — or the rollforward would plug them into
        # other_movement and disagree with the balance sheet.
        if abs(unclosed_earnings) > 0.01 or abs(prior_unclosed_earnings) > 0.01:
            re = components.setdefault(
                "retained_earnings",
                EquityComponent(
                    component_type="retained_earnings",
                    label="Retained Earnings",
                    beginning_balance=ZERO,
                    ending_balance=ZERO,
                ),
            )
            re.ending_balance += unclosed_earnings
            re.beginning_balance += prior_unclosed_earnings

        # OCI movement — if an AOCI component exists, the movement is
        # beginning → ending less explicit contributions / distributions.
        if "aoci" in components:
            aoci = components["aoci"]
            explained = aoci.contributions + aoci.net_income_allocation - aoci.distributions - aoci.dividends
            aoci.other_comprehensive_income = aoci.ending_balance - aoci.beginning_balance - explained

        # Residual for every other component → other_movement so the
        # rollforward balances.
        for component in components.values():
            if component.component_type == "aoci":
                continue
            explained = (
                component.contributions
                + component.net_income_allocation
                - component.distributions
                - component.dividends
            )
            component.other_movement = component.ending_balance - component.beginning_balance - explained
            # Collapse tiny rounding residuals.
            if abs(component.other_movement) < MONETARY_NEAR_ZERO:
                component.other_movement = ZERO

        components_list = list(components.values())
        # Deterministic order: common, APIC, retained, treasury, AOCI, other
        priority = {
            "common_stock": 0,
            "additional_paid_in_capital": 1,
            "retained_earnings": 2,
            "treasury_stock": 3,
            "aoci": 4,
            "other": 5,
        }
        components_list.sort(key=lambda c: priority.get(c.component_type, 99))

        return StatementOfChangesInEquity(
            components=components_list,
            beginning_total_equity=prior_total_equity if self.prior_grouping else ZERO,
            net_income=net_income,
            total_contributions=sum((c.contributions for c in components_list), ZERO),
            total_distributions=sum((c.distributions for c in components_list), ZERO),
            total_dividends=sum((c.dividends for c in components_list), ZERO),
            total_other_comprehensive_income=sum((c.other_comprehensive_income for c in components_list), ZERO),
            total_other_movement=sum((c.other_movement for c in components_list), ZERO),
            ending_total_equity=total_equity,
            unmapped_accounts=unmapped,
        )

    def _build_cash_flow_statement(self, net_income: Decimal, equity_change: Decimal = ZERO) -> CashFlowStatement:
        """
        Build Cash Flow Statement using indirect method (ASC 230 / IAS 7).

        Operating: Start with net income, add back non-cash items, adjust
        for working capital changes.
        Investing: Changes in non-current assets (E, F).
        Financing: Changes in debt (I, J) and equity (K excl. retained earnings).
        """
        has_prior = bool(self.prior_grouping)
        notes: list[str] = []

        # Build activity sections
        operating_items = self._build_operating_items(net_income, has_prior, notes)
        operating_subtotal = sum((item.amount for item in operating_items), ZERO)
        operating = CashFlowSection(
            label="Cash Flows from Operating Activities",
            items=operating_items,
            subtotal=operating_subtotal,
        )

        investing_items = self._build_investing_items(has_prior, notes)
        investing_subtotal = sum((item.amount for item in investing_items), ZERO)
        investing = CashFlowSection(
            label="Cash Flows from Investing Activities",
            items=investing_items,
            subtotal=investing_subtotal,
        )

        financing_items = self._build_financing_items(net_income, has_prior, equity_change)
        financing_subtotal = sum((item.amount for item in financing_items), ZERO)
        financing = CashFlowSection(
            label="Cash Flows from Financing Activities",
            items=financing_items,
            subtotal=financing_subtotal,
        )

        # Reconciliation
        net_change = operating_subtotal + investing_subtotal + financing_subtotal
        ending_cash = self._get_lead_sheet_balance("A")
        beginning_cash = self._get_prior_balance("A") if has_prior else ZERO

        if has_prior:
            expected_ending = beginning_cash + net_change
            reconciliation_diff = ending_cash - expected_ending
            is_reconciled = abs(reconciliation_diff) < BALANCE_TOLERANCE
        else:
            reconciliation_diff = ZERO
            is_reconciled = False
            if not any("Prior period" in n for n in notes):
                notes.append("Prior period required for cash flow reconciliation")

        return CashFlowStatement(
            operating=operating,
            investing=investing,
            financing=financing,
            net_change=net_change,
            beginning_cash=beginning_cash,
            ending_cash=ending_cash,
            is_reconciled=is_reconciled,
            reconciliation_difference=reconciliation_diff,
            has_prior_period=has_prior,
            notes=notes,
        )
