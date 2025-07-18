from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr



class UserRole(str, Enum):
    donor = "donor"
    tenant_admin = "tenant_admin"
    platform_admin = "platform_admin"

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.donor

class UserOut(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True #allows pydantic to read the data from the ORM model