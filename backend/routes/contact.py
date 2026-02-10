"""
Paciolus API — Contact Form
Sprint 132: Public contact form endpoint

POST /contact/submit — rate limited, honeypot-protected
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, EmailStr, Field
from shared.rate_limits import limiter

router = APIRouter(prefix="/contact", tags=["contact"])

VALID_INQUIRY_TYPES = ["General", "Walkthrough Request", "Support", "Enterprise"]


class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    company: str = Field(default="", max_length=200)
    inquiry_type: str = Field(..., min_length=1)
    message: str = Field(..., min_length=10, max_length=5000)
    honeypot: str = Field(default="")


class ContactFormResponse(BaseModel):
    success: bool
    message: str


@router.post("/submit", response_model=ContactFormResponse)
@limiter.limit("3/minute")
async def submit_contact_form(request: Request, form: ContactFormRequest):
    """
    Submit a contact form inquiry.
    Public endpoint — no auth required.
    """
    # Honeypot check: bots fill hidden fields
    if form.honeypot:
        # Return success to not tip off bots, but don't actually send
        return ContactFormResponse(
            success=True,
            message="Message received. We'll respond within 1-2 business days."
        )

    # Validate inquiry type
    if form.inquiry_type not in VALID_INQUIRY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid inquiry type. Must be one of: {', '.join(VALID_INQUIRY_TYPES)}"
        )

    # Send email
    from email_service import send_contact_form_email
    result = send_contact_form_email(
        name=form.name,
        email=form.email,
        company=form.company,
        inquiry_type=form.inquiry_type,
        message=form.message,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail="Failed to send message. Please try again later.")

    return ContactFormResponse(
        success=True,
        message="Message received. We'll respond within 1-2 business days."
    )
