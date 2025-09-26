import json
import logging

from aio_pika import IncomingMessage

logger = logging.getLogger(__name__)


async def handle_sms(message: IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        logger.info(f"Sending SMS receipt to {data['donor_email']} for donation {data['amount']} KES")
        # Call the business logic here
