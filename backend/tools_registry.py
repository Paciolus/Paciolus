"""
Tools Registry — Sprint 717 single source of truth for the Paciolus catalog.

Every tool that contributes to the marketing-canon "18 tools" claim must
appear in this registry. CI test `tests/test_catalog_consistency.py`
enforces:
  - registry tool count == frontend `tool-ledger.ts` length
  - registry test counts match each engine's actual test list length
  - every tool's cited standards are registered in `standards_registry.py`

Origin: agent-sweep 2026-04-24 — Hallucination Audit C-1 + MarketScout Top-1
launch-blocker found 11 surfaces with the "12 vs 18" tool-count drift after
Sprint 689g flipped the backend constant but didn't propagate to the frontend
catalog or the marketing/legal pages.

The 18 tools = original 12 (Sprint 706 catalog) + 6 NEW from Sprint 689b–g.
Multi-Currency (689a) is excluded from the 18 — it's a side-car panel
already wired into 4 other tools, promoted to a standalone page in 689a but
not a *new* audit tool. (Reflected in the `is_marketing_audit_tool` flag.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Tool:
    """A single Paciolus tool."""

    slug: str  # canonical key matching `enforce_tool_access` and `ToolName` enum
    display_name: str  # short name as shown in nav / tool-ledger
    category: str  # 'Core Analysis' / 'Testing Suite' / 'Advanced'
    test_count: int | None  # number of automated tests in the engine, None for non-test-suite tools
    standards: tuple[str, ...]  # codes that must exist in standards_registry
    is_marketing_audit_tool: bool  # counts toward the "18 tools" marketing claim
    has_dedicated_page: bool  # has /tools/<slug> page (vs side-car only)
    summary: str  # one-liner for tool-ledger.ts
    # Sprint 891 (16A): what the dashboard, activity feed and command surfaces read.
    href: str | None = None  # page URL, None for tools without a dedicated page
    short_label: str = ""  # Quick Launch / activity-feed label
    dashboard_description: str = ""  # empty = not on the dashboard
    dashboard_icon: str = ""  # key in components/dashboard/ToolIcon.tsx


# ───────────────── Registry ─────────────────

TOOLS: Final[tuple[Tool, ...]] = (
    # ── Core Analysis (4) ───────────────────────────────
    Tool(
        slug="trial_balance",
        href="/tools/trial-balance",
        short_label="TB Diagnostics",
        dashboard_description="Ratio analysis, anomaly detection, lead sheets",
        dashboard_icon="chart",
        display_name="Trial Balance Diagnostics",
        category="Core Analysis",
        test_count=None,
        standards=("ISA 520", "ISA 315"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Ratio analysis, anomaly detection, lead-sheet mapping, and financial-statement generation from a single TB upload.",
    ),
    Tool(
        slug="multi_period",
        href="/tools/multi-period",
        short_label="Multi-Period",
        dashboard_description="Trend analysis across reporting periods",
        dashboard_icon="clock",
        display_name="Multi-Period Comparison",
        category="Core Analysis",
        test_count=None,
        standards=("ISA 520",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Side-by-side variance analysis across up to three periods.",
    ),
    Tool(
        slug="bank_reconciliation",
        href="/tools/bank-rec",
        short_label="Bank Rec",
        dashboard_description="Bank-to-book reconciliation testing",
        dashboard_icon="banknotes",
        display_name="Bank Reconciliation",
        category="Core Analysis",
        test_count=None,
        # Sprint 837: ISA 505 removed. The tool reconciles the client's own bank and
        # ledger records (ISA 500); a bank confirmation (ISA 505 / AS 2310) is a
        # separate procedure the auditor may perform.
        standards=("ISA 500",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Match bank statements against book records to surface reconciling items and unexplained discrepancies.",
    ),
    Tool(
        slug="three_way_match",
        href="/tools/three-way-match",
        short_label="Three-Way Match",
        dashboard_description="PO, receipt, and invoice matching",
        dashboard_icon="receipt",
        display_name="Three-Way Match",
        category="Core Analysis",
        test_count=None,
        standards=("ISA 500",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="PO / receiving report / vendor invoice reconciliation to surface procurement anomalies.",
    ),
    # ── Testing Suite (7) ───────────────────────────────
    Tool(
        slug="journal_entry_testing",
        href="/tools/journal-entry-testing",
        short_label="JE Testing",
        dashboard_description="19-test battery incl. Benford and fraud-risk indicators",
        dashboard_icon="shield",
        display_name="Journal Entry Testing",
        category="Testing Suite",
        test_count=19,
        standards=("ISA 240", "AS 2401", "Nigrini 2012"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Benford's Law, structural validation, weekend/holiday posting, round-dollar, reversal-window — 19-test battery over the GL.",
    ),
    Tool(
        slug="ap_testing",
        href="/tools/ap-testing",
        short_label="AP Testing",
        dashboard_description="Duplicate payments, vendor anomalies",
        dashboard_icon="calculator",
        display_name="AP Payment Testing",
        category="Testing Suite",
        test_count=14,
        standards=("ISA 240", "ISA 500", "ACFE 2024"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Duplicate payments, vendor anomalies, ghost vendors, and invoice-without-PO flags across the AP register.",
    ),
    Tool(
        slug="revenue_testing",
        href="/tools/revenue-testing",
        short_label="Revenue Testing",
        dashboard_description="ASC 606 / IFRS 15 contract analysis",
        dashboard_icon="banknotes",
        display_name="Revenue Testing",
        category="Testing Suite",
        test_count=18,
        standards=("ASC 606", "IFRS 15", "ISA 240"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="ASC 606 / IFRS 15 contract-aware revenue testing including cut-off, prior-period timing, and contract validity.",
    ),
    Tool(
        slug="ar_aging",
        href="/tools/ar-aging",
        short_label="AR Aging",
        dashboard_description="Receivables aging and collectibility",
        dashboard_icon="clock",
        display_name="AR Aging",
        category="Testing Suite",
        test_count=12,
        standards=("ISA 540", "ISA 500", "AS 2310"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Aged receivables analysis with collectibility risk, concentration, and sign-anomaly detection.",
    ),
    Tool(
        slug="payroll_testing",
        href="/tools/payroll-testing",
        short_label="Payroll Testing",
        dashboard_description="Ghost-employee indicators, rate anomalies",
        dashboard_icon="calculator",
        display_name="Payroll Testing",
        category="Testing Suite",
        test_count=13,
        standards=("ISA 240",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Ghost-employee indicators, rate anomalies, overtime spikes, gross-to-net reconciliation across the payroll register.",
    ),
    Tool(
        slug="fixed_asset_testing",
        href="/tools/fixed-assets",
        short_label="Fixed Assets",
        dashboard_description="Depreciation, impairment, disposals",
        dashboard_icon="building",
        display_name="Fixed Assets",
        category="Testing Suite",
        test_count=11,
        standards=("ISA 500", "IAS 16", "ASC 360"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Depreciation recalc, impairment indicators, disposals, and lease-classification flags against the FA register.",
    ),
    Tool(
        slug="inventory_testing",
        href="/tools/inventory-testing",
        short_label="Inventory Testing",
        dashboard_description="Valuation, obsolescence, cutoff",
        dashboard_icon="box",
        display_name="Inventory Testing",
        category="Testing Suite",
        test_count=10,
        # Sprint 837: ISA 501 removed — no test involves attending a physical count.
        standards=("ISA 500", "IAS 2", "ASC 330"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Valuation anomalies, LCM/NRV, obsolescence indicators, and cutoff issues across inventory records.",
    ),
    # ── Advanced — Original (1) ─────────────────────────
    Tool(
        slug="statistical_sampling",
        href="/tools/statistical-sampling",
        short_label="Stat Sampling",
        dashboard_description="ISA 530 sample design and evaluation",
        dashboard_icon="percentage",
        display_name="Statistical Sampling",
        category="Advanced",
        test_count=None,
        standards=("ISA 530", "AS 2315", "AICPA Audit Sampling Guide Table A-1"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Monetary unit sampling (Stringer bound) and simple random sampling per ISA 530, with stratification, projection and evaluation.",
    ),
    # ── Advanced — Promoted in 689b–g (6) ───────────────
    Tool(
        slug="sod_checker",
        href="/tools/sod",
        short_label="Segregation of Duties",
        dashboard_description="Conflicting roles and access combinations",
        dashboard_icon="shield",
        display_name="Segregation of Duties",
        category="Advanced",
        test_count=None,
        standards=("SOC 1", "COSO 2013"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Analyze user-role and role-permission matrices against a hardcoded SoD rule library — per-user risk ranking with mitigating control suggestions.",
    ),
    Tool(
        slug="intercompany_elimination",
        href="/tools/intercompany",
        short_label="Intercompany",
        dashboard_description="Elimination entries and mismatches",
        dashboard_icon="building",
        display_name="Intercompany Elimination",
        category="Advanced",
        test_count=None,
        standards=("ASC 810", "IFRS 10", "ISA 600"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Multi-entity TB upload to match reciprocal intercompany balances, propose elimination journal entries, and render a consolidation worksheet.",
    ),
    Tool(
        slug="w2_reconciliation",
        href="/tools/w2-reconciliation",
        short_label="W-2 / W-3",
        dashboard_description="W-2, W-3 and Form 941 reconciliation",
        dashboard_icon="receipt",
        display_name="W-2 / W-3 Reconciliation",
        category="Advanced",
        test_count=None,
        standards=("IRC §6051", "Form W-2", "Form W-3", "Form 941"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Reconcile payroll YTD to draft W-2s, and Form 941 quarterlies to payroll YTD and the W-3, before year-end filing.",
    ),
    Tool(
        slug="form_1099",
        href="/tools/form-1099",
        short_label="1099 Review",
        dashboard_description="Vendor payments against 1099 thresholds",
        dashboard_icon="receipt",
        display_name="1099 Vendor Threshold Review",
        category="Advanced",
        test_count=None,
        standards=("IRC §6041", "IRC §6041A", "Pub 1220"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Identify vendors meeting 1099-NEC / 1099-MISC / 1099-INT thresholds with corporate safe-harbor and processor-exemption logic.",
    ),
    Tool(
        slug="book_to_tax",
        href="/tools/book-to-tax",
        short_label="Book-to-Tax",
        dashboard_description="Schedule M-1 / M-3 and tax provision draft",
        dashboard_icon="calculator",
        display_name="Book-to-Tax Reconciliation",
        category="Advanced",
        test_count=None,
        standards=("Form 1120 Schedule M-1", "Form 1120 Schedule M-3", "ASC 740"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Bridge book pretax income to taxable income with Schedule M-1 / M-3 reconciliation and ASC 740 deferred-tax roll.",
    ),
    Tool(
        slug="cash_flow_projector",
        href="/tools/cash-flow-projector",
        short_label="Cash Flow",
        dashboard_description="90-day cash position across scenarios",
        dashboard_icon="banknotes",
        display_name="Cash Flow Projector",
        category="Advanced",
        test_count=None,
        # Sprint 837: ASC 230 removed — it governs historical cash flow statements,
        # not forecasts. No standard is cited for the projection itself.
        standards=(),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Project 90-day cash position across base / stress / best scenarios with liquidity-breach flagging.",
    ),
    # ── Side-car (not counted toward the 18) ────────────
    Tool(
        slug="currency_rates",
        href="/tools/multi-currency",
        short_label="Multi-Currency",
        display_name="Multi-Currency Conversion",
        category="Advanced",
        test_count=None,
        standards=("IAS 21", "ASC 830"),
        is_marketing_audit_tool=False,  # Side-car panel promoted to standalone page in 689a, not a new audit tool
        has_dedicated_page=True,
        summary="Manage exchange-rate tables and manual rate entries — ISO 4217 validation, cohort-aware staleness detection.",
    ),
)

TOOLS_BY_SLUG: Final[dict[str, Tool]] = {t.slug: t for t in TOOLS}


# ───────────────── Public derived constants ─────────────

# The marketing canon — the "X tools" claim across pricing, terms, marketing pages.
MARKETING_AUDIT_TOOL_COUNT: Final[int] = sum(1 for t in TOOLS if t.is_marketing_audit_tool)


def marketing_audit_tools() -> tuple[Tool, ...]:
    """Return the tools that count toward the marketing-canon tool count."""
    return tuple(t for t in TOOLS if t.is_marketing_audit_tool)


def all_tools() -> tuple[Tool, ...]:
    """Return every tool in the registry, including side-cars."""
    return TOOLS


def get(slug: str) -> Tool:
    """Return the tool by slug or raise KeyError."""
    return TOOLS_BY_SLUG[slug]


def is_registered(slug: str) -> bool:
    """Return True if `slug` matches a registered tool."""
    return slug in TOOLS_BY_SLUG
