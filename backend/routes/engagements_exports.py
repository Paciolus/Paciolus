"""
Engagement export routes — anomaly summary PDF, diagnostic package ZIP, convergence CSV.

Split from engagements.py (Sprint 539).
"""

import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from analytical_expectation_memo_generator import AnalyticalExpectationMemoGenerator
from anomaly_summary_generator import AnomalySummaryGenerator
from auth import require_current_user, require_verified_user
from database import get_db
from engagement_export import EngagementExporter
from engagement_manager import EngagementManager
from models import User
from security_utils import log_secure_operation
from shared.entitlement_checks import check_export_access
from shared.export_helpers import MEDIA_ZIP, attachment_response, csv_response, pdf_response
from shared.pdf_branding import apply_pdf_branding, load_pdf_branding_context
from shared.rate_limits import RATE_LIMIT_EXPORT, limiter
from sum_schedule_memo_generator import SumScheduleMemoGenerator

router = APIRouter(tags=["engagements"])


@router.post(
    "/engagements/{engagement_id}/export/anomaly-summary",
    dependencies=[Depends(check_export_access)],
)
@limiter.limit(RATE_LIMIT_EXPORT)
def export_anomaly_summary(
    request: Request,
    engagement_id: int,
    fill_from_saved: bool = Query(
        False,
        description=(
            "Fill the Section III worksheet from the dispositions and notes saved in Paciolus, "
            "each with the date it was recorded. Default: a blank worksheet for the firm to complete."
        ),
    ),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    """Generate anomaly summary PDF for an engagement (Sprint 887: optional saved dispositions)."""
    log_secure_operation(
        "anomaly_summary_export",
        f"User {current_user.id} exporting anomaly summary for engagement {engagement_id}",
    )

    generator = AnomalySummaryGenerator(db)

    # Sprint 679 (completion): Enterprise branding on anomaly summary PDFs.
    # apply_pdf_branding no-ops for non-Enterprise tiers.
    branding = load_pdf_branding_context(current_user, db)
    try:
        with apply_pdf_branding(branding):
            pdf_bytes = generator.generate_pdf(current_user.id, engagement_id, fill_from_saved=fill_from_saved)
    except ValueError:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return pdf_response(pdf_bytes, "anomaly_summary.pdf")


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
) -> Response:
    """Generate and stream diagnostic package ZIP for an engagement."""
    log_secure_operation(
        "engagement_package_export",
        f"User {current_user.id} exporting diagnostic package for engagement {engagement_id}",
    )

    exporter = EngagementExporter(db)

    # Sprint 813: the ZIP carries the same anomaly summary PDF the standalone
    # route brands, so it gets the same branding scope.
    branding = load_pdf_branding_context(current_user, db)
    try:
        with apply_pdf_branding(branding):
            zip_bytes, filename = exporter.generate_zip(current_user.id, engagement_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return attachment_response(zip_bytes, filename, MEDIA_ZIP)


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
) -> Response:
    """Export convergence index as CSV."""
    from shared.filenames import safe_csv_writer

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
    # One cell per value through the shared writer: an account name with a comma,
    # quote or line break stays one quoted cell, and formula text is escaped (OUT-01).
    writer = safe_csv_writer(output, lineterminator="\n")
    writer.writerow(["Account", "Convergence Count", "Tools Flagging It"])
    for item in items:
        writer.writerow([item["account"], int(item["convergence_count"]), "; ".join(item["tools_flagging_it"])])

    csv_bytes = output.getvalue().encode("utf-8")

    return csv_response(csv_bytes, f"convergence_index_{engagement_id}.csv")


@router.post(
    "/engagements/{engagement_id}/export/analytical-expectations",
    dependencies=[Depends(check_export_access)],
)
@limiter.limit(RATE_LIMIT_EXPORT)
def export_analytical_expectations(
    request: Request,
    engagement_id: int,
    include_signoff: bool = Query(False, description="Add a sign-off block (off by default)."),
    prepared_by: Optional[str] = Query(None, max_length=200),
    reviewed_by: Optional[str] = Query(None, max_length=200),
    workpaper_date: Optional[str] = Query(None, max_length=40),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    """Sprint 728a (ISA 520): export the analytical-expectations workpaper PDF."""
    log_secure_operation(
        "analytical_expectations_export",
        f"User {current_user.id} exporting ISA 520 workpaper for engagement {engagement_id}",
    )

    generator = AnalyticalExpectationMemoGenerator(db)

    branding = load_pdf_branding_context(current_user, db)
    try:
        with apply_pdf_branding(branding):
            pdf_bytes = generator.generate_pdf(
                current_user.id,
                engagement_id,
                include_signoff=include_signoff,
                prepared_by=prepared_by,
                reviewed_by=reviewed_by,
                workpaper_date=workpaper_date,
            )
    except ValueError:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return pdf_response(pdf_bytes, "analytical_expectations.pdf")


@router.post(
    "/engagements/{engagement_id}/export/sum-schedule",
    dependencies=[Depends(check_export_access)],
)
@limiter.limit(RATE_LIMIT_EXPORT)
def export_sum_schedule(
    request: Request,
    engagement_id: int,
    include_signoff: bool = Query(False, description="Add a sign-off block (off by default)."),
    prepared_by: Optional[str] = Query(None, max_length=200),
    reviewed_by: Optional[str] = Query(None, max_length=200),
    workpaper_date: Optional[str] = Query(None, max_length=40),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> Response:
    """Sprint 729a (ISA 450): export the SUM-schedule workpaper PDF."""
    log_secure_operation(
        "sum_schedule_export",
        f"User {current_user.id} exporting ISA 450 SUM workpaper for engagement {engagement_id}",
    )

    generator = SumScheduleMemoGenerator(db)

    branding = load_pdf_branding_context(current_user, db)
    try:
        with apply_pdf_branding(branding):
            pdf_bytes = generator.generate_pdf(
                current_user.id,
                engagement_id,
                include_signoff=include_signoff,
                prepared_by=prepared_by,
                reviewed_by=reviewed_by,
                workpaper_date=workpaper_date,
            )
    except ValueError:
        raise HTTPException(status_code=404, detail="Engagement not found")

    return pdf_response(pdf_bytes, "sum_schedule.pdf")
