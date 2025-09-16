from datetime import timedelta, datetime

from jose import jwt, ExpiredSignatureError, JWTError
from passlib.context import CryptContext

from app.common.handle_error import handle_error
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Check password match
def check_password_match(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        handle_error(401, "Token expired", )
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Token expired",
        #     headers={"WWW-Authenticate": "Bearer"},
        # )
    except JWTError:
        handle_error(401, "Invalid token", )


def create_refresh_token(data: dict):
    expire = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        handle_error(401, "Invalid refresh token", )
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Invalid refresh token",
        #     headers={"WWW-Authenticate": "Bearer"},
        # )
