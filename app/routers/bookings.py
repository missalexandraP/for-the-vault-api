"""Booking endpoints — create, manage, and track reservations."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.booking import (
    BookingCreate, BookingResponse, BookingListResponse,
    AvailabilityCheck, AvailabilityResponse,
)
from app.services.booking_service import BookingService
from app.utils.security import get_current_user, require_verified, require_admin
from app.models.user import User

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(
    data: BookingCreate,
    current_user: User = Depends(require_verified),
    db: Session = Depends(get_db),
):
    """Create a new booking. Requires identity verification."""
    return BookingService.create_booking(
        db=db,
        user_id=current_user.id,
        data=data.model_dump(),
    )


@router.get("", response_model=BookingListResponse)
def list_my_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's bookings."""
    return BookingService.get_user_bookings(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details for a specific booking."""
    booking = BookingService.get_booking(db=db, booking_id=booking_id)
    # Users can only see their own bookings; admins can see all
    if booking.user_id != current_user.id and not current_user.is_admin:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: str,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a booking (only if in pending or confirmed status)."""
    return BookingService.cancel_booking(
        db=db,
        booking_id=booking_id,
        user_id=current_user.id,
        reason=reason,
    )


@router.post("/availability", response_model=AvailabilityResponse)
def check_availability(
    data: AvailabilityCheck,
    db: Session = Depends(get_db),
):
    """Check if a bag is available for a given date range."""
    return BookingService.check_availability(
        db=db,
        bag_id=data.bag_id,
        start=data.start_date,
        end=data.end_date,
    )


# --- Admin endpoints ---

@router.get("/admin/all", response_model=BookingListResponse)
def list_all_bookings(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: list all bookings with optional status filter."""
    return BookingService.list_all_bookings(
        db=db,
        status_filter=status,
        page=page,
        page_size=page_size,
    )


@router.put("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: str,
    status: str = Query(...),
    notes: Optional[str] = Query(None),
    damage_notes: Optional[str] = Query(None),
    damage_charge: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update booking status (e.g., confirm, ship, return, complete)."""
    return BookingService.update_booking_status(
        db=db,
        booking_id=booking_id,
        status=status,
        notes=notes,
        damage_notes=damage_notes,
        damage_charge=damage_charge,
    )