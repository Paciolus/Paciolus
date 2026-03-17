"""
Paciolus PDF generation package.

Re-exports the public surface that was previously provided by the monolithic
``pdf_generator`` module so that ``from pdf import ...`` works identically.
"""

from pdf.components import (
    DoubleRule,
    LedgerRule,
    create_leader_dots,
    format_classical_date,
    generate_reference_number,
)
from pdf.orchestrator import (
    generate_audit_report,
    generate_financial_statements_pdf,
)
from pdf.styles import (
    ClassicalColors,
    _add_or_replace_style,
    create_classical_styles,
)

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
