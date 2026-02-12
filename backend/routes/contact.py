"""
Paciolus API — Contact Form
Sprint 132: Public contact form endpoint

POST /contact/submit — rate limited, honeypot-protected
"""
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from typing import Literal

from pydantic import BaseModel, EmailStr, Field
from shared.helpers import safe_background_email
from shared.rate_limits import limiter

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactFormRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    company: str = Field(default="", max_length=200)
    inquiry_type: Literal["General", "Walkthrough Request", "Support", "Enterprise"]
    message: str = Field(..., min_length=10, max_length=5000)
    honeypot: str = Field(default="")


class ContactFormResponse(BaseModel):
    success: bool
    message: str


@router.post("/submit", response_model=ContactFormResponse)
@limiter.limit("3/minute")
def submit_contact_form(
    request: Request,
    form: ContactFormRequest,
    background_tasks: BackgroundTasks,
):
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

    from email_service import send_contact_form_email
    background_tasks.add_task(
        safe_background_email,
        send_contact_form_email,
        label="contact_form",
        name=form.name,
        email=form.email,
        company=form.company,
        inquiry_type=form.inquiry_type,
        message=form.message,
    )

    return ContactFormResponse(
        success=True,
        message="Message received. We'll respond within 1-2 business days."
    )
