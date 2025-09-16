import stripe
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db.index import get_db
from app.features.campaign.models import Campaign
from app.features.donation.models import Donation
from app.features.payments.stripe.schemas import CheckoutRequest

router = APIRouter()
stripe.api_key = settings.stripe_secret_key


@router.get("/session")
def get_checkout_session(session_id: str = Query(..., alias="session_id")):
    try:
        session = stripe.checkout.Session.retrieve(session_id)

        return {
            "amount_total": session["amount_total"],
            "currency": session["currency"],
            "customer_email": session.get("customer_email"),
            "metadata": session.get("metadata", {}),
        }
    except stripe.error.InvalidRequestError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching session details")


@router.post("/checkout")
def create_checkout_session(data: CheckoutRequest, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == data.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(data.amount * 100),
                    'product_data': {
                        'name': f'Donation to: {campaign.title}'
                    },
                },
                'quantity': 1
            }],
            metadata={
                "campaign_id": str(data.campaign_id),
                "campaign_title": campaign.title,
                "donor_name": data.donor_name,
                "donor_email": data.donor_email,
                "message": data.message or ""
            },
            success_url="http://localhost:3000/thank-you?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:3000/cancel"
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


