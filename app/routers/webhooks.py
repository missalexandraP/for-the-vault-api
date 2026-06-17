"""Stripe webhook handler — receives payment lifecycle events."""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stripe_service import StripeService
from app.models.payment import Payment
from app.models.booking import Booking, BookingStatus
from datetime import datetime

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle incoming Stripe webhook events.

    Events handled:
    - payment_intent.succeeded: Confirm the booking
    - payment_intent.payment_failed: Mark payment as failed
    - charge.refunded: Mark payment as refunded
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    result = await StripeService.handle_webhook(payload, sig_header)
    event_type = result["type"]

    if event_type == "payment_intent.succeeded":
        data = result.get("data", {})
        payment_intent_id = data.get("id", "")
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if payment:
            payment.status = "succeeded"
            payment.processed_at = datetime.utcnow()

            # Confirm the booking
            if payment.booking_id:
                booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
                if booking and booking.status == BookingStatus.PENDING:
                    booking.status = BookingStatus.CONFIRMED
                    booking.confirmed_at = datetime.utcnow()
            db.commit()

    elif event_type == "payment_intent.payment_failed":
        data = result.get("data", {})
        payment_intent_id = data.get("id", "")
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if payment:
            payment.status = "failed"
            payment.failure_message = data.get("last_payment_error", {}).get("message", "Unknown error")
            db.commit()

    elif event_type == "charge.refunded":
        data = result.get("data", {})
        payment_intent = data.get("payment_intent", "")
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent
        ).first()

        if payment:
            amount_refunded = data.get("amount_refunded", 0) / 100
            if amount_refunded >= payment.amount:
                payment.status = "refunded"
            else:
                payment.status = "partially_refunded"
            payment.refunded_at = datetime.utcnow()
            db.commit()

    return {"received": True}