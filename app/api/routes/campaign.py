import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_tenant_admin
from app.db.index import get_db
from app.features.campaign.models import Campaign
from app.lib.helper_fns import serialize_campaign
from app.lib.upload import upload_image
from app.schemas.campaign import CampaignOut, CampaignUpdate, CampaignStats, CampaignStatus

router = APIRouter()


@router.post('/', response_model=CampaignOut)
def create_campaign(
        title: str = Form(...),
        description: str = Form(...),
        status: Optional[CampaignStatus] = Form(CampaignStatus.active),
        goal_amount: Decimal = Form(...),
        start_date: datetime = Form(...),
        end_date: Optional[datetime] = Form(None),
        image: UploadFile = File(...),
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    if image is None:
        raise HTTPException(status_code=400, detail="Campaign Image file is required")

    # get tenant of this user
    user, tenant = auth
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this user")

    # CHECK IF CAMPAIGN TITLE EXISTS
    existingCampaign = db.query(Campaign).filter(Campaign.title == title).first()
    if existingCampaign:
        raise HTTPException(status_code=400, detail="Campaign with this title already exists")

    campaign_id = uuid.uuid4()

    image_url = upload_image(image, "campaigns", public_id=campaign_id)

    new_campaign = Campaign(
        id=campaign_id,
        title=title,
        description=description,
        goal_amount=goal_amount,
        start_date=start_date,
        status=status,
        end_date=end_date,
        image_url=image_url,
        tenant_id=tenant.id
    )

    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return serialize_campaign(new_campaign, db)


@router.get("/", response_model=list[CampaignOut])
def list_campaigns(
        db: Session = Depends(get_db),
        active_only: Optional[bool] = True,
        tenant_id: Optional[UUID] = None,  # 🔹 Accept tenant_id as a filter
):
    query = db.query(Campaign).options(joinedload(Campaign.tenant))

    if active_only:
        now = datetime.now()
        query = query.filter(Campaign.start_date <= now, Campaign.end_date >= now)

    if tenant_id:
        query = query.filter(Campaign.tenant_id == tenant_id)

    campaigns = query.order_by(Campaign.created_at.desc()).all()

    results = []
    for campaign in campaigns:
        results.append(serialize_campaign(campaign, db))

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

    return serialize_campaign(campaign, db)


@router.put("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
        campaign_id: UUID,
        update: CampaignUpdate,
        db: Session = Depends(get_db),
        adminRes=Depends(require_tenant_admin)
):
    print("update: ", update)
    user, tenant = adminRes
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="You can only edit your own campaign")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)

    db.commit()
    db.refresh(campaign)
    return serialize_campaign(campaign, db)


# CAMPAIGN STATS
@router.get("/{campaign_id}/stats", response_model=CampaignStats)
def get_campaign_stats(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    goal = float(campaign.goal_amount)
    raised = float(campaign.current_amount)

    # avoid divide by zero
    percent_funded = (raised / goal) * 100 if goal > 0 else 0.0
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
        percent_funded=round(percent_funded, 2),
        amount_remaining=amount_remaining,
        days_left=days_left,
        is_active=is_active
    )
