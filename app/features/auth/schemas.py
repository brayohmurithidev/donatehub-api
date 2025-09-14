from pydantic import BaseModel, EmailStr

from app.features.auth.models import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.donor


class TokenRefreshRequest(BaseModel):
    refresh_token: str
