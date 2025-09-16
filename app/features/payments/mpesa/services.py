import base64
from datetime import datetime

import httpx
import requests
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from fastapi import HTTPException
from app.common.security import decrypt_secret
from app.features.donation.models import Donation, PaymentMethod
from app.features.payments.mpesa.schemas import MPESAIntegrationOut


def get_url(environment):
    if environment == "sandbox":
        return "https://sandbox.safaricom.co.ke"
    else:
        return "https://api.safaricom.co.ke"


def get_access_token(consumer_key, consumer_secret, base_url):
    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if r.status_code != 200:
        raise Exception("Failed to get access token")
    data = r.json()
    return data['access_token']


async def initiate_stk_push(integration, donation: Donation, db: Session):
    url = get_url(integration.environment)
    token = get_access_token(integration.consumer_key, integration.consumer_secret, url)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f"{integration.shortcode}{integration.passkey}{timestamp}".encode()).decode()

    payload = {
        "BusinessShortCode": integration.shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(donation.amount),
        "PartyA": donation.donor_phone,
        "PartyB": integration.shortcode,
        "PhoneNumber": donation.donor_phone,
        "CallBackURL": integration.callback_url,
        "AccountReference": str(donation.campaign.title),
        "TransactionDesc": donation.message or "Donation"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{url}/mpesa/stkpush/v1/processrequest", json=payload,
                                     headers=headers)
        resp_json = response.json()
        donation.transaction_id = resp_json.get("CheckoutRequestID")
        donation.callback_data = resp_json
        db.commit()
        return resp_json



async def process_payment(donation: Donation, db: Session):
    if donation.method == PaymentMethod.MPESA:
        integrations = donation.tenant.mpesa_integrations
        active_integration = next((integration for integration in integrations if integration.is_active), None)
        if active_integration is None:
            raise HTTPException(status_code=400, detail="No active M-PESA integration found")

        integration = MPESAIntegrationOut(
            consumer_key=decrypt_secret(active_integration.consumer_key),
            consumer_secret=decrypt_secret(active_integration.consumer_secret),
            shortcode=active_integration.shortcode,
            passkey=decrypt_secret(active_integration.passkey),
            callback_url=active_integration.callback_url,
            environment=active_integration.environment,
            is_active=active_integration.is_active,
            id=active_integration.id,
            tenant_id=active_integration.tenant_id,
            created_at=active_integration.created_at,
            updated_at=active_integration.updated_at,
        )

        return await initiate_stk_push(integration, donation, db)
    return None

