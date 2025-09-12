from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.index import get_db
from app.db.models import Donation
from app.features.campaign.models import Campaign

router = APIRouter()
stripe.api_key = settings.stripe_secret_key


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session1 = event["data"]["object"]

        metadata = session1.get("metadata", {})
        campaign_id = metadata.get("campaign_id")
        amount_total = session1.get("amount_total", 0)

        donor_email = metadata.get("donor_email") or session1.get("customer_email")
        donor_name = metadata.get("donor_name") or session1.get("customer_details", {}).get("name")
        message = metadata.get("message", "")

        if not campaign_id:
            raise HTTPException(status_code=400, detail="Missing campaign_id in metadata")

        # Save donation
        campaign = db.query(Campaign).filter(Campaign.id == metadata["campaign_id"]).first()
        if campaign:
            campaign.current_amount += amount_total / 100
            db.add(campaign)
            donation = Donation(
                amount=amount_total / 100,
                donor_name=donor_name or "Anonymous",
                donor_email=donor_email or None,
                message=message,
                campaign_id=campaign.id,
                donated_at=datetime.now()
            )
            db.add(donation)
            db.commit()
    return {"status": "ok"}
