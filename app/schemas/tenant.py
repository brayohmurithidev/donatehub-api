from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr


class TenantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    is_Verified: Optional[bool] = False


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
    is_Verified: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True