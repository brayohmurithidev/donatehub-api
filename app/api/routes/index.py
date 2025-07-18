from fastapi import APIRouter

from app.api.routes import auth
from app.api.routes import tenant
from app.api.routes import campaign
from app.api.routes import donation
from app.api.routes import uploads
from app.api.routes import stripe_webhook
from app.api.routes import stripe_checkout
from app.api.routes import stripe_session

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=['Auth'])
router.include_router(tenant.router, prefix="/tenants", tags=['Tenants'])
router.include_router(campaign.router, prefix="/campaigns", tags=['Campaigns'])
router.include_router(donation.router, prefix="/donations", tags=['Donations'])
router.include_router(uploads.router, prefix="/uploads", tags=['Uploads'])
router.include_router(stripe_checkout.router, prefix="/donations", tags=['Donations'])
router.include_router(stripe_webhook.router, prefix="/stripe", tags=['Stripe'])
router.include_router(stripe_session.router, prefix="/stripe", tags=['Stripe'])
