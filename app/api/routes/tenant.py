from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_tenant_admin
from app.db.index import get_db
from app.schemas.tenant import TenantOut, TenantCreate, TenantUpdate
from app.db.models.tenant import Tenant
from typing import List, Optional

router = APIRouter()


@router.post("/", response_model=TenantOut)
def create_tenant(
        tenant_in: TenantCreate,
        db: Session = Depends(get_db),
        user = Depends(require_tenant_admin)
):
    # Check if user already owns a tenant
    existing = db.query(Tenant).filter(Tenant.admin_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already manage a tenant")

    new_tenant = Tenant(
        name=tenant_in.name,
        description=tenant_in.description,
        logo_url=tenant_in.logo_url,
        phone=tenant_in.phone,
        email=tenant_in.email,
        location=tenant_in.location,
        is_Verified=False,
        admin_id=user.id
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return new_tenant

# Admin gets their tenant record
@router.get("/me", response_model=TenantOut)
def get_my_tenant(
    db: Session = Depends(get_db),
    user = Depends(require_tenant_admin)
):
    tenant = db.query(Tenant).filter(Tenant.admin_id == user.id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this user")
    return tenant

# Get single tenant
@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.get("/", response_model=List[TenantOut])
def list_tenants(
        verified: Optional[bool] = Query(None, description="Filter by verified status"),
        db: Session = Depends(get_db),
):
    query = db.query(Tenant)
    if verified is not None:
        query = query.filter(Tenant.is_Verified == verified)
    return query.all()



# Update tenant details
@router.put("/{tenant_id}", response_model=TenantOut)
def update_tenant(
        tenant_id: str,
        update: TenantUpdate,
        db: Session = Depends(get_db),
        user =  Depends(require_tenant_admin)
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    #Allow update only if current user is the tenant admin
    if tenant.admin_id != user.id:
        raise HTTPException(status_code=403, detail="You are not authorized to update this tenant")

    for key, value in update.model_dump(exclude_unset=True).items():
        print(key, value)
        setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)
    return tenant



