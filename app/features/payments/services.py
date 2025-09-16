from app.features.donation.models import Donation
from app.features.payments.mpesa.services import process_payment as process_mpesa_payment


async def process_payment(donation: Donation, db):
    return await process_mpesa_payment(donation, db)


