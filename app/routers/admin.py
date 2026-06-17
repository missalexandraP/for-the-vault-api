"""Admin dashboard and system management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.utils.security import require_admin
from app.models.user import User
from app.models.booking import Booking
from app.models.inventory import Bag
from app.models.payment import Payment
from app.models.payment import WaitlistEntry

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get aggregated admin dashboard statistics."""
    total_users = db.query(User).count()
    total_bags = db.query(Bag).filter(Bag.is_active == True).count()
    active_bookings = db.query(Booking).filter(
        Booking.status.in_(["confirmed", "preparing", "shipped", "active"])
    ).count()
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "succeeded"
    ).scalar() or 0
    pending_verifications = db.query(User).filter(User.is_verified == False).count()
    waitlist_count = db.query(WaitlistEntry).filter(
        WaitlistEntry.is_notified == False
    ).count()

    return {
        "total_users": total_users,
        "total_bags": total_bags,
        "active_bookings": active_bookings,
        "total_revenue": round(total_revenue, 2),
        "pending_verifications": pending_verifications,
        "waitlist_count": waitlist_count,
    }


@router.get("/users")
def list_all_users(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: list all users."""
    query = db.query(User).order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "is_verified": u.is_verified,
                "is_admin": u.is_admin,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "booking_count": len(u.bookings),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/revenue-overview")
def get_revenue_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: get revenue breakdown."""
    total_rental = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "succeeded",
        Payment.payment_type == "rental",
    ).scalar() or 0

    total_deposits = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "succeeded",
        Payment.payment_type == "deposit",
    ).scalar() or 0

    total_refunds = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "refunded",
    ).scalar() or 0

    total_damage_charges = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "succeeded",
        Payment.payment_type == "damage_charge",
    ).scalar() or 0

    return {
        "total_rental_revenue": round(total_rental, 2),
        "total_deposits_held": round(total_deposits, 2),
        "total_refunds_issued": round(total_refunds, 2),
        "total_damage_charges": round(total_damage_charges, 2),
        "net_revenue": round(total_rental + total_damage_charges - total_refunds, 2),
    }