"""
Comprehensive QA Sweep — All Tools, All Known Issues
Runs against paciolus_test_tb_cascade_fy2025.csv
"""
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import pandas as pd
from io import BytesIO

# ============================================================
# TOOL 1: Diagnostic Report (audit_engine.py)
# ============================================================
print("=" * 80)
print("TOOL 1: DIAGNOSTIC REPORT (audit_engine.py)")
print("=" * 80)

csv_path = os.path.join(os.path.dirname(__file__), 'paciolus_test_tb_cascade_fy2025.csv')
with open(csv_path, 'rb') as f:
    file_bytes = f.read()

from audit_engine import audit_trial_balance_streaming

result = audit_trial_balance_streaming(
    file_bytes=file_bytes,
    filename='paciolus_test_tb_cascade_fy2025.csv',
    materiality_threshold=50000.0,
)

# Extract key sections
abnormal_balances = result.get('abnormal_balances', [])
diagnostics = result.get('diagnostics', {})
classified_accounts = result.get('classified_accounts', {})
account_subtypes = result.get('account_subtypes', {})
lead_sheet_grouping = result.get('lead_sheet_grouping', {})
category_totals_data = result.get('category_totals', {})

print(f"\nTotal abnormal_balances found: {len(abnormal_balances)}")

# --- 1A: Contra Account Recognition ---
print("\n--- 1A: Contra Account Recognition ---")
contra_accounts = [
    "1140", "1250", "1540", "1560", "1580", "1600", "1720", "1740",
    "3050", "3060", "3070", "3080", "4080", "4090"
]
contra_names = {
    "1140": "Allowance for Doubtful Accounts",
    "1250": "Inventory — Obsolescence Reserve",
    "1540": "Accumulated Depreciation — Buildings",
    "1560": "Accumulated Depreciation — Machinery",
    "1580": "Accumulated Depreciation — Furniture",
    "1600": "Accumulated Depreciation — Vehicles",
    "1720": "Accumulated Amortization — Patents",
    "1740": "Accumulated Amortization — Customer Lists",
    "3050": "Accumulated Other Comprehensive Loss — Pension",
    "3060": "Accumulated Other Comprehensive Loss — FX",
    "3070": "Dividends Declared — Class A",
    "3080": "Dividends Declared — Class B",
    "4080": "Sales Discounts and Allowances",
    "4090": "Sales Returns",
}

for acct_num in contra_accounts:
    acct_name = contra_names[acct_num]
    found_in_findings = False
    for ab in abnormal_balances:
        ab_account = ab.get('account', '')
        if acct_num in ab_account or acct_name.lower() in ab_account.lower():
            # Check if it's a natural_balance_violation (false positive)
            atype = ab.get('anomaly_type', '')
            if atype == 'natural_balance_violation':
                print(f"  FAIL: {acct_num} {acct_name} — appears as natural_balance_violation")
                found_in_findings = True
                break
    if not found_in_findings:
        print(f"  PASS: {acct_num} {acct_name} — correctly suppressed")

# --- 1B: Genuine Anomalies Must Fire ---
print("\n--- 1B: Genuine Anomalies Must Fire ---")
expected_anomalies = {
    "1220": {"name": "Inventory — Work in Progress", "expected_type": "natural_balance_violation"},
    "2150": {"name": "Customer Deposits — Refundable", "expected_type": "natural_balance_violation"},
    "1840": {"name": "Suspense — ERP System Migration", "expected_type": "suspense_account"},
    "1850": {"name": "Suspense — Insurance Claim Proceeds", "expected_type": "suspense_account"},
    "1150": {"name": "AR Related Party", "expected_type": "related_party"},
    "2020": {"name": "AP Related Party", "expected_type": "related_party"},
    "2530": {"name": "Note Payable — Shareholder", "expected_type": "related_party"},
    "4060": {"name": "Revenue — Related Party", "expected_type": "related_party"},
    "1810": {"name": "Intercompany Receivable", "expected_type": "intercompany_imbalance"},
    "4010": {"name": "Revenue — OEM Manufacturing", "expected_type": "revenue_concentration"},
}

for acct_num, expected in expected_anomalies.items():
    found = False
    found_type = None
    for ab in abnormal_balances:
        ab_account = ab.get('account', '')
        if acct_num in ab_account or expected['name'].lower()[:15] in ab_account.lower():
            found = True
            found_type = ab.get('anomaly_type', 'unknown')
            break
    if found:
        type_match = expected['expected_type'] in (found_type or '')
        status = "PASS" if type_match else f"PARTIAL (found as {found_type}, expected {expected['expected_type']})"
        print(f"  {status}: {acct_num} {expected['name']} — found as {found_type}")
    else:
        print(f"  FAIL: {acct_num} {expected['name']} — NOT found in findings")

# --- 1C: False Related Party Findings ---
print("\n--- 1C: False Related Party Findings ---")
false_rp_accounts = ["6330", "6550"]
false_rp_names = {
    "6330": "Directors and Officers Insurance",
    "6550": "Board of Directors Fees",
}
for acct_num in false_rp_accounts:
    found_as_rp = False
    for ab in abnormal_balances:
        ab_account = ab.get('account', '')
        if (acct_num in ab_account or false_rp_names[acct_num].lower()[:15] in ab_account.lower()):
            if ab.get('anomaly_type', '') == 'related_party':
                found_as_rp = True
                break
    if found_as_rp:
        print(f"  FAIL: {acct_num} {false_rp_names[acct_num]} — falsely flagged as related party")
    else:
        print(f"  PASS: {acct_num} {false_rp_names[acct_num]} — correctly excluded from related party")

# --- 1D: Related Party vs Suspense Classification ---
print("\n--- 1D: Related Party vs Suspense Classification ---")
rp_not_suspense = {
    "1150": "Accounts Receivable — Related Party (Cascade Holdings LLC)",
    "2020": "Accounts Payable — Related Party (Cascade Holdings LLC)",
    "4060": "Revenue — Related Party (Cascade Holdings LLC)",
}
for acct_num, acct_name in rp_not_suspense.items():
    found_as_suspense = False
    found_as_rp = False
    for ab in abnormal_balances:
        ab_account = ab.get('account', '')
        if acct_num in ab_account:
            atype = ab.get('anomaly_type', '')
            if atype == 'suspense_account':
                found_as_suspense = True
            if atype == 'related_party':
                found_as_rp = True
    if found_as_suspense:
        print(f"  FAIL: {acct_num} {acct_name} — classified as suspense (should be related party)")
    elif found_as_rp:
        print(f"  PASS: {acct_num} {acct_name} — correctly classified as related party")
    else:
        print(f"  PARTIAL: {acct_num} {acct_name} — not found as either suspense or related party")

# --- 1E: Intercompany Imbalance ---
print("\n--- 1E: Intercompany Imbalance Detection ---")
ic_found = False
ic_finding = None
for ab in abnormal_balances:
    ab_account = ab.get('account', '')
    if '1810' in ab_account or 'intercompany' in ab_account.lower():
        if ab.get('anomaly_type', '') == 'intercompany_imbalance':
            ic_found = True
            ic_finding = ab
            break
if ic_found:
    issue_text = ic_finding.get('issue', '').lower()
    has_no_offset = 'no offsetting' in issue_text or 'elimination gap' in issue_text or 'no matching' in issue_text
    has_counterparty = 'cascade mexico' in issue_text or 'mexico' in issue_text
    print(f"  Finding type: intercompany_imbalance — PASS")
    print(f"  References 'no offsetting payable': {'PASS' if has_no_offset else 'FAIL'} — issue: {ic_finding.get('issue', '')[:100]}")
    print(f"  References counterparty name: {'PASS' if has_counterparty else 'FAIL'}")
    # Check it's NOT also in related party list
    also_rp = False
    for ab in abnormal_balances:
        if '1810' in ab.get('account', '') and ab.get('anomaly_type', '') == 'related_party':
            also_rp = True
    print(f"  Absent from Related Party list: {'PASS' if not also_rp else 'FAIL (also appears as related party)'}")
else:
    print(f"  FAIL: 1810 Intercompany Receivable not found as intercompany_imbalance")
    # Check if it's elsewhere
    for ab in abnormal_balances:
        if '1810' in ab.get('account', ''):
            print(f"    Found as: {ab.get('anomaly_type', '')} — {ab.get('issue', '')[:80]}")

# --- 1F: Score Decomposition ---
print("\n--- 1F: Score Decomposition ---")
risk_score = diagnostics.get('risk_score', result.get('risk_score'))
risk_factors = diagnostics.get('risk_factors', result.get('risk_factors'))
print(f"  Risk score: {risk_score}")
if risk_factors:
    print(f"  Number of factor lines: {len(risk_factors)}")
    total_factor_points = sum(f[1] if isinstance(f, (list, tuple)) else 0 for f in risk_factors)
    print(f"  Sum of factor points: {total_factor_points}")
    print(f"  Score matches factor sum: {'PASS' if total_factor_points == risk_score else 'FAIL'}")
    for f in risk_factors:
        fname = f[0] if isinstance(f, (list, tuple)) else str(f)
        fval = f[1] if isinstance(f, (list, tuple)) and len(f) > 1 else '?'
        print(f"    {fname}: {fval}")
else:
    print(f"  FAIL: No risk_factors found in output")
    # Try to find them in diagnostics
    for key in sorted(diagnostics.keys()):
        if 'risk' in key.lower() or 'score' in key.lower() or 'factor' in key.lower():
            print(f"    diagnostics['{key}']: {str(diagnostics[key])[:120]}")

# --- 1G: Grammar Check ---
print("\n--- 1G: Grammar Check ---")
grammar_fail = False
for ab in abnormal_balances:
    issue = ab.get('issue', '')
    if 'liabilitys' in issue.lower():
        print(f"  FAIL: Found 'liabilitys' in: {issue[:100]}")
        grammar_fail = True
    suggestions = ab.get('suggestions', [])
    for s in (suggestions if isinstance(suggestions, list) else []):
        if 'liabilitys' in str(s).lower():
            print(f"  FAIL: Found 'liabilitys' in suggestion: {str(s)[:100]}")
            grammar_fail = True
if not grammar_fail:
    print(f"  PASS: No 'liabilitys' found in any finding text")

# --- 1H: Population Composition ---
print("\n--- 1H: Population Composition ---")
pop_profile = result.get('population_profile', {})
section_density = None
if pop_profile:
    section_density = pop_profile.get('section_density', pop_profile.get('category_breakdown'))
    print(f"  Population profile present: PASS")
    print(f"  Account count: {pop_profile.get('account_count', 'N/A')}")
    if section_density:
        print(f"  Section density entries: {len(section_density) if isinstance(section_density, (list, dict)) else 'N/A'}")
        if isinstance(section_density, dict):
            for k, v in section_density.items():
                print(f"    {k}: {v}")
        elif isinstance(section_density, list):
            for item in section_density[:5]:
                print(f"    {item}")
    else:
        print(f"  Section density: NOT FOUND")
        print(f"  Available keys: {list(pop_profile.keys())[:15]}")
else:
    print(f"  FAIL: No population_profile in result")
    print(f"  Result top-level keys: {list(result.keys())}")

print(f"\n  NOTE: PDF export check requires manual verification via API endpoint")

# ============================================================
# TOOL 2: Key Metrics / Ratio Engine
# ============================================================
print("\n" + "=" * 80)
print("TOOL 2: KEY METRICS / RATIO ENGINE")
print("=" * 80)

from ratio_engine import extract_category_totals, calculate_analytics

# Build account_balances dict from result
account_balances = result.get('account_balances', {})
if not account_balances:
    # Build from CSV
    df = pd.read_csv(csv_path)
    account_balances = {}
    for _, row in df.iterrows():
        name = f"{row['account_number']} — {row['account_name']}"
        account_balances[name] = {
            'debit': float(row.get('debit', 0) or 0),
            'credit': float(row.get('credit', 0) or 0),
        }

print(f"  Account balances loaded: {len(account_balances)} accounts")

cat_totals = extract_category_totals(account_balances, classified_accounts, account_subtypes)

print(f"\n  Category Totals:")
print(f"    Total Assets: ${cat_totals.total_assets:,.2f}")
print(f"    Current Assets: ${cat_totals.current_assets:,.2f}")
print(f"    Inventory: ${cat_totals.inventory:,.2f}")
print(f"    Accounts Receivable: ${cat_totals.accounts_receivable:,.2f}")
print(f"    Total Liabilities: ${cat_totals.total_liabilities:,.2f}")
print(f"    Current Liabilities: ${cat_totals.current_liabilities:,.2f}")
print(f"    Total Equity: ${cat_totals.total_equity:,.2f}")
print(f"    Total Revenue: ${cat_totals.total_revenue:,.2f}")
print(f"    COGS: ${cat_totals.cost_of_goods_sold:,.2f}")
print(f"    Operating Expenses: ${cat_totals.operating_expenses:,.2f}")
print(f"    Total Expenses: ${cat_totals.total_expenses:,.2f}")

analytics = calculate_analytics(cat_totals)

# --- 2A: Current Ratio ---
print("\n--- 2A: Current Ratio ---")
ratios = analytics.get('ratios', analytics)
current_ratio = None
for key in ['current_ratio', 'liquidity']:
    if key in ratios:
        val = ratios[key]
        if isinstance(val, dict):
            current_ratio = val.get('value', val.get('current_ratio'))
        else:
            current_ratio = val
        break
if current_ratio is None and isinstance(ratios, dict):
    # Try nested
    for section_key, section in ratios.items():
        if isinstance(section, dict):
            for k, v in section.items():
                if 'current_ratio' in k.lower() or 'current ratio' in k.lower():
                    current_ratio = v.get('value') if isinstance(v, dict) else v
                    break

print(f"  Current Ratio: {current_ratio}")
if current_ratio is not None and current_ratio != 'N/A':
    try:
        cr_val = float(current_ratio)
        print(f"  Expected: ~2.0-2.3x, Got: {cr_val:.2f}x — {'PASS' if 1.5 < cr_val < 3.0 else 'FAIL'}")
    except (ValueError, TypeError):
        print(f"  FAIL: Non-numeric value: {current_ratio}")
else:
    print(f"  FAIL: Current Ratio is N/A or missing")

# --- 2B: Quick Ratio ---
print("\n--- 2B: Quick Ratio ---")
quick_ratio = None
for section_key, section in (ratios.items() if isinstance(ratios, dict) else []):
    if isinstance(section, dict):
        for k, v in section.items():
            if 'quick_ratio' in k.lower() or 'quick ratio' in k.lower():
                quick_ratio = v.get('value') if isinstance(v, dict) else v
                break
    if quick_ratio is not None:
        break
print(f"  Quick Ratio: {quick_ratio}")
if quick_ratio is not None and quick_ratio != 'N/A':
    try:
        qr_val = float(quick_ratio)
        print(f"  Expected: lower than Current Ratio — {'PASS' if current_ratio and qr_val < float(current_ratio) else 'CHECK'}")
    except (ValueError, TypeError):
        print(f"  FAIL: Non-numeric value: {quick_ratio}")
else:
    print(f"  FAIL: Quick Ratio is N/A or missing")

# --- 2C: Gross Margin ---
print("\n--- 2C: Gross Margin ---")
gross_margin = None
for section_key, section in (ratios.items() if isinstance(ratios, dict) else []):
    if isinstance(section, dict):
        for k, v in section.items():
            if 'gross' in k.lower() and 'margin' in k.lower():
                gross_margin = v.get('value') if isinstance(v, dict) else v
                break
    if gross_margin is not None:
        break

print(f"  Gross Margin: {gross_margin}")
if gross_margin is not None and gross_margin != 'N/A':
    try:
        gm_val = float(gross_margin)
        # Could be percentage (16.86) or decimal (0.1686)
        gm_pct = gm_val if gm_val > 1 else gm_val * 100
        print(f"  Expected: ~16-18%, Got: {gm_pct:.1f}% — {'PASS' if 10 < gm_pct < 25 else 'FAIL'}")
        if gm_pct > 90:
            print(f"  FAIL: Likely COGS not being recognized (shows ~100%)")
    except (ValueError, TypeError):
        print(f"  FAIL: Non-numeric value: {gross_margin}")
else:
    print(f"  FAIL: Gross Margin is N/A or missing")
    print(f"  COGS value from category_totals: ${cat_totals.cost_of_goods_sold:,.2f}")
    print(f"  Revenue value: ${cat_totals.total_revenue:,.2f}")
    if cat_totals.total_revenue > 0:
        manual_gm = (cat_totals.total_revenue - cat_totals.cost_of_goods_sold) / cat_totals.total_revenue * 100
        print(f"  Manual calculation: {manual_gm:.1f}%")

# --- 2D: Expense Category Distribution ---
print("\n--- 2D: Expense Category Distribution ---")
try:
    from expense_category_engine import compute_expense_categories
    expense_cats = compute_expense_categories(
        account_balances, classified_accounts,
        total_revenue=cat_totals.total_revenue,
        materiality_threshold=50000.0,
    )
    print(f"  COGS: ${expense_cats.cogs:,.2f} (ratio: {expense_cats.cogs_ratio:.1%})")
    print(f"  Payroll: ${expense_cats.payroll:,.2f} (ratio: {expense_cats.payroll_ratio:.1%})")
    print(f"  D&A: ${expense_cats.depreciation_amortization:,.2f} (ratio: {expense_cats.depreciation_ratio:.1%})")
    print(f"  Other OpEx: ${expense_cats.other_operating:,.2f} (ratio: {expense_cats.other_operating_ratio:.1%})")

    all_zero_except_other = (
        expense_cats.cogs == 0 and expense_cats.payroll == 0 and
        expense_cats.depreciation_amortization == 0
    )
    if all_zero_except_other:
        print(f"  FAIL: All categories $0 except Other Operating — classification not working")
    else:
        print(f"  PASS: Meaningful breakdown across categories")
except Exception as e:
    print(f"  ERROR: {e}")

# ============================================================
# TOOL 3: Lead Sheet Grouping
# ============================================================
print("\n" + "=" * 80)
print("TOOL 3: LEAD SHEET GROUPING")
print("=" * 80)

summaries = []
if isinstance(lead_sheet_grouping, dict):
    summaries = lead_sheet_grouping.get('summaries', [])
elif hasattr(lead_sheet_grouping, 'summaries'):
    summaries = lead_sheet_grouping.summaries

print(f"\n  Lead sheets found: {len(summaries)}")
total_acct_count = 0

# --- 3A: Credits Column ---
print("\n--- 3A: Credits Column ---")
liability_sheets = ['G', 'H', 'I', 'J']
equity_sheets = ['K']
revenue_sheets = ['L']

for s in summaries:
    ls = s.get('lead_sheet', s.get('letter', '')) if isinstance(s, dict) else getattr(s, 'lead_sheet', '')
    ls_str = str(ls).upper()
    name = s.get('name', '') if isinstance(s, dict) else getattr(s, 'name', '')
    total_credit = s.get('total_credit', 0) if isinstance(s, dict) else getattr(s, 'total_credit', 0)
    total_debit = s.get('total_debit', 0) if isinstance(s, dict) else getattr(s, 'total_debit', 0)
    net = s.get('net_balance', 0) if isinstance(s, dict) else getattr(s, 'net_balance', 0)
    acct_count = s.get('account_count', 0) if isinstance(s, dict) else getattr(s, 'account_count', 0)
    total_acct_count += acct_count

    if ls_str in liability_sheets + equity_sheets + revenue_sheets:
        status = "PASS" if total_credit > 0 else "FAIL (Credits: $0)"
        print(f"  {ls_str} ({name}): Debits=${total_debit:,.0f}, Credits=${total_credit:,.0f}, Net=${net:,.0f} — {status}")

# --- 3B: Net Values ---
print("\n--- 3B: Net Values (Liability/Equity/Revenue should be negative) ---")
for s in summaries:
    ls = s.get('lead_sheet', s.get('letter', '')) if isinstance(s, dict) else getattr(s, 'lead_sheet', '')
    ls_str = str(ls).upper()
    name = s.get('name', '') if isinstance(s, dict) else getattr(s, 'name', '')
    net = s.get('net_balance', 0) if isinstance(s, dict) else getattr(s, 'net_balance', 0)

    if ls_str in liability_sheets + equity_sheets + revenue_sheets:
        status = "PASS" if net < 0 else "FAIL (Net is positive — credits may be missing)"
        print(f"  {ls_str} ({name}): Net=${net:,.0f} — {status}")

# --- 3C: Account Count ---
print("\n--- 3C: Account Count ---")
print(f"  Total lead sheets: {len(summaries)}")
print(f"  Total accounts across sheets: {total_acct_count}")

unclassified = 0
for s in summaries:
    ls = s.get('lead_sheet', s.get('letter', '')) if isinstance(s, dict) else getattr(s, 'lead_sheet', '')
    if str(ls).upper() == 'Z':
        unclassified = s.get('account_count', 0) if isinstance(s, dict) else getattr(s, 'account_count', 0)

print(f"  Unclassified (Z) accounts: {unclassified}")
print(f"  Expected: ~13-16 sheets covering 144 accounts, 0 unclassified")

# Print all sheets summary
print(f"\n  All Lead Sheets:")
for s in summaries:
    ls = s.get('lead_sheet', s.get('letter', '')) if isinstance(s, dict) else getattr(s, 'lead_sheet', '')
    name = s.get('name', '') if isinstance(s, dict) else getattr(s, 'name', '')
    acct_count = s.get('account_count', 0) if isinstance(s, dict) else getattr(s, 'account_count', 0)
    net = s.get('net_balance', 0) if isinstance(s, dict) else getattr(s, 'net_balance', 0)
    print(f"    {ls}: {name} — {acct_count} accounts, Net=${net:,.0f}")

# ============================================================
# TOOL 4: Financial Statements
# ============================================================
print("\n" + "=" * 80)
print("TOOL 4: FINANCIAL STATEMENTS")
print("=" * 80)

from financial_statement_builder import FinancialStatementBuilder

# Serialize lead_sheet_grouping for builder
ls_dict = lead_sheet_grouping
if not isinstance(ls_dict, dict):
    # Try to serialize
    ls_dict = {
        'summaries': [],
        'total_debits': 0,
        'total_credits': 0,
        'unclassified_count': 0,
    }
    if hasattr(lead_sheet_grouping, 'summaries'):
        for s in lead_sheet_grouping.summaries:
            accounts = []
            if hasattr(s, 'accounts'):
                for a in s.accounts:
                    if isinstance(a, dict):
                        accounts.append(a)
                    else:
                        accounts.append({
                            'name': getattr(a, 'name', str(a)),
                            'debit': getattr(a, 'debit', 0),
                            'credit': getattr(a, 'credit', 0),
                        })
            ls_dict['summaries'].append({
                'lead_sheet': str(getattr(s, 'lead_sheet', '')),
                'name': getattr(s, 'name', ''),
                'category': getattr(s, 'category', ''),
                'total_debit': getattr(s, 'total_debit', 0),
                'total_credit': getattr(s, 'total_credit', 0),
                'net_balance': getattr(s, 'net_balance', 0),
                'account_count': getattr(s, 'account_count', 0),
                'accounts': accounts,
            })
        ls_dict['total_debits'] = getattr(lead_sheet_grouping, 'total_debits', 0)
        ls_dict['total_credits'] = getattr(lead_sheet_grouping, 'total_credits', 0)
        ls_dict['unclassified_count'] = getattr(lead_sheet_grouping, 'unclassified_count', 0)

try:
    builder = FinancialStatementBuilder(
        lead_sheet_grouping=ls_dict,
        entity_name="Cascade Manufacturing Inc.",
        period_end="2025-12-31",
    )
    statements = builder.build()

    # --- 4A: Balance Sheet Balance ---
    print("\n--- 4A: Balance Sheet Balance ---")
    print(f"  Total Assets: ${statements.total_assets:,.2f}")
    print(f"  Total Liabilities: ${statements.total_liabilities:,.2f}")
    print(f"  Total Equity: ${statements.total_equity:,.2f}")
    print(f"  L + E: ${statements.total_liabilities + statements.total_equity:,.2f}")
    print(f"  Is Balanced: {statements.is_balanced}")
    print(f"  Balance Difference: ${statements.balance_difference:,.2f}")
    status = "PASS" if statements.is_balanced or abs(statements.balance_difference) < 1 else "FAIL"
    print(f"  Status: {status}")

    # --- 4B: Sign Convention ---
    print("\n--- 4B: Sign Convention ---")
    print(f"  Total Liabilities display value: ${statements.total_liabilities:,.2f}")
    print(f"  Total Equity display value: ${statements.total_equity:,.2f}")
    liab_positive = statements.total_liabilities > 0
    equity_positive = statements.total_equity > 0
    print(f"  Liabilities positive: {'PASS' if liab_positive else 'FAIL (negative)'}")
    print(f"  Equity positive: {'PASS' if equity_positive else 'FAIL (negative)'}")

    # Check individual BS line items
    for item in statements.balance_sheet:
        label = item.get('label', '') if isinstance(item, dict) else getattr(item, 'label', '')
        amount = item.get('amount', 0) if isinstance(item, dict) else getattr(item, 'amount', 0)
        if 'current liab' in label.lower() and 'total' in label.lower():
            print(f"  '{label}': ${amount:,.2f} — {'PASS' if amount > 0 else 'FAIL (negative)'}")
        if 'equity' in label.lower() and 'total' in label.lower():
            print(f"  '{label}': ${amount:,.2f} — {'PASS' if amount > 0 else 'FAIL (negative)'}")

    # --- 4C: Account Mapping ---
    print("\n--- 4C: Account Mapping Completeness ---")
    mapping_trace = getattr(statements, 'mapping_trace', None) or getattr(statements, 'account_mapping_trace', None)
    if mapping_trace:
        mapped_count = len(mapping_trace)
        print(f"  Mapped accounts: {mapped_count}")
        print(f"  Expected: 144 — {'PASS' if mapped_count >= 140 else 'PARTIAL'}")
    else:
        print(f"  Mapping trace not available in statements object")
        print(f"  Available attributes: {[a for a in dir(statements) if not a.startswith('_')]}")

    # --- 4D: Contra Account Treatment ---
    print("\n--- 4D: Contra Account Treatment ---")
    # Check if accumulated depreciation appears net within PP&E
    for item in statements.balance_sheet:
        label = item.get('label', '') if isinstance(item, dict) else getattr(item, 'label', '')
        amount = item.get('amount', 0) if isinstance(item, dict) else getattr(item, 'amount', 0)
        if 'accumulated' in label.lower() or 'depreciation' in label.lower() or 'amortization' in label.lower():
            if amount > 0:
                print(f"  FAIL: '{label}' shows as positive ${amount:,.0f} (should be netted or negative)")
            else:
                print(f"  PASS: '{label}' shows as ${amount:,.0f}")
        if 'property' in label.lower() or 'ppe' in label.lower() or 'plant' in label.lower():
            print(f"  PP&E line: '{label}' = ${amount:,.0f}")

    # --- 4E: Income Statement ---
    print("\n--- 4E: Income Statement ---")
    print(f"  Total Revenue: ${statements.total_revenue:,.2f}")
    print(f"  Gross Profit: ${statements.gross_profit:,.2f}")
    print(f"  Operating Income: ${statements.operating_income:,.2f}")
    print(f"  Net Income: ${statements.net_income:,.2f}")

    gp_reasonable = -50000000 < statements.gross_profit < 50000000 and statements.gross_profit > 0
    print(f"  Gross Profit reasonable (~$4-6M positive): {'PASS' if 2000000 < statements.gross_profit < 8000000 else 'FAIL'}")

    has_opex = False
    for item in statements.income_statement:
        label = item.get('label', '') if isinstance(item, dict) else getattr(item, 'label', '')
        amount = item.get('amount', 0) if isinstance(item, dict) else getattr(item, 'amount', 0)
        if 'operating' in label.lower() and 'expense' in label.lower():
            has_opex = amount != 0
            print(f"  Operating Expenses line: '{label}' = ${amount:,.0f} — {'PASS' if has_opex else 'FAIL ($0)'}")

    # --- 4F: Financial Statement Ratios ---
    print("\n--- 4F: Gross Margin in Financial Statements ---")
    if statements.total_revenue > 0 and statements.gross_profit != 0:
        fs_gross_margin = (statements.gross_profit / statements.total_revenue) * 100
        print(f"  Computed from statements: {fs_gross_margin:.1f}%")
        print(f"  Expected: ~16-18% — {'PASS' if 10 < fs_gross_margin < 25 else 'FAIL'}")
    else:
        print(f"  FAIL: Cannot compute — Revenue: {statements.total_revenue}, GP: {statements.gross_profit}")

except Exception as e:
    print(f"  ERROR building financial statements: {e}")
    import traceback
    traceback.print_exc()

# ============================================================
# TOOL 5: Period-Over-Period Analysis
# ============================================================
print("\n" + "=" * 80)
print("TOOL 5: PERIOD-OVER-PERIOD ANALYSIS")
print("=" * 80)

prior_csv = os.path.join(os.path.dirname(__file__), 'cascade_fy2024_prior.csv')
actual_csv = os.path.join(os.path.dirname(__file__), 'cascade_fy2025_actual.csv')
budget_csv = os.path.join(os.path.dirname(__file__), 'cascade_fy2025_budget.csv')

# --- 5A: File Ingestion ---
print("\n--- 5A: File Ingestion ---")
try:
    df_prior = pd.read_csv(prior_csv)
    df_actual = pd.read_csv(actual_csv)
    df_budget = pd.read_csv(budget_csv)
    print(f"  Prior (FY2024): {len(df_prior)} rows loaded — PASS")
    print(f"  Actual (FY2025): {len(df_actual)} rows loaded — PASS")
    print(f"  Budget (FY2025): {len(df_budget)} rows loaded — PASS")
    print(f"  Columns: {list(df_prior.columns)}")
except Exception as e:
    print(f"  FAIL: {e}")

# Convert DataFrames to account dicts
def df_to_accounts(df):
    accounts = []
    for _, row in df.iterrows():
        accounts.append({
            'account': f"{row['account_number']} — {row['account_name']}",
            'debit': float(row.get('debit', 0) or 0),
            'credit': float(row.get('credit', 0) or 0),
            'type': str(row.get('type', '')).lower(),
        })
    return accounts

prior_accounts = df_to_accounts(df_prior)
current_accounts = df_to_accounts(df_actual)
budget_accounts = df_to_accounts(df_budget)

# --- 5B-5F: Multi-Period Comparison ---
print("\n--- 5B-5F: Multi-Period Comparison ---")
try:
    from multi_period_comparison import compare_trial_balances

    # Current vs Prior
    movement = compare_trial_balances(
        prior_accounts=prior_accounts,
        current_accounts=current_accounts,
        prior_label="FY2024",
        current_label="FY2025",
        materiality_threshold=50000.0,
    )

    print(f"\n  5B Account Matching:")
    num_new = len(movement.new_accounts)
    num_closed = len(movement.closed_accounts)
    sign_changes = movement.movements_by_type.get("sign_change", 0)
    print(f"    New accounts: {num_new} — {movement.new_accounts[:5]}")
    print(f"    Closed accounts: {num_closed} — {movement.closed_accounts[:5]}")
    print(f"    Sign changes: {sign_changes}")

    # Expected: 3 new (1840, 1850, 6940), 0 closed, 1 sign change (1220 WIP)
    new_ok = num_new >= 3
    sign_ok = sign_changes >= 1
    print(f"    New accounts >= 3: {'PASS' if new_ok else f'FAIL (got {num_new})'}")
    print(f"    Sign changes >= 1: {'PASS' if sign_ok else f'FAIL (got {sign_changes})'}")

    print(f"\n  5C YoY Variance Detection:")
    total_movement = sum(abs(m.change_amount) for m in movement.all_movements)
    print(f"    Total movement: ${total_movement:,.0f}")
    print(f"    Lead sheet summaries: {len(movement.lead_sheet_summaries)}")

    # Inspect individual movements for key accounts
    for ls_summary in movement.lead_sheet_summaries:
        for item in ls_summary.movements:
            if abs(item.change_amount) > 400000:
                is_new = item.movement_type.value == "new_account"
                has_sign = item.movement_type.value == "sign_change"
                print(f"      {item.account_name}: delta=${item.change_amount:,.0f} new={is_new} sign_flip={has_sign}")

    # Budget vs Actual
    print(f"\n  5D Budget vs Actual:")
    try:
        budget_movement = compare_trial_balances(
            prior_accounts=budget_accounts,
            current_accounts=current_accounts,
            prior_label="Budget",
            current_label="FY2025 Actual",
            materiality_threshold=50000.0,
        )
        btotal = sum(abs(m.change_amount) for m in budget_movement.all_movements)
        print(f"    Total movement (Budget vs Actual): ${btotal:,.0f}")
        print(f"    New vs budget: {len(budget_movement.new_accounts)}")
        print(f"    Sign changes vs budget: {budget_movement.movements_by_type.get('sign_change', 0)}")

        for ls_summary in budget_movement.lead_sheet_summaries:
            for item in ls_summary.movements:
                if abs(item.change_amount) > 400000:
                    has_sign = item.movement_type.value == "sign_change"
                    print(f"      {item.account_name}: delta=${item.change_amount:,.0f} sign_flip={has_sign}")
    except Exception as e:
        print(f"    ERROR: {e}")

    # 5E: Structural Anomalies
    print(f"\n  5E Structural Anomalies (new accounts in FY2025):")
    for ls_summary in movement.lead_sheet_summaries:
        for item in ls_summary.movements:
            if item.movement_type.value == "new_account":
                print(f"      NEW: {item.account_name}: ${item.change_amount:,.0f}")

    # 5F: Output Quality
    print(f"\n  5F Output Quality:")
    print(f"    Comparison table produced: PASS")
    print(f"    Variances in dollar terms: PASS (change_amount available)")
    has_pct = False
    for ls_summary in movement.lead_sheet_summaries:
        for item in ls_summary.movements:
            if item.change_percent is not None:
                has_pct = True
                break
        if has_pct:
            break
    print(f"    Variances in percentage terms: {'PASS' if has_pct else 'FAIL'}")
    sig_count = len(movement.significant_movements)
    print(f"    Significant movements: {sig_count} {'PASS' if sig_count > 0 else 'CHECK'}")

except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# ============================================================
# DUMP ALL ABNORMAL BALANCES FOR REFERENCE
# ============================================================
print("\n" + "=" * 80)
print("REFERENCE: All abnormal_balances entries")
print("=" * 80)
for i, ab in enumerate(abnormal_balances):
    acct = ab.get('account', '?')
    atype = ab.get('anomaly_type', '?')
    issue = ab.get('issue', '?')[:120]
    amount = ab.get('amount', '?')
    severity = ab.get('severity', '?')
    mat = ab.get('materiality', '?')
    print(f"  [{i+1}] {acct}")
    print(f"      type={atype}, severity={severity}, materiality={mat}, amount={amount}")
    print(f"      issue: {issue}")

print("\n" + "=" * 80)
print("REFERENCE: Analytics ratios structure")
print("=" * 80)
def print_dict(d, indent=2):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict):
                print(f"{'  ' * indent}{k}:")
                print_dict(v, indent + 1)
            elif isinstance(v, list):
                print(f"{'  ' * indent}{k}: [{len(v)} items]")
            else:
                print(f"{'  ' * indent}{k}: {v}")
    else:
        print(f"{'  ' * indent}{d}")

print_dict(analytics)

print("\n\nQA SWEEP COMPLETE")
