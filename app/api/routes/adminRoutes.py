from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.db.index import get_db
from app.features.auth.models import User
from app.features.campaign.models import Campaign, CampaignStatus
from app.features.tenant.models import Tenant
from app.schemas.adminSchemas import TenantOut

router = APIRouter()


# Get tenants (list)
@router.get("/tenants", response_model=list[TenantOut])
def get_tenants(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_platform_admin),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
):
    # subquery aggregates per tenant
    subq = (
        select(
            Campaign.tenant_id.label("tenant_id"),
            # use distinct in count to avoid duplication if joins elsewhere produce duplicates
            func.count(func.distinct(Campaign.id)).label("total_campaigns"),
            func.coalesce(func.sum(Campaign.current_amount), 0).label("total_raised"),
            # count active campaigns
            func.coalesce(
                func.sum(case((Campaign.status == CampaignStatus.active, 1), else_=0)),
                0,
            ).label("active_campaigns"),
        )
        .group_by(Campaign.tenant_id)
        .subquery()
    )

    stmt = (
        select(
            Tenant,
            func.coalesce(subq.c.total_campaigns, 0).label("total_campaigns"),
            func.coalesce(subq.c.total_raised, 0).label("total_raised"),
            func.coalesce(subq.c.active_campaigns, 0).label("active_campaigns"),
        )
        .outerjoin(subq, Tenant.id == subq.c.tenant_id)
        .offset(skip)
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    result = []
    for tenant_obj, total_campaigns, total_raised, active_campaigns in rows:
        total_raised_float = float(total_raised) if total_raised is not None else 0.0

        # Pull contact/admin info (if present)
        contact_name = None
        contact_email = None
        if tenant_obj.admin_id:
            admin_user = db.query(User).filter(User.id == tenant_obj.admin_id).first()
            if admin_user:
                contact_name = getattr(admin_user, "full_name", None)
                contact_email = getattr(admin_user, "email", None)

        result.append(
            {
                "id": tenant_obj.id,
                "name": tenant_obj.name,
                "description": tenant_obj.description,
                "logo_url": tenant_obj.logo_url,
                "phone": tenant_obj.phone,
                "email": tenant_obj.email,
                "location": tenant_obj.location,
                "is_Verified": bool(tenant_obj.is_Verified),
                "website": tenant_obj.website,
                "total_campaigns": int(total_campaigns or 0),
                "active_campaigns": int(active_campaigns or 0),
                "total_raised": total_raised_float,
                "contact_person_name": contact_name,
                "contact_person_email": contact_email,
                "created_at": tenant_obj.created_at,
                "updated_at": tenant_obj.updated_at,
            }
        )

    return result


# Get single tenant by id (includes same aggregates + contact info)
@router.get("/tenants/{tenant_id}", response_model=TenantOut)
def get_tenant(
        tenant_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_platform_admin),
):
    subq = (
        select(
            Campaign.tenant_id.label("tenant_id"),
            func.count(func.distinct(Campaign.id)).label("total_campaigns"),
            func.coalesce(func.sum(Campaign.current_amount), 0).label("total_raised"),
            func.coalesce(
                func.sum(case((Campaign.status == CampaignStatus.active, 1), else_=0)),
                0,
            ).label("active_campaigns"),
        )
        .group_by(Campaign.tenant_id)
        .subquery()
    )

    stmt = (
        select(
            Tenant,
            func.coalesce(subq.c.total_campaigns, 0).label("total_campaigns"),
            func.coalesce(subq.c.total_raised, 0).label("total_raised"),
            func.coalesce(subq.c.active_campaigns, 0).label("active_campaigns"),
        )
        .outerjoin(subq, Tenant.id == subq.c.tenant_id)
        .where(Tenant.id == tenant_id)
    )

    row = db.execute(stmt).first()

    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant_obj, total_campaigns, total_raised, active_campaigns = row
    total_raised_float = float(total_raised) if total_raised is not None else 0.0

    # Pull contact/admin info (if present)
    contact_name = None
    contact_email = None
    if tenant_obj.admin_id:
        admin_user = db.query(User).filter(User.id == tenant_obj.admin_id).first()
        if admin_user:
            contact_name = getattr(admin_user, "full_name", None)
            contact_email = getattr(admin_user, "email", None)

    result = {
        "id": tenant_obj.id,
        "name": tenant_obj.name,
        "description": tenant_obj.description,
        "logo_url": tenant_obj.logo_url,
        "phone": tenant_obj.phone,
        "email": tenant_obj.email,
        "location": tenant_obj.location,
        "is_Verified": bool(tenant_obj.is_Verified),
        "website": tenant_obj.website,
        "total_campaigns": int(total_campaigns or 0),
        "active_campaigns": int(active_campaigns or 0),
        "total_raised": total_raised_float,
        "contact_person_name": contact_name,
        "contact_person_email": contact_email,
        "created_at": tenant_obj.created_at,
        "updated_at": tenant_obj.updated_at,
    }

    return result

# Get tenant by id

# Get Tenant campaigns

# Get Campaign by ID


# Verify NGO
