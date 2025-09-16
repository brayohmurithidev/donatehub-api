# Get tenants
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.auth import hash_password
from app.common.handle_error import handle_error
from app.features.auth.models import User
from app.features.campaign.models import Campaign
from app.features.tenant.models import Tenant, TenantSupportDocuments


def get_all_tenants(db: Session, verified: bool = None, search: str = None, page: int = 1, limit: int = 10, ):
    query = (
        db.query(Tenant,
                 func.count(Campaign.id).label("total_campaigns"),
                 func.coalesce(func.sum(Campaign.current_amount), 0).label("total_raised"),
                 ).outerjoin(Campaign, Tenant.id == Campaign.tenant_id).group_by(Tenant.id)
    )
    if verified is not None:
        query = query.filter(Tenant.is_Verified == bool(verified))
    if search:
        query = query.filter(Tenant.name.ilike(f"%{search}%"))

    total_count = query.count()

    # Apply pagination
    offset_value = (page - 1) * limit
    query = query.offset(offset_value).limit(limit)
    tenants = query.all()
    return tenants, total_count


# Get tenant by id
def get_tenant_by_id(db: Session, tenant_id: UUID):
    return (
        db.query(Tenant,
                 func.count(Campaign.id).label("total_campaigns"),
                 func.coalesce(func.sum(Campaign.current_amount), 0).label("total_raised"),
                 ).outerjoin(Campaign, Tenant.id == Campaign.tenant_id).group_by(Tenant.id)
        .filter(Tenant.id == tenant_id).first()
    )


# Create tenant
def create_new_tenant(db: Session, data):
    admin = data.pop("admin")
    # Create admin
    if not admin:
        handle_error(400, "Organization contact person is required")

    try:
        password = admin.pop("password")
        hashed_pass = hash_password(password)
        admin['password'] = hashed_pass
        new_admin_user = User(**admin)
        db.add(new_admin_user)
        db.flush()  # pushes inserts to db without commiting

        # retrieve the admin ID
        data["admin_id"] = new_admin_user.id
        tenant = Tenant(**data)
        db.add(tenant)
        db.commit()
        db.refresh(new_admin_user)
        db.refresh(tenant)
        return tenant

    except IntegrityError as e:
        db.rollback()
        if "ix_user_email" in str(e.orig):
            handle_error(400, "AThis user is already linked with another Organization", e)

        else:
            handle_error(500, "An error occurred while creating the organization. Please try again later:", e)

    except Exception as e:
        # Rollback transaction
        db.rollback()
        handle_error(500, "Unexpected error occurred while creating the organization", e)


# Update Tenant
def update_tenant_data(db, tenant_id, data):
    try:

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        for key, value in data.items():
            setattr(db.query(Tenant).filter(Tenant.id == tenant_id).first(), key, value)
        db.commit()
        db.refresh(tenant)
        return tenant
    except Exception as e:
        db.rollback()
        handle_error(500, "Unexpected error occurred while updating the organization", e)


# GET tenants campaigns
def get_campaigns_by_tenant_id(db: Session, tenant_id: UUID, search, page, limit):
    query = db.query(Campaign).filter(Campaign.tenant_id == tenant_id).order_by(Campaign.created_at.desc())
    if search:
        query = query.filter(Campaign.title.ilike(f"%{search}%"))

    # pagination
    offset_value = (page - 1) * limit
    query = query.offset(offset_value).limit(limit)

    total_count = query.count()

    campaigns = query.all()

    return campaigns, total_count


# Get tenants documents
def get_documents_by_tenant_id(db: Session, tenant_id: UUID):
    documents = db.query(TenantSupportDocuments).filter(TenantSupportDocuments.tenant_id == tenant_id).all()
    return documents

# Get tenant by name
