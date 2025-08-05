from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.user import UserCreate


class UserInTenant(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr


class TenantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    is_Verified: Optional[bool] = False
    website: Optional[str] = None
    admin: UserCreate


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None


class TenantOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    campaignCount: Optional[int] = 0
    website: Optional[str] = None
    is_Verified: bool
    admin: Optional[UserInTenant] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
