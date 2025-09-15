from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.common.handle_error import handle_error
from app.common.utils.map_tenant_to_response_model import map_tenant_to_response_model
from app.db.index import get_db
from app.features.tenant.schemas import TenantCreate
from app.features.tenant.services import get_all_tenants, get_tenant_by_id, create_new_tenant
from app.logger import logger

router = APIRouter()

"""
Public routes:
1. Get all tenants
2. Get tenant by ID
3. Register tenant
4. Verify tenant
5. Unverify tenant
6. Get tenant contact info
7. Update tenant contact info
8. Get tenant logo
9. Update tenant logo
10. Get tenant description
11. Update tenant description
12. Get tenant location
"""


@router.get('/')
def get_tenants(
        db: Session = Depends(get_db),
        verified: Optional[bool] = Query(None, description="Filter by verified status"),
        search: Optional[str] = Query(None, description="Filter by tenant name"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(10, ge=1, le=200, description="Number of results per page")
):
    tenants, total_count = get_all_tenants(db, verified, search, page, limit)

    if not tenants:
        raise HTTPException(status_code=404, detail="No tenants found")

    results = [
        map_tenant_to_response_model(tenant, total_campaigns, total_raised) for tenant, total_campaigns, total_raised in
        tenants
    ]
    logger.info("Fetched tenants")
    return {
        "tenants": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total_count,
            "pages": (total_count // limit) + (1 if total_count % limit > 0 else 0)
        }
    }


@router.get("/{tenant_id}")
def get_tenant(
        tenant_id: UUID,
        db: Session = Depends(get_db)
):
    result = get_tenant_by_id(db, tenant_id=tenant_id)
    if not result:
        handle_error(404, "Tenant not found")
    tenant, total_campaigns, total_raised = result
    return map_tenant_to_response_model(tenant, total_campaigns, total_raised)


# REGISTER NEW TENANT
@router.post("/")
def creat_tenant(
        payload: TenantCreate,
        db: Session = Depends(get_db)
):
    req_body = payload.model_dump()
    new_tenant = create_new_tenant(db, req_body)
    return map_tenant_to_response_model(new_tenant, 0, 0)
