"""Referral system endpoints — invite codes, claiming, and stats."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.payment import WaitlistInquiry
from app.models.referral import ReferralCode, Referral, generate_referral_code
from app.schemas.payment import (
    ReferralCodeResponse, ReferralClaimRequest, ReferralClaimResponse,
    ReferralStatsResponse,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/referral", tags=["Referral"])


def _get_or_create_referral_code(owner_id: str = None, waitlist_id: str = None, db: Session = None) -> ReferralCode:
    """Get existing referral code for a user/waitlist inquiry, or create a new one."""
    if owner_id:
        existing = db.query(ReferralCode).filter(
            ReferralCode.owner_id == owner_id,
            ReferralCode.is_active == True,
        ).first()
        if existing:
            return existing

    if waitlist_id:
        existing = db.query(ReferralCode).filter(
            ReferralCode.waitlist_inquiry_id == waitlist_id,
            ReferralCode.is_active == True,
        ).first()
        if existing:
            return existing

    # Create new unique code
    for _ in range(10):  # Retry loop for uniqueness
        code_str = generate_referral_code()
        exists = db.query(ReferralCode).filter(ReferralCode.code == code_str).first()
        if not exists:
            new_code = ReferralCode(
                code=code_str,
                owner_id=owner_id,
                waitlist_inquiry_id=waitlist_id,
            )
            db.add(new_code)
            db.flush()
            return new_code

    raise HTTPException(status_code=500, detail="Failed to generate unique referral code")


@router.get("/my-code", response_model=ReferralCodeResponse)
def get_my_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the authenticated user's referral code.

    If the user doesn't have one yet, a new code is generated.
    """
    code = _get_or_create_referral_code(owner_id=current_user.id, db=db)
    db.commit()
    db.refresh(code)
    return code


@router.post("/claim", response_model=ReferralClaimResponse)
def claim_referral(
    data: ReferralClaimRequest,
    db: Session = Depends(get_db),
):
    """Claim a referral code when joining the waitlist (no auth required).

    Records that someone used a referral code, creating a link between
    the referrer and the new signup.
    """
    # Find the referral code
    code = db.query(ReferralCode).filter(
        ReferralCode.code == data.code.strip().upper(),
        ReferralCode.is_active == True,
    ).first()

    if not code:
        raise HTTPException(status_code=404, detail="Invalid referral code")

    # Check if this email already claimed a referral
    existing = db.query(Referral).filter(
        Referral.referee_email == data.email.strip().lower(),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This email has already used a referral code")

    # Create the referral record
    referral = Referral(
        referral_code_id=code.id,
        referee_email=data.email.strip().lower(),
    )
    code.total_uses += 1
    db.add(referral)
    db.commit()

    return ReferralClaimResponse(
        success=True,
        message="Referral code accepted. Welcome to The Vault!",
        referrer_code=data.code.strip().upper(),
    )


@router.get("/stats", response_model=ReferralStatsResponse)
def get_referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get referral stats for the authenticated user.

    Shows how many people used their referral code.
    """
    code = db.query(ReferralCode).filter(
        ReferralCode.owner_id == current_user.id,
        ReferralCode.is_active == True,
    ).first()

    if not code:
        return ReferralStatsResponse(
            referral_code=None,
            total_referrals=0,
            successful_signups=0,
        )

    total = db.query(Referral).filter(
        Referral.referral_code_id == code.id,
    ).count()

    return ReferralStatsResponse(
        referral_code=code.code,
        total_referrals=total,
        successful_signups=total,
    )