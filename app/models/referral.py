"""Referral and invite code models."""

import uuid
import random
import string
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code like VAULT-K7X2M9."""
    chars = string.ascii_uppercase + string.digits
    # Exclude confusing characters: 0, O, I, L
    chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('L', '')
    code = ''.join(random.choices(chars, k=length))
    return f"VAULT-{code}"


class ReferralCode(Base):
    """Unique referral codes assigned to users/waitlist signups."""
    __tablename__ = "referral_codes"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    waitlist_inquiry_id = Column(String, ForeignKey("waitlist_inquiries.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    total_uses = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", backref="referral_codes", foreign_keys=[owner_id])
    referrals = relationship("Referral", back_populates="referral_code", foreign_keys="Referral.referral_code_id")

    def __repr__(self):
        return f"<ReferralCode {self.code}>"


class Referral(Base):
    """Tracks when someone uses a referral code to sign up."""
    __tablename__ = "referrals"

    id = Column(String, primary_key=True, default=generate_uuid)
    referral_code_id = Column(String, ForeignKey("referral_codes.id"), nullable=False, index=True)
    referee_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    referee_waitlist_id = Column(String, ForeignKey("waitlist_inquiries.id"), nullable=True, index=True)
    referee_email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    referral_code = relationship("ReferralCode", back_populates="referrals")
    referee_user = relationship("User", backref="referrals_received", foreign_keys=[referee_user_id])

    def __repr__(self):
        return f"<Referral {self.referral_code_id} -> {self.referee_email}>"