from fastapi import APIRouter

from app.features.campaign import routes as campaign

router = APIRouter()

router.include_router(router=campaign.router, prefix="/campaigns", tags=["Campaigns V2"])
