from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret
from app.db.models import Donation, MPESAIntegration
from app.db.models.donation import PaymentMethod
from app.schemas.mpesa_integration import MPESAIntegrationCreate, MPESAIntegrationOut
from app.services.mpesa import initiate_stk_push


async def process_payment(donation: type[Donation], db):
    if donation.method == PaymentMethod.MPESA:
        # GET INTEGRATION DETAILS
        integrations = donation.tenant.mpesa_integrations
        active_integration = next((integration for integration in integrations if integration.is_active), None)
        integration = MPESAIntegrationOut(
            consumer_key=decrypt_secret(active_integration.consumer_key),
            consumer_secret=decrypt_secret(active_integration.consumer_secret),
            shortcode=active_integration.shortcode,
            passkey=decrypt_secret(active_integration.passkey),
            callback_url=active_integration.callback_url,
            # environment=response.environment.value,
        )
        if not integration:
            raise HTTPException(status_code=400, detail="No active M-PESA integration found")
        print("integration", integration, donation.__dict__)
        return await initiate_stk_push(integration, donation, db)
    # CREATE DONATION VIA CARD
    return None