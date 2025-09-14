from fastapi import APIRouter

from app.features.auth import routes as auth
from app.features.campaign import routes as campaign
from app.features.tenant import routes as tenant

router = APIRouter()

router.include_router(router=campaign.router, prefix="/campaigns", tags=["Campaigns V2"])
router.include_router(router=auth.router, prefix="/auth", tags=["Auth V2"])
router.include_router(router=tenant.router, prefix="/tenants", tags=["Tenants V2"])
