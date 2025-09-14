# Get tenants
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.campaign.models import Campaign
from app.features.tenant.models import Tenant


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
    return query.offset((page - 1) * limit).limit(limit).all()

# Get tenant by id

# Get tenant by name
