from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.features.auth.models import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.donor


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
