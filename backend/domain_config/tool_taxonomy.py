"""
Central tool taxonomy configuration.

Canonical source for tool classification lists used across engagement analytics,
convergence calculations, workpaper generation, and export flows.

Sprint 539: Extracted from routes/engagements.py to eliminate hardcoded lists.
"""

# GL-account-level tools with convergence extractors
CONVERGENCE_TOOLS: list[str] = [
    "trial_balance",
    "multi_period",
    "journal_entry_testing",
    "ap_testing",
    "revenue_testing",
    "ar_aging",
    "flux_analysis",
]

# Sub-ledger-level tools without GL account fields
CONVERGENCE_EXCLUDED: list[str] = [
    "bank_reconciliation",
    "payroll_testing",
    "three_way_match",
    "fixed_asset_testing",
    "inventory_testing",
    "statistical_sampling",
]

# All supported tool names (convergence + excluded)
ALL_TOOLS: list[str] = CONVERGENCE_TOOLS + CONVERGENCE_EXCLUDED

# Tool display labels for workpaper index and UI
TOOL_DISPLAY_LABELS: dict[str, str] = {
    "trial_balance": "Trial Balance Analysis",
    "multi_period": "Multi-Period Comparison",
    "journal_entry_testing": "Journal Entry Testing",
    "ap_testing": "Accounts Payable Testing",
    "revenue_testing": "Revenue Testing",
    "ar_aging": "AR Aging Analysis",
    "flux_analysis": "Flux Analysis",
    "bank_reconciliation": "Bank Reconciliation",
    "payroll_testing": "Payroll Testing",
    "three_way_match": "Three-Way Match",
    "fixed_asset_testing": "Fixed Asset Testing",
    "inventory_testing": "Inventory Testing",
    "statistical_sampling": "Statistical Sampling",
}
