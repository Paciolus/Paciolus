"""
Paciolus API — User Profile Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import (
    UserResponse, UserProfileUpdate, PasswordChange,
    update_user_profile, change_user_password,
    require_current_user,
)

router = APIRouter(tags=["users"])


@router.put("/users/me", response_model=UserResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile (name and/or email)."""
    try:
        updated_user = update_user_profile(db, current_user, profile_data)
        return UserResponse.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/me/password")
def change_password(
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
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
