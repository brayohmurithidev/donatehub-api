import json

import aio_pika
from aio_pika import Channel, ExchangeType, DeliveryMode

from app.common.send_email import send_verification_email
from app.logger import logger
from app.services.rabbitmq.publisher import Exchanges, RoutingKeys

RETRY_QUEUE = "email_verification_retry_queue"
DLQ_QUEUE = "email_verification_dlq"
DLX_NAME = "dlx.notifications"
MAX_RETRIES = 3


async def email_verification_worker(channel: Channel):
    # Declare main exchange
    exchange = await channel.declare_exchange(
        Exchanges.NOTIFICATIONS.value,
        ExchangeType.TOPIC,
        durable=True
    )

    # Dead letter exchange
    dlx = await channel.declare_exchange(
        DLX_NAME,
        ExchangeType.TOPIC,
        durable=True
    )

    # DLQ
    dlq = await channel.declare_queue(DLQ_QUEUE, durable=True)
    await dlq.bind(dlx, routing_key=RoutingKeys.EMAIL_VERIFICATION.value)

    # Retry queue with TTL (sends back to main exchange after TTL)
    retry_queue = await channel.declare_queue(
        RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": 10000,  # retry after 10s
            "x-dead-letter-exchange": Exchanges.NOTIFICATIONS.value,
            "x-dead-letter-routing-key": RoutingKeys.EMAIL_VERIFICATION.value,
        }
    )
    await retry_queue.bind(exchange, routing_key=RETRY_QUEUE)

    # Main queue (with DLX config)
    queue = await channel.declare_queue(
        f"{RoutingKeys.EMAIL_VERIFICATION.value}_queue",
        durable=True,
        arguments={
            "x-dead-letter-exchange": DLX_NAME,
            "x-dead-letter-routing-key": RoutingKeys.EMAIL_VERIFICATION.value,
        }
    )
    await queue.bind(exchange, routing_key=RoutingKeys.EMAIL_VERIFICATION.value)

    logger.info("Listening for email.verification events...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process(ignore_processed=True):
                try:
                    payload = json.loads(message.body)
                    email = payload["email"]

                    logger.info(f"Processing verification email for {email}")
                    res = await send_verification_email(email, payload)

                    if not res:
                        raise Exception("Email send failed")

                    logger.info(f"Email sent successfully: {res}")

                except Exception as e:
                    retries = (message.headers or {}).get("x-retry", 0)

                    if retries >= MAX_RETRIES:
                        await dlx.publish(
                            aio_pika.Message(
                                body=message.body,
                                delivery_mode=DeliveryMode.PERSISTENT
                            ),
                            routing_key=RoutingKeys.EMAIL_VERIFICATION.value
                        )
                        logger.warning(f"Moved to DLQ after {MAX_RETRIES} retries: {message.body}")
                    else:
                        await exchange.publish(
                            aio_pika.Message(
                                body=message.body,
                                delivery_mode=DeliveryMode.PERSISTENT,
                                headers={"x-retry": retries + 1}
                            ),
                            routing_key=RETRY_QUEUE
                        )
                        logger.info(f"Sent to retry queue (retry={retries + 1})")

                    await message.ack()
