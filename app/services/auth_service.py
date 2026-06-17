"""Authentication and user management service."""

from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserVerification
from app.utils.security import hash_password, verify_password, create_access_token
from app.services.email_service import EmailService


class AuthService:
    @staticmethod
    def register(db: Session, email: str, password: str, full_name: str,
                 phone: str = None, invitation_code: str = None) -> dict:
        """Register a new user. Returns tokens and user data."""
        # Check if email already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check invitation code if required (for invite-only phase)
        # In the MVP, we accept any valid-looking code or allow open registration
        # Future: validate against an invitation codes table

        user = User(
            email=email,
            full_name=full_name,
            phone=phone,
            password_hash=hash_password(password),
            invitation_code=invitation_code,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Send welcome email (non-blocking — logs to console in dev)
        try:
            EmailService.send_welcome_email(
                to_email=user.email,
                name=user.full_name,
                invite_code=invitation_code or f"VAULT-{user.id[:8].upper()}",
            )
        except Exception:
            pass  # Email failure should not block registration

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
            },
        }

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        """Authenticate a user and return tokens."""
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
            },
        }

    @staticmethod
    def get_profile(db: Session, user_id: str) -> User:
        """Get a user's profile."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def update_profile(db: Session, user_id: str, full_name: str = None, phone: str = None) -> User:
        """Update a user's profile."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if full_name is not None:
            user.full_name = full_name
        if phone is not None:
            user.phone = phone
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def submit_verification(db: Session, user_id: str, document_type: str, document_url: str) -> UserVerification:
        """Submit an identity verification document."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        verification = UserVerification(
            user_id=user_id,
            document_type=document_type,
            document_url=document_url,
            status="pending",
        )
        db.add(verification)
        db.commit()
        db.refresh(verification)
        return verification

    @staticmethod
    def approve_verification(db: Session, verification_id: str) -> UserVerification:
        """Admin: approve a verification document."""
        verification = db.query(UserVerification).filter(UserVerification.id == verification_id).first()
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")
        verification.status = "approved"
        verification.verified_at = __import__('datetime').datetime.utcnow()
        # Mark user as verified
        user = db.query(User).filter(User.id == verification.user_id).first()
        if user:
            user.is_verified = True
        db.commit()
        db.refresh(verification)
        return verification

    @staticmethod
    def reject_verification(db: Session, verification_id: str, reason: str) -> UserVerification:
        """Admin: reject a verification document."""
        verification = db.query(UserVerification).filter(UserVerification.id == verification_id).first()
        if not verification:
            raise HTTPException(status_code=404, detail="Verification not found")
        verification.status = "rejected"
        verification.rejection_reason = reason
        db.commit()
        db.refresh(verification)
        return verification