import stripe
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db.index import get_db
from app.features.campaign.models import Campaign
from app.schemas.checkout import CheckoutRequest

router = APIRouter()
stripe.api_key = settings.stripe_secret_key


@router.post("/checkout")
def create_checkout_session(data: CheckoutRequest, db: Session = Depends(get_db)):
    # Fetch campaign title
    campaign = db.query(Campaign).filter(Campaign.id == data.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            # customer_email=data.donor_email or None,
            # consent_collection={
            #     "terms_of_service": "required"
            # },
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(data.amount * 100),  # in cents
                    'product_data': {
                        'name': f'Donation to: {campaign.title}'
                    },
                },
                'quantity': 1
            }
            ],
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
