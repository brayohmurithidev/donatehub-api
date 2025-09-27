from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from fastapi import UploadFile, File
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.features.auth.models import UserRole
from app.features.tenant.models import Tenant


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
    is_email_verified: Optional[bool] = False
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
    is_email_verified: bool
    date_joined: datetime

    class Config:
        from_attributes = True


def get_tenant_by_id(db: Session, tenant_id: UUID) -> TenantListOut:
    """
    Get a single tenant by its ID.

    Args:
        db (Session): Database session.
        tenant_id (UUID): The ID of the tenant to retrieve.

    Returns:
        TenantListOut: Tenant details if found.

    Raises:
        HTTPException: If no tenant is found with the given ID.
    """
    tenant = db.query(
        Tenant.id,
        Tenant.name,
        Tenant.logo_url,
        Tenant.description,
        Tenant.short_description,
        Tenant.email,
        Tenant.phone,
        Tenant.website,
        Tenant.location,
        Tenant.total_campaigns,
        Tenant.total_raised,
        Tenant.is_verified,
        Tenant.date_joined
    ).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found."
        )

    return TenantListOut.from_orm(tenant)
