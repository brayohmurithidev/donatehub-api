from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

class DonationCreate(BaseModel):
    amount: Decimal
    donor_name: Optional[str] = None
    donor_email: Optional[EmailStr] = None
    message: Optional[str] = None
    campaign_id: UUID

class DonationOut(BaseModel):
    id: UUID
    amount: Decimal
    donor_name: Optional[str]
    message: Optional[str]
    donated_at: datetime
    campaign_id: UUID

    class Config:
        from_attributes = True