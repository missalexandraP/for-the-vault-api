"""Payment and waitlist models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def generate_uuid():
    return str(uuid.uuid4())


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentType(str, enum.Enum):
    RENTAL = "rental"
    DEPOSIT = "deposit"
    INSURANCE = "insurance"
    SHIPPING = "shipping"
    DAMAGE_CHARGE = "damage_charge"
    REFUND = "refund"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=True, index=True)

    # Stripe
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    stripe_charge_id = Column(String(255), nullable=True)

    # Payment details
    payment_type = Column(String(50), nullable=False, default=PaymentType.RENTAL)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(20), default=PaymentStatus.PENDING, index=True)
    failure_message = Column(Text, nullable=True)

    # Receipt
    receipt_url = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payments")
    booking = relationship("Booking", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.id} - ${self.amount} - {self.status}>"


class WaitlistEntry(Base):
    """Customers waiting for a specific bag to become available."""
    __tablename__ = "waitlist_entries"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    bag_id = Column(String, ForeignKey("bags.id"), nullable=False, index=True)

    # Preferences
    max_daily_rate = Column(Float, nullable=True)  # Max they're willing to pay per day
    preferred_start_date = Column(DateTime, nullable=True)
    preferred_end_date = Column(DateTime, nullable=True)

    # Status
    is_notified = Column(Boolean, default=False)  # Whether we've notified them
    is_converted = Column(Boolean, default=False)  # Whether they booked after notification
    notified_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="waitlist_entries")
    bag = relationship("Bag")

    def __repr__(self):
        return f"<WaitlistEntry {self.user_id} -> {self.bag_id}>"


class WaitlistInquiry(Base):
    """Pre-registration inquiries from the landing page waitlist form (no auth required)."""
    __tablename__ = "waitlist_inquiries"

    id = Column(String, primary_key=True, default=generate_uuid)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    piece = Column(Text, nullable=True)  # Which bag they're looking for
    source = Column(String(100), nullable=True)  # How they heard about us
    instagram = Column(String(255), nullable=True)  # Instagram handle
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WaitlistInquiry {self.email}>"