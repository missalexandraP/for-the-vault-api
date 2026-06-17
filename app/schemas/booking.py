"""Pydantic schemas for bookings."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    bag_id: str
    start_date: datetime
    end_date: datetime
    shipping_address_line1: str
    shipping_address_line2: Optional[str] = None
    shipping_city: str
    shipping_state: str
    shipping_zip: str
    shipping_country: str = "US"
    insurance_fee: float = 0.0
    notes: Optional[str] = None


class BookingStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    damage_notes: Optional[str] = None
    damage_charge: Optional[float] = None


class BookingUpdate(BaseModel):
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_zip: Optional[str] = None
    shipping_country: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: str
    user_id: str
    bag_id: str
    start_date: datetime
    end_date: datetime
    duration_days: int
    rental_price: float
    deposit_amount: float
    insurance_fee: float
    shipping_fee: float
    total_amount: float
    currency: str
    status: str
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_zip: Optional[str] = None
    shipping_country: Optional[str] = None
    tracking_number_outbound: Optional[str] = None
    tracking_number_inbound: Optional[str] = None
    returned_condition: Optional[str] = None
    damage_notes: Optional[str] = None
    damage_charge: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    items: List[BookingResponse]
    total: int
    page: int
    page_size: int


class AvailabilityCheck(BaseModel):
    bag_id: str
    start_date: datetime
    end_date: datetime


class AvailabilityResponse(BaseModel):
    bag_id: str
    is_available: bool
    conflicting_bookings: int = 0
    available_quantity: int = 0