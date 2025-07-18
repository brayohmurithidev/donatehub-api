from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_tenant_admin
from app.db.index import get_db
from app.db.models import Tenant, Campaign, Donation
from app.schemas.campaign import CampaignOut, CampaignCreate, CampaignUpdate, CampaignStats

router = APIRouter()

@router.post('/', response_model=CampaignOut)
def create_campaign(
        campaign_in: CampaignCreate,
        db: Session = Depends(get_db),
        user = Depends(require_tenant_admin)
    ):
    # get tenant of this user
    tenant = db.query(Tenant).filter(Tenant.admin_id == user.id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this user")

    new_campaign = Campaign(
        title=campaign_in.title,
        description=campaign_in.description,
        goal_amount=campaign_in.goal_amount,
        start_date=campaign_in.start_date,
        end_date=campaign_in.end_date,
        image_url=campaign_in.image_url,
        tenant_id=tenant.id
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign


@router.get("/", response_model=list[CampaignOut])
def list_campaigns(
        db: Session = Depends(get_db),
        active_only: Optional[bool] = None,
):
    query = db.query(Campaign).options(joinedload(Campaign.tenant))

    if active_only:
        now = datetime.now()
        query = query.filter(Campaign.start_date <= now, Campaign.end_date >= now)

    campaigns = query.order_by(Campaign.created_at.desc()).all()

    results = []
    for campaign in campaigns:
        # Get computed values
        percent = (campaign.current_amount / campaign.goal_amount) * 100 if campaign.goal_amount else 0
        days = (campaign.end_date - datetime.now()).days if campaign.end_date else 0
        donor_count = db.query(Donation.donor_email).filter(Donation.campaign_id == campaign.id).distinct().count()

        # Serialize model
        campaign_dict = campaign.__dict__.copy()
        campaign_dict["percent_funded"] = round(percent, 2)
        campaign_dict["days_left"] = days
        campaign_dict["total_donors"] = donor_count

        results.append(campaign_dict)

    return results


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id)
        .options(joinedload(Campaign.tenant))  # Eager load the tenant
        .first()
    )

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Calculate extra stats
    percent = (campaign.current_amount / campaign.goal_amount) * 100 if campaign.goal_amount else 0
    days = (campaign.end_date - datetime.now()).days if campaign.end_date else 0
    donor_count = db.query(Donation.donor_email)\
        .filter(Donation.campaign_id == campaign.id).distinct().count()

    # Convert base fields
    campaign_dict = campaign.__dict__.copy()

    # Serialize tenant manually
    campaign_dict["tenant"] = {
        "id": campaign.tenant.id,
        "name": campaign.tenant.name,
        # "website": campaign.tenant.website,
    } if campaign.tenant else None

    # Add computed fields
    campaign_dict["percent_funded"] = round(percent, 2)
    campaign_dict["days_left"] = max(days, 0)
    campaign_dict["total_donors"] = donor_count

    return CampaignOut(**campaign_dict)

@router.put("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
    campaign_id: UUID,
    update: CampaignUpdate,
    db: Session = Depends(get_db),
    user = Depends(require_tenant_admin)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Ensure this campaign belongs to current tenant admin
    tenant = db.query(Tenant).filter(Tenant.admin_id == user.id).first()
    if campaign.tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="You can only edit your own campaign")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)
    return campaign


# CAMPAIGN STATS
@router.get("/{campaign_id}/stats", response_model=CampaignStats)
def get_campaign_stats(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    goal = float(campaign.goal_amount)
    raised = float(campaign.current_amount)

    #avoid divide by zero
    percent_funded = (raised/ goal )* 100 if goal > 0 else 0.0
    amount_remaining = campaign.goal_amount - campaign.current_amount

    # Days left
    if campaign.end_date:
        now = datetime.now()
        delta = campaign.end_date - now
        days_left = max(0, delta.days)
        is_active = campaign.start_date <= now <= campaign.end_date
    else:
        days_left = None
        is_active = True

    return CampaignStats(
        percent_funded=round(percent_funded,2),
        amount_remaining=amount_remaining,
        days_left=days_left,
        is_active=is_active
    )