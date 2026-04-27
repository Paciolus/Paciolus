"""
Standards Registry — Sprint 717 single source of truth for cited audit / accounting standards.

Every standard cited on a customer-facing surface (marketing pages, trust page,
USER_GUIDE, memo PDFs) must appear in this registry. CI test
`tests/test_citation_consistency.py` enforces the contract.

Adding a new standard:
1. Add the entry below with `body`, `code`, `title`, and `usage` notes.
2. Cite it where it belongs in code/copy.
3. The CI test will pass.

Removing a standard:
1. Find every citing surface (CI test will list them on a removal attempt).
2. Replace or remove citations.
3. Then remove the registry entry.

Origin: agent-sweep 2026-04-24 — Hallucination Audit C-4 + Accounting Methodology
Audit Rank-1 found "PCAOB AS 1215" cited on 5 customer-facing files where the
correct standard is AS 2401 (the platform's actual JE-testing reference).
The registry exists so this drift is mechanically detectable next time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class Standard:
    """A single cited audit / accounting standard."""

    body: str  # 'PCAOB' / 'ISA' / 'IAASB' / 'AICPA' / 'ASC' / 'IFRS' / 'IAS' / 'IRS'
    code: str  # 'AS 2401' / 'ISA 240' / 'ASC 606' / etc.
    title: str  # short human-readable title
    usage: tuple[str, ...] = field(default_factory=tuple)  # where the platform uses it


# ───────────────────────── Registry ─────────────────────────

STANDARDS: Final[tuple[Standard, ...]] = (
    # ── PCAOB Auditing Standards ─────────────────────────────
    Standard(
        body="PCAOB",
        code="AS 1215",
        title="Audit Documentation",
        usage=("Workpaper retention guidance only — not currently a primary citation on any tool.",),
    ),
    Standard(
        body="PCAOB",
        code="AS 2305",
        title="Substantive Analytical Procedures",
        usage=("flux engine", "ratio engine", "multi-period TB"),
    ),
    Standard(
        body="PCAOB",
        code="AS 2310",
        title="The Confirmation Process",
        usage=("bank reconciliation memo", "AR aging memo"),
    ),
    Standard(
        body="PCAOB",
        code="AS 2315",
        title="Audit Sampling",
        usage=("sampling engine", "sampling memo generator"),
    ),
    Standard(
        body="PCAOB",
        code="AS 2401",
        title="Consideration of Fraud in a Financial Statement Audit",
        usage=(
            "JE testing engine + memo (primary)",
            "AP testing memo",
            "payroll testing memo",
            "revenue testing memo",
        ),
    ),
    Standard(
        body="PCAOB",
        code="AS 2501",
        title="Auditing Accounting Estimates, Including Fair Value Measurements",
        usage=("AR aging memo", "fixed asset memo", "inventory memo"),
    ),
    # ── ISA / IAASB ──────────────────────────────────────────
    Standard(
        body="ISA",
        code="ISA 240",
        title="The Auditor's Responsibilities Relating to Fraud",
        usage=("JE testing", "AP testing", "payroll testing", "revenue testing"),
    ),
    Standard(
        body="ISA",
        code="ISA 265",
        title="Communicating Deficiencies in Internal Control",
        usage=("Boundary reference for memo language — what we do NOT classify",),
    ),
    Standard(
        body="ISA",
        code="ISA 315",
        title="Identifying and Assessing the Risks of Material Misstatement",
        usage=("composite risk engine (Appendix 1 RMM matrix)",),
    ),
    Standard(
        body="ISA",
        code="ISA 320",
        title="Materiality in Planning and Performing an Audit",
        usage=("engagement-layer materiality cascade",),
    ),
    Standard(
        body="ISA",
        code="ISA 330",
        title="The Auditor's Responses to the Assessed Risks",
        usage=("composite risk follow-on",),
    ),
    Standard(
        body="ISA",
        code="ISA 450",
        title="Evaluation of Misstatements Identified During the Audit",
        usage=("(future Sprint 729 — SUM schedule)",),
    ),
    Standard(
        body="ISA", code="ISA 500", title="Audit Evidence", usage=("AP, three-way match, fixed asset, inventory memos",)
    ),
    Standard(
        body="ISA",
        code="ISA 501",
        title="Audit Evidence — Specific Considerations for Selected Items",
        usage=("inventory memo",),
    ),
    Standard(body="ISA", code="ISA 505", title="External Confirmations", usage=("bank reconciliation memo",)),
    Standard(
        body="ISA",
        code="ISA 520",
        title="Analytical Procedures",
        usage=("flux engine", "ratio engine", "multi-period TB", "TB diagnostics"),
    ),
    Standard(body="ISA", code="ISA 530", title="Audit Sampling", usage=("sampling engine + memo (primary)",)),
    Standard(
        body="ISA",
        code="ISA 540",
        title="Auditing Accounting Estimates and Related Disclosures",
        usage=("AR aging memo", "fixed asset depreciation memo"),
    ),
    Standard(body="ISA", code="ISA 570", title="Going Concern", usage=("going concern engine + PDF section",)),
    Standard(body="ISA", code="ISA 580", title="Written Representations", usage=("memo retention guidance",)),
    Standard(
        body="ISA",
        code="ISA 600",
        title="Special Considerations — Audits of Group Financial Statements",
        usage=("intercompany elimination tool",),
    ),
    # ── ASC (FASB Codification) ───────────────────────────────
    Standard(
        body="ASC",
        code="ASC 230",
        title="Statement of Cash Flows",
        usage=("cash flow statement generator (indirect method)",),
    ),
    Standard(
        body="ASC",
        code="ASC 250",
        title="Accounting Changes and Error Corrections",
        usage=("classification validator notes",),
    ),
    Standard(body="ASC", code="ASC 330", title="Inventory", usage=("inventory testing memo",)),
    Standard(
        body="ASC",
        code="ASC 360",
        title="Property, Plant, and Equipment",
        usage=("fixed asset memo", "depreciation calculator"),
    ),
    Standard(
        body="ASC",
        code="ASC 606",
        title="Revenue from Contracts with Customers",
        usage=("revenue testing engine + memo (contract-aware)",),
    ),
    Standard(body="ASC", code="ASC 740", title="Income Taxes", usage=("book-to-tax reconciliation tool",)),
    Standard(body="ASC", code="ASC 810", title="Consolidation", usage=("intercompany elimination tool",)),
    Standard(body="ASC", code="ASC 830", title="Foreign Currency Matters", usage=("multi-currency conversion tool",)),
    Standard(
        body="ASC",
        code="ASC 842",
        title="Leases",
        usage=("lease classification indicator", "fixed asset memo lease flag"),
    ),
    Standard(
        body="ASC",
        code="ASC 326",
        title="Credit Losses (CECL)",
        usage=("AR aging — collectibility risk references in marketing copy",),
    ),
    # ── IFRS / IAS ───────────────────────────────────────────
    Standard(
        body="IFRS", code="IFRS 10", title="Consolidated Financial Statements", usage=("intercompany elimination tool",)
    ),
    Standard(
        body="IFRS",
        code="IFRS 15",
        title="Revenue from Contracts with Customers",
        usage=("revenue testing engine + memo (contract-aware)",),
    ),
    Standard(body="IFRS", code="IFRS 16", title="Leases", usage=("lease classification indicator (IFRS-aligned)",)),
    Standard(
        body="IAS",
        code="IAS 1",
        title="Presentation of Financial Statements",
        usage=("financial statement generator — disclosure framing",),
    ),
    Standard(body="IAS", code="IAS 2", title="Inventories", usage=("inventory testing memo",)),
    Standard(
        body="IAS",
        code="IAS 7",
        title="Statement of Cash Flows",
        usage=("cash flow statement generator (indirect method)",),
    ),
    Standard(
        body="IAS",
        code="IAS 16",
        title="Property, Plant and Equipment",
        usage=("fixed asset memo", "depreciation calculator"),
    ),
    Standard(
        body="IAS",
        code="IAS 21",
        title="The Effects of Changes in Foreign Exchange Rates",
        usage=("multi-currency conversion tool",),
    ),
    # ── AICPA / AU-C ─────────────────────────────────────────
    Standard(
        body="AICPA",
        code="AU-C 450",
        title="Evaluation of Misstatements Identified During the Audit",
        usage=("(future Sprint 729 — SUM schedule)",),
    ),
    Standard(
        body="AICPA",
        code="AICPA Audit Sampling Guide Table A-1",
        title="Confidence factor / expansion factor table",
        usage=("sampling engine — `shared/aicpa_tables.py`", "sampling memo"),
    ),
    # ── IRS / Tax / Forms ────────────────────────────────────
    Standard(
        body="IRS", code="IRC §6041", title="Information returns at source", usage=("Form 1099 preparation tool",)
    ),
    Standard(
        body="IRS",
        code="IRC §6041A",
        title="Information returns regarding services",
        usage=("Form 1099 preparation tool",),
    ),
    Standard(body="IRS", code="IRC §6051", title="Receipts for employees (W-2)", usage=("W-2 reconciliation tool",)),
    Standard(
        body="IRS",
        code="Pub 1220",
        title="Specifications for Electronic Filing of Information Returns",
        usage=("Form 1099 preparation tool",),
    ),
    Standard(body="IRS", code="Pub 946", title="How To Depreciate Property", usage=("depreciation calculator",)),
    Standard(body="IRS", code="Form W-2", title="Wage and Tax Statement", usage=("W-2 reconciliation tool",)),
    Standard(
        body="IRS", code="Form W-3", title="Transmittal of Wage and Tax Statements", usage=("W-2 reconciliation tool",)
    ),
    Standard(
        body="IRS", code="Form 941", title="Employer's Quarterly Federal Tax Return", usage=("W-2 reconciliation tool",)
    ),
    Standard(
        body="IRS",
        code="Form 1120 Schedule M-1",
        title="Reconciliation of Income (Loss) per Books",
        usage=("book-to-tax reconciliation tool",),
    ),
    Standard(
        body="IRS",
        code="Form 1120 Schedule M-3",
        title="Net Income (Loss) Reconciliation",
        usage=("book-to-tax reconciliation tool",),
    ),
    # ── Frameworks / Other ───────────────────────────────────
    Standard(
        body="COSO",
        code="COSO 2013",
        title="Internal Control — Integrated Framework",
        usage=("segregation of duties tool",),
    ),
    Standard(
        body="AICPA",
        code="SOC 1",
        title="Reporting on Controls at a Service Organization",
        usage=("segregation of duties tool",),
    ),
    Standard(
        body="ACFE",
        code="ACFE 2024",
        title="Report to the Nations on Occupational Fraud",
        usage=("AP testing engine — fraud-pattern coverage rationale",),
    ),
    Standard(
        body="Nigrini",
        code="Nigrini 2012",
        title="Benford's Law: Applications for Forensic Accounting",
        usage=("JE testing — Benford minimum-N=300 rationale",),
    ),
)

STANDARDS_BY_CODE: Final[dict[str, Standard]] = {s.code: s for s in STANDARDS}


def is_registered(code: str) -> bool:
    """Return True if `code` is a registered standard."""
    return code in STANDARDS_BY_CODE


def get(code: str) -> Standard:
    """Return the registered standard or raise KeyError."""
    return STANDARDS_BY_CODE[code]


def all_codes() -> tuple[str, ...]:
    """Return every registered code in registration order."""
    return tuple(s.code for s in STANDARDS)
