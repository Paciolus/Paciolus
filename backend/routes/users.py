"""
Paciolus API — User Profile Routes
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import (
    UserResponse, UserProfileUpdate, PasswordChange,
    update_user_profile, change_user_password,
    require_current_user,
)
from email_service import send_verification_email
from shared.helpers import safe_background_email
from shared.response_schemas import SuccessResponse
from shared.rate_limits import limiter, RATE_LIMIT_AUTH
from shared.error_messages import sanitize_error

router = APIRouter(tags=["users"])


@router.put("/users/me", response_model=UserResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def update_profile(
    request: Request,
    profile_data: UserProfileUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's profile (name and/or email)."""
    try:
        updated_user, verification_token = update_user_profile(db, current_user, profile_data)

        # Sprint 203: Send verification email to new address + notification to old
        if verification_token and updated_user.pending_email:
            background_tasks.add_task(
                safe_background_email,
                send_verification_email,
                label="email_change_verification",
                to_email=updated_user.pending_email,
                token=verification_token,
                user_name=updated_user.name,
            )
            from email_service import send_email_change_notification
            background_tasks.add_task(
                safe_background_email,
                send_email_change_notification,
                label="email_change_notification",
                to_email=updated_user.email,
                new_email=updated_user.pending_email,
                user_name=updated_user.name,
            )

        return UserResponse.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="user_profile_validation", allow_passthrough=True,
        ))


@router.put("/users/me/password", response_model=SuccessResponse)
@limiter.limit(RATE_LIMIT_AUTH)
def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    try:
        success = change_user_password(
            db, current_user,
            password_data.current_password,
            password_data.new_password
        )
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect"
            )
        return {"success": True, "message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=sanitize_error(
            e, log_label="password_change_validation", allow_passthrough=True,
        ))
