"""Payment endpoints — create payment intents, manage payments, and refunds."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.payment import (
    PaymentIntentCreate, PaymentIntentResponse,
    PaymentResponse, PaymentListResponse,
)
from app.services.stripe_service import StripeService
from app.services.booking_service import BookingService
from app.utils.security import get_current_user, require_admin
from app.models.user import User
from app.models.payment import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe PaymentIntent for a booking."""
    booking = BookingService.get_booking(db=db, booking_id=data.booking_id)

    # Ensure the booking belongs to the current user
    if booking.user_id != current_user.id and not current_user.is_admin:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # Create Stripe PaymentIntent
    intent_data = await StripeService.create_payment_intent(booking)

    # Create payment record in database
    StripeService.create_payment_record(
        db=db,
        user_id=current_user.id,
        booking_id=booking.id,
        amount=booking.total_amount,
        payment_type=data.payment_type,
        stripe_payment_intent_id=intent_data["payment_intent_id"],
    )

    return intent_data


@router.get("", response_model=PaymentListResponse)
def list_my_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's payment history."""
    query = db.query(Payment).filter(Payment.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Payment.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details for a specific payment."""
    from fastapi import HTTPException, status
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return payment


@router.post("/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: str = Query(...),
    amount: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: Issue a refund for a payment (full or partial)."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status != "succeeded":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Cannot refund payment with status '{payment.status}'")

    refunded = await StripeService.process_refund(payment, amount)
    db.commit()
    db.refresh(refunded)
    return refunded