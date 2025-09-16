from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import Form, UploadFile, File
from pydantic import BaseModel, HttpUrl


class CampaignStatus(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


# Tenant in a campaign
class TenantInCampaign(BaseModel):
    id: UUID
    name: str
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None


class CampaignCreate(BaseModel):
    title: str = Form(...)
    description: str = Form(...)
    status: Optional[CampaignStatus] = Form(CampaignStatus.active)
    goal_amount: Decimal = Form(...)
    start_date: datetime = Form(...)
    end_date: Optional[datetime] = Form(None)
    image: Optional[UploadFile] = File(None)


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    goal_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignOut(BaseModel):
    id: UUID
    title: str
    description: str
    status: CampaignStatus
    goal_amount: Decimal
    current_amount: Decimal
    start_date: datetime
    end_date: Optional[datetime] = None
    image_url: Optional[str] = None
    tenant_id: UUID
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    tenant: Optional[TenantInCampaign]

    percent_funded: Optional[float] = 0
    days_left: Optional[int] = 0
    total_donors: Optional[int] = 0

    class Config:
        from_attributes = True


# stats
class CampaignStats(BaseModel):
    percent_funded: float
    amount_remaining: Decimal
    days_left: Optional[int]
    is_active: bool
