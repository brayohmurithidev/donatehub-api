import os
from typing import Optional

from fastapi import HTTPException

from app.logger import logger


def handle_error(
        status_code: int,
        error_message: str,
        exc: Optional[BaseException] = None,
        *,
        expose_stack: bool = os.environ.get("ENV") == "development",
) -> None:
    """
    Log and raise HTTPException.
    - status_code: numeric HTTP status (e.g., 400, 404, 500)
    - error_message: human-friendly message
    - exc: optional caught exception object (for stack trace)
    - expose_stack: if True, include stack trace in HTTP response (dev only)
    """

    # Always log with stack trace if an exception exists
    if exc:
        logger.error(
            "Application error",
            status_code=status_code,
            error_message=error_message,
            exc_info=exc,  # <--- structured stack trace
        )
    else:
        logger.error(
            "Application error",
            status_code=status_code,
            error_message=error_message,
            stack="No exception provided",
        )

    # Prepare response detail
    detail = error_message

    raise HTTPException(status_code=status_code, detail=detail)
