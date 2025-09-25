import json

import aio_pika

from app.services.rabbitmq.connection import get_channel


async def publish_message(queue_name: str, message: dict):
    """
    Publish a message to a specific queue
    """
    channel = await get_channel()
    queue = await channel.declare_queue(queue_name, durable=True)
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue.name,
    )

    print(f"Message published to {queue_name} : {message}")
