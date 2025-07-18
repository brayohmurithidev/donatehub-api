from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


# Tenant in a campaign
class TenantInCampaign(BaseModel):
    id: UUID
    name: str
    website: Optional[HttpUrl]  =None



class CampaignCreate(BaseModel):
    title: str
    description: str
    goal_amount: Decimal
    start_date: datetime
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goal_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None


class CampaignOut(BaseModel):
    id: UUID
    title: str
    description: str
    goal_amount: Decimal
    current_amount: Decimal
    start_date: datetime
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None
    tenant_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    tenant: Optional[TenantInCampaign]

    percent_funded: float
    days_left: int
    total_donors: int

    class Config:
        from_attributes = True



# stats
class CampaignStats(BaseModel):
    percent_funded: float
    amount_remaining: Decimal
    days_left: Optional[int]
    is_active: bool