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


# ───────────────── Registry ─────────────────

TOOLS: Final[tuple[Tool, ...]] = (
    # ── Core Analysis (4) ───────────────────────────────
    Tool(
        slug="trial_balance",
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
        display_name="Multi-Period Comparison",
        category="Core Analysis",
        test_count=None,
        standards=("ISA 520",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Side-by-side variance analysis across up to three periods with reclassification detection.",
    ),
    Tool(
        slug="bank_reconciliation",
        display_name="Bank Reconciliation",
        category="Core Analysis",
        test_count=None,
        standards=("ISA 505", "ISA 500"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Match bank statements against book records to surface reconciling items and unexplained discrepancies.",
    ),
    Tool(
        slug="three_way_match",
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
        display_name="Payroll Testing",
        category="Testing Suite",
        test_count=13,
        standards=("ISA 240",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Ghost-employee detection, rate anomalies, overtime spikes, gross-to-net reconciliation across the payroll register.",
    ),
    Tool(
        slug="fixed_asset_testing",
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
        display_name="Inventory Testing",
        category="Testing Suite",
        test_count=10,
        standards=("ISA 501", "IAS 2", "ASC 330"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Valuation anomalies, LCM/NRV, obsolescence indicators, and cutoff issues across inventory records.",
    ),
    # ── Advanced — Original (1) ─────────────────────────
    Tool(
        slug="statistical_sampling",
        display_name="Statistical Sampling",
        category="Advanced",
        test_count=None,
        standards=("ISA 530", "AS 2315", "AICPA Audit Sampling Guide Table A-1"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="MUS + classical variables + attribute sampling per ISA 530 with full projection + evaluation workflow.",
    ),
    # ── Advanced — Promoted in 689b–g (6) ───────────────
    Tool(
        slug="sod_checker",
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
        display_name="W-2 / W-3 Reconciliation",
        category="Advanced",
        test_count=None,
        standards=("IRC §6051", "Form W-2", "Form W-3", "Form 941"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Reconcile payroll YTD to draft W-2s and Form 941 quarterlies before year-end filing.",
    ),
    Tool(
        slug="form_1099",
        display_name="Form 1099 Preparation",
        category="Advanced",
        test_count=None,
        standards=("IRC §6041", "IRC §6041A", "Pub 1220"),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Identify vendors meeting 1099-NEC / 1099-MISC / 1099-INT thresholds with corporate safe-harbor and processor-exemption logic.",
    ),
    Tool(
        slug="book_to_tax",
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
        display_name="Cash Flow Projector",
        category="Advanced",
        test_count=None,
        standards=("ASC 230",),
        is_marketing_audit_tool=True,
        has_dedicated_page=True,
        summary="Project 90-day cash position across base / stress / best scenarios with liquidity-breach flagging.",
    ),
    # ── Side-car (not counted toward the 18) ────────────
    Tool(
        slug="currency_rates",
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
