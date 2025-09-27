from datetime import datetime, timedelta
from urllib.parse import urlencode

from jose import jwt, ExpiredSignatureError, JWTError

from app.config import settings


def generate_verification_token(user_id: str, expires_in_minutes: int = 60) -> str:
    """
    Generate a signed JWT verification token.

    Args:
        user_id (str): ID of the user or tenant admin.
        Expires_in_minutes (int): Expiry time for token.

    Returns:
        str: Encoded JWT token
        :param user_id:
        :param expires_in_minutes:
    """
    payload = {
        "sub": str(user_id),
        "type": "email_verification",
        "exp": datetime.now() + timedelta(minutes=int(expires_in_minutes)),
        "iat": datetime.now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def verify_verification_token(token: str) -> dict:
    """
    Verify and decode the JWT verification token.

    Args:
        token (str): Encoded JWT token.

    Returns:
        dict: Decoded payload if valid.

    Raises:
        jwt.ExpiredSignatureError: If token expired.
        jwt.InvalidTokenError: If token is invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "email_verification":
            raise JWTError("Invalid token type")
        return payload
    except ExpiredSignatureError:
        raise
    except JWTError:
        raise


def generate_verification_url(token: str, base_url: str = None) -> str:
    """
    Generate a verification URL for email confirmation.

    Args:
        token (str): Verification token (JWT, UUID, etc.)
        base_url (str, optional): Frontend base URL. Defaults to settings.FRONTEND_URL.

    Returns:
        str: Fully qualified verification URL.
    """

    base = base_url or settings.FRONTEND_URL
    path = "/verify-email"  # frontend route for verification

    query = urlencode({"token": token})
    return f"{base}{path}?{query}"
