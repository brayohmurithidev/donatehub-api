from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import UploadFile, File
from pydantic import BaseModel, EmailStr, Field

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


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    website: Optional[str] = Field(None, description="URL of the tenant's website")


class TenantSupportedDocuments(BaseModel):
    registration: Optional[UploadFile] = File(None, description="Certificate of registration")
    tax_certificate: Optional[UploadFile] = File(None, description="Tax certificate / Exemption Certificate")
    governance_document: Optional[UploadFile] = File(None, description="Board Resolution / Governance structure")
    id: Optional[UploadFile] = File(None, description="Director/ Trustee ID")
    bank: Optional[UploadFile] = File(None, description="Bank Verification Document")
    financial_report: Optional[UploadFile] = File(None, description="Audited Financial Statements")
    report: Optional[UploadFile] = File(None, description="Annual / Impact Report")


class TenantListOut(BaseModel):
    id: UUID
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    total_campaigns: int
    total_raised: Decimal
    is_verified: bool
    date_joined: datetime

    class Config:
        from_attributes = True
