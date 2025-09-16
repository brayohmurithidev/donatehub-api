import base64
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.common.deps import require_tenant_admin
from app.common.security import encrypt_secret, decrypt_secret
from app.db.index import get_db
from app.features.donation.models import Donation, PaymentStatus
from app.features.campaign.models import Campaign
from app.features.payments.mpesa.models import MPESAIntegration
from app.features.payments.mpesa.schemas import MPESAIntegrationCreate, MPESAIntegrationOut, \
    MpesaIntegrationUpdate, MpesaIntegrationTestCreate
from app.features.payments.mpesa.services import get_access_token, get_url

router = APIRouter()


@router.get("/")
def get_mpesa_integrations(
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    integration = db.query(MPESAIntegration).filter(MPESAIntegration.tenant_id == tenant.id).first()
    return integration


@router.post("/add-payment", summary="Create M-PESA Integration")
def add_mpesa_payment(
        payload: MPESAIntegrationCreate,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    try:
        tenant_id = tenant.id

        existing = db.query(MPESAIntegration).filter(MPESAIntegration.tenant_id == tenant_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Tenant already has an M-PESA integration")

        if payload.is_active:
            active_exists = (
                db.query(MPESAIntegration)
                .filter(MPESAIntegration.tenant_id == tenant_id)
                .filter(MPESAIntegration.is_active == True)
                .first()
            )
            if active_exists:
                raise HTTPException(status_code=400, detail="Tenant already has an active integration")

            if not payload.shortcode.isdigit() or not (5 <= len(payload.shortcode) <= 6):
                raise HTTPException(status_code=400, detail="Invalid shortcode format. Must be 5-6 digits.")

        integration_id = uuid4()
        callback_url = f"https://4caf5f17f0b2.ngrok-free.app/api/v1/mpesa/callback",

        integration = MPESAIntegration(
            id=integration_id,
            tenant_id=tenant_id,
            name=payload.name,
            shortcode=payload.shortcode,
            consumer_key=encrypt_secret(payload.consumer_key),
            consumer_secret=encrypt_secret(payload.consumer_secret),
            passkey=encrypt_secret(payload.passkey),
            callback_url=f"{callback_url}/{integration_id}",
            account_reference=payload.account_reference,
            environment=payload.environment.value,
            is_active=payload.is_active
        )

        db.add(integration)
        db.commit()
        db.refresh(integration)

        return {"message": "M-PESA Integration created successfully", "integration_id": str(integration.id)}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.put("/update-payment", response_model=MPESAIntegrationOut, summary="Update M-PESA Integration")
def update_mpesa_payment(
        payload: MpesaIntegrationUpdate,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    payment = db.query(MPESAIntegration).filter(MPESAIntegration.tenant_id == tenant.id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="No M-PESA integration found for this tenant")
    try:
        for key, value in payload.model_dump(exclude_unset=True).items():
            if key == "consumer_key" or key == "consumer_secret" or key == "passkey":
                if not value:
                    continue
                value = encrypt_secret(value)
            if isinstance(value, HttpUrl):
                value = str(value)
            setattr(payment, key, value)

        db.commit()
        db.refresh(payment)
        return payment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.post("/test-integration", summary="Test M-PESA Integration")
async def test_mpesa_integration(
        payload: MpesaIntegrationTestCreate,
        db: Session = Depends(get_db),
        auth=Depends(require_tenant_admin)
):
    user, tenant = auth
    if not payload.amount or not payload.phone:
        raise HTTPException(status_code=400, detail="Amount and phone number are required")
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this auth")
    try:
        integration = db.query(MPESAIntegration).filter(MPESAIntegration.tenant_id == tenant.id).first()

        if not integration:
            raise HTTPException(status_code=404, detail="No M-PESA integration found for this tenant")
        url = get_url(integration.environment)
        key = decrypt_secret(str(integration.consumer_key))
        secret = decrypt_secret(str(integration.consumer_secret))
        passKey = decrypt_secret(str(integration.passkey))
        token = get_access_token(key, secret, url)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{integration.shortcode}{passKey}{timestamp}".encode()).decode()

        payload = {
            "BusinessShortCode": integration.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": payload.amount,
            "PartyA": payload.phone,
            "PartyB": integration.shortcode,
            "PhoneNumber": payload.phone,
            "CallBackURL": integration.callback_url,
            "AccountReference": "Payment Integration Test",
            "TransactionDesc": "Payment Integration Test"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{url}/mpesa/stkpush/v1/processrequest", json=payload,
                                         headers=headers)
            resp_json = response.json()

            if resp_json.get("ResponseCode") == "0":
                integration.is_verified = True
                db.commit()
                return {"message": "M-PESA Integration test successful", "response": resp_json}
            raise HTTPException(status_code=400, detail=resp_json.get("errorMessage"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.post("/callback/{integration_id}")
async def mpesa_callback(
        integration_id: str,
        request: Request,
        db: Session = Depends(get_db)
):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    try:
        body = json.loads(body_str)
        stk_callback = body["Body"]["stkCallback"]
        checkout_request_id = stk_callback["CheckoutRequestID"]
        result_code = stk_callback["ResultCode"]
        result_desc = stk_callback["ResultDesc"]

        amount = None
        mpesa_receipt_number = None
        phone_number = None

        if result_code == 0:
            metadata_items = stk_callback['CallbackMetadata']['Item']
            for item in metadata_items:
                if item['Name'] == 'Amount':
                    amount = item['Value']
                elif item['Name'] == 'MpesaReceiptNumber':
                    mpesa_receipt_number = item['Value']
                elif item['Name'] == 'PhoneNumber':
                    phone_number = item['Value']

            donation = db.query(Donation).filter(Donation.transaction_id == checkout_request_id).first()
            if donation:
                donation.status = PaymentStatus.SUCCESS
                donation.donor_phone = phone_number
                donation.transaction_id = mpesa_receipt_number
                donation.callback_data = body
                donation.donated_at = datetime.now(timezone.utc)
                db.add(donation)

                campaign = db.query(Campaign).filter(Campaign.id == donation.campaign_id).first()
                campaign.current_amount += Decimal(amount)
                db.commit()
        else:
            donation = db.query(Donation).filter(Donation.transaction_id == checkout_request_id).first()
            if donation:
                donation.status = PaymentStatus.FAILED
                donation.callback_data = body_str
                db.commit()

        return {"message": "Callback received"}, 200

    except Exception as e:
        return {"error": str(e)}, 500


