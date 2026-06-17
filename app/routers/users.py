"""User profile and identity verification endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import (
    UserUpdate, UserResponse, UserVerificationCreate,
    UserVerificationResponse,
)
from app.services.auth_service import AuthService
from app.utils.security import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile."""
    return AuthService.update_profile(
        db=db,
        user_id=current_user.id,
        full_name=data.full_name,
        phone=data.phone,
    )


@router.post("/verifications", response_model=UserVerificationResponse)
def submit_verification(
    data: UserVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an identity verification document."""
    return AuthService.submit_verification(
        db=db,
        user_id=current_user.id,
        document_type=data.document_type,
        document_url=data.document_url,
    )


@router.get("/verifications", response_model=list[UserVerificationResponse])
def list_verifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's verification submissions."""
    return current_user.verifications


# --- Admin endpoints ---

@router.put("/verifications/{verification_id}/approve", response_model=UserVerificationResponse)
def approve_verification(
    verification_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: approve a user's identity verification."""
    return AuthService.approve_verification(db=db, verification_id=verification_id)


@router.put("/verifications/{verification_id}/reject", response_model=UserVerificationResponse)
def reject_verification(
    verification_id: str,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: reject a user's identity verification."""
    return AuthService.reject_verification(db=db, verification_id=verification_id, reason=reason)