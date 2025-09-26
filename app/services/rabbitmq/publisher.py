import json
from enum import Enum

import aio_pika
from aio_pika import ExchangeType, DeliveryMode

from app.logger import logger
from app.services.rabbitmq.connection import get_connection, get_channel


class Exchanges(str, Enum):
    NOTIFICATIONS = "notifications"


class RoutingKeys(str, Enum):
    EMAIL_VERIFICATION = "email.verification"
    EMAIL_RESET_PASSWORD = "email.reset_password"
    SMS_AUTH = "sms.auth"


# EXCHANGE TYPE TOPIC
async def publish_notification(routing_key: RoutingKeys, payload: dict):
    connection = await get_connection()
    async with connection:
        channel = await get_channel()

        # Declare exchange of a type topic
        exchange = await channel.declare_exchange(
            Exchanges.NOTIFICATIONS.value, ExchangeType.TOPIC, durable=True
        )

        # Publish a message with a routing key
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=DeliveryMode.PERSISTENT
        )

        await exchange.publish(message, routing_key=routing_key.value)
        logger.info(f"[Producer] Sent message with routing_key={routing_key.value}: {payload}")


# EXCHANGE TYPE FANOUT
async def publish_donation_event(donation_id: str, donor_email: str, amount: float):
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()

        # Fanout exchange - > broadcasts to all queues
        exchange = await channel.declare_exchange("donation_events", aio_pika.ExchangeType.FANOUT)

        event = {
            "donation_id": donation_id,
            "donor_email": donor_email,
            "amount": amount
        }

        await exchange.publish(
            aio_pika.Message(body=json.dumps(event).encode()),
            routing_key=""  # not needed for fanout
        )

        logger.info(f"[X] Published donation event : {event}")
