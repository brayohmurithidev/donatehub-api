import aio_pika

from app.config import settings


async def get_connection():
    return await aio_pika.connect_robust(
        url=settings.RABBITMQ_URL
    )


async def get_channel():
    connection = await get_connection()
    return await connection.channel()
