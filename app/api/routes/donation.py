from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.index import get_db
from app.db.models import Campaign
from app.db.models.donation import Donation
from app.schemas.donation import DonationOut, DonationCreate

router = APIRouter()

@router.post("/", response_model=DonationOut)
def make_donation(donation_in: DonationCreate, db: Session = Depends(get_db)):
    # 1. Ensure campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == donation_in.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Prevent donation if campaign is over
    now = datetime.now()
    if campaign.end_date and campaign.end_date < now:
        raise HTTPException(status_code=400, detail="This campaign has ended.")

    # 3. Create donation
    donation = Donation(
        amount=donation_in.amount,
        donor_name=donation_in.donor_name,
        donor_email=donation_in.donor_email,
        message=donation_in.message,
        campaign_id=donation_in.campaign_id,
    )

    # 4. Update campaign amount
    campaign.current_amount += donation.amount

    db.add(donation)
    db.commit()
    db.refresh(donation)

    return donation



@router.get("/campaigns/{campaign_id}", response_model=list[DonationOut])
def list_campaign_donations(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    donations = db.query(Donation)\
        .filter(Donation.campaign_id == campaign_id).order_by(Donation.donated_at.desc()).all()

    return donations