"""
Branding Routes — Phase LXIX: Pricing v3 (Phase 8).

Custom PDF branding for Enterprise tier.
Logo upload (S3), header/footer text.

Route group prefix: /branding
"""

import io
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import require_current_user
from database import get_db
from firm_branding_model import FirmBranding
from models import User
from organization_model import OrganizationMember, OrgRole
from shared.entitlement_checks import check_custom_branding_access
from shared.organization_schemas import BrandingResponse, DetailResponse
from shared.rate_limits import RATE_LIMIT_WRITE, limiter

router = APIRouter(prefix="/branding", tags=["branding"])

MAX_LOGO_SIZE = 500 * 1024  # 500KB
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg"}
# Sprint 852 (security review L9): a 500 KB PNG can declare a huge canvas, which
# every PDF render would then decode. Dimensions are read from the header only.
MAX_LOGO_SIDE_PX = 4000
MAX_LOGO_PIXELS = 25_000_000


def _validate_logo_dimensions(contents: bytes) -> None:
    """Reject logos over MAX_LOGO_SIDE_PX per side or MAX_LOGO_PIXELS in total.

    ``Image.open`` is lazy: it parses the header (format and size) and does not
    decode pixel data. Pillow itself raises ``DecompressionBombError`` at open
    time for canvases over twice its own pixel limit, so that is a rejection too.
    """
    too_large = HTTPException(
        status_code=400,
        detail=f"Logo must be at most {MAX_LOGO_SIDE_PX}x{MAX_LOGO_SIDE_PX} pixels.",
    )
    try:
        with Image.open(io.BytesIO(contents)) as img:
            image_format = img.format
            width, height = img.size
    except Image.DecompressionBombError:
        raise too_large
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="File content does not match a valid PNG or JPEG image.")
    # MPO is how Pillow reports a multi-picture JPEG (common from phone cameras).
    if image_format not in ("PNG", "JPEG", "MPO"):
        raise HTTPException(status_code=400, detail="Only PNG and JPG images are allowed.")
    if width > MAX_LOGO_SIDE_PX or height > MAX_LOGO_SIDE_PX or width * height > MAX_LOGO_PIXELS:
        raise too_large


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UpdateBrandingRequest(BaseModel):
    header_text: str | None = Field(default=None, max_length=200)
    footer_text: str | None = Field(default=None, max_length=300)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_branding(db: Session, user: User, *, write: bool = False) -> tuple[FirmBranding, int]:
    """Get or create branding for user's org. Returns (branding, org_id).

    Any member may read the branding. ``write=True`` also requires the owner
    or an admin role (Sprint 848, security review M8): the branding appears on
    every memo PDF the firm exports, so a plain member must not be able to
    change it.
    """
    # AUDIT-08: correct arg order — signature is (user: User, db: Session)
    check_custom_branding_access(user, db)

    member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="No organization found.")

    # Same rule and response as shared.organization_policy.require_admin.
    if write and member.role not in (OrgRole.OWNER, OrgRole.ADMIN):
        raise HTTPException(status_code=403, detail="Access denied.")

    branding = db.query(FirmBranding).filter(FirmBranding.organization_id == member.organization_id).first()
    if not branding:
        branding = FirmBranding(organization_id=member.organization_id)
        db.add(branding)
        db.flush()

    return branding, member.organization_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/", response_model=BrandingResponse)
def get_branding(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get current branding configuration."""
    branding, _ = _get_branding(db, user)
    return branding.to_dict()


@router.put("/", response_model=BrandingResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def update_branding(
    body: UpdateBrandingRequest,
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Update header/footer text."""
    branding, _ = _get_branding(db, user, write=True)

    if body.header_text is not None:
        branding.header_text = body.header_text
    if body.footer_text is not None:
        branding.footer_text = body.footer_text

    db.commit()
    db.refresh(branding)
    return branding.to_dict()


@router.post("/logo", response_model=BrandingResponse)
@limiter.limit(RATE_LIMIT_WRITE)
async def upload_logo(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Upload a logo image. Enterprise only. Max 500KB, PNG/JPG."""
    branding, org_id = _get_branding(db, user, write=True)

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
    _validate_logo_dimensions(contents)

    # Store in S3 (or local for development)
    s3_key = f"branding/{org_id}/logo"
    upload_succeeded = False
    try:
        from shared.storage_client import upload_bytes

        upload_succeeded = upload_bytes(s3_key, contents, file.content_type or "image/png")
    except ImportError:
        upload_succeeded = False

    # Sprint 677: Only persist logo metadata when the object is actually in S3.
    # Previously the DB row was committed regardless of upload success, leaving
    # dangling logo_s3_key rows in dev / S3-unconfigured environments that Sprint
    # 679's PDF branding pipeline would then try to fetch and fail on.
    if not upload_succeeded:
        raise HTTPException(
            status_code=503,
            detail="Logo storage is not configured. Contact support to enable custom branding.",
        )

    branding.logo_s3_key = s3_key
    branding.logo_content_type = file.content_type
    branding.logo_size_bytes = len(contents)

    db.commit()
    db.refresh(branding)
    return branding.to_dict()


@router.delete("/logo", response_model=DetailResponse)
@limiter.limit(RATE_LIMIT_WRITE)
def delete_logo(
    request: Request,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Remove the logo."""
    branding, _ = _get_branding(db, user, write=True)

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
