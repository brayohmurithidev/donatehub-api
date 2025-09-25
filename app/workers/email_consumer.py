import asyncio
import json

from aio_pika import IncomingMessage

from app.services.rabbitmq.connection import get_channel


async def send_email_consumer(message: IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        print(f"Received message: {data}")

        # Do some work
        await asyncio.sleep(5)
        print("Done processing")


async def main():
    channel = await get_channel()
    queue = await channel.declare_queue("email_queue", durable=True)
    await  queue.consume(send_email_consumer)
    print("Waiting for messages. To exit press CTRL+C")
    await asyncio.Future()


asyncio.run(main())
