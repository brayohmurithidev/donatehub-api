import base64
from datetime import datetime

import httpx
import requests
from fastapi import Depends
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from app.db.index import get_db
from app.db.models import Donation


def get_url(environment):
    if environment == "sandbox":
        return "https://sandbox.safaricom.co.ke"
    else:
        return "https://api.safaricom.co.ke"


def get_access_token(consumer_key, consumer_secret, base_url):
    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    print("consumer: ", consumer_secret, consumer_key)
    r = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if r.status_code != 200:
        raise Exception("Failed to get access token")
    data = r.json()
    return data['access_token']


async def initiate_stk_push(integration, donation: type[Donation], db: Session = Depends(get_db)):
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
