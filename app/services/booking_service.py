"""Booking management service."""

from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.booking import Booking, BookingStatus
from app.models.inventory import Bag
from app.models.user import User
from app.services.email_service import EmailService


class BookingService:
    @staticmethod
    def _calculate_duration(start: datetime, end: datetime) -> int:
        """Calculate the number of days in a rental period."""
        delta = end - start
        days = delta.days
        if delta.seconds > 0:
            days += 1  # Round up partial days
        return max(1, days)

    @staticmethod
    def _check_availability(db: Session, bag_id: str, start: datetime, end: datetime,
                            exclude_booking_id: Optional[str] = None) -> bool:
        """Check if a bag is available for the given period."""
        query = db.query(Booking).filter(
            Booking.bag_id == bag_id,
            Booking.status.in_([
                BookingStatus.CONFIRMED,
                BookingStatus.PREPARING,
                BookingStatus.SHIPPED,
                BookingStatus.ACTIVE,
                BookingStatus.RETURN_IN_TRANSIT,
            ]),
            Booking.start_date < end,
            Booking.end_date > start,
        )
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
        return query.count() == 0

    @staticmethod
    def create_booking(db: Session, user_id: str, data: dict) -> Booking:
        """Create a new booking reservation."""
        bag = db.query(Bag).filter(Bag.id == data["bag_id"], Bag.is_active == True).first()
        if not bag:
            raise HTTPException(status_code=404, detail="Bag not found or unavailable")

        start = data["start_date"]
        end = data["end_date"]
        if end <= start:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        duration = BookingService._calculate_duration(start, end)

        if not BookingService._check_availability(db, bag.id, start, end):
            raise HTTPException(status_code=409, detail="Bag is not available for the selected dates")

        # Calculate pricing
        rental_price = round(bag.rental_price_per_day * duration, 2)
        deposit_amount = bag.deposit_amount
        insurance_fee = data.get("insurance_fee", 0.0)
        shipping_fee = data.get("shipping_fee", 0.0)  # Can be calculated based on address
        total_amount = round(rental_price + deposit_amount + insurance_fee + shipping_fee, 2)

        booking = Booking(
            user_id=user_id,
            bag_id=bag.id,
            start_date=start,
            end_date=end,
            duration_days=duration,
            rental_price=rental_price,
            deposit_amount=deposit_amount,
            insurance_fee=insurance_fee,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            status=BookingStatus.PENDING,
            shipping_address_line1=data.get("shipping_address_line1"),
            shipping_address_line2=data.get("shipping_address_line2"),
            shipping_city=data.get("shipping_city"),
            shipping_state=data.get("shipping_state"),
            shipping_zip=data.get("shipping_zip"),
            shipping_country=data.get("shipping_country", "US"),
            notes=data.get("notes"),
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get_booking(db: Session, booking_id: str) -> Booking:
        """Get a booking by ID."""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking

    @staticmethod
    def get_user_bookings(db: Session, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        """Get all bookings for a user."""
        query = db.query(Booking).filter(Booking.user_id == user_id)
        total = query.count()
        query = query.order_by(Booking.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def list_all_bookings(db: Session, status_filter: Optional[str] = None,
                          page: int = 1, page_size: int = 20) -> dict:
        """Admin: list all bookings with optional status filter."""
        query = db.query(Booking)
        if status_filter:
            query = query.filter(Booking.status == status_filter)
        total = query.count()
        query = query.order_by(Booking.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def update_booking_status(db: Session, booking_id: str, status: str,
                              notes: Optional[str] = None,
                              damage_notes: Optional[str] = None,
                              damage_charge: Optional[float] = None) -> Booking:
        """Update booking status. Used by admins and the system."""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        now = datetime.utcnow()
        status_ts_map = {
            BookingStatus.CONFIRMED: "confirmed_at",
            BookingStatus.RETURNED: "returned_at",
            BookingStatus.COMPLETED: "completed_at",
            BookingStatus.CANCELLED: "cancelled_at",
        }

        booking.status = status
        if status in status_ts_map:
            setattr(booking, status_ts_map[status], now)

        if notes is not None:
            booking.notes = notes
        if damage_notes is not None:
            booking.damage_notes = damage_notes
        if damage_charge is not None:
            booking.damage_charge = damage_charge

        # When cancelled, make sure the bag is marked as available
        if status == BookingStatus.CANCELLED:
            booking.cancellation_reason = notes

        db.commit()
        db.refresh(booking)

        # Send email notifications on status changes
        user = db.query(User).filter(User.id == booking.user_id).first()
        bag = db.query(Bag).filter(Bag.id == booking.bag_id).first()
        bag_name = f"{bag.brand} {bag.model}" if bag else "your bag"

        import logging
        logger = logging.getLogger(__name__)

        if status == BookingStatus.CONFIRMED and user:
            try:
                EmailService.send_booking_confirmation(
                    to_email=user.email,
                    name=user.full_name,
                    bag_name=bag_name,
                    start_date=booking.start_date.strftime("%b %d, %Y") if booking.start_date else "",
                    end_date=booking.end_date.strftime("%b %d, %Y") if booking.end_date else "",
                    duration=booking.duration_days,
                    total_amount=booking.total_amount,
                    booking_id=booking.id,
                )
            except Exception as e:
                logger.warning(f"Failed to send booking confirmation email: {e}")

        return booking

    @staticmethod
    def check_availability(db: Session, bag_id: str, start: datetime, end: datetime) -> dict:
        """Check bag availability for a date range."""
        bag = db.query(Bag).filter(Bag.id == bag_id, Bag.is_active == True).first()
        if not bag:
            raise HTTPException(status_code=404, detail="Bag not found")

        is_available = BookingService._check_availability(db, bag_id, start, end)

        # Count conflicting bookings
        conflict_count = 0
        if not is_available:
            conflict_count = db.query(Booking).filter(
                Booking.bag_id == bag_id,
                Booking.status.in_([
                    BookingStatus.CONFIRMED,
                    BookingStatus.PREPARING,
                    BookingStatus.SHIPPED,
                    BookingStatus.ACTIVE,
                    BookingStatus.RETURN_IN_TRANSIT,
                ]),
                Booking.start_date < end,
                Booking.end_date > start,
            ).count()

        return {
            "bag_id": bag_id,
            "is_available": is_available,
            "conflicting_bookings": conflict_count,
            "available_quantity": bag.stock_quantity if is_available else 0,
        }

    @staticmethod
    def cancel_booking(db: Session, booking_id: str, user_id: str, reason: Optional[str] = None) -> Booking:
        """Cancel a booking (by user or admin)."""
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == user_id,
        ).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel booking in '{booking.status}' status"
            )

        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = reason
        booking.cancelled_at = datetime.utcnow()
        db.commit()
        db.refresh(booking)
        return booking