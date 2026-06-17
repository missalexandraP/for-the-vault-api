"""Pydantic schemas for payments and waitlist."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PaymentIntentCreate(BaseModel):
    booking_id: str
    payment_type: str = "rental"


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: float
    currency: str


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    booking_id: Optional[str] = None
    payment_type: str
    amount: float
    currency: str
    status: str
    stripe_payment_intent_id: Optional[str] = None
    failure_message: Optional[str] = None
    receipt_url: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    items: List[PaymentResponse]
    total: int
    page: int
    page_size: int


class WaitlistCreate(BaseModel):
    bag_id: str
    max_daily_rate: Optional[float] = None
    preferred_start_date: Optional[datetime] = None
    preferred_end_date: Optional[datetime] = None


class WaitlistResponse(BaseModel):
    id: str
    user_id: str
    bag_id: str
    max_daily_rate: Optional[float] = None
    preferred_start_date: Optional[datetime] = None
    preferred_end_date: Optional[datetime] = None
    is_notified: bool
    is_converted: bool
    notified_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WaitlistListResponse(BaseModel):
    items: List[WaitlistResponse]
    total: int
    page: int
    page_size: int


class WaitlistJoinRequest(BaseModel):
    """Public waitlist inquiry from the landing page (no auth required)."""
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    piece: Optional[str] = Field(None, max_length=1000)
    source: Optional[str] = Field(None, max_length=100)
    instagram: Optional[str] = Field(None, max_length=255)


class WaitlistJoinResponse(BaseModel):
    id: str
    message: str = "You've been added to the waitlist. We'll be in touch."