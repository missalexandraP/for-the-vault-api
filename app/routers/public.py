"""Public (unauthenticated) endpoints — landing page and waitlist signup."""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pathlib import Path
import logging

from app.database import get_db
from app.schemas.payment import WaitlistJoinRequest, WaitlistJoinResponse
from app.models.payment import WaitlistInquiry
from app.models.referral import ReferralCode, generate_referral_code
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Public"])

# Path to the static HTML landing page
LANDING_PAGE = Path(__file__).resolve().parent.parent / "static" / "index.html"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_landing_page():
    """Serve the waitlist landing page at the root URL."""
    if LANDING_PAGE.exists():
        return HTMLResponse(content=LANDING_PAGE.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>The Vault</h1><p>Coming soon.</p>", status_code=200)


@router.post("/api/waitlist/join", response_model=WaitlistJoinResponse)
def join_waitlist(
    data: WaitlistJoinRequest,
    db: Session = Depends(get_db),
):
    """Public endpoint: submit a waitlist inquiry from the landing page (no auth required).

    Stores the lead's name, email, desired piece, referral source, and Instagram handle.
    Generates a unique referral code for the signup and sends a confirmation email
    (logged to console in dev mode).
    """
    # Create the waitlist inquiry
    inquiry = WaitlistInquiry(
        full_name=data.full_name.strip(),
        email=data.email.strip().lower(),
        piece=data.piece.strip() if data.piece else None,
        source=data.source.strip() if data.source else None,
        instagram=data.instagram.strip() if data.instagram else None,
    )
    db.add(inquiry)
    db.flush()  # Get the ID without committing yet

    # Generate a unique referral code for this signup
    referral_code = None
    for _ in range(10):
        code_str = generate_referral_code()
        exists = db.query(ReferralCode).filter(ReferralCode.code == code_str).first()
        if not exists:
            ref_code = ReferralCode(
                code=code_str,
                waitlist_inquiry_id=inquiry.id,
            )
            db.add(ref_code)
            db.flush()
            referral_code = code_str
            break

    # Calculate queue position
    queue_position = db.query(WaitlistInquiry).filter(
        WaitlistInquiry.id <= inquiry.id
    ).count()

    db.commit()
    db.refresh(inquiry)

    # Send waitlist confirmation email (logs to console in dev mode)
    try:
        EmailService.send_waitlist_confirmation(
            to_email=inquiry.email,
            name=inquiry.full_name.split()[0] if inquiry.full_name else inquiry.full_name,
            queue_position=queue_position,
            referral_code=referral_code or "",
        )
    except Exception as e:
        logger.warning(f"Failed to send waitlist confirmation email: {e}")

    return WaitlistJoinResponse(
        id=inquiry.id,
        referral_code=referral_code,
        queue_position=queue_position,
        message="You've been added to the waitlist. We'll be in touch.",
    )