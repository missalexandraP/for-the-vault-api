"""Waitlist endpoints — join, check, leave, and manage waitlists for unavailable bags."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.payment import (
    WaitlistCreate, WaitlistResponse, WaitlistListResponse,
)
from app.utils.security import get_current_user, require_admin
from app.models.user import User
from app.models.payment import WaitlistEntry
from app.models.inventory import Bag
from app.models.booking import Booking, BookingStatus

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


@router.post("", response_model=WaitlistResponse, status_code=201)
def join_waitlist(
    data: WaitlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Join the waitlist for a bag that's currently unavailable."""
    bag = db.query(Bag).filter(Bag.id == data.bag_id, Bag.is_active == True).first()
    if not bag:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Bag not found")

    # Check if already on waitlist
    existing = db.query(WaitlistEntry).filter(
        WaitlistEntry.user_id == current_user.id,
        WaitlistEntry.bag_id == data.bag_id,
        WaitlistEntry.is_notified == False,
    ).first()
    if existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Already on waitlist for this bag")

    entry = WaitlistEntry(
        user_id=current_user.id,
        bag_id=data.bag_id,
        max_daily_rate=data.max_daily_rate,
        preferred_start_date=data.preferred_start_date,
        preferred_end_date=data.preferred_end_date,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=WaitlistListResponse)
def list_my_waitlist(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's waitlist entries."""
    query = db.query(WaitlistEntry).filter(WaitlistEntry.user_id == current_user.id)
    total = query.count()
    items = query.order_by(WaitlistEntry.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.delete("/{entry_id}", status_code=204)
def leave_waitlist(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a waitlist entry."""
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == entry_id,
        WaitlistEntry.user_id == current_user.id,
    ).first()
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    db.delete(entry)
    db.commit()


@router.get("/check")
def check_waitlist_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll for waitlist availability notifications.

    Returns any waitlist entries where:
    - The bag is now available for the specified dates
    - The user has been notified but hasn't booked yet
    """
    entries = db.query(WaitlistEntry).filter(
        WaitlistEntry.user_id == current_user.id,
    ).all()

    results = []
    for entry in entries:
        bag = db.query(Bag).filter(Bag.id == entry.bag_id).first()
        if not bag:
            continue

        # Check if user has been notified but not converted
        notified_not_converted = entry.is_notified and not entry.is_converted

        # Check if bag is currently available
        now = datetime.utcnow()
        conflicting = db.query(Booking).filter(
            Booking.bag_id == entry.bag_id,
            Booking.status.in_([
                BookingStatus.CONFIRMED, BookingStatus.PREPARING,
                BookingStatus.SHIPPED, BookingStatus.ACTIVE,
                BookingStatus.RETURN_IN_TRANSIT,
            ]),
            Booking.start_date < now,
            Booking.end_date > now,
        ).count()
        is_available = conflicting < bag.stock_quantity and bag.is_available

        results.append({
            "waitlist_id": entry.id,
            "bag_id": entry.bag_id,
            "bag_brand": bag.brand,
            "bag_model": bag.model,
            "max_daily_rate": entry.max_daily_rate,
            "is_available": is_available,
            "is_notified": entry.is_notified,
            "is_converted": entry.is_converted,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        })

    return {"items": results, "total": len(results), "check_time": datetime.utcnow().isoformat()}


@router.post("/notify/{entry_id}", status_code=200)
def mark_notified(
    entry_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: Mark a waitlist entry as notified (e.g. after sending an alert)."""
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.id == entry_id).first()
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Waitlist entry not found")
    entry.is_notified = True
    entry.notified_at = datetime.utcnow()
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "is_notified": True, "notified_at": entry.notified_at.isoformat()}


# --- Admin endpoints ---

@router.get("/admin/all", response_model=WaitlistListResponse)
def list_all_waitlist(
    bag_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: view all waitlist entries, optionally filtered by bag."""
    query = db.query(WaitlistEntry)
    if bag_id:
        query = query.filter(WaitlistEntry.bag_id == bag_id)
    total = query.count()
    items = query.order_by(WaitlistEntry.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}