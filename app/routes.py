from fastapi import APIRouter

from app.features.auth import routes as auth
from app.features.campaign import routes as campaign
from app.features.donation import routes as donation
from app.features.payments.stripe import routes as stripe
from app.features.payments.mpesa import routes as mpesa
from app.features.stats import routes as stats
from app.features.uploads import routes as uploads
from app.features.admin import routes as admin
from app.features.tenant import routes as tenant

router = APIRouter()

router.include_router(router=campaign.router, prefix="/campaigns", tags=["Campaigns V2"])
router.include_router(router=auth.router, prefix="/auth", tags=["Auth V2"])
router.include_router(router=tenant.router, prefix="/tenants", tags=["Tenants V2"])
router.include_router(router=donation.router, prefix="/donations", tags=["Donations V2"])
router.include_router(router=stripe.router, prefix="/stripe", tags=["Stripe V2"])
router.include_router(router=mpesa.router, prefix="/mpesa", tags=["Mpesa V2"])
router.include_router(router=stats.router, prefix="/stats", tags=["Stats V2"])
router.include_router(router=uploads.router, prefix="/uploads", tags=["Uploads V2"])
router.include_router(router=admin.router, prefix="/admin", tags=["Admin V2"])
