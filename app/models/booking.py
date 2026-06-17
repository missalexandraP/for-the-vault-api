"""Booking model — reservations and rental periods."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def generate_uuid():
    return str(uuid.uuid4())


class BookingStatus(str, enum.Enum):
    PENDING = "pending"           # Awaiting payment
    CONFIRMED = "confirmed"       # Payment received, bag reserved
    PREPARING = "preparing"       # Being authenticated & packed
    SHIPPED = "shipped"           # In transit to customer
    ACTIVE = "active"             # In customer's possession
    RETURN_IN_TRANSIT = "return_in_transit"  # Being returned
    RETURNED = "returned"         # Received back, pending inspection
    COMPLETED = "completed"       # Inspection passed, booking closed
    CANCELLED = "cancelled"       # Cancelled by customer or admin
    DISPUTED = "disputed"         # Damage/loss dispute


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    bag_id = Column(String, ForeignKey("bags.id"), nullable=False)

    # Rental period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    duration_days = Column(Integer, nullable=False)

    # Pricing
    rental_price = Column(Float, nullable=False)       # Subtotal for rental period
    deposit_amount = Column(Float, nullable=False)      # Security deposit
    insurance_fee = Column(Float, default=0.0)          # Optional insurance
    shipping_fee = Column(Float, default=0.0)           # Shipping cost
    total_amount = Column(Float, nullable=False)         # Grand total
    currency = Column(String(3), default="USD")

    # Status
    status = Column(String(20), default=BookingStatus.PENDING, index=True)
    cancellation_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Shipping
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_zip = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    tracking_number_outbound = Column(String(255), nullable=True)
    tracking_number_inbound = Column(String(255), nullable=True)

    # Return inspection
    returned_condition = Column(String(50), nullable=True)
    damage_notes = Column(Text, nullable=True)
    damage_charge = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="bookings")
    bag = relationship("Bag")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking {self.id} - {self.status}>"