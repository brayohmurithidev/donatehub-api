from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, and_, Float, cast
from sqlalchemy.orm import Session

from app.api.deps import require_tenant_admin
from app.db.index import get_db
from app.db.models import Campaign, Donation
from app.schemas.donation import PaymentStatus

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_stats(
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this user")

    # GET TOTAL CAMPAIGNS
    total_campaigns = db.query(func.count(Campaign.id)).filter(Campaign.tenant_id == tenant.id).scalar()

    # Amount contributed
    total_amount_contributed = db.query(func.sum(Donation.amount)).filter(
        and_(Donation.tenant_id == tenant.id, Donation.status == PaymentStatus.SUCCESS)).scalar()

    # TOTAL CURRENT AMOUNT
    total_current = db.query(func.sum(Campaign.current_amount)).filter(Campaign.tenant_id == tenant.id).scalar()
    total_goal_amount = db.query(func.sum(Campaign.goal_amount)).filter(Campaign.tenant_id == tenant.id).scalar()

    success_rate = (total_current / total_goal_amount) * 100 if total_goal_amount > 0 else 0.0
    success_rate_expr = (
            (cast(Campaign.current_amount, Float) / cast(Campaign.goal_amount, Float)) * 100
    )

    total_donors = db.query(func.count(Donation.id)).filter(Donation.tenant_id == tenant.id).scalar()

    recent_donors = (db.query(
        Donation.id,
        Donation.donor_name,
        Donation.amount,
        Donation.method,
        Campaign.title.label("campaign_name")
    )
                     .filter(and_(
        Donation.tenant_id == tenant.id,
        Donation.status == PaymentStatus.SUCCESS
    )).order_by(Donation.donated_at.asc())
                     .limit(5).all())
    recent_donors = [
        {
            "id": row.id,
            "donor_name": row.donor_name if row.donor_name else "Anonymous",
            "amount": row.amount,
            "paymentMethod": row.method,
            "campaign_name": row.campaign_name
        } for row in recent_donors
    ]
    top_performing_campaigns = (
        db.query(
            Campaign.id,
            Campaign.title,
            Campaign.current_amount,
            success_rate_expr.label("success_rate")
        )
        .filter(
            and_(
                Campaign.tenant_id == tenant.id,
                Campaign.status == "active",
                Campaign.goal_amount.isnot(None),
                Campaign.goal_amount > 0
            )
        )
        .order_by(
            (cast(Campaign.current_amount, Float) / Campaign.goal_amount).desc()
        )
        .limit(5)
        .all()
    )

    # Convert Row objects to dicts
    top_performing_campaigns = [
        {
            "id": row.id,
            "title": row.title,
            "amount": row.current_amount,
            "success_rate": float(row.success_rate) if row.success_rate else 0.0
        }
        for row in top_performing_campaigns
    ]
    return {"total_campaigns": total_campaigns, "total_amount_contributed": total_amount_contributed,
            "overall_success_rate": success_rate,
            "top_performing_campaigns": top_performing_campaigns, "recent_donors": recent_donors,
            "total_donors": total_donors, }
