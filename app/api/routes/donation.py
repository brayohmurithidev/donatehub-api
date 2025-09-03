from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.index import get_db
from app.db.models import Campaign
from app.db.models.donation import Donation
from app.schemas.donation import DonationOut, CreateDonation
from app.services.payment_service import process_payment

router = APIRouter()


@router.post("/", response_model=DonationOut)
async def make_donation(payload: CreateDonation, db: Session = Depends(get_db)):
    # 1. Ensure campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Prevent donation if campaign is over
    now = datetime.now()
    if campaign.end_date and campaign.end_date < now:
        raise HTTPException(status_code=400, detail="This campaign has ended.")

    # 3. Create donation
    donation = Donation(
        tenant_id=payload.tenant_id,
        campaign_id=payload.campaign_id,
        amount=payload.amount,
        donor_name=payload.donor_name,
        donor_phone=payload.donor_phone,
        donor_email=payload.donor_email,
        message=payload.message,
        method=payload.method,
        is_anonymous=payload.is_anonymous,
    )

    # # 4. Update campaign amount - add after payment verification
    # campaign.current_amount += donation.amount

    db.add(donation)
    db.commit()
    db.refresh(donation)
    return donation

    # try:
    #     result = await process_payment(donation, db)
    #     return {"status": "initiated", "payment_data": result, "donation": donation}
    # except Exception as e:
    #     donation.status = "FAILED"
    #     db.commit()
    #     raise HTTPException(status_code=500, detail=f"Payment failed: {str(e)}")


@router.post("/one-click")
async def make_donation(payload: CreateDonation, db: Session = Depends(get_db)):
    # 1. Ensure campaign exists
    campaign = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # 2. Prevent donation if campaign is over
    now = datetime.now()
    if campaign.end_date and campaign.end_date < now:
        raise HTTPException(status_code=400, detail="This campaign has ended.")

    # 3. Create donation
    donation = Donation(
        tenant_id=payload.tenant_id,
        campaign_id=payload.campaign_id,
        amount=payload.amount,
        donor_name=payload.donor_name,
        donor_phone=payload.donor_phone,
        donor_email=payload.donor_email,
        message=payload.message,
        method=payload.method,
        is_anonymous=payload.is_anonymous,
        status="PENDING"  # Set initial status
    )

    db.add(donation)
    db.commit()
    db.refresh(donation)

    # 4. Handle payment based on method
    try:
        if payload.method == "MPESA":
            # Validate MPESA requirements
            if donation.tenant_id is None:
                raise HTTPException(status_code=400, detail="Tenant ID is required")

            integrations = donation.tenant.mpesa_integrations
            active_integration = next((integration for integration in integrations if integration.is_active), None)
            if active_integration is None:
                raise HTTPException(status_code=400, detail="No active MPESA integration found")

            # Process MPESA payment
            payment_result = await process_payment(donation, db)

            # Update donation status
            donation.status = "PENDING"
            donation.payment_reference = payment_result.get("reference")
            db.commit()

            return {
                "donation_id": str(donation.id),
                "donation": donation,
                "payment_status": "initiated",
                "payment_data": payment_result,
                "message": "MPESA payment initiated successfully"
            }

        elif payload.method == "CARD":
            # For card payments, return donation with payment intent
            # The frontend will handle Stripe payment separately
            return {
                "donation_id": str(donation.id),
                "donation": donation,
                "payment_status": "pending",
                "message": "Donation created. Please complete card payment.",
                "requires_stripe_payment": True
            }

        else:
            raise HTTPException(status_code=400, detail="Unsupported payment method")

    except Exception as e:
        # If payment fails, mark donation as failed
        donation.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")


@router.get("/", response_model=list[DonationOut])
def list_donations(
        db: Session = Depends(get_db),
        active_only: bool = False,
        tenant_id: UUID | None = None,
        campaign_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
):
    query = db.query(Donation).options(joinedload(Donation.campaign))
    if active_only:
        now = datetime.now()
        query = query.filter(Donation.donated_at >= now)
    if tenant_id:
        query = query.filter(Donation.tenant_id == tenant_id)
    if campaign_id:
        query = query.filter(Donation.campaign_id == campaign_id)
    if start_date:
        query = query.filter(Donation.donated_at >= start_date)
    if end_date:
        query = query.filter(Donation.donated_at <= end_date)

    donations = query.order_by(Donation.donated_at.desc()).all()

    return donations


@router.post("/pay/{donation_id}")
async def pay_donation(donation_id: UUID, db: Session = Depends(get_db)):
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    if donation.status == "PAID":
        raise HTTPException(status_code=400, detail="Donation already paid")
    if donation.method != "MPESA":
        raise HTTPException(status_code=400, detail="Donation method not supported")
    if donation.amount <= 0:
        raise HTTPException(status_code=400, detail="Donation amount must be greater than 0")
    if donation.tenant_id is None:
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    integrations = donation.tenant.mpesa_integrations
    active_integration = next((integration for integration in integrations if integration.is_active), None)
    if active_integration is None:
        raise HTTPException(status_code=400, detail="No active MPESA integration found")
    try:
        result = await process_payment(donation, db)
        return {"status": "initiated", "payment_data": result, "donation_id": donation.id}
    except Exception as e:
        donation.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Payment failed: {str(e)}")


@router.get("/pay/{donation_id}/status")
def get_payment_status(donation_id: UUID, db: Session = Depends(get_db)):
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return {
        "status": donation.status,
        "transaction_code": donation.transaction_id
    }


@router.get("/campaigns/{campaign_id}", response_model=list[DonationOut])
def list_campaign_donations(campaign_id: UUID, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    donations = db.query(Donation) \
        .filter(Donation.campaign_id == campaign_id).order_by(Donation.donated_at.desc()).all()

    return donations
