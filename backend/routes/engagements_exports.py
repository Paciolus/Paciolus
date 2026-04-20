"""
Engagement export routes — anomaly summary PDF, diagnostic package ZIP, convergence CSV.

Split from engagements.py (Sprint 539).
"""

import io
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from anomaly_summary_generator import AnomalySummaryGenerator
from auth import require_current_user, require_verified_user
from database import get_db
from engagement_export import EngagementExporter
from engagement_manager import EngagementManager
from models import User
from security_utils import log_secure_operation
from shared.entitlement_checks import check_export_access
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter

router = APIRouter(tags=["engagements"])


@router.post(
    "/engagements/{engagement_id}/export/anomaly-summary",
    dependencies=[Depends(check_export_access)],
)
@limiter.limit(RATE_LIMIT_EXPORT)
def export_anomaly_summary(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate anomaly summary PDF for an engagement."""
    log_secure_operation(
        "anomaly_summary_export",
        f"User {current_user.id} exporting anomaly summary for engagement {engagement_id}",
    )

    generator = AnomalySummaryGenerator(db)

    try:
        pdf_bytes = generator.generate_pdf(current_user.id, engagement_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Engagement not found")

    def iter_pdf() -> Iterator[bytes]:
        chunk_size = 8192
        for i in range(0, len(pdf_bytes), chunk_size):
            yield pdf_bytes[i : i + chunk_size]

    return StreamingResponse(
        iter_pdf(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="anomaly_summary.pdf"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.post(
    "/engagements/{engagement_id}/export/package",
    dependencies=[Depends(check_export_access)],
)
@limiter.limit(RATE_LIMIT_EXPORT)
def export_engagement_package(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and stream diagnostic package ZIP for an engagement."""
    log_secure_operation(
        "engagement_package_export",
        f"User {current_user.id} exporting diagnostic package for engagement {engagement_id}",
    )

    exporter = EngagementExporter(db)

    try:
        zip_bytes, filename = exporter.generate_zip(current_user.id, engagement_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Engagement not found")

    def iter_zip() -> Iterator[bytes]:
        chunk_size = 8192
        for i in range(0, len(zip_bytes), chunk_size):
            yield zip_bytes[i : i + chunk_size]

    return StreamingResponse(
        iter_zip(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(zip_bytes)),
        },
    )


@router.post(
    "/engagements/{engagement_id}/export/convergence-csv",
    dependencies=[Depends(check_export_access)],
)
@limiter.limit(RATE_LIMIT_EXPORT)
def export_convergence_csv(
    request: Request,
    engagement_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export convergence index as CSV."""
    from shared.helpers import sanitize_csv_value

    log_secure_operation(
        "convergence_csv_export",
        f"User {current_user.id} exporting convergence CSV for engagement {engagement_id}",
    )

    manager = EngagementManager(db)
    engagement = manager.get_engagement(current_user.id, engagement_id)

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    items = manager.get_convergence_index(engagement_id)

    output = io.StringIO()
    output.write("Account,Convergence Count,Tools Flagging It\n")
    for item in items:
        account = sanitize_csv_value(item["account"])
        count = item["convergence_count"]
        tools = sanitize_csv_value("; ".join(item["tools_flagging_it"]))
        output.write(f"{account},{count},{tools}\n")

    csv_bytes = output.getvalue().encode("utf-8")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="convergence_index_{engagement_id}.csv"',
            "Content-Length": str(len(csv_bytes)),
        },
    )
