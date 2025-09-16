import os
from typing import Optional

import redis

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        # Ping once to verify connectivity; ignore failures silently
        _redis_client.ping()
        return _redis_client
    except Exception:
        return None
