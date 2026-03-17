"""
Backward-compatibility shim for the decomposed pdf package.

All logic has moved into ``backend/pdf/`` (styles, components, chrome,
sections, orchestrator).  This module re-exports every public symbol so
that existing ``from pdf_generator import X`` statements continue to
resolve without modification.
"""

# Re-export the full public surface from the pdf package
from pdf import (  # noqa: F401 -- re-exports for backward compatibility
    ClassicalColors,
    DoubleRule,
    LedgerRule,
    _add_or_replace_style,
    create_classical_styles,
    create_leader_dots,
    format_classical_date,
    generate_audit_report,
    generate_financial_statements_pdf,
    generate_reference_number,
)

# Keep the class available for any code that references it directly
from pdf.orchestrator import generate_audit_report as _gar  # noqa: F401

__all__ = [
    "ClassicalColors",
    "DoubleRule",
    "LedgerRule",
    "_add_or_replace_style",
    "create_classical_styles",
    "create_leader_dots",
    "format_classical_date",
    "generate_audit_report",
    "generate_financial_statements_pdf",
    "generate_reference_number",
]
