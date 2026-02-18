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
    - Investing: Change in PPE (E) + Other Non-Current Assets (F)
    - Financing: Change in Debt (I, J) + Change in Equity (K excl. retained earnings)

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

import math
from dataclasses import dataclass, field
from typing import Optional

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
    amount: float
    indent_level: int = 0       # 0=section header, 1=line item
    is_subtotal: bool = False
    is_total: bool = False
    lead_sheet_ref: str = ""    # "A", "B", etc.


@dataclass
class CashFlowLineItem:
    """A single line item on the cash flow statement."""
    label: str
    amount: float
    source: str = ""            # lead_sheet_ref or "computed"
    indent_level: int = 1       # 0=section header, 1=line item


@dataclass
class CashFlowSection:
    """A section of the cash flow statement (Operating, Investing, or Financing)."""
    label: str
    items: list[CashFlowLineItem] = field(default_factory=list)
    subtotal: float = 0.0

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
    net_change: float = 0.0
    beginning_cash: float = 0.0
    ending_cash: float = 0.0
    is_reconciled: bool = False
    reconciliation_difference: float = 0.0
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
    debit: float
    credit: float
    net_balance: float
    confidence: float
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class MappingTraceEntry:
    """Maps a financial statement line to its contributing TB accounts."""
    statement: str              # "Balance Sheet" | "Income Statement"
    line_label: str             # e.g. "Cash and Cash Equivalents"
    lead_sheet_ref: str         # "A"
    lead_sheet_name: str        # "Cash and Cash Equivalents"
    statement_amount: float     # sign-corrected display amount
    account_count: int
    accounts: list[MappingTraceAccount] = field(default_factory=list)
    is_tied: bool = True
    tie_difference: float = 0.0
    raw_aggregate: float = 0.0           # Sprint 295: sum of account net balances (pre-sign-correction)
    sign_correction_applied: bool = False # Sprint 295: True for credit-normal letters (G-K, L, O)


@dataclass
class FinancialStatements:
    """Complete financial statements built from lead sheet groupings."""
    balance_sheet: list[StatementLineItem]
    income_statement: list[StatementLineItem]
    # Balance Sheet totals
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    total_equity: float = 0.0
    is_balanced: bool = False
    balance_difference: float = 0.0
    # Income Statement totals
    total_revenue: float = 0.0
    gross_profit: float = 0.0
    operating_income: float = 0.0
    net_income: float = 0.0
    # Cash Flow Statement (Sprint 83)
    cash_flow_statement: Optional[CashFlowStatement] = None
    # Account-to-Statement Mapping Trace (Sprint 284)
    mapping_trace: list[MappingTraceEntry] = field(default_factory=list)
    # Metadata
    entity_name: str = ""
    period_end: str = ""

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        result = {
            "balance_sheet": [
                {
                    "label": item.label,
                    "amount": item.amount,
                    "indent_level": item.indent_level,
                    "is_subtotal": item.is_subtotal,
                    "is_total": item.is_total,
                    "lead_sheet_ref": item.lead_sheet_ref,
                }
                for item in self.balance_sheet
            ],
            "income_statement": [
                {
                    "label": item.label,
                    "amount": item.amount,
                    "indent_level": item.indent_level,
                    "is_subtotal": item.is_subtotal,
                    "is_total": item.is_total,
                    "lead_sheet_ref": item.lead_sheet_ref,
                }
                for item in self.income_statement
            ],
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "total_equity": self.total_equity,
            "is_balanced": self.is_balanced,
            "balance_difference": self.balance_difference,
            "total_revenue": self.total_revenue,
            "gross_profit": self.gross_profit,
            "operating_income": self.operating_income,
            "net_income": self.net_income,
            "entity_name": self.entity_name,
            "period_end": self.period_end,
        }
        if self.cash_flow_statement is not None:
            result["cash_flow_statement"] = self.cash_flow_statement.to_dict()
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
    SIGN_CORRECTED_LETTERS: set[str] = {'G', 'H', 'I', 'J', 'K', 'L', 'O'}

    def __init__(
        self,
        lead_sheet_grouping: dict,
        entity_name: str = "",
        period_end: str = "",
        prior_lead_sheet_grouping: Optional[dict] = None,
    ):
        self.grouping = lead_sheet_grouping
        self.entity_name = entity_name
        self.period_end = period_end
        self.prior_grouping = prior_lead_sheet_grouping
        # Index summaries by lead sheet letter for fast lookup
        self._balance_map: dict[str, float] = {}
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            self._balance_map[letter] = summary.get("net_balance", 0.0)
        # Index prior period balances
        self._prior_balance_map: dict[str, float] = {}
        if self.prior_grouping:
            for summary in self.prior_grouping.get("summaries", []):
                letter = summary.get("lead_sheet", "")
                self._prior_balance_map[letter] = summary.get("net_balance", 0.0)
        # Index account descriptions for depreciation detection
        self._account_descriptions: dict[str, list[str]] = {}
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            accounts = summary.get("accounts", [])
            self._account_descriptions[letter] = [
                a.get("name", "") if isinstance(a, dict) else str(a)
                for a in accounts
            ]

    def _get_lead_sheet_balance(self, letter: str) -> float:
        """Get net_balance for a lead sheet letter, 0.0 if missing."""
        return self._balance_map.get(letter, 0.0)

    def _get_prior_balance(self, letter: str) -> float:
        """Get prior period net_balance for a lead sheet letter, 0.0 if missing."""
        return self._prior_balance_map.get(letter, 0.0)

    def build(self) -> FinancialStatements:
        """Build complete financial statements."""
        balance_sheet = self._build_balance_sheet()
        income_statement = self._build_income_statement()

        # Calculate totals from raw lead sheet balances
        # Assets: A-F, positive net_balance = asset
        current_assets = sum(
            self._get_lead_sheet_balance(ls) for ls in ["A", "B", "C", "D"]
        )
        noncurrent_assets = sum(
            self._get_lead_sheet_balance(ls) for ls in ["E", "F"]
        )
        total_assets = current_assets + noncurrent_assets

        # Liabilities: G-J, negative net_balance → flip sign
        current_liabilities = sum(
            -self._get_lead_sheet_balance(ls) for ls in ["G", "H"]
        )
        noncurrent_liabilities = sum(
            -self._get_lead_sheet_balance(ls) for ls in ["I", "J"]
        )
        total_liabilities = current_liabilities + noncurrent_liabilities

        # Equity: K, negative net_balance → flip sign
        total_equity = -self._get_lead_sheet_balance("K")

        # Balance check
        balance_difference = total_assets - (total_liabilities + total_equity)
        is_balanced = abs(balance_difference) < 0.01

        # Income Statement totals
        total_revenue = -self._get_lead_sheet_balance("L")  # Credits → positive
        cogs = self._get_lead_sheet_balance("M")            # Debits → positive
        gross_profit = total_revenue - cogs
        operating_expenses = self._get_lead_sheet_balance("N")  # Debits → positive
        operating_income = gross_profit - operating_expenses
        other_net = -self._get_lead_sheet_balance("O")  # Credits = income
        net_income = operating_income + other_net

        # Cash Flow Statement (Sprint 83)
        cash_flow = self._build_cash_flow_statement(net_income)

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
            cash_flow_statement=cash_flow,
            entity_name=self.entity_name,
            period_end=self.period_end,
        )

        # Account-to-Statement Mapping Trace (Sprint 284)
        statements.mapping_trace = self._build_mapping_trace(statements)

        return statements

    def _build_balance_sheet(self) -> list[StatementLineItem]:
        """Build Balance Sheet line items from lead sheets A-K."""
        lines: list[StatementLineItem] = []

        # ── ASSETS ──
        lines.append(StatementLineItem("ASSETS", 0.0, indent_level=0))

        # Current Assets
        lines.append(StatementLineItem("Current Assets", 0.0, indent_level=0))
        cash = self._get_lead_sheet_balance("A")
        receivables = self._get_lead_sheet_balance("B")
        inventory = self._get_lead_sheet_balance("C")
        prepaid = self._get_lead_sheet_balance("D")

        lines.append(StatementLineItem("Cash and Cash Equivalents", cash, indent_level=1, lead_sheet_ref="A"))
        lines.append(StatementLineItem("Receivables", receivables, indent_level=1, lead_sheet_ref="B"))
        lines.append(StatementLineItem("Inventory", inventory, indent_level=1, lead_sheet_ref="C"))
        lines.append(StatementLineItem("Prepaid Expenses", prepaid, indent_level=1, lead_sheet_ref="D"))

        total_current_assets = cash + receivables + inventory + prepaid
        lines.append(StatementLineItem("Total Current Assets", total_current_assets, indent_level=1, is_subtotal=True))

        # Non-Current Assets
        lines.append(StatementLineItem("Non-Current Assets", 0.0, indent_level=0))
        ppe = self._get_lead_sheet_balance("E")
        intangibles = self._get_lead_sheet_balance("F")

        lines.append(StatementLineItem("Property, Plant & Equipment", ppe, indent_level=1, lead_sheet_ref="E"))
        lines.append(StatementLineItem("Other Assets & Intangibles", intangibles, indent_level=1, lead_sheet_ref="F"))

        total_noncurrent_assets = ppe + intangibles
        lines.append(StatementLineItem("Total Non-Current Assets", total_noncurrent_assets, indent_level=1, is_subtotal=True))

        total_assets = total_current_assets + total_noncurrent_assets
        lines.append(StatementLineItem("TOTAL ASSETS", total_assets, indent_level=0, is_total=True))

        # ── LIABILITIES & EQUITY ──
        lines.append(StatementLineItem("LIABILITIES & EQUITY", 0.0, indent_level=0))

        # Current Liabilities (flip sign)
        lines.append(StatementLineItem("Current Liabilities", 0.0, indent_level=0))
        ap = -self._get_lead_sheet_balance("G")
        other_cl = -self._get_lead_sheet_balance("H")

        lines.append(StatementLineItem("AP & Accrued Liabilities", ap, indent_level=1, lead_sheet_ref="G"))
        lines.append(StatementLineItem("Other Current Liabilities", other_cl, indent_level=1, lead_sheet_ref="H"))

        total_current_liabilities = ap + other_cl
        lines.append(StatementLineItem("Total Current Liabilities", total_current_liabilities, indent_level=1, is_subtotal=True))

        # Non-Current Liabilities (flip sign)
        lines.append(StatementLineItem("Non-Current Liabilities", 0.0, indent_level=0))
        lt_debt = -self._get_lead_sheet_balance("I")
        other_lt = -self._get_lead_sheet_balance("J")

        lines.append(StatementLineItem("Long-term Debt", lt_debt, indent_level=1, lead_sheet_ref="I"))
        lines.append(StatementLineItem("Other Long-term Liabilities", other_lt, indent_level=1, lead_sheet_ref="J"))

        total_noncurrent_liabilities = lt_debt + other_lt
        lines.append(StatementLineItem("Total Non-Current Liabilities", total_noncurrent_liabilities, indent_level=1, is_subtotal=True))

        total_liabilities = total_current_liabilities + total_noncurrent_liabilities
        lines.append(StatementLineItem("Total Liabilities", total_liabilities, indent_level=0, is_subtotal=True))

        # Equity (flip sign)
        equity = -self._get_lead_sheet_balance("K")
        lines.append(StatementLineItem("Stockholders' Equity", equity, indent_level=1, lead_sheet_ref="K"))

        total_le = total_liabilities + equity
        lines.append(StatementLineItem("TOTAL LIABILITIES & EQUITY", total_le, indent_level=0, is_total=True))

        return lines

    def _build_income_statement(self) -> list[StatementLineItem]:
        """Build Income Statement line items from lead sheets L-O."""
        lines: list[StatementLineItem] = []

        # Revenue (flip sign: credits → positive)
        revenue = -self._get_lead_sheet_balance("L")
        lines.append(StatementLineItem("Revenue", revenue, indent_level=0, lead_sheet_ref="L"))

        # COGS (debits → positive, displayed as expense)
        cogs = self._get_lead_sheet_balance("M")
        lines.append(StatementLineItem("Cost of Goods Sold", cogs, indent_level=0, lead_sheet_ref="M"))

        # Gross Profit
        gross_profit = revenue - cogs
        lines.append(StatementLineItem("GROSS PROFIT", gross_profit, indent_level=0, is_subtotal=True))

        # Operating Expenses (debits → positive)
        opex = self._get_lead_sheet_balance("N")
        lines.append(StatementLineItem("Operating Expenses", opex, indent_level=0, lead_sheet_ref="N"))

        # Operating Income
        operating_income = gross_profit - opex
        lines.append(StatementLineItem("OPERATING INCOME", operating_income, indent_level=0, is_subtotal=True))

        # Other Income / (Expense), Net (flip sign: credits = income)
        other_net = -self._get_lead_sheet_balance("O")
        lines.append(StatementLineItem("Other Income / (Expense), Net", other_net, indent_level=0, lead_sheet_ref="O"))

        # Net Income
        net_income = operating_income + other_net
        lines.append(StatementLineItem("NET INCOME", net_income, indent_level=0, is_total=True))

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

    def _build_mapping_trace(self, statements: 'FinancialStatements') -> list[MappingTraceEntry]:
        """Build mapping trace linking each statement line to its contributing TB accounts."""
        # Index summaries by lead sheet letter
        summary_index: dict[str, dict] = {}
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            if letter:
                summary_index[letter] = summary

        # Index statement amounts by lead sheet ref for tie-out comparison
        stmt_amounts: dict[str, float] = {}
        for item in statements.balance_sheet:
            if item.lead_sheet_ref:
                stmt_amounts[item.lead_sheet_ref] = item.amount
        for item in statements.income_statement:
            if item.lead_sheet_ref:
                stmt_amounts[item.lead_sheet_ref] = item.amount

        trace: list[MappingTraceEntry] = []

        for stmt_name, line_label, ref in self.STATEMENT_LINE_MAP:
            summary = summary_index.get(ref)
            statement_amount = stmt_amounts.get(ref, 0.0)

            if summary is None:
                # Lead sheet not present — empty entry, trivially tied
                trace.append(MappingTraceEntry(
                    statement=stmt_name,
                    line_label=line_label,
                    lead_sheet_ref=ref,
                    lead_sheet_name=line_label,
                    statement_amount=statement_amount,
                    account_count=0,
                    is_tied=True,
                    tie_difference=0.0,
                    sign_correction_applied=ref in self.SIGN_CORRECTED_LETTERS,
                ))
                continue

            lead_sheet_name = summary.get("name", line_label)
            raw_accounts = summary.get("accounts", [])
            accounts: list[MappingTraceAccount] = []
            net_values: list[float] = []

            for acct in raw_accounts:
                if not isinstance(acct, dict):
                    continue
                acct_name = acct.get("account", acct.get("name", "Unknown"))
                debit = acct.get("debit", 0.0)
                credit = acct.get("credit", 0.0)
                net = debit - credit
                net_values.append(net)
                confidence = acct.get("confidence", 1.0)
                keywords = acct.get("matched_keywords", [])
                accounts.append(MappingTraceAccount(
                    account_name=acct_name,
                    debit=debit,
                    credit=credit,
                    net_balance=net,
                    confidence=confidence,
                    matched_keywords=keywords,
                ))

            raw_sum = math.fsum(net_values)
            sign_corrected = ref in self.SIGN_CORRECTED_LETTERS

            # Tie-out: compare raw account sum to the summary net_balance
            summary_net = summary.get("net_balance", 0.0)
            tie_diff = abs(raw_sum - summary_net)
            is_tied = tie_diff < 0.01

            trace.append(MappingTraceEntry(
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
            ))

        return trace

    # ─── Cash Flow Statement (Sprint 83) ─────────────────────────────

    def _extract_depreciation(self) -> float:
        """
        Detect depreciation/amortization from account descriptions in OpEx (N)
        and Non-Current Assets (E, F).

        Returns the estimated depreciation amount as a positive number.
        Searches for depreciation keywords in account names across lead sheets
        E, F, and N. If found in expense accounts (N), uses the debit balance.
        If not separately identifiable, returns 0.0.
        """
        # Look for depreciation in operating expenses (N) accounts
        # In the lead sheet grouping, accounts may have amount detail
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            if letter not in ("E", "F", "N"):
                continue
            accounts = summary.get("accounts", [])
            for acct in accounts:
                if not isinstance(acct, dict):
                    continue
                name = acct.get("name", "").lower()
                for keyword, is_phrase in DEPRECIATION_KEYWORDS:
                    if is_phrase:
                        if keyword in name:
                            # Found depreciation — return its balance as positive
                            balance = acct.get("net_balance", 0.0)
                            return abs(balance)
                    else:
                        if keyword in name.split() or keyword in name:
                            balance = acct.get("net_balance", 0.0)
                            return abs(balance)
        return 0.0

    def _compute_balance_change(self, letter: str) -> float:
        """
        Compute the change in a lead sheet balance: current - prior.

        Returns 0.0 if no prior period is available.
        """
        if not self.prior_grouping:
            return 0.0
        current = self._get_lead_sheet_balance(letter)
        prior = self._get_prior_balance(letter)
        return current - prior

    def _build_operating_items(
        self, net_income: float, has_prior: bool, notes: list[str]
    ) -> list[CashFlowLineItem]:
        """Build operating activity line items (indirect method).

        Starts with net income, adds back non-cash items (depreciation),
        then adjusts for working capital changes (B, C, D, G, H).
        Mutates notes list with depreciation/prior-period warnings.
        """
        items: list[CashFlowLineItem] = []

        # Net Income (starting point)
        items.append(CashFlowLineItem(
            "Net Income", net_income, source="computed", indent_level=1,
        ))

        # Adjustments for non-cash items
        depreciation = self._extract_depreciation()
        if depreciation > 0:
            items.append(CashFlowLineItem(
                "Depreciation & Amortization", depreciation,
                source="E/N", indent_level=1,
            ))
        else:
            notes.append("Depreciation not separately identified in trial balance")

        # Working capital changes (require prior period)
        if has_prior:
            # Change in Receivables (B): increase = cash outflow (negative)
            delta_b = self._compute_balance_change("B")
            if abs(delta_b) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Accounts Receivable",
                    -delta_b,  # Asset increase = cash outflow
                    source="B", indent_level=1,
                ))

            # Change in Inventory (C): increase = cash outflow
            delta_c = self._compute_balance_change("C")
            if abs(delta_c) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Inventory",
                    -delta_c,
                    source="C", indent_level=1,
                ))

            # Change in Prepaid Expenses (D): increase = cash outflow
            delta_d = self._compute_balance_change("D")
            if abs(delta_d) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Prepaid Expenses",
                    -delta_d,
                    source="D", indent_level=1,
                ))

            # Change in Accounts Payable (G): liability increase = cash inflow
            # G has negative net_balance (credit), so change is also negative
            # When liability increases: more negative → delta is negative → flip = positive inflow
            delta_g = self._compute_balance_change("G")
            if abs(delta_g) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Accounts Payable",
                    -delta_g,  # Liability: more negative = increase = cash inflow
                    source="G", indent_level=1,
                ))

            # Change in Accrued Liabilities (H): same as AP
            delta_h = self._compute_balance_change("H")
            if abs(delta_h) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Accrued Liabilities",
                    -delta_h,
                    source="H", indent_level=1,
                ))
        else:
            notes.append("Prior period required for working capital changes")

        return items

    def _build_investing_items(self, has_prior: bool) -> list[CashFlowLineItem]:
        """Build investing activity line items.

        Changes in non-current assets: PPE (E) and Other Non-Current (F).
        """
        items: list[CashFlowLineItem] = []

        if has_prior:
            # Change in PPE (E): asset increase = cash outflow (capital expenditure)
            delta_e = self._compute_balance_change("E")
            if abs(delta_e) > 0.005:
                items.append(CashFlowLineItem(
                    "Capital Expenditures (PPE)",
                    -delta_e,  # Asset increase = cash outflow
                    source="E", indent_level=1,
                ))

            # Change in Other Non-Current Assets (F)
            delta_f = self._compute_balance_change("F")
            if abs(delta_f) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Other Non-Current Assets",
                    -delta_f,
                    source="F", indent_level=1,
                ))

        return items

    def _build_financing_items(
        self, net_income: float, has_prior: bool
    ) -> list[CashFlowLineItem]:
        """Build financing activity line items.

        Changes in long-term debt (I, J) and equity excluding retained earnings (K).
        """
        items: list[CashFlowLineItem] = []

        if has_prior:
            # Change in Long-Term Debt (I): liability increase = cash inflow
            # I has negative net_balance; more negative = increase
            delta_i = self._compute_balance_change("I")
            if abs(delta_i) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Long-Term Debt",
                    -delta_i,  # More negative = increase = cash inflow
                    source="I", indent_level=1,
                ))

            # Change in Short-Term Debt / Other LT Liabilities (J)
            delta_j = self._compute_balance_change("J")
            if abs(delta_j) > 0.005:
                items.append(CashFlowLineItem(
                    "Change in Other Long-Term Liabilities",
                    -delta_j,
                    source="J", indent_level=1,
                ))

            # Change in Equity (K), excluding retained earnings change
            # Retained earnings change ≈ net_income, so equity change from
            # financing = total equity change - net income
            delta_k = self._compute_balance_change("K")
            # K has negative net_balance; change in displayed equity = -delta_k
            equity_change_displayed = -delta_k
            financing_equity_change = equity_change_displayed - net_income
            if abs(financing_equity_change) > 0.005:
                items.append(CashFlowLineItem(
                    "Equity Changes (excl. Retained Earnings)",
                    financing_equity_change,
                    source="K", indent_level=1,
                ))

        return items

    def _build_cash_flow_statement(self, net_income: float) -> CashFlowStatement:
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
        operating_subtotal = sum(item.amount for item in operating_items)
        operating = CashFlowSection(
            label="Cash Flows from Operating Activities",
            items=operating_items,
            subtotal=operating_subtotal,
        )

        investing_items = self._build_investing_items(has_prior)
        investing_subtotal = sum(item.amount for item in investing_items)
        investing = CashFlowSection(
            label="Cash Flows from Investing Activities",
            items=investing_items,
            subtotal=investing_subtotal,
        )

        financing_items = self._build_financing_items(net_income, has_prior)
        financing_subtotal = sum(item.amount for item in financing_items)
        financing = CashFlowSection(
            label="Cash Flows from Financing Activities",
            items=financing_items,
            subtotal=financing_subtotal,
        )

        # Reconciliation
        net_change = operating_subtotal + investing_subtotal + financing_subtotal
        ending_cash = self._get_lead_sheet_balance("A")
        beginning_cash = self._get_prior_balance("A") if has_prior else 0.0

        if has_prior:
            expected_ending = beginning_cash + net_change
            reconciliation_diff = ending_cash - expected_ending
            is_reconciled = abs(reconciliation_diff) < 0.01
        else:
            reconciliation_diff = 0.0
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
