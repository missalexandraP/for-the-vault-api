"""Authentication endpoints — register, login, identity verification."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    UserVerificationCreate, UserVerificationResponse,
)
from app.services.auth_service import AuthService
from app.utils.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user. Returns JWT token and user data."""
    result = AuthService.register(
        db=db,
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        phone=data.phone,
        invitation_code=data.invitation_code,
    )
    return result


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and return JWT token."""
    result = AuthService.login(db=db, email=data.email, password=data.password)
    return result


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.post("/verify-identity", response_model=UserVerificationResponse)
def verify_identity(
    data: UserVerificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a government ID for identity verification.

    Accepts government ID upload (passport, drivers_license, or id_card).
    Alias for POST /users/verifications.
    """
    return AuthService.submit_verification(
        db=db,
        user_id=current_user.id,
        document_type=data.document_type,
        document_url=data.document_url,
    )


@router.get("/verification-status", response_model=list[UserVerificationResponse])
def verification_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check identity verification status.

    Returns all verification submissions and their current status.
    Alias for GET /users/verifications.
    """
    return current_user.verifications