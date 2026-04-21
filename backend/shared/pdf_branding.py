"""Sprint 679: PDF branding context loader.

The ``FirmBranding`` model (``firm_branding_model.py``), ``POST /branding/*``
routes, ``upload_bytes`` storage client, and ``custom_branding`` entitlement
gate have existed since Phase LXIX (Pricing v3). The only thing missing was
the wiring from those stored assets into the PDF output pipeline — marketing
pages, pricing, UpgradeModal, Settings, and ``domain/pricing.ts`` all promised
"Custom PDF branding" as the Enterprise differentiator, but **zero memo
generators read ``logo_s3_key``, ``header_text``, or ``footer_text``**. This
module closes that gap.

Load flow
---------
Route handler receives ``current_user``. Calls
``load_pdf_branding_context(current_user, db)`` which:

  1. Resolves the user's organization (if any).
  2. Checks the user's effective entitlement for ``custom_branding``. Returns
     a blank ``PDFBrandingContext`` (all fields None) when the tier doesn't
     include branding OR when no ``FirmBranding`` row exists.
  3. Downloads the logo bytes from S3 via ``shared.storage_client.download_bytes``.
     Logo download failures (missing object, bad creds, etc.) degrade to
     no-logo branding rather than crashing PDF generation.
  4. Returns a populated ``PDFBrandingContext`` — consumer memo templates
     inspect ``tier_has_branding`` and swap the default Paciolus logo for
     the firm's logo on success.

Design principles
-----------------
* Zero-Storage compliance — logo bytes are held only in memory for the
  duration of PDF generation; never persisted outside the S3 object store.
* Best-effort — a branding lookup that fails (DB disconnect, S3 timeout,
  corrupted object) falls back to default Paciolus branding. The user
  still gets a PDF.
* Cache-friendly — the returned context is immutable; callers can pass it
  through ``run_pipeline`` without defensive copying.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PDFBrandingContext:
    """Immutable branding payload passed through to PDF generators.

    When ``tier_has_branding`` is False, consumers MUST render the default
    Paciolus branding — the other fields may still be populated (e.g., if
    a user downgraded from Enterprise) but are not authorised for use.
    """

    tier_has_branding: bool = False
    logo_bytes: Optional[bytes] = None
    logo_content_type: Optional[str] = None
    header_text: Optional[str] = None
    footer_text: Optional[str] = None

    # Diagnostic metadata — helps audit why a branding override didn't fire.
    # Consumers should not render these fields; they're for logging only.
    resolution_notes: tuple[str, ...] = field(default_factory=tuple)

    def effective_header_text(self) -> Optional[str]:
        """Return ``header_text`` only when the tier is authorised.

        Guardrail so a downgraded user's previously-saved header doesn't
        leak into a PDF they're no longer entitled to.
        """
        return self.header_text if self.tier_has_branding else None

    def effective_footer_text(self) -> Optional[str]:
        """Return ``footer_text`` only when the tier is authorised."""
        return self.footer_text if self.tier_has_branding else None

    def effective_logo_bytes(self) -> Optional[bytes]:
        """Return ``logo_bytes`` only when the tier is authorised."""
        return self.logo_bytes if self.tier_has_branding else None


# Sentinel used everywhere a branding context is optional — saves callers
# from allocating a fresh instance on every PDF build.
BLANK_BRANDING = PDFBrandingContext()


# =============================================================================
# Sprint 679: ContextVar-based branding propagation
# =============================================================================
#
# Threading a ``branding_context`` kwarg through 18 memo-generator
# signatures was the alternative to a ContextVar. ContextVar wins on
# three grounds:
#
#  1. **Zero-touch memo generators.** Wrapper functions already carry
#     10+ kwargs each; adding a 19th bloats the surface and risks
#     partial-threading bugs (route passes it, wrapper forgets to forward).
#  2. **Scope-safe.** asyncio context propagation is automatic; PDF builds
#     that happen inside ``asyncio.to_thread`` still see the context
#     because ``run_in_executor`` copies the current context snapshot.
#  3. **Reset-safe.** The context manager below guarantees the ContextVar
#     resets after the ``with`` block exits, even on exceptions — so a
#     failed PDF build never leaks branding into the next request.
#
# Route code:
#
#     branding = load_pdf_branding_context(current_user, db)
#     with apply_pdf_branding(branding):
#         pdf_bytes = generate_ap_testing_memo(result, ...)
#
# Memo template reads via ``current_pdf_branding()`` — falls back to
# ``BLANK_BRANDING`` if no context has been applied.

_PDF_BRANDING_CV: ContextVar[PDFBrandingContext] = ContextVar(
    "paciolus_pdf_branding",
    default=BLANK_BRANDING,
)


def current_pdf_branding() -> PDFBrandingContext:
    """Return the active branding context for this request / async task.

    Returns ``BLANK_BRANDING`` when no branding has been applied — memo
    templates can read this unconditionally.
    """
    return _PDF_BRANDING_CV.get()


@contextmanager
def apply_pdf_branding(branding: Optional[PDFBrandingContext]):
    """Scope a ``PDFBrandingContext`` to the enclosed block.

    ``branding`` may be None — this is the common case when the caller
    doesn't need branding. The context manager is a no-op in that case
    so callers can wrap unconditionally:

        branding = load_pdf_branding_context(user, db)
        with apply_pdf_branding(branding):
            pdf_bytes = generate_memo(...)

    The ContextVar resets on block exit even when an exception fires,
    so a partial branding state never leaks.
    """
    if branding is None or branding is BLANK_BRANDING:
        # Fast path — nothing to set.
        yield
        return

    token = _PDF_BRANDING_CV.set(branding)
    try:
        yield
    finally:
        _PDF_BRANDING_CV.reset(token)


def load_pdf_branding_context(
    user: object,
    db: object,
) -> PDFBrandingContext:
    """Resolve the caller's PDF branding context.

    ``user`` is the authenticated ``User`` (typed loosely to avoid a
    ``models`` import at the shared layer). ``db`` is the SQLAlchemy
    session — also loosely typed for the same reason.

    Returns ``BLANK_BRANDING`` on any failure path — logo download issues,
    missing org, tier downgrade, or simply no FirmBranding row. The
    caller's PDF should fall back to the default Paciolus branding
    automatically.
    """
    notes: list[str] = []

    try:
        # Lazy imports to keep the shared layer out of the engine/model
        # import graph at module load time.
        from shared.entitlement_checks import get_effective_entitlements

        entitlements = get_effective_entitlements(user, db)
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("pdf_branding: entitlement lookup failed: %s", type(exc).__name__)
        return PDFBrandingContext(
            resolution_notes=("entitlement_lookup_failed",),
        )

    if not getattr(entitlements, "custom_branding", False):
        return PDFBrandingContext(
            tier_has_branding=False,
            resolution_notes=("tier_lacks_custom_branding",),
        )

    # Resolve org membership — branding is stored per-organization.
    try:
        if not isinstance(db, Session):
            # Not a real DB session (e.g., unit-test Depends stand-in) —
            # can't fetch the FirmBranding row; return blank rather than
            # crash.
            return PDFBrandingContext(
                tier_has_branding=True,
                resolution_notes=("db_not_a_session",),
            )

        from firm_branding_model import FirmBranding
        from organization_model import OrganizationMember

        member = db.query(OrganizationMember).filter(OrganizationMember.user_id == getattr(user, "id", None)).first()
        if member is None:
            return PDFBrandingContext(
                tier_has_branding=True,
                resolution_notes=("no_organization_membership",),
            )

        branding = db.query(FirmBranding).filter(FirmBranding.organization_id == member.organization_id).first()
        if branding is None:
            return PDFBrandingContext(
                tier_has_branding=True,
                resolution_notes=("no_firm_branding_row",),
            )
    except Exception as exc:
        logger.warning("pdf_branding: DB lookup failed: %s", type(exc).__name__)
        return PDFBrandingContext(
            tier_has_branding=True,
            resolution_notes=("db_lookup_failed",),
        )

    header_text = branding.header_text
    footer_text = branding.footer_text
    logo_bytes: Optional[bytes] = None
    logo_content_type: Optional[str] = None

    if branding.logo_s3_key:
        try:
            from shared.storage_client import download_bytes

            logo_bytes = download_bytes(branding.logo_s3_key)
            if logo_bytes is None:
                # Sprint 677's DB-integrity fix ensures we shouldn't hit
                # this path normally; but defensive against stale rows
                # that predate that fix.
                notes.append("logo_s3_fetch_returned_none")
            else:
                logo_content_type = branding.logo_content_type
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning(
                "pdf_branding: logo download failed: %s",
                type(exc).__name__,
            )
            logo_bytes = None
            notes.append("logo_s3_fetch_exception")

    return PDFBrandingContext(
        tier_has_branding=True,
        logo_bytes=logo_bytes,
        logo_content_type=logo_content_type,
        header_text=header_text,
        footer_text=footer_text,
        resolution_notes=tuple(notes),
    )
