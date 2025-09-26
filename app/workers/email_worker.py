import json
import logging

from aio_pika import IncomingMessage

logger = logging.getLogger(__name__)


async def handle_email(message: IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        logger.info(f"Sending email receipt to {data['donor_email']} for donation {data['amount']} KES")
