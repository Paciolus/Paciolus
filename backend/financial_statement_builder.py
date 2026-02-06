"""
Financial Statement Builder Module
Sprint 71: Financial Statements — Backend Builder

Transforms lead sheet groupings (A-Z) into formatted Balance Sheet
and Income Statement documents.

Data Flow:
    TB → StreamingAuditor → Classification → lead_sheet_grouping dict
                                                    ↓
    lead_sheet_grouping → FinancialStatementBuilder → BalanceSheet + IncomeStatement

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

from dataclasses import dataclass, field


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
    # Metadata
    entity_name: str = ""
    period_end: str = ""

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
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


class FinancialStatementBuilder:
    """
    Builds formatted financial statements from lead sheet groupings.

    Accepts the serialized dict form of LeadSheetGrouping (not the dataclass),
    as produced by lead_sheet_grouping_to_dict().
    """

    def __init__(
        self,
        lead_sheet_grouping: dict,
        entity_name: str = "",
        period_end: str = "",
    ):
        self.grouping = lead_sheet_grouping
        self.entity_name = entity_name
        self.period_end = period_end
        # Index summaries by lead sheet letter for fast lookup
        self._balance_map: dict[str, float] = {}
        for summary in self.grouping.get("summaries", []):
            letter = summary.get("lead_sheet", "")
            self._balance_map[letter] = summary.get("net_balance", 0.0)

    def _get_lead_sheet_balance(self, letter: str) -> float:
        """Get net_balance for a lead sheet letter, 0.0 if missing."""
        return self._balance_map.get(letter, 0.0)

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

        return FinancialStatements(
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
            entity_name=self.entity_name,
            period_end=self.period_end,
        )

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
