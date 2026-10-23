"""
A reference chart of accounts, for measuring the lead-sheet classifier against a
population rather than spot-checking it.

Sprint 804 (findings A-3 / A-4). The full-spectrum review of 2026-10-22 drove
`group_by_lead_sheet` with a chart built from standard account names and found
**13 of 68 (19%)** on lead sheet Z with zero keywords matched — the entire
compensation block among them — plus four accounts filed to the wrong statement
at confidence 0.80–0.90. Unclassified accounts are excluded from both statements,
so net income was wrong by their sum.

Every name here is one a practitioner would expect to see on an ordinary
small-business or mid-market trial balance. Nothing exotic belongs in this file:
its job is to prove the classifier handles the *plain* cases, which is precisely
where it was failing. `tests/test_lead_sheet_reference_chart.py` asserts a
classification floor against it, so adding a name here tightens the gate.

Each entry is `(account_name, expected_lead_sheet)`.
"""

# (account name, expected lead sheet letter)
REFERENCE_CHART: list[tuple[str, str]] = [
    # --- A: Cash -----------------------------------------------------------
    ("Cash - Operating", "A"),
    ("Cash in Bank - Payroll", "A"),
    ("Petty Cash", "A"),
    ("Savings Account", "A"),
    ("Money Market Account", "A"),
    # --- B: Receivables ----------------------------------------------------
    ("Accounts Receivable", "B"),
    ("Accounts Receivable - Trade", "B"),
    ("Allowance for Doubtful Accounts", "B"),
    ("Notes Receivable", "B"),
    ("Employee Advances Receivable", "B"),
    # --- C: Inventory ------------------------------------------------------
    ("Inventory - Finished Goods", "C"),
    ("Inventory - Raw Materials", "C"),
    ("Work in Process", "C"),
    # --- D: Prepaid and other current assets -------------------------------
    ("Prepaid Expense", "D"),
    ("Prepaid Insurance", "D"),
    ("Prepaid Rent", "D"),
    ("Security Deposits", "D"),
    # --- E: PP&E -----------------------------------------------------------
    ("Land", "E"),
    ("Buildings", "E"),
    ("Machinery and Equipment", "E"),
    ("Furniture and Fixtures", "E"),
    ("Vehicles", "E"),
    ("Leasehold Improvements", "E"),
    ("Accumulated Depreciation", "E"),
    ("Right-of-Use Asset - Operating Lease", "E"),
    # --- F: Other assets and intangibles -----------------------------------
    ("Goodwill", "F"),
    ("Patents and Trademarks", "F"),
    ("Deferred Tax Asset", "F"),
    # --- G: AP and accrued liabilities -------------------------------------
    ("Accounts Payable", "G"),
    ("Accrued Expenses", "G"),
    ("Accrued Liabilities", "G"),
    ("Wages Payable", "G"),
    ("Salaries Payable", "G"),
    # --- H: Other current liabilities --------------------------------------
    ("Unearned Revenue", "H"),
    ("Deferred Revenue", "H"),
    ("Sales Tax Payable", "H"),
    ("Payroll Taxes Payable", "H"),
    ("Customer Deposits", "H"),
    ("Current Portion of Long-Term Debt", "H"),
    ("Lease Liability", "H"),
    # --- I: Long-term debt -------------------------------------------------
    ("Notes Payable - Bank", "I"),
    ("Mortgage Payable", "I"),
    ("Line of Credit", "I"),
    # --- J: Other long-term liabilities ------------------------------------
    ("Deferred Tax Liability", "J"),
    ("Asset Retirement Obligation", "J"),
    # --- K: Equity ---------------------------------------------------------
    ("Common Stock", "K"),
    ("Additional Paid-In Capital", "K"),
    ("Retained Earnings", "K"),
    ("Treasury Stock", "K"),
    ("Owner's Draw", "K"),
    ("Shareholder Distributions", "K"),
    # --- L: Revenue --------------------------------------------------------
    ("Sales Revenue", "L"),
    ("Service Revenue", "L"),
    ("Consulting Income", "L"),
    ("Sales Returns and Allowances", "L"),
    ("Sales Discounts", "L"),
    # --- M: Cost of sales --------------------------------------------------
    ("Cost of Goods Sold", "M"),
    ("Direct Labor", "M"),
    ("Direct Materials", "M"),
    ("Manufacturing Overhead", "M"),
    ("Freight In", "M"),
    # --- N: Operating expenses ---------------------------------------------
    # The compensation block. Every one of these was unclassified before
    # Sprint 804 except "Payroll Expense", which is why the gap stayed invisible.
    ("Salaries and Wages Expense", "N"),
    ("Salaries Expense", "N"),
    ("Wages Expense", "N"),
    ("Payroll Expense", "N"),
    ("Payroll Tax Expense", "N"),
    ("Officer Compensation", "N"),
    ("Employee Benefits", "N"),
    ("Commissions Expense", "N"),
    ("Contract Labor", "N"),
    # The rest of an ordinary operating-expense block.
    ("Rent Expense", "N"),
    ("Utilities Expense", "N"),
    ("Insurance Expense", "N"),
    ("Depreciation Expense", "N"),
    ("Amortization Expense", "N"),
    ("Advertising and Marketing", "N"),
    ("Professional Fees", "N"),
    ("Legal and Accounting", "N"),
    ("Office Supplies Expense", "N"),
    ("Telephone and Internet", "N"),
    ("Travel Expense", "N"),
    ("Meals and Entertainment", "N"),
    ("Repairs and Maintenance", "N"),
    ("Bank Service Charges", "N"),
    ("Bad Debt Expense", "N"),
    ("Software Expense", "N"),
    ("Vehicle Expense", "N"),
    ("Charitable Contributions", "N"),
    ("Postage and Delivery", "N"),
    ("Dues and Subscriptions", "N"),
    # --- O: Other income and expense ---------------------------------------
    ("Interest Income", "O"),
    ("Interest Expense", "O"),
    ("Gain on Sale of Assets", "O"),
    ("Income Tax Expense", "O"),
    ("Other Income", "O"),
]
