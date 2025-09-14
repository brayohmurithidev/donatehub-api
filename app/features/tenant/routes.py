from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.index import get_db
from app.features.tenant.schemas import TenantListOut
from app.features.tenant.services import get_all_tenants

router = APIRouter()


@router.get('/')
def get_tenants(
        db: Session = Depends(get_db),
        verified: Optional[bool] = Query(None, description="Filter by verified status"),
        search: Optional[str] = Query(None, description="Filter by tenant name"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=200, description="Number of results per page")
):
    tenants = get_all_tenants(db)

    if not tenants:
        raise HTTPException(status_code=404, detail="No tenants found")

    results = []
    for tenant, total_campaigns, total_raised in tenants:
        results.append(
            TenantListOut(
                id=tenant.id,
                name=tenant.name,
                logo_url=tenant.logo_url,
                description=tenant.description,
                short_description=tenant.description[:100] + "..." if tenant.description else None,
                email=tenant.email,
                phone=tenant.phone,
                website=tenant.website,
                location=tenant.location,
                total_campaigns=total_campaigns,
                total_raised=round(total_raised, 2),  # round to 2 decimal places
                is_verified=tenant.is_Verified,
                date_joined=tenant.created_at,
            ))
    return results
