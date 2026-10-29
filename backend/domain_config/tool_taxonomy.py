"""
Central tool taxonomy configuration.

Canonical source for tool classification lists used across engagement analytics,
convergence calculations, workpaper generation, and export flows.

Sprint 539: Extracted from routes/engagements.py to eliminate hardcoded lists.
"""

# GL-account-level tools with convergence extractors.
#
# Sprint 787: this list is exactly the key set of
# `shared/account_extractors.ACCOUNT_EXTRACTORS` — a tool can only contribute to the
# convergence index if something can pull GL account identifiers out of its result.
# `tests/test_toolname_catalog_parity.py` asserts that equivalence, so adding a tool
# here without an extractor (or vice versa) fails the build.
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
    # Sprint 787 — the Sprint 689 tools. None produces GL-account-level findings:
    # SoD works on user/role matrices, 1099 and W-2/W-3 on vendor and employee
    # records, book-to-tax on an income bridge, and the projector on forward
    # scenarios rather than findings at all. Intercompany is the one plausible
    # future convergence candidate, but that needs an account extractor written
    # first — classification cannot substitute for the extractor.
    "sod_checker",
    "intercompany_elimination",
    "w2_reconciliation",
    "form_1099",
    "book_to_tax",
    "cash_flow_projector",
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
    # Sprint 787 — the Sprint 689 tools
    "sod_checker": "Segregation of Duties",
    "intercompany_elimination": "Intercompany Elimination",
    "w2_reconciliation": "W-2 / W-3 Reconciliation",
    "form_1099": "1099 Vendor Threshold Review",
    "book_to_tax": "Book-to-Tax Reconciliation",
    "cash_flow_projector": "Cash Flow Projector",
}
