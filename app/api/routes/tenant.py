from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.api.deps import require_tenant_admin
from app.core.security import hash_password
from app.db.index import get_db
from app.features.auth.models import User
from app.features.campaign.models import CampaignStatus, Campaign
from app.features.tenant.models import Tenant
from app.schemas.campaign import CampaignOut
from app.schemas.tenant import TenantOut, TenantCreate, TenantUpdate, TenantListOut

router = APIRouter()


@router.post("/", response_model=TenantOut)
def create_tenant(
        tenant_in: TenantCreate,
        db: Session = Depends(get_db)
):
    tenant_exists = db.query(Tenant).filter(Tenant.email == tenant_in.email,
                                            Tenant.website == tenant_in.website).first()
    user_exists = db.query(User).filter(User.email == tenant_in.email).first()

    if tenant_exists or user_exists:
        raise HTTPException(status_code=400,
                            detail="This organization is already registered. Please login to continue.")
    try:
        new_user = User(
            full_name=tenant_in.admin.full_name,
            email=tenant_in.admin.email,
            password=hash_password(tenant_in.admin.password),
            role="tenant_admin"
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        new_tenant = Tenant(
            name=tenant_in.name,
            description=tenant_in.description,
            logo_url=tenant_in.logo_url,
            phone=tenant_in.phone,
            email=tenant_in.email,
            location=tenant_in.location,
            is_Verified=False,
            website=tenant_in.website,
            admin_id=new_user.id
        )

        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)

        return new_tenant
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin gets their tenant record
@router.get("/me", response_model=TenantOut)
def get_my_tenant(
        db: Session = Depends(get_db),
        adminResponse=Depends(require_tenant_admin)
):
    user, tenant = adminResponse
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this auth")
    return tenant


# Get single tenant
@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.get("/{tenant_id}/campaigns", response_model=List[CampaignOut])
def get_tenant_campaigns(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_campaigns = db.query(Campaign).filter(
        and_(
            Campaign.tenant_id == tenant_id,
            Campaign.status == CampaignStatus.active
        )
    ).all()
    return tenant_campaigns


@router.get("/", response_model=List[TenantListOut])
def list_tenants(
        db: Session = Depends(get_db),
        verified: Optional[bool] = Query(None, description="Filter by verified status"),
        search: Optional[str] = Query(None, description="Search by tenant name"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Page size"),
):
    query = (
        db.query(
            Tenant,
            func.count(Campaign.id).label("totalCampaigns"),
            func.coalesce(func.sum(Campaign.current_amount), 0).label("totalRaised"),
        )
        .outerjoin(Campaign, Campaign.tenant_id == Tenant.id)
        .group_by(Tenant.id)
    )

    # Default filter: only verified unless explicitly overridden
    if verified is None:
        query = query.filter(Tenant.is_Verified == True)
    else:
        query = query.filter(Tenant.is_Verified == verified)

    if search:
        query = query.filter(Tenant.name.ilike(f"%{search}%"))

    # Pagination
    tenants = query.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for tenant, total_campaigns, total_raised in tenants:
        results.append(
            TenantListOut(
                id=tenant.id,
                name=tenant.name,
                logo_url=tenant.logo_url,
                description=tenant.description,
                shortDescription=tenant.description[:100] + "..." if tenant.description else None,
                email=tenant.email,
                phone=tenant.phone,
                website=tenant.website,
                location=tenant.location,
                totalCampaigns=total_campaigns,
                totalRaised=round(total_raised, 2),  # round to 2 decimal places
                isVerified=tenant.is_Verified,
                dateJoined=tenant.created_at,
            )
        )

    return results


# Update tenant details
@router.put("/{tenant_id}", response_model=TenantOut)
def update_tenant(
        tenant_id: str,
        update: TenantUpdate,
        db: Session = Depends(get_db),
        adminRes=Depends(require_tenant_admin)
):
    user, tenant = adminRes
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Allow update only if current auth is the tenant admin
    if tenant.admin_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this tenant")

    for key, value in update.model_dump(exclude_unset=True).items():
        print(key, value)
        setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)
    return tenant
