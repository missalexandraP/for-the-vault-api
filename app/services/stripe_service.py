"""Stripe payment processing service."""

from typing import Optional
import stripe
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus, PaymentType


class StripeService:
    @staticmethod
    def initialize():
        """Initialize Stripe with the secret key."""
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
        else:
            # In dev mode without Stripe, we just log
            pass

    @staticmethod
    async def create_payment_intent(booking: Booking) -> dict:
        """Create a Stripe PaymentIntent for a booking."""
        if not settings.STRIPE_SECRET_KEY:
            # Dev mode: return a mock client secret
            return {
                "client_secret": f"pi_mock_{booking.id}_secret_mock",
                "payment_intent_id": f"pi_mock_{booking.id}",
                "amount": booking.total_amount,
                "currency": "usd",
            }

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(booking.total_amount * 100),  # Stripe uses cents
                currency=booking.currency.lower(),
                metadata={
                    "booking_id": booking.id,
                    "user_id": booking.user_id,
                },
                description=f"The Vault — Booking {booking.id[:8]}",
            )
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": booking.total_amount,
                "currency": booking.currency,
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")

    @staticmethod
    async def confirm_payment(db: Session, payment_intent_id: str) -> Payment:
        """Record a successful payment from a Stripe webhook or client confirmation."""
        # Find or create the payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if payment:
            payment.status = PaymentStatus.SUCCEEDED
            payment.processed_at = __import__('datetime').datetime.utcnow()
            db.commit()
            db.refresh(payment)
            return payment

        raise HTTPException(status_code=404, detail="Payment intent not found")

    @staticmethod
    async def process_refund(payment: Payment, amount: Optional[float] = None) -> Payment:
        """Process a refund for a payment."""
        if not settings.STRIPE_SECRET_KEY or not payment.stripe_payment_intent_id:
            # Dev mode mock
            payment.status = PaymentStatus.REFUNDED
            return payment

        try:
            refund_amount = int((amount or payment.amount) * 100)
            stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
                amount=refund_amount,
            )
            payment.status = PaymentStatus.REFUNDED if amount is None or amount >= payment.amount else PaymentStatus.PARTIALLY_REFUNDED
            payment.refunded_at = __import__('datetime').datetime.utcnow()
            return payment
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Refund error: {str(e)}")

    @staticmethod
    async def handle_webhook(payload: bytes, sig_header: str) -> dict:
        """Handle incoming Stripe webhook events."""
        if not settings.STRIPE_WEBHOOK_SECRET:
            # Dev mode: parse and return the event type
            import json
            event = json.loads(payload)
            return {"type": event.get("type", "unknown"), "processed": True}

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return {"type": event.type, "data": event.data.object, "processed": True}
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    @staticmethod
    def create_payment_record(db: Session, user_id: str, booking_id: str,
                              amount: float, payment_type: str = PaymentType.RENTAL,
                              stripe_payment_intent_id: Optional[str] = None) -> Payment:
        """Create a payment record in the database."""
        payment = Payment(
            user_id=user_id,
            booking_id=booking_id,
            payment_type=payment_type,
            amount=amount,
            stripe_payment_intent_id=stripe_payment_intent_id,
            status=PaymentStatus.PENDING,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment