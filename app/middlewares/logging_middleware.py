import time
import uuid

import structlog
from fastapi import Request
from jose import jwt, JWTError
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.config import settings

logger = structlog.get_logger()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))  # use existing else generate new one
    user_id = None
    tenant_id = None

    # try to extract user info from the auth header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
        except JWTError:
            logger.warning("Invalid JWT", token=token[:10] + "...")

    # Bind contexts for this request
    bind_contextvars(request_id=request_id, user_id=user_id)

    start_time = time.time()

    try:
        response = await call_next(request)
        duration = round(time.time() - start_time, 3)

        # Add request_id to the response headers - helps in client reporting
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "HTTP Request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            client=request.client.host,
            # user_id=user_id,
        )
        return response

    finally:
        clear_contextvars()
