"""
Generate Large Trial Balance Test Data
Creates a CSV with 50,000 rows of dummy trial balance data for stress testing.
"""

import csv
import random
from datetime import datetime

# Account templates with expected balance directions
ASSET_ACCOUNTS = [
    "Cash - Operating",
    "Cash - Payroll",
    "Petty Cash",
    "Bank of America Checking",
    "Wells Fargo Savings",
    "Accounts Receivable",
    "Accounts Receivable - Trade",
    "Allowance for Doubtful Accounts",
    "Inventory - Raw Materials",
    "Inventory - Finished Goods",
    "Prepaid Insurance",
    "Prepaid Rent",
    "Prepaid Expenses",
    "Equipment",
    "Accumulated Depreciation - Equipment",
    "Vehicles",
    "Land",
    "Building",
    "Office Furniture",
]

LIABILITY_ACCOUNTS = [
    "Accounts Payable",
    "Accounts Payable - Trade",
    "Accrued Expenses",
    "Accrued Payroll",
    "Accrued Interest",
    "Sales Tax Payable",
    "Income Tax Payable",
    "Payroll Tax Payable",
    "Unearned Revenue",
    "Deferred Revenue",
    "Notes Payable - Short Term",
    "Notes Payable - Long Term",
    "Mortgage Payable",
    "Line of Credit",
    "Loan Payable - Bank",
    "Customer Deposits",
]

EQUITY_ACCOUNTS = [
    "Common Stock",
    "Retained Earnings",
    "Owner's Equity",
    "Dividends",
    "Treasury Stock",
]

REVENUE_ACCOUNTS = [
    "Sales Revenue",
    "Service Revenue",
    "Consulting Revenue",
    "Interest Income",
    "Rental Income",
    "Commission Revenue",
    "Royalty Revenue",
]

EXPENSE_ACCOUNTS = [
    "Cost of Goods Sold",
    "Salaries Expense",
    "Wages Expense",
    "Rent Expense",
    "Utilities Expense",
    "Insurance Expense",
    "Depreciation Expense",
    "Office Supplies Expense",
    "Advertising Expense",
    "Marketing Expense",
    "Travel Expense",
    "Meals & Entertainment",
    "Professional Fees",
    "Bank Charges",
    "Interest Expense",
    "Bad Debt Expense",
    "Repairs & Maintenance",
    "Telephone Expense",
    "Internet Expense",
    "Software Subscriptions",
]


def generate_account_number():
    """Generate a random account number."""
    return f"{random.randint(1000, 9999)}-{random.randint(100, 999)}"


def generate_trial_balance(num_rows: int, output_file: str):
    """
    Generate a trial balance CSV with the specified number of rows.
    Ensures debits = credits for a balanced trial balance.
    Includes some abnormal balances for testing detection.
    """
    print(f"Generating {num_rows:,} row trial balance...")

    rows = []
    total_debits = 0.0
    total_credits = 0.0

    # Combine all accounts
    all_accounts = (
        [(acc, "asset") for acc in ASSET_ACCOUNTS] +
        [(acc, "liability") for acc in LIABILITY_ACCOUNTS] +
        [(acc, "equity") for acc in EQUITY_ACCOUNTS] +
        [(acc, "revenue") for acc in REVENUE_ACCOUNTS] +
        [(acc, "expense") for acc in EXPENSE_ACCOUNTS]
    )

    # Generate rows
    for i in range(num_rows - 1):  # Leave one row for balancing
        account_name, account_type = random.choice(all_accounts)

        # Add variety with department/location suffixes
        suffix = ""
        if random.random() < 0.3:
            suffix = f" - {random.choice(['East', 'West', 'North', 'South', 'HQ', 'Branch'])}"
        if random.random() < 0.2:
            suffix += f" #{random.randint(1, 50)}"

        full_account_name = f"{account_name}{suffix}"
        account_number = generate_account_number()

        # Generate amount
        amount = round(random.uniform(10, 50000), 2)

        # Determine debit or credit based on account type
        # Add ~5% abnormal balances for testing
        is_abnormal = random.random() < 0.05

        if account_type in ["asset", "expense"]:
            # Normally debit balance
            if is_abnormal:
                debit = 0.0
                credit = amount
            else:
                debit = amount
                credit = 0.0
        elif account_type in ["liability", "equity", "revenue"]:
            # Normally credit balance
            if is_abnormal:
                debit = amount
                credit = 0.0
            else:
                debit = 0.0
                credit = amount
        else:
            # Random
            if random.random() < 0.5:
                debit = amount
                credit = 0.0
            else:
                debit = 0.0
                credit = amount

        total_debits += debit
        total_credits += credit

        rows.append({
            "Account Number": account_number,
            "Account Name": full_account_name,
            "Debit": debit if debit > 0 else "",
            "Credit": credit if credit > 0 else "",
        })

        if (i + 1) % 10000 == 0:
            print(f"  Generated {i + 1:,} rows...")

    # Add a balancing entry to ensure debits = credits
    difference = total_debits - total_credits
    if abs(difference) > 0.01:
        if difference > 0:
            # Need more credits
            rows.append({
                "Account Number": "9999-999",
                "Account Name": "Suspense Account",
                "Debit": "",
                "Credit": round(difference, 2),
            })
            total_credits += difference
        else:
            # Need more debits
            rows.append({
                "Account Number": "9999-999",
                "Account Name": "Suspense Account",
                "Debit": round(abs(difference), 2),
                "Credit": "",
            })
            total_debits += abs(difference)
    else:
        # Add a zero-balance placeholder
        rows.append({
            "Account Number": "9999-999",
            "Account Name": "Suspense Account",
            "Debit": "",
            "Credit": "",
        })

    # Write to CSV
    print(f"Writing to {output_file}...")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Account Number", "Account Name", "Debit", "Credit"])
        writer.writeheader()
        writer.writerows(rows)

    print("\nGeneration complete!")
    print(f"  Total rows: {len(rows):,}")
    print(f"  Total debits: ${total_debits:,.2f}")
    print(f"  Total credits: ${total_credits:,.2f}")
    print(f"  Difference: ${abs(total_debits - total_credits):.2f}")
    print(f"  Output file: {output_file}")


if __name__ == "__main__":
    generate_trial_balance(50000, "large_test.csv")
