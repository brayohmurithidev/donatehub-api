from enum import Enum

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

class PaymentMethod(str, Enum):
    MPESA = "MPESA"
    CARD = "CARD"
    PAYPAL = "PAYPAL"
    BANK = "BANK"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class CampaignInDonation(BaseModel):
    id: UUID
    title: str
    goal_amount: Decimal
    start_date: datetime
    end_date: datetime
    image_url: Optional[str] = None

class DonationBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    donor_name: Optional[str] = None
    donor_phone: Optional[str] = None
    donor_email: Optional[EmailStr] = None
    message: Optional[str] = None
    method: Optional[PaymentMethod] = None
    is_anonymous: bool = False

class CreateDonation(DonationBase):
    tenant_id: UUID
    campaign_id:UUID




class DonationOut(DonationBase):
    id: UUID
    tenant_id: UUID
    donor_id: Optional[UUID] = None
    campaign_id: UUID
    status: PaymentStatus
    transaction_id: Optional[str] = None
    callback_data: Optional[dict] = None
    amount: Decimal
    donor_name: Optional[str]
    donor_phone: Optional[str]
    donor_email: Optional[EmailStr]
    message: Optional[str]
    donated_at: datetime
    campaign: CampaignInDonation


    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v) #to make it json serializable
        }