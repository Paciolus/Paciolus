"""
Input validators for Paciolus diagnostic exports.

Validation logic that was previously inline in route handlers is centralized
here. Each validator raises an HTTPException on failure, keeping route handlers
and the pipeline free of validation branching.
"""

from fastapi import HTTPException

from shared.export_schemas import FinancialStatementsInput


def validate_financial_statements_input(payload: FinancialStatementsInput) -> None:
    """Ensure the financial statements payload has the required structure.

    Raises HTTPException(400) if lead_sheet_grouping contains no summaries.
    """
    summaries = payload.lead_sheet_grouping.get("summaries", [])
    if not summaries:
        raise HTTPException(status_code=400, detail="lead_sheet_grouping must contain non-empty 'summaries' list")
