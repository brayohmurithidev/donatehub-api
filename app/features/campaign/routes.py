import uuid
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.common.deps import require_tenant_admin
from app.common.handle_error import handle_error
from app.common.upload import upload_image
from app.common.utils.serialize_campaign import serialize_campaign
from app.db.index import get_db
from app.features.campaign.schemas import CampaignOut, CampaignCreate, CampaignUpdate
from app.features.campaign.services import fetch_campaigns, fetch_campaign, fetch_campaign_by_title, \
    create_new_campaign, update_campaign_data

router = APIRouter()

"""
Public routes:
1. Get Campaigns
2. Get Campaign By ID
"""


@router.get("/", response_model=List[CampaignOut])
def get_campaigns(db: Session = Depends(get_db)):
    campaigns = fetch_campaigns(db=db)

    if not campaigns:
        handle_error(404, "No campaigns found")

    return [serialize_campaign(campaign, db) for campaign in campaigns]


# Get Campaign By ID
@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = fetch_campaign(db, campaign_id)

    if not campaign:
        handle_error(404, "Campaign not found")

    return serialize_campaign(campaign, db)


"""
Protected routes:
1. Create Campaign
2. Update Campaign
3. Delete Campaign - Soft delete
"""


@router.post("/", response_model=CampaignOut)
def create_campaign(
        body: CampaignCreate,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    image, *others = body
    if image is None:
        handle_error(400, "Campaign Image file is required")

    user, tenant = auth
    if not tenant:
        handle_error(404, "No tenant found for this user")

    campaign = fetch_campaign_by_title(db, body.title)
    if campaign:
        handle_error(400, "Campaign with this title already exists")

    campaign_id = uuid.uuid4()

    image_url = upload_image(image, "campaigns", public_id=campaign_id)

    new_campaign = create_new_campaign(db, {"image_url": image_url, **others})

    return {
        "message": "Campaign created successfully",
        "campaign": serialize_campaign(new_campaign, db)}


@router.put("/{campaign_id}", response_model=CampaignOut)
def update_campaign(
        campaign_id: UUID,
        body: CampaignUpdate,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    campaign = fetch_campaign(db, campaign_id)
    if not campaign:
        handle_error(404, "Campaign not found")

    if campaign.tenant_id != tenant.id:
        handle_error(403, "You can only edit your own campaign")

    updated_campaign = update_campaign_data(db, campaign_id, body.model_dump(exclude_unset=True))

    return serialize_campaign(updated_campaign, db)


# Update campaign image
@router.put("/{campaign_id}/image", response_model=dict)
def update_campaign_image(
        campaign_id: UUID,
        image: UploadFile = File(..., description="Campaign Image file"),
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    if image is None:
        handle_error(400, "Campaign Image file is required")
    user, tenant = auth
    campaign = fetch_campaign(db, campaign_id)
    if not campaign:
        handle_error(404, "Campaign not found")
    if campaign.tenant_id != tenant.id:
        handle_error(403, "You can only edit your own campaign")
    try:
        image_url = upload_image(image, "campaigns", public_id=campaign_id)
        campaign.image_url = image_url
        db.commit()
        db.refresh(campaign)
        return {"message": "Campaign image updated successfully", "campaign": serialize_campaign(campaign, db)}
    except Exception as e:
        db.rollback()
        handle_error(500, "Error updating campaign image", e)


@router.delete("/{campaign_id}", response_model=dict)
def delete_campaign(
        campaign_id: UUID,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    campaign = fetch_campaign(db, campaign_id)
    if not campaign:
        handle_error(404, "Campaign not found")

    if campaign.tenant_id != tenant.id:
        handle_error(403, "You can only delete your own campaign")

    db.delete(campaign)
    db.commit()
    return {"message": "Campaign deleted successfully"}
