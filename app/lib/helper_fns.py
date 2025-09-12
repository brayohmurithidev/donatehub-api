from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Donation
from app.features.campaign.models import Campaign
from app.schemas.campaign import CampaignOut, TenantInCampaign


def serialize_campaign(campaign: Campaign, db: Session) -> CampaignOut:
    unique_donor_count = db.query(Donation.donor_email) \
        .filter(Donation.campaign_id == campaign.id) \
        .distinct() \
        .count()
    return CampaignOut(
        id=campaign.id,
        title=campaign.title,
        description=campaign.description,
        goal_amount=campaign.goal_amount,
        status=campaign.status,
        current_amount=campaign.current_amount,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        image_url=campaign.image_url,
        tenant_id=campaign.tenant_id,
        percent_funded=float((campaign.current_amount / campaign.goal_amount) * 100 if campaign.goal_amount else 0),
        days_left=max((campaign.end_date - datetime.now()).days if campaign.end_date else 0, 0),
        total_donors=unique_donor_count,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        tenant=TenantInCampaign(
            id=campaign.tenant.id,
            name=campaign.tenant.name,
            # website=campaign.tenant.website,
            logo_url=campaign.tenant.logo_url,
        )
    )
