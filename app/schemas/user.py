"""Pydantic schemas for user auth & profile."""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = None
    invitation_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strength requirements."""
        errors = []
        if not re.search(r"[A-Z]", v):
            errors.append("uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("lowercase letter")
        if not re.search(r"[0-9]", v):
            errors.append("number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_+\-=\[\]\\;'/~`]", v):
            errors.append("special character")
        if errors:
            raise ValueError(f"Password must contain at least one {', '.join(errors)}")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (optional)."""
        if v is None:
            return v
        # Strip common formatting
        cleaned = re.sub(r"[\s\-\(\)\.\+]", "", v)
        # Allow digits only, 7-15 chars
        if not re.match(r"^\d{7,15}$", cleaned):
            raise ValueError("Phone number must contain 7-15 digits")
        return v

    @field_validator("full_name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize name — strip whitespace and limit length."""
        return v.strip()[:255]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    is_verified: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = re.sub(r"[\s\-\(\)\.\+]", "", v)
        if not re.match(r"^\d{7,15}$", cleaned):
            raise ValueError("Phone number must contain 7-15 digits")
        return v

    @field_validator("full_name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip()[:255]


class UserVerificationCreate(BaseModel):
    document_type: str = Field(..., pattern="^(passport|drivers_license|id_card)$")
    document_url: str = Field(..., min_length=5, max_length=2048)

    @field_validator("document_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation for document URL."""
        if not v.startswith(("http://", "https://", "s3://")):
            raise ValueError("Document URL must start with http://, https://, or s3://")
        return v.strip()[:2048]


class UserVerificationResponse(BaseModel):
    id: str
    user_id: str
    document_type: str
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True