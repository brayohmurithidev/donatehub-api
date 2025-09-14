from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.features.campaign.models import Campaign


# Create Campaign
def create_new_campaign(db: Session, data):
    campaign = Campaign(**data)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


# Get Campaign -> By ID
def fetch_campaign(db: Session, campaign_id: UUID):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).options(joinedload(Campaign.tenant)).first()
    return campaign


def fetch_campaign_by_title(db: Session, title: str):
    campaign = db.query(Campaign).filter(Campaign.title.ilike(title)).options(joinedload(Campaign.tenant)).first()
    return campaign


# Get Campaigns
def fetch_campaigns(db: Session, active_only: bool = False):
    query = db.query(Campaign).options(joinedload(Campaign.tenant))
    print("active only: ", active_only)
    if active_only:
        now = datetime.now()
        query = query.filter(Campaign.start_date <= now, Campaign.end_date >= now)
    return query.all()


# Update Campaign
def update_campaign_data(db: Session, campaign_id: UUID, data):
    for key, value in data.items():
        setattr(db.query(Campaign).filter(Campaign.id == campaign_id).first(), key, value)
    db.commit()
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


# Delete campaign
def delete_campaign(db: Session, campaign_id: UUID):
    pass
