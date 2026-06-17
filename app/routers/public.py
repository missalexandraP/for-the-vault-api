"""Public (unauthenticated) endpoints — landing page and waitlist signup."""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.schemas.payment import WaitlistJoinRequest, WaitlistJoinResponse
from app.models.payment import WaitlistInquiry

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
    """
    inquiry = WaitlistInquiry(
        full_name=data.full_name.strip(),
        email=data.email.strip().lower(),
        piece=data.piece.strip() if data.piece else None,
        source=data.source.strip() if data.source else None,
        instagram=data.instagram.strip() if data.instagram else None,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    return WaitlistJoinResponse(
        id=inquiry.id,
        message="You've been added to the waitlist. We'll be in touch.",
    )