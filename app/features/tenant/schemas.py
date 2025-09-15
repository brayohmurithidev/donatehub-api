from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl

from app.features.auth.models import UserRole


class TenantAdmin(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.tenant_admin


class TenantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    is_Verified: Optional[bool] = False
    website: Optional[str] = None
    admin: TenantAdmin


class TenantListOut(BaseModel):
    id: UUID
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    location: Optional[str] = None
    total_campaigns: int
    total_raised: Decimal
    is_verified: bool
    date_joined: datetime

    class Config:
        from_attributes = True
