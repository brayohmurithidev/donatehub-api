from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TenantOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    is_Verified: bool
    website: Optional[str] = None

    total_campaigns: int = 0
    active_campaigns: int = 0
    total_raised: float = 0.0
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


