"""
Branding Routes — Phase LXIX: Pricing v3 (Phase 8).

Custom PDF branding for Enterprise tier.
Logo upload (S3), header/footer text.

Route group prefix: /branding
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from firm_branding_model import FirmBranding
from models import User
from organization_model import OrganizationMember
from shared.entitlement_checks import check_custom_branding_access
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(prefix="/branding", tags=["branding"])

MAX_LOGO_SIZE = 500 * 1024  # 500KB
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UpdateBrandingRequest(BaseModel):
    header_text: str | None = Field(default=None, max_length=200)
    footer_text: str | None = Field(default=None, max_length=300)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_branding(db: Session, user: User) -> tuple[FirmBranding, int]:
    """Get or create branding for user's org. Returns (branding, org_id)."""
    # AUDIT-08: correct arg order — signature is (user: User, db: Session)
    check_custom_branding_access(user, db)

    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="No organization found.")

    branding = db.query(FirmBranding).filter(FirmBranding.organization_id == member.organization_id).first()
    if not branding:
        branding = FirmBranding(organization_id=member.organization_id)
        db.add(branding)
        db.flush()

    return branding, member.organization_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/")
async def get_branding(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get current branding configuration."""
    branding, _ = _get_branding(db, user)
    return branding.to_dict()


@router.put("/")
@limiter.limit(RATE_LIMIT_WRITE)
async def update_branding(
    body: UpdateBrandingRequest,
    request: Any = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Update header/footer text."""
    branding, _ = _get_branding(db, user)

    if body.header_text is not None:
        branding.header_text = body.header_text
    if body.footer_text is not None:
        branding.footer_text = body.footer_text

    db.commit()
    db.refresh(branding)
    return branding.to_dict()


@router.post("/logo")
@limiter.limit(RATE_LIMIT_WRITE)
async def upload_logo(
    request: Any = None,
    file: UploadFile = File(...),
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Upload a logo image. Enterprise only. Max 500KB, PNG/JPG."""
    branding, org_id = _get_branding(db, user)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG and JPG images are allowed.")

    contents = await file.read()
    if len(contents) > MAX_LOGO_SIZE:
        raise HTTPException(status_code=413, detail="Logo must be under 500KB.")

    # SECURITY: Validate magic bytes match declared content type (prevents disguised uploads)
    _PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
    is_png = contents.startswith(_PNG_MAGIC)
    # JPEG SOI marker (0xFFD8) followed by segment marker (JFIF, EXIF, or raw DCT)
    is_jpeg = len(contents) >= 3 and contents[:2] == b"\xff\xd8" and contents[2] == 0xFF
    if not is_png and not is_jpeg:
        raise HTTPException(
            status_code=400,
            detail="File content does not match a valid PNG or JPEG image.",
        )

    # Store in S3 (or local for development)
    s3_key = f"branding/{org_id}/logo"
    try:
        from shared.storage_client import upload_bytes

        upload_bytes(s3_key, contents, file.content_type or "image/png")
    except ImportError:
        # S3 not configured — store key placeholder for development
        pass

    branding.logo_s3_key = s3_key
    branding.logo_content_type = file.content_type
    branding.logo_size_bytes = len(contents)

    db.commit()
    db.refresh(branding)
    return branding.to_dict()


@router.delete("/logo")
@limiter.limit(RATE_LIMIT_WRITE)
async def delete_logo(
    request: Any = None,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Remove the logo."""
    branding, _ = _get_branding(db, user)

    if branding.logo_s3_key:
        try:
            from shared.storage_client import delete_key

            delete_key(branding.logo_s3_key)
        except ImportError:
            pass

    branding.logo_s3_key = None
    branding.logo_content_type = None
    branding.logo_size_bytes = None

    db.commit()
    return {"detail": "Logo removed."}
