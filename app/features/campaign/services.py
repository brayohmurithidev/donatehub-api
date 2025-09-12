from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.features.campaign.models import Campaign


# Create Campaign


# Get Campaign -> By ID
def fetch_campaign(db: Session, campaign_id: UUID):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    return campaign


# Get Campaigns
def fetch_campaigns(db: Session, active_only: bool = False):
    query = db.query(Campaign)
    print("active only: ", active_only)
    if active_only:
        now = datetime.now()
        query = query.filter(Campaign.start_date <= now, Campaign.end_date >= now)
    return query.all()


# Update Campaign
def update_campaign(db: Session, campaign_id: UUID, data):
    campaign = fetch_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")


# Delete campaign
def delete_campaign(db: Session, campaign_id: UUID):
    pass
