from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.index import get_db
from app.features.campaign.services import fetch_campaigns

router = APIRouter()


@router.get("/")
def get_campaigns(db: Session = Depends(get_db)):
    campaigns = fetch_campaigns(db=db)

    if not campaigns:
        raise HTTPException(status_code=404, detail="No campaigns found")

    return campaigns
