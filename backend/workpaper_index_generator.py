"""
Workpaper Index Generator — Sprint 100
Phase X: Engagement Layer

Generates a document register, file manifest, and cross-reference matrix
for an engagement. Auditor sign-off fields are BLANK by design.

ZERO-STORAGE: Reads tool run metadata and follow-up item summaries only.
No financial data is stored or transmitted.
"""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.orm import Session

from models import Client
from engagement_model import Engagement, ToolRun, ToolName, ToolRunStatus
from follow_up_items_model import FollowUpItem, FollowUpSeverity, FollowUpDisposition


# ---------------------------------------------------------------------------
# Display maps
# ---------------------------------------------------------------------------

TOOL_LABELS = {
    ToolName.TRIAL_BALANCE: "TB Diagnostics",
    ToolName.MULTI_PERIOD: "Multi-Period Comparison",
    ToolName.JOURNAL_ENTRY_TESTING: "Journal Entry Testing",
    ToolName.AP_TESTING: "AP Payment Testing",
    ToolName.BANK_RECONCILIATION: "Bank Reconciliation",
    ToolName.PAYROLL_TESTING: "Payroll & Employee Testing",
    ToolName.THREE_WAY_MATCH: "Three-Way Match Validator",
    ToolName.REVENUE_TESTING: "Revenue Testing",
}

TOOL_LEAD_SHEET_REFS = {
    ToolName.TRIAL_BALANCE: ["A-Z (all lead sheets)"],
    ToolName.MULTI_PERIOD: ["Comparative analysis"],
    ToolName.JOURNAL_ENTRY_TESTING: ["JE-1 through JE-18"],
    ToolName.AP_TESTING: ["AP-1 through AP-13"],
    ToolName.BANK_RECONCILIATION: ["C (Cash & equivalents)"],
    ToolName.PAYROLL_TESTING: ["PR-1 through PR-11"],
    ToolName.THREE_WAY_MATCH: ["TWM-1 (PO/Invoice/Receipt)"],
    ToolName.REVENUE_TESTING: ["RT-1 through RT-12"],
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class WorkpaperIndexGenerator:
    """Generates workpaper index data for an engagement."""

    def __init__(self, db: Session):
        self.db = db

    def _verify_engagement_access(
        self, user_id: int, engagement_id: int
    ) -> Optional[Engagement]:
        """Verify engagement exists and user has access through client ownership."""
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id == user_id,
            )
            .first()
        )

    def generate(self, user_id: int, engagement_id: int) -> dict:
        """
        Generate workpaper index for an engagement.

        Returns dict with:
        - engagement metadata (client_name, period)
        - document_register: list of tool entries with run counts and status
        - follow_up_summary: counts by severity, disposition, tool_source
        - sign_off: BLANK fields for auditor (prepared_by, reviewed_by, date)
        """
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client #{engagement.client_id}"

        # Build document register from tool runs
        tool_runs = (
            self.db.query(ToolRun)
            .filter(ToolRun.engagement_id == engagement_id)
            .order_by(ToolRun.run_at.desc())
            .all()
        )

        # Group by tool
        runs_by_tool: dict[ToolName, list[ToolRun]] = {}
        for run in tool_runs:
            runs_by_tool.setdefault(run.tool_name, []).append(run)

        document_register = []
        for tool_name in ToolName:
            runs = runs_by_tool.get(tool_name, [])
            latest = runs[0] if runs else None

            document_register.append({
                "tool_name": tool_name.value,
                "tool_label": TOOL_LABELS.get(tool_name, tool_name.value),
                "run_count": len(runs),
                "last_run_date": latest.run_at.isoformat() if latest and latest.run_at else None,
                "status": "completed" if runs else "not_started",
                "lead_sheet_refs": TOOL_LEAD_SHEET_REFS.get(tool_name, []),
            })

        # Follow-up item summary
        follow_up_items = (
            self.db.query(FollowUpItem)
            .filter(FollowUpItem.engagement_id == engagement_id)
            .all()
        )

        by_severity: dict[str, int] = {}
        by_disposition: dict[str, int] = {}
        by_tool_source: dict[str, int] = {}

        for item in follow_up_items:
            sev = item.severity.value if item.severity else "unknown"
            by_severity[sev] = by_severity.get(sev, 0) + 1

            disp = item.disposition.value if item.disposition else "unknown"
            by_disposition[disp] = by_disposition.get(disp, 0) + 1

            src = item.tool_source or "unknown"
            by_tool_source[src] = by_tool_source.get(src, 0) + 1

        follow_up_summary = {
            "total_count": len(follow_up_items),
            "by_severity": by_severity,
            "by_disposition": by_disposition,
            "by_tool_source": by_tool_source,
        }

        return {
            "engagement_id": engagement_id,
            "client_name": client_name,
            "period_start": engagement.period_start.isoformat() if engagement.period_start else "",
            "period_end": engagement.period_end.isoformat() if engagement.period_end else "",
            "generated_at": datetime.now(UTC).isoformat(),
            "document_register": document_register,
            "follow_up_summary": follow_up_summary,
            "sign_off": {
                "prepared_by": "",
                "reviewed_by": "",
                "date": "",
            },
        }
