import asyncio

from aio_pika import ExchangeType

from app.logger import logger
from app.services.rabbitmq.connection import get_channel
from app.workers.SMS_Worker import handle_sms
from app.workers.email_verification_worker import email_verification_worker
from app.workers.email_worker import handle_email


async def start_consumer(queue_name: str, handler, channel, exchange):
    queue = await channel.declare_queue(queue_name, durable=True)
    await queue.bind(exchange)
    await queue.consume(handler)
    logger.info(f"Started consumer: {queue_name}")


async def main():
    channel = await get_channel()

    # Declare fanout exchange
    exchange = await channel.declare_exchange("donation_events", ExchangeType.FANOUT)

    # Start consumers concurrently
    await asyncio.gather(
        start_consumer("email_requests", handle_email, channel, exchange),
        start_consumer("sms_receipts", handle_sms, channel, exchange),
        email_verification_worker(channel)
    )

    logger.info("All consumers are running ... waiting for message")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
